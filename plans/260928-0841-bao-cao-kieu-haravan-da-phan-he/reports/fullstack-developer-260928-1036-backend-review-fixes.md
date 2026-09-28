# Backend fixes — review P01-03 báo cáo kiểu Haravan (28/09/2026)

Nguồn: `reports/code-reviewer-260928-1029-phase-01-03-review.md`. Tất cả Critical/High/Medium đã
xử lý; Low xử lý những cái rẻ (L2·L3·L4·L10·L11 + L1 qua contract), bỏ L5/L6/L7/L8/L9 (xem Concerns).

## Hợp đồng đã đổi (FE đang dựa vào)

- `meta.metrics[i]` LUÔN có `helper: bool`, `snapshot: bool` (áp cho cả metric thường lẫn derived).
  `helper=true`: chỉ số PHỤ (mẫu số/tử số của derived) — FE/Excel bỏ khỏi bảng/cột. `snapshot=true`:
  số THỜI ĐIỂM (vd `debt_remaining`/`debt_overdue`) — chỉ có nghĩa ở `totals`.
- Derived (`on_time_rate`, `avg_amount`...) chia cho mẫu số 0 → **JSON `null`**, ở CẢ BA cấp
  (`totals.current/compare`, `trend[].current/compare`, `groups[].current/compare`).
- `trend[].compare`: dòng của kỳ so sánh được DỜI (offset = `date_from - compare_from` ngày;
  riêng `compare=year` dời đúng 1 năm lịch) rồi gộp lên TRỤC/độ hạt của kỳ NÀY — không còn tự
  tính độ hạt riêng rồi ghép theo chỉ số mốc. `trend` luôn cùng độ dài hai vế.
- `groups`: HỢP khóa hiện diện ở kỳ NÀY **hoặc** kỳ SO SÁNH — khóa chỉ có ở kỳ trước vẫn hiện,
  `current` = 0 (metric thường) / `null` (derived) / vắng khóa (snapshot). Sắp theo `rank_by`
  của kỳ NÀY, giảm dần.

## Theo từng finding

- **H1** (trend lệch độ hạt): `report_compute.trend_on_axis` + `compare_shift` + `build_report`
  dùng CHUNG một `axis` cho cả hai vế. Test: `test_trend_ky_so_sanh_gop_theo_truc_hien_tai_...`.
- **H2** (0/0 → 0 sai): `compute_derived` trả `None` khi mẫu số 0. Test:
  `test_derived_ve_null_khi_mau_so_bang_0_khong_phai_0`.
- **M1** (snapshot hiện 0 ở nhóm/Excel): `MetricSpec.snapshot=True` cho `debt_remaining`/
  `debt_overdue`; `drop_snapshot` bỏ khóa khỏi trend/groups; Excel dùng cột `kind="text"` riêng
  (`_snap_text`) — RỖNG ở dòng nhóm, số có dấu phẩy ở dòng Tổng. Test:
  `test_cong_no_la_snapshot_vang_mat_o_nhom_khong_phai_0`.
- **Finding #3 / spend "(Chưa gắn)"**: `payable_rows` nay tra `Payable.department_id` (bảng
  Phòng ban) → lùi về `PurchaseOrder.department` khi rỗng; NSPT suy từ PO liên quan; PO nhiều
  nhóm hàng → CHIA chi phí theo tỷ trọng giá trị đặt (`_split_by_weight`, dòng cuối nhận phần
  dư để tổng khớp tuyệt đối). Ghi chú cũ ("gộp vào Chưa gắn") đã bỏ, thay bằng mô tả đúng + còn
  1 ghi chú cho ca dư (không có ĐMH). Test: `test_chi_phi_gan_duoc_phong_ban_va_chia_theo_nhom_hang`.
  Live check: spend dàn trải 7 phòng ban thật, chỉ ~6.7% rơi "(Chưa gắn)" (trước đó 100%).
