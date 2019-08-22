import datetime
import time
from random import randint

import psycopg2
from telebot.types import Message

from bot_config import ConfigManager
from bot_consts import ConstantManager
from bot_logging import LogManager


def check_time(func):
    """"""

    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        func_name = func.__name__
        result = func(self, *args, **kwargs)
        exec_time = round(time.time() - start_time, 4)
        user_msg = None
        user_id = None
        config = ConfigManager.create_config(ConstantManager.config_path)
        for arg in args:
            if isinstance(arg, Message):
                user_msg = arg.text
                user_id = arg.from_user.id
                break

        if exec_time > float(config.get('general', 'exec_time')):
            LogManager.write_log_file(func_name, exec_time, user_msg, user_id)

        return result

    return wrapper


class DBManager:
    dbname = None
    user = None
    password = None
    host = 'localhost'
    cursor = None
    conn = None

    def __init__(self, dbname, user, password):
        self.dbname = dbname
        self.user = user
        self.password = password
        self.conn = psycopg2.connect(dbname=self.dbname, user=self.user, password=self.password, host=self.host,
                                     port='5432')
        self.cursor = self.conn.cursor()
        self.conn.commit()

    def save_report(self, uid, traceback, err_info):
        """Метод записывает информацию по ошибке
        :param uid - id пользователя
        :param traceback - traceback ошибки
        :param err_info - общая информация о пользователе и ошибке
        """

        self.cursor.execute("SELECT id from admin.error_reports order by id desc limit 1")
        result = self.cursor.fetchone()

        # Проверяем id. Если база пустая, задаем id = 1 Для избежания ошибки при записи
        report_id = 1 if result is None else int(result[0]) + 1

        self.cursor.execute("""INSERT INTO admin.error_reports(
	                            id, uid, traceback, err_info)
	                            VALUES (%s, %s, %s, %s);""", (report_id, uid, traceback, err_info))
        self.conn.commit()

        return report_id

    def get_report_info(self, report_id):
        """Метод выводит отчет об ошибке
        :param report_id - id отчета
        """

        self.cursor.execute("SELECT traceback, err_info from admin.error_reports WHERE id = {}".format(report_id))
        self.conn.commit()
        result = self.cursor.fetchone()

        return result

    def get_last_report_id(self):
        """Метод возвращает id последнего номера отчета"""

        self.cursor.execute("SELECT id from admin.error_reports order by id desc limit 1")
        result = self.cursor.fetchone()
        if result:
            return result
        else:
            return False

    def delete_report(self, report_id):
        """Метод удаляет информацию об ошибке
        :param report_id - id отчета
        """

        report = self.get_report_info(report_id)
        if report:
            self.cursor.execute("""DELETE FROM admin.error_reports WHERE id = {}""".format(report_id))
            self.conn.commit()

    def get_user_name(self, uid):
        """Метод возвращает имя пользователя
        :param uid - id пользователя
        """

        self.conn.commit()
        self.cursor.execute("""SELECT user_name from admin.users WHERE id = {}""".format(uid))
        self.conn.commit()
        result = self.cursor.fetchone()

        return result

    @check_time
    def _is_uid_exists(self, uid):
        """Метод проверяет, есть ли такой uid в базе
        :param uid - id пользователя
        """

        self.cursor.execute('SELECT id from admin.users WHERE id = {}'.format(uid))
        self.conn.commit()
        result = self.cursor.fetchone()
        if result is None:
            return False

        return True

    def _is_chat_id_exists(self, uid):
        """Метод проверяет, есть ли у юзера id чата
        :param uid - id юзера
        """

        self.cursor.execute('SELECT chat_id from admin.users WHERE id = {}'.format(uid))
        result = self.cursor.fetchone()[0]
        if result is None:
            return False

        return True

    @check_time
    def set_user_info(self, func):
        """Метод записывает в БД инфу про юзера"""

        cur_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        def wrapper(message):
            if not self._is_uid_exists(message.from_user.id):
                user_name = '{} {}'.format(message.from_user.first_name, message.from_user.last_name) \
                    if message.from_user.last_name else message.from_user.first_name
                self.cursor.execute('INSERT INTO admin.users(id, user_name, last_online) VALUES (%s, %s, %s);',
                                    (message.from_user.id,
                                     user_name,
                                     cur_date))
            elif not self._is_chat_id_exists(message.from_user.id):
                self.cursor.execute("""UPDATE admin.users SET chat_id=%s WHERE id=%s""",
                                    (message.chat.id, message.from_user.id))

            else:
                self.cursor.execute('UPDATE admin.users	SET last_online=%s	WHERE id = %s',
                                    (cur_date, message.from_user.id))
            self.conn.commit()
            func(message)

        return wrapper

    @check_time
    def set_unknown_message_info(self, message):
        """Метод записывает информацию о нераспознанном сообщении в базу"""

        cur_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.cursor.execute("SELECT id from admin.unknown_messages order by id desc limit 1")
        result = self.cursor.fetchone()

        # Проверяем id. Если база пустая, задаем id = 1 Для избежания ошибки при записи
        if result is None:
            message_id = 1
        else:
            message_id = result[0] + 1

        last_user_name = ' ' + message.from_user.last_name if message.from_user.last_name else ''

        self.cursor.execute('INSERT INTO admin.unknown_messages('
                            'id, uid, name, message, message_time)	VALUES ('
                            '%s, %s, %s, %s, %s);', (
                                message_id, message.from_user.id,
                                last_user_name,
                                message.text, cur_date))

        self.conn.commit()

    @check_time
    def get_unknown_massage_info(self):
        """Метод выдает информацию о нераспознанном сообщении из базы"""

        self.cursor.execute('SELECT id, uid, name, message, message_time '
                            'FROM admin.unknown_messages;')
        self.conn.commit()
        result = self.cursor.fetchall()
        if result:
            my_unknown_msg = 'Неопознанные сообщения:\n\n'
            for line in result:
                my_unknown_msg += '[{}]   Гость {} написал "{}" \n'.format(line[4], line[2], line[3])
        else:
            my_unknown_msg = 'Неопознанных сообщений нет'

        return my_unknown_msg

    @check_time
    def delete_all_unknown_messages(self):
        """Метод очищает всю таблицу"""

        self.cursor.execute('TRUNCATE admin.unknown_messages')
        self.conn.commit()

        return 'Неопознанные сообщения стерты'

    @check_time
    def is_admin_id(self, user_id):
        """Метод проверяет, id админа передано или нет"""

        self.cursor.execute("SELECT id FROM admin.users WHERE user_name = 'Святослав Ященко';")
        self.conn.commit()

        return self.cursor.fetchone()[0] == user_id

    @check_time
    def set_regions_info(self, region_hrefs, region_names):
        """Метод записывает в базу информацию о регионах яндекс.погоды
        :param region_hrefs - списов ссылок на регионы в яндекс.погоде
        :param region_names - список названий регионов
        """

        for i in range(len(region_names)):
            self.cursor.execute("SELECT id from admin.regions order by id desc limit 1")
            result = self.cursor.fetchone()

            # Проверяем id. Если база пустая, задаем id = 1 Для избежания ошибки при записи
            region_id = 1 if result is None else int(result[0]) + 1
            self.cursor.execute('INSERT INTO admin.regions( '
                                'id, region_name, region_href) VALUES ('
                                '%s, %s, %s);', (region_id, region_names[i], region_hrefs[i]))
            self.conn.commit()

    @check_time
    def set_places_info(self, places_info):
        for i in range(len(places_info)):
            region_name = next(iter(places_info[i]))

            for j in range(len(places_info[i][region_name][0])):
                self.cursor.execute("SELECT id from admin.places order by id desc limit 1")
                result = self.cursor.fetchone()
                place_id = 1 if result is None else int(result[0]) + 1
                self.cursor.execute('INSERT INTO admin.places('
                                    'id, region_name, place_name, place_href) VALUES ('
                                    '%s, %s, %s, %s);', (place_id, region_name, places_info[i][region_name][1][j],
                                                         places_info[i][region_name][0][j]))
                self.conn.commit()

    @check_time
    def get_weather_edit_mode_stage(self, user_id):
        """Проверяем, не идет ли настройка погоды у пользователя"""

        self.cursor.execute('SELECT edit_weather_mode FROM admin.users where id=%s', [user_id])
        result = self.cursor.fetchone()
        self.conn.commit()

        return result[0]

    @check_time
    def is_weather_place_set(self, user_id):
        """Метод проверяет, выставлен ли город для определения погоды
        :param user_id - id пользователя
        """

        self.cursor.execute('SELECT weather_place_id FROM admin.users where id=%s', [user_id])
        result = self.cursor.fetchone()
        self.conn.commit()

        return result[0]

    @check_time
    def set_weather_edit_mode(self, user_id, stage):
        """Выставляем флаг начала настройки погоды
        :param user_id - id пользователя
        :param stage - этап настройки
        """

        self.cursor.execute("UPDATE admin.users	SET edit_weather_mode=%s WHERE id=%s;", (stage, user_id))
        self.conn.commit()

        return 'Выставлен режим настройки: {}'.format(stage)

    @check_time
    def get_place_info_by_name(self, text):
        """Метод выдергивает информацию о населенном пункте по его названию
        :param - текст, по которому ищем населенный пункт
        """

        self.cursor.execute('SELECT id, region_name, place_name, place_href	'
                            'FROM admin.places '
                            "where place_name ~* %s;", [text])
        self.conn.commit()

        result = self.cursor.fetchall()

        return result

    @check_time
    def set_place_id_to_user(self, place_id, user_id):
        """Метод записывает id населенного пункта в информацию юзера
        :param place_id - id населенного пункта
        :param user_id - id пользователя
        """

        self.cursor.execute('UPDATE admin.users	SET weather_place_id=%s	WHERE id=%s;', (place_id, user_id))
        self.conn.commit()

    @check_time
    def get_place_info_of_user_by_user_id(self, user_id):
        """Метод возвращает id места по id юзера
        :param user_id - id юзера
        """

        self.cursor.execute('SELECT weather_place_id FROM admin.users WHERE id=%s', [user_id])
        place_id = self.cursor.fetchone()[0]
        self.cursor.execute('SELECT place_href, place_name, region_name FROM admin.places WHERE id=%s;', [place_id])
        place_info = self.cursor.fetchone()
        self.conn.commit()

        return place_info

    @check_time
    def create_tmp_table_for_search_place(self, user_id):
        """Метод создает временную таблицу для хранения промежуточных значений результатов поиска
        :param user_id - id юзера
        """

        table_name = 'admin.user_{}_tmp'.format(user_id)

        self.cursor.execute('DROP TABLE IF EXISTS {};\n'
                            'CREATE TABLE {}\n'
                            '(\n'
                            'id integer NOT NULL,\n'
                            'place_id integer NOT NULL,\n'
                            'region_name text COLLATE pg_catalog."default" NOT NULL,\n'
                            'place_name text COLLATE pg_catalog."default" NOT NULL,\n'
                            'place_href text COLLATE pg_catalog."default" NOT NULL)\n'
                            'WITH (\n'
                            'OIDS = FALSE\n'
                            ')\n'
                            'TABLESPACE pg_default;\n'

                            'ALTER TABLE admin.places\n'
                            'OWNER to postgres;'.format(table_name, table_name))
        self.conn.commit()

        return table_name

    @check_time
    def set_tmp_result_of_search_weather_place(self, table_name, result):
        """Метод записывает удачный результат поиска во временную таблицу
        :param table_name - название временной таблицы
        :param result - результат, который хотим сохранить
        """

        for result_line in result:
            self.cursor.execute("SELECT id from {} order by id desc limit 1".format(table_name))
            result = self.cursor.fetchone()
            self.conn.commit()

            # Проверяем id. Если база пустая, задаем id = 1 Для избежания ошибки при записи
            tmp_id = 1 if not result else result[0] + 1

            self.cursor.execute('INSERT INTO {}('
                                'id, place_id, region_name, place_name, place_href) VALUES ('
                                '%s, %s, %s, %s, %s);'.format(table_name), (tmp_id, result_line[0],
                                                                            result_line[1], result_line[2],
                                                                            result_line[3]))
            self.conn.commit()

    @check_time
    def get_all_info_from_tmp_weather_places(self, tmp_table):
        """Метод вытаскивает всю информацию о поиске из временной таблицы
        :param tmp_table - название временной таблицы
        """

        self.cursor.execute('SELECT * FROM {};'.format(tmp_table))
        result = self.cursor.fetchall()
        self.conn.commit()

        return result

    @check_time
    def get_some_info_from_tmp_weather_places(self, tmp_table, row_id=1):
        """Метод вытаскивает некоторую информацию из временной таблицы
        :param tmp_table - название временной таблицы
        :param row_id - id во временной таблице
        """

        self.cursor.execute('SELECT * FROM {} WHERE id =%s;'.format(tmp_table), [row_id])
        result = self.cursor.fetchone()
        self.conn.commit()

        return result

    @check_time
    def get_max_id_from_tmp_weather_places(self, tmp_table):
        """Метод вытаскивает последний id из временной таблицы резульаттов
        :param tmp_table - название временной таблицы
        :param row_id - id во временной таблице
        """

        self.cursor.execute("SELECT id from {} order by id desc limit 1".format(tmp_table))
        result = self.cursor.fetchone()
        self.conn.commit()

        return result

    @check_time
    def drop_tmp_table(self, table_name):
        """Метод удаляет временную таблицу из бд
        :param table_name - название временной таблицы
        """

        self.cursor.execute("DROP TABLE {};".format(table_name))
        self.conn.commit()

    @check_time
    def set_city_feature(self, city_name):
        """Метод задает населенному пункту в таблице признак города
        :param city_name - название города
        """

        self.cursor.execute('SELECT id FROM admin.places '
                            "where place_name ILIKE %s", [city_name])
        self.conn.commit()

        place_id = self.cursor.fetchone()
        if place_id:
            place_id = place_id[0]
            self.cursor.execute('UPDATE admin.places SET is_city=TRUE WHERE id = %s;', [place_id])
            self.conn.commit()
        else:
            print('В списке городов не найден: {}'.format(city_name))

    def set_game_cities_mode(self, user_id, stage):
        """Метод записывает в БД название этапа игры (Вступление/Игра)
        :param user_id - id пользователя
        :param stage - название этапа
        """

        self.cursor.execute("UPDATE admin.users	SET game_cities=%s WHERE id=%s;", (stage, user_id))
        self.conn.commit()

    @check_time
    def get_game_cities_mode_stage(self, user_id):
        """Проверяем, не идет ли игра Города у пользователя"""

        self.cursor.execute('SELECT game_cities FROM admin.users where id=%s', [user_id])
        result = self.cursor.fetchone()
        self.conn.commit()

        return result[0]

    def create_tmp_game_cities_table(self, user_id):
        """Метод создает игровую таблицу для игры Города
        :param user_id - id пользователя
        """

        part_table_name = '{}{}'.format('cities_', user_id)
        full_table_name = 'admin.{}'.format(part_table_name)

        self.cursor.execute(""" DROP TABLE IF EXISTS {1};
                                CREATE TABLE {1}(
                                id integer NOT NULL,
                                place_id integer NOT NULL,
                                city_name text NOT NULL,
                                is_bot boolean NOT NULL,
                                CONSTRAINT {0}_pkey PRIMARY KEY (id));""".format(part_table_name, full_table_name))
        self.conn.commit()

        return full_table_name

    def set_new_city_in_game_table(self, user_id, city_id, city_name, is_bot):
        """Метод записывает новый город в игрвую таблицу
        :param user_id - id юзера
        :param city_id - id города
        :param city_name - название города
        :param is_bot - город назвал бот
        """

        table_name = '{}{}'.format('admin.cities_', user_id)

        self.cursor.execute("SELECT id from {} order by id desc limit 1".format(table_name))
        result = self.cursor.fetchone()
        self.conn.commit()
        tmp_id = 1 if not result else result[0] + 1

        self.cursor.execute(
            """INSERT INTO {}(id, place_id, city_name, is_bot)VALUES (%s, %s, %s, %s);""".format(table_name),
            (tmp_id, city_id, city_name, is_bot))
        self.conn.commit()

    def select_random_city_against_user_city(self, user_id, city_name):
        """Метод возвращает случайный город, основываясь на городе пользователя
        :param user_id - id юзера
        :param city_name - название города
        """

        table_name = '{}{}'.format('admin.cities_', user_id)

        if city_name[-1] in ['ь', 'ъ', 'й', 'ю', 'ы', 'ё']:
            last_let = city_name[-2]
        else:
            last_let = city_name[-1]

        if last_let in ['ь', 'ъ', 'й', 'ю', 'ы', 'ё']:
            last_let = city_name[-3]

        # Получаем список оставшихся городов на эту букву
        self.cursor.execute(
            "select id, place_name from admin.game_cities WHERE place_name ilike '{}%' "
            "AND id NOT IN "
            "(select place_id from {})".format(last_let, table_name))
        self.conn.commit()
        all_list = self.cursor.fetchall()
        random_int = randint(0, len(all_list) - 1)

        # Выбираем случайный город из списка
        random_city_id = all_list[random_int][0]
        random_city_name = all_list[random_int][1]

        # Записываем в игровую таблицу новый город
        self.set_new_city_in_game_table(user_id, random_city_id, random_city_name, True)

        return random_city_name

    def is_city_exists(self, city):
        """Метод ищет город названный пользователем в базе
        :param city - название города
        """

        self.cursor.execute("SELECT id from admin.game_cities where place_name ilike %s ", [city])
        self.conn.commit()
        result = self.cursor.fetchone()

        if result:
            return result[0]

        return False

    def is_city_was_called(self, city_name, user_id):
        """Метод ищет город названный пользователем в уже названных
        :param city_name - название города
        :param city_id - id города
        :param user_id - id пользователя
        """

        table_name = '{}{}'.format('admin.cities_', user_id)

        self.cursor.execute("select place_id from {} where city_name ilike %s".format(table_name), [city_name])
        self.conn.commit()
        result = self.cursor.fetchone()

        if result:
            return True

        return False

    def is_city_starts_with_end_letter(self, user_id, user_city, city_id):
        """Метод проверяет, действительно ли названный город начинается на ту букву, которой закончился предыдущий
        :param user_id - id пользователя
        :param user_city - город названный пользователем
        """

        table_name = '{}{}'.format('admin.cities_', user_id)

        self.cursor.execute("SELECT city_name from {} order by id desc limit 1".format(table_name))
        result = self.cursor.fetchone()
        self.conn.commit()

        if not result:  # Если это наш первый город
            self.set_new_city_in_game_table(user_id, city_id, user_city, False)
            return True
        else:
            city_name = result[0]

        if city_name[-1] in ['ь', 'ъ', 'й', 'ю', 'ы']:
            last_let = city_name[-2]
        else:
            last_let = city_name[-1]

        if last_let == 'ы':
            last_let = city_name[-3]

        if last_let == user_city[0].lower():
            self.set_new_city_in_game_table(user_id, city_id, user_city, False)
            return True
        else:
            return False

    def is_user_already_win(self, user_id):
        """Метод проверяет, не победил ли уже игрок
        :param user_id - id пользователя
        """

        table_name = '{}{}'.format('admin.cities_', user_id)

        self.cursor.execute("SELECT id from {} order by id desc limit 1".format(table_name))
        result = self.cursor.fetchone()[0]
        self.conn.commit()

        if result > 50:
            return True
        else:
            return False

    def set_random_five_mode(self, user_id, stage):
        """Метод выставляет флаг начала random 5
        :param user_id - id пользователя
        :param stage - этап мода (True, None)
        """

        self.cursor.execute("""UPDATE admin.users
	                           SET is_random_5=%s
	                           WHERE id=%s;""", (stage, user_id))
        self.conn.commit()

    def is_random_five_mode(self, user_id):
        """Метод проверяет, не выставлен ли режим random_5
        :param user_id - id пользователя
        """

        self.cursor.execute("""SELECT is_random_5
	                           FROM admin.users
	                           WHERE id=%s;""", [user_id])
        self.conn.commit()

        result = self.cursor.fetchone()[0]

        return result

    def set_all_game_cities(self, all_cities):
        """Метод заполняет базу всеми городами мира
        :param all_cities - список из множеств городов на разные буквы
        """

        for all_cities_letter in all_cities:
            for city in all_cities_letter:
                self.cursor.execute("SELECT id from admin.game_cities order by id desc limit 1")
                result = self.cursor.fetchone()
                self.conn.commit()
                tmp_id = 1 if not result else result[0] + 1
                self.cursor.execute("""INSERT INTO admin.game_cities(
	                                    id, place_name)
	                                    VALUES (%s, %s);""", (tmp_id, city))
                self.conn.commit()

    def update_all_cities(self):
        """Метод вытаскивает все города россии из таблицы places"""

        self.cursor.execute("""SELECT place_name from admin.places WHERE place_name NOT IN 
        (SELECT place_name FROM admin.game_cities) AND is_city=TRUE
        """)
        self.conn.commit()

        result = self.cursor.fetchall()
        all_ru_cities = [city[0] for city in result]

        for city in all_ru_cities:
            self.cursor.execute("SELECT id from admin.game_cities order by id desc limit 1")
            result = self.cursor.fetchone()
            self.conn.commit()
            tmp_id = 1 if not result else result[0] + 1
            self.cursor.execute("""INSERT INTO admin.game_cities(
        	                                    id, place_name)
        	                                    VALUES (%s, %s);""", (tmp_id, city))
            self.conn.commit()

    def update_europe_cities(self, cities_list):
        """Метод записывает города в таблицу городов европы
        :param cities_list - список списков городов европы
        """

        for cities in cities_list:
            for city in cities:
                self.cursor.execute("SELECT id from admin.europe_cities order by id desc limit 1")
                result = self.cursor.fetchone()
                self.conn.commit()
                tmp_id = 1 if not result else result[0] + 1
                self.cursor.execute("""INSERT INTO admin.europe_cities(
                        	                                    id, place_name)
                        	                                    VALUES (%s, %s);""", (tmp_id, city))
                self.conn.commit()

    def update_all_cities_with_europe(self):
        """Метод обновляет информацию по городам, добавляя города европы"""

        self.cursor.execute("""SELECT place_name from admin.europe_cities WHERE place_name NOT IN 
        (SELECT place_name FROM admin.game_cities)
        """)

        self.conn.commit()

        result = self.cursor.fetchall()
        all_ru_cities = [city[0] for city in result]

        for city in all_ru_cities:
            self.cursor.execute("SELECT id from admin.game_cities order by id desc limit 1")
            result = self.cursor.fetchone()
            self.conn.commit()
            tmp_id = 1 if not result else result[0] + 1
            self.cursor.execute("""INSERT INTO admin.game_cities(
        	                                    id, place_name)
        	                                    VALUES (%s, %s);""", (tmp_id, city))
            self.conn.commit()
