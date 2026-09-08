# Nghỉ phép — phân hệ Nhân sự

| | |
|---|---|
| Bản | 1.2 — 07/09/2026 (kết sổ cuối năm · bảng trường Loại nghỉ) |
| CR | **CR-259** · duoc-CR-302 · duoc-CR-303 · **duoc-CR-304** |
| Giao diện | **chỉ có trên `frontend-v2/`** (cổng 8083), menu *Nhân sự ▸ Nghỉ phép* |
| Kế hoạch gốc | `plans/260903-0956-quan-ly-nghi-phep/plan.md` |
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

## 3. Năm màn hình

| Màn | Đường dẫn | Khóa quyền |
|---|---|---|
| Đơn nghỉ phép (danh sách + chi tiết + nộp mới) | `/hr/leave-requests` | `leave_request` |
| Lịch nghỉ (theo tuần) | `/hr/leave-calendar` | `leave_request` |
| Quỹ phép năm | `/hr/leave-balances` | `leave_balance` |
| Thiết lập ▸ Loại nghỉ (kèm tab *Bậc thâm niên*) | `/hr/leave-types` | `leave_type` |
| Thiết lập ▸ Lịch ngày lễ | `/hr/holidays` | `holiday` |

Hai màn thiết lập dựng bằng **khung CRUD khai báo** (`shared/crud/`), ba màn còn
lại viết tay vì có nghiệp vụ riêng.

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

**Chỉ sửa được ở «Nháp» và «Trả về chỉnh sửa».** Đã gửi duyệt là khóa.

**«Từ chối» khác «Trả về chỉnh sửa»** — và phải khác. Từ chối là khóa hẳn, muốn
nghỉ nữa thì lập **đơn khác**. Trả về là mời sửa rồi gửi lại chính tờ đó. Gộp hai
cái vào một trạng thái thì người soạn mở đơn ra không biết mình vừa bị dẹp hay
đang được mời sửa lại (bài học 24/08/2026 của phân hệ Văn thư).

## 5. Quỹ phép — công thức và bốn nhịp

```
còn lại = (hạn mức + thâm niên + chuyển năm trước + điều chỉnh tay)
          − đã nghỉ − đang chờ duyệt
```

**Số còn lại KHÔNG lưu thành cột.** Lưu thêm thì có hai nguồn sự thật, và cái thứ
hai sẽ lệch. `balance_service.remaining()` là nơi duy nhất tính.

Sổ quỹ chạy theo bốn nhịp, khớp bốn kết cục của bộ máy duyệt:

| Nhịp | Khi nào | Làm gì |
|---|---|---|
| `reserve` | gửi duyệt | `pending_days += n` — **giữ chỗ** |
| `consume` | duyệt xong | `pending −= n`, `used += n` |
| `release` | từ chối / trả về / rút / hủy | `pending −= n` |
| `refund_used` | hủy một đơn **đã duyệt** | `used −= n` |

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

### Không có ứng phép (QĐ-NP2)

Xin vượt quỹ là **chặn lúc gửi duyệt**, không ghi nợ. Muốn nghỉ tiếp thì chọn loại
**«Nghỉ không lương»** — câu chặn của backend nói thẳng đường đó. Ghi nợ nghe thì
tiện nhưng kéo theo cả một sổ công nợ phép và luật trừ lương khi nghỉ việc.

### Cấp phát quỹ

Nút *Cấp quỹ năm* ở màn Quỹ phép, **chạy lại được**: chỉ tạo dòng còn thiếu. Bấm
hai lần không nhân đôi; thêm người giữa năm thì bấm lại là họ có quỹ. Cấp **một
lần đầu năm** (Q1), thâm niên tính tại 01/01 — không cộng dần theo tháng.

⚠️ Cố ý **không** cập nhật dòng đã có theo hạn mức mới: đổi hạn mức giữa năm thì
quỹ đã cấp giữ nguyên, luật mới áp cho lần cấp sau.

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
  nhận, loại nhận phải **khác chính nó** và phải bật «Trừ vào quỹ phép năm».
- **Phần mang sang HẾT HẠN** cuối tháng `carry_over_expire_month` của năm nhận
  (thông lệ: hết 31/3; `0` = không hết hạn). Thu hồi lúc **chạm vào** dòng quỹ
  (`expire_carried`), không phải bằng việc chạy nền.
