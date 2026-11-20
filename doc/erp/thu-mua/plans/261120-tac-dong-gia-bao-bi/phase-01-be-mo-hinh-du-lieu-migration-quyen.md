# Phase 01 — BE mô hình dữ liệu, migration, khóa quyền, bộ mã

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 20/11/2026 | planner | Nháp | duoc-CR-784 |

Ưu tiên P2 · 3 giờ · chặn mọi phase sau.

## Bối cảnh
- `tab_product` là bảng VARIANT, nối bằng chuỗi `product_code`, **cấm** cột giá trên nó (§11) → mọi bảng giá là bảng riêng,
  nối bằng `product_code` (không FK, đúng nếp 7 bảng ở §2).
- `tab_purchase_history.price` ghi theo **đồng tiền của dòng ĐMH** (snapshot không chụp `currency` / `exchange_rate`);
  dữ liệu legacy là VNĐ. Sổ giá phải quy về VNĐ lúc ghi.
- `purchase_history` đang gác bằng `product.read` (ai xem sản phẩm cũng xem giá mua). Màn mới chứa giá vốn bao bì nên
  KHÔNG dùng lại khóa đó.

## Thiết kế bảng (một migration duy nhất, gọt tay)

**`tab_product_price_ledger`** — máy ghi, không AuditMixin; có `synced_at`.
| Cột | Kiểu | Ghi chú |
|---|---|---|
| id | BIGINT PK | |
| source_type | SMALLINT | `PriceSourceType`: 1 lịch sử mua hàng, 2 dòng đơn mua hàng |
| source_id | BIGINT | id `tab_purchase_history` (1) / id `tab_po_item` (2) |
| doc_id | BIGINT default 0, index | id ĐMH (0 với legacy) — để đồng bộ theo đơn và mở ngược chứng từ |
| product_code | String(50) | |
| supplier_code | String(50) default "" | |
| company_id | BIGINT default 0 | chừa cho câu hỏi phạm vi theo công ty, không tốn backfill về sau |
| price_date | Date | ngày đơn (`order_date`); dòng ngày hỏng thì bỏ, đếm trong báo cáo script |
| price | Numeric(18,4) | **VNĐ, chưa VAT** = giá dòng x `exchange_rate` |
| vat | Numeric(5,2) | % |
| qty | Numeric(18,3) | |
| unit | String(25) | ĐVT lúc mua — để cảnh báo lệch ĐVT danh mục |
| synced_at | DateTime | |
Ràng buộc: `uq_ppl_source (source_type, source_id)`; index PHỦ `ix_ppl_code_latest (product_code, price_date, doc_id, id, price, company_id)` (đổi từ `ix_ppl_code_date (product_code, price_date, id)` sau đợt đo hiệu năng 20/11/2026, xem phase 04 mục Hiệu năng).

**`tab_product_price_quote`** — AuditMixin. `product_code` S50, `supplier_code` S50 default "", `price` N(18,4) VNĐ chưa VAT,
`vat` N(5,2), `valid_from` Date, `note` S500. Index `ix_ppq_code_from (product_code, valid_from, id)`.

**`tab_product_price_limit`** — AuditMixin. `product_code` S50 **unique**, `floor_price` N(18,4) NULL, `ceiling_price`
N(18,4) NULL, `note` S500. Bảng riêng, không gắn vào báo giá: ngưỡng là **một giá trị mỗi mã**, báo giá có nhiều dòng theo
thời gian — gắn vào báo giá thì không biết dòng nào giữ ngưỡng, và xóa báo giá là mất ngưỡng.

**`tab_packaging_bom`** — AuditMixin. `hh_code` S50 **unique**, `hh_name` S255, `legal_name` S255, `bottle_code`,
`cap_code`, `label_code`, `carton_label_code`, `carton_code` (S50 default ""), `carton_qty` Integer default 0 (0 = chưa
có). Index đơn trên 5 cột mã thành phần (tra "sản phẩm nào dùng mã X").

### Vì sao báo giá không là nguồn 3 của sổ giá
Sổ giá là **giá đã giao dịch** (min/max, số lần mua, 2 lần gần nhất). Báo giá là giá **dự kiến**; trộn vào thì min/max và
"lần mua gần nhất" sai nghĩa, và công thức cũ/mới phải tách nó ra lại. Một sự thật một chỗ: báo giá ở bảng của nó.
Số 3 để trống, cấp sau nếu có nguồn giao dịch mới (vd nạp sổ chi tiết mua hàng MISA — câu hỏi Q1).

## Bộ mã (R2) — tệp mới `backend/app/core/packaging_price_codes.py` (thuần stdlib)
- `PriceSourceType` 1 PURCHASE_HISTORY "Lịch sử mua hàng", 2 PO_LINE "Dòng đơn mua hàng".
- `PackagingRole` 1 BOTTLE Chai, 2 CAP Nắp, 3 LABEL Nhãn, 4 CARTON_LABEL Nhãn thùng, 5 CARTON Thùng.
- `CostTrend` 1 UP Tăng, 2 DOWN Giảm, 3 SAME Không đổi, 4 NO_PRICE Chưa có giá.
- `CostWarning` 1 thiếu giá chai, 2 không có mã thành phần, 3 thiếu giá thành phần, 4 thiếu quy cách thùng,
  5 ĐVT mua khác ĐVT danh mục, 6 dưới ngưỡng sàn, 7 vượt ngưỡng trần.
`register(...)` từng bộ; thêm dòng import vào `app/core/code_sets.py`; chạy `backend/scripts/gen_status_ts.py`.

