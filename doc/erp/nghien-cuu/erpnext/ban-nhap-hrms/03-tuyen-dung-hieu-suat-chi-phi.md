> **BẢN NHÁP — chỉ để tham khảo.** Agent nghiên cứu viết ngày 02/11/2026 (duoc-CR-709). Một số chỗ thiếu trích dẫn hoặc sai so với mã;
> bản đã kiểm lại với mã là [`../04-hrms-chuc-nang-va-lien-ket.md`](../04-hrms-chuc-nang-va-lien-ket.md) — khi hai bên khác nhau thì tin bản 04.

# Frappe HRMS: Tuyển Dụng, Hiệu Suất, Chi Phí & Công Tác

## 1. TUYỂN DỤNG (Recruitment)

### 1.1 Kế Hoạch Tuyển Dụng — Staffing Plan

**Dùng để**: Xác định định biên (số chỗ cần tuyển) theo chức danh × phòng ban × khoảng thời gian; kiểm soát không vượt quá ngân sách.

**Doctype**: `Staffing Plan` + `Staffing Plan Detail` (bảng con)

**Trường chính**:
- `company` (bắt buộc): Công ty
- `department`: Phòng ban
- `from_date`, `to_date`: Khoảng thời gian kế hoạch
- `staffing_details`: Bảng gồm:
  - `designation` (bắt buộc): Chức danh
  - `vacancies` (bắt buộc): Số chỗ cần tuyển
  - `estimated_cost_per_position`: Chi phí dự tính/1 vị trí
  - `current_count` (chỉ xem): Tính tự động từ số nhân viên Active hiện tại
  - `current_openings` (chỉ xem): Tính tự động từ Job Opening mở
  - `number_of_positions` (chỉ xem): = vacancies + current_count
  - `total_estimated_cost` (chỉ xem): = vacancies × estimated_cost_per_position
- `total_estimated_budget` (chỉ xem): Tổng chi phí của cả kế hoạch

**Luồng trạng thái**: Draft → Submit. Có thể `Amend` (sửa lại lần khác).

**Nút/Liên kết chính**:
- **«Get Job Requisitions»** (nút): Nạp Job Requisition vào chi tiết (chép designation, vacancies, expected_compensation).
- **Kiểm chặn**: Không cho phép 2 Staffing Plan cùng designation × company × khoảng thời gian chồng lắp; kiểm validate vacancies không vượt quá kế hoạch của công ty cha (nếu có cây công ty).

**Chưa kiểm**: Ghi lại DB mapping từ staffing_details vào field nào.

---

### 1.2 Yêu Cầu Tuyển Dụng — Job Requisition

**Dùng để**: Nộp formal từng yêu cầu tuyển dụng từ phòng ban; track giai đoạn tuyển (draft → submitted → filled/cancelled).

**Doctype**: `Job Requisition`

**Trường chính** (chưa kiểm):
- Designation, số lượng cần tuyển, expected compensation.
- Status: Draft / Open / Filled / Cancelled.

**Liên kết**:
- Job Opening tham chiếu Job Requisition; khi Job Opening đóng → Job Requisition status → "Filled".
- Nạp vào Staffing Plan qua nút «Get Job Requisitions».

---

### 1.3 Tin Tuyển — Job Opening

**Dùng để**: Mở tin tuyển dụng, optionally publish lên website, track số lượng applicant.

**Doctype**: `Job Opening`

**Trường chính**:
- `job_title` (bắt buộc): Tên chức danh hiển thị
- `company`, `designation` (bắt buộc): Công ty, Chức danh hệ thống
- `department`, `employment_type`, `location` (Branch): Chi tiết vai trò
- `status` (Open/Closed): Trạng thái tin tuyển
- `staffing_plan`, `planned_vacancies` (chỉ xem): Link tới Staffing Plan tương ứng (tìm tự động dựa designation + company + ngày); chỉ cho phép mở tin nếu `number_of_positions` (staffing plan) > `current_count + current_openings` (tức còn chỗ trống)
- `job_requisition`, `vacancies` (chỉ xem): Từ Job Requisition
- `publish` (checkbox): Công khai lên website
- `route`: URL slug nếu publish
- `description`, `lower_range`, `upper_range`, `currency`, `salary_per`: Mô tả công việc, mức lương
- `closes_on`, `closed_on`: Hạn chót + ngày đóng tin
- `prevent_duplicate_applicant`: Cấm apply lại cùng email

**Luồng**:
1. Lập Job Opening → Validate `staffing_plan` tự động
2. Publish = Công khai trên website (route = `/jobs/{company}/{job_title}`)
3. Status: Open → Closed (bằng nút hay lập lịch tự động nếu `closes_on` đã qua)
4. Đóng tin (status = Closed) → Job Requisition status → "Filled" + lưu ngày đóng (`closed_on`)

**Nút**:
- «Close Job Opening» / «Reopen Job Opening»: Toggle trạng thái. Khi đóng, cảnh báo nếu chưa đủ định biên.

**Liên kết**:
- Khi chọn `designation` + `company` → tự tìm Staffing Plan đang hoạt động cho khoảng ngày hôm nay.
- Job Opening Template: Nạp mẫu để tự điền description, salary, etc.

---

### 1.4 Hồ Sơ Ứng Viên — Job Applicant

