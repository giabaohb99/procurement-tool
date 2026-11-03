# Phase 06 — Báo cáo Công việc / Dự án

## Context links
- `backend/app/modules/work/task_model.py:36` (`tab_work_task`: list_id, section_id, parent_id, status, kind, start_date/due_date String(10), creator_employee_id, completed_at DateTime, deleted_at, company_id)
- `work/model.py:34` (WorkTaskStatus OPEN=1, DONE=2, CANCELLED=3; WorkTaskKind TASK=1, MILESTONE=2), `tab_work_task_assignee(task_id, employee_id, kind: PIC=1/FOLLOWER=2)`, `tab_work_list` (dự án), `tab_work_group`
- `work/overview_service.py:46` (luật lọc gốc + quá hạn), `work/membership_service.py:67` (`visible_list_ids`)
- Nhãn ưu tiên: `WorkLabelField.system_key == PRIORITY_KEY` → `WorkLabelOption`
- Menu FE: `/project/lists` → `work_task`

## Overview
- Priority: P2 · Status: pending · Effort: 4h · Sở hữu: `work/report_service.py`, `work/report_controller.py`, `config/report-catalog-work.ts`, `pages/work-report-page.tsx`

## Key insights
- `work_task` là PUBLIC trong `SCOPE_FIELDS` → chốt THẬT là `list_id IN visible_list_ids(db, employee_id)`; tài khoản `employee_id=0` bị chặn (`require_employee`). Bỏ chốt này = lộ việc của mọi dự án.
- Luật gốc giống `/api/work/overview`: `parent_id IS NULL`, `deleted_at IS NULL`; quá hạn = `status==OPEN and due_date != "" and due_date < hôm nay (giờ VN)`.
- PIC nhiều người → chiều nhiều giá trị (Tổng tính riêng, khung P01).
- Ưu tiên là nhãn RIÊNG từng dự án → gom theo TÊN option.

## Báo cáo — Công việc & Dự án
- `GET /api/work/summary` (+export) · `require('work_task','read'|'export')` · lọc `visible_list_ids`.
- Trường ngày: `created_at` cho "tạo mới", `completed_at` cho "hoàn thành" (hai luồng đếm trong cùng kỳ = biểu đồ thông lượng kiểu Haravan: 2 đường). Chỉ số snapshot tính tại `min(to, hôm nay)`.
- Chỉ số: Việc tạo mới, Việc hoàn thành, Đang mở (snapshot), Quá hạn (snapshot, good down), Tỷ lệ đúng hạn % (hoàn thành có hạn và `completed_at` (VN) ≤ `due_date`, good up), Thời gian hoàn thành TB ngày (`created_at→completed_at`, good down).
- Xem theo: thời gian · dự án (`list_id`) · nhóm dự án (`group_id` của list) · người phụ trách (PIC) · công ty · trạng thái · độ ưu tiên.
- Breakdowns: top dự án theo quá hạn; top PIC theo việc mở.
- Lọc riêng (FE `extraFilters`): dự án (ô chọn từ danh sách dự án người xem thấy), gồm việc con (Q6.1, mặc định không).

## Related code files
Tạo: `backend/app/modules/work/report_service.py`, `test/backend/test_bao_cao_cong_viec.py`; điền route vào `work/report_controller.py` (P01).
Frontend: `config/report-catalog-work.ts` (group "Công việc"), `pages/work-report-page.tsx`, `components/work-report-project-filter.tsx` (nếu cần, dùng hook dự án sẵn có của `modules/work`, tự tắt khi thiếu quyền). Route (P02): `/report/work`.

## Implementation steps
1. `fetch` 2 luồng (tạo trong kỳ / hoàn thành trong kỳ) → 1 danh sách hàng có cờ `created_in`/`completed_in`; PIC + ưu tiên tra theo lô (2 truy vấn).
2. `snapshot(at)`: đang mở/quá hạn từ cùng tập dự án thấy được.
3. Test + FE + cổng kiểm.

## Test matrix
| Ca | Kỳ vọng |
|---|---|
| Không là thành viên dự án | 0 việc của dự án đó |
| `employee_id=0` | 403/chặn như overview |
| Việc 2 PIC | mỗi PIC +1, Tổng +1 |
| Việc đã xóa mềm / việc con | không đếm (mặc định) |
| Hoàn thành 23:30 UTC ngày hạn−1 | tính theo ngày VN = ngày hạn → đúng hạn |

## Success criteria
5 ca xanh; số "Quá hạn" = số ở `/api/work/overview` cho cùng người dùng hôm nay.

## Risk assessment
| Rủi ro | K×A | Giảm thiểu |
|---|---|---|
| Quên `visible_list_ids` | Thấp×Cao | test thành viên; review bắt buộc |
| Việc không có hạn làm méo % đúng hạn | TB×Thấp | mẫu số chỉ gồm việc có hạn; hiện số việc thiếu hạn ở `notes` |

## Security considerations
Chỉ trả tên người phụ trách + tên dự án người xem đã thấy.

## Câu hỏi
- Q6.1 Có đếm việc con (subtask) và mốc (milestone) không? Đề xuất: không.
