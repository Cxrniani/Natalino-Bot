import boto3

# Inicializa o cliente e recurso do boto3
cloudformation_client = boto3.client('cloudformation')
s3_resource = boto3.resource('s3')

stack_name = 'appGrupo03Sprint10-dev'

# Lista os recursos na stack
resources = cloudformation_client.list_stack_resources(StackName=stack_name)

for resource in resources['StackResourceSummaries']:
    resource_type = resource['ResourceType']
    resource_id = resource['PhysicalResourceId']

    if resource_type == 'AWS::S3::Bucket':
        try:
            # Esvazia e exclui o bucket S3
            bucket = s3_resource.Bucket(resource_id)
            bucket.objects.delete()
            bucket.delete()
            print(f"Bucket {resource_id} excluído com sucesso.")
        except Exception as e:
            print(f"Erro ao excluir bucket {resource_id}: {str(e)}")

# Tenta excluir a stack novamente
try:
    cloudformation_client.delete_stack(StackName=stack_name)
    print(f"Solicitação de exclusão da stack {stack_name} enviada.")
except Exception as e:
    print(f"Erro ao excluir a stack {stack_name}: {str(e)}")
