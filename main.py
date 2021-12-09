import datetime
import sqlite3
import telebot

from loguru import logger
from telebot import types
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP

from config import BOT_TOKEN
from datetime import datetime, timedelta
from database.database import add_user, add_search_history_city, get_dates
from database.database import create_table, get_history, check_dates, update_dates, update_request
from functions.api_request import check_hotels, find_city, find_hotels
from functions.photo_sender import find_photo
from urls_and_param import urls

logger.add("logging.log", encoding="utf-8")
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
    try:
        add_user(user_id, user_name)
    except sqlite3.OperationalError:
        create_table()
        add_user(user_id, user_name)
    finally:
        output_message = "Добро пожаловать, я бот который поможет найти отель по тем или иным условиям.\n" \
                         "Используйте /help, чтобы узнать, что я умею"
        bot.reply_to(message, output_message)
        logger.success(f"Юзер №{message.chat.id} получил приветственное сообщение")


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
    logger.success(f"Юзер №{message.chat.id} использовал команду /help")


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
    logger.success(f"Юзер №{message.chat.id} использовал команду /lowprice")
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
    logger.success(f"Юзер №{message.chat.id} использовал команду /highprice")
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
    logger.success(f"Юзер №{message.chat.id} использовал команду /bestdeal")
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
        logger.success(f"Команда /history выполнена, но у Юзера №{message.chat.id} нет истории запросов")
    elif 0 < result[1] < 3:
        text = "В базе данных  недостаточно ваших запросов, будет выведено меньше 3 запросов"
        bot.send_message(message.chat.id, text)
        bot.send_message(message.chat.id, result[0])
        logger.success(f"Команда /history выполнена, но у Юзера №{message.chat.id} меньше 3 запросов")

    else:
        bot.send_message(message.chat.id, result[0])
        logger.success(f"Команда /history от Юзера №{message.chat.id} выполнена")


def dates(message: types.Message):
    """
    Промежуточная функция, создаёт календарь для выбора даты въезда

    Parameters:
    -------------
        message : types.Message
            сообщение пользователя, требуется для отправки календаря по id пользователя
    """
    min_date = datetime.date(datetime.now())
    calendar, step = DetailedTelegramCalendar(min_date=min_date, locale="ru").build()
    bot.send_message(message.chat.id,
                     f"Выберите дату въезда",
                     reply_markup=calendar)
    logger.success(f"Юзеру №{message.chat.id} отправлен календарь въезда")


def send_date(message: types.Message):
    """
    Функция отвечающая за проверку введеных дат въезда и выезда пользователя
    с последующим форматированием данных для запроса
    Если команда пользователя /lowprice или /highprice, то после форматирования дат
    происходит переход к поиску отелей по заданным параметрам
    Если команда пользователя /bestdeal то после форматирования дат, происходит запрос
    диапозона цен и выполнени последующих команд

    Parameters:
    -------------
        message : types.Message
            сообщение от пользователя содержащее информацию об id чата
    """
    try:
        parameters = url_and_parameters["parameters_casual"]
        user_dates = get_dates(message.chat.id)
        check_in = datetime.strptime(user_dates[0], "%Y-%m-%d")
        check_out = datetime.strptime(user_dates[1], "%Y-%m-%d")
        day_difference = (check_out - check_in).days

        if day_difference > 28:
            text = "Забронировать можно не более чем на 28 дней, произведу расчет на 28 дней"
            bot.send_message(message.chat.id, text)
            parameters["checkIn"] = check_in.strftime("%Y-%m-%d")
            parameters["checkOut"] = (check_in + timedelta(28)).strftime("%Y-%m-%d")
            logger.warning(f"Юзер №{message.chat.id} превысил максимальный срок бронирования")
        else:
            parameters["checkIn"] = check_in.strftime("%Y-%m-%d")
            parameters["checkOut"] = check_out.strftime("%Y-%m-%d")

        update_dates(message.chat.id, "1", "1")

        command = url_and_parameters["command"]
        sql_result = update_request(message.chat.id, request=1)
        photo_answer = sql_result[1]
        hotel_count = sql_result[0]
        if command == "low":
            parameters["sortOrder"] = "PRICE"
            result = check_hotels(parameters)
            command = "/lowprice"
        elif command == "high":
            parameters["sortOrder"] = "PRICE_HIGHEST_FIRST"
            result = check_hotels(parameters)
            command = "/highprice"
        elif command == "best":
            parameters["sortOrder"] = "PRICE"
            parameters["pageSize"] = 25
            message = bot.send_message(message.chat.id, "Введите диапозон цены за 1 день проживания. Пример 1000-9000")
            bot.register_next_step_handler(message, price_range, day_difference, parameters)
            return None

        if not result:
            raise NameError("Отели не найдены")

        if len(result.keys()) < hotel_count:
            bot.send_message(message.chat.id, "Отелей нашлось меньше чем надо =(")

        if photo_answer == "y":
            photo(message, result)
        elif photo_answer == "n":
            output_message = ""
            for index in result.keys():
                output_message += result[index][0] + "\n"
            bot.send_message(message.chat.id, output_message)
            logger.success(f"Юзеру №{message.chat.id} отправлен результат поиска отелей")

        history_hotels = []
        for value in result.values():
            history_hotels.append(value[2])
        add_search_history_city(message.chat.id, command, history_hotels)
        logger.success(f"История запроса для Юзера №{message.chat.id} записана")
    except NameError:
        bot.send_message(message.chat.id, f"Отели по заданным параметрам не найдены. Введите новый запрос {command}")
        logger.warning(f"Отели для Юзера №{message.chat.id} не найдены")
    except TimeoutError:
        bot.send_message(message.chat.id, "Сервер не даёт ответа, возможно он сломался. Повторите позже")
        logger.error("Сервер не отвечает, проблема не в боте")


