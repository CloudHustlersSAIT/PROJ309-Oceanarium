# [ADR-004] Technology Alternatives Analysis

| Field            | Value                  |
|------------------|------------------------|
| **ID**           | ADR-004                |
| **Version**      | 1.0                    |
| **Status**       | Informational          |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-12             |
| **Last Updated** | 2026-03-12             |

---

## Purpose

This document provides a comprehensive analysis of **technology alternatives considered** for each major component in the Oceanarium tech stack. It serves as a reference for understanding why specific technologies were chosen and what trade-offs were made.

Each section follows the pattern:
- **Chosen Technology** (what we use)
- **Alternatives Considered** (what we evaluated)
- **Decision Rationale** (why we chose what we did)
- **Trade-offs** (what we gained and what we gave up)

## 1. Frontend Framework

### Chosen: **Vue 3** (v3.5.22)

### Alternatives Considered

#### Option A: React (v18+)
**Pros:**
- Largest ecosystem and community
- Most job market demand
- Extensive third-party libraries (React Query, Zustand, etc.)
- Excellent TypeScript support
- Meta (Facebook) backing

**Cons:**
- Larger bundle size (~45KB minified)
- Hooks can be confusing (dependency arrays, closure issues)
- No official state management (ecosystem fragmentation: Redux, MobX, Zustand, Jotai)
- No official router (React Router is de facto but third-party)
- More boilerplate for forms and two-way binding

**Why Not Chosen:**
Vue's composition API is cleaner than React hooks for this team's experience level. Official router and state management reduce decision fatigue.

---

#### Option B: Angular (v17+)
**Pros:**
- Complete framework (batteries-included: router, HTTP, forms, RxJS)
- Strong typing with TypeScript (mandatory)
- Best for large enterprise teams with strict standards
- Google backing

**Cons:**
- Steepest learning curve (RxJS, decorators, dependency injection)
- Heaviest bundle size (~150KB+ base framework)
- Verbose syntax (decorators, modules, services)
- Overkill for a 4-person team and 6-month capstone project
- Slower iteration speed

**Why Not Chosen:**
Too heavyweight for the project scope. The team has no prior Angular experience, and the learning curve would delay feature velocity.

---

#### Option C: Svelte (v4+)
**Pros:**
- Smallest bundle size (~10KB base)
- No virtual DOM (compiles to vanilla JS)
- Simplest syntax (less boilerplate)
- Fastest performance in benchmarks

**Cons:**
- Smallest ecosystem (fewer libraries, less community support)
- Fewer jobs/demand (risky for student resumes)
- Less mature DevTools
- Smaller talent pool if team needs to expand
- Newer technology (less Stack Overflow answers)

**Why Not Chosen:**
While technically superior in performance, Vue 3 offers a better balance of simplicity and ecosystem maturity. The team wanted a framework with proven enterprise adoption.

---

#### Option D: Vue 3 (Chosen)
**Pros:**
- **Composition API** — cleaner than React hooks, more powerful than Options API
- **Official ecosystem** — Vue Router, Pinia (state), Vite (build)
- **Smaller bundle** (~35KB) than React, larger than Svelte
- **Two-way binding** with `v-model` (simpler forms than React)
- **Excellent DevTools** — time-travel debugging, component inspector
- **Gentle learning curve** — easier than Angular, comparable to React
- **Growing adoption** — Laravel, Nuxt, Element Plus

**Cons:**
- Smaller community than React (but still top 3 frameworks)
- Fewer third-party libraries than React
- Less job market demand than React (but growing)

**Why Chosen:**
Best balance of **developer experience**, **performance**, and **ecosystem maturity** for a team with mixed experience levels. Vite integration is seamless.

---

## 2. Backend Framework

### Chosen: **FastAPI** (v0.128.8)

### Alternatives Considered

#### Option A: Flask (v3+)
**Pros:**
- Minimalist, micro-framework (unopinionated)
- Huge ecosystem of extensions
- Most popular Python web framework
- Simple to learn

**Cons:**
- **Synchronous by default** (no async support without extensions)
- No built-in validation (need Flask-Pydantic or Marshmallow)
- No automatic API documentation (need Flasgger or manual Swagger)
- Manual dependency injection
- Slower than async frameworks for I/O-bound tasks

**Why Not Chosen:**
FastAPI's async-first design and automatic OpenAPI docs provide better developer experience for an API-centric project.

---

#### Option B: Django + Django REST Framework (v5+)
**Pros:**
- Batteries-included (ORM, admin panel, auth, migrations out of the box)
- Largest ecosystem
- Best for rapid prototyping with forms/CRUD
- Excellent admin interface
- Strong security defaults

