from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(db: AsyncSession, user_id: int, notification_type: str, message: str) -> None:
    db.add(Notification(user_id=user_id, type=notification_type, message=message))
