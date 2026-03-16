# Admin Screen: Dashboard

## Route and Access

- Route: `/dashboard`
- Access: authenticated admin only

## Purpose

Show operational KPIs and trends across selectable time windows.

## Key User Actions

- Switch time ranges (all-time, month, week, day)
- Review KPI cards and trend deltas
- Review operational alerts and read state

## Data Dependencies

- API: `getStats()`, `getSchedules()`, `getBookings()`, `getGuides()`, `getTours()`
- Local persistence: `localStorage` key `dashboard-alert-read-state-v1`

## UI States

- `loading`: metrics retrieval in progress
- `apiError`: hard failure state
- `apiWarnings`: degraded data quality warnings
- Alert cards with read/unread handling

## Business Rules and Notes

- Trend deltas are calculated against a previous comparison window.
- Alerting is based on configured thresholds (cancellation/occupancy/coverage signals).

## Quick Manual Test Checklist

1. Changing range updates KPIs and charts.
2. API failure renders user-visible error.
3. Alert read state persists across refresh.

## Related Source Files

- `frontend/src/views/DashboardView.vue`
- `frontend/src/services/api.js`
