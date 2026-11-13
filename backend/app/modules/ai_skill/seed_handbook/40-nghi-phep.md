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
  của **chính người đang hỏi**. Hỏi phép / ngày đã nghỉ của **người khác** thì gọi
  **`employee_leave_summary`** (chỉ người có quyền xem Quỹ phép mới dùng được, và chỉ thấy
  người trong phạm vi của họ); tool từ chối hoặc trả rỗng thì nói đúng như vậy, đừng tìm
  đường vòng (không dùng `employee_lookup` hay đơn nghỉ để suy ra phép của người khác).

## Bốn khái niệm, đừng lẫn

| Thứ | Là gì |
|---|---|
| **Đơn nghỉ phép** | Chứng từ nghiệp vụ. Nguồn sự thật, có số `NP-xxx`. |
| **Giấy nghỉ phép (GNP)** | **Văn bản** trong phân hệ Văn thư, tự sinh **sau khi đơn đã duyệt**. Là hồ sơ lưu sổ, không phải thứ để nộp. |
| **Loại nghỉ** | Danh mục cấu hình (Phép năm, Nghỉ ốm, Thai sản…). Sửa được luật mà không cần lập trình. Có sẵn năm loại chế độ BHXH riêng (BHXH chi trả, không trừ quỹ phép): Nghỉ khám thai, Nghỉ sảy thai/phá thai, Nghỉ thực hiện biện pháp tránh thai, Nghỉ chăm con ốm, Nghỉ dưỡng sức phục hồi sức khỏe — mức luật ghi ở ghi chú từng loại. |
| **Quỹ phép** | Số ngày của **một người × một năm × một loại nghỉ**. |
| **Phiếu thanh toán nghỉ phép** (`TTP…`) | Xin **đổi ngày phép chưa nghỉ ra tiền** (phép dư cuối năm hoặc khi nghỉ việc). Phiếu chỉ ghi **số ngày**; số tiền do kế toán nhập ở Yêu cầu thanh toán. |
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

## Quỹ phép — năm con số cộng, ba con số trừ

    còn lại = (hạn mức + thâm niên + chuyển năm trước + điều chỉnh tay + nghỉ bù cộng thêm) − đã nghỉ − đang chờ duyệt
              − đã thanh toán ra tiền
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

Nhân sự khai ở *Thiết lập*, tab *Loại nghỉ* (trang một loại có tab *Thông tin* / *Bậc thâm niên* / *Hạn mức theo nhóm*). Tool trả
`accrual_mode_label` cho từng loại:

| Cách cấp | Nghĩa |
|---|---|
| **Đủ hạn mức đầu năm** (mặc định) | Đầu năm có đủ số ngày. |
| **Theo tỷ lệ tháng làm việc** | Người vào làm giữa năm được hạn mức × số tháng làm / 12 (vào làm ngày 1–15 tính cả tháng đó). |
| **Cộng dần theo tháng** | Quỹ ghi đủ cả năm nhưng **phần chưa tới tháng chưa dùng được**: 12 ngày, đang tháng 5 → dùng được 5 (làm tròn xuống nửa ngày). Tool trả phần này ở `not_yet_accrued_days`. Thâm niên, phép chuyển sang, điều chỉnh tay, nghỉ bù không bị cộng dần. |

- **Hạn mức theo nhóm**: một loại nghỉ có thể khai hạn mức riêng theo **hình thức nhân viên** (chính thức, thử việc…)
  hoặc **cấp bậc**; ưu tiên **chính sách nghỉ phép được phân bổ cho người đó** (mục dưới) → hình thức → cấp bậc → hạn mức chung. Quỹ đã cấp **không tự tính lại** khi Nhân sự đổi luật —
  người dùng hỏi "sao đổi rồi mà quỹ tôi không đổi" thì bảo họ nhờ Nhân sự điều chỉnh tay.
- **Dùng được sau N ngày vào làm** (`applicable_after_days`): nhân viên mới xin loại đó trước mốc thì hệ chặn với câu
  *Loại nghỉ "Phép năm" chỉ dùng được sau 60 ngày vào làm (từ dd/mm/yyyy).* — chọn ngày từ mốc đó hoặc loại khác.

