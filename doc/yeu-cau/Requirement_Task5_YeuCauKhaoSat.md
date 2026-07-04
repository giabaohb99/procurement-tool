# Requirement — Task 5: Phiếu Yêu cầu khảo sát (mới) & Pipeline sinh PYC

> **Phiên bản:** 1.0  
> **Ngày:** 2026-07-04  
> **Phạm vi:** Toàn bộ luồng từ khi người yêu cầu tạo Yêu cầu khảo sát đến khi sinh ra Phiếu yêu cầu mua hàng (PYC) ở trạng thái nháp.  
> **Tài liệu nền:** `Plan_CapNhat_Flow_KhaoSat_v2.md`, code thực tế `survey/model.py`, `purchase_request/model.py`, `purchase_request/service.py`.

---

## 1. Mục tiêu & Vì sao ảnh hưởng flow gốc

### 1.1 Bối cảnh

**Flow hiện tại:** Người yêu cầu (người YC) tạo thẳng Phiếu yêu cầu mua hàng (PYC) → trưởng bộ phận duyệt → nhân sự thu mua (NSTM) xử lý đặt hàng. Khảo sát NCC / khảo sát sản phẩm là hai phiếu **rời**, do NSTM tự làm, không liên kết vào luồng của người YC — dẫn đến người YC không biết mua ở đâu, giá bao nhiêu, và NSTM phải làm thủ công.

**Vấn đề cần giải quyết:**
1. Người YC chưa biết NCC, giá cả → tạo PYC với giá ước lệ, thiếu cơ sở.
2. NSTM phải khảo sát nhưng kết quả không phản hồi ngược lại cho người YC.
3. Tên NCC cần được **ẩn hoàn toàn** với người YC (chỉ NSTM biết NCC thật).
4. Khi có kết quả khảo sát, việc tạo PYC lại phải làm thủ công lần nữa.

### 1.2 Mục tiêu Task 5

- Tạo **entity mới "Yêu cầu khảo sát"** (3 bảng: header, line, option) đứng **trước** PYC.
- NSTM xử lý bằng cách liên kết dòng khảo sát sản phẩm **đã duyệt** (bảng `tab_survey_product_line`) vào từng item → tạo "option" ẩn danh NCC.
- Người YC thấy kết quả theo format "Option 1 — ID 789" (không thấy NCC).
- Người YC chọn 1 option/sản phẩm → hệ thống **tự sinh PYC nháp** (gom theo NCC, 1 NCC = 1 phiếu).
- Luồng PYC mới đi tiếp workflow PYC chuẩn hiện có.

**Lưu ý:** Người YC **vẫn có thể tạo PYC thẳng** như cũ — luồng khảo sát là tùy chọn, không thay thế.

### 1.3 Sơ đồ luồng end-to-end (ASCII)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                      LUỒNG MỚI — TASK 5 (Yêu cầu khảo sát)                 ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Người YC
   │
   ├─► [Tạo Yêu cầu khảo sát] ──► status = draft
   │         │ (điền header + các dòng sản phẩm cần khảo sát)
   │         │
   │         ▼ submit
   │   status = submitted (Chờ duyệt)
   │         │
   │         ▼ Trưởng BP duyệt
   │   status = approved
   │         │
   │         │── [HỆ THỐNG tự gán NSTM theo phân loại — tái dùng Task 4]
   │         │
   │         ▼
   │   status = processing (Đang xử lý)
   │         │
   │         │   NSTM (màn xử lý riêng)
   │         │   ├─ Chọn NCC
   │         │   ├─ Xem danh sách dòng khảo sát SP đã duyệt của NCC đó
   │         │   │      (tab_survey_product_line: line_approve = "Duyệt")
   │         │   ├─ Chọn dòng phù hợp → tạo Option (ẩn danh NCC)
   │         │   │      (tab_survey_request_option: public_id = "ID 789")
   │         │   └─ Nếu chưa có / không phù hợp:
   │         │        └─► Kích hoạt quy trình khảo sát sản phẩm mới (Tab 7)
   │         │               → Khi khảo sát đó được duyệt → quay lại chọn option
   │         │
   │         ▼ Admin chốt
   │   status = survey_done (Hoàn thành khảo sát)
   │         │
   │         ▼ Người YC xem kết quả (ẩn NCC)
   │   [Màn kết quả] — hiện các Option (Option 1/ID 789, Option 2/ID 812...)
   │         │ Người YC chọn 1 option / mỗi sản phẩm
   │         │
   │         ▼ Nhấn "Tạo Phiếu yêu cầu mua"
   │   [HỆ THỐNG gom option theo NCC nguồn]
   │         │ Mỗi NCC → 1 PYC nháp riêng
   │         │ Điền giá từ khảo sát, người YC sửa tự do (nháp)
   │         │
   │         ▼
   │   tab_purchase_request (status=draft) ──► Workflow PYC chuẩn
   │         │        (submit → approved trưởng BP → tự gán NSTM Task 4 → xử lý)
   │         ▼
   │   [Liên kết ngược: survey_request_line.pr_id trỏ vào PYC vừa sinh]
   │
   └─► SONG SONG: Người YC tạo PYC thẳng (flow cũ vẫn hoạt động)

╔═══════════════════════════════════════════════════════════════════════════════╗
║              LUỒNG GỐC (vẫn hoạt động song song — không thay đổi)           ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Người YC ──► [Tạo PYC thẳng] ──► draft ──► submitted ──► approved (trưởng BP)
                                              ──► Tự gán NSTM (Task 4) ──► NSTM xử lý
