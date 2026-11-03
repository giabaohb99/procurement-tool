# Phase 04 — Báo cáo Nhân sự + Nghỉ phép

## Context links
- `backend/app/modules/employee/model.py` (status :39, hire_date :49, resign_date :97, gender :55, employment_type :92, job_level :93, position_id :33, date_of_birth :71), `employee/constants.py`, `employee/sensitive.py` (`SENSITIVE_FIELDS` :27), `core/status_codes.py:62` (`EMPLOYEE_STATUS`: official/collaborator/maternity_leave/resigned)
- `backend/app/modules/leave/request_model.py` (:27 request, :139 line), `leave/balance_model.py:29`, `leave/catalog_model.py:31`, `leave/constants.py:28` (LR_DRAFT=1, PENDING=2, APPROVED=3, REJECTED=4, RETURNED=5, CANCELLED=6)
- Scope: `SCOPE_FIELDS` employee `{company, dept_id, self:id}`, leave_request `{company, dept_id, owner:created_by, self:employee_id}`, leave_balance `{company, self:employee_id}`
- Test: `test/backend/conftest.py` (`world`, `cap_quyen`), `scope_factory.MODEL_OF` đã có leave_request/leave_balance

## Overview
- Priority: P2 · Status: pending · Effort: 7h · Sở hữu: `employee/report_*`, `leave/report_*`, `config/report-catalog-hr.ts`, `pages/hr-*-report-page.tsx`

## Key insights
- Không có bảng lịch sử điều chuyển → chiều phòng ban của Nhân sự là phòng HIỆN TẠI (ghi `notes`). Đơn nghỉ chụp `department_id` lúc tạo → đúng phòng tại thời điểm nghỉ.
- `resign_date`/`hire_date` có thể rỗng ở dữ liệu cũ; `status=resigned` mà thiếu `resign_date` → không tính vào "nghỉ việc trong kỳ", đếm vào `notes` (chất lượng dữ liệu).
- `date_of_birth` là trường NHẠY CẢM → KHÔNG có chiều độ tuổi. Không chiều nào đọc cột trong `SENSITIVE_FIELDS`.
- Dòng đơn nghỉ không có ngày; đơn vắt qua 2 tháng → quy về `from_date` (Q4.1).
- `own` của leave_request = `created_by == uid OR employee_id == eid` → `apply_scope` tự hợp; KHÔNG nới "đang có việc duyệt" (chỉ dành cho đọc từng đơn).

## Báo cáo
### 4.1 Nhân sự — Biến động & cơ cấu
- Endpoint `GET /api/employees/summary` (+ `/summary/export`), `require('employee','read')` / `('employee','export')`; nguồn menu `/hr/employees`, entity `employee`.
- Truy vấn: `apply_scope(Employee, 'employee')`, `with_entities(id, company_id, department_id, job_level, employment_type, gender, position_id, status, hire_date, resign_date, created_at)`.
- Trường ngày: `hire_date` (vào), `resign_date` (nghỉ). Hồ sơ thiếu `hire_date` → coi có mặt từ `created_at` (giờ VN).
- Chỉ số: Định biên cuối kỳ (snapshot: đã vào ≤ `to` và chưa nghỉ ≤ `to`), Định biên đầu kỳ, Vào mới, Nghỉ việc (good down), Tỷ lệ nghỉ việc % = nghỉ / TB(đầu, cuối) (good down), Thay đổi ròng.
- Xu hướng: định biên cuối mỗi mốc + vào/nghỉ theo mốc (dùng `snapshot` của khung).
- Xem theo: thời gian · công ty · phòng ban · cấp bậc (`JOB_LEVEL_*`) · loại hình (`EMPLOYMENT_*`) · giới tính (`GENDER_*`) · chức vụ (`position_id` → tên) · thâm niên (dải 0–1/1–3/3–5/5+ năm từ `hire_date`).
- Breakdowns: theo trạng thái (`EMPLOYEE_STATUS` nhãn từ code set).
### 4.2 Nghỉ phép — Tình hình nghỉ
- Endpoint `GET /api/leave-requests/summary` (+export), `require('leave_request','read'|'export')`; nguồn `/hr/leave-requests`, entity `leave_request`.
- Truy vấn: `apply_scope(LeaveRequest,'leave_request')`, `is_deleted=False`, `status != LR_DRAFT`; dòng lấy theo lô `tab_leave_request_line` (1 truy vấn).
- Trường ngày: `from_date` (Date).
- Chỉ số: Số đơn, Ngày nghỉ đã duyệt (Σ `line.days` của đơn APPROVED), Ngày đang chờ duyệt, Số người nghỉ (distinct `employee_id`, đơn duyệt), Tỷ lệ từ chối/trả về % (good down), Thời gian duyệt TB giờ (`submitted_at→decided_at`, good down).
- Xem theo: thời gian · loại nghỉ (THEO DÒNG — đơn nhiều loại vào nhiều nhóm, Tổng tính riêng) · phòng ban · công ty · nhân sự (`employee_id` → họ tên, KHÔNG thêm trường nào khác) · trạng thái.
- Breakdowns: theo trạng thái; top loại nghỉ.
### 4.3 Quỹ phép năm
- Endpoint `GET /api/leave-balances/summary` (+export), `require('leave_balance', ...)`; nguồn `/hr/leave-balances`, entity `leave_balance`.
- Kỳ = NĂM của `to` (`year` SmallInteger); so sánh = năm trước; không có xu hướng theo ngày → `trend` rỗng, FE ẩn biểu đồ xu hướng, vẽ cột chồng dùng/giữ chỗ/còn theo nhóm. Cấu hình FE `periodMode: 'year'` (bộ chọn chỉ còn Năm nay/Năm trước/Tùy chọn năm).
- Chỉ số: Được cấp (allocated+seniority+carried+adjusted), Đã dùng, Đang giữ chỗ (`pending_days`), Còn lại (công thức `remaining_days` của model, tính Python), Tỷ lệ sử dụng %.
- Xem theo: loại nghỉ · công ty · phòng ban (phòng HIỆN TẠI của nhân sự, join Employee trong phạm vi đã scope của balance) · nhân sự.

