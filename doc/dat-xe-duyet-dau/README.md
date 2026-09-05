# Kế hoạch: Phân hệ ĐẶT XE NỘI BỘ (DEGO Booking Auto)

> **Trạng thái tổng quát (03/09/2026):** MVP + danh mục + luồng nghiệp vụ theo vai trò + đồng bộ
> UI/UX + đưa Thêm/Sửa lên trang — **ĐÃ XONG (PHA 0→5)**. Còn lại: **nối runtime luồng duyệt**,
> **"Chuyến của tôi"**, **chống trùng giờ**, **thông báo**, và vài việc phụ (PHA 6). Xem log ở
> [TIEN-DO.md](TIEN-DO.md).

Nhánh làm việc: **`pltgiang`** (frontend-v2 + backend). Phân hệ chạy ở menu **Đặt xe**
(`/vehicle-booking`), gồm 3 màn chính: **Yêu cầu đặt xe · Quản lý xe · Quản lý tài xế**.

## Mục lục (theo thứ tự làm)

| Tài liệu | Nội dung |
|---|---|
| **README.md** *(file này)* | Tổng quan · mô hình dữ liệu · chi tiết chức năng · quyết định đã chốt |
| [TIEN-DO.md](TIEN-DO.md) | Log tick từng đầu việc theo PHA 0→6 + lệnh chạy local |
| [phase-0-nen-mo-hinh.md](phase-0-nen-mo-hinh.md) | ✅ Nền: model R2, phạm vi quyền, vai trò, đăng ký entity duyệt |
| [phase-1-mvp-phieu.md](phase-1-mvp-phieu.md) | ✅ MVP phiếu: 2 loại, điểm dừng, danh sách/chi tiết/sửa |
| [phase-2-danh-muc-xe-tai-xe.md](phase-2-danh-muc-xe-tai-xe.md) | ✅ Danh mục Xe & Tài xế: nguồn/NCC, tìm tài khoản, migration, seed |
| [phase-3-dieu-phoi-luong-nghiep-vu.md](phase-3-dieu-phoi-luong-nghiep-vu.md) | ✅ Điều phối + luồng nghiệp vụ theo vai trò (duyệt/trả/từ chối · tài xế) |
| [phase-4-5-dong-bo-ui-va-len-trang.md](phase-4-5-dong-bo-ui-va-len-trang.md) | ✅ Đồng bộ UI/UX + đưa Thêm/Sửa lên TRANG (C-02) |
| [phase-6-con-lai.md](phase-6-con-lai.md) | ✅ **Nâng cấp — đã làm & kiểm** (runtime duyệt + panel duyệt · Chuyến của tôi · chống trùng giờ · lọc tài xế · thông báo & email + trang cài đặt/template HTML · bản in · test 6 bước); còn E2E trình duyệt (host-run) |
| [test-phan-quyen.md](test-phan-quyen.md) | **Kịch bản kiểm tra phân quyền tay** — 7 tài khoản test (NS/TP/ĐPV/Tài xế) + các ca xem/quyền, dùng nút Đổi tài khoản nhanh |
| [../tai-lieu-chuc-nang/16-dat-xe.md](../tai-lieu-chuc-nang/16-dat-xe.md) | **Tài liệu chức năng** (đặc tả trường, vòng đời trạng thái, phân quyền) cho người dùng/BA |

> Mỗi phase một file chi tiết theo khung 7 mục — giống bộ [ke-hoach-celery](../ke-hoach-celery/) /
> [ke-hoach-import](../ke-hoach-import/). PHA 0→5 là **hồi cứu** (đã xong, ghi lại thiết kế + cái đã
> kiểm); PHA 6 là **kế hoạch phía trước**. §2–§4 dưới đây là bản tóm gọn xuyên suốt các phase.

## Quy ước chung (mọi phase tuân theo)
- **Tiếng Việt**, bám đúng code hiện tại (tên file/hàm/cột thật) — **nguồn sự thật là `model.py`**;
  khi tài liệu lệch code thì **mã đúng, tài liệu sai**, sửa tài liệu trong cùng đợt CR.
- **Rule R2 (QĐ-11):** cột nghĩa trạng thái/loại lưu **SMALLINT + hằng số nguyên**, API trả **số kèm
  nhãn**, tiếng Việt chỉ ở tầng hiển thị.
