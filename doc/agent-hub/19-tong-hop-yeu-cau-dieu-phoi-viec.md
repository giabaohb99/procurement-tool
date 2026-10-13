# Tổng hợp yêu cầu: Trợ lý AI điều phối công việc theo kế hoạch

> Bản 1.1 · 13/10/2026 · Trạng thái: thiết kế, chưa lập trình. Chi tiết kỹ thuật ở
> [`18-dieu-phoi-viec-theo-ke-hoach.md`](18-dieu-phoi-viec-theo-ke-hoach.md).

## 1. Mục tiêu

Một trợ lý AI chạy trên nền ERP và bot chat hiện có của DEGO. Người quản lý đưa danh sách việc, bot lập kế hoạch, hỏi
từng người nhận việc, theo dõi tiến độ, báo cáo khi xong và rút bài học cho lần sau. Mọi việc đều nằm trong phân hệ Dự
án của ERP nên người quản lý xem và sửa được trên màn hình như việc bình thường.

## 2. Cách hoạt động

```
Danh sách việc ──► Kế hoạch ──► Hỏi nhận việc ──► Duyệt và khóa ──► Báo bắt đầu ──► Theo dõi ──► Báo cáo ──► Bài học
  (chat, tệp)      (Dự án ERP)   (từng người)      (người quản lý)   (từng bên)     (hỏi tiến độ)  (Word/Excel)
```

1. **Lập kế hoạch.** Từ danh sách việc, bot đưa ra kế hoạch theo giai đoạn: việc cha, việc con, người làm, tiêu chí
   đánh giá cho từng việc nhỏ, mốc thời gian. Người quản lý sửa trực tiếp trên màn Dự án hoặc nhắn bot sửa.
2. **Hỏi nhận việc.** Bot nhắn từng người làm. Người làm trả lời: *nhận* · *nhận nhưng giờ khác* (ghi giờ) · *từ chối*
   kèm lý do. Bot ghi nhận và báo lại người quản lý.
3. **Duyệt và khóa.** Khi kế hoạch ổn, người quản lý duyệt. Bot báo *bắt đầu làm* và xác nhận với từng bên phần việc của họ.
4. **Theo dõi.** Tới mốc, bot hỏi: xong chưa; chưa thì bao nhiêu phần trăm, tự chấm 1–10; chưa làm thì lý do. Người làm
   cũng chủ động nhắn bot bất cứ lúc nào. Mỗi việc **xác nhận xong ngay trên bot**, bot ghi giờ bắt đầu và giờ xong.
5. **Xếp lại.** Có người báo giờ khác thì bot xếp lại mốc; trong ngưỡng cho phép thì tự dời, ngoài ngưỡng thì đề xuất để
   người quản lý duyệt rồi mới gửi lại cho mọi người.
6. **Báo cáo kết thúc.** So sánh kế hoạch với thực tế: việc nào trễ, tiêu chí nào đạt, kẹt ở đâu, của ai. Xuất Word hoặc Excel.
7. **Bài học.** Bot ghi lại việc loại nào hay trễ, ai hay quá tải, ước lượng nào sai; lần lập kế hoạch sau áp dụng và nói rõ.

Mỗi sáng bot gửi **bản tin kế hoạch và lịch trình hôm nay** cho người quản lý và cho từng người có việc trong ngày.

Bot hỏi và trả lời tự nhiên như bot chat hiện tại, không theo mẫu câu cố định; nút bấm chỉ là lối tắt.

## 3. Kênh liên lạc và quyền

- **Kênh:** Zalo qua tài khoản bot chung của công ty là kênh ưu tiên; Telegram là kênh phụ. Bot chỉ nhắn riêng từng
  người, không đăng vào nhóm.
- **Người nhận việc:** lấy từ hồ sơ nhân sự, có Zalo hoặc số điện thoại dùng Zalo. Nhắn không được thì bot gắn nhãn
  *Nhắn không được* lên việc và báo người quản lý.
