"""
Guide Profile languages: view and edit languages spoken by a guide.

Reads and updates guide_languages only; reads languages catalog.
Does not modify scheduler, guide_assignment, poller, or any other logic.
"""

from __future__ import annotations

from sqlalchemy import text

from .exceptions import NotFoundError, ValidationError


def get_guide_languages(conn, guide_id: int) -> dict:
    """
    Return the languages spoken by the guide for the profile page.
    Returns { "languages": [ { "id", "name", "code" }, ... ] }.
    """
    # Ensure guide exists (optional: return empty list if not found; we return 404 for consistency)
    guide = conn.execute(
        text("SELECT id FROM guides WHERE id = :guide_id"),
        {"guide_id": guide_id},
    ).fetchone()
    if not guide:
        raise NotFoundError("Guide not found")

    rows = conn.execute(
        text(
            """
            SELECT l.id, l.name, l.code
            FROM guide_languages gl
            JOIN languages l ON l.id = gl.language_id
            WHERE gl.guide_id = :guide_id
            ORDER BY l.name
            """
        ),
        {"guide_id": guide_id},
    ).fetchall()

    languages = [{"id": row[0], "name": row[1], "code": row[2]} for row in rows]
    return {"languages": languages}


def update_guide_languages(conn, guide_id: int, language_ids: list[int]) -> None:
    """
    Replace the guide's languages with the given list of language IDs.
    Validates guide and all language_ids exist. Single transaction: delete then insert, commit.
    """
    if not isinstance(language_ids, list):
        raise ValidationError("language_ids must be a list")

    # Ensure guide exists
    guide = conn.execute(
        text("SELECT id FROM guides WHERE id = :guide_id"),
        {"guide_id": guide_id},
    ).fetchone()
    if not guide:
        raise NotFoundError("Guide not found")

    # Normalize: unique integers only
    ids = list({int(x) for x in language_ids if x is not None and str(x).strip() != ""})
    # Validate each language_id exists in languages table
    for lid in ids:
        row = conn.execute(
            text("SELECT id FROM languages WHERE id = :lid"),
            {"lid": lid},
        ).fetchone()
        if not row:
            raise ValidationError(f"Language id {lid} not found in languages table")

    # Replace: delete all existing, insert new set
    conn.execute(
        text("DELETE FROM guide_languages WHERE guide_id = :guide_id"),
        {"guide_id": guide_id},
    )
    for lang_id in ids:
        conn.execute(
            text(
                """
                INSERT INTO guide_languages (guide_id, language_id)
                VALUES (:guide_id, :language_id)
                """
            ),
            {"guide_id": guide_id, "language_id": lang_id},
        )

    conn.commit()
