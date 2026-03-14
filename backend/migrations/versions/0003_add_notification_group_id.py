"""Add group_id UUID to notifications for correlating PORTAL and EMAIL rows

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-13
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE notifications
        ADD COLUMN IF NOT EXISTS group_id UUID;
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_notifications_group_id
        ON notifications (group_id);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_notifications_group_id;")
    op.execute("ALTER TABLE notifications DROP COLUMN IF EXISTS group_id;")
