# TIẾN ĐỘ — Phân hệ Đặt xe nội bộ

Nhánh: **`pltgiang`**. Ký hiệu: `[ ]` chưa làm · `[~]` đang làm · `[x]` xong.
Tổng quan & đặc tả: [README.md](README.md).

## Chạy local để test
```bash
docker compose up -d db api erp            # http://localhost:8083/vehicle-booking
# Nạp dữ liệu mẫu:
docker compose exec -T api python -m scripts.seed_vehicles
docker compose exec -T api python -m scripts.seed_drivers
docker compose exec -T api python -m scripts.seed_datxe_demo
# Cổng kiểm frontend trước khi giao:
docker compose exec erp npm run check       # typecheck + lint + test
```

---

## PHA 0 — Nền & mô hình dữ liệu ✅
| TT | Việc | Ghi chú |
|---|---|---|
| [x] | Model `Vehicle · Driver · VehicleBooking` (SMALLINT trạng thái/loại + hằng số, R2) | `model.py` |
| [x] | Khai phạm vi `vehicle_booking` (company/dept/owner), `vehicle`/`driver` = PUBLIC | `core/scoping.py` |
| [x] | Nhánh phạm vi `assigned` cho tài xế (thấy phiếu được phân qua `Driver.user_id`) | `core/scoping.py` |
| [x] | 3 vai trò seed: `booking_dispatcher · booking_manager · booking_driver` | `seed.py` (STD_ROLES) |
| [x] | Đăng ký entity `vehicle_booking` vào `/approval/flows` (ENTITY_LABELS/ROUTES) | `entity-link.ts` |

## PHA 1 — MVP phiếu (tạo & theo dõi) ✅
| TT | Việc | Ghi chú |
|---|---|---|
| [x] | Tạo phiếu 2 loại (công tác/giao hàng), lưu nháp / gửi duyệt | `service.create_booking` |
| [x] | Điểm dừng trung gian (địa điểm + tên + SĐT người liên hệ), đổi thứ tự | `schema.StopItem` |
| [x] | Danh sách + chi tiết + sửa (chỉ khi Nháp / Yêu cầu chỉnh sửa) | controller + page |
| [x] | Badge trạng thái phiếu + nhãn tiếng Việt (số + label ở API) | `status-pill.tsx` |

## PHA 2 — Danh mục Xe & Tài xế ✅
| TT | Việc | Ghi chú |
|---|---|---|
| [x] | CRUD Xe & Tài xế (`make_crud_router` /api/vehicles, /api/drivers) | `catalog_controller.py` |
| [x] | `capacity` Integer→Float; tách `license_number` + `license_class` | migration `vcap2float01`, `drv1class01` |
| [x] | Nguồn Nội bộ/Thuê ngoài; thuê ngoài DN/CN + MST · địa chỉ thuế · CCCD | migration `drv2supplier01`, `veh2supplier01` |
| [x] | Tài xế nội bộ: tìm tài khoản nhân sự theo SĐT (avatar+tên), tự điền khóa xám | `/api/users` +search SĐT, `use-driver-account-search` |
| [x] | Icon minh họa loại xe (xe con/xe tải) + badge Nguồn/Trạng thái | `vehicle-type-icon.tsx` |
| [x] | Nạp dữ liệu thật: 13 xe + 13 tài xế | `seed_vehicles.py`, `seed_drivers.py` |

## PHA 3 — Điều phối & luồng nghiệp vụ theo vai trò ✅
| TT | Việc | Ghi chú |
|---|---|---|
| [x] | Điều phối: gán 1 xe + 1 tài xế → Điều phối / tài xế Chờ nhận | `service.dispatch_booking` |
| [x] | Người duyệt: Duyệt · Yêu cầu chỉnh sửa · Từ chối (kèm lý do) | endpoints `/approve /return /reject` |
| [x] | Tài xế: Chấp nhận · Từ chối chuyến · Bắt đầu · Hoàn tất (km/chi phí) | endpoints `/driver/*` |
| [x] | Chốt chặn: `_ensure_can_drive` (đúng tài xế được phân) + `require` | service + controller |
| [x] | Nút chuyển trạng thái bày theo vai trò trên trang chi tiết | `booking-workflow-actions.tsx` |
| [x] | Tạo luồng duyệt cấu hình "Duyệt yêu cầu đặt xe" (2 bước) + full test data | `seed_datxe_demo.py` |

