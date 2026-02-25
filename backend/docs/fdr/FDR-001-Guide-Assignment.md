# Functional Requirements Document: Guide Assignment

| Field            | Detail             |
| ---------------- | ------------------ |
| **FDR Number**   | FDR-001            |
| **Author**       | Evandro Maciel     |
| **Date Created** | February 12, 2026  |
| **Version**      | 1.1                |

---

## 1. Purpose

This document defines the functional requirements for the automated Guide Assignment feature within the Oceanarium Tour Scheduling System. Tours are booked by customers through the **Clorian System** (third-party booking platform). Our system must pull booking data from Clorian, detect new, changed, or cancelled bookings, and automatically assign the most suitable guide based on availability, expertise, and language criteria.

---

## 2. Scope

This FDR covers:

- Integration with Clorian to sync tour bookings.
- Logic and rules for determining guide eligibility.
- Automated guide assignment and reassignment.

It does not cover the Clorian booking interface itself, visitor-facing features, or payment processing.

---

## 3. Actors

- **Clorian System**: External booking platform where customers book tours. Source of truth for booking data.
- **System**: Pulls bookings from Clorian, evaluates guide suitability, and performs assignment.
- **Admin**: Can manually override assignments, manage guide profiles, and configure availability patterns.
- **Guide**: Can update personal availability, view assigned tours, and request exceptions.

---

## 4. Assumptions

- Each tour requires exactly one guide.
- A guide can only be assigned to one tour at a time (no overlapping assignments).
- Guide profiles (languages, expertise, availability) are kept up to date by admins or guides themselves.
- All times follow the timezone defined in the guide's `AvailabilityPattern`.
- Clorian is the single source of truth for bookings. Our system never creates bookings — it only consumes them.
- Clorian provides an API or data export that can be queried on a scheduled basis.

---

## 5. Functional Requirements

### FR-01: Clorian Booking Sync

- The system must pull tour bookings from the Clorian System every **15 minutes** via scheduled sync.
- Each sync must detect:
  - **New bookings**: Tours that don't exist yet in our system → create and trigger guide assignment.
  - **Changed bookings**: Tours whose date, time, expertise, or language has been modified → reassess current guide assignment.
  - **Cancelled bookings**: Tours that no longer exist in Clorian → release the assigned guide and mark the tour as cancelled.
- The system must store a local copy of each booking with a reference to the Clorian booking ID for traceability.
- The system must log each sync cycle with: timestamp, number of new/changed/cancelled bookings detected, and any errors.

### FR-02: Guide Profile Management

- The system must store each guide's name, email, and active status.
- The system must support associating one or more languages to a guide.
- The system must support associating one or more expertise areas (with name and category) to a guide.

### FR-03: Availability Pattern Management

- Each guide must have one availability pattern with a defined timezone.
- Each availability pattern must contain one or more availability slots defining recurring weekly availability (day of week, start time, end time).
- The system must support availability exceptions (date, type, reason) to override the recurring pattern.

### FR-04: Guide Suitability Validation

When assigning a guide to a tour, the system must validate **all three** rules below. A guide is eligible only if every rule passes (AND logic).

#### Rule 1: Availability

The guide must be available during the entire tour time window.

1. Retrieve the guide's `AvailabilityPattern` and find the `AvailabilitySlot` matching the tour's day of week.
2. Confirm the slot's `startTime ≤ tour.startTime` AND `endTime ≥ tour.endTime`.
3. Check `AvailabilityException` for the tour date — if a blocking exception exists, the guide is not available.
4. Confirm `guide.isActive == true`.
5. Confirm the guide has no other tour assigned during the same time window.

```
isAvailable =
    guide.isActive
    AND slot.dayOfWeek == tour.dayOfWeek
    AND slot.startTime <= tour.startTime
    AND slot.endTime >= tour.endTime
    AND NO blocking exception exists for tour.date
    AND NO overlapping tour assignment exists
```

