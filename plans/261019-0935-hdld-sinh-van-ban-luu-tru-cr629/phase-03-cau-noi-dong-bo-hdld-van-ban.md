# Phase 03 — Cầu nối đồng bộ HĐLĐ → Văn bản + script bù

**Ưu tiên:** P2 · **Trạng thái:** pending · **Effort:** 4h · **Phụ thuộc:** 01
**Sở hữu tệp:** `backend/app/modules/labor_contract/*`, `backend/scripts/backfill_hdld_van_ban_luu_tru.py`, `test/backend/test_hdld_van_ban_luu_tru_dong_bo_cr629.py`

## Context
- Khuôn: `leave/approval_bridge.py:308-373 create_leave_document` (tra loại theo mã, thiếu thì bỏ qua im lặng, ghi ngược `document_id`).
- `document/service.create_document` (`:169`) **tự commit** + `queue_reindex`; `user=None` ⇒ bỏ kiểm cửa thư mục; thư mục rơi về gốc pháp nhân.
- `labor_contract/file_response.py`: `load_bytes`, `store_bytes`, `delete_files_after_commit`, `discard_new_file`.
- `attachment/service.py:47 create_stored_file` (qua `guard_upload` theo `kind`), `:74 delete_stored_file` (không soi `FileLink`) ⇒ **không dùng chung file_id**.
- `generate_service.py:84-106` xóa cứng tệp cũ khi sinh lại / thay bản ký; `service.update` bỏ tệp sinh khi sửa.

## Kiến trúc
Một điểm vào duy nhất, **idempotent**, **best-effort**, gọi SAU khi nghiệp vụ HĐ đã commit:

```python
# labor_contract/document_archive_sync.py (~150 dòng)
def archive_sync(db, contract_id: int, actor_id: int) -> int:   # trả document_id, 0 nếu bỏ qua/lỗi
    try:
        lc = SELECT ... FOR UPDATE populate_existing   (kể cả is_deleted)
        doc = _ensure_document(db, lc, actor_id)      # chưa có → create_document(...); lc.document_id=doc.id; COMMIT ngay
        if doc is None: return 0                       # loại HDLD thiếu / tắt
        _apply_fields(db, lc, doc)                     # tiêu đề, tóm tắt, ngày, trạng thái
        document_archive_files.mirror(db, lc, doc, actor_id)   # commit + dọn tệp cũ sau commit
        return doc.id
    except Exception: db.rollback(); log.exception(...CR-628...); return 0
def soft_delete_archive_of(db, lc, user_id)            # cho delete_all_of — KHÔNG commit
```
`archive_sync` nhận **id** (không nhận object) vì nơi gọi đã commit; tự khóa lại dòng.

### Tạo văn bản (`_ensure_document`)
- `DocType.code == LABOR_CONTRACT_DOC_TYPE and is_active` — không có ⇒ `None`.
- `lc.document_id` đã có nhưng văn bản bị xóa cứng/không tồn tại ⇒ tạo lại (tự lành).
- `DocumentCreate(doc_type_id, company_id=lc.company_id, department_id=lc.department_id or 0, title, summary, content_mode=CONTENT_MODE_FILES)`;
  **không** `owner_employee_id`, **không** `metadata`, `created_by = actor_id`.
- Tiêu đề: `f"HĐLĐ {lc.contract_no or lc.code} — {emp.full_name}"`; tóm tắt: loại HĐ · hiệu lực từ–đến · trạng thái HĐ (+ lý do hủy/chấm dứt). **Cấm** lương/phụ cấp/CCCD/STK.

### Ánh xạ trạng thái (`_apply_fields`, ghi thẳng cột, không qua luồng duyệt)
| HĐLĐ (lưu) | `Document.status` | Ngày |
|---|---|---|
| Nháp (1) | `STATUS_DRAFT` (1) | effective_date=start_date, expire_date=end_date |
| Đã ký (2) | `STATUS_EFFECTIVE` (4) | như trên (Hết hạn = suy ra, không đổi) |
| Đã chấm dứt (4) | `STATUS_EXPIRED` (6) | expire_date=terminated_date |
| Đã hủy (5) | `STATUS_ARCHIVED` (8) | tóm tắt ghi «Đã hủy: <lý do>» |
| HĐ xóa mềm | `STATUS_ARCHIVED` (8) | tóm tắt ghi «Hợp đồng đã xóa ở phân hệ Nhân sự ngày …» |
| Hồ sơ NV xóa cứng (`delete_all_of`) | văn bản `mark_deleted` | — |

Không dùng `STATUS_REVOKED` (kéo theo luật bãi bỏ `revoke_access`).

### Gương tệp (`document_archive_files.py`, ~100 dòng)
- Mong muốn = sha256 của `{generated_file_id, signed_file_id}` khác 0 (đọc `StoredFile`, không tải byte).
- Hiện có = `FileLink(entity="document_version", entity_id=doc.current_version_id)` ⨝ `StoredFile`.
- sha có mà không mong muốn ⇒ gỡ `FileLink` (+ dòng `tab_file`) trong giao dịch; byte trên storage xóa **sau commit** (`delete_files_after_commit`).
- sha mong muốn chưa có ⇒ `load_bytes` gốc → `store_bytes(..., kind=<kind gốc>, category="labor-contract-archive")` → `FileLink(sort_order: docx 0, bản ký 1, created_by=actor)`. Lỗi ⇒ `discard_new_file`.
- Không có `FileLink` nào khác trên phiên bản này được (ghi văn bản bị chặn ở phase 02) ⇒ so sha là đủ, không cần cột mới.

