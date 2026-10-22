# 06 — Kịch bản dùng thử Dự án / Công việc (mốc MVP, việc CV1-3)

| | |
|---|---|
| Bản | 0.1 — 22/10/2026, Agent 2 (*A2 Rà mã & Tài liệu*), việc *kh-tai-lieu-agc* |
| Mục đích | Một đội thật đi **trọn một vòng** trên dev để đóng mốc MVP của W2 (`03-lo-trinh-phase.md`) |
| Ở đâu | `https://deverp.degoholding.vn`, thẻ **Dự án** ở màn chọn phân hệ |
| Ai | **Chưa chốt đội** — đại ca chọn (câu treo ở `doc/erp/00-ke-hoach-theo-module.md` mục 8). Cần 3–5 người: 1 người làm *Chủ sở hữu*, 1 *Quản trị*, 2–3 *Thành viên*, nên có 1 *Khách xem* |
| Thời lượng | Buổi đầu 45 phút cùng nhau; sau đó dùng thật 5 ngày làm việc |
| Kết quả | Biên bản theo mẫu ở mục 5, gửi Agent 1 để chốt mốc MVP |

Nhãn nút trong kịch bản lấy từ mã giao diện ngày 22/10/2026. Người dẫn buổi thử nên đi trước một lượt
trên dev; nhãn nào khác màn thật thì ghi vào biên bản, đó cũng là lỗi cần sửa (bài hướng dẫn hoặc màn hình).

## 1. Chuẩn bị (người dẫn làm trước buổi thử)

| Việc | Kiểm |
|---|---|
| Mỗi người trong đội có tài khoản dev và vai trò có quyền xem + tạo *Công việc* | Đăng nhập dev, thẻ **Dự án** hiện và mở được |
| Người dẫn có quyền tạo nhóm dự án | Ở thanh bên trái có nút **Tạo nhóm dự án** |
| Đồng hồ: ghi giờ bắt đầu / kết thúc từng bước | Cột *Giờ* của biên bản |
| Điện thoại: ít nhất một người làm bước 7–9 trên điện thoại | Cột *Thiết bị* |

Không dùng dữ liệu thật của công ty trong buổi đầu: đặt tên nhóm bắt đầu bằng *THỬ —* để dọn sau.

## 2. Vòng chính (buổi đầu, cả đội cùng làm)

