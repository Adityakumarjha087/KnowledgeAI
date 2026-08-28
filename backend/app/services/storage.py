import os
import boto3
from abc import ABC, abstractmethod
from botocore.client import Config
from app.core.config import settings


class StorageProvider(ABC):
    @abstractmethod
    def upload_file(self, file_bytes: bytes, file_name: str, content_type: str) -> str:
        """Uploads a file and returns its access path / URL"""
        pass

    @abstractmethod
    def download_file(self, file_path: str) -> bytes:
        """Downloads a file's bytes from storage"""
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Deletes a file from storage"""
        pass


class LocalStorageProvider(StorageProvider):
    def __init__(self, base_dir: str = "data/uploads"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_full_path(self, file_name: str) -> str:
        return os.path.join(self.base_dir, file_name)

    def upload_file(self, file_bytes: bytes, file_name: str, content_type: str) -> str:
        # Prevent path traversal attacks
        safe_name = os.path.basename(file_name)
        full_path = self._get_full_path(safe_name)
        with open(full_path, "wb") as f:
            f.write(file_bytes)
        return safe_name

    def download_file(self, file_path: str) -> bytes:
        safe_path = self._get_full_path(os.path.basename(file_path))
        if not os.path.exists(safe_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(safe_path, "rb") as f:
            return f.read()

    def delete_file(self, file_path: str) -> bool:
        safe_path = self._get_full_path(os.path.basename(file_path))
        if os.path.exists(safe_path):
            os.remove(safe_path)
            return True
        return False


class S3StorageProvider(StorageProvider):
    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_ENDPOINT_URL,
            region_name=settings.AWS_REGION,
            config=Config(signature_version="s3v4")
        )
        self.bucket = settings.STORAGE_BUCKET
        # Ensure bucket exists (or suppress errors in testing if connection fails)
        try:
            self.s3_client.create_bucket(Bucket=self.bucket)
        except Exception:
            pass

    def upload_file(self, file_bytes: bytes, file_name: str, content_type: str) -> str:
        safe_name = os.path.basename(file_name)
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=safe_name,
            Body=file_bytes,
            ContentType=content_type
        )
        return safe_name

    def download_file(self, file_path: str) -> bytes:
        response = self.s3_client.get_object(Bucket=self.bucket, Key=file_path)
        return response["Body"].read()

    def delete_file(self, file_path: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=file_path)
            return True
        except Exception:
            return False


# Dependency injector to resolve correct storage provider based on environment variables
def get_storage_provider() -> StorageProvider:
    if settings.STORAGE_PROVIDER == "s3":
        return S3StorageProvider()
    return LocalStorageProvider()
