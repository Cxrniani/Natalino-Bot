import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError

def upload_image_to_s3(image_name, bucket_name, object_name=None):

    """
    Faz o upload de uma imagem para o bucket no S3

    image_name: imagem a ser enviada
    object_name: nome do objeto no S3. Se none, image é usado
    bucket_name: bucket para onde a imagem será enviada
    return: True se o upload foi bem sucedido, False caso contrário
    """

    if object_name is None:
        object_name = image_name

    s3_client = boto3.client('s3')

    try:
        # Verifica se a imagem está presente no bucket
        s3_client.head_object(Bucket=bucket_name, Key=object_name)
        print(f"O arquivo {object_name} já existe no bucket {bucket_name}")
        return False

    except ClientError as e:
        # Se não existir, a exceção é lançada e o código continua
        error_code = e.response['Error']['Code']

        if error_code == '404':
            # objeto não existe no bucket então faz o upload
            try: 
                s3_client.upload_file(image_name, bucket_name, object_name)
                print(f"Arquivo {object_name} enviado com sucesso para o bucket {bucket_name}")
                return True    
            except NoCredentialsError:
                print("Credenciais não encontradas")
                return False
        else:
            # Outros erros
            print(f"Erro ao tentar o objeto {object_name} no bucket {bucket_name}: {error_code}")
            return False
        

def upload_directory_to_s3(directory, bucket_name):
    """
    Faz o upload de todos os arquivos de um diretório para um bucket no S3.

    directory: diretório local contendo os arquivos a serem enviados
    bucket_name: bucket para onde os arquivos serão enviados
    return: True se todos os uploads foram bem sucedidos, False caso contrário
    """

    try:
        success = True
        for root, dirs, files in os.walk(directory):
            for file in files:
                local_path = os.path.join(root, file)
                s3_key = os.path.relpath(local_path, directory).replace("\\", "/")

                if not upload_image_to_s3(local_path, bucket_name, s3_key):
                    success = False
        
        return success

    except Exception as e:
        print(f"Erro ao tentar fazer upload dos arquivos para o bucket {bucket_name}: {str(e)}")
        return False
    
# Exemplo de uso:
if __name__ == "__main__":
    # Exemplo para fazer upload de todos os arquivos de um diretório
    directory_to_upload = '../images/'
    bucket_name = 'rafashrek'

    upload_directory_to_s3(directory_to_upload, bucket_name)