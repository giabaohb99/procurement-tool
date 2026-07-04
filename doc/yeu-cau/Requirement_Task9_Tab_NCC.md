# Requirement — Task 9: Tab "Khảo sát của NCC" trên trang Chi tiết Nhà cung cấp

> **Phiên bản:** 1.0  
> **Ngày soạn:** 2026-07-04  
> **Trạng thái:** Sẵn sàng triển khai  
> **Phụ thuộc:** Task 7 (gộp 2 phiếu khảo sát thành 1 giao diện) phải hoàn thành trước

---

## 1. Mục tiêu & Phạm vi

### 1.1 Làm ngay (Task 9)

Trên trang **Chi tiết Nhà cung cấp** (`/suppliers/:id`), thêm một tab mới tên **"Khảo sát của NCC"** bên cạnh 4 tab hiện có (Thông tin / Đánh giá / Hợp đồng / Công nợ).

Tab này có **2 sub-tab**:

| Sub-tab | Nguồn dữ liệu | Cách match |
|---|---|---|
| **KSNCC** (Khảo sát Nhà cung cấp) | `tab_survey_supplier_line` | `tax_code` của dòng = `tax_code` của NCC |
| **KSSP** (Khảo sát Sản phẩm) | `tab_survey_product_line` | `supplier_code` của dòng = `code` của NCC |

Người dùng click vào một dòng bất kỳ → mở phiếu khảo sát gốc tương ứng.

### 1.2 Tạm hoãn

**Tab "Sản phẩm của NCC"** (danh sách sản phẩm thực tế mà NCC đang cung cấp trong DB) **bị hoãn vô thời hạn** vì chưa có cơ chế liên kết giữa:
- "sản phẩm" xuất hiện trong phiếu khảo sát (`tab_survey_product_line.product_name`)
- và "sản phẩm thật" trong DB nội bộ (bảng inventory/product hiện có)

Xem chi tiết lý do và đề xuất kiến trúc tại **Mục 5**.

---

## 2. Cách match dữ liệu theo `tax_code`

### 2.1 Sơ đồ liên kết

```
tab_supplier
  .code        ──────────────────────────────► tab_survey_product_line.supplier_code
  .tax_code    ──► tab_survey_supplier_line.tax_code
               └──► (fallback) tab_survey_product_line qua supplier_code → lấy tax_code từ tab_supplier
```

### 2.2 Quy tắc match chi tiết

#### Sub-tab KSNCC — `tab_survey_supplier_line`

- Điều kiện lọc: `tab_survey_supplier_line.tax_code = <tax_code của NCC hiện tại>`
- `tax_code` có trong cả hai bảng (`tab_supplier.tax_code` và `tab_survey_supplier_line.tax_code`) nên match trực tiếp.

#### Sub-tab KSSP — `tab_survey_product_line`

- `tab_survey_product_line` **không có cột `tax_code`** trực tiếp; chỉ có `supplier_code`.
- Điều kiện lọc: `tab_survey_product_line.supplier_code = <code của NCC hiện tại>` (tức `tab_supplier.code`).
- Nếu sau này muốn match theo `tax_code` cho KSSP: cần join `tab_supplier` để chuyển `supplier_code → tax_code`, hoặc thêm cột `tax_code` vào `tab_survey_product_line` (hiện chưa có — **không làm trong task này**).

### 2.3 Rủi ro dữ liệu

| Tình huống | Ảnh hưởng | Xử lý |
|---|---|---|
| NCC có `tax_code = ""` (rỗng) | Sub-tab KSNCC không trả kết quả dù có dữ liệu khảo sát | Hiển thị cảnh báo: _"NCC chưa có mã số thuế — không thể tìm phiếu KSNCC"_ |
| `supplier_code` trong dòng khảo sát không trùng `code` NCC | KSSP bị lọt dữ liệu | Không xử lý tự động; cần nghiệp vụ nhập đúng khi khảo sát |
| Nhiều NCC trùng `tax_code` (nhập sai, hoặc chi nhánh) | Sub-tab KSNCC trả dữ liệu của nhiều NCC khác nhau | Hiển thị `supplier_name` trong bảng để người dùng phân biệt; ghi chú phía trên bảng |
| Dòng khảo sát có `tax_code` rỗng (không điền khi khảo sát) | Không match được | Hiển thị bình thường các dòng khác; dòng thiếu không hiện |

---

## 3. Màn hình

### 3.1 Vị trí chèn tab

