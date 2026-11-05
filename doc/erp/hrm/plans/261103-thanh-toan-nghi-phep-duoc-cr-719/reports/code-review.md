# Code review — duoc-CR-719 Thanh toán nghỉ phép (backend + frontend)

| Bản | Ngày | Người phụ trách | Trạng thái | CR liên quan |
|---|---|---|---|---|
| 1 | 03/11/2026 | code-reviewer | Hiệu lực | duoc-CR-719 |

## Phạm vi
- Backend: `leave/encashment_*` (9 tệp), `payment_request/{hr_payout_guard,leave_encashment_payout,service,controller,export,model}.py`,
  `core/{scoping,permissions,entity_models}.py`, `approval/*` (4 tệp), `notification/service.py`, `assistant/tools/leave_*`,
  `employee/references.py`, `seed.py`, migration `lvenc719`.
- Frontend: `hr/*encashment*`, `leave-engine-decision-actions`, `finance/components/payment-request-leave-encashment-*`,
  `payment-request-detail-page`, `payment-request-print-page`, routes / query keys / permission groups.
- Kiểm đã chạy: 3 tệp pytest CR-719 = **88 xanh**; `npm run typecheck` (host) = **0 lỗi**; không có « » trong mã mới.
- Hai lỗi dưới đây (**H1**, **M1**) đã **xác nhận bằng bài dò** (pytest tạm trong `/tmp` của container, đã xóa, không sửa repo).

## Đánh giá chung
Thiết kế chắc: chốt xem YCTT đặt đúng một chỗ (`scope_condition`) nên mọi đường `apply_scope` / `get_scoped` /
danh sách người duyệt / tập dữ liệu AI / nhật ký theo entity đều được phủ; chiếm trạng thái bằng UPDATE có điều kiện;
`active_key` UNIQUE; HookVeto cuộn đúng; YCTT nghỉ phép chặn xóa / hoàn tiền / cập nhật theo công nợ / tạo tay. Đã rà
các đường đọc YCTT không qua `scope_condition` (supplier, payable, cycle_specs, central_purchasing, report_summary, audit)
— không thấy đường rò số tiền nào qua API đọc thường. Các vấn đề còn lại nằm ở **quyền ghi của chính người nhận**,
**tương tác với hết hạn phần mang sang**, **D4 đụng D5**, và **nhật ký hệ thống**.

---

## High

### H1. Người nhận tiền tự nhập số tiền, tự duyệt, tự ghi chi YCTT của chính mình
- **Chỗ:** `backend/app/modules/payment_request/hr_payout_guard.py:28-31` (chốt chỉ hỏi phạm vi `leave_encashment.read`,
  mà phạm vi đó có nhánh `self` = `employee_id`); `payment_request/controller.py:276-280` (PATCH), `:350-356` (submit),
  `:359-365` (approve), `:379-385` (pay); `payment_request/leave_encashment_payout.py:189-215` (`apply_payout_update`)
  — không chỗ nào so `user.employee_id` với `req.payee_employee_id`.
- **Kịch bản (đã dò):** seed cấp mọi vai trò `leave_encashment` `own` (có `self`). Nhân sự A là kế toán / Quản lý thu
  mua phòng (YCTT `write` + `approve` phạm vi company). Phiếu thanh toán nghỉ phép của A được Nhân sự duyệt → YCTT
  Nháp tiền 0. A mở YCTT (thấy nhờ `self`), nhập 99.000.000, gửi duyệt, duyệt, ghi Đã chi — cả chuỗi đi qua
  `get_scoped(..., "write"/"approve")` và `set_status` không lỗi. Bài dò ra `status paid total 99000000.00`.
  Nhân viên thu mua (`payment_request.write` company, không có approve) vẫn tự đặt được số tiền của chính mình trước khi gửi.
