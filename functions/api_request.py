import json
import re
from typing import List, Tuple

import requests

from datetime import datetime
from loguru import logger
from telebot import types
from telebot.types import InputMediaPhoto

from config import API_TOKEN
from urls_and_param import urls

url_and_parameters = urls

headers = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': API_TOKEN
}


def find_city(message: types.Message, command: str) -> types.InlineKeyboardMarkup or Tuple[bool, str]:
    """
    Функция отвечает за сбор информации об указанном пользователем городе.

    Функция запрашивает у пользователя город поиска, id которого будет передано в следующую функцию

    Parameters:
    -------------
        message : types.Message
            Сообщение отправленное от пользователя боту, содержит название города.
            Является классом библиотеки telebot
    """

    url = url_and_parameters["url_city"]
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
            return cities_button
    except ValueError:
        text = f"В указаном городе нет отелей, либо такого города нет. Введите новый город {command}"
        return False, text


def find_hotels(message: types.Message, destination: str, command: str, error=False):
    """
        Функция отвечает за принятие количества отелей и id места назначения(города)
        Запрос по отелям производится с платы за 1 день проживания по убыванию цены

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
                url_and_parameters["hotel_count"] = 10
                logger.warning(f"Юзер №{message.chat.id} ввёл число отелей больше чем 10, замена числа на 10")
        elif error:
            hotels_count = "5"
            url_and_parameters["hotel_count"] = 5
        url_and_parameters["hotel_count"] = hotels_count

        buttons = types.InlineKeyboardMarkup()
        button_yes = types.InlineKeyboardButton(text='Да!', callback_data=f'y|{command}|{hotels_count}|{destination}')
        button_no = types.InlineKeyboardButton(text='Нет =(', callback_data=f'n|{command}|{hotels_count}|{destination}')
        buttons.add(button_yes, button_no)
        return buttons
    except ValueError:
        logger.warning(f"Юзер №{message.chat.id} ввел не цифровое значение, будет использовано стандартное значение = 5")
        return False


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

    parameters = url_and_parameters["parameters_city"]
    parameters["query"] = city
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
        url = url_and_parameters["url_hotel"]
        response = requests.request("GET", url,
                                    headers=headers,
                                    params=parameters,
                                    timeout=15)
        find_hotel = []
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
            find_hotel.append(hotels_info)

        hotel_output = send_message(find_hotel)
        output_message = hotel_output[0]
        hotel_id = hotel_output[1]
        result = {key: None for key, _ in enumerate(output_message)}
        for key in result.keys():
            result[key] = [output_message[key], hotel_id[key], find_hotel[key]]
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


def send_message(hotels: List[dict]) -> tuple:
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
               f"Стоимость проживания: {cost}\n" \
               f"Сайт бронирования\nhttps://ru.hotels.com/ho{hotel['id']}\n"

        hotels_text.append(text)
    return hotels_text, hotel_id
