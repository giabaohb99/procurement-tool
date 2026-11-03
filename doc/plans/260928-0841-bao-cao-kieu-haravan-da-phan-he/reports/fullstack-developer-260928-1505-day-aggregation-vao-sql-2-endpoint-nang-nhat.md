# Đẩy CỘNG vào SQL GROUP BY — 2 endpoint báo cáo nặng nhất

## Trạng thái: DONE

Mục tiêu: `/survey-report/summary` (+ `/export`) và `/reports/procurement/summary`
(+ `/export`) nhận HÀNG ĐÃ GOM SẴN từ SQL thay vì hàng thô, output byte-identical.

## 1. Thiết kế mỗi endpoint

### `survey-report/summary` — GOM TOÀN BỘ ở SQL (không có q)

File mới: `backend/app/modules/survey/report_grouped_fetch.py`.

- GROUP BY (ngày hiệu lực, nspt, item_group, line_approve ĐÃ chuẩn hóa) trên MỖI bảng dòng
  (NCC/SP), hai nhánh y hệt `_lines_in_range` cũ (ngày liên hệ trong kỳ / ngày liên hệ rỗng lùi
  về `Survey.received_date`), JOIN với subquery phiếu đã `apply_scope`. `line_approve` chuẩn hóa
  bằng `COALESCE(NULLIF(col,''), 'Chờ duyệt')` NGAY TRONG GROUP BY key. Trả `COUNT(*) AS cnt`.
- `report_summary_service.py`: 4 `MetricSpec.value_of` đổi từ hằng `1` sang `r.get("cnt", 1)` —
  MỘT `ReportSpec` chạy đúng cho CẢ hàng cũ (không có "cnt" → mặc định 1) LẪN hàng gom (có "cnt").
  `distinct_of` không dùng ở spec này nên không vướng giới hạn "không gom được qua GROUP BY".
- 4 bộ lọc trang (kind/item_group/supplier/nspt) chuyển sang SQL WHERE — kind bỏ hẳn bảng dòng
  không khớp; item_group so khớp CHÍNH XÁC; supplier/nspt so khớp CHỨA qua `LOWER()+LIKE` (khớp
  ASCII, giới hạn đã biết: SQLite `lower()` không gập hoa/thường chữ có dấu, MySQL thì có —
  chấp nhận vì NSPT/mã NCC trong dữ liệu thật đa số ASCII, cùng mức rủi ro `.like()` trần đã
  dùng khắp `apply_filters`).
- **`q` (tìm đa trường) LÙI VỀ ĐƯỜNG CŨ** (`service.report_rows_in_range` + `_filter_report_rows`,
  nạp từng dòng) — đúng như plan cho phép: `q` dò 10 cột trải cả header lẫn 2 bảng dòng, dựng lại
  portable y hệt bằng SQL là việc lớn cho một ô tìm phụ. `controller._ranged_report_fetch` chọn
  đường theo `if q:`.
- **Bẫy thứ tự hòa điểm (mới phát hiện, không có trong plan gốc):** `report_aggregate.aggregate()`
  sắp `groups`/`breakdowns` theo hạng rồi dùng THỨ TỰ LẦN ĐẦU XUẤT HIỆN trong `rows` làm tiêu chí
  phụ khi hòa điểm (Python `sort` ổn định). Gộp nhiều dòng thành 1 hàng SQL mà không giữ đúng thứ
  tự đó thì hai nhóm hòa điểm có thể TRÁO CHỖ trong JSON dù tổng số đúng — phá "byte-identical".
  Vá bằng `MIN(line.id)` trong mỗi SQL group, rồi sắp lại (kind NCC trước SP, MIN(id) tăng dần) —
  đúng CHỨNG MINH được: dòng gốc luôn là "mọi dòng NCC (theo id) rồi mọi dòng SP (theo id)", nên
  vị trí "lần đầu gặp giá trị X của một chiều" chỉ phụ thuộc kind + id nhỏ nhất, không phụ thuộc
  item_group/nspt/line_approve khác.

### `reports/procurement/summary` — CHỈ gom phần AN TOÀN (số nguyên)

File mới: `backend/app/modules/report/procurement_grouped_rows.py`, thay hàm `po_rows` (đã xóa)
trong `procurement_summary_rows.py`.

