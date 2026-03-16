# Admin Screen: Settings

## Route and Access

- Route: `/settings`
- Access: authenticated admin only

## Purpose

Manage admin operational preferences and policy-related settings.

## Key User Actions

- Update profile display values
- Adjust timezone/language settings
- Configure policy and notification toggles
- Save section-level settings

## Data Dependencies

- Auth context: `user`, `profile`
- Local persistence: `localStorage` key `oceanarium-admin-settings-v1`

## UI States

- Save confirmation info messages
- Validation feedback for selectable policy options
- Persisted values after reload

## Business Rules and Notes

- Current implementation persists admin preferences client-side.
- Settings affect UX and operational defaults, not authentication identity.

## Quick Manual Test Checklist

1. Updated values persist after browser refresh.
2. Invalid options are rejected with feedback.
3. Section save message appears after update.

## Related Source Files

- `frontend/src/views/SettingsView.vue`
- `frontend/src/contexts/authContext.js`
