# Plan cập nhật Thu mua — Đợt 2026-07

| Thuộc tính | Giá trị |
|---|---|
| Phiên bản | v0.1 (DRAFT) |
| Ngày lập | 2026-07-22 |
| Người lập | Team kỹ thuật |
| Nguồn yêu cầu | Danh sách task khách phòng Thu mua (I. Các phần sẽ update) |
| Trạng thái | Đề xuất — chờ chốt các câu hỏi ở Mục 3 trước khi code |
| Tài liệu liên quan | `Plan_CapNhat_Flow_KhaoSat_v2.md`, `Mapping_Sheet06_TienDoMuaHang.md`, `Requirement_PO_Detail.md`, `Requirement_Module_File.md`, `technical-design.md`, `change-log.md` |

---

## 1. Mục tiêu

Triển khai 9 yêu cầu cập nhật (task 1–8, 10) trên 3 module:

- **Yêu cầu khảo sát (survey_request)** — đổi tên nghiệp vụ thành "Yêu cầu báo giá"; thêm duyệt/đổi trạng thái theo dòng; cho phòng ban yêu cầu đóng phiếu.
- **Yêu cầu mua hàng (purchase_request)** — VAT theo dòng; ẩn NCC theo quyền; thêm cột ngày dự kiến ở list; trang Tiến độ mua hàng.
- **Đơn mua hàng (purchase_order)** — thêm trạng thái "Chưa gửi ĐMH cho KT" + ngày giao chứng từ; sửa bug upload file + trạng thái hồ sơ chứng từ.

---

## 2. Phạm vi & nguyên tắc

- Giữ nguyên **entity key**, **route URL**, **tên bảng DB**, **prefix mã phiếu** — chỉ đổi **nhãn hiển thị** (task 1). Đổi key sẽ kéo theo migration + seed + phân quyền, rủi ro cao, không nằm trong đợt này.
- Mọi thay đổi model đi qua **Alembic migration** (không `ALTER TABLE` tay có tiếng Việt — mojibake). Model mới phải khai báo trong `backend/app/core/all_models.py`.
- Enforcement quyền ở **backend** (`require` + `apply_scope`); `can()` ở frontend chỉ để ẩn/hiện UI.
- Mọi endpoint trả qua envelope `success/error` (`app.core.response`).
- Sau khi sửa role/label entity: `perm_cache_clear` hoặc restart container (cache TTL 60s).

---

## 3. Quyết định đã chốt (2026-07-22)

Các điểm trước đây còn treo, khách đã xác nhận — plan cập nhật theo:

1. **Task 9 — không tồn tại.** Khách đánh số bị sót, không có task 9. Bỏ qua.

2. **Task 4 — VAT: thêm lại.** Xác nhận đảo hướng quyết định cũ (`TASKS.md:32`): YCMH tính lại VAT theo dòng.
   - Công thức: `giá đề xuất đã gồm VAT = giá đề xuất × (1 + VAT%)` (hệ thống tự tính).
   - `thành tiền dòng = SL × giá đề xuất đã gồm VAT`.
   - Phiếu in: đổi cột "Đơn giá đề xuất" → "Giá đề xuất đã gồm VAT", thêm cột VAT%. Layout cuối cùng vẫn cần đối chiếu mẫu in với kế toán khi làm (không chặn code).

3. **Task 5 — Ẩn NCC: gate bằng `supplier.read`.** Đúng: ẩn = trả rỗng 3 trường `suggested_supplier*` ở list, chi tiết, phiếu in khi user không có `supplier.read`.
   - **Thêm việc:** gỡ quyền xem NCC (`supplier.read`) khỏi role **nhân viên cơ bản** trong seed (mặc định nhân viên thường không thấy NCC).

4. **Task 6 — Thêm cột hiển thị, KHÔNG migration.** "Ngày dự kiến mua hàng" chính là `expected_date` đã có sẵn ở cấp dòng (chỉ hiện trong popup chi tiết dòng). Yêu cầu: thêm 1 **cột hiển thị** ngay trên bảng dòng ở ngoài để khỏi phải mở popup. Không thêm trường, không migration. (Khách sẽ gửi hình minh hoạ; xác nhận đúng bảng khi làm.)

