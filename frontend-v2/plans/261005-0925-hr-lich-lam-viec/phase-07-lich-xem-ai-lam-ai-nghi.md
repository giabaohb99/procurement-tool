# Phase 07 — Màn «Lịch làm việc» dạng lịch: nhìn vào biết ngày nào ai làm, ai nghỉ

Yêu cầu đại ca 05/10/2026: «lịch làm việc hiện dạng schedule, nhìn vô biết ngày nay ai làm ai nghỉ».

## Quyết định đã chốt (05/10/2026)
1. Mặc định xem **TUẦN** (T2→CN của tuần chứa hôm nay), có nút chuyển sang **THÁNG**.
2. Nghỉ phép hiện **cả đơn ĐÃ DUYỆT lẫn CHỜ DUYỆT** — đã duyệt tô đặc, chờ duyệt viền nét đứt. Nghỉ nửa buổi chỉ tô nửa ô.
3. Phạm vi: hàng = nhân sự trong phạm vi `employee.read` của người xem (`apply_scope(Employee,'employee')`).
   Lớp nghỉ phép chỉ hiện nếu người xem cũng đọc được đơn đó (`apply_scope(LeaveRequest,'leave_request')` + nới
   «đang có việc duyệt trên đơn» KHÔNG cần). Không đọc được đơn → ô hiện như ngày làm bình thường theo lịch.

## Hợp đồng API (khóa cứng — BE và FE làm song song theo đây)

`GET /api/work-schedules/tools/roster` — gác `require("employee","read")` (giống `/tools/effective`).

Tham số: `from_date`, `to_date` (YYYY-MM-DD, bắt buộc; `to >= from`; tối đa **42 ngày** → 422/400 rõ nghĩa;
năm 2000..2100), `company_id` (0 = mọi), `department_id` (0 = mọi), `q` (tìm theo mã/tên NV, ≤100 ký tự),
`page` (≥1), `page_size` (1..100, mặc định 50). Chỉ nhân sự CHƯA nghỉ việc trước `from_date`
(xem cách danh sách nhân sự lọc «đang làm» — dùng đúng cột/luật đó). Sắp theo phòng ban rồi tên.

```json
{
  "from_date": "2026-10-05", "to_date": "2026-10-11",
  "days": [{"date": "2026-10-05", "weekday": 0, "holiday_name": ""}],
  "total": 123,
  "items": [{
    "employee_id": 253, "code": "admin", "full_name": "Quản trị viên",
    "department_id": 4, "department_name": "Lập trình & IT nội bộ",
    "cells": [{
      "date": "2026-10-05",
      "work_kind": 2,                 // WorkDayKind: 1 Nghỉ · 2 Cả ngày · 3 Buổi sáng · 4 Buổi chiều (theo lịch hiệu lực NGÀY ĐÓ)
      "start_time": "08:00", "end_time": "17:00",
      "schedule_name": "Hành chính T2–T7",
      "is_holiday": false,
      "leave": null                   // hoặc {"request_id": 12, "code": "NP012", "leave_type_name": "Phép năm",
                                      //       "status": 3, "status_label": "Đã duyệt", "is_approved": true,
                                      //       "morning": true, "afternoon": false}
    }]
  }]
}
```
- `leave.morning/afternoon`: nửa buổi nào của NGÀY ĐÓ bị nghỉ (dùng chính luật mốc buổi của
  `workday_service` — `leave_mask` — không chép công thức). Nhiều đơn chồng cùng ngày: ưu tiên đơn đã duyệt.
- Trạng thái lấy: đã duyệt + đang chờ duyệt (xem mã ở `leave/constants.py`); nháp/từ chối/hủy/rút KHÔNG lấy.
- Ngày lễ: theo `holiday_dates` của pháp nhân của người đó (dòng chung + dòng riêng).

## Hiệu năng (bắt buộc — xem memory «API báo cáo phải nhanh nhất»)
Số truy vấn **cố định**, không phụ thuộc số nhân sự × số ngày: trang nhân sự (+count), gán lịch gom cho mọi
đích (nhân sự/phòng ban/pháp nhân/hệ thống) 1 truy vấn, mẫu + 7 ngày 1–2, ngày lễ 1, đơn nghỉ + dòng 1–2.
Cần bản GOM của resolver (`resolver.load_day_plans_many(...)`) — không gọi resolver từng người. Test đếm truy vấn
cho 5 người × 7 ngày và 50 người × 42 ngày phải bằng nhau.

## Backend — sở hữu tệp
- `backend/app/modules/work_schedule/roster_service.py` (mới), `roster_schema.py` nếu cần, thêm route vào
  `template_controller.py` (hoặc `roster_controller.py` mới + đăng ký `main.py`; nhớ BB4), `resolver.py` (thêm hàm gom).
- `test/backend/test_lich_lam_viec_roster.py` (mới): phạm vi (người ngoài phạm vi không ra; đơn ngoài phạm vi
  leave_request không lộ), nửa buổi, lễ, đơn chờ duyệt vs đã duyệt, nghỉ việc, ranh hiệu lực gán giữa kỳ,
  42 ngày OK / 43 ngày lỗi, đếm truy vấn.

## Frontend — sở hữu tệp
- Trang `modules/hr/pages/work-roster-page.tsx` + components `work-roster-*.tsx`, hook `use-work-roster.ts`,
  api thêm vào `api/work-schedule-api.ts`, utils `work-roster-*.ts` (+ test), route `/hr/work-roster`
  (`appRoutes.hr.workRoster`), query key ở `shared/constants/query-keys.ts`.
- Menu: nhóm «Lịch làm việc» thêm con ĐẦU TIÊN «Lịch tuần» → `/hr/work-roster`, gác `entity: 'employee'`
  (KHÔNG `manage`), mục cha đổi `entities` để người chỉ có `employee.read` vẫn thấy nhóm; hai con cũ giữ `manage`.
  Cập nhật `module-visibility.test.ts`.
- Bố cục: thanh công cụ (Tuần/Tháng · ‹ Hôm nay › · nhãn kỳ · lọc Pháp nhân/Phòng ban · tìm), chú giải màu,
  lưới cột tên dính trái + cột ngày (hôm nay nổi bật, ngày lễ/CN nền khác), gom hàng theo phòng ban,
  hàng tổng đầu bảng «Đang làm x / Nghỉ y» theo từng ngày (tính trên trang đang xem).
  Ô tuần: chữ ngắn («08–17», «Sáng», «Nghỉ tuần», «Lễ», «Phép năm») + tô; Ô tháng: chỉ màu + ký hiệu 1 chữ,
  tooltip đầy đủ. Ô có đơn nghỉ bấm được → `/hr/leave-requests/:id`.
  Khổ điện thoại: chọn MỘT ngày → danh sách nhân sự chia hai nhóm «Đi làm» / «Nghỉ» (không ép lưới).
- Màu dùng token ngữ nghĩa trong `src/index.css` (thêm biến cả `:root` lẫn `.dark` nếu cần), không hex rời.
- Phân trang thật (page_size 50), không tải cả công ty một lần.

## Todo
- [x] BE: resolver gom + roster_service + route + test
- [x] FE: api/hook/utils + lưới tuần/tháng + mobile + menu + test
- [ ] Kiểm trên trình duyệt (desktop + emulate 390px)
