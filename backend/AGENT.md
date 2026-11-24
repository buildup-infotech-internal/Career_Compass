# Career Compass Backend — Agent Context

Read this file first for future backend tasks. Treat `API_CONTRACT.md` and `SCHEMA.md` at the repository root as the design references, and inspect implementation files only when needed. Do not silently resolve documented schema/API conflicts; discuss potentially breaking choices first. After each implementation phase, update this file with verified changes, files/endpoints, tests, decisions, remaining issues, and next phase.

## Project and stack

Career Compass is a career guidance and job-search platform. The Next.js App Router frontend consumes this FastAPI backend at `/api/v1`.

- Python 3.12; FastAPI; SQLAlchemy 2.x; Alembic; PostgreSQL on Supabase.
- Pydantic / pydantic-settings for validation and settings. Profile request/response schemas are implemented; schemas for other feature APIs remain pending.
- Synchronous SQLAlchemy sessions via `Session` and `sessionmaker`.
- Supabase Auth is the identity provider and the Next.js browser SDK handles auth flows. Gemini is the primary AI provider and Groq the fallback; neither AI integration is implemented yet.
- Use `uv` for environment and dependencies (`pyproject.toml`, `uv.lock`); add runtime/dev dependencies there rather than managing packages ad hoc. Current project requirement is `requires-python >=3.12`; the SQLAlchemy range in `pyproject.toml` is `>=2.1.9`.
- Frontend: Next.js App Router, React, TypeScript, Tailwind, ESLint, npm; Supabase Auth uses `@supabase/supabase-js`. Frontend test tooling is Vitest + Testing Library.

## Backend layout

- `app/main.py`: FastAPI app factory, lifespan, CORS, exception handlers, root/health routes, Swagger/OpenAPI setup.
- `app/api/v1/router.py`: versioned router aggregator; endpoint routers live in `app/api/v1/endpoints/`.
- `app/core/config.py`: centralized Pydantic settings loaded from the backend `.env` file.
- `app/core/responses.py`: common success envelope helper.
- `app/core/security.py`, `dependencies.py`: Supabase JWT verification and authenticated-user dependency.
- `app/api/v1/endpoints/auth.py`: diagnostic `/auth-check` and `/auth/me`.
- `app/db/base.py`, `mixins.py`, `session.py`: declarative base, timestamp mixin, sync engine/session dependency and disposal.
- `app/models/`: SQLAlchemy models, imported through `app/models/__init__.py` for Alembic metadata.
- `app/schemas/profiles.py`: profile create/update and response models, including flexible education/experience entries.
- `app/services/profiles.py`: profile retrieval, upsert, and deletion scoped to the verified user ID.
- `app/utils/`: no feature implementation yet.
- `frontend/app/`: Next.js login, signup, dashboard, and password recovery routes; `frontend/components/auth/` contains auth/session UI and provider; `frontend/lib/` contains Supabase client and authenticated API client.
- `frontend/.env.example`: public Supabase URL/key and API origin placeholders; frontend ignores real `.env*` files.
- `frontend/*test*`, `frontend/**/*.test.*`: Vitest and Testing Library tests for SDK config, auth forms, and API/profile initialization.
- `alembic/env.py`, `alembic/versions/`: migration setup and initial schema revision.
- `tests/test_foundation.py`: API foundation, CORS, Swagger, error-envelope, and DB-session tests.
- `tests/supabase_auth_test.py`: opt-in manual Supabase login/backend integration check; guarded by a main entry point so pytest collection does not prompt.

## Database and ORM conventions

Use SQLAlchemy 2-style typed declarative mappings, UUID application primary keys, PostgreSQL JSONB where defined, timezone-aware timestamps, foreign keys with explicit delete behavior, and Alembic for schema changes. `TimestampMixin` adds `created_at` / `updated_at`. Preserve uniqueness/check constraints in models and migrations.

Supabase `auth.users` is externally managed. `app/db/base.py` declares only a metadata table reference for the profile FK; do not create, alter, or drop `auth.users` with Alembic. `alembic/env.py` excludes tables in the `auth` schema during autogeneration. The initial migration creates application tables and an FK to `auth.users.id` only.

### Existing application tables

The model/migration set contains 18 application tables:

- Identity/career: `profiles` (FK to external `auth.users`), `career_roles`, `learner_interests`.
- Skills/assessment: `skills`, `learner_skills`, `assessment_questions`, `assessments`, `assessment_answers`.
- Jobs: `jobs`, `job_skills`, `job_matches`, `job_ingestion_logs`.
- Learning: `learning_resources`, `learning_plans`, `learning_steps`.
- Assistant/feedback: `chat_sessions`, `chat_messages`, `feedback`.

