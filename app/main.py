from fastapi import FastAPI, WebSocket, UploadFile, File, Body
from fastapi.responses import JSONResponse, FileResponse
import shutil
import json
from pathlib import Path
from typing import List, Optional, Dict

from pydantic import BaseModel

class DescriptionRequest(BaseModel):
    filename: str
    description: str

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

QUEUE_FILE = BASE_DIR / "queue.json"
if not QUEUE_FILE.exists():
    QUEUE_FILE.write_text("[]")

admin_connection: Optional[WebSocket] = None
user_connections: Dict[str, WebSocket] = {}

# WebSocket connection for admin
@app.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    global admin_connection
    await websocket.accept()
    admin_connection = websocket
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        print(f"WebSocket disconnected: {e}")
    finally:
        admin_connection = None

# WebSocket connection for users
@app.websocket("/ws/user/{user_id}")
async def websocket_user(websocket: WebSocket, user_id: str):
    await websocket.accept()
    user_connections[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from user {user_id}: {data}")
    except Exception as e:
        print(f"User {user_id} disconnected: {e}")
    finally:
        user_connections.pop(user_id, None)

# Upload file endpoint
@app.post("/upload")
async def post_file(file: UploadFile = File(...), user_id: str = "anonymous"):
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

    if admin_connection:
        await admin_connection.send_text(f"new_task:{file.filename}")
            
    return JSONResponse(content={"status": "image received", "filename": file.filename})

# Get file by filename
@app.get("/uploads/{filename}")
async def get_file(filename: str):
    filepath = UPLOAD_DIR / filename
    if filepath.exists():
        return FileResponse(filepath)
    else:
        return JSONResponse(content={"error": "File not found"}, status_code=404)

@app.post("/describe")
async def post_description(data: DescriptionRequest):
    user_id = data.filename.split("_")[0]
    
    queue = json.loads(QUEUE_FILE.read_text())
    for item in queue:
        if item["filename"] == data.filename:
            item["description"] = data.description
            item["status"] = "completed"
            break
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))

    if user_id in user_connections:
        await user_connections[user_id].send_text(f"new_description:{data.description}")

    return JSONResponse(content={"description": data.description})

# @app.get("/descriptions/{filename}")
# async def get_description(filename: str):
#     description = None

#     queue = json.loads(QUEUE_FILE.read_text())
#     for item in queue:
#         if item["filename"] == filename and "description" in item and item["status"] == "completed":
#             description = item["description"]
#             break
    
#     if description is None:
#         return JSONResponse(content={"error": "Description not found"}, status_code=404)

#     return JSONResponse(content={"description": description})