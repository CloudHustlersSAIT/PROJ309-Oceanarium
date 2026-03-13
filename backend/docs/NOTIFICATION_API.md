# Notification API Reference

Complete reference for all notification endpoints in the Oceanarium backend.

## Base URL

- **Local Development:** `http://localhost:8000`
- **Production:** `https://oceanarium.duckdns.org`

All notification endpoints are under the `/notifications` prefix.

---

## Authentication

Most endpoints require authentication. Include the Firebase ID token in the Authorization header:

```
Authorization: Bearer <your-firebase-id-token>
```

For local development with `AUTH_BYPASS=True`, you can use:
```
Authorization: Bearer dev-bypass
```

---

## Endpoints

### 1. List Notifications

**GET** `/notifications`

List notifications for the authenticated user with enhanced filtering.

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | - | Filter by status: `SENT`, `FAILED`, `PENDING` |
| `channel` | string | - | Filter by channel: `EMAIL`, `PORTAL` |
| `unread_only` | boolean | false | Show only unread notifications |
| `priority` | string | - | Filter by priority: `urgent`, `high`, `normal`, `low` |
| `limit` | integer | 50 | Number of results (max 100) |
| `offset` | integer | 0 | Pagination offset |

**Example Request:**
```bash
GET /notifications?unread_only=true&limit=20
```

**Response:**
```json
{
  "notifications": [
    {
      "id": 42,
      "message": "New assignment: Ocean Discovery Tour on March 15, 2026...",
      "event_type": "GUIDE_ASSIGNED",
      "priority": "normal",
      "channel": "EMAIL",
      "status": "SENT",
      "read_at": null,
      "created_at": "2026-03-13T14:30:00",
      "schedule_id": 123,
      "guide_id": 5,
      "primary_action": {
        "label": "View Schedule",
        "url": "/schedule/123"
      }
    }
  ],
  "pagination": {
    "total": 15,
    "limit": 20,
    "offset": 0,
    "has_more": false
  },
  "summary": {
    "unread_count": 5,
    "urgent_count": 1,
    "action_required_count": 2
  }
}
```

---

### 2. Get Notification Detail

**GET** `/notifications/{notification_id}`

Get full notification detail and automatically mark as read.

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | integer | Notification ID |

**Example Request:**
```bash
GET /notifications/42
```

**Response:**
```json
{
  "id": 42,
  "message": "New assignment: Ocean Discovery Tour on March 15, 2026...",
  "event_type": "GUIDE_ASSIGNED",
  "priority": "normal",
  "channel": "EMAIL",
  "status": "SENT",
  "read_at": "2026-03-13T14:35:00",
  "created_at": "2026-03-13T14:30:00",
  "schedule_id": 123,
  "schedule_date": "2026-03-15T10:00:00",
  "tour_name": "Ocean Discovery Tour",
  "detail": {
    "title": "New Tour Assignment",
    "tour_name": "Ocean Discovery Tour",
    "date": "March 15, 2026",
    "time": "10:00 AM",
    "language": "EN",
    "ticket_count": 8
  },
  "actions": [
    {
      "label": "View Schedule",
      "url": "/schedule/123",
      "primary": true
    },
    {
      "label": "Contact Admin",
      "url": "/issues/new"
    }
  ],
  "related_notifications": [
    {
      "id": 40,
      "message": "Schedule created for Ocean Discovery Tour",
      "created_at": "2026-03-12T09:00:00"
    }
  ]
}
```

---

### 3. Get Notification Summary

**GET** `/notifications/summary`

Get notification counts and summary for current user.

**Authentication:** Required

**Example Request:**
```bash
GET /notifications/summary
```

**Response:**
```json
{
  "total": 45,
  "unread": 5,
  "action_required": 2,
  "by_priority": {
    "urgent": 1,
    "high": 3,
    "normal": 38,
    "low": 3
  },
  "by_event_type": {
    "GUIDE_ASSIGNED": 20,
    "GUIDE_REASSIGNED": 5,
    "SCHEDULE_UNASSIGNABLE": 2,
    "SCHEDULE_CHANGED": 18
  }
}
```

---

### 4. Mark Notification as Read

**PATCH** `/notifications/{notification_id}/read`

Mark a single notification as read.

