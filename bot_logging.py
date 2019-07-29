import logging
import sys
from datetime import datetime
import os

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

    @staticmethod
    def write_log_file(func_name, exec_time, user_msg, user_id):
        """Метод пишет логи в logs.txt
        :param user_id - id пользователя
        :param func_name - название метода
        :param exec_time - время выполнения метода
        :param user_msg - запрос пользователя
        """

        log_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'logs.txt')
        func_name_str = '{}{}{}'.format(func_name, (40-len(func_name)) * ' ', '|')
        exec_time_str = '   {}с{}{}'.format(exec_time, (10-len(str(exec_time))) * ' ', '|')
        user_id_str = '   {}{}{}'.format(user_id, (12-len(str(user_id))) * ' ', '|')
        user_msg = '{}'.format(user_msg)

        head_func_name = 14*' ' + 'METHOD_NAME' + 15*' ' + '|'
        head_exec_time = 'EXECUTION_TIME|'
        head_id = '    USER_ID    |'
        head_msg = 'USER_MESSAGE'

        head_datetime = '    CALL_DATE    |'
        time_log = '{}|'.format(datetime.now().strftime("%m-%d-%y %H:%M:%S"))

        empty_file = False
        with open(log_path, "r", encoding='utf-8') as log_file:
            read_file = [line for line in log_file]
            if not read_file:
                empty_file = True

        with open(log_path, "a", encoding='utf-8') as log_file:
            if empty_file:
                log_file.write('{}{}{}{}{}\n'.format(head_func_name, head_datetime, head_exec_time, head_id, head_msg))
                log_file.write(102 * '=' + '\n')
            log_file.write('{}{}{}{}{}\n'.format(func_name_str, time_log, exec_time_str, user_id_str, user_msg))