- **Người quản lý kế hoạch:** ban đầu là ban lãnh đạo; về sau là người được cấp quyền này trên ERP.
- **Email công việc:** bot được cấp quyền đọc, không xóa, khi cấp trên duyệt. Cấp qua đăng nhập Google chính thức với
  phạm vi chỉ đọc; bot không giữ mật khẩu của ai; rút quyền được bất cứ lúc nào. Bot chỉ đọc thư liên quan việc đang
  theo dõi và ghi sổ từng lượt đọc.
- **Thao tác cần người quản lý duyệt:** ban hành kế hoạch, dời mốc ngoài ngưỡng, đổi người làm, đóng kế hoạch. Bot chỉ đề xuất.

## 4. Cấu trúc trong phân hệ Dự án

| Trong kế hoạch | Trong Dự án | Người quản lý thấy ở đâu |
|---|---|---|
| Kế hoạch | Bảng (danh sách) | Một bảng riêng trên màn Dự án |
| Giai đoạn | Cột kanban | Cột trên kanban, kéo thẻ qua lại được |
| Việc cha | Việc | Thẻ trên kanban và Gantt |
| Việc con | Việc con | Trong bảng chi tiết của việc cha |

Phân hệ cho hai tầng việc (việc con không có con nữa). Khi cần chia sâu hơn, bot nâng phần đó thành một việc cha mới
trong cùng giai đoạn, nối với việc gốc bằng liên kết *thuộc về*, và nói rõ khi làm vậy. Kế hoạch quá lớn thì mỗi giai
đoạn thành một bảng riêng.

## 5. Bộ quy tắc lập kế hoạch (bản nháp, người quản lý sửa trên màn cấu hình)

| Nhóm | Quy tắc |
|---|---|
| Ưu tiên | 3 mức: **Gấp** (trong ngày) · **Ưu tiên** (trong 3 ngày) · **Thường** (theo kế hoạch). Mặc định Thường. |
| Chia việc | Mỗi việc cha tối đa 7 việc con; việc con tối đa 2 ngày công, dài hơn thì chia tiếp. |
| Chọn người | Theo phòng ban và chức vụ trên hồ sơ; ưu tiên người đang ít việc mở nhất. Không có ai phù hợp thì để trống và hỏi. |
| Mốc thời gian | Việc con có ngày bắt đầu và hạn; việc cha lấy hạn muộn nhất của con. Không xếp việc vào Chủ nhật. |
| Tiêu chí đánh giá | Mỗi việc con 1–3 tiêu chí đo được. Thiếu thì dùng: hoàn thành đúng hạn và được người giao xác nhận. |
| Hỏi nhận việc | Gửi ngay sau khi duyệt. Trả lời trong 4 giờ làm việc; quá thì nhắc một lần; quá 1 ngày thì báo người quản lý. |
| Hỏi tiến độ | Đúng ngày hạn lúc 15:00 và ngày sau hạn lúc 08:00. |
| Dời lịch | Thường: tự dời tối đa 3 ngày nếu không đẩy hạn việc cha · Ưu tiên: tối đa 1 ngày · Gấp: không tự dời. |
| Nhắn không được | Thử 2 lần cách nhau 2 giờ; vẫn không được thì gắn nhãn lên việc và báo trong bản tin ngày. |
| Báo người quản lý | Một bản tin mỗi sáng gom mọi thay đổi; việc Gấp bị từ chối hoặc trễ thì báo ngay. |

## 6. Lộ trình

