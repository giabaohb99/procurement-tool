# TỪ ĐIỂN DỮ LIỆU — CỤM CHỨNG TỪ THU MUA

Bản 1.0 — 28/08/2026. Nguồn sự thật là model.py; tệp này chép Ý NGHĨA, không thay mã.

---

## Mục lục

1. `tab_survey_request` — Yêu cầu báo giá (YCBG / YCKS)
2. `tab_survey_request_line` — Dòng yêu cầu báo giá
3. `tab_survey_request_option` — Phương án khảo sát (Option)
4. `tab_survey_request_pr` — Liên kết YCBG → YCMH
5. `tab_survey` — Phiếu khảo sát
6. `tab_survey_supplier_line` — Dòng NCC trong phiếu khảo sát
7. `tab_survey_product_line` — Dòng sản phẩm trong phiếu khảo sát
8. `tab_purchase_request` — Yêu cầu mua hàng (YCMH / PYC)
9. `tab_purchase_request_item` — Dòng hàng của YCMH
10. `tab_purchase_order` — Đơn mua hàng (ĐMH / PO)
11. `tab_po_item` — Dòng hàng của ĐMH
12. `tab_po_delivery` — Lần giao hàng
13. `tab_goods_receipt` — Phiếu nhập kho (sinh ngầm)
14. `tab_purchase_history` — Lịch sử mua hàng (snapshot)

---

## `tab_survey_request` — Yêu cầu báo giá

Phiếu do bộ phận yêu cầu lập để nhờ phòng thu mua khảo sát sản phẩm/nhà cung cấp. Sau khi khảo sát xong, người yêu cầu chọn phương án và hệ thống sinh Yêu cầu mua hàng (PYC). Mã nguồn: `backend/app/modules/survey_request/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính (AuditMixin) |
| `created_at` | datetime | Thời điểm tạo (AuditMixin) |
| `updated_at` | datetime | Thời điểm cập nhật lần cuối (AuditMixin) |
| `created_by` | int | ID tài khoản tạo (AuditMixin) |
| `updated_by` | int | ID tài khoản cập nhật lần cuối (AuditMixin) |
| `code` | str(50) | Mã phiếu duy nhất, định dạng `YCBGDDMMYYnn` |
| `company_id` | int | ID pháp nhân nhận hóa đơn |
| `requester` | str(255) | Tên người yêu cầu (bản chụp) |
| `requester_id` | int | ID nhân sự người yêu cầu — dùng để kiểm phạm vi xem |
| `requester_position` | str(100) | Chức vụ người yêu cầu (bản chụp) |
| `department_id` | int | ID phòng ban (nguồn sự thật; CR-086) |
| `department` | str(255) | Bản chụp tên phòng ban tại thời điểm lập phiếu — sẽ xóa (N-008) |
| `head_of_dept_id` | int | ID nhân sự trưởng bộ phận (CR-087) |
| `head_of_dept` | str(255) | Bản chụp tên trưởng bộ phận — sẽ xóa (N-008) |
| `purpose` | str(255) | Mục đích yêu cầu khảo sát |
| `request_date` | str(10) | Ngày lập phiếu (YYYY-MM-DD) |
| `status` | str(30) | Trạng thái phiếu: `draft` / `submitted` / `approved` / `rejected` / `processing` / `survey_done` / `pr_created` / `done` / `cancelled` |
| `note` | text | Ghi chú chung |
| `reject_reason` | text | Lý do từ chối hoặc hủy (ghi khi `status` = `rejected` / `cancelled`) |

**Logic chính:**

- Vòng đời trạng thái: `draft` → `submitted` → `approved` → `processing` → `survey_done` → `pr_created` → `done`. Trả lại: `approved` → `rejected` (khóa cứng, phải nhân bản). Hủy: bất kỳ thời điểm nào → `cancelled`.
- Chỉ sửa được khi `status` là `draft` hoặc `rejected`; phiếu `rejected` đã khóa nên thực tế phải dùng chức năng Nhân bản.
- Sau khi duyệt (`approved`), hệ thống tự gán NSTM cho từng dòng theo phân loại (`auto_assign`).
- Khi NSTM chốt xong mọi dòng (có phương án hoặc chốt rỗng) → phiếu tự lên `survey_done`.
- Khi tạo YCMH từ option đã chọn, phiếu nâng từ `survey_done` → `pr_created`; hoàn thành thủ công hoặc tự động (khi mọi YCMH liên quan đã `completed`) → `done`.
- Xóa chỉ được khi `status` thuộc `draft`, `rejected`, `cancelled`.
- `department_id` là nguồn sự thật cho phân quyền và lọc; cột `department` chỉ để in.

---

## `tab_survey_request_line` — Dòng yêu cầu báo giá

Mỗi dòng đại diện cho một sản phẩm hoặc nhóm hàng cần khảo sát trong phiếu YCBG. Mã nguồn: `backend/app/modules/survey_request/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `survey_request_id` | int | FK → `tab_survey_request.id` |
| `internal_line_code` | str(50) | Mã dòng nội bộ tự sinh (`YCBGLnnnnnn`) — không hiện với người yêu cầu |
| `received_date` | str(10) | Ngày NSTM tiếp nhận dòng (tự ghi khi được gán) |
| `result_due_date` | str(10) | Hạn trả kết quả khảo sát |
| `result_date` | str(10) | Ngày NSTM thực tế trả kết quả (ghi một lần; CR-075) |
| `department_requester` | str(255) | Bộ phận / người yêu cầu theo dòng |
| `item_group` | str(100) | Phân loại sản phẩm (dùng để ghép phương án và phân NSTM) |
| `requirement_detail` | text | Thông số kỹ thuật và yêu cầu chất lượng |
| `other_requirement` | text | Yêu cầu khác |
| `request_qty` | decimal(18,3) | Số lượng dự kiến mua |
| `uom` | str(25) | Đơn vị tính |
| `proposed_price` | decimal(18,4) | Giá đề xuất (VNĐ, chưa VAT; 4 số lẻ) |
| `image_file` | str(500) | Đường dẫn/tên file hình ảnh đính kèm |
| `assignee` | str(100) | Mã nhân viên NSTM phụ trách dòng này |
| `pr_id` | int | ID YCMH gần nhất được tạo từ dòng này (tham khảo, không phải FK đầy đủ) |
| `pr_code` | str(50) | Mã YCMH gần nhất |
| `is_completed` | bool | Cờ "đã từng tạo YCMH ít nhất một lần" (không khoá tạo thêm) |
| `line_status` | str(30) | Trạng thái do người yêu cầu cập nhật: rỗng / `resurvey` / `completed` |
| `no_option` | bool | Chốt rỗng: khảo sát xong nhưng không có phương án phù hợp |