```

---

## 2. Các Actor & Quyền

### 2.1 Danh sách actor

| Actor | Vai trò | Mô tả |
|-------|---------|-------|
| **Người YC** (requester) | Người yêu cầu | Tạo yêu cầu khảo sát, xem kết quả (ẩn NCC), chọn option, tạo PYC |
| **Trưởng bộ phận** (head_of_dept) | Người duyệt | Duyệt hoặc từ chối yêu cầu khảo sát; không thấy NCC |
| **NSTM** (nhân sự thu mua) | Người xử lý | Xử lý khảo sát: chọn NCC → chọn dòng khảo sát đã duyệt → tạo option; thấy đầy đủ NCC |
| **AdminTM** (admin thu mua) | Quản trị | Chốt "Hoàn thành khảo sát" (survey_done); có thể gán tay NSTM; thấy đầy đủ NCC; gán tay option nếu cần |

### 2.2 Ma trận quyền — Entity `survey_request`

| Hành động | Người YC | Trưởng BP | NSTM | AdminTM |
|-----------|----------|-----------|------|---------|
| Tạo yêu cầu khảo sát | Chỉ phiếu mình tạo | — | — | Có |
| Xem danh sách phiếu mình tạo | Có (scope=own) | Có (scope=dept) | Không | Có (scope=all) |
| Sửa phiếu (status=draft) | Chỉ phiếu mình tạo | — | — | Có |
| Gửi duyệt (submit) | Chỉ phiếu mình tạo | — | — | Có |
| Duyệt / Từ chối | Không | Có (scope=dept) | Không | Có |
| Xem màn xử lý NSTM (options có NCC) | **KHÔNG** | **KHÔNG** | Có (dòng được giao) | Có |
| Tạo / sửa option (chọn NCC → dòng KS) | Không | Không | Có (dòng được giao) | Có |
| Chốt survey_done | Không | Không | Không | **Chỉ AdminTM** |
| Xem kết quả ẩn NCC (màn người YC) | Có (scope=own) | Có (scope=dept) | Không (dùng màn khác) | Có |
| Chọn option + tạo PYC | Chỉ phiếu mình tạo | — | — | Có |

> **Quan trọng:** Quyền "survey_request" là **entity mới** — cần khai báo trong bảng permission/grant, tách biệt với quyền "survey" (khảo sát NCC/SP cũ) và "purchase_request".

### 2.3 Quyền cụ thể cần thêm vào hệ thống

| Permission key | Mô tả |
|---------------|-------|
| `survey_request.read` | Xem danh sách và chi tiết (theo scope) |
| `survey_request.create` | Tạo phiếu mới |
| `survey_request.write` | Sửa phiếu (khi draft/rejected) |
| `survey_request.submit` | Gửi duyệt (tích hợp vào write hoặc tách riêng) |
| `survey_request.approve` | Duyệt / từ chối (trưởng BP, AdminTM) |
| `survey_request.process` | Xử lý options — màn NSTM (thấy NCC) |
| `survey_request.complete` | Chốt survey_done (AdminTM) |
| `survey_request.delete` | Xóa phiếu (chỉ khi draft) |

---

## 3. Data Model Mới — 3 Bảng

### 3.1 Bảng header: `tab_survey_request`

> Tương tự header của `tab_purchase_request`. Lưu thông tin chung của toàn phiếu yêu cầu khảo sát.

| Cột | Kiểu SQLAlchemy | Nullable | Default | Ý nghĩa |
|-----|-----------------|----------|---------|---------|
| `id` | BigInteger PK | No | auto | Khóa chính (kế thừa Base) |
| `code` | String(50) UNIQUE | No | `""` | Mã phiếu, auto sinh: `YCKSNDDMMYY01` (ví dụ `YCKS04072601`). Quy tắc: prefix `YCKS` + ngày tạo DDMMYY + seq 2 số |
| `company_id` | BigInteger FK→company | No | `0` | Pháp nhân nhận hóa đơn (giống PYC) |
| `requester` | String(255) | No | `""` | Tên người yêu cầu (tự điền hoặc lấy từ user) |
| `requester_position` | String(100) | No | `""` | Chức vụ người yêu cầu |
| `department` | String(255) | No | `""` | Phòng ban / thương hiệu yêu cầu |
| `head_of_dept` | String(255) | No | `""` | Trưởng bộ phận (tự điền theo phòng ban, tương tự PYC) |
| `purpose` | String(255) | No | `""` | Mục đích khảo sát / mua hàng |
| `request_date` | String(10) | No | `""` | Ngày tạo phiếu (YYYY-MM-DD) |
| `status` | String(30) | No | `"draft"` | Trạng thái phiếu: `draft` / `submitted` / `approved` / `rejected` / `processing` / `survey_done` |
| `assignee_id` | BigInteger FK→employee | No | `0` | NSTM chính phụ trách toàn phiếu (tự gán khi approve, AdminTM gán lại được) |
| `note` | Text | Yes | `""` | Ghi chú chung |
| `reject_reason` | Text | Yes | `""` | Lý do từ chối (khi status=rejected) |
| `survey_request_id_origin` | BigInteger | Yes | `null` | Liên kết ngược: nếu phiếu này sinh ra từ 1 phiếu khảo sát khác (dự phòng mở rộng sau) |
| `created_by` | BigInteger | No | — | User ID tạo phiếu (AuditMixin) |
| `updated_by` | BigInteger | No | — | User ID cập nhật cuối (AuditMixin) |
| `created_at` | DateTime | No | now() | Thời gian tạo (AuditMixin) |
| `updated_at` | DateTime | No | now() | Thời gian cập nhật (AuditMixin) |

**Chỉ số DB:** `idx_survey_request_status`, `idx_survey_request_department`, `idx_survey_request_created_by`.

---

### 3.2 Bảng dòng: `tab_survey_request_line`

> Mỗi dòng = 1 sản phẩm/nhóm hàng cần khảo sát. Người YC nhập khi tạo phiếu.

| Cột | Kiểu SQLAlchemy | Nullable | Default | Ý nghĩa |
|-----|-----------------|----------|---------|---------|
| `id` | BigInteger PK | No | auto | Khóa chính |
| `survey_request_id` | BigInteger FK→tab_survey_request | No | — | Header phiếu |
| `internal_line_code` | String(50) | No | `""` | Mã yêu cầu dòng, **auto sinh** (ví dụ `YCKSL000001`), **không hiển thị với người YC** — dùng nội bộ để liên kết option |
| `received_date` | String(10) | No | `""` | Ngày tiếp nhận yêu cầu (YYYY-MM-DD), do NSTM/admin điền khi nhận |
| `result_due_date` | String(10) | No | `""` | Ngày yêu cầu trả kết quả (YYYY-MM-DD), người YC hoặc NSTM điền |
| `department_requester` | String(255) | No | `""` | BP / Người YC (select phòng ban hoặc nhập tên) |
| `item_group` | String(100) | No | `""` | Phân loại hàng hóa (select từ danh mục item_group, giống `PurchaseRequestItem.item_group`) |
| `requirement_detail` | Text | Yes | `""` | Chi tiết thông số kỹ thuật & chất lượng (text dài) |
| `other_requirement` | Text | Yes | `""` | Yêu cầu khác (text) |
| `request_qty` | Numeric(18,3) | No | `0` | Số lượng dự kiến mua (optional, 0 = chưa xác định) |
| `uom` | String(25) | No | `""` | Đơn vị tính (select từ danh mục ĐVT) |
| `proposed_price` | Numeric(18,2) | No | `0` | Giá đề xuất VNĐ (người YC ước tính) |
| `image_file` | String(500) | Yes | `""` | URL file hình đính kèm (lưu qua attachment service) |
| `image_attachment_id` | BigInteger | Yes | `null` | FK → tab_attachment.id (nếu dùng attachment service có sẵn) |
| `assignee` | String(100) | No | `""` | Mã nhân sự NSTM phụ trách dòng này (tự gán theo item_group khi approve, AdminTM gán tay được) |
| `pr_id` | BigInteger | Yes | `null` | FK → tab_purchase_request.id — điền khi dòng này đã được chuyển thành PYC |
| `pr_code` | String(50) | No | `""` | Mã PYC tương ứng (để hiển thị nhanh, không cần JOIN) |
| `is_completed` | Boolean | No | `false` | True khi đã chọn option và tạo PYC xong |
| `created_by` | BigInteger | No | — | AuditMixin |
| `updated_by` | BigInteger | No | — | AuditMixin |
| `created_at` | DateTime | No | — | AuditMixin |
| `updated_at` | DateTime | No | — | AuditMixin |

**Chỉ số DB:** `idx_srl_survey_request_id`, `idx_srl_item_group`, `idx_srl_assignee`.

---

### 3.3 Bảng option: `tab_survey_request_option`

> Mỗi option = 1 kết quả khảo sát sản phẩm đã duyệt được NSTM "gắn" vào 1 dòng yêu cầu. Đây là bảng trung tâm cho cơ chế ẩn NCC.

| Cột | Kiểu SQLAlchemy | Nullable | Default | Ý nghĩa |
|-----|-----------------|----------|---------|---------|
| `id` | BigInteger PK | No | auto | Khóa chính |
| `survey_request_line_id` | BigInteger FK→tab_survey_request_line | No | — | Dòng yêu cầu mà option này thuộc về |
| `product_survey_line_id` | BigInteger FK→tab_survey_product_line | No | — | **Nguồn dữ liệu:** ID dòng khảo sát sản phẩm (`tab_survey_product_line`) đã duyệt (`line_approve="Duyệt"`) |
| `public_id` | Integer | No | auto | **ID ẩn danh** hiển thị với người YC: số nguyên tự tăng trong phạm vi 1 survey_request_line (Option 1, Option 2…). **Không bao giờ** lộ supplier_code/supplier_name qua field này |
| `display_label` | String(50) | No | `""` | Label hiển thị: ví dụ `"Option 1 — ID 789"` (sinh tự động: `Option {public_id} — ID {id}`) |
| `is_chosen` | Boolean | No | `false` | True khi người YC chọn option này để tạo PYC |
| `chosen_at` | DateTime | Yes | `null` | Thời điểm người YC chọn |
| `chosen_by` | BigInteger | Yes | `null` | User ID người YC đã chọn |
| — **SNAPSHOT thông số (copy từ nguồn tại thời điểm gắn)** — | | | | |
| `snap_product_name` | String(255) | No | `""` | Tên sản phẩm (từ `SurveyProductLine.product_name`) |
| `snap_spec` | Text | Yes | `""` | Thông số kỹ thuật (từ `SurveyProductLine.spec`) |
| `snap_origin` | String(100) | No | `""` | Xuất xứ (từ `SurveyProductLine.origin`) |
| `snap_quote_unit` | String(25) | No | `""` | ĐVT báo giá (từ `SurveyProductLine.quote_unit`) |
| `snap_moq` | Numeric(18,3) | No | `0` | Số lượng đặt hàng tối thiểu MOQ (từ `SurveyProductLine.moq`) |
| `snap_price_by_volume` | Numeric(18,2) | No | `0` | Đơn giá (từ `SurveyProductLine.price_by_volume`) |
| `snap_volume_range` | String(100) | No | `""` | Khoảng số lượng áp giá (từ `SurveyProductLine.volume_range`) |
| `snap_vat` | Numeric(5,2) | No | `0` | VAT % (từ `SurveyProductLine.vat`) |
| `snap_delivery_time` | String(100) | No | `""` | Thời gian giao hàng (từ `SurveyProductLine.delivery_time`) |
| `snap_delivery_place` | String(255) | No | `""` | Địa điểm giao hàng (từ `SurveyProductLine.delivery_place`) |
| `snap_shipping_cost` | Numeric(18,2) | No | `0` | Phí vận chuyển (từ `SurveyProductLine.shipping_cost`) |
| `snap_sample_ready` | Boolean | No | `false` | Có mẫu sẵn (từ `SurveyProductLine.sample_ready`) |
| `snap_lab_result` | String(20) | No | `""` | Kết quả kiểm định lab (từ `SurveyProductLine.lab_result`) |
| `snap_internal_code` | String(50) | No | `""` | Mã SP theo NCC — **CHỈ NSTM thấy, KHÔNG trả về API người YC** |
| — **Trường nội bộ NSTM — KHÔNG trả về API người YC** — | | | | |
| `supplier_code` | String(50) | No | `""` | Mã NCC thật — **backend lọc, không trả cho người YC** |
| `supplier_name` | String(255) | No | `""` | Tên NCC thật — **backend lọc, không trả cho người YC** |
| `supplier_survey_id` | BigInteger | No | `0` | ID phiếu khảo sát nguồn (`tab_survey.id`) — **backend lọc** |
| `nstm_note` | Text | Yes | `""` | Ghi chú nội bộ NSTM (từ `SurveyProductLine.nspt_reason`) — **không trả cho người YC** |
| — | | | | |
| `created_by` | BigInteger | No | — | AuditMixin |
| `updated_by` | BigInteger | No | — | AuditMixin |
| `created_at` | DateTime | No | — | AuditMixin |
| `updated_at` | DateTime | No | — | AuditMixin |

**Chỉ số DB:** `idx_sro_line_id`, `idx_sro_product_survey_line_id`, `idx_sro_is_chosen`.

**Tại sao snapshot?** Dữ liệu khảo sát sản phẩm có thể bị sửa sau khi đã gắn option → snapshot bảo toàn dữ liệu tại thời điểm gắn. Người YC thấy đúng thông tin đã được NSTM chọn.

---

## 4. Trạng thái & Sơ đồ chuyển trạng thái (State Machine)

### 4.1 Bảng trạng thái

| Mã trạng thái | Tên hiển thị | Màu badge | Mô tả |
|---------------|-------------|-----------|-------|
| `draft` | Nháp | Xám | Vừa tạo, chưa gửi duyệt; người YC có thể sửa/xóa |
| `submitted` | Chờ duyệt | Vàng | Đã gửi duyệt, chờ trưởng BP; không sửa được |
| `approved` | Đã duyệt | Xanh lá nhạt | Trưởng BP đã duyệt; hệ thống tự gán NSTM; chuyển ngay sang `processing` |
| `rejected` | Từ chối | Đỏ | Trưởng BP từ chối, có lý do; người YC sửa lại rồi submit lại |
| `processing` | Đang xử lý | Xanh dương | NSTM đang gắn options; người YC thấy trạng thái này |
| `survey_done` | Hoàn thành khảo sát | Xanh lá đậm | AdminTM chốt; người YC có thể chọn option và tạo PYC |

### 4.2 Sơ đồ state machine (ASCII)

```
                    ┌───────────────────────────────────────────────────┐
                    │                                                   │
          [TẠO MỚI] │                                                   │ [Sửa & gửi lại]
                    ▼                                                   │
              ┌─────────┐   submit()   ┌───────────┐                   │
              │  draft  │─────────────►│ submitted │                   │
              └─────────┘              └───────────┘                   │
                  ▲                          │                          │
                  │ reject()                 │ approve()                │
                  │         ┌────────────────┤                          │
                  │         │                ▼                          │
              ┌──────────┐  │        ┌──────────┐  [tự gán NSTM]      │
              │ rejected │◄─┘        │ approved │─────────────────►   │
              └──────────┘           └──────────┘                      │
                    │                     │                             │
                    └─────────────────────┘                             │
                                          │ (auto)                      │
                                          ▼                             │
                                   ┌────────────┐                      │
                                   │ processing │                      │
                                   └────────────┘                      │
                                          │                             │
                                          │ complete() [AdminTM]        │
                                          ▼                             │
                                  ┌─────────────┐                      │
                                  │ survey_done │──► Người YC chọn    │
                                  └─────────────┘    option + tạo PYC │
                                                                        │
              Lưu ý: reject() từ submitted → rejected ──────────────────┘
