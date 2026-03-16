# Frontend Documentation Overview

This folder centralizes product-facing frontend documentation for active admin screens.

## Scope

- Covers active admin routes defined in `frontend/src/router/index.js`.
- Documents expected behavior from a user and maintenance perspective.
- Complements API contract docs such as `backend/docs/SCHEDULE_ENDPOINT_FRONTEND_GUIDE.md`.

## Document Map

### Active Admin Screens

- `ADMIN_HOME.md`
- `ADMIN_DASHBOARD.md`
- `ADMIN_NOTIFICATIONS.md`
- `ADMIN_ASSETS.md`
- `ADMIN_BOOKINGS.md`
- `ADMIN_CALENDAR.md`
- `ADMIN_SETTINGS.md`

## Standard Structure (Used in Each Screen Doc)

1. Route and access control
2. Purpose
3. Key user actions
4. Data dependencies
5. UI states
6. Business rules and notes
7. Quick manual test checklist
8. Related source files

## Update Policy

- Update screen docs in the same PR whenever behavior changes.
- Keep examples concise and tied to actual implemented flows.
- Prefer factual behavior over aspirational behavior.
- If backend contract changes, update the screen doc and link to the relevant backend doc.

## References

- Router: `frontend/src/router/index.js`
- Frontend setup: `frontend/README.md`
- API and integration docs: `backend/docs/`