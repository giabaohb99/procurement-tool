# Lịch làm việc — phân hệ Nhân sự

| | |
|---|---|
| Bản | 1.2 — 13/11/2026 (duoc-CR-757 lượt 2: **Trưởng phòng gán lịch riêng** cho nhân viên — khóa `work_schedule_personal`, §20 mới; sổ việc trước khi deploy §21 mới; §3 · §10 · §11 sửa) · 1.1 — 13/11/2026 (duoc-CR-757: tab **Lịch làm việc** ở trang phòng ban, đường `/tools/effective-department`, trợ lý AI đọc lịch làm việc và ngày đã nghỉ — §19 mới; §3 · §5 · §11 · §13 · §15 sửa, §5 sửa mã cấp cho khớp `WorkScheduleLevel`) · 1.0 — 05/10/2026 (duoc-CR-589) |
| Ngày | 13/11/2026 |
| Người phụ trách | Anh Được |
| Trạng thái | Hiệu lực |
| CR | **duoc-CR-589** · **duoc-CR-757** |
| Giao diện | **chỉ có trên `frontend-v2/`** (cổng 8083), menu *Nhân sự ▸ Lịch làm việc* |
| Kế hoạch gốc | `plans/261005-0925-hr-lich-lam-viec/plan.md` · CR-757: [`plans/261113-lich-lam-viec-phong-ban-tro-ly-tra-phep-duoc-cr-757/plan.md`](plans/261113-lich-lam-viec-phong-ban-tro-ly-tra-phep-duoc-cr-757/plan.md) |
| Bài Help Center | `backend/scripts/seed_help_nhan_su.py` — bài **Nhân sự — Lịch làm việc của phòng ban và cách đếm ngày nghỉ** (duoc-CR-757) |
| Nguồn nghiệp vụ | `doc/erp/tham-khao-hrm/01-nhan-su.md` · [`02-nghi-phep.md`](02-nghi-phep.md) |

---

## 1. Chức năng này để làm gì

Quản lý lịch làm việc hàng tuần: một mẫu lịch 7 ngày với loại từng ngày (cả ngày / nửa ngày sáng / nửa ngày chiều / nghỉ) và giờ làm. Mẫu được gán theo **bốn cấp độ** (từ hẹp đến rộng): nhân sự riêng → phòng ban → pháp nhân → hệ thống, **người duyệt đơn nghỉ phép dùng lịch của chính người** để tính ngày công thay cho cứng `WEEKEND_DAYS = (6,)` cũ.

