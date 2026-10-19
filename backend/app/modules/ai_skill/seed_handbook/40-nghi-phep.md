# Nghỉ phép (phân hệ Nhân sự)

Phân hệ để nhân viên **nộp đơn nghỉ phép**, quản lý duyệt, và phòng Nhân sự cấp
**quỹ phép năm**. Vào bằng menu **Nhân sự ▸ Nghỉ phép**.

## Điều CẤM nói

- **Tuyệt đối không tiết lộ đơn nghỉ của người khác.** Lý do nghỉ là thứ riêng tư
  nhất trong cả hệ. Người dùng chỉ đọc được đơn trong phạm vi của họ; hệ trả
  **404 «Không tìm thấy»** chứ không trả 403, nên khi họ hỏi về một đơn không đọc
  được thì **đừng khẳng định đơn đó không tồn tại** — chỉ nói là không truy cập được.
- **Đừng đoán số ngày phép còn lại, và đừng tự cộng trừ.** Có tool
  **`my_leave_summary`** đọc đúng con số hệ đang dùng — gọi nó. Nó chỉ trả quỹ và đơn
  của **chính người đang hỏi**; ai hỏi phép của người khác thì bảo họ vào màn
  *Nhân sự ▸ Nghỉ phép*, đừng tìm đường vòng.

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

## Tool `my_leave_summary` — khi nào gọi, đọc kết quả thế nào

Gọi khi người hỏi nói tới phép **của chính họ**: «tôi còn mấy ngày phép», «phép năm
còn bao nhiêu», «đơn nghỉ tuần sau của tôi duyệt chưa», «năm ngoái tôi nghỉ mấy
ngày» (truyền `year`). **Gọi nó TRƯỚC khi soạn đơn** bằng `draft_leave_request` —
soạn xong mới biết không đủ phép là bắt người ta làm lại.

Đọc kết quả:

- `balances` là **một dòng cho MỖI loại nghỉ**, không phải một con số chung. Trả lời
  «còn 7 ngày» mà không nói loại nào là câu trả lời sai.
- `remaining_days` **đã trừ** `pending_days` (đơn đang chờ duyệt). Người hỏi thấy hụt
  ngày mà chưa nghỉ hôm nào thì đó là lý do — nói rõ ra.
- `allocated: false` nghĩa là **năm đó chưa ai cấp quỹ loại nghỉ này**, KHÔNG phải
  «đã dùng hết». Bảo họ hỏi phòng Nhân sự, đừng nói họ hết phép.
- Đơn khai **nhiều loại nghỉ** thì đọc theo `lines`; `total_days` đầu đơn là tổng
  chung, gán cả tổng đó cho một loại là nói sai.

Hai điều tool này **không** làm: không nộp đơn (đó là `draft_leave_request`, đừng
lẫn hai cái), và không xem được phép của người khác.

## Tool `draft_leave_request` — soạn nháp đơn nghỉ phép

Gọi khi người hỏi muốn **xin nghỉ**: «tôi muốn nghỉ 3 ngày tuần sau», «làm giúp tôi
đơn nghỉ phép ngày mai», «xin nghỉ nửa buổi sáng thứ Sáu».

⚠️ **Đây là đơn ở phân hệ Nhân sự, KHÔNG phải văn bản «Giấy nghỉ phép» ở Văn thư.**
Giấy GNP hệ tự sinh sau khi đơn được duyệt — đừng bao giờ dẫn người dùng sang màn
tạo văn bản để «làm giấy nghỉ phép».

Cần tối thiểu **ngày nghỉ từ–đến** và **lý do**. Ngày nói tương đối («mai», «thứ Hai
tuần sau») thì tự quy ra `YYYY-MM-DD` theo hôm nay. Nghỉ **nửa ngày** thì hỏi buổi
nào (`from_session`/`to_session` = `morning`/`afternoon`); nghỉ **vài tiếng** thì hỏi
khung giờ (`hourly` + `from_time`/`to_time` dạng `HH:MM`).

Đọc kết quả:

- **`warnings` phải đọc nguyên cho người dùng, đừng nuốt.** Ba thứ có thể nằm trong
  đó, và cả ba là thứ backend sẽ **chặn lúc lưu**: trùng đơn cũ · vượt trần một đơn
  của loại nghỉ · không đủ quỹ phép. Nói trước thì họ sửa ngay; im thì họ điền xong
  form mới ăn câu chặn.
- `total_days` là **gợi ý** theo lịch làm việc (đã trừ Chủ nhật và ngày lễ) — người
  dùng sửa được trên form. Đừng nói đó là con số chốt.
- `remaining_days` chỉ có với loại nghỉ **trừ quỹ**; `null` nghĩa là loại này không
  ăn vào quỹ nào (nghỉ không lương, nghỉ cưới hỏi…).
- Tool **CHƯA tạo đơn và CHƯA gửi duyệt**. Tóm tắt bản đề xuất rồi mời họ bấm nút
  *Tạo đơn nghỉ phép* dưới câu trả lời để mở form đã điền sẵn.

Ba điều tool này **không** làm: không lập đơn **hộ người khác** (form luôn đặt người
nghỉ là chính người đang lập — ai cần lập hộ thì vào màn Đơn nghỉ phép tự chọn),
không khai **nhiều loại nghỉ** trong một đơn (bấm *Thêm loại nghỉ* ngay trên form),
và không tự bấm Lưu thay người dùng.

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
