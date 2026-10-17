from fastapi import FastAPI, File, UploadFile, HTTPException, status, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from utils.constants import PORT
from utils.websocket import ConnectionManager
from utils.storage import list_shared_files, save_upload_file, get_base_path, delete_shared_file, get_shared_text, set_shared_text
from utils.network import get_local_ip, gen_qr_bytes
from utils.schemas import TextPayload

app = FastAPI()
manager = ConnectionManager()

@app.get("/")
def read_index() -> dict:
    """Home page."""
    return FileResponse("index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Websocket Endpoint."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/qr")
async def get_qr() -> Response:
    """Gets the app QR code."""
    local_ip = get_local_ip()
    url = f"http://{local_ip}:{PORT}"
    qr_bytes = gen_qr_bytes(url)

    return Response(content=qr_bytes, media_type="image/png")

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
    await manager.broadcast("file_uploaded")
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
    await manager.broadcast("file_deleted")
    return {"filename": filename, "status": "deleted successfully"}

@app.get("/text")
async def read_text() -> dict:
    return {"text": get_shared_text()}

@app.post("/text")
async def update_text(payload: TextPayload) -> dict:
    set_shared_text(payload.text)
    await manager.broadcast("text_updated")
    return {"status": "success"}