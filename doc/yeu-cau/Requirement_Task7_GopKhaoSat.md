# Requirement — Task 7: Gộp 2 phiếu khảo sát thành 1 giao diện có 2 bảng + thêm trường Ghi chú mỗi dòng

> **Phiên bản:** 1.0 — Ngày soạn: 2026-07-04
> **Trạng thái:** Đã chốt, chờ triển khai
> **Tác giả:** Thu mua / PM
> **Phụ thuộc:** Task 6 (đổi tên menu) hoàn thành. Task 5, 8, 9 phụ thuộc vào Task 7.

---

## 1. Mục tiêu & Hiện trạng

### 1.1 Hiện trạng

Hệ thống hiện tại tách hoàn toàn 2 loại phiếu khảo sát:

| Khía cạnh | Hiện trạng |
|---|---|
| DB header | Bảng `tab_survey`, cột `survey_type = 'supplier'` hoặc `'product'` |
| DB dòng NCC | Bảng `tab_survey_supplier_line` (25 trường + duyệt) |
| DB dòng SP | Bảng `tab_survey_product_line` (28 trường + duyệt) |
| API | 2 router riêng: `/api/surveys-supplier` và `/api/surveys-product` |
| Frontend config | 2 entry trong `cruds.tsx`: `surveys-supplier` và `surveys-product` |
| Menu | 2 mục "Khảo sát NCC" (`/surveys-supplier`) và "Khảo sát SP" (`/surveys-product`) |
| Màn chi tiết | 1 component `SurveyDetail.tsx` nhận prop `type: 'supplier' \| 'product'` |

**Nhược điểm của kiến trúc tách rời:**
- Thu mua phải tạo 2 phiếu riêng cho cùng 1 đợt khảo sát, mỗi đợt thường đi kèm cả NCC lẫn sản phẩm.
- Không thể xem toàn bộ kết quả khảo sát 1 đợt trên 1 màn hình.
- Workflow duyệt và thông báo chạy 2 lần cho cùng 1 nhu cầu.
- 2 mục menu gây nhầm lẫn khi quyết định tạo phiếu nào.

### 1.2 Mục tiêu sau Task 7

| Khía cạnh | Sau Task 7 |
|---|---|
| Giao diện | **1 phiếu khảo sát** chứa **2 bảng** (Bảng NCC ở trên, Bảng SP ở dưới) nhập cùng 1 màn |
| Menu | Gộp thành **1 mục "Khảo sát"** (`/surveys`) |
| API | **1 endpoint thống nhất** (`/api/surveys`) trả cả 2 loại line trong 1 phiếu |
| DB | **Giữ nguyên 2 bảng line** — chỉ thay đổi giao diện và API, không migrate dữ liệu cột |
| Trường mới | Thêm cột `note TEXT` vào cả `tab_survey_supplier_line` và `tab_survey_product_line` |
| Ẩn thông tin | `note` **không được xuất** sang Yêu cầu khảo sát (Task 5) — chỉ dùng nội bộ thu mua |

---

## 2. Thay đổi Data Model

### 2.1 Thêm cột `note` vào 2 bảng line

#### 2.1.1 Bảng `tab_survey_supplier_line`

Thêm 1 cột ở **cuối** bảng (trước hoặc sau `line_approve_note`):

| Cột mới | Kiểu | Default | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| `note` | `TEXT` | `''` (chuỗi rỗng) | Nullable, không bắt buộc | Ghi chú nội bộ của NSPT cho dòng NCC này — không hiển thị ra ngoài |

**Danh sách toàn bộ cột hiện có của `tab_survey_supplier_line` (25 cột + id + audit):**

| # | Tên cột | Kiểu | Mô tả |
|---|---|---|---|
| — | `id` | BigInt PK | |
| — | `survey_id` | BigInt FK→tab_survey | |
| 1 | `contact_date` | String(10) | Ngày liên hệ NCC |
| 2 | `reply_date` | String(10) | Ngày dự kiến NCC phản hồi |
| 3 | `result_date` | String(10) | Ngày dự kiến trả KQ |
| 4 | `supplier_code` | String(50) | Mã viết tắt NCC |
| 5 | `supplier_name` | String(255) | Tên NCC (tự điền) |
| 6 | `tax_code` | String(25) | Mã số thuế |
| 7 | `reg_address` | Text | Địa chỉ theo ĐKKD |
| 8 | `warehouse_address` | Text | Địa chỉ kho NCC |
| 9 | `google_maps` | String(500) | Link định vị kho |
| 10 | `contact_person` | String(100) | NVKD của NCC |
| 11 | `contact_phone` | String(30) | SĐT NCC |
| 12 | `supply_group` | String(255) | Nhóm SP/dịch vụ NCC cung ứng |
| 13 | `quote_folder` | String(500) | Link báo giá |
| 14 | `source_of_information` | String(255) | Nguồn thông tin đầu vào |
| 15 | `production_tech` | String(255) | Công nghệ SX |
| 16 | `production_time` | String(100) | Thời gian SX |
| 17 | `nvkd_eval` | String(100) | Đánh giá NVKD |
| 18 | `invoice_policy` | String(255) | Chính sách hóa đơn |
| 19 | `reliability` | String(20) | Mức độ tin cậy |
| 20 | `delivery_policy` | String(255) | Chính sách nhận hàng |
| 21 | `debt_policy` | String(50) | Chính sách công nợ |
| 22 | `defect_return` | String(255) | Hàng lỗi/hàng trả |
| 23 | `nspt_note` | String(20) | Nhận xét NSPT (Đạt/Không đạt) |
| 24 | `nspt_reason` | Text | Lý do nhận xét NSPT |
| 25 | `line_approve` | String(20) | Duyệt dòng (TP/QL) |
| 26 | `line_approve_note` | Text | Ý kiến TP/QL |
| **MỚI** | **`note`** | **Text** | **Ghi chú nội bộ — KHÔNG xuất sang Task 5** |

