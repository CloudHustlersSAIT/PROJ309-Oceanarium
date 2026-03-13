# Notification Endpoints - Quick Testing Guide

Quick reference for testing notification endpoints in Insomnia.

## Setup

1. ✅ Backend is running at `http://localhost:8000`
2. ✅ Insomnia collection updated with 15 notification endpoints (v3.0)
3. ✅ Email system configured (test mode)

## Testing Order

### 1️⃣ Test Email System (No Auth Required)

**Fastest way to verify everything works!**

```
POST /notifications/test-email?to_email=evandro.maciel.silva@gmail.com&template_type=system
```

Try all three templates:
- `template_type=system` - Simple test email
- `template_type=guide_assignment` - Guide assignment email
- `template_type=admin_alert` - Urgent admin alert

**Expected Result:** 
- Response: `{"success": true, "message": "Test email sent to..."}`
- Check `evandro.maciel.silva@gmail.com` inbox for the email

---

### 2️⃣ Get Notification Summary (Auth Required)

```
GET /notifications/summary
Authorization: Bearer dev-bypass
```

**Expected Result:**
```json
{
  "total": 45,
  "unread": 5,
  "by_priority": {...},
  "by_event_type": {...}
}
```

---

### 3️⃣ List Notifications (Auth Required)

**All notifications:**
```
GET /notifications
Authorization: Bearer dev-bypass
```

**Only unread:**
```
GET /notifications?unread_only=true
Authorization: Bearer dev-bypass
```

**Filter by priority:**
```
GET /notifications?priority=urgent
Authorization: Bearer dev-bypass
```

**Expected Result:**
```json
{
  "notifications": [...],
  "pagination": {...},
  "summary": {...}
}
```

---

### 4️⃣ Get Notification Detail (Auth Required)

Pick a notification ID from the list above, then:

```
GET /notifications/{id}
Authorization: Bearer dev-bypass
```

**Expected Result:**
- Full notification details
- Related notifications
- Actions available
- Automatically marked as read

---

### 5️⃣ Mark Notification as Read (Auth Required)

```
PATCH /notifications/{id}/read
Authorization: Bearer dev-bypass
```

**Expected Result:**
```json
{
  "success": true,
  "notification_id": 42
}
```

---

### 6️⃣ Mark All as Read (Auth Required)

**Mark everything:**
```
PATCH /notifications/read-all
Authorization: Bearer dev-bypass
```

**Mark only specific type:**
```
PATCH /notifications/read-all?event_type=GUIDE_ASSIGNED
Authorization: Bearer dev-bypass
```

**Expected Result:**
```json
{
  "success": true,
  "count": 5
}
```

---

### 7️⃣ Get Notification Preferences (Auth Required)

```
GET /notifications/preferences
Authorization: Bearer dev-bypass
```

**Expected Result:**
```json
[
  {
    "event_type": "GUIDE_ASSIGNED",
    "email_enabled": true,
    "portal_enabled": true
  },
  ...
]
```

---

### 8️⃣ Update Notification Preferences (Auth Required)

```
PUT /notifications/preferences
Authorization: Bearer dev-bypass
Content-Type: application/json

[
  {
    "event_type": "GUIDE_ASSIGNED",
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

**Expected Result:**
```json
{
  "success": true,
  "updated": 2
}
```

---

### 9️⃣ Retry Failed Notifications (Admin Only)

```
POST /notifications/retry-failed
Authorization: Bearer dev-bypass
```

**Expected Result:**
```json
{
  "success": true,
  "total_failed": 5,
  "retried": 4
}
```

---

## Trigger Notification Endpoints (v3.0 - NEW!)

These endpoints allow manual triggering of notifications for testing and debugging.

### 🔟 Trigger Guide Assigned Notification

```bash
POST /notifications/guide-assigned
Authorization: Bearer dev-bypass
Content-Type: application/json

