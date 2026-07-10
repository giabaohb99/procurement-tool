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
| `submitted` | Chờ duyệt | Đã gửi, đợi TP/QL duyệt | Duyệt, Từ chối (TP/QL) |
| `approved` | Đã duyệt | TP/QL đã duyệt, cho phép nhập giao hàng | Thêm lần giao, Hủy đơn |
| `partial` | Đang giao | Đã nhận một phần (tự động khi `received > 0` và `received < total`) | Hủy đơn |
| `received` | Đã nhận đủ | Toàn bộ SL đã nhận | Hoàn thành, Hủy đơn |
| `completed` | Hoàn thành | Đã đóng đơn (khóa sửa hoàn toàn) | Nhân bản |
| `rejected` | Từ chối | TP/QL từ chối (khóa sửa) | Xóa, Nhân bản |
| `cancelled` | Đã hủy | Bị hủy bởi người có quyền cancel (khóa sửa) | Nhân bản |

Luồng trạng thái chính: `draft` → `submitted` → `approved` → `partial` → `received` → `completed`.

Trạng thái `partial` và `received` được cập nhật tự động sau mỗi lần lưu khi đơn đang ở `approved/partial/received`. Đơn ở `completed` hoặc `cancelled` không cho phép sửa; dùng "Nhân bản" để tạo đơn Nháp mới.

Nút "Mở lại" (`reopen`) chuyển đơn về `draft`.

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

- Kiểu nhập: Nhập tay (tự điền từ PYC hoặc nhập trực tiếp)
- Mặc định: trống (tự điền từ `purchase_request.requester` khi chọn PYC)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Hiển thị trên bản in Đơn mua hàng (MH) như "Nhân viên mua hàng".

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
- Logic đặc biệt: Dùng làm `invoice_no` khi hệ thống sinh công nợ hàng (`payable` loại `goods`) cho các lần giao của dòng này.

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
- Mặc định: trống (hiển thị "NCC tự vận chuyển")
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng NCC (`/api/suppliers`) — chỉ NCC có `supplier_type = 'transport'`
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Khi chọn carrier, tự điền `carrier_name`. Khi có carrier và `shipping_amount > 0`, hệ thống tạo công nợ vận chuyển riêng (`payable` loại `shipping`) với số ngày nợ của carrier.

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

---

## F. Quy tắc nghiệp vụ

1. Lưu đơn: dòng hàng không có `product_name` và `product_code` bị loại bỏ trước khi gửi lên BE. Mỗi lần lưu gọi `recompute_effects` để tính lại toàn bộ số liệu và side-effect.
2. Gửi duyệt: bắt buộc điền `misa_code` (kiểm tra ở cả FE và BE); không kiểm tra trường dòng hàng.
3. Duyệt đơn: bắt buộc `misa_code` không trống (kiểm tra ở BE).
4. Từ chối / Hủy: yêu cầu nhập lý do (`reason`); lý do lưu vào `approve_note`.
5. Khóa sửa: đơn `completed` hoặc `cancelled` trả lỗi 400 khi `PATCH`; chỉ cho phép Nhân bản.
6. Nhân bản: tạo đơn Nháp mới từ đơn gốc; giữ dòng hàng nhưng xóa toàn bộ lần giao, số đã nhận, và trạng thái dòng; reset `code`, `misa_code`, `status`.
7. Xóa đơn: BE xóa theo thứ tự deliveries → side-effect → items → attachments → header. Chỉ cho phép khi đơn ở `draft` hoặc `rejected` (kiểm tra ở FE; BE không chặn theo trạng thái ở delete endpoint).
8. Tổng tiền trên header: `subtotal` = SL nhận × đơn giá; `vat` = tiền thuế từ thực nhận; `total` = subtotal + vat; `order_subtotal`/`order_total` = theo SL đặt (dùng cho bản in).
9. Công nợ hàng: sinh khi `received_qty > 0`; xóa khi `received_qty` về 0. Không có VAT riêng ở cấp đơn vị giao — VAT tính từ `po_item.vat`.
10. Công nợ vận chuyển: sinh khi carrier được chọn VÀ `shipping_amount > 0`; xóa khi carrier xóa hoặc `shipping_amount = 0`.
11. Lọc danh sách: hỗ trợ lọc theo `code`, `status`, `supplier_code`, `pr_code`.

---

## G. Quyền thao tác (RBAC)

Entity: `purchase_order`.

| Thao tác | Quyền yêu cầu | Điều kiện trạng thái |
|----------|---------------|----------------------|
| Xem danh sách / chi tiết | `purchase_order:read` | Mọi trạng thái (theo phạm vi dữ liệu scope) |
| Tạo mới / Nhân bản | `purchase_order:create` | — |
| Sửa header, dòng hàng | `purchase_order:write` | Đơn chưa `completed` / `cancelled` |
| Thêm / sửa lần giao | `purchase_order:write` | Đơn ở `approved` / `partial` / `received` |
| Gửi duyệt | `purchase_order:write` | Đơn `draft` |
| Mở lại (về nháp) | `purchase_order:write` | Mọi trạng thái (qua `/reopen`) |
| Đóng đơn (hoàn thành) | `purchase_order:write` | Đơn `received` |
| Duyệt | `purchase_order:approve` | Đơn `submitted` |
| Từ chối | `purchase_order:approve` | Đơn `submitted` |
| Hủy đơn | `purchase_order:cancel` | Đơn `approved` / `partial` / `received` |
| Xóa | `purchase_order:delete` | Đơn `draft` / `rejected` (kiểm tra ở FE) |
| In (cả 2 mẫu) | `purchase_order:print` | Mọi trạng thái |
| Tải lên đính kèm / xóa đính kèm | `purchase_order:write` | Đơn chưa khóa |
