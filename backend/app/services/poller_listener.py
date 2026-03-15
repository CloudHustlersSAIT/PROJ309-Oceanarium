import hashlib
import json
import logging

from sqlalchemy import text

from .guide_assignment import UnassignableError, auto_assign_guide
from .notification import notify_guide_assignment, notify_schedule_unassignable
from .notification_dispatcher import dispatch_events
from .rescheduling import handle_reservation_cancellation, handle_reservation_change
from .schedule_service import get_or_create_schedule

logger = logging.getLogger(__name__)

# Limit number of rows processed per scheduler run
BATCH_SIZE = 25


def _safe_parse_payload(payload):
    """
    Safely parse payload_json.

    Handles:
    - dict
    - JSON string
    - double encoded JSON
    """

    if payload is None:
        return None

    attempts = 0

    while isinstance(payload, str) and attempts < 3:
        try:
            payload = json.loads(payload)
        except Exception:
            logger.exception("Failed parsing payload_json")
            return None
        attempts += 1

    if not isinstance(payload, dict):
        return None

    return payload


def process_staging_rows(conn):
    """
    Process unprocessed rows from poll_staging.

    - Inserts customers, reservations, tickets
    - Assigns schedules
    - Auto assigns guides
    - Handles reservation changes
    - Handles row level failures safely
    """

    rows = (
        conn.execute(
            text(
                """
                SELECT *
                FROM public.poll_staging
                WHERE processed_at IS NULL
                ORDER BY created_at
                LIMIT :limit
                """
            ),
            {"limit": BATCH_SIZE},
        )
        .mappings()
        .all()
    )

    if not rows:
        return 0

    processed_count = 0

    for row in rows:
        row_id = row["id"]

        try:
            payload = _safe_parse_payload(row["payload_json"])

            if not payload:
                raise Exception("Invalid payload_json")

            customer = payload["customer"]
            reservation = payload
            tickets = payload.get("tickets", [])

            # -------------------------
            # Insert / upsert customer
            # -------------------------

            conn.execute(
                text(
                    """
                    INSERT INTO customers (
                        clorian_client_id,
                        first_name,
                        last_name,
                        email
                    )
                    VALUES (
                        :client_id,
                        :first_name,
                        :last_name,
                        :email
                    )
                    ON CONFLICT (clorian_client_id) DO NOTHING
                    """
                ),
                {
                    "client_id": customer["clorian_client_id"],
                    "first_name": customer["first_name"],
                    "last_name": customer["last_name"],
                    "email": customer["email"],
                },
            )

            customer_id = conn.execute(
                text(
                    """
                    SELECT id
                    FROM customers
                    WHERE clorian_client_id = :client_id
                    """
                ),
                {"client_id": customer["clorian_client_id"]},
            ).scalar_one()

            # -------------------------
            # Find internal tour
            # -------------------------

            tour = conn.execute(
                text(
                    """
                    SELECT id
                    FROM tours
                    WHERE clorian_product_id = :program_id
                    """
                ),
                {"program_id": reservation["tour"]["program_id"]},
            ).fetchone()

            if not tour:
                raise Exception("Tour not found")

            tour_id = tour[0]

            # -------------------------
            # Fetch existing reservation
            # -------------------------

            old = conn.execute(
                text(
                    """
                    SELECT id, tour_id, language_code, event_start_datetime, status, schedule_id
                    FROM reservations
                    WHERE clorian_reservation_id = :rid
                    """
                ),
                {"rid": reservation["clorian_reservation_id"]},
            ).fetchone()

            # -------------------------
            # Upsert reservation
            # -------------------------

            result_row = conn.execute(
                text(
                    """
                    INSERT INTO reservations (
                        clorian_reservation_id,
                        clorian_purchase_id,
                        customer_id,
                        tour_id,
                        language_code,
                        event_start_datetime,
                        status,
                        current_ticket_num,
                        clorian_created_at,
                        clorian_modified_at
                    )
                    VALUES (
                        :reservation_id,
                        :purchase_id,
                        :customer_id,
                        :tour_id,
                        :language,
                        :event_start,
                        :status,
                        :ticket_count,
                        :created_at,
                        :modified_at
                    )
                    ON CONFLICT (clorian_reservation_id) DO UPDATE
                    SET tour_id = EXCLUDED.tour_id,
                        language_code = EXCLUDED.language_code,
                        event_start_datetime = EXCLUDED.event_start_datetime,
                        status = EXCLUDED.status,
                        current_ticket_num = EXCLUDED.current_ticket_num,
                        clorian_modified_at = EXCLUDED.clorian_modified_at
                    RETURNING id
                    """
                ),
                {
                    "reservation_id": reservation["clorian_reservation_id"],
                    "purchase_id": reservation["clorian_purchase_id"],
                    "customer_id": customer_id,
                    "tour_id": tour_id,
                    "language": reservation["language_code"],
                    "event_start": reservation["event_start_datetime"],
                    "status": reservation["status"],
                    "ticket_count": reservation["current_ticket_num"],
                    "created_at": reservation["clorian_created_at"],
                    "modified_at": reservation["clorian_modified_at"],
                },
            ).fetchone()

            reservation_id = result_row[0]

            # -------------------------
            # Schedule assignment
            # -------------------------

            if old is None:
                event_start = reservation["event_start_datetime"]
                event_end = reservation.get("event_end_datetime") or event_start

                schedule_id = get_or_create_schedule(
                    conn=conn,
                    tour_id=tour_id,
                    language_code=reservation["language_code"],
                    event_start_datetime=event_start,
                    event_end_datetime=event_end,
                )

                conn.execute(
                    text(
                        """
                        UPDATE reservations
                        SET schedule_id = :schedule_id
                        WHERE id = :reservation_id
                        """
                    ),
                    {
                        "schedule_id": schedule_id,
                        "reservation_id": reservation_id,
                    },
                )

                # -------------------------
                # Auto guide assignment
                # -------------------------

                schedule_row = conn.execute(
                    text(
                        """
                        SELECT guide_id
                        FROM schedule
                        WHERE id = :schedule_id
                        """
                    ),
                    {"schedule_id": schedule_id},
                ).fetchone()

                if schedule_row and schedule_row[0] is None:
                    try:
                        assign_result = auto_assign_guide(
                            conn,
                            schedule_id,
                            commit=False,
                        )

                        notify_guide_assignment(
                            conn,
                            schedule_id,
                            assign_result["guide_id"],
                            "AUTO",
                            commit=False,
                        )

                    except UnassignableError as e:
                        notify_schedule_unassignable(
                            conn,
                            schedule_id,
                            e.reasons,
                            commit=False,
                        )

                    except Exception:
                        logger.exception(
                            "Guide auto assignment failed for schedule %s",
                            schedule_id,
                        )

            # -------------------------
            # Insert tickets
            # -------------------------

            for ticket in tickets:
                conn.execute(
                    text(
                        """
                        INSERT INTO tickets (
                            clorian_ticket_id,
                            reservation_id,
                            buyer_type_id,
                            buyer_type_name,
                            start_datetime,
                            end_datetime,
                            ticket_status,
                            price,
                            venue_id,
                            venue_name,
                            clorian_created_at,
                            clorian_modified_at
                        )
                        VALUES (
                            :ticket_id,
                            :reservation_id,
                            :buyer_type_id,
                            :buyer_type_name,
                            :start_datetime,
                            :end_datetime,
                            :status,
                            :price,
                            :venue_id,
                            :venue_name,
                            :created_at,
                            :modified_at
                        )
                        ON CONFLICT (clorian_ticket_id) DO NOTHING
                        """
                    ),
                    {
                        "ticket_id": ticket["clorian_ticket_id"],
                        "reservation_id": reservation_id,
                        "buyer_type_id": ticket["buyer_type_id"],
                        "buyer_type_name": ticket["buyer_type_name"],
                        "start_datetime": ticket["start_datetime"],
                        "end_datetime": ticket["end_datetime"],
                        "status": ticket["ticket_status"],
                        "price": ticket["price"],
                        "venue_id": ticket["venue_id"],
                        "venue_name": ticket["venue_name"],
                        "created_at": ticket["clorian_created_at"],
                        "modified_at": ticket["clorian_modified_at"],
                    },
                )

            # -------------------------
            # Reservation versioning
            # -------------------------

            payload_string = json.dumps(payload, sort_keys=True)
            hash_value = hashlib.sha256(payload_string.encode()).hexdigest()

            latest_hash = conn.execute(
                text(
                    """
                    SELECT hash
                    FROM reservation_versions
                    WHERE reservation_id = :reservation_id
                    ORDER BY id DESC
                    LIMIT 1
                    """
                ),
                {"reservation_id": reservation_id},
            ).fetchone()

            if not latest_hash or latest_hash[0] != hash_value:
                conn.execute(
                    text(
                        """
                        INSERT INTO reservation_versions (
                            reservation_id,
                            hash,
                            status,
                            current_ticket_num,
                            language_code,
                            event_start_datetime,
                            poll_execution_id
                        )
                        VALUES (
                            :reservation_id,
                            :hash,
                            :status,
                            :ticket_num,
                            :language,
                            :event_start,
                            :poll_execution_id
                        )
                        """
                    ),
                    {
                        "reservation_id": reservation_id,
                        "hash": hash_value,
                        "status": reservation["status"],
                        "ticket_num": reservation["current_ticket_num"],
                        "language": reservation["language_code"],
                        "event_start": reservation["event_start_datetime"],
                        "poll_execution_id": row["poll_execution_id"],
                    },
                )

            # -------------------------
            # Detect reservation changes
            # -------------------------

            if old is not None and old[5] is not None:
                old_tour_id = old[1]
                old_language = old[2]
                old_event_start = str(old[3]) if old[3] else None
                old_status = (old[4] or "").strip().upper()
                old_schedule_id = old[5]

                new_status = (reservation["status"] or "").strip().upper()

                if new_status == "CANCELLED" and old_status != "CANCELLED":
                    conn.execute(
                        text("UPDATE reservations SET schedule_id = NULL WHERE id = :id"),
                        {"id": reservation_id},
                    )

                    events = handle_reservation_cancellation(
                        conn,
                        reservation_id,
                        old_schedule_id,
                    )

                    if isinstance(events, list):
                        dispatch_events(conn, events)

                elif (
                    old_tour_id != tour_id
                    or (old_language or "").lower() != (reservation["language_code"] or "").lower()
                    or old_event_start != reservation["event_start_datetime"]
                ):
                    events = handle_reservation_change(
                        conn,
                        reservation_id=reservation_id,
                        old_schedule_id=old_schedule_id,
                        new_tour_id=tour_id,
                        new_language_code=reservation["language_code"],
                        new_event_start=reservation["event_start_datetime"],
                        new_event_end=reservation.get(
                            "event_end_datetime",
                            reservation["event_start_datetime"],
                        ),
                    )

                    if events:
                        if isinstance(events, dict):
                            events = [events]
                        elif not isinstance(events, list):
                            events = [events]
                        dispatch_events(conn, events)

            # -------------------------
            # Mark row processed
            # -------------------------

            conn.execute(
                text(
                    """
                    UPDATE public.poll_staging
                    SET processed_at = NOW(),
                        processed_status = 'SUCCESS'
                    WHERE id = :id
                    """
                ),
                {"id": row_id},
            )

            processed_count += 1

        except Exception as e:
            logger.exception("Failed processing staging row %s", row_id)

            conn.execute(
                text(
                    """
                    UPDATE public.poll_staging
                    SET processed_at = NOW(),
                        processed_status = 'FAILED',
                        processed_error = :error
                    WHERE id = :id
                    """
                ),
                {"id": row_id, "error": str(e)[:1000]},
            )

            raise e

    return processed_count
