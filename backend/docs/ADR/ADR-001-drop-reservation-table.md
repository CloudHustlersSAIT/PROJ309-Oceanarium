# [ADR-001] Drop Reservation Table — Clorian Reservation Maps to Bookings

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | ADR-001                |
| **Version**      | 1.1                    |
| **Status**       | Accepted               |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-03             |
| **Last Updated** | 2026-03-03             |

---

## Context

The original schema considered a `reservation` table sitting between `bookings` (external data from Clorian) and `schedule` (internal guide assignments). The proposed data flow was:

```
Clorian ticket → booking → reservation (1:1) → schedule (N:1)
```

After analyzing the actual Clorian API payloads (see [FDR-001]), we confirmed that Clorian's data model is:

```
Purchase (customer transaction)
  └── Reservation (a tour/product at a specific time)
        └── Ticket (individual attendee)
```

The Clorian **Reservation** is the schedulable unit — it represents a group booking for a specific tour at a specific time. This maps directly to what we need in our `bookings` table. A separate `reservation` table would be a 1:1 duplicate.

We already have:
- **`purchases`** — maps to Clorian Purchase (carries `language_code`, customer link)
- **`bookings`** — maps to Clorian Reservation (tour, time, status, schedule link)
- **`booking_versions`** — immutable version history with `hash`-based change detection
- **`tickets`** — maps to Clorian Ticket (individual attendees)

## Decision

**Clorian's "Reservation" maps directly to our `bookings` table. No separate `reservation` table needed.**

The relationship is:

```
customers 1──N purchases 1──N bookings 1──N tickets
                                  │
                                  N
                                  │
                                  1
                               schedule N──1 guides
```

- `bookings.schedule_id` FK → `schedule.id` (N bookings → 1 schedule)
- `schedule.guide_id` FK → `guides.id` (1 guide per schedule)

## Options Considered

### Option A: Keep reservation table (booking → reservation 1:1 → schedule N:1)

- **Pros**:
  - Clean separation between external (booking) and internal (reservation) concepts
  - Future flexibility if reservation gains its own lifecycle
- **Cons**:
  - 1:1 mapping with no additional attributes — pure indirection
  - Extra JOIN on every query
  - More code to maintain
  - Violates YAGNI

### Option B: Clorian Reservation = our bookings (chosen)

- **Pros**:
  - Natural mapping to Clorian's actual data model
  - Simpler: fewer tables, fewer JOINs
  - `booking_versions` provides the audit trail
  - `tickets` as a child table captures individual attendees
  - Easy to introduce a reservation layer later if needed
- **Cons**:
  - Tighter coupling between external data identity and internal scheduling
  - If reservation gains independent business rules, a refactor is needed

## Consequences

### Positive

- Clean 3-level mapping: Purchase → Booking → Ticket mirrors Clorian's Purchase → Reservation → Ticket
- `language_code` lives on `purchases` (where Clorian puts it), accessed via JOIN
- Fewer tables, faster queries
- `booking_versions` + `hash` enables change detection without a separate entity

### Negative

- If reservation-specific business logic emerges (e.g., internal approval step), extraction would require a migration

### Risks

- Low risk: extracting a reservation layer later is a straightforward add-table + backfill migration

## Related

- [FDR-001] Booking Ingestion from Clorian — Clorian payload structure and field mapping
- [FDR-002] Guide Assignment Rules
- [FDR-004] Auto Re-scheduling
- [DDD-001] Domain Model Overview
- [DB] ERD (`backend/docs/db/ERD.md`)

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-03 | Evandro Maciel | Initial proposal — drop reservation table |
| 1.1     | 2026-03-03 | Evandro Maciel | Confirmed with Clorian payload analysis: Reservation = bookings; status changed to Accepted |
