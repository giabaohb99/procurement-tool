# Requirement — Task 8: Màn báo cáo "NCC & Sản phẩm đang khảo sát" + Trạng thái "Thiếu thông tin" mức dòng

> **Phiên bản:** 1.0  
> **Ngày soạn:** 2026-07-04  
> **Người soạn:** Auto-generated từ codebase + Plan_CapNhat_Flow_KhaoSat_v2.md  
> **Phụ thuộc:** Task 7 (gộp 2 phiếu khảo sát thành 1 giao diện) cần hoàn thành trước khi làm Task 8.

---

## 1. Mục tiêu & Vấn đề gốc

### 1.1 Vấn đề hiện tại

Phiếu khảo sát (`tab_survey`) có thể chứa **nhiều dòng** (nhiều NCC hoặc nhiều sản phẩm). Mỗi dòng có trường `line_approve` để quản lý duyệt độc lập từng dòng.

**Vấn đề phát sinh:**

| # | Hiện tượng | Hệ quả |
|---|---|---|
| 1 | 1 phiếu có 5 dòng, quản lý chỉ duyệt 3 dòng, 2 dòng còn `line_approve = 'Chờ duyệt'` | Phiếu **bị kẹt** — không ai theo dõi 2 dòng chưa được xử lý |
| 2 | Quản lý duyệt toàn phiếu (`approve_status = 'Duyệt'`) mà chưa xem hết các dòng | Dòng thiếu thông tin lọt qua, gây lỗi ở bước sau |
| 3 | Dòng thiếu thông tin: nhân sự phụ trách phải **đợi quản lý "Trả lại" cả phiếu** mới sửa được | Tốn thời gian, phiếu tồn đọng, khó thống kê |
| 4 | Không có màn nào liệt kê **tất cả dòng** NCC/SP đang khảo sát theo trạng thái | Admin/quản lý không có công cụ thống kê/follow-up |

### 1.2 Giải pháp (Task 8)

1. **Thêm trạng thái "Thiếu thông tin" (`missing_info`) vào `line_approve`** — cho phép quản lý đánh dấu dòng cần bổ sung mà không cần trả lại cả phiếu; nhân sự phụ trách được phép sửa dòng đó ngay khi phiếu đang "chờ duyệt".
2. **Tạo màn báo cáo riêng "NCC & Sản phẩm đang khảo sát"** trong menu Báo cáo — liệt kê theo từng dòng (không theo phiếu), hỗ trợ filter trạng thái, xuất CSV.

---

## 2. Trạng thái dòng (line_approve) — Tập giá trị mới

### 2.1 Tập trạng thái đầy đủ

| Giá trị DB | Nhãn hiển thị | Màu badge | Ý nghĩa |
|---|---|---|---|
| `''` hoặc `'Chờ duyệt'` | Chờ duyệt | Cam `#d97706` | Dòng chưa được quản lý xem xét. Mặc định khi tạo dòng mới. |
| `'Đã duyệt'` | Đã duyệt | Xanh lá `#16a34a` | Quản lý đã xem xét và chấp nhận dòng này. |
| `'Không duyệt'` | Không duyệt | Đỏ `#b91c1c` | Quản lý từ chối dòng này (NCC/SP không phù hợp). |
| `'Thiếu thông tin'` | Thiếu thông tin | Tím `#7c3aed` | **(MỚI)** Dòng chưa đủ thông tin để duyệt; nhân sự phụ trách cần bổ sung thêm. |

> **Lưu ý code hiện tại:** `APPROVE_OPTS` trong `SurveyDetail.tsx` đang là `['Chờ duyệt', 'Đã duyệt', 'Không duyệt']`. Cần bổ sung `'Thiếu thông tin'` vào mảng này và `APPROVE_COLOR`.

### 2.2 Ý nghĩa chi tiết trạng thái "Thiếu thông tin"

- Quản lý đặt trạng thái này khi **không đủ dữ liệu để duyệt** (thiếu báo giá, thiếu MST, thiếu thông số kỹ thuật, v.v.).
- Khi đặt `'Thiếu thông tin'`, quản lý **bắt buộc phải điền `line_approve_note`** (ghi rõ cần bổ sung gì).
- Nhân sự phụ trách **nhìn thấy dòng bị đánh dấu** và được phép cập nhật nội dung dòng đó ngay (xem mục 3).
- Sau khi nhân sự cập nhật xong, trạng thái dòng **tự động quay về `'Chờ duyệt'`** để quản lý xem lại — HOẶC nhân sự tự đặt lại `'Chờ duyệt'` thủ công (tùy thiết kế UX, xem Mục 9.1).

