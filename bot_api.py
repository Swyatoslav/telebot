import os
import time

import requests
import telebot
from telebot.types import ReplyKeyboardRemove

from bot_config import ConfigManager
from bot_consts import ConstantManager
from bot_db import DBManager
from bot_games import CitiesGameManager, CapitalsGameManager, SpaceQuest
from bot_logging import LogManager
from bot_skills import MasterOfWeather, CommunicationManager, RandomManager, NotesManager
from bot_tools import BotButtons
from bot_calls import CallsManager
from functions import send_message


# Создадим конфиг
config = ConfigManager().create_config(ConstantManager.config_path)

# Запишем токен
with open(os.path.join(config.get('general', 'settings_path'), 'token.txt'), 'r') as token_file:
    token_line = token_file.read()
    config.set('general', 'token', token_line)

# Инициализируем бота
bot = telebot.TeleBot(config.get('general', 'token'), threaded=False)
hello_message = 'Привет! Я бета версия умного бота :)\n\n'
info_message = 'Вот что я умею:\n\n' \
               'Общаться, но пока что с трудом..\n' \
               'Говорить погоду /weather\n' \
               'Играть в города /game_cities\n' \
               'Игра в столицы /game_capitals\n\n' \
               'Полный список команд вы увидите,\n' \
               'нажав на кнопку [ / ] справа от строки сообщения\n\n' \
               'Ссылка на меня: \nhttp://t.me/svyat93_bot\n\n' \
               'Повтор подсказок: /help\n'

info_message_admin = """Вот чему ты меня научил:\n\n
Общаться, но пока что с трудом..\n
Говорить погоду /weather\n
Играть в города /game_cities\n
Игра в столицы /game_capitals\n
5 рандомных чисел /random_5\n
Вывод последнего отчета о баге /glr\n
Заметки (dev) /note\n
Команда -выдай неопознанные- для вывода неопознанных сообщений\n
Команда -почисти неопознанные- для очистки нераспозанных мною сообщений\n
Космический квест (dev) /space_quest\n
Ссылка на меня: \nhttp://t.me/svyat93_bot\n\n
Повтор подсказок: /help\n"""

lm = LogManager()  # логирование
db = DBManager(config.get('general', 'db'), config.get('general', 'db_user_name'),
               config.get('general', 'db_user_password'))  # Соединение с бд
cm = CommunicationManager()  # Общение с пользователем
mow = MasterOfWeather()  # Работа с погодой
cities_gm = CitiesGameManager()
capitals_gm = CapitalsGameManager()
rm = RandomManager()
sq = SpaceQuest()
bb = BotButtons()
cman = CallsManager()
nm = NotesManager()


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    mods = db.is_any_mode_activate(call.from_user.id)
    if mods:
        cman.call_trigger(db, bot, call, mods)
    else:
        cman.report_calls(db, bot, call)


@bot.message_handler(commands=['start', 'help', 'weather', 'qwsa1234', 'new_weather', 'game_cities', 'random_5',
                               'glr', 'send_update_message', 'send_user_message', 'game_capitals', 'space_quest',
                               'note'])
