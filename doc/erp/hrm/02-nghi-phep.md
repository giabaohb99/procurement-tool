# Nghỉ phép — phân hệ Nhân sự

| | |
|---|---|
| Bản | 2.2 — 11/11/2026 (**gộp Chính sách + Phân bổ thành một màn hai tab** — duoc-CR-750: bảng màn hình §2) · 2.1 — 11/11/2026 (**nối Phân bổ chính sách với Quỹ phép năm** — duoc-CR-745: §15.6a mới) · 2.0 — 03/11/2026 (**thanh toán nghỉ phép** (Leave Encashment) — duoc-CR-719: §16 mới; §3 · §5 · §9 · §10 · §11.1 sửa) · 1.9 — 03/11/2026 (**chính sách nghỉ phép + phân bổ chính sách, báo cáo "Làm việc vào ngày lễ, ngày nghỉ", quỹ theo nhân sự, cấp quỹ có lọc** — duoc-CR-717: §15 mới; §3 · §5 · §9 · §10 · §13.7 sửa; Kỳ nghỉ phép (Leave Period) **không làm**) · 1.8 — 03/11/2026 (**nghỉ phép kiểu ERPNext** — duoc-CR-715: cách cấp quỹ, hạn mức theo nhóm, dùng sau N ngày, ứng phép, ngày cấm nghỉ, phiếu nghỉ bù — §13 mới; **Cài đặt nhân sự tab Nghỉ phép** — duoc-CR-713, §14 mới; trang Loại nghỉ bố cục phẳng — duoc-CR-716, §11; §3 · §5 · §9 · §10 · §11.1 · §12 sửa) · 1.7 — 26/10/2026 (**một đơn khai nhiều khoảng ngày không liền kề** — duoc-CR-683: §7.3 mới, §6 + §7 + §12 sửa; **bỏ HR3-3** ở §7.1) · 1.6 — 23/10/2026 (sửa dòng cờ **Bắt buộc đính kèm** ở bảng Loại nghỉ cho khớp duoc-CR-661) · 1.5 — 22/10/2026 (cờ **Bắt buộc đính kèm** chặn lúc gửi duyệt — duoc-CR-661; bảng Đối chiếu kết sổ — duoc-CR-664) · 1.4 — 01/10/2026 (§10 đối chiếu lại với mã nguồn) · 1.3 — 08/09/2026 (ba tab của màn Đơn nghỉ phép — §8.1) |
| CR | **CR-259** · duoc-CR-302 · duoc-CR-303 · **duoc-CR-304** · duoc-CR-323 · duoc-CR-661 · duoc-CR-664 · **duoc-CR-683** · duoc-CR-713 · **duoc-CR-715** · duoc-CR-716 · **duoc-CR-717** · **duoc-CR-719** |
| Giao diện | **chỉ có trên `frontend-v2/`** (cổng 8083), menu *Nhân sự ▸ Nghỉ phép* |
| Kế hoạch gốc | `plans/260903-0956-quan-ly-nghi-phep/plan.md` · CR-715: `doc/erp/hrm/plans/261102-nghi-phep-kieu-erpnext-duoc-cr-715/plan.md` (+ `reports/review-fixes.md`) · CR-717: `doc/erp/hrm/plans/261103-nghi-phep-du-nhu-nexterp-duoc-cr-717/plan.md` · CR-719: `doc/erp/hrm/plans/261103-thanh-toan-nghi-phep-duoc-cr-719/plan.md` |
| Bài Help Center | `backend/scripts/seed_help_nghi_phep.py` (15 bài: thẻ + 14 bài con) · bài YCTT nghỉ phép cho kế toán ở `backend/scripts/seed_help_yctt_thanh_toan_nghi_phep.py` · bài Cài đặt nhân sự ở `backend/scripts/seed_help_nhan_su.py` · báo cáo khóa 30 ở `backend/scripts/seed_help_bao_cao_nhan_su.py`. Nội dung ở đây và ở seed phải khớp nhau |
| Nguồn nghiệp vụ | `doc/erp/tham-khao-hrm/02-don-tu-va-duyet.md` (DT1, DT6) · `10-de-xuat-ap-dung.md` (V1-6, V1-7) |

---

## 1. Phân hệ này để làm gì

Số hóa một việc mà trước đây chạy bằng giấy và tin nhắn: **xin nghỉ, duyệt nghỉ,
và biết mỗi người còn bao nhiêu ngày phép.**

Thứ đáng giá nhất không phải tờ đơn — tờ đơn thì phần mềm nào cũng làm được — mà
là **số ngày phép còn lại hiện ngay lúc đang nhập**. Doc nghiệp vụ gọi đó là
*"chi tiết nhỏ, nhưng nó cắt phần lớn số đơn sai và phần lớn câu hỏi gửi về
phòng Nhân sự"*. Toàn bộ phần quỹ phép, bậc thâm niên và lịch ngày lễ tồn tại để
con số đó đúng.

## 2. Bốn khái niệm — đừng lẫn

| Thứ | Bảng | Là gì |
|---|---|---|
| **Đơn nghỉ phép** | `tab_leave_request` | **Chứng từ nghiệp vụ**, nguồn sự thật. Có số `NP001`. |
| **Dòng loại nghỉ** | `tab_leave_request_line` | Một loại nghỉ trong đơn kèm số ngày. Một đơn nhiều dòng — xem §7.1. |
| **Giấy nghỉ phép (GNP)** | `tab_document` loại `GNP` | **Hồ sơ lưu sổ**, tự sinh sau khi đơn đã duyệt. |
| **Loại nghỉ** | `tab_leave_type` | Danh mục cấu hình — đổi luật bằng dữ liệu, không sửa mã. |
| **Quỹ phép** | `tab_leave_balance` | Số ngày của (một người × một năm × một loại nghỉ). |

**Vì sao giữ CẢ đơn lẫn giấy** (QĐ-NP5): *Lịch nghỉ* và mọi báo cáo phải trả lời
"tuần tới ai nghỉ" và "người này năm nay dùng bao nhiêu ngày". Trả lời được trên
cột `DATE` có chỉ mục; quét `JSON_EXTRACT` trên `tab_document.metadata` thì vừa
chậm vừa không đánh chỉ mục, và trừ quỹ sẽ dựa trên một ô không có ràng buộc kiểu.
Nhưng giấy GNP là **giấy tờ** — có số hiệu, có chữ ký, nằm trong sổ văn bản — nên
không bỏ. Hai thứ nối nhau bằng `LeaveRequest.document_id`.

⚠️ Người dùng hỏi "làm giấy nghỉ phép" thì họ muốn **nộp đơn**, không phải tạo
văn bản ở Văn thư. Tạo tay ở Văn thư là ra một tờ giấy **không gắn với quỹ phép nào**.

## 3. Chín màn hình

Menu *Nhân sự ▸ Nghỉ phép* có bảy mục con: **Đơn nghỉ phép · Nghỉ bù · Thanh toán nghỉ phép · Lịch nghỉ · Quỹ phép năm ·
Phân bổ chính sách · Thiết lập**. *Thiết lập* gom bốn màn danh mục, chuyển qua lại bằng hàng thẻ `LeaveSectionTabs` (mỗi thẻ chỉ hiện với
người sửa được danh mục đó). Các đường dẫn `/hr/holidays`, `/hr/leave-blocks`, `/hr/leave-policies` và
`/hr/leave-policy-assignments/bulk` có mục menu **ẩn** để route có gác quyền (gác điều hướng mặc định MỞ; trang hàng
loạt gác `leave_balance` + `write`, mục ẩn dài hơn thắng).

| Màn | Đường dẫn | Khóa quyền |
|---|---|---|
| Đơn nghỉ phép (danh sách + chi tiết + nộp mới) | `/hr/leave-requests` | `leave_request` |
| Nghỉ bù — phiếu xin nghỉ bù (danh sách + chi tiết + lập mới) — §13.6 | `/hr/leave-comp-requests` | `leave_comp_request` |
| Thanh toán nghỉ phép — phiếu đổi ngày phép ra tiền (danh sách + chi tiết + lập mới) — §16 | `/hr/leave-encashments` | `leave_encashment` |
| Lịch nghỉ (theo tuần) | `/hr/leave-calendar` | `leave_request` |
| Quỹ phép năm (thẻ *Theo dòng quỹ* · *Theo nhân sự* `?view=people`) — §15.6 | `/hr/leave-balances` | `leave_balance` |
| **Chính sách nghỉ phép** — một màn hai tab (duoc-CR-750): *Phân bổ* (+ trang *Phân bổ chính sách hàng loạt* `/bulk`) §15.3 · *Chính sách* (gói) §15.2; `?tab=assignments\|policies` | `/hr/leave-policy-assignments` | tab Phân bổ `leave_balance.write`, tab Chính sách `leave_type.write`; mục menu hiện khi có một trong hai |
| Thiết lập ▸ Loại nghỉ (tab *Thông tin* · *Bậc thâm niên* · *Hạn mức theo nhóm*) | `/hr/leave-types` | `leave_type` |
| Thiết lập ▸ Lịch ngày lễ | `/hr/holidays` | `holiday` |
| Thiết lập ▸ Ngày cấm nghỉ — §13.5 | `/hr/leave-blocks` | `leave_type` (không thêm khóa) |
| Chi tiết gói chính sách (tab *Thông tin* · *Loại nghỉ & số ngày* · *Đang phân bổ*) — §15.2; `/hr/leave-policies` cũ chuyển về tab Chính sách | `/hr/leave-policies/:id`, `/new` | `leave_type` (không thêm khóa) |

Bốn màn thiết lập dựng bằng **khung CRUD khai báo** (`shared/crud/`), các màn còn
lại viết tay vì có nghiệp vụ riêng. Các công tắc của nghỉ phép nằm ở trang **Cài đặt nhân sự** (`/hr/settings`,
khóa `setting`) — §14.

### 3.1. Lịch nghỉ ở khổ điện thoại (duoc-CR-329, 09/09/2026)

Ba chế độ xem của `/hr/leave-calendar` đổi hình dạng khác nhau ở khổ hẹp, và
đó là **ba vai khác nhau** chứ không phải ba bản thu nhỏ của cùng một thứ:

| Chế độ | Khổ rộng | Khổ hẹp | Trả lời câu |
|---|---|---|---|
| Tháng | chip tên trong ô | **vạch ngang xếp chồng** (một vạch một người: xanh = đã duyệt ở trên, vàng = chờ duyệt ở dưới), cả ô là một nút | *tháng này ngày nào đông người nghỉ* |
| Tuần | hàng ngang, nhãn ngày một cột | hàng ngang, nhãn ngày + số đếm ở dòng trên, chip tên xuống dòng dưới | *tuần này ai nghỉ* |
| Ngày | bảng 7 cột | danh sách **thẻ** (`LeaveRequestCard`), ô lọc dọn vào tờ trượt **Bộ lọc** | *hôm đó ai nghỉ, nghỉ mấy ngày* |

- ⚠️ **Chế độ tháng ở khổ hẹp KHÔNG có tên người — cố ý.** Ô rộng ~48px, chip
  tên cắt còn ba ký tự (**Deg**, **Phạ**) thì tốn trọn chỗ mà không nói được ai.
  Đường xem tên là **đổi sang Tuần** hoặc **chạm vào ô** để mở chế độ Ngày.
  Đã dựng thêm một **bản liệt kê dọc** dưới lưới để bù, rồi **bỏ** cùng ngày:
  một tháng 21 lượt nghỉ ra 21 hàng dài hơn 2000px và nói lại gần đúng thứ chế
  độ Tuần đã bày sẵn.
- ⚠️ Ngưỡng đổi hình dạng tính trên **bề rộng ĐO ĐƯỢC của lưới** (`< 92px` một
  ô), không trên bề rộng màn hình: máy 820px với menu trái mở chỉ còn 75px một
  ô — hỏng y hệt điện thoại nhưng không ai gọi nó là điện thoại.
- Nhãn khoảng đang xem ở khổ hẹp **là nút mở bảng chọn tháng/năm**
  (`LeaveCalendarMonthPicker`), gộp ba thứ mà khổ rộng bày rời. Hàng đầu xếp
  *trái là "đang ở đâu", phải là "đi đâu"* (**Hôm nay** + cặp mũi tên).
- **Lối bày lưới tháng theo Google Calendar** (duoc-CR-330): số ngày canh giữa
  đầu ô · không tô nền cuối tuần / ngoài tháng (chỉ làm nhạt chữ) · ngày lễ là
  chip đầu tiên trong ô · ngày 1 kèm tên tháng (**1 thg 10**). Riêng **nền hồng
  của ngày lễ thì giữ** — với Google đó chỉ là một sự kiện, với bảng công nó là
  cả công ty nghỉ.
- ⚠️ **Số chip bày được trong một ô là ĐO, không đặt cứng**
  (`utils/month-cell-lines.ts`): ô cao ~96px trên màn 1440×900 (3 chip) nhưng
  chỉ ~79px trên laptop 1280×800 (2 chip). Dòng **+N người nữa** **chiếm chỗ của
  một chip** chứ không cộng thêm — vẽ đủ chip rồi thêm dòng đó là nó bị đường kẻ
  ô cắt ngang, mà nó là lối duy nhất đọc tên những người bị giấu.
- ⚠️ Bộ chọn **Ngày · Tuần · Tháng** ở khổ hẹp dựng kiểu **cấp hai** — chữ trần
  + gạch chân, không khung không nền xanh. Dải tab chuyển màn ngay phía trên đã
  là nút xanh nền đặc; hai dải cùng kiểu thì đọc thành cùng một cấp và không ai
  biết cái nào chuyển màn, cái nào đổi cách nhìn.

### 3.2. Chi tiết đơn ở khổ điện thoại (duoc-CR-333, 09/09/2026)

`/hr/leave-requests/:id` là **một trang cho hai chế độ**: đơn còn sửa được thì
dựng `LeaveRequestForm`, đã gửi duyệt thì dựng `LeaveRequestSummary`. Cả hai
chế độ đều đã bấm tay ở 360 · 390 · 768 · 1024 · 1440.

- ⚠️ **Bản chỉ xem KHÔNG bày trường bằng khung kiểu ô nhập.** Đến 09/09/2026 mỗi
  trường còn là một `ReadOnlyValue` (viền, nền xám, cao 36px) xếp theo lưới của
  form. Ba cái sai của lối đó, thấy rõ nhất trên điện thoại:
  1. **Ô không ai khai thành một khung trống trơn** — ở một trang không cho gõ,
     nó đọc ra *"màn hình lỗi"* chứ không đọc ra *"người nộp không khai số điện
     thoại"*. Nay ô trống hiện **dấu gạch**.
  2. **Bốn giá trị ngắn ngốn 330px chiều cao**, trong khi giá trị dài nhất là
     mười ba ký tự.
  3. **Hai thứ ngôn ngữ trong cùng một thẻ** — khung kiểu-ô-nhập nằm cạnh hai
     bảng viền thật (*Loại nghỉ*, *Bàn giao*) đọc ra như hai màn ghép lại.

  Nay cả thẻ dùng chung một ngôn ngữ: hàng có viền, nhãn xám, giá trị đậm
  (`InfoList` / `InfoRow`). Khổ hẹp nhãn nằm trên giá trị, từ `sm` nhãn thành
  cột trái rộng 11rem. ⚠️ **Vẫn là chữ thật trong thẻ thường** — luật cấm
  `<Input disabled>` không đổi, chỉ đổi hình dạng. ⚠️ Và **không dùng
  `justify-between`** cho hàng nhãn–giá trị: trên màn 1440 nó đẩy giá trị ra tận
  mép phải, cách nhãn cả nghìn pixel.
- ⚠️ **Nhóm nút xếp theo CẤP BẬC, không xếp lưới đều.** Bản đầu dựng lưới 2×2
  đều tăm tắp rồi bỏ ngay trong ngày (*"4 cục nhìn nó xấu á"*): bốn khối trắng
  bằng vai nhau thì mắt không biết bấm cái nào, mà cả bốn cùng to nên nút xanh
  cũng chẳng nổi hơn. Nay **đúng một nút chính** trải hết hàng trên, mọi nút còn
  lại chia đều hàng dưới. Hai lớp `PRIMARY_ACTION_SLOT` /
  `SECONDARY_ACTION_SLOT` khai ở `hr/utils/leave-detail-action-slots.ts` — khai
  một chỗ vì cụm nút do **hai tệp** cùng dựng (trang chi tiết +
  `leave-detail-decision-actions.tsx`), chép tay hai bản là hai bên xếp lệch
  nhau. Nút chính đổi theo trạng thái: *Duyệt đơn* khi đang duyệt · *Gửi duyệt*
  khi đơn đã lưu · *Lưu nháp* khi đơn chưa có id.
- ⚠️ **"Lưu nháp" chỉ xanh đặc khi đơn CHƯA có id.** Đơn đã lưu rồi thì việc
  người ta định làm là *Gửi duyệt*; hai nút xanh đứng cạnh nhau thì chẳng nút
  nào còn là nút chính nữa.
- ⚠️ **Huy hiệu trạng thái nằm ở dòng MÔ TẢ, không nằm trong nhóm nút.** Nó là
  thông tin về tờ đơn chứ không phải một hành động; đứng chung với cụm nút thì
  nó ăn mất một chỗ và mọi nút sau lệch đi một nhịp.
- ⚠️ **`PageHeader` dùng `flex-[1_1_16rem]`, không dùng `flex-1`** — sửa ở tầng
  dùng chung nên mọi trang chi tiết hưởng theo. `flex-1` đặt cỡ gốc bằng **0**,
  tức khối tiêu đề không đòi lấy một pixel nào: ở 768px màn 4 nút bóp tiêu đề
  còn ~60px và **Đơn nghỉ phép NP010** rơi xuống bốn dòng mỗi dòng một chữ, trong
  khi cụm nút vẫn thong dong một hàng. 16rem là mức tiêu đề đòi giữ — đủ chỗ thì
  nút vẫn ở cùng hàng, không đủ thì cả cụm xuống hàng riêng.
