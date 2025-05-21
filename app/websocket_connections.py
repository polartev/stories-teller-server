from typing import Dict, Optional
from fastapi import WebSocket
from app.server_messages import Message

admin_connection: Optional[WebSocket] = None
user_connections: Dict[str, WebSocket] = {}

async def message_admin(message: Message):
    print(f"Sending message to admin connection: {admin_connection}")
    if admin_connection:
        await admin_connection.send_text(message.model_dump_json())

async def message_user(user_id: str, message: Message):
    print(f"Sending message to user connection {user_id}: {user_connections.get(user_id)}")
    if user_id in user_connections:
        await user_connections[user_id].send_text(message.model_dump_json())