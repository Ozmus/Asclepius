from botocore.awsrequest import logger
from botocore.exceptions import ClientError


def delete_twitter_credentials(dynamo_db, discord_id):
    try:
        table = dynamo_db.Table('TwitterCredentials')
        table.delete_item(Key={'discord_id': discord_id})
    except ClientError as err:
        logger.error(
            "Couldn't delete twitter credentials %s. Here's why: %s: %s", discord_id,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise

