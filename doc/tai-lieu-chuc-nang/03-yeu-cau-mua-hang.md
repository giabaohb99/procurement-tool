# Yêu cầu mua hàng (PYC)

## Mục đích

Ghi nhận nhu cầu mua vật tư, hàng hóa, dịch vụ từ các bộ phận trong công ty. Một phiếu gồm thông tin chung (header) và danh sách dòng hàng (items). Sau khi được duyệt, phiếu chuyển sang giai đoạn xử lý thu mua và theo dõi tiến độ từng dòng.

Đường dẫn: `/purchase-requests` (danh sách), `/purchase-requests/:id` (chi tiết), `/purchase-requests/new` (tạo mới).

## Vai trò tham gia

- Người yêu cầu / Nhân viên (`purchase_request:create`, `purchase_request:read`): tạo và gửi duyệt phiếu của mình.
- Trưởng bộ phận / Người duyệt bước 1 (`purchase_request:approve` phạm vi `dept`): duyệt hoặc từ chối phiếu của phòng mình. **KHÔNG điều phối** (xem CR-034).
- Admin / Quản lý thu mua — người ĐIỀU PHỐI (`purchase_request:approve` phạm vi `proc` hoặc `all`): duyệt lần 2 (nút **Duyệt** trên phiếu đang ở "Đã duyệt") — đây là lúc hệ thống tự động phân bổ NSTM phụ trách. Quyền này trên môi trường đang chạy do migration `d2e6f4b81a37` cấp cho vai trò `pur_admin`; `seed.py` chỉ áp cho cài mới.
- Admin / Quản lý thu mua (`purchase_request:cancel`): Từ chối phiếu (→ `cancelled`), Trả về (→ `rejected`), đánh dấu Hoàn thành.
- Nhân sự thu mua (NSTM) (`purchase_request:read`, được giao dòng): cập nhật trạng thái và tiến độ các dòng được phân công.
- Người có `purchase_request:write`: sửa nội dung phiếu của người khác (ngoài chủ phiếu).

## Vòng đời trạng thái

| Mã trạng thái | Tên hiển thị | Ý nghĩa | Nút thao tác hiển thị |
|--------------|--------------|---------|----------------------|
| `draft` | Nháp | Đang soạn, chưa gửi | Lưu, Gửi duyệt, Xóa (nếu có `delete`) |
| `submitted` | Chờ duyệt | Đã gửi, đợi TP/QL | Duyệt, Trả về, Từ chối phiếu (nếu có `approve`) |
| `approved` | Đã duyệt | Trưởng bộ phận đã duyệt, **chờ thu mua điều phối**. Phiếu CHƯA có NSTM phụ trách và CHƯA tạo được ĐMH | **Duyệt** (lần 2 — Admin/QL thu mua), Trả về, Từ chối phiếu (nếu có `cancel`) |
| `dispatched` | Đã điều phối | Thu mua đã duyệt lần 2; hệ thống đã tự động phân bổ NSTM — mốc bắt đầu làm việc thật (tạo được ĐMH) | Tạo ĐMH, Trả về, Từ chối phiếu, Hoàn thành (nếu có `cancel`) |
| `processing` | Đang xử lý | Ít nhất 1 dòng đã bắt đầu xử lý | Trả về, Từ chối phiếu, Hoàn thành (nếu có `cancel`) |
| `completed` | Hoàn thành | Tất cả dòng Hoàn thành hoặc đánh dấu thủ công | (chỉ xem) |
| `rejected` | Bị trả lại | Phiếu bị trả về để sửa lại; người tạo/người yêu cầu được sửa như Nháp | Lưu, Gửi duyệt lại, Xóa (nếu có `delete`) |
| `cancelled` | Đã từ chối | Phiếu bị từ chối hoàn toàn (khóa); vẫn xóa được (nếu có `delete`) | Xóa |

**Điều kiện chuyển trạng thái:**

- `draft` / `rejected` → `submitted`: người tạo, người yêu cầu (khớp `requester_id`) hoặc có `write` nhấn "Gửi duyệt"; yêu cầu pass `validate()`.
- `submitted` → `approved`: người có `approve` **trong phạm vi phiếu** nhấn "Duyệt". **KHÔNG phân công NSTM ở bước này** (CR-034) — phiếu chỉ dừng ở hàng chờ của phòng thu mua.
- `approved` → `dispatched`: Admin / Quản lý thu mua nhấn **"Duyệt"** lần 2 ở phiếu Đã duyệt (`POST /api/purchase-requests/{id}/dispatch`); hệ thống chạy `auto_assign_by_category` phân bổ NSTM theo phân loại, rồi báo lại số dòng đã gán và số dòng còn trống (phân loại chưa cấu hình người phụ trách → chọn tay). Thông báo `pr_assigned` gửi cho NSTM ở bước này. Chỉ điều phối được đúng 1 lần, đúng từ `approved`.
- `submitted` → `rejected`: người có `approve` nhấn "Trả về" và nhập lý do; xóa nhân sự phụ trách (`assignee_id = 0`) + reset trạng thái mọi dòng về "Chưa đặt hàng".
- `submitted` → `cancelled`: người có `approve` nhấn "Từ chối phiếu" và nhập lý do; phiếu bị khóa hoàn toàn (không sửa được, chỉ xóa).
- `approved` / `dispatched` / `processing` → `rejected`: người có `cancel` nhấn "Trả về"; reset toàn bộ NSTM và trạng thái dòng về "Chưa đặt hàng" (trả về thì phải điều phối lại từ đầu).
- `approved` / `dispatched` / `processing` → `cancelled`: người có `cancel` nhấn "Từ chối phiếu" và nhập lý do.
- `dispatched` / `processing` → `completed`: thủ công qua nút "Hoàn thành" (người có `cancel`); BE kiểm tra mọi dòng phải ở "Hoàn thành" hoặc "Hủy đơn" — sẽ báo lỗi nếu còn dòng chưa xong; hoặc tự động khi `recompute_status` xét thấy tất cả dòng đã ở điểm cuối.
- `dispatched` → `processing`: tự động khi ít nhất 1 dòng có trạng thái khác "Chưa đặt hàng" và "Hủy đơn" (hàm `recompute_status`).

Chỉ trạng thái `draft` và `rejected` cho phép sửa nội dung header và dòng hàng. Sau khi duyệt, chỉ NSTM phụ trách (hoặc người có `approve`/`cancel`) cập nhật được trạng thái/tiến độ dòng qua endpoint `/item-status` và `/assign`.

**Công tắc bật/tắt bước duyệt lần 2 (CR-034a):** màn **Cấu hình hệ thống → Quy trình duyệt → "Yêu cầu mua hàng: bắt buộc thu mua duyệt lần 2 (điều phối)"** (key `pr_dispatch_enabled`, lưu DB, đổi có hiệu lực ngay, không cần deploy; `.env PR_DISPATCH_ENABLED` là giá trị dự phòng).

