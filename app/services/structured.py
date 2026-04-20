from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FaqStructured, Inventory, Location, Product


@dataclass
class StructuredResult:
    answer_text: str
    answer_source: str = "structured"
    model_used: str = "structured"
    confidence: float = 0.99


_KEYWORD_GROUPS: list[tuple[list[str], str]] = [
    (["営業時間", "何時まで", "何時から", "開店", "閉店"], "hours"),
    (["トイレ", "お手洗い", "化粧室"], "restroom"),
    (["レジ", "会計", "お支払い", "支払い"], "register"),
    (["売り場", "どこ", "場所", "フロア", "階"], "location"),
    (["在庫", "ある", "残り", "入荷"], "inventory"),
]


class StructuredSearchService:
    def detect_intent(self, question: str) -> str | None:
        for keywords, intent in _KEYWORD_GROUPS:
            for kw in keywords:
                if kw in question:
                    return intent
        return None

    async def search(
        self,
        db: AsyncSession,
        question: str,
        location_id: str,
        language_code: str,
    ) -> StructuredResult | None:
        faq = await self._search_faq(db, question, location_id)
        if faq:
            return StructuredResult(answer_text=faq)

        intent = self.detect_intent(question)
        if intent == "hours":
            return await self._search_hours(db, location_id)
        if intent == "restroom":
            return await self._search_location_type(db, location_id, "restroom")
        if intent == "register":
            return await self._search_location_type(db, location_id, "register")
        if intent == "location":
            return await self._search_product_location(db, question, location_id)
        if intent == "inventory":
            return await self._search_inventory(db, question, location_id)

        return None

    async def _search_faq(
        self, db: AsyncSession, question: str, location_id: str
    ) -> str | None:
        result = await db.execute(
            select(FaqStructured).where(FaqStructured.location_id == location_id)
        )
        faqs = result.scalars().all()
        for faq in faqs:
            if any(tag in question for tag in (faq.tags_json or [])):
                return faq.answer
            if any(word in question for word in faq.question.split()):
                return faq.answer
        return None

    async def _search_hours(
        self, db: AsyncSession, location_id: str
    ) -> StructuredResult | None:
        result = await db.execute(
            select(Location).where(
                Location.location_id == location_id,
                Location.type == "store",
            )
        )
        loc = result.scalar_one_or_none()
        if loc and loc.guidance_text:
            return StructuredResult(answer_text=loc.guidance_text)
        result = await db.execute(
            select(FaqStructured).where(
                FaqStructured.location_id == location_id,
                FaqStructured.category == "hours",
            )
        )
        faq = result.scalar_one_or_none()
        if faq:
            return StructuredResult(answer_text=faq.answer)
        return None

    async def _search_location_type(
        self, db: AsyncSession, location_id: str, loc_type: str
    ) -> StructuredResult | None:
        result = await db.execute(
            select(Location).where(
                Location.location_id == location_id,
                Location.type == loc_type,
            )
        )
        loc = result.scalar_one_or_none()
        if loc:
            return StructuredResult(answer_text=loc.guidance_text)
        return None

    async def _search_product_location(
        self, db: AsyncSession, question: str, location_id: str
    ) -> StructuredResult | None:
        result = await db.execute(
            select(Product).where(Product.location_id == location_id)
        )
        products = result.scalars().all()
        for p in products:
            names = [p.name] + (p.aliases_json or [])
            if any(n in question for n in names):
                text = f"{p.name}は{p.shelf_floor} {p.shelf_zone}にございます。"
                return StructuredResult(answer_text=text)
        return None

    async def _search_inventory(
        self, db: AsyncSession, question: str, location_id: str
    ) -> StructuredResult | None:
        result = await db.execute(
            select(Product).where(Product.location_id == location_id)
        )
        products = result.scalars().all()
        for p in products:
            names = [p.name] + (p.aliases_json or [])
            if any(n in question for n in names):
                inv_result = await db.execute(
                    select(Inventory).where(Inventory.sku == p.sku)
                )
                inv = inv_result.scalar_one_or_none()
                if inv:
                    if inv.stock_status == "in_stock" and inv.quantity > 0:
                        text = f"{p.name}は在庫がございます（残り{inv.quantity}点）。"
                    else:
                        text = f"{p.name}は現在在庫切れとなっております。"
                    return StructuredResult(answer_text=text)
        return None
