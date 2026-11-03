# Giai đoạn B — Ngày cấm nghỉ (Leave Block List)

## Quyết định thiết kế
1. Bảng `tab_leave_block_period(id, company_id 0=mọi, department_id 0=mọi, from_date, to_date, reason String(255),
   is_active, audit)`; CRUD `make_crud_router` ở `/api/leave-block-periods`, khóa quyền `leave_type` (cùng **Thiết lập**
   nghỉ phép, không thêm entity). Kẹp: `to_date ≥ from_date`, dài tối đa 366 ngày.
2. `leave/block_period_service.find_conflicts(db, employee, periods) -> list` — khớp pháp nhân / phòng của NGƯỜI NGHỈ,
   giao khoảng ngày bất kỳ khoảng nào của đơn (đọc khoảng qua `period_spans`, không đọc đầu đơn).
3. Lúc LẬP / SỬA: không chặn, trả kèm `block_conflicts` ở serializer đơn + công cụ `/tools/estimate-periods` → form hiện
   khung vàng ngay khi chọn ngày; trang chi tiết cũng hiện.
4. Lúc DUYỆT CHẶNG CUỐI (hook `_on_approved` của `approval_bridge`, dùng chung cho duyệt thẳng): còn xung đột → 422,
   giao dịch cuộn lại, trừ khi người bấm (`instance.updated_by`) có vai trò trong cài đặt mới `leave_block_exempt_roles`
   (kiểu `roles`, tab Nghỉ phép của Cài đặt nhân sự) hoặc `admin`.
5. Giao diện: thêm thẻ **Ngày cấm nghỉ** vào `LeaveSectionTabs` (cạnh Loại nghỉ / Lịch ngày lễ) + trang danh sách CRUD;
   `matchPaths` của mục menu **Thiết lập**.

## Xong khi
Bài kiểm: khớp đúng pháp nhân / phòng / mọi; khoảng ngày giao một phần; đơn nhiều khoảng có khe không dính; cảnh báo
không chặn lưu; duyệt chặng cuối bị chặn, vai trò miễn qua; tắt dòng cấm (`is_active=False`) thì hết chặn.
