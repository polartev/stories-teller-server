from fastapi import FastAPI, WebSocket, UploadFile, File, Body, Form
from fastapi.responses import JSONResponse, FileResponse
import shutil
import json

from app.base_paths import *
from app.server_messages import *
import app.websocket_connections as ws

app = FastAPI()

# WebSocket connection for admin
@app.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    
    await websocket.accept()
    ws.admin_connection = websocket
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        print(f"WebSocket disconnected: {e}")
    finally:
        ws.admin_connection = None

# WebSocket connection for users
@app.websocket("/ws/user/{user_id}")
async def websocket_user(websocket: WebSocket, user_id: str):
    await websocket.accept()
    ws.user_connections[user_id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from user {user_id}: {data}")
    except Exception as e:
        print(f"User {user_id} disconnected: {e}")
    finally:
        ws.user_connections.pop(user_id, None)

# Upload file endpoint
@app.post("/upload", response_model=Message)
async def post_file(
    file: UploadFile = File(...), 
    user_id: str = "anonymous",
    story: str = Form(""),
    language: str = Form("ua")
):

    filepath = UPLOAD_DIR / file.filename
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    if not QUEUE_FILE.exists():
        QUEUE_FILE.write_text("[]")

    queue = json.loads(QUEUE_FILE.read_text())
    queue.append({
        "filename": file.filename,
        "user_id": user_id,
        "language": language,
        "status": "pending",
        "description": story
    })
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))

    await ws.message_admin(Message(
        type="task",
        payload=BasePayload(
            action="load_file",
            data={"filename": file.filename, "user_id": user_id, "language": language}
        ),
        meta={"timestamp": datetime.utcnow().isoformat() + "Z"}
    ))

    return Message(
        type="success",
        payload=BasePayload(
            action="file_uploaded",
            data={"filename": file.filename, "user_id": user_id}
        ),
        meta={"timestamp": datetime.utcnow().isoformat() + "Z"}
    )

# Get file by filename
@app.get("/uploads/{filename}")
async def get_file(filename: str):

    filepath = UPLOAD_DIR / filename
    if filepath.exists():
        return FileResponse(filepath)
    else:
        return JSONResponse(content={"error": "File not found"}, status_code=404)

@app.post("/describe", response_model=Message)
async def post_description(message: Message):
    
    if message.type == "info" and message.payload.action == "description_is_ready":
        data = message.payload.data
        user_id = data.get("user_id")
        filename = data.get("filename")
        description = data.get("description")
        
        queue = json.loads(QUEUE_FILE.read_text())
        for item in queue:
            if item["filename"] == filename:
                item.update(description=description, status="completed")
                break
        QUEUE_FILE.write_text(json.dumps(queue, indent=2))

        await ws.message_user(user_id, Message(
            type="task",
            payload=BasePayload(
                action="load_description",
                data={"user_id": user_id, "filename": filename}
            ),
            meta={"timestamp": datetime.utcnow().isoformat() + "Z"}
        ))

        return Message(
            type="success",
            payload=BasePayload(
                action="description_received",
                data={"filename": filename, "description": description}
            ),
            meta={"timestamp": datetime.utcnow().isoformat() + "Z"}
        )

    return Message(
        type="error",
        payload=BasePayload(
            action="description_error",
            data={"error": "Invalid message format"}
        ),
        meta={"timestamp": datetime.utcnow().isoformat() + "Z"}
    )

@app.get("/descriptions/{filename}")
async def get_description(filename: str, user_id: str = "anonymous"):

    description = None

    queue = json.loads(QUEUE_FILE.read_text())
    for item in queue:
        if item["filename"] == filename and "description" in item:
            if item["user_id"] == user_id:
                description = item["description"]
            break
    
    filepath = UPLOAD_DIR / filename

    if filepath.exists():
        try:
            filepath.unlink()
        except Exception as e:
            return JSONResponse(content={"error": f"Failed to delete file: {str(e)}"}, status_code=500)

    if description is None or description == "":
        return JSONResponse(content={"error": "Description not found"}, status_code=404)

    return JSONResponse(content={"description": description})