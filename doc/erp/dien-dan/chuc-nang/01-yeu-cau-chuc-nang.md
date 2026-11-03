# YÊU CẦU CHỨC NĂNG — DIỄN ĐÀN NỘI BỘ

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 · CR-199, CR-200, CR-206, CR-261, CR-263, CR-269, CR-271 · bao-CR-272, bao-CR-707 |

Tệp này là chỉ mục yêu cầu: mỗi chức năng tóm tắt ngắn rồi trỏ về tài liệu cũ. Nguồn chính:
[10-giao-dien-va-logic-hien-thi.md](10-giao-dien-va-logic-hien-thi.md) (*GD10*), [phạm vi và kế hoạch](../plans/00-pham-vi-va-ke-hoach.md)
(*KH00*), [lộ trình phase](../plans/02-lo-trinh-phase.md) (*LT02*, mã phase F0–F13).

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Mọi người đăng nhập (không cần vai trò riêng) | Đọc bảng tin theo đối tượng xem, đăng bài, bình luận, bày tỏ cảm xúc, xem trang cá nhân, tìm bài, tự xóa / sửa bài của mình |
| Quản trị diễn đàn (`forum_admin`, `forum_post` read / write / delete và `forum_board` đủ quyền, phạm vi `all`) | Ẩn, xóa, khôi phục bài kèm lý do; ghim bài; dựng chuyên mục; xem nhật ký kiểm duyệt |

Nguồn: KH00 QĐ-D1, D-Q2; `backend/app/seed.py` (vai trò `forum_admin`).

## 2. Danh sách chức năng

