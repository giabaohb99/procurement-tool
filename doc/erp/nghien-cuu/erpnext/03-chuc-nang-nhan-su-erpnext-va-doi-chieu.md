# Chức năng nhân sự của ERPNext và đối chiếu với phân hệ Nhân sự của DEGO ERP

| | |
|---|---|
| **Mã việc** | duoc-CR-707 (tài liệu) · duoc-CR-708 (đổi khung màn chi tiết nhân sự theo ERPNext) |
| **Ngày viết** | 02/11/2026 |
| **Mục đích** | Ghi lại phần nhân sự mà ERPNext có sẵn, rồi đặt cạnh phân hệ Nhân sự của DEGO để biết chỗ nào giống, chỗ nào khác, chỗ nào đáng học. |
| **Nguồn ERPNext** | Repo `dego-holding/nexterp/erpnext` (lõi ERPNext trên Frappe). Đường dẫn trong tài liệu tính từ `erpnext/erpnext/`. |
| **Nguồn DEGO** | `backend/app/modules/employee/`, `leave/`, `work_schedule/`, `labor_contract/`, `frontend-v2/src/modules/hr/`, `doc/erp/hrm/*.md`, `.claude/rules/hr-*.md`. |

> **Giới hạn quan trọng.** Repo `nexterp` chỉ có lõi ERPNext. Từ bản 14, nghỉ phép, chấm công, ca, lương,
> tuyển dụng, đánh giá… được tách sang app riêng **`hrms`** (`frappe/hrms`), và app đó **không có trong
> repo**. Mục 1.2 vì vậy chỉ là kiến thức chung, chưa đối chiếu mã nguồn. Mọi khẳng định khác về
> ERPNext đều có trích tệp.

---

## 1. Phần nhân sự của ERPNext

### 1.1 Các doctype nhân sự còn trong lõi (`setup/doctype/`)

| Doctype | Dùng để làm gì | Trường chính (dấu * là bắt buộc) |
|---|---|---|
| **Employee** | Hồ sơ nhân sự, đồng thời là **cây tổ chức** theo `reports_to` | Xem mục 2 |
| **Employee Education** (bảng con) | Học vấn | `school_univ`, `qualification`, `level`, `year_of_passing`, `class_per`, `maj_opt_subj` |
| **Employee External Work History** (bảng con) | Kinh nghiệm trước khi vào công ty | `company_name`, `designation`, `salary`, `address`, `contact`, `total_experience` |
| **Employee Internal Work History** (bảng con) | Quá trình trong công ty | `branch`, `department`, `designation`, `from_date`, `to_date` |
| **Department** | Phòng ban, dạng cây | `department_name`*, `parent_department`, `company`*, `is_group`, `disabled`. Tên tự gắn thêm viết tắt của công ty (`department/department.py:34`, `get_abbreviated_name`) |
| **Designation** | Chức danh | `designation_name`*, `description` |
| **Branch** | Chi nhánh | `branch`* (chỉ một ô) |
| **Employee Group** | Nhóm nhân sự tự đặt (để lọc, gửi thông báo) | `employee_group_name`*, bảng `employee_list` |
| **Holiday List** | Lịch nghỉ lễ + ngày nghỉ hằng tuần | `holiday_list_name`*, `from_date`*, `to_date`*, `weekly_off` (tự sinh ngày nghỉ trong tuần), `country`/`subdivision` (kéo ngày lễ theo quốc gia), bảng `holidays` (có `is_half_day`) |

Holiday List được tra theo thứ tự: lịch gán trên hồ sơ → lịch mặc định của công ty → báo lỗi
(`employee/employee.py:425-444`, hàm `get_holiday_list_for_employee`). App `hrms` được phép thay hẳn hàm
này qua hook `employee_holiday_list`.

### 1.2 Phần nằm ở app `hrms` (không có trong repo, kiến thức chung)

