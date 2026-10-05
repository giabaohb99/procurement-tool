# Code review — backend Lịch làm việc (erp-v2, chưa commit)

## Scope
- Files: `core/work_schedule_codes.py`, `core/{code_sets,all_models,permissions,scoping}.py`, `seed.py`, `main.py`, `modules/work_schedule/*` (9 tệp), `migrations/versions/wsched01_lich_lam_viec.py`, `leave/{workday_service,holiday_calendar,constants,request_service,request_controller}.py`, `assistant/tools/draft_tool.py`, `test/backend/test_lich_lam_viec_*.py` + factory
- LOC: ~1.1k mã + ~980 test
- Đã chạy: 5 tệp `test_lich_lam_viec_*` + `test_pham_vi_khai_du_b07` → **678 passed**; test nghỉ phép cũ (`test_nghi_phep_{so_ngay_dau_cuoi,don_va_duyet,quy_va_ngay_cong}`, `test_assistant_draft_tool`, `test_pham_vi_luat_bat_bien`) → **162 passed**
- `alembic heads` = `wsched01` (một head, local đã lên). Seed tiếng Việt trong DB đúng byte UTF-8 (`48C3A06E68…E28093…`), collation `utf8mb4_unicode_ci`.

## Overall
Chắc tay. Phần quan trọng nhất (số ngày nghỉ khi chưa gán gì) **tương đương chính xác**: đã soát từng nhánh so với `git show HEAD:…/workday_service.py` — `leave_mask` khớp `START/END_DAY_CREDIT` + `same_day_credit` (kể cả mã buổi lạ → 1.0); theo giờ: chia cho 8.0 là phép nhân lũy thừa 2 nên `Σ(h_i/8)` bằng đúng bit `(Σh_i)/8` → không lệch làm tròn; `exclude_holiday=False` → `FULL_DAY_SPEC` + bỏ lễ = y cũ. Bài kiểm tương đương so với bản đóng băng của luật cũ, đủ 3×3 buổi × 7 thứ × 3 độ dài × có/không lễ. Số truy vấn cố định (2 lịch + 1 lễ), có bài đếm 400 ngày. Mọi route có `require`; `/tools/effective` gác `employee.read` + `get_scoped`. Tệp đều < 200 dòng. R2 đúng (SMALLINT + IntEnum, số không bắt đầu từ 0).

Không có lỗi Critical/High. 4 Medium, 6 Low.

## Critical
Không có.

## High
Không có.

## Medium

### M1. Giờ có múi giờ («08:00Z») làm nổ 500 khi tạo/sửa mẫu lịch
`work_schedule/template_schema.py:39,48` — `model_validator` so `self.start_time >= self.end_time` / chuỗi `<` của giờ trưa. Pydantic nhận `"08:00Z"` thành `time` CÓ tzinfo; so với `"17:00"` (không tz) ném **`TypeError`**, không phải `ValueError` → pydantic không đổi thành lỗi kiểm → FastAPI trả **500** (đã tái hiện bằng TestClient: `POST` với `start_time:"08:00Z"` → 500). Cả hai đầu cùng có `Z` thì qua kiểm, lưu `TIME` mất tz, vô hại nhưng vẫn là rác lọt cửa.
Fix: trong `DayIn`, thêm `field_validator("start_time","end_time","lunch_start","lunch_end", mode="after")` từ chối `v.tzinfo is not None` (hoặc `v.replace(tzinfo=None)`), và cấm giây ≠ 0 cùng chỗ (xem L2).

### M2. Hai lệnh TẠO gán sát nhau (bấm đúp / 2 người) sinh dòng chồng — DB không có chốt
`work_schedule/assignment_service.py:126-162` — kiểm chồng là `SELECT` rồi `INSERT`, không khóa, bảng không có UNIQUE nào. Hai POST cùng đối tượng cùng thấy dòng cũ A «không thời hạn» → cả hai cùng đóng A ở `from−1` (ghi đè cùng giá trị) và cùng chèn dòng mới; nếu là lịch tạm thì còn chèn **2 dòng nối lại** A′. Kết quả: 2 cặp dòng chồng nhau. Resolver vẫn tất định (`max(from,id)`) nên số ngày chưa sai, nhưng từ đó mọi POST/PATCH khác cho đối tượng này ăn 400 «Đã có lịch…» cho tới khi HR tự tìm và xóa bản trùng; danh sách hiện 2 dòng y hệt. `commit_or_conflict` không cứu được vì không có ràng buộc nào để vi phạm.
Fix tối thiểu: thêm `UniqueConstraint("target_level","target_id","effective_from")` (model + migration — migration chưa lên prod nên sửa thẳng `wsched01`) → bấm đúp cùng payload sẽ thành 400 sạch. Chặt hơn: khóa các dòng của đối tượng bằng `.with_for_update()` trong `_overlaps` ở cả create/update (MySQL InnoDB khóa khoảng chỉ mục `ix_wsa_target`).

