# Phase 03 — Backend: nối lịch làm việc vào tính ngày nghỉ phép

## Context links
- `.claude/rules/hr-leave.md` («Số ngày nghỉ chỉ tính ở `workday_service.count_leave_days()`»)
- `backend/app/modules/leave/workday_service.py` (204 dòng) · `leave/constants.py` (`START/END_DAY_CREDIT`, `same_day_credit`, `WORK_*`)
- Người gọi (đã rà hết bằng grep): `leave/request_service.compute_days` + `hourly_days`,
  `leave/request_controller.estimate_days` (`/tools/estimate-days`), `assistant/tools/draft_tool.py:~557-625`
- Test hiện có phải XANH NGUYÊN VẸN, không sửa: `test_nghi_phep_quy_va_ngay_cong.py`, `test_nghi_phep_so_ngay_dau_cuoi.py`,
  `test_assistant_draft_tool.py`, `test_nghi_phep_*` khác

## Overview
Priority P1 trong feature (đây là chỗ đổi số tiền phép) · Status done (05/10/2026) · 5h.
Giữ nguyên ngữ nghĩa «GỢI Ý, người dùng sửa đè được» (`requested > 0`) và «theo giờ không sửa đè».

## Key insights
- Công một ngày = `0.5 × popcount(leave_mask(day) & work_mask(spec))`. Với ngày FULL (mask 3), công
  = `0.5 × popcount(leave_mask)` = **đúng** `session_credit` cũ ở mọi tổ hợp → tương thích tuyệt đối khi chưa gán.
- `leave_mask` dịch thẳng quy ước MỐC ở `constants.py`: ngày đầu `from_session==AFTERNOON → PM`, khác → AM|PM;
  ngày cuối `to_session==MORNING → AM`, khác → AM|PM; cùng một ngày = các nửa từ nửa-bắt-đầu tới nửa-kết-thúc
  (Chiều→Sáng = 0). Ở giữa = AM|PM.
- Theo giờ: mỗi ngày làm việc góp `worked_hours(spec, a, b) / day_hours(spec) × day_capacity(spec)`;
  ngày 8h ra đúng `giờ/8` như cũ. Ngày đầu `[from_time, spec.end)`, ngày cuối `[spec.start, to_time)`, giữa = trọn.
- `exclude_holiday=False` → KHÔNG đọc lịch, mọi ngày dùng `FALLBACK_WEEK[FULL]` (thai sản đếm lịch dương như cũ).
- `compute_days` báo lỗi khi tổng 0 — câu cũ nhắc «cuối tuần»; đổi thành «không có ngày làm việc nào theo lịch làm việc
  áp cho «tên NV» (hoặc rơi vào ngày lễ)».

## Architecture — chữ ký mới (tương thích ngược)
```python
def count_leave_days(db, from_date, to_date, from_session=SESSION_FULL, to_session=SESSION_FULL,
                     *, company_id=0, exclude_holiday=True, employee: Employee | None = None) -> float
def count_hourly_days(db, from_date, to_date, from_time, to_time,
                      *, company_id=0, exclude_holiday=True, employee: Employee | None = None) -> float
def schedule_name_on(db, employee, on_date) -> str   # cho estimate-days
```
`employee` có → lấy `employee.id/department_id/company_id` (company_id kw vẫn dùng cho NGÀY LỄ như cũ, mặc định
`employee.company_id`). `employee=None` (bài test cũ) → chỉ SYSTEM + `company_id` → không gán gì = FALLBACK = số cũ.
Bỏ `WEEKEND_DAYS`, `is_working_day`, `session_credit`, `worked_hours` cũ (grep: không ai ngoài tệp dùng).
`MAX_RANGE_DAYS`, `holiday_dates`, `date_range` giữ nguyên tên (draft_tool + request_service đọc `MAX_RANGE_DAYS`).

Giữ < 200 dòng: tách `holiday_dates` + `date_range` + `MAX_RANGE_DAYS` sang `leave/holiday_calendar.py`,
`workday_service` import lại (tên `workday_service.MAX_RANGE_DAYS` vẫn tồn tại cho người gọi).

## Related code files
**Create**: `backend/app/modules/leave/holiday_calendar.py`, `test/backend/test_lich_lam_viec_tinh_ngay_nghi.py`
**Modify**
- `backend/app/modules/leave/workday_service.py` — viết lại hai hàm đếm theo `load_day_plans`; docstring đầu tệp bỏ đoạn «chỉ Chủ nhật»
- `backend/app/modules/leave/constants.py` — XÓA `WORK_DAY_START/END`, `LUNCH_START/END`, `WORK_HOURS_PER_DAY`
  (nguồn giờ mặc định dời sang `work_schedule/day_rules.FALLBACK_WEEK`); sửa chú thích `UNIT_HALF_DAY/UNIT_HOUR` («chờ Lịch làm việc» → đã có)
- `backend/app/modules/leave/request_service.py` — `compute_days`/`hourly_days` truyền `employee=`; câu lỗi giờ không còn in hằng số
- `backend/app/modules/leave/request_controller.py` — `estimate_days` truyền `employee=`, trả thêm `schedule_name` (thêm trường, không đổi trường cũ)
- `backend/app/modules/assistant/tools/draft_tool.py` — `kwargs` thêm `employee=emp`

