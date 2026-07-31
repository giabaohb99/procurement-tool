# Đơn mua hàng (PO)

## Mục đích

Ghi nhận quyết định mua hàng chính thức với một nhà cung cấp: bao gồm danh sách hàng hóa, số lượng, đơn giá, và lịch giao hàng nhiều lần. PO là trung tâm vòng đời mua hàng — khi nhận hàng, hệ thống tự động sinh phiếu nhập kho ngầm, cập nhật tồn kho, và tạo bút toán công nợ NCC (hàng hóa và cước vận chuyển).

Đường dẫn: `/purchase-orders` (danh sách), `/purchase-orders/:id` (chi tiết).

Bảng DB: `tab_purchase_order` (header), `tab_po_item` (dòng hàng), `tab_po_delivery` (lần giao).

## Vai trò tham gia

- NSPT / Người tạo đơn (`purchase_order:create`, `purchase_order:write`): tạo đơn, nhập thông tin header và dòng hàng, gửi duyệt, nhân bản, ghi nhận lần giao.
- TP/QL / Người duyệt (`purchase_order:approve`): duyệt đơn hoặc từ chối.
- Người hủy (`purchase_order:cancel`): hủy đơn khi đã duyệt hoặc đang giao.
- Người in (`purchase_order:print`): truy cập trang in A4.

## Vòng đời trạng thái

### Trạng thái đơn (`status`)

| Giá trị DB | Nhãn hiển thị | Ý nghĩa | Nút thao tác hiển thị |
|------------|---------------|---------|----------------------|
| `draft` | Nháp | Đang soạn hoặc vừa mở lại | Lưu, Gửi duyệt, Xóa, Nhân bản |
| `submitted` | Chờ duyệt | Đã gửi, đợi TP/QL duyệt | Duyệt, Trả về, Từ chối (TP/QL), Nhân bản |
| `approved` | Đã duyệt | TP/QL đã duyệt, cho phép nhập giao hàng | Thêm lần giao, Hủy đơn, Nhân bản |
| `partial` | Đã nhận một phần | Đã nhận một phần (tự động khi SL nhận > 0 và < SL đặt) | Hoàn thành, Hủy đơn, Nhân bản |
| `received` | Đã nhận đủ | Toàn bộ SL đã nhận | Hoàn thành, Hủy đơn, Nhân bản |
| `completed` | Hoàn thành | Đã đóng đơn (khóa sửa hoàn toàn) | Nhân bản |
| `rejected` | Bị trả lại | TP/QL trả về để người tạo sửa và gửi duyệt lại (không khóa sửa) | Lưu, Gửi duyệt, Xóa, Nhân bản |
| `cancelled` | Đã từ chối / Đã hủy | Bị từ chối hẳn (từ `submitted` qua nút Từ chối) hoặc bị hủy thủ công (từ `approved`/`partial`/`received` qua nút Hủy) — khóa sửa; badge hiển thị "Đã từ chối" | Nhân bản |

Luồng trạng thái chính: `draft` → `submitted` → `approved` → `partial` → `received` → `completed`. Ngoài ra từ `partial` cũng có thể chuyển thẳng sang `completed` (nút Hoàn thành khi muốn chốt đơn dù chưa nhận đủ).

Trạng thái `partial` và `received` được cập nhật tự động sau mỗi lần lưu khi đơn đang ở `approved/partial/received`. Đơn ở `completed` hoặc `cancelled` không cho phép sửa; dùng "Nhân bản" để tạo đơn Nháp mới.

Nút "Mở lại" (`reopen`) chuyển đơn từ `completed` về trạng thái theo tiến độ nhận thực tế: `received` (đã nhận đủ), `partial` (đã nhận một phần), hoặc `approved` (chưa nhận gì) — không hạ về `draft`. Endpoint: `POST /{id}/reopen`; chỉ áp dụng cho đơn `completed`, hiển thị nút trên trang chi tiết.

### Trạng thái dòng hàng (`line_status` — tự động)

| Giá trị | Ý nghĩa |
|---------|---------|
| `Chưa giao` | SL đã nhận = 0 |
| `Đang giao` | SL đã nhận > 0 và < SL đặt |
| `Đủ` | SL đã nhận >= SL đặt |

### Trạng thái lần giao (`PODelivery.status` — tự động)

| Giá trị | Ý nghĩa |
|---------|---------|
| `Chờ giao` | `received_qty` = 0 |
| `Lỗi` | `qc_result` = "Lỗi" |
| `Giao thiếu` | `received_qty` > 0 và < `ship_qty` (và QC không phải Lỗi) |
| `Đã nhận` | `received_qty` >= `ship_qty` |

---

## A. Thông tin chung (header đơn)

### 1. Mã PO (`code`)

- Kiểu nhập: Tự động
- Mặc định: Sinh tự động `PO{id:05d}` (ví dụ: `PO00045`) khi tạo mới; trống cho đến khi tạo
- Bắt buộc: — (hệ thống sinh, không sửa)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống (trường bị khóa)
- Logic đặc biệt: Hiển thị trong tiêu đề trang và bản in. Nếu truyền `code` khi tạo thì dùng giá trị đó thay vì tự sinh.

### 2. Mã đơn MISA (`misa_code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Bắt buộc khi Gửi duyệt và khi Duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Backend kiểm tra trường này trước khi chuyển sang trạng thái `submitted` hoặc `approved`; trả lỗi 400 nếu trống. Dùng làm số tham chiếu trên bản in. Khi có carrier và cước vận chuyển, hệ thống tạm sinh số HĐ vận chuyển theo công thức `{misa_code}-{product_code}`.

### 3. Mã PYC nguồn (`pr_code`)

- Kiểu nhập: Nhập tay với gợi ý (datalist) hoặc nhập trực tiếp mã PYC
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Danh sách Yêu cầu mua hàng (`/api/purchase-requests`)
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Khi chọn mã PYC từ gợi ý, tự điền `department`, `nspt`, `company_id` từ PYC tương ứng (nếu còn trống).

### 4. Mã phiếu khảo sát (`survey_code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Phiếu khảo sát giá (`survey`)
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Tham chiếu truy vết; không kéo dữ liệu tự động từ phiếu khảo sát.

### 5. Công ty nhận hóa đơn (`company_id`)

- Kiểu nhập: Chọn (ô tìm kiếm SearchSelect)
- Mặc định: 0 (trống)
- Bắt buộc: Không bắt buộc khi Nháp; nên điền để sinh tự động phiếu nhập kho và công nợ đúng pháp nhân
- Nguồn dữ liệu / liên kết: Bảng Công ty (`/api/companies`), tối đa 200 bản ghi
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: `company_id` được truyền vào toàn bộ các side-effect (phiếu nhập kho ngầm `goods_receipt`, tồn kho `inventory`, công nợ `payable`). Thông tin công ty (tên, địa chỉ, MST, email HĐ) hiển thị trên bản in.