File: `frontend/src/pages/SupplierDetail.tsx`

Mảng `TABS` hiện tại (dòng 11–16):

```typescript
const TABS = [
  { key: 'info',      label: 'Thông tin' },
  { key: 'eval',      label: 'Đánh giá' },
  { key: 'contracts', label: 'Hợp đồng' },
  { key: 'payables',  label: 'Công nợ' },
]
```

Thêm một entry mới **sau** `payables`:

```typescript
{ key: 'surveys', label: 'Khảo sát của NCC' },
```

Tab này **chỉ hiển thị** khi `!isNew` (không hiện khi đang tạo NCC mới) — giống các tab hiện có.

### 3.2 Cấu trúc tab "Khảo sát của NCC"

```
[Tab: Khảo sát của NCC]
  ┌───────────────────────────────────────────┐
  │  [Sub-tab: KSNCC]  [Sub-tab: KSSP]        │
  │  ─────────────────────────────────────── │
  │  (bảng dữ liệu tương ứng)                │
  └───────────────────────────────────────────┘
```

Nếu NCC không có `tax_code`:
- Sub-tab KSNCC: hiện banner cảnh báo thay cho bảng.
- Sub-tab KSSP: vẫn truy vấn bình thường theo `supplier_code`.

### 3.3 Sub-tab KSNCC — Các cột hiển thị

Nguồn: `tab_survey_supplier_line` + join `tab_survey` (lấy `code`, `status`, `received_date`)

| Cột | Nguồn trường | Ghi chú |
|---|---|---|
| Mã phiếu KS | `tab_survey.code` | Link mở phiếu khảo sát |
| Ngày tiếp nhận | `tab_survey.received_date` | |
| Trạng thái phiếu | `tab_survey.status` | Badge: Nháp / Chờ duyệt / Đã duyệt / Từ chối |
| Tên NCC (trong phiếu) | `supplier_line.supplier_name` | Cần khi nhiều NCC trùng tax_code |
| MST (trong phiếu) | `supplier_line.tax_code` | Để đối chiếu |
| Nhóm cung cấp | `supplier_line.supply_group` | |
| Đánh giá NV KD | `supplier_line.nvkd_eval` | |
| Độ tin cậy | `supplier_line.reliability` | |
| Kết quả duyệt dòng | `supplier_line.line_approve` | Duyệt / Không duyệt / (trống) |
| Thao tác | — | Nút "Xem phiếu" → `/surveys-supplier/:survey_id` |

### 3.4 Sub-tab KSSP — Các cột hiển thị

Nguồn: `tab_survey_product_line` + join `tab_survey` (lấy `code`, `status`, `received_date`)

| Cột | Nguồn trường | Ghi chú |
|---|---|---|
| Mã phiếu KS | `tab_survey.code` | Link mở phiếu khảo sát |
| Ngày tiếp nhận | `tab_survey.received_date` | |
| Trạng thái phiếu | `tab_survey.status` | Badge |
| Tên sản phẩm | `product_line.product_name` | |
| Thông số kỹ thuật | `product_line.spec` | Rút gọn nếu dài |
| Đơn vị báo giá | `product_line.quote_unit` | |
| MOQ | `product_line.moq` | |
| Đơn giá | `product_line.price_by_volume` | Định dạng số VN |
| VAT (%) | `product_line.vat` | |
| Kết quả duyệt dòng | `product_line.line_approve` | |
| Thao tác | — | Nút "Xem phiếu" → `/surveys-supplier/:survey_id` (sau Task 7 gộp phiếu) |

### 3.5 Hành vi click / điều hướng

- Click nút "Xem phiếu" (hoặc click vào dòng): navigate đến trang chi tiết phiếu khảo sát tương ứng.
- Route hiện tại: `/surveys-supplier/:id` (KSNCC) và `/surveys-product/:id` (KSSP) — **sau Task 7 gộp lại** chỉ còn một route. Document này ghi rõ cả hai để tương thích.
- Mở trong **cùng tab** (không mở tab mới), người dùng dùng nút back để quay lại.

### 3.6 Trạng thái rỗng

| Tình huống | Thông báo hiển thị |
|---|---|
| Chưa có dòng nào | _"Chưa có khảo sát nào liên kết với nhà cung cấp này."_ |
| NCC không có `tax_code` (KSNCC) | Banner vàng: _"Nhà cung cấp chưa có mã số thuế. Vui lòng cập nhật trong tab Thông tin để tra cứu phiếu KSNCC."_ |

