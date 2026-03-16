# Admin Screen: Notifications

## Route and Access

- Route: `/notifications`
- Access: authenticated admin only

## Purpose

Manage operational notifications with filtering, triage, and read lifecycle actions.

## Key User Actions

- Search notifications
- Filter by event type and read state
- Mark items as read
- Delete notifications after confirmation
- Open notification details

## Data Dependencies

- Store: `useNotificationStore()`
- Store-backed API integration from notification store actions

## UI States

- `loading`: notifications retrieval
- Empty state adapted to active filters
- Summary cards (total/unread/urgent/action required)
- Pagination (10 per page)
- Delete confirmation dialog

## Business Rules and Notes

- Admin notifications are authenticated-only.
- Read/unread handling is part of core triage workflow.

## Quick Manual Test Checklist

1. Filters change list and counters consistently.
2. Mark-as-read updates badges and counts.
3. Delete flow requires confirmation and removes item.
4. Search debounce does not spam requests.

## Related Source Files

- `frontend/src/views/NotificationsView.vue`
- `frontend/src/stores/notification.js`
