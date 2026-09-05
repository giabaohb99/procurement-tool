# PHA 2 — Danh mục Xe & Tài xế ✅

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **ĐÃ XONG** (hồi cứu).

## Mục tiêu
Hai danh mục nền để điều phối chọn được: **Xe** và **Tài xế**, mỗi cái phân **Nội bộ / Thuê ngoài**;
thuê ngoài tách **Doanh nghiệp / Cá nhân** với đủ trường thuế/CCCD. Tài xế nội bộ **gắn tài khoản nhân
sự** (tìm theo SĐT). Nạp dữ liệu thật để dùng ngay.

## Phạm vi & việc đã làm
- [x] CRUD Xe & Tài xế qua `make_crud_router` (`/api/vehicles`, `/api/drivers`) — tự require + scope + audit + CSV.
- [x] `capacity` Integer → **Float**; tách `license_number` (số GPLX) + `license_class` (hạng).
- [x] Nguồn Nội bộ/Thuê ngoài; thuê ngoài DN/CN + **MST · địa chỉ thuế · CCCD** (`supplier_type` SMALLINT).
- [x] Tài xế nội bộ: **tìm tài khoản nhân sự theo SĐT** (avatar + tên), chọn → tự điền khóa xám.
- [x] Icon minh họa loại xe (xe con / xe tải) + badge Nguồn / Trạng thái.
- [x] Nạp dữ liệu thật: **13 xe + 13 tài xế**.

## Thiết kế kỹ thuật
| Việc | Vị trí |
|---|---|
| Router CRUD | `backend/app/modules/vehicle_booking/catalog_controller.py` (`make_crud_router` x2) |
| Schema | `schema.py` — `VehicleBase/Update/Response`, `DriverBase/Update/Response` (+ `supplier_type_label`) |
| Tìm tài khoản theo SĐT | `backend/app/modules/user/controller.py` + `service.py` — `/api/users?search=` khớp `Employee.phone`, trả thêm `code · phone · contact_email · avatar` |
| Hook tìm tài khoản | `frontend-v2/.../hooks/use-driver-account-search.*` |
| Form Xe / Tài xế | `components/vehicle-form.tsx` · `components/driver-form.tsx` (nút Nội bộ/Thuê ngoài, DN/CN, thẻ tài khoản đã chọn) |
| Icon loại xe | `components/vehicle-type-icon.tsx` (`VehicleTypeIcon` — tải→truck, else→car) |
| Badge nguồn/trạng thái | `components/status-pill.tsx` (`SourceBadge`, `AvailabilityBadge`) |
| Seed dữ liệu | `backend/scripts/seed_vehicles.py` (13) · `seed_drivers.py` (13) |

## Cấu hình / migration
Migration **viết tay** (chỉ đổi đúng ý định, không để autogenerate kéo drift):
| Revision | Nội dung |
|---|---|
| `62540f5e1a14` | driver email + index |
| `vcap2float01` | `capacity` Integer → Float |
| `drv1class01` | thêm `license_class` |
| `drv2supplier01` | tài xế: `supplier_type · tax_code · tax_address · id_number` |
| `veh2supplier01` | xe: `supplier_type · tax_code · tax_address · id_number` |

Chạy seed:
```bash
docker compose exec -T api python -m scripts.seed_vehicles
docker compose exec -T api python -m scripts.seed_drivers
```

## Chống trùng / Idempotent
- `license_plate` **unique** (chặn trùng biển số / tên xe).
- Seed dữ liệu idempotent theo biển số / tên tài xế (chạy lại không nhân đôi).

## Đã kiểm (tiêu chí hoàn thành)
- Tạo xe/tài xế nội bộ + thuê ngoài DN + thuê ngoài CN; khóa nguồn + loại NCC khi **sửa**.
- Tài xế nội bộ: nhập đủ SĐT → hiện danh sách nhân sự; chọn → điền khóa xám, chỉ nhập thêm GPLX + hạng.
- Badge nguồn (Nội bộ xanh / Thuê ngoài hổ phách) + trạng thái đúng màu.

## Rủi ro & lưu ý
- ⚠️ Tab/màn **mượn dữ liệu phân hệ khác** phải tự tắt query khi thiếu quyền (`enabled`/`can`) — tránh toast 403.
- Tài xế nội bộ seed để trống `license_number` (bắt buộc ở form) → khi sửa mới phải bổ sung.
- "Cấp ID/PW riêng" cho tài xế thuê ngoài **tạm bỏ** (xem quyết định §4.3 README).
