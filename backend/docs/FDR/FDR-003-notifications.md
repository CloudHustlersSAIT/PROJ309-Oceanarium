# [FDR-003] Notifications

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | FDR-003                |
| **Version**      | 5.0                    |
| **Status**       | Active                 |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-03             |
| **Last Updated** | 2026-03-17             |

---

## 1. Purpose

Every scheduling change must be communicated to the relevant Admin and Guide through two channels: the Oceanarium portal (in-app) and email. This ensures no assignment change goes unnoticed and enables timely action.

**Notifications are triggered via dedicated API endpoints, decoupling notification logic from domain services.** This API-first approach provides flexibility, testability, and clear separation of concerns between business logic and notification delivery.

## 2. Scope

### In Scope

- In-portal notifications (real-time or near-real-time)
- Email notifications via Resend.com
- Notification for Admins and Guides
- Notification lifecycle tracking (pending → sent → failed)
- User notification preferences per event type and channel
- Rich notification detail view with full context
- Priority levels and action-required flags
- Automatic retry for failed email notifications (max 3 attempts)
- **API-first notification triggering via dedicated POST endpoints**
- **Decoupled architecture: domain services independent of notification logic**
- **Manual notification triggering and retry capabilities**

### Out of Scope

- Customer-facing notifications (Clorian handles customer communication)
- SMS or push notifications (future phase)
- Real-time WebSocket notifications (using polling for MVP)

## 3. Actors

| Actor | Description |
|-------|-------------|
| **Notification Service** | REST API service that exposes endpoints to trigger notifications across channels. Domain services do not directly invoke notification logic. |
| **Frontend/Orchestrator** | Coordinates domain operations and notification triggers by calling respective API endpoints |
| **Admin** | Staff member who manages schedules — receives all scheduling notifications |
| **Guide** | Tour guide — receives notifications about their own assignments |

## 4. Functional Requirements

### FR-1: Notify on guide assignment

- **Description**: When a guide is assigned to a schedule (auto or manual), notify the guide and all admins.
- **Trigger**: `POST /notifications/guide-assigned` API call
- **Called By**: Backend route after guide assignment OR frontend/orchestrator
- **Request Body**:
  ```
  schedule_id: int (required)
  guide_id: int (required)
  assignment_type: "AUTO" | "MANUAL" (required)
  ```
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
- **Trigger**: Two separate API calls:
  1. `POST /notifications/guide-unassigned` for the removed guide
  2. `POST /notifications/guide-assigned` for the new guide
- **Request Body (unassigned)**:
  ```
  schedule_id: int (required)
  guide_id: int (required)
  reason: string (required)
  replacement_guide_id: int (optional)
  ```
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
- **Trigger**: `POST /notifications/schedule-changed` API call
- **Request Body**:
  ```
  schedule_id: int (required)
  change_type: "RESERVATION_CANCELLED" (required)
  change_details: string (required)
  affected_guide_id: int (optional)
  ```
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
- **Trigger**: `POST /notifications/schedule-changed` API call
- **Request Body**:
  ```
  schedule_id: int (required)
  change_type: "RESERVATION_MOVED" (required)
  change_details: string (required)
  affected_guide_id: int (optional)
  old_state: object (optional)
  new_state: object (optional)
  ```
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
- **Trigger**: `POST /notifications/schedule-unassignable` API call
- **Called By**: Backend route when auto-assignment fails OR frontend/orchestrator
- **Request Body**:
  ```
  schedule_id: int (required)
  reasons: list[string] (required)
  attempted_guides_count: int (optional)
  ```
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
  - All rows created for the same logical event share a `group_id` UUID, correlating PORTAL and EMAIL rows
  - The portal only displays PORTAL-channel notifications; the corresponding EMAIL status (`email_status`, `email_sent_at`) is embedded via a LEFT JOIN on `group_id`
  - Failed email notifications should be retried up to 3 times
  - `sent_at` is set when the notification is successfully delivered
- **Acceptance Criteria**:
  - Every notification has a trackable lifecycle
  - Portal shows only PORTAL notifications, with embedded email delivery status
  - Failed notifications are visible to admins in the portal

### FR-7: Notify on swap request received

- **Description**: When a guide creates a swap request, notify the candidate guide (the one being asked to take over) and all admins.
- **Trigger**: `POST /notifications/swap-request-received` API call, or called internally by `create_swap_request()` in the guide requests service
- **Request Body**:
  ```
  schedule_id: int (required)
  candidate_guide_id: int (required)
  requesting_guide_id: int (required)
  ```
