# Tồn kho & Công nợ

---

# Tồn kho

## Mục đích

Theo dõi số lượng và giá trị hàng hóa đang tồn tại từng kho của từng pháp nhân. Tồn kho được cập nhật tự động khi nhân viên ghi nhận số lượng thực nhận trên đơn mua hàng; ngoài ra có thể điều chỉnh tay (tăng hoặc giảm) với lý do ghi rõ.

Đường dẫn: `/inventory` (danh sách tồn kho).

Bảng DB chính: `tab_inventory` (1 dòng = 1 bộ khóa công ty + kho + sản phẩm). Bảng phụ: `tab_inventory_move` (sổ phát sinh nhập/xuất — nguồn tính toán giá bình quân).

## Vai trò tham gia

- Người xem (`inventory:read`): xem danh sách tồn kho và bộ lọc.
- Người điều chỉnh (`inventory:write`): thực hiện điều chỉnh tồn tay qua form popup.
- Hệ thống (service nội bộ): tự động ghi nhập kho khi lưu số lượng nhận trên đơn mua hàng (không cần quyền người dùng).

---

## A. Màn hình Tồn kho (bảng xem)

Màn hình chỉ đọc hiển thị trạng thái tồn hiện tại. Không có form tạo/sửa dòng trực tiếp — mọi thay đổi đến từ nhận hàng (tự động) hoặc điều chỉnh tay (popup).

### 1. Công ty (`company_id`)

- Kiểu nhập: Bộ lọc — Chọn (ô tìm kiếm, gợi ý tên công ty)
- Mặc định: Tất cả (không lọc)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng `company`
- Người sửa: Người dùng tự chọn để lọc; hệ thống ghi khi nhận hàng
- Logic đặc biệt: Truyền thêm query param `company_id` vào API; scope RBAC tự giới hạn theo phạm vi công ty của user

### 2. Kho (`warehouse_code`)

- Kiểu nhập: Bộ lọc — Chọn (ô tìm kiếm, hiển thị "mã — tên")
- Mặc định: Tất cả (không lọc)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng `warehouse`
- Người sửa: Người dùng tự chọn để lọc; hệ thống ghi khi nhận hàng (lấy từ dòng giao hoặc dòng hàng PO)
- Logic đặc biệt: Cột hiển thị trong bảng kết quả, đồng thời là chiều lọc

### 3. Mã sản phẩm (`product_code`)

- Kiểu nhập: Bộ lọc — Nhập tự do (LIKE)
- Mặc định: Trống (không lọc)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Danh mục sản phẩm (`product`)
- Người sửa: Người dùng tự nhập để lọc; hệ thống ghi khi nhận hàng
- Logic đặc biệt: Lọc bằng LIKE (chứa chuỗi); đây là một trong ba cột `FILTERABLE` của module (`warehouse_code`, `product_code`, `product_name`)

### 4. Tên sản phẩm (`product_name`)

- Kiểu nhập: Chỉ hiển thị (cột bảng)
- Mặc định: — (do hệ thống điền từ dữ liệu nhận hàng)
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Lấy từ `POItem.product_name` khi nhận hàng hoặc từ form điều chỉnh
- Người sửa: Hệ thống (không sửa trực tiếp trên màn tồn kho)
- Logic đặc biệt: Cũng là cột `FILTERABLE` — bộ lọc LIKE có thể áp vào tên sản phẩm nếu truyền query param `product_name`

### 5. Đơn vị tính (`unit`)

- Kiểu nhập: Chỉ hiển thị (cột bảng)
- Mặc định: — (do hệ thống điền)
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Lấy từ `POItem.unit` hoặc `product.unit` khi nhận hàng / điều chỉnh
- Người sửa: Hệ thống
- Logic đặc biệt: Đơn vị tính đi kèm cột Tồn hiện tại

### 6. Tồn hiện tại (`qty`)

- Kiểu nhập: Chỉ hiển thị (cột bảng, in đậm)
- Mặc định: 0
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Tổng hợp từ `tab_inventory_move` — `qty = SUM(move.qty)` (dương = nhập, âm = xuất/điều chỉnh giảm)
- Người sửa: Hệ thống (tính lại mỗi khi có phát sinh mới)
- Logic đặc biệt: Số này là kết quả tính toán lưu sẵn (`_recompute`), không phải tổng live; được làm tròn 3 chữ số thập phân

### 7. Đơn giá bình quân (`avg_cost`)

- Kiểu nhập: Chỉ hiển thị (cột bảng)
- Mặc định: 0
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Tính theo phương pháp bình quân gia quyền: `avg_cost = SUM(move.qty × move.unit_price) / SUM(move.qty)`
- Người sửa: Hệ thống (tính lại sau mỗi phát sinh)
- Logic đặc biệt: Điều chỉnh tay dùng `avg_cost` hiện tại làm `unit_price` cho phát sinh mới (giữ nguyên trị giá bình quân, chỉ thay đổi số lượng); khi `qty = 0` thì `avg_cost = 0`

### 8. Giá trị tồn (`value`)

- Kiểu nhập: Chỉ hiển thị (cột bảng, in đậm)
- Mặc định: 0
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `value = SUM(move.qty × move.unit_price)` — tổng giá vốn tích lũy
- Người sửa: Hệ thống
- Logic đặc biệt: Làm tròn 2 chữ số thập phân; hiển thị định dạng số VN (`toLocaleString('vi-VN')`)

---

## B. Form Điều chỉnh tồn (popup)

