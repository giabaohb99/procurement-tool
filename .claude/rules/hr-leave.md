---
paths:
  - "backend/app/modules/leave/**"
  - "backend/app/modules/approval/**"
  - "frontend-v2/src/modules/hr/**"
  - "test/backend/*nghi_phep*"
  - "doc/erp/hrm/02-nghi-phep.md"
  - "backend/app/modules/payment_request/leave_encashment_payout.py"
  - "backend/app/modules/payment_request/hr_payout_guard.py"
---
# Phân hệ NGHỈ PHÉP (CR-259, 03/09/2026)

> Chuyển nguyên văn từ CLAUDE.md gốc ngày 01/10/2026 — chỉ nạp khi làm việc với các đường dẫn ở trên.


Nằm **trong phân hệ Nhân sự** (`frontend-v2/src/modules/hr/`, menu *Nghỉ phép*),
backend ở `app/modules/leave/`. Tài liệu đầy đủ: `doc/erp/hrm/02-nghi-phep.md`.

- ⚠️ **Bốn khóa quyền mới** — `leave_request` · `leave_balance` · `leave_type` · `holiday`
  (ENTITIES 46 → **50**). Tách bốn vì `leave_balance` ghi được nghĩa là **tặng thêm
  ngày phép cho bất kỳ ai**. Trên hệ ĐANG CHẠY, vai trò cũ **không tự có** chúng (seed
  không ghi đè — D-018): phải tick ở màn Phân quyền, hoặc `SEED_FORCE_SYNC=true` một lần.
- ⚠️ **`leave_request` là entity đầu tiên khai CẢ `owner` LẪN `self`** trong `SCOPE_FIELDS`.
  Một tờ đơn có hai người dính tới nó — người **lập** (`created_by`, hành chính lập hộ) và
  người **nghỉ** (`employee_id`). Nhánh `own` của `_role_scope_cond` HỢP cả hai, và chặn
  khi `employee_id = 0` (nếu không thì `== 0` trúng mọi dòng chưa gắn nhân sự → **mở rộng**
  phạm vi thay vì thu hẹp).
- ⚠️ **`pending_days` (giữ chỗ) là cột bắt buộc, không phải tối ưu.** Gửi duyệt là trừ
  ngay. Thiếu nhịp này thì nộp mười đơn liền tay đều lọt. Đối xứng: **ba kết cục
  không-duyệt (từ chối · trả về · rút) đều phải TRẢ LẠI** — gộp chung một hàm
  `_release_and_set`, đừng tách ba bản chép.
- ⚠️ **MỘT ĐƠN KHAI NHIỀU LOẠI NGHỈ** (07/09/2026, `tab_leave_request_line`). Cả đơn
  dùng chung các khoảng ngày (một hoặc nhiều, xem bullet dưới), dòng chỉ chia SỐ NGÀY,
  không gắn khoảng. Hai cột đầu đơn thành **dẫn
  xuất**: `total_days` = tổng các dòng, `leave_type_id` = loại của dòng nhiều ngày
  nhất. **Sổ quỹ phải chạy THEO DÒNG ở cả bốn nhịp** — dùng `reserve_lines` ·
  `consume_lines` · `release_lines` · `refund_lines` của `request_service`, đừng gọi
  thẳng `balance_service` với `obj.total_days` (trừ tổng vào loại chính là cộng ngày
  không lương vào quỹ phép năm). Chốt xóa loại nghỉ phải hỏi **cả hai bảng**. Luồng
  duyệt chỉ thấy loại CHÍNH — **đã chốt bỏ 26/10/2026 (HR3-3)**: luồng duyệt coi mọi
  đơn là nghỉ phép, đừng thêm điều kiện rẽ nhánh theo loại nghỉ của dòng (§7.1 của
  `doc/erp/hrm/02-nghi-phep.md`).
