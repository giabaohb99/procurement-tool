# Danh mục

Nhóm màn hình quản lý danh mục dùng chung trong toàn hệ thống. Mỗi danh mục là một bảng độc lập hỗ trợ thao tác Xem danh sách / Thêm / Sửa / Xóa; các danh mục có `importExport: true` bổ sung thêm Import CSV và Export CSV. Dữ liệu danh mục được tham chiếu từ các chứng từ nghiệp vụ (PYC, Khảo sát, PO, Hợp đồng, ...).

---

## Nhà cung cấp

Lưu trữ thông tin pháp lý, liên lạc và tài chính của các đối tác cung ứng hàng hóa (`goods`) và đơn vị vận chuyển (`transport`). Mỗi nhà cung cấp được định danh bằng mã viết tắt duy nhất, được tham chiếu từ phiếu khảo sát, hợp đồng, đơn mua hàng và công nợ. Trang chi tiết có nhiều tab: Thông tin / Đánh giá / Hợp đồng / Công nợ / Khảo sát của NCC / **Lịch sử mua hàng** (từng bán những gì, giá bao nhiêu — xem `04-don-mua-hang.md` mục I).

Đường dẫn: `/suppliers` (danh sách), `/suppliers/:id` (trang riêng `SupplierDetail`).

### 1. Mã / viết tắt (`code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có (kiểm tra khi lưu; không được để trống)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `supplier:create` — chỉ nhập khi tạo mới; không sửa được sau đó (`readonlyOnEdit`)
- Logic: Là khóa nghiệp vụ; trường `supplier_code` / `party_code` trong các chứng từ lưu giá trị này. Khi chọn NCC trong phiếu khảo sát, `code` của NCC được dùng để tra cứu và tự điền thông tin

### 2. Vai trò cung cấp (`supplier_type`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: NCC bán hàng (`goods`)
- Bắt buộc: Không (mặc định `goods` nếu không chọn)
- Nguồn dữ liệu / liên kết: NCC bán hàng (`goods`) / Đơn vị vận chuyển (`transport`)
- Người sửa: Người dùng có quyền `supplier:write`

### 3. Tên pháp lý (`name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có (kiểm tra khi lưu; không được để trống)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `supplier:write`

### 4. Loại nhà cung cấp (`legal_type`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Công ty / Cá nhân / Hợp danh / Hộ kinh doanh
- Người sửa: Người dùng có quyền `supplier:write`

### 5. Người liên hệ (`contact_person`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `supplier:write`

### 6. Điện thoại (`phone`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `supplier:write`

### 7. Địa chỉ (`address`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `supplier:write`

### 8. Mã số thuế (`tax_code`)

- Kiểu nhập: Nhập tay (chỉ nhập ký tự số)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `supplier:write`
- Logic: Khi chọn NCC trong dòng khảo sát NCC, trường này tự điền vào `tax_code` của dòng khảo sát

### 9. VAT mặc định (`vat`)

- Kiểu nhập: Nhập số (%), từ 0 đến **dưới 100** (CR-058)
- Mặc định: 8 (tức 8%)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `supplier:write`
- Logic: Lưu vào DB dưới dạng **tỉ lệ** (ví dụ 0.08 cho 8%); **trang chi tiết NCC** hiển thị và nhận nhập theo phần trăm (8) rồi tự chia 100 khi lưu. Cẩn thận: **form NCC ở màn hình danh mục chung** (và **cột VAT trong file import CSV**) gửi thẳng **tỉ lệ**, không nhân/chia — gõ `8` ở đó nghĩa là 800%. Server chặn `0 ≤ vat < 1`, import CSV báo lỗi rõ nếu ngoài khoảng.

### 10. Hình thức thanh toán (`payment_terms`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Công nợ 60 ngày / Thanh toán 100% khi nhận hàng / Công nợ 30 ngày / Thanh toán trước khi giao hàng / Thanh toán 7 ngày sau khi nhận hàng / Công nợ 20 ngày
- Người sửa: Người dùng có quyền `supplier:write`

### 11. Số tài khoản ngân hàng (`bank_account`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `supplier:write`

### 12. Tên ngân hàng & Chi nhánh (`bank_name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `supplier:write`