## Chính sách nghỉ phép và phân bổ (từ 03/11/2026)

**Chính sách nghỉ phép** = gói *loại nghỉ → số ngày/năm* (ví dụ *Chính sách cấp quản lý*: Phép năm 15). Nhân sự khai ở
menu ***Nhân sự ▸ Thiết lập***, hai tab đứng cạnh nhau trong dải tab Thiết lập (từ 12/11/2026): tab ***Gói chính sách*** khai gói (chi tiết gói có
*Thông tin* · *Loại nghỉ & số ngày* · *Đang phân bổ*), tab ***Phân bổ chính sách*** gán cho người (nút ***Phân bổ*** cho một người, ***Phân bổ hàng loạt*** tối đa 500
người; dòng phân bổ có ***Kết thúc*** / ***Xóa***).

- **Thứ tự hạn mức**: phân bổ chính sách của người > hình thức nhân viên > cấp bậc > hạn mức của loại. Loại **không có
  trong gói** thì vẫn theo luật của loại — đừng nói là 0 ngày.
- **Đổi chính sách giữa năm chia theo tháng, mốc ngày 15**: luật loại 12, gói 15 từ 01/07 → hạn mức **13,5**. Phân bổ bắt
  đầu từ (hoặc trước, hoặc trong tháng) ngày vào làm thì áp **cả năm** theo số của gói (vào làm 01/10, gói 15 → 15).
- Ô ***Tính lại hạn mức năm nay cho quỹ đã cấp*** (mặc định bật) chỉ sửa cột *Hạn mức* của quỹ **năm nay**; tắt thì
  áp từ lần cấp quỹ sau. Năm đã qua không bao giờ đổi. Sửa số ngày trong gói **không** tự tính lại quỹ đã cấp.
- **Hai màn nối nhau** (từ 11/11/2026): tab *Phân bổ chính sách* có cột ***Hạn mức năm nay*** (*Phép năm 15
  ngày*, bấm sang đúng dòng quỹ; *chưa cấp quỹ* khi chưa có dòng); *Quỹ phép năm* có cột ***Chính sách*** ở cả hai thẻ
  (*Theo loại nghỉ* khi không gói nào khai loại đó). Người hỏi "quỹ tôi lấy theo chính sách nào" thì chỉ cột này.
  Hai màn không ghi đè nhau: phân bổ chỉ đổi cột *Hạn mức*, điều chỉnh tay ở Quỹ phép năm nằm ở cột *Điều chỉnh tay*.
- **Không ai (trừ quản trị) tự tạo / sửa / xóa phân bổ của chính mình** — người hỏi muốn tự gán thì bảo nhờ người khác
  trong phòng Nhân sự. Người được phân bổ phải trong **phạm vi ghi quỹ phép** của người làm; người đã nghỉ việc không
  phân bổ được. Một người tại một ngày chỉ có **một** chính sách — chồng ngày thì tick ***Kết thúc chính sách đang hiệu
  lực***.
- Không có khóa quyền mới: chính sách theo `leave_type`, phân bổ theo `leave_balance`.
- Người dùng hỏi **sao hạn mức phép năm của tôi khác đồng nghiệp**: gọi `my_leave_summary`, đọc `policy` và
  `policy_annual_days` của đúng loại (xem mục tool). Chi tiết dòng quỹ trên màn có dòng ***Chính sách đang áp***.
- Kỳ nghỉ phép (Leave Period) **không có** — quỹ theo năm dương lịch; đừng hướng dẫn tạo kỳ phép.

## Xem quỹ của cả phòng và cấp quỹ có lọc (Nhân sự, từ 03/11/2026)

- Màn *Quỹ phép năm* có hai thẻ ***Theo dòng quỹ*** · ***Theo nhân sự*** (mỗi người một dòng, mỗi loại nghỉ một cột, ô là
  số dùng được hôm nay, ***Tổng còn lại***, ***Xuất Excel***). Ô **—** = chưa có dòng quỹ loại đó, khác **0** = đã dùng hết.
