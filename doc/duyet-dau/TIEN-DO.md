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

## PHA 0 — Nền & mô hình dữ liệu ✅ (05/09/2026)
> Chi tiết: [phase-0-nen-mo-hinh.md](phase-0-nen-mo-hinh.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [x] | `seal_request.status` **String→SmallInteger** + hằng số `SEAL_*` (R2) | `model.py` |
| [x] | Thêm cột `copies` (SmallInteger, số bản cần đóng dấu) | `model.py` |
| [x] | Migration `seal1status01` (đổi kiểu status + thêm copies) — bảng chưa có dữ liệu | đã `upgrade head`, status=SMALLINT |
| [x] | Khai `FILE_POLICY["seal_request"]` (pdf/ảnh, ≤50MB) | `core/file_registry.py` |
| [x] | Xác nhận scoping `seal_request` (company/dept/owner) + `seal_type` PUBLIC (đã có) | `core/scoping.py`, b07 test xanh |
| [x] | Vai trò seed: `seal_clerk` (Văn thư, company), `seal_approver` (TBP, dept), `seal_admin` (all) | `seed.py` STD_ROLES |
| [x] | Đăng ký nhãn `seal_request='Duyệt dấu'` vào `/approval/flows` (ENTITY_LABELS) | `entity-link.ts` (route thêm ở PHA 1) |

## PHA 1 — MVP phiếu + upload chứng từ + Danh mục Loại con dấu 🟡 (backend xong 05/09)
> Chi tiết: [phase-1-mvp-phieu-va-upload.md](phase-1-mvp-phieu-va-upload.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [x] | `service.py`: `create_seal_request` / `update` / list / `get` / delete (+ `_next_seal_code` DD###) | hand-write, có test |
| [x] | `schema.py`: Create/Update/Response + action inputs (ReasonIn/CompleteSealIn) | + nhãn status, join loại dấu/công ty(MST)/người tạo |
| [x] | `controller.py` + include_router `main.py` (prefix `/api/seal-requests`) | require + get_scoped |
| [x] | Validate **chứng từ chữ ký sống** (`doc_type="signed_doc"`) ≥1 khi gửi duyệt | `count_signed_docs` (reuse `attachment`) |
| [x] | Danh mục Loại con dấu: `catalog_controller.py` `make_crud_router` `/api/seal-types` + seed | `seed_seal_types.py` |
| [x] | FE: bật module (`enabled:true`, icon Stamp), route list/detail/new/edit + seal-types, `api/` + hooks | `approval-seal/` |
| [x] | FE: `SealRequestForm` (TRANG riêng) + khối tệp (tái dùng `DocumentAttachmentsCard entity="seal_request"`, mở tab/xem/tải) | C-02 |
| [x] | FE: danh sách `DataTable` + chi tiết (header back+badge, info người tạo, AuditTimeline) + `SealStatusBadge` | |
| [x] | FE: danh mục Loại con dấu (CrudListPage + popup) | `config/seal-type-crud.tsx` |
| — | ⚠️ Gate tệp nới thành **≥1 tệp bất kỳ** (`count_attachments`) — `DocumentAttachmentsCard` không gắn `doc_type=signed_doc`; tách signed_doc/note để PHA 4 | `service.py` |

## PHA 2 — Luồng duyệt 2 cổng (TBP + Văn thư) 🟡 (backend xong 05/09)
> Chi tiết: [phase-2-luong-duyet-2-cong.md](phase-2-luong-duyet-2-cong.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [x] | TBP: `approve_seal` · `return_seal` · `reject_seal` (endpoints `/approve /return /reject`) | kiểm trạng thái nguồn |
| [x] | Văn thư: `complete_seal` (đóng dấu xong, `copies`+ghi chú) · return/reject từ *Đã duyệt* (`/complete`, `/return-clerk`, `/reject-clerk`) | |
| [x] | Ghi lý do có nhãn vào `note` (`_append_note`) | service |
| [x] | Chốt chặn: `require` + trạng thái nguồn + `get_scoped`; TBP `approve`, Văn thư `write` | có test `test_duyet_dau.py` (7 ca) |
| [x] | FE: `SealWorkflowActions` bày nút theo vai trò + `seal-reason-dialog` / `seal-complete-dialog` (popup) | |

## PHA 3 — Thông báo & Email theo bước ✅ (05/09/2026)
> Chi tiết: [phase-3-thong-bao-va-email.md](phase-3-thong-bao-va-email.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [x] | `seal_request/notify.py`: sự kiện `dd_submitted/approved/returned/rejected/completed` | mẫu `vehicle_booking/notify.py`, best-effort |
| [x] | Duyệt xong → chuông + email **NSYC + Văn thư (lọc theo company) + Giám đốc (role `company_head` best-effort)** | wired vào service (submit/approve/return/reject/complete) |
| [x] | Mẫu email mặc định (`_wrap_seal` + 5 dd_* trong `DEFAULTS`) + biến `SEAL_VARIABLES` — tự hiện ở `/system/settings` | `email_template_service.py` |
| [x] | Loại trừ email — dùng chung `email_exclusion` (`send_event_email` đã gọi `filter_recipients`), dd_* tự vào bộ lọc | không cần code thêm |
| [x] | Test `test_duyet_dau_thong_bao.py` (3 ca: báo người tạo khi duyệt/trả · im khi không người nhận) | |
| — | ⚠️ "Giám đốc" = vai trò `company_head` (chưa có vai trò giám đốc chuẩn) — chốt ở quyết định A | |

## PHA 4 — Đồng bộ UI/UX + bản in + nhân bản 🟡 (05/09/2026)
> Chi tiết: [phase-4-dong-bo-ui-va-ban-in.md](phase-4-dong-bo-ui-va-ban-in.md).

| TT | Việc | Ghi chú |
|---|---|---|
| [x] | Header có nút back + tiêu đề = Mục đích + badge | `SealPageHeader` (từ PHA 1) |
| [x] | Bản in phiếu (`/print/approval-seal/:id`) — nhúng ảnh chứng từ (fetch attachments, `<img>`), liệt kê PDF | `seal-request-print-page.tsx` + route ở `app-router.tsx` |
| [x] | Nhân bản phiếu (`/new?from=<id>`, prefill trừ code/status/tệp) — nút ở chi tiết + dòng danh sách | |
| [x] | Nút **In phiếu** ở chi tiết | |
| [x] | Badge pill + confirm dialog + sort cột (dùng chung) | có từ PHA 1 |
| [ ] | Tách khối **chứng từ chữ ký sống** vs **ảnh ghi chú** (`doc_type` signed_doc/note) — **HOÃN** (đang dùng chung `DocumentAttachmentsCard`; cần UI 2 khối riêng, chờ khách quyết có làm không) | |

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
