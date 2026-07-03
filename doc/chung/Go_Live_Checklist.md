# Checklist Go-Live — Mini Tool Thu Mua

Danh sách cần rà trước khi đưa lên production (VPS). Đánh ☑ khi hoàn tất.

---

## 0. Kết quả UAT (2026-07-03)
- ✅ 26/26 endpoint chính trả 200 (PR, khảo sát, PO, tồn kho, công nợ, thanh toán, danh mục, users, roles, settings, notifications, alerts, reports…).
- ✅ Luồng PYC end-to-end: Nháp → Gửi duyệt → Duyệt → (đổi dòng) Đang xử lý → (dòng xong) Hoàn thành → Nhân bản. Trạng thái tự suy đúng.
- ✅ Khảo sát: gửi duyệt (đủ trường) → duyệt từng dòng → trả lại → duyệt phiếu.
- ✅ File: upload → trả link R2 công khai, tải lại được; đính kèm PR/khảo sát hiển thị.
- ✅ Cấu hình R2/SMTP trong DB (secret mã hóa), test R2 OK.
- ✅ Chuông thông báo lọc theo quyền; email workflow đã tắt (chỉ chuông).

---

## 1. Bảo mật (LÀM TRƯỚC TIÊN)
- ☐ **Rotate khóa R2** — R2 Secret Key từng bị chia sẻ trong chat lúc phát triển → tạo khóa mới trên Cloudflare, nhập lại ở **Cấu hình hệ thống**.
- ☐ **JWT_SECRET**: đặt chuỗi mạnh, **cố định**, **backup an toàn**. Đây là khóa mã hóa secret trong DB — đổi nó = mất giải mã R2/SMTP đã lưu.
- ☐ Xác nhận `.env` **không** lên git (đã có `.env`, `.env.*` trong `.gitignore`; `!.env.example` vẫn đẩy mẫu).
- ☐ Đổi mật khẩu admin mặc định (`ADMIN_PASSWORD`) khỏi giá trị demo.
- ☐ `CORS_ORIGINS` chỉ chứa domain thật của production.

## 2. Biến môi trường `.env` trên VPS
- ☐ `DB_*` trỏ đúng MySQL production.
- ☐ `JWT_SECRET` (như mục 1), `ACCESS_EXPIRE_MIN`, `REFRESH_EXPIRE_DAYS`.
- ☐ `ADMIN_CODE` / `ADMIN_PASSWORD` cho seed admin.
- ☐ `FRONTEND_URL`, `VITE_API_URL` = domain thật.
- ☐ R2/SMTP **không** cần đặt ở `.env` (cấu hình trong DB qua UI); nếu muốn bootstrap thì thêm tạm.
- ☐ Lưu ý: đổi `.env` phải `docker compose up -d` (recreate), **không** `restart`.

## 3. Cấu hình trong app (Hệ thống → Cấu hình hệ thống)
- ☐ Nhập **R2**: endpoint, bucket, public URL, Access Key ID, Secret Key → "Kiểm tra kết nối R2" phải OK.
- ☐ **Email**: quyết định bật/tắt. Nếu bật để test → nhập SMTP + đặt tạm **Email test override** = email của bạn; khi chạy thật thì **xóa override**.
- ☐ Email workflow (duyệt phiếu) hiện **chỉ gửi qua chuông**; email chỉ dùng cho cấp tài khoản / reset mật khẩu.

## 4. Cơ sở dữ liệu & Migration
- ☐ `docker compose up --build -d` → `start.sh` tự chạy `alembic upgrade head` + seed.
- ☐ Kiểm `alembic upgrade head` không lỗi (schema mới nhất).
- ☐ Seed vai trò chuẩn + admin chạy xong.

## 5. Dữ liệu thật
- ☐ Import master data thật: Công ty, Phòng ban, Nhân sự, NCC, Sản phẩm, Kho, ĐVT, Phân loại.
- ☐ Tạo tài khoản cho toàn bộ nhân sự (username = mã NV).
- ☐ **Xóa dữ liệu mẫu/test**: các phiếu khảo sát mẫu (KS0000x), PYC test, thông báo test.
- ☐ Khôi phục mật khẩu các tài khoản test về đúng mã NV (nếu đã đổi khi thử).

## 6. Phân quyền
- ☐ Rà **Vai trò & quyền**: gán đúng entity × action cho từng vai trò chuẩn.
- ☐ Quyền `setting` (Cấu hình hệ thống) chỉ admin / vai trò IT.
- ☐ Menu danh mục chỉ hiện cho người có quyền quản lý (đã áp).
- ☐ Tạo vai trò **Admin IT** nếu cần, gán cho người phụ trách.
- ☐ Kiểm 1 tài khoản nhân viên: chỉ thấy Trang chủ + Yêu cầu mua; tạo & gửi duyệt được phiếu của mình.

## 7. Triển khai (Docker)
- ☐ `docker compose up --build -d` (db, api, web, adminer).
- ☐ Web: domain/reverse-proxy (nginx) → cổng web (5173/8080). API → 8000.
- ☐ Volume: `db_data` (MySQL) + `backend/uploads` (fallback khi R2 lỗi) được mount/bền.
- ☐ Adminer chỉ mở nội bộ (không public) hoặc tắt trên prod.

## 8. Sao lưu & vận hành
- ☐ Lịch backup DB (mysqldump định kỳ).
- ☐ Backup `JWT_SECRET` (ngoài server).
- ☐ Theo dõi log api; DB ngoài (nếu dùng) phải ổn định — app lỗi tạm khi DB chớp tắt.

## 9. Smoke test sau deploy
- ☐ Đăng nhập admin OK.
- ☐ Tạo 1 PYC → gửi duyệt → duyệt.
- ☐ Upload 1 file đính kèm → mở link được.
- ☐ "Kiểm tra kết nối R2" ở Cấu hình → OK.
- ☐ Chuông hiển thị thông báo/cảnh báo.

---

## 10. Hạn chế đã biết / nên làm sớm sau go-live
- 🔴 **Module File P1 chưa làm**: hiện **ai đăng nhập cũng tải/xóa được file** (chưa gắn quyền theo phiếu cha), chưa giới hạn loại/dung lượng, xóa phiếu chưa dọn file. Nên làm sớm (bảo mật).
- ⚪ Chưa có **worker nền** (Celery/Redis) — email/thông báo chạy background task của FastAPI.
- ⚪ API **Nhân sự chưa hỗ trợ ô tìm kiếm** (search bị bỏ qua).
- ⚪ Chưa có: duyệt PO theo ngưỡng giá trị, quy đổi ĐVT (Sheet 5).
