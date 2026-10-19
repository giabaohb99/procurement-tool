# Dự án — quản lý công việc (tri thức nền)

Phân hệ **Dự án** (`/project`, chỉ có trên ERP v2): giao việc, theo dõi tiến độ,
trao đổi quanh từng công việc. Dựng theo Lark Tasks.

Gói này là **luật nghiệp vụ** — thứ trợ lý không được nói sai. Cần **các bước bấm
nút chi tiết** thì tra HDSD bằng `search_docs`, đừng tự bịa đường đi.

---

## 1. Bốn tầng — gọi sai tầng là người dùng tìm không ra nút

| Từ ĐÚNG trên màn hình | Là gì |
|---|---|
| **Nhóm** | Thư mục chứa dự án, tối đa 2 cấp. Thành viên nhóm **kế thừa** xuống mọi dự án trong nhóm |
| **Dự án** | Một danh sách công việc. **Đơn vị phân quyền chính** |
| **Cột** | Một cột kanban — nhãn người dùng tự đặt |
| **Công việc** | Một việc, nằm trong đúng một cột |
| **Việc con** | Việc nhỏ bên trong một công việc |
| **Cột mốc** | Công việc chỉ có MỘT ngày (hạn); Gantt vẽ hình thoi |

⚠️ **«Dự án» và «danh sách công việc» là MỘT thứ**, không phải hai tầng chồng nhau.
Đừng nói với người dùng là "tạo danh sách trong dự án".

⚠️ Đừng dùng chữ **«task»** trần với người dùng — trên màn hình là **«công việc»**.
(Chữ "task" trong hệ đã bị bộ máy duyệt và tab «Việc cần làm» chiếm.)

---

## 2. LUẬT QUAN TRỌNG NHẤT: cột kanban ≠ trạng thái

Đây là chỗ trợ lý dễ trả lời sai nhất, và sai thì người dùng tưởng đã xong việc.

| | **Cột kanban** | **Trạng thái** |
|---|---|---|
| Giá trị | Bất kỳ, từng dự án tự đặt (`Đã chạy`, `Chờ duyệt`…) | Cố định: **Đang mở · Hoàn thành · Đã hủy** |
| Đổi bằng | Kéo thẻ sang cột khác | **Tick ô tròn** trên thẻ/dòng, hoặc chọn trong panel |
| Dùng để | Xếp việc theo quy trình riêng của đội | Đếm việc chưa xong, báo cáo |

**Kéo việc vào cột tên «Xong» KHÔNG làm nó thành «Hoàn thành».**

Người dùng hỏi *"tôi kéo vào cột Xong rồi mà sao vẫn tính chưa xong?"* → trả lời:
cột chỉ là nhãn tự đặt, phải **tick ô tròn** ở đầu thẻ (hoặc đổi trạng thái trong
panel chi tiết). Đừng bảo họ liên hệ quản trị.

---

## 3. Phân quyền — KHÁC hẳn phân hệ chứng từ

**Hai lớp, phải qua cả hai:**

1. **Vai trò hệ thống** — khóa `work_task`. Chỉ là cửa vào phân hệ.
2. **Tư cách THÀNH VIÊN của dự án** — quyết định thật sự.

⚠️ **KHÔNG có "phạm vi phòng ban / pháp nhân"** ở đây. Có `work_task.read` toàn hệ
vẫn **không** đọc được dự án mình không tham gia. Đừng giải thích quyền của phân hệ
này bằng ngôn ngữ phạm vi dữ liệu của thu mua.

### Bốn vai trò trong một dự án

| Vai trò | Làm được |
|---|---|
| **Khách xem** | Đọc mọi thứ kể cả bình luận. KHÔNG sửa, KHÔNG gửi bình luận, KHÔNG thêm/gỡ tệp |
| **Thành viên** | Tạo/sửa việc, kéo thả, tick xong, bình luận, đính kèm |
| **Quản trị** | Thêm: sửa cột, khai trường tùy biến, mời/gỡ thành viên |
| **Chủ sở hữu** | Thêm: đổi tên dự án, lưu trữ, chuyển quyền sở hữu |

Vai trò hiệu lực = **CAO NHẤT** trong mọi nguồn (mời riêng + kế thừa từ nhóm).
Khách xem ở dự án nhưng Quản trị ở nhóm chứa nó → hiệu lực **Quản trị**.

Mỗi dự án luôn **đúng một** chủ sở hữu; chủ muốn rời phải **chuyển quyền trước**.

### Hai câu trả lời phải đúng

- *"Sao tôi không thấy dự án của anh A?"* → vì **chưa được mời vào dự án đó** (hoặc
  vào nhóm chứa nó). Cách ra: nhờ **Quản trị hoặc Chủ sở hữu của chính dự án đó**
  mời vào. Không phải việc của quản trị hệ thống.
- *"Sao tôi không bình luận được?"* → nhiều khả năng đang là **Khách xem**. Khách xem
  đọc được nhưng không gửi được.

⚠️ Tài khoản **chưa gắn hồ sơ nhân sự** không tham gia dự án được. Hệ báo rõ; việc
phải làm là **nhờ quản trị gắn nhân sự cho tài khoản**, không phải cấp thêm quyền.

---

## 4. Bốn khung nhìn