| Nhóm | Ví dụ doctype | Với DEGO |
|---|---|---|
| Nghỉ phép | Leave Type, Leave Allocation, Leave Application, Leave Policy | DEGO đã tự làm (`modules/leave/`) |
| Chấm công, ca | Attendance, Employee Checkin, Shift Type, Shift Assignment | **Ngoài phạm vi (đã chốt không làm, 16/10/2026)** |
| Lương | Salary Structure, Salary Slip, Payroll Entry | **Ngoài phạm vi (đã chốt không làm, 16/10/2026)** |
| Tuyển dụng | Job Opening, Job Applicant, Job Offer | Chưa có |
| Đánh giá | Appraisal, Appraisal Cycle, Goal | Chưa có |
| Vào làm / nghỉ việc | Employee Onboarding, Employee Separation, Exit Interview | Chưa có quy trình; DEGO có màn kiểm việc treo trước khi khóa tài khoản (duoc-CR-665) |
| Chi phí, tạm ứng | Expense Claim, Employee Advance | Chưa có |
| Điều chuyển, thăng chức | Employee Transfer, Employee Promotion | DEGO làm bằng Quá trình công tác (duoc-CR-585) |

Một hệ HRM tham khảo khác (không phải ERPNext) đã được phân tích ở `doc/erp/tham-khao-hrm/`, đề xuất áp dụng ở
`doc/erp/tham-khao-hrm/10-de-xuat-ap-dung.md`.

---

## 2. Hồ sơ Employee của ERPNext

### 2.1 Bố cục form (theo `field_order` của `employee/employee.json`)

Form có **9 tab**. Trong tab có nhiều **nhóm** (Section), mỗi nhóm chia 2–3 cột (Column Break).

| Tab | Nhóm → trường |
|---|---|
| **Overview** | *(không tên)*: `first_name`*, `middle_name`, `last_name`, `employee_name` (tự ghép), `gender`*, `date_of_birth`*, `salutation`, `date_of_joining`*, `image`, `status`* · **User Details**: `user_id`, `create_user_permission`, `create_user_automatically` · **Company Details**: `company`*, `department`, `employee_number`, `designation`, `reports_to`, `branch` |
| **Address & Contacts** | `cell_number`, `company_email`, `personal_email`, `prefered_contact_email`, `prefered_email` (tự tính), `unsubscribed` · **Address**: địa chỉ hiện tại + thường trú, mỗi cái kèm «thuê / sở hữu» · **Emergency Contact**: tên, số điện thoại, quan hệ |
| **Attendance & Leaves** | `attendance_device_id` (không trùng), `holiday_list` |
| **Salary** | `ctc`, `salary_currency`, `salary_mode` (Bank / Cash / Cheque) · **Bank Details**: `bank_name`, `bank_ac_no`, `iban` (chỉ hiện khi trả qua ngân hàng) |
| **Personal Details** | `marital_status`, `family_background`, `blood_group`, `health_details` · **Passport Details**: số, ngày cấp, hạn, nơi cấp |
| **Profile** | `bio` · ba bảng con: học vấn, kinh nghiệm ngoài, quá trình trong công ty |
| **Joining** | `scheduled_confirmation_date` (ngày offer), `final_confirmation_date` (ngày chính thức), `contract_end_date`, `notice_number_of_days`, `date_of_retirement` |
| **Exit** | `resignation_letter_date`, `relieving_date` (bắt buộc khi trạng thái là Left), `held_on` (phỏng vấn nghỉ việc), `new_workplace`, `leave_encashed` + `encashment_date` · **Feedback**: `reason_for_leaving`, `feedback` |
| **Connections** | Chứng từ liên quan (do app khác gắn vào) |

Ngoài form, khung trang của Frappe có **thanh bên phải** (ảnh, tên, mã, người được giao, tệp đính kèm, thẻ, chia
sẻ, người tạo / sửa) và **bình luận + dòng hoạt động** ở cuối trang. Các nhóm nằm liền nhau trên một mặt phẳng,
ngăn bằng đường kẻ; nhóm phụ như «Chi tiết người dùng» gập / mở được.

### 2.2 Đặt tên, trạng thái, cây