### Chỗ gọi (controller, sau service, trước `_item`)
`create_contract`, `update_contract`, `generate_document`, `upload_signed_file`, `transition_contract`, `delete_contract` → `document_archive_sync.archive_sync(db, row.id, user.id)`.
`service.delete_all_of` → `soft_delete_archive_of` trong cùng giao dịch (trước `db.delete(r)` — sau đó mất liên kết, văn bản sẽ rơi về luật `is_personal`).

### API thêm trường (cộng thêm, không phá)
`LaborContractOut`: `document_id: int`, `can_open_document: bool` = `document_id > 0 and has_perm(profile, "document", "read")` (tính 1 lần cho cả trang).

### Script bù `backend/scripts/backfill_hdld_van_ban_luu_tru.py`
- Duyệt mọi `tab_labor_contract` (kể cả xóa mềm), gọi `archive_sync(db, id, lc.created_by)`; in đếm tạo/đồng bộ/bỏ qua/lỗi.
- `--dry-run` (chỉ đếm HĐ chưa có văn bản), `--soft-delete-all` (cho rollback: xóa mềm mọi văn bản HĐLĐ, đặt `document_id=0`).
- Idempotent: chạy lại không sinh thêm.

## Tệp
- Tạo: `labor_contract/document_archive_sync.py`, `labor_contract/document_archive_files.py`
- Sửa: `labor_contract/controller.py` (6 chỗ gọi), `labor_contract/service.py` (`delete_all_of`), `labor_contract/schema.py`, `labor_contract/serializer.py`
- Tạo: `backend/scripts/backfill_hdld_van_ban_luu_tru.py`, `test/backend/test_hdld_van_ban_luu_tru_dong_bo_cr629.py`

## Test (pytest) — `test_hdld_van_ban_luu_tru_dong_bo_cr629.py`
Dùng `hdld_factory` (`storage`, `client_as`, `grant_all`, `upload_template`, `make_contract`); tự tạo `DocType(code="HDLD", is_personal=True)` (test cũ không có loại ⇒ cầu nối im lặng, đếm storage cũ không đổi).
1. Lập ⇒ `document_id>0`; văn bản loại HDLD, Nháp, `content_mode=2`, company/department = snapshot; `owner_employee_id` rỗng, `meta` rỗng; tiêu đề/tóm tắt KHÔNG chứa số lương/phụ cấp.
2. Thiếu loại HDLD ⇒ lập 201, `document_id=0`; thêm loại rồi sinh tệp ⇒ tự tạo văn bản.
3. `create_document` ném lỗi (monkeypatch) ⇒ lập vẫn 201, `document_id=0`.
4. Sinh tệp ⇒ phiên bản hiện hành có đúng 1 `FileLink`, `file_id ≠ generated_file_id`, cùng sha256.
5. Sinh lại ⇒ vẫn 1 `FileLink`; byte bản sao cũ biến khỏi `storage`.
6. PATCH sửa HĐ nháp ⇒ bản sao docx bị gỡ; tiêu đề/ngày theo giá trị mới.
7. Tải bản ký ⇒ 2 tệp; thay bản ký ⇒ vẫn 2 (bản ký mới).
8. Ký ⇒ `STATUS_EFFECTIVE`; chấm dứt ⇒ `STATUS_EXPIRED` + `expire_date`; hủy ⇒ `STATUS_ARCHIVED` + lý do.
9. Xóa mềm HĐ ⇒ văn bản còn, `STATUS_ARCHIVED`, tệp bản sao còn.
10. Xóa hồ sơ NV (`delete_all_of`) ⇒ văn bản `is_deleted`.
11. Xóa tệp gốc HĐ không đụng bản sao (tách file_id).
12. `archive_sync` gọi 2 lần ⇒ không thêm văn bản / `FileLink` / `tab_file`.
13. Script: `--dry-run` không ghi; chạy thật 2 lần ⇒ mỗi HĐ đúng 1 văn bản.
14. Serializer: `can_open_document` true/false theo `document.read`.

Chạy: `pytest test/backend/test_hdld_van_ban_luu_tru_dong_bo_cr629.py test/backend/test_hdld_hop_dong_api.py test/backend/test_hdld_sinh_tai_tep.py test/backend/test_hdld_khoa_dong_xoa_mem_cr627.py -q`.

## Tiêu chí xong
- 14 test xanh + 3 tệp test HĐLĐ cũ xanh không sửa.
- Thủ công local: lập HĐ → mở `/documents/{id}` thấy văn bản «Nháp», tab Tệp có .docx sau khi sinh.

## Rủi ro
| Rủi ro | K×Ả | Giảm thiểu |
|---|---|---|
| Đồng bộ hỏng lặng lẽ ⇒ lưu trữ thiếu tệp | TB × TB | `log.exception` có mã HĐ; mọi sự kiện sau tự lành; script bù chạy lại được |
| Chép 50MB trong request ⇒ chậm | Thấp × Thấp | ~100 người dùng; chấp nhận; nếu cần dời sang Celery sau |
| Hai người thao tác cùng lúc ⇒ chép trùng | Thấp × Thấp | `FOR UPDATE` dòng HĐ trong `archive_sync`; so sha |
| Văn bản tạo xong nhưng chưa ghi `document_id` (khe giữa 2 commit) | Thấp × TB | Commit `document_id` NGAY sau tạo; khe đó văn bản rơi về luật `is_personal` (chỉ người tạo/`all`) |
| Xóa byte trước commit ⇒ mất tệp | Thấp × Cao | Byte chỉ xóa sau commit (khuôn `delete_files_after_commit`) |

## Bảo mật
- Không nới quyền nào ở HĐLĐ; cầu nối không đọc `employee_sensitive` — chỉ tên NV + mã HĐ vào tiêu đề.
- Tệp bản sao nằm sau `document_version` (PRIVATE_ENTITIES) ⇒ không trả `url` trần.
