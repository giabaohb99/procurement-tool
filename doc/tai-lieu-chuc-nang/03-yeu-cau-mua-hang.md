# Yêu cầu mua hàng (PYC)

## Mục đích

Ghi nhận nhu cầu mua vật tư, hàng hóa, dịch vụ từ các bộ phận trong công ty. Một phiếu gồm thông tin chung (header) và danh sách dòng hàng (items). Sau khi được duyệt, phiếu chuyển sang giai đoạn xử lý thu mua và theo dõi tiến độ từng dòng.

Đường dẫn: `/purchase-requests` (danh sách), `/purchase-requests/:id` (chi tiết), `/purchase-requests/new` (tạo mới).

## Vai trò tham gia

- Người yêu cầu / Nhân viên (`purchase_request:create`, `purchase_request:read`): tạo và gửi duyệt phiếu của mình.
- TP/QL / Người duyệt (`purchase_request:approve`): duyệt hoặc từ chối; phân bổ NSTM phụ trách.
- Admin / Quản lý thu mua (`purchase_request:cancel`): hủy đơn, trả phiếu về Nháp, đánh dấu Hoàn thành.
- Nhân sự thu mua (NSTM) (`purchase_request:read`, được giao dòng): cập nhật trạng thái và tiến độ các dòng được phân công.
- Người có `purchase_request:write`: sửa nội dung phiếu của người khác (ngoài chủ phiếu).

## Vòng đời trạng thái

| Mã trạng thái | Tên hiển thị | Ý nghĩa | Nút thao tác hiển thị |
|--------------|--------------|---------|----------------------|
| `draft` | Nháp | Đang soạn, chưa gửi | Lưu, Gửi duyệt, Xóa (nếu có `delete`) |
| `submitted` | Chờ duyệt | Đã gửi, đợi TP/QL | Duyệt, Từ chối (nếu có `approve`) |
| `approved` | Đã duyệt | TP/QL đã duyệt, chờ NSTM xử lý | Trả về, Hủy đơn (nếu có `cancel`) |
| `processing` | Đang xử lý | Ít nhất 1 dòng đã bắt đầu xử lý | Trả về, Hủy đơn, Hoàn thành (nếu có `cancel`) |
| `completed` | Hoàn thành | Tất cả dòng Hoàn thành hoặc đánh dấu thủ công | (chỉ xem) |
| `rejected` | Từ chối | TP/QL từ chối; vẫn cho sửa và gửi lại | Lưu, Gửi duyệt lại |
| `cancelled` | Đã hủy | Phiếu bị hủy (khóa) | (chỉ xem) |

**Điều kiện chuyển trạng thái:**

- `draft` / `rejected` → `submitted`: người tạo hoặc có `write` nhấn "Gửi duyệt"; yêu cầu pass `validate()`.
- `submitted` → `approved`: người có `approve` nhấn "Duyệt"; tự động phân công NSTM theo phân loại (`auto_assign_by_category`).
- `submitted` → `rejected`: người có `approve` nhấn "Từ chối" và nhập lý do.
- `approved` / `processing` / `completed` → `draft`: người có `cancel` nhấn "Trả về" (reset toàn bộ NSTM và trạng thái dòng về "Chưa đặt hàng").
- `approved` / `processing` → `cancelled`: người có `cancel` nhấn "Hủy đơn" và nhập lý do.
- `approved` / `processing` → `completed`: thủ công qua nút "Hoàn thành" (người có `cancel`); hoặc tự động khi tất cả dòng đều là "Hoàn thành".
- `approved` → `processing`: tự động khi ít nhất 1 dòng có trạng thái khác "Chưa đặt hàng" (hàm `recompute_status`).

Chỉ trạng thái `draft` và `rejected` cho phép sửa nội dung header và dòng hàng. Sau khi duyệt, chỉ NSTM phụ trách (hoặc người có `approve`/`cancel`) cập nhật được trạng thái/tiến độ dòng qua endpoint `/item-status` và `/assign`.

---

## A. Thông tin chung (header phiếu)

### 1. Mã phiếu yêu cầu (`code`)

- Kiểu nhập: Nhập tay hoặc để trống (tự sinh)
- Mặc định: trống — hệ thống tự sinh theo định dạng `PYC{ddmmyy}{seq:02d}` dựa trên `request_date`
- Bắt buộc: Không (tự sinh nếu trống)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo (chỉ khi tạo mới, trường bị khóa sau khi phiếu đã lưu)
- Logic đặc biệt: Trường bị `disabled` sau lần tạo đầu tiên (`!isNew`). Mã hiển thị trên bản in khi `show_code_on_print = true`.