def price_range(message: types.Message, day_difference: int, parameters: dict) -> None:
    """
    Функция принимает данные и проверяет корректность ввода пользователем данных о диапозоне цен
    для поиска отелей

    Parameters:
    -------------
        message: types.Message
            Сообщение с диапозоном цен

        day_difference : int
            количество дней от даты въезда до даты выезда

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
            bot.send_message(message.chat.id, "Укажите диапозон расстояния отеля от центра города.\nПример: 1.5-4")
            bot.register_next_step_handler(message, distance_range, prices, day_difference, parameters)

    except ValueError:
        bot.send_message(message.chat.id, "Указано неверное значение диапозона цен, повторите ввод")
        bot.register_next_step_handler(message, price_range, parameters)
    except IndexError:
        bot.send_message(message.chat.id, "Указано неверное значение диапозона цен, повторите ввод")
        bot.register_next_step_handler(message, price_range, parameters)


def distance_range(message: types.Message, prices: list, day_difference: int, parameters: dict):
    """
    Функция принимает данные и проверяет корректность ввода этих данных о диапозоне
    дистанции для поиска отелей с последующим выводом ответа для пользователя

    Parameters:
    -------------
        message: types.Message
            Сообщение с диапозоном цен

        prices : list
            информация о минимальной и максимальной цене

        day_difference : int
            количество дней от даты въезда до даты выезда

        parameters : dict
            установки для запроса в базу данных, передаются в следующую функцию
    """

    try:
        sql_result = update_request(message.chat.id, request=1)
        photo_answer = sql_result[1]
        hotel_count = sql_result[0]
        distance = message.text
        if distance.find(","):
            distance = distance.replace(",", ".")
        distance = distance.split("-")
        min_distance = float(distance[0])
        max_distance = float(distance[1])
        min_price = prices[0]
        max_price = prices[1]
        parameters["priceMin"] = min_price
        parameters["priceMax"] = max_price
        result = check_hotels(parameters)

        if not result:
            raise NameError("Отели не найдены")

        keys = set([key for key in result.keys()])
        for key in keys:
            hotel_distance = result[key][2]["distance"].split(" ")
            hotel_distance = hotel_distance[0].replace(",", ".")
            hotel_distance = float(hotel_distance)
            hotel_price = result[key][2]["cur_price"] / day_difference
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

        if photo_answer == "y":
            photo(message, result)
        elif photo_answer == "n":
            output_message = ""
            for index in result.keys():
                output_message += result[index][0] + "\n"
            bot.send_message(message.chat.id, output_message)
            output_message = "/lowprice - вывод информации об отелях с самой низкой ценой по городу\n" \
                             "/highprice - вывод информации об отелях с самой высокой ценой по городу\n" \
                             "/bestdeal - вывод наиболее подходящих отелей по заданым параметрам\n" \
                             "/history - вывод информации о ранее введеных запросах"
            bot.send_message(message.chat.id, output_message)
            logger.success(f"Юзеру №{message.chat.id} отправлено сообщение с командами")

        history_hotels = []
        for value in result.values():
            history_hotels.append(value[2])
        add_search_history_city(message.chat.id, "/bestdeal", history_hotels)

    except ValueError:
        bot.send_message(message.chat.id, "Указано неверное значение дистанции, повторите ввод")
        bot.register_next_step_handler(message, distance_range, prices, parameters)
        logger.error(f"Юзер №{message.chat.id} ввел неверное значение дистанции")
    except NameError:
        bot.send_message(message.chat.id, f"Отели в городе не найдены. Введите новый запрос /bestdeal")
        logger.warning(f"Отели по запросу Юзера №{message.chat.id} не найдены")


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
    logger.success(f"Юзер №{message.chat.id} ввел город = {message.text}")
    update_request(message.chat.id)
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
    logger.success(f"Юзер №{message.chat.id} ввел число отелей = {message.text}")
    data = hotel_data.split("|")
    id_city = data[0]
    command = data[1]
    result = find_hotels(message, id_city, command)

    if isinstance(result, bool):
        bot.send_message(message.chat.id, "Введено не число, будет введено базовое значение отелей")
        result = find_hotels(message, id_city, command, error=True)

    bot.send_message(message.chat.id, "Произвести вывод фотографий отелей?", reply_markup=result)


def photo_number(message: types.Message, error: bool = False):
    try:
        if error:
            photo_count = 5
        else:
            photo_count = int(message.text)
            if photo_count > 10:
                photo_count = 10
                bot.send_message(message.chat.id, "Максимально допустимое число фотографий = 10")
                logger.warning(f"Юзер №{message.chat.id} превысил количество фотографий на вывод")
            logger.success(f"Юзер №{message.chat.id} ввел число фотографий = {message.text}")
        update_request(message.chat.id, photos_count=photo_count)
        dates(message)
    except ValueError:
        bot.send_message(message.chat.id, "Введено не число, будет использовано стандартное значение")
        logger.warning(f"Юзер №{message.chat.id} ввел не число, используется стандартное значение для вывода")
        photo_number(message, error=True)


def photo(message: types.Message, photo_data: dict):
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
    sql_result = update_request(message.chat.id, request=2)
    photo_count = sql_result[0]
    result = find_photo(photo_data, photo_count)
    for media in result:
        bot.send_media_group(message.chat.id, media)
    logger.success(f"Юзеру №{message.chat.id} отправлены сообщения с фотографиями")
    output_message = "/lowprice - вывод информации об отелях с самой низкой ценой по городу\n" \
                     "/highprice - вывод информации об отелях с самой высокой ценой по городу\n" \
                     "/bestdeal - вывод наиболее подходящих отелей по заданым параметрам\n" \
                     "/history - вывод информации о ранее введеных запросах"
    bot.send_message(message.chat.id, output_message)
    logger.success(f"Юзеру №{message.chat.id} отправлено сообщение с командами")


@bot.callback_query_handler(func=lambda call: call.data[0] in ["y", "n"])
def callback_data(call: types.CallbackQuery) -> None:
    """
    Callback функция, обрабатывает нажатие на кнопки с информацией об ответе,
    data : list
            основные сведения необходимые для поиска отелей
            data[0] - y|n ответ на вывод фотографий
            data[1] - best название команды, требуется для записи в историю запросов
            data[2] - число отелей для поиска
            data[3] - id города в котором ищется отель
    """

    data = call.data.split("|")
    destination = data[3]
    hotels_count = int(data[2])
    url_and_parameters["parameters_casual"]["pageSize"] = hotels_count
    url_and_parameters["parameters_casual"]["destinationId"] = destination
    url_and_parameters["command"] = data[1]
    update_request(call.message.chat.id, hotels_count=hotels_count)
    update_request(call.message.chat.id, answer=data[0])
    logger.success(f"От Юзера №{call.message.chat.id} получен ответ по выводу фотографий")
    if data[0] == "y":
        bot.send_message(call.message.chat.id, "Сколько фотографий вывести?")
        bot.register_next_step_handler(call.message, photo_number)
    if data[0] == "n":
        dates(call.message)


@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def callback_calendar(call: types.CallbackQuery):
    """
    Callback функция, отвечает за выбор дат календаря
    """

    user_id = call.message.chat.id
    sql_result = check_dates(call.message.chat.id)
    if sql_result[1] == 1:
        min_date = datetime.date(datetime.now())
        result, key, step = DetailedTelegramCalendar(min_date=min_date).process(call.data)
    elif sql_result[1] == 2:
        min_date = get_dates(call.message.chat.id)
        min_date = datetime.date(datetime.strptime(min_date[0], "%Y-%m-%d"))
        result, key, step = DetailedTelegramCalendar(min_date=min_date).process(call.data)

    if LSTEP[step] == "month":
        choice = "месяц"
    elif LSTEP[step] == "day":
        choice = "день"

    if not result and key:
        bot.edit_message_text(f"Выберите {choice}",
                              call.message.chat.id,
                              call.message.message_id,
                              reply_markup=key)
    elif result:
        check = check_dates(user_id)
        if check[1] == 1:
            update_dates(user_id, date_in=str(result))
            bot.edit_message_text(f"Выбранная дата: {result}",
                                  call.message.chat.id,
                                  call.message.message_id)
            max_date = result + timedelta(28)
            calendar, step = DetailedTelegramCalendar(min_date=result, max_date=max_date).build()
            bot.send_message(call.message.chat.id,
                             f"Выберите дату выезда",
                             reply_markup=calendar)
            logger.success(f"Юзеру №{call.message.chat.id} отправлен календарь выезда")
        elif check[1] == 2:
            update_dates(user_id, date_out=result)
            bot.edit_message_text(f"Выбранная дата: {result}",
                                  call.message.chat.id,
                                  call.message.message_id)
            logger.success(f"Юзер №{call.message.chat.id} завершил выбор дат")
            send_date(call.message)


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
    logger.success(f"Юзер №{message.from_user.id} ввел неизвестную боту команду или слово")
    bot.reply_to(message, "Мне не удается понять, что от меня требуется, используйте"
                          " команду /help для получения справки по моим возможностям")


if __name__ == "__main__":
    bot.infinity_polling()
