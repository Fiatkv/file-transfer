import shutil
import json
import uuid
from pathlib import Path
from fastapi import UploadFile
from datetime import datetime


from utils.constants import (DATA_DIR_PATH, UPLOAD_DIR_PATH, SHARED_TEXT_FILENAME)

UPLOAD_DIR = Path(UPLOAD_DIR_PATH)
UPLOAD_DIR.mkdir(exist_ok=True)

DATA_DIR_PATH = Path(DATA_DIR_PATH)
DATA_DIR_PATH.mkdir(exist_ok=True)

SHARED_TEXT_FILE = DATA_DIR_PATH / SHARED_TEXT_FILENAME

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

def get_shared_text_history() -> list[dict]:
    """Reads all shared text entries from JSON storage."""
    if SHARED_TEXT_FILE.exists():
        try:
            return json.loads(SHARED_TEXT_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []

def add_shared_text(text: str) -> dict:
    """Appends a new text snippet to history, capping the list at 20 items"""
    history = get_shared_text_history()

    new_entry = {
        "id": str(uuid.uuid4())[:8],
        "text": text,
        "timestamp": datetime.now().strftime("%H:%M"),
    }

    history.insert(0, new_entry)
    history = history[:20]

    SHARED_TEXT_FILE.write_text(
        json.dumps(history, indent=2),
        encoding="utf-8"
    )
    return new_entry

def clear_shared_text_history() -> bool:
    """Clears all shared text entries from storage."""
    SHARED_TEXT_FILE.write_text("[]", encoding="utf-8")
    return True

def delete_shared_text(text_id: str) -> bool:
    """Deletes a specific text entry by ID."""
    history = get_shared_text_history()
    filtered_history = [item for item in history if item["id"] != text_id]

    if len(filtered_history) == len(history):
        return False

    SHARED_TEXT_FILE.write_text(
        json.dumps(filtered_history, indent=2),
        encoding="utf-8"
    )
    return True
