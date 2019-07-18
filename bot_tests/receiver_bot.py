import telebot

from bot_logging import LogManager

# Включим логирование
lm = LogManager()

# Создаем тестового бота - получателя
receiver_bot = telebot.TeleBot('922589748:AAF_FC_W-FK2vyzqlJs9U3zioNL33OYAIhY', threaded=False)


def start_receiver():
    receiver_bot.polling(none_stop=True, interval=1, timeout=120)


@receiver_bot.message_handler(content_types=['text'])
@lm.log_message
def send_text(message):
    if message.text:
        receiver_bot.send_message(message.chat.id, 'receiver')
    # elif ('выдай неопознанные' in message.text.lower()) and db.is_admin_id(message.from_user.id):


if __name__ == "__main__":
    start_receiver()
