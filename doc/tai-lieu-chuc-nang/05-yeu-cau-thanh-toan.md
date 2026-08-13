# Yêu cầu thanh toán

## Mục đich

Lập phiếu đề nghị thanh toán cho một nhà cung cấp, gom nhiều khoản công nợ (nhiều PO) vào một phiếu duy nhất. Phiếu hỗ trợ in theo mẫu biểu nội bộ (002/BM/PKT). Khi "Ghi nhận đã chi", hệ thống tự động cộng số tiền vào `paid_amount` của từng khoản công nợ tương ứng và tính lại trạng thái công nợ.

Ràng buộc cốt lõi: mỗi phiếu chỉ thuộc về một NCC và một loại công nợ (`source_type`). Lối vào chính là chọn các khoản công nợ trên màn Công nợ (hoặc trong Đơn mua hàng) rồi bấm "Tạo yêu cầu thanh toán"; hệ thống mở màn nhập liệu để soát lại, và chỉ ghi phiếu khi bấm **Tạo phiếu** — tự tách mỗi NCC thành một phiếu riêng. Từ CR-066 còn lối vào **form trắng** (nút "Thêm" ở danh sách) cho trường hợp hàng chưa về nên chưa sinh công nợ: gõ tay từng dòng, in bản nháp trình ký, và chỉ bị chặn ở khâu **Gửi duyệt** khi dòng chưa khớp khoản nợ nào.

Đường dẫn: `/payment-requests` (danh sách), `/payment-requests/:id` (chi tiết), `/print/payment-request/:id` (in phiếu).

## Vai trò tham gia

- Người tạo / nhân sự phụ trách (`payment_request:create`, `payment_request:write`): khởi tạo phiếu từ màn Công nợ, chỉnh sửa khi Nháp, gửi duyệt, đính kèm chứng từ. Quyền `payment_request:write` hiện tại được cấp cho **Quản lý thu mua** và **nhân viên được gán** (scope phù hợp).
- TP/QL / Người duyệt (`payment_request:approve`): duyệt hoặc từ chối phiếu ở trạng thái Chờ duyệt.
- Ghi nhận đã chi (`payment_request:write`, endpoint `/pay`): xác nhận tiền đã xuất, trừ công nợ tương ứng. Thao tác này yêu cầu cùng quyền `payment_request:write` — **Quản lý thu mua** và **nhân viên được gán**.
- Người in (`payment_request:print`): mở trang in phiếu.

## Vòng đời trạng thái

| Trạng thái | Mã (`status`) | Y nghia | Nút thao tác hiển thị |
|---|---|---|---|
| Nháp | `draft` | Vừa tạo, chưa gửi | Lưu, Gửi duyệt, Xóa |
| Chờ duyệt | `submitted` | Đã gửi, chờ TP/QL | Duyệt |
| Đã duyệt | `approved` | TP/QL đã duyệt, chờ chi tiền | Ghi nhận đã chi |
| Đã chi | `paid` | Tiền đã xuất, công nợ đã khấu trừ | (chỉ xem, in) |

Chỉ trạng thái Nháp (`draft`) cho phép sửa nội dung phiếu và các dòng. Phiếu đã chi (`paid`) không sửa và không xóa được.

Luồng chuyển trạng thái: `draft` -> `submitted` (Gửi duyệt) -> `approved` (Duyệt) -> `paid` (Ghi nhận đã chi).

### Thông báo theo bước

| Sự kiện | Người nhận thông báo |
|---------|----------------------|
| Gửi duyệt (`submitted`) | Người có quyền duyệt YCTT — `payment_request:approve` (Quản lý thu mua / Admin TM) |
| Duyệt (`approved`) | Người tạo phiếu |
| Từ chối (`cancelled`) | Người tạo phiếu |
| Ghi nhận đã chi (`paid`) | Người tạo phiếu |

Thông báo gửi qua chuông trong app (và Web Push nếu thiết bị đã đăng ký). Không gửi email cho workflow YCTT.

---

## A. Thông tin phiếu (phần đầu phiếu)

