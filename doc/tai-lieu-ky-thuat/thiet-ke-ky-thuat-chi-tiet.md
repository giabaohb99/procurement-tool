# TÀI LIỆU THIẾT KẾ KỸ THUẬT CHI TIẾT (Low-Level Design — LLD)
## Mini Tool Quản lý Thu Mua — DEGO Holding

| | |
|---|---|
| **Phiên bản** | v1.0 |
| **Ngày** | 2026-07-08 |
| **Loại** | Thiết kế chi tiết — Từ điển dữ liệu + Liên kết bảng + Phân quyền |
| **Đi kèm** | [technical-design.md](technical-design.md) (tổng quan) · [so-do-ky-thuat.md](so-do-ky-thuat.md) (sơ đồ, ERD) |

> Tài liệu này mô tả **chi tiết từng bảng** (cột, kiểu, ý nghĩa), **cách các bảng liên kết** với nhau, và **cơ chế phân quyền**. Số liệu trích **trực tiếp từ mã nguồn** (SQLAlchemy models + core RBAC).

---

## Mục lục
1. Quy ước chung
2. Tổng quan 39 bảng (theo nhóm)
3. Từ điển dữ liệu chi tiết
   - 3.1 Danh mục nền
   - 3.2 Yêu cầu khảo sát
   - 3.3 Phiếu khảo sát
   - 3.4 Yêu cầu mua
   - 3.5 Đơn mua hàng
   - 3.6 Nhận hàng · Tồn kho
   - 3.7 Công nợ · Thanh toán
   - 3.8 Hệ thống & Phân quyền
4. Bản đồ liên kết bảng (khóa mềm)
5. Phân quyền (RBAC) chi tiết
6. Quy tắc toàn vẹn & tác dụng phụ

---

## 1. Quy ước chung

### 1.1 Cột chuẩn — mọi bảng đều có (AuditMixin)
| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT PK, auto-increment | Khóa chính |
| `created_at` | DATETIME (server default now) | Thời điểm tạo |
| `created_by` | BIGINT | `user.id` người tạo |
| `updated_at` | DATETIME (auto onupdate) | Thời điểm sửa gần nhất |
| `updated_by` | BIGINT | `user.id` người sửa |

> Các bảng bên dưới **chỉ liệt kê cột nghiệp vụ**; ngầm hiểu đã có 5 cột chuẩn trên.

### 1.2 Quy ước
- **Tên bảng:** `tab_<tên>` (VD `tab_purchase_order`).
- **Liên kết mềm (soft reference):** hệ thống **không dùng khóa ngoại cứng (FK)** ở DB. Các bảng liên kết nhau qua:
  - **`*_id`** (BIGINT) → trỏ tới `id` bảng khác (VD `po_id`, `company_id`, `survey_request_id`).
  - **`*_code`** (VARCHAR) → trỏ tới cột `code` bảng khác (VD `supplier_code`, `product_code`, `pr_code`).
  - Một số nơi liên kết theo **tên** (VD `department` lưu *tên phòng*, `item_group` lưu *tên phân loại*).
- **Kiểu tiền:** `NUMERIC(18,2)`; **số lượng:** `NUMERIC(18,3)`; **VAT suất:** `NUMERIC(5,4)` (0.08 = 8%).
- **Ngày:** lưu chuỗi `VARCHAR(10)` dạng `YYYY-MM-DD` (trừ `created_at/updated_at` là DATETIME).
- **Trạng thái:** chuỗi tiếng Anh chuẩn (`draft`, `approved`…) hoặc tiếng Việt tùy bảng (ghi rõ ở từng bảng).

---

## 2. Tổng quan 40 bảng (theo nhóm)

| Nhóm | Bảng |
|---|---|
| **Danh mục nền** | `tab_product`, `tab_supplier`, `tab_company`, `tab_department`, `tab_employee`, `tab_warehouse`, `tab_unit`, `tab_item_group`, `tab_brand`, `tab_category_assignee`, `tab_contract` |
| **Yêu cầu khảo sát** | `tab_survey_request`, `tab_survey_request_line`, `tab_survey_request_option` |
| **Phiếu khảo sát** | `tab_survey`, `tab_survey_supplier_line`, `tab_survey_product_line` |
| **Yêu cầu mua** | `tab_purchase_request`, `tab_purchase_request_item` |
| **Đơn mua hàng** | `tab_purchase_order`, `tab_po_item`, `tab_po_delivery` |
| **Nhận hàng · Tồn kho** | `tab_goods_receipt`, `tab_inventory`, `tab_inventory_move` |
| **Công nợ · Thanh toán** | `tab_payable`, `tab_payment_request`, `tab_payment_request_line` |
| **Hệ thống & Phân quyền** | `tab_user`, `tab_role`, `tab_permission`, `tab_user_role`, `tab_user_scope`, `tab_audit_log`, `tab_notification`, `tab_attachment`, `tab_setting`, `tab_email_log`, `tab_report_snapshot`, **`tab_push_subscription`** |

---

## 3. Từ điển dữ liệu chi tiết

