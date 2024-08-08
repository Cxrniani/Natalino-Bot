import boto3
from botocore.exceptions import ClientError

class LambdaClass():
    
    # Inicia o serviço da Lambda
    def __init__(self):
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        self.increaseLambdaTimeOut()

    def list_lambda_functions(self):
        
        try: 
            response = self.lambda_client.list_functions()
            function_names = [function['FunctionName'] for function in response.get('Functions', []) 
                              if function['FunctionName'] != 'NatalinoBot-projeto-final-dev-webhook' and
                                function['FunctionName'] != 'aws-controltower-NotificationForwarder']
            return function_names
        
        except ClientError as e:
            print(f"Error listing Lambda Function: {e}")
            return None
        
    def update_lambda_timeout(self, function_name, timeout):
        try:
            response = self.lambda_client.update_function_configuration(
                FunctionName=function_name,
                Timeout=timeout
            )
            return response
        except ClientError as e:
            print(f"Error updating Lambda timeout: {e}")
            return None
    
    def increaseLambdaTimeOut(self):
        list_lambda = self.list_lambda_functions()

        for function_name in list_lambda:
            self.update_lambda_timeout(function_name, 30)
        self.update_lambda_timeout('NatalinoBot-projeto-final-dev-webhook', 90)
        return True
