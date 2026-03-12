import hashlib
import json

from sqlalchemy import text


def handle_reservation_cancellation(conn, reservation_id, schedule_id):
    """Placeholder so tests can patch this."""
    pass


def handle_reservation_change(
    conn,
    reservation_id,
    old_schedule_id,
    new_tour_id,
    new_language_code,
    new_event_start,
    new_event_end,
):
    """Placeholder so tests can patch this."""
    pass


def process_staging_rows(conn):
    rows = (
        conn.execute(
            text(
                """
        SELECT *
        FROM public.poll_staging
        WHERE processed_at IS NULL
        ORDER BY created_at
        """
            )
        )
        .mappings()
        .all()
    )

    processed_count = 0

    for row in rows:
        payload = row["payload_json"]

        customer = payload["customer"]
        reservation = payload
        tickets = payload["tickets"]

        # Insert customer
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

        # Get customer id
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

        # Get tour id
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

        # Insert reservation
        conn.execute(
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
            ON CONFLICT (clorian_reservation_id) DO NOTHING
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
        )

        # Get reservation id
        reservation_id = conn.execute(
            text(
                """
            SELECT id
            FROM reservations
            WHERE clorian_reservation_id = :rid
        """
            ),
            {"rid": reservation["clorian_reservation_id"]},
        ).scalar_one()

        # Insert tickets
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

        # Hash payload
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

        # Detect cancellation or changes
        old = conn.execute(
            text(
                """
            SELECT id, tour_id, language_code, event_start_datetime, status, schedule_id
            FROM reservations
            WHERE id = :id
        """
            ),
            {"id": reservation_id},
        ).fetchone()

        if old:
            old_status = (old[4] or "").upper()
            new_status = (reservation["status"] or "").upper()

            # Cancellation
            if new_status == "CANCELLED" and old_status != "CANCELLED":
                conn.execute(
                    text("UPDATE reservations SET schedule_id = NULL WHERE id = :id"),
                    {"id": reservation_id},
                )

                handle_reservation_cancellation(conn, reservation_id, old[5])

            # Language / schedule change
            elif (
                old[1] != tour_id
                or (old[2] or "").lower() != (reservation["language_code"] or "").lower()
                or str(old[3]) != reservation["event_start_datetime"]
            ):
                handle_reservation_change(
                    conn,
                    reservation_id=reservation_id,
                    old_schedule_id=old[5],
                    new_tour_id=tour_id,
                    new_language_code=reservation["language_code"],
                    new_event_start=reservation["event_start_datetime"],
                    new_event_end=reservation.get(
                        "event_end_datetime",
                        reservation["event_start_datetime"],
                    ),
                )

        # Mark processed
        conn.execute(
            text(
                """
            UPDATE public.poll_staging
            SET processed_at = NOW(),
                processed_status = 'SUCCESS'
            WHERE id = :id
        """
            ),
            {"id": row["id"]},
        )

        processed_count += 1

    return processed_count
