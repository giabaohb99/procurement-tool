# TDD — REDESIGN PHÂN HỆ QUẢN LÝ KHO (Warehouse)

## Mini Tool Quản lý Thu Mua — DEGO Holding

| | |
|---|---|
| **Loại** | Technical Design Document (TDD) — thiết kế 1 phân hệ |
| **Phiên bản** | v0.1 (DRAFT — chờ duyệt nội bộ kỹ thuật) |
| **Ngày** | 2026-07-13 |
| **Liên quan** | [technical-design.md](technical-design.md) · [thiet-ke-ky-thuat-chi-tiet.md](thiet-ke-ky-thuat-chi-tiet.md) · [change-log.md](change-log.md) (CR-001) |
| **Trạng thái quyết định** | ✅ Giữ nguyên mã kho cũ · ✅ Kho nội bộ→`company_id`, kho đối tác→`supplier_code` |

> Tài liệu này mô tả **XÂY BẰNG CÁCH NÀO** cho việc quy hoạch lại danh mục Kho. **Chưa code** cho tới khi được duyệt (theo [quy-trinh-tai-lieu.md](quy-trinh-tai-lieu.md)).

---

## 1. Vấn đề & mục tiêu

### 1.1 Hiện trạng (đã đối chiếu code + seed)
`tab_warehouse` ([catalog/model.py](../../backend/app/modules/catalog/model.py)) hiện chỉ có `code / name / address / is_active`, dùng `make_crud_router` generic.

| Vấn đề | Bằng chứng |
|---|---|
| Thiếu liên kết công ty sở hữu | Không có cột `company_id` |
| Không phân biệt kho nội bộ vs đối tác | Kho thật của DEGO (C1-2, Lab Dego, B18…) nằm chung với "kho" là NCC bên ngoài (An Nông, Agama, Basel…) |
| Kho đối tác trùng danh mục NCC | `name` kho = tên pháp nhân NCC (vd "CÔNG TY TNHH TẬP ĐOÀN AN NÔNG") |
| Mã lộn xộn | "Kho C1-2", "Kho F49 - Icare", "Kho Lab Dego" (có dấu, khoảng trắng, viết thường) |

### 1.2 Mục tiêu
- Bổ sung **chủ sở hữu** và **phân loại** kho, hiển thị rõ ràng.
- Chuẩn hóa mã **cho kho tạo mới** mà **không phá vỡ dữ liệu đang có**.
- Không tạo trùng lặp với danh mục Nhà cung cấp.

### 1.3 Ngoài phạm vi (Out of scope) — *ghi rõ để chống "đẻ việc"*
- ❌ **KHÔNG đổi mã kho cũ** trong đợt này (xem Ràng buộc §2).
- ❌ **KHÔNG** chuyển tham chiếu từ `warehouse_code` (chuỗi) sang `warehouse_id` (FK) — vẫn dùng code làm khóa.
- ❌ **KHÔNG** gộp/di trú kho đối tác sang bảng NCC.

---

## 2. ⚠️ Ràng buộc cốt lõi — Mã kho là "khóa ngoại dạng chuỗi"

Toàn hệ thống **không dùng `warehouse_id`**; mọi nơi lưu **`warehouse_code` (string)**:

| Bảng | Cột | Bản ghi đang có |
|---|---|---|
| `tab_goods_receipt` | `warehouse_code` | 21 |
| `tab_po_item` | `warehouse_code` | 22 |
| `tab_purchase_request_item` | `warehouse` | 51 |
| `tab_inventory_*` (tồn kho, giao dịch) | `warehouse_code` | (có dữ liệu) |

> **Hệ quả:** đổi/chuẩn hóa mã kho ("Kho C1-2" → "C1_2") mà không migrate đồng loạt các cột trên sẽ **làm mồ côi tồn kho + lịch sử nhập + PO/PYC**.
> **Quyết định:** đợt này **giữ nguyên mã cũ**. Chỉ **thêm cột** + phân loại + owner. Việc chuẩn hóa mã cũ (nếu cần) sẽ là **CR riêng** kèm migration ánh xạ toàn bảng.

---

## 3. Mô hình dữ liệu — thay đổi `tab_warehouse`

### 3.1 Cột thêm mới

| Cột | Kiểu | Mặc định | Mô tả | Liên kết |
|---|---|---|---|---|
| `warehouse_type` | VARCHAR(20) | `"internal"` | `internal` = kho nội bộ (thuộc tập đoàn) · `partner` = kho đối tác/NCC/nhà máy | |
| `company_id` | BIGINT | `0` | Công ty thành viên sở hữu — **chỉ dùng khi `internal`** | → `tab_company.id` |
| `supplier_code` | VARCHAR(50) | `""` | NCC sở hữu — **chỉ dùng khi `partner`** | → `tab_supplier.code` |

Cột giữ nguyên: `code` (VARCHAR(25) UNIQUE, **không đổi giá trị cũ**), `name`, `address`, `is_active`.

### 3.2 Quy tắc hợp lệ (validate ở service)
- `warehouse_type = internal` → `company_id` bắt buộc (>0), `supplier_code` để trống.
- `warehouse_type = partner` → `supplier_code` bắt buộc (khớp NCC tồn tại), `company_id = 0`.
- **Mã kho tạo mới**: ép `^[A-Z0-9_]+$` (HOA, không dấu, không space, dùng `_`). **Mã cũ được miễn** (không validate lại khi sửa — `readonlyOnEdit`).
- `code` vẫn UNIQUE.

