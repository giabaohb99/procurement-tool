---
title: "Nhân sự — Lịch làm việc (mẫu lịch tuần + gán 4 cấp + nối vào tính ngày nghỉ phép)"
description: "Mẫu lịch tuần 7 ngày (cả ngày / nửa ngày / nghỉ), gán theo hệ thống·pháp nhân·phòng ban·nhân sự có ngày hiệu lực; workday_service đọc lịch thay cho WEEKEND_DAYS cứng."
status: pending
priority: P2
effort: 31h
branch: erp-v2
tags: [hrm, leave, work-schedule, backend, frontend-v2, migration, permissions]
created: 2026-10-05
---

# Lịch làm việc (work schedule)

Hôm nay `workday_service` cứng `WEEKEND_DAYS=(6,)` + giờ 08–17 cho mọi pháp nhân. Thay bằng lịch
của chính người nghỉ, theo TỪNG NGÀY trong khoảng nghỉ. Chưa gán gì → ra **đúng từng số** như cũ.

## Quyết định kiến trúc

| # | Quyết định | Lý do |
|---|---|---|
| A1 | Phân hệ backend RIÊNG `app/modules/work_schedule/`; `leave` gọi sang (một chiều) | Khái niệm Nhân sự, khóa quyền riêng; `leave/` đã 4.6k dòng |
| A2 | 3 bảng: `tab_work_schedule` · `tab_work_schedule_day` (7 dòng/mẫu) · `tab_work_schedule_assignment` | Cột có kiểu + UNIQUE dưới DB, không JSON |
| A3 | `WorkDayKind` (OFF/FULL/MORNING/AFTERNOON) + `WorkScheduleLevel` (SYSTEM/COMPANY/DEPARTMENT/EMPLOYEE) IntEnum ở `core/work_schedule_codes.py` → `gen_status_ts` | R2/QĐ-11 |
| A4 | Nửa ngày = **loại ngày**, không suy từ giờ. Công 1 ngày = 0.5 × số nửa-buổi (nghỉ ∩ làm) | Khớp tuyệt đối quy ước `START/END_DAY_CREDIT`; T7 sáng = 0.5 |
| A5 | Theo giờ: giờ nghỉ ÷ giờ làm CỦA NGÀY ĐÓ × sức chứa ngày (1 hoặc 0.5). Bỏ `WORK_HOURS_PER_DAY` | Ngày ngắn (T6 7h) nghỉ trọn vẫn = 1.0; ngày 8h ra y như cũ |
| A6 | Mặc định hệ thống = gán cấp SYSTEM (có ngày hiệu lực); không có → `FALLBACK_WEEK` trong mã (T2–T7 08–17) | Một cơ chế duy nhất; local/test rỗng vẫn chạy như cũ |
| A7 | Thứ tự thắng: EMPLOYEE > DEPARTMENT (phòng CHÍNH `employee.department_id`) > COMPANY (`employee.company_id`) > SYSTEM > fallback | Phòng kiêm nhiệm bỏ qua — một người một lịch |
| A8 | Cùng (cấp, đối tượng) CẤM chồng khoảng ngày. **Ngoại lệ (chốt 05/10)**: TẠO gán mới mà đối tượng đang có dòng «không thời hạn» bắt đầu TRƯỚC `from` mới → tự đặt `effective_to = from − 1` cho dòng cũ (cùng transaction, ghi audit). Mọi chồng khác → 400 kèm tên dòng trùng | HR đổi lịch một thao tác; phân giải vẫn tất định |
| A9 | `exclude_holiday=False` (thai sản) → bỏ qua lịch, đếm lịch dương như cũ | Giữ nguyên nghĩa cột `LeaveType.exclude_holiday` |
| A10 | Khóa quyền `work_schedule` (ENTITIES 71→72), `PUBLIC` ở `SCOPE_FIELDS` | Danh mục cấu hình; đích gán đa hình không hợp khuôn một-cột |
| A11 | Thẻ lịch trên hồ sơ gác `employee.read` + `get_scoped(Employee)`, KHÔNG đòi `work_schedule.read` | Prod không tự cấp khóa mới cho vai trò cũ (D-018) |
| A12 | FE dùng `shared/crud` (`CrudListPage`/`CrudDetailPage`) + ô `type:'custom'` cho bảng 7 ngày | Cùng khuôn holiday/leave-type; backend viết tay nhưng giữ hợp đồng `{total, items}` |

