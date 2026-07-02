# Yêu cầu mua (PYC) — chi tiết form item + luồng (plan)

## 1. Đưa VAT (%) và Thời gian cần hàng vào TỪNG DÒNG hàng
- Lý do: mỗi mặt hàng có VAT khác nhau, thời gian cần khác nhau.
- **Model** `tab_purchase_request_item` thêm:
  - `vat` (Numeric(5,2)) — % VAT của dòng
  - `required_date` (String(10)) — thời gian cần hàng/dịch vụ của dòng
- **Tổng tiền** = Σ (qty × giá đề xuất × (1 + vat%/100)). Bỏ VAT ở header (header `vat_rate` giữ để tương thích cũ nhưng không dùng để tính).
- Header bỏ ô "Thời gian cần hàng/dịch vụ" và "VAT (%)" (chuyển xuống item).

## 2. Nút "Mở chi tiết (popup)" + "Copy dòng" cho item (khôi phục)
- Bảng item ngoài chỉ hiện cột chính (Mã, Tên, ĐVT, SL, Giá, Thành tiền, [Phân bổ NSTM nếu có quyền]).
- Mỗi dòng có: **nút mở popup chi tiết** (✎) + **nút copy** (nhân đôi dòng) + nút xóa.
- **Popup chi tiết 1 dòng** (theo hình) gồm:
  - Mã vật tư · **Tên vật tư*** · Phân loại · Mô tả
  - **Số lượng mua*** · Giá đề xuất · ĐVT
  - **Kho nhận*** · Nhân sự phụ trách (chỉ người có quyền duyệt) · Ngày cần hàng · **VAT (%)** · Trạng thái xử lý · Chi tiết tiến độ (text) · Ghi chú khác (text)
- Ràng buộc: **Kho nhận bắt buộc**, Tên vật tư bắt buộc, Số lượng > 0. Ghi chú/Chi tiết tiến độ = textarea.

## 3. Fix auto-điền "Trưởng bộ phận (TBP)/Người liên hệ"
- Hiện tìm theo `position` chứa "trưởng" → dữ liệu thật để ở `role_name` → không ra.
- **Sửa:** khi chọn người yêu cầu → lấy phòng ban mặc định của nhân sự đó → tìm nhân sự cùng phòng có `role_name`/`position` là **Trưởng bộ phận** → tự điền TBP. (Nếu phòng có nhiều, lấy người đầu.)

## 4. NCC đề xuất — nhập tay (bỏ select)
- Người yêu cầu KHÔNG có quyền xem danh sách NCC → **Tên NCC** đổi từ dropdown sang **ô nhập tay**.
- Mã số thuế, Thông tin liên hệ: giữ ô nhập tay. Bỏ phụ thuộc `/api/suppliers`.

## 5. Luồng trạng thái
`Nháp (draft)` → gửi duyệt → `Chờ duyệt (submitted)` → **Trưởng phòng duyệt** → `Đã duyệt (approved)`
→ bắt đầu xử lý → `Đang xử lý (processing)` → hoàn tất → `Hoàn thành (completed)`. (+ `Từ chối (rejected)`).
- Thêm 2 trạng thái mới: `processing`, `completed` + badge.
- **Cần chốt:** ai chuyển "Đang xử lý" và "Hoàn thành"?
  - Đề xuất: **Nhân viên thu mua được giao** bấm "Bắt đầu xử lý" (approved→processing) và "Hoàn thành" (processing→completed). Quản lý/Admin cũng làm được.

## 6. Model/migration
- `PurchaseRequestItem`: + `vat` (Numeric(5,2), default 8), + `required_date` (String(10)).
- Trạng thái PYC: chuỗi, chỉ thêm giá trị mới (không cần cột mới).
- FE: popup item, tính tổng theo item, đổi NCC sang input, fix auto TBP, thêm nút xử lý/hoàn thành theo quyền.

## 7. ĐÃ CHỐT (triển khai)

**VAT:** bỏ hẳn khỏi phiếu yêu cầu (không header, không dòng). Tổng = Σ SL × giá. In không có thuế.

**Trạng thái theo DÒNG** (`line_status`, mặc định "Chưa đặt hàng"):
`Chưa đặt hàng · Đã đặt hàng · Đã gửi ĐMH cho KT · Đã nhận hàng · Hoàn thành · Hủy đơn · Tạm ngưng`.
- Sửa bởi: **nhân sự phụ trách dòng đó** hoặc **admin/quản lý** — trong popup chi tiết dòng.

**Trạng thái PHIẾU tự suy ra** (khi phiếu đã `approved`/`processing`):
- Mọi dòng = "Hoàn thành" → phiếu **Hoàn thành** (tự động).
- Có ≥1 dòng ≠ "Chưa đặt hàng" → phiếu **Đang xử lý**.
- Có ≥1 dòng = "Hủy đơn" → **tô đỏ dòng phiếu trên danh sách** để admin xử lý (thêm cờ `has_cancelled_line`).

**Hành động header:**
- **Duyệt** (Chờ duyệt → Đã duyệt): quyền `approve` (trưởng phòng). Hiển thị "Trưởng phòng đã duyệt".
- **Trả phiếu về** (→ **Nháp**): quyền `cancel` (admin/quản lý). Nhập **lý do**; **reset mọi dòng về "Chưa đặt hàng"** + **xóa nhân sự phụ trách**.
- **Hủy đơn** (→ Hủy): quyền `cancel`. Nhập **lý do** (nếu đang Nháp thì hủy thẳng, không cần lý do).
- **Hoàn thành** (thủ công): quyền `cancel` (admin/quản lý) — ngoài việc tự hoàn thành khi mọi dòng xong.
- → Bỏ `cancel` khỏi vai trò **Trưởng phòng** (chỉ còn duyệt), để Hủy/Trả/Hoàn thành chỉ dành admin/quản lý.

**Trường form dòng:** thêm **Ngày cần hàng** (`required_date`).
**"Mô tả phân loại"** = tự sinh từ Phân loại: "Hàng NCC có sẵn: X ngày; không sẵn: Y ngày" (ẩn phần thiếu). Lấy `std_days` / `std_days_unavail` của ItemGroup.
**NCC đề xuất:** tên NCC = ô nhập tay (bỏ dropdown).
**Auto TBP:** sửa lấy trưởng phòng theo phòng ban của người yêu cầu (dò theo `role_name`/`position`).