- Nút ***Cấp quỹ năm …*** mở hộp lọc: loại nghỉ (nhiều), pháp nhân, phòng ban, hình thức nhân viên, cấp bậc — ô trống là
  không lọc. Vẫn chỉ tạo dòng còn thiếu. Hai người bấm cùng lúc thì hệ tự chạy lại; vẫn vướng thì báo *Một lượt cấp quỹ
  khác đang chạy cùng lúc* — bảo người dùng tải lại trang, còn thiếu thì bấm lại (không mất, không nhân đôi ngày).
- **Bảng Quỹ phép năm chỉ có dòng cho loại bật *Trừ vào quỹ phép*** (thường chỉ Phép năm, có nơi thêm Nghỉ bù). Ốm đau,
  cưới hỏi, tang chế, thai sản… không trừ quỹ nên không có dòng — người hỏi "sao tôi chỉ thấy Phép năm" thì giải thích
  vậy, đừng nói là thiếu quỹ. Người có nhiều loại thì hàng người có mũi tên bung ra từng loại.

## Ba thao tác hay nhầm: Cấp quỹ · Phân bổ chính sách · Điều chỉnh tay

| | ***Cấp quỹ*** (Quỹ phép năm) | ***Phân bổ*** (Thiết lập › tab Phân bổ chính sách) | ***Điều chỉnh tay*** (chi tiết dòng quỹ) |
|---|---|---|---|
| Làm gì | Mở dòng quỹ CÒN THIẾU cho năm (đầu năm, người mới) | Gán gói luật cho người theo khoảng ngày | Cộng / trừ ngày cho một dòng quỹ |
| Đụng dòng đã có | **Không** | Chỉ ô *Hạn mức* năm nay (khi tick tính lại) | Chỉ ô *Điều chỉnh tay* (ghi đè, có nhật ký) |
| Khi nào dùng | Đầu năm, có người mới | Người đổi chế độ (lên chức, đủ thâm niên, thử việc) | Trường hợp lẻ một người, một lần |

Một câu: *Chính sách* = luật · *Phân bổ* = ai áp luật nào từ lúc nào · *Quỹ phép năm* = sổ ngày phép thực tế. Không bấm
Cấp quỹ thì người dùng vẫn nộp đơn được — mở form chọn loại nghỉ là hệ tự mở dòng quỹ còn thiếu cho riêng người đó.

## Báo cáo "Làm việc vào ngày lễ, ngày nghỉ" (khóa báo cáo 30, từ 03/11/2026)

*Báo cáo ▸ Nhân sự ▸ Làm việc vào ngày lễ, ngày nghỉ*: ai đi làm ngày lễ / ngày nghỉ theo lịch, bao nhiêu lượt, bao nhiêu
ngày nghỉ bù được duyệt. Tool `report_summary` với `report_key = holiday_work` (thêm `include_pending`, `day_kind` 0 tất cả · 1
ngày lễ · 2 ngày nghỉ theo lịch, `department_id`).

- ⚠️ **Nguồn là phiếu xin nghỉ bù, KHÔNG phải chấm công** (công ty không chấm công): ai đi làm mà không lập phiếu thì không
  có trong báo cáo. Mặc định chỉ phiếu **Đã duyệt**; ô ***Gồm phiếu chờ duyệt*** thêm phiếu đang chờ. Dữ liệu từ 02/11/2026.
- Phòng ban là **phòng ghi trên phiếu**. Kỳ tối đa 366 ngày.
- Không thấy báo cáo: cần được giao ở *Phân quyền tài khoản ▸ tab Báo cáo* **và** có quyền xem *Phiếu nghỉ bù*; vừa được
  giao thì phải **đăng xuất rồi đăng nhập lại**. Báo cáo Quỹ phép năm có thêm cột ***Nghỉ bù cộng thêm***.

## Ngày cấm nghỉ (từ 02/11/2026)

Nhân sự khai ở *Thiết lập*, tab *Ngày cấm nghỉ* (khoảng ngày + lý do, áp cho cả công ty, một pháp nhân hoặc một phòng).

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

