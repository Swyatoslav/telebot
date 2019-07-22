import json
from datetime import date

import apiai
import bs4
import requests
from telebot import types


class MasterOfWeather:
    """Класс, работающий с парсингом погоды (Мастер над погодой)"""

    cur_day = date.today().day

    today_elm = ".forecast-details>dd:nth-child(2)"
    tomorrow_elm = '.forecast-details>dd:nth-child(5)'

    button1 = 'Прервать настройку'
    button2 = 'Продолжить настройку'

    first_phase = 'Начало настройки'
    second_phase = 'Поиск города'
    third_phase = 'Выбор города'

    def _hello_from_mow(self, message, db, bot):
        """Метод здоровается с пользователем и включает 1 фазу редактирования погоды"""

        mow_hello_msg = 'Здравствуйте :) Меня зовут Мастер над погодой.\n' \
                        'Давайте определим город, в котором вам интересна погода.\n' \
                        'Это делается всего один раз, но при желании\n' \
                        'вы сможете потом поменять город командой /new_weather '

        bot.send_message(message.chat.id, mow_hello_msg)
        db.set_weather_edit_mode(message.from_user.id, self.first_phase)
        bot.send_message(message.chat.id, 'Выберите, пожалуйста, нужную кнопку :)',
                         reply_markup=self.set_buttons(self.button1, self.button2))

    def _first_phase_to_set_place(self, message, db, bot):
        """Метод переводит пользователя с 1 фазы настройки на 2 фазу
        (согласие начать искать город или отказ от настроек)
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        if self.button2 in message.text:
            db.set_weather_edit_mode(message.from_user.id, self.second_phase)
            bot.send_message(message.chat.id, 'Хорошо, начнем настройку :)')
            bot.send_message(message.chat.id, 'Введите, пожалуйста, название своего\n'
                                              'населенного пункта (без слов "Город", "Хутор" и тп.)\n\n'
                                              'Прошу вас вводить название без ошибок :)',
                                              reply_markup=self.set_buttons(self.button1))
        else:
            bot.send_message(message.chat.id, 'Вы находитесь в режиме настройки погоды. Прервать настройку?',
                             reply_markup=self.set_buttons(self.button1, self.button2))

    def _second_phase_to_set_place(self, message, db, bot):
        """Метод ищет для пользователя город, в котором тот хочет видеть погоду
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        if 'верно' in message.text.lower() and not 'не' in message.text.lower():
            tmp_result = db.get_info_from_tmp_weather_places('admin.user_{}_tmp'.format(message.from_user.id))
            db.set_place_id_to_user(tmp_result[0][0], message.from_user.id)
            db.set_weather_edit_mode(message.from_user.id, None)
            bot.send_message(message.chat.id, 'Настройка успешно завершена :)\n'
                                              'Теперь можете спрашивать меня о погоде \n'
                                              'на сегодня и на завтра\n')
            return

        result = db.get_place_info_by_name(message.text)
        if not result:
            bot.send_message(message.chat.id, 'Возможно, название населенного пункта введено неверно.\n'
                                              'Попробуйте ещё раз.',
                                               reply_markup=self.set_buttons(self.button1))
        elif len(result) > 1:
            tmp_table = db.create_tmp_table_for_search_place(message.from_user.id)
            db.set_tmp_result_of_search_weather_place(tmp_table, result)
            db.set_weather_edit_mode(message.from_user.id, '')
            bot.send_message(message.chat.id, 'Найдено более одного совпадения\n'
                                              'Пожалуйста, посмотрите результаты\n'
                                              'и введите номер строки с верным результатом.')

        else:
            bot.send_message(message.chat.id, '{} ({}), верно?'.format(result[0][2], result[0][1]),
                                              reply_markup=self.set_buttons('Верно', 'Неверно'))
            # Запись результатов поиска во временную бд
            tmp_table = db.create_tmp_table_for_search_place(message.from_user.id)
            db.set_tmp_result_of_search_weather_place(tmp_table, result)

    def _third_phase_to_set_place(self, message, db, bot):
        """Метод предлагает пользователю выбор из нескольких городов, найденных по запросу
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """





    def weather_place_mode(self, message, db, bot):
        """Режим настройки места для вывода погоды пользователю
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        if self.button1 in message.text or 'позже' in message.text:
            bot.send_message(message.chat.id, 'Хорошо, настроим в другой раз :)')
            db.set_weather_edit_mode(message.from_user.id, None)
            return

        phase = db.get_weather_edit_mode_stage(message.from_user.id)
        if not phase:
            self._hello_from_mow(message, db, bot)
        elif phase == self.first_phase:
            self._first_phase_to_set_place(message, db, bot)
        elif phase == self.second_phase:
            self._second_phase_to_set_place(message, db, bot)
        elif phase == self.third_phase:
            self._third_phase_to_set_place(message, db, bot)

    def get_weather_info(self, db, message):
        """Метод позволяет спарсить погоду сайта Яндекс
        :param message - сообщение пользователя
        """

        day_parts = ['Утро', 'День', 'Вечер', 'Ночь']
        day_txt = 'завтра' if 'завтра' in message.text.lower() else 'сегодня'
        place_url, place_name = db.get_place_info_of_user_by_user_id(message.from_user.id)

        weather = [self._parse_weather_info(day_part, day_txt, place_url) for day_part in day_parts]
        weather.insert(0, day_txt)  # День, когда смотрим погоду
        weather.insert(0, place_name)

        return '{0}: {1} погода такая\n{2}{3}{4}{5}'.format(*weather)

    def set_buttons(self, *buttons):
        """Метод размещает под панелью клавиатуры одну или несколько кнопок
        :param buttons - текст кнопок
        """

        markup = types.ReplyKeyboardMarkup(row_width=len(buttons), one_time_keyboard=True, resize_keyboard=True)
        my_buttons = [types.KeyboardButton(button_text) for button_text in buttons]
        markup.add(*my_buttons)

        return markup

    def _parse_weather_info(self, day_part, day_txt, place_url):
        """Вспомогательный метод, парсит погоду
        :param day_part - Время дня (Утро/День/Вечер/Ночь)
        :param day_txt - на какой день выводить погоду (сегодня/завтра)
        :param place_url - url, по которому находим населенный пункт
        """

        day_elm = self.today_elm if day_txt == 'сегодня' else self.tomorrow_elm

        weather_site = '{}/details#{}'.format(place_url, self.cur_day)
        response = requests.get(weather_site)
        bs = bs4.BeautifulSoup(response.text, "html.parser")

        # Температуры на утро, день, вечер и ночь в яндексе идут один за другим
        day_query = {'Утро': '1', 'День': '2', 'Вечер': '3', 'Ночь': '4'}
        tmp_value = day_query[day_part]
        day_part_elm = ' .weather-table__body>tr:nth-child({})'.format(tmp_value)  # Локатор строки времени дня

        # Ищем температуру
        temp_elm = ' .weather-table__body-cell_type_feels-like .temp .temp__value'
        temp_join = "{}{}{}".format(day_elm, day_part_elm, temp_elm)
        temp_str = bs.select(temp_join)[0].get_text()

        # Ищем погодные условия
        condition_elm = ' .weather-table__body-cell_type_condition'
        condition_join = '{}{}{}'.format(day_elm, day_part_elm, condition_elm)
        condition_str = bs.select(condition_join)[0].get_text()
        condition_emodji = self._get_emoji(condition_str, day_part)

        return '\n{}: {} {}'.format(day_part, temp_str, condition_emodji)

    def _get_emoji(self, condition, day_part):
        """Возвращает смайлик, соответствующий погодным условиям
        :param condition - погодные условия
        :param day_part - Время дня
        """

        thunderstorm = u'\U0001F4A8'
        rain = u'\U00002614'
        clearSky = u'\U00002600' if day_part != 'Ночь' else u'\U0001F303'
        fewClouds = u'\U000026C5' if day_part != 'Ночь' else u'\U0001F303'
        clouds = u'\U00002601'
        hot = u'\U0001F525'

        weather_query = {'Облачно с прояснениями': fewClouds,
                         'Малооблачно': fewClouds,
                         'Небольшой дождь': rain,
                         'Дождь': rain,
                         'Ясно': clearSky,
                         'Пасмурно': clouds,
                         'Ливень': thunderstorm,
                         }

        return weather_query[condition]


class CommunicationManager:
    """Класс для общения с людьми"""

    def get_bot_answer(self, message):
        """Метод отвечает на сообщение пользователя
        :param message - сообщение пользователя
        """

        request = apiai.ApiAI('9b5ef6f406254c3e8e38908ae1196e29').text_request()  # Токен API к Dialogflow
        request.lang = 'ru'  # На каком языке будет послан запрос
        request.session_id = 'small-talk-bmnycd'  # ID Сессии диалога (нужно, чтобы потом учить бота)
        request.query = message.text  # Посылаем запрос к ИИ с сообщением от юзера
        response_json = json.loads(request.getresponse().read().decode('utf-8'))

        return response_json['result']['fulfillment']['speech']  # Разбираем JSON и вытаскиваем ответ

    def is_weather_question(self, message):
        """Метод проверяет, не о погоде ли спросили бота
        :param message сообщение боту
        """

        weather_phrases = ['погода', ' погоде', 'погоду', 'погодой', 'погода']

        for phrase in weather_phrases:
            if phrase in message.lower():
                return True

        return False

    def is_skill_question(self, message):
        """Метод проверяет, не про возможности ли бота был задан вопрос
        :param message - сообщение юзера
        """

        skills_questions = ['что ты умеешь', 'что умеешь', 'что ещё умеешь', 'что еще умеешь', 'ты умеешь',
                            'твои функции', 'твои возможности', 'ты сможешь', 'ты можешь', 'ты ещё сможешь',
                            'ты еще сможешь', 'ты ещё можешь', 'ты еще можешь', 'ты мог бы', 'мог бы ты',
                            'твоя функция', 'твои навыки', 'чему ты обучен', 'ты обучен', 'что можешь',
                            'что могешь']

        for skill_question in skills_questions:
            if skill_question in message.text.lower():
                return True

        return False
