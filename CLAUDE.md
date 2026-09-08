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
(bản 2.0, xem **CR-097**): bản cũ có **48 màn** — _(rà lại từng dòng 03/09/2026)_ bảng §1 nay
**50 dòng** *(48 màn cũ + `/system/exports` + 44b)*: **50 xong** · **0 khuyết** · **0 thiếu** ·
**0 chờ quyết**. Chia **15 đợt Đ-01 … Đ-15**: đã xong **Đ-01…Đ-14**; còn mỗi **Đ-15**
(tắt `frontend/`), và **không còn gì chặn nó**. Màn cuối cùng — **_Chứng từ_** — đã dời
03/09/2026 (CR-266): `/procurement/purchase-orders/:id/documents`, **không đứng trong menu**,
vào từ nút _Xem cả chuỗi chứng từ_ trong thẻ chứng từ của chi tiết ĐMH. ⚠️ Đụng vào nó thì nhớ
`/api/attachments/chain` khai entity `survey_line` **hai lần** (id dòng NCC + id dòng sản phẩm)
nên **phải khử trùng theo `link_id`** — bản v1 không khử nên đếm dôi; và `url` trong kết quả
**rỗng với entity riêng tư**, xem trước phải đi qua `/api/attachments/{id}/view`.
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
_Quản lý Import_ (MC-6) từng bị hoãn nhưng khách **mở lại 25/08/2026**: hai màn `/system/imports`
(+ `/:id`) và cụm `/system/exports` **đã chạy** (CR-186, Đ-13a/13b); phần còn dở của Đ-13 là **mở
rộng tính năng**, không phải màn thiếu — xem `doc/erp/16-quan-ly-import-export-v2.md` §9. _Tiến độ báo giá_ và _Xử lý khảo sát_ từng quyết bỏ nhưng
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
`REQUIRED_LINE_FIELDS` ở `backend/app/modules/purchase_order/service.py` (cổng CR-095); YCMH và
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

### Phân hệ NGHỈ PHÉP (CR-259, 03/09/2026)

Nằm **trong phân hệ Nhân sự** (`frontend-v2/src/modules/hr/`, menu *Nghỉ phép*),
backend ở `app/modules/leave/`. Tài liệu đầy đủ: `doc/tai-lieu-chuc-nang/17-nghi-phep.md`.

- ⚠️ **Bốn khóa quyền mới** — `leave_request` · `leave_balance` · `leave_type` · `holiday`
  (ENTITIES 46 → **50**). Tách bốn vì `leave_balance` ghi được nghĩa là **tặng thêm
  ngày phép cho bất kỳ ai**. Trên hệ ĐANG CHẠY, vai trò cũ **không tự có** chúng (seed
  không ghi đè — D-018): phải tick ở màn Phân quyền, hoặc `SEED_FORCE_SYNC=true` một lần.
- ⚠️ **`leave_request` là entity đầu tiên khai CẢ `owner` LẪN `self`** trong `SCOPE_FIELDS`.
  Một tờ đơn có hai người dính tới nó — người **lập** (`created_by`, hành chính lập hộ) và
  người **nghỉ** (`employee_id`). Nhánh `own` của `_role_scope_cond` HỢP cả hai, và chặn
  khi `employee_id = 0` (nếu không thì `== 0` trúng mọi dòng chưa gắn nhân sự → **mở rộng**
  phạm vi thay vì thu hẹp).
- ⚠️ **`pending_days` (giữ chỗ) là cột bắt buộc, không phải tối ưu.** Gửi duyệt là trừ
  ngay. Thiếu nhịp này thì nộp mười đơn liền tay đều lọt. Đối xứng: **ba kết cục
  không-duyệt (từ chối · trả về · rút) đều phải TRẢ LẠI** — gộp chung một hàm
  `_release_and_set`, đừng tách ba bản chép.