### 2.3 Ai được đặt trạng thái nào

| Trạng thái | Nhân sự phụ trách (NSPT) | Quản lý / Admin (`survey.approve`) |
|---|---|---|
| Chờ duyệt | Không được tự đổi | Có thể đặt (reset lại để xem lại) |
| Đã duyệt | Không | Có |
| Không duyệt | Không | Có |
| **Thiếu thông tin** | Không | **Có** |

> NSPT không được tự ý thay đổi `line_approve`. NSPT chỉ được **cập nhật nội dung dòng** khi dòng ở trạng thái `'Thiếu thông tin'` (xem Mục 3).

---

## 3. Quy tắc "sửa dòng khi phiếu đang Chờ duyệt"

### 3.1 Vấn đề phân quyền hiện tại

Code hiện tại (`service.py` — `update_survey`):

```python
if s.status not in ("draft", "rejected"):
    raise HTTPException(400, "Chỉ sửa được khi ở trạng thái Nháp/Từ chối")
```

Tức là: khi phiếu ở trạng thái `submitted` (Chờ duyệt), **không ai được sửa nội dung dòng**. Đây là nguyên nhân gây kẹt khi dòng thiếu thông tin.

### 3.2 Luồng mới — mở khóa có kiểm soát

```
Phiếu = submitted
        │
        ├─► Quản lý đặt dòng X = 'Thiếu thông tin' + ghi note
        │          └─► Hệ thống gửi thông báo cho NSPT (tùy chọn)
        │
        └─► NSPT được phép cập nhật NỘI DUNG dòng X (chỉ dòng đó, không phải cả phiếu)
                    └─► Sau khi lưu → trạng thái dòng X tự reset về 'Chờ duyệt'
                                └─► Quản lý xem lại và duyệt/từ chối/thiếu thông tin
```

### 3.3 Phân quyền chi tiết theo trường hợp

| Trạng thái phiếu | Trạng thái dòng | Người | Được làm |
|---|---|---|---|
| `draft` / `rejected` | bất kỳ | NSPT có `survey.write` | Sửa toàn bộ phiếu + dòng |
| `submitted` | bất kỳ | Quản lý có `survey.approve` | Sửa `line_approve` + `line_approve_note` (qua endpoint `/line-approve`) |
| `submitted` | `missing_info` | NSPT có `survey.write` | **Sửa nội dung dòng đó** (các trường khác `line_approve`); KHÔNG được sửa dòng ở trạng thái khác |
| `submitted` | `Chờ duyệt` / `Đã duyệt` / `Không duyệt` | NSPT | Chỉ đọc |
| `approved` | bất kỳ | Bất kỳ | Chỉ đọc |

### 3.4 API endpoint mới cho phép sửa dòng cụ thể

Cần thêm endpoint:

```
PATCH /api/surveys-{type}/{sid}/lines/{line_id}/fill
```

- Yêu cầu: phiếu phải ở `submitted`, dòng phải ở `missing_info`, caller phải là người tạo phiếu hoặc có `survey.write`.
- Cho phép cập nhật tất cả trường nội dung của dòng (trừ `line_approve`, `line_approve_note`).
- Sau khi lưu: tự động set `line_approve = 'Chờ duyệt'` (reset lại để quản lý xem lại).
- Ghi audit log: `"fill_missing"`.

---

## 4. Màn báo cáo "NCC & Sản phẩm đang khảo sát"

### 4.1 Vị trí trong hệ thống

- Menu: **Báo cáo** → tab mới **"KS: NCC & Sản phẩm"** (đặt cạnh các tab hiện có trong `Reports.tsx`).
- Route: `/reports/survey-lines` (hoặc thêm tab `survey_lines` vào `TABS` trong `Reports.tsx`).
- Đây là **màn báo cáo riêng theo dòng**, không phải danh sách phiếu.

### 4.2 Mô tả UI tổng quan

