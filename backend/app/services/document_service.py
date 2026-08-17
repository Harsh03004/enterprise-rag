from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


PROJECT_ROOT = Path(__file__).resolve().parents[3]
STORAGE_ROOT = PROJECT_ROOT / "storage"


async def save_uploaded_file(
    file: UploadFile,
    user_id: int,
) -> str:
    storage_id = uuid4()

    user_directory = (
        STORAGE_ROOT
        / "users"
        / str(user_id)
        / str(storage_id)
    )

    user_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = user_directory / file.filename

    contents = await file.read()

    file_path.write_bytes(contents)

    return str(file_path.relative_to(PROJECT_ROOT))