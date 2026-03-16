# Admin Screen: Calendar

## Route and Access

- Route: `/calendar`
- Access: authenticated admin only

## Purpose

Plan schedules and manage guide assignment workflows in a calendar-first interface.

## Key User Actions

- Create schedule events
- Manually assign guides to schedules
- Auto-assign guides
- Remove/cancel guide assignment from a schedule
- Inspect eligible guides and assignment reasons

## Data Dependencies

- Store: `useCalendarStore()`
- API: `getTours()`, `createSchedule()`, `manualAssignGuide()`, `autoAssignGuide()`, `cancelGuideFromSchedule()`, `getEligibleGuides()`, `getGuideLanguages()`

## UI States

- Loading states for schedules, tours, and candidates
- Form-level validation errors for schedule creation
- Assignment result notices and reason summaries
- Modal/dialog flows for assignment operations

## Business Rules and Notes

- Calendar is centered on schedule entities (not raw reservations).
- Assignment UX should reflect backend constraints and warnings clearly.
- See backend contract details in `backend/docs/SCHEDULE_ENDPOINT_FRONTEND_GUIDE.md`.

## Quick Manual Test Checklist

1. New schedule appears in the expected day/time slot.
2. Manual assignment updates event details.
3. Auto-assign returns clear success or unassignable reason.
4. Eligible guide preview aligns with assignment behavior.

## Related Source Files

- `frontend/src/views/CalendarView.vue`
- `frontend/src/stores/calendar.js`
- `backend/docs/SCHEDULE_ENDPOINT_FRONTEND_GUIDE.md`
