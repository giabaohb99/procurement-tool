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
- [x] Alembic migration (thay cho create_all) — `backend/migrations/` · start.sh chạy `alembic upgrade head` trước seed
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
- [x] Survey NCC + SP (form + bảng con inline đủ cột Sheet 3/4 + LAB + duyệt)
- [ ] Email cơ bản (giao việc, chờ duyệt, kết quả)

## Phase 2 — Mua hàng + Nhận hàng (GR) + Tồn + Công nợ + Thanh toán
- [x] Purchase Order (header + items) · luồng Nháp→Gửi→Duyệt/Từ chối · in PO (A4 ngang)
- [x] PO Delivery (giao nhiều lần, trong popup từng dòng) + vận chuyển (cước riêng) + đính kèm phiếu giao
- [x] Goods Receipt ngầm + QC + tồn kho theo company/kho (chỉ nhập + điều chỉnh tay)
- [x] Công nợ tự sinh 2 luồng (hàng/vận chuyển) + màn Công nợ (tuổi nợ, filter, summary)
- [x] Yêu cầu thanh toán (1 NCC/phiếu, gom nhiều PO, tự tách theo NCC, in được)
- [ ] Duyệt PO theo ngưỡng (đang dùng luồng duyệt cơ bản; ngưỡng để Phase 5)

## Phase 3 — Cảnh báo & thông báo (Celery + Redis)
- [ ] Celery worker + beat + Redis (thêm service docker)
- [ ] Cảnh báo trễ hạn, nhắc D-1, công nợ, HĐ hết hạn
- [ ] Báo cáo chạy ngầm (bảng snapshot)

## Phase 4 — Công nợ · Báo cáo · Hợp đồng
- [x] Công nợ 2 luồng (hàng/vận chuyển) + yêu cầu thanh toán gom + đính kèm (làm sớm ở Phase 2)
- [x] Báo cáo mua hàng (1 màn nhiều tab: Tổng quan/NCC/Phân loại/NSPT/Bộ phận/Vận chuyển/Tồn) — precompute snapshot (`tab_report_snapshot`) + nút Cập nhật + In. Xem `doc/Requirement_BaoCao_MuaHang.md`
- [ ] Lịch tự refresh snapshot báo cáo (Phase 3 worker) · Hợp đồng + cảnh báo hết hạn

## Phase 5 — Quản trị nâng cao
- [ ] Cấu hình duyệt theo ngưỡng · mẫu in · audit log UI · sao lưu
- [ ] Đính kèm R2 + xem bộ chứng từ theo đơn

---
## Quy trình đổi cấu trúc DB (Alembic) — KHÔNG drop bảng tay nữa
1. Sửa model (`app/modules/**/model.py`) + thêm import vào `app/core/all_models.py` nếu là model mới.
2. Sinh migration:  `docker compose exec api sh -c "cd /app && alembic revision --autogenerate -m 'mo ta'"`
3. Áp dụng:        `docker compose exec api sh -c "cd /app && alembic upgrade head"`  (start.sh cũng tự chạy khi khởi động)
4. Kiểm tra khớp:  `docker compose exec api sh -c "cd /app && alembic check"`  → "No new upgrade operations detected"
- Lùi 1 bước: `alembic downgrade -1`. Migration lưu ở `backend/migrations/versions/`.

---
**Đăng nhập:** `degoadmin` / `dego2026` (đổi qua `.env`). Web: http://localhost:8080 · API: http://localhost:8000/docs