Mở khi nhấn nút "Điều chỉnh tồn" (yêu cầu `inventory:write`). Tạo 1 phát sinh loại `adjust` trong `tab_inventory_move` rồi tính lại tồn.

### 1. Công ty (`company_id`)

- Kiểu nhập: Chọn (ô tìm kiếm, gợi ý tên công ty)
- Mặc định: Trống (bắt buộc chọn)
- Bắt buộc: Không kiểm tra phía FE, nhưng giá trị 0 sẽ lưu vào phát sinh
- Nguồn dữ liệu / liên kết: Bảng `company`
- Người sửa: Người dùng có quyền `inventory:write`
- Logic đặc biệt: Giá trị số nguyên (chuyển từ string sang `Number`)

### 2. Kho (`warehouse_code`)

- Kiểu nhập: Chọn (ô tìm kiếm, hiển thị "mã — tên")
- Mặc định: Trống
- Bắt buộc: Không kiểm tra phía FE
- Nguồn dữ liệu / liên kết: Bảng `warehouse`
- Người sửa: Người dùng có quyền `inventory:write`

### 3. Sản phẩm (`product_code`, `product_name`, `unit`)

- Kiểu nhập: Chọn (ô tìm kiếm, hiển thị "mã — tên")
- Mặc định: Trống
- Bắt buộc: Không kiểm tra phía FE
- Nguồn dữ liệu / liên kết: Bảng `product` (load toàn bộ tối đa 2 000 bản ghi)
- Người sửa: Người dùng có quyền `inventory:write`
- Logic đặc biệt: Khi chọn mã sản phẩm, tự điền `product_name` và `unit` từ bản ghi sản phẩm tương ứng; cả ba giá trị được gửi lên API và lưu vào `tab_inventory`

### 4. Số lượng điều chỉnh (`qty`)

- Kiểu nhập: Nhập số (dương hoặc âm)
- Mặc định: 0
- Bắt buộc: Không kiểm tra phía FE (gửi 0 nếu để trống)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `inventory:write`
- Logic đặc biệt: Đây là giá trị delta — dương nghĩa là tăng tồn, âm nghĩa là giảm tồn; sau khi lưu hệ thống gọi `_recompute` để tính lại `qty`, `avg_cost`, `value`

### 5. Lý do (`note`)

- Kiểu nhập: Nhập tay (text)
- Mặc định: Trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng có quyền `inventory:write`
- Logic đặc biệt: Lưu vào cột `note` của bản ghi `InventoryMove`; đồng thời được ghi vào audit log (`record(db, user_id, "inventory", row.id, "adjust", note)`)

---

## C. Luồng ghi tồn tự động khi nhận hàng

Khi người dùng lưu số lượng thực nhận (`received_qty > 0`) trên một dòng giao (`PODelivery`), service PO gọi `inv_service.apply_delivery(...)`:

1. Tìm bản ghi `InventoryMove` có `ref_type = "gr"` và `ref_id = delivery_id`.
2. Nếu chưa có: tạo mới; nếu đã có: cập nhật (idempotent theo `delivery_id`).
3. Ghi `qty = received_qty`, `unit_price = POItem.price`, `warehouse_code` = kho trên dòng giao (ưu tiên) hoặc kho trên dòng hàng PO.
4. Gọi `_recompute` để tính lại `tab_inventory` cho bộ khóa (company, warehouse, product).
5. Nếu kho thay đổi so với lần ghi trước: gọi thêm `_recompute` cho bộ khóa cũ.

Khi dòng giao bị xóa hoặc `received_qty` về 0: gọi `inv_service.remove_delivery(delivery_id)` — xóa phát sinh và tính lại tồn.

---

## D. Quy tắc nghiệp vụ

1. Khóa duy nhất tồn kho: bộ `(company_id, warehouse_code, product_code)` — không có hai dòng tồn kho cho cùng một bộ khóa.
2. Giá bình quân gia quyền: mỗi khi có phát sinh (nhập từ GR hoặc điều chỉnh tay), hệ thống tính lại toàn bộ `Inventory` cho bộ khóa đó từ toàn bộ `InventoryMove` — không dùng giá bình quân di động.
3. Điều chỉnh tay dùng `avg_cost` hiện tại làm đơn giá phát sinh: đảm bảo điều chỉnh số lượng không làm lệch giá trị bình quân.
4. Tồn kho không thể về âm về mặt giao diện (FE không kiểm tra), nhưng giá trị âm vẫn được lưu nếu có phát sinh giảm lớn hơn tồn.
5. Tải tối đa 500 dòng trên một trang (query param `page_size=500` mặc định ở FE).
6. Audit: mọi điều chỉnh tay đều được ghi vào bảng audit (`record`).

## E. Quyền thao tác (RBAC)

| Thao tác | Quyền yêu cầu | Điều kiện |
|----------|---------------|-----------|
| Xem danh sách tồn kho | `inventory:read` | Phạm vi lọc theo `company_id` (SCOPE_FIELDS: `company`) |
| Xem sổ phát sinh (`/moves`) | `inventory:read` | Lọc thêm theo `warehouse_code`, `product_code` |
| Điều chỉnh tồn tay | `inventory:write` | Bất kỳ trạng thái; không có quy trình duyệt |
| Ghi tồn tự động từ GR | Không cần quyền riêng | Gọi từ service PO nội bộ, kế thừa user_id người lưu PO |

Phạm vi dữ liệu (`apply_scope`): entity `inventory` chỉ có chiều `company` (`company_id`). Scope `own`/`dept` không có cột owner nên tự động nâng lên `company`. Scope `all` không lọc gì thêm.