> Cột **Liên kết** = bảng/cột mà giá trị này trỏ tới (khóa mềm).

### 3.1 Danh mục nền

#### `tab_product` — Sản phẩm (VTBB/NL)
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(50) UNIQUE | Mã VTBB/NL | ← nhiều bảng trỏ tới qua `product_code` |
| name | VARCHAR(255) | Tên VTBB/NL | |
| invoice_name | VARCHAR(255) | Tên trên hóa đơn | |
| legal_name | VARCHAR(255) | Tên pháp lý | |
| item_group | VARCHAR(50) | Phân loại (Thùng, Nhãn…) | → `tab_item_group.name` (theo tên) |
| unit | VARCHAR(25) | ĐVT | → `tab_unit.name` |
| **hh_code** | VARCHAR(50) INDEX | **Mã HH (liên kết sản phẩm hoàn chỉnh)** | 1 HH ↔ nhiều VTBB |
| **hh_name** | VARCHAR(255) | Tên Sản phẩm (HH) | |
| is_active | BOOLEAN | Còn dùng | |

#### `tab_supplier` — Nhà cung cấp
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(50) UNIQUE | Tên viết tắt (mã NCC) | ← `supplier_code` nhiều bảng |
| name | VARCHAR(255) | Tên pháp lý | |
| legal_type | VARCHAR(30) | Công ty/Cá nhân/Hộ KD… | |
| tax_code | VARCHAR(25) | MST | |
| address | TEXT | Địa chỉ | |
| **supplier_type** | VARCHAR(20) | `goods` = bán hàng · `transport` = vận chuyển | Quyết định luồng công nợ |
| contact_person, phone | VARCHAR | Liên hệ | |
| payment_terms | VARCHAR(255) | Hình thức thanh toán | |
| bank_account, bank_name | VARCHAR | Tài khoản ngân hàng | |
| vat | FLOAT | Suất VAT mặc định (0.08) | |
| is_active | BOOLEAN | | |

#### `tab_company` — Pháp nhân nhận hóa đơn
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(25) UNIQUE | | ← `company_id` (qua id) |
| name, tax_code, address | | | |
| invoice_email | VARCHAR(255) | Email nhận HĐ | |
| parent | BIGINT | Công ty cha (0 = gốc) | → `tab_company.id` |
| legal_representative_id | BIGINT | Người đại diện PL | → `tab_employee.id` |
| legal_rep_title | VARCHAR(100) | Chức danh đại diện | |
| is_active | BOOLEAN | | |

#### `tab_department` — Phòng ban
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(25) UNIQUE | | |
| name | VARCHAR(255) | Tên phòng | ← nhiều bảng liên kết **theo tên** (`department`) |
| company_id | BIGINT | Thuộc công ty | → `tab_company.id` |
| parent | BIGINT | Phòng cha (0 = gốc) | → `tab_department.id` |
| manager_id | BIGINT | Trưởng bộ phận | → `tab_employee.id` |
| is_active | BOOLEAN | | |

#### `tab_employee` — Nhân viên
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(25) UNIQUE | Mã NV | ← `assignee` (mã NSTM) ở dòng PR/SR |
| full_name | VARCHAR(255) | | |
| email, phone | | | |
| company_id | BIGINT | | → `tab_company.id` |
| department_id | BIGINT | | → `tab_department.id` |
| position, role_name | VARCHAR | Chức vụ | |
| status | VARCHAR(50) | Chính thức/… | |
| is_active | BOOLEAN | | |

#### `tab_category_assignee` — Phân công NSTM theo phân loại ⭐
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| item_group_id | BIGINT UNIQUE | Phân loại VTBB | → `tab_item_group.id` |
| primary_employee_id | BIGINT | NSTM **chính** | → `tab_employee.id` |
| backup_employee_id | BIGINT | NSTM **dự phòng** | → `tab_employee.id` |

> Dùng để **tự gán NSTM** cho từng dòng khi duyệt Yêu cầu khảo sát / Yêu cầu mua theo phân loại.

#### `tab_contract` — Hợp đồng
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(50) | HD00001 | |
| party_type | VARCHAR(30) | Nhà cung cấp/Khách hàng/Khác | |
| party_code | VARCHAR(50) INDEX | Mã đối tượng | → `tab_supplier.code` (khi NCC) |
| party_name | VARCHAR(255) | | |
| company_id | BIGINT | Pháp nhân ký | → `tab_company.id` |
| title, contract_type | VARCHAR | | |
| start_date, end_date | VARCHAR(10) | | |
| signed | BOOLEAN | Đã ký | |
| status | VARCHAR(30) | Hiệu lực/Hết hạn/Thanh lý | |

> **Danh mục khác:** `tab_warehouse` (kho: code, name…), `tab_unit` (ĐVT: name), `tab_item_group` (phân loại: name, dùng liên kết với `category_assignee`), `tab_brand` (thương hiệu) — cấu trúc đơn giản (code/name + is_active).

---

### 3.2 Yêu cầu khảo sát (Task 5)