- Backend: gác quyền `require(entity, action)`, bó phạm vi `apply_scope`/`get_scoped`, ghi vết `audit`,
  phong bì `{success, message, data}`.
- Frontend: danh sách dùng `DataTable`; Thêm/Sửa là **TRANG riêng** (case UI **C-02**); màu qua token
  semantic; badge "pill" theo `po_badges_design.md`.
- **Khung mỗi file phase chi tiết:** *Mục tiêu · Phạm vi & việc cụ thể (checklist) · Thiết kế kỹ thuật ·
  Cấu hình · Chống trùng/Idempotent · Kiểm thử & tiêu chí · Rủi ro & lưu ý.*

---

## 0. Mục tiêu & phạm vi

Số hóa việc đặt xe nội bộ của DEGO: nhân sự tạo **yêu cầu đặt xe** (2 loại — *công tác* chở người /
*giao hàng* chở hàng), trưởng bộ phận **duyệt**, điều phối viên **phân xe + tài xế**, tài xế **nhận →
bắt đầu → hoàn tất**. Kèm hai danh mục nền **Xe** và **Tài xế** (nội bộ / thuê ngoài).

Ngoài phạm vi (chưa làm): tính cước tự động, GPS/định vị realtime, app riêng cho tài xế.

---

## 1. Kiến trúc & vị trí mã

| Lớp | Đường dẫn |
|---|---|
| Backend module | `backend/app/modules/vehicle_booking/` (`model.py · schema.py · service.py · controller.py · catalog_controller.py`) |
| Phạm vi quyền | `backend/app/core/scoping.py` (nhánh `vehicle_booking`, `vehicle`, `driver`) |
| Vai trò seed | `backend/app/seed.py` (`booking_dispatcher · booking_manager · booking_driver`) |
| Seed dữ liệu mẫu | `backend/scripts/seed_datxe_demo.py · seed_vehicles.py · seed_drivers.py` |
| Frontend module | `frontend-v2/src/modules/vehicle-booking/` (`pages/ · components/ · config/ · hooks/ · api/ · types/ · routes.tsx`) |

**Backend theo khuôn module chung:** `require(entity, action)` gác quyền + `apply_scope`/`get_scoped`
bó phạm vi; phong bì `{success, message, data}`. Danh mục Xe/Tài xế dùng `make_crud_router` (tự
require + scope + audit + CSV). Nghiệp vụ phiếu hand-write controller.

**Frontend:** danh sách dùng `DataTable`; form Thêm/Sửa **là TRANG riêng** (case UI **C-02**, đảo C-01);
các dialog thao tác nhanh (điều phối / nhập lý do / hoàn tất) vẫn là popup (C-01).

---

## 2. Mô hình dữ liệu

**Rule R2 (QĐ-11):** cột nghĩa trạng thái/loại lưu **SMALLINT + hằng số nguyên**, tiếng Việt chỉ ở
tầng hiển thị. Áp cho `request_type`, `status`, `driver_status`, `supplier_type`.

### `tab_vehicle` — Xe
`license_plate` (biển số / tên xe thuê ngoài, unique) · `model` · `type` (chuỗi: Xe con/Xe tải/Xe bán tải) ·
`capacity` **Float** (số chỗ hoặc tấn) · `status` (available/maintenance/inactive) · `is_external` ·
`external_company` · **`supplier_type`** (0 none·1 DN·2 CN) · `tax_code` (MST) · `tax_address` (địa chỉ thuế) · `id_number` (CCCD).

### `tab_driver` — Tài xế
`user_id` (liên kết tài khoản đăng nhập, nội bộ) · `name` · `email` · `phone` · `license_number` (số GPLX) ·
**`license_class`** (hạng B2/C/D) · `status` (available/on_leave/inactive) · `is_external` · `external_company` ·
**`supplier_type`** · `tax_code` · `tax_address` · `id_number`.

### `tab_vehicle_booking` — Yêu cầu đặt xe
`code` (DX###) · **`request_type`** (1 công tác·2 giao hàng) · `purpose` · lộ trình (`start_location`,
`end_location`, `stops` JSON — mỗi điểm có địa điểm + người liên hệ + SĐT) · `start_time`/`end_time` ·
khối công tác (`passenger_count`, `attendees`, `contact_phone`, `is_round_trip`) · khối giao hàng
(`goods_name`, `goods_size`, `sender_*`, `receiver_*`, `special_instructions`) · người tạo & phạm vi
(`requester`, `requester_id`, `department_id`, `company_id`) · **`status`** · điều phối
(`assigned_vehicle_id`, `assigned_driver_id`, `dispatched_by/at`, **`driver_status`**) · chạy thực tế
(`actual_start_time`, `actual_end_time`, `distance_km`, `cost`) · `note`.

