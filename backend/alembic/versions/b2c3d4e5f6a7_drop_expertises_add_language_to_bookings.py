"""drop expertises tables and add requested_language_code to bookings

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("guide_expertises")
    op.drop_table("expertises")
    op.add_column("bookings", sa.Column("requested_language_code", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("bookings", "requested_language_code")
    op.create_table(
        "expertises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
    )
    op.create_table(
        "guide_expertises",
        sa.Column("guide_id", sa.Integer(), sa.ForeignKey("guides.id"), primary_key=True),
        sa.Column("expertise_id", sa.Integer(), sa.ForeignKey("expertises.id"), primary_key=True),
    )
