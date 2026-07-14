# Yêu cầu khảo sát (YCKS)

## Mục đích

Ghi nhận nhu cầu khảo sát giá / nhà cung cấp do bộ phận nghiệp vụ lập, chuyển cho nhân sự thu mua (NSTM) thực hiện. Sau khi NSTM gắn đủ phương án (option) — ẩn danh NCC với người yêu cầu — người yêu cầu chọn phương án và hệ thống tự sinh Yêu cầu mua hàng (YCMH/PYC), gom theo nhà cung cấp.

Đường dẫn: `/survey-requests` (danh sách), `/survey-requests/:id` (chi tiết + kết quả khảo sát), `/survey-requests/:id/process` (màn xử lý dành riêng NSTM).

Màn chi tiết hiển thị phần **Lịch sử thao tác** (audit log) ở cột bên phải khi phiếu đã có thao tác được ghi nhận — gọi `GET /api/audit-logs?entity=survey_request&entity_id={id}`.

## Vai trò tham gia

- Người yêu cầu — scope `own` (`survey_request:create` / `write`): lập phiếu, gửi duyệt, chọn phương án, tạo YCMH.
- Trưởng bộ phận / Quản lý — (`survey_request:approve`): duyệt phiếu, trả đơn hoặc từ chối.
- NSTM — scope `proc` (`survey_request:process`): vào màn Xử lý (NCC được hiển thị đầy đủ), gắn option, đặt mã SP hệ thống, chốt hoàn thành khảo sát.
- Admin / Quản lý TM — scope `all` (`survey_request:approve` + `process`): toàn quyền; chuyển phiếu sang Hoàn thành (finalize).

## Vòng đời trạng thái

| Trạng thái | Giá trị DB | Ý nghĩa | Nút thao tác |
|-----------|------------|---------|-------------|
| Nháp | `draft` | Đang soạn | Lưu, Gửi duyệt, Xóa |
| Chờ duyệt | `submitted` | Đã gửi, chờ TP/QL | Duyệt, Trả đơn, Từ chối |
| Đã duyệt | `approved` | Trạng thái trung gian tức thời — tự chuyển ngay sang Đang xử lý | — |
| Bị trả lại | `rejected` | TP/QL trả về, người YC còn sửa và gửi lại được | Lưu, Gửi duyệt lại |
| Đã từ chối | `cancelled` | TP/QL từ chối — khóa vĩnh viễn, không sửa được | — |
| Đang xử lý | `processing` | NSTM đang thực hiện khảo sát | Xử lý khảo sát, Tạo phiếu khảo sát, Lấy từ khảo sát |
| Đã khảo sát | `survey_done` | NSTM đã chốt — người YC chọn phương án | Xử lý khảo sát (vẫn mở), Tạo yêu cầu mua |
| Đã tạo YCMH | `pr_created` | PYC đã sinh, chờ Admin/QL chốt | Chuyển Hoàn thành (Admin/QL TM) |
| Hoàn thành | `done` | Khép kín — không chỉnh sửa | — |

Các chuyển tiếp trạng thái:

- `draft` → `submitted` — endpoint `POST /{id}/submit`; người YC hoặc người có quyền sửa phiếu.
- `submitted` → `approved` → `processing` — endpoint `POST /{id}/approve`; tức thời, hai bước trong một lần gọi; quyền `approve`. Sau đó `auto_assign` gán NSTM theo phân loại.
- `submitted` → `rejected` — endpoint `POST /{id}/reject`; quyền `approve`; phiếu quay về trạng thái có thể sửa.
- `submitted` → `cancelled` — endpoint `POST /{id}/cancel`; quyền `approve`; khóa vĩnh viễn.
- `rejected` → `submitted` — người YC sửa rồi gửi duyệt lại.
- `processing` → `survey_done` — endpoint `POST /{id}/complete`; quyền `process` + `is_purchaser`; mỗi NSTM validate dòng mình phụ trách; phiếu chuyển khi TẤT CẢ dòng (mọi NSTM) đã có option. Mọi option phải có Mã SP hệ thống (kiểm tra phía FE). Có thể gọi lại từ `survey_done`.
- `survey_done` → `pr_created` — endpoint `POST /{id}/create-prs`; người YC (`created_by`) hoặc Admin TM (quyền `delete`).
- `pr_created` → `done` (thủ công) — endpoint `POST /{id}/finalize`; Admin/QL TM (scope `all` + quyền `approve`).
- `pr_created` → `done` (tự động) — hàm `auto_complete_from_pr` kích hoạt khi PYC liên quan chuyển `completed`; nếu mọi PYC của YCKS đều `completed` thì YCKS tự sang `done`.

## Bộ lọc danh sách

Màn danh sách `/survey-requests` hỗ trợ các bộ lọc:

| Nhãn lọc | Param API | Loại | Ghi chú |
|-----------|-----------|------|---------|
| Mã phiếu | `code` | LIKE | |
| Công ty | `company_id` | Bằng (ID) | |
| Người yêu cầu | `requester` | LIKE | |
| Bộ phận | `department` | LIKE | |
| NSTM phụ trách | `assignee` | Bằng (mã NV) | Lọc theo `SurveyRequestLine.assignee` (subquery) |
| Phân loại | `item_group` | LIKE | Lọc theo `SurveyRequestLine.item_group` (subquery) |
| Ngày tạo | `request_date_from` / `request_date_to` | Khoảng ngày | |
| Trạng thái | `status` | Bằng | `draft`, `submitted`, `approved`, `rejected`, `cancelled`, `processing`, `survey_done`, `pr_created`, `done` |

