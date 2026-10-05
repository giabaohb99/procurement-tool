# Phase 01 — Nền backend: bộ mã, model, migration, khóa quyền, seed

> Status: DONE 05/10/2026 — migration `wsched01` (viết tay, down_revision `wkhist01`), seed mẫu «Hành chính T2–T7» trong migration, `hr_profile` cũng được sửa (chốt 05/10). Test BB4 `employee/work_history_controller.py` đỏ sẵn từ trước (không thuộc phase này).

## Context links
- `CLAUDE.md` gốc (R2/QĐ-11, B-07 SCOPE_FIELDS, all_models, alembic) · `.claude/rules/backend-input-limits.md`
- Mẫu bộ mã số: `backend/app/core/hr_work_history_codes.py` (IntEnum + CodeSet chuỗi số) · `core/code_sets.py`
- Mẫu danh mục PUBLIC: `holiday` ở `core/permissions.py` / `core/scoping.py` / `seed.py` (dòng ~221, ~616, ~678)
- Bộ test canh: `test_pham_vi_khai_du_b07.py:187` (đếm 71), `test_pham_vi_luat_bat_bien.py` (BB3 lý do PUBLIC),
  `test_dong_bo_giao_dien_v2.py:90` (ENTITIES FE == BE), `test_status_catalog_b01.py` (statuses.ts khớp)
- Memory: migration autogenerate trôi ~650 dòng → **phải gọt về đúng 3 bảng**.

## Overview
Priority P2 · Status pending · 4h. Dựng phần mà mọi phase sau phụ thuộc: bộ mã, 3 bảng, khóa quyền.
Xong phase này thì FE (phase 4) có `statuses.ts` + `permission-types.ts` để code.

## Key insights
- `test_dong_bo_giao_dien_v2` đọc `frontend-v2/.../permission-types.ts` → thêm entity BE mà không thêm FE là đỏ.
  Vì vậy phase này **sở hữu luôn 1 dòng** ở tệp FE đó (ngoại lệ có chủ đích).
- `statuses.ts` là tệp SINH — chỉ phase này chạy `gen_status_ts`, không ai sửa tay.
- Prod: `ensure_admin_role` tự cấp FULL cho `admin`; vai trò khác KHÔNG tự có (D-018) → ghi vào tài liệu phase 6.
- Nhân sự chỉ có MỘT `company_id` + MỘT `department_id` (phòng chính, khớp `tab_employee_department.is_primary`).

## Data model

### Bộ mã — `backend/app/core/work_schedule_codes.py` (stdlib-only, như `hr_work_history_codes.py`)
```python
class WorkDayKind(IntEnum):        # tab_work_schedule_day.day_kind
    OFF = 1        # Nghỉ
    FULL = 2       # Cả ngày
    MORNING = 3    # Chỉ buổi sáng  (vd T7 08:00–12:00 → 0.5 công)
    AFTERNOON = 4  # Chỉ buổi chiều
class WorkScheduleLevel(IntEnum):  # tab_work_schedule_assignment.target_level
    SYSTEM = 1      # Toàn hệ thống (target_id = 0)
    COMPANY = 2     # Pháp nhân
    DEPARTMENT = 3  # Phòng ban
    EMPLOYEE = 4    # Nhân sự
LEVEL_PRECEDENCE = (EMPLOYEE, DEPARTMENT, COMPANY, SYSTEM)  # hẹp thắng rộng — KHÔNG suy từ độ lớn số
```
`0` không hợp lệ (quy ước «0 = chưa khai»). Số đã cấp không đổi/không tái dùng. Đăng ký 2 `CodeSet`
`work_day_kind`, `work_schedule_level` (value = `str(int)`), thêm import vào `core/code_sets.py`.

### Bảng (model ở `backend/app/modules/work_schedule/model.py`, `Base, AuditMixin`)
| Bảng | Cột | Ràng buộc / index |
|---|---|---|
| `tab_work_schedule` | `name String(150)`, `note String(500)=""`, `is_active Bool=True` | `UNIQUE(name)` `uq_work_schedule_name` |
| `tab_work_schedule_day` | `schedule_id BigInt`, `weekday SmallInt` (0=T2…6=CN, = `date.weekday()`), `day_kind SmallInt`, `start_time/end_time/lunch_start/lunch_end Time NULL` | `UNIQUE(schedule_id, weekday)` `uq_work_schedule_day`; index `schedule_id` |
| `tab_work_schedule_assignment` | `target_level SmallInt`, `target_id BigInt=0`, `schedule_id BigInt`, `effective_from Date NOT NULL`, `effective_to Date NULL` (NULL = không thời hạn), `note String(500)=""` | index `ix_wsa_target(target_level, target_id, effective_from)`, index `ix_wsa_schedule(schedule_id)` |

FK mềm (không FK cứng) — cùng quy ước `department_id`/`manager_id` của repo; chốt id-có-thật ở service (phase 2).
Không thêm `hours_per_day`: giờ chuẩn suy từ chính ngày đó (A5 của plan).