---

## F. Tab "Đơn hàng về kho" trên trang chi tiết Kho

Bổ sung 2026-08-08. Màn Tồn kho chỉ trả lời "kho đang có gì"; tab này trả lời câu hỏi còn lại của thủ kho — **"sắp có gì về"**. Đây là tab thứ hai của trang chi tiết Kho (`/warehouses/:id`), khai báo bằng `detailTabs` của `CrudDetail` chứ không viết trang riêng.

### Người dùng thấy gì

Một thẻ trắng, bên trên là ô tìm kiếm và ô lọc tiến độ, bên dưới là bảng phân trang. Mỗi dòng của bảng là **một dòng hàng của một đơn mua hàng** (không phải cả đơn) — vì một đơn có thể chia hàng về nhiều kho, gộp theo đơn sẽ hiện cả hàng của kho khác.

| Cột | Nội dung |
|-----|----------|
| Ngày đặt | `PurchaseOrder.order_date` |
| Mã PO | mã đơn — bấm vào dòng mở chi tiết đơn mua hàng |
| Nhà cung cấp | tên NCC của đơn |
| Mã SP / Tên sản phẩm | `POItem.product_code` / `product_name` |
| ĐVT | đơn vị tính của dòng |
| SL đặt | `qty_order` |
| **Đã nhận (kho này)** | `qty_received_here` — phần thực về ĐÚNG kho đang xem |
| **Đã nhận (tất cả)** | `qty_received` — tổng mọi kho của dòng đó |
| Còn lại | `qty_remaining` của dòng |
| Tiến độ | `progress_status` — badge màu theo 8 trạng thái tiến độ của dòng hàng |

Hai cột "Đã nhận" tách đôi là có chủ đích: thủ kho cần biết kho mình đã nhận bao nhiêu, còn người điều phối cần biết dòng hàng đó **đã về đủ chưa trên toàn hệ thống** — nhìn một cột thì luôn thiếu một nửa câu chuyện.

Ô tìm kiếm gõ tới đâu chờ **300 ms** rồi mới gọi API (khỏi bắn request mỗi ký tự), tìm theo Mã PO · Mã SP · Tên sản phẩm. Trạng thái rỗng phân biệt hai tình huống: đang có bộ lọc thì báo "không khớp bộ lọc", không lọc mà vẫn rỗng thì báo kho chưa có đơn nào về.

Người không có `purchase_order:read` thấy thẻ "Bạn không có quyền xem đơn mua hàng." thay cho bảng — tab vẫn hiện nhưng không rò dữ liệu đơn.

### API và cách khớp kho

`GET /api/purchase-orders/lines?warehouse_code=&page=&page_size=&q=&progress_status=`

Route này **phải khai báo trước `/{pid}`** trong `purchase_order/controller.py`; nếu đứng sau, chuỗi `"lines"` rơi vào route `/{pid}` và lỗi ép kiểu int.

**Dòng nào thuộc kho này** — điều kiện `OR` hai vế:

1. `POItem.warehouse_code = <kho>` (kho nhận mặc định của dòng), **hoặc**
2. dòng có ít nhất một lần giao (`PODelivery`) ghi `warehouse_code = <kho>`.

Vế 2 không được bỏ: lần giao đổi kho so với mặc định vẫn là **hàng thực về kho này**, bỏ sót là báo cáo sai.

**`qty_received_here` tính thế nào** — tổng SL nhận của các lần giao ghi rõ kho này, **cộng** phần đã nhận trên dòng mà chưa gắn vào lần giao/kho nào (`qty_received − tổng SL nhận đã gắn kho`, chặn không âm), phần dư đó quy về **kho mặc định của dòng**. Không có vế cộng thêm này thì toàn bộ dữ liệu nhập lịch sử — vốn chỉ có SL nhận ở mức dòng, không tách lần giao — sẽ hiện **0 ở mọi kho**.

Quyền: `require("purchase_order", "read")` + `apply_scope(...)` giống mọi màn đơn mua hàng khác — tab này không mở thêm cửa nào.

---

---

# Công nợ

## Mục đích

Theo dõi các khoản công nợ phải trả phát sinh từ hoạt động mua hàng — gồm nợ tiền hàng (NCC bán) và nợ cước vận chuyển (đơn vị carrier). Mọi khoản nợ được **sinh tự động** khi ghi nhận số lượng nhận hàng; người dùng không tạo thủ công. Màn hình cho phép lọc, xem tuổi nợ, và chọn các khoản để lập phiếu yêu cầu thanh toán.

Đường dẫn: `/payables` (danh sách công nợ).

Bảng DB: `tab_payable` (1 dòng = 1 lần giao × 1 luồng `goods`/`shipping`).

## Vai trò tham gia

- Người xem (`payable:read`): xem danh sách, bộ lọc, thẻ tổng hợp, tuổi nợ.
- Người lập đề nghị thanh toán (`payment_request:create`): chọn khoản nợ và tạo phiếu yêu cầu thanh toán (không cần quyền `payable:write`).
- Hệ thống (service nội bộ): sinh/cập nhật/xóa công nợ khi lưu đơn mua hàng.

---

## A. Thẻ tổng hợp (Summary cards)

Hiển thị bốn chỉ số tổng hợp theo bộ lọc hiện tại (gọi endpoint `/api/payables/summary`).

### 1. Tổng nợ (`total`)

- Kiểu nhập: Chỉ hiển thị
- Mặc định: 0
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `SUM(payable.total)` — tổng số tiền phải trả (đã bao gồm VAT) của toàn bộ khoản nợ trong bộ lọc
- Người sửa: Hệ thống

