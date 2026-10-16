from fastapi import FastAPI, File, UploadFile, HTTPException, status
from pathlib import Path
import shutil
from constants import UPLOAD_DIR_PATH

app = FastAPI()

UPLOAD_DIR = Path(UPLOAD_DIR_PATH)
UPLOAD_DIR.mkdir(exist_ok=True)

@app.get("/")
def home() -> dict:
    return {"Hello": "World"}

@app.post("/upload")
async def upload_file(file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    filename = Path(file.filename).name
    destination = UPLOAD_DIR / filename

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": filename,
        "content_type": file.content_type,
        "status": "File uploaded successfully"
    }