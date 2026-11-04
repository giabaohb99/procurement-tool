> **BẢN NHÁP — chỉ để tham khảo.** Agent nghiên cứu viết ngày 02/11/2026 (duoc-CR-709). Một số chỗ thiếu trích dẫn hoặc sai so với mã;
> bản đã kiểm lại với mã là [`../04-hrms-chuc-nang-va-lien-ket.md`](../04-hrms-chuc-nang-va-lien-ket.md) — khi hai bên khác nhau thì tin bản 04.

### Hệ thống Nhân sự Frappe HRMS: HR Setup & Tenure/Vòng đời

Tài liệu mô tả kiến trúc quản lý hồ sơ nhân sự (Employee Lifecycle) trong Frappe HRMS từ tuyển dụng → tiếp nhận → điều chuyển/thăng chức → nghỉ việc → quyết toán.

---

### I. Cơ sở dữ liệu (HR Setup)

#### 1. Employee (Hồ sơ Nhân sự)
Dùng để lưu thông tin nhân viên, tích hợp quyền duyệt và lịch sử công tác.
- **Doctype**: `Employee` (override từ lõi ERPNext ở `hrms/overrides/employee_master.py:EmployeeMaster`)
- **Trường chính**:
  - `employee` (tên), `employee_name` (bắt buộc), `company`, `department`, `designation`
  - `job_offer`, `job_applicant` (từ tuyển dụng)
  - `leave_approver`, `expense_approver` (người duyệt)
  - `date_of_joining`, `relieving_date`, `status` (Active/Left/...)
  - `internal_work_history` (bảng, ghi lịch công tác)
  - `held_on` (ngày interview khi exit)
  - `ctc` (Cost-to-Company)
- **Luồng**: Tạo ngoài onboarding flow (hoặc qua `make_employee` từ Employee Onboarding)
- **Liên kết**: `validate_onboarding_process` hook cập nhật `employee` field khi Job Offer → Employee Onboarding thành Completed
- **Luật chặn**: `emp_created_by` ở HR Settings xác định naming (Naming Series / Employee Number / Full Name)

#### 2. Employee Grade (Cấp bậc)
Xác định mức lương cơ sở và chính sách cấp cho từng nhân viên.
- **Doctype**: `Employee Grade`
- **Trường chính**: `name`, `description`
- **Liên kết**: Gán cho `employee.employee_grade`, được copy khi Employee Onboarding → Employee

#### 3. Department, Designation, Branch
Phân loại cơ bản cho nhân viên.
- **Department** (override HRMS): `leave_approvers`, `expense_approvers`, `shift_request_approver` (bảng + field)
- **Designation** (lõi ERPNext): Chức danh
- **Branch**: Chi nhánh công ty

#### 4. HR Settings (Cấu hình)
Điều khiển hành vi toàn hệ (reminders, leave, approval, etc.).
- **Doctype**: `HR Settings` (single doctype)
- **Cấu hình quan trọng**:
  - `emp_created_by`: Cách đặt tên Employee (Naming Series / Employee Number / Full Name)
  - `retirement_age`: Tuổi nghỉ hưu (default 60)
  - `standard_working_hours`: Giờ làm tiêu chuẩn
  - **Reminders**: `send_birthday_reminders`, `send_work_anniversary_reminders`, `send_holiday_reminders` (bật/tắt)
  - `frequency`: Tần suất nhắc (dùng mục tiêu nhắc theo ngày trong tuần)
  - **Leave**: `auto_leave_encashment`, `leave_approver_mandatory_in_leave_application`, `prevent_self_leave_approval`
  - **Exit**: `exit_questionnaire_web_form`, `exit_questionnaire_notification_template`

#### 5. Organizational Chart (Trang)
Hiển thị sơ đồ tổ chức dạng cây (quản lý → nhân viên).

---

### II. Vòng đời Nhân viên (Tenure)