**Authentication:** Required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | integer | Notification ID |

**Example Request:**
```bash
PATCH /notifications/42/read
```

**Response:**
```json
{
  "success": true,
  "notification_id": 42
}
```

**Error Response (404):**
```json
{
  "error": "Notification not found or already read"
}
```

---

### 5. Mark All as Read

**PATCH** `/notifications/read-all`

Mark all unread notifications as read for current user.

**Authentication:** Required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `event_type` | string | - | Optional: Only mark this event type as read |

**Example Request:**
```bash
# Mark all as read
PATCH /notifications/read-all

# Mark only guide assignments as read
PATCH /notifications/read-all?event_type=GUIDE_ASSIGNED
```

**Response:**
```json
{
  "success": true,
  "count": 5
}
```

---

### 6. Get Notification Preferences

**GET** `/notifications/preferences`

Get notification preferences for current user (email and portal settings per event type).

**Authentication:** Required

**Example Request:**
```bash
GET /notifications/preferences
```

**Response:**
```json
[
  {
    "event_type": "GUIDE_ASSIGNED",
    "email_enabled": true,
    "portal_enabled": true
  },
  {
    "event_type": "GUIDE_REASSIGNED",
    "email_enabled": true,
    "portal_enabled": true
  },
  {
    "event_type": "SCHEDULE_UNASSIGNABLE",
    "email_enabled": true,
    "portal_enabled": true
  },
  {
    "event_type": "SCHEDULE_CHANGED",
    "email_enabled": false,
    "portal_enabled": true
  }
]
```

---

### 7. Update Notification Preferences

**PUT** `/notifications/preferences`

Update notification preferences for specific event types.

**Authentication:** Required

**Request Body:**
```json
[
  {
    "event_type": "GUIDE_ASSIGNED",
    "email_enabled": true,
    "portal_enabled": true
  },
  {
    "event_type": "GUIDE_REASSIGNED",
    "email_enabled": true,
    "portal_enabled": true
  },
  {
    "event_type": "SCHEDULE_CHANGED",
    "email_enabled": false,
    "portal_enabled": true
  }
]
```

**Response:**
```json
{
  "success": true,
  "updated": 3
}
```

---

### 8. Retry Failed Notifications (Admin Only)

**POST** `/notifications/retry-failed`

Retry all failed email notifications. Maximum 100 at a time.

**Authentication:** Required (Admin role)

**Example Request:**
```bash
POST /notifications/retry-failed
```

**Response:**
```json
{
  "success": true,
  "total_failed": 5,
  "retried": 4
}
```

**Error Response (403):**
```json
{
  "error": "Admin access required"
}
```

---

### 9. Test Email Endpoints

**POST** `/notifications/test-email`

Send test emails to verify email delivery and template rendering. Development/testing only.

**Authentication:** Not required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `to_email` | string | Yes | Email address to send test to |
| `template_type` | string | Yes | Template type: `system`, `guide_assignment`, `admin_alert` |

**Example Requests:**

#### System Test Email
```bash
POST /notifications/test-email?to_email=evandro.maciel.silva@gmail.com&template_type=system
```

#### Guide Assignment Test
```bash
POST /notifications/test-email?to_email=evandro.maciel.silva@gmail.com&template_type=guide_assignment
```

#### Admin Alert Test
```bash
POST /notifications/test-email?to_email=evandro.maciel.silva@gmail.com&template_type=admin_alert
```

**Success Response:**
```json
{
  "success": true,
  "message": "Test email sent to evandro.maciel.silva@gmail.com",
  "subject": "✅ Oceanarium Notification System - Test Email",
  "template_type": "system"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Failed to send email - check backend logs for details"
}
```

---

## Event Types

The notification system supports the following event types:

| Event Type | Description | Recipients | Priority |
|------------|-------------|------------|----------|
| `GUIDE_ASSIGNED` | Guide assigned to a tour (auto or manual) | Guide | Normal |
| `GUIDE_REASSIGNED` | Guide removed/replaced from a tour | Previous guide | Normal |
| `SCHEDULE_UNASSIGNABLE` | No guide available for schedule (urgent) | Admin | Urgent |
| `SCHEDULE_CHANGED` | Schedule details modified | Admin, affected guide | Normal |

---

## Notification Channels