**Logic chính:**

- `line_status` và `is_completed` được đồng bộ: `is_completed = (line_status == "completed")`.
- Chỉ được chốt `completed` khi có ít nhất một option đã được chọn (`is_chosen = True`).
- Khi đặt `resurvey`: tự bỏ chọn mọi option của dòng; nếu phiếu đang `survey_done` thì hạ về `processing`.
- Khi NSTM chọn "chốt rỗng", `no_option = True` và `result_date` được ghi lần đầu.
- `result_date` ghi một lần duy nhất (CR-075): khảo sát lại không được ghi đè để giữ dấu trễ hạn.
- Khi nhân bản phiếu, chỉ copy các dòng người dùng được phép xem (theo phạm vi phân quyền).

---

## `tab_survey_request_option` — Phương án khảo sát

Bảng trung tâm cơ chế ẩn NCC: mỗi option là một kết quả khảo sát sản phẩm đã duyệt, được snapshot hoàn chỉnh để người yêu cầu so sánh mà không biết tên nhà cung cấp. Mã nguồn: `backend/app/modules/survey_request/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `survey_request_line_id` | int | FK → `tab_survey_request_line.id` |
| `product_survey_line_id` | int | ID nguồn `tab_survey_product_line` (0 nếu nhập tay) |
| `public_id` | int | Số thứ tự ẩn danh trong 1 dòng (Option 1, 2, ...) |
| `display_label` | str(50) | Nhãn hiển thị: `"Option N — ID NNN"` |
| `is_chosen` | bool | Người yêu cầu đã chọn phương án này |
| `chosen_by` | int | ID tài khoản đã chọn |
| `system_product_code` | str(50) | Mã sản phẩm hệ thống (`tab_product.code`) — NSTM gắn để tạo dòng YCMH |
| `snap_product_name` | str(255) | Snapshot tên sản phẩm |
| `snap_spec` | text | Snapshot thông số kỹ thuật |
| `snap_origin` | str(100) | Snapshot xuất xứ |
| `snap_quote_unit` | str(25) | Snapshot đơn vị báo giá |
| `snap_moq` | decimal(18,3) | Snapshot số lượng tối thiểu |
| `snap_price_by_volume` | decimal(18,4) | Snapshot đơn giá (4 số lẻ) |
| `snap_volume_range` | str(100) | Snapshot khoảng sản lượng |
| `snap_vat` | decimal(5,2) | Snapshot % VAT |
| `snap_delivery_time` | str(100) | Snapshot thời gian giao hàng |
| `snap_delivery_place` | str(255) | Snapshot địa điểm giao hàng |
| `snap_shipping_cost` | decimal(18,2) | Snapshot phí vận chuyển |
| `snap_sample_ready` | bool | Snapshot cờ có mẫu sẵn |
| `snap_lab_result` | str(20) | Snapshot kết quả kiểm nghiệm |
| `snap_internal_code` | str(50) | Snapshot mã sản phẩm theo NCC (nội bộ NSTM, backend lọc) |
| `supplier_code` | str(50) | Mã NCC (nội bộ NSTM, backend lọc) |
| `supplier_name` | str(255) | Tên NCC (nội bộ NSTM, backend lọc) |
| `supplier_survey_id` | int | ID phiếu khảo sát nguồn (nội bộ NSTM, backend lọc) |
| `nstm_note` | text | Ghi chú của NSTM (CR-147: hiện cho người yêu cầu xem) |

**Logic chính:**

- Khi gắn option: chỉ nhận dòng khảo sát SP có `line_approve = "Đã duyệt"`; tối đa 5 option/dòng.
- Snapshot được chép tại thời điểm gắn từ `SurveyProductLine` — không thay đổi khi dữ liệu gốc thay đổi sau đó.
- Các cột `supplier_*`, `snap_internal_code` bị lọc ở tầng API trước khi trả cho người yêu cầu.
- Toggle chọn: bấm lại option đang chọn thì bỏ chọn; chọn option mới thì tự gỡ cờ `resurvey` của dòng.
- Nếu nguồn `tab_survey_product_line` bị xóa → vẫn giữ snapshot (đã đầy đủ tự đứng).
- Nếu nguồn còn tồn tại nhưng bị `line_approve = "Không duyệt"` → ẩn option; bị hủy cứng bằng `_purge_yc_options`.

---

## `tab_survey_request_pr` — Liên kết YCBG → YCMH

Bảng ghi nhận mỗi lần tạo YCMH từ một option của một dòng YCBG. Một dòng YCBG có thể dẫn đến nhiều YCMH (mua lại nhiều lần). Mã nguồn: `backend/app/modules/survey_request/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `survey_request_id` | int | FK → `tab_survey_request.id` |
| `survey_request_line_id` | int | FK → `tab_survey_request_line.id` |
| `option_id` | int | FK → `tab_survey_request_option.id` |
| `product_survey_line_id` | int | ID `tab_survey_product_line` nguồn (để thống kê toàn hệ) |
| `pr_id` | int | FK → `tab_purchase_request.id` |
| `pr_code` | str(50) | Mã YCMH (denormalize để truy vấn nhanh) |

