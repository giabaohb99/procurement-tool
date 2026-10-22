# Phase 07 — D1c: Tải đang ôm, tính ngay lúc hỏi

## Context links
- Lời đại ca: «Tải đang ôm tính ngay lúc hỏi, không chỉ theo tuần»
- `doc/erp/tai-lieu-ai/22-ai-ke-hoach-phan-viec.md` §4 `team_capacity` (số việc đang mở, quá hạn, nghỉ phép trong khoảng, giờ theo lịch)
- Nguồn: `approval/task_service.my_tasks` / `count_my_tasks` (có cả việc được ủy quyền), `tab_approval_task` (index `(assignee_employee_id, status)`),
  `tab_delegation` (`ix_delegation_to/_from`), `tab_work_task(+_assignee)`, `tab_purchase_request.assignee_id/head_of_dept_id`, `tab_purchase_order.nspt_id`,
  dòng YCBG `assignee` (mã NV chuỗi), `tab_document.clone_assignee_employee_id` (status 11), `tab_leave_request`
- Đã có ở snapshot tuần: `pending_now`, `work_overdue_open` (chỉ theo tuần — đây là bản tức thì)

## Overview
- P1 · **1 ngày** (BE) · **implemented — duoc-CR-656 (20/10/2026)** · sau phase 05 (giờ ước lượng) và 06 (index gom ở migration D1a).
- Một hàm dịch vụ `current_load(...)` trả tải từng người tại thời điểm gọi, **số truy vấn cố định (≤ 10)**, không cache quá 60 giây.

## Key insights
- Snapshot tuần không đủ: AI chia việc cần tải *bây giờ*. Không cần bảng mới — đọc thẳng bảng nguồn, có index.
- Duyệt Thu mua (YCMH/YCBG/ĐMH) không gán duyệt cho một người; chỉ YCMH có `head_of_dept_id` → dùng làm đại diện, YCBG/ĐMH chờ duyệt **không** tính theo người (Q6).
- Ủy quyền: việc vẫn nằm ở `assignee_employee_id` của người ủy quyền; người được ủy quyền thấy và làm được (`my_tasks`). → tách hai số (Q5).

## Requirements
- Theo người: duyệt đang chờ (và quá hạn), việc dự án đang mở (quá hạn, Σ giờ ước lượng còn lại), phiếu đang xử lý theo loại, việc được ủy quyền nhận thay, đang nghỉ / nghỉ sắp tới trong `horizon_days` (mặc định 14).
- Lọc theo pháp nhân / phòng ban / danh sách nhân sự. Nhanh: < 300 ms cho 100 người.

## Architecture
`capability/workload_service.py` — `current_load(db, *, company_id=None, department_ids=None, employee_ids=None, now=None, horizon_days=14) -> list[dict]`
Mỗi truy vấn là một `GROUP BY employee` có lọc `IN (employee_ids)`:
| # | Số | Nguồn / điều kiện |
|---|---|---|
| Q1 | nhân sự trong phạm vi | `tab_employee` đang làm việc + phòng ban |
| Q2 | `approvals_pending`, `approvals_overdue` | `tab_approval_task` status=PENDING, `due_at < now` |
| Q3 | `delegated_in` (+ `delegated_out_to`) | `tab_delegation` đang hiệu lực hôm nay × Q2 của người ủy quyền (tính trong Python) |
| Q4 | `work_open`, `work_overdue`, `work_estimate_hours_open` | `tab_work_task_assignee(kind=PIC)` ⨝ `tab_work_task` status=OPEN, `deleted_at IS NULL`; `due_date < hôm nay VN` |
| Q5 | `pr_handling` | YCMH `assignee_id` ∈, status ∉ {draft, completed, done, cancelled, rejected} |
| Q6 | `pr_approval_pending` (đại diện) | YCMH status=`submitted` theo `head_of_dept_id` |
| Q7 | `po_handling` | ĐMH `nspt_id` ∈, status ∉ {draft, received, completed, cancelled, rejected} (20/10: `received` = xong) |
| Q8 | `survey_lines_handling` | dòng YCBG `assignee` (mã NV) chưa xong ⨝ `tab_employee.code` |
| Q9 | `docs_pending_issue` | văn bản status=11 theo `clone_assignee_employee_id` |
| Q10 | `on_leave_today`, `leave_days_ahead` | nghỉ phép đã duyệt giao `[hôm nay, hôm nay + horizon]` |
Trả thêm `computed_at` và `open_items_total` (Σ các số «đang xử lý» + duyệt chờ; không trọng số — AI tự cân, Q11).
Không ghi gì; không phụ thuộc `tab_work_cycle`.