**Dùng để**: Lưu thông tin ứng viên, track trạng thái (Open → Replied → Shortlisted → Accepted/Rejected), ghi chú đánh giá.

**Doctype**: `Job Applicant`

**Trường chính**:
- `applicant_name`, `email_id` (bắt buộc): Tên, email ứng viên
- `phone_number`, `country`: Liên hệ
- `job_title`: Link tới Job Opening mà ứng viên apply
- `designation`: Chức danh (chép từ Job Opening hoặc nhập thêm)
- `status` (bắt buộc): Open / Replied / Shortlisted / Rejected / Hold / Accepted
- `source`: Nguồn tuyển (Job Applicant Source; nếu từ Website thì "Website Listing", nếu từ referral thì "Employee Referral")
- `source_name`: Employee referral (nếu source = "Employee Referral")
- `employee_referral`: Link tới Employee Referral record (chưa kiểm cấu trúc)
- `applicant_rating`: Điểm tự định (1-5 sao)
- `resume_attachment`, `resume_link`: Tệp CV hoặc link
- `cover_letter`, `notes`: Thư xin việc, ghi chú (notes = chỉ xem, từ Interview tổng hợp?)
- `lower_range`, `upper_range`, `currency`: Mức lương kỳ vọng

**Luồng trạng thái**:
- Open (mới apply) → Replied (liên hệ) → Shortlisted (lọc) → Accepted / Rejected / Hold
- Job Applicant status ←→ Employee Referral status (nếu có source_name):
  - Job Applicant status ∈ {Open, Replied, Hold} → Employee Referral status = "In Process"
  - Job Applicant status ∈ {Accepted, Rejected} → Employee Referral status = tương ứng

**Kiểm chặn**:
- Không cho apply vào Job Opening đã Closed
- Nếu Job Opening `prevent_duplicate_applicant` = True → không cho apply 2 lần cùng email

**Nút/Hàm Whitelist**:
- **`create_interview(job_applicant, interview_type)`**: Tạo Interview từ Job Applicant với một Interview Type.
- **`schedule_interview(job_applicant, interview_type, scheduled_on, from_time, to_time, interviewers)`**: Tạo + Schedule Interview luôn.
- **`make_employee(job_applicant)`**: Mapper → Employee (tệp:dòng chưa kiểm).
  - Chép: applicant_name → first_name, email_id → personal_email, phone_number → cell_number, currency → salary_currency
  - Nếu Job Opening có thông tin → lấy company, department, employment_type sang
- **`get_interview_details(job_applicant)`**: Lấy danh sách Interview liên quan + rating.
- **`get_applicant_to_hire_percentage()`**: Tính % applicant có status = "Accepted".
- **Kanban Board**: Job Applicant có Kanban view với các cột Open/Replied/Shortlisted/Accepted, hiển thị designation + applicant_rating.

**Onload**:
- Nạp `job_offer` (Job Offer record liên quan) và `employee` (Employee nếu đã được hire).

---

### 1.5 Phỏng Vấn — Interview

**Dùng để**: Lên lịch và ghi chép phỏng vấn ứng viên; người phỏng vấn cho điểm từng ứng viên.

**Doctype**: `Interview` + `Interview Detail` (bảng người phỏng vấn)

**Trường chính**:
- `interview_type` (bắt buộc): Interview Type (ví dụ "Round 1", "Final Round"; có thể binding tới designation nhất định)
- `job_applicant` (bắt buộc): Job Applicant
- `job_opening` (chỉ xem): Fetch từ job_applicant.job_title
- `designation` (chỉ xem): Fetch từ interview_type.designation
- `status` (mặc định "Pending"): Pending / Under Review / Cleared / Rejected / Cancelled
- `scheduled_on` (bắt buộc): Ngày phỏng vấn
- `from_time`, `to_time` (bắt buộc): Giờ bắt đầu — kết thúc
- `interview_details`: Bảng chứa:
  - `interviewer` (Link → User): Người phỏng vấn
- `average_rating` (chỉ xem, cho phép sửa sau submit): Điểm trung bình từ Interview Feedback
- `expected_average_rating` (chỉ xem): Fetch từ interview_type
- `interview_summary`: Text; nhân viên HR ghi tóm tắt (allow_on_submit)
- `resume_link`: Fetch từ job_applicant (hoặc nhập thủ công)
- `reminded`: Đã gửi lời nhắc hay chưa

**Luồng trạng thái**: Draft → Submit. Có thể Amend.
- Status chuyển từ Pending → Under Review → Cleared / Rejected / Cancelled.

**Liên kết**:
- **Interview Feedback**: Link doctype tới Interview (mối quan hệ 1:N).
  - Mỗi người phỏng vấn lập riêng 1 Interview Feedback để ghi điểm + nhận xét.
  - `average_rating` của Interview = trung bình các Interview Feedback.
- Interview Type có trường `expected_average_rating` để so sánh.

**Nút**:
- Hàm `get_interviewers(interview_type)`: Lấy danh sách người phỏng vấn từ Interview Type.

**Chưa kiểm**: Cách nhân viên Tuyển Dụng tạo Interview từ Job Applicant, liệu có Kanban hay form để match ứng viên ↔ Interview Type.

---

### 1.6 Phản Hồi Phỏng Vấn — Interview Feedback

