"""Seed data for structured search and RAG."""
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk, FaqStructured, Inventory, Location, Product

logger = logging.getLogger(__name__)

_DEFAULT_LOCATION_ID = "odaiba-branch"


async def seed_if_empty(db: AsyncSession) -> None:
    result = await db.execute(select(Location).limit(1))
    if result.scalar_one_or_none() is not None:
        logger.info("Seed data already exists, skipping.")
        return

    logger.info("Seeding initial data...")
    await _seed_locations(db)
    await _seed_faq(db)
    await _seed_products(db)
    await _seed_inventories(db)
    await _seed_documents(db)
    logger.info("Seed data inserted.")


async def _seed_locations(db: AsyncSession) -> None:
    entries = [
        Location(
            location_entry_id="loc-store-001",
            location_id=_DEFAULT_LOCATION_ID,
            type="store",
            floor="1F-3F",
            zone="全館",
            display_name="お台場店",
            guidance_text="当店の営業時間は10時から21時までです。",
            aliases_json=["お台場", "本店"],
        ),
        Location(
            location_entry_id="loc-restroom-001",
            location_id=_DEFAULT_LOCATION_ID,
            type="restroom",
            floor="2F",
            zone="エスカレーター横",
            display_name="お手洗い",
            guidance_text="お手洗いは2階、エスカレーター横にございます。",
            aliases_json=["トイレ", "化粧室", "お手洗い"],
        ),
        Location(
            location_entry_id="loc-register-001",
            location_id=_DEFAULT_LOCATION_ID,
            type="register",
            floor="1F",
            zone="正面入口付近",
            display_name="レジ",
            guidance_text="レジは1階正面入口付近にございます。",
            aliases_json=["会計", "お支払い", "キャッシャー"],
        ),
        Location(
            location_entry_id="loc-elevator-001",
            location_id=_DEFAULT_LOCATION_ID,
            type="facility",
            floor="1F",
            zone="北側",
            display_name="エレベーター",
            guidance_text="エレベーターは1階北側にございます。",
            aliases_json=["EV"],
        ),
    ]
    db.add_all(entries)


async def _seed_faq(db: AsyncSession) -> None:
    entries = [
        FaqStructured(
            faq_id="faq-hours-001",
            location_id=_DEFAULT_LOCATION_ID,
            question="営業時間は何時ですか",
            answer="当店の営業時間は10時から21時までです。",
            category="hours",
            tags_json=["営業時間", "何時まで", "何時から", "開店", "閉店"],
        ),
        FaqStructured(
            faq_id="faq-restroom-001",
            location_id=_DEFAULT_LOCATION_ID,
            question="トイレはどこですか",
            answer="お手洗いは2階、エスカレーター横にございます。",
            category="facility",
            tags_json=["トイレ", "お手洗い", "化粧室"],
        ),
        FaqStructured(
            faq_id="faq-register-001",
            location_id=_DEFAULT_LOCATION_ID,
            question="レジはどこですか",
            answer="レジは1階正面入口付近にございます。",
            category="facility",
            tags_json=["レジ", "会計", "お支払い"],
        ),
        FaqStructured(
            faq_id="faq-parking-001",
            location_id=_DEFAULT_LOCATION_ID,
            question="駐車場はありますか",
            answer="地下1階に駐車場がございます。3,000円以上のお買い上げで2時間無料です。",
            category="facility",
            tags_json=["駐車場", "パーキング", "車"],
        ),
        FaqStructured(
            faq_id="faq-wifi-001",
            location_id=_DEFAULT_LOCATION_ID,
            question="Wi-Fiは使えますか",
            answer="店内で無料Wi-Fiをご利用いただけます。SSID: ShopAI-Guest",
            category="service",
            tags_json=["Wi-Fi", "WiFi", "ワイファイ", "インターネット"],
        ),
    ]
    db.add_all(entries)


async def _seed_products(db: AsyncSession) -> None:
    entries = [
        Product(
            sku="SKU-001",
            location_id=_DEFAULT_LOCATION_ID,
            name="ワイヤレスイヤホン",
            category="家電",
            attributes_json={"brand": "SoundMax", "color": "black"},
            shelf_floor="2F",
            shelf_zone="家電コーナー",
            aliases_json=["イヤホン", "Bluetoothイヤホン"],
        ),
        Product(
            sku="SKU-002",
            location_id=_DEFAULT_LOCATION_ID,
            name="USB充電器",
            category="家電",
            attributes_json={"brand": "PowerUp", "watts": "65W"},
            shelf_floor="2F",
            shelf_zone="家電コーナー",
            aliases_json=["充電器", "ACアダプター"],
        ),
        Product(
            sku="SKU-003",
            location_id=_DEFAULT_LOCATION_ID,
            name="エコバッグ",
            category="雑貨",
            attributes_json={"material": "リサイクルポリエステル"},
            shelf_floor="1F",
            shelf_zone="雑貨コーナー",
            aliases_json=["買い物袋", "マイバッグ"],
        ),
    ]
    db.add_all(entries)


