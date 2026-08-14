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
docker compose up --build           # start db + api + web + erp + help + adminer
# Web (frontend/, đóng băng) http://localhost:8080
# ERP v2 (frontend-v2/, đang phát triển) http://localhost:8083
# Help Center http://localhost:8082
# API http://localhost:8000/docs · Adminer http://localhost:8081
```

On `api` startup, `backend/start.sh` runs automatically: wait for DB → `alembic upgrade head` → `python -m app.seed` (idempotent) → uvicorn with `--reload`. Code is bind-mounted, so backend and frontend hot-reload without rebuilds.

⚠️ **Hai bản seed.** `app/seed.py` = bản đầy đủ, CÓ dữ liệu mẫu — chỉ dùng cho LOCAL (`start.sh`).
Prod/dev-UAT (`start.prod.sh`) chạy `app/seed_prod.py`: không nạp dữ liệu mẫu, không tạo tài khoản demo,
và **không ghi đè** phân quyền/danh mục người dùng đã sửa trên UI — vì seed chạy lại mỗi lần deploy.
Khi đổi `STD_ROLES`, phân quyền cũ trên DB thật KHÔNG tự đổi theo; muốn áp lại phải đặt
`SEED_FORCE_SYNC=true` trong `.env`, restart api một lần rồi trả về `false`.

```bash
# DB migrations (after editing any app/modules/*/model.py)
docker compose exec api alembic revision --autogenerate -m "mo_ta"   # then review file in backend/migrations/versions/
docker compose exec api alembic upgrade head

# Reseed data + roles/permissions (LOCAL — có dữ liệu mẫu)
docker compose exec api python -m app.seed

# Backend tests (pytest, SQLite in-memory — never touches real DB)
docker compose exec -T api pip install pytest
docker compose exec -T api python -m pytest test/backend -q
docker compose exec -T api python -m pytest test/backend/test_process.py -q   # single file

# E2E (Playwright, run on host; requires stack up + demo accounts)
pytest test/e2e --headed -v

# Adding dependencies
docker compose exec web npm install <pkg> && docker compose restart web   # frontend (edit package.json)
docker compose exec erp npm install <pkg> && docker compose restart erp   # frontend-v2
docker compose up --build api                                             # backend (edit requirements.txt)

# Cổng kiểm tra frontend-v2 — chạy hết trước khi báo xong việc (typecheck + lint + test)
docker compose exec erp npm run check
docker compose exec erp npm run test          # vitest run
docker compose exec erp npm run lint          # eslint . — phải 0 lỗi
docker compose exec erp npm run typecheck     # tsc --noEmit — phải 0 lỗi
# Prettier có sẵn nhưng CHƯA nằm trong cổng: `format:check` đang đỏ ~381 tệp vì chưa
# ai chạy `format --write` lần nào. Muốn dọn thì chạy riêng thành một commit độc lập.
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

⚠️ **`frontend/` ĐÃ ĐÓNG BĂNG (D-026, 13/08/2026) — chỉ sửa lỗi, KHÔNG nhận tính năng mới.**
Mọi phát triển giao diện từ nay làm ở **`frontend-v2/`** (React 19 + Vite 8 + Tailwind 4 +
shadcn/Radix + TanStack Query + zustand). Backend không đổi: v2 gọi đúng `/api/...` cũ và
đúng phong bì `{success, message, data}` cũ.

Phân xử khi có yêu cầu mới: **sửa lỗi** màn đang chạy thật → `frontend/`; **tính năng mới**
→ `frontend-v2/`, màn đó chưa có ở v2 thì dựng màn đó trước. `frontend/` chưa được tắt vì v2
còn thiếu 6 màn: Yêu cầu báo giá, Công nợ, Yêu cầu thanh toán, Tiến độ mua hàng, Báo cáo,
Phân quyền.

### `frontend-v2/` — giao diện ERP (đang phát triển)

Chạy bằng `docker compose up -d erp` → **http://localhost:8083**. Không có npm workflow ngoài
Docker; code bind-mount nên HMR chạy. Gọi API bằng đường **tương đối** rồi qua proxy Vite
(`VITE_API_PROXY_TARGET`, trong Docker là `http://api:8000`) nên không dính CORS.

- **Phân hệ.** `src/modules/<tên>/` mỗi phân hệ một thư mục, khai báo ở `src/app/router/module-registry.ts`.
  Thêm phân hệ = thêm một dòng. Phân hệ chưa làm để `enabled: false` — hiện "Sắp có" nhưng không đăng ký route.
- **Tầng dùng chung.** `src/core/` (api, auth, authorization, i18n) · `src/shared/` (ui, data-table,
  conditional-filter, utils). Component riêng của phân hệ **không** để ở `shared/`.
- **Gọi API.** Dùng `apiGet<T>/apiPost<T>/apiPatch<T>/apiDelete<T>` (`@/core/api`) — đã bóc sẵn
  lớp phong bì, trả thẳng `data`. Cần cả `message` thì dùng `httpClient`.
