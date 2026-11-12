# TÀI LIỆU API — NHÂN SỰ (HRM)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 12/11/2026 |
| Người phụ trách | tai-lieu-kiem-thu (Agent 2) |
| Trạng thái | Nháp — mục 1 dựng bằng máy cho cả phân hệ; mục 2–5 mới viết phần Kiêm nhiệm, các phần khác chưa viết |
| CR liên quan | duoc-CR-755 |

**Tra tham số đầy đủ:** trang `/api/docs` (Swagger do FastAPI sinh từ mã — chỉ mở ở dev `https://deverp.degoholding.vn/api/docs` và local `http://localhost:8000/api/docs`; prod tắt), nhóm (tag) `employee`, `employee-work-history`, `employee-change-request`, `job-position-roles`, `leave`, `work_schedule`, `labor-contract`, `labor-contract-template`, `labor-contract-variable`, `labor_contract`, `labor_register`, `labor_usage_report`, `meeting-room`, `report`. Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`. Danh sách có phân trang trả `data = {items, total, page, page_size}`.

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 12/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `employee`, `leave`, `work_schedule`, `labor_contract`, `labor_register`, `meeting_room`; danh mục dựng bằng `make_crud_router`: `/api/job-positions`, `/api/leave-policies`, `/api/leave-types`, `/api/holidays`, `/api/leave-block-periods`, `/api/meeting-rooms`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/attendance-report/summary` | attendance summary | `báo cáo 26`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/attendance-report/summary/export` | attendance summary export | `báo cáo 26`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/attendance-report/summary/rows` | attendance summary rows | `báo cáo 26`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/benefit-audience/summary` | benefit summary | `báo cáo 22`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/benefit-audience/summary/export` | benefit summary export | `báo cáo 22`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/benefit-audience/summary/rows` | benefit summary rows | `báo cáo 22`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/employee-concurrents` | Người đang kiêm nhiệm ở một phòng ban (trang chi tiết phòng ban, bảng "Kiêm nhiệm tại phòng này"). | `employee.read` | chỉ dòng mà phạm vi `employee.read` của người xem phủ cặp (phòng, công ty) — `concurrent_row_scope_condition` | tự dò: v2 `hr` |
| GET | `/api/employees` | list employees | `employee.read` | `apply_scope` | tự dò: v2 `dossier`, v2 `hr`, v2 `procurement` |
| POST | `/api/employees` | create employee | `employee.create` |  | tự dò: v2 `dossier`, v2 `hr`, v2 `procurement` |
| GET | `/api/employees/change-requests` | list change requests | `employee.write` |  | tự dò: v2 `hr` |
| GET | `/api/employees/change-requests/pending-count` | count pending change requests | `employee.write` |  | tự dò: v2 `hr` |
| GET | `/api/employees/change-requests/{rid}` | get change request | `employee.write` |  | tự dò: v2 `hr` |
| POST | `/api/employees/change-requests/{rid}/approve` | approve change request | `employee.write` |  | tự dò: v2 `hr` |
| POST | `/api/employees/change-requests/{rid}/reject` | reject change request | `employee.write` |  | tự dò: v2 `hr` |
| GET | `/api/employees/export/csv` | export employees csv | `employee.export` | `apply_scope` |  |
| GET | `/api/employees/export/xlsx` | Xuất Nhân sự ra .xlsx theo đúng bộ lọc đang áp + phạm vi dữ liệu (Đ-13b). | `employee.export` | `apply_scope` |  |
| POST | `/api/employees/import/csv` | duoc-CR-628: Nhập CSV nhân sự đã NGỪNG. | `employee.import` |  |  |
| GET | `/api/employees/me` | Hồ sơ nhân sự của CHÍNH người đang đăng nhập — cho màn *Trang cá nhân*. | đăng nhập |  | tự dò: v2 `hr`, v2 dùng chung |
| GET | `/api/employees/me/change-requests` | list my change requests | đăng nhập |  | tự dò: v2 `hr`, v2 dùng chung |
| POST | `/api/employees/me/change-requests` | submit change request | đăng nhập |  | tự dò: v2 `hr`, v2 dùng chung |
| POST | `/api/employees/me/change-requests/{rid}/withdraw` | withdraw change request | đăng nhập |  | tự dò: v2 `hr` |
| PATCH | `/api/employees/me/contact` | Tự sửa số điện thoại + hai địa chỉ. | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/employees/me/contacts` | Người báo tin của CHÍNH MÌNH — không cần `employee_sensitive.read` (ngoại lệ `self`, xem `sensitive.can_read_sensitive`). | đăng nhập |  | tự dò: v2 `hr`, v2 dùng chung |
| PUT | `/api/employees/me/contacts` | Đặt lại danh sách người báo tin của chính mình — cùng `contact_service` với cửa của phòng Nhân sự, nên trần 30 dòng và luật bỏ dòng rỗng họ tên chỉ có một bản. | đăng nhập |  | tự dò: v2 `hr`, v2 dùng chung |
| GET | `/api/employees/me/families` | Hộ gia đình của CHÍNH MÌNH (trang in) — ngoại lệ `self`, không cần `employee_sensitive.read`. | đăng nhập |  | tự dò: v2 `hr`, v2 dùng chung |
| GET | `/api/employees/me/work-history` | Chỉ đòi ĐĂNG NHẬP — id lấy từ `user.employee_id`, không nhận tham số. | đăng nhập |  | tự dò: v2 `hr`, v2 dùng chung |
| GET | `/api/employees/monthly-reminders` | monthly reminders | `employee.read` | `apply_scope` | tự dò: v2 `hr` |
| GET | `/api/employees/profile-gaps/summary` | profile gaps summary | `báo cáo 18`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/employees/profile-gaps/summary/export` | profile gaps summary export | `báo cáo 18`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/employees/profile-gaps/summary/rows` | profile gaps summary rows | `báo cáo 18`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/employees/summary` | employee summary | `báo cáo 6`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/employees/summary/export` | employee summary export | `báo cáo 6`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/employees/summary/rows` | Bấm một con số ra danh sách nhân sự — cùng cổng quyền/phạm vi với `/summary` (CR-686). | `báo cáo 6`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/employees/{eid}` | get employee | `employee.read` |  | tự dò: v2 `hr` |
| PATCH | `/api/employees/{eid}` | update employee | `employee.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/employees/{eid}` | delete employee | `employee.delete` |  | tự dò: v2 `hr` |
| POST | `/api/employees/{eid}/avatar` | Đổi ảnh đại diện của nhân sự. | `employee.write` |  | tự dò: v2 `hr` |
| GET | `/api/employees/{eid}/concurrents` | Danh sách kiêm nhiệm của một nhân sự (mới nhất trước). | `employee.read` | hồ sơ cha: `employee_in_scope(read)` có nhánh kiêm nhiệm (Q1); ngoài → 404 | tự dò: v2 `hr` |
| POST | `/api/employees/{eid}/concurrents` | Thêm một dòng kiêm nhiệm (công ty, phòng, chức vụ, ngày, quyết định, công tắc phạm vi). | `employee.write` | hồ sơ cha: `employee_in_scope(write)` theo vị trí chính + L1/L2 cặp/L3 | tự dò: v2 `hr` |
| PATCH | `/api/employees/{eid}/concurrents/{cid}` | Sửa một dòng kiêm nhiệm tại chỗ (id dòng và tệp quyết định giữ nguyên). | `employee.write` | hồ sơ cha: `employee_in_scope(write)` theo vị trí chính + L1/L2 cặp/L3 | tự dò: v2 `hr` |
| DELETE | `/api/employees/{eid}/concurrents/{cid}` | Xóa một dòng kiêm nhiệm cùng tệp quyết định đính kèm. | `employee.write` | hồ sơ cha: `employee_in_scope(write)` theo vị trí chính + L1/L2 cặp/L3 | tự dò: v2 `hr` |
| GET | `/api/employees/{eid}/contacts` | Người báo tin trong trường hợp cần thiết. | `employee.read` |  | tự dò: v2 `hr` |
| PUT | `/api/employees/{eid}/contacts` | set employee contacts | `employee.write` |  | tự dò: v2 `hr` |
| GET | `/api/employees/{eid}/departments` | Phòng chính + phòng kiêm nhiệm CÙNG công ty còn hiệu lực (giữ cho nơi gọi cũ). | `employee.read` |  | tự dò: v2 `hr` |
| GET | `/api/employees/{eid}/families` | Thành viên hộ gia đình — phục vụ kê khai BHXH. | `employee.read` |  | tự dò: v2 `hr` |
| PUT | `/api/employees/{eid}/families` | set employee families | `employee.write` |  | tự dò: v2 `hr` |
| POST | `/api/employees/{eid}/id-image/{side}` | Tải ảnh CCCD mặt trước / mặt sau. | `employee.write` |  | tự dò: v2 `hr` |
| GET | `/api/employees/{eid}/labor-contract-templates` | list employee templates | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/employees/{eid}/labor-contracts` | list employee contracts | `labor_contract.read` |  | tự dò: v2 `hr` |
| POST | `/api/employees/{eid}/labor-contracts` | create contract | `labor_contract.create` |  | tự dò: v2 `hr` |
| GET | `/api/employees/{eid}/pending-work` | duoc-CR-665 (V0-4): việc duyệt người này đang giữ — xem TRƯỚC khi khóa tài khoản / cho nghỉ việc. | `employee.read` |  | tự dò: v2 `hr` |
| POST | `/api/employees/{eid}/set-password` | Đặt mật khẩu tài khoản của nhân sự. | `employee.write` |  | tự dò: v2 `hr` |
| POST | `/api/employees/{eid}/signature` | Đặt ảnh chữ ký cho nhân sự (HR làm hộ). | `employee.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/employees/{eid}/signature` | Gỡ chữ ký của nhân sự. | `employee.write` |  | tự dò: v2 `hr` |
| GET | `/api/employees/{eid}/work-history` | list work history | `employee.read` |  | tự dò: v2 `hr` |
| POST | `/api/employees/{eid}/work-history` | create work history | `employee.write` |  | tự dò: v2 `hr` |
| PATCH | `/api/employees/{eid}/work-history/{hid}` | update work history | `employee.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/employees/{eid}/work-history/{hid}` | delete work history | `employee.write` |  | tự dò: v2 `hr` |
| POST | `/api/employees/{eid}/work-history/{hid}/apply` | apply work history | `employee.write` |  | tự dò: v2 `hr` |
| GET | `/api/holiday-work-report/summary` | holiday work summary | `báo cáo 30`, `leave_comp_request.read` |  | tự dò: v2 `report` |
| GET | `/api/holiday-work-report/summary/export` | holiday work summary export | `báo cáo 30`, `leave_comp_request.export` |  | tự dò: v2 `report` |
| GET | `/api/holiday-work-report/summary/rows` | holiday work summary rows | `báo cáo 30`, `leave_comp_request.read` |  | tự dò: v2 `report` |
| GET | `/api/holidays` | Danh sách nghỉ phép › Thiết lập › Lịch ngày lễ, có lọc và phân trang. | `holiday.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/holidays` | Thêm một dòng nghỉ phép › Thiết lập › Lịch ngày lễ; chặn trùng mã, ghi nhật ký. | `holiday.create` |  | tự dò: v2 `hr` |
| GET | `/api/holidays/{oid}` | Xem một dòng nghỉ phép › Thiết lập › Lịch ngày lễ theo id. | `holiday.read` | `get_scoped` |  |
| PATCH | `/api/holidays/{oid}` | Sửa một dòng nghỉ phép › Thiết lập › Lịch ngày lễ; chỉ ghi các ô gửi lên, ghi nhật ký. | `holiday.write` | `get_scoped` |  |
| DELETE | `/api/holidays/{oid}` | Xóa một dòng nghỉ phép › Thiết lập › Lịch ngày lễ; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `holiday.delete` | `get_scoped` |  |
| GET | `/api/job-positions` | Danh sách danh mục Chức vụ, có lọc và phân trang. | `job_position.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/job-positions` | Thêm một dòng danh mục Chức vụ; chặn trùng mã, ghi nhật ký. | `job_position.create` |  | tự dò: v2 `hr` |
| GET | `/api/job-positions/export/csv` | Xuất danh mục Chức vụ ra tệp CSV theo bộ lọc đang chọn. | `job_position.export` | `apply_scope` |  |
| POST | `/api/job-positions/import/csv` | Nhập danh mục Chức vụ hàng loạt từ tệp CSV (thêm, sửa, xóa theo cột hành động). | `job_position.import` | `scope_condition` |  |
| GET | `/api/job-positions/{oid}` | Xem một dòng danh mục Chức vụ theo id. | `job_position.read` | `get_scoped` |  |
| PATCH | `/api/job-positions/{oid}` | Sửa một dòng danh mục Chức vụ; chỉ ghi các ô gửi lên, ghi nhật ký. | `job_position.write` | `get_scoped` |  |
| DELETE | `/api/job-positions/{oid}` | Xóa một dòng danh mục Chức vụ; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `job_position.delete` | `get_scoped` |  |
| GET | `/api/job-positions/{position_id}/roles` | get position roles | `role.read` |  | tự dò: v2 `hr` |
| PUT | `/api/job-positions/{position_id}/roles` | set position roles | `role.write` |  | tự dò: v2 `hr` |
| POST | `/api/job-positions/{position_id}/roles/apply` | apply position roles | `role.write` |  |  |
| GET | `/api/labor-contract-templates` | list templates | `labor_contract_template.read` |  | tự dò: v2 `hr`, v2 dùng chung |
| POST | `/api/labor-contract-templates` | create template | `labor_contract_template.create` |  | tự dò: v2 `hr`, v2 dùng chung |
| GET | `/api/labor-contract-templates/placeholders` | list placeholders | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/labor-contract-templates/{template_id}` | get template | `labor_contract_template.read` |  | tự dò: v2 `hr` |
| PATCH | `/api/labor-contract-templates/{template_id}` | update template | `labor_contract_template.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/labor-contract-templates/{template_id}` | delete template | `labor_contract_template.delete` |  | tự dò: v2 `hr` |
| GET | `/api/labor-contract-templates/{template_id}/content` | duoc-CR-606 — tệp mẫu mở thành HTML + lề trái/phải, cho trang soạn trên web. | `labor_contract_template.read` |  | tự dò: v2 `hr` |
| PUT | `/api/labor-contract-templates/{template_id}/content` | Lưu nội dung soạn trên web thành .docx — kiểm biến y như tải tệp lên. | `labor_contract_template.write` |  | tự dò: v2 `hr` |
| GET | `/api/labor-contract-templates/{template_id}/file` | download template file | `labor_contract_template.read` |  | tự dò: v2 `hr` |
| PUT | `/api/labor-contract-templates/{template_id}/file` | replace template file | `labor_contract_template.write` |  | tự dò: v2 `hr` |
| GET | `/api/labor-contract-variables` | list variables | `labor_contract_template.read` |  | tự dò: v2 `hr` |
| POST | `/api/labor-contract-variables` | create variable | `labor_contract_template.write` |  | tự dò: v2 `hr` |
| GET | `/api/labor-contract-variables/input-fields` | input fields | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/labor-contract-variables/{variable_id}` | get variable | `labor_contract_template.read` |  | tự dò: v2 `hr` |
| PATCH | `/api/labor-contract-variables/{variable_id}` | update variable | `labor_contract_template.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/labor-contract-variables/{variable_id}` | delete variable | `labor_contract_template.delete` |  | tự dò: v2 `hr` |
| GET | `/api/labor-contracts/expiring` | HĐLĐ sắp hết / đã hết hạn trong phạm vi người xem (duoc-CR-620) — thẻ Tổng quan Nhân sự. | `labor_contract.read` |  | tự dò: v2 `hr` |
| GET | `/api/labor-contracts/summary` | labor contract summary | `báo cáo 17`, `labor_contract.read` |  | tự dò: v2 `report` |
| GET | `/api/labor-contracts/summary/export` | labor contract summary export | `báo cáo 17`, `labor_contract.export` |  | tự dò: v2 `report` |
| GET | `/api/labor-contracts/summary/rows` | labor contract summary rows | `báo cáo 17`, `labor_contract.read` |  | tự dò: v2 `report` |
| GET | `/api/labor-contracts/{cid}` | get contract | `labor_contract.read` |  | tự dò: v2 `hr` |
| PATCH | `/api/labor-contracts/{cid}` | update contract | `labor_contract.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/labor-contracts/{cid}` | delete contract | `labor_contract.delete` |  | tự dò: v2 `hr` |
| GET | `/api/labor-contracts/{cid}/document` | download document | `labor_contract.print` |  | tự dò: v2 `hr` |
| POST | `/api/labor-contracts/{cid}/generate` | generate document | `labor_contract.write` |  | tự dò: v2 `hr` |
| GET | `/api/labor-contracts/{cid}/signed-file` | download signed file | `labor_contract.read` |  | tự dò: v2 `hr` |
| PUT | `/api/labor-contracts/{cid}/signed-file` | upload signed file | `labor_contract.write` |  | tự dò: v2 `hr` |
| GET | `/api/labor-contracts/{cid}/templates` | Ô chọn mẫu của hộp "Sinh tệp": mẫu theo pháp nhân + loại CỦA HĐ (không theo NV hiện tại). | `labor_contract.write` |  | tự dò: v2 `hr` |
| POST | `/api/labor-contracts/{cid}/transition` | transition contract | `labor_contract.write` |  | tự dò: v2 `hr` |
| GET | `/api/labor-register/summary` | labor register summary | `báo cáo 19`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/labor-register/summary/export` | labor register summary export | `báo cáo 19`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/labor-register/summary/rows` | labor register summary rows | `báo cáo 19`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/labor-usage-report/summary` | labor usage summary | `báo cáo 20`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/labor-usage-report/summary/export` | labor usage summary export | `báo cáo 20`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/labor-usage-report/summary/rows` | labor usage summary rows | `báo cáo 20`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/leave-balances` | Quỹ trong phạm vi người xem ("Quỹ của tôi" khi phạm vi = own). | `leave_balance.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/leave-balances/allocate` | Cấp phát quỹ hàng loạt cho một năm — Q1: cấp MỘT LẦN đầu năm. | `leave_balance.create` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/leave-balances/close-year` | Kết sổ cuối năm — số dư đi tiếp theo luật của từng loại nghỉ. | `leave_balance.write` | `apply_scope` | tự dò: v2 `hr` |
| GET | `/api/leave-balances/close-year/review` | Bảng đối chiếu trước/sau kết sổ năm `year` (mặc định năm ngoái), mỗi dòng một (người x loại). | `leave_balance.read` |  | tự dò: v2 `hr` |
| GET | `/api/leave-balances/close-year/review/export` | Xuất Excel bảng đối chiếu kết sổ — cùng dữ liệu `close_year_review`. | `leave_balance.export` |  | tự dò: v2 `hr` |
| GET | `/api/leave-balances/matrix` | Ma trận nhân sự x loại nghỉ. | `leave_balance.read` |  | tự dò: v2 `hr` |
| GET | `/api/leave-balances/matrix/export` | Xuất Excel ma trận — nhận cùng `sort_by` / `sort_dir` với bảng nên tệp ra đúng thứ tự đang xem. | `leave_balance.export` |  | tự dò: v2 `hr` |
| GET | `/api/leave-balances/summary` | leave balance summary | `báo cáo 8`, `leave_balance.read` |  | tự dò: v2 `report` |
| GET | `/api/leave-balances/summary/export` | leave balance summary export | `báo cáo 8`, `leave_balance.export` |  | tự dò: v2 `report` |
| GET | `/api/leave-balances/summary/rows` | Bấm một con số ra danh sách người/dòng quỹ — cùng cổng với `/summary` (CR-686). | `báo cáo 8`, `leave_balance.read` |  | tự dò: v2 `report` |
| GET | `/api/leave-balances/tools/summary` | Toàn bộ quỹ của MỘT người trong một năm — dữ liệu của thẻ "Quỹ phép của tôi". | `leave_balance.read` | `apply_scope` | tự dò: v2 `hr` |
| GET | `/api/leave-balances/{bid}` | get balance | `leave_balance.read` | `get_scoped` | tự dò: v2 `hr` |
| PATCH | `/api/leave-balances/{bid}/adjust` | Chỉnh tay — cộng hoặc TRỪ. | `leave_balance.write` | `get_scoped` | tự dò: v2 `hr` |
| GET | `/api/leave-block-periods` | Danh sách nghỉ phép › Thiết lập › Loại nghỉ, có lọc và phân trang. | `leave_type.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/leave-block-periods` | Thêm một dòng nghỉ phép › Thiết lập › Loại nghỉ; chặn trùng mã, ghi nhật ký. | `leave_type.create` |  | tự dò: v2 `hr` |
| GET | `/api/leave-block-periods/{oid}` | Xem một dòng nghỉ phép › Thiết lập › Loại nghỉ theo id. | `leave_type.read` | `get_scoped` |  |
| PATCH | `/api/leave-block-periods/{oid}` | Sửa một dòng nghỉ phép › Thiết lập › Loại nghỉ; chỉ ghi các ô gửi lên, ghi nhật ký. | `leave_type.write` | `get_scoped` |  |
| DELETE | `/api/leave-block-periods/{oid}` | Xóa một dòng nghỉ phép › Thiết lập › Loại nghỉ; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `leave_type.delete` | `get_scoped` |  |
| GET | `/api/leave-comp-requests` | Danh sách trong phạm vi người xem. | `leave_comp_request.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/leave-comp-requests` | create request | `leave_comp_request.create` |  | tự dò: v2 `hr` |
| GET | `/api/leave-comp-requests/to-approve` | Phiếu ĐANG chờ chính tôi ký (kèm `task` = việc của tôi, `flow` = luồng duyệt). | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/leave-comp-requests/{rid}` | Chi tiết. | `leave_comp_request.read` |  | tự dò: v2 `hr` |
| PATCH | `/api/leave-comp-requests/{rid}` | update request | `leave_comp_request.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/leave-comp-requests/{rid}` | delete request | `leave_comp_request.delete` |  | tự dò: v2 `hr` |
| POST | `/api/leave-comp-requests/{rid}/approve` | Duyệt THẲNG — chỉ khi phiếu không chạy trong luồng nhiều bước. | `leave_comp_request.approve` |  | tự dò: v2 `hr` |
| POST | `/api/leave-comp-requests/{rid}/cancel` | Hủy: Nháp / Chờ duyệt / Trả về → Đã hủy (rút phiên duyệt trước); Đã duyệt → trừ lại nếu còn đủ, không thì 422. | `leave_comp_request.cancel` |  | tự dò: v2 `hr` |
| POST | `/api/leave-comp-requests/{rid}/reject` | Từ chối THẲNG — cùng điều kiện với `/approve`. | `leave_comp_request.approve` |  | tự dò: v2 `hr` |
| POST | `/api/leave-comp-requests/{rid}/submit` | Gửi duyệt: kiểm TRƯỚC, trình bộ máy SAU. | `leave_comp_request.write` |  | tự dò: v2 `hr` |
| GET | `/api/leave-encashments` | Danh sách phiếu thanh toán nghỉ phép trong phạm vi người xem. | `leave_encashment.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/leave-encashments` | Lập phiếu thanh toán nghỉ phép (Nháp) cho chính mình hoặc lập hộ. | `leave_encashment.create` |  | tự dò: v2 `hr` |
| GET | `/api/leave-encashments/preview` | Xem trước số ngày được thanh toán (chỉ đọc, không cấp quỹ, không khóa) để điền form. | `leave_encashment.create` |  | tự dò: v2 `hr` |
| GET | `/api/leave-encashments/to-approve` | Phiếu ĐANG chờ chính tôi ký (kèm `task` = việc của tôi, `flow` = luồng duyệt). | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/leave-encashments/{rid}` | Chi tiết phiếu. | `leave_encashment.read` |  | tự dò: v2 `hr` |
| PATCH | `/api/leave-encashments/{rid}` | Sửa phiếu Nháp / Trả về (lý do, ngày, số ngày, ghi chú). | `leave_encashment.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/leave-encashments/{rid}` | Xóa mềm phiếu Nháp. | `leave_encashment.delete` |  | tự dò: v2 `hr` |
| POST | `/api/leave-encashments/{rid}/approve` | Duyệt THẲNG — chỉ khi phiếu không chạy trong luồng nhiều bước. | `leave_encashment.approve` |  | tự dò: v2 `hr` |
| POST | `/api/leave-encashments/{rid}/cancel` | Hủy phiếu: Nháp / Chờ duyệt / Trả về -> Đã hủy (rút phiên duyệt trước); Đã duyệt -> trả ngày về quỹ. | `leave_encashment.cancel` |  | tự dò: v2 `hr` |
| POST | `/api/leave-encashments/{rid}/reject` | Từ chối THẲNG (trả ngày giữ chỗ) — cùng điều kiện với `/approve`. | `leave_encashment.approve` |  | tự dò: v2 `hr` |
| POST | `/api/leave-encashments/{rid}/submit` | Gửi duyệt: khóa quỹ, kiểm lại số được phép, giữ chỗ ngày, trình bộ máy duyệt. | `leave_encashment.write` |  | tự dò: v2 `hr` |
| GET | `/api/leave-policies` | Danh sách nghỉ phép › Thiết lập › Loại nghỉ, có lọc và phân trang. | `leave_type.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/leave-policies` | Thêm một dòng nghỉ phép › Thiết lập › Loại nghỉ; chặn trùng mã, ghi nhật ký. | `leave_type.create` |  | tự dò: v2 `hr` |
| GET | `/api/leave-policies/{oid}` | Xem một dòng nghỉ phép › Thiết lập › Loại nghỉ theo id. | `leave_type.read` | `get_scoped` |  |
| PATCH | `/api/leave-policies/{oid}` | Sửa một dòng nghỉ phép › Thiết lập › Loại nghỉ; chỉ ghi các ô gửi lên, ghi nhật ký. | `leave_type.write` | `get_scoped` |  |
| DELETE | `/api/leave-policies/{oid}` | Xóa một dòng nghỉ phép › Thiết lập › Loại nghỉ; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `leave_type.delete` | `get_scoped` |  |
| GET | `/api/leave-policies/{policy_id}/lines` | Dòng của gói (loại nghỉ → số ngày/năm). | `leave_type.read` |  | tự dò: v2 `hr` |
| PUT | `/api/leave-policies/{policy_id}/lines` | THAY cả danh sách dòng. | `leave_type.write` |  | tự dò: v2 `hr` |
| GET | `/api/leave-policy-assignments` | Phân bổ trong phạm vi người xem. | `leave_balance.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/leave-policy-assignments` | Phân bổ cho MỘT nhân sự → `{assignment, balances:{created, recalculated[], kept, negative_after[]}}`. | `leave_balance.write` |  | tự dò: v2 `hr` |
| POST | `/api/leave-policy-assignments/bulk` | Phân bổ HÀNG LOẠT (≤500). | `leave_balance.write` |  | tự dò: v2 `hr` |
| POST | `/api/leave-policy-assignments/preview` | XEM TRƯỚC — dùng chung `plan_change` với đường ghi, KHÔNG ghi gì. | `leave_balance.write` |  | tự dò: v2 `hr` |
| GET | `/api/leave-policy-assignments/{aid}` | get assignment | `leave_balance.read` | `get_scoped` | tự dò: v2 `hr` |
| PATCH | `/api/leave-policy-assignments/{aid}` | Chỉ sửa `effective_to` (null = không thời hạn) và `note`; đổi gói / ngày bắt đầu = xóa rồi tạo lại. | `leave_balance.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/leave-policy-assignments/{aid}` | Xóa phân bổ; `?recalc_current_year=true` thì tính lại các loại của gói về luật của loại. | `leave_balance.write` |  | tự dò: v2 `hr` |
| GET | `/api/leave-requests` | Danh sách đơn trong phạm vi người xem ("Đơn của tôi" khi phạm vi = own). | `leave_request.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/leave-requests` | create request | `leave_request.create` |  | tự dò: v2 `hr` |
| GET | `/api/leave-requests/inbox/handled` | Đơn chính tôi vừa duyệt / trả về / từ chối gần đây — MỖI ĐƠN MỘT DÒNG. | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/leave-requests/inbox/to-approve` | Đơn ĐANG chờ chính tôi ký, kèm đủ thông tin để quyết ngay trên dòng. | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/leave-requests/summary` | leave request summary | `báo cáo 7`, `leave_request.read` |  | tự dò: v2 `report` |
| GET | `/api/leave-requests/summary/export` | leave request summary export | `báo cáo 7`, `leave_request.export` |  | tự dò: v2 `report` |
| GET | `/api/leave-requests/summary/rows` | Bấm một con số ra danh sách đơn — cùng cổng quyền/phạm vi với `/summary` (CR-686). | `báo cáo 7`, `leave_request.read` |  | tự dò: v2 `report` |
| GET | `/api/leave-requests/tools/estimate-days` | Số ngày GỢI Ý cho khoảng đang chọn — form gọi mỗi lần đổi ngày. | `leave_request.read` |  | tự dò: v2 `hr` |
| POST | `/api/leave-requests/tools/estimate-periods` | Số ngày GỢI Ý cho từng khoảng của đơn nhiều khoảng (duoc-CR-683). | `leave_request.read` |  | tự dò: v2 `hr` |
| GET | `/api/leave-requests/tools/my-balance` | Số phép còn lại — ràng buộc §6.1: form phải hiện con số này lúc nộp. | `leave_request.read` |  | tự dò: v2 `hr` |
| GET | `/api/leave-requests/{rid}` | get request | `leave_request.read` |  | tự dò: v2 `hr` |
| PATCH | `/api/leave-requests/{rid}` | update request | `leave_request.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/leave-requests/{rid}` | delete request | `leave_request.delete` |  | tự dò: v2 `hr` |
| POST | `/api/leave-requests/{rid}/approve` | Duyệt THẲNG — chỉ dùng khi môi trường chưa khai luồng nhiều bước. | `leave_request.approve` |  | tự dò: v2 `hr` |
| POST | `/api/leave-requests/{rid}/cancel` | Hủy đơn và TRẢ LẠI quỹ — cả đơn đang chờ lẫn đơn đã duyệt. | `leave_request.cancel` |  | tự dò: v2 `hr` |
| POST | `/api/leave-requests/{rid}/reject` | Từ chối THẲNG — cùng điều kiện với `/approve`. | `leave_request.approve` |  | tự dò: v2 `hr` |
| POST | `/api/leave-requests/{rid}/submit` | Gửi duyệt: kiểm đủ phép TRƯỚC, trình bộ máy SAU, rồi mới giữ chỗ quỹ. | `leave_request.write` |  | tự dò: v2 `hr` |
| GET | `/api/leave-seniority-tiers` | Bậc thâm niên, thường hỏi theo một loại nghỉ. | `leave_type.read` |  | tự dò: v2 `hr` |
| POST | `/api/leave-seniority-tiers` | create tier | `leave_type.create` |  | tự dò: v2 `hr` |
| PATCH | `/api/leave-seniority-tiers/{tid}` | update tier | `leave_type.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/leave-seniority-tiers/{tid}` | delete tier | `leave_type.delete` |  | tự dò: v2 `hr` |
| GET | `/api/leave-types` | Danh sách nghỉ phép › Thiết lập › Loại nghỉ, có lọc và phân trang. | `leave_type.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/leave-types` | Thêm một dòng nghỉ phép › Thiết lập › Loại nghỉ; chặn trùng mã, ghi nhật ký. | `leave_type.create` |  | tự dò: v2 `hr` |
| GET | `/api/leave-types/{oid}` | Xem một dòng nghỉ phép › Thiết lập › Loại nghỉ theo id. | `leave_type.read` | `get_scoped` |  |
| PATCH | `/api/leave-types/{oid}` | Sửa một dòng nghỉ phép › Thiết lập › Loại nghỉ; chỉ ghi các ô gửi lên, ghi nhật ký. | `leave_type.write` | `get_scoped` |  |
| DELETE | `/api/leave-types/{oid}` | Xóa một dòng nghỉ phép › Thiết lập › Loại nghỉ; danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `leave_type.delete` | `get_scoped` |  |
| GET | `/api/leave-types/{type_id}/quotas` | Hạn mức theo hình thức nhân viên / cấp bậc của một loại nghỉ. | `leave_type.read` |  | tự dò: v2 `hr` |
| PUT | `/api/leave-types/{type_id}/quotas` | THAY cả danh sách hạn mức. | `leave_type.write` |  | tự dò: v2 `hr` |
| GET | `/api/legal-watch/summary` | legal watch summary | `báo cáo 29`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/legal-watch/summary/export` | legal watch summary export | `báo cáo 29`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/legal-watch/summary/rows` | legal watch summary rows | `báo cáo 29`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/management-span/summary` | management span summary | `báo cáo 23`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/management-span/summary/export` | management span export | `báo cáo 23`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/management-span/summary/rows` | management span rows | `báo cáo 23`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/me/labor-contracts` | list my contracts | đăng nhập |  | tự dò: v2 `hr`, v2 dùng chung |
| GET | `/api/me/labor-contracts/{cid}/document` | download my document | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/me/labor-contracts/{cid}/signed-file` | download my signed file | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/meeting-rooms` | Danh sách phòng họp (danh mục), có lọc và phân trang. | `meeting_room.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/meeting-rooms` | Thêm một dòng phòng họp (danh mục); chặn trùng mã, ghi nhật ký. | `meeting_room.create` |  | tự dò: v2 `hr` |
| GET | `/api/meeting-rooms/{oid}` | Xem một dòng phòng họp (danh mục) theo id. | `meeting_room.read` | `get_scoped` |  |
| PATCH | `/api/meeting-rooms/{oid}` | Sửa một dòng phòng họp (danh mục); chỉ ghi các ô gửi lên, ghi nhật ký. | `meeting_room.write` | `get_scoped` |  |
| DELETE | `/api/meeting-rooms/{oid}` | Xóa một dòng phòng họp (danh mục); danh mục có xóa mềm thì chỉ đánh dấu, đang được nơi khác dùng thì chặn. | `meeting_room.delete` | `get_scoped` |  |
| GET | `/api/org-chart` | get org chart | `employee.read` | `apply_scope`, `scope_condition` | tự dò: v2 `hr` |
| GET | `/api/payroll-fund/summary` | payroll fund summary | `báo cáo 21`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/payroll-fund/summary/export` | payroll fund summary export | `báo cáo 21`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/payroll-fund/summary/rows` | payroll fund summary rows | `báo cáo 21`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/profile-change-report/summary` | profile change summary | `báo cáo 27`, `employee.write` |  | tự dò: v2 `report` |
| GET | `/api/profile-change-report/summary/export` | profile change summary export | `báo cáo 27`, `employee.write`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/profile-change-report/summary/rows` | profile change summary rows | `báo cáo 27`, `employee.write` |  | tự dò: v2 `report` |
| GET | `/api/room-bookings` | Danh sách phiếu trong phạm vi người xem; `scope=mine` thu về phiếu của chính người gọi. | `room_booking.read` | `apply_scope` | tự dò: v2 `hr` |
| POST | `/api/room-bookings` | create booking | `room_booking.create` |  | tự dò: v2 `hr` |
| GET | `/api/room-bookings/availability` | Phòng nào trống trong khoảng này — **cảnh báo sớm**, không phải chốt chặn. | `room_booking.read` |  | tự dò: v2 `hr` |
| GET | `/api/room-bookings/inbox/handled` | Phiếu chính tôi vừa duyệt / trả về / từ chối gần đây — MỖI PHIẾU MỘT DÒNG. | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/room-bookings/inbox/to-approve` | Phiếu ĐANG chờ chính tôi ký, kèm đủ thông tin để quyết ngay trên dòng. | đăng nhập |  | tự dò: v2 `hr` |
| GET | `/api/room-bookings/{bid}` | get booking | `room_booking.read` |  | tự dò: v2 `hr` |
| PATCH | `/api/room-bookings/{bid}` | update booking | `room_booking.write` |  | tự dò: v2 `hr` |
| DELETE | `/api/room-bookings/{bid}` | delete booking | `room_booking.delete` |  | tự dò: v2 `hr` |
| POST | `/api/room-bookings/{bid}/approve` | Duyệt THẲNG — chỉ dùng khi môi trường chưa khai luồng nhiều bước. | `room_booking.approve` |  | tự dò: v2 `hr` |
| GET | `/api/room-bookings/{bid}/attendees` | Danh sách người được mời — tách khỏi `/{bid}` cho màn nào chỉ cần phần này. | `room_booking.read` |  | tự dò: v2 `hr` |
| POST | `/api/room-bookings/{bid}/cancel` | Hủy phiếu và NHẢ phòng — cả phiếu đang chờ lẫn phiếu đã duyệt. | `room_booking.cancel` |  | tự dò: v2 `hr` |
| POST | `/api/room-bookings/{bid}/reject` | Từ chối THẲNG — cùng điều kiện với `/approve`. | `room_booking.approve` |  | tự dò: v2 `hr` |
| PATCH | `/api/room-bookings/{bid}/reschedule` | Dời giờ / đổi phòng — đường phục vụ thao tác KÉO THẢ trên màn Lịch. | `room_booking.write` |  | tự dò: v2 `hr` |
| POST | `/api/room-bookings/{bid}/submit` | Gửi duyệt: kiểm phòng trống TRƯỚC, trình bộ máy SAU, rồi mới giữ phòng. | `room_booking.write` |  | tự dò: v2 `hr` |
| GET | `/api/room-usage/summary` | room usage summary | `báo cáo 28`, `room_booking.read` |  | tự dò: v2 `report` |
| GET | `/api/room-usage/summary/export` | room usage summary export | `báo cáo 28`, `room_booking.export` |  | tự dò: v2 `report` |
| GET | `/api/room-usage/summary/rows` | room usage summary rows | `báo cáo 28`, `room_booking.read` |  | tự dò: v2 `report` |
| GET | `/api/work-moves/summary` | work moves summary | `báo cáo 24`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/work-moves/summary/export` | work moves export | `báo cáo 24`, `employee.export` |  | tự dò: v2 `report` |
| GET | `/api/work-moves/summary/rows` | work moves rows | `báo cáo 24`, `employee.read` |  | tự dò: v2 `report` |
| GET | `/api/work-schedule-assignments` | list assignments | `work_schedule.read` | `apply_scope`, `scope_condition` | tự dò: v2 `hr` |
| POST | `/api/work-schedule-assignments` | create assignment | `work_schedule.create` |  | tự dò: v2 `hr` |
| GET | `/api/work-schedule-assignments/{oid}` | get assignment | `work_schedule.read` |  |  |
| PATCH | `/api/work-schedule-assignments/{oid}` | update assignment | `work_schedule.write` |  |  |
| DELETE | `/api/work-schedule-assignments/{oid}` | delete assignment | `work_schedule.delete` |  |  |
| GET | `/api/work-schedules` | list schedules | `work_schedule.read` | `apply_scope` | tự dò: v2 `hr`, v2 dùng chung |
| POST | `/api/work-schedules` | create schedule | `work_schedule.create` |  | tự dò: v2 `hr`, v2 dùng chung |
| GET | `/api/work-schedules/tools/effective` | Lịch làm việc hiệu lực của một nhân sự vào `on_date` (mặc định hôm nay). | `employee.read` | `get_scoped` | tự dò: v2 `hr` |
| GET | `/api/work-schedules/tools/roster` | "Ai làm / ai nghỉ" từng ngày — lưới nhân sự × ngày (tối đa 42 ngày, phân trang theo người). | `employee.read` |  | tự dò: v2 `hr` |
| GET | `/api/work-schedules/{oid}` | get schedule | `work_schedule.read` |  |  |
| PATCH | `/api/work-schedules/{oid}` | update schedule | `work_schedule.write` |  |  |
| DELETE | `/api/work-schedules/{oid}` | delete schedule | `work_schedule.delete` |  |  |

## 2. Dữ liệu vào / ra chính

Mới viết phần **Kiêm nhiệm** (duoc-CR-755). Luật nghiệp vụ đầy đủ: [`../01-ho-so-nhan-su.md` §7.18](../01-ho-so-nhan-su.md).

| Đường | Trường | Ý nghĩa / luật |
|---|---|---|
| `GET /api/employees/{eid}/concurrents` | `items[]` | Mọi dòng kiêm nhiệm của một người, mới nhất trước. Mỗi dòng: `company_id` + `company_name`, `department_id` + `department_name`, `position_id` + `position_label` (nhãn chụp), `from_date`, `to_date`, `decision_no`, `decision_date`, `note`, `counts_scope`, `work_history_id` (0 = nhập tay), `status` (số `ConcurrentStatus`: 1 Sắp tới · 2 Đang hiệu lực · 3 Đã hết, dẫn xuất từ ngày theo giờ VN) + `status_label`, `file_count` |
| | `can_edit` · `can_open_files` | Cờ do backend tính: `can_edit` = có `employee.write` đúng phạm vi hồ sơ và không phải hồ sơ của chính mình (L1, kể cả quản trị); `can_open_files` = đọc được nhạy cảm của hồ sơ (chính chủ luôn được). Giao diện chỉ dựa vào hai cờ này |
| `POST /api/employees/{eid}/concurrents` | thân `ConcurrentIn` | `company_id` > 0, `department_id` > 0 bắt buộc; `position_id` (0 = không); `from_date` bắt buộc; `to_date` trống = chưa kết thúc, phải ≥ `from_date`; ngày trong 1900-2100; `decision_no` ≤ 50, `note` ≤ 500; `counts_scope` mặc định `true`. Khóa lạ → 422. Trả `{item}`, mã 201 |
| `PATCH /api/employees/{eid}/concurrents/{cid}` | thân `ConcurrentPatch` | Gửi ô nào đổi ô đó, sửa TẠI CHỖ (id + tệp giữ nguyên). Chỉ `to_date` / `decision_date` được gửi `null` (mở lại / xóa ngày); ô khác gửi `null` → 422. Đổi cặp (phòng, công ty) thì L2 đo cả cặp cũ lẫn mới |
| `DELETE /api/employees/{eid}/concurrents/{cid}` | — | Xóa dòng kèm tệp QĐ. Dòng có tệp của người khác cần thêm `employee_sensitive.read` |
| `GET /api/employee-concurrents` | `department_id` (bắt buộc, > 0) · `company_id` (tùy chọn) · `include_ended` (0/1) | Người đang kiêm nhiệm ở một phòng — chỉ dòng mà phạm vi `employee.read` của người xem phủ cặp (phòng, công ty); bỏ người đã nghỉ việc, dòng trùng phòng chính; mặc định bỏ dòng đã hết. Trả `{items, total, truncated}`, trần 200, xếp họ tên. Mỗi dòng là bản tóm tắt: `id`, `employee_id`, `code`, `full_name`, `position_label`, công ty + phòng kiêm nhiệm, `from_date`, `to_date`, `status` + `status_label`, `counts_scope`, `primary_company_*`, `primary_department_*`, `can_open` (mở được hồ sơ đầy đủ không). Không điện thoại, email, ngày sinh |
| `PATCH /api/employees/{id}` | `end_old_company_concurrent: bool \| null` · `keep_concurrent_ids: int[]` (≤ 30) | Trường ĐIỀU KHIỂN (không phải cột), chỉ có tác dụng khi `company_id` đổi sang công ty khác 0. `null` / `true` = kết thúc dòng kiêm nhiệm ở công ty cũ (đến ngày = hôm qua) trừ id trong `keep_concurrent_ids`; `false` = giữ hết. Dòng đã hết không đụng; dòng chưa bắt đầu bị XÓA kèm tệp; dòng ở công ty khác không đụng |
| `PATCH /api/employees/{id}` | `keep_old_department` | (có từ bao-CR-709) đổi phòng chính mà giữ phòng cũ → nay tạo dòng kiêm nhiệm (phòng cũ, công ty trước lần lưu, từ hôm nay, công tắc bật) |
| `POST /api/employees/{eid}/work-history/{hid}/apply` | loại Kiêm nhiệm (mã 4) | Ghi / cập nhật MỘT dòng kiêm nhiệm khóa `work_history_id`; `applied_changes` là *Kiêm nhiệm — thêm phòng "X"* / *cập nhật phòng "X"* / *kết thúc phòng "X" (đến dd/mm/yyyy)* |
| `GET /api/org-chart` | `concurrents[]` | Dòng kiêm nhiệm ĐANG HIỆU LỰC trong phạm vi người xem, cùng hình dạng dòng của `/api/employee-concurrents` |
| `GET /api/auth/me` | `kiem_nhiem[]` · `concurrents[]` | `kiem_nhiem` = câu *Phòng X — Công ty B (Chức vụ)* của mọi dòng đang hiệu lực (kể cả tắt công tắc); `concurrents` có cấu trúc (`department_id`, `company_id`, tên, `position_label`, `counts_scope`) cho popup phạm vi |
| `GET /api/employees/{eid}/departments` | `extra_department_ids` | Giữ cho tương thích: = phòng kiêm nhiệm đang hiệu lực CÙNG công ty chính. Đường `PUT` cùng tên ĐÃ BỎ |
| MCP `employee_lookup` | `concurrent_roles[]` | Câu *Phòng X — Công ty B (Chức vụ)* của các dòng đang hiệu lực; rỗng = không kiêm nhiệm. Bộ lọc người không đổi |

## 3. Lỗi riêng của phân hệ

Mới viết phần **Kiêm nhiệm**.

| Mã HTTP | Khi nào | Câu báo |
|---|---|---|
| 400 | Phòng không phục vụ công ty đã chọn (L3) | *Phòng ban "X" không phục vụ công ty đã chọn* |
| 400 | Phòng trùng phòng chính | *Trùng phòng ban chính — phòng này đã là phòng chính của nhân sự* |
| 400 | Quá 30 dòng / người | *Hồ sơ này đã có N dòng kiêm nhiệm — tối đa 30 dòng/người* |
| 400 | Nhập Excel đổi pháp nhân còn dòng chưa bắt đầu ở công ty cũ (lỗi dòng) | *Còn kiêm nhiệm chưa bắt đầu ở công ty cũ — sửa ở tab Kiêm nhiệm trước* |
| 403 | Tự sửa phòng / kiêm nhiệm của chính mình (L1, kể cả quản trị) | *Không tự đổi phòng ban của chính mình được — …* |
| 403 | Cặp đích ngoài phạm vi ghi của người thao tác (L2) | *Không gán được kiêm nhiệm ở phòng ban mà chính bạn không có phạm vi ghi trên đó: "X" (Công ty B). …* |
| 403 | Xóa / gắn / gỡ tệp QĐ của người khác khi thiếu `employee_sensitive.read` | *… cần quyền xem nhạy cảm (employee_sensitive.read) …* |
| 403 | Gắn / gỡ tệp QĐ kiêm nhiệm của chính mình | *Không tự gắn/gỡ tệp quyết định kiêm nhiệm của chính mình được* |
| 404 | Hồ sơ ngoài phạm vi, hoặc `cid` không thuộc `eid` | *Không tìm thấy dòng kiêm nhiệm* |
| 409 | Hai giai đoạn của cùng (phòng, công ty) chồng nhau | *Giai đoạn kiêm nhiệm chồng với một dòng khác của cùng phòng ban và công ty — sửa dòng cũ hoặc đổi ngày.* |
| 422 | `to_date` < `from_date`; gửi `null` cho ô không được null; khóa lạ | *Đến ngày phải sau hoặc bằng từ ngày* |

## 4. Bộ lọc danh sách

| Tham số | Kiểu | Ghi chú |
|---|---|---|
| `department_id` (`/api/employee-concurrents`) | int > 0, bắt buộc | Thiếu / ≤ 0 → 422 |
| `company_id` (`/api/employee-concurrents`) | int > 0, tùy chọn | Chỉ lấy kiêm nhiệm ở công ty này (phòng dùng chung) |
| `include_ended` (`/api/employee-concurrents`) | 0 / 1 | 1 = lấy cả dòng đã hết |

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
| 12/11/2026 | duoc-CR-755 | Thêm `GET/POST /api/employees/{eid}/concurrents`, `PATCH/DELETE /api/employees/{eid}/concurrents/{cid}`, `GET /api/employee-concurrents`; `PATCH /api/employees/{id}` thêm `end_old_company_concurrent`, `keep_concurrent_ids`; `/api/org-chart` và `/api/auth/me` thêm `concurrents`; MCP `employee_lookup` thêm `concurrent_roles`. Bỏ `PUT /api/employees/{eid}/departments` |
