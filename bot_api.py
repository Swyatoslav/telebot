import os
import sys
import time

import requests
import telebot
from telebot import types

from bot_config import ConfigManager
from bot_db import DBManager
from bot_logging import LogManager
from bot_skills import WeatherManager, CommunicationManager

# Создадим конфиг
config_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'config.ini')
config = ConfigManager().create_config(config_path)

# Запишем токен
with open(os.path.join(config.get('general', 'settings_path'), 'token.txt'), 'r') as token_file:
    token_line = token_file.read()
    config.set('general', 'token', token_line)

# Инициализируем бота
bot = telebot.TeleBot(config.get('general', 'token'), threaded=False)
hello_message = 'Привет! Я бета версия умного бота :)\n\n'
info_message = 'Вот что я умею:\n' \
               'Общаться, но пока что с трудом..\n' \
               'Говорить погоду /weather\n' \
               'Ссылка на меня: http://t.me/svyat93_bot\n\n' \
               'Повтор подсказок: /help\n' \
               'Полный список команд вы увидите,\n' \
               'введя в поле сообщения (не отправляя) символ /'


lm = LogManager()  # логирование
db = DBManager(config.get('general', 'db'), config.get('general', 'db_user_name'),
               config.get('general', 'db_user_password'))  # Соединение с бд
cm = CommunicationManager()  # Общение с пользователем
wm = WeatherManager()  # Работа с погодой


@db.set_user_info
@bot.message_handler(commands=['start', 'help', 'weather', 'qwsa1234'])
@lm.log_message
def start_message(message):
    if message.text in '/start':
        bot.send_message(message.chat.id, hello_message)
        bot.send_message(message.chat.id, info_message)
    elif '/weather' in message.text:
        bot.send_message(message.chat.id, 'Нажмите нужную кнопку внизу', reply_markup=wm.show_weather_buttons(),)
    elif message.text in ['/help']:
        bot.send_message(message.chat.id, info_message)
    elif 'qwsa1234' in message.text and message.from_user.id:
        bot.send_message(message.chat.id, 'Привет, Святослав')
        bot.send_message(message.chat.id, 'Твои инструменты:'
                                          '\nвыдай неопознанные'
                                          '\nочисти неопознанные'
                                          '\nссылка на меня: http://t.me/svyat93_bot')


@bot.message_handler(content_types=['text'])
@lm.log_message
@db.set_user_info
def send_text(message):
    time.sleep(0.5)
    if cm.is_weather_question(message.text):
        bot.send_message(message.chat.id, 'Секундочку')
        bot.send_message(message.chat.id, wm.get_weather_info(message))
    elif ('выдай неопознанные' in message.text.lower()) and db.is_admin_id(message.from_user.id):
        bot.send_message(message.chat.id, db.get_unknown_massage_info())
    elif ('очисти неопознанные' in message.text.lower()) and db.is_admin_id(message.from_user.id):
        bot.send_message(message.chat.id, db.delete_all_unknown_messages())
    elif ('дай ссылку на себя' in message.text.lower() or 'дай свою ссылку' in message.text.lower()) \
            and db.is_admin_id(db.is_admin_id(message.from_user.id)):
        bot.send_message(message.chat.id, 'http://t.me/svyat93_bot')
    elif cm.is_skill_question(message):
        bot.send_message(message.chat.id, info_message)
    else:
        # Если есть ответ от бота - присылаем юзеру, если нет - бот его не понял
        response = cm.get_bot_answer(message)
        if response:
            bot.send_message(chat_id=message.chat.id, text=response)
        else:
            db.set_unknown_message_info(message)
            bot.send_message(message.chat.id, text='Я Вас не совсем понял!')
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