- ⚠️ **MỘT ĐƠN KHAI NHIỀU KHOẢNG NGÀY** (duoc-CR-683, 26/10/2026, bảng con
  `tab_leave_request_period`, ≥1 dòng mỗi đơn). **Đầu đơn `from_*`/`to_*` là BAO NGOÀI dẫn
  xuất** (khoảng đầu → khoảng cuối) và nuốt cả KHE giữa các khoảng. Mọi chỗ hỏi *"ngày D có
  nghỉ không"* (lịch nghỉ, ai làm/ai nghỉ, hồ sơ làm việc, tải việc, chốt trùng ngày) PHẢI đọc
  qua `leave/period_spans.py` (`LeaveSpan`, `span_of`, `periods_by_request`) bằng OUTER JOIN —
  đơn chưa có dòng khoảng rơi về đầu đơn. Đọc thẳng `[from_date, to_date]` của đầu đơn là
  ngày khe hiện nghỉ, im lặng. Ghi khoảng chỉ qua `leave/request_periods.py`; ≥2 khoảng phải
  cùng năm (422), nghỉ theo giờ chỉ 1 khoảng, tối đa 20; đơn ≥2 khoảng sửa ngày thì PATCH phải
  gửi đủ `periods`. Chỉ tổng được sửa đè, không sửa đè từng khoảng. Báo cáo **Tình hình nghỉ phép**
  (duoc-CR-686, đổi luật cũ của CR-683): số ĐƠN / người / tỷ lệ neo ngày bắt đầu; số NGÀY chia
  theo ngày thật rơi vào kỳ / mốc — chỉ đơn vắt qua biên mới tính lại bằng Python
  (`leave/report_day_split*.py`), đừng thêm đường tính ngày thứ hai. Chi tiết `02-nghi-phep.md` §7.3.
- ⚠️ **Số phép còn lại KHÔNG lưu thành cột** — `balance_service.remaining()` là nơi duy
  nhất tính. **Số ngày nghỉ** chỉ tính ở `workday_service.count_leave_days()` — **SỬ DỤNG LỊCH LÀM VIỆC của người nghỉ** (`work_schedule/resolver.load_day_plans`), không còn `WEEKEND_DAYS`. Gọi `count_leave_days()` hoặc `count_hourly_days()` **PHẢI truyền `employee=`**, nếu quên thì sẽ tính theo lịch mặc định cho người có lịch riêng, dẫn tới sai âm thầm. Xem chi tiết ở `doc/erp/hrm/03-lich-lam-viec.md` §7, §12.
- ⚠️ **Hủy đơn KHÔNG được gọi `block_legacy_path`** (chốt đó chỉ dành cho duyệt/từ chối
  thẳng). Đường hủy đi qua `approval_bridge.cancel_request()` — nó **rút phiên duyệt**
  trước. Không rút thì người duyệt ký xong là hook trừ quỹ cho một tờ đơn đã hủy.
- Bộ mã **số** ở `leave/constants.py` (R2/QĐ-11), bản TypeScript gõ tay ở
  `hr/types/leave.ts` — `gen_status_ts.py` chỉ sinh cho bộ mã CHUỖI. Đừng lẫn với
  `core/leave_codes.py`: tệp đó khai mã **chuỗi** cho ô JSON của giấy GNP, và hai thế
  giới nối nhau qua `tab_leave_type.code`.
- **Seed chạy tay**, cố ý không nằm trong `app/seed.py`:
  `docker compose exec api python -m app.seed_nghi_phep` (chỉ THÊM, chạy lại được).

#### Duyệt NGAY trong màn Nghỉ phép (CR-260, 03/09/2026)

Màn `/hr/leave-requests` nay có **ba tab**: _Cần tôi duyệt_ · _Đơn của tôi_ ·
_Tôi đã duyệt_. Người duyệt không phải sang màn Phê duyệt nữa.

- ⚠️ **`apply_scope` một mình KHÔNG đủ cho nghỉ phép.** Người duyệt chặng 2 thường
  là Trưởng phòng Nhân sự, mà phạm vi dữ liệu của họ không với tới đơn của nhân
  viên phòng khác — bộ máy giao việc rồi chặn chính người được giao. `_get_or_404`
  và `approval_bridge.can_read_request` nay nới thêm: **đang có việc `TASK_PENDING`
  trên tờ đơn thì đọc được nó**. Nới đúng lúc treo, KHÔNG nới cho "đã từng ký" —
  ký xong quyền đó đóng lại, xem lại thì vào tab _Tôi đã duyệt_.
