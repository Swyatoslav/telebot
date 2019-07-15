import random
from datetime import date

import bs4
import requests


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

        morning_temp = self._get_weather_info('Утро')
        day_temp = self._get_weather_info('День')
        evening_temp = self._get_weather_info('Вечер')
        night_temp = self._get_weather_info('Ночь')

        return 'Погода в Новосибирске сегодня такая..\nУтро: {}°\nДень: {}°\nВечер: {}°\nНочь: {}°'.format(
            morning_temp, day_temp, evening_temp, night_temp)

    def _get_weather_info(self, day_part):
        """Вспомогательный метод, парсит погоду на утро"""

        # Температуры на утро, день, вечер и ночь в яндексе идут один за другим
        day_query = {'Утро': '1', 'День': '2', 'Вечер': '3', 'Ночь': '4'}
        tmp_value = day_query[day_part]

        # Определяем диапазон утренней погоды на сегодня
        range_elm = ' tbody>tr:nth-child({})>td:nth-child(1) .weather-table__temp'.format(tmp_value)
        # Определяем начальное значение диапазона погоды
        start_elm = '>.temp:nth-child(1)'
        # Собираем локатор для определения начального значение диапазона погоды
        start_join = "{}{}{}".format(self.today_elm, range_elm, start_elm)
        # Определяем начальное значение диапазона погоды
        start_str = self.bs.select(start_join)[0].get_text()
        # Определяем конечное значение диапазона погоды
        end_elm = '>.temp:nth-child(2)'
        # Собираем локатор для определения конечного значение диапазона погоды
        end_join = "{}{}{}".format(self.today_elm, range_elm, end_elm)
        # Определяем конечное значение диапазона погоды
        end_str = self.bs.select(end_join)[0].get_text()

        # Считаем среднее значение температуры за интервал
        start_value = start_str[1:len(start_str) - 1]
        end_value = end_str[1: len(end_str) - 1]

        return (int(start_value) + int(end_value)) // 2


class CommunicationManager:
    """Класс для общения с людьми"""

    def is_hello(self, message):
        """Метод проверяет, поздоровались ли с ботом
        :param message - принятое сообщение
        """

        hello_phrases = ['здорова', 'здарова', 'че как', 'че как', 'хай', 'хаюшки', 'привет', 'доброе утро', 'добрый день',
                         'добрый вечер', 'hello', 'hi', 'здравствуй']
        for phrase in hello_phrases:
            if phrase in message.lower():
                return True

        return False

    def is_goodbye(self, message):
        """Метод проверяет, попрощались ли с ботом
        :param - сообщение боту
        """

        bye_phrases = ['пока', 'досвидания', 'до свидания', 'досвиданья', 'до свидания', 'Увидимся', 'до завтра',
                       'бывай', 'до скорого', 'увидимся']

        for phrase in bye_phrases:
            if phrase in message.lower():
                return True

        return False

    def say_hello(self):
        """Метод здоровается с человеком"""
        hello_phrases = ['Привет, человек!', 'Хееееей здорова :)', 'Я вас категорически приветствую',
                          'Привет, ты кто? Шутка, я все про тебя знаю ;)', 'Guten tag! С немецкого - Добрый день :)']

        answer_num = random.randint(0, len(hello_phrases) - 1)
        return hello_phrases[answer_num]

    def say_goodbye(self):
        """Метод прощается с человеком"""

        goodbye_phrases = ['Не пропадай!', 'Жду нашей следующей встречи :)', 'Пока! =)', 'Даже на десерт не остался..',
                           'Очень жаль.. видимо у тебя есть дела поважнее']

        answer_num = random.randint(0, len(goodbye_phrases) - 1)

        return goodbye_phrases[answer_num]

    def is_weather_question(self, message):
        """Метод проверяет, не о погоде ли спросили бота
        :param message сообщение боту
        """

        weather_phrases = ['погода',' погоде', 'погоду', 'погодой', 'погода']

        for phrase in weather_phrases:
            if phrase in message.lower():
                return True

        return False