- ⚠️ **MỘT ĐƠN KHAI NHIỀU LOẠI NGHỈ** (07/09/2026, `tab_leave_request_line`). Cả đơn
  dùng chung một khoảng ngày, dòng chỉ chia SỐ NGÀY. Hai cột đầu đơn thành **dẫn
  xuất**: `total_days` = tổng các dòng, `leave_type_id` = loại của dòng nhiều ngày
  nhất. **Sổ quỹ phải chạy THEO DÒNG ở cả bốn nhịp** — dùng `reserve_lines` ·
  `consume_lines` · `release_lines` · `refund_lines` của `request_service`, đừng gọi
  thẳng `balance_service` với `obj.total_days` (trừ tổng vào loại chính là cộng ngày
  không lương vào quỹ phép năm). Chốt xóa loại nghỉ phải hỏi **cả hai bảng**. Điều
  kiện rẽ nhánh luồng duyệt chỉ thấy loại CHÍNH — hạn chế đã biết, xem §7.1 của
  `doc/tai-lieu-chuc-nang/17-nghi-phep.md`.
- ⚠️ **Số phép còn lại KHÔNG lưu thành cột** — `balance_service.remaining()` là nơi duy
  nhất tính. **Số ngày nghỉ** chỉ tính ở `workday_service.count_leave_days()`.
- ⚠️ **Hủy đơn KHÔNG được gọi `block_legacy_path`** (chốt đó chỉ dành cho duyệt/từ chối
  thẳng). Đường hủy đi qua `approval_bridge.cancel_request()` — nó **rút phiên duyệt**
  trước. Không rút thì người duyệt ký xong là hook trừ quỹ cho một tờ đơn đã hủy.
- Bộ mã **số** ở `leave/constants.py` (R2/QĐ-11), bản TypeScript gõ tay ở
  `hr/types/leave.ts` — `gen_status_ts.py` chỉ sinh cho bộ mã CHUỖI. Đừng lẫn với
  `core/leave_codes.py`: tệp đó khai mã **chuỗi** cho ô JSON của giấy GNP, và hai thế
  giới nối nhau qua `tab_leave_type.code`.
- **Seed chạy tay**, cố ý không nằm trong `app/seed.py`:
  `docker compose exec api python -m app.seed_nghi_phep` (chỉ THÊM, chạy lại được).

#### Duyệt NGAY trong màn Nghỉ phép (CR-260, 03/09/2026)

Màn `/hr/leave-requests` nay có **ba tab**: _Cần tôi duyệt_ · _Đơn của tôi_ ·
_Tôi đã duyệt_. Người duyệt không phải sang màn Phê duyệt nữa.

- ⚠️ **`apply_scope` một mình KHÔNG đủ cho nghỉ phép.** Người duyệt chặng 2 thường
  là Trưởng phòng Nhân sự, mà phạm vi dữ liệu của họ không với tới đơn của nhân
  viên phòng khác — bộ máy giao việc rồi chặn chính người được giao. `_get_or_404`
  và `approval_bridge.can_read_request` nay nới thêm: **đang có việc `TASK_PENDING`
  trên tờ đơn thì đọc được nó**. Nới đúng lúc treo, KHÔNG nới cho "đã từng ký" —
  ký xong quyền đó đóng lại, xem lại thì vào tab _Tôi đã duyệt_.
- ⚠️ Cột **Luồng duyệt** là **CHỮ một dòng**, không phải dải chấm. Bản dải chấm
  (chặng đang chờ sáng lên) đã dựng rồi BỎ ngày 03/09/2026 — trong ô bảng cao 35px
  nó đọc ra như một dãy biểu tượng lỗi. Câu chữ do **backend** dựng
  (`approval/steps_service._summary`) vì còn dùng cho bản in; đừng chép luật sang TS.
