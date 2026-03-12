# [FDR-004] Auto Re-scheduling

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | FDR-004                |
| **Version**      | 2.0                    |
| **Status**       | Implemented            |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-03             |
| **Last Updated** | 2026-03-11             |

---

## 1. Purpose

When a reservation changes (date, time, language, or tour) or a guide becomes unavailable, the system must automatically re-evaluate and adjust schedules and guide assignments without manual intervention. This is the core automation that replaces the current fully manual scheduling process.

## 2. Scope

### In Scope

- Automatic re-scheduling when reservation details change
- Automatic guide replacement when a guide cancels
- Removing cancelled reservations from schedules
- Schedule lifecycle management (creation, updates, emptying)

### Out of Scope

- Initial schedule creation from new reservations (covered in guide assignment flow — [FDR-002])
- Capacity management (Clorian's responsibility)
- Manual overrides (covered in [FDR-002] FR-5)

## 3. Actors

| Actor | Description |
|-------|-------------|
| **Re-scheduling Service** | Automated service that reacts to domain events and adjusts schedules |
| **Guide Assignment Service** | Called by re-scheduling service to find a replacement guide |
| **Notification Service** | Dispatches notifications for every change (see [FDR-003]) |

## 4. Functional Requirements

### FR-1: Re-schedule on reservation date/time change

- **Description**: When a reservation's `event_start_datetime` changes (detected during Clorian ingestion), remove the reservation from its current schedule and place it in a matching schedule.
- **Trigger**: `ReservationTimeChanged` domain event (from [FDR-001] FR-3)
- **Input**: Reservation with new `event_start_datetime`
- **Process**:
  1. Remove reservation from current schedule (`reservations.schedule_id = NULL`)
  2. Search for an existing schedule matching: same `tour_id` + same `language_code` + same new timeslot
  3. If matching schedule found → add reservation to it
  4. If no matching schedule → create a new schedule and trigger guide assignment ([FDR-002])
  5. If old schedule has no remaining reservations → set old schedule `status = 'CANCELLED'`
- **Acceptance Criteria**:
  - Reservation is moved to the correct schedule
  - Old schedule is cleaned up if empty
  - Notifications sent to affected guides and admins ([FDR-003] FR-4)

### FR-2: Re-schedule on reservation language change

- **Description**: When a reservation's `language_code` changes (propagated from a Clorian purchase update), the reservation must be re-evaluated for schedule compatibility.
- **Trigger**: `ReservationLanguageChanged` domain event (from [FDR-001] FR-2)
- **Input**: Reservation with new `language_code`
- **Process**:
  1. Remove reservation from current schedule
  2. Search for a schedule matching: same `tour_id` + new `language_code` + same timeslot
  3. If found → add reservation; if not → create new schedule + assign guide
  4. Clean up old schedule if empty
- **Acceptance Criteria**:
  - Reservation moved to a language-compatible schedule
  - New guide speaks the new language
  - Notifications sent

### FR-3: Re-schedule on reservation tour change

- **Description**: When a reservation's tour changes (different `productId` from Clorian), move it to a schedule for the new tour.
- **Trigger**: `ReservationTourChanged` domain event (from [FDR-001] FR-3)
- **Input**: Reservation with new `tour_id`
- **Process**:
  1. Remove from current schedule
  2. Search for schedule matching: new `tour_id` + same `language_code` + same timeslot
  3. If found → add; if not → create new schedule + assign guide qualified for the new tour
  4. Clean up old schedule if empty
- **Acceptance Criteria**:
  - Reservation placed in a schedule for the correct tour
  - Assigned guide is qualified for the new tour
  - Notifications sent

### FR-4: Remove cancelled reservations from schedule

- **Description**: When a reservation is cancelled, remove it from its schedule.
- **Trigger**: `ReservationCancelled` domain event (from [FDR-001] FR-5)
- **Input**: Cancelled reservation
- **Process**:
  1. Set `reservations.schedule_id = NULL`
  2. If the schedule has no remaining active reservations → set schedule `status = 'CANCELLED'`, unassign guide
  3. Notify affected guide and admins
- **Acceptance Criteria**:
  - Cancelled reservation no longer belongs to any schedule
  - Empty schedules are cancelled
  - Guide notified of reduced/cancelled schedule

### FR-5: Auto-replace guide when guide cancels

- **Description**: When a guide becomes unavailable for an assigned schedule, automatically find and assign a replacement.
- **Trigger**: `GuideCancelled` event (triggered by admin action or guide self-service)
- **Input**: Schedule ID where guide is being removed
- **Process**:
  1. Unassign current guide from schedule (`schedule.guide_id = NULL`, `status = 'UNASSIGNED'`)
  2. Log unassignment in `tour_assignment_logs` with `action = 'UNASSIGNED'`
  3. Run guide assignment ([FDR-002]) with the same constraints: tour + language + timeslot
  4. If a replacement is found → assign and log with `action = 'REASSIGNED'`
  5. If no replacement found → set schedule `status = 'UNASSIGNABLE'`, notify admins urgently
- **Acceptance Criteria**:
  - Old guide unassigned and notified
  - New guide assigned (if available) and notified
  - If no guide available, admins receive urgent notification ([FDR-003] FR-5)
  - Full audit trail in `tour_assignment_logs`

### FR-6: Schedule matching criteria

- **Description**: Defines how the system determines if a reservation can be placed in an existing schedule.
- **Matching Criteria** — a reservation matches a schedule when ALL of the following are true:
  1. **Same tour**: `reservations.tour_id = schedule.tour_id`
  2. **Same language**: `reservations.language_code = schedule.language_code`
  3. **Same timeslot**: `reservations.event_start_datetime = schedule.event_start_datetime`
  4. **Schedule is active**: `schedule.status` IN (`UNASSIGNED`, `ASSIGNED`)
- **Acceptance Criteria**:
  - Reservations are only grouped with compatible schedules
  - No reservation is placed in a schedule with mismatched tour, language, or time

## 5. Data Model Impact

| Table | Impact |
|-------|--------|
| `reservations` | `schedule_id` updated (set or cleared) |
| `schedule` | New rows created; `status` updated; `guide_id` updated |
| `tour_assignment_logs` | Audit entries for every guide change |
| `notifications` | Notifications dispatched for every change |

## 6. Event Flow Diagram

```
Clorian Poll
    │
    ├── ReservationTimeChanged ──────► Re-scheduling Service
    ├── ReservationTourChanged ──────► Re-scheduling Service
    ├── ReservationLanguageChanged ──► Re-scheduling Service
    ├── ReservationCancelled ────────► Re-scheduling Service
    │                                       │
    │                                       ├── Remove from old schedule
    │                                       ├── Find/create matching schedule
    │                                       ├── Trigger Guide Assignment (FDR-002)
    │                                       └── Dispatch Notifications (FDR-003)
    │
Admin/Guide Action
    │
    └── GuideCancelled ──────────────► Re-scheduling Service
                                            │
                                            ├── Unassign guide
                                            ├── Find replacement (FDR-002)
                                            └── Dispatch Notifications (FDR-003)
```

## 7. Error Handling

| Scenario | Expected Behavior | HTTP Status |
|----------|-------------------|-------------|
| No matching schedule and guide assignment fails | Create schedule with `status = 'UNASSIGNABLE'`, notify admins | N/A |
| Reservation references a schedule that no longer exists | Log warning, treat as new reservation needing scheduling | N/A |
| Multiple reservations change simultaneously | Process sequentially within the same poll batch | N/A |
| Re-scheduling service unavailable | Events queued for retry | N/A |

## 8. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| [FDR-001] Reservation Ingestion | Internal | Produces domain events that trigger re-scheduling |
| [FDR-002] Guide Assignment | Internal | Called to assign/reassign guides |
| [FDR-003] Notifications | Internal | Called to notify on every change |

## 9. Open Questions

| # | Question | Answer | Status |
|---|----------|--------|--------|
| 1 | Should re-scheduling be synchronous (within the poll) or async (event queue)? | Synchronous within poll batch for MVP | Resolved |
| 2 | What happens if a reservation changes multiple attributes at once (e.g., time + tour)? | Process as a single re-schedule using new values | Resolved |
| 3 | Should there be a cool-down period to batch rapid changes? | No cool-down for MVP; changes processed sequentially per poll batch | Resolved |
| 4 | When a schedule becomes empty, should it be hard-deleted or soft-deleted? | Soft-delete (`status = 'CANCELLED'`) | Resolved |

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-03 | Evandro Maciel | Initial draft — re-scheduling on booking changes + guide cancellation |
| 1.1     | 2026-03-03 | Evandro Maciel | Renamed bookings→reservations; updated all event names to Reservation*; language change now from reservation directly |
| 2.0     | 2026-03-11 | Evandro Maciel | Implemented: rescheduling service, poller listener change detection, guide cancellation endpoint, notifications |
