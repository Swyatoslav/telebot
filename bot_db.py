import datetime

import psycopg2


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

    def _is_uid_exists(self, uid):
        self.cursor.execute('SELECT id from admin.users WHERE id = {}'.format(uid))
        result = self.cursor.fetchone()
        if result is None:
            return False

        return True

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

    def delete_all_unknown_messages(self):
        """Метод очищает всю таблицу"""

        self.cursor.execute('TRUNCATE admin.unknown_messages')
        self.conn.commit()

    def is_admin_id(self, user_id):
        """Метод проверяет, id админа передано или нет"""

        self.cursor.execute("SELECT id FROM admin.users WHERE user_name = 'Святослав Ященко';")
        self.conn.commit()

        return self.cursor.fetchone()[0] == user_id

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