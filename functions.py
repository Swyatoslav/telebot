"""Модуль вспомогательных функций для обучения бота"""

import requests
from bot_db import DBManager
from bot_config import ConfigManager
import os
import bs4
import sys
import re


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
            and 'meteum' not in href and 'informer' not in href and 'details' not in href\
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
        parce_result= bs.find_all('a', href=re.compile('/pogoda/.*'))

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


# region_hrefs, region_names = parse_regions_info()
# all_places_info = parse_places_info(region_hrefs, region_names)
# db.set_places_info(all_places_info)