## Related code files
Tạo BE: `backend/app/modules/capability/workload_service.py` · `workload_sources.py` (tách truy vấn, mỗi tệp < 200 dòng).
Không sửa model/tệp nghiệp vụ. Index cần đã nằm ở migration phase 06 (`tab_purchase_request(assignee_id, status)`, `tab_purchase_order(status)`); index sẵn có: approval_task, work_task_assignee, delegation, leave.

## Implementation steps
1. Xác minh hằng trạng thái thật (YCBG `line_status`, YCMH `assignee_id` là NV — kết quả spike phase 06).
2. Viết `workload_sources` (10 hàm truy vấn) + `workload_service` (gộp thuần).
3. EXPLAIN từng truy vấn trên bản sao dev — không full scan bảng lớn.
4. Đo thời gian 100 người.

## Todo
- [x] xác minh hằng (kết quả bên dưới)
- [x] 10 truy vấn + gộp (`capability/workload_sources.py` · `workload_service.py`)
- [x] EXPLAIN + đo: 143 người local = 10 truy vấn, 69 ms; optimizer chọn index mới cho PO/YCMH-duyệt/văn bản; YCMH-dòng và dòng YCBG quét bảng nhỏ (chưa đủ lớn để chọn index)
- [x] test (`test_tai_dang_om_cr656.py`, 10 bài) + API quản trị `GET /api/work-capability/load` (`setting.read`, 422 nếu không chọn phạm vi)
- [x] đối chiếu «Việc của tôi»: `approvals_pending`/`delegated_in` khớp `approval.task_service.my_tasks` cho 60/60 người local; đối chiếu bảng Dự án/Thu mua bằng tay: chưa (local gần như không có dữ liệu)

### Hằng trạng thái đã xác minh — chỗ lệch kế hoạch
- **Văn bản «chờ ban hành» (status 11) tính theo `drafter_employee_id`** (người soạn — `document.service.can_issue`), không phải `clone_assignee_employee_id` như bảng kế hoạch. Chỉ mục: `ix_document_drafter_status`.
- **`pr_handling` theo `tab_purchase_request_item.assignee` (mã NV)**, không theo `assignee_id` (luôn 0 — xem phase 06). Đếm số YCMH (distinct), dòng đã xong/hủy và phiếu draft/submitted/completed/done/cancelled/rejected bị loại.
- Dòng YCBG đang giữ = `line_status != completed` và `pr_code == ''` và phiếu cha ∈ `submitted/approved/processing`.
- Mọi bảng `SoftDeleteMixin` (YCMH, YCBG, ĐMH, văn bản, nghỉ phép) lọc `is_deleted`.
- Chỉ mục thêm (cùng migration `d1cap01`): `ix_pr_head_status`, `ix_po_nspt_status`, `ix_srl_assignee_status`, `ix_document_drafter_status` (khai cả trong model để autogenerate không trôi). Bỏ `tab_purchase_request(assignee_id,status)` và `tab_payment_request(status)` vì không còn truy vấn nào dùng.

## Tests
Backend `test/backend/test_tai_dang_om_cr656.py`: dữ liệu mẫu đủ 10 nguồn → đúng từng số; task đã xóa mềm / CANCELLED không tính;
ủy quyền hết hạn không tính `delegated_in`; nghỉ ngoài `horizon` không tính; lọc phòng ban; **đếm truy vấn ≤ 10** với 5 và 200 nhân sự; `now` tiêm được (không phụ thuộc giờ máy).

## Success criteria
- `current_load` cho 100 người < 300 ms trên bản sao dev; số khớp với màn «Việc của tôi» (duyệt) và bảng Dự án của 5 người đối chiếu tay.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| Tải Thu mua thiếu người duyệt thật | Chắc × TB | Ghi rõ «đại diện theo trưởng phòng»; Q6 |
| Hằng trạng thái lệch thực tế | TB × TB | Lấy từ `status_codes`/hằng module, không gõ tay chuỗi |
| Mã NV ở dòng YCBG không khớp | TB × Thấp | Join theo `code`, mã lạ bỏ qua + đếm vào log cảnh báo |

## Security
Hàm không tự gác quyền — người gọi (controller D1d gác khóa 16; A1 gác theo doc 22 §4) phải truyền phạm vi phòng ban đã kiểm.
Ghi điều này ở docstring + test «không truyền phạm vi thì không trả gì» (mặc định an toàn: không truyền `company_id`, `department_ids` lẫn `employee_ids` → `[]`; muốn cả công ty phải truyền rõ).

## Rollback
Không có thay đổi dữ liệu; gỡ tệp là xong.

## Next steps
D1d mở đường `/api/work-capability/load` và đưa hàm cho A1.
