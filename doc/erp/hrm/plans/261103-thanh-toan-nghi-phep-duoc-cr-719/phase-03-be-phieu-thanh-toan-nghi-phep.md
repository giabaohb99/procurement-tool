# Phase 03 — BE: Phiếu thanh toán nghỉ phép, duyệt, AI

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | backend | Nháp | duoc-CR-719 |

## Context
- [plan.md](plan.md) D3–D9. Khuôn chép: `leave/comp_request_{model,schema,service,controller}.py`, `leave/comp_approval_bridge.py`
  (claim nguyên tử, `HookVeto`, `can_read_request`, `entity_hooks.register*`). Quỹ: `balance_service.{ensure_balance,
  available_days, get_balance}` (khóa `for_update`). Lập hộ: `request_service.{resolve_leave_taker, ensure_can_create_for}`.
- ERPNext: `leave_encashment.py` `set_actual_encashable_days`, `set_encashment_days`, `on_cancel`.
- Hợp đồng YCTT: [phase-02](phase-02-be-yctt-nguon-nghi-phep.md) mục **Hợp đồng**.

## Luật tính (hàm thuần mới `leave/encashment_math.py`)
```
unused_carried = max(0, carried_days − used_days − pending_days)        # "mang sang tiêu trước" (carryover_service)
year_end:   base = available − unused_carried (D6a) − non_encashable_days ; cap = max_encashable_days − đã_thanh_toán_năm
resignation: base = available ; không trần (D5a)
encashable = clamp(base, 0, cap nếu cap > 0 và year_end)                # available = balance_service.available_days(row)
```
`đã_thanh_toán_năm` = `encashed_days` của dòng (D4a nên không có phiếu chờ khác cùng khóa). `days` bước 0,5, `0 < days ≤ encashable`;
bỏ trống `days` lúc lập → lấy `encashable` (ERPNext). Ứng phép âm → encashable 0.

## Luật nghiệp vụ (`leave/encashment_service.py`, mọi đổi trạng thái qua `claim` nguyên tử như phiếu nghỉ bù)
1. **Lập** (Nháp): người nhận = `resolve_leave_taker` + `ensure_can_create_for(..., "leave_encashment")`; loại đang dùng,
   `allow_encashment` + `counts_balance`; `balance_year ∈ {năm nay, năm trước}` (D9a); `reason_kind=2` bắt `employee.resign_date`
   (422 *Nhập ngày nghỉ việc trên hồ sơ trước*); nhân sự `status="resigned"` thì chỉ nhận lý do 2; chưa có dòng quỹ → 422 (không
   tự cấp quỹ năm cũ); `active_key = "{emp}:{type}:{year}"` UNIQUE → 409 *Đã có phiếu thanh toán … còn hiệu lực* (D4a);
   `encashment_date` mặc định `vn_today()`; snapshot `balance_snapshot = available`, `encashable_snapshot`.
2. **Sửa / xóa**: chỉ Nháp / Trả về; xóa mềm chỉ Nháp (`active_key = NULL`).
3. **Gửi duyệt**: `claim` → Chờ duyệt; `ensure_balance(..., for_update=True)`, tính lại encashable (trên số đã khóa), `days >` → 422;
   `pending_days += days`; ghi lại snapshot; `instance_service.start(... entity_title=f"Thanh toán nghỉ phép {code} — {days:g} ngày")`.
4. **Duyệt** (`_on_approved` qua `HookVeto` / duyệt thẳng `HTTPException`): `claim` Chờ duyệt → Đã duyệt; dòng quỹ khóa:
   `pending −= days` (kẹp 0), `encashed_days += days`; `create_payout_request` → `payment_request_id`. Lỗi bất kỳ sau khi chiếm →
   ném lại để cả giao dịch cuộn (khuôn `comp_approval_bridge.approve_now`).
5. **Từ chối / trả về / rút**: `claim` + trả `pending` trong cùng một hàm `_release_and_set` (không chép ba bản). Rút → Nháp.
6. **Hủy**: Nháp / Chờ duyệt / Trả về → rút phiên duyệt (`withdraw_running_approval`) rồi Đã hủy (+ trả `pending` nếu đang giữ chỗ);
   Đã duyệt → chỉ khi `payout_allows_cancel(payout_state(...))` (D7a), rồi `encashed_days −= days` (kẹp 0) + `void_draft_payout`
   nếu YCTT còn Nháp; YCTT Chờ duyệt / Đã duyệt → 400 *YCTT {code} đang ở {trạng thái} — kế toán từ chối YCTT trước*; Đã chi → 400.
7. **Chặn tự duyệt**: `self_approval_policy.ALWAYS_STRICT_ENTITIES` thêm `leave_encashment`; duyệt thẳng gọi `ensure_not_self_approval`.
8. **Kết sổ cuối năm**: không sửa `carryover_service` — phiếu giữ chỗ không bị mang đi; bị từ chối sau kết sổ thì lượt kết sổ sau vét
   (hành vi sẵn có). Ghi rõ trong docstring `encashment_service`.

