from fastapi import FastAPI, Form, HTTPException, Request, Response, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from utils.constants import DEFAULT_SENDER, PORT
from utils.network import gen_qr_bytes, get_local_ip
from utils.schemas import TextPayload
from utils.storage import (add_shared_text, clear_shared_text_history, delete_shared_file, delete_shared_text, get_base_path,
                           get_shared_text_history, list_shared_files_info, save_upload_file)
from utils.websocket import ConnectionManager

app = FastAPI()
manager = ConnectionManager()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_index() -> FileResponse:
    return FileResponse("index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/qr")
async def get_qr() -> Response:
    local_ip = get_local_ip()
    url = f"http://{local_ip}:{PORT}"
    return Response(content=gen_qr_bytes(url), media_type="image/png")

@app.get("/files")
async def list_files() -> dict:
    return {"files": list_shared_files_info()}

@app.post("/files")
async def upload_file(file: UploadFile, sender: str = Form(DEFAULT_SENDER)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file provided")

    saved_filename = save_upload_file(file, sender)
    await manager.broadcast("file_uploaded")
    return {"filename": saved_filename, "status": "uploaded successfully"}

@app.get("/files/{filename}")
async def download_file(filename: str) -> FileResponse:
    file_path = get_base_path(filename)
    if not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    return FileResponse(path=file_path, filename=file_path.name)

@app.delete("/files/{filename}")
async def delete_file(filename: str) -> dict:
    if not delete_shared_file(filename):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    await manager.broadcast("file_deleted")
    return {"filename": filename, "status": "deleted successfully"}

@app.get("/text")
async def read_text_history() -> dict:
    return {"history": get_shared_text_history()}

@app.post("/text")
async def create_text(payload: TextPayload, request: Request) -> dict:
    if not payload.text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text cannot be empty")

    client_ip = request.client.host if request.client else "Local"
    sender_name = payload.sender if payload.sender != DEFAULT_SENDER else client_ip

    add_shared_text(payload.text, sender_name)
    await manager.broadcast("text_added")
    return {"status": "success"}

@app.delete("/text")
async def clear_text_history() -> dict:
    clear_shared_text_history()
    await manager.broadcast("text_deleted")
    return {"status": "success"}

@app.delete("/text/{text_id}")
async def remove_text(text_id: str) -> dict:
    if not delete_shared_text(text_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")

    await manager.broadcast("text_deleted")
    return {"status": "success"}