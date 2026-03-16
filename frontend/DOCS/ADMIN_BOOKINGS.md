# Admin Screen: Bookings

## Route and Access

- Route: `/bookings`
- Access: authenticated admin only

## Purpose

Create and manage reservations, including rescheduling and cancellation.

## Key User Actions

- Search bookings
- Create booking
- Reschedule booking
- Cancel booking
- Filter by customer

## Data Dependencies

- API: `getSchedules()`, `getBookings()`, `createBooking()`, `rescheduleBooking()`, `cancelBooking()`

## UI States

- `loading`: booking/schedule retrieval
- Create success and error messaging
- Form validation for customer and ticket fields
- Pagination (15 per page)

## Business Rules and Notes

- Booking operations depend on schedule availability and backend validation.
- Search input uses debounce behavior for list updates.

## Quick Manual Test Checklist

1. Create booking success adds new item to list.
2. Invalid booking payload shows error.
3. Reschedule updates booking date/time correctly.
4. Cancellation updates status and UI actions.

## Related Source Files

- `frontend/src/views/BookingsView.vue`
- `frontend/src/services/api.js`
