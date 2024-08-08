import sys
import os
import json
import hashlib
import requests
from utils.logger import logger, error

# Adicione o caminho para o diretório 'visao-computacional'
sys.path.append(os.path.abspath('visao-computacional/'))

# Importar classes de serviços S3, Transcribe e Bedrock
from services.s3_service import S3BucketClass
from services.transcribe_service import TranscribeClass
from services.bedrock_service import BedrockService

# Importar utils para o Controller
from utils.increase_lambda_timeout import LambdaClass
from utils.s3_configuration_acess import S3BucketConfiguration
from utils.url_decomposer import url_decomposer, url_decomposer_s3bucket

# Inicialize o serviço S3 e DynamoDB com os nomes dos recursos
SERVICE_NAME = os.environ['BUCKET_NAME']
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']

class BotController:
    def __init__(self):
        """
        Inicializa os serviços necessários, incluindo S3, Transcribe e Bedrock.

        Configura um bucket S3 e define o nome do bucket para futuras operações.
        """ 
        # Inicializa os serviços S3, Transcribe e Bedrock
        self.s3_service = S3BucketClass(SERVICE_NAME)
        self.s3_config = S3BucketClass(SERVICE_NAME)
        self.transcribe_service = TranscribeClass()
        self.bedrock_service = BedrockService()
        
        # Cria um bucket S3
        self.create_s3_bucket()

        # Inicializa configurações para a Lambda e S3
        self.lambda_utils = LambdaClass()
        self.s3_config = S3BucketConfiguration(SERVICE_NAME)

        # Define o nome do bucket S3 para a API
        self.api_bucket = SERVICE_NAME
          
#################### S3 Bucket ####################

    # -+-+-+-+-+ Criação do S3 Bucket -+-+-+-+-+ 
    def create_s3_bucket(self):
        """
        Cria um bucket S3 para armazenar arquivos.

        Inicializa o serviço S3 e cria um bucket com o nome definido.
        """        
        try:  # Criação de um S3 bucket
            self.s3_service.create_s3_bucket()
        except Exception as e:  # Em caso de erro, loga a exceção e retorna
            error(e)
            raise Exception('Creation S3 Bucket: Internal Server Error')

    # -+-+-+-+-+ Criação do Url para o S3 Bucket -+-+-+-+-+ 
    def create_s3bucket_url(self, bucket, key_name): 
        """
        Gera uma URL assinada para um item em um bucket S3.

        Parameters:
            bucket (str): Nome do bucket S3.
            key_name (str): Nome da chave do item no bucket.

        Returns:
            str: URL assinada para o item no bucket S3.
        """       
        url_s3bucket = self.s3_service.get_signed_url(bucket, key_name)
        return url_s3bucket
    
#################### Construtor da Função ####################
    def generate_unique_id(self, url): 
        """
        Gera um ID único para o item com base na URL fornecida, usando o algoritmo MD5.

        Parameters:
            url (str): URL do item.

        Atualiza o atributo `unique_id` com o hash MD5 da URL.
        """       
        self.unique_id = hashlib.md5(url.encode()).hexdigest()

# #################### Transcriber #################### 
    
    # -+-+-+-+-+ Criação do STT usando Transcribe -+-+-+-+-+ 
    def speechToText_transcribe(self, url_link):
        """
        Inicia um trabalho de transcrição para um arquivo de áudio carregado no S3 usando o Amazon Transcribe.

        Parameters:
            bucket_name (str): Nome do bucket S3 onde o arquivo de áudio está armazenado.
            key_name (str): Nome do arquivo de áudio no bucket S3.

        Returns:
            dict: Resposta do serviço de transcrição.
        """
        url_without_format, media_format = url_decomposer(url_link)
        self.generate_unique_id(url_without_format)
        job_name = self.unique_id + '-transcription'

        try:
            # Inicia o job de transcrição
            transcribe_url = self.transcribe_service.start_transcription(
                job_name=job_name,
                job_uri=url_link,
                media_format=media_format,
                output_bucket=self.api_bucket
            )
            
            response = requests.get(transcribe_url)
            transcribe_json = response.json()

            # Concatenar
            sentences = []
            for segment in transcribe_json.get('results', {}).get('transcripts', []):
                sentences.append(segment.get('transcript', ''))

            transcribe_message = ' '.join(sentences)
            return transcribe_message
        
        except Exception as e:  # Em caso de erro, loga a exceção e retorna
            error(e)
            raise Exception(f'Transcribe: Internal Server Error {str(e)}')

 
# #################### Bedrock #################### 
    
    # -+-+-+-+-+ Criação da Função do Bedrock -+-+-+-+-+ 
    def bedrockExecute(self, intent, msg=None):
        """
        Executa um modelo Bedrock com a mensagem fornecida.

        Parameters:
            msg (str): Mensagem a ser processada pelo modelo Bedrock.

        Returns:
            dict: Resposta do modelo Bedrock com o resultado da execução.
        """        
        try:
            self.bedrock_service.set_intent_lex(intent, msg)
            response = self.bedrock_service.invoke_model()

            if response['statusCode'] == 200:
                response_body = json.loads(response['message'])

            return response_body

        except Exception as e:  # Em caso de erro, loga a exceção e retorna
            error(e)
            raise Exception('Bedrock: Internal Server Error')