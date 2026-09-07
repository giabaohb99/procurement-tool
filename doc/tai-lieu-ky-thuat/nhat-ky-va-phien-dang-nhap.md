# NHẬT KÝ THAY ĐỔI DỮ LIỆU & PHIÊN ĐĂNG NHẬP — KẾ HOẠCH

**Bản:** 1.0 — 07/09/2026 · **CR:** bao-CR-312 · **Trạng thái: ĐỀ XUẤT, CHƯA LÀM.**

Tệp này là bản thiết kế để bàn, không phải mô tả thứ đang chạy. Mọi thứ dưới đây **chưa có
một dòng mã nào**. Đọc kèm `change-log-bao.md` (dòng bao-CR-311 — dấu vết gắn phương án, đã
làm) vì hai việc chung một gốc.

---

## 1. Vì sao

Ngày 07/09/2026 khách báo một phiếu Yêu cầu báo giá (YCBG05092603) hiện kết quả khảo sát của
mặt hàng khác. Truy ra được, nhưng **truy bằng cách đọc cột `created_by` trên chính dòng dữ
liệu** — không màn hình nào hiện nó, phải vào tận database. Nhật ký của phiếu **trống trơn**.

Đó không phải một lỗ thủng lẻ. Ba lỗ thủng nằm cùng chỗ:

| Câu hỏi | Trả lời được không |
|---|---|
| *Ai* đã đổi? | Được, nếu chỗ đó có gọi `record(...)`. Tùy lập trình viên nhớ hay quên. |
| Đổi **từ giá trị nào sang giá trị nào**? | **KHÔNG.** Cả hệ chỉ lưu một câu chữ, không lưu giá trị cũ. |
| Người đó thao tác **từ đâu, bằng máy nào**? | **KHÔNG**, trừ đúng lúc đăng nhập. |

Đo trên bản đang chạy (07/09/2026):

- `tab_audit_log` có **4.139 dòng**, **3.365 dòng trong 30 ngày** (~112 dòng/ngày), **0,8 MB**.
- Bảng chỉ có 4 cột nghiệp vụ: `entity`, `entity_id`, `action`, `message`. Không IP, không
  thiết bị, không giá trị cũ/mới.
- **213 lời gọi `record(...)` nằm rải trong 54 tệp.** Ghi hay không ghi là do người viết mã
  quyết định từng chỗ một — nên chỗ nào quên thì im lặng vĩnh viễn, đúng như YCBG05092603.
- Đăng nhập **có** ghi IP, nhưng nhét trong câu chữ (`"Đăng nhập thành công (IP 1.2.3.4)"`) —
  không lọc được, không thống kê được, và không có user-agent.
- Token JWT chỉ mang `sub` (id người dùng) + `type` + `exp`. **Không có định danh phiên**, nên
  không có cách nào nối một thao tác về đúng lần đăng nhập nào đã sinh ra nó. Kèm theo: đăng
  xuất hiện chỉ xóa token ở trình duyệt, token cũ vẫn còn hiệu lực tới khi hết hạn — **không
  thu hồi được**.

---

## 2. Nguyên tắc: HAI lớp nhật ký, không gộp

Sai lầm dễ mắc là nhồi giá trị cũ/mới vào `tab_audit_log`. Đừng. Hai lớp phục vụ hai người
đọc khác nhau, trộn vào là hỏng cả hai.

| | Lớp KỂ CHUYỆN | Lớp MÁY GHI |
|---|---|---|
| Bảng | `tab_audit_log` (đang có) | `tab_change_log` (**mới**) |
| Ai đọc | Người dùng thường, trên dòng thời gian của phiếu | Quản trị / lúc truy sự cố |
| Nội dung | Một câu tiếng Việt: *"Duyệt phiếu YCMH0912"* | Trường nào đổi, từ gì sang gì |
| Sinh ra bởi | Lời gọi `record(...)` do người viết mã đặt | **Tự động** ở tầng ORM, không ai đặt tay |
| Bỏ sót được không | Có — và đã bỏ sót | **Không.** Đổi dữ liệu là có dòng |

Điểm cốt lõi của cả kế hoạch nằm ở ô cuối cùng bên phải: **lớp máy ghi không được phép phụ
thuộc vào trí nhớ của người viết mã.** Nếu nó cũng là một lời gọi phải đặt tay thì năm sau
mình lại ngồi đọc `created_by` trong database lần nữa.

---

## 3. Ba bảng