#### 2.1.2 Bảng `tab_survey_product_line`

Thêm 1 cột tương tự:

| Cột mới | Kiểu | Default | Ràng buộc | Ghi chú |
|---|---|---|---|---|
| `note` | `TEXT` | `''` | Nullable | Ghi chú nội bộ của NSPT cho dòng SP này — không hiển thị ra ngoài |

**Danh sách toàn bộ cột hiện có của `tab_survey_product_line` (28 cột + id + audit):**

| # | Tên cột | Kiểu | Mô tả |
|---|---|---|---|
| — | `id` | BigInt PK | |
| — | `survey_id` | BigInt FK→tab_survey | |
| 1 | `contact_date` | String(10) | Ngày liên hệ |
| 2 | `reply_date` | String(10) | Ngày dự kiến phản hồi |
| 3 | `result_date` | String(10) | Ngày dự kiến trả KQ |
| 4 | `supplier_code` | String(50) | Mã viết tắt NCC |
| 5 | `internal_code` | String(50) | Mã SP theo NCC (nhập tay) |
| 6 | `product_name` | String(255) | Tên SP (tên NCC đặt) |
| 7 | `spec` | Text | Thông số kỹ thuật |
| 8 | `origin` | String(100) | Xuất xứ |
| 9 | `quote_unit` | String(25) | ĐVT báo giá |
| 10 | `moq` | Numeric(18,3) | MOQ tối thiểu |
| 11 | `price_by_volume` | Numeric(18,2) | Giá theo sản lượng (VNĐ) |
| 12 | `volume_range` | String(100) | Khung sản lượng |
| 13 | `vat` | Numeric(5,2) | VAT (%) |
| 14 | `request_qty` | Numeric(18,3) | SL yêu cầu |
| 15 | `amount` | Numeric(18,2) | Thành tiền (tự tính) |
| 16 | `internal_unit` | String(25) | ĐVT quy đổi về ĐVT Cty |
| 17 | `amount_converted` | Numeric(18,2) | Thành tiền đã quy đổi |
| 18 | `shipping_cost` | Numeric(18,2) | Chi phí vận chuyển |
| 19 | `delivery_time` | String(100) | Thời gian giao hàng |
| 20 | `delivery_place` | String(255) | Địa điểm giao/nhận hàng |
| 21 | `quote_file` | String(500) | Link/file báo giá |
| 22 | `sample_ready` | Boolean | Mẫu sẵn |
| 23 | `sample_date` | String(10) | Ngày lấy mẫu |
| 24 | `sample_qty` | Numeric(18,3) | Số lượng mẫu nhận |
| 25 | `lab_result` | String(20) | Đánh giá từ LAB |
| 26 | `lab_note` | Text | Ghi chú LAB |
| 27 | `nspt_note` | String(20) | NSPT đánh giá |
| 28 | `nspt_reason` | Text | Lý do NSPT |
| 29 | `line_approve` | String(20) | Duyệt dòng (TP/QL) |
| 30 | `line_approve_note` | Text | Ý kiến TP/QL |
| **MỚI** | **`note`** | **Text** | **Ghi chú nội bộ — KHÔNG xuất sang Task 5** |

### 2.2 Xử lý cột `survey_type` trên `tab_survey`

**Vấn đề:** Hiện tại `tab_survey.survey_type` bắt buộc có giá trị (`supplier` hoặc `product`). Sau khi gộp, 1 phiếu chứa cả 2 loại line, nên `survey_type` không còn phân biệt loại phiếu nữa.

**Đề xuất chốt:** **Giữ cột `survey_type`, đặt giá trị mặc định là `'combined'` cho phiếu mới.**

| Giá trị | Ý nghĩa | Xử lý |
|---|---|---|
| `'combined'` | Phiếu mới (sau Task 7) — chứa cả 2 bảng line | Giá trị mặc định khi tạo mới |
| `'supplier'` | Phiếu cũ chỉ có supplier line | Giữ nguyên, dữ liệu cũ tương thích |
| `'product'` | Phiếu cũ chỉ có product line | Giữ nguyên, dữ liệu cũ tương thích |

