# Yêu cầu báo giá (YCBG)

Ghi chú: tên cũ trong tài liệu và một số comment code là "Yêu cầu khảo sát (YCKS)". Tên hiển thị trên menu hiện tại là **"Yêu cầu báo giá"**; mã phiếu đổi prefix thành `YCBG`; entity/bảng DB vẫn giữ tên `survey_request` / `tab_survey_request`.

## Mục đích

Ghi nhận nhu cầu khảo sát giá / nhà cung cấp do bộ phận nghiệp vụ lập, chuyển cho nhân sự thu mua (NSTM) thực hiện. Sau khi NSTM gắn đủ phương án (option) — ẩn danh NCC với người yêu cầu — người yêu cầu chọn phương án và hệ thống tự sinh Yêu cầu mua hàng (YCMH/PYC), gom theo nhà cung cấp.

Đường dẫn: `/survey-requests` (danh sách), `/survey-requests/:id` (chi tiết + kết quả khảo sát), `/survey-requests/:id/process` (màn xử lý dành riêng NSTM).

Màn chi tiết hiển thị phần **Lịch sử thao tác** (audit log) ở cột bên phải khi phiếu đã có thao tác được ghi nhận — gọi `GET /api/audit-logs?entity=survey_request&entity_id={id}`. Khối này dùng chung `components/AuditTimeline.tsx`: hiện **10 thao tác gần nhất**, còn nữa thì có nút **"Xem thêm N thao tác"** và **"Thu gọn"**.

## Vai trò tham gia

- Người yêu cầu — scope `own` (`survey_request:create` / `write`): lập phiếu, gửi duyệt, chọn phương án, tạo YCMH, đổi trạng thái dòng.
- Cùng phòng ban người yêu cầu: đổi trạng thái dòng (`line-status`), chuyển Hoàn thành (finalize).
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
| Đã tạo YCMH | `pr_created` | PYC đã sinh, chờ Admin/QL chốt | Tạo yêu cầu mua (tái sử dụng), Chuyển Hoàn thành |
| Hoàn thành | `done` | Khép kín — không chỉnh sửa | Tạo yêu cầu mua (tái sử dụng vẫn cho phép) |

Các chuyển tiếp trạng thái:

- `draft` → `submitted` — endpoint `POST /{id}/submit`; người YC hoặc người có quyền sửa phiếu.
- `submitted` → `approved` → `processing` — endpoint `POST /{id}/approve`; tức thời, hai bước trong một lần gọi; quyền `approve`. Sau đó `auto_assign` gán NSTM theo phân loại.
- `submitted` → `rejected` — endpoint `POST /{id}/reject`; quyền `approve`; phiếu quay về trạng thái có thể sửa.
- `submitted` → `cancelled` — endpoint `POST /{id}/cancel`; quyền `approve`; khóa vĩnh viễn.
- `rejected` → `submitted` — người YC sửa rồi gửi duyệt lại.
- `processing` → `survey_done` — endpoint `POST /{id}/complete`; quyền `process` + `is_purchaser`; mỗi NSTM validate dòng mình phụ trách (hoặc dòng "chốt rỗng" `no_option`); phiếu chuyển khi TẤT CẢ dòng (mọi NSTM) đã có option hoặc được chốt rỗng. Có thể gọi lại từ `survey_done`.
- `survey_done` → `pr_created` — endpoint `POST /{id}/create-prs`; chỉ nâng cấp status từ `survey_done`; nếu phiếu đang `pr_created` hoặc `done` thì tạo YCMH nhưng không hạ status. Xem mục E.12.
- `survey_done` hoặc `pr_created` → `done` (thủ công) — endpoint `POST /{id}/finalize`; Admin/QL TM (scope `all` + quyền `approve`) HOẶC người yêu cầu / cùng phòng ban người yêu cầu.
- `pr_created` → `done` (tự động) — hàm `auto_complete_from_pr` kích hoạt khi PYC liên quan chuyển `completed`; nếu mọi PYC của YCBG đều `completed` thì YCBG tự sang `done`.

## Bộ lọc danh sách

Màn danh sách `/survey-requests` hỗ trợ các bộ lọc:

| Nhãn lọc | Param API | Loại | Ghi chú |
|-----------|-----------|------|---------|
| Mã phiếu | `code` | LIKE | |
| Sản phẩm cần báo giá | `product` | LIKE | **CR-069** — dòng YCBG **không có ô mã/tên hàng**, nên ô này dò: `SurveyRequestLine.requirement_detail` (Thông số kỹ thuật) · `other_requirement` (Yêu cầu khác) · **và** mã/tên SP của **phương án ĐÃ CHỐT** (`SurveyRequestOption.system_product_code` / `snap_product_name`, chỉ `is_chosen = true`). Khớp một phần, không phân biệt hoa/thường và dấu. **KHÔNG dò** `snap_internal_code` và các cột `supplier_*` — nếu dò thì người không có `supplier.read` sẽ suy ra được NCC bằng cách gõ thử mã NCC |
| Công ty | `company_id` | Bằng (ID) | |
| Người yêu cầu | `requester` | LIKE | |
| Bộ phận | `department` | LIKE | |
| NSTM phụ trách | `assignee` | Bằng (mã NV) | Lọc theo `SurveyRequestLine.assignee` (subquery) |
| Phân loại | `item_group` | LIKE | Lọc theo `SurveyRequestLine.item_group` (subquery) |
| Ngày tạo | `request_date_from` / `request_date_to` | Khoảng ngày | |
| Trạng thái | `status` | Bằng | `draft`, `submitted`, `approved`, `rejected`, `cancelled`, `processing`, `survey_done`, `pr_created`, `done` |

---

## A. Trường header phiếu YCBG

### 1. Mã phiếu (`code`)