**Bộ mã trạng thái phiếu:** 1 Nháp · 2 Chờ duyệt · 3 Đã duyệt · 4 Điều phối · 5 Hoàn thành ·
6 Từ chối · 7 Đã hủy · 8 Yêu cầu chỉnh sửa. **Trạng thái tài xế:** 0 chưa phân · 1 Chờ tài xế ·
2 Đã nhận · 3 Đang đi · 4 Hoàn thành · 5 Tài xế từ chối.

Migrations liên quan: `62540f5e1a14` (driver email + index), `vcap2float01` (capacity Float),
`drv1class01` (license_class), `drv2supplier01` (driver supplier), `veh2supplier01` (vehicle supplier).

---

## 3. Chi tiết chức năng

### 3.1 Yêu cầu đặt xe (`/vehicle-booking`)
- **Danh sách:** lọc theo loại/trạng thái/tìm nhanh, **sắp xếp theo cột** (mã, loại, mục đích, thời
  gian, người tạo, trạng thái), badge trạng thái dạng "pill", nút **Nhân bản** mỗi dòng.
- **Tạo / Sửa:** **TRANG riêng** (`/new`, `/:id/edit`, nhân bản `/new?from=<id>`) — 2 loại phiếu
  (công tác/giao hàng), lộ trình + điểm dừng trung gian (thêm/xóa/đổi thứ tự, người liên hệ mỗi
  điểm), khứ hồi, khối riêng theo loại, **Lưu nháp / Gửi duyệt**. Chỉ sửa được khi phiếu Nháp / bị
  Yêu cầu chỉnh sửa.
- **Chi tiết** (`/:id`): xem đầy đủ + **cụm nút chuyển trạng thái theo vai trò** + **Lịch sử thao tác**.

### 3.2 Quản lý xe (`/vehicle-booking/vehicles`)
- Danh sách: cột **Loại xe (kèm icon minh họa) · Biển số · Mẫu xe · Tải · Nguồn · Trạng thái**, sort,
  badge Nguồn (Nội bộ xanh / Thuê ngoài hổ phách) + Trạng thái.
- Thêm/Sửa **TRANG riêng**: nút **Nội bộ / Thuê ngoài**; thuê ngoài chọn **Doanh nghiệp / Cá nhân** →
  DN nhập Tên DN·MST·**Địa chỉ thuế (bắt buộc)**, CN nhập CCCD. Khóa nguồn + loại NCC khi sửa. Trang
  sửa có **Xóa** + **Lịch sử thao tác**.

### 3.3 Quản lý tài xế (`/vehicle-booking/drivers`)
- Danh sách: **Tên · Điện thoại · Số GPLX · Hạng · Nguồn · Trạng thái**, sort, badge (Nghỉ phép = vàng).
- Thêm/Sửa **TRANG riêng**: **Nội bộ** → tìm **tài khoản nhân sự theo số điện thoại** (kết quả chỉ hiện
  khi nhập đủ SĐT, hiện avatar + tên; chọn xong giữ thẻ đã chọn, tự điền Họ tên/SĐT/Email khóa xám),
  nhập thêm Số GPLX + Hạng. **Thuê ngoài** → Doanh nghiệp / Cá nhân + trường tương ứng (như xe). Khóa
  nguồn + loại NCC khi sửa. Trang sửa có **Xóa** + **Lịch sử thao tác**.

### 3.4 Luồng nghiệp vụ theo vai trò (trên trang chi tiết phiếu)
- **Người duyệt** (`approve`): Duyệt · Yêu cầu chỉnh sửa (lý do) · Từ chối (lý do).
- **Điều phối** (`write`): **Điều phối** (chọn 1 xe + 1 tài xế) → phiếu *Điều phối*, tài xế *Chờ nhận*.
- **Tài xế được phân** (`write`, đúng người): Chấp nhận · Từ chối chuyến (lý do, quay về điều phối) ·
  Bắt đầu (chấm giờ đi) · Hoàn tất (km + chi phí).