#### `tab_survey_request` — Header
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(50) UNIQUE | `YCKS+DDMMYY+seq` | |
| company_id | BIGINT | Pháp nhân | → `tab_company.id` |
| requester, requester_position | VARCHAR | Người YC + chức vụ | |
| department | VARCHAR(255) INDEX | Phòng (theo tên) | → `tab_department.name` |
| head_of_dept | VARCHAR(255) | Trưởng bộ phận | |
| purpose | VARCHAR(255) | Mục đích | |
| request_date | VARCHAR(10) | | |
| **status** | VARCHAR(30) INDEX | `draft→submitted→approved→processing→survey_done→pr_created→done`; `rejected` | |
| ~~assignee_id~~ | — | **ĐÃ BỎ (CR-018)** — NSTM chính toàn phiếu; cột đã drop khỏi DB (migration `a3f5c81d7e64`). NSTM chỉ còn ở **dòng** (`tab_survey_request_line.assignee`). | — |
| note, reject_reason | TEXT | | |

#### `tab_survey_request_line` — Dòng (1 SP/nhóm cần khảo sát)
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| survey_request_id | BIGINT INDEX | Thuộc phiếu | → `tab_survey_request.id` |
| internal_line_code | VARCHAR(50) | Mã dòng nội bộ (ẨN với người YC) | |
| received_date, result_due_date | VARCHAR(10) | Ngày tiếp nhận / hạn KQ | |
| department_requester | VARCHAR(255) | BP/Người YC | |
| item_group | VARCHAR(100) INDEX | Phân loại | → `tab_item_group.name` (dùng auto-gán NSTM) |
| requirement_detail, other_requirement | TEXT | TSKT & yêu cầu | |
| request_qty | NUMERIC(18,3) | SL dự kiến mua | |
| uom | VARCHAR(25) | ĐVT | |
| proposed_price | NUMERIC(18,2) | Giá đề xuất | |
| image_file | VARCHAR(500) | Ảnh đính kèm | |
| assignee | VARCHAR(100) | Mã NSTM phụ trách dòng | → `tab_employee.code` |
| pr_id / pr_code | BIGINT / VARCHAR | PYC sinh ra từ dòng | → `tab_purchase_request` |
| is_completed | BOOLEAN | Dòng đã hoàn thành | |

#### `tab_survey_request_option` — Phương án (bảng ẩn NCC) ⭐⭐
| Cột | Kiểu | Mô tả | Liên kết / Ghi chú |
|---|---|---|---|
| survey_request_line_id | BIGINT INDEX | Thuộc dòng | → `tab_survey_request_line.id` |
| product_survey_line_id | BIGINT INDEX | Nguồn khảo sát SP | → `tab_survey_product_line.id` |
| public_id | INT | **ID ẩn danh** (Option 1,2…) | Hiện với người YC |
| display_label | VARCHAR(50) | "Option 1 — ID 789" | |
| is_chosen | BOOLEAN INDEX | Đã chọn PA | |
| chosen_by | BIGINT | Người chọn | → `tab_user.id` |
| **snap_*** (12 cột) | | **SNAPSHOT thông số** (tên SP, spec, xuất xứ, MOQ, giá theo SL, VAT, giao hàng, phí VC, mẫu, lab…) | ✅ **Hiện được** với người YC |
| **snap_internal_code** | VARCHAR(50) | Mã SP theo NCC | 🔒 **ẨN** với người YC |
| **supplier_code / supplier_name** | VARCHAR | NCC | 🔒 **ẨN** — backend whitelist không trả |
| supplier_survey_id | BIGINT | Phiếu KS nguồn | → `tab_survey.id` · 🔒 ẨN |
| nstm_note | TEXT | Ghi chú NSTM | 🔒 ẨN |

> **Cơ chế ẩn NCC:** API trả cho người YC dùng **whitelist** — chỉ các cột `snap_*` (trừ `snap_internal_code`), `public_id`, `display_label`, `is_chosen`. Các cột `supplier_*`, `snap_internal_code`, `supplier_survey_id`, `nstm_note`, `product_survey_line_id` **không bao giờ** rời backend cho người không phải thu mua.

---

### 3.3 Phiếu khảo sát

#### `tab_survey` — Header (dùng chung NCC & SP)
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(50) UNIQUE | `KS…` | ← `supplier_survey_id` (option) |
| survey_type | VARCHAR(10) | `supplier` \| `product` | |
| pr_code | VARCHAR(50) | PYC liên kết | → `tab_purchase_request.code` |
| received_date, result_due_date | VARCHAR(10) | | |
| item_group | VARCHAR(100) | Phân loại | → `tab_item_group.name` |
| requirement_detail | TEXT | Yêu cầu KT & CL | |
| request_qty | NUMERIC(18,3) | SL dự kiến | |
| nspt | VARCHAR(100) | NSPT = người tạo | |
| has_product_code, item_code, item_name | | SP khi đã có mã | → `tab_product.code` |
| uom, proposed_rate | | ĐVT, giá đề xuất | |
| approve_status | VARCHAR(20) | Duyệt \| Không duyệt (cả phiếu) | |
| status | VARCHAR(30) | draft/… | |