- ⚠️ Cột **Luồng duyệt** là **CHỮ một dòng**, không phải dải chấm. Bản dải chấm
  (chặng đang chờ sáng lên) đã dựng rồi BỎ ngày 03/09/2026 — trong ô bảng cao 35px
  nó đọc ra như một dãy biểu tượng lỗi. Câu chữ do **backend** dựng
  (`approval/steps_service._summary`) vì còn dùng cho bản in; đừng chép luật sang TS.
- ⚠️ **Không tab nào của màn Đơn nghỉ phép còn BÀY cột đó nữa** (duoc-CR-323,
  08/09/2026): _Đơn của tôi_ và _Tôi đã duyệt_ bỏ hẳn, _Cần tôi duyệt_ giữ nhưng
  `defaultHidden`. Cột **Việc của tôi** bỏ hẳn, **Hạn xử lý** rút về ngày giờ
  trần. Hai tín hiệu mất theo, đừng tưởng là sót: dấu **Quá hạn** (cờ
  `task.is_overdue` backend vẫn gửi, màn hình thôi không vẽ — bày lại thì đọc cờ
  đó, đừng tự so ngày ở TS) và dòng **Bấm thay ‹tên›**, thứ báo cho người được
  ủy quyền biết họ đang ký THAY người khác; nay chỉ còn ở màn chi tiết. Chi tiết
  ở §8.1 của `doc/erp/hrm/02-nghi-phep.md`.
- ⚠️ **`defaultHidden` KHÔNG áp cho người đã từng đụng menu "Cột"** của bảng đó:
  `useTableLayout` đọc `readLayout(storageKey) ?? defaultLayout`, có bản lưu
  trong `localStorage` là bản đó thắng. Muốn thấy đúng mặc định mới thì xóa khóa
  `erp.table.<storageKey>`.
- ⚠️ `steps_service` đọc **cả bảng việc lẫn `flow_snapshot`**. Bảng việc chỉ có
  chặng ĐÃ MỞ, nên hỏi riêng nó thì luồng 2 chặng vừa gửi đi chỉ ra một chấm.
  Tổng số chặng lấy từ bản chụp luồng nằm trong chính phiếu. Gom **3 truy vấn cho
  cả trang** bất kể bao nhiêu dòng — có test đếm truy vấn canh, đừng đặt query
  trong vòng lặp.
- ⚠️ Tab _Tôi đã duyệt_ **gộp mỗi đơn một dòng** (`_latest_per_request`):
  `handled_tasks` trả theo dấu vết nên ký hai chặng của cùng tờ đơn ra hai dòng
  giống hệt nhau.
- ⚠️ **`ENTITY_LABELS` + `ENTITY_LINKS` của `task_notification.py` phải có mọi
  entity mới.** Thiếu thì thư vẫn gửi nhưng ghi "Phiếu NP009" và `link` RỖNG —
  bấm vào không đi đâu cả, và `notify_new_tasks` nuốt lỗi nên không chỗ nào đỏ lên.
  Test canh: `test_nghi_phep_thong_bao_duyet.py`.
- Hai hook duyệt **khác nhau, đừng gọi nhầm**: `useLeaveRequestAction` bấm vào tờ
  ĐƠN (duyệt thẳng, chỉ chạy khi chưa khai luồng — nút này nay chỉ hiện khi
  `approval_instance_id === 0`), còn `useLeaveApprovalDecision` bấm vào PHIÊN DUYỆT.
- ⚠️ **Mục "Bàn giao công việc" LUÔN dựng, kể cả khi rỗng** — ở cả màn chi tiết
  lẫn hộp xác nhận duyệt. Trước 03/09/2026 nó ẩn hẳn khi không có ai, và người
  duyệt không phân biệt được *"người nộp chưa khai ai"* với *"màn hình thiếu mục
  đó"*. Mà **thiếu người bàn giao là lý do trả đơn phổ biến nhất**, tức chính là
  thứ quyết định họ bấm Duyệt hay Trả về — nó phải nói thành lời, không để suy ra
  từ một khoảng trống. Hộp việc duyệt trả kèm `handovers` đúng vì lý do đó.

