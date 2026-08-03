from arq.connections import ArqRedis
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import ACCESS_TOKEN_COOKIE_NAME, decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole, UserStatus

__all__ = ["get_db", "get_current_user", "get_arq_pool_dep", "require_admin"]


def get_arq_pool_dep(request: Request) -> ArqRedis:
    return request.app.state.arq_pool


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="Not logged in. Please log in and try again.")

    user_id = decode_access_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Session expired or invalid. Please log in again.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Account not found. Please log in again.")
    if user.status == UserStatus.suspended:
        raise HTTPException(status_code=403, detail="This account has been suspended. Contact an admin for help.")

    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return current_user