- Mã hồ sơ tự sinh theo dãy `HR-EMP-` (`employee.py:117-119`); trường `employee` luôn bằng mã đó.
- Bốn trạng thái **Active / Inactive / Suspended / Left**. Danh sách mặc định lọc Active và tô màu xanh lá / đỏ /
  cam / xám (`employee/employee_list.js`).
- Employee là `NestedSet` với `nsm_parent_field = "reports_to"` (`employee.py:26`, `115`). Màn cây và sơ đồ tổ
  chức đọc qua `get_children` (`employee.py:567-594`), chỉ lấy người Active.

### 2.3 Luật khi lưu (`employee.py`)

| Luật | Vị trí |
|---|---|
| Tự ghép họ tên từ ba ô | `set_employee_name`, dòng 150-153 |
| Ngày sinh không sau hôm nay; ngày sinh < ngày vào làm < ngày nghỉ hưu / ngày nghỉ việc / ngày hết hợp đồng | `validate_date`, 266-273 |
| Email công ty và email cá nhân phải đúng định dạng | `validate_email`, 275-279 |
| Không được báo cáo cho chính mình | `validate_reports_to`, 371-373 |
| **Chuyển sang Left bị chặn nếu còn người Active đang báo cáo cho mình**, màn liệt kê từng người; và bắt nhập ngày nghỉ việc | `validate_status`, 285-305 |
| Một tài khoản chỉ gắn với một hồ sơ Active | `validate_duplicate_user_id`, 354-369 |
| **Chống leo quyền**: chỉ System Manager được gắn / gỡ / sửa tài khoản đang giữ vai trò quản trị | `validate_user_access`, 170-181 |
| Bật «tạo tài khoản tự động» thì phải có ít nhất một email | `validate_auto_user_creation`, 183-191 |

### 2.4 Đồng bộ hồ sơ ↔ tài khoản

- Gắn tài khoản: tự thêm vai trò **Employee**; chép họ tên (nếu tài khoản chưa có), ngày sinh, giới tính, ảnh
  sang tài khoản (`update_user`, 235-264).
- `create_user_permission` bật thì tạo **User Permission** cho đúng hồ sơ đó và công ty của họ, tức người đó chỉ
  thấy chính mình (`update_user_permissions`, 220-233). Đây là cách ERPNext giới hạn phạm vi dữ liệu theo người.
- Trạng thái khác **Active** (Inactive, Suspended hay Left) thì tài khoản bị tắt; về lại Active thì bật lại,
  nhưng chỉ khi người bấm có quyền sửa User hoặc lần tắt gần nhất là do đổi trạng thái hồ sơ
  (`update_user_status`, 311-334; `can_reenable_user`, 336-352).
- Gỡ tài khoản khỏi hồ sơ: gỡ vai trò Employee và quyền theo người (`validate`, 136-145).
- Chuyển sang Left: tắt luôn Sales Person gắn với người đó (`deactivate_sales_person`, 475-482).
- Nút **Create User** trên form (khi chưa có tài khoản) mở hộp nhập email rồi gọi `create_user`
  (`employee.js:49-96`, `employee.py:484-531`).

### 2.5 Hành vi trên form (`employee.js`)

- Ô Phòng ban chỉ cho chọn phòng của công ty đang chọn; ô Báo cáo cho chỉ cho chọn người Active, trừ chính mình.
- Thanh bên hiện **Sinh nhật** và **Kỷ niệm N năm làm việc** khi trùng ngày (`add_anniversary_indicator`,
  dòng 98-194).
- Đổi công ty thì đổi theo loại tiền lương.

### 2.6 Phân quyền (`employee.json`)

| Vai trò | Quyền |
|---|---|
| HR User, HR Manager | Toàn quyền: tạo, đọc, sửa, xóa, nhập, xuất, in, chia sẻ |
| Employee | Chỉ đọc. Kết hợp User Permission nên thực tế chỉ thấy hồ sơ của mình |
| Accounts, Stock, Projects, Manufacturing, Quality, Delivery, Fleet, Sales Master | Chỉ **chọn** hồ sơ trong ô liên kết, không mở được |

---

## 3. Phân hệ Nhân sự của DEGO (tóm tắt)