- ⚠️ **Không tab nào của màn Đơn nghỉ phép còn BÀY cột đó nữa** (duoc-CR-323,
  08/09/2026): _Đơn của tôi_ và _Tôi đã duyệt_ bỏ hẳn, _Cần tôi duyệt_ giữ nhưng
  `defaultHidden`. Cột **Việc của tôi** bỏ hẳn, **Hạn xử lý** rút về ngày giờ
  trần. Hai tín hiệu mất theo, đừng tưởng là sót: dấu **«Quá hạn»** (cờ
  `task.is_overdue` backend vẫn gửi, màn hình thôi không vẽ — bày lại thì đọc cờ
  đó, đừng tự so ngày ở TS) và dòng **«Bấm thay ‹tên›»**, thứ báo cho người được
  ủy quyền biết họ đang ký THAY người khác; nay chỉ còn ở màn chi tiết. Chi tiết
  ở §8.1 của `doc/tai-lieu-chuc-nang/17-nghi-phep.md`.
- ⚠️ **`defaultHidden` KHÔNG áp cho người đã từng đụng menu «Cột»** của bảng đó:
  `useTableLayout` đọc `readLayout(storageKey) ?? defaultLayout`, có bản lưu
  trong `localStorage` là bản đó thắng. Muốn thấy đúng mặc định mới thì xóa khóa
  `erp.table.<storageKey>`.
- ⚠️ `steps_service` đọc **cả bảng việc lẫn `flow_snapshot`**. Bảng việc chỉ có
  chặng ĐÃ MỞ, nên hỏi riêng nó thì luồng 2 chặng vừa gửi đi chỉ ra một chấm.
  Tổng số chặng lấy từ bản chụp luồng nằm trong chính phiếu. Gom **3 truy vấn cho
  cả trang** bất kể bao nhiêu dòng — có test đếm truy vấn canh, đừng đặt query
  trong vòng lặp.
- ⚠️ Tab _Tôi đã duyệt_ **gộp mỗi đơn một dòng** (`_latest_per_request`):
  `handled_tasks` trả theo dấu vết nên ký hai chặng của cùng tờ đơn ra hai dòng
  giống hệt nhau.
- ⚠️ **`ENTITY_LABELS` + `ENTITY_LINKS` của `task_notification.py` phải có mọi
  entity mới.** Thiếu thì thư vẫn gửi nhưng ghi "Phiếu NP009" và `link` RỖNG —
  bấm vào không đi đâu cả, và `notify_new_tasks` nuốt lỗi nên không chỗ nào đỏ lên.
  Test canh: `test_nghi_phep_thong_bao_duyet.py`.
- Hai hook duyệt **khác nhau, đừng gọi nhầm**: `useLeaveRequestAction` bấm vào tờ
  ĐƠN (duyệt thẳng, chỉ chạy khi chưa khai luồng — nút này nay chỉ hiện khi
  `approval_instance_id === 0`), còn `useLeaveApprovalDecision` bấm vào PHIÊN DUYỆT.
- ⚠️ **Mục «Bàn giao công việc» LUÔN dựng, kể cả khi rỗng** — ở cả màn chi tiết
  lẫn hộp xác nhận duyệt. Trước 03/09/2026 nó ẩn hẳn khi không có ai, và người
  duyệt không phân biệt được *"người nộp chưa khai ai"* với *"màn hình thiếu mục
  đó"*. Mà **thiếu người bàn giao là lý do trả đơn phổ biến nhất**, tức chính là
  thứ quyết định họ bấm Duyệt hay Trả về — nó phải nói thành lời, không để suy ra
  từ một khoảng trống. Hộp việc duyệt trả kèm `handovers` đúng vì lý do đó.

### HỒ SƠ NHÂN SỰ mở rộng (duoc-CR-314, 08/09/2026 — Đợt 1/4)

Thiết kế + nhật ký từng đợt: `doc/erp/hrm/01-ho-so-nhan-su.md`. Đợt 1 là **nền dữ
liệu backend**, chưa có màn hình nào ở `frontend-v2` (đó là Đợt 2).