#### Cài đặt nhân sự — tab Nghỉ phép (duoc-CR-713, 02/11/2026)

Trang `/hr/settings` (gác `setting.read`/`write`, đi chung `/api/settings`, nhóm khóa `hr`). Hai công tắc, mặc định TẮT:

- ⚠️ **Chặn đơn nghỉ lùi ngày** — chỉ đọc qua `leave/leave_policy.ensure_not_backdated`, gọi ở ĐỦ ba nhịp `create` ·
  `update` · `prepare_submit` (nháp hợp lệ để qua ngày mới gửi cũng là lùi ngày). **Hôm nay** = `vn_today()`. Miễn:
  vai trò khai ở `leave_backdated_roles` + `admin`. Thêm đường lập đơn mới (nhập Excel, trợ lý AI lập nháp…) thì phải
  gọi hàm này, đừng đọc thẳng `app_settings`.
- ⚠️ **Chặn tự duyệt đơn nghỉ** — chỉ đọc qua `approval/self_approval_policy`. Luật I08 (`exclude_submitter_ids`) CỐ Ý
  giữ bước khai đích danh + người dự phòng (CR-113, NP022); cờ `strict` chỉ siết cho `leave_request`. Mọi chỗ tra người
  duyệt cho một phiên phải truyền `strict=strict_self_exclusion(entity)` (mở chặng, đồng bộ luồng, xem trước) — sót một
  chỗ là màn xem trước nói một người, lúc chạy ra người khác. Chốt cuối ở `action_service.approve` + duyệt thẳng.
  Bước rỗng → người dự phòng → KẸT; đừng thêm nhánh tự duyệt qua.

#### Nghỉ phép kiểu ERPNext (duoc-CR-715, 02/11/2026)

- ⚠️ **Số dùng được = `balance_service.available_days(db, row)`**, KHÔNG phải `row.remaining_days`: loại nghỉ
  `accrual_mode = MONTHLY` giữ lại phần chưa tới tháng (`accrual_service.accrual_holdback`). Màn hình, chốt đủ quỹ, trợ lý
  AI đều phải đọc hàm này; chỗ đọc thẳng property chỉ đúng với năm đã qua (kết sổ cuối năm).
- Cấp quỹ (`ensure_balance`): hạn mức `accrual_service.resolve_quota` (hình thức nhân viên > cấp bậc > `annual_quota_days`)
  rồi `prorate_allocation` (ngày vào làm 1–15 tính cả tháng; vào làm năm SAU → 0). Quỹ đã cấp không tính lại khi đổi luật.
- `check_enough*` cho xuống `-max_negative_days`; `applicable_after_days` chặn ở lập / sửa (khi ngày hoặc dòng loại đổi) / gửi.
- ⚠️ **Ngày cấm nghỉ chặn ở hook `_on_approved` bằng `approval.entity_hooks.HookVeto`** — loại lỗi hook DUY NHẤT `fire`
  ném tiếp. Hook nào ném nó phải ném TRƯỚC khi đổi gì của chứng từ; đường duyệt không được commit trước lúc `fire`.
- ⚠️ **Phiếu nghỉ bù** (`leave_comp_request`, khóa quyền riêng, owner + self như đơn nghỉ): duyệt xong cộng
  `tab_leave_balance.comp_days` của loại `is_compensatory`; mọi chỗ cộng `allocated + seniority + carried + adjusted`
  phải cộng cả `comp_days`. Hủy phiếu đã duyệt chỉ khi số dùng được của loại đó ≥ `days`.
- ⚠️ Phiếu nghỉ bù LƯU SẴN đích cộng: `comp_leave_type_id` (chốt lúc gửi) + `balance_year` (= max(năm làm, năm nay),
  chốt lúc duyệt); duyệt / hủy chỉ dùng hai cột này, KHÔNG gọi lại `get_comp_type()` (HR đổi cờ giữa chừng là cộng /
  trừ nhầm loại). Mọi đổi trạng thái đi qua `comp_request_service.claim` (UPDATE … WHERE status IN …, thua → 409).
  `active_key` UNIQUE giữ **một ngày một phiếu** khi hai lượt chèn cùng lúc (NULL khi từ chối / hủy / xóa).
