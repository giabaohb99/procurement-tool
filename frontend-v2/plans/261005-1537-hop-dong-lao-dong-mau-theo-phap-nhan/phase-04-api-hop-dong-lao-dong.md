# Phase 04 — API Hợp đồng lao động

## Context Links
- Khuôn tab con theo người: `employee/work_history_{controller,service,serializer,access}.py` (cờ `can_edit` do BACKEND tính, A9)
- `employee/service.delete_employee` (dọn bảng con ở service), `core/utils.generate_code`, `core/vn_time.vn_today`
- Phase 02 `docx_engine`, `context_builder`; phase 03 `access.py`, `file_response.py`

## Overview
Priority P1. Status done (05/10/2026). CRUD + sinh .docx + tải về + bản scan + chuyển trạng thái.

## Endpoints (khóa `labor_contract`)
| Method | Path | Quyền | Ghi chú |
|---|---|---|---|
| GET | `/api/employees/{eid}/labor-contracts` | read | `apply_scope` + `employee_id == eid`; trả `{items, can_create}`; mỗi item kèm `effective_status`, `can_edit`, `can_generate`, `transitions[]` |
| GET | `/api/employees/{eid}/labor-contract-templates?contract_type=` | create HOẶC write | mẫu `is_active` của **`employee.company_id` hiện tại** (+ loại); chỉ id/name/type |
| POST | `/api/employees/{eid}/labor-contracts` | create | Employee phải tồn tại & `company_id > 0`; snapshot company/department; mặc định `job_title = employee.position`, `work_location = employee.work_location`; `ensure_created_in_scope` |
| GET | `/api/labor-contracts/{id}` | read | `get_scoped` |
| PATCH | `/api/labor-contracts/{id}` | write | chỉ khi DRAFT (409 khác) |
| DELETE | `/api/labor-contracts/{id}` | delete | chỉ DRAFT/CANCELLED; xóa kèm 2 tệp |
| POST | `/api/labor-contracts/{id}/generate` | write | chỉ DRAFT; `template_id` (body) phải: active, `company_id == contract.company_id`, `contract_type` khớp; sinh lại → xóa tệp cũ sau commit |
| GET | `/api/labor-contracts/{id}/document` | **print** + phạm vi read | stream .docx; tên `HDLD-{so}-{ho_ten}.docx` |
| PUT | `/api/labor-contracts/{id}/signed-file` | write | multipart, kind `labor_contract_signed`; DRAFT/SIGNED |
| GET | `/api/labor-contracts/{id}/signed-file` | read | stream |
| POST | `/api/labor-contracts/{id}/transition` | write | `{to_status, date?, reason?}` |

## Luật trạng thái (`labor_contract/rules.py`, thuần, test bảng)
| Từ → Đến | Điều kiện |
|---|---|
| DRAFT → SIGNED | KHÔNG bắt buộc có tệp (đại ca chốt 05/10/2026); `date` = sign_date bắt buộc |
| DRAFT → CANCELLED | `reason` bắt buộc |
| SIGNED → TERMINATED | `date` = terminated_date ≥ start_date; `reason` bắt buộc |
| khác | 409 |
`effective_status = EXPIRED` khi SIGNED và `end_date < vn_today()`; vẫn TERMINATE được.

## Ràng buộc dữ liệu (schema + rules, backend là chuẩn)
- `contract_type` ∈ enum; `start_date` bắt buộc; `end_date ≥ start_date`; loại ∈ `REQUIRES_END_DATE` → bắt buộc end; INDEFINITE → end phải rỗng.
- Tiền: `0 ≤ x ≤ 10^12`, số nguyên. `insurance_salary` mặc định = `base_salary` nếu bỏ trống? → **không**, để 0 (tránh đoán).
- `max_length` cho mọi chuỗi (contract_no 50, job_title 100, work_location 255, note/allowance_note/terminate_reason 500).
- `contract_no` trùng trong cùng `company_id` (khác HĐ CANCELLED) → 400.

## Key Insights
- `context_builder` đọc model THÔ (không qua serializer che `employee_sensitive`): người có `labor_contract.print` cầm bản HĐ có CCCD/STK — đó là bản chất của HĐLĐ; ghi rõ trong comment + tài liệu quyền.
- Đơn vị lập HĐ = pháp nhân của NV **lúc tạo**. NV đổi pháp nhân sau đó: HĐ cũ giữ pháp nhân cũ; ô chọn mẫu khi sinh lại dùng `contract.company_id` (không phải company hiện tại) — tránh HĐ pháp nhân A in tiêu đề pháp nhân B.
- Hồ sơ bị xóa: `delete_employee` **chặn 409** nếu còn HĐ không phải DRAFT/CANCELLED (chứng từ pháp lý); DRAFT/CANCELLED thì dọn kèm tệp.
- Audit: `create`/`update`/`delete`; chuyển trạng thái dùng `document_status`; sinh tệp dùng `update` + message «Sinh tệp hợp đồng từ mẫu …» (không mở mã mới trừ khi cần — khai ở `action_catalog.py`).

## Related Code Files
- Create (`backend/app/modules/labor_contract/`): `schema.py`, `rules.py`, `serializer.py`, `service.py`, `generate_service.py`, `signed_file_service.py`, `controller.py`; tests `test/backend/test_hdld_luat_trang_thai.py`, `test_hdld_hop_dong_api.py`, `test_hdld_sinh_tai_tep.py`
- Modify: `backend/app/main.py` (include TRƯỚC `employee_router` vì chung tiền tố `/api/employees`), `backend/app/modules/employee/service.py::delete_employee`

## Implementation Steps
1. `rules.py` + test bảng chuyển trạng thái/ràng buộc ngày.
2. Schema/serializer (cờ backend tính; tên pháp nhân/phòng gom 1 truy vấn).
3. Service CRUD + `generate_service` (load mẫu → `download_bytes` → `render` → `create_stored_file(BytesIO, kind="labor_contract_docx", category="labor-contract")`).
4. Signed file service; controller; wire `main.py`; chặn ở `delete_employee`.
5. Test: ngoài phạm vi → 404 ở mọi đường `{id}`; tạo cho NV pháp nhân ngoài phạm vi → 403; sinh với mẫu pháp nhân khác → 400; sinh khi SIGNED → 409; tải `document` thiếu `print` → 403; sinh lại xóa tệp cũ; `delete_employee` có HĐ SIGNED → 409; `effective_status` EXPIRED theo ngày truyền vào.

## Todo
- [x] rules + test · [x] schema/serializer · [x] service/generate/signed · [x] controller + main.py · [x] delete_employee guard · [x] test API

## Success Criteria
3 tệp test xanh + `test_qua_trinh*` & `test_ho_so_nhan_su_dot1.py` vẫn xanh (đụng `delete_employee`).

## Risk Assessment
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Route `/api/employees/{eid}/labor-contracts` bị `employee_router` nuốt | Trung×Trung | include trước, test gọi thật |
| Render lỗi lúc sinh dù mẫu đã kiểm (dữ liệu lạ) | Thấp×Trung | bắt Exception → 422 «Mẫu không sinh được: …», không 500 |
| Hai người sinh cùng lúc | Thấp×Thấp | `with_for_update` dòng HĐ trong generate |

## Security
`require()` + `get_scoped` mọi đường `{id}`; tải bản sinh đòi `print`; không trả `url`/`file_key`; lương chỉ trong payload của khóa `labor_contract`.

## Next
Phase 06.
