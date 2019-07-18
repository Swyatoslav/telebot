import telebot

from bot_logging import LogManager

# Включим логирование
lm = LogManager()

# Создаем тестового бота - отправителя
sender_bot = telebot.TeleBot('840665994:AAH9G6SP8KvrRj_PADBa5ABa44gTBBUMwG8', threaded=False)


def start_sender():
    sender_bot.polling(none_stop=True, interval=1, timeout=120)


@sender_bot.message_handler(content_types=['text'])
@lm.log_message
def send_text(message):
    if message.text:
        sender_bot.send_message(message.chat.id, 'sender')


if __name__ == "__main__":
    start_sender()
