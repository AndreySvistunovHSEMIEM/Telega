from dotenv import load_dotenv
import os

load_dotenv()

API_TOKEN = os.getenv('API_TOKEN')
GIGACHAT_API_KEY = os.getenv('GIGACHAT_API_KEY')
WELCOME_TEXT = os.getenv('WELCOME_TEXT', "Добро пожаловать в наш реабилитационный бот!")
CONTENT = os.getenv('CONTENT')