| Đợt | Nội dung | Điều kiện |
|---|---|---|
| 1 | **Chỉ ghi nhận việc, chưa nối phân hệ khác.** Lập kế hoạch vào Dự án, hỏi nhận việc, duyệt và khóa, báo bắt đầu, xác nhận xong trên bot và ghi giờ, bản tin sáng. Kênh Telegram. | Không |
| 2 | Nhắc mốc và hỏi tiến độ tự động; nhãn Nhắn không được; bản tin sáng cho từng người. | Đợt 1 |
| 3 | Kênh Zalo. | Quét QR tài khoản Zalo công ty |
| 4 | Báo cáo kết thúc Word / Excel, đẩy Drive; bài học cho lần sau. | Đợt 1 |
| 5 | Xếp lại kế hoạch: tự động trong ngưỡng, đề xuất ngoài ngưỡng. | Đợt 2 chạy ổn 2 tuần |
| 6 | Nối phân hệ ERP khi việc có công cụ tương ứng: Đặt xe, Duyệt dấu, đề nghị thanh toán tạm ứng, lịch Google. Việc không có công cụ thì vẫn chỉ ghi nhận xong. | Đợt 1 ổn |
| 7 | Đọc email công việc (chỉ đọc) gắn với việc đang theo dõi. | Cấp trên duyệt danh sách người nối |

Đợt 1 chỉ cần phân hệ Dự án và bot Telegram đang chạy, dùng được sớm nhất.

## 7. Ví dụ chi tiết

Người quản lý nhắn bot lúc 14:00 ngày 13/10: *ngày mai Bảo đi tiếp khách hàng Trung Quốc với anh, cả ngày, đón ở sân bay
Cần Thơ 8:00, ăn trưa, thăm nhà máy Dego Organic buổi chiều.*

### 7.1 Kế hoạch bot lập (người quản lý duyệt trước khi gửi)

Bảng trong Dự án: **Tiếp khách Trung Quốc 14/10**. Hai cột kanban là hai giai đoạn: **Chuẩn bị (13/10)** và **Ngày tiếp
khách (14/10)**. Mỗi việc cha có việc con; mỗi việc con có người làm, khung giờ, mức ưu tiên và tiêu chí đánh giá.

**Giai đoạn 1 — Chuẩn bị (13/10)**

| Việc cha → việc con | Người | Khung giờ | Ưu tiên | Tiêu chí đánh giá |
|---|---|---|---|---|
| **A. Bảo đi cùng cả ngày 14/10** | Bảo | | Ưu tiên | Cả 3 việc con đạt |
| A1. Xác nhận lịch, dời các việc khác của ngày 14/10 | Bảo | 13/10 14:00–16:00 | Ưu tiên | Lịch 14/10 không còn việc khác; bot thấy lịch Google trống |
| A2. Chuẩn bị hồ sơ giới thiệu công ty và bảng giá (bản tiếng Trung) | Bảo | 13/10 14:00–18:00 | Ưu tiên | Có tệp đính kèm trên việc, người quản lý xác nhận đã xem |
| A3. Chuẩn bị quà tặng khách | Bảo | 13/10 16:00–18:00 | Thường | Có ảnh quà đính kèm |
| **B. Tạm ứng chi phí tiếp khách** | Kế toán | | Gấp | Tiền có trong tay người đi trước 7:30 ngày 14/10 |
| B1. Lập đề nghị tạm ứng 15 triệu, trình duyệt | Kế toán | 13/10 14:00–15:00 | Gấp | Đề nghị tạm ứng được duyệt trước 16:00 |
| B2. Chi tiền mặt hoặc chuyển khoản cho Bảo | Kế toán | 13/10 15:00–17:00 | Gấp | Bảo xác nhận đã nhận trên bot |
| **C. Xe đưa đón** | Điều phối xe | | Gấp | Xe và tài xế có mặt tại điểm đón 7:30 ngày 14/10 |
| C1. Kiểm tra xe 7 chỗ còn trống ngày 14/10, tình trạng xe | Điều phối xe | 13/10 14:00–15:00 | Gấp | Ghi rõ biển số xe trên việc |
| C2. Xác nhận tài xế và số điện thoại | Điều phối xe | 13/10 14:00–15:00 | Gấp | Tên và số điện thoại tài xế ghi trên việc |
| C3. Lập phiếu đặt xe, trình duyệt | Điều phối xe | 13/10 15:00–16:00 | Gấp | Phiếu đặt xe được duyệt trước 17:00 |
| C4. Nhắn tài xế lộ trình: sân bay → nhà hàng → nhà máy → khách sạn | Điều phối xe | 13/10 16:00–17:00 | Thường | Tài xế xác nhận đã nhận lộ trình |

