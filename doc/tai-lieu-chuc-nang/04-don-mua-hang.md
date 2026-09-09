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
| `approved` | Đã duyệt | TP/QL đã duyệt, cho phép nhập giao hàng; **nội dung đơn khóa lại** (xem mục "Khóa sửa sau khi duyệt") | Thêm lần giao, Hủy duyệt, Hủy đơn, Nhân bản |
| `partial` | Đã nhận một phần | Đã nhận một phần (tự động khi SL nhận > 0 và < SL đặt) | Hoàn thành, Hủy duyệt, Hủy đơn, Nhân bản |
| `received` | Đã nhận đủ | Toàn bộ SL đã nhận | Hoàn thành, Hủy duyệt, Hủy đơn, Nhân bản |
| `completed` | Hoàn thành | Đã đóng đơn (khóa sửa hoàn toàn) | Nhân bản |
| `rejected` | Bị trả lại | TP/QL trả về để người tạo sửa và gửi duyệt lại (không khóa sửa) | Lưu, Gửi duyệt, Xóa, Nhân bản |
| `cancelled` | Đã từ chối / Đã hủy | Bị từ chối hẳn (từ `submitted` qua nút Từ chối) hoặc bị hủy thủ công (từ `approved`/`partial`/`received` qua nút Hủy) — khóa sửa; badge hiển thị "Đã từ chối" | Nhân bản |

Luồng trạng thái chính: `draft` → `submitted` → `approved` → `partial` → `received` → `completed`. Ngoài ra từ `partial` cũng có thể chuyển thẳng sang `completed` (nút Hoàn thành khi muốn chốt đơn dù chưa nhận đủ).

Trạng thái `partial` và `received` được cập nhật tự động sau mỗi lần lưu khi đơn đang ở `approved/partial/received`. Đơn ở `completed` hoặc `cancelled` không cho phép sửa; dùng "Nhân bản" để tạo đơn Nháp mới.

Nút "Mở lại" (`reopen`) chuyển đơn từ `completed` về trạng thái theo tiến độ nhận thực tế: `received` (đã nhận đủ), `partial` (đã nhận một phần), hoặc `approved` (chưa nhận gì) — không hạ về `draft`. Endpoint: `POST /{id}/reopen`; chỉ áp dụng cho đơn `completed`, hiển thị nút trên trang chi tiết.

### Khóa sửa sau khi duyệt (CR-108)

Từ lúc đơn sang `approved` (và giữ nguyên ở `partial` / `received`), nội dung đơn là thứ TP/QL đã ký — **không sửa được nữa**. Chỉ còn **5 ô phát sinh sau khi duyệt** mở cho người phụ trách:

| Ô còn sửa được | Vì sao mở |
|---|---|
| Tên trên hóa đơn (`invoice_name`) | NCC xuất hóa đơn tên khác tên hàng, chốt được sau khi có hóa đơn |
| Ngày dự kiến có hàng (`expected_date`) | NCC dời lịch giao sau khi đã nhận đơn |
| Kho nhận mặc định (`warehouse_code`) | Điều phối kho đổi theo thực tế nhận hàng |
| Ghi chú (`note`) | Ghi việc phát sinh trong quá trình giao |
| Giao hàng (nhiều lần) | Cả khối lần giao — đây chính là việc sau khi duyệt |

Ngoài ra ô **Ngày giao chứng từ cho KT** (`document_delivery_date`) cũng để mở, dù phiếu hỗ trợ không liệt kê: bước tiến độ "Đã gửi ĐMH cho KT" lấy đúng ô này làm mốc (`_step_ok` trong `purchase_order/service.py`), khóa lại thì dòng hàng không bao giờ đi hết tiến độ được.

Mọi ô còn lại đều khóa: **Mã hàng cho copy nhưng không cho sửa**; ĐVT, SL đặt NCC, Đơn giá, VAT% chỉ đọc. Cũng **không thêm dòng, không xóa dòng**.

Muốn đổi phần đã duyệt thì bấm **"Hủy duyệt"** (`POST /{id}/unapprove`, quyền `purchase_order:approve`, bắt buộc nhập lý do): đơn về **`draft`**, sửa xong phải **Gửi duyệt** rồi **Duyệt** lại — nên đơn nào cũng đi qua đủ cổng kiểm CR-095 một lần nữa. Hủy duyệt bị **chặn** khi:

- có dòng đã nhận hàng (`qty_received > 0`),
- có dòng ở tiến độ "Hoàn thành",
- hoặc đơn đã có yêu cầu thanh toán chưa hủy.

Backend chặn ở `block_edit_approved_order()` (`purchase_order/service.py`) — gửi thẳng PATCH cũng không lách được; giao diện chỉ khóa cho êm tay. Test: `test/backend/test_po_lock_after_approve_cr108.py`.

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
- Logic đặc biệt: Khi chọn mã PYC từ gợi ý, tự điền `department`, `nspt`, `company_id` từ PYC tương ứng (nếu còn trống). **CR-034 — chốt chặn theo trạng thái YCMH:** backend (`_ensure_pr_dispatched`) từ chối tạo đơn (và từ chối đổi `pr_code`) nếu YCMH đang ở `draft` / `submitted` / `approved` / `rejected` — báo *"YCMH … chưa được điều phối (chưa có nhân sự phụ trách)"* — hoặc ở `cancelled` (đã bị từ chối). Chỉ YCMH từ **Đã điều phối** trở đi mới lập được ĐMH. Mã gõ tay không khớp phiếu nào trong hệ thống (dữ liệu cũ) thì không bị chặn.

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
- Tự tính trên form (FE): tự tích nếu có ít nhất 1 dòng mà **"Ngày yêu cầu có hàng" − "Ngày đặt hàng" < số ngày QĐ của phân loại**. Từ CR-065 số ngày QĐ ở đây dùng **mốc dài nhất** (không sẵn hàng, thiếu thì 15 ngày) và **không còn phụ thuộc checkbox "NCC có sẵn hàng"** — kết quả tính cờ gấp rộng hơn trước. Người dùng vẫn tích/bỏ tích tay được.

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

### 18. Loại đơn (`order_type`) — bao-CR-319

- Kiểu nhập: Chọn từ danh sách cố định
- Mặc định: `1` (Trong nước)
- Bắt buộc: Có (server kẹp `1 ≤ order_type ≤ 2`)
- Nguồn dữ liệu / liên kết: `OrderType` IntEnum — `1` Trong nước · `2` Nhập khẩu
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Cột MỚI nên lưu **SMALLINT + IntEnum** theo luật R2/QĐ-11, không lưu chữ. Chọn *Nhập khẩu* mới mở cụm tờ khai hải quan, ô đồng tiền và các ô khối lượng / quy cách trên dòng hàng. Chuyển ngược về *Trong nước* thì giao diện đặt lại đồng tiền = VNĐ, tỷ giá = 1. Danh sách ĐMH chỉ đánh dấu đơn nhập khẩu (đơn trong nước để trống cho gọn) và lọc được qua **Bộ lọc điều kiện → Loại đơn**.

### 19. Đồng tiền đơn hàng (`currency`) — bao-CR-319

- Kiểu nhập: Nhập tay có gợi ý (datalist VND · USD · CNY · EUR · JPY · KRW · THB), chỉ hiện với đơn nhập khẩu
- Mặc định: `"VND"`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Là giá trị MẶC ĐỊNH chép xuống dòng hàng khi dòng không tự khai
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Đồng tiền dùng để tính là đồng tiền **của dòng hàng**, không phải của đơn — một đơn nhập khẩu vẫn lẫn dòng trả bằng tiền Việt (phí nội địa). Ô ở header chỉ là giá trị mặc định.

### 20. Tỷ giá (`exchange_rate`) — bao-CR-319

- Kiểu nhập: Nhập số, tối đa 6 số thập phân; chỉ hiện khi đồng tiền đơn khác VNĐ
- Mặc định: `1`
- Bắt buộc: Không (nhưng để 0 sẽ được hiểu thành 1)
- Nguồn dữ liệu / liên kết: Chép xuống dòng hàng cùng với `currency`
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Mọi chỗ đọc tỷ giá đều đi qua `service.rate_of` — thiếu giá trị hoặc bằng 0 đều trả về 1, vì nhân với 0 sẽ biến cả đơn hàng thành 0 đồng mà không có lỗi nào nổi lên.

### 21. Số tờ khai hải quan (`customs_decl_no`) — bao-CR-319

- Kiểu nhập: Nhập tay, chỉ hiện với đơn nhập khẩu
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) — **sửa được cả sau khi đơn đã duyệt**
- Logic đặc biệt: Nằm trong `ORDER_FIELDS_EDITABLE_AFTER_APPROVAL` (cùng nhóm với `misa_code` và `document_status`) vì tờ khai chỉ có sau khi hàng thông quan, tức luôn muộn hơn bước duyệt đơn. Nhân bản đơn (`copy_po`) **cố ý không chép** số/ngày tờ khai — mỗi lô hàng một tờ khai riêng.