### M3. Danh sách gán lộ lịch + họ tên nhân sự ngoài phạm vi — lách được chốt `get_scoped` của `/tools/effective`
`work_schedule/assignment_controller.py:26-41` + `scoping.py` (`work_schedule: PUBLIC`) + `seed.py:624` (mọi vai trò có `work_schedule.read`). `GET /api/work-schedule-assignments?target_level=4&target_id=<X>` (hoặc không lọc) trả mọi dòng gán cấp Nhân sự kèm `target_name` = `full_name`, mẫu lịch, khoảng ngày — cho **bất kỳ ai** có `read`, ở mọi pháp nhân. Thiết kế cố ý gác `/tools/effective` theo `employee` + `get_scoped` để «thẻ trên hồ sơ không lộ lịch người ngoài phạm vi» (`template_controller.py:1-6`), nhưng chính dữ liệu đó đọc được qua đường này. Mức nhạy cảm thấp (tên + lịch), nhưng mâu thuẫn với ý đồ và với quy ước `get_scoped`.
Lựa chọn: (a) chấp nhận và ghi rõ trong A10 rằng gán cấp Nhân sự là công khai trong nội bộ; hoặc (b) chỉ cấp `read` cho hr_leave/hr_profile (bỏ `setdefault` đại trà — form nghỉ không cần khóa này vì `estimate-days` không đòi `work_schedule.read`); hoặc (c) ở list/get, dòng cấp EMPLOYEE lọc thêm `target_id IN (employee trong phạm vi employee.read)`. (b) rẻ nhất và khớp «ai cần mới có».

### M4. Xóa dòng gán vừa tạo KHÔNG hoàn tác việc tự đóng/nối — số ngày nghỉ đổi âm thầm
`work_schedule/assignment_service.py:176-180`. Tạo lịch mới C từ 01/03 trên dòng A «không thời hạn» → A bị đóng 28/02 (và có thể sinh A′ từ `to+1`). HR thấy nhầm, xóa C → A vẫn đóng ở 28/02, khoảng của C giờ là **lỗ hổng**: nhân sự rơi xuống lịch phòng ban/pháp nhân/hệ thống/mặc định mà không ai báo, ước lượng ngày nghỉ trong khoảng đó đổi theo. Đúng loại «lịch tạm hết thì tụt xuống cấp rộng» mà chốt 05/10 muốn tránh.
Fix: khi xóa, nếu có dòng cùng đối tượng kết thúc đúng `obj.effective_from − 1` và/hoặc dòng cùng mẫu bắt đầu `obj.effective_to + 1` (dấu vết auto-close/resume) thì hỏi/nối lại; tối thiểu trả cảnh báo trong message xóa + test khóa hành vi. Cần đại ca chốt hành vi mong muốn (xem câu hỏi).

## Low

- **L1. `estimate-days` trả `schedule_name` của nhân sự bất kỳ** — `leave/request_controller.py:323-325`. `resolve_leave_taker` cố ý không gác phạm vi (đường chỉ đọc), nên ai có `leave_request.read` gõ `employee_id` bất kỳ là biết tên lịch của người đó. Lộ thông tin nhỏ, mới phát sinh trong diff. Fix: chỉ trả tên khi `employee_id` rỗng/là chính mình hoặc `get_scoped(Employee,…)` qua.
- **L2. Giờ có giây tạo ngày FULL 0 giờ** — `template_schema.py:39`: `08:00:30 → 08:00:59` qua kiểm (`start < end`), `_minutes` bỏ giây → `day_hours = 0`. `count_leave_days` vẫn tính ngày đó **1.0**, còn `count_hourly_days` bỏ qua (0) → hai đường lệch nhau. Fix: ép `second == microsecond == 0` và đòi `end − start ≥ 1 phút` theo phút.
- **L3. Loại ngày nửa buổi không ràng giờ với buổi** — `template_schema.py:42-45`. MORNING 13:00–17:00 hợp lệ; đơn bắt đầu «Chiều» ngày đó ra 0 (mask PM ∩ AM) dù người đó làm buổi chiều. Đúng A4 (loại thắng giờ) nhưng là bẫy nhập liệu; ít nhất cảnh báo khi MORNING có `end_time > 13:00` / AFTERNOON có `start_time < 12:00`, hoặc ghi rõ trên FE.
- **L4. Xóa mẫu đua với tạo gán** — `template_service.py:113-122` đếm rồi xóa, không khóa; gán tạo chen giữa trỏ vào mẫu đã xóa → resolver log cảnh báo + dùng FALLBACK theo ngày, `/tools/effective` hiện «mặc định» dù có dòng gán. Hiếm; cùng fix khóa ở M2.
- **L5. Vai trò thêm sau vòng `setdefault` không có `work_schedule.read`** — `seed.py:615-624` chạy trước `hr_leave/coffee_admin/coffee_counter/market_lookup` (dòng 681+). `hr_leave` khai tường minh nên ổn; ba vai trò còn lại thiếu `read` (cùng cảnh `holiday`). Không ảnh hưởng form nghỉ; chỉ lệch với câu «mọi vai trò khác chỉ read». Nếu chọn M3(b) thì việc này tự hết.
- **L6. `ix_wsd_schedule` thừa** — `model.py:33`, migration dòng 70: `uq_work_schedule_day(schedule_id, weekday)` đã là chỉ mục có tiền tố `schedule_id`. Vô hại, có thể bỏ trước khi lên prod.

