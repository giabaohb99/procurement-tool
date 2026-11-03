# Nghỉ phép (phân hệ Nhân sự)

Phân hệ để nhân viên **nộp đơn nghỉ phép**, quản lý duyệt, và phòng Nhân sự cấp
**quỹ phép năm**. Vào bằng menu **Nhân sự ▸ Nghỉ phép**.

## Điều CẤM nói

- **Tuyệt đối không tiết lộ đơn nghỉ của người khác.** Lý do nghỉ là thứ riêng tư
  nhất trong cả hệ. Người dùng chỉ đọc được đơn trong phạm vi của họ; hệ trả
  **404 *Không tìm thấy*** chứ không trả 403, nên khi họ hỏi về một đơn không đọc
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
| **Loại nghỉ** | Danh mục cấu hình (Phép năm, Nghỉ ốm, Thai sản…). Sửa được luật mà không cần lập trình. Có sẵn năm loại chế độ BHXH riêng (BHXH chi trả, không trừ quỹ phép): Nghỉ khám thai, Nghỉ sảy thai/phá thai, Nghỉ thực hiện biện pháp tránh thai, Nghỉ chăm con ốm, Nghỉ dưỡng sức phục hồi sức khỏe — mức luật ghi ở ghi chú từng loại. |
| **Quỹ phép** | Số ngày của **một người × một năm × một loại nghỉ**. |
| **Phiếu nghỉ bù** (`NB…`) | Đã **đi làm** ngày lễ / ngày nghỉ theo lịch → xin **cộng thêm** ngày vào quỹ. **Không phải đơn nghỉ**: duyệt xong mới có ngày, rồi nộp đơn nghỉ loại nghỉ bù để dùng. |

Người dùng hỏi "làm giấy nghỉ phép" thì họ muốn **nộp đơn** ở
*Nhân sự ▸ Đơn nghỉ phép*, **không** phải tạo văn bản ở Văn thư. Giấy GNP hệ tự
sinh; tạo tay là ra một tờ giấy không gắn với quỹ phép nào.

## Vòng đời đơn — sáu trạng thái

`Nháp → Chờ duyệt → Đã duyệt`, cộng ba ngã rẽ: *Từ chối*, *Trả về chỉnh sửa*, *Đã hủy*.

- **Chỉ sửa được ở *Nháp* và *Trả về chỉnh sửa*.** Đã gửi duyệt là khóa; muốn sửa
  thì hủy đơn rồi lập lại, hoặc chờ người duyệt trả về.
- ***Từ chối* khác *Trả về chỉnh sửa*.** Từ chối là khóa hẳn — muốn nghỉ nữa thì
  lập **đơn khác**. Trả về là mời sửa rồi gửi lại chính tờ đơn đó.
- **Hủy đơn được cả khi đã duyệt** (đổi kế hoạch) — ngày phép được hoàn lại.
  Nhưng **chỉ chính người nộp** mới hủy được đơn đang nằm trong luồng duyệt;
  người khác phải dùng *Trả lại* / *Từ chối* ở màn **Phê duyệt**.

## Quỹ phép — năm con số cộng, hai con số trừ

    còn lại = (hạn mức + thâm niên + chuyển năm trước + điều chỉnh tay + nghỉ bù cộng thêm) − đã nghỉ − đang chờ duyệt
              (− phần CHƯA TỚI THÁNG nếu loại nghỉ cộng dần theo tháng)

- ⚠️ **Hỏi "còn bao nhiêu phép" thì gọi `my_leave_summary` và đọc `remaining_days`** — đó là đúng con số form nộp
  đơn, bảng Quỹ phép năm và báo cáo đang dùng. **Đừng tự lấy hạn mức năm trừ đi** (sai với loại cộng dần, sai khi
  có nghỉ bù, sai khi có ứng phép).

- ***Đang chờ duyệt* ĐÃ bị trừ khỏi *còn lại*.** Nộp đơn 3 ngày là số còn lại tụt
  ngay 3 ngày, chưa cần ai duyệt. Người dùng thấy hụt ngày mà chưa nghỉ hôm nào —
  giải thích chỗ này, đừng bảo họ hệ tính sai.