### 13. Đang hoạt động (`is_active`)

- Kiểu nhập: Checkbox
- Mặc định: Có (tích)
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `supplier:write`
- Logic: NCC không hoạt động vẫn giữ nguyên trong hệ thống và không bị xóa khỏi các chứng từ cũ

---

## Sản phẩm

Danh mục vật tư bao bì / nguyên liệu / hàng hóa nội bộ (VTBB/NL). Mỗi sản phẩm có mã nội bộ duy nhất và có thể liên kết với mã hàng hóa (HH) trong hệ thống kế toán/bán hàng. Được tham chiếu từ phiếu khảo sát (chọn Mã VTBB/VL) và PYC. Trang chi tiết có tab **Lịch sử mua hàng** — mặt hàng này từng mua của NCC nào, giá bao nhiêu, lần nào (xem `04-don-mua-hang.md` mục I).

Đường dẫn: `/products`.

### 1. Mã VTBB/NL (`code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có (duy nhất)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `product:create` — không sửa được sau khi tạo (`readonlyOnEdit`)

### 2. Tên VTBB/NL (`name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `product:write`

### 3. Tên trên hóa đơn (`invoice_name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `product:write`

### 4. Tên pháp lý (`legal_name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `product:write`

### 5. Phân loại (`item_group`)

- Kiểu nhập: Chọn (dropdown, lấy từ `/api/item-groups`; value và label đều là `name`)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Phân loại VTBB/NL (`item_group.name`)
- Người sửa: Người dùng có quyền `product:write`
- Logic: Khi người dùng chọn sản phẩm này trong phiếu khảo sát, giá trị phân loại được tự điền vào trường `item_group` của phiếu

### 6. Đơn vị tính (`unit`)

- Kiểu nhập: Nhập tay (mã hoặc tên ĐVT)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Đơn vị tính (`unit.name`)
- Người sửa: Người dùng có quyền `product:write`
- Logic: Khi người dùng chọn sản phẩm này trong phiếu khảo sát, ĐVT được tự điền vào trường `uom` của phiếu

### 7. Mã HH (sản phẩm) (`hh_code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Mã sản phẩm trong hệ thống kế toán / HH bên ngoài (có index riêng để tra cứu nhanh)
- Người sửa: Người dùng có quyền `product:write`

### 8. Tên Sản phẩm (HH) (`hh_name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `product:write`

### 9. Thông số kỹ thuật (`specs`)

- Kiểu nhập: Nhập nhiều dòng (textarea, tối đa 255 ký tự)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `product:write`
- Logic: Khi chọn sản phẩm này ở dòng hàng Đơn mua hàng, giá trị được tự điền vào ô
  **Xuất xứ / TSKT / chất liệu** (`spec`) của dòng — xem `04-don-mua-hang.md` mục "Dòng hàng → 5".
  Backend còn tự điền lần nữa lúc LƯU đơn cho các dòng MỚI còn bỏ trống (áp cho cả ĐMH tạo từ PYC).
  Giới hạn 255 ký tự để khớp `po_item.spec`, tránh bị cắt cụt khi sao chép sang đơn.
- Import/Export CSV: cột **"Thông số kỹ thuật"** (import chấp nhận cả tiêu đề "TSKT")

### 10. Đang dùng (`is_active`)

- Kiểu nhập: Chọn (danh sách cố định: Đang dùng / Ngừng)
- Mặc định: Đang dùng
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `product:write`

---

## Hợp đồng

Quản lý hợp đồng giữa công ty (pháp nhân nội bộ) và đối tác bên ngoài (nhà cung cấp, khách hàng hoặc đối tượng khác). Mỗi hợp đồng lưu thông tin cơ bản và đính kèm file PDF/ảnh gốc. Tab "Hợp đồng" trong trang Nhà cung cấp hiển thị danh sách hợp đồng của NCC đó. Danh sách hợp đồng tô màu cảnh báo theo trạng thái hết hạn.

Đường dẫn: `/contracts` (danh sách), `/contracts/:id` (trang riêng `ContractDetail`).

