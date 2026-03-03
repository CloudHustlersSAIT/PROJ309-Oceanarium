# [ADR-001] Naming & Structure — Clorian Reservation = Our Reservations, No Purchases Table

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | ADR-001                |
| **Version**      | 2.0                    |
| **Status**       | Accepted               |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-03             |
| **Last Updated** | 2026-03-03             |

---

## Context

The team had significant naming confusion around "booking", "reservation", and "ticket":
- In the old system, a "booking" was treated as a single ticket/entry
- In Clorian's model, a "Reservation" is the group (N tickets), which is the schedulable unit
- A "Ticket" is an individual attendee within a reservation

After team discussion, we agreed:
- A **reservation** is the core entity — the thing we schedule
- A **ticket** is an individual attendee (adult, child, etc.) within a reservation
- A **schedule** groups N reservations with the same tour + language + timeslot

Clorian's 3-level hierarchy:
```
Purchase (customer transaction)
  └── Reservation (a tour/product at a specific time)  ← this is what we schedule
        └── Ticket (individual attendee)
```

We also questioned whether the `purchases` table adds value. Since `language_code` and `customer_id` can be denormalized onto `reservations`, the `purchases` table becomes unnecessary overhead.

## Decision

**1. Clorian Reservation maps to our `reservations` table (not "bookings").**

**2. Drop the `purchases` table. Denormalize `language_code`, `customer_id`, and `clorian_purchase_id` onto `reservations`.**

The data model is:

```
customers  1──N  reservations  1──N  tickets
                      │
                      N
                      │
                      1
                   schedule  N──1  guides
```

Key fields on `reservations`:
- `clorian_reservation_id` (UK) — maps to Clorian's `reservationId`
- `clorian_purchase_id` — denormalized from Purchase for traceability
- `customer_id` (FK) — denormalized from Purchase
- `language_code` — denormalized from Purchase; critical for guide assignment
- `schedule_id` (FK, nullable) — links N reservations → 1 schedule

## Options Considered

### Option A: Keep `bookings` name + separate `purchases` table

- **Pros**: Normalized, familiar name from original codebase
- **Cons**: "Booking" caused naming confusion with the team; `purchases` adds a JOIN with no unique domain value

### Option B: Rename to `reservations` + keep `purchases` table

- **Pros**: Clear naming, normalized
- **Cons**: `purchases` only carries `language_code` and `customer_id` — pure overhead for an extra JOIN on every scheduling query

### Option C: Rename to `reservations` + denormalize purchases (chosen)

- **Pros**:
  - Matches Clorian's terminology and team's mental model
  - "Reservation" is unambiguous — it's the schedulable unit, not a ticket
  - No extra table or JOIN for the most common queries
  - `clorian_purchase_id` kept for traceability without a separate table
- **Cons**:
  - If a purchase's `language_code` changes, all linked reservations must be updated (rare, handled during polling)
  - Slight denormalization trade-off

## Consequences

### Positive

- Clear, unambiguous naming: reservation = schedulable unit, ticket = attendee
- Simpler model: `customers → reservations → tickets` (3 tables, no intermediate)
- Fewer JOINs on scheduling queries (language is directly on reservations)
- Team alignment — everyone agrees on what "reservation" means

### Negative

- Denormalized `language_code` means updating N reservation rows if a purchase's language changes (edge case)
- Renaming from `bookings` requires updating all existing code, tests, and docs

### Risks

- Low risk: if `purchases` is ever needed as a first-class entity, it can be extracted via a straightforward migration

## Related

- [FDR-001] Booking Ingestion from Clorian — Clorian payload structure
- [FDR-002] Guide Assignment Rules — uses `reservations.language_code`
- [FDR-004] Auto Re-scheduling
- [DDD-001] Domain Model Overview
- [DB] ERD v4.0

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-03 | Evandro Maciel | Initial proposal — drop reservation as separate table |
| 1.1     | 2026-03-03 | Evandro Maciel | Confirmed with Clorian payload: Reservation = bookings |
| 2.0     | 2026-03-03 | Evandro Maciel | Renamed `bookings`→`reservations`; dropped `purchases` table (denormalized onto reservations); updated title and scope |