{
  "schedule_id": 1,
  "guide_id": 5,
  "assignment_type": "AUTO"
}
```

**When to use:** Test guide assignment notifications without actually assigning a guide.

**curl example:**
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

**Expected Result:**
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

---

### 1️⃣1️⃣ Trigger Guide Unassigned Notification

```bash
POST /notifications/guide-unassigned
Authorization: Bearer dev-bypass
Content-Type: application/json

{
  "schedule_id": 1,
  "guide_id": 5,
  "reason": "Guide cancellation",
  "replacement_guide_id": 7
}
```

**When to use:** Test guide unassignment notifications.

**curl example:**
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

---

### 1️⃣2️⃣ Trigger Schedule Unassignable Notification

```bash
POST /notifications/schedule-unassignable
Authorization: Bearer dev-bypass
Content-Type: application/json

{
  "schedule_id": 1,
  "reasons": [
    "No guides available with Spanish language",
    "All certified guides already assigned"
  ],
  "attempted_guides_count": 12
}
```

**When to use:** Test urgent unassignable schedule alerts (admins only).

**curl example:**
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

---

### 1️⃣3️⃣ Trigger Schedule Changed Notification

```bash
POST /notifications/schedule-changed
Authorization: Bearer dev-bypass
Content-Type: application/json

{
  "schedule_id": 1,
  "change_type": "RESERVATION_CANCELLED",
  "change_details": "Reservation #456 cancelled - 2 tickets removed",
  "affected_guide_id": 5
}
```

**When to use:** Test schedule change notifications (reservation cancelled/moved).

**curl example:**
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

---

## Common Testing Scenarios

### Scenario 1: Check for New Notifications

```bash
# 1. Get summary
GET /notifications/summary

# 2. List unread
GET /notifications?unread_only=true&limit=10

# 3. Get detail of first unread
GET /notifications/{id}

# 4. Mark as read
PATCH /notifications/{id}/read
```

---

### Scenario 2: Test Email Delivery

```bash
# 1. Send system test
POST /notifications/test-email?to_email=evandro.maciel.silva@gmail.com&template_type=system

# 2. Send guide assignment test
POST /notifications/test-email?to_email=evandro.maciel.silva@gmail.com&template_type=guide_assignment

# 3. Send admin alert test
POST /notifications/test-email?to_email=evandro.maciel.silva@gmail.com&template_type=admin_alert

# 4. Check inbox!
```

---

### Scenario 3: Configure Preferences

```bash
# 1. Get current preferences
GET /notifications/preferences

# 2. Update preferences
PUT /notifications/preferences
[Body with updated preferences]

# 3. Verify changes
GET /notifications/preferences
```

---

### Scenario 4: Test Complete Notification Flow (v3.0)

```bash
# 1. Trigger guide assigned notification
POST /notifications/guide-assigned?schedule_id=1&guide_id=5&assignment_type=AUTO

# 2. Check notification was created
GET /notifications?unread_only=true

# 3. Check email inbox (evandro.maciel.silva@gmail.com)

# 4. Get notification detail
GET /notifications/{id}

# 5. Mark as read
PATCH /notifications/{id}/read
```

---

### Scenario 5: Clean Up Notifications

```bash
# 1. Check unread count
GET /notifications/summary

# 2. Mark all as read
PATCH /notifications/read-all

# 3. Verify
GET /notifications/summary
```

---

## Troubleshooting

### Email Not Sending

**Check:**
1. `EMAIL_ENABLED=true` in `.env`
2. `RESEND_API_KEY` is set
3. Using `EMAIL_FROM=onboarding@resend.dev` for test mode
4. Sending to `evandro.maciel.silva@gmail.com` (account owner email)

**Error:** "You can only send testing emails to your own email address"
**Solution:** You're in test mode. Either:
- Send to `evandro.maciel.silva@gmail.com`
- Or verify a domain on Resend to send to any email

---

### 401 Unauthorized

**Check:**
1. `Authorization` header is included
2. Using `Bearer dev-bypass` for local testing
3. `AUTH_BYPASS=True` is set in `.env`

---

### 404 Not Found

**Check:**
1. Backend is running: `curl http://localhost:8000/health`
2. Notification ID exists
3. You have permission to access the notification