**Dùng để**: Mỗi người phỏng vấn ghi điểm & ý kiến riêng lẻ về ứng viên.

**Doctype**: `Interview Feedback`

**Trường chính** (chưa kiểm):
- `interview`: Link tới Interview
- Các trường ghi chép điểm, ý kiến.

---

### 1.7 Đề Xuất Tuyển — Job Offer

**Dùng để**: HR lập Đề xuất tuyển với điều kiện lương, ngày vào, policy, và gửi cho ứng viên; track status (Draft → Ready to Send → Awaiting Response → Accepted/Rejected).

**Doctype**: `Job Offer` + `Job Offer Component` (bảng CTC) + `Job Offer Term` (bảng điều khoản) + `Job Offer Term Template`

**Trường chính**:
- `job_applicant`: Link tới Job Applicant (filter: status != "Rejected")
- `applicant_name`, `applicant_email` (bắt buộc, fetch từ job_applicant)
- `offer_date`, `offer_valid_till`: Ngày đề xuất, hạn chót
- `status` (mặc định "Draft"): Draft / Ready to Send / Awaiting Response / Accepted / Rejected / Cancelled
  - Draft (docstatus=0): chỉnh sửa
  - Submit → Ready to Send (docstatus=1): sẵn sàng gửi email
  - Email sent → Awaiting Response (tự update khi HR send ngoài hệ)
  - Nhận reply từ ứng viên → Accepted / Rejected

**Vai trò (Role)**:
- `company`, `designation` (bắt buộc): Công ty, Chức danh
- `department`, `reports_to`, `employment_type`, `branch`, `location`: Chi tiết
- `date_of_joining`: Ngày vào làm (mặc định = offer_date nếu không chỉ định)

**Lương & CTC**:
- `salary_structure`: Link tới Salary Structure template
- `calculate_component_amount_from`: Base and Variable / CTC (cách tính breakdown)
- `base`, `variable`, `ctc`, `gross` (tính tự động)
- `grade`, `currency`
- `ctc_breakup`: Bảng chi tiết từng thành phần lương

**Leave & Holiday**:
- `leave_policy`: Link tới Leave Policy (nạp leave_allocations auto)
- `leave_allocations`: Bảng các loại nghỉ phép (fetch từ leave_policy)
- `holiday_list`: Link tới Holiday List
- `weekly_off_days`, `total_public_holidays` (tính auto từ holiday_list)

**Chính sách lao động**:
- `probation_period_days`: Thời gian thử việc (ngày)
- `notice_number_of_days`: Thời gian báo trước khi nghỉ (ngày, bình thường)
- `notice_period_during_probation`: Thời gian báo trong thử việc (ngày)
- `working_hours`: Giờ làm việc/ngày

**Điều khoản**:
- `select_terms`: Link tới Job Offer Term Template để nạp
- `terms`: Text HTML ghi các điều khoản tự do
- `offer_terms`: Bảng chi tiết (fetch từ template hoặc nhập thủ công)

**In ấn**:
- `offer_letter_print_format`: Format mẫu in (đặt mặc định ở HR Settings?)
- `letter_head`, `signature`: Letterhead + chữ ký của người lập
- `offer_letter_preview`: Preview HTML

**Kiểm chặn**:
- Không cho lập 2 Job Offer cho cùng email với status ∉ {Rejected, Cancelled}
- Nếu HR Settings `check_vacancies` = True → kiểm `staffing_plan` có đủ vacancies (vacancies - số Job Offer trong khoảng thời gian > 0); nếu không → throw error "There are no vacancies under staffing plan..."

**Liên kết**:
- **Job Applicant**: Khi Job Offer accept/reject → Job Applicant status → Accepted/Rejected (onchange)
- **Make Employee** (hàm whitelist):
  - Chép: applicant_name → employee_name, offer_date → scheduled_confirmation_date, applicant_email → personal_email
  - Chép: company, department, employment_type, date_of_joining
  - Set job_offer = Job Offer.name (backlink)
  - Mapper sẽ tạo Employee mới
- **Build Prospective Assignment** (nội bộ):
  - Từ Job Offer → Salary Structure Assignment (tạm thể)
  - Chép: salary_structure, company, currency, variable, from_date, department, designation, grade
  - Dùng để preview lương trước khi hire

**Communication**:
- Khi status = Ready to Send + HR send email → Job Offer status tự update → Awaiting Response (via on_communication_update).

**Onload**:
- Nạp `employee` (Employee record nếu đã được tạo từ Job Offer này).

---

### 1.8 Thư Bổ Nhiệm — Appointment Letter

**Dùng để**: Tạo thư chính thức bổ nhiệm / hợp đồng lao động cho nhân viên mới.

**Doctype**: `Appointment Letter` + `Appointment Letter Content` (template) + `Appointment Letter Template`

**Trường chính** (chưa kiểm):
- Employee, chứng từ liên quan.
- Template, content.
- Status, submission.

---

### 1.9 Tuyến Cử Nhân Viên — Employee Referral

**Dùng để**: Ghi nhân viên hiện tại tuyến cử ứng viên; track status (Open → In Process → Accepted/Rejected) và có thể thưởng referral nếu hire.

**Doctype**: `Employee Referral`

