import os
import shutil
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from solarops.acquisition.brpvgen import checksum


class ObjectStore:
    def __init__(self, settings):
        self.root = settings.root
        self.bucket = os.getenv("SOLAROPS_S3_BUCKET", "solarops-demo")
        self.client = None
        if settings.s3_endpoint:
            self.client = boto3.client(
                "s3",
                endpoint_url=settings.s3_endpoint,
                aws_access_key_id=os.environ["SOLAROPS_S3_ACCESS_KEY"],
                aws_secret_access_key=os.environ["SOLAROPS_S3_SECRET_KEY"],
                region_name="us-east-1",
            )
            try:
                self.client.head_bucket(Bucket=self.bucket)
            except ClientError as exc:
                if exc.response["Error"]["Code"] not in ("404", "NoSuchBucket"):
                    raise
                self.client.create_bucket(Bucket=self.bucket)

    def upload(self, path: Path, key: str):
        if self.client:
            self.client.upload_file(
                str(path), self.bucket, key, ExtraArgs={"Metadata": {"sha256": checksum(path)}}
            )
            return f"s3://{self.bucket}/{key}"
        return str(path.resolve())

    def raw(self, path, org, digest):
        key = f"raw/{org}/{digest}/{path.name}"
        if self.client:
            try:
                obj = self.client.head_object(Bucket=self.bucket, Key=key)
                if obj["Metadata"].get("sha256") != digest:
                    raise ValueError("Immutable raw object checksum differs")
            except ClientError as exc:
                if exc.response["Error"]["Code"] not in ("404", "NoSuchKey"):
                    raise
                self.upload(path, key)
            return f"s3://{self.bucket}/{key}"
        target = self.root / key
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with path.open("rb") as source, target.open("xb") as out:
                shutil.copyfileobj(source, out)
        if checksum(target) != digest:
            raise ValueError("Immutable raw object checksum differs")
        return str(target.resolve())
