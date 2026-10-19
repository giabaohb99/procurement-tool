# Phase 01 — Nền: cột, migration, loại văn bản HDLD, seed

**Ưu tiên:** P2 · **Trạng thái:** pending · **Effort:** 1.5h · **Phụ thuộc:** —

## Context
- `backend/app/modules/labor_contract/model.py:20-58` (FK mềm, `SoftDeleteMixin`)
- `backend/app/seed_data/document_phase1.py:14-44` (`_doc_type`), `:101` (GNP, `is_personal=True`)
- `backend/app/seed.py:1181` `seed_document_phase1` — insert-only theo `code`, gọi ở cả `seed_prod.py:94`
- `backend/app/modules/document/type_metadata.py:25` `LEAVE_DOC_TYPE = "GNP"` (khuôn hằng)
- Head alembic hiện tại: `grp14` (`grp14_so_thay_doi_bot.py`) — **chạy `alembic heads` xác nhận lại**.
- Memory repo: autogenerate trôi ~650 dòng ⇒ **viết tay** migration.

## Yêu cầu
- `tab_labor_contract.document_id` BIGINT NOT NULL default 0 + index (subquery `IN/NOT IN` của luật đọc dùng cột này).
- Loại văn bản `HDLD` «Hợp đồng lao động», nhóm `C`, `is_personal=True`, `needs_signature=False`, `needs_approval=False`, `number_when=2` (không bao giờ cấp số).
- Hằng `LABOR_CONTRACT_DOC_TYPE = "HDLD"` — một chỗ khai, hai phía (document + labor_contract) import.
- Vai trò mẫu `hr_profile` thêm `"document": (["read"], "own")` (xem Kiến trúc).

## Kiến trúc
- Vì sao `hr_profile` cần `document.read` phạm vi `own`: lớp 1 của **danh sách văn bản** (`require("document","read")`) và của **tải tệp** (`attachment/controller._check` → `user_has_permission(document, read)`) chặn người không có vai trò nào ở Văn bản. Phạm vi `own` (= `created_by`) không mở thêm văn bản thường nào; bản lưu trữ HĐLĐ mở qua nhánh riêng ở phase 02. Hệ đang chạy **không tự có** (D-018) ⇒ ghi chú triển khai phase 05.
- `document` KHÔNG thêm vào `_SYS_ENTITIES` (không đổi hành vi vai trò khác).

## Tệp
- Sửa: `backend/app/modules/labor_contract/model.py` (+`document_id`, comment FK mềm tới `tab_document`)
- Sửa: `backend/app/modules/document/type_metadata.py` (+`LABOR_CONTRACT_DOC_TYPE`)
- Sửa: `backend/app/seed_data/document_phase1.py` (`_doc_type` thêm kwarg `needs_approval: bool = True`; thêm dòng `HDLD`)
- Sửa: `backend/app/seed.py` (`STD_ROLES["hr_profile"]["perms"]` +`document`)
- Tạo: `backend/migrations/versions/lbrct02_hdld_van_ban_luu_tru.py`

## Migration (viết tay)
```python
revision = "lbrct02"; down_revision = "<head hiện tại, vd grp14>"
def upgrade():
    op.add_column("tab_labor_contract",
        sa.Column("document_id", sa.BigInteger(), nullable=False, server_default="0"))
    op.create_index("ix_labor_contract_document", "tab_labor_contract", ["document_id"])
def downgrade():
    op.drop_index("ix_labor_contract_document", table_name="tab_labor_contract")
    op.drop_column("tab_labor_contract", "document_id")
```
Không backfill, không chèn `tab_doc_type` (seed lo). Không đụng FULLTEXT ⇒ không cần `innodb_ft_enable_stopword`.

## Các bước
1. `alembic heads` lấy head; viết migration như trên.
2. Thêm cột vào model (cùng `__table_args__` thêm `Index("ix_labor_contract_document", "document_id")`).
3. Hằng + seed loại + kwarg `needs_approval`.
4. Seed `hr_profile.document`.
5. `docker compose exec api alembic upgrade head`; `alembic check`/autogenerate thử ⇒ **không** được sinh thêm diff cho bảng này (rồi xóa tệp thử).

## Todo
- [ ] migration `lbrct02` + upgrade/downgrade chạy được trên MySQL local
- [ ] model + index khớp migration
- [ ] `LABOR_CONTRACT_DOC_TYPE`
- [ ] seed `HDLD` insert-only, `is_personal=True`
- [ ] `hr_profile` +`document.read own`

## Tiêu chí xong
- `alembic upgrade head` rồi `downgrade -1` rồi `upgrade head` sạch.
- Chạy `python -m app.seed` 2 lần: đúng 1 dòng `tab_doc_type.code='HDLD'`; sửa tên loại trên UI rồi seed lại ⇒ tên giữ nguyên.
- Test cũ HĐLĐ xanh: `pytest test/backend/test_hdld_hop_dong_api.py test/backend/test_hdld_nen_du_lieu.py -q`.

## Rủi ro
| Rủi ro | K.năng × Ả.hưởng | Giảm thiểu |
|---|---|---|
| Môi trường đã có loại mã `HDLD` do người dùng tự tạo (nghĩa khác) | Thấp × TB | Seed bỏ qua theo mã ⇒ cầu nối dùng loại đó; phase 05 kiểm `SELECT * FROM tab_doc_type WHERE code='HDLD'` trên prod trước deploy |
| Down_revision sai head ⇒ 2 head | TB × Cao | Bước 1 bắt buộc `alembic heads`; CI pytest không bắt được |

## Bảo mật
- `document.read own` không mở văn bản của người khác (scope `owner`=`created_by`, `core/scoping.py:73`).
