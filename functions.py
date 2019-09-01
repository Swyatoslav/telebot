"""Модуль вспомогательных функций для обучения бота"""

import os
import re
import sys

import bs4
import requests

from bot_config import ConfigManager
from bot_db import DBManager
import wikipedia
from itertools import groupby

site = 'https://yandex.ru/pogoda/region/225?from=main_other_cities'

# создаем экземпляр бд
config_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'config.ini')
cm = ConfigManager().create_config(config_path)
db = DBManager(cm.get('general', 'db'), cm.get('general', 'db_user_name'), cm.get('general', 'db_user_password'))


def parse_regions_info():
    """Метод парсит информацию о регионах яндекс.погоды"""

    short_site = 'https://yandex.ru'
    response = requests.get(site)
    bs = bs4.BeautifulSoup(response.text, "html.parser")
    regions = bs.find_all('a', href=re.compile('/pogoda/region/.*'))
    region_hrefs = [short_site + re.compile('/pogoda/region[^\s"]+').findall(str(region))[0] for region in regions]
    region_names = [re.compile('>[\w\s\-()—]*<').findall(str(region))[0][1:-1] for region in regions]

    return region_hrefs, region_names


def _is_correct_href(href):
    """Метод проверяет, корректна ли ссылка"""

    if 'map' not in href and 'region' not in href and 'month' not in href \
            and 'meteum' not in href and 'informer' not in href and 'details' not in href \
            and 'compare' not in href:
        return href


def parse_places_info(region_hrefs, region_names):
    """Метод парсит информацию о населенных пунктах"""

    short_site = 'https://yandex.ru'
    all_places_info = []
    for i in range(len(region_hrefs)):
        # Делаем запрос по ссылке
        response = requests.get(region_hrefs[i])

        # Возвращаем страницу запроса
        bs = bs4.BeautifulSoup(response.text, "html.parser")

        # Парсим страницу запроса, результат идет в виде списка элементов класса Tag
        parce_result = bs.find_all('a', href=re.compile('/pogoda/.*'))

        # Преобразуем список тэгов в список строк
        res = [str(line) for line in parce_result]

        # Убираем из списка лишние элементы
        places = [place for place in filter(_is_correct_href, res)]

        # Парсим ссылки из строк
        places_hrefs = [short_site + re.compile('/pogoda/[^\s"]+').findall(str(place))[0] for place in places]

        # Парсим название населенных пунктов из строк
        places_names = [re.compile('>[\w\s\-()—,./№«»]*<').findall(str(place))[0][1:-1] for place in places]

        # Возвращаем результат в виде словаря {название_региона: [ссылки_на_города_региона, названия_городов_региона]}
        places_info = {region_names[i]: [places_hrefs, places_names]}
        all_places_info.append(places_info)

    return all_places_info


def parse_all_country_cities():
    """Метод парсит города россии"""

    site = 'https://ru.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA' \
           '_%D0%B3%D0%BE%D1%80%D0%BE%D0%B4%D0%BE%D0%B2_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D0%B8'

    # Получаем страницу википедии с городами России
    response = requests.get(site)
    bs = bs4.BeautifulSoup(response.text, "html.parser")

    # Получаем список строк с названиями городов
    city_rows_elm = bs.select('table.sortable tr>td:nth-child(3) a')

    # Получаем список title с названиями городов
    city_titles = [re.compile('title="[\D\s]*"').findall(str(city))[0] for city in city_rows_elm]

    # Получаем список названий городов
    city_names = [re.compile('"[\D\s]*"').findall(city)[0][1:-1] for city in city_titles]

    # Убираем указание города из названия
    for i in range(len(city_names)):
        if ' (' in city_names[i]:
            city_names[i] = city_names[i][0: city_names[i].index(' (')]

    # Убираем дубли из городов и лишнюю запись
    unique_city_names = set(city_names)
    unique_city_names.remove('Проблема принадлежности Крыма')

    return unique_city_names


def parse_all_cities():
    """Метод парсит все города мира с сайта"""

    first_site = 'http://www.1000mest.ru/cityA'
    e = '.field-item tr'
    e2 = 'nth-child'

    response = requests.get(first_site)
    bs = bs4.BeautifulSoup(response.text, "html.parser")

    # Получаем список ссылок на буквы городов
    parce_result = bs.select('h4 a')
    all_letters = []
    for i in parce_result:
        start_index = str(i).index('"')
        end_index = str(i).index('"', start_index + 1)
        all_letters.append(str(i)[start_index + 1:end_index])

    # Получаем названия городов на буквы
    all_cities = []
    for letter in all_letters:
        site = 'http://www.1000mest.ru/{}'.format(letter)
        response_new = requests.get(site)
        bs = bs4.BeautifulSoup(response_new.text, "html.parser")
        rows = len(bs.select(e))
        cities = []
        for i in range(1, rows):
            cities.append(str(bs.select('{}:{}({})'.format(e, e2, i))[0].get_text()).replace('\n', ''))

        all_cities.append(set(cities))

    return all_cities