**Cons:**
- **Overkill for API-only** (includes templating, forms, sessions we don't need)
- Synchronous ORM (async support is experimental)
- Heavier than FastAPI/Flask (~150KB vs ~30KB)
- Opinionated structure (less flexible)
- Django REST Framework adds complexity for serializers

**Why Not Chosen:**
We don't need Django's admin panel, templating, or form system. FastAPI is lighter and faster for pure API development.

---

#### Option C: Quart (async Flask)
**Pros:**
- Flask-compatible API but fully async
- Drop-in replacement for Flask apps
- Supports WebSockets natively

**Cons:**
- Smaller community than Flask/FastAPI
- Fewer extensions
- Less mature ecosystem
- No automatic OpenAPI docs

**Why Not Chosen:**
FastAPI has better validation (Pydantic) and automatic documentation generation, which are critical for frontend-backend contract clarity.

---

#### Option D: FastAPI (Chosen)
**Pros:**
- **Async-first** — non-blocking I/O for database and external APIs
- **Automatic OpenAPI docs** — Swagger UI and ReDoc at `/docs` and `/redoc`
- **Pydantic validation** — type-safe request/response models with automatic error messages
- **Dependency injection** — clean way to inject DB sessions, auth, etc.
- **Fast performance** — benchmarks near Node.js/Go speeds
- **Type hints** — leverages Python 3.11 type system for IDE support

**Cons:**
- Newer than Flask/Django (less Stack Overflow history)
- Smaller plugin ecosystem than Flask
- Async code can be harder to debug

**Why Chosen:**
**Best performance**, **automatic documentation**, and **type safety** align perfectly with the project's needs. The team wanted modern Python 3.11 features.

---

## 3. Database

### Chosen: **PostgreSQL 16**

### Alternatives Considered

#### Option A: MySQL (v8+)
**Pros:**
- Popular, widely supported
- Good performance for simple queries
- Easier to learn

**Cons:**
- **No JSONB** (JSON support is weaker)
- Weaker full-text search than PostgreSQL
- Less robust constraint enforcement
- No advanced features (CTEs, window functions) until v8

**Why Not Chosen:**
JSONB support is critical for `poll_staging` table (storing raw Clorian payloads). PostgreSQL's timezone handling is also superior for scheduling.

---

#### Option B: MongoDB (NoSQL)
**Pros:**
- Schema-less (flexible documents)
- Horizontal scaling (sharding)
- Good for unstructured data

**Cons:**
- **No foreign keys** — relationships must be managed in application code
- **No ACID transactions across collections** (until v4.0, still limited)
- **No SQL** — team would need to learn aggregation pipelines
- Overkill for structured, relational data (customers, reservations, schedules)

**Why Not Chosen:**
Reservations, schedules, and guides are inherently relational. PostgreSQL's foreign keys and constraints enforce data integrity at the database level.

---

#### Option C: SQLite (embedded)
**Pros:**
- Zero configuration (file-based)
- Perfect for local development
- Serverless

**Cons:**
- **Single-writer** — no concurrent writes (fatal for multi-user app)
- No user management (no roles/permissions)
- Limited data types (no native JSONB, weak date/time)
- Not suitable for production

**Why Not Chosen:**
Multi-user production environment requires concurrent writes. SQLite is development-only for single-user scenarios.

---

#### Option D: PostgreSQL 16 (Chosen)
**Pros:**
- **JSONB support** — efficient storage and indexing for `poll_staging` payloads
- **Timezone-aware timestamps** — critical for event scheduling
- **Robust constraints** — foreign keys, check constraints, unique constraints
- **Advanced features** — CTEs, window functions, full-text search
- **Production-ready** — ACID guarantees, replication, connection pooling
- **Open source** — no licensing costs

**Cons:**
- Slightly more complex than MySQL to configure
- Vertical scaling limits (horizontal sharding is harder than MongoDB)

**Why Chosen:**
**JSONB, timezone support, and constraints** are must-haves for this domain. PostgreSQL is the most feature-rich open-source RDBMS.

---

## 4. Backend Linter

### Chosen: **Ruff** (≥0.11)

### Alternatives Considered

#### Option A: flake8 + black + isort (traditional stack)
**Pros:**
- Battle-tested
- Every plugin available
- Separate concerns (lint, format, imports)

**Cons:**
- **Three tools** — separate configs, separate commands
- **Slow** — Python-based, 10-100x slower than Ruff
- **Three config files** — `.flake8`, `pyproject.toml`, `.isort.cfg`

**Why Not Chosen:**
Ruff replaces all three tools with a single, 100x faster tool.

---

#### Option B: Pylint
**Pros:**
- Most comprehensive linter
- Detailed error messages

**Cons:**
- **Slowest** — takes minutes on large codebases
- **Opinionated** — many false positives
- **Complex config** — hundreds of rules

**Why Not Chosen:**
Too slow and too opinionated for fast iteration.

---

#### Option C: Ruff (Chosen)
**Pros:**
- **10-100x faster** — Rust-based
- **Replaces flake8 + black + isort** — one tool for lint + format + imports
- **Single config** — `pyproject.toml` only
- **Drop-in replacement** — implements flake8 rules
- **Auto-fix** — `ruff check --fix`

**Cons:**
- Newer tool (some niche flake8 plugins not ported yet)
- Smaller community than flake8/black

**Why Chosen:**
**Speed and simplicity**. One tool, one config, sub-second linting on entire codebase.

---

## 5. Frontend Testing

### Chosen: **Vitest** (v4.0.18)

### Alternatives Considered

#### Option A: Jest
**Pros:**
- Most popular JS test framework
- Largest ecosystem
- Most tutorials/docs

**Cons:**
- **Slow with ESM** — requires transforms (Babel/SWC)
- **Separate config** — doesn't share Vite config
- **No Vite integration** — misses HMR benefits

**Why Not Chosen:**
Vitest is Jest-compatible API but 10x faster with Vite integration.

---

#### Option B: Cypress Component Testing
**Pros:**
- Real browser testing
- Great for integration tests

**Cons:**
- **Slow** — spins up real browser
- **Heavier** — 200MB+ install
- Overkill for unit tests

**Why Not Chosen:**
Vitest is faster for unit tests. Cypress is better for E2E.

---

#### Option C: Vitest (Chosen)
**Pros:**
- **Vite-native** — shares config, instant HMR
- **Jest-compatible API** — easy to learn
- **Fast** — ESM-first, no transforms
- **Built-in coverage** — c8/v8 provider
- **Watch mode** — instant re-runs

**Cons:**
- Newer than Jest (smaller community)
- Some Jest plugins not ported yet

**Why Chosen:**
**10x faster than Jest** for Vite projects. Native ESM support means no Babel/SWC transforms.

---

## 6. Backend Testing

### Chosen: **pytest** (≥8)

### Alternatives Considered

#### Option A: unittest (stdlib)
**Pros:**
- Built-in (no dependency)
- Simple for basic tests

**Cons:**
- **Verbose** — class-based, `self.assertEqual()`
- **No fixtures** — manual setup/teardown
- **Poor async support**

**Why Not Chosen:**
pytest is the Python standard for modern testing.

---

#### Option B: nose2
**Pros:**
- Extension of unittest
- Plugin system

**Cons:**
- **Abandoned** — last release 2019
- Less popular than pytest

**Why Not Chosen:**
pytest is the de facto standard with active development.

---

#### Option C: pytest (Chosen)
**Pros:**
- **Industry standard** for Python testing
- **Fixture-based** — clean setup/teardown
- **Plugin ecosystem** — pytest-asyncio, pytest-cov, httpx
- **Excellent FastAPI integration** — TestClient
- **Powerful assertions** — detailed failure messages

**Cons:**
- None significant

**Why Chosen:**
**Standard tool** for Python testing. Best FastAPI integration with httpx TestClient.

---

## Summary Comparison Table

| Category | Chosen | Runner-Up | Why Chosen Won |
|----------|--------|-----------|----------------|
| **Frontend Framework** | Vue 3 | React | Cleaner API, official ecosystem, smaller bundle |
| **Backend Framework** | FastAPI | Flask | Async-first, auto docs, Pydantic validation |
| **Database** | PostgreSQL 16 | MySQL | JSONB, timezone support, advanced features |
| **Backend Linter** | Ruff | flake8+black | 100x faster, one tool replaces three |
| **Frontend Tests** | Vitest | Jest | Vite-native, faster, ESM-first |
| **Backend Tests** | pytest | unittest | Fixtures, plugins, FastAPI integration |

---

## Key Decision Principles

Across all technology choices, the team prioritized:

1. **Modern tooling** — Latest stable versions (Vue 3, FastAPI, PostgreSQL 16, Python 3.11)
2. **Developer experience** — Fast builds (Vite), auto-docs (FastAPI), type safety (Pydantic)
3. **Performance** — Async frameworks, small bundles, fast linters
4. **Ecosystem maturity** — Official tools (Pinia, Alembic) over third-party when available
5. **Team skill level** — Balanced learning curve (Vue easier than Angular, FastAPI easier than Django)
6. **Project constraints** — 6-month timeline, 4-person team, student budget

---

## Related Documents

- [ADR-001](ADR-001-drop-reservation-table.md) — Naming & Structure
- [ADR-002](ADR-002-layered-domain-architecture.md) — Layered Domain Architecture
- [ADR-003](ADR-003-code-quality-infrastructure.md) — Code Quality Infrastructure
- [DDD-001](../DDD/DDD-001-domain-model-overview.md) — Domain Model Overview
- [ARCHITECTURE-TECH-STACK](../ARCHITECTURE-TECH-STACK.md) — Complete architecture overview

---

## Changelog

| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-12 | Evandro Maciel  | Initial technology alternatives analysis covering 6 major stack decisions |