---

## A. Trường header phiếu YCKS

### 1. Mã phiếu (`code`)

- Kiểu nhập: Tự động — không nhập tay
- Mặc định: Sinh ngay sau khi tạo theo quy tắc `YCKS{DDMMYY}{seq:02d}` (VD: `YCKS10072601`). Số thứ tự đếm theo prefix ngày, đặt lại từ 01 mỗi ngày.
- Bắt buộc: Hệ thống điền, không sửa được
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống (trường khóa)
- Logic đặc biệt: Chỉ hiển thị trên màn xem (không hiện khi tạo mới). Đặt sau `db.commit()` đầu tiên để dùng được `id` trong công thức đếm.

### 2. Công ty nhận hóa đơn (`company_id`)

- Kiểu nhập: Chọn (Select, tìm kiếm theo tên)
- Mặc định: Tự điền từ `employee.company_id` của người đang đăng nhập nếu khớp danh sách nhân viên; trống nếu không xác định được
- Bắt buộc: Có — validate khi Lưu/Gửi duyệt: "Vui lòng chọn Công ty"
- Nguồn dữ liệu / liên kết: Bảng Công ty (`tab_company`), API `/api/companies`
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Khi chọn Người yêu cầu từ danh sách nhân viên (`handleRequesterChange`), giá trị `company_id` tự điền theo nhân viên đó; có thể ghi đè. Khi tạo PYC sao chép sang `PurchaseRequest.company_id`.

### 3. Người yêu cầu (`requester`)

- Kiểu nhập: Chọn (Select, tìm theo tên đầy đủ nhân viên)
- Mặc định: Tự điền tên người đang đăng nhập (khớp theo `email` hoặc `full_name`)
- Bắt buộc: Có — "Vui lòng nhập Người yêu cầu"
- Nguồn dữ liệu / liên kết: Bảng Nhân viên (`tab_employee`), API `/api/employees`
- Người sửa: Admin/QL sửa thủ công; người thường (`isStaff`) bị khóa trường
- Logic đặc biệt: Khi chọn nhân viên, tự điền Chức vụ, Bộ phận YC, Trưởng bộ phận, Công ty. Khi tạo PYC sao chép sang `PurchaseRequest.requester`.

### 4. Chức vụ (`requester_position`)

- Kiểu nhập: Nhập tay (tự điền từ nhân viên, có thể sửa sau)
- Mặc định: Tự điền từ `employee.position` hoặc `employee.role_name`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ danh sách nhân viên
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Khi tạo PYC sao chép sang `PurchaseRequest.requester_position`.

### 5. Bộ phận yêu cầu (`department`)

- Kiểu nhập: Chọn (SearchSelect, gõ để lọc)
- Mặc định: Tự điền từ phòng ban của Người yêu cầu
- Bắt buộc: Hiển thị dấu `*` trên form; không validate phía FE — nhưng cần thiết để `auto_assign` và thông báo hoạt động đúng
- Nguồn dữ liệu / liên kết: Bảng Phòng ban (`tab_department`), API `/api/departments`
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Thay đổi Bộ phận khi tạo mới → tự tra API `GET /api/survey-requests/meta/dept-head?department=...` để điền Trưởng bộ phận. Khi tạo PYC sao chép sang `PurchaseRequest.department`. Dùng để gửi thông báo cho trưởng phòng khi người YC gửi duyệt.

### 6. Trưởng bộ phận (`head_of_dept`)

- Kiểu nhập: Chỉ đọc (tự điền)
- Mặc định: Tự điền qua API `meta/dept-head` hoặc tìm nhân viên cùng phòng có chức vụ trưởng
- Bắt buộc: Hiển thị dấu `*` trên form; không validate phía FE
- Nguồn dữ liệu / liên kết: API `/api/survey-requests/meta/dept-head`; tái dùng `find_dept_head` từ module `purchase_request`
- Người sửa: Hệ thống (trường `disabled`)
- Logic đặc biệt: Khi tạo PYC sao chép sang `PurchaseRequest.head_of_dept` (dùng `find_dept_head` làm fallback nếu trống).

### 7. Mục đích khảo sát (`purpose`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Có — "Vui lòng nhập Mục đích khảo sát"
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Khi chọn YCKS trên màn tạo Phiếu khảo sát, trường **Nội dung chính** (`main_content`) của phiếu khảo sát tự điền từ đây. Khi tạo PYC sao chép sang `PurchaseRequest.purpose`.

### 8. Ngày tạo (`request_date` / `created_at`)

- Kiểu nhập: Chọn ngày — chỉ khi TẠO MỚI (nhập `request_date`). Khi XEM phiếu đã tạo, ô hiển thị `created_at` (ngày + giờ đầy đủ từ hệ thống, chỉ đọc); nếu không có `created_at` thì fallback về `request_date`.
- Mặc định: Ngày hiện tại (ISO format `YYYY-MM-DD`)
- Bắt buộc: Hiển thị dấu `*`; không validate phía FE
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC khi phiếu `draft` / `rejected` (chỉ ảnh hưởng đến `request_date`; `created_at` do hệ thống ghi lúc tạo và không thay đổi)
- Logic đặc biệt: `request_date` dùng làm ngày tham chiếu khi sinh mã PYC (`_gen_pr_code`). `created_at` là timestamp tạo phiếu thực tế và được ưu tiên hiển thị trên giao diện.

