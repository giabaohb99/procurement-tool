# Phiếu khảo sát

## Mục đích

Ghi nhận kết quả khảo sát giá/nhà cung cấp cho một nhu cầu mua hàng. Một phiếu gồm hai bảng:

- Khảo sát Nhà cung cấp (NCC): thông tin từng NCC được liên hệ.
- Khảo sát Sản phẩm (SP): báo giá từng sản phẩm theo NCC.

Đường dẫn: `/surveys` (danh sách), `/surveys/:id` (chi tiết).

## Vai trò tham gia

- NSPT / Người tạo phiếu (`survey:write`): nhập nội dung phiếu, các dòng NCC và SP.
- TP/QL / Người duyệt (`survey:approve`): duyệt từng dòng và duyệt cả phiếu.

## Vòng đời trạng thái

| Trạng thái | Ý nghĩa | Nút thao tác hiển thị |
|-----------|---------|-----------------------|
| Nháp (`draft`) | Đang soạn (ẩn nhãn trạng thái) | Lưu, Gửi duyệt, Xóa |
| Chờ duyệt (`submitted`) | Đã gửi, đợi TP/QL | Duyệt phiếu, Từ chối, Trả lại |
| Đã duyệt (`approved`) | TP/QL đã duyệt | (chỉ xem) |
| Bị trả lại (`rejected`) | TP/QL trả về để NSPT sửa & gửi lại | Lưu, Gửi duyệt, Xóa |
| Đã từ chối (`cancelled`) | TP/QL từ chối (khóa) | Xóa |

Chỉ trạng thái Nháp (`draft`) và Bị trả lại (`rejected`) mới cho phép sửa nội dung và xóa phiếu. Trạng thái Đã từ chối (`cancelled`) cũng cho phép xóa nhưng không cho sửa. Riêng dòng bị đánh dấu "Thiếu thông tin" có thể mở ở chế độ Bổ sung để sửa dù phiếu đang ở trạng thái Chờ duyệt hoặc Đã duyệt.

---

## A. Thông tin tiếp nhận (phần đầu phiếu)

### 1. Yêu cầu báo giá (YCBG) (`sr_code` + `survey_request_id`)

- Kiểu nhập: Nhập/chọn — ô gõ tự do với gợi ý danh sách Yêu cầu báo giá (datalist), placeholder "Nhập/chọn mã YCBG để tự điền…"
- Mặc định: trống (tự gắn sẵn nếu mở phiếu từ nút "Tạo phiếu khảo sát" trên Yêu cầu báo giá)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Danh sách Yêu cầu báo giá (YCBG, module `survey_request`) — hiển thị theo phạm vi người dùng (NSTM chỉ thấy phiếu được gán, admin/quản lý thấy hết). Lưu cả `survey_request_id` (id) và `sr_code` (mã)
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Chọn YCBG tự điền Nội dung chính (trường `main_content`) từ trường "Mục đích" (`purpose`) của YCBG. Là liên kết để hệ thống tự gắn phương án (option) ngược lại cho dòng YCBG khớp phân loại — kích hoạt mỗi khi duyệt dòng khảo sát (`PATCH /line-approve`) hoặc duyệt cả phiếu (`POST /approve`). (Trường `pr_code` cũ vẫn còn trong dữ liệu để tương thích ngược, không còn dùng trên form.)

### 2. Nội dung chính (`main_content`)

- Kiểu nhập: Nhập văn bản (một dòng)
- Mặc định: trống; tự điền từ trường "Mục đích" (`purpose`) của Yêu cầu báo giá (YCBG) khi chọn YCBG
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Hiển thị trong danh sách phiếu và bộ lọc. Tự điền một lần từ trường "Mục đích" (`purpose`) của YCBG khi chọn liên kết YCBG; có thể sửa thủ công sau đó. Tối đa 500 ký tự.

### 3. Ngày tiếp nhận (`received_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: Ngày hiện tại (hôm nay)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 4. Ngày dự kiến trả KQ (`result_due_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 5. Phân loại (`item_group`)