### 1. Đối tượng (`party_type`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: Nhà cung cấp
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: Nhà cung cấp / Khách hàng / Khác
- Người sửa: Người dùng có quyền `contract:write`
- Logic: Khi chọn "Nhà cung cấp", trường nhập đối tượng chuyển thành SearchSelect NCC (tự điền `party_name`); khi chọn loại khác, chuyển thành ô nhập tay

### 2. Nhà cung cấp / Tên đối tượng (`party_code` / `party_name`)

- Kiểu nhập: Chọn NCC (SearchSelect, hiển thị "mã — tên") khi đối tượng là Nhà cung cấp; Nhập tay khi đối tượng là loại khác
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: Bảng Nhà cung cấp (`supplier`) khi chọn NCC
- Người sửa: Người dùng có quyền `contract:write`
- Logic: Khi chọn NCC từ danh sách, `party_name` tự điền từ `supplier.name`; `party_code` lưu mã viết tắt NCC

### 3. Công ty (bên mình) ký (`company_id`)

- Kiểu nhập: Chọn (SearchSelect)
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: Bảng Công ty (`company`)
- Người sửa: Người dùng có quyền `contract:write`

### 4. Loại hợp đồng (`contract_type`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Mua bán / Nguyên tắc / Vận chuyển
- Người sửa: Người dùng có quyền `contract:write`

### 5. Trích yếu hợp đồng (`title`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `contract:write`

### 6. Từ ngày (`start_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `contract:write`

### 7. Đến ngày (`end_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `contract:write`
- Logic: Hệ thống tự tính trường phái sinh `expiry` theo ngày này: Hết hạn (đã quá ngày kết thúc), Sắp hết hạn (còn trong vòng 30 ngày), Còn hạn. Danh sách tô nền đỏ nhạt / vàng nhạt tương ứng

### 8. Trạng thái (`status`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: Hiệu lực
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Hiệu lực / Hết hạn / Thanh lý
- Người sửa: Người dùng có quyền `contract:write`

### 9. Đã ký (`signed`)

- Kiểu nhập: Checkbox
- Mặc định: Không tích
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `contract:write`

### 10. Ghi chú (`note`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `contract:write`

### 11. Tệp đính kèm

- Kiểu nhập: Upload file (nhiều file; kéo/chọn; PDF, ảnh, v.v.)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Lưu trên Cloudflare R2; bảng `attachment` với `entity='contract'`, `entity_id=<id hợp đồng>`
- Người sửa: Người dùng có quyền `contract:write`
- Logic: Chỉ đính kèm được sau khi hợp đồng đã được tạo và có `id`. Mỗi file xóa riêng lẻ qua nút xóa bên cạnh

### Bộ lọc danh sách

| Bộ lọc | Kiểu | Ghi chú |
|---|---|---|
| Mã HĐ | Nhập text | |
| Tên đối tượng | Nhập text | Lọc theo `party_name` |
| Đối tượng | Chọn | Nhà cung cấp / Khách hàng / Khác |
| Loại | Chọn | Mua bán / Nguyên tắc / Vận chuyển |
| Trạng thái | Chọn | Hiệu lực / Hết hạn / Thanh lý |
| Tình trạng hết hạn | Chọn | Còn hạn / Sắp hết hạn / Hết hạn (tính từ `end_date` so với hôm nay) |
| Đã ký | Chọn | Đã ký / Chưa ký |
| Ngày hết hạn | Khoảng ngày | Lọc theo khoảng `end_date` |

---

## Kho

Danh sách kho hàng vật lý của tổ chức. Được tham chiếu từ nghiệp vụ nhận hàng (GR) và tồn kho. Hỗ trợ Import/Export CSV.

Đường dẫn: `/warehouses`.

### 1. Mã (`code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có (duy nhất)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `warehouse:create` — không sửa được sau khi tạo (`readonlyOnEdit`)

### 2. Tên kho (`name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `warehouse:write`

### 3. Địa chỉ (`address`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `warehouse:write`

### 4. Đang dùng (`is_active`)

- Kiểu nhập: Chọn (danh sách cố định: Đang dùng / Ngừng)
- Mặc định: Đang dùng
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `warehouse:write`

> **Ghi chú:** Đang có CR-001 (đề xuất redesign Kho — bổ sung `company_id`, `supplier_code`, `warehouse_type`) chờ phê duyệt; chưa được triển khai vào code. Cấu trúc hiện tại là `code / name / address / is_active`.

