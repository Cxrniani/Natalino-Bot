import json
import urllib.parse
import os
from services.telegram_service import getFileInfo, sendMessage, createInlineKeyboardFromResponseCard, processCallbackQuery
from services.lex_service import sendTextToLex
from controller.VisionController import VisionController
from controller.BotController import BotController

#################### Handler do Health ####################

def healthMyApp(event, context): 
    """Verifica a saúde da aplicação."""
    body = {
        "message": "Go Serverless v3.0! Your function executed successfully!",
        "input": event,
    }

    response = {"statusCode": 200, "body": json.dumps(body)} # Retorna a resposta com o código 200 e a mensagem de sucesso
    return response

#################### Handler do Transcribe ####################

def convertSpeechToText(event, context):
    """Testa as funções do controller e retorna os detalhes."""
        
    # bucket = event['Records'][0]['s3']['bucket']['name']
    # key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    body = json.loads(event['body'])
    url_link = body.get('url')

    try: 
        BotControllerClass = BotController()
        response = BotControllerClass.speechToText_transcribe(url_link)
        
        return {
                'statusCode': 200,
                'body': json.dumps({'message': response}, indent=4, sort_keys=True, default=str)
            }
    except Exception as e: 
        error_message = f'Cannot run Transcribe!! Internal Server Error: {str(e)}'
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': error_message})
        }
    
#################### Handler do Bedrock ####################

def messageBedrock(event, context):
    """Testa as funções do controller e retorna os detalhes."""
        
    body = json.loads(event['body'])
    intent = body.get('intent')
    message = body.get('message')
    
    try: 
        BotControllerClass = BotController()
        response = BotControllerClass.bedrockExecute(intent, message)
        return {
                'statusCode': 200,
                'body': json.dumps({'message': response})
            }
    except Exception as e: 
        error_message = f'Cannot load Bedrock!! Internal Server Error: {str(e)}'
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': error_message})
        }

#################### Handler do Upload na S3 Bucket ####################

def lambdaBackend(event, context):
    print("lambdaBackend event received:", json.dumps(event))
    try: 
        body = json.loads(event['body'])
        url_link = body.get('url')
        print(f"URL link: {url_link}")

        response_s3bucket = uploadS3Bucket(event, context)
        print(f"S3 bucket response: {response_s3bucket}")

        response_rekogntion = loadRekogntion(response_s3bucket, context)
        print(f"Rekognition response: {response_rekogntion}")

        response = generateLogDynamo(response_rekogntion, context)
        print(f"DynamoDB log response: {response}")

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    
    except Exception as e: 
        error_message = f'Internal Server Error: {str(e)}'
        print(f"Error in lambdaBackend function: {error_message}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': error_message})
        }


#################### Handler do Upload na S3 Bucket ####################

def uploadS3Bucket(event, context):
    """Testa as funções do controller e retorna os detalhes."""
    
    body = json.loads(event['body'])
    url_link = body.get('url')
    
    try: 
        ControllerVisionClass = VisionController()      
        response = ControllerVisionClass.upload_to_s3_bucket(url_link)
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    
    except Exception as e: 
        error_message = f'Cannot upload image to S3!! Internal Server Error: {str(e)}'
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': error_message})
        } 

#################### Handler do Upload na S3 Bucket ####################

def loadRekogntion(event, context):
    """Testa as funções do controller e retorna os detalhes."""
    
    # Verifica se 'bucket' e 'imageName' estão presentes no evento
    if ('bucket' in event) and ('imageName' in event):
        body = {
            'bucket': event['bucket'],
            'imageName': event['imageName']
        }
        event['body'] = json.dumps(body)
     
    if 'body' not in event:  # Valida se há um body na requisição
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing body in request'})
        }
    
    body = json.loads(event['body'])
    url_link = body.get('url')
    try:
        ControllerVisionClass = VisionController()
        response = ControllerVisionClass.load_rekogntion(url_link)

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    
    except Exception as e: 
        error_message = f'Cannot load rekogntion !! Internal Server Error: {str(e)}'
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': error_message})
    }