Foreign-key relationships follow the names: profiles own interests, skills, assessments, matches, plans, chat sessions, and feedback; career roles connect to interests, questions, assessments, and plans; skills connect to learner skills, questions, job skills, resources, and learning steps; assessments contain answers; jobs connect to job skills and matches; learning plans contain steps; chat sessions contain messages. Explicit ORM `relationship()` properties are only present for some of these pairs, so inspect models before relying on relationship navigation.

## API conventions and security

Follow `API_CONTRACT.md`: `/api/v1` prefix; Supabase login/registration on the frontend; send `Authorization: Bearer <access_token>`; backend must verify JWT and authorize learner-owned records. Use the documented success/error envelopes, `?page=1&limit=20` pagination shape, and route/request/response behavior. Never let a user edit `account_role`; never expose assessment answer keys; score assessments deterministically in Python. Resume uploads are PDF/DOCX, max 1 MB, processed transiently and never persisted. Job match numerical scores are deterministic; AI may provide explanations only. Use verified catalogue links for learning resources.

Supabase JWT verification is implemented with PyJWT/JWKS (ES256, authenticated audience, issuer and required claims); profile endpoints reuse `get_current_user` and scope every query to its UUID. `/auth/me` returns the verified user ID and nullable application profile. Other feature API ownership rules and RLS policies are not implemented. Root, health, auth-check, auth-me, and profile endpoints use the common success envelope; HTTP, request-validation, and unexpected errors are normalized to the contract error envelope. Swagger UI is at `/docs`, OpenAPI JSON at `/openapi.json`.

Frontend authentication uses the browser Supabase SDK only: SDK-managed persistent session, callback detection and auto-refresh; signup/login, confirmation-required signup messaging, logout, recovery email and password update; protected dashboard; and API bearer-token forwarding. After a valid session, the provider checks `/profiles/me` and initializes a missing profile via authenticated `PUT /profiles/me`. Backend never stores passwords or issues tokens.

## Settings / environment names

Names declared by `backend/app/core/config.py` and backend `.env.example` (never put values or secrets here): `APP_NAME`, `API_V1_PREFIX`, `API_BASE_URL`, `DEBUG`, `DATABASE_URL`, `CORS_ORIGINS`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`. Frontend `.env.example` names: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_BASE_URL`. The frontend anon/publishable key is public by design; never use service-role keys or secrets in `NEXT_PUBLIC_*`. `CORS_ORIGINS` is a comma-separated allowlist, blank by default; configure it for the frontend origin. `.env` is resolved relative to the backend source. Real env files are ignored and must not be committed.

## Verified implementation and phase

Implemented: Pydantic settings; synchronous SQLAlchemy session dependency with deterministic session close and cached-engine disposal on app shutdown; all 18 planned ORM models; initial Alembic revision `38de988c81b0_create_initial_database_schema.py`; FastAPI app initialization, configurable CORS, common response/error envelopes, split v1 endpoint routers, health/auth-check endpoints, Swagger/OpenAPI, and profile APIs. The initial migration is reported as applied to Supabase; application connectivity was verified with a read-only `SELECT 1` during Phase 1.

Current phase: **Profile APIs and authentication client integration complete; domain feature APIs remain pending.** Routes: `GET /api/v1/auth/me`, temporary `GET /api/v1/auth-check`, and protected profile GET/PUT/DELETE. Auth-me and profile routes use the verified subject. Profile GET returns 404 if absent; PUT initializes or updates only the caller's profile, rejects ID/role input, and preserves existing role; DELETE removes only application profile data and does not delete `auth.users`. Frontend signup/login/session/refresh/logout/recovery/profile initialization are implemented in Next.js. In-process profile initialization requests are deduplicated per user. No DB schema or migration changes were made. Root `API_CONTRACT.md` documents auth-me and application-only profile deletion.

Latest validation: backend `uv run pytest` = **27 passed**; Ruff passes on the new JWT tests and changed auth route. Frontend `npm run test` = **10 passed**, `npm run lint`, `npm run typecheck`, and `npm run build` all pass. Browser smoke test loaded `/login` and `/signup`. Tests use generated local P-256 keys/mocked JWKS and mocked Supabase/API calls; no live auth credentials or token values are committed. Existing backend full-project Ruff baseline still has 15 findings outside the touched auth tests/route and TestClient emits one httpx deprecation warning. Vitest emits a non-fatal Vite config-loader warning.