- **Form**: hàng *ngày · buổi · giờ* của đơn **nghỉ theo giờ** chỉ đứng cùng một
  hàng từ `sm`. Ba ô cứng trên màn 390px thì hai ô sau chiếm 240px, ô NGÀY còn
  chưa tới 60px — không đọc nổi ngày nào. Dưới `sm` ô ngày trải hết hàng, buổi
  và giờ chia đôi hàng dưới. Cột **Số ngày** của bảng loại nghỉ cũng rút lại dưới
  `sm`: phần thừa đó lấy đúng từ ô chọn loại nghỉ, thứ duy nhất ở hàng có chữ
  dài (**Nghỉ không lương**).

## 4. Vòng đời một tờ đơn

```
        lập đơn                gửi duyệt
Nháp ──────────────► Nháp ──────────────► Chờ duyệt ──────► Đã duyệt
 ▲                                          │  │  │           │
 │      rút phiếu                           │  │  │           │ sinh giấy GNP
 └────────────────────────────────────────  ┘  │  │           │ trừ quỹ thật
        Trả về chỉnh sửa ◄────────────────────┘  │
        Từ chối (khóa)   ◄───────────────────────┘
        Đã hủy  ◄── người nộp, kể cả sau khi duyệt
```

Sáu trạng thái lưu **`SMALLINT`** (R2/QĐ-11): `1` Nháp · `2` Chờ duyệt ·
`3` Đã duyệt · `4` Từ chối · `5` Trả về chỉnh sửa · `6` Đã hủy. Tiếng Việt chỉ ở
tầng hiển thị; API trả kèm `status_label`.

**Chỉ sửa được ở "Nháp" và "Trả về chỉnh sửa".** Đã gửi duyệt là khóa.

**"Từ chối" khác "Trả về chỉnh sửa"** — và phải khác. Từ chối là khóa hẳn, muốn
nghỉ nữa thì lập **đơn khác**. Trả về là mời sửa rồi gửi lại chính tờ đó. Gộp hai
cái vào một trạng thái thì người soạn mở đơn ra không biết mình vừa bị dẹp hay
đang được mời sửa lại (bài học 24/08/2026 của phân hệ Văn thư).

## 5. Quỹ phép — công thức và bốn nhịp

```
còn lại = (hạn mức + thâm niên + chuyển năm trước + điều chỉnh tay + nghỉ bù)
          − đã nghỉ − đang chờ duyệt − đã thanh toán ra tiền
dùng được hôm nay = còn lại − phần chưa tới tháng (chỉ loại "Cộng dần theo tháng")
```

**Số còn lại KHÔNG lưu thành cột.** Lưu thêm thì có hai nguồn sự thật, và cái thứ
hai sẽ lệch. `balance_service.remaining()` là nơi duy nhất tính.

⚠️ Từ duoc-CR-715, số mà **màn hình, chốt đủ quỹ, báo cáo và trợ lý AI** đọc là
`balance_service.available_days(db, row)` (nhiều dòng: `available_days_map`, 3 truy vấn cho bất kỳ số dòng), không
phải property `remaining_days`: loại `accrual_mode = MONTHLY` giữ lại phần chưa tới tháng
(`accrual_service.accrual_holdback`). Đọc thẳng `remaining_days` chỉ đúng với năm đã qua. Cột `comp_days` (ngày nghỉ bù
đã duyệt, §13.6) nằm trong tổng được nghỉ — mọi chỗ cộng `allocated + seniority + carried + adjusted` phải cộng cả nó.

Sổ quỹ chạy theo bốn nhịp, khớp bốn kết cục của bộ máy duyệt:

| Nhịp | Khi nào | Làm gì |
|---|---|---|
| `reserve` | gửi duyệt | `pending_days += n` — **giữ chỗ** |
| `consume` | duyệt xong | `pending −= n`, `used += n` |
| `release` | từ chối / trả về / rút / hủy | `pending −= n` |
| `refund_used` | hủy một đơn **đã duyệt** | `used −= n` |

Phiếu thanh toán nghỉ phép (duoc-CR-719, §16) đi đúng ba nhịp đầu nhưng nhịp duyệt ghi vào cột riêng: duyệt `pending −= n`, `encashed_days += n` (không cộng `used`); hủy phiếu đã duyệt `encashed_days −= n`. `remaining_days` đã trừ `encashed_days`, nên mọi chỗ đi qua `available_days` tự đúng.

⚠️ **Nhịp GIỮ CHỖ là bắt buộc.** Thiếu nó thì nộp mười đơn liền tay đều lọt, vì
đơn nào cũng thấy quỹ còn nguyên — lỗi cổ điển của mọi hệ nghỉ phép, và nó chỉ lộ
ra khi đã có người nghỉ thừa hai tuần.

⚠️ Ba kết cục **không duyệt** đều phải `release`. Quên một cái thì số ngày đó treo
vĩnh viễn trong `pending_days`, người ta mất phép, và lỗi **không có triệu chứng**
cho tới khi ai đó cộng tay lại sổ cuối năm.

### Bậc thâm niên

Luật *"cứ 5 năm thì thêm 1 ngày phép"* khai bằng **dữ liệu** (`tab_leave_type_seniority`),
không bằng `years // 5` trong mã — công ty đổi sang bậc không đều là sửa bảng chứ
không deploy lại. Bộ seed: *5 năm +1 · 10 năm +2 · 15 năm +3 · 20 năm trở lên +4*.

**Lấy bậc CAO NHẤT khớp được, không cộng dồn**: người 10 năm được **+2**, không
phải +3. Màn hình nói câu này ra thành chữ, vì đọc bảng số không đoán được.

### Ứng phép: mặc định không có (QĐ-NP2, nới ở duoc-CR-715)

Mặc định xin vượt quỹ là **chặn lúc gửi duyệt**, không ghi nợ. Muốn nghỉ tiếp thì chọn loại
**Nghỉ không lương** — câu chặn của backend nói thẳng đường đó.

Từ duoc-CR-715 mỗi loại nghỉ có `max_negative_days` (ô *Cho ứng phép tối đa (ngày)*, 0–30, mặc định 0 = như cũ):
`check_enough*` cho số dùng được xuống tới `−N`. Hệ **vẫn không có sổ công nợ phép** — phần ứng chỉ hiện thành số âm
ở cột *Còn lại*; đối chiếu khi nghỉ việc là việc của phòng Nhân sự. Hộp gợi ý trên form đơn đọc `max_negative_days` từ
`/api/leave-requests/tools/my-balance` và chỉ cảnh báo khi vượt cả phần được ứng.

### Cấp phát quỹ

Nút *Cấp quỹ năm* ở màn Quỹ phép, **chạy lại được**: chỉ tạo dòng còn thiếu. Bấm
hai lần không nhân đôi; thêm người giữa năm thì bấm lại là họ có quỹ. Cấp **một
lần đầu năm** (Q1), thâm niên tính tại 01/01 — không cộng dần theo tháng.

Số `allocated_days` của dòng mới: từ duoc-CR-717 `ensure_balance` gọi `policy_allocation.allocated_days` — thứ tự
**phân bổ chính sách của người (§15) → khớp hình thức nhân viên → khớp cấp bậc → `annual_quota_days`** (ba bước sau là
`accrual_service.resolve_quota` của CR-715, §13.2), rồi nhân tỷ lệ theo `accrual_mode`. Loại không có trong chính sách
rơi về luật của loại. Không có phân bổ nào thì ra **đúng từng con số** của `prorate_allocation(resolve_quota(...))` cũ.

Hộp *Cấp quỹ phép năm …* (duoc-CR-717) lọc thêm theo loại nghỉ (nhiều), pháp nhân, phòng ban, hình thức nhân viên, cấp
bậc — xem §15.7.

⚠️ Cố ý **không** cập nhật dòng đã có theo hạn mức mới: đổi hạn mức giữa năm thì
quỹ đã cấp giữ nguyên, luật mới áp cho lần cấp sau. Ngoại lệ duy nhất: tạo / kết thúc / xóa **phân bổ chính sách** có ô
*Tính lại hạn mức năm nay* (mặc định bật) — chỉ quỹ năm nay, chỉ cột `allocated_days` (§15.4).

### Kết sổ cuối năm (07/09/2026)

Số dư năm cũ đi đâu là **luật của từng loại nghỉ** (`year_end_mode`), không phải
luật chung:

| Nước | Mã | Làm gì |
|---|---|---|
| Hết năm là mất | `0` | Mặc định. Không đụng tới dòng quỹ nào |
| Mang sang năm sau | `1` | Cộng vào `carried_days` của **chính loại đó**, năm sau |
| Quy đổi sang loại nghỉ khác | `2` | Cộng vào loại **nhận**, sau khi nhân `convert_ratio` |

⚠️ **Không có gì tự chạy đêm 31/12.** Phải có người bấm *Kết sổ năm N* ở màn Quỹ
phép. Cùng lý lẽ với nút *Cấp quỹ*: hệ không có bộ chạy nền, mà một việc nền hỏng
lặng lẽ đêm 31/12 thì tới tháng Ba mới có người phát hiện — lúc đó cả công ty đã
nghỉ theo một con số sai.

- **Gác bằng `leave_balance.write`**, không phải `create` như nút Cấp quỹ: kết sổ
  **sửa hai dòng quỹ đã có** (trừ năm cũ, cộng năm mới) — cùng mức nguy hiểm với
  cột điều chỉnh tay. Chỉ chạm tới nhân sự **trong phạm vi người bấm**.
- **Chạy lại được, và lượt sau vét nốt.** Mỗi lượt chỉ đẩy phần `remaining_days`
  còn lại, cộng dồn vào `carried_out_days`. Bấm hai lần liền không nhân đôi; nhưng
  nếu giữa hai lượt có đơn năm cũ **bị từ chối** hoặc đơn đã duyệt **bị hủy** thì
  số ngày quay lại đó được đẩy tiếp — bản đầu bỏ qua hẳn dòng đã kết sổ nên mấy
  ngày ấy kẹt vĩnh viễn ở năm cũ.
- **Cấu hình quy đổi hỏng thì BỎ dòng, không đoán** — và trả về `skipped_config`
  để câu thông báo nói ra. Backend còn chặn sớm hơn, **ngay lúc lưu loại nghỉ**
  (`catalog_controller._check_year_end_config`): tỷ lệ phải > 0, phải chọn loại
  nhận, loại nhận phải **khác chính nó** và phải bật **Trừ vào quỹ phép năm**.
- **Phần mang sang HẾT HẠN** cuối tháng `carry_over_expire_month` của năm nhận
  (thông lệ: hết 31/3; `0` = không hết hạn). Thu hồi lúc **chạm vào** dòng quỹ
  (`expire_carried`), không phải bằng việc chạy nền.
- ⚠️ **Phần mang sang được coi là TIÊU TRƯỚC.** Sổ chỉ có một cục `used_days`,
  không biết ngày nào tiêu vào quỹ nào, nên phải chọn một phía — chọn phía có lợi
  cho người lao động, vì phép mang sang là phép sắp hết hạn.
- Phần đã **quy đổi** thì sống theo luật hết hạn của **loại nhận**, không theo
  loại nguồn.

**Bảng đối chiếu kết sổ (duoc-CR-664, 22/10/2026).** Kết sổ xong, hộp **Đối chiếu kết sổ
‹năm›** tự mở (mở lại bằng nút cùng tên ở màn Quỹ phép) — mỗi dòng một (nhân sự × loại
nghỉ): **số cũ** (trước kết sổ) · **số mới** (sau) · **chênh** · loại nhận · ngày cộng vào
năm sau; nút *Xuất Excel*. API: `GET /api/leave-balances/close-year/review?year=` và
`.../review/export`, gác `leave_balance.read` / `export` + `apply_scope` (thuộc màn Quỹ
phép, KHÔNG phải báo cáo của phân hệ Báo cáo nên không cần `ReportKey`).

- **Không thêm bảng snapshot / migration.** `close_year` đã để dấu trong chính dòng quỹ:
  `carried_out_days` = tổng ngày đã chuyển đi, và `remaining_days` đã trừ nó. Nên
  `số cũ = còn lại + đã chuyển`, `số mới = còn lại`, `chênh = -đã chuyển`. Mã:
  `carryover_review_service.py`; số truy vấn cố định ≤ 4 (có test đếm).
- ⚠️ **Số cũ dựng lại tại thời điểm xem**, không phải ảnh chụp: đơn năm cũ duyệt/hủy sau
  kết sổ làm số đổi theo. Loại nhận và tỷ lệ theo cấu hình loại nghỉ **hiện hành** (sửa
  cấu hình sau kết sổ thì cột **cộng vào năm sau** là số ước). Chỉ liệt kê dòng ĐÃ chuyển
  (`carried_out_days > 0`); dòng bị bỏ vì cấu hình hỏng vẫn chỉ báo ở câu thông báo.
- Cần ảnh chụp bất biến theo từng lần bấm (kiểm toán) thì mới phải thêm bảng lưu vết; chưa ai đòi.

### Điều chỉnh tay

Cột duy nhất nhận **số âm**. **Ghi ĐÈ, không cộng dồn** — người dùng nhìn con số
hiện tại và gõ con số họ muốn nó thành; cộng dồn thì bấm Lưu hai lần là gấp đôi.
**Bắt buộc có lý do**, ghi vào `tab_audit_log`: đây là thao tác tặng ngày phép.

## 6. Số ngày nghỉ

`workday_service.count_leave_days()` là nơi **duy nhất** tính. ⚠️ **Thứ Bảy không còn cứng — đó là cấp Chủ nhật của lịch làm việc của mỗi người.** Xem cách tính chi tiết ở [21-lich-lam-viec.md — §7, §12](03-lich-lam-viec.md).

### Hai ô buổi là MỐC, không phải buổi (vá 07/09/2026)

`from_session` nói nghỉ **bắt đầu** lúc nào, `to_session` nói nghỉ **kết thúc**
lúc nào. Nên **ngày đầu và ngày cuối tra hai bảng khác nhau**:

| Ô buổi | Ngày ĐẦU | Ngày CUỐI |
|---|---|---|
| Cả ngày | 1.0 | 1.0 |
| Buổi sáng | **1.0** — bắt đầu từ sáng là nghỉ trọn ngày | 0.5 |
| Buổi chiều | 0.5 | **1.0** — kết thúc cuối chiều là nghỉ trọn ngày |

Nghỉ gọn trong **một ngày** thì hai ô cùng nói về ngày ấy, phải xét cả hai
(`constants.same_day_credit`): *Cả ngày → Sáng* là **0.5**, *Sáng → Chiều* là **1.0**.

⚠️ Bản trước 07/09/2026 tra CHUNG một bảng `{Cả ngày: 1, Sáng: .5, Chiều: .5}`
cho cả hai đầu — tức đọc ô buổi thành *"buổi nào của ngày đó được nghỉ"*, mâu
thuẫn với chính luật *chiều → sáng cùng ngày là khoảng trống* mà nó đang chặn.
Ba nhóm ca sai, **im lặng**, vì con số ra vẫn hợp lý:

| Ca | Bản cũ | Đúng | Ai chịu |
|---|---|---|---|
| Sáng 05 → hết 07 | 2.5 | 3.0 | công ty trừ hụt phép |
| Cả ngày 05 → Chiều 07 | 2.5 | 3.0 | công ty trừ hụt phép |
| Cả ngày → Sáng, cùng ngày | 1.0 | 0.5 | **người lao động mất nửa ngày** |

Cùng luật đó phải khớp ở **ba nơi**: `leave/constants.py` (đơn),
`core/leave_codes.py` (giấy GNP), và bản TypeScript
`document/helpers/suggested-day-count.ts`. Lệch một nơi là cùng một tờ đơn ra
hai con số tùy người nhập qua màn nào.

### Trần khoảng ngày

Một tờ đơn tối đa `MAX_RANGE_DAYS = 400` ngày dương lịch, chặn ở
`check_date_range`. Đơn nhiều khoảng (§7.3) tính trần trên **bao ngoài** (từ ngày đầu khoảng đầu tới ngày cuối khoảng cuối, kể cả khe), chặn ở `request_periods.check_periods`. ⚠️ Không có chốt này thì `date_range` lặng lẽ dừng ở 400 và
trả con số nhỏ hơn sự thật — gõ nhầm năm 2036 (3651 ngày) ra đúng **343 ngày**,
không có triệu chứng nào cho tới lúc đối chiếu sổ.

- Người dùng **sửa đè được** — lịch làm việc thật luôn có ngoại lệ máy không biết
  (ca kíp, nghỉ bù, công trường chạy Chủ nhật).
- Loại nghỉ dài liên tục (**Thai sản**) tắt cờ `exclude_holiday` nên đếm tuốt —
  nghỉ 6 tháng thì không ai bù cuối tuần.
- **Lịch ngày lễ**: `company_id = 0` là áp cho **mọi pháp nhân**; pháp nhân có lịch
  riêng thì thêm dòng của nó, hai nguồn được gộp. Cờ *lặp hằng năm* chỉ dùng cho
  ngày **cố định theo dương lịch** (01/01, 30/4, 02/9) — Tết Âm và Giỗ Tổ trôi theo
  lịch âm nên mỗi năm nhập lại.

## 7. Luật trên tờ đơn