---

## Đơn vị tính

Danh sách đơn vị tính dùng cho sản phẩm và phiếu khảo sát (ĐVT báo giá, ĐVT quy đổi về công ty). Hỗ trợ Import/Export CSV.

Đường dẫn: `/units`.

### 1. Mã (`code`)

- Kiểu nhập: Nhập tay (hệ thống tự sinh với tiền tố `DVT` nếu để trống)
- Mặc định: trống (tự sinh)
- Bắt buộc: Không (tự sinh nếu để trống)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `unit:create` — không sửa được sau khi tạo

### 2. Tên ĐVT (`name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `unit:write`

### 3. Đang dùng (`is_active`)

- Kiểu nhập: Chọn (danh sách cố định: Đang dùng / Ngừng)
- Mặc định: Đang dùng
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `unit:write`

---

## Phân loại (nhóm hàng)

Danh sách nhóm phân loại VTBB/NL kèm thời gian quy định (số ngày chuẩn để hoàn thành mua hàng). Tham chiếu từ phiếu khảo sát, PYC và bảng Phân công phụ trách. Hỗ trợ Import/Export CSV.

Đường dẫn: `/item-groups`.

### 1. Phân loại (`name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có (duy nhất)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `item_group:create` — không sửa được sau khi tạo (`readonlyOnEdit`)
- Logic: Tên phân loại là khóa nghiệp vụ; trường `item_group` trong Product và Survey lưu chuỗi tên này. Phân loại cũng dùng làm khóa tra cứu trong bảng Phân công phụ trách

### 2. Số ngày QĐ khi NCC có sẵn hàng (`std_days`)

- Kiểu nhập: Nhập tay (chuỗi, ví dụ: "5", "5–7")
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `item_group:write`

### 3. Số ngày QĐ khi NCC không sẵn hàng (`std_days_unavail`)

- Kiểu nhập: Nhập tay (chuỗi)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `item_group:write`

### 4. Ghi chú (`note`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `item_group:write`

### 5. Ngày áp dụng (`apply_date`)

- Kiểu nhập: Nhập tay (chuỗi ngày)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `item_group:write`

### 6. Đang dùng (`is_active`)

- Kiểu nhập: Chọn (danh sách cố định: Đang dùng / Ngừng)
- Mặc định: Đang dùng
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `item_group:write`

---

## Thương hiệu

Danh sách thương hiệu hoặc bộ phận đặt hàng nội bộ kèm người quản lý phụ trách. API: `/api/brands`. Hỗ trợ Export CSV.

### 1. Mã (`code`)

- Kiểu nhập: Nhập tay (hệ thống tự sinh với tiền tố `PBA` nếu để trống)
- Mặc định: trống (tự sinh)
- Bắt buộc: Không (tự sinh nếu để trống; duy nhất sau khi tạo)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `brand:create` — không sửa được sau khi tạo

### 2. Bộ phận đặt hàng (`department`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `brand:write`

### 3. Người quản lý (`manager_id`)

- Kiểu nhập: Chọn nhân sự
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`employee`); API `/api/employees`
- Người sửa: Người dùng có quyền `brand:write`
- Logic: Trả về thêm trường phái sinh `manager_name` (họ tên nhân sự) trong dữ liệu đọc

### 4. Đang dùng (`is_active`)

- Kiểu nhập: Checkbox
- Mặc định: Có (tích)
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `brand:write`

---

## Phòng ban

Cơ cấu tổ chức các phòng ban / bộ phận. Tham chiếu từ PYC (bộ phận yêu cầu), hồ sơ nhân sự và phạm vi dữ liệu trong phân quyền (`dept`). Hỗ trợ phân cấp qua trường `parent`. Hỗ trợ Import/Export CSV.

Đường dẫn: `/departments`.

### 1. Mã phòng ban (`code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có (duy nhất)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `department:create` — không sửa được sau khi tạo (`readonlyOnEdit`)

### 2. Tên phòng ban (`name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `department:write`

### 3. Công ty (`company_id`)

