import pytest

from src.aws import AWSManager


@pytest.mark.skip(reason="avoids connecting to AWS")
def test_s3_bucket_exists():
    aws_manager = AWSManager()

    buckets = aws_manager.list_s3_buckets()

    assert "cyclingsimilarity-s3" in buckets
