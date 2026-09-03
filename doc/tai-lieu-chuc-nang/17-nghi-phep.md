# Nghỉ phép — phân hệ Nhân sự

| | |
|---|---|
| Bản | 1.0 — 03/09/2026 |
| CR | **CR-259** |
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

### Điều chỉnh tay

Cột duy nhất nhận **số âm**. **Ghi ĐÈ, không cộng dồn** — người dùng nhìn con số
hiện tại và gõ con số họ muốn nó thành; cộng dồn thì bấm Lưu hai lần là gấp đôi.
**Bắt buộc có lý do**, ghi vào `tab_audit_log`: đây là thao tác tặng ngày phép.

## 6. Số ngày nghỉ

`workday_service.count_leave_days()` là nơi **duy nhất** tính. Đã trừ thứ Bảy,
Chủ nhật và ngày lễ theo `tab_holiday`.

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
| Báo trước | Nghỉ ốm `0` ngày (không ai biết trước mai mình ốm); phép năm 3 ngày; thai sản 15 ngày. So với **hôm nay**, không với ngày lập đơn |
| Nhập đủ | Chốt ở lúc **gửi duyệt**, không phải lúc lưu nháp — cùng luật với `required-fields.ts` của Thu mua |
| Lập hộ | Được. Cả người lập (`created_by`) lẫn người nghỉ (`employee_id`) đều thấy tờ đơn ở phạm vi «của mình» |

## 8. Duyệt

Chạy trên **bộ máy duyệt dùng chung** (`app/modules/approval/`), entity
`leave_request`. Luồng mẫu do `app/seed_nghi_phep.py` nạp: **trưởng bộ phận của
người xin nghỉ → trưởng phòng Nhân sự**, cả hai chặng đều khai người **dự phòng**.

⚠️ Dự phòng là bắt buộc: luật I08 bỏ người nộp ra khỏi danh sách người duyệt, nên
trưởng phòng tự xin nghỉ thì chặng 1 rỗng — mà quản lý thì cũng phải nghỉ phép.

**Chưa khai luồng thì vẫn nộp được.** Lúc đó `approval_instance_id = 0` và người
có `leave_request.approve` bấm **Duyệt** thẳng ở màn chi tiết. Đơn **đang** chạy
trong luồng thì đường đó bị chặn — không chặn là mở một đường tắt đi vòng qua cả
luồng.

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
| Nghỉ **nửa ngày / theo giờ** | Cột `unit` đã khai sẵn ba giá trị nhưng bản này chỉ dùng *Ngày* (QĐ-NP4). Chờ phân hệ **Lịch làm việc**; lúc đó chỉ thêm cách quy đổi, không đổi cấu trúc bảng |
| **Đính kèm** trên đơn | Cột `require_attachment` của loại nghỉ đã có nhưng chưa nối vào hạ tầng đính kèm |
| Danh sách **bàn giao** trên giao diện | Bảng `tab_leave_handover` và API đã có; form v2 chưa dựng ô nhập (bản chỉ xem thì hiện đủ) |
| **Chuyển phép sang năm sau** | Cờ `carry_over` đã có, mặc định TẮT; chưa có việc chạy cuối năm để chuyển (Q2 chưa chốt) |
| **Báo cáo / thống kê** nghỉ phép | Chưa dựng màn riêng |
| Nạp `hire_date` cho hồ sơ cũ | Phải nhập bù trước khi chạy thật, nếu không thâm niên tính bằng 0 (Q4) |

## 11. Tra cứu nhanh

| Cần gì | Ở đâu |
|---|---|
| Bộ mã số (trạng thái, buổi, đơn vị, giới tính) | `backend/app/modules/leave/constants.py` |
| Công thức đếm ngày công | `backend/app/modules/leave/workday_service.py` |
| Sổ quỹ (bốn nhịp) | `backend/app/modules/leave/balance_service.py` |
| Luật trên tờ đơn | `backend/app/modules/leave/request_service.py` |
| Nối bộ máy duyệt + sinh giấy GNP | `backend/app/modules/leave/approval_bridge.py` |
| Seed loại nghỉ · ngày lễ · luồng | `backend/app/seed_nghi_phep.py` |
| Bộ mã CHUỖI của giấy GNP | `backend/app/core/leave_codes.py` |
| Giao diện | `frontend-v2/src/modules/hr/` (`pages/leave-*`, `components/leave-*`) |
| Gói tri thức Trợ lý AI | `backend/app/modules/assistant/packs/40-nghi-phep.md` |
| Bài kiểm | `test/backend/test_nghi_phep_*.py` · `frontend-v2/src/modules/hr/**/leave-*.test.*` |
