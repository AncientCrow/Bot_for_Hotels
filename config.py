from dotenv import dotenv_values


config = dotenv_values(".env") # if smb want to use this code, add '.env' with your Telegram bot token and api token from hotels.com GL HF
BOT_TOKEN = config['BOT_TOKEN']
API_TOKEN = config['API_TOKEN']