- `tab_employee` thêm **30 cột** + `extra_fields` (JSON, trần 20 khóa) và hai bảng
  con `tab_employee_contact` · `tab_employee_family`. Bốn ô phân loại lưu
  **SMALLINT + bộ mã số** ở `employee/constants.py` (R2/QĐ-11); `Employee.status`
  vẫn là mã CHUỖI — ngoại lệ lịch sử B-03, đừng lấy làm mẫu.
- ⚠️ **Khóa quyền mới `employee_sensitive`** (ENTITIES **53 → 54**). Che **15
  trường** (ngày sinh · MST · địa chỉ nhà · ngân hàng · CCCD · số BHXH) ở **tầng
  serializer** — `modules/employee/sensitive.py` là nơi DUY NHẤT khai danh sách
  đó. Ẩn ô trên giao diện là vô nghĩa: API, CSV và trợ lý AI đi đường khác.
  **Cửa GHI cũng che.** Ngoại lệ `self`: ai cũng đọc đủ hồ sơ của chính mình
  (nhánh này chặn `employee_id = 0`, nếu không «chưa gắn ai» khớp mọi hồ sơ).
- ⚠️ **Thêm entity mới vào `ENTITIES` thì phải hỏi: nó có nên rơi vào
  `_SYS_ENTITIES` của `seed.py` không?** `_PUR_MANAGER_PERMS` là
  `{e: ALL for e in ENTITIES if e not in _SYS_ENTITIES}` — quên một dòng là Quản
  lý thu mua tự nhiên có khóa đó. Với `employee_sensitive` nghĩa là đọc được CCCD
  + tài khoản ngân hàng của toàn công ty. Có test canh
  (`test_ho_so_nhan_su_dot1.py`).
- ⚠️ **Hai bảng con CỐ Ý không có khóa phân quyền riêng** — chúng không có màn
  hình riêng (luật «một khóa = một màn hình», CR-157) và phạm vi của chúng không
  diễn đạt được bằng khuôn một-cột của `apply_scope` (bảng con chỉ có
  `employee_id`). Chốt là **hai lớp của hồ sơ CHA**: `get_scoped(Employee, ...)`
  → 404 ngoài phạm vi, rồi `employee_sensitive.read` → 403. Bản thiết kế K2 ghi
  3 khóa mới là chưa tính tới điều đó, xem §5.4.
- ⚠️ **`manager_id` không phải trường hiển thị cho đẹp** — đó là dữ liệu mà
  `APPROVER_DIRECT_MANAGER` (Đợt 3) sẽ đọc. `block_manager_cycle` chặn vòng, kể
  cả vòng dài A→B→C→A: vòng lặp **không nổ lúc lưu hồ sơ**, nó nổ lúc ai đó nộp
  đơn nghỉ phép, ở một tệp không có chữ `employee` nào. Xóa hồ sơ thì gỡ
  `manager_id` của cấp dưới về `0` (id chết → bộ máy duyệt lùi IM LẶNG).
- ⚠️ **Cột mới có `default=` trên model vẫn ra `None` khi bản ghi chưa flush** —
  `default` là mặc định lúc INSERT. Thiếu validator `mode="before"` thì
  `EmployeeOut.model_validate()` ném 26 lỗi cùng lúc và **cả màn danh sách nhân
  sự trả 500** vì một ô chưa ai nhập. Cùng bài học `_gender_none_is_unknown`.
- ⚠️ Trên hệ ĐANG CHẠY, vai trò cũ **không tự có** `employee_sensitive` (D-018):
  tick ở màn Phân quyền, hoặc `SEED_FORCE_SYNC=true` một lần rồi trả về `false`.
  Vai trò mẫu seed sẵn: **`hr_profile`** — "Nhân sự — Hồ sơ nhân viên".
  Kèm theo: người **đang đăng nhập giữ map quyền CŨ** tới khi đăng xuất/đăng
  nhập lại — thêm entity xong mà màn hình vẫn báo thiếu quyền thì đó là lý do,
  đừng đi tìm lỗi ở `require()`.

