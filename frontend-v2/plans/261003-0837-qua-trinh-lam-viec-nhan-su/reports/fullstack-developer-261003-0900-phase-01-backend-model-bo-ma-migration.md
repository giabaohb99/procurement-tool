# Phase 01 — Backend: model, bộ mã, migration

## Thực thi
- Phase: phase-01-backend-model-bo-ma-migration.md
- Plan: frontend-v2/plans/261003-0837-qua-trinh-lam-viec-nhan-su/plan.md
- Trạng thái: **completed**

## Tệp đã sửa/tạo
- TẠO `backend/app/core/hr_work_history_codes.py` (79 dòng) — `WorkEventType(IntEnum)` + `MAIN_TRACK`/`APPLICABLE`/`POSITION_TRACK` + register bộ mã.
- TẠO `backend/app/modules/employee/work_history_model.py` (74 dòng) — model `EmployeeWorkHistory`.
- TẠO `backend/migrations/versions/wkhist01_qua_trinh_cong_tac_nhan_su.py` (73 dòng) — viết tay, không autogenerate.
- SỬA `backend/app/core/code_sets.py` (+1 dòng import `hr_work_history_codes`).
- SỬA `backend/app/core/all_models.py` (+1 dòng import `work_history_model`).
- SINH `frontend-v2/src/shared/constants/statuses.ts` (qua `gen_status_ts.py`, không sửa tay).

## Chi tiết để agent phase 02/04 dùng

### Bảng `tab_employee_work_history`
18 cột thật (14 cột nghiệp vụ + 4 cột audit `created_at/by`, `updated_at/by` +
`id`) — khác số "14" ghi ở mục "Thành công khi" của phase file, số đó đếm thiếu
4 cột audit chuẩn `AuditMixin` (mọi bảng trong repo đều có, không thể bỏ). Đã
xác nhận bằng `SHOW CREATE TABLE` sau khi `upgrade head`:

| Cột | Kiểu | Default |
|---|---|---|
| `id` | BIGINT PK AI | — |
| `employee_id` | BIGINT NOT NULL | — (FK mềm, không ForeignKey) |
| `event_type` | SMALLINT NOT NULL | — |
| `from_date` | DATE NOT NULL | — |
| `to_date` | DATE NULL | — |
| `company_id` / `department_id` / `position_id` | BIGINT NOT NULL | 0 |
| `position_label` | VARCHAR(100) NOT NULL | '' |
| `decision_no` | VARCHAR(50) NOT NULL | '' |
| `decision_date` | DATE NULL | — |
| `note` | VARCHAR(500) NOT NULL | '' |
| `applied_at` | DATETIME NULL | — |
| `applied_by` | BIGINT NOT NULL | 0 |
| `created_at/by`, `updated_at/by` | AuditMixin chuẩn | |

Index: `ix_employee_work_history_emp_from (employee_id, from_date)`. Không UNIQUE.

### Bộ mã `WorkEventType` (`backend/app/core/hr_work_history_codes.py`)
```python
class WorkEventType(IntEnum):
    HIRE = 1; TRANSFER = 2; APPOINT = 3; CONCURRENT = 4
    DISMISS = 5; RESIGN = 6; OTHER = 9   # 7 để trống cho "Đi làm lại" V2-5
```
Kèm `WORK_EVENT_TYPE_LABELS`, `MAIN_TRACK = {1,2,3,5,6}`,
`APPLICABLE = {1,2,3,4,5,6}`, `POSITION_TRACK = {1,2,3,5}` (frozenset of
`WorkEventType`, so sánh trực tiếp bằng `in`). Đăng ký `CodeSet("work_event_type", ...)`.

### Hằng sinh trong `statuses.ts`
`export const WORK_EVENT_TYPE: readonly StatusOption[]` — 7 phần tử, `value`
là chuỗi số `"1".."9"` (bỏ 7, 8), `sort_order` = chính số đó. Có trong
`STATUS_SETS.work_event_type`. Dùng `labelOf(WORK_EVENT_TYPE, String(code))`
ở FE (phase 04/05).

### Alembic
- Revision mới: `wkhist01`, `down_revision = rptacc01` (head trước khi làm).
- Đã chạy `upgrade head` → `downgrade -1` → `upgrade head` sạch, không lỗi.
- `alembic heads` còn đúng 1 head: `wkhist01 (head)`.

## Việc đã làm
- [x] codes + register + code_sets
- [x] model + all_models
- [x] migration viết tay, lên/xuống sạch
- [x] gen_status_ts, `statuses.ts` sinh cùng lúc

## Kiểm tra
- `alembic upgrade head` / `downgrade -1` / `upgrade head`: sạch, 1 head.
- `SHOW CREATE TABLE tab_employee_work_history`: khớp thiết kế (18 cột, 1 index,
  không FK thật trên `employee_id`).
- `python -m scripts.gen_status_ts --check`: "OK: statuses.ts đã khớp với backend (17 bộ mã)".
- `pytest test/backend/test_status_catalog_b01.py test/backend/test_pham_vi_khai_du_b07.py -q`:
  31 passed, 1 skipped (test cũ vốn skip, không liên quan).
- Không đổi `ENTITIES`/`SCOPE_FIELDS` — không chạy lại toàn bộ `test/backend`
  theo đúng chỉ dẫn (chỉ test liên quan tới bộ mã + phạm vi bất biến).
- Không commit (theo chỉ dẫn).

## Concerns
- Số "14 cột" ở mục "Thành công khi" của phase file là đếm thiếu 4 cột audit —
  đã document ở trên, không phải lỗi, chỉ là phase file đếm sai; không sửa phase
  file (ngoài phạm vi việc được giao: chỉ triển khai, không chỉnh plan/phase).
- Chưa đụng `schema.py`/`field_limits.py` (thuộc phase 02) — model dùng
  `String(100)`/`String(50)`/`String(500)` trực tiếp khớp thiết kế, phase 02
  sẽ cần khai alias ở `field_limits.py` khi viết Pydantic schema để tránh lỗi
  500 (xem `.claude/rules/backend-input-limits.md`).

**Status:** DONE
**Summary:** Model + bộ mã `WorkEventType` + migration `wkhist01` chạy sạch lên/xuống, 1 head; `statuses.ts` sinh lại khớp (`WORK_EVENT_TYPE`). Test bộ mã + phạm vi bất biến xanh. Không đổi file ngoài phạm vi phase 01, không commit.
**Concerns:** Mục "14 cột" trong phase file đếm thiếu audit columns — bảng thật có 18 cột, đã ghi rõ ở report để phase 02 không bất ngờ.
