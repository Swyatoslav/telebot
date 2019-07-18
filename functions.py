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


def set_weather_info(db):
    response = requests.get(site)
    bs = bs4.BeautifulSoup(response.text, "html.parser")
    regions = bs.find_all('a', href=re.compile('/pogoda/region/.*'))
    region_hrefs = [re.compile('/pogoda/region[^\s"]+').findall(str(region))[0] for region in regions]
    region_names = [re.compile('>[\w\s\-()—]*<').findall(str(region))[0][1:-1] for region in regions]
    

set_weather_info(db)