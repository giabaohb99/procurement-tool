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

### 8. Trưởng bộ phận (`head_of_dept` + `head_of_dept_id`)

- Kiểu nhập: **Ô chọn** (CR-071). Trước đây là trường khóa `disabled`; đổi vì phòng có phó phòng / quyền trưởng phòng cùng ký được, khóa cứng theo `manager_id` thì **in ra sai tên**.
- Mặc định: trưởng phòng của bộ phận (`Department.manager_id`). Bỏ chọn → quay về mặc định này.
- Bắt buộc: Có (đánh dấu `*` trên UI); điền tự động nên ít khi trống nếu phòng ban đã có trưởng
- Nguồn danh sách chọn: những người **thật sự duyệt được phiếu đó** — `GET /api/purchase-requests/meta/dept-head-candidates?department=&company_id=` (màn tạo mới) và `GET /api/purchase-requests/{pid}/dept-head-candidates` (màn sửa). Backend lọc bằng chính `apply_scope`. Danh sách rỗng → ô về dạng chữ khóa như cũ.
- Nguồn mặc định: `Department.manager_id` → `Employee.full_name`, hoặc API `/api/purchase-requests/meta/dept-head` (người không có quyền xem DS nhân sự cũng tra được)
- Người sửa: Người lập phiếu, khi phiếu còn sửa được (`draft` / `rejected`). Đổi Nhân sự YC sang phòng khác thì bỏ người đã chọn tay và lấy lại mặc định của phòng mới.
- **Ý nghĩa: LƯU TRỮ + IN, không phải phân quyền.** Chọn ai **không** khóa quyền duyệt của bất kỳ ai — ai có `purchase_request:approve` và phiếu nằm trong phạm vi của họ thì vẫn bấm Duyệt được y như trước. Lưu bằng **id nhân sự** (`head_of_dept_id`, `0` = theo mặc định phòng); cột `head_of_dept` là **bản chụp TÊN để in**, backend đồng bộ theo id mỗi lần tạo/sửa.

### 9. Đơn gấp (`is_urgent`)

- Kiểu nhập: Checkbox
- Mặc định: Không tích (`false`)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Khi tích, hệ thống gắn cờ ưu tiên trong thông báo (`is_urgent=true` được truyền vào `trigger_notification`). Danh sách hiển thị badge "Gấp" màu cam.
- **Tự bật Đơn gấp (CR-082).** Chỉ cần **1 dòng** có **"Ngày cần hàng" < "Ngày tiếp nhận" + số ngày QĐ của phân loại** là hệ thống tự tích cờ gấp cho cả phiếu. Thiếu **đúng một ngày** cũng tính là gấp — không có ngưỡng dung sai (cần trong 14 ngày mà phân loại quy định 15 ngày thì vẫn là gấp). Số ngày QĐ lấy **mốc dài nhất** (không sẵn hàng, thiếu thì mốc có sẵn, thiếu cả hai thì 15 ngày — xem CR-065), nên phân loại chưa khai báo số ngày vẫn được xét.
  - Bỏ qua: dòng **chưa nhập Ngày cần hàng**, dòng **Hủy đơn**, và phiếu **chưa có Ngày tiếp nhận** (không có mốc gốc thì không suy ra được ngày QĐ).
  - **Chỉ BẬT, không bao giờ tự tắt.** Sửa ngày cho đúng hạn thì cờ vẫn còn — bỏ gấp là việc của người dùng (ô tích / nút Đơn gấp). Nếu chính lần Lưu đó là hành động tắt cờ thì hệ thống tôn trọng, không bật lại ngay; nhưng lần Lưu sau, nếu ngày cần hàng vẫn sớm hơn quy định thì cờ được bật lại.
  - Chạy ở **backend** (nguồn sự thật) tại: tạo phiếu, lưu dòng hàng, **nhân bản phiếu**, và **gửi duyệt** — nên phiếu cũ tạo trước luật này cũng được đánh dấu đúng khi gửi duyệt, và thông báo duyệt đi kèm mức ưu tiên thật. Khi bật, cờ **đồng bộ xuống mọi ĐMH cùng `pr_code`** và ghi lý do vào nhật ký thao tác (tên hàng · ngày cần · ngày QĐ · số ngày của phân loại).
  - Trên form (FE): ô tích tự bật sẵn khi phiếu còn sửa được, kèm dòng chữ đỏ *"Tự động: N dòng có ngày cần hàng sớm hơn thời gian quy định của phân loại"* (đưa chuột vào xem danh sách dòng vi phạm).

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
- Bắt buộc: **KHÔNG** (bao-CR-310). Trước đây bắt buộc khi dòng có `product_name`; nay bỏ, giống phiếu khảo sát vốn có cả loại **có mã** lẫn loại **không mã** — người yêu cầu phải mua được thứ chưa nằm trong danh mục mà không phải chờ mở mã trước.
- Nguồn dữ liệu / liên kết: Danh mục Sản phẩm (`product`), API `/api/products`
- Người sửa: Người tạo / có `write`, khi phiếu ở `draft` hoặc `rejected`
- Logic đặc biệt: Chọn mã tự điền `product_name`, `unit`, `item_group`, `group_desc`. Gõ thẳng `product_name` mà không chọn mã thì **vẫn gửi duyệt được** — người lập tự điền ĐVT và phân loại.
- **Đánh đổi của dòng KHÔNG MÃ**: dòng ĐMH nối ngược về dòng YCMH bằng **chuỗi `product_code`** (`sync_from_purchase_orders`, quy tắc 14), nên dòng không mã **không được cộng tiến độ** `qty_ordered` / `qty_received` tự động — NSTM phải tự cập nhật `line_status`. Muốn bỏ hẳn ràng buộc này thì phải nối dòng bằng khóa dòng, xem việc còn nợ **N-004**.
- **DUY NHẤT trên phiếu (CR-047)**: mỗi mã hàng chỉ được đứng ở **1 dòng**. Cần mua thêm cùng một mã thì **cộng số lượng vào một dòng**, đừng thêm dòng thứ hai. Ô mã trùng được tô đỏ ngay khi nhập; bấm Lưu sẽ báo `Mã hàng bị trùng: <mã>`. Xem quy tắc 22 mục C.
- **Tham chiếu giá cũ**: sau khi chọn mã hàng, trong ô có nút mở **Lịch sử mua hàng** của mặt hàng đó (từng mua của NCC nào, giá bao nhiêu). Chọn 1 dòng lịch sử sẽ điền ĐVT / SL / đơn giá / VAT vào dòng, **không tự lưu**. Từ bao-CR-320 (ticket 36, 09/09/2026) nút hiện ở **mọi trạng thái** của phiếu: phiếu còn sửa được (nháp / bị từ chối) thì chọn để điền như cũ; phiếu đã gửi duyệt / đã duyệt / đã điều phối / hoàn thành thì popup mở **chỉ xem** (`readOnly`, không có cột Chọn, không ghi đè dòng) — trước đó nút bị ẩn hẳn nên thu mua không tra được giá cũ khi đang điều phối. Xem `04-don-mua-hang.md` mục I và tài liệu riêng `12-lich-su-mua-hang.md`. Từ CR-058, VAT của lần mua trước được điền **nguyên giá trị** (trước đây chỉ điền khi trùng một trong các mức 0/5/8/10, không trùng thì âm thầm bỏ qua); chỉ số rác (âm hoặc ≥ 100) mới bị bỏ để giữ VAT đang có của dòng.
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
- Mặc định: **lấy theo NGÀY QĐ CÓ HÀNG của Phân loại** (CR-065, thay cho CR-064) = `request_date` ("Ngày tiếp nhận" của phiếu) **+ số ngày QĐ của phân loại dòng đó**. Số ngày QĐ lấy **mốc DÀI NHẤT**: `item_group.std_days_unavail` (không sẵn hàng) → thiếu thì `std_days` (có sẵn) → thiếu cả hai thì **15 ngày**. Phiếu chưa có Ngày tiếp nhận thì để trống.
  - Chỉ điền lúc **TẠO dòng**, sau đó sửa được. Trên FE ngày được điền ngay khi chọn Phân loại (kể cả phân loại đến từ danh mục Sản phẩm), chỉ với dòng chưa lưu và ô còn trống; BE điền lại lúc lưu nếu ô vẫn trống.
  - Dòng nhân bản từ phiếu khác cũng khởi tạo lại theo ngày QĐ của phiếu mới chứ không bê ngày dự kiến của phiếu gốc.
  - Đổi "Ngày cần hàng" về sau KHÔNG kéo ngày dự kiến chạy theo (hai trường độc lập).
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
- Mặc định: `Chưa tạo đơn mua hàng` (CR-074 — trước đây là `Chưa đặt hàng`)
- Bắt buộc: Không (có giá trị mặc định)
- Nguồn dữ liệu / liên kết: Danh sách 6 mức cố định: `Chưa tạo đơn mua hàng / Chưa đặt hàng / Đã đặt hàng / Đã nhận hàng / Hoàn thành / Hủy đơn`
- Người sửa: NSTM được giao dòng, hoặc người có `approve`/`cancel`; cập nhật qua popup (endpoint `PATCH /{pid}/item-status`). Sau khi phiếu có ĐMH liên kết, trạng thái tự đồng bộ theo tiến độ ĐMH.
- Logic đặc biệt: Thay đổi trạng thái dòng kích hoạt `recompute_status` tự điều chỉnh trạng thái phiếu. Dòng "Hủy đơn" tô đỏ toàn bộ hàng trong danh sách phiếu (`has_cancelled_line`). Khi trả phiếu về ("Bị trả lại"), tất cả dòng reset về "Chưa tạo đơn mua hàng". Dòng YCMH thủ công đặt "Hủy đơn" sẽ được giữ nguyên khi đồng bộ từ ĐMH.