### 9. NSTM chính (`assignee_id`)

- Kiểu nhập: Tự động
- Mặc định: `0` (chưa gán)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhân viên (`tab_employee.id`)
- Người sửa: Hệ thống — gán qua `auto_assign` sau khi duyệt phiếu
- Logic đặc biệt: Được lấy từ NSTM của dòng đầu tiên có phân loại được cấu hình trong bảng `CategoryAssignee`. Không hiển thị trực tiếp trên form header; dùng để lập báo cáo và lọc theo scope. Nếu không có cấu hình phân loại thì giữ nguyên `0`.

### 10. Ghi chú (`note`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC khi phiếu `draft` / `rejected`

### 11. Lý do trả đơn / từ chối (`reject_reason`)

- Kiểu nhập: Tự động — người dùng nhập qua popup prompt khi TP/QL thao tác
- Mặc định: trống
- Bắt buộc: Không (TP/QL có thể để trống)
- Nguồn dữ liệu / liên kết: —
- Người sửa: TP/QL (quyền `survey_request:approve`) qua endpoint `POST /{id}/reject` hoặc `/{id}/cancel`
- Logic đặc biệt: Hiển thị banner cảnh báo bên dưới header khi phiếu ở trạng thái `rejected` hoặc `cancelled`. Ghi vào cả hai trường hợp (trả đơn và từ chối).

### 12. Trạng thái (`status`)

- Kiểu nhập: Hệ thống — thay đổi qua endpoint chuyên biệt
- Mặc định: `draft`
- Bắt buộc: Hệ thống điền
- Nguồn dữ liệu / liên kết: Giá trị cho phép: `draft`, `submitted`, `approved`, `rejected`, `cancelled`, `processing`, `survey_done`, `pr_created`, `done`
- Người sửa: Hệ thống (qua các endpoint submit/approve/reject/cancel/complete/create-prs/finalize)
- Logic đặc biệt: Xem bảng Vòng đời trạng thái. `approved` tồn tại rất ngắn — hàm `approve_` gọi `set_status("approved")` rồi ngay lập tức gọi `auto_assign` và `set_status("processing")` trong cùng một request.

---

## B. Trường của từng dòng yêu cầu (`SurveyRequestLine`)

Mỗi dòng = một sản phẩm / nhóm hàng cần khảo sát. Bảng tóm tắt hiển thị các cột chính; toàn bộ trường xem và sửa trong popup "Chi tiết dòng".

**Hiển thị dòng theo người xem (`visible_lines_for`)**: Thấy **hết** dòng nếu là người **tạo phiếu** (`created_by`) HOẶC có quyền **duyệt** (`survey_request:approve`, tức Admin/Quản lý TM) HOẶC có phạm vi đọc `dept`/`company`/`all`. NSTM (scope `proc`, không có quyền duyệt) chỉ thấy dòng được giao (`assignee == mã NV của mình`) hoặc dòng có phân loại mình phụ trách theo bảng `CategoryAssignee`. Quy tắc này áp dụng cho cả màn chi tiết, màn Xử lý, lẫn hàm Nhân bản (`clone`).

### 1. Ngày tiếp nhận (`received_date`)

- Kiểu nhập: Chỉ đọc (tự tính)
- Mặc định: trống; tự điền ngày hiện tại khi NSTM được gán vào dòng (`assignee` thay đổi từ trống sang có giá trị)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống — tự điền khi gán `assignee`; xóa khi bỏ gán
- Logic đặc biệt: Chỉ hiển thị với NSTM/Quản lý TM (`showNstmCols`); ẩn hoàn toàn với người YC. Trong popup chi tiết dòng, hiện nhãn "Ngày tiếp nhận (tự tính khi gán NSTM)" và bị `disabled`. Khi `auto_assign` gán, cũng điền `received_date` nếu còn trống.

### 2. Ngày yêu cầu trả kết quả (`result_due_date`)

- Kiểu nhập: Chọn ngày (sửa inline trong bảng hoặc trong popup)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Hiển thị cả trong bảng (cột "Ngày YC trả KQ") và trong popup chi tiết dòng.

### 3. Bộ phận / người yêu cầu dòng (`department_requester`)

- Kiểu nhập: Không có ô nhập trên form hiện tại (trường DB dự phòng)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: —
- Logic đặc biệt: Có trong model `tab_survey_request_line` nhưng chưa có ô nhập tương ứng trên frontend. Dùng cho tương lai khi một phiếu YCKS có nhiều dòng từ các bộ phận khác nhau.

### 4. Phân loại (`item_group`)

- Kiểu nhập: Chọn (SearchSelect, gõ để lọc — variant table trong bảng, variant mặc định trong popup)
- Mặc định: trống
- Bắt buộc: Một trong `item_group` hoặc `requirement_detail` phải có để Lưu/Gửi duyệt
- Nguồn dữ liệu / liên kết: Bảng Phân loại (`tab_item_group`), API `/api/item-groups`
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Là khóa cho `auto_assign` (tra `CategoryAssignee` để tìm NSTM phụ trách). Là khóa khớp trong `sync_options_from_surveys` — hệ thống tìm Phiếu khảo sát liên kết có cùng `item_group`. Popup chi tiết hiển thị mô tả phân loại (`std_days`, `std_days_unavail`, `note`) khi chọn.

### 5. Chi tiết thông số kỹ thuật & chất lượng (`requirement_detail`)

