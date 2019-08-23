from bot_db import check_time
from telebot import types
from random import randint
from telebot.types import ReplyKeyboardRemove
import time
import wikipedia


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
            bot.send_message(message.chat.id, 'Подождите, ищу информацию про {}..'.format(city))
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

        info_msg1 = 'Правила очень простые:\n'\
                    'Я называю один из городов,\n'\
                    'например Рига. Ты мне говоришь город, \n'\
                    'начинающийся на последнюю букву моего города,\n'\
                    'например Анапа.\n'\
                    'Продержишься 25 ходов - и ты победил :)'
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
*-ы-, -й-, -ь-, -ъ-* не участвуют в игре.
Если город оканчивается на эти буквы, берется последняя разрешенная буква.
Если город оканчивается на *-ый-*, берется буква перед *-ы-*.
"""

        if 'начнем' in message.text.lower():
            db.set_game_cities_mode(message.from_user.id, 'Игра')
            db.create_tmp_game_cities_table(message.from_user.id)
            # bot.send_message(message.chat.id, 'Обратите внимание, буквы'
            #                                   '\n-ы-, -й-, -ь-, -ъ-'
            #                                   '\nне участвуют в игре.'
            #                                   '\nЕсли город оканчивается'
            #                                   '\nна эти буквы, берется последняя'
            #                                   '\nразрешенная буква.',
            #                  reply_markup=self.set_buttons('Прервать игру'))
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

        city_id = db.is_city_exists(message.text)

        if city_id:
            if not db.is_city_was_called(message.text, message.from_user.id):
                if db.is_city_starts_with_end_letter(message.from_user.id, message.text, city_id):
                    if db.is_user_already_win(message.from_user.id):
                        bot.send_message(message.chat.id, 'Вы победили! Игра окончена :)',
                                         reply_markup=ReplyKeyboardRemove())
                        db.set_game_cities_mode(message.from_user.id, None)
                        db.drop_tmp_table('admin.cities_{}'.format(message.from_user.id))
                    else:
                        bot_city = db.select_random_city_against_user_city(message.from_user.id, message.text)
                        bot.send_message(message.chat.id, bot_city,
                                         reply_markup=self.set_buttons('Прервать игру', 'Узнать про {}'.format(bot_city)))
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