- **Tác động:** tự quyết tiền lương trả cho chính mình; trái tinh thần "luôn chặn tự duyệt" mà phiếu nghỉ phép đã áp.
- **Sửa:** chặn ở tầng service cho nguồn nghỉ phép (phủ cả web, v1, MCP):
  ```python
  # leave_encashment_payout.py
  def ensure_not_payee(req, user) -> None:
      emp = getattr(user, "employee_id", 0) or 0
      if is_payout(req) and emp and emp == int(req.payee_employee_id or 0):
          raise HTTPException(403, "Không tự xử lý yêu cầu thanh toán nghỉ phép của chính mình")
  ```
  gọi ở `update_request` (khi `is_pay`) và `set_status` cho `submitted/approved/cancelled/paid` (cần truyền `user`
  hoặc tra `User` theo `user_id`). Phương án gọn hơn: trong `payout_visibility_cond` dùng phạm vi KHÔNG có nhánh
  `self` khi `action != "read"` (người nhận vẫn xem được, không ghi được). Thêm bài kiểm ca này.

---

## Medium

### M1. Thanh toán do nghỉ việc gồm cả phần mang sang, sau hạn mang sang quỹ bị trừ LẦN HAI → còn lại âm
- **Chỗ:** `backend/app/modules/leave/encashment_math.py:55-56` (nghỉ việc: nền = `available`, gồm phần mang sang, D5a);
  `leave/carryover_service.py:74-76` (`consumed = used + pending`, không tính `encashed_days`);
  `leave/encashment_transitions.py:102-103` (duyệt chuyển `pending` sang `encashed_days`).
- **Kịch bản (đã dò):** quỹ năm nay `allocated 12`, `carried 5` (hạn mang sang tháng 12), có `resign_date`. Lập phiếu
  lý do Nghỉ việc → 17 ngày, duyệt → còn lại 0. Qua hạn, bất kỳ màn đọc quỹ nào gọi `expire_carried`: `consumed = 0`
  → thu hồi 5 ngày mang sang → **còn lại = -5**. Cùng hiện tượng với người có `resign_date` tương lai (đang báo trước,
  hạn mang sang thường là cuối quý 1): quỹ âm, báo cáo quỹ âm, đơn nghỉ trong thời gian báo trước bị chặn sai số.
  Trong lúc phiếu còn Chờ duyệt thì ngược lại: `pending` của phiếu được tính là "đã tiêu phần mang sang" nên hạn qua
  mà phần mang sang không bị thu hồi, tới lúc duyệt mới lệch.
- **Sửa:** cho `expire_carried` coi ngày đã thanh toán là đã tiêu (đúng thứ tự "mang sang tiêu trước" khi lý do
  nghỉ việc): `consumed = used + pending + encashed_days`. Với cuối năm (D6a phần thanh toán không lấy từ mang sang)
  công thức này làm phần mang sang sống lâu hơn thực tế, nên chính xác hơn là lưu riêng số ngày mang sang đã thanh
  toán (ví dụ `encashed_carried_days`, chỉ khác 0 khi lý do nghỉ việc) và cộng nó vào `consumed`. Thêm bài kiểm
  nghỉ việc + phần mang sang + qua hạn.

### M2. D4 (một phiếu còn hiệu lực / người, loại, năm) chặn khoản thanh toán nghỉ việc bắt buộc theo luật
- **Chỗ:** `backend/app/modules/leave/encashment_service.py:31-32` (`INACTIVE_STATUSES` không gồm APPROVED nên phiếu
  đã duyệt giữ `active_key` vĩnh viễn), `:124-126` (409).
- **Kịch bản:** tháng 11 nhân sự E được thanh toán phép dư cuối năm 2026 (Đã duyệt, kế toán Đã chi). Tháng 12 E nghỉ
  việc, còn ngày phép năm 2026 chưa nghỉ (phần mang sang, phần giữ lại `non_encashable_days`, phần vượt trần). Lập
  phiếu lý do Nghỉ việc năm 2026 → 409 trùng. Không hủy được phiếu cũ vì YCTT đã chi (D7a). Không còn đường nào trong
  hệ để trả khoản Điều 113 khoản 3 bắt buộc.
