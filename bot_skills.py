import random
from datetime import date

import bs4
import requests

import apiai
import json


class WeatherManager:
    """Класс, работающий с парсингом погоды"""

    today = date.today()
    cur_day = date.today().day
    weather_site = 'https://yandex.ru/pogoda/novosibirsk/details#{}'.format(cur_day)
    response = requests.get(weather_site)
    bs = bs4.BeautifulSoup(response.text, "html.parser")

    today_elm = ".forecast-details>dd:nth-child(2)"

    def get_weather_info(self):
        """Метод позволяет спарсить погоду сайта Яндекс
        Подсказки:
        # following-sibling - следующий элемент в DOM на том же уровне
        # ancestor:: - поиск предка

        """

        morning_weather = self._parse_weather_info('Утро')
        day_weather = self._parse_weather_info('День')
        evening_weather = self._parse_weather_info('Вечер')
        night_weather = self._parse_weather_info('Ночь')

        return 'Погода в Новосибирске сегодня такая\n' \
               '{0}{1}{2}{3}'.format(morning_weather, day_weather, evening_weather, night_weather)

    def _parse_weather_info(self, day_part):
        """Вспомогательный метод, парсит погоду"""

        # Температуры на утро, день, вечер и ночь в яндексе идут один за другим
        day_query = {'Утро': '1', 'День': '2', 'Вечер': '3', 'Ночь': '4'}
        tmp_value = day_query[day_part]
        day_part_elm = ' .weather-table__body>tr:nth-child({})'.format(tmp_value)  # Локатор строки времени дня

        # Ищем температуру
        temp_elm = ' .weather-table__body-cell_type_feels-like .temp .temp__value'
        temp_join = "{}{}{}".format(self.today_elm, day_part_elm, temp_elm)
        temp_str = self.bs.select(temp_join)[0].get_text()

        # Ищем погодные условия
        condition_elm = ' .weather-table__body-cell_type_condition'
        condition_join = '{}{}{}'.format(self.today_elm, day_part_elm, condition_elm)
        condition_str = self.bs.select(condition_join)[0].get_text()
        condition_emodji = self._get_emoji(condition_str)

        return '\n{}: {} {}'.format(day_part, temp_str, condition_emodji)

    def _get_emoji(self, condition):
        """Возвращает смайлик, соответствующий погодным условиям
        :param condition - погодные условия
        """

        thunderstorm = u'\U0001F4A8'
        rain = u'\U00002614'
        clearSky = u'\U00002600'
        fewClouds = u'\U000026C5'
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

        weather_phrases = ['погода',' погоде', 'погоду', 'погодой', 'погода']

        for phrase in weather_phrases:
            if phrase in message.lower():
                return True

        return False