| Luật | Chi tiết |
|---|---|
| Khoảng ngày | **Mỗi khoảng** phải có `to_date >= from_date`; nghỉ từ **chiều đến sáng cùng ngày** là khoảng trống → chặn (câu báo lỗi nêu **Khoảng thứ N**). Một đơn có 1–20 khoảng, xem §7.3 |
| Chồng ngày | Hai đơn còn hiệu lực (chờ duyệt / đã duyệt) của **cùng một người** không được chồng khoảng — chồng là trừ phép hai lần cho một ngày. Xét **từng khoảng**, không xét bao ngoài: đơn khác rơi vào khe giữa hai khoảng vẫn gửi được (§7.3) |
| Giới tính | Thai sản chỉ áp cho hồ sơ nữ. **Hồ sơ chưa khai giới tính KHÔNG bị chặn** — chặn là khóa cả công ty tới khi Nhân sự nhập bù |
| Trần mỗi lần | Cưới hỏi · tang chế 3 ngày. `0` = không giới hạn |
| ~~Báo trước~~ | **ĐÃ BỎ 05/09/2026.** Không còn luật "phải nộp trước N ngày" — nghỉ ngày mai vẫn gửi duyệt được. Cột `min_notice_days` còn trong bảng nhưng không ai đọc, và đã gỡ khỏi schema lẫn màn danh mục loại nghỉ |
| Nhập đủ | Chốt ở lúc **gửi duyệt**, không phải lúc lưu nháp — cùng luật với `required-fields.ts` của Thu mua |
| Lập hộ | Được, và từ 07/09/2026 form có ô **Người nghỉ** (mặc định điền sẵn chính mình). Gác bằng `ensure_can_create_for`: phải có `leave_request.create` phạm vi **rộng hơn `own`** VÀ đọc được hồ sơ người đó trong phạm vi `employee`. Cả người lập (`created_by`) lẫn người nghỉ (`employee_id`) đều thấy tờ đơn ở phạm vi **của mình** |
| Nghỉ **theo giờ** | Buổi nghỉ có lựa chọn thứ tư **Theo giờ** (`SESSION_HOURLY = 4`, 07/09/2026): khai `from_time`/`to_time`, **vắt qua nhiều ngày được** (từ 14:00 ngày A đến 10:00 ngày B). Số ngày do máy quy đổi, **không cho gõ đè** — ngày đầu tính tới hết giờ làm, ngày cuối từ đầu giờ làm, ngày giữa trọn một công, T7/CN/lễ bỏ qua. Khung giờ làm khai ở `constants`: **08:00–17:00, nghỉ trưa 12:00–13:00, 8 giờ công/ngày**; giờ ngoài khung không tính |

### 7.1. Nhiều loại nghỉ trong một đơn (07/09/2026)

*"Nghỉ 07→10/09, trong đó 3 ngày phép năm + 1 ngày không lương"* — trước đó phải
lập hai đơn, mà chốt **chồng ngày** ở trên lại chặn đúng chuyện đó.

**Cả đơn dùng CHUNG các khoảng ngày (một hoặc nhiều, §7.3); dòng chỉ chia SỐ NGÀY, không gắn khoảng.** Bản khai ngày riêng
cho từng dòng tra được *"ngày 09 nghỉ loại gì"*, nhưng đổi lại người nhập phải gõ
hai đầu ngày cho mỗi loại và chốt chống chồng ngày phải chạy cả trong lẫn ngoài
tờ đơn. Khách chọn bản gọn.

Hai cột đầu đơn thành **dẫn xuất — backend tự đặt, giao diện không gõ**:

```
total_days    = Σ line.days
leave_type_id = loại của dòng NHIỀU NGÀY NHẤT (hòa → dòng đầu)
```

Sáu luật trên bảng dòng (`request_service.collect_lines` → `resolve_days` → `check_lines`):

| Luật | Chi tiết |
|---|---|
| Không trùng loại | Một loại chỉ một dòng — hai dòng cùng loại là hai lượt trừ vào cùng một sổ quỹ |
| Số ngày > 0 | Ngoại lệ: đơn có **đúng một dòng** để trống thì máy tự tính từ khoảng ngày, y như trước |
| Trần số loại | `MAX_LINES = 10` |
| Giới tính · trần mỗi lần | Xét theo **từng dòng**, theo loại của dòng đó — Thai sản nằm ở dòng phụ vẫn bị chặn với hồ sơ nam |
| Theo giờ | Khóa còn **một dòng** — nghỉ hai tiếng chia hai loại là ca chưa từng có, và nó phá phép quy đổi giờ→ngày |
| Trần theo khoảng | `Σ days` không vượt số ngày **dương lịch** của khoảng. Trần đếm cả T7/CN/lễ nên không chặn nhầm ca hợp lệ (công trường chạy Chủ nhật), nhưng bịt được lỗ cũ: `total_days` sửa đè tự do nên gõ 30 ngày trên khoảng hai ngày lọt thẳng vào sổ quỹ |

⚠️ **Sổ quỹ chạy theo DÒNG ở cả bốn nhịp.** Gói vào bốn hàm `reserve_lines` ·
`consume_lines` · `release_lines` · `refund_lines` chứ không để nơi gọi tự lặp:
nơi gọi có bốn chỗ và chỉ cần một chỗ quên vòng lặp là sổ lệch âm thầm. `check_enough`
cũng theo dòng — 4 ngày = 3 phép năm + 1 không lương có thể qua trong khi 4 ngày
phép năm thì hết phép.

**Giấy GNP: một tờ cho cả đơn.** `metadata.leave_type` là loại chính; ô `leave_lines`
liệt kê đủ và **chỉ ghi khi từ hai dòng trở lên**, để đơn một loại giữ nguyên hình
dạng cũ. Mã loại trong ô đó cố ý không đối chiếu `LEAVE_TYPE_SET` — giấy là bản
chép của một quyết định đã ký, chặn ở đó không cứu được gì.

⚠️ **Hạn chế đã biết — ĐÃ CHỐT BỎ 26/10/2026 (HR3-3, duoc-CR-683).** Điều kiện rẽ nhánh của luồng duyệt đọc
`leave_type_id`, tức **loại chính**. Chủ sản phẩm chốt: luồng duyệt coi mọi đơn là nghỉ phép, **không rẽ nhánh theo từng loại nghỉ của đơn**; không làm phương án đọc đủ loại. Đoạn dưới giữ lại để biết hành vi hiện tại, không còn là việc chờ làm. Nhánh khai *"loại nghỉ = không lương thì thêm
chặng Giám đốc"* sẽ KHÔNG chạy cho tờ đơn 3 ngày phép năm + 1 ngày không lương.
Cố ý không đưa danh sách loại vào `entity_context`: `condition_service` chỉ so được
giá trị vô hướng, thêm một ô mà phép `in` của nó không đọc nổi thì tệ hơn không có.

### 7.2. Tệp đính kèm và bản in (bao-CR-505, 28/09/2026)

Màn chi tiết đơn có thẻ **Tệp đính kèm** ngay dưới tờ đơn (ảnh giấy khám bệnh, giấy
ra viện, thiệp cưới… — ảnh JPG/PNG/WEBP, PDF, Word, Excel, tối đa 50MB mỗi tệp). Đơn
mới chưa lưu thì thẻ chỉ nhắc **Lưu nháp để đính kèm tệp**; đơn **Nháp / Trả về** thì
thêm và gỡ được; đã gửi duyệt trở đi thì chỉ xem và tải về (backend khóa y hệt bằng
`check_editable`). Người **đang phải ký** tờ đơn xem được tệp dù ngoài phạm vi dữ liệu
— cùng ngoại lệ CR-260 ở §8; ký xong là hết. Tệp là **riêng tư** (không có URL công
khai), đi qua cửa đính kèm dùng chung với `entity=leave_request`.

**Bản in** (nút **In đơn**, trang `/print/leave-request/:id` — từ bao-CR-506 in được cả đơn Nháp / Chờ duyệt / Trả về, không riêng đơn đã duyệt): mỗi ảnh đính kèm in thành **một trang A4
riêng sau tờ đơn** (in hai mặt thì ảnh đầu nằm đúng mặt sau), co vừa trang, giữ tỉ lệ.
Tệp không phải ảnh không in, chỉ ghi tên ở dòng **Tài liệu đính kèm** trên mặt đơn. Nút
In khóa tới khi mọi ảnh đã nạp xong; ảnh nào nạp hỏng thì trang in báo tên ảnh đó.

**Bắt buộc đính kèm theo loại nghỉ (duoc-CR-661, 22/10/2026).** Loại nghỉ bật cờ
**Bắt buộc đính kèm** (`tab_leave_type.require_attachment`) thì đơn phải có ít nhất một
tệp lúc **gửi duyệt** — `request_service.check_required_attachment`, gọi trong
`prepare_submit` (sau chốt **lý do**, trước chốt trùng ngày/đủ phép). Thiếu thì 400 kèm
câu nêu tên loại, ví dụ *"Loại nghỉ **Nghỉ ốm** bắt buộc đính kèm giấy tờ…"*.

- **Lưu nháp KHÔNG bị chặn** — tệp chỉ treo được vào đơn đã có id, nên luồng thật là:
  lưu nháp → tải tệp ở thẻ **Tệp đính kèm** → bấm *Gửi duyệt*. Đơn đang tạo (chưa có id)
  không có nút Gửi duyệt nên không kẹt.
- **Đơn nhiều loại (§7.1):** chỉ cần MỘT loại bật cờ là đơn phải có tệp. Tệp treo ở tờ
  đơn chứ không ở từng dòng, nên không phân biệt tệp nào của loại nào — chặn theo
  **có hay chưa**, câu chặn chỉ nêu các loại đòi tệp.
- **Giao diện báo trước:** thẻ **Tệp đính kèm** có dấu sao đỏ + dòng đỏ nêu tên loại khi
  form đang chọn loại bật cờ; nút *Gửi duyệt* chặn sớm (toast) khi danh sách tệp đã tải
  xong và rỗng. Chốt thật vẫn là backend; luật giao diện ở
  `hr/utils/leave-required-attachment.ts`.
- Đơn **Trả về** rồi gửi lại cũng bị kiểm lại; gỡ hết tệp ở đơn Trả về thì gửi lại bị chặn.
- Chỉ đếm tệp `entity = leave_request` của đúng đơn; không kiểm loại/đuôi tệp.

### 7.3. Nhiều khoảng ngày trong một đơn (duoc-CR-683, 26/10/2026)

*"Nghỉ 27/10 cả ngày, rồi 03/11 chiều tới 07/11"* — trước đó phải lập hai đơn. Nay một đơn khai được nhiều khoảng ngày không liền kề; đơn cũ là đúng 1 khoảng.

**Mô hình.** Bảng con `tab_leave_request_period` (`request_id`, `from_date`, `from_session`, `to_date`, `to_session`, `days`, `sort_order`). Backend **luôn ghi ≥1 dòng** (đơn cũ được backfill bởi migration `cr683nghiphep01`). Hai cặp ngày/buổi ở **đầu đơn là BAO NGOÀI dẫn xuất**: `from_*` = khoảng đầu, `to_*` = khoảng cuối, nên lọc, sắp xếp và báo cáo cũ chạy nguyên. `total_days` = tổng ngày các khoảng (có thể sửa đè ở TỔNG, không sửa đè từng khoảng).

```
Ví dụ: 27/10/2026 (T3) cả ngày  +  03/11 (T3) chiều → 07/11 (T7) cả ngày, lịch T2–T7
  periods.days = [1, 4.5]   total_days = 5.5   đầu đơn = 27/10 → 07/11
  ngày 28/10 – 02/11 là KHE: không phải ngày nghỉ
```

**Luật** (`leave/request_periods.py`, `check_periods`):

| # | Luật | Câu trả khi sai |
|---|---|---|
| 1 | 1–20 khoảng mỗi đơn | 422 (schema) |
| 2 | **Nghỉ theo giờ chỉ một khoảng** (giữ hành vi cũ: được vắt nhiều ngày) | 400 **Nghỉ theo giờ chỉ khai được một khoảng ngày** |
| 3 | Các khoảng **không chồng nhau**; sát nhau thì qua | 400 nêu hai khoảng chồng |
| 4 | Bao ngoài ≤ `MAX_RANGE_DAYS = 400` ngày | 400 |
| 5 | **Từ 2 khoảng trở lên phải cùng một năm** (quỹ trừ theo năm); đơn 1 khoảng vắt năm giữ như cũ | **422** **Tách thành hai đơn** |
| 6 | Đơn từ 2 khoảng: khoảng không có ngày làm việc nào → **luôn** chặn, kể cả khi gõ đè Tổng số ngày (form luôn gửi số ngày nên chặn theo cờ sửa đè thì không bao giờ chạy — rà mã 26/10), nêu **Khoảng thứ N … Bỏ khoảng này khỏi đơn**. Đơn 1 khoảng giữ luật cũ: gõ đè tổng thì qua | 400 |
| 7 | `check_lines`: trần Σ ngày các dòng = Σ ngày **dương lịch của các khoảng** (khe không tính) | 400 |

**Sửa đơn (PATCH).** Có `periods` thì ghi đè cả danh sách. Vắng `periods`: đơn 1 khoảng vẫn sửa bằng ô ngày như cũ; đơn từ 2 khoảng mà gửi ô ngày/buổi thì **400** **gửi đủ danh sách khoảng khi sửa ngày**; chỉ đổi lý do/bàn giao thì giữ nguyên các khoảng. Payload cũ (không `periods`) dựng thành 1 khoảng từ `from_date`/`to_date`.

**Chốt trùng ngày** xét từng khoảng của đơn khác (một truy vấn): đơn khác rơi vào khe gửi được, chạm một khoảng thì chặn.

**Sổ quỹ** vẫn chạy theo DÒNG ở bốn nhịp (§7.1); các khoảng chỉ chia ngày để tính tổng, không đụng sổ.

⚠️ **Mọi chỗ hỏi *"ngày D có nghỉ không"* phải đọc qua khoảng ngày** — `leave/period_spans.py` (`LeaveSpan`, `span_of`, `periods_by_request`) với OUTER JOIN và đường rơi về đầu đơn cho đơn chưa có dòng khoảng. Không đọc `[from_date, to_date]` của đầu đơn vì nó nuốt cả khe. Đã áp cho: Lịch nghỉ, **Ai làm / ai nghỉ** (`work_schedule/roster_leave.py`), hồ sơ làm việc theo ngày (`usage_profile/daily_sources.py`), tải việc (`capability/workload_sources.py`), chốt trùng ngày.

**API.** Vào: `periods?: [{from_date, from_session, to_date, to_session}]`. Ra (list, chi tiết, hộp việc duyệt): `periods: [{id, from_date, from_session(_label), to_date, to_session(_label), days, sort_order}]`, luôn ≥1 phần tử. `POST /api/leave-requests/tools/estimate-periods` ước tính ngày từng khoảng và tổng (giao diện dùng cho dòng **Cộng N khoảng**); `GET /tools/estimate-days` giữ nguyên. Giấy GNP: ô `leave_periods` chỉ ghi khi từ hai khoảng trở lên (cùng nếp với `leave_lines`).

**Giao diện.** Nút **+ Thêm khoảng ngày** ở form; mỗi khoảng một khung **Khoảng ngày N · X ngày**; dòng **Cộng N khoảng: Y ngày**. Màn chi tiết có mục **Thời gian nghỉ**; cột danh sách hiện **07/11/2026 · 2 khoảng**; Lịch nghỉ để trống các ngày khe; bản in liệt kê đủ khoảng.

**Trợ lý AI** soạn và sửa được nhiều khoảng qua `periods` (`draft_leave_request`, `update_tool`); hoàn tác giữ nguyên các khoảng. Đơn từ 2 khoảng thì `update_tool` từ chối sửa bằng `from_date`/`to_date`, phải gửi `periods`.

**Báo cáo theo kỳ (đổi ngày 27/10/2026, duoc-CR-686):** số **ngày** nghỉ chia theo ngày thật rơi vào kỳ / mốc (đơn 31/10 + 03/11 thì tháng 10 nhận 1 ngày, tháng 11 nhận 1 ngày), trọng số theo lịch làm việc, ngày lễ và nửa buổi. Số **đơn**, số người nghỉ, tỷ lệ từ chối, thời gian duyệt vẫn neo ngày bắt đầu, để một đơn không bị đếm hai lần. Bản trước (CR-683) neo cả số ngày vào ngày bắt đầu.

## 8. Duyệt

Chạy trên **bộ máy duyệt dùng chung** (`app/modules/approval/`), entity
`leave_request`. Luồng mẫu do `app/seed_nghi_phep.py` nạp: **trưởng bộ phận của
người xin nghỉ → trưởng phòng Nhân sự**, cả hai chặng đều khai người **dự phòng**.

⚠️ Dự phòng là bắt buộc: luật I08 bỏ người nộp ra khỏi danh sách người duyệt, nên
trưởng phòng tự xin nghỉ thì chặng 1 rỗng — mà quản lý thì cũng phải nghỉ phép.
Luồng mẫu này dùng **trưởng bộ phận / trưởng phòng Nhân sự**, tức người duyệt
được SUY RA, nên I08 vẫn áp đủ. (Từ 05/09/2026 I08 **không** áp cho bước khai
đích danh một người — xem `instance_service._exclude_submitter`.)

**Chưa khai luồng thì vẫn nộp được.** Lúc đó `approval_instance_id = 0` và người
có `leave_request.approve` bấm **Duyệt** thẳng ở màn chi tiết. Đơn **đang** chạy
trong luồng thì đường đó bị chặn — không chặn là mở một đường tắt đi vòng qua cả
luồng.

⚠️ **Còn một công tắc nữa: màn "Bật bộ máy duyệt"** (`/approval/engine`, dòng
*Nghỉ phép*). Đó là **đường lui của cả phân hệ** — gạt tắt là mọi đơn nộp từ giây
đó đi đường duyệt thẳng ở đoạn trên, kể cả khi luồng đã khai đầy đủ; đơn đang chạy
dở thì đi hết bản luồng đã chụp lúc trình, không bị cắt ngang. Phân biệt với đoạn
trên: kia là *tình cờ chưa có luồng*, đây là *cố ý tắt để quay về*. Cờ mặc định
**TẮT** khi chưa có dòng nào trong `tab_approval_switch`; `app/seed_nghi_phep.py`
nạp sẵn một dòng bật cho `leave_request`, nên hệ đã chạy seed đó thì không phải
làm gì. Tắt cờ **không** đụng tới quỹ phép — giữ chỗ `pending_days` vẫn trừ y hệt.

### 8.2. Luồng riêng cho một công ty (ca AGC, 21/10/2026)