## Thanh toán nghỉ phép (từ 03/11/2026)

Menu *Nhân sự ▸ Nghỉ phép ▸ Thanh toán nghỉ phép*, khóa quyền riêng `leave_encashment`. Đổi ngày phép **chưa nghỉ** ra tiền
khi **cuối năm còn dư** hoặc khi **nghỉ việc** (Điều 113 khoản 3 Bộ luật Lao động: thôi việc mà chưa nghỉ hết phép thì
được thanh toán số ngày chưa nghỉ).

- ⚠️ **TUYỆT ĐỐI KHÔNG nói số tiền**, không ước tính, không nhân lương ngày, kể cả khi người hỏi là chính người được
  thanh toán. Số tiền chia số ngày ra lương ngày; tool không trả tiền và trợ lý cũng không đi tìm (không đọc YCTT để lấy
  tiền). Hỏi **được bao nhiêu tiền** thì nói: số tiền do kế toán nhập ở Yêu cầu thanh toán; chính người được thanh toán xem
  ở khối **Thanh toán** trên trang chi tiết phiếu.
- Chỉ loại nghỉ Nhân sự bật **Cho phép thanh toán nghỉ phép** mới thanh toán được (tool: `allow_encashment` của dòng
  loại). `false` thì nói thẳng loại đó không đổi ra tiền, đừng hứa.
- **Hỏi "tôi được thanh toán mấy ngày phép"**: gọi `my_leave_summary`, lấy `remaining_days` của đúng loại, rồi giải thích
  theo luật của loại — **đừng chốt con số** như số cuối cùng, vì hệ còn trừ phần mang sang chưa dùng (tool không tách riêng
  phần này) và làm tròn xuống nửa ngày. Con số chốt nằm ở hộp **Số ngày được thanh toán** khi lập phiếu.
  - **Phép dư cuối năm**: còn lại − phần mang sang từ năm trước chưa dùng − `non_encashable_days` (số ngày phải giữ lại);
    rồi không vượt `max_encashable_days` trừ `encashed_days` đã thanh toán trong năm (`max_encashable_days = 0` là không
    trần); làm tròn xuống 0,5; âm thì 0.
  - **Nghỉ việc**: hết số còn lại, kể cả phần mang sang, không giữ lại, không trần; hồ sơ phải có ngày nghỉ việc (thiếu
    thì nhờ Nhân sự nhập trước).
  - Nói dạng **khoảng tối đa N ngày, con số chính xác xem ở hộp Số ngày được thanh toán khi lập phiếu**.
- Năm quỹ chỉ chọn **năm nay hoặc năm trước**; mỗi người, mỗi loại nghỉ, mỗi năm chỉ **một phiếu còn hiệu lực cho mỗi
  lý do** (một phiếu cuối năm, một phiếu nghỉ việc; kể cả phiếu đã duyệt). Năm trước đã kết sổ thì không còn ngày để thanh toán.
- Vòng đời: nhân viên lập (hoặc Nhân sự lập hộ) → gửi duyệt (giữ chỗ ngày) → **phòng Nhân sự duyệt** (không ai tự duyệt
  phiếu của mình) → ngày bị trừ khỏi quỹ, hệ tạo YCTT cho kế toán → kế toán nhập tiền, duyệt, **Ghi nhận đã chi**. Trạng
  thái chi đọc ở `payment_status_label` của từng phiếu trong `encashments`.
- `payment_status = cancelled` mà phiếu vẫn **Đã duyệt** = **kế toán từ chối chi**: ngày vẫn đang bị trừ; bảo họ liên hệ
  phòng Nhân sự để hủy phiếu (trả ngày về quỹ) rồi lập lại nếu cần. Phiếu đã chi thì không hủy được nữa.
- Trợ lý **không soạn nháp** phiếu này (chưa có tool). Người muốn lập thì dẫn vào màn *Thanh toán nghỉ phép*, nút
  **Lập phiếu thanh toán**. Đừng dùng `draft_leave_request` hay `draft_payment_request` thay thế.
