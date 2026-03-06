# [FDR-003] Notifications

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | FDR-003                |
| **Version**      | 1.1                    |
| **Status**       | Draft                  |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-03             |
| **Last Updated** | 2026-03-03             |

---

## 1. Purpose

Every scheduling change must be communicated to the relevant Admin and Guide through two channels: the Oceanarium portal (in-app) and email. This ensures no assignment change goes unnoticed and enables timely action.

## 2. Scope

### In Scope

- In-portal notifications (real-time or near-real-time)
- Email notifications
- Notification for Admins and Guides
- Notification lifecycle tracking (pending → sent → failed)

### Out of Scope

- Customer-facing notifications (Clorian handles customer communication)
- SMS or push notifications (future phase)
- Notification preferences / opt-out settings (future phase)

## 3. Actors

| Actor | Description |
|-------|-------------|
| **Notification Service** | Internal service that dispatches notifications across channels |
| **Admin** | Staff member who manages schedules — receives all scheduling notifications |
| **Guide** | Tour guide — receives notifications about their own assignments |

## 4. Functional Requirements

### FR-1: Notify on guide assignment

- **Description**: When a guide is assigned to a schedule (auto or manual), notify the guide and all admins.
- **Trigger**: `GuideAssigned` domain event
- **Recipients**: Assigned guide + all active admins
- **Channels**: Portal + Email
- **Message Content**:
  - Schedule date/time
  - Tour name
  - Language
  - Number of reservations / total tickets
  - Assignment type (auto/manual)
- **Acceptance Criteria**:
  - Guide receives portal + email notification
  - All active admins receive portal notification
  - `notifications` row created with `event_type = 'GUIDE_ASSIGNED'`

### FR-2: Notify on guide re-assignment

- **Description**: When a guide is replaced on a schedule (due to cancellation or manual override), notify both the old and new guide plus admins.
- **Trigger**: `GuideReassigned` domain event
- **Recipients**: Previous guide (unassigned) + new guide (assigned) + all active admins
- **Channels**: Portal + Email
- **Message Content**:
  - Reason for change (guide cancelled / manual override / reservation change)
  - Schedule details
  - For previous guide: "You have been removed from schedule X"
  - For new guide: "You have been assigned to schedule X"
- **Acceptance Criteria**:
  - Both guides notified
  - Admins notified
  - Two `notifications` rows: one for unassignment, one for assignment

### FR-3: Notify on reservation cancellation affecting a schedule

- **Description**: When a reservation is cancelled and removed from a schedule, notify the assigned guide and admins.
- **Trigger**: `ReservationRemovedFromSchedule` domain event
- **Recipients**: Assigned guide + all active admins
- **Channels**: Portal + Email
- **Message Content**:
  - Which reservation was cancelled
  - Updated schedule (remaining reservations, ticket count)
  - If schedule is now empty: "Schedule X has no remaining reservations"
- **Acceptance Criteria**:
  - Guide receives notification with updated schedule info
  - Admins notified
  - `notifications` row created with `event_type = 'RESERVATION_CANCELLED'`

### FR-4: Notify on reservation change causing re-scheduling

- **Description**: When a reservation changes (date, time, language, tour) and moves to a different schedule, notify the affected guides and admins.
- **Trigger**: `ReservationMovedToSchedule` domain event
- **Recipients**: Guide of old schedule + guide of new schedule + all active admins
- **Channels**: Portal + Email
- **Message Content**:
  - What changed (date/time/language/tour)
  - Old schedule → new schedule
  - Impact on both schedules
- **Acceptance Criteria**:
  - Both affected guides notified
  - Admins notified
  - `notifications` rows created for each recipient

### FR-5: Notify on unassignable schedule

- **Description**: When no guide matches all constraints for a schedule, alert admins.
- **Trigger**: `ScheduleUnassignable` domain event
- **Recipients**: All active admins
- **Channels**: Portal + Email
- **Message Content**:
  - Schedule details
  - Which constraints failed (no language match / no availability / no expertise)
  - Suggested action: manual assignment
- **Acceptance Criteria**:
  - All active admins receive urgent notification
  - `notifications` row created with `event_type = 'SCHEDULE_UNASSIGNABLE'`

### FR-6: Notification lifecycle

- **Description**: Track the status of every notification.
- **Business Rules**:
  - `status` transitions: `PENDING` → `SENT` or `FAILED`
  - Each channel (portal, email) creates its own `notifications` row
  - Failed email notifications should be retried up to 3 times
  - `sent_at` is set when the notification is successfully delivered
- **Acceptance Criteria**:
  - Every notification has a trackable lifecycle
  - Failed notifications are visible to admins in the portal

## 5. Data Model Impact

| Table | Impact |
|-------|--------|
| `notifications` | New row per notification per channel per recipient |
| `users` | Read — identify active admins |
| `guides` | Read — guide email for email notifications |
| `schedule` | Read — schedule details for notification content |

## 6. API Contracts

### `GET /notifications`

List notifications for the authenticated user (admin or guide).

**Response (200):**
```json
[
  {
    "id": 1,
    "event_type": "GUIDE_ASSIGNED",
    "message": "You have been assigned to Ocean Discovery Tour on Mar 15 at 10:00 (en)",
    "channel": "PORTAL",
    "status": "SENT",
    "created_at": "2026-03-10T14:30:00Z"
  }
]
```

### `PATCH /notifications/{id}/read`

Mark a portal notification as read.

## 7. Error Handling

| Scenario | Expected Behavior | HTTP Status |
|----------|-------------------|-------------|
| Email delivery failure | `status = 'FAILED'`, retry up to 3 times | N/A |
| Guide has no email configured | Log warning, send portal notification only | N/A |
| Notification service unavailable | Queue notifications for later delivery | N/A |

## 8. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Email service (SMTP/SES/SendGrid) | Infrastructure | For email delivery |
| [FDR-002] Guide Assignment | Internal | Produces assignment events |
| [FDR-004] Auto Re-scheduling | Internal | Produces rescheduling events |

## 9. Open Questions

| # | Question | Answer | Status |
|---|----------|--------|--------|
| 1 | Which email service to use? | TBD | Open |
| 2 | Should portal notifications be real-time (WebSocket) or polling? | TBD | Open |
| 3 | Should admins receive email for every change or just critical ones? | TBD | Open |
| 4 | Notification templates — managed in code or DB? | TBD | Open |

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-03 | Evandro Maciel | Initial draft — portal + email for admin and guide |
| 1.1     | 2026-03-03 | Evandro Maciel | Renamed bookings→reservations throughout; updated event names |
