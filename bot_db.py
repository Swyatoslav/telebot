import datetime
import time
import psycopg2
from telebot.types import Message
from bot_logging import LogManager
from bot_consts import ConstantManager
from bot_config import ConfigManager


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

    @check_time
    def _is_uid_exists(self, uid):
        self.cursor.execute('SELECT id from admin.users WHERE id = {}'.format(uid))
        result = self.cursor.fetchone()
        if result is None:
            return False

        return True

    @check_time
    def set_user_info(self, func):
        """Метод записывает в БД инфу про юзера"""

        cur_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        def wrapper(message):
            if not self._is_uid_exists(message.from_user.id):
                self.cursor.execute('INSERT INTO admin.users(id, user_name, last_online) VALUES (%s, %s, %s);',
                                    (message.from_user.id,
                                     message.from_user.first_name + ' ' + message.from_user.last_name,
                                     cur_date))
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
                                                                        result_line[1], result_line[2], result_line[3]))
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
    def get_some_info_from_tmp_weather_places(self, tmp_table, row_id):
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
