# Admin Screen: Home

## Route and Access

- Route: `/home`
- Access: authenticated admin only

## Purpose

Provide an operational snapshot of today and guide the next best admin actions.

## Key User Actions

- Review today's schedule highlights
- Inspect alerts and health indicators
- Navigate to calendar, bookings, dashboard, and notifications

## Data Dependencies

- API: `getSchedules()`, `getStats()`

## UI States

- `loading`: schedule/stat fetch in progress
- `scheduleLoadWarning`: partial or delayed sync warning
- Alert blocks with severity styling
- Truncated schedule list with overflow indicator

## Business Rules and Notes

- Home prioritizes actionable operations (unassigned guides, delayed or cancelled items).
- Intended as an operations launchpad, not a deep analytics view.

## Quick Manual Test Checklist

1. Home loads with current-day schedule cards.
2. Alerts appear when edge conditions exist.
3. Quick navigation actions route correctly.

## Related Source Files

- `frontend/src/views/HomeView.vue`
- `frontend/src/services/api.js`
