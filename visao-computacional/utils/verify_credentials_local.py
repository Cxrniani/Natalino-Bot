import boto3
from botocore.exceptions import ClientError

class AWSUtils:
    def __init__(self, region_name='us-east-1'):
        self.session = boto3.Session(region_name=region_name)
        self.iam_client = self.session.client('iam')
        self.dynamodb_client = self.session.client('dynamodb')
        self.s3_client = self.session.client('s3')

    def verify_credentials(self):
        try:
            sts_client = self.session.client('sts')
            identity = sts_client.get_caller_identity()
            print("AWS credentials are valid.")
            print(f"Account: {identity['Account']}, UserID: {identity['UserId']}, ARN: {identity['Arn']}")
        except ClientError as e:
            print(f"Error verifying credentials: {e}")
            return False
        return True

    def list_dynamodb_tables(self):
        try:
            response = self.dynamodb_client.list_tables()
            print("DynamoDB Tables:", response['TableNames'])
        except ClientError as e:
            print(f"Error listing DynamoDB tables: {e}")
            return False
        return True

    def list_s3_buckets(self):
        try:
            response = self.s3_client.list_buckets()
            print("S3 Buckets:", [bucket['Name'] for bucket in response['Buckets']])
        except ClientError as e:
            print(f"Error listing S3 buckets: {e}")
            return False
        return True

    def create_iam_policy(self, policy_name, policy_document):
        try:
            response = self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=policy_document
            )
            print(f"Policy {policy_name} created with ARN: {response['Policy']['Arn']}")
        except ClientError as e:
            print(f"Error creating IAM policy: {e}")
            return False
        return True

if __name__ == "__main__":
    aws_utils = AWSUtils()

    if aws_utils.verify_credentials():
        aws_utils.list_dynamodb_tables()
        aws_utils.list_s3_buckets()