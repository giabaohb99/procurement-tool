# Lịch làm việc — phân hệ Nhân sự

| | |
|---|---|
| Bản | 1.0 — 05/10/2026 (duoc-CR-589) |
| CR | **duoc-CR-589** |
| Giao diện | **chỉ có trên `frontend-v2/`** (cổng 8083), menu *Nhân sự ▸ Lịch làm việc* |
| Kế hoạch gốc | `plans/261005-0925-hr-lich-lam-viec/plan.md` |
| Nguồn nghiệp vụ | `doc/erp/tham-khao-hrm/01-co-cau-to-chuc-nhan-su.md` · `doc/tai-lieu-chuc-nang/17-nghi-phep.md` |

---

## 1. Chức năng này để làm gì

Quản lý lịch làm việc hàng tuần: một mẫu lịch 7 ngày với loại từng ngày (cả ngày / nửa ngày sáng / nửa ngày chiều / nghỉ) và giờ làm. Mẫu được gán theo **bốn cấp độ** (từ hẹp đến rộng): nhân sự riêng → phòng ban → pháp nhân → hệ thống, **người duyệt đơn nghỉ phép dùng lịch của chính người** để tính ngày công thay cho cứng `WEEKEND_DAYS = (6,)` cũ.

**Vì sao không màn riêng « Lịch làm việc» dạng lưới xem-ai-làm-ai-nghỉ ở đây.** Đó là màn [«Xem lịch»](#9-xem-lịch--màn-lịch-làm-việc-dạng-lịch) (§9 dưới), màn hiển thị dữ liệu từ bốn nguồn:
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

## 3. Bốn màn hình

| Màn | Đường dẫn | Khóa quyền | Vai trò |
|---|---|---|---|
| Mẫu lịch (danh sách + chi tiết + thêm) | `/hr/work-schedules` | `work_schedule.read` / `.create` / `.write` / `.delete` | HR + sửa lịch |
| Gán lịch (danh sách + chi tiết + thêm) | `/hr/work-schedule-assignments` | `work_schedule.read` / `.create` / `.write` / `.delete` | HR + sửa lịch |
| Xem lịch (tuần / tháng, nhân sự × ngày) | `/hr/work-roster` | `employee.read` (hàng), `leave_request.read` (lớp nghỉ phép) | mọi người, xem riêng |
| Thẻ lịch trên hồ sơ | Tab trên `/hr/employees/:id` | `employee.read` | xem cùng nhân sự |

**Quyền sửa** (`work_schedule.write` / `.create` / `.delete`): chỉ **`admin` · `hr_leave` · `hr_profile`**. Mọi vai trò khác chỉ `read` (cho form nghỉ phép đọc lịch tính số ngày). Trên hệ **đang chạy** (prod/dev-UAT), vai trò cũ **không tự có** khóa `work_schedule` — seed không ghi đè — phải thêm ở màn Phân quyền tài khoản, hoặc `SEED_FORCE_SYNC=true` một lần rồi khởi động lại API.

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
| **Chọn mẫu** | `schedule_id` | chọn (nạp từ API) | — | Có | Danh sách mẫu đang dùng (`is_active = true`) |
| **Cấp độ gán** | `target_level` | chọn | — | Có | SYSTEM (0) / COMPANY / DEPARTMENT / EMPLOYEE (3) — dùng `WorkScheduleLevel` |
| **Gán cho** | `target_id` | chọn (thay đổi theo cấp độ) | — | Có (ngoại trừ SYSTEM) | Danh sách pháp nhân / phòng ban / nhân sự tùy cấp độ; cấp SYSTEM để mặc định 0 |
| Từ ngày | `effective_from` | chọn ngày | — | Có | Ngày gán có hiệu lực |
| Đến ngày | `effective_to` | chọn ngày | — | Không | NULL = không thời hạn (cứ dùng tới khi thay bằng gán khác) |
| **Ghi chú** | `note` | nhiều dòng | rỗng | Không | Lý do thay đổi lịch (dùng nội bộ) |

### 5.1. Luật cấm chồng (tính trên `target_level + target_id + effective_from`)

**Cùng đối tượng không được có hai gán bắt đầu cùng một ngày** — được kiểm bằng **UNIQUE constraint** ở DB. **Ngoài lệ tự động** (ngày 05/10/2026 chốt):

Nếu **tạo gán mới** và **đối tượng đã có dòng « không thời hạn»** (xảy ra ngày T, nhỏ hơn ngày gán mới):
- Backend tự **đóng dòng cũ** ở ngày `from_mới − 1`, tự ghi audit, tất cả trong **một transaction**.
- Nếu gán mới **có thời hạn** (đến ngày D ≠ NULL):
  - Gán cũ được **nối lại** (mở thêm dòng) từ `D + 1`, ngầm hiểu đó là lịch tạm (ngoài gán chính).
  - Nếu xóa gán tạm này → gán chính quay lại (reset `effective_to = NULL`), nhìn thấy ngay khi tải lại.
- Nếu gán mới **không thời hạn** → gán cũ **hết hiệu lực vĩnh viễn**.

**Mọi chồng khác** (cùng cấp, cùng đối tượng, nhưng ngày bắt đầu khác, hay khác cấp): **chặn + báo 400**, nêu tên dòng trùng rõ ràng.

### 5.2. Đổi mục đích gán giữa nhập liệu (ô cấp độ / gán cho)

Nếu người dùng chọn «Phòng ban» rồi xổ danh sách phòng, sau đó **đổi lại thành «Nhân sự»**, ô **Gán cho** tự xóa (giữ nguyên dòng, chỉ trả ô về trống). Backend kiểm toàn bộ ở `assignment_controller` khi nhận **POST / PATCH** — nếu cấp độ và đối tượng **không khớp** (ví dụ: cấp EMPLOYEE nhưng `target_id` là id của phòng), trả lỗi 400.

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

Khi sửa mẫu, **hộp thoại cảnh báo** (chỉ frontend): *«Mẫu này đang được sử dụng bởi X người. Sửa số giờ có thể tính lại số ngày của những đơn nháp của họ.»*

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

Tab **«Lịch làm việc»** ở `/hr/employees/:id` — **chỉ xem**, hiện **mẫu và ngày hiệu lực** của người đó.

Gác `employee.read` (xem nhân sự) — **không đòi** `work_schedule.read` (xem cấu hình lịch). Luật:
- Sửa hồ sơ (quyền `hr_profile` / `hr_leave`) → mở `CrudDetailPage` của hồ sơ → tab «Lịch làm việc» có nút **[Sửa lịch]** dẫn tới `/hr/work-schedule-assignments?employee_id=X`, đơn giản hóa tìm kiếm (lọc sẵn người).
- Chỉ xem (quyền `employee.read` không quản lý lịch) → tab chỉ thấy dòng hiện tại.

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

```bash
# Kiểm luật ngày công (tương đương với bản cũ khi chưa gán)
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_ngay_cong.py -v

# Kiểm luật gán + auto-close/reopen
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_gan.py -v

# Kiểm lịch xem (roster) — phạm vi + nửa buổi + số truy vấn
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_roster.py -v

# Kiểm tính tương đương bản cũ
docker compose exec -T api python -m pytest test/backend/test_lich_lam_viec_tuong_duong_cu.py -v
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

