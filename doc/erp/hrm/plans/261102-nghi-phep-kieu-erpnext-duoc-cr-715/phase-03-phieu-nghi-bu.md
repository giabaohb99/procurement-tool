# Giai đoạn C — Phiếu xin nghỉ bù (Compensatory Leave Request)

## Quyết định thiết kế
1. Khóa quyền mới `leave_comp_request` (ENTITIES +1): `SCOPE_FIELDS` giống `leave_request` (owner `created_by` + self
   `employee_id`, chặn `employee_id = 0`); nhãn quyền; seed cấp như `leave_request` (KHÔNG rơi vào quyền của Quản lý thu
   mua — xem bẫy `_SYS_ENTITIES` ở `.claude/rules/hr-employee-profile.md`); `task_notification.ENTITY_LABELS` + `ENTITY_LINKS`;
   test đếm entity cập nhật.
2. Cờ `tab_leave_type.is_compensatory` BOOL default False — loại nhận ngày bù (đúng một loại đang dùng được bật; nhiều thì
   lấy loại `sort_order` nhỏ nhất, không có thì chặn lập phiếu với câu rõ ràng).
3. Bảng `tab_leave_comp_request(id, code **NB…**, company_id, department_id, employee_id, work_date, days FLOAT 0.5|1,
   reason String(1000), status SMALLINT (bộ mã riêng: nháp / chờ duyệt / đã duyệt / từ chối / trả về / đã hủy),
   approval_instance_id, decided_at, audit)`.
4. Chốt khi lập / gửi: `work_date ≤ hôm nay (vn_today)`; là ngày lễ (`Holiday`) HOẶC ngày nghỉ theo lịch làm việc của
   người đó (`work_schedule.resolver`); một ngày một phiếu (không tính phiếu đã hủy / từ chối); `days ∈ {0.5, 1}`.
5. Luồng duyệt chung (`entity_hooks.register`): duyệt xong cộng `days` vào cột mới `tab_leave_balance.comp_days` của năm
   `work_date`, loại nghỉ bù; `remaining()` cộng `comp_days`. Hủy phiếu ĐÃ DUYỆT chỉ khi còn lại ≥ `days` → trừ lại.
6. Giao diện: mục con **Nghỉ bù** trong menu Nghỉ phép → danh sách (của tôi / cần tôi duyệt), trang lập, trang chi tiết có
   khối duyệt như đơn nghỉ.

## Xong khi
Bài kiểm vòng đời (lập → gửi → duyệt → quỹ tăng; từ chối / rút → quỹ không đổi; hủy sau duyệt trừ lại; ngày làm việc
thường bị chặn; trùng ngày bị chặn; ngày tương lai bị chặn); phạm vi: người khác phòng không đọc được phiếu.