## Khóa quyền `packaging_cost` ("Giá bao bì") — bảy sổ theo skill `them-entity-moi`
1. `core/permissions.py`: `ENTITIES`, `ENTITY_LABELS`, thêm vào `SENSITIVE_PROCUREMENT_ENTITIES` (giá vốn bao bì).
2. `core/scoping.py`: `SCOPE_FIELDS["packaging_cost"]` khai cột `company_id` của **sổ giá** (Q4 đã chốt: phạm vi theo pháp
   nhân; `company` = pháp nhân của mình, `all` = mọi pháp nhân). Định mức, báo giá, ngưỡng là danh mục dùng chung, không lọc
   theo pháp nhân. Giá cũ / mới / min / max chỉ tính trên các dòng sổ giá người xem được thấy.
3. `core/entity_models.py`: khai `packaging_cost` → `ProductPriceLedger`.
4. `seed.py` `STD_ROLES`: admin đủ; vai trò quản lý thu mua `read/create/write/delete/export` phạm vi `all`. Prod tick tay.
5. FE `permission-types.ts` + `permission-groups.ts` (nhóm Thu mua) — làm ở phase 05 nhưng **cùng commit** với phase 01
   kẻo `test_dong_bo_giao_dien_v2.py` đỏ.
6. `core/action_catalog.py`: không có mã hành động mới ngoài CRUD chuẩn (nếu thêm `import` thì khai).
7. `test_canh_do_dai_o_chu_cr538.py`: thêm 2 module mới vào `MODULES` + `TARGETS` (làm ở phase 03 khi có schema ghi).

## Tệp
- Tạo: `backend/app/modules/product_price/{__init__,model}.py` (ledger, quote, limit) · `backend/app/modules/packaging_cost/{__init__,model}.py` (BOM) ·
  `backend/app/core/packaging_price_codes.py` · `backend/migrations/versions/<rev>_tac_dong_gia_bao_bi.py`.
- Sửa: `core/all_models.py`, `core/code_sets.py`, `core/permissions.py`, `core/scoping.py`, `app/seed.py`,
  `test/backend/test_pham_vi_khai_du_b07.py` (hai số đếm +1), `frontend-v2/src/core/authorization/permission-types.ts`,
  `frontend-v2/src/modules/system/config/permission-groups.ts`, tệp TS sinh từ `gen_status_ts.py`.

## Các bước
1. Viết model; khai `all_models.py`.
2. `alembic revision --autogenerate`, **gọt về đúng 4 bảng + index** (repo trôi ~650 dòng); `down_revision` = head lúc viết
   (hôm nay `mrg761a`, kiểm lại `alembic heads` ngay trước commit, hai đầu thì thêm migration gộp).
3. Bộ mã + code_sets + gen TS. 4. Bảy sổ quyền. 5. `upgrade` → `downgrade -1` → `upgrade` trên local.

## Kiểm xong
- Cụm 6 bài canh của `them-entity-moi` xanh; `alembic heads` một đầu; downgrade sạch.
- `/meta/statuses` có 4 bộ mã mới; typecheck v2 0 lỗi.

## Rủi ro
| Rủi ro | Khả năng x Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Migration cuốn theo trôi dạt | Cao x Cao | Gọt tay, soát diff chỉ còn 4 `create_table` + index |
| Hai đầu alembic vì CR khác cùng lúc | TB x TB | Kiểm `heads` trước commit, migration gộp |
| Quên một sổ quyền | TB x TB | Chạy đúng cụm bài canh, cùng commit FE + BE |

## Đã chốt (người chủ, 20/11/2026)
- **Q1** Chưa nạp sổ MISA; đợt 1 chỉ dùng lịch sử mua + dòng ĐMH của ERP. Số nguồn 3 để trống cho đợt sau. Số trên ERP được
  phép lệch bản mẫu (ghi rõ trong HDSD).
- **Q2** Báo giá có `valid_from` ở tương lai **tính ngay là giá mới** (mục đích là xem trước tác động khi NCC báo tăng giá).
- **Q4** Khóa quyền mới `packaging_cost`; mặc định admin + trưởng phòng thu mua, người khác tick sau. Phạm vi theo pháp nhân
  (cột `company_id`).
- **Q8** Dòng ĐMH vào sổ giá từ trạng thái **đã duyệt** (giống đồng bộ YCMH).

## Câu hỏi còn treo
- **Q3** ĐVT: nhãn / thùng có mua theo kg, cuộn, nghìn cái không? Công thức coi giá là **theo cái**; lệch ĐVT chỉ cảnh báo,
  chưa quy đổi. Cần hệ số quy đổi không?
- **Q5** Lịch sử legacy có ngày **ở tương lai** (local max 03/12/2026) do sửa ngày tự suy — loại dòng `price_date > hôm nay`
  khỏi "lần mua gần nhất", hay sửa dữ liệu gốc?
- **Q6** Dữ liệu `sp` trong bản mẫu đúng 1000 dòng (nghi bị cắt), `ma_thung` rỗng cả 1000 dòng, nhãn thùng chỉ 104 dòng →
  CP/thùng đang thiếu phần thùng. Cần tệp `DATA_CHAI.xlsx` thật (máy này không có) và xác nhận cột mã thùng.
- **Q7** Định mức có cần nhiều phiên bản theo thời gian (đổi chai cho cùng mã HH) không? Kế hoạch: một dòng mỗi mã HH, lịch
  sử sửa xem qua nhật ký thao tác.