---

## 4. API

### 4.1 Endpoint lấy dữ liệu KSNCC cho 1 NCC

```
GET /api/suppliers/{supplier_id}/survey-supplier-lines
```

**Query params (tùy chọn):**

| Param | Kiểu | Mô tả |
|---|---|---|
| `page` | int | Trang hiện tại (default: 1) |
| `page_size` | int | Số dòng mỗi trang (default: 50) |

**Logic backend:**
1. Lấy `tax_code` của NCC từ `tab_supplier` theo `supplier_id`.
2. Nếu `tax_code` rỗng → trả về `{ items: [], warning: "no_tax_code" }`.
3. Query: `SELECT ssl.*, s.code AS survey_code, s.status, s.received_date FROM tab_survey_supplier_line ssl JOIN tab_survey s ON s.id = ssl.survey_id WHERE ssl.tax_code = :tax_code ORDER BY s.id DESC`.
4. Phân trang.

**Response (thành công):**
```json
{
  "ok": true,
  "data": {
    "total": 12,
    "tax_code_used": "0123456789",
    "items": [
      {
        "id": 45,
        "survey_id": 7,
        "survey_code": "KS00007",
        "survey_status": "approved",
        "received_date": "2025-11-01",
        "supplier_name": "Công ty ABC",
        "tax_code": "0123456789",
        "supply_group": "Vật liệu xây dựng",
        "nvkd_eval": "Tốt",
        "reliability": "Cao",
        "line_approve": "Duyệt"
      }
    ]
  }
}
```

**Response khi NCC không có tax_code:**
```json
{
  "ok": true,
  "data": {
    "total": 0,
    "warning": "no_tax_code",
    "items": []
  }
}
```

---

### 4.2 Endpoint lấy dữ liệu KSSP cho 1 NCC

```
GET /api/suppliers/{supplier_id}/survey-product-lines
```

**Query params:** `page`, `page_size` (giống 4.1)

**Logic backend:**
1. Lấy `code` của NCC từ `tab_supplier` theo `supplier_id`.
2. Query: `SELECT spl.*, s.code AS survey_code, s.status, s.received_date FROM tab_survey_product_line spl JOIN tab_survey s ON s.id = spl.survey_id WHERE spl.supplier_code = :supplier_code ORDER BY s.id DESC`.
3. Phân trang.

**Response (thành công):**
```json
{
  "ok": true,
  "data": {
    "total": 5,
    "supplier_code_used": "ABC",
    "items": [
      {
        "id": 21,
        "survey_id": 7,
        "survey_code": "KS00007",
        "survey_status": "approved",
        "received_date": "2025-11-01",
        "product_name": "Thép hộp 40x40",
        "spec": "Dày 1.5mm, mạ kẽm",
        "quote_unit": "cây",
        "moq": 100,
        "price_by_volume": 85000,
        "vat": 8,
        "line_approve": "Duyệt"
      }
    ]
  }
}
```

### 4.3 Vị trí triển khai trong codebase

| Thành phần | File đề xuất |
|---|---|
| Router | `backend/app/modules/supplier/controller.py` — thêm 2 route phụ |
| Logic query | `backend/app/modules/supplier/service.py` — thêm 2 hàm |
| Schema response | `backend/app/modules/supplier/schema.py` |
| Frontend fetch | `frontend/src/pages/SupplierDetail.tsx` — thêm state + useEffect cho tab `surveys` |

### 4.4 Phân quyền API

- Yêu cầu: user đã đăng nhập, có quyền `survey.read` (xem phiếu khảo sát).
- Không cần quyền riêng cho 2 endpoint này — dùng lại `require("survey", "read")` của module survey.

---

## 5. Phần HOÃN — Tab "Sản phẩm của NCC"

### 5.1 Mô tả tính năng (chưa làm)

Tab "Sản phẩm của NCC" dự kiến hiển thị **danh sách sản phẩm thực tế** mà NCC đang cung cấp, kèm thông số giá tham chiếu — giúp nhân viên thu mua tra cứu nhanh mà không phải mở từng phiếu khảo sát.

### 5.2 Lý do hoãn

Hiện tại, thông tin sản phẩm của NCC chỉ tồn tại trong **`tab_survey_product_line`** (dạng text tự do: `product_name`, `spec`, `origin`...) và **không có liên kết** đến bất kỳ bản ghi sản phẩm nào trong DB nội bộ.

