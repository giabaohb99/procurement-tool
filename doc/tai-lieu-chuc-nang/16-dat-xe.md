# Đặt xe nội bộ (DEGO Booking Auto)

## Mục đích

Số hóa việc đặt xe trong nội bộ DEGO: nhân sự tạo **yêu cầu đặt xe** (2 loại — *công tác* chở người,
*giao hàng* chở hàng), trưởng bộ phận **duyệt**, điều phối viên **phân 1 xe + 1 tài xế**, tài xế
**nhận → bắt đầu → hoàn tất**. Phân hệ kèm hai **danh mục nền**: Xe và Tài xế (nội bộ / thuê ngoài).

Đường dẫn (chỉ có trên `frontend-v2/`, cổng 8083):
- Yêu cầu đặt xe: `/vehicle-booking` (danh sách), `/vehicle-booking/:id` (chi tiết), `/vehicle-booking/new` (tạo), `/vehicle-booking/:id/edit` (sửa).
- Quản lý xe: `/vehicle-booking/vehicles` · `/vehicles/new` · `/vehicles/:id`.
- Quản lý tài xế: `/vehicle-booking/drivers` · `/drivers/new` · `/drivers/:id`.

> **Rule R2 (QĐ-11).** Cột nghĩa *loại / trạng thái* lưu **`SMALLINT` + hằng số nguyên** (IntEnum-style),
> API trả **số kèm nhãn**, tiếng Việt chỉ ở tầng hiển thị. Áp cho `request_type`, `status`,
> `driver_status`, `supplier_type` — xem hằng số ở `backend/app/modules/vehicle_booking/model.py`.
> Mọi endpoint trả phong bì `{success, message, data}`; gác quyền bằng `require(entity, action)`,
> bó phạm vi bằng `apply_scope`/`get_scoped`; ghi vết bằng `audit`.

## Vai trò tham gia

- **Người tạo / Nhân sự** (`vehicle_booking:create`, `:read`): tạo & gửi duyệt yêu cầu của mình; sửa
  khi phiếu còn *Nháp* hoặc bị *Yêu cầu chỉnh sửa*.
- **Người duyệt — Trưởng bộ phận / Quản lý điều phối** (`vehicle_booking:approve`): Duyệt · Yêu cầu
  chỉnh sửa · Từ chối phiếu *Chờ duyệt*.
- **Điều phối viên** (`booking_dispatcher`, `vehicle_booking:write` phạm vi `all`): **Điều phối** —
  gán 1 xe + 1 tài xế; phân lại khi tài xế từ chối.
- **Quản lý điều phối** (`booking_manager`): như điều phối viên + quản danh mục Xe/Tài xế
  (`vehicle`/`driver` create/write/delete).
- **Tài xế** (`booking_driver`, `vehicle_booking:write` phạm vi `assigned`): thao tác trên chuyến
  **được phân cho chính mình** — Chấp nhận · Từ chối chuyến · Bắt đầu · Hoàn tất.
- **Người có `vehicle_booking:write`** không phải tài xế (admin/điều phối): được thao tác **thay** tài
  xế khi cần (tài xế báo qua điện thoại).

> **Phạm vi dữ liệu.** `vehicle_booking` lọc theo `company_id` / `department_id` / `created_by`
> (`core/scoping.py`). Nhánh **`assigned`** (dùng cho vai trò Tài xế): thấy phiếu **mình tạo** +
> phiếu **được phân cho mình** (nối qua `Driver.user_id`). `vehicle` và `driver` khai **PUBLIC**
> (danh mục dùng chung, không lọc theo pháp nhân).

## Vòng đời trạng thái phiếu (`status`)

