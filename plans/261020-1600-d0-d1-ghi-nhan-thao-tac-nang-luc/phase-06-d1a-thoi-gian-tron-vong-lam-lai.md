# Phase 06 — D1a: Thời gian trọn vòng + số lần làm lại theo loại việc và theo người

## Context links
- Lời đại ca: «chị A làm một YCMH từ lúc tạo tới lúc xong trung bình mấy ngày, chậm nhất mấy ngày» · «số lần phải làm lại theo từng loại việc»
- `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §4 (`task_type_stats`: trung vị/p90, tỷ lệ làm lại, số mẫu, theo người chỉ khi ≥ 5 mẫu), §5 nhóm 3.7
- Nguồn: `tab_change_log` (`change_log/model.py`: table_name, row_id, field, before_value, after_value, created_at; index `ix_change_log_row`; giữ **16 tháng**),
  `tab_audit_log` (YCMH `returned`), `tab_approval_instance/task/action`, `tab_work_task(+_assignee)`
- Tham khảo đã có: `approval/report_turnaround.turnaround_hours`, `usage_profile/snapshot_metrics_flow.chain_metrics` (`returned_rate`, có lỗ ở xe/dấu/nghỉ/phòng)

## Overview
- P1 · **2,5 ngày** (BE) · **implemented — duoc-CR-656 (20/10/2026)** · sau phase 05.
- Bảng **sự kiện vòng đời đã tính sẵn** `tab_work_cycle` (1 dòng / phiếu / vai / người) dựng gia tăng mỗi đêm + script dựng lại toàn bộ.

## Key insights
- Không có nguồn lịch sử trạng thái chung: Thu mua dùng cột chuỗi riêng, 5 loại dùng bộ máy duyệt; YCMH/ĐMH tự chuyển `completed`/`received` **không ghi audit**.
  `tab_change_log` (hook ORM) là nguồn duy nhất thấy mọi lần đổi `status` → dùng **một bộ chuyển đổi chung theo cấu hình** + một ngoại lệ (YCMH «trả về» lấy từ audit vì YCMH dùng `rejected` cho cả từ chối lẫn trả về).
- `tab_change_log` chỉ giữ 16 tháng → phải **lưu kết quả** vào bảng riêng giữ lâu (3 năm), không tính lại từ log mỗi lần hỏi. Đồng thời làm báo cáo nhanh.
- Mọi `DateTime` trong DB là UTC naive; cột chuỗi giờ của xe/dấu không dùng (lấy mốc từ change_log/instance).
- ⚠️ Cần **spike 0,5 ngày đầu**: xác nhận change_log có ghi `status` khi service dùng `query.update()` hàng loạt (bỏ qua sự kiện ORM). Chỗ nào không ghi → dùng mốc dự phòng của chính bảng (`completed_at` task, `decided_at` nghỉ/phòng, `issued_at` văn bản, `finished_at` instance).
- `assignee_id` của YCMH: xác minh là id nhân sự hay user ở bước spike.

## Requirements
- Theo loại việc × người × vai: số phiếu xong, thời gian trọn vòng (giờ → hiện ngày), số lần làm lại, kết cục (xong/hủy/từ chối), trễ hạn (task có hạn).
- Định nghĩa «xong» và «làm lại» cố định trong code, ghi tài liệu (Q2 — duyệt bảng dưới).

## Architecture
**Mã** `backend/app/core/capability_codes.py` (thuần stdlib, đăng ký code sets, sinh TS):
`CycleKind` 1 PURCHASE_REQUEST · 2 SURVEY_REQUEST · 3 PURCHASE_ORDER · 4 PAYMENT_REQUEST · 5 DOCUMENT · 6 VEHICLE_BOOKING · 7 SEAL_REQUEST · 8 ROOM_BOOKING · 9 LEAVE_REQUEST · 10 WORK_TASK;
`CycleRole` 1 CREATOR «Người lập/đề nghị» · 2 HANDLER «Người xử lý»; `CycleOutcome` 1 OPEN · 2 DONE · 3 CANCELLED · 4 REJECTED.

**Bảng định nghĩa** (`capability/cycle_specs.py`, cấu hình — không rải `if` theo loại):
| Loại | Bảng | Xong (status mới) | Kết cục âm | Làm lại = số lần | Người lập | Người xử lý (mốc bắt đầu) |
|---|---|---|---|---|---|---|
| YCMH | tab_purchase_request | `completed`/`done` | `cancelled`; audit `rejected` (từ chối) | audit action `returned` | `requester_id` | `assignee_id` (mốc: lần đầu change_log `assignee_id` = người đó) |
| YCBG | tab_survey_request | `done` (Q2: hay `survey_done`) | `cancelled` | status → `rejected` (= Trả về) | `requester_id` | `assignee` từng dòng (mã NV → id) |
| ĐMH | tab_purchase_order | `received` hoặc `completed` (đại ca chốt 20/10/2026: «Đã nhận đủ» = xong; mốc = lần đầu) | `cancelled` | status → `rejected` (= Trả về) | `created_by`→NV | `nspt_id` (mốc: change_log `nspt_id`) |
| YCTT | tab_payment_request | `paid` | `cancelled` | — (không có trả về) | `created_by`→NV | — |
| Văn bản | tab_document | 3 hoặc 4 (lần đầu) | 10, 7 | status → 9 | `drafter_employee_id` | — |
| Đặt xe | tab_vehicle_booking | 5 | 6, 7 | status → 8 | `requester_id` | — |
| Duyệt dấu | tab_seal_request | 4 | 5, 6 | status → 7 | `requester_id` | `completed_by`→NV |
| Phòng họp | tab_room_booking | 3 | 4, 6 | status → 5 | `requester_employee_id` | — |
| Nghỉ phép | tab_leave_request | 3 | 4, 6 | status → 5 | `employee_id` | — |
| Task Dự án | tab_work_task | 2 (lần cuối) | 3 | status 2 → 1 (mở lại) | `creator_employee_id` | mỗi PIC (`tab_work_task_assignee.kind=1`) |
Trọn vòng = `done_at − start` (start = `created_at` với vai lập; mốc giao việc với vai xử lý). Nhận hàng: không có vòng đời → **không tính** (Q4).

**Bảng `tab_work_cycle`** (`capability/model.py`, không AuditMixin, giữ 3 năm):
`id · kind SMALLINT · entity_id BIGINT · role SMALLINT · employee_id BIGINT · company_id · department_id (của nhân sự lúc tính) · task_type_id BIGINT DEFAULT 0 ·
started_at DATETIME · done_at DATETIME NULL · outcome SMALLINT · cycle_hours FLOAT NULL · rework_count SMALLINT · due_date DATE NULL · is_late BOOL NULL ·
estimate_hours DECIMAL(6,2) NULL · actual_hours DECIMAL(6,2) NULL · review_outcome SMALLINT DEFAULT 0 · computed_at DATETIME`
UNIQUE `(kind, entity_id, role, employee_id)` · INDEX `(done_at, kind)` · INDEX `(employee_id, kind, done_at)`.
Cùng migration gom **mọi index D1** (memory «index gom 1 migration»): `tab_change_log(table_name, field, created_at)` nếu chưa có tương đương ·
`tab_purchase_request(assignee_id, status)` · `tab_purchase_order(status)` · `tab_payment_request(status)` (phục vụ D1c).

**Dựng gia tăng** (`capability/cycle_builder.py`, celery `capability.build_cycles` 05:00 VN):
1. Lấy tập phiếu chạm tới từ `since = lần chạy trước − 1 ngày` (watermark lưu `tab_setting` khóa `capability_cycle_watermark`): change_log theo `table_name ∈ spec` (1 truy vấn) ∪ phiếu tạo mới (1 truy vấn/bảng) ∪ task đổi PIC (`updated_at`).
2. Theo từng loại, chia lô 1000 id: nạp dòng phiếu (1) + change_log status/người xử lý (1) + audit trả về YCMH (1, chỉ YCMH) + PIC/dòng YCBG (1) → hàm **thuần** `compute_cycles(spec, rows, logs, …)` → xóa dòng cũ của các `(kind, entity_id)` đó + INSERT nhiều dòng.
3. Số truy vấn cố định theo (loại × lô), không theo số phiếu. `scripts/backfill_work_cycles.py` chạy cùng hàm trên mọi id (phạm vi = change_log còn giữ, ~16 tháng).

## Related code files
Tạo BE: `backend/app/core/capability_codes.py` · `backend/app/modules/capability/{__init__,model,cycle_specs,cycle_compute,cycle_sources,cycle_builder,tasks}.py` ·
`backend/scripts/backfill_work_cycles.py` · migration `d1cycle01_vong_doi_phieu_va_chi_muc.py` · `doc/tai-lieu-ky-thuat/nang-luc-theo-loai-viec.md` (định nghĩa xong/làm lại).
Sửa BE: `core/code_sets.py` · `core/all_models.py` · `core/celery_app.py` (include + beat 05:00, dọn 3 năm).
Không sửa model nghiệp vụ nào (chỉ thêm index qua migration; khai index tương ứng trong model để autogenerate không trôi — `purchase_request/model.py`, `purchase_order/model.py`, `payment_request/model.py`: chỉ `__table_args__`).

## Implementation steps
1. Spike: chạy trên bản sao dev — change_log có đủ `status` cho 10 bảng? `query.update()` nào bỏ qua? `assignee_id` là NV hay user? Ghi kết quả vào tài liệu.
2. Mã + bảng + index + migration (nối head hiện hành).
3. `cycle_specs` + `cycle_compute` thuần (không DB) — phần lớn test nằm ở đây.
4. `cycle_sources` (truy vấn theo lô) + `cycle_builder` (gia tăng, watermark) + task + beat + dọn.
5. Backfill trên dev; đối chiếu tay 10 phiếu mỗi loại với màn chi tiết.
6. Viết tài liệu định nghĩa.

## Todo
- [x] spike change_log / update hàng loạt / assignee_id (kết quả bên dưới)
- [x] mã + bảng + migration index (`capability_codes.py` · `capability/model.py` · `d1cap01`)
- [x] specs + compute thuần (`cycle_specs.py` · `cycle_compute.py`)
- [x] sources + builder + task + watermark (`cycle_sources.py` · `cycle_builder.py` · `tasks.py`, beat 05:00)
- [x] backfill + đối chiếu (local 0,7 giây; đối chiếu YCMH/YCBG với audit, task với change_log — xem dưới; chưa đối chiếu 10 phiếu/loại trên dev vì local ít dữ liệu)
- [x] tài liệu định nghĩa: `doc/tai-lieu-ky-thuat/nang-luc-theo-loai-viec.md`

### Kết quả spike (20/10/2026, DB local)
1. **change_log có bắt `status` khi đổi qua ORM** (kể cả task mở lại 2→1) — thử trực tiếp bằng service thật trong `open_context`: 3 dòng cho 3 lần đổi.
   **Đổi bằng `query.update()` hàng loạt thì KHÔNG có dòng nào** (đã thử). Rà mã: không đường nào dùng `update()` hàng loạt để đổi `status` của 10 bảng; ngoại lệ thực tế là
   việc nền Celery / script không mở `open_context` (đồng bộ app đặt xe cũ, nạp từ tệp) — cũng không ghi nhật ký.
2. **`tab_change_log` chỉ có từ 16/09/2026** (local), `tab_audit_log` từ 01/07/2026. Với 4 chứng từ Thu mua dùng **audit** làm nguồn chính (có từ vựng «trả về»/«từ chối»),
   change_log bổ sung (bắt cả bước tự chuyển); hai nguồn gộp, sự kiện cùng loại cách ≤ 120 giây tính một. Phiếu không có dấu vết nào → **dòng ước tính** (`is_estimated`, `done_at` lấy từ cột mốc của bảng hoặc `updated_at`).
   Đây là **phương án dự phòng kế hoạch đã nêu** ("mốc dự phòng của chính bảng"), chọn vì không thể dựng lại lịch sử trước ngày bật nhật ký.
3. **`tab_purchase_request.assignee_id` là id nhân sự nhưng luôn 0** (72/72 dòng local; bị xóa lúc duyệt/từ chối). Người phụ trách YCMH thật nằm ở `tab_purchase_request_item.assignee` (mã NV) →
   dùng cột dòng (YCBG đã vậy). Kéo theo D1c: `pr_handling` đếm theo dòng hàng, không theo `assignee_id`.
4. Sự kiện «hoàn thành tự động» của YCMH (`sync_from_purchase_orders`) không ghi audit: 3/10 phiếu `completed` local thiếu → dòng ước tính.
5. Lệch kế hoạch khác: `tab_seal_request.approved_at/completed_at` và `tab_vehicle_booking.approved_at` là **chuỗi ISO** (không phải DateTime) → `cycle_sources.as_datetime`.

**Lệch so với kế hoạch (có chủ ý):** thêm cột `is_estimated` vào `tab_work_cycle`; không thêm chỉ mục `tab_change_log(table_name, field, created_at)` (đã có `ix_change_log_row (table_name,row_id,id)` đủ cho truy vấn theo lô id) và không thêm chỉ mục `updated_at`
(bảng nhỏ, quét một lần/đêm); chọn tập phiếu «chạm tới» bằng `updated_at >= since` + bảng con thay vì quét change_log.

## Tests
Backend `test_vong_doi_phieu_cr656_tinh_thuan.py` (34 bài, hàm thuần) + `test_vong_doi_phieu_cr656_dung_bang.py` (9 bài, DB + đếm truy vấn):
- compute thuần mỗi loại: tạo → gửi → trả về → gửi lại → xong ⇒ `rework_count=1`, `cycle_hours` đúng; hủy ⇒ outcome CANCELLED, `done_at` NULL;
  YCMH `rejected`+audit `returned` ⇒ làm lại, `rejected`+audit `rejected` ⇒ REJECTED; task mở lại 2 lần rồi xong ⇒ `rework_count=2`, `done_at` = lần cuối; task nhiều PIC ⇒ 1 dòng/PIC.
- builder: chạy 2 lần không nhân đôi; chỉ phiếu chạm tới được tính lại; watermark tiến; **đếm truy vấn** = hằng số × số loại khi 10 hay 500 phiếu.
- múi giờ: mốc UTC; ngày VN không lệch.

## Success criteria
- Backfill dev xong < 5 phút; đối chiếu tay 10 phiếu/loại khớp 100%.
- Lượt đêm gia tăng < 30 giây; số truy vấn không tăng theo số phiếu.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| change_log thiếu dòng do `query.update()` | TB × Cao | Spike bước 1; mốc dự phòng từ bảng gốc; ghi rõ loại nào dùng dự phòng |
| Định nghĩa «xong» sai ý đại ca | TB × TB | Q2 duyệt bảng; specs là cấu hình — đổi một dòng, chạy lại backfill |
| Chỉ có ~16 tháng lịch sử | Chắc × Thấp | Ghi «dữ liệu từ …» trên báo cáo; từ nay giữ 3 năm trong bảng riêng |
| Thêm index trên bảng lớn | Thấp × TB | Online DDL InnoDB; chạy ngoài giờ cao điểm (như `usgprof01`) |

## Security
Bảng chỉ số + mã + id; không nội dung phiếu. Đọc chỉ qua service D1d (gác khóa 16) và hàm cho A1.

## Rollback
Gỡ beat; downgrade drop bảng + index. Không ghi vào bảng nghiệp vụ nên không có thiệt hại dây chuyền.

## Next steps
D1d tính trung vị/p90/tỷ lệ làm lại từ `tab_work_cycle`.