- **GOM Ở SQL**: số LẦN GIAO đã nhận + đúng hạn của từng `POItem` — trước đây nạp TOÀN BỘ
  `PODelivery` liên quan rồi đếm bằng 2 dict Python; nay `GROUP BY po_item_id` một lượt
  (`_delivery_agg`), LEFT JOIN vào truy vấn chính. Số nguyên, cộng ở SQL hay Python luôn khớp
  tuyệt đối — không rủi ro.
- **CỐ Ý GIỮ Ở MỨC DÒNG** (không GROUP BY thêm), có ghi trong docstring:
  - `order_value`: `report_service.order_amount_of` cộng bằng **float Python từng dòng** (ép
    `float()` từng số hạng rồi nhân/cộng). Thử cộng bằng SQL SUM trên cột DECIMAL rồi đổi sang
    float một lần ở cuối cho **kết quả khác bit cuối** với cộng float-per-item của Python (hai
    thuật toán khác nhau về mặt số học dấu phẩy động, không có cách nào đảm bảo trùng tuyệt đối
    trừ khi lặp Python đúng thứ tự cũ) — mà `report_bench.py` so khớp JSON bằng `!=` tuyệt đối,
    không làm tròn. Giữ công thức ở Python, chỉ đổi CÁCH LẤY DỮ LIỆU (1 JOIN gọn thay 3 truy vấn
    ORM rời + dict nối tay), và `ORDER BY POItem.id` để giữ ĐÚNG thứ tự cộng dồn cũ (cộng float
    không kết hợp được, đổi thứ tự có thể đổi bit cuối của tổng).
  - `po_count`: `distinct_of=lambda r: r.po_id` của `report_aggregate` — khung đếm phân biệt
    THEO TỪNG BUCKET (một ĐMH nhiều nhóm hàng phải đếm 1 Ở MỖI nhóm hàng), nên hàng phải giữ
    `po_id` thật ở mức DÒNG; gộp theo PO sẽ làm sai đếm khi group_by=department/company (PO có
    nhiều item cùng phòng ban thì bị đếm NHIỀU LẦN nếu tổng hợp count() rồi cộng lại qua GROUP BY
    thô — bài toán kinh điển "distinct không cộng được qua GROUP BY lại").
  - `payable_rows` (chi phí) **không đổi** — `_split_by_weight` chia tỷ trọng có "dòng cuối nhận
    phần dư" (làm tròn phụ thuộc THỨ TỰ dict), không portable hóa an toàn bằng SQL trong ngân
    sách của việc này; bảng nguồn (182 → 9.100 ở 50x) nhỏ hơn hẳn POItem×lần giao, không phải
    điểm nghẽn theo load test gốc.
- Xóa `po_rows` (hàm cũ, ~40 dòng) khỏi `procurement_summary_rows.py` cùng 2 hằng cột chỉ nó
  dùng (`_PO_COLS`, `_DELIVERY_COLS`) — tránh 2 cách lấy cùng dữ liệu tồn tại song song (DRY).

## 2. Bảng trước/sau — 1×/10×/50× (median/max ms, rows SQL, peak RSS)

Đo bằng CSDL throwaway `procurement-bench-db` (mysql:8.0, mạng `procurement-tool_default`,
dump từ CSDL thật qua `mysqldump` bằng creds `app` CHỈ ĐỌC — không viết vào CSDL thật). Nhân
7 bảng nuôi 2 endpoint này (KHÔNG nhân `tab_purchase_request*`/`tab_survey_request*` — không
liên quan 2 endpoint đang tối ưu) lên đúng 10.00× và 50.00× (id offset `k*10.000.000`, mã
UNIQUE gắn hậu tố `-Lk`, FK offset khi khác 0 — cùng luật `id=0 là giá trị thật`). Đo bằng
`TestClient` trong tiến trình `docker exec` riêng, `get_db` trỏ sang CSDL throwaway, đăng nhập
`admin`/`admin`, 5 lần lặp (bỏ 1 lần khởi động), `rows` = tổng `cursor.rowcount` mọi câu SQL.

Số liệu TRƯỚC lấy từ báo cáo load-test gốc (`fullstack-developer-260928-1437-...md`), MySQL
cùng máy, cùng phương pháp.

### `/api/survey-report/summary?group_by=line_approve` — endpoint từng OOM-crash