**Ranh giới hai nhãn đầu (CR-074).** Trước đây ba tình huống khác hẳn nhau cùng đeo một nhãn
"Chưa đặt hàng", người yêu cầu nhìn vào không biết NSTM đã bắt tay làm chưa. Nay tách:

| Nhãn | Nghĩa |
|---|---|
| **Chưa tạo đơn mua hàng** | Chưa ĐMH nào có dòng cho sản phẩm này (hoặc mọi ĐMH chứa nó đã bị hủy) |
| **Chưa đặt hàng** | ĐÃ có dòng ĐMH — **kể cả đơn còn Nháp / Chờ duyệt** — nhưng chưa bấm đặt hàng |

Nhãn đổi **ngay lúc lập đơn**, không đợi duyệt; **xóa đơn Nháp thì dòng quay lại "Chưa tạo đơn
mua hàng"** (`create_po`/`delete_po` đều gọi `_sync_pr`). Đơn `cancelled` không được tính là đã lập.
Từ "Đã đặt hàng" trở đi giữ nguyên luật cũ. Hai nhãn này đều được coi là "chưa động tới" khi suy
trạng thái phiếu (`LINE_STATUS_IDLE`) nên phiếu vừa điều phối xong **không** tự nhảy "Đang xử lý",
và nút "Tạo ĐMH" vẫn hiện khi dòng mới có đơn Nháp (dòng đó còn có thể cần thêm đơn cho NCC khác).

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
2. Gửi duyệt: kiểm tra `validate()` — phải có `company_id`, `requester`, ít nhất 1 dòng có `product_name`; mỗi dòng đó phải có `qty > 0`, `warehouse` và `required_date`. **`product_code` KHÔNG còn bắt buộc** từ bao-CR-310 (xem mục B.1). Nếu không pass, thông báo lỗi cụ thể từng trường. Luật khai một chỗ ở `frontend-v2/src/modules/procurement/utils/required-fields.ts`; backend không kiểm gì ở `submit_pr`.
3. Mã phiếu tự sinh: định dạng `PYC{ddmmyy}{seq:02d}`, trong đó `ddmmyy` lấy từ `request_date` (không có thì lấy ngày hiện tại), `seq` là số thứ tự tăng dần trong ngày.
4. Chọn Nhân sự YC: tự điền `requester_position` (chức vụ), `department` (phòng ban), `head_of_dept` (trưởng bộ phận theo `manager_id` của phòng ban), `company_id`. Trưởng bộ phận tra qua API `/api/purchase-requests/meta/dept-head` (với người không có quyền xem DS nhân sự). Sau đó **đổi được** sang người khác trong danh sách người duyệt được phiếu — chỉ đổi tên in, không đổi quyền duyệt (CR-071, xem §8).
5. Chọn Mã hàng: tự điền `product_name`, `unit`, `item_group`, `group_desc`.
6. Chọn Phân loại: tự điền `group_desc` với thời gian sản xuất tiêu chuẩn từ `item_group.std_days` và `item_group.std_days_unavail`; đồng thời điền `expected_date` = ngày QĐ có hàng (xem mục 12) cho dòng chưa lưu còn trống ô đó.
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
| Gắn phương án lên dòng (H) | `purchase_request:write` + là NSTM phụ trách dòng (hoặc scope `dept`/`company`/`all`) | `dispatched`, `processing`, `purchasing`, `purchased` |
| **Chốt phương án** (H) | là người yêu cầu (`created_by` / `requester_id`) **hoặc** `purchase_request:approve` | `dispatched`, `processing`, `purchasing`, `purchased` |
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
| `product` | Mã / tên hàng | Văn bản (LIKE) | **CR-069** — lọc phiếu có ít nhất 1 dòng hàng mà **Mã hàng HOẶC Tên hàng** chứa chuỗi đã gõ. Khớp **một phần**: gõ `5155` ra cả `HOP5155` lẫn `NHG5155`. Không phân biệt hoa/thường và **không phân biệt dấu** (collation `utf8mb4_0900_ai_ci`: gõ `thung` vẫn ra `thùng`) |
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
Bộ lọc đang đặt cũng là bộ lọc của **file xuất Excel** (chung hàm `_list_query`), nên lọc theo mã hàng
rồi bấm "Xuất Excel" sẽ ra đúng bấy nhiêu phiếu.

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
| TP/BP mua hàng | **Trưởng phòng** của phòng ban mà người bấm **Điều phối** (bước 2, CR-034) đang thuộc — `Department.manager_id` (bao-CR-397). Phòng chưa gán trưởng thì lùi về chính người điều phối | `purchasing_head_signature` + `purchasing_head_name` (cặp `dispatcher_*` = người bấm nút vẫn trả, giữ tương thích) |
| Giám đốc | Không có bước duyệt tương ứng → **để trống, ký tay** | — |