- Kiểu nhập: Nhập nhiều dòng (textarea trong popup; nhập tự do inline trong bảng)
- Mặc định: trống
- Bắt buộc: Một trong `requirement_detail` hoặc `item_group` phải có
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Dùng làm tiêu đề dòng trên màn Xử lý (cắt 60 ký tự nếu dài). Khi tạo PYC: dùng làm `PurchaseRequestItem.product_name` nếu option không có `snap_product_name`. Hiện trong phần tóm tắt phương án ("Sản phẩm N: ...") trên màn kết quả.

### 6. Yêu cầu khác (`other_requirement`)

- Kiểu nhập: Nhập nhiều dòng (textarea trong popup)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Hiển thị trong card dòng trên màn Xử lý, nhãn "YC khác:".

### 7. Số lượng dự kiến mua (`request_qty`)

- Kiểu nhập: Nhập số (NumberInput định dạng VN; sửa inline trong bảng)
- Mặc định: `0` (hiển thị trống khi bằng 0)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Lưu kiểu `Numeric(18, 3)`. Khi tạo PYC: dùng làm `PurchaseRequestItem.qty`; `amount = qty × snap_price_by_volume`.

### 8. Đơn vị tính (`uom`)

- Kiểu nhập: Chọn (SearchSelect, gõ để lọc)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Đơn vị tính (`tab_unit`), API `/api/units`
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Khi tạo PYC: dùng làm `PurchaseRequestItem.unit` nếu option không có `snap_quote_unit`.

### 9. Giá đề xuất (`proposed_price`)

- Kiểu nhập: Nhập số (VNĐ, NumberInput; sửa inline trong bảng)
- Mặc định: `0` (hiển thị trống khi bằng 0)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC khi phiếu `draft` / `rejected`
- Logic đặc biệt: Lưu kiểu `Numeric(18, 2)`. Hiển thị trên màn Kết quả khảo sát để người YC so sánh với giá thực từ phương án. Nằm trong `_LINE_PUBLIC_FIELDS` — người YC được xem.

### 10. Hình ảnh đính kèm (`image_file`)

- Kiểu nhập: URL văn bản — trường kế thừa (tương thích ngược)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: —
- Logic đặc biệt: Trường DB này không còn là đường dẫn upload chính. Đính kèm thực tế thực hiện qua module attachment (`POST /api/attachments`, entity `survey_request_line`), hỗ trợ nhiều file (jpg/png/webp/pdf). Popup chi tiết dòng có nút "Thêm hình / file"; file chờ (`pendingFiles`) được upload sau khi bấm Lưu phiếu lần đầu.

### 11. Nhân sự phụ trách dòng (`assignee`)

- Kiểu nhập: Chọn (SearchSelect theo mã NV) — chỉ hiển thị với người có quyền `process`
- Mặc định: trống; tự điền qua `auto_assign` ngay sau khi phiếu được duyệt
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhân viên (`tab_employee.code`)
- Người sửa: NSTM / Quản lý / Admin TM (quyền `survey_request:process`) qua endpoint `PATCH /{id}/lines/{line_id}/assignee`
- Logic đặc biệt: Gán mã NV → `received_date = hôm nay`; bỏ gán → xóa `received_date`. Ẩn hoàn toàn với người YC (`showNstmCols = canAssign && !isNew`). Dùng trong `can_process_line`: NSTM scope `proc` chỉ được xử lý dòng có `assignee == emp_code` của mình hoặc phân loại dòng thuộc `CategoryAssignee` (primary/backup) của mình. Khi gán, hệ thống gửi thông báo cho NSTM được phân công.

### 12. ID Yêu cầu mua hàng liên kết (`pr_id`)

- Kiểu nhập: Tự động
- Mặc định: `0`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Bảng `tab_purchase_request`
- Người sửa: Hệ thống — điền khi `create_prs` sinh PYC từ dòng này
- Logic đặc biệt: Nằm trong `_LINE_PUBLIC_FIELDS` — người YC được xem. Dùng trong `auto_complete_from_pr` để tra mọi PYC của YCKS. Khi `pr_id != 0`, dòng bị khóa: không thêm/xóa option được.

### 13. Mã Yêu cầu mua hàng liên kết (`pr_code`)

- Kiểu nhập: Tự động
- Mặc định: trống
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Bảng `tab_purchase_request`
- Người sửa: Hệ thống — điền cùng lúc với `pr_id` khi tạo PYC
- Logic đặc biệt: Hiển thị trong popup chi tiết dòng làm nhãn liên kết tra cứu. Nằm trong `_LINE_PUBLIC_FIELDS`.

### 14. Đã hoàn thành (`is_completed`)

- Kiểu nhập: Hệ thống + có thể đổi thủ công
- Mặc định: `false`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống tự đặt `true` khi tạo PYC; NSTM/QL có thể đổi thủ công qua `PATCH /{id}/lines/{line_id}/status` (quyền `write`)
- Logic đặc biệt: Khi `true`: dòng không được đưa vào `create_prs` lần nữa; không thêm/xóa option được; hiển thị badge "Hoàn thành" (xanh lá). Tình trạng dòng hiển thị trên badge bảng được tính từ: `is_completed` → "Hoàn thành"; `has_chosen` → "Đã chọn PA"; `option_count > 0` → "Đã khảo sát"; còn lại → "Chưa xong".

---

## C. Trường của Option (phương án) — `SurveyRequestOption`

