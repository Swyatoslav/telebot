from bot_logging import LogManager
from functions import send_message
from telebot.types import ReplyKeyboardRemove
from bot_tools import BotButtons
from time import sleep
import datetime


class CallsManager(object):
    """Класс для обработки call запросов"""

    lm = LogManager()
    bb = BotButtons()

    def report_calls(self, db, bot, call):
        """Call запросы отчетов
        :param db - экземпляр бд
        :param bot - экземпляр бота
        :param call - call данные
        """

        call_data = call.data.split('_')
        if call_data[0] == 'savereport':
            result = db.get_report_info(call_data[1])
            if result:
                send_message(bot, '344950989', '{}{}'.format(result[0], result[1]),
                                 reply_markup=self.lm.gen_report_buttons(call_data[1], 'delreport'))
            else:
                bot.answer_callback_query(call.id, "Данный отчет удалён")

        elif call_data[0] == 'delreport':
            db.delete_report(call_data[1])
            bot.answer_callback_query(call.id, "Отчет {} успешно удален".format(call_data[1]))

    def call_trigger(self, db, bot, call, mode):
        """Метод для распределения call Запросов в программах
        :param db - экземпляр бд
        :param bot - экземпляр бота
        :param call - call данные
        :param mode - информация о запущенном моде
        """

        if 'космический квест' in mode.lower():
            self.space_quest_calls(db, bot, call)
        elif 'заметки':
            self.notes_calls(db, bot, call)

    def space_quest_calls(self, db, bot, call):
        """Мето для обработки call запросов игры Космический квест
        :param db - экземпляр бд
        :param bot - экземпляр бота
        :param call - call данные
        """

        if call.data == 'start':
            db.set_space_quest_mode(call.from_user.id, 'Игра')
            send_message(bot, call.from_user.id, 'Начнем наш квест.')

        elif call.data == 'later':
            db.set_space_quest_mode(call.from_user.id, None)
            send_message(bot, call.from_user.id, 'Хорошо, сыграем в другой раз')

    def notes_calls(self, db, bot, call):
        """Мето для обработки call запросов заметок
        :param db - экземпляр бд
        :param bot - экземпляр бота
        :param call - call данные
        """

        buttons = ('Меню', 'Выйти из заметок')
        note_id = int(call.data.split('_')[1])
        note_info = db.get_note_by_id(note_id)

        if 'rnote' in call.data:
            sleep(0.3)

            if note_info:
                note_date = note_info[0].strftime('%Y.%m.%d %H:%M')
                note_head = note_info[1]
                note_body = note_info[2]
                send_message(bot, call.from_user.id, f'*{note_head}*\nВремя создания: {note_date}',
                             reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')

                if note_body:
                    sleep(0.5)
                    send_message(bot, call.from_user.id, f'_{note_body}_',
                                 reply_markup=self.bb.gen_underline_butons(*buttons),
                                 parse_mode='Markdown')

            else:
                bot.answer_callback_query(call.id, 'Заметка была удалена')
            
        elif 'dnote' in call.data:
            
            if note_info:
                note_head = note_info[1]
                db.remove_note_by_id(note_id)
                bot.answer_callback_query(call.id, f'Заметка "{note_head}" удалена')
            else:
                bot.answer_callback_query(call.id, 'Заметка уже удалена')

        elif 'enote' in call.data:
            if note_info:
                note_head = note_info[1]
                db.remove_note_by_id(note_id)
                bot.answer_callback_query(call.id, f'Заметка "{note_head}" удалена')
            else:
                bot.answer_callback_query(call.id, 'Заметка уже удалена')

