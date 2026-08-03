"""One-off admin bootstrap. Usage: venv/bin/python3.11 -m app.scripts.promote_admin <email>"""

import asyncio
import sys

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole


async def promote(email: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            print(f"No user found with email {email!r}. Register the account first, then promote it.")
            raise SystemExit(1)
        if user.role == UserRole.admin:
            print(f"{email} is already an admin.")
            return
        user.role = UserRole.admin
        db.add(AuditLog(user_id=user.id, action=f"cli_promoted_admin:{user.id}"))
        await db.commit()
        print(f"{email} promoted to admin.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: venv/bin/python3.11 -m app.scripts.promote_admin <email>")
        raise SystemExit(1)
    asyncio.run(promote(sys.argv[1]))