#### 2A. Tiếp nhận (Employee Onboarding)
Quản lý danh sách công việc từ khi nhân viên ký Job Offer tới khi tạo Employee record.
- **Doctype**: `Employee Onboarding`
- **Trường chính** (bắt buộc: job_offer, employee_name, date_of_joining):
  - `job_offer` (bắt buộc, status="Accepted", docstatus=1)
  - `job_applicant` (auto-fetch từ job_offer)
  - `employee_onboarding_template` → auto-fill `activities` (nếu có template)
  - `company`, `department`, `designation`, `employee_grade`, `holiday_list`
  - `date_of_joining`, `boarding_begins_on`
  - `activities` (bảng EmployeeBoardingActivity: task, description, required_for_employee_creation)
  - `project` (tạo auto từ template hoặc template → project)
  - `boarding_status` (Pending → In Process → Completed, read-only)
  - `employee` (populate sau khi tạo)
  - `notify_users_by_email` (gửi email tới approvers)
- **Luồng**:
  1. Draft onboarding từ Job Offer (`make_onboarding` hay tay)
  2. Chọn template → populate activities
  3. Submit → activities sinh Project + Task (qua EmployeeBoardingController)
  4. **Nút "Create Employee"**: gọi `make_employee` mapper (chỉ available khi docstatus=1 & !employee)
     - `validate_employee_creation()`: Kiểm **tất cả mandatory tasks** phải Completed/Cancelled
     - Ánh xạ: job_offer.applicant_email → Employee.personal_email, job_offer → Employee.job_offer, status="Active"
  5. Employee được insert → hook `validate_onboarding_process` (ở employee_master.py:40-48) cập nhật boarding_status ← "In Process"
  6. Nút "Mark as Completed": Set status Completed cho tất cả task, project → status Completed, boarding_status ← "Completed"
- **Connections**: Xuất hiện ở Employee tab "Lifecycle" (qua dashboard_overrides.py:21-27)
- **Luật chặn** (`employee_onboarding.py:58-67`):
  - Không được tạo 2 Employee Onboarding cho cùng 1 job_offer (docstatus != 2)
  - Job Offer phải status="Accepted", docstatus=1

#### 2B. Điều chuyển (Employee Transfer)
Thay đổi công ty, phòng ban hoặc tạo ID nhân viên mới cho cùng người.
- **Doctype**: `Employee Transfer`
- **Trường chính** (bắt buộc: employee, transfer_date):
  - `employee`, `employee_name` (auto), `company` (auto), `new_company`
  - `transfer_date` (bắt buộc)
  - `transfer_details` (bảng EmployeePropertyHistory: fieldname, current, new → ghi lịch thay đổi)
  - `department` (phòng ban mới)
  - `create_new_employee_id` (tạo Employee mới hoặc update cái cũ), `new_employee_id`
  - `reallocate_leaves` (phân bổ lại ngày phép)
- **Luồng**:
  1. Draft với employee + transfer_date
  2. Điền transfer_details (chẳng hạn: department, company, salary_structure)
  3. Submit → `on_submit` (`employee_transfer.py:46-73`):
     - Nếu `create_new_employee_id=True`: Copy employee → mới (new_employee.status="Left"), move user_id từ cũ → mới
     - Nếu `False`: Update fields trực tiếp trên employee cũ
     - Call `update_employee_work_history(...)` → ghi internal_work_history
     - Nếu new_company khác company: Set company, date_of_joining → transfer_date
  4. on_cancel: Restore internal_work_history, khôi phục employee status
- **Luật chặn** (`employee_transfer.py:39-44`):
  - transfer_date phải ≤ hôm nay (không submit trước)
  - `update_employee_transfer` hook (employee_master.py:142-146): Xóa Employee → xóa new_employee_id khỏi Transfer đó

#### 2C. Thăng chức (Employee Promotion)
Cập nhật chức vụ, phòng ban, lương.
- **Doctype**: `Employee Promotion`
- **Trường chính** (bắt buộc: employee, promotion_date):
  - `employee`, `employee_name` (auto), `company` (auto)
  - `promotion_date` (bắt buộc)
  - `promotion_details` (bảng EmployeePropertyHistory: fieldname, current, new)
  - `current_ctc`, `revised_ctc` (lương cũ/mới)
  - `salary_currency`
- **Luồng**:
  1. Draft employee + promotion_date + details (designation, department, ctc, ...)
  2. Submit → `on_submit` (`employee_promotion.py:48-55`):
     - `validate_active_employee`: Employee phải status="Active"
     - Call `update_employee_work_history(...)` → ghi internal_work_history
     - Nếu revised_ctc: Set employee.ctc ← revised_ctc
  3. on_cancel: Restore internal_work_history, ctc ← current_ctc