| Mã (SMALLINT) | Tên hiển thị | Ý nghĩa | Nút thao tác hiển thị |
|---|---|---|---|
| `1` | Nháp | Đang soạn, chưa gửi duyệt | Lưu nháp · Gửi duyệt · Sửa · Xóa |
| `2` | Chờ duyệt | Đã gửi, đợi người duyệt | **Duyệt · Yêu cầu chỉnh sửa · Từ chối** (nếu có `approve`) |
| `3` | Đã duyệt | Đã duyệt, chờ điều phối | **Điều phối** (nếu có `write`) |
| `4` | Điều phối | Đã phân xe/tài xế; theo dõi ở `driver_status` | Theo bước tài xế + **Điều phối lại** (khi tài xế từ chối) |
| `5` | Hoàn thành | Tài xế đã hoàn tất chuyến | (chỉ xem) |
| `6` | Từ chối | Người duyệt từ chối — khóa | (chỉ xem) |
| `7` | Đã hủy | Đã hủy — kết thúc | (chỉ xem) |
| `8` | Yêu cầu chỉnh sửa | Trả người tạo sửa rồi gửi lại | Lưu · Gửi duyệt lại · Sửa |

**Trạng thái tài xế (`driver_status`)** — tách riêng, chỉ có nghĩa khi phiếu ở *Điều phối*:
`0` chưa phân · `1` Chờ tài xế · `2` Đã nhận · `3` Đang đi · `4` Hoàn thành · `5` Tài xế từ chối.

**Điều kiện chuyển trạng thái** (backend `service.py`, kiểm quyền + trạng thái nguồn):

- `Nháp` / `Yêu cầu chỉnh sửa` → `Chờ duyệt`: người tạo (hoặc `write`) bấm **Gửi duyệt**; pass `validate()` (mục A/B). Lưu nháp thì không kiểm.
- `Chờ duyệt` → `Đã duyệt`: người có `approve` bấm **Duyệt** (`POST /{id}/approve`).
- `Chờ duyệt` → `Yêu cầu chỉnh sửa`: bấm **Yêu cầu chỉnh sửa** + nhập lý do (`/{id}/return`); lý do ghi vào ghi chú.
- `Chờ duyệt` → `Từ chối`: bấm **Từ chối** + nhập lý do (`/{id}/reject`).
- `Đã duyệt` (hoặc `Điều phối` khi tài xế từ chối) → `Điều phối`: điều phối viên chọn **1 xe + 1 tài xế** (`/{id}/dispatch`) → đặt `driver_status = Chờ tài xế`, ghi `dispatched_by/at`.
- `Điều phối` + tài xế: **Chấp nhận** (`/driver/accept`, Chờ tài xế → Đã nhận) · **Từ chối chuyến** (`/driver/reject` + lý do → Tài xế từ chối, chờ điều phối lại) · **Bắt đầu** (`/driver/start`, Đã nhận → Đang đi, chấm `actual_start_time`) · **Hoàn tất** (`/driver/complete`, Đang đi → phiếu *Hoàn thành* + `driver_status` Hoàn thành, chấm `actual_end_time`, ghi km/chi phí).
- Chốt chặn tài xế: `_ensure_can_drive` — người **là tài xế** chỉ đụng được chuyến của mình; người **không phải tài xế** (admin/điều phối) được thao tác thay.

> **Lưu ý — luồng duyệt hiện tại.** Các bước Duyệt/Trả/Từ chối là **chuyển trạng thái trực tiếp theo
> quyền `approve`**, **CHƯA** chạy qua engine đa-bước của `approval_flow`. Đã tạo sẵn **luồng duyệt
> cấu hình** "Duyệt yêu cầu đặt xe" (entity `vehicle_booking`, 2 bước) ở `/approval/flows`, nhưng
> *runtime bridge* (`entity_hooks.register` + `ApprovalSwitch`) là việc của phase sau — xem
> `doc/dat-xe-duyet-dau/`.

Chỉ trạng thái **Nháp** và **Yêu cầu chỉnh sửa** cho sửa nội dung phiếu (`EDITABLE_STATUSES`); sau khi
vào luồng thì khóa.

---

## A. Thông tin chung của phiếu (header)

### 1. Mã phiếu (`code`)
- Kiểu nhập: Tự động
- Mặc định: hệ thống sinh `DX{seq:03d}` khi tạo (không sửa)
- Bắt buộc: — (tự sinh)
- Nguồn / liên kết: `generate_code(db, VehicleBooking, "DX")`
- Người sửa: Hệ thống

