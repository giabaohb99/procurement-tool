# Rà backend duoc-CR-757 (lịch làm việc phòng ban + trợ lý tra phép)

| | |
|---|---|
| Ngày | 13/11/2026 |
| Người rà | code-reviewer (độc lập, chỉ đọc) |
| Phạm vi | diff chưa commit: `work_schedule/{resolver,resolver_many,template_controller}.py`, `assistant/tools/{leave_tool,leave_taken_schedule,employee_leave_tool,__init__}.py`, `assistant/{tool_router,service}.py`, `agent_hub/{core_v2,intent_ledger,mcp,mcp_settings}.py`, 3 tệp bài kiểm. Bỏ qua `frontend-v2/`. |
| Kết luận | **Trả lại** — 1 lỗi Chặn (lọt dữ liệu đơn nghỉ ra ngoài phạm vi `leave_request`), sửa một dòng lọc + 1 bài kiểm là gộp được |

## Đã chạy

- `test_tro_ly_tra_phep_lich_lam_viec_cr757.py` + 4 bài canh MCP (`test_assistant_pham_vi_doc`, `test_agent_hub_y_dinh_tu_nho`, `test_agent_hub_cau_hinh_mcp_cr216`, `test_agent_hub_cong_mcp_cr207`): **88 xanh**.
- 4 tệp `test_lich_lam_viec_*` (api, phân giải, phân giải gom, bộ mã quyền) + `test_pham_vi_bo_may_duyet_xuyen_suot`, `test_agent_hub_ai_cua_toi_cr213`, `test_pham_vi_luat_bat_bien`, `test_pham_vi_duong_vong`, `test_assistant_leave_tool`: **176 xanh**.
- `ruff check` các tệp đổi: sạch. Không có ngoặc kép góc, không emoji.
- Hai bài dò tạm trong `/tmp` của container (đã xóa) xác nhận lỗi Chặn dưới đây.

## Chặn

### C1. `taken_by_type` của người khác không qua phạm vi `leave_request`, lộ ngày nghỉ ốm / không lương / thai sản ngoài phạm vi đơn nghỉ

`employee_leave_tool.py:144` gọi `taken_by_type_many(ctx.db, ids, ...)`; truy vấn ở `leave_taken_schedule.py:53-60` chỉ lọc `employee_id IN ids`, KHÔNG `apply_scope(LeaveRequest, "leave_request")`, và tool cũng không hỏi `ctx.can("leave_request")`. Tập `ids` lấy theo `employee ∩ leave_balance`, nên dữ liệu rút từ ĐƠN NGHỈ đi theo phạm vi của QUỸ PHÉP + HỒ SƠ — hai khóa không phải chủ của dữ liệu đó. Màn Quỹ phép chỉ hiện `used_days` của loại trừ quỹ; số ngày nghỉ ốm, không lương, thai sản (dữ liệu gần sức khỏe) trước nay chỉ thấy ở màn Đơn nghỉ phép, gác `leave_request`.

Hai kịch bản đã chạy thật (bài dò trên SQLite, cùng fixture `cap_quyen`):

1. Vai trò tự dựng có `leave_balance.read` phạm vi tất cả + `employee.read` tất cả, KHÔNG có `leave_request` (vd kế toán đối soát quỹ phép): `employee_leave_summary(employee="TESTREQ")` trả `taken_by_type = [{UNPAID, approved_days: 3}]`.
2. Trưởng phòng theo seed (`leave_balance` dept, `leave_request` dept, `employee` dept) + một vai trò danh bạ có `employee.read` tất cả (`vanban_xem`, `vanban_sua`, `pur_admin`, `hr_profile`, `coffee_admin` đều có): hỏi người PHÒNG KHÁC cùng công ty → trả đủ `taken_by_type` (3 ngày không lương). Lý do: `leave_balance` không có cột phòng nên bậc `dept` rơi về công ty (`core/scoping.py` nhánh `scope == "dept"`, chỉ có `company`), còn `employee` là HỢP các grant nên mở cả công ty. Màn Đơn nghỉ phép của chính người này chỉ thấy phòng mình.