Luồng duyệt có ô **Pháp nhân áp dụng** (màn **Phê duyệt › Luồng duyệt**). Đơn nghỉ phép mang
pháp nhân của **người nghỉ** (`tab_leave_request.company_id`, chép từ hồ sơ lúc lập), và
`flow_service.pick_flow` xét **luồng khai đúng pháp nhân đó trước** mọi luồng dùng chung, bất kể
độ ưu tiên. Không có luồng riêng nào khớp mới rơi về luồng dùng chung; không có cả hai thì đơn
đi đường duyệt thẳng như đoạn trên.

Hiện trạng prod sau ca AGC:

| | Trước 21/10 | Sau 21/10 |
|---|---|---|
| Công tắc *Nghỉ phép* ở **Bật bộ máy duyệt** | TẮT, 0 luồng, 0 đơn | **BẬT** (toàn hệ) |
| Luồng | không có | `NP-AGC`, pháp nhân = AGC, **một chặng** *Trưởng bộ phận người nộp*, dự phòng đích danh trưởng phòng Kinh doanh AGC |
| Công ty khác | duyệt thẳng | **vẫn duyệt thẳng** (chưa có luồng riêng, chưa có luồng dùng chung) |

Hệ quả cần biết:

- Chỉ đơn của người AGC có **chuông báo người duyệt**; đơn công ty khác vẫn đi đường cũ, không
  ai được báo. Việc đề xuất người duyệt cho các công ty còn lại là *kh-HR1-3*.
- Muốn quay về như cũ: tắt luồng `NP-AGC` ở màn Luồng duyệt, hoặc gạt dòng *Nghỉ phép* ở **Bật
  bộ máy duyệt** (gạt là tắt cho **mọi** công ty).
- Một chặng *Trưởng bộ phận người nộp* đọc **trưởng phòng ghi trên phòng ban** của người nộp,
  không đọc phòng của người duyệt. Trưởng phòng AGC có hồ sơ ở công ty khác vẫn duyệt được, và
  người AGC **không thấy** hồ sơ của trưởng phòng đó trong danh bạ (đại ca chọn giữ như vậy).
- Luồng chọn theo pháp nhân trong **hồ sơ người nghỉ**. Trưởng phòng AGC có hồ sơ ở công ty khác
  nên đơn của chính họ **không** đi `NP-AGC` mà đi theo công ty trong hồ sơ của họ. Ngày nào có
  người hồ sơ AGC làm trưởng phòng thì phải đổi người dự phòng: chặng *Trưởng bộ phận người nộp*
  bỏ người nộp ra (luật I08), rơi về dự phòng, mà dự phòng đang là chính trưởng phòng, tức họ
  tự duyệt đơn của mình (`instance_service._handle_no_approver`).

**Hủy đơn đang trong luồng** thì hệ **rút phiên duyệt** trước rồi mới hủy. Không
rút thì phiếu vẫn chạy, người duyệt ký xong là hook trừ quỹ cho một tờ đơn đã hủy.
Chỉ **người nộp** rút được (luật của bộ máy); người khác dùng *Trả lại* / *Từ chối*
ở màn Phê duyệt, nơi có ô ghi lý do.

### 8.1. Màn `/hr/leave-requests` có BA TAB

| Tab | Ai mở | Nội dung |
|---|---|---|
| **Cần tôi duyệt** | người đang có việc treo | Đơn đang chờ chính mình ký. Không có nút thao tác trên dòng — **bấm vào dòng** để vào chi tiết rồi duyệt. |
| **Đơn của tôi** | ai cũng có | Đơn trong phạm vi dữ liệu của mình: người thường thấy đơn của chính mình, trưởng phòng thấy cả phòng, Nhân sự thấy toàn công ty. |
| **Tôi đã duyệt** | người từng ký | Lịch sử đã ký, **gộp mỗi đơn một dòng** — ký hai chặng của cùng tờ đơn thì vẫn một dòng. |

⚠️ **`apply_scope` một mình KHÔNG đủ.** Người duyệt chặng 2 thường là Trưởng
phòng Nhân sự, mà phạm vi dữ liệu của họ không với tới đơn của nhân viên phòng
khác — bộ máy giao việc rồi chặn chính người được giao. Nên đang có việc
`TASK_PENDING` trên tờ đơn thì đọc được nó. Nới **đúng lúc treo**, không nới cho
"đã từng ký": ký xong quyền đó đóng lại, xem lại thì vào tab *Tôi đã duyệt*.

**Cột trên ba tab** (chốt 08/09/2026, sau khi khách bấm thử):

- Cột **Luồng duyệt** — câu chữ một dòng kiểu *Đang ở chặng 1/2 · Dego Admin*
  — nay **không tab nào bày ra**. Hai tab *Đơn của tôi* / *Tôi đã duyệt* bỏ hẳn;
  tab *Cần tôi duyệt* giữ nhưng **ẩn sẵn**, bật lại ở menu **Cột**. Với người
  nộp thì cột *Trạng thái* ngay bên cạnh đã trả lời đúng câu họ hỏi (*đơn của tôi
  tới đâu rồi*); tên từng chặng và ai đang cầm là việc của người duyệt.
  ⚠️ Câu tóm tắt đó **vẫn sống** ở màn chi tiết đơn và ở bản in, và vẫn do
  **backend** dựng (`approval/steps_service._summary`) — đừng xóa hàm đó, cũng
  đừng chép luật dựng câu sang TypeScript.
- Cột **Việc của tôi** ở tab *Cần tôi duyệt* — **bỏ hẳn**. Cột **Hạn xử lý** rút
  về ngày giờ trần.

⚠️ **Hai tín hiệu mất theo hai cột đó. Ghi ra đây để lần sau không ai tưởng là
sót:**

1. Dấu **Quá hạn**. Cờ `task.is_overdue` backend **vẫn gửi và vẫn đúng**, chỉ
   là màn hình thôi không vẽ. Muốn bày lại thì đọc cờ đó, đừng tự so ngày ở tầng
   giao diện.
2. Dòng **Bấm thay ‹tên›** — báo cho người được ủy quyền biết họ đang ký **thay
   mặt người khác**. Nay không còn chỗ nào trên màn danh sách; họ chỉ biết khi mở
   chi tiết đơn. Đây là tín hiệu **trách nhiệm** (chữ ký đi vào dấu vết mang cả
   hai tên), không phải trang trí — cần bày lại thì gắn vào cột **Số đơn** hoặc
   **Người nghỉ**, đừng dựng lại cả một cột cho một dòng chữ hiếm khi có.

⚠️ **Ẩn sẵn (`defaultHidden`) KHÔNG áp cho người đã từng đụng menu "Cột"** của
bảng đó: bảng nhớ bố cục trong `localStorage`, có bản lưu là bản đó thắng. Muốn
thấy đúng mặc định mới thì xóa khóa `erp.table.hr.leave-to-approve`.

## 9. Phân quyền — sáu khóa, đừng gộp

| Khóa | Màn |
|---|---|
| `leave_request` | Đơn nghỉ phép · Lịch nghỉ |
| `leave_comp_request` (nhãn *Nghỉ phép › Phiếu nghỉ bù*, duoc-CR-715) | Nghỉ bù |
| `leave_encashment` (nhãn *Nghỉ phép › Thanh toán nghỉ phép*, duoc-CR-719) | Thanh toán nghỉ phép · kèm chốt xem YCTT nguồn nghỉ phép (§16.4) |
| `leave_balance` | Quỹ phép năm · Phân bổ chính sách (duoc-CR-717) |
| `leave_type` | Loại nghỉ (kèm bậc thâm niên, hạn mức theo nhóm) · Ngày cấm nghỉ · Chính sách nghỉ phép (duoc-CR-717) |
| `holiday` | Lịch ngày lễ |

`leave_comp_request` tách riêng vì duyệt phiếu = **tạo thêm ngày phép**; vì cùng lý do, phiếu nghỉ bù luôn chặn tự
duyệt (§13.6). Ngày cấm nghỉ dùng chung `leave_type` (cùng người khai danh mục, luật **một khóa = một màn hình** được
nới vì đây là một thẻ trong cùng mục *Thiết lập*). Chính sách nghỉ phép và phân bổ chính sách (duoc-CR-717, D4) cũng
**không thêm khóa**: chính sách theo `leave_type`, phân bổ theo `leave_balance` — ENTITIES, `SCOPE_FIELDS` và seed giữ
nguyên, nên hệ đang chạy không phải tick thêm gì.

Tách bốn vì **`leave_balance` ghi được nghĩa là tặng thêm ngày phép cho bất kỳ ai**.
Gộp chung với `leave_request` thì cho ai xem đơn của mình là cho họ tự cộng phép.

**Phạm vi dữ liệu**: `leave_request` khai **cả `owner` lẫn `self`** — điểm khác mọi
entity khác. Một tờ đơn có hai người dính tới nó, người **lập** (`created_by`) và
người **nghỉ** (`employee_id`), cả hai phải thấy nó ở phạm vi **của mình**.
`leave_balance` chỉ khai `self` (người cấp phát là Nhân sự, lấy đó làm "của mình"
thì nhân viên không thấy quỹ của chính họ). Hai danh mục khai `PUBLIC`.

`leave_comp_request` khai **cả `owner` (`created_by`) lẫn `self` (`employee_id`)** như `leave_request`, chặn
`employee_id = 0`. Người đang có việc duyệt trên phiếu đọc được phiếu dù ngoài phạm vi (cùng luật CR-260).

`leave_encashment` (duoc-CR-719) khai cùng khuôn: `company_id`, `department_id`, `owner` = `created_by`, `self` =
`employee_id`. Khóa này còn gác **ai thấy YCTT nguồn nghỉ phép** bên Tài chính và cần tick tay trên hệ đang chạy — xem
§16.4, §16.5.

**Vai trò mẫu `hr_leave`** — Nhân sự quản lý nghỉ phép, có đủ năm khóa. Không gán
tự động cho ai. Seed (`app/seed.py`) cấp `leave_comp_request` phạm vi **của mình** cho mọi vai trò, trưởng bộ phận
thêm `approve` phạm vi phòng, trưởng công ty phạm vi công ty; khóa này nằm trong `_SYS_ENTITIES` nên Quản lý thu mua
không tự có.

⚠️ **Trên hệ ĐANG CHẠY, vai trò cũ không tự có các khóa này** (kể cả `leave_comp_request` mới thêm 02/11/2026).
Seed cố ý không ghi đè phân quyền đã chỉnh tay (D-018), nên quản trị phải tick thêm ở
*Quản trị ▸ Phân quyền tài khoản*, hoặc chạy một lần với `SEED_FORCE_SYNC=true` rồi trả về `false`.
Người dùng báo "không thấy menu Nghỉ phép" thì gần như chắc là chỗ này.

## 10. Những thứ CHƯA có

| Thiếu | Ghi chú |
|---|---|
| ~~Nghỉ **nửa ngày / theo giờ**~~ | **ĐÃ CÓ 07/09/2026** — nửa ngày qua hai ô buổi (§6), theo giờ qua buổi thứ tư *Theo giờ* (§7). Cột `unit` vẫn chỉ dùng giá trị *Ngày*: số giờ được **quy đổi ra ngày**, không lưu thành đơn vị riêng |
| ~~**Đính kèm** trên đơn~~ | **ĐÃ CÓ 28/09/2026** (bao-CR-505, §7.2). Cờ `require_attachment` được ép lúc GỬI DUYỆT từ 22/10/2026 (duoc-CR-661, §7.2) |
| ~~Danh sách **bàn giao** trên giao diện~~ | **ĐÃ CÓ** — ô nhập `leave-handover-editor.tsx` trên form đơn (đối chiếu 01/10/2026) |
| ~~**Chuyển phép sang năm sau**~~ | **ĐÃ CÓ 07/09/2026** — ba nước *mất / mang sang / quy đổi* + nút **Kết sổ cuối năm**, xem §5. Cờ `carry_over` cũ thành di tích (§11.2). **Bảng đối chiếu** trước/sau kết sổ: **ĐÃ CÓ 22/10/2026** (duoc-CR-664, §5) |
| ~~**Báo cáo / thống kê** nghỉ phép~~ | **ĐÃ CÓ 01/10/2026** (duoc-CR-548) — phân hệ Báo cáo: **Tình hình nghỉ phép** và **Quỹ phép năm** |
| ~~Cấp quỹ **theo tỷ lệ** người vào làm giữa năm / **cộng dần** / hạn mức **theo nhóm** / **dùng sau N ngày** / **ứng phép**~~ | **ĐÃ CÓ 02/11/2026** (duoc-CR-715, §13.1–13.4) |
| ~~**Ngày cấm nghỉ** (Leave Block List)~~ | **ĐÃ CÓ 02/11/2026** (duoc-CR-715, §13.5) |
| ~~**Phiếu xin nghỉ bù** (Compensatory Leave Request)~~ | **ĐÃ CÓ 02/11/2026** (duoc-CR-715, §13.6) |
| ~~Chặn đơn **lùi ngày** · chặn **tự duyệt** bước khai đích danh~~ | **ĐÃ CÓ 02/11/2026** (duoc-CR-713, §14) |
| ~~**Chính sách nghỉ phép** + **phân bổ** (Leave Policy / Leave Policy Assignment / Leave Control Panel)~~ | **ĐÃ CÓ 03/11/2026** (duoc-CR-717, §15.1–15.5) |
| ~~Báo cáo **làm việc ngày lễ** (Employees working on a holiday) · quỹ **tổng hợp theo người** (Leave Balance Summary)~~ | **ĐÃ CÓ 03/11/2026** (duoc-CR-717, §15.6, §15.8) |
| **Kỳ nghỉ phép** (Leave Period) | **Không làm** — anh Được bỏ 03/11/2026; quỹ giữ theo năm dương lịch |
| ~~Quy đổi phép dư ra tiền (Leave Encashment)~~ | **ĐÃ CÓ 03/11/2026** (duoc-CR-719, §16) — phiếu ghi số ngày, duyệt trừ quỹ và sinh YCTT cho kế toán nhập tiền |
| Sổ **công nợ phép** khi ứng phép | Chưa có, chưa có yêu cầu. Ứng phép chỉ hiện số âm ở *Còn lại* |
| Nạp `hire_date` cho hồ sơ cũ | **Ô nhập đã có từ 07/09/2026** ở *Nhân sự ▸ chi tiết hồ sơ* (kèm ô *Giới tính*) — trước đó hai cột này có trong bảng nhưng không schema nào khai, nên không màn nào nhập được và thâm niên của cả công ty tính bằng 0. Việc còn lại là **nhập bù dữ liệu**, không phải dựng màn |

## 11. Danh mục **Loại nghỉ** — từng trường

`/hr/leave-types` (danh sách) · `/hr/leave-types/new` (thêm) · `/hr/leave-types/:id`
(sửa, tab *Thông tin* · *Bậc thâm niên* · *Hạn mức theo nhóm*; hai tab sau chỉ hiện khi bản ghi đã tạo). Dựng bằng khung CRUD khai báo — mọi thứ dưới đây
khai ở **một chỗ**: `frontend-v2/src/modules/hr/config/leave-type-crud.tsx`.
Bảng: `tab_leave_type` (`leave/catalog_model.py`).

Form thêm/sửa **dài nên đi trang riêng, không hộp thoại**, và chia **ba cụm** —
người khai danh mục là nhân sự, không phải người viết luật, mà ở màn này đoán sai
quan hệ giữa hai ô là khai sai luật nghỉ cho **cả công ty**.

**Bố cục phẳng kiểu ERPNext (duoc-CR-716, 03/11/2026)** — `LEAVE_TYPE_CRUD_CONFIG.detailLayout = 'flat'`
(`shared/crud/crud-detail-flat-layout.tsx`): một mặt phẳng trắng tràn khung, hàng tiêu đề **dính** (mũi tên lùi · tên ·
nhãn trạng thái/mã · nút *Lưu* — lúc thêm là *Tạo loại nghỉ* — và *Xóa*), dải tab gạch chân, ba cụm thành dải ngăn bằng
đường kẻ **gập / mở được** (nhớ trạng thái ở `erp.section.crud.leave_type.*`), chú thích ô thu vào nút **(i)** cạnh
nhãn, công tắc thành dòng gọn không viền, lưới ô 3 cột khi đủ rộng. Khối **Hoạt động** (`AuditActivityFeed`) là nhóm cuối
của tab *Thông tin*. Tab *Bậc thâm niên* / *Hạn mức theo nhóm* tự làm phẳng thẻ con bằng `ERP_FLATTEN_CARDS`. Hộp thoại
thêm nhanh và mọi màn CRUD khác vẫn bố cục thẻ (`'card'`, mặc định).

### 11.1. Các trường có trên form