- **BẬT (mặc định):** đúng luồng 2 chặng mô tả ở trên.
- **TẮT:** bỏ hẳn chặng 2 — trưởng bộ phận nhấn Duyệt là hệ thống phân bổ NSTM ngay và phiếu đi thẳng sang `dispatched` (đúng luồng cũ trước CR-034). Nút duyệt lần 2 biến mất, `POST /dispatch` trả lỗi 400. Những phiếu đang kẹt ở `approved` từ lúc công tắc còn bật vẫn tạo được ĐMH / hoàn thành / tự suy trạng thái bình thường (nếu không sẽ không ai gỡ được cho chúng).

Người dùng ở màn chi tiết thấy **dòng nhắc màu vàng** khi phiếu ở `approved`: người có quyền điều phối được nhắc bấm Duyệt, người khác được cho biết phiếu còn chờ thu mua duyệt lần nữa. Công tắc TẮT thì không hiện dòng này.

**Chốt chặn tạo Đơn mua hàng (CR-034):** backend `_ensure_pr_dispatched` chặn tạo/sửa ĐMH tham chiếu YCMH đang ở `draft` · `submitted` · `approved` · `rejected` ("YCMH … chưa được điều phối (chưa có nhân sự phụ trách)") và `cancelled` ("đã bị từ chối"). Ẩn nút ở FE chỉ là tiện ích — chặn thật nằm ở backend. Mã YCMH gõ tay không khớp phiếu nào (dữ liệu cũ) thì không chặn.

---

## A. Thông tin chung (header phiếu)

### 1. Mã phiếu yêu cầu (`code`)

- Kiểu nhập: Nhập tay hoặc để trống (tự sinh)
- Mặc định: trống — hệ thống tự sinh theo định dạng `PYC{ddmmyy}{seq:02d}` dựa trên `request_date`
- Bắt buộc: Không (tự sinh nếu trống)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo (chỉ khi tạo mới, trường bị khóa sau khi phiếu đã lưu)
- Logic đặc biệt: Trường bị `disabled` sau lần tạo đầu tiên (`!isNew`). Mã hiển thị trên bản in khi `show_code_on_print = true`.

### 2. Ngày tạo (`created_at`)

- Kiểu nhập: Chỉ đọc (hệ thống — timestamp khi phiếu được khởi tạo)
- Mặc định: Thời điểm `INSERT` bản ghi (`AuditMixin.created_at`)
- Bắt buộc: — (hệ thống điền, không thay đổi được)
- Nguồn dữ liệu / liên kết: Cột `created_at` trong bảng `tab_purchase_request` (từ `AuditMixin`)
- Người sửa: Hệ thống (khóa hoàn toàn)
- Logic đặc biệt: Hiển thị cạnh "Ngày tiếp nhận" trên trang chi tiết khi xem phiếu đã tạo (`!isNew`), định dạng ngày+giờ đầy đủ qua `fmtDateTime`. Ẩn trên form tạo mới. Trả về trong API response (`_out()`).

### 3. Ngày tiếp nhận (`request_date`)

- Kiểu nhập: Chọn ngày (date input)
- Mặc định: Ngày hiện tại (hôm nay, `new Date().toISOString().slice(0,10)`)
- Bắt buộc: Có (đánh dấu `*` trên UI)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Ngày này ảnh hưởng đến định dạng mã tự sinh (`ddmmyy` lấy từ `request_date`).

### 4. Công ty nhận hóa đơn (`company_id`)

- Kiểu nhập: Chọn (SearchSelect, tìm kiếm theo tên)
- Mặc định: 0 (chưa chọn); tự điền từ công ty của Nhân sự YC nếu nhân sự đã có `company_id`
- Bắt buộc: Có (`validate()` kiểm tra: "Vui lòng chọn Công ty")
- Nguồn dữ liệu / liên kết: Bảng Công ty (`company`), API `/api/companies`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Tên công ty (`company_name`) được tra cứu và gắn vào response để hiển thị; không lưu riêng.

### 5. Nhân sự yêu cầu (`requester` + `requester_id`)

- Kiểu nhập: Chọn (SearchSelect, tìm theo tên đầy đủ); lưu tên vào `requester`, ID nhân sự vào `requester_id`
- Mặc định: Tự điền tên người đang đăng nhập (khớp email hoặc full_name với danh sách nhân sự)
- Bắt buộc: Có (`validate()` kiểm tra: "Vui lòng chọn Nhân sự yêu cầu")
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`employee`), API `/api/employees`
- Người sửa: Người có `write` (TP/QL); nhân viên thường (`isStaff`) bị khóa trường này — chỉ điền tên mình
- Logic đặc biệt: Chọn nhân sự tự điền `requester_position`, `department`, `head_of_dept`, `company_id` theo dữ liệu nhân sự đó. `requester_id` (ID nhân sự, ẩn trên UI) dùng để xác định quyền: người yêu cầu (khớp `employee_id` của tài khoản đăng nhập với `requester_id` trên phiếu) được sửa, gửi duyệt và xem toàn bộ dòng hàng của phiếu, kể cả khi admin tạo phiếu giùm.

### 6. Chức vụ (`requester_position`)

- Kiểu nhập: Nhập tay (tự điền khi chọn Nhân sự YC)
- Mặc định: trống; tự điền từ `employee.position` (Vị trí / Chức vụ trong hồ sơ nhân sự)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Tự điền từ `employee.position`; có thể sửa thủ công sau
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`

### 7. Bộ phận yêu cầu (`department`)

- Kiểu nhập: Tự động (trường bị khóa `disabled`)
- Mặc định: trống; tự điền theo phòng ban của Nhân sự YC đã chọn
- Bắt buộc: — (hệ thống điền, không sửa trực tiếp)
- Nguồn dữ liệu / liên kết: Lấy tên phòng ban từ `employee.department_id` → `department.name`
- Người sửa: Hệ thống (thay đổi khi đổi Nhân sự YC)

### 8. Trưởng bộ phận (`head_of_dept`)

- Kiểu nhập: Tự động (trường bị khóa `disabled`)
- Mặc định: trống; tự điền từ trưởng phòng của bộ phận
- Bắt buộc: Có (đánh dấu `*` trên UI); điền tự động nên ít khi trống nếu phòng ban đã có trưởng
- Nguồn dữ liệu / liên kết: Tra qua `Department.manager_id` → `Employee.full_name`; hoặc qua API `/api/purchase-requests/meta/dept-head` (người không có quyền xem DS nhân sự cũng tra được)
- Người sửa: Hệ thống (cập nhật khi đổi Nhân sự YC; BE cũng tự điền khi tạo qua `find_dept_head`)

### 9. Đơn gấp (`is_urgent`)

- Kiểu nhập: Checkbox
- Mặc định: Không tích (`false`)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Khi tích, hệ thống gắn cờ ưu tiên trong thông báo (`is_urgent=true` được truyền vào `trigger_notification`). Danh sách hiển thị badge "Gấp" màu cam.

### 10. Mục đích mua hàng (`purpose`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Có (đánh dấu `*` trên UI)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Trường này được dùng làm tiêu đề phiếu trên trang chi tiết (`pr.purpose || pr.code`). Phiếu khảo sát (Survey) liên kết PYC cũng tự điền `requirement_detail` từ trường này.

### 11. Nội dung mua hàng (`note`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`

