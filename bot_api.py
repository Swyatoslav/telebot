import os
import sys
import time

import requests
import telebot
from telebot.types import ReplyKeyboardRemove

from bot_config import ConfigManager
from bot_db import DBManager
from bot_logging import LogManager
from bot_skills import MasterOfWeather, CommunicationManager
from bot_consts import ConstantManager
from bot_games import CitiesGameManager

# Создадим конфиг
config = ConfigManager().create_config(ConstantManager.config_path)

# Запишем токен
with open(os.path.join(config.get('general', 'settings_path'), 'token.txt'), 'r') as token_file:
    token_line = token_file.read()
    config.set('general', 'token', token_line)

# Инициализируем бота
bot = telebot.TeleBot(config.get('general', 'token'), threaded=False)
hello_message = 'Привет! Я бета версия умного бота :)\n\n'
info_message = 'Вот что я умею:\n' \
               'Общаться, но пока что с трудом..\n' \
               'Говорить погоду /weather\n\n' \
               'Играть в города /game_cities\n'\
               'Полный список команд вы увидите,\n' \
               'нажав на кнопку [ / ] справа от строки сообщения\n\n' \
               'Ссылка на меня: \nhttp://t.me/svyat93_bot\n\n' \
               'Повтор подсказок: /help\n'

lm = LogManager()  # логирование
db = DBManager(config.get('general', 'db'), config.get('general', 'db_user_name'),
               config.get('general', 'db_user_password'))  # Соединение с бд
cm = CommunicationManager()  # Общение с пользователем
mow = MasterOfWeather()  # Работа с погодой
cities_gm = CitiesGameManager()


@db.set_user_info
@bot.message_handler(commands=['start', 'help', 'weather', 'qwsa1234', 'new_weather', 'game_cities'])
@lm.log_message
def start_message(message):
    if '/start' in message.text.lower():
        bot.send_message(message.chat.id, hello_message, reply_markup=ReplyKeyboardRemove())
        bot.send_message(message.chat.id, info_message, reply_markup=ReplyKeyboardRemove())
    elif '/weather' in message.text:
        bot.send_message(message.chat.id, 'Выберите одну из кнопок внизу',
                         reply_markup=mow.set_buttons('Погода сегодня', 'Погода завтра'))
    elif '/help'in message.text.lower():
        bot.send_message(message.chat.id, info_message, reply_markup=ReplyKeyboardRemove())
    elif message.text == '!' and message.from_user.id:
        bot.send_message(message.chat.id, 'Привет, Святослав')
        bot.send_message(message.chat.id, 'Твои инструменты:'
                                          '\nвыдай неопознанные'
                                          '\nочисти неопознанные'
                                          '\nссылка на меня: http://t.me/svyat93_bot',
                                          reply_markup=ReplyKeyboardRemove())
    elif 'new_weather' in message.text and db.is_weather_place_set(message.from_user.id):
        result = db.get_place_info_of_user_by_user_id(message.from_user.id)
        bot.send_message(message.chat.id, 'Сейчас вы смотрите погоду здесь: \n'
                                          '{} ({})\n'
                                          'Если желаете изменить его, нажмите\n'
                                          'соответствующую кнопку'.format(result[1], result[2]),
                                          reply_markup=mow.set_buttons('Желаю изменить', 'Оставлю как есть'))
    elif 'new_weather' in message.text and not db.is_weather_place_set(message.from_user.id):
        bot.send_message(message.chat.id,   'Чтобы поменять место, его нужно сначало установить :)\n'
                                            'Сделайте это с помощью команды /weather')
    elif 'game_cities' in message.text:
        cities_gm.game_mode(message, db, bot)


@bot.message_handler(content_types=['text'])
@lm.log_message
@db.set_user_info
def send_text(message):
    time.sleep(0.5)

    # Настройка вывода погоды
    if db.get_weather_edit_mode_stage(message.from_user.id):
        mow.weather_place_mode(message, db, bot)
    # Игра Города
    elif db.get_game_cities_mode_stage(message.from_user.id):
        cities_gm.game_mode(message, db, bot)
    # Вывод погоды
    elif cm.is_weather_question(message.text):
        bot.send_message(message.chat.id, 'Секундочку')
        if not db.is_weather_place_set(message.from_user.id):  # Если неизвестно, где искать погоду, идем настраивать
            mow.weather_place_mode(message, db, bot)
        else:
            bot.send_message(message.chat.id, mow.get_weather_info(db, message), reply_markup=ReplyKeyboardRemove())
    elif 'оставлю как есть' in message.text.lower():
        bot.send_message(message.chat.id, 'Хорошо, вы знаете где меня найти :)', reply_markup=ReplyKeyboardRemove())
    elif 'желаю изменить' in message.text.lower():
        db.set_place_id_to_user(None, message.from_user.id)
        mow.weather_place_mode(message, db, bot)
    elif ('выдай неопознанные' in message.text.lower()) and db.is_admin_id(message.from_user.id):
        bot.send_message(message.chat.id, db.get_unknown_massage_info())
    elif ('очисти неопознанные' in message.text.lower()) and db.is_admin_id(message.from_user.id):
        bot.send_message(message.chat.id, db.delete_all_unknown_messages())
    elif cm.is_skill_question(message):
        bot.send_message(message.chat.id, info_message, reply_markup=ReplyKeyboardRemove())
    else:
        # Если есть ответ от бота - присылаем юзеру, если нет - бот его не понял
        response = cm.get_bot_answer(message)
        if response:
            bot.send_message(chat_id=message.chat.id, text=response)
        else:
            db.set_unknown_message_info(message)
            bot.send_message(message.chat.id, text='Я Вас не совсем понял!')
            time.sleep(0.5)
            bot.send_message(message.chat.id, info_message)


# Команда для запуска бота

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True, interval=1, timeout=120)
        except requests.exceptions.ConnectTimeout:
            bot.stop_polling()
            print('Словил таймаут исключение')
            time.sleep(1)
            bot.polling(none_stop=True, interval=1, timeout=120)
