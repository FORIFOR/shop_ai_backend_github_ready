import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import StaffCallRecord

logger = logging.getLogger(__name__)


class StaffCallService:
    async def record(
        self,
        db: AsyncSession,
        *,
        session_id: str,
        device_id: str,
        location_id: str,
        reason: str,
        trigger_text: str,
    ) -> StaffCallRecord:
        record = StaffCallRecord(
            call_id=uuid.uuid4().hex,
            session_id=session_id,
            device_id=device_id,
            location_id=location_id,
            reason=reason,
            trigger_text=trigger_text,
            status="pending",
        )
        db.add(record)
        await db.flush()

        logger.info(
            "staff_call recorded: call_id=%s location=%s reason=%s",
            record.call_id,
            location_id,
            reason,
        )
        return record
