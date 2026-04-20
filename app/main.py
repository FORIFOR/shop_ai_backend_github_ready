import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import ALLOWED_ORIGINS, APP_NAME, APP_VERSION
from app.database import get_db, init_db
from app.orchestrator import ChatOrchestrator
from app.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    StaffCallRequest,
    StaffCallResponse,
)
from app.services.llm import LlmDispatcher
from app.services.policy import PolicyService
from app.services.rag import RagService
from app.services.session import SessionService
from app.services.staff import StaffCallService
from app.services.structured import StructuredSearchService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

_llm = LlmDispatcher()
_policy = PolicyService()
_session_svc = SessionService()
_structured = StructuredSearchService()
_rag = RagService(_llm)
_staff_svc = StaffCallService()
_orchestrator = ChatOrchestrator(
    policy=_policy,
    session_svc=_session_svc,
    structured=_structured,
    rag=_rag,
    llm=_llm,
)


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("Initializing database tables...")
    await init_db()
    logger.info("Database ready.")

    from app.database import async_session
    from app.seed import seed_if_empty
    async with async_session() as db:
        await seed_if_empty(db)
        await db.commit()

    yield

    await _llm.close()


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="店舗設置型 AI アシスタント バックエンド API",
    lifespan=lifespan,
)

origins = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_device_id(x_device_id: str | None) -> str:
    if not x_device_id:
        raise HTTPException(status_code=401, detail="X-Device-ID is required")
    return x_device_id


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="shop-ai-backend")


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
    db: AsyncSession = Depends(get_db),
):
    require_device_id(x_device_id)
    response = await _orchestrator.process(db, request)
    await db.commit()
    return response


@app.post("/api/v1/staff-call", response_model=StaffCallResponse, status_code=202)
async def staff_call(
    request: StaffCallRequest,
    x_device_id: str | None = Header(default=None, alias="X-Device-ID"),
    db: AsyncSession = Depends(get_db),
):
    require_device_id(x_device_id)
    await _staff_svc.record(
        db,
        session_id=request.session_id,
        device_id=request.device_id,
        location_id=request.location_id,
        reason=request.reason,
        trigger_text=request.trigger_text,
    )
    await db.commit()
    logger.info("Staff call accepted: location=%s", request.location_id)
    return StaffCallResponse(
        accepted=True,
        message=f"スタッフ通知を受け付けました。location={request.location_id}",
    )