**Giai đoạn 2 — Ngày tiếp khách (14/10)**

| Việc cha → việc con | Người | Khung giờ | Ưu tiên | Tiêu chí đánh giá |
|---|---|---|---|---|
| **D. Đón và đưa khách** | Điều phối xe | | Gấp | Đúng giờ ở cả 3 điểm |
| D1. Xe có mặt sân bay | Tài xế | 14/10 7:30 | Gấp | Bot nhận xác nhận trước 7:35 |
| D2. Đưa khách đến nhà hàng trưa | Tài xế | 14/10 11:30 | Thường | Đến trước 11:45 |
| D3. Đưa khách về khách sạn | Tài xế | 14/10 17:00 | Thường | Tài xế báo xong |
| **E. Tiếp khách** | Bảo | | Ưu tiên | Có biên bản ghi nhớ nhu cầu khách |
| E1. Ghi chép yêu cầu, số lượng, giá khách quan tâm | Bảo | 14/10 9:00–17:00 | Ưu tiên | Biên bản đính kèm trước 20:00 cùng ngày |
| E2. Chụp ảnh buổi thăm nhà máy | Bảo | 14/10 14:00–16:00 | Thường | Ít nhất 5 ảnh đính kèm |
| **F. Quyết toán chi phí** | Bảo, Kế toán | | Thường | Hoàn ứng xong trong 2 ngày |
| F1. Bảo gửi hóa đơn, chứng từ | Bảo | 15/10 trước 12:00 | Thường | Đủ chứng từ theo số tiền đã chi |
| F2. Kế toán đối chiếu và hoàn ứng | Kế toán | 16/10 trước 17:00 | Thường | Số dư tạm ứng về 0 |

### 7.2 Bot hỏi nhận việc (13/10, 14:10)

Bot nhắn riêng Bảo, kế toán, điều phối xe; mỗi người thấy đúng phần việc của mình với khung giờ và tiêu chí. Ví dụ
kế toán trả lời: *B1 làm ngay được, B2 thì 17:30 mới chi được vì 16:00 em họp.* Bot ghi B2 dời sang 17:30 (trong ngưỡng
tự dời của việc Gấp là không, nên bot đề xuất và người quản lý duyệt), rồi báo lại người quản lý. Điều phối xe trả lời
*nhận hết*. Bảo trả lời *A3 nhờ Hành chính mua giúp được không* → bot đề xuất đổi người làm A3 sang Hành chính, người
quản lý duyệt.

### 7.3 Theo dõi trong ngày

- 15:00 ngày 13/10: bot hỏi điều phối xe C1, C2 xong chưa. Trả lời: *xong, xe 65A-123.45, tài xế anh Tâm 09xx*. Bot ghi
  giờ xong 14:50, tiêu chí đạt (có biển số, có tên và số điện thoại).
- 17:00: bot hỏi kế toán B2. Trả lời: *đã chuyển khoản 15 triệu cho Bảo*. Bot hỏi Bảo xác nhận; Bảo trả lời *đã nhận*.
  B2 xong lúc 17:25, tiêu chí đạt.
- 18:00: A2 chưa có tệp đính kèm. Bot hỏi Bảo: *A2 xong bao nhiêu phần trăm, chấm mấy điểm?* Bảo trả lời *80%, 7 điểm,
  còn phần bảng giá tiếng Trung, 21:00 xong*. Bot ghi tiến độ, dời hạn A2 sang 21:00 (trong ngưỡng), báo người quản lý.
