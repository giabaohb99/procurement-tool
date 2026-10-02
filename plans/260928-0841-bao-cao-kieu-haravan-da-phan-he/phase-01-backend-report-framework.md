# Phase 01 — Khung backend báo cáo (kỳ · so sánh · gom nhóm · Excel · thời gian duyệt)

## Context links
- Khuôn gom Python: `backend/app/modules/report/service.py:501` (`compute_pr_lines_summary`)
- Excel: `backend/app/core/export_xlsx.py` (`Col`, `xlsx_response`, `VN_OFFSET`)
- Scope: `backend/app/core/scoping.py` (`apply_scope` :782, `scope_condition` :748), `core/auth.py` (`require` :291, `get_perm_profile` :166)
- Duyệt: `backend/app/modules/approval/instance_model.py` (instance/task + hằng số)
- Mẫu đăng ký router trước router chính: `backend/app/main.py` (document_search_router trước document_router)

## Overview
- Priority: P1 (chặn mọi phase sau) · Status: pending · Effort: 6h
- Dựng helper dùng chung + hợp đồng JSON chuẩn + khung router rỗng cho P04–P06.

## Key insights
- Mọi `/summary` hiện có gom bằng Python (`(date or "")[:7]`), không dùng `DATE_FORMAT` → giữ nguyên hướng này (SQLite test = MySQL prod). Chỉ LỌC kỳ bằng SQL (so sánh `>=`/`<`, chạy cả hai DB).
- Ngày lưu 3 kiểu: chuỗi `YYYY-MM-DD`/ISO (`order_date`, `request_date`, `start_time`, `approved_at`, `due_date` của work), `Date` (`from_date`, `hire_date`), `DateTime` UTC (`created_at`, `submitted_at`, `completed_at`, `started_at`). Container chạy UTC → `created_at` phải +7h trước khi lấy ngày, và cận lọc SQL phải −7h.
- Không có so sánh kỳ ở đâu cả → mới hoàn toàn.
- Excel báo cáo hiện gác bằng `require(entity,'export')` (vd `/api/reports/export`) → giữ luật đó.
- Thời gian duyệt: task tuần tự tạo sẵn ở WAITING nên `created_at` phóng đại thời gian chờ; task CANCELLED không có `decided_at`.

## Requirements
Chức năng:
- `parse_period(query_params)` → `Period(date_from, date_to, compare_mode, compare_from, compare_to, granularity)`.
  - Mặc định (thiếu tham số): 30 ngày qua, compare=`previous`.
  - `compare=previous`: cùng số ngày ngay trước; `compare=year`: lùi 1 năm (29/02 → 28/02); `none`.
  - Độ hạt TỰ ĐỘNG: ≤31 ngày → `day`; ≤92 → `week` (tuần bắt đầu thứ Hai, cắt theo biên kỳ); còn lại → `month`.
  - Chặn: định dạng sai, `to < from`, khoảng > 1096 ngày → 422 qua phong bì chuẩn.
- `bucket_axis(from, to, gran)` → danh sách `{key, label}` ĐỦ mốc (mốc rỗng = 0).
- `to_local_date(value)` nhận `str | date | datetime(UTC)` → `date` giờ VN hoặc `None`.
- `range_filter(col, kind, d_from, d_to)` với `kind ∈ {'str','date','datetime_utc'}` → điều kiện SQL cận nửa mở.
- `aggregate(rows, spec, period, group_by)` — `spec` khai báo: `date_of(row)`, `metrics` (thành phần CỘNG ĐƯỢC + `distinct`), `derived` (tỷ lệ/trung bình tính sau khi cộng: `num/den*scale`), `dimensions` (`key_of(row) -> list[(key,label)]` — cho phép nhiều giá trị), `breakdowns` tùy chọn.
- `build_report(fetch, spec, period, group_by, snapshot=None)` gọi `fetch(from,to)` cho kỳ này và kỳ so sánh, trả hợp đồng chuẩn (dưới). `snapshot(to)` tùy chọn cho chỉ số "tại thời điểm" (đang mở, quá hạn, định biên).
- `report_xlsx(filename, data, spec)` → dòng `Tổng` đầu tiên + mỗi nhóm; cột: chiều · mỗi chỉ số · (nếu có so sánh) kỳ so sánh + `±%`. Dùng lại `xlsx_response`.
- `approval/report_turnaround.py`: `turnaround(db, entity, entity_ids_subq, d_from, d_to)` → theo phiên (`started_at→finished_at`) và theo bước (mốc bắt đầu = max(`decided_at` bước trước) hoặc `started_at`; kết thúc = `decided_at`; bỏ CANCELLED/SKIPPED); chiều: người duyệt (`assignee_employee_id`), bước (`node_name`), loại chứng từ; tỷ lệ bước quá hạn (`decided_at > due_at`).
- Router rỗng (`APIRouter(prefix=...)`) cho P04–P06, đăng ký trong `main.py` TRƯỚC router chính của phân hệ (tránh `/summary` rơi vào `/{id}` → 422).

Phi chức năng: mỗi tệp <200 dòng; không SQL riêng MySQL; 1 lần gọi = tối đa 2 lượt truy vấn nguồn (kỳ này + so sánh) + tra nhãn theo lô (không N+1).

