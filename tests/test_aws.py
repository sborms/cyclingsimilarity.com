from src.aws import AWSManager

aws_manager = AWSManager()


def test_s3_bucket_exists():
    buckets = aws_manager.list_s3_buckets()

    assert "cyclingsimilarity-s3" in buckets
