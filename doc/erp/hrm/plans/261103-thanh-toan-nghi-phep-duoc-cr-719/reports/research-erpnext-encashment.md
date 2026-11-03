# Nghiên cứu: Leave Encashment của ERPNext và chỗ khớp vào DEGO

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | planner | Hiệu lực | duoc-CR-719 |

Nguồn ERPNext: `nexterp/hrms/hrms/hr/doctype/leave_encashment/` (`.py`, `.json`, `.js`, `test_leave_encashment.py`),
`leave_type/leave_type.json`, `leave_ledger_entry.py`, `hr/utils.py:326` (`generate_leave_encashment`), `hooks.py:282-305`,
`full_and_final_statement.py:247,429`, `patches/v15_0/rename_and_update_leave_encashment_fields.py`.

## 1. Cấu hình trên Loại nghỉ (`leave_type.json`)

| Trường ERPNext | Kiểu | Nghĩa | DEGO đặt tên |
|---|---|---|---|
| `allow_encashment` | Check | Loại này được đổi ra tiền | `allow_encashment` Bool |
| `max_encashable_leaves` | Int | Trần số ngày cho MỘT phiếu | `max_encashable_days` Float — **trần theo NĂM** (người chủ nói "tối đa mỗi năm") |
| `non_encashable_leaves` | Int | Số ngày phải giữ lại, không đổi (tên cũ `encashment_threshold_days`, đổi ở v15) | `non_encashable_days` Float |
| `earning_component` | Link | Khoản lương nhận tiền (chỉ khi trả qua bảng lương) | Không làm — DEGO không có lương (memory: không làm chấm công, lương) |

## 2. Phiếu Leave Encashment (submittable, `is_submittable = 1`)

Trường chính: `employee`, `leave_type` (lọc `allow_encashment = 1`), `leave_period`, `encashment_date` (mặc định hôm nay),
`leave_allocation`, `leave_balance` (chỉ đọc), `actual_encashable_days` (chỉ đọc), `encashment_days` (sửa được, không vượt
actual), `encashment_amount`, `pay_via_payment_entry`, `payable_account`, `expense_account`, `paid_amount`,
`status` = Draft / Unpaid / Paid / Submitted / Cancelled, `additional_salary`.

Luật (`leave_encashment.py`):
- `validate`: nhân sự không ở trạng thái Inactive (`validate_active_employee` — người **Left** vẫn lập được);
  `encashment_date = encashment_date or today`; tính lại chi tiết.
- `set_leave_balance`: `balance = total_leaves_allocated − carry_forwarded_leaves_count + leaves_taken_trong_kỳ` →
  **phần mang sang KHÔNG được đổi ra tiền**; không có allocation → lỗi.
- `set_actual_encashable_days`: không `allow_encashment` → lỗi; `actual = balance − non_encashable` (kẹp 0) rồi
  `min(actual, max_encashable)`.
- `set_encashment_days`: bỏ trống → lấy `actual`; vượt `actual` → lỗi.
- `set_encashment_amount`: số ngày × `leave_encashment_amount_per_day` của cơ cấu lương → **DEGO không làm** (người chủ chốt:
  phiếu chỉ ghi số ngày, số tiền do người có quyền tài chính nhập sau, không lộ lương).
- `before_submit`: số tiền phải > 0 → DEGO dời chốt này sang **lúc gửi duyệt YCTT** (số tiền nằm ở YCTT).
- `on_submit`: trả qua Payment Entry (`pay_via_payment_entry=1` → ghi sổ cái công nợ phải trả cho **Employee**) hoặc qua
  Additional Salary; cộng `total_leaves_encashed` của allocation; ghi Leave Ledger Entry `−days`. Kỳ đã hết và loại không mang
  sang → ghi thêm dòng `+days` đảo phần đã hết hạn.
- `on_cancel`: hủy Additional Salary, trừ `total_leaves_encashed`, đảo sổ cái, xóa ledger entry → **trả lại ngày**.
- `set_status`: docstatus 1 → Unpaid nếu `encashment_amount > paid_amount`, ngược lại Paid.
- Không có luật "một phiếu mỗi kỳ"; phiếu sau tự nhỏ đi vì số dư đã trừ (ledger), nhưng trần áp theo từng phiếu.

**Ánh xạ sang DEGO:** `pay_via_payment_entry` (công nợ phải trả cho nhân viên rồi chi bằng Payment Entry) chính là ý
người chủ chốt ở QĐ 3 — tạo **YCTT** cho kế toán chi như mọi khoản chi khác. Trạng thái Unpaid / Paid của ERPNext ở DEGO là
trạng thái của YCTT đi kèm (đọc dẫn xuất, không lưu hai nơi).

## 3. Ai lập (quyền doctype)

| Vai trò | read | create | write | delete | submit | cancel |
|---|---|---|---|---|---|---|
| System Manager, HR Manager, HR User | có | có | có | có | **có** | có |
| Employee | có | có | có | có | **không** | không |

