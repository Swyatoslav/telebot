import telebot
from bot_logging import LogManager
import time


LogManager().start_logging()
bot = telebot.TeleBot('820045015:AAGT5vZMYrXdynheOm9ZLCbdWYY3WbDximI')
help_message = 'Привет!\n' \
               'Я бета версия умного бота.\n' \
               'Вот что я пока умею:\n' \
               '\n' \
               'Отвечать на команду "Привет"\n' \
               'Отвечать на команду "Пока"'


@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    time.sleep(1)
    bot.send_message(message.chat.id, help_message)


@bot.message_handler(content_types=['text'])
def send_text(message):
    time.sleep(1)
    if message.text == 'Привет':
        bot.reply_to(message, 'Привет, мой создатель')
    elif message.text == 'Пока':
        bot.reply_to(message, 'Прощай, создатель')




bot.polling()