Chữ ký lấy từ ảnh người dùng tự tải lên ở Trang cá nhân (`tab_user.signature`, xem
`09-thong-bao-va-trang-ca-nhan.md`) — hoặc do **Nhân sự/quản trị đặt hộ** ở thẻ *Chữ ký cá nhân*
trên hồ sơ nhân viên (bao-CR-398, có ở cả hai giao diện; backend `POST/DELETE
/api/employees/{id}/signature`, quyền `employee.write`). Ảnh in giới hạn 56×180px, cách dòng họ
tên 10px (CR-036 — cỡ cũ 40×150px in ra giấy quá nhỏ, tên lại dính sát nét ký).
Ai chưa tải chữ ký thì ô đó chỉ có họ tên, ký tay như cũ.

**Bố cục ô ký** (bao-CR-389 → bao-CR-398): cả 4 ô cao **130px**, họ tên luôn **dồn xuống đáy ô**
để bốn cái tên thẳng hàng; ảnh chữ ký (nếu có) xếp ngay trên tên, ô không ảnh chừa ~100px trống
để ký tay. Bản trước (bao-CR-389/397) cho ô CÓ ảnh 94px căn giữa nên tên người có chữ ký nổi cao
hơn ba tên còn lại — khách chê lệch hàng trên phiếu PYC12092604.

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
3. **Ô "TP/BP mua hàng" KHÔNG in người bấm Điều phối** (bao-CR-397, 14/09/2026). Trên prod người
   bấm nút là **admin thu mua**, còn ô đó phải là chữ ký **trưởng phòng thu mua**. Hệ không có cờ
   "phòng thu mua", nên `_purchasing_head()` đi: tài khoản người điều phối → nhân sự →
   `department_id` → `Department.manager_id` (ô *Trưởng bộ phận* ở danh mục Phòng ban) → họ tên +
   chữ ký **theo nhân sự trưởng phòng** (`resolve_signature_by_employee`, ảnh phải khớp tên đang in;
   trưởng phòng chưa tải chữ ký thì ô chỉ có tên, **không mượn ảnh** của người điều phối).
   Không suy ra được (tài khoản chưa gắn nhân sự · nhân sự chưa có phòng · phòng chưa gán trưởng ·
   `manager_id` trỏ tới nhân sự đã xóa) → **lùi về người điều phối** như trước. Muốn ô này ra đúng
   người thì phải **gán Trưởng bộ phận cho phòng thu mua** ở danh mục Phòng ban.
4. Công tắc `pr_dispatch_enabled` **tắt** (luồng 1 bước): người duyệt bước 1 cũng ghi `dispatched`,
   nên ô "TP/BP mua hàng" ra **trưởng phòng của người duyệt** (thường chính là họ) — chấp nhận, vì
   luồng đó không có thu mua nào chạm vào phiếu.

Helper dùng chung: `resolve_signature_by_employee()`, `resolve_signature()`, `resolve_actor()` trong
`app/core/audit.py`. Test: `test/backend/test_pyc_print_purchasing_head_cr397.py`.

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

---

## G. Xuất Excel danh sách (CR-068)

Nút **"Xuất Excel"** nằm trên thanh công cụ màn danh sách YCMH, chỉ hiện với người có hành động
**`export`** trên `purchase_request`. Endpoint: `GET /api/purchase-requests/export/xlsx`.

**Xuất cái gì**

- Đúng **bộ lọc + thứ tự sắp xếp** đang áp trên bảng, và đúng **các cột đầu phiếu đang hiển thị**
  (theo lựa chọn cột của từng người). Không tick dòng nào thì xuất **toàn bộ kết quả đang lọc**,
  không phải chỉ trang hiện tại.
- Bảng có **cột tick chọn** ở đầu (ô trên tiêu đề = chọn/bỏ chọn cả trang). Tick vài phiếu thì
  chỉ xuất bấy nhiêu — nút hiện luôn số đã chọn: *"Xuất Excel (3)"*. Đổi trang / lọc lại thì bỏ tick.
- Phạm vi dữ liệu vẫn do `apply_scope` quyết định: thấy được phiếu nào trên danh sách thì xuất
  được đúng bấy nhiêu, xuất file không mở rộng quyền.

**Mỗi dòng hàng là một dòng Excel.** Cụm đầu phiếu (mã, ngày tạo, người yêu cầu, bộ phận, ngày cần,
tổng tiền, gấp, trạng thái) **lặp lại** ở mọi dòng của cùng một phiếu, nên **không cộng thẳng cột
"Tổng tiền"** — lọc cột **"STT dòng" = 1** rồi mới cộng theo phiếu, hoặc cộng cột "Thành tiền" khi
cần cộng theo sản phẩm. Phiếu chưa có dòng hàng vẫn ra một hàng (cụm dòng để trống).

Khối cột dòng hàng **luôn có mặt** dù bảng đang ẩn: STT dòng · Mã SP · Tên SP · Phân loại · ĐVT ·
Số lượng · Đơn giá · %VAT · Thành tiền · Kho nhận · Ngày cần hàng (dòng) · Dự kiến có hàng ·
NSTM phụ trách · Trạng thái dòng · SL đã đặt · SL đã nhận · Ghi chú dòng.

**Quy ước file** (chung cho cả 4 màn có nút này): ô tiền/số lượng giữ **kiểu số** (không kèm chữ "đ")
để cộng · lọc · pivot ngay trong Excel; ô ngày là **kiểu ngày** thật; `Ngày tạo` quy về **giờ VN**;
dòng tiêu đề đóng băng và bật auto-filter; tên file `yeu-cau-mua-hang-DDMMYYYY.xlsx`.
Một lần xuất tối đa **5.000 dòng** — vượt thì hệ thống báo lỗi nhắc lọc bớt hoặc tự tick chọn phiếu.

**Ai được xuất.** Vai trò chuẩn có sẵn ô "Xuất" của YCMH: *Trưởng phòng · Quản lý công ty ·
NV thu mua · Admin thu mua · Quản lý thu mua · Quản trị hệ thống*. Vai trò **"Nhân sự"** (người
yêu cầu thường) **KHÔNG** được xuất — muốn cho ai đó xuất thì tạo một **vai trò riêng** chỉ tick ô
"Xuất" của màn tương ứng rồi gán thêm cho người đó (quyền là hợp của các vai trò được gán, nên
không phải sửa vai trò "Nhân sự"). Vai trò **tự tạo tay** cũng phải tick ô "Xuất" mới thấy nút.

## H. Phương án trên dòng hàng (bao-CR-310)

Cho phép **xử lý khảo sát ngay trên YCMH**: NSTM gắn phương án (NCC + giá) lên từng dòng hàng,
người yêu cầu chốt, rồi từ các dòng đã chốt sinh thẳng đơn mua hàng. Yêu cầu báo giá (YCBG)
**giữ nguyên không đụng tới** — đây là đường thứ hai, dùng khi phiếu đã đủ mã hàng và thông tin
mà chỉ vướng giá biến động.

Thay cho hướng gộp YCMH vào YCBG của cụm bao-CR-277..291 (đã khai tử).

### H.1 Bài toán

Người yêu cầu lập phiếu mua cái ly, đã có mã hàng, đã có giá. Thu mua tiếp nhận thì phát hiện
**giá vừa biến động** — có khi phải đổi sang NCC khác. Trước đây phải trả phiếu về hoặc mở
một YCBG mới. Nay thu mua gắn thêm vài phương án ngay trên dòng đó để người yêu cầu chốt lại.

