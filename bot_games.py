import time

import wikipedia
from telebot import types
from telebot.types import ReplyKeyboardRemove

from bot_db import check_time


class CitiesGameManager:
    """Класс для работы с игрой Города"""

    btn1 = 'Начнем игру'
    btn2 = 'Прервать игру'

    @check_time
    def set_buttons(self, *buttons):
        """Метод размещает под панелью клавиатуры одну или несколько кнопок
        :param buttons - текст кнопок
        """

        markup = types.ReplyKeyboardMarkup(row_width=len(buttons), one_time_keyboard=True, resize_keyboard=True)
        my_buttons = [types.KeyboardButton(button_text) for button_text in buttons]
        markup.add(*my_buttons)

        return markup

    @check_time
    def game_mode(self, message, db, bot):
        """Режим игры в Города
        :param message - сообщение пользователяtime.sleep(0.5)
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        if 'прервать' in message.text.lower() or 'прервем' in message.text.lower():
            db.set_game_cities_mode(message.from_user.id, None)
            bot.send_message(message.chat.id, 'Хорошо, поиграем в другой раз!',
                             reply_markup=ReplyKeyboardRemove())
            return
        elif 'Узнать про' in message.text:
            city = message.text.split('Узнать про')[1]
            time.sleep(0.5)
            bot.send_message(message.chat.id, 'Подождите, ищу информацию про{}..'.format(city))
            city_info = self.get_info_about_city(city)
            if city_info:
                bot.send_message(message.chat.id, city_info, reply_markup=ReplyKeyboardRemove())
            else:
                bot.send_message(message.chat.id, 'К сожалению, пока я не могу\n'
                                                  ' ничего рассказать про{}'.format(city),
                                 reply_markup=ReplyKeyboardRemove())
            time.sleep(2)
            bot.send_message(message.chat.id, 'Итак, мой город {}. Ваша очередь :)'.format(city),
                             reply_markup=self.set_buttons('Прервать игру'))
            return

        phase = db.get_game_cities_mode_stage(message.from_user.id)

        if not phase:
            self._hello_stage_game_cities(message, db, bot)
        elif phase == 'Вступление':
            self._first_game_cities_stage(message, db, bot)
        elif phase == 'Игра':
            self._second_game_cities_stage(message, db, bot)

    def _hello_stage_game_cities(self, message, db, bot, first_time=True):
        """Приветствие в игре Города
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        :param попадаем на фазу приветствия первый раз
        """

        db.set_game_cities_mode(message.from_user.id, 'Вступление')
        if first_time:
            time.sleep(0.5)
            bot.send_message(message.chat.id, 'Приветствую вас в игре Города!')

        info_msg1 = 'Правила очень простые:\n' \
                    'Я называю один из городов,\n' \
                    'например Рига. Ты мне говоришь город, \n' \
                    'начинающийся на последнюю букву моего города,\n' \
                    'например Анапа.\n' \
                    'Продержишься 35 ходов - и ты победил :)'
        info_msg2 = 'Начнем игру?'

        time.sleep(0.5)
        bot.send_message(message.chat.id, info_msg1)
        time.sleep(1)
        bot.send_message(message.chat.id, info_msg2, reply_markup=self.set_buttons('Начнем игру', 'Прервать игру'))

    def _first_game_cities_stage(self, message, db, bot):
        """Первая стадия игры
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        rules = """ Обратите внимание, буквы
*-ы-, -й-, -ь-, -ъ-, -ё-, -ю-* не участвуют в игре.
Если город оканчивается на одну из этих букв,
берется буква, стоящая перед ней.
Если город оканчивается на *-ый-*, берется буква перед *-ы-*.
"""

        if 'начнем' in message.text.lower():
            db.set_game_cities_mode(message.from_user.id, 'Игра')
            db.create_tmp_game_cities_table(message.from_user.id)
            bot.send_message(message.chat.id, rules,
                             reply_markup=self.set_buttons('Прервать игру'),
                             parse_mode='Markdown')
            time.sleep(1)
            bot.send_message(message.chat.id, 'Первым ходите вы :) Пишите любой город.')
            return

        if 'продолжить' in message.text.lower():
            bot.send_message(message.chat.id, 'Хорошо, напомню правила :)')
            db.set_game_cities_mode(message.from_user.id, None)
            self._hello_stage_game_cities(message, db, bot, first_time=False)
        else:
            bot.send_message(message.chat.id, 'Включена игра "Города". Прервать игру?',
                             reply_markup=self.set_buttons('Прервать', 'Продолжить'))

    def _second_game_cities_stage(self, message, db, bot):
        """Вторая стадия игры - сама игра
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        city_info = db.is_city_exists(message.text)

        if city_info:
            city_id = city_info[0]
            city_name = city_info[1]
            if not db.is_city_was_called(city_name, message.from_user.id):
                if db.is_city_starts_with_end_letter(message.from_user.id, city_name, city_id):
                    if db.is_user_already_win(message.from_user.id):
                        bot.send_message(message.chat.id, 'Вы победили! Игра окончена :)',
                                         reply_markup=ReplyKeyboardRemove())
                        db.set_game_cities_mode(message.from_user.id, None)
                        db.drop_tmp_table('admin.cities_{}'.format(message.from_user.id))
                    else:
                        bot_city = db.select_random_city_against_user_city(message.from_user.id, city_name)
                        bot.send_message(message.chat.id, '*{}*'.format(bot_city),
                                         reply_markup=self.set_buttons('Прервать игру',
                                                                       'Узнать про {}'.format(bot_city)),
                                         parse_mode='Markdown')
                else:
                    bot.send_message(message.chat.id, 'Названный вами город начинается\n'
                                                      ' не с последней буквы предыдущего! ',
                                     reply_markup=self.set_buttons('Прервать игру'))
            else:
                bot.send_message(message.chat.id, 'Город уже был назван! Введите другой',
                                 reply_markup=self.set_buttons('Прервать игру'))
        else:
            bot.send_message(message.chat.id, 'Извините, я не знаю такого города. Введите другой',
                             reply_markup=self.set_buttons('Прервать игру'))

    @check_time
    def get_info_about_city(self, city):
        """Метод парсит википедию в поисках  города
        :param city - название города
        """

        search_str = '{} {}'.format(city, '(город)')
        wikipedia.set_lang('ru')
        try:
            info = wikipedia.summary(search_str, sentences=5)
            if '=' in info:
                info = info[0:info.index('=')]
            return info
        except wikipedia.exceptions.PageError:
            return False
        except wikipedia.exceptions.DisambiguationError:
            return False


class CapitalsGameManager:
    """Класс для работы с игрой -Столицы мира-"""

    cm = CitiesGameManager()

    @check_time
    def game_mode(self, message, db, bot):
        """Режим игры в Столицы Мира
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        if 'прервать' in message.text.lower() or 'прервем' in message.text.lower():
            db.set_game_capitals_mode(message.from_user.id, None)
            bot.send_message(message.chat.id, 'Хорошо, поиграем в другой раз!',
                             reply_markup=ReplyKeyboardRemove())
            return

        phase = db.get_game_capitals_mode_stage(message.from_user.id)

        if not phase:
            self._hello_stage_game_capitals(message, db, bot)
        elif phase == 'Вступление' or phase == 'Игра':
            self._first_game_capitals_stage(message, db, bot)

    def _hello_stage_game_capitals(self, message, db, bot, first_time=True):
        """Приветствие в игре Столицы
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        :param попадаем на фазу приветствия первый раз
        """

        db.set_game_capitals_mode(message.from_user.id, 'Вступление')
        if first_time:
            time.sleep(0.5)
            bot.send_message(message.chat.id, 'Приветствую вас в игре Столицы Мира!')

        # info_msg1 = 'Правила очень простые:\n' \
        #             'Я называю страну, ты - столицу этой страны :)\n' \
        #             'Для победы нужно правильно назвать \n' \
        #             'не меньше 15 столиц из 20'
        info_msg1 = """Правила очень простые:
я называю страну, ты - столицу этой страны :)
Для победы нужно правильно назвать
*не меньше 15 столиц из 20*"""
        info_msg2 = 'Начнем игру?'

        time.sleep(0.5)
        bot.send_message(message.chat.id, info_msg1, parse_mode="Markdown")
        time.sleep(1)
        bot.send_message(message.chat.id, info_msg2, reply_markup=self.cm.set_buttons('Начнем игру', 'Прервать игру'))

    def _first_game_capitals_stage(self, message, db, bot):
        """Первая стадия игры
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        phase = db.get_game_capitals_mode_stage(message.from_user.id)

        # первый ход
        if 'начнем' in message.text.lower() and phase == 'Вступление':
            db.set_game_capitals_mode(message.from_user.id, 'Игра')
            db.create_tmp_game_capitals_table(message.from_user.id)
            self._get_new_capital(db, bot, message)
            return

        # Нажатие на кнопку Не знаю
        if 'не знаю' in message.text.lower() or 'незнаю' in message.text.lower():
            capital = db.return_capital(message.from_user.id)
            bot.send_message(message.chat.id, '*Правильный ответ: {}*'.format(capital),
                             reply_markup=ReplyKeyboardRemove(),
                             parse_mode='Markdown')

            if db.is_game_over(message.from_user.id):
                self._game_over(db, bot, message)
            else:
                self._get_new_capital(db, bot, message)

            return

        # нажатие на кнопку Подсказка
        elif 'подсказка' in message.text.lower():
            capital = db.return_capital(message.from_user.id)
            hide_capital = ''
            for i in range(len(capital)):
                if i > len(capital) / 2:
                    hide_capital += '*'
                else:
                    hide_capital += capital[i]

            bot.send_message(message.chat.id, 'Подсказка: {}'.format(hide_capital),
                             reply_markup=self.cm.set_buttons('Не знаю', 'Прервать игру'),)

            return

        # Анализ сообщения пользователя, верную ли столицу он назвал
        if db.is_right_capital(message.from_user.id, message.text):
            bot.send_message(message.from_user.id, 'Верно!')
            db.set_capital(message.from_user.id)
            time.sleep(0.5)

            # проверка, не закончилась ли игра
            if db.is_game_over(message.from_user.id):
                self._game_over(db, bot, message)
                return
            else:
                self._get_new_capital(db, bot, message)
                return

        else:
            bot.send_message(message.chat.id, 'Неверно.. Попробуйте ещё раз :) Или сдаетесь?',
                             reply_markup=self.cm.set_buttons('Подсказка', 'Не знаю', 'Прервать игру'))
            return

    def _get_new_capital(self, db, bot, message):
        """Метод выдает новую страну для игры
                :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        country_name = db.select_random_capital(message.from_user.id)
        time.sleep(0.5)
        bot.send_message(message.chat.id, '*{} - ?*'.format(country_name),
                         reply_markup=self.cm.set_buttons('Подсказка', 'Не знаю', 'Прервать игру'),
                         parse_mode='Markdown')

    def _game_over(self, db, bot, message):
        """Метод заканчивает игру и подводит итоги
        :param message - сообщение пользователя
        :param db - экземпляр БД
        :param bot - экземпляр бота
        """

        result = db.get_results_capitals(message.from_user.id)
        if result >= 15:
            bot.send_message(message.chat.id, 'Поздравляю, вы победили!')

        else:
            bot.send_message(message.chat.id, 'К сожалению, вы проиграли..')

        db.set_game_capitals_mode(message.from_user.id, None)
        bot.send_message(message.chat.id, 'Ваш результат: {} из 20'.format(result))
        bot.send_message(message.chat.id, 'Спасибо за игру!', reply_markup=ReplyKeyboardRemove())