### 1. Mã phiếu (`code`)

- Kiểu nhập: Tự động
- Mặc định: Hệ thống sinh sau khi tạo, định dạng `YCTT{id:05d}` (ví dụ: `YCTT00045`)
- Bắt buộc: — (hệ thống điền, không sửa được)
- Nguồn dữ liệu / liên kết: Sinh từ `id` của bản ghi sau khi `db.flush()`
- Người sửa: Hệ thống (khóa hoàn toàn)
- Logic đặc biệt: Mã chỉ được gán ngay sau khi INSERT; trước thời điểm đó trường rỗng

### 2. Nhà cung cấp — mã (`supplier_code`)

- Kiểu nhập: Tự động (điền từ khoản công nợ khi tạo phiếu)
- Mặc định: Lấy từ `payable.supplier_code` của khoản nợ đầu tiên trong nhóm
- Bắt buộc: — (hệ thống điền, không sửa sau khi tạo)
- Nguồn dữ liệu / liên kết: Bảng Nhà cung cấp (`supplier`) qua `payable.supplier_code`
- Người sửa: Hệ thống (khóa hoàn toàn); mã này là khóa nhóm khi tách phiếu
- Logic đặc biệt: Khi cập nhật dòng (`PATCH`), server từ chối bất kỳ khoản nợ nào có `payable.supplier_code` khác với `supplier_code` của phiếu

### 3. Nhà cung cấp — tên (`supplier_name`)

- Kiểu nhập: Tự động (điền từ khoản công nợ khi tạo phiếu)
- Mặc định: Lấy từ `payable.supplier_name`
- Bắt buộc: — (hệ thống điền)
- Nguồn dữ liệu / liên kết: `payable.supplier_name`
- Người sửa: Hệ thống (trường hiển thị, không chỉnh sửa trực tiếp)
- Logic đặc biệt: Dùng làm "Đối tượng" và "Tên TK thụ hưởng" trên phiếu in

### 4. Loại công nợ (`source_type`)

- Kiểu nhập: Tự động
- Mặc định: `goods` (hàng hóa); hoặc `shipping` (vận chuyển) — lấy từ `payable.source_type`
- Bắt buộc: — (hệ thống điền, không sửa)
- Nguồn dữ liệu / liên kết: `payable.source_type`; hiển thị: `goods` -> "Hàng hóa", `shipping` -> "Vận chuyển"
- Người sửa: Hệ thống (khóa hoàn toàn; là khóa nhóm cùng với `supplier_code` khi tách phiếu)

### 5. Công ty (`company_id`)

- Kiểu nhập: Tự động
- Mặc định: Lấy từ `payable.company_id` của nhóm
- Bắt buộc: — (hệ thống điền)
- Nguồn dữ liệu / liên kết: Bảng Công ty (`company`); dùng để lấy tên, địa chỉ, MST in lên phiếu
- Người sửa: Hệ thống (không chỉnh sửa)
- Logic đặc biệt: Endpoint `/print` join thêm `Company` để lấy `name`, `address`, `tax_code` in vào header phiếu

### 6. Người yêu cầu (`created_by_name`)

- Kiểu nhập: Chỉ đọc (tự động — tên người tạo phiếu)
- Mặc định: Tên đầy đủ của người tạo phiếu (`resolve_actor(db, created_by)`)
- Bắt buộc: — (hệ thống điền)
- Nguồn dữ liệu / liên kết: Bảng `employee` / `user` qua `created_by` (user_id)
- Người sửa: Hệ thống (khóa hoàn toàn)
- Logic đặc biệt: Trả về trong `_out()` dưới key `created_by_name`; hiển thị trên form chi tiết và phiếu in.

### 7. Ngày lập (`created_at` / `request_date`)