### 22. Ngày tờ khai hải quan (`customs_decl_date`) — bao-CR-319

- Kiểu nhập: Chọn ngày, chỉ hiện với đơn nhập khẩu
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Như `customs_decl_no` — sửa được sau khi duyệt
- Logic đặc biệt: Xem mục 21.

### 23. Số ngày kiểm tra hàng (`inspection_days`) — bao-CR-321

- Kiểu nhập: Nhập tay (số nguyên 0–365), cụm đầu đơn ngay dưới "Hình thức thanh toán NCC"
- Mặc định: 0 = chưa khai; khi chọn NCC (`onPickSupplier`) tự chép giá trị của NCC xuống (`07-danh-muc.md` mục 14), NCC chưa khai thì giữ giá trị đang có trên đơn
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: In ở mục 5 bản in Đơn đặt hàng ("kiểm tra hàng trong vòng N ngày")
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn còn nháp / bị từ chối; **khóa sau khi duyệt** như `payment_terms` (KHÔNG nằm trong `ORDER_FIELDS_EDITABLE_AFTER_APPROVAL` vì là nội dung đã gửi NCC duyệt)
- Logic đặc biệt: Là **bản chép** trên đơn, sửa riêng từng đơn được mà không đụng NCC. Nhân bản đơn (`copy_po`) chép nguyên ba ô. Bản in không đọc thẳng cột này mà đọc `print_terms` do backend gộp (mục E).

### 24. Số ngày thu hồi / đổi trả (`return_days`) — bao-CR-321

- Kiểu nhập: Nhập tay (số nguyên 0–365)
- Mặc định: 0 = chưa khai, chép từ NCC khi chọn
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Mục 5 bản in ("thu hồi, đổi trả trong vòng NN ngày", in hai chữ số)
- Người sửa / Logic: Như mục 23.

### 25. Thời gian nhận hóa đơn (`invoice_deadline`) — bao-CR-321

- Kiểu nhập: Nhập tay, chữ tự do tối đa 255 ký tự
- Mặc định: trống = chưa khai, chép từ NCC khi chọn
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Mục 2 bản in "Thời gian nhận hóa đơn"
- Người sửa / Logic: Như mục 23. Không phải hạn kế toán, không sinh nhắc việc hay ảnh hưởng `document_status`.

---

## B. Dòng hàng (`tab_po_item`)

Mỗi dòng = một sản phẩm/hàng hóa trong đơn. Bảng tóm tắt hiển thị các cột chính; toàn bộ trường xem và sửa trong popup "Chi tiết dòng". Frontend chỉ lưu dòng có `product_name` hoặc `product_code` không trống.

### 1. Mã hàng VTBB/NL (`product_code`)

- Kiểu nhập: Chọn sản phẩm qua ProductPicker (tìm theo mã hoặc tên)
- Mặc định: trống
- Bắt buộc: Không (trường xác định dòng là `product_name`)
- Nguồn dữ liệu / liên kết: Danh mục Sản phẩm (`product`)
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa `completed`/`cancelled`
- Logic đặc biệt: Chọn sản phẩm tự điền `product_name`, `invoice_name`, `unit`, `item_group`, `spec`, `fg_code`, `fg_name`. Dùng làm tham chiếu trong phiếu nhập kho ngầm và tồn kho.
- **DUY NHẤT trên đơn (CR-047)**: mỗi mã hàng chỉ được đứng ở **1 dòng**. Đặt thêm cùng một mã thì **cộng số lượng vào một dòng**. Ô mã trùng tô đỏ ngay khi nhập, bấm Lưu báo `Mã hàng bị trùng: <mã>`. Xem quy tắc 16 mục F.

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

- Kiểu nhập: **Chọn/tìm trong Danh mục Phân loại** (CR-083, trước đó là ô nhập tay); tự điền khi chọn SP. Ô nằm trong popup chi tiết dòng hàng, bảng ngoài không còn cột này (từ 30/06).
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ `product.item_group`; danh sách chọn lấy từ bảng `ItemGroup` (Danh mục > Phân loại VTBB/NL)
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt:
  - Hệ thống dùng `item_group` để tra `std_days` (số ngày quy định giao hàng) từ bảng `ItemGroup` khi tính lại lần giao.
  - **Tra KHÔNG phân biệt hoa/thường và bỏ dấu cách thừa (CR-083).** Dữ liệu sản phẩm còn nhiều tên viết lệch danh mục ("Nhãn thùng" vs "Nhãn Thùng"); trước CR-083 các dòng đó rơi về mặc định 15 ngày nên sai Ngày QĐ và sai cờ Đơn gấp.
  - Dòng cũ ghi lệch hoa/thường thì ô hiển thị theo cách viết của danh mục; phân loại đã bị xóa khỏi danh mục vẫn hiện, kèm chú thích "(ngoài danh mục)".

### 5. Xuất xứ / TSKT / chất liệu (`spec`)

- Kiểu nhập: Nhập nhiều dòng (tự điền khi chọn SP), sửa tay đè lên được
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ **Thông số kỹ thuật** của sản phẩm (`product.specs`)
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt:
  - **Tự điền 2 lớp.** (a) Ngay khi chọn sản phẩm trên giao diện (ô chọn SP ở bảng dòng hàng hoặc trong popup
    "Chi tiết dòng") → điền `product.specs` vào ô này. (b) Lúc **lưu đơn**, backend điền lại cho những
    **dòng MỚI** còn để trống, tra theo `product_code`. Lớp (b) là để ĐMH tạo từ **PYC** cũng có TSKT —
    dòng PYC không có trường `spec` nên nếu chỉ dựa vào (a) thì đơn tạo từ PYC sẽ trống.
  - Backend **chỉ** điền lúc tạo dòng. Sửa đơn mà người dùng cố ý xóa trắng ô này thì giữ nguyên trắng,
    không bị điền đè lại.
  - Hiển thị trên bản in Đơn đặt hàng (cột "Xuất xứ/TSKT/chất liệu").

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
- Logic đặc biệt: **Từ CR-065 ô này KHÔNG còn ảnh hưởng tới `std_days` nữa** — số ngày QĐ luôn lấy mốc dài nhất của phân loại (xem §11 phần lần giao). Ô vẫn giữ để ghi nhận thông tin NCC và phục vụ báo cáo. (Trước CR-065: tích → tra `group.std_days`; không tích → tra `group.std_days_unavail`.)

### 10. Ngày yêu cầu có hàng (`required_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Dùng tính `diff_required` trong lần giao: `regulated_date − required_date`. Giá trị âm = ngày quy định trễ hơn KD yêu cầu.

### 10a. Dự kiến có hàng (`expected_date`) — CR-062

- Kiểu nhập: Chọn ngày (popup chi tiết dòng hàng, ngay dưới "Ngày yêu cầu có hàng")
- Mặc định: trống → khi LƯU, backend tự chép từ dòng YCMH nguồn cùng mã hàng (nếu có)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Hai chiều với **"Thời gian dự kiến có hàng" của dòng YCMH** (`tab_pr_item.expected_date`) — nối theo `PurchaseOrder.pr_code` + `product_code` (không có khóa ngoại; mã hàng là duy nhất trên mỗi phiếu ở cả hai phía)
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt:
  - **Chép xuống:** chỉ điền khi ô còn TRỐNG. Đã có giá trị (nhập tay hay chép từ lần lưu trước) thì giữ nguyên. Đặt ở backend `_save_items` nên nhập khẩu và dòng thêm sau cũng được điền, không chỉ nút "Tạo ĐMH".
  - **Cuộn ngược:** giá trị MUỘN NHẤT trong các dòng ĐMH cùng `pr_code` + mã hàng được đẩy lên dòng YCMH nếu ô bên đó còn trống; nếu bên đó đã có và lệch thì **KHÔNG ghi đè** và hệ thống không tạo thông báo nào. Chi tiết ở [03 §12](./03-yeu-cau-mua-hang.md).
  - **Popup cảnh báo lệch ngày:** khi bấm Lưu đơn, nếu có dòng mà ngày ở đây khác ngày đang ghi trên YCMH thì hiện hộp thoại "Lệch ngày dự kiến có hàng", liệt kê từng dòng (`YCMH dd/mm/yyyy → đơn này dd/mm/yyyy`) và nói rõ ngày trên YCMH sẽ KHÔNG tự đổi theo. Hai lựa chọn: **Vẫn lưu** / **Quay lại sửa**. Ngày YCMH để so sánh do API trả kèm trong trường chỉ-đọc `pr_expected_date` của mỗi dòng.
  - Dòng ĐMH **không gắn YCMH** (`pr_code` trống — đơn tạo tay) hoặc mã hàng không có trên YCMH: nhập tay bình thường, không có gì để cuộn.
  - Cột **"Dự kiến nhận"** ở màn Tiến độ mua hàng đọc từ đây. Trước CR-062 nó đọc `tab_po_delivery.expected_date` — cột đó không nơi nào ghi (chỉ có 10 dòng rác nạp tay), nay **đã bỏ dùng** và đã dọn về rỗng.

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
- Số lẻ: đơn giá lưu và hiển thị **tối đa 4 số thập phân** (đơn giá theo gram / mét hay lẻ tới phần nghìn); ô nhập tự cắt phần lẻ vượt quá 4 số trước khi gửi lên server. **Các cột TIỀN (thành tiền, tổng cộng, công nợ) hiển thị làm tròn về đồng** — kế toán chỉ ghi nhận tới đồng — nhưng giá trị lưu trong CSDL giữ nguyên độ chính xác.

