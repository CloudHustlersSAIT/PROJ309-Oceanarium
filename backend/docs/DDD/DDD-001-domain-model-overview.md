# [DDD-001] Domain Model Overview

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | DDD-001                |
| **Version**      | 3.0                    |
| **Status**       | Draft                  |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-03             |
| **Last Updated** | 2026-03-03             |

---

## 1. Domain Overview

The Oceanarium system manages tour reservations that originate from an external ticketing platform (Clorian), assigns qualified guides to scheduled tours, and tracks availability, feedback, notifications, and operational sync metrics.

The system is **not** the source of truth for ticket sales — Clorian is. The Oceanarium backend is the source of truth for **guide assignment**, **scheduling**, **notifications**, and **operational orchestration**.

### Problem Statement

Currently, the Oceanarium handles all post-sale operations manually:
- Creating schedules
- Assigning reservations to schedules
- Organizing reservations by language, expertise, and timeslot
- Searching for and matching guides

### What We Solve

- Auto-schedule one guide for many reservations (each reservation can have many tickets: adults, children)
- Auto-replace a guide when they can't make an assigned tour
- Auto-reassign reservations when they change (date/time, language, tour)
- Auto-remove cancelled reservations from schedules
- Notify admins and guides of every change (portal + email)

### What We Don't Handle

