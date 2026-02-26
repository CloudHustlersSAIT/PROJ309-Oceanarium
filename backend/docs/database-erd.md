# Database Schema Documentation

## Entity-Relationship Diagram

![ERD](erd.png)

---

## Tables

### Booking Domain

#### `bookings`

Main booking record synced from the Clorian external system.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `booking_id` | Integer | PK, indexed | Auto-generated primary key |
| `clorian_booking_id` | String | NOT NULL, UNIQUE, indexed | External ID from Clorian |
| `customer_id` | Integer | FK -> `customers.id`, nullable | Associated customer |
| `tour_id` | Integer | FK -> `tours.id`, nullable | Associated tour |
| `created_at` | DateTime | NOT NULL, default=utcnow | Record creation timestamp |

**Relationships:** has many `booking_versions`, belongs to `customers`, belongs to `tours`

---

#### `booking_versions`

Immutable temporal snapshots of a booking's state. Each change creates a new version rather than mutating the record.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `booking_id` | Integer | FK -> `bookings.booking_id`, NOT NULL | Parent booking |
| `hash` | String(64) | NOT NULL | Content hash for idempotency checks |
| `status` | String(50) | NOT NULL | Booking status (`pending`, `cancelled`, etc.) |
| `adult_tickets` | Integer | NOT NULL | Number of adult tickets |
| `child_tickets` | Integer | NOT NULL | Number of child tickets |
| `start_date` | Date | NOT NULL | Scheduled date for the booking |
| `received_at` | DateTime | NOT NULL, default=utcnow | When this version was received |
| `valid_from` | DateTime | NOT NULL | Start of this version's validity |
| `poll_execution_id` | Integer | FK -> `poll_execution.id`, nullable | Sync cycle that created this version |

**Unique constraint:** `(booking_id, hash)` — prevents duplicate versions for the same content

**Relationships:** belongs to `bookings`, belongs to `poll_execution`, has many `schedules`, has many `surveys`

---

#### `customers`

Customer information.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `first_name` | String | NOT NULL | Customer first name |
| `last_name` | String | NOT NULL | Customer last name |
| `email` | String | NOT NULL | Customer email |
| `phone` | String | nullable | Customer phone number |

**Relationships:** has many `bookings`, has many `surveys`

---

### Guide Domain

#### `guides`

Tour guides who can be assigned to bookings.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `first_name` | String | NOT NULL | Guide first name |
| `last_name` | String | NOT NULL | Guide last name |
| `email` | String | NOT NULL, UNIQUE | Guide email |
| `phone` | String | NOT NULL, default="" | Guide phone number |
| `guide_rating` | Numeric | nullable, default=0 | Average rating from surveys |
| `is_active` | Boolean | NOT NULL, default=true | Whether the guide is currently active |

**Relationships:** many-to-many with `languages`, `expertises`, `tours`; has one `availability_patterns`; has many `schedules`, `surveys`

---

#### `languages`

Languages that guides can speak.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `code` | String | NOT NULL, UNIQUE | ISO language code (e.g. `en`, `pt`) |
| `name` | String | NOT NULL | Full language name |

**Relationships:** many-to-many with `guides` via `guide_languages`

---

#### `expertises`

Areas of expertise that guides can have.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `name` | String | NOT NULL | Expertise name (e.g. "Sharks", "Coral Reef") |
| `category` | String | NOT NULL | Expertise category (e.g. "Marine Biology") |

**Relationships:** many-to-many with `guides` via `guide_expertises`

---

#### `guide_languages` (junction)

| Column | Type | Constraints | Description |
|---|---|---|---|
| `guide_id` | Integer | PK, FK -> `guides.id` | Guide reference |
| `language_id` | Integer | PK, FK -> `languages.id` | Language reference |

---

#### `guide_expertises` (junction)

| Column | Type | Constraints | Description |
|---|---|---|---|
| `guide_id` | Integer | PK, FK -> `guides.id` | Guide reference |
| `expertise_id` | Integer | PK, FK -> `expertises.id` | Expertise reference |