- 08:00 ngày 14/10: bản tin sáng gửi người quản lý và từng người: lịch trình D1 → E1 → D2 → E2 → D3, kèm việc còn mở.

### 7.4 Báo cáo kết thúc (bot lập ngày 16/10 sau khi F2 xong)

| Việc | Kế hoạch | Thực tế | Tiêu chí | Tự chấm | Ghi nhận |
|---|---|---|---|---|---|
| A1 | 13/10 16:00 | 13/10 15:40 | Đạt | 9 | |
| A2 | 13/10 18:00 | 13/10 21:10 | Đạt, trễ 3 giờ | 7 | Thiếu người dịch bảng giá tiếng Trung |
| A3 | 13/10 18:00 | 13/10 17:20 | Đạt | 8 | Đổi người làm sang Hành chính |
| B1 | 13/10 15:00 | 13/10 14:45 | Đạt | 9 | |
| B2 | 13/10 17:00 | 13/10 17:25 | Đạt, dời có duyệt | 8 | Kế toán trùng lịch họp |
| C1–C4 | 13/10 17:00 | 13/10 16:30 | Đạt | 9 | |
| D1 | 14/10 7:30 | 14/10 7:40 | Không đạt, trễ 10 phút | 6 | Kẹt xe cầu Cần Thơ; lần sau xuất phát sớm 15 phút |
| D2, D3 | đúng giờ | đúng giờ | Đạt | 9 | |
| E1 | 14/10 20:00 | 14/10 22:30 | Đạt, trễ 2,5 giờ | 7 | Biên bản dài, nên ghi ngay trong ngày |
| E2 | 14/10 16:00 | 14/10 15:30 | Đạt | 9 | |
| F1 | 15/10 12:00 | 15/10 10:00 | Đạt | 9 | |
| F2 | 16/10 17:00 | 16/10 11:00 | Đạt | 9 | |

Tổng kết: 16 việc con, 15 đạt tiêu chí, 1 không đạt (D1); 3 việc trễ hạn, 2 việc dời có duyệt, 1 việc đổi người. Điểm tự
chấm bình quân 8,2. Kẹt ở: đón sân bay (giờ xuất phát) và tài liệu tiếng Trung (thiếu người dịch). Bot xuất Word và Excel,
đẩy lên Drive của người quản lý.

### 7.5 Bài học cho lần sau

- Việc đón khách ở sân bay: xuất phát sớm 15 phút so với giờ hẹn.
- Tài liệu tiếng Trung: thêm việc con *đặt dịch* từ trước 2 ngày, giao phòng Thiết kế hoặc thuê ngoài.
- Việc chi tiền của kế toán: đặt trước 15:00 để không trùng giờ họp cố định 16:00.

Lần sau người quản lý nhắn *tiếp khách Hàn Quốc tuần sau*, bot lập kế hoạch với 3 điểm trên đã sửa và nói rõ đã áp dụng
bài học nào. Ở đợt 1, mọi việc trên chỉ là việc trong Dự án và xác nhận trên bot; từ đợt 6, B1 và C3 sẽ do bot soạn sẵn
phiếu để đưa duyệt.

## 8. Ngoài phạm vi giai đoạn này

- Bot tự gửi, sửa hoặc xóa email thay người khác.
- Bot tự ban hành kế hoạch hoặc tự đổi người làm khi chưa có duyệt.
- Dùng điểm tự chấm để xét lương thưởng; điểm chỉ phục vụ theo dõi tiến độ.

## 9. Điều kiện cần

- Hồ sơ nhân sự đủ chức vụ và số điện thoại (hiện 25 hồ sơ chưa có chức vụ) để bot chọn người đúng.
- Tài khoản Zalo công ty được quét QR để mở kênh Zalo (đợt 3).
- Bộ quy tắc ở mục 5 được người quản lý rà và sửa sau 1–2 kế hoạch chạy thật.
