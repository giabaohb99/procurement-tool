# Phase 08 — D1d: Báo cáo «Năng lực theo loại việc» (ReportKey 16) + hợp đồng dữ liệu cho AI chia việc

## Context links
- Đích của đại ca: «phần dữ liệu để AI chia việc đúng người»
- `doc/erp/22-ai-ke-hoach-phan-viec.md` §2.1 (máy tính số, AI viết chữ), §4 (`task_type_stats`, `team_capacity`), §6 (năng lực + tải: quản trị xem; người khác chỉ thấy kết quả đề xuất), §7 A1 (Agent 4, song song D1)
- Cổng B: `backend/app/modules/agent_gateway/controller.py` (`/api/agent-gw/*`, vùng Agent 4)
- Mẫu gác kép: `usage_profile/controller.py`; lớp gác báo cáo: `report_access/guard.py`

## Overview
- P1 · **1,5 ngày** (BE 0,8 · FE 0,7) · **implemented (duoc-CR-657, 20/10/2026)** · sau phase 06, 07; FE sau CR-651 (cùng `modules/report/**`).
- Hàm thống kê `task_type_stats(...)` + báo cáo quản trị khóa **16** + bàn giao hợp đồng cho A1. Công cụ MCP/Trợ lý là việc của Agent 4 (A1) — **không** làm ở đây.

## Key insights
- DRY: báo cáo quản trị và công cụ AI dùng **chung hai hàm** (`task_type_stats`, `current_load`); A1 chỉ bọc lại ở cổng B + MCP với phạm vi phòng ban riêng.
- MySQL 8 không có hàm phân vị → lấy cột cần thiết từ `tab_work_cycle` (1 truy vấn, đã lọc kỳ + phạm vi), tính trung vị/p90/max trong Python. Vài chục nghìn dòng/180 ngày — chấp nhận được.
- Ngưỡng **≥ 5 mẫu** cho số theo người (doc 22 §4) — dưới ngưỡng trả `null` + lý do `BELOW_THRESHOLD` (dùng lại `UnmeasuredReason`).

### Vì sao ReportKey 16 riêng
Năng lực + tải là «dữ liệu năng lực tổng hợp» — doc 22 §6 tách hẳn với «hồ sơ hành vi chi tiết» (khóa 14). Khóa riêng để sau T1 đại ca có thể mở cho trưởng phòng
(phòng mình) mà không mở hồ sơ hành vi. Mặc định chỉ admin.

## Requirements
- Bảng: hàng = người × loại việc (× loại task Dự án), cột: số xong, TB ngày, trung vị, p90, chậm nhất, tỷ lệ làm lại, trễ hạn, sai số ước lượng (thực tế/ước lượng), tải hiện tại.
- Lọc kỳ (mặc định 180 ngày), pháp nhân, phòng ban, loại việc, vai (lập/xử lý). Xuất Excel. Liên kết sang hồ sơ (khóa 14) nếu người xem có khóa đó.

## Architecture
**Hàm** `capability/stats_service.py`:
`task_type_stats(db, *, kinds=None, task_type_ids=None, role=HANDLER, company_id=None, department_ids=None, employee_ids=None, date_from, date_to, group_by=("kind","task_type_id","employee_id"), min_samples=5) -> list[dict]`
→ mỗi nhóm: `n_done, n_cancelled, mean_days, p50_days, p90_days, max_days, rework_rate (= Σrework/n), first_pass_rate (rework=0), late_rate, est_ratio_p50 (actual/estimate, task có cả hai)`, kèm `below_threshold`.
Truy vấn: Q1 dòng `tab_work_cycle` theo `(done_at, kind)` + phạm vi; Q2 tên nhân sự/loại task (1 truy vấn gộp). Tổng ≤ 3.
**API** `capability/controller.py`, `prefix=/api/work-capability`, mọi đường `dependencies=[Depends(require_report(ReportKey.WORK_CAPABILITY))]` + `require("setting","read"|"export")`:
- `GET /summary` (bảng người × loại, phân trang Python) · `GET /summary/export` · `GET /load` (`current_load` của phase 07, cùng bộ lọc).
**Hợp đồng cho A1 (Agent 4)** — tệp `capability/README.md` hoặc mục trong `doc/tai-lieu-ky-thuat/nang-luc-theo-loai-viec.md`: chữ ký 2 hàm, đơn vị (ngày, giờ), ngưỡng mẫu,
và **luật phạm vi**: người gọi tự tính `department_ids` được phép (trưởng phòng: phòng mình + phòng con; quản trị: tất cả) — hàm không tự mở rộng phạm vi.
*Tùy chọn (nếu A1 cần HTTP mà Agent 4 muốn ERP làm sẵn):* `GET /api/agent-gw/capability/stats|load` trong `agent_gateway/controller.py` — chỉ làm khi Agent 4 đồng ý, vì tệp đó thuộc vùng Agent 4.
**Mã** `ReportKey.WORK_CAPABILITY = 16` «Năng lực theo loại việc», nhóm «Quản trị». FE: `report-catalog-system.ts` (key 16, entity `setting`, `sourcePath: appRoutes.system.logs`).
**Tùy chọn mục 3.7 trong hồ sơ** (doc 22 §5): 3 khóa phẳng `cycle_done_count` (count, 0), `rework_per_item` (ratio, −1), `load_open_items` (count, 0) — đọc `tab_work_cycle` + `current_load` lúc dựng snapshot.
Chỉ làm nếu lead muốn trọn «nhóm 3.7» (≈ 0,5 ngày thêm, sửa `usage_profile/metric_catalog.py` sau CR-651).

## Related code files
Tạo BE: `backend/app/modules/capability/{stats_service,stats_export,controller,schema}.py`.
Sửa BE: `core/report_keys.py` (16 + REPORT_META) · `app/main.py` (router) · `test/backend/test_ho_so_lam_viec_ma_so_cr641.py` (khóa lớn nhất).
Sinh lại `statuses.ts`.
Tạo FE: `modules/report/pages/work-capability-report-page.tsx` · `components/work-capability/{work-capability-columns,work-capability-filters,work-load-panel}.tsx` ·
`api/work-capability-api.ts` · `hooks/use-work-capability.ts` · `types/work-capability.ts`.
Sửa FE: `report-catalog-system.ts` · `modules/report/routes.tsx` + nav (`reportKeys: [16]`, Tổng quan thêm 16) · `shared/constants/app-routes.ts` · `query-keys.ts`.

## Implementation steps
1. `ReportKey 16` + sinh TS (sau khi phase 03 đã thêm 15 — tránh tranh số).
2. `stats_service` thuần phần tính (hàm nhận list dòng) + phần truy vấn; test ngưỡng mẫu.
3. Controller 3 đường + xuất Excel; khai `/summary` trước đường tham số.
4. Tài liệu hợp đồng A1; gửi lead chuyển Agent 4.
5. FE trang + bảng `DataTable` + panel tải tức thì + bộ lọc; hiển thị «chưa đủ mẫu» thay số.
6. Gate FE: typecheck, lint, vitest `src/modules/report`.

## Todo
- [x] ReportKey 16 + sinh TS
- [x] stats_service (`stats_math` + `stats_service`) + test ngưỡng
- [x] controller (`/summary`, `/summary/export`, `/load` gác khóa 16) + export Excel (thêm kind `decimal` ở `core/export_xlsx.py`)
- [x] hợp đồng A1: `capability/ai_contract.py` (`suggest_assignees`, `get_capability`) + mục 4 của `doc/tai-lieu-ky-thuat/nang-luc-theo-loai-viec.md`
- [x] trang FE `/report/work-capability` (3 tab: theo loại việc, theo người, tải đang ôm) + dải nhắc
- [ ] (tùy chọn) 3 khóa mục 3.7 — KHÔNG làm (Q14: YAGNI)
- [x] Chốt 20/10: ĐMH `received` = XONG (`cycle_specs`, `po_handling`), dòng `is_estimated` tách riêng, backfill local đã chạy

## Kết quả triển khai (CR-657)
- Không có migration mới (head vẫn `d01merge01`); khóa 16 chỉ là mã + dòng `tab_report_access` cho admin (`ensure_report_access_defaults` chèn lúc seed).
- Lệch so với bản thiết kế: hàm đặt ở `stats_service.fetch_stats/task_type_stats` nhận `StatsFilter` (không phải danh sách tham số rời); `/summary` trả `types[]` + `people[]` cùng lúc, không phân trang (trần 2000 dòng người);
  ngưỡng ≥ 5 áp cả cho dòng theo loại (một người một mình chiếm loại thì số loại = số người đó); không có `n_cancelled` (phiếu hủy không có mốc ngày để lọc kỳ).
- Mốc đo: 3 truy vấn cho `/summary` (4 khi có task có loại việc), `/load` ≤ 10 + tầng xác thực; bài kiểm đếm truy vấn với 5 và 201 người.

## Tests
Backend `test/backend/test_bao_cao_nang_luc_d1.py`: trung vị/p90/max đúng trên mẫu biết trước; nhóm < 5 mẫu ⇒ `null` + `below_threshold`;
lọc vai/loại/phòng ban; **đếm truy vấn** `/summary` ≤ 3, `/load` ≤ 10; gác: thiếu khóa 16 → 403, admin → 200, `/summary/export` cần `setting.export`;
hàm gọi không phạm vi → `[]`.
Vitest: `report-catalog.test.ts` (đã có, tự bắt key 16), `work-capability-report-page.test.tsx` (ô dưới ngưỡng hiện «chưa đủ mẫu», panel tải gọi `/load`).

## Success criteria
- Đại ca mở «Năng lực theo loại việc», lọc YCMH vai «Người xử lý» → thấy «chị A: 12 phiếu, trung vị 3,5 ngày, chậm nhất 9 ngày, làm lại 8%, đang ôm 7 việc».
- Agent 4 nhận hợp đồng và gọi được hai hàm trong A1 mà không cần sửa ERP thêm.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| Diễn giải sai «chậm» (việc khó ≠ người chậm) | TB × Cao | Hiện số mẫu, p90, theo loại task; ghi chú mục đích (cải tiến, không chấm điểm — doc 22 §6) |
| Tranh số ReportKey với phase 03 | TB × Thấp | Thứ tự cố định 15 (D0c) → 16 (D1d); test catalog bắt lệch |
| A1 tự viết lại công thức | TB × TB | Hợp đồng rõ; lead nhắc DRY |

## Security
Khóa 16 + `setting`; mặc định chỉ admin. Số theo người chỉ ≥ 5 mẫu. Mỗi lần xem có `tab_request_log`. A1 phải tự gác phạm vi phòng ban (doc 22 §4) — ghi trong hợp đồng.

## Rollback
Gỡ router + trang; khóa 16 không tái dùng, thu hồi dòng `tab_report_access` bằng `revoked_at`.

## Next steps
A1 (Agent 4): bọc `task_type_stats`/`current_load` thành công cụ; A3: so ước lượng với thực tế từ `estimate_hours`/`actual_hours`; T1 thử phòng Thu mua.