- Kiểu nhập: Chỉ đọc trên UI chi tiết — hiển thị `created_at` (timestamp hệ thống, ngày+giờ đầy đủ qua `fmtDateTime`)
- Mặc định: Thời điểm `INSERT` bản ghi (`AuditMixin.created_at`)
- Bắt buộc: — (hệ thống điền)
- Nguồn dữ liệu / liên kết: `AuditMixin.created_at`; trường `request_date` (`String(10)`) vẫn tồn tại trong backend và API response (dùng tính `period = request_date[:7]` cho phiếu in), nhưng không hiển thị dưới dạng ô nhập chỉnh sửa trong UI chi tiết hiện tại
- Người sửa: Hệ thống (`created_at`); `request_date` được set tại thời điểm tạo và không đổi trong UI chi tiết
- Logic đặc biệt: Phiếu in (`/print`) dùng `request_date[:7]` làm `period` (dạng `YYYY-MM`) để ghép nội dung chuyển khoản.

### 8. Tổng tiền đề nghị (`total`)

- Kiểu nhập: Tự tính
- Mặc định: Tổng `amount` của tất cả dòng trong phiếu (tính khi tạo và khi cập nhật dòng)
- Bắt buộc: — (hệ thống tính, không nhập tay)
- Nguồn dữ liệu / liên kết: Sum(`PaymentRequestLine.amount`) cho `request_id` tương ứng
- Người sửa: Hệ thống (cập nhật tự động mỗi khi PATCH thay đổi dòng)
- Logic đặc biệt: Hiển thị trên phiếu in cả dạng số (`fmt`) lẫn dạng chữ (`docTien`)

### 9. Hình thức thanh toán (`payment_method`) — CR-035

- Kiểu nhập: Chọn 1 trong 2 (dropdown) — **Chuyển khoản** (`transfer`) / **Tiền mặt** (`cash`)
- Mặc định: `transfer` (Chuyển khoản) — mọi phiếu tạo trước CR-035 cũng mang giá trị này nên bản in giữ nguyên như cũ
- Bắt buộc: Không (không chọn = Chuyển khoản)
- Nguồn dữ liệu / liên kết: — (giá trị tự do trong 2 lựa chọn; giá trị lạ bị `norm_method()` đưa về `transfer`)
- Người sửa: Người lập phiếu (quyền `payment_request:write`) khi phiếu còn **Nháp**; chọn ngay ở màn tạo phiếu `/payment-requests/new`, sửa lại được ở màn chi tiết rồi bấm Lưu
- Logic đặc biệt: Quyết định cụm **HÌNH THỨC THANH TOÁN** trên phiếu in — xem quy tắc C.8. Cột "Hình thức TT" cũng hiện ở màn danh sách và lọc được trong Bộ lọc điều kiện.

### 10. Ghi chú (`note`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo (quyền `payment_request:write`) khi phiếu Nháp

---

## B. Dòng công nợ thanh toán (PaymentRequestLine)

Mỗi dòng thường tương ứng với một khoản công nợ (`Payable`) được đưa vào phiếu thanh toán.

**CR-066 — dòng nhập tay được:** `po_code`, `invoice_no`, `invoice_date`, `amount` là dữ liệu **lưu trên dòng phiếu** và **sửa được khi phiếu ở màn Tạo hoặc trạng thái Nháp**; lúc tạo từ màn Công nợ thì ô nào để trống mới lấy theo `Payable`. Ngược lại `due_date`, `payable_total`, `payable_paid` **luôn đọc lại từ Công nợ** mỗi lần trả dữ liệu (không lưu trên `tab_payment_request_line`) để không lệch số khi có phiếu khác chi cùng khoản nợ. Dòng chưa khớp khoản nợ nào (form trắng, hàng chưa về) trả về `matched = false`, các cột nợ bằng 0.

Server tìm khoản nợ của một dòng bằng hàm `matching_payables(supplier_code, source_type, po_code, invoice_no)` — một số hóa đơn có thể ứng với nhiều `Payable`; nếu không khớp thì lùi về `payable_id` đã lưu.

### 1. Liên kết khoản công nợ (`payable_id`)

