"""Add notification preferences and tracking fields

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-11
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing columns to notifications table
    op.execute("""
        ALTER TABLE notifications
        ADD COLUMN IF NOT EXISTS read_at TIMESTAMPTZ,
        ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS priority VARCHAR(20) NOT NULL DEFAULT 'normal',
        ADD COLUMN IF NOT EXISTS action_required BOOLEAN NOT NULL DEFAULT FALSE,
        ADD COLUMN IF NOT EXISTS detail_json JSONB,
        ADD COLUMN IF NOT EXISTS actions_json JSONB;
    """)

    # Create notification preferences table
    op.execute("""
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            guide_id INTEGER REFERENCES guides(id) ON DELETE CASCADE,
            event_type VARCHAR(100) NOT NULL,
            email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            portal_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT check_user_or_guide CHECK (
                (user_id IS NOT NULL AND guide_id IS NULL) OR
                (user_id IS NULL AND guide_id IS NOT NULL)
            ),
            CONSTRAINT unique_user_event UNIQUE(user_id, event_type),
            CONSTRAINT unique_guide_event UNIQUE(guide_id, event_type)
        );
    """)

    # Create indexes for faster preference lookups
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_notification_preferences_user_id
        ON notification_preferences(user_id);
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_notification_preferences_guide_id
        ON notification_preferences(guide_id);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS notification_preferences CASCADE;")
    op.execute("""
        ALTER TABLE notifications
        DROP COLUMN IF EXISTS read_at,
        DROP COLUMN IF EXISTS retry_count,
        DROP COLUMN IF EXISTS priority,
        DROP COLUMN IF EXISTS action_required,
        DROP COLUMN IF EXISTS detail_json,
        DROP COLUMN IF EXISTS actions_json;
    """)
