# Phase 02 — Backend: luật ngày, phân giải lịch, API mẫu lịch + gán lịch

## Context links
- Phase 1 (model, bộ mã) · `backend/app/core/crud.py` (hợp đồng list/get/create/update/delete để giữ y hệt)
- `core/base_controller.py` (`pagination`, `apply_filters`, `apply_sort`) · `core/audit.py record`
- Mẫu chốt xóa: `leave/catalog_controller._block_delete_used_type`
- `.claude/rules/backend-input-limits.md` (max_length, dải năm, trần số dòng)

## Overview
Priority P2 · Status done (05/10/2026) · 8h. Hai router + tầng luật thuần + bộ phân giải. Viết tay (không
`make_crud_router`) vì mẫu lịch ghi KÈM 7 dòng con và danh sách gán phải trả tên đích — nhưng giữ
nguyên hình dạng `{total, items}` / đường dẫn để FE dùng `shared/crud` không cần sửa gì.

## Key insights
- Nửa buổi biểu diễn bằng **bitmask**: `AM=1`, `PM=2`. `work_mask`: OFF=0, FULL=3, MORNING=1, AFTERNOON=2.
  Phase 3 tính `leave_mask` rồi công = `0.5 × popcount(leave_mask & work_mask)`.
- Phân giải theo TỪNG NGÀY, nhưng số truy vấn CỐ ĐỊNH (memory «API phải nhanh»): 1 truy vấn gán +
  1 truy vấn ngày của các mẫu được trỏ — bất kể khoảng 1 hay 400 ngày.
- Đích `target_id = 0` ở cấp ≠ SYSTEM là dữ liệu hỏng: CHẶN lúc ghi VÀ bộ phân giải không bao giờ hỏi
  `(COMPANY, 0)` — nếu không, mọi NV chưa khai pháp nhân dính lịch của một dòng rác.

## Architecture

### Tệp & trách nhiệm (mỗi tệp < 200 dòng)
| Tệp | Nội dung |
|---|---|
| `day_rules.py` | THUẦN (không DB): `DaySpec` dataclass frozen (`kind, start, end, lunch_start, lunch_end`), `FALLBACK_WEEK` (T2–T7 FULL 08:00–17:00 trưa 12–13, CN OFF — **nguồn duy nhất** của giờ mặc định), `work_mask(spec)`, `day_capacity(spec)` (1.0/0.5/0), `worked_hours(spec, start, end)` (cắt theo khung ngày, trừ trưa), `day_hours(spec)`, `weekly_workdays(specs)` |
| `resolver.py` | `load_day_plans(db, *, employee_id, department_id, company_id, from_date, to_date) -> Callable[[date], DaySpec]`; `effective_for_employee(db, employee, on_date) -> dict` (cho thẻ hồ sơ) |
| `template_schema.py` | `DayIn/DayOut`, `ScheduleCreate/Update/Out` + validator |
| `assignment_schema.py` | `AssignmentCreate/Update/Out`, `EffectiveOut` |
| `template_service.py` | list/get/create/update (thay trọn 7 dòng), chặn xóa khi còn gán, `assignment_count` gom 1 truy vấn |
| `assignment_service.py` | kiểm đích có thật, kiểm mẫu có thật + đang dùng, chặn chồng khoảng, gắn tên đích gom 3 truy vấn |
| `template_controller.py` | `/api/work-schedules` + `/api/work-schedules/tools/effective` |
| `assignment_controller.py` | `/api/work-schedule-assignments` |

### Thuật toán phân giải (`load_day_plans`)
1. Cặp ứng viên: `(SYSTEM,0)`; `(COMPANY,company_id)` nếu >0; `(DEPARTMENT,department_id)` nếu >0; `(EMPLOYEE,employee_id)` nếu >0.
2. Truy vấn 1: dòng gán khớp một trong các cặp VÀ `effective_from <= to_date` VÀ `(effective_to IS NULL OR effective_to >= from_date)`.
3. Truy vấn 2: `tab_work_schedule_day` theo các `schedule_id` → `{schedule_id: {weekday: DaySpec}}`.
4. Hàm trả về `plan(day)`: duyệt `LEVEL_PRECEDENCE`; ở mỗi cấp lấy dòng phủ `day`
   (hòa → `effective_from` muộn hơn, rồi `id` lớn hơn — phòng thủ, bình thường đã cấm chồng);
   mẫu thiếu dòng thứ đó (hỏng dữ liệu) → `FALLBACK_WEEK[weekday]` + `logger.warning`; không cấp nào phủ → `FALLBACK_WEEK`.