- Kiểu nhập: Tự động (điền khi chọn khoản nợ từ màn Công nợ / Đơn mua hàng)
- Mặc định: ID của `Payable` được chọn; **`0` với dòng gõ tay trên form trắng** (CR-066)
- Bắt buộc: Không bắt buộc — dòng `payable_id = 0` vẫn lưu và in được; chỉ khi **Gửi duyệt** mới bắt buộc khớp một khoản nợ còn nợ (quy tắc C.2)
- Nguồn dữ liệu / liên kết: Bảng `tab_payable`; khi cập nhật phiếu server bỏ qua `payable_id` thuộc NCC khác
- Người sửa: Hệ thống (không hiển thị để sửa trên màn hình)
- Logic đặc biệt: Khi `set_status` -> `paid`, server ưu tiên khớp khoản nợ theo `(supplier_code, source_type, po_code, invoice_no)`, chỉ lùi về `payable_id` khi không khớp được — nên dòng gõ tay vẫn trừ đúng công nợ

### 2. Mã PO (`po_code`)

- Kiểu nhập: Nhập chữ (ô text) khi ở màn Tạo phiếu hoặc phiếu Nháp; chỉ đọc ở trạng thái khác
- Mặc định: Lấy `payable.po_code` của khoản nợ tương ứng khi TẠO phiếu từ màn Công nợ; form trắng thì rỗng
- Bắt buộc: — (để trống vẫn lưu được bản nháp)
- Nguồn dữ liệu / liên kết: Lưu trên `tab_payment_request_line.po_code`; đối chiếu ngược với Đơn mua hàng (`purchase_order`) qua `payable.po_code`
- Người sửa: Người tạo (quyền `payment_request:write`) khi phiếu Nháp
- Logic đặc biệt: Hiển thị cột "PO" trong bảng dòng phiếu. Khi SỬA bản nháp, ô để trống **không** bị điền đè lại từ khoản nợ (người dùng có quyền xóa trắng); khi TẠO thì mới lấy theo khoản nợ

### 3. Số hóa đơn (`invoice_no`)

- Kiểu nhập: Nhập chữ (ô text) khi ở màn Tạo phiếu hoặc phiếu Nháp; chỉ đọc ở trạng thái khác
- Mặc định: Lấy `payable.invoice_no` của khoản nợ tương ứng khi TẠO phiếu; form trắng thì rỗng
- Bắt buộc: **Không bắt buộc khi tạo** (CR-066 — bỏ chặn cũ). **Bắt buộc khi Gửi duyệt**: thiếu số hóa đơn thì server chặn với thông báo "Chưa gửi duyệt được: … chưa có Số hóa đơn"
- Nguồn dữ liệu / liên kết: Lưu trên `tab_payment_request_line.invoice_no`; là số hóa đơn của lần giao hàng trên dòng Đơn mua hàng (`tab_po_delivery.invoice_no` -> `payable.invoice_no`)
- Người sửa: Người tạo (quyền `payment_request:write`) khi phiếu Nháp
- Logic đặc biệt: Các dòng **cùng (mã PO + số hóa đơn)** được gộp thành một dòng khi tạo phiếu; dòng **chưa có số hóa đơn** thì để riêng (không gộp theo PO, vì chưa biết có cùng một hóa đơn hay không). Ô trống được **in trắng** trên phiếu để người dùng điền tay

### 4. Ngày hóa đơn (`invoice_date`)

- Kiểu nhập: Chọn ngày (`DateInput`) khi ở màn Tạo phiếu hoặc phiếu Nháp; chỉ đọc ở trạng thái khác
- Mặc định: Ngày hóa đơn của lần giao hàng sinh ra khoản nợ — `tab_po_delivery.invoice_date` (format `YYYY-MM-DD`)
- Bắt buộc: — (để trống thì in trắng, điền tay trên bản in)
- Nguồn dữ liệu / liên kết: Lưu trên `tab_payment_request_line.invoice_date` (thêm bởi migration `f4d1a6c92e08`); khi ô trống, lúc đọc server lùi về `tab_po_delivery.invoice_date` nên phiếu cũ không cần điền ngược dữ liệu
- Người sửa: Người tạo (quyền `payment_request:write`) khi phiếu Nháp
- Logic đặc biệt: Hiển thị cột "Ngày hóa đơn" trong bảng; trên phiếu in hiển thị `dd/mm/yyyy`, **trống thì in trắng** chứ không lấy ngày khác thay thế. Trước CR-066 cột này là "Ngày PS" và thực chất suy ra từ `created_at` của dòng (ngày tạo phiếu). Trường `incur_date` (ngày phát sinh công nợ) vẫn được trả về trong API để tham chiếu nhưng không còn hiển thị