**Logic chính:**

- Ghi một bản mỗi lần bấm "Tạo YCMH"; không xóa khi YCMH bị hủy (giữ lịch sử liên kết).
- Hệ thống dùng bảng này để xác định khi nào phiếu YCBG có thể tự chuyển `done` (khi tất cả YCMH liên kết đều `completed`).
- Mỗi option sau khi tạo YCMH sẽ bị tự bỏ chọn (`is_chosen = False`) để không tạo trùng lần sau.

---

## `tab_survey` — Phiếu khảo sát

Header phiếu khảo sát dùng chung cho hai loại: khảo sát NCC (`supplier`) và khảo sát sản phẩm (`product`). Thực tế hệ thống tạo với `survey_type = "combined"` (gộp cả hai sheet). Mã nguồn: `backend/app/modules/survey/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `code` | str(50) | Mã phiếu duy nhất (tự sinh `KSnnnnn` nếu trống) |
| `survey_type` | str(10) | Loại phiếu: `supplier` / `product` / `combined` |
| `pr_code` | str(50) | Mã PYC liên kết (trường cũ, giữ tương thích) |
| `survey_request_id` | int | ID YCBG liên kết |
| `sr_code` | str(50) | Mã YCBG liên kết (denormalize) |
| `received_date` | str(10) | Ngày tiếp nhận yêu cầu khảo sát |
| `result_due_date` | str(10) | Hạn trả kết quả |
| `item_group` | str(100) | Phân loại sản phẩm cần khảo sát |
| `main_content` | str(500) | Nội dung chính (clone từ mục đích YCBG) |
| `requirement_detail` | text | Yêu cầu kỹ thuật và chất lượng |
| `request_qty` | decimal(18,3) | Số lượng dự kiến mua |
| `market_price` | decimal(18,2) | Giá thị trường tham khảo (deprecated, không dùng) |
| `nspt` | str(100) | Mã NSTM phụ trách = người tạo phiếu |
| `has_product_code` | bool | Cờ sản phẩm đã có mã trong hệ thống |
| `item_code` | str(50) | Mã VTBB/VL nội bộ (khi `has_product_code = True`) |
| `item_name` | str(255) | Tên VTBB (tự điền theo mã) |
| `uom` | str(25) | Đơn vị tính |
| `proposed_rate` | decimal(18,4) | Giá đề xuất (4 số lẻ) |
| `approve_status` | str(20) | Quyết định duyệt: `pending` / `approved` / `rejected` (B-04) — nhớ QUYẾT ĐỊNH, không thay đổi khi phiếu bị hủy sau đó |
| `approve_note` | text | Ghi chú khi duyệt/từ chối |
| `status` | str(30) | Trạng thái hiện tại phiếu: `draft` / `submitted` / `approved` / `rejected` / `cancelled` |
| `import_key` | str(160) | Khóa idempotent khi nhập từ file (phân loại::NCC) |

**Logic chính:**

- Vòng đời `status`: `draft` → `submitted` → `approved` / `rejected`; từ bất kỳ → `cancelled`.
- Chỉ sửa được khi `status` là `draft` hoặc `rejected`.
- `approve_status` chỉ thay đổi tại hai sự kiện `approved` và `rejected`; phiếu bị hủy sau khi duyệt vẫn giữ `approve_status = "approved"` — hai cột phản ánh hai khía cạnh khác nhau.
- Khi phiếu bị hủy hoặc dòng SP bị "Không duyệt": gỡ mọi option YCBG đang tham chiếu các dòng SP đó (`_purge_yc_options`).
- Duyệt từng dòng (`line_approve`) độc lập với duyệt cả phiếu (`status`).
- Khi nhân bản: không copy liên kết YCBG/PYC — bản sao là phiếu độc lập.

---

## `tab_survey_supplier_line` — Dòng NCC trong phiếu khảo sát

Mỗi dòng là thông tin một nhà cung cấp được liên hệ trong đợt khảo sát (Sheet NCC). Mã nguồn: `backend/app/modules/survey/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `survey_id` | int | FK → `tab_survey.id` |
| `contact_date` | str(10) | Ngày liên hệ NCC |
| `reply_date` | str(10) | Ngày dự kiến phản hồi |
| `result_date` | str(10) | Ngày dự kiến trả kết quả |
| `supplier_code` | str(50) | Mã NCC trong hệ thống |
| `supplier_name` | str(255) | Tên NCC |
| `tax_code` | str(25) | Mã số thuế NCC |
| `reg_address` | text | Địa chỉ đăng ký kinh doanh |
| `warehouse_address` | text | Địa chỉ kho hàng |
| `google_maps` | str(500) | Link Google Maps |
| `contact_person` | str(100) | Người liên hệ |
| `contact_phone` | str(30) | Số điện thoại liên hệ |
| `supply_group` | str(255) | Nhóm hàng cung cấp |
| `quote_folder` | str(500) | Đường dẫn thư mục báo giá |
| `source_of_information` | str(255) | Nguồn thông tin đầu vào |
| `production_tech` | str(255) | Công nghệ sản xuất |
| `production_time` | str(100) | Thời gian sản xuất |
| `nvkd_eval` | str(100) | Đánh giá nhân viên kinh doanh NCC |
| `invoice_policy` | str(255) | Chính sách xuất hóa đơn |
| `reliability` | str(255) | Độ tin cậy |
| `delivery_policy` | str(255) | Chính sách giao hàng |
| `debt_policy` | str(50) | Chính sách công nợ |
| `defect_return` | str(255) | Chính sách đổi trả hàng lỗi |
| `nspt_note` | str(255) | Nhận xét của NSTM |
| `nspt_reason` | text | Lý do / chi tiết đánh giá NSTM |
| `line_approve` | str(255) | Trạng thái duyệt dòng NCC (ngoại lệ — dùng chuỗi, không phải mã cố định) |
| `line_approve_note` | text | Ghi chú duyệt dòng |
| `note` | text | Ghi chú nội bộ (không hiện ở YCBG) |
| `import_line_key` | str(200) | Khóa idempotent khi nhập từ file (mã yêu cầu + MST) |

