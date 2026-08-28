# TỪ ĐIỂN DỮ LIỆU — TÀI CHÍNH · DANH MỤC · KHO

Bản 1.0 — 28/08/2026. Nguồn sự thật là model.py; tệp này chép Ý NGHĨA, không thay mã.

---

## Mục lục

1. [Tài chính](#1-tài-chính)
   - [`tab_payable` — Khoản công nợ phải trả](#tab_payable--khoản-công-nợ-phải-trả)
   - [`tab_payment_request` — Phiếu yêu cầu thanh toán](#tab_payment_request--phiếu-yêu-cầu-thanh-toán)
   - [`tab_payment_request_line` — Dòng đề nghị chi](#tab_payment_request_line--dòng-đề-nghị-chi)
2. [Danh mục](#2-danh-mục)
   - [`tab_supplier` — Nhà cung cấp](#tab_supplier--nhà-cung-cấp)
   - [`tab_contract` — Hợp đồng](#tab_contract--hợp-đồng)
   - [`tab_product` — Biến thể sản phẩm / SKU](#tab_product--biến-thể-sản-phẩm--sku)
   - [`tab_warehouse` — Kho](#tab_warehouse--kho)
   - [`tab_unit` — Đơn vị tính](#tab_unit--đơn-vị-tính)
   - [`tab_item_group` — Phân loại VTBB/NL](#tab_item_group--phân-loại-vtbbnl)
   - [`tab_brand` — Bộ phận đặt hàng / Thương hiệu](#tab_brand--bộ-phận-đặt-hàng--thương-hiệu)
   - [`tab_category_assignee` — Phân công NSTM theo phân loại](#tab_category_assignee--phân-công-nstm-theo-phân-loại)
3. [Kho](#3-kho)
   - [`tab_inventory` — Tồn kho hiện tại](#tab_inventory--tồn-kho-hiện-tại)
   - [`tab_inventory_move` — Sổ phát sinh nhập/xuất kho](#tab_inventory_move--sổ-phát-sinh-nhậpxuất-kho)
4. [Báo cáo](#4-báo-cáo)
   - [`tab_report_snapshot` — Kết quả báo cáo tính sẵn](#tab_report_snapshot--kết-quả-báo-cáo-tính-sẵn)
5. [Quan hệ trong cụm](#5-quan-hệ-trong-cụm)

---

## Ghi chú chung về cột kiểm tra

Mọi bảng đều kế thừa `AuditMixin` với 5 cột sau (không lặp lại trong từng bảng):

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | bigint | Khóa chính tự tăng |
| `created_at` | datetime | Thời điểm tạo (server mặc định) |
| `created_by` | bigint | ID tài khoản tạo |
| `updated_at` | datetime | Thời điểm cập nhật gần nhất |
| `updated_by` | bigint | ID tài khoản cập nhật |

---

## 1. Tài chính

### `tab_payable` — Khoản công nợ phải trả

Ghi nhận mỗi khoản nợ phát sinh ngầm khi xác nhận nhận hàng. Mỗi dòng tương ứng một lần giao hàng (delivery) nhân một luồng nguồn (`goods` hoặc `shipping`); hệ thống tạo và cập nhật tự động, không có màn hình nhập tay.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `company_id` | bigint | Pháp nhân chịu khoản nợ |
| `supplier_code` | str(50) | Mã NCC (nối lỏng với `tab_supplier.code`) |
| `supplier_name` | str(255) | Tên NCC lưu tại thời điểm tạo (không FK) |
| `source_type` | str(20) | Loại nguồn: `goods` = nợ NCC bán hàng; `shipping` = nợ đơn vị vận chuyển |
| `ref_type` | str(20) | Loại chứng từ gốc; hiện chỉ có `delivery` |
| `ref_id` | bigint | ID chứng từ gốc (`tab_po_delivery.id` khi `ref_type = delivery`) |
| `po_id` | bigint | ID đơn mua hàng tương ứng |
| `po_code` | str(50) | Mã đơn mua hàng (lưu thêm để tra nhanh, không phải FK cứng) |
| `invoice_no` | str(50) | Số hóa đơn VAT của NCC |
| `incur_date` | str(10) | Ngày phát sinh nợ (= ngày xác nhận nhận hàng), dạng `YYYY-MM-DD` |
| `period` | str(7) | Năm phát sinh (`incur_date[:4]`), dùng để lọc và nhóm theo năm |
| `due_date` | str(10) | Ngày đến hạn thanh toán, tính từ `incur_date` + số ngày công nợ của NCC |
| `amount` | decimal(18,2) | Giá trị trước VAT |
| `vat` | decimal(18,2) | Tiền VAT |
| `total` | decimal(18,2) | Tổng phải trả = `amount + vat` |
| `paid_amount` | decimal(18,2) | Tổng tiền đã được phân bổ thanh toán |
| `remaining` | decimal(18,2) | Số còn lại = `total - paid_amount` (tính sẵn, không tổng hợp lúc đọc) |
| `status` | str(20) | Trạng thái: `unpaid` / `partial` / `paid`; bộ mã `PAYABLE_STATUS` trong `status_codes.py` |

**Logic chính:**

- Không có màn hình nhập tay; `service.upsert()` được gọi từ module nhận hàng, idempotent theo `(source_type, ref_type, ref_id)`.
- `status` là hàm tính (`recalc_status`) dựa trên `paid_amount` so với `total`, không phải máy trạng thái cứng — sửa `total` của khoản đã `paid` sẽ tự lùi về `partial`.
- Số ngày công nợ (`due_date`) suy ra từ trường `payment_terms` của NCC bằng regex tìm cụm "N ngày" (ví dụ "Công nợ 30 ngày").
- Phân bổ thanh toán được thực hiện khi phiếu `tab_payment_request` chuyển sang trạng thái `paid`; logic chỉ đổ tiền vào các khoản CÒN NỢ (`remaining > 0`), bỏ qua khoản đã tất toán để tránh số dư âm.
- Có 5 nhóm tuổi nợ (aging bucket): "Chưa đến hạn", "1-30", "31-60", "61-90", ">90" ngày quá hạn.
- Cột `remaining` lưu sẵn; mã ngoài module (Trang chủ, báo cáo, thẻ tổng hợp) so sánh trực tiếp `status == "paid"` qua hằng số `ST_PAID` trong `payable/service.py` — không gõ chuỗi thẳng.

---

### `tab_payment_request` — Phiếu yêu cầu thanh toán

Phiếu gom nhiều khoản nợ của cùng một NCC thành một đề nghị chi. Mỗi phiếu chỉ thuộc một NCC và một luồng (`goods` hoặc `shipping`). Có thể in để trình ký.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `code` | str(50) | Mã phiếu tự sinh, dạng `YCTT00045` |
| `supplier_code` | str(50) | Mã NCC (nối lỏng với `tab_supplier.code`) |
| `supplier_name` | str(255) | Tên NCC lưu tại thời điểm tạo |
| `company_id` | bigint | Pháp nhân lập phiếu |
| `source_type` | str(20) | Loại nguồn: `goods` / `shipping` |
| `request_date` | str(10) | Ngày lập phiếu, dạng `YYYY-MM-DD` |
| `payment_method` | str(20) | Hình thức thanh toán: `transfer` (chuyển khoản) / `cash` (tiền mặt); quyết định nội dung bản in |
| `prepay` | smallint | Cờ thanh toán trước: `0` = thanh toán công nợ (mặc định); `1` = trả trước cho đơn hàng; quyết định câu chữ bản in |
| `print_texts` | text | JSON tùy chỉnh câu chữ bản in: `{"content": ..., "line_desc": ..., "transfer": ...}`; rỗng = dùng câu tự động theo `prepay` |
| `total` | decimal(18,2) | Tổng số tiền đề nghị chi (tổng các dòng) |
| `note` | text | Ghi chú |
| `reject_reason` | text | Lý do từ chối (điền khi chuyển sang `cancelled`) |
| `status` | str(20) | Vòng đời phiếu: `draft` / `submitted` / `approved` / `paid` / `cancelled` |

**Logic chính:**

- Tạo phiếu (`create_requests`): nếu các khoản nợ gửi lên thuộc nhiều NCC, hệ thống tách tự động thành nhiều phiếu — mỗi NCC một phiếu.
- Các dòng cùng `(po_code, invoice_no)` được gom thành một dòng phiếu duy nhất.
- Ở trạng thái `draft`: số hóa đơn được phép để trống (để in ra trình ký rồi điền tay); điều kiện đủ chỉ bắt khi gửi duyệt (`submitted`).
- Khi gửi duyệt (`check_submit`): mỗi dòng phải có số hóa đơn và phải khớp ít nhất một khoản nợ còn lại (`remaining > 0`).
- Khóa sửa đổi sau khi qua `submitted`: trường tiền và số hóa đơn không sửa được; chỉ riêng `print_texts` (câu chữ bản in) được sửa ở `submitted`/`approved` để phục vụ in sau duyệt.
- Khi chuyển `paid`: tiền được phân bổ vào các khoản nợ khớp (`matching_payables`), sau đó kích hoạt `apply_auto_progress` trên các PO liên quan để tự tiến trạng thái dòng ĐMH.
- Xóa phiếu không được khi đã `paid`.

---

### `tab_payment_request_line` — Dòng đề nghị chi

Mỗi dòng đại diện cho một nhóm hóa đơn trong phiếu yêu cầu thanh toán. Các dòng cùng `(po_code, invoice_no)` được gom về một dòng khi tạo phiếu.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `request_id` | bigint | Trỏ vào `tab_payment_request.id` |
| `payable_id` | bigint | Trỏ vào `tab_payable.id`; `= 0` khi dòng gõ tay trên form trắng, chưa gắn khoản nợ nào |
| `po_code` | str(50) | Mã đơn mua hàng (nhập tay được, mặc định lấy từ khoản nợ khi tạo phiếu) |
| `invoice_no` | str(50) | Số hóa đơn VAT (nhập tay được; bản nháp cho phép để trống) |
| `invoice_date` | str(10) | Ngày hóa đơn; mặc định lấy từ `tab_po_delivery.invoice_date`, sửa tay được |
| `amount` | decimal(18,2) | Số tiền đề nghị chi cho dòng này |

**Logic chính:**

- `payable_id = 0` biểu thị dòng gõ tay; hệ thống vẫn cố tra ngược khoản nợ theo `(supplier_code, po_code, invoice_no)` khi phân bổ tiền.
- Khi tạo phiếu (`fill_from_payable=True`): ô bỏ trống được tự điền từ khoản nợ; khi sửa phiếu thì không tự điền đè — người dùng có quyền xóa trắng.
- Nếu `amount = 0` và dòng gắn khoản nợ, hệ thống lấy `remaining` của khoản nợ làm giá trị mặc định.
- Khi phân bổ thanh toán: một hóa đơn có thể ứng với nhiều khoản nợ (nhiều lần giao cùng PO + cùng hóa đơn); tiền được trả lần lượt vào các khoản còn nợ cho đến hết.

---

## 2. Danh mục

### `tab_supplier` — Nhà cung cấp

Danh mục nhà cung cấp toàn hệ. `supplier_type` phân biệt NCC bán hàng (`goods`) và đơn vị vận chuyển (`shipping`). Mã NCC (`code`) được dùng làm khóa nối lỏng ở nhiều bảng khác.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `code` | str(50) | Mã NCC duy nhất (tên viết tắt); dùng làm khóa nối lỏng toàn hệ |
| `name` | str(255) | Tên pháp lý đầy đủ |
| `legal_type` | str(30) | Loại pháp nhân; mã tiếng Anh, bộ `SUPPLIER_LEGAL_TYPE` trong `status_codes.py`; rỗng = chưa chọn |
| `tax_code` | str(25) | Mã số thuế |
| `address` | text | Địa chỉ |
| `supplier_type` | str(20) | Loại NCC: `goods` = bán hàng; `transport` = vận chuyển |
| `contact_person` | str(100) | Người liên hệ |
| `phone` | str(30) | Số điện thoại |
| `payment_terms` | str(255) | Hình thức thanh toán (ví dụ "Công nợ 30 ngày"); dùng để tính `due_date` trong `tab_payable` |
| `bank_account` | str(50) | Số tài khoản ngân hàng |
| `bank_name` | str(255) | Tên ngân hàng |
| `bank_account_name` | str(255) | Tên chủ tài khoản thụ hưởng |
| `vat` | float | Tỷ lệ VAT mặc định của NCC (lưu tỷ lệ thực, ví dụ `0.08` cho 8%, không phải `8`) |
| `is_active` | bool | Đang hoạt động hay đã ngừng |

**Logic chính:**

- Mã `code` là duy nhất; nếu không truyền khi tạo, hệ thống tự sinh theo tiền tố `NCC`.
- `legal_type` chứa mã tiếng Anh cố định từ `status_codes.py`; property `legal_type_label` dịch sang tiếng Việt.
- `payment_terms` được module công nợ đọc bằng regex để suy ra số ngày công nợ; giá trị tự do nên phải gõ đúng cụm "N ngày".
- `vat` lưu tỷ lệ thực (`0.08`), không phải số nguyên phần trăm; frontend phải dùng kiểu trường `percent` (không tự nhân/chia 100).

---

### `tab_contract` — Hợp đồng

Ghi nhận hợp đồng ký với nhiều loại đối tượng (NCC, khách hàng…). Chủ yếu dùng để biết đối tượng đã ký với pháp nhân nào và đính kèm file hợp đồng thật; không lưu chi tiết điều khoản.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `code` | str(50) | Mã hợp đồng, dạng `HD00001`; tự sinh nếu để trống |
| `party_type` | str(30) | Loại đối tượng ký: `supplier` / `customer` / `other`; mã tiếng Anh, bộ `CONTRACT_PARTY_TYPE` |
| `party_code` | str(50) | Mã đối tượng (ví dụ mã NCC khi `party_type = supplier`) |
| `party_name` | str(255) | Tên đối tượng; tự điền từ `tab_supplier.name` khi `party_type = supplier` |
| `company_id` | bigint | Pháp nhân bên mình ký hợp đồng |
| `title` | str(255) | Tên / trích yếu hợp đồng |
| `contract_type` | str(50) | Loại hợp đồng; mã tiếng Anh, bộ cố định trong `contract_types.py`; rỗng = chưa phân loại |
| `start_date` | str(10) | Ngày hiệu lực, dạng `YYYY-MM-DD` |
| `end_date` | str(10) | Ngày hết hạn, dạng `YYYY-MM-DD` |
| `signed` | bool | Đã ký chính thức |
| `status` | str(30) | Trạng thái người dùng đánh dấu: `active` / `expired` / `liquidated` / `cancelled`; bộ `CONTRACT_STATUS` |
| `note` | text | Ghi chú |

**Logic chính:**

- Bên cạnh `status` (do người dùng đánh dấu), API còn tính trường `expiry` (tình trạng hạn) từ `end_date` so với ngày hiện tại: `expired` / `expiring_soon` (trong 30 ngày) / `valid` / rỗng (không đặt hạn). Trường này không lưu DB, tính mỗi lần đọc.
- Scoping được áp cứng cả khi đọc lẫn khi tạo: người dùng không thể lập hợp đồng đứng tên pháp nhân ngoài phạm vi của mình.
- `contract_type` dùng `VARCHAR(50)` thay vì ENUM để thêm loại mới chỉ cần sửa danh sách code, không phải `ALTER TABLE`.
- Khi xóa hợp đồng, tệp đính kèm liên quan cũng bị xóa theo (qua `delete_attachments_for`).

---

### `tab_product` — Biến thể sản phẩm / SKU

**Lưu ý quan trọng (D-025):** `tab_product` là bảng VARIANT (SKU), không phải sản phẩm cha. Cột `code` là hạt dữ liệu kết nối toàn hệ — 7 bảng khác (YCMH, ĐMH, nhận hàng, tồn kho, luân chuyển kho, lịch sử mua hàng, option khảo sát) nối với nhau bằng **chuỗi `product_code`**, không có FK cứng vào bảng này. Xem mục "Quan hệ trong cụm" cuối tài liệu.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `code` | str(50) | Mã VTBB/NL duy nhất; là khóa nối lỏng toàn hệ |
| `name` | str(255) | Tên VTBB/NL |
| `invoice_name` | str(255) | Tên hiển thị trên hóa đơn (có thể khác tên thường dùng) |
| `legal_name` | str(255) | Tên pháp lý hàng hóa (tham chiếu col45) |
| `item_group` | str(50) | Mã phân loại; nối lỏng với `tab_item_group.code` |
| `unit` | str(25) | Mã đơn vị tính; nối lỏng với `tab_unit.code` |
| `hh_code` | str(50) | Mã hàng hóa (liên kết sản phẩm/hàng hóa) |
| `hh_name` | str(255) | Tên sản phẩm/hàng hóa |
| `specs` | str(255) | Thông số kỹ thuật / xuất xứ / chất liệu; tự điền vào ô "Xuất xứ/TSKT" của dòng ĐMH khi chọn sản phẩm; giới hạn 255 khớp `POItem.spec` |
| `is_active` | bool | Đang hoạt động |

**Logic chính:**

- Mã `code` phải là duy nhất; service từ chối tạo khi mã đã tồn tại.
- Không có bảng sản phẩm cha bên dưới; cấm thêm `tab_product_variant`, cấm đổi/tái dùng `product_code`, cấm đặt cột giá lên bảng này.
- `item_group` và `unit` là chuỗi nối lỏng (không có FK FOREIGN KEY cứng vào `tab_item_group`/`tab_unit`), phù hợp với kiến trúc nối bằng mã chuỗi của toàn cụm.
- Giá mua không lưu ở đây; giá lấy từ dòng ĐMH (`tab_po_item`) rồi phản ánh vào tồn kho qua đơn giá bình quân gia quyền.

---

### `tab_warehouse` — Kho

Danh mục kho hàng. Mã kho (`code`) được dùng làm khóa nối lỏng trong `tab_inventory` và `tab_inventory_move`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `code` | str(25) | Mã kho duy nhất; dùng làm khóa nối trong bảng tồn kho |
| `name` | str(255) | Tên kho |
| `address` | text | Địa chỉ kho |
| `is_active` | bool | Đang hoạt động |

**Logic chính:**

- Quản lý qua router CRUD chung (`make_crud_router`); hỗ trợ xuất CSV.
- Mã `code` duy nhất, không tự sinh tiền tố.

---

### `tab_unit` — Đơn vị tính

Danh mục đơn vị tính dùng cho sản phẩm, dòng YCMH, ĐMH và tồn kho.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `code` | str(25) | Mã ĐVT duy nhất; tự sinh tiền tố `DVT` nếu để trống |
| `name` | str(100) | Tên đơn vị tính |
| `is_active` | bool | Đang hoạt động |

**Logic chính:**

- Quản lý qua router CRUD chung; hỗ trợ xuất CSV.
- Mã `code` nối lỏng với cột `unit` trên `tab_product`, `tab_inventory`, `tab_inventory_move` — không FK cứng.

---

### `tab_item_group` — Phân loại VTBB/NL

Phân loại vật tư bán thành phẩm / nguyên liệu, kèm thời gian quy định giao hàng theo từng loại (dùng để tính chỉ tiêu trong phiếu khảo sát).

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `code` | str(25) | Mã phân loại duy nhất; tự sinh tiền tố `PLO` nếu để trống |
| `name` | str(100) | Tên phân loại; duy nhất |
| `std_days` | str(20) | Số ngày quy định khi NCC CÓ sẵn hàng |
| `std_days_unavail` | str(20) | Số ngày quy định khi NCC KHÔNG sẵn hàng |
| `note` | text | Ghi chú |
| `apply_date` | str(20) | Ngày áp dụng quy định |
| `is_active` | bool | Đang hoạt động |

**Logic chính:**

- Quản lý qua router CRUD chung; hỗ trợ xuất CSV.
- `std_days` và `std_days_unavail` lưu dạng chuỗi để linh hoạt (có thể ghi ghi chú kèm số).
- Bảng này là đầu vào của `tab_category_assignee`: mỗi phân loại có một NSTM chính và một NSTM dự phòng.

---

### `tab_brand` — Bộ phận đặt hàng / Thương hiệu

Đại diện cho bộ phận nội bộ đặt hàng hoặc nhãn hàng/thương hiệu trong hệ thống.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `code` | str(25) | Mã bộ phận/thương hiệu duy nhất; tự sinh tiền tố `PBA` |
| `department` | str(255) | Tên bộ phận đặt hàng |
| `manager_id` | bigint | ID nhân sự quản lý; nối lỏng với `tab_employee.id` qua relationship viewonly |
| `is_active` | bool | Đang hoạt động |

**Logic chính:**

- Quản lý qua router CRUD chung; hỗ trợ xuất CSV.
- Property `manager_name` tra ngược `tab_employee` qua relationship viewonly (`foreign(Brand.manager_id) == Employee.id`); không phải FK cứng ở DB.

---

### `tab_category_assignee` — Phân công NSTM theo phân loại

Lưu phân công nhân sự thu mua (NSTM) phụ trách từng phân loại VTBB. Mỗi phân loại có đúng một người chính và một người dự phòng. Khi trưởng phòng duyệt yêu cầu mua hàng (PYC), hệ thống tự điền `assignee` cho từng dòng theo phân loại của dòng đó.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `item_group_id` | bigint | ID phân loại VTBB; duy nhất (unique), nối với `tab_item_group.id` |
| `primary_employee_id` | bigint | ID nhân sự NSTM chính; nối lỏng với `tab_employee.id` |
| `backup_employee_id` | bigint | ID nhân sự NSTM dự phòng; nối lỏng với `tab_employee.id` |

**Logic chính:**

- Quan hệ 1-1 với `tab_item_group`: mỗi phân loại chỉ có đúng một bản ghi phân công (`unique` trên `item_group_id`).
- Khi duyệt PYC, service tra bảng này theo `item_group` của từng dòng để điền `assignee_id` tự động.
- `primary_employee_id` và `backup_employee_id` là ID nhân sự, không phải ID tài khoản (xem quy tắc chung của hệ thống: `assignee_id` / `requester_id` trên chứng từ là ID NHÂN SỰ).

---

## 3. Kho

### `tab_inventory` — Tồn kho hiện tại

Lưu số lượng tồn và giá trị tồn hiện tại của từng `(công ty, kho, sản phẩm)`. Được tính lại mỗi khi có phát sinh nhập/xuất hoặc điều chỉnh; không phải sổ phát sinh.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `company_id` | bigint | Pháp nhân |
| `warehouse_code` | str(50) | Mã kho; nối lỏng với `tab_warehouse.code` |
| `product_code` | str(50) | Mã sản phẩm; nối lỏng với `tab_product.code` |
| `product_name` | str(255) | Tên sản phẩm (lưu thêm để truy vấn nhanh) |
| `unit` | str(25) | Đơn vị tính (lưu thêm) |
| `qty` | decimal(18,3) | Số lượng tồn hiện tại (3 số lẻ) |
| `avg_cost` | decimal(18,4) | Đơn giá bình quân gia quyền (4 số lẻ, khớp độ chính xác đơn giá ĐMH) |
| `value` | decimal(18,2) | Giá trị tồn = `qty × avg_cost` (2 số lẻ) |

**Logic chính:**

- Bộ khóa thực tế là `(company_id, warehouse_code, product_code)`; không có cột `UNIQUE CONSTRAINT` ở tầng DB nhưng logic `_recompute` upsert theo đúng bộ này.
- `avg_cost` tính theo phương pháp bình quân gia quyền toàn kỳ: `Σ(qty × unit_price) / Σqty` trên toàn bộ `tab_inventory_move` của bộ khóa.
- Khi một dòng giao hàng bị sửa và thay đổi kho/sản phẩm, `_recompute` được gọi cho cả key cũ lẫn key mới để đảm bảo nhất quán.
- Không xuất kho thủ công ở Phase 2; chỉ nhập từ nhận hàng PO và điều chỉnh tay.

---

### `tab_inventory_move` — Sổ phát sinh nhập/xuất kho

Ghi nhận từng phát sinh làm thay đổi tồn kho. `qty > 0` là nhập; `qty < 0` là xuất hoặc điều chỉnh giảm. Đây là nguồn dữ liệu để tính lại `tab_inventory`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `company_id` | bigint | Pháp nhân |
| `warehouse_code` | str(50) | Mã kho; nối lỏng với `tab_warehouse.code` |
| `product_code` | str(50) | Mã sản phẩm; nối lỏng với `tab_product.code` |
| `qty` | decimal(18,3) | Số lượng phát sinh; dương = nhập, âm = xuất/điều chỉnh giảm |
| `unit_price` | decimal(18,4) | Đơn giá nhập (dùng để tính bình quân gia quyền); 4 số lẻ |
| `ref_type` | str(20) | Loại chứng từ gốc: `gr` (từ nhận hàng PO) / `adjust` (điều chỉnh tay) |
| `ref_id` | bigint | ID chứng từ gốc (`tab_po_delivery.id` khi `ref_type = gr`) |
| `note` | text | Ghi chú (tự điền "Nhận hàng từ PO" khi `ref_type = gr`) |

**Logic chính:**

- Phát sinh `gr` là idempotent theo `(ref_type, ref_id)`: gọi `apply_delivery` nhiều lần với cùng `delivery_id` chỉ cập nhật, không thêm dòng trùng.
- Sau mỗi thay đổi (thêm/sửa/xóa dòng), hàm `_recompute` tổng hợp lại toàn bộ các move của bộ khóa và ghi đè lên `tab_inventory`.
- Điều chỉnh tay (`adjust`): nếu không truyền `unit_price`, dùng `avg_cost` hiện tại của `tab_inventory` làm đơn giá.
- Xóa đợt giao hàng (`remove_delivery`) sẽ xóa dòng move tương ứng và tính lại tồn.

---

## 4. Báo cáo

### `tab_report_snapshot` — Kết quả báo cáo tính sẵn

Cache kết quả các báo cáo ma trận đã được tính trước (precompute) để đọc nhanh mà không cần tổng hợp lại lúc mở trang. Tác vụ tính lại chạy nền theo lịch (Celery).

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `key` | str(50) | Khóa tra cứu, dạng `{year}\|{company_id or "all"}`; duy nhất |
| `data` | text | Nội dung JSON chứa các báo cáo ma trận đã tính |
| `computed_at` | str(30) | Thời điểm tính gần nhất (chuỗi ISO 8601) |

**Logic chính:**

- Khóa `key` phân biệt theo năm và theo pháp nhân (hoặc `"all"` cho tất cả pháp nhân).
- `data` là JSON tự do; cấu trúc bên trong phụ thuộc từng loại báo cáo và có thể thay đổi theo nghiệp vụ mà không cần migration.
- Tác vụ tính lại (Celery beat) chạy 2 lần/ngày, ghi đè bản ghi hiện tại; API đọc thẳng snapshot thay vì query tổng hợp.

---

## 5. Quan hệ trong cụm

### 5.1 Quan hệ bằng khóa ngoại tường minh (hoặc nối ID)

| Bảng nguồn | Cột | Trỏ vào | Ghi chú |
|------------|-----|---------|---------|
| `tab_payment_request_line` | `request_id` | `tab_payment_request.id` | Quan hệ 1-N; dòng phiếu thuộc phiếu |
| `tab_payment_request_line` | `payable_id` | `tab_payable.id` | Nối lỏng; `= 0` khi dòng gõ tay |
| `tab_category_assignee` | `item_group_id` | `tab_item_group.id` | Quan hệ 1-1; unique |
| `tab_category_assignee` | `primary_employee_id` | `tab_employee.id` | Nối lỏng (ID nhân sự, không phải ID tài khoản) |
| `tab_category_assignee` | `backup_employee_id` | `tab_employee.id` | Nối lỏng (ID nhân sự) |
| `tab_brand` | `manager_id` | `tab_employee.id` | Relationship viewonly, không phải FK cứng DB |
| `tab_payable` | `ref_id` | `tab_po_delivery.id` (khi `ref_type = delivery`) | Nối lỏng theo loại |
| `tab_inventory_move` | `ref_id` | `tab_po_delivery.id` (khi `ref_type = gr`) | Nối lỏng theo loại |

### 5.2 Quan hệ bằng CHUỖI MÃ (không có FK cứng)

Đây là điểm đặc thù của kiến trúc hệ thống (D-025). Toàn bộ các bảng nối với sản phẩm, kho và NCC qua chuỗi mã — không có `FOREIGN KEY` constraint ở tầng DB. Xóa hoặc đổi mã gốc không phát sinh lỗi constraint nhưng sẽ làm đứt liên kết dữ liệu.

| Cột nối | Trỏ về mã của bảng | Các bảng sử dụng cột này |
|---------|-------------------|--------------------------|
| `product_code` | `tab_product.code` | `tab_inventory`, `tab_inventory_move`, `tab_po_item` (ĐMH), `tab_purchase_request_item` (YCMH), `tab_po_delivery` (nhận hàng), `tab_purchase_history` (lịch sử mua), và option khảo sát |
| `warehouse_code` | `tab_warehouse.code` | `tab_inventory`, `tab_inventory_move` |
| `supplier_code` | `tab_supplier.code` | `tab_payable`, `tab_payment_request`, `tab_contract` (qua `party_code`), và nhiều bảng trong luồng mua hàng |
| `item_group` (chuỗi) | `tab_item_group.code` | `tab_product` |
| `unit` (chuỗi) | `tab_unit.code` | `tab_product`, `tab_inventory`, `tab_inventory_move` |

### 5.3 Luồng nghiệp vụ tài chính

```
tab_po_delivery (nhận hàng)
  └── [sinh ngầm khi nhận] ──► tab_payable (1 khoản nợ / 1 lần giao / 1 luồng)
                                    │
                            [gom theo NCC]
                                    │
                                    ▼
                          tab_payment_request (phiếu YCTT)
                          tab_payment_request_line (dòng phiếu)
                                    │
                            [khi status = paid]
                                    │
                                    ├──► tab_payable.paid_amount += ... (phân bổ theo invoice_no)
                                    └──► tab_po_item (tự tiến trạng thái ĐMH)
```

### 5.4 Luồng nghiệp vụ kho

```
tab_po_delivery (nhận hàng, ghi nhận qty nhận)
  └── [apply_delivery()] ──► tab_inventory_move (1 dòng gr / 1 lần giao)
                                    │
                            [_recompute()]
                                    │
                                    ▼
                              tab_inventory (tồn + avg_cost cập nhật)
```
