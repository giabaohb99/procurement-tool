# Phase 01 — BE dữ liệu, migration, dịch vụ, API kiêm nhiệm

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 12/11/2026 | backend | Nháp | duoc-CR-755 |

## Context links
- [plan.md](plan.md) — quyết định dữ liệu, luật hiệu lực, Q1–Q6.
- Mã hiện có: `employee/department_model.py:24-47`, `employee/department_service.py` (L1 192, L2 227-283, L3 106-127,
  `set_departments` 286-324), `employee/controller.py:419-457`, `employee/work_history_model.py` (khuôn cột QĐ),
  `employee/work_history_access.py:77-125` (khuôn gác tệp), `core/file_registry.py:82-87,142-146`,
  `core/attachment_scope.py:147-155`, `department/references.py:47`, `employee/service.py:604` (xóa hồ sơ).
- Luật: `.claude/rules/backend-input-limits.md`, `.claude/rules/hr-employee-profile.md` (bẫy QĐ 2, 3, 6),
  `.claude/rules/chung-dat-ten-va-quy-uoc.md` §3, §5. Memory: migration autogenerate phải cắt tay.

## Overview
P1. Dựng bảng `tab_employee_concurrent` + chuyển dữ liệu cũ, dịch vụ CRUD có ba chốt L1/L2-theo-cặp/L3, API REST, tệp
quyết định, và đổi `core/auth.py` đọc phòng kiêm nhiệm CÙNG công ty từ bảng mới (để hành vi CR-167 không gãy giữa chừng).
Phạm vi khác công ty là việc của phase 02.

## Key insights
- 26/27 phòng prod là phòng dùng chung (`company_id = 0`): một id phòng có thể là phòng chính ở A và kiêm nhiệm ở B — bảng
  mới KHÔNG có UNIQUE(employee, department); chặn chồng giai đoạn ở service.
- Phòng phục vụ pháp nhân: `Department.company_id IN (0, c)` hoặc có dòng `DepartmentCompany(department_id, c, is_active)`.
- Tệp QĐ gắn theo id dòng → id phải bền: cấm xóa-chèn, sửa tại chỗ.
- `employees_of_department` (department_service.py:90) không ai gọi — xóa luôn.

## Requirements
Chức năng:
- Một dòng = công ty, phòng, chức vụ (danh mục), từ ngày (bắt buộc khi tạo mới), đến ngày (trống = chưa kết thúc), số QĐ,
  ngày QĐ, ghi chú, công tắc **Tính vào phạm vi quyền** (mặc định bật), tệp QĐ (đính kèm).
- Trạng thái dẫn xuất: 1 Sắp tới · 2 Đang hiệu lực · 3 Đã hết (theo `vn_today()`).
- Danh sách trả số + nhãn trạng thái, tên công ty / phòng / chức vụ, `file_count`, `can_edit`, `can_open_files`.
Phi chức năng:
- `decision_no` ≤ 50, `note` ≤ 500 (`max_length` ở schema, 422 chứ không 500); ngày trong khoảng 1900–2100; `to_date >=
  from_date`; trần **30 dòng / nhân sự**; không chồng giai đoạn cùng (phòng, công ty) → 409.
- Dòng trùng cặp phòng chính (phòng chính + công ty chính) → 400 *Trùng phòng ban chính*.