**Vì sao không màn riêng " Lịch làm việc" dạng lưới xem-ai-làm-ai-nghỉ ở đây.** Đó là màn [**Xem lịch**](#9-xem-lịch--màn-lịch-làm-việc-dạng-lịch) (§9 dưới), màn hiển thị dữ liệu từ bốn nguồn:
- Mẫu lịch của mỗi người.
- Đơn nghỉ phép của mỗi người (đã duyệt + chờ duyệt).
- Lịch ngày lễ (chung công ty + riêng pháp nhân).
- Nửa buổi nếu đơn khai nửa buổi.

---

## 2. Năm khái niệm — không lẫn

| Thứ | Bảng | Là gì |
|---|---|---|
| **Mẫu lịch tuần** | `tab_work_schedule` | Khuôn lịch chuẩn: bảy dòng, mỗi dòng một thứ. **Một mẫu tái dùng cho nhiều người.** |
| **Dòng lịch** | `tab_work_schedule_day` | Một thứ trong mẫu: thứ mấy · loại ngày · giờ bắt đầu/kết thúc/giờ trưa. |
| **Gán lịch** | `tab_work_schedule_assignment` | Gán mẫu A cho (người/phòng/pháp nhân/hệ thống) B từ ngày T1 đến T2 — **có giá trị ngân hạng**. |
| **Loại ngày** | `WorkDayKind` (bộ mã) | OFF / FULL / MORNING / AFTERNOON — quy tắc `(0,) / (8h) / (4h sáng) / (4h chiều)`. |
| **Hiệu lực lịch** | `effective_from` / `effective_to` | Gán từ ngày này đến ngày kia. Từ ngày = **bắt buộc**; đến ngày = **NULL nếu không thời hạn**. |

---

## 3. Màn hình

| Màn | Đường dẫn | Khóa quyền | Vai trò |
|---|---|---|---|
| Mẫu lịch (danh sách + chi tiết + thêm) | `/hr/work-schedules` | `work_schedule.read` / `.create` / `.write` / `.delete` | HR + sửa lịch |
| Gán lịch (danh sách + chi tiết + thêm) | `/hr/work-schedule-assignments` | `work_schedule.read` / `.create` / `.write` / `.delete` | HR + sửa lịch |
| Xem lịch (tuần / tháng, nhân sự × ngày) | `/hr/work-roster` | `employee.read` (hàng), `leave_request.read` (lớp nghỉ phép) | mọi người, xem riêng |
| Thẻ lịch trên hồ sơ | Khung **Lịch làm việc** trong tab **Quỹ phép** của `/hr/employees/:id` (`?tab=leave`) | `employee.read` | xem cùng nhân sự |
| Gán lịch RIÊNG cho nhân viên phòng mình (duoc-CR-757 lượt 2) | Nút **Đổi lịch riêng** ở khung Lịch làm việc của hồ sơ → `/hr/work-schedule-assignments` (hộp Thêm điền sẵn) | `work_schedule_personal.create` / `.write` / `.delete` (Trưởng phòng, bậc Phòng ban) | Trưởng phòng — xem §20 |
| Tab **Lịch làm việc** của phòng ban (duoc-CR-757) | `/hr/departments/:id?tab=work-schedule` | `department.read` (xem); nút **Gán lịch cho phòng** cần `work_schedule.create`, nút **Xem gán lịch** cần `work_schedule.read` | ai xem được phòng ban — xem §19 |

Đường menu (duoc-CR-754): **Mẫu lịch tuần** và **Gán lịch** là hai tab của *Nhân sự ▸ Thiết lập*; *Nhân sự ▸ Lịch làm việc* mở màn Xem lịch; trang phòng ban mở từ *Nhân sự ▸ Danh mục ▸ Phòng ban*.

**Quyền sửa** (`work_schedule.write` / `.create` / `.delete`): chỉ **`admin` · `hr_leave` · `hr_profile`**. Riêng việc gán lịch RIÊNG cấp Nhân sự có khóa thứ hai `work_schedule_personal` cho Trưởng phòng (`dept_head`), giới hạn ở §20. Mọi vai trò khác chỉ `read` (cho form nghỉ phép đọc lịch tính số ngày). Trên hệ **đang chạy** (prod/dev-UAT), vai trò cũ **không tự có** khóa `work_schedule` — seed không ghi đè — phải thêm ở màn Phân quyền tài khoản, hoặc `SEED_FORCE_SYNC=true` một lần rồi khởi động lại API.

Dựng bằng **khung CRUD khai báo** (`shared/crud/CrudListPage` + `CrudDetailPage`) kèm `FieldDescriptor` mục đích chung — chỉ máy tính + phút + giây trong các ô giờ, thay cho **datetime picker đầy đủ**.

---

## 4. Mẫu lịch tuần — mỗi trường

| Ô | Cột | Kiểu | Mặc định | Bắt buộc | Ghi chú |
|---|---|---|---|---|---|
| **Tên mẫu** | `name` | chữ | — | Có | ⚠️ **KHÓA sau khi tạo** — tên này đi vào báo cáo / lịch làm việc. Phải duy nhất |
| **Sảy dòng tuần** | | | | | Bảy ô ghép (M–C–T–N–T–S–CN = 0–6). Mỗi dòng là một `WorkScheduleDay` |
| Thứ _[ngày từ 0–6]_ | `weekday` | không chỉnh | — | Có | 0 = Thứ Hai … 6 = Chủ Nhật |
| Loại ngày | `day_kind` | chọn | FULL (cả ngày) | Có | OFF / FULL / MORNING / AFTERNOON (dùng bộ mã `WorkDayKind`) |
| Từ giờ | `start_time` | giờ:phút | 08:00 | Khi FULL/MORNING/AFTERNOON | Bắt buộc nếu loại ngày không phải OFF |
| Đến giờ | `end_time` | giờ:phút | 17:00 | Khi FULL/MORNING/AFTERNOON | Bắt buộc nếu loại ngày không phải OFF |
| Giờ trưa bắt đầu | `lunch_start` | giờ:phút | 12:00 | Tùy chọn | Để tính công nửa buổi (nếu đơn nghỉ khai nửa buổi) |
| Giờ trưa kết thúc | `lunch_end` | giờ:phút | 13:00 | Tùy chọn | |
| **Ghi chú** | `note` | nhiều dòng | rỗng | Không | Liên lạc ngoài hệ (phong cách làm việc) |
| **Đang dùng** | `is_active` | công tắc | Bật | Không | Tắt = ẩn khỏi ô chọn; gán cũ vẫn có hiệu lực |

Hàng M–C–T mặc định 08:00–17:00. Hàng T–S bất kỳ (thường 08:00–17:00 hoặc 08:00–12:00). Hàng CN luôn OFF.

**Bảy ô lịch viết thành CẢ MỘT custom field** (kiểu `type: 'custom'` của CRUD), dựng `WorkScheduleWeekEditor` tự vẽ 7 hàng 4 cột (loại · từ · đến · giờ trưa), không viết bảy ô riêng lẻ.

---

## 5. Gán lịch — mỗi trường

| Ô | Cột | Kiểu | Mặc định | Bắt buộc | Ghi chú |
|---|---|---|---|---|---|
| **Cấp áp dụng** | `target_level` | chọn | — | Có | Mã `WorkScheduleLevel`: **1** Toàn hệ thống · **2** Pháp nhân · **3** Phòng ban · **4** Nhân sự. Số `0` không hợp lệ (quy ước *chưa khai*); `level = 0` chỉ xuất hiện ở kết quả *lịch hiệu lực* khi `is_fallback = true`. Thứ tự hẹp thắng rộng là `LEVEL_PRECEDENCE`, KHÔNG suy từ độ lớn của số |
| **Đối tượng áp dụng** | `target_id` | chọn (thay đổi theo cấp) | — | Có (trừ Toàn hệ thống) | Danh sách pháp nhân / phòng ban / nhân sự tùy cấp; cấp Toàn hệ thống để `0` |
| **Mẫu lịch** | `schedule_id` | chọn (nạp từ API) | — | Có | Danh sách mẫu đang dùng (`is_active = true`) |
| **Hiệu lực từ ngày** | `effective_from` | chọn ngày | — | Có | Ngày gán có hiệu lực |
| Đến ngày | `effective_to` | chọn ngày | — | Không | NULL = không thời hạn (cứ dùng tới khi thay bằng gán khác) |
| **Ghi chú** | `note` | nhiều dòng | rỗng | Không | Lý do thay đổi lịch (dùng nội bộ) |

### 5.1. Luật cấm chồng (tính trên `target_level + target_id + effective_from`)

**Cùng đối tượng không được có hai gán bắt đầu cùng một ngày** — được kiểm bằng **UNIQUE constraint** ở DB. **Ngoài lệ tự động** (ngày 05/10/2026 chốt):

Nếu **tạo gán mới** và **đối tượng đã có dòng " không thời hạn"** (xảy ra ngày T, nhỏ hơn ngày gán mới):
- Backend tự **đóng dòng cũ** ở ngày `from_mới − 1`, tự ghi audit, tất cả trong **một transaction**.
- Nếu gán mới **có thời hạn** (đến ngày D ≠ NULL):
  - Gán cũ được **nối lại** (mở thêm dòng) từ `D + 1`, ngầm hiểu đó là lịch tạm (ngoài gán chính).
  - Nếu xóa gán tạm này → gán chính quay lại (reset `effective_to = NULL`), nhìn thấy ngay khi tải lại.
- Nếu gán mới **không thời hạn** → gán cũ **hết hiệu lực vĩnh viễn**.

**Mọi chồng khác** (cùng cấp, cùng đối tượng, nhưng ngày bắt đầu khác, hay khác cấp): **chặn + báo 400**, nêu tên dòng trùng rõ ràng.

### 5.2. Đổi mục đích gán giữa nhập liệu (ô cấp độ / gán cho)

Nếu người dùng chọn **Phòng ban** rồi xổ danh sách phòng, sau đó **đổi lại thành "Nhân sự"**, ô **Gán cho** tự xóa (giữ nguyên dòng, chỉ trả ô về trống). Backend kiểm toàn bộ ở `assignment_controller` khi nhận **POST / PATCH** — nếu cấp độ và đối tượng **không khớp** (ví dụ: cấp EMPLOYEE nhưng `target_id` là id của phòng), trả lỗi 400.

---

## 6. Mẫu seed sẵn

`backend/migrations/versions/wsched01_lich_lam_viec.py` — **một mẫu duy nhất** tạo lúc migration:

| Mẫu | Mô tả | CN | T2–T7 | T6 |
|---|---|---|---|---|
| **Hành chính T2–T7** | Mẫu chuẩn | OFF | FULL 08–17 (trưa 12–13) | FULL 08–17 |

**Không gán cho ai** — xem là tham chiếu và ghi chú khi thêm mẫu khác. Nếu xóa nó từ giao diện, **không tự hồi sinh** (seed chạy lần đầu ở migration, không hằng ngày).

---

## 7. Tính ngày công, khớp với loại ngày

**Ngày công = số ngày × hệ số**, áp quy tắc của loại ngày trên **lịch hiệu lực của người nghỉ**:

| Loại ngày | Công | Cách tính |
|---|---|---|
| OFF | 0 | Không làm, không trừ phép |
| FULL | 1.0 | Cả ngày, trừ 1 ngày |
| MORNING | 0.5 | Nửa buổi sáng, trừ 0.5 ngày |
| AFTERNOON | 0.5 | Nửa buổi chiều, trừ 0.5 ngày |

**Nửa buổi xác định bằng mốc giờ trưa** (`lunch_start`), không phải theo từng buổi của cả ngày:
- Từ `lunch_start` đến `end_time` = buổi chiều.
- Từ `start_time` đến `lunch_start` = buổi sáng.

**Một người nghỉ một khoảng ngày** → nhìn vào **lịch của người đó** từng ngày, tra loại ngày đó, cộng hệ số. Lấy từ `resolver.load_day_plans(employee, from_date, to_date)` — xem §12 dưới.

---

## 8. Sửa mẫu đang dùng — ảnh hưởng gì

### Ảnh hưởng lên **đơn nghỉ phép đã lưu**

⚠️ **Cột `total_days` (tổng số ngày) của đơn LƯU cứng lúc lưu** — sửa mẫu sau đó **không đổi** đơn cũ. Luật: *tờ đơn nhìn lịch ngày mình gửi duyệt (hoặc lưu nháp), sau đó sửa lịch không ảnh hưởng tới số ngày của tờ đơn rồi*.

- Đơn **chưa gửi duyệt** (nháp) — **mở lại được gợi ý theo lịch mới**, người dùng thấy số ngày khác và có cơ hội sửa. Máy chủ vẫn chấp nhận nếu cập nhật dòng loại nghỉ kèm số ngày mới (`tab_leave_request_line`).
- Đơn **đã gửi duyệt / đã duyệt** → lịch, số ngày, loại nghỉ ghi vào `tab_document.metadata` ở **hình chụp lúc duyệt** (không bao giờ đổi). Báo cáo / tính quỹ phép / màn xem lịch dùng `metadata` đó.

Khi sửa mẫu, **hộp thoại cảnh báo** (chỉ frontend): *Mẫu này đang được sử dụng bởi X người. Sửa số giờ có thể tính lại số ngày của những đơn nháp của họ.*

### Ảnh hưởng lên **mẫu seed sẵn**

Nếu xóa mẫu A đang được gán → **gán A trở thành cũ** (dòng `tab_work_schedule_assignment` vẫn tồn tại, chỉ trỏ tới id mẫu không tồn tại). Hệ thống coi thế là **lỗi cấu hình**, resolver sẽ fall back (xem §9.1).

---

## 9. Xem lịch — màn lịch làm việc dạng lịch

Màn `/hr/work-roster` — **lưới nhân sự × ngày**, cho phép xem ai làm, ai nghỉ, ngày nào lễ.

### 9.1. Luật rơi lại (fallback)

Nếu **chưa gán gì**, hoặc **gán trỏ tới mẫu bị xóa**:

```
FALLBACK_WEEK = T2–T7 FULL 08:00–17:00, CN OFF
```

Cơ chế **đồng nhất**: không có lịch = dùng lịch mặc định (cũng như trước kia cứng `WEEKEND_DAYS`).

Có **test tương đương** ở phase 3 — mọi tổ hợp loại ngày 7 thứ khi chưa gán phải ra số giống hệt bản cũ.

### 9.2. Phạm vi dữ liệu (hai lớp độc lập)

**Hàng** (nhân sự):
- Danh sách nhân sự = áp `apply_scope(Employee, 'employee', user, profile)` — người xem chỉ thấy nhân sự trong phạm vi của họ.
- Nếu người A nhìn không thấy người B → người B không ra trong hàng.

**Lớp nghỉ phép** (trong mỗi ô lịch):
- Mọi ô trước hết hiện **loại ngày theo lịch** (OFF / FULL / nửa buổi / giờ).
- Nếu có **đơn nghỉ phép** của người ở ô đó → chồng lên, nhưng **chỉ nếu người xem có quyền đọc đơn đó** (`apply_scope(LeaveRequest, 'leave_request', user, profile)`).
- Nếu người xem **không có quyền** đọc đơn → ô **hiện bình thường theo lịch**, không lộ dấu vết đơn.

Ví dụ: Quản lý kho xem lịch tuần nhân sự của cả công ty (quyền `employee.read` rộng) → thấy hết mọi hàng; nhưng chỉ đơn trong phạm vi duyệt của họ ở Kho (`leave_request.read` hẹp) mới thấy lớp nghỉ phép.

### 9.3. Hiển thị trạng thái đơn nghỉ

**Đã duyệt**: ô tô đầy màu, có tên loại nghỉ + tên đơn.
**Chờ duyệt**: ô viền nét đứt (dash), cùng tên.
**Các trạng thái khác** (nháp, từ chối, hủy, rút): **không hiện**.

Nửa buổi: tô / viền chỉ nửa ô (nửa sáng ở trên, nửa chiều ở dưới).

### 9.4. Hiệu năng (bắt buộc — xem memory)

**Số truy vấn CỐ ĐỊNH**, không phụ thuộc số nhân sự × số ngày:

1. **Danh sách nhân sự** (trang + count) — 2 truy vấn (qua `apply_scope`).
2. **Gán lịch** (gom bốn cấp độ) — 1–2 truy vấn (trong `resolver_many.load_day_plans_many`).
3. **Mẫu + bảy ngày mỗi mẫu** — 1–2 truy vấn.
4. **Ngày lễ** (chung + riêng pháp nhân) — 1 truy vấn.
5. **Đơn nghỉ phép + dòng loại** — 1–2 truy vấn (tra theo `employee_id` + phạm vi).

**Test đếm truy vấn**: 5 người × 7 ngày và 50 người × 42 ngày phải **bằng số truy vấn nhau** (chứng tỏ không loop lặp theo người × ngày).

### 9.5. Các chế độ xem

| Chế độ | Khổ rộng | Khổ hẹp (390px) | Trả lời |
|---|---|---|---|
| **Tuần** | Mặc định | Danh sách hàng (nhân sự), ô cột kia tô/viền nhỏ + chữ | Tuần này ai làm gì |
| **Tháng** | 6 cột (mặc định Google Calendar) | Ô nhỏ + ký hiệu một chữ, tooltip | Tháng này ai lặp lại gì |

Chuyển tuần/tháng bằng nút trên thanh công cụ; ở khổ hẹp chế độ và thanh dùng kiểu **cấp hai** (gạch chân).

### 9.6. Phạm vi ngày

- Mặc định: **tuần chứa hôm nay** (T2 tuần đó đến CN).
- Tối đa: **42 ngày** (6 tuần). Tham số `from_date` + `to_date` vượt 42 ngày → **422 / 400**.
- Mặc định `page_size = 50`; có pagination thật (không load cả công ty một lần).

---

## 10. Thẻ lịch trên hồ sơ nhân sự

Khung **Lịch làm việc** trong tab **Quỹ phép** ở `/hr/employees/:id` (đối chiếu màn 13/11/2026: không phải tab riêng) — **chỉ xem**, hiện **mẫu và ngày hiệu lực** của người đó.

Gác `employee.read` (xem nhân sự) — **không đòi** `work_schedule.read` (xem cấu hình lịch). Luật:
- Người có `work_schedule.write` thấy nút **Gán lịch** dẫn tới `/hr/work-schedule-assignments` (KHÔNG lọc sẵn người, không điền sẵn hộp Thêm).
- Người gán được lịch riêng cho người này (`work_schedule.create` hoặc `work_schedule_personal.create`) thấy thêm nút **Đổi lịch riêng** (duoc-CR-757 lượt 2): mở màn Gán lịch với hộp Thêm điền sẵn cấp Nhân sự + người này. Không hiện trên hồ sơ của chính mình. Luật của Trưởng phòng ở §20.
- Chỉ xem (quyền `employee.read` không quản lý lịch) → khung chỉ thấy lịch hiện tại, không có nút.

---

## 11. Danh sách API endpoints

| Điểm cuối | Phương thức | Gác | Ghi chú |
|---|---|---|---|
| `/api/work-schedules` | GET | `work_schedule.read` | Danh sách mẫu, lọc `is_active` |
| `/api/work-schedules` | POST | `work_schedule.create` | Tạo mẫu + 7 dòng |
| `/api/work-schedules/:id` | GET | `work_schedule.read` | Chi tiết mẫu |
| `/api/work-schedules/:id` | PATCH | `work_schedule.write` | Sửa mẫu + 7 dòng (thay toàn bộ) |
| `/api/work-schedules/:id` | DELETE | `work_schedule.delete` | Xóa mẫu (soft delete thành `is_active = false`) |
| `/api/work-schedule-assignments` | GET | `work_schedule.read` | Danh sách gán |
| `/api/work-schedule-assignments` | POST | `work_schedule.create` | Tạo gán (auto-close dòng cũ nếu cần) |
| `/api/work-schedule-assignments/:id` | GET | `work_schedule.read` | Chi tiết gán |
| `/api/work-schedule-assignments/:id` | PATCH | `work_schedule.write` | Sửa gán (kiểm luật cấm chồng lại) |
| `/api/work-schedule-assignments/:id` | DELETE | `work_schedule.delete` | Xóa gán (mở lại dòng cũ nếu bị tự đóng) |
| `/api/work-schedules/tools/effective` | GET | `employee.read` | **Công cụ**: lấy mẫu hiệu lực của người ngày hôm nay |
| `/api/work-schedules/tools/roster` | GET | `employee.read` | **Công cụ**: dựng lưới lịch (42 ngày, phân trang) |
| `/api/work-schedule-assignments` (POST / PATCH / DELETE) | — | `work_schedule.<hành động>` **hoặc** `work_schedule_personal.<hành động>` (duoc-CR-757 lượt 2) | Đường Trưởng phòng chịu thêm các chốt §20.2; đọc (GET) vẫn `work_schedule.read` |
| `/api/work-schedule-assignments/tools/assignable-employees` | GET | `work_schedule.create` hoặc `work_schedule_personal.create` | **Công cụ** (lượt 2): nhân sự ĐANG LÀM gán được lịch riêng — nguồn ô **Đối tượng áp dụng** ở cấp Nhân sự; `q` tìm mã / họ tên không dấu |
| `/api/work-schedules/tools/effective-department` | GET | `department.read` + `get_scoped` phòng ban | **Công cụ** (duoc-CR-757): lịch hiệu lực của cả phòng + cấp nguồn + các dòng gán cấp phòng ban — xem §19.2 |

Bảng đủ mọi đường của phân hệ (dựng bằng máy) và hợp đồng dữ liệu: [`tai-lieu-ky-thuat/api.md`](tai-lieu-ky-thuat/api.md).

---

## 12. Luật ngày công — từng chi tiết

### 12.1. Áp dụng lịch vào form nghỉ phép

Hàm **`workday_service.count_leave_days(from_date, to_date, from_session, to_session, employee, exclude_holiday)`** — **NỘI DUY NHẤT** tính số ngày công.

Ngôn ngữ giai đoạn (`from_session` / `to_session`): FULL / MORNING / AFTERNOON, chỉ điểm **bắt đầu** và **kết thúc** của khoảng nghỉ (không phải buổi của từng ngày).

| Ô buổi | Ngày ĐẦU | Ngày CUỐI |
|---|---|---|
| Cả ngày | **1.0** | **1.0** |
| Buổi sáng | **1.0** ← bắt đầu từ sáng, xem như cả ngày | 0.5 |
| Buổi chiều | 0.5 | **1.0** ← kết thúc cuối chiều, xem như cả ngày |

Khi **cùng một ngày** (xảy ra ca `Sáng → Chiều`): tra cả hai ô cùng ôi → **1.0** (không phải 0.5 + 0.5).

### 12.2. Bỏ qua lễ (`exclude_holiday = True` / `False`)

- `True` (mặc định): **loại ngày lễ** (cộng lễ từ `holiday_dates` của pháp nhân cộng hệ thống).
- `False` (thai sản): **giữ lễ như ngày thường**, đếm công y như bình thường. Chỉ bỏ OFF (chủ nhật của người nghỉ).

### 12.3. Luật ứng dụng bộ máy phê duyệt

`exclude_holiday` **không ảnh hưởng** tới bộ máy phê duyệt, chỉ ảnh hưởng tới **công thức số ngày**. Luồng duyệt vẫn chạy trên loại nghỉ chính (dòng có số ngày nhiều nhất) của đơn.

### 12.4. Khác biệt với bản cũ

**Bản cũ (cứng `WEEKEND_DAYS`)** tra một bảng chung cho ngày đầu + ngày cuối. **Nay tra hai bảng khác nhau** vì ngày đầu quyết định loại ngày qua `from_session`, ngày cuối quyết định loại ngày qua `to_session`. Ba ca sai âm thầm trước kia:

| Khoảng | Bản cũ (sai) | Nay (đúng) | Ai ăn |
|---|---|---|---|
| Sáng 05 → Hết 07 | 2.5 | 3.0 | Công ty trừ hụt |
| Cả ngày 05 → Chiều 07 | 2.5 | 3.0 | Công ty trừ hụt |
| Cả ngày → Sáng, **cùng ngày** | 1.0 | 0.5 | Người lao động mất 0.5 |

---

## 13. Tra cứu nhanh

| Cần gì | Ở đâu |
|---|---|
| Bộ mã loại ngày + cấp độ | `backend/app/core/work_schedule_codes.py` |
| Mẫu + danh sách gán | `backend/app/modules/work_schedule/model.py` |
| Luật ngày công | `backend/app/modules/work_schedule/day_rules.py` · `resolver.py` |
| Nạp lịch từng người / gom nhiều người | `backend/app/modules/work_schedule/resolver.py` · `resolver_many.py` |
| Dựng lưới lịch (42 ngày, phân trang) | `backend/app/modules/work_schedule/roster_service.py` |
| Đóng/mở dòng gán tự động | `backend/app/modules/work_schedule/assignment_heal.py` |
| Ngày lễ của người | `backend/app/modules/leave/holiday_calendar.py` |
| Màn mẫu + gán (danh sách + chi tiết) | `frontend-v2/src/modules/hr/pages/work-schedule-*.tsx` · `config/work-schedule-*.tsx` |
| Thẻ lịch trên hồ sơ | `frontend-v2/src/modules/hr/components/employee-work-schedule-card.tsx` |
| Tab Lịch làm việc của phòng ban (CR-757) | `frontend-v2/src/modules/hr/components/department-work-schedule-tab.tsx` · `work-schedule-week-grid.tsx` · `utils/describe-department-schedule-source.ts` · `utils/work-schedule-assignment-prefill.ts` |
| Lịch hiệu lực của phòng (CR-757) | `backend/app/modules/work_schedule/resolver.py` → `effective_for_department` |
| Trợ lý AI đọc lịch + ngày đã nghỉ (CR-757) | `backend/app/modules/assistant/tools/leave_taken_schedule.py` · `leave_tool.py` (`my_leave_summary`) · `employee_leave_tool.py` (`employee_leave_summary`) |
| Màn xem lịch (tuần/tháng) | `frontend-v2/src/modules/hr/pages/work-roster-page.tsx` · `components/work-roster-*.tsx` |
| Bài kiểm backend | `test/backend/test_lich_lam_viec_*.py` |
| Bài kiểm frontend | `frontend-v2/src/modules/hr/**/*.test.ts*` (các tệp liên quan lịch làm việc) |

---

## 14. Nguyên tắc sửa nhanh

- **Muốn thay đổi số giờ / loại ngày** → sửa mẫu (`tab_work_schedule` + `tab_work_schedule_day`), ảnh hưởng đơn **nháp** (mở lại gợi ý).
- **Muốn gán cho người/phòng/pháp nhân** → tạo dòng gán (`tab_work_schedule_assignment`).
- **Muốn bỏ gán** → xóa dòng gán, nếu nó tự đóng một dòng cũ → máy chủ tự mở lại dòng cũ.
- **Muốn kiểm tra nhân sự nào dùng lịch nào** → lọc gán theo người / phòng / loại.
- **Muốn xem tuần tới ai làm ai nghỉ** → màn `/hr/work-roster` (xem lịch).
- **Muốn không gán → dùng fallback** (T2–T7 08–17, CN OFF).

---

## 15. Lệnh kiểm tra (backend)

Chạy từng tệp, không quét cả thư mục (sửa 13/11/2026: bản 1.0 ghi bốn tên tệp không có thật).

```bash
# Bộ mã, quyền, luật ngày công, phân giải lịch (một người / gom nhiều người)
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_bo_ma_va_quyen.py -q --timeout=120
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_luat_ngay.py -q --timeout=120
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_phan_giai.py -q --timeout=120
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_phan_giai_gom.py -q --timeout=120

# Đường API, tính ngày nghỉ theo lịch, lưới Xem lịch, bài rà soát
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_api.py -q --timeout=120
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_tinh_ngay_nghi.py -q --timeout=120
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_roster.py -q --timeout=120
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_roster_ra_soat.py test/backend/test_lich_lam_viec_ra_soat_be.py -q --timeout=120

# duoc-CR-757: lịch của phòng ban + trợ lý tra phép / ngày đã nghỉ (phạm vi, số truy vấn cố định)
docker compose exec -T api python -m pytest test/backend/test_tro_ly_tra_phep_lich_lam_viec_cr757.py -q --timeout=120
```

---

## 16. Lệnh kiểm tra (frontend)

```bash
# Mẫu lịch + gán lịch
docker compose exec -T erp npm run typecheck
docker compose exec -T erp npm run lint
docker compose exec -T erp npx vitest run src/modules/hr

# Nếu sửa phần dùng chung
docker compose exec -T erp npx vitest run src/shared/crud
```

---

## 17. Ghi chú phát triển

⚠️ **Thay `WEEKEND_DAYS` bằng lịch**, do đó nếu **chưa gán gì** phải có **fallback bằng cứu** để **tương đương** — test này còn thiếu thì không khóa được chất lượng.

⚠️ **Auto-close / auto-reopen dòng gán** là khái niệm **mới** so với phần nghỉ phép — nếu sửa logic phải cẩn thận **không để người lao động mất ngày phép** hay **công ty trừ hụt ngày công**.

⚠️ **Thẻ lịch trên hồ sơ** chỉ hiện mẫu — không che giấu quyền (mục menu gác `manage`), nhưng **không bắt buộc quyền `work_schedule.read`** để xem hồ sơ thấy lịch.

---

## 18. Ghi chú sử dụng

**Chợ hay bỏ sót:**

1. **Gán rồi mà đơn nghỉ cũ vẫn khai theo lịch cũ** — vì đơn cũ **lưu số giờ cứng** ngày nộp, sửa lịch sau không đổi. Mở đơn nháp cũ lên → **nó gợi ý theo lịch mới**, nhưng nó chỉ là gợi ý, người dùng phải sửa dòng loại nghỉ + số ngày nếu muốn khác.
2. **Mẫu A được dùng bởi 10 người, sửa A rồi báo cáo thay đổi** — báo cáo gốc (hồi sinh từ `metadata` giấy GNP) không đổi; chỉ **đơn nháp** của những người đó **gợi ý lại khi mở** — khi gửi duyệt, để họ chốt số mới.
3. **Phòng kiêm nhiệm** — không tính, chỉ dùng **phòng chính** (`employee.department_id`). Người **hai phòng** được cấp lịch riêng nếu cần, nhưng lịch được áp là lịch của **phòng chính** duy nhất.
4. **Ngày lễ chung** — cộng công ty (`target_id = 0` trên bảng `holiday_dates`), tính vào công của **mọi pháp nhân**. **Ngày lễ riêng** (Tết Nguyên đán Âm lịch ở HCM nhưng không ở HN) → thêm riêng pháp nhân đó.
5. **Sửa lịch công ty nước ngoài** — không ảnh hưởng công ty Việt, chỉ ảnh hưởng người gán cho pháp nhân đó.

---

---

## 19. Lịch làm việc của phòng ban và trợ lý AI (duoc-CR-757, 13/11/2026)

Gán lịch theo phòng ban và đếm ngày nghỉ theo lịch của người nghỉ đã có từ duoc-CR-589 (§5, §7, §12). CR này thêm ba
thứ: trang phòng ban cho thấy phòng đang theo lịch nào, một đường API cho việc đó, và trợ lý AI / cổng MCP đọc được lịch
làm việc cùng số ngày đã nghỉ.

### 19.1. Tab Lịch làm việc ở trang phòng ban

Trang `/hr/departments/:id` (*Nhân sự ▸ Danh mục ▸ Phòng ban* ▸ bấm một phòng) có hai tab dưới biểu mẫu, nhớ ở `?tab=`:
**Pháp nhân & nhân sự** (nội dung cũ: pháp nhân áp dụng, bảng nhân sự, bảng kiêm nhiệm) và **Lịch làm việc** (mới).
Giá trị lạ trên URL rơi về tab đầu.

Tab **Lịch làm việc** gồm:

| Phần | Nội dung |
|---|---|
| Dòng nguồn | Tên mẫu lịch + câu nói lịch lấy từ đâu: *Gán riêng cho phòng này từ dd/mm/yyyy [đến dd/mm/yyyy]* · *Theo lịch của pháp nhân X* · *Theo lịch toàn hệ thống* · *Chưa gán — dùng lịch mặc định*. Rẽ nhánh theo mã cấp (`WORK_SCHEDULE_LEVEL_CODE`), không theo số trần |
| Lưới bảy ngày | Loại ngày + giờ từng thứ (`WorkScheduleWeekGrid`, dùng chung với thẻ lịch trên hồ sơ) |
| Hai dòng chú thích | *N ngày công/tuần* và *Nhân sự nào được gán lịch riêng thì theo lịch riêng đó, không theo lịch của phòng.* |
| **Gán lịch riêng cho phòng** | Mọi dòng gán CẤP PHÒNG BAN của phòng này, mới nhất trước: tên mẫu, *Từ … · đến …* hoặc *Không thời hạn*, nhãn **Đang áp** ở dòng đang hiệu lực. Không có dòng nào: *Phòng này chưa có dòng gán lịch riêng.* |
| Nút **Gán lịch cho phòng** | Chỉ hiện khi có `work_schedule.create`. Mở màn Gán lịch (`/hr/work-schedule-assignments?target_level=3&prefill_target_id=<id>&prefill_target_name=<tên>`) với hộp **Thêm dòng gán lịch** mở sẵn, ô **Cấp áp dụng** = Phòng ban, ô **Đối tượng áp dụng** = phòng này (vẫn đổi được). Đóng hộp (Hủy hoặc lưu xong) thì gỡ hai tham số `prefill_*` khỏi URL, giữ `target_level` vì đó cũng là bộ lọc **Cấp áp dụng** của bảng |
| Nút **Xem gán lịch** | Chỉ hiện khi có `work_schedule.read`. Mở màn Gán lịch lọc sẵn cấp Phòng ban |

Xem tab gác bằng quyền mở trang (`department.read`), **không** đòi `work_schedule.read` — cùng lý lẽ với thẻ lịch trên hồ sơ
(§10). Lỗi 403 / 404 chỉ hiện một câu *Không xem được lịch làm việc của phòng ban này.*, không chặn phần còn lại của trang.

### 19.2. Đường `GET /api/work-schedules/tools/effective-department`

Tham số `department_id` (bắt buộc) và `on_date` (mặc định hôm nay theo giờ VN, năm 2000–2100). Gác `department.read` +
`get_scoped` phòng ban: ngoài phạm vi và không tồn tại cùng trả 404.

Phân giải bằng chính luật hẹp thắng rộng (`resolver._pick`) với bộ (nhân sự = 0, phòng, pháp nhân của phòng): chỉ còn **phòng ban > pháp nhân >
toàn hệ thống**. Kết quả có đủ khóa của `/tools/effective` cộng `department_id`, `department_name`, `company_id`,
`assignments[]`. `level`: **3** Phòng ban · **2** Pháp nhân · **1** Toàn hệ thống · **0** khi `is_fallback = true`. Phòng
dùng chung (`company_id = 0`) không có cấp pháp nhân để kế thừa; nhân sự của phòng đó vẫn có thể theo lịch pháp nhân riêng
của họ. Lịch của phòng KHÔNG tính lịch gán riêng cho từng nhân sự — muốn biết một người theo lịch nào thì xem thẻ lịch trên
hồ sơ của người đó (`/tools/effective`).

### 19.3. Trợ lý AI và cổng MCP

| Công cụ | Thêm gì | Gác |
|---|---|---|
| `my_leave_summary` (chính người hỏi) | `work_schedule` = lịch đang áp hôm nay (tên, cấp nguồn, bảy ngày có nhãn thứ và giờ, số ngày công/tuần); `taken_by_type` = số ngày nghỉ trong năm theo TỪNG loại, gồm cả loại không trừ quỹ (không lương, ốm…), tách `approved_days` (đã duyệt, ngày bắt đầu ≤ hôm nay: đã / đang nghỉ), `approved_upcoming_days` (đã duyệt, sắp tới), `pending_days` (chờ duyệt); `taken_total_days` (= tổng `approved_days`, con số *đã nghỉ*), `upcoming_total_days`, `pending_total_days`. Năm mặc định đổi sang `vn_today()` | Như cũ (dữ liệu của chính mình) |
| `employee_leave_summary` (MỚI, chỉ đọc) | Quỹ phép (`remaining_days` qua `available_days_map`), ngày đã nghỉ theo loại (cùng khóa như trên) và tên lịch đang áp của nhân sự khác — tra theo mã / tên (`employee`) hoặc theo phòng (`department`, gõ kèm chữ *phòng* vẫn khớp); trần 20 người mặc định, tối đa 50 | `leave_balance.read`; người trả về = `employee.read` GIAO phạm vi `leave_balance` áp lên hồ sơ, đúng như màn Quỹ phép năm. **Ngày đã nghỉ** thêm một lớp: chỉ đơn trong phạm vi `leave_request.read` của người hỏi; thiếu khóa đó thì `taken_by_type` rỗng (quỹ vẫn trả) — số ngày nghỉ ốm, không lương gần dữ liệu sức khỏe, trước nay chỉ thấy ở màn Đơn nghỉ phép |

Luật giữ nguyên:

- **Một nơi tính.** Ngày đã nghỉ và bản gọn của lịch dựng ở `leave_taken_schedule.py`, hai công cụ dùng chung nên không thể
  nói hai con số khác nhau cho cùng một người. Số còn lại chỉ qua `balance_service.available_days(_map)`; công cụ không gọi
  `ensure_balance` (không tự cấp dòng quỹ).
- **Năm của một đơn = năm của `from_date`**, đúng luật sổ quỹ (`reserve_lines` / `consume_lines`); đổi cách chia là *đã nghỉ*
  lệch với `used_days`. Hệ quả đã chấp nhận: đơn vắt qua hai năm nằm trọn ở năm bắt đầu, nên có thể lệch báo cáo **Tình hình
  nghỉ phép** (báo cáo đó chia ngày theo ngày thật).
- **Đã nghỉ khác đã duyệt**: đơn đã duyệt mà ngày bắt đầu sau hôm nay (giờ VN) nằm ở `approved_upcoming_days`, không cộng vào
  `taken_total_days`.
- **Số truy vấn cố định** bất kể số người (bài đếm trong `test_tro_ly_tra_phep_lich_lam_viec_cr757.py`). Lịch của nhiều người
  đi qua `resolver_many.load_day_plans_many` (+ `DayPlansMany.winner` để biết cấp nguồn).
- `employee_leave_summary` có ở cổng MCP (`READ_TOOLS`), nhóm cấu hình **Nghỉ phép** (`mcp_settings.GROUPS`), nhãn ý định
  `LOOKUP_LEAVE`, bộ lọc công cụ nhóm `leave` của Trợ lý (từ khóa *lịch làm việc*, *giờ làm*, *đã nghỉ mấy ngày*…). Lõi
  bot bỏ tiền tố xưng hô (*anh / chị …*) khỏi tham số `employee` như `employee_lookup`.
- Cẩm nang trợ lý: `backend/app/modules/ai_skill/seed_handbook/40-nghi-phep.md` (mục *Lịch làm việc và ngày đã nghỉ*).

---

## 20. Trưởng phòng gán lịch riêng cho nhân viên (duoc-CR-757 lượt 2, 13/11/2026)

Thử trên local: Trưởng phòng không đổi được lịch cho nhân viên (403 — quyền sửa lịch chỉ Nhân sự có), mà tick
`work_schedule.create` cho họ thì họ sửa được cả mẫu lịch và gán cấp phòng / pháp nhân / toàn hệ thống cho bất kỳ ai. Đã chốt
(Q1): Trưởng phòng **được** gán lịch RIÊNG cho nhân viên phòng mình, chỉ chọn mẫu Nhân sự tạo sẵn, không sửa mẫu, không gán cấp
khác. Mã: `work_schedule/assignment_access.py` (cửa quyền), `assignment_picker.py` (ô chọn người), `assignment_heal.py`
(nối lại lịch cũ), `assignment_controller.py`.

### 20.1. Khóa `work_schedule_personal`

| | |
|---|---|
| Nhãn ở màn Phân quyền | **Nhân sự › Lịch làm việc riêng (Trưởng phòng gán)** |
| Đo phạm vi trên | HỒ SƠ NHÂN SỰ ĐÍCH của dòng gán (`ENTITY_MODEL_PATHS` → `Employee`; `SCOPE_FIELDS` = `company_id`, `department_id`, `self: id`) — bảng gán lịch có đích đa hình nên không lọc thẳng được |
| Hành động có tác dụng | `create` · `write` · `delete` (`read` có trên ma trận nhưng không kiểm ở đâu: đọc dòng gán vẫn là `work_schedule.read`, vai trò nào cũng có) |
| Seed | `dept_head`: `read` / `create` / `write` / `delete`, bậc **Phòng ban**. Nằm trong `_SYS_ENTITIES` nên Quản lý thu mua KHÔNG tự có. Admin nhận qua vòng bù `ENTITIES` của `seed.py` (hệ đang chạy thì không — §21) |
| Ô **Phòng ban được xem** | Có tác dụng (cộng thêm phòng) nhưng KHÔNG mở xuyên công ty: khóa nằm trong `scoping.INCLUDE_DEPT_SAME_COMPANY`, ô đó AND thêm công ty hiện tại của người xem |

Có khóa Nhân sự (`work_schedule.<hành động>`) thì luôn đi đường Nhân sự, luật cũ giữ nguyên từng chữ; chỉ khi THIẾU khóa
Nhân sự ở hành động đó mới xét khóa Trưởng phòng (`require_assignment_action`).

### 20.2. Chín luật của đường Trưởng phòng

| # | Luật | Vi phạm |
|---|---|---|
| 1 | Chỉ cấp **Nhân sự** (`WorkScheduleLevel.EMPLOYEE` = 4) — cả dòng đang có lẫn giá trị mới | 403 *Bạn chỉ được gán lịch làm việc riêng (cấp Nhân sự) cho nhân sự trong phạm vi của mình* |
| 2 | Nhân sự đích trong phạm vi khóa (bậc Phòng ban = phòng chính + phòng kiêm nhiệm của người gán, cùng công ty hiện tại) | 400 *Đối tượng được gán lịch không tồn tại* khi tạo / đổi đích (không lộ người đó có thật không); 404 khi sửa / xóa dòng của người ngoài phạm vi |
| 3 | Không gán / sửa / xóa lịch riêng của **chính mình** (so `profile.employee_id`, tài khoản chưa gắn hồ sơ không bao giờ trùng) | 403 *Bạn không được tự gán, sửa hay xóa lịch làm việc riêng của chính mình* |
| 4 | Chỉ chọn mẫu lịch **đang dùng** — `assignment_service._check_schedule`, áp cả hai đường | 400 *Mẫu lịch "…" đã tắt, không gán thêm được* |
| 5 | Không đụng mẫu lịch — `template_controller` vẫn chỉ nhận `work_schedule` | 403 |
| 6 | Chỉ sửa / xóa dòng do **chính mình** gán (`created_by`, kiểm SAU phạm vi). Dòng của Nhân sự hay người khác: không sửa / xóa được, nhưng TẠO dòng mới vẫn được và vẫn tự đóng / cắt đôi dòng "không thời hạn" của Nhân sự (cách đổi lịch từ một ngày trở đi, §5.1) | 403 *Lịch này do Nhân sự hoặc người khác gán, bạn chỉ sửa được lịch do chính mình gán* |
| 7 | **Hiệu lực từ ngày ≥ hôm nay** (giờ VN, `vn_today()`) khi tạo và khi sửa mà đổi ngày bắt đầu — không lùi ngày làm đổi cách đếm ngày nghỉ đã qua | 422 *Ngày hiệu lực phải từ hôm nay trở đi* |
| 8 | Dòng **đã bắt đầu** (`effective_from` < hôm nay): chỉ đổi **Đến ngày** (≥ hôm qua, hoặc bỏ trống) và **Ghi chú**; không đổi mẫu / người / cấp / ngày bắt đầu; **không xóa** | 403 *Lịch đã bắt đầu, chỉ đặt được ngày kết thúc* · 422 *Ngày kết thúc của lịch đã bắt đầu phải từ hôm qua trở đi* · 403 *Lịch đã bắt đầu, không xóa được — hãy đặt ngày kết thúc* |
| 9 | Dòng **đã thay lịch trước đó** (lúc tạo đã tự đóng một dòng khác — cờ `replaces_previous` ở API): khóa người + ngày bắt đầu (đổi sẽ gỡ liên kết, xóa sau đó không mở lại lịch cũ). Ngày kết thúc vẫn đổi được | 400 *Lịch này đã thay lịch trước đó, muốn đổi hãy xóa rồi tạo lại* |

Lý do luật 6–8: Trưởng phòng thường cũng là người duyệt đơn nghỉ và phiếu nghỉ bù của nhân viên đó; lùi lịch quá khứ (ví dụ
biến thứ Bảy đã đi làm thành ngày nghỉ) là mở đường xin nghỉ bù cho những ngày ấy (`comp_request_service` nhận ngày làm vào
ngày nghỉ bằng `count_leave_days == 0`).

### 20.3. Đổi ngày kết thúc của dòng đã thay lịch — lịch cũ tự nối lại

Áp cho CẢ đường Nhân sự lẫn Trưởng phòng (`assignment_service.update_assignment` + `assignment_heal.find_replaced_and_resume`,
`move_resume`). Dòng C được tạo đè lên dòng không thời hạn P (P bị đóng ở `C.from − 1`, có thể có dòng nối lại R từ `C.to + 1`).
Sửa CHỈ ngày kết thúc của C:

- đặt ngày kết thúc khi C đang không thời hạn → tạo R là bản sao lịch của P từ ngày hôm sau;
- đổi ngày kết thúc khi đã có R → dời ngày bắt đầu của R về ngày hôm sau (kéo dài hay rút ngắn đều liền mạch);
- bỏ trống ngày kết thúc → xóa R;
- ngày kết thúc mới chồng hết khoảng của R (R có hạn) → 400 *Ngày kết thúc mới chồng hết khoảng lịch cũ được nối lại; …*.

R luôn **giữ người gán gốc của P** (`created_by = P.created_by`, `updated_by` = người thao tác) — cả ở lúc tạo dòng (POST) — để
Trưởng phòng không thành "chủ" của dòng nối lại lịch Nhân sự rồi xóa nó (rà mã N4). Mỗi lần tạo / dời / xóa R ghi một dòng
nhật ký riêng. Đổi người hay ngày bắt đầu của C vẫn gỡ liên kết như cũ (§5.1).

### 20.4. Ô chọn người — `GET /api/work-schedule-assignments/tools/assignable-employees`

Nguồn ô **Đối tượng áp dụng** ở cấp Nhân sự. Có `work_schedule.create` → nhân sự trong phạm vi `employee.read`; chỉ có
`work_schedule_personal.create` → nhân sự trong phạm vi khóa đó (kể cả ô Phòng ban được xem, cùng công ty), **trừ chính
mình**; thiếu cả hai → 403. Chỉ người đang làm, xếp họ tên, `q` tìm mã / họ tên không dấu, phân trang; hai truy vấn cố định.
Trả `{total, items: [{id, code, full_name, department_name}]}`.

### 20.5. Giao diện

- Khung **Lịch làm việc** trên hồ sơ (tab **Quỹ phép**) có nút **Đổi lịch riêng** (người gán được, không phải hồ sơ của mình).
- Màn **Gán lịch** (*Nhân sự ▸ Thiết lập* ▸ tab **Gán lịch**) hiện cho cả người chỉ có `work_schedule_personal`; nút **Thêm
  dòng gán lịch** theo khóa của đường người dùng. Hộp Thêm / Sửa của Trưởng phòng: **Cấp áp dụng** khóa ở Nhân sự (chữ chỉ
  xem), câu nhắc *Bạn chỉ gán được lịch riêng cho nhân viên thuộc phòng mình. Mẫu lịch và lịch của cả phòng do Nhân sự cấu
  hình.*, **Hiệu lực từ ngày** không nhận ngày trước hôm nay; dòng đã bắt đầu chỉ còn **Đến ngày** + **Ghi chú** và ẩn nút
  Xóa; dòng đã thay lịch trước đó khóa người + ngày bắt đầu. API trả `created_by` để giao diện ẩn Sửa / Xóa với dòng không do
  chính Trưởng phòng gán.
- Mọi luật vẫn chốt ở backend; câu lỗi hiện ở toast của khung CRUD.

### 20.6. Ma trận quyền (sau duoc-CR-757)

| Việc | `work_schedule` (Nhân sự) | `work_schedule_personal` (Trưởng phòng) | Chỉ có `read` |
|---|---|---|---|
| Xem mẫu lịch, danh sách gán lịch | có | có (qua `work_schedule.read` mọi vai trò có) | có |
| Thêm / sửa / xóa mẫu lịch tuần | có | **không** | không |
| Gán cấp Toàn hệ thống / Pháp nhân / Phòng ban | có | **không** | không |
| Gán lịch riêng cấp Nhân sự | mọi nhân sự trong phạm vi `employee.read`, kể cả mình | nhân viên trong phạm vi khóa, **trừ mình**, từ hôm nay | không |
| Sửa / xóa dòng lịch riêng | mọi dòng | chỉ dòng tự gán; dòng đã bắt đầu chỉ đặt Đến ngày, không xóa | không |
| Xem lịch của phòng (tab ở trang phòng ban) | `department.read` | `department.read` | `department.read` |

Bài kiểm: `test/backend/test_truong_phong_gan_lich_rieng_cr757.py`.

---

## 21. Sổ việc trước và sau khi deploy duoc-CR-757 (dev / prod, D-018)

Seed prod (`seed_prod.py`) không ghi đè phân quyền đã sửa tay, nên khóa mới và bậc mới KHÔNG tự tới vai trò cũ. Làm đủ, theo thứ
tự:

1. **Trước deploy — đếm vai trò sẽ HẸP lại.** Bậc `dept` của `leave_balance` đổi nghĩa từ *cả công ty* sang *người thuộc phòng
   của tôi* (§19, `02-nghi-phep.md` §17). Đếm và báo người chủ danh sách:

   ```sql
   SELECT r.code, r.name FROM tab_permission p JOIN tab_role r ON r.id = p.role_id
   WHERE p.entity = 'leave_balance' AND p.scope = 'dept' AND p.can_read = 1;
   ```

   Kèm số người đang giữ ô **Phòng ban được xem** (`tab_user_scope`, chiều `department`, không loại trừ) trên vai trò có
   `leave_balance.read` — ô đó trước không có tác dụng với quỹ phép, nay MỞ thêm quỹ phép của người phòng đó (trong công ty
   hiện tại của người xem):

   ```sql
   SELECT r.code, r.name, COUNT(DISTINCT s.user_id) AS so_nguoi
   FROM tab_user_scope s
   JOIN tab_permission p ON p.role_id = s.role_id AND p.entity = 'leave_balance' AND p.can_read = 1
   JOIN tab_role r ON r.id = s.role_id
   WHERE s.dim = 'department' AND s.is_exclude = 0
   GROUP BY r.code, r.name;
   ```

   Vai trò có `leave_balance.write` / `create` bậc `dept` cũng hẹp ở màn **Phân bổ chính sách** (`writable_employee_query`).
2. **Deploy, rồi khởi động lại api** (cache quyền 60 giây theo tiến trình; người đang đăng nhập phải đăng xuất / đăng nhập lại
   mới nhận khóa mới). ⚠️ Chuỗi ký HMAC của cổng B nay gồm hai header kênh AI + chat riêng (`core/agent_signature.py`): ERP
   và dịch vụ AI (chế độ `service`) phải dựng lại CÙNG một đợt, lệch nhau là mọi lượt gọi qua cổng B bị 401.
3. **Cấp khóa mới cho vai trò admin TRƯỚC** — luật chống tự nâng quyền chặn admin tick một khóa mà chính vai trò của họ chưa có.
   Hai cách: đặt `SEED_FORCE_SYNC=true` trong `.env`, khởi động lại api một lần rồi trả về `false` (⚠️ cách này áp lại TOÀN BỘ
   `STD_ROLES` lên vai trò chuẩn, kể cả `dept_head` bên dưới); hoặc chạy một script nhỏ thêm dòng `tab_permission` cho vai trò
   admin, entity `work_schedule_personal`, đủ hành động, bậc Tất cả.
4. **Tick cho vai trò Trưởng phòng (`dept_head`)** ở *Quản trị ▸ Phân quyền tài khoản* ▸ tab Vai trò & quyền:
   - **Nhân sự › Lịch làm việc riêng (Trưởng phòng gán)**: Xem, Tạo, Sửa, Xóa — phạm vi **Phòng ban**;
   - **Nghỉ phép › Quỹ phép năm** (`leave_balance`): Xem — phạm vi **Phòng ban**;
   - **Nghỉ phép › Đơn nghỉ phép** (`leave_request`): Xem — phạm vi **Phòng ban** (để trợ lý trả được số ngày đã nghỉ của nhân viên).
   Kiểm vai trò Trưởng phòng của từng người có mang ô **Phòng ban được xem** không: ô đó cộng thêm phòng cho cả lịch riêng lẫn
   quỹ phép (cùng công ty).
5. **Tài liệu và trợ lý trên đúng môi trường đích:**

   ```bash
   docker compose exec -T api python scripts/seed_help_nhan_su.py
   docker compose exec -T api python scripts/publish_handbook_update.py --only nghi-phep,nhan-su-ho-so --note "duoc-CR-757"
   docker compose exec -T api python scripts/reindex_help_rag.py
   ```
