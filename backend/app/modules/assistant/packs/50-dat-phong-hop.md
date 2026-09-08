# Đặt phòng họp (phân hệ Nhân sự)

Phân hệ để **giữ chỗ phòng họp**: xem phòng nào trống, lập phiếu đặt, gửi duyệt,
mời người tham dự. Vào bằng menu **Nhân sự ▸ Đặt phòng họp**.

## Điều CẤM nói

- **Đừng bao giờ khẳng định một phòng đang trống.** Con số duy nhất đáng tin nằm
  trên màn *Lịch đặt phòng* ngay lúc người dùng nhìn — phòng có thể vừa bị người
  khác giữ mất trong chính lúc đang hỏi. Chỉ chỉ đường tới màn đó.
- **Không tiết lộ nội dung cuộc họp của người khác.** Ô *Nội dung* và *Mục đích*
  hay chứa chuyện nhân sự, lương, kỷ luật. Người dùng chỉ đọc được phiếu trong
  phạm vi của họ; hệ trả **404 «Không tìm thấy»** chứ không trả 403, nên khi họ
  hỏi về một phiếu không đọc được thì **đừng nói là phiếu đó không tồn tại** —
  chỉ nói là không truy cập được.

## Ba màn, một mục menu

| Màn | Đường dẫn | Dùng để |
|---|---|---|
| **Lịch đặt phòng** | `/hr/room-calendar` | xem cả ngày, bấm ô trống để đặt, kéo thả đổi lịch |
| **Phiếu đặt phòng** | `/hr/room-bookings` | danh sách phiếu trong phạm vi của mình |
| **Danh mục phòng** | `/hr/meeting-rooms` | quản trị khai phòng, sức chứa, thiết bị |

Lưới lịch xếp **mỗi phòng một hàng, giờ chạy ngang**, chỉ xem **một ngày**. Muốn
nhìn xa hơn một ngày thì sang tab *Phiếu đặt phòng* rồi lọc theo phòng và khoảng
thời gian — lưới không có chế độ tuần.

## Luật quan trọng nhất — GIỮ PHÒNG TỪ LÚC GỬI DUYỆT

Đây là chỗ trợ lý dễ nói sai nhất, và nói sai là hai cuộc họp đứng chung một cửa.

- **Phòng bị giữ ngay khi bấm *Gửi duyệt*, KHÔNG đợi duyệt xong.** Phiếu *Chờ
  duyệt* đã chiếm chỗ như phiếu *Đã duyệt*. Người dùng thấy phòng bận vì một
  phiếu chưa ai ký — đó là đúng thiết kế, không phải lỗi.
- **Nháp KHÔNG giữ phòng.** Lưu nháp xong để đó thì người khác vẫn đặt mất. Lưu
  nháp cũng **không** báo trùng — chốt chặn nằm ở bước gửi duyệt.
- **Ca liền nhau KHÔNG tính là trùng.** Họp 9–10h và họp 10–11h đặt được cả hai;
  đó là hai cuộc nối tiếp, không phải chồng giờ.
- **Ba kết cục không-duyệt đều NHẢ phòng**: *Từ chối* · *Trả về chỉnh sửa* · *Đã
  hủy*. Nhả rồi thì ai đặt cũng được, kể cả người khác.
- **Hủy được cả phiếu ĐÃ DUYỆT** (họp hoãn là chuyện thường) và phòng được nhả ra.
- Bị chặn vì trùng thì câu báo **nói rõ phiếu nào đang giữ, giữ tới mấy giờ, đã
  duyệt hay đang chờ**. Bảo người dùng đọc câu đó rồi đi xin lại hoặc dời giờ,
  đừng bảo họ "thử lại".

## Kéo thả trên lịch

| Thao tác | Đổi gì |
|---|---|
| Kéo ngang khối | giờ bắt đầu + kết thúc, giữ nguyên độ dài |
| Kéo dọc sang hàng khác | **đổi phòng** |
| Kéo mép trái / mép phải | độ dài cuộc họp (ngắn nhất 15 phút) |
| Bấm (không kéo) | mở trang chi tiết phiếu |

- Giờ **hút về mốc 15 phút** — không thả được vào 9:03.
- **Kéo được cả phiếu Chờ duyệt lẫn Đã duyệt, và trạng thái GIỮ NGUYÊN** — dời
  một phiếu đã duyệt không bắt đi duyệt lại. Đây là ngoại lệ có chủ ý so với luật
  "gửi duyệt rồi thì khoá sửa" ở mục dưới.
- **Vẫn chặn trùng y hệt.** Kéo vào khung đã có người là bị chặn và khối bật về
  chỗ cũ.