```
┌─────────────────────────────────────────────────────────────────────┐
│  Báo cáo — KS: NCC & Sản phẩm đang khảo sát          [Xuất CSV]   │
├─────────────────────────────────────────────────────────────────────┤
│  FILTER: [Loại dòng ▾] [Trạng thái dòng ▾] [Phân loại ▾]         │
│          [Từ ngày ___] [Đến ngày ___] [NCC ___]     [Lọc] [Reset] │
├─────────────────────────────────────────────────────────────────────┤
│  Thẻ tóm tắt: Tổng dòng | Chờ duyệt | Đã duyệt | Không duyệt | Thiếu TT │
├─────────────────────────────────────────────────────────────────────┤
│  Bảng kết quả (xem Mục 4.4)                                        │
│  [← Trước]  Trang 1/N  [Sau →]                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Bộ lọc (Filter)

| Trường filter | Kiểu | Mô tả |
|---|---|---|
| **Loại dòng** | Dropdown | `Tất cả` / `NCC (Supplier)` / `Sản phẩm (Product)` |
| **Trạng thái dòng** | Multi-select dropdown | `Chờ duyệt` / `Đã duyệt` / `Không duyệt` / `Thiếu thông tin` |
| **Phân loại VTBB** | Dropdown | Các nhóm `item_group` hiện có (Bao bì, Nguyên liệu, In ấn, Chai lọ, Hóa chất, ...) |
| **NCC** | Text search | Lọc theo `supplier_code` hoặc `supplier_name` (tìm gần đúng) |
| **Từ ngày** | Date picker | Lọc theo `contact_date` ≥ ngày chọn |
| **Đến ngày** | Date picker | Lọc theo `contact_date` ≤ ngày chọn |
| **Trạng thái phiếu** | Dropdown | `Tất cả` / `Nháp` / `Chờ duyệt` / `Đã duyệt` / `Từ chối` — cho phép admin thấy dòng từ phiếu đang chờ |
| **NSPT** | Text search | Lọc theo người phụ trách phiếu |

> Mặc định hiển thị: Loại dòng = Tất cả, Trạng thái dòng = `Chờ duyệt` + `Thiếu thông tin` (focus vào các dòng chưa xong).

### 4.4 Bảng kết quả — cột hiển thị

#### Cột chung (hiển thị cho cả 2 loại dòng)

| # | Cột | Nguồn dữ liệu | Ghi chú |
|---|---|---|---|
| 1 | Loại | `line_type` (tính toán) | `NCC` / `SP` |
| 2 | Mã phiếu | `tab_survey.code` | Link sang phiếu chi tiết |
| 3 | Ngày tiếp nhận phiếu | `tab_survey.received_date` | |
| 4 | Phân loại VTBB | `tab_survey.item_group` | |
| 5 | NSPT phụ trách | `tab_survey.nspt` | |
| 6 | NCC (viết tắt) | `supplier_code` | Từ dòng NCC hoặc dòng SP |
| 7 | Tên NCC | `supplier_name` (dòng NCC) / lookup từ `supplier_code` (dòng SP) | |
| 8 | Ngày liên hệ | `contact_date` | |
| 9 | Ngày dự kiến trả KQ | `result_date` | |
| 10 | **Trạng thái dòng** | `line_approve` | Badge màu |
| 11 | **Ghi chú duyệt dòng** | `line_approve_note` | Hiển thị lý do thiếu thông tin |
| 12 | Trạng thái phiếu | `tab_survey.status` | Badge: Nháp/Chờ duyệt/Đã duyệt/Từ chối |

#### Cột riêng — dòng NCC (`line_type = 'supplier'`)

| # | Cột | Nguồn | Ghi chú |
|---|---|---|---|
| 13 | MST NCC | `tax_code` | |
| 14 | Người liên hệ | `contact_person` | |
| 15 | Nhóm SP cung ứng | `supply_group` | |
| 16 | Mức tin cậy | `reliability` | |

#### Cột riêng — dòng SP (`line_type = 'product'`)

| # | Cột | Nguồn | Ghi chú |
|---|---|---|---|
| 13 | Tên SP | `product_name` | |
| 14 | Thông số KT | `spec` | Hiển thị rút gọn, xem đầy đủ khi hover/click |
| 15 | Giá theo sản lượng | `price_by_volume` | Format số, VNĐ |
| 16 | Thành tiền | `amount` | |
| 17 | KQ LAB | `lab_result` | |

> **Gợi ý UX:** Bảng mặc định hiển thị các cột chung (1–12). Người dùng có thể toggle hiện/ẩn cột riêng theo loại. Khi lọc `Loại dòng = NCC` → ẩn cột SP, và ngược lại.

### 4.5 Thẻ tóm tắt (Summary cards)

Hiển thị bên trên bảng, tự động cập nhật theo filter đang áp dụng:

| Thẻ | Nội dung |
|---|---|
| Tổng dòng | Tổng số dòng khớp filter |
| Chờ duyệt | Số dòng `line_approve = 'Chờ duyệt'` |
| Đã duyệt | Số dòng `line_approve = 'Đã duyệt'` |
| Không duyệt | Số dòng `line_approve = 'Không duyệt'` |
| Thiếu thông tin | Số dòng `line_approve = 'Thiếu thông tin'` — **Hiển thị màu tím, nổi bật** |

### 4.6 Tương tác trên bảng

- **Click mã phiếu** → điều hướng sang màn chi tiết phiếu (`/surveys-supplier/{id}` hoặc `/surveys-product/{id}`).
- **Sắp xếp** theo cột: Ngày tiếp nhận, Trạng thái dòng, NCC.
- **Phân trang**: 50 dòng/trang mặc định (có thể chọn 20/50/100).
- **Xuất CSV**: xuất toàn bộ kết quả theo filter hiện tại (không phân trang — xuất hết).

---

## 5. Data Model

### 5.1 Thay đổi tập giá trị `line_approve`

Cột `line_approve` trong cả 2 bảng (`tab_survey_supplier_line` và `tab_survey_product_line`) hiện là `String(20)`.

**Tập giá trị hợp lệ mới:**

```python
LINE_APPROVE_VALUES = ['', 'Chờ duyệt', 'Đã duyệt', 'Không duyệt', 'Thiếu thông tin']
```

Độ dài tối đa "Thiếu thông tin" = 16 ký tự < 20 → **không cần thay đổi kiểu cột**, chỉ cần cập nhật validation ở tầng service/schema.

### 5.2 Thêm cột mới: không cần

`line_approve_note` (kiểu `Text`) đã tồn tại trong cả 2 bảng — dùng để ghi lý do "Thiếu thông tin". Không cần thêm cột mới.

### 5.3 Migration DB

**Không cần migration schema** (không thêm/sửa cột). Chỉ cần:
1. Cập nhật validation trong schema Pydantic (nếu có enum validate).
2. Cập nhật front-end options list.

> Nếu sau này muốn thêm tracking "ai đặt missing_info lúc mấy giờ" → có thể thêm cột `line_missing_info_at` (String(20)) và `line_missing_info_by` (BigInteger), nhưng không bắt buộc cho Task 8.

---

## 6. API

### 6.1 Endpoint báo cáo dòng (MỚI)

```
GET /api/reports/survey-lines
```

**Query parameters:**

| Param | Kiểu | Mô tả |
|---|---|---|
| `line_type` | `supplier` / `product` / bỏ trống | Lọc loại dòng |
| `line_approve` | String (multi, dấu phẩy) | Lọc trạng thái dòng, VD: `Chờ duyệt,Thiếu thông tin` |
| `item_group` | String | Lọc phân loại |
| `supplier_code` | String | Tìm gần đúng NCC |
| `survey_status` | String | Lọc trạng thái phiếu header |
| `nspt` | String | Lọc NSPT |
| `from_date` | YYYY-MM-DD | Lọc `contact_date >=` |
| `to_date` | YYYY-MM-DD | Lọc `contact_date <=` |
| `page` | int, default 1 | Số trang |
| `page_size` | int, default 50 | Số dòng/trang |
| `export` | `csv` | Nếu có → trả file CSV (bỏ qua phân trang) |

**Response (JSON):**

```json
{
  "total": 123,
  "summary": {
    "pending": 40,
    "approved": 50,
    "rejected": 20,
    "missing_info": 13
  },
  "items": [
    {
      "line_id": 101,
      "line_type": "supplier",
      "survey_id": 10,
      "survey_code": "KS00010",
      "survey_status": "submitted",
      "received_date": "2026-06-01",
      "item_group": "Bao bì",
      "nspt": "Nguyễn Văn A",
      "supplier_code": "NCC001",
      "supplier_name": "Công ty TNHH ABC",
      "contact_date": "2026-06-05",
      "result_date": "2026-06-20",
      "line_approve": "Thiếu thông tin",
      "line_approve_note": "Cần bổ sung MST và link báo giá",
      // ... các trường riêng của supplier hoặc product
    }
  ]
}
```

**Logic backend:**

```python
# Gộp cả 2 bảng dòng thành 1 kết quả (UNION ALL)
supplier_q = db.query(SurveySupplierLine, Survey, literal("supplier").label("line_type"))
             .join(Survey, Survey.id == SurveySupplierLine.survey_id)

