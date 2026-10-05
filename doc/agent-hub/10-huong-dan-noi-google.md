# HƯỚNG DẪN BẬT GOOGLE CÁ NHÂN CHO TRỢ LÝ (dev)

**05/10/2026.** Để thử: xem lịch, đặt lịch họp có mời người (Google tự gửi email mời), tìm và đọc tệp Drive, bản tin
sáng 7:30 và nhắc trước họp 15 phút. Mã đã có từ ai-CR-064, chỉ thiếu cấu hình phía Google.

Dev đã có `GOOGLE_CLIENT_ID` (client OAuth dùng cho «Đăng nhập bằng Google», ai-CR-406). Dùng lại đúng client đó.
Còn thiếu: đường dẫn trả về, bật hai API, khai quyền, và **khóa bí mật** (`GOOGLE_CLIENT_SECRET`).

## Bước 1 — Mở đúng dự án Google Cloud

Vào https://console.cloud.google.com, chọn dự án đang chứa client đăng nhập ERP. Kiểm: **APIs & Services → Credentials →
OAuth 2.0 Client IDs** có một client mà Client ID bắt đầu bằng `692103…`.

## Bước 2 — Bật hai API

**APIs & Services → Library**, tìm và bấm **Enable** cho:

- Google Calendar API
- Google Drive API

## Bước 3 — Khai quyền trên màn đồng ý

**Google Auth Platform** (tên cũ: OAuth consent screen):

1. **Data access → Add or remove scopes**, tick đủ sáu quyền:
   - `openid`, `.../auth/userinfo.email`
   - `.../auth/calendar.events`, `.../auth/calendar.readonly`
   - `.../auth/drive.readonly`, `.../auth/drive.file`
2. **Audience**: để **Testing**, bấm **Add users**, thêm Gmail của đại ca (và ai muốn thử).
   - Testing: dùng được ngay, không cần Google duyệt; nhưng **7 ngày** phải nối lại một lần.
   - Muốn khỏi nối lại thì bấm **Publish app** (In production). Quyền đọc Drive là loại «hạn chế», app chưa được Google
     xác minh sẽ hiện màn cảnh báo «chưa xác minh» — bấm *Nâng cao → Tiếp tục* vẫn dùng được (dưới 100 người).

## Bước 4 — Thêm đường dẫn trả về và lấy khóa bí mật

**Credentials → bấm vào client `692103…`**:

1. **Authorized redirect URIs → Add URI**, dán đúng dòng này rồi **Save**:

   ```
   https://deverp.degoholding.vn/api/agent-hub/google/callback
   ```

2. Mục **Client secrets**: bấm **Add secret** (hoặc sao chép khóa đang có).
3. Dán khóa vào một tệp trên máy, mỗi tệp một dòng, **không gửi qua chat**:

   ```
   D:\New folder\thuthapykien\google-client.secret
   ```

   Nhắn em «xong google». Em đưa khóa lên `.env.dev` (không in ra), khởi động lại api + worker + poller, rồi xóa tệp.

## Bước 5 — Nối Google của mình

1. Đăng nhập https://deverp.degoholding.vn → **Trang cá nhân → tab «Khóa AI»** → thẻ **Google** → **Nối Google**.
2. Chọn tài khoản Gmail đã thêm ở bước 3 → **Cho phép** đủ các quyền.
3. Quay về trang cá nhân thấy «Đã nối …@gmail.com» là xong.

## Bước 6 — Thử trên Telegram

| Nhắn | Kết quả |
|---|---|
| «lịch hôm nay của anh» · «tuần này anh có họp gì» | Đọc lịch Google |
| «đặt lịch họp NCC Thiên An 14h mai 1 tiếng, mời a@gmail.com» | Tạo sự kiện; Google tự gửi email mời |
| «tìm trên Drive báo giá tháng 9» · «đọc tệp đó tóm tắt giúp anh» | Tìm / đọc Drive |
| «lên task gọi NCC Thiên An cho anh Được hạn thứ 6» (ai-CR-080) | Bản nháp việc ở phân hệ Dự án → «tạo» → người được giao nhận chuông |
| «nhắc anh 15h gọi NCC» | Nhắc giờ qua Telegram (không cần Google) |
| (tự động) | 7:30 bản tin sáng: lịch hôm nay + việc chờ duyệt · 15 phút trước mỗi cuộc họp: nhắc |

Không cần Google: lên task, nhắc giờ, chuông ERP chuyển sang Telegram — thử được ngay.