---

### Empty Notification List

**This is normal if:**
- Database is fresh/empty
- No guides have been assigned yet
- All notifications have been filtered out

**To create notifications:**
1. **Use trigger endpoints (v3.0):** `POST /notifications/guide-assigned`
2. Assign a guide to a schedule: `POST /schedules/{id}/assign`
3. Reassign/cancel a guide: `DELETE /schedules/{id}/guide`
4. Wait for system to detect unassignable schedules

---

## Quick Copy-Paste Examples

### Trigger Notification Endpoints (v3.0)
```bash
# Trigger guide assigned
curl -X POST "http://localhost:8000/notifications/guide-assigned" \
  -H "Authorization: Bearer dev-bypass" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": 1, "guide_id": 5, "assignment_type": "AUTO"}'

# Trigger guide unassigned
curl -X POST "http://localhost:8000/notifications/guide-unassigned" \
  -H "Authorization: Bearer dev-bypass" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": 1, "guide_id": 5, "reason": "Guide cancellation"}'

# Trigger schedule unassignable (urgent)
curl -X POST "http://localhost:8000/notifications/schedule-unassignable" \
  -H "Authorization: Bearer dev-bypass" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": 1, "reasons": ["No guides available"], "attempted_guides_count": 12}'

# Trigger schedule changed
curl -X POST "http://localhost:8000/notifications/schedule-changed" \
  -H "Authorization: Bearer dev-bypass" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": 1, "change_type": "RESERVATION_CANCELLED", "change_details": "Reservation cancelled", "affected_guide_id": 5}'
```

### Test All Email Templates
```bash
# System test
curl -X POST "http://localhost:8000/notifications/test-email?to_email=evandro.maciel.silva@gmail.com&template_type=system"

# Guide assignment
curl -X POST "http://localhost:8000/notifications/test-email?to_email=evandro.maciel.silva@gmail.com&template_type=guide_assignment"

# Admin alert
curl -X POST "http://localhost:8000/notifications/test-email?to_email=evandro.maciel.silva@gmail.com&template_type=admin_alert"
```

### Get Notification Data
```bash
# Summary
curl -H "Authorization: Bearer dev-bypass" http://localhost:8000/notifications/summary

# List unread
curl -H "Authorization: Bearer dev-bypass" "http://localhost:8000/notifications?unread_only=true"

# Get preferences
curl -H "Authorization: Bearer dev-bypass" http://localhost:8000/notifications/preferences
```

---

## Insomnia Tips

1. **Environment Variables**: Switch between Dev/Prod environments easily
2. **Save Responses**: Right-click response → Generate Code → Copy as cURL
3. **Request History**: View all past requests and responses
4. **Search Requests**: Cmd/Ctrl + K to quickly find endpoints
5. **Folder Organization**: All notifications grouped under "Notifications" folder

---

## What's in the Insomnia Collection

✅ **15 Notification Endpoints (v3.0):**
1. List Notifications (with filters)
2. Get Notification Detail
3. Get Notification Summary
4. Mark Notification as Read
5. Mark All as Read
6. Get Notification Preferences
7. Update Notification Preferences
8. Retry Failed Notifications
9. Test Email - System
10. Test Email - Guide Assignment
11. Test Email - Admin Alert
12. **🆕 Trigger Guide Assigned Notification**
13. **🆕 Trigger Guide Unassigned Notification**
14. **🆕 Trigger Schedule Unassignable Notification**
15. **🆕 Trigger Schedule Changed Notification**

**All with:**
- Pre-configured headers
- Query parameter examples
- Request body templates
- Descriptions

---

## Next Steps

1. ✅ Import/refresh Insomnia collection
2. 🧪 Test email endpoints (no auth required)
3. 📧 Check `evandro.maciel.silva@gmail.com` inbox
4. 🔐 Test authenticated endpoints with `dev-bypass`
5. ⚙️ Test preference management
6. 📊 Verify notification counts and summaries

**Ready to test? Start with the email test endpoints - they're the easiest!**