- **Recipients**: Candidate guide (PORTAL + EMAIL) + all active admins (PORTAL only)
- **Channels**: Portal + Email for candidate guide; Portal only for admins
- **Priority**: `high`
- **Action Required**: `True` (candidate must accept or reject)
- **Message Content**:
  - Requesting guide name
  - Tour name, date/time, language, guest count
  - Actions: View Request, Accept, Reject
- **Acceptance Criteria**:
  - Candidate guide receives portal + email notification with `action_required = true`
  - All active admins receive portal notification (informational)
  - `notifications` row created with `event_type = 'SWAP_REQUEST_RECEIVED'`
  - Notification failure does not break the swap request creation

### FR-8: Notify on swap request rejected

- **Description**: When a candidate guide rejects a swap request, notify the requesting guide (original assignee) and all admins.
- **Trigger**: `POST /notifications/swap-request-rejected` API call, or called internally by `reject_swap_request()` in the guide requests service
- **Request Body**:
  ```
  schedule_id: int (required)
  candidate_guide_id: int (required)
  requesting_guide_id: int (required)
  ```
- **Recipients**: Requesting guide / original assignee (PORTAL + EMAIL) + all active admins (PORTAL only)
- **Channels**: Portal + Email for requesting guide; Portal only for admins
- **Priority**: `normal`
- **Action Required**: `False`
- **Message Content**:
  - Which guide declined
  - Tour name, date/time
  - Suggestion to request another guide or contact admin
  - Actions: Find Another Guide, Contact Admin
- **Acceptance Criteria**:
  - Requesting guide receives portal + email notification
  - All active admins receive portal notification (informational)
  - `notifications` row created with `event_type = 'SWAP_REQUEST_REJECTED'`
  - Notification failure does not break the swap request rejection

## 5. Data Model Impact

| Table | Impact |
|-------|--------|
| `notifications` | New row per notification per channel per recipient. Includes `group_id UUID` (nullable, indexed) to correlate PORTAL and EMAIL rows for the same logical event. |
| `users` | Read — identify active admins |
| `guides` | Read — guide email for email notifications |
| `schedule` | Read — schedule details for notification content |

### notifications table — key columns

| Column | Type | Notes |
|--------|------|-------|
| `group_id` | `UUID` | Nullable. Generated once per `create_notification` call and shared by all channel rows in that batch. Used to LEFT JOIN email status into portal view. Indexed (`idx_notifications_group_id`). |

## 6. API Contracts

### 6.1 Read Endpoints (Existing)

#### `GET /notifications`

List portal notifications for the authenticated user (admin or guide). By default returns only `channel = 'PORTAL'` rows with embedded email delivery status.

**Response (200):**
```json
[
  {
    "id": 1,
    "event_type": "GUIDE_ASSIGNED",
    "message": "You have been assigned to Ocean Discovery Tour on Mar 15 at 10:00 (en)",
    "channel": "PORTAL",
    "status": "SENT",
    "email_status": "SENT",
    "email_sent_at": "2026-03-10T14:30:05Z",
    "created_at": "2026-03-10T14:30:00Z"
  }
]
```

`email_status` and `email_sent_at` are derived from the correlated EMAIL row via `group_id` LEFT JOIN. They are `null` when no EMAIL row exists for the event.

#### `PATCH /notifications/{id}/read`

Mark a portal notification as read.

### 6.2 Trigger Endpoints (NEW - v3.0)

All trigger endpoints use **JSON request body** for better structure, validation, and security.

#### `POST /notifications/guide-assigned`

Trigger guide assignment notifications (FR-1).

**Authentication:** Required (Admin or System)

**Request Body:**
```json
{
  "schedule_id": 123,
  "guide_id": 5,
  "assignment_type": "AUTO"
}
```

**Fields:**
- `schedule_id` (int, required): Schedule ID
- `guide_id` (int, required): Guide ID
- `assignment_type` (string, required): "AUTO" or "MANUAL"

**Response (200):**
```json
{
  "success": true,
  "event_type": "GUIDE_ASSIGNED",
  "schedule_id": 123,
  "guide_id": 5,
  "assignment_type": "AUTO",
  "message": "Notification sent for guide assignment"
}
```

**Response (400):**
```json
{
  "error": "Schedule not found",
  "details": "schedule_id 123 does not exist"
}
```

#### `POST /notifications/guide-unassigned`

Trigger guide unassignment notifications (FR-2).

**Authentication:** Required (Admin or System)

