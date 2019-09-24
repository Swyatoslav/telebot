from bot_logging import LogManager


class CallsManager(object):
    """Класс для обработки call запросов"""

    lm = LogManager()

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
                bot.send_message('344950989', '{}{}'.format(result[0], result[1]),
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

    def space_quest_calls(self, db, bot, call):
        """Мето для обработки call запросов игры Космический квест
        :param db - экземпляр бд
        :param bot - экземпляр бота
        :param call - call данные
        """

        if call.data == 'start':
            db.set_space_quest_mode(call.from_user.id, 'Игра')
            bot.send_message(call.from_user.id, 'Начнем наш квест.')

        elif call.data == 'later':
            db.set_space_quest_mode(call.from_user.id, None)
            bot.send_message(call.from_user.id, 'Хорошо, сыграем в другой раз')