**Logic chính:**

- Dòng được duyệt từng cái, độc lập với header phiếu: `line_approve` ghi nhận quyết định (không phải mã cố định theo quy tắc R2 — đây là ngoại lệ được giữ lại).
- Dòng đang `"Thiếu thông tin"` được phép bổ sung bất kể phiếu đang `submitted` hay `approved`; sau khi bổ sung tự về `"Chờ duyệt"`.
- Xóa/tạo lại toàn bộ dòng khi lưu (không upsert), nên id dòng thay đổi mỗi lần save.
- Khi nhân bản phiếu khảo sát: copy dòng NCC nhưng không copy `line_approve` và `line_approve_note` — bắt đầu lại từ trạng thái chờ duyệt.

---

## `tab_survey_product_line` — Dòng sản phẩm trong phiếu khảo sát

Mỗi dòng là kết quả khảo sát một sản phẩm từ một nhà cung cấp (Sheet SP). Sau khi được duyệt, dòng này trở thành nguồn để NSTM tạo option cho dòng YCBG. Mã nguồn: `backend/app/modules/survey/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `survey_id` | int | FK → `tab_survey.id` |
| `contact_date` | str(10) | Ngày liên hệ NCC |
| `reply_date` | str(10) | Ngày dự kiến phản hồi |
| `result_date` | str(10) | Ngày trả kết quả |
| `supplier_code` | str(50) | Mã NCC |
| `internal_code` | str(50) | Mã sản phẩm theo NCC (nhập tay khi khảo sát) |
| `product_name` | str(255) | Tên sản phẩm |
| `invoice_name` | str(255) | Tên ghi trên hóa đơn NCC xuất (CR-111 — khảo sát phải chốt sẵn) |
| `spec` | text | Thông số kỹ thuật |
| `active_ingredient` | str(255) | Hàm lượng hoạt chất (chủ yếu cho nguyên liệu) |
| `origin` | str(100) | Xuất xứ |
| `quote_unit` | str(25) | Đơn vị báo giá |
| `moq` | decimal(18,3) | Số lượng đặt tối thiểu |
| `price_by_volume` | decimal(18,4) | Đơn giá theo sản lượng (4 số lẻ) |
| `volume_range` | str(100) | Khoảng sản lượng áp dụng giá |
| `last_purchase_price` | decimal(18,4) | Giá mua gần nhất (tự điền từ lịch sử, sửa đè được; CR-111) |
| `max_purchase_price` | decimal(18,4) | Giá mua cao nhất lịch sử (tự điền, sửa đè được; CR-111) |
| `vat` | decimal(5,2) | % VAT |
| `request_qty` | decimal(18,3) | Số lượng yêu cầu |
| `amount` | decimal(18,2) | Thành tiền (qty × giá × (1 + VAT%)) |
| `internal_unit` | str(25) | Đơn vị tính nội bộ |
| `amount_converted` | decimal(18,2) | Thành tiền quy đổi |
| `shipping_cost` | decimal(18,2) | Phí vận chuyển theo báo giá NCC |
| `extra_shipping_cost` | decimal(18,2) | Phí phát sinh giao tới kho người yêu cầu (thương lượng riêng) |
| `shipping_policy` | str(255) | Chính sách vận chuyển |
| `debt_policy` | str(50) | Ngày công nợ |
| `delivery_time` | str(100) | Thời gian giao hàng |
| `delivery_place` | str(255) | Địa điểm giao hàng |
| `quote_file` | str(500) | Đường dẫn file báo giá |
| `sample_ready` | bool | Có mẫu sẵn |
| `sample_date` | str(10) | Ngày có mẫu |
| `sample_qty` | decimal(18,3) | Số lượng mẫu |
| `lab_result` | str(255) | Kết quả kiểm nghiệm |
| `lab_note` | text | Ghi chú kiểm nghiệm |
| `nspt_note` | str(255) | Nhận xét của NSTM |
| `nspt_reason` | text | Lý do / ghi chú NSTM (CR-147: snapshot sang `nstm_note` trong option, hiện cho người yêu cầu xem) |
| `line_approve` | str(255) | Trạng thái duyệt dòng SP (ngoại lệ — chuỗi, không phải mã cố định) |
| `line_approve_note` | text | Ghi chú duyệt dòng |
| `note` | text | Ghi chú chung |
| `import_line_key` | str(200) | Khóa idempotent khi nhập từ file |

**Logic chính:**

- Dòng `line_approve = "Đã duyệt"` mới được NSTM gắn làm option cho dòng YCBG.
- Dòng bị `"Không duyệt"` → hệ thống tự gỡ (`_purge_yc_options`) tất cả option YCBG đang tham chiếu dòng này.
- `last_purchase_price` và `max_purchase_price` tự điền từ lịch sử mua hàng của mã VTBB ở header phiếu, nhưng sửa đè được — không phải giá trị tính động (CR-111).
- Xóa/tạo lại toàn bộ khi lưu phiếu (không upsert); id dòng thay đổi mỗi lần save.
- `nspt_reason` được snapshot vào `tab_survey_request_option.nstm_note` lúc tạo option.

---

## `tab_purchase_request` — Yêu cầu mua hàng

Phiếu yêu cầu mua hàng do bộ phận lập, sau khi được duyệt sẽ là cơ sở để NSTM lập đơn mua hàng. Mã nguồn: `backend/app/modules/purchase_request/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `code` | str(50) | Mã phiếu duy nhất, định dạng `PYCDDMMYYnn` |
| `company_id` | int | ID pháp nhân nhận hóa đơn (apply_scope lọc theo cột này) |
| `requester` | str(255) | Tên người yêu cầu (bản chụp) |
| `requester_id` | int | ID nhân sự người yêu cầu (phân quyền phạm vi) |
| `requester_position` | str(100) | Chức vụ người yêu cầu (bản chụp) |
| `department_id` | int | ID phòng ban — nguồn sự thật (CR-086) |
| `department` | str(255) | Bản chụp tên phòng ban — sẽ xóa (N-008) |
| `head_of_dept` | str(255) | Bản chụp tên trưởng bộ phận để in |
| `head_of_dept_id` | int | ID nhân sự trưởng bộ phận (CR-071) — chỉ lưu + in, không khóa quyền duyệt |
| `purpose` | str(255) | Mục đích mua hàng |
| `request_date` | str(10) | Ngày lập phiếu (YYYY-MM-DD) |
| `need_date` | str(10) | Ngày cần hàng |
| `status` | str(30) | Trạng thái: `draft` / `submitted` / `approved` / `rejected` / `completed` |
| `is_urgent` | bool | Cờ gấp |
| `vat_rate` | decimal(5,4) | Tỷ lệ VAT mặc định cho phiếu (0.08 = 8%) |
| `assignee_id` | int | ID nhân sự NSTM phụ trách phiếu (không phải cột `assignee` của dòng) |
| `note` | text | Ghi chú |
| `show_code_on_print` | bool | Hiển thị mã sản phẩm khi in phiếu |
| `suggested_supplier` | str(255) | NCC hiệu lực (đồng bộ từ `supplier_info`, dùng cho ĐMH/list/in cũ) |
| `suggested_supplier_tax_code` | str(50) | MST NCC hiệu lực |
| `suggested_supplier_contact` | str(255) | Liên hệ NCC hiệu lực |
| `quote_filename` | str(255) | Tên file báo giá đính kèm |
| `quote_file_url` | str(1000) | URL file báo giá |
| `supplier_info` | text | JSON 2 cụm NCC: `{"req":{name,tax_code,contact}, "pur":{...}, "from_survey":bool}` |
| `is_deleted` | bool | Soft delete |

