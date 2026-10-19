# Phase 02 — Luật đọc bản lưu trữ ở phân hệ Văn bản

**Ưu tiên:** P1 (rò lương/CCCD/STK nếu sai) · **Trạng thái:** pending · **Effort:** 3h · **Phụ thuộc:** 01
**Sở hữu tệp:** `backend/app/modules/document/*`, `test/backend/test_hdld_van_ban_luu_tru_quyen_xem_cr628.py`

## Context
- `document/access_service.py` — `visible_condition` (~:202-284), `can` (~:347-440); luật `is_personal` KHÔNG đủ (mở cho `owner_employee_id`/người tạo/phạm vi `all` của `document`).
- `core/scoping.scope_condition` (`:802`) — `None` = tất cả, `false()` = không gì; KHÔNG tự lọc xóa mềm.
- `.claude/rules/document-folders-search.md` — mọi số đếm/bảng/tìm đi qua `visible_condition`; `tab_document_search` là dẫn xuất.

## Luật (thiết kế)
Văn bản D là **bản lưu trữ HĐLĐ** ⇔ ∃ `tab_labor_contract` L (kể cả L đã xóa mềm) với `L.document_id = D.id`.
- **Đọc** D ⇔ người dùng có `labor_contract.read` VÀ L nằm trong `scope_condition(LaborContract, "labor_contract", user, profile, "read")`. Hết.
- Không tính: phạm vi `document` (kể cả `all`/admin), chia đích danh, CẤM, sổ, đang/đã duyệt, phạm vi áp dụng, clone, chủ/người tạo.
- **Ghi/xóa** D: luôn `False` (bản lưu trữ chỉ đọc; mọi thay đổi đi từ Nhân sự).
- Thao tác **tạo văn bản mới từ D** dù chỉ cần quyền đọc (sao chép, clone, trích, ký) ⇒ 409.
- Người dùng tự tạo / đổi loại sang `HDLD` ở Văn bản ⇒ 400 «Loại này chỉ sinh từ phân hệ Nhân sự».
- D không vào chỉ mục toàn văn (loại `HDLD` HOẶC có liên kết — hai điều kiện, phòng đổi mã loại / chạy đua lúc tạo).

## Kiến trúc — module mới `document/labor_contract_archive_access.py` (~110 dòng)
```python
def archive_ids():                      # select(LaborContract.document_id).where(document_id > 0)
def readable_archive_ids(user, profile) # None nếu thiếu labor_contract.read; else select(...) + scope_condition
def wrap_visible(direct, user, profile, action):
    normal = ~Document.id.in_(archive_ids())  AND direct (nếu direct không None)
    if action != "read": return normal
    r = readable_archive_ids(...);  return normal if r is None else or_(normal, Document.id.in_(r))
def contract_of(db, doc) -> LaborContract | None   # 1 truy vấn, KHÔNG lọc is_deleted
def can_read(db, lc, user, profile) -> bool         # has_perm + scope_condition hỏi lại DB
def is_archive_document(db, doc) -> bool             # loại HDLD hoặc contract_of
def ensure_not_archive(db, doc)                      # 409 cho thao tác dẫn xuất
def ensure_not_system_type(db, doc_type_id)          # 400 khi người dùng chọn loại HDLD
```
Import `LaborContract` **cục bộ trong hàm** (tránh vòng import document ↔ labor_contract).
`has_perm` dùng lại `labor_contract/access.has_perm` (DRY).

### Chỗ cắm (mọi đường đọc đã liệt kê)
| Đường đọc | Đi qua | Xử lý |
|---|---|---|
| Danh sách / xuất Excel (`controller._list_query`, `export.py`) | `visible_condition` | `wrap_visible` cuối `visible_condition` |
| Chi tiết, phiên bản, nội dung, `/permissions`, `/access` GET, export docx (`controller._load`) | `can()` | nhánh đầu `can()` |
| Tab Tệp `GET /documents/{id}/attachments` (`files_controller`) | `_load` → `can()` | tự phủ |
| Tải/xem/preview tệp `/api/attachments/{link}/*` | `core/attachment_scope._ensure_document` → `ensure_can` | tự phủ (lớp 1 vẫn đòi `document.read` — phase 01 seed) |
| Tìm toàn văn (`search_service`) | `visible_condition` + chỉ mục | phủ + **loại khỏi chỉ mục** ở `search_index_service.reindex` |
| Cây/thư mục (`doc_catalog/folder_tree_service`, `folder_free_root_service`, `folder_link_bulk_service`, `folder_document_link_controller`, `book_service`) | `visible_condition`/`ensure_can` | tự phủ |
| Tổng quan, báo cáo (`dashboard_service`, `report_service`, `approval/report_service`, `legacy_pending_approval`) | `visible_condition` | tự phủ |
| Trợ lý AI (`assistant/tools/document_tool.py:251,334,438`) | `visible_condition` + `can()` | tự phủ |
| Ô chọn văn bản đích của quan hệ (`link_service.allowed_targets`) | **KHÔNG lọc quyền** (lỗ cũ) | thêm `~Document.id.in_(archive_ids())` — HĐ Đã ký = `STATUS_EFFECTIVE` ∈ `ALIVE_STATUSES` sẽ lộ tiêu đề |
| Cây quan hệ (`link_serializer._children/_clone_children`) | không lọc | D không thể là nguồn quan hệ/clone (ghi bị chặn) ⇒ không xuất hiện |
| Sao chép `POST /{id}/copy`, clone `clone_controller:98`, trích `link_controller:235`, ký `signature_controller:62` | chỉ `read` | `ensure_not_archive` |

