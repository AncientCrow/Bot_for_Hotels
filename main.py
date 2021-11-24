import telebot

token = "2122656203:AAH3LlK6cFl_HebqmQYBUqT9Cxrc8-71GJw"
bot = telebot.TeleBot(token, parse_mode=None)


@bot.message_handler(commands=["hello-world", "hello_world", "start"])
@bot.message_handler(func=lambda msg: msg.text.lower() == "привет")
def welcome_message(message: telebot.types.Message):
    """
    Приветственная функция. Реагирует на команду /hello-world или
    на сообщение состоящее из слова 'привет'

    Parameters:
    -------------
        message : telebot.types.Message
            Сообщение отправленное от пользователя, боту.
            Является классом библиотеки telebot
    """

    output_message = "Добро подаловать, я бот который поможет найти отель по тем или иным условиям.\n" \
                     "Используйте /help, чтобы узнать, что я умею"

    bot.reply_to(message, output_message)


@bot.message_handler(commands="help")
def help_message(message: telebot.types.Message):
    """
    Функция, передаёт информацию о возможных командах бота

    Parameters:
    -------------
        message : telebot.types.Message
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
def low_price(message: telebot.types.Message):
    """
    Функция отвечает за вывод информации об отелях по минимальной стоимости проживания.

    Функция запрашивает у пользователя город поиска и количество выводимых отелей,
    дополнительно будет запрашиваться разрешение на вывод изображений отеля

    Parameters:
    -------------
        message : telebot.types.Message
            Сообщение отправленное от пользователя, боту.
            Является классом библиотеки telebot
    """

    bot.reply_to(message, "Функция в разработке")


@bot.message_handler(commands="highprice")
def high_price(message: telebot.types.Message):
    """
    Функция отвечает за вывод информации об отелях по максимальной стоимости проживания.

    Функция запрашивает у пользователя город поиска и количество выводимых отелей,
    дополнительно будет запрашиваться разрешение на вывод изображений отеля.

    Parameters:
    -------------
        message : telebot.types.Message
            Сообщение отправленное от пользователя, боту.
            Является классом библиотеки telebot
    """

    bot.reply_to(message, "Функция в разработке")


@bot.message_handler(commands="bestdeal")
def best_deal(message: telebot.types.Message):
    """
        Функция отвечает за вывод информации об отелях по заданным параметрам.

        Функция запрашивает у пользователя город поиска, ценовой диапозон,
        диапозон расстояния от центра города, дополнительно будет
        запрашиваться вывод разрешение на вывод изображений отелей.

        Parameters:
        -------------
        message : telebot.types.Message
            Сообщение отправленное от пользователя, боту.
            Является классом библиотеки telebot
    """

    bot.reply_to(message, "Функция в разработке")


@bot.message_handler(commands="history")
def history(message: telebot.types.Message):
    """
    Функция отвечает за вывод пользователю истории его запросов
    с укзаанием времени запроса и отелей, которые были найдены

    Parameters:
    -------------
        message : telebot.types.Message
            Сообщение отправленное от пользователя, боту.
            Является классом библиотеки telebot
    """

    bot.reply_to(message, "Функция в разработке")


@bot.message_handler(func=lambda m: True)
def not_command_message(message: telebot.types.Message):
    """Функция отвечает за распознавание сообщений, не относящихся к командам"""
    bot.reply_to(message, "Мне не удается понять, что от меня требуется, используйте"
                          " команду /help для получения справки по моим возможностям")


if __name__ == "__main__":
    bot.infinity_polling()
