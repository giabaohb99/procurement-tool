> **BẢN NHÁP — chỉ để tham khảo.** Agent nghiên cứu viết ngày 02/11/2026 (duoc-CR-709). Một số chỗ thiếu trích dẫn hoặc sai so với mã;
> bản đã kiểm lại với mã là [`../04-hrms-chuc-nang-va-lien-ket.md`](../04-hrms-chuc-nang-va-lien-ket.md) — khi hai bên khác nhau thì tin bản 04.

# Nghiên cứu Frappe HRMS — Nghỉ phép & Chấm công

**Ngày:** 02/11/2026 | **Phạm vi:** Mã nguồn HRMS develop (ffadbbf 01/11/2026) | **Mục đích:** So sánh với hệ nghỉ phép DEGO hiện tại

---

## I. NGHỈ PHÉP (trọng tâm)

### Leave Type — Danh mục Loại nghỉ

**Dùng để:** Khai báo các loại nghỉ (phép năm, ốm, cưới hỏi, tang chế, v.v.) kèm luật cụ thể cho từng loại.

**Trường chính:** `leave_type_name` (tên) · `max_leaves_allowed` (hạn mức năm) · `max_continuous_days_allowed` (trần mỗi lần) · `applicable_after` (được phép xin sau N ngày)

**Các cờ:**
- `is_lwp` — Không lương (trừ tiền)
- `is_earned_leave` — Cộng dần theo tháng/quý (không cấp sẵn năm đầu)
- `is_carry_forward` — Chuyển năm sau (không bao giờ hết hạn nếu `0`)
- `is_compensatory` — Nghỉ bù khi làm ngày lễ
- `is_ppl` — Trả lương một phần (`fraction_of_daily_salary_per_leave`)
- `include_holiday` — Tính ngày lễ vào số ngày nghỉ (ví dụ: 01/01 là ngày lễ + 2 ngày phép = 3 ngày)
- `allow_encashment` — Quy đổi ra tiền (+ `earning_component` liên kết lương)
- `allow_negative` — Ứng phép (không kiểm đủ số dư)

**Luồng:** Chỉ tạo/sửa bởi HR Manager. Dữ liệu, không có submit.

**Liên kết:** Nút tạo trên leave_application.js khi chọn loại mới → mở form Leave Type. `Leave Allocation` + `Leave Application` đều FK tới Leave Type. Xóa loại chặn nếu còn quỹ phép nào của nó.

### Leave Period — Kỳ nghỉ

**Dùng để:** Định vòng cấp phép (ví dụ: 01/01 – 31/12/2026).

**Trường chính:** `period_name` · `from_date` · `to_date` · `company` · `is_active`

**Luồng:** Setup, không submit.

**Liên kết:** `Leave Allocation` FK tới Leave Period. Khi tạo Leave Allocation, chọn period để hệ tính ngày hết hạn của `carry_forward`.

### Leave Policy — Gói chính sách nghỉ phép

**Dùng để:** Gom danh sách các loại nghỉ + số ngày cho mỗi loại thành một gói, để gán hàng loạt.

**Trường chính:** `title` (tên gói) · Bảng `leave_policy_details` (loại nghỉ + số ngày)

**Ví dụ:** Gói «Standard 2026» có: Phép năm 12 ngày + Ốm 5 ngày + Cưới 3 ngày.

**Luộ:** Chỉ tạo/sửa bởi HR Manager. Nút _Create Leave Allocations_ ở form tạo Allocation cho tất cả nhân viên theo gói này.

**Liên kết:** `Leave Policy Assignment` gán gói này cho một nhân viên → tự tạo dòng Allocation.

### Leave Policy Assignment — Gán gói chính sách

**Dùng để:** Gán một gói `Leave Policy` cho một nhân viên (hoặc nhóm theo điều kiện).

**Trường chính:** `employee` (hoặc Employee Grade để gán hàng loạt) · `leave_policy` (chỉ tên gói) · `effective_from` (ngày bắt đầu)

**Luồng:** Nháp → Submit → hệ thống tự tạo dòng Allocation cho từng loại có trong gói.

**Liên kết:** `on_submit` → `leave_policy_assignment_tool.create_leave_allocations()`; xem `assignment.py`. Hoàn tác (amend): không xóa Allocation đã tạo (phân quyền người dùng). Nút «Create Allocations» tay ở màn danh sách để tạo lại nếu cần.

### Leave Allocation — Cấp quỹ phép

**Dùng để:** Ghi hồ sơ: nhân viên X được Y ngày phép loại Z trong kỳ từ ngày A đến ngày B.

**Trường chính:** `employee` · `leave_type` · `new_leaves_allocated` (số ngày cấp) · `from_date` · `to_date` · `leave_policy_assignment` (nếu từ gói)

**Các cột khác:**
- `carry_forward` — Số ngày chuyển từ năm trước
- `total_leaves_allocated` — Tổng = cấp + chuyển
- `expired` — Đã hết hạn (auto update khi LLE tạo)
- `leave_period` — Kỳ (tự tìm từ ngày)

**Luồng:** Nháp → Submit → tạo dòng Leave Ledger Entry (_"Allocation"_ type) để ghi số dư.

**Liên kết:** Submit → `create_leave_ledger_entry()` ở `leave_ledger_entry.py`. Amend = xóa dòng LLE cũ + tạo mới. Nút _Add_ ở Leave Allocation để thêm từng dòng tay (HR không thích gói cố định).

**Luật đáng chú ý:** `allow_over_allocation` (cấp được vượt hạn mức) · `carry_forward` không nhân đôi mỗi lần lưu lại (dữ liệu không thay đổi = giữ nguyên).

### Leave Ledger Entry — Sổ cái quỹ phép

**Dùng để:** Ghi mọi tác động tới quỹ phép: cấp, xin, hủy, hết hạn, quy đổi. Là bảng cấp độ chi tiết, không có form màn hình.

**Trường chính:** `employee` · `leave_type` · `transaction_type` · `leaves` (số ngày ±) · `from_date` · `to_date`

**transaction_type:** `Allocation` (cấp) · `Leave Application` (xin) · `Leave Encashment` (quy đổi) · `Leave Expiry` (hết hạn) · `Leave Transfer` (chuyển).

**Ví dụ dòng:**
```
Allocation:  employee=E001, leave_type=Phép năm, leaves=+12, from_date=01/01, to_date=31/12
Leave App:   employee=E001, leave_type=Phép năm, leaves=-2, from_date=10/09, to_date=11/09
Leave Expiry: employee=E001, leave_type=Phép năm carry_forward, leaves=-3 (hết hạn 31/03)
```

**Cách tạo:** Tự động bởi:
- Allocation `on_submit` → dòng _"Allocation"_
- Leave Application `on_submit` (trạng thái Approved) → dòng _"Leave Application"_
- Leave Encashment `on_submit` → dòng _"Encashment"_
- Holiday List `on_validate` + scheduler → dòng _"Leave Expiry"_ (chạy qua đêm)

**Tính số dư:** `Leave Balance` = SELECT SUM(leaves) FROM Leave Ledger Entry GROUP BY (employee, leave_type). Không lưu thành cột vì sẽ lệch khi có transaction mới. Hàm: `get_leave_balance()` ở `leave_balance.py`.

### Leave Application — Đơn xin nghỉ phép

**Dùng để:** Nhân viên nộp đơn xin nghỉ, quản lý duyệt → trừ quỹ.

**Trường chính:** `employee` (FK) · `leave_type` · `from_date` · `to_date` · `half_day` (nghỉ nửa ngày) · `total_leave_days` (tính tự động) · `leave_balance` (tính từ LLE)

**Luồng:** Nháp → Submit (lúc này phải set `status` = Approved/Rejected) → nếu Approved thì tạo LLE (`transaction_type=Leave Application`, `leaves=-N`).

**Trạng thái:** `Open` (đơn mới) · `Approved` (duyệt xong) · `Rejected` (từ chối) · `Cancelled` (hủy).

**Các cờ:**
- `follow_via_email` — Gửi email tới người duyệt
- `is_optional_leave` — Loại tùy chọn (không bắt buộc chọn nếu không có ngày lễ)

**Liên kết:** `leave_approver` tự tìm từ `Employee.leave_approver` (người duyệt mặc định). Amend (sửa đơn đã duyệt) khá phức tạp vì phải:
1. Xóa dòng LLE cũ (hoàn số dư)
2. Tạo dòng LLE mới (trừ quỹ lại theo dữ liệu mới)
3. Nếu đơn trước đó tạo Attendance với status _"On Leave"_ thì cập nhật lại.

