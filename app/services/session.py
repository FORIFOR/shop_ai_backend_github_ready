from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Session


class SessionService:
    async def ensure_session(
        self,
        db: AsyncSession,
        session_id: str,
        device_id: str,
        location_id: str,
        language_code: str,
        is_new_session: bool,
    ) -> Session:
        result = await db.execute(
            select(Session).where(Session.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        now = datetime.now(timezone.utc)

        if session is None:
            session = Session(
                session_id=session_id,
                device_id=device_id,
                location_id=location_id,
                language_code=language_code,
                status="active",
                created_at=now,
                last_seen_at=now,
            )
            db.add(session)
            await db.flush()
            return session

        if is_new_session:
            session.status = "active"
        session.last_seen_at = now
        await db.flush()
        return session
