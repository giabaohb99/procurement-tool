# Phase 03 — BE phiếu thanh toán nghỉ phép (duoc-CR-719)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | backend | Hiệu lực | duoc-CR-719 |

Trạng thái: xong, chưa commit. Không đổi migration. Một tiến trình pytest mỗi lượt.

## Tệp
Tạo (`backend/app/modules/leave/`): `encashment_math.py` (toán thuần) · `encashment_balance.py` (đọc quỹ, `compute`, `preview`) ·
`encashment_service.py` (kiểm, lập/sửa/xóa, `claim`) · `encashment_transitions.py` (gửi/duyệt/từ chối/hủy) ·
`encashment_approval_bridge.py` (hook bộ máy duyệt) · `encashment_serializer.py` · `encashment_schema.py` ·
`encashment_controller.py`; `assistant/tools/leave_encashment_tool.py`; `test/backend/test_nghi_phep_thanh_toan_cr719.py` (35 bài).
Sửa: `main.py` (router + nạp bridge) · `employee/references.py` (+2 dòng: `LeaveEncashment.employee_id`, `PaymentRequest.payee_employee_id`) ·
`approval/{task_notification,permission_approvers,report_service,self_approval_policy}.py` · `assistant/tools/leave_tool.py` + `assistant/service.py`
(một câu) · `payment_request/leave_encashment_payout.py` (+`notify_payout_outcome`, `payout_state(lock=)`) ·
`payment_request/controller.py` (`_notify_pay`, +4 dòng: YCTT nghỉ phép đi chuông riêng) · `notification/service.py` (+2 nhánh `pay_leave_paid`, `pay_leave_rejected`) ·
test: `test_pham_vi_duong_vong` (97 -> 98, +`encashment_controller` `_get_or_404`), `test_duyet_theo_quyen_cr680` (danh sách entity thêm `leave_encashment`).

## Luật tính (đã làm)
`encashable = floor0,5( clamp(base, 0, cap) )`. Cuối năm: `base = available - phần mang sang chưa dùng - non_encashable_days`,
`cap = max_encashable_days - encashed_days của dòng` (nếu trần > 0). Nghỉ việc: `base = available`, không trần. Ứng phép âm -> 0.
Làm tròn XUỐNG bước 0,5 (spec ghi `days` bước 0,5). `ensure_balance` (năm nay) / `get_balance` (năm trước, không tự cấp) + `expire_carried`.

## Hợp đồng API cho frontend — `/api/leave-encashments` (tag `leave`, phong bì `{success,message,data}`)
Mã trạng thái `status`: 1 Nháp · 2 Chờ duyệt · 3 Đã duyệt · 4 Từ chối · 5 Trả về · 6 Đã hủy. `reason_kind`: 1 Phép dư cuối năm · 2 Nghỉ việc.
Khóa quyền `leave_encashment` (read/create/write/delete/approve/cancel/export). Số tiền KHÔNG có trong phiếu.

| Phương thức | Đường | Quyền | Ghi chú |
|---|---|---|---|
| GET | `/` | read (phạm vi own+self / dept / company / all) | `page, limit`, lọc `status, employee_id, company_id, department_id, leave_type_id, balance_year, reason_kind`, `q` (mã / tên NV / ghi chú), `sort`. `{total, items[]}` |
| GET | `/to-approve` | đăng nhập | mỗi item thêm `task`, `flow` |
| GET | `/preview?leave_type_id&employee_id=0&balance_year&reason_kind=1` | create (lập hộ cần quyền như lập phiếu) | chỉ đọc (xem dưới) |
| GET | `/{id}` | read, hoặc đang có việc duyệt treo | thêm `created_by_name, has_running_approval, payment, cancel_blocked_reason` |
| POST | `/` | create | body `{employee_id?=0, leave_type_id, balance_year? (năm nay / năm trước), reason_kind=1, encashment_date?, days? (null = lấy số được phép), note<=1000}` |
| PATCH | `/{id}` | write | body `{reason_kind?, encashment_date?, days?, note?}`; chỉ Nháp / Trả về (người, loại, năm không đổi) |
| DELETE | `/{id}` | delete | xóa mềm, chỉ Nháp |
| POST | `/{id}/submit` | write | giữ chỗ + trình duyệt; cờ duyệt tắt -> Chờ duyệt, `approval_instance_id = 0` |
| POST | `/{id}/approve` | approve | duyệt thẳng; 400 nếu đang chạy luồng nhiều bước; 403 tự duyệt (luôn chặn) |
| POST | `/{id}/reject?reason=` | approve | `reason` <= 500 |
| POST | `/{id}/cancel?reason=` | cancel | `reason` <= 500 |

Item (list và chi tiết): `id, code (TTP#####), company_id, department_id, department_name, employee_id, employee_name, employee_code,
leave_type_id, leave_type_name, balance_year, reason_kind, reason_kind_label, encashment_date, days, balance_snapshot, encashable_snapshot,
note, status, status_label, approval_instance_id, decided_at, decision_note, payment_request_id, payment_status ("" | draft | submitted |
approved | paid | cancelled), payment_status_label, created_by, created_at, updated_at`.

`/preview` trả: `has_balance, available, unused_carried, already_encashed, non_encashable_days, max_encashable_days,
cap_remaining (null = không trần), encashable (tối đa, bước 0,5), employee_id, leave_type_id, balance_year, reason_kind, reason_kind_label`.