### 2. Ngày tiếp nhận (`request_date`)

- Kiểu nhập: Chọn ngày (date input)
- Mặc định: Ngày hiện tại (hôm nay, `new Date().toISOString().slice(0,10)`)
- Bắt buộc: Có (đánh dấu `*` trên UI)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Ngày này ảnh hưởng đến định dạng mã tự sinh (`ddmmyy` lấy từ `request_date`).

### 3. Công ty nhận hóa đơn (`company_id`)

- Kiểu nhập: Chọn (SearchSelect, tìm kiếm theo tên)
- Mặc định: 0 (chưa chọn); tự điền từ công ty của Nhân sự YC nếu nhân sự đã có `company_id`
- Bắt buộc: Có (`validate()` kiểm tra: "Vui lòng chọn Công ty")
- Nguồn dữ liệu / liên kết: Bảng Công ty (`company`), API `/api/companies`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Tên công ty (`company_name`) được tra cứu và gắn vào response để hiển thị; không lưu riêng.

### 4. Nhân sự yêu cầu (`requester`)

- Kiểu nhập: Chọn (SearchSelect, tìm theo tên đầy đủ)
- Mặc định: Tự điền tên người đang đăng nhập (khớp email hoặc full_name với danh sách nhân sự)
- Bắt buộc: Có (`validate()` kiểm tra: "Vui lòng chọn Nhân sự yêu cầu")
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`employee`), API `/api/employees`
- Người sửa: Người có `write` (TP/QL); nhân viên thường (`isStaff`) bị khóa trường này — chỉ điền tên mình
- Logic đặc biệt: Chọn nhân sự tự điền `requester_position`, `department`, `head_of_dept`, `company_id` theo dữ liệu nhân sự đó.

### 5. Chức vụ (`requester_position`)

- Kiểu nhập: Nhập tay (tự điền khi chọn Nhân sự YC)
- Mặc định: trống; tự điền từ `employee.position` hoặc `employee.role_name`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ `employee.position`; có thể sửa thủ công sau
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`

### 6. Bộ phận yêu cầu (`department`)

- Kiểu nhập: Tự động (trường bị khóa `disabled`)
- Mặc định: trống; tự điền theo phòng ban của Nhân sự YC đã chọn
- Bắt buộc: — (hệ thống điền, không sửa trực tiếp)
- Nguồn dữ liệu / liên kết: Lấy tên phòng ban từ `employee.department_id` → `department.name`
- Người sửa: Hệ thống (thay đổi khi đổi Nhân sự YC)

### 7. Trưởng bộ phận (`head_of_dept`)

- Kiểu nhập: Tự động (trường bị khóa `disabled`)
- Mặc định: trống; tự điền từ trưởng phòng của bộ phận
- Bắt buộc: Có (đánh dấu `*` trên UI); điền tự động nên ít khi trống nếu phòng ban đã có trưởng
- Nguồn dữ liệu / liên kết: Tìm nhân sự cùng phòng có chức danh chứa "trưởng" / "manager" / "head"; hoặc qua API `/api/purchase-requests/meta/dept-head`
- Người sửa: Hệ thống (cập nhật khi đổi Nhân sự YC; phía BE cũng tự điền khi tạo qua `find_dept_head`)

### 8. Đơn gấp (`is_urgent`)

- Kiểu nhập: Checkbox
- Mặc định: Không tích (`false`)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Khi tích, hệ thống gắn cờ ưu tiên trong thông báo (`is_urgent=true` được truyền vào `trigger_notification`). Danh sách hiển thị badge "Gấp" màu cam.

### 9. Mục đích mua hàng (`purpose`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Có (đánh dấu `*` trên UI)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Trường này được dùng làm tiêu đề phiếu trên trang chi tiết (`pr.purpose || pr.code`). Phiếu khảo sát (Survey) liên kết PYC cũng tự điền `requirement_detail` từ trường này.

### 10. Nội dung mua hàng (`note`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`

### 11. NSTM phụ trách phiếu (`assignee_id`)

- Kiểu nhập: Tự động (gán qua endpoint `PATCH /assign`, không có ô nhập trực tiếp trong form header)
- Mặc định: 0 (chưa gán)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`employee`)
- Người sửa: Người có `approve` (qua endpoint `PATCH /{pid}/assign`); tự động điền khi duyệt nếu truyền `assignee_id` vào `ApproveIn`
- Logic đặc biệt: Ảnh hưởng đến data scope — nhân viên thu mua chỉ thấy phiếu được giao cho mình (theo cấu hình scope `assigned`).