### 3.3 Cập nhật LLD
Bổ sung mục `tab_warehouse` vào [thiet-ke-ky-thuat-chi-tiet.md](thiet-ke-ky-thuat-chi-tiet.md) §3.1 (thay dòng "danh mục khác — cấu trúc đơn giản").

---

## 4. Migration (Alembic) — **an toàn, không đụng bảng khác**

1. `alembic revision --autogenerate -m "warehouse_add_type_owner"` → thêm 3 cột (default sẵn nên rows cũ không lỗi).
2. **Data migration phân loại** (viết bằng Python/SQLAlchemy trong migration — **KHÔNG** dùng SQL literal tiếng Việt, tránh mojibake theo [CLAUDE.md](../../CLAUDE.md)):
   - Danh sách **internal** (theo mã hiện có): `Dego Cần Thơ`, `Kho B18`, `Kho C1-2`, `Kho F49 - Icare`, `Kho Lab Dego`, `Kho Dr. Xanh` → `type=internal`, `company_id = <id DEGO>`.
   - Còn lại (Agama, Hà Long, Âu Việt, Basel, Niềm Tin Việt, Đại Tâm, Pesticidex, Yamato, ATC, Agrifuture, Thu Loan, Thái Nông, An Nông, ADU) → `type=partner`, `supplier_code = ` khớp theo tên với `tab_supplier` (fallback: để trống + đánh dấu để gán tay).
3. Không có bước nào chạm `tab_goods_receipt/po_item/purchase_request_item/inventory_*` → **0 rủi ro đứt liên kết**.

> Ghi chú map NCC: nhiều tên kho đối tác trùng tên NCC — migration sẽ match `LOWER(warehouse.name) == LOWER(supplier.name)`; case không match để trống, liệt kê ra log để nhập tay.

---

## 5. Backend — controller/service

Chuyển `warehouse` từ `make_crud_router` generic sang **controller viết tay nhẹ** (theo mẫu `contract`), để:
- Trả thêm `company_name`, `supplier_name` (resolve) cho danh sách/chi tiết.
- Lọc: `code`, `name` (LIKE), `company_id` (equals), `warehouse_type` (equals), `supplier_code`.
- Validate quy tắc §3.2 khi create/update.

Giữ RBAC entity `warehouse` như cũ (đã có trong `permissions.py`). Không thêm action mới.

---

## 6. Frontend — `cruds.tsx` (config-driven)

**Cột danh sách:**
| Cột | Nguồn |
|---|---|
| Mã kho | `code` |
| Tên kho | `name` |
| Chủ sở hữu | `company_name` (nội bộ) / `supplier_name` (đối tác) |
| Phân loại | badge: **Nội bộ** (navy) / **Đối tác** (cam đất) |
| Địa chỉ | `address` |
| Trạng thái | badge Hoạt động / Tạm khóa |

**Bộ lọc:** Công ty (SearchSelect `/api/companies`) · Loại kho (select nội bộ/đối tác) · Mã · Tên.

**Form thêm/sửa:** `code` (readonly khi sửa, hint định dạng) · `name` · `warehouse_type` (select) · `company_id` (select — hiện khi nội bộ) · `supplier_code` (select `/api/suppliers` — hiện khi đối tác) · `address` · `is_active`.
> Ẩn/hiện `company_id`/`supplier_code` theo `warehouse_type`: dùng `onValueChange` (đã có trong `FieldDef`) hoặc để cả 2 và validate ở save. Chốt ở bản triển khai.

---

## 7. Ảnh hưởng & tương thích ngược

| Khu vực | Ảnh hưởng |
|---|---|
| Tồn kho / GR / PO / PYC | **KHÔNG** — mã kho không đổi, tham chiếu string nguyên vẹn |
| Dropdown chọn kho ở PO/PYC/tồn kho | Không đổi (vẫn `/api/warehouses`); có thể lọc `internal` khi *nhận hàng* ở CR sau |
| Seed | `warehouses.json` bổ sung `warehouse_type` + owner; giữ `code` |

---

## 8. Test cases (phác thảo — QA)
1. Tạo kho nội bộ thiếu `company_id` → chặn.
2. Tạo kho đối tác thiếu `supplier_code` → chặn.
3. Tạo mã mới "kho abc" (thường/space) → chặn; "KHO_ABC" → OK.
4. Sửa kho cũ mã "Kho C1-2" (không đổi mã) → OK, không lỗi định dạng.
5. Sau migration: tồn kho/PO/PYC của "Kho C1-2" vẫn tra ra đúng (không mồ côi).
6. Lọc theo Công ty / Loại kho trả đúng.

---

## 9. Việc cần làm khi được duyệt (checklist triển khai)
- [ ] Model: thêm 3 cột vào `Warehouse`
- [ ] Migration autogenerate + data migration phân loại (Python)
- [ ] Controller/service viết tay + validate
- [ ] `cruds.tsx`: columns/filters/fields + badge loại kho
- [ ] Cập nhật `warehouses.json`
- [ ] Cập nhật LLD (`thiet-ke-ky-thuat-chi-tiet.md` §3.1) + sơ đồ ERD
- [ ] Test theo §8
- [ ] Ghi CR-001 "Đã hoàn tất" ở `change-log.md`

---

*DRAFT — chờ duyệt nội bộ kỹ thuật trước khi code (theo quy trình TDD).*