**Lý do giữ cột:**
- Dữ liệu cũ (`supplier`/`product`) vẫn đọc được bình thường, không cần migration dữ liệu cũ.
- Task 9 (tab NCC) có thể dùng để lọc nếu cần.
- Không xóa/rename tránh break code nào đang tham chiếu `survey_type`.

**Lý do không dùng `NULL`:** Rủi ro break filter hiện tại `service.list_surveys()` đang filter `Survey.survey_type == survey_type`.

### 2.3 Migration Script

#### 2.3.1 Alembic (backend)

Tạo migration mới:

```sql
-- Thêm cột note vào tab_survey_supplier_line
ALTER TABLE tab_survey_supplier_line ADD COLUMN note TEXT NOT NULL DEFAULT '';

-- Thêm cột note vào tab_survey_product_line
ALTER TABLE tab_survey_product_line ADD COLUMN note TEXT NOT NULL DEFAULT '';

-- Không xóa survey_type — giữ nguyên, chỉ thêm giá trị 'combined' hợp lệ
-- (không cần ALTER vì CHECK CONSTRAINT không có trên cột này)
```

#### 2.3.2 Tương thích dữ liệu cũ

- Phiếu cũ `survey_type = 'supplier'`: API mới vẫn trả `supplier_lines` (không rỗng) và `product_lines = []`. Giao diện hiển thị Bảng NCC có dữ liệu, Bảng SP rỗng — hoàn toàn bình thường.
- Phiếu cũ `survey_type = 'product'`: API mới trả `supplier_lines = []`, `product_lines` có dữ liệu. Bảng NCC rỗng.
- Phiếu mới `survey_type = 'combined'`: cả 2 bảng đều có thể có dữ liệu.
- Không cần chạy UPDATE hàng loạt cho dữ liệu cũ — giao diện 2 bảng vẫn hoạt động đúng kể cả khi 1 bảng rỗng.

---

## 3. Màn hình gộp — Mô tả Giao diện

### 3.1 Tổng quan layout

