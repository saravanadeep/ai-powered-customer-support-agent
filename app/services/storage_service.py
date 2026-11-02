
import os
import hashlib
from pathlib import Path

import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()


def get_storage_client():
    required_vars = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_ENDPOINT_URL_S3",
        "AWS_REGION",
    ]

    missing = [
        name for name in required_vars
        if not os.getenv(name)
    ]

    if missing:
        raise EnvironmentError(
            f"Missing storage environment variables: {missing}"
        )

    return boto3.client(
        "s3",
        endpoint_url=os.getenv("AWS_ENDPOINT_URL_S3"),
        region_name=os.getenv("AWS_REGION"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(
            s3={"addressing_style": "path"}
        ),
    )


def test_storage_connection():
    client = get_storage_client()

    response = client.list_objects_v2(
        Bucket="knowledge-base",
        MaxKeys=10,
    )

    objects = response.get("Contents", [])

    print("Neon Object Storage connection successful!")
    print("Bucket: knowledge-base")
    print("Existing objects:", len(objects))

    for obj in objects:
        print("-", obj["Key"])


def upload_test_document(file_path: str):
    client = get_storage_client()

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(path)

    # Generate SHA-256 checksum
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(block)

    checksum = sha256.hexdigest()

    # Keep test files separate from production documents
    object_key = f"migration-test/{path.name}"

    client.upload_file(
        str(path),
        "knowledge-base",
        object_key,
        ExtraArgs={
            "ContentType": "application/pdf",
            "Metadata": {
                "sha256": checksum
            }
        }
    )

    # Verify uploaded object
    response = client.head_object(
        Bucket="knowledge-base",
        Key=object_key
    )

    print("Upload successful!")
    print("Object key:", object_key)
    print("File size:", response["ContentLength"], "bytes")
    print("SHA-256:", checksum)
    print("Stored checksum:", response["Metadata"]["sha256"])

    return object_key



if __name__ == "__main__":
    test_storage_connection()