- Kế toán hỏi **không thấy YCTT nghỉ phép**: vai trò của họ cần quyền **đọc** *Nghỉ phép › Thanh toán nghỉ phép* phạm vi
  công ty (ngoài quyền Yêu cầu thanh toán) — gợi ý quản trị tick ở *Quản trị ▸ Phân quyền tài khoản*.

## Cài đặt nhân sự — hai công tắc nghỉ phép (từ 02/11/2026)

*Nhân sự ▸ Thiết lập*, tab *Cài đặt nhân sự*, tab **Nghỉ phép** trong màn; cả hai mặc định **TẮT**.

- **Chặn đơn nghỉ lùi ngày**: bật thì không lập / sửa / gửi duyệt được đơn có ngày nghỉ **trước hôm nay** — hệ báo
  *Không lập được đơn nghỉ cho ngày đã qua (dd/mm/yyyy)…*. Hôm nay vẫn lập được. Vai trò được miễn (khai ở cùng tab) và
  quản trị lập hộ được; đơn họ lập hộ thì người nghỉ vẫn gửi duyệt được. Người dùng quên nộp đơn thì bảo nhờ Nhân sự lập hộ.
- **Chặn tự duyệt đơn nghỉ**: bật thì người nghỉ không bao giờ là người duyệt đơn của chính mình, kể cả ở bước khai
  đích danh — bước chỉ còn chính họ thì chuyển người dự phòng. (Phiếu nghỉ bù thì luôn chặn, không cần công tắc.)

## Phép không dùng hết thì đi đâu (kết sổ cuối năm)

**Tùy từng loại nghỉ**, phòng Nhân sự khai ở *Thiết lập*, tab *Loại nghỉ*. Ba nước:
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

Hệ tự tính theo **lịch làm việc của chính người nghỉ** và **đã trừ ngày nghỉ của lịch đó +
ngày lễ** (theo danh mục *Lịch ngày lễ*). Lịch mặc định (chưa ai gán) là **T2–T7 làm cả ngày,
Chủ nhật nghỉ**.

⚠️ Theo lịch mặc định, **DEGO Holding làm cả ngày thứ Bảy** — T7 **vẫn tính là ngày phép**.
Người dùng hỏi *"sao nghỉ thứ Bảy vẫn bị trừ phép"*: gọi `my_leave_summary`, đọc
`work_schedule` — lịch của họ có thứ Bảy là ngày làm thì đó là đúng, không phải lỗi. Phòng
nào được gán lịch riêng (ví dụ thứ Bảy nghỉ, hoặc thứ Bảy chỉ làm buổi sáng) thì đếm theo
lịch đó: ngày **Nghỉ** của lịch không tính, ngày chỉ làm một buổi tính tối đa **0.5**.
Thấy lịch sai thì bảo người dùng báo phòng Nhân sự sửa lịch — đừng hứa sửa số ngày.

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
- **Loại nghỉ bắt buộc đính kèm giấy tờ** (phòng Nhân sự bật cờ ***Bắt buộc đính kèm*** ở *Thiết lập*, tab
  *Loại nghỉ*; Nghỉ ốm, Nghỉ vợ sinh con thường bật): đơn phải có **ít nhất một tệp** trước khi
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
- `encashed_days` là ngày **đã thanh toán ra tiền** (phiếu thanh toán nghỉ phép đã duyệt), **đã trừ** khỏi
  `remaining_days`; `encashments` là các phiếu thanh toán nghỉ phép của họ (số ngày, trạng thái, `payment_status_label`
  = trạng thái chi). Không có số tiền — xem mục **Thanh toán nghỉ phép** dưới.
- Hỏi "được ứng phép không / mới vào làm nghỉ phép năm được chưa" thì đọc `max_negative_days`
  và `applicable_after_days` của đúng loại — đừng đoán.
- `allocated: false` nghĩa là **năm đó chưa ai cấp quỹ loại nghỉ này**, KHÔNG phải
  **đã dùng hết**. Bảo họ hỏi phòng Nhân sự, đừng nói họ hết phép.
