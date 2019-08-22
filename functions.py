"""Модуль вспомогательных функций для обучения бота"""

import os
import re
import sys

import bs4
import requests

from bot_config import ConfigManager
from bot_db import DBManager

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


# cities_list = parse_europe_cities()
# db.update_europe_cities(cities_list)
# db.update_all_cities_with_europe()