5. Mẫu `is_active=False` VẪN được dùng nếu còn gán (tắt mẫu = ẩn khỏi ô chọn, không đổi cách tính quá khứ).

### API (phong bì `success(...)`; lỗi nghiệp vụ 400 câu tiếng Việt; validate 422)

**Mẫu lịch — khóa `work_schedule`**
| Method | Path | Quyền | Ghi chú |
|---|---|---|---|
| GET | `/api/work-schedules` | read | `?name=&is_active=&page=&page_size=&sort_by=&sort_dir=` → `{total, items:[ScheduleOut]}`; `apply_scope` (PUBLIC) |
| GET | `/api/work-schedules/{id}` | read | `get_scoped` |
| POST | `/api/work-schedules` | create | body `ScheduleCreate` |
| PATCH | `/api/work-schedules/{id}` | write | `ScheduleUpdate` (mọi trường tùy chọn; có `days` thì phải đủ 7 → thay trọn) |
| DELETE | `/api/work-schedules/{id}` | delete | 400 nếu `assignment_count > 0` |
| GET | `/api/work-schedules/tools/effective?employee_id=&on_date=` | **`employee.read`** + `get_scoped(Employee)` | `on_date` mặc định hôm nay; 404 nếu ngoài phạm vi |

```jsonc
// DayIn / DayOut (giờ "HH:MM"; OFF thì 4 ô giờ = null)
{"weekday":5,"day_kind":3,"start_time":"08:00","end_time":"12:00","lunch_start":null,"lunch_end":null}
// ScheduleCreate
{"name":"Hành chính T2–T6 + sáng T7","note":"","is_active":true,"days":[/* đúng 7 DayIn */]}
// ScheduleOut
{"id":3,"name":"…","note":"","is_active":true,"days":[/*7, xếp theo weekday*/],
 "weekly_workdays":5.5,"assignment_count":2,"created_at":"…","updated_at":"…"}
```
Validator `days`: đúng 7 dòng, `weekday` 0..6 không trùng; `day_kind` ∈ enum; OFF → server ép 4 ô giờ về null;
MORNING/AFTERNOON → bắt buộc start<end, CẤM giờ trưa; FULL → bắt buộc start<end, trưa đủ cặp hoặc bỏ cả cặp,
có trưa thì `start < lunch_start < lunch_end < end`; giờ làm của ngày > 0. `name` `max_length=150`, `note` 500.

**Gán lịch — khóa `work_schedule`**
| Method | Path | Quyền |
|---|---|---|
| GET | `/api/work-schedule-assignments?target_level=&target_id=&schedule_id=&page=…` | read |
| GET/PATCH/DELETE | `/api/work-schedule-assignments/{id}` | read/write/delete |
| POST | `/api/work-schedule-assignments` | create |
```jsonc
// AssignmentCreate
{"target_level":3,"target_id":12,"schedule_id":3,"effective_from":"2026-11-01","effective_to":null,"note":""}
// AssignmentOut (thêm trường dẫn xuất)
{"id":9,"target_level":3,"target_level_label":"Phòng ban","target_id":12,"target_name":"Phòng Kế toán",
 "schedule_id":3,"schedule_name":"…","effective_from":"2026-11-01","effective_to":null,"note":"","is_current":true}
```
Chốt ghi: `target_level` ∈ enum; SYSTEM ⇒ `target_id == 0`, cấp khác ⇒ `target_id > 0` và bản ghi đích tồn tại
(Company/Department/Employee); `schedule_id` tồn tại (tạo mới / đổi mẫu thì phải `is_active`);
`effective_to >= effective_from`; năm 2000..2100; **chồng khoảng** cùng `(target_level, target_id)` (trừ chính nó)
→ 400 «Đã có lịch «X» gán cho «Y» từ dd/mm/yyyy đến …; đặt "Đến ngày" cho dòng đó trước».
Sắp mặc định `effective_from desc, id desc`. Audit `record(db, user.id, "work_schedule", id, action)` mọi lần ghi.

```jsonc
// EffectiveOut — /tools/effective
{"schedule_id":3,"schedule_name":"…","days":[/*7*/],"weekly_workdays":5.5,"is_fallback":false,
 "level":3,"level_label":"Phòng ban","target_name":"Phòng Kế toán","assignment_id":9,
 "effective_from":"2026-11-01","effective_to":null}
// fallback: schedule_id=0, schedule_name="Mặc định hệ thống (T2–T7, 08:00–17:00)", is_fallback=true, level=0
```

