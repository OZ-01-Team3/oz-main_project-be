import logging
import base64
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def get_secret():
    secret_name = "prod/django"
    region_name = "ap-northeast-2"
    profile_name = "mainteam3"

    session = boto3.session.Session(profile_name=profile_name)
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        logger.info("Secret retrieved successfully.")
    except ClientError as e:
        if e.response['Error']['Code'] == "DecryptionFailure":
            msg = f"The requested secret can't be decrypted using the provided KMS key: {str(e)}"
        elif e.response['Error']['Code'] == "InternalServiceError":
            msg = f"An error occurred on service side: {str(e)}"
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            msg = f"The request had invalid params: {str(e)}"
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            msg = f"The request was invalid due to: {str(e)}"
        elif e.response["Error"]["Code"] == "ResourceNotFoundException":
            msg = f"The requested secret {secret_name} was not found."
        else:
            msg = f"An unknown error occurred: {str(e)}."
        logger.error(msg)
        raise e
    else:
        if "SecretString" in get_secret_value_response:
            return get_secret_value_response['SecretString']
        else:
            return base64.b64decode(get_secret_value_response["SecretBinary"])