- ⚠️ **Phần mang sang được coi là TIÊU TRƯỚC.** Sổ chỉ có một cục `used_days`,
  không biết ngày nào tiêu vào quỹ nào, nên phải chọn một phía — chọn phía có lợi
  cho người lao động, vì phép mang sang là phép sắp hết hạn.
- Phần đã **quy đổi** thì sống theo luật hết hạn của **loại nhận**, không theo
  loại nguồn.

### Điều chỉnh tay

Cột duy nhất nhận **số âm**. **Ghi ĐÈ, không cộng dồn** — người dùng nhìn con số
hiện tại và gõ con số họ muốn nó thành; cộng dồn thì bấm Lưu hai lần là gấp đôi.
**Bắt buộc có lý do**, ghi vào `tab_audit_log`: đây là thao tác tặng ngày phép.

## 6. Số ngày nghỉ

`workday_service.count_leave_days()` là nơi **duy nhất** tính. Đã trừ thứ Bảy,
Chủ nhật và ngày lễ theo `tab_holiday`.

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
thuẫn với chính luật *«chiều → sáng cùng ngày là khoảng trống»* mà nó đang chặn.
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
`check_date_range`. ⚠️ Không có chốt này thì `date_range` lặng lẽ dừng ở 400 và
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
| Khoảng ngày | `to_date >= from_date`; nghỉ từ **chiều đến sáng cùng ngày** là khoảng trống → chặn |
| Chồng ngày | Hai đơn còn hiệu lực (chờ duyệt / đã duyệt) của **cùng một người** không được chồng khoảng — chồng là trừ phép hai lần cho một ngày |
| Giới tính | Thai sản chỉ áp cho hồ sơ nữ. **Hồ sơ chưa khai giới tính KHÔNG bị chặn** — chặn là khóa cả công ty tới khi Nhân sự nhập bù |
| Trần mỗi lần | Cưới hỏi · tang chế 3 ngày. `0` = không giới hạn |
| ~~Báo trước~~ | **ĐÃ BỎ 05/09/2026.** Không còn luật "phải nộp trước N ngày" — nghỉ ngày mai vẫn gửi duyệt được. Cột `min_notice_days` còn trong bảng nhưng không ai đọc, và đã gỡ khỏi schema lẫn màn danh mục loại nghỉ |
| Nhập đủ | Chốt ở lúc **gửi duyệt**, không phải lúc lưu nháp — cùng luật với `required-fields.ts` của Thu mua |
| Lập hộ | Được, và từ 07/09/2026 form có ô **Người nghỉ** (mặc định điền sẵn chính mình). Gác bằng `ensure_can_create_for`: phải có `leave_request.create` phạm vi **rộng hơn `own`** VÀ đọc được hồ sơ người đó trong phạm vi `employee`. Cả người lập (`created_by`) lẫn người nghỉ (`employee_id`) đều thấy tờ đơn ở phạm vi «của mình» |
| Nghỉ **theo giờ** | Buổi nghỉ có lựa chọn thứ tư **«Theo giờ»** (`SESSION_HOURLY = 4`, 07/09/2026): khai `from_time`/`to_time`, **vắt qua nhiều ngày được** (từ 14:00 ngày A đến 10:00 ngày B). Số ngày do máy quy đổi, **không cho gõ đè** — ngày đầu tính tới hết giờ làm, ngày cuối từ đầu giờ làm, ngày giữa trọn một công, T7/CN/lễ bỏ qua. Khung giờ làm khai ở `constants`: **08:00–17:00, nghỉ trưa 12:00–13:00, 8 giờ công/ngày**; giờ ngoài khung không tính |

### 7.1. Nhiều loại nghỉ trong một đơn (07/09/2026)

*"Nghỉ 07→10/09, trong đó 3 ngày phép năm + 1 ngày không lương"* — trước đó phải
lập hai đơn, mà chốt **chồng ngày** ở trên lại chặn đúng chuyện đó.

**Cả đơn dùng CHUNG một khoảng ngày; dòng chỉ chia SỐ NGÀY.** Bản khai ngày riêng
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

