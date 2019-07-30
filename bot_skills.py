import json
from datetime import date

import apiai
import bs4
import requests
from telebot import types
from telebot.types import ReplyKeyboardRemove

from bot_db import check_time


class MasterOfWeather:
    """Класс, работающий с парсингом погоды (Мастер над погодой)"""

    cur_day = date.today().day

    today_elm = ".forecast-details>dd:nth-child(2)"
    tomorrow_elm = '.forecast-details>dd:nth-child(5)'

    btn1 = 'Прервать настройку'
    btn2 = 'Продолжить настройку'

    first_phase = 'Начало настройки'
    second_phase = 'Поиск города'
    third_phase = 'Выбор города'

    @check_time
    def _hello_from_mow(self, message, db, bot):
        """Метод здоровается с пользователем и включает 1 фазу редактирования погоды"""

        info_msg1 = 'Здравствуйте :) Меня зовут Мастер над погодой.\n' \
                    'Давайте определим город, в котором вам интересна погода.\n' \
                    'Это делается всего один раз, но при желании\n' \
                    'вы сможете потом поменять город командой /new_weather '
        info_msg2 = 'Выберите, пожалуйста, нужную кнопку :)'

        bot.send_message(message.chat.id, info_msg1)
        db.set_weather_edit_mode(message.from_user.id, self.first_phase)
        bot.send_message(message.chat.id, info_msg2, reply_markup=self.set_buttons(self.btn1, self.btn2))

    @check_time
    def _first_phase_to_set_place(self, message, db, bot):
        """Метод переводит пользователя с 1 фазы настройки на 2 фазу
        (согласие начать искать город или отказ от настроек)
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        info_msg1 = 'Хорошо, начнем настройку :)'
        info_msg2 = 'Введите, пожалуйста, название своего\n'\
                    'населенного пункта (без слов "Город", "Деревня" и тп.)\n\n'\
                    'Прошу вас вводить название без ошибок :)'
        info_msg3 = 'Вы находитесь в режиме настройки погоды. Прервать настройку?'

        if self.btn2 in message.text:
            db.set_weather_edit_mode(message.from_user.id, self.second_phase)
            bot.send_message(message.chat.id, info_msg1)
            bot.send_message(message.chat.id, info_msg2, reply_markup=self.set_buttons(self.btn1))
        else:
            bot.send_message(message.chat.id, info_msg3, reply_markup=self.set_buttons(self.btn1, self.btn2))

    @check_time
    def _second_phase_to_set_place(self, message, db, bot):
        """Метод ищет для пользователя город, в котором тот хочет видеть погоду
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        info_msg1 = 'Возможно, название населенного пункта введено неверно.\nПопробуйте ещё раз.'
        info_msg2 = 'Найдено несколько совпадений\nПосмотрите результаты и введите\nномер строки с верным результатом.'

        tmp_table = 'admin.user_{}_tmp'.format(message.from_user.id)

        if 'верно' in message.text.lower() and not 'не' in message.text.lower():
            tmp_result = db.get_some_info_from_tmp_weather_places(tmp_table)
            self._set_place_id_and_complete_weather_mode(message, db, bot, tmp_result, tmp_table)
            return

        result = db.get_place_info_by_name(message.text)
        if not result:  # результаты поиска отсутствуют
            bot.send_message(message.chat.id, info_msg1, reply_markup=self.set_buttons(self.btn1))
        elif len(result) > 1:  # найдено несколько результатов
            tmp_table = db.create_tmp_table_for_search_place(message.from_user.id)  # создаем временную таблицу
            db.set_tmp_result_of_search_weather_place(tmp_table, result)  # записываем результаты во временную таблицу
            db.set_weather_edit_mode(message.from_user.id, self.third_phase)  # переходим к фазе выбора нужного места
            bot.send_message(message.chat.id, info_msg2, reply_markup=self.set_buttons('Моего здесь нет'))
            result_list = db.get_all_info_from_tmp_weather_places(tmp_table)

            # формируем сообщение с вариантами выбора из найденных результатов поиска
            result_msg = ''
            for res_line in result_list:
                result_msg += '{}. {}, {}\n'.format(res_line[0], res_line[3], res_line[2])
            bot.send_message(message.chat.id, result_msg)
        else:
            bot.send_message(message.chat.id, '{} ({}), верно?'.format(result[0][2], result[0][1]),
                             reply_markup=self.set_buttons('Верно', 'Неверно'))
            # Запись результатов поиска во временную бд
            tmp_table = db.create_tmp_table_for_search_place(message.from_user.id)
            db.set_tmp_result_of_search_weather_place(tmp_table, result)

    @check_time
    def _third_phase_to_set_place(self, message, db, bot):
        """Метод предлагает пользователю выбор из нескольких городов, найденных по запросу
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        tmp_table = 'admin.user_{}_tmp'.format(message.from_user.id)
        info_msg1 = 'Указанной вами строки нет в предложенном списке..\nВведите номер ещё раз'
        info_msg2 = 'Возможно, тут какая-то ошибка..\nПроверьте правильность названия\n' \
                    'введенного места, и попробуйте\nнайти его ещё раз'
        info_msg3 = 'Пожалуйста, введите номер нужной строки'

        if message.text.isdigit():
            if int(message.text) in range(1, int(db.get_max_id_from_tmp_weather_places(tmp_table)[0] + 1)):
                tmp_result = db.get_some_info_from_tmp_weather_places(tmp_table, int(message.text))
                self._set_place_id_and_complete_weather_mode(message, db, bot, tmp_result, tmp_table)

            else:
                bot.send_message(message.chat.id, info_msg1)
        elif 'моего здесь нет' in message.text.lower():
            db.set_weather_edit_mode(message.from_user.id, self.second_phase)
            bot.send_message(message.chat.id, info_msg2)
        else:
            bot.send_message(message.chat.id, info_msg3)

    @check_time
    def _set_place_id_and_complete_weather_mode(self, message, db, bot, result_info, tmp_table):
        """Метод записывает id места пользователю и завершает настройку погоды
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        :param result_info - вся информация по нужному месту
        :param tmp_table - название временной таблицы
        """

        info_msg='Настройка успешно завершена :)\nСохранено: {}, {}\nВыберите нужную кнопку\n'.format(
                             result_info[3], result_info[2])

        db.set_place_id_to_user(result_info[1], message.from_user.id)  # Записываем id места юзеру в таблицу
        db.set_weather_edit_mode(message.from_user.id, None)  # Закрываем режим настройки
        bot.send_message(message.chat.id, info_msg, reply_markup=self.set_buttons('Погода сегодня', 'Погода завтра'))
        db.drop_tmp_table(tmp_table)

    @check_time
    def weather_place_mode(self, message, db, bot):
        """Режим настройки места для вывода погоды пользователю
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        info_msg = 'Хорошо, настроим в другой раз :)'

        if self.btn1 in message.text or 'позже' in message.text:
            bot.send_message(message.chat.id, info_msg, reply_markup=ReplyKeyboardRemove())
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

    @check_time
    def get_weather_info(self, db, message):
        """Метод позволяет спарсить погоду сайта Яндекс
        :param message - сообщение пользователя
        """

        day_parts = ['Утро', 'День', 'Вечер', 'Ночь']
        day_txt = 'завтра' if 'завтра' in message.text.lower() else 'сегодня'
        place_url, place_name, region_name = db.get_place_info_of_user_by_user_id(message.from_user.id)

        weather_site = '{}/details#{}'.format(place_url, self.cur_day)
        response = requests.get(weather_site)
        bs = bs4.BeautifulSoup(response.text, "html.parser")

        weather = [self._parse_weather_info(day_part, day_txt, bs) for day_part in day_parts]
        weather.insert(0, place_name)  # Название города
        weather.insert(1, region_name)  # Название области
        weather.insert(2, day_txt)  # День, когда смотрим погоду

        return '{0} ({1})\nПогода на {2}\n{3}{4}{5}{6}'.format(*weather)

    @check_time
    def set_buttons(self, *buttons):
        """Метод размещает под панелью клавиатуры одну или несколько кнопок
        :param buttons - текст кнопок
        """

        markup = types.ReplyKeyboardMarkup(row_width=len(buttons), one_time_keyboard=True, resize_keyboard=True)
        my_buttons = [types.KeyboardButton(button_text) for button_text in buttons]
        markup.add(*my_buttons)

        return markup

    @check_time
    def _parse_weather_info(self, day_part, day_txt, bs):
        """Вспомогательный метод, парсит погоду
        :param day_part - Время дня (Утро/День/Вечер/Ночь)
        :param day_txt - на какой день выводить погоду (сегодня/завтра)
        :param bs - экземпляр bs, содержащий результат запроса к Яндекс.Погода
        """

        day_elm = self.today_elm if day_txt == 'сегодня' else self.tomorrow_elm

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

    @check_time
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

    @check_time
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

    @check_time
    def is_weather_question(self, message):
        """Метод проверяет, не о погоде ли спросили бота
        :param message сообщение боту
        """

        weather_phrases = ['погода', ' погоде', 'погоду', 'погодой', 'погода']

        for phrase in weather_phrases:
            if phrase in message.lower():
                return True

        return False

    @check_time
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