- **M2** (ghi chú sai "Tiến độ dòng vẫn đếm đủ"): chọn sửa GHI CHÚ (đúng hành vi thật — dòng hủy
  bị BỎ ở mọi chỉ số kể cả khi Xem theo Tiến độ dòng, nhóm 'Đã hủy' hiện 0). Test:
  `test_ghi_chu_khop_hanh_vi_that_dong_huy_ve_0_o_moi_cho`.
- **M3** (Tiến độ mua hàng theo order_date thay vì received_date): đảo lại đúng quyết định gốc
  của plan — `purchase_progress/summary_service.py` viết lại theo khuôn `Row.kind` (như
  `procurement_summary_rows.py`): `deliveries/late_deliveries/on_time_deliveries` lọc/gộp theo
  `PODelivery.received_date`; `lines/unreceived_items/under_items/full_items` theo
  `PurchaseOrder.order_date`. Bỏ `wrap_rows`/`ProgRow` cũ, `NOTE` không còn nhắc "Q3.1" (chỉ còn
  trong docstring nội bộ cho dev). Test: `test_lan_giao_theo_ngay_nhan_dong_theo_ngay_dat`.
- **M4** (`/procurement/summary` không áp `report_dept_scope`): áp CÙNG hàm với `/matrix`;
  lọc theo `Row.department` (tên) sau khi Finding #3 đã cho payable rows có tên phòng ban thật.
  Test: `test_scope_phong_ban_ap_dung_nhu_bang_matrix`.
- **M5** (formula injection): fix Ở TẦNG DÙNG CHUNG `export_xlsx.xlsx_response` — chuỗi bắt đầu
  `=+-@`/tab/CR bị ép `cell.data_type = "s"` sau khi gán, áp cho MỌI cột chữ của MỌI màn xuất
  Excel trong repo (không riêng báo cáo). Test:
  `test_xlsx_nhan_nhom_bat_dau_bang_dau_bang_khong_thanh_cong_thuc`.
- **L2** (ngày cực đoan → 500): `report_period.MIN_REPORT_YEAR/MAX_REPORT_YEAR = 2000/2100`,
  chặn ở `_parse_date_param` → 422.
- **L3** (`company_id` không phải số → 500): `procurement_summary_rows.valid_company_id` +
  guard trong `report/service._pr_lines_base_query`. Test:
  `test_company_id_khong_phai_so_nem_422` (cả hai đường).
- **L4** (helper metric vẫn ra cột Excel): `_metric_columns` bỏ `helper=True`.
- **L10** (comment main.py trỏ ghi chú không tồn tại): sửa lại chỉ tới docstring thật.
- **L11** (survey-progress open/late "tính tới hôm nay"): thêm `NOTE` giải thích.
- **L1** (compare-only group biến mất) đã làm thành CONTRACT bắt buộc — `merge_groups_by_key`.
- Bỏ qua (không rẻ / cần quyết định sản phẩm): **L5** (±% tương đối vs điểm %, cần chọn UX),
  **L6/L7/L9** (frontend, agent khác sở hữu), **L8** (survey-report tải hết dòng bất kể kỳ —
  cần refactor lớn hơn "rẻ", để lại cho phase sau).

## Files

**Mới:** `backend/app/core/{report_compute,report_export,report_period,report_aggregate}.py`*,
`backend/app/modules/report/{summary_controller,procurement_summary_service,
procurement_summary_rows,pr_lines_period_service}.py`, `backend/app/modules/purchase_progress/
summary_service.py`, `backend/app/modules/survey_progress/summary_service.py`,
`backend/app/modules/survey/report_summary_service.py`
(*`report_compute.py` mới tinh — tách khỏi `report_aggregate.py` để dưới 200 dòng, không phụ
thuộc runtime vào `report_aggregate.py`, tránh import vòng).

**Sửa:** `backend/app/core/export_xlsx.py` (M5 + percent-None), `backend/app/main.py` (L10),
`backend/app/modules/report/service.py` (L3, `_pr_lines_base_query`), `backend/app/modules/
purchase_progress/controller.py` (M3 fetch), `backend/app/modules/survey_progress/controller.py`
(L11 note).