```
┌─────────────────────────────────────────────────────────────┐
│  [←]  Khảo sát KS00001  [badge trạng thái]   [Lưu] [Gửi duyệt]  │
├─────────────────────────────────────────────────────────────┤
│  CARD: Thông tin tiếp nhận (header phiếu — giữ nguyên)      │
│  (Mã PYC, Ngày tiếp nhận, Phân loại, NSPT, Yêu cầu KT,     │
│   Đã có mã SP sẵn?, Mã VTBB, Tên VTBB, SL, ĐVT, Giá đề xuất) │
├─────────────────────────────────────────────────────────────┤
│  CARD: Bảng khảo sát NCC                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ [Thêm dòng] [Thêm nhiều] [Xóa đã chọn]             │    │
│  │ Bảng dạng scroll ngang (tableCols NCC + cột Hành động) │ │
│  │ Mỗi dòng: [checkbox] [#] [NCC] [Ngày LH] ... [Duyệt] [✏️🗐🗑]│
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  CARD: Bảng khảo sát Sản phẩm                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ [Thêm dòng] [Thêm nhiều] [Xóa đã chọn]             │    │
│  │ Bảng dạng scroll ngang (tableCols SP + cột Hành động)│    │
│  │ Mỗi dòng: [checkbox] [#] [NCC] [Tên SP] [Giá]...[✏️🗐🗑]│
│  │ Tổng thành tiền: x,xxx,xxx đ                        │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│  CARD: Chứng từ đính kèm (phiếu)                            │
│  [Lịch sử thao tác - cột phải nếu có log]                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Thay đổi trên Header phiếu

**Không thay đổi** — giữ nguyên toàn bộ section "Thông tin tiếp nhận" hiện tại. Phần header dùng chung cho cả 2 loại khảo sát trong cùng 1 phiếu.

### 3.3 Bảng NCC (Bảng 1)

**Tiêu đề card:** "Bảng khảo sát Nhà cung cấp"

**Cột hiển thị trong bảng tóm tắt** (core columns — giữ như cũ):

| # | Key | Label | Ghi chú |
|---|---|---|---|
| 1 | `contact_date` | Ngày LH | |
| 2 | `supplier_code` | NCC (viết tắt) * | |
| 3 | `supplier_name` | Tên pháp lý | |
| 4 | `contact_person` | Người LH (NVKD) | |
| 5 | `contact_phone` | SĐT | |
| 6 | `nspt_note` | Nhận xét NSPT | |
| 7 | `line_approve` | Duyệt (TP/QL) | |

**Nút hành động mỗi dòng:** Sửa chi tiết (popup), Nhân bản, Xóa dòng.

**Popup chi tiết dòng NCC** — thêm mục "Ghi chú" vào cuối (sau cụm "Phê duyệt"):

```
Cụm: Ghi chú nội bộ
┌──────────────────────────────────────────────┐
│ Ghi chú (nội bộ thu mua, không gửi ra ngoài) │
│ [textarea — ô nhập tự do]                    │
└──────────────────────────────────────────────┘
```

- Label hiển thị: **"Ghi chú (nội bộ)"**
- Kiểu: `textarea`, chiều cao tối thiểu 64px
- Luôn có thể nhập dù phiếu ở trạng thái nào (kể cả `submitted`) — tương tự field `nspt_reason`
- Không hiện badge màu, không validate bắt buộc

**Popup chi tiết dòng NCC cũng bao gồm** mục đính kèm file theo dòng (đã có, giữ nguyên).

### 3.4 Bảng SP (Bảng 2)

**Tiêu đề card:** "Bảng khảo sát Sản phẩm"

**Cột hiển thị trong bảng tóm tắt** (core columns — giữ như cũ):

| # | Key | Label | Ghi chú |
|---|---|---|---|
| 1 | `supplier_code` | NCC * | |
| 2 | `internal_code` | Mã SP (NCC) | |
| 3 | `product_name` | Tên SP theo NCC * | |
| 4 | `quote_unit` | ĐVT báo giá | |
| 5 | `moq` | MOQ | |
| 6 | `price_by_volume` | Giá theo khung | |
| 7 | `amount` | Thành tiền | |
| 8 | `line_approve` | Duyệt (TP/QL) | |

**Dòng tổng:** "Tổng thành tiền: xxx,xxx đ" hiển thị dưới bảng SP (giữ nguyên logic hiện tại).

**Popup chi tiết dòng SP** — thêm mục "Ghi chú" vào cuối (sau cụm "Đánh giá & Phê duyệt"):

```
Cụm: Ghi chú nội bộ
┌──────────────────────────────────────────────┐
│ Ghi chú (nội bộ thu mua, không gửi ra ngoài) │
│ [textarea — ô nhập tự do]                    │
└──────────────────────────────────────────────┘
```

Quy tắc nhập: giống Bảng NCC — không bắt buộc, không validate.

### 3.5 Quy tắc chỉnh sửa từng bảng

| Điều kiện | Bảng NCC | Bảng SP |
|---|---|---|
| Phiếu = `draft` hoặc `rejected`, có quyền `write` | Thêm/sửa/xóa dòng tự do | Thêm/sửa/xóa dòng tự do |
| Phiếu = `submitted`, không có quyền `approve` | Chỉ xem, khóa | Chỉ xem, khóa |
| Phiếu = `submitted`, có quyền `approve` | Chỉ sửa `line_approve` + `line_approve_note` qua endpoint `/line-approve` | Tương tự |
| Phiếu = `approved` | Chỉ xem | Chỉ xem |
| Mỗi bảng có thể để rỗng | Cho phép — 0 dòng NCC là hợp lệ | Cho phép — 0 dòng SP là hợp lệ |

### 3.6 Validate khi Gửi duyệt

- Kiểm tra header: giữ nguyên validate hiện tại.
- **Ít nhất 1 trong 2 bảng phải có dữ liệu hợp lệ** (tức là: tổng số dòng NCC hợp lệ + dòng SP hợp lệ >= 1).
- Dòng NCC hợp lệ: có `supplier_code`.
- Dòng SP hợp lệ: có `product_name`.
- Nếu cả 2 bảng đều rỗng: báo lỗi `"Cần ít nhất 1 dòng khảo sát (NCC hoặc Sản phẩm)"`.

### 3.7 Trạng thái Submit

Luồng submit/approve/reject **không thay đổi** — áp dụng cho cả phiếu (header), không theo từng bảng. Duyệt dòng (`line_approve`) vẫn theo từng dòng riêng qua endpoint `/line-approve`.

---

## 4. Thay đổi Menu & Route

### 4.1 Menu

**Trước:**
```
Mua hàng
  ├── Yêu cầu mua          /purchase-requests
  ├── Khảo sát NCC         /surveys-supplier
  ├── Khảo sát SP          /surveys-product
  └── Đơn mua hàng         /purchase-orders
```

**Sau:**
```
Mua hàng
  ├── Yêu cầu mua          /purchase-requests
  ├── Khảo sát             /surveys            ← gộp 2 mục thành 1
  └── Đơn mua hàng         /purchase-orders
