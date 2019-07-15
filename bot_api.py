import time
import os
import telebot
from bot_config import ConfigManager
import sys

from bot_logging import LogManager
from bot_skills import WeatherManager, CommunicationManager
from bot_db import DBManager


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
bot = telebot.TeleBot(cm.get('general', 'token'))
hello_message = 'Привет!\nЯ бета версия умного бота'
info_message = 'Вот что я пока умею:\n' \
               '\n' \
               'Отвечать на приветствие\n' \
               'Отвечать на прощание\n' \
               'Говорить погоду /weather\n\n' \
               'Для повтора подсказок введите\n /help'
cm = CommunicationManager()


@db.set_user_info
@bot.message_handler(commands=['start', 'help', 'weather', 'secret93'])
@lm.log_message
def start_message(message):
    if message.text in '/start':
        bot.send_message(message.chat.id, cm.say_hello())
        bot.send_message(message.chat.id, info_message)
    elif '/weather' in message.text:
        bot.send_message(message.chat.id, 'Погоди, спрошу у Яндекса')
        bot.send_message(message.chat.id, WeatherManager().get_weather_info())
    elif message.text in ['/help']:
        bot.send_message(message.chat.id, info_message)
    elif 'secret93' in message.text:
        bot.send_message(message.chat.id, 'Привет, Святослав')
        bot.send_message(message.chat.id, 'Твои инструменты: \nвыдай неопознанные\nочисти неопознанные')


@bot.message_handler(content_types=['text'])
@lm.log_message
@db.set_user_info
def send_text(message):
    time.sleep(0.5)
    if cm.is_hello(message.text):
        bot.send_message(message.chat.id, cm.say_hello())
    elif cm.is_goodbye(message.text):
        bot.send_message(message.chat.id, cm.say_goodbye())
    elif cm.is_weather_question(message.text):
        bot.send_message(message.chat.id, 'Погоди, спрошу у Яндекса')
        bot.send_message(message.chat.id, WeatherManager().get_weather_info())
    elif 'как дела' in message.text.lower() or 'как жизнь' in message.text.lower() or 'как твои дела' \
            in message.text.lower():
        bot.send_message(message.chat.id, 'Отлично! Как и у вас, надеюсь :)')
    # служебные
    elif 'выдай неопознанные' in message.text.lower():
        bot.send_message(message.chat.id, db.get_unknown_massage_info())
    elif 'очисти неопознанные' in message.text.lower():
        bot.send_message(message.chat.id, db.delete_all_unknown_messages())
    else:
        db.set_unknown_message_info(message)
        time.sleep(1)
        bot.send_message(message.chat.id, 'Кажется, меня такому не учили :(')
        time.sleep(0.5)
        bot.send_message(message.chat.id, 'Пойду жаловаться создателю на свою глупость')
        time.sleep(1.5)
        bot.send_message(message.chat.id, info_message)

# Команда для запуска бота
bot.polling()


while True:  # Don't end the main thread.
    pass