## Architecture — hợp đồng JSON chuẩn (phong bì `success`)
```json
{
  "period": {"date_from","date_to","compare_from","compare_to","compare","granularity"},
  "meta": {"metrics":[{"key","label","kind":"int|money|days|hours|percent","good":"up|down|null"}],
           "dimensions":[{"key","label"}], "group_by":"department"},
  "totals": {"current":{...}, "compare":{...}|null},
  "trend":  [{"key","label","current":{...},"compare":{...}|null}],
  "groups": [{"key","label","current":{...},"compare":{...}|null}],
  "breakdowns": {"by_status":[{"key","label","value"}], ...},
  "notes": ["Có 12 hồ sơ nghỉ việc chưa có ngày nghỉ — không tính vào biến động"]
}
```
- `trend` ghép theo CHỈ SỐ mốc (mốc i kỳ này ↔ mốc i kỳ so sánh); thiếu mốc → `compare: null`.
- `group_by=none` → bỏ `groups` (trang Tổng quan gọi nhẹ).
- Nhãn mã trạng thái/khóa ngoại do backend điền (`label`) — frontend không tra bảng mã.

## Related code files
Tạo (Python theo quy ước snake_case của repo):
- `backend/app/core/report_period.py` — Period, parse, axis, bucket, range_filter, to_local_date
- `backend/app/core/report_aggregate.py` — MetricSpec/DimensionSpec/ReportSpec, aggregate, build_report
- `backend/app/core/report_export.py` — report_xlsx (dựa `export_xlsx.xlsx_response`)
- `backend/app/modules/approval/report_turnaround.py`
- Router rỗng (mỗi tệp chỉ `router = APIRouter(prefix=..., tags=[...])`), 9 tệp:
  `employee/report_controller.py` (`/api/employees`), `leave/report_controller.py` (`/api/leave-requests`),
  `leave/balance_report_controller.py` (`/api/leave-balances`), `vehicle_booking/report_controller.py`
  (`/api/vehicle-bookings`), `seal_request/report_controller.py` (`/api/seal-requests`),
  `document/report_controller.py` (`/api/documents`), `approval/report_controller.py` (`/api/approvals`),
  `work/report_controller.py` (`/api/work`), `report/summary_controller.py` (`/api/reports`)
- `test/backend/test_bao_cao_khung_ky_so_sanh.py`, `test/backend/test_bao_cao_thoi_gian_duyet.py`
Sửa:
- `backend/app/main.py` — import + `include_router` 9 router rỗng, đặt TRƯỚC router chính tương ứng. Sau P01 không phase nào sửa `main.py` nữa.

## Implementation steps
1. Viết `report_period.py`; test: 10 preset gửi từ frontend (hôm nay…năm trước), 29/02, kỳ 31/32/92/93 ngày đổi độ hạt, tuần cắt biên, UTC 17:30 → ngày VN hôm sau.
2. Viết `report_aggregate.py`: cộng thành phần, `distinct` bằng set rồi `len`, `derived` tính ở mọi cấp (mốc/nhóm/tổng), tổng tính từ HÀNG DUY NHẤT (không cộng nhóm); nhóm sắp theo chỉ số đầu giảm dần, nhãn `(Chưa gắn)` cho khóa 0/rỗng.
3. `report_export.py`: dựng cột từ `meta`, `Col(kind=int|money)`, % làm tròn 1 số lẻ; tên tệp `bao-cao-<slug>-<from>-<to>`.
4. `report_turnaround.py` + test (luồng 2 bước tuần tự, bước 2 chờ tính từ lúc bước 1 quyết).
5. Tạo 9 router rỗng + đăng ký `main.py`; kiểm `docker compose exec -T api python -c "import app.main"`.
6. Chạy đúng 2 tệp test mới.

## Todo
- [ ] report_period.py + test
- [ ] report_aggregate.py + test (tổng distinct, chiều nhiều giá trị)
- [ ] report_export.py + test (dòng Tổng, cột so sánh)
- [ ] approval/report_turnaround.py + test
- [ ] 9 router rỗng + main.py

## Success criteria
- 2 tệp test mới xanh; `import app.main` không lỗi; OpenAPI chưa có route mới (router rỗng).
- `aggregate` cho cùng dữ liệu ra cùng kết quả dù chiều nhiều giá trị (tổng ≠ Σ nhóm được test khẳng định).

## Risk assessment
| Rủi ro | Khả năng×Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Lệch ngày do UTC | Cao×TB | `to_local_date` + cận −7h, test biên 17:00 UTC |
| Dữ liệu lớn kéo cả kỳ vào Python | Thấp×TB (20–100 user) | `with_entities` chỉ cột cần; trần 1096 ngày |
| Route `/summary` bị `/{id}` nuốt | TB×Cao | router riêng đăng ký trước; test gọi thật qua TestClient |

## Security considerations
- Khung KHÔNG tự scope — mỗi `fetch` phải nhận truy vấn đã scope; docstring ghi rõ, review P04–P06 soát.
- Excel đi route riêng có `require(entity,'export')`.

## Next steps
P02 dùng hợp đồng JSON này (có thể bắt đầu ngay khi mục Architecture chốt).
