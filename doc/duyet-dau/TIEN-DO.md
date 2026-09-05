# TIẾN ĐỘ — Phân hệ Duyệt dấu

Nhánh: **`pltgiang`**. Ký hiệu: `[ ]` chưa làm · `[~]` đang làm · `[x]` xong.
Tổng quan & đặc tả: [README.md](README.md).

## Chạy local để test
```bash
docker compose up -d db api erp            # http://localhost:8083/approval-seal
# Nạp danh mục + dữ liệu mẫu (sau khi làm phase 0–1):
docker compose exec -T api python -m scripts.seed_seal_types
docker compose exec -T api python -m scripts.seed_duyetdau_demo
# Cổng kiểm frontend trước khi giao:
docker compose exec erp npm run check       # typecheck + lint + test
# Cổng kiểm backend:
docker compose exec -T api python -m pytest test/backend -q
```

---

## PHA 0 — Nền & mô hình dữ liệu
> Chi tiết: [phase-0-nen-mo-hinh.md](phase-0-nen-mo-hinh.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [ ] | `seal_request.status` **String→SmallInteger** + hằng số `SEAL_*` (R2) | `model.py` |
| [ ] | Thêm cột `copies` (SmallInteger, số bản cần đóng dấu) | `model.py` |
| [ ] | Migration `seal1status01` (đổi kiểu status + thêm copies) — bảng chưa có dữ liệu | `migrations/versions/` |
| [ ] | Khai `FILE_POLICY["seal_request"]` (pdf/ảnh, dung lượng tối đa) | `core/file_registry.py` |
| [ ] | Xác nhận scoping `seal_request` (company/dept/owner) + `seal_type` PUBLIC (đã có) | `core/scoping.py` |
| [ ] | Vai trò seed: `seal_clerk` (Văn thư), `seal_admin` (Quản trị con dấu) + cấp `seal_request:approve` cho TBP | `seed.py` (STD_ROLES) |
| [ ] | Đăng ký entity `seal_request` vào `/approval/flows` (ENTITY_LABELS/ROUTES, `entity-link.ts`) | frontend-v2 |

## PHA 1 — MVP phiếu + upload chứng từ + Danh mục Loại con dấu
> Chi tiết: [phase-1-mvp-phieu-va-upload.md](phase-1-mvp-phieu-va-upload.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [ ] | `service.py`: `create_seal_request` / `update` / list / `get` / delete (+ `_next_seal_code` DD###) | hand-write |
| [ ] | `schema.py`: bổ sung Create/Update/Response + action inputs (ReasonIn/CompleteIn) | |
| [ ] | `controller.py` + include_router `main.py` (prefix `/api/seal-requests`) | require + get_scoped |
| [ ] | Upload **chứng từ chữ ký sống** (`doc_type="signed_doc"`) + validate ≥1 khi gửi duyệt | reuse `attachment` |
| [ ] | Danh mục Loại con dấu: `catalog_controller.py` `make_crud_router` `/api/seal-types` + seed | |
| [ ] | FE: bật module (`enabled:true`), route list/detail/new/edit, `api/` + hooks TanStack Query | `approval-seal/` |
| [ ] | FE: `SealRequestForm` (TRANG riêng) + khối upload + khối tệp (mở tab/xem/tải) | C-02 |
| [ ] | FE: danh sách `DataTable` + chi tiết + badge pill | |

## PHA 2 — Luồng duyệt 2 cổng (TBP + Văn thư)
> Chi tiết: [phase-2-luong-duyet-2-cong.md](phase-2-luong-duyet-2-cong.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [ ] | TBP: `approve_seal` · `return_seal` · `reject_seal` (endpoints `/approve /return /reject`) | kiểm trạng thái nguồn = Chờ duyệt |
| [ ] | Văn thư: `complete_seal` (đóng dấu xong, `copies`+ghi chú) · return/reject từ *Đã duyệt* | endpoint `/complete` |
| [ ] | Ghi lý do có nhãn vào `note` (`_append_note`) | service |
| [ ] | Chốt chặn: `require` + trạng thái nguồn + `get_scoped`; Văn thư phạm vi `company` | service + controller |
| [ ] | FE: `SealWorkflowActions` bày nút theo vai trò + dialog lý do / hoàn thành (popup) | |

## PHA 3 — Thông báo & Email theo bước
> Chi tiết: [phase-3-thong-bao-va-email.md](phase-3-thong-bao-va-email.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [ ] | `seal_request/notify.py`: sự kiện `dd_submitted/approved/returned/rejected/completed` | mẫu `vehicle_booking/notify.py` |
| [ ] | Duyệt xong → chuông + email **NSYC + Văn thư (theo company) + Giám đốc công ty** | recipient helpers |
| [ ] | Mẫu email mặc định (`DEFAULTS`) + đăng ký vào trang cài đặt `/system/settings` | `email_template_*` |
| [ ] | Loại trừ email theo cá nhân/phòng/công ty cho sự kiện Duyệt dấu | reuse `email_exclusion_*` |

## PHA 4 — Đồng bộ UI/UX + bản in + nhân bản
> Chi tiết: [phase-4-dong-bo-ui-va-ban-in.md](phase-4-dong-bo-ui-va-ban-in.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [ ] | Header có nút back + tiêu đề = Mục đích + badge (mẫu `booking-page-header.tsx`) | |
| [ ] | Ghi chú **đính kèm ảnh** (`doc_type="note"`) hiển thị inline | |
| [ ] | Bản in phiếu (`/print/approval-seal/:id`) — kèm ảnh chứng từ chữ ký sống | |
| [ ] | Nhân bản phiếu (`/new?from=<id>`, không chép tệp) | |
| [ ] | Badge pill + confirm dialog + sort cột (dùng chung) | |

## PHA 5 — Runtime luồng duyệt + test tổng thể + phân quyền
> Chi tiết: [phase-5-runtime-duyet-va-test.md](phase-5-runtime-duyet-va-test.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [ ] | `seal_request/approval_bridge.py` (register 4 kết cục + subject + reader) + `block_legacy_path` | mẫu Đặt xe |
| [ ] | `_after_submit` mở phiên khi cờ `ApprovalSwitch` bật; tắt = đường cũ (tương thích ngược) | |
| [ ] | FE: `SealApprovalPanel` (Duyệt/Trả/Từ chối qua engine + dấu vết), ẩn nút cũ khi `approval_running` | reuse `ApprovalActionDialog` |
| [ ] | Test tổng thể tầng service: happy path 2 cổng + nhánh trả/từ chối (TBP & Văn thư) + bắt buộc tệp | `test_duyet_dau_tong_the.py` |
| [ ] | Kịch bản phân quyền: NS(own) · TBP(dept) · Văn thư(company) · Giám đốc(company) · seal_admin(all) | `test_duyet_dau_phan_quyen.py` |
| [ ] | ↳ E2E trình duyệt (Playwright) cho luồng 2 cổng | host-run, cần tài khoản demo |

---
> **Quyết định còn mở (chờ khách chốt — xem §4 README):** (A) Giám đốc chỉ nhận thông báo hay thêm cổng
> duyệt · (B) Văn thư trả → gửi lại về TBP hay thẳng Văn thư · (C) chọn TBP thủ công hay auto theo phòng ban.