Màn hình ở `frontend-v2` (duoc-CR-315, Đợt 2/4):
`/hr/employees/:id` nay **5 tab**, tab nhớ ở URL `?tab=`; danh sách có 3 cột mới
+ cảnh báo «Chưa gán» quản lý trực tiếp (K5).

- ⚠️ **`pickWritableProfile` (`hr/schemas/employee-schema.ts`) là chốt chống MẤT
  DỮ LIỆU — đừng gỡ.** Backend che trường nhạy cảm bằng **chuỗi rỗng**, nên
  người có `employee.write` mà thiếu `employee_sensitive.read` mở hồ sơ ra sửa
  số điện thoại rồi bấm Lưu là **PATCH rỗng đè lên số tài khoản ngân hàng thật**
  — không ai biết cho tới kỳ trả lương. Backend **cố ý không tự chặn**: nó không
  phân biệt được "gửi rỗng vì bị che" với "gửi rỗng vì muốn xóa ô đó". Chỗ duy
  nhất biết là nơi dựng form. `SENSITIVE_PROFILE_FIELDS` (13 trường) phải khớp
  `SENSITIVE_FIELDS` của `backend/.../employee/sensitive.py`; lệch là lủng.
- ⚠️ **Ô bị che trông y hệt ô chưa ai nhập.** Luôn dựng `SensitiveFieldsNotice`
  khi `can('employee_sensitive','read')` sai — không có nó thì người dùng đọc hồ
  sơ và tin rằng công ty chưa có số tài khoản ngân hàng của người đó.
- **MỘT form cho cả 4 tab đầu.** Radix hủy mount tab ẩn nhưng react-hook-form giữ
  giá trị trong `useForm` chứ không trong DOM — sửa ở tab này, bấm Lưu ở tab kia
  vẫn gửi đủ. Hai bảng con và hai ảnh CCCD **ngoài** form đó: cửa API riêng, khóa
  quyền riêng, nút Lưu riêng.
- Bộ mã số của hồ sơ gõ tay ở `hr/types/employee-codes.ts` (`gen_status_ts.py`
  chỉ sinh cho bộ mã CHUỖI) — cùng cảnh với `hr/types/leave.ts`. Có test chốt số
  mục, nhưng đổi ở backend vẫn phải nhớ sửa tay bên này.

### Danh mục CHỨC VỤ (duoc-CR-320, 08/09/2026)

Ô «Vị trí / Chức vụ» nay là **ô CHỌN** đọc từ `tab_job_position`; màn quản lý ở
`/hr/job-positions`. Khóa quyền mới **`job_position`** (ENTITIES **54 → 55**,
PUBLIC ở `SCOPE_FIELDS`); seed cấp `read` cho MỌI vai trò vì ô chọn cần nó, sửa
thì chỉ `hr_profile`. Chi tiết: `doc/erp/hrm/01-ho-so-nhan-su.md` §7.7.

- ⚠️ **HAI CỘT CHO MỘT SỰ THẬT.** `tab_employee.position_id` là khóa,
  `tab_employee.position` là **nhãn đã chép** — giữ cột chữ vì mười chỗ đọc
  thẳng nó (bản in YCMH/YCBG, tệp Excel, `core/audit`, trợ lý AI). Toàn hệ chỉ
  có **hai đường ghi** vào cột nhãn, cả hai ở `employee/position_service.py`:
  `sync_label` (lưu hồ sơ) và `propagate_rename` (đổi tên trong danh mục). Thêm
  đường thứ ba là nhãn trôi, và **bản in đưa cho khách ra tên cũ** trong khi màn
  hình hiện tên mới.
- ⚠️ **Luật «khóa = 0 thì xóa nhãn» CHỈ đúng ở đường CẬP NHẬT** (người dùng vừa
  bỏ chọn). Áp cả lúc TẠO thì đường nhập CSV / seed — những nơi chỉ truyền chữ —
  làm hồ sơ **mất chức danh ngay khi ra đời**, im lặng.
