import io
import os
import sys
import hashlib
import openpyxl
import pandas as pd
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import requests
from utils.logger import logger, error

# Adicione o caminho para o diretório 'visao-computacional'
sys.path.append(os.path.abspath('visao-computacional/'))

# Importar classes de serviços S3 e DynamoDB
from services.s3_service import S3BucketClass
from services.dynamodb_service import DynamoDBClass
from services.rekognition_service import RekognitionService

# Importar utils para o Controller
from utils.increase_lambda_timeout import LambdaClass
from utils.s3_configuration_acess import S3BucketConfiguration
from utils.rekogntion_extract_information import extract_data_from_rekognition_label
from utils.rekogntion_extract_information import extract_text_data_from_rekognition
from utils.url_decomposer import url_decomposer, url_decomposer_s3bucket

# Inicialize o serviço S3 e DynamoDB com os nomes dos recursos
SERVICE_NAME = os.environ['BUCKET_NAME']
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']


class VisionController:
    def __init__(self):
        """
        Inicializa os serviços necessários, incluindo S3, DynamoDB, Rekognition e Transcribe.

        Cria um bucket S3 e uma tabela DynamoDB, e configura o bucket e o nome da chave.
        """ 
        # Inicializa os serviços S3, DynamoDB, Rekognition e Transcribe
        self.s3_service = S3BucketClass(SERVICE_NAME)
        self.dynamodb_service = DynamoDBClass(DYNAMODB_TABLE_NAME)
        self.rekognition_service = RekognitionService()

        # Cria um bucket S3 e uma tabela DynamoDB
        self.create_s3_bucket()
        self.create_dynamodb_table()

        # Inicializa configurações para a Lambda e S3
        self.lambda_utils = LambdaClass()
        self.s3_config = S3BucketConfiguration(SERVICE_NAME)

        
        # Cria uma variável com o nome do Bucket da API
        self.api_bucket = SERVICE_NAME

#################### Construtor da Função ####################
    def decompose_url(self, url): 
        """
        Decompõe uma URL para extrair o link e o formato da chave.

        Parameters:
            url (str): URL completa do item.

        Atualiza os atributos `url_link` e `key_format` com base na URL fornecida.
        """       
        self.url_link, self.key_format = url_decomposer(url)

#################### Construtor da Função ####################
    def decompose_s3bucket_url(self, url): 
        """
        Decompõe uma URL S3 para extrair o nome do bucket, a chave e o formato da chave.

        Parameters:
            url (str): URL completa do item no S3.

        Atualiza os atributos `bucket_name`, `key_name` e `key_format` com base na URL fornecida.
        """       
        self.bucket_name, self.key_name, self.key_format = url_decomposer_s3bucket(url)

#################### Construtor da Função ####################
    def generate_unique_id(self, url): 
        """
        Gera um ID único para o item com base na URL fornecida, usando o algoritmo MD5.

        Parameters:
            url (str): URL do item.

        Atualiza o atributo `unique_id` com o hash MD5 da URL.
        """       
        self.unique_id = hashlib.md5(url.encode()).hexdigest()