**Trường chính** (chưa kiểm):
- `employee` (referrer): Nhân viên tuyến cử
- `applicant_name`, `email_id`: Thông tin ứng viên
- `status`: Open / In Process / Accepted / Rejected
- Liên kết → Job Applicant (Job Applicant.source = "Employee Referral", Job Applicant.source_name = employee này)

---

## 2. HIỆU SUẤT (Performance / Appraisal)

### 2.1 Chu Kỳ Đánh Giá — Appraisal Cycle

**Dùng để**: Định kỳ đánh giá hiệu suất nhân viên (ví dụ: hàng quý, hàng năm); tạo hàng loạt Appraisal cho tất cả nhân viên trong chu kỳ.

**Doctype**: `Appraisal Cycle`

**Trường chính** (chưa kiểm):
- `name`, `start_date`, `end_date`: Tên & khoảng thời gian chu kỳ
- Danh sách nhân viên tham gia (hoặc filter tự động)
- Nút tạo Appraisal hàng loạt

---

### 2.2 Bảng Đánh Giá — Appraisal Template

**Dùng để**: Mẫu câu hỏi / tiêu chí đánh giá; có thể tái sử dụng cho nhiều chu kỳ.

**Doctype**: `Appraisal Template` + `Appraisal Template Goal` (bảng)

**Trường chính** (chưa kiểm):
- `name`: Tên mẫu
- Template Goals: Danh sách các tiêu chí/KRA (tham chiếu KRA doctype hoặc nhập tự do)

---

### 2.3 Chỉ Số Đo Lường — KRA, Goal

**KRA** (Key Result Area — Lĩnh vực kết quả chính):
- **Doctype**: `KRA`
- **Dùng để**: Định nghĩa những lĩnh vực chính mà nhân viên cần đạt được (ví dụ: "Bán hàng", "Chất lượng dịch vụ")
- **Trường chính** (chưa kiểm): `name`, `description`.

**Goal** (Mục tiêu cá nhân):
- **Doctype**: `Goal`
- **Dùng để**: Nhân viên / quản lý lập mục tiêu cụ thể trong Appraisal; liên kết tới KRA.
- **Cây mục tiêu** (chưa kiểm): Có thể có parent/child goals.
- **Trường chính** (chưa kiểm): `name`, `start_date`, `end_date`, `goal_name`, `linked_kra`, `progress_update_available`.

---

### 2.4 Phiếu Đánh Giá — Appraisal

**Dùng để**: Đánh giá hiệu suất cụ thể của 1 nhân viên trong 1 chu kỳ; gồm tự đánh giá, quản lý đánh giá, feedback từ đồng nghiệp.

**Doctype**: `Appraisal` + `Appraisal KRA` (bảng chi tiết đánh giá từng KRA)

**Trường chính**:
- `naming_series` (mặc định "HR-APR-.YYYY.-"): Kiểu đặt tên
- `employee` (bắt buộc): Nhân viên được đánh giá
- `employee_name`, `department`, `designation` (chỉ xem, fetch từ employee)
- `appraisal_cycle` (bắt buộc): Chu kỳ đánh giá
- `start_date`, `end_date` (chỉ xem, fetch từ appraisal_cycle)
- `appraisal_template` (bắt buộc khi submit): Mẫu đánh giá
- `rate_goals_manually`: Checkbox; nếu checked → bỏ bảng appraisal_kra, nhập điểm tự do
- **Tab KRA**:
  - `appraisal_kra`: Bảng chi tiết, fetch từ `appraisal_template`:
    - `designation`, `kra` (Key Result Area)
    - `target`, `achieved` (Mục tiêu/Đã đạt được)
    - `rating`, `goal_score_percentage`
  - `goal_score_percentage`: % điểm từ goals
  - `total_score` (chỉ xem): Tính từ KRA ratings
- **Tab Feedback**:
  - `feedback_html`: HTML render danh sách feedback từ Employee Performance Feedback
  - `avg_feedback_score` (chỉ xem): Trung bình điểm feedback
- **Tab Self Appraisal**:
  - `self_ratings`: Tự đánh giá (chưa kiểm cấu trúc bảng)
  - `self_score` (chỉ xem): Tổng điểm tự đánh giá
  - `reflections`: Text; nhân viên ghi nhận xét cá nhân
- `final_score` (chỉ xem): Điểm chung cuộc (công thức chưa kiểm; có thể = (total_score + avg_feedback_score + self_score) / 3 ?)
- `remarks`: Ghi chú của HR
- `amended_from`: Nếu amend (sửa lại)

**Luồng**:
1. Tạo từ Appraisal Cycle (batch) hoặc lập thủ công
2. Draft: Nhân viên tự đánh giá (self_ratings), quản lý đánh giá KRA, HR thu feedback
3. Submit: Chốt điểm, final_score được tính
4. Có thể Amend lần khác

**Nút** (chưa kiểm): Có nút "Create Appraisal" hàng loạt từ Cycle không? Hoặc `make_appraisals(cycle)` function?

**Liên kết**:
- **Employee Performance Feedback**: Người khác (same level, reports_to, …) lập feedback riêng.
- **Employee Promotion** (chưa kiểm): Liệu có link từ Appraisal → quá trình thăng chức?

---

### 2.5 Phản Hồi Hiệu Suất — Employee Performance Feedback

**Dùng để**: Người khác (quản lý khác, peer, …) ghi nhận xét về nhân viên trong Appraisal; gom lại làm `avg_feedback_score`.