| Channel | Description |
|---------|-------------|
| `EMAIL` | Email notification via Resend API |
| `PORTAL` | In-app notification (displayed in portal) |

Users can configure preferences for each channel per event type.

---

## Notification Status

| Status | Description |
|--------|-------------|
| `PENDING` | Notification queued but not yet sent |
| `SENT` | Notification successfully delivered |
| `FAILED` | Notification delivery failed (can be retried) |

---

## Priority Levels

| Priority | Description | Use Case |
|----------|-------------|----------|
| `urgent` | Immediate action required | Schedule unassignable, critical failures |
| `high` | Important but not critical | Guide reassignments, schedule conflicts |
| `normal` | Standard notification | Guide assignments, confirmations |
| `low` | Informational only | System updates, reminders |

---

## Testing with Insomnia

1. **Import Collection**: Import `insomnia.json` from the project root
2. **Select Environment**: Choose "Development (localhost)" 
3. **Set Auth Token**: Update `auth_token` environment variable with your Firebase ID token or use `dev-bypass` for local testing
4. **Test Endpoints**: All notification endpoints are organized under the "Notifications" folder

### Quick Test Flow

1. **Get Summary** - Check current notification counts
2. **List Notifications** - View all notifications with filters
3. **Get Detail** - View full details of a specific notification
4. **Mark as Read** - Mark notifications as read
5. **Test Emails** - Send test emails to verify email delivery
6. **Update Preferences** - Configure notification preferences

---

## Trigger Notification Endpoints (v3.0)

These POST endpoints allow explicit triggering of notifications, decoupled from domain operations. Introduced in v3.0 as part of the API-first notification architecture.

### 9. Trigger Guide Assigned Notification

**POST** `/notifications/guide-assigned`

Trigger guide assignment notifications (FR-1). Sends notifications to assigned guide and all admins via EMAIL + PORTAL.

**Authentication:** Required (Admin or System)

**Request Body:**
```json
{
  "schedule_id": 1,
  "guide_id": 5,
  "assignment_type": "AUTO"
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/notifications/guide-assigned" \
  -H "Authorization: Bearer dev-bypass" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": 1,
    "guide_id": 5,
    "assignment_type": "AUTO"
  }'
```

**200 OK Response:**

```json
{
  "success": true,
  "event_type": "GUIDE_ASSIGNED",
  "schedule_id": 1,
  "guide_id": 5,
  "assignment_type": "AUTO",
  "message": "Notification sent for guide assignment"
}
```

**400 Bad Request:**

```json
{
  "error": "Schedule not found",
  "details": "schedule_id 1 does not exist"
}
```

---

### 10. Trigger Guide Unassigned Notification

**POST** `/notifications/guide-unassigned`

Trigger guide unassignment notifications (FR-2). Sends notifications to unassigned guide and all admins.

**Authentication:** Required (Admin or System)

**Request Body:**
```json
{
  "schedule_id": 1,
  "guide_id": 5,
  "reason": "Guide cancellation",
  "replacement_guide_id": 7
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/notifications/guide-unassigned" \
  -H "Authorization: Bearer dev-bypass" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": 1,
    "guide_id": 5,
    "reason": "Guide cancellation",
    "replacement_guide_id": 7
  }'
```

**200 OK Response:**

```json
{
  "success": true,
  "event_type": "GUIDE_UNASSIGNED",
  "schedule_id": 1,
  "guide_id": 5,
  "replacement_guide_id": 7,
  "reason": "Guide cancellation",
  "message": "Notification sent for guide unassignment"
}
```

---

### 11. Trigger Schedule Unassignable Notification

**POST** `/notifications/schedule-unassignable`

Trigger URGENT unassignable schedule notifications (FR-5). Sends urgent notifications to all admins only.

**Authentication:** Required (Admin or System)

**Request Body:**
```json
{
  "schedule_id": 1,
  "reasons": [
    "No guides available with Spanish language",
    "All certified guides already assigned"
  ],
  "attempted_guides_count": 12
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/notifications/schedule-unassignable" \
  -H "Authorization: Bearer dev-bypass" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": 1,
    "reasons": [
      "No guides available with Spanish language",
      "All certified guides already assigned"
    ],
    "attempted_guides_count": 12
  }'
```