- **Thâm niên khai bằng bảng bậc**, mặc định *5 năm +1 · 10 năm +2 · 15 năm +3 ·
  20 năm trở lên +4*. Lấy **bậc cao nhất khớp được**, **không cộng dồn** — người
  10 năm được +2, không phải +3.
- Hồ sơ **chưa có ngày vào làm** thì thâm niên tính bằng **0** và quỹ có thể
  thiếu ngày. Màn hình có cảnh báo; bảo họ báo phòng Nhân sự nhập bổ sung.
- **Ứng phép: mặc định KHÔNG cho**, xin vượt quỹ là bị **chặn lúc gửi duyệt** — muốn nghỉ tiếp thì thêm dòng
  ***Nghỉ không lương***. Nhân sự bật được **theo từng loại nghỉ** bằng ô ***Cho ứng phép tối đa (ngày)*** (trần 30):
  khi đó còn lại được xuống tới **âm** số đó (cột *Còn lại* hiện số âm = đã dùng trước), vượt nữa vẫn bị chặn. Trong
  kết quả tool là `max_negative_days` (0 = không cho ứng). Đừng hứa ứng phép khi số đó bằng 0.

## Loại nghỉ cấp quỹ thế nào (từ 02/11/2026)

Nhân sự khai ở *Thiết lập ▸ Loại nghỉ* (tab *Thông tin* / *Bậc thâm niên* / *Hạn mức theo nhóm*). Tool trả
`accrual_mode_label` cho từng loại:

| Cách cấp | Nghĩa |
|---|---|
| **Đủ hạn mức đầu năm** (mặc định) | Đầu năm có đủ số ngày. |
| **Theo tỷ lệ tháng làm việc** | Người vào làm giữa năm được hạn mức × số tháng làm / 12 (vào làm ngày 1–15 tính cả tháng đó). |
| **Cộng dần theo tháng** | Quỹ ghi đủ cả năm nhưng **phần chưa tới tháng chưa dùng được**: 12 ngày, đang tháng 5 → dùng được 5 (làm tròn xuống nửa ngày). Tool trả phần này ở `not_yet_accrued_days`. Thâm niên, phép chuyển sang, điều chỉnh tay, nghỉ bù không bị cộng dần. |

- **Hạn mức theo nhóm**: một loại nghỉ có thể khai hạn mức riêng theo **hình thức nhân viên** (chính thức, thử việc…)
  hoặc **cấp bậc**; ưu tiên hình thức → cấp bậc → hạn mức chung. Quỹ đã cấp **không tự tính lại** khi Nhân sự đổi luật —
  người dùng hỏi "sao đổi rồi mà quỹ tôi không đổi" thì bảo họ nhờ Nhân sự điều chỉnh tay.
- **Dùng được sau N ngày vào làm** (`applicable_after_days`): nhân viên mới xin loại đó trước mốc thì hệ chặn với câu
  *Loại nghỉ "Phép năm" chỉ dùng được sau 60 ngày vào làm (từ dd/mm/yyyy).* — chọn ngày từ mốc đó hoặc loại khác.

## Ngày cấm nghỉ (từ 02/11/2026)

Nhân sự khai ở *Thiết lập ▸ Ngày cấm nghỉ* (khoảng ngày + lý do, áp cho cả công ty, một pháp nhân hoặc một phòng).

- **Lập, sửa, gửi duyệt KHÔNG bị chặn** — chỉ hiện khung vàng *Đơn nghỉ này rơi vào ngày cấm nghỉ.*
- **Lượt duyệt CUỐI bị chặn** (kể cả duyệt thẳng), trừ người có vai trò được miễn (*Cài đặt nhân sự ▸ Nghỉ phép*) hoặc
  quản trị. Đơn vẫn *Chờ duyệt*, phép vẫn giữ chỗ — người duyệt **Trả về** để đổi ngày hoặc nhờ người được miễn duyệt.
- Soạn đơn bằng trợ lý mà đụng ngày cấm thì `draft_leave_request` trả cảnh báo + `block_conflicts` — **nói trước cho
  người dùng** rằng đơn sẽ kẹt ở lượt duyệt cuối, khuyên đổi ngày.

