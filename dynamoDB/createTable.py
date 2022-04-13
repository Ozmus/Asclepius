import boto3
from dotenv import load_dotenv
import os


load_dotenv()
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_ACCESS_KEY_SECRET = os.getenv('AWS_ACCESS_KEY_SECRET')
REGION_NAME = 'us-east-1'

client = boto3.client(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_ACCESS_KEY_SECRET,
    region_name=REGION_NAME
    )

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_ACCESS_KEY_SECRET,
    region_name=REGION_NAME
    )
ddb_exceptions = client.exceptions