Bài `test_truong_phong_pham_vi_phong_chi_thay_phong_minh` xanh chỉ vì người kiểm có ĐÚNG một grant `employee` bậc phòng; thêm bất kỳ vai trò danh bạ nào là lọt.

Sửa (giữ số truy vấn cố định, không thêm truy vấn):

```python
# leave_taken_schedule.taken_by_type_many: thêm tham số scope_cond=None
q = db.query(...).join(...).filter(...)
if scope_cond is not None:
    q = q.filter(scope_cond)

# employee_leave_tool._run
if ctx.can("leave_request"):
    cond = scope_condition(LeaveRequest, "leave_request", ctx.user, ctx.profile)
    taken = taken_by_type_many(ctx.db, ids, year, types, scope_cond=cond)
else:
    taken = {i: {"taken_by_type": [], "taken_total_days": 0.0, "pending_total_days": 0.0} for i in ids}
```

`scope_condition` trả `false()` khi không grant nào, nên nhánh `else` chỉ để rõ ý. Kèm một dòng glossary: "taken_by_type rỗng có thể vì đơn nghỉ của người này nằm ngoài phạm vi bạn được xem". Thêm 2 bài kiểm đúng hai kịch bản trên (khẳng định `taken_by_type == []`, `balances` vẫn có). Sửa câu ở `E2_CUA_GAC_CUA_TUNG_TOOL` (test_pham_vi_bo_may_duyet_xuyen_suot.py:1328) thêm "+ scope_condition(leave_request) cho ngày đã nghỉ". `my_leave_summary` không cần đổi (đã gác `ctx.can("leave_request")` và khóa cứng chính người hỏi).

## Nên sửa

### N1. Hỏi theo phòng bằng tên tự nhiên "phòng Kế toán" ra rỗng

`employee_leave_tool.py:77-83` so `fold(raw) in fold(name)`. Tên phòng trong DB phần lớn KHÔNG có chữ "Phòng" (local: "Kế toán", "Nhân sự", "Hành chính"...). Người dùng hỏi "phòng Kế toán năm nay ai nghỉ bao nhiêu" thì model rất dễ truyền `department="phòng Kế toán"` → "phong ke toan" không nằm trong "ke toan" → rỗng → trợ lý trả "không có trong phạm vi bạn được xem", sai. `NAME_ARGS` ở `core_v2.py:1497` chỉ bóc kính ngữ cho `employee`, không bóc "phòng". Sửa: bóc tiền tố `^(phong|ban|bo phan|p\.?)\s+` sau `fold` trong `_match_departments` (hoặc thử cả hai bản có / không tiền tố), thêm bài kiểm `department="phòng test"` khi tên phòng là "Test".

### N2. Không tính vào ngân sách dòng / phút của khóa MCP

`agent_hub/mcp.py:81` `ROW_BUDGET_TOOLS = {"erp_read", "office_read"}`; tool mới trả tới 50 người / lượt theo phòng, mỗi người kèm quỹ từng loại + ngày đã nghỉ từng loại. Một khóa có thể quét lần lượt mọi phòng, trần duy nhất là `rate_per_key` (lượt / phút). Skill `them-cong-cu-mcp` bước 4 ghi "đọc nhiều dòng → ROW_BUDGET_TOOLS". Tiền lệ ngược: `employee_lookup` cũng không tính, nên không xếp Chặn. Cách đơn giản nhất (2 dòng, không đổi khuôn kết quả):

```python
ROW_BUDGET_TOOLS = frozenset({"erp_read", "office_read", "employee_leave_summary"})
...
rows = result.get("items") or result.get("employees") or []
mcp_log.spend_rows(key.id, len(rows) + (1 if result.get("item") else 0))
```

Nếu muốn giữ một khóa chung thì đổi tên `employees` → `items` trong tool, nhưng sẽ phải sửa lời mô tả + bài kiểm; cách trên ít đụng hơn. Thêm khẳng định vào bài kiểm như `test_assistant_doc_phieu_van_phong_kh_ai2_3.py:76`.

