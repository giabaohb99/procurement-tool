# PHA 0 — Nền & mô hình dữ liệu ✅

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **ĐÃ XONG**.
> File này ghi hồi cứu (đã làm) theo khung 7 mục của bộ; phần "Kiểm thử" là cái đã được xác minh.

## Mục tiêu
Dựng lớp nền cho cả phân hệ: **mô hình dữ liệu** 3 bảng (Xe · Tài xế · Yêu cầu đặt xe) đúng **Rule R2**
(SMALLINT + hằng số), khai **phạm vi quyền** cho 3 entity, seed **3 vai trò**, và **đăng ký entity**
`vehicle_booking` vào màn cấu hình luồng duyệt. Không có nền này thì mọi màn/nghiệp vụ phía sau chỉ là
hình vẽ.

## Phạm vi & việc đã làm
- [x] Model `Vehicle · Driver · VehicleBooking` — cột nghĩa trạng thái/loại là **SMALLINT + hằng số**.
- [x] Khai phạm vi `vehicle_booking` (company / dept / owner); `vehicle` · `driver` = **PUBLIC**.
- [x] Nhánh phạm vi **`assigned`** cho tài xế (thấy phiếu được phân qua `Driver.user_id`).
- [x] 3 vai trò seed: `booking_dispatcher · booking_manager · booking_driver`.
- [x] Đăng ký entity `vehicle_booking` vào `/approval/flows` (nhãn + route).

## Thiết kế kỹ thuật
| Việc | Vị trí | Ghi chú |
|---|---|---|
| 3 model + hằng số | `backend/app/modules/vehicle_booking/model.py` | `BK_*` (trạng thái phiếu), `DRV_*` (trạng thái tài xế), `TYPE_*` (loại), `SUPPLIER_NONE/ENTERPRISE/INDIVIDUAL` + `SUPPLIER_TYPE_LABELS`; property `*_label` để API trả nhãn |
| Đăng ký entity vào `all_models` | `backend/app/core/all_models.py` | để `alembic --autogenerate` nhìn thấy bảng |
| Phạm vi | `backend/app/core/scoping.py` — `SCOPE_FIELDS["vehicle_booking"]` = company/dept/owner; `vehicle`/`driver` = `PUBLIC` | nhánh `assigned`: khớp `created_by` **OR** `assigned_driver_id` (subquery `Driver.user_id == user.id`) |
| Vai trò | `backend/app/seed.py` (`STD_ROLES`) | `booking_driver` phạm vi mặc định `assigned` |
| Đăng ký entity duyệt (FE) | `frontend-v2/src/modules/approval/.../entity-link.ts` (ENTITY_LABELS / ROUTES) | để `/approval/flows` chọn được `vehicle_booking` |

**Bộ mã (R2):** phiếu `status` 1 Nháp · 2 Chờ duyệt · 3 Đã duyệt · 4 Điều phối · 5 Hoàn thành ·
6 Từ chối · 7 Đã hủy · 8 Yêu cầu chỉnh sửa. Tài xế `driver_status` 0 chưa phân · 1 Chờ tài xế ·
2 Đã nhận · 3 Đang đi · 4 Hoàn thành · 5 Tài xế từ chối. `request_type` 1 công tác · 2 giao hàng.
`supplier_type` 0 none · 1 DN · 2 CN.

## Cấu hình / migration
- Migration tạo bảng nền cho `tab_vehicle · tab_driver · tab_vehicle_booking` (các cột bổ sung ở PHA 2).
- Không thêm ENV.

## Chống trùng / Idempotent
- Seed vai trò idempotent (chạy lại không tạo trùng) — theo cơ chế `seed.py`.
- ⚠️ Prod chạy `seed_prod.py`, **không** ghi đè phân quyền đã sửa trên UI; đổi `STD_ROLES` cần
  `SEED_FORCE_SYNC=true` một lần rồi trả `false` (xem CLAUDE.md).

## Đã kiểm (tiêu chí hoàn thành)
- `test_pham_vi_khai_du_b07.py` vẫn 44/44 sau khi khai 3 entity (đủ SCOPE_FIELDS, không rơi `false()`).
- Đăng nhập 3 vai trò seed → thấy đúng entity quyền; `/approval/flows` chọn được `vehicle_booking`.

## Rủi ro & lưu ý
- Thêm entity mà **quên khai `SCOPE_FIELDS`** → chặn sạch (`false()`) + log `app.scoping`, và test đỏ.
- `end_time`/`start_time` lưu **chuỗi ISO** (String) chứ không phải DateTime — nhất quán khi so sánh giờ
  ở PHA 6 (chống trùng giờ) phải parse.