**Luật chặn đáng chú ý:**
- `validate_balance_leaves()` — Kiểm đủ quỹ (chừa nếu `allow_negative=1`)
- `validate_leave_overlap()` — Chặn nếu cùng người đã có đơn khác chồng ngày (même leave type)
- `validate_block_days()` — Kiểm Leave Block List (ngày chặn)
- `validate_salary_processed_days()` — Chặn nếu Salary Slip đã xử lý kỳ đó (không sửa được sau xử lý lương)
- `validate_optional_leave()` — Chỉ áp nếu ngày đó là ngày lễ tùy chọn

**Ghi kỳ (backdated application):** Đơn xin hôm qua hoặc trước đó. Code kiểm `validate_back_dated_application()` để xem có Attendance record nào rồi không; nếu có thì phải update lại.

### Compensatory Leave Request — Nghỉ bù (làm ngày lễ)

**Dùng để:** Nhân viên làm việc vào ngày lễ → yêu cầu nghỉ bù một ngày bình thường (sau đó).

**Trường chính:** `employee` · `leave_type` (phải có `is_compensatory=1`) · `work_date` (ngày làm) · `compensatory_date` (ngày xin bù)

**Luộng:** Nháp → Submit → tạo Leave Allocation tự động (cấp 1 ngày loại bù) · Sau đó nhân viên gửi Leave Application để xin nghỉ ngày bù.

**Liên kết:** `on_submit` → `leave_allocation_tool.create_leave_allocation()`. Hoàn tác: xóa Allocation đã tạo nếu chưa bị xài.

### Leave Block List — Danh sách ngày chặn

**Dùng để:** HR ghi danh sách ngày nhất định không được phép xin nghỉ (ví dụ: những ngày close năm tài chính, ngày kiểm toán).

**Trường chính:** `block_list_name` · `company` · `purpose` (ghi chú) · Bảng `leave_blocks` (ngày từ/đến)

**Luộng:** Setup.

**Liên kết:** Khi xin Leave Application, hệ kiểm `get_applicable_block_dates(employee, from_date, to_date)` → chặn nếu ngày xin nằm trong danh sách.

### Holiday List — Lịch ngày lễ

**Dùng để:** Khai danh sách ngày lễ (Tết, 30/4, 02/9, v.v.) và ngày nghỉ mỗi tuần (T7/CN).

**Trường chính:** `holiday_list_name` · `from_date` · `to_date` · `weekly_off` (chọn T7 hoặc CN, hoặc cả hai) · Bảng `holidays` (mỗi hàng: ngày lễ + tên + `is_optional`)

**Ví dụ dòng holiday:**
```
holiday_date=01/01/2026, holiday_name="Tết Dương lịch"
holiday_date=10/02/2026, holiday_name="Tết Âm lịch" (ngày âm, phải nhập tay mỗi năm)
```

**Cơ chế gán:** Mỗi company/employee có một Holiday List; hệ tìm Holiday List áp dụng bằng `get_holiday_list_for_employee(employee)` → xem `employee.holiday_list` hoặc mặc định của company.

**Liên kết:** Khi xin Leave Application, nếu `include_holiday=1` cho loại đó, hệ sẽ:
1. Tìm ngày lễ trong khoảng `[from_date, to_date]`
2. Cộng vào tổng ngày ($\text{ngày_đề_cập} = \text{calendar_days} + \text{số ngày lễ trong khoảng}$)
3. Tính công thật (dùng lịch làm việc): Giảm T7/CN + ngày lễ = số công = số phép tính

**Luật:** `is_half_day` (có nửa ngày lễ không — hiếm) · `is_optional` (lễ tùy chọn, không bắt buộc) · `repeat_yearly` (lặp hằng năm).

**Scheduler:** Mỗi đêm, `update_leave_expiry()` chạy → tìm Carry Forward leaves hết hạn theo `expire_carry_forwarded_leaves_after_days` + Holiday List `to_date` → tạo dòng LLE kiểu _"Leave Expiry"_.

---

## II. CA & CHẤM CÔNG (ngoài phạm vi DEGO — mô tả sơ qua)

Nghỉ phép được tính toán dựa trên **công làm việc thật**, không theo công tắc. Do đó Attendance + Shift ảnh hưởng tới:
1. Số ngày nghỉ (nửa buổi hay cả ngày)
2. Tính công bù khi làm ngày lễ (Compensatory Leave)