### 2. Loại yêu cầu (`request_type`)
- Kiểu nhập: Chọn (2 thẻ: *Đặt xe công tác* / *Đặt xe giao hàng*)
- Mặc định: `1` (công tác)
- Bắt buộc: Có
- Nguồn / Giá trị: `1` = công tác (chở người) · `2` = giao hàng (chở hàng)
- Người sửa: Người tạo khi phiếu còn sửa được
- Logic: quyết định bộ trường ở mục B (khối riêng theo loại). Đổi loại thì đổi khối trường hiển thị.

### 3. Mục đích (`purpose`)
- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: **Có** (kiểm khi gửi duyệt: "Vui lòng nhập mục đích")
- Người sửa: Người tạo / `write`, khi phiếu sửa được

### 4. Điểm đi / Điểm lấy hàng (`start_location`)
- Kiểu nhập: Nhập tay
- Mặc định: "Văn phòng Degoholding"
- Bắt buộc: **Có** (nhãn đổi theo loại: *Điểm đi* / *Điểm lấy hàng*)
- Người sửa: Người tạo / `write`

### 5. Điểm đến / Điểm giao hàng (`end_location`)
- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: **Có**
- Người sửa: Người tạo / `write`

### 6. Điểm dừng trung gian (`stops`)
- Kiểu nhập: Danh sách động — mỗi điểm gồm **Địa điểm** + **Tên người liên hệ** + **Số điện thoại**; thêm / xóa / đổi thứ tự (lên–xuống)
- Mặc định: rỗng
- Bắt buộc: Không
- Nguồn / lưu: JSON `list[StopItem]` (`{location, contact_name, contact_phone}`); backend bỏ điểm không có địa điểm, giữ thứ tự. **Tương thích ngược:** phần tử chuỗi (bản cũ) tự bọc thành `{location}`.
- Người sửa: Người tạo / `write`

### 7. Thời gian đi/lấy hàng · Thời gian về/giao (`start_time` · `end_time`)
- Kiểu nhập: Chọn ngày-giờ (`datetime-local`)
- Mặc định: trống
- Bắt buộc: **Có cả hai**; kiểm `end_time > start_time` ("Thời gian về/giao phải SAU thời gian đi/lấy hàng")
- Người sửa: Người tạo / `write`

### 8. Ghi chú (`note`)
- Kiểu nhập: Nhập nhiều dòng
- Mặc định: trống
- Bắt buộc: Không
- Logic: các lý do *Yêu cầu chỉnh sửa / Từ chối / Tài xế từ chối* được **ghi thêm** một dòng có nhãn vào ô này.

### 9. Người tạo & phạm vi (`requester`, `requester_id`, `department_id`, `company_id`)
- Kiểu nhập: Tự động (chụp từ hồ sơ nhân sự của người đăng nhập lúc tạo)
- Người sửa: Hệ thống
- Logic: dùng để `apply_scope` lọc phiếu theo công ty/phòng ban/chủ phiếu. Không có hồ sơ nhân sự → lấy email làm tên, phạm vi = 0.

---

## B. Khối riêng theo loại

### B.1 Đặt xe công tác (`request_type = 1`)
| Trường | Kiểu nhập | Bắt buộc | Ghi chú |
|---|---|---|---|
| Số hành khách (`passenger_count`) | Nhập số | **Có** (≥ 1) | Mặc định 1 |
| SĐT liên hệ (`contact_phone`) | Nhập tay | Không | |
| Người tham gia (`attendees`) | Nhập nhiều dòng | Không | Danh sách người đi cùng |
| Yêu cầu chuyến khứ hồi (`is_round_trip`) | Checkbox | Không | Chỉ hiện ở loại công tác |