### 3.1. `tab_login_session` — mỗi lần đăng nhập một dòng

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | BIGINT | |
| `user_id` | BIGINT, index | |
| `token_id` | CHAR(36), unique | UUID, **nhét vào claim `jti` của token** — đây là sợi dây nối |
| `ip` | VARCHAR(45) | IPv6 dài 45 ký tự, đừng để 15 |
| `user_agent` | VARCHAR(500) | nguyên văn |
| `device`, `os`, `browser` | VARCHAR(60) | bóc từ user-agent lúc ghi, để lọc/thống kê |
| `login_method` | SMALLINT | 1 mật khẩu · 2 Google (R2/QĐ-11: số + IntEnum) |
| `last_seen_at` | DATETIME | dập lại mỗi lần gọi API, **tiết lưu 5 phút một lần** |
| `revoked_at`, `revoked_by` | DATETIME / BIGINT | đăng xuất hoặc bị thu hồi từ xa |

**Đăng nhập thất bại ghi chung bảng này** (thêm cột `ok BOOLEAN`) hay ghi riêng — xem câu hỏi
Q5. Nghiêng về ghi chung: dò mật khẩu là **cùng một IP thử nhiều tài khoản**, tách hai bảng là
phải join mới thấy.

Được thêm miễn phí khi có bảng này: **thu hồi phiên**. `get_current_user` tra `jti` → phiên bị
`revoked_at` thì 401. Đổi mật khẩu thì thu hồi mọi phiên khác. Đây là thứ hiện tại **không làm
được**.

Cái giá phải trả, nói thẳng: mỗi lời gọi API thêm **một truy vấn tra phiên**. Hiện `get_current_user`
chỉ giải mã token, không đụng DB cho phần này. Giảm đau bằng bộ nhớ đệm trong tiến trình 60 giây,
đúng khuôn `_PERM_CACHE` sẵn có — đổi lại thu hồi phiên trễ tối đa 60 giây, chấp nhận được.

### 3.2. `tab_change_log` — trước và sau

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `id` | BIGINT | |
| `table_name` | VARCHAR(64), index | tên bảng thật, vd `tab_survey_request_option` |
| `row_id` | BIGINT, index | |
| `op` | SMALLINT | 1 thêm · 2 sửa · 3 xóa |
| `before_json` | JSON | |
| `after_json` | JSON | |
| `session_id` | BIGINT, index | trỏ `tab_login_session.id` — **từ đây ra IP/thiết bị** |
| `request_id` | CHAR(36), index | gom mọi dòng sinh trong CÙNG một lời gọi API |
| `created_by`, `created_at` | | chuẩn `AuditMixin` |

`request_id` là thứ hay bị quên mà lại quan trọng nhất lúc truy: một lần bấm "Duyệt" đụng vào
5 bảng. Không có nó thì 5 dòng nằm rời rạc, có nó thì gõ một mã ra nguyên **một thao tác**.

**Sinh dòng bằng sự kiện của SQLAlchemy**, không phải bằng lời gọi tay:

```
before_flush  → duyệt session.new / session.dirty / session.deleted
              → inspect(obj).attrs.<ten_cot>.history cho ra (giá trị cũ, giá trị mới)
after_flush   → có id của dòng vừa thêm thì ghi nốt
```

Ba cái bẫy đã biết, phải xử ngay từ đầu chứ đừng để nổ ở prod:

1. **`record(...)` tự `db.commit()`.** Nhiều service commit nhiều nhịp trong một lời gọi. Gom
   dòng thay đổi vào một danh sách theo `request_id` rồi ghi ở cuối, đừng ghi giữa flush —
   ghi trong flush là đệ quy.
2. **Ngữ cảnh không nhìn thấy được từ trong sự kiện ORM.** Sự kiện không biết ai đang gọi.
   Phải có middleware đặt `ContextVar` (user_id, session_id, request_id, ip) ở đầu mỗi lời
   gọi API. Việc chạy nền (Celery sao lưu, script nhập liệu) không có ngữ cảnh → ghi
   `created_by = 0` và một nhãn nguồn, **đừng gán bừa cho một người**.
3. **Che dữ liệu nhạy cảm.** `password_hash`, `google_sub`, mọi token — **không bao giờ** vào
   JSON. Danh sách cột cấm khai một chỗ, mặc định là **cấm hết trừ khi cho phép** đối với bảng
   `tab_user`. Ghi nhầm một lần là chuỗi băm mật khẩu nằm trong nhật ký vĩnh viễn.

### 3.3. `tab_audit_log` — thêm ba cột

`session_id`, `request_id`, `ip`. Dòng cũ để `NULL`, **không backfill được** — dữ liệu đó chưa
từng tồn tại. Nói trước để sau này không ai đi tìm.

---

## 4. Dung lượng — con số thật, không phải cảm giác

