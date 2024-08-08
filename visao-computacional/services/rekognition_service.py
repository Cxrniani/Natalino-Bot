import boto3
from botocore.exceptions import BotoCoreError, ClientError

class RekognitionService:
    def __init__(self):
        """
        Inicializa a classe RekognitionService e cria o cliente boto3 para o Amazon Rekognition.
        """
        self.rekognition = boto3.client('rekognition')
   
    def detect_labels(self, bucket, image_name):
        """
        Detecta rótulos em uma imagem armazenada em um bucket do S3.

        :param bucket: Nome do bucket do S3 onde a imagem está armazenada.
        :param image_name: Nome do arquivo de imagem no bucket do S3.
        :return: Resposta da API detect_labels do Amazon Rekognition.
        """
        try:
            # Chama a API detect_labels do Amazon Rekognition
            response = self.rekognition.detect_labels(
                Image={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': image_name
                    }
                },
                MaxLabels=10,
                MinConfidence=80,
                Features=["GENERAL_LABELS", "IMAGE_PROPERTIES"],
                Settings={"ImageProperties": {"MaxDominantColors": 10}}
            )
            return response
        
        except BotoCoreError as e:
            # Em caso de erro, imprime a mensagem de erro e retorna None
            print(f"Erro ao detectar rótulos: {e}")
            return None

    def detect_text(self, bucket, image_name):
        """
        Detecta texto em uma imagem armazenada em um bucket do S3.

        :param bucket: Nome do bucket do S3 onde a imagem está armazenada.
        :param image_name: Nome do arquivo de imagem no bucket do S3.
        :return: Lista de detecções de texto na imagem.
        """
        try:
            # Chama a API detect_text do Amazon Rekognition
            response = self.rekognition.detect_text(
                Image={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': image_name
                    }
                }
            )

            # Obtém as detecções de texto da resposta
            textDetections = response['TextDetections']
            return textDetections
        
        except BotoCoreError as e:
            # Em caso de erro, imprime a mensagem de erro e retorna None
            print(f"Erro ao detectar texto: {e}")
            return None