**Logic chính:**

- Vòng đời `status`: `draft` → `submitted` → `approved` / `rejected`; khi mọi dòng đạt `completed` hoặc `cancelled` → phiếu tự lên `completed`.
- `supplier_info` lưu 2 cụm NCC: `req` (bộ phận đề xuất, ai cũng sửa được) và `pur` (thu mua/khảo sát, cần quyền `supplier.write`). NCC hiệu lực = cụm `pur` nếu có tên, ngược lại `req`; đồng bộ xuống `suggested_supplier*` để ĐMH cũ dùng.
- `head_of_dept_id` chỉ để lưu + in; không khóa quyền duyệt (CR-071).
- `department_id` là nguồn sự thật cho lọc và thông báo; `department` chỉ dùng đối chiếu phiếu cũ.
- Mã hàng phải duy nhất trên mỗi phiếu (`assert_unique_product_codes`).

---

## `tab_purchase_request_item` — Dòng hàng của YCMH

Mỗi dòng là một sản phẩm/vật tư trong phiếu yêu cầu mua hàng. Mã nguồn: `backend/app/modules/purchase_request/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `pr_id` | int | FK → `tab_purchase_request.id` |
| `product_code` | str(50) | Mã sản phẩm (nối theo chuỗi với ĐMH — không có FK vật lý) |
| `product_name` | str(255) | Tên sản phẩm |
| `item_group` | str(100) | Phân loại |
| `group_desc` | str(255) | Mô tả phân loại (vd: thời gian sản xuất) |
| `qty` | decimal(18,3) | Số lượng yêu cầu |
| `unit` | str(25) | Đơn vị tính |
| `price` | decimal(18,4) | Giá đề xuất chưa VAT (4 số lẻ) |
| `vat_pct` | decimal(5,2) | % VAT theo dòng |
| `amount` | decimal(18,2) | Thành tiền = qty × price × (1 + vat_pct / 100) |
| `warehouse` | str(100) | Kho nhận hàng |
| `required_date` | str(10) | Ngày cần hàng theo dòng |
| `expected_date` | str(10) | Dự kiến có hàng (NSTM cập nhật; đổi giá trị đã có phải kèm lý do) |
| `assignee` | str(100) | Mã nhân viên NSTM phụ trách dòng — scope "được giao" lọc theo cột này |
| `line_status` | str(30) | Mã trạng thái dòng: `no_po` / `not_ordered` / `ordered` / `received` / `completed` / `cancelled` |
| `qty_ordered` | decimal(18,3) | Tổng SL đã đặt (đồng bộ từ ĐMH liên kết) |
| `qty_received` | decimal(18,3) | Tổng SL đã nhận (đồng bộ từ ĐMH liên kết) |
| `progress_note` | text | Chi tiết tiến độ |
| `note` | str(255) | Ghi chú ngắn |

**Logic chính:**

- `line_status` dùng mã cố định theo `PR_LINE_STATUS` (B-06): `no_po` (mặc định, chưa có ĐMH) → `not_ordered` (đã có dòng ĐMH kể cả nháp, chưa đặt) → `ordered` → `received` → `completed` / `cancelled`.
- `no_po` và `not_ordered` là nhóm "chưa động tới" (`LINE_STATUS_IDLE`); `completed` và `cancelled` là điểm cuối (`LINE_STATUS_DONE`).
- `product_code` phải duy nhất trên mỗi phiếu.
- `expected_date` được copy từ dòng YCMH xuống dòng ĐMH khi tạo ĐMH.

---

## `tab_purchase_order` — Đơn mua hàng

Module trung tâm của vòng đời mua hàng. Lưu thông tin hợp đồng mua với nhà cung cấp, bao gồm điều khoản thanh toán và liên kết ngược lên YCMH. Mã nguồn: `backend/app/modules/purchase_order/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `code` | str(50) | Mã đơn duy nhất (vd: `PO00045`) |
| `misa_code` | str(50) | Mã đơn trên phần mềm kế toán MISA |
| `pr_code` | str(50) | Mã YCMH nguồn (cross-ref nóng — dùng để đồng bộ tiến độ) |
| `survey_code` | str(50) | Mã phiếu khảo sát nguồn |
| `company_id` | int | ID pháp nhân nhận hóa đơn |
| `supplier_code` | str(50) | Mã NCC bán hàng |
| `supplier_name` | str(255) | Tên NCC (bản chụp) |
| `department_id` | int | ID phòng ban — nguồn sự thật (CR-086) |
| `department` | str(255) | Bản chụp tên phòng ban — sẽ xóa (N-008) |
| `nspt_id` | int | ID nhân sự NSTM phụ trách (CR-087) |
| `nspt` | str(100) | Bản chụp tên NSTM — sẽ xóa (N-008) |
| `order_date` | str(10) | Ngày đặt hàng |
| `vat_rate` | decimal(5,4) | Tỷ lệ VAT mặc định toàn đơn |
| `payment_terms` | str(255) | Điều khoản thanh toán cho NCC |
| `is_urgent` | bool | Cờ gấp |
| `status` | str(30) | Trạng thái: `draft` / `submitted` / `approved` / `partial` / `received` / `cancelled` |
| `document_status` | str(30) | Trạng thái hồ sơ chứng từ kế toán (cập nhật tay): `none` / `partial` / `full` |
| `note` | text | Ghi chú |
| `approve_note` | text | Ghi chú khi duyệt |