product_q  = db.query(SurveyProductLine, Survey, literal("product").label("line_type"))
             .join(Survey, Survey.id == SurveyProductLine.survey_id)

# Áp filter, UNION ALL, phân trang
```

### 6.2 Endpoint sửa dòng khi phiếu đang chờ duyệt (MỚI)

```
PATCH /api/surveys-{type}/{sid}/lines/{line_id}/fill
```

**Body:** Các trường nội dung của dòng (tương tự body update dòng bình thường, nhưng KHÔNG bao gồm `line_approve`, `line_approve_note`).

**Điều kiện thực hiện (backend phải kiểm tra):**
1. Phiếu `sid` tồn tại và có `status = 'submitted'`.
2. Dòng `line_id` thuộc phiếu `sid`.
3. Dòng có `line_approve = 'Thiếu thông tin'`.
4. Caller có quyền `survey.write` VÀ là người tạo phiếu (hoặc Admin).

**Hành động sau khi lưu:**
- Cập nhật các trường nội dung dòng.
- **Tự động set `line_approve = 'Chờ duyệt'`** (reset để quản lý xem lại).
- Ghi audit: `record(db, user_id, "survey", sid, "fill_missing", f"Dòng #{line_id} đã bổ sung thông tin")`.

**Response:** Trả về dòng đã cập nhật.

### 6.3 Endpoint đặt trạng thái dòng (endpoint hiện có — mở rộng)

Endpoint hiện có:
```
PATCH /api/surveys-{type}/{sid}/line-approve
```

Hàm `approve_lines` trong `service.py` chỉ cập nhật `line_approve` và `line_approve_note`. Cần **thêm validation**:

- Nếu `line_approve = 'Thiếu thông tin'` → bắt buộc `line_approve_note` không được rỗng (lỗi 400 nếu thiếu).
- Chỉ user có `survey.approve` mới gọi được (đã có kiểm tra hiện tại).

---

## 7. Phân quyền

### 7.1 Xem màn báo cáo

| Role / Permission | Xem báo cáo `GET /api/reports/survey-lines` | Xuất CSV |
|---|---|---|
| `survey.read` | Chỉ thấy dòng thuộc phiếu mình tạo (scope) | Có (trong phạm vi scope) |
| `survey.approve` hoặc Admin | Thấy tất cả dòng | Có |

> Áp dụng cùng cơ chế `apply_scope` đang dùng cho danh sách phiếu trong `controller.py`.

### 7.2 Thao tác trên dòng

| Thao tác | Permission cần | Điều kiện bổ sung |
|---|---|---|
| Đặt `line_approve` = bất kỳ giá trị | `survey.approve` | Phiếu ở `submitted` hoặc `draft` |
| Đặt `line_approve = 'Thiếu thông tin'` | `survey.approve` | `line_approve_note` không được rỗng |
| Sửa nội dung dòng (endpoint `/fill`) | `survey.write` | Phiếu `submitted`, dòng `Thiếu thông tin`, là người tạo phiếu hoặc Admin |

---

## 8. Tiêu chí nghiệm thu (Acceptance Checklist)

### 8.1 Trạng thái dòng "Thiếu thông tin"

- [ ] Dropdown `line_approve` trong màn chi tiết phiếu (khi phiếu `submitted`) hiển thị đủ 4 giá trị, bao gồm "Thiếu thông tin".
- [ ] Khi chọn "Thiếu thông tin" mà bỏ trống `line_approve_note` → hệ thống báo lỗi, không lưu được.
- [ ] Badge "Thiếu thông tin" hiển thị màu tím (#7c3aed) đúng theo bảng màu.
- [ ] API `PATCH /line-approve` từ chối lưu "Thiếu thông tin" khi không có note.

### 8.2 Sửa dòng khi phiếu đang Chờ duyệt

- [ ] NSPT mở phiếu đang `submitted` → chỉ thấy dòng `Thiếu thông tin` có nút/trường chỉnh sửa; các dòng khác bị khóa.
- [ ] NSPT lưu nội dung dòng (qua `/fill`) → `line_approve` tự reset về "Chờ duyệt".
- [ ] Audit log ghi action `fill_missing` sau khi NSPT bổ sung thông tin.
- [ ] NSPT không thể sửa `line_approve` hay `line_approve_note` qua endpoint `/fill`.
- [ ] Quản lý vẫn thấy dòng đã reset về "Chờ duyệt" và có thể duyệt lại.

### 8.3 Màn báo cáo

- [ ] Tab "KS: NCC & Sản phẩm" xuất hiện trong menu Báo cáo.
- [ ] Bảng liệt kê dòng từ CẢ 2 bảng `tab_survey_supplier_line` và `tab_survey_product_line`.
- [ ] Filter trạng thái dòng hoạt động đúng (lọc đơn hoặc đa trạng thái).
- [ ] Filter loại dòng (NCC/SP/Tất cả) hoạt động đúng.
- [ ] Filter NCC tìm gần đúng theo `supplier_code` hoặc `supplier_name`.
- [ ] Filter theo ngày (`contact_date`) hoạt động đúng.
- [ ] Thẻ tóm tắt (summary cards) cập nhật đúng theo filter.
- [ ] Click mã phiếu điều hướng đúng sang phiếu chi tiết.
- [ ] Phân trang hoạt động.
- [ ] Xuất CSV tải về file đầy đủ các cột, đúng theo filter, không phân trang.
- [ ] Người chỉ có `survey.read` chỉ thấy dòng thuộc phiếu mình tạo.
- [ ] Admin/quản lý thấy tất cả dòng.

---

## 9. Edge Cases & Lưu ý

### 9.1 Reset trạng thái dòng sau khi NSPT bổ sung thông tin

Có 2 cách tiếp cận:

**Cách A (khuyến nghị):** Backend tự động reset `line_approve = 'Chờ duyệt'` sau khi NSPT lưu qua `/fill`.
- Ưu điểm: Đơn giản, không cần thêm bước UI.
- Nhược điểm: Quản lý không thấy rõ "dòng này mới được bổ sung" vs "dòng này chưa ai xem".

**Cách B:** Thêm trạng thái trung gian `'Đã bổ sung'` (NSPT đặt sau khi điền xong), quản lý thấy ngay "có dòng cần xem lại".
- Phức tạp hơn, cần thêm 1 giá trị vào tập trạng thái.

**Quyết định cần chốt:** Dùng Cách A cho Task 8. Nếu cần phân biệt rõ hơn → làm Cách B ở iteration sau.

### 9.2 Phiếu có nhiều dòng — một số duyệt, một số thiếu thông tin

- Phiếu vẫn ở trạng thái `submitted` cho đến khi quản lý bấm "Duyệt phiếu" hoặc "Trả lại".
- Quản lý có thể duyệt phiếu dù vẫn còn dòng `Chờ duyệt` hoặc `Thiếu thông tin` — **không bắt buộc tất cả dòng phải được xử lý trước**.
- Màn báo cáo sẽ giúp admin nhìn thấy các dòng còn tồn đọng, kể cả trong phiếu đã được duyệt tổng thể.

### 9.3 Sau Task 7 (gộp 2 phiếu thành 1 giao diện)

Task 7 gộp 2 màn khảo sát thành 1 (1 phiếu có 2 bảng: NCC và SP). Khi đó:
- `survey_type` có thể không còn phân biệt `supplier`/`product` ở header.
- Endpoint báo cáo `/api/reports/survey-lines` vẫn đọc từ 2 bảng dòng riêng, nên **không bị ảnh hưởng**.
- Màn chi tiết phiếu sau Task 7 cần hiển thị badge "Thiếu thông tin" ở cả 2 bảng dòng.

### 9.4 Thông báo (Notification)

Khi quản lý đặt dòng = `'Thiếu thông tin'`:
- **Nên** gửi thông báo cho NSPT phụ trách phiếu (dùng `trigger_notification` như đang làm với `survey_submitted`, `survey_approved`).
- Event mới: `survey_line_missing_info`.
- Nội dung thông báo: "Phiếu [code] — Dòng [NCC/SP] cần bổ sung thông tin: [note]".

### 9.5 Xuất CSV — encoding

File CSV xuất ra phải dùng **UTF-8 BOM** (`utf-8-sig`) để Excel trên Windows hiển thị đúng tiếng Việt. Xem cách làm trong các endpoint xuất CSV hiện có (nếu có), hoặc dùng:

```python
from io import StringIO
import csv
output = StringIO()
output.write('﻿')  # BOM
writer = csv.DictWriter(output, fieldnames=[...])
```

### 9.6 Hiệu năng query UNION ALL

Khi dữ liệu lớn, query gộp 2 bảng có thể chậm. Cần:
- Index trên `tab_survey_supplier_line.line_approve` và `tab_survey_product_line.line_approve`.
- Index trên `tab_survey_supplier_line.survey_id` và `tab_survey_product_line.survey_id` (đã có — `index=True` trong model).
- Nếu cần, có thể tạo view hoặc materialized table, nhưng không bắt buộc cho giai đoạn đầu.

---

## 10. Câu hỏi mở

| # | Câu hỏi | Mức độ ưu tiên | Ghi chú |
|---|---|---|---|
| 1 | NSPT có được phép tự đặt trạng thái dòng về "Chờ duyệt" thủ công sau khi bổ sung xong, hay để backend tự động reset? | Cao — cần chốt trước khi code | Xem Mục 9.1, khuyến nghị auto-reset |
| 2 | Khi quản lý đặt "Thiếu thông tin" → có gửi email thông báo NSPT không, hay chỉ thông báo trong app? | Trung bình | Dựa vào cấu hình email hiện có (`email-config-procurement.md`) |
| 3 | Màn báo cáo có cần phân quyền theo phạm vi công ty (company scope) không? | Thấp | Phụ thuộc cấu trúc multi-company |
| 4 | Có cần lưu lịch sử thay đổi `line_approve` (ai đặt khi nào) riêng, hay dùng audit log chung là đủ? | Thấp | Audit log chung là đủ cho Task 8 |
| 5 | Số dòng/trang mặc định trong báo cáo: 50 hay 100? | Thấp | Để người dùng chọn |

---

## Phụ lục — Tóm tắt thay đổi cần làm

### Backend

| File | Thay đổi |
|---|---|
| `backend/app/modules/survey/service.py` | Thêm hàm `fill_missing_line()`, thêm validation `line_approve_note` bắt buộc khi `missing_info` trong `approve_lines()` |
| `backend/app/modules/survey/controller.py` | Thêm endpoint `PATCH /{sid}/lines/{line_id}/fill` |
| `backend/app/modules/survey/schema.py` | Cập nhật enum/validation `line_approve` (thêm `'Thiếu thông tin'`) |
| `backend/app/modules/reports/controller.py` | Thêm endpoint `GET /api/reports/survey-lines` |
| `backend/app/modules/reports/service.py` | Logic query UNION ALL 2 bảng dòng + filter + phân trang + xuất CSV |
| `backend/app/modules/notification/...` | Thêm event `survey_line_missing_info` |

### Frontend

| File | Thay đổi |
|---|---|
| `frontend/src/pages/SurveyDetail.tsx` | Thêm `'Thiếu thông tin'` vào `APPROVE_OPTS` và `APPROVE_COLOR`; thêm UI cho NSPT sửa dòng khi `missing_info` |
| `frontend/src/pages/Reports.tsx` | Thêm tab `survey_lines` vào `TABS`; render bảng báo cáo dòng + filter + summary cards + xuất CSV |
| `frontend/src/config/cruds.tsx` | Thêm badge color cho `'Thiếu thông tin'` nếu dùng hàm badge chung |