- ⚠️ **Chức vụ đã ngừng dùng: chặn gán MỚI, nhưng hồ sơ đang giữ vẫn lưu được.**
  Màn hồ sơ gửi lại mọi ô mỗi lần lưu, nên không có ngoại lệ đó thì người đó
  không sửa nổi ô nào khác cho tới khi ai đi đổi chức vụ của họ.
- ⚠️ Đừng lẫn với **`job_level` (Cấp bậc)** — thang bậc CỐ ĐỊNH bảy mức khai
  trong mã nguồn (`employee/constants.py`), dùng để lọc và làm báo cáo cơ cấu.
  Chức vụ là chức danh cụ thể in trên phiếu, người dùng tự thêm bớt.
- ⚠️ Lọc danh sách nhân sự theo chức vụ đi bằng **`position_id`**, không bằng
  chữ: lọc bằng chữ thì đổi tên là bộ lọc đã lưu trượt sạch, và `contains` khớp
  cả chuỗi con («Phó phòng» lọt vào kết quả tìm «Trưởng phòng»).
- ⚠️ **Danh sách cột của bảng KHÁC danh sách ô nhập** (duoc-CR-321). `sort_order`
  và `department_id` còn dưới DB nhưng **cố ý không lên giao diện**: cột thứ tự
  là khái niệm của người dựng hệ thống (bảng hiện toàn 10·20·130, không chỗ nào
  giải nghĩa), còn «phòng ban thường giữ» không chặn gì cả nên hỏi cũng bằng
  thừa. Ô chọn chức vụ vì thế **phải khai `sort_by=name`** — mặc định của
  `make_crud_router` là `id desc`, tức danh sách tự đổi chỗ mỗi lần có ai thêm
  một dòng.
- ⚠️ **Đếm ngược người giữ đi qua `/api/job-positions/stats`, KHÔNG qua
  serializer** (duoc-CR-322): serializer chạy cho từng dòng nên đếm ở đó là
  N+1. Hai luật ngược nhau, cố ý — **số bày cho người xem thì lọc theo phạm vi**
  (`apply_scope` trên `employee`), **chốt chặn xóa thì đếm toàn công ty** vì đó
  là toàn vẹn dữ liệu; câu chặn nói rõ «trên toàn công ty» để hai số lệch nhau
  không đọc thành lỗi. Thiếu `employee.read` thì backend **không ném 403**, nó
  trả rỗng — giao diện phải tự tắt cột, không thì mọi dòng hiện 0 và người đọc
  tin là chưa ai giữ chức vụ nào.
- ⚠️ **`Employee.avatar` và `User.avatar` là `@property`, không phải cột** — đưa
  vào `with_entities` là `ArgumentError` lúc chạy. Ảnh thật ở `tab_file`, nối
  qua `tab_user.avatar_file_id`, ưu tiên `thumb_url or url`.
- Nút _Thêm chức vụ_ mở **trang riêng** `/hr/job-positions/new`
  (`CrudConfig.createRoute`) chứ không phải hộp thoại — khuôn có sẵn, dùng chung
  với Loại nghỉ · Phòng họp · Ngày lễ · Xe · Tài xế. Lý do không phải form dài
  (4 ô) mà là mỗi ô kéo theo một hệ quả phải đọc TRƯỚC khi gõ, hộp thoại thì
  buộc cắt ngắn cho vừa khung.
- ⚠️ **Hai cột ảnh xếp chồng nói HAI thứ khác nhau**: «Đang giữ» là ảnh của
  NGƯỜI, «Phòng ban đang giữ» là ảnh của PHÒNG BAN (vòng tròn chữ viết tắt tên
  phòng). Bản đầu cột sau xếp gương mặt nhân viên theo phòng và **lặp lại đúng
  nhóm mặt của cột trước trên cùng một dòng** — hai cột nói cùng một điều. Chữ
  viết tắt: tên NGƯỜI lấy hai từ **cuối**, tên PHÒNG lấy hai từ **đầu** (họ Việt
  đứng trước nên phần phân biệt ở cuối; tên phòng đọc xuôi nên ở đầu — lấy hai
  từ cuối thì «Công nghệ thông tin» ra «TT», trùng «Truyền thông»). Cả hai hàm ở
  `shared/utils/name-initials.ts`.