## Phiếu xin nghỉ bù (từ 02/11/2026)

Menu *Nhân sự ▸ Nghỉ phép ▸ Nghỉ bù*, khóa quyền riêng `leave_comp_request`.

- Chỉ xin cho ngày **đã đi làm** (không ở tương lai, từ 01/01 năm ngoái) mà ngày đó là **ngày lễ** hoặc **ngày nghỉ
  theo lịch làm việc** của chính người đó; mỗi ngày **một phiếu**; **0,5 hoặc 1 ngày**; gửi duyệt phải có lý do.
- Duyệt xong số ngày **cộng vào quỹ loại nghỉ nhận ngày bù** (Nhân sự bật ô *Loại nhận ngày nghỉ bù*) của năm đi làm,
  hoặc năm nay nếu ngày đi làm thuộc năm ngoái. Từ đó nghỉ bằng **đơn nghỉ phép** loại đó như mọi loại khác.
- ⚠️ **Không ai tự duyệt được phiếu nghỉ bù của chính mình**, bất kể công tắc nào. Trợ lý không bao giờ đề xuất duyệt
  phiếu của chính người hỏi.
- Hủy phiếu đã duyệt chỉ được khi ngày bù **chưa bị dùng** để nghỉ.
- **Soạn bằng trợ lý:** `draft_leave_comp_request` (cần `work_date` + lý do; `days` 0.5 / 1; Nhân sự / trưởng phòng lập
  hộ thì truyền `employee` = mã nhân sự). Tool chạy trước đủ các chốt trên; có `error` thì **đọc nguyên câu**, đừng tự
  soạn tiếp. Người dùng đồng ý thì xác nhận nháp với kind **`leave_comp`** (submit=true để gửi duyệt luôn). **Đừng lẫn**
  với `draft_leave_request`: xin nghỉ bù = xin THÊM ngày; nghỉ bằng ngày bù đã có = đơn nghỉ.

## Cài đặt nhân sự — hai công tắc nghỉ phép (từ 02/11/2026)

*Nhân sự ▸ Master ▸ Cài đặt nhân sự*, tab **Nghỉ phép**; cả hai mặc định **TẮT**.

- **Chặn đơn nghỉ lùi ngày**: bật thì không lập / sửa / gửi duyệt được đơn có ngày nghỉ **trước hôm nay** — hệ báo
  *Không lập được đơn nghỉ cho ngày đã qua (dd/mm/yyyy)…*. Hôm nay vẫn lập được. Vai trò được miễn (khai ở cùng tab) và
  quản trị lập hộ được; đơn họ lập hộ thì người nghỉ vẫn gửi duyệt được. Người dùng quên nộp đơn thì bảo nhờ Nhân sự lập hộ.
- **Chặn tự duyệt đơn nghỉ**: bật thì người nghỉ không bao giờ là người duyệt đơn của chính mình, kể cả ở bước khai
  đích danh — bước chỉ còn chính họ thì chuyển người dự phòng. (Phiếu nghỉ bù thì luôn chặn, không cần công tắc.)

## Phép không dùng hết thì đi đâu (kết sổ cuối năm)

**Tùy từng loại nghỉ**, phòng Nhân sự khai ở *Thiết lập ▸ Loại nghỉ*. Ba nước:
***Hết năm là mất*** (mặc định) · ***Mang sang năm sau*** · ***Quy đổi sang loại
nghỉ khác*** (đổi theo tỷ lệ, ví dụ 2 ngày phép đổi 1 ngày nghỉ bù).

- ⚠️ **Không có gì tự chạy đêm 31/12.** Phải có người của Nhân sự bấm nút ***Kết
  sổ năm …*** ở màn *Quỹ phép năm*. Người dùng hỏi *"sang năm rồi sao chưa thấy
  phép cũ"* thì đó là chưa ai bấm — bảo họ hỏi phòng Nhân sự, đừng nói hệ lỗi.
- **Phép mang sang có HẠN DÙNG**, thông lệ là **hết 31/3** năm sau (mỗi loại khai
  một hạn riêng, có thể để không hết hạn). Quá hạn là mất phần chưa dùng.