- Kiểu nhập: Chọn (ô tìm kiếm, gõ để lọc)
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: Bảng Phân loại (`item_group`)
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Tự điền khi chọn Mã VTBB/VL nếu sản phẩm đó đã có phân loại

### 6. NSPT phụ trách (`nspt`)

- Kiểu nhập: Tự động
- Mặc định: Tên đầy đủ của người đang đăng nhập (`user.full_name`)
- Bắt buộc: — (hệ thống điền, không sửa được)
- Nguồn dữ liệu / liên kết: Tài khoản người tạo phiếu
- Người sửa: Hệ thống (trường bị khóa, không chỉnh sửa thủ công)

### 7. Yêu cầu kỹ thuật & chất lượng (`requirement_detail`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt (trừ khi đã tick "Đã có mã sản phẩm sẵn" — xem trường 8)
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Khi tick "Đã có mã sản phẩm sẵn", trường này không bắt buộc (thay thế bằng nhóm trường Mã VTBB/VL, SL, ĐVT, Giá đề xuất)

### 8. Đã có mã sản phẩm sẵn (`has_product_code`)

- Kiểu nhập: Checkbox
- Mặc định: Không tích
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Khi tích, hiện thêm bốn trường bên dưới (Mã VTBB/VL, Số lượng dự kiến mua, ĐVT, Giá đề xuất) và chuyển nghĩa vụ bắt buộc từ Yêu cầu kỹ thuật sang bốn trường đó

### 9. Mã VTBB/VL (`item_code`)

- Kiểu nhập: Chọn sản phẩm (ProductPicker — tìm theo mã hoặc tên)
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt (chỉ khi đã tick "Đã có mã sản phẩm sẵn")
- Nguồn dữ liệu / liên kết: Danh mục Sản phẩm (`product`)
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Chọn mã tự điền Tên VTBB/VL, ĐVT, Phân loại. Tên VTBB/VL hiển thị ngay bên cạnh (trường đọc, không sửa)

### 10. Số lượng dự kiến mua (`request_qty`)

- Kiểu nhập: Nhập số
- Mặc định: 0 (hiển thị trống khi bằng 0)
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt (chỉ khi đã tick "Đã có mã sản phẩm sẵn")
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Thông tin tham khảo ở cấp phiếu (khi đã có mã sản phẩm sẵn). Công thức Thành tiền của dòng Sản phẩm sử dụng trường `request_qty` riêng của từng dòng SP (xem mục C).

### 11. ĐVT (`uom`)

- Kiểu nhập: Chọn (ô tìm kiếm, gõ để lọc)
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt (chỉ khi đã tick "Đã có mã sản phẩm sẵn")
- Nguồn dữ liệu / liên kết: Bảng Đơn vị tính (`unit`)
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Tự điền khi chọn Mã VTBB/VL nếu sản phẩm đã có ĐVT mặc định

### 12. Giá đề xuất (`proposed_rate`)

- Kiểu nhập: Nhập số (VNĐ)
- Mặc định: 0 (hiển thị trống khi bằng 0)
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt (chỉ khi đã tick "Đã có mã sản phẩm sẵn")
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

---

## B. Dòng khảo sát Nhà cung cấp (NCC)

Mỗi dòng = một NCC. Bảng tóm tắt hiện các cột chính; toàn bộ trường xem và sửa trong popup "Chi tiết dòng".

**Nhóm: Lịch làm việc với NCC**

### 1. Ngày liên hệ NCC (`contact_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 2. Ngày dự kiến NCC phản hồi (`reply_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 3. Ngày dự kiến trả KQ (`result_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

**Nhóm: Thông tin nhà cung cấp**

### 4. Tên viết tắt NCC (`supplier_code`)

- Kiểu nhập: Chọn (ô tìm kiếm, gõ để lọc), hiển thị "mã — tên"
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhà cung cấp (`supplier`)
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Chọn NCC tự điền Tên nhà cung cấp, Mã số thuế, Địa chỉ theo giấy đăng kí. Dòng chỉ bị kiểm tra bắt buộc khi Gửi duyệt nếu trường này không trống. Trong cả bảng tóm tắt và popup chi tiết dòng có thêm ô "NCC sẵn có" (checkbox, không lưu vào DB): khi bỏ tích, ô Tên viết tắt NCC chuyển sang nhập text tự do để ghi NCC chưa có trong danh mục.