- Kiểu nhập: Tự động — không nhập tay
- Mặc định: Sinh ngay sau khi tạo theo quy tắc `YCBG{DDMMYY}{seq:02d}` (VD: `YCBG10072601`). Số thứ tự lấy MAX hậu tố hiện có + 1 (không dùng COUNT để tránh trùng khi có khoảng trống do xóa). Nguồn: `service._gen_code()`.
- Bắt buộc: Hệ thống điền, không sửa được
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống (trường khóa)
- Logic đặc biệt: Chỉ hiển thị trên màn xem (không hiện khi tạo mới). Prefix cũ (`YCKS`) không còn được dùng — phiếu cũ đã tồn tại giữ nguyên mã cũ, phiếu mới sinh từ `YCBG`.

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
- Mặc định: Tự điền từ `employee.position` (Vị trí / Chức vụ trong hồ sơ nhân sự)
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
- Logic đặc biệt: Khi chọn YCBG trên màn tạo Phiếu khảo sát, trường **Nội dung chính** (`main_content`) của phiếu khảo sát tự điền từ đây. Khi tạo PYC sao chép sang `PurchaseRequest.purpose`.

### 8. Ngày tạo (`request_date` / `created_at`)

- Kiểu nhập: Chọn ngày — chỉ khi TẠO MỚI (nhập `request_date`). Khi XEM phiếu đã tạo, ô hiển thị `created_at` (ngày + giờ đầy đủ từ hệ thống, chỉ đọc); nếu không có `created_at` thì fallback về `request_date`.
- Mặc định: Ngày hiện tại (ISO format `YYYY-MM-DD`)
- Bắt buộc: Hiển thị dấu `*`; không validate phía FE
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC khi phiếu `draft` / `rejected` (chỉ ảnh hưởng đến `request_date`; `created_at` do hệ thống ghi lúc tạo và không thay đổi)
- Logic đặc biệt: `request_date` dùng làm ngày tham chiếu khi sinh mã PYC (`_gen_pr_code`). `created_at` là timestamp tạo phiếu thực tế và được ưu tiên hiển thị trên giao diện.

### 9. NSTM chính (`assignee_id`) — ĐÃ BỎ (CR-018)

Trường này **không còn tồn tại** trong hệ thống. Trước đây `auto_assign` ghi vào đây NSTM của **dòng
đầu tiên** có phân loại được cấu hình, và `apply_scope` dùng nó làm một điều kiện xem phiếu.

Lý do bỏ: một phiếu có thể do **nhiều NSTM** khảo sát, việc thuộc về **dòng** chứ không thuộc về
phiếu. Trường header chỉ được ghi **một lần** lúc duyệt và không đồng bộ khi đổi NSTM ở dòng → NSTM
cũ vẫn thấy phiếu mình không còn phần việc nào. Ô này cũng đã bị gỡ khỏi giao diện từ trước.

Người phụ trách khảo sát nay chỉ có **một nguồn duy nhất**: `SurveyRequestLine.assignee` (mã NV) —
xem mục Dòng sản phẩm. Cột `assignee_id` đã được **drop khỏi DB** bằng migration `a3f5c81d7e64`.

> Không nhầm với `PurchaseRequest.assignee_id` (YCMH) — trường đó **vẫn dùng**, người duyệt gán qua
> `PATCH /{pid}/assign`.

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

**Hiển thị dòng theo người xem (`visible_lines_for`)**: Thấy **hết** dòng nếu là người **tạo phiếu** (`created_by`) HOẶC là **người yêu cầu** (`requester_id == user.employee_id`, kể cả khi admin tạo giùm) HOẶC có quyền **duyệt** (`survey_request:approve`, tức Admin/Quản lý TM) HOẶC có phạm vi đọc `dept`/`company`/`all` HOẶC là Admin thu mua đọc-chỉ (scope `proc` nhưng KHÔNG có `write`). NSTM (scope `proc` + có `write`) chỉ thấy dòng được giao (`assignee == mã NV của mình`) hoặc dòng có phân loại mình phụ trách theo bảng `CategoryAssignee`. Quy tắc này áp dụng cho cả màn chi tiết, màn Xử lý, lẫn hàm Nhân bản (`clone`).

**Các trường trong `_LINE_PUBLIC_FIELDS`** (endpoint `/result` trả cho người YC): `id`, `item_group`, `requirement_detail`, `other_requirement`, `request_qty`, `uom`, `proposed_price`, `is_completed`, `line_status`, `pr_id`, `pr_code`, `no_option`.

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
- Logic đặc biệt: Có trong model `tab_survey_request_line` nhưng chưa có ô nhập tương ứng trên frontend. Dùng cho tương lai khi một phiếu YCBG có nhiều dòng từ các bộ phận khác nhau.

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
- Người sửa: Hệ thống — cập nhật sang YCMH gần nhất mỗi khi `create_prs` sinh PYC từ dòng này (1 dòng có thể tạo nhiều YCMH — xem mục E.12)
- Logic đặc biệt: Nằm trong `_LINE_PUBLIC_FIELDS` — người YC được xem. Dùng trong `auto_complete_from_pr` để tham chiếu YCMH gần nhất. Lịch sử đầy đủ (mọi lần tạo) lưu trong bảng `tab_survey_request_pr`.

### 13. Mã Yêu cầu mua hàng liên kết (`pr_code`)

- Kiểu nhập: Tự động
- Mặc định: trống
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Bảng `tab_purchase_request`
- Người sửa: Hệ thống — cập nhật cùng lúc với `pr_id` mỗi khi tạo PYC
- Logic đặc biệt: Hiển thị trong popup chi tiết dòng làm nhãn liên kết tra cứu. Nằm trong `_LINE_PUBLIC_FIELDS`.

### 14. Đã hoàn thành (`is_completed`)