**Request Body:**
```json
{
  "schedule_id": 123,
  "guide_id": 5,
  "reason": "Guide requested cancellation",
  "replacement_guide_id": 7
}
```

**Fields:**
- `schedule_id` (int, required): Schedule ID
- `guide_id` (int, required): Guide ID who was unassigned
- `reason` (string, required): Reason for unassignment
- `replacement_guide_id` (int, optional): New guide ID if replaced

**Response (200):**
```json
{
  "success": true,
  "event_type": "GUIDE_UNASSIGNED",
  "schedule_id": 123,
  "guide_id": 5,
  "replacement_guide_id": 7,
  "reason": "Guide requested cancellation",
  "message": "Notification sent for guide unassignment"
}
```

#### `POST /notifications/schedule-unassignable`

Trigger urgent unassignable schedule notifications (FR-5).

**Authentication:** Required (Admin or System)

**Request Body:**
```json
{
  "schedule_id": 123,
  "reasons": [
    "No guides available with Spanish language",
    "All certified guides already assigned"
  ],
  "attempted_guides_count": 12
}
```

**Fields:**
- `schedule_id` (int, required): Schedule ID
- `reasons` (list[string], required): List of constraint failures
- `attempted_guides_count` (int, optional): Number of guides checked (default: 0)

**Response (200):**
```json
{
  "success": true,
  "event_type": "SCHEDULE_UNASSIGNABLE",
  "schedule_id": 123,
  "priority": "urgent",
  "reasons": [
    "No guides available with Spanish language",
    "All certified guides already assigned"
  ],
  "attempted_guides_count": 12,
  "message": "Urgent notification sent to admins"
}
```

#### `POST /notifications/schedule-changed`

Trigger schedule change notifications (FR-3, FR-4).

**Authentication:** Required (Admin or System)

**Request Body:**
```json
{
  "schedule_id": 123,
  "change_type": "RESERVATION_CANCELLED",
  "change_details": "Reservation #456 cancelled - 2 tickets removed",
  "affected_guide_id": 5,
  "old_state": {
    "ticket_count": 10,
    "status": "CONFIRMED"
  },
  "new_state": {
    "ticket_count": 8,
    "status": "CONFIRMED"
  }
}
```

**Fields:**
- `schedule_id` (int, required): Schedule ID
- `change_type` (string, required): Type of change
- `change_details` (string, required): Description of change
- `affected_guide_id` (int, optional): Guide affected by change
- `old_state` (dict, optional): Previous state before change
- `new_state` (dict, optional): New state after change

**Response (200):**
```json
{
  "success": true,
  "event_type": "SCHEDULE_CHANGED",
  "schedule_id": 123,
  "change_type": "RESERVATION_CANCELLED",
  "affected_guide_id": 5,
  "message": "Notification sent for schedule change"
}
```

#### `POST /notifications/swap-request-received`

Trigger swap request received notification (FR-7).

**Authentication:** Required (Admin or System)

**Request Body:**
```json
{
  "schedule_id": 123,
  "candidate_guide_id": 7,
  "requesting_guide_id": 5
}
```

**Fields:**
- `schedule_id` (int, required): Schedule ID
- `candidate_guide_id` (int, required): Guide ID who receives the swap request
- `requesting_guide_id` (int, required): Guide ID who initiated the swap request

**Response (200):**
```json
{
  "success": true,
  "event_type": "SWAP_REQUEST_RECEIVED",
  "schedule_id": 123,
  "candidate_guide_id": 7,
  "requesting_guide_id": 5,
  "message": "Notification sent for swap request received"
}
```

#### `POST /notifications/swap-request-rejected`

Trigger swap request rejected notification (FR-8).

**Authentication:** Required (Admin or System)

**Request Body:**
```json
{
  "schedule_id": 123,
  "candidate_guide_id": 7,
  "requesting_guide_id": 5
}
```

**Fields:**
- `schedule_id` (int, required): Schedule ID
- `candidate_guide_id` (int, required): Guide ID who rejected the swap request
- `requesting_guide_id` (int, required): Guide ID who initiated the swap request

**Response (200):**
```json
{
  "success": true,
  "event_type": "SWAP_REQUEST_REJECTED",
  "schedule_id": 123,
  "candidate_guide_id": 7,
  "requesting_guide_id": 5,
  "message": "Notification sent for swap request rejected"
}
```

## 7. Error Handling

