import requests
from src.py.logic.propParser import get_telegram_config

TELEGRAM_SEND_MESSAGE_URL = 'https://api.telegram.org/bot{}/sendMessage'

def telegram_bot_sendtext(bot_message):
    bot_token, bot_chatID = get_telegram_config('config.properties')

    message_parts = [bot_message[i:i+4096] for i in range(0, len(bot_message), 4096)]
    for part in message_parts:
        params = {
            'chat_id': bot_chatID,
            'parse_mode': 'Markdown',
            'text': part
        }
        response = requests.get(TELEGRAM_SEND_MESSAGE_URL.format(bot_token), params=params)
        if response.status_code != 200:
            print("error break in telegram_bot_sendtext")
            raise ValueError('==========Request return error!==========')

    return response.json()