### 5. Hạn trả (`due_date`) — join từ Payable

- Kiểu nhập: Chỉ đọc (join từ `payable.due_date`)
- Mặc định: Hạn thanh toán của khoản nợ (format `YYYY-MM-DD`)
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `payable.due_date`
- Người sửa: Hệ thống (không lưu trên `PaymentRequestLine`)
- Logic đặc biệt: Hiển thị cột "Hạn trả" trong bảng chi tiết phiếu

### 6. Tổng nợ (`payable_total`) — join từ Payable

- Kiểu nhập: Chỉ đọc (join từ `payable.total`)
- Mặc định: Tổng phải trả của khoản nợ = `payable.amount` + `payable.vat`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `payable.total`
- Người sửa: Hệ thống
- Logic đặc biệt: Hiển thị cột "Tổng nợ" (tham khảo); không ảnh hưởng đến tổng phiếu

### 7. Đã trả (`payable_paid`) — join từ Payable

- Kiểu nhập: Chỉ đọc (join từ `payable.paid_amount`)
- Mặc định: Tổng số tiền đã thanh toán của khoản nợ tính đến thời điểm hiện tại
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `payable.paid_amount`
- Người sửa: Hệ thống (được cập nhật khi một phiếu thanh toán khác "Ghi nhận đã chi")
- Logic đặc biệt: Hiển thị cột "Đã trả"; giúp người dùng biết còn bao nhiêu chưa trả

### 8. Số tiền đề nghị trả (`amount`)

- Kiểu nhập: Nhập số (VND) qua component `NumberInput` ở màn Tạo phiếu và khi phiếu ở trạng thái Nháp; chỉ đọc ở trạng thái khác. Định dạng VN: dấu `.` ngăn nghìn, dấu `,` thập phân; chặn số âm.
- Mặc định: `payable.total - payable.paid_amount` (phần còn lại chưa trả) — áp dụng nếu người dùng để 0 hoặc không nhập; dòng gõ tay chưa gắn khoản nợ thì mặc định 0, người lập tự nhập
- Bắt buộc: Không bắt buộc (cho phép nhập 0 hoặc để trống; server tự tính từ phần còn lại)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo (quyền `payment_request:write`) khi phiếu Nháp
- Logic đặc biệt: Nếu `LineIn.amount > 0` thì dùng giá trị người nhập; ngược lại server tính `round(float(p.total) - float(p.paid_amount), 2)`. Tổng tất cả `amount` của dòng được cộng vào `PaymentRequest.total`. Số âm bị chặn ở FE (`NumberInput` không cho nhập âm).

---

## C. Quy tắc nghiệp vụ