### 6. Nhà cung cấp bán hàng (`supplier_code`)

- Kiểu nhập: Chọn (ô tìm kiếm SearchSelect), hiển thị "mã — tên"
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp; cần điền để tính công nợ NCC chính xác
- Nguồn dữ liệu / liên kết: Bảng NCC (`/api/suppliers`) — chỉ hiện NCC có `supplier_type != 'transport'`
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Khi chọn NCC, tự điền `supplier_name`, `vat_rate` (lấy từ `supplier.vat`), `payment_terms` (lấy từ `supplier.payment_terms`). NCC loại `'transport'` không được chọn ở đây; chỉ dùng làm carrier trong lần giao.

### 7. Tên nhà cung cấp (`supplier_name`)

- Kiểu nhập: Nhập tay (tự điền khi chọn NCC)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ `supplier.name`; có thể sửa thủ công
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Trường lưu snapshot tên NCC tại thời điểm tạo đơn; dùng trong công nợ và bản in.

### 8. Bộ phận (`department`)

- Kiểu nhập: Nhập tay
- Mặc định: trống (tự điền từ PYC nếu chọn)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ PYC (`purchase_request.department`) khi chọn `pr_code`
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa

### 9. NSPT phụ trách (`nspt`)

- Kiểu nhập: Chọn từ danh sách nhân sự (SearchSelect); điền tự động khi tạo đơn
- Mặc định: Tự sinh khi tạo — (a) nếu tạo từ YCMH (`pr_code`): lấy tên đầy đủ người phụ trách dòng (`assignee.full_name`) trong YCMH, ưu tiên dòng khớp sản phẩm với đơn; (b) nếu tạo trực tiếp (không qua YCMH): lấy tên đầy đủ của người tạo đơn (`Employee.full_name`). Nếu payload đã truyền `nspt` thì giữ giá trị đó, không tự sinh. Khi tạo từ YCMH qua nút "Tạo đơn mua hàng", giá trị này được điền sẵn trên form trước khi người dùng bấm lưu.
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`/api/employees`); giá trị lưu theo tên đầy đủ (`full_name`)
- Người sửa: Chỉ người có quyền `purchase_order:approve`; các vai trò khác thấy trường ở chế độ chỉ đọc (disable)
- Logic đặc biệt: Hiển thị trên bản in Đơn mua hàng (MH) như "Nhân viên mua hàng". Dùng làm tiêu chí lọc phạm vi dữ liệu (scoping): người dùng với scope `assigned`/`proc` thấy đơn mình tạo (`created_by = user.id`) VÀ đơn có `nspt` khớp tên đầy đủ của mình (`emp_name`); scope `proc` ngoài ra còn thấy mọi đơn ở trạng thái `approved`.

### 10. Ngày đặt hàng (`order_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: Ngày hiện tại (hôm nay) — khởi tạo từ `new Date().toISOString().slice(0,10)`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Dùng làm ngày gốc tính `regulated_date` trong từng lần giao: `order_date + std_days`.

### 11. Tỷ lệ VAT chung (`vat_rate`)

- Kiểu nhập: Tự điền (theo NCC); có thể sửa
- Mặc định: 0.08 (8%)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ `supplier.vat` khi chọn NCC
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Trường lưu ở DB dạng thập phân (`Numeric(5,4)`); hiển thị và truyền dạng số thực (ví dụ 0.08 = 8%). Mỗi dòng hàng có trường `vat` riêng (% nguyên); trường này là giá trị mặc định tham khảo.

### 12. Hình thức thanh toán NCC (`payment_terms`)

- Kiểu nhập: Nhập tay (tự điền khi chọn NCC)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ `supplier.payment_terms`; có thể sửa thủ công
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Hệ thống trích xuất số ngày công nợ bằng regex `(\d+)\s*ngày` để tính `due_days` trong bảng công nợ (`payable`). Hiển thị trên bản in Đơn mua hàng (MH) như "Điều khoản thanh toán" và "Số ngày được nợ".

### 13. Đơn gấp (`is_urgent`)

- Kiểu nhập: Checkbox
- Mặc định: Không tích
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Khi tích, thông báo gửi duyệt được đánh dấu `is_urgent=true`, kích hoạt kênh thông báo ưu tiên.

### 14. Ghi chú (`note`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Hiển thị trên bản in Đơn mua hàng (MH) như "Diễn giải".

### 15. Trạng thái đơn (`status`)

- Kiểu nhập: Tự động / thao tác nút
- Mặc định: `draft` khi tạo mới
- Bắt buộc: — (hệ thống quản lý)
- Nguồn dữ liệu / liên kết: Giá trị cố định: `draft` / `submitted` / `approved` / `partial` / `received` / `completed` / `rejected` / `cancelled`
- Người sửa: Hệ thống (qua các endpoint chuyên biệt: `/submit`, `/approve`, `/reject`, `/cancel`, `/complete`, `/reopen`)
- Logic đặc biệt: Xem bảng Vòng đời trạng thái. Trạng thái `partial`/`received` được tính lại tự động sau mỗi lần lưu khi đơn đang ở `approved/partial/received`. Không hạ cấp từ `approved` xuống `draft` khi lưu lần giao.

### 16. Ghi chú duyệt / lý do từ chối (`approve_note`)

- Kiểu nhập: Chỉ đọc (hệ thống ghi khi từ chối hoặc hủy đơn)
- Mặc định: trống
- Bắt buộc: — (không nhập thủ công)
- Nguồn dữ liệu / liên kết: Nội dung lý do từ `/reject` hoặc `/cancel` (`RejectIn.reason`)
- Người sửa: Hệ thống (ghi tự động từ payload khi từ chối/hủy)
- Logic đặc biệt: Hiển thị dưới dạng thẻ cảnh báo riêng trên trang chi tiết.

### 17. Trạng thái hồ sơ chứng từ (`document_status`)

- Kiểu nhập: Chọn thủ công từ danh sách cố định (qua endpoint riêng `PATCH /{id}/document-status`)
- Mặc định: `"chưa có chứng từ"` khi tạo mới
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: 3 giá trị cố định: `"chưa có chứng từ"` / `"đã có thông tin chứng từ"` / `"đã đủ chứng từ"`
- Người sửa: Người có quyền `purchase_order:write`; cho phép cập nhật kể cả khi đơn đã `completed` (chứng từ có thể bổ sung sau)
- Logic đặc biệt: Phản ánh tình trạng hồ sơ chứng từ vật lý (hóa đơn, phiếu giao nhận...) — không liên kết với luồng tiến độ `progress_status` của dòng hàng. Hiển thị trên màn hình Tiến độ mua hàng (`/purchase-progress`) dưới dạng cột "Hồ sơ CT". Endpoint riêng `PATCH /{id}/document-status`, body `{document_status}`.