### 12. NSTM phụ trách phiếu (`assignee_id`)

- Kiểu nhập: Tự động (gán qua endpoint `PATCH /assign`, không có ô nhập trực tiếp trong form header)
- Mặc định: 0 (chưa gán)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`employee`)
- Người sửa: Người có `approve` (qua endpoint `PATCH /{pid}/assign`); tự động điền khi duyệt nếu truyền `assignee_id` vào `ApproveIn` (CR-034: bước "Duyệt" không còn tự phân bổ NSTM dòng — việc đó chuyển sang bước **Điều phối**)
- Logic đặc biệt: Ảnh hưởng đến data scope + lọc DÒNG hàng (`_see_all_items` trong `purchase_request/controller.py`). Nhân viên thu mua scope `assigned`/`own` **chỉ thấy dòng có `assignee` = mã NV mình**. Người tạo phiếu / người yêu cầu (`requester_id`) / người có `approve` / người có scope `proc`/`dept`/`company`/`all` **thấy mọi dòng** của phiếu — trong đó **Admin thu mua (`pur_admin`) scope `proc` thấy đủ mọi dòng** (bổ sung `proc` vào `_see_all_items` ở CR-013, 2026-08-04; trước đó admin bị coi như NV được giao nên thấy trống). Hàm không đọc `assignee`, nên admin dù được giao 1 dòng vẫn thấy full.

### 13. Hiện mã trên bản in (`show_code_on_print`)

- Kiểu nhập: Checkbox (ẩn trong form chính, có trong schema)
- Mặc định: `true`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Kiểm soát việc hiển thị mã PYC trên bản in (`/print/purchase-request/:id`).

### 14. Nhà cung cấp đề xuất — 2 cụm (`supplier_req` / `supplier_pur`)

Thông tin NCC được lưu theo 2 cụm trong cột `supplier_info` (JSON). Mỗi cụm gồm 3 trường: `name` (tên NCC), `tax_code` (mã số thuế), `contact` (SĐT / email / địa chỉ).

**Cụm req — Bộ phận yêu cầu đề xuất (`supplier_req`):**

- Kiểu nhập: Nhập tay (3 ô: tên / MST / liên hệ)
- Mặc định: trống
- Bắt buộc: Không
- Người sửa: Ai cũng sửa được (kể cả người yêu cầu không có quyền xem NCC), khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Cụm do bộ phận người dùng tự điền trước khi gửi duyệt. Không yêu cầu quyền `supplier.read`.

**Cụm pur — Khảo sát / Thu mua (`supplier_pur`):**

- Kiểu nhập: Nhập tay (3 ô: tên / MST / liên hệ)
- Mặc định: trống
- Bắt buộc: Không
- Người sửa: Chỉ người có `supplier.write` (Quản lý / Admin thu mua), khi phiếu ở `draft` hoặc `rejected`; cũng cập nhật khi nhập từ khảo sát
- Quyền xem: Chỉ người có `supplier.read` mới thấy cụm này; người khác nhận về cụm rỗng
- Logic đặc biệt: Cụm này được ghi vào khi nhập liệu từ kết quả khảo sát NCC (`supplier_from_survey = true`).

**NCC hiệu lực (cột cũ `suggested_supplier*`):**

Các cột `suggested_supplier`, `suggested_supplier_tax_code`, `suggested_supplier_contact` được giữ lại và tự động đồng bộ: nếu `supplier_pur.name` có giá trị thì hiệu lực = cụm `pur`, ngược lại = cụm `req`. Các cột này dùng trong danh sách, bản in, và prefill ĐMH. Người không có `supplier.read` nhận về chuỗi rỗng cho cả 3 cột này.

### 15. Báo giá đính kèm (`quote_filename` + `quote_file_url`)

- Kiểu nhập: Upload file (1 file, chọn qua nút "Chọn báo giá")
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Lưu trên Cloudflare R2 qua API `/api/attachments` (entity `purchase_request_quote`); URL trả về ghi vào `quote_file_url`, tên file ghi vào `quote_filename`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Chỉ upload được sau khi phiếu đã được tạo (`!isNew`). Xóa file chỉ xóa tham chiếu (reset về trống), không xóa file trên R2.

### 16. Tỷ lệ VAT mặc định (`vat_rate`)

- Kiểu nhập: Số (không hiển thị trên form UI hiện tại)
- Mặc định: `0.08` (8%)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Qua API (không có ô nhập trực tiếp trên form)
- Logic đặc biệt: Được dùng làm VAT mặc định khi prefill dòng ĐMH từ phiếu (trường `vat` trong ĐMH). VAT thực tế của từng dòng PYC được lưu theo trường `vat_pct` cấp dòng (nhập số, dưới 100% — xem mục 8 phần C). **Lưu ý đơn vị:** `vat_rate` header lưu dạng **tỉ lệ** (0.08), còn `vat_pct` cấp dòng lưu dạng **phần trăm** (8). Giá trị `vat_rate` header vẫn được truyền sang ĐMH khi tạo từ phiếu.

---

## B. Dòng hàng (items)

Mỗi dòng = một sản phẩm / vật tư yêu cầu mua. Bảng tóm tắt hiện các cột chính; toàn bộ trường xem và sửa trong popup "Chi tiết dòng".

### 1. Mã hàng (`product_code`)

