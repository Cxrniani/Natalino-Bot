import requests
import os
import json
from services.lex_service import sendTextToLex

TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']

def sendMessage(chat_id, text, reply_markup=None):
    print(f"Sending message to chat_id: {chat_id}, text: {text}, reply_markup: {reply_markup}")
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        payload = {
            'chat_id': chat_id,
            'text': text,
            'reply_markup': reply_markup  # Adiciona o teclado inline se fornecido
        }
        
        # Verifica se reply_markup é None antes de fazer o POST
        if reply_markup is None:
            del payload['reply_markup']
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error in sendMessage function: {str(e)}")

def getFileInfo(file_id):
    print(f"Getting file info for file_id: {file_id}")
    try:
        url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/getFile"
        params = {'file_id': file_id}
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()['result']
    except requests.exceptions.RequestException as e:
        print(f"Error in getFileInfo function: {str(e)}")
        raise

def createInlineKeyboardFromResponseCard(response_card):
    """
    Cria um inline keyboard para o reply_markup do Telegram a partir de um ImageResponseCard.
    
    :param response_card: O dicionário do ImageResponseCard contendo os botões.
    :return: JSON representando o inline keyboard.
    """
    buttons = response_card.get('imageResponseCard', {}).get('buttons', [])
    
    # Cria o inline keyboard no formato esperado pela API do Telegram
    inline_keyboard = {
        'inline_keyboard': [
            [{'text': btn['text'], 'callback_data': btn['value']} for btn in buttons]
        ]
    }
    
    return json.dumps(inline_keyboard)

def processCallbackQuery(update):
    try:
        callback_query_id = update['callback_query']['id']
        callback_data = update['callback_query']['data']
        chat_id = update['callback_query']['message']['chat']['id']
        
        # Simule o envio do valor do botão clicado para o Lex
        lex_response = sendTextToLex(callback_data, str(chat_id))
        
        # Responda ao callback query para indicar que foi processado
        url = f'https://api.telegram.org/bot{os.environ["TELEGRAM_TOKEN"]}/answerCallbackQuery'
        payload = {
            'callback_query_id': callback_query_id,
            'text': 'Você escolheu: ' + callback_data
        }
        requests.post(url, json=payload)

        has_image_response_card = any(
            message.get('contentType') == 'ImageResponseCard'
            for message in lex_response.get('messages', [])
        )

        reply_markup = None
        
        if has_image_response_card:
            for message in lex_response.get('messages', []):
                if message.get('contentType') == 'ImageResponseCard':
                    reply_markup = createInlineKeyboardFromResponseCard(message)
                    print(f"Created reply_markup: {reply_markup}")
            
        for message in lex_response.get('messages', []):
            lex_response_text = message.get('content', '')
            # Depuração
            print(f"Processing message: {message}")
            
            # Depuração
            print(f"Sending message: {lex_response_text}")
            
            sendMessage(chat_id, lex_response_text, reply_markup)
            reply_markup = None
        
    except Exception as e:
        print(f"Error in processCallbackQuery function: {str(e)}")