**Test mới/sửa:** `test/backend/test_bao_cao_khung_gom_nhom_va_xuat.py` (+H1/H2/L1/M5),
`test/backend/test_bao_cao_thu_mua_theo_ky.py` (+M2/M3/M4/Finding3/M1/L3, sửa 4 test cũ thêm
`user`), `test/backend/test_tong_hop_bieu_do_tien_do_khao_sat.py` (đã sửa trước — không đụng
thêm), `test/backend/test_bao_cao_khung_ky_so_sanh.py` (không đổi, vẫn xanh).

Dòng file: `report_period.py` 207 (vượt ~200 khoảng 7 dòng — không tách vì là module gắn kết
chặt, tách sẽ hại đọc hiểu hơn lợi). `purchase_progress/controller.py` (435) và `survey_progress/
controller.py` (473) đã vượt 200 dòng TỪ TRƯỚC (không phải do lần sửa này) — ngoài phạm vi task.

## Test

`docker compose exec -T api python -m pytest test/backend/test_bao_cao_khung_gom_nhom_va_xuat.py
test/backend/test_bao_cao_khung_ky_so_sanh.py test/backend/test_bao_cao_thu_mua_theo_ky.py
test/backend/test_bao_cao_dong_ycmh_tong_hop.py test/backend/test_tong_hop_bieu_do_tien_do_khao_sat.py -q`
→ **79 passed**.

Chạy thêm 16 tệp test khác đụng `export_xlsx`/`report.service`/`purchase_progress` (không phải
5 tệp bắt buộc, nhưng cùng module bị sửa) để soát hồi quy: **272 passed**.

`py_compile` toàn bộ tệp sửa/mới: OK. Import toàn bộ module (bao gồm `app.main`): OK.

## Live check

Đăng nhập `admin/admin` → `GET /api/reports/procurement/summary?preset=this_year&compare=year&
group_by=department`: `spend` dàn trải **7 phòng ban thật** (SX - Ms Ly 350.6tr, Lập trình & IT
2.3tr, Kinh doanh 48.2tr, Sản xuất 49.3tr, Phòng Demo Thu Mua 29.4tr, Nhà máy Dego 18.7tr, KD
ICARE 2.8tr) + `(Chưa gắn)` 35.8tr/537tr (~6.7%, trước đó 100%). `debt_remaining` có ở `totals.
current` nhưng VẮNG ở mọi `groups[].current` (đúng M1). `meta.metrics[].helper/snapshot` đúng cờ.

`GET /api/purchase-progress/summary?preset=this_quarter&compare=previous&group_by=none`: period
`granularity=week`, `trend` dài **14**, **14/14** mốc có `compare` (không null) — hai vế CÙNG
độ dài, đúng yêu cầu.

## Unresolved

- L5 (±% tương đối hay điểm %) cần đại ca chốt UX, chưa làm.
- L8 (survey-report tải hết dòng bất kể kỳ) là vấn đề hiệu năng có sẵn từ trước, không "rẻ" như
  các Low khác — để phase sau.
- `report_period.py` 207 dòng, vượt nhẹ ngưỡng 200 — quyết định không tách (xem Files).

**Status:** DONE
**Summary:** Xử lý hết Critical/High/Medium + Low rẻ của review P01-03; hợp đồng `helper`/
`snapshot`/None-on-zero-denom/trend-align/groups-union đã lên đúng như FE cần; spend theo phòng
ban chạy thật trên live check; 79/79 test 5 tệp mục tiêu xanh, 272 test liên đới khác cũng xanh.
**Concerns:** L5/L8 để lại có chủ đích (cần quyết định sản phẩm / không rẻ). `report_period.py`
vượt 200 dòng ~7 dòng, chấp nhận vì tách sẽ hại đọc hiểu.
