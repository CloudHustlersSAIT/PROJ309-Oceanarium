# Admin Screen: Assets

## Route and Access

- Route: `/assets`
- Access: authenticated admin only

## Purpose

Manage customer and guide records from a dual-tab operational directory.

## Key User Actions

- Switch between customers and guides
- Search, sort, and filter entries
- Edit customer and guide records
- Create new guide
- Review guide expertise, availability, and languages

## Data Dependencies

- API: `getCustomers()`, `getGuides()`, `getTours()`, `getLanguages()`, `createGuide()`, `updateCustomer()`, `updateGuide()`

## UI States

- Loading states for lists and editor options
- Empty states for customer/guide datasets
- Pagination (15 per page)
- Inline and modal form validation

## Business Rules and Notes

- Asset updates should maintain data quality for downstream scheduling and assignment workflows.
- Guide creation/editing depends on language and expertise option data.

## Quick Manual Test Checklist

1. Search/sort/filter combinations return expected subset.
2. Edit customer persists and reflects in list.
3. Create guide persists and appears in guide tab.
4. Invalid form values show validation feedback.

## Related Source Files

- `frontend/src/views/AssetsView.vue`
- `frontend/src/services/api.js`
