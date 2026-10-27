# Phase 01 — Nền chung backend

**Ưu tiên:** cao (chặn 02–04) · **Trạng thái:** done (27/10/2026) · **Chủ:** điều phối

## Mục tiêu
Chốt hợp đồng dùng chung để ba nhánh 02 / 03 / 04 làm song song không đụng tệp nhau.

## Việc
1. `core/report_keys.py`: thêm `LABOR_CONTRACT = 17` («Hợp đồng lao động», «Nhân sự»), `HR_PROFILE_GAPS = 18` («Hồ sơ & tài khoản còn thiếu», «Nhân sự»); chạy `scripts/gen_status_ts.py`.
2. `modules/report/procurement_summary_rows.py`: thêm `valid_department_id(raw)` cạnh `valid_company_id` (rỗng / `all` → None, không phải số → 422).
3. `core/report_drilldown.py` (mới): hợp đồng «bấm số ra danh sách» — xem dưới.
4. `core/report_cache.py`: thêm 2 đường `/summary` mới vào allowlist.

## Hợp đồng chung (các phase sau PHẢI theo)

### Lọc phòng ban
- Tham số `department_id` (số). Lọc SAU `apply_scope`, chỉ thu hẹp. Báo cáo nào lọc theo cột nào ghi ở phase của báo cáo đó.
- Giao diện gửi khi người xem chọn phòng; `all` / rỗng = không lọc.

### «Bấm số ra danh sách người» (drill-down)
- Đường: `GET <gốc>/summary/rows` — cùng router, cùng `require(entity, 'read')`, cùng `require_report(key)` với `/summary`.
- Tham số: mọi tham số của `/summary` + `metric` (bắt buộc) + `group_by`, `group_key` (tùy chọn; `group_key=""` = nhóm «(Chưa gắn)»; `__other__` → 422).
- `metric` không nằm trong danh sách hỗ trợ → 422.
- Trả (`success(data)`):
```json
{"metric": {"key": "expiring_30", "label": "Sắp hết hạn 30 ngày"},
 "columns": [{"key": "employee_code", "label": "Mã NV", "kind": "text"}],
 "rows": [{"employee_code": "NSU001", "...": "...", "link": "/hr/employees/12?tab=labor-contracts"}],
 "total": 12, "truncated": false}
```
  `kind` ∈ `text | date | int | days | money`. `link` tùy chọn (đường giao diện v2). Trần `ROWS_LIMIT = 500`, quá trần → `truncated: true`, `total` vẫn là số thật.
- `/summary` báo cho giao diện biết chỉ số nào bấm được: `meta.drilldown_metrics: string[]`.
- Danh sách KHÔNG trả giá trị trường nhạy cảm (`employee/sensitive.py`), trừ lương ở B1 (đã chốt).

### Helper ở `core/report_drilldown.py`
- `ROWS_LIMIT = 500`; `Col(key, label, kind="text")`.
- `parse_rows_params(params, allowed: dict[str, str]) -> (metric, group_by, group_key)` — `allowed` = `{metric_key: nhãn}`.
- `filter_group(rows, dim: DimensionSpec | None, group_key)` — giữ hàng mà `dim.key_of(row)` có khóa trùng (`""` ↔ khóa rỗng / 0).
- `rows_response(metric_key, label, columns, rows) -> dict` — cắt trần, đếm `total`.

## Thành công khi
- `python -c "import app.main"` chạy; `gen_status_ts.py` sinh lại tệp TS có khóa 17, 18.
- Bài kiểm nhỏ cho `parse_rows_params` / `filter_group` / `rows_response`.