async def _seed_inventories(db: AsyncSession) -> None:
    entries = [
        Inventory(inventory_id="inv-001", sku="SKU-001", stock_status="in_stock", quantity=15),
        Inventory(inventory_id="inv-002", sku="SKU-002", stock_status="in_stock", quantity=8),
        Inventory(inventory_id="inv-003", sku="SKU-003", stock_status="out_of_stock", quantity=0),
    ]
    db.add_all(entries)


async def _seed_documents(db: AsyncSession) -> None:
    docs = [
        Document(
            doc_id="doc-return-001",
            location_id=_DEFAULT_LOCATION_ID,
            document_type="policy",
            title="返品ポリシー",
            content=(
                "商品の返品は、購入日から14日以内に限り承ります。"
                "レシートと未使用の商品をお持ちください。"
                "食品・衛生用品・セール品は返品対象外です。"
                "返品時は1階サービスカウンターまでお越しください。"
            ),
            language_code="ja",
        ),
        Document(
            doc_id="doc-exchange-001",
            location_id=_DEFAULT_LOCATION_ID,
            document_type="policy",
            title="交換ポリシー",
            content=(
                "商品の交換は、購入日から30日以内に承ります。"
                "同一商品の色・サイズ違いへの交換が可能です。"
                "価格差がある場合は差額をお支払いいただきます。"
                "交換時はレシートと商品をお持ちください。"
            ),
            language_code="ja",
        ),
        Document(
            doc_id="doc-faq-001",
            location_id=_DEFAULT_LOCATION_ID,
            document_type="faq",
            title="よくある質問",
            content=(
                "Q: ギフトラッピングはできますか？ A: はい、1階サービスカウンターで承ります。料金は330円です。"
                "Q: ポイントカードはありますか？ A: ShopAIメンバーズカードがございます。100円で1ポイント貯まります。"
                "Q: 配送はできますか？ A: 3,000円以上のお買い上げで配送を承ります。配送料は地域により異なります。"
            ),
            language_code="ja",
        ),
    ]
    db.add_all(docs)

    chunks = [
        DocumentChunk(
            chunk_id="chunk-ret-001", doc_id="doc-return-001",
            location_id=_DEFAULT_LOCATION_ID, chunk_index=0,
            content="商品の返品は、購入日から14日以内に限り承ります。レシートと未使用の商品をお持ちください。",
        ),
        DocumentChunk(
            chunk_id="chunk-ret-002", doc_id="doc-return-001",
            location_id=_DEFAULT_LOCATION_ID, chunk_index=1,
            content="食品・衛生用品・セール品は返品対象外です。返品時は1階サービスカウンターまでお越しください。",
        ),
        DocumentChunk(
            chunk_id="chunk-exc-001", doc_id="doc-exchange-001",
            location_id=_DEFAULT_LOCATION_ID, chunk_index=0,
            content="商品の交換は、購入日から30日以内に承ります。同一商品の色・サイズ違いへの交換が可能です。",
        ),
        DocumentChunk(
            chunk_id="chunk-exc-002", doc_id="doc-exchange-001",
            location_id=_DEFAULT_LOCATION_ID, chunk_index=1,
            content="価格差がある場合は差額をお支払いいただきます。交換時はレシートと商品をお持ちください。",
        ),
        DocumentChunk(
            chunk_id="chunk-faq-001", doc_id="doc-faq-001",
            location_id=_DEFAULT_LOCATION_ID, chunk_index=0,
            content="ギフトラッピングは1階サービスカウンターで承ります。料金は330円です。",
        ),
        DocumentChunk(
            chunk_id="chunk-faq-002", doc_id="doc-faq-001",
            location_id=_DEFAULT_LOCATION_ID, chunk_index=1,
            content="ShopAIメンバーズカードがございます。100円で1ポイント貯まります。",
        ),
        DocumentChunk(
            chunk_id="chunk-faq-003", doc_id="doc-faq-001",
            location_id=_DEFAULT_LOCATION_ID, chunk_index=2,
            content="3,000円以上のお買い上げで配送を承ります。配送料は地域により異なります。",
        ),
    ]
    db.add_all(chunks)