- Kiểu nhập: Nhập số (ID công ty; 0 = không gán công ty cụ thể)
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Công ty (`company`)
- Người sửa: Người dùng có quyền `department:write`

### 4. Phòng ban cha (`parent`)

- Kiểu nhập: Nhập số (ID phòng ban cha; 0 = phòng ban gốc)
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Phòng ban (tự tham chiếu)
- Người sửa: Người dùng có quyền `department:write`

### 5. Trưởng bộ phận (`manager_id`)

- Kiểu nhập: Chọn (SearchSelect)
- Mặc định: trống (0)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`employee`); API `/api/employees`
- Người sửa: Người dùng có quyền `department:write`
- Logic: Trả về thêm trường phái sinh `manager_name` trong dữ liệu đọc

### 6. Trạng thái (`is_active`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: Hoạt động (`true`)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Hoạt động / Đã ẩn
- Người sửa: Người dùng có quyền `department:write`

### Màn chi tiết phòng ban

Bố cục theo cùng mẫu trang chi tiết **Công ty** (`CrudDetail`):

- **Thẻ danh tính đầu trang**: tên phòng ban + dải chip `# mã` · `Trưởng BP: <tên>` · trạng thái.
  Không có ảnh đại diện — phòng ban không có logo để tải lên.
- **Form chia nhóm có tiêu đề**: ĐỊNH DANH (mã, tên) · PHỤ TRÁCH (trưởng bộ phận) · TỔ CHỨC (trạng thái).
  `company_id` và `parent` có trong CSDL + file CSV nhưng **chưa đưa lên form**, chỉ sửa được qua Import CSV.
- **Full chiều ngang, không chia 2 cột** — bên dưới form là thẻ "Nhân sự thuộc phòng" (bảng nhân sự thuộc
  phòng ban, trưởng BP xếp đầu kèm huy hiệu) rồi tới "Lịch sử thao tác". Bảng nhân sự cần trọn bề ngang.

Dữ liệu mẫu: `app/seed.py` (bản LOCAL) nạp sẵn 9 phòng ban `PBA001`–`PBA009` khi bảng còn rỗng —
chạy lại seed không dựng lại phòng ban đã bị xóa trên UI. Bản `seed_prod.py` **không** nạp dữ liệu mẫu này.

---

## Phân công phụ trách

Gán Nhân sự thu mua (NSTM) chính và dự phòng cho từng nhóm phân loại VTBB/NL. Hệ thống dùng bảng này để tự động điền người phụ trách (`assignee`) vào từng dòng PYC khi trưởng phòng duyệt. Mỗi phân loại chỉ được phân công một lần (`item_group_id` là duy nhất); để thay đổi nhân sự cần sửa bản ghi hiện có.

Đường dẫn: `/category-assignees` (trang riêng `CategoryAssignees`).

### Danh sách & bộ lọc

Cột hiển thị: Phân loại · NSTM chính (kèm mã NV) · NSTM dự phòng (kèm mã NV). Danh sách lấy 1 lần rồi **lọc phía client** ngay trên trang riêng (không qua tham số API):

- **Phân loại**: chọn từ danh mục Phân loại (`item_group`)
- **Tìm theo tên NSTM**: khớp tên NSTM chính hoặc dự phòng
- **Tìm theo mã NV**: khớp mã NSTM chính hoặc dự phòng

### 1. Phân loại VTBB (`item_group_id`)

- Kiểu nhập: Chọn (SearchSelect)
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: Bảng Phân loại (`item_group`); API `/api/item-groups`
- Người sửa: Người dùng có quyền `category_assignee:create`
- Logic: `UNIQUE` — mỗi phân loại chỉ có đúng một bản ghi phân công. Không thể tạo thêm khi phân loại đã được gán; cần xóa bản ghi cũ hoặc sửa trực tiếp

### 2. NSTM chính (`primary_employee_id`)

- Kiểu nhập: Chọn (SearchSelect)
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`employee`); API `/api/employees`
- Người sửa: Người dùng có quyền `category_assignee:write`
- Logic: Là nhân sự được ưu tiên giao xử lý PYC / khảo sát khi phân loại của dòng khớp

### 3. NSTM dự phòng (`backup_employee_id`)