### 15. VAT % của dòng (`vat`)

- Kiểu nhập: Nhập số (%) — **0 ≤ VAT < 100** (CR-058), tối đa 2 số thập phân; ô nhập kẹp về 99,99 ngay khi gõ quá, server chặn lại (`ge=0, lt=100`)
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
- Logic đặc biệt: `remaining_total > 0` khi còn nợ chưa trả; tổng `remaining_total` của tất cả dòng (cộng thêm công nợ vận chuyển, và từ bao-CR-319 P5 cộng thêm công nợ **chi phí lô hàng** `source_type='import_cost'` — xem mục K) tạo thành `unpaid_total` trên header đơn — khi `unpaid_total > 0` mới bật nút Tạo yêu cầu thanh toán.

### 30. Đồng tiền của dòng (`currency`) — bao-CR-319

- Kiểu nhập: Chọn từ danh sách, trong popup Chi tiết dòng; chỉ hiện khi đơn là nhập khẩu hoặc đã có dòng khác VNĐ
- Mặc định: trống ở lớp gửi lên — backend chép từ đồng tiền của ĐƠN xuống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: `PurchaseOrder.currency`
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: `POItemIn.currency` **cố ý để mặc định rỗng** chứ không phải `"VND"` — đặt sẵn VNĐ ở lớp schema thì dòng sinh tự động (tạo ĐMH từ YCMH, nhân bản đơn) sẽ mang cứng VNĐ vào đơn ngoại tệ. `_save_items` điền: dòng không khai thì lấy theo đơn; khai khác đồng tiền của đơn mà không khai tỷ giá thì tỷ giá = 1.

### 31. Tỷ giá của dòng (`exchange_rate`) — bao-CR-319

- Kiểu nhập: Nhập số, tối đa 6 số thập phân; chỉ hiện khi đồng tiền dòng khác VNĐ
- Mặc định: 0 khi gửi lên (nghĩa là "chưa khai") → backend điền theo đơn hoặc 1
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: `PurchaseOrder.exchange_rate`
- Người sửa: NSPT/Người tạo (quyền `purchase_order:write`) khi đơn chưa khóa
- Logic đặc biệt: Đây là tỷ giá THỰC SỰ dùng để quy đổi, đọc qua `service.rate_of` (0 hoặc rỗng đều thành 1).

### 32. Thành tiền quy đổi (`base_amount`) — bao-CR-319

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính, không sửa)
- Nguồn dữ liệu / liên kết: `amount × exchange_rate`
- Người sửa: Hệ thống (tính lại trong `recompute_effects` sau mỗi lần lưu)
- Logic đặc biệt: `price` và `amount` giữ nghĩa **NGUYÊN TỆ**; `base_amount` là bản quy đổi cho báo cáo. **Cấm đặt tên cột kiểu `amount_vnd`** — khóa cứng một loại tiền là sai hướng ngay từ tên cột. Công nợ và tồn kho KHÔNG có cột loại tiền nên `recompute_effects` đẩy sang hai chỗ đó giá đã quy đổi (`price × rate`). Hai chỗ cộng tiền ở phân hệ khác cũng nhân tỷ giá: `dashboard/controller.py::item_amt` và `report/service.py::_amt` / `_recv_amt`. Migration `c5a81b3f6d24` backfill `base_amount = amount` nên dữ liệu VNĐ cũ (tỷ giá 1) không đổi một đồng nào.

### 33. Khối lượng (`weight_kg`) — bao-CR-319

- Kiểu nhập: Nhập số (kg), tối đa 3 số thập phân; chỉ hiện với đơn nhập khẩu
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo — cho sửa cả sau khi đơn duyệt (nhóm `deSau`)
- Logic đặc biệt: Là căn cứ chia chi phí lô hàng theo khối lượng ở phase P4 (phân bổ). Nhập ngay từ P1 để lúc bật phân bổ không phải gõ lại cho các đơn đã có.

### 34. Quy cách / kích thước (`dimension`) — bao-CR-319

- Kiểu nhập: Nhập tay; chỉ hiện với đơn nhập khẩu
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Như `weight_kg`
- Logic đặc biệt: Chỉ để tra cứu và in — không tham gia phép tính nào.

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
- Mặc định: **lấy theo NGÀY QĐ CÓ HÀNG của Phân loại** (CR-065, thay cho CR-063) = `order_date` ("Ngày đặt hàng" của đơn) **+ số ngày QĐ của phân loại dòng hàng** — tức bằng `regulated_date` của lần giao (xem §12). Số ngày QĐ lấy **mốc DÀI NHẤT**: `item_group.std_days_unavail` → thiếu thì `std_days` → thiếu cả hai thì **15 ngày**. Đơn chưa có Ngày đặt hàng thì để trống. Chỉ điền lúc TẠO lần giao, sau đó sửa lại theo cam kết thật của NCC được.
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: `PurchaseOrder.order_date` + `ItemGroup.std_days_unavail`/`std_days` (chỉ ở thời điểm khởi tạo, không đồng bộ tiếp)
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt:
  - Dùng tính `diff_promise = promised_date − received_date`. Giá trị âm = NCC giao trễ so với cam kết.
  - Giá trị mặc định đặt ở CẢ hai nơi: nút "Thêm lần giao" trên giao diện (để NSTM thấy ngay) và `_save_deliveries` ở backend (để lần giao sinh từ nhập khẩu / copy đơn cũng có). Backend chỉ điền khi INSERT — lần giao đã tồn tại mà người dùng xóa trắng ô này thì giữ trắng, không tự điền lại.

### 9. Ngày dự kiến nhận (`expected_date`) — ĐÃ BỎ DÙNG (CR-062)

- Kiểu nhập: — (không có ô nhập nào trên giao diện, chưa từng có)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Không ai — **không nơi nào trong ứng dụng ghi cột này**
- Logic đặc biệt: Cột sinh ra do một cột Excel bị ánh xạ hai lần trong tài liệu yêu cầu; bản được cài thật là `promised_date` ("Cam kết giao"). Cột này chỉ có dữ liệu ở 10 dòng nạp tay ngày 13/07/2026, tất cả cùng một giá trị. Từ CR-062: đã dọn về rỗng, các chỗ đọc (`alert`, `dashboard`, màn Tiến độ) đã chuyển sang `promised_date` hoặc `POItem.expected_date`. **Cột trong DB được GIỮ LẠI, không xóa** (luật "cơ sở dữ liệu cũ: chỉ thêm, không sửa"). Trường "Dự kiến có hàng" mới nằm ở dòng hàng — xem §10a.

### 10. Ngày nhận thực tế (`received_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không (nhưng cần điền để tính chênh lệch và sinh công nợ có ngày phát sinh)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `purchase_order:write` khi đơn đang giao
- Logic đặc biệt: Dùng làm `incur_date` trong công nợ (`payable`). Dùng tính `diff_promise` và `diff_regulated`. Khi `received_date` trống, các cột chênh lệch hiển thị "—".

### 11. Số ngày quy định (`std_days`)

- Kiểu nhập: Nhập số (có thể ghi đè)
- Mặc định (CR-065): ô còn trống thì **tự điền theo Phân loại, lấy mốc DÀI NHẤT** — `ItemGroup.std_days_unavail` (không sẵn hàng) → thiếu thì `std_days` (có sẵn) → thiếu cả hai thì **15 ngày**
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng `ItemGroup` (tra theo `item.item_group`)
- Người sửa: Người có quyền `purchase_order:write`
- Logic đặc biệt (đổi ở CR-065):
  - **Không còn phụ thuộc checkbox "NCC có sẵn hàng"** — luôn lấy mốc dài nhất, để ngày QĐ phản ánh cam kết an toàn nhất.
  - **Ưu tiên số người dùng đã nhập:** dòng giao đã có `std_days > 0` thì `recompute_effects` GIỮ NGUYÊN, chỉ dòng còn trống/0 mới lấy mặc định theo phân loại. (Trước CR-065 thì ngược lại: giá trị `ItemGroup` ghi đè mỗi lần lưu.) Vì vậy các dòng giao cũ giữ nguyên số ngày đang có, chỉ dòng mới hưởng luật mới.