- **Phép mang sang được tiêu TRƯỚC phép của năm mới** — cố ý, vì nó sắp hết hạn.
- Đừng tự tính giúp họ mang được mấy ngày: con số đó nằm trên màn *Quỹ phép năm*.
- **Bảng *Đối chiếu kết sổ năm …*** (từ 22/10/2026): kết sổ xong, hộp ***Đối chiếu kết sổ phép
  năm …*** **tự mở** ra, liệt kê từng người, từng loại nghỉ với các cột **Số cũ (trước)** ·
  **Số mới (sau)** · **Chênh** (= số mới trừ số cũ, thường âm: đúng phần đã chuyển đi) · **Sang loại** (ghi ***Chưa khai*** nếu loại quy đổi chưa khai loại nhận) ·
  **Cộng vào năm sau** (= phần chuyển đi × tỷ lệ quy đổi). Đóng rồi muốn xem lại thì
  bấm nút ***Đối chiếu kết sổ …*** cạnh nút Kết sổ ở màn *Quỹ phép năm*; hộp có nút ***Xuất Excel***
  (chỉ người có quyền xuất Quỹ phép năm mới thấy). Đây là bảng **chỉ xem**, không sửa số ở đó.
  ⚠️ **Số cũ được tính lại lúc mở bảng** (số còn lại + số đã chuyển đi), không phải ảnh chụp
  lúc bấm nút — nên đơn của năm cũ được duyệt hoặc hủy **sau** kết sổ sẽ làm số đổi theo. Khi người
  dùng hỏi "sao số đối chiếu khác hôm kết sổ" thì giải thích đúng điểm này; đừng đoán con số.

## Một đơn khai được NHIỀU loại nghỉ

*"Nghỉ 4 ngày: 3 ngày phép năm + 1 ngày không lương"* — làm **trong một tờ đơn**,
không phải hai. Trên form, phần *Loại nghỉ* là một bảng: bấm ***Thêm loại nghỉ***
để có dòng thứ hai, mỗi dòng chọn loại và ghi số ngày.

- **Cả đơn dùng chung các khoảng ngày** (một hoặc nhiều, xem mục dưới). Dòng chỉ chia số ngày, không khai ngày riêng và không gắn với khoảng nào.
- **Quỹ phép trừ theo từng loại** — 3 ngày vào quỹ phép năm, 1 ngày vào quỹ không
  lương. Số phép còn lại hiện ngay dưới từng dòng.
- **Một loại chỉ khai một dòng.** Muốn 3 ngày phép năm thì ghi 3 vào một dòng,
  đừng tách thành hai dòng 2+1.
- **Người dùng hỏi "hết phép năm rồi thì làm sao"**: thêm một dòng *Nghỉ không
  lương* cho phần vượt, thay vì lập đơn thứ hai — đơn thứ hai sẽ bị chặn vì
  **chồng ngày** với đơn đầu.
- **Nghỉ theo giờ thì chỉ một loại.**

## Một đơn khai được NHIỀU KHOẢNG NGÀY không liền kề

*"Nghỉ 27/10, rồi nghỉ tiếp chiều 03/11 tới hết 07/11"* — **một tờ đơn**, không phải hai.
Trên form, người dùng bấm ***+ Thêm khoảng ngày***; mỗi khoảng có khung **Khoảng ngày N · X ngày**,
dòng cuối ghi **Cộng N khoảng: Y ngày**. Đơn cũ là đơn đúng một khoảng.

- **Ví dụ chuẩn:** 27/10/2026 cả ngày + 03/11 chiều → 07/11 cả ngày, lịch T2–T7 → hai khoảng
  **1 ngày và 4,5 ngày, tổng 5,5 ngày**. Các ngày 28/10–02/11 là **ngày đi làm** — không trừ phép,
  không hiện nghỉ ở Lịch nghỉ hay **Ai làm / ai nghỉ**.