| Ô | Cột | Kiểu | Mặc định | Ghi chú |
|---|---|---|---|---|
| **Mã loại nghỉ** | `code` | chữ | — | ⚠️ **KHÓA sau khi tạo** (`readonlyOnEdit` + backend chặn lớp hai): mã này đi vào metadata mọi giấy GNP đã phát hành. Phải khớp `core/leave_codes.LEAVE_TYPE_SET` |
| **Tên loại nghỉ** | `name` | chữ | — | Bắt buộc |
| *Cụm **Quỹ phép và lương*** | | | | |
| Trừ vào quỹ phép năm | `counts_balance` | công tắc | Tắt | Bật thì nộp đơn **bị chặn khi hết phép** — trừ phần **Cho ứng phép tối đa**. Đứng **đầu cụm, cột trái** vì nó mở ra ô hạn mức ngay bên dưới |
| Có hưởng lương | `is_paid` | công tắc | Bật | Tách khỏi `counts_balance`: cưới hỏi vẫn hưởng lương nhưng không ăn vào phép năm |
| Hạn mức mỗi năm (ngày) | `annual_quota_days` | số | 0 | **Chỉ hiện khi** **Trừ vào quỹ phép năm** bật. Bậc thâm niên cộng thêm khai ở tab riêng; mức riêng theo nhóm ở tab *Hạn mức theo nhóm* (§13.2) |
| Cách cấp quỹ | `accrual_mode` | chọn | Đủ hạn mức đầu năm (`1`) | **Chỉ hiện khi** có trừ quỹ. `1` Đủ hạn mức đầu năm · `2` Theo tỷ lệ tháng làm việc (người vào làm trong năm) · `3` Cộng dần theo tháng — §13.1 |
| Cho ứng phép tối đa (ngày) | `max_negative_days` | số | 0 | **Chỉ hiện khi** có trừ quỹ. 0–30; `0` = không cho ứng — §13.4 |
| Loại nhận ngày nghỉ bù | `is_compensatory` | công tắc | Tắt | **Chỉ hiện khi** có trừ quỹ. Loại được cộng `comp_days` khi phiếu nghỉ bù duyệt; nhiều loại bật thì lấy `sort_order` nhỏ nhất — §13.6 |
| *Cụm **Điều kiện áp dụng*** | | | | |
| Áp dụng cho giới tính | `gender` | chọn | Mọi giới (`0`) | Hồ sơ **chưa khai** giới tính vẫn nộp được — chặn là khóa cả công ty tới khi Nhân sự nhập bù |
| Tối đa mỗi lần nghỉ (ngày) | `max_days_per_request` | số | 0 | `0` = không giới hạn. Trần của **một đơn**, không dính quỹ năm |
| Dùng được sau (ngày kể từ ngày vào làm) | `applicable_after_days` | số | 0 | 0–3650; `0` = không chặn — §13.3 |
| Trừ ngày nghỉ theo lịch làm việc và ngày lễ | `exclude_holiday` | công tắc | Bật | ⚠️ **Thứ Bảy VẪN tính công** — DEGO làm cả T7 (lịch mặc định T2–T7, CN OFF). Xem [21-lich-lam-viec.md §12.2](03-lich-lam-viec.md) để hiểu khi nào tắt cửa này. |
| Bắt buộc đính kèm | `require_attachment` | công tắc | Tắt | Bật lên thì đơn thiếu tệp bị chặn **lúc Gửi duyệt**, lưu nháp không chặn (duoc-CR-661, §7.2) |
| *Cụm **Số dư cuối năm*** — xem §5 | | | | |
| Cách xử lý số dư | `year_end_mode` | chọn | Hết năm là mất (`0`) | Ba nước loại trừ nhau nên là ô chọn, không phải hai công tắc |
| Hạn dùng phép mang sang | `carry_over_expire_month` | chọn 13 mục | Đến hết tháng 3 năm sau | **Chỉ hiện khi** **Mang sang năm sau**. `0` = không hết hạn. Ô CHỌN chứ không phải ô gõ số: hạn này **lặp mỗi năm** nên không chốt cứng được thành một cặp ngày, mà tháng 2 còn nhảy 28/29 |
| Loại nghỉ nhận số ngày | `convert_to_type_id` | chọn (nạp từ API) | 0 | **Chỉ hiện khi** **Quy đổi**. Phải khác chính nó và phải bật **Trừ vào quỹ phép năm** — backend chặn **ngay lúc lưu** |
| Tỷ lệ quy đổi | `convert_ratio` | số | 1 | **Chỉ hiện khi** **Quy đổi**. 1 ngày dư đổi được mấy ngày ở loại nhận; hai đổi một thì ghi `0.5`. Phải > 0 |
| *Cụm **Thanh toán nghỉ phép*** — xem §16 (duoc-CR-719, `hr/config/leave-type-encashment-fields.ts`) | | | | |
| Cho phép thanh toán nghỉ phép | `allow_encashment` | công tắc | Tắt | **Luôn hiện** (cố ý không `showWhen`: khung CRUD vẫn gửi giá trị ô ẩn, ẩn công tắc khi tắt trừ quỹ thì `true` cũ đi lên ăn 422 mà hết chỗ gạt về). Bật mà `counts_balance` tắt → 422 lúc tạo / sửa. Danh sách Loại nghỉ hiện nhãn **Cho thanh toán nghỉ phép** |
| Tối đa mỗi năm (ngày) | `max_encashable_days` | số | 0 | **Chỉ hiện khi** trừ quỹ + bật thanh toán. Trần THEO NĂM quỹ, cộng dồn `encashed_days` của dòng; `0` = không trần; 0–366. Lý do Nghỉ việc bỏ qua |
| Số ngày phải giữ lại | `non_encashable_days` | số | 0 | **Chỉ hiện khi** trừ quỹ + bật thanh toán. Chỉ trừ ở lý do Phép dư cuối năm; 0–366 |
| **Ghi chú** | `note` | nhiều dòng | rỗng | |
| **Đang dùng** | `is_active` | công tắc | Bật | Tắt = ẩn khỏi ô chọn; đơn cũ giữ nguyên |

⚠️ **Ẩn/hiện chỉ là chuyện HIỂN THỊ** (`showWhen`) — giá trị vẫn nằm trong form và
vẫn gửi lên. Luật thật nằm ở backend.

### 11.2. Cột CÓ trong bảng nhưng KHÔNG hỏi trên form

| Cột | Vì sao |
|---|---|
| `carry_over_max_days` | Trần số ngày mỗi người được chuyển. **Bỏ khỏi form 07/09/2026**: DEGO không có luật trần (dư bao nhiêu mang hết bấy nhiêu), mà ô đó đứng cạnh chữ *số dư* thì đọc mãi vẫn ra "số dư của người này" — trong khi số dư do `balance_service.remaining()` tính, không ai gõ tay. `0` = không giới hạn, và mọi loại đang là `0`. Khai lại ô này nếu công ty đặt trần thật |
| `sort_order` | **Bỏ khỏi form 07/09/2026** — bộ loại nghỉ hơn chục dòng, thứ tự đã seed sẵn; bắt người khai nghĩ ra một con số xếp hạng là hỏi một câu họ không có câu trả lời. Backend vẫn xếp theo nó |
| `carry_over` (bool) | **Di tích.** Công tắc hai nước, đã thay bằng `year_end_mode` (07/09/2026) vì nó không nói được nước thứ ba — *quy đổi*. Đừng đọc, đừng ghi |
| `min_notice_days` | **Di tích.** Luật "phải nộp trước N ngày" đã bỏ 05/09/2026, không còn trong schema lẫn form |

### 11.3. Mười ba loại nghỉ seed sẵn

`app/seed_nghi_phep.py` — chỉ **THÊM** loại còn thiếu, loại đã có thì không đụng
vào (người ta đã sửa). Chạy tay: `docker compose exec api python -m app.seed_nghi_phep`.

| Mã | Tên | Lương | Trừ quỹ | Hạn mức | Trần/lần | Giới tính | Đính kèm | Trừ CN+lễ |
|---|---|---|---|---|---|---|---|---|
| `annual` | Phép năm | ✔ | ✔ | 12 | — | mọi | — | ✔ |
| `unpaid` | Nghỉ không lương | — | — | — | — | mọi | — | ✔ |
| `sick` | Nghỉ ốm đau | ✔ | — | — | — | mọi | ✔ | ✔ |
| `maternity` | Nghỉ thai sản | ✔ | — | — | — | **nữ** | ✔ | **—** |
| `paternity` | Nghỉ vợ sinh con | ✔ | — | — | **14** | **nam** | ✔ | ✔ |
| `wedding` | Nghỉ cưới hỏi | ✔ | — | — | 3 | mọi | — | ✔ |
| `funeral` | Nghỉ tang chế | ✔ | — | — | 3 | mọi | — | ✔ |
| `comp_off` | Nghỉ bù | ✔ | — | — | — | mọi | — | ✔ |
| `child_sick` | Nghỉ chăm con ốm | ✔ (BHXH) | — | — | **20** | mọi | ✔ | ✔ |
| `recuperation` | Nghỉ dưỡng sức phục hồi sức khỏe | ✔ (BHXH) | — | — | **10** | mọi | — | **—** |
| `prenatal` | Nghỉ khám thai | ✔ (BHXH) | — | — | **2** | **nữ** | ✔ | ✔ |
| `miscarriage` | Nghỉ sảy thai, phá thai | ✔ (BHXH) | — | — | **50** | **nữ** | ✔ | **—** |
| `contraception` | Nghỉ thực hiện biện pháp tránh thai | ✔ (BHXH) | — | — | **15** | mọi | ✔ | **—** |

⚠️ **Nghỉ vợ sinh con** (07/09/2026): trần **14** là mức **cao nhất** của luật
(sinh đôi trở lên, mổ); mức thường là 5, mổ là 7. Máy không biết ca nào nên chỉ
chặn trần — **người duyệt canh phần còn lại**.

⚠️ **Năm loại chế độ BHXH** (bao-CR-708, 02/11/2026): tách khỏi `sick` / `maternity` vì khác nhau ở giới
tính, trần ngày và cách tính ngày lễ. "Lương ✔ (BHXH)" nghĩa là người nghỉ có tiền thay lương nhưng **BHXH
chi trả, không phải công ty**. Mức luật (Luật BHXH 2024, hiệu lực 01/07/2025) ghi ở cột `note` của từng loại:
khám thai 5 lần × tối đa 2 ngày (Đ.51); sảy thai 10/20/40/50 ngày theo tuổi thai, tính cả lễ (Đ.52); tránh thai
7 ngày đặt vòng / 15 ngày triệt sản (Đ.57); chăm con ốm 20 ngày làm việc/năm con dưới 3 tuổi, 15 ngày con 3–7
tuổi; dưỡng sức 5–10 ngày, tính cả lễ. Máy chỉ chặn trần mỗi lần — người duyệt đối chiếu giấy tờ. Bản in đơn
đánh ô *Nghỉ chế độ bảo hiểm* theo tên loại (`leave-print-category.ts`, thêm từ khóa *tránh thai*).

### 11.4. Bậc thâm niên (tab riêng)

`tab_leave_type_seniority`, mỗi dòng là *từ năm thứ A đến dưới năm thứ B: +N ngày*.
`B = 0` là bậc cuối, không có trần trên. Khoảng **nửa mở**: khớp khi
`A <= thâm niên < B`. Lấy **bậc cao nhất khớp được, KHÔNG cộng dồn**.

## 12. Tra cứu nhanh

| Cần gì | Ở đâu |
|---|---|
| Khoảng ngày của đơn (chuẩn hóa · luật · ghi · chốt trùng) | `backend/app/modules/leave/request_periods.py` |
| Đọc **ngày D có nghỉ không** (`LeaveSpan`, OUTER JOIN) | `backend/app/modules/leave/period_spans.py` |
| Luật bảng dòng loại nghỉ | `backend/app/modules/leave/request_service.py` — `collect_lines` · `resolve_days` · `check_lines` |
| Bảng dòng trên giao diện | `frontend-v2/src/modules/hr/components/leave-request-lines-editor.tsx` |
| Bộ mã số (trạng thái, buổi, đơn vị, giới tính) | `backend/app/modules/leave/constants.py` |
| Công thức đếm ngày công | `backend/app/modules/leave/workday_service.py` |
| Sổ quỹ (bốn nhịp) | `backend/app/modules/leave/balance_service.py` |
| Kết sổ cuối năm · hết hạn phép mang sang | `backend/app/modules/leave/carryover_service.py` — `close_year` · `expire_carried` |
| Khai báo màn **Loại nghỉ** (toàn bộ trường) | `frontend-v2/src/modules/hr/config/leave-type-crud.tsx` |
| Luật trên tờ đơn | `backend/app/modules/leave/request_service.py` |
| Nối bộ máy duyệt + sinh giấy GNP | `backend/app/modules/leave/approval_bridge.py` |
| Seed loại nghỉ · ngày lễ · luồng | `backend/app/seed_nghi_phep.py` |
| Bộ mã CHUỖI của giấy GNP | `backend/app/core/leave_codes.py` |
| Giao diện | `frontend-v2/src/modules/hr/` (`pages/leave-*`, `components/leave-*`) |
| Gói tri thức Trợ lý AI | `backend/app/modules/assistant/packs/40-nghi-phep.md` |
| Hai tool Trợ lý AI đọc/soạn nghỉ phép | `assistant/tools/leave_tool.py` (`my_leave_summary`, bao-CR-386) · `assistant/tools/draft_tool.py` → `_run_leave` (`draft_leave_request`, bao-CR-387). ⚠️ `draft_leave_request` **chỉ soạn nháp**, không ghi DB, và **không mang `employee_id`** để không mở đường nộp đơn hộ người khác qua chat. Nó gác `leave_request.create` — trước 12/09/2026 gác nhầm `document.create` vì bản đầu soạn **văn bản GNP ở Văn thư**, thứ mà `approval_bridge` vốn tự sinh sau khi duyệt |
| Cấp quỹ: chọn hạn mức theo nhóm · tỷ lệ · cộng dần · chốt **dùng sau N ngày** | `backend/app/modules/leave/accrual_service.py` — `resolve_quota` · `prorate_allocation` · `accrual_holdback` · `ensure_applicable` |
| Ngày cấm nghỉ (tìm xung đột · chốt duyệt) | `backend/app/modules/leave/block_period_service.py` — `find_conflicts` · `ensure_approvable` |
| Phiếu nghỉ bù | `backend/app/modules/leave/comp_request_{model,schema,service,controller}.py` · `comp_approval_bridge.py` |
| Chặn đơn lùi ngày (Cài đặt nhân sự) | `backend/app/modules/leave/leave_policy.py` — `ensure_not_backdated` |
| Chặn tự duyệt | `backend/app/modules/approval/self_approval_policy.py` (`ALWAYS_STRICT_ENTITIES`, `strict_self_exclusion`) |
| Lỗi hook được ném tiếp | `backend/app/modules/approval/entity_hooks.py` — `HookVeto` |
| Giao diện CR-715 | `frontend-v2/src/modules/hr/`: `components/leave-type-quota-card.tsx`, `config/leave-block-crud.tsx`, `pages/leave-block-*`, `components/leave-block-warning-banner.tsx`, `pages/leave-comp-request-*`, `components/leave-comp-*`, `hooks/use-single-flight.ts` |
| HDSD cho người dùng (Help Center) | `backend/scripts/seed_help_nghi_phep.py` — **12 bài** (bản 6, 03/11/2026; ban đầu 10 bài, bản 2 04/09/2026), chạy `docker compose exec -T api python scripts/seed_help_nghi_phep.py`. Nội dung nằm trong DB **từng môi trường**, chạy script ở môi trường đích thì mới có |
| Bài kiểm | `test/backend/test_nghi_phep_*.py` (CR-715: `test_nghi_phep_cap_quy_cr715.py`, `test_nghi_phep_ngay_cam_cr715.py`, `test_nghi_phep_nghi_bu_cr715.py`, `test_nghi_phep_review_cr715.py`) · `frontend-v2/src/modules/hr/**/leave-*.test.*` |

## 13. Nghỉ phép kiểu ERPNext (duoc-CR-715, 02/11/2026)

Mang năm chức năng nghỉ phép của ERPNext (hrms) sang. Đối chiếu nguồn ở
[`doc/erp/nghien-cuu/erpnext/04-hrms-chuc-nang-va-lien-ket.md`](../nghien-cuu/erpnext/04-hrms-chuc-nang-va-lien-ket.md) §4;
kế hoạch + báo cáo từng giai đoạn ở `doc/erp/hrm/plans/261102-nghi-phep-kieu-erpnext-duoc-cr-715/`. **Luật chung: mọi cột / công tắc mới
mặc định = hành vi cũ** — bật tính năng mới là việc của quản trị. Chuỗi migration: `lvacc715` (down `jobrun01`) →
`lvblk715` → `lvcmp715` → `lvcmp716` (lượt rà mã), cả bốn viết tay, chạy lại được. Bộ mã số mới (R2/QĐ-11) ở
`leave/constants.py`, bản TS gõ tay ở `hr/types/leave.ts` và `hr/types/leave-comp.ts`.

### 13.1. Cách cấp quỹ — `tab_leave_type.accrual_mode` (SMALLINT, `LeaveAccrualMode`)

| Mã | Nhãn trên form | Luật |
|---|---|---|
| `1` FULL_YEAR | Đủ hạn mức đầu năm | Như cũ: ai cũng nhận đủ hạn mức (mặc định) |
| `2` PRORATA_HIRE | Theo tỷ lệ tháng làm việc (người vào làm trong năm) | Người vào làm TRONG năm: `hạn mức × số tháng làm / 12` (Điều 113 khoản 2 BLLĐ 2019). Ngày vào làm 1–15 tính cả tháng đó, từ 16 tính từ tháng sau; làm tròn **lên** tới 0,5. Vào làm trước năm đó hoặc chưa có `hire_date` → đủ; vào làm năm SAU → 0 |
| `3` MONTHLY | Cộng dần theo tháng | `allocated_days` vẫn ghi CẢ NĂM (đã tỷ lệ như mã 2) để báo cáo đọc đúng; phần chưa tới tháng trừ động ở `accrual_holdback`: dùng được = `allocated × số tháng đã tới (tính cả tháng hiện tại) / số tháng của kỳ`, làm tròn **xuống** 0,5. Năm đã qua → đủ |

Ví dụ hạn mức 12: vào làm 10/03 → 10 ngày; vào làm 20/03 → 9 ngày; loại cộng dần, đang tháng 5 → dùng được 5 ngày.
Thâm niên, phép mang sang, điều chỉnh tay và `comp_days` **không** tỷ lệ, **không** cộng dần.

⚠️ Quỹ ĐÃ CẤP không tính lại khi đổi `accrual_mode` hay hạn mức (luật cũ của `allocate`) — **trừ** mã 3, vì phần chưa
tới tháng tính động. Lời giải thích của ô trên form nói đúng điều này.

### 13.2. Hạn mức theo nhóm — `tab_leave_type_quota`