- **Luật chặn**:
  - promotion_date phải ≤ hôm nay (trước submit)
  - Employee phải Active (không Left)

#### 2D. Nghỉ việc (Employee Separation + Exit Interview + Full and Final)
Quản lý toàn bộ exit process: khai báo → phỏng vấn → quyết toán.

**2D1. Employee Separation**
Theo dõi các công việc khi nhân viên rời công ty (tương tự Onboarding).
- **Doctype**: `Employee Separation` (inherit EmployeeBoardingController)
- **Trường chính**:
  - `employee` (bắt buộc), `employee_name`, `company` (bắt buộc)
  - `resignation_letter_date`, `boarding_begins_on` (ngày bắt đầu exit process)
  - `employee_separation_template` → auto-fill `activities`
  - `activities` (bảng: clearance, asset return, doc handover, etc.)
  - `project`, `boarding_status` (Pending → In Process → Completed)
- **Luồng**: Tương tự Employee Onboarding (template → tasks → project)
- **Connections**: Xuất hiện ở Employee tab "Employee Exit"

**2D2. Exit Interview**
Lấy phản hồi từ nhân viên đang rời.
- **Doctype**: `Exit Interview`
- **Trường chính** (bắt buộc: employee, status, date):
  - `employee`, `employee_name` (auto), `company`
  - `email` (auto-set từ employee)
  - `status` (Pending → Scheduled → Completed / Cancelled) (bắt buộc)
  - `date` (ngày phỏng vấn), `relieving_date` (auto từ employee)
  - `department`, `designation`, `reports_to`, `date_of_joining`
  - `ref_doctype`, `reference_document_name` (nếu có document liên quan)
  - `questionnaire_email_sent`, `interviewers` (bảng Interviewer), `interview_summary`
  - `employee_status` (Employee Retained / Exit Confirmed)
- **Luồng**:
  1. Draft employee + status
  2. Submit → `on_submit` (`exit_interview.py:74-78`):
     - Kiểm status phải = "Completed"
     - Update `employee.held_on` ← date
  3. on_cancel: Xóa held_on
- **Luật chặn** (`exit_interview.py:49-68`):
  - Employee phải có relieving_date (không được null)
  - Chỉ 1 Exit Interview per employee (không trùng lặp ngoài docstatus=2)

**2D3. Full and Final Statement**
Quyết toán tài sản, nợ lương, hoàn trả tạm ứng.
- **Doctype**: `Full and Final Statement`
- **Trường chính** (bắt buộc: employee, transaction_date):
  - `employee`, `employee_name`, `company`
  - `transaction_date`, `relieving_date`
  - `department`, `designation`, `date_of_joining`
  - `status` (Unpaid / Paid / Cancelled)
  - `payables` (bảng FullandFinalOutstandingStatement: nợ lương, tạm ứng, ...)
  - `receivables` (bảng: phải hoàn trả, nợ công ty)
  - `assets_allocated` (bảng FullandFinalAsset: tài sản, action=Return/Recover Cost)
  - `total_payable_amount`, `total_receivable_amount`, `total_asset_recovery_cost`
- **Luồng**:
  1. Auto-populate `payables`, `receivables` từ Salary Slip, Expense Claim, Employee Advance, Loan
  2. Auto-populate `assets_allocated` từ Asset Assignment
  3. Settlement: Chỉnh lại status từ "Unsettled" → settled (bằng tay hoặc auto-generate payable/receivable)
  4. Submit → `on_submit` (`full_and_final_statement.py:62-63`):
     - Validate: Tất cả payables/receivables phải settled (không có status="Unsettled")
     - Validate: Assets có action=Return phải status="Return" (not "Owned")
     - Call `process_loan_accrual(...)` → tính nợ vay
  5. on_cancel: Call `cancel_loan_repayment(...)` → khôi phục
- **Luật chặn**:
  - relieving_date phải có
  - Không submit nếu còn unsettled payable/receivable
  - Assets Return phải xác nhận trả

#### 2E. Kỹ năng & Đào tạo (Employee Skill Map, Training)

