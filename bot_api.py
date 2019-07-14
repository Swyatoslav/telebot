import time
import os
import telebot

from bot_logging import LogManager
from bot_skills import WeatherManager, CommunicationManager

# Прочитаем токен
token_path = 'C:\\Projects'
token = None
with open(os.path.join(token_path, 'token.txt'), 'r') as token_file:
    token = token_file.read()


lm = LogManager()
# lm.start_logging()
bot = telebot.TeleBot(token)
hello_message = 'Привет!\nЯ бета версия умного бота'
help_message = 'Вот что я пока умею:\n' \
               '\n' \
               'Отвечать на приветствие\n' \
               'Отвечать на команду "Пока"\n' \
               'Говорить погоду /weather\n\n' \
               'Для повтора подсказок введите\n /help'
cm = CommunicationManager()


@bot.message_handler(commands=['start', 'help', 'weather'])
@lm.log_message
def start_message(message):
    if '/start' in message.text or '/help' in message.text:
        bot.send_message(message.chat.id, cm.say_hello())
        bot.send_message(message.chat.id, help_message)
    elif '/weather' in message.text:
        bot.send_message(message.chat.id, 'Погоди, спрошу у Яндекса')
        bot.send_message(message.chat.id, WeatherManager().get_weather_info())


@bot.message_handler(content_types=['text'])
@lm.log_message
def send_text(message):
    time.sleep(0.5)
    if cm.is_hello(message.text):
        bot.send_message(message.chat.id, cm.say_hello())
    elif message.text == 'Пока':
        bot.send_message(message.chat.id, 'Прощай, человек')
    elif 'погод' in message.text.lower():
        bot.send_message(message.chat.id, 'Погоди, спрошу у Яндекса')
        bot.send_message(message.chat.id, WeatherManager().get_weather_info())
    else:
        time.sleep(1)
        bot.send_message(message.chat.id, 'Кажется, меня такому не учили :(')
        time.sleep(0.5)
        bot.send_message(message.chat.id, help_message)


bot.polling()

while True:  # Don't end the main thread.
    pass