- Đơn khai **nhiều loại nghỉ** thì đọc theo `lines`; `total_days` đầu đơn là tổng
  chung, gán cả tổng đó cho một loại là nói sai.
- Đơn **nhiều khoảng ngày** thì đọc ngày nghỉ theo `periods`, không theo `from_date`/`to_date` đầu đơn (bao ngoài, có khe).
- `policy` là chính sách nghỉ phép **đang áp** cho người hỏi (`null` = không có, hạn mức theo luật của loại). Ở từng dòng
  `balances`: `policy_name` + `policy_annual_days` (`null` = gói không khai loại đó → theo luật của loại). Hạn mức thật
  vẫn là `allocated_days` (đổi gói giữa năm thì đã chia theo tháng) — **đừng lấy `policy_annual_days` thay cho nó**.

- `taken_by_type` là **số ngày nghỉ trong năm theo TỪNG loại**, gồm CẢ loại không trừ quỹ
  (nghỉ không lương, nghỉ ốm, cưới hỏi…). Mỗi loại có ba con số:
  `approved_days` = đơn **đã duyệt** có ngày bắt đầu từ hôm nay trở về trước (**đã / đang nghỉ**),
  `approved_upcoming_days` = đơn đã duyệt cho ngày **sắp tới** (chưa nghỉ),
  `pending_days` = đơn **đang chờ duyệt**. Ba tổng tương ứng: `taken_total_days`,
  `upcoming_total_days`, `pending_total_days`.
- Hỏi **tôi đã nghỉ mấy ngày** thì trả `taken_total_days` rồi kể theo loại; phần đã duyệt sắp
  tới và phần chờ duyệt **nói riêng**, đừng cộng vào số đã nghỉ. Đừng lấy `used_days` của
  `balances` để trả lời câu này — nó chỉ có loại trừ quỹ (và tính cả đơn sắp tới).
- **Cả đơn tính vào năm của ngày bắt đầu nghỉ** (giống quỹ phép). Đơn vắt qua hai năm (ví dụ
  30/12 → 02/01) nằm trọn ở năm cũ; báo cáo *Tình hình nghỉ phép* chia theo ngày thật nên có thể
  lệch — người hỏi thấy hai con số khác nhau thì giải thích đúng lý do đó.
- `work_schedule` là **lịch làm việc đang áp hôm nay** của người hỏi: `schedule_name`,
  `level_label` (lịch lấy từ đâu: Nhân sự / Phòng ban / Pháp nhân / Toàn hệ thống),
  `target_name` (gán cho ai), `effective_from` / `effective_to`, `weekly_workdays` (số ngày
  công/tuần), `days` (bảy ngày: `weekday_label`, `day_kind_label`, giờ vào / ra, giờ nghỉ
  trưa). `is_fallback: true` = chưa ai gán lịch, đang theo lịch mặc định T2–T7 08:00–17:00.

Hai điều tool này **không** làm: không nộp đơn (đó là `draft_leave_request`, đừng
lẫn hai cái), và không xem được phép của người khác (đó là `employee_leave_summary`).

## Lịch làm việc — trả lời thế nào

- **"Lịch làm việc của tôi thế nào / thứ Bảy tôi có phải đi làm không / mấy giờ vào làm"**:
  gọi `my_leave_summary`, đọc `work_schedule`. Kể tên lịch, lịch đó đến từ đâu (gán riêng
  cho bạn / theo phòng ban / theo pháp nhân / toàn công ty / mặc định) và giờ từng thứ.
- **"Phòng tôi đang theo lịch nào / gán lịch cho phòng ở đâu"**: lịch của một phòng xem ở
  *Nhân sự ▸ Danh mục ▸ Phòng ban* ▸ bấm vào phòng ▸ tab ***Lịch làm việc***. Người có quyền
  gán lịch thấy nút ***Gán lịch cho phòng*** (mở sẵn hộp ***Thêm dòng gán lịch*** đã chọn đúng
  phòng); cách khác là *Nhân sự ▸ Thiết lập* ▸ tab ***Gán lịch***.