---

## B. Dòng hàng (`tab_po_item`)

Mỗi dòng = một sản phẩm/hàng hóa trong đơn. Bảng tóm tắt hiển thị các cột chính; toàn bộ trường xem và sửa trong popup "Chi tiết dòng". Frontend chỉ lưu dòng có `product_name` hoặc `product_code` không trống.

### 1. Mã hàng VTBB/NL (`product_code`)

- Kiểu nhập: Chọn sản phẩm qua ProductPicker (tìm theo mã hoặc tên)
- Mặc định: trống
- Bắt buộc: Không (trường xác định dòng là `product_name`)
- Nguồn dữ liệu / liên kết: Danh mục Sản phẩm (`product`)
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa `completed`/`cancelled`
- Logic đặc biệt: Chọn sản phẩm tự điền `product_name`, `invoice_name`, `unit`, `item_group`, `fg_code`, `fg_name`. Dùng làm tham chiếu trong phiếu nhập kho ngầm và tồn kho.

### 2. Tên hàng (`product_name`)

- Kiểu nhập: Nhập tay (tự điền khi chọn SP) hoặc nhập trực tiếp
- Mặc định: trống
- Bắt buộc: Đây là trường xác định dòng — dòng không có `product_name` và `product_code` sẽ bị loại khi lưu
- Nguồn dữ liệu / liên kết: Tự điền từ `product.name`; có thể sửa thủ công
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa

### 3. Tên trên hóa đơn (`invoice_name`)

- Kiểu nhập: Nhập tay (tự điền từ `product.invoice_name` hoặc `product.name`)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ sản phẩm khi chọn
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Hiển thị trên cả hai bản in (cột "Tên trên HĐ" / "Tên hàng xuất hóa đơn").

### 4. Phân loại (`item_group`)

- Kiểu nhập: Nhập tay (tự điền khi chọn SP)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ `product.item_group`; liên kết bảng `ItemGroup`
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Hệ thống dùng `item_group` để tra `std_days` (số ngày quy định giao hàng) từ bảng `ItemGroup` khi tính lại lần giao.

### 5. Xuất xứ / TSKT / chất liệu (`spec`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Hiển thị trên bản in Đơn đặt hàng (cột "Xuất xứ/TSKT/chất liệu").

### 6. Mã HH / thành phẩm (`fg_code`)

- Kiểu nhập: Nhập tay (tự điền từ `product.hh_code` khi chọn SP)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ sản phẩm
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Gắn mã thành phẩm để truy vết nguồn gốc nguyên liệu.

### 7. Tên HH / thành phẩm (`fg_name`)

- Kiểu nhập: Nhập tay (tự điền từ `product.hh_name`)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ sản phẩm
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa

### 8. Số hóa đơn theo sản phẩm (`invoice_no`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Dùng làm `invoice_no` khi hệ thống sinh công nợ hàng (`payable` loại `goods`) cho các lần giao của dòng này. Khi người dùng nhập `invoice_no` mà `invoice_date` còn trống, hệ thống tự đặt `invoice_date` = ngày hôm nay.

### 8b. Ngày hóa đơn (`invoice_date`)

- Kiểu nhập: Chọn ngày; hoặc tự đặt ngày hôm nay khi nhập `invoice_no` lần đầu (sửa tay được)
- Mặc định: trống; tự điền khi `invoice_no` có giá trị và `invoice_date` còn trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Nếu payload đã gửi `invoice_date` không trống, giá trị đó được giữ nguyên (không bị ghi đè). Trả về trong response `_item()` dưới key `invoice_date`.

### 8c. Ngày giao chứng từ cho KT (`document_delivery_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không (nhưng là điều kiện bắt buộc để dòng tự động tiến sang bước "Đã gửi ĐMH cho KT")
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Khi trường này có giá trị, hệ thống tự động nâng `progress_status` của dòng từ "Chưa gửi ĐMH cho KT" lên "Đã gửi ĐMH cho KT" (bước 4 trong máy trạng thái tiến độ). Xem mục H để biết chi tiết cơ chế. Trả về trong response `_item()` dưới key `document_delivery_date`.

### 9. NCC có sẵn hàng (`supplier_ready`)

- Kiểu nhập: Checkbox
- Mặc định: Không tích
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Ảnh hưởng đến `std_days` tra bảng `ItemGroup`: nếu tích → tra `group.std_days` (NCC có sẵn); nếu không tích → tra `group.std_days_unavail` (không sẵn hàng).

### 10. Ngày yêu cầu có hàng (`required_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Dùng tính `diff_required` trong lần giao: `regulated_date − required_date`. Giá trị âm = ngày quy định trễ hơn KD yêu cầu.

### 11. Đơn vị tính (`unit`)

- Kiểu nhập: Chọn từ danh sách (select, tự điền khi chọn SP)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng ĐVT (`/api/units`)
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Dùng trong phiếu nhập kho ngầm và tồn kho khi nhận hàng.

### 12. Số lượng yêu cầu (`qty_request`)

- Kiểu nhập: Nhập số
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: SL yêu cầu từ phía nội bộ (KD/sản xuất); hiển thị trên bản in Đơn mua hàng (MH) cột "SL yêu cầu".

### 13. Số lượng đặt NCC (`qty_order`)

- Kiểu nhập: Nhập số
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: SL thực đặt NCC; dùng tính giá trị đặt hàng (`order_subtotal`, `order_total`) và `qty_remaining`. Hiển thị trên bản in Đơn đặt hàng (A4 ngang).

### 14. Đơn giá (`price`)

- Kiểu nhập: Nhập số (VNĐ) — hiển thị dạng số có phân cách (CurrencyInput)
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Dùng tính `amount` (SL thực nhận × đơn giá × (1+VAT/100)) và công nợ hàng (`payable.amount = received_qty × price`).

### 15. VAT % của dòng (`vat`)

- Kiểu nhập: Nhập số (%)
- Mặc định: 8 (khởi tạo từ frontend `emptyItem`)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Dùng tính `amount` và tiền thuế VAT trong công nợ (`vat = amount × vat / 100`). Mỗi dòng có VAT riêng; `vat_rate` header chỉ là mặc định tham khảo.

### 16. Thành tiền dòng (`amount`)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính, không sửa)
- Nguồn dữ liệu / liên kết: `qty_received × price × (1 + vat/100)` — theo SL thực nhận
- Người sửa: Hệ thống (tính lại trong `recompute_effects` sau mỗi lần lưu)
- Logic đặc biệt: Đây là thành tiền đã chốt (theo SL nhận). Phân biệt với `order_total` (theo SL đặt) dùng cho bản in Đơn đặt hàng gửi NCC.

