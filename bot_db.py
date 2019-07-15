import psycopg2
import datetime


class DBManager:
    dbname = None
    user = None
    password = None
    host = 'localhost'
    cursor = None
    conn = None
    cur_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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

    def set_user_info(self, message):
        """Метод записывает в БД инфу про юзера"""

        self.cursor.execute('INSERT INTO admin.users(id, user_name, last_online) VALUES (%s, %s, %s);',
                            (message.from_user.id, message.from_user.first_name + ' ' + message.from_user.last_name,
                             self.cur_date))
        self.conn.commit()

    def set_unknown_message_info(self, message):
        """Метод записывает информацию о нераспознанном сообщении в базу"""

        self.cursor.execute("SELECT id from admin.unknown_messages order by id desc limit 1")
        result = self.cursor.fetchone()

        # Проверяем id. Если база пустая, задаем id = 1 Для избежания ошибки при записи
        if result is None:
            message_id = 1
        else:
            message_id = result[0] + 1
        # если юзера написавшего сообщение, еще нет в базе, записываем
        if not self._is_uid_exists(message.from_user.id):
            self.set_user_info(message)
        self.cursor.execute('INSERT INTO admin.unknown_messages('
                            'id, uid, name, message, message_time)	VALUES ('
                            '%s, %s, %s, %s, %s);' , (
            message_id, message.from_user.id, message.from_user.first_name + ' ' + message.from_user.last_name,
            message.text, self.cur_date))

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

        return 'Неопознанные сообщения стёрты'
# db = DBManager('telebot', 'postgres', '89134580458Asd')
# db.set_inknown_message_info('фигота')
