# Functional Requirements Document: [Feature Name]

| Field            | Detail                  |
| ---------------- | ----------------------- |
| **FDR Number**   | FDR-XXX                 |
| **Author**       | [Author Name]           |
| **Date Created** | [Month Day, Year]       |
| **Version**      | 1.0                     |

---

## 1. Purpose

Describe the business need and the high-level goal of this feature. Explain
*why* this feature exists and what problem it solves within the Oceanarium Tour
Scheduling System.

> Example from FDR-001: "This document defines the functional requirements for
> the automated Guide Assignment feature within the Oceanarium Tour Scheduling
> System."

---

## 2. Scope

### In Scope

- List what this FDR covers (features, integrations, workflows).
- Be specific about boundaries.

### Out of Scope

- List what this FDR explicitly does NOT cover.
- This prevents scope creep and sets clear expectations.

---

## 3. Actors

Identify every person, system, or role that interacts with this feature.

- **[Actor Name]**: Description of their role and how they interact with the feature.
- **System**: What the system does automatically.
- **Admin**: What manual actions an admin can perform.

---

## 4. Assumptions

List all assumptions that must hold true for this feature to work as designed.

- Assumption 1
- Assumption 2
- Assumption 3

---

## 5. Functional Requirements

### FR-01: [Requirement Title]

- Describe the requirement in clear, testable terms.
- Use "must" for mandatory behaviour and "should" for preferred behaviour.
- Break complex logic into sub-bullets.

### FR-02: [Requirement Title]

- Requirement details.

### FR-XX: [Requirement Title]

For requirements with business logic or validation rules, include pseudocode:

```
isValid =
    condition_1
    AND condition_2
    AND NOT exception_condition
```

---

## 6. Non-Functional Requirements

- **NFR-01**: Performance requirement (e.g., "Must execute within X seconds for up to Y records").
- **NFR-02**: Auditability requirement (e.g., "All changes must be persisted in an audit log").
- **NFR-03**: Resilience requirement (e.g., "Must handle downstream API failures gracefully").
- **NFR-04**: Consistency requirement (e.g., "Must handle timezone conversions using a single source of truth").

---

## 7. Acceptance Criteria

| ID    | Scenario                            | Expected Result                         |
| ----- | ----------------------------------- | --------------------------------------- |
| AC-01 | [Describe the scenario]             | [Describe the expected outcome]         |
| AC-02 | [Describe the scenario]             | [Describe the expected outcome]         |
| AC-03 | [Describe the scenario]             | [Describe the expected outcome]         |
| AC-04 | [Error / edge case scenario]        | [Describe graceful handling]            |
| AC-05 | [Happy path scenario]               | [Describe success outcome]              |

> Tip: Each functional requirement should map to at least one acceptance
> criterion. Edge cases and error scenarios are just as important as happy paths.

---

## 8. Dependencies

List all systems, services, data sources, or preconditions that must be in place
for this feature to function.

- **[System/Service Name]**: What it must provide or expose.
- **[Data Dependency]**: What data must exist before the feature can operate.

---

## 9. Out of Scope

Reiterate items from Section 2 that are explicitly excluded to avoid ambiguity.

- Item 1
- Item 2
- Item 3

---

## Appendix (Optional)

### A. Data Model

If the feature introduces new entities, describe them here or reference an ER
diagram.

### B. Flowchart

If the feature has complex workflow logic, include or reference a flowchart
diagram.

### C. Revision History

| Version | Date            | Author          | Changes              |
| ------- | --------------- | --------------- | -------------------- |
| 1.0     | [Month Day, Year] | [Author Name] | Initial draft        |
| 1.1     | [Month Day, Year] | [Author Name] | [Summary of changes] |
