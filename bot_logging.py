import logging
import sys

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