### 12. Ngày quy định (`regulated_date`)

- Kiểu nhập: Tự tính
- Mặc định: trống
- Bắt buộc: — (hệ thống tính)
- Nguồn dữ liệu / liên kết: `order_date + std_days` (ngày đặt hàng cộng số ngày quy định)
- Người sửa: Hệ thống (hiển thị chỉ đọc)
- Logic đặc biệt: Nếu `order_date` hoặc `std_days` trống/0, hiển thị "—". Đây chính là **"ngày QĐ có hàng"** dùng làm giá trị mặc định cho "Cam kết giao" (§8) và cho "Thời gian dự kiến có hàng" bên YCMH (tài liệu 03 mục 12, nhưng bên đó mốc gốc là `request_date`).

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

**Điều khoản in theo NCC (bao-CR-321).** Ba chỗ trên mẫu Đơn đặt hàng từng là chữ cứng — mục 2 "Thời gian nhận hóa đơn: Chậm nhất 24h kể từ khi nhận hàng", mục 5 "kiểm tra hàng trong vòng 15 ngày" và "thu hồi, đổi trả trong vòng 07 ngày" — nay là dữ liệu. Endpoint print trả thêm khóa `print_terms` do `resolve_print_terms(po, sup)` (`purchase_order/service.py`) gộp theo thứ tự **đơn -> NCC -> mặc định** (0 / chuỗi rỗng / toàn khoảng trắng = chưa khai): `{inspection_days, return_days, inspection_days_label, return_days_label, invoice_deadline}`, hai `*_label` là chuỗi hai chữ số để in "07". Gộp ở backend một chỗ để bản in, test và sau này frontend-v2 cùng một logic; `PrintPurchaseOrder.tsx` vẫn giữ mặc định cục bộ phòng API cũ chưa có khóa. Mẫu nội bộ (`PrintPurchaseOrderMH.tsx`) và mẫu nhập khẩu không có cụm điều khoản này nên không đổi. Mặc định giữ nguyên số cũ nên toàn bộ đơn đã có trước CR in ra y hệt. Test: `test/backend/test_po_dieu_khoan_in_cr321.py`.

| Mẫu | File | Trang in | Nội dung chính | Tổng tiền hiển thị |
|-----|------|----------|----------------|-------------------|
| Đơn đặt hàng (gửi NCC) | `PrintPurchaseOrder.tsx` | A4 ngang (landscape) | Bảng hàng theo SL đặt, đơn giá chưa/đã VAT, kho nhận, tên trên HĐ; điều khoản giao nhận + thông tin HĐ | `order_total` (theo SL đặt) |
| Đơn mua hàng (nội bộ) | `PrintPurchaseOrderMH.tsx` | A4 dọc (portrait) | Bảng hàng theo SL yêu cầu + SL thực nhập, tiền thuế GTGT riêng; số tiền bằng chữ; điều khoản NCC | `order_total` (theo SL đặt) + `order_subtotal` tách thuế riêng |

**Tên file khi lưu PDF (CR-057).** Hộp thoại "Save As" do hệ điều hành vẽ, trang web không can thiệp được; thứ duy nhất điều khiển được tên gợi ý là **`document.title`** — trình duyệt và máy in ảo (Foxit, Microsoft Print to PDF) lấy đúng chuỗi đó. Cả 2 mẫu dùng hook `usePrintTitle` (`frontend/src/hooks/usePrintTitle.ts`) đặt tiêu đề tab thành **`<Mã PO>-DDMMYYYY`** (ví dụ `PO00353-31072026`), trả lại tiêu đề cũ khi rời trang. Dùng `code` **chứ không phải `misa_code`** — mã MISA chỉ một phần đơn có và trùng nhau giữa các đơn nhập lại, đặt tên theo nó thì file đè lên nhau. Ngày lấy `order_date` (ngày đơn), **không** lấy ngày bấm in, để in lại lúc nào cũng ra cùng một tên. Tiêu đề tab không lọt lên giấy vì `@page { margin: 0 }` đã bỏ header/footer của trình duyệt. Quy ước này dùng chung cho **cả 4 phiếu in** của hệ thống — 2 mẫu ĐMH ở trên, [phiếu đề xuất YCMH](03-yeu-cau-mua-hang.md) và [phiếu YCTT](05-yeu-cau-thanh-toan.md) (hai phiếu kia lấy `request_date` thay cho `order_date`). Test: `test/e2e/test_print_filename.py`.

Ngoài 2 mẫu trên, phiếu liên quan là **Phiếu đề xuất mua hàng hóa/dịch vụ** (Mẫu 003/BM/PKT, file `PrintPurchaseRequest.tsx`) — là bản in của phiếu YCMH nguồn, mở từ trang chi tiết YCMH (không phải từ trang PO). Bảng hàng hóa trên phiếu đề xuất đã có cột **Nơi giao** hiển thị mã kho nhận (`warehouse_code`) thay vì tên đầy đủ kho (dùng hàm `whCode` tra ngược từ danh mục kho).

---

## F. Quy tắc nghiệp vụ

1. Lưu đơn: dòng hàng không có `product_name` và `product_code` bị loại bỏ trước khi gửi lên BE. Mỗi lần lưu gọi `recompute_effects` để tính lại toàn bộ số liệu và side-effect.
2. Gửi duyệt: bắt buộc điền `misa_code` (kiểm tra ở cả FE và BE). **Từ CR-095 mỗi dòng hàng phải điền đủ 11 ô bắt buộc**: Mã hàng, Phân loại, Tên hàng, Tên trên hóa đơn, Ngày yêu cầu có hàng, Ngày dự kiến có hàng, ĐVT, Kho nhận mặc định, SL yêu cầu, SL đặt NCC, Đơn giá — thiếu ô nào thì BE trả 400 kèm tên dòng và tên ô, FE khóa sẵn nút Gửi duyệt và hiện khối cảnh báo liệt kê. Danh sách nằm ở `REQUIRED_LINE_FIELDS` (`purchase_order/service.py`), FE mirror ở `REQUIRED_LINE_FIELDS`. **VAT KHÔNG bắt buộc** (0 vừa là "chưa nhập" vừa là "không chịu thuế"), các ô còn lại (xuất xứ/TSKT, mã & tên HH thành phẩm, ngày giao chứng từ cho KT, ghi chú) cũng không bắt buộc. Chỉ chặn lúc **Gửi duyệt**, Lưu nháp vẫn lưu được đơn còn thiếu.
3. Duyệt đơn: bắt buộc `misa_code` không trống (kiểm tra ở BE).
4. Từ chối / Hủy: yêu cầu nhập lý do (`reason`); lý do lưu vào `approve_note`.
5. Khóa sửa: đơn `completed` hoặc `cancelled` trả lỗi 400 khi `PATCH`; chỉ cho phép Nhân bản.
6. Nhân bản: tạo đơn Nháp mới từ đơn gốc; giữ dòng hàng nhưng xóa toàn bộ lần giao, số đã nhận, và trạng thái dòng; reset `code`, `misa_code`, `status`, `invoice_no`, `invoice_date` (chứng từ riêng từng đơn, phải nhập lại ở bản sao). `progress_status` của mọi dòng được reset về `"Chưa đặt hàng"`.
7. Xóa đơn: BE xóa theo thứ tự deliveries → side-effect → items → attachments → header. Chỉ cho phép khi đơn ở `draft` hoặc `rejected`; BE trả 400 nếu đơn ở trạng thái khác (không chỉ FE kiểm tra).
8. Tổng tiền trên header: `subtotal` = SL nhận × đơn giá; `vat` = tiền thuế từ thực nhận; `total` = subtotal + vat; `order_subtotal`/`order_total` = theo SL đặt (dùng cho bản in).
9. Công nợ hàng: sinh khi `received_qty > 0`; xóa khi `received_qty` về 0. Không có VAT riêng ở cấp đơn vị giao — VAT tính từ `po_item.vat`.
10. Công nợ vận chuyển: sinh khi carrier được chọn VÀ `shipping_amount > 0`; xóa khi carrier xóa hoặc `shipping_amount = 0`.
11. Tạo yêu cầu thanh toán từ đơn: khi đơn ở `approved`/`partial`/`received`/`completed` và tổng công nợ còn lại (`unpaid_total`) > 0, người dùng có quyền `payment_request:create` thấy nút "Tạo yêu cầu thanh toán". Popup hiện tối đa 3 tab: **NCC sản xuất** (hàng hóa, `source_type='goods'`), **NCC vận chuyển** (`source_type='shipping'`) và — từ bao-CR-319 P5, chỉ khi đơn có khoản nợ loại này — **Chi phí lô hàng** (`source_type='import_cost'`). Tab mở sẵn là tab đầu tiên có khoản nợ. Mặc định chọn sẵn (tick) toàn bộ khoản nợ hàng hóa; khoản nợ vận chuyển / chi phí lô hàng người dùng tự chọn thêm. Gửi lên `POST /api/payment-requests` — server tự tách mỗi cặp (NCC, loại nợ) một phiếu. Với đơn nhập khẩu còn hai đường tạo YCTT nữa ngay trong thẻ chi phí lô hàng (mục K.4).

