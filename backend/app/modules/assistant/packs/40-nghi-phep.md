# Nghỉ phép (phân hệ Nhân sự)

Phân hệ để nhân viên **nộp đơn nghỉ phép**, quản lý duyệt, và phòng Nhân sự cấp
**quỹ phép năm**. Vào bằng menu **Nhân sự ▸ Nghỉ phép**.

## Điều CẤM nói

- **Tuyệt đối không tiết lộ đơn nghỉ của người khác.** Lý do nghỉ là thứ riêng tư
  nhất trong cả hệ. Người dùng chỉ đọc được đơn trong phạm vi của họ; hệ trả
  **404 «Không tìm thấy»** chứ không trả 403, nên khi họ hỏi về một đơn không đọc
  được thì **đừng khẳng định đơn đó không tồn tại** — chỉ nói là không truy cập được.
- **Đừng đoán số ngày phép còn lại.** Con số đó chỉ có trên màn hình (ô cạnh «Loại
  nghỉ» và thẻ *Quỹ phép của tôi*). Bảo họ nhìn vào đó, đừng tự tính.

## Bốn khái niệm, đừng lẫn

| Thứ | Là gì |
|---|---|
| **Đơn nghỉ phép** | Chứng từ nghiệp vụ. Nguồn sự thật, có số `NP-xxx`. |
| **Giấy nghỉ phép (GNP)** | **Văn bản** trong phân hệ Văn thư, tự sinh **sau khi đơn đã duyệt**. Là hồ sơ lưu sổ, không phải thứ để nộp. |
| **Loại nghỉ** | Danh mục cấu hình (Phép năm, Nghỉ ốm, Thai sản…). Sửa được luật mà không cần lập trình. |
| **Quỹ phép** | Số ngày của **một người × một năm × một loại nghỉ**. |

Người dùng hỏi "làm giấy nghỉ phép" thì họ muốn **nộp đơn** ở
*Nhân sự ▸ Đơn nghỉ phép*, **không** phải tạo văn bản ở Văn thư. Giấy GNP hệ tự
sinh; tạo tay là ra một tờ giấy không gắn với quỹ phép nào.

## Vòng đời đơn — sáu trạng thái

`Nháp → Chờ duyệt → Đã duyệt`, cộng ba ngã rẽ: *Từ chối*, *Trả về chỉnh sửa*, *Đã hủy*.

- **Chỉ sửa được ở «Nháp» và «Trả về chỉnh sửa».** Đã gửi duyệt là khóa; muốn sửa
  thì hủy đơn rồi lập lại, hoặc chờ người duyệt trả về.
- **«Từ chối» khác «Trả về chỉnh sửa».** Từ chối là khóa hẳn — muốn nghỉ nữa thì
  lập **đơn khác**. Trả về là mời sửa rồi gửi lại chính tờ đơn đó.
- **Hủy đơn được cả khi đã duyệt** (đổi kế hoạch) — ngày phép được hoàn lại.
  Nhưng **chỉ chính người nộp** mới hủy được đơn đang nằm trong luồng duyệt;
  người khác phải dùng *Trả lại* / *Từ chối* ở màn **Phê duyệt**.

## Quỹ phép — bốn con số cộng, hai con số trừ

    còn lại = (hạn mức + thâm niên + chuyển năm trước + điều chỉnh tay) − đã nghỉ − đang chờ duyệt

- **«Đang chờ duyệt» ĐÃ bị trừ khỏi «còn lại».** Nộp đơn 3 ngày là số còn lại tụt
  ngay 3 ngày, chưa cần ai duyệt. Người dùng thấy hụt ngày mà chưa nghỉ hôm nào —
  giải thích chỗ này, đừng bảo họ hệ tính sai.
- **Thâm niên khai bằng bảng bậc**, mặc định *5 năm +1 · 10 năm +2 · 15 năm +3 ·
  20 năm trở lên +4*. Lấy **bậc cao nhất khớp được**, **không cộng dồn** — người
  10 năm được +2, không phải +3.
- Hồ sơ **chưa có ngày vào làm** thì thâm niên tính bằng **0** và quỹ có thể
  thiếu ngày. Màn hình có cảnh báo; bảo họ báo phòng Nhân sự nhập bổ sung.
- **Không có ứng phép, không ghi nợ.** Xin vượt quỹ là bị **chặn lúc gửi duyệt**.
  Muốn nghỉ tiếp thì chọn loại **«Nghỉ không lương»**.

## Số ngày nghỉ

Hệ tự tính và **đã trừ thứ Bảy, Chủ nhật và ngày lễ** (theo danh mục *Lịch ngày
lễ*). Người dùng **sửa đè được** con số đó — lịch làm việc thật có ngoại lệ máy
không biết (ca kíp, công trường chạy Chủ nhật).

Ngoại lệ: loại nghỉ dài liên tục như **Thai sản** cố ý **không** trừ cuối tuần và lễ.

## Vài luật hay bị hỏi

- **Nghỉ ốm không phải báo trước** (đúng vậy — không ai biết trước mai mình ốm),
  nhưng **có thể** phải đính kèm giấy khám bệnh.
- **Cưới hỏi và tang chế tối đa 3 ngày mỗi lần.**
- **Thai sản chỉ hiện với hồ sơ nữ.** Hồ sơ **chưa khai giới tính** thì **không bị
  chặn** — cứ nộp được.
- **Hai đơn không được chồng ngày** của cùng một người. Chồng thì cùng một ngày bị
  trừ phép hai lần.
- **Nghỉ từ buổi chiều đến buổi sáng cùng ngày** là khoảng trống — hệ chặn.
- Lập đơn **hộ người khác** được (hành chính, trợ lý). Cả người lập lẫn người nghỉ
  đều thấy tờ đơn đó.

## Bốn khóa quyền — đừng gộp

| Khóa | Mở màn nào |
|---|---|
| `leave_request` | Đơn nghỉ phép · Lịch nghỉ |
| `leave_balance` | Quỹ phép năm (cấp phát, **điều chỉnh tay**) |
| `leave_type` | Thiết lập ▸ Loại nghỉ (kèm bậc thâm niên) |
| `holiday` | Thiết lập ▸ Lịch ngày lễ |

Tách bốn vì **`leave_balance` ghi được nghĩa là tặng thêm ngày phép cho bất kỳ ai**.
Đó là việc của phòng Nhân sự (vai trò mẫu **`hr_leave`**), không phải của người nộp đơn.

⚠️ Bốn khóa này **mới thêm 03/09/2026**. Trên hệ đang chạy, các vai trò cũ
**không tự có** chúng — quản trị phải tick thêm ở *Nhân sự ▸ Phân quyền tài khoản*.
Người dùng báo "không thấy menu Nghỉ phép" thì gần như chắc là do chỗ này.

## Bảng từ dùng đúng

| Nói thế này | Đừng nói |
|---|---|
| Đơn nghỉ phép | phiếu nghỉ, đơn xin phép |
| Quỹ phép năm | số dư phép, tài khoản phép |
| Gửi duyệt | trình ký, submit |
| Trả về chỉnh sửa | trả lại (dễ lẫn với Từ chối) |
| Điều chỉnh tay | cộng phép, bù phép |
| Lịch ngày lễ | ngày nghỉ lễ (đó là danh mục, tên đúng là «Lịch ngày lễ») |