- Kiểu nhập: Chọn sản phẩm (ProductPicker — tìm theo mã hoặc tên)
- Mặc định: trống
- Bắt buộc: Có (khi dòng có `product_name`, `validate()` yêu cầu phải chọn mã hàng từ danh mục: "cần chọn Mã hàng (chọn từ danh mục)")
- Nguồn dữ liệu / liên kết: Danh mục Sản phẩm (`product`), API `/api/products`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Chọn mã tự điền `product_name`, `unit`, `item_group`, `group_desc`. Nhập thủ công `product_name` mà không chọn mã sẽ bị chặn khi gửi duyệt.
- **DUY NHẤT trên phiếu (CR-047)**: mỗi mã hàng chỉ được đứng ở **1 dòng**. Cần mua thêm cùng một mã thì **cộng số lượng vào một dòng**, đừng thêm dòng thứ hai. Ô mã trùng được tô đỏ ngay khi nhập; bấm Lưu sẽ báo `Mã hàng bị trùng: <mã>`. Xem quy tắc 22 mục C.
- **Tham chiếu giá cũ**: sau khi chọn mã hàng, trong ô có nút mở **Lịch sử mua hàng** của mặt hàng đó (từng mua của NCC nào, giá bao nhiêu). Chọn 1 dòng lịch sử sẽ điền ĐVT / SL / đơn giá / VAT vào dòng, **không tự lưu**. Nút chỉ hiện khi dòng còn sửa được — xem `04-don-mua-hang.md` mục I và tài liệu riêng `12-lich-su-mua-hang.md`. Từ CR-058, VAT của lần mua trước được điền **nguyên giá trị** (trước đây chỉ điền khi trùng một trong các mức 0/5/8/10, không trùng thì âm thầm bỏ qua); chỉ số rác (âm hoặc ≥ 100) mới bị bỏ để giữ VAT đang có của dòng.
- **Người yêu cầu KHÔNG thấy Nhà cung cấp trong popup này (CR-060)**: popup mở được từ YCMH, mà route `/api/products/{code}/purchase-history` chỉ đòi `product.read` — nên trước đây người yêu cầu (không có `supplier.read`) vẫn đọc nguyên tên/mã NCC, trong khi mọi màn khác đã che theo quy tắc 2 cụm NCC ở mục A.14. Nay **backend** tự xóa `supplier_code`/`supplier_name` khỏi dữ liệu trả về, **và bỏ luôn tên NCC khỏi vế tìm kiếm** — chỉ che cột thôi thì gõ tên một NCC rồi xem có ra dòng nào là suy ngược ra được ai bán mã hàng đó. Giao diện ẩn hẳn cột cho gọn, nhưng đó chỉ là trang trí: chốt chặn nằm ở server.

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
- Logic đặc biệt: Khi chọn Phân loại, tự điền `group_desc` với thông tin thời gian sản xuất tiêu chuẩn. Phân loại cũng được dùng để tự phân công NSTM khi **điều phối** phiếu (`auto_assign_by_category`) — CR-034 chuyển bước này từ "Duyệt" sang "Điều phối".

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
- Logic đặc biệt: Dùng trong công thức tính Thành tiền: `qty × price × (1 + vat_pct / 100)`.

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
- Logic đặc biệt: Dùng trong công thức tính Thành tiền cùng với `vat_pct`.

### 8. % VAT theo dòng (`vat_pct`)

- Kiểu nhập: Nhập số (%) — **0 ≤ VAT < 100**, tối đa 2 số thập phân (sửa được cả trong bảng dòng hàng lẫn popup chi tiết dòng)
- Mặc định: 8 (tức 8%)
- Bắt buộc: Không (có giá trị mặc định)
- Nguồn dữ liệu / liên kết: `tab_survey_request_option.snap_vat` khi phiếu sinh từ **Yêu cầu báo giá**
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Được dùng để tính Thành tiền gồm VAT: `qty × price × (1 + vat_pct / 100)`. Trước CR-058 ô này là select cố định 0/5/8/10% nên thuế suất khác (vd 3,5%) không nhập được; nay nhập số tự do, ô nhập **kẹp về 99,99 ngay khi gõ** quá và server chặn lại (`ge=0, lt=100`). Phiếu tạo từ **Yêu cầu báo giá** (`create_prs`) lấy VAT theo phương án đã chọn — **trước CR-058 bước này bị bỏ sót**, dòng nhận 0% và `amount` thiếu thuế; YCMH tạo theo lối cũ cần kiểm lại cột VAT trước khi tạo ĐMH.

### 9. Thành tiền (`amount`)

- Kiểu nhập: Tự tính
- Mặc định: 0
- Bắt buộc: — (hệ thống tính, không sửa)
- Nguồn dữ liệu / liên kết: `qty × price × (1 + vat_pct / 100)` (tính ở FE và lưu vào DB tại hàm `_save_items`)
- Người sửa: Hệ thống (chỉ hiển thị)
- Logic đặc biệt: Thành tiền GỒM VAT. Phiếu hiển thị 3 dòng tổng kết: Tiền hàng chưa VAT (`subtotal = sum(qty × price)`), Tiền VAT (`vat = total − subtotal`), Tổng cộng gồm VAT (`total = sum(amount)`).

### 10. Kho nhận (`warehouse`)