12. Khóa dòng hoàn thành: dòng hàng có `progress_status = 'Hoàn thành'` hoặc `'Hủy đơn'` bị khóa hoàn toàn — không sửa thông tin sản phẩm, không thêm/sửa/xóa lần giao trong popup chi tiết dòng. Backend bỏ qua (skip) dòng bị khóa khi lưu đơn (không cho phép sửa kể cả qua API).

13. Phạm vi xem đơn theo NSPT: người dùng với scope `assigned` hoặc `proc` thấy đơn mình tạo (`created_by = user.id`) VÀ đơn có `nspt` khớp tên đầy đủ của mình (`emp_name`). Riêng scope `proc` còn thấy thêm mọi đơn đang ở trạng thái `approved` (để nhặt việc phân bổ). **Admin thu mua (`pur_admin`) có scope `all` trên Đơn mua hàng (từ CR-013, 2026-08-04): THẤY + IN mọi đơn của phòng kể cả nháp/chờ duyệt, nhưng KHÔNG có quyền `approve`.** Quản lý thu mua (`pur_manager`) scope `all` và có `approve`.

14. Lọc danh sách: hỗ trợ các bộ lọc sau:
    - LIKE trên header PO: `code`, `status`, `supplier_code`, `pr_code`, `misa_code`, `nspt`, `is_urgent`, `department`, `document_status`
    - Exact match: `company_id`
    - Khoảng ngày: `order_date` (từ–đến)
    - Lọc qua dòng hàng `tab_po_item` (trả về PO có ít nhất một dòng khớp): `item_group` (LIKE), `invoice_no` (LIKE)
    - Danh sách PO còn gắn kèm `pr_id` (ID phiếu YCMH tương ứng `pr_code`) để frontend tạo deep-link điều hướng thẳng sang chi tiết PYC khi click cột "Mã PYC" trong danh sách.

15. Hoàn thành đơn: endpoint `POST /{id}/complete` chỉ chấp nhận khi MỌI dòng hàng đều ở trạng thái tiến độ `"Hoàn thành"` hoặc `"Hủy đơn"`. Nếu còn dòng chưa đạt điểm cuối, BE trả 400 và liệt kê tên sản phẩm còn chưa hoàn thành. Điều này đảm bảo đơn chỉ được đóng khi toàn bộ quy trình (nhập hóa đơn → thanh toán) đã xong cho mọi dòng. Riêng **đơn nhập khẩu** còn phải trả đủ mọi khoản chi phí lô hàng (cước, thuế, phí) mới được đóng — xem mục K.4 luật 8.

16. **Mã hàng duy nhất trên đơn (CR-047)**: một `product_code` chỉ được xuất hiện ở **1 dòng** của đơn. Dòng để trống mã không bị tính trùng.
    - **Vì sao**: dòng ĐMH nối ngược về dòng YCMH bằng **chuỗi `product_code`** chứ không có khóa dòng (mục H.4). `sync_from_purchase_orders` cộng dồn SL đặt/nhận **theo mã** rồi ghi **cùng một con số** vào **mọi** dòng YCMH trùng mã → tiến độ nhân đôi, `line_status` và trạng thái phiếu sai. Ví dụ thật: ĐMH 141 có 8 dòng THC0005 làm dòng YCMH tương ứng hiện "đã đặt 8.000" trong khi chỉ yêu cầu 1.000.
    - **Chỉ chặn TRÙNG MỚI** (số lần một mã xuất hiện **tăng** so với dữ liệu đang lưu): đơn cũ đã lỡ trùng vẫn sửa và lưu lại được. Chặn cứng sẽ khóa chết những đơn đó — dòng ở `Hoàn thành`/`Hủy đơn` bị khóa theo quy tắc 12 và **không có nút xóa**, nên không ai gỡ được dòng trùng ra để lưu.
    - Cài đặt tại `app/core/utils.assert_unique_product_codes`, gọi trong `_save_items` của cả ĐMH lẫn YCMH. Không migration, không sửa dữ liệu cũ — các dòng đã trùng phải **gộp tay**.
    - Muốn bỏ ràng buộc này (hỗ trợ cùng một mã nhận ở **hai Kho** khác nhau) thì phải thêm khóa dòng `tab_po_item.pr_item_id` — xem việc còn nợ **N-004** trong `../tai-lieu-ky-thuat/change-log.md`.

---

## G. Quyền thao tác (RBAC)

Entity: `purchase_order`.

| Thao tác | Quyền yêu cầu | Điều kiện trạng thái |
|----------|---------------|----------------------|
| Xem danh sách / chi tiết | `purchase_order:read` | Mọi trạng thái (theo phạm vi dữ liệu scope — xem quy tắc 13) |
| Tạo mới / Nhân bản | `purchase_order:create` | — |
| Sửa header, dòng hàng | `purchase_order:write` | Đơn `draft` / `rejected`; dòng có `progress_status = 'Hoàn thành'/'Hủy đơn'` bị khóa riêng. Đơn `approved`/`partial`/`received` chỉ còn 5 ô + khối giao hàng (CR-108) |
| Thêm / sửa lần giao | `purchase_order:write` | Đơn ở `approved` / `partial` / `received`; lần giao thuộc dòng đã khóa không sửa được |
| Gửi duyệt | `purchase_order:write` | Đơn `draft` hoặc `rejected` (Bị trả lại) |
| Mở lại (về nháp) | `purchase_order:write` | Mọi trạng thái (qua `/reopen`) |
| Đóng đơn (hoàn thành) | `purchase_order:write` | Đơn `received` hoặc `partial` (nút Hoàn thành xuất hiện ở cả hai) |
| Duyệt | `purchase_order:approve` | Đơn `submitted` |
| Trả về (Bị trả lại) | `purchase_order:approve` | Đơn `submitted`; cần nhập lý do |
| Từ chối (khóa hẳn) | `purchase_order:approve` | Đơn `submitted`; cần nhập lý do; status → `cancelled` |
| Hủy duyệt (về Nháp) | `purchase_order:approve` | Đơn `approved` / `partial` / `received`; cần nhập lý do; status → `draft`; chặn nếu đã nhận hàng / có dòng "Hoàn thành" / có YCTT chưa hủy (CR-108) |
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

> **Ghép theo CHUỖI mã hàng, không theo khóa dòng.** Vì vậy mã hàng phải **duy nhất trên mỗi phiếu/đơn** (quy tắc 16 mục F, CR-047): nếu một mã đứng ở 2 dòng thì tổng SL cộng dồn được ghi vào **cả hai** dòng → tiến độ nhân đôi. Việc còn nợ **N-004** là thay cách ghép này bằng khóa dòng `tab_po_item.pr_item_id`.

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

Màn hình riêng tại đường dẫn `/purchase-progress` (nhãn menu "Tiến độ mua hàng"), sử dụng endpoint `GET /api/purchase-progress`. Hiển thị dạng bảng phẳng, mỗi dòng = 1 dòng hàng (`po_item`) kèm thông tin lần giao tương ứng. Các cột chính: Mã ĐMH, Mã MISA, Mã PYC, Công ty, Bộ phận, NCC, NSPT, Ngày đặt, Mã SP, Tên SP, Tên hóa đơn, Nhóm hàng, Mã HH, Số HĐ, Ngày cần, **Dự kiến nhận** (`po_item.expected_date` — xem §10a; trước CR-062 lấy nhầm từ `po_delivery.expected_date` nên hiện số rác), ĐVT, SL đặt, Đơn giá, Thành tiền đặt, **Tiến độ** (`progress_status`), Lần giao, Kho, Ngày nhận, Ngày quy định, CL cam kết, CL quy định, CL vs YC, Hồ sơ CT (`document_status`). Sắp xếp theo cột; phân trang. Xuất Excel toàn bộ kết quả đang lọc: xem §J.2.

**Lọc (CR-080, CR-081).** Thanh lọc cố định còn 6 ô cơ bản: **Công ty · Bộ phận · Trạng thái tiến độ · Tình trạng nhận · Ngày đặt hàng (khoảng) · Tìm kiếm**. "Tình trạng nhận" bắt buộc ở lại vì là cột TÍNH — cộng dồn số lượng nhận của mọi lần giao, không có cột nào trong DB để lọc trực tiếp; Bộ phận và khoảng Ngày đặt hàng ở lại vì là hai lát cắt dùng gần như mọi lần mở màn (CR-081). Mọi cột còn lại (bộ phận, NSPT, NCC, các mốc ngày, số lượng, tiền…) lọc bằng **Bộ lọc điều kiện** — nút ở cuối thanh lọc, chọn trường + phép so sánh (chứa, bằng, khác, lớn/nhỏ hơn, trong khoảng, đang trống…), nhiều điều kiện nối VÀ / HOẶC. Người không có quyền `supplier.read` thì cụm NCC / vận chuyển không xuất hiện trong danh sách trường, đúng như cột đó bị ẩn trên bảng.