- Kiểu nhập: Chọn (SearchSelect)
- Mặc định: 0 (không gán)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`employee`); API `/api/employees`
- Người sửa: Người dùng có quyền `category_assignee:write`

---

## Công ty

Danh sách pháp nhân (công ty hoặc chi nhánh) của tổ chức. Dùng làm bên ký kết trong hợp đồng và làm căn cứ lọc phạm vi dữ liệu (`company`) trong phân quyền. Hỗ trợ phân cấp qua trường `parent`. Hỗ trợ Import/Export CSV.

Đường dẫn: `/companies`.

### 1. Mã (`code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có (duy nhất)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `company:create` — không sửa được sau khi tạo (`readonlyOnEdit`)

### 2. Tên pháp nhân (`name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `company:write`

### 3. Mã số thuế (`tax_code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `company:write`
- Logic: Khi xuất CSV, hệ thống tự thêm dấu nháy đơn trước MST (`'0123456789`) để tránh Excel cắt số 0 đầu

### 4. Địa chỉ (`address`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `company:write`

### 5. Email nhận hóa đơn (`invoice_email`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `company:write`

### 6. Thuộc công ty cha (`parent`)

- Kiểu nhập: Nhập số (ID công ty cha; 0 = pháp nhân gốc)
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Công ty (tự tham chiếu)
- Người sửa: Người dùng có quyền `company:write`

### 7. Người đại diện pháp lý (`legal_representative_id`)

- Kiểu nhập: Chọn (SearchSelect)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`employee`); API `/api/employees`
- Người sửa: Người dùng có quyền `company:write`
- Logic: Trả về thêm trường phái sinh `legal_rep_name` (họ tên) trong dữ liệu đọc

### 8. Chức danh người đại diện (`legal_rep_title`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `company:write`

### 9. Trạng thái (`is_active`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: Đang dùng (`true`)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Đang dùng / Ngừng
- Người sửa: Người dùng có quyền `company:write`

---

## Quyền thao tác (RBAC)

Mỗi danh mục ánh xạ sang một entity trong hệ thống phân quyền. Quyền được cấp theo cặp `(entity, action)` thông qua vai trò.

| Danh mục | Entity | Xem | Tạo | Sửa | Xóa | Xuất CSV | Nhập CSV |
|---|---|---|---|---|---|---|---|
| Nhà cung cấp | `supplier` | `supplier:read` | `supplier:create` | `supplier:write` | `supplier:delete` | `supplier:export` | `supplier:create` |
| Sản phẩm | `product` | `product:read` | `product:create` | `product:write` | `product:delete` | `product:export` | `product:create` |
| Hợp đồng | `contract` | `contract:read` | `contract:create` | `contract:write` | `contract:delete` | — | — |
| Kho | `warehouse` | `warehouse:read` | `warehouse:create` | `warehouse:write` | `warehouse:delete` | `warehouse:export` | `warehouse:create` |
| Đơn vị tính | `unit` | `unit:read` | `unit:create` | `unit:write` | `unit:delete` | `unit:export` | `unit:create` |
| Phân loại | `item_group` | `item_group:read` | `item_group:create` | `item_group:write` | `item_group:delete` | `item_group:export` | `item_group:create` |
| Thương hiệu | `brand` | `brand:read` | `brand:create` | `brand:write` | `brand:delete` | `brand:export` | — |
| Phòng ban | `department` | `department:read` | `department:create` | `department:write` | `department:delete` | `department:export` | `department:create` |
| Phân công phụ trách | `category_assignee` | `category_assignee:read` | `category_assignee:create` | `category_assignee:write` | `category_assignee:delete` | — | — |
| Công ty | `company` | `company:read` | `company:create` | `company:write` | `company:delete` | `company:export` | `company:create` |

Ghi chú:
- Cột "Nhập CSV" dùng quyền `:create` (cùng action với thêm mới đơn lẻ).
- Hợp đồng và Phân công phụ trách không có chức năng Import/Export CSV trong phiên bản hiện tại.
- Thương hiệu có Export CSV (qua `make_crud_router`) nhưng chưa có Import CSV.
- Ngoài các action trên, hệ thống còn định nghĩa thêm `approve`, `cancel`, `print` nhưng không áp dụng cho nhóm danh mục này.
