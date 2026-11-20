# Phase 04 — BE API tác động giá, bảng giá VTBB, xuất Excel

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 20/11/2026 | planner | Nháp | duoc-CR-784 |

Ưu tiên P1 · 6 giờ · cần 01, 03 (bảng BOM / quote / limit). Hợp đồng dưới đây là **khóa** cho phase 05.

## Phạm vi đợt này (so với các tab của bản mẫu)
| Tab bản mẫu | Đợt này | Lý do |
|---|---|---|
| Tác động (chọn mã, giá giả định, KPI) | CÓ | giá trị chính của tính năng |
| Bảng giá VTBB (cũ/mới/chênh/số SP dùng, nút Báo giá) | CÓ | cửa vào báo giá + ngưỡng |
| Báo giá, Định mức | CÓ (phase 03) | dữ liệu nền |
| Lịch sử mua theo mã / theo SP, 5 lần gần nhất, Tổng hợp | ĐỢT SAU (phase 07) | đọc lại cùng dịch vụ giá; màn Lịch sử mua hàng hiện có đã xem được từng lần mua |

## Dịch vụ (thuần, không phụ thuộc HTTP)
- `product_price/price_state_service.py::get_price_states(db, codes: set[str] | None, as_of, date_from, date_to, scope_cond,
  also, new_only, stats_codes) -> dict[str, PriceState]` — **tối đa 5 truy vấn** (4 khi mọi mã cùng một tầng), không phụ thuộc số mã:
  1. sổ giá, MỘT câu cho mỗi tầng (`product_price/latest_priced_query.py`, **không hàm cửa sổ** — xem "Hiệu năng"): số gộp theo mã
     (`COUNT(*)` mọi dòng kể cả giá 0, `MAX(price_date)`, `MIN/MAX(price)` với `price > 0` trong `[date_from, date_to]` — khoảng ngày
     CHỈ áp cho min/max) + hai lần mua `price > 0` gần nhất (ngày, `doc_id`, id giảm). Tầng nhẹ (`stats_codes` không phủ mã đó, hoặc
     `new_only`) bỏ số gộp;
  2. báo giá mới nhất theo mã, **kể cả `valid_from` ở tương lai** (Q2 đã chốt 20/11: báo giá sắp áp dụng tính ngay là giá mới
     để xem trước tác động), `ROW_NUMBER() ... ORDER BY valid_from DESC, id DESC`, `rn = 1`;
  3. ngưỡng theo mã (bỏ qua khi `new_only`); 4. `tab_product` (tên, `item_group`, ĐVT).
  `PriceState`: `old, new, p1{price,date,supplier_code,unit,source_type,doc_id}, p2, quote{price,valid_from,supplier_code},
  purchase_count, last_date, min, max, floor, ceiling, name, group, unit`. Luật cũ/mới ở `plan.md`.
- `packaging_cost/cost_service.py::compute_product_cost(bom, prices, overrides) -> ProductCost` — hàm THUẦN, chép đúng
  `productRow()`: thiếu giá chai → CP rỗng, trend 4; thành phần khác thiếu giá → tính 0 + cảnh báo; nắp / nhãn không có mã →
  cảnh báo 2 (nhãn thùng / thùng không có mã thì im); có nhãn thùng / thùng mà quy cách 0 → cảnh báo 4, phần đó tính 0;
  chênh > 1e-6 tăng, < -1e-6 giảm. Tính bằng `Decimal`, trả 4 số lẻ. Cảnh báo 5 khi ĐVT `p1.unit` khác ĐVT danh mục
  (so sau khi bỏ dấu + chữ thường), 6/7 khi giá đang dùng ra ngoài ngưỡng.
- `packaging_cost/impact_service.py` — tối đa **6 truy vấn**: (1) BOM có ít nhất một mã đã chọn ở 5 cột (chỉ các cột cần, không cột
  kiểm toán); (2) gom mã thành phần của các dòng đó → `get_price_states` (5; mã ĐÃ CHỌN có đủ min/max, mã thành phần khác chỉ cần
  cũ/mới). "Số SP dùng" mỗi mã đã chọn đếm ngay từ (1). Chi phí MỌI sản phẩm bị ảnh hưởng tính trong bộ nhớ (KPI cần cả tập), rồi
  tìm (`q`) / xếp / cắt trang tại máy chủ và chỉ dựng dòng JSON cho trang được hỏi.
- `packaging_cost/price_list_service.py` — danh sách mã = mã thành phần trong BOM ∪ mã có báo giá ∪ (tùy chọn
  `scope=all`) mọi mã trong sổ giá. Lọc / **xếp tại máy chủ** theo khóa trắng, rồi phân trang; ô trống xuống cuối, khóa phụ mã (luật §8).
  Xếp theo cột danh mục (`code, name, group, unit`, `scope=bom`, không `breach_only`) = ĐƯỜNG NHANH: lọc + xếp + cắt trang trên khung
  danh mục rồi mới tính giá cho mã của trang. Xếp theo số (chênh, min, max…), `breach_only`, `scope=all` buộc tính giá cả tập rồi mới xếp.