---

## I. Lịch sử mua hàng (`tab_purchase_history`)

Mỗi lần một **dòng hàng vào trạng thái "Hoàn thành"**, hệ thống **chụp lại (snapshot)** dòng đó thành một bản ghi lịch sử mua hàng: mã/tên hàng, NCC, ĐVT, số lượng, đơn giá, VAT, thành tiền, ngày đặt, mã ĐMH… (phần Thông tin chung còn lại giữ trong cột `extra` dạng JSON).

Vì sao chụp lại thay vì đọc thẳng đơn cũ: đơn hàng còn sửa được về sau (đổi giá, đổi số lượng, hủy dòng), còn lịch sử phải là **giá tại thời điểm mua** thì lần sau tham chiếu mới có nghĩa.

**Cách hoạt động**

- Chốt ngay trong bước tự nâng tiến độ dòng nên **phủ cả luồng nhập Excel**, không chỉ thao tác trên giao diện.
- **Một dòng ĐMH chỉ sinh một bản ghi** (`po_item_id` là khóa duy nhất) — chạy lại không nhân đôi.
- Lỗi khi chốt lịch sử **không chặn** luồng tiến độ mua hàng: dòng vẫn Hoàn thành bình thường.
- Dòng chỉ vào "Hoàn thành" khi **công nợ đã trả đủ** → công nợ phân bổ sai thì lịch sử cũng không được chốt (xem CR-044 trong `change-log.md`).

**Xem ở đâu**

| Nơi xem | Nội dung |
|---|---|
| Chi tiết **Sản phẩm** → tab *Lịch sử mua hàng* | Mặt hàng này từng mua của những NCC nào, giá bao nhiêu, lần nào |
| Chi tiết **Nhà cung cấp** → tab *Lịch sử mua hàng* | NCC này từng bán những gì, giá bao nhiêu |
| **Ô Mã hàng** trên dòng ĐMH và dòng YCMH | Nút mở popup lịch sử để **tham chiếu giá lúc lập đơn** |

Popup tham chiếu giá: 20 dòng/trang, có tìm kiếm + phân trang; chọn 1 dòng thì **điền ĐVT / SL / đơn giá / VAT vào dòng hàng nhưng KHÔNG tự lưu** — người lập đơn còn soát lại rồi mới Lưu. Nút hiện khi dòng **đã chọn mã hàng**, ở **mọi trạng thái đơn** (CR-096) — đơn đang Chờ duyệt chính là lúc người duyệt cần đối chiếu giá cũ nhất. Dòng không còn sửa được thì popup mở ở **chế độ chỉ xem**: vẫn thấy đủ giá cũ nhưng không có đường "Dùng giá này".

**Dữ liệu cũ (trước khi có hệ thống)**

Lịch sử còn được nạp thêm từ file khảo sát cũ, đánh dấu **nguồn `legacy`**:

- Cột ĐMH hiển thị **"Dữ liệu cũ"** và **không bấm vào được** — vì không có đơn thật trong hệ thống để mở.
- Có khóa chống nạp trùng, chạy lại script không nhân đôi dữ liệu.
- Dữ liệu nguồn có lỗi đã được xử lý khi nạp: giá ghi bằng nghìn đồng, số lượng vô lý, ngày gõ sai/đảo ngày-tháng, NCC và mã hàng chưa có trong danh mục.

**Quyền xem**: theo quyền đọc của danh mục tương ứng — `product.read` cho lịch sử theo sản phẩm, `supplier.read` cho lịch sử theo nhà cung cấp.

---

## J. Xuất Excel danh sách (CR-068)

### J.1 Màn Đơn mua hàng

Nút **"Xuất Excel"** trên thanh công cụ màn danh sách ĐMH, chỉ hiện với người có hành động
**`export`** trên `purchase_order`. Endpoint: `GET /api/purchase-orders/export/xlsx`.

- Đúng **bộ lọc + thứ tự sắp xếp** đang áp và đúng **các cột đầu đơn đang hiển thị**; không tick
  dòng nào thì xuất **toàn bộ kết quả đang lọc**, tick thì chỉ xuất đơn đã tick.
- **Khối cột dòng hàng dùng đúng bộ cột của màn Tiến độ mua hàng** (yêu cầu khách): mỗi hàng Excel là
  **một lần giao** của một dòng hàng, có đủ khối kho/vận chuyển/ngày nhận/chênh lệch như §J.2.
  Dòng hàng chưa có lần giao nào vẫn ra một hàng (phần giao để trống); đơn chưa có dòng hàng cũng vậy.
- Cụm đầu đơn lặp lại ở mọi hàng nên **không cộng thẳng cột "Tiền hàng"** — lọc *STT dòng = 1* rồi mới
  cộng. "STT dòng" đánh số **liên tục theo hàng trong đơn** (dòng hàng 2 lần giao chiếm STT 1 và 2).
- Cột **"Nhà cung cấp"** (đầu đơn) lấy mã NCC, thiếu mã mới rơi về tên (giống cột trên bảng); cột
  **"Tên NCC"** trong khối dòng là tên đầy đủ.
- **Che dữ liệu**: người không có `supplier:read` thì file **bỏ hẳn** các cột Tên NCC · Mã ĐVVC ·
  Đơn vị VC · Đơn giá VC · Tiền VC (cột "Nhà cung cấp" của đầu đơn vẫn giữ, vì nó là cột mặc định
  của bảng ĐMH).

**Ba cột tiền, đừng nhầm:**

| Cột | Công thức | Dùng khi |
|---|---|---|
| **Tiền hàng** (đầu đơn) | tổng *Thành tiền ĐH* của các **dòng hàng**, tính một lần nên không nhân theo lần giao | Khớp cột trên bảng danh sách |
| **Thành tiền ĐH** (dòng) | SL đặt × đơn giá × (1 + VAT%) | Giá trị đã đặt của dòng |
| **Thành tiền nhận** (dòng) | SL **thực nhận của lần giao đó** × đơn giá × (1 + VAT%) | Con số ghi công nợ |

Số liệu dòng do `purchase_progress.export.row_values` tính — **cùng một chỗ** với màn Tiến độ, nên hai
file không bao giờ lệch nhau.

Khối cột dòng: STT dòng · Công ty · Bộ phận · Tên NCC · NSPT · Ngày ĐH · Mã SP · Tên SP · Tên hóa đơn ·
Nhóm hàng · Quy cách · Mã HH · Số HĐ · Ngày cần · Dự kiến nhận · ĐVT · SL YC · SL đặt · Đơn giá · VAT% ·
Thành tiền ĐH · Tiến độ · Lần giao · Kho · Mã ĐVVC · Đơn vị VC · SL giao · SL nhận · Cam kết giao ·
Ngày nhận · Ngày QĐ · Ngày quy định · CL cam kết · CL quy định · CL vs YC · Số HĐ (giao) · Đơn giá VC ·
Tiền VC · QC · TT giao · Thành tiền nhận · SL còn lại · Trạng thái dòng · Ghi chú dòng.

Tên file `don-mua-hang-DDMMYYYY.xlsx`. Quy ước định dạng và trần 5.000 dòng/lần xuất — xem
[03-yeu-cau-mua-hang.md §G](03-yeu-cau-mua-hang.md).

### J.2 Màn Tiến độ mua hàng

Nút **"Xuất Excel"** đặt cạnh dòng đếm *"· N dòng"* ở đầu màn `/purchase-progress`.
Endpoint: `GET /api/purchase-progress/export/xlsx`. Màn này vốn đã phẳng (một hàng = **một lần giao**
của một dòng hàng) nên file ra **đúng bảng đang xem**: cùng bộ lọc, cùng thứ tự, **đúng các cột đang
hiển thị và đúng thứ tự cột người dùng đang thấy**, kèm cột STT.

- **Quyền**: cần hành động `export` của **Đơn mua hàng HOẶC Yêu cầu mua hàng** — vì màn này phục vụ
  cả người theo dõi tiến độ phía yêu cầu.
- **Che dữ liệu**: người không có `purchase_order:read` thì file **bỏ hẳn** các cột Mã NCC · Nhà cung cấp ·
  Mã ĐVVC · Đơn vị VC · Đơn giá VC · Tiền VC — đúng như bảng đang che.

Tên file `tien-do-mua-hang-DDMMYYYY.xlsx`.

**Ai được xuất.** Vai trò chuẩn có sẵn ô "Xuất" của ĐMH: *Quản lý công ty · NV thu mua · Admin thu mua ·
Quản lý thu mua · Quản trị hệ thống*. Màn Tiến độ nhận thêm cả người có "Xuất" của YCMH (Trưởng phòng…).
Vai trò **"Nhân sự"** (người yêu cầu thường) **KHÔNG** được xuất ở bất kỳ màn nào — muốn cho ai đó xuất
thì tạo một **vai trò riêng** chỉ tick ô "Xuất" của màn tương ứng rồi gán thêm cho người đó. Vai trò
**tự tạo tay** cũng phải tick ô "Xuất" mới thấy nút.

