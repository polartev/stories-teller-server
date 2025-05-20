from typing import Literal, Optional, Union, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

MessageType = Literal["info", "task", "error", "success"]

class BasePayload(BaseModel):
    action: str
    data: Dict[str, Any] = Field(default_factory=dict)

class Message(BaseModel):
    type: MessageType
    payload: BasePayload
    meta: Optional[Dict[str, Any]] = None