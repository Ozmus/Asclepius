from botocore.awsrequest import logger


def get_twitter_credentials(dynamo_db, discord_id):
    try:
        table = dynamo_db.Table('TwitterCredentials')
        response = table.get_item(Key={'discord_id': discord_id})
        return response['Item']
    except:
        logger.error(
            "Couldn't get twitter credentials %s from table %s. Here's why: %s: %s",
            discord_id, table.name)
        raise
    
def get_spotify_credentials(dynamo_db, discord_id):
    try:
        table = dynamo_db.Table('SpotifyCredentials')
        response = table.get_item(Key={'discord_id': discord_id})
        return response['Item']
    except:
        logger.error(
            "Couldn't get spotify credentials %s from table %s. Here's why: %s: %s",
            discord_id, table.name)
        raise