**Doctype**: `Employee Performance Feedback` + `Employee Feedback Rating` (bảng điểm)

**Trường chính** (chưa kiểm):
- `appraisal`: Link tới Appraisal
- `employee`: Nhân viên được đánh giá
- `feedback_by` (người phản hồi): User hoặc Employee
- Bảng rating từng tiêu chí (`Employee Feedback Rating` — chưa kiểm chi tiết)

**Liên kết**:
- `Employee Feedback Criteria`: Danh sách tiêu chí định nghĩa sẵn để feedback
- Gom vào Appraisal.feedback_html + avg_feedback_score

---

### 2.6 Thăng Chức — Employee Promotion

**Dùng để**: Ghi chép khi nhân viên được thăng chức (chức danh, lương, phòng ban mới).

**Doctype**: `Employee Promotion`

**Trường chính** (chưa kiểm):
- `employee`: Nhân viên
- `promotion_date`: Ngày thăng chức
- `new_designation`, `new_department`, `new_grade`, `new_salary_structure`: Chi tiết mới
- Link từ Appraisal (hoặc được khởi tạo sau đánh giá tốt)

---

## 3. CHI PHÍ & CÔNG TÁC (Expenses & Travel)

### 3.1 Yêu Cầu Công Tác — Travel Request

**Dùng để**: Nhân viên đề xuất chuyến công tác; track approval & related expenses.

**Doctype**: `Travel Request` + `Travel Itinerary` (chưa kiểm)

**Trường chính** (chưa kiểm):
- `employee`, `department`, `designation`: Nhân viên
- `travel_date_from`, `travel_date_to`: Khoảng thời gian
- `purpose_of_travel`: Mục đích (Link tới Purpose of Travel)
- `itinerary`: Bảng chi tiết tuyến đường (từng điểm dừng, ngày, địa điểm)
- Status, approval

---

### 3.2 Tạm Ứng Nhân Viên — Employee Advance

**Dùng để**: Nhân viên xin tạm ứng tiền (cho chi phí công tác, khó khăn, …); tạo Payment Entry → Payment Entry sau submit → nhân viên nhận tiền → hoàn ứng hoặc khấu vào Expense Claim.

**Doctype**: `Employee Advance`

**Trường chính** (chưa kiểm):
- `employee` (bắt buộc): Nhân viên
- `advance_date`, `posting_date`: Ngày tạm ứng
- `advance_amount`, `purpose`: Số tiền, mục đích
- `currency`: Tiền tệ
- `status` (chưa kiểm cách tính): Pending / Paid / Partly Claimed and Returned / Claimed / Returned
- `paid_amount`: Số tiền đã chi trả (chỉ xem, từ Payment Entry / Journal Entry)
- `claimed_amount`: Số tiền đã khấu (từ Expense Claim)
- `return_amount`: Số tiền trả lại

**Nút/Hàm** (chưa kiểm):
- `make_payment_entry(employee_advance)`: Tạo Payment Entry từ tạm ứng → chi trả cho nhân viên

**Liên kết**:
- Sau submit → tạo Payment Entry (hoặc lập thủ công)
- Payment Entry status = Submitted → Employee Advance `paid_amount` += amount
- Expense Claim.advances[]: Bảng chọn các tạm ứng để khấu vào chi phí
  - Expense Claim.advance_payments_sb (section): Lưu bảng `advances` (Expense Claim Advance — chưa kiểm)
  - Khấu auto: chi phí sanctioned × factor - advance → hoàn ứng

---

### 3.3 Phiếu Chi Phí — Expense Claim

**Dùng để**: Nhân viên nộp chi phí công tác (khách sạn, ăn uống, vé xe, …); HR duyệt, lập Payment Entry để hoàn tiền hoặc khấu vào lương.

**Doctype**: `Expense Claim` + `Expense Claim Detail` (bảng chi tiết) + `Expense Claim Advance` (bảng tạm ứng liên kết) + `Expense Taxes and Charges` (bảng thuế)

**Trường chính**:
- `naming_series` (mặc định "HR-EXP-.YYYY.-"): Kiểu đặt tên
- `employee` (bắt buộc): Nhân viên nộp
- `employee_name` (chỉ xem, fetch từ employee)
- `department` (fetch từ employee nếu trống)
- `company` (bắt buộc): Công ty
- `currency`, `exchange_rate`: Tiền tệ (nếu foreign) × tỷ giá
- **Chi tiết chi phí**:
  - `expenses` (bắt buộc): Bảng `Expense Claim Detail`:
    - `expense_type`: Link tới Expense Claim Type (ví dụ "Accommodation", "Travel", "Meals")
    - `expense_date`: Ngày chi
    - `description`: Mô tả (ví dụ "Hotel X, 2 đêm")
    - `amount`: Số tiền
    - `sanctioned_amount`: Số tiền chấp thuận (nhân viên duyệt hoặc HR thay đổi)
    - `expense_account`: TK chi phí (lấy từ Expense Claim Type hoặc nhập thủ công)
    - `cost_center`: Trung tâm chi phí
  - `taxes`: Bảng Expense Taxes and Charges (thuế VAT, …):
    - `account_head`, `tax_type`: TK thuế, loại thuế
    - `tax_amount`, `rate`: Số tiền / tỷ lệ
  - `total_claimed_amount` (chỉ xem): Tổng chi phí nhân viên claim (sum expenses.amount)
  - `total_sanctioned_amount` (chỉ xem): Tổng chi phí chấp thuận (sum expenses.sanctioned_amount)
  - `total_taxes_and_charges` (chỉ xem): Tổng thuế