⚠️ **Hạn chế đã biết — không phải lỗi.** Điều kiện rẽ nhánh của luồng duyệt đọc
`leave_type_id`, tức **loại chính**. Nhánh khai *"loại nghỉ = không lương thì thêm
chặng Giám đốc"* sẽ KHÔNG chạy cho tờ đơn 3 ngày phép năm + 1 ngày không lương.
Cố ý không đưa danh sách loại vào `entity_context`: `condition_service` chỉ so được
giá trị vô hướng, thêm một ô mà phép `in` của nó không đọc nổi thì tệ hơn không có.

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

⚠️ **Còn một công tắc nữa: màn «Bật bộ máy duyệt»** (`/approval/engine`, dòng
*Nghỉ phép*). Đó là **đường lui của cả phân hệ** — gạt tắt là mọi đơn nộp từ giây
đó đi đường duyệt thẳng ở đoạn trên, kể cả khi luồng đã khai đầy đủ; đơn đang chạy
dở thì đi hết bản luồng đã chụp lúc trình, không bị cắt ngang. Phân biệt với đoạn
trên: kia là *tình cờ chưa có luồng*, đây là *cố ý tắt để quay về*. Cờ mặc định
**TẮT** khi chưa có dòng nào trong `tab_approval_switch`; `app/seed_nghi_phep.py`
nạp sẵn một dòng bật cho `leave_request`, nên hệ đã chạy seed đó thì không phải
làm gì. Tắt cờ **không** đụng tới quỹ phép — giữ chỗ `pending_days` vẫn trừ y hệt.

**Hủy đơn đang trong luồng** thì hệ **rút phiên duyệt** trước rồi mới hủy. Không
rút thì phiếu vẫn chạy, người duyệt ký xong là hook trừ quỹ cho một tờ đơn đã hủy.
Chỉ **người nộp** rút được (luật của bộ máy); người khác dùng *Trả lại* / *Từ chối*
ở màn Phê duyệt, nơi có ô ghi lý do.

## 9. Phân quyền — bốn khóa, đừng gộp

| Khóa | Màn |
|---|---|
| `leave_request` | Đơn nghỉ phép · Lịch nghỉ |
| `leave_balance` | Quỹ phép năm |
| `leave_type` | Loại nghỉ (kèm bậc thâm niên) |
| `holiday` | Lịch ngày lễ |

Tách bốn vì **`leave_balance` ghi được nghĩa là tặng thêm ngày phép cho bất kỳ ai**.
Gộp chung với `leave_request` thì cho ai xem đơn của mình là cho họ tự cộng phép.

**Phạm vi dữ liệu**: `leave_request` khai **cả `owner` lẫn `self`** — điểm khác mọi
entity khác. Một tờ đơn có hai người dính tới nó, người **lập** (`created_by`) và
người **nghỉ** (`employee_id`), cả hai phải thấy nó ở phạm vi «của mình».
`leave_balance` chỉ khai `self` (người cấp phát là Nhân sự, lấy đó làm "của mình"
thì nhân viên không thấy quỹ của chính họ). Hai danh mục khai `PUBLIC`.

**Vai trò mẫu `hr_leave`** — Nhân sự quản lý nghỉ phép, có đủ bốn khóa. Không gán
tự động cho ai.

⚠️ **Trên hệ ĐANG CHẠY, vai trò cũ không tự có bốn khóa này.** Seed cố ý không ghi
đè phân quyền đã chỉnh tay (D-018), nên quản trị phải tick thêm ở
*Nhân sự ▸ Phân quyền tài khoản*, hoặc chạy một lần với `SEED_FORCE_SYNC=true`.
Người dùng báo "không thấy menu Nghỉ phép" thì gần như chắc là chỗ này.

## 10. Những thứ CHƯA có