## Architecture
```
tab_employee_concurrent  id BIGINT PK · employee_id BIGINT · company_id BIGINT · department_id BIGINT
                         position_id BIGINT default 0 · position_label String(100) default '' (nhãn CHỤP)
                         from_date Date NULL (NULL chỉ cho dòng chuyển từ dữ liệu cũ) · to_date Date NULL
                         decision_no String(50) default '' · decision_date Date NULL · note String(500) default ''
                         counts_scope Bool default 1 · work_history_id BIGINT default 0 (dòng QTCT đã Áp ra nó, phase 03)
                         AuditMixin
                         INDEX (employee_id) · INDEX (department_id, company_id) · INDEX (work_history_id)
```
Luồng ghi: controller (`require("employee","write")`) → `employee_in_scope(... "write")` (phạm vi trên công ty CHÍNH) →
L1 `block_edit_own_department` → L3 `check_concurrent_target` → L2 `block_out_of_scope_pair` (cặp MỚI; khi sửa cặp thì kiểm
cả cặp CŨ) → kiểm chồng giai đoạn + trần → ghi tại chỗ → `clear_perm_cache_of(employee_id)` → commit → audit.

L2 theo cặp (`department_service.pair_in_write_scope(db, profile, dept, company)`), đo trên `employee.write`, bậc rộng nhất:
- `all` → được; `company` → `company == profile.company_id`;
- `dept` trở xuống → `(dept ∈ dept_ids và company == company chính)` hoặc `[dept, company] ∈ profile.concurrent_pairs`
  (khóa này phase 02 mới điền; trước đó rỗng) hoặc `(dept ∈ inc.department và company == company chính)`.
  ⚠️ Ô "Phòng ban được xem" CHỈ phủ công ty chính — chặt hơn phạm vi đọc, cố ý (mở rộng tầm nhìn người khác).

Hồ sơ quyền (`core/auth.py:246-278`, phần của phase này): bỏ `departments_of`; một truy vấn bảng mới lấy dòng hiệu lực +
`counts_scope`; dòng `company_id == công ty chính` → nối vào `dept_ids` sau phòng chính. Dòng khác công ty BỎ QUA (phase 02).

API (router `tags=["employee"]`, docstring tiếng Việt):
| Phương thức | Đường | Quyền |
|---|---|---|
| GET | `/api/employees/{eid}/concurrents` | `employee.read` + phạm vi hồ sơ |
| POST | `/api/employees/{eid}/concurrents` | `employee.write` + L1/L2/L3 |
| PATCH | `/api/employees/{eid}/concurrents/{cid}` | như POST; `cid` phải thuộc `eid` (404) |
| DELETE | `/api/employees/{eid}/concurrents/{cid}` | như POST; dòng có tệp cần thêm `employee_sensitive.read` |
| GET | `/api/employees/{eid}/departments` | giữ, `extra_department_ids` = phòng kiêm nhiệm hiệu lực cùng công ty (tương thích) |
`PUT /api/employees/{eid}/departments` **gỡ** (chỉ frontend-v2 gọi, thay ở phase 04).

Tệp QĐ: entity mới `employee_concurrent` ở `FILE_POLICY` (`("employee", _DOC, 50)`) + `PRIVATE_ENTITIES`;
`attachment_scope` thêm nhánh `_fk(EmployeeConcurrent.employee_id, Employee, EmployeeConcurrent.id)`; gác riêng ở
`concurrent_access.check_file` (cùng luật Q4 của QTCT: chính chủ đọc; người khác cần `employee_sensitive.read`; gắn/gỡ cần
`employee.write` đúng phạm vi + L2 cặp), gọi ở đầu `attachment/controller._check` ngay sau dòng của QTCT.

## Related code files
Tạo (phase sở hữu):
- `backend/app/modules/employee/concurrent_model.py` · `concurrent_schema.py` · `concurrent_service.py` ·
  `concurrent_controller.py` · `concurrent_access.py`