- Trang chi tiết chạy hết bề ngang (`detailMaxWidth: 'max-w-none'`) vì có tab
  **«Người đang giữ»** — bảng nhân sự phân trang thật, kèm ô tìm kiếm và hai ô
  lọc *phòng ban* · *tình trạng*.

⚠️ **BỐN BẪY CỦA BIỂU MẪU, tìm ra bằng cách bấm tay trên trình duyệt** (duoc-CR-317
— áp cho MỌI màn, không riêng nhân sự). Cả bốn im lặng, không test đơn vị nào bắt
được, và ba trong số đó là lỗi có sẵn của khuôn chung:

- **Ô sai ở TAB ĐANG ẨN → bấm Lưu không có gì xảy ra.** Radix hủy mount tab ẩn
  nên `FormMessage` không có chỗ hiện; react-hook-form chặn submit trong im lặng
  tuyệt đối — không toast, không lỗi, không request. Biểu mẫu chia tab **bắt
  buộc** có nhánh `onInvalid` nhảy tới tab chứa ô sai. Mẫu:
  `hr/utils/profile-field-tab.ts` + `form.handleSubmit(onSubmit, onInvalid)`.
- **Nhấn Enter trong ô con nằm trong `<form>` → submit form CHA.** Bảng con có
  nút Lưu riêng thì Enter phải bị `preventDefault`, không thì người dùng gõ dở
  một dòng, nhấn Enter, và hệ thống lưu thứ khác rồi **báo thành công**.
- **Nút mở hộp thoại trong `<form>` phải khai `type="button"`.** Thiếu thì HTML
  mặc định `submit`: bấm «Xóa» là form LƯU bản ghi trước, hộp xác nhận mở sau —
  bấm Hủy thì đã lưu rồi. `shared/ui/delete-confirm-button.tsx` từng thiếu, ảnh
  hưởng ~11 màn chi tiết.
- **`disabled={mutation.isPending}` KHÔNG chặn được bấm đúp.** Nó là state React
  nên chỉ đúng ở lần render sau; bấm 5 lần liền tay ra 5 request và 5 dòng nhật
  ký cho một lần lưu. Chặn bằng `useRef` đổi ngay trong tick, `disabled` chỉ để
  báo hiệu. Khuôn chung còn lỗ này ở nhiều màn.

⚠️ **BA BẪY CỦA BẢNG CÓ BỘ LỌC** (duoc-CR-322 — áp cho MỌI màn danh sách):

- **`id = 0` là một GIÁ TRỊ THẬT, đừng lấy làm mốc «tất cả».** Cột tham chiếu
  bỏ trống (`department_id`, `company_id`, `manager_id`…) lưu `0`, và
  `apply_filters` so khớp CHÍNH XÁC nên `department_id=0` lọc ra đúng nhóm *chưa
  gắn*. Lấy `0` làm sentinel thì nhóm đó thành thứ **duy nhất không lọc ra
  được**, mà nó lại chính là nhóm người ta cần tìm để đi gắn cho đủ. Dùng `-1`.
- **Đổi bộ lọc phải kéo trang về 1** — dùng `usePageResetOnFilterChange`, KHÔNG
  `useEffect(() => setPage(1), [...])`: effect chạy sau khi commit nên lượt
  render đầu vẫn gọi API với số trang cũ (một request thừa vào trang không còn
  tồn tại), và ESLint chặn `setState` trong effect. Theo dõi giá trị tìm kiếm
  **đã hoãn** chứ không theo ô nhập thô, kẻo mỗi ký tự một lần đặt lại trang.
