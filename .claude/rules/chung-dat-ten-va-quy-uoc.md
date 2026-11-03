# Luật chung: đặt tên và quy ước viết mã

> **Luôn nạp** (tệp không khai `paths:`). Đây là MỘT chỗ duy nhất cho luật dùng chung mọi khu — gom ngày 03/11/2026
> (bao-CR-712) từ `backend/.claude/rules/naming.md`, `frontend-v2/.claude/rules/naming.md`, `doc/v1/chung/NAMING_CONVENTIONS.md`
> (bản V1) và các đoạn quy ước trong `CLAUDE.md`. Luật riêng từng khu vẫn ở `.claude/rules/<khu>-*.md` và
> `frontend-v2/.claude/rules/*.md`; mục lục đủ ở `doc/tai-lieu-ky-thuat/quy-dinh/README.md`.

## Mục lục

1. [Định danh trong mã](#1-định-danh-trong-mã)
2. [Tên tệp và thư mục](#2-tên-tệp-và-thư-mục)
3. [Cơ sở dữ liệu và API](#3-cơ-sở-dữ-liệu-và-api)
4. [Ngôn ngữ chuỗi, chú thích, tài liệu](#4-ngôn-ngữ-chuỗi-chú-thích-tài-liệu)
5. [Cột trạng thái](#5-cột-trạng-thái)
6. [Commit và đẩy mã](#6-commit-và-đẩy-mã)
7. [Bài kiểm](#7-bài-kiểm)

---

## 1. Định danh trong mã

- **Mọi định danh bằng tiếng Anh** — hàm, biến, hằng, lớp, tham số, khóa JSON của API. Không đặt tên tiếng Việt (có dấu
  hay không dấu) cho định danh.
- **Hàm là động từ**, không phải danh từ: hàm là một hành động.

  ```python
  def lay_danh_sach_nhan_vien(): ...   # SAI — tiếng Việt
  def employee_list(): ...             # SAI — danh từ
  def get_employee_list(): ...         # ĐÚNG
  ```
- **Python (backend):** hàm / biến `snake_case`, lớp `PascalCase`, hằng `SCREAMING_SNAKE_CASE`.
- **TypeScript (frontend-v2):** component / type / interface `PascalCase`; hook, hàm, biến `camelCase`; hằng toàn cục /
  cấu hình `SCREAMING_SNAKE_CASE`, hằng cục bộ `camelCase`. Hook bắt đầu bằng `use`.
- Tên dài mà rõ hơn tên ngắn mà khó đoán: đọc tên là biết bên trong làm gì.

## 2. Tên tệp và thư mục

- **Backend:** mỗi phân hệ một thư mục `backend/app/modules/<feature>/` (`snake_case`) gồm `model.py · schema.py ·
  service.py · controller.py` (thêm `serializer.py`, `tasks.py`… khi cần). Dùng chung → `backend/app/core/`. Model mới
  phải khai trong `backend/app/core/all_models.py`.
- **frontend-v2:** mọi tệp `.ts` / `.tsx` là **kebab-case**, đặt theo vai trò của thứ nó xuất ra:
  `employee-list-page.tsx` (trang, nằm trong `pages/`), `use-employees.ts` (hook), `employee-api.ts` (gọi API).
  Một tệp một thứ xuất chính; bài kiểm nằm cạnh tệp nó kiểm (`format-money.test.ts`). Chi tiết riêng v2 (thư mục phân
  hệ, query key, barrel) ở `frontend-v2/.claude/rules/naming.md`.
- **Bài kiểm backend:** `test/backend/test_<chủ đề tiếng Việt không dấu>_<mã CR>.py` (vd `test_so_viec_chay_ngam_cr703.py`).
- **Tài liệu:** chữ thường, không dấu, nối gạch ngang — luật đủ ở `.claude/rules/chung-tai-lieu.md`.

## 3. Cơ sở dữ liệu và API

- Bảng tiền tố `tab_`, số ít, `snake_case` (`tab_purchase_order`); cột `snake_case`; khóa chính `id` BIGINT tự tăng
  (không UUID). Tiền `DECIMAL(18,2)`, số lượng `DECIMAL(18,3)`. Bảng nghiệp vụ mang `created_at / created_by /
  updated_at / updated_by` (AuditMixin) trừ bảng do máy ghi.
- Cột `String(n)` nhận từ người dùng phải có `max_length` ở schema (xem `.claude/rules/backend-input-limits.md`).
- Đổi model thì đi bằng migration Alembic; **cấm** `ALTER` / `INSERT` chữ tiếng Việt thẳng qua `mysql -e` (lỗi mã hóa).
- API REST: `GET /api/<danh-từ-số-nhiều>`, `GET /api/<…>/{id}`, `POST`, `PATCH`, `DELETE`; hành động
  `POST /api/<…>/{id}/approve`. Mọi đường trả phong bì `success(data, message)` → `{success, message, data}`.
- **Mô tả API cho trang `/docs`** (giữ mở trên dev và prod, người chủ chốt 03/11/2026): đường API MỚI hoặc vừa sửa phải
  có **docstring tiếng Việt** (dòng đầu = tóm tắt một câu, hiện ở `/docs`; các dòng sau: quyền, phạm vi, lỗi riêng) và
  router khai `tags=[...]` theo phân hệ. Khai `response_model` khi dữ liệu trả về có schema rõ. Đường cũ thiếu mô tả bổ
  sung dần khi đụng tới. Đồng thời cập nhật `doc/erp/<phan-he>/tai-lieu-ky-thuat/api.md` (luật ở `chung-tai-lieu.md`).

## 4. Ngôn ngữ chuỗi, chú thích, tài liệu

- **Chuỗi người dùng thấy, chú thích, docstring, tài liệu: tiếng Việt.** Đây là công cụ nội bộ công ty Việt; từ nghiệp
  vụ (YCMH, YCBG, ĐMH, NCC, YCTT…) là một phần của đặc tả. Đừng "dịch" chuỗi / chú thích tiếng Việt có sẵn sang tiếng
  Anh. Từ tiếng Anh chỉ giữ khi công ty vẫn gọi bằng từ đó (commit, deploy, migration, API).
- **Không emoji** ở mã, chuỗi, tài liệu, commit.
- **Không dùng ngoặc kép góc** (ký tự U+00AB / U+00BB). Câu lỗi API, chú thích, log dùng nháy thẳng `"…"`; chữ hiển thị
  dạng markdown (tin bot, lời Trợ lý, mô tả công cụ MCP, cẩm nang) dùng **in đậm** / *in nghiêng*. Mã DÒ ký tự đó trong
  chữ người gõ / dữ liệu cũ thì giữ (bao-CR-695).
- Dữ liệu hiển thị dạng chữ trơn (mô tả việc, chuông thông báo) không được chứa markdown.

## 5. Cột trạng thái

Cột mang nghĩa trạng thái / loại / mức / giai đoạn MỚI: **`SMALLINT` + `IntEnum`**, API trả số kèm nhãn, tiếng Việt chỉ ở
tầng hiển thị (luật R2, QĐ-11). Bộ mã khai ở `backend/app/core/status_catalog.py` + `code_sets.py`; bản TypeScript sinh
bằng `backend/scripts/gen_status_ts.py`, **không viết tay danh sách trạng thái** ở giao diện. Ngoại lệ cũ (thu mua dùng
mã chuỗi tiếng Anh, QĐ-9) xem `CLAUDE.md` — không chép ngoại lệ vào mã mới.

## 6. Commit và đẩy mã

- Thông điệp commit mở đầu bằng **mã CR** (`bao-CR-712 …`, `duoc-CR-…`, `ai-CR-…`); không có mã thì `docs(...)` /
  `chore(...)` kèm mã trong thân. Cuối thông điệp: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` (agent).
- **`git add` đúng tệp của mình** — không `git add -A` / `git add .` ở cây dùng chung; kiểm `git status` + grep dấu xung
  đột (`<<<<<<<`) trước MỌI commit.
- **Gộp bằng merge, KHÔNG rebase** nhánh đã đẩy: `git fetch origin erp-v2 && git merge origin/erp-v2` trước khi làm và
  trước mỗi lần đẩy. `erp-v2` = dev (nguồn), `main` = prod.
- Đặt chỗ CR trong `doc/tai-lieu-ky-thuat/change-log-bao.md` (hoặc sổ của dải mình) ngay khi nhận việc; xong ghi mục
  `doc/tai-lieu-ky-thuat/nhat-ky-task.md` bằng câu tiếng Việt trọn vẹn, không dùng chữ *đại ca* / *em*.

## 7. Bài kiểm

- **Chỉ chạy bài kiểm của phần vừa sửa**, theo thư mục / tệp — không quét cả `test/backend` hay full vitest trừ khi được
  bảo rõ hoặc ngay trước deploy.
- Backend: `docker compose exec -T api python -m pytest test/backend/<tệp> -q --timeout=120` (SQLite trong bộ nhớ, không
  đụng DB thật; luôn kèm `--timeout`). frontend-v2: `npm run typecheck` + `npm run lint` cả cây, `npx vitest run
  src/modules/<phân hệ>` (luật đủ ở `frontend-v2/.claude/rules/testing.md`).
- Bài kiểm canh (phạm vi dữ liệu, sổ công cụ AI, bộ mã…) đỏ thì **sửa bảng khai kèm lý do thật**, không nới luật.
- Sửa chuỗi người dùng thấy thì sửa luôn bài kiểm so chuỗi trong cùng commit.
