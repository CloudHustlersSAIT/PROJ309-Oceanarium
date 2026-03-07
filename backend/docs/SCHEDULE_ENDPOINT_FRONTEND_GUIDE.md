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