| Khối | Có gì | Nguồn |
|---|---|---|
| Hồ sơ | `tab_employee` mở rộng ~30 cột + `extra_fields` (JSON ≤ 20 khóa) + bảng con người báo tin, hộ gia đình. Mã tự sinh `NSU…` | `employee/model.py`, `employee/service.py:229`, `doc/erp/hrm/01-ho-so-nhan-su.md` |
| Trường nhạy cảm | 15 trường (ngày sinh, MST, địa chỉ, ngân hàng, CCCD, BHXH) che ở tầng serializer, khóa `employee_sensitive`; chính chủ luôn thấy đủ | `employee/sensitive.py` |
| Lương trên hồ sơ | `salary_monthly`, `allowance_monthly` — chỉ chính chủ đọc được số; ký HĐLĐ tự chép | duoc-CR-693 |
| Nhiều số điện thoại | `phone` + `extra_phones` (≤ 4 số phụ, có nhãn) | duoc-CR-694, `employee/phone_rules.py` |
| Quản lý trực tiếp | `manager_id`, chặn tự trỏ mình, chặn vòng dài, chặn trỏ hồ sơ không tồn tại | `employee/service.py:145-195` (`block_manager_cycle`) |
| Kiêm nhiệm | `tab_employee_department` (phòng chính + phòng kiêm), mở rộng phạm vi dữ liệu | `employee/department_model.py` |
| Chức vụ | Danh mục `tab_job_position`; mỗi chức vụ có gói vai trò tự cấp | duoc-CR-320, duoc-CR-653 |
| Quá trình công tác | Một bảng sự kiện (vào làm, điều chuyển, bổ nhiệm, kiêm nhiệm, miễn nhiệm, nghỉ việc, khác) kèm tệp quyết định; «Áp» vào hồ sơ | duoc-CR-585, `employee/work_history_*.py` |
| Nghỉ việc | Chuyển sang nghỉ việc / ngừng dùng thì **khóa tài khoản + đá phiên** trong cùng giao dịch; trước đó có màn kiểm việc duyệt đang treo | `employee/service.py:314-335`, duoc-CR-665 |
| Duyệt sửa hồ sơ | Nhân viên tự đề nghị sửa, nhân sự duyệt | `employee/change_request_*.py` |
| Sơ đồ tổ chức | Đọc thẳng phòng ban (có cha) + `manager_id` | duoc-CR-669, `employee/org_chart_controller.py` |
| Nghỉ phép, ngày lễ | Đơn nhiều loại nghỉ, nhiều khoảng ngày, giữ chỗ quỹ phép, duyệt ngay trong màn | `modules/leave/`, `doc/erp/hrm/02-nghi-phep.md` |
| Lịch làm việc | Lịch tuần gán theo hệ thống / pháp nhân / phòng / người; chỉ dùng để tính ngày nghỉ | `modules/work_schedule/`, `doc/erp/hrm/03-lich-lam-viec.md` |
| Hợp đồng lao động | Mẫu Word theo pháp nhân, biến mẫu động, cảnh báo sắp hết hạn | `modules/labor_contract/`, `doc/erp/hrm/04-hop-dong-lao-dong.md` |
| Báo cáo | Kho mẫu 8 nhóm (biến động, HĐ, nghỉ phép, quá trình, hồ sơ thiếu, phúc lợi…), mỗi báo cáo gác thêm `require_report` | `doc/erp/hrm/05-bao-cao-nhan-su.md` |
| Lịch nhắc | Sinh nhật, kỷ niệm 1/3/5/10 năm, HĐ sắp hết trong tháng (Tổng quan Nhân sự) | `employee/monthly_reminders_service.py` |
| Nhập Excel | Qua `import_tool`, có chạy thử và hoàn tác | duoc-CR-628 |

Màn chi tiết `/hr/employees/:id` có 8 tab: Chung · Quá trình công tác · Quyết định bổ nhiệm · Liên hệ & Ngân hàng ·
Giấy tờ & BHXH · Hợp đồng · Quỹ phép · Tài khoản.

---

## 4. Đối chiếu

### 4.1 Theo khối chức năng

