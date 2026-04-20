import logging
import time
import uuid
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import QuestionLog
from app.schemas import ApiMessage, ChatChoice, ChatRequest, ChatResponse
from app.services.llm import LlmDispatcher
from app.services.policy import PolicyService
from app.services.rag import RagService
from app.services.session import SessionService
from app.services.structured import StructuredSearchService

logger = logging.getLogger(__name__)

Route = Literal["structured", "rag", "fast_llm", "deep_llm", "safe_fallback", "staff_handoff"]

_STRUCTURED_KEYWORDS = [
    "営業時間", "何時まで", "何時から", "開店", "閉店",
    "トイレ", "お手洗い", "化粧室",
    "レジ", "会計", "お支払い",
    "売り場", "どこ", "場所", "フロア", "階",
    "在庫",
]
_RAG_KEYWORDS = ["FAQ", "返品", "交換", "ルール", "説明", "注意事項", "ポリシー", "規約"]
_STAFF_KEYWORDS = ["スタッフ", "店員", "呼んで", "来て"]

_SAFE_FALLBACK_MESSAGES = [
    "詳しいご案内は担当スタッフにご相談ください。",
    "そのご質問にはお答えできません。スタッフにおつなぎします。",
]

_SYSTEM_PROMPT = (
    "あなたは店舗に設置されたAIアシスタントです。"
    "お客様の質問に丁寧かつ簡潔に日本語で回答してください。"
    "わからないことは「スタッフにお尋ねください」と案内してください。"
)


