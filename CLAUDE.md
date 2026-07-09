# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Internal procurement tool for DEGO Holding (~20–100 users) digitizing the flow:
**Purchase Request (PYC) → Price Survey (NCC/SP) → Purchase Order (PO) → Goods Receipt (GR) → Payables → Payment Request**, with RBAC + data-scope permissions.

Domain language is **Vietnamese** — entity names, status strings, code comments, and UI labels are all in Vietnamese. Preserve this when editing. Status values stored in the DB are often Vietnamese strings (e.g. `line_status == "Hủy đơn"`), not enums.

Stack: FastAPI 0.115 · SQLAlchemy 2.0 · Pydantic v2 · MySQL 8 · Alembic · React 18 + Vite + TS. Runs entirely via Docker Compose.

## Commands

Everything runs in Docker; there is no local venv/npm workflow.

```bash
docker compose up --build           # start db + api + web + adminer
# Web http://localhost:8080 · API http://localhost:8000/docs · Adminer http://localhost:8081
```

On `api` startup, `backend/start.sh` runs automatically: wait for DB → `alembic upgrade head` → `python -m app.seed` (idempotent) → uvicorn with `--reload`. Code is bind-mounted, so backend and frontend hot-reload without rebuilds.

```bash
# DB migrations (after editing any app/modules/*/model.py)
docker compose exec api alembic revision --autogenerate -m "mo_ta"   # then review file in backend/migrations/versions/
docker compose exec api alembic upgrade head

# Reseed data + roles/permissions
docker compose exec api python -m app.seed

# Backend tests (pytest, SQLite in-memory — never touches real DB)
docker compose exec -T api pip install pytest
docker compose exec -T api python -m pytest test/backend -q
docker compose exec -T api python -m pytest test/backend/test_process.py -q   # single file

# E2E (Playwright, run on host; requires stack up + demo accounts)
pytest test/e2e --headed -v

# Adding dependencies
docker compose exec web npm install <pkg> && docker compose restart web   # frontend (edit package.json)
docker compose up --build api                                             # backend (edit requirements.txt)
```

⚠️ **Never run `ALTER TABLE` / `INSERT` with Vietnamese text directly via `docker compose exec db mysql -e "..."`** — causes double-encoding mojibake. Always go through an Alembic migration or a Python/SQLAlchemy script.

⚠️ `alembic --autogenerate` only sees models imported in `backend/app/core/all_models.py`. A new module's model must be added there or migrations will miss its tables.

## Backend architecture

**Module pattern.** Each feature is `app/modules/<feature>/` with `model.py` (SQLAlchemy), `schema.py` (Pydantic), `service.py` (business logic), `controller.py` (FastAPI routes). Routers are all wired in `app/main.py`. `app/core/` holds shared infra.

**Response envelope.** All endpoints return via `app.core.response.success(data, message)` / `error(...)`. Shape is `{success, message, data}` or `{success, error:{code,message,details}}`. HTTPException and validation errors are remapped to this envelope by global handlers in `main.py`. The frontend depends on this shape.

**Two-axis permission system** (this is the core concept — spans `core/permissions.py`, `core/auth.py`, `core/scoping.py`):

1. **Actions belong to ROLES** — a `(entity × action)` matrix. Guard endpoints with the dependency `require(entity, action)` from `core/auth.py`. `ACTIONS = read·create·write·delete·approve·cancel·print·export`. `ENTITIES` are the canonical list in `core/permissions.py`.
2. **Data scope belongs to USERS** — each `(user × role)` grant carries its own scope (`own·assigned·proc·dept·company·all`) plus explicit include/exclude by company/department/employee. `apply_scope(query, Model, entity, user, profile)` filters a query as the **OR (union)** of every grant that has `action` on that entity. Which columns a scope filters on per entity is defined in `SCOPE_FIELDS` in `scoping.py` — an entity missing a dimension there simply isn't filtered on it.

A typical list endpoint composes both: `require(...)` as the route dependency, then `apply_scope(apply_filters(query, ...), ...)`. See `modules/purchase_request/controller.py` for the canonical example.

**Permission profile cache.** `get_perm_profile(db, user)` builds the grant profile and caches it in-process for 60s (`_PERM_CACHE` in `core/auth.py`). **When mutating roles/permissions/role-assignments you must call `perm_cache_clear(user_id)`** or scopes go stale for up to a minute.

**Generic vs custom CRUD.** Simple catalog entities use the router factory `make_crud_router(...)` in `core/crud.py` (list/get/create/update/delete + audit + optional CSV import/export). Complex features (purchase_request, survey, purchase_order, etc.) hand-write their controllers. Follow whichever pattern the neighboring module uses.

**Filtering & pagination.** `apply_filters` (whitelist-based LIKE / IN filters from query params) and `pagination` live in `core/base_controller.py`. Mutations are audited via `core/audit.py record(...)`.

## Frontend architecture

**Config-driven CRUD.** Most list/detail screens are declared as data in `src/config/cruds.tsx` (`CrudConfig`: columns, fields, filters, entity, apiPath) and rendered generically by `components/CrudList.tsx` + `components/CrudDetail.tsx`. Routing in `App.tsx`: the catch-all `:entity` / `:entity/:id` routes drive these; anything needing bespoke logic (PurchaseRequestDetail, SurveyDetail, PurchaseOrderDetail, Reports, RolePermissions, print pages, …) gets an explicit route + a page in `src/pages/`. **To add a simple screen, add a config entry; only write a page when behavior is genuinely custom.**

**Auth & gating.** `auth/AuthContext.tsx` exposes `can(entity, action)` backed by the permissions map returned at login. Use it to hide menu items / action buttons and lock fields. This is UI-only convenience — the backend `require`/`apply_scope` is the real enforcement, so never rely on `can()` for security.

**API client.** `src/api/client.ts` — axios instance with a request interceptor injecting the Bearer token and a response interceptor that auto-refreshes the access token once on 401 (via `/api/auth/refresh`) then retries, logging out on failure. Non-GET errors auto-toast unless `config._silent` is set.

## Tests

- `test/backend/` — pytest against SQLite in-memory (fixtures in `test/backend/conftest.py`); fast, isolated per function, tests services/serializers/RBAC helpers directly.
- `test/e2e/` — Playwright Python on the host; needs the stack running and demo accounts (`TESTREQ`, `DEMONV`, `DEMOTP`, `DEMO_MANAGER_PURCHASE`, password = code).

## Docs

Requirements, permission design, and naming conventions live in `doc/` (Vietnamese) — index at `doc/README.md`. Permission design detail: `doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`. Progress checklist: `TASKS.md`.
