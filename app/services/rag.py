import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DocumentChunk
from app.services.llm import LlmDispatcher

logger = logging.getLogger(__name__)

_RAG_KEYWORDS = ["返品", "交換", "ルール", "説明", "注意事項", "FAQ", "ポリシー", "規約"]


@dataclass
class RagResult:
    answer_text: str
    answer_source: str = "rag"
    model_used: str = "rag+fast_llm"
    confidence: float = 0.80


class RagService:
    def __init__(self, llm: LlmDispatcher) -> None:
        self._llm = llm

    def is_rag_candidate(self, question: str) -> bool:
        return any(kw in question for kw in _RAG_KEYWORDS)

    async def retrieve_and_answer(
        self,
        db: AsyncSession,
        question: str,
        location_id: str,
        language_code: str,
    ) -> RagResult | None:
        chunks = await self._retrieve_chunks(db, question, location_id)
        if not chunks:
            return None

        context = "\n---\n".join(c.content for c in chunks)
        messages = [
            {
                "role": "system",
                "content": (
                    "あなたは店舗アシスタントです。以下の参考情報のみに基づいて、"
                    "お客様の質問に正確に回答してください。"
                    "参考情報に含まれない内容は推測せず、"
                    "「詳しくはスタッフにお尋ねください」と案内してください。"
                ),
            },
            {
                "role": "user",
                "content": f"参考情報:\n{context}\n\n質問: {question}",
            },
        ]

        try:
            answer = await self._llm.generate_fast(messages)
            return RagResult(answer_text=answer)
        except Exception:
            logger.exception("RAG LLM call failed")
            return None

    async def _retrieve_chunks(
        self,
        db: AsyncSession,
        question: str,
        location_id: str,
        top_k: int = 3,
    ) -> list[DocumentChunk]:
        result = await db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.location_id == location_id)
            .order_by(DocumentChunk.chunk_index)
        )
        all_chunks = result.scalars().all()

        scored: list[tuple[int, DocumentChunk]] = []
        for chunk in all_chunks:
            score = sum(1 for kw in _RAG_KEYWORDS if kw in chunk.content)
            q_words = [w for w in question if len(w) > 1]
            score += sum(1 for w in q_words if w in chunk.content)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
