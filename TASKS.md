# TASKS — Tiến độ triển khai (làm tới đâu tick tới đó)

## Phase 0 — Nền tảng
- [x] Cấu trúc dự án (feature-based) + docker-compose (file tổng) + hot reload
- [x] core: config · database · base_model · response · auth(JWT+RBAC) · permissions · base_controller
- [x] Đăng nhập nội bộ (mã NV + mật khẩu) + JWT + `/api/auth/me`
- [x] Danh sách quyền config (`core/permissions.py`) + RBAC `require(entity, action)`
- [x] Seed admin `degoadmin` / `dego2026` (full quyền) + role `admin`
- [x] Module: company (CRUD) · department (CRUD) · employee (CRUD)
- [x] Module: role (list/create + ma trận quyền + meta) · user (cấp tài khoản, đổi mật khẩu, gán vai trò)
- [x] Frontend: login · layout · trang Công ty · trang Nhân viên
- [x] Chạy thử `docker compose up`, sửa lỗi phát sinh (môi trường thật)
- [ ] Alembic migration (thay cho create_all) — `migrations/`
- [ ] Màn cấu hình phân quyền (FE) dùng `/api/roles/{id}/permissions` + `/meta`
- [ ] Google OAuth (sau)

## Cross-cutting (áp dụng mọi module — xem doc/FEATURE_CHECKLIST.md)
- [x] Filter động (FE FilterBar + BE apply_filters)
- [x] Responsive điện thoại (sidebar drawer + bảng cuộn ngang)
- [x] Adminer xem DB (http://localhost:8081)
- [x] Data mẫu seed từ DATA CHUNG
- [x] Trang chi tiết theo route (/:entity/:id) — không popup, có form sửa/xóa
- [x] Audit log (tab_audit_log): ai/làm gì/khi nào — hiển thị timeline ở trang chi tiết
- [x] Import data thật từ Excel (tools/import_excel.py)
- [x] Phân trang (page + limit 10/20/50/100)

## Phase 1 — Danh mục + Khảo sát
- [x] Supplier (có `supplier_type` goods/transport) + data mẫu + filter
- [x] Product (VTBB/NL) + data mẫu + filter
- [x] Dashboard trang chủ (thẻ chỉ số + shortcut + biểu đồ xu hướng/cơ cấu trạng thái) — khớp mockup & phân tách rõ ràng
- [x] Purchase Request (PYC): header + bảng items + luồng Nháp→Gửi duyệt→Duyệt/Từ chối + log + đính kèm báo giá/chứng từ riêng biệt
- [ ] Unit / Unit conversion (Sheet 5)
- [ ] Survey (form chính + bảng con supplier/product) + LAB result
- [ ] Email cơ bản (giao việc, chờ duyệt, kết quả)

## Phase 2 — Mua hàng + Nhận hàng (GR)
- [ ] Purchase Order (+ items) · duyệt theo ngưỡng · in PO (PDF)
- [ ] PO Delivery (giao nhiều lần) + vận chuyển (chi phí riêng)
- [ ] Goods Receipt + QC + tồn kho (theo company)

## Phase 3 — Cảnh báo & thông báo (Celery + Redis)
- [ ] Celery worker + beat + Redis (thêm service docker)
- [ ] Cảnh báo trễ hạn, nhắc D-1, công nợ, HĐ hết hạn
- [ ] Báo cáo chạy ngầm (bảng snapshot)

## Phase 4 — Công nợ · Báo cáo · Hợp đồng
- [ ] Công nợ 2 luồng (hàng/vận chuyển) + thanh toán gom (nút trên màn + đính kèm)
- [ ] Báo cáo tiến độ/KPI/chi phí · Hợp đồng + cảnh báo hết hạn

## Phase 5 — Quản trị nâng cao
- [ ] Cấu hình duyệt theo ngưỡng · mẫu in · audit log UI · sao lưu
- [ ] Đính kèm R2 + xem bộ chứng từ theo đơn

---
**Đăng nhập:** `degoadmin` / `dego2026` (đổi qua `.env`). Web: http://localhost:8080 · API: http://localhost:8000/docs
