import logging
import tempfile
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import UploadFile

from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STORAGE_ROOT = PROJECT_ROOT / "storage"
logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
SUPPORTED_UPLOAD_EXTENSIONS = {".pdf", ".docx", ".md", ".txt"}


def validate_upload_filename(filename: str | None) -> str:
    safe_filename = sanitize_filename(filename)
    if Path(safe_filename).suffix.lower() not in SUPPORTED_UPLOAD_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_UPLOAD_EXTENSIONS))
        raise ValueError(f"Unsupported file type. Supported extensions: {supported}.")
    return safe_filename


def sanitize_filename(filename: str | None) -> str:
    name = Path(filename or "uploaded-file").name.strip()

    if not name or name in {".", ".."}:
        return "uploaded-file"

    return name[:255]


async def save_uploaded_file(
    file: UploadFile,
    user_id: int,
) -> str:
    storage_id = uuid4()

    if settings.storage_backend.lower() == "s3":
        if not settings.s3_bucket:
            raise RuntimeError("S3_STORAGE_BUCKET must be set when STORAGE_BACKEND=s3.")
        total_bytes = 0
        content = bytearray()
        while chunk := await file.read(1024 * 1024):
            total_bytes += len(chunk)
            if total_bytes > MAX_UPLOAD_BYTES:
                raise ValueError(
                    f"Uploaded files must be {MAX_UPLOAD_BYTES // (1024 * 1024)} MB or smaller."
                )
            content.extend(chunk)
        key = f"users/{user_id}/{storage_id}/{sanitize_filename(file.filename)}"
        try:
            _s3_client().put_object(
                Bucket=settings.s3_bucket,
                Key=key,
                Body=bytes(content),
                ContentType=file.content_type or "application/octet-stream",
                ServerSideEncryption="AES256",
            )
        except (BotoCoreError, ClientError) as exc:
            raise RuntimeError("The uploaded file could not be saved to object storage.") from exc
        return f"s3://{settings.s3_bucket}/{key}"

    if settings.storage_backend.lower() != "local":
        raise RuntimeError("STORAGE_BACKEND must be either local or s3.")

    user_directory = STORAGE_ROOT / "users" / str(user_id) / str(storage_id)

    user_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = sanitize_filename(file.filename)
    file_path = user_directory / safe_filename

    total_bytes = 0

    with file_path.open("wb") as output:
        while chunk := await file.read(1024 * 1024):
            total_bytes += len(chunk)

            if total_bytes > MAX_UPLOAD_BYTES:
                file_path.unlink(missing_ok=True)
                raise ValueError(
                    f"Uploaded files must be {MAX_UPLOAD_BYTES // (1024 * 1024)} MB or smaller."
                )

            output.write(chunk)

    return str(file_path.relative_to(PROJECT_ROOT))


def remove_uploaded_file(file_path: str | None) -> None:
    """Remove an uploaded file only when its resolved path is inside storage."""
    if not file_path:
        return

    if file_path.startswith("s3://"):
        parsed = urlparse(file_path)
        if parsed.netloc != settings.s3_bucket or not parsed.path.lstrip("/"):
            return
        try:
            _s3_client().delete_object(Bucket=parsed.netloc, Key=parsed.path.lstrip("/"))
        except (BotoCoreError, ClientError):
            logger.exception("Could not remove uploaded object from S3")
        return

    resolved_path = (PROJECT_ROOT / file_path).resolve()
    storage_root = STORAGE_ROOT.resolve()
    try:
        resolved_path.relative_to(storage_root)
    except ValueError:
        return

    resolved_path.unlink(missing_ok=True)


def _s3_client():
    credentials = {}
    if settings.s3_access_key_id:
        credentials["aws_access_key_id"] = settings.s3_access_key_id
    if settings.s3_secret_access_key:
        credentials["aws_secret_access_key"] = settings.s3_secret_access_key
    return boto3.client(
        "s3",
        region_name=settings.s3_region,
        endpoint_url=settings.s3_endpoint_url or None,
        config=Config(connect_timeout=2, read_timeout=5, retries={"max_attempts": 1}),
        **credentials,
    )


@contextmanager
def materialize_uploaded_file(file_path: str):
    """Yield a local path for parser libraries, downloading S3 objects to a temp file when needed."""
    if not file_path.startswith("s3://"):
        yield str(PROJECT_ROOT / file_path)
        return

    parsed = urlparse(file_path)
    if parsed.netloc != settings.s3_bucket or not parsed.path.lstrip("/"):
        raise ValueError("The document object storage reference is invalid.")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=Path(parsed.path).suffix, delete=False) as temporary_file:
            temporary_path = Path(temporary_file.name)
            _s3_client().download_fileobj(parsed.netloc, parsed.path.lstrip("/"), temporary_file)
        yield str(temporary_path)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError("The document could not be downloaded from object storage.") from exc
    finally:
        if temporary_path:
            temporary_path.unlink(missing_ok=True)


def check_storage_ready() -> bool:
    if settings.storage_backend.lower() == "local":
        try:
            STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
            return STORAGE_ROOT.is_dir()
        except OSError:
            return False
    if settings.storage_backend.lower() != "s3" or not settings.s3_bucket:
        return False
    try:
        _s3_client().head_bucket(Bucket=settings.s3_bucket)
        return True
    except (BotoCoreError, ClientError):
        return False
