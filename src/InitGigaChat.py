from gigachat import GigaChat
from src.Constants import GIGACHAT_API_KEY

gigachat = GigaChat(
    credentials=GIGACHAT_API_KEY, verify_ssl_certs=False)