### Attendance — Chấm công (4 dòng)

**Dùng để:** Ghi hạng (có/vắng/ốm) của một nhân viên một ngày. Tạo tay hoặc tự động từ `Employee Checkin`.

**Kết nối với Leave:** Khi Leave Application Approved, hệ có thể tạo Attendance tự động với `status=On Leave` (tùy cấu hình). Xin lại đơn (amend) = cập nhật Attendance.

### Shift Type & Shift Assignment — Ca làm việc

**Dùng để:** Định ca làm (sáng 8:00–12:00, chiều 13:00–17:00, hay ca đêm, ca 24h). Gán ca cho nhân viên.

**Kết nối với Leave:** Lịch ca quy định «buổi nào là sáng» để hệ tính:
- Nghỉ buổi sáng = 0.5 ngày (không phải 1.0 ngày)
- Có lịch ca đặc biệt (ca đêm) thì tính công khác biệt

DEGO đã chốt không làm chấm công/ca, nên **mục này chỉ để biết luồng liên kết**.

---

## III. SƠ ĐỒ DÒNG CHẢY QUỸ PHÉP (Frappe)

```
       Năm T              Năm T+1
         │                 │
    ┌────┴─────────────┐   │
    │  Leave Policy    │   │
    │  (gói chính)     │   │
    └────┬─────────────┘   │
         │                 │
    ┌────▼──────────────────────┐
    │ Leave Policy Assignment   │◄─── Gán hàng loạt theo Grade
    │ (nhân viên + từ ngày)     │
    └────┬──────────────────────┘
         │
         │ on_submit → tạo
         ▼
    ┌────────────────────────────┐
    │ Leave Allocation           │ ◄── Cấp Y ngày loại Z
    │ (X= people, Y= days, Z=type)
    │ new_leaves_allocated       │
    │ carry_forward (từ năm trước)
    │ total_leaves_allocated     │
    └────┬────────────────────────┘
         │ on_submit → tạo LLE
         │
    ┌────▼─────────────────────────────────────────┐
    │ Leave Ledger Entry (Allocation)              │
    │ leaves = +new_leaves_allocated + carry_fwd   │
    └────┬─────────────────────────────────────────┘
         │
         │ Số dư = SUM(LLE.leaves) GROUP BY employee, leave_type
         │
    ┌────▼───────────────────────────┐
    │   Nhân viên có X ngày phép      │
    └────┬───────────────────────────┘
         │
    ┌────▼──────────────────────┐
    │ Leave Application         │ ◄── Xin N ngày
    │ from_date, to_date        │
    │ status = Approved/Rejected│
    └────┬───────────────────────┘
         │ on_submit (approved) → tạo LLE
         │
    ┌────▼──────────────────────────┐
    │ Leave Ledger Entry (App)       │
    │ leaves = -N (trừ quỹ)         │
    └────┬──────────────────────────┘
         │
    ┌────▼──────────────────────────────┐
    │ Số dư = X - N (hay X - pending)   │
    │ pending_days (khi chờ duyệt)      │
    └───────────────────────────────────┘

    ┌──────────────────────────────────┐
    │ Leave Encashment (quy đổi → lương│
    │ status = Draft/Submitted/Paid    │
    │ on_submit → tạo LLE (Encashment) │
    │ leaves = -M, Salary Slip tạo sẵn │
    └──────────────────────────────────┘

    ┌──────────────────────────────────┐
    │ Holiday List → Scheduler         │
    │ (scheduler update_leave_expiry)  │
    │ → tạo LLE (Expiry) khi hết hạn   │
    │ leaves = -X (mất phần mang sang)  │
    └──────────────────────────────────┘
```

---

## IV. BẢNG SO SÁNH: ERPNext/Frappe vs DEGO

