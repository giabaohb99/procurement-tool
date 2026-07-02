# Checklist chuẩn cho MỖI chức năng (Definition of Done)

Mỗi module/chức năng phải đạt đủ các mục sau trước khi coi là xong:

## Backend (module = 1 thư mục: controller · model · schema · service)
- [ ] Model theo quy ước DB (id BIGINT, `tab_` prefix, code varchar 25/50, note/json TEXT, `parent=0`, đủ cột kiểm toán)
- [ ] CRUD: list (phân trang) · detail · create · update · delete
- [ ] **Filter động** (whitelist trường lọc trong service, dùng `apply_filters`)
- [ ] **Phân quyền** trên mọi endpoint (`require(entity, action)`: read/create/write/delete...)
- [ ] JSON trả về chuẩn (`success()` / `error()`)
- [ ] Đăng ký router ở `main.py`

## Frontend (View)
- [ ] Trang list + **FilterBar động** + bảng (badge trạng thái) + nút theo quyền (`can()`)
- [ ] Form tạo/sửa + validate + báo lỗi
- [ ] **Responsive** (chạy tốt trên điện thoại — sidebar drawer, bảng cuộn ngang)
- [ ] Mục menu trong sidebar

## Dữ liệu & vận hành
- [ ] **Data mẫu** seed (lấy cột tương ứng từ DATA CHUNG / DATA NL-VTBB)
- [ ] **Đính kèm chứng từ** (khi áp dụng) — lưu R2
- [ ] Audit log (ai tạo/sửa)
- [ ] Cập nhật `TASKS.md`

> Ghi chú: Yêu cầu thanh toán (payment) **gom được nhiều đơn hàng** (1 phiếu ↔ nhiều công nợ qua `tab_payment_line`).
