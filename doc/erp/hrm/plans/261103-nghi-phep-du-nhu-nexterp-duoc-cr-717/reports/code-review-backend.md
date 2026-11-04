# Code review BE — duoc-CR-717 (chính sách + phân bổ + báo cáo 30 + ma trận + cấp quỹ có lọc)

Phạm vi: diff chưa commit `backend/` + 4 tệp test CR-717. Tests: 4 tệp CR-717 = 143 xanh; gác báo cáo / BB4 / B07 xanh;
`test_canh_do_dai_o_chu_cr538` đỏ 1 bài do customs/forum (có sẵn, không phải CR-717).

## HIGH

### H1. MySQL REPEATABLE READ: khóa `tab_employee` rồi đọc phân bổ bằng SELECT thường → chồng ngày lọt + `allocated_days` sai
- `policy_assignment_service.py:42-47` (`lock_employees`), `:120-121`, `:131-132`, `:167-169`; `policy_assignment_plan.py:88`;
  `policy_allocation.py:42-48` (đọc phân bổ trong `reconcile_balances` → `allocated_days`).
- Engine không đặt isolation → RR. Trong request đã có đọc nhất quán TRƯỚC khóa (`get_current_user`,
  `_employee_query(...).first()`, `_policy_or_404`) → ảnh chụp MVCC cố định từ đó. T1, T2 cùng phân bổ nhân sự X (T1: từ
  01/07, T2: từ 01/09, không `close_previous`) → T2 chờ khóa, T1 commit → T2 `load_assignments` vẫn đọc ảnh chụp cũ, không
  thấy lượt của T1 → không 409 → chèn được (UNIQUE chỉ bắt trùng `effective_from`) → 2 phân bổ chồng ngày. Bản lành hơn
  (hai lượt KHÔNG chồng, ví dụ hai HR chạy bulk nửa đầu / nửa cuối năm): `reconcile_balances` của T2 tính lại chỉ với phân bổ
  của mình rồi GHI ĐÈ `allocated_days` T1 vừa ghi → quỹ sai, không ai báo. Khóa dòng quỹ `for_update=True` không cứu vì số mới
  tính từ phân bổ đọc không khóa. Cùng bẫy đã xác nhận bằng probe ở CR-628 M7; SQLite test không thể thấy.
- Sửa: mọi lần đọc phân bổ trên đường GHI phải là đọc có khóa — thêm `for_update` cho `load_assignments` (dùng
  `.with_for_update(read=True)` sau `lock_employees`) và truyền xuống `policy_allocation.allocated_days` khi gọi từ
  `reconcile_balances`/`update_one` (`others`). Hoặc đặt `READ COMMITTED` cho ba đường ghi
  (`db.connection(execution_options={"isolation_level": "READ COMMITTED"})` là câu ĐẦU của giao dịch). Thêm bài probe MySQL
  hai luồng như CR-628.

### H2. Tạo / bulk lấy phạm vi `employee.read` nhưng tác động là GHI quỹ `leave_balance` → vượt phạm vi ghi quỹ
- `policy_assignment_controller.py:45-48`, `:115`, `:149`, `:169` (so với `:100`, `:193`, `:201` dùng phạm vi `leave_balance`).
- Lead ghi là cố ý (giống `allocate`). Nhưng `allocate` chỉ TẠO dòng thiếu theo luật chuẩn; phân bổ thì `reconcile_balances`
  GHI ĐÈ `allocated_days` theo gói bất kỳ (dòng gói cho tới 366 ngày). Phạm vi là hợp (OR) mọi grant: HR công ty A được
  `hr_leave` với grant phạm vi `company`, đồng thời giữ một vai trò khác có `employee.read` = `all` (seed dòng 443/502/523
  đều `all`) → POST `/api/leave-policy-assignments` cho nhân sự công ty B → quỹ năm nay của người B bị tính lại theo gói tùy ý.
  Sau đó chính người đó KHÔNG thấy / sửa / xóa được lượt vừa tạo (list/PATCH/DELETE lọc `leave_balance` → 404) → dữ liệu
  mồ côi chỉ admin dọn được.
