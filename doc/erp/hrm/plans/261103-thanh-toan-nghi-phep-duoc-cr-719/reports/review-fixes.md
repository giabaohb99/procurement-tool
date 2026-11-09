# Sửa theo code review — duoc-CR-719 Thanh toán nghỉ phép

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | fullstack-developer | Hiệu lực | duoc-CR-719 |

Nguồn: [code-review.md](code-review.md). Chưa commit. Thêm ba sửa nhỏ do bên tài liệu báo (cuối bảng).

## Đã sửa

| Mã | Sửa gì | Nơi sửa |
|---|---|---|
| H1 | Người nhận tiền KHÔNG sửa / gửi duyệt / duyệt / từ chối / ghi chi YCTT nghỉ phép của chính mình: 403 "Không tự xử lý yêu cầu thanh toán nghỉ phép của chính mình…". Không ngoại lệ (quản trị cũng bị nếu là người nhận). Chốt ở service nên phủ web, v1, công cụ AI. | `payment_request/leave_encashment_payout.py` (`ensure_not_payee`), `service.py` (`update_request`, `set_status`) |
| M1 | Thêm `tab_leave_balance.encashed_carried_days` (phần mang sang đã thanh toán) + `tab_leave_encashment.carried_paid_days` (chốt lúc duyệt, để hủy trả đúng). `expire_carried` tính `consumed = used + pending + encashed_carried_days`. Chỉ lý do Nghỉ việc lấy từ mang sang (mang sang tiêu trước); cuối năm = 0 (D6a nguyên vẹn). Hủy phiếu Đã duyệt trả cả hai cột. | `balance_model.py`, `encashment_model.py`, `carryover_service.py`, `encashment_math.py`, `encashment_balance.py`, `encashment_transitions.py`, migration `lvenc719` (sửa tại chỗ, chưa lên môi trường nào) |
| M2 | `active_key = "<nv>:<loại>:<năm>:<lý do>"`: tối đa một phiếu cuối năm + một phiếu nghỉ việc còn hiệu lực. `update` đổi lý do thì đổi khóa + kiểm trùng + bắt `IntegrityError`. | `encashment_service.py` |
| M3 | `change_tracker` che theo DÒNG: `tab_payment_request.total` và `tab_payment_request_line.amount/allocated_amount` ghi `is_masked`, không giá trị trước/sau (cả snapshot thêm/xóa) khi nguồn là `leave_encashment`; YCTT thường giữ nguyên. Thân request `/api/payment-requests/{id}...` che `amount/total/allocated_amount`. | `core/change_tracker.py`, `core/logging_policy.py` |
| L1 | Duyệt thẳng / qua bộ máy: kiểm dòng quỹ có mặt (không khóa) -> chiếm phiếu -> mới khóa dòng quỹ. Từ chối / hủy vốn đã chiếm phiếu trước. Cùng thứ tự "phiếu rồi quỹ" nên hai lượt đua nhau ra 409, không deadlock. | `encashment_transitions.py` (`approve_now`) |
| L2 | `set_status` của YCTT nghỉ phép đọc lại dòng `populate_existing` + `FOR UPDATE` (MySQL) và 404 nếu đã xóa mềm. Hủy phiếu vốn khóa cùng dòng nên hai chiều đều có khóa. | `leave_encashment_payout.py` (`lock_live_payout`), `service.py` |
| L3 | Chế độ bộ máy duyệt: người có `leave_encashment.cancel` trong phạm vi (cổng ở controller) rút phiên HỘ người trình (nhân sự nhận). Ghi lý do "Người có quyền hủy (tài khoản #id) hủy hộ…". Vẫn chặn khi đã có người ký (luật `withdraw`). `leave_request` không có đường này nên làm bản tối thiểu. | `encashment_approval_bridge.py` |
| L4 | Listener `after_commit` bỏ qua `in_nested_transaction()`, chạy đúng một lần ở commit thật (cờ, không gỡ listener giữa lúc phát sự kiện). | `encashment_transitions.py` |
| L5 | `useLeaveApprovalDecision({ alsoInvalidate })`; thanh toán nghỉ phép truyền `queryKeys.finance.all`. Nút Duyệt thẳng ẩn khi phiếu là của chính người xem (`isOwnRequest`). | `hooks/use-leave.ts`, `leave-engine-decision-actions.tsx`, `leave-encashment-decision-actions.tsx`, `types/leave-encashment.ts`, `leave-encashment-detail-page.tsx` |
| L6 | Chuông Nhân sự khi kế toán từ chối không còn lý do tự do: "Kế toán từ chối chi — xem lý do ở Yêu cầu thanh toán <mã>…". | `notification/service.py`, `leave_encashment_payout.py` |
| (1) | Câu 422 loại nghỉ không cho thanh toán gọi đúng tên ô: "Cho phép thanh toán nghỉ phép". | `encashment_service.py` |
| (2) | Câu 409 trùng phiếu nêu lý do (cuối năm / nghỉ việc) và "chỉ hủy (hoặc bị từ chối) phiếu đó mới lập được phiếu mới". Bài kiểm cũ cập nhật. | `encashment_service.py` |
| (3) | Mô tả skill `nghi-phep` thêm "thanh toán nghỉ phép (đổi ngày phép chưa nghỉ ra tiền)". | `ai_skill/handbook_seed.py` |

