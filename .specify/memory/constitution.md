# Builders Constitution

Stack: Python backend + TypeScript frontend (FSD architecture).

## Core Principles

### I. KISS & YAGNI — Simplicity First
- Implement the simplest solution that satisfies the current requirement. No speculative
  abstractions, config options, or generalization "for the future".
- New abstractions (base classes, interfaces, generics, factories) are introduced only when
  there are at least two real consumers, or a spec explicitly requires the extension point.
- Prefer flat, readable code over clever code. If a junior can't follow it, rewrite it.
- Dead code, commented-out blocks, and unused dependencies are deleted, not kept "just in case".

### II. DRY — Single Source of Truth
- Business rules, constants, validation schemas, and type contracts are defined once.
  Backend ↔ frontend contracts live in a single schema source (OpenAPI / generated types).
- Duplication is removed on the third occurrence (rule of three); do not prematurely
  abstract on the second.
- Copy-paste between modules/slices is a review blocker unless justified in the PR description.

### III. OOP & SOLID
- **S**: A class/module has one reason to change. Services do not mix transport, business
  logic, and persistence.
- **O**: Extend behavior via composition and new implementations, not by editing stable code
  with `if`-branches per client.
- **L**: Subtypes must be substitutable; no overrides that throw `NotImplementedError` or
  weaken contracts.
- **I**: Small, focused interfaces (Python `Protocol` / TS `interface`). No "god" interfaces.
- **D**: High-level logic depends on abstractions. External systems (DB, HTTP, queues, FS)
  are accessed through injected adapters; construction is wired at the composition root.
- Prefer composition over inheritance. Inheritance depth > 2 requires justification.

### IV. Clean Code
- Intention-revealing names; no abbreviations except industry-standard (id, url, db).
- Functions do one thing at one level of abstraction; max 4 parameters (use objects/dataclasses beyond that).
- No magic numbers/strings — named constants or enums.
- Comments explain *why*, never *what*. Self-documenting code first.
- Errors are handled at meaningful boundaries; no silent `except`/`catch`, no swallowed errors.
  Errors are typed/structured, logs are structured and never contain secrets.
- Python: PEP 8, full type hints on public APIs, `ruff` + `mypy` clean.
- TypeScript: `strict: true`, no `any` (use `unknown` + narrowing), ESLint clean.

### V. Size Guard (enforced)
| Unit | Soft limit | Hard limit |
|---|---|---|
| File / module | 400 lines | 500 lines |
| Function / method | 60 lines | 80 lines |
| Class | 300 lines | 400 lines |
| React component | 200 lines | 250 lines |
| Cyclomatic complexity | 10 | 15 |
| Nesting depth | 3 | 4 |

- Crossing a soft limit means "plan a split"; crossing a hard limit blocks merge — split the
  unit before merging (extract module, hook, service, or sub-component).
- Limits are enforced by linters where possible (ruff/pylint `max-*`, eslint `max-lines`,
  `max-lines-per-function`, `complexity`, `max-depth`) and checked in CI.
- Generated code, migrations, and lock files are exempt.

### VI. FSD — Feature-Sliced Design (frontend)
- Layers: `app → pages → widgets → features → entities → shared`.
- Imports point strictly downward; a layer never imports from a layer above it, slices on the
  same layer do not import each other directly (use the layer below or `shared`).
- Every slice exposes a public API via its `index.ts`; deep imports into slice internals are
  forbidden (enforced via eslint `boundaries`/`import` rules).
- Business logic lives in `entities`/`features`; `shared` contains only stack-agnostic
  utilities and UI kit — no business knowledge.
- Backend mirrors the spirit: layered structure (api/routers → services → domain → infrastructure),
  domain layer has zero framework imports.

### VII. TDD — Pragmatic Test-First
- Business logic, domain rules, services, and utilities: test-first (red → green → refactor).
  A bug fix starts with a failing test reproducing the bug.
- UI components and glue code: tests may follow implementation, but must exist before merge
  for anything with conditional logic.
- Test pyramid: many unit tests, focused integration tests at boundaries (API contracts, DB,
  inter-service), few e2e for critical flows.
- Tests are deterministic and isolated: no real network, real time, or shared mutable state;
  external systems are faked/stubbed at the adapter boundary.
- Coverage gate: changed business-logic code ≥ 80% line coverage. Coverage is a floor, not a target.

## Additional Constraints

- **Security**: secrets only via environment/secret manager, never in code or logs; validate
  all external input at the boundary (Pydantic / zod); parameterized queries only.
- **Dependencies**: adding a dependency requires justification in the PR; prefer stdlib and
  existing deps; pin versions; no packages published < 7 days ago.
- **API contracts**: breaking changes to public API require versioning and a migration note.
- **Commits**: small, atomic, imperative mood; a commit must leave the build green.

## Development Workflow & Quality Gates

Every PR must pass, in order:
1. Formatters/linters clean (ruff, mypy, eslint, tsc, prettier) — includes size-guard rules.
2. All tests green; new/changed business logic covered per Principle VII.
3. Review checklist: SOLID violations, duplication, size limits, FSD boundary breaches,
   naming, error handling. Any violation is a blocker unless explicitly waived with a
   written justification in the PR.
4. No TODOs without a linked issue.

## Governance

- This constitution supersedes ad-hoc practices. Specs, plans, and tasks produced by the
  spec-kit workflow must comply with it; `/speckit-plan` and `/speckit-analyze` check against it.
- Complexity that violates a principle must be justified in the plan's Complexity Tracking
  section — "we might need it later" is never a valid justification (YAGNI).
- Amendments: PR to this file with rationale, version bump per semver
  (breaking principle change = MAJOR, new principle/section = MINOR, wording = PATCH).

**Version**: 1.0.0 | **Ratified**: 2026-08-08 | **Last Amended**: 2026-08-08