## Hợp đồng API (prefix `/api/packaging-cost`, tag `packaging-cost`)
| Phương thức · đường | Quyền | Vào | Ra (`data`) |
|---|---|---|---|
| `POST /impact` | `packaging_cost.read` | `{codes: str[1..500], assumed_prices?: {code: number>=0}, date_from?, date_to?, page=1, page_size=50 (1..500), sort_by=hh_code, sort_dir=asc, q=""}` | `{selected[], kpis, products[], products_total}` |
| `POST /impact/export` | `packaging_cost.export` | như trên (bỏ qua `page` / `page_size`; vẫn theo `q` + xếp) | tệp xlsx (2 sheet: Mã đã chọn, Sản phẩm bị ảnh hưởng) |
| `GET /price-list` | `packaging_cost.read` | `q, group, scope=bom\|all, breach_only, date_from, date_to, sort_by, sort_dir, page, page_size` | `{items[], total}` |
| `GET /price-list/export` | `packaging_cost.export` | cùng bộ lọc + thứ tự | xlsx |
| `GET /code-options` | `packaging_cost.read` | `q, group` | mã dùng trong BOM kèm `{code, name, group, usage, new}` cho ô chọn nhiều (trả đủ, ~1.500 mã) |

- `selected[]`: `{code, name, group, unit, old, new, assumed, applied, diff, pct, usage, min, max, floor, ceiling, warnings[]}`
  (`applied` = giả định nếu có, không thì `new`).
- `products[]` (CHỈ trang được hỏi, đã lọc `q` + xếp; `products_total` = số dòng sau lọc `q`, `kpis.affected_products` = chưa lọc): `{hh_code, hh_name, legal_name, carton_qty, parts[{role, code, name, old, new, applied, selected}],
  cost_old_bottle, cost_new_bottle, cost_applied_bottle, diff_bottle, pct, cost_old_carton, cost_applied_carton,
  diff_carton, trend, warnings[{kind, role?}]}` — số kèm nhãn qua bộ mã sinh TS, **không** gửi câu tiếng Việt. Khóa `sort_by` cho phép:
  `hh_code, hh_name, carton_qty, cost_old_bottle, cost_applied_bottle, diff_bottle, diff_carton, cost_old_carton, cost_applied_carton,
  pct, trend` (khóa lạ → `hh_code`); ô trống xuống cuối cả hai chiều, khóa phụ `hh_code` tăng dần.
- `kpis`: `{selected_count, selected_by_group{group: n}, assumed_count, affected_products, increased, decreased,
  max_increase_carton, max_increase_bottle}` — đúng 4 thẻ của bản mẫu.
- Lỗi riêng: mã không có trong BOM nào → vẫn 200, `products` rỗng; `codes` rỗng hoặc > 500, giá âm, `date_from > date_to`
  → 422. Hai đường xuất dùng `xlsx_response` + `guard_formula_row` (`core/export_xlsx.py`), `check_row_limit`.
- `POST /impact` là đọc thuần (không ghi nhật ký) nên giao diện được dùng `useQuery`.

## Hiệu năng (luật "API báo cáo phải nhanh nhất") — chốt sau đợt đo 20/11/2026
Đo trên MySQL 8 thật với dữ liệu giả lập ×100 (650 nghìn dòng sổ giá / ~3,5 nghìn mã / 8 pháp nhân, 20 nghìn dòng định mức, 10 nghìn
báo giá). Bản đầu xếp hạng bằng `ROW_NUMBER() OVER (PARTITION BY ...)` rồi lọc `rn <= n`: MySQL không đẩy `rn <= n` xuống nên xếp CẢ sổ
(5 – 20 giây mỗi lần gọi). Cách mới (`product_price/latest_priced_query.py`):
- **Chỉ mục phủ** `ix_ppl_code_latest (product_code, price_date, doc_id, id, price, company_id)` (thay `ix_ppl_code_date`): đúng thứ tự "lần mua
  gần nhất" và có sẵn `price` + `company_id` nên điều kiện giá > 0 / phạm vi pháp nhân đọc ngay trong chỉ mục.
- **MySQL 8**: bảng dẫn = danh sách mã (quét chỉ mục bỏ qua), mỗi mã một lần dò `LATERAL ... ORDER BY ... LIMIT n` lấy n id mới nhất và (nếu cần)
  một lần dò gộp; nối khóa chính lấy chi tiết. **Cách chuẩn** (SQLite của bài kiểm, MariaDB): `thr` = ngày của lần mua thứ n (truy vấn con vô
  hướng) rồi nối `price_date >= thr`. Hai cách cho CÙNG kết quả (bài đối chiếu `PKG784_MYSQL_URL` trong `test_truy_van_gia_moi_nhat_cr784.py`).
- Định mức: 5 chỉ mục một cột GIỮ NGUYÊN (đo: 1 mã dùng `index_merge`, 1 ms; chọn nhiều thì MySQL tự quét bảng 20 nghìn dòng, ~100 ms — nhanh hơn
  UNION 5 truy vấn con ~2×). Báo giá: `ix_ppq_code_from` giữ nguyên (cửa sổ trên 10 nghìn dòng, 40 – 90 ms).