- **Câu «bảng rỗng» phải phân biệt _rỗng vì bộ lọc_ với _rỗng vì chưa có gì_.**
  Một câu chung cho cả hai thì người vừa gõ nhầm một chữ đọc ra "chưa có dữ
  liệu" và tin là vậy.

Bẫy thứ tư nằm ở `frontend-v2/docs/ui/table.md` §4: **`defaultHidden` chỉ áp cho
người chưa từng đụng menu «Cột»** — bảng nhớ bố cục trong `localStorage` và bản
lưu thắng toàn bộ, nên sửa `defaultHidden` xong mà màn hình không đổi thì không
phải mã sai.

⚠️ **CỘT `String(n)` MÀ SCHEMA KHÔNG KHAI `max_length` = LỖI 500, KHÔNG PHẢI
422** (duoc-CR-316 — luật này áp cho MỌI module, không riêng nhân sự). Chuỗi dài
đi thẳng xuống MySQL, và MySQL là chỗ đầu tiên phản đối: người dùng dán nhầm một
đoạn văn bản vào ô là nhận «mã sự cố», quản trị đi tra một lỗi vốn đáng ra là câu
«tối đa n ký tự». Rà 22 trường của hồ sơ nhân sự thì **12 ca trả 500**, trong đó
4 trường có lỗ từ lâu.

- Khai bằng bí danh ở `modules/employee/field_limits.py` (`Str20`, `Str255`…),
  số phải khớp ĐÚNG `String(n)` ở `model.py`.
- ⚠️ **`test/backend` chạy SQLite, và SQLite KHÔNG ép độ dài `VARCHAR`.** Bài
  kiểm nào ghi xuống DB rồi khẳng định là **xanh giả** — đúng lý do lỗ hổng này
  sống lâu vậy. Phải kiểm ở tầng SCHEMA (`pytest.raises(ValidationError)`).
- Cùng họ với nó: cột JSON cần trần **kích thước** chứ không chỉ trần số khóa
  (20 khóa × 2MB = 40MB một bản ghi, MySQL nhận hết); cột ngày cần **dải năm**
  hợp lý (MySQL nhận tới năm 9999, mà `hire_date` năm 0001 là hai nghìn năm
  thâm niên); danh sách con cần **trần số dòng** (`sort_order` SMALLINT tràn ở
  dòng 32768).
- ⚠️ Vòng dò có TRẦN ĐỘ SÂU thì chạm trần phải **chặn**, đừng trả về im lặng —
  "dò không thấy" không phải "không có". `block_manager_cycle` từng bỏ lọt đúng
  kiểu đó, và cái lọt là vòng lặp vô hạn trong bộ máy duyệt.

## Tests

- `test/backend/` — pytest against SQLite in-memory (fixtures in `test/backend/conftest.py`); fast, isolated per function, tests services/serializers/RBAC helpers directly.
- `test/e2e/` — Playwright Python on the host; needs the stack running and demo accounts (`TESTREQ`, `DEMONV`, `DEMOTP`, `DEMO_MANAGER_PURCHASE`, password = code).

## Docs

Requirements, permission design, and naming conventions live in `doc/` (Vietnamese) — index at `doc/README.md`. Permission design detail: `doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`. Progress checklist: `TASKS.md`.

⚠️ **Trước khi đụng vào cấu trúc Sản phẩm, đọc `doc/tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md`.** `tab_product` **là bảng VARIANT (SKU)**, không phải sản phẩm cha — cố ý như vậy. Không có FK nào trỏ vào nó; 7 bảng (YCMH, ĐMH, nhận hàng, tồn kho, luân chuyển kho, lịch sử mua hàng, option khảo sát) nối nhau bằng **chuỗi `product_code`**, nên đó là hạt dữ liệu của cả hệ. Muốn gom nhóm thì thêm tầng cha Ở TRÊN; **cấm** thêm `tab_product_variant` ở dưới, cấm đổi/tái dùng `product_code`, cấm đặt cột giá lên sản phẩm. Xem D-025 trong `change-log.md`.