- **Tạm ứng liên kết**:
  - `advances` (bảng Expense Claim Advance): Danh sách tạm ứng để khấu:
    - `employee_advance`: Link (filter: docstatus=1, employee=this.employee, paid_amount > 0, status ∉ {Claimed, Returned, Partly Claimed and Returned}, currency=this.currency)
    - `advance_amount`: Số tiền tạm ứng (fetch từ employee_advance.paid_amount - claimed_amount)
    - `allocated_amount`: Số tiền khấu từ chi phí này
  - `total_advance_amount` (chỉ xem): Tổng tạm ứng khấu (sum advances.allocated_amount)
- **Kết toán**:
  - `base_*` fields (base currency): Tính toán ở currency công ty
  - `grand_total` = total_sanctioned_amount + total_taxes_and_charges - total_advance_amount
    - Nếu grand_total > 0: hoàn tiền cho nhân viên
    - Nếu grand_total < 0: nhân viên nợ công ty (tiếp nối từ advance)
  - `total_amount_reimbursed` (chỉ xem): Số tiền đã hoàn từ Payment Entry
  - `total_exchange_gain_loss`: Chênh lệch tỷ giá (nếu foreign currency)
- **Duyệt phê chuẩn**:
  - `expense_approver`: Người duyệt (Link → User; filter từ Department Approver)
  - `approval_status` (permlevel=1, mặc định "Draft"): Draft / Approved / Rejected / Cancelled
  - `is_paid`: Checkbox; nếu checked → grand_total = 0 (đã trả hết, dùng cho Payment Entry)
- **Kế toán**:
  - `posting_date` (bắt buộc, mặc định hôm nay): Ngày ghi sổ
  - `payable_account`: TK Phải trả (Payable account của công ty)
  - `bank_or_cash_account`: TK Ngân hàng / Tiền mặt (nếu lập Payment Entry)
  - `mode_of_payment`: Hình thức thanh toán (chuyển khoản, tiền mặt, …)
  - `project`, `cost_center`: Dự án, trung tâm chi phí (có thể để accounting_dimensions)
- **Status**:
  - `status` (chỉ xem, tính auto): Draft / Submitted / Approved / Rejected / Paid / Partially Paid / Unpaid / Cancelled
    - Draft: docstatus=0
    - Submitted: docstatus=1 (lập xong, chờ duyệt)
    - Approved: docstatus=1 + approval_status=Approved
    - Rejected: docstatus=1 + approval_status=Rejected
    - Paid: docstatus=1 + approval_status=Approved + (is_paid=True hoặc total_amount_reimbursed=grand_total hoặc grand_total=0)
    - Partially Paid: docstatus=1 + approval_status=Approved + total_amount_reimbursed > 0 (nhưng < grand_total)
    - Unpaid: docstatus=1 + approval_status=Approved + total_amount_reimbursed=0 + grand_total > 0
    - Cancelled: docstatus=2
  - `task`, `vehicle_log`, `delivery_trip`: Liên kết (chỉ xem) nếu được tạo từ những doctype này
- `remark`: Ghi chú từ HR / Kế toán
- `clearance_date`: Ngày hoàn ứng / kết thúc (sau thanh toán)

**Kiểm chặn**:
- Không cho lập Expense Claim cho inactive employee
- Nếu employee của tạm ứng (advances) ≠ employee Claim → throw error
- Nếu currency of tạm ứng ≠ currency Claim → throw error
- sanctioned_amount ≤ amount (không cho chấp thuận > claim)

**Luồng trạng thái**:
1. Draft: Nhân viên lập
2. Submit (docstatus=1): Gửi duyệt cho Expense Approver
3. Approved (approval_status=Approved): HR/Approver duyệt; có thể lập Payment Entry
4. Make Payment Entry: Tạo phiếu chi (Payment Entry hoặc Journal Entry):
   - `get_payment_entry_for_employee(dt="Expense Claim", dn=name)` (chưa kiểm): Tạo Payment Entry từ Claim
   - Payment Entry link: reference_type=Expense Claim, reference_name=this.name
5. Payment submitted: employee_advance → claimed_amount cập nhật (chưa kiểm hàm nào); status → Paid / Partially Paid

**Nút/Hàm**:
- **«Make Payment Entry»** (nút): Gọi `get_payment_entry_for_employee(dt, dn)` → tạo Payment Entry (từ erpnext.overrides.employee_payment_entry module)
- `notify_approver()`: Gửi thông báo cho expense_approver (sau insert)
- `calculate_total_amount()`, `calculate_taxes()`: Tính tổng auto
- `set_expense_account(validate=True)`: Set TK chi phí từ Expense Claim Type nếu trống

**Liên kết**:
- **Employee Advance**: Bảng `advances` khấu vào chi phí claim (trạng thái tạm ứng cập nhật)
- **Journal Entry / Payment Entry**: Lập từ nút «Make Payment» → ghi sổ hoặc chi tiền cho nhân viên
  - Ghi: Dr. Payable Account / Cr. Bank Account (hoặc ngược lại nếu nhân viên nợ)