### 17. Số lượng đã nhận (`qty_received`)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính)
- Nguồn dữ liệu / liên kết: Tổng `Σ delivery.received_qty` của dòng
- Người sửa: Hệ thống (cập nhật trong `recompute_effects`)
- Logic đặc biệt: Hiển thị trên bảng tóm tắt dạng `đã nhận/SL đặt` và trong bản in MH cột "SL thực nhập".

### 18. Số lượng còn lại (`qty_remaining`)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính)
- Nguồn dữ liệu / liên kết: `qty_order − qty_received`
- Người sửa: Hệ thống (cập nhật trong `recompute_effects`)

### 19. Trạng thái dòng (`line_status`)

- Kiểu nhập: Tự động
- Mặc định: trống
- Bắt buộc: — (hệ thống ghi)
- Nguồn dữ liệu / liên kết: Xem bảng Trạng thái dòng hàng ở phần Vòng đời
- Người sửa: Hệ thống (cập nhật trong `recompute_effects`)

### 20. Kho nhận mặc định (`warehouse_code`)

- Kiểu nhập: Chọn (SearchSelect), hiển thị "mã — tên"
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Kho (`/api/warehouses`)
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Là kho mặc định cho mỗi lần giao mới thêm vào dòng. Lần giao cụ thể có thể ghi đè bằng `delivery.warehouse_code`. Khi in, hệ thống tra tên kho theo `wh_names` map.

### 21. Ghi chú dòng (`note`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Hiển thị trên cả hai bản in cột "Ghi chú".

### 22. Tiến độ đặt hàng dòng (`progress_status`)

- Kiểu nhập: Tự động (hệ thống nâng khi đủ điều kiện); thao tác tay chỉ qua endpoint riêng `POST /api/purchase-orders/{pid}/items/{item_id}/progress`
- Mặc định: `"Chưa đặt hàng"` (gán khi tạo dòng mới)
- Bắt buộc: — (hệ thống/nghiệp vụ quản lý)
- Nguồn dữ liệu / liên kết: Giá trị chuỗi theo máy trạng thái — xem mục H
- Người sửa: Hệ thống (tự động); người dùng có quyền `purchase_order:write` chỉ đặt được "Tạm ngưng" / "Hủy đơn" / "Tiếp tục" qua endpoint riêng
- Logic đặc biệt: Máy trạng thái tiến độ riêng của dòng hàng — **khác hoàn toàn với `status` của phiếu PO**. Sau mỗi lần lưu đơn (`PATCH`), backend gọi `apply_auto_progress` để tự động nâng dòng lên bước cao nhất thỏa điều kiện cộng dồn (forward-only, không hạ ngược). Trả về trong response `_item()` dưới key `progress_status`. Khi dòng bị tạm ngưng / hủy: `progress_status` trước đó được snapshot vào `status_before_pause` để phục hồi sau, lý do ghi vào `pause_reason`. Xem mục H để biết đầy đủ máy trạng thái, điều kiện từng bước, và cơ chế liên kết ngược về YCMH.

### 23. Ngày KT xác nhận thanh toán (`pay_confirm_date`)

- Kiểu nhập: Nhập tay (Kế toán điền) qua endpoint chuyên biệt
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Kế toán (qua endpoint riêng)
- Logic đặc biệt: Ngày Kế toán xác nhận đã thanh toán cho dòng hàng cụ thể. Lưu dạng `"YYYY-MM-DD"` (String(10)). **Trạng thái hiện tại**: tồn tại trong DB và model; chưa được đưa vào schema API và chưa trả về trong response dòng hàng thông thường.

### 24. Lý do hủy / tạm ngưng dòng (`pause_reason`)

