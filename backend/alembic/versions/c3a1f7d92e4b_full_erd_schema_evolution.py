"""full ERD schema evolution

Revision ID: c3a1f7d92e4b
Revises: 89059e6406ba
Create Date: 2026-02-25 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3a1f7d92e4b"
down_revision: Union[str, None] = "89059e6406ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- 1. New standalone tables ---
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"])

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("first_name", sa.String(), nullable=False),
        sa.Column("last_name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_customers_id"), "customers", ["id"])

    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("quantity_available", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_resources_id"), "resources", ["id"])

    op.create_table(
        "poll_execution",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("window_start", sa.DateTime(), nullable=False),
        sa.Column("window_end", sa.DateTime(), nullable=False),
        sa.Column("executed_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.String(50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_poll_execution_id"), "poll_execution", ["id"])

    # --- 2. Restructure tours ---
    op.add_column("tours", sa.Column("name", sa.String(), nullable=True))
    op.add_column("tours", sa.Column("description", sa.String(), nullable=True))
    op.add_column("tours", sa.Column("duration", sa.Integer(), nullable=True))

    op.drop_constraint("tours_assigned_guide_id_fkey", "tours", type_="foreignkey")
    op.drop_column("tours", "clorian_booking_id")
    op.drop_column("tours", "date")
    op.drop_column("tours", "start_time")
    op.drop_column("tours", "end_time")
    op.drop_column("tours", "required_expertise")
    op.drop_column("tours", "required_category")
    op.drop_column("tours", "requested_language_code")
    op.drop_column("tours", "status")
    op.drop_column("tours", "assigned_guide_id")

    # --- 3. Restructure guides ---
    op.add_column("guides", sa.Column("first_name", sa.String(), nullable=True))
    op.add_column("guides", sa.Column("last_name", sa.String(), nullable=True))
    op.add_column("guides", sa.Column("phone", sa.String(), nullable=True))
    op.add_column("guides", sa.Column("guide_rating", sa.Numeric(), nullable=True))

    op.execute("UPDATE guides SET first_name = split_part(name, ' ', 1)")
    op.execute(
        "UPDATE guides SET last_name = CASE "
        "WHEN position(' ' in name) > 0 THEN substring(name from position(' ' in name) + 1) "
        "ELSE '' END"
    )
    op.execute("UPDATE guides SET phone = '' WHERE phone IS NULL")
    op.execute("UPDATE guides SET guide_rating = 0 WHERE guide_rating IS NULL")

    op.alter_column("guides", "first_name", nullable=False)
    op.alter_column("guides", "last_name", nullable=False)
    op.alter_column("guides", "phone", nullable=False, server_default="")
    op.drop_column("guides", "name")

    # --- 4. guide_tour_types association ---
    op.create_table(
        "guide_tour_types",
        sa.Column("guide_id", sa.Integer(), sa.ForeignKey("guides.id"), nullable=False),
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id"), nullable=False),
        sa.PrimaryKeyConstraint("guide_id", "tour_id"),
    )

    # --- 5. Restructure bookings ---
    # First migrate data to booking_versions (need the table first)

    op.create_table(
        "booking_versions",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.booking_id"), nullable=False),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("adult_tickets", sa.Integer(), nullable=False),
        sa.Column("child_tickets", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("valid_from", sa.DateTime(), nullable=False),
        sa.Column("poll_execution_id", sa.Integer(), sa.ForeignKey("poll_execution.id"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_id", "hash", name="uq_booking_hash"),
    )
    op.create_index(op.f("ix_booking_versions_id"), "booking_versions", ["id"])

    # Insert initial poll_execution row
    op.execute(
        "INSERT INTO poll_execution (window_start, window_end, status) "
        "VALUES ('2015-01-01', NOW(), 'initial_load')"
    )

    # Migrate booking data to booking_versions
    op.execute(
        "INSERT INTO booking_versions "
        "(booking_id, hash, status, adult_tickets, child_tickets, start_date, valid_from, poll_execution_id) "
        "SELECT "
        "booking_id, "
        "md5(booking_id::text || '|' || status || '|' || adult_tickets::text || '|' || child_tickets::text || '|' || date::text), "
        "status, "
        "adult_tickets, "
        "child_tickets, "
        "date, "
        "created_at, "
        "1 "
        "FROM bookings"
    )

    # Now alter customer_id from String to BigInteger FK
    op.drop_column("bookings", "customer_id")
    op.add_column("bookings", sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=True))

    # Drop moved columns from bookings
    op.drop_column("bookings", "date")
    op.drop_column("bookings", "start_time")
    op.drop_column("bookings", "end_time")
    op.drop_column("bookings", "required_expertise")
    op.drop_column("bookings", "required_category")
    op.drop_column("bookings", "requested_language_code")
    op.drop_column("bookings", "adult_tickets")
    op.drop_column("bookings", "child_tickets")
    op.drop_column("bookings", "status")

    # --- 6. Remaining dependent tables ---
    op.create_table(
        "cost",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id"), nullable=False),
        sa.Column("ticket_type", sa.String(20), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("valid_from", sa.DateTime(), nullable=False),
        sa.Column("valid_to", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cost_id"), "cost", ["id"])

    op.create_table(
        "tour_resources",
        sa.Column("tour_id", sa.Integer(), sa.ForeignKey("tours.id"), nullable=False),
        sa.Column("resource_id", sa.Integer(), sa.ForeignKey("resources.id"), nullable=False),
        sa.Column("quantity_required", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("tour_id", "resource_id"),
    )

    op.create_table(
        "schedule",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("booking_version_id", sa.Integer(), sa.ForeignKey("booking_versions.id"), nullable=False),
        sa.Column("guide_id", sa.Integer(), sa.ForeignKey("guides.id"), nullable=False),
        sa.Column("resource_id", sa.Integer(), sa.ForeignKey("resources.id"), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_schedule_id"), "schedule", ["id"])

    op.create_table(
        "surveys",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("guide_id", sa.Integer(), sa.ForeignKey("guides.id"), nullable=False),
        sa.Column("booking_version_id", sa.Integer(), sa.ForeignKey("booking_versions.id"), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_surveys_id"), "surveys", ["id"])


def downgrade() -> None:
    # Drop new dependent tables
    op.drop_index(op.f("ix_surveys_id"), table_name="surveys")
    op.drop_table("surveys")
    op.drop_index(op.f("ix_schedule_id"), table_name="schedule")
    op.drop_table("schedule")
    op.drop_table("tour_resources")
    op.drop_index(op.f("ix_cost_id"), table_name="cost")
    op.drop_table("cost")

    # Restore bookings columns
    op.add_column("bookings", sa.Column("status", sa.String(), nullable=True, server_default="pending"))
    op.add_column("bookings", sa.Column("child_tickets", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("bookings", sa.Column("adult_tickets", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("bookings", sa.Column("requested_language_code", sa.String(), nullable=True))
    op.add_column("bookings", sa.Column("required_category", sa.String(), nullable=True))
    op.add_column("bookings", sa.Column("required_expertise", sa.String(), nullable=True))
    op.add_column("bookings", sa.Column("end_time", sa.Time(), nullable=True))
    op.add_column("bookings", sa.Column("start_time", sa.Time(), nullable=True))
    op.add_column("bookings", sa.Column("date", sa.Date(), nullable=True))

    # Restore booking data from booking_versions
    op.execute(
        "UPDATE bookings b SET "
        "status = bv.status, "
        "adult_tickets = bv.adult_tickets, "
        "child_tickets = bv.child_tickets, "
        "date = bv.start_date "
        "FROM (SELECT DISTINCT ON (booking_id) * FROM booking_versions ORDER BY booking_id, id DESC) bv "
        "WHERE b.booking_id = bv.booking_id"
    )

    # Restore customer_id as String
    op.drop_column("bookings", "customer_id")
    op.add_column("bookings", sa.Column("customer_id", sa.String(), nullable=True))

    # Drop booking_versions
    op.drop_index(op.f("ix_booking_versions_id"), table_name="booking_versions")
    op.drop_table("booking_versions")

    # Drop guide_tour_types
    op.drop_table("guide_tour_types")

    # Restore guides
    op.add_column("guides", sa.Column("name", sa.String(), nullable=True))
    op.execute("UPDATE guides SET name = first_name || ' ' || last_name")
    op.alter_column("guides", "name", nullable=False)
    op.drop_column("guides", "guide_rating")
    op.drop_column("guides", "phone")
    op.drop_column("guides", "last_name")
    op.drop_column("guides", "first_name")

    # Restore tours
    op.add_column("tours", sa.Column("assigned_guide_id", sa.Integer(), nullable=True))
    op.add_column("tours", sa.Column("status", sa.String(), nullable=True, server_default="pending"))
    op.add_column("tours", sa.Column("requested_language_code", sa.String(), nullable=True))
    op.add_column("tours", sa.Column("required_category", sa.String(), nullable=True))
    op.add_column("tours", sa.Column("required_expertise", sa.String(), nullable=True))
    op.add_column("tours", sa.Column("end_time", sa.Time(), nullable=True))
    op.add_column("tours", sa.Column("start_time", sa.Time(), nullable=True))
    op.add_column("tours", sa.Column("date", sa.Date(), nullable=True))
    op.add_column("tours", sa.Column("clorian_booking_id", sa.String(), nullable=True))
    op.create_foreign_key("tours_assigned_guide_id_fkey", "tours", "guides", ["assigned_guide_id"], ["id"])
    op.drop_column("tours", "duration")
    op.drop_column("tours", "description")
    op.drop_column("tours", "name")

    # Drop standalone tables
    op.drop_index(op.f("ix_poll_execution_id"), table_name="poll_execution")
    op.drop_table("poll_execution")
    op.drop_index(op.f("ix_resources_id"), table_name="resources")
    op.drop_table("resources")
    op.drop_index(op.f("ix_customers_id"), table_name="customers")
    op.drop_table("customers")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