#### `tab_survey_supplier_line` — Dòng khảo sát NCC (~28 cột)
Cột chính: `survey_id`(→survey.id), `supplier_code`(→supplier.code), `supplier_name`, `tax_code`, địa chỉ ĐK/kho, `contact_*`, chính sách (invoice/debt/delivery), `reliability`, **`line_approve`** (Đã duyệt/Không duyệt — duyệt **từng dòng**), `line_approve_note`, `note` (nội bộ — KHÔNG show ra Yêu cầu khảo sát).

#### `tab_survey_product_line` — Dòng khảo sát SP (~30 cột) ⭐
Nguồn dữ liệu cho **option**. Cột chính:
| Cột | Kiểu | Mô tả |
|---|---|---|
| survey_id | BIGINT | → `tab_survey.id` |
| supplier_code | VARCHAR(50) | → `tab_supplier.code` |
| internal_code | VARCHAR(50) | Mã SP theo NCC |
| product_name, spec, origin | | Tên/TSKT/xuất xứ |
| quote_unit, moq, price_by_volume, volume_range, vat | | Báo giá theo sản lượng |
| shipping_cost, delivery_time, delivery_place | | Giao hàng |
| sample_ready, sample_date, lab_result, lab_note | | Mẫu & lab |
| **line_approve** | VARCHAR(20) | **"Đã duyệt"** → mới được tạo option |
| note | TEXT | Nội bộ (không show) |

---

### 3.4 Yêu cầu mua

#### `tab_purchase_request` — Header (PYC)
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(50) UNIQUE | | ← `pr_code` (PO, survey, sr_line) |
| company_id | BIGINT | | → `tab_company.id` |
| requester, requester_position, department, head_of_dept | | | department → tên phòng |
| purpose, request_date, need_date | | | |
| status | VARCHAR(30) | `draft\|submitted\|approved\|dispatched\|processing\|completed\|rejected\|cancelled`. `approved` = TP duyệt xong, CHƯA có NSTM; `dispatched` ("Đã điều phối", CR-034) = thu mua duyệt lần 2, đã tự phân bổ NSTM — mốc bắt đầu tạo được ĐMH | |
| is_urgent | BOOLEAN | | |
| vat_rate | NUMERIC(5,4) | | |
| assignee_id | BIGINT | | → `tab_employee.id` |
| suggested_supplier* | | NCC đề xuất + MST + liên hệ | |
| quote_filename, quote_file_url | | File báo giá | |
| show_code_on_print | BOOLEAN | Tùy chọn in | |

#### `tab_purchase_request_item` — Dòng
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| pr_id | BIGINT INDEX | | → `tab_purchase_request.id` |
| product_code, product_name | | | → `tab_product.code` |
| item_group, group_desc | | Phân loại + mô tả | |
| qty, unit, price, amount | | SL/ĐVT/giá/thành tiền | |
| warehouse | VARCHAR(100) | Kho nhận | → `tab_warehouse` |
| required_date | VARCHAR(10) | Ngày cần (theo dòng) | |
| expected_date | VARCHAR(10) | Thời gian dự kiến có hàng — mặc định = `required_date` lúc TẠO dòng (CR-064); đổi giá trị đã có phải kèm lý do | ↔ `tab_po_item.expected_date` |
| assignee | VARCHAR(100) | Mã NSTM | → `tab_employee.code` |
| line_status | VARCHAR(30) | "Chưa đặt hàng"… | |
| progress_note | TEXT | | |

---

### 3.5 Đơn mua hàng

#### `tab_purchase_order` — Header (PO)
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(50) UNIQUE | PO00045 | ← `po_code` (payable, GR, PR line) |
| misa_code | VARCHAR(50) | Mã đơn MISA (tham chiếu) | |
| pr_code | VARCHAR(50) | Nguồn PYC | → `tab_purchase_request.code` |
| survey_code | VARCHAR(50) | | → `tab_survey.code` |
| company_id | BIGINT | Pháp nhân nhận HĐ | → `tab_company.id` |
| supplier_code, supplier_name | | NCC bán hàng | → `tab_supplier.code` |
| department, nspt | | | |
| order_date | VARCHAR(10) INDEX | | |
| vat_rate | NUMERIC(5,4) | | |
| payment_terms | VARCHAR(255) | Hình thức TT | |
| is_urgent | BOOLEAN | | |
| status | VARCHAR(30) | `draft\|submitted\|approved\|partial\|received\|cancelled` | |
| note, approve_note | TEXT | | |