Mỗi option = một kết quả khảo sát sản phẩm đã duyệt, gắn vào một dòng YCKS. Bảng Options hiển thị đầy đủ trên màn Xử lý (NSTM). Người YC chỉ thấy các trường snapshot công khai qua endpoint `/result` (backend whitelist `_OPT_PUBLIC_FIELDS`).

**Lọc option hợp lệ (`valid_options_of`)**: Tất cả view (màn chi tiết, màn Xử lý, màn kết quả) chỉ hiển thị option mà dòng khảo sát SP nguồn (`product_survey_line_id`) còn ở trạng thái `"Đã duyệt"`. Option của dòng đã bị "Không duyệt" hoặc phiếu khảo sát nguồn bị hủy (`cancelled`) sẽ bị **ẩn hoàn toàn** và **không cho chọn** — xử lý cả dữ liệu cũ còn kẹt trước khi có cascade xóa tự động. Option không gắn nguồn (`product_survey_line_id = 0`) vẫn được giữ.

### 1. ID ẩn danh trong dòng (`public_id`)

- Kiểu nhập: Tự động
- Mặc định: Số thứ tự trong dòng: `len(options_of(db, line.id)) + 1` tại thời điểm tạo
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống
- Logic đặc biệt: Số ẩn danh để người YC thấy "Option 1", "Option 2" mà không biết NCC. Nằm trong `_OPT_PUBLIC_FIELDS`. Không thay đổi khi xóa option khác.

### 2. Nhãn hiển thị (`display_label`)

- Kiểu nhập: Tự động
- Mặc định: `"Option {public_id} — ID {id}"` (VD: `"Option 1 — ID 42"`)
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống (cập nhật ngay sau `db.commit()` để có `id`)
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`. Phần "ID 42" giúp NSTM tham chiếu nhanh.

### 3. Đã chọn (`is_chosen`)

- Kiểu nhập: Tự động (người YC chọn qua endpoint `/choose`)
- Mặc định: `false`
- Bắt buộc: Cần chọn 1 option cho mỗi dòng trước khi "Tạo yêu cầu mua"
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC hoặc người sửa được phiếu, endpoint `PATCH /{id}/lines/{line_id}/options/{oid}/choose` (quyền `write`), chỉ khi phiếu `survey_done`
- Logic đặc biệt: Radio trong dòng — chọn option này tự hủy chọn (`is_chosen = false`) mọi option khác của cùng dòng. Ghi `chosen_by = user.id`. Frontend kiểm tra `allChosen` trước khi bật nút "Tạo yêu cầu mua". Nằm trong `_OPT_PUBLIC_FIELDS`.

### 4. Mã SP hệ thống (`system_product_code`)

- Kiểu nhập: Chọn sản phẩm (component `ProductPicker`, tìm theo mã hoặc tên)
- Mặc định: Tự điền từ `survey.item_code` (Mã VTBB/VL trên header Phiếu khảo sát nguồn) nếu có; trống nếu không
- Bắt buộc: Bắt buộc trước khi "Chốt hoàn thành" — frontend kiểm tra mọi option phải có mã (`missingOptions.length > 0` thì chặn)
- Nguồn dữ liệu / liên kết: Danh mục Sản phẩm (`tab_product.code`)
- Người sửa: NSTM phụ trách (`can_process_line`) hoặc Admin/QL TM — endpoint `PATCH /{id}/lines/{line_id}/options/{oid}` với body `{system_product_code}`
- Logic đặc biệt: Khi tạo PYC: dùng làm `PurchaseRequestItem.product_code`. Hiển thị trong cột "Mã SP hệ thống" bảng Options trên màn Xử lý; viền đỏ nếu thiếu sau khi bấm Chốt.

**Các trường snapshot (`snap_*`) — hiển thị cho người YC và NSTM:**

Được sao chép từ `SurveyProductLine` tại thời điểm tạo option; không thay đổi sau khi gắn (dù dữ liệu gốc thay đổi).

### 5. Tên SP — snapshot (`snap_product_name`)

- Kiểu nhập: Tự động (snapshot từ `SurveyProductLine.product_name`)
- Mặc định: Sao chép tại thời điểm tạo option
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.product_name`
- Người sửa: Hệ thống (không sửa sau khi gắn)
- Logic đặc biệt: Hiển thị là tiêu đề option trên card kết quả (người YC thấy). Khi tạo PYC: dùng làm `PurchaseRequestItem.product_name`.

### 6. Thông số kỹ thuật — snapshot (`snap_spec`)

