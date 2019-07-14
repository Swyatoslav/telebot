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

        # Определяем значение начала утренней погоды
        # Определяем блок сегодняшней погоды

        # Определяем диапазон утренней погоды на сегодня
        morning_range_elm = ' tbody>tr:nth-child(1)>td:nth-child(1) .weather-table__temp'  # Локатор для слова Утром
        # Определяем начальное значение диапазона утренней погоды
        morning_start_elm = '>.temp:nth-child(1)'
        # Собираем локатор для определения начального значение диапазона утренней погоды
        morning_start_join = "{}{}{}".format(self.today_elm, morning_range_elm, morning_start_elm)
        # Определяем начальное значение диапазона утренней погоды
        morning_start_value = self.bs.select(morning_start_join)[0].get_text()
        # Определяем конечное значение диапазона утренней погоды
        morning_end_elm = '>.temp:nth-child(2)'
        # Собираем локатор для определения конечного значение диапазона утренней погоды
        morning_end_join = "{}{}{}".format(self.today_elm, morning_range_elm, morning_end_elm)
        # Определяем конечное значение диапазона утренней погоды
        morning_end_value = self.bs.select(morning_end_join)[0].get_text()

        return 'Погода на сегодня\nУтро: {} - {}'.format(morning_start_value, morning_end_value)


class CommunicationManager():
    """Класс для общению с людьми"""

    def is_hello(self, message):
        """Метод проверяет, поздоровались ли с ботом
        :param message - принятое сообщение
        """

        hello_phrases = ['здорова', 'че как', 'че как', 'хай', 'хаюшки', 'привет', 'доброе утро', 'добрый день',
                         'добрый вечер', 'hello', 'hi', 'здравствуй']
        for phrase in hello_phrases:
            if phrase in message.lower():
                return True

        return False

    def say_hello(self):
        """Метод здоровается с человеком"""
        answer_phrases = ['Привет, человек!', 'Хееееей здорова :)', 'Я вас категорически приветствую',
                          'Привет, ты кто? Шутка, я все про тебя знаю ;)', 'Guten tag! С немецкого - Добрый день :)']

        answer_num = random.randint(0, len(answer_phrases))
        return answer_phrases[answer_num]