```

### 4.3 Quy tắc chuyển trạng thái

| Từ | Sang | Actor | Điều kiện | Side effects |
|----|------|-------|-----------|-------------|
| `draft` | `submitted` | Người tạo phiếu | Phải có ít nhất 1 dòng | Gửi notification tới trưởng BP |
| `submitted` | `approved` | Trưởng BP / AdminTM | — | Tự gán NSTM theo item_group (Task 4); chuyển sang `processing`; notification tới người YC + NSTM |
| `submitted` | `rejected` | Trưởng BP / AdminTM | Phải có `reject_reason` | Notification tới người YC kèm lý do |
| `rejected` | `submitted` | Người tạo phiếu | — | Notification tới trưởng BP |
| `approved` | `processing` | System (auto) | Ngay sau approve | Không có notification riêng (người YC thấy trạng thái thay đổi) |
| `processing` | `survey_done` | AdminTM | Mỗi dòng phải có ít nhất 1 option | Notification tới người YC: "Kết quả khảo sát đã sẵn sàng" |

> **Không có chuyển ngược** từ `processing`/`survey_done` về `approved` hoặc `submitted` — nếu cần điều chỉnh, AdminTM thêm/sửa option, không rollback trạng thái.

---

## 5. Màn hình chi tiết

### 5.1 Màn người YC — Tạo & xem Yêu cầu khảo sát

#### 5.1.a Màn danh sách (`/survey-requests`)

```
┌────────────────────────────────────────────────────────────────┐
│  YÊU CẦU KHẢO SÁT                          [+ Tạo mới]       │
├────────────────────────────────────────────────────────────────┤
│ Filter: [Trạng thái ▼] [Phòng ban ▼] [Từ ngày] [Đến ngày]   │
├──────┬──────────┬──────────────┬────────────┬─────────────────┤
│ Mã   │ Ngày tạo │ Mục đích     │ Số sản phẩm│ Trạng thái      │
├──────┼──────────┼──────────────┼────────────┼─────────────────┤
│ YCKS │ 04/07/26 │ Mua vật liệu │ 3 sản phẩm │ [Đang xử lý]   │
│ YCKS │ 01/07/26 │ ...          │ 1 sản phẩm │ [Hoàn thành]   │
└──────┴──────────┴──────────────┴────────────┴─────────────────┘
```

**Scope:** Người YC chỉ thấy phiếu do mình tạo (`created_by = user.id`). Trưởng BP thấy toàn phòng. AdminTM thấy tất cả.

#### 5.1.b Màn tạo / sửa phiếu (status=draft hoặc rejected)

**Phần HEADER (giống form PYC):**

| Trường | Loại input | Ghi chú |
|--------|-----------|---------|
| Công ty nhận hóa đơn | Select (từ `tab_company`) | Bắt buộc |
| Phòng ban / Thương hiệu | Select (từ `tab_department`) | Bắt buộc; khi chọn → tự điền Trưởng BP |
| Trưởng bộ phận | Text (readonly, tự điền theo phòng ban) | Gọi `/meta/dept-head` như PYC |
| Người yêu cầu | Text | Bắt buộc |
| Chức vụ | Text | |
| Mục đích khảo sát | Text | Bắt buộc |
| Ngày tạo | Date | Mặc định hôm nay |
| Ghi chú | Textarea | |

**Phần BẢNG DÒNG (thêm nhiều dòng):**

| Cột | Loại input | Bắt buộc | Ghi chú |
|-----|-----------|----------|---------|
| Ngày tiếp nhận | Date | Không | NSTM điền sau; người YC để trống |
| Ngày YC trả KQ | Date | Không | Người YC mong muốn nhận kết quả |
| BP/Người YC | Select phòng ban hoặc Text | Không | Mặc định lấy từ header |
| Phân loại | Select item_group | Có | Dùng để tự gán NSTM |
| Chi tiết thông số kỹ thuật & chất lượng | Textarea | Có | Mô tả sản phẩm cần khảo sát |
| Yêu cầu khác | Textarea | Không | Điều kiện đặc biệt |
| Số lượng dự kiến mua | Number | Không | 0 = chưa xác định |
| ĐVT | Select (đơn vị tính) | Không | |
| Giá đề xuất VNĐ | Number | Không | Giá tham chiếu người YC ước |
| File hình | Attachment (upload ảnh) | Không | Dùng attachment service |

**Nút hành động:**
- `[Lưu nháp]` — PATCH `/api/survey-requests/{id}` hoặc POST `/api/survey-requests`
- `[Gửi duyệt]` — POST `/api/survey-requests/{id}/submit`
- `[Xóa]` (chỉ khi draft) — DELETE

#### 5.1.c Màn xem chi tiết (status=submitted/approved/processing/survey_done)

**Tabs:**
1. **Tab "Thông tin"** — Header + bảng dòng (readonly); hiển thị trạng thái từng dòng.
2. **Tab "Kết quả khảo sát"** (chỉ hiện khi status=`survey_done`) — Xem option + nút chọn + nút tạo PYC.

**Banner trạng thái:**
- `draft` → "Phiếu đang ở nháp — nhấn Gửi duyệt để chuyển"
- `submitted` → "Chờ trưởng bộ phận duyệt"
- `processing` → "Đang được khảo sát — kết quả sẽ có sau ngày [result_due_date]"
- `survey_done` → "Khảo sát hoàn thành — xem kết quả và chọn phương án"

---

### 5.2 Màn xử lý riêng của NSTM

**URL:** `/survey-requests/{id}/process` — chỉ hiển thị với role có quyền `survey_request.process`.

#### 5.2.a Layout màn xử lý

```
┌────────────────────────────────────────────────────────────────────────┐
│  XỬ LÝ YÊU CẦU KHẢO SÁT — YCKS04072601                              │
│  Ngày tạo: 04/07/2026 | Phòng ban: Sản xuất | Trạng thái: Đang xử lý │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  SẢN PHẨM 1: Vật liệu nhựa PP                                        │
│  Phân loại: NVL | Thông số: ... | SL dự kiến: 500 kg | Giá đề xuất:  │
│                                                                        │
│  ┌──────────────────────────────────────────────────────┐             │
│  │ CHỌN NCC: [_____________________▼] (dropdown search) │             │
│  └──────────────────────────────────────────────────────┘             │
│                                                                        │
│  Dòng khảo sát sản phẩm đã duyệt của NCC này:                        │
│  ┌──────┬────────────┬──────────┬───────┬───────┬──────────────────┐ │
│  │ Chọn │ Tên SP     │ Spec     │ Giá   │ MOQ   │ Ngày KQ          │ │
│  ├──────┼────────────┼──────────┼───────┼───────┼──────────────────┤ │
│  │ [ ]  │ PP A1 grade│ ASTM...  │15,000 │ 200kg │ 01/06/2026       │ │
│  │ [ ]  │ PP B2 grade│ ISO...   │13,500 │ 100kg │ 15/06/2026       │ │
│  └──────┴────────────┴──────────┴───────┴───────┴──────────────────┘ │
│  [+ Chọn dòng này làm Option]                                         │
│                                                                        │
│  Nếu không có dòng phù hợp:                                           │
│  [Kích hoạt khảo sát sản phẩm mới với NCC này →]                     │
│                                                                        │
│  OPTIONS ĐÃ GẮN:                                                      │
│  ┌────────────┬────────────┬──────────┬───────┬───────┬───────────┐  │
│  │ Option 1   │ PP A1 grade│ ASTM...  │15,000 │200kg  │ [Xóa]     │  │
│  │ ID 789     │            │          │       │       │           │  │
│  │ NCC: Cty X │            │          │       │       │ [Chỉ NSTM]│  │
│  └────────────┴────────────┴──────────┴───────┴───────┴───────────┘  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