- Kiểu nhập: Nhập tay qua endpoint tiến độ dòng (`POST /api/purchase-orders/{pid}/items/{item_id}/progress`, body `{status: "Tạm ngưng"/"Hủy đơn", reason}`)
- Mặc định: trống
- Bắt buộc: Bắt buộc nhập khi chuyển dòng sang "Tạm ngưng" hoặc "Hủy đơn"
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` qua endpoint riêng
- Logic đặc biệt: Ghi lý do khi dòng bị tạm ngưng hoặc hủy (tối đa 500 ký tự). Kết hợp với `status_before_pause` để hỗ trợ khôi phục tiến độ khi mở lại dòng. Trả về trong response `_item()` dưới key `pause_reason`; hiển thị chú thích dưới badge trạng thái khi dòng ở "Tạm ngưng" hoặc "Hủy đơn".

### 25. Trạng thái tiến độ trước khi tạm ngưng (`status_before_pause`)

- Kiểu nhập: Tự động (hệ thống ghi khi dòng chuyển sang "Tạm ngưng")
- Mặc định: trống
- Bắt buộc: — (hệ thống ghi)
- Nguồn dữ liệu / liên kết: Giá trị `progress_status` tại thời điểm tạm ngưng
- Người sửa: Hệ thống (ghi tự động khi tạm ngưng dòng); bị xóa khi dòng phục hồi (Tiếp tục)
- Logic đặc biệt: Snapshot `progress_status` của dòng trước khi tạm ngưng. Khi gọi endpoint với `status = "__resume__"` (Tiếp tục), hệ thống khôi phục `progress_status = status_before_pause` và xóa `status_before_pause`. Dùng để `sync_from_purchase_orders` biết mức tiến độ thực của dòng đang tạm ngưng (không về "Chưa đặt hàng"). Trả về trong response `_item()` dưới key `status_before_pause`.

### 26. Giá trị đặt hàng theo dòng (`order_total` — tính phía server)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính, không lưu DB)
- Nguồn dữ liệu / liên kết: `qty_order × price × (1 + vat/100)` — theo SL đặt
- Người sửa: Hệ thống (tính trong `_item()` mỗi lần trả response)
- Logic đặc biệt: Hiển thị cột "Thành tiền đơn hàng" trên bảng dòng hàng UI; dùng bật nút Tạo yêu cầu thanh toán khi có công nợ còn lại.

### 27. Tiền hàng đã phát sinh công nợ theo dòng (`goods_total` — tính phía server)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính)
- Nguồn dữ liệu / liên kết: Tổng `payable.total` của các khoản công nợ hàng (`source_type='goods'`) thuộc các lần giao của dòng
- Người sửa: Hệ thống
- Logic đặc biệt: Phản ánh tiền hàng theo SL thực nhận đã tạo công nợ. Hiển thị trong popup chi tiết dòng.

### 28. Đã trả theo dòng (`paid_total` — tính phía server)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính)
- Nguồn dữ liệu / liên kết: Tổng `payable.paid_amount` của các khoản nợ hàng thuộc dòng
- Người sửa: Hệ thống (tăng lên khi YCTT ghi nhận đã chi)
- Logic đặc biệt: Hiển thị cột "Đã trả" trong popup chi tiết dòng.

### 29. Còn lại chưa trả theo dòng (`remaining_total` — tính phía server)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính)
- Nguồn dữ liệu / liên kết: Tổng `payable.remaining` của các khoản nợ hàng thuộc dòng
- Người sửa: Hệ thống
- Logic đặc biệt: `remaining_total > 0` khi còn nợ chưa trả; tổng `remaining_total` của tất cả dòng (cộng thêm công nợ vận chuyển) tạo thành `unpaid_total` trên header đơn — khi `unpaid_total > 0` mới bật nút Tạo yêu cầu thanh toán.

---

## C. Lần giao hàng (`tab_po_delivery`) — popup chi tiết dòng

Mỗi dòng hàng có thể được giao nhiều lần. Popup "Chi tiết dòng" hiển thị bảng lần giao. Chỉ thêm/sửa lần giao khi đơn ở trạng thái `approved`, `partial`, hoặc `received` và người dùng có quyền `purchase_order:write`.

Mỗi lần lưu đơn khi đơn đang giao, hệ thống gọi `recompute_effects` để sinh hoặc cập nhật các bản ghi ngầm: phiếu nhập kho (`goods_receipt`), tồn kho (`inventory`), công nợ hàng và công nợ vận chuyển (`payable`). Nếu `received_qty = 0`, các side-effect của lần giao đó bị xóa (`_cleanup_delivery`).

### 1. Số thứ tự lần giao (`delivery_no`)

- Kiểu nhập: Nhập số
- Mặc định: 1 (tăng dần theo số lần giao hiện có của dòng)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao

### 2. Kho nhận (`warehouse_code`)

- Kiểu nhập: Chọn (select)
- Mặc định: Kế thừa từ `item.warehouse_code` khi thêm lần giao mới
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Kho (`/api/warehouses`)
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Ghi đè kho mặc định của dòng. Nếu cả dòng và lần giao đều có kho, ưu tiên `delivery.warehouse_code` khi sinh phiếu nhập kho ngầm.

### 3. Đơn vị vận chuyển (`carrier_code`)

- Kiểu nhập: Chọn (select)
- Mặc định: trống. Trường này có **3 trạng thái giao diện**: (1) **Chưa chọn** — `carrier_code=''` và `carrier_name` trống; (2) **NCC tự vận chuyển** — chọn option "_NCC tự vận chuyển_", lưu `carrier_code=''` + `carrier_name='NCC tự vận chuyển'`; (3) **Đơn vị vận chuyển thật** — chọn NCC loại `transport`, lưu `carrier_code=mã` + `carrier_name` tự điền từ NCC.
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng NCC (`/api/suppliers`) — chỉ NCC có `supplier_type = 'transport'`
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Khi chọn carrier thật, tự điền `carrier_name`. Khi có `carrier_code` khác rỗng và `shipping_amount > 0`, hệ thống tạo công nợ vận chuyển riêng (`payable` loại `shipping`) với số ngày nợ của carrier. Trạng thái "NCC tự vận chuyển" không tạo công nợ carrier riêng (carrier_code trống).

### 4. Tên đơn vị vận chuyển (`carrier_name`)

- Kiểu nhập: Tự điền khi chọn carrier; nếu không chọn carrier = "NCC tự vận chuyển"
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ `supplier.name`
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao

### 5. Số lượng gửi (`ship_qty`)

- Kiểu nhập: Nhập số
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Dùng tính `diff_promise`/trạng thái giao: nếu `received_qty < ship_qty` → "Giao thiếu". Cũng dùng tính cước khi nhập `shipping_unit_price`: `shipping_amount = shipping_unit_price × ship_qty`.

### 6. Đơn vị tính vận chuyển (`ship_unit`)

- Kiểu nhập: Chọn (select): Kiện / Chuyến / m2 / tấn
- Mặc định: Kế thừa từ `item.unit` khi thêm lần giao
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Danh sách cố định: Kiện / Chuyến / m2 / tấn
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao

### 7. Số lượng thực nhận (`received_qty`)

- Kiểu nhập: Nhập số
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Đây là trường chủ chốt kích hoạt toàn bộ side-effect. Khi `received_qty > 0`, hệ thống sinh phiếu nhập kho ngầm (`goods_receipt`), cập nhật tồn kho (`inventory`), tạo công nợ hàng (`payable`). Khi `received_qty = 0`, các side-effect bị xóa.

### 8. Ngày NCC cam kết giao (`promised_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Dùng tính `diff_promise = promised_date − received_date`. Giá trị âm = NCC giao trễ so với cam kết.

### 9. Ngày dự kiến nhận (`expected_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Lưu trong DB và truyền trong payload; hiện tại không hiển thị thành cột riêng trong bảng giao hàng UI.

### 10. Ngày nhận thực tế (`received_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không (nhưng cần điền để tính chênh lệch và sinh công nợ có ngày phát sinh)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Dùng làm `incur_date` trong công nợ (`payable`). Dùng tính `diff_promise` và `diff_regulated`. Khi `received_date` trống, các cột chênh lệch hiển thị "—".

### 11. Số ngày quy định (`std_days`)

- Kiểu nhập: Nhập số (có thể ghi đè)
- Mặc định: 0; tính lại tự động theo `ItemGroup.std_days` (hoặc `std_days_unavail`) và `supplier_ready`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng `ItemGroup` (tra theo `item.item_group`)
- Người sửa: Người có quyền `purchase_order:write`; hệ thống ghi đè tự động nếu `ItemGroup` có giá trị
- Logic đặc biệt: Ưu tiên giá trị từ `ItemGroup`; nếu nhóm không có cấu hình thì giữ giá trị nhập thủ công. Công thức: nếu `supplier_ready=true` thì tra `group.std_days`; ngược lại tra `group.std_days_unavail` (hoặc `group.std_days` nếu `std_days_unavail` trống).

### 12. Ngày quy định (`regulated_date`)

- Kiểu nhập: Tự tính
- Mặc định: trống
- Bắt buộc: — (hệ thống tính)
- Nguồn dữ liệu / liên kết: `order_date + std_days` (ngày đặt hàng cộng số ngày quy định)
- Người sửa: Hệ thống (hiển thị chỉ đọc)
- Logic đặc biệt: Nếu `order_date` hoặc `std_days` trống/0, hiển thị "—".

### 13. Chênh lệch cam kết − ngày nhận (`diff_promise`)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính)
- Nguồn dữ liệu / liên kết: `promised_date − received_date` (số ngày)
- Người sửa: Hệ thống
- Logic đặc biệt: Giá trị âm = giao trễ so với cam kết. Hiển thị màu đỏ đậm khi âm.