### 5. Tên nhà cung cấp (`supplier_name`)

- Kiểu nhập: Nhập tay (tự điền khi chọn NCC)
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: Tự điền từ `supplier.name`; có thể sửa thủ công sau
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 6. Mã số thuế (`tax_code`)

- Kiểu nhập: Nhập tay (tự điền khi chọn NCC)
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: Tự điền từ `supplier.tax_code`; có thể sửa thủ công sau
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 7. Địa chỉ theo giấy đăng kí (`reg_address`)

- Kiểu nhập: Nhập nhiều dòng (tự điền khi chọn NCC)
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: Tự điền từ `supplier.address`; có thể sửa thủ công sau
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 8. Địa chỉ kho của NCC (`warehouse_address`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 9. Link định vị kho (`google_maps`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

**Nhóm: Kinh doanh & Báo giá**

### 10. NVKD của NCC (`contact_person`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 11. SĐT NCC đang làm việc (`contact_phone`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 12. Nhóm SP/dịch vụ cung ứng (`supply_group`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 13. Link báo giá (`quote_folder`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 14. Nguồn thông tin đầu vào (`source_of_information`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

**Nhóm: Đánh giá mặt hàng khảo sát**

### 15. Công nghệ SX, đa dạng chủng loại (`production_tech`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 16. Thời gian SX (`production_time`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 17. Đánh giá tư vấn NVKD (`nvkd_eval`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 18. Hóa đơn (`invoice_policy`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 19. Mức độ tin cậy (`reliability`)

- Kiểu nhập: Nhập tay (popup chi tiết); trong bảng tóm tắt: Chọn từ danh sách — Cao / Trung bình / Thấp
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: Popup nhập tự do; ô bảng đề xuất giá trị: Cao / Trung bình / Thấp
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 20. Chính sách nhận hàng (`delivery_policy`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 21. Chính sách công nợ (`debt_policy`)

- Kiểu nhập: Nhập nhiều dòng (popup chi tiết); trong bảng tóm tắt: Chọn từ danh sách
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: Popup nhập tự do; ô bảng đề xuất giá trị: Tiền mặt / Công nợ 30 ngày / Công nợ 60 ngày / Công nợ 90 ngày / Trả trước
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 22. Hàng lỗi, hàng trả (`defect_return`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 23. Nhận xét (NSPT) (`nspt_note`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 24. Lý do (NSPT) (`nspt_reason`)

- Kiểu nhập: Nhập nhiều dòng (chỉ hiển thị trong bảng tóm tắt — không có trong popup chi tiết dòng)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

**Nhóm: Ghi chú**

### 25. Ghi chú (`note`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

**Nhóm: Phê duyệt Trưởng phòng / Quản lý**

### 26. Duyệt (TP/QL) (`line_approve`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: Chờ duyệt
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Chờ duyệt / Đã duyệt / Không duyệt / Thiếu thông tin
- Người sửa: TP/QL (quyền `survey:approve`) khi phiếu Nháp, Chờ duyệt, hoặc Bị trả lại
- Logic đặc biệt: Chọn "Thiếu thông tin" mở nút "Bổ sung" trên dòng, cho phép NSPT sửa nội dung dù phiếu đang ở trạng thái Chờ duyệt

### 27. Yêu cầu (TP/QL) (`line_approve_note`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: TP/QL (quyền `survey:approve`) khi phiếu Nháp, Chờ duyệt, hoặc Bị trả lại

---

## C. Dòng khảo sát Sản phẩm (SP)

Mỗi dòng = một sản phẩm / báo giá theo NCC.

**Nhóm: Lịch làm việc**

### 1. Ngày liên hệ (`contact_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 2. Ngày dự kiến phản hồi (`reply_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 3. Ngày dự kiến trả KQ (`result_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

**Nhóm: Nhà cung cấp & Sản phẩm**

### 4. Tên viết tắt NCC (`supplier_code`)

- Kiểu nhập: Chọn (ô tìm kiếm, gõ để lọc), hiển thị "mã — tên"
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Nhà cung cấp (`supplier`)
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Trong cả bảng tóm tắt và popup chi tiết dòng có thêm ô "NCC sẵn có" (checkbox, không lưu vào DB): khi bỏ tích, ô Tên viết tắt NCC chuyển sang nhập text tự do để ghi NCC chưa có trong danh mục.

### 4a. Tên pháp lý NCC (`supplier_name`) — chỉ hiển thị FE

- Kiểu nhập: Nhập tay (tự điền từ danh mục khi chọn NCC theo `supplier_code`, cho phép sửa thủ công)
- Mặc định: trống; tự tra từ `supplier.name` theo `supplier_code` đã chọn
- Bắt buộc: Không (kiểu trường 'legal' bỏ qua khi kiểm tra Gửi duyệt)
- Nguồn dữ liệu / liên kết: Tự tra từ danh mục Nhà cung cấp; có thể sửa tay tạm thời
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Hiển thị trong cả bảng tóm tắt (cột "Tên pháp lý") và popup chi tiết dòng (nhãn "Tên pháp lý NCC"). Lưu ý: trường này KHÔNG có trong model `SurveyProductLine` và không được lưu vào DB — mỗi lần tải lại trang sẽ hiển thị lại theo danh mục NCC.

### 5. Mã SP (theo NCC) (`internal_code`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 6. Tên SP (tên NCC đặt) (`product_name`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Đây là trường xác định dòng — khi Gửi duyệt, chỉ kiểm tra các trường bắt buộc của những dòng có trường này không trống

### 7. Thông số kỹ thuật (`spec`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 8. Xuất xứ sản phẩm (`origin`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

**Nhóm: Báo giá & Quy đổi**

### 9. ĐVT báo giá (`quote_unit`)

- Kiểu nhập: Chọn (ô tìm kiếm, gõ để lọc)
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: Bảng Đơn vị tính (`unit`)
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 10. MOQ tối thiểu (`moq`)

- Kiểu nhập: Nhập số
- Mặc định: 0 (hiển thị trống khi bằng 0)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 11. Giá theo sản lượng (`price_by_volume`)

- Kiểu nhập: Nhập số (VNĐ)
- Mặc định: 0 (hiển thị trống khi bằng 0)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Dùng trong công thức tính Thành tiền: SL YC dòng SP (`request_qty`) × Giá × (1 + VAT/100)

### 12. Khung sản lượng (`volume_range`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 13. VAT % (`vat`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: 0
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: 0 / 2 / 4 / 6 / 8 / 10
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 14. SL YC theo dòng (`request_qty`)

- Kiểu nhập: Nhập số (chỉ hiển thị và chỉnh sửa trực tiếp trong bảng tóm tắt — không có trong popup chi tiết dòng)
- Mặc định: 0 (hiển thị trống khi bằng 0)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Là số lượng yêu cầu theo từng dòng SP. Server dùng để tính `amount` khi lưu: SL YC × Giá theo sản lượng × (1 + VAT/100). Phân biệt với `request_qty` ở header (mục A) là thông tin tổng của cả phiếu khi đã có mã sản phẩm.

### 15. Thành tiền (`amount`)

- Kiểu nhập: Tự tính (server tính khi lưu; preview trên giao diện dùng MOQ thay thế)
- Mặc định: 0
- Bắt buộc: — (hệ thống tính, không sửa)
- Nguồn dữ liệu / liên kết: SL YC dòng SP (`request_qty`) × Giá theo sản lượng × (1 + VAT/100)
- Người sửa: Hệ thống (chỉ hiển thị)

### 16. ĐVT quy đổi về Cty (`internal_unit`)

- Kiểu nhập: Chọn (ô tìm kiếm, gõ để lọc)
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: Bảng Đơn vị tính (`unit`)
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 17. Thành tiền đã quy đổi (`amount_converted`)

- Kiểu nhập: Nhập số (VNĐ)
- Mặc định: 0 (hiển thị trống khi bằng 0)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 18. Chi phí vận chuyển (`shipping_cost`)

- Kiểu nhập: Nhập số (VNĐ)
- Mặc định: 0 (hiển thị trống khi bằng 0)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 19. Thời gian giao hàng (`delivery_time`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 20. Địa điểm giao/nhận (`delivery_place`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 21. Link báo giá (`quote_file`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

**Nhóm: Lấy mẫu & LAB**

### 22. Mẫu sẵn (`sample_ready`)

- Kiểu nhập: Checkbox
- Mặc định: Không tích
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Khi tích, các trường Ngày lấy mẫu và Đánh giá chất lượng LAB trở thành bắt buộc khi Gửi duyệt

### 23. Ngày lấy mẫu (`sample_date`)

- Kiểu nhập: Chọn ngày
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt (chỉ khi đã tick "Mẫu sẵn")
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 24. Số lượng mẫu nhận (`sample_qty`)

- Kiểu nhập: Nhập số
- Mặc định: 0 (hiển thị trống khi bằng 0)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 25. Đánh giá chất lượng từ LAB (`lab_result`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt (chỉ khi đã tick "Mẫu sẵn")
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 26. Ghi chú LAB (`lab_note`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại
- Logic đặc biệt: Trường hiển thị trong bảng tóm tắt (`PRODUCT_COLS`) nhưng không có trong form popup chi tiết dòng (`PRODUCT_SECTIONS`)

**Nhóm: Ghi chú**

### 27. Ghi chú (`note`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

**Nhóm: Đánh giá & Phê duyệt**

### 28. NSPT Đánh giá (`nspt_note`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không bắt buộc khi Nháp, bắt buộc khi Gửi duyệt
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 29. Lý do NSPT (`nspt_reason`)

- Kiểu nhập: Nhập nhiều dòng (chỉ hiển thị và chỉnh sửa trực tiếp trong bảng tóm tắt — không có trong popup chi tiết dòng)
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: NSPT/Người tạo (quyền `survey:write`) khi phiếu Nháp hoặc Bị trả lại

### 30. Duyệt (TP/QL) (`line_approve`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: Chờ duyệt
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Chờ duyệt / Đã duyệt / Không duyệt / Thiếu thông tin
- Người sửa: TP/QL (quyền `survey:approve`) khi phiếu Nháp, Chờ duyệt, hoặc Bị trả lại
- Logic đặc biệt: Chọn "Thiếu thông tin" mở nút "Bổ sung" trên dòng, cho phép NSPT sửa nội dung dù phiếu đang ở trạng thái Chờ duyệt

### 31. Ý kiến TP/QL (`line_approve_note`)

- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: TP/QL (quyền `survey:approve`) khi phiếu Nháp, Chờ duyệt, hoặc Bị trả lại

---

## D. Quy tắc nghiệp vụ

1. Lưu (nháp): giữ mọi dòng có nội dung, kể cả dòng dở dang; chỉ bỏ dòng trống hoàn toàn. Không bắt buộc chọn NCC hoặc Tên SP khi Lưu.
2. Gửi duyệt: kiểm tra các trường "Bắt buộc = khi Gửi duyệt". Phải có ít nhất 1 dòng NCC (đã chọn Tên viết tắt NCC) hoặc 1 dòng Sản phẩm (đã nhập Tên SP); thiếu cả hai thì không cho gửi. Các trường bắt buộc còn trống được tô đỏ nhẹ (ô bảng và trong popup chi tiết), kèm thông báo liệt kê dòng nào còn thiếu. Lưu ý: một dòng NCC chỉ bị kiểm tra khi `supplier_code` không trống; một dòng SP chỉ bị kiểm tra khi `product_name` không trống.
3. Chọn NCC: chọn `supplier_code` tự điền `supplier_name`, `tax_code`, `reg_address`.
4. Trường số: hiển thị trống khi bằng 0, gửi về BE là giá trị số (0 nếu để trống).
5. Trường duyệt (`line_approve`, `line_approve_note`): chỉ TP/QL (`survey:approve`) sửa; NSPT chỉ xem. Chọn "Thiếu thông tin" cho phép NSPT mở dòng ở chế độ Bổ sung để sửa dù phiếu đã gửi.
6. Đính kèm: mỗi dòng đính kèm file (PDF/ảnh/Excel, tối đa 10MB/file), lưu trên Cloudflare R2. Phiếu cũng có đính kèm ở cấp toàn phiếu (riêng với đính kèm theo dòng).
7. Nhân bản (`POST /api/surveys/{id}/clone`): tạo phiếu Nháp mới từ phiếu nguồn — copy toàn bộ thông tin tiếp nhận (header) + dòng NCC + dòng SP. Phiếu mới được cấp mã tự động (KS…); trạng thái = Nháp; kết quả duyệt header và dòng bị reset về trống/Chờ duyệt. Liên kết YCBG/PYC (`sr_code`, `survey_request_id`, `pr_code`) KHÔNG được copy — phiếu nhân bản hoàn toàn độc lập. Nút "Nhân bản" hiển thị trong danh sách phiếu (người có quyền `survey:create`).
8. Gỡ option YCBG khi dòng SP bị không duyệt (`_purge_yc_options`): hệ thống tự xóa các option Yêu cầu báo giá (YCBG) đang tham chiếu dòng khảo sát SP không còn hợp lệ, tránh để option lỗi vẫn hiện hoặc chọn được trên form YCBG.
   - **Duyệt từng dòng** (`approve_lines`): nếu dòng SP bị đặt `line_approve = "Không duyệt"` (từ chối dứt khoát) → hệ thống **xóa cứng** mọi option YCBG đang tham chiếu dòng đó ngay sau khi lưu kết quả duyệt. (Các trạng thái tạm "Chờ duyệt" / "Thiếu thông tin" KHÔNG xóa cứng — option chỉ bị **ẩn tạm** qua `valid_options_of`, để nếu dòng được duyệt lại thì option vẫn còn.)
   - **Hủy cả phiếu** (`set_status` → `cancelled`): gỡ option YCBG của mọi dòng SP thuộc phiếu bị hủy.
9. Đồng bộ option YCBG khi duyệt (`_sync_ycks_options` → `sync_options_from_surveys`): sau mỗi thao tác duyệt dòng (`PATCH /{sid}/line-approve`) hoặc duyệt cả phiếu (`POST /{sid}/approve`), nếu phiếu có liên kết với một YCBG (`survey_request_id` > 0), hệ thống tự gọi `sync_options_from_surveys` để gắn/cập nhật phương án (option) vào các dòng YCBG khớp phân loại. Thao tác này chạy đồng bộ trong cùng request (không phải background). Nếu lỗi, request vẫn thành công (exception bị bắt và bỏ qua).
10. Thông báo và Web Push: mỗi sự kiện trong luồng phiếu tạo chuông trong app **và** đẩy **Web Push** (best-effort) tới thiết bị đã đăng ký của người nhận. Người nhận theo từng sự kiện: Gửi duyệt → người có quyền `survey:approve` (Quản lý/Admin TM). Duyệt phiếu → người tạo. Từ chối (`cancelled`) hoặc Trả lại (`rejected`) → người tạo.

## E. Quyền thao tác (RBAC)

| Thao tác | Quyền yêu cầu | Điều kiện trạng thái |
|----------|---------------|----------------------|
| Xem | `survey:read` | mọi trạng thái (theo phạm vi dữ liệu) |
| Tạo / Sửa nội dung | `survey:write` (hoặc `create`) | Nháp / Bị trả lại / tạo mới |
| Gửi duyệt | `survey:write` | Nháp / Bị trả lại |
| Duyệt dòng / Duyệt phiếu / Từ chối / Trả lại | `survey:approve` | Chờ duyệt (duyệt dòng: Nháp/Chờ duyệt/Bị trả lại) |
| Nhân bản | `survey:create` | mọi trạng thái (theo phạm vi dữ liệu) |
| Xóa | `survey:delete` | Nháp / Bị trả lại / Đã từ chối |
