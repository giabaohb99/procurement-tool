---
name: soat-man-dev
description: Soát màn hình mới trên dev bằng khung trình duyệt mà đại ca đã đăng nhập sẵn, đối chiếu với bài HDSD và hợp đồng API, phân loại lỗi chặn / lỗi nhỏ và báo đúng chủ khu. Dùng trước khi gộp main hoặc trước giờ đóng băng lên prod.
---

# Soát màn trên dev

## Khi nào dùng
Điều phối giao soát một cụm màn vừa lên dev (ví dụ Kho skill AI, AI của tôi), hoặc trước giờ đóng băng lên prod.
Mục tiêu: tìm lỗi người dùng NHÌN THẤY và chỗ màn lệch bài HDSD, không phải đọc mã.

## Các bước
1. **Không tự gõ mật khẩu vào host ngoài localhost.** Mở `https://deverp.degoholding.vn/<đường>` trong khung trình duyệt;
   thấy màn đăng nhập thì dừng, nhắn đại ca đăng nhập giúp trong chính khung đó, chờ đại ca nói xong mới soát. Phiên
   hết hạn giữa chừng thì xin lại, đừng thử đoán tài khoản. Localhost (`localhost:8083`) thì được dùng tài khoản mẫu
   của `app/seed.py` (ví dụ `admin` / `admin`, các tài khoản `*@demo.com` mật khẩu `demo123`).
2. **Mở rộng khung** để bảng không cắt cột: `resize_window` 1440x1000; xong việc `preset: desktop`.
3. **Đi hết menu** của phân hệ, mỗi màn: `navigate` → `wait` 2 tới 3 giây → `screenshot` cỡ 0.7 → `get_page_text`. Chữ
   lấy từ `get_page_text` (đếm số, nhãn, trạng thái), ảnh để nhìn bố cục. Màn có tab (Skill / Ai được đọc / Lịch sử) thì
   `find` tên tab rồi `left_click` theo `ref`. Hộp thoại xóa / thu hồi chỉ mở xem câu xác nhận rồi Hủy, không bấm đồng ý
   trên dữ liệu thật của dev nếu không được giao.
4. **Đối chiếu ba nơi** cho từng màn: nhãn nút và bước làm trên màn == bài HDSD == tài liệu chức năng. Số trên màn phải
   tự giải thích được (ví dụ Lượt gọi 7 ngày = 50 nhưng Công cụ dùng nhiều = 1 vì thẻ đếm cả lượt khởi tạo); tab đếm
   phải khớp bảng (lỗi Skill (0) trong khi bảng có 3 skill, 19/10). Nhãn viết hoa / thường phải thống nhất giữa ô chọn
   và cột bảng. Dòng lạ như `#0` ở cột Người là lỗ hiển thị.
5. **Phân loại**: lỗi CHẶN = người dùng không làm được việc, dữ liệu sai, lộ dữ liệu, màn trắng, 500 → nhắn Agent 1
   NGAY kèm ảnh + đường dẫn + bước tái hiện + giờ (để tra nhật ký). Lỗi NHỎ = nhãn, đếm, bố cục, câu chữ → gom một tin,
   đánh số, mỗi lỗi ghi màn · dữ liệu · kỳ vọng · thực tế · gợi ý sửa; gửi chủ khu (màn: Agent 3 `giao-dien-v2`;
   API / số liệu: Agent 4 `ai-mcp` hoặc Agent 1). Lỗi của bài HDSD thì tự sửa theo skill `viet-hdsd`.
6. **Báo đại ca** một tin: câu đầu là có / không lỗi chặn; bảng từng màn đã xem; lỗi nhỏ đã gửi ai. Ghi vào sổ nếu đợt soát
   gắn với một CR.

## Bẫy đã gặp
- 19/10/2026: hai tai nạn đăng nhập — tự đăng nhập local được nhưng dev thì không; nhờ đại ca đăng nhập sẵn mới soát
  được. Đừng chạy script dữ liệu mẫu của người khác (`scripts/.seed_k1_mau_tam.py`) để thay dev nếu đại ca đã mở phiên.
- `get_page_text` ở local đôi khi trả trang trắng vì Vite đang dựng: `wait` 6 tới 8 giây rồi đọc lại; xem
  `read_console_messages` để bắt 404 / 500 của API (local thiếu mã backend mới thì API 404 là bình thường, ghi rõ).
- Nút trong bảng không hiện vì quyền: kiểm `can_delete` / quyền của tài khoản trước khi báo lỗi.
- Dữ liệu kiểm thử của Agent khác (ứng dụng `kiem-thu-agent1`, bộ DEMO-*) không phải lỗi; chỉ nhắc dọn trước prod.

## Kiểm xong
- Mọi mục menu của cụm đã mở, mỗi màn có ảnh + chữ.
- Lỗi chặn (nếu có) đã tới Agent 1 với ảnh; lỗi nhỏ đã tới chủ khu; đại ca có tin tóm tắt.
- Khung trình duyệt trả về `desktop`; không gõ mật khẩu nào vào host ngoài localhost.
