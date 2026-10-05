---
paths:
  - "backend/app/modules/leave/**"
  - "backend/app/modules/approval/**"
  - "frontend-v2/src/modules/hr/**"
  - "test/backend/*nghi_phep*"
  - "doc/tai-lieu-chuc-nang/17-nghi-phep.md"
---
# Phân hệ NGHỈ PHÉP (CR-259, 03/09/2026)

> Chuyển nguyên văn từ CLAUDE.md gốc ngày 01/10/2026 — chỉ nạp khi làm việc với các đường dẫn ở trên.


Nằm **trong phân hệ Nhân sự** (`frontend-v2/src/modules/hr/`, menu *Nghỉ phép*),
backend ở `app/modules/leave/`. Tài liệu đầy đủ: `doc/tai-lieu-chuc-nang/17-nghi-phep.md`.

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
  dùng chung một khoảng ngày, dòng chỉ chia SỐ NGÀY. Hai cột đầu đơn thành **dẫn
  xuất**: `total_days` = tổng các dòng, `leave_type_id` = loại của dòng nhiều ngày
  nhất. **Sổ quỹ phải chạy THEO DÒNG ở cả bốn nhịp** — dùng `reserve_lines` ·
  `consume_lines` · `release_lines` · `refund_lines` của `request_service`, đừng gọi
  thẳng `balance_service` với `obj.total_days` (trừ tổng vào loại chính là cộng ngày
  không lương vào quỹ phép năm). Chốt xóa loại nghỉ phải hỏi **cả hai bảng**. Điều
  kiện rẽ nhánh luồng duyệt chỉ thấy loại CHÍNH — hạn chế đã biết, xem §7.1 của
  `doc/tai-lieu-chuc-nang/17-nghi-phep.md`.
- ⚠️ **Số phép còn lại KHÔNG lưu thành cột** — `balance_service.remaining()` là nơi duy
  nhất tính. **Số ngày nghỉ** chỉ tính ở `workday_service.count_leave_days()` — **SỬ DỤNG LỊCH LÀM VIỆC của người nghỉ** (`work_schedule/resolver.load_day_plans`), không còn `WEEKEND_DAYS`. Gọi `count_leave_days()` hoặc `count_hourly_days()` **PHẢI truyền `employee=`**, nếu quên thì sẽ tính theo lịch mặc định cho người có lịch riêng, dẫn tới sai âm thầm. Xem chi tiết ở `doc/tai-lieu-chuc-nang/21-lich-lam-viec.md` §7, §12.
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
  trần. Hai tín hiệu mất theo, đừng tưởng là sót: dấu **«Quá hạn»** (cờ
  `task.is_overdue` backend vẫn gửi, màn hình thôi không vẽ — bày lại thì đọc cờ
  đó, đừng tự so ngày ở TS) và dòng **«Bấm thay ‹tên›»**, thứ báo cho người được
  ủy quyền biết họ đang ký THAY người khác; nay chỉ còn ở màn chi tiết. Chi tiết
  ở §8.1 của `doc/tai-lieu-chuc-nang/17-nghi-phep.md`.
- ⚠️ **`defaultHidden` KHÔNG áp cho người đã từng đụng menu «Cột»** của bảng đó:
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
- ⚠️ **Mục «Bàn giao công việc» LUÔN dựng, kể cả khi rỗng** — ở cả màn chi tiết
  lẫn hộp xác nhận duyệt. Trước 03/09/2026 nó ẩn hẳn khi không có ai, và người
  duyệt không phân biệt được *"người nộp chưa khai ai"* với *"màn hình thiếu mục
  đó"*. Mà **thiếu người bàn giao là lý do trả đơn phổ biến nhất**, tức chính là
  thứ quyết định họ bấm Duyệt hay Trả về — nó phải nói thành lời, không để suy ra
  từ một khoảng trống. Hộp việc duyệt trả kèm `handovers` đúng vì lý do đó.
