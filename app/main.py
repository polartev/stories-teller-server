from fastapi import FastAPI, WebSocket, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
import shutil
import json
from pathlib import Path
from typing import List

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

QUEUE_FILE = BASE_DIR / "queue.json"
if not QUEUE_FILE.exists():
    QUEUE_FILE.write_text("[]")

active_connections: List[WebSocket] = []

# WebSocket connection for admin
@app.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        print(f"WebSocket disconnected: {e}")
    finally:
        active_connections.remove(websocket)

# Upload image endpoint
@app.post("/upload")
async def upload_image(file: UploadFile = File(...), user_id: str = "anonymous"):
    filepath = UPLOAD_DIR / file.filename
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    queue = json.loads(QUEUE_FILE.read_text())
    queue.append({
        "filename": file.filename,
        "user_id": user_id,
        "status": "pending"
    })
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))

    for conn in active_connections:
        try:
            await conn.send_text(f"new_task:{file.filename}")
        except Exception:
            pass 
            
    return JSONResponse(content={"status": "image received", "filename": file.filename})

# Get file by filename
@app.get("/uploads/{filename}")
async def get_file(filename: str):
    filepath = UPLOAD_DIR / filename
    if filepath.exists():
        return FileResponse(filepath)
    else:
        return JSONResponse(content={"error": "File not found"}, status_code=404)

# @app.get("/queue")
# def get_queue():
#     return json.loads(QUEUE_FILE.read_text())

# @app.post("/result")
# def post_result(filename: str, description: str):
#     queue = json.loads(QUEUE_FILE.read_text())
#     for item in queue:
#         if item["filename"] == filename:
#             item["status"] = "done"
#             item["description"] = description
#             break
#     QUEUE_FILE.write_text(json.dumps(queue, indent=2))
#     return {"status": "result saved"}