**2E1. Employee Skill Map**
Lập bản đồ kỹ năng của nhân viên + đào tạo tham gia.
- **Doctype**: `Employee Skill Map`
- **Trường chính** (unique: employee):
  - `employee` (unique), `employee_name` (read-only), `designation` (read-only)
  - `employee_skills` (bảng Employee Skill: skill name, proficiency)
  - `trainings` (bảng Employee Training: training event, date_completion, trainer, feedback)
- **Liên kết**: Được update khi Training Result submit (sau khi nhân viên hoàn training)

**2E2. Training Program**
Mô tả chương trình đào tạo (không nhân sự cụ thể).
- **Doctype**: `Training Program`
- **Trường chính**:
  - `training_program` (tên, unique, bắt buộc), `company` (bắt buộc)
  - `status` (Scheduled / Completed / Cancelled), `description`
  - `trainer_name`, `trainer_email`, `supplier`, `contact_number`

**2E3. Training Event**
Sự kiện đào tạo cụ thể (ngày, địa điểm, danh sách nhân viên).
- **Doctype**: `Training Event`
- **Trường chính**:
  - `event_name` (unique, bắt buộc), `training_program`, `type` (Seminar/Workshop/Conference/Exam/Internal/External)
  - `event_status` (Scheduled / Completed / Cancelled, bắt buộc)
  - `has_certificate` (dùng khi type=Seminar/Workshop/...)
  - `company`, `location`, `start_time`, `end_time`
  - `trainer_name`, `trainer_email`, `supplier`, `contact_number`
  - `course` (liên kết tới LMS nếu có), `introduction`
  - `employees` (bảng Training Event Employee: employee, attended=Yes/No)
  - `employee_emails` (auto-compute)

**2E4. Training Feedback & Training Result**
Ghi kết quả sau training.
- **Training Feedback**: Phản hồi từ trainer
- **Training Result**: Ghi điểm/pass/fail, update Employee Skill Map

#### 2F. Khiếu nại Nhân viên (Employee Grievance)
Theo dõi khiếu nại, điều tra, giải quyết.
- **Doctype**: `Employee Grievance`
- **Trường chính** (bắt buộc: raised_by, grievance_type, date, description):
  - `subject`, `raised_by` (employee nêu khiếu), `employee_name` (auto)
  - `grievance_type` (bắt buộc), `date` (bắt buộc)
  - `status` (Open → Investigated → Resolved / Invalid / Cancelled)
  - `description` (bắt buộc)
  - `cause_of_grievance` (mandatory nếu status=Investigated/Resolved)
  - `grievance_against_party` (nhân viên/phòng ban bị khiếu nại)
  - `associated_document_type`, `associated_document` (document liên quan)
  - `resolution_detail`, `resolved_by`, `resolution_date`, `employee_responsible`
  - `designation`, `reports_to` (auto)
- **Luồng**: Open (nộp) → Investigated (điều tra, ghi cause) → Resolved (ghi resolution)
- **Connections**: Xuất hiện ở Employee tab "Lifecycle" (fieldname=raised_by)

#### 2G. Lịch sử Tài sản (Employee Property History, Boarding Activity)
Ghi chép các thay đổi thuộc tính (transfer, promotion) và hoạt động (onboarding, separation).
- **Employee Property History** (bảng): `fieldname`, `current`, `new`, `date` (dùng trong Transfer, Promotion)
- **Employee Boarding Activity** (bảng): `task` (Link tới Task), `description`, `required_for_employee_creation` (chỉ onboarding), `status`

---

### III. Scheduler & Nhắc việc

Tại `hrms/hooks.py:263-287`:
- **daily**: `send_birthday_reminders`, `send_work_anniversary_reminders`
- **weekly**: `send_reminders_in_advance_weekly` (dùng cho leave, expense, shift chuẩn bị tuần tới)
- **monthly**: `send_reminders_in_advance_monthly` (dùng cho leave, expense, shift chuẩn bị tháng tới)

---

### IV. Sơ đồ Vòng đời Nhân viên

