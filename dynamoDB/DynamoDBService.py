import boto3
from dotenv import load_dotenv
import os
from dynamoDB.tables.TwitterCredentials import *
from dynamoDB.tables.SpotifyCredentials import *


load_dotenv()
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_ACCESS_KEY_SECRET = os.getenv('AWS_ACCESS_KEY_SECRET')
REGION_NAME = 'us-east-1'

def connectDynamoDB():
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
    return client, dynamodb

def createTables(client, dynamodb):
    existing_tables = client.list_tables()['TableNames']
    if 'TwitterCredentials' not in existing_tables:
        twitter_credentials = TwitterCredentials(dynamodb)
        twitter_credentials.create_table('TwitterCredentials')
    if 'SpotifyCredentials' not in existing_tables:
        spotify_credentials = SpotifyCredentials(dynamodb)
        spotify_credentials.create_table('SpotifyCredentials')


# to add new entry to spotify

# add_spotify_credentials(
#     dynamo_db=dynamodb,
#     discord_id='5415dasdaasd1as56f1as65f1as65asf1as65',
#     access_token='asdjasd',
#     refresh_token='oksfdsdf5sd1f65sdf1sfd'
# )



# to get an entry from table

# try:
#     spotify_credentials = get_spotify_credentials(
#         dynamo_db=dynamodb,
#         discord_id='5415dasdaasd1as56f1as65f1as65asf1as65'
#     )
# except:
#     print('exception')
# print(twitter_credentials)


# add_twitter_credentials(
#     dynamo_db=dynamodb,
#     discord_id='5415dasdaasd1as56f1as65f1as65asf1as65',
#     username='mahmut',
#     user_id='16516530',
#     access_token='asdjasd',
#     access_token_secret='oksfdsdf5sd1f65sdf1sfd'
# )

# try:
#     twitter_credentials = get_twitter_credentials(
#         dynamo_db=dynamodb,
#         discord_id='5415dasdaasd1as56f1as65f1as65asf1as65'
#     )
# except:
#     print('except')
# print(twitter_credentials)

# delete_twitter_credentials(dynamo_db=dynamodb,
#                            discord_id='5415dasdaasd1as56f1as65f1as65asf1as65')