1. Tạo phiếu từ màn Công nợ: người dùng vào `/payables`, chọn các dòng công nợ (có thể thuộc nhiều NCC), bấm "Tạo yêu cầu thanh toán". Lối vào thứ hai: nút "Tạo yêu cầu thanh toán" trong chi tiết Đơn mua hàng (chọn hóa đơn còn nợ của chính đơn đó, hoặc tạo theo tổng tiền PO khi chưa nhận hàng — CR-067).

   **CR-025 — không sinh phiếu nháp:** hai lối vào trên **không gọi API ngay**. Các khoản đã tick được chuyển sang màn `/payment-requests/new` qua URL (`?payables=1,2,3`) kèm `location.state.rows`; màn này cho soát lại và **sửa số tiền đề nghị từng dòng**, **bỏ bớt khoản** (có nút khôi phục), nhập **Ngày lập** + **Hình thức thanh toán** (CR-035) + **Ghi chú**, hiển thị trước **số phiếu sẽ tách ra** và cảnh báo khoản **chưa có số hóa đơn**. Chỉ khi bấm **Tạo phiếu** mới `POST /api/payment-requests`; **thoát giữa chừng thì không bản ghi nào được tạo**. Mở lại link / F5 vẫn đúng danh sách nhờ `GET /api/payables?ids=…&year=all`.

   **CR-067 — Tạo theo PO sớm:** Khi đơn PO chưa có đợt nhận hàng nào (chưa có dòng trong `tab_payable`), bấm nút "Tạo yêu cầu thanh toán" trên PO sẽ nạp sẵn dòng thanh toán với số tiền bằng đúng Tổng tiền đơn hàng PO để lập bản nháp và in phiếu trình ký sớm.

   **CR-066 — Tạo từ form trắng:** lối vào thứ ba là nút "Thêm" ở danh sách `/payment-requests`, mở thẳng `/payment-requests/new` **không kèm khoản nợ nào**. Ở chế độ này người lập tự chọn **Nhà cung cấp** + **Công ty** + **Loại công nợ** trên đầu phiếu, rồi gõ tay từng dòng (PO · Số hóa đơn · Ngày hóa đơn · Đề nghị trả) bằng nút "Thêm dòng"; vẫn có nút "Chọn từ Công nợ" để quay lại lối vào cũ. Dùng khi hàng chưa về nên chưa sinh công nợ mà vẫn cần in phiếu trình ký trước.

   Server nhận `PRequestCreate` với danh sách `lines` (mảng `{payable_id, po_code, invoice_no, invoice_date, amount}`) kèm `supplier_code` / `company_id` / `source_type` của phiếu; gom theo cặp `(supplier_code, source_type)`, tạo mỗi nhóm thành một `PaymentRequest` riêng. Dòng không gắn khoản nợ (`payable_id = 0`) phải có `supplier_code` trên đầu phiếu, nếu không server báo "Chưa chọn nhà cung cấp cho phiếu".

2. **Điều kiện GỬI DUYỆT (CR-066)** — thay cho điều kiện tiên quyết lúc tạo trước đây. Tạo phiếu và lưu nháp thì **không** đòi số hóa đơn (để in bản nháp trình ký sớm), nhưng khi bấm **Gửi duyệt** server chạy `check_submit`: **mỗi dòng phải khớp một khoản công nợ CÒN NỢ** theo `(NCC + loại công nợ + mã PO + số hóa đơn)`. Dòng vi phạm bị liệt kê trong lỗi 400 "Chưa gửi duyệt được: …" với 3 loại nguyên nhân:

   - `… chưa có Số hóa đơn`
   - `… không có khoản công nợ nào khớp Số HĐ X` (sai số hóa đơn / mã PO, hoặc hàng chưa được ghi nhận nhận)
   - `… khoản công nợ theo Số HĐ X đã tất toán`

   Lý do đặt cổng chặn ở đây: tiền chi phải trừ được vào một khoản nợ có thật, nếu không thì dòng Đơn mua hàng sẽ kẹt không lên "Hoàn thành". Trên màn hình, dòng chưa khớp được cảnh báo bằng thẻ vàng (`matched = false`) chứ không chặn thao tác lưu.

3. Mã phiếu tự sinh: sau `db.flush()`, server gán `code = f"YCTT{req.id:05d}"` rồi `db.commit()`.

4. Sửa phiếu (PATCH): **chỉ cho phép khi `status = "draft"`** (CR-066 — khóa cứng ở backend, không chỉ ẩn nút trên giao diện). Trạng thái khác bị từ chối 400 với thông báo riêng: Chờ duyệt "…thu hồi (từ chối) rồi mới sửa", Đã duyệt "…không sửa được số tiền và số hóa đơn nữa", Đã chi / Từ chối "…không sửa được". Khi cập nhật dòng, server xóa toàn bộ dòng cũ (`PaymentRequestLine`) và tạo lại từ danh sách mới; các khoản nợ có `supplier_code` khác với phiếu bị bỏ qua; ô để trống **không** bị điền đè từ khoản nợ. `total` được tính lại.

