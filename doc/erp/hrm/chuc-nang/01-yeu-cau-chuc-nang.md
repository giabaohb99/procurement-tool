# YÊU CẦU CHỨC NĂNG — NHÂN SỰ (HRM)

| | |
|---|---|
| Bản | 0.2 (13/11/2026: CN-HRM-01 sửa theo hai loại dòng Phòng ban / Công ty — duoc-CR-756) · 0.1 |
| Ngày | 13/11/2026 |
| Người phụ trách | tai-lieu-kiem-thu (Agent 2) |
| Trạng thái | Nháp — mới viết CN-HRM-01 Kiêm nhiệm; các chức năng khác của phân hệ chưa chép về khuôn này, đang nằm ở các tệp chức năng `01`…`06` của thư mục cha (bảng §2 của [`../README.md`](../README.md)) |
| CR liên quan | duoc-CR-755, duoc-CR-756 |

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Nhân sự — Hồ sơ nhân viên (`hr_profile`) | Lập, sửa hồ sơ; khai kiêm nhiệm, quá trình công tác |
| Trưởng phòng / người có phạm vi phòng ban hoặc công ty | Xem hồ sơ người trong phòng / công ty, kể cả người kiêm nhiệm ở phòng / công ty mình (chỉ đọc) |
| Nhân viên | Xem hồ sơ và kiêm nhiệm của chính mình ở Trang cá nhân |

Phần còn lại (nghỉ phép, lịch làm việc, hợp đồng, báo cáo): chưa viết ở tệp này.

## 2. Danh sách chức năng

Mỗi chức năng một mã cố định `CN-HRM-NN` (không tái dùng số khi bỏ). Trạng thái: **Có** (đã lên prod) · **Dev** (mới trên dev) · **Đang làm** · **Chưa** · **Bỏ**.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-HRM-01 | Kiêm nhiệm (tab riêng, hai loại dòng: Phòng ban của công ty hiện tại / cả Công ty khác) | Nhân sự, trưởng phòng, nhân viên | `/hr/employees/:id?tab=concurrent` · cột **Kiêm nhiệm** ở `/hr/employees` · trang chi tiết phòng ban · trang chi tiết công ty · sơ đồ tổ chức · Trang cá nhân | Đang làm (mã xong ở local, chưa lên dev) | duoc-CR-755, duoc-CR-756 |

## 3. Chi tiết từng chức năng

### CN-HRM-01 — Kiêm nhiệm

- **Mục đích:** ghi một người kiêm nhiệm thêm theo quyết định, theo một trong hai loại độc lập — *anh A kiêm nhiệm phòng
  ban A và công ty B; phòng ban thuộc công ty hiện tại*: loại **Phòng ban** (một phòng của công ty hiện tại) hoặc loại
  **Công ty** (cả một công ty khác trong tập đoàn) — và mở phạm vi dữ liệu tương ứng trong thời gian quyết định còn hiệu lực.
- **Luồng chính:** hồ sơ ▸ tab **Kiêm nhiệm** ▸ **Thêm kiêm nhiệm** ▸ chọn **Phòng ban | Công ty** ▸ chọn phòng (chỉ phòng của
  công ty hiện tại) hoặc **Công ty kiêm nhiệm** (trừ công ty hiện tại) ▸ Chức vụ, Từ ngày, Đến ngày, Số QĐ, Ngày QĐ, Tệp QĐ,
  công tắc **Tính vào phạm vi quyền**, Ghi chú ▸ **Lưu**. Sửa dòng không đổi được loại. Ngoài ra: hộp **Giữ phòng cũ làm kiêm
  nhiệm?** khi đổi phòng chính (pháp nhân không đổi), hộp **Kiêm nhiệm khi đổi pháp nhân** (liệt kê dòng sẽ kết thúc + ô **Vẫn
  kiêm nhiệm ở công ty cũ**), Áp dòng quá trình công tác loại Kiêm nhiệm. Xem: cột **Kiêm nhiệm** ở danh sách nhân sự (mục đầu
  + **+N**, rê chuột xem đủ), bảng **Kiêm nhiệm tại phòng này** / **Kiêm nhiệm tại công ty này**, sơ đồ tổ chức.
- **Luật nghiệp vụ:** trạng thái Sắp tới / Đang hiệu lực / Đã hết dẫn xuất theo ngày giờ VN, tự hết hạn; chỉ dòng đang hiệu lực +
  bật công tắc mở phạm vi. Loại Phòng ban cộng phòng đó vào phòng của người này; loại Công ty B tính B như công ty của họ THEO
  BẬC vai trò (bậc Công ty thấy cả B; bậc Phòng ban thấy phòng của họ ở B; bậc Cá nhân, Toàn hệ thống, phòng xử lý thu mua
  không đổi). Không trùng phòng chính / công ty chính; không chồng giai đoạn cùng phòng / cùng công ty; hồ sơ chưa gắn pháp
  nhân chính không khai được; tối đa 30 dòng / người; chức vụ kiêm nhiệm không cấp vai trò; báo cáo chỉ đếm ở vị trí chính.
  Đủ các quyết định Q1–Q6 và M1–M5 ở [`../01-ho-so-nhan-su.md` §7.18](../01-ho-so-nhan-su.md).
- **Dữ liệu:** bảng `tab_employee_concurrent` (cột `kind` 1 Phòng ban / 2 Công ty); Loại, nơi kiêm nhiệm theo loại, Từ ngày bắt
  buộc; công tắc mặc định bật.
- **Quyền:** `employee.read` (xem tab, cột danh sách, bảng ở trang phòng ban / công ty) · `employee.write` đúng phạm vi hồ sơ +
  phạm vi ghi phủ nơi kiêm nhiệm (loại Phòng ban: phủ phòng đó ở công ty hiện tại; loại Công ty: quyền ghi toàn công ty B) ·
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
