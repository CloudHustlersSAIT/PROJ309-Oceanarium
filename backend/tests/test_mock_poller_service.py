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
        create_slot_reuse_probability=1.0,
        create_slot_pool_max_size=4,
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


def test_generate_records_biases_english_over_other_languages(monkeypatch):
    monkeypatch.setattr(
        "app.services.mock_poller.load_tours",
        lambda _conn: [
            {"id": 1, "clorian_product_id": 10, "name": "Main", "description": "Main", "duration": 90},
            {"id": 2, "clorian_product_id": 11, "name": "Deep", "description": "Deep", "duration": 60},
            {"id": 3, "clorian_product_id": 12, "name": "Reef", "description": "Reef", "duration": 75},
        ],
    )
    monkeypatch.setattr(
        "app.services.mock_poller.load_guide_capabilities",
        lambda _conn: [
            {"clorian_product_id": 10, "language_code": "en"},
            {"clorian_product_id": 11, "language_code": "en"},
            {"clorian_product_id": 12, "language_code": "en"},
            {"clorian_product_id": 10, "language_code": "pt"},
            {"clorian_product_id": 10, "language_code": "es"},
            {"clorian_product_id": 11, "language_code": "fr"},
            {"clorian_product_id": 12, "language_code": "zh"},
        ],
    )
    monkeypatch.setattr("app.services.mock_poller.load_existing_reservations", lambda _conn: {})

    staged, counts = generate_records(
        conn=None,
        seed=42,
        batch_size=150,
        update_ratio=0.0,
        unchanged_ratio=0.0,
        create_slot_reuse_probability=0.0,
    )

    assert counts["created"] == 150

    language_counts: dict[str, int] = {}
    for item in staged:
        language_code = item["payload"]["language_code"]
        language_counts[language_code] = language_counts.get(language_code, 0) + 1

    assert language_counts["en"] >= language_counts.get("pt", 0)
    assert language_counts["en"] >= language_counts.get("es", 0)
    assert language_counts["en"] >= language_counts.get("fr", 0)
    assert language_counts["en"] > language_counts.get("zh", 0)


def test_generate_records_english_bias_survives_skewed_guide_caps(monkeypatch):
    monkeypatch.setattr(
        "app.services.mock_poller.load_tours",
        lambda _conn: [
            {"id": 1, "clorian_product_id": 10, "name": "Main", "description": "Main", "duration": 90},
            {"id": 2, "clorian_product_id": 11, "name": "Deep", "description": "Deep", "duration": 60},
            {"id": 3, "clorian_product_id": 12, "name": "Reef", "description": "Reef", "duration": 75},
        ],
    )
    monkeypatch.setattr(
        "app.services.mock_poller.load_guide_capabilities",
        lambda _conn: [
            {"clorian_product_id": 10, "language_code": "en"},
            {"clorian_product_id": 11, "language_code": "pt"},
            {"clorian_product_id": 12, "language_code": "pt"},
            {"clorian_product_id": 10, "language_code": "pt"},
            {"clorian_product_id": 11, "language_code": "pt"},
            {"clorian_product_id": 12, "language_code": "pt"},
            {"clorian_product_id": 10, "language_code": "es"},
            {"clorian_product_id": 11, "language_code": "es"},
            {"clorian_product_id": 12, "language_code": "fr"},
            {"clorian_product_id": 10, "language_code": "zh"},
        ],
    )
    monkeypatch.setattr("app.services.mock_poller.load_existing_reservations", lambda _conn: {})

    staged, counts = generate_records(
        conn=None,
        seed=42,
        batch_size=250,
        update_ratio=0.0,
        unchanged_ratio=0.0,
        create_slot_reuse_probability=0.0,
    )

    assert counts["created"] == 250

    language_counts: dict[str, int] = {}
    for item in staged:
        language_code = item["payload"]["language_code"]
        language_counts[language_code] = language_counts.get(language_code, 0) + 1

    assert language_counts["en"] >= language_counts.get("pt", 0)
    assert language_counts["en"] >= language_counts.get("es", 0)
    assert language_counts["en"] >= language_counts.get("fr", 0)
    assert language_counts["en"] > language_counts.get("zh", 0)