#### Rule 2: Expertise

The guide must have expertise that matches the tour's required expertise.

1. Retrieve the guide's list of `Expertise` entries.
2. Check if at least one expertise matches the tour's required expertise by name or category.

```
hasExpertise =
    guide.expertises
        .ANY(e => e.name == tour.requiredExpertise
             OR e.category == tour.requiredCategory)
```

#### Rule 3: Language

The guide must speak the language requested for the tour.

1. Retrieve the guide's list of `Language` entries.
2. Check if at least one language matches the tour's requested language by code.

```
speaksLanguage =
    guide.languages
        .ANY(l => l.code == tour.requestedLanguageCode)
```

#### Final Eligibility

```
isSuitable = isAvailable AND hasExpertise AND speaksLanguage
```

### FR-05: Assignment Execution

- If exactly one guide is suitable, the system assigns that guide automatically.
- If multiple guides are suitable, the system should assign the guide with the fewest tours assigned that day (load balancing).
- If no guide is suitable, the system must flag the tour as "Unassigned" and notify the admin.

### FR-06: Manual Override

- An admin must be able to manually assign or reassign a guide to a tour, bypassing the automated suitability check.
- Manual overrides must be logged with the admin's identity and a timestamp.

---

## 6. Non-Functional Requirements

- **NFR-01**: The suitability check must execute within 2 seconds for up to 100 active guides.
- **NFR-02**: All assignment changes (automatic and manual) must be persisted in an audit log.
- **NFR-03**: The system must handle timezone conversions consistently using the guide's `AvailabilityPattern.timezone`.
- **NFR-04**: The Clorian sync job must complete within 60 seconds per cycle and must not skip a cycle if the previous one is still running (queue or skip with a warning log).
- **NFR-05**: The system must be resilient to Clorian API downtime — if a sync fails, it must retry on the next cycle and alert the admin after 3 consecutive failures.

---

## 7. Acceptance Criteria

| ID    | Scenario                                                          | Expected Result                                                    |
| ----- | ----------------------------------------------------------------- | ------------------------------------------------------------------ |
| AC-01 | New booking detected in Clorian sync                              | Tour is created locally and guide assignment is triggered          |
| AC-02 | Booking changed in Clorian (different time/language/expertise)    | Current assignment is reassessed; guide is reassigned if no longer suitable |
| AC-03 | Booking cancelled in Clorian                                      | Assigned guide is released, tour marked as cancelled               |
| AC-04 | Clorian API is unreachable                                        | Sync is retried next cycle; admin notified after 3 consecutive failures |
| AC-05 | Guide is available, has matching expertise, speaks requested language | Guide is assigned to the tour                                   |
| AC-06 | Guide has a blocking exception on the tour date                   | Guide is excluded from assignment                                  |
| AC-07 | Guide lacks the required expertise                                | Guide is excluded from assignment                                  |
| AC-08 | Guide does not speak the requested language                       | Guide is excluded from assignment                                  |
| AC-09 | No suitable guide exists                                          | Tour is flagged as "Unassigned" and admin is notified              |
| AC-10 | Multiple suitable guides exist                                    | Guide with fewest tours that day is assigned                       |
| AC-11 | Guide already has an overlapping tour                             | Guide is excluded from assignment                                  |
| AC-12 | Admin manually overrides assignment                               | Override is applied and logged                                     |

---

## 8. Dependencies

- **Clorian System**: Must expose an API or data export for booking retrieval (new, changed, cancelled).
- Guide profiles must be populated with languages and expertise before assignment can run.
- Availability patterns and slots must be configured per guide.
- Tour data (date, time, required expertise, requested language) is sourced from Clorian bookings.

---

## 9. Out of Scope

- Clorian booking interface and customer-facing booking flow.
- Visitor-facing booking and payment.
- Guide performance tracking and ratings.
- Notification delivery mechanism (email, push, SMS).