**Logic chính:**

- Vòng đời `status`: `draft` → `submitted` → `approved` → `partial` → `received` → `cancelled`.
- `document_status` cập nhật tay theo hồ sơ giấy tờ kế toán, độc lập với `status`.
- `nspt_id` thay thế `nspt` (tên) làm nguồn sự thật — tên trùng nhau gây lộ đơn của người khác (CR-087).
- `pr_code` là cầu nối nóng với YCMH; không có FK vật lý để linh hoạt khi ĐMH độc lập.
- Mỗi lần lưu ĐMH (kể cả chỉ sửa một dòng) đều chạy `recompute_effects`: tính lại tồn kho, công nợ, phiếu nhập kho ngầm.

---

## `tab_po_item` — Dòng hàng của ĐMH

Mỗi dòng là một sản phẩm trên đơn mua hàng, bao gồm cả tiến độ giao nhận và chứng từ hóa đơn. Mã nguồn: `backend/app/modules/purchase_order/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `po_id` | int | FK → `tab_purchase_order.id` |
| `product_code` | str(50) | Mã sản phẩm (nối theo chuỗi với YCMH và lịch sử mua hàng) |
| `product_name` | str(255) | Tên sản phẩm |
| `invoice_name` | str(255) | Tên trên hóa đơn NCC xuất |
| `item_group` | str(100) | Phân loại |
| `spec` | str(255) | Xuất xứ / thông số kỹ thuật / chất liệu |
| `fg_code` | str(50) | Mã hàng hóa / thành phẩm |
| `fg_name` | str(255) | Tên hàng hóa / thành phẩm |
| `invoice_no` | str(50) | Số hóa đơn |
| `invoice_date` | str(10) | Ngày hóa đơn (tự gán hôm nay khi nhập số hóa đơn, sửa tay được) |
| `document_delivery_date` | str(10) | Ngày giao chứng từ cho kế toán |
| `supplier_ready` | bool | NCC có sẵn hàng |
| `required_date` | str(10) | Ngày yêu cầu có hàng |
| `expected_date` | str(10) | Dự kiến có hàng (copy từ dòng YCMH, sửa tay được) |
| `unit` | str(25) | Đơn vị tính |
| `qty_request` | decimal(18,3) | Số lượng yêu cầu |
| `qty_order` | decimal(18,3) | Số lượng đặt hàng thực tế |
| `price` | decimal(18,4) | Đơn giá (4 số lẻ) |
| `vat` | decimal(5,2) | % VAT của dòng |
| `amount` | decimal(18,2) | Thành tiền = qty_order × price × (1 + vat%) |
| `qty_received` | decimal(18,3) | Tổng SL đã nhận (tự tính từ lần giao, không nhập tay) |
| `qty_remaining` | decimal(18,3) | SL còn lại chưa nhận |
| `line_status` | str(30) | Trạng thái giao nhận: rỗng / `not_delivered` / `partial` / `full` (tự tính) |
| `warehouse_code` | str(50) | Kho mặc định cho dòng |
| `note` | str(255) | Ghi chú |
| `progress_status` | str(40) | Tiến độ dòng: `not_ordered` / `ordered` / `received` / `doc_pending` / `doc_sent` / `completed` / `paused` / `cancelled` |
| `pay_confirm_date` | str(10) | Ngày kế toán xác nhận thanh toán |
| `pause_reason` | str(500) | Lý do hủy / tạm ngưng |
| `status_before_pause` | str(40) | Bản chụp `progress_status` ngay trước khi tạm ngưng — dùng để khôi phục |

**Logic chính:**

- `progress_status` là máy trạng thái tiến độ: `not_ordered` → `ordered` → `received` → `doc_pending` → `doc_sent` → `completed`; có thể vào `paused` từ bất kỳ bước nào.
- Dòng đạt `completed` hoặc `cancelled` bị khóa cứng — không cho sửa.
- Dòng đã nhận hàng (`qty_received > 0`) không cho đổi `product_code`, `product_name`, `unit` để bảo toàn số liệu kho.
- `line_status` tự tính từ SL nhận so SL đặt (`_recalc`), không ai nhập tay.
- `status_before_pause` phải dùng cùng bộ mã `PO_PROGRESS_STATUS` với `progress_status`; đổi bộ mã phải đổi cả hai cột.
- Khi dòng vào `completed`: snapshot tự động vào `tab_purchase_history`.

---

## `tab_po_delivery` — Lần giao hàng

Ghi nhận từng lần giao hàng của một dòng ĐMH (một dòng có thể giao nhiều lần). Là nguồn để sinh phiếu nhập kho ngầm, cập nhật tồn kho và công nợ. Mã nguồn: `backend/app/modules/purchase_order/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `po_id` | int | FK → `tab_purchase_order.id` |
| `po_item_id` | int | FK → `tab_po_item.id` |
| `delivery_no` | int | Số thứ tự lần giao |
| `warehouse_code` | str(50) | Kho nhận hàng lần này |
| `carrier_code` | str(50) | Mã đơn vị vận chuyển |
| `carrier_name` | str(255) | Tên đơn vị vận chuyển |
| `ship_qty` | decimal(18,3) | Số lượng NCC gửi |
| `ship_unit` | str(25) | Đơn vị tính khi vận chuyển |
| `received_qty` | decimal(18,3) | Số lượng thực tế nhận được |
| `promised_date` | str(10) | NCC cam kết giao (mặc định = ngày quy định theo phân loại) |
| `expected_date` | str(10) | Đã bỏ dùng — không nơi nào ghi; "dự kiến có hàng" nay ở `POItem.expected_date` |
| `received_date` | str(10) | Ngày nhận thực tế |
| `std_days` | int | Số ngày quy định (AH) |
| `regulated_date` | str(10) | Ngày quy định có hàng (AI) |
| `diff_promise` | int | Chênh lệch cam kết − nhận (AL); âm = trễ |
| `diff_regulated` | int | Chênh lệch quy định − nhận (AM) |
| `diff_required` | int | Chênh lệch quy định − yêu cầu kinh doanh (AN) |
| `invoice_no` | str(50) | Số hóa đơn theo lần giao |
| `invoice_date` | str(10) | Ngày hóa đơn |
| `shipping_unit_price` | decimal(18,4) | Đơn giá vận chuyển (4 số lẻ) |
| `shipping_amount` | decimal(18,2) | Tiền vận chuyển |
| `qc_result` | str(20) | Kết quả kiểm tra: `Đạt` / `Thiếu` / `Lỗi` |
| `status` | str(30) | Trạng thái lần giao: `pending` / `short` / `defect` / `received` (tự tính) |
| `extra_request` | text | Yêu cầu khác (AC) |
| `progress_note` | text | Chi tiết tiến độ (AG) |

