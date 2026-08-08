# Yêu cầu thanh toán

## Mục đich

Lập phiếu đề nghị thanh toán cho một nhà cung cấp, gom nhiều khoản công nợ (nhiều PO) vào một phiếu duy nhất. Phiếu hỗ trợ in theo mẫu biểu nội bộ (002/BM/PKT). Khi "Ghi nhận đã chi", hệ thống tự động cộng số tiền vào `paid_amount` của từng khoản công nợ tương ứng và tính lại trạng thái công nợ.

Ràng buộc cốt lõi: mỗi phiếu chỉ thuộc về một NCC và một loại công nợ (`source_type`). Phiếu không tạo từ menu — người dùng chọn các khoản công nợ trên màn Công nợ (hoặc trong Đơn mua hàng) rồi bấm "Tạo yêu cầu thanh toán"; hệ thống mở màn nhập liệu để soát lại, và chỉ ghi phiếu khi bấm **Tạo phiếu** — tự tách mỗi NCC thành một phiếu riêng.

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

Mỗi dòng tương ứng với một khoản công nợ (`Payable`) được đưa vào phiếu thanh toán. Các trường `po_code`, `invoice_no` được sao chép từ `Payable` khi tạo dòng; `due_date`, `incur_date`, `payable_total`, `payable_paid` được join trực tiếp từ `Payable` khi trả dữ liệu (không lưu riêng trong `tab_payment_request_line`).

### 1. Liên kết khoản công nợ (`payable_id`)

- Kiểu nhập: Tự động (chọn từ màn Công nợ, không sửa được trong chi tiết phiếu)
- Mặc định: ID của `Payable` được chọn
- Bắt buộc: Bắt buộc (mỗi dòng phải liên kết với 1 `Payable` hợp lệ)
- Nguồn dữ liệu / liên kết: Bảng `tab_payable`; khi cập nhật phiếu server bỏ qua `payable_id` thuộc NCC khác
- Người sửa: Hệ thống (khóa sau khi tạo)
- Logic đặc biệt: Khi `set_status` -> `paid`, server dùng `payable_id` để cộng `amount` vào `payable.paid_amount` và gọi `recalc_status`

### 2. Mã PO (`po_code`)

- Kiểu nhập: Tự động (sao chép từ `payable.po_code` khi tạo dòng)
- Mặc định: Giá trị `po_code` của khoản nợ tương ứng
- Bắt buộc: — (hệ thống điền)
- Nguồn dữ liệu / liên kết: `payable.po_code` -> Đơn mua hàng (`purchase_order`)
- Người sửa: Hệ thống (khóa hoàn toàn)
- Logic đặc biệt: Hiển thị trong bảng dòng phiếu chi tiết (cột "PO")

### 3. Số hóa đơn (`invoice_no`)

- Kiểu nhập: Tự động (sao chép từ `payable.invoice_no` khi tạo dòng)
- Mặc định: Giá trị `invoice_no` của khoản nợ tương ứng
- Bắt buộc: Bắt buộc khi tạo — khoản nợ chưa có số hóa đơn bị từ chối, phiếu không được tạo
- Nguồn dữ liệu / liên kết: `payable.invoice_no`
- Người sửa: Hệ thống (khóa hoàn toàn)
- Logic đặc biệt: Server kiểm tra `(p.invoice_no or "").strip()` trước khi thêm vào nhóm; khoản nợ thiếu số HĐ bị liệt kê trong thông báo lỗi 400 và không được đưa vào phiếu

### 4. Ngày phát sinh (`incur_date`) — join từ Payable

- Kiểu nhập: Chỉ đọc (join từ `payable.incur_date` mỗi lần trả dữ liệu)
- Mặc định: Ngày nhận hàng / ngày phát sinh công nợ (format `YYYY-MM-DD`)
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: `payable.incur_date`
- Người sửa: Hệ thống (không lưu trên `PaymentRequestLine`, đọc trực tiếp từ `Payable`)
- Logic đặc biệt: Hiển thị cột "Ngày PS" trong bảng; trên phiếu in hiển thị dạng `dd/mm/yyyy`

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