- **Thứ tự áp lịch**: lịch gán riêng cho **nhân sự** thắng lịch của **phòng ban**, rồi tới
  **pháp nhân**, rồi **toàn hệ thống**; chưa ai gán thì theo mặc định. Người kiêm nhiệm chỉ
  theo lịch của **phòng chính**.
- **Đổi lịch không đổi đơn cũ**: đơn đã gửi duyệt giữ số ngày lúc gửi; chỉ đơn **nháp** mở lại
  mới gợi ý theo lịch mới.
- **Trưởng phòng muốn đổi lịch cho một nhân viên**: hướng dẫn mở hồ sơ người đó ▸ tab ***Quỹ phép*** ▸ khung
  ***Lịch làm việc*** ▸ ***Đổi lịch riêng*** (cần quyền *Lịch làm việc riêng (Trưởng phòng gán)*). Trưởng phòng chỉ gán lịch
  riêng cho nhân viên phòng mình, không cho chính mình, chỉ chọn mẫu có sẵn, hiệu lực từ hôm nay trở đi; lịch đã bắt đầu
  chỉ đặt được ngày kết thúc; không sửa được lịch do Nhân sự gán (tạo dòng mới từ ngày cần đổi). Lịch của cả phòng / công
  ty và mẫu lịch là việc của phòng Nhân sự.
- Trợ lý **không gán / sửa lịch được** — chỉ hướng dẫn thao tác trên màn.

## Tool `employee_leave_summary` — phép của người khác (Nhân sự, quản lý)

Gọi khi người hỏi nói tới phép / ngày nghỉ / lịch làm việc của **người khác**: **anh Nam còn
mấy ngày phép**, **chị Hà năm nay nghỉ bao nhiêu ngày**, **phòng Kế toán ai còn nhiều phép**,
**NSU123 theo lịch làm việc nào**. Truyền `employee` (mã nhân viên hoặc một phần họ tên,
không cần dấu, bỏ chữ *anh / chị*) **hoặc** `department` (tên / ID phòng — liệt kê người
đang làm của phòng đó; gõ cả *phòng Kế toán* cũng được); `year` khi hỏi năm khác; `limit`
mặc định 20, trần 50.

Đọc kết quả:

- Mỗi người trong `employees` có `balances` (giống `my_leave_summary`: `remaining_days` là số
  còn nghỉ được, đừng tự cộng trừ), `taken_by_type` + `taken_total_days` + `upcoming_total_days`
  + `pending_total_days` (đọc y như mục `my_leave_summary` ở trên), `work_schedule` (chỉ tên lịch
  + cấp nguồn). `balances` rỗng = chưa cấp quỹ năm đó cho người này (hoặc dòng quỹ nằm ngoài
  phạm vi người hỏi), KHÔNG phải hết phép.
- **`taken_by_type` rỗng KHÔNG có nghĩa người đó chưa nghỉ ngày nào.** Số ngày đã nghỉ đọc từ
  đơn nghỉ, nên chỉ hiện khi người hỏi còn được xem đơn nghỉ của người đó (phạm vi xem *Đơn nghỉ
  phép*, có thể hẹp hơn phạm vi xem Quỹ phép). Rỗng mà quỹ vẫn có thì nói: *bạn không xem được
  đơn nghỉ của người này nên không có số ngày đã nghỉ*.
- **Khớp nhiều người cùng tên** thì liệt kê ngắn (mã, họ tên, phòng) và hỏi lại người nào,
  đừng gộp số của nhiều người.
- `employees` rỗng (`note` *Không tìm thấy nhân sự nào khớp trong phạm vi bạn được xem.*) =
  không có ai khớp **trong phạm vi người hỏi** — nói đúng như vậy, **đừng khẳng định người đó
  không tồn tại**.
