import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import BotoCoreError, ClientError
from uuid import uuid4

class DynamoDBClass: 
    def __init__(self, dynamodb_table_name):
        """
        Inicializa a classe DynamoDBClass com o nome da tabela do DynamoDB e cria a sessão do DynamoDB.

        :param dynamodb_table_name: Nome da tabela do DynamoDB.
        """
        # Criação de nome da Dynamo Table
        self.dynamodb_table_name = dynamodb_table_name

        # Inicia a sessão do DynamoDB
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Inicia o serviço DynamoDB
        self.dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
    
    def create_table_dynamodb(self):
        """
        Cria uma tabela no DynamoDB se ela ainda não existir.

        :return: None
        """
        # Lista as tabelas existentes no DynamoDB
        tables = self.dynamodb_client.list_tables()

        # Verifica se a tabela já existe
        if self.dynamodb_table_name not in tables['TableNames']:
            try:
                # Define o esquema da tabela e suas propriedades
                table = self.dynamodb.create_table(
                    TableName=self.dynamodb_table_name,
                    KeySchema=[
                        {
                            'AttributeName': 'id',
                            'KeyType': 'HASH'  # Define a chave primária da tabela
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'id',
                            'AttributeType': 'S'  # Define o tipo de atributo da chave primária como String
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,  # Define a capacidade de leitura provisionada
                        'WriteCapacityUnits': 5  # Define a capacidade de escrita provisionada
                    }
                )

                # Espera até que a tabela exista para confirmar a criação
                table.meta.client.get_waiter('table_exists').wait(TableName=self.dynamodb_table_name)
                print('LOG: Criação de Tabela de log concluída com sucesso.')

            except (BotoCoreError, ClientError) as e: 
                # Caso ocorra um erro, imprime a mensagem de erro
                print(f'Error: {e}')

        else:
            print('LOG: Tabela de log foi criada previamente.')            

    def get_item(self, unique_id):
        """
        Método para buscar o item no DynamoDB pelo ID.

        :param unique_id: ID único do item a ser buscado.
        :return: Item encontrado no DynamoDB ou dicionário vazio.
        """
        table = self.dynamodb.Table(self.dynamodb_table_name)
        
        try: 
            # Busca o item no DynamoDB pelo ID
            response = table.get_item(Key={'id': unique_id})
            return response.get('Item', {})
            
        except ClientError as e: 
            # Caso ocorra um erro, retorna None
            print(f"Erro ao buscar o item no DynamoDB: {e}")
            return None
    
    def list_dynamodb_tables(self):
        """
        Lista as tabelas do DynamoDB.

        :return: True se as tabelas forem listadas com sucesso, False em caso de erro.
        """
        try: 
            # Lista as Tabelas do Dynamo
            response = self.dynamodb_client.list_tables()
            print("DynamoDB Tables:", response['TableNames'])
        
        except ClientError as e: 
            # Caso ocorra um erro, retorna False
            print(f"Error listing DynamoDB tables: {e}")
            return False
        return True

    def log_register_dynamodb(self, unique_id, s3_url, donation_type, donation_object=None, conservation_state=None, donation_value=None):
        """
        Registra um log no DynamoDB contendo informações da requisição e resposta.

        :param unique_id: ID único do log.
        :param s3_url: URL da imagem no S3.
        :param donation_type: Tipo de doação (Objeto ou Dinheiro).
        :param donation_object: Descrição do objeto doado.
        :param conservation_state: Estado de conservação do objeto.
        :param donation_value: Valor da doação em R$.
        :return: None
        """
        # Inicia o serviço de DynamoDB e acessa a tabela especificada
        table = self.dynamodb.Table(self.dynamodb_table_name)  

        # Configura os dados do log
        log_item = {
            'id': unique_id,
            'timestamp': datetime.utcnow().isoformat(),
            'url_image': s3_url,  # Foto do brinquedo ou comprovante
            'donation_type': donation_type,  # Objeto ou Dinheiro
            'donation_object': donation_object,  # O que é o objeto. Ex: caminhão, cobertor...
            'conservation_state': conservation_state,  # Bom estado, avariado
            'donation_value': donation_value  # Valor de doação em R$
        }
        
        try: 
            # Insere os dados do log na tabela do DynamoDB
            table.put_item(Item=log_item)
            print("Dados do log inseridos no DynamoDB com sucesso")
        
        except ClientError as e: 
            # Caso ocorra um erro, imprime a mensagem de erro
            print(f"Erro ao inserir os dados do log no DynamoDB: {e}")

    def repeated_value_dynamodb(self, unique_id):
        """
        Verifica se a frase já foi convertida.

        :param unique_id: O unique_id a ser pesquisada no DynamoDB.
        :return: True se a frase for encontrada, False se não for encontrada, None em caso de erro.
        """
        # Inicializa o serviço DynamoDB e acessa a tabela especificada
        table = self.dynamodb.Table(self.dynamodb_table_name)
        
        try: 
            # Usa a operação de get_item com um filtro para encontrar itens com a frase especificada
            response = table.get_item(Key={'id': unique_id}) 
            # Obtém os itens retornados na resposta
            return 'Item' in response
        
        except ClientError as e: 
            # Em caso de erro, imprime a mensagem de erro e retorna None
            print(f"Erro ao buscar a frase no DynamoDB: {e}")
            return None


    def import_table_dynamodb(self):
        """
        Escaneia a tabela DynamoDB para obter todos os itens.

        :return: Lista de itens da tabela
        """
        results = []
        last_evaluated_key = None
        
        # Loop para escanear todos os itens da tabela DynamoDB
        while True:
            if last_evaluated_key:
                # Se houver uma chave avaliada anteriormente, continue a escanear a partir dessa chave
                response = self.dynamodb_client.scan(
                    TableName=self.dynamodb_table_name,
                    ExclusiveStartKey=last_evaluated_key
                )
            else:
                # Caso contrário, inicie o escaneamento do começo da tabela
                response = self.dynamodb_client.scan(TableName=self.dynamodb_table_name)
            
            # Atualiza a última chave avaliada
            last_evaluated_key = response.get('LastEvaluatedKey')
            
            # Adiciona os itens escaneados à lista de resultados
            results.extend(response['Items'])
            
            # Se não houver mais chaves a serem avaliadas, saia do loop
            if not last_evaluated_key:
                break
        
        # Retorna a lista de itens da tabela
        return results
