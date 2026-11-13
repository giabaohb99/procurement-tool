# YÊU CẦU CHỨC NĂNG — NHÂN SỰ (HRM)

| | |
|---|---|
| Bản | 0.4 (13/11/2026: thêm CN-HRM-04 Trưởng phòng gán lịch riêng cho nhân viên; CN-HRM-03 thêm Trưởng phòng tra phép nhân viên phòng mình — duoc-CR-757 lượt 2) · 0.3 (13/11/2026: thêm CN-HRM-02 Lịch làm việc của phòng ban, CN-HRM-03 Trợ lý AI tra lịch làm việc và ngày nghỉ — duoc-CR-757) · 0.2 (13/11/2026: CN-HRM-01 sửa theo hai loại dòng Phòng ban / Công ty — duoc-CR-756) · 0.1 |
| Ngày | 13/11/2026 |
| Người phụ trách | tai-lieu-kiem-thu (Agent 2) |
| Trạng thái | Nháp — mới viết CN-HRM-01 Kiêm nhiệm, CN-HRM-02 … CN-HRM-04; các chức năng khác của phân hệ chưa chép về khuôn này, đang nằm ở các tệp chức năng `01`…`06` của thư mục cha (bảng §2 của [`../README.md`](../README.md)) |
| CR liên quan | duoc-CR-755, duoc-CR-756, duoc-CR-757 |

## 1. Người dùng và vai trò

| Vai trò (mã vai trò) | Làm gì trong phân hệ |
|---|---|
| Nhân sự — Hồ sơ nhân viên (`hr_profile`) | Lập, sửa hồ sơ; khai kiêm nhiệm, quá trình công tác |
| Trưởng phòng / người có phạm vi phòng ban hoặc công ty | Xem hồ sơ người trong phòng / công ty, kể cả người kiêm nhiệm ở phòng / công ty mình (chỉ đọc); Trưởng phòng (`dept_head`) gán lịch làm việc riêng cho nhân viên phòng mình và xem quỹ phép của họ |
| Nhân sự — Nghỉ phép (`hr_leave`) | Gán mẫu lịch làm việc cho phòng ban / pháp nhân / nhân sự; hỏi trợ lý AI quỹ phép và ngày đã nghỉ của nhân sự trong phạm vi |
| Nhân viên | Xem hồ sơ và kiêm nhiệm của chính mình ở Trang cá nhân; hỏi trợ lý AI lịch làm việc và số ngày đã nghỉ của chính mình |

Phần còn lại (nghỉ phép, phần lịch làm việc có từ duoc-CR-589, hợp đồng, báo cáo): chưa viết ở tệp này.

## 2. Danh sách chức năng

Mỗi chức năng một mã cố định `CN-HRM-NN` (không tái dùng số khi bỏ). Trạng thái: **Có** (đã lên prod) · **Dev** (mới trên dev) · **Đang làm** · **Chưa** · **Bỏ**.

| Mã | Chức năng | Ai dùng | Màn / nơi dùng | Trạng thái | CR |
|---|---|---|---|---|---|
| CN-HRM-01 | Kiêm nhiệm (tab riêng, hai loại dòng: Phòng ban của công ty hiện tại / cả Công ty khác) | Nhân sự, trưởng phòng, nhân viên | `/hr/employees/:id?tab=concurrent` · cột **Kiêm nhiệm** ở `/hr/employees` · trang chi tiết phòng ban · trang chi tiết công ty · sơ đồ tổ chức · Trang cá nhân | Đang làm (mã xong ở local, chưa lên dev) | duoc-CR-755, duoc-CR-756 |
| CN-HRM-02 | Lịch làm việc của phòng ban (xem lịch đang áp + nguồn kế thừa, gán lịch riêng cho phòng) | Nhân sự, trưởng phòng, ai xem được phòng ban | `/hr/departments/:id?tab=work-schedule` · hộp **Thêm dòng gán lịch** điền sẵn ở `/hr/work-schedule-assignments` | Đang làm (mã xong ở local, chưa lên dev) | duoc-CR-757 (nền duoc-CR-589) |
| CN-HRM-03 | Trợ lý AI / cổng MCP tra lịch làm việc, quỹ phép và số ngày đã nghỉ (của mình; của nhân sự khác theo quyền) | Mọi nhân viên; Nhân sự, Trưởng phòng (người phòng mình) | Trợ lý web, bot Telegram, cổng MCP (`my_leave_summary`, `employee_leave_summary`) | Đang làm (mã xong ở local, chưa lên dev) | duoc-CR-757 |
| CN-HRM-04 | Trưởng phòng gán lịch làm việc riêng cho nhân viên phòng mình | Trưởng phòng | Nút **Đổi lịch riêng** ở khung Lịch làm việc của hồ sơ · *Nhân sự ▸ Thiết lập* ▸ tab **Gán lịch** | Đang làm (mã xong ở local, chưa lên dev) | duoc-CR-757 lượt 2 |

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