- ⚠️ Phiếu nghỉ bù LUÔN chặn tự duyệt (`self_approval_policy.ALWAYS_STRICT_ENTITIES`), bất kể công tắc: nó tạo ra ngày
  phép mới. Đơn nghỉ vẫn theo công tắc `leave_prevent_self_approval`.
- ⚠️ `entity_hooks.fire` gặp `HookVeto` thì TỰ `db.rollback()` rồi mới ném — nơi gọi bắt lỗi rồi commit (cổng MCP ghi
  nhật ký) không thể lưu nửa lượt duyệt. Thêm nơi gọi duyệt mới vẫn nên rollback ở nhánh lỗi.
- Báo cáo quỹ phép trừ phần chưa tới tháng ngay trong câu SQL (join loại nghỉ + ngày vào làm) — số truy vấn cố định.

#### Chính sách nghỉ phép + phân bổ (duoc-CR-717, 03/11/2026)

Chi tiết: `doc/erp/hrm/02-nghi-phep.md` §15. Module `leave/policy_*.py` — ⚠️ `leave/leave_policy.py` là của CR-713 (chặn
đơn lùi ngày), đừng đè / đừng nhầm.

- ⚠️ **Cấp quỹ chỉ đi qua `balance_service.ensure_balance` → `policy_allocation.allocated_days`** (hàm thuần
  `policy_allocation_math.compute_allocated`). Đừng mở đường cấp / tính `allocated_days` thứ hai (nhập Excel, trợ lý AI,
  kết sổ…). Thứ tự: phân bổ chính sách của người > hình thức NV > cấp bậc > `annual_quota_days`; loại vắng trong gói →
  luật của loại. Đổi gói giữa năm chia theo tháng, mốc ngày 15; phân bổ bắt đầu ≤ tháng vào làm kéo lùi về 01/01 (áp cả
  năm theo số của gói).
- ⚠️ **Không có phân bổ = kết quả CŨ, từng con số** (`prorate_allocation(resolve_quota(...))`, kể cả hạn mức lẻ 12.25) và
  không thêm truy vấn thứ hai. Có bài kiểm ghim — sửa toán thì giữ bất biến này.
- ⚠️ **Đường ghi phân bổ phải đọc có khóa** (MySQL REPEATABLE READ): khóa `tab_employee` FOR UPDATE theo id tăng dần
  (`lock_employees`), rồi MỌI lần đọc phân bổ / dòng gói / dòng quỹ sau đó qua `policy_allocation.with_row_lock`
  (`lock=True`). Đọc thường thấy ảnh chụp cũ → lọt chồng ngày / ghi đè `allocated_days` của lượt khác. SQLite không tái
  hiện được — kiểm bằng cách soi SQL biên dịch sang MySQL (`test_nghi_phep_review_cr717.py`).
- ⚠️ **Phạm vi người được phân bổ = phạm vi XEM `employee` ∩ phạm vi GHI `leave_balance`**
  (`policy_assignment_scope.writable_employee_query`), chỉ người **đang làm**. Không thêm khóa quyền: gói theo
  `leave_type`, phân bổ theo `leave_balance` (D4) — ENTITIES / `SCOPE_FIELDS` / seed giữ nguyên. Bảng phân bổ phải giữ
  `company_id` + `employee_id` vì `apply_scope(..., "leave_balance")` đọc hai cột đó.
- ⚠️ **D5: không ai trừ `is_system_admin` tự tạo / sửa / xóa phân bổ của chính mình** (403, cả hàng loạt → `skipped`).
- Xem trước và ghi dùng CHUNG `policy_assignment_plan.plan_change` — thêm chốt mới thì thêm ở đó, không thì màn xem trước
  hứa điều đường ghi chặn. Hàng loạt KHÔNG savepoint (nhả savepoint làm `change_tracker` đóng dấu commit sớm); cả lô một
  commit, số truy vấn cố định theo số người.