#### 5.2.b Luồng tương tác NSTM

**Bước 1 — Chọn NCC:**
- Dropdown search NCC (gọi API danh sách NCC đang hoạt động).
- Khi chọn xong → gọi `GET /api/survey-requests/{id}/lines/{line_id}/available-survey-lines?supplier_code=X`.
- API trả về danh sách `tab_survey_product_line` thỏa: `supplier_code = X` AND `line_approve = "Duyệt"`.

**Bước 2 — Chọn dòng khảo sát:**
- NSTM tích chọn 1 hoặc nhiều dòng → nhấn `[Thêm làm Option]`.
- Gọi `POST /api/survey-requests/{id}/lines/{line_id}/options` với body: `{product_survey_line_id: int}`.
- Backend:
  - Lấy dòng `SurveyProductLine` theo ID → kiểm tra `line_approve == "Duyệt"`.
  - Tính `public_id = (số option hiện có của line + 1)`.
  - Snapshot các field cần thiết.
  - Tạo bản ghi `SurveyRequestOption`.

**Bước 3 — Nếu chưa có dòng phù hợp:**
- Nút `[Kích hoạt khảo sát sản phẩm mới →]` → chuyển hướng đến màn tạo phiếu khảo sát SP (Task 7), truyền sẵn thông tin: NCC đã chọn, thông số từ dòng yêu cầu.
- Khi phiếu khảo sát mới được **duyệt** → NSTM quay lại màn xử lý và thấy dòng mới trong danh sách.

**Bước 4 — Quản lý option đã gắn:**
- Xem danh sách option đã gắn cho từng dòng yêu cầu (NSTM thấy cả tên NCC).
- `[Xóa option]` — DELETE `/api/survey-requests/{id}/lines/{line_id}/options/{option_id}`.

**Bước 5 — Chốt hoàn thành (AdminTM):**
- Khi mỗi dòng có ít nhất 1 option → nút `[Chốt hoàn thành khảo sát]` hiện.
- Gọi `POST /api/survey-requests/{id}/complete`.
- Backend kiểm tra điều kiện → set `status = "survey_done"` → gửi notification tới người YC.

---

### 5.3 Màn người YC xem kết quả & chọn option

**URL:** `/survey-requests/{id}` Tab "Kết quả khảo sát" (chỉ hiện khi `survey_done`)

#### 5.3.a Layout màn kết quả

```
┌────────────────────────────────────────────────────────────────────────┐
│  KẾT QUẢ KHẢO SÁT — YCKS04072601                                     │
│  Trạng thái: HOÀN THÀNH KHẢO SÁT                                      │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  SẢN PHẨM 1: Vật liệu nhựa PP                                        │
│  Phân loại: NVL | SL dự kiến: 500 kg | Giá đề xuất của bạn: 15,000₫  │
│                                                                        │
│  Chọn phương án:                                                       │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ ◉ Option 1 — ID 789                                            │   │
│  │   Tên SP: PP A1 grade | Spec: ASTM D... | Xuất xứ: Hàn Quốc  │   │
│  │   Giá: 15,000₫/kg | MOQ: 200 kg | ĐVT: kg                     │   │
│  │   VAT: 10% | Thời gian giao: 7-10 ngày | Phí ship: 500,000₫   │   │
│  │   Có mẫu: Có | Lab: Đạt                                        │   │
│  ├────────────────────────────────────────────────────────────────┤   │
│  │ ○ Option 2 — ID 812                                            │   │
│  │   Tên SP: PP B2 grade | Spec: ISO ... | Xuất xứ: Việt Nam     │   │
│  │   Giá: 13,500₫/kg | MOQ: 100 kg | ĐVT: kg                     │   │
│  │   VAT: 10% | Thời gian giao: 3-5 ngày | Phí ship: 0₫          │   │
│  │   Có mẫu: Không | Lab: Chưa kiểm                               │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  SẢN PHẨM 2: Hộp carton 5 lớp                                        │
│  [tương tự...]                                                         │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│  [Tạo Phiếu yêu cầu mua hàng từ các option đã chọn]                  │
│  (nút này chỉ enable khi mỗi sản phẩm đã chọn đủ 1 option)           │
└────────────────────────────────────────────────────────────────────────┘
```

**Trường được hiển thị với người YC** (lấy từ `snap_*`, không lộ NCC):

| Trường hiển thị | Nguồn snapshot | Ẩn hay hiện |
|-----------------|----------------|-------------|
| Tên sản phẩm | `snap_product_name` | Hiện |
| Thông số kỹ thuật | `snap_spec` | Hiện |
| Xuất xứ | `snap_origin` | Hiện |
| ĐVT báo giá | `snap_quote_unit` | Hiện |
| Đơn giá | `snap_price_by_volume` | Hiện |
| Khoảng SL áp giá | `snap_volume_range` | Hiện |
| MOQ | `snap_moq` | Hiện |
| VAT % | `snap_vat` | Hiện |
| Thời gian giao | `snap_delivery_time` | Hiện |
| Địa điểm giao | `snap_delivery_place` | Hiện |
| Phí vận chuyển | `snap_shipping_cost` | Hiện |
| Có mẫu | `snap_sample_ready` | Hiện |
| Kết quả lab | `snap_lab_result` | Hiện |
| **Mã NCC** | `supplier_code` | **ẨN HOÀN TOÀN** |
| **Tên NCC** | `supplier_name` | **ẨN HOÀN TOÀN** |
| **Mã SP theo NCC** | `snap_internal_code` | **ẨN HOÀN TOÀN** |
| **Ghi chú NSTM** | `nstm_note` | **ẨN HOÀN TOÀN** |
| **ID phiếu khảo sát nguồn** | `supplier_survey_id` | **ẨN HOÀN TOÀN** |