#################### S3 Bucket ####################

    # -+-+-+-+-+ Criação do S3 Bucket -+-+-+-+-+ 
    def create_s3_bucket(self):
        """
        Cria um bucket S3 para armazenar arquivos.

        Inicializa o serviço S3 e cria um bucket com o nome definido.
        """        
        try:  # Criação de um bucket S3
            self.s3_service.create_s3_bucket()
        except Exception as e:  # Em caso de erro, loga a exceção e retorna
            error(e)
            raise Exception('S3 Bucket Creation: Internal Server Error')

    # -+-+-+-+-+ Upload de um audio no S3 Bucket -+-+-+-+-+    

    def upload_audio_to_s3(self, url, object_name=None):
        """
        Faz o upload de um arquivo de áudio para o bucket S3 usando a URL fornecida.

        Parameters:
            url (str): URL do áudio a ser carregado.
            object_name (str): Nome do objeto no S3. Se None, o nome da URL é usado.

        Returns:
            dict: Informações sobre o upload, incluindo a URL assinada, o bucket e o nome do objeto.
        """
        if object_name is None:
            object_name = url.split('/')[-1]

        s3_client = boto3.client('s3')
        s3_object = boto3.resource('s3').Object(self.api_bucket, object_name)

        try:
            # Faz o upload do áudio para o bucket S3
            with requests.get(url, stream=True) as r:
                s3_object.put(Body=r.content)
            
            # Obtém a URL assinada do objeto no S3
            url_bucket = f'https://{self.api_bucket}.s3.amazonaws.com/{object_name}'

            response_body = {
                'url': url_bucket, 
                'bucket': self.api_bucket, 
                'objectName': object_name
            }

            return response_body
        
        except NoCredentialsError:
            error_message = "Credenciais não encontradas"
            print(error_message)
            raise Exception(error_message)
        
        except ClientError as e:
            error_message = f"Erro ao fazer upload do áudio: {e}"
            print(error_message)
            raise Exception(error_message)

    # -+-+-+-+-+ Upload de uma imagem no S3 Bucket -+-+-+-+-+  
    def upload_to_s3_bucket(self, url):
        """
        Faz o upload de uma imagem para o bucket S3 usando a URL fornecida.

        Parameters:
            url (str): URL da imagem a ser carregada.

        Returns:
            dict: Informações sobre o upload, incluindo a URL assinada, o bucket e o nome do objeto.
        """ 
        self.decompose_url(url)
        self.generate_unique_id(self.url_link)
        self.object_name = f'{self.unique_id}.{self.key_format}'

        try: # Faz o upload da imagem para o bucket S3
            self.s3_service.upload_image_to_s3(url, self.object_name)
            self.url_bucket = self.s3_service.get_signed_url(self.api_bucket, self.object_name)

            response_body = {
                'url': self.url_bucket, 
                'bucket': self.api_bucket, 
                'imageName': self.object_name
            }

            return response_body
        
        except Exception as e:  # Em caso de erro, loga a exceção e retorna
            error(e)
            raise Exception('S3 Bucket Upload: Internal Server Error')

#################### Rekognition ####################
    # -+-+-+-+-+ Processa a imagem usando Rekognition -+-+-+-+-+ 
    def load_rekogntion(self, url):
        """
        Processa uma imagem carregada no S3 para detectar labels usando o Amazon Rekognition.

        Parameters:
            url (str): URL do item no S3.

        Returns:
            dict: Resposta com a URL da imagem, labels detectados, e outras propriedades da imagem.
        """      
        self.decompose_s3bucket_url(url)
        self.object_name = f'{self.key_name}.{self.key_format}'

        try:
            # Detectando labels na imagem
            response_labels = self.rekognition_service.detect_labels(self.api_bucket, self.object_name)
            rekogntion_labels_out = extract_data_from_rekognition_label(response_labels)
            
            # Obtendo metadados da imagem e URL assinada
            image_url = self.s3_service.get_signed_url(self.api_bucket, self.object_name)
            info_labels = self.filter_rekogntion_labels(rekogntion_labels_out)

            # Monta a resposta com a URL da imagem e os labels detectados
            response_body = {   
                "url": image_url,
                "bucket": self.bucket_name,
                "imageName": self.object_name,
                "label_rekogntion": {
                    "item_name": info_labels['item_name'],
                    "donation_type": info_labels['donation_type'],
                    "donation_value": info_labels['donation_value'],
                    "donation_object": info_labels['Categories'],
                    "conservation_state": info_labels['conservation_state']
                },
                "image_properties": {
                    "BoundingBox": info_labels['BoundingBox'],
                    "DominantColors": info_labels['colors']
                }
            }
            return response_body
        
        except Exception as e:  # Em caso de erro, loga a exceção e retorna
            error(e)
            raise Exception('Rekogntion: Internal Server Error')

    def filter_rekogntion_labels(self, rekogntion_labels):
        """
        Filtra e atualiza os labels detectados com informações adicionais, se necessário.

        Parameters:
            rekogntion_labels (dict): Labels detectados pela função Rekognition.

        Returns:
            dict: Labels atualizados com informações adicionais, se necessário.
        """
        # Detectando textos na imagem
        if 'Page' in rekogntion_labels['item_name'] or 'Text and Documents' in rekogntion_labels['Categories']:
            response_text = self.rekognition_service.detect_text(self.api_bucket, self.object_name)
            info_text = extract_text_data_from_rekognition(response_text)
            rekogntion_labels['donation_type'] = info_text['donation_type']
            rekogntion_labels['donation_value'] = info_text['donation_value']

        # Atualiza o estado de conservação se detectado
        if 'Damage Detection' in rekogntion_labels['Categories']:
            rekogntion_labels['conservation_state'] = 'bad state'
        
        # Define as categorias a serem filtradas
        filter_labels = ['Hobbies and Interests', 'Text and Documents', 'Food and Beverage', 'Events and Attractions']

        # Verifica se nenhuma das categorias desejadas está presente em 'Categories'
        if not any(label in rekogntion_labels['Categories'] for label in filter_labels):
            # Limpa ou define como vazios os campos relevantes se nenhuma categoria desejada for encontrada
            rekogntion_labels['item_name'] = []
            rekogntion_labels['donation_type'] = None
            rekogntion_labels['Categories'] = []
            rekogntion_labels['conservation_state'] = None
            rekogntion_labels['donation_value'] = None

        return rekogntion_labels

