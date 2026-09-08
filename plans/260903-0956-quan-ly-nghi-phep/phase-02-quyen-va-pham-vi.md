# P-02 — Quyền và phạm vi ✅ XONG (CR-259)

## Đã làm

- **Bốn entity mới** vào `core/permissions.ENTITIES` + nhãn:
  `leave_request` · `leave_balance` · `leave_type` · `holiday`.
- **Khai đủ ở `SCOPE_FIELDS`** (`core/scoping.py`) — B-07 bắt buộc, thiếu là test đỏ.
- Bốn khóa vào `frontend-v2/src/core/authorization/permission-types.ts`.
- Vai trò: mọi vai trò được `leave_request` (`own`) + `leave_balance` xem (`own`) +
  hai danh mục chỉ đọc; `dept_head` duyệt phạm vi `dept`; `company_head` phạm vi
  `company`; thêm vai trò mẫu **`hr_leave`**. Bốn khóa nằm trong `_SYS_ENTITIES`
  nên **không** rơi vào `_PUR_MANAGER_PERMS`.
- Test `test_pham_vi_khai_du_b07.py`: 46 → **50** entity.

## Quyết định đáng ghi

- **Bốn khóa chứ không một.** `leave_balance` ghi được nghĩa là **tặng thêm ngày
  phép cho bất kỳ ai** (cột điều chỉnh tay). Gộp với `leave_request` thì cho ai
  xem đơn của mình là cho họ tự cộng phép.
- **`leave_request` khai CẢ `owner` LẪN `self`** — điểm khác mọi entity phía trên
  trong `SCOPE_FIELDS`. Một tờ đơn có hai người dính tới nó: người **lập**
  (`created_by`, hành chính lập hộ là việc có thật) và người **nghỉ**
  (`employee_id`). Chỉ khai một cái là một trong hai mất dấu tờ đơn.
  Kèm theo là một sửa nhỏ ở nhánh `own` của `_role_scope_cond`: HỢP cả hai điều
  kiện, và **chặn khi `employee_id = 0`** (nếu không thì `== 0` trúng mọi dòng
  chưa gắn nhân sự, tức là **mở rộng** phạm vi thay vì thu hẹp).
- **`leave_balance` chỉ khai `self`**, không khai `owner`: `created_by` là người
  Nhân sự bấm nút cấp phát; lấy đó làm "của mình" thì nhân viên xem quỹ của chính
  họ lại không ra dòng nào.
- **`holiday` khai `PUBLIC` dù bảng CÓ `company_id`**: `0` ở đó nghĩa là "áp cho
  mọi pháp nhân", mà lọc `company_id == <của tôi>` thì cắt mất đúng những dòng
  dùng chung ấy. Phép gộp đúng nằm ở `workday_service.holiday_dates()`.

## Việc còn lại của người vận hành

⚠️ Seed **không ghi đè** phân quyền đã chỉnh tay (D-018), nên trên hệ đang chạy
các vai trò cũ **không tự có** bốn khóa này. Phải tick thêm ở
*Nhân sự ▸ Phân quyền tài khoản*, hoặc chạy một lần với `SEED_FORCE_SYNC=true`.
