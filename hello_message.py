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


bot.infinity_polling()