- **`from_date`/`to_date` ở đầu đơn chỉ là BAO NGOÀI** (ngày đầu khoảng đầu → ngày cuối khoảng cuối),
  nuốt cả khe giữa. **Đừng đọc "nghỉ từ 27/10 đến 07/11" thành nghỉ liên tục.** Muốn biết đơn nghỉ những
  ngày nào thì đọc **`periods`** (mỗi phần tử: `from_date`, `to_date`, `from_session`, `to_session`, `days`).
  Tool `my_leave_summary` cũng trả `periods` cho từng đơn.
- **Luật:** tối đa **20 khoảng**; các khoảng **không chồng ngày** nhau (sát nhau thì được);
  **từ hai khoảng trở lên phải cùng một năm** (vắt năm → hệ trả 422 **Tách thành hai đơn**, một đơn cho năm
  trước, một đơn cho năm sau); **nghỉ theo giờ chỉ một khoảng**. Chốt trùng ngày với đơn khác xét
  **từng khoảng** — đơn khác nằm trong khe thì không trùng.
- **Số ngày chỉ sửa đè ở TỔNG**, không sửa đè từng khoảng. Quỹ vẫn trừ theo **từng dòng loại nghỉ**.
- **Báo cáo theo tháng neo ngày bắt đầu của đơn** (đơn 31/10 + 03/11 tính vào tháng 10) — đã chốt, không phải lỗi.
- **Luồng duyệt coi mọi đơn là nghỉ phép, không rẽ nhánh theo loại nghỉ của từng dòng** (việc **đọc đủ
  mọi loại nghỉ** HR3-3 đã chốt **bỏ** 26/10/2026). Đừng hứa với người dùng rằng đơn có dòng **không
  lương** sẽ tự thêm chặng duyệt riêng.

**Soạn và sửa bằng Trợ lý:** khi người dùng nói nhiều đợt (**nghỉ 27/10 và chiều 3/11 tới 7/11**) thì
gọi `draft_leave_request` với **`periods`**, mỗi đợt một phần tử — **đừng gộp thành một
`from_date`/`to_date` liền**, gộp là tính nghỉ cả những ngày đi làm ở giữa. Đợt một ngày thì
`to_date` = `from_date`; nửa ngày dùng `from_session`/`to_session`. Đơn một khoảng thì vẫn dùng
`from_date`/`to_date` như cũ (có `periods` thì bỏ hai ô này). Kết quả trả `periods` kèm `days` từng
khoảng và `periods_text`; **`warnings` vẫn phải đọc nguyên** (vắt năm, chồng ngày, theo giờ nhiều khoảng
đều bị chặn). Sửa đơn có từ hai khoảng bằng `propose_document_update`: **ngày phải gửi qua `periods`** (đủ danh
sách), gửi `from_date`/`to_date` đơn lẻ sẽ bị từ chối; chỉ sửa lý do thì không đụng các khoảng.
Hoàn tác giữ nguyên các khoảng cũ.

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
- **Loại nghỉ bắt buộc đính kèm giấy tờ** (phòng Nhân sự bật cờ ***Bắt buộc đính kèm*** ở *Thiết lập ▸
  Loại nghỉ*; Nghỉ ốm, Nghỉ vợ sinh con thường bật): đơn phải có **ít nhất một tệp** trước khi
  **Gửi duyệt**. **Lưu nháp thì không bị chặn.** Thứ tự đúng: **Lưu nháp** → tải tệp lên ở mục
  ***Tệp đính kèm*** (mục này chỉ có sau khi đơn đã được lưu) → bấm **Gửi duyệt**. Chưa có tệp mà gửi
  thì hệ chặn bằng câu: ***Loại nghỉ *Nghỉ ốm* bắt buộc đính kèm giấy tờ (giấy khám bệnh, giấy chứng
  nhận…) — tải tệp lên ở mục *Tệp đính kèm* rồi gửi duyệt lại.*** Mục **Tệp đính kèm** hiện dấu bắt buộc
  và dòng báo đỏ ngay khi chọn loại nghỉ đó. Đơn nhiều loại nghỉ: chỉ cần **một** loại bật cờ là cả
  đơn phải có tệp. Trợ lý **không** đính kèm hộ được — bảo người dùng tự tải tệp lên.