#### `tab_po_item` — Dòng hàng
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| po_id | BIGINT INDEX | | → `tab_purchase_order.id` |
| product_code, product_name, invoice_name | | | → `tab_product.code` |
| item_group, spec | | Phân loại, xuất xứ/TSKT | |
| **fg_code / fg_name** | VARCHAR | **Mã HH / Tên HH** (tự gắn từ product) | ← `tab_product.hh_code/hh_name` |
| invoice_no | VARCHAR(50) | Số hóa đơn theo SP | |
| supplier_ready | BOOLEAN | NCC có sẵn hàng | |
| required_date | VARCHAR(10) | Ngày yêu cầu có hàng | |
| **expected_date** | VARCHAR(10) | **Dự kiến có hàng** (CR-062) — chép xuống từ dòng YCMH khi trống; ngày MUỘN NHẤT của các dòng cùng `pr_code`+mã hàng cuộn ngược lên YCMH **chỉ khi ô bên đó trống**, lệch thì cảnh báo popup ở màn ĐMH | ↔ `tab_pr_item.expected_date` |
| unit | VARCHAR(25) | | |
| qty_request, qty_order | NUMERIC(18,3) | SL yêu cầu / đặt | |
| price, vat, amount | NUMERIC | Giá / %VAT / thành tiền | |
| qty_received, qty_remaining | NUMERIC(18,3) | Auto = Σ đã nhận / còn lại | |
| line_status | VARCHAR(30) | Chưa giao/Đang giao/Đủ | |
| warehouse_code | VARCHAR(50) | Kho mặc định dòng | → `tab_warehouse` |

#### `tab_po_delivery` — Lần giao (1 dòng có thể giao nhiều lần) ⭐
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| po_id | BIGINT INDEX | | → `tab_purchase_order.id` |
| po_item_id | BIGINT INDEX | Dòng hàng | → `tab_po_item.id` |
| delivery_no | BIGINT | Lần giao thứ | |
| warehouse_code | VARCHAR(50) | Kho nhận | → `tab_warehouse` |
| carrier_code, carrier_name | | Đơn vị vận chuyển | → `tab_supplier.code` (type=transport) |
| ship_qty, ship_unit | | SL giao | |
| received_qty | NUMERIC(18,3) | SL thực nhận | |
| promised_date, received_date | VARCHAR(10) | Cam kết giao / **thực nhận**. `promised_date` mặc định = `tab_po_item.required_date` lúc TẠO lần giao (CR-063), sau đó sửa tự do | |
| ~~expected_date~~ | VARCHAR(10) | **BỎ DÙNG (CR-062)** — không nơi nào ghi, giữ cột theo luật "CSDL cũ: chỉ thêm, không sửa". "Dự kiến có hàng" nay ở `tab_po_item.expected_date` | |
| std_days, regulated_date | | Số ngày & ngày quy định | |
| diff_promise, diff_regulated, diff_required | BIGINT | Chênh lệch tiến độ (<0 = trễ) | |
| shipping_unit_price, shipping_amount | NUMERIC | Phí vận chuyển | → sinh công nợ VC |
| invoice_no, qc_result, status | | Hóa đơn, QC, trạng thái | |

> **Khi `received_date` được ghi (nhận hàng)** → hàm `recompute_effects` sinh **Goods Receipt + Inventory move + Payable** (xem mục 6).

---

### 3.6 Nhận hàng · Tồn kho

#### `tab_goods_receipt` — Phiếu nhập (sinh ngầm, 1 phiếu/lần giao)
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code, po_id, po_code | | | → PO |
| **delivery_id** | BIGINT **UNIQUE** | 1–1 với lần giao | → `tab_po_delivery.id` |
| company_id, warehouse_code | | | |
| product_code, product_name, unit | | | → product |
| qty_received | NUMERIC(18,3) | SL nhận | |
| received_date | VARCHAR(10) | | |
| qc_result | VARCHAR(20) | Đạt/Thiếu/Lỗi | |

#### `tab_inventory` — Tồn hiện tại (key: công ty + kho + SP)
| Cột | Kiểu | Mô tả |
|---|---|---|
| company_id, warehouse_code, product_code (đều INDEX) | | Khóa logic tồn |
| product_name, unit | | |
| qty | NUMERIC(18,3) | Tồn hiện tại |
| avg_cost | NUMERIC(18,2) | Đơn giá **bình quân gia quyền** |
| value | NUMERIC(18,2) | Giá trị tồn = qty × avg_cost |

#### `tab_inventory_move` — Sổ nhập/xuất
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| company_id, warehouse_code, product_code | | | |
| qty | NUMERIC(18,3) | >0 nhập, <0 xuất/điều chỉnh | |
| unit_price | NUMERIC(18,2) | Đơn giá nhập (cho BQ gia quyền) | |
| ref_type | VARCHAR(20) | `gr` (nhận hàng) \| `adjust` | |
| ref_id | BIGINT | | → `tab_po_delivery.id` (khi gr) |

---

### 3.7 Công nợ · Thanh toán

#### `tab_payable` — Công nợ phải trả (sinh ngầm; 1 dòng = 1 lần giao × 1 luồng) ⭐
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| company_id | BIGINT INDEX | | → company |
| supplier_code, supplier_name | | | → supplier |
| **source_type** | VARCHAR(20) INDEX | **`goods`** (nợ NCC bán) \| **`shipping`** (nợ đơn vị VC) | 2 luồng |
| ref_type | VARCHAR(20) | `delivery` | |
| ref_id | BIGINT INDEX | | → `tab_po_delivery.id` |
| po_id, po_code | | | → PO |
| invoice_no | VARCHAR(50) | | |
| incur_date | VARCHAR(10) INDEX | Ngày phát sinh (= ngày nhận) | |
| period | VARCHAR(7) INDEX | Năm (lọc/nhóm) | |
| due_date | VARCHAR(10) INDEX | Hạn trả | |
| amount, vat, total | NUMERIC(18,2) | Trước VAT / VAT / phải trả | |
| paid_amount, remaining | NUMERIC(18,2) | Đã trả / còn lại | |
| status | VARCHAR(20) INDEX | Chờ TT / Trả một phần / Đã TT | |