### B.2 Đặt xe giao hàng (`request_type = 2`)
| Trường | Kiểu nhập | Bắt buộc | Ghi chú |
|---|---|---|---|
| Tên hàng hóa (`goods_name`) | Nhập tay | **Có** | |
| Kích thước / Khối lượng (`goods_size`) | Nhập tay | Không | VD "30x50x20cm, 5kg" |
| Người gửi + SĐT (`sender_name`, `sender_phone`) | Nhập tay | **Có cả hai** | |
| Người nhận + SĐT (`receiver_name`, `receiver_phone`) | Nhập tay | **Có cả hai** | |
| Chỉ dẫn đặc biệt (`special_instructions`) | Nhập nhiều dòng | Không | |

---

## C. Điều phối & chạy chuyến (chỉ xem trên chi tiết; điền qua thao tác)

| Trường | Nguồn | Ghi khi |
|---|---|---|
| Xe được phân (`assigned_vehicle_id` → nhãn biển số + mẫu) | danh mục Xe | Điều phối |
| Tài xế được phân (`assigned_driver_id` → tên) | danh mục Tài xế | Điều phối |
| Người/Thời gian điều phối (`dispatched_by`, `dispatched_at`) | tài khoản điều phối | Điều phối |
| Trạng thái tài xế (`driver_status`) | máy trạng thái | Các bước tài xế |
| Bắt đầu / Kết thúc thực tế (`actual_start_time`, `actual_end_time`) | mốc giờ khi Bắt đầu / Hoàn tất | Tài xế |
| Số km (`distance_km`) · Chi phí (`cost`) | tài xế nhập khi Hoàn tất | Hoàn tất |

Backend nối nhãn xe/tài xế theo **lô** (`serialize_bookings`, tránh N+1). Cờ `is_assigned_driver` (tính
theo người đang xem) để giao diện bày đúng cụm nút của tài xế.

---

## D. Danh mục Xe (`/api/vehicles`, entity `vehicle`)

CRUD chuẩn qua `make_crud_router` (khóa tự nhiên **biển số**, chặn trùng). Bảng: `tab_vehicle`.

| # | Trường | Kiểu nhập | Bắt buộc | Ghi chú |
|---|---|---|---|---|
| 1 | Nguồn (`is_external`) | Chọn (nút **Nội bộ / Thuê ngoài**) | Có | **Khóa khi sửa** |
| 2 | Loại nhà cung cấp (`supplier_type`) | Chọn (**Doanh nghiệp / Cá nhân**) — chỉ khi thuê ngoài | Có (thuê ngoài) | `0` none · `1` DN · `2` CN. **Khóa khi sửa** |
| 3 | Biển số / Tên xe (`license_plate`) | Nhập tay | **Có** (unique) | Nội bộ = biển số; thuê ngoài = tên gọi (xe không biển) |
| 4 | Mẫu xe (`model`) | Nhập tay | Không | VD "Toyota Hilux" |
| 5 | Loại xe (`type`) | Nhập tay | Không | Xe con / Xe tải / Xe bán tải — hiện kèm icon minh họa ở bảng |
| 6 | Tải (người/tấn) (`capacity`) | Nhập số | Không | **Float** — số chỗ hoặc tải trọng lẻ (2.4 / 6.8) |
| 7 | Trạng thái (`status`) | Chọn | Có | available (Sẵn sàng) · maintenance (Bảo trì) · inactive (Ngưng sử dụng) |
| 8 | Tên doanh nghiệp (`external_company`) | Nhập tay | **Có** (DN) | Chỉ khi thuê ngoài + Doanh nghiệp |
| 9 | Mã số thuế (`tax_code`) | Nhập tay | **Có** (DN) | |
| 10 | Địa chỉ thuế (`tax_address`) | Nhập tay | **Có** (DN) | |
| 11 | CCCD (`id_number`) | Nhập tay | Không (CN) | Chỉ khi thuê ngoài + Cá nhân |

## E. Danh mục Tài xế (`/api/drivers`, entity `driver`)

CRUD qua `make_crud_router` (không có cột duy nhất). Bảng: `tab_driver`.

