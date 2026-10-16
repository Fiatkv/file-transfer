from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
import shutil
from constants import UPLOAD_DIR_PATH

app = FastAPI()

UPLOAD_DIR = Path(UPLOAD_DIR_PATH)
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
def home() -> dict:
    return {"Hello": "World"}

@app.get("/files")
async def list_files() -> dict:
    files = [file.name for file in UPLOAD_DIR.iterdir() if file.is_file()]
    return {"files": files}

@app.post("/files")
async def upload_file(file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no file provided")

    base_filename = Path(file.filename).name
    destination = UPLOAD_DIR / base_filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": base_filename,
        "content_type": file.content_type,
        "status": "file uploaded successfully"
    }

@app.get("/files/{filename}")
async def download_file(filename: str) -> FileResponse:
    base_filename = Path(filename).name
    file_path = UPLOAD_DIR / base_filename

    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"file {filename} not found")

    return FileResponse(path=file_path, filename=base_filename)