### CN-HRM-02 — Lịch làm việc của phòng ban

- **Mục đích:** nhìn ở trang phòng ban là biết phòng đang theo lịch nào, lịch đó lấy từ đâu (gán riêng cho phòng / theo pháp
  nhân / theo toàn hệ thống / mặc định), và gán lịch riêng cho phòng không phải đi tìm màn khác. Ngày nghỉ phép của nhân sự
  trong phòng được đếm theo lịch này (trừ người có lịch gán riêng).
- **Luồng chính:** *Nhân sự ▸ Danh mục ▸ Phòng ban* ▸ bấm một phòng ▸ tab **Lịch làm việc** ▸ xem tên mẫu + câu nguồn, lưới
  bảy ngày, số ngày công/tuần, danh sách **Gán lịch riêng cho phòng** ▸ bấm **Gán lịch cho phòng** ▸ hộp **Thêm dòng gán
  lịch** mở sẵn với **Cấp áp dụng** = Phòng ban, **Đối tượng áp dụng** = phòng này ▸ chọn **Mẫu lịch**, **Hiệu lực từ ngày**,
  (tùy chọn) **Đến ngày**, **Ghi chú** ▸ **Tạo mới**. Cách khác: *Nhân sự ▸ Thiết lập* ▸ tab **Gán lịch** ▸ **Thêm dòng gán
  lịch** và tự chọn cấp + phòng.
- **Luật nghiệp vụ:** hẹp thắng rộng — Nhân sự > Phòng ban > Pháp nhân > Toàn hệ thống; chưa ai gán thì dùng lịch mặc định
  T2–T7 08:00–17:00, Chủ nhật nghỉ. Phòng dùng chung (không thuộc pháp nhân nào) không kế thừa lịch pháp nhân. Luật chồng
  ngày và tự đóng / nối lại dòng cũ như §5.1 của [`../03-lich-lam-viec.md`](../03-lich-lam-viec.md). Đơn nghỉ đã gửi duyệt
  giữ số ngày lúc gửi, đổi lịch sau không đổi đơn cũ.
- **Dữ liệu:** không thêm bảng; đọc `tab_work_schedule_assignment` (cấp 3 = phòng ban) và mẫu lịch.
- **Quyền:** xem tab = `department.read` + phạm vi phòng ban (không đòi `work_schedule.read`); nút **Gán lịch cho phòng** cần
  `work_schedule.create`; nút **Xem gán lịch** cần `work_schedule.read`.
- **Ngoại lệ / lỗi người dùng gặp:** phòng ngoài phạm vi → tab báo *Không xem được lịch làm việc của phòng ban này.*; gán
  chồng ngày → câu báo lỗi của màn Gán lịch (§5.1 của `03-lich-lam-viec.md`).
- **Liên quan:** [`../03-lich-lam-viec.md` §19](../03-lich-lam-viec.md), đường `GET /api/work-schedules/tools/effective-department`
  ([`../tai-lieu-ky-thuat/api.md`](../tai-lieu-ky-thuat/api.md)). Bài HDSD: *Nhân sự — Lịch làm việc của phòng ban và cách
  đếm ngày nghỉ*.

### CN-HRM-03 — Trợ lý AI tra lịch làm việc và ngày nghỉ

- **Mục đích:** trả lời qua chat / MCP các câu *lịch làm việc của tôi thế nào*, *tôi đã nghỉ mấy ngày*, *anh X / phòng Y còn
  bao nhiêu ngày phép*.
- **Luồng chính:** người dùng hỏi trợ lý ▸ trợ lý gọi `my_leave_summary` (câu hỏi về chính mình) hoặc `employee_leave_summary`
  (về người khác, theo mã / tên hoặc theo phòng) ▸ trả lời bằng số của hệ thống kèm link màn Nghỉ phép / Quỹ phép năm.
- **Luật nghiệp vụ:** *đã nghỉ* = tổng ngày của đơn ĐÃ DUYỆT có ngày bắt đầu từ hôm nay trở về trước, theo từng loại, gồm cả
  loại không trừ quỹ (không lương, ốm…); đơn đã duyệt cho ngày sắp tới và đơn chờ duyệt nói riêng, không cộng vào; cả đơn tính
  vào năm của ngày bắt đầu nghỉ (như quỹ phép — đơn vắt hai năm có thể lệch báo cáo Tình hình nghỉ phép). Số còn lại là số của màn Quỹ phép (đã trừ ngày giữ
  chỗ và phần chưa tới tháng của loại cộng dần). Lịch làm việc là lịch đang áp hôm nay. Chỉ đọc, không tự cấp dòng quỹ.
