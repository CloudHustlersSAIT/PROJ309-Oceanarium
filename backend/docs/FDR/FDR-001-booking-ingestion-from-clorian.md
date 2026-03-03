# [FDR-001] Booking Ingestion from Clorian

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | FDR-001                |
| **Version**      | 2.0                    |
| **Status**       | Draft                  |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-03             |
| **Last Updated** | 2026-03-03             |

---

## 1. Purpose

Clorian is the external ticketing system where customers purchase Oceanarium tour tickets. The Oceanarium backend must periodically poll Clorian, ingest new and changed data across three entity levels (Purchase → Reservation → Ticket), and store them with full version history to enable downstream scheduling and guide assignment.

## 2. Scope

### In Scope

- Polling Clorian for new/updated/cancelled purchases, reservations, and tickets
- 3-level ingestion: Purchase → Reservation → Ticket
- Selective field storage (not all Clorian fields are persisted)
- Change detection via payload hashing
- Tracking each poll execution for observability

### Out of Scope

- Guide assignment (see [FDR-002])
- Auto re-scheduling on changes (see [FDR-004])
- Notifications (see [FDR-003])
- Clorian API authentication details (infrastructure concern)
- Capacity management (Clorian's responsibility)
- Resource management (future phase)

## 3. Actors

| Actor | Description |
|-------|-------------|
| **Clorian** | External ticketing system — source of truth for ticket purchases |
| **Poll Execution Service** | Internal scheduled job that queries Clorian |
| **Booking Ingestion Service** | Processes raw Clorian data into our domain model |

## 4. Clorian Data Model

Clorian exposes a 3-level hierarchy:

```
Purchase (customer transaction)
  └── Reservation (a tour/product at a specific time)
        └── Ticket (individual attendee: adult, child, etc.)
```

### 4.1 Purchase Payload

```json
{
  "purchaseId": 90010001,
  "clientId": 200,
  "languageCode": "en",
  "firstName": "Alex",
  "lastName": "Miller",
  "formAnswerList": [
    {
      "answer": "Canada",
      "purchaseId": 90010001,
      "answerValue": "CA",
      "genericFieldId": 4001,
      "genericFieldName": "Country",
      "genericFieldAnswerId": 70010001
    },
    {
      "answer": "School Bus",
      "purchaseId": 90010001,
      "genericFieldId": 4002,
      "genericFieldName": "Transportation",
      "genericFieldAnswerId": 70010002
    },
    {
      "answer": "Yes",
      "purchaseId": 90010001,
      "genericFieldId": 4003,
      "genericFieldName": "Consent",
      "genericFieldAnswerId": 70010003
    }
  ],
  "acceptedLopd": true,
  "appUserId": 50001,
  "webCookie": "b7d1c29a-92ab-4e1b-9f52-4e3c2fa8f1d9",
  "createdAt": "2026-03-10T14:15:22.123456Z",
  "modifiedAt": "2026-03-10T14:15:22.123456Z"
}
```

**Fields we store:**

| Clorian Field | Our Column | Table | Notes |
|---|---|---|---|
| `purchaseId` | `clorian_purchase_id` | `purchases` | Unique key for matching |
| `clientId` | `customer_id` | `purchases` | FK → `customers` (upsert by `clientId`) |
| `languageCode` | `language_code` | `purchases` | **Critical** for guide assignment |
| `firstName` | `first_name` | `customers` | Upserted |
| `lastName` | `last_name` | `customers` | Upserted |
| `createdAt` | `clorian_created_at` | `purchases` | Audit |
| `modifiedAt` | `clorian_modified_at` | `purchases` | Change detection |

**Fields we skip:** `formAnswerList`, `acceptedLopd`, `appUserId`, `webCookie`

### 4.2 Reservation Payload

```json
{
  "reservationId": 91020001,
  "purchaseId": 90010001,
  "creationDate": "2026-03-10T14:10:00Z",
  "modificationDate": "2026-03-10T14:10:00Z",
  "confirmationDate": "2026-03-10T14:10:00Z",
  "eventStartDatetime": "2026-03-15T10:00:00Z",
  "total": 75.00,
  "status": "confirmed",
  "currentTicketNum": 10,
  "productId": 3001,
  "productName": "Ocean Discovery Tour",
  "productCategoryId": 800,
  "productCategoryName": "Education",
  "salesGroupId": 1600,
  "salesGroupName": "Online Sales",
  "productPriceByPackage": false,
  "encryptedReservationId": "AbC9XyZ12345==",
  "schedulingStatus": "scheduled",
  "formAnswerList": [
    {
      "answer": "Introduction to Marine Life",
      "answerValue": "EDU01",
      "reservationId": 91020001,
      "genericFieldId": 4101,
      "genericFieldName": "Program Theme",
      "genericFieldAnswerId": 70020001
    }
  ],
  "createdAt": "2026-03-10T14:15:30.654321Z",
  "modifiedAt": "2026-03-10T14:20:00.000000Z"
}
```

**Fields we store:**

| Clorian Field | Our Column | Table | Notes |
|---|---|---|---|
| `reservationId` | `clorian_reservation_id` | `bookings` | Unique key for matching |
| `purchaseId` | `purchase_id` | `bookings` | FK → `purchases` |
| `eventStartDatetime` | `event_start_datetime` | `bookings` | **Critical** for scheduling |
| `status` | `status` | `bookings` | `confirmed` / `cancelled` |
| `currentTicketNum` | `current_ticket_num` | `bookings` | Total ticket count |
| `productId` | `tour_id` | `bookings` | FK → `tours` (mapped via `clorian_product_id`) |
| `productName` | `name` | `tours` | Upserted into tours catalog |
| `createdAt` | `clorian_created_at` | `bookings` | Audit |
| `modifiedAt` | `clorian_modified_at` | `bookings` | Change detection |

**Fields we skip:** `total`, `productCategoryId/Name`, `salesGroupId/Name`, `productPriceByPackage`, `encryptedReservationId`, `confirmationDate`, `creationDate`, `modificationDate` (we use `createdAt`/`modifiedAt`), `formAnswerList`, `schedulingStatus` (we manage our own)

### 4.3 Ticket Payload

```json
{
  "ticketId": 92030001,
  "reservationId": 91020001,
  "buyerTypeId": 5200,
  "buyerTypeName": "Children (6–10 years)",
  "amount": 7.50,
  "eventId": 60010001,
  "startDatetime": "2026-03-15T10:00:00Z",
  "endDatetime": "2026-03-15T11:00:00Z",
  "ticketStatus": "valid",
  "price": 7.50,
  "taxRate": 0.06,
  "ticketGroupId": 130001,
  "availabilityGroupId": 2100,
  "venueId": 3800,
  "venueName": "Discovery Lab",
  "venueCapacityId": 4300,
  "venueCapacityName": "Discovery Lab",
  "barcode": "OCN2026031592030001",
  "schedulingStatus": "scheduled",
  "ticketComplementSet": [],
  "ticketExtraSet": [],
  "createdAt": "2026-03-10T14:15:45.987654Z",
  "modifiedAt": "2026-03-10T14:20:05.000000Z"
}
```

**Fields we store:**

| Clorian Field | Our Column | Table | Notes |
|---|---|---|---|
| `ticketId` | `clorian_ticket_id` | `tickets` | Unique key for matching |
| `reservationId` | `booking_id` | `tickets` | FK → `bookings` (mapped via `clorian_reservation_id`) |
| `buyerTypeId` | `buyer_type_id` | `tickets` | Category ID (adult, child, etc.) |
| `buyerTypeName` | `buyer_type_name` | `tickets` | Human-readable label |
| `startDatetime` | `start_datetime` | `tickets` | Ticket-level start |
| `endDatetime` | `end_datetime` | `tickets` | Ticket-level end |
| `ticketStatus` | `ticket_status` | `tickets` | `valid` / `cancelled` |
| `price` | `price` | `tickets` | Unit price |
| `venueId` | `venue_id` | `tickets` | Useful for guide logistics |
| `venueName` | `venue_name` | `tickets` | Denormalized for display |
| `createdAt` | `clorian_created_at` | `tickets` | Audit |
| `modifiedAt` | `clorian_modified_at` | `tickets` | Change detection |

**Fields we skip:** `amount` (same as price), `taxRate`, `eventId`, `ticketGroupId`, `availabilityGroupId`, `venueCapacityId/Name` (capacity is Clorian's job), `barcode`, `schedulingStatus`, `ticketComplementSet`, `ticketExtraSet`

## 5. Functional Requirements

### FR-1: Poll Clorian on a scheduled interval

- **Description**: A background job runs at a configurable interval and queries Clorian for entities modified within the polling window.
- **Input**: `window_start`, `window_end` (timestamps)
- **Output**: Raw payloads for purchases, reservations, and tickets
- **Business Rules**:
  - Windows must not overlap or leave gaps between consecutive runs
  - If a poll fails, the window must be retried on the next execution
  - All three entity types (purchase, reservation, ticket) are polled in each cycle
- **Acceptance Criteria**:
  - A `poll_execution` record is created for every run with status `RUNNING` → `SUCCESS` or `FAILED`
  - `window_start` and `window_end` are persisted for auditability

### FR-2: Ingest purchases and upsert customers

- **Description**: For each purchase from Clorian, upsert the customer and create/update the purchase record.
- **Input**: Clorian purchase payload
- **Output**: `customers` row (upserted) + `purchases` row (created or updated)
- **Business Rules**:
  - Match customer on `clientId`; upsert `first_name`, `last_name`
  - Match purchase on `clorian_purchase_id` (unique key)
  - `language_code` is always stored — it drives downstream guide assignment
  - If `language_code` changes on an existing purchase, emit a `PurchaseLanguageChanged` event (triggers re-scheduling — see [FDR-004])
- **Acceptance Criteria**:
  - New purchase → new `customers` + `purchases` rows
  - Existing purchase with changed `modifiedAt` → updated `purchases` row
  - Language change detected and event emitted

### FR-3: Ingest reservations as bookings with versioning

- **Description**: For each reservation from Clorian, create/update the booking and create a new version if the payload changed.
- **Input**: Clorian reservation payload
- **Output**: `bookings` row + `booking_versions` row (if changed)
- **Business Rules**:
  - Match on `clorian_reservation_id` (unique key)
  - Map `productId` → `tours.clorian_product_id` to resolve `tour_id`; upsert tour if new
  - Compute `hash` from stored fields; if hash matches latest version → `UNCHANGED`, skip
  - If hash differs → new `booking_versions` row with `valid_from = NOW()`
  - Detect scheduling-relevant changes (see [FDR-004]):
    - `event_start_datetime` changed → `BookingTimeChanged` event
    - `status` changed to `cancelled` → `BookingCancelled` event
    - `tour_id` changed → `BookingTourChanged` event
- **Acceptance Criteria**:
  - New reservation → new `bookings` + `booking_versions` row
  - Changed reservation → new `booking_versions` row, previous untouched
  - Unchanged reservation → no new version
  - `poll_execution_id` set on every new version

### FR-4: Ingest tickets

- **Description**: For each ticket from Clorian, create/update the ticket record.
- **Input**: Clorian ticket payload
- **Output**: `tickets` row (created or updated)
- **Business Rules**:
  - Match on `clorian_ticket_id` (unique key)
  - Map `reservationId` → `bookings.clorian_reservation_id` to resolve `booking_id`
  - If `ticketStatus` changes to `cancelled`, update the record (no versioning needed for tickets)
- **Acceptance Criteria**:
  - New ticket → new `tickets` row linked to the correct booking
  - Updated ticket → existing row updated
  - Cancelled ticket → `ticket_status = 'cancelled'`

### FR-5: Handle cancellations

- **Description**: When Clorian reports a reservation as cancelled, create a cancellation version and trigger downstream processes.
- **Input**: Reservation payload with `status = 'cancelled'`
- **Output**: New `booking_versions` row + `BookingCancelled` event
- **Business Rules**:
  - Cancelling a booking does NOT delete data — immutable history preserved
  - If the booking is assigned to a schedule, emit `BookingCancelled` for downstream handling (see [FDR-004])
  - Associated tickets are also marked cancelled
- **Acceptance Criteria**:
  - Cancelled bookings have a version with `status = 'cancelled'`
  - `BookingCancelled` event emitted
  - Booking's `schedule_id` is NOT automatically cleared (downstream process handles it)

### FR-6: Track sync metrics

- **Description**: After each poll execution, record aggregated metrics.
- **Input**: Counts of new, changed, and cancelled entities
- **Output**: `sync_logs` row linked to `poll_execution`
- **Business Rules**:
  - One `sync_logs` entry per poll execution
  - Failed polls log the error in `sync_logs.errors`
- **Acceptance Criteria**:
  - `new_count`, `changed_count`, `cancelled_count` are accurate
  - `status` is `SUCCESS` or `FAILED`

## 6. Data Model Impact

| Table | Impact |
|-------|--------|
| `customers` | Upserted from Clorian purchase `clientId`, `firstName`, `lastName` |
| `purchases` | New rows from Clorian purchases; carries `language_code` |
| `bookings` | New rows from Clorian reservations; the schedulable unit |
| `booking_versions` | New row per detected change on a booking |
| `tickets` | New rows from Clorian tickets; individual attendees |
| `tours` | Upserted from Clorian `productId`/`productName` |
| `poll_execution` | New row per polling cycle |
| `sync_logs` | New row per polling cycle with metrics |

## 7. API Contracts

The polling is a background job. An admin endpoint is exposed for manual triggers:

### `POST /admin/poll/trigger`

**Response (200):**
```json
{
  "poll_execution_id": 42,
  "status": "SUCCESS",
  "new_count": 5,
  "changed_count": 2,
  "cancelled_count": 1
}
```

## 8. Error Handling

| Scenario | Expected Behavior | HTTP Status |
|----------|-------------------|-------------|
| Clorian API unreachable | `poll_execution.status = 'FAILED'`, retry next cycle | N/A (background) |
| Unknown `productId` from Clorian | Auto-create tour with `clorian_product_id` | N/A |
| Reservation references unknown `purchaseId` | Log warning, skip record, continue batch | N/A |
| Duplicate external ID race condition | DB unique constraint prevents duplicates | N/A |
| Manual trigger while poll is running | Return 409 Conflict | 409 |

## 9. Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| Clorian API | External | Source of truth; polling-based integration |
| PostgreSQL | Infrastructure | Target database |
| Scheduler (cron/Celery/APScheduler) | Infrastructure | Triggers the polling job |
| [FDR-004] Auto Re-scheduling | Internal | Consumes domain events from ingestion |

## 10. Open Questions

| # | Question | Answer | Status |
|---|----------|--------|--------|
| 1 | Exact Clorian API contract (endpoints, auth, pagination)? | TBD | Open |
| 2 | Desired polling interval? | 5 min (proposed) | Open |
| 3 | Does Clorian support webhooks as alternative to polling? | TBD | Open |
| 4 | Should `email` be stored on customers? Clorian purchase doesn't include it. | May come from a separate Clorian endpoint | Open |
| 5 | How to handle `formAnswerList` if needed in the future? | Store as JSONB on purchases/bookings if needed | Deferred |

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-03 | Evandro Maciel | Initial draft |
| 2.0     | 2026-03-03 | Evandro Maciel | Rewritten for 3-level Clorian model (Purchase→Reservation→Ticket); added full payload examples and field mapping tables; added `purchases` and `tickets` ingestion; domain events for scheduling triggers |
