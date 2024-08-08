import boto3
import json
import datetime
from botocore.exceptions import ClientError

class Logger:
    def __init__(self):
        self.logs = boto3.client('logs')

    # Função para garantir que um grupo de logs exista no CloudWatch
    def ensure_log_group(self, log_group_name):
        try:
            self.logs.create_log_group(logGroupName=log_group_name)
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                print(f"Unexpected error: {e}")

    # Função para garantir que um fluxo de logs exista no CloudWatch
    def ensure_log_stream(self, log_group_name, log_stream_name):
        try:
            self.logs.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                print(f"Unexpected error: {e}")

    # Função para gerar logs de mensagens no CloudWatch em um grupo e fluxo de logs específicos
    def log_message(self, log_group_name, log_stream_name, message):
        self.ensure_log_group(log_group_name) # Garante que o grupo de logs exista
        self.ensure_log_stream(log_group_name, log_stream_name) # Garante que o fluxo de logs exista
        try:
            response = self.logs.describe_log_streams(
                logGroupName=log_group_name,
                logStreamNamePrefix=log_stream_name
            )

            sequence_token = None
            if 'logStreams' in response and len(response['logStreams']) > 0:
                sequence_token = response['logStreams'][0].get('uploadSequenceToken', None)

            log_event = { # Cria um evento de log com a mensagem e o timestamp atual
                'logGroupName': log_group_name,
                'logStreamName': log_stream_name,
                'logEvents': [
                    {
                        'timestamp': int(datetime.datetime.now().timestamp() * 1000),
                        'message': json.dumps(message)
                    }
                ]
            }

            if sequence_token:
                log_event['sequenceToken'] = sequence_token

            self.logs.put_log_events(**log_event)
        except ClientError as e:
            print(f"Failed to put log events: {e}")

# Instância global do logger para ser utilizada em todo o projeto
logger_instance = Logger()

def logger(message):  # Função para gerar logs com mensagens de informação no CloudWatch em caso de sucesso na requisição.
    print(message)
    logger_instance.log_message('rekognition-logs', 'vision-logs', message)

def error(message):  # Função para gerar logs de mensagens de erro no CloudWatch
    print(message)
    logger_instance.log_message('rekognition-logs', 'vision-errors', message)