---

## K. Đơn nhập khẩu — chi phí lô hàng (`tab_po_import_cost`) — bao-CR-319 P3..P5

Chỉ áp cho đơn có `order_type = 2` (Nhập khẩu, mục A.18). Thẻ **"Chi phí lô hàng nhập khẩu"** nằm ngay
dưới bảng Dòng hàng trên màn chi tiết ĐMH, gồm: bảng chi phí phẳng (K.1) · dải thẻ số (K.3) · khối
"Thanh toán chi phí theo nhà cung cấp" (K.4) · panel "Chi phí theo dòng hàng" chỉ đọc (K.2).

**Ranh giới.** Đây là landed cost nhưng hệ CHƯA có phân hệ hóa đơn nên **không tính giá vốn / giá nhập
kho, không lưu kết quả phân bổ xuống cột nào** — chỉ lưu chi phí, sinh công nợ và in báo cáo. Vài đơn
một năm nên không làm custom-field engine.

### K.1 Bảng chi phí (P3)

Mỗi dòng là **một khoản chi phí của một nhà cung cấp** (hãng tàu · đơn vị khai thuê · kho bãi · bảo
hiểm · *Ngân sách nhà nước* cho các khoản thuế). NCC khai ở **từng dòng**, không lấy theo NCC bán hàng
của đơn. Bảng **mở cả khi đơn đã duyệt** (`block_edit_approved_order` bỏ qua khóa `import_costs`) vì
hóa đơn cước, tờ khai thuế, phí lưu bãi đều về sau ngày duyệt.

| Cột | Ý nghĩa / luật |
|-----|----------------|
| `cost_type` | SMALLINT + IntEnum `ImportCostType`: 1 Cước vận tải quốc tế · 2 Phí địa phương tại cảng · 3 Phí dịch vụ hải quan · 4 Thuế nhập khẩu · 5 Thuế GTGT hàng nhập · 6 Thuế TTĐB · 7 Thuế BVMT · 8 Kiểm tra chuyên ngành · 9 Bảo hiểm · 10 Vận chuyển nội địa · 11 Lưu kho/bãi · 99 Khác. Mã lạ đẩy về 99. Chọn nhóm thuế (4..7) thì giao diện tự điền NCC `NSNN` *Ngân sách nhà nước* (seed ở migration `ed610675320b`, `downgrade` cố ý giữ lại vì có thể đã gắn công nợ thật). **Loại chi phí ĐƯỢC TRÙNG trong một đơn** (cố ý, khách hỏi 09/09): một dòng = một hóa đơn của một NCC, nên hai hóa đơn cước của hai chặng, hay hai lần lưu bãi, là hai dòng cùng loại. |
| `description` | Diễn giải tự do. Ô trên bảng **xuống dòng và cao theo nội dung** (như Tên hàng), không cắt chữ; Ghi chú cũng vậy (09/09). |
| `supplier_code` / `supplier_name` | NCC nhận tiền của khoản này. Trống thì dòng vẫn lưu nhưng **không sinh công nợ** (K.4). |
| `currency` / `exchange_rate` | Cùng đồng tiền với đơn thì theo tỷ giá đơn; **khác đồng tiền thì tỷ giá = 1, không mượn tỷ giá đơn** (chi phí VNĐ trong đơn USD mà nhân 25.000 là phồng lên 25.000 lần). |
| `amount` | Tiền **nguyên tệ TRƯỚC thuế**. |
| `vat` | % thuế GTGT của khoản chi phí (0 với các dòng thuế nộp ngân sách). |
| `base_amount` | = `amount × (1 + vat%) × tỷ giá` — **đã gồm VAT, đã quy đổi**. Tính phía server (`import_cost_base`). Không đặt tên kiểu `amount_vnd` (xem B.32). |
| `allocation_method` | SMALLINT + IntEnum `AllocationMethod`: 1 theo giá trị (mặc định) · 2 theo khối lượng (`weight_kg`) · 3 theo số lượng (`qty_order`) · 4 chỉ định một mã hàng · 5 **nhập tay** (09/09). Chọn 4 mà bỏ trống mã thì hạ về 1. Cột hiện ngay sau Diễn giải để không bị đẩy khuất ngoài màn hình. |
| `allocation_target` | Mã hàng đích khi chọn cách 4. Là **mã** chứ không phải id dòng vì dòng ĐMH được phép trùng mã. |
| `manual_allocation` | TEXT JSON `{"<id dòng hàng>": số tiền VNĐ}`, chỉ dùng khi chọn cách 5 (cách khác lưu rỗng). Đây là cách chia **duy nhất phải lưu kết quả** vì con số do thu mua gõ để cân với chứng từ, không suy ra được từ dữ liệu khác. Khóa là **id dòng** (không phải mã hàng) vì gõ tay thì mỗi dòng một số kể cả trùng mã; khóa của dòng đã xóa bị bỏ khi lưu. Tổng các dòng phải bằng `base_amount` (dung sai 1 đ), lệch hoặc chưa gõ dòng nào thì **400** ngay lúc Lưu. Migration `b7e2c4d9a1f3`. |
| `invoice_no` / `invoice_date` | Số và ngày hóa đơn của khoản chi phí → chép sang công nợ (`invoice_no`, `incur_date`). |
| `payment_due_date` | Hạn thanh toán của khoản; có thì **ưu tiên** hơn hạn tính từ điều khoản NCC. |
| `note` | Ghi chú. |

Quy ước API: payload `PATCH` **không gửi** khóa `import_costs` (`None`) = *không đụng bảng*; gửi mảng
rỗng `[]` = *xóa hết*. Hai nghĩa khác nhau — gộp lại thì mọi lần lưu lần giao đều quét sạch bảng chi phí.

**Khóa VAT dòng hàng = 0 ở BACKEND** (`_save_items`) cho đơn nhập khẩu, không chỉ ẩn trên giao diện:
hóa đơn NCC nước ngoài không có thuế GTGT Việt Nam; thuế GTGT hàng nhập nộp ngân sách theo tờ khai và
đã khai thành một dòng chi phí. Để người dùng gõ VAT ở dòng hàng nữa là cộng thuế HAI LẦN và ghi nợ
khoản thuế đó cho chính người bán. Đơn trong nước không đổi.
Giao diện đơn nhập khẩu **ẩn hẳn** VAT dòng hàng (khách yêu cầu 09/09/2026, đỡ hai cột vô nghĩa): cột
*VAT%* + *Đơn giá (Sau VAT)* ở bảng dòng hàng, hai ô cùng tên ở popup chi tiết dòng, cột *VAT%* ở bảng lần
giao đều `!isImport`; bản in NK khối A vốn không có cột này. Đơn trong nước hiện như cũ. Backend vẫn ép 0
nên ẩn giao diện không làm lọt thuế.

### K.2 Phân bổ chỉ để xem (P4)

Hàm thuần `service.allocate_import_costs(items, costs)` chạy trong `_out` (khóa `import_cost_allocation`)
nên màn hình, bản in và YCTT đọc cùng một con số. **Không lưu, không đẩy vào kho.** Cơ sở chia cộng lại
bằng 0 (chưa gõ kg, SL 0, mã chỉ định không có trên đơn) thì **lùi về theo giá trị**, giá trị cũng 0
thì chia đều; khi lùi ghi `warnings` + `effective_method` khác `allocation_method` để giao diện / bản in
đánh dấu (*) chứ không đổi cách trong im lặng. Làm tròn 2 số lẻ, phần lệch **dồn vào dòng hàng cuối**
trong số các dòng nhận khoản đó nên tổng luôn khớp. Panel "Chi phí theo dòng hàng" lồng NGƯỢC: dòng hàng
là CHA, mở ra thấy từng khoản + cách chia + tỷ lệ; tính từ dữ liệu ĐÃ LƯU nên có dòng nhắc "sửa xong bấm
Lưu", kèm nút *Mở tất cả / Thu gọn*. Nhãn cột cố ý không dùng chữ "gánh": *Chi phí phân bổ* · *Tỷ lệ chi
phí* · *Số tiền (đ)* (09/09, theo góp ý khách).