---

#### `guide_tour_types` (junction)

| Column | Type | Constraints | Description |
|---|---|---|---|
| `guide_id` | Integer | PK, FK -> `guides.id` | Guide reference |
| `tour_id` | Integer | PK, FK -> `tours.id` | Tour reference |

---

### Availability Domain

#### `availability_patterns`

Weekly availability pattern for a guide (one-to-one with guides).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `guide_id` | Integer | FK -> `guides.id`, NOT NULL, UNIQUE | Owning guide (1:1) |
| `timezone` | String | NOT NULL, default="UTC" | Guide's local timezone |

**Relationships:** belongs to `guides`, has many `availability_slots`, has many `availability_exceptions`

---

#### `availability_slots`

Recurring weekly time slots when a guide is available.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `pattern_id` | Integer | FK -> `availability_patterns.id`, NOT NULL | Parent pattern |
| `day_of_week` | Integer | NOT NULL | Day of week (0=Monday ... 6=Sunday) |
| `start_time` | Time | NOT NULL | Slot start time |
| `end_time` | Time | NOT NULL | Slot end time |

**Relationships:** belongs to `availability_patterns`

---

#### `availability_exceptions`

Date-specific overrides to a guide's weekly pattern.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `pattern_id` | Integer | FK -> `availability_patterns.id`, NOT NULL | Parent pattern |
| `date` | Date | NOT NULL | The specific date |
| `type` | String | NOT NULL | Exception type: `"blocked"` or `"note"` |
| `reason` | String | nullable | Optional explanation |

**Relationships:** belongs to `availability_patterns`

---

### Tour & Scheduling Domain

#### `tours`

Tour types offered by the Oceanarium.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `name` | String | nullable | Tour name |
| `description` | String | nullable | Tour description |
| `duration` | Integer | nullable | Duration in minutes |

**Relationships:** has many `bookings`, `costs`, `tour_resources`, `tour_assignment_logs`; many-to-many with `guides` via `guide_tour_types`

---

#### `schedule`

Assigns a guide (and optionally a resource) to a specific booking version.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `booking_version_id` | Integer | FK -> `booking_versions.id`, NOT NULL | The booking version being scheduled |
| `guide_id` | Integer | FK -> `guides.id`, NOT NULL | Assigned guide |
| `resource_id` | Integer | FK -> `resources.id`, nullable | Optionally assigned resource |
| `start_date` | DateTime | NOT NULL | Schedule start |
| `end_date` | DateTime | NOT NULL | Schedule end |

**Relationships:** belongs to `booking_versions`, belongs to `guides`, belongs to `resources`

---

#### `cost`

Ticket pricing per tour with temporal validity.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `tour_id` | Integer | FK -> `tours.id`, NOT NULL | Associated tour |
| `ticket_type` | String(20) | NOT NULL | Type of ticket (e.g. "adult", "child") |
| `price` | Numeric(10,2) | NOT NULL | Ticket price |
| `valid_from` | DateTime | NOT NULL | Price validity start |
| `valid_to` | DateTime | NOT NULL | Price validity end |

**Relationships:** belongs to `tours`

---

#### `resources`

Physical resources available at the Oceanarium.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `name` | String | nullable | Resource name |
| `type` | String | nullable | Resource type |
| `quantity_available` | Integer | nullable | Total quantity available |

**Relationships:** has many `schedules`

---

#### `tour_resources` (junction)

Maps which resources a tour requires and in what quantity.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `tour_id` | Integer | PK, FK -> `tours.id` | Tour reference |
| `resource_id` | Integer | PK, FK -> `resources.id` | Resource reference |
| `quantity_required` | Integer | NOT NULL | How many units the tour needs |

**Relationships:** belongs to `tours`, belongs to `resources`

---

### Feedback Domain

#### `surveys`