- Kiểu nhập: Chọn (select từ danh sách kho) trong bảng; hoặc SearchSelect trong popup chi tiết
- Mặc định: trống
- Bắt buộc: Có (`validate()` yêu cầu `warehouse` không trống cho mỗi dòng có `product_name`)
- Nguồn dữ liệu / liên kết: Bảng Kho (`warehouse`), API `/api/warehouses`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`

### 11. Ngày cần hàng (theo dòng) (`required_date`)

- Kiểu nhập: Chọn ngày (date input)
- Mặc định: trống
- Bắt buộc: Có (đánh dấu `*`; `validate()` yêu cầu cho mỗi dòng có `product_name`: "cần nhập Ngày cần hàng")
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Trường cấp dòng, khác với `need_date` ở header phiếu (cấp phiếu toàn bộ, hiện chưa hiển thị trên form chi tiết nhưng là cột hiển thị trên trang danh sách).

### 12. Thời gian dự kiến có hàng (`expected_date`)

- Kiểu nhập: Chọn ngày (date input) — sửa trực tiếp trên bảng (nếu có quyền dòng) hoặc trong popup chi tiết dòng
- Mặc định: **lấy theo "Ngày cần hàng" (`required_date`) của chính dòng đó** (CR-064) — chỉ điền lúc TẠO dòng, sau đó sửa được. Dòng nhân bản từ phiếu khác cũng khởi tạo lại theo Ngày cần hàng chứ không bê ngày dự kiến của phiếu gốc. Đổi Ngày cần hàng về sau KHÔNG kéo ngày dự kiến chạy theo.
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Hai chiều với **"Dự kiến có hàng" của dòng ĐMH** (`tab_po_item.expected_date`) — nối theo `pr_code` + `product_code` (CR-062)
- Người sửa: NSTM được giao dòng hoặc người có `approve`/`cancel` (qua endpoint `PATCH /{pid}/item-status`, trường `expected_date`)
- Logic đặc biệt: Khi đổi giá trị ĐÃ CÓ (tức `expected_date` trước đó không trống), BE yêu cầu kèm `expected_date_reason`; thiếu lý do sẽ trả về HTTP 400. Nếu giá trị cũ trống thì cập nhật tự do. Thay đổi được ghi vào audit log. Lưu lại phiếu (`PUT`/`POST` cả phiếu) KHÔNG đụng tới ô này — payload dòng không mang `expected_date`.
- Báo cho người yêu cầu (CR-062): mỗi lần ngày này thực sự đổi trên YCMH, hệ thống gửi thông báo `pr_expected_date_changed` cho **người yêu cầu** (tài khoản của `requester_id`, không có thì người tạo phiếu) — nội dung liệt kê `tên hàng: ngày cũ → ngày mới · lý do`. Người vừa thao tác không tự nhận thông báo của chính mình.
- Đồng bộ với ĐMH (CR-062) — một dòng YCMH có thể trải ra NHIỀU ĐMH:
  - **Chép xuống:** khi lưu ĐMH, dòng ĐMH nào còn TRỐNG ô "Dự kiến có hàng" thì lấy giá trị của dòng YCMH cùng mã hàng. Ô đã có giá trị thì giữ nguyên.
  - **Cuộn ngược:** `sync_from_purchase_orders` lấy ngày **MUỘN NHẤT** trong các dòng ĐMH liên kết (bỏ ô trống, bỏ dòng Hủy đơn) — đó là lúc dòng được đáp ứng đủ.
    - Ô trên YCMH còn TRỐNG → ghi thẳng (đúng nhánh mà luật trên cho sửa tự do).
    - Ô trên YCMH đã có và LỆCH → **KHÔNG ghi đè và KHÔNG báo gì ở phía YCMH**. Người đang sửa ĐMH đã thấy popup cảnh báo lệch ngày ngay trên màn hình đơn (xem 04 §10a); sửa hay không là quyền của NSTM, và khi họ sửa thật trên YCMH thì mới phát thông báo cho người yêu cầu như trên. Ghi đè ở đây sẽ đi vòng qua luật "đổi ngày phải kèm lý do".

### 13. SL đã đặt / SL đã nhận (`qty_ordered` / `qty_received`)

- Kiểu nhập: Chỉ đọc (hệ thống đồng bộ từ ĐMH)
- Mặc định: 0
- Bắt buộc: — (hệ thống điền)
- Nguồn dữ liệu / liên kết: Đồng bộ từ các ĐMH cùng mã PYC (gộp theo `product_code`); chạy khi ĐMH thay đổi trạng thái dòng (`sync_from_purchase_orders`)
- Người sửa: Hệ thống (khóa hoàn toàn)
- Logic đặc biệt: Hiển thị trên bảng cột "Tiến độ nhận / đặt". `qty_ordered` = tổng SL đã đặt từ các ĐMH đã duyệt trở đi; `qty_received` = tổng SL đã nhận (từ chứng từ nhận hàng). Dùng để tính "còn thiếu" khi tạo ĐMH mới.

### 14. Nhân sự phụ trách dòng (`assignee`)

- Kiểu nhập: Chọn (SearchSelect, chỉ hiện cho người có quyền duyệt); lưu Mã NV
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Danh sách nhân sự phòng thu mua (`employee.department` chứa "thu mua"), API `/api/employees`
- Người sửa: Người có `approve` (trực tiếp trong popup chi tiết dòng hoặc qua endpoint `PATCH /{pid}/assign`); **tự động gán khi ĐIỀU PHỐI phiếu** (CR-034 — trước đây gán ngay lúc TP duyệt). Dòng đã chọn tay trước khi điều phối thì giữ nguyên, không bị ghi đè.
- Logic đặc biệt: Lưu mã NV (`employee.code`), hiển thị tên đầy đủ nhân sự (`employee.full_name`). Cột "NSTM phụ trách" chỉ hiển thị trên bảng khi người dùng có quyền xử lý khảo sát (`survey_request:process`). NSTM chỉ thấy dòng mà `assignee` trùng với `emp_code` của mình (khi không có quyền `approve`/`read` dept+).

### 15. Trạng thái xử lý dòng (`line_status`)

- Kiểu nhập: Chỉ đọc trên bảng (tự đồng bộ từ ĐMH); hoặc chọn trong popup chi tiết khi chưa có ĐMH
- Mặc định: `Chưa đặt hàng`
- Bắt buộc: Không (có giá trị mặc định)
- Nguồn dữ liệu / liên kết: Danh sách 5 mức cố định: `Chưa đặt hàng / Đã đặt hàng / Đã nhận hàng / Hoàn thành / Hủy đơn`
- Người sửa: NSTM được giao dòng, hoặc người có `approve`/`cancel`; cập nhật qua popup (endpoint `PATCH /{pid}/item-status`). Sau khi phiếu có ĐMH liên kết, trạng thái tự đồng bộ theo tiến độ ĐMH.
- Logic đặc biệt: Thay đổi trạng thái dòng kích hoạt `recompute_status` tự điều chỉnh trạng thái phiếu. Dòng "Hủy đơn" tô đỏ toàn bộ hàng trong danh sách phiếu (`has_cancelled_line`). Khi trả phiếu về ("Bị trả lại"), tất cả dòng reset về "Chưa đặt hàng". Dòng YCMH thủ công đặt "Hủy đơn" sẽ được giữ nguyên khi đồng bộ từ ĐMH.

### 16. Chi tiết tiến độ (`progress_note`)

- Kiểu nhập: Nhập nhiều dòng (textarea, trong popup chi tiết dòng)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSTM được giao dòng hoặc người có `approve`/`cancel`; cả khi phiếu đang ở các trạng thái không phải draft (qua endpoint `PATCH /{pid}/item-status`)

### 17. Ghi chú khác (`note`, cấp dòng)

- Kiểu nhập: Nhập nhiều dòng (textarea, trong popup chi tiết dòng)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write` (khi phiếu `draft`/`rejected`), hoặc NSTM / người có `approve`/`cancel` (qua endpoint `PATCH /{pid}/item-status`)

---

## C. Quy tắc nghiệp vụ