Hôm nay: 112 dòng nhật ký/ngày, 0,8 MB tổng.

| Cách ghi | Cỡ mỗi dòng | Một năm |
|---|---|---|
| Chụp **nguyên bản ghi** cả trước lẫn sau | ~3 KB (ĐMH có ~60 cột) | **~550 MB** |
| Chỉ ghi **trường thực sự đổi** (khuyến nghị) | ~200 B | **~40 MB** |

Chênh gần 14 lần. Khuyến nghị: **chỉ ghi trường đổi cho thao tác SỬA**, chụp nguyên bản ghi
cho THÊM và XÓA (hai ca này cần dựng lại được cả dòng). Xóa vẫn dựng lại được đầy đủ, sửa vẫn
truy được ai đổi gì — mà tốn 1/14. Đây là câu hỏi Q1, đại ca chốt.

Giữ bao lâu: đề xuất **12 tháng** rồi dọn bằng việc chạy nền hằng đêm (Celery beat đã chạy
thật ở prod, xem `celery-thuc-te-prod`). Không giới hạn thì 3 năm nữa bảng này to hơn cả dữ
liệu nghiệp vụ.

---

## 5. Chia đợt

| Đợt | Nội dung | Phụ thuộc |
|---|---|---|
| **P1** | `tab_login_session` + `jti` trong token + middleware `ContextVar` + bóc user-agent | — |
| **P2** | Màn *Phiên đăng nhập*: tab ở Trang cá nhân (tự xem của mình) + màn quản trị (xem tất cả, thu hồi) | P1 |
| **P3** | `tab_change_log` + sự kiện SQLAlchemy + che cột nhạy cảm + `request_id` | P1 |
| **P4** | Ba cột mới trên `tab_audit_log`; dòng thời gian nhật ký hiện thêm tab *Thay đổi* (bảng trường / cũ / mới) | P3 |
| **P5** | Dọn dữ liệu cũ theo hạn (Celery beat) | P3 |
| **P6** | Cảnh báo: đăng nhập từ IP lạ, xóa hàng loạt trong một `request_id` | P3 |

P1 làm trước vì cả P3 lẫn P4 đều cần `session_id`. Làm ngược là phải sửa lại hai lần.

**Phân quyền.** Cần khóa mới cho hai màn — hiện `ENTITIES` có **53** mục và `SCOPE_FIELDS`
khai đủ **53/53** (test `test_pham_vi_khai_du_b07.py` canh, thêm entity mà quên khai là test
đỏ). Đề xuất thêm `login_session` và `change_log`, cùng khai `PUBLIC` hoặc `own` tùy Q3 →
`ENTITIES` lên 55. Nhớ: vai trò đang chạy **không tự có** khóa mới (seed không ghi đè, D-018),
phải tick tay ở màn Phân quyền hoặc `SEED_FORCE_SYNC=true` một lần.

---

## 6. Câu hỏi phải chốt trước khi gõ mã

| | Câu hỏi | Nghiêng về |
|---|---|---|
| **Q1** | Sửa thì ghi **trường đổi** hay chụp **nguyên bản ghi**? | Trường đổi (40 MB/năm thay vì 550 MB/năm) |
| **Q2** | Giữ nhật ký thay đổi bao lâu? | 12 tháng |
| **Q3** | Ai đọc được `tab_change_log`? Chỉ quản trị (`setting`), hay ai đọc được chứng từ thì đọc được lịch sử của nó? | Quản trị. **Giá trị cũ có thể chứa tên NCC**, mà cả cơ chế phương án là để giấu NCC với người yêu cầu |
| **Q4** | Có làm **thu hồi phiên từ xa** không (đăng xuất máy khác)? | Có — bảng đã có sẵn cột, thêm gần như không tốn |
| **Q5** | Đăng nhập **thất bại** ghi chung bảng phiên hay bảng riêng? | Chung, thêm cột `ok` |
| **Q6** | Có ghi cả lượt **XEM** (mở phiếu, xuất Excel) không? | Chỉ ghi **xuất dữ liệu** và **xem tệp đính kèm**; ghi mọi lượt xem thì bảng phình mà gần như không ai đọc |

---

## 7. Những gì kế hoạch này KHÔNG làm

- **Không dựng lại được lịch sử đã qua.** Từ ngày bật trở đi mới có dữ liệu.
- **Không thay được sao lưu.** Nhật ký thay đổi để truy trách nhiệm, không phải để khôi phục
  dữ liệu.
- **Không chặn thao tác sai** — chỉ ghi lại. Muốn chặn thì là việc khác, ở từng nghiệp vụ.
