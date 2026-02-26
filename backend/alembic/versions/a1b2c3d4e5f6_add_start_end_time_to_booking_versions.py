"""add start_time and end_time to booking_versions

Revision ID: a1b2c3d4e5f6
Revises: c3a1f7d92e4b
Create Date: 2026-02-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "c3a1f7d92e4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("booking_versions", sa.Column("start_time", sa.Time(), nullable=True))
    op.add_column("booking_versions", sa.Column("end_time", sa.Time(), nullable=True))


def downgrade() -> None:
    op.drop_column("booking_versions", "end_time")
    op.drop_column("booking_versions", "start_time")