- Sửa (giữ quyết định **đọc employee để chọn người**): sau `db.flush()` của assignment mới ở `apply_plan`, kiểm
  `get_scoped(db, LeavePolicyAssignment, "leave_balance", assignment.id, user, prof, "write")`; `None` → rollback + 404
  (bulk: vào `skipped`). Cùng chốt cho `preview` để màn xem trước không hứa điều đường ghi sẽ chặn.

## MEDIUM

### M1. D5 (không tự phân bổ cho mình) chỉ chặn ở tạo / bulk; PATCH / DELETE lượt của chính mình vẫn qua
- `policy_assignment_controller.py:207-234`, `policy_assignment_service.py:160-198` — không có so sánh `obj.employee_id` với
  `user.employee_id`.
- Kịch bản: HR X đang có gói 12 ngày từ 01/07 (người khác gán) và gói 18 ngày 01/01–30/06. X DELETE lượt 12 ngày
  `?recalc_current_year=true` rồi PATCH lượt 18 ngày `effective_to=null` → quỹ năm nay của X lên 18, tự làm, không qua người thứ
  hai. (Lưu ý: `adjust_balance` cũng chưa có chốt tự sửa — lỗ cũ, ngoài CR này, nhưng nên ghi.)
- Sửa: trong `_writable` (hoặc service) `if obj.employee_id == user.employee_id and not is_system_admin(...)` → 403
  `SELF_MESSAGE`; thêm test PATCH/DELETE tự mình.

### M2. FULL_YEAR + phân bổ bắt đầu từ ngày vào làm (giữa năm) ra số "lai" thay vì số của gói
- `policy_allocation_math.py:56-66`. Probe: luật loại 12, gói 15, vào làm 01/10/2026, phân bổ từ 01/10 → **13.0**
  (9 tháng × 12 + 3 tháng × 15)/12. Không phân bổ → 12 (đúng cũ). Gói 0 ngày (thử việc) từ ngày vào làm → vẫn ăn 9 tháng luật
  loại. Đây là cách gán phổ biến nhất (gán từ ngày vào làm kiểu ERPNext). Ví dụ chốt của spec chỉ phủ **chính sách 15 cả năm**.
- Sửa (cần chủ dự án chốt): với FULL_YEAR, tháng TRƯỚC `first_month_in_year(hire)` không tính vào phép chọn; hoặc tháng chưa
  có phân bổ nằm trước tháng vào làm lấy theo phân bổ đầu tiên. Ghi vào ví dụ chốt + test.

### M3. Bulk dùng savepoint → `change_tracker` đóng dấu "đã commit" sớm → nhật ký thay đổi ma khi cả lô quay đầu
- `policy_assignment_service.py:140-151` + `core/change_tracker.py:369-377` (SA 2.0.35 phát `after_commit` khi nhả savepoint).
- Kịch bản: bulk 50 người, người thứ 30 dính deadlock / lock wait timeout (`OperationalError`) → `raise` → controller
  `db.rollback()` + 500 **chưa lưu gì**, nhưng change_log của 29 người trước đã `committed=True` → cuối request ghi 29 dòng
  `tab_leave_policy_assignment` / `tab_leave_balance` chưa từng tồn tại (vi phạm luật 4 của change_tracker).
- Sửa cục bộ: bỏ savepoint (chốt nghiệp vụ đã lọc ở `plan_change`; UNIQUE chỉ vỡ khi có race → để cả lô 409), hoặc sửa gốc ở
  `change_tracker._after_commit`: bỏ qua khi `session.in_nested_transaction()`.