## Related code files
**Create**
- `backend/app/core/work_schedule_codes.py`
- `backend/app/modules/work_schedule/__init__.py`
- `backend/app/modules/work_schedule/model.py` (~90 dòng)
- `backend/migrations/versions/<rev>_lich_lam_viec.py`
- `test/backend/test_lich_lam_viec_bo_ma_va_quyen.py`

**Modify**
- `backend/app/core/code_sets.py` (+1 import) · `backend/app/core/all_models.py` (+1 import)
- `backend/app/core/permissions.py` — `"work_schedule"` vào `ENTITIES` (khối Nhân sự, kèm chú thích),
  `ENTITY_LABELS["work_schedule"] = "Nhân sự › Lịch làm việc"`
- `backend/app/core/scoping.py` — `"work_schedule": PUBLIC` + chú thích lý do
- `backend/app/seed.py` — thêm vào `_SYS_ENTITIES`; vòng `setdefault` cấp `(["read"], "all")` cho mọi vai trò;
  `hr_leave` cấp `(["read","create","write","delete"], "all")`
- `test/backend/test_pham_vi_khai_du_b07.py` — 71 → 72 + một dòng lịch sử trong docstring
- `test/backend/test_pham_vi_luat_bat_bien.py` — `BB3_PUBLIC_CO_LY_DO["work_schedule"]`
- `frontend-v2/src/core/authorization/permission-types.ts` — `'work_schedule'` (bắt buộc bởi test đồng bộ)
- `frontend-v2/src/shared/constants/statuses.ts` — **SINH** bằng `python -m scripts.gen_status_ts`

`seed_prod.py`: KHÔNG sửa (nó import `STD_ROLES` + `ensure_admin_role` từ `seed.py`).

## Implementation steps
1. Viết `work_schedule_codes.py` + nhãn tiếng Việt; import ở `code_sets.py`.
2. Viết `model.py` (3 lớp); import module ở `all_models.py`.
3. `docker compose exec api alembic heads` (lấy head hiện tại) → `alembic revision --autogenerate -m "lich_lam_viec"`
   → **xóa mọi thứ ngoài 3 `create_table` + index/unique của chúng**; `downgrade` drop 3 bảng ngược thứ tự.
4. `alembic upgrade head` rồi `downgrade -1` rồi `upgrade head` lại trên local (kiểm downgrade chạy).
5. Khai entity/label/scope/seed như trên. Lý do PUBLIC (một câu, dùng cho cả scoping + BB3):
   *"danh mục cấu hình lịch dùng chung; dòng gán trỏ đích ĐA HÌNH (cấp + id) nên khuôn một-cột của
   apply_scope không diễn đạt được; ai SỬA gác bằng work_schedule.write"*.
6. Chạy `gen_status_ts`; thêm `'work_schedule'` vào FE `permission-types.ts`.
7. Test mới `test_lich_lam_viec_bo_ma_va_quyen.py`: 2 bộ mã đăng ký đủ, không có số 0, `LEVEL_PRECEDENCE`
   phủ đủ 4 cấp không trùng; `ENTITY_LABELS` có khóa; `hr_leave` có write, vai trò thường chỉ read;
   `pur_manager` KHÔNG có write (bẫy `_PUR_MANAGER_PERMS`).
8. Chạy đúng các test đụng: `pytest test/backend/test_pham_vi_khai_du_b07.py test_pham_vi_luat_bat_bien.py
   test_dong_bo_giao_dien_v2.py test_status_catalog_b01.py test_lich_lam_viec_bo_ma_va_quyen.py -q`.

## Todo
- [x] codes + code_sets  - [x] model + all_models  - [x] migration gọt sạch, up/down/up
- [x] permissions/scoping/seed  - [x] gen statuses.ts + permission-types.ts  - [x] test mới + 4 test canh xanh

## Success criteria
- `alembic upgrade head` tạo đúng 3 bảng; tệp migration chỉ chứa 3 bảng (diff < ~80 dòng).
- 5 tệp test ở bước 8 xanh; `gen_status_ts --check` báo khớp; FE `npm run typecheck` 0 lỗi.

## Risk assessment
| Rủi ro | Khả năng × Tác động | Giảm thiểu |
|---|---|---|
| Migration kéo theo drift (ALTER bảng khác) | Cao × Cao | Gọt tay, review diff; up/down/up local |
| Quên `_SYS_ENTITIES` → QL thu mua tự có quyền sửa lịch | TB × TB | Test bước 7 |
| `Time` trên SQLite test | Thấp × TB | Đã dùng ở `tab_leave_request.from_time` — chạy được |

## Security
Khóa mới chỉ cấp read đại trà; write chỉ `hr_leave` + `admin`. Không dữ liệu nhạy cảm.

## Rollback
`alembic downgrade -1`; revert commit (entity + test đếm quay về 71 cùng lúc).

## Next steps
Phase 2 (BE) · Phase 4 (FE) mở khóa.

## Câu hỏi mở
- Ngoài `hr_leave`, vai trò `hr_profile` có được SỬA lịch không? (mặc định plan: chỉ read)