- **Sửa (chọn một, cần anh Được chốt vì đụng D4a):** (a) nhả `active_key` khi phiếu sang Đã duyệt — trần năm vẫn đúng
  vì `annual_cap` đọc `row.encashed_days` (đã cộng dồn phiếu đã duyệt), `active_key` chỉ còn chặn hai phiếu cùng treo;
  (b) đưa `reason_kind` vào khóa cho lý do Nghỉ việc (`"{emp}:{type}:{year}:r2"`). Đồng thời sửa câu gợi ý ô
  `max_encashable_days` (`leave-type-encashment-fields.ts:39` ghi "cộng dồn mọi phiếu đã duyệt", hiện không thể có
  hai phiếu đã duyệt cùng năm).

### M3. Nhật ký hệ thống (khóa `change_log`) là đường vòng đọc số tiền YCTT nghỉ phép
- **Chỗ:** `backend/app/core/change_tracker.py:111-113` — danh sách che theo bảng chỉ có `tab_employee` và
  `tab_labor_contract`; `tab_payment_request.total` và `tab_payment_request_line.amount` vẫn ghi giá trị trước/sau.
  Thân PATCH `/api/payment-requests/{id}` (có `amount`) cũng không nằm trong `logging_policy.sensitive_keys_for_path`.
- **Kịch bản:** người có `change_log.read` (không cần `leave_encashment`) mở chi tiết nhật ký dòng PATCH YCTT nghỉ phép
  → thấy `amount 0 → 4.615.000` + mã phiếu TTP… (ghi chú YCTT ghi rõ số ngày) → ra lương ngày. Chính tệp này đã ghi luật
  "nhật ký hệ thống không được thành đường vòng đọc lương" cho HĐLĐ.
- **Sửa:** che theo DÒNG cho nguồn nghỉ phép: trong change_tracker, bỏ giá trị trước/sau của `total` / `amount` khi
  phiếu (hoặc phiếu cha của dòng) có `source_type == "leave_encashment"` (ghi `***`); thêm `amount`/`total` vào khóa che
  thân yêu cầu cho đường `/api/payment-requests/` khi phiếu là nguồn nghỉ phép (hoặc che luôn cho mọi YCTT nếu chấp nhận
  mất dấu vết tiền ở log yêu cầu — dấu vết nghiệp vụ vẫn còn ở audit theo entity, vốn đã qua `scope_condition`).
  Nếu anh Được coi `change_log` là khóa quản trị ngang admin thì ghi rõ ngoại lệ đó vào D1.

---

## Low

### L1. Đảo thứ tự khóa: duyệt thẳng với từ chối / hủy cùng lúc → deadlock MySQL 1213 → 500
- **Chỗ:** `leave/encashment_transitions.py:95-100` (duyệt: khóa dòng quỹ rồi UPDATE phiếu) so với `:61-65` và
  `:134-142` (từ chối / hủy: UPDATE phiếu rồi khóa dòng quỹ qua `balance_service.release` / `get_balance(for_update)`).
- **Kịch bản:** hai người Nhân sự cùng bấm Duyệt và Từ chối một phiếu Chờ duyệt (chế độ duyệt thẳng). Dữ liệu không hỏng
  (một giao dịch bị InnoDB giết), nhưng một người nhận 500 thay vì 409.
- **Sửa:** ở `release_and_set` và `cancel` khóa dòng quỹ (`get_balance(..., for_update=True)`) TRƯỚC khi `claim`, như
  `approve_now`; hoặc bắt `OperationalError 1213` đổi thành 409 `CONFLICT_MESSAGE`.