```
┌─────────────────────────────────────────────────────────────────┐
│                    VÒNG ĐỜI NHÂN VIÊN FRAPPE                   │
└─────────────────────────────────────────────────────────────────┘

[RECRUITMENT PHASE]
Job Applicant → Job Offer (status=Accepted)
         ↓
[ONBOARDING PHASE]
Job Offer → Employee Onboarding (doctype)
         → Create Project + Task
         → [Nút "Create Employee"] → Employee (active)
         → boarding_status = Completed

[ACTIVE WORK PHASE]
         → Employee Transfer (điều chuyển / tạo ID mới)
            ↓ internal_work_history
         → Employee Promotion (thăng chức)
            ↓ internal_work_history
         
         → Employee Skill Map + Training Event + Training Result
            ↓ Kỹ năng

         → Employee Grievance (khiếu nại → giải quyết)

[SEPARATION PHASE]
         → Employee.relieving_date = X (mark as Left)
         → Employee Separation (nếu dùng template)
            ↓ Project + Task checklist
         
         → Exit Interview (phỏng vấn, status=Completed)
            ↓ Update employee.held_on
         
         → Full and Final Statement
            ↓ Settle payables, receivables, assets
            → status = Paid

[END OF EMPLOYMENT]
         Employee.status = Left
         Employee.relieving_date = set
```

---

### V. So sánh DEGO vs Frappe HRMS

| Chức năng | DEGO đã có | Gợi ý học | Lý do |
|-----------|-----------|-----------|------|
| **Hồ sơ nhân sự** | Có (tích hợp HRM); quá trình công tác ghi tay 6 loại sự kiện (bổ nhiệm, điều chuyển, ...) kèm quyết định + nút áp vào hồ sơ | Cao: Copy cách lưu `internal_work_history` + `employee_property_history` | DEGO ghi tay có khó maintain, HRMS auto-ghi từ doctype |
| **Employee Onboarding** | KHÔNG | TB: Tiếp nhận gồm activities → project → task checklist | Tối ưu: Tránh miss công việc, automate reminder |
| **Employee Transfer** | KHÔNG (chuyên qua quá trình công tác ghi tay) | TB: Code `create_new_employee_id` + `internal_work_history` mô hình | Cho phép chuyển công ty hoặc tạo ID mới mà keep lịch sử |
| **Employee Promotion** | Ghi bằng "Bổ nhiệm" (quá trình công tác), không tính ctc | Cao: Auto cập nhật ctc + internal_work_history + validation | HRMS có quy trình validation (promotion_date ≤ hôm nay, Active employee) |
| **Employee Grievance** | KHÔNG | Thấp: Nếu DEGO không có khiếu nại, có thể defer | Tùy quy trình HR công ty |
| **Exit Interview** | KHÔNG (chỉ có quá trình dừa "Kết thúc HĐLĐ") | TB: Auto-fetch relieving_date, ghi held_on, status Completed check | Tối ưu: Chính thức ghi ngày phỏng vấn, tránh miss |
| **Full and Final** | KHÔNG | Cao: Gom payables, receivables, assets; validate settlement trước submit | Toàn diện: 1 doctype thay vì scattering trong nhiều chỗ |
| **Employee Skill Map** | KHÔNG (học thêm qua Training Event / Training Result) | TB: Nếu DEGO đã track qua Training thì có thể defer | Tối ưu: Map skill nhân viên ↔ job requirement |
| **Training Program + Event** | KHÔNG | Cao: Template, auto-fill employees; Training Feedback; Certificate | Tối ưu: Track attend, feedback, kết quả formal |
| **HR Settings** | Có (cấu hình reminders, leave, ...) | Cao: HRMS có template sẵn (sender email, frequency, ...) | DEGO có thể copy cấu hình khung |
| **Scheduler** | KHÔNG (DEGO không có birthday/anniversary nhắc auto) | Cao: `send_birthday_reminders`, `send_work_anniversary_reminders` daily | Tối ưu: Tự động gửi email, không cần thủ công |
| **Chấm công** | Ngoài phạm vi | — | DEGO chốt KHÔNG làm |
| **Lương / Phiếu lương** | Ngoài phạm vi | — | DEGO chốt KHÔNG làm |

---

### Unresolved Questions

1. Liệu DEGO có muốn áp dụng Employee Onboarding template-based với Project + Task checklist, hay giữ nguyên quá trình công tác ghi tay?
2. Grievance process có bắt buộc hay optional?
3. Full and Final Statement có cần settlement workflow chi tiết hay simple mark as Paid?
4. Có dùng Employee Grade để gán Salary Structure automatic hay manual assignment?
5. Có cần Training Event → Certificate → lưu vào Employee Profile không?
