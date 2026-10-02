# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Internal procurement tool for DEGO Holding (~20–100 users) digitizing the flow:
**Purchase Request (PYC) → Price Survey (NCC/SP) → Purchase Order (PO) → Goods Receipt (GR) → Payables → Payment Request**, with RBAC + data-scope permissions.

Domain language is **Vietnamese** — entity names, code comments, and UI labels are all in Vietnamese. Preserve this when editing.

**Status columns — rule R2 (QĐ-11, 22/08/2026). For anything NEW, do not store text.** A column meaning status / type / level / stage stores a **`SMALLINT` backed by an `IntEnum`**; the API returns the number plus a label, and Vietnamese lives only in the display layer. Reference implementation: the `import_tool`, `document/`, `approval/` and `doc_catalog/` modules.

Legacy exceptions, do not copy them into new code:

- **12 columns used to hold Vietnamese text** (e.g. `line_status == "Hủy đơn"`, `tab_po_item.progress_status`). Batches B-01…B-06 converted **all twelve** to codes on branch `erp-v2` — plan and per-batch record in [`doc/erp/15-do-be-tong-nen-v2.md`](doc/erp/15-do-be-tong-nen-v2.md). Two known leftovers stay in Vietnamese and are **out of scope** of that plan: `line_approve` on the two survey line tables (§2.2) and the `STATE_*` constants in `survey_request/line_state.py` (derived, never stored).
- **Thu mua migrates to fixed English string codes, not numbers** (QĐ-9), because its document `status` columns already use codes like `draft | submitted | approved`. Mixing two shapes inside one document is worse than the inconsistency between modules. This applies **only** to columns already in that plan — it is not a licence for new ones.

Fixed code sets of either shape are declared in `backend/app/core/status_catalog.py` and registered via `app/core/code_sets.py`; `backend/scripts/gen_status_ts.py` generates the frontend copy, so never hand-write a status list in TypeScript.

Stack: FastAPI 0.115 · SQLAlchemy 2.0 · Pydantic v2 · MySQL 8 · Alembic · React 18 + Vite + TS. Runs entirely via Docker Compose.

⚠️ **Trước khi đụng vào nhánh `main` hoặc vào VPS, đọc `doc/tai-lieu-ky-thuat/quy-trinh-nhanh-va-deploy.md`.**
Repo có **hai nhánh chạy song song**: `main` = prod (backend + `frontend/` + `help-center/`),
`erp-v2` = dev (`frontend-v2/`). Deploy prod **bắt buộc** có `-f docker-compose.production.yml`.

⚠️ **Luật "merge chỉ một chiều `main` → `erp-v2`" đã HẾT HIỆU LỰC ngày 11/09/2026**: `erp-v2` được
gộp vào `main` và **backend v2 đã lên prod** (115 migration, `alembic_version` = `bee157de2ec8`,
60 → 141 bảng). **Giao diện v2 cũng lên prod cùng tối** ở **`erp.degoholding.vn`** (service `erp`,
container `procurement-erp`) — chạy **song song** với `thumua.degoholding.vn` trên **cùng một
database**; tắt `frontend/` là đợt Đ-15 riêng, chưa làm. Nếp làm hằng ngày **giữ nguyên**: vá lỗi prod ở `main` rồi gộp sang `erp-v2`; muốn đi
chiều ngược lần nữa thì phải chạy đủ kịch bản phát hành (diễn tập trên bản sao · sao lưu có kiểm ·
ngưỡng quay đầu), xem §A.2 của `quy-trinh-nhanh-va-deploy.md`.