| Preset | TRƯỚC 1× | SAU 1× | TRƯỚC 10× | SAU 10× | TRƯỚC 50× | SAU 50× |
|---|---|---|---|---|---|---|
| this_month/previous | 11ms (15r) | **10.4ms (6r)** | 15ms (132r) | **12.1ms (6r)** | 58ms (652r) | **13.5ms (6r)** |
| this_quarter/previous | 52ms (1.211r) | **15.0ms (330r)** | 429ms (12.092r) | **34.2ms (330r)** | 3.150ms (60.452r) | **210ms (330r)** |
| this_year/year | 314ms (6.702r) | **34.9ms (1.468r)** | 2.552ms (67.002r) | **103ms (1.468r)** | 18.399ms (335.002r) | **515ms (1.468r)** |
| custom 2024–2026/none | 273ms (7.885r) | **33.5ms (1.824r)** | 3.122ms (78.832r) | **90ms (1.824r)** | **CRASH (OOM)** | **413ms (1.824r)** |

Peak RSS tiến trình đo (toàn bộ 8 case × 5 lần lặp, cả 2 endpoint): 1×=235MB, 10×=244MB,
50×=**285MB** — so với trước đây (chỉ riêng `survey-report` this_year 50× đã giữ 335.002 bản
ghi ORM trong RAM, và case custom giết cả container 2GB). **Hàng SQL trả về không đổi giữa
10× và 50×** (330/1.468/1.824 ở mọi mức) — đúng lý thuyết: số nhóm (ngày×nspt×nhóm hàng×kết
quả duyệt) bị chặn bởi SỐ NGÀY TRONG KỲ, không phải số dòng khảo sát; nhân dữ liệu chỉ làm
`cnt` mỗi nhóm to lên, không sinh thêm nhóm mới.

**Cải thiện median @50×**: this_quarter 3.150→210ms (**15×**), this_year 18.399→515ms
(**35,7×**), custom **crash→413ms** (hết hẳn nguy cơ OOM).

### `/api/reports/procurement/summary?group_by=department`

| Preset | TRƯỚC 1× | SAU 1× | TRƯỚC 10× | SAU 10× | TRƯỚC 50× | SAU 50× |
|---|---|---|---|---|---|---|
| this_month/previous | 16ms (592r) | 17.8ms (584r) | 63ms (5.623r) | 59.0ms (5.543r) | 391ms (27.983r) | **338ms (27.583r)** |
| this_quarter/previous | 26ms (1.166r) | 23.6ms (1.023r) | 226ms (11.363r) | 143.5ms (9.933r) | 1.195ms (56.683r) | **778ms (49.533r)** |
| this_year/year | 25ms (1.026r) | 22.0ms (840r) | 216ms (9.963r) | 116.7ms (8.103r) | 1.247ms (49.683r) | **697ms (40.383r)** |
| custom/none | 24ms (1.026r) | 20.2ms (840r) | 142ms (9.963r) | 117.6ms (8.103r) | 1.063ms (49.683r) | **685ms (40.383r)** |

Peak RSS: đã tính chung với survey-report ở trên (cùng tiến trình đo). **Cải thiện median
@50×**: 14–44% tùy preset (this_year nhanh nhất, 44%) — khiêm tốn hơn nhiều so với
survey-report, ĐÚNG THEO THIẾT KẾ vì `order_value`/`po_count` cố ý GIỮ độ hạt dòng (xem §1);
phần thắng thật sự là bỏ vòng lặp Python đếm `PODelivery` + tránh nạp 3 tập ORM entity rời.

## 3. Kiểm output byte-identical

`docker compose exec -T -w /app api sh -c 'PYTHONPATH=/app python /tmp/report_bench.py after &&
python /tmp/report_bench.py diff'` → **`RESULT: IDENTICAL`** (396 tổ hợp tham số × 3 người
dùng, so khớp CẢ 5 endpoint `/summary`, chạy 2 lần — trước khi thêm test và lần chốt cuối —
đều IDENTICAL). Baseline `/tmp/report_before.json` đã có sẵn từ phiên trước.

## 4. Tests

Lệnh: `docker compose exec -T api python -m pytest <8 tệp yêu cầu> + 2 tệp mới -q`
→ **130 passed** (116 cũ + 14 mới), 0 fail.

Tệp mới:
- `test/backend/test_bao_cao_khao_sat_gom_o_sql.py` (8 bài): so khớp TOÀN BỘ `aggregate()`
  (totals/trend/groups/breakdowns) giữa đường cũ và đường gom SQL — kể cả `line_approve` rỗng
  (chuẩn hóa "Chờ duyệt") và nhánh lùi ngày (contact_date rỗng → received_date); 4 bộ lọc trang
  (kind/item_group/supplier chứa không phân biệt hoa-thường/nspt); phạm vi `apply_scope` (phiếu
  ngoài `base_survey_query` không lọt hàng).