⚠️ Hệ quả: `visible_condition` **không còn trả `None`** (luôn có vế `NOT IN archive`). Mọi nơi gọi đã viết `if visible is not None: filter(...)` ⇒ đúng; rà lại 21 chỗ bằng grep, đặc biệt chỗ nào dùng `None` làm tín hiệu «thấy tất cả» cho việc khác (vd `has_visible_clone`, `report_service` Q5.3).

## Tệp
- Tạo: `backend/app/modules/document/labor_contract_archive_access.py`
- Sửa: `document/access_service.py` (2 chỗ: cuối `visible_condition`; đầu `can()` — trước cả lần đệ quy `read`)
- Sửa: `document/search_index_service.py` (`reindex`: archive ⇒ xóa dòng chỉ mục, trả `None`)
- Sửa: `document/link_service.py` (`allowed_targets`)
- Sửa: `document/controller.py` (POST `""` + PATCH: `ensure_not_system_type`; POST `/copy`: `ensure_not_archive`)
- Sửa: `document/clone_controller.py`, `document/link_controller.py`, `document/signature_controller.py` (`ensure_not_archive`)
- Tạo: `test/backend/test_hdld_van_ban_luu_tru_quyen_xem_cr628.py`

## Các bước
1. Viết module mới + test đơn vị luật trước (TDD).
2. Cắm vào `visible_condition` (`return wrap_visible(direct, user, profile, action)`) và `can()`:
   `lc = contract_of(db, doc); if lc is not None: return action == "read" and can_read(db, lc, user, profile)`.
3. `reindex`: `if doc is None or doc.is_deleted or is_archive_document(db, doc): xóa dòng`.
4. `allowed_targets`, 4 endpoint dẫn xuất, 2 endpoint tạo/sửa loại.
5. Grep `visible_condition(` rà nơi coi `None` là tín hiệu.

## Test (pytest, SQLite) — `test_hdld_van_ban_luu_tru_quyen_xem_cr628.py`
Dựng: 2 pháp nhân A/B; loại `HDLD`; HĐ của NV ở A có `document_id` → văn bản D.
1. HR `labor_contract.read` phạm vi `company` A ⇒ thấy D ở danh sách + `can(read)`; `can(write/delete)` = False.
2. HR phạm vi `company` B ⇒ không thấy, `ensure_can` 404.
3. Chính người lao động (có `document.read` own + `owner`) ⇒ không thấy (kể cả khi `owner_employee_id` bị gán tay).
4. Văn thư `document.read` phạm vi `company` A và cả `all` (admin không có `labor_contract`) ⇒ không thấy.
5. Dòng chia đích danh CHO PHÉP văn thư trên D ⇒ vẫn không thấy; thành viên sổ ⇒ không thấy.
6. Tìm: `search_service` với từ khóa = tên NV/mã HĐ ⇒ văn thư 0 kết quả; `tab_document_search` không có dòng D (bật `DOCUMENT_SEARCH_INDEX_SYNC`).
7. Tải tệp `/api/attachments/{link}/download` của D: văn thư 404, HR 200.
8. Tổng quan (`dashboard_service`) + cây thư mục: số đếm của văn thư không tính D.
9. Trợ lý AI tool tìm văn bản: văn thư không ra D.
10. `allowed_targets` không chứa D (D ở `STATUS_EFFECTIVE`).
11. Sao chép / clone / trích / ký trên D ⇒ 409; POST tạo văn bản loại `HDLD` ⇒ 400; PATCH đổi loại sang `HDLD` ⇒ 400.
12. HĐ xóa mềm ⇒ HR vẫn đọc được D (lưu trữ), văn thư vẫn không.
13. Văn bản thường cùng pháp nhân không đổi hành vi (hồi quy: chạy `test_van_ban_ca_nhan_ai_thay_duoc.py` + bộ quyền văn bản hiện có).

Chạy: `docker compose exec -T api python -m pytest test/backend/test_hdld_van_ban_luu_tru_quyen_xem_cr628.py test/backend/test_van_ban_ca_nhan_ai_thay_duoc.py -q` + các test `test_van_ban_*quyen*`/`*tim_kiem*` liên quan (chọn theo grep, không quét cả thư mục).

## Tiêu chí xong
- 13 nhóm test xanh; test văn bản hiện có liên quan xanh.
- Grep: không còn đường đọc `Document` phía người dùng nào bỏ qua `visible_condition`/`can()` ngoài các chỗ đã nêu.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| Sót một đường đọc ⇒ rò lương/CCCD | TB × **Cao** | Bảng trên + grep `query(Document`; tiêu đề/tóm tắt KHÔNG chứa lương (phase 03) ⇒ rò tiêu đề chỉ lộ tên + mã HĐ; tệp đi qua `can()` |
| Nơi gọi coi `visible_condition() is None` = thấy tất cả | TB × TB | Bước 5 rà từng chỗ; test 8 |
| `can()` thêm 1 truy vấn/lần ⇒ vòng lặp `document_tool` chậm | Thấp × Thấp | Chấp nhận (≤ vài chục văn bản/lần) |
| NOT IN subquery chậm | Thấp × Thấp | Bảng HĐ nhỏ + index phase 01 |

## Bảo mật
- 404 (không 403) khi không đọc được — giữ K03.
- Admin không có `labor_contract.read` cũng KHÔNG thấy — đúng ý «Chỉ Nhân sự»; admin seed có `labor_contract` nên vẫn thấy.
