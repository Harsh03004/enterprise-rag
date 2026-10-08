from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STORAGE_ROOT = PROJECT_ROOT / "storage"
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

    resolved_path = (PROJECT_ROOT / file_path).resolve()
    storage_root = STORAGE_ROOT.resolve()
    try:
        resolved_path.relative_to(storage_root)
    except ValueError:
        return

    resolved_path.unlink(missing_ok=True)
