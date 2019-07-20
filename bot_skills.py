import json
from datetime import date

import apiai
import bs4
import requests


class WeatherManager:
    """Класс, работающий с парсингом погоды"""

    cur_day = date.today().day
    weather_site = 'https://yandex.ru/pogoda/novosibirsk/details#{}'.format(cur_day)
    response = requests.get(weather_site)
    bs = bs4.BeautifulSoup(response.text, "html.parser")

    today_elm = ".forecast-details>dd:nth-child(2)"
    tomorrow_elm = '.forecast-details>dd:nth-child(5)'

    def get_weather_info(self, message):
        """Метод позволяет спарсить погоду сайта Яндекс
        :param message - сообщение пользователя
        """

        day_parts = ['Утро', 'День', 'Вечер', 'Ночь']
        day_txt = 'завтра' if 'завтра' in message.text.lower() else 'сегодня'
        weather = [self._parse_weather_info(day_part, day_txt) for day_part in day_parts]
        weather.insert(0, day_txt)  # Первым аргументом ставим день, когда смотрим погоду

        return 'Погода в Новосибирске {0} такая\n{1}{2}{3}{4}'.format(*weather)

    def _parse_weather_info(self, day_part, day_txt):
        """Вспомогательный метод, парсит погоду
        :param day_part - Время дня (Утро/День/Вечер/Ночь)
        :param day_txt - на какой день выводить погоду (сегодня/завтра)
        """

        day_elm = self.today_elm if day_txt == 'сегодня' else self.tomorrow_elm

        # Температуры на утро, день, вечер и ночь в яндексе идут один за другим
        day_query = {'Утро': '1', 'День': '2', 'Вечер': '3', 'Ночь': '4'}
        tmp_value = day_query[day_part]
        day_part_elm = ' .weather-table__body>tr:nth-child({})'.format(tmp_value)  # Локатор строки времени дня

        # Ищем температуру
        temp_elm = ' .weather-table__body-cell_type_feels-like .temp .temp__value'
        temp_join = "{}{}{}".format(day_elm, day_part_elm, temp_elm)
        temp_str = self.bs.select(temp_join)[0].get_text()

        # Ищем погодные условия
        condition_elm = ' .weather-table__body-cell_type_condition'
        condition_join = '{}{}{}'.format(day_elm, day_part_elm, condition_elm)
        condition_str = self.bs.select(condition_join)[0].get_text()
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
