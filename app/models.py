import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class Session(Base):
    __tablename__ = "sessions"

    session_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    location_id: Mapped[str] = mapped_column(String(128), nullable=False)
    language_code: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class QuestionLog(Base):
    __tablename__ = "question_logs"

    question_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_id)
    session_id: Mapped[str] = mapped_column(String(128), nullable=False)
    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    location_id: Mapped[str] = mapped_column(String(128), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str] = mapped_column(Text, default="")
    intent: Mapped[str] = mapped_column(String(64), default="")
    route: Mapped[str] = mapped_column(String(32), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_source: Mapped[str] = mapped_column(String(32), nullable=False)
    model_used: Mapped[str] = mapped_column(String(64), default="")
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    requires_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    handoff_reason: Mapped[str | None] = mapped_column(String(128), nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class StaffCallRecord(Base):
    __tablename__ = "staff_calls"

    call_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_id)
    session_id: Mapped[str] = mapped_column(String(128), default="")
    device_id: Mapped[str] = mapped_column(String(128), nullable=False)
    location_id: Mapped[str] = mapped_column(String(128), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    trigger_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Location(Base):
    __tablename__ = "locations"

    location_entry_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_id)
    location_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(64), default="")
    floor: Mapped[str] = mapped_column(String(32), default="")
    zone: Mapped[str] = mapped_column(String(64), default="")
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    guidance_text: Mapped[str] = mapped_column(Text, default="")
    aliases_json: Mapped[list] = mapped_column(JSON, default=list)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class Product(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(64), primary_key=True)
    location_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    category: Mapped[str] = mapped_column(String(128), default="")
    attributes_json: Mapped[dict] = mapped_column(JSON, default=dict)
    shelf_floor: Mapped[str] = mapped_column(String(32), default="")
    shelf_zone: Mapped[str] = mapped_column(String(64), default="")
    aliases_json: Mapped[list] = mapped_column(JSON, default=list)


class Inventory(Base):
    __tablename__ = "inventories"

    inventory_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_id)
    sku: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    stock_status: Mapped[str] = mapped_column(String(32), default="in_stock")
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class FaqStructured(Base):
    __tablename__ = "faq_structured"

    faq_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_id)
    location_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="")
    tags_json: Mapped[list] = mapped_column(JSON, default=list)


class Document(Base):
    __tablename__ = "documents"

    doc_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_id)
    location_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(64), default="")
    title: Mapped[str] = mapped_column(String(256), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    language_code: Mapped[str] = mapped_column(String(16), default="ja")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    chunk_id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_id)
    doc_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
