"""add user status

Revision ID: bb14567738ab
Revises: dad4915909ad
Create Date: 2026-08-02 04:55:38.480678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb14567738ab'
down_revision: Union[str, None] = 'dad4915909ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Autogenerate's bare add_column doesn't create the backing Postgres
    # enum type in this project's async migration setup — create it
    # explicitly first (checkfirst=True so this is safe to re-run).
    user_status = sa.Enum('active', 'suspended', name='user_status')
    user_status.create(op.get_bind(), checkfirst=True)
    op.add_column('users', sa.Column('status', user_status, server_default='active', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'status')
    sa.Enum(name='user_status').drop(op.get_bind(), checkfirst=True)
