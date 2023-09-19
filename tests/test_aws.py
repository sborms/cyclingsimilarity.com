from src.aws import authenticate_to_aws

aws_session = authenticate_to_aws()


def test_s3_bucket_exists():
    s3 = aws_session.client("s3")
    response = s3.list_buckets()
    buckets = [bucket["Name"] for bucket in response["Buckets"]]

    assert "cyclingsimilarity-s3" in buckets