### 2. Đã trả (`paid`)

- Kiểu nhập: Chỉ hiển thị
- Mặc định: 0
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `SUM(payable.paid_amount)`
- Người sửa: Hệ thống (cập nhật khi ghi nhận thanh toán)

### 3. Còn phải trả (`remaining`)

- Kiểu nhập: Chỉ hiển thị
- Mặc định: 0
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `SUM(payable.remaining)` — tổng số dư còn lại
- Người sửa: Hệ thống

### 4. Quá hạn (`overdue`)

- Kiểu nhập: Chỉ hiển thị (màu đỏ)
- Mặc định: 0
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `SUM(remaining)` của các khoản chưa thanh toán đủ (`status != "Đã TT"`) có `due_date` không trống và nhỏ hơn ngày hôm nay
- Người sửa: Hệ thống

---

## B. Bộ lọc

> Bộ lọc **tự áp dụng** ngay khi thay đổi (debounce 300 ms) — không cần nhấn nút riêng.
> Deep-link: khi vào `/payables?supplier=<code>` hoặc `/payables?po_code=<code>` (từ cảnh báo công nợ hoặc dashboard), trang tự điền sẵn bộ lọc tương ứng và đặt Năm = "Tất cả" để hiện đủ nợ.

### 1. Công ty (`company_id`)

- Kiểu nhập: Bộ lọc — Chọn (ô tìm kiếm)
- Mặc định: Tất cả
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng `company`
- Người sửa: Người dùng
- Logic đặc biệt: Truyền query param `company_id`; RBAC scope cũng lọc theo công ty

### 2. Nhà cung cấp (`supplier_code`)

- Kiểu nhập: Bộ lọc — Chọn (ô tìm kiếm, hiển thị tên NCC)
- Mặc định: Tất cả; tự điền nếu URL có `?supplier=<code>`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng `supplier`
- Người sửa: Người dùng
- Logic đặc biệt: Thuộc `FILTERABLE` của module (`supplier_code`, `po_code`, `invoice_no`, `source_type`, `status`)

### 3. PO (`po_code`)

- Kiểu nhập: Bộ lọc — Nhập tự do (LIKE)
- Mặc định: Trống; tự điền nếu URL có `?po_code=<code>`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Cột `po_code` trên `tab_payable`
- Người sửa: Người dùng
- Logic đặc biệt: Thuộc `FILTERABLE` — lọc LIKE chứa chuỗi

### 4. Số hóa đơn (`invoice_no`)

- Kiểu nhập: Bộ lọc — Nhập tự do (LIKE)
- Mặc định: Trống (không lọc)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Cột `invoice_no` trên `tab_payable`
- Người sửa: Người dùng
- Logic đặc biệt: Thuộc `FILTERABLE` — lọc LIKE chứa chuỗi

### 5. Loại nợ (`source_type`)

- Kiểu nhập: Bộ lọc — Chọn từ danh sách
- Mặc định: Tất cả
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: `goods` (Hàng hóa) / `shipping` (Vận chuyển)
- Người sửa: Người dùng

### 6. Trạng thái (`status`)

- Kiểu nhập: Bộ lọc — Chọn từ danh sách
- Mặc định: Tất cả
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: DB lưu `Chờ TT` / `Trả một phần` / `Đã TT`; nhãn hiển thị trong bộ lọc: "Chờ thanh toán" / "Thanh toán một phần" / "Đã thanh toán"
- Người sửa: Người dùng

### 7. Tuổi nợ (`aging`)

- Kiểu nhập: Bộ lọc — Chọn từ danh sách
- Mặc định: Tất cả
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: `Chưa đến hạn` / `1-30` / `31-60` / `61-90` / `>90` (đơn vị: ngày quá hạn)
- Người sửa: Người dùng
- Logic đặc biệt: Bộ lọc tuổi nợ được xử lý ở DB bằng cách so sánh `due_date` với ngày hiện tại; lọc "Chưa đến hạn" bao gồm cả dòng có `due_date` trống

### 8. Năm (`year`/`period`)

- Kiểu nhập: Bộ lọc — Chọn (năm hiện tại, năm trước, năm kia, hoặc "Tất cả")
- Mặc định: Năm hiện tại (hoặc "Tất cả" khi vào qua deep-link)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Cột `period` (`YYYY`, 4 ký tự đầu của `incur_date`)
- Người sửa: Người dùng
- Logic đặc biệt: Mặc định lọc năm hiện tại để giới hạn dữ liệu nạp; chọn "Tất cả" (`all`) bỏ lọc năm

### 9. Ngày phát sinh (`incur_from` / `incur_to`)

- Kiểu nhập: Bộ lọc — Chọn ngày (2 ô nhập: từ – đến)
- Mặc định: Trống (không lọc)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Cột `incur_date` trên `tab_payable`
- Người sửa: Người dùng
- Logic đặc biệt: Lọc `incur_date >= incur_from` và/hoặc `incur_date <= incur_to`; hai ô dùng độc lập hoặc kết hợp

### 10. Số tiền tổng nợ (`amount_from` / `amount_to`)

- Kiểu nhập: Bộ lọc — Nhập số (2 ô nhập: từ – đến)
- Mặc định: 0 (không lọc khi bằng 0)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Cột `total` trên `tab_payable` (tổng nợ = amount + vat)
- Người sửa: Người dùng
- Logic đặc biệt: Lọc `total >= amount_from` và/hoặc `total <= amount_to`

---

## C. Bảng danh sách công nợ