### 14. Chênh lệch quy định − ngày nhận (`diff_regulated`)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính)
- Nguồn dữ liệu / liên kết: `regulated_date − received_date` (số ngày)
- Người sửa: Hệ thống
- Logic đặc biệt: Giá trị âm = giao trễ so với ngày quy định. Hiển thị màu đỏ đậm khi âm.

### 15. Chênh lệch quy định − KD yêu cầu (`diff_required`)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính)
- Nguồn dữ liệu / liên kết: `regulated_date − item.required_date` (số ngày)
- Người sửa: Hệ thống
- Logic đặc biệt: Giá trị âm = ngày quy định muộn hơn yêu cầu của KD. Hiển thị "—" khi `required_date` trống.

### 16. Số hóa đơn lần giao (`invoice_no`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Trường này ghi ở cấp lần giao; phân biệt với `po_item.invoice_no` (cấp sản phẩm, dùng cho công nợ hàng). Không ghi đè `po_item.invoice_no` khi ghi nhận công nợ.

### 17. Đơn giá vận chuyển (`shipping_unit_price`)

- Kiểu nhập: Nhập số (VNĐ) — CurrencyInput
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Khi nhập đơn giá VC, tự tính `shipping_amount = shipping_unit_price × ship_qty`.

### 18. Thành tiền vận chuyển (`shipping_amount`)

- Kiểu nhập: Nhập số (VNĐ) — CurrencyInput; hoặc tự tính từ đơn giá × SL gửi
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Có thể nhập tay (ghi đè kết quả tính tự động). Dùng tạo công nợ vận chuyển riêng khi `carrier_code` có giá trị và `shipping_amount > 0`.

### 19. Kết quả QC (`qc_result`)

- Kiểu nhập: Chọn (select)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Danh sách cố định: (trống) / Đạt / Thiếu / Lỗi
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Khi chọn "Lỗi", trạng thái lần giao tự động chuyển thành "Lỗi". Dùng trong phiếu nhập kho ngầm (`gr_service.upsert_for_delivery`).

### 20. Trạng thái lần giao (`status`)

- Kiểu nhập: Tự động
- Mặc định: trống
- Bắt buộc: — (hệ thống ghi)
- Nguồn dữ liệu / liên kết: Xem bảng Trạng thái lần giao ở phần Vòng đời
- Người sửa: Hệ thống (tính trong `recompute_effects`)
- Logic đặc biệt: Hiển thị badge có màu: "Đã nhận" (xanh), "Lỗi" (đỏ), "Giao thiếu"/"Chờ giao" (vàng).

### 21. Yêu cầu khác (`extra_request`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao

### 22. Chi tiết tiến độ / phiếu giao (`progress_note`)

- Kiểu nhập: Nhập tay; trường lưu trong DB và truyền trong payload
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Trường lưu trữ nhưng hiện tại không hiển thị thành cột riêng trong bảng UI; dữ liệu được gửi và lưu trong `recompute_effects`.

---

## D. Chứng từ đính kèm

Hai cấp đính kèm riêng biệt:

1. Đính kèm cấp đơn: entity `purchase_order`, `entity_id = po.id`. Người dùng có `purchase_order:write` tải lên từ phần "Chứng từ đính kèm" (báo giá, HĐ...).
2. Đính kèm cấp lần giao: entity `delivery`, `entity_id = delivery.id`. Chỉ khả dụng sau khi lần giao đã được lưu (có `id`); người dùng có `purchase_order:write` tải lên trong bảng giao hàng.

File lưu trên Cloudflare R2.

---

## E. Chức năng in (2 mẫu A4)

Cả hai mẫu gọi cùng endpoint `GET /api/purchase-orders/{id}/print` (yêu cầu quyền `purchase_order:print`). Endpoint bổ sung thêm thông tin công ty, NCC, kho nhận, và `wh_names` map vào dữ liệu trả về.

| Mẫu | File | Trang in | Nội dung chính | Tổng tiền hiển thị |
|-----|------|----------|----------------|-------------------|
| Đơn đặt hàng (gửi NCC) | `PrintPurchaseOrder.tsx` | A4 ngang (landscape) | Bảng hàng theo SL đặt, đơn giá chưa/đã VAT, kho nhận, tên trên HĐ; điều khoản giao nhận + thông tin HĐ | `order_total` (theo SL đặt) |
| Đơn mua hàng (nội bộ) | `PrintPurchaseOrderMH.tsx` | A4 dọc (portrait) | Bảng hàng theo SL yêu cầu + SL thực nhập, tiền thuế GTGT riêng; số tiền bằng chữ; điều khoản NCC | `order_total` (theo SL đặt) + `order_subtotal` tách thuế riêng |

Ngoài 2 mẫu trên, phiếu liên quan là **Phiếu đề xuất mua hàng hóa/dịch vụ** (Mẫu 003/BM/PKT, file `PrintPurchaseRequest.tsx`) — là bản in của phiếu YCMH nguồn, mở từ trang chi tiết YCMH (không phải từ trang PO). Bảng hàng hóa trên phiếu đề xuất đã có cột **Nơi giao** hiển thị mã kho nhận (`warehouse_code`) thay vì tên đầy đủ kho (dùng hàm `whCode` tra ngược từ danh mục kho).

---

## F. Quy tắc nghiệp vụ

1. Lưu đơn: dòng hàng không có `product_name` và `product_code` bị loại bỏ trước khi gửi lên BE. Mỗi lần lưu gọi `recompute_effects` để tính lại toàn bộ số liệu và side-effect.
2. Gửi duyệt: bắt buộc điền `misa_code` (kiểm tra ở cả FE và BE); không kiểm tra trường dòng hàng.
3. Duyệt đơn: bắt buộc `misa_code` không trống (kiểm tra ở BE).
4. Từ chối / Hủy: yêu cầu nhập lý do (`reason`); lý do lưu vào `approve_note`.
5. Khóa sửa: đơn `completed` hoặc `cancelled` trả lỗi 400 khi `PATCH`; chỉ cho phép Nhân bản.
6. Nhân bản: tạo đơn Nháp mới từ đơn gốc; giữ dòng hàng nhưng xóa toàn bộ lần giao, số đã nhận, và trạng thái dòng; reset `code`, `misa_code`, `status`, `invoice_no`, `invoice_date` (chứng từ riêng từng đơn, phải nhập lại ở bản sao). `progress_status` của mọi dòng được reset về `"Chưa đặt hàng"`.
7. Xóa đơn: BE xóa theo thứ tự deliveries → side-effect → items → attachments → header. Chỉ cho phép khi đơn ở `draft` hoặc `rejected`; BE trả 400 nếu đơn ở trạng thái khác (không chỉ FE kiểm tra).
8. Tổng tiền trên header: `subtotal` = SL nhận × đơn giá; `vat` = tiền thuế từ thực nhận; `total` = subtotal + vat; `order_subtotal`/`order_total` = theo SL đặt (dùng cho bản in).
9. Công nợ hàng: sinh khi `received_qty > 0`; xóa khi `received_qty` về 0. Không có VAT riêng ở cấp đơn vị giao — VAT tính từ `po_item.vat`.
10. Công nợ vận chuyển: sinh khi carrier được chọn VÀ `shipping_amount > 0`; xóa khi carrier xóa hoặc `shipping_amount = 0`.
11. Tạo yêu cầu thanh toán từ đơn: khi đơn ở `approved`/`partial`/`received`/`completed` và tổng công nợ còn lại (`unpaid_total`) > 0, người dùng có quyền `payment_request:create` thấy nút "Tạo yêu cầu thanh toán". Popup hiện 2 tab: **NCC sản xuất** (hàng hóa, `source_type='goods'`) và **NCC vận chuyển** (`source_type='shipping'`). Mặc định chọn sẵn (tick) toàn bộ khoản nợ hàng hóa; khoản nợ vận chuyển người dùng tự chọn thêm. Gửi lên `POST /api/payment-requests`.