### H.2 Ai làm gì

| Vai | Thao tác |
|-----|----------|
| NSTM (`pur_staff`) | **Gắn** phương án lên dòng được giao. Không chốt. |
| Người yêu cầu | **Chốt** phương án — vì chỉ họ biết mức giá đó còn đáng mua không. |
| Quản lý TM / Admin TM (có `purchase_request:approve`) | **Chốt được luôn** — đường tắt cho hàng gấp, khỏi chờ người yêu cầu. |

Điều kiện chốt: **là người yêu cầu (`created_by` hoặc `requester_id`) HOẶC có
`purchase_request:approve`**. Khóa `approve` chia đúng ranh giới sẵn có: `pur_manager` và
`pur_admin` có, `pur_staff` không có — không phải đẻ quyền mới.

### H.3 Quy tắc

1. Mỗi dòng gắn **tối đa 5 phương án** (`option_service.MAX_OPTIONS_PER_LINE`). *Phương án 0
   (H.10) đứng NGOÀI trần này.*
2. Hai nguồn phương án: **chọn từ kho khảo sát đã duyệt** (`line_approve = "Đã duyệt"`), hoặc
   **NSTM gõ tay**. Gõ tay dành cho trường hợp giá biến động liên tục, NSTM cần đưa ra một mức
   hợp lý cho người yêu cầu chốt — không phải để lách kho khảo sát.
3. Phương án là **bản chụp (snapshot)**: phiếu khảo sát gốc sửa giá về sau thì phương án đã gắn
   không đổi theo.
4. **Mỗi dòng chốt đúng 1 phương án.** Bấm lại chính nó = bỏ chốt (toggle, giống YCBG).
5. "Dòng này đã chốt chưa" **không lưu thành cột** — suy ra từ cờ `is_chosen`.
6. **Cổng thời điểm**: chỉ gắn/chốt khi phiếu ở `dispatched`, `processing`, `purchasing`,
   `purchased` — tức sau khi thu mua tiếp nhận, trước khi phiếu đóng.
7. **Hàng rào dòng**: NSTM chỉ gắn được vào dòng có `assignee` là mình. Dòng của người khác 403.
8. **Người yêu cầu không thấy tên NCC** — giữ đúng luật 2 cụm NCC (Task 4). Họ thấy
   *"Phương án 1 / 2 / 3"* kèm giá và thời gian giao, chốt theo giá chứ không theo NCC.
9. **Đồng bộ mã hàng khi chốt** *(bổ sung 14/09/2026 theo chốt của khách)*: dòng **chưa có mã
   hàng** (`product_code` rỗng) mà phương án chốt có `snap_internal_code` thì **chép mã đó lên
   dòng** — ngoại lệ DUY NHẤT phương án được ghi vào nhóm trường nhu cầu (xem H.4). Nhờ vậy dòng
   bắt đầu được đồng bộ tiến độ `qty_ordered`/`qty_received` (vốn nối theo chuỗi `product_code`
   — tức đóng luôn N-004 cho các dòng này). Bỏ chốt **không xóa mã** đã chép: mã đã thành dữ
   liệu của dòng. *Đã có trong mã từ 15/09/2026 (`option_service.choose_option`); mã trùng
   với dòng khác trên phiếu thì KHÔNG chép — giữ luật CR-047 mỗi mã một dòng.*

### H.4 Dòng hàng và phương án không ghi đè nhau

> Dòng hàng = **"tôi cần gì"**. Phương án = **"mua ở đâu, giá nào"**.

| Nhóm trường | Nguồn |
|---|---|
| Nhu cầu: mã hàng, tên hàng, số lượng, ĐVT, ngày cần, kho nhận | **Luôn** lấy từ dòng hàng. Phương án không đụng — trừ đúng một ngoại lệ H.3.9: dòng chưa có mã hàng thì lúc chốt chép `snap_internal_code` lên dòng. |
| Thương mại: NCC, đơn giá, VAT, thời gian giao, nơi giao, phí vận chuyển, MOQ | Lấy từ **phương án đã chốt**; chưa chốt thì dùng giá đề xuất trên dòng. |

**Chốt phương án KHÔNG ghi đè `price` / `vat_pct` của dòng hàng.** Ba lý do: giữ được dấu vết
*giá đề xuất → giá chốt* (chính là thứ cần nhất khi giá biến động); bỏ chốt không phải khôi phục
gì; báo cáo cũ không bị đổi ngược sau lưng. Bản in vì vậy có **hai cột song song**
`Giá đề xuất | Giá chốt | Chênh lệch`.

Ba chỗ va chạm cần xử riêng:

- **ĐVT lệch nhau** (dòng ghi "cái", NCC báo giá theo "thùng 100 cái"): **không tự quy đổi** —
  sai hệ số một lần là sai tiền cả đơn. Màn hình cảnh báo, bản in ghi cả hai đơn vị, NSTM tự quy
  giá về đúng ĐVT của dòng khi nhập tay.
- **MOQ lớn hơn SL cần** (cần 100, NCC bán tối thiểu 500): cảnh báo ngay trên thẻ phương án để
  người yêu cầu thấy **trước khi** chốt. Tạo ĐMH vẫn lấy SL của dòng.
- **Tên hàng lệch nhau**: bản in ưu tiên **tên nội bộ**; tên NCC gọi chỉ in nhỏ ở bản của thu mua.

### H.5 Từ phương án đã chốt ra đơn mua hàng

`PurchaseOrder` chỉ mang **một** `supplier_code`, nên **N nhà cung cấp = bắt buộc N đơn mua hàng**.

Nút *Tạo đơn mua hàng theo phương án* gom các dòng đã chốt **theo `supplier_code`** rồi sinh
**N đơn nháp** một lượt: đơn giá lấy `snap_price_by_volume`, VAT lấy `snap_vat` (trống thì rơi về
`vat_pct` của dòng — CR-058), cam kết giao hàng đưa vào ghi chú.

Cùng khuôn với `survey_request.create_prs` (gom option đã chọn theo NCC ra nhiều YCMH nháp) —
chỉ khác là áp xuống một tầng.

*Mở rộng 14/09/2026 (H.10.6): các dòng mà phương án chọn CHƯA có NCC gom thành **một đơn nháp
riêng không NCC** — không chặn sinh đơn.*

### H.6 Hai bản in

**Bản A — cho người yêu cầu.** **Không đẻ mẫu mới** — vẫn là bản in phiếu đề xuất ở mục F,
in toàn bộ dòng của phiếu, không tick chọn gì. Phương án chỉ **điền vào các ô sẵn có**:

| Ô trên bản in | Lấy từ đâu |
|---|---|
| Nhà cung cấp (khối `supplier_pur`, mục A.14) | **Chỉ in thứ nhập trên phiếu** (rà lại vòng 3): cụm `supplier_pur` do thu mua ghi, trống thì rơi về cụm `supplier_req` của người yêu cầu; cả hai đều trống thì ô tên in chữ mặc định *"Nhà cung cấp tối ưu nhất"*. KHÔNG tự đổ NCC theo phương án vào đây nữa. |
| Đơn giá / %VAT trên từng dòng | Phương án đã chốt của dòng đó; dòng chưa chốt thì giữ **giá đề xuất** (`price` / `vat_pct`). |
| Thành tiền, tổng cộng | Tính lại theo giá đang in. |