### 12. Hiện mã trên bản in (`show_code_on_print`)

- Kiểu nhập: Checkbox (ẩn trong form chính, có trong schema)
- Mặc định: `true`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Kiểm soát việc hiển thị mã PYC trên bản in (`/print/purchase-request/:id`).

### 13. Tên nhà cung cấp đề xuất (`suggested_supplier`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`

### 14. Mã số thuế NCC đề xuất (`suggested_supplier_tax_code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`

### 15. Liên hệ NCC đề xuất (`suggested_supplier_contact`)

- Kiểu nhập: Nhập tay (SĐT / Email / Địa chỉ)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`

### 16. Báo giá đính kèm (`quote_filename` + `quote_file_url`)

- Kiểu nhập: Upload file (1 file, chọn qua nút "Chọn báo giá")
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Lưu trên Cloudflare R2 qua API `/api/attachments` (entity `purchase_request_quote`); URL trả về ghi vào `quote_file_url`, tên file ghi vào `quote_filename`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Chỉ upload được sau khi phiếu đã được tạo (`!isNew`). Xóa file chỉ xóa tham chiếu (reset về trống), không xóa file trên R2.

### 17. Tỷ lệ VAT (`vat_rate`)

- Kiểu nhập: Số (không hiển thị trên form UI hiện tại)
- Mặc định: `0.08` (8%)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Qua API (không có ô nhập trực tiếp trên form)
- Logic đặc biệt: Trường được lưu nhưng KHÔNG dùng để tính tổng tiền ở PYC (`vat = 0`, `total = subtotal`). Thuế chỉ tính ở giai đoạn PO / hóa đơn. Lưu lại để tham khảo hoặc dùng ở chức năng khác.

---

## B. Dòng hàng (items)

Mỗi dòng = một sản phẩm / vật tư yêu cầu mua. Bảng tóm tắt hiện các cột chính; toàn bộ trường xem và sửa trong popup "Chi tiết dòng".

### 1. Mã hàng (`product_code`)

- Kiểu nhập: Chọn sản phẩm (ProductPicker — tìm theo mã hoặc tên)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Danh mục Sản phẩm (`product`), API `/api/products`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Chọn mã tự điền `product_name`, `unit`, `item_group`, `group_desc`. Nếu không có trong danh mục, có thể nhập thủ công `product_name` trực tiếp.

### 2. Tên sản phẩm (`product_name`)

- Kiểu nhập: Nhập tay hoặc tự điền khi chọn Mã hàng
- Mặc định: trống
- Bắt buộc: Có (đánh dấu `*`; dòng chỉ được lưu khi `product_name` không trống — `validate()` kiểm tra "Cần ít nhất 1 sản phẩm")
- Nguồn dữ liệu / liên kết: Tự điền từ `product.name`; có thể nhập tay tự do
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Đây là trường xác định dòng — chỉ các dòng có `product_name` không trống mới được gửi lên BE khi lưu (`items.filter(it => it.product_name)`).

### 3. Phân loại (`item_group`)

- Kiểu nhập: Chọn (SearchSelect, gõ để lọc) hoặc tự điền khi chọn Mã hàng
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Phân loại (`item_group`), API `/api/item-groups`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Khi chọn Phân loại, tự điền `group_desc` với thông tin thời gian sản xuất tiêu chuẩn. Phân loại cũng được dùng để tự phân công NSTM khi duyệt phiếu (`auto_assign_by_category`).

### 4. Mô tả phân loại (`group_desc`)

- Kiểu nhập: Tự động (trường bị khóa)
- Mặc định: trống; tự điền khi chọn Phân loại hoặc Mã hàng
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tính từ `item_group.std_days` và `item_group.std_days_unavail` (vd: "Hàng NCC có sẵn: 7 ngày · không sẵn: 14 ngày")
- Người sửa: Hệ thống (chỉ hiển thị)

### 5. Số lượng mua (`qty`)

- Kiểu nhập: Nhập số
- Mặc định: 0 (hiển thị trống khi bằng 0)
- Bắt buộc: Có (`validate()` yêu cầu `qty > 0` cho mỗi dòng có `product_name`)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Dùng trong công thức tính Thành tiền: `qty × price`.

### 6. ĐVT (`unit`)

- Kiểu nhập: Chọn (SearchSelect, gõ để lọc) hoặc tự điền khi chọn Mã hàng
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Đơn vị tính (`unit`), API `/api/units`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`

### 7. Giá đề xuất (`price`)

