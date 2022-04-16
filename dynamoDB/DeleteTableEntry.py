from botocore.awsrequest import logger
from botocore.exceptions import ClientError


def delete_twitter_credentials(dynamo_db, discord_id):
    delete_credentials(dynamo_db, discord_id, 'Twitter')


def delete_spotify_credentials(dynamo_db, discord_id):
    delete_credentials(dynamo_db, discord_id, 'Spotify')


def delete_credentials(dynamo_db, discord_id, type):
    try:
        table = dynamo_db.Table(f"{type}Credentials")
        table.delete_item(Key={'discord_id': discord_id})
    except ClientError as err:
        logger.error(
            f"Couldn't delete {type} credentials %s. Here's why: %s: %s", discord_id,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