5. **Task 7 — Trang Tiến độ giao hàng, ẩn NCC + ẩn khối chi phí giao hàng.** Hiển thị thông tin theo **lần giao** (delivery) cho phòng yêu cầu, nhưng **ẩn cột nhà cung cấp** và **ẩn khối chi phí/đơn vị vận chuyển**. Nguồn cột theo `Mapping_Sheet06_TienDoMuaHang.md` + `sheet_06_tien_do_mua_hang.json`. Bản 1 dùng các cột đã có trong DB; cột 🔴 (`required_date`, `invoice_name`, `fg_code`, `diff_required`...) bổ sung ở bản 2.

6. **Task 10 — Trạng thái hồ sơ chứng từ do người dùng cập nhật tay + hiện ở list.** Không tự suy từ danh sách file (chưa có định nghĩa loại bắt buộc). Thêm **trường trạng thái lưu DB** (3 giá trị: "chưa có chứng từ" / "đã có thông tin chứng từ" / "đã đủ chứng từ"), người dùng chọn tay, và **hiển thị ở cả bảng danh sách ĐMH**.

---

## 4. Chi tiết thay đổi theo task

Ký hiệu độ khó: T (thấp) · TB (trung bình) · C (cao).

### Task 1 — Đổi nhãn "Yêu cầu khảo sát" → "Yêu cầu báo giá" [T]

Chỉ đổi label hiển thị, không đụng key/route/DB.

**Backend:**
- `core/permissions.py:42` — value `"Yêu cầu khảo sát"` → `"Yêu cầu báo giá"`.
- `modules/notification/service.py:159` — value trong DOC_LABEL.
- `modules/notification/service.py:186,189,192,195` — text nội dung thông báo.
- `modules/survey_request/controller.py:198,199,213,214,233,234,246,247` — tiêu đề + nội dung notification (8 chỗ).

**Frontend (nhãn hiển thị):**
- `layouts/AppLayout.tsx:41` — nhãn menu.
- `config/cruds.tsx:297` — title danh sách; `cruds.tsx:474,482` — label "Mã YCKS" → "Mã YCBG".
- `pages/Documents.tsx:16` — nhãn "Yêu cầu khảo sát" → "Yêu cầu báo giá" (giữ **key** `YCKS` ở `SRC_ORDER`/chain nếu backend còn phát key này — chỉ đổi text hiển thị).
- `pages/Reports.tsx:18,371` — tab + tiêu đề biểu đồ.
- `pages/SurveyRequestDetail.tsx:440` — thông báo 404.
- `pages/SurveyDetail.tsx:859,860,865` — nhãn field liên kết + placeholder "Mã YCKS" → "Mã YCBG".
- `pages/Dashboard.tsx:144` — KPI tile.

**Đổi logic sinh mã phiếu (theo yêu cầu):** prefix `YCKS` → **`YCBG`** (Yêu cầu Báo Giá).
- `survey_request/service.py:61` — `prefix = f"YCBG{ddmmyy}"` (mã phiếu `YCBG04072601`).
- `survey_request/service.py:94,162` — mã dòng nội bộ `internal_line_code` `YCKSL{id}` → `YCBGL{id}`.
- **Không migrate mã cũ:** phiếu đã tạo giữ nguyên `YCKS...` (mã là định danh bất biến); chỉ phiếu mới dùng `YCBG...`. Hai prefix cùng tồn tại — `_gen_code` lọc theo prefix nên seq mỗi ngày vẫn đúng.

**Cập nhật test khi đổi prefix:**
- `test/backend/test_codes.py:16,22,24,29,31` — `YCKS_PATTERN` → `^YCBG\d{6}\d{2}$`, assert `startswith("YCBG")`.
- `test/e2e/test_sr_create.py:59`, `test/e2e/helpers.py:253-254`, `test/e2e/test_sr_full_flow.py` — regex/text `YCKS` → `YCBG`.
- Fixture hardcode `code="YCKS-..."` trong `test_process.py`, `test_pipeline.py`, `test_ncc_hiding.py`, `test_auto_assign.py` **không bắt buộc đổi** (chỉ là mã tự đặt trong test, không qua `_gen_code`) — đổi cho đồng bộ nếu muốn.

**Gotcha:** sau khi đổi `permissions.py` cần restart/clear cache (label metadata, an toàn). Không đổi **entity key** `survey_request`, route, tên bảng — chỉ prefix mã + nhãn. Kiểm tra không nơi nào **filter cứng** `code LIKE 'YCKS%'` cho logic nghiệp vụ (chỉ `_gen_code` dùng, đã xử lý).

### Task 2 — Duyệt/đổi trạng thái theo dòng item khảo sát [C]

Hiện `SurveyRequestLine` chỉ có `is_completed` (bool), chưa có trạng thái chuỗi (`survey_request/model.py:48-49`).

**DB / migration:**
- Thêm cột `line_status String(30) default ""` vào `tab_survey_request_line` (giá trị: `""` chưa xác định · `can_khao_sat_lai` · `hoan_thanh`). Giữ `is_completed` đồng bộ (`is_completed = (line_status == "hoan_thanh")`).
- `alembic revision --autogenerate -m "add_line_status_to_survey_request_line"` → review → `upgrade head`.

**Backend:**
- `survey_request/model.py` — thêm cột.
- `survey_request/schema.py` — thêm `line_status` vào Line update schema.
- `survey_request/service.py` — hàm `set_line_status(db, sid, line_id, new_status, user)` + guard phòng ban.
- `survey_request/controller.py` — endpoint `PATCH /{sid}/lines/{line_id}/line-status`, `require("survey_request","write")` + guard trong body.

**Quyền:** chỉ **người YC** hoặc **cùng phòng ban với người YC** được đổi. Bổ sung `_can_edit_own` (controller.py:55-60) thêm nhánh `same_dept`: tra `Employee.department_id` từ `user.employee_id` so với `SurveyRequest.department`. Không cần action mới.

**Gotcha:** `SurveyRequestLine` không có `department` riêng — lấy từ header. Phải import `Employee`.

### Task 3 — Phòng ban yêu cầu đóng phiếu khảo sát [TB]

Hiện `finalize` chỉ cho Admin/QL thu mua (`controller.py:569`, `require approve` + `is_purchaser`).

**Backend:**
- `survey_request/controller.py:569-581` — đổi guard: `require("survey_request","write")` + trong body cho phép `_can_edit_own(...) OR is_purchaser(prof)`.
- `survey_request/service.py:558-563` — xem lại điều kiện trạng thái nguồn cho phép đóng (`survey_done|pr_created`; cân nhắc chặn đóng sớm từ `processing`).

**Gotcha:** không hạ hẳn xuống `write` mà không guard — vì NSTM cũng có `write`. Bắt buộc thêm guard người YC/phòng ban trong controller. `auto_complete_from_pr` (service.py:566) không bị ảnh hưởng.

### Task 4 — VAT theo dòng ở YCMH [TB-C] — ĐÃ CHỐT (Mục 3.2)

Công thức chốt: `giá đề xuất đã gồm VAT = price × (1 + vat_pct/100)`; `thành tiền dòng = qty × giá đã gồm VAT`.

**DB / migration:**
- Thêm `vat_pct Numeric(5,2) default 0` vào `tab_purchase_request_item`. Giá đã gồm VAT **tính tự động** (không cần cột riêng; tính ở service khi trả `_out()` và khi tính tổng).

**Backend:**
- `purchase_request/model.py:52-53` — thêm `vat_pct`.
- `purchase_request/schema.py:4-17` — thêm `vat_pct` vào `PRItemIn`.
- `purchase_request/service.py:217` — công thức tính (theo chốt Mục 3.2); thêm `vat_pct` vào list `_COPY` của `copy_pr` (service.py:273-274).
- `purchase_request/controller.py:62-68` — expose `vat_pct` + `price_incl_vat` trong `_out()`; `controller.py:70-73` — tính lại `vat`/`total` (không còn cứng = 0).

**Frontend:**
- `pages/PurchaseRequestDetail.tsx:898-900` — đổi nhãn "Giá đề xuất" → "Giá đề xuất đã gồm VAT"; thêm input VAT (%); hiển thị giá tự tính.
- `pages/PrintPurchaseRequest.tsx:265,279,296-313` — cột giá + dòng VAT/tổng theo chốt kế toán.

**Gotcha:** đây là đảo hướng quyết định "bỏ VAT" — cần cập nhật `TASKS.md:32` và change-log. Kiểm tra prefill VAT sang ĐMH (`PurchaseRequestDetail.tsx:389`).

### Task 5 — Ẩn NCC đề xuất theo quyền [TB] — ĐÃ CHỐT (Mục 3.3)

**Seed / phân quyền (thêm việc theo chốt):**
- `backend/app/seed.py` (hoặc file seed role) — **gỡ `supplier.read` khỏi role nhân viên cơ bản**. Sau seed lại: `perm_cache_clear` / restart.

**Backend (nguồn enforcement):**
- `purchase_request/controller.py:18-22,25-73` — trong `_out()`: nếu `not user_has_permission(db,user,"supplier","read")` → set rỗng `suggested_supplier`, `suggested_supplier_tax_code`, `suggested_supplier_contact`.
- `purchase_request/controller.py:77-119` — list endpoint lọc tương tự (truyền quyền xuống vòng lặp).

**Frontend (UX):**
- `pages/PrintPurchaseRequest.tsx:317-331` — block "THÔNG TIN NHÀ CUNG CẤP" tự rỗng khi BE trả rỗng (hoặc thêm `can('supplier','read')`).
- `pages/PurchaseRequestDetail.tsx:719-754` — wrap block NCC theo `can('supplier','read')`.

**Gotcha:** ẩn ở BE là bắt buộc (FE chỉ hỗ trợ). List đang serialize không có `user` context per-row — cần truyền cờ quyền vào hàm serialize.

### Task 6 — Thêm cột hiển thị "ngày dự kiến mua hàng" trên bảng dòng [T] — ĐÃ CHỐT (Mục 3.4)

Field đã có: `expected_date` cấp dòng (`purchase_request_item`), nhãn trong popup là **"Thời gian dự kiến có hàng"** (xác nhận qua hình khách). Hiện chỉ hiển thị trong popup "Chi tiết dòng"; yêu cầu đưa ra thành **1 cột** trên bảng **"Danh sách Sản phẩm Yêu cầu"** ở ngoài. Không thêm trường, **không migration**.

- `pages/PurchaseRequestDetail.tsx` — thêm cột "Thời gian dự kiến có hàng" (hoặc gọn: "Dự kiến có hàng") vào bảng dòng, đặt cạnh cột "Trạng thái" hoặc sau "Thành tiền"; hiển thị `it.expected_date` (format DD/MM/YYYY). Chỉ hiển thị read-only ở bảng; vẫn sửa trong popup như cũ. BE đã trả `expected_date` trong `_out()` item nên không đổi backend.

### Task 7 — Trang "Tiến độ mua hàng" [C] — ĐÃ CHỐT hướng (Mục 3.5)

Chưa tồn tại. Nguồn dữ liệu theo `Mapping_Sheet06_TienDoMuaHang.md` + `sheet_06_tien_do_mua_hang.json`: join `tab_purchase_order` → `tab_po_item` → `tab_po_delivery`. Hiển thị theo **lần giao (delivery)**.

**Che dữ liệu cho phòng yêu cầu:** **ẩn cột nhà cung cấp** (`supplier_code/name`) và **ẩn khối chi phí/đơn vị vận chuyển** (`carrier_code`, `shipping_unit_price`, `shipping_amount`, ĐVT VC...). Phòng thu mua xem đầy đủ.

**Backend:**
- Endpoint mới `GET /api/purchase-progress` — join 3 bảng, filter company/bộ phận/tháng/trạng thái, phân trang. Trả cột theo quyền: nếu chỉ có `purchase_request.read` (không có `purchase_order.read`) → loại bỏ NCC + khối vận chuyển khỏi payload.
- Quyền: gate `require` OR giữa `purchase_request.read` và `purchase_order.read` (phòng YC thường chỉ có cái đầu). Áp `apply_scope` để phòng YC chỉ thấy đơn thuộc bộ phận mình.

**Frontend:**
- `pages/PurchaseProgress.tsx` — bảng nhiều cột, cuộn ngang, filter; cột NCC/vận chuyển ẩn theo cờ BE trả về.
- `App.tsx` — route `purchase-progress`.
- `layouts/AppLayout.tsx` — menu (gate quyền).

**Phạm vi bản 1 vs bản 2:** Bản 1 chỉ dùng cột **đã có trong DB** (bỏ tạm các cột 🔴 `required_date`, `invoice_name`, `fg_code`, `diff_required`, `supplier_ready`, `payment_terms`, `product.legal_name`). Bản 2 thêm migration cho các cột này theo Mục C của Mapping. `log`/ghi chú rõ cột nào tạm bỏ để không hiểu nhầm là đã đủ 46 cột.

**Gotcha:** task nặng nhất đợt này; nên làm sau cùng. Có thể tận dụng `sheet_06_tien_do_mua_hang.json` để dựng khung cột.

### Task 8 — Thêm trạng thái "Chưa gửi ĐMH cho KT" + ngày giao chứng từ [TB]

Máy trạng thái hiện: `PROGRESS_ORDER = ["Chưa đặt hàng","Đã đặt hàng","Đã nhận hàng","Đã gửi ĐMH cho KT","Hoàn thành"]` (`service.py:389`). Bước 3 hiện: có `invoice_no` → thẳng "Đã gửi ĐMH cho KT" (`service.py:426`).

**Ý đồ:** tách làm 2 bước — "Đã nhận hàng" → (có `invoice_no`) → **"Chưa gửi ĐMH cho KT"** → (có `document_delivery_date`) → "Đã gửi ĐMH cho KT".

**DB / migration:**
- Thêm `document_delivery_date String(10) default ""` vào `tab_po_item`.

**Backend:**
- `purchase_order/model.py:31` — thêm cột.
- `purchase_order/service.py:389` — chèn `"Chưa gửi ĐMH cho KT"` vào giữa; **re-index** toàn bộ `_STEP_MISSING` (service.py:409) và `_step_ok` (service.py:417-429): `ti==3` → `bool(invoice_no)`, `ti==4` → `bool(document_delivery_date)`.
- `purchase_order/schema.py` — `document_delivery_date` vào `POItemIn`.
- `purchase_order/controller.py` — expose trong `_item()`.

**Frontend:**
- `pages/PurchaseOrderDetail.tsx` — input `type="date"` cho `document_delivery_date` trong popup dòng; thêm vào body `save()`; thêm key màu "Chưa gửi ĐMH cho KT" vào `PG_COLOR`.

**Gotcha:** máy trạng thái forward-only nên dữ liệu cũ an toàn — dòng đang "Đã gửi ĐMH cho KT" giữ nguyên (thành index 4 mới). Dòng "Đã nhận hàng" có `invoice_no` sẽ tự tiến sang "Chưa gửi ĐMH cho KT" ở lần lưu kế. Đồng bộ re-index cả 3 chỗ, nếu không `validate_progress` bỏ sót.

### Task 10 — Fix bug upload + trạng thái hồ sơ chứng từ [C]

**Bug chính (upload "không hiện") — `core/storage.py:38`:** khi R2 được config nhưng `R2_PUBLIC_URL` trống, URL lưu vào DB thiếu host/prefix (`/file/{uuid}_...`) → link không mở được dù file đã lên R2.
- Sửa `storage.py:38` — guard: R2 client tồn tại mà `r2_public_url` trống → fallback local hoặc raise cấu hình lỗi (không lưu URL sai).

**Bug phụ (không upload được khi PO "hoàn thành") — `pages/PurchaseOrderDetail.tsx:158,824,881`:** `deliveryEditable` chỉ cho `approved|partial|received` → khi `completed` nút upload lần giao bị ẩn.
- Tách `deliveryAttachEditable` riêng, cho phép gắn file cả khi `completed` (không mở các field khác như SL nhận/ngày nhận).
- Dùng `deliveryAttachEditable` cho điều kiện hiển thị nút (line 881).

**Trạng thái "hồ sơ chứng từ" — người dùng cập nhật tay, lưu DB, hiện ở list (Mục 3.6):**
- **DB / migration:** thêm `document_status String(30) default "chưa có chứng từ"` vào `tab_purchase_order` (header). 3 giá trị: `"chưa có chứng từ"` · `"đã có thông tin chứng từ"` · `"đã đủ chứng từ"`.
- `purchase_order/model.py:7` — thêm cột.
- `purchase_order/schema.py` — thêm vào PO update schema.
- `purchase_order/controller.py` — expose trong header serialize; endpoint cập nhật (dùng update PO sẵn có hoặc `PATCH /{id}/document-status`), `require("purchase_order","write")`.
- `pages/PurchaseOrderDetail.tsx` — dropdown chọn 3 trạng thái (badge màu); cho phép đổi cả khi PO `completed`.
- `config/cruds.tsx` (PO list) — thêm cột "Hồ sơ chứng từ" hiển thị badge.

**Gotcha:** không auto-suy từ danh sách file (chưa có định nghĩa loại bắt buộc — để mở rộng sau). Nếu đổi `storage.py` fallback local khi thiếu `r2_public_url` thì file không lên R2 — báo người cấu hình. `_check()` (attachment/controller.py:54-65) không chặn theo PO status nên không cần sửa BE cho việc upload khi completed.

---

## 5. Ảnh hưởng DB / migration (tổng hợp)

| # | Bảng | Cột thêm | Task |
|---|---|---|---|
| 1 | `tab_survey_request_line` | `line_status VARCHAR(30) DEFAULT ''` | 2 |
| 2 | `tab_purchase_request_item` | `vat_pct DECIMAL(5,2) DEFAULT 0` | 4 |
| 3 | `tab_po_item` | `document_delivery_date VARCHAR(10) DEFAULT ''` | 8 |
| 4 | `tab_purchase_order` | `document_status VARCHAR(30) DEFAULT 'chưa có chứng từ'` | 10 |
| 5 | `tab_po_item` / `tab_po_delivery` | các cột sheet 6 còn thiếu (bản 2) | 7 |

Task 6 **không** cần migration (dùng `expected_date` sẵn có). Mỗi migration: sửa model → `alembic revision --autogenerate` → **review file** → `upgrade head`. Model mới phải có trong `all_models.py`. Không `ALTER TABLE` tay có tiếng Việt — default `'chưa có chứng từ'` để trong Python model (SQLAlchemy `default=`), không viết thẳng vào SQL migration nếu tránh được mojibake; nếu autogenerate sinh `server_default` tiếng Việt thì đổi sang set default ở tầng ORM.

---

## 6. Thứ tự triển khai đề xuất

- **Đợt A — nhanh + bugfix:** Task 1 (đổi nhãn) · Task 10 phần bugfix upload (storage.py + FE cho phép upload khi completed) · Task 6 (thêm cột hiển thị).
- **Đợt B — luồng khảo sát:** Task 2 (line_status) · Task 3 (phòng ban đóng phiếu) — đi cùng vì chung cơ chế quyền phòng ban.
- **Đợt C — đơn mua hàng:** Task 8 (trạng thái + ngày giao chứng từ) · Task 10 phần trạng thái hồ sơ chứng từ (cột DB + list).
- **Đợt D — nghiệp vụ + màn lớn:** Task 4 (VAT — đối chiếu mẫu in với kế toán khi làm) · Task 5 (ẩn NCC + gỡ quyền role cơ bản) · Task 7 (trang Tiến độ — lớn nhất, làm bản 1 trước).

Lý do: đưa bugfix và việc ít rủi ro lên trước; dồn màn lớn/đối chiếu kế toán về sau để không chặn tiến độ.

---

## 7. Testcase cần bổ sung (`doc/testcase/`)

- Task 2/3: đổi `line_status` bởi người YC / cùng phòng ban (cho phép) vs người ngoài (chặn 403); đóng phiếu bởi phòng ban YC.
- Task 4: công thức giá gồm VAT + tổng phiếu; copy dòng giữ `vat_pct`.
- Task 5: user có/không `supplier.read` → NCC hiện/rỗng ở list, chi tiết, phiếu in; role nhân viên cơ bản sau seed không còn `supplier.read`.
- Task 7: phòng YC (chỉ `purchase_request.read`) → payload không có cột NCC + vận chuyển; phòng thu mua thấy đủ; scope theo bộ phận.
- Task 8: chuỗi trạng thái Đã nhận → (invoice_no) Chưa gửi ĐMH → (document_delivery_date) Đã gửi; dữ liệu cũ không vỡ.
- Task 10: upload khi PO completed; URL file mở được; đổi `document_status` tay và hiển thị đúng ở list.

Backend test tại `test/backend/` (SQLite in-memory); luồng E2E tại `test/e2e/`.

---

## 8. Việc tài liệu kèm theo (khi plan được duyệt)

1. Thêm CR vào `doc/tai-lieu-ky-thuat/change-log.md` (trạng thái `Đề xuất`):

   ```
   | CR-00X | 2026-07-22 | Khách phòng TM | Cập nhật Thu mua đợt 2026-07 (task 1-8,10): rename YCKS→Yêu cầu báo giá, line_status khảo sát, phòng ban đóng phiếu, VAT YCMH, ẩn NCC + gỡ quyền role cơ bản, cột ngày dự kiến, trang Tiến độ giao hàng, trạng thái ĐMH + ngày giao chứng từ, fix upload file + trạng thái hồ sơ chứng từ. | Trung bình-Cao — 4 migration, 3 module, 1 page mới, sửa seed quyền. | Đề xuất | [Plan_CapNhat_ThuMua_2026_07.md](../yeu-cau/Plan_CapNhat_ThuMua_2026_07.md) |
   ```

2. Cập nhật `TASKS.md` (gốc) — thêm nhóm "Cập nhật Thu mua đợt 2026-07" với 9 dòng `- [ ]` (task 1-8, 10).

3. Task 4: sửa dòng `TASKS.md:32` (đảo quyết định "bỏ VAT") + cập nhật `technical-design.md` mục data model. Task 5: cập nhật `doc/phan-quyen/Thiet_Ke_Phan_Quyen.md` (role cơ bản không còn `supplier.read`).
