import logging
import sys
from datetime import datetime

import telebot


class LogManager:
    """Класс отвечает за вывод логов действий с ботом в консоль"""

    logger = telebot.logger
    formatter = logging.Formatter('[%(asctime)s] %(thread)d {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                                  '%m-%d %H:%M:%S')

    def start_logging(self):
        """Метод включает логироование"""

        ch = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(ch)
        self.logger.setLevel(logging.DEBUG)  # or use logging.INFO
        ch.setFormatter(self.formatter)

    def log_message(self, func):
        """Метод логирует сообщение, переданное боту"""

        def wrapper(message):
            t = datetime.now()
            time_log = t.strftime("[%m-%d-%y %H:%M:%S]")
            if message.from_user.last_name is None:
                last_user_name = ''
            else:
                last_user_name = message.from_user.last_name

            user_info = [message.from_user.first_name, last_user_name, message.from_user.id]

            print('{0}  USER: [{1} {2}]  USER_ID: [{3}]  MESSAGE: [{4}]'.format(
                time_log, user_info[0], user_info[1], user_info[2], message.text))
            func(message)

        return wrapper
