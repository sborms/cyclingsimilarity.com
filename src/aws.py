import io
import os
import pickle

import boto3
import pandas as pd
from dotenv import load_dotenv
from fastai.collab import load_learner


class AWSManager:
    def __init__(self):
        self.session = AWSManager.authenticate_to_aws()

    @staticmethod
    def authenticate_to_aws():
        """Authenticates to AWS given credentials stored in a .env file."""
        load_dotenv()

        session = boto3.Session(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        return session

    @staticmethod
    def get_status(response):
        """Prints the status code from an AWS response."""
        status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        print(f"Status: {status}")

    def list_s3_buckets(self):
        """Lists all S3 buckets in account."""
        s3 = self.session.client("s3")
        response = s3.list_buckets()
        buckets = [bucket["Name"] for bucket in response["Buckets"]]

        return buckets

    #####################
    ##### STORAGE     ###
    #####################

    def store_data_from_file_to_s3(self, file, bucket, key):
        """Stores data from a file to specified S3 bucket."""
        s3 = self.session.client("s3")
        s3.upload_file(Bucket=bucket, Key=key, Filename=file)

    def store_data_from_string_to_s3(self, string, bucket, key):
        """Stores a string or text file to specified S3 bucket."""
        s3 = self.session.client("s3")
        response = s3.put_object(Bucket=bucket, Key=key, Body=string)

        AWSManager.get_status(response)

    def store_pickle_to_s3(self, obj, bucket, key):
        """Stores an object as a pickle file to specified S3 bucket."""
        s3 = self.session.client("s3")
        with io.BytesIO() as buffer:
            pickle.dump(obj, buffer)
            buffer.seek(0)

            response = s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())

        AWSManager.get_status(response)

    def store_pandas_as_csv_to_s3(self, df, bucket, key):
        """Stores a pandas DataFrame as a csv file to specified S3 bucket."""
        s3 = self.session.client("s3")
        with io.StringIO() as buffer:
            df.to_csv(buffer, index=False)

            response = s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())

        AWSManager.get_status(response)

    #####################
    ##### RETRIEVAL   ###
    #####################

    def load_data_from_s3(self, bucket, key, is_pickle=False):
        """Loads data key from specified S3 bucket."""
        s3 = self.session.client("s3")
        response = s3.get_object(Bucket=bucket, Key=key)

        AWSManager.get_status(response)

        # this is a bit tricky in case the request failed
        if is_pickle:
            obj = pickle.loads(response.get("Body").read())
        else:
            obj = response.get("Body").read()

        return obj

    def load_csv_as_pandas_from_s3(self, bucket, key, **kwargs):
        """Loads a csv file from specified S3 bucket into a pandas DataFrame."""
        s3 = self.session.client("s3")
        response = s3.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(response.get("Body"), **kwargs)

        AWSManager.get_status(response)

        return df

    def load_learner_from_s3(self, bucket, key):
        """Loads a fastai learner from specified S3 bucket."""
        s3 = self.session.resource("s3")
        with io.BytesIO() as data:
            s3.Bucket(bucket).download_fileobj(key, data)
            data.seek(
                0
            )  # move back to the beginning after writing (not to disk though)
            learn = load_learner(
                data
            )  # only works if first stored via learn.export(), not plain pickle

        return learn
