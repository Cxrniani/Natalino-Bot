import boto3
import os
import json

# Usando o cliente do Lex V2
lex_client = boto3.client('lexv2-runtime')

def sendTextToLex(text, user_id):
    print(f"Sending text to Lex: {text}, user_id: {user_id}")
    try:
        response = lex_client.recognize_text(
            botId=os.environ['LEX_BOT_ID'],  # Bot ID no Lex V2
            botAliasId=os.environ['LEX_BOT_ALIAS_ID'],  # Bot Alias ID no Lex V2
            localeId='pt_BR',  # Linguagem do bot
            sessionId=user_id,
            text=text
        )
        print(f"Lex response: {json.dumps(response)}")
        return response
    except Exception as e:
        print(f"Error in sendTextToLex function: {str(e)}")
        return {"messages": [{"contentType": "PlainText", "content": "Desculpe, ocorreu um erro ao processar sua solicitação."}]}