- **Delivery Trip**: Nếu claim từ delivery trip → `delivery_trip` field (chỉ xem)
- **Vehicle Log**: Nếu từ khoảng cách xe → `vehicle_log` field (chỉ xem)

**Onload**:
- `self_expense_approval_not_allowed` (từ HR Settings): Cảnh báo nếu employee = expense_approver (tự duyệt?)

---

### 3.4 Loại Chi Phí — Expense Claim Type

**Dùng để**: Danh mục chi phí (Accommodation, Meals, Transport, …); gắn TK chi phí mặc định và trung tâm chi phí.

**Doctype**: `Expense Claim Type`

**Trường chính** (chưa kiểm):
- `name`: Tên loại (ví dụ "Accommodation")
- `expense_account`: TK chi phí mặc định (ví dụ 5xxx)
- `cost_center`: Trung tâm chi phí mặc định

---

### 3.5 Ghi Chép Xe — Vehicle Log

**Dùng để**: Ghi chép chuyến sử dụng xe công ty (tuyến, khoảng cách, nhiên liệu, …); có thể tạo Expense Claim tự động từ dữ liệu này.

**Doctype**: `Vehicle Log` + `Vehicle Service` (bảng lịch sử bảo dưỡng), `Vehicle Service Item` (chưa kiểm)

**Trường chính** (chưa kiểm):
- `vehicle` (Link → Vehicle từ lõi ERPNext): Xe công ty
- `employee`, `driver` (chưa kiểm): Tài xế / người sử dụng
- `trip_start_date`, `trip_end_date`: Ngày bắt đầu/kết thúc
- `starting_odometer`, `ending_odometer`: Quãng số trong quá trình
- `distance` (chỉ xem, tính auto): = ending - starting
- `fuel_qty`, `cost`: Lượng xăng / chi phí xăng
- `expense_type`: Loại chi phí (nếu tạo Expense Claim)
- `remarks`: Ghi chú

**Liên kết**:
- **Expense Claim** (chưa kiểm): Có button tạo Expense Claim từ Vehicle Log?
  - Nút «Make Expense Claim» hoặc `make_expense_claim_for_vehicle_log(vehicle_log)`: Tạo claim với expense_type = fuel, amount = fuel cost

---

## 4. LƯƠNG / THUẾ & PHÚC LỢI (Ngắn)

⚠️ **DEGO chốt KHÔNG làm module Lương/Bảy.** Danh sách dưới chỉ tham khảo; mỗi doctype 1 câu, không chi tiết.

- **Salary Component** (Thành phần lương): Định nghĩa từng khoản trong bảng lương (cơ bản, phụ cấp, bảo hiểm, thuế, …).
- **Salary Structure** (Bảng lương): Mẫu bảng lương; gom các Salary Component lại với công thức tính từng khoản.
- **Salary Structure Assignment** (Gán bảng lương): Gắn từng nhân viên tới Salary Structure từ ngày nào; track from_date, to_date, salary, grade, …
- **Payroll Entry** (Chạy lương): Tạo batch để lập Salary Slip cho tất cả nhân viên trong 1 tháng; lập hàng loạt.
- **Salary Slip** (Phiếu lương): Chi tiết lương của 1 nhân viên 1 tháng; show từng khoản, tính thuế, net lương.
- **Additional Salary** (Lương bổ sung): Ghi lương thêm ngoài Salary Slip (thưởng, bồi thường, …).
- **Salary Withholding** (Khấu lương): Ghi khi phải khấu lương (nợ công ty, dịch, …).
- **Employee Incentive** (Thưởng nhân viên): Ghi thưởng hiệu suất, KPI, …
- **Retention Bonus** (Tiền thù lao giữ chân): Thưởng giữ chân khi nhân viên đã đi / sắp đi.
- **Arrear** (Lương chậm/bổ sung): Ghi lương các tháng trước bị bỏ sót hoặc điều chỉnh.
- **Payroll Correction** (Điều chỉnh lương): Sửa Salary Slip sau khi submit.
- **Income Tax Slab** (Bảng thuế thu nhập): Định nghĩa bậc lương × tỷ lệ thuế hàng năm.
- **Employee Tax Exemption Declaration** (Khai báo giảm thuế): Nhân viên khai hoàn cảnh giảm thuế (con, vợ, …).
- **Employee Tax Exemption** (Giảm thuế): Ghi số tiền được giảm dựa khai báo.
- **Gratuity** (Tiền thưởng hưu trí / khoản tiểu thử): Tính & ghi tiền khi nhân viên nghỉ; công thức = (lương bình quân × năm làm việc × %).
- **Full and Final Statement** (Tính toán cuối cùng): Khi nhân viên nghỉ, tổng hợp tất cả khoản nợ, tiền lương, bảo hiểm để thanh toán một lần.

---

## 5. SƠ ĐỒ LUỒNG

### Tuyển dụng → Onboarding

```
Staffing Plan (xác định định biên)
    ↓
Job Opening (mở tin tuyển)
    ↓ (publish on website)
Job Applicant (ứng viên apply)
    ↓
Interview (phỏng vấn)
    ↓
Job Offer (đề xuất tuyển, negotiation)
    ↓ (accept)
Appointment Letter (thư bổ nhiệm)
    ↓
make_employee() → Employee (tạo nhân viên)
    ↓ (optionally)
Employee Onboarding (hướng dẫn, setup account, …)
```

