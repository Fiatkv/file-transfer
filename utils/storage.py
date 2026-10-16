import shutil
from pathlib import Path
from fastapi import UploadFile
from utils.constants import UPLOAD_DIR_PATH

UPLOAD_DIR = Path(UPLOAD_DIR_PATH)
UPLOAD_DIR.mkdir(exist_ok=True)

def get_base_path(filename: str) -> Path:
    """Strips directory traversal sequences and returns an absolute file target path."""
    base_name = Path(filename).name
    return UPLOAD_DIR / base_name

def list_shared_files() -> list[str]:
    """Returns a list of all filenames stored in the shared files directory."""
    return [file.name for file in UPLOAD_DIR.iterdir() if file.is_file()]

def save_upload_file(file: UploadFile) -> str:
    """Streams an incoming UploadFile to the storage directory in chunks."""
    target_path = get_base_path(file.filename)
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return target_path.name

def delete_shared_file(filename: str) -> bool:
    """Deletes a file from the shared files directory (if it exists)."""
    file_path = get_base_path(filename)
    if file_path.exists() and file_path.is_file():
        file_path.unlink()
        return True
    return False