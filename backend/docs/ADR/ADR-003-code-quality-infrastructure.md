# [ADR-003] Adopt Code Quality Infrastructure — Lint, Unit Tests, Load Tests, Pre-push & CI
| Field            | Value                  |
|------------------|------------------------|
| **ID**           | ADR-003                |
| **Version**      | 1.0                    |
| **Status**       | Proposed               |
| **Author**       | Evandro Maciel         |
| **Created**      | 2026-03-10             |
| **Last Updated** | 2026-03-10             |
---
## Context
The Oceanarium project currently has no automated quality gates:
- **No linting**: the frontend has Prettier for formatting but no static analysis (ESLint). The backend has no linting or formatting tool configured.
- **No tests**: neither frontend (Vue 3) nor backend (FastAPI) have any test framework, test files, or coverage tooling.
- **No load tests**: no performance baseline or regression detection.
- **No git hooks**: nothing prevents pushing broken code. Quality is entirely manual.
- **CI is limited**: the only CI workflow validates Alembic migrations. No lint, test, or coverage checks run on PRs.
As the codebase grows across 8 bounded contexts with 20+ tables, the absence of automated quality enforcement will compound: regressions will slip through, code style will diverge, and performance issues will surface only in production.
## Decision
**Adopt a comprehensive code quality stack covering linting, unit testing, load testing, git hooks, and CI — enforced both locally (pre-push) and remotely (GitHub Actions).**
### Tooling Choices
| Concern | Frontend (Vue 3) | Backend (FastAPI) |
|---------|-------------------|-------------------|
| **Linting** | ESLint 9 (flat config) + eslint-plugin-vue + eslint-config-prettier | Ruff (linting + formatting) |
| **Formatting** | Prettier (existing) | Ruff format |
| **Unit Tests** | Vitest + @vue/test-utils + jsdom | pytest + pytest-asyncio + httpx |
| **Coverage** | @vitest/coverage-v8 (80% threshold) | pytest-cov (80% threshold) |
| **Load Tests** | — | Locust (headless mode) |
| **Git Hooks** | Husky (root package.json, pre-push) | Same hook calls backend tools |
| **CI** | GitHub Actions (lint + test + coverage) | GitHub Actions (lint + test + coverage + load test) |
### Enforcement Points
Developer pushes code │ ▼ ┌─────────────────────┐ │ Pre-push Hook │ ← Husky: lint + unit tests (frontend & backend) │ (local, blocking) │ └────────┬────────────┘ │ push succeeds ▼ ┌─────────────────────┐ │ GitHub Actions CI │ ← PR: lint + test + coverage + load test + migration validation │ (remote, blocking) │ └────────┬────────────┘ │ all checks pass ▼ PR mergeable