- Kiểu nhập: Hệ thống + có thể đổi thủ công
- Mặc định: `false`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống tự đặt `true` khi tạo PYC lần đầu; NSTM/QL có thể đổi thủ công qua `PATCH /{id}/lines/{line_id}/status` (quyền `write`)
- Logic đặc biệt: Khi `true`: hiển thị badge "Hoàn thành" (xanh lá); không thêm/xóa option được (`add_option_` kiểm tra và trả HTTP 400). Lưu ý: cờ `is_completed = True` chỉ đánh dấu "đã từng tạo YCMH" — KHÔNG còn ngăn tạo thêm YCMH lần sau (tái sử dụng dòng). Đồng bộ với `line_status`: `line_status = "completed"` kéo `is_completed = true` và ngược lại.

### 15. Mã yêu cầu dòng (`internal_line_code`)

- Kiểu nhập: Tự động
- Mặc định: Sinh sau khi tạo dòng: `YCBGL{id:06d}` (VD: `YCBGL000042`)
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống (không sửa sau khi tạo)
- Logic đặc biệt: KHÔNG hiển thị với người YC — chỉ dùng nội bộ trong thông báo lỗi `complete_sr` ("Còn N dòng chưa có phương án") và tra cứu NSTM. Không nằm trong `_LINE_PUBLIC_FIELDS`.

### 16. Trạng thái dòng (`line_status`)

- Kiểu nhập: Hệ thống — thay đổi qua endpoint `PATCH /{id}/lines/{line_id}/line-status`
- Mặc định: `""` (chưa xác định)
- Giá trị cho phép: `""` / `"resurvey"` / `"completed"`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC hoặc cùng phòng ban người YC (`_can_act_as_requester_side`) hoặc Admin TM (quyền `delete`). Chặn khi phiếu ở trạng thái `cancelled` / `done`.
- Logic đặc biệt: Nằm trong `_LINE_PUBLIC_FIELDS` — người YC được xem. Đồng bộ hai chiều với `is_completed`: `"completed"` đặt `is_completed = true`; `""` / `"resurvey"` đặt `is_completed = false`. Khi đặt `"resurvey"`: tự hủy chọn (`is_chosen = false`) mọi option của dòng; nếu phiếu đang `survey_done` thì hạ về `processing`. Khi chọn một phương án (PA): tự gỡ cờ `resurvey` về `""`. Chốt `"completed"` yêu cầu dòng phải có option đang được chọn (`is_chosen = true`). **CR-077:** badge trên màn chi tiết KHÔNG còn do FE tự tính — backend nhét sẵn `progress_state` + `progress_tone` vào payload (`_out` và `/result`), dùng chung đúng bộ 9 nhãn của màn Tiến độ báo giá (xem §H và `survey_request/line_state.py`). Trước CR-077 FE tự suy 5 nhãn riêng, lại coi `is_completed` là "Hoàn thành" trong khi cờ đó chỉ nghĩa "đã TỪNG tạo YCMH" — nên dòng vừa tạo YCMH bị gắn nhãn Hoàn thành sai.

### 17. Không có phương án phù hợp (`no_option`)

- Kiểu nhập: Hệ thống — đặt khi NSTM "chốt rỗng" qua endpoint `POST /{id}/complete` với body `{empty_line_ids: [...]}`
- Mặc định: `false`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống — đặt `true` khi NSTM gửi `empty_line_ids` chứa `line_id` này; đặt về `false` khi sau đó có option được gắn vào dòng
- Logic đặc biệt: Nằm trong `_LINE_PUBLIC_FIELDS` — người YC được xem. FE hiển thị banner "Không có phương án phù hợp (đã chốt rỗng) — sản phẩm này không mua được từ phiếu khảo sát" thay cho danh sách option. Dòng được chốt rỗng được tính là "xong" trong `complete_sr` — phiếu vẫn chuyển `survey_done` khi mọi dòng hoặc có option hoặc `no_option = true`.

### 18. Ngày trả kết quả thực tế (`result_date`) — CR-075

- Kiểu nhập: Hệ thống — không có ô nhập, không sửa tay được
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: đi cặp với `result_due_date` (mục 2) để đo trễ hạn
- Người sửa: Hệ thống — đóng mốc trong `complete_sr` (`_stamp_result_date`) khi NSTM bấm **"Chốt khảo sát"**, cho cả hai nhánh: dòng có phương án và dòng **chốt rỗng** (chốt rỗng cũng là đã trả kết quả — "khảo sát rồi, không có NCC phù hợp")
- Logic đặc biệt: **Ghi MỘT LẦN duy nhất.** Dòng bị trả về `resurvey` rồi chốt lần hai **không** ghi đè mốc cũ — nếu ghi đè thì mọi dấu trễ hạn của lần đầu bị xóa sạch chỉ bằng một lần khảo sát lại. Ngày lấy theo **giờ Việt Nam** (`VN_OFFSET`) vì container chạy UTC. Dữ liệu cũ đã backfill bằng `backend/scripts/backfill_result_date_cr075.py` (dòng có phương án → ngày tạo phương án sớm nhất; dòng chốt rỗng → `updated_at`; còn lại để trống) — đây là mốc **suy đoán**, phiếu nhập từ Excel lịch sử mang ngày nhập liệu.

---

## C. Trường của Option (phương án) — `SurveyRequestOption`

Mỗi option = một kết quả khảo sát sản phẩm đã duyệt, gắn vào một dòng YCBG. Bảng Options hiển thị đầy đủ trên màn Xử lý (NSTM). Người YC chỉ thấy các trường snapshot công khai qua endpoint `/result` (backend whitelist `_OPT_PUBLIC_FIELDS`).

**Lọc option hợp lệ (`valid_options_of`)**: Tất cả view (màn chi tiết, màn Xử lý, màn kết quả) chỉ hiển thị option hợp lệ theo quy tắc sau:
- Nếu dòng khảo sát SP nguồn (`product_survey_line_id`) **còn tồn tại** trong DB: chỉ giữ option có `line_approve == "Đã duyệt"`. Option có nguồn còn tồn tại nhưng bị "Không duyệt" sẽ bị ẩn và không cho chọn.
- Nếu dòng khảo sát SP nguồn **đã bị xóa** (phiếu khảo sát bị xóa): giữ nguyên snapshot, vì snapshot đã tự đủ thông tin và có thể đã được chọn / tạo YCMH trước đó.
- Option không gắn nguồn (`product_survey_line_id = 0`): giữ nguyên.