| # | Trường | Kiểu nhập | Bắt buộc | Ghi chú |
|---|---|---|---|---|
| 1 | Nguồn (`is_external`) | Chọn (**Nội bộ / Thuê ngoài**) | Có | **Khóa khi sửa** |
| 2 | **Tài khoản nhân sự** (`user_id`) | **Tìm theo SĐT** (chỉ mode Nội bộ) | — | Nhập đủ SĐT → hiện danh sách (avatar + tên); chọn → giữ thẻ, tự điền Họ tên/SĐT/Email (khóa xám) |
| 3 | Loại nhà cung cấp (`supplier_type`) | Chọn (**Doanh nghiệp / Cá nhân**) — chỉ thuê ngoài | Có (thuê ngoài) | **Khóa khi sửa** |
| 4 | Họ tên (`name`) | Nội bộ: tự điền/khóa · Thuê ngoài: nhập tay | **Có** | |
| 5 | Số điện thoại (`phone`) | Nội bộ: tự điền/khóa · Thuê ngoài: nhập tay | **Có** | |
| 6 | Email (`email`) | Nội bộ: tự điền/khóa · Thuê ngoài: nhập tay | Không | |
| 7 | Số giấy phép lái xe (`license_number`) | Nhập tay | **Có** | Số GPLX (tách khỏi hạng) |
| 8 | Hạng GPLX (`license_class`) | Nhập tay | Không | B2 / C / D… |
| 9 | Trạng thái (`status`) | Chọn | Có | available (Sẵn sàng) · on_leave (Nghỉ phép — badge vàng) · inactive (Ngưng sử dụng) |
| 10 | Tên DN · MST · Địa chỉ thuế (`external_company`, `tax_code`, `tax_address`) | Nhập tay | **Có** (DN) | Địa chỉ thuế bắt buộc |
| 11 | CCCD (`id_number`) | Nhập tay | Không (CN) | |

> **Đã chốt:** "Cấp ID/PW riêng" cho tài xế thuê ngoài **tạm bỏ** (chưa tạo tài khoản đăng nhập cho
> tài xế ngoài). Nguồn (nội bộ/thuê ngoài) và loại NCC (DN/CN) **không đổi được sau khi tạo**.

Danh mục nội bộ hỗ trợ tìm nhân sự: `/api/users?search=<SĐT>` (backend tìm cả theo SĐT, trả kèm
`phone` · `contact_email` · `code` · `avatar`).

---

## Giao diện dùng chung (3 màn)

- **Badge trạng thái dạng "pill"** theo `po_badges_design.md`: Sẵn sàng = xanh lá · Bảo trì/Nghỉ phép
  = vàng · Ngưng dùng = xám; **Nguồn** Nội bộ = xanh dương / Thuê ngoài = hổ phách.
- **Thêm & Sửa mở TRANG riêng** (không popup) — case UI **C-02** (đảo C-01); trang sửa có nút **Xóa**
  + khối **Lịch sử thao tác** (`AuditTimeline`). Riêng **thao tác nhanh** (Điều phối / nhập lý do /
  Hoàn tất) vẫn là **popup**.
- **Sắp xếp theo cột** (server-side, whitelist cột thật) ở cả 3 bảng.
- **Nhân bản** phiếu đặt xe: bấm biểu tượng ở dòng → mở trang tạo mới đã chép nội dung (`/new?from=<id>`).

## Phân quyền

| Vai trò (mã) | Quyền chính | Phạm vi |
|---|---|---|
| Điều phối viên (`booking_dispatcher`) | `vehicle_booking` read/approve/cancel/write · `vehicle`/`driver` read | `all` |
| Quản lý điều phối (`booking_manager`) | như trên + `vehicle`/`driver` create/write/delete | `all` |
| Tài xế (`booking_driver`) | `vehicle_booking` read/write · `vehicle`/`driver` read | **`assigned`** |

Chi tiết thiết kế phân quyền hai trục: `doc/phan-quyen/Thiet_Ke_Phan_Quyen.md`.

## Liên quan

- Kế hoạch & tiến độ theo phase: `doc/dat-xe-duyet-dau/` (`README.md` + `TIEN-DO.md` + `phase-6-con-lai.md`).
- Case thiết kế giao diện đã chốt: skill `ui` (C-01 popup, **C-02** trang cho Đặt xe).