| Scenario | Expected Behavior | HTTP Status |
|----------|-------------------|-------------|
| Email delivery failure | `status = 'FAILED'`, retry up to 3 times | N/A |
| Guide has no email configured | Log warning, send portal notification only | N/A |
| Notification service unavailable | Queue notifications for later delivery | N/A |
| Invalid schedule_id (API) | Return error: "Schedule not found" | 400 |
| Invalid guide_id (API) | Return error: "Guide not found" | 400 |
| Unauthorized API call | Return error: "Admin access required" | 403 |
| Missing required fields (API) | Return error: "Missing required field: schedule_id" | 400 |

## 8. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Email service (Resend.com) | Infrastructure | For email delivery |
| [FDR-002] Guide Assignment | Internal | Independent - notifications triggered via API |
| [FDR-004] Auto Re-scheduling | Internal | Independent - notifications triggered via API |
| Frontend/Orchestrator | Application Layer | Coordinates domain operations and notification API calls |

## 9. Open Questions

| # | Question | Answer | Status |
|---|----------|--------|--------|
| 1 | Which email service to use? | Resend.com (easiest setup, 3000 emails/month free) | Resolved |
| 2 | Should portal notifications be real-time (WebSocket) or polling? | Polling for MVP (simpler implementation) | Resolved |
| 3 | Should admins receive email for every change or just critical ones? | Every change, but configurable via preferences | Resolved |
| 4 | Notification templates — managed in code or DB? | Code (notification_templates.py) | Resolved |
| 5 | Should notifications be triggered automatically by domain services or via explicit API calls? | Explicit API calls (v3.0) - Decoupled architecture for better testability and flexibility | Resolved |
| 6 | Who is responsible for triggering notifications: backend routes or frontend? | Both supported: Backend routes can call notification API internally, OR frontend can orchestrate after domain operations | Resolved |

## 10. Architecture Decision

### 10.1 Event-Based vs API-Based Notifications

**Decision:** API-based notification triggering (v3.0)

**Rationale:**
1. **Decoupling:** Domain services (guide assignment, rescheduling) remain focused on business logic without notification concerns
2. **Testability:** Notifications can be tested independently without triggering domain operations
3. **Flexibility:** Frontend or backend can decide when to send notifications
4. **Retry Logic:** Failed notifications can be easily retried via API calls
5. **Manual Control:** Admins can manually trigger notifications via API
6. **Observability:** Clear API logs show when and why notifications were triggered

**Trade-offs:**
- **Slightly more coordination required:** Caller must explicitly trigger notifications after domain operations
- **Potential for missed notifications:** If caller forgets to trigger notification API
- **Mitigation:** Backend routes call notification service directly; frontend can use orchestration layer

### 10.2 Notification Triggering Patterns

**Pattern 1: Backend Route Coordination** (Recommended for MVP)
```python
# Backend route handles both domain operation and notification
result = guide_assignment_service.auto_assign_guide(conn, schedule_id)

# Trigger notification internally
notification_service.notify_guide_assignment(
    conn, schedule_id, result["guide_id"], "AUTO"
)

return result
```

**Pattern 2: Frontend Orchestration** (Recommended for production)
```typescript
// Frontend coordinates domain and notification
const result = await api.post('/schedules/1/assign');

await api.post('/notifications/guide-assigned', {
  schedule_id: 1,
  guide_id: result.guide_id,
  assignment_type: 'AUTO'
});
```

**Pattern 3: Event-Driven** (Future consideration)
- Domain services publish events to message queue
- Notification service subscribes and processes events
- Provides eventual consistency and retry mechanisms

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-03 | Evandro Maciel | Initial draft — portal + email for admin and guide |
| 1.1     | 2026-03-03 | Evandro Maciel | Renamed bookings→reservations throughout; updated event names |
| 2.0     | 2026-03-11 | Evandro Maciel | Implemented: Multi-channel notifications with Resend.com, user preferences, rich detail view, priority levels, action buttons, enhanced templates following 2026 best practices |
| 3.0     | 2026-03-13 | Evandro Maciel | Architecture refactor: API-first notification triggering, decoupled from domain services, added POST endpoints for manual/programmatic notification triggering, updated trigger mechanism from events to explicit API calls |
| 4.0     | 2026-03-14 | Evandro Maciel | Notification deduplication: added `group_id` UUID to correlate PORTAL/EMAIL rows, portal shows only PORTAL channel with embedded email status, removed dev-only test-trigger endpoints |
| 5.0     | 2026-03-17 | Evandro Maciel | Swap request notifications: added FR-7 (SWAP_REQUEST_RECEIVED) and FR-8 (SWAP_REQUEST_REJECTED) with corresponding trigger endpoints, templates, and service functions |