- Kiểu nhập: Nhập số (VND) qua component `NumberInput` khi phiếu ở trạng thái Nháp; chỉ đọc ở trạng thái khác. Định dạng VN: dấu `.` ngăn nghìn, dấu `,` thập phân; chặn số âm.
- Mặc định: `payable.total - payable.paid_amount` (phần còn lại chưa trả) — áp dụng nếu người dùng để 0 hoặc không nhập
- Bắt buộc: Không bắt buộc (cho phép nhập 0 hoặc để trống; server tự tính từ phần còn lại)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo (quyền `payment_request:write`) khi phiếu Nháp
- Logic đặc biệt: Nếu `LineIn.amount > 0` thì dùng giá trị người nhập; ngược lại server tính `round(float(p.total) - float(p.paid_amount), 2)`. Tổng tất cả `amount` của dòng được cộng vào `PaymentRequest.total`. Số âm bị chặn ở FE (`NumberInput` không cho nhập âm).

---

## C. Quy tắc nghiệp vụ

1. Tạo phiếu từ màn Công nợ: người dùng vào `/payables`, chọn các dòng công nợ (có thể thuộc nhiều NCC), bấm "Tạo yêu cầu thanh toán". Lối vào thứ hai: nút "Tạo yêu cầu thanh toán" trong chi tiết Đơn mua hàng (chọn hóa đơn còn nợ của chính đơn đó).

   **CR-025 — không sinh phiếu nháp:** hai lối vào trên **không gọi API ngay**. Các khoản đã tick được chuyển sang màn `/payment-requests/new` qua URL (`?payables=1,2,3`) kèm `location.state.rows`; màn này cho soát lại và **sửa số tiền đề nghị từng dòng**, **bỏ bớt khoản** (có nút khôi phục), nhập **Ngày lập** + **Hình thức thanh toán** (CR-035) + **Ghi chú**, hiển thị trước **số phiếu sẽ tách ra** và cảnh báo khoản **chưa có số hóa đơn**. Chỉ khi bấm **Tạo phiếu** mới `POST /api/payment-requests`; **thoát giữa chừng thì không bản ghi nào được tạo**. Mở lại link / F5 vẫn đúng danh sách nhờ `GET /api/payables?ids=…&year=all`.

   Server nhận `PRequestCreate` với danh sách `lines` (mảng `{payable_id, amount}`), gom theo cặp `(supplier_code, source_type)`, tạo mỗi nhóm thành một `PaymentRequest` riêng.

2. Điều kiện tiên quyết khi tạo: mỗi `Payable` trong danh sách gửi lên phải có `invoice_no` không rỗng. Các khoản nợ chưa có số hóa đơn bị liệt kê trong thông báo lỗi 400 và toàn bộ yêu cầu tạo bị từ chối.

3. Mã phiếu tự sinh: sau `db.flush()`, server gán `code = f"YCTT{req.id:05d}"` rồi `db.commit()`.

4. Sửa phiếu (PATCH): chỉ cho phép khi `status != "paid"`. Khi cập nhật dòng, server xóa toàn bộ dòng cũ (`PaymentRequestLine`) và tạo lại từ danh sách mới; các khoản nợ có `supplier_code` khác với phiếu bị bỏ qua. `total` được tính lại.

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
| Tạo phiếu (từ màn Công nợ) | `payment_request:create` | — |
| Sửa nội dung phiếu và dòng | `payment_request:write` | `draft` |
| Gửi duyệt | `payment_request:write` | `draft` |
| Duyệt | `payment_request:approve` | `submitted` |
| Ghi nhận đã chi | `payment_request:write` | `approved`; thực hiện bởi Quản lý thu mua / nhân viên được gán |
| Xóa | `payment_request:delete` | không phải `paid` |
| Xóa nhiều (bulk) | `payment_request:delete` | không phải `paid` |
| In phiếu | `payment_request:print` | mọi trạng thái |
| Đính kèm / xóa file | `payment_request:write` | không giới hạn trạng thái |