- Tính lại quỹ: chỉ năm `vn_today().year`, chỉ cột `allocated_days`, ghi nhật ký `leave_balance`; năm đã qua không bao giờ.
- Trạng thái phân bổ (`LeavePolicyAssignmentState` 1 Sắp tới · 2 Đang hiệu lực · 3 Đã kết thúc) DẪN XUẤT theo ngày, không lưu.
- Ma trận `/api/leave-balances/matrix` phải đăng ký router TRƯỚC `leave_balance_router` (không thì `/{bid}` nuốt); khóa
  `cells` là chuỗi id loại, ô vắng = chưa có dòng quỹ (khác 0).
- Báo cáo **ReportKey 30** `HOLIDAY_WORK` **Làm việc vào ngày lễ, ngày nghỉ**: nguồn phiếu nghỉ bù (không chấm công), gác kép
  `leave_comp_request` + `require_report(30)`; phòng ban = phòng ghi trên phiếu. Số 30 đã cấp, bỏ thì để trống, không tái dùng.
- Kỳ nghỉ phép (Leave Period): **không làm** (anh Được bỏ 03/11/2026) — đừng đề xuất lại.

#### Thanh toán nghỉ phép (duoc-CR-719, 03/11/2026)

Phiếu `tab_leave_encashment` (`TTP…`, khóa `leave_encashment`) chỉ ghi SỐ NGÀY; duyệt xong trừ quỹ và sinh YCTT nguồn
`leave_encashment` để kế toán nhập tiền. Tài liệu: `doc/erp/hrm/02-nghi-phep.md` §16.

- ⚠️ **`encashed_days` là khoản TRỪ, đã nằm trong `remaining_days`** (nên cả `available_days` / `available_days_map`).
  Mọi chỗ tự cộng trừ quỹ (báo cáo, kết sổ, nhập Excel, trợ lý AI) phải trừ nó, hoặc tốt hơn là đi qua `available_days`.
  Duyệt: `pending −= days`, `encashed_days += days` (KHÔNG cộng `used_days`); hủy phiếu đã duyệt: `encashed_days −= days`.
- ⚠️ **Chốt xem YCTT nghỉ phép nằm ở `core/scoping.scope_condition`** (vỏ bọc AND `hr_payout_guard.payout_visibility_cond`
  khi `entity == "payment_request"`): cần `leave_encashment.read` phủ phiếu nguồn, vì tiền ÷ ngày = lương ngày. Đừng tự
  lọc lại ở chỗ khác, đừng bỏ; đọc YCTT luôn qua `apply_scope` / `get_scoped` — **không bao giờ `db.get(PaymentRequest, id)`**
  ở đường người dùng chạm tới (kể cả công cụ AI, xuất Excel, chuông). Đường đọc thẳng mới phải khai vào
  `test_pham_vi_duong_vong.py` kèm lý do.
- Bốn hàm hợp đồng ở `payment_request/leave_encashment_payout.py`: `create_payout_request` (flush, KHÔNG commit) ·
  `payout_state` · `void_draft_payout` · `payout_allows_cancel`. YCTT được tạo **bên trong giao dịch duyệt**; chuông kế
  toán `notify_payout_created` chạy **sau commit** (`after_commit` trong `approve_now`, phiên mới) — `trigger_notification`
  luôn commit, gọi chung là commit lửng giao dịch duyệt.
- Hủy phiếu Đã duyệt chỉ khi YCTT **Nháp** (xóa mềm theo) hoặc **Đã từ chối** (D7a); YCTT Chờ duyệt / Đã duyệt / Đã chi →
  400. Đọc YCTT **có khóa dòng** (`payout_state(lock=True)`) trước khi trả ngày. Kế toán từ chối không tự hủy phiếu: phiếu giữ
  Đã duyệt, màn hiện băng **Kế toán từ chối chi**.