- `test/backend/test_bao_cao_mua_hang_gom_o_sql.py` (6 bài): `order_value` khớp công thức cũ
  (SL×giá×(1+VAT%)×tỷ giá, tỷ giá 0/rỗng → 1); trạng thái ĐMH không thật bị loại; đúng-hạn =
  KHÔNG (diff_promise HOẶC diff_regulated âm); **1 ĐMH nhiều nhóm hàng đếm `po_count`=1 Ở MỖI
  nhóm** (kiểm cả tổng KHÔNG cộng đôi); lọc công ty + hợp nhiều khoảng ngày.

## 5. Dọn dẹp (đã kiểm)

1. `docker rm -f procurement-bench-db` (bản 50×) + `procurement-bench-db-1x` (bản 1× riêng,
   xóa ngay sau khi đo) — cả hai đã xóa, `docker ps -a`/`network ls`/`volume ls` sạch.
2. Xóa `/tmp/procurement-bench` (host) + `/tmp/multiply.py`, `/tmp/measure.py`,
   `/tmp/measure_{1x,10x,50x}.json` (container `api`) — đã xóa.
3. **CSDL thật xác nhận BYTE-IDENTICAL** trước/sau (COUNT chính xác qua creds `app`):
   `tab_survey=2711, tab_survey_supplier_line=53, tab_survey_product_line=5150,
   tab_purchase_order=96, tab_po_item=113, tab_po_delivery=103, tab_payable=182, tab_user=276,
   tab_login_session=330` — khớp cả 9/9 chỉ số trước và sau.
4. Không đổi `test/backend/conftest.py` hay bất kỳ tệp nào ngoài 2 module gom SQL + 2 tệp test
   mới + 3 tệp gọi chúng (`report_summary_service.py`, `controller.py` của survey,
   `procurement_summary_service.py`, `procurement_summary_rows.py` của report).

## 6. File đã sửa/tạo

- Mới: `backend/app/modules/survey/report_grouped_fetch.py` (102 dòng)
- Mới: `backend/app/modules/report/procurement_grouped_rows.py` (85 dòng)
- Sửa: `backend/app/modules/survey/report_summary_service.py` (4 `value_of` → `r.get("cnt",1)`)
- Sửa: `backend/app/modules/survey/controller.py` (+`_ranged_report_fetch` dùng chung 2 route)
- Sửa: `backend/app/modules/report/procurement_summary_service.py` (gọi `grouped_po_rows`)
- Sửa: `backend/app/modules/report/procurement_summary_rows.py` (xóa `po_rows` + 2 hằng cột chết)
- Mới: `test/backend/test_bao_cao_khao_sat_gom_o_sql.py`, `test/backend/test_bao_cao_mua_hang_gom_o_sql.py`

**Status:** DONE
**Summary:** 2 endpoint nặng nhất đẩy CỘNG vào SQL GROUP BY; survey-report (endpoint từng OOM ở
50× custom) nay 13-515ms mọi mức thay vì 58ms-18,4s-CRASH — 15-36× nhanh hơn, hết hẳn nguy cơ
sập container; procurement cải thiện khiêm tốn 14-44% (order_value/po_count cố ý giữ độ hạt
dòng vì lý do float-precision/distinct-count, có ghi rõ trong code + báo cáo). Output JSON
byte-identical qua 396 tổ hợp tham số × 3 người dùng (`RESULT: IDENTICAL`), 130/130 test pass
(116 cũ + 14 mới), CSDL thật xác nhận không đổi, mọi tài nguyên throwaway đã dọn sạch.
**Concerns:** (1) `survey-report`'s `q` filter vẫn lùi về đường cũ (nạp từng dòng) — nếu người
dùng vừa gõ `q` vừa xem kỳ có hàng chục nghìn dòng, ca đó CHƯA được vá (hiếm, vì `q` thường đi
kèm bộ lọc khác thu hẹp kết quả trước). (2) `procurement`'s `order_value`/`po_count` không được
gom nhỏ hơn mức dòng — nếu tương lai ĐMH tăng vọt (hiện 50× chỉ ra 5.650 POItem, còn lâu mới
chạm ngưỡng nguy hiểm như khảo sát), sẽ cần giải pháp khác (có thể: cache ngắn hạn theo tham số,
đã đề xuất ở báo cáo load-test gốc mục "Most effective fixes #2").