**Logic chính:**

- `status` tự tính bởi `_recalc` sau mỗi lần sửa lần giao, dùng bộ mã `PO_DELIVERY_STATUS` (B-06).
- Khi `received_qty > 0`: tự sinh/cập nhật phiếu nhập kho ngầm (`tab_goods_receipt`) và cập nhật tồn kho.
- Khi xóa lần giao: gỡ toàn bộ side-effect (nhập kho, tồn kho, công nợ hàng hóa, công nợ vận chuyển).
- `promised_date` mặc định = ngày quy định theo phân loại khi tạo mới; không ghi đè khi đã có giá trị.
- `expected_date` là cột chết — được giữ lại theo luật "CSDL cũ: chỉ thêm, không sửa".

---

## `tab_goods_receipt` — Phiếu nhập kho

Sinh tự động khi ghi nhận nhận hàng trên lần giao của ĐMH (1 phiếu/lần giao). Không có màn nhập riêng. Mã nguồn: `backend/app/modules/goods_receipt/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `code` | str(50) | Mã phiếu tự sinh (`GRnnnnn`) |
| `po_id` | int | FK → `tab_purchase_order.id` |
| `po_code` | str(50) | Mã ĐMH (denormalize) |
| `delivery_id` | int | FK → `tab_po_delivery.id` (unique — 1 lần giao / 1 phiếu nhập kho) |
| `company_id` | int | ID pháp nhân |
| `warehouse_code` | str(50) | Kho nhận hàng |
| `product_code` | str(50) | Mã sản phẩm (nối theo chuỗi) |
| `product_name` | str(255) | Tên sản phẩm (bản chụp) |
| `unit` | str(25) | Đơn vị tính |
| `qty_received` | decimal(18,3) | Số lượng thực nhận |
| `received_date` | str(10) | Ngày nhận |
| `qc_result` | str(20) | Kết quả kiểm tra: `Đạt` / `Thiếu` / `Lỗi` |
| `note` | text | Ghi chú |

**Logic chính:**

- Upsert (tạo hoặc cập nhật) theo `delivery_id` — idempotent khi tính lại sau chỉnh sửa lần giao.
- Bị xóa tự động khi lần giao tương ứng bị xóa (`remove_for_delivery`).
- Không có luồng nghiệp vụ riêng — toàn bộ vòng đời phụ thuộc vào `tab_po_delivery`.

---

## `tab_purchase_history` — Lịch sử mua hàng

Snapshot bất biến của một dòng hàng ĐMH tại thời điểm dòng đó đạt `completed`. Phục vụ màn chi tiết Sản phẩm và màn chi tiết NCC. Mã nguồn: `backend/app/modules/purchase_history/model.py`.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `id` | int | Khóa chính |
| `po_item_id` | int (unique, nullable) | FK → `tab_po_item.id` (NULL cho dữ liệu cũ từ file Excel) |
| `source` | str(10) | Nguồn: `system` (tự động) / `legacy` (nhập từ file lịch sử) |
| `legacy_key` | str(190) (unique, nullable) | Khóa nguồn dữ liệu cũ (file + sheet + số dòng) — chống nhập trùng |
| `po_id` | int | ID ĐMH (0 cho dữ liệu cũ) |
| `po_code` | str(50) | Mã ĐMH |
| `product_code` | str(50) | Mã sản phẩm — dùng để lọc màn Sản phẩm |
| `supplier_code` | str(50) | Mã NCC — dùng để lọc màn NCC |
| `order_date` | str(10) | Ngày đặt hàng (sắp xếp mặc định giảm dần) |
| `company_id` | int | ID pháp nhân |
| `product_name` | str(255) | Tên sản phẩm (snapshot) |
| `supplier_name` | str(255) | Tên NCC (snapshot) |
| `company_name` | str(255) | Tên pháp nhân (snapshot — denormalize để bảng tự đứng được) |
| `unit` | str(25) | Đơn vị tính |
| `qty_order` | decimal(18,3) | Số lượng đặt |
| `price` | decimal(18,4) | Đơn giá tại thời điểm chốt (4 số lẻ — nếu để 2 số lẻ MySQL làm tròn mất số lẻ vĩnh viễn) |
| `vat` | decimal(5,2) | % VAT |
| `amount` | decimal(18,2) | Thành tiền |
| `completed_at` | str(10) | Ngày dòng ĐMH vào `completed` |
| `extra` | text | JSON gom phần còn lại: `pr_code`, `misa_code`, `nspt`, `payment_terms`, `is_urgent`, `po_note`, `department`, `item_group`, `spec`, `invoice_name`, `fg_code`, `fg_name`, `qty_received`, `required_date`, `invoice_no`, `invoice_date`, `warehouse_code`, `item_note` |

**Logic chính:**

- Bất biến: ghi một lần khi dòng ĐMH vào `completed`, không sửa/xóa sau đó.
- `po_item_id` unique là lớp bảo hiểm chống ghi trùng; `auto_advance_line` bỏ qua dòng đã ở `completed` nên snapshot chỉ chạy đúng một lần.
- Dữ liệu cũ (`source = "legacy"`) không có `po_item_id` (NULL) và dùng `legacy_key` để chống trùng.
- Cột phẳng (`product_code`, `supplier_code`, `order_date`, v.v.) phục vụ lọc/sắp xếp; phần còn lại gói vào `extra` (JSON, không lọc/sort).
- Có 2 composite index: `(product_code, order_date)` và `(supplier_code, order_date)` — prefix bên trái phủ cả truy vấn lọc đơn cột.

---

## Quan hệ trong cụm

Sơ đồ kết nối chính giữa các bảng trong cụm chứng từ thu mua:

- **`tab_survey_request`** ← `tab_survey_request_line` (`survey_request_id`): một YCBG có nhiều dòng.
- **`tab_survey_request_line`** ← `tab_survey_request_option` (`survey_request_line_id`): mỗi dòng YCBG có tối đa 5 option (snapshot từ phiếu khảo sát).
- **`tab_survey_request_option.product_survey_line_id`** → `tab_survey_product_line.id`: liên kết option với dòng SP nguồn — nếu nguồn bị xóa thì vẫn giữ snapshot trong option.
- **`tab_survey_request`** ← `tab_survey_request_pr` (`survey_request_id`) → `tab_purchase_request` (`pr_id`): bảng liên kết ghi nhận mỗi lần tạo YCMH từ option đã chọn; một dòng YCBG có thể dẫn đến nhiều YCMH.
- **`tab_survey`** ← `tab_survey_supplier_line` / `tab_survey_product_line` (`survey_id`): một phiếu khảo sát có nhiều dòng NCC và nhiều dòng SP.
- **`tab_survey.survey_request_id`** → `tab_survey_request.id`: phiếu khảo sát liên kết với YCBG nguồn.
- **`tab_purchase_request`** ← `tab_purchase_request_item` (`pr_id`): một YCMH có nhiều dòng hàng.
- **`tab_purchase_order`** ← `tab_po_item` (`po_id`) ← `tab_po_delivery` (`po_item_id`): chuỗi 3 cấp ĐMH → dòng → lần giao.
- **`tab_po_delivery.delivery_id`** ↔ `tab_goods_receipt.delivery_id` (unique): 1 lần giao chỉ có 1 phiếu nhập kho.
- **`tab_po_item.id`** ↔ `tab_purchase_history.po_item_id` (unique): khi dòng ĐMH vào `completed`, một bản snapshot ghi vào lịch sử mua hàng.
- **Nối theo chuỗi `product_code`** (không có FK vật lý): `tab_purchase_request_item`, `tab_po_item`, `tab_goods_receipt`, `tab_purchase_history`, `tab_survey_product_line` (qua `Survey.item_code`), và `tab_survey_request_option.system_product_code` đều dùng `product_code` làm hạt nối — thay đổi mã sản phẩm sau khi đã nhận hàng là vi phạm tính nhất quán và bị service chặn cứng.
- **Nối ĐMH ↔ YCMH theo chuỗi `pr_code`**: `tab_purchase_order.pr_code = tab_purchase_request.code` — không có FK vật lý để ĐMH độc lập (không bắt buộc từ YCMH) vẫn hợp lệ.