### L2. Khóa YCTT lúc hủy phiếu chỉ chặn được một chiều
- **Chỗ:** `payment_request/leave_encashment_payout.py:100-102` (hủy đọc YCTT FOR UPDATE) nhưng
  `payment_request/service.py:658-677` (`set_status`) đọc không khóa và UPDATE theo khóa chính, không điều kiện.
- **Kịch bản:** Nhân sự hủy phiếu Đã duyệt (YCTT Nháp) đúng lúc kế toán bấm Gửi duyệt YCTT. Nếu lượt hủy khóa trước:
  YCTT bị xóa mềm + trả ngày, rồi UPDATE của kế toán vẫn ghi `status = submitted` lên YCTT đã xóa và trả "Đã gửi duyệt".
  Không mất tiền (YCTT đã xóa không mở được nữa) nhưng kế toán nhận thông báo sai và dữ liệu lệch.
- **Sửa:** cho các chuyển trạng thái YCTT nghỉ phép (ít nhất submitted/approved/paid) dùng UPDATE có điều kiện
  `WHERE id=? AND status IN allowed AND is_deleted=0` (đếm 0 dòng → 409), hoặc `get_request(..., for_update=True)`.

### L3. Nút Hủy ở chế độ bộ máy duyệt gần như luôn 403
- **Chỗ:** `leave/encashment_approval_bridge.py:51` + `:67-68` (`submitter_employee_id = obj.employee_id`) và
  `approval/action_service.py:241` (chỉ người trình mới rút); frontend `hr/types/leave-encashment.ts:206` hiện Hủy cho
  phiếu Chờ duyệt có phiên khi có quyền `cancel`.
- **Kịch bản:** người Nhân sự (`cancel` all) bấm Hủy phiếu Chờ duyệt đang chạy luồng của nhân sự E → `withdraw` 403
  "Chỉ người trình duyệt mới rút lại được". Nhân viên E không có `cancel` theo seed. Kế thừa nguyên khuôn phiếu nghỉ bù.
- **Sửa:** ẩn Hủy khi `approval_instance_id > 0` và người xem không phải người nhận; hoặc ở backend hủy phiên bằng một
  hàm hủy quản trị thay vì `withdraw`. Ghi vào HDSD: muốn dừng phiếu đang trong luồng thì người duyệt Từ chối / Trả về.

### L4. Listener `after_commit` không có chốt savepoint
- **Chỗ:** `leave/encashment_transitions.py:86`.
- **Rủi ro:** SQLAlchemy 2.0.35 phát `after_commit` cả khi nhả `begin_nested`; nếu sau này có savepoint chen giữa
  `approve_now` và commit thật (cổng MCP ghi audit bằng savepoint, `approver_candidates`…), listener `once=True` chạy sớm,
  phiên mới không thấy YCTT chưa commit → chuông kế toán mất im lặng. Hiện chưa có đường nào như vậy.
- **Sửa:** trong `run(session)` bỏ qua khi `session.in_nested_transaction()` (giống `notification/email_queue._flush`),
  và chỉ gỡ listener khi chạy thật thay vì `once=True`.

### L5. Frontend nhỏ
- `hr/components/leave-encashment-decision-actions.tsx:38` dùng `useLeaveApprovalDecision` (chỉ dọn `hr.all` +
  `approval.all`); duyệt chặng cuối qua bộ máy sinh YCTT nhưng `finance.all` không được dọn → danh sách YCTT cũ tới khi
  hết `staleTime`. Sửa: thêm `queryKeys.finance.all` khi entity là `leave_encashment`.
- `hr/types/leave-encashment.ts:204`: `directDecision` không loại phiếu của chính người xem → Nhân sự mở phiếu của mình
  thấy nút Duyệt rồi ăn 403. Truyền `isSelf` (`request.employee_id === user.employee_id`) vào hàm thuần.