- Kiểu nhập: Nhập số (VNĐ)
- Mặc định: 0 (hiển thị trống khi bằng 0)
- Bắt buộc: Không ("Để trống nếu chưa có giá")
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Dùng trong công thức tính Thành tiền: `qty × price`. Nếu để trống, Thành tiền bằng 0.

### 8. Thành tiền (`amount`)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính, không sửa)
- Nguồn dữ liệu / liên kết: `qty × price` (tính ở FE và lưu vào DB tại hàm `_save_items`: `data["amount"] = round(qty * price, 2)`)
- Người sửa: Hệ thống (chỉ hiển thị)
- Logic đặc biệt: PYC KHÔNG tính VAT — `total = subtotal = sum(amount)` (VAT chỉ tính ở PO/hóa đơn).

### 9. Kho nhận (`warehouse`)

- Kiểu nhập: Chọn (select từ danh sách kho) trong bảng; hoặc SearchSelect trong popup chi tiết
- Mặc định: trống
- Bắt buộc: Có (`validate()` yêu cầu `warehouse` không trống cho mỗi dòng có `product_name`)
- Nguồn dữ liệu / liên kết: Bảng Kho (`warehouse`), API `/api/warehouses`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`

### 10. Ngày cần hàng (theo dòng) (`required_date`)

- Kiểu nhập: Chọn ngày (date input)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Trường cấp dòng, khác với `need_date` ở header phiếu (cấp phiếu toàn bộ, hiện chưa hiển thị trên form).

### 11. Nhân sự phụ trách dòng (`assignee`)

- Kiểu nhập: Chọn (SearchSelect, chỉ hiện cho người có `approve`); lưu Mã NV
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Danh sách nhân sự phòng thu mua (`employee.department` chứa "thu mua"), API `/api/employees`
- Người sửa: Người có `approve` (trực tiếp trong popup chi tiết dòng hoặc qua endpoint `PATCH /{pid}/assign`); tự động gán khi duyệt phiếu
- Logic đặc biệt: Lưu mã NV (`employee.code`), hiển thị tên (`employee.full_name`). NSTM chỉ thấy dòng mà `assignee` trùng với `emp_code` của mình (khi không có quyền `approve`/`read` dept+).

### 12. Trạng thái xử lý dòng (`line_status`)

- Kiểu nhập: Chọn (select từ danh sách cố định) — hiển thị ngay trên bảng hoặc trong popup chi tiết
- Mặc định: `Chưa đặt hàng`
- Bắt buộc: Không (có giá trị mặc định)
- Nguồn dữ liệu / liên kết: Danh sách cố định: `Chưa đặt hàng / Đã đặt hàng / Đã gửi ĐMH cho KT / Đã nhận hàng / Hoàn thành / Hủy đơn / Tạm ngưng`
- Người sửa: NSTM được giao dòng, hoặc người có `approve`/`cancel`; cập nhật trực tiếp trên bảng hoặc qua popup (endpoint `PATCH /{pid}/item-status`)
- Logic đặc biệt: Khi phiếu ở `approved`/`processing`/`completed`, thay đổi trạng thái dòng kích hoạt `recompute_status` tự điều chỉnh trạng thái phiếu. Dòng "Hủy đơn" tô đỏ toàn bộ hàng trong danh sách. Khi trả phiếu về Nháp, tất cả dòng reset về "Chưa đặt hàng".

### 13. Chi tiết tiến độ (`progress_note`)

- Kiểu nhập: Nhập nhiều dòng (textarea, trong popup chi tiết dòng)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSTM được giao dòng hoặc người có `approve`/`cancel`; cả khi phiếu đang ở các trạng thái không phải draft (qua endpoint `PATCH /{pid}/item-status`)

### 14. Ghi chú khác (`note`, cấp dòng)

- Kiểu nhập: Nhập nhiều dòng (textarea, trong popup chi tiết dòng)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write` (khi phiếu `draft`/`rejected`), hoặc NSTM / người có `approve`/`cancel` (qua endpoint `PATCH /{pid}/item-status`)

---

## C. Quy tắc nghiệp vụ

