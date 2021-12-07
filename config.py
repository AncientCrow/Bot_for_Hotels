from dotenv import dotenv_values


config = dotenv_values(".env")
BOT_TOKEN = config['BOT_TOKEN']
API_TOKEN = config['API_TOKEN']