### N3. Tài liệu bắt buộc chưa có (P5 ghi "chưa")

Đường API mới `/tools/effective-department` chưa ở `doc/erp/hrm/tai-lieu-ky-thuat/api.md`; tool mới chưa ở `doc/agent-hub/06-cong-mcp.md`, `change-log-ai.md`, `nhat-ky-task.md` (skill bước 12 + luật `chung-dat-ten-va-quy-uoc.md` §3). Không chặn rà mã nhưng phải có trước khi đánh dấu xong.

## Gợi ý

- **G1. "Đã nghỉ" gồm cả đơn duyệt cho ngày SẮP TỚI.** `taken_total_days` cộng mọi đơn `LR_APPROVED` có `from_date` trong năm, kể cả tháng sau. Glossary có nói, nhưng lời dặn ở `service.py` bảo đọc `taken_total_days` cho câu "đã nghỉ mấy ngày" → model dễ nói "đã nghỉ 5 ngày" khi 2 ngày chưa tới. Có thể tách `approved_upcoming_days` (đơn `from_date > hôm nay`) trong cùng GROUP BY (thêm một cột `case`), không thêm truy vấn.
- **G2. Năm gán theo `from_date` lệch báo cáo Tình hình nghỉ phép.** Đúng với sổ quỹ (`request_service.reserve_lines/consume_lines` lấy `obj.from_date.year`, đã kiểm), nhưng báo cáo duoc-CR-686 (`leave/report_day_split.py`) chia ngày theo kỳ thật. Đơn 30/12 → 02/01 cho hai con số khác nhau giữa trợ lý và báo cáo năm. Glossary nên thêm nửa câu "báo cáo Tình hình nghỉ phép chia theo ngày thật nên có thể khác ở đơn vắt qua năm".
- **G3. Quỹ phép của người đổi pháp nhân giữa năm.** `LeaveBalance.company_id` chụp lúc cấp (`balance_service.py:128`), không theo khi chuyển công ty. Nhân sự B (bậc công ty) thấy người vừa chuyển sang nhưng `balances` rỗng (dòng quỹ còn mang công ty A) → glossary nói "Rỗng = Nhân sự chưa cấp quỹ năm này" là sai. Đổi câu thành "chưa cấp quỹ năm này, hoặc dòng quỹ nằm ngoài phạm vi bạn xem". Không phải lọt dữ liệu (lọc kép là hẹp hơn màn Quỹ phép).
- **G4. `department="0"` lách chốt `IN [0]`.** `employee_leave_tool.py:80-81` nhận chuỗi số bất kỳ, kể cả "0" → khớp nhân sự chưa gắn phòng; chú thích dòng 95 nói đang tránh đúng trường hợp này. Vẫn trong phạm vi, chỉ là kết quả lạ. Lọc `int(raw) > 0`.
- **G5. Bộ lọc công cụ hụt vài câu.** "nhân viên phòng IT nghỉ bao nhiêu" không nạp nhóm `leave` (ra ticket / employee / analytics) nên `employee_leave_summary` không có trong danh sách. Thêm `nghi bao nhieu|ngay da nghi|so ngay nghi` vào regex ở `tool_router.py:57-58`. (Câu không khớp nhóm nào thì router trả `None` = đủ bộ, không sao.)
- **G6. Có sẵn từ trước, không thuộc CR này:** `leave_balance` bậc `dept` (seed `dept_head`, `seed.py:697`) thực chất là cả công ty trên màn Quỹ phép vì bảng không có cột phòng. Tool hẹp hơn màn (giao với `employee`), nên ghi chú plan "theo đúng phạm vi màn Quỹ phép" không hoàn toàn đúng; nên ghi rõ trong tài liệu P5 và cân nhắc một CR riêng (khai `dept_id` cho `leave_balance` qua `Employee` hoặc subquery).
- **G7.** `_visible_employees` nạp toàn bộ nhân sự trong phạm vi rồi lọc từ khóa bằng Python — với HR phạm vi tất cả là vài trăm đến vài nghìn dòng 6 cột, chấp nhận được; chỉ nhắc nếu sau này số nhân sự lớn.