- **Trưởng phòng hỏi phép của nhân viên** ("phòng tôi ai còn nhiều phép", "em Lan nghỉ mấy ngày rồi"): gọi tool với
  `department` là phòng của họ hoặc `employee` là tên người. Phạm vi Quỹ phép bậc **Phòng ban** chỉ gồm người có phòng
  chính thuộc phòng của Trưởng phòng (kể cả phòng họ kiêm nhiệm), trong công ty hiện tại — không còn là cả công ty. Người
  phòng khác chỉ kiêm nhiệm vào phòng họ thì không ra; đó là đúng phạm vi, đừng nói người đó không tồn tại.
- Tool báo thiếu quyền = người hỏi không có quyền xem Quỹ phép. Nói thẳng: muốn xem phép của
  người khác phải được phòng Nhân sự / quản trị cấp quyền xem *Quỹ phép năm*.
- `has_more: true` = còn người chưa trả; đọc `note`, gợi ý thu hẹp theo tên / phòng.
- Kèm link `url` (*Quỹ phép năm*) để người dùng mở xem bảng đủ.
- Tool **không có** lương, lý do nghỉ hay thông tin cá nhân — đừng hứa những thứ đó.

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

## Sáu khóa quyền — đừng gộp

| Khóa | Mở màn nào |
|---|---|
| `leave_request` | Đơn nghỉ phép · Lịch nghỉ |
| `leave_comp_request` | Nghỉ bù (phiếu xin nghỉ bù) |
| `leave_encashment` | Thanh toán nghỉ phép (kèm quyền thấy YCTT nghỉ phép bên Tài chính) |
| `leave_balance` | Quỹ phép năm (cấp phát, **điều chỉnh tay**) · tab *Phân bổ chính sách* của Thiết lập (cần quyền **sửa**) · quyền **xem** mở tool `employee_leave_summary` (tra phép người khác, theo đúng phạm vi xem Quỹ phép) |
| `leave_type` | Ba tab của Thiết lập: *Loại nghỉ* (kèm bậc thâm niên, hạn mức theo nhóm), *Ngày cấm nghỉ*, *Gói chính sách* (cần quyền **sửa**) |
| `holiday` | Tab *Lịch ngày lễ* của Thiết lập |

Tách như vậy vì **`leave_balance` ghi được nghĩa là tặng thêm ngày phép cho bất kỳ ai**.
Đó là việc của phòng Nhân sự (vai trò mẫu **`hr_leave`**), không phải của người nộp đơn.

⚠️ Bốn khóa đầu **mới thêm 03/09/2026**, `leave_comp_request` thêm **02/11/2026**, `leave_encashment` thêm **03/11/2026**. Trên hệ đang chạy,
các vai trò cũ **không tự có** chúng — quản trị phải tick thêm ở *Quản trị ▸ Phân quyền tài khoản*.
Người dùng báo "không thấy menu Nghỉ phép / Nghỉ bù" thì gần như chắc là do chỗ này.

Luồng duyệt đơn có thể khai bước ***Người có quyền duyệt (theo phân quyền)*** (duoc-CR-680): người
nhận việc là ai giữ vai trò được tick **Duyệt** trên `leave_request` với phạm vi Phòng ban, Công ty
hoặc Tất cả, không tính vai trò Quản trị hệ thống, và phạm vi đó phủ được tờ đơn (phạm vi **Phòng ban** chỉ
nhận đơn của phòng mình). Người dùng hỏi **sao đơn của tôi không tới ai duyệt** mà luồng khai cách này:
gợi ý quản trị kiểm ở *Quản trị ▸ Phân quyền tài khoản* xem có vai trò nào tick Duyệt nghỉ phép với
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
| Thanh toán nghỉ phép · phiếu thanh toán nghỉ phép | quy đổi phép, bán phép, trả lương phép |
| Lịch ngày lễ | ngày nghỉ lễ (đó là danh mục, tên đúng là **Lịch ngày lễ**) |
| Kết sổ cuối năm | chốt sổ, khóa sổ, chuyển phép tự động |
| Mang sang năm sau | bảo lưu phép, cộng dồn phép |
| Chính sách nghỉ phép (tab Gói chính sách · tab Phân bổ chính sách) | gói phép, chế độ phép, gán quỹ, phân bổ chính sách |