PWA tự phục vụ (`hrms/frontend/src/views`) chỉ có leave / expense_claim / employee_advance / attendance / salary_slip — **không
có** Leave Encashment. Nghĩa là: nhân viên lập nháp được (trên desk), chỉ Nhân sự mới gửi (submit) được. DEGO: nhân viên tự lập
phạm vi **của mình** + Nhân sự lập hộ; duyệt đi bộ máy duyệt dùng chung, quyền `approve` chỉ ở `hr_leave` (D3).

## 4. Tự động và liên kết

- `generate_leave_encashment` (lịch chạy hằng ngày, cờ HR Settings `auto_leave_encashment`) lập NHÁP cho mọi allocation vừa hết
  hạn của loại cho phép đổi. DEGO không có bộ chạy nền (cùng lý lẽ `ensure_balance`, `close_year`) → **không làm**.
- Full and Final Statement (nghỉ việc) gom Leave Encashment vào khoản phải trả. DEGO không có F&F → dùng lý do **Nghỉ việc**
  trên phiếu (Điều 113 khoản 3 BLLĐ 2019: thôi việc mà chưa nghỉ hết phép năm thì được trả tiền những ngày chưa nghỉ).

## 5. Bài kiểm của ERPNext đáng chép ý

`test_non_encashable_leaves_setting`, `test_max_encashable_leaves_setting`, cả hai cùng lúc,
`test_creation_of_leave_ledger_entry_on_submit`, `test_unused_leaves_after_leave_encashment_for_carry_forwarding_leave_type`
(mang sang: đổi 5/10 thì còn 5, kết kỳ không mất thêm), `test_leave_expiry_after_leave_encashment_for_non_carry_forwarding`,
`test_status_on_discard`.

## 6. Chỗ khớp ở DEGO

| Ý ERPNext | DEGO hiện có | Việc |
|---|---|---|
| Leave Allocation theo kỳ | `tab_leave_balance` theo **năm dương lịch** (Kỳ nghỉ phép không làm — CR-717) | Phiếu chốt `balance_year` |
| `total_leaves_encashed` | chưa có | Cột `tab_leave_balance.encashed_days` vào công thức còn lại |
| Leave Ledger Entry `−days` | `used_days` / `pending_days` | Gửi duyệt giữ chỗ `pending_days`, duyệt chuyển sang `encashed_days` |
| Hủy → trả ngày | khuôn `revoke_days` của phiếu nghỉ bù | `encashed_days −= days` |
| Payment Entry cho Employee | YCTT (`payment_request`) chỉ dành cho NCC + công nợ | Mở rộng tối thiểu: nguồn `leave_encashment`, người nhận là nhân sự, chặn xem (D1) |
| Kỳ kết thúc, loại không mang sang → đảo phần hết hạn | Kết sổ cuối năm là nút bấm, vét phần còn lại | Phiếu năm cũ lập trước khi kết sổ; đã kết sổ thì số dùng được = 0 tự chặn |

## 7. Vì sao YCTT hiện tại KHÔNG vừa nguyên trạng cho nhân viên

- Phiếu gắn **một NCC** (`supplier_code`), dòng gắn **khoản công nợ** (`payable_id`, mã PO, số hóa đơn); `check_submit` bắt mọi
  dòng khớp công nợ còn nợ; `set_status('paid')` cộng tiền vào công nợ và đẩy tiến độ ĐMH.
- Ai đọc YCTT: Nhân viên thu mua / Quản lý thu mua / phòng tự mua phạm vi **công ty** hoặc **tất cả** (seed dòng 373–457).
  Thả YCTT thanh toán nghỉ phép vào đó = cả phòng thu mua thấy **số tiền ÷ số ngày = lương ngày** của từng người — trái QĐ 2 và
  luật ô lương CR-693 (chỉ chính chủ đọc được số).
- Bản in lấy số tài khoản theo NCC; số tài khoản nhân viên là trường nhạy cảm (`employee_sensitive`).
- Không có vai trò Kế toán trong seed: chuỗi Duyệt → Đã chi của YCTT hiện do Quản lý thu mua bấm.

Kết luận: vừa được nếu thêm (1) nguồn `leave_encashment` + người nhận là nhân sự + liên kết ngược, (2) nhánh riêng ở gửi duyệt /
chi tiền / nạp lại / xóa, (3) **một chốt chặn xem đặt ở `scoping.scope_condition`** để mọi đường đọc YCTT (danh sách, chi tiết,
xuất Excel, tập dữ liệu AI, chuông duyệt) đều qua. Phần đánh đổi ghi ở D1 / D2 của `plan.md`.

## Câu hỏi chưa giải
- Công ty đã có vai trò Kế toán trên prod chưa (seed không có)? Nếu chưa, quản trị phải dựng vai trò có `payment_request`
  read/write/approve/print + `leave_encashment.read` phạm vi công ty.
- Nghỉ việc giữa năm với loại cấp đủ năm (FULL_YEAR): luật có bắt tỷ lệ theo tháng làm không? Plan để Nhân sự sửa số ngày xuống.