- Mọi đổi trạng thái đi qua `service.claim` (UPDATE … WHERE status IN …); thua → 409. Một phiếu còn hiệu lực / (người,
  loại, năm, **lý do**) bằng `active_key` UNIQUE (D4) — NULL khi Từ chối / Đã hủy / xóa, Đã duyệt vẫn giữ khóa. Lý do nằm
  trong khóa để phiếu nghỉ việc vẫn lập được sau phiếu cuối năm đã chi (BLLĐ Điều 113).
- ⚠️ **Người nhận tiền không bao giờ tự xử lý YCTT của mình** (sửa / gửi / duyệt / chi / từ chối → 403, kể cả admin) —
  chốt ở `payment_request/leave_encashment_payout.py`, không dựa vào quyền. Ngày mang sang đã thanh toán ghi riêng
  (`encashed_carried_days`) để hủy ngày mang sang hết hạn không trừ lần hai (quỹ âm).
- Nhật ký hệ thống che số tiền YCTT thanh toán nghỉ phép (`change_tracker` theo dòng; `logging_policy` che `amount` /
  `total` trên mọi đường `/api/payment-requests/...`).
- **Luôn chặn tự duyệt** (`ALWAYS_STRICT_ENTITIES`), như phiếu nghỉ bù.
- `employee/references.py` chặn xóa nhân sự còn `LeaveEncashment.employee_id` hoặc là `PaymentRequest.payee_employee_id`;
  loại nghỉ có phiếu (mọi trạng thái) không xóa được. Bật `allow_encashment` khi `counts_balance` tắt → 422.
- Trợ lý AI chỉ đọc (D8): `my_leave_summary` trả ngày + trạng thái, **không bao giờ trả số tiền**; không có công cụ soạn nháp.
- Khóa `leave_encashment` mới: hệ đang chạy phải tick tay (D-018), kể cả `read` phạm vi công ty cho vai trò Kế toán.

#### Quỹ phép bậc phòng ban + trợ lý tra phép (duoc-CR-757, 13/11/2026)

Chi tiết: `doc/erp/hrm/02-nghi-phep.md` §17, `doc/erp/hrm/03-lich-lam-viec.md` §19–§21.

- ⚠️ **Bậc `dept` của `leave_balance` nay là "người thuộc phòng của tôi", không còn là cả công ty.** Bảng quỹ không có cột
  phòng nên `SCOPE_FIELDS["leave_balance"]` khai `dept_via_employee: "employee_id"`: điều kiện là truy vấn con trên
  `tab_employee` (bí danh) — phòng CHÍNH của người giữ quỹ ∈ `dept_ids` của người xem (gồm kiêm nhiệm của NGƯỜI XEM) VÀ
  `tab_employee.company_id` ∈ công ty hiện tại của người xem (chính + kiêm nhiệm loại Công ty). Ô **Phòng ban được xem** và
  bậc `dept_proc` của quỹ phép đi cùng đường đó (không mở xuyên công ty). Mọi chỗ đọc quỹ qua `apply_scope` / `get_scoped` /
  `scope_condition` tự hưởng — đừng tự lọc lại theo phòng.
- ⚠️ **`tab_leave_balance.company_id` là ẢNH CHỤP lúc cấp quỹ** (local: nhiều dòng `= 0` hoặc lệch công ty hiện tại). Bậc
  `dept` đã tránh bằng cách ràng công ty HIỆN TẠI của nhân sự; bậc `company` và ô **Chỉ trong / Loại trừ công ty** vẫn so cột
  của dòng nên dòng cũ lệch công ty không hiện ở đó (giới hạn G3, ngoài CR này — chờ điền lùi `company_id`).
- Hệ đang chạy: vai trò nào đặt `leave_balance` bậc `dept` sẽ HẸP lại sau deploy (trước là cả công ty) — đếm trước khi
  deploy, câu SQL ở `03-lich-lam-viec.md` §21. Màn phân bổ chính sách (`writable_employee_query`) hẹp theo cùng luật.
- Trợ lý: `employee_leave_summary` (người khác) gác `leave_balance.read`; số ngày đã nghỉ của người khác còn qua phạm vi
  `leave_request` (thiếu thì rỗng). Năm của đơn = năm `from_date` (khớp sổ quỹ, lệch báo cáo Tình hình nghỉ phép ở đơn vắt
  hai năm).
