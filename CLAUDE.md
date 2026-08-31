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
`erp-v2` = dev (`frontend-v2/`). Merge **chỉ một chiều `main` → `erp-v2`**; đưa ngược lại là kéo
34 migration chưa duyệt vào database thật. Deploy prod **bắt buộc** có `-f docker-compose.production.yml`.

## Rules

    Pls check rule in @backend/.claude/rules/**

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
2. **Data scope belongs to USERS** — each `(user × role)` grant carries its own scope (`own·assigned·proc·dept·company·all`) plus explicit include/exclude by company/department/employee. `apply_scope(query, Model, entity, user, profile)` filters a query as the **OR (union)** of every grant that has `action` on that entity. Which columns a scope filters on per entity is defined in `SCOPE_FIELDS` in `scoping.py`. **Every entity in `ENTITIES` must be declared there** (B-07/CR-131, branch `erp-v2`): either with real columns, or with the `PUBLIC` sentinel when it is deliberately unfiltered. An entity that is missing, or a scope that cannot be turned into a condition, now **blocks everything** (`false()`) and logs a warning to `app.scoping` — it no longer falls through to "see all". A test asserts 44/44 (`test_pham_vi_khai_du_b07.py`), so adding an entity without declaring it turns the suite red. Fetching a single row by id must go through `get_scoped(...)`, not `db.get(...)`, or the list filter is trivially bypassed by typing an id into the URL.

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
còn thiếu màn. **Số đo đầy đủ và kế hoạch dời nằm ở `doc/erp/13-ke-hoach-man-con-lai-v2.md`**
(bản 2.0, xem **CR-097**): bản cũ có **48 màn** — _(đếm 24/08/2026, CR-132)_ **35 xong** ·
**1 có nhưng KHUYẾT** · **9 chưa có** · 2 đã bỏ · 1 chờ quyết. Chia **15 đợt Đ-01 … Đ-15**: đã
xong **Đ-01…Đ-12, Đ-14**; còn mỗi **Đ-15** (tắt `frontend/`), mà nó chờ **Đ-13** _Quản lý Import_
đang **hoãn**. Nghĩa là **không còn việc dựng màn hình nào trước mắt**.
⚠️ Mấy con số này cũ rất nhanh — **luôn mở §0 và bảng §3 của `13-...md` để lấy số mới nhất**,
đừng trích lại dòng này.
⚠️ **NHẬN ĐỢT TRƯỚC KHI LÀM.** Nhiều người cùng đẩy lên `erp-v2`, nên cột **_Ai làm_** trong bảng
§3 của `13-...md` là **chỗ ghi phân công duy nhất** — luật bốn dòng ở §3.1: ghi tên + đổi
_Đang làm_ rồi **push riêng dòng đó ngay** trước khi gõ mã, xong thì đổi _Xong (CR-xxx)_, bỏ
giữa chừng thì trả về _(chưa nhận)_. `git fetch` trước mỗi lần bắt đầu và trước mỗi lần push.
**Cụm Yêu cầu thanh toán ĐÃ XONG** (Đ-06/07/08, CR-119): danh sách + chi tiết + phiếu in ở
`/finance/payment-requests` theo QĐ-5 — `modules/finance/pages/payment-request-{list,detail,print}-page.tsx`,
route in đăng ở `app/router/app-router.tsx`. Bản in cũng đã có **gom dòng trùng số chứng từ** và
tab _Mẫu thuế_ giống hệt bản v1 (CR-127). Nghĩa là **không còn màn nào chặn nghiệp vụ** — dòng
"chặn nghiệp vụ chỉ còn Yêu cầu thanh toán" ở các bản CLAUDE.md trước nay đã sai, bỏ đi.
Trong 9 màn còn thiếu, nặng nhất là _Quản lý Import_ (MC-6) và khách đã cho **hoãn**; danh sách
đầy đủ ở §1 của `13-...md`. _Tiến độ báo giá_ và _Xử lý khảo sát_ từng quyết bỏ nhưng
**đã SỐNG LẠI 29/08/2026** (CR-227 + CR-222) — xem đính chính ở `doc/erp/12-...` mục 2.7:
Xử lý khảo sát là trang riêng `/procurement/survey-requests/:id/process`, Tiến độ báo giá ở
`/procurement/survey-progress`, menu Thu mua v2 xếp đúng thứ tự bản v1.
**Đã xong Đ-11** (CR-132 — số cũ CR-129 bị trùng nên đánh lại): Trang chủ có lại đủ 4 khối
(_Top nhà cung cấp_, _Chi tiêu theo bộ phận_, _Trạng thái đơn hàng_, _Tuổi nợ_) và thao tác nhanh
_Duyệt / Trả lại_ YCMH; **Tổng quan Tài chính** và **Tổng quan Kho** đã dựng xong. §1.8 của `13`
nay đã ĐÓNG HẾT: dòng cuối (chi tiết YCBG thiếu nút _Xử lý khảo sát_) xong ở CR-222 ngày 29/08.
⚠️ **`/api/dashboard/overview` chỉ đòi đăng nhập, rồi gác TỪNG KHỐI bên trong bằng `can(entity)`
và BỎ HẲN khóa** khi thiếu quyền — nên đọc nhầm khóa của phân hệ khác thì không ai ăn 403, chỉ
thấy **0** vĩnh viễn. Mọi khóa trong `DashboardOverview.kpi` là **tùy chọn**, luôn đọc kèm `?? 0`.
Hai khóa dễ nhầm nhất: `top_suppliers` = **CHI TIÊU** theo NCC _(khối `purchase_order`)_, còn
`top_debt_suppliers` = **NỢ CÒN LẠI** _(khối `payable`)_. Xem `test/backend/test_tong_quan_thu_mua.py`.
Màn **Công nợ đã đủ** cột tick chọn + nút _Tạo đề nghị thanh toán_ từ Đ-09 (CR-119).
**Đã xong MC-1…MC-4** (CR-094): Đặt lại mật khẩu · Thông báo (`/notifications`) · Trang cá
nhân (`/me`) · Cấu hình hệ thống (`/system/settings`, phân hệ Quản trị nay **bật**).
**Đã xong Đ-01** (CR-098): Dựng khung Generic Declarative CRUD (`frontend-v2/src/shared/crud/`)
kế thừa 3 cấp độ (CrudListPage + CrudDetailPage có RecordIdentityCard + AuditTimeline + hỗ trợ tabs/bảng con DataTable + CrudFormDialog) và dời Danh mục Kho (`/inventory/warehouses` và `/inventory/warehouses/:id`).
**Đã xong Đ-02** (CR-099): Dời Đơn vị tính (`/production/units` + `/production/units/:id`) và Phân loại VTBB/NL (`/production/item-groups` + `/production/item-groups/:id`) sang `frontend-v2` kế thừa 100% tầng generic CRUD, gắn vào phân hệ Sản xuất.
**Đã xong Đ-03** (CR-100): Dời Sản phẩm & Vật tư (`/production/products` + `/production/products/:id`) sang `frontend-v2` có tab _Lịch sử mua hàng_ (`PurchaseHistoryTable` với `DataTable` riêng, ẩn/hiện cột NCC theo quyền `supplier.read`, link sang ĐMH và gắn `AuditTimeline`).
**Đã xong Đ-05** (CR-106): **Nhà cung cấp** — danh sách `/production/suppliers` dời sang khung CRUD
khai báo (`production/config/supplier-crud.tsx`) và dựng `/production/suppliers/:id` **5 tab** đúng
bản cũ: _Thông tin_ · _Hợp đồng_ · _Công nợ & Đánh giá_ · _Lịch sử mua hàng_ · _Khảo sát của NCC_
(kế hoạch `erp/13` ghi "3 tab" là đếm sai, đã đính chính). Đây là màn danh sách **cuối cùng** còn tự
ghép `<Table>`. Khung CRUD nay có kiểu trường **`percent`** (`shared/crud/field-values.ts`) — dùng nó
cho VAT, đừng tự nhân chia 100 ở tầng màn: `Supplier.vat` lưu **tỷ lệ** `0.08` chứ không lưu `8`
(CR-058). ⚠️ **Tab mượn dữ liệu của phân hệ khác thì phải tự tắt khi thiếu quyền** — `usePayables`,
`usePayableSummary`, `useCompanies` không có nhánh tắt, cứ mount là gọi và người dùng ăn toast 403
ngay lúc mở tab; truyền `enabled` hoặc bọc bằng `can(...)` trước khi dựng component con.
**Bảng DÒNG CHỨNG TỪ dùng chung `LinesTable`** (`shared/data-table/lines-table.tsx`, CR-101 + CR-102):
bốn bảng dòng (YCMH · YCBG · ĐMH · Giao hàng nhiều lần trong popup chi tiết dòng ĐMH) đều chạy trên
nó — ghim cột, kéo thả đổi thứ tự, co giãn + auto-fit, tô màu, nhớ `localStorage`, nút _Bảng rút gọn
/ Bảng đầy đủ_ (cột phụ khai `compactHidden`, bảng nhiều cột bật `defaultCompact`). Bảng dòng mới
**phải dùng `LinesTable`**, đừng chép khung. ⚠️ **Không đặt bề rộng cứng cho `<table>`** —
`table-fixed` + `w-full` là đủ; gắn `style={{ width: totalWidth }}` thì ẩn cột xong bảng co lại,
chừa một lỗ trắng bên phải trong khung viền (đúng lỗi CR-102 phải vá). Xem `doc/erp/13-...md` §6.
⚠️ **Ô CHỈ XEM: cấm `<Input disabled>` / `<Textarea disabled>`** — `disabled` gỡ luôn khả năng
nhận con trỏ nên người dùng KHÔNG bôi đen, KHÔNG copy được giá trị, lại còn bị làm mờ 50% nhìn
như chữ gợi ý. Dùng `shared/ui/read-only-value.tsx` (chữ trong thẻ thường, khung viền nền mờ).
Giá trị nằm trong **ô CHỌN** thì bản chất là một `<button>` — bôi đen không được bằng cách nào cả,
phải gắn `shared/ui/copy-button.tsx` bên cạnh (xem CR-105).
⚠️ **TRƯỜNG BẮT BUỘC của YCMH · YCBG · ĐMH khai MỘT CHỖ:**
`modules/procurement/utils/required-fields.ts` (CR-107) — vừa là nguồn vẽ dấu sao đỏ, vừa là
nguồn câu chặn lúc **gửi duyệt** (không chặn lúc lưu nháp). Bộ trường của ĐMH phải khớp
`TRUONG_BAT_BUOC_DONG` ở `backend/app/modules/purchase_order/service.py` (cổng CR-095); YCMH và
YCBG thì backend **không kiểm**, luật chỉ nằm ở giao diện. Đừng gõ `*` thẳng vào chuỗi nhãn —
ô nhập dùng `shared/ui/required-mark.tsx`, tiêu đề cột dùng đuôi `" *"`
(`shared/data-table/required-header.ts`, xem `docs/ui/table.md` §1). **VAT cố ý KHÔNG bắt buộc**:
`0` vừa nghĩa "chưa nhập" vừa nghĩa "hàng không chịu thuế".
Đụng vào **bảng dòng của phiếu khảo sát** (cả hai bản) thì đọc **hợp đồng hiển thị** ở dòng
**CR-090** trong `doc/tai-lieu-ky-thuat/change-log.md` trước — 5 điều kiện về xuống dòng /
ô chỉ xem / ô chọn NCC / phím Enter / bề rộng cột, làm hụt là lủng đúng chỗ vừa sửa lỗi.
_Tiến độ mua hàng_ và _Phân quyền_ thì **đã có ở v2** rồi
(`procurement/pages/purchase-progress-page.tsx`, `hr/pages/role-permission-page.tsx` +
`user-permission-detail-page.tsx`) — danh sách cũ ghi sai.
Vừa dời xong: **chi tiết Phiếu khảo sát** (`procurement/pages/survey-detail-page.tsx`, xem
CR-091), **chi tiết Yêu cầu báo giá** (`procurement/pages/survey-request-detail-page.tsx` —
nút _Xử lý khảo sát_ đã có từ CR-222, dẫn sang trang riêng), **Công nợ**
(`finance/pages/payable-list-page.tsx` — cột tick chọn đã có lại ở Đ-09/CR-119),
**Tồn kho** (`inventory/pages/inventory-list-page.tsx`) và **Báo cáo mua hàng**
(`procurement/pages/purchase-report-page.tsx` — tám tab, dữ liệu vẫn gom theo TÊN phòng
ban / NSPT, xem N-008 trong `doc/tai-lieu-ky-thuat/change-log.md`).

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
- **Kiểm tra trước khi giao: `docker compose exec erp npm run check`** — gộp ba cổng:
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