| Khối | ERPNext lõi | ERPNext `hrms` (chung) | DEGO | Nhận xét |
|---|---|---|---|---|
| Hồ sơ | Employee ~60 trường | Thêm vài trường | ~45 trường + JSON | DEGO sát pháp lý Việt Nam hơn (CCCD, BHXH, BHYT, dân tộc, MST); ERPNext có hộ chiếu, nhóm máu, ngày offer / chính thức |
| Phạm vi dữ liệu | User Permission theo bản ghi | — | Phạm vi theo vai trò (`own`…`all`) + gán thêm/bớt theo pháp nhân, phòng, người | DEGO mạnh hơn hẳn; ERPNext phải tạo User Permission từng người |
| Trường nhạy cảm | Không phân lớp (`permlevel` mặc định 0) | — | Khóa `employee_sensitive`, che ở serializer | DEGO kỹ hơn |
| Cây tổ chức | `reports_to` + NestedSet | — | `manager_id` + phòng ban có cha | Hai bên cùng ý; DEGO không dùng NestedSet nên không có `lft`/`rgt` |
| Kiêm nhiệm | Không | Không rõ | Có | Chỉ DEGO |
| Chức danh | Designation (tên + mô tả) | — | Chức vụ + gói quyền | DEGO thêm tự cấp quyền theo chức vụ |
| Chi nhánh | Branch | — | Không (có `work_location` dạng chữ) | |
| Nhóm nhân sự | Employee Group | — | Không | |
| Quá trình | 3 bảng con nhập tay | Employee Transfer / Promotion | 1 bảng sự kiện + tệp QĐ + «Áp» vào hồ sơ | DEGO chặt hơn (áp có kiểm tra, khóa tài khoản khi nghỉ) |
| Học vấn | Bảng con | — | Hai ô `education_level` + `major` | ERPNext chi tiết hơn |
| Lịch nghỉ | Holiday List gán theo người / công ty | — | Ngày lễ + lịch làm việc 4 cấp | Tương đương; DEGO linh hoạt hơn về ca tuần |
| Nghỉ phép | — | Có | Có | DEGO tự làm |
| Hợp đồng lao động | Chỉ ô `contract_end_date` | — | Cả phân hệ HĐLĐ | DEGO vượt |
| Chấm công, ca, lương | `attendance_device_id`, `ctc` | Có | Không | **Ngoài phạm vi (đã chốt không làm)** |
| Tuyển dụng, đánh giá, onboarding | — | Có | Không | Chưa có nhu cầu |

### 4.2 Từng trường của hồ sơ

**Có ở cả hai:** họ tên (ERPNext tách 3 ô, DEGO một ô `full_name`) · giới tính (DEGO thêm «Khác») · ngày sinh ·
ngày vào làm (ERPNext bắt buộc, DEGO để trống được) · trạng thái · ảnh (DEGO lấy từ tài khoản) · tài khoản
(ERPNext `user_id` trên hồ sơ, DEGO `tab_user.employee_id` trỏ ngược) · công ty · phòng ban · chức danh / chức vụ ·
quản lý trực tiếp · số điện thoại · email công ty · email cá nhân · địa chỉ hiện tại · địa chỉ thường trú ·
người liên hệ khẩn cấp (ERPNext 3 ô phẳng, DEGO bảng con) · tình trạng hôn nhân · tên ngân hàng · số tài khoản ·
quá trình trong công ty · ngày nghỉ việc (`relieving_date` ↔ `resign_date`) · lương (`ctc` ↔ `salary_monthly`).

**Chỉ ERPNext:** `salutation` · `employee_number` · `branch` · `create_user_permission` · `create_user_automatically` ·
`prefered_contact_email` / `prefered_email` · `unsubscribed` · kiểu nhà ở (thuê / sở hữu) × 2 · `attendance_device_id`* ·
`holiday_list` (DEGO gán lịch qua màn Lịch làm việc) · `salary_currency`* · `salary_mode`* · `iban` · `blood_group` ·
`family_background` · `health_details` · hộ chiếu (4 ô) · `bio` · học vấn (bảng) · kinh nghiệm ngoài (bảng) ·
`scheduled_confirmation_date` · `final_confirmation_date` · `contract_end_date` (DEGO nằm ở HĐLĐ) ·
`notice_number_of_days` · `date_of_retirement` (DEGO tính ở báo cáo `legal_watch_retirement.py`) ·
`resignation_letter_date` · `held_on` · `new_workplace` · `leave_encashed` + `encashment_date` · `reason_for_leaving` ·
`feedback`. *(dấu * = thuộc chấm công / lương, ngoài phạm vi.)*

