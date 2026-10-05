# HƯỚNG DẪN BẬT GOOGLE CÁ NHÂN CHO TRỢ LÝ (dev)

**05/10/2026 · sửa theo ai-CR-083.** Để thử: xem lịch, đặt lịch họp có mời người (Google tự gửi email mời), tìm và đọc
tệp Drive, bản tin sáng 7:30 và nhắc trước họp 15 phút.

Hai thứ khác nhau:

- **Ứng dụng Google (làm MỘT lần cho cả công ty):** chỉ là «cánh cửa» cho ERP xin quyền Google, không chứa lịch hay tệp
  của ai. Dùng một OAuth client **riêng** của Trợ lý (`AGENT_GOOGLE_CLIENT_ID` + `AGENT_GOOGLE_CLIENT_SECRET`), tách
  khỏi client «Đăng nhập bằng Google» của ERP — đổi gì ở đây không ảnh hưởng đăng nhập.
- **Nối Google (MỖI NGƯỜI tự làm):** ai muốn dùng thì vào Trang cá nhân bấm «Nối Google» bằng Gmail của chính mình. Bot
  chỉ đọc lịch / Drive của đúng người đó.

## Bước 1 — Tạo dự án riêng

Không dùng dự án «API Degoholding Dev» (của Firebase app cũ). Trên https://console.cloud.google.com:
bấm ô tên dự án trên cùng → **New project** → tên `ERP Tro ly AI` → **Create** → chọn dự án vừa tạo.

## Bước 2 — Bật hai API

☰ → **APIs and services → Library** → tìm và **Enable**: `Google Calendar API`, `Google Drive API`.

## Bước 3 — Màn đồng ý (Google Auth Platform)

☰ → **APIs and services → OAuth consent screen** → **Get started**:

1. **App information:** tên `ERP DEGO - Trợ lý AI`, email hỗ trợ = Gmail của đại ca → Next.
2. **Audience:** chọn **External** → Next.
3. **Contact information:** Gmail của đại ca → Next → tick đồng ý → **Create**.
4. Menu trái **Audience → Test users → + Add users** → Gmail của đại ca (và ai muốn thử) → Save.
5. Menu trái **Data access → Add or remove scopes** → kéo xuống ô **Manually add scopes**, dán 4 dòng → **Add to table**
   → **Update** → **Save**:

   ```
   https://www.googleapis.com/auth/calendar.events
   https://www.googleapis.com/auth/calendar.readonly
   https://www.googleapis.com/auth/drive.readonly
   https://www.googleapis.com/auth/drive.file
   ```

Testing: dùng ngay, nhưng 7 ngày phải nối lại một lần. Muốn bỏ hạn đó thì sau này bấm **Audience → Publish app**
(sẽ có màn «ứng dụng chưa xác minh», bấm Nâng cao → Tiếp tục vẫn dùng được, dưới 100 người).

## Bước 4 — Tạo client

Menu trái **Clients → + Create client**:

- Application type: **Web application** · Name: `ERP Tro ly`
- **Authorized redirect URIs → + Add URI**, dán:

  ```
  https://deverp.degoholding.vn/api/agent-hub/google/callback
  ```

- **Create** → hộp thoại hiện **Client ID** và **Client secret**. Chép CẢ HAI vào một tệp, dòng 1 là Client ID, dòng 2 là
  Client secret, **không gửi qua chat**:

  ```
  D:\New folder\thuthapykien\google-client.secret
  ```

Nhắn em «xong google». Em đưa hai khóa lên `.env.dev` (`AGENT_GOOGLE_CLIENT_ID`, `AGENT_GOOGLE_CLIENT_SECRET`, không in ra),
khởi động lại bot, rồi xóa tệp.

## Bước 5 — Nối Google của mình

https://deverp.degoholding.vn → **Trang cá nhân → tab «Khóa AI»** → thẻ **Google** → **Nối Google** → chọn Gmail đã thêm ở
bước 3 → **Cho phép**. Báo `redirect_uri_mismatch` thì đợi 5 phút (Google áp thay đổi chậm) rồi thử lại.

## Bước 6 — Thử trên Telegram

| Nhắn | Kết quả |
|---|---|
| «lịch hôm nay của anh» · «tuần này anh có họp gì» | Đọc lịch Google |
| «đặt lịch họp NCC Thiên An 14h mai 1 tiếng, mời a@gmail.com» | Tạo sự kiện; Google tự gửi email mời |
| «tìm trên Drive báo giá tháng 9» · «đọc tệp đó tóm tắt giúp anh» | Tìm / đọc Drive |
| «lên task gọi NCC Thiên An cho anh Được hạn thứ 6» (ai-CR-080) | Bản nháp việc ở phân hệ Dự án → «tạo» → chuông cho người được giao |
| (tự động) | 7:30 bản tin sáng: lịch hôm nay + việc chờ duyệt · 15 phút trước mỗi cuộc họp: nhắc |

Không cần Google: lên task, nhắc giờ («nhắc anh 15h gọi NCC»), chuông ERP chuyển sang Telegram.
