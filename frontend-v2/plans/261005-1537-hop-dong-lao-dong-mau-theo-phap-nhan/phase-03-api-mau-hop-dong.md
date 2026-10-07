# Phase 03 — API Mẫu hợp đồng

## Context Links
- Khuôn CRUD tay: `backend/app/modules/document/template_{controller,service,schema}.py`
- Tải tệp: `attachment/service.create_stored_file / delete_stored_file`, `storage.download_bytes`
- Phản hồi docx: `document/controller.py` ~L750 (`filename*=UTF-8''{quote(name)}`)
- Phạm vi: `core/scoping.apply_scope / get_scoped`; nhật ký `core/audit.record` + `core/action_catalog.py`

## Overview
Priority P1. Status done (05/10/2026). CRUD mẫu theo pháp nhân + tải lên/thay/tải về tệp + danh mục biến.

## Endpoints (`/api/labor-contract-templates`, khóa `labor_contract_template`)
| Method | Path | Quyền | Ghi chú |
|---|---|---|---|
| GET | `/placeholders` | đăng nhập + (`labor_contract_template.read` HOẶC `labor_contract.create`) | trả `PLACEHOLDERS` (key/label/group/example) |
| GET | `` | read | `apply_scope`; lọc `company_id`, `contract_type`, `is_active`, `q`; phân trang |
| GET | `/{id}` | read | `get_scoped` → 404 |
| POST | `` (multipart: file, name, company_id, contract_type, note) | create | `inspect_template` → 422 `{unknown:[...]}`; lưu tệp kind `labor_contract_template`; kiểm row mới nằm trong phạm vi create (xem dưới) |
| PATCH | `/{id}` | write | name, note, contract_type, is_active (KHÔNG đổi company_id) |
| PUT | `/{id}/file` | write | thay tệp, kiểm lại; xóa tệp cũ SAU khi commit tệp mới |
| GET | `/{id}/file` | read | stream bytes, không trả `url` |
| DELETE | `/{id}` | delete | 409 nếu có HĐ tham chiếu `template_id` → gợi ý «Ngừng dùng» |

## Key Insights
- **Kiểm phạm vi lúc TẠO**: chưa có dòng thì `get_scoped` không hỏi được ⇒ `flush()` rồi `get_scoped(db, Model, entity, row.id, user, profile, "create")`; `None` → rollback + 403 «Pháp nhân ngoài phạm vi của bạn». Tách thành helper dùng chung với phase 04 (`labor_contract/access.py::ensure_created_in_scope`).
- `company_id` phải tồn tại & `is_active`; `contract_type` ∈ enum (0 = sai → 422).
- HĐ đã sinh giữ bản chụp riêng ⇒ thay/xóa mẫu không đụng HĐ cũ.
- Trùng tên trong cùng pháp nhân → 400 rõ câu (UniqueConstraint là lưới cuối).

## Requirements
- Schema `max_length` khớp cột (name 200, note 500); `extra="forbid"`.
- Serializer trả: id, company_id, company_name, contract_type, name, note, original_filename, file_size, placeholders, is_active, created_at/by_name, `contract_count` (đếm GOM 1 truy vấn `GROUP BY template_id` cho cả trang — không N+1).
- Audit: `create`/`update`/`delete` (mã có sẵn trong `action_catalog`).

## Related Code Files
- Create: `backend/app/modules/labor_contract/template_schema.py`, `template_service.py`, `template_controller.py`, `access.py`, `file_response.py` (helper stream bytes + Content-Disposition, dùng chung phase 04), `test/backend/test_hdld_mau_hop_dong_api.py`
- Modify: `backend/app/main.py` (include router — chỉ phase này và phase 04 sửa, chạy TUẦN TỰ)

## Implementation Steps
1. `access.py`: `ensure_created_in_scope`, `get_or_404_scoped`.
2. Service: create (guard → inspect → store → row), replace_file, update_meta, delete (đếm tham chiếu), list.
3. Controller + router; đăng ở `main.py`.
4. Test (SQLite, mock `storage.upload_fileobj/download_bytes` ở tầng `core.storage` — hoặc dùng storage local của conftest nếu có): phạm vi company A không thấy/không tải được mẫu company B (404); tạo mẫu cho pháp nhân ngoài phạm vi → 403; biến lạ → 422 kèm tên; xóa mẫu đang được dùng → 409; tải tệp thiếu quyền → 403.

## Todo
- [x] access helpers · [x] service · [x] controller + main.py · [x] test API

## Success Criteria
`pytest test/backend/test_hdld_mau_hop_dong_api.py -q` xanh; Swagger `/docs` thấy 8 đường.

## Risk Assessment
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Lộ tệp qua `url` storage | Trung×Trung | Không serialize `url`/`file_key`; chỉ stream |
| Tệp mồ côi khi lỗi giữa chừng | Trung×Thấp | Upload trước, lỗi DB thì `delete_key` trong `except`; xóa tệp cũ sau commit |

## Security
2 lớp: `require()` + `apply_scope/get_scoped`; trần 10MB; tên tệp tải về chỉ từ dữ liệu DB, đã `quote()` (chặn header injection).

## Next
Phase 04 (BE) ∥ Phase 05 (FE).