**Chỉ DEGO:** nơi sinh · dân tộc · tôn giáo · số con · MST cá nhân · trình độ học vấn · chuyên ngành · hình thức
nhân viên · cấp bậc · nơi làm việc · nhãn số chính + số điện thoại khác · chủ tài khoản · chi nhánh ngân hàng ·
CCCD (số, ngày cấp, nơi cấp, ngày hết hạn, 2 ảnh) · số BHXH · nơi / mã KCB BHYT · hộ gia đình (bảng) · phụ cấp ·
chữ ký (trên tài khoản) · `extra_fields` · cờ «Đang dùng» (`is_active`, tách khỏi tình trạng làm việc).

### 4.3 Luật

| Luật | ERPNext | DEGO |
|---|---|---|
| Tự làm quản lý / báo cáo cho chính mình | Chặn (`employee.py:371-373`) | Chặn (`employee/service.py:162-163`) |
| Vòng quản lý A→B→A | Không thấy kiểm trong `employee.py`; có thể do NestedSet của Frappe (thư viện ngoài repo, **chưa kiểm**) | Chặn cả vòng dài, chạm trần 50 cấp cũng chặn (`service.py:167-195`) |
| Nghỉ việc khi còn cấp dưới trỏ vào mình | **Chặn**, liệt kê từng người (`employee.py:285-303`) | **Không chặn**. Chỉ khi xóa hồ sơ mới gỡ `manager_id` của cấp dưới về 0 (`service.py:578`). Đơn của cấp dưới sẽ lùi về trưởng bộ phận |
| Nghỉ việc phải có ngày nghỉ | Bắt buộc (`employee.py:304-305`) | Không bắt buộc; màn chỉ nhắc «nhớ đổi cả ô Tình trạng». Báo cáo sổ lao động bỏ qua người nghỉ mà thiếu ngày (`labor_register/people_data.py:6`) |
| Thứ tự ngày (sinh < vào làm < nghỉ) | Chặn (`employee.py:266-273`) | Chưa kiểm |
| Khóa tài khoản khi nghỉ | Tắt tài khoản khi không còn Active | Khóa + đá phiên mọi thiết bị trong cùng giao dịch, có màn kiểm việc duyệt treo trước (duoc-CR-665) |
| Mở lại tài khoản | Có luật ai được bật lại (`can_reenable_user`) | Mở khóa ở tab Tài khoản (gói quyền theo chức vụ được cấp lại) |
| Một tài khoản – một hồ sơ | Chặn trùng `user_id` với hồ sơ Active | Email công việc là email đăng nhập, chặn trùng (`ensure_email_unique`) |
| Chống leo quyền khi gắn tài khoản | Chỉ System Manager được đụng tài khoản quản trị | Gói quyền theo chức vụ cấm vai trò quản trị, không tự cấp cho chính mình (duoc-CR-653) |
| Trạng thái lưu dạng | Chữ tiếng Anh | Mã chuỗi tiếng Anh (`official`, `collaborator`, `maternity_leave`, `resigned`) — ngoại lệ B-03 của luật R2 |

### 4.4 Bố cục màn chi tiết