12. Khóa dòng hoàn thành: dòng hàng có `progress_status = 'Hoàn thành'` hoặc `'Hủy đơn'` bị khóa hoàn toàn — không sửa thông tin sản phẩm, không thêm/sửa/xóa lần giao trong popup chi tiết dòng. Backend bỏ qua (skip) dòng bị khóa khi lưu đơn (không cho phép sửa kể cả qua API).

13. Phạm vi xem đơn theo NSPT: người dùng với scope `assigned` hoặc `proc` thấy đơn mình tạo (`created_by = user.id`) VÀ đơn có `nspt` khớp tên đầy đủ của mình (`emp_name`). Riêng scope `proc` còn thấy thêm mọi đơn đang ở trạng thái `approved` (để nhặt việc phân bổ).

14. Lọc danh sách: hỗ trợ các bộ lọc sau:
    - LIKE trên header PO: `code`, `status`, `supplier_code`, `pr_code`, `misa_code`, `nspt`, `is_urgent`, `department`, `document_status`
    - Exact match: `company_id`
    - Khoảng ngày: `order_date` (từ–đến)
    - Lọc qua dòng hàng `tab_po_item` (trả về PO có ít nhất một dòng khớp): `item_group` (LIKE), `invoice_no` (LIKE)
    - Danh sách PO còn gắn kèm `pr_id` (ID phiếu YCMH tương ứng `pr_code`) để frontend tạo deep-link điều hướng thẳng sang chi tiết PYC khi click cột "Mã PYC" trong danh sách.

15. Hoàn thành đơn: endpoint `POST /{id}/complete` chỉ chấp nhận khi MỌI dòng hàng đều ở trạng thái tiến độ `"Hoàn thành"` hoặc `"Hủy đơn"`. Nếu còn dòng chưa đạt điểm cuối, BE trả 400 và liệt kê tên sản phẩm còn chưa hoàn thành. Điều này đảm bảo đơn chỉ được đóng khi toàn bộ quy trình (nhập hóa đơn → thanh toán) đã xong cho mọi dòng.

---

## G. Quyền thao tác (RBAC)

Entity: `purchase_order`.

| Thao tác | Quyền yêu cầu | Điều kiện trạng thái |
|----------|---------------|----------------------|
| Xem danh sách / chi tiết | `purchase_order:read` | Mọi trạng thái (theo phạm vi dữ liệu scope — xem quy tắc 13) |
| Tạo mới / Nhân bản | `purchase_order:create` | — |
| Sửa header, dòng hàng | `purchase_order:write` | Đơn chưa `completed` / `cancelled`; dòng có `progress_status = 'Hoàn thành'/'Hủy đơn'` bị khóa riêng |
| Thêm / sửa lần giao | `purchase_order:write` | Đơn ở `approved` / `partial` / `received`; lần giao thuộc dòng đã khóa không sửa được |
| Gửi duyệt | `purchase_order:write` | Đơn `draft` hoặc `rejected` (Bị trả lại) |
| Mở lại (về nháp) | `purchase_order:write` | Mọi trạng thái (qua `/reopen`) |
| Đóng đơn (hoàn thành) | `purchase_order:write` | Đơn `received` hoặc `partial` (nút Hoàn thành xuất hiện ở cả hai) |
| Duyệt | `purchase_order:approve` | Đơn `submitted` |
| Trả về (Bị trả lại) | `purchase_order:approve` | Đơn `submitted`; cần nhập lý do |
| Từ chối (khóa hẳn) | `purchase_order:approve` | Đơn `submitted`; cần nhập lý do; status → `cancelled` |
| Hủy đơn | `purchase_order:cancel` | Đơn `approved` / `partial` / `received`; bắt buộc nhập lý do; bị chặn nếu có dòng đã "Hoàn thành" |
| Xóa | `purchase_order:delete` | Đơn `draft` / `rejected` (kiểm tra ở FE) |
| In (cả 2 mẫu) | `purchase_order:print` | Mọi trạng thái |
| Tải lên đính kèm / xóa đính kèm | `purchase_order:write` | Đơn chưa khóa |
| Cập nhật tiến độ dòng (Tạm ngưng / Hủy đơn / Tiếp tục) | `purchase_order:write` | Đơn `approved`/`partial`/`received`/`completed`; dòng chưa ở điểm cuối |
| Cập nhật trạng thái hồ sơ chứng từ | `purchase_order:write` | Mọi trạng thái (kể cả `completed`) |

---

## H. Tiến độ mua hàng dòng (`progress_status`) — cơ chế tự động và liên kết ngược về YCMH

### H.1 Máy trạng thái tiến độ dòng

Mỗi dòng hàng (`tab_po_item`) có trường `progress_status` riêng, độc lập với `status` của phiếu PO. Máy trạng thái gồm hai nhóm:

**Nhóm tuần tự (tự động, forward-only):**

| Bước | Giá trị `progress_status` | Điều kiện bắt buộc tích lũy (cộng dồn) |
|------|--------------------------|----------------------------------------|
| 0 | `"Chưa đặt hàng"` | — (trạng thái khởi đầu) |
| 1 | `"Đã đặt hàng"` | PO có `misa_code` không trống |
| 2 | `"Đã nhận hàng"` | Bước 1 thỏa VÀ `qty_received > 0` |
| 3 | `"Chưa gửi ĐMH cho KT"` | Bước 2 thỏa VÀ dòng có `invoice_no` không trống |
| 4 | `"Đã gửi ĐMH cho KT"` | Bước 3 thỏa VÀ dòng có `document_delivery_date` không trống |
| 5 | `"Hoàn thành"` | Bước 4 thỏa VÀ mọi công nợ hàng (`payable.remaining`) của dòng <= 0 |

