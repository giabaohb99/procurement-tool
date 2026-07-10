# Phiếu khảo sát

## Mục đích
Ghi nhận kết quả khảo sát giá/nhà cung cấp cho một nhu cầu mua hàng. Một phiếu gồm hai bảng:
- **Khảo sát Nhà cung cấp (NCC)**: thông tin từng NCC được liên hệ.
- **Khảo sát Sản phẩm (SP)**: báo giá từng sản phẩm theo NCC.

Đường dẫn: `/surveys` (danh sách), `/surveys/:id` (chi tiết).

## Vai trò tham gia
- **NSPT / Người tạo phiếu** (`survey:write`): nhập nội dung phiếu, các dòng NCC và SP.
- **TP/QL / Người duyệt** (`survey:approve`): duyệt từng dòng và duyệt cả phiếu.

## Vòng đời trạng thái
| Trạng thái | Ý nghĩa | Nút thao tác hiển thị |
|-----------|---------|-----------------------|
| Nháp | Đang soạn (ẩn nhãn trạng thái) | Lưu, Gửi duyệt, Xóa |
| Chờ duyệt | Đã gửi, đợi TP/QL | Duyệt phiếu, Từ chối, Trả lại |
| Đã duyệt | TP/QL đã duyệt | (chỉ xem) |
| Bị trả lại | TP/QL trả về để khảo sát lại | Cho sửa lại + Gửi duyệt lại |
| Đã từ chối | TP/QL từ chối (khóa) | Xóa |

Chỉ **Nháp** và **Bị trả lại** mới sửa được nội dung. Riêng dòng bị đánh dấu "Thiếu thông tin"
có thể mở ở chế độ **Bổ sung** để sửa dù phiếu đã gửi.

---

## A. Thông tin tiếp nhận (phần đầu phiếu)

| Trường | Kiểu nhập | Mặc định | Bắt buộc | Nguồn / Giá trị | Người sửa |
|--------|-----------|----------|----------|-----------------|-----------|
| Mã yêu cầu PYC (`pr_code`) | Chọn / nhập | trống | Không | Danh sách PYC | NSPT |
| Ngày tiếp nhận (`received_date`) | Chọn ngày | Hôm nay | Không | — | NSPT |
| Ngày dự kiến trả KQ (`result_due_date`) | Chọn ngày | trống | Không | — | NSPT |
| Phân loại (`item_group`) | Chọn (tìm) | trống | Khi gửi duyệt | Bảng Phân loại | NSPT |
| NSPT phụ trách (`nspt`) | Tự động | Theo người tạo | — | Khóa, không sửa | Hệ thống |
| Yêu cầu kỹ thuật & chất lượng (`requirement_detail`) | Nhập nhiều dòng | trống | Khi gửi duyệt (nếu không tick "đã có mã SP") | — | NSPT |
| Đã có mã SP sẵn (`has_product_code`) | Checkbox | Không tích | Không | — | NSPT |
| Mã VTBB/VL (`item_code`) | Chọn SP | trống | Khi gửi duyệt (nếu tick "đã có mã SP") | Danh mục Sản phẩm | NSPT |
| Số lượng dự kiến mua (`request_qty`) | Nhập số | 0 | Khi gửi duyệt (nếu tick "đã có mã SP") | — | NSPT |
| ĐVT (`uom`) | Chọn (tìm) | trống | Khi gửi duyệt (nếu tick "đã có mã SP") | Bảng Đơn vị tính | NSPT |
| Giá đề xuất (`proposed_rate`) | Nhập số | 0 | Khi gửi duyệt (nếu tick "đã có mã SP") | — | NSPT |

Ghi chú: chọn **Mã VTBB/VL** sẽ tự điền Tên hàng, ĐVT, Phân loại. Chọn **Mã yêu cầu PYC** tự điền một số thông tin từ PYC.

---

## B. Dòng khảo sát Nhà cung cấp (NCC)

Mỗi dòng = một NCC. Trong bảng chỉ hiện cột chính; đầy đủ các trường xem ở popup "Chi tiết dòng".

