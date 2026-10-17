import json
import shutil
import uuid

from datetime import datetime
from pathlib import Path
from fastapi import UploadFile

from utils.constants import DATA_DIR_PATH, DEFAULT_SENDER, FILES_METADATA_FILENAME, SHARED_TEXT_FILENAME, UPLOAD_DIR_PATH

UPLOAD_DIR = Path(UPLOAD_DIR_PATH)
UPLOAD_DIR.mkdir(exist_ok=True)

DATA_DIR = Path(DATA_DIR_PATH)
DATA_DIR.mkdir(exist_ok=True)

FILES_METADATA_FILE = DATA_DIR / FILES_METADATA_FILENAME
SHARED_TEXT_FILE = DATA_DIR / SHARED_TEXT_FILENAME

def get_base_path(filename: str) -> Path:
    """Strips directory traversal sequences to return a safe file path."""
    return UPLOAD_DIR / Path(filename).name

def get_files_metadata() -> dict[str, dict]:
    if FILES_METADATA_FILE.exists():
        try:
            return json.loads(FILES_METADATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}

def save_files_metadata(metadata: dict[str, dict]) -> None:
    FILES_METADATA_FILE.write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

def list_shared_files_info() -> list[dict]:
    metadata = get_files_metadata()
    files = []

    for file in UPLOAD_DIR.iterdir():
        if file.is_file():
            file_meta = metadata.get(file.name, {})
            files.append(
                {
                    "filename": file.name,
                    "sender": file_meta.get("sender", DEFAULT_SENDER),
                    "timestamp": file_meta.get("timestamp", "--:--"),
                }
            )
    return files

def save_upload_file(file: UploadFile, sender: str = DEFAULT_SENDER) -> str:
    target_path = get_base_path(file.filename)
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    metadata = get_files_metadata()
    metadata[target_path.name] = {
        "sender": sender,
        "timestamp": datetime.now().strftime("%H:%M"),
    }
    save_files_metadata(metadata)

    return target_path.name

def delete_shared_file(filename: str) -> bool:
    file_path = get_base_path(filename)
    if file_path.exists() and file_path.is_file():
        file_path.unlink()

        metadata = get_files_metadata()
        if filename in metadata:
            del metadata[filename]
            save_files_metadata(metadata)

        return True
    return False

def get_shared_text_history() -> list[dict]:
    if SHARED_TEXT_FILE.exists():
        try:
            return json.loads(SHARED_TEXT_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []

def add_shared_text(text: str, sender: str = DEFAULT_SENDER) -> dict:
    history = get_shared_text_history()

    new_entry = {
        "id": str(uuid.uuid4())[:8],
        "text": text,
        "sender": sender,
        "timestamp": datetime.now().strftime("%H:%M"),
    }

    history.insert(0, new_entry)
    history = history[:20]

    SHARED_TEXT_FILE.write_text(
        json.dumps(history, indent=2), encoding="utf-8"
    )
    return new_entry

def clear_shared_text_history() -> bool:
    SHARED_TEXT_FILE.write_text("[]", encoding="utf-8")
    return True

def delete_shared_text(text_id: str) -> bool:
    history = get_shared_text_history()
    filtered_history = [item for item in history if item["id"] != text_id]

    if len(filtered_history) == len(history):
        return False

    SHARED_TEXT_FILE.write_text(
        json.dumps(filtered_history, indent=2), encoding="utf-8"
    )
    return True