## PHA 4 — Đồng bộ UI/UX ✅
| TT | Việc | Ghi chú |
|---|---|---|
| [x] | Badge "pill" theo `po_badges_design.md` (ok/warn/err/info/gray) | `status-pill.tsx` |
| [x] | Hộp xác nhận có style toàn cục (thay `window.confirm`) | `shared/ui/confirm-dialog.tsx` |
| [x] | Sắp xếp theo cột cho 3 bảng (server-side, whitelist cột thật) | `sortable` + `apply_sort` |
| [x] | Icon sedan tự vẽ cho menu Quản lý xe + thẻ phân hệ | `booking-type-icons.tsx` |
| [x] | Bảng Phân quyền `/hr/permissions` dạng cây + 3 vai trò Đặt xe + màu | `role-permission-matrix.tsx` |
| [x] | Chọn vai trò khi giao duyệt "theo vai trò" ở form node | `approval-node-form.tsx` |

## PHA 5 — Đưa Thêm/Sửa lên TRANG (bỏ popup) ✅
| TT | Việc | Ghi chú |
|---|---|---|
| [x] | Khung CRUD: thêm `createRoute` (nút Thêm điều hướng), bỏ popup danh mục | `shared/crud` |
| [x] | Trang Thêm/Sửa Xe (`/vehicles/new`, `/:id`) — `VehicleForm` | `vehicle-catalog-form-page.tsx` |
| [x] | Trang Thêm/Sửa Tài xế (`/drivers/new`, `/:id`) — `DriverForm` | `driver-catalog-form-page.tsx` |
| [x] | Trang Thêm/Sửa Yêu cầu (`/new`, `/:id/edit`, nhân bản `?from=`) — `BookingForm` | `vehicle-booking-form-page.tsx` |
| [x] | Khối **Lịch sử thao tác** + nút **Xóa** trên trang sửa | `AuditTimeline` |
| [x] | Ghi case **C-02** vào `/ui` (đảo C-01) | skill `ui` |

## PHA 6 — NÂNG CẤP ✅ (04/09/2026)
> Kế hoạch chi tiết từng việc (khung 7 mục): **[phase-6-con-lai.md](phase-6-con-lai.md)**.
> Cổng kiểm: pytest backend suite exit 0 · `npm run check` (typecheck/lint 0 lỗi · 1669 test) xanh.

| TT | Việc | Ghi chú |
|---|---|---|
| [x] | **Nối RUNTIME luồng duyệt** (backend): `approval_bridge.py` (register 4 kết cục + subject + reader), `_after_submit` mở phiên khi cờ bật, `block_legacy_path` chặn đường tắt | tương thích ngược (cờ tắt = đường cũ) + `test_dat_xe_luong_duyet_runtime.py` |
| [x] | ↳ Frontend: `BookingApprovalPanel` trên trang chi tiết (Duyệt/Trả/Từ chối qua engine + dấu vết), ẩn 3 nút duyệt cũ khi `approval_running` | tái dùng `ApprovalActionDialog` + `ApprovalTrailCard` |
| [x] | Màn **"Chuyến của tôi"** (`/vehicle-booking/my-trips`) cho tài xế — lọc `?mine=1` (`filter_my_trips`) | `my-trips-page.tsx` + test |
| [x] | **Chống trùng giờ** khi điều phối (giáp ranh không tính) | `_find_time_conflict` + test |
| [x] | **Nguồn tài xế theo vai trò** khi điều phối — `/api/dispatch/drivers` (`drivers_for_dispatch`) | thuê ngoài + nội bộ giữ vai trò `booking_driver` + test |
| [x] | **Thông báo & Email** theo bước (TBP duyệt → chuông+email tới Điều phối viên) | `vehicle_booking/notify.py` + test |
| [x] | **Trang cài đặt email** trong `/system/settings`: bật/tắt + sửa HTML + xem trước + gửi thử | `tab_email_template` + `EmailTemplatePanel` |
| [x] | **Bản in** phiếu đặt xe (`/print/vehicle-booking/:id`) | `vehicle-booking-print-page.tsx` + nút "In phiếu" ở chi tiết |
| [x] | **Kịch bản 6 bước tự động** (integration, tầng service) | `test_dat_xe_luong_6_buoc.py` (happy path + trả/từ chối) |
| [ ] | ↳ E2E trình duyệt (Playwright) cho 6 bước | cần host + tài khoản demo 3 vai trò — chạy trên host |
| — | (Quyết định) Đưa dialog thao tác nhanh lên trang | **GIỮ POPUP** (case C-01) — không làm trừ khi có yêu cầu |
| — | (Quyết định) Cấp ID/PW cho tài xế thuê ngoài | **TẠM BỎ** (§4.3 README) — làm khi có nhu cầu thật |

---
> **PHA 6 xong** — mọi việc lõi đã làm & kiểm. Còn lại chỉ 2 quyết định (giữ popup · tạm bỏ cấp tài
> khoản tài xế ngoài) và 1 việc host-run (E2E trình duyệt). Không mục nào chặn dùng hằng ngày.