```

**Thay đổi trong `AppLayout.tsx`:**
- Xóa 2 `NavItem` `{ to: '/surveys-supplier', ... }` và `{ to: '/surveys-product', ... }`
- Thêm 1 `NavItem`: `{ to: '/surveys', label: 'Khảo sát', icon: 'ti-clipboard-search', entity: 'survey' }`

### 4.2 Route

**Trước:**
```
/surveys-supplier          → SurveyList (type='supplier')
/surveys-supplier/:id      → SurveyDetail (type='supplier')
/surveys-product           → SurveyList (type='product')
/surveys-product/:id       → SurveyDetail (type='product')
```

**Sau:**
```
/surveys                   → SurveyList (unified)
/surveys/:id               → SurveyDetail (unified, 2 bảng)
```

### 4.3 Xử lý URL cũ (redirect)

Thêm redirect trong React Router để tránh link cũ 404:

| URL cũ | Redirect về |
|---|---|
| `/surveys-supplier` | `/surveys` |
| `/surveys-supplier/:id` | `/surveys/:id` |
| `/surveys-product` | `/surveys` |
| `/surveys-product/:id` | `/surveys/:id` |

> **Lưu ý:** ID phiếu trong DB là duy nhất (không phân biệt `supplier`/`product`), nên redirect `:id` là an toàn — 1 ID chỉ thuộc 1 phiếu duy nhất.

### 4.4 Thay đổi trong `cruds.tsx`

- Xóa 2 entry `'surveys-supplier'` và `'surveys-product'`
- Thêm 1 entry mới `'surveys'`:

```typescript
'surveys': {
  slug: 'surveys', entity: 'survey', title: 'Khảo sát', apiPath: '/api/surveys', txn: true,
  columns: [
    { key: 'code', label: 'Mã phiếu' },
    { key: 'pr_code', label: 'Mã YC (PYC)' },
    { key: 'item_group', label: 'Nhóm hàng' },
    { key: 'nspt', label: 'NSPT' },
    { key: 'supplier_count', label: 'Dòng NCC' },   // trường computed từ API
    { key: 'product_count', label: 'Dòng SP' },     // trường computed từ API
    { key: 'status', label: 'Trạng thái', render: (r) => prBadge(r.status) },
  ],
  filters: [
    { key: 'code', label: 'Mã phiếu' },
    { key: 'pr_code', label: 'Mã YC' },
    { key: 'item_group', label: 'Nhóm hàng', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
    { key: 'nspt', label: 'NSPT' },
    { key: 'status', label: 'Trạng thái', type: 'select', options: [...] },
  ],
  fields: [],  // chi tiết dùng SurveyDetail
}
```

---

## 5. Thay đổi API

### 5.1 Endpoints mới (unified)

| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/surveys` | Danh sách phiếu (tất cả `survey_type`) |
| GET | `/api/surveys/:id` | Chi tiết 1 phiếu — trả cả `supplier_lines` và `product_lines` |
| POST | `/api/surveys` | Tạo phiếu mới (mặc định `survey_type='combined'`) |
| PATCH | `/api/surveys/:id` | Cập nhật phiếu (cả 2 loại line) |
| DELETE | `/api/surveys/:id` | Xóa phiếu và toàn bộ dòng (cả 2 bảng) |
| POST | `/api/surveys/:id/submit` | Gửi duyệt |
| POST | `/api/surveys/:id/approve` | Duyệt phiếu |
| POST | `/api/surveys/:id/reject` | Trả lại |
| PATCH | `/api/surveys/:id/line-approve` | Duyệt dòng (gộp cả NCC và SP vào 1 endpoint) |

**Giữ lại các endpoint cũ** `/api/surveys-supplier` và `/api/surveys-product` như là **alias** (hoặc deprecated) trong ít nhất 1 sprint để không break notification links hiện tại (`link=f"/surveys-{survey_type}/{s.id}"`).

### 5.2 Response format chi tiết phiếu (GET `/api/surveys/:id`)

**Thay đổi so với hiện tại:** thay vì 1 trường `lines`, trả về 2 trường riêng:

```json
{
  "id": 42,
  "code": "KS00042",
  "survey_type": "combined",
  "pr_code": "PYC001",
  "status": "draft",
  "... (toàn bộ header fields) ...",
  "supplier_lines": [
    {
      "id": 101,
      "survey_id": 42,
      "supplier_code": "NCC_ABC",
      "supplier_name": "Công ty ABC",
      "contact_date": "2026-07-01",
      "note": "Đã hẹn gặp trực tiếp tại kho",
      "line_approve": "Chờ duyệt",
      "... (toàn bộ supplier line fields) ..."
    }
  ],
  "supplier_count": 1,
  "product_lines": [
    {
      "id": 201,
      "survey_id": 42,
      "supplier_code": "NCC_ABC",
      "product_name": "Hộp carton 3 lớp",
      "price_by_volume": 5200,
      "note": "Cần xác nhận lại MOQ trước khi duyệt",
      "line_approve": "Chờ duyệt",
      "... (toàn bộ product line fields) ..."
    }
  ],
  "product_count": 1,
  "subtotal": 5200.0
}
```

### 5.3 Request body khi tạo/cập nhật

**POST / PATCH `/api/surveys`:**

```json
{
  "pr_code": "PYC001",
  "received_date": "2026-07-04",
  "item_group": "Bao bì",
  "... (header fields) ...",
  "supplier_lines": [ { "supplier_code": "NCC_ABC", "note": "...", "... supplier fields ..." } ],
  "product_lines":  [ { "product_name": "Hộp carton", "note": "...", "... product fields ..." } ]
}
```

- Nếu `supplier_lines` không truyền hoặc `null`: giữ nguyên dòng cũ (không xóa).
- Nếu `supplier_lines = []`: xóa toàn bộ dòng NCC của phiếu.
- Tương tự cho `product_lines`.

### 5.4 Endpoint `/line-approve` sau khi gộp

**PATCH `/api/surveys/:id/line-approve`** nhận cả 2 loại line trong cùng 1 request:

```json
{
  "supplier_lines": [
    { "id": 101, "line_approve": "Đã duyệt", "line_approve_note": "Đạt yêu cầu" }
  ],
  "product_lines": [
    { "id": 201, "line_approve": "Không duyệt", "line_approve_note": "Cần báo giá lại" }
  ]
}
```

### 5.5 Danh sách phiếu (GET `/api/surveys`)

- Không filter theo `survey_type` nữa — trả toàn bộ phiếu.
- Thêm 2 computed field vào mỗi item trong list: `supplier_count` (số dòng NCC) và `product_count` (số dòng SP).
- Các filter hiện tại (`code`, `pr_code`, `status`, `item_group`, `nspt`) giữ nguyên.

### 5.6 Backward compatibility

**Giữ 2 router cũ** nhưng đánh dấu `deprecated`:

```python
# controller.py — giữ lại để tránh break notification links
supplier_survey_router = _build_router("supplier", "/api/surveys-supplier", ...)
product_survey_router  = _build_router("product",  "/api/surveys-product", ...)

# Router mới
unified_survey_router = build_unified_router("/api/surveys")
```

Trong tương lai (sau khi notification links đã cập nhật) sẽ xóa 2 router cũ.

---

## 6. Quy tắc ẩn `note` khi xuất sang Yêu cầu khảo sát (Task 5)

### 6.1 Nguyên tắc

- Trường `note` là **thông tin nội bộ của bộ phận thu mua** — chứa nhận xét, nghi ngờ, ý kiến riêng của NSPT về từng NCC/sản phẩm.
- **Người yêu cầu khảo sát (Task 5) và toàn bộ UI của họ không được thấy `note`.**
- Việc ẩn phải thực hiện **ở tầng backend (API)**, không chỉ ẩn ở UI.

### 6.2 Quy tắc kỹ thuật

| Endpoint / ngữ cảnh | Hành vi với `note` |
|---|---|
| `GET /api/surveys/:id` — người có quyền `survey:read` (NSPT/Admin) | **Trả về `note`** trong `supplier_lines[].note` và `product_lines[].note` |
| `GET /api/survey-requests/:id/options` — NSTM và Người YC xem option | **Loại bỏ `note`** khỏi payload (dù option được build từ `product_line`) |
| Bất kỳ endpoint nào trả thông tin cho người ngoài thu mua | Không include `note` |
| Export Excel / in phiếu | `note` **không hiển thị** trong bản in — chỉ là ghi chú soạn thảo nội bộ |

### 6.3 Triển khai backend (Task 5 chịu trách nhiệm)

Khi Task 5 build `survey_request_option` từ `product_line`, dùng whitelist field thay vì `model_dump()` để đảm bảo không vô tình expose `note`:

```python
OPTION_PUBLIC_FIELDS = [
    "product_name", "spec", "origin", "quote_unit", "moq",
    "price_by_volume", "volume_range", "vat", "amount",
    "internal_unit", "amount_converted", "shipping_cost",
    "delivery_time", "delivery_place",
    "sample_ready", "sample_date", "sample_qty",
    "lab_result",   # lab_note cũng cân nhắc ẩn nếu có thông tin NCC
]
# Không include: supplier_code, supplier_name, note, nspt_note, nspt_reason, ...
```

---

## 7. Tác động tới các phần liên quan

### 7.1 Task 5 — Yêu cầu khảo sát (đọc dòng SP đã duyệt)

| Điểm chạm | Thay đổi cần thiết |
|---|---|
| NSTM chọn option từ khảo sát SP | Đọc từ `tab_survey_product_line` (giữ nguyên bảng) — không thay đổi |
| Option trả về cho người YC | **Phải loại bỏ `note`** (xem mục 6) |
| Link notification `survey_submitted` / `survey_approved` | Cập nhật từ `/surveys-supplier/:id` và `/surveys-product/:id` → **`/surveys/:id`** |
| Lọc dòng SP đã duyệt | Vẫn dùng `line_approve = 'Đã duyệt'` — không thay đổi |

### 7.2 Task 8 — Báo cáo dòng khảo sát

| Điểm chạm | Thay đổi cần thiết |
|---|---|
| Báo cáo liệt kê theo dòng | Cần query cả `tab_survey_supplier_line` và `tab_survey_product_line` — hiện tại đã tách theo loại, sau Task 7 có thể UNION hoặc hiển thị 2 tab con trong màn báo cáo |
| Trạng thái "Thiếu thông tin" ở mức dòng | Áp dụng cho cả 2 bảng line (không ảnh hưởng bởi việc gộp giao diện) |
| Cột `note` trong báo cáo | **Hiển thị `note` trong báo cáo nội bộ** (báo cáo thu mua được xem), **ẩn trong báo cáo công khai nếu có** |

### 7.3 Task 9 — Tab NCC

| Điểm chạm | Thay đổi cần thiết |
|---|---|
| Sub-tab "Khảo sát NCC" theo `tax_code` | Đọc từ `tab_survey_supplier_line JOIN tab_survey` — không thay đổi |
| Sub-tab "Khảo sát SP" theo `supplier_code` | Đọc từ `tab_survey_product_line` — không thay đổi |
| Link từ tab sang phiếu | Cập nhật link sang `/surveys/:survey_id` thay vì `/surveys-supplier/:id` hoặc `/surveys-product/:id` |

### 7.4 Notification links

File `controller.py` hiện tại sinh link:
```python
link=f"/surveys-{survey_type}/{s.id}"
```

Sau Task 7 cần sửa thành:
```python
link=f"/surveys/{s.id}"
```

Áp dụng cho tất cả `trigger_notification` trong survey controller: `survey_submitted`, `survey_approved`, `survey_rejected`.

---

## 8. Tiêu chí Nghiệm thu

### 8.1 Menu & Route

- [ ] Sidebar chỉ còn 1 mục "Khảo sát" trỏ tới `/surveys`
- [ ] Không còn mục "Khảo sát NCC" và "Khảo sát SP"
- [ ] Truy cập `/surveys-supplier` và `/surveys-product` → tự redirect về `/surveys`
- [ ] Truy cập `/surveys-supplier/42` → redirect về `/surveys/42`

### 8.2 Danh sách phiếu

- [ ] Màn `/surveys` liệt kê TẤT CẢ phiếu (cả `supplier`, `product`, `combined`)
- [ ] Hiển thị cột "Dòng NCC" và "Dòng SP" đúng số lượng
- [ ] Filter code/pr_code/item_group/nspt/status hoạt động đúng

### 8.3 Tạo phiếu mới

- [ ] Tạo phiếu mới (`/surveys/new`) → phiếu tạo ra có `survey_type = 'combined'`
- [ ] Có thể thêm dòng NCC + dòng SP cùng lúc trong 1 phiếu
- [ ] Có thể lưu phiếu chỉ có dòng NCC (dòng SP rỗng)
- [ ] Có thể lưu phiếu chỉ có dòng SP (dòng NCC rỗng)

### 8.4 Trường Ghi chú

- [ ] Popup chi tiết dòng NCC có ô "Ghi chú (nội bộ)" — `textarea`
- [ ] Popup chi tiết dòng SP có ô "Ghi chú (nội bộ)" — `textarea`
- [ ] Nhập ghi chú và lưu → ghi chú được persist (hiển thị lại khi mở lại dòng)
- [ ] Ghi chú hiển thị trong màn chi tiết khảo sát (khi NSPT xem lại)
- [ ] `note` **không** xuất hiện trong response của option (Task 5)

### 8.5 Duyệt dòng

- [ ] Người có quyền `approve` duyệt được dòng NCC và dòng SP trong cùng 1 phiếu
- [ ] Endpoint `/line-approve` nhận cả `supplier_lines` và `product_lines`
- [ ] Lưu duyệt dòng NCC không ảnh hưởng dòng SP và ngược lại

### 8.6 Phiếu cũ

- [ ] Phiếu cũ `survey_type = 'supplier'` vẫn mở được qua `/surveys/:id`
- [ ] Phiếu cũ `survey_type = 'supplier'`: hiển thị Bảng NCC có dữ liệu, Bảng SP rỗng
- [ ] Phiếu cũ `survey_type = 'product'`: hiển thị Bảng NCC rỗng, Bảng SP có dữ liệu
- [ ] Phiếu cũ không bị mất dữ liệu

### 8.7 Notification

- [ ] Khi gửi duyệt/duyệt/từ chối → notification link trỏ tới `/surveys/:id`

### 8.8 Validate submit

- [ ] Submit phiếu 0 dòng NCC + 0 dòng SP → báo lỗi rõ ràng
- [ ] Submit phiếu có ít nhất 1 dòng NCC hoặc 1 dòng SP hợp lệ → thành công

---

## 9. Edge Cases & Migration dữ liệu cũ

### 9.1 Phiếu cũ chỉ có 1 loại dòng

| Tình huống | Xử lý |
|---|---|
| Phiếu `survey_type='supplier'` → open qua `/surveys/:id` | API trả `supplier_lines` có dữ liệu, `product_lines = []`. Giao diện hiển thị Bảng NCC có dữ liệu, Bảng SP hiển thị "Chưa có dòng nào". Người dùng CÓ THỂ thêm dòng SP nếu phiếu vẫn ở trạng thái draft. |
| Phiếu `survey_type='product'` → open qua `/surveys/:id` | Tương tự — Bảng NCC rỗng, Bảng SP có dữ liệu |
| Notification link cũ `/surveys-supplier/42` được click | Redirect về `/surveys/42` — phiếu vẫn mở đúng |
| API `/api/surveys-supplier/42` được gọi (từ code cũ chưa update) | Trả response bình thường — router cũ vẫn hoạt động trong giai đoạn chuyển tiếp |

### 9.2 Cột `note` = NULL trên dữ liệu cũ

Do migration thêm `DEFAULT ''`, tất cả dòng cũ sẽ có `note = ''` (chuỗi rỗng). Giao diện hiển thị ô trống — không có vấn đề.

### 9.3 ID phiếu trùng nhau giữa loại cũ

Không có rủi ro: `tab_survey` dùng ID tự tăng duy nhất, không phân biệt loại. Phiếu ID=42 luôn là 1 phiếu duy nhất dù trước đây gọi là "supplier" hay "product".

### 9.4 Quyền truy cập

Quyền hiện tại dùng entity `"survey"` — không thay đổi sau khi gộp. Người có quyền `survey:read` xem được cả phiếu gộp mới và phiếu cũ.

### 9.5 Phiếu cũ đang ở trạng thái `submitted`

Phiếu đang chờ duyệt khi migrate sẽ hoạt động bình thường — không cần can thiệp. Người duyệt vào phiếu qua `/surveys/:id`, thấy bảng line tương ứng, duyệt như cũ.

### 9.6 Xóa phiếu gộp

Khi xóa phiếu `combined`: xóa cả `tab_survey_supplier_line` (theo `survey_id`) và `tab_survey_product_line` (theo `survey_id`) + toàn bộ attachment theo phiếu và theo line. Phải cập nhật hàm `delete_survey()` trong `service.py` để xóa cả 2 bảng thay vì chỉ xóa theo `survey_type`.

---

## 10. Câu hỏi mở

| # | Câu hỏi | Ưu tiên | Gợi ý |
|---|---|---|---|
| 1 | **Có cần giữ 2 filter riêng** "xem chỉ phiếu NCC" / "xem chỉ phiếu SP" trong danh sách không? | Thấp | Có thể thêm filter `survey_type` trong màn danh sách. Phiếu `combined` sẽ xuất hiện ở cả 2 filter. |
| 2 | **2 router cũ** `/api/surveys-supplier` và `/api/surveys-product` giữ bao lâu? | Trung bình | Đề xuất: 1–2 sprint sau khi Task 7 deploy; xóa sau khi confirm notification links đã cập nhật. |
| 3 | **`note` có hiển thị trong báo cáo xuất Excel** (Task 8) không? | Trung bình | Nếu báo cáo chỉ dành cho nội bộ thu mua → hiển thị. Nếu có báo cáo dành cho người ngoài → ẩn. Cần xác nhận với nghiệp vụ. |
| 4 | **Khi phiếu `combined` có cả dòng NCC lẫn dòng SP**: nút "Gửi duyệt" kích hoạt 1 lần hay phải gửi riêng từng bảng? | Đã chốt | 1 lần — phiếu submit = cả 2 bảng đi duyệt cùng lúc. |
| 5 | **Tab NCC (Task 9)**: link từ sub-tab khảo sát sang phiếu — dùng `/surveys/:id` ngay sau Task 7 hay chờ Task 9? | Thấp | Nên cập nhật link khi làm Task 9, không cần làm trước. |
| 6 | **Phiếu `combined` có thể chỉ nhập 1 bảng** (ví dụ chỉ NCC, SP để rỗng) — có hợp lệ nghiệp vụ không? | Trung bình | Theo tài liệu đã chốt: cho phép. Cần xác nhận với nghiệp vụ nếu muốn bắt buộc cả 2 bảng phải có ít nhất 1 dòng. |

---

## Phụ lục — Tóm tắt thay đổi file

| File | Loại thay đổi | Mô tả |
|---|---|---|
| `backend/app/modules/survey/model.py` | Sửa | Thêm `note: Mapped[str]` vào `SurveySupplierLine` và `SurveyProductLine` |
| `backend/app/modules/survey/schema.py` | Sửa | Thêm `note` vào Pydantic schema cho cả 2 line; thêm schema `CombinedSurveyCreate/Update` |
| `backend/app/modules/survey/service.py` | Sửa | Thêm hàm `lines_both()`, sửa `_save_lines()` và `delete_survey()` để xử lý cả 2 bảng; sửa `list_surveys()` bỏ filter `survey_type` |
| `backend/app/modules/survey/controller.py` | Sửa | Thêm `unified_survey_router`; sửa `_out()` trả `supplier_lines` + `product_lines`; giữ 2 router cũ (deprecated) |
| `backend/app/main.py` | Sửa | Register `unified_survey_router` |
| `backend/alembic/versions/xxxx_add_note_to_survey_lines.py` | Tạo mới | Migration thêm cột `note` |
| `frontend/src/config/cruds.tsx` | Sửa | Xóa `surveys-supplier`, `surveys-product`; thêm `surveys` |
| `frontend/src/layouts/AppLayout.tsx` | Sửa | Gộp 2 nav item thành 1 "Khảo sát" → `/surveys` |
| `frontend/src/App.tsx` (hoặc router file) | Sửa | Thêm redirect từ URL cũ; route mới `/surveys` và `/surveys/:id` |
| `frontend/src/pages/SurveyDetail.tsx` | Sửa | Bỏ prop `type`; state riêng cho `supplier_lines` và `product_lines`; render 2 bảng riêng; thêm ô `note` vào popup chi tiết cả 2 loại dòng |
| `frontend/src/pages/SurveyList.tsx` (nếu có file riêng) | Sửa | Dùng API `/api/surveys` thay vì 2 API cũ |
