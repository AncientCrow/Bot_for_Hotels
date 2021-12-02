import datetime
import json
import os
import requests
import telebot

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


def find_photo(message: types.Message or int, hotels: dict, error=False):
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
        chat_id = message.chat.id
        hotels_id = []
        photos = []
        for index in hotels.keys():
            querystring = {"id": {hotels[index][1]}}
            hotel = hotels[index][0]
            photos.append(hotels_photo(querystring, hotel, photo_count))
        send_photos(chat_id, photos)
    except ValueError:
        text = bot.send_message(message.chat.id, "Указано не число, будет выведено базовое значение фотографий")
        time = datetime.datetime.today().strftime('%Y-%m-%d-%H-%M')
        logger.debug(f"{time}: User input data is not number(photos)")
        find_photo(text, hotels, error=True)


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


def send_photos(chat_id: str, photo_send: list[list]):
    for elements in photo_send:
        media = elements
        bot.send_media_group(chat_id, media)

