import os
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import (
    ApiMessage,
    ChatChoice,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    StaffCallRequest,
    StaffCallResponse,
)

APP_NAME = os.getenv("APP_NAME", "Shop AI Staff Backend API")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "GitHub から clone / download 後すぐに起動できる、"
        "Android フロント接続用のモック API です。"
    ),
)

origins = [origin.strip() for origin in ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_device_id(x_device_id: str | None):
    if not x_device_id:
        raise HTTPException(status_code=401, detail="X-Device-ID is required")


def latest_user_message(messages: list[ApiMessage]) -> str:
    for msg in reversed(messages):
        if msg.role == "user":
            return msg.content.strip()
    return ""


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="shop-ai-backend-mock")


@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "server_time": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_device_id: str | None = Header(default=None, alias="X-Device-ID"),
):
    require_device_id(x_device_id)
    latest = latest_user_message(request.messages)

    if request.is_staff_call or any(word in latest for word in ["スタッフ", "店員", "呼んで", "来て"]):
        return ChatResponse(
            id=f"chat_{uuid.uuid4().hex[:12]}",
            choices=[
                ChatChoice(
                    message=ApiMessage(
                        role="assistant",
                        content="担当スタッフをお呼びします。少々お待ちください。",
                    )
                )
            ],
            model_used="safe_fallback",
            session_id=request.session_id,
            requires_staff=True,
            answer_source="safe_fallback",
            confidence=0.96,
            handoff_reason="customer_requested_staff",
        )

    if any(word in latest for word in ["営業時間", "何時まで", "何時から"]):
        return ChatResponse(
            id=f"chat_{uuid.uuid4().hex[:12]}",
            choices=[
                ChatChoice(
                    message=ApiMessage(
                        role="assistant",
                        content="当店の営業時間は10時から21時までです。",
                    )
                )
            ],
            model_used="structured",
            session_id=request.session_id,
            requires_staff=False,
            answer_source="structured",
            confidence=0.99,
        )

    if any(word in latest for word in ["トイレ", "お手洗い"]):
        return ChatResponse(
            id=f"chat_{uuid.uuid4().hex[:12]}",
            choices=[
                ChatChoice(
                    message=ApiMessage(
                        role="assistant",
                        content="お手洗いは2階、エスカレーター横にございます。",
                    )
                )
            ],
            model_used="structured",
            session_id=request.session_id,
            requires_staff=False,
            answer_source="structured",
            confidence=0.98,
        )

    if request.question_level == "MEDIUM":
        return ChatResponse(
            id=f"chat_{uuid.uuid4().hex[:12]}",
            choices=[
                ChatChoice(
                    message=ApiMessage(
                        role="assistant",
                        content="関連情報を確認しました。こちらの商品は1階中央の売り場にございます。",
                    )
                )
            ],
            model_used="rag-mock",
            session_id=request.session_id,
            requires_staff=False,
            answer_source="rag",
            confidence=0.83,
        )

    if request.question_level == "HARD":
        return ChatResponse(
            id=f"chat_{uuid.uuid4().hex[:12]}",
            choices=[
                ChatChoice(
                    message=ApiMessage(
                        role="assistant",
                        content="内容を確認しました。詳しくご案内できるよう、担当者または詳細モードで対応いたします。",
                    )
                )
            ],
            model_used="deep-mock",
            session_id=request.session_id,
            requires_staff=False,
            answer_source="deep_llm",
            confidence=0.74,
        )

    return ChatResponse(
        id=f"chat_{uuid.uuid4().hex[:12]}",
        choices=[
            ChatChoice(
                message=ApiMessage(
                    role="assistant",
                    content="承知しました。詳しく確認いたしますので、少々お待ちください。",
                )
            )
        ],
        model_used="fast-mock",
        session_id=request.session_id,
        requires_staff=False,
        answer_source="fast_llm",
        confidence=0.72,
    )


@app.post("/api/v1/staff-call", response_model=StaffCallResponse, status_code=202)
async def staff_call(
    request: StaffCallRequest,
    x_device_id: str | None = Header(default=None, alias="X-Device-ID"),
):
    require_device_id(x_device_id)
    return StaffCallResponse(
        accepted=True,
        message=f"スタッフ通知を受け付けました。location={request.location_id}",
    )