#### 5.3.b Hành động chọn option

1. Người YC nhấn radio chọn 1 option cho mỗi sản phẩm.
2. Gọi `PATCH /api/survey-requests/{id}/lines/{line_id}/options/{option_id}/choose`.
3. Backend: set `is_chosen=true` cho option đó, `is_chosen=false` cho tất cả option khác của cùng dòng.
4. Khi **tất cả dòng đều có `is_chosen=true`** → enable nút "Tạo PYC".

---

## 6. Cơ chế ẩn NCC — Chi tiết kỹ thuật

### 6.1 Nguyên tắc thiết kế

Ẩn NCC phải được thực thi **tại backend** — không chỉ ẩn trường ở UI. Nếu chỉ ẩn ở frontend, người dùng có thể mở DevTools → Network → xem response JSON và thấy `supplier_name`. Phải ngăn ở tầng API.

### 6.2 Hai endpoint riêng biệt

| Endpoint | Dùng cho | Trả về trường NCC |
|----------|----------|------------------|
| `GET /api/survey-requests/{id}/result` | Người YC / Trưởng BP xem kết quả | **KHÔNG** — lọc bỏ hoàn toàn |
| `GET /api/survey-requests/{id}/process` | NSTM / AdminTM xử lý | **CÓ** — đầy đủ |

### 6.3 Schema Pydantic — hai serializer riêng

```python
# Schema cho người YC (public view)
class OptionPublicOut(BaseModel):
    id: int
    public_id: int
    display_label: str         # "Option 1 — ID 789"
    is_chosen: bool
    snap_product_name: str
    snap_spec: str
    snap_origin: str
    snap_quote_unit: str
    snap_moq: float
    snap_price_by_volume: float
    snap_volume_range: str
    snap_vat: float
    snap_delivery_time: str
    snap_delivery_place: str
    snap_shipping_cost: float
    snap_sample_ready: bool
    snap_lab_result: str
    # KHÔNG có: supplier_code, supplier_name, snap_internal_code,
    #           nstm_note, supplier_survey_id, product_survey_line_id

# Schema cho NSTM / Admin (internal view)
class OptionInternalOut(OptionPublicOut):
    supplier_code: str
    supplier_name: str
    snap_internal_code: str
    nstm_note: str
    supplier_survey_id: int
    product_survey_line_id: int
```

### 6.4 Logic phân quyền trong controller

```python
@router.get("/{rid}/result")
def get_result(rid: int, db: Session = Depends(get_db),
               user=Depends(require("survey_request", "read"))):
    # Kiểm tra scope: người YC chỉ xem phiếu mình tạo
    sr = _get_scoped(db, rid, user)
    if sr.status != "survey_done":
        raise HTTPException(400, "Kết quả chưa sẵn sàng")
    # Serialize KHÔNG kèm NCC — dùng OptionPublicOut
    return success(_out_public(db, sr))

@router.get("/{rid}/process")
def get_process_view(rid: int, db: Session = Depends(get_db),
                     user=Depends(require("survey_request", "process"))):
    # Chỉ NSTM / Admin có quyền "process"
    sr = db.get(SurveyRequest, rid)
    # Serialize ĐẦY ĐỦ — dùng OptionInternalOut
    return success(_out_internal(db, sr))
```

### 6.5 Kiểm tra thêm — bảo vệ tầng dữ liệu

- **Không được** dùng chung 1 endpoint với tham số `?include_ncc=true/false` → dễ bị bypass.
- Phải là **2 URL khác nhau**, 2 quyền khác nhau, 2 serializer khác nhau.
- Khi chạy test bảo mật: đăng nhập bằng tài khoản người YC → gọi endpoint `/process` → phải nhận `403 Forbidden`.
- Đăng nhập người YC → gọi endpoint `/result` → response JSON **không được chứa** bất kỳ key nào trong `{supplier_code, supplier_name, snap_internal_code, nstm_note, supplier_survey_id}`.

---

## 7. Quy tắc sinh PYC từ Option

### 7.1 Trigger

Khi người YC nhấn `[Tạo Phiếu yêu cầu mua hàng]` → gọi `POST /api/survey-requests/{id}/create-prs`.

### 7.2 Thuật toán gom theo NCC — sinh N phiếu PYC

```
Input: survey_request_id

1. Lấy tất cả dòng (tab_survey_request_line) của phiếu
2. Với mỗi dòng, lấy option có is_chosen = true
   → Nếu dòng không có option nào is_chosen → raise lỗi 400
3. Gom các option theo supplier_code (lấy từ option.supplier_code):
   groups = { supplier_code: [option1, option2, ...] }
4. Với mỗi supplier_code trong groups:
   a. Tạo PurchaseRequest (header):
      - code: auto sinh format PYCDDMMYYxx
      - company_id: từ survey_request.company_id
      - requester: từ survey_request.requester
      - requester_position: từ survey_request.requester_position
      - department: từ survey_request.department
      - head_of_dept: từ survey_request.head_of_dept
      - purpose: từ survey_request.purpose
      - request_date: today
      - status: "draft"
      - note: f"Sinh tự động từ YCKS {survey_request.code}"
      - suggested_supplier: option.supplier_name  ← điền sẵn NCC
      - created_by: user.id
   b. Với mỗi option trong group:
      Tạo PurchaseRequestItem:
      - product_name: option.snap_product_name
      - item_group: survey_request_line.item_group
      - qty: survey_request_line.request_qty (hoặc 0 nếu chưa điền)
      - unit: option.snap_quote_unit
      - price: option.snap_price_by_volume   ← giá từ khảo sát
      - amount: qty * price
      - note: f"Từ {option.display_label}"
      - assignee: ""  ← chưa gán (sẽ tự gán khi PYC được duyệt)
      - line_status: "Chưa đặt hàng"
   c. Cập nhật survey_request_line:
      - pr_id = pr.id
      - pr_code = pr.code
      - is_completed = true
5. Trả về danh sách PYC vừa tạo (code + id)
```

### 7.3 Map field khảo sát → field PYC

| Nguồn (option/line) | Đích (PYC header/item) | Ghi chú |
|--------------------|----------------------|---------|
| `survey_request.company_id` | `PurchaseRequest.company_id` | Copy |
| `survey_request.requester` | `PurchaseRequest.requester` | Copy |
| `survey_request.department` | `PurchaseRequest.department` | Copy |
| `survey_request.head_of_dept` | `PurchaseRequest.head_of_dept` | Copy |
| `survey_request.purpose` | `PurchaseRequest.purpose` | Copy |
| `option.supplier_name` | `PurchaseRequest.suggested_supplier` | Điền sẵn |
| `option.snap_product_name` | `PurchaseRequestItem.product_name` | |
| `survey_request_line.item_group` | `PurchaseRequestItem.item_group` | |
| `survey_request_line.request_qty` | `PurchaseRequestItem.qty` | Người YC sửa được |
| `option.snap_quote_unit` | `PurchaseRequestItem.unit` | |
| `option.snap_price_by_volume` | `PurchaseRequestItem.price` | Người YC sửa được |
| `qty * price` | `PurchaseRequestItem.amount` | Tính lại |

### 7.4 Trạng thái PYC sinh ra

- Luôn là `"draft"` — người YC **được quyền sửa tự do** (thêm/bớt dòng, sửa số lượng, sửa giá) trước khi gửi duyệt.
- Sau khi sửa xong → gửi duyệt → workflow PYC chuẩn (Task 4 tự gán NSTM khi duyệt).
- `suggested_supplier` trên PYC là **thông tin tham khảo**, không khóa cứng — NSTM có thể mua từ NCC khác nếu xét thấy phù hợp.

### 7.5 Liên kết ngược

```
tab_survey_request
    └── tab_survey_request_line (1..*) ── pr_id, pr_code (sau khi tạo PYC)
            └── tab_survey_request_option (1..*) ── is_chosen
                    └── tab_survey_product_line (FK nguồn)

tab_purchase_request (PYC sinh ra)
    └── note chứa "Sinh tự động từ YCKS XXXXXXXX"
    └── tab_purchase_request_item
            └── note chứa "Từ Option N — ID XXX"
```

---

## 8. API Endpoints

### 8.1 CRUD Phiếu yêu cầu khảo sát

| Method | URL | Quyền | Mô tả |
|--------|-----|-------|-------|
| GET | `/api/survey-requests` | `survey_request.read` | Danh sách (có filter + pagination) |
| GET | `/api/survey-requests/{id}` | `survey_request.read` | Chi tiết header + dòng (không có NCC option) |
| POST | `/api/survey-requests` | `survey_request.create` | Tạo phiếu mới (status=draft) |
| PATCH | `/api/survey-requests/{id}` | `survey_request.write` | Sửa phiếu (chỉ khi draft/rejected) |
| DELETE | `/api/survey-requests/{id}` | `survey_request.delete` | Xóa (chỉ khi draft) |

**Request body tạo phiếu:**
```json
{
  "company_id": 1,
  "requester": "Nguyễn Văn A",
  "department": "Sản xuất",
  "purpose": "Mua NVL Q3",
  "lines": [
    {
      "item_group": "NVL",
      "requirement_detail": "PP grade A, ASTM D...",
      "request_qty": 500,
      "uom": "kg",
      "proposed_price": 15000,
      "result_due_date": "2026-07-15"
    }
  ]
}
```

### 8.2 Workflow (submit / approve / reject / complete)

| Method | URL | Quyền | Mô tả |
|--------|-----|-------|-------|
| POST | `/api/survey-requests/{id}/submit` | `survey_request.write` | Gửi duyệt (draft/rejected → submitted) |
| POST | `/api/survey-requests/{id}/approve` | `survey_request.approve` | Duyệt (submitted → approved → processing) + tự gán NSTM |
| POST | `/api/survey-requests/{id}/reject` | `survey_request.approve` | Từ chối (submitted → rejected), body: `{reason: str}` |
| POST | `/api/survey-requests/{id}/complete` | `survey_request.complete` | Chốt hoàn thành (processing → survey_done) |

### 8.3 Màn NSTM — chọn NCC & option

| Method | URL | Quyền | Mô tả |
|--------|-----|-------|-------|
| GET | `/api/survey-requests/{id}/process` | `survey_request.process` | Màn xử lý NSTM — trả về đầy đủ NCC |
| GET | `/api/survey-requests/{id}/lines/{lid}/available-survey-lines` | `survey_request.process` | Danh sách `tab_survey_product_line` đã duyệt theo supplier_code |
| POST | `/api/survey-requests/{id}/lines/{lid}/options` | `survey_request.process` | Tạo option từ dòng khảo sát SP; body: `{product_survey_line_id: int}` |
| DELETE | `/api/survey-requests/{id}/lines/{lid}/options/{oid}` | `survey_request.process` | Xóa option |
| PATCH | `/api/survey-requests/{id}/lines/{lid}/options/{oid}` | `survey_request.process` | Sửa note nội bộ option |

**Query params cho available-survey-lines:**
- `supplier_code` (bắt buộc): mã NCC
- `item_group` (tùy chọn): lọc thêm theo phân loại

**Logic available-survey-lines:**
```sql
SELECT spl.*
FROM tab_survey_product_line spl
JOIN tab_survey s ON s.id = spl.survey_id
WHERE spl.supplier_code = :supplier_code
  AND spl.line_approve = 'Duyệt'
  AND s.status = 'approved'
ORDER BY spl.id DESC
```

### 8.4 Kết quả cho người YC (đã lọc NCC)

| Method | URL | Quyền | Mô tả |
|--------|-----|-------|-------|
| GET | `/api/survey-requests/{id}/result` | `survey_request.read` | Kết quả khảo sát — **serializer ẩn NCC** |
| PATCH | `/api/survey-requests/{id}/lines/{lid}/options/{oid}/choose` | `survey_request.write` | Chọn option (set is_chosen) |

**Response mẫu `/result` — không có trường NCC:**
```json
{
  "id": 123,
  "code": "YCKS04072601",
  "status": "survey_done",
  "lines": [
    {
      "id": 456,
      "item_group": "NVL",
      "requirement_detail": "PP grade A...",
      "request_qty": 500,
      "uom": "kg",
      "options": [
        {
          "id": 789,
          "public_id": 1,
          "display_label": "Option 1 — ID 789",
          "is_chosen": false,
          "snap_product_name": "PP A1 grade",
          "snap_spec": "ASTM D...",
          "snap_origin": "Hàn Quốc",
          "snap_price_by_volume": 15000,
          "snap_moq": 200,
          "snap_quote_unit": "kg",
          "snap_vat": 10,
          "snap_delivery_time": "7-10 ngày"
        }
      ]
    }
  ]
}
```

### 8.5 Endpoint sinh PYC

| Method | URL | Quyền | Mô tả |
|--------|-----|-------|-------|
| POST | `/api/survey-requests/{id}/create-prs` | `survey_request.write` | Sinh PYC từ option đã chọn — trả về list PYC code+id |

**Điều kiện tiên quyết backend phải kiểm tra:**
1. `survey_request.status == "survey_done"`
2. Tất cả dòng đều có ít nhất 1 option với `is_chosen=true`
3. Người gọi là người tạo phiếu (`created_by == user.id`) hoặc AdminTM

**Response:**
```json
{
  "created_prs": [
    {"id": 201, "code": "PYC04072601", "supplier_name": "***"},
    {"id": 202, "code": "PYC04072602", "supplier_name": "***"}
  ],
  "message": "Đã tạo 2 phiếu yêu cầu mua hàng"
}
```

> Lưu ý: `supplier_name` trong response tạo PYC **không cần ẩn** vì PYC là bước sau, người YC đã qua việc chọn option — họ sẽ thấy NCC trên PYC của mình.

### 8.6 Phân quyền theo scope (giống hệ thống hiện tại)

| Scope | Người YC | Trưởng BP | NSTM | AdminTM |
|-------|----------|-----------|------|---------|
| `own` | Thấy phiếu mình tạo | — | — | — |
| `dept` | — | Thấy phiếu toàn phòng | — | — |
| `all` | — | — | Thấy phiếu được giao | Thấy tất cả |

---

## 9. Phân quyền chi tiết — Entity mới cần khai báo

### 9.1 Các quyền cần thêm vào seed / bảng phân quyền

```python
# Thêm vào danh sách entity trong bảng tab_permission_entity hoặc tương đương
SURVEY_REQUEST_PERMS = {
    "survey_request": {
        "read":     "Xem yêu cầu khảo sát",
        "create":   "Tạo yêu cầu khảo sát",
        "write":    "Sửa / Gửi duyệt yêu cầu khảo sát",
        "approve":  "Duyệt / Từ chối yêu cầu khảo sát",
        "process":  "Xử lý khảo sát (màn NSTM — thấy NCC)",
        "complete": "Chốt hoàn thành khảo sát (AdminTM)",
        "delete":   "Xóa yêu cầu khảo sát (chỉ nháp)",
    }
}
```

### 9.2 Gán quyền mặc định theo role

| Role | Quyền mặc định |
|------|----------------|
| Người dùng thông thường | `read(own)`, `create`, `write(own)` |
| Trưởng bộ phận | `read(dept)`, `approve(dept)` |
| Nhân sự thu mua | `read(all)`, `process` |
| Admin thu mua | Tất cả quyền + `complete` + `delete` + scope=all |

---

## 10. Tiêu chí nghiệm thu (Acceptance Criteria)

### 10.1 Luồng tạo & duyệt phiếu

```gherkin
Scenario: Người YC tạo phiếu yêu cầu khảo sát thành công
  Given  Người YC đăng nhập và có quyền survey_request.create
  When   Người YC tạo phiếu với 2 dòng sản phẩm, điền đủ phân loại và thông số
  Then   Hệ thống tạo phiếu với status=draft và code dạng YCKSDDMMYYxx
  And    Người YC thấy phiếu trong danh sách của mình

Scenario: Trưởng BP duyệt phiếu và hệ thống tự gán NSTM
  Given  Phiếu ở trạng thái submitted
  And    Bảng tab_category_assignee có cấu hình: item_group "NVL" → primary NSTM "NV001"
  When   Trưởng BP nhấn Duyệt
  Then   status chuyển sang processing
  And    Mỗi dòng có assignee = "NV001" (tự gán theo item_group)
  And    NSTM "NV001" nhận notification

Scenario: Trưởng BP từ chối phiếu
  Given  Phiếu ở trạng thái submitted
  When   Trưởng BP nhấn Từ chối với lý do "Thông số chưa rõ"
  Then   status chuyển sang rejected
  And    Người YC nhận notification kèm lý do "Thông số chưa rõ"
  And    Người YC có thể sửa và gửi lại
```