- `backend/app/core/hr_concurrent_codes.py` (`ConcurrentStatus` IntEnum + nhãn + `get_concurrent_status(from, to, today)`)
- `backend/migrations/versions/kn755a_bang_kiem_nhiem.py`
- `test/backend/test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py`, `test/backend/test_kiem_nhiem_migration_cr755.py`
Sửa (phase sở hữu):
- `backend/app/core/all_models.py`, `core/code_sets.py`, `core/file_registry.py`, `core/attachment_scope.py`
- `backend/app/core/auth.py` (chỉ khối dựng `dept_ids`, dòng 246-278)
- `backend/app/modules/employee/department_service.py` (thêm L2 cặp, L3 đích; xóa `employees_of_department`)
- `backend/app/modules/employee/controller.py` (gỡ PUT, GET giữ), `backend/app/main.py` (gắn router)
- `backend/app/modules/attachment/controller.py` (một dòng gọi `concurrent_access.check_file`)
- `backend/app/modules/department/references.py` (+ tham chiếu `EmployeeConcurrent.department_id`; company references nếu có
  tệp tương tự ở `company/`)
- `backend/app/modules/employee/service.py` (chỉ `delete_employee_core` dòng ~604: xóa dòng kiêm nhiệm + liên kết tệp)
- `test/backend/test_kiem_nhiem_phong_ban.py`, `test/backend/scope_factory.py` (`add_department` → tạo dòng bảng mới),
  `test/backend/test_pham_vi_dinh_kem_b08.py` (canh `FILE_POLICY` từng dòng)
- `frontend-v2/src/**/status-codes*.ts` sinh bằng `backend/scripts/gen_status_ts.py` (chỉ chạy script, không sửa tay)

## Implementation steps
1. `git fetch origin erp-v2 && git merge origin/erp-v2`; `alembic heads` lấy đầu thật (12/11 là `stix723`).
2. Model + khai `all_models.py`. Bộ mã `hr_concurrent_codes.py`, đăng ký `code_sets.py`, chạy `gen_status_ts.py`.
3. Migration viết tay `kn755a` (không autogenerate): tạo bảng nếu chưa có; chép
   `INSERT INTO tab_employee_concurrent (employee_id, company_id, department_id, counts_scope, note, created_at, created_by, ...)
   SELECT ed.employee_id, e.company_id, ed.department_id, 1, 'Chuyển từ kiêm nhiệm cũ', ed.created_at, ed.created_by ...
   FROM tab_employee_department ed JOIN tab_employee e ON e.id = ed.employee_id WHERE ed.is_primary = 0`;
   rồi `DELETE FROM tab_employee_department WHERE is_primary = 0`. Chữ tiếng Việt trong migration qua tham số bind, không qua
   `mysql -e`. Downgrade: chép dòng hiệu lực cùng công ty chính về `is_primary = 0` (bỏ trùng), `DROP TABLE`.
4. Schema `ConcurrentIn/ConcurrentPatch/ConcurrentOut` (`max_length`, `ge/le` ngày, validator `to >= from`).
5. Service: `list_concurrents`, `create_concurrent`, `update_concurrent`, `delete_concurrent`,
   `active_concurrent_rows(db, employee_id, today, counts_scope_only)` (một truy vấn, dùng lại ở auth + phase 03/05),
   `check_concurrent_target` (L3), `block_overlap`, nhãn chức vụ chụp từ `tab_job_position` (chặn chức vụ ngừng dùng khi gán mới,
   giữ khi sửa ô khác — cùng luật hồ sơ).
6. `department_service`: `pair_in_write_scope`, `block_out_of_scope_pair` (403 nêu tên phòng + công ty).
7. `concurrent_access.py` (`can_edit`, `check_file`) + nối `attachment/controller._check` + `file_registry` + `attachment_scope`.
8. Controller + `main.py`; gỡ PUT `/departments` và schema `ExtraDepartmentsIn`; GET `/departments` tính `extra_department_ids`
   từ bảng mới.
9. `core/auth.py`: dựng `dept_ids` từ phòng chính + dòng cùng công ty (hiệu lực, bật công tắc). Giữ số truy vấn cố định.
10. `delete_employee_core`: xóa dòng + `FileLink` (dùng helper xóa của `attachment/service.py`, khuôn `work_history_service.delete_all_of`).
11. Sửa `department_service.set_departments`/`set_extra_departments`: CHƯA đổi ở phase này ngoài việc không còn ai ghi phòng phụ
    qua API; dọn hẳn ở phase 03 (cùng tệp, chạy sau).