| Chức năng | Frappe HRMS | DEGO (hiện tại) | Ghi chú |
|-----------|------------|-----------------|--------|
| **Cấp phép năm** | Leave Allocation submit → tạo LLE | `leave_balance` (nhưng chưa LLE) | DEGO: số dư tính động, không lưu cột |
| **Giữ chỗ (reserve)** | Không: chỉ kiểm balance khi submit | `pending_days` (bắt buộc) | DEGO: trừ ngay lúc gửi duyệt |
| **Xin phép** | Leave Application → status Approved/Rejected | `tab_leave_request` (6 trạng thái) | DEGO: thêm «Trả về chỉnh sửa» |
| **Sổ cái** | Leave Ledger Entry (bảng tự động) | (không có, tính qua `remaining_days()`) | DEGO: tính thời gian thực từ app+pending+balance |
| **Số dơi** | LLE.leaves = +Alloc, -App, -Expiry | app.used + pending + balance logic | DEGO: cộng 4 nhịp (reserve/consume/release/refund) |
| **Duyệt nhiều tầng** | Workflow (approve flow không bắt buộc) | approval_instance + approval_switch | DEGO: bộ máy duyệt dùng chung + luồng riêng per công ty |
| **Một đơn nhiều loại** | Không (một app = một loại) | `tab_leave_request_line` | DEGO: CR-683 thêm khả năng này |
| **Nhiều khoảng ngày** | Không (một app = một khoảng [from, to]) | `tab_leave_request_period` | DEGO: CR-683 cho phép 1–20 khoảng |
| **Tính ngày theo lịch làm việc** | `get_holiday_dates_for_employee()` + Holiday List | `workday_service.count_leave_days()` + lịch làm việc 4 cấp | DEGO: tính theo ca làm + T7/CN + lễ |
| **Kết sổ năm** | Scheduler không, chặn vượt `maximum_carry_forwarded_leaves` | Nút «Kết sổ năm» tay ở màn Quỹ phép | DEGO: chạy lại được, vét lọt được, hỗ trợ 3 nước (mất/mang sang/quy đổi) |
| **Ứng phép** | `allow_negative` = cho phép (khác ứng thực sự) | Chặn hẳn khi gửi duyệt (QĐ-NP2) | DEGO: khác HRMS, không có nợ dài hạn |
| **Đơn bắt buộc đính kèm** | Không có cơ chế | `tab_leave_request.require_attachment` + kiểm ở submit | DEGO: CR-661 thêm cơ chế gọng này |
| **Hạn chế đã biết** | Chưa xử lý nhiều loại + khoảng đơn như DEGO | (Không có giới hạn, nhưng Frappe chưa làm) | DEGO: phải đi vào các chi tiết cụ thể |

---

## V. NHỮNG ĐIỂM ĐÁN MỨC CAO CẤP

1. **Khoảng ngày khe (CR-683 DEGO):** Frappe HRMS chưa có. DEGO dùng `tab_leave_request_period` với OUTER JOIN để tìm ngày thật nghỉ (bỏ ngày khe). Frappe chỉ theo [from_date, to_date] = cả khoảng.

2. **Earning Leave Scheduler:** Frappe chạy hàng tháng/quý để tự cộng, DEGO không làm vì «hệ không có bộ chạy nền, mà nó hỏng thì tháng Ba mới phát hiện» (QĐ-NP4).

3. **Luồng duyệt:** Frappe có Workflow tùy chọn (không bắt buộc), DEGO có bộ máy duyệt bắt buộc + luồng + approval_switch.

4. **Tài liệu xuất gia đình:** DEGO tạo Giấy Nghỉ Phép (GNP) tự động khi Approved, Frappe chỉ tạo Attendance `on_submit`.

5. **Dịch vụ phạm vi dữ liệu:** Frappe chưa có bậc phạm vi (own/dept/company/all) như DEGO, hệ chỉ có quyền vai trò cơ bản.

---

## VI. UNRESOLVED QUESTIONS

- **Paid Leave Components:** Frappe `earning_component` trỏ tới Salary Component (lương), nhưng DEGO không liên kết với lương (bao-CR-688 là báo cáo quỹ lương, không ghi trữ). Chưa rõ Frappe triển khai Encashment như thế nào khi có bảng công + Salary Slip.
- **Leave vs Attendance Sync:** Khi Leave Application approved ở Frappe, hệ có tạo Attendance nào không? Code `update_attendance()` chỉ là stub (empty). DEGO tạo tài liệu GNP, không biết có tạo Attendance hay không.
- **Scope Mapping:** Bộ máy duyệt DEGO dùng `entity_context` và luật tìm người duyệt («Trưởng phòng nhân sự»), Frappe chỉ có `leave_approver` từ hồ sơ người. Chưa biết cách Frappe cấu hình luồng duyệt dành cho một company cụ thể (CA AGC case) như DEGO.