1. Lưu (Nháp): lọc bỏ dòng không có `product_name`; dòng còn lại được lưu theo cơ chế upsert — dòng có `id` thì cập nhật tại chỗ (giữ nguyên `id`), dòng không có `id` thêm mới, dòng cũ không còn trong danh sách thì xóa (`_save_items`). Cơ chế upsert thay cho DELETE+INSERT cũ, giữ nguyên `id` để ảnh đính kèm theo dòng (`purchase_request_line_image`) không bị mồ côi.
2. Gửi duyệt: kiểm tra `validate()` — phải có `company_id`, `requester`, ít nhất 1 dòng có `product_name`; mỗi dòng đó phải có `product_code` (chọn từ danh mục), `qty > 0`, `warehouse` và `required_date`. Nếu không pass, thông báo lỗi cụ thể từng trường.
3. Mã phiếu tự sinh: định dạng `PYC{ddmmyy}{seq:02d}`, trong đó `ddmmyy` lấy từ `request_date` (không có thì lấy ngày hiện tại), `seq` là số thứ tự tăng dần trong ngày.
4. Chọn Nhân sự YC: tự điền `requester_position` (chức vụ), `department` (phòng ban), `head_of_dept` (trưởng bộ phận theo `manager_id` của phòng ban), `company_id`. Trưởng bộ phận tra qua API `/api/purchase-requests/meta/dept-head` (với người không có quyền xem DS nhân sự).
5. Chọn Mã hàng: tự điền `product_name`, `unit`, `item_group`, `group_desc`.
6. Chọn Phân loại: tự điền `group_desc` với thời gian sản xuất tiêu chuẩn từ `item_group.std_days` và `item_group.std_days_unavail`.
7. Thành tiền: `amount = qty × price × (1 + vat_pct / 100)` (gồm VAT theo dòng). Tổng kết phiếu gồm 3 dòng: Tiền hàng chưa VAT (`subtotal = sum(qty × price)`), Tiền VAT (`vat = total − subtotal`), Tổng cộng gồm VAT (`total = sum(amount)`).
8. Phân quyền xem dòng: người tạo phiếu, người yêu cầu (khớp `requester_id`), và người có `approve` hoặc scope `dept`/`company`/`all` xem được mọi dòng; NSTM (scope nhỏ hơn) chỉ thấy dòng có `assignee` trùng với mã NV của mình.
9. Tự phân công NSTM khi duyệt: hàm `auto_assign_by_category` gán NSTM cho từng dòng theo bảng phân công phụ trách (`category_assignee`).
10. Trạng thái phiếu tự tính lại: sau mỗi lần NSTM cập nhật `line_status`, hàm `recompute_status` xét lại trạng thái phiếu (chỉ khi phiếu đang ở `approved`/`processing`/`completed`).
11. Nhân bản phiếu: `POST /api/purchase-requests/{id}/copy` (và alias `/clone`) tạo phiếu `draft` mới — copy toàn bộ header và dòng hàng (bao gồm `vat_pct` và `supplier_info`); người yêu cầu của bản sao = người bấm Nhân bản (không giữ người yêu cầu phiếu gốc); reset `assignee_id = 0`, `assignee = ""`, `line_status = "Chưa đặt hàng"`, `progress_note = ""`; mã mới tự sinh theo ngày tạo bản sao. Nút "Nhân bản" có trên trang chi tiết (cần `purchase_request:create`) và trên danh sách (cấu hình `cloneable = true`, endpoint `/clone`).
12. Xóa mềm: phiếu xóa được đánh dấu `is_deleted = true`, không xóa vật lý; xóa được khi `status` là `draft`, `rejected` (Bị trả lại) hoặc `cancelled` (Đã từ chối). Xóa hàng loạt qua `DELETE /api/purchase-requests?ids=...`.
13. Cờ Đơn gấp ngoài luồng sửa: endpoint riêng `PATCH /{pid}/urgent` cho phép bật/tắt `is_urgent` ngay cả khi phiếu đã duyệt (mọi trạng thái trừ `cancelled`), yêu cầu `purchase_request:write`; tự động đồng bộ xuống các ĐMH cùng `pr_code`.
14. Đồng bộ tiến độ từ ĐMH: khi ĐMH thay đổi trạng thái dòng, hàm `sync_from_purchase_orders` cập nhật `line_status`, `qty_ordered`, `qty_received` trên các dòng YCMH khớp `product_code`, rồi gọi `recompute_status`. Dòng YCMH thủ công đặt "Hủy đơn" thì giữ nguyên (không bị ghi đè từ ĐMH).
15. Tự hoàn thành Yêu cầu khảo sát liên quan: khi YCMH đạt trạng thái `completed`, hệ thống tự gọi `sr_service.auto_complete_from_pr` để tự động hoàn thành Yêu cầu khảo sát nếu mọi YCMH của nó đã xong.
16. Thông báo và Web Push: mỗi sự kiện tạo chuông trong app và đẩy Web Push (best-effort) tới thiết bị đã đăng ký của người nhận. Người nhận: Gửi duyệt (`pr_submitted`) → Trưởng bộ phận của người YC (chỉ TBP — không fallback QL/Admin). Duyệt (`pr_approved`) → người tạo + Quản lý TM + Admin TM. Từ chối (`pr_rejected`), Trả về (`pr_returned`), Hủy (`pr_cancelled`) → người tạo. Phân bổ NSTM (`pr_assigned`) → NSTM được gán (không tự báo mình).
17. Đính kèm tài liệu: mỗi phiếu có thể đính kèm nhiều file (entity `purchase_request`); riêng báo giá NCC đề xuất dùng entity riêng `purchase_request_quote` (chỉ 1 file). Cả hai lưu trên Cloudflare R2 qua API `/api/attachments`.
    - **Ảnh đối chiếu của dòng đính kèm được ngay khi phiếu chưa lưu (CR-060)**: popup "Chi tiết dòng" trước đây hiện dòng chữ *"Lưu phiếu trước để đính kèm…"* vì liên kết file cần id dòng thật — người dùng phải làm hai lượt cho một việc. Nay ô đính kèm có **chế độ chờ lưu**: chưa có id thì file được giữ ở trình duyệt, vẫn xem trước / xóa / kéo-thả bình thường; bấm **Lưu** phiếu xong hệ thống mới tải file lên và gắn vào dòng vừa có id.
    - Khớp dòng gửi đi với dòng server trả về **không theo thứ tự** (server không sắp xếp, dòng cũ giữ id cũ lẫn dòng mới vừa được cấp id): khớp lần lượt theo **id → mã hàng** (duy nhất trên phiếu, xem quy tắc 22) **→ tên hàng**. Ghép theo vị trí sẽ gắn ảnh nhầm dòng.
18. Dòng "Hủy đơn": khi ít nhất 1 dòng có `line_status = "Hủy đơn"`, danh sách tô đỏ toàn bộ hàng đó (`rowStyle`, qua field `has_cancelled_line` trong response).
19. Nút "Tạo đơn mua hàng": Hiển thị khi phiếu ở `approved` hoặc `processing`, người dùng có quyền `purchase_order:create` và thuộc phòng thu mua / có quyền `approve` / `cancel`, đồng thời còn ít nhất 1 dòng có `line_status = "Chưa đặt hàng"`. Khi bấm, tự điền header ĐMH từ phiếu (mã PYC nguồn, công ty, bộ phận...) và điền NSPT của ĐMH = tên đầy đủ (`full_name`) của người phụ trách dòng đầu tiên có `assignee` trong YCMH; nếu không có dòng nào có `assignee` thì để trống (ĐMH tự lấy người tạo làm NSPT). Số lượng từng dòng được prefill theo "còn thiếu" (yêu cầu − đã đặt trong các ĐMH cùng mã PYC); dòng đã đặt đủ/vượt hiện cảnh báo trước khi cho mua thêm.
20. Điều hướng PYC ↔ ĐMH: Trên trang chi tiết YCMH, nút "ĐMH liên quan (N)" xuất hiện khi có ít nhất 1 đơn mua hàng cùng mã PYC; bấm mã ĐMH trong popup điều hướng sang trang chi tiết ĐMH tương ứng (`/purchase-orders/{id}`). Trên trang chi tiết ĐMH, trường "Mã PYC nguồn" có biểu tượng liên kết ngoài; bấm biểu tượng điều hướng ngược về trang YCMH tương ứng (`/purchase-requests/{id}`).

