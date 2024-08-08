import boto3
import logging
import requests
from botocore.exceptions import ClientError, NoCredentialsError

class S3BucketClass: 
    def __init__(self, bucket_name):
        """
        Inicializa a classe S3BucketClass com o nome do bucket e o cliente S3.
        
        :param bucket_name: Nome do bucket S3
        """
        # Cria uma variável global bucket_name
        self.bucket_name = bucket_name

        # Inicia o serviço S3 Bucket
        self.s3_client = boto3.client('s3')
         
    def create_s3_bucket(self):
        """
        Cria um bucket S3 com o nome especificado.

        :return: True se o bucket for criado com sucesso, caso contrário False
        """
        try:
            # Verifica se o bucket já existe, caso não exista, cria o bucket
            if self._bucket_exists(self.bucket_name):
                print(f"Bucket {self.bucket_name} já existe.")
                return True
            self.s3_client.create_bucket(Bucket=self.bucket_name)
            
        except ClientError as e:
            # Caso ocorra um erro, imprime a mensagem de erro
            logging.error(f"Erro ao criar o bucket: {e}")
            return False
        return True

    def _bucket_exists(self, bucket_name):
        """
        Verifica se o bucket já existe no S3.

        :param bucket_name: Nome do bucket
        :return: True se o bucket existir, caso contrário False
        """
        try:
            # Verifica se o bucket já existe no S3
            self.s3_client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            # Caso não exista, retorna False
            return False 
        
    def list_s3_bucket(self):
        """
        Lista os nomes dos buckets S3 existentes.

        :return: True se a operação for bem sucedida, caso contrário False
        """
        try:
            # Recupera a lista de buckets existentes
            response = self.s3_client.list_buckets()
            
            # Exibe os nomes dos buckets
            print("S3 Buckets:", [bucket['Name'] for bucket in response['Buckets']])

        except ClientError as e:
            # Caso ocorra um erro, imprime a mensagem de erro
            print(f"Error listing S3 buckets: {e}")
            return False
        return True
    
    def upload_s3_bucket(self, upload_file, file_name):
        """
        Faz o upload de um arquivo para o bucket S3.

        :param upload_file: Caminho do arquivo a ser enviado
        :param file_name: Nome do arquivo no bucket S3
        :return: URL do arquivo no S3 se o upload for bem sucedido, caso contrário None
        """
        try:
            # Faz o upload do arquivo no S3
            self.s3_client.upload_fileobj(upload_file, self.bucket_name, file_name)
            file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{file_name}"
            return file_url
        
        except ClientError as e:
            # Caso ocorra um erro, imprime a mensagem de erro
            logging.error(f"Erro ao fazer upload do arquivo: {e}")
            return None    
    
    def upload_image_to_s3(self, url_key, object_name=None):
        """
        Faz o upload de uma imagem para o bucket no S3.

        :param url_key: URL da imagem a ser enviada
        :param object_name: Nome do objeto no S3. Se None, o nome da URL é usado
        :return: True se o upload foi bem sucedido, False caso contrário
        """
        if object_name is None:
            object_name = url_key

        s3_object = boto3.resource('s3').Object(self.bucket_name, object_name)
    
        try:
            # Verifica se a imagem está presente no bucket
            with requests.get(url_key, stream=True) as r:
                s3_object.put(Body=r.content)
            print(f"O arquivo {object_name} já existe no bucket {self.bucket_name}")
            return False
    
        except ClientError as e:
            # Se não existir, a exceção é lançada e o código continua
            error_code = e.response['Error']['Code']
    
            if error_code == '404':
                # Objeto não existe no bucket, então faz o upload
                try: 
                    with requests.get(url_key, stream=True) as r:
                        s3_object.put(Body=r.content)
                    print(f"Arquivo {object_name} enviado com sucesso para o bucket {self.bucket_name}")
                    return True    
                except NoCredentialsError:
                    # Credenciais não encontradas
                    print("Credenciais não encontradas")
                    return False
            else:
                # Outros erros
                print(f"Erro ao tentar o objeto {object_name} no bucket {self.bucket_name}: {error_code}")
                return False        
       
    def get_image_metadata(self, bucket_name, key_name):
        """
        Obtém os metadados de uma imagem no S3.

        :param bucket_name: Nome do bucket S3
        :param key_name: Nome da chave do objeto no S3
        :return: Objeto de metadados
        """
        try:
            metadata = self.s3_client.head_object(Bucket=bucket_name, Key=key_name)
            return metadata
        except ClientError as e:
            # Caso ocorra um erro, imprime a mensagem de erro
            logging.error(f"Erro ao obter metadados da imagem: {e}")
            return None
        
    def get_signed_url(self, bucket_name, key_name):
        """
        Gera uma URL pública para acessar a imagem no S3.

        :param bucket_name: Nome do bucket S3
        :param key_name: Nome da chave do objeto no S3
        :return: URL pública da imagem
        """
        url = f'https://{bucket_name}.s3.amazonaws.com/{key_name}'
        return url
