# PHA 1 — MVP phiếu + Upload chứng từ chữ ký sống + Danh mục Loại con dấu

> Tổng quan: [README.md](README.md) · Log: [TIEN-DO.md](TIEN-DO.md). Trạng thái: **CHƯA LÀM**.
> Khuôn 1-1: `vehicle_booking` (backend) + `vehicle-booking` (frontend-v2).

## Mục tiêu
Cho phép NSYC **tạo / sửa / theo dõi** yêu cầu đóng dấu (danh sách · chi tiết · trang Thêm/Sửa) và
**upload ảnh/PDF chứng từ có chữ ký sống**; dựng **Danh mục Loại con dấu**. Chưa có luồng duyệt
(để PHA 2) — mới tới *Nháp / Chờ duyệt*.

## Phạm vi & việc cụ thể
**Backend**
- [ ] `service.py`: `create_seal_request(db, data, user, submit)` · `update_seal_request` · `list_seal_requests` · `get_seal_request` (qua `get_scoped`) · `delete` (soft `is_deleted`). `_next_seal_code(db)` sinh `DD{max+1:03d}` (chỉ đếm `DD\d+`).
- [ ] `create`: `company_id` = `data.company_id` **hoặc** công ty người tạo (không đè khi đã chọn); chụp `requester/requester_id/department_id`.
- [ ] `validate_for_submit`: có **Mục đích · Loại con dấu · Công ty** và **≥ 1 tệp `signed_doc`** (đếm `FileLink` theo entity/id). Lưu nháp KHÔNG kiểm.
- [ ] `schema.py`: `SealRequestCreate/Update` (thêm `copies`, cho `company_id`), `SealRequestResponse` (kèm nhãn status, tên loại dấu, tên công ty + MST, thông tin người tạo, danh sách tệp).
- [ ] `controller.py`: `GET /` (list + `apply_scope` + filter/sort/paginate) · `GET /{id}` · `POST /` · `PATCH /{id}` · `DELETE /{id}` · `POST /{id}/submit`. Gác `require("seal_request", action)`.
- [ ] `main.py`: `include_router(seal_request_router, prefix="/api/seal-requests")` + catalog router.
- [ ] `all_models.py`: đã import (giữ nguyên).

**Đính kèm (tái dùng module `attachment`)**
- [ ] Upload chứng từ: FE gọi `POST /api/attachments` (`entity=seal_request`, `entity_id`, `doc_type=signed_doc`); liệt kê `GET /api/attachments?entity=seal_request&entity_id=`.
- [ ] Kiểm quyền upload kế thừa phiếu (parent entity `seal_request`) — có sẵn trong controller attachment.

**Danh mục Loại con dấu**
- [ ] `catalog_controller.py`: `make_crud_router(SealType, entity="seal_type", prefix="/api/seal-types")` (list/get/create/update/delete + audit).
- [ ] `scripts/seed_seal_types.py`: *Dấu tròn công ty · Dấu chức danh · Dấu treo · Dấu giáp lai*.

**Frontend-v2 (`modules/approval-seal/`)**
- [ ] Bật module: `routes.tsx` `enabled:true`; route `/approval-seal` (list), `/:id`, `/new`, `/:id/edit`, `/seal-types*`. Route constant ở `app-routes.ts` (thêm new/detail/edit như `vehicleBooking`).
- [ ] `api/seal-request-api.ts` + `hooks/use-seal-requests.ts` (TanStack Query, query-keys tập trung).
- [ ] `pages/seal-request-list-page.tsx` (`DataTable`, badge pill, nút Nhân bản) · `seal-request-detail-page.tsx` · `seal-request-form-page.tsx` (TRANG riêng).
- [ ] `components/`: `SealRequestForm` (mục đích/loại dấu/công ty/số bản/ghi chú + **khối upload chứng từ**), `AttachmentList` (mỗi tệp: **Mở tab mới · Xem · Tải**), `status-pill`.
- [ ] Danh mục Loại con dấu: khung Generic Declarative CRUD (`shared/crud`) — khai `seal-type-crud.tsx`.

## Thiết kế kỹ thuật
| Chức năng | Endpoint | Hàm service |
|---|---|---|
| Danh sách | `GET /api/seal-requests` | `list_seal_requests` |
| Chi tiết | `GET /api/seal-requests/{id}` | `get_seal_request` (get_scoped) |
| Tạo | `POST /api/seal-requests` (+`?submit=`) | `create_seal_request` |
| Sửa | `PATCH /api/seal-requests/{id}` | `update_seal_request` |
| Gửi duyệt | `POST /api/seal-requests/{id}/submit` | `submit_seal_request` |
| Xóa | `DELETE /api/seal-requests/{id}` | soft-delete |
| Tệp | `/api/attachments` (entity=seal_request) | module `attachment` |

- Serialize nối **lô**: tên loại dấu (`seal_type_id`), tên+MST công ty (`company_id`), thông tin người
  tạo (email/SĐT/vai trò từ hồ sơ nhân sự), danh sách tệp (`FileLink`) — tránh N+1 (khuôn `serialize_bookings`).
- Ô **chỉ xem** dùng `read-only-value.tsx`, **không** `<Input disabled>`; ô CHỌN kèm `copy-button`.
- Tệp: ảnh → **Xem trực tiếp** inline (`/preview`); PDF → **Mở tab mới** (`/view`); mọi loại có **Tải về** (`/download`).

## Cấu hình / migration
- Không thêm cột (đã xong ở PHA 0). Chỉ thêm code + seed danh mục.
```bash
docker compose exec -T api python -m scripts.seed_seal_types
docker compose exec erp npm run check
```

## Chống trùng / Idempotent
- `_next_seal_code` bỏ qua mã đã tồn tại (max+1, thử tiếp nếu trùng) — **không** dùng `count()` (đã là lỗi từng gặp ở Đặt xe: mã demo có chữ làm `int()` vỡ → về DD001 trùng).
- Seed loại con dấu idempotent theo `name` (unique).
- Nhân bản `?from=` **không** chép tệp đính kèm (chứng từ chữ ký sống là bản gốc từng phiếu).

## Kiểm thử & tiêu chí
- Tạo phiếu nháp → sửa → xóa; gửi duyệt **thiếu tệp signed_doc → 400**; có tệp → sang *Chờ duyệt*.
- Upload 1 PDF + 1 ảnh, chi tiết hiện 3 nút; ảnh xem inline, PDF mở tab mới, tải được.
- `apply_scope`: user `own` chỉ thấy phiếu mình tạo (test tầng service).
- `npm run check` xanh (typecheck/lint/test).

## Rủi ro & lưu ý
- **Bắt buộc tệp chỉ ở tầng gửi duyệt**, không chặn lưu nháp — chớ chặn nhầm lúc lưu.
- File 17 MB: kiểm `FILE_POLICY` cho phép dung lượng; FE báo tiến trình upload, chặn quá cỡ trước khi gửi.
- Chưa có nút Duyệt/Hoàn thành ở phase này — chỉ tạo/sửa/gửi duyệt; đừng lộ nút cổng 2 sớm.