Mỗi dòng tương ứng một bản ghi `Payable`. Khoản nợ không thể sửa trực tiếp trên màn này.

### 1. Chọn (checkbox)

- Kiểu nhập: Checkbox (chọn nhiều)
- Mặc định: Không chọn
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng
- Logic đặc biệt: Chỉ cho phép chọn khoản nợ thỏa mãn đồng thời: `status != "Đã TT"`, `remaining > 0`, và `invoice_no` không trống. Mục đích: chọn để lập phiếu yêu cầu thanh toán

### 2. Nhà cung cấp (`supplier_name`)

- Kiểu nhập: Chỉ hiển thị (cột bảng)
- Mặc định: —
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Được lấy từ `PurchaseOrder.supplier_name` hoặc `carrier_name` khi sinh công nợ
- Người sửa: Hệ thống (cập nhật khi lưu lại PO)
- Logic đặc biệt: Hiển thị `supplier_name` ưu tiên; nếu trống hiển thị `supplier_code`. Cột "Mã NCC" là cột riêng liền kề (xem C.3)

### 3. Mã NCC (`supplier_code`)

- Kiểu nhập: Chỉ hiển thị (cột bảng, màu mờ/muted)
- Mặc định: —
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Cột `supplier_code` trên `tab_payable`
- Người sửa: Hệ thống
- Logic đặc biệt: Cột độc lập với cột "Nhà cung cấp"; dùng để tra cứu nhanh mã NCC

### 4. Loại (`source_type`)

- Kiểu nhập: Chỉ hiển thị (cột bảng)
- Mặc định: —
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `goods` hiển thị "Hàng hóa"; `shipping` hiển thị "Vận chuyển"
- Người sửa: Hệ thống

### 5. Công ty (`company_id`)

- Kiểu nhập: Chỉ hiển thị (cột bảng, hiển thị tên công ty)
- Mặc định: —
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Bảng `company`
- Người sửa: Hệ thống (lấy từ `PurchaseOrder.company_id`)

### 6. PO (`po_code`)

- Kiểu nhập: Chỉ hiển thị (cột bảng)
- Mặc định: —
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Liên kết tới đơn mua hàng (`po_id`)
- Người sửa: Hệ thống
- Logic đặc biệt: Có thể dùng để tìm kiếm bằng bộ lọc `po_code` (FILTERABLE)

### 7. Số hóa đơn (`invoice_no`)

- Kiểu nhập: Chỉ hiển thị (cột bảng)
- Mặc định: Trống
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Luồng `goods`: lấy từ `POItem.invoice_no` (nhập trên chi tiết sản phẩm của PO); luồng `shipping`: sinh tự động từ `"{po.misa_code}-{item.product_code}"`
- Người sửa: Hệ thống (cập nhật mỗi khi lưu PO)
- Logic đặc biệt: Khoản nợ thiếu số hóa đơn hiển thị cảnh báo "chưa có HĐ" màu đỏ và không cho chọn để tạo yêu cầu thanh toán

### 8. Ngày phát sinh (`incur_date`)

- Kiểu nhập: Chỉ hiển thị (cột bảng)
- Mặc định: —
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Bằng `PODelivery.received_date` — ngày ghi nhận hàng thực nhận
- Người sửa: Hệ thống

### 9. Hạn trả (`due_date`)

- Kiểu nhập: Chỉ hiển thị (cột bảng)
- Mặc định: —
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `incur_date + N ngày` — N lấy từ `payment_terms` của NCC (regex tìm số nguyên trước "ngày", vd "Công nợ 30 ngày" → 30)
- Người sửa: Hệ thống (tính lại khi lưu PO)
- Logic đặc biệt: Nếu `payment_terms` không chứa số ngày (tiền mặt, v.v.) thì `due_days = 0` và `due_date = incur_date`

### 10. Tuổi nợ (`aging`)

- Kiểu nhập: Chỉ hiển thị (nhãn badge màu)
- Mặc định: —
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Tính thời điểm đọc bằng `aging_bucket(due_date)`: so sánh `due_date` với ngày hiện tại; trả về "Chưa đến hạn" / "1-30" / "31-60" / "61-90" / ">90"
- Người sửa: Hệ thống (tính live, không lưu DB)
- Logic đặc biệt: Badge màu: "Chưa đến hạn" = xám; "1-30", "31-60" = vàng (warn); "61-90", ">90" = đỏ (err)

### 11. Tổng nợ (`total`)

- Kiểu nhập: Chỉ hiển thị (cột bảng, căn phải)
- Mặc định: 0
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `total = amount + vat`; `amount = received_qty × đơn giá PO` (luồng goods) hoặc `shipping_amount` (luồng shipping); `vat = amount × vat_rate / 100` (luồng goods) hoặc 0 (luồng shipping)
- Người sửa: Hệ thống

### 12. Đã trả (`paid_amount`)

- Kiểu nhập: Chỉ hiển thị (cột bảng, căn phải)
- Mặc định: 0
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: Cộng dồn từ các thanh toán đã ghi nhận trên phiếu yêu cầu thanh toán
- Người sửa: Hệ thống (module payment)

### 13. Còn lại (`remaining`)

- Kiểu nhập: Chỉ hiển thị (cột bảng, in đậm, căn phải)
- Mặc định: 0
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `remaining = total - paid_amount` — lưu sẵn trong DB (không tính live khi đọc)
- Người sửa: Hệ thống (cập nhật sau mỗi thanh toán qua `recalc_status`)

### 14. Trạng thái (`status`)

