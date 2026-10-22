import os
import shutil
import uuid
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from solarops.acquisition.brpvgen import checksum


class ObjectStore:
    def __init__(self, settings, initialize=True):
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
            if not initialize:
                return
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
        target = self.raw_path(org, digest, path.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            staged = self.root / "staging" / org / ("raw-" + uuid.uuid4().hex) / path.name
            staged.parent.mkdir(parents=True, exist_ok=False)
            with path.open("rb") as source, staged.open("xb") as out:
                shutil.copyfileobj(source, out)
                out.flush()
                os.fsync(out.fileno())
            if checksum(staged) != digest:
                raise ValueError("Immutable raw object checksum differs")
            # Link a completed file atomically without replacing a concurrent winner.
            # Keep staging evidence; it shares bytes with the published file on success.
            try:
                os.link(staged, target)
            except FileExistsError:
                pass
        if checksum(target) != digest:
            raise ValueError("Immutable raw object checksum differs")
        if self.client:
            try:
                obj = self.client.head_object(Bucket=self.bucket, Key=key)
                if obj["Metadata"].get("sha256") != digest:
                    raise ValueError("Immutable raw object checksum differs")
            except ClientError as exc:
                if exc.response["Error"]["Code"] not in ("404", "NoSuchKey"):
                    raise
                self.upload(target, key)
            return f"s3://{self.bucket}/{key}"
        return str(target.resolve())

    def raw_path(self, org, digest, name):
        return self.root / "raw" / org / digest / name
