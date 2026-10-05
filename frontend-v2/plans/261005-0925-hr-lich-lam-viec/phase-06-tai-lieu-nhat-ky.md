# Phase 06 — Tài liệu, luật cho trợ lý, nhật ký task

## Context links
- `doc/tai-lieu-chuc-nang/17-nghi-phep.md` · `.claude/rules/hr-leave.md` · `doc/tai-lieu-ky-thuat/nhat-ky-task.md`
  (đọc luật viết mô tả ở đầu sổ: câu tiếng Việt trọn vẹn, tên tệp dồn xuống dòng `Mã nguồn:`)

## Overview
Priority P3 · Status pending · 1.5h · làm sau khi phase 3 + 5 xong.

## Related code files (sở hữu phase 6)
**Create**: `doc/tai-lieu-chuc-nang/21-lich-lam-viec.md` (số kế tiếp sau 20; kiểm lại `README.md` mục lục)
**Modify**: `doc/tai-lieu-chuc-nang/README.md` (mục lục) · `doc/tai-lieu-chuc-nang/17-nghi-phep.md` (mục cách đếm ngày:
bỏ «chỉ Chủ nhật», trỏ sang 21) · `.claude/rules/hr-leave.md` (1 gạch đầu dòng, xem dưới) ·
`doc/tai-lieu-ky-thuat/nhat-ky-task.md` (1 mục)

## Nội dung bắt buộc
`21-lich-lam-viec.md`: mẫu lịch tuần (4 loại ngày, T7 nửa ngày = 0,5); 4 cấp + thứ tự thắng; ngày hiệu lực + luật
cấm chồng; FALLBACK khi chưa gán; `exclude_holiday=False` bỏ qua lịch; sửa mẫu đang dùng ảnh hưởng gì (đơn đã lưu
KHÔNG đổi); phòng kiêm nhiệm không tính; **prod: khóa `work_schedule` chỉ `admin` tự có — HR phải tick ở Phân quyền
hoặc `SEED_FORCE_SYNC=true` một lần (D-018)**.

`hr-leave.md` thêm: «⚠️ Số ngày theo LỊCH LÀM VIỆC của người nghỉ (`work_schedule/resolver.load_day_plans`), không còn
`WEEKEND_DAYS`. Gọi `count_leave_days/count_hourly_days` PHẢI truyền `employee=` — quên là tính theo lịch mặc định
cho người có lịch riêng, sai âm thầm.»

## Implementation steps
1. Viết tài liệu. 2. Thêm luật. 3. Ghi sổ nhật ký → `python backend/scripts/sync_task_journal.py` theo hướng dẫn ở sổ.

## Todo
- [ ] 21-lich-lam-viec.md + mục lục  - [ ] 17-nghi-phep.md  - [ ] hr-leave.md  - [ ] nhật ký task

## Success criteria
Người đọc tài liệu trả lời được: «NV X nghỉ T7 bị trừ mấy ngày và vì sao».

## Câu hỏi mở tổng hợp (cần đại ca chốt trước/trong khi làm)
1. Ngoài `hr_leave`, `hr_profile` có quyền SỬA lịch không? (plan: chỉ read)
2. Gán mới khi dòng cũ còn «không thời hạn»: chặn + báo (plan) hay tự đóng dòng cũ ở ngày trước?
3. Có tạo sẵn mẫu «T2–T7 08:00–17:00» bằng seed/migration cho HR bắt đầu? (plan: không — fallback trong mã)
4. NV điều chuyển: dùng phòng/pháp nhân HIỆN TẠI cho cả quá khứ (plan) hay đọc quá trình công tác?
5. Phòng kiêm nhiệm bị bỏ qua — đúng ý?
6. Màn «Lịch nghỉ» có cần tô ngày nghỉ theo lịch (T7 chiều) không? (plan: chưa)
7. Đơn NHÁP cũ mở lại sẽ được gợi ý số theo lịch mới — chấp nhận?
