import os
import telebot

from datetime import datetime
from loguru import logger
from telebot import types

bot_token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(bot_token, parse_mode=None)
logger.add("logging.log")


def find_hotels_low(message: types.Message, destination: str, error=False):
    """
    Функция отвечает за принятие количества отелей и id места назначения(города)
    Запрос по отелям производится с платы за 1 день проживания по возрастанию цены

    Parameters:
    -------------
        message : types.Message
            сообщение о количестве отелей

        destination : str
            текстовая информация об уникальном id города, в котором ищется отель
    """
    try:
        hotels_count = message.text
        if hotels_count.isalpha() and error is False:
            if int(hotels_count) > 10:
                hotels_count = "10"
        elif error:
            hotels_count = "5"

        buttons = types.InlineKeyboardMarkup()
        button_yes = types.InlineKeyboardButton(text='Да!', callback_data=f'y|low|{hotels_count}|{destination}')
        button_no = types.InlineKeyboardButton(text='Нет =(', callback_data=f'n|low|{hotels_count}|{destination}')
        buttons.add(button_yes, button_no)
        bot.send_message(message.chat.id, "Произвести вывод фотографий отелей?", reply_markup=buttons)
    except ValueError:
        bot.send_message(message.chat.id, "Введено не число, будет введено базовое значение отелей")
        time = datetime.today().strftime('%Y-%m-%d-%H-%M')
        logger.debug(f"{time}: User input data is not number(hotels)")
        find_hotels_low(message, destination, error=True)