#### `tab_payment_request` — Phiếu yêu cầu thanh toán (1 NCC/phiếu)
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| code | VARCHAR(50) | YCTT00045 | |
| supplier_code, supplier_name | | 1 NCC/phiếu | → supplier |
| company_id | BIGINT | | → company |
| source_type | VARCHAR(20) | goods \| shipping | |
| request_date, total | | | |
| payment_method | VARCHAR(20) | `transfer` (Chuyển khoản, mặc định) \| `cash` (Tiền mặt) — CR-035; `cash` thì bản in bỏ cụm Thông tin chuyển khoản | |
| status | VARCHAR(20) | `draft\|submitted\|approved\|paid` | |

#### `tab_payment_request_line` — Dòng (gom nhiều khoản nợ)
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| request_id | BIGINT INDEX | | → `tab_payment_request.id` |
| payable_id | BIGINT | Khoản nợ được gom | → `tab_payable.id` |
| po_code, invoice_no, amount | | | |

---

### 3.8 Hệ thống & Phân quyền

#### `tab_user` — Tài khoản
| Cột | Kiểu | Mô tả | Liên kết |
|---|---|---|---|
| email | VARCHAR(255) INDEX | Đăng nhập bằng email | |
| google_sub | VARCHAR(100) | OAuth Google | |
| password_hash | VARCHAR(255) | | |
| employee_id | BIGINT INDEX | Gắn nhân viên | → `tab_employee.id` |
| avatar, is_active | | | |

#### `tab_role` — Vai trò
`code` UNIQUE, `name`, `description`. ← trỏ tới bởi permission/user_role/user_scope.

#### `tab_permission` — Quyền (vai trò × đối tượng) ⭐
| Cột | Kiểu | Mô tả |
|---|---|---|
| role_id | BIGINT INDEX | → `tab_role.id` |
| entity | VARCHAR(50) INDEX | Tên chức năng (VD `purchase_order`) |
| can_read, can_create, can_write, can_delete, can_approve, can_cancel, can_print, can_export | BOOLEAN | **8 cờ hành động** |
| scope | VARCHAR(10) | `own \| dept \| company \| all` |

#### `tab_user_role` — Gán vai trò cho user
`user_id` (→user.id), `role_id` (→role.id). 1 user có thể nhiều vai trò.

#### `tab_user_scope` — Phạm vi dữ liệu theo user (Lớp B) ⭐
| Cột | Kiểu | Mô tả |
|---|---|---|
| user_id | BIGINT INDEX | → user.id |
| role_id | BIGINT INDEX | Phạm vi theo từng vai trò (0 = chung) |
| entity | VARCHAR(50) INDEX | `''` = áp chung mọi chức năng; hoặc override 1 chức năng |
| dim | VARCHAR(20) | `company` \| `department` \| `employee` |
| value | VARCHAR(100) | Giá trị được cấp (id công ty / tên phòng / id NV) |
| is_exclude | BOOLEAN | True = **loại trừ** giá trị này |

#### `tab_push_subscription` — Đăng ký Web Push theo thiết bị ⭐
| Cột | Kiểu | Mô tả |
|---|---|---|
| user_id | BIGINT INDEX | → `tab_user.id` |
| endpoint | TEXT | URL push service của trình duyệt (mỗi thiết bị 1 dòng; dedup ở code) |
| p256dh | VARCHAR(255) | Khóa công khai thiết bị (mã hóa payload) |
| auth | VARCHAR(255) | Auth secret thiết bị |

> Endpoint 404/410 khi gửi push → bản ghi tự xóa (`push_service.send_to_users`). Lưu/cập nhật qua `push_service.save_subscription`; xóa thủ công qua `push_service.remove_subscription`.

> **Các bảng hệ thống khác:** `tab_audit_log` (ghi vết), `tab_notification` (thông báo bell), `tab_attachment` (file đính kèm), `tab_setting` (cấu hình key-value, secret mã hóa Fernet), `tab_email_log` (log email), `tab_report_snapshot` (ảnh chụp báo cáo).

---

## 4. Bản đồ liên kết bảng (khóa mềm)

> Sơ đồ ERD trực quan xem **[so-do-ky-thuat.md](so-do-ky-thuat.md) — Sơ đồ 6**. Dưới đây là bảng liên kết dạng chữ.

