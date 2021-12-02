import json
import os
import re
import requests
import telebot

from datetime import datetime, timedelta
from loguru import logger
from telebot import types
from telebot.types import InputMediaPhoto

bot_token = os.getenv("BOT_TOKEN")
api_token = os.getenv("API_TOKEN")
bot = telebot.TeleBot(bot_token, parse_mode=None)

headers = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': api_token
}
logger.add("logging.log")


def find_city(message: types.Message, command: str) -> None:
    """
    Функция отвечает за сбор информации об указанном пользователем городе.

    Функция запрашивает у пользователя город поиска, id которого будет передано в следующую функцию

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
                if command == "/lowprice":
                    callback_data = f"{city[1]}|low"
                elif command == "/highprice":
                    callback_data = f"{city[1]}|high"
                elif command == "/bestdeal":
                    callback_data = f"{city[1]}|best"

                city_name = city[0]
                new_button = types.InlineKeyboardButton(text=city_name, callback_data=callback_data)
                cities_button.add(new_button)
            bot.send_message(message.chat.id, "Выберите город:", reply_markup=cities_button)
    except ValueError:

        text = f"В указаном городе нет отелей, либо такого города нет. Введите новый город {command}"
        bot.send_message(message.chat.id, text)


def check_city(url: str, city: str) -> dict or tuple:
    """
    Функция принимает, и возвращает данные с Web-API

    Parameters:
    -------------
        url : str
            URL адресс сайта, содержащего api

        city: str
            название города, которое будет искаться

    Returns:
    ---------
        cities : list
            список городов, найденных в процессе поиска

    """

    parameters = {"query": city, "locale": "ru_RU", "currency": "RUB"}
    response = requests.request("GET", url,
                                headers=headers,
                                params=parameters,
                                timeout=15)
    data = json.loads(response.text)
    entities = data["suggestions"][0]["entities"]
    cities = []
    for entity in entities:
        if entity["type"] == "CITY":
            city_name = entity["caption"]
            city_name = " ".join(re.findall(r"[а-яА-Я]\w*", city_name))
            cities.append([city_name, entity["destinationId"]])
    return cities


def check_hotels(parameters: dict) -> dict or bool:
    """
    Функция отвечает за поиск указанного количества отелей в указаном
    городе (destination). Если сервер не отвечает, возвращает False

    Parameters:
    -------------
        hotels_count : str
            количество отелей, которое требуется вывести

        destination : str
            id города, в котором ведётся поиск отеля

    Returns:
    ---------
        output_message : list[str]
            список, содержащий в себе текст о каждом найденом отеле

        hotel_id : list[str]
            список, содержащий в себе id каждого отеля, для поиска фотографий(если затребуют)

        find_hotels : list[dict]

        Если произошла ошибка TimeoutError то возвращается False
    """
    try:
        url = "https://hotels4.p.rapidapi.com/properties/list"
        response = requests.request("GET", url,
                                    headers=headers,
                                    params=parameters,
                                    timeout=15)
        find_hotels = []
        data = json.loads(response.text)

        for elements in data["data"].get("body").get("searchResults").get("results"):
            hotels_info = dict()
            hotels_info["id"] = elements.get("id")
            hotels_info["name"] = elements.get("name")
            hotels_info["starRating"] = elements.get("starRating")
            hotels_info["address"] = elements.get("address").get("streetAddress")
            hotels_info["locality"] = elements.get("address").get("locality")
            hotels_info["postalCode"] = elements.get("address").get("postalCode")
            hotels_info["countryName"] = elements.get("address").get("countryName")
            hotels_info["distance"] = elements.get("landmarks")[0].get("distance")
            hotels_info["price"] = elements.get("ratePlan").get("price").get("current")
            hotels_info["cur_price"] = elements.get("ratePlan").get("price").get("exactCurrent")
            find_hotels.append(hotels_info)

        hotel_output = send_message(find_hotels)
        output_message = hotel_output[0]
        hotel_id = hotel_output[1]
        result = {key: None for key, _ in enumerate(output_message)}
        for key in result.keys():
            result[key] = [output_message[key], hotel_id[key], find_hotels[key]]
        return result
    except requests.exceptions.ReadTimeout:
        return False
    except KeyError:
        return False


def hotels_photo(parameters: dict, text: str, photo_count: int) -> list:
    """
     Функция отвечает за нахождение фотографий, по id переданному в parameters

     Parameters:
     --------------
        parameters : dict
            словарь, содержащий в себе id отеля

        text : str
            сообщение, содержащее информацию об отеле, подкрепляется к InputMediaPhoto
            для последующей передачи пользователю

        photo_count : int
            число фотографий, которое просит вывести пользователь, если больше 10,
            то приравнивается к 10

    Returns:
    ---------
        photo_list ; list
            список содержащий в себе объекты InputMediaPhoto, в последующем будет передан,
            для вывода сообщений с фотографиями отеля
    """
    if photo_count > 10:
        photo_count = 10
    url = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
    response = requests.request("GET", url, headers=headers, params=parameters)
    data = json.loads(response.text)
    photo_list = []
    data = data.get("hotelImages")
    for number, element in enumerate(data):
        if number < photo_count:
            image_url = element["baseUrl"]
            image_url = image_url.replace("{size}", "b")
            if number == 0:
                photo_list.append(InputMediaPhoto(media=image_url, caption=text))
            else:
                photo_list.append(InputMediaPhoto(media=image_url))
    return photo_list


def send_message(hotels: list[dict]) -> tuple:
    """
    Функция отвечает за составление текста сообщения с последующей передачей кортежа,
    содержащего список отелей с описанием отелей и список c id каждого отеля

    Parameters:
    -------------
        hotels: list[dict]
            список содержащий словарь с данными об отеле

    Returns:
    ---------
        hotels_text : list
            список с описаниями отелей

        hotel_id : list
            список с id отелей, для последующего поиска фотографий(если потребуется)
    """

    hotels_text = []
    hotel_id = []
    for hotel in hotels:
        hotel_id.append(hotel["id"])
        name = hotel['name']
        rating = hotel['starRating']
        place = f"{hotel['postalCode']}, {hotel['countryName']}, {hotel['locality']}, {hotel['address']}"
        cost = hotel['price']
        distance = hotel["distance"]
        text = f"{name}\nРейтинг: {rating}\n" \
               f"Адрес: {place}\n" \
               f"Расстояние от центра: {distance}\n" \
               f"Стоимость дня: {cost}\n"
        hotels_text.append(text)
    return hotels_text, hotel_id