| Tab | Là gì |
|---|---|
| **Bảng** | Kanban, kéo thả thẻ và cột |
| **Danh sách** | Bảng phẳng, gom theo cột, sửa ngay trên dòng |
| **Gantt** | Lưới trái = chính khung Danh sách + trục thời gian; kéo thanh dời lịch, mũi tên phụ thuộc, cột mốc hình thoi |
| **Hoạt động** | Nhật ký gộp CẢ DỰ ÁN |

**Chưa có tab Dashboard** — đừng hứa có biểu đồ thống kê dự án.

### Về tab Hoạt động

Gộp ba nguồn: việc trong dự án (kể cả **việc đã xóa**) · thành viên vào-ra · sửa dự án
và cột. Lọc theo **loại sự kiện** và theo **người**.

⚠️ Hai điều **phải nói đúng**:
- **Bình luận KHÔNG nằm trong dòng hoạt động** (bình luận không ghi nhật ký thao tác).
- **Chưa lọc được theo MỘT công việc.** Panel chi tiết cũng không còn khối lịch sử
  riêng. Ai hỏi "xem lịch sử của riêng việc này ở đâu" → nói thẳng là hiện chưa có
  đường xem riêng, phải mở tab Hoạt động của dự án.

### Kéo thả không ăn?

Nguyên nhân hay gặp nhất: **đang sắp xếp theo tiêu chí khác «Tay (kéo thả)»** → hệ
khóa kéo, vì thả xong danh sách tự xếp lại chỗ cũ. Đổi lại ở nút **Sắp xếp**.

---

## 5. Trường tùy biến và Độ ưu tiên

Mỗi dự án **tự khai bộ trường riêng** (Quản lý dự án → Thiết lập). Sáu kiểu: chọn một ·
chọn nhiều · người · số · ngày · chữ.

⚠️ **«Độ ưu tiên» chỉ là một trường tùy biến nạp sẵn**, không phải thang cố định của hệ
thống: bậc và màu do từng dự án tự đặt, và **xóa được**. Vì vậy KHÔNG nói "hệ thống có
4 mức ưu tiên P1–P4" như một luật chung — phải xem dự án cụ thể.

Nút **Tùy chỉnh** quyết định trường nào hiện trên thẻ / cột bảng / lưới Gantt — **một
bộ cột dùng chung cho cả ba khung nhìn**.

---

## 6. Bình luận và đính kèm

- Bình luận: danh sách **phẳng** (chưa có luồng trả lời nhiều cấp), ô soạn ghim đáy panel.
- **@nhắc tên** → người bị nhắc **nhận chuông**, bấm vào mở thẳng đúng công việc.
- Kèm tệp vào bình luận: kẹp giấy, nút ảnh, **dán ảnh thẳng vào ô**, hoặc **kéo thả tệp**
  vào ô. **Tối đa 5 tệp** mỗi bình luận.
- Gửi: nút **Gửi** hoặc **Ctrl/Cmd + Enter**. Có tệp mà không gõ chữ vẫn gửi được.
- **Xóa** được bình luận của mình; **SỬA thì chưa có**.
- Đính kèm ở cấp công việc: tách riêng với tệp trong bình luận, **tối đa 50MB/tệp**.

⚠️ **Chưa có định dạng chữ** (đậm/nghiêng/danh sách) trong ô bình luận.

⚠️ **Tệp không có đường dẫn công khai** — tải phải qua nút trong hệ thống. Đừng hướng
dẫn người dùng dán link tệp ra ngoài hay chia sẻ đường dẫn; làm vậy sẽ bị từ chối.

---

## 7. Thông báo — nói đúng cái ĐÃ có

| Việc | Có bắn chuông? |
|---|---|
| Được **@nhắc tên** trong bình luận | **Có** |
| Có **bình luận mới** (người tạo việc + ai đã bình luận) | **Có** |
| **Được giao việc** | **CHƯA** |
| **Nhắc hạn** (đến hạn / quá hạn) | **CHƯA** |

⚠️ Đây là chỗ dễ hứa thừa. Người dùng hỏi *"giao việc cho ai đó thì họ có nhận được
thông báo không?"* → trả lời **chưa**, và bảo họ **@nhắc tên trong bình luận** nếu cần
báo gấp. Nói có là họ giao việc rồi ngồi chờ một cái chuông không bao giờ kêu.

---

## 8. Những thứ CHƯA có — đừng hứa

Dashboard thống kê dự án · nhắc hạn · việc của dự án trong tab «Việc cần làm» · màn
«Việc của tôi» gom việc mọi dự án · thùng rác khôi phục việc đã xóa · chuyển việc sang
dự án khác · sửa bình luận · định dạng chữ trong bình luận · gom nhóm kanban theo
người/ưu tiên/hạn (hiện chỉ gom theo cột).

⚠️ **«Xóa» dự án hoặc nhóm là LƯU TRỮ**, không xóa hẳn — nói đúng chữ này, kẻo người
dùng tưởng mất dữ liệu. Xóa **công việc** là xóa mềm (dữ liệu còn) nhưng **chưa có màn
thùng rác để tự khôi phục**.

---

## 9. Bảng từ dùng đúng

| Nói ĐÚNG | Đừng nói |
|---|---|
| Dự án | danh sách công việc, list, board |
| Công việc | task, đầu việc |
| Cột | trạng thái, giai đoạn, stage |
| Việc con | subtask, task con |
| Cột mốc | milestone, mốc |
| Khách xem / Thành viên / Quản trị / Chủ sở hữu | viewer, member, admin, owner |
| Tick ô tròn để đánh dấu hoàn thành | kéo sang cột Xong |
| Lưu trữ dự án | xóa dự án |