`payment` (chi tiết): `null` khi chưa có YCTT hoặc YCTT đã xóa mềm; ngược lại `{id, code, status, status_label, total}`. `total` = số
tiền CHỈ khi người xem là chính nhân sự nhận tiền hoặc đọc được YCTT (có quyền YCTT và `leave_encashment.read` phủ); còn lại `total = null`
(người duyệt Nhân sự không thấy tiền). `cancel_blocked_reason`: chuỗi khác rỗng = nút Hủy phải tắt (phiếu Đã duyệt mà YCTT Chờ duyệt /
Đã duyệt / Đã chi; kế toán từ chối YCTT trước). Phiếu Đã duyệt mà YCTT bị kế toán từ chối: `payment.status = "cancelled"`, hủy được (D7a).

Lỗi riêng: 422 loại nghỉ không cho thanh toán / năm ngoài {nay, trước} / quỹ năm trước chưa có / thiếu ngày nghỉ việc ("Nhập ngày nghỉ
việc trên hồ sơ nhân sự…") / người đã nghỉ việc dùng lý do 1 / `days` ngoài bước 0,5 hoặc vượt `encashable`; 409 trùng phiếu còn hiệu
lực cùng (người, loại, năm) hoặc "Phiếu vừa được xử lý bởi lượt khác"; 400 sửa/xóa sai trạng thái, hủy bị YCTT chặn; 403 lập hộ / tự duyệt.

## Hành vi
- Gửi: khóa quỹ, tính lại, `pending_days += days`, ghi snapshot. Duyệt: `pending -= days`, `encashed_days += days`, `create_payout_request`
  -> `payment_request_id`. Từ chối / trả về / rút: một hàm `release_and_set` trả `pending`. Hủy Đã duyệt: `encashed_days -= days` (+ xóa mềm
  YCTT nếu còn Nháp), YCTT đọc có khóa (`payout_state(lock=True)`). Duyệt hỏng giữa chừng (`HookVeto`) -> cả giao dịch cuộn, test ép lỗi.
- Chuông kế toán `notify_payout_created`: đăng ký bằng `after_commit` (một lần) trong `approve_now`, chạy bằng phiên mới cùng kết nối; hỏng
  thì không chạy (test). Áp cho cả đường bộ máy duyệt lẫn duyệt thẳng.
- Chuông theo lead: YCTT Đã chi -> tài khoản của nhân sự nhận tiền (`pay_leave_paid`, link `/hr/leave-encashments/{id}`, không số tiền / ngày);
  kế toán từ chối -> người duyệt (`updated_by` của phiếu) + người lập, khác nhau thì cả hai (`pay_leave_rejected`, kèm lý do kế toán nhập).
  Móc ở `payment_request/controller._notify_pay` (4 dòng) -> `payout.notify_payout_outcome`.
- Chặn tự duyệt: `ALWAYS_STRICT_ENTITIES` + `ensure_not_self_approval` ở duyệt thẳng (câu riêng cho phiếu thanh toán nghỉ phép).
- AI: `my_leave_summary` thêm `encashed_days`, `allow_encashment / max_encashable_days / non_encashable_days` mỗi loại, `encashments[]` (chỉ ngày +
  trạng thái + trạng thái chi, không tiền; gác khóa `leave_encashment`), glossary + một câu ở `assistant/service.py`.

## Kiểm (một tiến trình mỗi lượt)
- `test_nghi_phep_thanh_toan_cr719.py` 35 xanh (toán bảng ERPNext, lập/chặn, vòng đời qua bộ máy thật, `HookVeto`, hủy 4 trạng thái YCTT, tự duyệt,
  phạm vi + việc duyệt treo, ẩn `payment.total`, chuông, nối dây, xóa nhân sự bị chặn, preview, `my_leave_summary` không tiền).
- Hồi quy xanh: `khai_du_b07`, `duong_vong`, `luat_bat_bien`, `duyet_theo_quyen_cr680`, `cr538`, `bo_may_duyet_xuyen_suot`, `nen_cr719`, `yctt_..._cr719` (284);
  8 tệp YCTT/payment + 3 tệp assistant nghỉ phép + `thong_bao_duyet` + `nghi_bu_cr715` (164); `-k "nghi_phep and not stress"` 717; `-k stress and nghi_phep` 97;
  `-k "cr715 or cr717"` 124 xanh + 1 đỏ có sẵn (`test_ton_kho_chan_trung_cr717` — chuỗi migration, dev khác). Chưa chạy toàn bộ `test/backend`.

## Câu hỏi mở / lưu ý
1. `approval/permission_approvers.py` thêm `leave_encashment` nên cách duyệt 9 (theo quyền) nay mở cho entity này; phạm vi Phòng ban / Công ty của nó
   nghĩa đúng (có cột `department_id`, `company_id`). Nếu không muốn mở thì gỡ một dòng.
2. Chưa thêm `leave_encashment` vào `assistant/tools/approval_tool.py` / `approval_action_tool.py` (ngoài danh sách tệp): trợ lý chưa liệt kê / duyệt hộ phiếu này.
3. `encashment_controller.py` 220 dòng (phần lớn docstring Swagger); `leave_tool.py` 349 dòng (đã 326 trước khi sửa).
4. `encashable` làm tròn XUỐNG 0,5 (ví dụ 6,25 -> 6,0) — suy ra từ bước 0,5 của `days`; nói lại nếu muốn hiển thị số lẻ.
5. Cần tick quyền `leave_encashment` cho vai trò trên hệ chạy (D-018) và bật luồng duyệt entity `leave_encashment` ở Phê duyệt; chưa bật thì duyệt thẳng.

**Status:** DONE
**Summary:** API 11 đường + hook duyệt + hủy theo YCTT + chuông + AI xong, 35 bài mới và hồi quy liên quan xanh.
**Concerns/Blockers:** Không chặn; xem câu 1-2 trên (mở cách duyệt 9; chưa nối công cụ duyệt hộ của trợ lý).
