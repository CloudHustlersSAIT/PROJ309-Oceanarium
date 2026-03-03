# [FDR-002] Guide Assignment Rules

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | FDR-002                |
| **Version**      | 2.0                    |
| **Status**       | Draft                  |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-03             |
| **Last Updated** | 2026-03-03             |

---

## 1. Purpose

Every schedule (a group of N reservations sharing the same tour, timeslot, and language) must be assigned exactly one guide. The assignment must satisfy three hard constraints: **language**, **availability**, and **expertise**. This document defines the rules, priority, and fallback behavior for guide assignment.

## 2. Scope

### In Scope

- Automatic guide assignment when a schedule is created or updated
- Validation of the three hard constraints (language, availability, expertise)
- Manual override by admin
- Audit logging of assignments

### Out of Scope

- Guide on-boarding/profile management (CRUD operations on `guides`)
- Customer-facing guide selection
- Guide performance scoring algorithm
- Re-scheduling logic (see [FDR-004])
- Notifications (see [FDR-003])

## 3. Actors

| Actor | Description |
|-------|-------------|
| **Assignment Service** | Automated service that evaluates constraints and assigns guides |
| **Admin** | Staff member who can manually assign or override guide assignments |
| **Guide** | Tour guide whose availability and qualifications are checked |

## 4. Functional Requirements

### FR-1: Language Constraint (hard requirement)

- **Description**: The assigned guide must speak the language requested by the customer at the time of ticket purchase through Clorian.
- **Input**: `reservations.language_code` (denormalized from Clorian Purchase) → matched against guide's language capabilities via `guide_languages` → `languages`
- **Output**: Filtered list of guides who speak the required language
- **Business Rules**:
  - `language_code` originates from the Clorian Purchase payload and is denormalized onto `reservations` (see [FDR-001] §4.1)
  - It is propagated to `schedule.language_code` when a schedule is created
  - A guide's language capabilities are stored in `guide_languages` (junction of `guides` ↔ `languages`)
  - If no guide speaks the requested language, the schedule is flagged as `UNASSIGNABLE` with reason `NO_LANGUAGE_MATCH`
- **Acceptance Criteria**:
  - Only guides who speak `schedule.language_code` are considered as candidates
  - A schedule with no language-matching guide is not auto-assigned
  - Notification sent to admins when unassignable (see [FDR-003] FR-5)

### FR-2: Availability Constraint (hard requirement)

- **Description**: The assigned guide must be available during the schedule's time window.
- **Input**: `schedule.event_start_datetime`, `schedule.event_end_datetime`
- **Output**: Filtered list of guides available at the required time
- **Business Rules**:
  - Guide availability is defined by `availability_patterns` → `availability_slots` (recurring weekly) and `availability_exceptions` (date-specific overrides)
  - A guide is **available** if:
    1. The schedule's day-of-week falls within an `availability_slots.day_of_week` for an active pattern
    2. The schedule's time range falls within `availability_slots.start_time` — `end_time`
    3. No `availability_exceptions` of type `BLOCKED` exists for that date
  - A guide is **unavailable** if already assigned to another overlapping schedule
  - Time zone is resolved via `availability_patterns.timezone`
- **Acceptance Criteria**:
  - Guides with conflicting schedules are excluded
  - Guides with `BLOCKED` exceptions on the date are excluded
  - Guides whose weekly slots don't cover the time window are excluded

### FR-3: Expertise Constraint (hard requirement)

- **Description**: The assigned guide must be qualified to lead the specific tour type.
- **Input**: `schedule.tour_id` → matched against `guide_tour_types`
- **Output**: Filtered list of guides trained for this tour
- **Business Rules**:
  - `guide_tour_types` is a junction table linking `guides.id` ↔ `tours.id`
  - A guide is qualified if a row exists in `guide_tour_types` for the given `(guide_id, tour_id)` pair
  - Only active guides (`guides.is_active = true`) are considered
- **Acceptance Criteria**:
  - Only guides with a matching `guide_tour_types` entry are considered
  - Inactive guides are never assigned

### FR-4: Assignment Priority (soft preference)

- **Description**: When multiple guides satisfy all three hard constraints, select the best candidate.
- **Input**: List of eligible guides after filtering
- **Output**: Single guide selected for the schedule
- **Business Rules**:
  - Priority order (highest to lowest):
    1. **Fewest assignments that day** — distribute workload evenly
    2. **Highest `guide_rating`** — prefer better-rated guides
    3. **Deterministic tiebreaker** — lowest `guide.id` to ensure consistency
