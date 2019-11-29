from telebot.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton


class BotButtons(object):
    """Класс для работы с кнопками"""

    def gen_inline_buttons(self, *buttons):
        """Метод создает кнопку с вопросом о записи информации в бд
        :param buttons - кортежи/списки из двух элементов, где 1-ый - текст кнопки, 2-ой - callback data кнопки
        """

        markup = InlineKeyboardMarkup()
        markup.row_width = 2
        my_buttons = [InlineKeyboardButton(button[0], callback_data=button[1]) for button in buttons]
        markup.add(*my_buttons)

        return markup

    def gen_underline_butons(self, *buttons, **second_row_buttons):
        """Метод размещает под панелью клавиатуры одну или несколько кнопок
        :param buttons - текст кнопок
        """

        markup = ReplyKeyboardMarkup(row_width=len(buttons), one_time_keyboard=True, resize_keyboard=True)
        my_buttons = [KeyboardButton(button_text) for button_text in buttons]
        if second_row_buttons.get('second_row_button'):
            my_buttons.append(second_row_buttons.get('second_row_button'))
        markup.add(*my_buttons)

        return markup