## Rules

    Pls check rule in @backend/.claude/rules/**

Luật chi tiết theo từng khu nằm ở `.claude/rules/` — mỗi tệp khai `paths:` nên chỉ nạp khi làm việc
với đúng thư mục đó (CLAUDE.md giữ phần cốt lõi). Thêm luật cho một khu cụ thể thì ghi vào tệp đó,
đừng nhồi lại vào đây:

| Tệp | Nạp khi đụng | Nội dung |
|---|---|---|
| `.claude/rules/frontend-v2-migration-status.md` | `frontend/`, `frontend-v2/` | Tiến độ dời màn v1 → v2 (Đ-01…Đ-15), luật nhận đợt, các màn vừa dời |
| `.claude/rules/frontend-v2-ui-conventions.md` | `frontend-v2/src/` | `LinesTable`, ô chỉ xem, trường bắt buộc YCMH/YCBG/ĐMH, bốn bẫy biểu mẫu, bẫy bảng có bộ lọc |
| `.claude/rules/frontend-v1-frozen.md` | `frontend/`, `help-center/` | CRUD khai báo, `can()`, Help Center, định dạng tiền, API client của bản cũ |
| `.claude/rules/hr-leave.md` | `leave/`, `approval/`, `hr/` | Nghỉ phép: khóa quyền, giữ chỗ quỹ, đơn nhiều loại nghỉ, duyệt ngay trong màn |
| `.claude/rules/hr-employee-profile.md` | `employee/`, `hr/`, seed | Hồ sơ nhân sự mở rộng, `employee_sensitive`, danh mục Chức vụ |
| `.claude/rules/backend-input-limits.md` | `backend/app/`, `test/backend/` | Cột `String(n)` phải có `max_length` (500 → 422), trần JSON/ngày/số dòng |
| `.claude/rules/document-folders-search.md` | `document/`, `doc_catalog/`, migrations | Thư mục văn bản, `doc_folder`, chỉ mục tìm toàn văn, bẫy từ dừng FULLTEXT |
| `frontend-v2/.claude/rules/*.md` | `frontend-v2/` | Component, styling, icon, naming, TypeScript, testing của giao diện v2 |

## Commands

Everything runs in Docker; there is no local venv/npm workflow.

⚠️ **Máy đơ / tự thoát app khi chạy test hay build? Đọc `doc/tai-lieu-ky-thuat/gioi-han-tai-nguyen-docker.md`.**
Stack local có **11 container**; `docker-compose.yml` đã đặt `mem_limit` + `cpus` cho từng cái —
**không tự ý gỡ**. Trần đó chỉ chặn từng container; chặn cả máy ảo Docker phải đặt thêm
`%USERPROFILE%\.wslconfig` (mẫu ở `docker/wslconfig.example`, mỗi máy tự chép, không commit).
Bốn luật cho trợ lý AI: **chỉ chạy test của phần vừa sửa** (đừng quét cả `test/backend`) ·
`restart` thay vì `up --build` khi không đổi `requirements.txt`/`package.json`/`Dockerfile.*` ·
**không tự chạy `wsl --shutdown`** (giết mọi container) · máy yếu thì tạo
`docker-compose.override.yml` riêng (đã gitignore) chứ đừng sửa tệp dùng chung.

```bash
docker compose up --build           # start db + api + web + erp + help + adminer
# Nhẹ máy: docker compose stop adminer redisinsight qdrant   (+ web help nếu chỉ làm erp)
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

# Cổng kiểm tra frontend-v2 — typecheck + lint chạy CẢ CÂY, vitest chỉ chạy THEO THƯ MỤC vừa sửa
docker compose exec -T erp npm run typecheck                          # tsc --noEmit — phải 0 lỗi
docker compose exec -T erp npm run lint                               # eslint . — phải 0 lỗi
docker compose exec -T erp npx vitest run src/modules/<phân hệ>       # chỉ phân hệ vừa đụng
docker compose exec -T erp npx vitest run src/shared/<khu>            # đụng lớp dùng chung thì thêm khu đó
# `npm run check` / `npm run test` = quét hết ~3200 bài (5-6 phút, ăn trọn 2 CPU của container).
# Đại ca chốt 17/09/2026: KHÔNG chạy full nữa; chỉ chạy khi đại ca bảo hoặc ngay trước deploy.
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
2. **Data scope belongs to USERS** — each `(user × role)` grant carries its own scope (`own·assigned·proc·dept_proc·dept·company·all`; `dept_proc` = `proc` AND the ticket's department or handler department is one of mine, bao-CR-414) plus explicit include/exclude by company/department/employee. `apply_scope(query, Model, entity, user, profile)` filters a query as the **OR (union)** of every grant that has `action` on that entity. Which columns a scope filters on per entity is defined in `SCOPE_FIELDS` in `scoping.py`. **Every entity in `ENTITIES` must be declared there** (B-07/CR-131, branch `erp-v2`): either with real columns, or with the `PUBLIC` sentinel when it is deliberately unfiltered. An entity that is missing, or a scope that cannot be turned into a condition, now **blocks everything** (`false()`) and logs a warning to `app.scoping` — it no longer falls through to "see all". A test asserts 44/44 (`test_pham_vi_khai_du_b07.py`), so adding an entity without declaring it turns the suite red. Fetching a single row by id must go through `get_scoped(...)`, not `db.get(...)`, or the list filter is trivially bypassed by typing an id into the URL.

A typical list endpoint composes both: `require(...)` as the route dependency, then `apply_scope(apply_filters(query, ...), ...)`. See `modules/purchase_request/controller.py` for the canonical example.

**Permission profile cache.** `get_perm_profile(db, user)` builds the grant profile and caches it in-process for 60s (`_PERM_CACHE` in `core/auth.py`). **When mutating roles/permissions/role-assignments you must call `perm_cache_clear(user_id)`** or scopes go stale for up to a minute.

**Generic vs custom CRUD.** Simple catalog entities use the router factory `make_crud_router(...)` in `core/crud.py` (list/get/create/update/delete + audit + optional CSV import/export). Complex features (purchase_request, survey, purchase_order, etc.) hand-write their controllers. Follow whichever pattern the neighboring module uses.

**Filtering & pagination.** `apply_filters` (whitelist-based LIKE / IN filters from query params) and `pagination` live in `core/base_controller.py`. Mutations are audited via `core/audit.py record(...)`.

## Frontend architecture

⚠️ **`frontend/` ĐÃ ĐÓNG BĂNG (D-026, 13/08/2026) — chỉ sửa lỗi, KHÔNG nhận tính năng mới.**
Mọi phát triển giao diện từ nay làm ở **`frontend-v2/`** (React 19 + Vite 8 + Tailwind 4 +
shadcn/Radix + TanStack Query + zustand). Backend không đổi: v2 gọi đúng `/api/...` cũ và
đúng phong bì `{success, message, data}` cũ.

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
- **Phân hệ Văn bản ĐÃ CÓ backend thật** (đính chính 27/08/2026 — bản CLAUDE.md cũ ghi
  "chạy localStorage" là hết hạn): backend nằm ở `app/modules/document/` + `app/modules/doc_catalog/`
  (router đăng ký đủ trong `main.py`, dữ liệu trong MySQL qua Alembic); frontend-v2 gọi API thật qua
  `modules/document/api/*` + hook TanStack Query. `store/local-collection.ts` chỉ còn là di tích:
  duy nhất kiểu `HistoryEntry` còn được import, `hooks/use-collection.ts` không ai dùng nữa.
- **Kiểm tra trước khi giao — ba cổng, nhưng cổng `test` chạy THEO THƯ MỤC** (đại ca chốt
  17/09/2026, bộ test đã hơn 3200 bài): `npm run typecheck` + `npm run lint` cả cây, rồi
  `npx vitest run src/modules/<phân hệ vừa sửa>` (đụng `src/shared/*` hay `src/core/*` thì chạy
  thêm đúng khu đó). `npm run check` gộp full test — **chỉ chạy khi đại ca bảo hoặc trước deploy**:
  - `typecheck` (`tsc --noEmit`) phải **0 lỗi** (khác `frontend/`, bên đó baseline là đúng 4 lỗi cũ);
  - `lint` (**ESLint 10** flat config, `eslint.config.js`) phải **0 lỗi**. Cảnh báo hiện còn **23**
    (đều NGOÀI lớp CRUD — `react-refresh/only-export-components` + vài chỗ tích lũy từ các CR văn
    thư/Trang chủ). Nhóm 7 `no-explicit-any` của lớp CRUD **đã hết** sau B-09/CR-142
    (`shared/crud/` ràng `CrudRecord`, §6.5 của `doc/erp/13-...md` đóng) — đừng thêm mới.
    `typescript` ghim ở **5.9.3**,
    KHÔNG nâng lên 7 vì `typescript-eslint@8` chưa chạy được trên TS 7 (xem D-027);
  - `test` (**Vitest 4** + jsdom + Testing Library, cấu hình `vitest.config.ts`) phải xanh hết.
- **Test đặt cạnh tệp nó kiểm** (`format-money.ts` → `format-money.test.ts`); luật đầy đủ ở
  `frontend-v2/.claude/rules/testing.md`. Múi giờ khi chạy test cố định `Asia/Ho_Chi_Minh`.

## Tests

- `test/backend/` — pytest against SQLite in-memory (fixtures in `test/backend/conftest.py`); fast, isolated per function, tests services/serializers/RBAC helpers directly.
- `test/e2e/` — Playwright Python on the host; needs the stack running and demo accounts (`TESTREQ`, `DEMONV`, `DEMOTP`, `DEMO_MANAGER_PURCHASE`, password = code).

## Docs

Requirements, permission design, and naming conventions live in `doc/` (Vietnamese) — index at `doc/README.md`. Permission design detail: `doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`. Progress checklist: `TASKS.md`.

### Nhật ký task — `doc/tai-lieu-ky-thuat/nhat-ky-task.md`

Mỗi phiên làm việc phải ghi một mục vào sổ này; `backend/scripts/sync_task_journal.py` đẩy sổ lên phân hệ **Dự án** (`modules/work`) và **sổ SỞ HỮU phần mô tả** — đừng sửa mô tả task bằng tay trên ERP. Mặc định người phụ trách là `NSU209` (đại ca), khai bằng `- pic:` hoặc biến `WORK_SYNC_PIC`; sổ ghi **mã** nhân sự chứ không ghi số id vì id local/dev/prod khác nhau.

⚠️ **Luật viết mô tả (đại ca chốt 17/09/2026): mô tả phải là câu tiếng Việt trọn vẹn.** Nói việc trước, tên tệp sau — tên hàm/tên bảng/mã commit gom xuống dòng cuối mở đầu bằng `Mã nguồn:` / `Commit:` / `Deploy:`. Dòng chỉ gồm tên tệp nối nhau là SAI. Từ tiếng Anh chỉ giữ khi công ty vẫn gọi bằng từ đó (commit, deploy, migration, script, API); còn lại dịch (*upsert* → có rồi thì cập nhật chưa có thì tạo, *endpoint* → đường API, *test* → bài kiểm). Bản đầy đủ của luật nằm ở đầu chính tệp sổ — đọc trước khi ghi mục mới.

⚠️ **Trước khi đụng vào cấu trúc Sản phẩm, đọc `doc/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md`.** `tab_product` **là bảng VARIANT (SKU)**, không phải sản phẩm cha — cố ý như vậy. Không có FK nào trỏ vào nó; 7 bảng (YCMH, ĐMH, nhận hàng, tồn kho, luân chuyển kho, lịch sử mua hàng, option khảo sát) nối nhau bằng **chuỗi `product_code`**, nên đó là hạt dữ liệu của cả hệ. Muốn gom nhóm thì thêm tầng cha Ở TRÊN; **cấm** thêm `tab_product_variant` ở dưới, cấm đổi/tái dùng `product_code`, cấm đặt cột giá lên sản phẩm. Xem D-025 trong `change-log.md`.