## Edge cases đã soát và ổn
- `effective_to IS NULL` ở cả `_load_rows`, `_pick`, `_overlaps`; ranh hai mẫu đổi giữa khoảng nghỉ chọn theo TỪNG ngày.
- NV `company_id/department_id = 0/None` không bao giờ hỏi cặp `(cấp≠SYSTEM, 0)`; schema chặn ghi `target_id=0` ở cấp ≠ SYSTEM.
- Auto-close chỉ khi TẠO, chỉ dòng `to IS NULL` và `from < from_mới`; trùng `from` → 400; PATCH không bao giờ tự đóng; resume `to+1` không chồng được vì dòng mở vốn che hết phần sau.
- PATCH gộp giá trị rồi mới `check_target/check_period` + kiểm chồng loại trừ chính nó; đổi đích kiểm đích có thật; đổi mẫu kiểm mẫu đang bật.
- Xóa mẫu đang gán → 400; trần nhập: `name` 150 / `note` 500 khớp cột, năm 2000–2100 cho gán và `on_date`, `days` ≤ 7 và đúng 7 thứ không trùng, id ≤ 2^53.
- Không còn ai import `WORK_DAY_*`, `WORK_HOURS_PER_DAY`, `WEEKEND_DAYS`, `is_working_day`, `session_credit` (chỉ còn nhắc trong docstring migration cũ + 1 comment test `test_nghi_phep_quy_va_ngay_cong.py:62` — nên sửa comment cho khỏi dẫn sai).
- `draft_tool`: `emp` có thể `None` (hồ sơ bị xóa) → `workday_service` xử lý `employee=None` đúng.
- Migration: viết tay, đúng 3 bảng + 1 mẫu + 7 dòng ngày, `down_revision = wkhist01` (head duy nhất), downgrade bỏ index rồi bảng, không đụng phân quyền. Prod chỉ `admin` có khóa mới (D-018) — đã ghi ở phase 1 để phase 6 đưa vào tài liệu.

## Recommended actions (theo thứ tự)
1. M1 — chặn tzinfo/giây trong `DayIn` (5 dòng + 2 test).
2. M2 — UNIQUE `(target_level, target_id, effective_from)` vào `wsched01` (chưa lên prod) + `with_for_update()` trong `_overlaps`.
3. M3 — chốt với đại ca: thu hẹp `read` về hr_leave/hr_profile, hoặc ghi rõ «gán cấp Nhân sự là công khai».
4. M4 — chốt hành vi xóa sau auto-close; ít nhất cảnh báo + test khóa hành vi.
5. L1, L2 khi tiện tay.

## Metrics
- Tests: 678 + 162 passed (chỉ các tệp liên quan, không chạy cả bộ).
- Type/lint backend: không có cổng riêng; import sạch (pytest nạp toàn bộ app).
- Kích thước tệp: lớn nhất `assignment_service.py` 180 dòng.

## Unresolved questions
1. M3: gán lịch cấp Nhân sự có được coi là thông tin công khai nội bộ không? (quyết định giữa a/b/c)
2. M4: xóa dòng gán vừa tạo có phải tự mở lại dòng cũ đã bị tự đóng / gộp dòng nối lại không, hay chỉ cảnh báo?
3. Prod: có cấp `work_schedule` cho `hr_leave`/`hr_profile` bằng tay sau deploy, hay muốn một migration cấp quyền như đã làm với `tab_report_access`?