Cụ thể:
- `tab_survey_product_line` lưu `internal_code` (mã SP theo NCC, nhập tay khi khảo sát) nhưng không có foreign key sang bảng inventory/product.
- Không có bảng map `NCC ↔ sản phẩm nội bộ`.
- Nếu hiển thị trực tiếp từ khảo sát: dữ liệu trùng lặp, không chuẩn hóa, khó làm giá.

### 5.3 Đề xuất kiến trúc để làm sau (không code bây giờ)

Cần xây **1 bảng map riêng**, ví dụ:

```sql
-- Phương án A: Bảng product_supplier (đơn giản)
CREATE TABLE tab_product_supplier (
    id           BIGINT PRIMARY KEY AUTO_INCREMENT,
    supplier_id  BIGINT NOT NULL,   -- FK → tab_supplier.id
    product_id   BIGINT NOT NULL,   -- FK → tab_product.id (bảng sản phẩm nội bộ)
    supplier_sku VARCHAR(100),       -- Mã SP theo NCC (so khớp internal_code trong khảo sát)
    ref_price    DECIMAL(18,2),      -- Giá tham chiếu gần nhất
    last_survey_line_id BIGINT,      -- FK tùy chọn → tab_survey_product_line.id (dòng khảo sát gần nhất)
    is_active    BOOLEAN DEFAULT TRUE,
    updated_at   DATETIME,
    ...
);

-- Phương án B: Map trực tiếp survey_product_line ↔ product (phức tạp hơn)
-- Không khuyến nghị vì survey_product_line thay đổi theo từng phiếu
```

**Quy trình để làm sau:**
1. Xây `tab_product_supplier` (Phương án A).
2. Khi Admin duyệt một dòng KSSP (`line_approve = "Duyệt"`): cho phép "Lưu vào danh mục NCC" → tạo/cập nhật `tab_product_supplier`.
3. Tab "Sản phẩm của NCC" đọc từ `tab_product_supplier` join `tab_product`.

---

## 6. Phân quyền

| Quyền | Điều kiện | Mô tả |
|---|---|---|
| Xem tab "Khảo sát của NCC" | `survey.read = true` | Nhân viên thu mua, quản lý, admin |
| Xem chi tiết phiếu (khi click) | `survey.read = true` + scoping hiện tại | Giữ nguyên logic scoping của module survey |
| Không hiển thị tab | `survey.read = false` | Người YC, nhân viên khác không có quyền survey |

**Lưu ý:** Tab này là **read-only** — không có nút tạo/sửa/xóa phiếu khảo sát tại đây. Để sửa phiếu, người dùng vào module Khảo sát.

Kiểm tra quyền trong `SupplierDetail.tsx`:
```typescript
// Chỉ hiện tab surveys nếu có quyền đọc survey
const canViewSurveys = can('survey', 'read')

const TABS = [
  { key: 'info', label: 'Thông tin' },
  { key: 'eval', label: 'Đánh giá' },
  { key: 'contracts', label: 'Hợp đồng' },
  { key: 'payables', label: 'Công nợ' },
  ...(canViewSurveys ? [{ key: 'surveys', label: 'Khảo sát của NCC' }] : []),
]
```

---

## 7. Tiêu chí nghiệm thu

### 7.1 Checklist chức năng

- [ ] Tab "Khảo sát của NCC" xuất hiện trên trang chi tiết NCC (khi NCC đã tồn tại, không hiện ở màn tạo mới).
- [ ] Tab chỉ hiện với user có quyền `survey.read`; user không có quyền không thấy tab.
- [ ] Sub-tab KSNCC hiển thị đúng các dòng `tab_survey_supplier_line` có `tax_code` trùng với NCC.
- [ ] Sub-tab KSSP hiển thị đúng các dòng `tab_survey_product_line` có `supplier_code` trùng với `code` của NCC.
- [ ] Khi NCC không có `tax_code`: sub-tab KSNCC hiển thị banner cảnh báo thay vì bảng trống câm.
- [ ] Nút "Xem phiếu" / click dòng → điều hướng đúng đến phiếu khảo sát gốc.
- [ ] Bảng KSNCC hiển thị đủ các cột: Mã phiếu, Ngày tiếp nhận, Trạng thái, Tên NCC, MST, Nhóm cung cấp, Đánh giá NV KD, Độ tin cậy, Kết quả duyệt dòng.
- [ ] Bảng KSSP hiển thị đủ các cột: Mã phiếu, Ngày tiếp nhận, Trạng thái, Tên sản phẩm, Thông số, ĐVT, MOQ, Đơn giá, VAT, Kết quả duyệt dòng.
- [ ] Phân trang hoạt động đúng nếu số dòng vượt `page_size`.

