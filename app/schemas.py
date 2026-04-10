from typing import Any, Literal
from pydantic import BaseModel, Field


class ApiMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ApiMessage]
    model: str = "shopai-auto"
    stream: bool = False

    device_id: str = Field(..., min_length=1, max_length=128)
    location_id: str = Field(..., min_length=1, max_length=128)
    language_code: str = Field(..., min_length=2, max_length=16)
    session_id: str = Field(..., min_length=1, max_length=128)
    is_new_session: bool = False
    is_staff_call: bool = False
    question_level: Literal["EASY", "MEDIUM", "HARD"] = "EASY"
    timestamp: int = Field(..., ge=0)
    metadata: dict[str, str] = Field(default_factory=dict)


class ChatChoice(BaseModel):
    message: ApiMessage
    finish_reason: Literal["stop", "length", "content_filter"] = "stop"


class ChatResponse(BaseModel):
    id: str = ""
    choices: list[ChatChoice] = Field(default_factory=list)
    model_used: str = ""
    session_id: str = ""
    requires_staff: bool = False
    answer_source: Literal[
        "structured",
        "rag",
        "fast_llm",
        "deep_llm",
        "safe_fallback",
    ] = "structured"
    confidence: float | None = None
    handoff_reason: str | None = None


class StaffCallRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=512)
    device_id: str = Field(..., min_length=1, max_length=128)
    location_id: str = Field(..., min_length=1, max_length=128)
    timestamp: int = Field(..., ge=0)
    trigger_text: str = Field(default="", max_length=2000)
    session_id: str = Field(default="", max_length=128)


class StaffCallResponse(BaseModel):
    accepted: bool
    message: str = ""


class HealthResponse(BaseModel):
    status: str
    service: str


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
