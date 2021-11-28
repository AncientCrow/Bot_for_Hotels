import requests
import json
import os
import re

from datetime import datetime, timedelta
from telebot.types import InputMediaPhoto


api_token = os.getenv("API_TOKEN")
headers = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': api_token
}


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
            city_name = " ". join(re.findall(r"[а-яА-Я]\w*", city_name))
            cities.append([city_name, entity["destinationId"]])
    return cities


def check_hotels(hotels_count: str, destination: str) -> tuple or bool:
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
        check_in = datetime.today().strftime('%Y-%m-%d')
        check_out = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        parameters = {"destinationId": destination, "pageNumber": "1", "pageSize": hotels_count,
                      "checkIn": check_in,
                      "checkOut": check_out, "adults1": "1", "sortOrder": "PRICE", "locale": "ru_RU",
                      "currency": "RUB"}
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
            find_hotels.append(hotels_info)

        hotel_output = send_message(find_hotels)
        output_message = hotel_output[0]
        hotel_id = hotel_output[1]
        return output_message, hotel_id, find_hotels
    except TimeoutError:
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
    headers_photo = {
        'x-rapidapi-host': "hotels4.p.rapidapi.com",
        'x-rapidapi-key': api_token
    }
    response = requests.request("GET", url, headers=headers_photo, params=parameters)
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
        text = f"{name}\nРейтинг: {rating}\n" \
               f"Адрес: {place}\nСтоимость дня: {cost}\n"
        hotels_text.append(text)
    return hotels_text, hotel_id