| Thiếu | Ghi chú |
|---|---|
| ~~Nghỉ **nửa ngày / theo giờ**~~ | **ĐÃ CÓ 07/09/2026** — nửa ngày qua hai ô buổi (§6), theo giờ qua buổi thứ tư *«Theo giờ»* (§7). Cột `unit` vẫn chỉ dùng giá trị *Ngày*: số giờ được **quy đổi ra ngày**, không lưu thành đơn vị riêng |
| **Đính kèm** trên đơn | Cột `require_attachment` của loại nghỉ đã có nhưng chưa nối vào hạ tầng đính kèm |
| Danh sách **bàn giao** trên giao diện | Bảng `tab_leave_handover` và API đã có; form v2 chưa dựng ô nhập (bản chỉ xem thì hiện đủ) |
| ~~**Chuyển phép sang năm sau**~~ | **ĐÃ CÓ 07/09/2026** — ba nước *mất / mang sang / quy đổi* + nút **Kết sổ cuối năm**, xem §5. Cờ `carry_over` cũ thành di tích (§11.2). Còn thiếu: **báo cáo đối chiếu** trước/sau kết sổ — hiện chỉ có câu thông báo đếm dòng |
| **Báo cáo / thống kê** nghỉ phép | Chưa dựng màn riêng |
| Nạp `hire_date` cho hồ sơ cũ | **Ô nhập đã có từ 07/09/2026** ở *Nhân sự ▸ chi tiết hồ sơ* (kèm ô *Giới tính*) — trước đó hai cột này có trong bảng nhưng không schema nào khai, nên không màn nào nhập được và thâm niên của cả công ty tính bằng 0. Việc còn lại là **nhập bù dữ liệu**, không phải dựng màn |

## 11. Danh mục **Loại nghỉ** — từng trường

`/hr/leave-types` (danh sách) · `/hr/leave-types/new` (thêm) · `/hr/leave-types/:id`
(sửa, kèm tab *Bậc thâm niên*). Dựng bằng khung CRUD khai báo — mọi thứ dưới đây
khai ở **một chỗ**: `frontend-v2/src/modules/hr/config/leave-type-crud.tsx`.
Bảng: `tab_leave_type` (`leave/catalog_model.py`).

Form thêm/sửa **dài nên đi trang riêng, không hộp thoại**, và chia **ba cụm** —
người khai danh mục là nhân sự, không phải người viết luật, mà ở màn này đoán sai
quan hệ giữa hai ô là khai sai luật nghỉ cho **cả công ty**.

### 11.1. Các trường có trên form

| Ô | Cột | Kiểu | Mặc định | Ghi chú |
|---|---|---|---|---|
| **Mã loại nghỉ** | `code` | chữ | — | ⚠️ **KHÓA sau khi tạo** (`readonlyOnEdit` + backend chặn lớp hai): mã này đi vào metadata mọi giấy GNP đã phát hành. Phải khớp `core/leave_codes.LEAVE_TYPE_SET` |
| **Tên loại nghỉ** | `name` | chữ | — | Bắt buộc |
| *Cụm «Quỹ phép và lương»* | | | | |
| Trừ vào quỹ phép năm | `counts_balance` | công tắc | Tắt | Bật thì nộp đơn **bị chặn khi hết phép** (không ứng trước). Đứng **đầu cụm, cột trái** vì nó mở ra ô hạn mức ngay bên dưới |
| Có hưởng lương | `is_paid` | công tắc | Bật | Tách khỏi `counts_balance`: cưới hỏi vẫn hưởng lương nhưng không ăn vào phép năm |
| Hạn mức mỗi năm (ngày) | `annual_quota_days` | số | 0 | **Chỉ hiện khi** «Trừ vào quỹ phép năm» bật. Bậc thâm niên cộng thêm khai ở tab riêng |
| *Cụm «Điều kiện áp dụng»* | | | | |
| Áp dụng cho giới tính | `gender` | chọn | Mọi giới (`0`) | Hồ sơ **chưa khai** giới tính vẫn nộp được — chặn là khóa cả công ty tới khi Nhân sự nhập bù |
| Tối đa mỗi lần nghỉ (ngày) | `max_days_per_request` | số | 0 | `0` = không giới hạn. Trần của **một đơn**, không dính quỹ năm |
| Trừ Chủ nhật và ngày lễ | `exclude_holiday` | công tắc | Bật | ⚠️ **Thứ Bảy VẪN tính công** — DEGO làm cả T7 (`WEEKEND_DAYS = (6,)`). Tắt cho loại nghỉ dài liên tục (thai sản) |
| Bắt buộc đính kèm | `require_attachment` | công tắc | Tắt | Cột đã có; **chưa nối vào hạ tầng đính kèm** (xem §10) |
| *Cụm «Số dư cuối năm»* — xem §5 | | | | |
| Cách xử lý số dư | `year_end_mode` | chọn | Hết năm là mất (`0`) | Ba nước loại trừ nhau nên là ô chọn, không phải hai công tắc |
| Hạn dùng phép mang sang | `carry_over_expire_month` | chọn 13 mục | Đến hết tháng 3 năm sau | **Chỉ hiện khi** «Mang sang năm sau». `0` = không hết hạn. Ô CHỌN chứ không phải ô gõ số: hạn này **lặp mỗi năm** nên không chốt cứng được thành một cặp ngày, mà tháng 2 còn nhảy 28/29 |
| Loại nghỉ nhận số ngày | `convert_to_type_id` | chọn (nạp từ API) | 0 | **Chỉ hiện khi** «Quy đổi». Phải khác chính nó và phải bật «Trừ vào quỹ phép năm» — backend chặn **ngay lúc lưu** |
| Tỷ lệ quy đổi | `convert_ratio` | số | 1 | **Chỉ hiện khi** «Quy đổi». 1 ngày dư đổi được mấy ngày ở loại nhận; hai đổi một thì ghi `0.5`. Phải > 0 |
| **Ghi chú** | `note` | nhiều dòng | rỗng | |
| **Đang dùng** | `is_active` | công tắc | Bật | Tắt = ẩn khỏi ô chọn; đơn cũ giữ nguyên |

