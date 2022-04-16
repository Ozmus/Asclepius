from botocore.awsrequest import logger


def get_twitter_credentials(dynamo_db, discord_id):
    get_credentials(dynamo_db, discord_id, 'Twitter')


def get_spotify_credentials(dynamo_db, discord_id):
    get_credentials(dynamo_db, discord_id, 'Spotify')


def get_credentials(dynamo_db, discord_id, type):
    try:
        table = dynamo_db.Table(f"{type}Credentials")
        response = table.get_item(Key={'discord_id': discord_id})
        return response['Item']
    except:
        logger.error(
            f"Couldn't get {type} credentials %s from table %s. Here's why: %s: %s",
            discord_id, table.name)
        raise