#################### DynamoDB ####################

    # -+-+-+-+-+ Criação do DynamoDB Table -+-+-+-+-+ 
    def create_dynamodb_table(self):
        """
        Cria uma tabela DynamoDB para registrar logs de doações.

        Inicializa o serviço DynamoDB e cria uma tabela para armazenar logs.
        """  
        try: # Criação de uma tabela DynamoDB
            self.dynamodb_service.create_table_dynamodb()
        
        except Exception as e:  # Em caso de erro, loga a exceção e retorna
            error(e)
            raise Exception('DynamoDB: Internal Server Error')
    
    # -+-+-+-+-+ Criação do Log do DynamoDB -+-+-+-+-+ 
    def generateLog(self, rekognition_item, url):
        """
        Registra um log no DynamoDB com informações da doação e gera um ID único para o item.

        Parameters:
            rekognition_item (dict): Informações da doação detectadas pelo Rekognition.
            url (str): URL do item no S3.

        Returns:
            DataFrame: Dados exportados para um arquivo Excel.
        """    
        self.decompose_s3bucket_url(url)

        try: # Log em uma tabela DynamoDB            
            # Prepara o corpo da resposta para o DynamoDB
            response_body = {
                'unique_id': self.key_name, 
                's3_url': url, 
                'donation_type': rekognition_item['donation_type'], 
                'donation_object': rekognition_item['donation_object'],
                'conservation_state': rekognition_item['conservation_state'],
                'donation_value': rekognition_item['donation_value']
            }
            # Se o 'donation_type' for None, retorna uma mensagem de operação inválida
            if rekognition_item['donation_type'] is None:
                return 'Operação inválida!! Tente refazer novamente a operação'
            
            # Registra o log no DynamoDB
            self.dynamodb_service.log_register_dynamodb(**response_body)
            
            # Exporta os dados para um arquivo Excel e faz o upload para o S3
            self.export_to_excel(filename='inventory.xlsx')

            return 'Operação realizada com sucesso !!'

        except Exception as e:  # Em caso de erro, loga a exceção e retorna
            error(e)
            raise Exception('DynamoDB: Internal Server Error')

    # -+-+-+-+-+ Criação de Arquivo CSV -+-+-+-+-+ 
    def export_to_excel(self, filename='inventory.xlsx'):
        """
        Exporta todos os dados da tabela DynamoDB para um arquivo Excel.

        Parameters:
            filename (str): Nome do arquivo Excel a ser salvo.

        Returns:
            DataFrame: DataFrame com os dados exportados da tabela DynamoDB.
        """

        # Importa dados da tabela DynamoDB
        dynamo_data = self.dynamodb_service.import_table_dynamodb()
        
        if dynamo_data is None:
            print("Erro ao obter itens da tabela DynamoDB.")
            return None

        # Cria um DataFrame do Pandas a partir dos itens
        dataframe = pd.DataFrame(dynamo_data)
        
        # Salva o DataFrame em um objeto BytesIO
        with io.BytesIO() as excel_buffer:
            dataframe.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)  # Retorna o ponteiro para o início do buffer

            # Faz o upload para o S3
            self.s3_service.upload_s3_bucket(excel_buffer, filename)