- **Dữ liệu:** không thêm bảng; đọc đơn nghỉ + dòng loại nghỉ, quỹ phép, gán lịch.
- **Quyền:** về chính mình — cần `leave_request.read` như trước; về người khác — cần `leave_balance.read`, chỉ thấy người nằm
  trong CẢ phạm vi xem hồ sơ nhân sự LẪN phạm vi xem Quỹ phép (đúng như màn Quỹ phép năm; bậc Phòng ban của Quỹ phép từ lượt 2
  là đúng người thuộc phòng mình, không còn là cả công ty — Trưởng phòng được seed bậc đó); số ngày đã nghỉ của họ chỉ hiện khi
  người hỏi còn xem được đơn nghỉ của họ (`leave_request.read` đúng phạm vi). Không trả lương, không trường nhạy cảm.
- **Ngoại lệ / lỗi người dùng gặp:** không có ai khớp trong phạm vi → *Không tìm thấy nhân sự nào khớp trong phạm vi bạn được
  xem.*; thiếu quyền Quỹ phép → trợ lý nói rõ thiếu quyền; quá 20 người (mặc định) → trả 20 người đầu kèm câu nhắc thu hẹp.
- **Liên quan:** [`../03-lich-lam-viec.md` §19.3](../03-lich-lam-viec.md), [`../02-nghi-phep.md` §17](../02-nghi-phep.md), cẩm
  nang trợ lý `40-nghi-phep`. Bài HDSD: *Nhân sự — Lịch làm việc của phòng ban và cách đếm ngày nghỉ* (mục hỏi trợ lý AI).

### CN-HRM-04 — Trưởng phòng gán lịch riêng cho nhân viên

- **Mục đích:** Trưởng phòng tự đổi lịch làm việc cho một nhân viên phòng mình (ví dụ chuyển sang làm thứ Bảy, làm ca riêng)
  mà không phải nhờ Nhân sự, và không được quyền sửa mẫu lịch hay lịch của cả phòng / công ty.
- **Luồng chính:** hồ sơ nhân viên ▸ tab **Quỹ phép** ▸ khung **Lịch làm việc** ▸ **Đổi lịch riêng** ▸ hộp **Thêm dòng gán
  lịch** đã chọn sẵn cấp Nhân sự + người đó ▸ chọn **Mẫu lịch**, **Hiệu lực từ ngày** (từ hôm nay), **Đến ngày** (tùy chọn) ▸
  **Tạo mới**. Cách khác: *Nhân sự ▸ Thiết lập* ▸ tab **Gán lịch** ▸ **Thêm dòng gán lịch** ▸ chọn người trong ô **Đối tượng
  áp dụng** (chỉ liệt kê người gán được).
- **Luật nghiệp vụ:** chín luật ở [`../03-lich-lam-viec.md` §20.2](../03-lich-lam-viec.md): chỉ cấp Nhân sự; chỉ người trong
  phạm vi, không phải chính mình; chỉ mẫu đang dùng; không sửa mẫu; chỉ sửa / xóa dòng tự gán; ngày hiệu lực từ hôm nay;
  dòng đã bắt đầu chỉ đặt được ngày kết thúc (từ hôm qua) và không xóa; dòng đã thay lịch trước đó không đổi người / ngày bắt
  đầu. Đặt ngày kết thúc cho lịch tạm thì lịch cũ (kể cả lịch Nhân sự gán) tự nối lại từ hôm sau.
- **Dữ liệu:** không thêm bảng; dòng `tab_work_schedule_assignment` cấp 4, `created_by` = Trưởng phòng.
- **Quyền:** khóa mới `work_schedule_personal` (`create` / `write` / `delete`), bậc Phòng ban, đo trên hồ sơ nhân sự đích; ô
  Phòng ban được xem cộng thêm phòng nhưng không sang công ty khác. Người có khóa Nhân sự `work_schedule` đi đường cũ.
- **Ngoại lệ / lỗi người dùng gặp:** bảng mục 3 của [`../tai-lieu-ky-thuat/api.md`](../tai-lieu-ky-thuat/api.md).
- **Liên quan:** CN-HRM-02, `doc/tai-lieu-ky-thuat/phan-quyen/thiet-ke-phan-quyen.md` §4d. Bài HDSD: *Nhân sự — Lịch làm việc
  của phòng ban và cách đếm ngày nghỉ* (mục Trưởng phòng đổi lịch riêng). Hệ đang chạy phải tick tay — `03-lich-lam-viec.md` §21.

## 4. Luồng trạng thái chứng từ (nếu có)

Không áp dụng cho kiêm nhiệm: trạng thái tính từ ngày, không có duyệt. CN-HRM-02 và CN-HRM-03 không có chứng từ riêng.

## 5. Câu hỏi còn mở

| # | Câu hỏi | Ai trả lời | Hạn |
|---|---|---|---|
| 1 | `GET /api/employees/{eid}` có bịt theo phạm vi (khi đó Q1 mới áp cho đường chi tiết) không? | Người chủ | Chưa hẹn |
| 2 | Có làm loại trừ đích danh nhân sự có hiệu lực cho entity `employee` không? | Người chủ | Chưa hẹn |
| 3 | Báo cáo Điều chuyển & bổ nhiệm có đếm thêm dòng của tab Kiêm nhiệm không? | Người chủ | Chưa hẹn |