- Kiểu nhập: Tự động
- Mặc định: Sao chép từ `SurveyProductLine.spec`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.spec`
- Người sửa: Hệ thống
- Logic đặc biệt: Hiển thị dưới nét đứt trong card option (người YC thấy). Nằm trong `_OPT_PUBLIC_FIELDS`.

### 7. Xuất xứ — snapshot (`snap_origin`)

- Kiểu nhập: Tự động
- Mặc định: Sao chép từ `SurveyProductLine.origin`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.origin`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`.

### 8. ĐVT báo giá — snapshot (`snap_quote_unit`)

- Kiểu nhập: Tự động
- Mặc định: Sao chép từ `SurveyProductLine.quote_unit`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.quote_unit`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`. Khi tạo PYC: dùng làm `PurchaseRequestItem.unit` (ưu tiên hơn `line.uom`).

### 9. MOQ tối thiểu — snapshot (`snap_moq`)

- Kiểu nhập: Tự động (`Numeric(18, 3)`)
- Mặc định: `0`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.moq`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`.

### 10. Giá theo sản lượng — snapshot (`snap_price_by_volume`)

- Kiểu nhập: Tự động (`Numeric(18, 2)`, VNĐ)
- Mặc định: `0`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.price_by_volume`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`; hiển thị nhãn "Đơn giá" trên card kết quả (người YC). Khi tạo PYC: `PurchaseRequestItem.price = snap_price_by_volume`; `amount = qty × price`.

### 11. Khoảng sản lượng áp giá — snapshot (`snap_volume_range`)

- Kiểu nhập: Tự động
- Mặc định: trống
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.volume_range`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`.

### 12. VAT % — snapshot (`snap_vat`)

- Kiểu nhập: Tự động (`Numeric(5, 2)`)
- Mặc định: `0`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.vat`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`.

### 13. Thời gian giao hàng — snapshot (`snap_delivery_time`)

- Kiểu nhập: Tự động
- Mặc định: trống
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.delivery_time`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`.

### 14. Địa điểm giao/nhận — snapshot (`snap_delivery_place`)

- Kiểu nhập: Tự động
- Mặc định: trống
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.delivery_place`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`.

### 15. Phí vận chuyển — snapshot (`snap_shipping_cost`)

- Kiểu nhập: Tự động (`Numeric(18, 2)`, VNĐ)
- Mặc định: `0`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.shipping_cost`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`. Hiển thị "Miễn phí" trên card kết quả nếu bằng 0.

### 16. Có mẫu sẵn — snapshot (`snap_sample_ready`)

- Kiểu nhập: Tự động (Boolean)
- Mặc định: `false`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.sample_ready`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`. Hiển thị "Có" / "Không" trên card kết quả.

### 17. Kết quả LAB — snapshot (`snap_lab_result`)

- Kiểu nhập: Tự động (String 20)
- Mặc định: trống
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.lab_result`
- Người sửa: Hệ thống
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`.

**Các trường nội bộ NSTM — backend lọc, không trả cho người YC:**

Các trường dưới đây KHÔNG có trong `_OPT_PUBLIC_FIELDS`. Backend endpoint `/result` lọc hoàn toàn; người YC không lấy được dù gọi API trực tiếp.

### 18. Mã SP theo NCC — nội bộ (`snap_internal_code`)

- Kiểu nhập: Tự động (snapshot từ `SurveyProductLine.internal_code`)
- Mặc định: trống
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.internal_code` (mã sản phẩm NCC đặt)
- Người sửa: Hệ thống
- Logic đặc biệt: Chỉ NSTM thấy trong bảng Options màn Xử lý; ẩn với người YC.

### 19. Mã NCC — nội bộ (`supplier_code`)