| ERPNext | DEGO sau duoc-CR-708 |
|---|---|
| Một mặt phẳng, nhóm ngăn bằng đường kẻ, ô nền xám, nhóm phụ gập / mở | **Đã có**: không thẻ con, tiêu đề nhóm chữ thường, ô nền xám, Lương và Kiêm nhiệm gập / mở |
| Thanh bên phải: ảnh, tên + mã, người được giao, thẻ, tệp, người tạo / sửa, Sinh nhật / Kỷ niệm | **Đã có**: thanh bên phải với ảnh, tên + mã, chức vụ, phòng ban, quản lý trực tiếp, công ty, ngày vào làm + thâm niên, Sinh nhật / Tròn N năm làm việc, lần cập nhật cuối (không có giao việc / thẻ / chia sẻ) |
| Tiêu đề + nhãn trạng thái tô màu + nút bên phải | **Đã có**: tên + nhãn tình trạng (xanh lá / xanh dương / hổ phách / xám, thêm nhãn đỏ «Ngừng dùng») + In / Lưu / Xóa |
| Tab Overview (cơ bản + tài khoản + công ty) | Tab **Chung**: nhóm Thông tin cá nhân · Công việc · **Vào làm & nghỉ việc** (tách theo tab Joining / Exit) · Lương · Kiêm nhiệm. Nhóm xếp 3 cột khi đủ rộng |
| Address & Contacts | Liên hệ & Ngân hàng |
| Personal Details + Passport | Giấy tờ & BHXH (CCCD thay hộ chiếu) |
| Profile (học vấn, kinh nghiệm, quá trình) | Quá trình công tác + Quyết định bổ nhiệm |
| Joining, Exit | Gộp vào nhóm «Vào làm & nghỉ việc» của tab Chung; HĐ ở tab Hợp đồng |
| Attendance & Leaves, Salary | Quỹ phép (+ lịch làm việc); không có chấm công / tính lương |
| Connections | Không có tab riêng |
| Dòng hoạt động cuối trang | Lịch sử thao tác cuối trang |

---

## 5. Đề xuất có thể học

Đã loại trừ chấm công, ca và lương.

| Ưu tiên | Đề xuất | Lý do |
|---|---|---|
| **Cao** | Chặn (hoặc ít nhất cảnh báo trong hộp xác nhận nghỉ việc) khi còn người đang có `manager_id` trỏ vào hồ sơ sắp nghỉ, liệt kê từng người như ERPNext | Hiện người nghỉ vẫn là «quản lý trực tiếp» của cấp dưới; đơn của họ âm thầm lùi về trưởng bộ phận, không ai biết phải gán lại. Có sẵn hộp kiểm việc treo (duoc-CR-665) để gắn thêm mục này |
| **Cao** | Bắt nhập Ngày nghỉ việc khi chuyển sang «Nghỉ việc» (hoặc tự điền hôm nay) | Thiếu ngày thì sổ quản lý lao động và báo cáo biến động bỏ sót người đó |
| **Trung bình** | Kiểm thứ tự ngày: ngày sinh < ngày vào làm ≤ ngày nghỉ việc | Rẻ, chặn được lỗi gõ năm |
| **Trung bình** | Ghi thông tin nghỉ việc: ngày nộp đơn, lý do nghỉ (mã số theo luật R2) | Phục vụ báo cáo nghỉ việc và giữ chân; ERPNext có cả tab Exit |
| **Trung bình** | Ngày chính thức (hết thử việc) trên hồ sơ, hoặc lấy từ HĐ thử việc | Báo cáo thâm niên, phép năm đầu |
| **Thấp** | Bảng học vấn chi tiết (trường, bằng, năm) | Chỉ cần khi làm hồ sơ năng lực |
| **Thấp** | Chi nhánh (Branch) và nhóm nhân sự tự đặt (Employee Group) | Chưa có nhu cầu; `work_location` đang đủ |
| **Thấp** | Nhóm máu, liên hệ y tế | Tùy chính sách an toàn lao động |
| Đã làm | Thanh bên, nhãn trạng thái, Sinh nhật / Kỷ niệm trên màn chi tiết | duoc-CR-708 |

---

## 6. Câu hỏi còn treo

1. Hai đề xuất ưu tiên Cao ở mục 5 (chặn nghỉ việc khi còn cấp dưới; bắt nhập ngày nghỉ) có làm không, và chặn
   cứng hay chỉ cảnh báo?
2. Có cần cài thêm app `hrms` vào `nexterp` để đối chiếu phần nghỉ phép bằng mã nguồn thật không?
