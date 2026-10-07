# Phase 01 — Nền dữ liệu, bộ mã, quyền

## Context Links
- `CLAUDE.md` (R2/QĐ-11, SCOPE_FIELDS/B-07, all_models) · `.claude/rules/hr-employee-profile.md` (bẫy `_SYS_ENTITIES`, D-018) · `.claude/rules/backend-input-limits.md`
- Khuôn: `backend/app/core/hr_work_history_codes.py`, `employee/work_history_model.py` (FK mềm), migration `wkhist01_*`
- Memory: autogenerate trôi ~650 dòng → cắt tay

## Overview
Priority P1 (chặn mọi phase). Status pending. Tạo 2 bảng, 2 bộ mã SMALLINT, 2 khóa quyền + phạm vi, seed, đồng bộ ENTITIES FE.

## Key Insights
- `gen_status_ts.py` chỉ sinh bộ mã CHUỖI → đăng ký `Code(str(int(k)), label)` như `WORK_EVENT_TYPE_SET`; FE tra `labelOf(SET, String(n))`.
- Thêm entity vào `ENTITIES` mà quên `SCOPE_FIELDS` → test B-07 đỏ; quên `_SYS_ENTITIES` → Quản lý thu mua tự có quyền xem LƯƠNG toàn công ty.
- `test_pham_vi_khai_du_b07.py:189` ghim `len(ENTITIES) == 72` → 74. `test_dong_bo_giao_dien_v2.py` so ENTITIES FE/BE.
- Hồ sơ cha dùng FK mềm (không `ForeignKey`), dọn ở service.

## Requirements
**Bộ mã** `backend/app/core/labor_contract_codes.py` (stdlib-only, số đã cấp không tái dùng):
- `LaborContractType`: 1 PROBATION «Thử việc» · 2 FIXED_TERM «Xác định thời hạn» · 3 INDEFINITE «Không xác định thời hạn» · 4 SERVICE «Khoán việc / dịch vụ» · 5 COLLABORATOR «Cộng tác viên» · 9 OTHER «Khác». `REQUIRES_END_DATE = {1, 2, 4, 5}`; `INDEFINITE` cấm `end_date`.
- `LaborContractStatus`: 1 DRAFT «Nháp» · 2 SIGNED «Đã ký – hiệu lực» · 3 EXPIRED «Hết hạn» (SUY RA, không ghi DB) · 4 TERMINATED «Đã chấm dứt / thanh lý» · 5 CANCELLED «Đã hủy».
- `register(CodeSet("labor_contract_type", ...))`, `register(CodeSet("labor_contract_status", ...))`; import trong `core/code_sets.py`.

**Bảng `tab_labor_contract_template`** (`Base, AuditMixin`): `company_id BigInteger` (index) · `contract_type SmallInteger` · `name String(200)` · `note String(500)` · `file_id BigInteger` (→ `tab_file`) · `original_filename String(255)` · `placeholders JSON` (danh sách biến phát hiện lúc tải lên) · `is_active Boolean`. `UniqueConstraint(company_id, name)`; `Index(company_id, contract_type, is_active)`.

**Bảng `tab_labor_contract`** (`Base, AuditMixin`): `code String(25) unique` (`generate_code(..., "HDLD")`) · `contract_no String(50)` (số in trên HĐ, rỗng → dùng `code`) · `employee_id BigInteger` · `company_id BigInteger` · `department_id BigInteger` (snapshot cho phạm vi) · `template_id BigInteger default 0` · `contract_type SmallInteger` · `status SmallInteger default 1` · `sign_date/start_date/end_date Date` (start NOT NULL) · `job_title String(100)` (khớp `Employee.position`) · `work_location String(255)` · `base_salary BigInteger` · `insurance_salary BigInteger` · `allowance BigInteger` · `allowance_note String(500)` · `note String(500)` · `generated_file_id BigInteger default 0` · `generated_at DateTime` · `generated_by BigInteger` · `signed_file_id BigInteger default 0` · `terminated_date Date` · `terminate_reason String(500)`. `Index(employee_id, start_date)`, `Index(company_id, status)`.
- Tiền = **đồng nguyên** (BigInteger), không lẻ.