- Bài kiểm đếm truy vấn (`count_queries`): `POST /impact` cùng số truy vấn (<= 6) với 1 hay 30 mã, 10 hay 300 dòng BOM, trang 1 hay trang xa, có hay không `q`
  / xếp; `get_price_states` = 4 (5 khi chia tầng); `GET /price-list` <= 7; `GET /last-prices` = 5.
- **Kết quả đo** (ms, MySQL 8 local trong Docker, nóng, trung vị; "trước" = bản hàm cửa sổ + `ix_ppl_code_date`; ×100 = 650 nghìn dòng sổ
  giá, 20 nghìn dòng định mức, 10 nghìn báo giá, 21,5 nghìn mã trong định mức; ×10 = một phần mười):

  | Việc | Dữ liệu hiện tại (6,5 nghìn dòng) trước → sau | ×10 trước → sau | ×100 trước → sau |
  |---|---|---|---|
  | `impact` 1 mã (chai dùng nhiều nhất) | 18 → 23 | 8 → 7 | 150 → 22 |
  | `impact` 500 mã nhãn, trang 1 | 38 → 45 | 281 → 95 | 5.472 → 234 |
  | `impact` chọn cả 400 chai (20 nghìn SP bị ảnh hưởng) | 68 → 63 | 504 → 226 | 7.884 → 1.389 |
  | `get_price_states` 3 nghìn mã | 124 → 86 | 380 → 152 | 11.256 → 493 |
  | `price-list` mặc định (trang 1, xếp theo mã) | 47 → 17 | 408 → 36 | 19.555 → 195 |
  | `price-list` xếp theo chênh (số) | 47 → 36 | 408 → 185 | 19.555 → 899 |
  | `price-list` `scope=all` | 105 → 87 | 352 → 166 | 11.390 → 817 |
  | `last-prices` n=5 / n=10 | 35 / 35 → 26 / 26 | 1.165 / 713 → 199 / 329 | 22.750 / 15.664 → 599 / 655 |
  | `code-options` | 49 → 29 | 602 → 122 | 12.316 → 640 |

  Chưa đạt mục tiêu ×100: `get_price_states` 3 nghìn mã (đích 300, đạt 493), `price-list` xếp theo số và `scope=all` (đích 800, đạt 899 / 817),
  `impact` chọn cả nhóm chai (20 nghìn SP). Sàn của cách quét hiện tại là đọc ~555 nghìn mục chỉ mục của 3 nghìn mã (~0,4 µs / mục);
  muốn xuống dưới nữa phải thêm bảng tóm tắt "n lần mua gần nhất theo (mã, pháp nhân)" — xem câu hỏi mở của lượt đo.

## Tệp
- Tạo: `product_price/price_state_service.py`, `packaging_cost/{cost_service,impact_service,price_list_service,
  impact_controller,export_columns}.py`, `test/backend/test_tac_dong_gia_bao_bi_cr784.py`,
  `test/backend/test_trang_thai_gia_theo_ma_cr784.py`.
- Sửa: `app/main.py` (đăng ký router).

## Bài kiểm
- Trạng thái giá: có báo giá → mới = báo giá, cũ = p1; báo giá tương lai vẫn là giá mới (Q2); không báo giá → p1/p2; một lần mua →
  cũ = mới; dòng giá 0 bị bỏ nhưng vẫn đếm; cùng ngày → id lớn hơn là gần hơn; min/max theo khoảng ngày.
- Công thức: ba dòng dựng tay lấy từ bản mẫu (vd `HH0417.1` chai `CPT0105` + nắp `NAP0085`, quy cách 40) với số kỳ vọng
  tính theo `productRow()`; thiếu chai; thiếu quy cách có thùng; nhãn thùng chia quy cách; giá giả định đổi `applied`.
- KPI: đếm tăng / giảm / tăng nhiều nhất theo thùng và theo chai đúng bản mẫu.
- Đếm truy vấn như trên; 403 khi thiếu quyền; 422 các ca biên; xuất Excel mở được, ô bắt đầu bằng `=` bị chặn công thức.

## Rủi ro
| Rủi ro | KN x AH | Giảm thiểu |
|---|---|---|
| Hai cách truy vấn (LATERAL của MySQL / chuẩn của SQLite) lệch nhau | Thấp x Cao | Bài đối chiếu từng id trên MySQL thật (`PKG784_MYSQL_URL`) + bài kiểm hình dạng SQL; cách chuẩn chạy trong mọi bài kiểm SQLite |
| Số trên ERP lệch bản mẫu (nguồn khác) | Cao x TB | Ghi rõ trong HDSD; Q1 |
| Chọn cả nhóm chai → hàng nghìn SP | TB x TB | Máy chủ phân trang + tìm + xếp bảng sản phẩm (mỗi trang tối đa 500 dòng); KPI vẫn tính trên cả tập trong bộ nhớ |
| ĐVT lệch làm CP sai | TB x Cao | Cảnh báo 5 hiện rõ từng ô; Q3 |

## Quay lui
Bỏ router — không bảng nào khác phụ thuộc.