## Data flow
`estimate-days(employee_id)` → `resolve_leave_taker` → `Employee` → `count_*(…, employee=emp)` →
`load_day_plans(emp, from, to)` [2 truy vấn] + `holiday_dates(company)` [1 truy vấn] → vòng ngày → `{total_days, schedule_name}`.
Lưu đơn: `compute_days` → cùng đường → `total_days` lưu cột (đơn cũ KHÔNG bị tính lại khi lịch đổi).

## Implementation steps
1. Tách `holiday_calendar.py` (cắt-dán, không đổi logic); chạy 2 test ngày công cũ → xanh.
2. Viết `leave_mask(day, from, to, fs, ts)` + vòng đếm mới; xóa hằng số cũ; sửa 3 người gọi.
3. Viết test mới; chạy bộ: `pytest test/backend/test_lich_lam_viec_tinh_ngay_nghi.py test_nghi_phep_quy_va_ngay_cong.py
   test_nghi_phep_so_ngay_dau_cuoi.py test_nghi_phep_nhieu_loai.py test_nghi_phep_don_va_duyet.py test_assistant_draft_tool.py -q`.
4. `grep -rn "WORK_HOURS_PER_DAY\|WORK_DAY_START\|WEEKEND_DAYS" backend test` → chỉ còn chú thích migration cũ.

## Test matrix — `test_lich_lam_viec_tinh_ngay_nghi.py`
| Ca | Kỳ vọng |
|---|---|
| **Tương đương**: chưa gán gì, tham số hóa 3×3 buổi (FULL/MORNING/AFTERNOON) × ngày bắt đầu T2..CN × độ dài 1/2/8 ngày | `== công thức cũ` (chép `session_credit` + `WEEKEND_DAYS=(6,)` vào test làm «bản tham chiếu đóng băng») |
| Mẫu T2–T6 FULL + T7 MORNING + CN OFF, nghỉ trọn T7 | **0.5** |
| Cùng mẫu, nghỉ T6→T2 (Cả ngày→Cả ngày) | 1 + 0.5 + 0 + 1 = **2.5** |
| Bắt đầu T7 buổi Chiều (T7 chỉ sáng) | ngày T7 góp **0** |
| T7 Sáng→Sáng một ngày | 0.5; T7 Chiều→Chiều | 0 → `compute_days` 400 |
| Lịch đổi giữa khoảng (dòng A tới 31/10, dòng B từ 01/11) | mỗi ngày theo dòng của ngày đó |
| NV có gán EMPLOYEE, phòng có gán khác | theo EMPLOYEE |
| Theo giờ trên T7 sáng 08–12: 10:00→12:00 | 2/4 × 0.5 = **0.25** |
| Theo giờ T2 8h 08:00→17:00 | **1.0**; ngày FULL 7h (08–16) nghỉ trọn | **1.0** |
| Theo giờ rơi ngày OFF / ngoài khung / trong giờ trưa | 0 |
| `exclude_holiday=False` + mẫu toàn OFF, 7 ngày | **7.0** (bỏ qua lịch) |
| Ngày lễ trùng ngày làm | vẫn bị trừ như cũ |
| Mẫu toàn OFF + `requested=2` | trả 2 (sửa đè vẫn thắng); `requested=0` → 400 |
| `to < from` | 0.0, không nổ |
| Đếm truy vấn `count_leave_days` 400 ngày có employee | ≤ 3 |
| draft_tool với NV có lịch T7 nửa ngày | `days` khớp `count_leave_days` |

## Todo
- [x] tách holiday_calendar  - [x] leave_mask + vòng đếm  - [x] bỏ hằng số + sửa 3 người gọi  - [x] test mới + bộ cũ xanh

## Success criteria
Mọi test nghỉ phép cũ xanh KHÔNG sửa dòng nào; test mới xanh; `estimate-days` trả `schedule_name`.

## Risk assessment
| Rủi ro | K×T | Giảm thiểu |
|---|---|---|
| Lệch số âm thầm so với hôm nay | TB × **Cao** (tiền phép) | Bài tương đương đóng băng công thức cũ |
| Quên một người gọi → tính theo FALLBACK cho NV có lịch riêng | TB × Cao | Grep bước 4 + test draft_tool |
| Trùng truy vấn trong vòng lặp | Thấp × TB | Test đếm truy vấn |

## Rollback
Revert phase này = luật cứng cũ trở lại; bảng lịch vô hại. Không có migration ở phase này.

## Next steps
Phase 5 đọc `schedule_name`. Phase 6 cập nhật `17-nghi-phep.md`.

## Câu hỏi mở
- Đơn NHÁP cũ mở ra sửa sẽ được gợi ý số mới theo lịch mới — chấp nhận (plan) hay giữ số cũ?
- NV điều chuyển phòng: dùng phòng HIỆN TẠI cho cả khoảng quá khứ (plan), không đọc `tab_employee_work_history`.