### Chi phí công tác → Hoàn tiền

```
Employee Advance (xin tạm ứng)
    ↓ submit
    ↓ make_payment_entry()
Payment Entry (chi tiền cho nhân viên)
    ↓
Travel Request / Expense Claim (nộp chi phí)
    ↓
Expense Claim Detail (ghi từng khoản: hotel, meal, …)
    ↓
Expense Claim Detail.allocated_amount (khấu từ tạm ứng)
    ↓ approved
    ↓ make_payment_entry()
Payment Entry (hoàn tiền hoặc khấu lương)
```

### Hiệu suất

```
Appraisal Cycle (định kỳ)
    ↓
Appraisal (tạo hàng loạt từ cycle)
    ↓
Employee (tự đánh giá)
Manager (đánh giá KRA)
Peer / Others (feedback)
    ↓ (gom lại)
Appraisal.final_score (chốt điểm)
    ↓ (high score)
Employee Promotion (thăng chức)
```

---

## 6. SO SÁNH VỚI DEGO

| Chức năng ERPNext HRMS | DEGO đã có | Gợi ý học | Lý do |
|---|---|---|---|
| Staffing Plan | KHÔNG | **Cao** | Định biên là quy trình của DEGO (số chỉ tiêu / chức danh); Staffing Plan mapping tới Yêu Cầu Tuyển Dụng (phân hệ Thu Mua) |
| Job Opening / Job Applicant | KHÔNG | **Cao** | Logic apply, filter, track trạng thái tương tự Purchase Request → Purchase Order; có thể học cấu trúc state machine |
| Interview | KHÔNG | **TB** | Phỏng vấn chưa trong phạm vi; nếu mở rộng thì học Interview Type, Interview Feedback |
| Job Offer | KHÔNG | **TB** | Có thể mapping tới Offer / Proposal ở lõi; JSON lương (CTC breakup) tương tự Job Offer Component |
| Appraisal Cycle / Appraisal | KHÔNG | **Thấp** | Hiệu suất nằm ngoài phạm vi DEGO (theo CLAUDE.md: KHÔNG làm đánh giá hiệu suất) |
| Employee Advance | Có (Yêu Cầu Thanh Toán?) | **TB** | Cấu trúc advance → payment tương tự; DEGO có luồng duyệt Yêu Cầu Thanh Toán riêng |
| Expense Claim | Có (Yêu Cầu Thanh Toán?) | **Cao** | Cấu trúc chi tiết (bảng expenses, taxes, khấu advance) tương tự DEGO; tính toán sanctioned_amount ≈ DEGO duyệt số tiền |
| Travel Request | KHÔNG | **Thấp** | Có thể mapping tới Đặt Xe công ty (Vehicle Booking ở DEGO); Travel Request → Vehicle Log → Expense Claim tương tự Purchase Request → Goods Receipt → Payment |
| Salary Components / Payroll | KHÔNG | **NGOÀI PHẠM VI** | DEGO chốt KHÔNG làm lương (1); nếu mở rộng thì học JSON CTC, component formula |

---

## Unresolved Questions

1. **Interview → Job Applicant status**: Khi nào Interview status (Cleared/Rejected) tự update Job Applicant status?
2. **Employee Advance `claimed_amount` tính toán**: Khi nào, từ đâu tính field này?
3. **Expense Claim total_amount_reimbursed**: Tính từ Payment Entry nào? (tệp:dòng chưa kiểm)
4. **Appraisal final_score công thức**: Công thức chính xác để gom `total_score` + `avg_feedback_score` + `self_score`?
5. **Employee Promotion thích hợp với Appraisal**: Liệu có hook tự động tạo Promotion từ Appraisal high score, hay thủ công?
6. **Onboarding workflow**: Employee Onboarding template + checklist hoạt động thế nào?
7. **Job Offer → Salary Structure Assignment**: Job Offer `build_prospective_assignment()` được dùng khi nào (preview, hay create assignment when accepted)?
8. **Job Applicant duplicate prevention**: Với `prevent_duplicate_applicant` = True, scope check là email hay (email + job_title)?

---

**Status:** DONE_WITH_CONCERNS

**Summary**: Nghiên cứu 9 doctype Tuyển Dụng (Staffing Plan → Job Opening → Job Applicant → Interview → Job Offer → Appointment Letter), 6 doctype Hiệu Suất (Appraisal Cycle → Appraisal → Feedback), 6 doctype Chi Phí (Employee Advance, Expense Claim, Travel Request, Vehicle Log). Ghi 450+ dòng tài liệu tiếng Việt với trường chính, luồng trạng thái, nút tạo chứng từ, luật chặn, và so sánh với DEGO (không có tuyển/hiệu suất, có chi phí dạng Yêu Cầu Thanh Toán).

**Concerns**: 8 câu hỏi chưa kiểm lại (cấu trúc bảng Detail/Feedback, hook event, công thức tính); chưa đọc toàn bộ Onboarding Template, Employee Referral thực tiễn; Salary/Payroll được giảm tối thiểu theo yêu cầu DEGO KHÔNG làm.