5. Xóa phiếu: chỉ cho phép khi `status != "paid"`. Khi xóa, server gọi `delete_attachments_for` để xóa file đính kèm, xóa toàn bộ dòng, rồi xóa phiếu.

6. Luồng "Ghi nhận đã chi" (`/pay`): khi chuyển sang `paid`, với mỗi `PaymentRequestLine`:
   - Tìm **tập** khoản nợ cùng `(supplier_code, source_type, po_code, invoice_no)` với dòng phiếu; nếu không có khoản nào khớp thì lùi về đúng `payable_id` của dòng.
   - Rải số tiền của dòng vào tập đó, **chỉ rải vào khoản còn nợ** — xem quy tắc 6a.
   - Mỗi lần cộng tiền: `payable.paid_amount += phần được rải`, rồi gọi `recalc_status(p)` để cập nhật `payable.status` (Chờ TT / Trả một phần / Đã TT) và `payable.remaining`. Nếu khoản nợ sinh từ phiếu giao hàng (`source_type = goods`, `ref_type = delivery`) thì đơn mua hàng tương ứng được xếp hàng để tự tiến trạng thái dòng sau khi commit.

   **6a. Bỏ qua khoản đã tất toán (CR-044).** Một số hóa đơn có thể ứng với **nhiều** khoản nợ (mỗi lần giao hàng sinh một khoản). Khi rải tiền, server **bỏ qua mọi khoản có `remaining = 0`** và chỉ trả tối đa bằng phần còn nợ của từng khoản. Nếu trả **dư** so với tổng nợ khớp được (chi thêm, làm tròn…), phần dư ghi vào đúng khoản của dòng phiếu (`payable_id`), không rải tiếp.

   Lý do: trước bản sửa, tiền dồn hết vào khoản đầu danh sách — kể cả khoản đã trả xong — làm **công nợ âm**, trong khi khoản thật sự còn nợ vẫn treo. Hệ quả dây chuyền là dòng Đơn mua hàng **không bao giờ đủ điều kiện "Hoàn thành"**, nên cũng **không sinh được bản ghi Lịch sử mua hàng** (xem `04-don-mua-hang.md` mục I). Bản sửa chỉ chặn dữ liệu sai **phát sinh mới**; công nợ đã âm từ trước phải sửa tay.

7. Số tiền dòng: nếu `LineIn.amount > 0` dùng giá trị người nhập; nếu `<= 0` server tự tính phần còn lại chưa trả.

8. Phiếu in: endpoint `GET /{rid}/print` yêu cầu quyền `payment_request:print`; trả thêm `company` (tên, địa chỉ, MST), `created_by_name`, `period` (7 ký tự đầu `request_date`). Trang in (`PrintPaymentRequest.tsx`) đọc số tiền thành chữ tiếng Việt bằng hàm `docTien`.

   **CR-035 — cụm HÌNH THỨC THANH TOÁN theo `payment_method`:**
   - `transfer` (Chuyển khoản): tick ô "Chuyển khoản"; cột phải in đủ **Thông tin chuyển khoản** — Tên TK thụ hưởng (= tên NCC), Số TK, Ngân hàng (lấy từ hồ sơ NCC `supplier.bank_account` / `bank_name`), Nội dung chuyển khoản.
   - `cash` (Tiền mặt): tick ô "Tiền mặt"; cột phải **vẫn in đủ nhãn** (tiêu đề "Thông tin chuyển khoản:" và 4 dòng Tên TK / Số TK / Ngân hàng / Nội dung CK) nhưng **phần nội dung để trống thành dòng chấm** — giữ nguyên khung mẫu 002/BM/PKT và điền tay được khi cần. Server vẫn không gửi số TK / tên ngân hàng ra bản in (`bank_account = bank_name = ""`), nên dù có xem API cũng không lộ.
   - NCC chưa khai số TK thì chỗ đó vẫn in dấu chấm để điền tay như trước.

   **CR-066 — in trắng ô còn thiếu:** cột "Số hóa đơn" và "Ngày" (ngày hóa đơn) của từng dòng **để trống khi chưa có dữ liệu**, không lấy ngày phát sinh công nợ in thay như trước. Nhờ vậy bản nháp in ra trình ký sớm được, người dùng điền tay hai ô đó rồi mới nhập lại vào phiếu để gửi duyệt.