Ghi chú: so với phiên bản cũ, hàm không còn kiểm tra `Survey.status == "cancelled"` — chỉ quan tâm đến trạng thái của từng dòng SP nguồn (`line_approve`).

### 1. ID ẩn danh trong dòng (`public_id`)

- Kiểu nhập: Tự động
- Mặc định: Số thứ tự trong dòng: `len(options_of(db, line.id)) + 1` tại thời điểm tạo
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống
- Logic đặc biệt: Số ẩn danh để người YC thấy "Option 1", "Option 2" mà không biết NCC. Nằm trong `_OPT_PUBLIC_FIELDS`. Không thay đổi khi xóa option khác.

### 2. Nhãn hiển thị (`display_label`)

- Kiểu nhập: Tự động
- Mặc định: `"Option {public_id}"` khi tạo, ngay sau khi `db.commit()` cập nhật thành `"Option {public_id} — ID {id}"` (VD: `"Option 1 — ID 42"`)
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống (cập nhật ngay sau `db.commit()` để có `id`)
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`. Phần "ID 42" giúp NSTM tham chiếu nhanh. Trên endpoint `/result`, nhãn được FE đổi thành `"Option {public_id} — NCC #{ncc_ref}"` (số NCC ẩn danh theo thứ tự xuất hiện toàn phiếu).

### 3. Đã chọn (`is_chosen`)

- Kiểu nhập: Tự động (người YC chọn qua endpoint `/choose`)
- Mặc định: `false`
- Bắt buộc: Cần chọn 1 option cho mỗi dòng trước khi "Tạo yêu cầu mua"
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người YC hoặc người sửa được phiếu, endpoint `PATCH /{id}/lines/{line_id}/options/{oid}/choose` (quyền `write`), khi phiếu ở trạng thái `processing`, `survey_done`, `pr_created`, hoặc `done`
- Logic đặc biệt: Radio trong dòng — chọn option này tự hủy chọn (`is_chosen = false`) mọi option khác của cùng dòng; bấm lại option đang chọn → bỏ chọn (toggle). Ghi `chosen_by = user.id`. Frontend kiểm tra `allChosen` trước khi bật nút "Tạo yêu cầu mua". Nằm trong `_OPT_PUBLIC_FIELDS`. Sau khi `create_prs` tạo YCMH, option tự bỏ chọn (`is_chosen = false`).

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
- Logic đặc biệt: Nằm trong `_OPT_PUBLIC_FIELDS`. Đơn vị là **phần trăm** (8 = 8%), khác `vat_rate` ở phần đầu chứng từ và `supplier.vat` — hai chỗ đó lưu tỉ lệ (0.08). Khi bấm **Tạo YCMH** (mục E.12), giá trị này được chép sang `vat_pct` của dòng YCMH và tính vào thành tiền. **Trước CR-058 bước chép này bị bỏ sót** — dòng YCMH nhận mặc định 0% dù phương án có thuế, và `amount` tính thiếu VAT; YCMH tạo trước CR-058 cần kiểm lại cột VAT bằng tay.

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

## D. Bảng liên kết lịch sử YCMH (`SurveyRequestPr`)

Bảng `tab_survey_request_pr` lưu lịch sử mỗi lần sinh YCMH từ một option của một dòng YCBG. Cho phép 1 dòng tạo nhiều YCMH ở các thời điểm khác nhau (tái sử dụng dòng — mua lại).

| Trường | Kiểu | Ý nghĩa |
|--------|------|---------|
| `survey_request_id` | BigInt | FK phiếu YCBG |
| `survey_request_line_id` | BigInt | FK dòng YCBG |
| `option_id` | BigInt | FK option được chọn |
| `product_survey_line_id` | BigInt | FK dòng khảo sát SP nguồn (đếm toàn hệ thống) |
| `pr_id` | BigInt | FK PYC được sinh |
| `pr_code` | String | Mã PYC |

Dữ liệu trong bảng này được dùng để:
- Hiển thị `ycmh_list` trên màn kết quả (endpoint `/result`): mỗi option có danh sách PYC đã sinh kèm ngày và trạng thái.
- `auto_complete_from_pr`: tra mọi `pr_id` thuộc YCBG qua bảng này; nếu tất cả đều `completed` thì YCBG tự chuyển `done`.

---

## E. Quy tắc nghiệp vụ

1. Mã phiếu tự sinh ngay sau khi tạo theo `YCBG{DDMMYY}{seq:02d}`. Số thứ tự lấy MAX hậu tố hiện có + 1 (tránh trùng khi có khoảng trống do xóa). Đặt lại từ 01 mỗi ngày (không đặt lại theo tháng/năm). Mã dòng nội bộ: `YCBGL{id:06d}`.

2. Validate khi Lưu/Gửi duyệt (phía FE): phải có Công ty (`company_id`), Người yêu cầu (`requester`), Mục đích (`purpose`), và ít nhất 1 dòng có `item_group` hoặc `requirement_detail`.

3. Sửa nội dung phiếu chỉ cho phép khi `status = draft` hoặc `rejected`. Backend trả HTTP 400 "Chỉ sửa được khi phiếu ở trạng thái Nháp hoặc Bị trả lại (phiếu Đã từ chối đã khóa — hãy Nhân bản thành phiếu mới)" nếu cố sửa ở trạng thái khác. Phiếu `cancelled` bị khóa vĩnh viễn — hệ thống gợi ý Nhân bản (`clone`) thành phiếu nháp mới.

4. Sau khi Duyệt: hàm `auto_assign` tự gán NSTM cho từng dòng theo bảng `CategoryAssignee` (khớp `item_group`) và cập nhật `received_date`. **Chỉ gán ở dòng — không ghi NSTM nào ở đầu phiếu** (CR-018). Phiếu chuyển `processing` trong cùng một request. Gửi hai thông báo riêng: (a) **Đã duyệt** — tới người tạo + Quản lý TM + Admin TM; (b) **Phân công khảo sát** — tới NSTM vừa được tự gán theo phân loại (nếu có).

5. Cơ chế ẩn NCC: endpoint `GET /{id}/result` (dành cho người YC) chỉ trả các field trong `_OPT_PUBLIC_FIELDS` và `_LINE_PUBLIC_FIELDS`. Các field `supplier_code`, `supplier_name`, `snap_internal_code`, `nstm_note`, `supplier_survey_id`, `product_survey_line_id` bị loại ở tầng Python trước khi trả response — không thể lấy được kể cả gọi API trực tiếp với token người YC.

6. Vào màn Xử lý (`GET /{id}/process`): chỉ người có `survey_request:read` với scope `proc` hoặc `all` (`is_purchaser`) mới được vào. Backend kiểm tra và trả HTTP 403 cho người YC (scope `own`/`dept`).

7. NSTM scope `proc` chỉ gắn/xóa/sửa option cho dòng mình phụ trách (`can_process_line`): hoặc `assignee == emp_code`, hoặc phân loại dòng thuộc `CategoryAssignee.primary_employee_id` / `backup_employee_id` của NSTM đó. Admin/QL TM (scope `all`) xử lý được mọi dòng.

8. Gắn option thủ công: NSTM chọn NCC → gọi `GET /{id}/lines/{line_id}/available-survey-lines?supplier_code=...` lấy dòng khảo sát SP đã duyệt (`line_approve = "Đã duyệt"`, phiếu khảo sát không phải `cancelled`) khớp phân loại → chọn 1 hoặc nhiều dòng → `POST /{id}/lines/{line_id}/options`. Không thể gắn cùng 1 `product_survey_line_id` hai lần cho cùng 1 dòng YCBG. Tối đa 5 option mỗi dòng (`MAX_OPTIONS_PER_LINE = 5`).

9. Nút "Tạo phiếu khảo sát" (chỉ hiển thị khi `status = processing`, với người có quyền `process`): điều hướng sang `/surveys/new?sr={id}&sr_code={code}`, truyền sẵn liên kết YCBG để Phiếu khảo sát mới tự gắn `survey_request_id`. Khi Phiếu khảo sát được duyệt, hệ thống có thể dùng nút "Lấy từ khảo sát" để tự gắn option.

10. Nút "Lấy từ khảo sát" (`POST /{id}/sync-options`): hàm `sync_options_from_surveys` tìm mọi Phiếu khảo sát (`status` bất kỳ trừ `cancelled`) đã liên kết YCBG qua `survey.survey_request_id = sid`, lấy dòng SP `line_approve = "Đã duyệt"`, khớp `item_group` với dòng YCBG để gắn option. Nếu YCBG chỉ có 1 dòng nhưng phân loại không khớp thì cũng tự gắn vào dòng đó. Bỏ qua dòng đã có option nguồn đó. Trả về số option mới thêm. Chỉ hoạt động khi `status = processing` hoặc `survey_done`. (Lưu ý: frontend chỉ hiện nút "Lấy từ khảo sát" khi `processing`, nhưng backend cho phép cả `survey_done`.)

11. Chốt hoàn thành khảo sát (`POST /{id}/complete`, chấp nhận `processing` hoặc `survey_done`): Backend validate rằng các dòng người gọi phụ trách (`my_lines`) đều có ít nhất 1 option HOẶC được "chốt rỗng" (`no_option = true`). Body tùy chọn: `{empty_line_ids: [...]}` — danh sách dòng chưa có option nhưng NSTM muốn chốt rỗng (không có NCC phù hợp). Phiếu chuyển `survey_done` chỉ khi TẤT CẢ dòng (mọi NSTM) đã có option hoặc được chốt rỗng; nếu còn dòng của NSTM khác chưa xong thì phiếu giữ nguyên `processing`. Quản lý/Admin TM (scope `all`) và người tạo phiếu validate toàn bộ dòng cùng lúc. Frontend kiểm tra thêm trước khi gọi API: mọi option hiển thị phải có `system_product_code`. Khi phiếu chuyển sang `survey_done`, gửi thông báo cho người YC (phân biệt 2 nội dung: "Khảo sát xong" vs "Đã khảo sát lại" nếu có dòng vừa khảo sát lại sau cờ `resurvey`).

12. Tạo YCMH (`POST /{id}/create-prs`): Được phép gọi khi phiếu ở trạng thái `processing`, `survey_done`, `pr_created`, hoặc `done`. Gom option đang được chọn (`is_chosen = true`) theo `supplier_code` → mỗi NCC 1 PYC Nháp. Mỗi dòng YCMH lấy `qty` từ `request_qty` của dòng khảo sát, `price` từ `snap_price_by_volume`, **`vat_pct` từ `snap_vat`** và `amount = qty × price × (1 + vat_pct/100)` (gồm VAT — cùng công thức với khi lập YCMH bằng tay). Bước chép VAT được bổ sung ở **CR-058**; trước đó dòng nhận 0% và `amount` thiếu thuế. Sau khi tạo: option tự bỏ chọn (`is_chosen = false`); dòng cập nhật `pr_id`/`pr_code` (YCMH gần nhất) và `is_completed = true` (cờ "đã từng tạo"); ghi bản ghi vào `tab_survey_request_pr`. Cờ `is_completed` KHÔNG ngăn tạo thêm YCMH lần sau — người YC chọn lại option và bấm "Tạo yêu cầu mua" lần nữa là được (tái sử dụng dòng, mua lại). Chỉ nâng status `survey_done → pr_created`; không thay đổi nếu phiếu đang `pr_created` / `done`. Ghi vào bảng `tab_survey_request_pr` để theo dõi toàn bộ lịch sử YCMH. Chỉ người YC (`created_by` hoặc `requester_id == user.employee_id`) hoặc Admin TM (quyền `delete`) được gọi.

13. Tự hoàn thành (`auto_complete_from_pr`): khi 1 PYC liên quan chuyển sang `completed`, hàm tra tất cả `pr_id` trong `tab_survey_request_pr` của YCBG đó. Nếu tất cả đều `completed` và YCBG đang `pr_created` → tự chuyển YCBG sang `done` và ghi audit log "Tự hoàn thành".

14. Xóa phiếu: chỉ khi `draft`, `rejected`, hoặc `cancelled` (backend kiểm tra). Xóa cascade: xóa toàn bộ `SurveyRequestOption` của các dòng trước, rồi xóa `SurveyRequestLine`, cuối cùng xóa phiếu header. Hỗ trợ xóa hàng loạt qua `DELETE /api/survey-requests?ids=1,2,3`.

15. Hiển thị dòng theo người xem (`visible_lines_for`): Thấy **hết** dòng nếu là người **tạo phiếu** (`created_by`) HOẶC là **người yêu cầu** (`requester_id == user.employee_id`) HOẶC có quyền **duyệt** (`survey_request:approve`) HOẶC có phạm vi đọc `dept`/`company`/`all` HOẶC là Admin thu mua đọc-chỉ (scope `proc` + không có quyền `write`). NSTM thường (scope `proc` + có `write`) chỉ thấy dòng được giao hoặc phân loại mình phụ trách theo bảng `CategoryAssignee`. Quy tắc áp dụng cho cả endpoint `GET /{id}`, `GET /{id}/process`, hàm `complete_sr` và hàm `clone_sr`.

16. Lọc option hợp lệ (`valid_options_of`): Xem phần C — logic bảo toàn snapshot khi nguồn bị xóa, ẩn option khi nguồn còn tồn tại nhưng bị "Không duyệt".

17. Nhân bản phiếu (`POST /{id}/clone`, quyền `survey_request:create`): Tạo phiếu Nháp mới — sao chép toàn bộ trường header (`company_id`, `requester`, `requester_position`, `department`, `head_of_dept`, `purpose`, `request_date`, `note`) và các dòng mà người dùng được xem (`visible_lines_for`). Người yêu cầu của bản sao = người bấm nhân bản (không giữ người yêu cầu phiếu gốc) — hệ thống tra hồ sơ nhân viên của người clone để điền lại. Sinh mã phiếu mới theo quy tắc `_gen_code`. Các thông tin sau KHÔNG được sao chép: `assignee` (reset về rỗng), `received_date` (reset về rỗng), option, `pr_id`/`pr_code`, `is_completed`, `line_status`, `no_option`. Đính kèm file dòng được tái sử dụng (thêm `FileLink` mới trỏ cùng file gốc — không sao chép file vật lý). Có thể nhân bản từ bất kỳ trạng thái nào, kể cả phiếu `cancelled`.

18. Thông báo và Web Push: mỗi sự kiện dưới đây tạo chuông trong app **và** đẩy **Web Push** (best-effort) tới thiết bị đã đăng ký của người nhận.

| Sự kiện | Người nhận thông báo |
|---------|---------------------|
| Gửi duyệt (`submit`) | Người có quyền `survey_request:approve` (Quản lý/Admin TM) + Trưởng bộ phận của người YC |
| Duyệt (`approve`) | Người tạo + Quản lý TM + Admin TM |
| Phân công NSTM tự động (ngay sau duyệt) | NSTM vừa được gán theo phân loại |
| Phân công dòng thủ công (`set_line_assignee`) | NSTM được gán vào dòng |
| Trả đơn (`reject` → `rejected`) | Người tạo |
| Từ chối (`cancel` → `cancelled`) | Người tạo |
| Chốt hoàn thành khảo sát lần đầu (`complete` → `survey_done`) | Người tạo (nội dung: "Kết quả khảo sát đã sẵn sàng — vào chọn phương án") |
| Chốt khảo sát lại (`complete` sau `resurvey`) | Người tạo (nội dung: "NSTM đã khảo sát lại N dòng — vào chọn lại phương án") |
| Tạo YCMH từ phương án (`create-prs`) | Quản lý TM + Admin TM |
| Chuyển Hoàn thành (`finalize`) | Người tạo |

---

### Lối vào từ YCMH bị trả lại / từ chối (CR-026)

Ngoài lối tạo YCBG thông thường, màn `/survey-requests/new` còn nhận dữ liệu điền sẵn từ nút **"Tạo yêu cầu báo giá"** trên phiếu YCMH ở trạng thái `rejected` (Bị trả lại) hoặc `cancelled` (Đã từ chối). Dữ liệu đi kèm điều hướng (`location.state`), **chưa ghi DB**; tiêu đề phiếu hiện nhãn `Từ {mã YCMH}` để biết nguồn. Chi tiết ánh xạ trường xem [03-yeu-cau-mua-hang.md](03-yeu-cau-mua-hang.md) §C.21.

Bổ sung ở CR-027:

- **Ảnh đối chiếu theo dòng được kéo sang.** Mỗi dòng điền sẵn mang thêm `src_pr_item_id`; `POST /api/survey-requests` (và `PATCH` khi thêm dòng mới) đọc trường này rồi chép **liên kết file** từ `("purchase_request_line_image", id dòng YCMH)` sang `("survey_request_line", id dòng YCBG)` — cùng `file_id`, không upload lại. Chỉ chép dòng thuộc YCMH mà người dùng có quyền xem. Trường này **không phải cột DB**, chỉ dùng lúc tạo dòng; sửa phiếu lần sau không chép lại lần nữa.
- **Nút quay lại** (mũi tên góc trái) khi mở từ YCMH sẽ về **đúng phiếu YCMH nguồn** (`/purchase-requests/{id}`) thay vì nhảy ra danh sách YCBG.

## F. Quyền thao tác (RBAC)

Entity: `survey_request`. Actions: `read`, `create`, `write`, `approve`, `cancel`, `delete`, `process`.

| Thao tác | Quyền yêu cầu | Điều kiện trạng thái | Ghi chú scope |
|----------|---------------|----------------------|---------------|
| Xem danh sách / chi tiết | `survey_request:read` | mọi trạng thái | `own` → chỉ phiếu mình tạo; `dept` → phòng ban; `proc` → NSTM phụ trách (theo dòng `assignee` hoặc phân loại); `all` → toàn bộ |
| Tạo phiếu mới | `survey_request:create` | — | — |
| Sửa nội dung phiếu | `survey_request:read` + (`created_by == user.id` hoặc `requester_id == user.employee_id` hoặc `survey_request:write`) | `draft`, `rejected` | Backend kiểm tra `_can_edit_own` |
| Gửi duyệt | như Sửa | `draft`, `rejected` | — |
| Duyệt phiếu | `survey_request:approve` | `submitted` | Tự chuyển sang `processing` sau khi duyệt; tự gán NSTM |
| Trả đơn (`reject`) | `survey_request:approve` | `submitted` | Phiếu về `rejected`, người YC sửa và gửi lại được |
| Từ chối (`cancel`) | `survey_request:approve` | `submitted` | Phiếu về `cancelled`, khóa vĩnh viễn |
| Vào màn Xử lý khảo sát | `survey_request:read` + `is_purchaser` (scope `proc`/`all`) | mọi trạng thái | Người YC (scope `own`/`dept`) bị chặn tại backend (HTTP 403) |
| Gán NSTM cho dòng | `survey_request:process` | mọi trạng thái (trừ `cancelled`/`done`) | NSTM / QL / Admin TM |
| Gắn option cho dòng | `survey_request:process` + `can_process_line` | `processing`, `survey_done` | NSTM scope `proc`: chỉ dòng mình phụ trách; Admin/QL scope `all`: mọi dòng |
| Xóa option | `survey_request:process` + `can_process_line` + dòng chưa `is_completed` | `processing`, `survey_done` | — |
| Đặt Mã SP hệ thống cho option | `survey_request:process` + `can_process_line` | mọi trạng thái | — |
| Cập nhật ghi chú NSTM cho option | `survey_request:process` + `can_process_line` | mọi trạng thái | — |
| Lấy từ khảo sát (`sync-options`) | `survey_request:process` + `is_purchaser` | `processing`, `survey_done` | `POST /{id}/sync-options` |
| Chốt hoàn thành khảo sát | `survey_request:process` + `is_purchaser` | `processing`, `survey_done` | Backend validate dòng người gọi phụ trách; phiếu chuyển `survey_done` khi mọi dòng đủ option hoặc chốt rỗng |
| Chọn phương án (người YC) | `survey_request:write` + (`created_by == user.id` hoặc `requester_id == user.employee_id` hoặc `write`) | `processing`, `survey_done`, `pr_created`, `done` | Endpoint `PATCH /{id}/lines/{line_id}/options/{oid}/choose` |
| Đổi trạng thái dòng (`line-status`) | `survey_request:write` + `_can_act_as_requester_side` (người YC, cùng phòng ban, hoặc Admin TM) | mọi trạng thái (trừ `cancelled`/`done`) | `PATCH /{id}/lines/{line_id}/line-status`; body: `{line_status: ""}` |
| Đổi `is_completed` thủ công | `survey_request:write` | mọi trạng thái (trừ `cancelled`/`done`) | `PATCH /{id}/lines/{line_id}/status`; body: `{is_completed: bool}` |
| Tạo YCMH từ phương án | `created_by == user.id` hoặc `requester_id == user.employee_id` hoặc `survey_request:delete` | `processing`, `survey_done`, `pr_created`, `done` | Gom theo NCC; chỉ người YC hoặc Admin TM |
| Chuyển Hoàn thành (finalize) | (`survey_request:approve` + `is_purchaser`) HOẶC `_can_act_as_requester_side` (người YC, cùng phòng ban, Admin TM) | `survey_done`, `pr_created` | Admin/QL TM hoặc phía người yêu cầu |
| Nhân bản phiếu | `survey_request:create` | mọi trạng thái | `POST /{id}/clone` |
| Xóa phiếu | `survey_request:delete` | `draft`, `rejected`, `cancelled` | Xóa cascade dòng và option |

---

## G. Xuất Excel danh sách (CR-068)

Nút **"Xuất Excel"** trên thanh công cụ màn danh sách YCBG, chỉ hiện với người có hành động
**`export`** trên `survey_request`. Endpoint: `GET /api/survey-requests/export/xlsx`.

**Xuất cái gì**

- Đúng **bộ lọc + thứ tự sắp xếp** đang áp và đúng **các cột đầu phiếu đang hiển thị**; không tick
  dòng nào thì xuất **toàn bộ kết quả đang lọc**, tick thì chỉ xuất phiếu đã tick.
- **Mỗi DÒNG YÊU CẦU là một dòng Excel**, cụm đầu phiếu lặp lại; phiếu chưa có dòng vẫn ra một hàng.
- **CHỈ xuất PHƯƠNG ÁN ĐÃ CHỐT** của từng dòng (quyết định của khách) — các option còn lại không ra
  file. Dòng chưa chốt phương án thì cụm phương án để trống.

**Bộ cột**: cụm dòng yêu cầu (STT dòng · Mã dòng nội bộ · Phân loại · Thông số kỹ thuật · Yêu cầu khác ·
SL dự kiến · ĐVT · Giá đề xuất · Ngày tiếp nhận · Hạn trả kết quả · NSTM phụ trách · Trạng thái dòng ·
Mã YCMH đã tạo) rồi tới cụm phương án chốt (Phương án chốt · Mã/Tên NCC · Mã SP theo NCC ·
Mã SP hệ thống · Tên SP báo giá · Quy cách · Xuất xứ · ĐVT báo giá · SL tối thiểu · Đơn giá báo ·
Khoảng SL áp giá · %VAT · Thời gian giao · Nơi giao · Phí vận chuyển · Có mẫu · Kết quả kiểm nghiệm ·
Ghi chú NSTM).

**ẨN NCC — file Excel không được thành đường rò.** Đúng luật của màn kết quả khảo sát:

| Người xuất | File nhận được |
|---|---|
| Không có `supplier.read` (người yêu cầu, trưởng bộ phận…) | **Bỏ hẳn** các cột Mã NCC · Tên NCC · Mã SP theo NCC · Ghi chú NSTM · Mã dòng nội bộ |
| NSTM (không có phạm vi `all`) | Chỉ xuất **dòng mình được giao hoặc thuộc phân loại mình phụ trách**; STT dòng đánh lại theo số dòng thấy được |
| Người tạo · người yêu cầu · Quản lý/Admin TM | Thấy hết dòng của phiếu |

Quy ước định dạng file, trần 5.000 dòng/lần xuất và tên file `yeu-cau-bao-gia-DDMMYYYY.xlsx` — xem
[03-yeu-cau-mua-hang.md §G](03-yeu-cau-mua-hang.md).

**Ai được xuất.** Vai trò chuẩn có sẵn ô "Xuất" của YCBG: *Trưởng phòng · NV thu mua · Admin thu mua ·
Quản lý thu mua · Quản trị hệ thống*. Vai trò **"Nhân sự"** (người yêu cầu thường) **KHÔNG** được xuất —
muốn cho ai đó xuất thì tạo một **vai trò riêng** chỉ tick ô "Xuất" của màn tương ứng rồi gán thêm cho
người đó. Vai trò **tự tạo tay** cũng phải tick ô "Xuất" mới thấy nút.

---

## H. Màn "Tiến độ báo giá" (CR-075)

Đường dẫn `/survey-progress`, menu **Mua hàng → Tiến độ báo giá**. Là màn song sinh của
**Tiến độ mua hàng** nhưng đọc chuỗi Yêu cầu báo giá. Endpoint `GET /api/survey-progress`
(module `app/modules/survey_progress/` — **không** dùng chung code với `purchase_progress/`).

**Đơn vị một hàng = MỘT DÒNG yêu cầu**, kèm phương án đã chốt của dòng đó. Khác Tiến độ mua hàng
ở chỗ này: bên kia nở theo LẦN GIAO, bên này **không** nở theo phương án — dòng có 5 phương án
vẫn là một hàng, vì thứ cần theo dõi là "dòng này khảo sát tới đâu rồi", không phải "có mấy báo giá".

**Ba cột tính** — phần giá trị riêng của màn này, không có trong màn danh sách YCBG:

| Cột | Cách tính |
|---|---|
| **Trễ (ngày)** | Đã trả kết quả: `result_date − result_due_date`. **Chưa trả mà đã quá hạn: `hôm nay − result_due_date`** (đang trễ, số còn tăng). Trả sớm/đúng hạn/không có hạn → để trống; **không hiện số âm** vì cột này để soi việc trễ |
| **Số ngày xử lý** | `result_date − received_date`; thiếu một trong hai mốc → để trống |
| **Tiến độ dòng** | Suy từ dữ liệu đang có, **không lưu cột riêng**. Nguồn duy nhất: `survey_request/line_state.py` — **cả màn chi tiết YCBG cũng dùng chung** (CR-077). Xếp từ mốc xa nhất về gần: **Hoàn thành** › Đã tạo YCMH › Cần khảo sát lại › Đã chọn phương án › Chốt rỗng › Đã trả kết quả › Đang khảo sát › Đã tiếp nhận › Chưa tiếp nhận. **Hoàn thành là điểm cuối** (CR-077, trước đó thua "Đã tạo YCMH"): một dòng tạo được YCMH nhiều lần khi mua lại, nên `pr_code` không khép dòng; chỉ khi người YC chốt hoàn thành thì dòng mới thật sự xong |

**Bộ lọc**: Công ty · Bộ phận · Phân loại · NSTM phụ trách · **Tiến độ dòng** · Trạng thái phiếu ·
Trạng thái dòng · Đã/chưa trả kết quả · **Chỉ dòng trễ hạn** · Tháng tiếp nhận · ba khoảng ngày
(tiếp nhận, hạn trả kết quả, ngày trả kết quả) · từ khóa (mã YCBG · mục đích · phân loại · thông số ·
mã YCMH). Lọc theo **Tiến độ dòng** được dịch sang SQL bám đúng thứ tự ưu tiên ở trên — mỗi nhãn là
"khớp mốc của mình VÀ không khớp mốc nào xa hơn", nên chín nhãn chia trọn số dòng, không trùng không
sót. Sắp xếp tại server theo cột thật; ba cột tính ở trên **không sort được** vì giá trị không nằm
trong DB (sort trên trang đang xem thì làm ở trình duyệt).

**Xuất Excel**: `GET /api/survey-progress/export/xlsx`, gate ở hành động **`export`** trên
`survey_request`, xuất đúng bộ lọc + đúng cột đang hiện, trần 5.000 dòng, tên file
`tien-do-bao-gia-DDMMYYYY.xlsx`.

**Phân quyền — hai cờ RỜI, đừng gộp** (bài học CR-071):

| Cờ | Quyết định |
|---|---|
| `survey_request.read` | Vào được màn hay không, và **phạm vi dữ liệu** (qua `apply_scope`). NSTM chỉ thấy dòng mình phụ trách — điều kiện dòng dịch nguyên từ `_see_all_lines` / `can_process_line` sang SQL |
| `supplier.read` | Cụm cột NCC (Mã/Tên NCC · Mã SP theo NCC · Ghi chú NSTM · Mã dòng nội bộ) hiện hay **bị gỡ khỏi dữ liệu** — gỡ ở API chứ không chỉ ẩn cột, để màn tiến độ không thành đường rò danh tính nhà cung cấp |
