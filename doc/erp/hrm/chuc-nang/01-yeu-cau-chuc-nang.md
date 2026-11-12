# YÊU CẦU CHỨC NĂNG — NHÂN SỰ (HRM)

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 12/11/2026 |
| Người phụ trách | tai-lieu-kiem-thu (Agent 2) |
| Trạng thái | Nháp — mới viết CN-HRM-01 Kiêm nhiệm; các chức năng khác của phân hệ chưa chép về khuôn này, đang nằm ở các tệp chức năng `01`…`06` của thư mục cha (bảng §2 của [`../README.md`](../README.md)) |
| CR liên quan | duoc-CR-755 |

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Nhân sự — Hồ sơ nhân viên (`hr_profile`) | Lập, sửa hồ sơ; khai kiêm nhiệm, quá trình công tác |
| Trưởng phòng / người có phạm vi phòng ban | Xem hồ sơ người trong phòng, kể cả người kiêm nhiệm ở phòng mình (chỉ đọc) |
| Nhân viên | Xem hồ sơ và kiêm nhiệm của chính mình ở Trang cá nhân |

Phần còn lại (nghỉ phép, lịch làm việc, hợp đồng, báo cáo): chưa viết ở tệp này.

## 2. Danh sách chức năng

Mỗi chức năng một mã cố định `CN-HRM-NN` (không tái dùng số khi bỏ). Trạng thái: **Có** (đã lên prod) · **Dev** (mới trên dev) · **Đang làm** · **Chưa** · **Bỏ**.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-HRM-01 | Kiêm nhiệm (tab riêng, kiêm nhiệm được ở công ty khác) | Nhân sự, trưởng phòng, nhân viên | `/hr/employees/:id?tab=concurrent` · trang chi tiết phòng ban · sơ đồ tổ chức · Trang cá nhân | Đang làm (mã xong ở local, chưa lên dev) | duoc-CR-755 |

## 3. Chi tiết từng chức năng

### CN-HRM-01 — Kiêm nhiệm

- **Mục đích:** ghi một người kiêm nhiệm thêm một phòng (ở công ty mình hay công ty khác) theo quyết định, và mở phạm vi dữ liệu
  đúng phòng đó ở đúng công ty đó trong thời gian quyết định còn hiệu lực.
- **Luồng chính:** hồ sơ ▸ tab **Kiêm nhiệm** ▸ **Thêm kiêm nhiệm** ▸ chọn Công ty, Phòng ban, Chức vụ, Từ ngày, Đến ngày, Số QĐ,
  Ngày QĐ, Ghi chú, công tắc **Tính vào phạm vi quyền**, tệp QĐ ▸ **Lưu**. Ngoài ra: hộp **Giữ phòng cũ làm kiêm nhiệm?** khi đổi
  phòng chính, hộp **Kiêm nhiệm ở công ty cũ** khi đổi pháp nhân, Áp dòng quá trình công tác loại Kiêm nhiệm.
- **Luật nghiệp vụ:** trạng thái Sắp tới / Đang hiệu lực / Đã hết dẫn xuất theo ngày giờ VN, tự hết hạn; chỉ dòng đang hiệu lực +
  bật công tắc mở phạm vi, theo CẶP (phòng, công ty); không trùng phòng chính; không chồng giai đoạn cùng cặp; tối đa 30 dòng /
  người; chức vụ kiêm nhiệm không cấp vai trò; báo cáo chỉ đếm ở vị trí chính. Đủ sáu quyết định Q1–Q6 ở
  [`../01-ho-so-nhan-su.md` §7.18](../01-ho-so-nhan-su.md).
- **Dữ liệu:** bảng `tab_employee_concurrent`; Công ty, Phòng ban, Từ ngày bắt buộc; công tắc mặc định bật.
- **Quyền:** `employee.read` (xem tab) · `employee.write` đúng phạm vi hồ sơ + phạm vi ghi phủ cặp đích (thêm / sửa / xóa) ·
  `employee_sensitive.read` (tệp QĐ của người khác). Không ai tự sửa kiêm nhiệm của chính mình, kể cả quản trị.
- **Ngoại lệ / lỗi người dùng gặp:** bảng mục 3 của [`../tai-lieu-ky-thuat/api.md`](../tai-lieu-ky-thuat/api.md).
- **Liên quan:** quá trình công tác (`01-ho-so-nhan-su.md` §7.11), sơ đồ tổ chức (§7.12), nhập Excel nhân sự, công cụ MCP
  `employee_lookup` (trả `concurrent_roles`). Bài HDSD: *Nhân sự — Khai kiêm nhiệm (kể cả ở công ty khác)*.

## 4. Luồng trạng thái chứng từ (nếu có)

Không áp dụng cho kiêm nhiệm: trạng thái tính từ ngày, không có duyệt.

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | `GET /api/employees/{eid}` có bịt theo phạm vi (khi đó Q1 mới áp cho đường chi tiết) không? | Người chủ | Chưa hẹn |
| 2 | Có làm loại trừ đích danh nhân sự có hiệu lực cho entity `employee` không? | Người chủ | Chưa hẹn |
| 3 | Báo cáo Điều chuyển & bổ nhiệm có đếm thêm dòng của tab Kiêm nhiệm không? | Người chủ | Chưa hẹn |