- **Cưới hỏi và tang chế tối đa 3 ngày mỗi lần.**
- **Thai sản chỉ hiện với hồ sơ nữ.** Hồ sơ **chưa khai giới tính** thì **không bị
  chặn** — cứ nộp được.
- ***Nghỉ vợ sinh con* chỉ hiện với hồ sơ nam**, cần đính kèm giấy chứng sinh. Hệ
  chỉ chặn ở **trần 14 ngày** — đó là mức cao nhất của luật (sinh đôi trở lên, mổ);
  mức thường là 5 ngày, sinh mổ 7 ngày. **Đừng khẳng định họ được bao nhiêu ngày** —
  máy không biết ca nào, người duyệt quyết.
- **Hai đơn không được chồng ngày** của cùng một người. Chồng thì cùng một ngày bị
  trừ phép hai lần.
- **Nghỉ từ buổi chiều đến buổi sáng cùng ngày** là khoảng trống — hệ chặn (áp cho từng khoảng).
- Lập đơn **hộ người khác** được (hành chính, trợ lý). Cả người lập lẫn người nghỉ
  đều thấy tờ đơn đó.

## Tool `my_leave_summary` — khi nào gọi, đọc kết quả thế nào

Gọi khi người hỏi nói tới phép **của chính họ**: **tôi còn mấy ngày phép**, **phép năm
còn bao nhiêu**, **đơn nghỉ tuần sau của tôi duyệt chưa**, **năm ngoái tôi nghỉ mấy
ngày** (truyền `year`). **Gọi nó TRƯỚC khi soạn đơn** bằng `draft_leave_request` —
soạn xong mới biết không đủ phép là bắt người ta làm lại.

Đọc kết quả:

- `balances` là **một dòng cho MỖI loại nghỉ**, không phải một con số chung. Trả lời
  **còn 7 ngày** mà không nói loại nào là câu trả lời sai.
- `remaining_days` **đã trừ** `pending_days` (đơn đang chờ duyệt) và phần chưa tới tháng
  (`not_yet_accrued_days`, loại cộng dần). Người hỏi thấy hụt ngày mà chưa nghỉ hôm nào thì
  nói rõ lý do nào. Số **âm** = đang ứng phép (chỉ có khi `max_negative_days` > 0).
- `comp_days` là ngày **nghỉ bù đã duyệt** cộng vào loại đó (đã nằm trong `total_days`);
  `comp_requests` là các phiếu xin nghỉ bù của họ kèm trạng thái.
- Hỏi "được ứng phép không / mới vào làm nghỉ phép năm được chưa" thì đọc `max_negative_days`
  và `applicable_after_days` của đúng loại — đừng đoán.
- `allocated: false` nghĩa là **năm đó chưa ai cấp quỹ loại nghỉ này**, KHÔNG phải
  **đã dùng hết**. Bảo họ hỏi phòng Nhân sự, đừng nói họ hết phép.
- Đơn khai **nhiều loại nghỉ** thì đọc theo `lines`; `total_days` đầu đơn là tổng
  chung, gán cả tổng đó cho một loại là nói sai.
- Đơn **nhiều khoảng ngày** thì đọc ngày nghỉ theo `periods`, không theo `from_date`/`to_date` đầu đơn (bao ngoài, có khe).

Hai điều tool này **không** làm: không nộp đơn (đó là `draft_leave_request`, đừng
lẫn hai cái), và không xem được phép của người khác.

## Tool `draft_leave_request` — soạn nháp đơn nghỉ phép

Gọi khi người hỏi muốn **xin nghỉ**: **tôi muốn nghỉ 3 ngày tuần sau**, **làm giúp tôi
đơn nghỉ phép ngày mai**, **xin nghỉ nửa buổi sáng thứ Sáu**.

⚠️ **Đây là đơn ở phân hệ Nhân sự, KHÔNG phải văn bản *Giấy nghỉ phép* ở Văn thư.**
Giấy GNP hệ tự sinh sau khi đơn được duyệt — đừng bao giờ dẫn người dùng sang màn
tạo văn bản để **làm giấy nghỉ phép**.