## Related code files
**Create** (`backend/app/modules/work_schedule/`): `day_rules.py`, `resolver.py`, `template_schema.py`,
`assignment_schema.py`, `template_service.py`, `assignment_service.py`, `template_controller.py`, `assignment_controller.py`
**Create tests**: `test/backend/test_lich_lam_viec_luat_ngay.py`, `test_lich_lam_viec_phan_giai.py`, `test_lich_lam_viec_api.py`
**Modify**: `backend/app/main.py` (import + `include_router` ×2)

## Implementation steps
1. `day_rules.py` + test thuần (`test_lich_lam_viec_luat_ngay.py`).
2. Schemas + test tầng schema (`pytest.raises(ValidationError)` — SQLite không ép độ dài).
3. `resolver.py` + `test_lich_lam_viec_phan_giai.py`.
4. Services + controllers; nối `main.py`; test API/service (`test_lich_lam_viec_api.py`).
5. Chạy: `pytest test/backend/test_lich_lam_viec_*.py test_pham_vi_luat_bat_bien.py -q` (BB4: controller gọi `apply_scope/get_scoped` nên không cần khai miễn).

## Test matrix (đi tìm chỗ SAI, không chứng minh đúng)
| Nhóm | Ca |
|---|---|
| day_rules | `work_mask` 4 loại; `worked_hours` khoảng ngoài khung → 0, vắt trưa, `start==end`, ngày OFF → 0; `day_capacity` MORNING=0.5; `weekly_workdays` mẫu T2–T6+sáng T7 = 5.5, toàn OFF = 0 |
| schema | 6 / 8 dòng; weekday trùng; weekday 7 hoặc -1; day_kind 0/5; FULL start>=end; trưa thiếu một nửa; trưa nằm ngoài khung; MORNING kèm trưa; OFF kèm giờ → bị ép null; `name` 151 ký tự; `effective_to < from`; năm 1900/9999; SYSTEM với target_id 5; COMPANY với target_id 0 |
| resolver | không gán gì → FALLBACK; chỉ SYSTEM; EMPLOYEE thắng DEPARTMENT thắng COMPANY; NV `company_id=0` KHÔNG dính dòng `(COMPANY,0)` cài tay vào DB; khoảng vắt qua ranh `effective_to` → ngày trước/sau ra hai mẫu; `effective_to` NULL; dòng kết thúc hôm qua không áp hôm nay; hai dòng chồng cài tay → `effective_from` muộn thắng; mẫu thiếu thứ 6 → fallback ngày đó; mẫu `is_active=False` vẫn áp; đếm truy vấn = 2 cho khoảng 400 ngày |
| service/API | đích không tồn tại → 400; chồng khoảng (trùng mép 1 ngày cũng là chồng) → 400; sát mép (to=31/10, from=01/11) → OK; PATCH chính nó không tự chặn mình; xóa mẫu đang gán → 400; gán mẫu đã tắt → 400; `/tools/effective` NV ngoài phạm vi → 404; `assignment_count` đúng với 0/nhiều dòng |

## Todo
- [x] day_rules + test  - [x] schemas + test  - [x] resolver + test  - [x] services/controllers + main.py + test

## Success criteria
3 tệp test mới xanh; `/docs` hiện 2 nhóm route; `curl` tạo mẫu 7 ngày + gán SYSTEM chạy trên local.

## Risk assessment
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Hai request song song tạo 2 dòng chồng (MySQL không có exclusion constraint) | Thấp × TB | Người dùng ít; resolver có luật hòa tất định |
| `/tools/effective` lộ lịch NV ngoài phạm vi | TB × Thấp | `get_scoped(Employee)` + test |
| Sửa giờ của mẫu đang dùng đổi kết quả tính lại quá khứ | TB × TB | Đơn đã lưu không đổi (`total_days` là cột); FE cảnh báo (phase 4) |

## Security
Ghi gác `require("work_schedule", create/write/delete)`; đọc thẻ hồ sơ gác theo phạm vi nhân sự. Mọi chuỗi có `max_length`.

## Next steps
Phase 3 dùng `load_day_plans` + `day_rules`.

## Câu hỏi mở
- ĐÃ CHỐT 05/10: POST tự đóng dòng «không thời hạn» bắt đầu trước `from` mới (audit); PATCH không bao giờ tự đóng. Cài đặt: `assignment_service.create_assignment`; bài kiểm `test_lich_lam_viec_api.py`.