## API `/api/leave-encashments` (tags `["leave"]`, docstring tiếng Việt: dòng đầu tóm tắt, dòng sau quyền + lỗi riêng)
`GET /` (lọc `status, employee_id, company_id, department_id, leave_type_id, balance_year, reason_kind, q`) · `GET /to-approve`
(đăng ký TRƯỚC `/{id}`) · `GET /preview?employee_id&leave_type_id&balance_year&reason_kind` (số dư, phần mang sang chưa dùng, trần,
encashable — chỉ đọc, gác `leave_encashment.create`) · `GET /{id}` · `POST /` · `PATCH /{id}` · `DELETE /{id}` · `POST /{id}/submit`
· `/approve` · `/reject?reason=` · `/cancel?reason=` (`Query(max_length=500)`). Chi tiết trả `payment = payout_state(...)`;
`payment.total` CHỈ khi người xem là chính chủ (`sensitive.is_self`) hoặc `get_scoped(PaymentRequest, "payment_request")` thấy YCTT.
Schema mới `leave/encashment_schema.py` (`note: str = Field("", max_length=1000)`, `days: float | None = Field(None, gt=0, le=366)`,
`balance_year` 2000–2100, `reason_kind` thuộc bộ mã).

## Nối dây
`main.py` (router + nhập `encashment_approval_bridge` cho hook) · `approval/task_notification.py` ENTITY_LABELS **Thanh toán nghỉ
phép**, ENTITY_LINKS `/hr/leave-encashments/{id}` · `approval/permission_approvers.py` · `approval/report_service.py`
`APPROVAL_REPORT_SOURCES` · `approval/self_approval_policy.py`.
**AI (D8a)**: `assistant/tools/leave_tool.py` — `_balances` trả `encashed_days`, luật loại `allow_encashment`,
`max_encashable_days`, `non_encashable_days`; thêm `encashments` (phiếu của người hỏi, năm đang xem, chỉ số ngày + trạng thái +
trạng thái chi, KHÔNG số tiền); sửa mô tả trường. `assistant/service.py` câu hướng dẫn một dòng.

## Bài kiểm `test/backend/test_nghi_phep_thanh_toan_cr719.py`
Toán (bảng ca ERPNext: non 4/bal 10 → 6; max 3 → 3; cả hai; mang sang 5 không tính khi cuối năm, tính khi nghỉ việc; trần năm trừ
đã thanh toán; MONTHLY giữ phần chưa tới tháng) · lập: loại không cho phép 422, năm 2 năm trước 422, nghỉ việc thiếu `resign_date`
422, trùng `active_key` 409 · gửi: giữ chỗ, vượt 422, hai lượt song song chỉ một qua (claim) · duyệt: quỹ đổi đúng, YCTT Nháp sinh
đúng người nhận + `created_by=0`, `HookVeto` khi hỏng thì không nửa chừng · từ chối / trả về / rút trả `pending` · hủy: theo bốn trạng
thái YCTT · chặn tự duyệt (cả bộ máy lẫn duyệt thẳng) · người có việc duyệt đọc được phiếu ngoài phạm vi · `payment.total` ẩn với
người duyệt Nhân sự · ENTITY_LABELS/LINKS (sửa `test_nghi_phep_thong_bao_duyet.py` nếu nó liệt kê cứng) · `my_leave_summary` có
`encashed_days`, không có tiền. Sửa `test_pham_vi_duong_vong.py` (tổng hiện **95** + số dòng mới, ghi lý do),
`test_canh_do_dai_o_chu_cr538.py` nếu bài đòi khai schema mới, `test_pham_vi_bo_may_duyet_xuyen_suot.py` nếu thêm công cụ AI.

## Tệp sở hữu
Tạo: `backend/app/modules/leave/{encashment_math,encashment_service,encashment_controller,encashment_approval_bridge,
encashment_schema}.py`, `test/backend/test_nghi_phep_thanh_toan_cr719.py`. Sửa: `backend/app/main.py`,
`backend/app/modules/approval/{task_notification,permission_approvers,report_service,self_approval_policy}.py`,
`backend/app/modules/assistant/tools/leave_tool.py`, `backend/app/modules/assistant/service.py`,
`test/backend/{test_pham_vi_duong_vong,test_canh_do_dai_o_chu_cr538,test_nghi_phep_thong_bao_duyet}.py`.
Mỗi tệp mới < 200 dòng (tách `encashment_service` thành `encashment_service.py` + `encashment_transitions.py` nếu vượt).

## Xong khi
Bài kiểm phase + `test_nghi_phep_nghi_bu_cr715.py` + `test_assistant_nghi_phep_erpnext_cr715.py` + bài phạm vi xanh; `/api/docs`
hiện nhóm `leave` có đủ 11 đường kèm mô tả tiếng Việt.

## Rủi ro
| Rủi ro | K × T | Giảm |
|---|---|---|
| Hook duyệt tạo YCTT hỏng → phiên Đã duyệt, phiếu Chờ duyệt | TB × Cao | `HookVeto` + `fire` tự rollback (CR-715); bài kiểm ép lỗi |
| Hủy phiếu khi kế toán đang duyệt YCTT | TB × Cao | Chặn theo trạng thái YCTT đọc có khóa trong cùng giao dịch |
| Đua gửi duyệt trừ quỹ hai lần | TB × Cao | `claim` + khóa dòng quỹ; active_key UNIQUE |
