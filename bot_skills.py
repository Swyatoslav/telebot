import json
from datetime import date
from random import randint
from time import sleep

import apiai
import bs4
import requests
from telebot.types import ReplyKeyboardRemove

from bot_db import check_time
from bot_tools import BotButtons
from functions import send_message


class MasterOfWeather(object):
    """Класс, работающий с парсингом погоды (Мастер над погодой) """

    bb = BotButtons()
    cur_day = date.today().day

    today_elm = ".forecast-details>div:nth-child(1)"
    tomorrow_elm = '.forecast-details>div:nth-child(3)'

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

        send_message(bot, message.chat.id, info_msg1)
        db.set_weather_edit_mode(message.from_user.id, self.first_phase)
        send_message(bot, message.chat.id, info_msg2, reply_markup=self.bb.gen_underline_butons(self.btn1, self.btn2))

    @check_time
    def _first_phase_to_set_place(self, message, db, bot):
        """Метод переводит пользователя с 1 фазы настройки на 2 фазу
        (согласие начать искать город или отказ от настроек)
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        info_msg1 = 'Хорошо, начнем настройку :)'
        info_msg2 = 'Введите, пожалуйста, название своего\n' \
                    'населенного пункта (без слов "Город", "Деревня" и тп.)\n\n' \
                    'Прошу вас вводить название без ошибок :)'
        info_msg3 = 'Вы находитесь в режиме настройки погоды. Прервать настройку?'

        if self.btn2 in message.text:
            db.set_weather_edit_mode(message.from_user.id, self.second_phase)
            send_message(bot, message.chat.id, info_msg1)
            send_message(bot, message.chat.id, info_msg2, reply_markup=self.bb.gen_underline_butons(self.btn1))
        else:
            send_message(bot, message.chat.id, info_msg3,
                             reply_markup=self.bb.gen_underline_butons(self.btn1, self.btn2))

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
            send_message(bot, message.chat.id, info_msg1, reply_markup=self.bb.gen_underline_butons(self.btn1))
        elif len(result) > 1:  # найдено несколько результатов
            tmp_table = db.create_tmp_table_for_search_place(message.from_user.id)  # создаем временную таблицу
            db.set_tmp_result_of_search_weather_place(tmp_table, result)  # записываем результаты во временную таблицу
            db.set_weather_edit_mode(message.from_user.id, self.third_phase)  # переходим к фазе выбора нужного места
            send_message(bot, message.chat.id, info_msg2, reply_markup=self.bb.gen_underline_butons('Моего здесь нет'))
            result_list = db.get_all_info_from_tmp_weather_places(tmp_table)

            # формируем сообщение с вариантами выбора из найденных результатов поиска
            result_msg = ''
            for res_line in result_list:

                # Случай, когда найдено слишком много совпадений
                if int(res_line[0]) > 200:
                    db.set_weather_edit_mode(message.from_user.id, self.second_phase)
                    send_message(bot, message.chat.id, 'Найдено более 200 совпадений, уточните поиск.'
                                                      '\nВведите ещё раз название населенного пункта')
                    return
                else:
                    result_msg += '{}. {}, {}\n'.format(res_line[0], res_line[3], res_line[2])

            # Если сообщение вышло слишком длинное, дробим его на несколько
            if len(result_msg) > 4096:
                for x in range(0, len(result_msg), 4096):
                    send_message(bot, message.chat.id, result_msg[x:x + 4096])
            else:
                send_message(bot, message.chat.id, result_msg)

        else:
            send_message(bot, message.chat.id, '{} ({}), верно?'.format(result[0][2], result[0][1]),
                             reply_markup=self.bb.gen_underline_butons('Верно', 'Неверно'))

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
                send_message(bot, message.chat.id, info_msg1)
        elif 'моего здесь нет' in message.text.lower():
            db.set_weather_edit_mode(message.from_user.id, self.second_phase)
            send_message(bot, message.chat.id, info_msg2)
        else:
            send_message(bot, message.chat.id, info_msg3)

    @check_time
    def _set_place_id_and_complete_weather_mode(self, message, db, bot, result_info, tmp_table):
        """Метод записывает id места пользователю и завершает настройку погоды
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        :param result_info - вся информация по нужному месту
        :param tmp_table - название временной таблицы
        """

        info_msg = 'Настройка успешно завершена :)\nСохранено: {}, {}\nВыберите нужную кнопку\n'.format(
            result_info[3], result_info[2])

        db.set_place_id_to_user(result_info[1], message.from_user.id)  # Записываем id места юзеру в таблицу
        db.set_weather_edit_mode(message.from_user.id, None)  # Закрываем режим настройки
        send_message(bot, message.chat.id, info_msg,
                         reply_markup=self.bb.gen_underline_butons('Погода сегодня', 'Погода завтра'))
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
            send_message(bot, message.chat.id, info_msg, reply_markup=ReplyKeyboardRemove())
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
        snow = u'\U00002744'
        hot = u'\U0001F525'
        drop = u'\U0001F4A7'

        weather_query = {'Облачно с прояснениями': fewClouds,
                         'Малооблачно': fewClouds,
                         'Небольшой дождь': rain,
                         'Дождь': rain,
                         'Ясно': clearSky,
                         'Пасмурно': clouds,
                         'Ливень': thunderstorm,
                         'Небольшой снег': snow,
                         'Снег': f'{snow} {snow}',
                         'Дождь со снегом': f'{drop} {snow}'
                         }

        if not weather_query.get(condition):
            return ''

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


class NotesManager(object):
    """Менеджер по работе с заметками"""

    bb = BotButtons()
    head = 'Заголовок заметки'
    body = 'Тело заметки'
    menu = 'Меню'
    none = None

    def notes_mode(self, message, db, bot):
        """Режим заметок"""

        menu_buttons = ('Создать заметку', 'Показать заметки', 'Выйти из заметок')
        menu_text = 'Вы находитесь в меню заметок'

        stage = db.get_notes_mode_stage(message.from_user.id)

        if message.text.lower() in ['выйти из заметок', 'прервать']:
            db.set_notes_mode_stage(message.from_user.id, self.none)
            send_message(bot, message.from_user.id, 'Работа с заметками окончена :)', reply_markup=ReplyKeyboardRemove())

            return

        elif 'меню' in message.text.lower():
            db.set_notes_mode_stage(message.from_user.id, self.menu)
            send_message(bot, message.from_user.id, menu_text, reply_markup=self.bb.gen_underline_butons(*menu_buttons))

            return

        elif message.text.lower() == 'создать заметку' and stage not in [self.head, self.body]:
            note_text = 'Пожалуйста, введите заголовок заметки (не более 50 символов)'
            note_buttons = ('Меню', 'Показать заметки', 'Выйти из заметок')

            send_message(bot, message.from_user.id, note_text, reply_markup=self.bb.gen_underline_butons(*note_buttons))
            db.set_notes_mode_stage(message.from_user.id, self.head)

            return

        elif message.text.lower() == 'показать заметки':
            self.get_note_list(message, db, bot)
            return

        stage = db.get_notes_mode_stage(message.from_user.id)

        if not stage:
            self.welcome_stage(message, db, bot)

        elif stage == 'Меню':
            self.menu_stage(message, db, bot)

        elif stage == 'Заголовок заметки':
            self.head_note_stage(message, db, bot)

        elif stage == 'Тело заметки':
            self.body_note_stage(message, db, bot)

    def welcome_stage(self, message, db, bot):
        """Первый вход в заметки"""

        welcome_text = 'Здесь вы можете создавать, просматривать, редактировать \nи удалять свои заметки'
        buttons = ('Создать заметку', 'Показать заметки', 'Выйти из заметок')

        send_message(bot, message.from_user.id, welcome_text, reply_markup=self.bb.gen_underline_butons(*buttons))
        db.set_notes_mode_stage(message.from_user.id, self.menu)

        return

    def menu_stage(self, message, db, bot):
        """Стадия 'Меню'"""

        note_text = 'Пожалуйста, введите заголовок заметки (не более 50 символов)'
        buttons = ("Создать заметку", 'Показать заметки', "Выйти из заметок")

        if message.text.lower() == 'создать заметку':
            send_message(bot, message.from_user.id, note_text, reply_markup=self.bb.gen_underline_butons(*buttons))
            db.set_notes_mode_stage(message.from_user.id, self.head)

            return

        else:
            send_message(bot, message.from_user.id, 'Вы находитесь в меню заметок',
                         reply_markup=self.bb.gen_underline_butons(*buttons))
            return

    def head_note_stage(self, message, db, bot):
        """Стадия 'Заголовок заметки'"""

        buttons = ("Меню", "Выйти из заметок")
        attention_head = 'Заголовок заметки не может быть пустым или превышать размер 50 символов.\n' \
                         'Пожалуйста, введите заголовок еще раз'
        body_text = 'Введите тело заметки (Не более 500 символов)'

        body_button = 'Сохранить пустую заметку'

        if len(message.text) > 50 or self._is_only_whitespaces(message.text):
            send_message(bot, message.from_user.id, attention_head, reply_markup=self.bb.gen_underline_butons(*buttons))

            return

        else:
            db.save_note(message.from_user.id, message.text)
            db.set_notes_mode_stage(message.from_user.id, self.body)
            send_message(bot, message.from_user.id, body_text,
                         reply_markup=self.bb.gen_underline_butons(*buttons, second_row_button=body_button))

            return

    def body_note_stage(self, message, db, bot):
        """Стадия 'Тело заметки'"""

        buttons = ("Меню", "Выйти из заметок")
        menu_buttons = ('Создать заметку', 'Показать заметки', 'Выйти из заметок')
        body_button = 'Сохранить пустую заметку'

        attention_body = 'Содержимое заметки не может превышать 500 символов.'
        success_text = '*Заметка успешно сохранена!*'

        note_body = None if 'сохранить пустую заметку' in message.text.lower() else message.text

        if len(message.text) > 500:
            send_message(bot, message.from_user.id, attention_body,
                         reply_markup=self.bb.gen_underline_butons(*buttons, second_row_button=body_button))

            return

        else:
            db.update_note(message.from_user.id, body_text=note_body)
            db.set_notes_mode_stage(message.from_user.id, self.menu)
            send_message(bot, message.from_user.id, success_text,
                         reply_markup=self.bb.gen_underline_butons(*menu_buttons),
                         parse_mode='Markdown')

            return

    def get_note_list(self, message, db, bot):
        """Стадия 'Список заметок'"""

        note_list_text = '*Список заметок*'
        buttons = ("Меню", 'Создать заметку', "Выйти из заметок")
        list_buttons = ('Создать заметку', 'Меню', 'Выйти из заметок')

        sleep(0.7)
        send_message(bot, message.from_user.id, note_list_text, reply_markup=self.bb.gen_underline_butons(*buttons,
                     second_row_button='Показать заметки'),
                     parse_mode='Markdown')
        result = db.get_all_user_notes(message.from_user.id)

        if result:
            for index, note in enumerate(result):
                send_message(bot, message.chat.id, f'{index + 1}. *{note[1]}*',
                            reply_markup=self.bb.gen_inline_buttons(['Прочитать', f'rnote_{note[2]}'],
                                                                    ['Удалить', f'dnote_{note[2]}']),
                             parse_mode='Markdown')

        else:
            send_message(bot, message.chat.id, 'Заметки отсутствуют',
                         reply_markup=self.bb.gen_underline_butons(*list_buttons))

    def _is_only_whitespaces(self, text):
        """Метод проверки сообщения на пробелы
        ":param text - текст сообщения пользователя
        """

        is_only_whitespaces = True
        for char in text:
            if char != ' ':
                is_only_whitespaces = False


        return is_only_whitespaces


class RandomManager(object):
    """Менеджер по работе с модом random five"""

    bb = BotButtons()

    def random_five_mode(self, message, db, bot):
        """Мод random five - поиск и выдача 5 случайных чисел диапазона, в случае
        если конечное значение диапазона передано корректно"""

        if message.text.isdigit():
            if '.' in message.text:
                send_message(bot, message.chat.id, 'Пожалуйста, введите целое число',
                                 reply_markup=self.bb.gen_underline_butons('Прервать random_5'))
                return

            elif int(message.text) <= 0 or message.text[0] == '0':
                send_message(bot, message.chat.id, 'Пожалуйста, введите положительное целое число',
                                 reply_markup=self.bb.gen_underline_butons('Прервать random_5'))
                return

            elif len(message.text) > 15:
                send_message(bot, message.chat.id, 'Слишком большой диапазон, укажите меньше',
                                 reply_markup=self.bb.gen_underline_butons('Прервать random_5'))
                return
            elif int(message.text) < 5:
                send_message(bot, message.chat.id, 'Введите число больше 4',
                                 reply_markup=self.bb.gen_underline_butons('Прервать random_5'))
            else:
                db.set_random_five_mode(message.from_user.id, None)
                result = self._get_random_five(message.text)
                send_message(bot, message.chat.id, '5 случайных чисел: {}, {}, {}, {}, {}'.format(*result),
                                 reply_markup=ReplyKeyboardRemove())

        elif 'прервать' in message.text.lower():
            db.set_random_five_mode(message.from_user.id, None)
            send_message(bot, message.chat.id, 'Прерывание режима random_5',
                             reply_markup=ReplyKeyboardRemove())
        else:
            send_message(bot, message.chat.id, 'Ошибка: нужно положительное целое число для границы диапазона',
                             reply_markup=self.bb.gen_underline_butons('Прервать random_5'))

    def _get_random_five(self, end_range):
        """Метод генерирует пять случайных чисел в диапазоне
        :param end_range - граница диапазона
        """

        numbers = list()

        numbers.append(randint(1, int(end_range)))
        while len(numbers) < 5:
            random_number = randint(1, int(end_range))
            if random_number not in numbers:
                numbers.append(random_number)

        return sorted(numbers)
