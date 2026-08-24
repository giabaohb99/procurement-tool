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
- [~] Phân quyền — **Bước 1 xong**: hành động thêm **Hủy** (`cancel`); scope cấp bậc **own/dept/company/all**; màn **Phân quyền** (`/roles` → RolePermissions: tab Vai trò + Ma trận quyền); seed 6 vai trò chuẩn (Nhân sự/Trưởng phòng/Quản lý cty/NV thu mua/QL thu mua/Admin thu mua). Xem `doc/Thiet_Ke_Phan_Quyen.md`
- [~] Phân quyền — **Bước 2 (lõi xong)**: `perm_cache` in-process + `get_perm_profile` (gộp phạm vi rộng nhất) · `scope_query` own/dept/company/all (`core/scoping.py`) đã áp cho **Yêu cầu mua** (list+chi tiết) · ẩn menu theo quyền Xem · tab **Người dùng** gán vai trò · invalidate cache khi sửa quyền. Đã test: admin thấy tất cả, user scope own bị lọc.
- [~] Phân quyền — **Bước 2 (tiếp)**: đã áp `scope_query` cho **PO · Công nợ · Tồn kho · Thanh toán** (Báo cáo/Dashboard tổng hợp để sau) · **tạo 21 tài khoản phòng Thu mua** (user=pass=mã NV) + gán vai trò (NSU210/NSU215=QL thu mua, NSU224=Admin thu mua, còn lại=NV thu mua) · login bằng email hoặc mã NV
- [~] Phân quyền — **Bước 2 (mô hình GRANT)**: phạm vi theo **(user × vai trò)** — mỗi vai trò gán cho user có phạm vi RIÊNG (công ty/phòng ban/**nhân sự** + loại trừ). Enforcement = HỢP (OR) các grant có quyền (`core/scoping.py`). Bảng `tab_user_scope` (thêm `role_id`). **Trang chi tiết Người dùng** (`/users/:id`) liệt kê vai trò + nút **Phạm vi → popup** (mã/tên ngắn, tìm nhân sự). API `/api/users/{id}` · `/api/users/{id}/roles/{role_id}/scope`. Người dùng list: phân trang 20 + tìm kiếm.
- [ ] Phân quyền — **còn lại (tùy chọn)**: popup phạm vi RIÊNG theo từng quyền (override per-entity) · scope cho Báo cáo/Dashboard · cấp tài khoản hàng loạt cho nhân sự ngoài phòng thu mua · chiều Nhân sự/Kho
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

## Yêu cầu mua — nâng cấp form + luồng (đã xong)
- [x] Bỏ VAT khỏi PYC (tổng = SL×giá); **Ngày cần hàng + Trạng thái xử lý theo TỪNG DÒNG** (`required_date`, `line_status` 7 giá trị)
- [x] Item = **popup chi tiết** (đủ trường như hình) + nút **Copy dòng**; bảng ngoài gọn + badge trạng thái dòng
- [x] "Mô tả phân loại" tự sinh từ Phân loại (Ngày QĐ sẵn/không sẵn); Kho nhận bắt buộc
- [x] NCC đề xuất = ô nhập tay (người YC không xem được DS NCC); fix auto Trưởng bộ phận theo phòng ban (dò role_name)
- [x] Luồng: Nháp→Chờ duyệt→(Trưởng phòng) Đã duyệt→**Đang xử lý** (tự khi có dòng ≠ Chưa đặt hàng)→**Hoàn thành** (tự khi mọi dòng xong)
- [x] Admin/Quản lý: **Hủy / Trả về (Nháp, xóa NSTM, reset dòng) / Hoàn thành** (quyền `cancel`; đã gỡ cancel khỏi Trưởng phòng); dòng "Hủy đơn" → **tô đỏ phiếu** trên danh sách
- [x] Endpoint: `item-status` (NSTM/quản lý) · `cancel` · `return` · `complete`. Fix bug vai trò `ADMINISTRATOR` thiếu `cancel`.

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
- [x] Logic cảnh báo + endpoint `GET /api/alerts` (giao trễ/sắp tới hạn · công nợ đến/quá hạn · HĐ sắp hết hạn) — xem `doc/Requirement_Phase34_UX.md`
- [ ] Celery worker + beat + Redis (thêm service docker) — chạy ngầm: sinh notification/email + tự refresh snapshot báo cáo
- [ ] Chuông thông báo (FE) đọc `/api/alerts` (badge + dropdown)

## Phase 4 — Công nợ · Báo cáo · Hợp đồng
- [x] Công nợ 2 luồng (hàng/vận chuyển) + yêu cầu thanh toán gom + đính kèm (làm sớm ở Phase 2)
- [x] Báo cáo mua hàng (1 màn nhiều tab: Tổng quan/NCC/Phân loại/NSPT/Bộ phận/Vận chuyển/Tồn) — precompute snapshot (`tab_report_snapshot`) + nút Cập nhật + In. Xem `doc/Requirement_BaoCao_MuaHang.md`
- [x] Hợp đồng **tổng quát** (module `contract`: đối tượng NCC/Khách hàng/Khác · công ty ký · đã ký · **đính kèm file thật (R2)** · bỏ giá trị · cảnh báo Còn hạn/Sắp hết hạn/Hết hạn) — trang ContractDetail riêng
- [x] NCC: thêm **Loại NCC** (Công ty/Cá nhân/Hợp danh/Hộ kinh doanh) · người liên hệ/SĐT · **TK ngân hàng**; trang chi tiết NCC 4 tab (Thông tin/Đánh giá/Hợp đồng/Công nợ) đầy đủ thêm-sửa-xóa
- [ ] Lịch tự refresh snapshot báo cáo (Phase 3 worker)

## UX (đợt này)
- [x] Task 1 — Ô search tự lọc khi ngừng gõ (debounce 400ms), bỏ nút Lọc
- [x] Task 7 — Gom sidebar theo cụm (Mua hàng / Kho & Công nợ / Danh mục thu gọn / Hệ thống)
- [x] Task 9 — Trang chi tiết NCC dạng tab (Thông tin · Đánh giá · Hợp đồng · Công nợ)
- [x] Fix `start.sh` bị CRLF làm container crash (chuẩn hóa LF)
- [x] Thiết kế lại giao diện kiểu Horizon: màu theo **logo DEGO** (xanh biển #00AEEF + xanh lá #92C83E), gắn logo vào sidebar, bỏ gradient chói. Xem `doc/Thiet_Ke_Giao_Dien.md`
- [x] Trang chủ "dày thông tin": 6 KPI (đơn chờ duyệt/PO chạy/nợ đến hạn/nợ quá hạn/HĐ sắp hết/mặt hàng hết) + biểu đồ chi phí 12 tháng + donut cơ cấu phân loại + Top NCC + Cảnh báo + Tồn thấp — endpoint `GET /api/dashboard/overview`
- [x] Fix bug `alert.build` còn tham chiếu `Contract.supplier_name` (đã đổi generic → `party_name`)

## Cập nhật Thu mua đợt 2026-07 (CR-007 — xem doc/yeu-cau/Plan_CapNhat_ThuMua_2026_07.md)
Đợt A — nhanh + bugfix:
- [x] Task 1 — Đổi nhãn "Yêu cầu khảo sát"→"Yêu cầu báo giá" (BE+FE) + đổi prefix mã phiếu `YCKS`→`YCBG` (mã dòng `YCKSL`→`YCBGL`), cập nhật test
- [x] Task 10a — Fix bug upload file không hiện (`core/storage.py` R2 URL khi `r2_public_url` rỗng) + cho phép upload chứng từ khi PO `completed`
- [x] Task 6 — Thêm cột "Thời gian dự kiến có hàng" (`expected_date`) ra bảng dòng YCMH (không migration)

Đợt B — luồng khảo sát:
- [x] Task 2 — Trạng thái theo dòng khảo sát: thêm `line_status` (chưa xác định / cần khảo sát lại / hoàn thành) + guard người YC/cùng phòng ban (migration `a2c4e6f8b1d3`)
- [x] Task 3 — Phòng ban người YC được đóng/hoàn thành phiếu khảo sát (nới guard `finalize` → purchaser+approve HOẶC người YC/cùng phòng ban)

Đợt C — đơn mua hàng:
- [x] Task 8 — Thêm trạng thái "Chưa gửi ĐMH cho KT" + trường `document_delivery_date` (dòng); tách bước máy trạng thái tiến độ (PROGRESS_ORDER 6 bước) — migration `b4d6f8a0c2e5`
- [x] Task 10b — Trạng thái hồ sơ chứng từ `document_status` (chưa có / đã có thông tin / đã đủ) cập nhật tay (endpoint `PATCH /{pid}/document-status`, sửa được cả khi Hoàn thành) + hiện ở list ĐMH — migration `b4d6f8a0c2e5`

Đợt D — nghiệp vụ + màn lớn:
- [x] Task 4 — Thêm lại VAT theo dòng YCMH (`vat_pct`, thành tiền gồm VAT tự tính; tổng = tiền hàng + VAT) + phiếu in tách Tiền hàng/VAT/Tổng + chuyển VAT theo dòng khi tạo ĐMH — migration `c6e8a0b2d4f7`
- [x] Task 5 — Ẩn NCC đề xuất theo `supplier.read`: BE che 3 trường `suggested_supplier*` ở list + chi tiết (`_out(db,pr,user)`) · FE ẩn card NCC + khối in khi thiếu quyền · seed xóa `supplier.read` khỏi role `employee`/`staff` (không migration)
- [x] Task 7 — Trang "Tiến độ mua hàng" (bản 1 cột sẵn có; ẩn NCC + chi phí VC cho phòng YC; theo lần giao) — module `purchase_progress` (`GET /api/purchase-progress`, join PO→POItem→PODelivery, gate OR `purchase_order.read`/`purchase_request.read`, `apply_scope` PO cho phòng thu mua / lọc theo bộ phận cho phòng YC, ẩn NCC+VC khi thiếu `purchase_order.read`) · FE `pages/PurchaseProgress.tsx` + route + menu `anyEntity`. KHÔNG migration. Bản 2 (tạm bỏ): `product.legal_name` + các cột master còn thiếu theo Mapping

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

## Cập nhật Giao diện v2 & Phân quyền (2026-08)
- [x] Fix màn chi tiết chứng từ không mở được (Bỏ logic `!draft` sai ở 4 trang chi tiết: YCBG, YCMH, ĐMH, Phiếu khảo sát).
- [x] Màn hình Tiến độ mua hàng (`/procurement/purchase-progress`): Cập nhật nav item `entity: 'purchase_request'` để Nhân viên & Trưởng phòng phòng YC truy cập được menu trái đúng logic Backend.
- [x] Bổ sung cụm tài khoản Test có data (`TESTREQ`, `DEMONV`, `DEMOTP`, `DEMOQL`, `DEMOAD`, `DEMOTP2`, `DEMOTP3`) vào menu Đổi tài khoản nhanh (Dev).
- [x] Tùy chỉnh màu sọc chẵn/lẻ bảng (`even:bg-slate-100`), khôi phục font 13.5px & limit 20.
- [x] Nổi bật tiêu đề cột (`HEAD_CELL` font-bold text-slate-900).
- [x] Chuẩn hóa ô trống: Hiển thị khoảng trắng phẳng rỗng (`""` / `null`) thay vì dấu gạch `"-"` hay `"—"` trên toàn bộ bảng danh sách, bảng dòng & các thẻ chi tiết.

---
**Đăng nhập:** `degoadmin` / `dego2026` (đổi qua `.env`). Web: http://localhost:8080 · API: http://localhost:8000/docs