- **Bảng danh sách.** Luôn dùng `DataTable` (`@/shared/data-table`), đọc `docs/ui/table.md` trước.
  Không tự ghép `<Table>` ở tầng trang.
- **Phân hệ Văn bản chưa có backend** — đang chạy trên localStorage (`modules/document/store/local-collection.ts`).
  Đây là bản mô phỏng giao diện; kiểu dữ liệu của nó **chưa khớp** thiết kế ở `ke-hoach/erp/van-thu/04-bang-du-lieu.md`.
- **Kiểm tra trước khi giao: `docker compose exec erp npm run check`** — gộp ba cổng:
  - `typecheck` (`tsc --noEmit`) phải **0 lỗi** (khác `frontend/`, bên đó baseline là đúng 4 lỗi cũ);
  - `lint` (**ESLint 10** flat config, `eslint.config.js`) phải **0 lỗi**. Cảnh báo hiện còn **6**
    (`react-refresh/only-export-components`) — đừng thêm mới. `typescript` ghim ở **5.9.3**,
    KHÔNG nâng lên 7 vì `typescript-eslint@8` chưa chạy được trên TS 7 (xem D-027);
  - `test` (**Vitest 4** + jsdom + Testing Library, cấu hình `vitest.config.ts`) phải xanh hết.
- **Test đặt cạnh tệp nó kiểm** (`format-money.ts` → `format-money.test.ts`); luật đầy đủ ở
  `frontend-v2/.claude/rules/testing.md`. Múi giờ khi chạy test cố định `Asia/Ho_Chi_Minh`.

### `frontend/` — bản đang chạy thật (đóng băng)

**Config-driven CRUD.** Most list/detail screens are declared as data in `src/config/cruds.tsx` (`CrudConfig`: columns, fields, filters, entity, apiPath) and rendered generically by `components/CrudList.tsx` + `components/CrudDetail.tsx`. Routing in `App.tsx`: the catch-all `:entity` / `:entity/:id` routes drive these; anything needing bespoke logic (PurchaseRequestDetail, SurveyDetail, PurchaseOrderDetail, Reports, RolePermissions, print pages, …) gets an explicit route + a page in `src/pages/`. **To add a simple screen, add a config entry; only write a page when behavior is genuinely custom.**

**Auth & gating.** `auth/AuthContext.tsx` exposes `can(entity, action)` backed by the permissions map returned at login. Use it to hide menu items / action buttons and lock fields. This is UI-only convenience — the backend `require`/`apply_scope` is the real enforcement, so never rely on `can()` for security.

**Help Center is a separate app.** `help-center/` (React 18 + Vite + **Tailwind v4 + shadcn/ui** — KHÁC stack plain-CSS của `frontend/`) chạy độc lập ở cổng 8082, **dùng chung backend + tài khoản**. Menu "Hướng dẫn sử dụng" trong `frontend/` chỉ là link ra ngoài (`VITE_HELP_URL`) — không còn route `/hdsd`. Quyền ghi tài liệu = entity `help_article` (vai trò `help_admin` seed sẵn, đăng nhập `helpadmin`). Chi tiết: `help-center/README.md`.

**Money formatting.** Never call `toLocaleString('vi-VN')` straight on an amount — it defaults to 3 fraction digits, so cents leak into list columns (`4.760.000,08 đ`). Use `src/utils/money.ts`: `fmtVND` for TIỀN (rounds to đồng) and `fmtPrice` for ĐƠN GIÁ (keeps all 4 decimals allowed since migration `d4b9e7c1a305`). Display-only — stored values stay exact.

**API client.** `src/api/client.ts` — axios instance with a request interceptor injecting the Bearer token and a response interceptor that auto-refreshes the access token once on 401 (via `/api/auth/refresh`) then retries, logging out on failure. Non-GET errors auto-toast unless `config._silent` is set.

## Tests

- `test/backend/` — pytest against SQLite in-memory (fixtures in `test/backend/conftest.py`); fast, isolated per function, tests services/serializers/RBAC helpers directly.
- `test/e2e/` — Playwright Python on the host; needs the stack running and demo accounts (`TESTREQ`, `DEMONV`, `DEMOTP`, `DEMO_MANAGER_PURCHASE`, password = code).

## Docs

Requirements, permission design, and naming conventions live in `doc/` (Vietnamese) — index at `doc/README.md`. Permission design detail: `doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`. Progress checklist: `TASKS.md`.

⚠️ **Trước khi đụng vào cấu trúc Sản phẩm, đọc `doc/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md`.** `tab_product` **là bảng VARIANT (SKU)**, không phải sản phẩm cha — cố ý như vậy. Không có FK nào trỏ vào nó; 7 bảng (YCMH, ĐMH, nhận hàng, tồn kho, luân chuyển kho, lịch sử mua hàng, option khảo sát) nối nhau bằng **chuỗi `product_code`**, nên đó là hạt dữ liệu của cả hệ. Muốn gom nhóm thì thêm tầng cha Ở TRÊN; **cấm** thêm `tab_product_variant` ở dưới, cấm đổi/tái dùng `product_code`, cấm đặt cột giá lên sản phẩm. Xem D-025 trong `change-log.md`.