1. Lưu (Nháp): lọc bỏ dòng không có `product_name`; dòng còn lại được lưu toàn bộ (xóa dòng cũ và ghi lại — `_save_items` dùng `DELETE` rồi `INSERT`).
2. Gửi duyệt: kiểm tra `validate()` — phải có `company_id`, `requester`, ít nhất 1 dòng có `product_name`, mỗi dòng đó phải có `qty > 0` và `warehouse`. Nếu không pass, thông báo lỗi cụ thể.
3. Mã phiếu tự sinh: định dạng `PYC{ddmmyy}{seq:02d}`, trong đó `ddmmyy` lấy từ `request_date` (không có thì lấy ngày hiện tại), `seq` là số thứ tự tăng dần trong ngày.
4. Chọn Nhân sự YC: tự điền `requester_position` (chức vụ), `department` (phòng ban), `head_of_dept` (trưởng bộ phận tìm theo chức danh), `company_id`.
5. Chọn Mã hàng: tự điền `product_name`, `unit`, `item_group`, `group_desc`.
6. Chọn Phân loại: tự điền `group_desc` với thời gian sản xuất tiêu chuẩn từ `item_group.std_days` và `item_group.std_days_unavail`.
7. Thành tiền: tính ở FE (`qty × price`), lưu vào DB. PYC không tính VAT; tổng phiếu = tổng `amount` các dòng.
8. Phân quyền xem dòng: người tạo phiếu và người có `approve` hoặc scope `dept`/`company`/`all` xem được mọi dòng; NSTM (scope nhỏ hơn) chỉ thấy dòng có `assignee` trùng với mã NV của mình.
9. Tự phân công NSTM khi duyệt: hàm `auto_assign_by_category` gán NSTM cho từng dòng theo bảng phân công phụ trách (`category_assignee`).
10. Trạng thái phiếu tự tính lại: sau mỗi lần NSTM cập nhật `line_status`, hàm `recompute_status` xét lại trạng thái phiếu (chỉ khi phiếu đang ở `approved`/`processing`/`completed`).
11. Nhân bản phiếu: tạo phiếu `draft` mới, copy header và dòng hàng (không copy `assignee`, `line_status`, `progress_note`); mã mới được tự sinh.
12. Xóa mềm: phiếu xóa được đánh dấu `is_deleted = true`, không xóa vật lý; chỉ xóa được khi `status = draft`.
13. Thông báo: gửi khi gửi duyệt (`pr_submitted`), duyệt (`pr_approved`), và từ chối (`pr_rejected`). Thông báo gồm thông tin người tạo, mã phiếu, link, cờ gấp.
14. Đính kèm tài liệu: mỗi phiếu có thể đính kèm nhiều file (entity `purchase_request`); riêng báo giá NCC đề xuất dùng entity riêng `purchase_request_quote` (chỉ 1 file). Cả hai lưu trên Cloudflare R2 qua API `/api/attachments`.
15. Dòng "Hủy đơn": khi ít nhất 1 dòng có `line_status = "Hủy đơn"`, danh sách tô đỏ toàn bộ hàng đó (`rowStyle`, qua field `has_cancelled_line` trong response).

## D. Quyền thao tác (RBAC)

Entity: `purchase_request`

| Thao tác | Quyền yêu cầu | Điều kiện trạng thái |
|----------|---------------|----------------------|
| Xem danh sách | `purchase_request:read` | mọi trạng thái (theo phạm vi dữ liệu của grant) |
| Xem chi tiết phiếu | `purchase_request:read` | mọi trạng thái (theo phạm vi) |
| Xem chi tiết dòng | `purchase_request:read` + là người tạo / có `approve` / scope dept+ | xem tất cả dòng; NSTM chỉ thấy dòng được giao |
| Tạo mới / Nhân bản | `purchase_request:create` | — |
| Sửa nội dung header + dòng | `purchase_request:write` hoặc là người tạo phiếu | `draft`, `rejected` |
| Gửi duyệt | `purchase_request:write` hoặc là người tạo phiếu | `draft`, `rejected` |
| Duyệt | `purchase_request:approve` | `submitted` |
| Từ chối | `purchase_request:approve` | `submitted` |
| Phân bổ NSTM | `purchase_request:approve` | mọi trạng thái trừ `cancelled` |
| Cập nhật trạng thái / tiến độ dòng | `purchase_request:read` + là NSTM phụ trách hoặc có `approve`/`cancel` | mọi trạng thái sau duyệt |
| Hủy đơn | `purchase_request:cancel` | trạng thái khác `draft`, `submitted`, `cancelled`, `completed` |
| Trả phiếu về (Nháp) | `purchase_request:cancel` | trạng thái khác `draft`, `cancelled` |
| Hoàn thành | `purchase_request:cancel` | `approved`, `processing` |
| Xóa | `purchase_request:delete` | `draft` |
| In phiếu | `purchase_request:read` (hoặc `print` nếu cấu hình riêng) | mọi trạng thái |