`(id, leave_type_id, basis SMALLINT, basis_value SMALLINT, quota_days FLOAT, audit)`, UNIQUE
`(leave_type_id, basis, basis_value)`. `basis`: `1` hình thức nhân viên (`Employee.employment_type`), `2` cấp bậc
(`Employee.job_level`) — bộ mã của hồ sơ ở `employee/constants.py`. Thứ tự áp lúc cấp (`accrual_service.resolve_quota`):
khớp hình thức nhân viên → khớp cấp bậc → `annual_quota_days`.

API thay-cả-danh-sách: `GET /api/leave-types/{id}/quotas` (gác `leave_type.read`) · `PUT /api/leave-types/{id}/quotas`
(gác `leave_type.write`), trần 50 dòng. Giao diện: tab *Hạn mức theo nhóm* (`components/leave-type-quota-card.tsx`) —
ô *Theo* · *Nhóm* · *Số ngày mỗi năm*, nút *Thêm dòng* (trùng nhóm thì ghi đè), *Lưu hạn mức* gửi cả danh sách.

### 13.3. Dùng được sau N ngày vào làm — `tab_leave_type.applicable_after_days`

INT 0–3650, mặc định 0 = không chặn. Ngày bắt đầu của khoảng sớm nhất có dòng loại đó < `hire_date + N` → 422
*Loại nghỉ "X" chỉ dùng được sau N ngày vào làm (từ dd/mm/yyyy).* (`accrual_service.ensure_applicable`). Kiểm ở **lập**,
**sửa** (khi ngày hoặc dòng loại đổi) và **gửi duyệt**. Không có `hire_date` → không chặn.

### 13.4. Ứng phép — `tab_leave_type.max_negative_days`

FLOAT 0–30, mặc định 0. `check_enough*` cho số dùng được xuống tới `−N`; loại `counts_balance = False` không bị ảnh
hưởng. `/api/leave-requests/tools/my-balance` trả kèm `max_negative_days` để hộp gợi ý trên form chỉ cảnh báo khi vượt
cả phần được ứng (client cũ không đọc trường này thì coi là 0). Xem §5.

### 13.5. Ngày cấm nghỉ — `tab_leave_block_period` (Leave Block List)

`(id, company_id, department_id, from_date, to_date, reason String(255), is_active, audit)`; `0` ở pháp nhân / phòng ban
= mọi nơi. Một khoảng dài tối đa 366 ngày, năm 2000–2100. CRUD khai báo (`config/leave-block-crud.tsx`,
`block_period_router` ở `catalog_controller.py`), khóa `leave_type`; màn `/hr/leave-blocks` là thẻ thứ ba của *Thiết lập*.

| Nhịp | Hệ làm gì |
|---|---|
| Lập · sửa · gửi duyệt | **Không chặn.** `find_conflicts` (một truy vấn) trả `block_conflicts` trong `/tools/estimate-days`, `/tools/estimate-periods` và trang chi tiết đơn (không có ở danh sách — tránh N+1; bỏ qua với đơn từ chối / hủy). Giao diện hiện khung vàng *Đơn nghỉ này rơi vào ngày cấm nghỉ.* (`leave-block-warning-banner.tsx`) |
| Duyệt chặng cuối · duyệt thẳng | `approval_bridge._on_approved` gọi `block_period_service.ensure_approvable` **trước** khi trừ quỹ: còn xung đột mà người bấm không phải `admin` và không có vai trò trong `leave_block_exempt_roles` (§14) → `HookVeto` 422 *Đơn nghỉ này rơi vào ngày cấm nghỉ: … Chưa duyệt được — …*. Đơn ở nguyên Chờ duyệt, quỹ giữ chỗ nguyên |

Khớp theo **người nghỉ** (pháp nhân / phòng của họ), không theo người lập hộ. Đơn nhiều khoảng đọc qua `period_spans`:
KHE giữa các khoảng không dính. Thêm / tắt một khoảng cấm không đổi đơn đã duyệt.

⚠️ **`HookVeto`** (`approval/entity_hooks.py`, lớp con của `HTTPException`) là loại lỗi hook **duy nhất** `fire` ném
tiếp — mọi lỗi hook khác vẫn bị nuốt và ghi `finish_reason` như cũ. Hook nào ném nó phải ném **trước** khi đổi gì của
chứng từ; đường duyệt không được commit trước lúc `fire`. Sau lượt rà mã, `fire` **tự `db.rollback()`** trước khi ném,
nên nơi gọi bắt lỗi rồi commit (cổng MCP ghi nhật ký) không thể lưu nửa lượt duyệt.

### 13.6. Phiếu xin nghỉ bù — `tab_leave_comp_request` (Compensatory Leave Request)

Nhân sự đi làm vào ngày lễ hoặc ngày nghỉ theo lịch làm việc thì lập phiếu; duyệt xong cộng ngày vào quỹ. Giao diện
mục *Nghỉ bù* (`/hr/leave-comp-requests`, `/new`, `/:id`); bài HDSD *Xin nghỉ bù*.

**Bảng** `(id, code **NB…**, company_id, department_id, employee_id, work_date, days FLOAT 0.5|1, reason String(1000),
status SMALLINT, approval_instance_id, decided_at, decision_note, comp_leave_type_id, balance_year, active_key String(40)
UNIQUE NULL, created_by, …)`. Thêm cột `tab_leave_balance.comp_days` và cờ `tab_leave_type.is_compensatory`.

**Trạng thái** (`LeaveCompStatus`, cùng số với đơn nghỉ): `1` Nháp · `2` Chờ duyệt · `3` Đã duyệt · `4` Từ chối ·
`5` Trả về chỉnh sửa · `6` Đã hủy. Sửa / gửi được ở 1 và 5; xóa mềm chỉ ở 1.

**API** `/api/leave-comp-requests` (khóa `leave_comp_request`, phong bì chuẩn): `GET /` (lọc `status`, `employee_id`,
`company_id`, `department_id`, `q`) · `GET /to-approve` · `GET /{id}` · `POST /` · `PATCH /{id}` · `DELETE /{id}` ·
`POST /{id}/submit` · `POST /{id}/approve` · `POST /{id}/reject?reason=` · `POST /{id}/cancel?reason=`. Gửi duyệt: bật
bộ máy duyệt cho *Phiếu nghỉ bù* thì trình luồng; không thì `approval_instance_id = 0` và người có `approve` duyệt thẳng.

**Luật lập / gửi** (`comp_request_service`):
- `work_date ≤ vn_today()` và `≥ 01/01 của năm trước` (năm kết sổ từ lâu không nhận thêm ngày bù); schema chặn năm
  ngoài 2000–2100.
- Phải là ngày lễ HOẶC ngày nghỉ theo lịch làm việc của người đó (`workday_service.count_leave_days(..., employee=)` = 0;
  nửa ngày làm, ví dụ sáng thứ Bảy, vẫn là ngày làm việc).
- Một ngày một phiếu còn hiệu lực (Nháp / Chờ duyệt / Đã duyệt / Trả về) → 409. Giữ bằng cả câu kiểm lẫn khóa UNIQUE
  `active_key = "{employee_id}:{work_date}"` (NULL khi Từ chối / Đã hủy / xóa) — hai lượt chèn cùng lúc thì lượt sau
  thua ở khóa → 409.
- Lý do bắt buộc lúc gửi; `days ∈ {0.5, 1}`; chưa có loại `is_compensatory` đang dùng + có trừ quỹ → 422.

**Luật duyệt / hủy (sau lượt rà mã, `lvcmp716`)**:
- **Đích cộng lưu sẵn trên phiếu**: `comp_leave_type_id` chốt lúc GỬI; `balance_year = max(năm của work_date, năm nay)`
  chốt lúc DUYỆT (ngày đi làm thuộc năm trước thì cộng vào quỹ năm nay vì quỹ năm cũ đã kết sổ). Duyệt / hủy chỉ dùng hai
  cột này, **không** gọi lại `get_comp_type()` — HR đổi cờ giữa chừng không làm ngày bù rơi sang loại khác. Loại đã chốt
  không còn hợp lệ lúc duyệt qua bộ máy → `HookVeto` 422.
- **Mọi đổi trạng thái đi qua `claim`**: `UPDATE … SET status=… WHERE id AND status IN (expected)`, đếm dòng; thua → 409
  *Phiếu vừa được xử lý bởi lượt khác — tải lại trang*. Áp cho gửi, duyệt thẳng, từ chối, hủy (chiếm trước rồi mới trừ quỹ,
  trừ hỏng thì rollback), sửa, xóa, hook bộ máy. Giao diện chặn bấm đúp bằng `useSingleFlight` (`useRef`).
- **Luôn chặn tự duyệt**: `self_approval_policy.ALWAYS_STRICT_ENTITIES = {"leave_comp_request"}` — gạt người nghỉ ở mọi
  kiểu bước (kể cả khai đích danh, người dự phòng) và chặn duyệt thẳng 403 *Bạn không được tự duyệt phiếu nghỉ bù của
  chính mình.*, **bất kể** công tắc `leave_prevent_self_approval` (đơn nghỉ vẫn theo công tắc).
- Duyệt xong: `comp_days += days` ở dòng quỹ (`ensure_balance` tạo nếu chưa có). Hủy phiếu ĐÃ DUYỆT chỉ khi
  `available_days` của dòng đó ≥ `days`, rồi `comp_days −= days`; thiếu → 422 *Không hủy được: ngày nghỉ bù của phiếu này
  (… ngày) đã được dùng để nghỉ…*.

**Hiển thị quỹ**: cột *Nghỉ bù cộng thêm* ở bảng Quỹ phép năm (`defaultHidden`), ô cùng tên ở trang chi tiết dòng quỹ khi
khác 0, thẻ quỹ trên Trang cá nhân ghi `+N nghỉ bù`; `hasQuota` tính cả `comp_days`.

**Thông báo**: `task_notification.ENTITY_LABELS` = **Phiếu nghỉ bù**, `ENTITY_LINKS` = `/hr/leave-comp-requests/{id}`.

### 13.7. Báo cáo và trợ lý AI

Báo cáo **Quỹ phép năm** (`balance_report_spec.rows_of`) trừ phần chưa tới tháng ngay trong câu truy vấn quỹ (OUTER JOIN
`LeaveType.accrual_mode` + `Employee.hire_date`, tính `accrual_holdback` từng dòng bằng Python) — số truy vấn không đổi,
có bài kiểm đếm truy vấn. Số tổng / còn lại của báo cáo gồm cả `comp_days`. Danh sách quỹ, quỹ của tôi và
`assistant/tools/leave_tool.py` đọc `available_days_map`.

Từ duoc-CR-717: báo cáo **Quỹ phép năm** có thêm chỉ số **Nghỉ bù cộng thêm** (`comp`, kind days — cột bảng, totals,
groups, tệp Excel; không thêm truy vấn); bảng quỹ **theo nhân sự** (§15.6) và báo cáo **khóa 30** **Làm việc vào ngày lễ,
ngày nghỉ** (§15.8); `my_leave_summary` trả thêm `policy` và `policy_name` / `policy_annual_days` từng loại (§15.9).

### 13.8. Khóa quyền trên hệ đang chạy (D-018)

Khóa `leave_comp_request` mới: hệ đang chạy **không tự cấp** cho vai trò cũ (seed không ghi đè). Tick ở *Quản trị ▸ Phân
quyền tài khoản* (hr_leave, trưởng bộ phận, trưởng công ty, nhân viên **của mình**), hoặc `SEED_FORCE_SYNC=true` một lần
rồi trả về `false`. Người đang đăng nhập giữ map quyền cũ tới khi đăng xuất / đăng nhập lại. Không có luồng duyệt mẫu
cho *Phiếu nghỉ bù* — quản trị tự bật bộ máy duyệt nếu muốn đi luồng.

## 14. Cài đặt nhân sự — tab Nghỉ phép (duoc-CR-713, 02/11/2026)

Trang `/hr/settings` (menu *Nhân sự ▸ Master ▸ Cài đặt nhân sự*), bố cục HR Settings của ERPNext: dải tab gạch chân
*Nhân viên · Nghỉ phép · Hợp đồng lao động*, nút *Lưu* ở đầu phải dải tab lưu cả ba tab một lần. Gác `setting.read`
(xem) / `setting.write` (sửa); lưu qua `PUT /api/settings` nên ghi chung nhật ký *Lịch sử thay đổi* của Cấu hình hệ
thống; khóa thuộc nhóm `hr` (màn Cấu hình hệ thống không vẽ nhóm này). Bộ đệm cấu hình 30 giây. Tiêu đề trang trùng chữ
cuối của thanh đường dẫn nên chỉ còn `sr-only` (duoc-CR-714). Tab *Nhân viên* / *Hợp đồng lao động*: xem
[01-ho-so-nhan-su.md §7.17](01-ho-so-nhan-su.md) và [04-hop-dong-lao-dong.md §A.8](04-hop-dong-lao-dong.md).

| Khóa | Nhãn trên màn | Kiểu · mặc định | Đọc ở đâu |
|---|---|---|---|
| `leave_restrict_backdated` | Chặn đơn nghỉ lùi ngày | công tắc · TẮT | `leave/leave_policy.ensure_not_backdated` — gọi ở ĐỦ ba nhịp `create` · `update` · `prepare_submit` (nháp hợp lệ để qua ngày mới gửi cũng là lùi ngày). **Hôm nay** = `vn_today()`. 422 *Không lập được đơn nghỉ cho ngày đã qua (dd/mm/yyyy). Cài đặt nhân sự đang chặn đơn lùi ngày — nhờ phòng Nhân sự lập hộ nếu cần.* |
| `leave_backdated_roles` | Vai trò được lập đơn nghỉ lùi ngày | danh sách vai trò · rỗng (= chỉ quản trị) | Miễn khi người thao tác HOẶC người đã lập đơn có vai trò này (Nhân sự lập hộ thì nhân viên vẫn gửi duyệt được). Ô mờ khi công tắc trên tắt |
| `leave_block_exempt_roles` | Vai trò được duyệt đơn nghỉ rơi vào ngày cấm nghỉ | danh sách vai trò · rỗng (= chỉ quản trị) | `block_period_service.exempt_roles` — §13.5 |
| `leave_prevent_self_approval` | Chặn tự duyệt đơn nghỉ | công tắc · TẮT | `approval/self_approval_policy` — `strict_self_exclusion(entity)` phải truyền ở mọi chỗ tra người duyệt (mở chặng, đồng bộ luồng, xem trước); chốt cuối ở `action_service.approve` + duyệt thẳng, 403 *Cài đặt nhân sự đang chặn tự duyệt: bạn không duyệt được đơn nghỉ của chính mình.* Bước rỗng → người dự phòng → KẸT (không tự duyệt qua). Phiếu nghỉ bù luôn strict (§13.6) |

Kiểu ô `roles` (mới): giao diện là ô chọn nhiều vai trò (cần `role.read`, không có thì hiện mã trơn), lưu chuỗi
`"a,b"`; cửa lưu kiểm mã vai trò có thật. Thêm đường lập đơn mới (nhập Excel, trợ lý AI lập nháp…) thì phải gọi
`ensure_not_backdated`, đừng đọc thẳng `app_settings`. Cuối tab có khối *Danh mục nghỉ phép* với ba lối tắt *Loại nghỉ &
bậc thâm niên* · *Lịch ngày lễ* · *Ngày cấm nghỉ* (mỗi lối tắt gác quyền sửa danh mục đó).

Bài kiểm: `test/backend/test_cai_dat_nhan_su_cr713.py`; vitest `hr/components/hr-settings-form.test.tsx`,
`hr/utils/hr-setting-values.test.ts`.

## 15. Chính sách nghỉ phép, phân bổ, báo cáo ngày lễ (duoc-CR-717, 03/11/2026)

Anh Được (03/11/2026): **làm đủ theo như nexterp**. Đối chiếu 12 mục menu Nghỉ phép của ERPNext ở
`doc/erp/hrm/plans/261103-nghi-phep-du-nhu-nexterp-duoc-cr-717/reports/research-erpnext-vs-dego-12-muc.md`; quyết định D1–D9 đều theo
phương án (a) (`plan.md`). **Kỳ nghỉ phép (Leave Period): không làm** (anh Được bỏ 03/11/2026) — quỹ vẫn theo năm dương
lịch. Migration `lvpol717` (down `lvcmp716`), viết tay, chạy lại được. **Luật chung: không có phân bổ nào = hành vi cũ,
từng con số.**

### 15.1. Mô hình dữ liệu

| Bảng | Cột chính | Ràng buộc |
|---|---|---|
| `tab_leave_policy` | `code String(30)`, `name String(150)`, `note String(500)`, `is_active` + audit | UNIQUE `code` (không đổi sau khi tạo — schema sửa không nhận `code`) |
| `tab_leave_policy_line` | `policy_id`, `leave_type_id`, `annual_days FLOAT` | UNIQUE `(policy_id, leave_type_id)`; index `policy_id`; ≤ 50 dòng; 0–366 bước 0,5; loại phải `counts_balance` và không `is_compensatory` |
| `tab_leave_policy_assignment` | `employee_id`, `company_id` (chép từ hồ sơ lúc tạo — cho `apply_scope`), `policy_id`, `effective_from DATE`, `effective_to DATE NULL` (= không thời hạn), `note String(500)` | UNIQUE `(employee_id, effective_from)` (chống bấm đúp); index `(employee_id, effective_from, effective_to)`; chồng ngày chặn ở service |

Trạng thái phân bổ **dẫn xuất theo `vn_today()`, không lưu** (`LeavePolicyAssignmentState` ở `leave/constants.py`):
`1` Sắp tới · `2` Đang hiệu lực · `3` Đã kết thúc. ⚠️ Tệp `leave/leave_policy.py` là của CR-713 (chặn đơn lùi ngày) —
module mới tên `policy_*.py`: `policy_model` · `policy_schema` · `policy_allocation_math` (thuần) · `policy_allocation`
(nạp CSDL) · `policy_assignment_plan` (`plan_change` dùng chung xem trước + ghi) · `policy_assignment_scope` ·
`policy_assignment_balances` · `policy_assignment_service` · `policy_assignment_view` · `policy_controller` ·
`policy_assignment_controller`.