Cần tối thiểu **ngày nghỉ từ–đến** (hoặc `periods` khi nghỉ nhiều đợt) và **lý do**. Ngày nói tương đối (**mai**, **thứ Hai
tuần sau**) thì tự quy ra `YYYY-MM-DD` theo hôm nay. Nghỉ **nửa ngày** thì hỏi buổi
nào (`from_session`/`to_session` = `morning`/`afternoon`); nghỉ **vài tiếng** thì hỏi
khung giờ (`hourly` + `from_time`/`to_time` dạng `HH:MM`).

Đọc kết quả:

- **`warnings` phải đọc nguyên cho người dùng, đừng nuốt.** Backend sẽ **chặn lúc lưu / gửi**:
  trùng đơn cũ · vượt trần một đơn của loại nghỉ · không đủ quỹ (kể cả phần được ứng) · đơn lùi
  ngày khi công tắc bật · chưa đủ ngày vào làm của loại đó. Hai cảnh báo **không chặn lưu**: đang
  **ứng phép** trong mức cho phép (nói rõ còn lại sẽ thành số âm), và **ngày cấm nghỉ** (kẹt ở lượt
  duyệt cuối, xem `block_conflicts`). Nói trước thì họ sửa ngay; im thì họ điền xong form mới ăn câu chặn.
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

## Năm khóa quyền — đừng gộp

| Khóa | Mở màn nào |
|---|---|
| `leave_request` | Đơn nghỉ phép · Lịch nghỉ |
| `leave_comp_request` | Nghỉ bù (phiếu xin nghỉ bù) |
| `leave_balance` | Quỹ phép năm (cấp phát, **điều chỉnh tay**) |
| `leave_type` | Thiết lập ▸ Loại nghỉ (kèm bậc thâm niên, hạn mức theo nhóm) |
| `holiday` | Thiết lập ▸ Lịch ngày lễ |

Tách như vậy vì **`leave_balance` ghi được nghĩa là tặng thêm ngày phép cho bất kỳ ai**.
Đó là việc của phòng Nhân sự (vai trò mẫu **`hr_leave`**), không phải của người nộp đơn.

⚠️ Bốn khóa đầu **mới thêm 03/09/2026**, `leave_comp_request` thêm **02/11/2026**. Trên hệ đang chạy,
các vai trò cũ **không tự có** chúng — quản trị phải tick thêm ở *Nhân sự ▸ Phân quyền tài khoản*.
Người dùng báo "không thấy menu Nghỉ phép / Nghỉ bù" thì gần như chắc là do chỗ này.

Luồng duyệt đơn có thể khai bước ***Người có quyền duyệt (theo phân quyền)*** (duoc-CR-680): người
nhận việc là ai giữ vai trò được tick **Duyệt** trên `leave_request` với phạm vi Phòng ban, Công ty
hoặc Tất cả, không tính vai trò Quản trị hệ thống, và phạm vi đó phủ được tờ đơn (phạm vi **Phòng ban** chỉ
nhận đơn của phòng mình). Người dùng hỏi **sao đơn của tôi không tới ai duyệt** mà luồng khai cách này:
gợi ý quản trị kiểm ở *Nhân sự ▸ Phân quyền tài khoản* xem có vai trò nào tick Duyệt nghỉ phép với
phạm vi phủ phòng / công ty của người nộp — đừng đoán tên người duyệt.

## Bảng từ dùng đúng

| Nói thế này | Đừng nói |
|---|---|
| Đơn nghỉ phép | phiếu nghỉ, đơn xin phép |
| Quỹ phép năm | số dư phép, tài khoản phép |
| Gửi duyệt | trình ký, submit |
| Trả về chỉnh sửa | trả lại (dễ lẫn với Từ chối) |
| Điều chỉnh tay | cộng phép, bù phép (đó là việc Nhân sự sửa quỹ) |
| Phiếu xin nghỉ bù | đơn nghỉ bù, phiếu làm thêm |
| Lịch ngày lễ | ngày nghỉ lễ (đó là danh mục, tên đúng là **Lịch ngày lễ**) |
| Kết sổ cuối năm | chốt sổ, khóa sổ, chuyển phép tự động |
| Mang sang năm sau | bảo lưu phép, cộng dồn phép |
