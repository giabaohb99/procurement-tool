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

## Phép không dùng hết thì đi đâu (kết sổ cuối năm)

**Tùy từng loại nghỉ**, phòng Nhân sự khai ở *Thiết lập ▸ Loại nghỉ*. Ba nước:
**«Hết năm là mất»** (mặc định) · **«Mang sang năm sau»** · **«Quy đổi sang loại
nghỉ khác»** (đổi theo tỷ lệ, ví dụ 2 ngày phép đổi 1 ngày nghỉ bù).

- ⚠️ **Không có gì tự chạy đêm 31/12.** Phải có người của Nhân sự bấm nút **«Kết
  sổ năm …»** ở màn *Quỹ phép năm*. Người dùng hỏi *"sang năm rồi sao chưa thấy
  phép cũ"* thì đó là chưa ai bấm — bảo họ hỏi phòng Nhân sự, đừng nói hệ lỗi.
- **Phép mang sang có HẠN DÙNG**, thông lệ là **hết 31/3** năm sau (mỗi loại khai
  một hạn riêng, có thể để không hết hạn). Quá hạn là mất phần chưa dùng.
- **Phép mang sang được tiêu TRƯỚC phép của năm mới** — cố ý, vì nó sắp hết hạn.
- Đừng tự tính giúp họ mang được mấy ngày: con số đó nằm trên màn *Quỹ phép năm*.

## Một đơn khai được NHIỀU loại nghỉ

*"Nghỉ 4 ngày: 3 ngày phép năm + 1 ngày không lương"* — làm **trong một tờ đơn**,
không phải hai. Trên form, phần *Loại nghỉ* là một bảng: bấm **«Thêm loại nghỉ»**
để có dòng thứ hai, mỗi dòng chọn loại và ghi số ngày.

- **Cả đơn dùng chung một khoảng ngày.** Dòng chỉ chia số ngày, không khai ngày riêng.
- **Quỹ phép trừ theo từng loại** — 3 ngày vào quỹ phép năm, 1 ngày vào quỹ không
  lương. Số phép còn lại hiện ngay dưới từng dòng.
- **Một loại chỉ khai một dòng.** Muốn 3 ngày phép năm thì ghi 3 vào một dòng,
  đừng tách thành hai dòng 2+1.
- **Người dùng hỏi "hết phép năm rồi thì làm sao"**: thêm một dòng *Nghỉ không
  lương* cho phần vượt, thay vì lập đơn thứ hai — đơn thứ hai sẽ bị chặn vì
  **chồng ngày** với đơn đầu.
- **Nghỉ theo giờ thì chỉ một loại.**

## Số ngày nghỉ

Hệ tự tính và **đã trừ Chủ nhật + ngày lễ** (theo danh mục *Lịch ngày lễ*).

⚠️ **DEGO Holding làm cả ngày thứ Bảy** — T7 **vẫn tính là ngày phép**. Người
dùng hỏi *"sao nghỉ thứ Bảy vẫn bị trừ phép"* thì đó là đúng, không phải lỗi.

Người dùng **sửa đè được** con số đó — lịch làm việc thật có ngoại lệ máy không
biết (ca kíp, công trường chạy Chủ nhật). Đơn nhiều loại thì con số máy tính chỉ
là mốc đối chiếu; người dùng tự phân bổ vào từng dòng.

**Hai ô buổi nói MỐC, không nói buổi**: *Buổi bắt đầu = Sáng* nghĩa là nghỉ từ
đầu ngày đó (trọn ngày), *Buổi kết thúc = Chiều* nghĩa là nghỉ tới hết ngày đó
(trọn ngày). Muốn nghỉ đúng nửa ngày thì khai cùng một buổi ở cả hai ô.

Ngoại lệ: loại nghỉ dài liên tục như **Thai sản** cố ý **không** trừ cuối tuần và lễ.

## Vài luật hay bị hỏi

- **Nghỉ ốm không phải báo trước** (đúng vậy — không ai biết trước mai mình ốm),
  nhưng **có thể** phải đính kèm giấy khám bệnh.
- **Cưới hỏi và tang chế tối đa 3 ngày mỗi lần.**
- **Thai sản chỉ hiện với hồ sơ nữ.** Hồ sơ **chưa khai giới tính** thì **không bị
  chặn** — cứ nộp được.
- **«Nghỉ vợ sinh con» chỉ hiện với hồ sơ nam**, cần đính kèm giấy chứng sinh. Hệ
  chỉ chặn ở **trần 14 ngày** — đó là mức cao nhất của luật (sinh đôi trở lên, mổ);
  mức thường là 5 ngày, sinh mổ 7 ngày. **Đừng khẳng định họ được bao nhiêu ngày** —
  máy không biết ca nào, người duyệt quyết.
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
| Kết sổ cuối năm | chốt sổ, khóa sổ, chuyển phép tự động |
| Mang sang năm sau | bảo lưu phép, cộng dồn phép |