- Kiểu nhập: Chỉ hiển thị (nhãn badge màu)
- Mặc định: `Chờ TT`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: DB lưu `Chờ TT` (paid = 0) / `Trả một phần` (0 < paid < total − 0.01) / `Đã TT` (paid ≥ total − 0.01)
- Người sửa: Hệ thống (`recalc_status` được gọi mỗi khi `paid_amount` thay đổi)
- Logic đặc biệt: Nhãn hiển thị đầy đủ: "Chờ thanh toán" / "Thanh toán một phần" / "Đã thanh toán". Badge màu: "Đã TT" = xanh lá; "Trả một phần" = vàng; "Chờ TT" = xám

---

## D. Luồng sinh công nợ tự động (2 luồng)

Hàm `recompute_effects` trong `purchase_order/service.py` được gọi mỗi lần lưu PO (tạo mới hoặc cập nhật). Với mỗi dòng giao (`PODelivery`) có `received_qty > 0`:

### Luồng 1: Công nợ hàng hóa (`source_type = "goods"`)

1. NCC: lấy từ `PurchaseOrder.supplier_code` / `supplier_name`.
2. Số ngày nợ: đọc `supplier.payment_terms` → regex tìm số nguyên trước "ngày" (`debt_days()`).
3. Số tiền: `amount = received_qty × POItem.price`; `vat = amount × POItem.vat / 100`; `total = amount + vat`.
4. Số hóa đơn: `POItem.invoice_no` (nhập thủ công trên chi tiết sản phẩm của đơn mua hàng).
5. Gọi `pay_service.upsert(source_type="goods", ref_id=delivery_id, ...)` — idempotent theo `(source_type, ref_type, ref_id)`.
6. `incur_date = received_date`; `due_date = incur_date + goods_days ngày`; `period = YYYY`.

### Luồng 2: Công nợ vận chuyển (`source_type = "shipping"`)

1. Điều kiện kích hoạt: dòng giao có `carrier_code` không trống **và** `shipping_amount > 0`.
2. NCC carrier: lấy từ `PODelivery.carrier_code` / `carrier_name` (hoặc `supplier.name`).
3. Số ngày nợ: đọc `carrier.payment_terms` tương tự luồng goods.
4. Số tiền: `amount = shipping_amount`; `vat = 0` (vận chuyển không có VAT riêng); `total = amount`.
5. Số hóa đơn tạm: `"{po.misa_code}-{item.product_code}"` (không có hóa đơn riêng từ carrier).
6. Gọi `pay_service.upsert(source_type="shipping", ref_id=delivery_id, ...)`.
7. Nếu carrier bị xóa hoặc `shipping_amount` về 0: gọi `pay_service.remove("shipping", delivery_id)`.

**Xóa công nợ:** khi dòng giao bị xóa hoặc `received_qty` về 0, hàm `_cleanup_delivery` gọi `pay_service.remove("goods", delivery_id)` và `pay_service.remove("shipping", delivery_id)`.

---

## E. Tạo phiếu yêu cầu thanh toán từ màn Công nợ

1. Người dùng chọn một hoặc nhiều khoản nợ thỏa điều kiện (còn nợ + có số HĐ).
2. Nhấn nút "Tạo yêu cầu thanh toán".
3. API `POST /api/payment-requests` nhận danh sách `{ payable_id, amount }` — mỗi amount mặc định bằng `remaining`.
4. Hệ thống tự nhóm theo `supplier_code` và tạo 1 phiếu yêu cầu thanh toán cho mỗi NCC.
5. Nếu chỉ tạo 1 phiếu: chuyển thẳng sang chi tiết phiếu; nếu nhiều phiếu: chuyển sang danh sách phiếu.
6. Sau khi tạo: khoản nợ chưa thay đổi trạng thái — trạng thái cập nhật sau khi phiếu thanh toán được duyệt và ghi nhận thực chi.

---

## F. Quy tắc nghiệp vụ

1. Công nợ là dữ liệu chỉ đọc trên màn `/payables` — không có form sửa trực tiếp; mọi thay đổi đến từ việc lưu PO hoặc ghi nhận thanh toán.
2. Idempotent: mỗi `(source_type, ref_type="delivery", ref_id=delivery_id)` chỉ có một bản ghi `Payable`. Lưu PO nhiều lần cập nhật đúng bản ghi cũ, không tạo trùng.
3. Số ngày nợ (`due_days`) được xác định theo `payment_terms` của NCC bằng regex; nếu không tìm thấy số ngày thì `due_days = 0` (hạn trả = ngày nhận hàng).
4. Khoản nợ vận chuyển chỉ sinh khi đồng thời có `carrier_code` và `shipping_amount > 0` trên dòng giao; thiếu một trong hai thì khoản nợ shipping bị xóa (nếu đã tồn tại).
5. Điều kiện chọn để lập phiếu thanh toán: `status != "Đã TT"` **và** `remaining > 0` **và** `invoice_no` không trống — kiểm tra phía FE (`payable` function trong `Payables.tsx`).
6. Khi chọn nhiều khoản từ nhiều NCC: hệ thống tự tách thành nhiều phiếu yêu cầu thanh toán (1 phiếu/NCC), hiển thị cảnh báo số phiếu sẽ tạo.
7. Mặc định API lọc theo năm hiện tại (`period = YYYY`) để tránh nạp toàn bộ lịch sử; chọn "Tất cả" bỏ lọc này. Khi vào qua deep-link (`?supplier=` hoặc `?po_code=`), FE tự chuyển Năm sang "Tất cả".
8. Tuổi nợ (`aging`) được tính thời điểm đọc, không lưu DB.
9. Deep-link từ cảnh báo: cảnh báo công nợ quá hạn/sắp hạn tạo link `/payables?po_code=<mã_PO>`; dashboard cũng có thể link `/payables?supplier=<mã_NCC>`. Payables đọc cả hai URL param khi load trang.
10. Phân trang phía FE: API lấy tối đa 1 000 dòng mỗi lần gọi (`page_size=1000`); FE phân trang cục bộ với cỡ trang mặc định 20 dòng.
11. **Ghi tiền chi vào công nợ (CR-044):** một số hóa đơn có thể ứng với **nhiều** khoản nợ (mỗi lần giao hàng một khoản). Khi phiếu thanh toán chuyển "Đã chi", tiền được rải theo `(NCC, loại nợ, PO, số hóa đơn)` và **chỉ rải vào khoản còn `remaining > 0`**; khoản đã tất toán bị bỏ qua, phần trả dư ghi vào đúng khoản của dòng phiếu. Nếu không có quy tắc này thì `paid_amount` vượt `total` làm **`remaining` âm** trong khi khoản còn nợ thật vẫn treo, kéo theo dòng Đơn mua hàng không đạt "Hoàn thành". Chi tiết: `05-yeu-cau-thanh-toan.md` mục C, quy tắc 6a.

