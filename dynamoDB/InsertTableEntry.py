from botocore.awsrequest import logger
from botocore.exceptions import ClientError


def add_twitter_credentials(dynamo_db, discord_id, username, user_id, access_token, access_token_secret):
    try:
        table = dynamo_db.Table('TwitterCredentials')
        table.put_item(
            Item={
                'discord_id': discord_id,
                'username': username,
                'user_id': user_id,
                'access_token': access_token,
                'access_token_secret': access_token_secret})
    except ClientError as err:
        logger.error(
            "Couldn't add twitter credentials %s to table %s. Here's why: %s: %s",
            discord_id, table.name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise

def add_spotify_credentials(dynamo_db, discord_id, access_token, refresh_token):
    try:
        table = dynamo_db.Table('SpotifyCredentials')
        table.put_item(
            Item={
                'discord_id': discord_id,
                'access_token': access_token,
                'refresh_token': refresh_token})
    except ClientError as err:
        logger.error(
            "Couldn't add spotify credentials %s to table %s. Here's why: %s: %s",
            discord_id, table.name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise

