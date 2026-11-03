# Requirement & Kế hoạch triển khai — Mini Tool Quản lý Thu Mua

> Web nội bộ ~20 user, dữ liệu nhỏ. Mục tiêu: số hóa 3 nghiệp vụ Thu mua (Khảo sát → Mua hàng → Nhận hàng/GR) + công nợ + báo cáo, có phân quyền & thông báo email.
> Tài liệu này dùng để **bàn giao cho dev code theo từng phase**.

---

## 0. Công nghệ & nguyên tắc

| Lớp | Công nghệ |
|---|---|
| Frontend | **React + Vite + TypeScript** (SPA), UI lib: Mantine/Ant Design |
| Backend | **FastAPI** + SQLAlchemy + Alembic + Pydantic |
| Async/Lịch | **Celery Worker + Celery Beat + Redis** |
| Database | **MySQL 8** |
| Auth | **Google OAuth** (chỉ nhân viên active) **+ mã NV/mật khẩu** + JWT + RBAC |
| In PDF | **WeasyPrint** (HTML → PDF) |
| Lưu file đính kèm | **Cloudflare R2** (S3-compatible) — DB chỉ lưu key/url |
| Triển khai | **Docker Compose** / 1 VPS ~4GB — services: `nginx · api · worker · beat · redis · mysql` |

**Nguyên tắc:** monolith gọn, không microservices; mọi danh sách có filter + phân trang + xuất Excel; mọi bước duyệt có nhánh Duyệt/Từ chối (kèm lý do); mọi thao tác ghi audit log; **mọi thao tác đính kèm được chứng từ** và xem "bộ chứng từ liên quan" theo đơn (nếu có quyền); ưu tiên **thao tác gọn trên 1 màn hình** (nhập số liệu + đính kèm ngay, tránh đi tới đi lui); **phiếu giao hàng & hóa đơn ghi nhận ngầm**, người dùng chỉ thao tác trên màn đơn giản (kiểu sheet).

## 0.1 Quy ước Database & kỹ thuật (BẮT BUỘC)

- **Khóa chính:** `id` kiểu **BIGINT AUTO_INCREMENT** (số tăng dần) — **KHÔNG dùng UUID**.
- **Mã (code):** `VARCHAR(25)` (mã ngắn) hoặc `VARCHAR(50)` (mã dài).
- **Tên:** `VARCHAR(255)`.
- **Ghi chú / mô tả / JSON:** `TEXT` — **JSON lưu dạng chuỗi text**, không dùng kiểu JSON native.
- **Trạng thái:** `VARCHAR(30)`.
- **Tiền:** `DECIMAL(18,2)` · **Số lượng:** `DECIMAL(18,3)`.
- **Ngày:** `DATE` / `DATETIME` · **Boolean:** `TINYINT(1)` (vd `is_active`).
- **Khóa ngoại:** `{entity}_id BIGINT`.
- **Cây phân cấp:** cột `parent BIGINT` — **`parent = 0` nghĩa là node gốc** (cha cao nhất).
- **Cột kiểm toán (mọi bảng):** `created_at, created_by, updated_at, updated_by`.
- **Báo cáo (chạy ngầm):** KHÔNG tính trực tiếp lúc mở màn hình (tránh treo). **Worker cập nhật bảng snapshot báo cáo** mỗi khi có action liên quan (tạo/duyệt/nhận hàng…); màn hình báo cáo chỉ ĐỌC snapshot → luôn nhanh.
- **Template in/email:** giai đoạn đầu **định nghĩa trong backend** (Jinja). Thêm bảng template cấu hình động ở giai đoạn sau.

---

## 1. Vai trò & phân quyền (RBAC)

| Vai trò | Phạm vi dữ liệu | Quyền chính |
|---|---|---|
| BPYC | Đơn của mình | Tạo yêu cầu mua, theo dõi, nghiệm thu |
| NSTM | Dữ liệu của mình | Khảo sát, nhập liệu, tạo PO, nhận hàng, công nợ |
| QLTM | Toàn phòng | Duyệt: đơn gấp, chi phí, NCC, PO, chứng từ, thanh toán |
| Admin TM | Toàn phòng | Soát dữ liệu, danh mục, báo cáo, cấu hình hệ thống |
| Kế toán | Công nợ/hóa đơn | Mã NCC MISA, đối chiếu công nợ, thanh toán |
| Nhân viên kho | Đơn cần nhận | Nhận hàng, nhập tồn |

### 1.1 Phân quyền chi tiết (granular) — quyền theo HÀNH ĐỘNG × ĐỐI TƯỢNG

Mỗi cặp (Vai trò × Đối tượng) gắn các cờ quyền:

| Cờ quyền | Ý nghĩa |
|---|---|
| `can_read` | Xem |
| `can_create` | Tạo mới |
| `can_write` | Sửa |
| `can_delete` | Xóa |
| `can_approve` | Duyệt / từ chối (với đối tượng có luồng duyệt) |
| `can_print` | In (PDF) |
| `can_export` | Xuất Excel |
| `scope` | Phạm vi dòng: `own` (bản ghi **do mình tạo HOẶC được gán** `assigned_to_id`) / `dept` (bộ phận) / `all` (toàn cục) |

**Đối tượng (entity):** supplier, product, contract, purchase_request, survey, purchase_order, goods_receipt, inventory, payable, report, settings…

**Bảng DB:**
```
roles(id, name)
permissions(id, role_id, entity, can_read, can_create, can_write,
            can_delete, can_approve, can_print, can_export, scope)
user_roles(user_id, role_id)
```

**Thực thi:** backend kiểm tra quyền ở mỗi endpoint (dependency của FastAPI) — đây là lớp chặn thật; `scope` lọc dữ liệu theo người tạo/bộ phận. Frontend chỉ **ẩn/hiện nút** theo quyền (UX), không phải lớp bảo mật. Màn “Quản trị → Phân quyền” cho Admin tick các cờ trên một ma trận Vai trò × Đối tượng.

> ✅ **Đã chốt:** QLTM là **cấp duyệt cao nhất** (trước mắt không có BOD). NSTM `scope = own` — chỉ xem bản ghi **do mình tạo hoặc được gán** (`assigned_to_id`).

### 1.2 Đăng nhập & cấp tài khoản
- **2 cách đăng nhập:** (1) **Google** (email) — chỉ chấp nhận nếu khớp một **nhân viên đang active** có `tab_user`; (2) **Mã nhân viên + mật khẩu** (`employee.code` + password).
- **Cấp/khóa tài khoản & đổi mật khẩu:** vai trò **Quản lý nhân sự / Admin** được **cấp tài khoản** cho nhân viên và **đặt lại mật khẩu** cho họ.
- Mọi đăng nhập bắt buộc `tab_user.is_active = 1` và nhân viên active.

---

## 2. Cấu trúc dự án (gợi ý)

```
repo/
├─ docker-compose.yml
├─ backend/            # FastAPI
│  ├─ app/
│  │  ├─ api/          # routers theo module
│  │  ├─ models/       # SQLAlchemy
│  │  ├─ schemas/      # Pydantic
│  │  ├─ services/     # business logic
│  │  ├─ tasks/        # Celery tasks (email, report, beat schedules)
│  │  ├─ core/         # config, auth, rbac, db
│  │  └─ main.py
│  └─ alembic/
├─ frontend/           # React + Vite + TS
│  ├─ src/
│  │  ├─ pages/        # theo màn hình
│  │  ├─ components/
│  │  ├─ api/          # gọi REST
│  │  ├─ auth/         # Google OAuth, guard theo quyền
│  │  └─ layouts/
└─ nginx/
```

### 2.1 Docker — khởi động nhanh (Phase 0)

**Bản gọn lúc đầu** (chưa cần Redis/Celery — email gửi qua FastAPI BackgroundTasks):

```yaml
# docker-compose.yml (Phase 0-2)
services:
  db:    { image: mysql:8, env: MYSQL_DATABASE/USER/PASSWORD, volume: db_data }
  api:   { build: ./backend, depends_on: [db], ports: ["8000:8000"] }   # uvicorn FastAPI
  web:   { build: ./frontend, ports: ["80:80"] }                        # build React → nginx
# Phase 3 thêm:
#  redis, worker (celery), beat (celery beat)
```

**Cấu hình qua `.env`** (KHÔNG commit — thêm `.gitignore`): `DB_*`, `JWT_SECRET`, `GOOGLE_OAUTH_*`, `SMTP_*`, và **R2**: `R2_ENDPOINT`, `R2_PUBLIC_URL`, `R2_BUCKET=nexterp-storage`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`. *(Secret R2 đã lộ trong chat → nên rotate lại trên Cloudflare.)*

**Các bước bắt đầu:**
1. `docker compose up -d db` → `alembic upgrade head` (tạo bảng).
2. `docker compose up api web` → mở `http://localhost`.
3. Tạo seed: roles + permissions mặc định + 1 user Admin.
4. **Làm 1 “lát cắt dọc” trước** (vertical slice): Đăng nhập → RBAC → 1 đối tượng **NCC** (list + filter + tạo + sửa + phân quyền) chạy thông suốt. Chốt khung này rồi **nhân bản** sang các đối tượng khác — đây là cách dựng nhanh & gọn nhất.

---

## 3. Mô hình dữ liệu (bảng `tab_`)

> Tuân thủ Quy ước DB ở mục 0.1 (id BIGINT, code varchar 25/50, note/json = TEXT, `parent=0` là gốc, đủ cột kiểm toán).

**Tài khoản · Tổ chức · Phân quyền**
- `tab_user` — tài khoản đăng nhập (email, google_sub, **password_hash**, employee_id, is_active)
- `tab_employee` — nhân viên (code, full_name, email, phone, company_id, department_id, position, user_id)
- `tab_company` — **pháp nhân nhận hóa đơn** (code, name, tax_code, address, invoice_email, **parent**, is_active)
- `tab_department` — phòng ban (code, name, company_id, **parent**, is_active)
- `tab_role`, `tab_permission`, `tab_user_role` — phân quyền chi tiết (mục 1.1)

**Danh mục dùng chung**
- `tab_unit`, `tab_unit_conversion` (Sheet 5), `tab_item_group`, `tab_warehouse`, `tab_tolerance_rule`, `tab_cancel_reason`, `tab_code_rule`

**Đối tác & hàng hóa**
- `tab_supplier` (có `supplier_type = goods | transport` — NCC bán hàng / đơn vị vận chuyển), `tab_supplier_contact`, `tab_product`, `tab_contract`

**Nghiệp vụ**
- `tab_purchase_request` (+ `tab_purchase_request_item`) — Yêu cầu mua
- `tab_survey` (+ `tab_survey_supplier_line` / `tab_survey_product_line`) — Khảo sát: 1 form chính + bảng con theo `survey_type`
- `tab_sample`, `tab_lab_result` — mẫu & kết quả test
- `tab_purchase_order` (+ `tab_po_item`) — đơn mua; **giá hàng nằm ở `tab_po_item`**
- `tab_po_delivery` — các lần giao/nhận của từng `po_item` (Sheet 6): kho, đơn vị vận chuyển, SL gửi/nhận, **chi phí vận chuyển riêng**
- `tab_goods_receipt` (+ `tab_gr_item`), `tab_inventory`, `tab_inventory_move`
- `tab_payable` (`source_type = goods | shipping` — 2 luồng công nợ riêng), `tab_payment` (+ `tab_payment_line` — gom nhiều công nợ vào 1 phiếu)
- `tab_purchase_invoice` (+ `tab_purchase_invoice_line`) — hóa đơn mua, ghi nhận ngầm từ các lần nhận; phiếu giao hàng in từ `tab_po_delivery` gom theo đơn

**Hệ thống**
- `tab_attachment` — **đa hình** (`entity_type`, `entity_id`) + `purchase_order_id` để gom "bộ chứng từ theo đơn"; `tab_notification`, `tab_email_log`, `tab_audit_log` (`tab_email_template`: giai đoạn sau)
- `tab_report_*` — **bảng snapshot báo cáo** do worker cập nhật ngầm (vd `tab_report_purchase_progress`, `tab_report_supplier_kpi`)

---

### 3.1 Đơn hàng – Giao hàng – Vận chuyển – Công nợ (quan trọng)

- **Đơn mua** `tab_purchase_order` → nhiều dòng **`tab_po_item`** (mỗi SP: SL yêu cầu, SL đặt NCC, ĐVT, **đơn giá hàng**, VAT, thành tiền). *Giá hàng nằm ở đây.*
- Mỗi `tab_po_item` có thể **giao nhiều lần** → nhiều dòng **`tab_po_delivery`** (đúng như Sheet 6): `delivery_no`, `warehouse_id` (kho nhận), `carrier_id` (đơn vị vận chuyển), `ship_qty`, `ship_unit` (vd Kiện), `received_qty` (SL đã nhận), `received_date`, `status`.
- **Chi phí vận chuyển TÍNH RIÊNG:** mỗi `tab_po_delivery` có `shipping_unit_price` (giá theo ĐVT vận chuyển, vd theo Kiện) + `shipping_amount`. **KHÔNG cộng vào giá đơn hàng.**
- **Đơn vị vận chuyển là NCC riêng** (`supplier_type = transport`, vd Mekong Logistics; hoặc "NCC tự vận chuyển"). Có **công nợ riêng, thanh toán riêng**, không ảnh hưởng công nợ hàng hóa.
- **Hai luồng công nợ** (`tab_payable.source_type`): (1) `goods` — công nợ hàng cho NCC bán (SL nhận × đơn giá); (2) `shipping` — công nợ vận chuyển cho đơn vị vận chuyển (theo `shipping_amount`).
- **Thanh toán gom** (`tab_payment` + `tab_payment_line`): 1 phiếu có thể **gom nhiều công nợ** (DNTT theo tháng) hoặc **theo từng đơn** (DNTT theo đơn). `tab_payment_line` nối payment ↔ payable.

### 3.2 Chứng từ · Kho · Nguyên tắc 1 màn hình

- **Đính kèm khắp nơi:** `tab_attachment` đa hình (`entity_type`, `entity_id`) + `purchase_order_id` → gom **"bộ chứng từ liên quan theo đơn"** (phiếu đề xuất, báo giá, PO, phiếu giao hàng, hóa đơn, chứng từ thanh toán). Ai có quyền xem đơn thì xem được cả bộ.
- **Phiếu giao hàng & Hóa đơn (ghi nhận ngầm):** phiếu giao hàng in được, gom theo đơn từ `tab_po_delivery`; `tab_purchase_invoice` tạo ngầm từ các lần nhận. Người dùng chỉ thao tác trên màn đơn giản (kiểu sheet), hệ thống lo phần chứng từ.
- **Thao tác 1 màn hình:** ví dụ màn công nợ có nút **Thanh toán** ngay tại chỗ → nhập số tiền + đính kèm chứng từ → xong, không phải chuyển nhiều màn.
- **Kho & tồn (đơn giản nhất):** `tab_warehouse` thuộc **company** (`company_id`); `tab_inventory` theo (`warehouse_id`, `product_id`); nhập kho lấy từ `tab_po_delivery.received_qty` → biết mỗi đơn đã nhập bao nhiêu. **Quy đổi ĐVT:** tự động nếu có cấu hình (Sheet 5), không thì cho nhập tay số quy đổi.

## 4. Danh sách chức năng (mã F)

**Chung:** F-01 Đăng nhập Google+RBAC · F-02 Dashboard theo vai trò · F-03 Thông báo in-app · F-04 Hồ sơ
**PYC:** F-10 Tạo/sửa yêu cầu · F-11 Giao việc · F-12 Duyệt/từ chối · F-13 Theo dõi trạng thái
**Khảo sát:** F-20 Khảo sát NCC · F-21 Khảo sát SP · F-22 Quy đổi ĐVT · F-23 Mẫu & LAB · F-24 Trình duyệt
**Mua hàng:** F-30 Tạo PO · F-31 Duyệt PO theo ngưỡng · F-32 Tiến độ + cảnh báo trễ · F-33 In PO · F-34 Giao hàng nhiều lần + vận chuyển (chi phí & công nợ riêng)
**GR:** F-40 Nhận & đối chiếu PO · F-41 Cập nhật nhận & QC · F-42 Xử lý thiếu/lỗi/trả · F-43 Duyệt chứng từ & nhập kho · F-44 Phiếu giao hàng (gom theo đơn) · F-45 Hóa đơn ghi nhận ngầm
**Công nợ:** F-50 Công nợ hàng (NCC bán) · F-52 Công nợ vận chuyển (đơn vị VC, riêng) · F-51 Thanh toán gom 1/nhiều lần — **nút Thanh toán ngay trên màn: nhập số tiền + đính kèm chứng từ**
**Danh mục:** F-60 NCC · F-61 Sản phẩm · F-62 Hợp đồng · F-63 Kho (theo company) & tồn đơn giản + quy đổi tùy chọn
**Báo cáo:** F-70 Tiến độ · F-71 KPI/đánh giá NCC · F-72 Chi phí · F-73 Xuất Excel/PDF *(đọc từ bảng snapshot worker cập nhật ngầm)*
**Tổ chức:** F-87 Quản lý Công ty (pháp nhân, cây `parent`) · F-88 Quản lý Phòng ban (cây `parent`) · F-89 Quản lý Nhân viên (theo công ty/phòng ban, gắn tài khoản)
**Hệ thống:** F-80 User & phân quyền · F-81 Cấu hình email · F-82 Cấu hình duyệt theo ngưỡng · F-83 Danh mục dùng chung · F-84 Quy tắc mã · F-85 Audit log · F-86 Sao lưu
**Xuyên suốt:** F-90 Đính kèm ở mọi thao tác + **xem bộ chứng từ liên quan theo đơn** · F-91 Filter nâng cao · F-92 Bình luận/@mention

---

## 5. KẾ HOẠCH THEO PHASE

### 🔧 Phase 0 — Nền tảng (foundation)
- **Mục tiêu:** dựng khung dự án chạy được, đăng nhập & phân quyền.
- **Việc:** scaffold FE/BE; `docker-compose` (api, web, mysql, redis, worker, beat, nginx); Google OAuth + JWT; bảng `users/roles/permissions` + middleware RBAC; layout chung (sidebar, topbar, chuông thông báo); base `audit_logs`, `settings`; trang 403/404; CI build.
- **Chức năng:** F-01, F-02 (khung), F-03 (khung), F-85 (ghi log).
- **Done khi:** đăng nhập Google → vào dashboard rỗng theo vai trò; route bị chặn đúng theo quyền; Celery gửi được 1 email test.

### 🟦 Phase 1 — Danh mục + Khảo sát (MVP lõi)
- **Mục tiêu:** chạy trọn luồng Khảo sát → trình duyệt.
- **Màn hình:** Quản lý NCC, Quản lý Sản phẩm, Quy đổi ĐVT; Yêu cầu mua (PYC) list+form+chi tiết; Khảo sát NCC (Sheet 3 – so sánh 2-3 NCC); Khảo sát SP (Sheet 4); Mẫu & kết quả LAB; Trình duyệt khảo sát.
- **Chức năng:** F-60, F-61, F-22, F-10→F-13, F-20→F-24, F-90, F-91.
- **Bảng:** suppliers, products, unit_conversions, purchase_requests(+items), survey_suppliers, survey_products, samples, lab_results, attachments.
- **Email:** F-81 cơ bản — giao việc, chờ duyệt, kết quả duyệt/từ chối.
- **Done khi:** BPYC tạo yêu cầu → QLTM giao NSTM → NSTM khảo sát NCC/SP, quy đổi giá, ghi kết quả LAB → trình QLTM duyệt → phản hồi; có email ở các mốc.

### 🟩 Phase 2 — Mua hàng (PO) + Nhận hàng (GR)
- **Mục tiêu:** từ NCC đã duyệt → tạo PO → nhận hàng → tồn kho.
- **Màn hình:** Đơn mua & PO (chi tiết line item có **bảng giao hàng nhiều lần**); In PO/Đơn mua hàng; Nhận hàng & Kiểm tra (GR) theo từng lần giao; cập nhật tồn cơ bản.
- **Chức năng:** F-30→F-34, F-40→F-43, F-63 (tồn cơ bản).
- **Bảng:** `tab_purchase_order`(+`tab_po_item`), **`tab_po_delivery`** (giao/nhận nhiều lần + vận chuyển), `tab_goods_receipt`(+items), `tab_inventory`, `tab_inventory_move`.
- **Done khi:** tạo PO → duyệt → in PO → mỗi line item giao nhiều lần (kho, đơn vị vận chuyển, chi phí VC riêng) → nhận từng lần, nhập SL thực nhận + QC → cập nhật tồn.

### 🔔 Phase 3 — Cảnh báo & thông báo đầy đủ
- **Mục tiêu:** tự động nhắc việc, cảnh báo trễ hạn.
- **Việc:** Celery Beat — quét đơn trễ hạn (chênh lệch ngày < 0), nhắc D-1 trước giao, nhắc công nợ trước ngày 12, cảnh báo HĐ sắp hết hạn; nghiệm thu BPYC; trung tâm thông báo đầy đủ; cấu hình email F-81 full (bật/tắt, người nhận, template, log+retry).
- **Chức năng:** F-32 (cảnh báo), F-03 full, F-81 full.
- **Done khi:** các email/nhắc lịch chạy tự động đúng lịch; xem được nhật ký email.

### 📊 Phase 4 — Công nợ · Báo cáo · Hợp đồng
- **Màn hình:** Công nợ (2 luồng: hàng + vận chuyển) & Thanh toán gom (Sheet 8/10); Quản lý Hợp đồng + cảnh báo hết hạn; Báo cáo tiến độ/KPI/chi phí; xuất Excel.
- **Chức năng:** F-50, F-52, F-51, F-62, F-70→F-73.
- **Bảng:** `tab_payable` (`source_type` goods/shipping), `tab_payment`(+`tab_payment_line`), `tab_contract`.
- **Done khi:** công nợ hàng & vận chuyển tách riêng; 1 phiếu thanh toán gom nhiều công nợ; báo cáo & xuất Excel; cảnh báo HĐ hết hạn.

### ⚙️ Phase 5 — Quản trị nâng cao & tinh chỉnh
- **Việc:** F-82 cấu hình quy trình duyệt theo ngưỡng; F-83 danh mục dùng chung; F-84 quy tắc mã tự sinh; mẫu in (template) + logo; UI audit log; F-86 sao lưu.
- **(Tùy chọn):** tích hợp MISA (đồng bộ mã/công nợ), liên kết Zalo.

---

## 6. API chính (REST — gợi ý)

```
POST /auth/google            # đăng nhập
GET  /me                     # thông tin + quyền

GET/POST/PUT  /suppliers          /products       /contracts
GET/POST/PUT  /purchase-requests  + /{id}/assign  /{id}/approve  /{id}/reject
GET/POST/PUT  /surveys/suppliers  /surveys/products  /surveys/{id}/submit  /approve
POST          /lab-results
GET/POST/PUT  /purchase-orders    /{id}/approve   /{id}/print(pdf)
GET           /order-tracking     (+filter)
POST          /goods-receipts     /{id}/qc        /{id}/approve-docs
GET           /inventory
GET/POST      /payables           /payments
GET           /reports/...        (+export)
GET/PUT       /settings/...       /notifications  /audit-logs
```
Mọi endpoint danh sách hỗ trợ `?filter=...&sort=...&page=...`.

---

## 7. Thông báo & email (trigger)

| Sự kiện | Người nhận | Kênh | Phase |
|---|---|---|---|
| Giao việc khảo sát | NSTM | in-app+email | 1 |
| PYC/PO chờ duyệt | QLTM | in-app+email | 1/2 |
| Kết quả duyệt/từ chối | NSTM (+BPYC) | in-app+email | 1 |
| Kết quả test LAB | NSTM | in-app+email | 1 |
| Đơn sắp tới hạn (D-1) | NSTM | email (Beat) | 3 |
| Đơn trễ hạn | NSTM+QLTM | in-app+email (Beat) | 3 |
| Cần nghiệm thu | BPYC | in-app+email | 3 |
| Công nợ tới hạn (trước 12) | NSTM+Kế toán | email (Beat) | 4 |
| HĐ sắp hết hạn | NSTM+QLTM | email (Beat) | 4 |

---

## 8. Quy ước

- **Mã:** `PYC.[TH/NM].[ddmmyy].[STT]` · PO theo MISA · mã hàng NLNK/NLT/BTPM/CPNK + số tăng.
- **Trạng thái:**
  - PYC: Mới → Đang khảo sát → Chờ duyệt → Đã duyệt → Hoàn thành / Hủy
  - **PO: Nháp → Chưa đặt hàng → Đã đặt hàng → Đang giao → Đã nhận đủ → Hoàn thành / Hủy** (in PO = gửi NCC từ trạng thái "Chưa đặt hàng" trở đi)
  - Giao hàng (`tab_po_delivery`): Chờ giao → Đang giao → Đã nhận (Đủ / Thiếu / Lỗi)
  - *(Trạng thái lấy theo Sheet 6: Đang chờ, Đã giao đủ, Giao thiếu, Trễ, Hủy, Hoàn thành — sẽ map vào các trạng thái trên.)*
- **Filter chung:** đa tiêu chí AND, tìm nhanh mã/tên, lọc khoảng ngày, lưu bộ lọc, xuất Excel.
- **Nhận hàng:** chênh lệch SL cho phép & số ngày kiểm theo từng NCC (cấu hình `tolerance_rules`).

---

## 9. Quyết định đã chốt
1. ✅ Phân cấp duyệt: **QLTM là cấp cao nhất** (trước mắt không có BOD).
2. ✅ NSTM `scope = own` — chỉ xem bản ghi **do mình tạo hoặc được gán**.
3. ✅ Công nợ: **có luồng đầy đủ** (2 luồng hàng/vận chuyển), xây ở Phase 4.
4. ✅ File đính kèm: **Cloudflare R2** (S3), cấu hình qua `.env`.
5. ✅ Đăng nhập: **Google (chỉ nhân viên active) + Mã NV/mật khẩu**; Admin/HR cấp tài khoản & đặt lại mật khẩu.
6. ✅ **Không đồng bộ MISA.**
```