- Capacity control per schedule (Clorian's responsibility)
- Resource management for tours (future phase)

## 2. Ubiquitous Language

| Term | Definition |
|------|-----------|
| **Customer** | A person who purchases tickets through Clorian, identified by `clientId` |
| **Reservation** | Maps to a Clorian Reservation — a specific tour at a specific time; the **schedulable unit**. Carries `language_code` denormalized from the Clorian Purchase. |
| **Reservation Version** | An immutable snapshot of a reservation's state; used for change detection via `hash` |
| **Ticket** | An individual attendee within a reservation (e.g., "Children 6–10 years", "Adult"); maps to a Clorian Ticket |
| **Schedule** | An internal grouping of N reservations that share the same tour, language, and timeslot; assigned to exactly one guide |
| **Guide** | A tour guide employed by the Oceanarium with language capabilities, availability, and tour qualifications |
| **Tour** | A predefined tour program (e.g., "Ocean Discovery Tour") mapped from Clorian's `productId` |
| **Assignment** | The act of linking a guide to a schedule based on three hard constraints |
| **Availability Pattern** | A guide's recurring weekly availability template |
| **Availability Exception** | A date-specific override (holiday, sick day, etc.) |
| **Poll Execution** | A single run of the Clorian polling job |
| **Survey** | Post-tour feedback from a customer about a guide |
| **Notification** | A message sent to an admin or guide via portal or email about a scheduling change |

> **Deprecated terms**: "Booking" (was ambiguous — meant both reservation and ticket). Use "Reservation" for the schedulable unit, "Ticket" for individual attendees.

## 3. Bounded Contexts

```mermaid
graph TB
    subgraph External
        CLORIAN[Clorian Ticketing]
    end

    subgraph Oceanarium
        SYNC[Sync / Operational Context]
        RESERVATION[Reservation Context]
        SCHEDULING[Scheduling Context]
        GUIDE[Guide Context]
        AVAILABILITY[Availability Context]
        FEEDBACK[Feedback Context]
        NOTIFICATION[Notification Context]
        AUTH[Auth Context]
    end

    CLORIAN -->|purchases, reservations, tickets via polling| SYNC
    SYNC -->|ingested data| RESERVATION
    RESERVATION -->|reservation events| SCHEDULING
    GUIDE -->|qualified guides| SCHEDULING
    AVAILABILITY -->|time slots| SCHEDULING
    SCHEDULING -->|assignment events| NOTIFICATION
    SCHEDULING -->|completed tours| FEEDBACK
    AUTH -->|admin actions| SCHEDULING
    NOTIFICATION -->|portal + email| GUIDE
    NOTIFICATION -->|portal + email| AUTH
```

### Context Responsibilities

| Context | Responsibility | Key Entities |
|---------|---------------|--------------|
| **Reservation** | Owns customer, reservation, and ticket data ingested from Clorian | `customers`, `reservations`, `reservation_versions`, `tickets` |
| **Scheduling** | Groups reservations into schedules, assigns guides, handles re-scheduling | `schedule`, `tour_assignment_logs` |
| **Guide** | Manages guide profiles, qualifications, and language capabilities | `guides`, `languages`, `guide_languages`, `guide_tour_types` |
| **Availability** | Defines and queries guide availability | `availability_patterns`, `availability_slots`, `availability_exceptions` |
| **Feedback** | Collects post-tour surveys | `surveys` |
| **Notification** | Dispatches portal and email notifications to admins and guides | `notifications` |
| **Sync / Operational** | Orchestrates Clorian polling and tracks sync health | `poll_execution`, `sync_logs` |
| **Auth** | User authentication and authorization | `users` |

## 4. Aggregates

### Aggregate: Reservation

- **Root Entity**: `reservations`
- **Value Objects**: `reservation_versions` (immutable snapshots)
- **Children**: `tickets` (via `reservation_id`)
- **Invariants**:
  - A reservation must have exactly one `clorian_reservation_id` (unique)
  - Versions are append-only; existing versions are never mutated
  - The "current" version is the one with the latest `valid_from`
  - A reservation belongs to at most one schedule
  - `language_code` is required (denormalized from Clorian Purchase)

### Aggregate: Schedule

- **Root Entity**: `schedule`
- **Invariants**:
  - A schedule must have exactly one guide (or be in `UNASSIGNED` / `UNASSIGNABLE` state)
  - All reservations in a schedule must share the same `tour_id`, `language_code`, and `event_start_datetime`
  - A guide cannot be assigned to overlapping schedules
  - Status transitions: `UNASSIGNED` → `ASSIGNED` → `COMPLETED` or `CANCELLED`

### Aggregate: Guide

- **Root Entity**: `guides`
- **Value Objects**: language capabilities (`guide_languages`), tour qualifications (`guide_tour_types`)
- **Invariants**:
  - A guide must be `is_active = true` to receive new assignments
  - Guide qualifications and language skills must be set before assignment

### Aggregate: Availability

- **Root Entity**: `availability_patterns`
- **Value Objects**: `availability_slots`, `availability_exceptions`
- **Invariants**:
  - Slots within the same pattern must not overlap
  - An exception on a specific date overrides the recurring slot for that day

## 5. Domain Events

| Event | Trigger | Consumers | Reference |
|-------|---------|-----------|-----------|
| `ReservationIngested` | New reservation from Clorian | Scheduling Context | FDR-001 |
| `ReservationTimeChanged` | `event_start_datetime` changed | Re-scheduling Service | FDR-004 FR-1 |
| `ReservationTourChanged` | `tour_id` changed | Re-scheduling Service | FDR-004 FR-3 |
| `ReservationLanguageChanged` | `language_code` changed (from purchase update) | Re-scheduling Service | FDR-004 FR-2 |
| `ReservationCancelled` | Status changed to `cancelled` | Re-scheduling Service | FDR-004 FR-4 |
| `ScheduleCreated` | Reservations grouped into a new schedule | Guide Assignment Service | FDR-002 |
| `GuideAssigned` | Guide linked to a schedule | Notification Service, Audit Logger | FDR-003 FR-1 |
| `GuideReassigned` | Guide replaced on a schedule | Notification Service, Audit Logger | FDR-003 FR-2 |
| `GuideUnassigned` | Guide removed from a schedule | Notification Service, Audit Logger | FDR-003 FR-2 |
| `GuideCancelled` | Guide marks unavailable for schedule | Re-scheduling Service | FDR-004 FR-5 |
| `ScheduleUnassignable` | No guide matches constraints | Notification Service (urgent) | FDR-003 FR-5 |
| `ReservationRemovedFromSchedule` | Reservation taken out of schedule | Notification Service | FDR-003 FR-3 |
| `ReservationMovedToSchedule` | Reservation moved between schedules | Notification Service | FDR-003 FR-4 |
| `PollCompleted` | Clorian polling cycle finished | Sync Logs | FDR-001 |
| `SurveySubmitted` | Customer submits feedback | Guide Rating Service | — |

## 6. Domain Services

| Service | Responsibility | References |
|---------|---------------|------------|
| **ClorianPollerService** | Executes polling, ingests 3-level data (purchases, reservations, tickets) | FDR-001 |
| **ReservationIngestionService** | Processes raw Clorian data, upserts entities, detects changes, emits events | FDR-001 |
| **ScheduleBuilderService** | Groups compatible reservations into schedules (same tour + language + timeslot) | FDR-004 FR-6 |
| **GuideAssignmentService** | Evaluates language + availability + expertise constraints, selects best guide | FDR-002 |
| **ReSchedulingService** | Reacts to reservation/guide changes, adjusts schedules and reassigns guides | FDR-004 |
| **NotificationService** | Dispatches portal + email notifications to admins and guides | FDR-003 |
| **AvailabilityQueryService** | Resolves guide availability for a given date/time considering patterns + exceptions | FDR-002 FR-2 |

## 7. Repository Interfaces

| Repository | Aggregate | Key Operations |
|-----------|-----------|----------------|
| `CustomerRepository` | Customer | `upsert_by_client_id()` |
| `ReservationRepository` | Reservation | `find_by_clorian_id()`, `create()`, `add_version()`, `update_schedule()` |
| `TicketRepository` | Ticket | `find_by_clorian_ticket_id()`, `create()`, `update()` |
| `ScheduleRepository` | Schedule | `find_matching(tour_id, language_code, event_start)`, `find_unassigned()`, `assign_guide()`, `cancel()` |
| `GuideRepository` | Guide | `find_eligible(tour_id, language_code, date, time_range)` |
| `AvailabilityRepository` | Availability | `get_patterns(guide_id)`, `get_exceptions(guide_id, date)` |
| `NotificationRepository` | Notification | `create()`, `mark_sent()`, `find_by_user()` |
| `SurveyRepository` | Survey | `create()`, `find_by_guide()` |

## 8. Context Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL                                   │
│  ┌──────────┐                                                       │
│  │ Clorian  │──── Polling (ACL) ────┐                               │
│  │ Purchase │                       │                               │
│  │ Reserv.  │                       │                               │
│  │ Ticket   │                       │                               │
│  └──────────┘                       │                               │
└─────────────────────────────────────┼───────────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      OCEANARIUM SYSTEM                               │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐           │
│  │    Sync /    │───▶│ Reservation  │───▶│  Scheduling  │           │
│  │ Operational  │    │   Context    │    │   Context    │           │
│  │              │    │              │    │              │           │
│  │ poll_exec    │    │ customers    │    │ schedule     │           │
│  │ sync_logs    │    │ reservations │    │ assignment   │           │
│  └──────────────┘    │ versions     │    │ logs         │           │
│                      │ tickets      │    └──────┬───────┘           │
│                      └──────────────┘           │                   │
│                                          ┌──────┴───────┐           │
│                                          │              │           │
│                           ┌──────────────┤              │           │
│                           │              │              │           │
│                           ▼              ▼              ▼           │
│                    ┌──────────────┐ ┌──────────┐ ┌─────────────┐   │
│                    │    Guide     │ │Availabil.│ │ Notification│   │
│                    │   Context    │ │ Context  │ │   Context   │   │
│                    │              │ │          │ │             │   │
│                    │ guides       │ │ patterns │ │ portal      │   │
│                    │ languages    │ │ slots    │ │ email       │   │
│                    │ guide_langs  │ │ except.  │ │             │   │
│                    │ guide_tours  │ └──────────┘ └─────────────┘   │
│                    └──────────────┘                                 │
│                                                                     │
│  ┌──────────────┐                     ┌──────────────┐             │
│  │   Feedback   │◀── after tour ─────│  Scheduling  │             │
│  │   Context    │                     │   Context    │             │
│  └──────────────┘                     └──────────────┘             │
│                                                                     │
│  ┌──────────────┐                                                   │
│  │     Auth     │──── admin actions ──▶ Scheduling + Notification   │
│  │   Context    │                                                   │
│  └──────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────┘

Integration Patterns:
  Clorian → Sync:               Anti-Corruption Layer (ACL) via polling
  Sync → Reservation:           Shared Kernel (same DB, direct writes)
  Reservation → Scheduling:     Domain Events (ReservationIngested, etc.)
  Scheduling → Notification:    Domain Events (GuideAssigned, etc.)
  Guide/Availability → Scheduling: Query interface (read-only)
```

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-03 | Evandro Maciel | Initial domain model — 7 bounded contexts |
| 2.0     | 2026-03-03 | Evandro Maciel | Added Purchase, Ticket, Notification contexts (8 total) |
| 3.0     | 2026-03-03 | Evandro Maciel | Renamed Booking→Reservation throughout; dropped Purchase aggregate (denormalized); deprecated "booking" in ubiquitous language; updated all events, services, and repositories |