#################### Handler do Upload de AUDIO na S3 Bucket ####################

def uploadAudioS3Bucket(event, context):
    """Testa as funções do controller e retorna os detalhes."""
    
    body = json.loads(event['body'])
    url_link = body.get('url')
    
    try: 
        ControllerVisionClass = VisionController()      
        response = ControllerVisionClass.upload_audio_to_s3(url_link)
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    
    except Exception as e: 
        error_message = f'Cannot upload audio to S3!! Internal Server Error: {str(e)}'
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': error_message})
        } 

#################### Handler do Log do DynamoDB ####################

def generateLogDynamo(event, context):
    """Testa as funções do controller e retorna os detalhes."""

    if 'body' not in event:  # Valida se há um body na requisição
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Missing body in request'})
    }

    body = json.loads(event['body'])
    rekognition_item = body.get('label_rekogntion')
    url = body.get('url')
    
    try:
        ControllerVisionClass = VisionController()
        response = ControllerVisionClass.generateLog(rekognition_item, url)

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    
    except Exception as e: 
        error_message = f'Cannot register in Log Dynamo !! Internal Server Error: {str(e)}'
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({'message': error_message})
    }

#################### Handler do Webhook (Integração Chatbot Lex com Telegram) ####################

def webhook(event, context):
    print("Webhook event received:", json.dumps(event))
    try:
        # Verifique se 'body' está presente no evento
        if 'body' not in event:
            raise ValueError("Event does not contain 'body'")

        body = json.loads(event['body'])
        print("Parsed body:", json.dumps(body))

        if 'message' in body:
            chat_id = body['message']['chat']['id']
            user_id = str(body['message']['from']['id'])
            print(f"Received message from chat_id: {chat_id}, user_id: {user_id}")

            if 'photo' in body['message']:
                reply_markup = None
                file_id = body['message']['photo'][-1]['file_id']
                print(f"Received photo with file_id: {file_id}")

                file_info = getFileInfo(file_id)
                print(f"File info: {file_info}")
                
                if 'file_path' not in file_info:
                    raise ValueError("File info does not contain 'file_path'")

                file_path = file_info['file_path']
                file_url = f"https://api.telegram.org/file/bot{os.environ['TELEGRAM_TOKEN']}/{file_path}"
                print(f"File URL: {file_url}")

                backend_event = {
                    "body": json.dumps({"url": file_url})
                }
                response = lambdaBackend(backend_event, context)
                print(f"Lambda backend response: {response}")

                santa_emoji = '\xF0\x9F\x8E\x85'
                christmas_tree_emoji = '\xF0\x9F\x8E\x84'

                message_content = f'Obrigado! Sua foto foi recebida com sucesso e sua doação está registrada no nosso sistema como "pendente"!\nEncaminhe-se até um dos postos de doação, disponíveis no instagram oficial da ação: @natal_dos_pequenos, para finalizar sua doação.\nOu entre em contato conosco através do instagram para agendar um horário para que um de nossos voluntários possa buscar sua doação!\nSe quiser realizar mais alguma doação, digite "realizar doação", ou para mais informações, digite "saber mais".\n\nAgradeçemos novamente pela ajuda, e também por fazer o natal de uma criança mais feliz!\nBoas Festas!! Ho Ho Ho!'
                sendMessage(chat_id, message_content)
                print(f"Sent message: {message_content}")
            
            elif 'voice' in body['message']:
                reply_markup = None
                
                # Extrai o id do arquivo de áudio enviado
                file_id = body['message']['voice']['file_id']
                print(f"Received voice message with file_id: {file_id}")

                file_info = getFileInfo(file_id)
                print(f"File info: {file_info}")
                
                if 'file_path' not in file_info:
                    raise ValueError("File info does not contain 'file_path'")

                # Extrai o URL do áudio enviado
                file_path = file_info['file_path']
                file_url = f"https://api.telegram.org/file/bot{os.environ['TELEGRAM_TOKEN']}/{file_path}"
                print(f"File URL: {file_url}")

                backend_event = {
                    "body": json.dumps({"url": file_url})
                }

                url_s3 = uploadAudioS3Bucket(backend_event, context)

                # Envia o áudio transcrito para o bedrock
                response = convertSpeechToText(url_s3, context)
                response_body = json.loads(response['body'])
                print(f"ConvertSpeechToText response: {response_body}")

                # Checa se 'message' contém o texto transcrito
                transcribed_text = response_body.get('message', 'Texto não disponível.')
                
                # Bedrock retorna "realizar doação" ou "saber mais"
                bedrock_response = messageBedrock({
                    'body': json.dumps({'intent': 'voice', 'message': transcribed_text})
                    }, None)
                bedrock_response_body = json.loads(bedrock_response['body'])
                bedrock_response_text = bedrock_response_body['message']
                print(f"Bedrock response: {bedrock_response_text}")
                
                # Resposta do bedrock é enviada para o Lex
                lex_response = sendTextToLex(bedrock_response_text, user_id)
                print(f"Lex response: {json.dumps(lex_response)}")

                # Lex envia a mensagem para o usuário
                for message in lex_response.get('messages', []):
                    if message.get('contentType') == 'PlainText':
                        message_content = message.get('content', '')
                    elif message.get('contentType') == 'ImageResponseCard':
                        reply_markup = createInlineKeyboardFromResponseCard(message)

                sendMessage(chat_id, message_content, reply_markup)
                print(f"Sent message: {message_content} with reply_markup: {reply_markup}")


            elif 'text' in body['message']:
                text = body['message']['text']
                print(f"Received text: {text}")

                lex_response = sendTextToLex(text, user_id)
                print(f"Lex response: {json.dumps(lex_response)}")

                message_content = ""
                reply_markup = None
                fallback_detected = False  # Adicione esta linha

                # Verificar se a intent é a fallback intent
                if 'fallback' in lex_response.get('sessionState', {}).get('intent', {}).get('name', '').lower():
                    fallback_detected = True

                if fallback_detected:
                    # Se a fallback intent foi detectada, chamar a função do Bedrock
                    bedrock_response = messageBedrock({
                        'body': json.dumps({'intent': 'fallback', 'message': text})
                    }, None)
                    bedrock_response_body = json.loads(bedrock_response['body'])
                    sendMessage(chat_id, bedrock_response_body.get('message'), None)
                    print(f"Sent Bedrock response: {bedrock_response_body.get('message')}")
                else:
                    # Enviar resposta do Lex se não for fallback
                    for message in lex_response.get('messages', []):
                        if message.get('contentType') == 'PlainText':
                            message_content = message.get('content', '')
                        elif message.get('contentType') == 'ImageResponseCard':
                            reply_markup = createInlineKeyboardFromResponseCard(message)

                    sendMessage(chat_id, message_content, reply_markup)
                    print(f"Sent message: {message_content} with reply_markup: {reply_markup}")

        elif 'callback_query' in body:
            print("Received callback query")
            processCallbackQuery(body)

        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'ok'})
        }
    except Exception as e:
        print(f"Error in webhook function: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }


    ##################################################################################################

    # # Verifica se 'bucket' e 'imageName' estão presentes no evento
    # if ('bucket' in event) and ('imageName' in event):
    #     body = {
    #         'bucket': event['bucket'],
    #         'imageName': event['imageName']
    #     }
    #     event['body'] = json.dumps(body)
        
    # if 'body' not in event:  # Valida se há um body na requisição
    #     return {
    #         'statusCode': 400,
    #         'body': json.dumps({'message': 'Missing body in request'})
    #     }
    