def parse_europe_cities():
    """Метод вытаскивает все города Европы"""

    site = 'https://avtoturistu.ru/page/%D1%81%D0%BF%D0%B8%D1%81%D0%BE%D0%BA' \
           '_%D0%B3%D0%BE%D1%80%D0%BE%D0%B4%D0%BE%D0%B2_%D0%95%D0%B2%D1%80%D0%BE%D0%BF%D1%8B/'

    response = requests.get(site)
    bs = bs4.BeautifulSoup(response.text, "html.parser")

    # Записываем информацию про
    cities_info = []
    parse_result = bs.select('.content tr td:not([colspan="4"])')
    for item in parse_result:
        cities_info.append(item.get_text())

    # Убираем лишние символы из городов
    cities_info_cut_n = [city_row.replace('\n', ' ').replace('\r', ' ') for city_row in cities_info]
    cities_info_cut_bracket = []
    for city_block in cities_info_cut_n:
        new_city_block = city_block
        while '(' in new_city_block and ')' in new_city_block:
            start_index = new_city_block.index('(')
            end_index = new_city_block.index(')')
            new_city_block = new_city_block.replace(new_city_block[start_index -1:end_index+1], '')

        cities_info_cut_bracket.append(new_city_block)

    cities_cut_tripple_whitespaces = [city_info.replace('   ', ' ') for city_info in cities_info_cut_bracket]
    cities_cut_double_white_spaces = [city_info.replace('  ', ' ') for city_info in cities_cut_tripple_whitespaces]
    cities = [city.split(' ') for city in cities_cut_double_white_spaces]

    return cities

def get_usa_cities_list():
    """Метод выдирает все города с сайта"""

    site = 'http://www.americancities.ru/info/usa_cities_in_alphabetical/'

    # Делаем запрос на сайт
    response = requests.get(site)
    bs = bs4.BeautifulSoup(response.text, "html.parser")
    result = bs.select('.stat tr>td:nth-child(1)')

    return [str(city)[4:-5] for city in result]


def get_problem_cities():
    """Метод вытаскивает все проблемные города из городов, и делает их навание доступным
    после чего обрабатывает их
    """

    result = db.get_all_problem_cities()
    result_collection = [(place_id, place_name, place_name.replace('ё', 'е').replace('-', ' '))
                         for place_id, place_name in result]

    return result_collection

def get_problem_capitals():
    """Метод вытаскивает все проблемные столицы для игры -Столицы Мира-, и делает их навание доступным
    после чего обрабатывает их
    """

    result = db.get_all_problem_capitals()
    result_collection = [(capital_id, capital_name, capital_name.replace('ё', 'е').replace('-', ' '))
                         for capital_id, capital_name in result]

    return result_collection

def parse_all_countries_with_capitals():
    """Метод парсит википедию и получает список столиц со странами"""

    site = 'https://ru.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D1%81%D1%82%D0%BE%D0%BB%D0%B8%D1%86_%D0%BC%D0%B8%D1%80%D0%B0'

    response = requests.get(site)
    bs = bs4.BeautifulSoup(response.text, "html.parser")
    elms = bs.find_all('a', title=re.compile('[а-яА-ЯёЁ\s()-]*'))
    row_list = [line.get('title') for line in elms if
                ':' not in line.get('title')
                and line.get('title') not in
                ['Европа', 'Азия', 'Африка', 'Америка' 'Австралия и Океания']]
    # country_list = [elm for elm in row_list if ' ' not in elm or ':' not in elm]
    country_list_without_doubles = [el for el, _ in groupby(row_list) if el != 'Ватикан'][:420]
    country_list_corr = [elm.replace(' (город)', '').replace(' (Сейшельские острова)', '').replace(' (округ Колумбия)', '').replace(' (Ямайка)', '').replace(' (Багамы)', '').replace(' (Коста-Рика)', '')
                         for elm in country_list_without_doubles if
                         'Поиск' not in elm and
                         'Перейти' not in elm and
                         'Статьи' not in elm and
                         'Части' not in elm and
                         'раздел' not in elm and
                         'Флаг' not in elm and
                         'Редактировать' not in elm and
                         'Нью-Дели' not in elm and
                         'Баирики' not in elm and
                         'Сингапур' not in elm and
                         'Америка' not in elm and
                         'Австралия и Океания' not in elm
                        ]
    country_list_corr.extend(['Ватикан', 'Ватикан', 'Сингапур', 'Сингапур'])
    countries_list = [country_list_corr[i] for i in range(len(country_list_corr)) if i % 2 == 1]
    capitals_list = [country_list_corr[i] for i in range(len(country_list_corr)) if i % 2 == 0]
    result = [(countries_list[i], capitals_list[i]) for i in range(len(countries_list))]

    return result


problem_list = get_problem_capitals()
db.set_all_problem_capitals(problem_list)