## Mục được kiểm, đạt

- **Lộ sự tồn tại qua tìm tên:** từ khóa lọc SAU khi đã áp phạm vi; mã khớp đúng cũng chỉ trong tập đã lọc; ngoài phạm vi và không tồn tại trả cùng `NOT_FOUND`. Danh sách phòng dò không theo phạm vi nhưng chỉ dùng làm bộ lọc, tên phòng chỉ hiện cho người thấy được. Đạt.
- **Người nghỉ việc:** tra theo tên / mã trả cả người đã nghỉ kèm `is_active` — khớp màn Quỹ phép (không lọc `is_active`); tra theo phòng chỉ người đang làm như mô tả. Đạt.
- **Đơn nháp / từ chối / trả về / đã hủy / xóa mềm:** loại hết (`status IN (approved, pending)` + `is_deleted = False`); hủy sau duyệt thì sổ quỹ hoàn lại và tool cũng bỏ — khớp. Dữ liệu cũ một loại đã được migration `cbb45a57ada1` chép sang `tab_leave_request_line`. Đạt.
- **Số truy vấn:** cố định (nhân sự · [phòng] · loại nghỉ · tên phòng · quỹ · 2 của `available_days_map` · ngày đã nghỉ · 3 của `load_day_plans_many`), có bài đếm 2 vs 10 người. Sửa C1 không thêm truy vấn. Đạt.
- **Tách `effective_for_employee`:** `_winner` gọi `_winner_for` với đúng ba số cũ; `_effective_payload` là nguyên thân hàm cũ sau dòng tìm `hit`; `DayPlansMany.at` gọi `winner` = `_pick` cũ. Không đổi hành vi; các bài phân giải cũ xanh. `employee_id = 0` an toàn vì `_candidate_pairs` bỏ đích `0` ở mọi cấp trừ hệ thống. Đạt.
- **Đường `/tools/effective-department`:** `require("department","read")` + `get_scoped` → 404 chung cho không tồn tại / ngoài phạm vi; `department_id ge=1`; dải năm 422; docstring tiếng Việt; router có `tags`. Chỉ trả dòng gán CẤP PHÒNG, không lộ dòng gán cấp nhân sự. Đạt.
- **Đăng ký tool:** `_active_specs`, `READ_TOOLS`, đúng một nhóm G7 (`leave`, bật mặc định), `tool_router`, `TOOL_SUB`, `NAME_ARGS` (bóc kính ngữ), phân loại `TOOL_CHUNG_TU`, `CA_O_TEP_KHAC`, `E2_CUA_GAC_CUA_TUNG_TOOL`, đếm 92. Thiếu: `ROW_BUDGET_TOOLS` (N2) và tài liệu (N3).
- **Luật chung:** chuỗi / chú thích tiếng Việt, định danh tiếng Anh, hàm là động từ (trừ `year_bounds`, `schedule_brief`, `schedule_label_many` là danh từ — nhỏ, có thể đổi `get_year_bounds`, `build_schedule_brief`, `build_schedule_labels`), không emoji, không ngoặc kép góc. `vn_today()` thay `date.today()` cho năm mặc định là vá đúng.
- **`hr-leave.md`:** tool không gọi `ensure_balance`, số còn lại chỉ qua `available_days_map`, không tự cộng trừ cột. Đạt.

## Câu hỏi còn treo

1. Chủ dự án có muốn trưởng phòng (bậc `dept`) thấy quỹ phép cả công ty như màn hiện nay (G6) không, hay đó là lỗ cũ cần CR riêng?
2. "Đã nghỉ" có nên tính đơn đã duyệt cho ngày tương lai (G1) — cần người chủ chốt cách nói.

## Lượt 2 (13/11/2026) — rà phần sửa

**Kết luận: gộp được.** Không còn lỗi Chặn.

### Đã chạy

