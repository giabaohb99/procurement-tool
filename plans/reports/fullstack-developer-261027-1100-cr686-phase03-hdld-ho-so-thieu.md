# CR-686 Phase 03 — B1 HĐLĐ + E1 Hồ sơ thiếu (backend)

## Endpoints (6, đều gác `require(entity)` + `require_report(key)`)
- `GET /api/labor-contracts/summary | /summary/export | /summary/rows` — khóa 17, `labor_contract` read|export.
- `GET /api/employees/profile-gaps/summary | /summary/export | /summary/rows` — khóa 18, `employee` read|export.
- Router include TRƯỚC `labor_contract_router` / `employee_router` (cạnh `employee_report_router` trong main.py).
- Phạm vi: controller tự dựng `apply_scope` (HĐ + Employee) rồi đưa query vào service -> BB4 qua mà không cần miễn trừ.

## B1 — chỉ số (đếm cờ, trend=[], compare tính lại tại cuối kỳ của nó; as_of = min(cuối kỳ, hôm nay))
- active: SIGNED, start<=as_of, end trống hoặc >=as_of, CHỈ người còn làm (is_active và !resigned).
- resigned_not_terminated «Người đã nghỉ, HĐ chưa chấm dứt»: cùng điều kiện hiệu lực nhưng người đã nghỉ (có trong drilldown) — cho Nhân sự dọn sổ.
- expiring_30/60/90: active + end có + chưa có HĐ nối tiếp (`expiry_service._has_successor`, tái dùng) + người còn làm; TÍCH LŨY (30 ⊂ 60 ⊂ 90).
- probation_expiring_30: expiring_30 và loại THỬ VIỆC.
- overdue: SIGNED, end<as_of, còn làm, không có nối tiếp (luật nháp overdue=True).
- no_contract: nhân sự đang làm (is_active, !resigned, hire_date null/<=as_of) chưa có HĐ SIGNED/TERMINATED start<=as_of (NOT IN subquery, 1 câu).
- missing_scan: active + signed_file_id=0. second_fixed_term: active FIXED_TERM + >=2 HĐ FIXED_TERM đã ký.
- new_contracts: start trong kỳ (chỉ nạp SIGNED/TERMINATED nên không có nháp/hủy). terminated: TERMINATED + terminated_date trong kỳ.
- Dimensions company/department/contract_type; breakdown contract_type (rank_by active). Hàng chưa HĐ dùng phòng/công ty của hồ sơ.
- /rows: cột Mã NV, Họ tên, Phòng ban, Mã HĐ, Loại HĐ, Bắt đầu, Kết thúc, Còn (ngày), 3 cột lương; link `/hr/employees/{id}?tab=labor-contracts`. Lương chỉ ở /rows.
- Hàng không mang cờ nào bị bỏ khỏi payload.

## E1 — chỉ số (tình trạng hiện tại, period trả nguyên, compare=None, trend=[])
- active_total, complete (helper) -> complete_rate (derived, helper `gap_rows` cho xếp hạng nhóm/breakdown gap_kind).
- missing_hire_date/position/manager/department (position_id=0, manager_id=0, department_id=0).
- Nhạy cảm (chỉ khi `perms_union.employee_sensitive.read`; cột KHÔNG nạp khỏi DB nếu thiếu quyền): missing_dob/id_number/tax_code/social_insurance/bank, id_expiring_90 (<= hôm nay+90, gồm đã hết).
- Tài khoản (chỉ khi `user.read`): no_account «Đang làm, chưa có tài khoản đang mở» (tài khoản khóa tính là chưa có), account_no_role, resigned_active_account.
- complete = đủ các trường THIẾU đang đếm cho người xem (4 cơ bản + 5 nhạy cảm nếu có quyền); KHÔNG xét tài khoản, CCCD sắp hết hạn. Ghi trong notes.
- Thiếu quyền: chỉ số vắng khỏi meta + notes; /rows của chỉ số đó -> 422. Chỉ cột `id_expiry_date` của id_expiring_90 là giá trị nhạy cảm duy nhất, chỉ khi có quyền.
- Tải nhân sự: đang làm HOẶC (đã nghỉ và EXISTS tài khoản is_active) trong SQL; số truy vấn vẫn cố định. gap_kind là breakdown (không phải group_by; group_by=gap_kind -> 422).

## Files
- NEW labor_contract/report_controller.py (64), report_data.py (163), report_service.py (123)
- NEW employee/profile_gaps_report_controller.py (66), profile_gaps_report_data.py (117), profile_gaps_report_service.py (134)
- main.py: 2 import + 2 include. test_phan_quyen_bao_cao_gac_duong.py: +4 GATED, +2 ROUTE_SPECS.
- NEW test/backend/test_bao_cao_hdld_cr686.py (13 bài), test_bao_cao_ho_so_thieu_cr686.py (17 bài).

## Tests
`pytest` 5 tệp được giao: 142 passed. Gồm: định nghĩa từng chỉ số, phạm vi dept + department_id chỉ thu hẹp, 403 cả 3 đường, 422 (metric lạ, __other__, group_by lạ, department_id rác), xlsx, không rò giá trị nhạy cảm, đếm truy vấn 5 vs 50 hồ sơ bằng nhau.

## Số truy vấn (mỗi lần fetch; summary gọi fetch 1 lần, 2 lần nếu có kỳ so sánh — B1)
- B1: 4 (HĐ · hồ sơ theo IN · HĐ cùng người · chưa-có-HĐ) + tối đa 1 câu tên công ty/phòng.
- E1: 1 (nhân sự) + 2 khi user.read (tài khoản · vai trò) + tối đa 1 tên; luôn 1 lần fetch.

## Chốt của điều phối (đã áp dụng)
1. expiring_N giữ [as_of, as_of+N]. 2. active chỉ người còn làm + chỉ số resigned_not_terminated. 3. Đổi nhãn no_account. 4. Tối ưu tải người đã nghỉ bằng EXISTS.
Test: 5 tệp, 142 passed.

## Câu hỏi mở
- complete_rate chia cho active_total toàn phạm vi; không loại người chưa có tài khoản.

## Sửa theo code review
1. B1 kỳ quá khứ: nạp thêm TERMINATED có terminated_date > as_of; coi là đã ký tại as_of (active/overdue/resigned_not_terminated) -> áp cả kỳ so sánh. Bài kiểm kỳ 60–31 ngày trước.
2. second_fixed_term: bộ đếm riêng gồm cả FIXED_TERM đã chấm dứt; danh sách HĐ nối tiếp (`_has_successor`) vẫn chỉ nháp/đã ký.
3. test_phan_quyen_bao_cao_gac_duong.py: 5 đường /summary/rows vào GATED + lưới soi route; bài đếm: 3 route cho khóa có /rows, 2 cho khóa còn lại (ROWS_KEYS suy từ GATED).
4. `type_label` (report_data.py): mã loại lạ -> «Khác», hết 500.
5. B1 nạp bằng with_entities (HĐ 15 cột, nhân sự 5 cột, hàng chưa-HĐ 5 cột; bỏ custom_values). `load_group_names` dùng chung đặt ở employee/profile_gaps_report_data.py, B1 import.
Test: 5 tệp + test_assistant_report_summary_cr208.py = 155 passed.
