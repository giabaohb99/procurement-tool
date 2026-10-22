# 04 — Kịch bản dùng thử Diễn đàn nội bộ (phase F6, việc DD1-2)

| | |
|---|---|
| Bản | 0.1 — 22/10/2026, Agent 2 (*A2 Rà mã & Tài liệu*), việc *kh-tai-lieu-agc* |
| Mục đích | Nhóm nhỏ **IT + HR** dùng thử trên điện thoại rồi mới thông báo toàn công ty (điều kiện đủ của F6, `02-lo-trinh-phase.md`) |
| Ở đâu | `https://deverp.degoholding.vn`, thẻ **Diễn đàn** ở màn chọn phân hệ (cùng tên miền ERP, không có tên miền riêng — QĐ-D6) |
| Ai | 4–6 người: 2–3 IT, 2–3 HR; **1 người giữ vai trò Quản trị diễn đàn** (`forum_admin`) |
| Thời lượng | Buổi đầu 30 phút; sau đó dùng thật 5 ngày làm việc |
| Kết quả | Biên bản theo mẫu ở mục 5, gửi Agent 1 để đóng F6 |

*Cần kiểm lại:* kế hoạch `doc/erp/00-ke-hoach-theo-module.md` ghi chưa rõ diễn đàn đã thông báo toàn công ty
hay chưa. Trước khi mở buổi thử, hỏi đại ca: nếu đã thông báo rồi thì kịch bản này dùng để **nghiệm thu
lại**, không phải thử trước khi mở.

Nhãn trong kịch bản lấy theo bộ bài hướng dẫn *Hướng dẫn sử dụng Diễn đàn nội bộ* (seed
`backend/scripts/seed_help_dien_dan.py`). Nhãn nào khác màn thật thì ghi vào biên bản.

## 1. Chuẩn bị

| Việc | Kiểm |
|---|---|
| Mọi người có tài khoản dev (diễn đàn **không cần cấp quyền thêm**) | Đăng nhập dev, thẻ **Diễn đàn** hiện |
| Một người được gán vai trò *Quản trị diễn đàn* | Người đó thấy tab **Quản trị** trên thanh trên cùng của diễn đàn |
| **Ít nhất 3 người làm trên điện thoại** (một Android, một iPhone) | Cột *Thiết bị* của biên bản |
| Người dẫn đặt sẵn một ảnh và một video mp4 ngắn trong máy để đăng thử | |

## 2. Vòng chính (buổi đầu)

| # | Ai làm | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| 1 | Mỗi người, trên điện thoại | Mở thẻ **Diễn đàn**, đi qua bốn tab **Diễn đàn · Bảng tin · Thông báo · Trang của tôi** | Không có menu trái của ERP; các tab đọc được trên màn nhỏ |
| 2 | IT (điện thoại) | Tab **Bảng tin**, bấm ô **Bạn đang nghĩ gì?**, viết bài có **chữ đậm** + 1 ảnh chụp từ máy, chọn đối tượng **Phòng ban**, đăng | Người **cùng phòng** thấy bài; người phòng khác **không** thấy |
| 3 | HR (điện thoại) | Đăng bài chọn **Toàn tập đoàn**, kèm video mp4 | Cả nhóm thấy; video phát ngay trên trang |
| 4 | Mỗi người | Thả cảm xúc: bấm **Thích**, rồi giữ nút để đổi sang cảm xúc khác; bấm vào số đếm xem ai đã thả | Đổi được; danh sách người thả lọc được theo loại |
| 5 | Mỗi người | Bình luận bài ở bước 3, **trả lời** một bình luận, **@nhắc** một người | Người được nhắc nhận chuông; bấm chuông mở đúng bài |
| 6 | IT | Mở một **chuyên mục** (ví dụ *Mẹo dùng hệ thống ERP*), tạo chủ đề có **tiêu đề** và nhãn đầu bài *Kiến thức* | Chủ đề nằm trong chuyên mục và **vẫn hiện trên Bảng tin**, đối tượng xem là toàn tập đoàn |
| 7 | Mỗi người | Ô tìm trên thanh đầu trang: gõ một từ có trong bài bước 6 (từ 2 ký tự) | Khay gợi ý hiện bài đó; bấm *Xem tất cả N kết quả* mở trang tìm đầy đủ |
| 8 | Người đăng bước 2 | **Trang của tôi**: xóa bài bước 2 | Bài biến khỏi Bảng tin của mọi người |
| 9 | Quản trị diễn đàn | Menu ba chấm trên bài bước 3 › **ghim** | Bài hiện ở tab **Thông báo**, khung **Nổi bật** (trên điện thoại dồn lên đầu trang) và mục *Bài ghim* của tab **Quản trị** |
| 10 | Quản trị diễn đàn | Menu ba chấm trên bài bước 6 › **Ẩn bài**, nhập lý do; rồi **Khôi phục bài** | Lúc ẩn: chỉ tác giả và quản trị còn thấy, tác giả nhận chuông kèm lý do và thấy băng rôn *đã bị quản trị viên ẩn*. Có dòng trong *Nhật ký kiểm duyệt* |
| 11 | Mỗi người | Bấm vào ảnh trong bài để phóng to, chuyển ảnh, đóng bằng nút X | Xem được trên điện thoại |
| 12 | Một người | Đang soạn bài thì đóng khung đăng, mở lại | Nội dung gõ dở còn nguyên |

## 3. Năm ngày dùng thật

Nhóm dùng diễn đàn cho trao đổi thật trong 5 ngày (thông báo nội bộ IT / HR, hỏi đáp ERP). Cuối mỗi ngày mỗi
người ghi một dòng *vướng gì, thiếu gì*. Người dẫn đếm: số bài, số bình luận, số người đăng từ điện thoại.

## 4. Những thứ đã biết là CHƯA có (đừng ghi là lỗi)

- **Sửa bài sau khi đăng**: chưa có, phải xóa rồi đăng lại.
- **Duyệt bài trước khi hiện** (F8), tab **Hướng dẫn** (F7), ghim + tìm kiếm nâng cao (F9): thuộc đợt 2.
- Chọn đối tượng xem chỉ có ở bài đăng lên Bảng tin; bài trong chuyên mục luôn toàn tập đoàn.

## 5. Mẫu biên bản

| # bước | Ai | Thiết bị | Giờ | Đạt / Không | Ghi chú | Chặn mở toàn công ty? |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

Cuối biên bản: **Kết luận nhóm** (mở toàn công ty / mở nếu sửa X / chưa mở) · **Ba việc nên sửa nhất** ·
**Ngày thử** · **Người dẫn**. Điều kiện đủ còn lại của F6 — **sao lưu R2 phủ các bảng diễn đàn** — do Agent 1
kiểm (không phải người dùng thử) và ghi vào cùng biên bản.

Tham chiếu: `02-lo-trinh-phase.md` F6 · `00-pham-vi-va-ke-hoach.md` · bài HDSD seed `backend/scripts/seed_help_dien_dan.py`.