- **Acceptance Criteria**:
  - The guide with the fewest same-day assignments is preferred
  - Ties are broken by rating, then by ID

### FR-5: Manual Override

- **Description**: An admin can manually assign a guide to a schedule, bypassing the automatic rules.
- **Input**: `schedule_id`, `guide_id`, `assigned_by` (admin username)
- **Output**: Updated `schedule.guide_id`, new `tour_assignment_logs` entry
- **Business Rules**:
  - Manual assignment is logged with `assignment_type = 'MANUAL'` in `tour_assignment_logs`
  - The system should **warn** (not block) if the manually assigned guide violates a constraint
  - Notification sent to the assigned guide (see [FDR-003] FR-1)
- **Acceptance Criteria**:
  - Admin can override even if constraints are violated (with a warning)
  - An audit log entry is always created
  - Guide and admins notified

### FR-6: Audit Trail

- **Description**: Every guide assignment (auto or manual) is recorded.
- **Input**: Assignment details
- **Output**: `tour_assignment_logs` row
- **Business Rules**:
  - `assignment_type`: `AUTO` or `MANUAL`
  - `action`: `ASSIGNED`, `REASSIGNED`, `UNASSIGNED`
  - `assigned_by`: service name for auto, admin username for manual
  - References `schedule_id` for precise tracking
- **Acceptance Criteria**:
  - Every assignment change produces exactly one log entry
  - Logs are immutable (append-only)

## 5. Data Model Impact

| Table | Impact |
|-------|--------|
| `schedule` | `guide_id` and `status` set during assignment |
| `guides` | Read — filter by `is_active` |
| `guide_languages` | Read — match against `schedule.language_code` |
| `languages` | Read — resolve language code to language ID |
| `guide_tour_types` | Read — verify guide is qualified for `schedule.tour_id` |
| `availability_patterns` / `slots` / `exceptions` | Read — check guide availability |
| `tour_assignment_logs` | Write — audit trail for every assignment |
| `notifications` | Write — dispatched via [FDR-003] |

## 6. API Contracts

### `POST /schedules/{schedule_id}/assign`

Auto-assign a guide to a schedule.

**Response (200):**
```json
{
  "schedule_id": 10,
  "guide_id": 3,
  "guide_name": "Maria Silva",
  "assignment_type": "AUTO",
  "constraints_met": {
    "language": true,
    "availability": true,
    "expertise": true
  }
}
```

### `PUT /schedules/{schedule_id}/assign`

Manual override by admin.

**Request:**
```json
{
  "guide_id": 7,
  "reason": "Customer requested specific guide"
}
```

**Response (200):**
```json
{
  "schedule_id": 10,
  "guide_id": 7,
  "assignment_type": "MANUAL",
  "warnings": ["Guide does not speak requested language: pt-BR"]
}
```

## 7. Error Handling

| Scenario | Expected Behavior | HTTP Status |
|----------|-------------------|-------------|
| No guide matches all three constraints | Return `UNASSIGNABLE` with reasons; notify admins | 422 |
| Schedule already has a guide assigned | Reassign and log as `REASSIGNED` | 200 |
| Guide ID does not exist | Return error | 404 |
| Guide is inactive | Return error | 400 |
| Schedule does not exist | Return error | 404 |

## 8. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| [FDR-001] Reservation Ingestion | Internal | Reservations must be ingested first |
| [FDR-003] Notifications | Internal | Dispatches notifications on assignment |
| `schedule` table | Data | Must exist with `tour_id`, `language_code`, `event_start_datetime` |
| `availability_*` tables | Data | Must be populated with guide schedules |
| `guide_tour_types` | Data | Must be populated with qualifications |
| `guide_languages` + `languages` | Data | Must be populated with guide language capabilities |

## 9. Open Questions

| # | Question | Answer | Status |
|---|----------|--------|--------|
| 1 | Should auto-assignment run immediately when a schedule is created, or in batch? | TBD | Open |
| 2 | How is guide-language association stored? | `guide_languages` junction table | Resolved |
| 3 | Should constraint violations on manual override be warnings or soft-blocks? | Warnings (proposed) | Open |
| 4 | What is the maximum number of reservations per schedule? | Controlled by Clorian capacity, not us | Resolved |

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-03 | Evandro Maciel | Initial draft — three hard constraints + priority rules |
| 1.1     | 2026-03-03 | Evandro Maciel | Language via `purchases.language_code`; linked to FDR-003/004 |
| 2.0     | 2026-03-03 | Evandro Maciel | Renamed bookings→reservations; `language_code` now directly on `reservations` (no purchases table) |