- Kiểu nhập: Tự động (snapshot từ `SurveyProductLine.supplier_code`)
- Mặc định: trống
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_supplier.code`
- Người sửa: Hệ thống
- Logic đặc biệt: Dùng trong `create_prs` để gom option theo NCC — mỗi giá trị `supplier_code` duy nhất tạo 1 PYC riêng. Hiển thị badge cam "NCC (nội bộ)" trong bảng Options màn Xử lý.

### 20. Tên NCC — nội bộ (`supplier_name`)

- Kiểu nhập: Tự động (tra `Supplier.name` qua `resolve_supplier_name`)
- Mặc định: trống (dùng `supplier_code` làm fallback nếu không tìm thấy)
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `tab_supplier.name`
- Người sửa: Hệ thống
- Logic đặc biệt: Khi tạo PYC: dùng làm `PurchaseRequest.suggested_supplier`. Hiển thị trong badge cam "NCC (nội bộ)" cùng với `supplier_code`.

### 21. Ghi chú NSTM (`nstm_note`)

- Kiểu nhập: Tự động từ `SurveyProductLine.nspt_reason`; NSTM có thể cập nhật sau
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: `tab_survey_product_line.nspt_reason` (lý do/nhận xét NSPT từ phiếu khảo sát gốc)
- Người sửa: NSTM phụ trách (`can_process_line`) — endpoint `PATCH /{id}/lines/{line_id}/options/{oid}` với body `{nstm_note}`
- Logic đặc biệt: Không có trong `_OPT_PUBLIC_FIELDS`; ẩn hoàn toàn với người YC. Dùng để NSTM ghi chú nội bộ về chất lượng, lý do chọn/không chọn option này.

---

## D. Quy tắc nghiệp vụ

1. Mã phiếu tự sinh ngay sau khi tạo theo `YCKS{DDMMYY}{seq:02d}`. Số thứ tự đếm theo prefix ngày trong cùng ngày, đặt lại từ 01 mỗi ngày (không đặt lại theo tháng/năm).

2. Validate khi Lưu/Gửi duyệt (phía FE): phải có Công ty (`company_id`), Người yêu cầu (`requester`), Mục đích (`purpose`), và ít nhất 1 dòng có `item_group` hoặc `requirement_detail`.

3. Sửa nội dung phiếu chỉ cho phép khi `status = draft` hoặc `rejected`. Backend trả HTTP 400 "Chỉ sửa được khi phiếu ở trạng thái Nháp hoặc Bị trả lại" nếu cố sửa ở trạng thái khác. Phiếu `cancelled` ("Đã từ chối") bị khóa vĩnh viễn — hệ thống gợi ý Nhân bản (`clone`) thành phiếu nháp mới.

4. Sau khi Duyệt: hàm `auto_assign` tự gán NSTM cho từng dòng theo bảng `CategoryAssignee` (khớp `item_group`), cập nhật `received_date`, và đặt `SurveyRequest.assignee_id`. Phiếu chuyển `processing` trong cùng một request. Gửi thông báo đến NSTM được gán và Admin/QL TM.

5. Cơ chế ẩn NCC: endpoint `GET /{id}/result` (dành cho người YC) chỉ trả các field trong `_OPT_PUBLIC_FIELDS` và `_LINE_PUBLIC_FIELDS`. Các field `supplier_code`, `supplier_name`, `snap_internal_code`, `nstm_note`, `supplier_survey_id`, `product_survey_line_id` bị loại ở tầng Python trước khi trả response — không thể lấy được kể cả gọi API trực tiếp với token người YC.

6. Vào màn Xử lý (`GET /{id}/process`): chỉ người có `survey_request:read` với scope `proc` hoặc `all` (`is_purchaser`) mới được vào. Backend kiểm tra và trả HTTP 403 cho người YC (scope `own`/`dept`).

7. NSTM scope `proc` chỉ gắn/xóa/sửa option cho dòng mình phụ trách (`can_process_line`): hoặc `assignee == emp_code`, hoặc phân loại dòng thuộc `CategoryAssignee.primary_employee_id` / `backup_employee_id` của NSTM đó. Admin/QL TM (scope `all`) xử lý được mọi dòng.

8. Gắn option thủ công: NSTM chọn NCC → gọi `GET /{id}/lines/{line_id}/available-survey-lines?supplier_code=...` lấy dòng khảo sát SP đã duyệt (`line_approve = "Đã duyệt"`, `Survey.status` bất kỳ trừ `cancelled`) khớp phân loại → chọn 1 hoặc nhiều dòng → `POST /{id}/lines/{line_id}/options`. Không thể gắn cùng 1 `product_survey_line_id` hai lần cho cùng 1 dòng YCKS.

9. Nút "Tạo phiếu khảo sát" (chỉ hiển thị khi `status = processing`, với người có quyền `process`): điều hướng sang `/surveys/new?sr={id}&sr_code={code}`, truyền sẵn liên kết YCKS để Phiếu khảo sát mới tự gắn `survey_request_id`. Khi Phiếu khảo sát được duyệt, hệ thống có thể dùng nút "Lấy từ khảo sát" để tự gắn option.

10. Nút "Lấy từ khảo sát" (`POST /{id}/sync-options`): hàm `sync_options_from_surveys` tìm mọi Phiếu khảo sát (`status` bất kỳ trừ `cancelled`) đã liên kết YCKS qua `survey.survey_request_id = sid`, lấy dòng SP `line_approve = "Đã duyệt"`, khớp `item_group` với dòng YCKS để gắn option. Nếu YCKS chỉ có 1 dòng nhưng phân loại không khớp thì cũng tự gắn vào dòng đó. Bỏ qua dòng đã có option nguồn đó. Trả về số option mới thêm. Chỉ hoạt động khi `status = processing` hoặc `survey_done`. (Lưu ý: frontend chỉ hiện nút "Lấy từ khảo sát" khi `processing`, nhưng backend cho phép cả `survey_done`.)

11. Chốt hoàn thành khảo sát (`POST /{id}/complete`, chấp nhận `processing` hoặc `survey_done`): Backend chỉ validate rằng các dòng người gọi phụ trách (`my_lines`) đều có ít nhất 1 option — Quản lý/Admin TM (scope `all`) và người tạo phiếu (`created_by`) validate toàn bộ dòng. Phiếu chuyển `survey_done` chỉ khi TẤT CẢ dòng (mọi NSTM) đã có option; nếu còn dòng của NSTM khác chưa xong thì phiếu giữ nguyên `processing` (backend trả thông báo "còn dòng chưa xong"). Frontend kiểm tra thêm trước khi gọi API: mọi dòng hiển thị phải có option VÀ mọi option phải có `system_product_code`. Khi phiếu chuyển sang `survey_done`, gửi thông báo cho người YC.

12. Tạo PYC (`POST /{id}/create-prs`, `survey_done → pr_created`): gom option đã chọn (`is_chosen = true`) theo `supplier_code` → mỗi NCC 1 PYC Nháp. Dữ liệu PYC lấy từ snapshot option. Đặt `is_completed = true` và điền `pr_id`/`pr_code` cho dòng. Chỉ người YC (`created_by`) hoặc Admin TM (quyền `delete`) được gọi.

13. Tự hoàn thành (`auto_complete_from_pr`): khi 1 PYC liên quan chuyển sang `completed`, hàm tra tất cả PYC (`pr_id`) sinh từ YCKS đó. Nếu tất cả đều `completed` và YCKS đang `pr_created` → tự chuyển YCKS sang `done` và ghi audit log "Tự hoàn thành".

14. Xóa phiếu: chỉ khi `draft` hoặc `rejected` (backend kiểm tra). Xóa cascade: xóa toàn bộ `SurveyRequestOption` của các dòng trước, rồi xóa `SurveyRequestLine`, cuối cùng xóa phiếu header.

15. Hiển thị dòng theo người xem (`visible_lines_for`): Thấy **hết** dòng nếu là người **tạo phiếu** (`created_by`) HOẶC có quyền **duyệt** (`survey_request:approve`, tức Admin/Quản lý TM) HOẶC có phạm vi đọc `dept`/`company`/`all`. NSTM (scope `proc`, không có quyền duyệt) chỉ thấy dòng được giao (`assignee == mã NV`) hoặc dòng có phân loại mình phụ trách theo bảng `CategoryAssignee` (primary/backup). Quy tắc áp dụng cho cả endpoint `GET /{id}` (màn chi tiết), `GET /{id}/process` (màn xử lý), hàm `complete_sr` (validate chỉ "dòng mình") và hàm `clone_sr` (chỉ sao chép "dòng mình"). (Logic đồng bộ với `purchase_request._see_all_items`.)

16. Lọc option hợp lệ (`valid_options_of`): Các view xử lý khảo sát (`_out_process`), kết quả (`_out_result`), và màn chi tiết (`_out`) đều dùng `valid_options_of` thay cho `options_of` thô. Hàm này **chỉ trả option** có dòng khảo sát SP nguồn (`product_survey_line_id`) còn trạng thái `"Đã duyệt"`. Option của dòng đã bị "Không duyệt" hoặc phiếu khảo sát nguồn bị `cancelled` sẽ **bị ẩn, không được tính** vào `option_count`/`has_chosen`, và không cho chọn — xử lý cả dữ liệu cũ còn kẹt. Option không gắn nguồn (`product_survey_line_id = 0`) vẫn được giữ.

16. Nhân bản phiếu (`POST /{id}/clone`, quyền `survey_request:create`): Tạo phiếu Nháp mới — sao chép toàn bộ trường header (`company_id`, `requester`, `requester_position`, `department`, `head_of_dept`, `purpose`, `request_date`, `note`) và các dòng mà người dùng được xem (`visible_lines_for`). Sinh mã phiếu mới theo quy tắc `_gen_code`. Các thông tin sau KHÔNG được sao chép: `assignee` (NSTM phụ trách dòng; reset về rỗng), `received_date` (reset về rỗng), option, `pr_id`/`pr_code`, `is_completed`. Đính kèm file dòng được tái sử dụng (thêm `FileLink` mới trỏ cùng file gốc — không sao chép file vật lý). Có thể nhân bản từ bất kỳ trạng thái nào, kể cả phiếu `cancelled`.

---

## E. Quyền thao tác (RBAC)

Entity: `survey_request`. Actions: `read`, `create`, `write`, `approve`, `cancel`, `delete`, `process`.

| Thao tác | Quyền yêu cầu | Điều kiện trạng thái | Ghi chú scope |
|----------|---------------|----------------------|---------------|
| Xem danh sách / chi tiết | `survey_request:read` | mọi trạng thái | `own` → chỉ phiếu mình tạo; `dept` → phòng ban; `proc` → NSTM phụ trách (theo dòng `assignee` hoặc phân loại); `all` → toàn bộ |
| Tạo phiếu mới | `survey_request:create` | — | — |
| Sửa nội dung phiếu | `survey_request:read` + (`created_by == user.id` hoặc `survey_request:write`) | `draft`, `rejected` | Backend kiểm tra `_can_edit_own` |
| Gửi duyệt | như Sửa | `draft`, `rejected` | — |
| Duyệt phiếu | `survey_request:approve` | `submitted` | Tự chuyển sang `processing` sau khi duyệt; tự gán NSTM |
| Trả đơn (`reject`) | `survey_request:approve` | `submitted` | Phiếu về `rejected`, người YC sửa và gửi lại được |
| Từ chối (`cancel`) | `survey_request:approve` | `submitted` | Phiếu về `cancelled`, khóa vĩnh viễn |
| Vào màn Xử lý khảo sát | `survey_request:read` + `is_purchaser` (scope `proc`/`all`) | `processing`, `survey_done` | Người YC (scope `own`/`dept`) bị chặn tại backend (HTTP 403) |
| Gán NSTM cho dòng | `survey_request:process` | mọi trạng thái | NSTM / QL / Admin TM |
| Gắn option cho dòng | `survey_request:process` + `can_process_line` | `processing`, `survey_done` | NSTM scope `proc`: chỉ dòng mình phụ trách; Admin/QL scope `all`: mọi dòng |
| Xóa option | `survey_request:process` + `can_process_line` + dòng chưa `is_completed` | `processing`, `survey_done` | — |
| Đặt Mã SP hệ thống cho option | `survey_request:process` + `can_process_line` | mọi trạng thái | — |
| Cập nhật ghi chú NSTM cho option | `survey_request:process` + `can_process_line` | mọi trạng thái | — |
| Lấy từ khảo sát (`sync-options`) | `survey_request:process` + `is_purchaser` | `processing`, `survey_done` | `POST /{id}/sync-options` |
| Chốt hoàn thành khảo sát | `survey_request:process` + `is_purchaser` | `processing`, `survey_done` | Backend validate dòng người gọi phụ trách; phiếu chuyển `survey_done` khi mọi dòng đủ option |
| Chọn phương án (người YC) | `survey_request:write` + `created_by == user.id` hoặc `write` | `survey_done` | Endpoint `PATCH /{id}/lines/{line_id}/options/{oid}/choose` |
| Tạo YCMH từ phương án | `created_by == user.id` hoặc `survey_request:delete` | `survey_done` | Gom theo NCC; chỉ người YC hoặc Admin TM |
| Chuyển Hoàn thành (finalize) | `survey_request:approve` + `is_purchaser` (scope `all`) | `pr_created` | Admin / QL TM |
| Đổi trạng thái dòng thủ công | `survey_request:write` | mọi trạng thái | `PATCH /{id}/lines/{line_id}/status` |
| Xóa phiếu | `survey_request:delete` | `draft`, `rejected` | Xóa cascade dòng và option |