### 10.2 Màn NSTM tạo option

```gherkin
Scenario: NSTM chọn dòng khảo sát đã duyệt và tạo option
  Given  Phiếu ở trạng thái processing
  And    Trong tab_survey_product_line có dòng ID=100: supplier_code="NCC01", line_approve="Duyệt"
  When   NSTM vào màn process, chọn NCC "NCC01", thấy dòng ID=100
  And    NSTM nhấn "Thêm làm Option"
  Then   Bảng tab_survey_request_option có bản ghi mới:
         product_survey_line_id=100, public_id=1, supplier_code="NCC01"
         snap_product_name, snap_price_by_volume... snapshot đúng từ dòng nguồn

Scenario: NSTM chưa tìm thấy dòng khảo sát phù hợp
  Given  NCC "NCC02" không có dòng khảo sát SP nào đã duyệt
  When   NSTM chọn NCC "NCC02"
  Then   Danh sách dòng trống + hiện nút "Kích hoạt khảo sát sản phẩm mới"
  When   NSTM nhấn nút đó
  Then   Chuyển đến màn tạo phiếu khảo sát SP (Task 7) với NCC và thông số điền sẵn
```

### 10.3 Cơ chế ẩn NCC — bảo mật API

```gherkin
Scenario: Người YC KHÔNG thấy NCC qua API
  Given  Người YC đăng nhập với token hợp lệ
  And    Phiếu survey_request ID=5 của người YC ở trạng thái survey_done
  When   Người YC gọi GET /api/survey-requests/5/result
  Then   HTTP 200 trả về JSON
  And    JSON.lines[*].options[*] KHÔNG chứa key: supplier_code, supplier_name,
         snap_internal_code, nstm_note, supplier_survey_id, product_survey_line_id

Scenario: Người YC bị chặn khi truy cập endpoint nội bộ NSTM
  Given  Người YC đăng nhập (không có quyền survey_request.process)
  When   Người YC gọi GET /api/survey-requests/5/process
  Then   HTTP 403 Forbidden
  And    Response body chứa message lỗi, KHÔNG chứa dữ liệu NCC

Scenario: Người YC không thể bypass bằng cách đoán option ID
  Given  Người YC đăng nhập
  When   Người YC gọi GET /api/survey-request-options/789 (giả sử có endpoint đó)
  Then   HTTP 403 hoặc 404 — không trả về dữ liệu có NCC
```

### 10.4 Sinh PYC từ option

```gherkin
Scenario: Sinh đúng số PYC theo số NCC khác nhau
  Given  Phiếu survey_request có 3 dòng:
         - Dòng 1 chọn Option từ NCC-A
         - Dòng 2 chọn Option từ NCC-A
         - Dòng 3 chọn Option từ NCC-B
  When   Người YC nhấn "Tạo Phiếu yêu cầu mua hàng"
  Then   Hệ thống tạo 2 PYC:
         - PYC #1: 2 dòng hàng (dòng 1 + dòng 2, NCC-A)
         - PYC #2: 1 dòng hàng (dòng 3, NCC-B)
  And    Cả 2 PYC có status=draft
  And    PYC #1.suggested_supplier = tên NCC-A
  And    Các dòng PYC có giá lấy từ snap_price_by_volume của option

Scenario: Giá và số lượng trên PYC có thể sửa tự do
  Given  PYC vừa sinh với price=15,000₫
  When   Người YC sửa price thành 14,000₫ và submit
  Then   Hệ thống chấp nhận (PYC ở draft — sửa tự do)
  And    Workflow PYC tiếp tục bình thường

Scenario: Liên kết ngược ghi đúng
  Given  Sau khi sinh PYC thành công
  Then   survey_request_line.pr_id = ID của PYC tương ứng
  And    survey_request_line.pr_code = code của PYC tương ứng
  And    survey_request_line.is_completed = true
```

### 10.5 Các CA nghiệm thu bổ sung

```gherkin
Scenario: Không cho phép chốt survey_done khi còn dòng chưa có option
  Given  Phiếu có 2 dòng: dòng 1 có 2 option, dòng 2 chưa có option nào
  When   AdminTM nhấn "Chốt hoàn thành khảo sát"
  Then   HTTP 400: "Dòng 2 chưa có kết quả khảo sát nào"

Scenario: Không cho phép tạo PYC khi còn dòng chưa chọn option
  Given  Phiếu survey_done: dòng 1 đã chọn option, dòng 2 chưa chọn
  When   Người YC nhấn "Tạo PYC"
  Then   HTTP 400: "Vui lòng chọn phương án cho tất cả sản phẩm"
  And    UI hiển thị highlight dòng 2 chưa chọn
```

---

## 11. Edge Cases

### 11.1 Dòng không có option sau thời gian dài

**Tình huống:** NSTM nhận việc nhưng không tìm được NCC, dòng yêu cầu bị treo.

**Xử lý:**
- AdminTM vẫn có thể xóa option không phù hợp và thêm option mới bất kỳ lúc nào (khi `processing`).
- Không có timeout tự động — AdminTM theo dõi qua màn báo cáo (Task 8).
- Nếu thực sự không khảo sát được: AdminTM có thể chốt `survey_done` với ghi chú, option rỗng — hệ thống không bắt buộc phải có option (nhưng **nút chọn option + tạo PYC sẽ disabled** cho dòng đó, chỉ dòng nào có option mới được tạo PYC).
- **Quyết định khi dòng không có option:** Cho phép tạo PYC từ các dòng có option, bỏ qua dòng không có option → thể hiện trên UI rõ ràng ("Sản phẩm X không có kết quả khảo sát — không tạo PYC").

### 11.2 Nhiều option cùng một NCC trên cùng một dòng

**Tình huống:** NSTM gắn 2 option từ cùng NCC-A (2 dòng khảo sát khác nhau) cho cùng 1 dòng yêu cầu.

**Xử lý:**
- Hệ thống cho phép, `public_id` vẫn tăng tuần tự (Option 1, Option 2).
- Khi người YC chọn 1 trong 2 → chỉ option đó `is_chosen=true`.
- Khi sinh PYC: gom theo `supplier_code` → cả 2 option thuộc NCC-A → chỉ tạo **1 PYC** với 2 dòng hàng? Hay 1 dòng?
- **Quyết định:** Mỗi option = 1 dòng hàng trong PYC (dù cùng NCC). Người YC chỉ chọn 1 option/dòng yêu cầu → khi gom chỉ có 1 option được chọn → 1 dòng PYC. Không có trường hợp 2 option cùng NCC cùng dòng đều `is_chosen=true`.

### 11.3 Người YC muốn đổi option sau khi đã chọn (chưa tạo PYC)

**Tình huống:** Người YC chọn Option 1, sau đó muốn đổi sang Option 2.

**Xử lý:**
- Endpoint `PATCH .../options/{oid}/choose` tự động unset option cũ (`is_chosen=false`) của cùng dòng.
- Hoàn toàn tự do trước khi nhấn "Tạo PYC".

### 11.4 Người YC muốn đổi option sau khi đã tạo PYC

**Tình huống:** PYC đã sinh ở nháp, người YC muốn quay lại chọn option khác.

**Xử lý:**
- PYC đang `draft` → người YC **sửa trực tiếp trên PYC** (thay đổi giá, số lượng) thay vì đổi option.
- Nếu muốn đổi NCC hoàn toàn: người YC xóa PYC nháp → quay lại survey_request → nhấn "Tạo PYC" lại (sẽ tạo PYC mới, PYC cũ bị xóa hoặc giữ nguyên tuỳ quyết định).
- **Quyết định đơn giản:** Nếu đã có PYC (`survey_request_line.pr_id != null`), nút "Tạo PYC" đổi thành "Xem PYC" + "Tạo lại PYC" (cảnh báo sẽ tạo phiếu mới, phiếu cũ vẫn tồn tại ở nháp — người YC tự xóa phiếu cũ).

### 11.5 Khảo sát sản phẩm mới bị từ chối sau khi NSTM kích hoạt

**Tình huống:** NSTM kích hoạt khảo sát mới → khảo sát đó bị từ chối → không có dòng đã duyệt.

**Xử lý:**
- Dòng yêu cầu vẫn ở trạng thái không có option.
- NSTM phải thử NCC khác hoặc sửa lại khảo sát SP rồi gửi duyệt lại.
- Không có side effect trên phiếu yêu cầu khảo sát.

### 11.6 Option nguồn bị xóa sau khi snapshot