## G. Quyền thao tác (RBAC)

| Thao tác | Quyền yêu cầu | Điều kiện |
|----------|---------------|-----------|
| Xem danh sách công nợ | `payable:read` | Phạm vi lọc theo `company_id` (chiều `company`) và `created_by` (chiều `owner`) |
| Xem thẻ tổng hợp | `payable:read` | Tổng hợp trên cùng bộ lọc với danh sách |
| Chọn khoản nợ để lập đề nghị | `payable:read` + `payment_request:create` | Khoản nợ thỏa điều kiện (còn nợ + có số HĐ) |
| Sinh/cập nhật/xóa công nợ tự động | Không cần quyền riêng | Gọi từ service PO nội bộ, kế thừa user_id người lưu PO |

Phạm vi dữ liệu (`apply_scope`): entity `payable` có hai chiều — `company` (`company_id`) và `owner` (`created_by`). Scope `own` lọc theo `created_by = user.id`. Scope `company` lọc theo `company_id` của user. Scope `all` không lọc thêm.

---

## H. Dashboard "Công nợ & Đánh giá" trên trang chi tiết NCC

Đổi 2026-08-08. Trước đó trang chi tiết NCC có hai tab rời: "Công nợ" là một **bảng phẳng** liệt kê khoản nợ, và "Đánh giá" là vài con số KPI giao hàng. Người dùng phải tự cộng nhẩm để trả lời câu hỏi thật sự của họ — "NCC này mình còn nợ bao nhiêu, có khoản nào quá hạn không". Nay gộp thành **một tab báo cáo** tên "Công nợ & Đánh giá".

Thành phần: `frontend/src/components/supplier-payables-dashboard.tsx` (phần vẽ) + `supplier-payables-stats.ts` (phần tính, tách riêng cho thuần hàm) + `supplier-payables-filters.tsx` (thanh lọc).

### 1. Thứ tự các khối trên tab

1. **Thẻ "Đánh giá nhà cung cấp"** — số lần giao dịch · số lần giao trễ · tỷ lệ trễ · số hợp đồng. Đặt **trên** thanh lọc và **không chịu ảnh hưởng bộ lọc**: đây là số của cả kỳ, lọc theo khoản nợ sẽ làm sai ý nghĩa. Có ghi chú "· cả kỳ, không theo bộ lọc bên dưới" ngay cạnh tiêu đề để không ai hiểu nhầm. Tỷ lệ trễ > 30% hiện thêm badge đỏ "Tỷ lệ giao trễ cao". KPI lấy 1 dòng từ `/api/reports/matrix`, số hợp đồng lấy từ tab Hợp đồng của cùng trang.
2. **Thanh lọc** — xem mục 3.
3. **Hàng KPI công nợ** — Tổng phát sinh · Đã thanh toán · Còn phải trả · Quá hạn, cộng thẻ thứ năm "Trả dư / ghi có" **chỉ hiện khi có phát sinh**.
4. **Tiến độ thanh toán** — một thanh ngang xanh/đỏ với dòng chữ "Đã trả X / Y — còn Z". Phần chưa trả tô **hồng đỏ khi có khoản quá hạn**, xanh nhạt khi chưa tới hạn.
5. **Ba thẻ ngang hàng** — Tuổi nợ (còn phải trả) · Cơ cấu nợ theo loại (Hàng hóa / Vận chuyển) · Trạng thái khoản nợ.
6. **Biểu đồ cột "Nợ phát sinh theo tháng"** — 6 tháng gần nhất **có dữ liệu** (không phải 6 tháng liên tiếp tính lùi), cạnh nó là **"Khoản nợ cần chú ý"** — tối đa 6 khoản, sắp quá hạn nặng nhất trước rồi tới số tiền còn lại lớn nhất, kèm nút "Mở trang công nợ" deep-link sang `/payables?supplier=<mã>`.
7. **Bảng chi tiết** — vẫn còn nguyên nhưng **gập lại** mặc định, mở bằng nút "Chi tiết N khoản công nợ".

Thẻ "Tổng quan công nợ" cũ đã bỏ vì trùng hàng KPI.

### 2. Xử lý CÔNG NỢ ÂM (trả dư / ghi có)