## Pending implementation phases

1. Configure frontend `NEXT_PUBLIC_*` environment values, Supabase allowed redirect URLs, and backend `CORS_ORIGINS` in each deployment; validate with a non-production account.
2. Reconcile remaining API/schema/model/migration differences before adding endpoints for those domains; preserve existing deployed schema unless changes are approved.
3. Implement career-role, interest, and skill APIs with tests, reusing the existing profile auth/service/session patterns.
4. Implement transient resume extraction (Gemini primary, Groq fallback) and Pydantic output validation.
5. Implement assessment APIs/scoring and tests, protecting answer keys and ownership.
6. Implement job listing/filters, scheduled ingestion, deterministic matching, and tests.
7. Implement learning resources/plans, chat, and feedback APIs, with ownership/deletion behavior and tests.
8. Complete security/RLS, integration, and migration verification.

## Known documentation / implementation differences

Do not change these automatically; `SCHEMA.md` says its design is proposed, while the project instructions say models/migration already exist and the initial migration was applied. Confirm intended source of truth before a breaking migration.

- `career_roles`: schema/API use `name`; model and migration use unique `title`.
- `learner_interests`: schema/API require `is_primary` and only one primary interest; model/migration have no `is_primary` field or constraint.
- Profiles: resolved for the API as arrays of flexible objects; JSONB remains schema-flexible. Profile response normalization also supports legacy single-object JSON values.
- Assessments: schema calls for `correct_answers`, `started_at`, and `completed_at`; model/migration omit them. Schema says numeric score; model uses inferred float / migration `DOUBLE`. Answers schema requires `answered_at`; model/migration instead provide mixin timestamps, and `selected_answer` / `is_correct` are nullable.
- Jobs: schema/API use `experience_min/max`, `currency`, `application_url`, and `last_verified_at`; implementation instead has `experience_level`, `salary_currency`, `apply_url`, and `expires_at`, with no `last_verified_at`.
- `job_skills`: schema has `requirement_type` and `importance`; model/migration omit both.
- `job_matches`: schema has `matched_skills`, `missing_skills`, and `explanation`; implementation stores a generic `match_details` JSONB instead.
- Ingestion logs: schema expects fetched/inserted/updated/rejected counts; implementation has `jobs_fetched`, `jobs_created`, `jobs_updated` and no rejected count.
- Learning: schema expects `resource_url` and `is_verified`; implementation uses `url` and `is_active` (plus extra fields). Schema expects `learning_steps.completed_at`, which is absent.
- Chat: schema uses `sender` and optional `provider`; implementation uses `role` (including `system`) and has no provider field.
- Feedback: schema uses nullable `rating` and `message`; implementation requires rating, calls the text field `comment`, and adds status.
- `SCHEMA.md` still says model implementation is pending, which is stale relative to existing models and the initial migration.

Other unresolved implementation details: configure Supabase callback/redirect allowlists and backend CORS per environment; run frontend-to-real-Supabase integration with a non-production account; automated JWT tests use a fake JWKS client and do not test real JWKS network/key-rotation behavior; RLS policy ownership/deployment; one-primary-interest enforcement; schema reconciliation/migration for remaining domains; seed/catalogue data and ingestion scheduling. No RLS policies or seed data are present in the initial migration. Profile deletion intentionally leaves the Supabase Auth identity active; deleting that identity requires a separate trusted Supabase Auth workflow.

Configuration follow-up: set backend `CORS_ORIGINS` to the frontend origin (e.g. local port 3000), set frontend public `NEXT_PUBLIC_*` variables, and add `/update-password` to Supabase allowed redirect URLs. No local `.env` or Supabase project settings were changed.

## Development commands

Run from `backend/` with the project environment set up:

- `uv sync` — install locked project/development dependencies.
- `uv sync --locked` — synchronize the environment without modifying the lockfile.
- `uv run uvicorn app.main:app --reload` — run the API locally.
- `uv run pytest` — run the test suite (latest result: 27 passed).
- `uv run ruff check .` — full-project lint; currently reports 15 existing findings outside the touched auth tests/route.
- `uv run alembic upgrade head` — apply migrations; verify target and environment before running against Supabase.
- `uv run alembic revision --autogenerate -m "description"` — generate a candidate revision; always review it, especially external `auth` references, before applying.

From `frontend/`:

- `npm install` — install frontend dependencies.
- `npm run dev` — run Next.js locally.
- `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build` — frontend verification.