### L6. Chuông kế toán từ chối chuyển nguyên lý do tự do cho Nhân sự
- **Chỗ:** `notification/service.py` nhánh `pay_leave_rejected` (+ `leave_encashment_payout.py:178-181`).
- Lý do do kế toán gõ (ví dụ "số tiền 4.615.000 sai") đi thẳng tới người duyệt Nhân sự — người không được thấy số tiền
  theo D1a. Chấp nhận được nếu ghi chú ở màn từ chối nhắc "không ghi số tiền vào lý do".

---

## Ca biên đã rà, không thấy lỗi
- Duyệt hai lần / bấm đúp: `try_claim` + `create_payout_request` kiểm trùng; gửi duyệt đúp thua ở `claim` sau khi chờ
  khóa dòng quỹ.
- HookVeto: `approve_now` bọc mọi lỗi sau khi chiếm thành `error_cls`, `entity_hooks.fire` cuộn tại nguồn.
- Từ chối / trả về / rút / hủy Chờ duyệt: một hàm `release_and_set`, `release` kẹp 0.
- D6: cuối năm trừ phần mang sang chưa dùng; D9: năm trước đã kết sổ thì `available = 0`.
- Tự duyệt: `ALWAYS_STRICT_ENTITIES` + `ensure_not_self_approval` ở duyệt thẳng.
- Giới hạn đầu vào: `note` 1000 / `decision_note` 500 khớp cột; `days` `gt 0 le 366` + bước 0,5 ở service; số tiền
  `0..9.999.999.999.999`; năm 2000..2100; `reason_kind` có validator.
- Migration chạy lại được, cột mới `NOT NULL` có `server_default`.
- Frontend: hàng rào route qua mục menu `entity: 'leave_encashment'`; nút `type="button"`; chặn bấm đúp bằng `useRef`;
  "Gửi duyệt" = lưu rồi gửi, lưu xong gửi hỏng vẫn chuyển sang phiếu nháp; số tiền chỉ vẽ khi `payment.total !== null`;
  bản in ghi "kế toán tự điền" khi `bank_hidden`.

## Câu hỏi còn mở
1. D5 trả "hết ngày chưa nghỉ" nhưng quỹ năm nay của loại cấp đủ đầu năm là CẢ NĂM: người nghỉ việc tháng 2 được thanh
   toán đủ 12 ngày. Có cần tính theo tỷ lệ tháng làm việc tới `resign_date` không? (hiện chỉ loại cộng dần theo tháng
   mới tự đúng).
2. Lý do Nghỉ việc chỉ cần `resign_date` khác rỗng — kể cả ngày ở xa tương lai. Có giới hạn (ví dụ trong 60 ngày tới) không?
3. Sau deploy chưa vai trò nào ngoài admin có `leave_encashment.read` phạm vi rộng + quyền YCTT, nên chuông
   `pay_leave_created` rơi về quản trị và không ai ngoài admin xử lý được YCTT nghỉ phép cho tới khi tick tay vai trò
   kế toán (D-018). Đã có kế hoạch tick vai trò nào trên prod chưa?
4. `change_log` có được coi là khóa ngang quản trị (chấp nhận thấy tiền) không — quyết định cho M3.

**Status:** DONE_WITH_CONCERNS
**Summary:** Chốt xem YCTT phủ đủ đường đọc API; còn 1 High (người nhận tự nhập tiền / tự duyệt / tự chi YCTT của mình, đã
dò), 3 Medium (quỹ âm khi nghỉ việc gồm phần mang sang rồi qua hạn — đã dò; D4 chặn khoản nghỉ việc sau khi đã thanh
toán cuối năm; nhật ký `change_log` lộ số tiền), 6 Low. Test CR-719 88 xanh, typecheck 0 lỗi.
**Concerns/Blockers:** H1 nên sửa trước khi lên prod; M2 cần anh Được chốt lại D4.

Thứ tự theo mức độ: **H1** > **M1** > **M2** > **M3** > **L1** > **L2** > **L3** > **L4** > **L5** > **L6**.
