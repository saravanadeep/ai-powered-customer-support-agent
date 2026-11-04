
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

def upload_knowledge_document(file_path: str, object_key: str):
    client = get_storage_client()

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(path)

    # Calculate SHA-256 checksum
    sha256 = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(block)

    checksum = sha256.hexdigest()

    # Determine content type
    content_types = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    content_type = content_types.get(
        path.suffix.lower(),
        "application/octet-stream"
    )

    # Upload original document to Neon
    client.upload_file(
        str(path),
        "knowledge-base",
        object_key,
        ExtraArgs={
            "ContentType": content_type,
            "Metadata": {
                "sha256": checksum
            }
        }
    )

    # Verify upload
    response = client.head_object(
        Bucket="knowledge-base",
        Key=object_key
    )

    return {
        "success": True,
        "object_key": object_key,
        "filename": path.name,
        "size": response["ContentLength"],
        "checksum": checksum
    }


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


def upload_index_file(file_path: str, object_key: str):
    """Upload the TF-IDF index to object storage."""

    client = get_storage_client()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(path)

    client.upload_file(
        str(path),
        "knowledge-base",
        object_key,
        ExtraArgs={
            "ContentType": "application/octet-stream"
        }
    )

    # Verify upload
    response = client.head_object(
        Bucket="knowledge-base",
        Key=object_key
    )

    return {
        "success": True,
        "object_key": object_key,
        "size": response["ContentLength"]
    }


def download_index_file(object_key: str, destination_path: str):
    """Download the TF-IDF index from object storage."""

    client = get_storage_client()
    path = Path(destination_path)

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        client.download_file(
            "knowledge-base",
            object_key,
            str(path)
        )

        return {
            "success": True,
            "object_key": object_key,
            "local_path": str(path)
        }

    except Exception as exc:
        from botocore.exceptions import ClientError

        if (
            isinstance(exc, ClientError)
            and exc.response.get("Error", {}).get("Code") == "404"
        ):
            return {
                "success": False,
                "message": "Index does not exist in object storage."
            }

        raise




if __name__ == "__main__":
    test_storage_connection()