**Quyền** `core/permissions.py`: thêm `"labor_contract"`, `"labor_contract_template"` + nhãn («Hợp đồng lao động (có lương)», «Mẫu hợp đồng lao động»), comment lý do tách khóa.
**Phạm vi** `core/scoping.py`:
- `"labor_contract": {"company": "company_id", "dept_id": "department_id", "self": "employee_id", "owner": "created_by"}`
- `"labor_contract_template": {"company": "company_id", "owner": "created_by"}`
**Seed** `seed.py`: 2 khóa vào `_SYS_ENTITIES`; `hr_profile` nhận `labor_contract` (read/create/write/delete/print, all) + `labor_contract_template` (read/create/write/delete, all). Kiểm `seed_prod.py` có cùng nguồn STD_ROLES.
**FE** `frontend-v2/src/core/authorization/permission-types.ts` (ENTITIES) + `modules/system/config/permission-groups.ts` (nhóm Nhân sự).

## Related Code Files
- Create: `backend/app/core/labor_contract_codes.py`, `backend/app/modules/labor_contract/__init__.py`, `.../labor_contract/model.py`, `.../labor_contract/template_model.py`, `backend/migrations/versions/lbrct01_hop_dong_lao_dong.py`
- Modify: `backend/app/core/code_sets.py`, `core/all_models.py`, `core/permissions.py`, `core/scoping.py`, `app/seed.py`, `test/backend/test_pham_vi_khai_du_b07.py` (72→74), `frontend-v2/src/core/authorization/permission-types.ts`, `frontend-v2/src/modules/system/config/permission-groups.ts`, `frontend-v2/src/shared/constants/statuses.ts` (sinh bằng script, không gõ tay)

## Implementation Steps
1. Viết `labor_contract_codes.py` theo khuôn `hr_work_history_codes.py`.
2. Hai model; FK mềm; mọi `String(n)` ghi chú độ dài.
3. Thêm import vào `all_models.py`.
4. `alembic heads` (hiện `wsched01`) → `alembic revision --autogenerate -m "hop_dong_lao_dong"` → **cắt tay** chỉ giữ 2 `create_table` + index; đặt revision `lbrct01`; downgrade drop 2 bảng.
5. Quyền + phạm vi + seed + nhãn; sửa số 72→74; grep thêm `len(ENTITIES)` ở `test/backend` và FE test nếu ghim số.
6. `docker compose exec -T api python scripts/gen_status_ts.py` → kiểm diff `statuses.ts`.
7. FE ENTITIES + permission-groups.
8. `alembic upgrade head`; chạy `pytest test/backend/test_pham_vi_khai_du_b07.py test/backend/test_dong_bo_giao_dien_v2.py test/backend/test_ho_so_nhan_su_dot1.py -q`.

## Todo
- [ ] codes + register · [ ] 2 model + all_models · [ ] migration cắt tay · [ ] permissions/scoping/seed · [ ] gen statuses.ts · [ ] FE ENTITIES/groups · [ ] test đếm 74

## Success Criteria
`alembic upgrade head` + `downgrade -1` + `upgrade` sạch; 3 tệp test trên xanh; `npm run typecheck` 0 lỗi; `statuses.ts` có `LABOR_CONTRACT_TYPE`/`LABOR_CONTRACT_STATUS`.

## Risk Assessment
| Rủi ro | Khả năng×Tác động | Giảm thiểu |
|---|---|---|
| Migration kéo theo drift của bảng khác | Cao×Cao | Cắt tay; review diff chỉ còn 2 bảng |
| Quên `_SYS_ENTITIES` → lộ lương | Trung×Cao | Thêm assert trong test phase 07 |
| Snapshot `department_id` lệch khi NV điều chuyển | Trung×Thấp | Chấp nhận: HĐ thuộc phòng lúc ký; HR phạm vi `company` vẫn thấy |

## Security
Lương nằm sau khóa riêng; không cấp mặc định cho vai trò nào ngoài `hr_profile` + admin.

## Next
Phase 02.