21. Nút "Tạo yêu cầu báo giá" (CR-026): hiện trên trang chi tiết YCMH khi phiếu ở trạng thái `rejected` (Bị trả lại) hoặc `cancelled` (Đã từ chối) và người dùng có quyền `survey_request:create`. Bấm nút sẽ mở màn **tạo YCBG** (`/survey-requests/new`) đã điền sẵn từ phiếu này — **không tạo bản ghi nào** cho tới khi người dùng bấm Lưu / Gửi duyệt (cùng cơ chế với CR-025).
    - Header chép sang: công ty, người yêu cầu (kèm `requester_id`), chức vụ, phòng ban, trưởng bộ phận, mục đích. Ghi chú được nối thêm dòng `(Tạo từ YCMH {code})` để giữ vết phiếu nguồn.
    - Dòng chép sang (bỏ dòng "Hủy đơn" và dòng trống tên hàng): `item_group` → Phân loại · `qty` → SL dự kiến · `unit` → ĐVT · `price` → Giá đề xuất · `note` → Yêu cầu khác. YCBG **không có ô mã/tên hàng**, nên `product_name` (nối thêm `group_desc` nếu có) được gộp vào **Chi tiết thông số** để không mất thông tin.
    - Không chép sang: mã phiếu, trạng thái, NSTM phụ trách, ngày tiếp nhận / ngày YC trả KQ (do thu mua và người YC nhập lại theo đợt khảo sát mới).
    - **Ảnh đối chiếu của dòng (CR-027):** mỗi dòng mang theo `src_pr_item_id` (id dòng YCMH nguồn); khi bấm **Lưu**, backend tự **kéo ảnh đối chiếu** của dòng YCMH đó sang dòng YCBG mới. Chỉ **thêm liên kết** (`tab_file_link`) trỏ vào **cùng file gốc** — không tải file lên lần nữa, không nhân bản dung lượng. Ảnh chỉ được kéo nếu người bấm **có quyền xem** phiếu YCMH nguồn (lọc bằng `apply_scope` trên `purchase_request`). Xóa dòng/phiếu YCBG chỉ gỡ liên kết của nó, **ảnh bên YCMH vẫn còn nguyên**.
    - **Không** tạo liên kết YCMH ↔ YCBG trong `tab_survey_request_pr`: bảng đó chỉ ghi chiều **YCBG → YCMH** (YCMH sinh ra từ phương án khảo sát) và được dùng để tự hoàn thành YCBG khi mọi YCMH con đã xong; gắn ngược một YCMH đã bị từ chối vào đó sẽ làm YCBG không bao giờ tự hoàn thành. Vết phiếu nguồn giữ ở **ghi chú** + nhãn `Từ {mã YCMH}` trên tiêu đề.
    - Phiếu YCMH gốc **giữ nguyên** trạng thái để truy vết; hệ thống không đánh dấu "đã thay thế".

22. **Mã hàng duy nhất trên phiếu (CR-047)**: một `product_code` chỉ được xuất hiện ở **1 dòng** của phiếu. Dòng chưa chọn mã (để trống) không bị tính trùng.
    - **Vì sao**: dòng ĐMH nối ngược về dòng YCMH bằng **chuỗi `product_code`**, không có khóa dòng. `sync_from_purchase_orders` (quy tắc 14) cộng dồn SL đặt/nhận **theo mã** rồi ghi **cùng một con số** vào **mọi** dòng trùng mã → tiến độ nhân đôi, kéo theo `line_status` và `recompute_status` sai. Ví dụ thật: PYC 143 có 2 dòng NLT0330, cả hai đều hiện `2.109 / 2.000`.
    - **Chặn ở 3 chỗ**: `_save_items` của YCMH và của ĐMH (`app/core/utils.assert_unique_product_codes`), và `survey_request.create_prs` — 2 phương án khảo sát của **cùng một NCC** gắn trùng mã VTBB thì chặn **trước** vòng lặp tạo phiếu (vòng lặp commit theo từng NCC, báo lỗi giữa chừng sẽ để lại vài YCMH tạo dở).
    - **Chỉ chặn TRÙNG MỚI** (số lần xuất hiện của một mã **tăng** so với dữ liệu đang lưu): phiếu/đơn cũ đã lỡ trùng vẫn sửa và lưu lại được. Nếu chặn cứng thì các ĐMH cũ sẽ khóa chết — dòng ĐMH ở "Hoàn thành"/"Hủy đơn" bị khóa và giao diện **không có nút xóa**, không ai gỡ được dòng trùng ra để lưu.
    - Không migration, không sửa dữ liệu cũ. Các dòng đã trùng phải **gộp tay**.
    - Muốn bỏ hẳn ràng buộc này (để hỗ trợ cùng một mã nhận ở **hai Kho** khác nhau) thì phải nối dòng bằng khóa dòng — xem việc còn nợ **N-004** trong `../tai-lieu-ky-thuat/change-log.md`.

## D. Quyền thao tác (RBAC)

Entity: `purchase_request`

| Thao tác | Quyền yêu cầu | Điều kiện trạng thái |
|----------|---------------|----------------------|
| Xem danh sách | `purchase_request:read` | mọi trạng thái (theo phạm vi dữ liệu của grant) |
| Xem chi tiết phiếu | `purchase_request:read` | mọi trạng thái (theo phạm vi) |
| Xem chi tiết dòng (tất cả dòng) | `purchase_request:read` + là người tạo, người yêu cầu (khớp `requester_id`), có `approve`, hoặc scope `dept`/`company`/`all` | mọi trạng thái; NSTM chỉ thấy dòng được giao |
| Tạo mới / Nhân bản | `purchase_request:create` | — |
| Sửa nội dung header + dòng | `purchase_request:write` hoặc là người tạo phiếu hoặc người yêu cầu (khớp `requester_id`) | `draft`, `rejected` |
| Gửi duyệt | `purchase_request:write` hoặc là người tạo phiếu hoặc người yêu cầu (khớp `requester_id`) | `draft`, `rejected` |
| Duyệt | `purchase_request:approve` | `submitted` |
| Trả về (→ `rejected`) | `purchase_request:approve` (tại `submitted`) hoặc `purchase_request:cancel` | `submitted`, `approved`, `processing` |
| Từ chối phiếu (→ `cancelled`) | `purchase_request:approve` (tại `submitted`) hoặc `purchase_request:cancel` | `submitted`, `approved`, `processing` |
| Phân bổ NSTM | `purchase_request:approve` | mọi trạng thái trừ `cancelled`, `completed` |
| Cập nhật trạng thái / tiến độ / `expected_date` dòng | `purchase_request:read` + là NSTM phụ trách hoặc có `approve`/`cancel` | mọi trạng thái sau duyệt (trừ `cancelled`, `completed`) |
| Bật / tắt cờ Đơn gấp ngoài luồng sửa | `purchase_request:write` | mọi trạng thái trừ `cancelled` |
| Hoàn thành | `purchase_request:cancel` | `approved`, `processing` (yêu cầu mọi dòng ở "Hoàn thành"/"Hủy đơn") |
| Xóa | `purchase_request:delete` | `draft`, `rejected`, `cancelled` |
| In phiếu | `purchase_request:read` (hoặc `print` nếu cấu hình riêng) | mọi trạng thái |

## E. Bộ lọc danh sách

Trang danh sách `/purchase-requests` hỗ trợ các bộ lọc sau (khai báo trong `cruds.tsx` và xử lý ở controller):