class ChatOrchestrator:
    def __init__(
        self,
        policy: PolicyService,
        session_svc: SessionService,
        structured: StructuredSearchService,
        rag: RagService,
        llm: LlmDispatcher,
    ) -> None:
        self._policy = policy
        self._session = session_svc
        self._structured = structured
        self._rag = rag
        self._llm = llm

    async def process(self, db: AsyncSession, request: ChatRequest) -> ChatResponse:
        start = time.monotonic()

        question = self._extract_latest_user_message(request.messages)
        if question is None:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_ARGUMENT", "message": "No user message found"},
            )

        await self._session.ensure_session(
            db,
            session_id=request.session_id,
            device_id=request.device_id,
            location_id=request.location_id,
            language_code=request.language_code,
            is_new_session=request.is_new_session,
        )

        pre = self._policy.precheck(question)
        if pre.decision == "staff_handoff":
            resp = self._compose_staff_handoff(request)
            await self._log(db, request, question, "staff_handoff", resp, start)
            return resp
        if pre.decision == "safe_fallback":
            resp = self._compose_safe_fallback(request, pre.reason)
            await self._log(db, request, question, "safe_fallback", resp, start)
            return resp

        route = self._determine_route(question, request)
        resp = await self._execute(db, route, question, request)

        final = self._policy.final_check(resp.choices[0].message.content)
        if final.decision != "allow":
            resp = self._compose_safe_fallback(request, final.reason)
            route = "safe_fallback"

        await self._log(db, request, question, route, resp, start)
        return resp

    def _extract_latest_user_message(self, messages: list[ApiMessage]) -> str | None:
        for msg in reversed(messages):
            if msg.role == "user":
                text = msg.content.strip()
                if text:
                    return text
        return None

    def _determine_route(self, question: str, request: ChatRequest) -> Route:
        if request.is_staff_call:
            return "staff_handoff"
        for kw in _STAFF_KEYWORDS:
            if kw in question:
                return "staff_handoff"

        for kw in _STRUCTURED_KEYWORDS:
            if kw in question:
                return "structured"

        for kw in _RAG_KEYWORDS:
            if kw in question:
                return "rag"
        if request.question_level == "MEDIUM":
            return "rag"

        if request.question_level == "HARD":
            return "deep_llm"

        return "fast_llm"

    async def _execute(
        self,
        db: AsyncSession,
        route: Route,
        question: str,
        request: ChatRequest,
    ) -> ChatResponse:
        if route == "staff_handoff":
            return self._compose_staff_handoff(request)

        if route == "structured":
            result = await self._structured.search(
                db, question, request.location_id, request.language_code
            )
            if result:
                return self._compose(
                    request,
                    content=result.answer_text,
                    model_used=result.model_used,
                    answer_source=result.answer_source,
                    confidence=result.confidence,
                )

        if route in ("rag", "structured"):
            rag_result = await self._rag.retrieve_and_answer(
                db, question, request.location_id, request.language_code
            )
            if rag_result:
                return self._compose(
                    request,
                    content=rag_result.answer_text,
                    model_used=rag_result.model_used,
                    answer_source=rag_result.answer_source,
                    confidence=rag_result.confidence,
                )
            return await self._call_llm(request, question, deep=False)

        if route == "deep_llm":
            return await self._call_llm(request, question, deep=True)

        return await self._call_llm(request, question, deep=False)

    async def _call_llm(
        self, request: ChatRequest, question: str, *, deep: bool
    ) -> ChatResponse:
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
        try:
            if deep:
                answer = await self._llm.generate_deep(messages)
                model_used = "deep-local-model"
                answer_source = "deep_llm"
            else:
                answer = await self._llm.generate_fast(messages)
                model_used = "fast-local-model"
                answer_source = "fast_llm"
        except Exception:
            logger.exception("LLM call failed, returning safe fallback")
            return self._compose_safe_fallback(request, "llm_unavailable")

        return self._compose(
            request,
            content=answer,
            model_used=model_used,
            answer_source=answer_source,
            confidence=0.75 if deep else 0.72,
        )

    def _compose(
        self,
        request: ChatRequest,
        *,
        content: str,
        model_used: str,
        answer_source: str,
        confidence: float | None = None,
        requires_staff: bool = False,
        handoff_reason: str | None = None,
    ) -> ChatResponse:
        return ChatResponse(
            id=f"chat_{uuid.uuid4().hex[:12]}",
            choices=[
                ChatChoice(
                    message=ApiMessage(role="assistant", content=content),
                    finish_reason="stop",
                )
            ],
            model_used=model_used,
            session_id=request.session_id,
            requires_staff=requires_staff,
            answer_source=answer_source,
            confidence=confidence,
            handoff_reason=handoff_reason,
        )

    def _compose_staff_handoff(self, request: ChatRequest) -> ChatResponse:
        return self._compose(
            request,
            content="担当スタッフをお呼びします。少々お待ちください。",
            model_used="safe_fallback",
            answer_source="safe_fallback",
            confidence=0.96,
            requires_staff=True,
            handoff_reason="customer_requested_staff",
        )

    def _compose_safe_fallback(
        self, request: ChatRequest, reason: str
    ) -> ChatResponse:
        return self._compose(
            request,
            content="詳しいご案内は担当スタッフにご相談ください。",
            model_used="safe_fallback",
            answer_source="safe_fallback",
            confidence=1.0,
            requires_staff=True,
            handoff_reason=reason,
        )

    async def _log(
        self,
        db: AsyncSession,
        request: ChatRequest,
        question: str,
        route: str,
        response: ChatResponse,
        start: float,
    ) -> None:
        latency_ms = int((time.monotonic() - start) * 1000)
        answer_text = ""
        if response.choices:
            answer_text = response.choices[0].message.content

        log = QuestionLog(
            question_id=uuid.uuid4().hex,
            session_id=request.session_id,
            device_id=request.device_id,
            location_id=request.location_id,
            question_text=question,
            normalized_text=question.lower(),
            intent=route,
            route=route,
            answer_text=answer_text,
            answer_source=response.answer_source,
            model_used=response.model_used,
            confidence=response.confidence,
            requires_staff=response.requires_staff,
            handoff_reason=response.handoff_reason,
            latency_ms=latency_ms,
        )
        db.add(log)