- `test_tro_ly_tra_phep_lich_lam_viec_cr757.py` (nay 19 hàm, thêm bài C1 ×2, N1, bộ lọc công cụ, ngân sách dòng MCP) cùng
  `test_assistant_pham_vi_doc`, `test_pham_vi_bo_may_duyet_xuyen_suot`, `test_assistant_leave_tool`,
  `test_assistant_doc_phieu_van_phong_kh_ai2_3`, `test_agent_hub_cong_mcp_cr207`, `test_agent_hub_y_dinh_tu_nho`: **126 xanh**.
  `ruff` sạch.
- Chạy lại HAI bài dò C1 trên mã mới (tệp tạm trong `/tmp` của container, đã xóa):
  1. `leave_balance` + `employee` tất cả, không có `leave_request` → `taken_by_type == []`, `taken_total_days == 0`. **Đạt.**
  2. Trưởng phòng (`leave_balance` / `leave_request` / `employee` bậc phòng) + vai trò danh bạ `employee` tất cả → người phòng
     khác: `taken_by_type == []`; người cùng phòng vẫn ra đúng 2 ngày. **Đạt.**
- Câu GROUP BY mới (có `case(from_date > hôm nay)` ở cả SELECT lẫn GROUP BY) chạy được trên MySQL local đang bật
  `ONLY_FULL_GROUP_BY` (script chỉ đọc, `rollback`). Lưu ý: DB local không có đơn nào trong 2025–2026 nên chỉ chứng minh câu
  biên dịch và được MySQL nhận, không chứng minh con số.

### Từng mục

| Mục | Trạng thái | Ghi chú |
|---|---|---|
| C1 | Đã sửa | `ctx.can("leave_request")` + `scope_condition(LeaveRequest, "leave_request")` lọc ngay trong câu GROUP BY, không thêm truy vấn; thiếu quyền → `build_empty_taken`. `TAKEN_SCOPE_NOTE` dặn model không nói "chưa nghỉ ngày nào". `my_leave_summary` giữ `scope_cond=None` (chính người hỏi, đã gác `leave_request.read`) — đúng. Bảng E2 đã cập nhật. |
| N1 | Đã sửa | `_DEPT_PREFIX` bóc `phong ban / phong / ban / bo phan / p.`; so cả bản bóc lẫn bản đủ nên "Ban Giám đốc" vẫn khớp. |
| N2 | Đã sửa | Có trong `ROW_BUDGET_TOOLS`; đếm `items or employees`. Có bài kiểm. |
| G1 | Đã sửa | Tách `approved_upcoming_days` / `upcoming_total_days`; lời dặn ở `service.py`, `leave_tool._DESC`, glossary đều bảo không cộng phần sắp tới. |
| G2 | Đã sửa | Glossary nêu lệch với báo cáo Tình hình nghỉ phép ở đơn vắt qua năm. |
| G3 | Đã sửa | Glossary `balances`: rỗng có thể do dòng quỹ ngoài phạm vi (pháp nhân cũ). |
| G4 | Đã sửa | `"0"` → `[]`. |
| G5 | Đã sửa | Regex thêm `nghi bao nhieu / ngay da nghi / so ngay nghi / nghi (it|nhieu) nhat`; có bài kiểm tham số hóa. |
| G6 | Giữ nguyên | Có từ trước; vẫn đề nghị một CR riêng. |
| Đặt tên hàm | Đã sửa | `get_year_bounds`, `build_schedule_brief`, `build_schedule_label`, `build_empty_taken`. |

### Gợi ý còn lại (không chặn)

- Đơn ĐANG nghỉ (bắt đầu ≤ hôm nay, kết thúc > hôm nay) tính cả đơn vào `approved_days`, gồm cả những ngày còn lại sau hôm
  nay. Glossary đã ghi "đã / đang nghỉ" nên chấp nhận được; muốn chính xác từng ngày thì phải chia theo `workday_service`, không
  đáng làm ở CR này.
- Mục N3 (tài liệu `api.md`, `06-cong-mcp.md`, `change-log-ai.md`, `nhat-ky-task.md`) vẫn thuộc P5 — phải có trước khi đánh dấu xong
  CR, không chặn việc gộp mã backend.
