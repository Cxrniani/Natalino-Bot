import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

class S3BucketConfiguration:
    def __init__(self, bucket_name):
        """
        Inicializa o cliente S3 e define o nome do bucket.
        """
        self.s3_client = boto3.client('s3', region_name='us-east-1')
        self.bucket_name = bucket_name

        self.set_public_access_block()
        self.set_notification_configuration()

    def get_public_access_block(self):
        """
        Obtém a configuração de bloqueio de acesso público do bucket S3 e a retorna formatada em JSON.
        """
        try:
            response = self.s3_client.get_public_access_block(Bucket=self.bucket_name)
            return json.dumps(response, indent=4)
        except ClientError as e:
            print(f"Erro ao obter configuração de bloqueio de acesso público: {e}")
            return None
        except NoCredentialsError:
            print("Credenciais AWS não encontradas.")
            return None

    def set_public_access_block(self, block_public_acls=False, ignore_public_acls=False, block_public_policy=False, restrict_public_buckets=False):
        """
        Define a configuração de bloqueio de acesso público para o bucket S3.
        """
        try:
            self.s3_client.put_public_access_block(
                Bucket=self.bucket_name,
                PublicAccessBlockConfiguration={
                    'BlockPublicAcls': block_public_acls,
                    'IgnorePublicAcls': ignore_public_acls,
                    'BlockPublicPolicy': block_public_policy,
                    'RestrictPublicBuckets': restrict_public_buckets
                }
            )
            print(f"Configuração de bloqueio de acesso público para o bucket {self.bucket_name} atualizada com sucesso.")
        except ClientError as e:
            print(f"Erro ao definir configuração de bloqueio de acesso público: {e}")
        except NoCredentialsError:
            print("Credenciais AWS não encontradas.")

    def set_notification_configuration(self):
        """
        Define a configuração de notificação para o bucket S3 para acionar uma função Lambda quando um objeto .mp3 for criado.
        """
        bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "Statement1",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": [
                            f"arn:aws:s3:::{self.bucket_name}/*",
                            f"arn:aws:s3:::{self.bucket_name}/*"
                        ]
                    }
                ]
            }

        bucket_policy = json.dumps(bucket_policy)
        try:
            self.s3_client.put_bucket_policy(Bucket=self.bucket_name, Policy=bucket_policy)
            print(f"Configuração de notificação para o bucket {self.bucket_name} atualizada com sucesso.")
        except ClientError as e:
            print(f"Erro ao configurar notificação do bucket: {e}")
        except NoCredentialsError:
            print("Credenciais AWS não encontradas.")