12. Bài kiểm (mục Success criteria), chạy đúng tệp.

## Todo
- [x] Merge + đầu alembic
- [x] Model, bộ mã, sinh TS
- [x] Migration chép dữ liệu + downgrade + bài kiểm migration (khuôn `test_hdld_gop_bang_mau_migration_cr629b.py`)
- [x] Schema giới hạn đầu vào
- [x] Service CRUD + L3 + chồng giai đoạn + trần
- [x] L2 theo cặp
- [x] Gác tệp QĐ + đăng ký entity tệp
- [x] API + gỡ PUT
- [x] auth `dept_ids` từ bảng mới
- [x] Xóa hồ sơ dọn dòng + tệp; tham chiếu xóa phòng
- [x] Sửa `test_kiem_nhiem_phong_ban.py`, `scope_factory.py`, `test_pham_vi_dinh_kem_b08.py`

## Success criteria
- `docker compose exec -T api python -m pytest test/backend/test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py
  test/backend/test_kiem_nhiem_migration_cr755.py test/backend/test_kiem_nhiem_phong_ban.py
  test/backend/test_pham_vi_dinh_kem_b08.py test/backend/test_department_company.py -q --timeout=120` xanh.
- Bài kiểm phủ: tạo dòng khác công ty với phòng dùng chung (cùng id phòng chính) qua được; phòng không phục vụ công ty → 400;
  chồng giai đoạn → 409; trần 30 → 400; tự sửa của mình → 403 (L1); người bậc `dept` ở A gán cặp ở B → 403 (L2); bậc
  `company` ở A gán (X, A) → được, (X, B) → 403; `note` 501 ký tự → 422; xóa dòng có tệp thiếu nhạy cảm → 403; tệp QĐ người
  khác thiếu nhạy cảm → 403, chính chủ đọc được; migration chép đủ N dòng phụ, bảng cũ chỉ còn dòng chính, downgrade trả lại.
- Hồ sơ quyền: người có phòng kiêm nhiệm cùng công ty vẫn thấy phiếu phòng đó (hồi quy CR-167); dòng hết hạn / tắt công tắc
  → không thấy. Đếm truy vấn `get_perm_profile` với 0 dòng và 5 dòng bằng nhau.
- `ruff check app` 0 lỗi.

## Risks
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Migration chép thiếu / nhân đôi khi chạy lại | Thấp × Cao | Chỉ chèn khi bảng mới trống dòng cho (employee, dept, company); bài kiểm migration chạy hai lần |
| Nhân sự `company_id = 0` có phòng phụ | Trung × Trung | Dòng chép mang `company_id = 0`; auth coi `0 == 0` là cùng công ty → hành vi cũ giữ nguyên; ghi chú trong tài liệu |
| Gỡ PUT làm hỏng màn hiện tại trước phase 04 | Cao × Thấp | Không deploy giữa 01 và 04 (ghi ở plan.md) |
| Bài kiểm cũ dựng phòng phụ bằng `EmployeeDepartment` | Cao × Thấp | Sửa `scope_factory.add_department` một chỗ; grep `is_primary=False` trong `test/backend` |

## Security
- L1 giữ (kể cả admin, như hiện tại). L2 đo cả cặp mới và cặp cũ khi sửa; bật lại công tắc, nới ngày, đổi phòng/công ty đều
  là mở rộng phạm vi → luôn qua L2.
- Tệp QĐ thuộc nhóm riêng tư (không lộ `url`), gác nhạy cảm như QTCT.
- Mọi ghi xóa cache quyền của tài khoản gắn nhân sự (`clear_perm_cache_of`).

## Next steps
Phase 02 (phạm vi khác công ty) và 03 (đường ghi phụ) chạy song song sau phase này.