| Từ (cột) | → Đến (bảng.cột) | Ý nghĩa |
|---|---|---|
| `*.company_id` | `tab_company.id` | Pháp nhân |
| `*.supplier_code` | `tab_supplier.code` | Nhà cung cấp |
| `*.product_code` | `tab_product.code` | Sản phẩm |
| `po_item.fg_code/fg_name` | `tab_product.hh_code/hh_name` | Mã/Tên HH (snapshot khi chọn SP) |
| `*.department` | `tab_department.name` | Phòng (theo tên) |
| `*.assignee` (mã NV) | `tab_employee.code` | NSTM phụ trách dòng |
| `purchase_request.assignee_id` | `tab_employee.id` | NSTM chính toàn phiếu YCMH (YCBG đã bỏ trường này — CR-018) |
| `category_assignee.item_group_id` | `tab_item_group.id` | Phân loại → NSTM |
| `survey_request_line.survey_request_id` | `tab_survey_request.id` | Dòng ↔ phiếu YCKS |
| `survey_request_option.survey_request_line_id` | `tab_survey_request_line.id` | Option ↔ dòng |
| `survey_request_option.product_survey_line_id` | `tab_survey_product_line.id` | Option ← khảo sát SP |
| `survey_request_option.supplier_survey_id` | `tab_survey.id` | (ẩn) phiếu KS nguồn |
| `survey_*_line.survey_id` | `tab_survey.id` | Dòng KS ↔ phiếu KS |
| `purchase_request_item.pr_id` | `tab_purchase_request.id` | Dòng ↔ PYC |
| `purchase_order.pr_code` | `tab_purchase_request.code` | PO ← PYC |
| `po_item.po_id` | `tab_purchase_order.id` | Dòng ↔ PO |
| `po_delivery.po_item_id` | `tab_po_item.id` | Lần giao ↔ dòng |
| `goods_receipt.delivery_id` (UNIQUE) | `tab_po_delivery.id` | 1–1 nhận ↔ giao |
| `inventory_move.ref_id` (ref_type=gr) | `tab_po_delivery.id` | Phát sinh tồn ← lần giao |
| `payable.ref_id` (ref_type=delivery) | `tab_po_delivery.id` | Công nợ ← lần giao |
| `payment_request_line.payable_id` | `tab_payable.id` | Phiếu TT gom khoản nợ |
| `payment_request_line.request_id` | `tab_payment_request.id` | Dòng ↔ phiếu TT |
| `permission.role_id` / `user_role.role_id` / `user_scope.role_id` | `tab_role.id` | Phân quyền |
| `user.employee_id` | `tab_employee.id` | Tài khoản ↔ nhân viên |

---

## 5. Phân quyền (RBAC) chi tiết

### 5.1 Mô hình 3 lớp
```
User ──(tab_user_role)── Role ──(tab_permission)── Quyền theo Entity
  │                                                 (8 cờ + scope)
  └──(tab_user_scope)── Phạm vi dữ liệu cụ thể (công ty/phòng/NV, cấp/loại trừ)
```
- **Lớp A — Vai trò → Quyền (`tab_permission`):** với mỗi (vai trò × entity) định nghĩa **8 cờ hành động** + **1 cấp phạm vi**.
- **Lớp B — Phạm vi theo user (`tab_user_scope`):** giới hạn/nới cụ thể theo công ty, phòng ban, nhân sự; có thể **loại trừ** (`is_exclude`).
- 1 user có thể có **nhiều vai trò** → quyền là **HỢP (OR)** của các vai trò.

### 5.2 Tám hành động (actions)
`read` · `create` · `write` (sửa) · `delete` · `approve` (duyệt) · `cancel` (hủy/trả) · `print` (in) · `export` (xuất).
> Ngoài ra hệ thống **suy ra** hành động ảo `process` cho **người thu mua** (không lưu DB) — xem 5.5.

### 5.3 Bốn cấp phạm vi (scope) + 2 cấp đặc biệt
| Cấp | Ý nghĩa | Điều kiện lọc dữ liệu |
|---|---|---|
| `own` | Của mình | `created_by == user.id` (hoặc `self` với employee) |
| `dept` | Phòng của mình | công ty + `department == tên phòng user` |
| `company` | Pháp nhân của mình | `company_id == công ty user` |
| `all` | Tất cả | Không giới hạn |
| `assigned` *(đặc biệt)* | Được giao | phiếu của mình **+** dòng có `assignee == mã NV` |
| `proc` *(đặc biệt)* | Thu mua | như `assigned` **+** mọi phiếu **đã duyệt** để nhặt việc/phân bổ |

### 5.4 Cơ chế thực thi
- **Chặn API:** mỗi endpoint bọc `require(entity, action)` → nếu cờ tương ứng = False ⇒ **HTTP 403**.
- **Lọc dữ liệu:** `apply_scope(query, model, entity, user, profile)` thêm điều kiện WHERE theo scope. Cấu hình cột lọc ở `SCOPE_FIELDS`:
  - `purchase_request / survey_request / purchase_order`: theo `company_id`, `department`, `created_by`.
  - `payable / payment_request`: theo `company_id`, `created_by`.
  - `inventory`: theo `company_id`. `survey`: theo `created_by`. `employee`: theo `company_id`, `department_id`, `self`.