@db.set_user_info
@lm.log_message
def start_message(message):
    try:
        mods = db.is_any_mode_activate(message.from_user.id)
        if mods:
            send_message(bot, message.chat.id, 'Сначала завершите программу {}'.format(mods),
                             reply_markup=bb.gen_underline_butons('Прервать'))
        else:
            if '/start' in message.text.lower():
                send_message(bot, message.chat.id, hello_message, reply_markup=ReplyKeyboardRemove())
                send_message(bot, message.chat.id, info_message, reply_markup=ReplyKeyboardRemove())
            elif '/weather' in message.text:
                send_message(bot, message.chat.id, 'Выберите одну из кнопок внизу',
                                 reply_markup=bb.gen_underline_butons('Погода сегодня', 'Погода завтра'))
            elif '/help' in message.text.lower() and db.is_admin_id(message.from_user.id):
                send_message(bot, message.chat.id, info_message_admin, reply_markup=ReplyKeyboardRemove())
            elif '/help' in message.text.lower() and not db.is_admin_id(message.from_user.id):
                send_message(bot, message.chat.id, info_message, reply_markup=ReplyKeyboardRemove())
            elif message.text == '!' and db.is_admin_id(message.from_user.id):
                send_message(bot, message.chat.id, 'Привет, Святослав')
                send_message(bot, message.chat.id, 'Твои инструменты:'
                                                  '\nвыдай неопознанные'
                                                  '\nочисти неопознанные'
                                                  '\nссылка на меня: http://t.me/svyat93_bot',
                                 reply_markup=ReplyKeyboardRemove())
            elif 'new_weather' in message.text and db.is_weather_place_set(message.from_user.id):
                result = db.get_place_info_of_user_by_user_id(message.from_user.id)
                send_message(bot, message.chat.id, 'Сейчас вы смотрите погоду здесь: \n'
                                                  '{} ({})\n'
                                                  'Если желаете изменить его, нажмите\n'
                                                  'соответствующую кнопку'.format(result[1], result[2]),
                                 reply_markup=bb.gen_underline_butons('Желаю изменить', 'Оставлю как есть'))
            elif 'new_weather' in message.text and not db.is_weather_place_set(message.from_user.id):
                send_message(bot, message.chat.id, 'Чтобы поменять место, его нужно сначало установить :)\n'
                                                  'Сделайте это с помощью команды /weather')
            elif 'game_cities' in message.text:
                cities_gm.game_mode(message, db, bot)
            elif 'game_capitals' in message.text:
                capitals_gm.game_mode(message, db, bot)

            elif 'random_5' in message.text:
                db.set_random_five_mode(message.from_user.id, True)
                time.sleep(0.5)
                send_message(bot, message.chat.id, 'Введите максимально возможное число диапазона',
                                 reply_markup=bb.gen_underline_butons('Прервать random_5'))

            elif 'glr' in message.text and db.is_admin_id(message.from_user.id):
                last_report_id = db.get_last_report_id()
                if last_report_id:
                    result = db.get_report_info(last_report_id[0])
                    send_message(bot, '344950989', 'Отчет №{}\n{}{}'.format(last_report_id[0], result[0], result[1]),
                                     reply_markup=lm.gen_report_buttons(last_report_id[0], 'delreport'))
                else:
                    send_message(bot, '344950989', 'Отчеты об ошибках отсутствуют')

            elif 'space_quest' in message.text and db.is_admin_id(message.from_user.id):
                sq.game_mode(message, db, bot)

            # elif 'send_update_message' in message.text and db.is_admin_id(message.from_user.id)
                chat_ids = db.get_chat_ids()
                # for chat_id in chat_ids:
                #     try:
                #         send_message(bot, chat_id, """""", parse_mode='Markdown')
                #     except ApiException:
                #         pass

                # send_message(bot, 344950989, '', parse_mode='Markdown', reply_markup=)

            elif 'send_user_message' in message.text and db.is_admin_id(message.from_user.id):
                send_message(bot, 214864371, """""", parse_mode='Markdown')

            elif 'note' in message.text and db.is_admin_id(message.from_user.id):
                nm.notes_mode(message, db, bot)

    except Exception as err:
        lm.send_error_report(bot, db, message, err)


@bot.message_handler()
@lm.log_message
@db.set_user_info
def send_text(message):
    try:
        time.sleep(0.5)
        # ========= ВКЛЮЧЕННЫЕ МОДЫ ===========
        # random_five
        if db.is_random_five_mode(message.from_user.id):
            rm.random_five_mode(message, db, bot)
        # Настройка вывода погоды
        elif db.get_weather_edit_mode_stage(message.from_user.id):
            mow.weather_place_mode(message, db, bot)
        # Игра Города
        elif db.get_game_cities_mode_stage(message.from_user.id):
            cities_gm.game_mode(message, db, bot)
        elif db.get_game_capitals_mode_stage(message.from_user.id):
            capitals_gm.game_mode(message, db, bot)
        elif db.get_space_quest_mode(message.from_user.id):
            sq.game_mode(message, db, bot)
        elif db.get_notes_mode_stage(message.from_user.id):
            nm.notes_mode(message, db, bot)
        # ========= Общение ===========
        elif cm.is_weather_question(message.text):
            send_message(bot, message.chat.id, 'Секундочку')
            if not db.is_weather_place_set(
                    message.from_user.id):  # Если неизвестно, где искать погоду, идем настраивать
                mow.weather_place_mode(message, db, bot)
            else:
                send_message(bot, message.chat.id, mow.get_weather_info(db, message), reply_markup=ReplyKeyboardRemove())
        elif 'оставлю как есть' in message.text.lower():
            send_message(bot, message.chat.id, 'Хорошо, вы знаете где меня найти :)', reply_markup=ReplyKeyboardRemove())
        elif 'желаю изменить' in message.text.lower():
            db.set_place_id_to_user(None, message.from_user.id)
            mow.weather_place_mode(message, db, bot)
        elif ('выдай неопознанные' in message.text.lower()) and db.is_admin_id(message.from_user.id):
            send_message(bot, message.chat.id, db.get_unknown_massage_info())
        elif ('очисти неопознанные' in message.text.lower()) and db.is_admin_id(message.from_user.id):
            send_message(bot, message.chat.id, db.delete_all_unknown_messages())
        elif cm.is_skill_question(message):
            send_message(bot, message.chat.id, info_message, reply_markup=ReplyKeyboardRemove())
        else:
            # Если есть ответ от бота - присылаем юзеру, если нет - бот его не понял
            response = cm.get_bot_answer(message)
            if response:

                send_message(bot, message.chat.id, response)
            else:
                db.set_unknown_message_info(message)
                send_message(bot, message.chat.id, 'Я Вас не совсем понял!')
                time.sleep(0.5)
                send_message(bot, message.chat.id, info_message)
    except Exception as err:
        lm.send_error_report(bot, db, message, err)


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