Trạng thái: **Có** (đã lên prod) · **Dev** · **Đang làm** · **Chưa** · **Bỏ**. *Chưa ghi* nghĩa là lộ trình ghi đã làm
xong trong mã nhưng không nói môi trường.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-DD-01 | Bảng tin: xếp theo thời gian thuần, phân trang con trỏ, lọc đối tượng xem ngay trong SQL ([GD10 §4](10-giao-dien-va-logic-hien-thi.md#4-bảng-tin--logic-hiển-thị-khi-dữ-liệu-lớn), LT02 F1–F2) | Mọi người | `/forum/feed` | chưa ghi (xong 27/08/2026) | |
| CN-DD-02 | Đăng bài: chữ có định dạng, ảnh và video, chọn đối tượng xem phòng ban / công ty / toàn tập đoàn, không duyệt trước ([GD10 §3](10-giao-dien-va-logic-hien-thi.md#3-đăng-bài), KH00 QĐ-D1, QĐ-D3) | Mọi người | Hộp thoại đăng bài | chưa ghi (xong 27/08/2026; rich text 03/09/2026) | CR-261 |
| CN-DD-03 | Trang cá nhân: chỉ bài của chính người đó; trang của mình thấy cả bài bị ẩn ([GD10 §2](10-giao-dien-va-logic-hien-thi.md#2-trang-cá-nhân--có)) | Mọi người | `/forum/me`, `/forum/users/:id` | chưa ghi (xong 27/08/2026) | |
| CN-DD-04 | Bày tỏ cảm xúc, không sinh chuông; xem ai đã bày tỏ ([GD10 §6](10-giao-dien-va-logic-hien-thi.md#6-like-bài-viết), LT02 F4) | Mọi người | Thẻ bài | chưa ghi | CR-206 |
| CN-DD-05 | Bình luận hai cấp dùng hệ bình luận chung, chuông *bình luận mới trong bài của bạn* ([GD10 §5](10-giao-dien-va-logic-hien-thi.md#5-comment--bê-nguyên-hệ-cr-033-đây-là-chỗ-rẻ-nhất), LT02 F4) | Mọi người | Chi tiết bài | chưa ghi (xong 27/08/2026) | |
| CN-DD-06 | Kiểm duyệt: ẩn, xóa, khôi phục bài, lý do bắt buộc, chuông cho tác giả; màn nhật ký kiểm duyệt (KH00 QĐ-D1, LT02 F5) | Quản trị diễn đàn | Tab Quản trị | chưa ghi (xong 27/08/2026; màn nhật ký 03/09/2026) | CR-263 |
| CN-DD-07 | Ghim bài và tab *Thông báo* (LT02 F9a) | Quản trị diễn đàn | Dải ghim đầu bảng tin, tab Thông báo | chưa ghi (xong 27/08/2026) | CR-199 |
| CN-DD-08 | Bài tự động khi đổi ảnh đại diện, có hỏi trước khi đăng (LT02 F10) | Mọi người | Hộp thoại sau khi đổi ảnh đại diện | chưa ghi (xong 27/08/2026) | |
| CN-DD-09 | Đăng thông báo từ Văn thư khi ban hành văn bản thành bài đã ghim (LT02 F12) | Người ban hành văn bản | Hộp thoại Ban hành của Văn thư | chưa ghi (xong 27/08/2026) | CR-200 |
| CN-DD-10 | Chuyên mục kiểu VOZ: nhóm → box → thread có tiêu đề và prefix; bài trong box vẫn ra bảng tin (KH00 QĐ-D7, LT02 F13a–b) | Mọi người; quản trị dựng chuyên mục | `/forum/boards`, `/forum/boards/:id` | chưa ghi (xong 03/09/2026) | CR-269 |
| CN-DD-11 | Sidebar phải: Nổi bật (bài ghim), Đang sôi nổi (tự tính 7 ngày), Mới nhất (LT02 F13c) | Mọi người | `/forum/boards` (màn rộng) | chưa ghi (xong 03/09/2026) | CR-271 |
| CN-DD-12 | Tìm kiếm bài viết cho mọi người (kết quả tự lọc theo quyền), ô tìm gợi ý top 5, bộ lọc ở tab Quản trị (LT02 nhật ký 03/09/2026) | Mọi người | `/forum/search`, ô tìm đầu trang | chưa ghi (xong 03/09/2026) | CR-263, bao-CR-272, bao-CR-273.1 |
| CN-DD-13 | Sửa bài kèm nhãn *đã chỉnh sửa*; quản trị sửa được mọi bài (LT02 F9) | Tác giả, quản trị | Chi tiết bài | chưa ghi (`PATCH /api/forum/posts/{pid}`, [api.md](../tai-lieu-ky-thuat/api.md)) | bao-CR-707 |
| CN-DD-14 | Tác giả tự xóa bài của mình | Tác giả | Chi tiết bài | chưa ghi (`DELETE /api/forum/posts/{pid}`, [api.md](../tai-lieu-ky-thuat/api.md)) | |
| CN-DD-15 | Tab *Hướng dẫn* gộp Trung tâm trợ giúp (KH00 QĐ-D4, LT02 F7) | — | — | Chưa | |
| CN-DD-16 | Bật cơ chế duyệt bài trước khi đăng (KH00 QĐ-D2, LT02 F8) | — | — | Chưa (dữ liệu đã chừa sẵn) | |
| CN-DD-17 | Người đăng tự chọn bố cục ảnh (LT02 F11) | — | — | Chưa (mới là ý tưởng, chưa chốt làm) | |
| CN-DD-18 | Trợ lý AI đọc diễn đàn bằng hai công cụ có ép quyền ([đề xuất](../nghien-cuu/03-de-xuat-ai-doc-dien-dan.md)) | — | — | Chưa (chưa xếp lịch) | |
| CN-DD-19 | Đợt 3: theo dõi người / phòng, nhóm kín, khảo sát trong bài (KH00 mục 5) | — | — | Chưa | |

## 3. Chi tiết từng chức năng

### CN-DD-01 — Bảng tin

- **Luật nghiệp vụ:** thứ tự thời gian thuần, không xếp hạng; ai thấy bài nào lọc ngay trong SQL theo đối tượng xem, người
  thiếu phòng ban / pháp nhân thì bị chặn; phân trang bằng con trỏ, cấm OFFSET; số đếm và dữ liệu kèm bài gom theo trang
  ([GD10 §4](10-giao-dien-va-logic-hien-thi.md#4-bảng-tin--logic-hiển-thị-khi-dữ-liệu-lớn)).
- **Quyền:** chỉ cần đăng nhập; quyền đọc đi theo luật đối tượng xem của API.

### CN-DD-02 — Đăng bài

- **Luật nghiệp vụ:** lên bảng tin ngay, không duyệt (QĐ-D1); bài trong box không tự chọn đối tượng xem mà theo box (QĐ-D7a).
- **Dữ liệu:** giới hạn ký tự và số tệp ở [02-yeu-cau-phi-chuc-nang.md](02-yeu-cau-phi-chuc-nang.md) PCN-DD-04.

### CN-DD-06 — Kiểm duyệt

- **Luật nghiệp vụ:** không có đường ẩn lặng lẽ; ẩn và xóa bắt buộc lý do (thiếu là 400), ghi `tab_forum_moderation_log`,
  tác giả nhận đúng một chuông; bài ẩn biến khỏi bảng tin mọi người nhưng còn ở trang cá nhân tác giả và mắt quản trị
  (KH00 QĐ-D1, LT02 F5).
- **Quyền:** `forum_post.write` (ẩn, khôi phục, ghim), `forum_post.delete` (xóa kiểm duyệt).

### CN-DD-10 — Chuyên mục kiểu VOZ

- **Luật nghiệp vụ:** lớp phân loại đè lên nền bài viết sẵn có, không xây forum engine riêng; bài trong box vẫn đổ ra bảng
  tin; bình luận giữ mô hình hai cấp (KH00 QĐ-D7). Xóa nhóm / box chỉ khi rỗng ([api.md](../tai-lieu-ky-thuat/api.md)).
- **Quyền:** dựng / sửa / xóa chuyên mục cần `forum_board.create` / `write` / `delete`.

## 4. Luồng trạng thái chứng từ

Trạng thái bài viết (LT02 F5): `Đã đăng → Ẩn → (Khôi phục) Đã đăng`; `Đã đăng / Ẩn → Đã xóa`. Giá trị *chờ duyệt* đã chừa
sẵn cho F8, chưa dùng.

## 5. Câu hỏi còn mở

Nguồn: KH00 mục 6.

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| D-Q4 | Người đăng được tự xóa / sửa bài của mình hay chỉ ẩn? Mã hiện đã có tự xóa và sửa bài (CN-DD-13, CN-DD-14), KH00 chưa cập nhật | chưa có | chưa có |
| D-Q5 | *Công ty* trong đối tượng xem là pháp nhân theo hồ sơ nhân sự — người thuộc holding thấy gì? | chưa có | chưa có |
| D-Q6 | Bày tỏ cảm xúc có sinh chuông cho tác giả không? Mặc định đợt 1: không (api.md xác nhận không sinh chuông) | chưa có | chưa có |