⚠️ **Ẩn/hiện chỉ là chuyện HIỂN THỊ** (`showWhen`) — giá trị vẫn nằm trong form và
vẫn gửi lên. Luật thật nằm ở backend.

### 11.2. Cột CÓ trong bảng nhưng KHÔNG hỏi trên form

| Cột | Vì sao |
|---|---|
| `carry_over_max_days` | Trần số ngày mỗi người được chuyển. **Bỏ khỏi form 07/09/2026**: DEGO không có luật trần (dư bao nhiêu mang hết bấy nhiêu), mà ô đó đứng cạnh chữ *«số dư»* thì đọc mãi vẫn ra "số dư của người này" — trong khi số dư do `balance_service.remaining()` tính, không ai gõ tay. `0` = không giới hạn, và mọi loại đang là `0`. Khai lại ô này nếu công ty đặt trần thật |
| `sort_order` | **Bỏ khỏi form 07/09/2026** — bộ loại nghỉ hơn chục dòng, thứ tự đã seed sẵn; bắt người khai nghĩ ra một con số xếp hạng là hỏi một câu họ không có câu trả lời. Backend vẫn xếp theo nó |
| `carry_over` (bool) | **Di tích.** Công tắc hai nước, đã thay bằng `year_end_mode` (07/09/2026) vì nó không nói được nước thứ ba — *quy đổi*. Đừng đọc, đừng ghi |
| `min_notice_days` | **Di tích.** Luật "phải nộp trước N ngày" đã bỏ 05/09/2026, không còn trong schema lẫn form |

### 11.3. Tám loại nghỉ seed sẵn

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

⚠️ **Nghỉ vợ sinh con** (07/09/2026): trần **14** là mức **cao nhất** của luật
(sinh đôi trở lên, mổ); mức thường là 5, mổ là 7. Máy không biết ca nào nên chỉ
chặn trần — **người duyệt canh phần còn lại**.

### 11.4. Bậc thâm niên (tab riêng)

`tab_leave_type_seniority`, mỗi dòng là *«từ năm thứ A đến dưới năm thứ B: +N ngày»*.
`B = 0` là bậc cuối, không có trần trên. Khoảng **nửa mở**: khớp khi
`A <= thâm niên < B`. Lấy **bậc cao nhất khớp được, KHÔNG cộng dồn**.

## 12. Tra cứu nhanh

| Cần gì | Ở đâu |
|---|---|
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
| HDSD cho người dùng (Help Center) | `backend/scripts/seed_help_nghi_phep.py` — **10 bài** (bản 2, 04/09/2026), chạy `docker compose exec -T api python scripts/seed_help_nghi_phep.py`. Nội dung nằm trong DB **từng môi trường**, chạy script ở môi trường đích thì mới có |
| Bài kiểm | `test/backend/test_nghi_phep_*.py` · `frontend-v2/src/modules/hr/**/leave-*.test.*` |