Nghĩa là người yêu cầu cầm về một tờ phiếu **quen thuộc y như cũ**, chỉ khác là số tiền và tên
NCC nay là con số đã chốt chứ không còn là ước lượng lúc lập phiếu.

**3 sản phẩm chốt 3 NCC khác nhau vẫn in CHUNG MỘT BẢNG**, không tách trang, không thêm cột NCC
theo dòng. Người yêu cầu vốn không thấy NCC, nên chuyện phiếu này mua ở mấy nơi là việc của thu
mua, không phải thứ cần đưa vào tờ trình của họ. Việc tách theo NCC chỉ xảy ra ở **bản B**.

Ô NCC chung **không dính gì tới phương án** (đính chính ở rà lại vòng 3 — bản đợt 4 từng tự đổ
NCC của phương án chiếm giá trị lớn nhất vào đây và bị khách bắt lỗi "đâu có nhập gì đâu mà ra
1 NCC"): mục này tên là *NCC DO BỘ PHẬN ĐỀ XUẤT* nên chỉ in thứ nhập trên phiếu; NCC theo
phương án xem ở **bản B**.

**Luật ẩn NCC vẫn áp** (H.3.8): người không có `supplier:read` thì ô NCC của cụm `pur` hiện
*"Phương án 2"* thay cho tên thật — đây là hành vi **đã có sẵn** của bản in hiện tại, không phải
luật mới. Riêng cụm `supplier_req` là do chính người yêu cầu gõ vào nên họ luôn thấy.

**Bản B — cho thu mua: CHÍNH TỜ PHIẾU ĐỀ XUẤT, TÁCH THEO NCC.** Không có bố cục riêng nào cả
(chốt ở rà lại vòng 4) — mỗi trang là **một tờ phiếu y mẫu 003/BM/PKT giống hệt bản A**, chỉ
khác đúng hai chỗ: bảng hàng chỉ còn dòng đã chốt phương án của NCC đó, và ô *NHÀ CUNG CẤP DO
BỘ PHẬN ĐỀ XUẤT* điền sẵn tên NCC đó. Mọi thứ còn lại — bảng phiên bản, tiêu đề, THÔNG TIN
CHUNG, MỤC ĐÍCH & NỘI DUNG, 9 cột bảng hàng, khối tổng ba dòng, PHẦN DÀNH CHO BỘ PHẬN MUA HÀNG,
cụm XÉT DUYỆT 4 ô, dòng chữ chân trang — là **cùng một component** với bản A.

Chọn NCC nào in bằng hàng ô tick ngay dưới thanh công cụ, mỗi NCC một ô:

```
[x] NCC A    3 dòng    12.400.000 đ
[x] NCC B    1 dòng     3.200.000 đ
[ ] NCC C    2 dòng     8.750.000 đ
```

Tick 2 NCC rồi bấm In → **1 file 2 trang**, mỗi trang một tờ phiếu hoàn chỉnh của một NCC.
Thanh công cụ có đủ hai nút gạt của bản A: *Có/Không chữ ký* và *Mẫu thường/Mẫu thuế*.

Mỗi trang chính là **bản nháp của một đơn mua hàng**: in ra ký trước, ký xong bấm *Tạo đơn
mua hàng* thì ra đúng N đơn khớp với N trang vừa ký. Và vì phương án đã chọn không đổi sau
khi lên đơn, bản in vẫn khớp các đơn ĐÃ tạo — nên tạo đơn xong **vẫn in lại được** (đây là
bản lưu/ký hồ sơ, không phải lệnh tạo đơn; xem rà lại vòng 2 bên dưới).

**Ghi chú thi công (P4, 15/09/2026).** Cả hai bản in không cần backend mới — chi tiết YCMH đã
nhúng `chosen_option` từng dòng (kèm luật che NCC). Phần tính nằm chung một tệp thuần
`frontend-v2/src/modules/procurement/utils/purchase-request-print-options.ts` (có test cạnh
tệp): bản A dùng `printLineValues` / `printedTotals` đắp vào trang in cũ (hàm
`dominantChosenSupplier` từng đổ NCC phương án vào ô NCC chung đã GỠ ở rà lại vòng 3); bản B là trang mới `/print/purchase-request-suppliers/:id`
(`purchase-request-supplier-print-page.tsx`) dùng `buildSupplierPrintPlan` — hàm này gom
theo NCC **cùng cách gom** với nút tạo đơn backend (`generate_orders`) nhưng chỉ bỏ qua
**hai** loại dòng: dòng hủy · dòng không chọn phương án. Dòng đã lên ĐMH (kể cả đơn nháp —
CR-074 rời `no_po` ngay lúc lập) **vẫn in** — bản in là bản lưu/ký, không phải lệnh tạo đơn;
bản đầu soi gương cả luật đó nên khách vừa tạo đơn xong là bản in ra 0 trang (sửa ở rà lại
vòng 2 bên dưới). Số dòng bị bỏ qua nói thành lời trên thanh công cụ, không in ra giấy. Ô tick NCC nằm ngay
dưới thanh công cụ của trang in (mặc định tick hết, nhóm *Chưa có NCC* cũng là một trang
tick được). Lưu ý H.4 về ĐVT đã áp cho cả hai bản: ĐVT báo giá lệch thì in kèm chú
*(báo giá: …)* — "lệch" so KHÔNG phân biệt hoa thường ("Cái" của báo giá và "cái" của dòng là
một đơn vị, rà lại vòng 2). Lưu ý còn lại của H.4 (tên NCC gọi mặt hàng in nhỏ dưới tên nội
bộ) **đã bỏ ở rà lại vòng 4** vì mẫu 003/BM/PKT không có ô cho nó.

**Rà lại theo góp ý khách (15/09/2026).** Ba chỉnh sau khi khách xem bản đầu:

1. **Bản B đổ lại theo đúng khuôn mẫu 003/BM/PKT** của phiếu đề xuất (bản đầu tự chế bố cục
   riêng, khách chê "không giống form in yêu cầu của mình"): bảng phiên bản góc phải, tiêu đề
   giữa *BẢNG HÀNG THEO NHÀ CUNG CẤP* + dòng *Kèm phiếu đề xuất số* + ngày kiểu văn thư,
   mục **NHÀ CUNG CẤP** theo thanh mục của khuôn, khối tổng ba dòng (Tổng cộng · Tiền VAT ·
   Tổng cộng thanh toán) và mục **XÉT DUYỆT** hai ô ký (*TP/BP mua hàng* · *Người lập* —
   bản nháp làm việc của thu mua nên không đổ chữ ký số; **cách rút gọn này bị khách chê tiếp
   ở vòng 3, đã đổi lại thành cụm 4 ô + chữ ký số y mẫu chung** — xem rà lại vòng 3 bên dưới).
   Ba mảnh khuôn
   (`DocumentVersionTable` / `PrintSection` / `PrintLine`) export từ trang bản A dùng lại,
   không chép mã.
   **Đính chính — cả mục 1 này đã HẾT HIỆU LỰC ở rà lại vòng 4**: bố cục *BẢNG HÀNG THEO NHÀ CUNG CẤP*
   bỏ hẳn, bản B nay in lại nguyên tờ phiếu đề xuất. Giữ đoạn này để thấy đường đi, đừng thi
   công theo.
2. **Nút vào dồn về header trang chi tiết** — thẻ chọn phương án không còn nút nào. Khách chê
   4 nút (2 tạo đơn + 2 in) là rối, gợi ý nút in sổ xuống: nay *In phiếu* là **dropdown 2 mục**
   (*Phiếu yêu cầu mua hàng* · *Bảng hàng theo nhà cung cấp* — mục sau vẫn cần `supplier:read`
   và có dòng đã chốt), *Tạo đơn mua hàng* cũng là **dropdown 2 mục** (*Lập tay* · *Theo
   phương án đã chọn — gom theo NCC*). Chỉ đủ điều kiện MỘT biến thể thì nút về dạng thường,
   không sổ (dropdown một mục là bắt bấm hai lần vô cớ).
3. **Nút gom hết lỗi 500** (mã sự cố 515E39D6): mã nhật ký cũ `options_generate_orders`
   22 ký tự, tràn cột `tab_audit_log.action` `VARCHAR(20)` → MySQL 1406. Đổi thành
   `options_gen_orders` (18 ký tự) + đăng nhãn ở `action_catalog.py`. Lưu ý: `create_po`
   commit theo TỪNG đơn nên lần bấm dính 500 vẫn đã tạo đủ đơn — lỗi chỉ nổ ở khâu ghi
   nhật ký sau đó; pytest SQLite không ép độ dài VARCHAR nên test cũ xanh giả, đã kiểm
   lại end-to-end trên MySQL thật.

**Rà lại vòng 2 (cũng 15/09/2026).** Khách thử tiếp bản sau rework và gửi ba góp ý nữa;
cả ba chỉ đụng frontend-v2, backend giữ nguyên:

1. **Ô ĐVT hết gãy dòng vì chú "(báo giá: …)" thừa**: dòng ĐVT `cái` chọn báo giá ĐVT
   `Cái` là in "cái (báo giá: Cái)" — hai chuỗi chỉ khác hoa thường mà bị coi là hai đơn
   vị. `printLineValues` nay so trim + không phân biệt hoa thường; đơn vị khác thật
   (m vs cuộn) vẫn in kèm chú vì giá là giá theo đơn vị báo giá (H.4).
2. **Bản B in ra "0 trang" sau khi tạo đơn**: bản đầu soi gương cả luật "bỏ dòng đã rời
   `no_po`" của nút gom, mà CR-074 rời `no_po` ngay khi lên đơn NHÁP — khách bấm tạo đơn
   xong quay lại in là trống trơn. Chốt lại ngữ nghĩa: **bản B là bản lưu/ký hồ sơ, không
   phải lệnh tạo đơn** — dòng đã lên ĐMH vẫn in (phương án chọn không đổi sau khi lên đơn
   nên trang in vẫn khớp đơn đã tạo); chặn tạo trùng là việc riêng của nút gom.
   `SupplierPrintPlan.skipped` chỉ còn `noChosen` + `cancelled`.
3. **Bấm gom lần hai ra toast đỏ 400 "Không còn dòng nào tạo được đơn..."** — không phải
   lỗi: đó là chốt chống tạo trùng của backend nói đúng sự thật (2 đơn nháp đã tạo ở lần
   bấm trước), nhưng toast đỏ đọc ra như hệ thống hỏng. Nay trang chi tiết tự ẩn mục gom
   khi không còn dòng đủ điều kiện (`hasLineToGenerate` soi gương đúng luật bỏ qua của
   `generate_orders`: chưa hủy · còn `no_po` · còn phương án đang chọn); đường *Lập tay*
   vẫn mở nên nút "Tạo đơn mua hàng" rơi về dạng thường không sổ xuống.

**Rà lại vòng 3 (cũng 15/09/2026).** Khách xem tiếp bản sau vòng 2 và gửi ba góp ý;
cả ba chỉ đụng frontend-v2:

1. **Ô NCC chung của bản A THÔI tự đổ NCC theo phương án** — khách hỏi đúng chỗ hở:
   *"NCC đâu có nhập gì đâu mà ra 1 NCC"*. Mục đó tên là *NCC DO BỘ PHẬN ĐỀ XUẤT* nên chỉ
   được in thứ nhập trên phiếu: `supplier_pur` trước, trống thì `supplier_req`, cả hai trống
   thì ô tên in chữ mặc định *"Nhà cung cấp tối ưu nhất"* (đúng hành vi trước đợt 4). Hàm
   `dominantChosenSupplier` gỡ hẳn khỏi `purchase-request-print-options.ts` (kèm 6 test).
   Giá / %VAT theo phương án trên từng dòng GIỮ NGUYÊN — chỉ ô NCC chung đổi.
2. **Gom xong nhảy thẳng sang danh sách ĐMH đã lọc theo phiếu**: `onSuccess` của nút gom
   (trang chi tiết YCMH) điều hướng tới `/procurement/purchase-orders?q=<mã YCMH>` — ô tìm
   kiếm nhanh của danh sách ĐMH vốn LIKE cả cột `pr_code` (backend `_list_query`) nên danh
   sách hiện đúng các đơn của phiếu, mã phiếu nằm sẵn trong ô tìm kiếm cho người dùng tự xóa.
   Toast "Đã tạo N đơn..." của hook vẫn nổ; không thêm param backend nào.
3. **Cụm XÉT DUYỆT của bản B đổ lại y mẫu chung**: bản 2 ô ký tay tự chế ở vòng 1 vẫn bị chê
   *"không theo mẫu chung"* — nay dùng lại nguyên `SignatureSection` (4 ô *Giám đốc ·
   TP/BP mua hàng · TP/BP đề xuất · Người lập* + chữ ký số) và `PrintToggle` *Có/Không chữ ký*
   export từ trang bản A; 3 class `pr-print-signature*` khai lại trong PRINT_STYLES cục bộ vì
   stylesheet hai trang không dùng chung. Nút *Mẫu thuế* KHÔNG thêm vào bản B — đó là biến thể
   thuế của tờ phiếu, không phải của bảng hàng theo NCC. Phần THÔNG TIN CHUNG / MỤC ĐÍCH cũng
   không lặp lại ở bản B vì là nội dung phiếu đã có ở bản A.
   **Đính chính — ba câu cuối của mục 3 này hết hiệu lực ở vòng 4**: bản B nay LÀ tờ phiếu, nên có đủ
   THÔNG TIN CHUNG / MỤC ĐÍCH và có cả nút *Mẫu thuế*; stylesheet cũng không còn khai lại
   class nào — hai trang nạp chung `PURCHASE_REQUEST_PRINT_STYLES`.

**Rà lại vòng 4 (cũng 15/09/2026) — BỎ HẲN BỐ CỤC RIÊNG CỦA BẢN B.** Khách xem bản sau vòng 3
và bác lần thứ ba: *"bỏ bản này, phải là bản phiếu yêu cầu, nhưng có điền thông tin NCC vào là
oke"*. Ba vòng trước đều là sửa vụn một bố cục tự chế, vòng nào cũng còn chỗ lệch mẫu chung.
Chốt lại: **đừng thiết kế biến thể của tờ phiếu, chỉ đổi DỮ LIỆU đổ vào tờ phiếu.**

1. **Tách `PurchaseRequestPrintSheet`** khỏi trang bản A — một tờ phiếu 003/BM/PKT nhận
   `items` (dòng nào in) + `supplier` (ô NCC in gì) + `taxMode` / `showSignature`. Bản A gọi
   nó một lần với cả phiếu; bản B gọi mỗi NCC một lần. `PurchaseRequestPrintItems` đổi sang
   nhận **danh sách dòng** thay vì cả phiếu, nên `printedTotals` tự cộng đúng phần đang in.
   `PRINT_STYLES` đổi tên thành `PURCHASE_REQUEST_PRINT_STYLES` và export — bản B nạp nguyên
   tệp CSS đó, thôi khai lại class nào.
2. **Ô NCC của bản B điền theo phương án** (khách duyệt rõ chỗ này, ngược với mục 1 của vòng
   3 vốn chỉ nói về bản A): tên lấy từ NCC của nhóm. Mã số thuế / liên hệ **chỉ điền khi tên
   trùng** một trong hai cụm NCC nhập trên phiếu (`supplier_pur` → `supplier_req`) — phương án
   khảo sát chỉ chụp mã + tên NCC, không chụp MST; đoán bừa là in sai hồ sơ ký tay. Nhóm *Chưa
   có NCC* để tên rỗng nên tờ đó in chữ mặc định *"Nhà cung cấp tối ưu nhất"* y bản A.
3. **Ba thứ của bố cục cũ KHÔNG chuyển sang** vì mẫu 003/BM/PKT không có ô: *Mã NCC*, *Thời
   gian giao* và *Nơi giao* **theo cam kết NCC**, *tên NCC gọi mặt hàng*. Lưu ý cột *Nơi giao*
   trên bảng hàng của mẫu chung là **kho nhận** của dòng, không phải nơi NCC cam kết giao —
   hai khái niệm khác nhau, đừng dồn vào một cột. Cần in mấy thứ đó thì phải sửa mẫu chung,
   không lách bằng một bản in riêng. `SupplierPrintLine` gỡ theo 4 trường đã chết
   (`quoteUnit` · `supplierProductName` · `deliveryTime` · `deliveryPlace`), chỉ còn `item` +
   phần tính tiền để cộng tổng cho ô tick.
4. **Xếp nhiều tờ trong một trang in** cần thêm đúng một stylesheet nhỏ (`MULTI_SHEET_STYLES`):
   chừa khoảng cách giữa các tờ trên màn hình · mỗi tờ ăn trọn một trang giấy, tờ cuối không
   đẻ trang trắng · **dòng chữ chân trang trả về `position: absolute`** — bản A để `fixed` khi
   in (đúng cho một tờ), nhiều tờ thì trình duyệt lặp nó lên MỌI trang và chồng N dòng lên nhau.
5. **Nhãn đổi theo**: mục dropdown *In phiếu* nay là *Phiếu yêu cầu tách theo nhà cung cấp*
   (cũ: *Bảng hàng theo nhà cung cấp*), tiêu đề tab trình duyệt là
   `<mã phiếu> - Phiếu đề xuất theo nhà cung cấp`.

`tab_purchase_request_item_option` (migration `6835fb9cfecd`) — 29 cột, khóa về
`tab_purchase_request_item.id`. Cụm `snap_*` là bản chụp từ dòng khảo sát; `supplier_code` /
`supplier_name` / `snap_internal_code` chịu hàng rào 2 cụm NCC như `supplier_pur` (cần
`supplier:read` để xem, `supplier:write` để sửa).

### H.8 Các đợt làm

| Đợt | Nội dung | Tình trạng |
|-----|----------|-----------|
| P1 | Bảng dữ liệu + service + 6 endpoint (gắn từ khảo sát · gắn tay · sửa · gỡ · chốt · liệt kê) + test | **Xong — đã commit**; bảng `tab_purchase_request_item_option` (migration `6835fb9cfecd`) đã có trên **cả dev lẫn prod** (theo lượt gộp 11/09) |
| P2 | **MỞ RỘNG 14/09 — xem H.10**: nền phương án 0 + nới khóa sau chốt + áp 1 NCC cho nhiều dòng, rồi gom theo NCC → sinh N đơn nháp + 1 đơn riêng không NCC + **đồng bộ mã hàng H.3.9** | **Xong — nằm trong commit `60d3f4ad`, đã push + deploy dev 15/09** |
| P3 | Màn *Xử lý phương án* ở `frontend-v2` (`/procurement/purchase-requests/:id/process`) + **P3b**: chốt hoàn thành xử lý + thẻ chọn phương án ở màn chi tiết | **Xong — commit `60d3f4ad`, đã push + deploy dev 15/09** |
| P4 | Hai bản in ở H.6 + gác N-17 + cập nhật HDSD | **Xong local 15/09** — bản A đắp giá phương án vào trang in cũ; bản B trang mới `/print/purchase-request-suppliers/:id` (util chung `purchase-request-print-options.ts` + test); **rà lại 4 vòng cùng ngày theo góp ý khách** (vòng 1: bản B theo khuôn 003/BM/PKT · gom nút về 2 dropdown · vá 500 nút gom; vòng 2: ĐVT hết chú thừa · bản B in được sau khi tạo đơn · ẩn mục gom hết dòng; vòng 3: ô NCC chung chỉ in thứ nhập trên phiếu · gom xong nhảy sang danh sách ĐMH lọc theo phiếu · cụm XÉT DUYỆT bản B y mẫu chung; vòng 4: **bỏ hẳn bố cục riêng của bản B** — mỗi trang là chính tờ phiếu đề xuất, lọc dòng theo NCC và điền tên NCC vào ô NCC — xem cuối H.6); HDSD chờ nhịp deploy (bài viết nằm trong DB) |

Thứ tự làm tiếp đã chốt: **P3 trước P2** (màn *Xử lý phương án* là chỗ nghiệm thu bằng mắt,
có nó rồi mới thấy dữ liệu để bấm sinh đơn), rồi P4 sau cùng vì bản B phụ thuộc N-17.
P3 + P3b đã xong; bên trong P2 đi theo thứ tự H.10.8.

### H.9 Còn nợ

- **N-17 — ĐÃ ĐÓNG 15/09/2026 (P4)**: quyền `print` của `purchase_request` backend không kiểm
  ở đâu cả — ai mở được chi tiết phiếu (`read`) là in được. Cách đóng gồm hai lớp:
  - **Lớp dữ liệu (đã có sẵn từ P1, có test)**: serializer `_out` của chi tiết YCMH che sạch
    NCC khi thiếu `supplier:read` — cụm `supplier_pur` rỗng, `suggested_supplier*` rỗng, và 4
    trường NCC trên từng phương án (`supplier_code` / `supplier_name` / `supplier_survey_id` /
    `snap_internal_code`) trả chuỗi rỗng (`test_ycmh_phuong_an_cr310.py`). Nghĩa là kể cả ai
    đó gõ thẳng URL bản in, dữ liệu NCC cũng không có mà lộ.
  - **Lớp giao diện (P4)**: trang bản B tự chặn cả trang khi thiếu `supplier:read` (ErrorState
    nói rõ cần quyền gì), và mục *Phiếu yêu cầu tách theo nhà cung cấp* trong dropdown **In phiếu** ở
    header trang chi tiết chỉ hiện khi có quyền (rà lại 15/09 — nút vào cũ trên thẻ chọn
    phương án đã bỏ). Bản A không cần gác — nó vốn không in tên NCC ngoài ô đề xuất cũ.

### H.10 Mở rộng đợt 2 — "Phương án 0" (chốt thiết kế 14/09/2026; cả ba chặng (a)(b)(c) xong, commit `60d3f4ad` đã push + deploy dev 15/09)

Câu hỏi gốc của khách: *người yêu cầu không chọn phương án, hoặc khảo sát không ra NCC, thì có
mua hàng được không?* Thay vì chặn hoặc đẻ thêm luật ngoại lệ, chốt hướng: **mọi dòng luôn có
ít nhất một phương án** — chính dòng yêu cầu tự làm phương án cho nó.

#### H.10.1 Phương án 0 là gì

Hệ thống **tự sinh** cho mọi dòng khi phiếu được điều phối (phiếu đang chạy dở thì sinh bù),
ruột chụp từ chính dòng yêu cầu: tên hàng, quy cách, ĐVT, giá đề xuất của người yêu cầu —
**chưa có NCC**. Bản chất kỹ thuật: một **phương án nhập tay do hệ thống tạo** (nguồn hiển thị
*"Yêu cầu gốc"*), sửa được như phương án nhập tay, nhưng **không xóa được** và **không chiếm
chỗ trong trần 5** của H.3.1 — mỗi dòng tối đa 5 phương án NSTM gắn + phương án 0 đứng ngoài.

#### H.10.2 Chọn sẵn

Phương án 0 được **tick chọn từ đầu** (chỉ khi dòng chưa chọn gì khác). Người yêu cầu im lặng
= mua theo đúng yêu cầu gốc. Chọn phương án khảo sát thì phương án 0 tự bỏ chọn — luật
một-dòng-một-phương-án H.3.4 giữ nguyên.

#### H.10.3 Chốt rỗng đổi nghĩa

"Chốt rỗng" nay = **không có phương án NSTM nào** (phương án 0 không tính) — trở thành lời
khai *"khảo sát không ra NCC"* thuần túy. Dòng chốt rỗng **vẫn chọn được phương án 0** → vẫn
mua được, thu mua tự tìm NCC ở nhịp sau.

#### H.10.4 Nới khóa sau chốt — đúng một khe

Luật P3b khóa dòng sau khi NSTM *chốt hoàn thành xử lý*; nhưng màn chọn chỉ hiện dòng đã
chốt, mà khách muốn chỉnh ngay trên đó, nên nới: sau chốt vẫn **sửa được GIÁ của mọi phương
án** và **điền/sửa NCC trên phương án 0 + phương án nhập tay** (người có
`purchase_request:write` + `supplier:read`). **Gắn thêm / gỡ phương án vẫn khóa** — muốn thì
bấm *Mở lại cho NSTM xử lý*. Phương án từ khảo sát **không đổi NCC được** — đổi NCC nghĩa là
một phương án khác, không phải sửa phương án cũ.

#### H.10.5 Màn chọn hai tầng người dùng

Người yêu cầu: bấm chọn thẻ như P3b, không thấy NCC (H.3.8 giữ nguyên). Thu mua
(`purchase_request:write` + `supplier:read`): thấy thêm nút sửa giá/NCC trên từng thẻ + khu
**"Áp 1 NCC cho nhiều dòng"** ngay trên màn chọn — tick các dòng đang thiếu NCC → chọn một
NCC → áp một phát, sửa giá kèm nếu cần.

#### H.10.6 Sinh đơn — bổ sung cho H.5

Gom dòng đã chọn theo NCC → N đơn nháp (H.5 giữ nguyên); **các dòng mà phương án chọn CHƯA có
NCC gom thành MỘT đơn nháp riêng không NCC** — không chặn sinh đơn, thu mua vào đơn điền NCC
sau; cổng gửi duyệt ĐMH sẵn có (CR-095, `REQUIRED_LINE_FIELDS`) chặn tới khi điền đủ. Kèm
H.3.9 chép mã hàng lúc chọn. **Đường tạo ĐMH tay giữ nguyên, luôn hoạt động** — và được nâng
cấp tự điền NCC/giá/mã từ phương án đã chọn của dòng.

#### H.10.7 Chọn thay

Admin / Quản lý thu mua (`purchase_request:approve`) chọn giúp người yêu cầu — đã có sẵn từ
P3b, không phải làm gì thêm.

#### H.10.8 Thứ tự thi công

(a) backend phương án 0 + nới khóa H.10.4 + endpoint áp NCC hàng loạt → (b) màn chọn nâng cấp
H.10.5 → (c) sinh đơn H.10.6. Xong (c) là hết đợt 2; hai bản in vẫn nằm ở đợt 4.
**Cả ba chặng đã xong local 15/09.** (b) nằm trọn trong
`purchase-request-choose-card.tsx`: hộp sửa giá/NCC trên từng thẻ (đường
`PATCH .../supplier` khi có NCC, PATCH giá thường khi không), khu "Áp 1 NCC cho nhiều
dòng" (chỉ nhận dòng mình phụ trách đang chọn phương án thiếu NCC, không phải khảo
sát), và dòng chốt rỗng hiện thẻ Phương án 0 chọn được thay vì tắt hẳn lưới.

