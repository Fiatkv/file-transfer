from fastapi import FastAPI, File, UploadFile, HTTPException, status, Response, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from utils.constants import PORT, DEFAULT_SENDER
from utils.websocket import ConnectionManager
from utils.storage import (list_shared_files, save_upload_file, get_base_path, delete_shared_file, get_shared_text_history,
                           add_shared_text, clear_shared_text_history, delete_shared_text)
from utils.network import get_local_ip, gen_qr_bytes
from utils.schemas import TextPayload

app = FastAPI()
manager = ConnectionManager()

app.mount("/static", StaticFiles(directory="static"), name="static")

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
async def read_text_history() -> dict:
    """Gets the text history."""
    return {"history": get_shared_text_history()}

@app.post("/text")
async def create_text(payload: TextPayload, request: Request) -> dict:
    """Adds a text snippet."""
    if not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="text cannot be empty")

    client_ip = request.client.host if request.client else "Local"
    sender_name = payload.sender if payload.sender != DEFAULT_SENDER else client_ip

    add_shared_text(payload.text, sender_name)
    await manager.broadcast("text_added")
    return {"status": "success"}

@app.delete("/text")
async def clear_text_history() -> dict:
    """Clears all shared text history."""
    clear_shared_text_history()
    await manager.broadcast("text_deleted")
    return {"status": "success"}

@app.delete("/text/{text_id}")
async def remove_text(text_id: str) -> dict:
    """Deletes a text entry."""
    if not delete_shared_text(text_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="entry not found")

    await manager.broadcast("text_deleted")
    return {"status": "success"}