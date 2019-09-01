import logging
import sys
from datetime import datetime
import os
import traceback
import time
import telebot
from telebot.types import ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup


class LogManager:
    """Класс отвечает за вывод логов действий с ботом в консоль"""

    logger = telebot.logger
    formatter = logging.Formatter('[%(asctime)s] %(thread)d {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
                                  '%m-%d %H:%M:%S')

    def gen_report_buttons(self, report_id, operation):
        """Метод создает кнопку с вопросом о записи информации в бд"""

        markup = InlineKeyboardMarkup()
        markup.row_width = 1

        oper_txt = 'Показать' if operation == 'savereport' else 'Удалить'
        markup.add(InlineKeyboardButton(oper_txt + " отчет", callback_data='{}_{}'.format(operation, report_id)))

        return markup

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

    def send_error_report(self, bot, db, message, err):
        """Отсылает разработчику отчет об ошибке, полученной в результате действий пользователя
        :param bot - экземпляр класса telebot
        :param db - экземпляр БД
        :param message - сообщение пользователя с полной информацией
        :param err - текст ошибки
        """

        uid = message.from_user.id

        bot.send_message(message.chat.id, 'Прошу прощения, в программе возникла ошибка.\n'
                                          'Мой создатель обязательно с ней разберется.\n'
                                          'До тех пор пожалуйста, не повторяйте действие,\n'
                                          'приведшее к ошибке. Спасибо :)',
                                          reply_markup=ReplyKeyboardRemove())
        user_name = db.get_user_name(uid)[0]
        err_report = 'MESSAGE: {}\nUSER_NAME: {}\nCHAT_ID: {}\n'.format(message.text, user_name, message.chat.id)

        weather_place = db.is_weather_place_set(uid)
        if weather_place:
            err_report += 'WEATHER PLACE: {}\n'.format(weather_place)

        # информация про random 5
        if db.is_random_five_mode(uid):
            db.set_random_five_mode(uid, None)
            err_report += 'Random 5 mode: True\n'
            time.sleep(0.5)
            bot.send_message(message.chat.id, '*Аварийный выход из мода Random 5*', reply_markup=ReplyKeyboardRemove(),
                             parse_mode='Markdown')

        # информация про мод настройки погоды
        elif db.get_weather_edit_mode_stage(uid):
            weather_stage = db.get_weather_edit_mode_stage(uid)
            db.set_weather_edit_mode(uid, None)
            err_report += 'Weather setup mode: True\nWeather setup stage: {}\n'.format(weather_stage)
            time.sleep(0.5)
            bot.send_message(message.chat.id, '*Аварийный выход из настройки погоды*', reply_markup=ReplyKeyboardRemove(),
                             parse_mode='Markdown')

        # информация про игру Города
        elif db.get_game_cities_mode_stage(uid):
            game_cities_stage = db.get_game_cities_mode_stage(uid)
            db.set_game_cities_mode(uid, None)
            err_report += 'Game cities mode: True\nGame cities stage: {}\n'.format(game_cities_stage)
            time.sleep(0.5)
            bot.send_message(message.chat.id, '*Аварийный выход из игры "Города мира"*', reply_markup=ReplyKeyboardRemove(),
                             parse_mode='Markdown')

        # информация про игру Столицы
        elif db.get_game_capitals_mode_stage(uid):
            game_capitals_stage = db.get_game_capitals_mode_stage(uid)
            db.set_game_capitals_mode(uid, None)
            err_report += 'Game capitals mode: True\nGame capitals stage: {}\n'.format(game_capitals_stage)
            time.sleep(0.5)
            bot.send_message(message.chat.id, '*Аварийный выход из игры "Столицы мира"*', reply_markup=ReplyKeyboardRemove(),
                             parse_mode='Markdown')

        # Формирование stacktrace
        err_stacktrace = ''.join(traceback.format_exception(etype=type(err), value=err, tb=err.__traceback__))
        if len(err_stacktrace) > 3950:
            err_stacktrace = '...{}'.format(err_stacktrace[-1:-3950])

        # Отправка сообщения об ошибке в чат админа
        report_id = db.save_report(uid, err_stacktrace, err_report)
        bot.send_message('344950989', '*Пользователь {} получил ошибку\n\n*'.format(user_name),
                         reply_markup=self.gen_report_buttons(report_id, 'savereport'),
                         parse_mode='Markdown')