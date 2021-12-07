import datetime
import sqlite3
import telebot

from config import BOT_TOKEN
from urls_and_param import urls
from datetime import datetime, timedelta
from database.database import add_user, add_search_history_city, create_table, get_history, User
from functions.api_request import check_hotels, find_city, find_hotels
from functions.photo_sender import find_photo
from loguru import logger
from telebot import types

logger.add("logging.log")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
url_and_parameters = urls


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
    Функция отвечает за прием команды lowprice с последующим запросом города
    и передачей информации в следующую функцию

    Parameters:
    -------------
        message : types.Message
            Сообщение отправленное от пользователя, боту.
            Является классом библиотеки telebot
    """

    bot.send_message(message.chat.id, "Введите название города для поиска отелей")
    command = message.text
    bot.register_next_step_handler(message, city, command)


@bot.message_handler(commands="highprice")
def high_price(message: types.Message) -> None:
    """
        Функция отвечает за прием команды highprice с последующим запросом города
        и передачей информации в следующую функцию

        Parameters:
        -------------
            message : types.Message
                Сообщение отправленное от пользователя, боту.
                Является классом библиотеки telebot
    """

    bot.send_message(message.chat.id, "Введите название города для поиска отелей")
    command = message.text
    bot.register_next_step_handler(message, city, command)


@bot.message_handler(commands="bestdeal")
def best_deal(message: types.Message):
    """
    Функция отвечает за прием команды bestdeal с последующим запросом города
    и передачей информации в следующую функцию

    Parameters:
    -------------
        message : types.Message
            Сообщение отправленное от пользователя, боту.
            Является классом библиотеки telebot
    """

    bot.send_message(message.chat.id, "Введите название города для поиска отелей")
    command = message.text
    bot.register_next_step_handler(message, city, command)


@bot.message_handler(commands="history")
def history(message: types.Message) -> None:
    """
    Функция принимает входящую команду history и передаёт пользователю историю его запросов

    Parameters:
    -------------
        message : types.Message
            сообщение содержащее команду, а также позволяет взять id пользователя
    """

    result = get_history(message.from_user.id)
    if result[1] == 0:
        text = "В базе данных нет ваших запросов, сначала стоит поискать что-то"
        bot.send_message(message.chat.id, text)
        logger.debug("history without user's info(data not found)")
    elif 0 < result[1] < 3:
        text = "В базе данных  недостаточно ваших запросов, будет выведено меньше 3 запросов"
        bot.send_message(message.chat.id, text)
        bot.send_message(message.chat.id, result[0])
    else:
        bot.send_message(message.chat.id, result[0])


def price_range(message: types.Message, data: list, parameters: dict) -> None:
    """
    Функция принимает данные и проверяет корректность ввода пользователем данных о диапозоне цен
    для поиска отелей

    Parameters:
    -------------
        message: types.Message
            Сообщение с диапозоном цен

        data : list
            основные сведения необходимые для поиска отелей
            data[0] - y|n ответ на вывод фотографий
            data[1] - best название команды, требуется для записи в историю запросов
            data[2] - число отелей для поиска
            data[3] - id города в котором ищется отель

        parameters : dict
            установки для запроса в базу данных, передаются в следующую функцию
    """

    try:
        prices = message.text

        if prices.find(","):
            prices = prices.replace(",", ".")
        prices = prices.split("-")

        for index, _ in enumerate(prices):
            prices[index] = round(float(prices[index]))

        if int(prices[0]) > int(prices[1]):
            raise ValueError
        else:
            data.append(prices)
            bot.send_message(message.chat.id, "Укажите диапозон расстояния отеля от центра города.\nПример: 1.5-4")
            bot.register_next_step_handler(message, distance_range, data, parameters)

    except ValueError:
        bot.send_message(message.chat.id, "Указано неверное значение диапозона цен, повторите ввод")
        bot.register_next_step_handler(message, price_range, data, parameters)
    except IndexError:
        bot.send_message(message.chat.id, "Указано неверное значение диапозона цен, повторите ввод")
        bot.register_next_step_handler(message, price_range, data, parameters)


def distance_range(message: types.Message, data: list, parameters: dict):
    """
    Функция принимает данные и проверяет корректность ввода этих данных о диапозоне
    дистанции для поиска отелей с последующим выводом ответа для пользователя

    Parameters:
    -------------
        message: types.Message
            Сообщение с диапозоном цен

        data : list
            основные сведения необходимые для поиска отелей
            data[0] - y|n ответ на вывод фотографий
            data[1] - best название команды, требуется для записи в историю запросов
            data[2] - число отелей для вывода
            data[3] - id города в котором ищется отель
            data[4] - диапозон стоимости дня проживания

        parameters : dict
            установки для запроса в базу данных, передаются в следующую функцию
    """

    try:
        distance = message.text
        if distance.find(","):
            distance = distance.replace(",", ".")
        distance = distance.split("-")
        min_distance = float(distance[0])
        max_distance = float(distance[1])
        prices = data[4]
        min_price = prices[0]
        max_price = prices[1]
        parameters["priceMin"] = min_price
        parameters["priceMax"] = max_price
        result = check_hotels(parameters)

        if not result:
            raise NameError("Отели не найдены")

        hotel_count = int(data[2])
        keys = set([key for key in result.keys()])
        for key in keys:
            hotel_distance = result[key][2]["distance"].split(" ")
            hotel_distance = hotel_distance[0].replace(",", ".")
            hotel_distance = float(hotel_distance)
            hotel_price = result[key][2]["cur_price"]
            if min_distance > hotel_distance or hotel_distance > max_distance:
                del result[key]
            elif min_price > hotel_price or max_price < hotel_price:
                del result[key]

        while len(result.keys()) > hotel_count:
            new_keys = [key for key in result.keys()]
            del result[new_keys[-1]]
            new_keys.pop(-1)

        if len(result.keys()) < hotel_count:
            bot.send_message(message.chat.id, "Отелей нашлось меньше чем надо =(")

        if data[0] == "y":
            output_message = bot.send_message(message.chat.id, "Сколько фотографий вывести")
            bot.register_next_step_handler(output_message, photo, result)
        elif data[0] == "n":
            output_message = ""
            for index in result.keys():
                output_message += result[index][0] + "\n"
            bot.send_message(message.chat.id, output_message)

        history_hotels = []
        for value in result.values():
            history_hotels.append(value[2])
        add_search_history_city(message.chat.id, "/bestdeal", history_hotels)
    except ValueError:
        bot.send_message(message.chat.id, "Указано неверное значение дистанции, повторите ввод")
        bot.register_next_step_handler(message, distance_range, data, parameters)
    except NameError:
        bot.send_message(message.chat.id, f"Отели в городе не найдены. Введите новый запрос /bestdeal")


def city(message: types.Message, city_command: str) -> None:
    """
    Функция отвечает за прием сообщения с названием города и получением
    результата по поиску города в базе данных.
    При отсутствии результата пользователю передаётся сообщение, что стоит указать другой город

    Parameters:
    -------------
        message : types.Message
            сообщение с названием города

        city_command : str
            команда использованная пользователем
    """

    result = find_city(message, city_command)

    if isinstance(result, tuple):
        bot.send_message(message.chat.id, result[1])

    bot.send_message(message.chat.id, "Выберите город:", reply_markup=result)


def hotel(message: types.Message, hotel_data: str) -> None:
    """
    Функция отвечает за прием сообщения с количеством отелей для вывода, id города и командой
    При ошибке, будет произведён поиск со стандартным значением для вывода отелей

    Parameters:
    -------------
        message : types.Message
            сообщение с указанием числа отелей для вывода

        hotel_data : str
            строковая информация, сиволом "|" разделяется необходимая информация
            в последующем используется для создания data: list
            data[0] - id города
            data[1] - название команды
    """

    data = hotel_data.split("|")
    id_city = data[0]
    command = data[1]
    result = find_hotels(message, id_city, command)

    if isinstance(result, bool):
        bot.send_message(message.chat.id, "Введено не число, будет введено базовое значение отелей")
        result = find_hotels(message, id_city, command, error=True)

    bot.send_message(message.chat.id, "Произвести вывод фотографий отелей?", reply_markup=result)


def photo(message: types.Message, photo_data: dict, error=False):
    """
    Функция отвечает за прием сообщения с количеством фотографий на вывод,
    а также словаря с информацией о найденых отелях.

    Parameters:
    -------------
        message : types.Message
            сообщение с количеством фотографий для вывода

        photo_data : dict
            словарь с информацией о найденных отелях допуск к отелю по ключу
            photo_data[0][0] - текстовое сообщение о найденом отеле
            photo_data[0][1] - id отеля
            photo_data[0][2] - словарь с основной информацией об отеле от id до цены за день проживания

        error : bool
            булевое значение отвечает за ошибку ввода пользователем числа фотографий для вывода
            изначально является False
    """

    try:
        if error:
            photo_count = 5
        else:
            photo_count = int(message.text)
        result = find_photo(photo_data, photo_count)
        for media in result:
            bot.send_media_group(message.chat.id, media)
    except ValueError:
        bot.send_message(message.chat.id, "Введено не число, будет использовано стандартное значение")
        time = datetime.today().strftime('%Y-%m-%d-%H-%M')
        logger.debug(f"{time}: User input data is not number(photos)")
        photo(message, photo_data, error=True)


@bot.callback_query_handler(func=lambda call: call.data[0] in ["y", "n"])
def callback_photo(call: types.CallbackQuery) -> None:
    """
    Callback функция, обрабатывает нажатие на кнопки, касающиеся вывода фотографий
    """

    try:
        check_in = datetime.today().strftime('%Y-%m-%d')
        check_out = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        data = call.data.split("|")
        destination = data[3]
        hotels_count = data[2]
        parameters = url_and_parameters["parameters_casual"]
        parameters["pageSize"] = hotels_count
        parameters["destinationId"] = destination
        parameters["checkIn"] = check_in
        parameters["checkOut"] = check_out

        if data[1] == "low":
            parameters["sortOrder"] = "PRICE"
            result = check_hotels(parameters)
            command = "/lowprice"
        elif data[1] == "high":
            parameters["sortOrder"] = "PRICE_HIGHEST_FIRST"
            result = check_hotels(parameters)
            command = "/highprice"
        elif data[1] == "best":
            parameters["sortOrder"] = "PRICE"
            parameters["pageSize"] = 25
            message = bot.send_message(call.message.chat.id, "Введите диапозон цен. Пример 1000-9000")
            bot.register_next_step_handler(message, price_range, data, parameters)
            return None

        if not result:
            raise NameError("Отели не найдены")

        if data[0] == "y":
            bot.send_message(call.message.chat.id, "Сколько фотографий вывести")
            bot.register_next_step_handler(call.message, photo, result)
        elif data[0] == "n":
            output_message = ""
            for index in result.keys():
                output_message += result[index][0] + "\n"
            bot.send_message(call.message.chat.id, output_message)

        history_hotels = []
        for value in result.values():
            history_hotels.append(value[2])
        add_search_history_city(call.message.chat.id, command, history_hotels)

    except NameError:
        bot.send_message(call.message.chat.id, f"Отели в городе не найдены. Введите новый запрос {command}")
        time = datetime.today().strftime('%Y-%m-%d-%H-%M')
        logger.debug(f"{time}: Hotels not found")
    except TimeoutError:
        bot.send_message(call.message.chat.id, "Сервер не даёт ответа, возможно он сломался. Повторите позже")
        time = datetime.today().strftime('%Y-%m-%d-%H-%M')
        logger.debug(f"{time}: Server didn't respond, bad request")


@bot.callback_query_handler(func=lambda call: call.data)
def callback(call: types.CallbackQuery):
    """
    Callback функция, обрабатывает нажатие на кнопки касающееся вывода города
    """

    bot.send_message(call.message.chat.id, "Сколько вывести отелей? Максимум 10")
    bot.register_next_step_handler(call.message, hotel, call.data)


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