## Quyết định đã chốt với đại ca (05/10/2026) — ĐÈ lên mọi chỗ khác trong phase files

1. Gán chồng lên dòng «không thời hạn» → **tự đóng dòng cũ** ở ngày `from − 1` (xem A8). Chỉ khi TẠO, chỉ dòng có `effective_to IS NULL` và `effective_from < from` mới; còn lại vẫn 400. Nếu lịch mới CÓ «Đến ngày» (lịch tạm) → dòng cũ còn được **nối lại** «không thời hạn» từ `to + 1` (ghi audit), để hết tạm thì quay về lịch cũ chứ không tụt xuống cấp rộng hơn.
2. **Seed sẵn một mẫu** «Hành chính T2–T7» (T2–T7 FULL 08:00–17:00 nghỉ trưa 12:00–13:00, CN OFF) — chèn **trong migration** (chạy đúng một lần, HR xóa/sửa thì không bị seed hồi sinh). KHÔNG gán cho ai → số nghỉ phép không đổi.
3. Quyền SỬA (`read·create·write·delete`): `hr_leave` **và `hr_profile`**. Mọi vai trò khác chỉ `read`.
4. Phòng ban/pháp nhân để phân giải = **hiện tại** của nhân sự (`employee.department_id` / `company_id`), không tra quá trình công tác. Phòng kiêm nhiệm bỏ qua.
5. Lịch nghỉ không tô ngày không làm (để sau). Đơn nháp mở lại được gợi ý theo lịch mới — chấp nhận.

## Phases

| # | Phase | Owner | Effort | Blocked by | Status |
|---|---|---|---|---|---|
| 1 | [Nền backend: bộ mã, model, migration, quyền, seed](phase-01-backend-nen-bo-ma-model-migration-quyen.md) | BE | 4h | — | done |
| 2 | [Backend: luật ngày, phân giải, API mẫu + gán](phase-02-backend-luat-ngay-phan-giai-api.md) | BE | 8h | 1 | done |
| 3 | [Backend: nối vào tính ngày nghỉ phép](phase-03-backend-noi-tinh-ngay-nghi-phep.md) | BE | 5h | 2 | done |
| 4 | [Frontend: màn Mẫu lịch tuần + Gán lịch](phase-04-frontend-mau-lich-va-gan-lich.md) | FE | 9h | 1 (code), 2 (chạy thật) | done |
| 5 | [Frontend: thẻ lịch trên hồ sơ + chữ ở form nghỉ](phase-05-frontend-the-ho-so-va-form-nghi.md) | FE | 3.5h | 4, 3 | done |
| 6 | [Tài liệu + nhật ký task](phase-06-tai-lieu-nhat-ky.md) | BE/lead | 1.5h | 3, 5 | pending |

Song song: BE làm 1→2→3; FE bắt đầu phase 4 ngay khi phase 1 xong (hợp đồng API ở phase 2 §API).
Không hai phase nào sửa chung một tệp — bảng sở hữu ở từng phase.

## Luồng dữ liệu

```
HR sửa mẫu/gán ──► /api/work-schedules, /api/work-schedule-assignments ──► 3 bảng
Form nghỉ / trợ lý AI / lưu đơn ──► workday_service.count_*(…, employee)
   └► resolver.load_day_plans(employee, from, to)  [2 truy vấn cố định]
        └► mỗi ngày: DaySpec ─► leave_mask ∩ work_mask ─► công; trừ lễ (holiday_dates)
Hồ sơ NV ──► /api/work-schedules/tools/effective?employee_id ──► thẻ «Lịch làm việc»
```

## Rủi ro chính
- Lệch số so với hôm nay khi chưa gán gì → bài kiểm TƯƠNG ĐƯƠNG mọi tổ hợp buổi × 7 thứ (phase 3).
- Sửa mẫu đang dùng đổi cả tính lại quá khứ (đơn đã lưu KHÔNG đổi — `total_days` là cột) → cảnh báo trên form.
- Đổi đích gán ở FE giữ nhầm `target_id` cũ → ô đích tự xóa khi đổi cấp + backend kiểm đích có thật.

## Rollback
Revert phase 3 = về luật cứng cũ (bảng còn đó, vô hại). Xóa hết dòng gán = hành vi cũ y nguyên.
Migration `downgrade` xóa 3 bảng. FE revert độc lập (menu gác `manage`).

## Câu hỏi còn mở → cuối mỗi phase + tổng hợp ở phase 6.