**Tình huống:** Sau khi snapshot, dòng `tab_survey_product_line` bị xóa hoặc thay đổi.

**Xử lý:** Snapshot đã lưu riêng trong `tab_survey_request_option.snap_*` → không bị ảnh hưởng. `product_survey_line_id` có thể trỏ đến bản ghi không còn tồn tại nhưng dữ liệu hiển thị không thay đổi.

### 11.7 Phiếu yêu cầu khảo sát bị từ chối sau khi đã processing một phần

**Tình huống:** Phiếu đang `processing`, NSTM đã tạo một số option → trưởng BP muốn từ chối?

**Xử lý:** Sau khi `approved` thì không có transition về `rejected`. Nếu yêu cầu thay đổi:
- AdminTM chỉnh sửa dòng yêu cầu (sửa thông số, xóa/thêm dòng) ngay cả khi đang `processing`.
- Xóa/thêm option nếu cần.
- Không rollback trạng thái phiếu.

### 11.8 Hai người YC cùng nhấn "Tạo PYC" cùng lúc (concurrency)

**Xử lý:** Backend cần dùng database transaction. Kiểm tra `is_completed` của các dòng trước khi tạo. Nếu dòng đã `is_completed=true` thì bỏ qua (idempotent). Phòng trường hợp duplicate PYC, có thể dùng SELECT FOR UPDATE hoặc UNIQUE constraint trên `(survey_request_line_id)` cho bản ghi đã hoàn thành.

---

## 12. Câu hỏi mở còn lại

Theo tài liệu `Plan_CapNhat_Flow_KhaoSat_v2.md`, **không còn câu hỏi mở nào chặn triển khai**. Tuy nhiên, trong quá trình code có thể phát sinh:

| # | Câu hỏi | Đề xuất xử lý mặc định |
|---|---------|------------------------|
| 1 | Khi survey_done nhưng một số dòng không có option — có cho phép tạo PYC từ dòng có option không? | Cho phép — tạo PYC từ dòng có option, bỏ qua dòng không có option; cảnh báo trên UI |
| 2 | Thông báo (notification) gửi cho NSTM khi nào? | Ngay khi approve (tự gán NSTM) — dùng `trigger_notification` tương tự survey cũ |
| 3 | Có cần in phiếu "Yêu cầu khảo sát"? | Chưa cần — PYC mới cần in; yêu cầu khảo sát là nội bộ hệ thống |
| 4 | Scope NSTM xem màn process: chỉ thấy phiếu được giao (assignee) hay tất cả? | Thấy phiếu có ít nhất 1 dòng được giao cho mình (`assignee = emp_code`) |
| 5 | PYC sinh ra có cần gắn `assignee_id` ở header không? | Không — để trống; Task 4 tự gán khi trưởng BP duyệt PYC |
| 6 | Nếu người YC không muốn tạo PYC từ khảo sát mà muốn tạo thẳng PYC sau khi xem kết quả? | Vẫn được — họ chỉ cần không nhấn "Tạo PYC từ khảo sát" và tạo PYC thẳng như cũ |

---

## Phụ lục A — Cấu trúc thư mục backend đề xuất

```
backend/app/modules/
├── survey/                    (đã có — khảo sát NCC/SP cũ)
│   ├── model.py
│   ├── service.py
│   └── controller.py
└── survey_request/            (MỚI — Task 5)
    ├── model.py               (SurveyRequest, SurveyRequestLine, SurveyRequestOption)
    ├── schema.py              (Pydantic: Create/Update/Out/PublicOut/InternalOut)
    ├── service.py             (CRUD, workflow, option management, create_prs)
    └── controller.py         (router /api/survey-requests/*)
```

## Phụ lục B — Cấu trúc frontend đề xuất

```
frontend/src/
├── pages/
│   ├── SurveyRequests/
│   │   ├── List.tsx           (danh sách — người YC xem)
│   │   ├── Form.tsx           (tạo/sửa — draft/rejected)
│   │   ├── Detail.tsx         (xem chi tiết + tab kết quả — người YC)
│   │   └── ProcessView.tsx    (màn xử lý NSTM — cần quyền process)
│   └── ...
├── api/
│   └── survey-request.ts     (API calls)
└── config/
    └── cruds.tsx              (thêm route + menu)
```

## Phụ lục C — Migration DB

```sql
-- Bảng 1: header
CREATE TABLE tab_survey_request (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL DEFAULT '',
    company_id BIGINT NOT NULL DEFAULT 0,
    requester VARCHAR(255) NOT NULL DEFAULT '',
    requester_position VARCHAR(100) NOT NULL DEFAULT '',
    department VARCHAR(255) NOT NULL DEFAULT '',
    head_of_dept VARCHAR(255) NOT NULL DEFAULT '',
    purpose VARCHAR(255) NOT NULL DEFAULT '',
    request_date VARCHAR(10) NOT NULL DEFAULT '',
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    assignee_id BIGINT NOT NULL DEFAULT 0,
    note TEXT,
    reject_reason TEXT,
    created_by BIGINT NOT NULL,
    updated_by BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sr_status (status),
    INDEX idx_sr_department (department),
    INDEX idx_sr_created_by (created_by)
);

-- Bảng 2: dòng yêu cầu
CREATE TABLE tab_survey_request_line (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    survey_request_id BIGINT NOT NULL,
    internal_line_code VARCHAR(50) NOT NULL DEFAULT '',
    received_date VARCHAR(10) NOT NULL DEFAULT '',
    result_due_date VARCHAR(10) NOT NULL DEFAULT '',
    department_requester VARCHAR(255) NOT NULL DEFAULT '',
    item_group VARCHAR(100) NOT NULL DEFAULT '',
    requirement_detail TEXT,
    other_requirement TEXT,
    request_qty DECIMAL(18,3) NOT NULL DEFAULT 0,
    uom VARCHAR(25) NOT NULL DEFAULT '',
    proposed_price DECIMAL(18,2) NOT NULL DEFAULT 0,
    image_file VARCHAR(500),
    image_attachment_id BIGINT,
    assignee VARCHAR(100) NOT NULL DEFAULT '',
    pr_id BIGINT,
    pr_code VARCHAR(50) NOT NULL DEFAULT '',
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_by BIGINT NOT NULL,
    updated_by BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_srl_survey_request_id (survey_request_id),
    INDEX idx_srl_item_group (item_group),
    INDEX idx_srl_assignee (assignee)
);

-- Bảng 3: option (kết quả khảo sát gắn vào dòng)
CREATE TABLE tab_survey_request_option (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    survey_request_line_id BIGINT NOT NULL,
    product_survey_line_id BIGINT NOT NULL,
    public_id INT NOT NULL DEFAULT 1,
    display_label VARCHAR(50) NOT NULL DEFAULT '',
    is_chosen BOOLEAN NOT NULL DEFAULT FALSE,
    chosen_at DATETIME,
    chosen_by BIGINT,
    -- Snapshot thông số (public — hiển thị với người YC)
    snap_product_name VARCHAR(255) NOT NULL DEFAULT '',
    snap_spec TEXT,
    snap_origin VARCHAR(100) NOT NULL DEFAULT '',
    snap_quote_unit VARCHAR(25) NOT NULL DEFAULT '',
    snap_moq DECIMAL(18,3) NOT NULL DEFAULT 0,
    snap_price_by_volume DECIMAL(18,2) NOT NULL DEFAULT 0,
    snap_volume_range VARCHAR(100) NOT NULL DEFAULT '',
    snap_vat DECIMAL(5,2) NOT NULL DEFAULT 0,
    snap_delivery_time VARCHAR(100) NOT NULL DEFAULT '',
    snap_delivery_place VARCHAR(255) NOT NULL DEFAULT '',
    snap_shipping_cost DECIMAL(18,2) NOT NULL DEFAULT 0,
    snap_sample_ready BOOLEAN NOT NULL DEFAULT FALSE,
    snap_lab_result VARCHAR(20) NOT NULL DEFAULT '',
    -- Thông tin NCC (nội bộ — KHÔNG trả cho người YC)
    snap_internal_code VARCHAR(50) NOT NULL DEFAULT '',
    supplier_code VARCHAR(50) NOT NULL DEFAULT '',
    supplier_name VARCHAR(255) NOT NULL DEFAULT '',
    supplier_survey_id BIGINT NOT NULL DEFAULT 0,
    nstm_note TEXT,
    -- Audit
    created_by BIGINT NOT NULL,
    updated_by BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sro_line_id (survey_request_line_id),
    INDEX idx_sro_product_survey_line_id (product_survey_line_id),
    INDEX idx_sro_is_chosen (is_chosen)
);
```
