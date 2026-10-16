from fastapi import FastAPI, File, UploadFile, HTTPException, status, Response
from fastapi.responses import FileResponse

from utils.storage import (list_shared_files, save_upload_file, get_base_path, delete_shared_file)
from utils.network import(get_local_ip, gen_qr_bytes)
from utils.constants import (PORT)

app = FastAPI()

@app.get("/")
def read_index() -> dict:
    """Home page."""
    return FileResponse("index.html")

@app.get("/files")
async def list_files() -> dict:
    """Lists all shared files."""
    return {"files": list_shared_files()}

@app.post("/files")
async def upload_file(file: UploadFile) -> dict:
    """Uploads a file."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no file provided")

    saved_filename = save_upload_file(file)
    return {"filename": saved_filename, "status": "uploaded successfully"}

@app.get("/files/{filename}")
async def download_file(filename: str) -> FileResponse:
    """Downloads a file."""
    file_path = get_base_path(filename)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file not found")

    return FileResponse(path=file_path, filename=file_path.name)

@app.delete("/files/{filename}")
async def delete_file(filename: str) -> dict:
    """Deletes a file."""
    if not delete_shared_file(filename):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file not found")
    return {"filename": filename, "status": "deleted successfully"}

@app.get("/qr")
async def get_qr() -> Response:
    """Gets the app QR code."""
    local_ip = get_local_ip()
    url = f"http://{local_ip}:{PORT}"
    qr_bytes = gen_qr_bytes(url)

    return Response(content=qr_bytes, media_type="image/png")