(c) gồm hai đường:

- **Nút gom** — `POST /{pid}/options/generate-orders`
  (`option_service.generate_purchase_orders`): gom dòng đã chọn phương án theo NCC (mã, hoặc
  tên với NCC gõ tay ngoài danh mục), mỗi nhóm một đơn NHÁP đi qua đúng
  `purchase_order.service.create_po` để hưởng trọn tác dụng phụ của đường tạo tay (sinh mã
  `PO{id:05d}`, NSPT mặc định, chép ngày dự kiến, `_sync_pr` CR-074, `recompute_effects`,
  nhật ký); nhóm không NCC đứng CUỐI thành một đơn riêng, ghi chú đơn nhắc bổ sung NCC trước
  khi gửi duyệt. Giá dòng = `snap_price_by_volume`, VAT = `snap_vat` (trống rơi về `vat_pct`
  của dòng, CR-058), ĐVT = ĐVT báo giá nếu có, cam kết giao/nơi giao chép vào ghi chú dòng.
  **Chống sinh trùng bằng `line_status`**: dòng đã nằm trên một ĐMH (kể cả nháp — CR-074 đã
  lật `not_ordered`) bị bỏ qua, hết dòng thì 400 — và cố ý KHÔNG bỏ chọn phương án, vì phương
  án đã chọn là quyết định của người yêu cầu (khác YCBG). Dòng bị người yêu cầu bỏ chọn hết
  (kể cả phương án 0) = "khoan mua dòng này" — bỏ qua, đếm vào `skipped.no_chosen`. Cổng:
  `purchase_order:create` (nút này LẬP ĐƠN) + phạm vi đọc `purchase_request` (`_in_scope`,
  ngoài phạm vi 404) + giai đoạn mở. Nút đặt trên thẻ chọn phương án của màn chi tiết, có hộp
  xác nhận, toast kể tên các đơn vừa sinh.
- **Đường tạo ĐMH tay nâng cấp** (`utils/purchase-order-draft.ts`): dòng đã chọn phương án
  thì `buildPurchaseOrderLines` điền sẵn giá/VAT/ĐVT + cam kết giao theo phương án đó;
  `toDraftFromRequest` điền NCC lên đầu đơn khi **mọi dòng còn mua đều chọn phương án cùng
  MỘT NCC** (lệch một dòng là để trống như cũ). Phương án 0 chụp đúng giá trị dòng nên phiếu
  chưa ai đụng phương án cho kết quả y như trước.
