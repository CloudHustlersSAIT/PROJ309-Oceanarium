from app.services.mock_poller import generate_records


def test_generate_records_reuses_schedule_fingerprints_for_create_rows(monkeypatch):
    monkeypatch.setattr(
        "app.services.mock_poller.load_tours",
        lambda _conn: [
            {"id": 1, "clorian_product_id": 10, "name": "Main", "description": "Main", "duration": 90},
            {"id": 2, "clorian_product_id": 11, "name": "Deep", "description": "Deep", "duration": 60},
        ],
    )
    monkeypatch.setattr(
        "app.services.mock_poller.load_guide_capabilities",
        lambda _conn: [
            {"clorian_product_id": 10, "language_code": "en"},
            {"clorian_product_id": 11, "language_code": "pt"},
        ],
    )
    monkeypatch.setattr("app.services.mock_poller.load_existing_reservations", lambda _conn: {})

    staged, counts = generate_records(
        conn=None,
        seed=42,
        batch_size=12,
        update_ratio=0.0,
        unchanged_ratio=0.0,
    )

    assert counts["created"] == 12

    fingerprints = [
        (
            item["payload"]["tour"]["program_id"],
            item["payload"]["language_code"],
            item["payload"]["event_start_datetime"],
        )
        for item in staged
    ]

    assert len(set(fingerprints)) < len(fingerprints)


def test_generate_records_can_force_single_shared_create_slot(monkeypatch):
    monkeypatch.setattr(
        "app.services.mock_poller.load_tours",
        lambda _conn: [
            {"id": 1, "clorian_product_id": 10, "name": "Main", "description": "Main", "duration": 90},
            {"id": 2, "clorian_product_id": 11, "name": "Deep", "description": "Deep", "duration": 60},
        ],
    )
    monkeypatch.setattr(
        "app.services.mock_poller.load_guide_capabilities",
        lambda _conn: [
            {"clorian_product_id": 10, "language_code": "en"},
            {"clorian_product_id": 11, "language_code": "pt"},
        ],
    )
    monkeypatch.setattr("app.services.mock_poller.load_existing_reservations", lambda _conn: {})

    staged, counts = generate_records(
        conn=None,
        seed=42,
        batch_size=8,
        update_ratio=0.0,
        unchanged_ratio=0.0,
        create_slot_reuse_probability=1.0,
        create_slot_pool_max_size=1,
    )

    assert counts["created"] == 8

    fingerprints = [
        (
            item["payload"]["tour"]["program_id"],
            item["payload"]["language_code"],
            item["payload"]["event_start_datetime"],
        )
        for item in staged
    ]

    assert len(set(fingerprints)) == 1