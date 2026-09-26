from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VeraRequest(BaseModel):
    trigger_id: str


class Message(BaseModel):
    body: str
    cta: Optional[str] = None
    send_as: str


class VeraResponse(BaseModel):
    should_act: bool
    status: str

    audience: Optional[str] = None
    action: Optional[str] = None
    opportunity: Optional[str] = None

    priority: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    message: Optional[Message] = None

    evidence: Dict[str, Any] = {}
    reasons: List[str] = []

    suppression_key: Optional[str] = None