| Trường | Kiểu nhập | Mặc định | Bắt buộc | Nguồn / Giá trị | Người sửa |
|--------|-----------|----------|----------|-----------------|-----------|
| Ngày liên hệ NCC (`contact_date`) | Chọn ngày | trống | Khi gửi duyệt | — | NSPT |
| Ngày dự kiến NCC phản hồi (`reply_date`) | Chọn ngày | trống | Không | — | NSPT |
| Ngày dự kiến trả KQ (`result_date`) | Chọn ngày | trống | Không | — | NSPT |
| Tên viết tắt NCC (`supplier_code`) | Chọn (tìm) | trống | Không | Bảng Nhà cung cấp | NSPT |
| Tên nhà cung cấp (`supplier_name`) | Nhập tay | trống | Khi gửi duyệt | Tự điền khi chọn NCC | NSPT |
| Mã số thuế (`tax_code`) | Nhập tay | trống | Khi gửi duyệt | Tự điền khi chọn NCC | NSPT |
| Địa chỉ theo giấy ĐK (`reg_address`) | Nhập nhiều dòng | trống | Khi gửi duyệt | Tự điền khi chọn NCC | NSPT |
| Địa chỉ kho của NCC (`warehouse_address`) | Nhập nhiều dòng | trống | Khi gửi duyệt | — | NSPT |
| Link định vị kho (`google_maps`) | Nhập tay | trống | Không | — | NSPT |
| NVKD của NCC (`contact_person`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| SĐT NCC đang làm việc (`contact_phone`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| Nhóm SP/dịch vụ cung ứng (`supply_group`) | Nhập nhiều dòng | trống | Khi gửi duyệt | — | NSPT |
| Link báo giá (`quote_folder`) | Nhập tay | trống | Không | — | NSPT |
| Nguồn thông tin đầu vào (`source_of_information`) | Nhập tay | trống | Không | — | NSPT |
| Công nghệ SX, chủng loại (`production_tech`) | Nhập nhiều dòng | trống | Khi gửi duyệt | — | NSPT |
| Thời gian SX (`production_time`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| Đánh giá tư vấn NVKD (`nvkd_eval`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| Hóa đơn (`invoice_policy`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| Mức độ tin cậy (`reliability`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| Chính sách nhận hàng (`delivery_policy`) | Nhập nhiều dòng | trống | Khi gửi duyệt | — | NSPT |
| Chính sách công nợ (`debt_policy`) | Nhập nhiều dòng | trống | Khi gửi duyệt | — | NSPT |
| Hàng lỗi, hàng trả (`defect_return`) | Nhập nhiều dòng | trống | Không | — | NSPT |
| Nhận xét (NSPT) (`nspt_note`) | Nhập nhiều dòng | trống | Khi gửi duyệt | — | NSPT |
| Ghi chú (`note`) | Nhập nhiều dòng | trống | Không | — | NSPT |
| Duyệt (TP/QL) (`line_approve`) | Chọn | Chờ duyệt | Không | Chờ duyệt / Đã duyệt / Không duyệt / Thiếu thông tin | **TP/QL** |
| Yêu cầu (TP/QL) (`line_approve_note`) | Nhập nhiều dòng | trống | Không | — | **TP/QL** |

---

## C. Dòng khảo sát Sản phẩm (SP)

Mỗi dòng = một sản phẩm/báo giá theo NCC.

| Trường | Kiểu nhập | Mặc định | Bắt buộc | Nguồn / Giá trị | Người sửa |
|--------|-----------|----------|----------|-----------------|-----------|
| Ngày liên hệ (`contact_date`) | Chọn ngày | trống | Khi gửi duyệt | — | NSPT |
| Ngày dự kiến phản hồi (`reply_date`) | Chọn ngày | trống | Không | — | NSPT |
| Ngày dự kiến trả KQ (`result_date`) | Chọn ngày | trống | Không | — | NSPT |
| Tên viết tắt NCC (`supplier_code`) | Chọn (tìm) | trống | Không | Bảng Nhà cung cấp | NSPT |
| Mã SP theo NCC (`internal_code`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| Tên SP (tên NCC đặt) (`product_name`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| Thông số kỹ thuật (`spec`) | Nhập nhiều dòng | trống | Khi gửi duyệt | — | NSPT |
| Xuất xứ sản phẩm (`origin`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| ĐVT báo giá (`quote_unit`) | Chọn (tìm) | trống | Khi gửi duyệt | Bảng Đơn vị tính | NSPT |
| MOQ tối thiểu (`moq`) | Nhập số | 0 | Không | — | NSPT |
| Giá theo sản lượng (`price_by_volume`) | Nhập số | 0 | Không | — | NSPT |
| Khung sản lượng (`volume_range`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| VAT % (`vat`) | Chọn | 0 | Không | 0 / 2 / 4 / 6 / 8 / 10 | NSPT |
| Thành tiền (`amount`) | Tự tính | 0 | — | SL x Giá x (1+VAT) | Hệ thống |
| ĐVT quy đổi về Cty (`internal_unit`) | Chọn (tìm) | trống | Khi gửi duyệt | Bảng Đơn vị tính | NSPT |
| Thành tiền đã quy đổi (`amount_converted`) | Nhập số | 0 | Không | — | NSPT |
| Chi phí vận chuyển (`shipping_cost`) | Nhập số | 0 | Không | — | NSPT |
| Thời gian giao hàng (`delivery_time`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| Địa điểm giao/nhận (`delivery_place`) | Nhập tay | trống | Khi gửi duyệt | — | NSPT |
| Link báo giá (`quote_file`) | Nhập tay | trống | Không | — | NSPT |
| Mẫu sẵn (`sample_ready`) | Checkbox | Không tích | Không | — | NSPT |
| Ngày lấy mẫu (`sample_date`) | Chọn ngày | trống | Khi gửi duyệt (nếu có mẫu) | — | NSPT |
| Số lượng mẫu nhận (`sample_qty`) | Nhập số | 0 | Không | — | NSPT |
| Đánh giá chất lượng LAB (`lab_result`) | Nhập nhiều dòng | trống | Khi gửi duyệt (nếu có mẫu) | — | NSPT |
| Ghi chú LAB (`lab_note`) | Nhập nhiều dòng | trống | Không | — | NSPT |
| Nhận xét NSPT (`nspt_note`) | Nhập nhiều dòng | trống | Khi gửi duyệt | — | NSPT |
| Ghi chú (`note`) | Nhập nhiều dòng | trống | Không | — | NSPT |
| Duyệt (TP/QL) (`line_approve`) | Chọn | Chờ duyệt | Không | Chờ duyệt / Đã duyệt / Không duyệt / Thiếu thông tin | **TP/QL** |
| Ý kiến TP/QL (`line_approve_note`) | Nhập nhiều dòng | trống | Không | — | **TP/QL** |

---

## D. Quy tắc nghiệp vụ

1. **Lưu (nháp)**: giữ mọi dòng có nội dung, kể cả dòng dở dang; chỉ bỏ dòng trống hoàn toàn. Không bắt buộc chọn NCC/Tên SP khi Lưu.
2. **Gửi duyệt**: kiểm tra các trường "Bắt buộc = Khi gửi duyệt". Trường thiếu được tô đỏ nhẹ (ô + trong popup chi tiết), kèm thông báo dòng nào thiếu.
3. **Chọn NCC**: tự điền Tên NCC, MST, Địa chỉ ĐKKD.
4. **Trường số** hiển thị trống khi bằng 0.
5. **Trường duyệt** (`line_approve`, `line_approve_note`) chỉ TP/QL sửa; NSPT chỉ xem. Chọn "Thiếu thông tin" cho phép NSPT mở dòng ở chế độ Bổ sung để sửa dù phiếu đã gửi.
6. **Đính kèm**: mỗi dòng đính kèm file (PDF/ảnh/Excel, tối đa 10MB), lưu trên Cloudflare R2.

## E. Quyền thao tác (RBAC)
| Thao tác | Quyền yêu cầu | Điều kiện trạng thái |
|----------|---------------|----------------------|
| Xem | `survey:read` | mọi trạng thái (theo phạm vi dữ liệu) |
| Tạo / Sửa nội dung | `survey:write` (hoặc `create`) | Nháp / Bị trả lại / tạo mới |
| Gửi duyệt | `survey:write` | Nháp / Bị trả lại |
| Duyệt dòng / Duyệt phiếu / Từ chối / Trả lại | `survey:approve` | Chờ duyệt (duyệt dòng: Nháp/Chờ duyệt/Bị trả lại) |
| Xóa | `survey:delete` | Nháp / Đã từ chối |