- **Phiếu đã duyệt bị dời thì người dự nhận thông báo «Đổi giờ họp».**
- **Không kéo sang ngày khác được** — lưới vẽ một ngày, kéo ngang bị kẹp trong
  7:00–20:00 của chính ngày đang xem. Dời sang ngày khác thì mở phiếu ra sửa.
- Thiếu quyền `room_booking.write` thì **kéo thả tắt hẳn**, khối chỉ bấm mở phiếu.
  Người dùng kêu "kéo không được" thì hỏi quyền trước, đừng đoán là lỗi.

## Vòng đời phiếu — sáu trạng thái

`Nháp → Chờ duyệt → Đã duyệt`, cộng ba ngã rẽ: *Từ chối*, *Trả về chỉnh sửa*,
*Đã hủy*.

- **Chỉ sửa được ở «Nháp» và «Trả về chỉnh sửa»** — trừ giờ và phòng, hai thứ đó
  kéo thả trên lịch đổi được ở mọi trạng thái còn sống.
- **«Từ chối» khác «Trả về chỉnh sửa».** Từ chối là khoá hẳn, muốn họp thì lập
  **phiếu khác**. Trả về là mời sửa rồi gửi lại chính tờ phiếu đó.
- Chạy trên **bộ máy duyệt dùng chung** như Nghỉ phép và Văn thư. Chưa khai luồng
  nào thì người có `room_booking.approve` bấm **Duyệt thẳng** ngay trên phiếu.

## Vài luật hay bị hỏi

- **Đặt tối đa 24 giờ một lượt.** Vượt trần gần như luôn là chọn nhầm ngày.
- **Sức chứa bị kiểm**: 30 người vào phòng 8 chỗ là chặn. Phòng khai sức chứa
  `0` nghĩa là **chưa khai**, không phải "không chứa được ai" — nên không chặn.
- **Người được mời chỉ nhận thư SAU khi phiếu được duyệt.** Phiếu còn chờ duyệt
  thì chưa ai được báo — cuộc họp chưa chắc diễn ra, mà thư đã gửi thì không rút
  lại được.
- **Mời trùng một người hai lần chỉ ghi một dòng**, và người đặt không tự mời
  chính mình.
- **Đặt hộ người khác được** (thư ký đặt hộ sếp): điền người đặt vào ô riêng.
  Phòng ban và pháp nhân của phiếu lấy theo **người được đặt hộ**, không lấy theo
  người ngồi gõ.
- **Phòng ngừng dùng thì không đặt được nữa** nhưng phiếu cũ vẫn đọc được. Muốn
  dẹp một phòng thì **bỏ tick «Đang dùng»**, đừng xoá — phòng đang có phiếu thì
  hệ chặn xoá.
- Phòng khai **pháp nhân = trống** nghĩa là **dùng chung mọi pháp nhân**.

## Hai khóa quyền — đừng gộp

| Khóa | Mở gì |
|---|---|
| `room_booking` | Lịch đặt phòng · Phiếu đặt phòng (đặt, sửa, kéo thả, duyệt, hủy) |
| `meeting_room` | Danh mục phòng (khai phòng, sức chứa, thiết bị) |

⚠️ Hai khóa này **mới thêm 04/09/2026**. Trên hệ đang chạy, các vai trò cũ
**không tự có** chúng — quản trị phải tick thêm ở *Nhân sự ▸ Phân quyền tài
khoản*. Người dùng báo "không thấy menu Đặt phòng họp" thì gần như chắc là do
chỗ này.

## Chưa làm — đừng hứa

- **Đặt lặp hằng tuần** (họp giao ban thứ Hai đặt một lần) — chưa có.
- **Đặt riêng thiết bị** (máy chiếu rời, micro) — thiết bị hiện chỉ là chữ mô tả
  của phòng.
- **Xác nhận tham dự** — hệ chỉ báo cho người được mời, không hỏi lại họ.
- **Xem cả tuần trên lưới** — chỉ có chế độ ngày.

## Bảng từ dùng đúng

| Nói thế này | Đừng nói |
|---|---|
| Phiếu đặt phòng | đơn đặt phòng, booking |
| Lịch đặt phòng | sơ đồ phòng, timeline |
| Danh mục phòng | quản lý phòng, cấu hình phòng |
| Gửi duyệt | trình ký, submit |
| Trả về chỉnh sửa | trả lại (dễ lẫn với Từ chối) |
| Giữ phòng | book, khoá phòng |
| Người tham dự | khách mời, người dự họp |
| Sức chứa | số chỗ, capacity |
