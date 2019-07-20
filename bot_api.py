import os
import sys
import time

import requests
import telebot

from bot_config import ConfigManager
from bot_db import DBManager
from bot_logging import LogManager
from bot_skills import WeatherManager, CommunicationManager

# Создадим конфиг
config_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'config.ini')
cm = ConfigManager().create_config(config_path)

# Запишем токен
with open(os.path.join(cm.get('general', 'settings_path'), 'token.txt'), 'r') as token_file:
    token_line = token_file.read()
    cm.set('general', 'token', token_line)

# Включим логирование
lm = LogManager()
# lm.start_logging()

# создаем экземпляр бд
db = DBManager(cm.get('general', 'db'), cm.get('general', 'db_user_name'), cm.get('general', 'db_user_password'))

# Инициализируем бота
bot = telebot.TeleBot(cm.get('general', 'token'), threaded=False)
hello_message = 'Привет!\nЯ бета версия умного бота'
info_message = 'Вот что я пока умею:\n' \
               '\n' \
               'Общаться \n' \
               'Говорить погоду /weather\n\n' \
               'Для повтора подсказок введите\n /help'
cm = CommunicationManager()


@db.set_user_info
@bot.message_handler(commands=['start', 'help', 'weather', 'qwsa1234'])
@lm.log_message
def start_message(message):
    if message.text in '/start':
        bot.send_message(message.chat.id, cm.say_hello())
        bot.send_message(message.chat.id, info_message)
    elif '/weather' in message.text:
        bot.send_message(message.chat.id, 'Секундочку')
        bot.send_message(message.chat.id, WeatherManager().get_weather_info())
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
        bot.send_message(message.chat.id, WeatherManager().get_weather_info())
    elif ('выдай неопознанные' in message.text.lower()) and db.is_admin_id(message.from_user.id):
        bot.send_message(message.chat.id, db.get_unknown_massage_info())
    elif ('очисти неопознанные' in message.text.lower()) and db.is_admin_id(message.from_user.id):
        bot.send_message(message.chat.id, db.delete_all_unknown_messages())
    elif ('дай ссылку на себя' in message.text.lower() or 'дай свою ссылку' in message.text.lower()) \
            and db.is_admin_id(db.is_admin_id(message.from_user.id)):
        bot.send_message(message.chat.id, 'http://t.me/svyat93_bot')
    else:
        # Если есть ответ от бота - присылаем юзеру, если нет - бот его не понял
        response = cm.get_bot_answer(message)
        if response:
            bot.send_message(chat_id=message.chat.id, text=response)
        else:
            db.set_unknown_message_info(message)
            bot.send_message(chat_id=message.chat.id, text='Я Вас не совсем понял!')


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
