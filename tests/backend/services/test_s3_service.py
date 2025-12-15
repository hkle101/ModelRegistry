from __future__ import annotations

from io import BytesIO

from backend.services.s3_service import S3Service


class _FakeS3:
    """Minimal in-memory stub of the boto3 S3 client used by `S3Service` tests."""

    def __init__(self):
        self.uploads = []
        self.downloads = []
        self.deletes = []
        self.deleted_batches = []
        self.presigned = []
        self.objects = {"k": b"data"}

    def upload_fileobj(self, fileobj: BytesIO, bucket: str, key: str):
        self.uploads.append((bucket, key, fileobj.read()))

    def download_fileobj(self, bucket: str, key: str, fileobj: BytesIO):
        self.downloads.append((bucket, key))
        fileobj.write(self.objects[key])

    def generate_presigned_url(self, op: str, Params, ExpiresIn: int):
        self.presigned.append((op, Params, ExpiresIn))
        return f"https://example.com/{Params['Key']}?exp={ExpiresIn}"

    def delete_object(self, Bucket: str, Key: str):
        self.deletes.append((Bucket, Key))

    def list_objects_v2(self, Bucket: str):
        return {"Contents": [{"Key": "a"}, {"Key": "b"}]}

    def delete_objects(self, Bucket: str, Delete):
        self.deleted_batches.append((Bucket, Delete))


def test_s3_service_upload_artifact_returns_s3_uri():
    svc = S3Service(bucket_name="b")
    svc.s3 = _FakeS3()

    uri = svc.upload_artifact(b"abc", "id1", "file.bin")
    assert uri == "s3://b/artifacts/id1/file.bin"
    assert svc.s3.uploads == [("b", "artifacts/id1/file.bin", b"abc")]


def test_s3_service_download_artifact_reads_bytes():
    svc = S3Service(bucket_name="b")
    fake = _FakeS3()
    fake.objects["artifacts/id1/file.bin"] = b"xyz"
    svc.s3 = fake

    out = svc.download_artifact("artifacts/id1/file.bin")
    assert out == b"xyz"


def test_s3_service_generate_presigned_url_passes_params():
    svc = S3Service(bucket_name="b")
    svc.s3 = _FakeS3()

    url = svc.generate_presigned_url("artifacts/id1/file.bin", expires_in=123)
    assert url.endswith("artifacts/id1/file.bin?exp=123")


def test_s3_service_delete_artifact_returns_true():
    svc = S3Service(bucket_name="b")
    svc.s3 = _FakeS3()

    ok = svc.delete_artifact("artifacts/id1/file.bin")
    assert ok is True
    assert svc.s3.deletes == [("b", "artifacts/id1/file.bin")]


def test_s3_service_reset_bucket_deletes_all_contents():
    svc = S3Service(bucket_name="b")
    svc.s3 = _FakeS3()

    svc.reset_bucket()
    assert svc.s3.deleted_batches == [
        ("b", {"Objects": [{"Key": "a"}, {"Key": "b"}]})
    ]