**200 OK Response:**

```json
{
  "success": true,
  "event_type": "SCHEDULE_UNASSIGNABLE",
  "schedule_id": 1,
  "priority": "urgent",
  "reasons": [
    "No guides available with Spanish language",
    "All certified guides already assigned"
  ],
  "attempted_guides_count": 12,
  "message": "Urgent notification sent to admins"
}
```

---

### 12. Trigger Schedule Changed Notification

**POST** `/notifications/schedule-changed`

Trigger schedule change notifications (FR-3, FR-4). Covers reservation cancellations, moves, and modifications.

**Authentication:** Required (Admin or System)

**Request Body:**
```json
{
  "schedule_id": 1,
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

**Example Request:**

```bash
curl -X POST "http://localhost:8000/notifications/schedule-changed" \
  -H "Authorization: Bearer dev-bypass" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": 1,
    "change_type": "RESERVATION_CANCELLED",
    "change_details": "Reservation #456 cancelled - 2 tickets removed",
    "affected_guide_id": 5
  }'
```

**200 OK Response:**

```json
{
  "success": true,
  "event_type": "SCHEDULE_CHANGED",
  "schedule_id": 1,
  "change_type": "RESERVATION_CANCELLED",
  "affected_guide_id": 5,
  "message": "Notification sent for schedule change"
}
```

---

## Notification Flow Architecture (v3.0)

### Backend Coordination Pattern (Current Implementation)

The backend routes directly call notification service functions after domain operations:

```python
# Example: Auto-assign guide and notify
result = guide_assignment_service.auto_assign_guide(conn, schedule_id)

# Trigger notification directly
notification_service.notify_guide_assignment(
    conn, schedule_id, result["guide_id"], "AUTO"
)
```

### Frontend Orchestration Pattern (Alternative)

Frontend can coordinate domain operations and notifications separately:

```javascript
// Step 1: Perform domain operation
const result = await api.post('/schedules/1/assign');

// Step 2: Trigger notification explicitly
await api.post('/notifications/guide-assigned', {
  params: {
    schedule_id: 1,
    guide_id: result.guide_id,
    assignment_type: 'AUTO'
  }
});
```

### Benefits of API-First Approach

1. **Decoupling:** Domain services remain focused on business logic
2. **Testability:** Notifications can be tested independently
3. **Flexibility:** Backend or frontend can decide when to send notifications
4. **Retry Logic:** Failed notifications can be easily retried via API calls
5. **Manual Control:** Admins can manually trigger notifications via API
6. **Observability:** Clear API logs show when and why notifications were triggered

---

## Email Configuration

For email notifications to work:

1. Set environment variables in `.env`:
   ```env
   EMAIL_ENABLED=true
   RESEND_API_KEY=your-resend-api-key
   EMAIL_FROM=onboarding@resend.dev
   EMAIL_FROM_NAME=Oceanarium Scheduling System
   ```

2. **Test Mode (Current)**: Using `onboarding@resend.dev` allows sending only to the Resend account owner's email

3. **Production Mode**: Verify a domain on Resend to send to any email address:
   - Go to https://resend.com/domains
   - Verify your domain (e.g., `oceanarium.com`)
   - Update `EMAIL_FROM=notifications@oceanarium.com`

---

## Error Handling

All endpoints return standard error responses:

**400 Bad Request:**
```json
{
  "error": "Invalid parameter value"
}
```

**401 Unauthorized:**
```json
{
  "error": "Authentication required"
}
```

**403 Forbidden:**
```json
{
  "error": "Admin access required"
}
```

**404 Not Found:**
```json
{
  "error": "Notification not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "detail": "Error message details"
}
```

---

## Related Documentation

- [Email Testing Guide](./EMAIL_TESTING_GUIDE.md) - Complete guide for testing email notifications
- [Architecture & Tech Stack](./ARCHITECTURE-TECH-STACK.md) - System architecture overview
- [Notification Templates](../app/services/notification_templates.py) - Email template source code
- [Notification Service](../app/services/notification_service.py) - Notification logic

---

## Support

For issues or questions:
- Check backend logs for detailed error messages
- Review the Email Testing Guide for email-specific issues
- Verify authentication tokens are valid
- Ensure the backend server is running on the correct port