### 7.2 Checklist API

- [ ] `GET /api/suppliers/{id}/survey-supplier-lines` trả đúng dữ liệu, có `total`.
- [ ] `GET /api/suppliers/{id}/survey-product-lines` trả đúng dữ liệu, có `total`.
- [ ] API trả `warning: "no_tax_code"` khi NCC không có `tax_code`.
- [ ] API trả 403 khi user không có quyền `survey.read`.
- [ ] API trả 404 khi `supplier_id` không tồn tại.

### 7.3 Checklist edge case

- [ ] NCC không có bất kỳ dòng khảo sát nào: cả 2 sub-tab hiển thị thông báo trạng thái rỗng.
- [ ] NCC có nhiều dòng (>50): phân trang đúng, không bị mất dữ liệu.
- [ ] Nhiều NCC trùng `tax_code`: cột "Tên NCC (trong phiếu)" giúp phân biệt, ghi chú cảnh báo phía trên bảng.

---

## 8. Edge Cases

| Tình huống | Hành vi kỳ vọng |
|---|---|
| NCC `tax_code = ""` hoặc `null` | KSNCC: banner cảnh báo. KSSP: vẫn query bình thường theo `supplier_code`. |
| NCC `tax_code` có khoảng trắng thừa | Backend trim trước khi query để tránh miss match. |
| Nhiều NCC trùng `tax_code` | Hiển thị note nhỏ: _"Có thể có nhiều nhà cung cấp cùng MST này"_. Cột `supplier_name` trong bảng giúp phân biệt. |
| Phiếu khảo sát đã bị xóa nhưng dòng vẫn còn | JOIN với `tab_survey` sẽ loại bỏ các dòng mồ côi (INNER JOIN). |
| `supplier_code` trong `tab_survey_product_line` nhập sai cách (khác hoa thường) | Backend so sánh case-insensitive (`LOWER()`) hoặc nghiệp vụ phải chuẩn hóa khi nhập. Đề xuất: normalize khi lưu dòng khảo sát. |
| Phiếu khảo sát có nhiều dòng NCC cùng tax_code (1 phiếu, nhiều dòng của NCC này) | Tất cả các dòng đều hiện — đúng hành vi. Người dùng thấy nhiều dòng cùng 1 `survey_code`. |
| Người dùng click "Xem phiếu" khi không có quyền xem phiếu đó (scope hạn chế) | Backend trả 403 khi load phiếu; frontend hiển thị thông báo lỗi chuẩn của app. |
| Tab được load khi đang ở màn tạo NCC mới (`isNew = true`) | Tab không hiển thị (giống các tab hiện có). |

---

## 9. Câu hỏi mở

| # | Câu hỏi | Mức độ chặn |
|---|---|---|
| 1 | Sau Task 7 gộp phiếu, route `/surveys-supplier/:id` và `/surveys-product/:id` có được gộp thành 1 không? Nếu có, cần cập nhật lại link "Xem phiếu" ở tab này. | Thấp — chỉ đổi URL |
| 2 | Có cần **phân trang** hay chỉ cần load tối đa 200 dòng (giống các tab contracts/payables hiện tại)? | Trung bình |
| 3 | Sub-tab KSSP có cần thêm filter theo trạng thái phiếu (chỉ xem dòng "đã duyệt") không, hay xem tất cả? | Trung bình |
| 4 | Khi click "Xem phiếu" từ sub-tab: mở **cùng tab** hay **tab mới**? (Document này chọn cùng tab, cần xác nhận với UX.) | Thấp |
| 5 | Có cần **export Excel** danh sách khảo sát của NCC từ tab này không? | Thấp — làm sau nếu cần |
| 6 | `tab_survey_product_line` có `supplier_code` — trường này có **bắt buộc điền** khi tạo phiếu khảo sát không? Nếu không bắt buộc thì KSSP có thể miss dữ liệu. | Cao — cần xác nhận nghiệp vụ nhập liệu |

---

*Tài liệu này mô tả yêu cầu cho phần "làm ngay" của Task 9. Phần hoãn (tab Sản phẩm của NCC) sẽ được mô tả trong một requirement riêng khi có quyết định về bảng map.*