Điều kiện mang tính **cộng dồn**: để đạt bước N, tất cả các bước từ 1 đến N đều phải thỏa. Hệ thống tìm bước cao nhất liên tục thỏa rồi cập nhật `progress_status` lên bước đó.

**Nhóm ngoại lệ (thủ công, cần lý do):**

| Giá trị | Hành động | Điều kiện | Phục hồi |
|---------|-----------|-----------|----------|
| `"Tạm ngưng"` | Người dùng bấm nút | Cần nhập lý do; lưu vào `pause_reason`; snapshot bước hiện tại vào `status_before_pause` | Bấm "Tiếp tục" (`status = "__resume__"`) → khôi phục `progress_status = status_before_pause` |
| `"Hủy đơn"` | Người dùng bấm nút | Cần nhập lý do; điểm cuối — không phục hồi được | — |

`"Hoàn thành"` và `"Hủy đơn"` là hai điểm cuối; không thể thay đổi trạng thái sau khi đạt một trong hai. Hệ thống khóa toàn bộ dòng đó (không cho sửa sản phẩm, không cho thêm/sửa lần giao).

### H.2 Cơ chế tự động nâng bước (`apply_auto_progress`)

Sau mỗi lần lưu đơn (`PATCH`), backend chạy `apply_auto_progress`:
1. Duyệt mọi dòng hàng của PO.
2. Với mỗi dòng chưa ở điểm cuối và chưa tạm ngưng, tính `highest_satisfied_step` — bước cao nhất liên tục thỏa điều kiện.
3. Nếu bước đó cao hơn bước hiện tại, cập nhật `progress_status` và ghi audit log `item_progress_auto`.
4. Nếu có bất kỳ dòng nào đổi bước, commit và kích hoạt đồng bộ sang YCMH (`_sync_pr`).

Logic là **forward-only**: chỉ tiến lên, không hạ ngược dù dữ liệu thay đổi (ví dụ xóa `invoice_no` sau khi dòng đã đạt bước 3 không kéo dòng về bước 2).

Ngoài ra, khi người dùng cập nhật thủ công qua endpoint `POST /{pid}/items/{item_id}/progress` (chỉ dùng cho "Tạm ngưng", "Hủy đơn", "__resume__"), hệ thống cũng gọi `_sync_pr` sau khi cập nhật.

### H.3 Cập nhật thủ công tiến độ dòng

Endpoint: `POST /api/purchase-orders/{pid}/items/{item_id}/progress`

Body `{status, reason}`:
- `status = "Tạm ngưng"`: bắt buộc có `reason`; lưu bước hiện tại vào `status_before_pause`.
- `status = "Hủy đơn"`: bắt buộc có `reason`; điểm cuối — dòng bị khóa hoàn toàn.
- `status = "__resume__"`: phục hồi từ "Tạm ngưng" về `status_before_pause` (hoặc về "Chưa đặt hàng" nếu không có snapshot).
- Mọi giá trị trong `PROGRESS_ORDER` (bước tuần tự): bị từ chối 400 — các bước đó chỉ được nâng tự động, không đặt tay.

Điều kiện áp dụng: đơn phải ở trạng thái `approved`/`partial`/`received`/`completed`; dòng chưa ở "Hoàn thành"/"Hủy đơn".

### H.4 Liên kết ngược từ PO về YCMH nguồn (`_sync_pr`)

Khi PO có `pr_code` (liên kết YCMH), mọi thao tác làm thay đổi tiến độ hoặc trạng thái PO đều kích hoạt `_sync_pr(db, po.pr_code)` → `sync_from_purchase_orders(db, pr_code)`.

**Quy tắc đồng bộ:**

- Chỉ tính các PO có `status` trong `("approved", "partial", "received", "completed")` — bỏ qua nháp, chờ duyệt, bị trả, đã từ chối.
- Với mỗi `product_code`, tổng hợp tất cả các dòng PO tương ứng:
  - Cộng `qty_order` → `pr_item.qty_ordered`
  - Cộng `qty_received` (từ các lần giao) → `pr_item.qty_received`
  - Tính `ordered_min`: mức tiến độ KÉM NHẤT trong các dòng đã đặt (index >= 1)
- Quy tắc đặc biệt:
  - Dòng PO `"Hủy đơn"`: không cộng SL, đánh dấu sản phẩm có dòng hủy.
  - Dòng PO `"Tạm ngưng"`: dùng `status_before_pause` thay cho `progress_status` (dùng mức thực trước khi tạm ngưng).
  - Dòng PO `"Chưa đặt hàng"`: bỏ qua hoàn toàn (không kéo tiến độ YCMH xuống).

**Kết quả cập nhật trên YCMH (`line_status` của dòng YCMH):**

| Điều kiện | `line_status` YCMH |
|-----------|-------------------|
| Không có dòng PO đã đặt; sản phẩm có dòng hủy | `"Hủy đơn"` |
| Không có dòng PO đã đặt; không có dòng hủy | `"Chưa đặt hàng"` |
| Có dòng đặt, `ordered_min` >= bước "Hoàn thành" | `"Hoàn thành"` |
| Có dòng đặt, đã nhận hàng (`qty_received > 0`) | `"Đã nhận hàng"` |
| Có dòng đặt, chưa nhận gì | `"Đã đặt hàng"` |

Nếu dòng YCMH đã được đặt thủ công thành `"Hủy đơn"` trên YCMH, hệ thống giữ nguyên và không ghi đè.

Sau khi cập nhật toàn bộ dòng, hệ thống gọi lại `recompute_status` để suy lại trạng thái tổng của phiếu YCMH.

### H.5 Màn hình Tiến độ mua hàng (`/purchase-progress`)

Màn hình riêng tại đường dẫn `/purchase-progress` (nhãn menu "Tiến độ mua hàng"), sử dụng endpoint `GET /api/purchase-progress`. Hiển thị dạng bảng phẳng, mỗi dòng = 1 dòng hàng (`po_item`) kèm thông tin lần giao tương ứng. Các cột chính: Mã ĐMH, Mã MISA, Mã PYC, Công ty, Bộ phận, NCC, NSPT, Ngày đặt, Mã SP, Tên SP, Tên hóa đơn, Nhóm hàng, Mã HH, Số HĐ, Ngày cần, ĐVT, SL đặt, Đơn giá, Thành tiền đặt, **Tiến độ** (`progress_status`), Lần giao, Kho, Ngày nhận, Ngày quy định, CL cam kết, CL quy định, CL vs YC, Hồ sơ CT (`document_status`). Hỗ trợ lọc theo công ty, bộ phận, tháng, trạng thái tiến độ, khoảng ngày đặt/nhận; sắp xếp theo cột; phân trang.