### Coverage Strategy
- **Minimum threshold**: 80% for lines, branches, functions, and statements
- **Initial focus**: stores, utils, and services (pure logic, high ROI)
- **Progressive expansion**: components and routes as the test culture matures
- Coverage is enforced in both CI (fail the build) and locally (pre-push runs tests)
### Load Test Strategy
- **Tool**: Locust in headless mode
- **CI thresholds**: fail ratio < 1%, average response time < 500ms
- **CI parameters**: 50 users, ramp-up 10/s, duration 30s (lightweight, validates no severe regressions)
- **Local use**: developers can run with higher load for profiling (`-u 100 -r 10 -t 60s`)
- **Scope**: public read endpoints (health, schedule, guides, tours) — write endpoints added as auth test fixtures mature
## Options Considered
### Linting — Frontend
#### Option A: ESLint 9 flat config + Prettier (chosen)
- **Pros**: Industry standard for Vue, flat config is simpler than legacy `.eslintrc`, Prettier handles formatting separately with existing config
- **Cons**: Two tools for frontend (ESLint for logic, Prettier for formatting)
#### Option B: Biome (lint + format in one tool)
- **Pros**: Single tool, extremely fast, no Prettier needed
- **Cons**: Vue SFC support is still limited, smaller ecosystem, would require removing the existing Prettier setup
### Linting — Backend
#### Option A: Ruff (chosen)
- **Pros**: Replaces flake8 + black + isort in a single tool, 10-100x faster, covers linting and formatting, actively maintained, Python-native config in `pyproject.toml`
- **Cons**: Newer tool, some niche flake8 plugins not yet ported
#### Option B: flake8 + black + isort (traditional)
- **Pros**: Battle-tested, every plugin available
- **Cons**: Three tools to configure and maintain, significantly slower, three config files
### Unit Testing — Frontend
#### Option A: Vitest (chosen)
- **Pros**: Native Vite integration (shares config, instant HMR), ESM-first, Jest-compatible API, built-in coverage via v8, fastest test runner for Vite projects
- **Cons**: Smaller ecosystem than Jest (but growing fast)
#### Option B: Jest
- **Pros**: Largest ecosystem, most documentation
- **Cons**: Requires additional configuration for ESM/Vite, slower transforms, separate toolchain from Vite
### Unit Testing — Backend
#### Option A: pytest (chosen)
- **Pros**: De facto Python testing standard, rich plugin ecosystem (asyncio, cov, fixtures), excellent FastAPI integration via httpx, fixture-based setup is clean
- **Cons**: None significant
#### Option B: unittest (stdlib)
- **Pros**: No dependency needed
- **Cons**: Verbose class-based syntax, no fixture system, no plugin ecosystem, poor async support
### Load Testing
#### Option A: Locust (chosen)
- **Pros**: Python-native (same language as backend), scriptable test scenarios, headless mode with CI-friendly exit codes (`--check-fail-ratio`, `--check-avg-response-time`), web UI for local profiling
- **Cons**: Single-process by default (sufficient for CI smoke tests)
#### Option B: k6 (Grafana)
- **Pros**: Go-based (very fast), JavaScript test scripts, excellent CI support
- **Cons**: Different language from backend, requires separate binary install in CI, steeper learning curve
### Git Hooks
#### Option A: Husky (chosen)
- **Pros**: Most widely used Node.js hook manager, simple setup (`npx husky init`), supports any hook type, zero config after init
- **Cons**: Requires Node.js (available — frontend is Node-based)
#### Option B: pre-commit (Python framework)
- **Pros**: Language-agnostic, rich hook registry
- **Cons**: Adds another tool/config, YAML-based config is verbose, Python-specific hooks would duplicate Ruff config
#### Option C: lefthook
- **Pros**: Fast (Go binary), parallel hook execution
- **Cons**: Less ecosystem adoption, separate binary to install
## Consequences
### Positive
- Every push is validated locally (lint + tests) — broken code never reaches the remote
- Every PR is validated in CI (lint + tests + coverage + load + migrations) — broken code never reaches `main`
- Consistent code style is enforced automatically (ESLint + Prettier + Ruff) — no style debates in reviews
- Performance regressions are caught early via load tests in CI
- Coverage thresholds prevent test quality from degrading over time
- All tools are standard for their ecosystems — low learning curve for new contributors
### Negative
- Pre-push hook adds ~30-60s to each push (lint + test run)
- Initial effort to write the first batch of tests and fix all lint violations
- Load tests in CI add ~45s to the pipeline (lightweight by design)
- Root `package.json` added for Husky — minor structural change
### Risks
- **False sense of security from 80% coverage**: coverage measures code exercised, not correctness — must be paired with meaningful assertions
- **Load test flakiness in CI**: shared CI runners may have variable performance — thresholds are set conservatively (500ms avg) to account for this
- **Pre-push hook bypass**: developers can skip with `--no-verify` — CI is the final safety net
## Related
- [ADR-002] Layered Domain Architecture — defines the `services/`, `routes/` structure that tests will mirror
- [DDD-001] Domain Model Overview — defines bounded contexts that guide test organization
- [DB-001] Initial Schema Migration — the migration CI job that this ADR extends
## Changelog
| Version | Date       | Author          | Description |
|---------|------------|-----------------|-------------|
| 1.0     | 2026-03-10 | Evandro Maciel  | Initial proposal — lint, unit tests, load tests, pre-push hook, and CI pipeline |
