import boto3
import time
import json

class TranscribeClass:
    def __init__(self):
        """
        Inicializa a classe TranscribeClass com o cliente do Amazon Transcribe.
        """
        # Inicializa o cliente do Amazon Transcribe
        self.transcribe_client = boto3.client('transcribe')

    def start_transcription(self, job_name, job_uri, media_format, language_code='pt-BR', output_bucket=None):
        """
        Inicia um trabalho de transcrição de áudio usando o Amazon Transcribe.
        
        Parâmetros:
        - job_name: Nome do trabalho de transcrição.
        - job_uri: URI do arquivo de mídia a ser transcrito.
        - media_format: Formato do arquivo de mídia (por exemplo, mp3, mp4, wav, flac).
        - language_code: Código do idioma do áudio (padrão: 'pt-BR').
        - output_bucket: Nome do bucket S3 onde o resultado da transcrição será armazenado (opcional).
        
        Retorna:
        - response: Resposta do serviço Amazon Transcribe.
        """
        # Verificar se já existe um trabalho com o mesmo nome
        try: 
            self.transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
        except:
            pass
        
        try:
            # Converte o formato do áudio para um formato suportado pelo transcribe
            if media_format == 'oga':
                media_format = 'ogg'

            # Inicia o trabalho de transcrição com os parâmetros fornecidos
            response = self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': job_uri},
                MediaFormat=media_format,
                LanguageCode=language_code,
                OutputBucketName=output_bucket
            )

            response_item = self.get_transcription_result(job_name)
            return response_item
                
        except Exception as e:
            # Em caso de erro, imprime a mensagem de erro e relança a exceção
            print(f"Erro ao começar a transcrição do áudio: {str(e)}")
            raise

    def get_transcription_result(self, job_name):
        """
        Obtém o resultado da transcrição após a conclusão do trabalho e retorna o response completo do objeto.

        Parâmetros:
        - job_name: Nome do trabalho de transcrição.

        Retorna:
        - response: Response completo do serviço Amazon Transcribe.
        """
        while True:
            # Verifica o status do trabalho de transcrição
            response = self.transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            transcribe_status = response['TranscriptionJob']['TranscriptionJobStatus']
            
            # Retorna o response completo do serviço Amazon Transcribe
            if transcribe_status == 'COMPLETED':
                return response['TranscriptionJob']['Transcript']['TranscriptFileUri'] 
           
            # Caso falhe, retorna um erro
            if transcribe_status == 'FAILED':
                raise Exception("Transcription Service failed")
            
            # Aguarda antes de verificar novamente
            time.sleep(2.5)