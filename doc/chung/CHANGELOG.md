# CHANGELOG — Nhật ký thay đổi

Ghi theo ngày, gộp theo nhóm chức năng. Mới nhất ở trên.

---

## 2026-07-15

### PWA & Thông báo đẩy (Web Push)
- Thêm **PWA** (cài được như app, cache asset, nhắc cập nhật bản mới) + banner mời cài sau đăng nhập; fix bắt `beforeinstallprompt` sớm (popup cài trên Edge), nút "Cài ứng dụng" trong menu, chuông thông báo cố định trên mobile khỏi bị cắt.
- Thêm **Web Push** (VAPID + pywebpush): đẩy thông báo tới thiết bị đã bật, chạy nền không chặn API. Endpoint đăng ký/hủy subscription; tự xóa endpoint hết hạn (404/410).
- **Toggle banner cài đặt** qua biến `VITE_PWA_INSTALL_PROMPT` (mặc định ẩn; đặt `=on` để hiện). VAPID **private key chuyển sang ENV** (không để trong source).

### Chuông thông báo (in-app + push)
- Chia thông báo **theo cấp nhân sự**, bỏ gộp sự kiện, báo khi phân công NSTM.
- **YCKS (Yêu cầu khảo sát)**: bổ sung Web Push + báo đúng người duyệt (trước đây thiếu hẳn thông báo).
- **PYC (Yêu cầu mua hàng)**: trả về/hủy báo người tạo.
- **YCTT (Yêu cầu thanh toán)**: thêm thông báo gửi duyệt / duyệt / từ chối / đã chi (trước đây không có).
- Thông báo lưu/gửi duyệt YCKS + YCTT chuyển sang dùng **toast** thay vì hiện chữ dưới bảng.

### Đơn mua hàng (ĐMH/PO)
- Thêm **tiền theo dòng** (tổng đặt/tiền hàng/đã trả/còn lại) + nút **Tạo yêu cầu thanh toán** (2 tab NCC sản xuất / vận chuyển) + chặn nhập liệu + tự khớp NCC theo MST/tên.
- **Đơn vị vận chuyển 3 trạng thái**: chưa chọn / NCC tự vận chuyển / đơn vị VC thật.
- Mặc định tick NCC sản xuất; nhãn trạng thái **"Đã nhận một phần"**; QLTM ghi nhận đã chi.
- **Giới hạn xem theo NSPT** (người phụ trách), khóa dòng đã Hoàn thành (kể cả bảng vận chuyển), gọn UI/trạng thái.
- Nút **"Từ chối"** chỉ hiện ở bước **gửi duyệt**; ở đơn đã duyệt/đang nhận đổi thành **"Hủy"** — chặn hủy khi có dòng đã Hoàn thành + **bắt buộc lý do**.
- **NSPT phụ trách tự điền** khi tạo đơn: từ YCMH → người phụ trách dòng; đơn trực tiếp → người tạo. Hiện sẵn trong form (chỉ vai trò duyệt được sửa).

### Báo cáo
- Bỏ dòng "(Không rõ)" (key rỗng) ở mọi tab; sửa số liệu (lọc `is_deleted`, chỉ đơn thật, không lọc theo company sai); bỏ viết tắt nhãn; thêm lọc bộ phận.
- Phân trang chi tiết chi phí vận chuyển; tab cuộn ngang thay vì xuống dòng.
- **Mobile**: bộ lọc thu gọn, cột báo cáo ghim (sticky) responsive, tồn kho phân trang.

### Phân quyền (RBAC)
- **Quản lý thu mua**: toàn quyền nghiệp vụ (như admin, trừ quản trị hệ thống user/role/setting).
- **Admin thu mua**: CRUD toàn bộ cụm danh mục; nghiệp vụ chỉ đọc phạm vi `proc` (thấy sau khi đã duyệt).

### Nhân sự & tài khoản
- **Đặt mật khẩu tự tạo tài khoản đăng nhập** nếu nhân sự chưa có (lấy email + vai trò của nhân sự).
- **Mặc định vai trò "Nhân sự (cơ bản)"** khi tạo nhân sự; **gộp + xóa vai trò legacy "Nhân viên" (STAFF)** (218 nhân sự + 2 tài khoản chuyển sang "Nhân sự cơ bản").

### Đăng nhập & Email
- Wire `VITE_GOOGLE_CLIENT_ID` làm build arg → **đăng nhập Google** hoạt động (cần thêm origin trong Google Console).
- **Reset mật khẩu gửi được kể cả khi tắt email chung** (`force=True`); email chung để tắt.

### In phiếu thanh toán
- Điền chức vụ/bộ phận/trưởng BP + thông tin ngân hàng NCC; thu hẹp header bảng.

### Thao tác dữ liệu (không qua commit)
- Đồng bộ **data ngân hàng NCC** từ DB dev → VPS (31 NCC cập nhật).
- Backfill **NSPT** cho 12 đơn cũ đang trống.
- Cấu hình VPS: VAPID keys, Google Client ID vào `.env`; SMTP Brevo đã cấu hình (email tắt).