| # | Ai làm | Thao tác | Kết quả mong đợi |
|---|---|---|---|
| 1 | Người dẫn | Thanh bên trái › **Tạo nhóm dự án**, nhập *Tên nhóm dự án* = `THỬ — <tên đội>` | Nhóm hiện trên cây ở thanh bên |
| 2 | Người dẫn | Trong nhóm vừa tạo, **Tạo dự án** (nút *Dự án mới*), *Tên dự án* = `Việc tuần này` | Dự án mở ra ở khung kanban, có sẵn cột mặc định |
| 3 | Người dẫn | **Quản lý dự án** › **Mời người**: mời đủ đội, chọn *Vai trò cho người được mời* (1 *Quản trị*, còn lại *Thành viên*, 1 *Khách xem* nếu có) | Mỗi người được mời thấy dự án trong cây của mình (tải lại trang) |
| 4 | Quản trị | **Quản lý dự án** › **Thêm cột** một cột tên `Chờ duyệt` giữa *Đang làm* và *Xong* | Cột mới hiện trên kanban của cả đội |
| 5 | Mỗi thành viên | **Việc mới**: tạo 2 việc thật của mình trong tuần, có hạn | Việc hiện ở cột đầu |
| 6 | Người dẫn | Mở một việc, **Gán người phụ trách** cho **2 người** cùng lúc | Thẻ ghi *2 người phụ trách*; **cả hai** người nhận chuông *Bạn được giao việc: …* |
| 7 | Thành viên | Mở việc mình phụ trách, gắn **nhãn** (tạo nhãn mới nếu chưa có) và chọn **Loại việc** | Nhãn hiện trên thẻ kanban |
| 8 | Thành viên | Thêm 3 **việc con**, tick xong 1 | Thẻ cha hiện *1/3* |
| 9 | Thành viên | **Kéo thẻ** sang *Đang làm*, rồi *Chờ duyệt* | Người cùng việc nhận chuông đổi trạng thái; người khác tải lại thấy thẻ ở cột mới |
| 10 | Thành viên | Bình luận, **@nhắc** một người trong đội | Người được nhắc nhận chuông *Bạn được nhắc trong bình luận*, bấm chuông mở thẳng việc |
| 11 | Người viết bình luận | **Sửa bình luận** vừa viết | Bình luận mang nhãn *(đã sửa)*; không ai nhận thêm chuông |
| 12 | Quản trị | Tick xong mọi việc con, kéo thẻ sang *Xong* | Việc ở trạng thái hoàn thành; biến khỏi tab *Việc cần làm* của người phụ trách |
| 13 | Mỗi người | Trang cá nhân › **Việc của tôi** › tab **Việc cần làm** | Thấy đúng việc dự án mình **phụ trách** còn mở (nhãn *Việc được giao* / *Việc quá hạn*); việc chỉ theo dõi **không** có ở đây |
| 14 | Thành viên | Xóa một việc của mình, rồi **Quản lý dự án** › **Thùng rác** › **Khôi phục** | Việc quay lại đúng cột |
| 15 | Mỗi người | Rê chuột vào tên dự án ở thanh bên › **Ghim lên đầu danh sách** | Dự án lên khu *Đã ghim*; đổi trình duyệt vẫn còn |
| 16 | Khách xem | Thử kéo thẻ, thử bình luận, thử mở *Thùng rác* | Không làm được; không thấy mục *Thùng rác* |
| 17 | Người dẫn | Đổi khung nhìn sang **Danh sách** và **Gantt**, bật cột **Loại việc** ở menu *Cột* | Cột *Loại việc* mặc định ẩn, bật lên thì hiện đúng loại đã chọn ở bước 7 |

## 3. Năm ngày dùng thật

Sau buổi đầu, đội **dùng dự án `Việc tuần này` cho việc thật** trong 5 ngày làm việc, không chạy song song
công cụ cũ cho đúng các việc đã đưa vào. Cuối mỗi ngày mỗi người ghi một dòng: *hôm nay vướng gì, thiếu gì*.

## 4. Những thứ đã biết là CHƯA có (đừng ghi là lỗi)

Lấy từ `03-lo-trinh-phase.md` W2 và bài hướng dẫn *Dự án — Chuông báo giao việc và Việc cần làm*:

- **Nhắc hạn tự động** (đến hạn / quá hạn) qua chuông: chưa có.
- **Lọc theo điều kiện** trên thanh công cụ khung nhìn: chưa có (P0 còn thiếu của W2).
- **Kéo ngang đổi thứ tự cột**: chưa có; thẻ thì kéo được.
- Tab **Dashboard**, **Gom nhóm** ngoài cột: chưa có (P1).

Nếu đội thấy một trong các thứ trên **chặn** việc dùng thật thì vẫn ghi vào biên bản ở cột *Chặn MVP?* để
đại ca xếp thứ tự.

## 5. Mẫu biên bản

| # bước | Ai | Thiết bị | Giờ | Đạt / Không | Ghi chú (nhãn khác màn, chậm, khó hiểu) | Chặn MVP? |
|---|---|---|---|---|---|---|
| 1 | | | | | | |

Cuối biên bản: **Kết luận đội** (dùng tiếp / dùng tiếp nếu sửa X / không dùng) · **Ba việc nên sửa nhất** ·
**Ngày thử** · **Người dẫn**. Agent 2 gom biên bản, lỗi giao diện gửi Agent 3, lỗi máy chủ gửi Agent 1.

Tham chiếu: `03-lo-trinh-phase.md` W2 · `01-danh-sach-tinh-nang.md` · bài HDSD seed `backend/scripts/seed_help_cong_viec.py`.
