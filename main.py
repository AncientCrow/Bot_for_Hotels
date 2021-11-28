import datetime
import os
import sqlite3

import telebot

from functions.low_price import check_city, check_hotels, hotels_photo
from functions.history import add_user, add_search_history_city, create_table, User
from loguru import logger
from telebot import types

logger.add("logging.log")
bot_token = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(bot_token, parse_mode=None)


@bot.message_handler(commands=["hello-world", "hello_world", "start"])
@bot.message_handler(func=lambda msg: msg.text.lower() == "привет")
def welcome_message(message: types.Message) -> None:
    """
    Приветственная функция. Реагирует на команду /hello-world или
    на сообщение состоящее из слова 'привет'

    Parameters:
    -------------
        message : types.Message
            Сообщение отправленное от пользователя, боту.
            Является классом библиотеки telebot
    """
    user_id = message.chat.id
    user_name = f"{message.from_user.first_name} {message.from_user.last_name}"
    user = User(user_id, user_name)
    try:
        add_user(user)
    except sqlite3.OperationalError:
        create_table()
        add_user(user)
    finally:
        output_message = "Добро пожаловать, я бот который поможет найти отель по тем или иным условиям.\n" \
                         "Используйте /help, чтобы узнать, что я умею"
        bot.reply_to(message, output_message)




@bot.message_handler(commands="help")
def help_message(message: types.Message) -> None:
    """
    Функция, передаёт информацию о возможных командах бота

    Parameters:
    -------------
        message : types.Message
            Сообщение отправленное от пользователя, боту.
            Является классом библиотеки telebot
    """

    output_message = f"/hello_world - приветственное сообщение\n" \
                     "/help - справка о возможностях бота\n" \
                     "/lowprice - вывод информации об отелях с самой низкой ценой по городу\n" \
                     "/highprice - вывод информации об отелях с самой высокой ценой по городу\n" \
                     "/bestdeal - вывод наиболее подходящих отелей по заданым параметрам\n" \
                     "/history - вывод информации о ранее введеных запросах"
    bot.reply_to(message, output_message)


@bot.message_handler(commands="lowprice")
def low_price(message: types.Message) -> None:
    """
        Функция отвечает за прием команды с последующим запросом города
        и передачей информации в следующую функцию

        Parameters:
        -------------
            message : types.Message
                Сообщение отправленное от пользователя, боту.
                Является классом библиотеки telebot
    """

    city = bot.send_message(message.chat.id, "Введите название города для поиска отелей")
    bot.register_next_step_handler(city, find_city)


def find_city(message: types.Message) -> None:
    """
    Функция отвечает за сбор информации об указанном пользователем городе.

    Функция запрашивает у пользователя город поиска и количество выводимых отелей,
    дополнительно будет запрашиваться разрешение на вывод изображений отеля

    Parameters:
    -------------
        message : types.Message
            Сообщение отправленное от пользователя боту, содержит название города.
            Является классом библиотеки telebot
    """

    url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    try:
        city_response = check_city(url, message.text)
        if len(city_response) == 0:
            raise ValueError
        else:
            cities_button = types.InlineKeyboardMarkup()
            for city in city_response:
                callback_data = city[1]
                city_name = city[0]
                new_button = types.InlineKeyboardButton(text=city_name, callback_data=callback_data)
                cities_button.add(new_button)
            bot.send_message(message.chat.id, "Выберите город:", reply_markup=cities_button)

    except ValueError:
        bot.send_message(message.chat.id, "В указаном городе нет отелей, либо такого города нет")
        time = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M')
        logger.debug(f"{find_city.__name__}{time}: Hotels not found ")


def find_hotels(message: types.Message, destination: str, error=False):
    """
    Функция отвечает за принятие количества отелей и id места назначения(города)
    Запрос по отелям производится с платы за 1 день проживания

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
        button_yes = types.InlineKeyboardButton(text='Да!', callback_data=f'y|{hotels_count}|{destination}')
        button_no = types.InlineKeyboardButton(text='Нет =(', callback_data=f'n|{hotels_count}|{destination}')
        buttons.add(button_yes, button_no)
        bot.send_message(message.chat.id, "Произвести вывод фотографий отелей?", reply_markup=buttons)
    except ValueError:
        bot.send_message(message.chat.id, "Введено не число, будет введено базовое значение отелей")
        time = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M')
        logger.debug(f"{time}: User input data is not number(hotels)")
        find_hotels(message, destination, error=True)


def find_photo(message: types.Message or int, hotels: tuple, error=False):
    """
    Функция отвечает за создание сообщения для пользователя с выводом фотографий

    Parameters:
    --------------
        message : types.Message
            сообщение с количеством фотографий на вывод
    """
    try:
        if error:
            photo_count = 5
        else:
            photo_count = int(message.text)
        hotels_list = hotels[0]
        hotels_id = hotels[1]
        photos = []

        for index, hotel in enumerate(hotels_list):
            querystring = {"id": {hotels_id[index]}}
            photos.append(hotels_photo(querystring, hotel, photo_count))
        for elements in photos:
            bot.send_media_group(message.chat.id, media=elements)
    except ValueError:
        text = bot.send_message(message.chat.id, "Указано не число, будет выведено базовое значение фотографий")
        time = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M')
        logger.debug(f"{time}: User input data is not number(photos)")
        find_photo(text, hotels, error=True)


@bot.callback_query_handler(func=lambda call: call.data[0] in ["y", "n"])
def callback_photo(call: types.CallbackQuery) -> None:
    """Callback функция, обрабатывает нажатие на кнопки, касающиеся вывода фотографий"""
    try:
        data = call.data.split("|")
        result = check_hotels(data[1], data[2])
        hotels = result[0]
        add_search_history_city(call.message.chat.id, result[2])
        if data[0] == "y":
            if len(hotels) == 0:
                raise ValueError("Отели не найдены")
            message = bot.send_message(call.message.chat.id, "Сколько фотографий вывести")
            bot.register_next_step_handler(message, find_photo, result)
        elif data[0] == "n":
            message = ""
            if len(result[0]) == 0:
                raise ValueError("Отели не найдены")
            else:
                for hotel in hotels:
                    message += hotel + "\n"
                bot.send_message(call.message.chat.id, message)
    except ValueError:
        bot.send_message(call.message.chat.id, "Отели в городе не найдены. Введите новый город /lowprice")
        time = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M')
        logger.debug(f"{time}: Hotels not found")


@bot.callback_query_handler(func=lambda call: call.data)
def callback(call: types.CallbackQuery):
    """Callback функция, обрабатывает нажатие на кнопки касающееся вывода города"""
    id_city = call.data
    bot.send_message(call.message.chat.id, "Сколько вывести отелей? Максимум 10")
    bot.register_next_step_handler(call.message, find_hotels, id_city)


@bot.message_handler(func=lambda m: True)
def not_command_message(message: types.Message) -> None:
    """
    Функция отвечает за распознавание сообщений, не относящихся к командам

    Parameters:
    -------------
        message : types.Message
            Сообщение отправленное от пользователя, боту.
            Является классом библиотеки telebot
    """
    bot.reply_to(message, "Мне не удается понять, что от меня требуется, используйте"
                          " команду /help для получения справки по моим возможностям")


if __name__ == "__main__":
    bot.infinity_polling()