### 15.2. API chính sách — gác `leave_type`

`make_crud_router`: `GET /api/leave-policies` (lọc `code`, `name`, `is_active`, phân trang chuẩn) · `POST` (201) ·
`GET / PATCH / DELETE /api/leave-policies/{id}` (PATCH `{name?, note?, is_active?}`, cấm `null` tường minh → 422).
Dòng gói thay cả danh sách: `GET /api/leave-policies/{id}/lines` → `{total, items:[{id, leave_type_id, annual_days}]}` ·
`PUT …/lines` body `{items:[{leave_type_id, annual_days}]}`; nhật ký ghi danh sách `loại:ngày` trước → sau; hai PUT đồng
thời vỡ UNIQUE → 409 *Dòng của chính sách vừa được người khác sửa — tải lại rồi thử lại.* Xóa gói còn phân bổ → 409
*Chính sách đang được phân bổ cho N nhân sự — kết thúc / xóa phân bổ trước.* Ngừng dùng (`is_active = false`) chỉ chặn
phân bổ MỚI (422 *Chính sách đã ngừng dùng — không phân bổ mới được.*); phân bổ đang có vẫn áp.

Giao diện: `config/leave-policy-crud.tsx` (`detailLayout: 'flat'`), tab *Loại nghỉ & số ngày*
(`leave-policy-lines-card.tsx`, nút *Thêm dòng* / *Lưu số ngày*) và *Đang phân bổ* (`leave-policy-assignments-tab.tsx`,
gác `leave_balance.read`). Sửa dòng gói **không** tính lại quỹ đã cấp.

### 15.3. API phân bổ — gác `leave_balance`

| Đường | Việc |
|---|---|
| `GET /api/leave-policy-assignments` | Lọc `employee_id`, `policy_id`, `company_id`, `active_on=YYYY-MM-DD`, `search` (≤ 100 ký tự, lọc trong SQL); phạm vi `leave_balance` read; sắp `effective_from` giảm dần. Item: `id, employee_id, company_id, policy_id, effective_from, effective_to, note, employee_name, employee_code, policy_name, state, updated_at` |
| `GET /{id}` | `get_scoped`, ngoài phạm vi → 404 |
| `POST /` | `{employee_id, policy_id, effective_from, effective_to?, note?, recalc_current_year=true, close_previous=false}` → `{assignment, balances:{created, recalculated:[{leave_type_id, before, after}], kept, negative_after}}` |
| `POST /preview` | `{policy_id, effective_from, effective_to?, close_previous, employee_ids? (≤ 500) \| company_id?, department_id?, employment_type?, job_level?, only_without_active=true}` → `{items:[{employee_id, code, name, department_name, hire_date, current, conflict: null\|overlap\|self\|inactive, conflict_message, changes}], total, truncated}` (trần 500) |
| `POST /bulk` | `{policy_id, effective_from, effective_to?, employee_ids (1..500), recalc_current_year, close_previous}` → `{created, skipped:[{employee_id, name, reason}], balances}` |
| `PATCH /{id}` | `{effective_to? (null = không thời hạn), note?, recalc_current_year=true}`; chỉ đổi `effective_to` mới tính lại quỹ |
| `DELETE /{id}?recalc_current_year=` | Mặc định backend `false`; giao diện luôn gửi tường minh, ô mặc định bật (D3a) |

**Chốt khi ghi** (thứ tự): người được phân bổ phải nằm trong **phạm vi GHI quỹ phép** của người làm
(`policy_assignment_scope.writable_employee_query`: phạm vi xem `employee` ∩ `scope_condition(leave_balance, write)`
dựng thẳng trên cột hồ sơ) và **đang làm** (người đã nghỉ việc → 404 *Không tìm thấy nhân sự (đã nghỉ việc, hoặc ngoài
phạm vi của bạn).*; hàng loạt → `skipped`) → gói tồn tại → **không tự phân bổ cho chính mình** (D5, 403
*Không tự phân bổ chính sách nghỉ phép cho chính mình — nhờ người khác trong phòng Nhân sự làm.*, áp cho **tạo, hàng
loạt, sửa và xóa**, chỉ `is_system_admin` qua) → gói đang dùng → **chồng ngày** 409 *Nhân sự X đã có chính sách P từ
dd/mm/yyyy đến …* hoặc `close_previous` (chỉ khi đúng một lượt chồng bắt đầu TRƯỚC `from`; đặt `to = from − 1`) →
UNIQUE `(employee, from)` vỡ → 409 *Nhân sự đã có phân bổ bắt đầu đúng ngày này.*

⚠️ **MySQL REPEATABLE READ:** đường ghi khóa `tab_employee` FOR UPDATE (id tăng dần) rồi MỌI lần đọc phân bổ / dòng gói /
dòng quỹ sau đó là **đọc có khóa** (`policy_allocation.with_row_lock` — `with_for_update(read=True).populate_existing()`);
đọc thường thấy ảnh chụp cũ nên lọt chồng ngày hoặc ghi đè `allocated_days` của lượt khác. Xóa gói khóa dòng gói và
đọc phân bổ có khóa; tạo phân bổ cho gói vừa xóa → 404. SQLite (bộ test) không có khóa hàng — bài kiểm soi câu SQL biên
dịch sang MySQL.

**Hàng loạt:** không savepoint (nhả savepoint làm `change_tracker` đóng dấu **đã commit** sớm) — lỗi CSDL giữa lô thì
rollback cả lô + 500 *Lỗi cơ sở dữ liệu khi phân bổ hàng loạt (…) — chưa lưu gì.*; số truy vấn cố định theo số người
(một câu đọc khóa dòng quỹ, một lần ghi gộp). Xem trước và ghi dùng chung `plan_change` nên màn xem trước không hứa điều
đường ghi sẽ chặn.

### 15.4. Hạn mức theo phân bổ — `policy_allocation_math.compute_allocated`

- **Thứ tự (D1a):** dòng chính sách của phân bổ khớp tháng → hình thức NV → cấp bậc → `annual_quota_days`; loại không có
  trong chính sách → luật của loại (khác ERPNext, nơi loại vắng = 0 ngày).
- **Chia theo tháng, mốc ngày 15 (D2a):** tháng `m` thuộc phân bổ ⇔ `from ≤ 15/m ≤ to`. `q(m)` = số của gói nếu tháng có
  phân bổ và gói khai loại đó, không thì luật của loại. Tập tháng: FULL_YEAR 1..12; PRORATA_HIRE / MONTHLY từ tháng vào
  làm (`first_month_in_year`). Mọi `q(m)` bằng nhau → trả ĐÚNG `prorate_allocation(q)` cũ (kể cả hạn mức lẻ 12.25); khác
  nhau → `round_half_up(Σ q(m) / 12)`. Ví dụ chốt: luật loại 12, gói 15 từ 01/07 → **13,5**; từ 16/07 → 13,25 làm tròn
  **13,5**; PRORATA vào làm 10/03 gói 15 → 12,5; kết thúc 14/09 → tháng 9 về luật loại.
- **Phân bổ từ ngày vào làm (lead chốt 03/11, review M2):** phân bổ bắt đầu trước / đúng ngày vào làm, hoặc trong tháng
  vào làm, được kéo lùi về 01/01 (`extend_to_year_start`, không lấn vào phân bổ khác kết thúc trước nó) — áp **cả năm
  theo số của gói**: luật loại 12 (FULL_YEAR), gói 15 gán từ ngày vào làm 01/10 → **15**, không phải số lai 13; gói 0
  ngày (thử việc) → 0. PRORATA / MONTHLY thì tỷ lệ tính trên số của gói. Phân bổ bắt đầu SAU tháng vào làm không kéo lùi.
- MONTHLY đổi gói giữa năm: `accrual_holdback` vẫn nhân tỷ lệ tháng trên `allocated_days` — xấp xỉ, đã chốt.

**Tính lại quỹ (D3a):** chỉ quỹ **năm nay** (`vn_today().year`), chỉ khi phân bổ (mới / bị đóng / bị sửa / bị xóa) chạm
năm đó; loại = hợp loại của gói mới ∪ gói bị đóng (chỉ loại đang dùng + có trừ quỹ). Thiếu dòng → `ensure_balance`
(`created`); có dòng + `recalc` → chỉ `allocated_days`, nhật ký `leave_balance` *… hạn mức X năm Y a → b ngày*; không
tick / bằng nhau → `kept`. `negative_after` khi số dùng được < −`max_negative_days`. Năm đã qua / năm sau không bao giờ bị
đụng. Rollback CR: quỹ đã tính lại không tự về — số trước/sau nằm trong `tab_audit_log`.

### 15.5. Giao diện phân bổ

Danh sách `/hr/leave-policy-assignments` (`DataTable`, cột Nhân sự · Chính sách · Từ ngày · Đến ngày · Trạng thái · Ghi
chú · Thao tác; lọc tìm / chính sách / *Đang hiệu lực hôm nay* / pháp nhân; khổ < 768px ra thẻ). Hộp *Phân bổ chính sách
nghỉ phép* (`leave-policy-assign-dialog.tsx`): nhân sự (cần `employee.read`), chính sách đang dùng, *Từ ngày* (+ nút *Từ
ngày vào làm*), *Đến ngày* (trống = không thời hạn), ghi chú, ô *Tính lại hạn mức năm nay cho quỹ đã cấp* (mặc định bật);
tự gọi `/preview` (bảng *Hiện tại → Sau phân bổ*); `overlap` hiện ô *Kết thúc chính sách đang hiệu lực*; `self` /
`inactive` khóa nút. Hộp *Kết thúc phân bổ* (PATCH `effective_to`) · *Xóa phân bổ chính sách?* — cả hai có ô tính lại mặc
định bật. Trang *Phân bổ chính sách hàng loạt*: khối 1 chính sách + ngày + hai ô tick, khối 2 lọc pháp nhân / phòng ban /
hình thức NV / cấp bậc + *Chỉ người chưa có chính sách hiệu lực hôm nay*, *Xem danh sách* → bảng chọn (dòng vướng khóa ô
chọn kèm lý do), đổi thông số thì phải xem lại, *Phân bổ N người* → khung *Đã phân bổ N · Bỏ qua M*. Chặn bấm đúp
`useSingleFlight`. Chi tiết dòng quỹ: dòng *Chính sách đang áp: P (từ → đến)* + **khai X ngày/năm cho loại nghỉ này** /
**không khai loại nghỉ này nên vẫn theo hạn mức của loại nghỉ** (`leave-balance-policy-note.tsx`).

### 15.6. Quỹ phép năm — thẻ *Theo nhân sự* (ma trận)

`GET /api/leave-balances/matrix` (+ `/matrix/export`, trần 5000 người) — gác `leave_balance.read` / `export` +
`apply_scope(LeaveBalance)`, không khóa báo cáo. ⚠️ Router đăng ký **TRƯỚC** `leave_balance_router`, nếu không `/{bid}`
nuốt mất `/matrix` (có bài kiểm). Query `year` (0 = năm nay), `company_id`, `department_id` (phòng HIỆN TẠI),
`employee_status` (`working` mặc định | `resigned` | `all`, khác → 422), `search` (escape `%` `_`), `page`, `page_size`.
Trả `{year, columns:[{leave_type_id, name}], items:[{employee_id, code, name, department_name, cells:{"<id>": số}, total}],
total}` — khóa `cells` là **chuỗi**; người thiếu dòng quỹ một loại → không có khóa (giao diện hiện **—**, khác số 0). Ô =
`available_days`. Số truy vấn cố định (bài kiểm 2 vs 42 người). Giao diện `leave-balance-matrix-table.tsx` (cột Mã NV ·
Họ tên · Phòng ban · từng loại · Tổng còn lại; lọc tìm / phòng ban / *Trạng thái nhân sự* / năm; *Xuất Excel* gác
`leave_balance.export`). Đổi thẻ giữ tìm + năm; thẻ dòng quỹ tắt truy vấn 5000 dòng khi đang ở thẻ nhân sự.

### 15.6a. Nối Phân bổ chính sách với Quỹ phép năm (duoc-CR-745, 11/11/2026)

Kiểu mục *Leaves* / liên kết ngược của ERPNext (ở ERPNext, gửi một Leave Policy Assignment sinh ngay một Leave
Allocation mỗi loại nghỉ, mỗi allocation trỏ ngược về assignment). Mình không sinh bản ghi mới, chỉ ĐỌC chéo —
`leave/policy_balance_links.py`, số truy vấn cố định theo trang (bài kiểm đếm truy vấn 2 vs 32 người):

| Đường | Trường mới | Nghĩa |
|---|---|---|
| `GET /api/leave-policy-assignments` | `current_year_quotas: [{leave_type_id, leave_type_name, allocated_days \| null, balance_id}]` | Hạn mức `allocated_days` năm nay của các loại trong gói (chỉ loại `counts_balance`, thứ tự danh mục); `null` + `balance_id = 0` = chưa có dòng quỹ; `[]` = phân bổ không chạm năm nay. Dòng quỹ qua `apply_scope(leave_balance)` |
| `GET /api/leave-balances` | `policy_name` | Gói của các phân bổ chạm năm của dòng VÀ khai đúng loại đó, nối ` → ` theo ngày bắt đầu; rỗng = theo luật của loại |
| `GET /api/leave-balances/matrix` (+ `/export`) | `policy_name` (Excel: cột *Chính sách*, rỗng ghi *Theo loại nghỉ*) | Gói của các phân bổ chạm năm đang xem |

Giao diện: cột *Hạn mức năm nay* (`leave-policy-current-year-quotas.tsx`, cả thẻ điện thoại) · cột *Chính sách* hiện sẵn
ở thẻ *Theo dòng quỹ* (6 cột hiện sẵn, hàng người gộp tên gói của dòng con — `policyNameOfRow`) và thẻ *Theo nhân sự*.
Các cột này không xếp được (giá trị tính ra). Hai màn **không ghi đè nhau**: phân bổ chỉ đổi `allocated_days`, điều
chỉnh tay ghi `adjusted_days`; mỗi (người, loại, năm) một dòng quỹ nên không cộng hai lần. Cùng CR: ô chọn chính sách
khóa và báo *Chưa có chính sách nào đang dùng* khi rỗng (`leave-policy-select.tsx`), nút **?** giải thích *Từ ngày* /
*Đến ngày* (`utils/leave-policy-date-hints.ts`), câu *quỹ năm nay không đổi* nêu đủ ba lý do.

### 15.7. Cấp quỹ có lọc

`POST /api/leave-balances/allocate` nhận thêm `company_id`, `department_id`, `employment_type`, `job_level` (int ≥ 0, 0 =
bỏ qua, âm → 422) cạnh `year`, `leave_type_ids`. Lọc `Employee` TRƯỚC `apply_scope`, chỉ thu hẹp; luật **chỉ tạo dòng
thiếu** giữ nguyên; response không đổi. Giao diện: hộp `leave-balance-allocate-dialog.tsx` thay nút bấm-là-chạy — ô trống
không gửi.

### 15.8. Báo cáo khóa 30 "Làm việc vào ngày lễ, ngày nghỉ"

`ReportKey.HOLIDAY_WORK = 30` (nhóm Nhân sự). `/api/holiday-work-report/summary` · `/summary/export` · `/summary/rows` —
gác kép `require(leave_comp_request, read|export)` + `require_report(30)`, phạm vi `apply_scope(LeaveCompRequest)`; khóa
`/summary` vào `REPORT_SUMMARY_PATHS` (Redis). **Nguồn = phiếu nghỉ bù** (D8a, không có chấm công): mỗi phiếu là một lượt
đi làm ở `work_date`; mặc định chỉ *Đã duyệt*, `include_pending=1` thêm *Chờ duyệt*. Loại ngày theo *Lịch ngày lễ* hiện
hành: trùng lễ → *Ngày lễ*, còn lại → *Ngày nghỉ theo lịch* (gồm ngày nghỉ tuần theo lịch làm việc, như Holiday List của
ERPNext). Query thêm `company_id`, `department_id` (phòng GHI TRÊN PHIẾU), `day_kind` (0/1/2), kỳ ≤ 366 ngày (422).
`group_by`: `department | company | employee | day_kind | holiday_name` (ngày nghỉ theo lịch → *(Chưa gắn)*). Chỉ số:
`lines` Lượt đi làm · `holiday_lines` Trong đó ngày lễ · `offday_lines` Ngày nghỉ theo lịch · `people` Số người ·
`comp_days` Ngày nghỉ bù được duyệt (chỉ phiếu đã duyệt) · `pending_lines` Đang chờ duyệt (chỉ có khi bật chờ duyệt).
`/rows?metric=lines` → Mã NV · Họ tên · Phòng ban · Ngày · Thứ · Loại ngày · Tên ngày lễ · Số ngày bù · Trạng thái phiếu
· Mã phiếu (trần 500, link hồ sơ). Giao diện `/report/holiday-work` (`holiday-work-report-page.tsx` + ô lọc *Loại ngày*,
công tắc *Gồm phiếu chờ duyệt*). Admin tự có khóa 30 (`ensure_report_access_defaults` khi api khởi động); người dùng phải
**đăng nhập lại** mới nhận `report_keys` mới; giao cho người khác ở *Phân quyền tài khoản ▸ tab Báo cáo*. Trợ lý AI:
`REPORTS["holiday_work"]` của `report_summary`.

### 15.9. Trợ lý AI

`my_leave_summary` trả thêm `policy` (`name, code, effective_from, effective_to` của phân bổ phủ mốc = hôm nay kẹp vào năm
hỏi; `null` = không có) và ở từng dòng `balances`: `policy_name`, `policy_annual_days` (`null` = gói không khai loại đó).
Chỉ đọc qua `policy_allocation.load_assignments` / `load_lines` (không khóa), 3 truy vấn. Hạn mức thật vẫn là
`allocated_days`. Cẩm nang `ai_skill/seed_handbook/40-nghi-phep.md` có mục chính sách + báo cáo khóa 30.

### 15.10. Bài kiểm