`remaining < 0` là chuyện có thật: trả dư cho NCC, hoặc hóa đơn điều chỉnh giảm / trả hàng làm `total` âm. Nếu tính gộp như nợ thường thì tổng nợ bị trừ khống và người đọc tưởng đã trả bớt. Quy ước:

| Khái niệm | Định nghĩa |
|-----------|-----------|
| `debt` | **chỉ** phần `remaining > 0` — dùng cho tuổi nợ, quá hạn, danh sách cần chú ý |
| `credit` | tổng phần `remaining < 0`, đã đổi dấu nên luôn ≥ 0 — tách thành chỉ số "Trả dư / ghi có" riêng |
| `remainNet` | `debt − credit` — số dư thực còn nợ NCC, **có thể âm** |

Hệ quả:

- Khoản âm **không** được xếp vào bất kỳ mốc tuổi nợ nào — không thể "quá hạn" một khoản mình không nợ. Thẻ Tuổi nợ ghi chú riêng "N khoản trả dư (-X đ) không xếp mốc tuổi nợ".
- Bar biểu đồ vẽ theo **trị tuyệt đối** (`Math.abs`) để cột âm vẫn nhìn thấy; số tiền âm hiện dấu trừ và tô xanh dương (`#0284c7`) để không đọc nhầm thành nợ phải trả.
- **Trạng thái hiển thị ghi đè**: khoản có `remaining < 0` hiện "Trả dư" dù DB lưu gì. Cần thiết vì backend `recalc_status` viết `"Chờ TT"` khi `paid <= 0` — với phiếu điều chỉnh giảm thì đọc lên sẽ hiểu nhầm là **vẫn còn nợ**.
- Nhóm "Trả dư" trong thẻ Trạng thái đo bằng **số dư âm**, không phải `total` — tổng phát sinh của phiếu điều chỉnh giảm không nói lên điều gì.
- Tỉ lệ đã trả chặn trong khoảng 0–100%; `total <= 0` (toàn phiếu điều chỉnh giảm) thì coi như 0% vì không có gì để chia.

### 3. Bộ lọc — hai tầng

**Thanh lọc chính** giữ đúng 3 ô hay dùng nhất khi đọc báo cáo:

| Ô | Giá trị | Lọc ở đâu |
|---|---------|-----------|
| Xem nhanh | Còn phải trả (`remaining > 0`) · Đang quá hạn (`remaining > 0` và `aging ≠ Chưa đến hạn`) · Trả dư / ghi có (`remaining < 0`) | **client** — backend không có tham số tương ứng cho "trả dư" |
| Tuổi nợ | Chưa đến hạn · 1-30 · 31-60 · 61-90 · >90 | API (`aging`) |
| Ngày phát sinh | khoảng ngày | API (`incur_from` / `incur_to`) |

**Bộ lọc điều kiện** (nút bên phải thanh lọc) chứa mã PO · số hóa đơn · loại nợ · trạng thái — **lọc tại DB**, cấu hình ở `SUPPLIER_PAYABLE_COND_FILTERS` trong `config/conditional-filters.ts` (= bộ lọc của màn `/payables` trừ ô `supplier_code`, vì đang đứng trong trang của chính NCC đó). Chia hai tầng để thanh lọc khỏi dài mà vẫn đủ điều kiện.

Cạnh nút lọc luôn hiện "Đang xem **N**/M khoản" — N sau khi áp Xem nhanh, M là số API trả về theo các điều kiện còn lại.

Mọi khối KPI/biểu đồ đều tính trên **phần đã lọc**, không phải toàn bộ dữ liệu.

### 4. Cách tab lấy dữ liệu

Tab **tự gọi** `GET /api/payables?supplier_code=&year=all&page_size=500&…` chứ không nhận sẵn danh sách từ trang cha — vì bộ lọc điều kiện sinh query param cho backend. Gõ trong bảng lọc làm param đổi liên tục nên có **debounce 300 ms** trước khi gọi API.

Đổi lại, `SupplierDetail` đã **bỏ state `payables`** — mở trang chi tiết NCC nay ít hơn một request; công nợ chỉ tải khi thật sự bấm vào tab.

---

## I. Lần rà soát gần nhất

Rà 2026-08-11. Đối chiếu tài liệu với mã nguồn:

| Nội dung kiểm | Đối chiếu với | Kết quả |
|---------------|---------------|---------|
| Tab "Đơn hàng về kho" | `frontend/src/components/warehouse-purchase-lines.tsx` | đúng |
| Endpoint `/api/purchase-orders/lines` (thứ tự khai báo, khớp kho, `qty_received_here`) | `backend/app/modules/purchase_order/controller.py` | đúng |
| Dashboard công nợ NCC — bố cục, KPI, biểu đồ | `frontend/src/components/supplier-payables-dashboard.tsx` | đúng |
| Quy ước nợ âm (`debt` / `credit` / `remainNet`, `rowStatus`) | `frontend/src/components/supplier-payables-stats.ts` | đúng |
| Bộ lọc 2 tầng | `supplier-payables-filters.tsx` + `config/conditional-filters.ts` | đúng |
| Tab NCC gộp "Công nợ & Đánh giá" | `frontend/src/pages/SupplierDetail.tsx` (`TABS`) | đúng |

Hai tính năng ở mục F và H do `minhduoc-tran` phát triển (commit `1a2a3bd` và `6917d77`, ngày 2026-08-08) và **chưa từng được đưa vào tài liệu chức năng** cho tới lần rà này. Phần Tồn kho A–E và Công nợ A–G không đổi kể từ bản 2026-08-08.
