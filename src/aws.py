import io
import os

import boto3
from dotenv import load_dotenv
from fastai.collab import load_learner


def authenticate_to_aws():
    """Authenticates to AWS given credentials stored in .env file."""
    load_dotenv()

    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    )

    return session


def store_data_to_s3(session, file, bucket, key):
    """Stores data to specified S3 bucket."""
    s3 = session.client("s3")
    s3.upload_file(Filename=file, Bucket=bucket, Key=key)


def load_data_from_s3(session, bucket, key):
    """Loads data from specified S3 bucket."""
    s3 = session.client("s3")
    obj = s3.get_object(Bucket=bucket, Key=key)

    return obj


def load_learner_from_s3(session, bucket, key):
    """Loads a fastai learner from specified S3 bucket."""
    s3 = session.resource("s3")
    with io.BytesIO() as data:
        s3.Bucket(bucket).download_fileobj(key, data)
        data.seek(0)  # move back to the beginning after writing (not to disk though)
        learn = load_learner(data)

    return learn