9. Đính kèm file: sử dụng module `attachment` với `entity = "payment_request"`, `entity_id = <id>`. Không giới hạn số file; file xóa kèm khi phiếu bị xóa.

10. Tổng hiển thị cuối bảng dòng trên UI được tính phía client (`req.lines.reduce(sum, 0)`) và có thể khác `req.total` nếu người dùng đang chỉnh sửa chưa lưu. Sau khi lưu, `req.total` từ server là giá trị chính xác.

11. Lịch sử thao tác (audit log): mỗi hành động thay đổi trạng thái (tạo — `create`, cập nhật — `update`, gửi duyệt — `submitted`, duyệt — `approved`, ghi nhận đã chi — `paid`, xóa — `delete`) được ghi vào bảng audit log (`entity = "payment_request"`, `entity_id = id`). Trang chi tiết hiển thị khối "Lịch sử thao tác" khi có ít nhất 1 bản ghi (API `/api/audit-logs?entity=payment_request&entity_id=<id>`). Khối dùng chung `components/AuditTimeline.tsx`: hiện **10 thao tác gần nhất**, còn nữa thì có nút **"Xem thêm N thao tác"** và **"Thu gọn"**; API mặc định chỉ trả **100 dòng gần nhất** (`limit`, tối đa 500) nên chạm ngưỡng thì khối ghi rõ ở cuối.

---

## D. Quyền thao tác (RBAC)

Entity: `payment_request`

| Thao tác | Quyền yêu cầu | Điều kiện trạng thái |
|---|---|---|
| Xem danh sách | `payment_request:read` | mọi trạng thái (lọc theo data scope) |
| Xem chi tiết | `payment_request:read` | mọi trạng thái (lọc theo data scope) |
| Tạo phiếu (từ màn Công nợ, từ Đơn mua hàng, hoặc form trắng) | `payment_request:create` | — |
| Sửa nội dung phiếu và dòng | `payment_request:write` | **chỉ `draft`** — chặn ở backend (CR-066) |
| Gửi duyệt | `payment_request:write` | `draft` **và mọi dòng khớp một khoản công nợ còn nợ** (quy tắc C.2) |
| Duyệt | `payment_request:approve` | `submitted` |
| Ghi nhận đã chi | `payment_request:write` | `approved`; thực hiện bởi Quản lý thu mua / nhân viên được gán |
| Xóa | `payment_request:delete` | không phải `paid` |
| Xóa nhiều (bulk) | `payment_request:delete` | không phải `paid` |
| In phiếu | `payment_request:print` | mọi trạng thái |
| Đính kèm / xóa file | `payment_request:write` | không giới hạn trạng thái |

---

## E. Phiếu in (`/print/payment-request/:id`)

**Tên file khi lưu PDF (CR-057).** Trang in đặt `document.title` = **`<Mã YCTT>-DDMMYYYY`** (ví dụ `YCTT00190-07082026`) qua hook `usePrintTitle` — trình duyệt và máy in ảo (Foxit, Microsoft Print to PDF) lấy đúng chuỗi đó làm tên file gợi ý, thay cho `Thu Mua Tool` mặc định. Ngày lấy `request_date` (ngày yêu cầu), **không** lấy ngày bấm in, nên in lại lúc nào cũng ra cùng một tên. Đây cũng chính là cột đang dùng để tính `period` in trên phiếu. Chi tiết cách làm: xem mục E của [04-don-mua-hang.md](04-don-mua-hang.md).