## Related code files
Tạo: `backend/app/modules/employee/report_service.py`, `backend/app/modules/leave/report_service.py`, `backend/app/modules/leave/balance_report_service.py`; ghi route vào router rỗng P01 (`employee/report_controller.py`, `leave/report_controller.py`, `leave/balance_report_controller.py`); `test/backend/test_bao_cao_nhan_su.py`, `test/backend/test_bao_cao_nghi_phep.py`.
Frontend: `config/report-catalog-hr.ts` (3 mục, group "Nhân sự"), `pages/hr-headcount-report-page.tsx`, `pages/leave-usage-report-page.tsx`, `pages/leave-balance-report-page.tsx` (mỗi tệp = cấu hình + `ReportAnalyticsPage`).
Route FE (P02 đã khai): `/report/hr-headcount`, `/report/leave-usage`, `/report/leave-balance`.

## Implementation steps
1. Employee: `fetch` + `snapshot(date)`; nhãn chiều từ `*_LABELS`/`label_of`, chức vụ/phòng/công ty tra theo lô.
2. Leave: request + dòng theo lô; thời gian duyệt bằng Python trên `submitted_at/decided_at` (UTC → cùng hệ, trừ trực tiếp).
3. Balance: năm; phòng ban join Employee.
4. Test (dưới). 5. Frontend 3 trang + danh mục. 6. Cổng kiểm FE + pytest 2 tệp mới.

## Test matrix
| Ca | Kỳ vọng |
|---|---|
| Quyền `employee` scope dept | chỉ đếm nhân sự phòng mình |
| Người thiếu `employee_sensitive` | JSON không chứa khóa nào trong `SENSITIVE_FIELDS`; không có dimension tuổi (khẳng định bằng test duyệt đệ quy khóa) |
| leave_request scope `own` | thấy đơn mình lập HỘ + đơn của chính mình; không thấy đơn người khác dù đang là người duyệt |
| Đơn 2 loại (3+2 ngày) | nhóm A=3, B=2, Tổng ngày=5, Tổng đơn=1 |
| Nghỉ việc thiếu `resign_date` | không vào chỉ số, có trong `notes` |
| `/summary` vs `/{id}` | TestClient gọi `/api/employees/summary` → 200 (không 422) |

## Success criteria
Tất cả ca trên xanh; 3 trang hiện đúng KPI/biểu đồ/bảng; Excel mở được và có dòng Tổng.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| Lộ dữ liệu nhạy cảm qua chiều mới sau này | TB×Cao | test canh khóa + docstring "cấm chiều từ SENSITIVE_FIELDS" |
| Định biên quá khứ sai do thiếu lịch sử | Cao×TB | ghi chú rõ trên trang (`notes`); Q4.2 |
| Hồ sơ `is_active=False` nhưng `status≠resigned` | TB×TB | Q4.3; mặc định dựa `status`+ngày |

## Security considerations
Không có ngoại lệ "đang có việc duyệt"; chiều Nhân sự chỉ trả họ tên (không mã, không email). Excel theo `export`.

## Câu hỏi
- Q4.1 Đơn vắt qua kỳ: tính theo `from_date` (đề xuất) hay chia ngày theo lịch làm việc?
- Q4.2 Cần lịch sử điều chuyển thật (đọc `tab_change_log`) hay chấp nhận phòng ban hiện tại?
- Q4.3 "Đang làm việc" = `status ≠ resigned` hay còn xét `is_active`?