- Chốt chặn thật ở backend: `require` + `_ensure_can_drive` (chỉ tài xế được phân, người không phải
  tài xế được thao tác thay). Máy trạng thái đã kiểm end-to-end.

### 3.5 Phân quyền & luồng duyệt
- 3 vai trò seed: **Điều phối viên** (`booking_dispatcher`) · **Quản lý điều phối** (`booking_manager`) ·
  **Tài xế** (`booking_driver`, phạm vi `assigned` — thấy phiếu được phân qua `Driver.user_id`).
- Đã tạo **luồng duyệt cấu hình** "Duyệt yêu cầu đặt xe" (entity `vehicle_booking`, 2 bước: TBP người
  nộp → Quản lý điều phối theo vai trò) trên `/approval/flows`.

### 3.6 Đồng bộ UI/UX (dùng chung)
- **Badge "pill"** theo `po_badges_design.md`: `status-pill.tsx` (tông ok/warn/err/info/gray) +
  `SourceBadge` + `AvailabilityBadge`.
- **Hộp xác nhận có style toàn cục** `shared/ui/confirm-dialog.tsx` (thay `window.confirm`).
- **Icon sedan tự vẽ** cho menu Quản lý xe + thẻ phân hệ.

---

## 4. Các quyết định đã chốt
1. **Thêm/Sửa của 3 màn = TRANG riêng, không popup** (đảo case C-01 → **C-02** trong `/ui`). Dialog
   thao tác nhanh (điều phối/lý do/hoàn tất) vẫn popup.
2. **Nguồn** (nội bộ/thuê ngoài) và **loại nhà cung cấp** (DN/CN) **khóa khi sửa** — không đổi sau khi tạo.
3. **Tài xế thuê ngoài "cấp ID/PW riêng" → TẠM BỎ** (chưa tạo tài khoản đăng nhập cho tài xế ngoài).
4. Xe/tài xế thuê ngoài: **DN** cần Tên DN + MST + **Địa chỉ thuế (bắt buộc)**; **CN** nhập CCCD (không bắt buộc).
5. `capacity` là **Float** (chứa tải trọng lẻ 2.4 / 6.8 tấn); B2/C là **hạng** → cột `license_class`.
6. Luồng duyệt hiện là **chuyển trạng thái trực tiếp theo quyền** — **chưa** chạy qua engine đa-bước
   của `approval_flow` (bridge runtime tách riêng, xem PHA 6).

---

## 5. Các phase & tiến độ

| Phase | Nội dung | Trạng thái |
|---|---|---|
| **PHA 0** | Nền & mô hình dữ liệu (model, scoping, vai trò, đăng ký entity duyệt) | ✅ Xong — [phase-0](phase-0-nen-mo-hinh.md) |
| **PHA 1** | MVP phiếu — tạo/sửa/danh sách/chi tiết, 2 loại, điểm dừng | ✅ Xong — [phase-1](phase-1-mvp-phieu.md) |
| **PHA 2** | Danh mục Xe & Tài xế — CRUD + form nguồn/NCC + seed dữ liệu | ✅ Xong — [phase-2](phase-2-danh-muc-xe-tai-xe.md) |
| **PHA 3** | Điều phối & luồng nghiệp vụ theo vai trò + luồng duyệt cấu hình | ✅ Xong — [phase-3](phase-3-dieu-phoi-luong-nghiep-vu.md) |
| **PHA 4–5** | Đồng bộ UI/UX (badge/confirm/sort/icon) + đưa Thêm/Sửa lên TRANG | ✅ Xong — [phase-4-5](phase-4-5-dong-bo-ui-va-len-trang.md) |
| **PHA 6** | Nâng cấp — runtime duyệt, "Chuyến của tôi", chống trùng giờ, lọc tài xế, thông báo/email, bản in | ✅ Xong (trừ E2E trình duyệt) — [phase-6](phase-6-con-lai.md) |

Chi tiết từng đầu việc + log: **[TIEN-DO.md](TIEN-DO.md)** · Kế hoạch phần còn lại:
**[phase-6-con-lai.md](phase-6-con-lai.md)** · Tài liệu chức năng: **[../tai-lieu-chuc-nang/16-dat-xe.md](../tai-lieu-chuc-nang/16-dat-xe.md)**.