`test_nghi_phep_chinh_sach_cr717.py` · `test_nghi_phep_phan_bo_hang_loat_cr717.py` · `test_nghi_phep_review_cr717.py`
(H1–L6 của lượt rà mã) · `test_bao_cao_lam_ngay_le_cr717.py` · `test_nghi_phep_quy_tong_hop_cr717.py` ·
`test_assistant_nghi_phep_chinh_sach_cr717.py`; vitest các tệp `hr/**/leave-policy-*.test.tsx`,
`leave-balance-{matrix-table,allocate-dialog,policy-note}.test.tsx`, `report/components/holiday-work-report-filters.test.tsx`,
`app/router/module-visibility.test.ts`.

## 16. Thanh toán nghỉ phép (duoc-CR-719, 03/11/2026)

Leave Encashment của ERPNext: đổi ngày phép chưa nghỉ ra tiền khi **cuối năm còn dư** hoặc khi **nghỉ việc** (Điều 113
khoản 3 Bộ luật Lao động). Anh Được chốt bốn ý (FINAL): bật theo **loại nghỉ** + trần; phiếu chỉ ghi **số ngày**, số tiền
do người có quyền tài chính nhập sau, **không lộ lương** (không đụng phần lương, chốt 16/10/2026 vẫn giữ); duyệt xong
**trừ quỹ** và **sinh YCTT** ở Tài chính; ai lập **y ERPNext**. Kế hoạch:
`doc/erp/hrm/plans/261103-thanh-toan-nghi-phep-duoc-cr-719/plan.md` (nghiên cứu ERPNext ở `reports/research-erpnext-encashment.md`).
Giao diện: mục menu *Thanh toán nghỉ phép* (`/hr/leave-encashments`, `/new`, `/:id`) + khung riêng của YCTT nghỉ phép bên
Tài chính. Bài HDSD: **Thanh toán nghỉ phép** (`seed_help_nghi_phep.py`) và **Yêu cầu thanh toán nghỉ phép: nhập số tiền
và chi** (`seed_help_yctt_thanh_toan_nghi_phep.py`, thư mục *Dành cho Kho & Kế toán*).

### 16.1. Mô hình dữ liệu (migration `lvenc719`, down `hqx718b`, viết tay, chạy lại được)

- **`tab_leave_encashment`** (`leave/encashment_model.py`): `code` **TTP…** UNIQUE · `company_id` · `department_id` ·
  `employee_id` · `leave_type_id` · `balance_year` · `reason_kind` SMALLINT (`LeaveEncashmentReason`: `1` Phép dư cuối năm
  · `2` Nghỉ việc) · `encashment_date` · `days` (bước 0,5) · `balance_snapshot` / `encashable_snapshot` (chụp lúc gửi) ·
  `note` (1000) · `status` SMALLINT (`LeaveEncashmentStatus`: `1` Nháp · `2` Chờ duyệt · `3` Đã duyệt · `4` Từ chối ·
  `5` Trả về chỉnh sửa · `6` Đã hủy) · `approval_instance_id` · `decided_at` · `decision_note` (500) ·
  `payment_request_id` · `active_key` String(60) UNIQUE NULL · `is_deleted` (cột riêng, không `SoftDeleteMixin`) · audit.
  Chỉ mục `(employee_id, balance_year)`. **Không có cột tiền.**
- `tab_leave_type`: `allow_encashment` (bool, mặc định 0) · `max_encashable_days` (trần THEO NĂM, 0 = không trần) ·
  `non_encashable_days` (giữ lại, chỉ lý do cuối năm) — §11.1.
- `tab_leave_balance.encashed_days` — khoản **trừ**. `remaining_days` đã trừ nó; `available_days` / `available_days_map`
  đi qua `remaining_days` nên tự đúng. Báo cáo **Quỹ phép năm** có chỉ số `encashed` *Đã thanh toán ra tiền* (không thêm
  truy vấn); bảng quỹ có cột ẩn sẵn **Đã thanh toán ra tiền**, chi tiết dòng quỹ có ô cùng tên khi khác 0, thẻ quỹ ghi
  `N đã thanh toán`.
- `tab_payment_request`: `payee_employee_id` · `source_ref_id` (BigInteger, mặc định 0) + chỉ mục
  `ix_payment_request_source_ref (source_type, source_ref_id)`. Nguồn mới `source_type = "leave_encashment"` (hằng
  `payment_request.hr_payout_guard.PAYMENT_SOURCE_LEAVE_ENCASHMENT`), trạng thái YCTT giữ mã chuỗi thu mua cũ (QĐ-9).

### 16.2. Luật tính số được thanh toán (`leave/encashment_math.py`, `encashment_balance.py`)

```
encashable = floor_0,5( clamp(base, 0, cap) )
Phép dư cuối năm: base = available − phần mang sang chưa dùng − non_encashable_days
                  cap  = max_encashable_days − encashed_days của dòng   (chỉ khi trần > 0)
Nghỉ việc:        base = available, không trần, không giữ lại
```

Làm tròn **xuống** bước 0,5; quỹ âm (ứng phép) → 0. Năm quỹ = năm nay (tự cấp quỹ nếu chưa có) hoặc năm trước (không tự
cấp, có `expire_carried`; năm đã kết sổ thì số dùng được về 0). `GET /preview` trả từng số để hộp **Số ngày được thanh
toán** trên form đọc lại, giao diện **không** tự tính.

### 16.3. API `/api/leave-encashments` (tag `leave`, khóa `leave_encashment`)

| Phương thức | Đường | Quyền | Ghi chú |
|---|---|---|---|
| GET | `/` | `read` + phạm vi | lọc `status, employee_id, company_id, department_id, leave_type_id, balance_year, reason_kind`, `q`, `sort`; mỗi dòng có `payment_status` đọc từ YCTT |
| GET | `/to-approve` | đăng nhập | việc duyệt đang chờ người gọi |
| GET | `/preview` | `create` | chỉ đọc; lập hộ cần quyền lập trong phạm vi người đó |
| GET | `/{id}` | `read`, hoặc có việc duyệt treo | thêm `payment` (`total` chỉ có với chính người nhận hoặc người đọc được YCTT, còn lại `null`) và `cancel_blocked_reason` |
| POST | `/` | `create` | luôn ra Nháp; `days = null` = lấy số tối đa |
| PATCH | `/{id}` | `write` | chỉ Nháp / Trả về; người, loại, năm không đổi |
| DELETE | `/{id}` | `delete` | xóa mềm, chỉ Nháp |
| POST | `/{id}/submit` | `write` | khóa dòng quỹ, tính lại, `pending += days`, chụp snapshot, trình luồng (không có luồng → Chờ duyệt, `approval_instance_id = 0`) |
| POST | `/{id}/approve` | `approve` | duyệt thẳng; 400 nếu đang chạy luồng; 403 tự duyệt |
| POST | `/{id}/reject?reason=` | `approve` | `reason` ≤ 500 |
| POST | `/{id}/cancel?reason=` | `cancel` | xem §16.6 |

Lỗi riêng: 422 loại nghỉ không cho thanh toán · năm ngoài {nay, trước} · chưa có quỹ · lý do Nghỉ việc mà hồ sơ thiếu ngày
nghỉ việc · người đã nghỉ việc chọn lý do cuối năm · `days` lệch bước 0,5 hoặc vượt số được phép; 409 trùng phiếu còn hiệu
lực (D4) hoặc *Phiếu vừa được xử lý bởi lượt khác — tải lại trang* (mọi đổi trạng thái đi qua `claim` nguyên tử); 400 sửa /
xóa sai trạng thái, hủy bị YCTT chặn; 403 lập hộ ngoài phạm vi / tự duyệt.

### 16.4. Phân quyền và chốt xem YCTT (D1a)

Seed (`app/seed.py`): mọi vai trò `read, create, write, delete` phạm vi **của mình**; `dept_head` `read, export` phòng;
`company_head` `read, export` công ty; `hr_leave` đủ bảy hành động phạm vi tất cả. Khóa nằm trong `_SYS_ENTITIES` (Quản lý
thu mua không tự có `all`). `self_approval_policy.ALWAYS_STRICT_ENTITIES` có `leave_encashment`: **luôn chặn tự duyệt**,
bất kể công tắc Cài đặt nhân sự. Cách duyệt 9 *theo quyền* (duoc-CR-680) mở cho entity này.

**Chốt xem YCTT** nằm ở `core/scoping.scope_condition` (vỏ bọc; thân cũ là `_grant_scope_condition`): với
`entity == "payment_request"` AND thêm `hr_payout_guard.payout_visibility_cond` — YCTT nguồn `leave_encashment` chỉ hiện
khi phạm vi `leave_encashment.read` của người xem phủ phiếu nguồn (`source_ref_id IN (SELECT id FROM tab_leave_encashment
WHERE <phạm vi>)`); không có quyền đó → chỉ còn YCTT nguồn khác. Phủ `apply_scope`, `get_scoped`,
`get_approvers_for_entity` nên danh sách, chi tiết, in, xuất Excel, tập dữ liệu AI, việc chờ duyệt, chuông đều theo.
Lý do: số tiền ÷ số ngày = lương ngày. Hệ quả có chủ đích: Quản lý / Nhân viên thu mua mặc định **không** thấy YCTT nghỉ phép.

### 16.5. Khóa quyền trên hệ đang chạy (D-018)

`seed_prod.py` không ghi đè phân quyền, nên dev / prod phải tick tay ở *Quản trị ▸ Phân quyền tài khoản* (hoặc
`SEED_FORCE_SYNC=true` một lần rồi trả về `false`):

- mọi vai trò nhân viên: `leave_encashment` `read, create, write, delete` phạm vi **của mình**;
- `hr_leave`: đủ hành động phạm vi tất cả (người duy nhất duyệt / hủy được phiếu);
- trưởng bộ phận / trưởng công ty: `read, export` phạm vi phòng / công ty;
- **vai trò Kế toán**: `payment_request` `read, write, approve, print` **và** `leave_encashment` `read` phạm vi **công ty**
  (hoặc tất cả). Thiếu khóa sau thì **không ai bên Tài chính thấy YCTT nghỉ phép**, chuông *cần nhập số tiền* rơi về quản trị.

Muốn phiếu đi luồng thì bật bộ máy duyệt cho entity `leave_encashment` (nhãn *Thanh toán nghỉ phép*) ở Phê duyệt; chưa bật
thì `hr_leave` duyệt thẳng. Người đang đăng nhập phải đăng xuất / đăng nhập lại để nhận map quyền mới.

### 16.6. Vòng đời, YCTT đi kèm và ma trận hủy

- **Gửi**: `pending_days += days`. **Từ chối / trả về / rút / hủy khi Chờ duyệt**: một hàm `release_and_set` trả `pending`.
- **Duyệt** (bộ máy duyệt hoặc duyệt thẳng, cùng một giao dịch): `pending −= days`, `encashed_days += days`, gọi
  `payment_request.leave_encashment_payout.create_payout_request` → YCTT **Nháp**, nguồn `leave_encashment`, người nhận =
  nhân sự (`payee_employee_id`), một dòng tiền 0, `source_ref_id` = id phiếu; ghi `payment_request_id`. Hỏng giữa chừng
  (`HookVeto`) thì cuộn cả giao dịch.
- **YCTT nghỉ phép** (`leave_encashment_payout.py`): chỉ sửa ngày, ghi chú, hình thức, chữ in, trưởng bộ phận và đúng một
  dòng tiền `0 ≤ amount ≤ 9.999.999.999.999`; gửi duyệt 400 *Nhập số tiền thanh toán nghỉ phép trước khi gửi duyệt* khi
  bằng 0; cấm cấn trừ / trả trước / thêm dòng; chi (`paid`) không đụng công nợ hay ĐMH; chặn xóa (cả xóa nhiều), hoàn
  tiền, cập nhật theo công nợ; API tạo YCTT từ chối `source_type = "leave_encashment"` (chỉ máy tạo). Bản in (D2a): số tài
  khoản lấy từ hồ sơ nhân sự chỉ khi chuyển khoản **và** người in có `employee_sensitive.read` hoặc là chính chủ, không thì
  `bank_hidden: true` → bản in ghi **kế toán tự điền**.
- Phiếu **không lưu** trạng thái chi: đọc từ YCTT (`payout_state`) mỗi lần trả về.

| Phiếu | YCTT | Hủy phiếu |
|---|---|---|
| Nháp | — | màn chỉ bày **Xóa phiếu** (xóa mềm, nhả `active_key`); API `cancel` vẫn nhận, ra Đã hủy |
| Chờ duyệt · Trả về | — | được, trả `pending` (đang chạy luồng thì rút luồng trước) |
| Đã duyệt | Nháp | được: `encashed_days −= days`, YCTT Nháp xóa mềm (`void_draft_payout`) |
| Đã duyệt | Chờ duyệt · Đã duyệt | **chặn** 400 *YCTT … đang ở … — kế toán từ chối YCTT trước* (nút ẩn, `cancel_blocked_reason`) |
| Đã duyệt | Đã chi | **chặn** *YCTT … đã chi tiền — không hủy được phiếu* |
| Đã duyệt | Đã từ chối | được (D7a), YCTT giữ nguyên làm hồ sơ |
| Từ chối · Đã hủy | — | 400 |

YCTT được đọc **có khóa dòng** (`payout_state(lock=True)`) lúc hủy để kế toán không gửi duyệt chen giữa. Kế toán không bỏ
được YCTT Nháp (không xóa, không từ chối từ Nháp) — Nhân sự hủy phiếu (D7a, chấp nhận 03/11/2026).

### 16.7. Thông báo

| Sự kiện | Ai nhận | Câu |
|---|---|---|
| `pay_leave_created` — phiếu duyệt xong, YCTT sinh ra | người duyệt YCTT thấy được phiếu (`get_approvers_for_entity`, đã qua chốt D1a), không có thì quản trị | *… — Thanh toán nghỉ phép cần nhập số tiền* |
| `pay_leave_paid` — YCTT ghi nhận đã chi | tài khoản của nhân sự được thanh toán | *… — Đã chi thanh toán nghỉ phép* |
| `pay_leave_rejected` — kế toán từ chối YCTT | người duyệt phiếu (`updated_by`) và người lập phiếu | *… — Kế toán từ chối chi thanh toán nghỉ phép*, kèm lý do |

Chuông `pay_leave_created` gửi **sau commit** (đăng ký `after_commit` trong `approve_now`, chạy bằng phiên mới): gọi chung
giao dịch duyệt thì `trigger_notification` commit lửng. Chữ chuông không có số tiền, không có số ngày. Việc duyệt phiếu:
`task_notification.ENTITY_LABELS` = **Thanh toán nghỉ phép**, link `/hr/leave-encashments/{id}`.

### 16.8. Quyết định D1–D9 (chốt 03/11/2026, tất cả phương án a)

| # | Chốt |
|---|---|
| D1 | YCTT nghỉ phép chỉ hiện với người có quyền YCTT **và** `leave_encashment.read` phủ phiếu (chốt ở `scope_condition`) |
| D2 | Số tài khoản trên bản in chỉ khi có `employee_sensitive.read` hoặc là chính chủ, không thì **kế toán tự điền** |
| D3 | Mọi vai trò lập phạm vi của mình, Nhân sự lập hộ; `approve` chỉ `hr_leave`; trưởng bộ phận / công ty chỉ xem; luôn chặn tự duyệt |
| D4 | Một phiếu còn hiệu lực (Nháp / Chờ duyệt / Đã duyệt / Trả về) cho mỗi (người, loại, năm, **lý do**) — `active_key = "<employee_id>:<leave_type_id>:<balance_year>:<reason_kind>"`, NULL khi Từ chối / Đã hủy / xóa. Thêm lý do vào khóa sau lượt rà mã (M2): đã thanh toán phép dư cuối năm rồi nghỉ việc trong cùng năm vẫn phải lập được phiếu nghỉ việc (BLLĐ Điều 113) |
| D5 | Nghỉ việc: bỏ hai trần, tính cả phần mang sang; bắt hồ sơ có `resign_date` |
| D6 | Cuối năm không đổi phần mang sang chưa dùng (như ERPNext) |
| D7 | Kế toán từ chối YCTT: phiếu giữ Đã duyệt, màn hiện băng **Kế toán từ chối chi**, Nhân sự hủy phiếu để trả ngày |
| D8 | Trợ lý AI chỉ đọc: `my_leave_summary` trả `encashed_days` mỗi dòng quỹ, `allow_encashment` / `max_encashable_days` / `non_encashable_days` mỗi loại, `encashments[]` (số ngày, trạng thái, trạng thái chi, **không tiền**); không có công cụ soạn nháp |
| D9 | Năm quỹ là năm nay hoặc năm trước |

Hành vi chấp nhận sau lượt soát màn (03/11/2026): người chỉ có `create` vẫn thấy nút **Gửi duyệt** (lưu nháp rồi ăn 403 ở
bước gửi, như khuôn nghỉ bù); link YCTT trên phiếu chỉ dựa `payment_request.read` (ngoài phạm vi D1a thì mở ra 404).
Xóa hồ sơ nhân sự bị chặn khi còn phiếu thanh toán nghỉ phép hoặc là người nhận YCTT (`employee/references.py`).

### 16.9. Bài kiểm

`test_thanh_toan_nghi_phep_nen_cr719.py` (16 — công thức quỹ, khóa quyền, chốt xem YCTT) ·
`test_yctt_thanh_toan_nghi_phep_cr719.py` (37 — YCTT nguồn nghỉ phép, bản in D2a, rà đường đọc) ·
`test_nghi_phep_thanh_toan_cr719.py` (35 — toán, vòng đời qua bộ máy thật, `HookVeto`, ma trận hủy, tự duyệt, chuông,
`my_leave_summary` không tiền); `test_pham_vi_khai_du_b07.py` 80/80; vitest `hr/types/leave-encashment.test.ts`,
`hr/components/leave-encashment-{form,payment-card}.test.tsx`, `finance/components/payment-request-leave-encashment-view.test.tsx`.