Post-visit customer feedback linking a customer, guide, and booking version.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `customer_id` | Integer | FK -> `customers.id`, NOT NULL | Customer who submitted |
| `guide_id` | Integer | FK -> `guides.id`, NOT NULL | Guide being rated |
| `booking_version_id` | Integer | FK -> `booking_versions.id`, NOT NULL | Associated booking version |
| `comment` | String | nullable | Free-text feedback |
| `rating` | Integer | NOT NULL | Numeric rating |

**Relationships:** belongs to `customers`, belongs to `guides`, belongs to `booking_versions`

---

### Sync / Operational Domain

#### `poll_execution`

Tracks individual Clorian polling cycles.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `window_start` | DateTime | NOT NULL | Poll window start |
| `window_end` | DateTime | NOT NULL | Poll window end |
| `executed_at` | DateTime | NOT NULL, default=utcnow | When the poll ran |
| `status` | String(50) | NOT NULL | Execution status (`running`, `success`, `failed`) |

**Relationships:** has many `booking_versions`

---

#### `sync_logs`

High-level audit log for each Clorian sync cycle.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `started_at` | DateTime | NOT NULL, default=utcnow | Cycle start time |
| `finished_at` | DateTime | nullable | Cycle end time |
| `new_count` | Integer | default=0 | Bookings created in this cycle |
| `changed_count` | Integer | default=0 | Bookings updated in this cycle |
| `cancelled_count` | Integer | default=0 | Bookings cancelled in this cycle |
| `status` | String | NOT NULL, default="running" | Cycle status (`running`, `success`, `failed`) |
| `errors` | Text | nullable | Error details if the cycle failed |

**Relationships:** standalone (no FKs)

---

#### `tour_assignment_logs`

Audit trail for guide-to-tour assignments (auto and manual).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `tour_id` | Integer | FK -> `tours.id`, NOT NULL | The tour involved |
| `guide_id` | Integer | FK -> `guides.id`, nullable | The guide involved |
| `assigned_at` | DateTime | NOT NULL, default=utcnow | When the action occurred |
| `assigned_by` | String | nullable | `null` for auto-assignment, admin email for manual |
| `assignment_type` | String | NOT NULL | `"auto"` or `"manual"` |
| `action` | String | NOT NULL | `"assigned"`, `"released"`, or `"reassigned"` |

**Relationships:** belongs to `tours`, belongs to `guides` (optional)

---

### Auth / Standalone

#### `users`

Application users for authentication and authorization.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `username` | String | NOT NULL, UNIQUE | Login username |
| `email` | String | NOT NULL, UNIQUE | User email |
| `password_hash` | String | NOT NULL | Hashed password |
| `full_name` | String | NOT NULL | Display name |
| `role` | String | NOT NULL | User role |
| `is_active` | Boolean | NOT NULL, default=true | Whether the account is active |
| `created_at` | DateTime | NOT NULL, default=utcnow | Account creation timestamp |

**Relationships:** standalone (no FKs)

---

#### `issues`

Operational issue tracker.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PK, indexed | Auto-generated primary key |
| `description` | String | NOT NULL | Issue description |
| `created_at` | DateTime | NOT NULL, default=utcnow | When the issue was reported |

**Relationships:** standalone (no FKs)

---

## Summary

| Domain | Tables | Count |
|---|---|---|
| Booking | `bookings`, `booking_versions`, `customers` | 3 |
| Guide | `guides`, `languages`, `expertises`, `guide_languages`, `guide_expertises`, `guide_tour_types` | 6 |
| Availability | `availability_patterns`, `availability_slots`, `availability_exceptions` | 3 |
| Tour & Scheduling | `tours`, `schedule`, `cost`, `resources`, `tour_resources` | 5 |
| Feedback | `surveys` | 1 |
| Sync / Ops | `poll_execution`, `sync_logs`, `tour_assignment_logs` | 3 |
| Auth / Standalone | `users`, `issues` | 2 |
| **Total** | | **23** |