**Cách 5 "Nhập tay" (09/09, khách chốt):** thu mua thường phải gõ tay để cân số với chứng từ. Chọn *Nhập
tay* ở cột Cách phân bổ thì bảng "Chi phí theo dòng hàng" tự mở mọi dòng, trong mỗi dòng hàng hiện thêm
một dòng con nền vàng có **ô gõ số tiền** cho khoản đó (số đang chia theo cách cũ được điền sẵn để chỉ
sửa vài dòng cần cân); dải báo trên panel cộng sống *đã nhập / phải bằng / lệch*. **Chỉ có hiệu lực khi
bấm Lưu của đơn** — không có nút lưu riêng, đúng ý khách "sửa điều kiện thì phải bấm Lưu". Giao diện chặn
sớm khi lệch, backend chặn thật (400) trong `_save_import_costs`. Lúc xem, `allocate_import_costs` vẫn kiểm
lại: tổng khớp thì dùng nguyên số đã gõ (`effective_method = 5`, tỷ lệ = số gõ / khoản), dòng không gõ thì
không nhận khoản; lệch (dòng hàng bị xóa sau đó, số tiền khoản đổi) thì lùi về theo giá trị + `warnings`
như các cách khác. Giữ nguyên "Chỉ định một mã hàng" một mã; không làm popup, không gõ tay tỷ lệ.

**Popup chi tiết một khoản chi phí (09/09, khách yêu cầu "như dòng hàng"):** cột cuối bảng chi phí đổi
thành *Hành động* gồm cây bút (mọi trạng thái) và thùng rác (chỉ khi còn sửa được). Cây bút mở popup
*Chi tiết chi phí #n* bày đủ mọi trường theo dạng form hai cột (loại · NCC · diễn giải · tiền tệ · tỷ giá
· số tiền · VAT · quy đổi · cách phân bổ · mã chỉ định / tình trạng nhập tay · số và ngày hóa đơn · hạn
thanh toán · công nợ đã chi / còn lại · ghi chú). Popup **dùng chung state với bảng** (`setCost`): sửa ở
đâu cũng là một, và vẫn phải bấm **Lưu của đơn** như mọi thay đổi trên bảng; đơn khóa thì popup chỉ xem.
Đầu popup ghi vì sao dòng chưa thành công nợ (dòng mới chưa Lưu · chưa chọn NCC hoặc tiền 0 · đơn chưa
duyệt) để thu mua khỏi đoán.

Bản in thứ ba **"In Đơn nhập khẩu"** (`PrintPurchaseOrderImport.tsx`, route
`/print/purchase-order-import/:id`, chỉ hiện với đơn NK) gồm 4 khối: A hàng hóa (nguyên tệ + quy đổi,
cột kg, VAT 0) · B chi phí lồng hai tầng theo loại kèm NCC · C phải trả theo từng NCC (NCC bán hàng +
`import_cost_summary.by_supplier`) · D chi phí chia về dòng hàng. Hai mẫu in ở mục E không đụng.

### K.3 Dải thẻ số

Năm thẻ ngay dưới bảng chi phí: **Tiền hàng quy đổi** (`goods_base_total`) · **Tổng chi phí NK**
(`cost_total`, kèm % so tiền hàng) · **Đã chi** (`paid_total`) · **Còn phải chi** (`remaining_total`) ·
**Tổng giá trị lô hàng** (`landed_total` = tiền hàng + chi phí). Hai thẻ Đã chi / Còn phải chi chỉ hiện khi đơn đã đủ điều kiện sinh nợ
(K.4) hoặc đã có tiền chi. Số lấy từ `import_cost_summary` trả về trong `_out`.

### K.4 Công nợ từng dòng chi phí + Yêu cầu thanh toán (P5)

Dùng lại bảng `tab_payable` — **không dựng luồng công nợ thứ hai**. Mỗi dòng chi phí thành **một khoản
nợ** `source_type = ref_type = 'import_cost'`, `ref_id` = id dòng chi phí, `po_id`/`po_code` = đơn.
Nhãn hiển thị "Chi phí nhập khẩu" dùng chung ở màn Công nợ, YCTT, dashboard NCC, xuất Excel
(`frontend/src/utils/payable.ts`, `payable/export.py`).

Luật đồng bộ (`sync_import_cost_payables`, idempotent, gọi sau mỗi lần lưu bảng chi phí và mỗi lần đổi
trạng thái đơn):

1. Đơn ở `approved` / `partial` / `received` / `completed` (`IMPORT_COST_PAYABLE_STATUSES`) mới sinh nợ.
   Nháp / chờ duyệt là số ước tính; hủy / từ chối thì không còn gì phải trả.
2. Dòng 0 đồng hoặc chưa khai NCC không thành nợ; đang có nợ mà bỏ NCC → gỡ nợ (nếu chưa chi).
3. `amount` công nợ = gốc trước VAT đã quy đổi, `vat` = tiền thuế, `total` = `base_amount` — cùng quy
   ước với nợ hàng. `incur_date` = ngày hóa đơn của dòng, trống thì lấy ngày đặt hàng. `due_date` ưu tiên
   `payment_due_date` của dòng, trống thì tính theo điều khoản NCC (`debt_days`).
4. Sửa số tiền / NCC / hóa đơn của dòng → cùng khoản nợ cập nhật theo (khóa theo `ref_id`).
5. **Dòng đã chi (paid_amount > 0) thì cấm xóa** (`block_delete_paid_import_cost`, 400 "đã chi") — xóa là
   mất chỗ đối chiếu số đã trả. Sửa số tiền hoặc ghi chú thay vì xóa.
6. Hủy / từ chối đơn: gỡ khoản nợ chưa chi, **giữ** khoản đã chi (cùng cách với nợ hàng khi hủy đơn).
7. `unpaid_total` trên header cộng cả phần còn lại của nợ chi phí (B.29). Báo cáo công nợ theo ngày
   (`report/controller.py`) cộng nợ chi phí vào tổng nhưng **không đếm vào cột hàng**.
8. **Đơn NHẬP KHẨU chỉ được Hoàn thành khi trả đủ chi phí lô hàng** (`block_complete_unpaid_import_costs`,
   gọi trong `POST /{id}/complete` sau khi đã kiểm dòng hàng; khách chốt "mức chặt" 09/09/2026). Duyệt từng
   dòng chi phí có tiền: chưa thành công nợ (chưa chọn NCC / chưa Lưu đơn) hoặc còn lại > 0,01 đ (tính
   `total - paid_amount`, không đọc cột `remaining` tính sẵn) → 400 liệt kê từng khoản "Diễn giải (NCC): còn
   X đ". **Đơn trong nước không đổi** (chi phí lô hàng vốn không có). Giao diện: hộp xác nhận Hoàn thành nhắc
   trước số còn lại (`import_cost_summary.remaining_total`) để khỏi bấm rồi ăn lỗi. Tiến độ từng dòng hàng
   vẫn chỉ xét nợ hàng (`is_line_paid`), nên dòng hàng có thể "Hoàn thành" trước khi đơn đóng được.

Tạo YCTT từ nợ chi phí — **YCTT chỉ nhận một NCC / một loại nợ mỗi phiếu**, nên có ba đường, cả ba đều
đưa về `/payment-requests/new?payables=<id,id,...>` và server tự tách phiếu:

- **Khối "Thanh toán chi phí theo nhà cung cấp"**: mỗi NCC một dòng Số khoản · Phải trả · Đã chi · Còn lại
  và nút **Tạo YCTT** riêng (gửi `unpaid_payable_ids` của NCC đó); chi đủ rồi thì hiện "Đã chi đủ". Đây là
  đường chính — bấm là ra phiếu hợp lệ, khỏi tick tay rồi bị chặn.
- **Tick trên bảng chi phí**: cột checkbox đầu bảng (chỉ dòng đã có nợ và còn phải chi) + nút **"Tạo YCTT
  (n dòng đã tick)"** trên đầu thẻ; tick nhiều NCC thì server tách mỗi NCC một phiếu.
- **Popup "Tạo yêu cầu thanh toán"** của đơn: tab thứ ba *Chi phí lô hàng* (quy tắc F.11).

Cả ba chỉ hiện khi đơn đủ điều kiện sinh nợ và người dùng có `payment_request:create`. Bảng chi phí có
thêm hai cột **Đã chi** / **Còn lại** đọc từ khoản nợ (dòng chưa thành nợ hiện "—" và Còn lại = `base_amount`).

Phía YCTT: `check_submit` vẫn bắt mỗi dòng có Số hóa đơn (gõ ngay trên phiếu được); khớp khoản nợ theo
(NCC, loại, mã ĐMH, số HĐ) như cũ, dòng `import_cost` không khớp được thì lùi về khớp theo `payable_id`
của dòng (nhiều dòng chi phí cùng ĐMH có thể chưa có số HĐ lúc lập phiếu). Chi tiền (`paid`) trừ đúng
khoản nợ của từng dòng chi phí. Phiếu gõ tay chấp nhận `source_type = 'import_cost'`.

**Test:** `test_po_tien_te_cr319.py` (P1) · `test_po_chi_phi_nhap_khau_cr319.py` (P3) ·
`test_po_phan_bo_chi_phi_cr319.py` (P4) · `test_po_cong_no_chi_phi_cr319.py` (P5). Dữ liệu thử local:
`backend/scripts/seed_demo_import_po.py`.
