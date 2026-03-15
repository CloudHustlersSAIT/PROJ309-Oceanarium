# Schedule Endpoint Frontend Guide

This is a quick reference for consuming the new backend endpoint that powers calendar events.

## Endpoint

- Method: `GET`
- Path: `/schedules`
- Base URL (local): `http://localhost:8000`
- Full local URL: `http://localhost:8000/schedules`

## Purpose

Returns schedule-level events from the `schedule` table.

Important domain note:
- A single schedule can have multiple reservations.
- The calendar should display schedules (events), not individual reservations.

## Query Parameters (All Optional)

- `start_date` (format: `YYYY-MM-DD`)
- `end_date` (format: `YYYY-MM-DD`)
- `status` (case-insensitive exact match, example: `scheduled`)

### Date Filtering Behavior

- `start_date`: keeps events that end on or after this date.
- `end_date`: keeps events that start before the day after this date.

This means range filtering is overlap-based (good for calendar windows).

## Example Requests

No filters:

```http
GET /schedules
```

Date range:

```http
GET /schedules?start_date=2026-03-01&end_date=2026-03-31
```

Status only:

```http
GET /schedules?status=scheduled
```

Combined:

```http
GET /schedules?start_date=2026-03-01&end_date=2026-03-31&status=scheduled
```

## Example Response Shape

```json
[
  {
    "id": 101,
    "guide_id": 7,
    "tour_id": 3,
    "language_code": "en",
    "event_start_datetime": "2026-03-08T14:00:00+00:00",
    "event_end_datetime": "2026-03-08T15:00:00+00:00",
    "status": "scheduled",
    "created_at": "2026-03-01T10:12:44+00:00",
    "tour_name": "Shark Tunnel Tour",
    "guide_name": "Alex Rivera",
    "reservation_count": 12
  }
]
```

## Frontend Usage (Vite/Vue)

```js
// src/services/api.js
export async function getSchedules(params = {}) {
  const query = new URLSearchParams(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== ''),
  ).toString()

  const endpoint = query ? `/schedules?${query}` : '/schedules'
  return fetchAPI(endpoint)
}
```

```js
// example call from calendar store/view
const schedules = await getSchedules({
  start_date: '2026-03-01',
  end_date: '2026-03-31',
  status: 'scheduled',
})
```

## Mapping Tip for Calendar UI

Recommended mapping for each returned item:

- `id`: `schedule-${id}`
- `title`: `tour_name`
- `start`: `event_start_datetime`
- `end`: `event_end_datetime`
- `resourceName`: `guide_name || 'Unassigned Guide'`
- `notes`: `Reservations: ${reservation_count}`
- `status`: `status`

## Error Cases

- `400 Bad Request`: `start_date` is after `end_date`.
- `500 Internal Server Error`: unexpected backend failure.

Example `400` response:

```json
{
  "detail": "start_date cannot be after end_date"
}
```

---

## Guide Assignment Endpoints

These endpoints assign a guide to a schedule based on FDR-002 rules.

### Auto Assign Guide

- Method: `POST`
- Path: `/schedules/{schedule_id}/assign`
- No request body required.

Automatically finds the best eligible guide using three hard constraints:

1. **Language** — guide speaks `schedule.language_code`
2. **Expertise** — guide is qualified for `schedule.tour_id`
3. **Availability** — guide has matching availability slots, no blocked exceptions, and no overlapping schedules

When multiple guides pass all constraints, priority is:
1. Fewest same-day assignments
2. Highest `guide_rating`
3. Lowest `guide.id` (deterministic tiebreaker)

#### Example Request

```http
POST /schedules/10/assign
```

#### Success Response (200)

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

#### Unassignable Response (422)

Returned when no guide satisfies all constraints. The schedule status is set to `UNASSIGNABLE`.

```json
{
  "detail": {
    "message": "No eligible guide found for this schedule",
    "reasons": ["NO_LANGUAGE_MATCH"]
  }
}
```

Possible reason codes: `NO_LANGUAGE_MATCH`, `NO_EXPERTISE_MATCH`, `NO_AVAILABILITY_MATCH`.

### Manual Assign Guide (Admin Override)

- Method: `PUT`
- Path: `/schedules/{schedule_id}/assign`

Assigns a specific guide to a schedule. Constraint violations produce warnings but do **not** block the assignment.

#### Example Request

```http
PUT /schedules/10/assign
Content-Type: application/json

{
  "guide_id": 7,
  "reason": "Customer requested specific guide"
}
```

#### Success Response (200)

```json
{
  "schedule_id": 10,
  "guide_id": 7,
  "guide_name": "John Doe",
  "assignment_type": "MANUAL",
  "warnings": ["Guide does not speak requested language: pt"]
}
```

`warnings` is an empty array when all constraints are satisfied.

### Preview Eligible Guides

- Method: `GET`
- Path: `/schedules/{schedule_id}/eligible-guides`

Read-only endpoint that returns a ranked list of guides eligible for a schedule. It does **not** modify any data — use it to preview candidates before assigning.

The endpoint evaluates the same three hard constraints used by auto-assign (language, expertise, availability) and ranks results by fewest same-day assignments, then highest rating, then lowest ID.

#### Example Request

```http
GET /schedules/10/eligible-guides
```

#### Success Response (200) — Guides Found

```json
{
  "schedule_id": 10,
  "eligible_guides": [
    {
      "id": 3,
      "first_name": "Maria",
      "last_name": "Silva",
      "guide_rating": 4.8,
      "same_day_assignments": 1,
      "ranking_position": 1
    },
    {
      "id": 7,
      "first_name": "John",
      "last_name": "Doe",
      "guide_rating": 4.5,
      "same_day_assignments": 2,
      "ranking_position": 2
    }
  ],
  "reasons": [],
  "total": 2
}
```

#### Success Response (200) — No Eligible Guides

Returns an empty list (not an error) with reason codes explaining why no guides qualified.

```json
{
  "schedule_id": 10,
  "eligible_guides": [],
  "reasons": ["NO_LANGUAGE_MATCH"],
  "total": 0
}
```

Possible reason codes: `NO_LANGUAGE_MATCH`, `NO_EXPERTISE_MATCH`, `NO_AVAILABILITY_MATCH`.

#### Error Cases

- `404 Not Found`: schedule does not exist.

#### Frontend Usage

```js
// Preview eligible guides before assigning
export async function getEligibleGuides(scheduleId) {
  return fetchAPI(`/schedules/${scheduleId}/eligible-guides`)
}
```

### Assignment Error Cases

- `404 Not Found`: schedule or guide does not exist.
- `400 Bad Request`: guide is inactive.
- `422 Unprocessable Entity`: no eligible guide (auto-assign only).

### Frontend Usage

```js
// Auto-assign a guide
export async function autoAssignGuide(scheduleId) {
  return fetchAPI(`/schedules/${scheduleId}/assign`, { method: 'POST' })
}

// Manual assign a guide (admin override)
export async function manualAssignGuide(scheduleId, guideId, reason = null) {
  return fetchAPI(`/schedules/${scheduleId}/assign`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ guide_id: guideId, reason }),
  })
}
```
