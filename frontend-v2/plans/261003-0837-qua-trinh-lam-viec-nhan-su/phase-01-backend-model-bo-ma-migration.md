# Phase 01 — Backend: model, bộ mã, migration

**Ưu tiên:** P2 · **Effort:** 2h · **Trạng thái:** completed · **Phụ thuộc:** —

## Bối cảnh
- `backend/app/modules/employee/department_model.py` (khuôn FK mềm + index), `contact_model.py` (bảng con).
- `backend/app/core/report_keys.py` (khuôn IntEnum + CodeSet giá trị số-viết-thành-chuỗi), `core/code_sets.py`, `scripts/gen_status_ts.py`.
- `.claude/rules/backend-input-limits.md` (max_length, dải năm, trần số dòng).
- Bộ nhớ: autogenerate trôi ~650 dòng → **viết tay** migration.

## Thiết kế bảng `tab_employee_work_history`

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id`, `created_at/by`, `updated_at/by` | AuditMixin | |
| `employee_id` | BIGINT NOT NULL | FK mềm → `tab_employee.id` (khuôn `tab_employee_department`; xóa hồ sơ dọn ở tầng service) |
| `event_type` | SMALLINT NOT NULL | `WorkEventType` — 0 không hợp lệ ở schema |
| `from_date` | DATE NOT NULL | **= ngày hiệu lực** (Q1 chốt GỘP 03/10/2026 — không có cột `effective_date`) |
| `to_date` | DATE NULL | NULL = đang hiệu lực |
| `company_id` / `department_id` / `position_id` | BIGINT default 0 | 0 = không khai |
| `position_label` | VARCHAR(100) default '' | **Nhãn CHỤP lúc lưu**, cố ý KHÔNG `propagate_rename` — lịch sử phải giữ chức danh đúng thời điểm; chức vụ bị xóa vẫn còn chữ. Khớp `String(100)` của `tab_employee.position` |
| `decision_no` | VARCHAR(50) default '' | Số QĐ |
| `decision_date` | DATE NULL | Ngày ký QĐ |
| `note` | VARCHAR(500) default '' | |
| `applied_at` | DATETIME NULL | Lần áp vào hồ sơ gần nhất |
| `applied_by` | BIGINT default 0 | |

Index: `ix_employee_work_history_emp_from (employee_id, from_date)` — mọi truy vấn lọc theo người, xếp theo ngày.
Không UNIQUE (một ngày có thể vừa bổ nhiệm vừa kiêm nhiệm).

**Đường nâng lên V1-8 (không đập bỏ):** V1-8 thêm `tab_hr_decision` (đầu phiếu: tờ trình, số/ngày QĐ, nội dung, PDF, trạng thái duyệt) + cột `decision_id BIGINT default 0` ở bảng này (+ `replaces_employee_id` cho «Thay thế cho»). Dòng ghi tay hiện tại = `decision_id 0`, giữ nguyên. Duyệt phiếu V1-8 sinh dòng vào CHÍNH bảng này rồi gọi cùng hàm áp hồ sơ của phase 02.

## Bộ mã `WorkEventType` (`core/hr_work_history_codes.py`, thuần stdlib)

| Số | Hằng | Nhãn | Nhóm | Áp hồ sơ |
|---|---|---|---|---|
| 1 | HIRE | Tuyển dụng | chính | công ty/phòng/chức vụ |
| 2 | TRANSFER | Điều chuyển | chính | như trên |
| 3 | APPOINT | Bổ nhiệm | chính | như trên |
| 4 | CONCURRENT | Kiêm nhiệm | kiêm nhiệm | thêm/gỡ phòng kiêm nhiệm |
| 5 | DISMISS | Miễn nhiệm | chính | như trên |
| 6 | RESIGN | Thôi việc | chính (kết thúc) | tình trạng → nghỉ việc + `resign_date` (Q2, xem phase 02) |
| 9 | OTHER | Khác | — | không |

Luật bất biến ghi đầu tệp: số đã cấp không đổi, không tái dùng, thêm thì lấy số kế (7 = «Đi làm lại» để dành V2-5).
Khai thêm `MAIN_TRACK = {1,2,3,5,6}`, `APPLICABLE = {1,2,3,4,5,6}`, `POSITION_TRACK = {1,2,3,5}` ngay trong tệp (một chỗ, BE dùng; FE nhận cờ `can_apply` qua API, không chép luật).
Đăng ký: `register(CodeSet("work_event_type", "Loại quá trình công tác", [Code(str(int(k)), label, sort_order=int(k)) ...]))`.

## Tệp

| Tạo | Sửa |
|---|---|
| `backend/app/core/hr_work_history_codes.py` | `backend/app/core/code_sets.py` (+1 dòng import) |
| `backend/app/modules/employee/work_history_model.py` | `backend/app/core/all_models.py` (+1 dòng) |
| `backend/migrations/versions/<rev>_qua_trinh_cong_tac_nhan_su.py` (viết tay) | `frontend-v2/src/shared/constants/statuses.ts` (SINH, không sửa tay) |

## Các bước
1. Viết `hr_work_history_codes.py` (IntEnum + LABELS + MAIN_TRACK/APPLICABLE + register).
2. Thêm import vào `code_sets.py`.
3. Viết model (comment tiếng Việt giải thích FK mềm, nhãn chụp). Thêm vào `all_models.py`.
4. `docker compose exec api alembic heads` lấy `down_revision`; viết tay migration: `create_table` + 1 index; `downgrade` = drop index + drop table. Không autogenerate.
5. `alembic upgrade head`, rồi `downgrade -1`, rồi `upgrade head` lại trên local.
6. Sinh TS trên MÁY (container api không mount `frontend-v2/`): `cd backend && python3 -m scripts.gen_status_ts`; kiểm `statuses.ts` có `WORK_EVENT_TYPE`.

## Todo
- [x] codes + register + code_sets
- [x] model + all_models
- [x] migration viết tay, lên/xuống sạch
- [x] gen_status_ts, commit `statuses.ts` cùng commit

## Thành công khi
Bảng có trên MySQL local đúng 14 cột + 1 index; `/meta/statuses` trả `work_event_type`; `gen_status_ts` lần hai báo «đã khớp».

## Rủi ro
| Rủi ro | Khả năng × Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Quên `code_sets.py` → bộ mã vắng mặt im lặng | TB × TB | Bước 6 kiểm `statuses.ts`; test phase 03 gọi `get("work_event_type")` |
| Migration lệch head do người khác push | TB × Thấp | `git fetch` + `alembic heads` ngay trước khi viết |

## Rollback
`alembic downgrade -1` (bảng mới, không ai khác tham chiếu). Xóa dòng trong `code_sets.py`/`all_models.py`, sinh lại TS.
Trên prod: sao lưu trước khi downgrade — mất mọi dòng HR đã nhập.

## Bảo mật
Không cột nhạy cảm. Không đổi `ENTITIES`/`SCOPE_FIELDS`.
