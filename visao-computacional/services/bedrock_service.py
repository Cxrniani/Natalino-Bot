import boto3
import botocore
import json
from botocore.exceptions import ClientError

"""
Caso for testar o Bedrock veja se está habilitado o modelo no AWS Bedrock (https://us-east-1.console.aws.amazon.com/bedrock/home?region=us-east-1#/modelaccess)
"""

class BedrockService:
    def __init__(self):
        """
        Inicializa o serviço AWS Bedrock.

        Cria uma sessão do Boto3 e um cliente para o serviço Bedrock, com a região configurada como 'us-east-1'.
        """
        # Inicia a sessão do Boto3
        self.session = boto3.Session(region_name='us-east-1')

        # Inicia o serviço Bedrock
        self.bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
               
    def set_intent_lex(self, intent, msg=None):
        """
        Define a mensagem a ser usada pelo serviço de geração de texto.

        Parameters:
            msg (str): Mensagem que descreve a raça do animal de estimação.

        Returns:
            bool: Retorna True após definir a mensagem.
        """
        self.message_intent = intent
        self.message_text = msg
        return True

    def create_prompt(self):
        """
        Cria um prompt detalhado para o modelo Bedrock.

        O prompt fornece instruções para gerar uma resposta humanizada em Português-Brasil, informando que não foi possível entender a solicitação do usuário e fornecendo as informações que podem ser lidas.

        Returns:
            str: O prompt formatado para ser enviado ao modelo.
        """

        if self.message_intent == 'voice':
            prompt = f"""
                {self.message_text}

                O que o texto deseja? Escolha uma das opções a seguir:
                realizar doação
                saber mais
                """


            return prompt
        
        prompt = f"""
            Você é um assistente virtual humanizado.
            Gere um texto claro com os seguintes pontos:

            Reconheça que a solicitação não foi compreendida e peça desculpas pelo inconveniente.
            Ofereça o instagram @natal_dos_pequenos para quaisquer dúvidas ou informações adicionais.
            Mantenha um tom amigável, encorajador e ofereça suporte adicional ao usuário.
            Instrua o usuário que ele pode tentar realizar uma doação novamente digitando 'realizar doação' ou optar por saber mais digitando 'saber mais'.
        """


        
        return prompt
     
    def generate_request_body(self):
        """
        Gera o corpo da requisição para enviar ao modelo Bedrock.

        Inclui o prompt e configurações de geração de texto como o número máximo de tokens, temperatura e topP.

        Returns:
            str: O corpo da requisição em formato JSON.
        """
        request_body = {
            "inputText": self.create_prompt(),
            "textGenerationConfig": {
                "maxTokenCount": 384,
                "temperature": 0.5, # temperature: aleatoriedade na geração de texto (quanto maior, mais aleatório e menos conservador o texto é)
                "topP": 0.9 # topP: tokens que compõem o top p% da probabilidade cumulativa
            },
        }
        return json.dumps(request_body)

    def invoke_model(self):
        """
        Invoca o modelo Bedrock com o corpo da requisição gerado.

        Configura os parâmetros de invocação, incluindo o ID do modelo, o tipo de conteúdo e o corpo da requisição. Processa a resposta do modelo e retorna a resposta formatada.

        Returns:
            dict: Resposta formatada com o código de status e o texto gerado pelo modelo.
        """
        model_id = "amazon.titan-text-express-v1"

        try:
            # Invoca o modelo com o corpo da requisição gerado
            response = self.bedrock.invoke_model(
                modelId=model_id, 
                contentType='application/json',
                accept="*/*",
                body=self.generate_request_body()
            )
            
            # Processa a resposta do modelo
            model_response = json.loads(response["body"].read().decode('utf-8'))
            response_text = model_response["results"][0]["outputText"]

            # Retorna a resposta formatada
            return {'statusCode': 200, 'message': json.dumps(response_text, indent=4, ensure_ascii=False)}
        
        except ClientError as e:
            print(f"Error invoking model: {e}")
            return {'statusCode': 500, 'body': json.dumps(str(e))}
