import json
import requests

from config import API_TOKEN
from urls_and_param import urls
from telebot.types import InputMediaPhoto

url_and_parameters = urls

headers = {
    'x-rapidapi-host': "hotels4.p.rapidapi.com",
    'x-rapidapi-key': API_TOKEN
}


def find_photo(hotels: dict, photo_count):
    """
    Функция отвечает за создание сообщения для пользователя с выводом фотографий

    Parameters:
    --------------
        message : types.Message
            сообщение с количеством фотографий на вывод
    """

    photos = []
    for index in hotels.keys():
        querystring = {"id": {hotels[index][1]}}
        hotel = hotels[index][0]
        photos.append(hotels_photo(querystring, hotel, photo_count))
    return photos


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

    url = url_and_parameters["url_photo"]
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
