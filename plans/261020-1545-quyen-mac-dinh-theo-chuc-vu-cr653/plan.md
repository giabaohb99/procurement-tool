# duoc-CR-653 — Quyền mặc định theo chức vụ

Mục tiêu: mỗi chức vụ (`tab_job_position`) khai một gói vai trò; tài khoản của nhân sự giữ chức vụ đó
được hệ thống tự cấp gói, đổi chức vụ thì chỉ đổi phần HỆ THỐNG đã cấp.

## Quyết định thiết kế (đã đối chiếu mã nguồn)
- Bậc phạm vi dòng (own/dept/company/all) nằm ở `tab_permission.scope` (vai trò × entity), KHÔNG nằm ở
  `tab_user_role`. Gói chức vụ vì thế chỉ khai DANH SÁCH VAI TRÒ; bậc phạm vi đi theo vai trò (vd vai trò
  «Trưởng phòng (duyệt PYC)» đã là bậc dept). Không thêm cột bậc ghi đè (sẽ đổi lõi `get_perm_profile`).
- `tab_job_position_role(job_position_id, role_id)` unique. `tab_user_role.granted_by_position_id` (0 = tay).
- Một hàm duy nhất `position_role_service.sync_employee_roles` — chỉ `flush`, audit không commit, xóa cache
  quyền SAU commit (listener `after_commit`). Gọi ở: cấp TK, `update_employee_core`, nhập Excel (nhánh chức vụ
  chữ), hoàn tác lô nhập, mở khóa TK. Work-history apply đi qua `update_employee` nên đã phủ.
- Gói sửa bằng `role.write` + chặn nâng quyền; «Áp lại» cũng vậy, bỏ qua chính người bấm.

## Phase
| # | Việc | Trạng thái |
|---|---|---|
| 1 | Model + migration + service + hook | done |
| 2 | API gói + áp lại + script đề xuất | done |
| 3 | Frontend tab «Quyền mặc định» + badge | done |
| 4 | Test backend/vitest + kiểm thật | done |

## Đợt sửa sau review (plans/reports/code-reviewer-261020-cr653-review.md) — done
C1 cấm tự cấp cho chính mình (mọi đường) · H1 lọc leo thang (+ bỏ qua có nhật ký) · H2 403 tự thêm vào gói chức vụ mình giữ
· H3 reference vai trò, JOIN Role, dọn gói khi xóa chức vụ, gỡ dòng hệ thống khi xóa cứng hồ sơ · M1 dedup giữ dòng tay
· M2 unique(user_id, role_id) + dọn trùng trong jobposrole01 + IntegrityError êm · M3 chỉ ghi tài liệu · M4 script mặc định
>=3 người, loại vai trò cấm, nhật ký · M5 vai trò cấm ở PUT và lúc cấp · Lows: nhật ký cùng giao dịch, 409, summary, useRef,
type=button. Bài hồi quy: test/backend/test_quyen_theo_chuc_vu_cr653_review.py.