### M4. Đường GHI bulk không có số truy vấn cố định, giữ khóa 500 hồ sơ suốt thời gian đó
- `policy_assignment_service.py:55-90`: mỗi (người × loại) = `get_balance FOR UPDATE` + `allocated_days` (luật hạn mức +
  phân bổ + dòng gói) + `available_days` + audit insert; thêm `LeaveType` mỗi người. 500 người × 3 loại ≈ 8–10k câu trong một
  giao dịch đang khóa 500 dòng `tab_employee` → sửa hồ sơ / mọi đường khóa nhân sự bị chờ, dễ chạm `innodb_lock_wait_timeout`
  (rồi rơi vào M3). `plan_change` đã nạp đủ dữ liệu một lượt — tái dùng: tính `new_value` từ `PlanItem` (đã có `after` spans,
  `rules`, `balances`) và chỉ khóa các dòng quỹ cần ghi bằng một câu `IN (...) FOR UPDATE`.

## LOW

- L1 `policy_assignment_controller.py:149`, `:169` — create / bulk không lọc `Employee.is_active` (preview có, `:115`) → gọi
  API thẳng phân bổ được cho người đã nghỉ việc và `reconcile_balances` cấp luôn dòng quỹ năm nay cho họ. Thêm
  `.filter(Employee.is_active.is_(True))` như preview / `allocate`.
- L2 `policy_controller.py:82`, `:30` — `query(...).delete()` bulk đi vòng `before_flush` nên change_log không thấy dòng gói bị
  xóa; audit chỉ ghi **N dòng** → mất số ngày/năm CŨ của gói (thứ quyết định quỹ). Hai PUT đồng thời → `IntegrityError`
  (uq policy/type) rơi 500. Ghi before/after (danh sách `type:days`) vào câu audit; bắt `IntegrityError` → 409.
- L3 `policy_schema.py:34-39` — PATCH `{"name": null}` / `{"is_active": null}` lọt schema → NOT NULL vỡ ở MySQL →
  `commit_or_conflict` trả 409 **code đã tồn tại** (sai thông điệp). Thêm validator cấm null tường minh.
- L4 `policy_controller.py:23-30` vs `policy_assignment_service.create_*` — xóa gói không khóa dòng gói; tạo phân bổ đồng thời
  → phân bổ trỏ gói đã xóa (dòng gói cũng xóa) → im lặng về luật loại. Khóa `LeavePolicy` FOR UPDATE ở cả hai đường.
- L5 `policy_assignment_service.py:171` — `if clash and employee is not None`: hồ sơ bị xóa cứng thì kéo dài được chồng ngày.
  Kiểm chồng không cần `employee` (chỉ cần cho thông điệp).
- L6 `policy_assignment_controller.py:70-74` — `search` nạp cả bảng nhân sự vào Python mỗi lần gõ; `search` không có trần độ
  dài. Chấp nhận ở quy mô hiện tại; nên `Query(None, max_length=100)`.

## Đã soát, không thấy vấn đề
- Báo cáo 30: gác kép đủ 3 đường (`require` + `require_report`), export dùng phạm vi `export`, `day_kind`/`group_by` 422, kỳ
  ≤366 ngày, 3 câu cố định mỗi `fetch`; cache Redis khóa theo token nên không rò chéo người.
- Ma trận: phạm vi `leave_balance` + action đúng, router đăng ký trước `/{bid}`, số câu cố định, export trần 5000.
- `allocate` có lọc: chỉ thu hẹp, vẫn qua `apply_scope`. `pick_quota` tách đúng hành vi cũ; không phân bổ → đúng
  `prorate_allocation` cũ (kể cả 12.25).
- Schema: `String(n)` đều có `max_length` khớp, ngày 2000–2100, trần 50 dòng / 500 người. IDOR qua id: GET/PATCH/DELETE
  `get_scoped`, bulk/preview/create lọc phạm vi (xem H2 về loại phạm vi).

## Câu hỏi mở
1. H2: giữ **chọn người theo employee.read** nhưng có đồng ý chặn thêm bằng phạm vi `leave_balance.write` không?
2. M2: FULL_YEAR + phân bổ từ ngày vào làm giữa năm nên ra số của gói (15) hay số lai (13)?
3. M1: D5 có áp cho sửa / xóa lượt của chính mình không (đề xuất: có)?

**Status:** DONE_WITH_CONCERNS
**Summary:** 2 High (RR snapshot race trên đường ghi phân bổ; phạm vi ghi quỹ mượn employee.read), 4 Medium, 6 Low.