- **Nhiều vai trò:** điều kiện của các grant có quyền `action` được **OR** lại (rộng nhất thắng).
- **Lớp B (user_scope):** thêm include/exclude cụ thể (VD chỉ thấy công ty X, trừ phòng Y).

### 5.5 Người thu mua & ẩn NCC
- `is_purchaser` = user có grant **`survey_request.read`** với scope **`proc`** hoặc **`all`** (người YC = `own`, trưởng phòng = `dept` → KHÔNG phải purchaser).
- Purchaser được inject cờ ảo **`survey_request.process = True`** (để FE mở màn xử lý NSTM).
- **Chỉ purchaser** mới thấy field NCC ở kết quả khảo sát; người khác nhận bản **đã lọc** (whitelist — xem 3.2).

### 5.6 Ma trận quyền mẫu (theo vai trò điển hình)

| Entity | `employee` (NV cơ bản) | `dept_head` | `pur_staff` (NSTM) | `pur_manager` (QL TM) | `pur_admin` (Admin TM) |
|---|:--:|:--:|:--:|:--:|:--:|
| survey_request | R,C,W (own) | R,**A** (dept) | R,W (proc) | **Full 8** (all) | R (proc) |
| purchase_request | R,C (own) | R,**A** (dept) | R,C,W (assigned) | **Full 8** (all) | R (proc) |
| purchase_order | – | – | R,C,W,**print** (assigned) | **Full 8** (all) | R (proc) |
| payable | – | – | R (company) | **Full 8** (all) | R (all) |
| payment_request | – | – | R,C,W,**print** (company) | **Full 8** (all) | R (all) |
| supplier/product/…(danh mục) | – | R (all) | R (all) | **Full 8** (all) | **R,C,W,D** (all) |
| user/role/setting | – | – | – | – | – |
| admin | full | full | – | – | – |

*(R=read, C=create, W=write, D=delete, A=approve, print=in; scope trong ngoặc; Full 8 = read/create/write/delete/approve/cancel/print/export)*

> `pur_manager` và `pur_admin` được seed qua `resync_role_perms()` — phản ánh `STD_ROLES` trong `seed.py` và **luôn ghi đè** trên DB đã tồn tại.

### 5.7 Lưu ý vận hành
- Quyền được **cache ở trình duyệt (localStorage)** sau đăng nhập → **đổi phân quyền phải ĐĂNG NHẬP LẠI** mới có hiệu lực.
- Token JWT mã hóa bằng **Fernet** (`JWT_SECRET` là khóa master — không được đổi khi đã có dữ liệu mã hóa).

---

## 6. Quy tắc toàn vẹn & tác dụng phụ

### 6.1 Không FK cứng — vì sao & rủi ro
Hệ thống liên kết bằng **code/id mềm** (không ràng buộc FK ở DB) để linh hoạt import/đồng bộ dữ liệu (VD sản phẩm từ sheet). Đổi lại, **toàn vẹn do tầng service đảm bảo**, không phải DB. → Không xóa cứng danh mục đang được tham chiếu (VD sản phẩm đã nằm trong PO).

### 6.2 Tác dụng phụ khi NHẬN HÀNG (quan trọng nhất) ⭐
Khi ghi `received_date` cho 1 `po_delivery`, gọi **`po_service.recompute_effects(db, po, user)`** — sinh ĐỒNG BỘ:
1. **`tab_goods_receipt`** — 1 phiếu nhập/lần giao (`delivery_id` UNIQUE ⇒ không nhân đôi).
2. **`tab_inventory_move`** + cập nhật **`tab_inventory`** (`inv_service.apply_delivery` — cộng tồn, tính lại bình quân gia quyền).
3. **`tab_payable`** — 2 luồng (`pay_service.upsert`): `goods` (tiền hàng) + `shipping` (phí VC nếu có).

> ⚠️ **Không** được insert thẳng `po_delivery` bỏ qua hàm này — sẽ **mất** tồn kho & công nợ.

### 6.3 Idempotent
- **Đồng bộ sản phẩm:** import lại cùng file → **update** theo `code`, không tạo trùng; gộp mã trùng trong file.
- **Nhận hàng:** `goods_receipt.delivery_id` UNIQUE ⇒ nhận lại cùng lần giao không sinh phiếu nhập/tồn/nợ trùng.

---

## 7. Nhật ký phiên bản

| Version | Ngày | Nội dung | Người duyệt |
|---|---|---|---|
| v1.0 | 2026-07-08 | Bản LLD đầu tiên (39 bảng + RBAC) | ☐ chờ ký |
| v1.1 | 2026-07-15 | Thêm `tab_push_subscription` (40 bảng); cập nhật RBAC `pur_manager`/`pur_admin` (resync); thêm `tab_setting` ghi chú mã hóa Fernet | ☐ chờ ký |

> Mọi thay đổi cấu trúc bảng/quyền → ghi **Change Request** ở [change-log.md](change-log.md) + cập nhật tài liệu này.

*Hết. Tổng quan xem [technical-design.md](technical-design.md); sơ đồ xem [so-do-ky-thuat.md](so-do-ky-thuat.md).*