| Tham số | Nhãn trên UI | Kiểu | Ghi chú |
|---------|-------------|------|---------|
| `code` | Mã PYC | Văn bản (LIKE) | Tìm theo mã phiếu |
| `company_id` | Công ty | Chọn (exact) | Source: `/api/companies` |
| `requester` | Người yêu cầu | Văn bản (LIKE) | Tìm theo tên nhân sự yêu cầu |
| `department` | Bộ phận YC | Chọn (LIKE) | Source: `/api/departments` |
| `assignee` | NSTM phụ trách | Chọn (exact — mã NV) | Lọc phiếu có ít nhất 1 dòng gán cho NSTM này; source: `/api/employees` |
| `item_group` | Phân loại | Chọn (LIKE) | Lọc phiếu có ít nhất 1 dòng thuộc phân loại này; source: `/api/item-groups` |
| `request_date` | Ngày tạo | Khoảng ngày (daterange) | Tham số `request_date_from` / `request_date_to` |
| `need_date` | Ngày cần hàng | Khoảng ngày (daterange) | Tham số `need_date_from` / `need_date_to` |
| `is_urgent` | Đơn gấp | Chọn (`true`/`false`) | Lọc đơn gấp / thường |
| `status` | Trạng thái | Chọn | `draft` (Nháp), `submitted` (Chờ duyệt), `approved` (Đã duyệt), `rejected` (Bị trả lại), `cancelled` (Đã từ chối), `processing` (Đang xử lý), `completed` (Hoàn thành) |

Tất cả bộ lọc kết hợp với nhau theo AND và áp dụng thêm `apply_scope` theo phân quyền dữ liệu của người dùng.

---

## F. Bản in phiếu đề xuất (`/print/purchase-request/:id`)

Hai mẫu chọn bằng nút gạt ở đầu trang:

- **Mẫu thường** — in đầy đủ thông tin người yêu cầu.
- **Mẫu thuế** — để trống toàn bộ thông tin người yêu cầu (tên, chức vụ, ô ký).

Riêng **Mẫu thường** có thêm nút **Có chữ ký / Không chữ ký** (CR-036): "Không chữ ký" bỏ ảnh chữ ký số
nhưng **vẫn in họ tên** dưới ô — dành cho bản đem đi ký tay, đúng nghĩa dòng *"(Ký, ghi rõ họ tên)"*.
Mẫu thuế không có nút này vì vốn để trống toàn bộ.

**Tên file khi lưu PDF (CR-057).** Trang in đặt `document.title` = **`<Mã PYC>-DDMMYYYY`** (ví dụ `PYC07082601-31072026`) qua hook `usePrintTitle` — trình duyệt và máy in ảo lấy đúng chuỗi đó làm tên file gợi ý, thay cho `Thu Mua Tool` mặc định. Ngày lấy `request_date` (ngày yêu cầu), không lấy ngày bấm in. Không phụ thuộc `show_code_on_print`: cờ đó chỉ chi phối việc **in mã lên giấy**, còn tên file thì luôn cần mã để phân biệt. Chi tiết cách làm: xem mục E của [04-don-mua-hang.md](04-don-mua-hang.md).

### Khối XÉT DUYỆT — tự điền chữ ký

Khối cuối phiếu có 4 ô ký: **Giám đốc · TP/BP mua hàng · TP/BP đề xuất · Người lập**.

Ở **Mẫu thường**, 3 trong 4 ô tự điền **ảnh chữ ký + họ tên**; **Mẫu thuế để trống toàn bộ**.

| Ô ký | Người ký | Trường API |
|---|---|---|
| Người lập | Người yêu cầu trên phiếu | `requester_signature` + `requester` |
| TP/BP đề xuất | Người bấm **Duyệt** (bước 1) | `approver_signature` + `approver_name` |
| TP/BP mua hàng | Người bấm **Điều phối** (bước 2, CR-034) | `dispatcher_signature` + `dispatcher_name` |
| Giám đốc | Không có bước duyệt tương ứng → **để trống, ký tay** | — |

Chữ ký lấy từ ảnh người dùng tự tải lên ở Trang cá nhân (`tab_user.signature`, xem
`09-thong-bao-va-trang-ca-nhan.md`). Ảnh in giới hạn 56×180px, cách dòng họ tên 10px
(CR-036 — cỡ cũ 40×150px in ra giấy quá nhỏ, tên lại dính sát nét ký).
Ai chưa tải chữ ký thì ô đó chỉ có họ tên, ký tay như cũ.

**Cách tra chữ ký Người lập** (`requester_signature`):

1. Tra theo **nhân sự người yêu cầu** (`requester_id`) → tài khoản đang hoạt động của nhân sự đó → `signature`.
2. Phiếu cũ chưa có `requester_id`: chỉ lấy chữ ký **người tạo phiếu** khi tên người tạo **trùng** với
   `requester`. Ràng buộc này để tránh in chữ ký người A dưới tên người B trong trường hợp thu mua
   lập phiếu hộ bộ phận khác.

**Cách tra chữ ký 2 ô duyệt** (`_approval_signers()` trong controller):

1. Tra **nhật ký thao tác** (audit log) của phiếu: bản ghi `action='approved'` gần nhất → người duyệt
   bước 1; `action='dispatched'` gần nhất → người điều phối bước 2.
2. **Chỉ in từ mốc trạng thái tương ứng trở đi**: ô "TP/BP đề xuất" cần trạng thái ≥ Đã duyệt,
   ô "TP/BP mua hàng" cần ≥ Đã điều phối. Phiếu bị **trả về / từ chối** thì cả hai ô rỗng lại —
   không in chữ ký duyệt của lần trước.
3. Công tắc `pr_dispatch_enabled` **tắt** (luồng 1 bước): một người làm cả 2 bước → hai ô cùng một
   chữ ký, đúng thực tế.

Helper dùng chung: `resolve_signature_by_employee()`, `resolve_signature()`, `resolve_actor()` trong
`app/core/audit.py`.

### Khổ giấy và cách xuống trang (CR-036)

- `@page { margin: 0 }` — bỏ lề khổ giấy nên trình duyệt **không còn chỗ vẽ** ngày giờ / tên tab /
  đường dẫn / số trang. Người dùng không phải tự tắt "Headers and footers" trong hộp thoại In.
  Lề thật (10mm trên/dưới, 12mm trái/phải) chuyển vào padding của `.print-doc`.
- `box-decoration-break: clone` — phiếu nhiều dòng hàng tràn sang trang 2 thì **mỗi trang vẫn đủ lề**.
  Không có nó, trang 1 chạy sát mép giấy (máy in cắt mất dòng cuối) và trang 2 bắt đầu ngay mép trên.
- Dải tiêu đề mục đặt `break-after: avoid` — không để tiêu đề đứng trơ cuối trang còn nội dung của nó
  lật sang trang sau.
- Khối XÉT DUYỆT đặt `break-inside: avoid` — 4 ô ký luôn nằm trọn trên một trang.

Dòng ghi chú nhỏ *"Phiếu đề xuất này được in từ hệ thống thu mua"* in ở **góc phải dưới của mọi trang**
(cả 2 mẫu). Khi in nó chuyển sang `position: fixed` nên trình duyệt lặp lại ở đúng góc từng tờ giấy;
neo theo khối phiếu (`absolute`) thì phiếu dài 2 trang sẽ rơi xuống giữa trang cuối.