## Lệch so với yêu cầu (cần chủ dự án biết)

1. **H1, vế "nhánh `self` của chốt xem chỉ cho READ": KHÔNG làm.** Làm vậy người nhận ra 404 ở `_scoped` trước khi tới service, mất câu 403 rõ nghĩa mà yêu cầu cũng đòi; chốt service đã chặn mọi đường ghi bất kể phạm vi nên lớp thứ hai không thêm an toàn. Nếu vẫn muốn: thêm tham số `action` cho `payout_visibility_cond` và loại hàng `payee_employee_id = nhân sự của tôi` khi `action != read`.
2. **M3, thân request**: tầng log không tra DB nên không biết nguồn phiếu -> che `amount/total/allocated_amount` ở MỌI đường `/api/payment-requests/{id}...` (kể cả YCTT mua hàng). Dấu vết số tiền YCTT mua hàng còn ở `change_tracker` (không che) và `audit`. Cần che theo nguồn thì phải tra DB trong middleware (không làm).
3. **M1, còn một điểm lệch nhỏ**: khi phiếu CHỜ duyệt, `pending_days` vẫn coi là đã tiêu phần mang sang (cả phiếu cuối năm), nên qua hạn lúc phiếu còn treo thì mang sang không bị thu hồi; tới khi duyệt/từ chối thì đúng lại ở lượt đọc kế. Không âm quỹ; không sửa.

## Câu hỏi mở "tính theo tỷ lệ tới resign_date"
KHÔNG làm (theo chỉ đạo): phiếu nghỉ việc vẫn trả hết quỹ dùng được; Nhân sự giảm số ngày bằng tay nếu cần.

## Kiểm
- Bài mới: `test/backend/test_thanh_toan_nghi_phep_review_cr719.py` (21 bài): H1 qua controller (người nhận có `payment_request` write + approve nhận 403 ở sửa / gửi / duyệt / từ chối / chi), H1 qua service, M1 (12 + 5 mang sang, trả 17, qua hạn còn 0; cuối năm; hủy), M2 (cuối năm đã chi rồi lập nghỉ việc; trùng nghỉ việc 409; trùng cuối năm 409; đổi lý do), M3 (change_tracker + đường dẫn), L1 (thứ tự khóa), L2, L3, L4, câu 422.
- Sửa bài cũ: `active_key` có hậu tố lý do; chuông từ chối không còn lý do; bài trợ lý AI nhập tiền bằng tài khoản không phải người nhận.
- pytest (từng nhóm, một tiến trình): 4 tệp CR-719 + 8 tệp YCTT (226 xanh); nhật ký / change_tracker + `pham_vi_khai_du_b07` / `duong_vong` / `luat_bat_bien` + kết sổ cuối năm (313 xanh); nhóm nghỉ phép / trợ lý / skill AI / báo cáo (194 xanh).
- Frontend: `npm run typecheck` (host) 0 lỗi; eslint các tệp đổi 0 lỗi; vitest `src/modules/hr` 1588 bài xanh (148 tệp), `src/modules/finance` 81 bài xanh.
- SQLite không tái hiện được khóa `FOR UPDATE` / deadlock: L1 kiểm bằng thứ tự gọi, L2 bằng đọc lại dòng cũ; chưa chạy trên MySQL.

## Tài liệu cần đồng bộ (không thuộc phần này)
`.claude/rules/hr-leave.md` (D4: "người, loại, năm" -> thêm "lý do"), `doc/erp/hrm/02-nghi-phep.md` §16 (cột mới, D4/M2, M1), `doc/erp/thu-mua/tai-lieu-ky-thuat/api.md` (403 người nhận), HDSD (Hủy hộ trong luồng; chuông từ chối không kèm lý do).

**Status:** DONE_WITH_CONCERNS
**Summary:** Sửa H1, M1, M2, M3, L1-L6 và 3 việc nhỏ của bên tài liệu; 21 bài mới + 733 bài liên quan xanh, typecheck/eslint sạch.
**Concerns/Blockers:** Hai lệch ở mục "Lệch so với yêu cầu" (không làm vế self-read-only của H1; che số tiền ở thân request cho mọi YCTT). Migration `lvenc719` được sửa tại chỗ (thêm 2 cột) nên máy đã chạy bản cũ phải `downgrade`/`upgrade` lại hoặc thêm cột tay.
