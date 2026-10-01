---
paths:
  - "backend/app/modules/employee/**"
  - "backend/app/seed*.py"
  - "frontend-v2/src/modules/hr/**"
  - "frontend-v2/src/shared/utils/name-initials.ts"
  - "test/backend/*ho_so*"
  - "test/backend/*nhan_su*"
  - "doc/erp/hrm/**"
---
# Hồ sơ nhân sự mở rộng và danh mục Chức vụ

> Chuyển nguyên văn từ CLAUDE.md gốc ngày 01/10/2026 — chỉ nạp khi làm việc với các đường dẫn ở trên.

### HỒ SƠ NHÂN SỰ mở rộng (duoc-CR-314, 08/09/2026 — Đợt 1/4)

Thiết kế + nhật ký từng đợt: `doc/erp/hrm/01-ho-so-nhan-su.md`. Đợt 1 (nền dữ liệu)
và Đợt 2 (màn hình `frontend-v2`) đã xong; Đợt 3 xong phần lớn — **còn thiếu K3** (duyệt theo
quản lý trực tiếp) và màn kiểm việc treo trước khi khóa. Danh sách còn treo: §7.10 của tài liệu
đó; tình trạng cả lộ trình HRM: §0 của `doc/erp/tham-khao-hrm/10-de-xuat-ap-dung.md`.

- `tab_employee` thêm **30 cột** + `extra_fields` (JSON, trần 20 khóa) và hai bảng
  con `tab_employee_contact` · `tab_employee_family`. Bốn ô phân loại lưu
  **SMALLINT + bộ mã số** ở `employee/constants.py` (R2/QĐ-11); `Employee.status`
  vẫn là mã CHUỖI — ngoại lệ lịch sử B-03, đừng lấy làm mẫu.
- ⚠️ **Khóa quyền mới `employee_sensitive`** (ENTITIES **53 → 54**). Che **15
  trường** (ngày sinh · MST · địa chỉ nhà · ngân hàng · CCCD · số BHXH) ở **tầng
  serializer** — `modules/employee/sensitive.py` là nơi DUY NHẤT khai danh sách
  đó. Ẩn ô trên giao diện là vô nghĩa: API, CSV và trợ lý AI đi đường khác.
  **Cửa GHI cũng che.** Ngoại lệ `self`: ai cũng đọc đủ hồ sơ của chính mình
  (nhánh này chặn `employee_id = 0`, nếu không «chưa gắn ai» khớp mọi hồ sơ).
- ⚠️ **Thêm entity mới vào `ENTITIES` thì phải hỏi: nó có nên rơi vào
  `_SYS_ENTITIES` của `seed.py` không?** `_PUR_MANAGER_PERMS` là
  `{e: ALL for e in ENTITIES if e not in _SYS_ENTITIES}` — quên một dòng là Quản
  lý thu mua tự nhiên có khóa đó. Với `employee_sensitive` nghĩa là đọc được CCCD
  + tài khoản ngân hàng của toàn công ty. Có test canh
  (`test_ho_so_nhan_su_dot1.py`).
- ⚠️ **Hai bảng con CỐ Ý không có khóa phân quyền riêng** — chúng không có màn
  hình riêng (luật «một khóa = một màn hình», CR-157) và phạm vi của chúng không
  diễn đạt được bằng khuôn một-cột của `apply_scope` (bảng con chỉ có
  `employee_id`). Chốt là **hai lớp của hồ sơ CHA**: `get_scoped(Employee, ...)`
  → 404 ngoài phạm vi, rồi `employee_sensitive.read` → 403. Bản thiết kế K2 ghi
  3 khóa mới là chưa tính tới điều đó, xem §5.4.
- ⚠️ **`manager_id` không phải trường hiển thị cho đẹp** — đó là dữ liệu mà
  `APPROVER_DIRECT_MANAGER` (Đợt 3) sẽ đọc. `block_manager_cycle` chặn vòng, kể
  cả vòng dài A→B→C→A: vòng lặp **không nổ lúc lưu hồ sơ**, nó nổ lúc ai đó nộp
  đơn nghỉ phép, ở một tệp không có chữ `employee` nào. Xóa hồ sơ thì gỡ
  `manager_id` của cấp dưới về `0` (id chết → bộ máy duyệt lùi IM LẶNG).
- ⚠️ **Cột mới có `default=` trên model vẫn ra `None` khi bản ghi chưa flush** —
  `default` là mặc định lúc INSERT. Thiếu validator `mode="before"` thì
  `EmployeeOut.model_validate()` ném 26 lỗi cùng lúc và **cả màn danh sách nhân
  sự trả 500** vì một ô chưa ai nhập. Cùng bài học `_gender_none_is_unknown`.
- ⚠️ Trên hệ ĐANG CHẠY, vai trò cũ **không tự có** `employee_sensitive` (D-018):
  tick ở màn Phân quyền, hoặc `SEED_FORCE_SYNC=true` một lần rồi trả về `false`.
  Vai trò mẫu seed sẵn: **`hr_profile`** — "Nhân sự — Hồ sơ nhân viên".
  Kèm theo: người **đang đăng nhập giữ map quyền CŨ** tới khi đăng xuất/đăng
  nhập lại — thêm entity xong mà màn hình vẫn báo thiếu quyền thì đó là lý do,
  đừng đi tìm lỗi ở `require()`.

Màn hình ở `frontend-v2` (duoc-CR-315, Đợt 2/4):
`/hr/employees/:id` nay **5 tab**, tab nhớ ở URL `?tab=`; danh sách có 3 cột mới
+ cảnh báo «Chưa gán» quản lý trực tiếp (K5).

- ⚠️ **`pickWritableProfile` (`hr/schemas/employee-schema.ts`) là chốt chống MẤT
  DỮ LIỆU — đừng gỡ.** Backend che trường nhạy cảm bằng **chuỗi rỗng**, nên
  người có `employee.write` mà thiếu `employee_sensitive.read` mở hồ sơ ra sửa
  số điện thoại rồi bấm Lưu là **PATCH rỗng đè lên số tài khoản ngân hàng thật**
  — không ai biết cho tới kỳ trả lương. Backend **cố ý không tự chặn**: nó không
  phân biệt được "gửi rỗng vì bị che" với "gửi rỗng vì muốn xóa ô đó". Chỗ duy
  nhất biết là nơi dựng form. `SENSITIVE_PROFILE_FIELDS` (13 trường) phải khớp
  `SENSITIVE_FIELDS` của `backend/.../employee/sensitive.py`; lệch là lủng.
- ⚠️ **Ô bị che trông y hệt ô chưa ai nhập.** Luôn dựng `SensitiveFieldsNotice`
  khi `can('employee_sensitive','read')` sai — không có nó thì người dùng đọc hồ
  sơ và tin rằng công ty chưa có số tài khoản ngân hàng của người đó.
- **MỘT form cho cả 4 tab đầu.** Radix hủy mount tab ẩn nhưng react-hook-form giữ
  giá trị trong `useForm` chứ không trong DOM — sửa ở tab này, bấm Lưu ở tab kia
  vẫn gửi đủ. Hai bảng con và hai ảnh CCCD **ngoài** form đó: cửa API riêng, khóa
  quyền riêng, nút Lưu riêng.
- Bộ mã số của hồ sơ gõ tay ở `hr/types/employee-codes.ts` (`gen_status_ts.py`
  chỉ sinh cho bộ mã CHUỖI) — cùng cảnh với `hr/types/leave.ts`. Có test chốt số
  mục, nhưng đổi ở backend vẫn phải nhớ sửa tay bên này.

### Danh mục CHỨC VỤ (duoc-CR-320, 08/09/2026)

Ô «Vị trí / Chức vụ» nay là **ô CHỌN** đọc từ `tab_job_position`; màn quản lý ở
`/hr/job-positions`. Khóa quyền mới **`job_position`** (ENTITIES **54 → 55**,
PUBLIC ở `SCOPE_FIELDS`); seed cấp `read` cho MỌI vai trò vì ô chọn cần nó, sửa
thì chỉ `hr_profile`. Chi tiết: `doc/erp/hrm/01-ho-so-nhan-su.md` §7.7.

- ⚠️ **HAI CỘT CHO MỘT SỰ THẬT.** `tab_employee.position_id` là khóa,
  `tab_employee.position` là **nhãn đã chép** — giữ cột chữ vì mười chỗ đọc
  thẳng nó (bản in YCMH/YCBG, tệp Excel, `core/audit`, trợ lý AI). Toàn hệ chỉ
  có **hai đường ghi** vào cột nhãn, cả hai ở `employee/position_service.py`:
  `sync_label` (lưu hồ sơ) và `propagate_rename` (đổi tên trong danh mục). Thêm
  đường thứ ba là nhãn trôi, và **bản in đưa cho khách ra tên cũ** trong khi màn
  hình hiện tên mới.
- ⚠️ **Luật «khóa = 0 thì xóa nhãn» CHỈ đúng ở đường CẬP NHẬT** (người dùng vừa
  bỏ chọn). Áp cả lúc TẠO thì đường nhập CSV / seed — những nơi chỉ truyền chữ —
  làm hồ sơ **mất chức danh ngay khi ra đời**, im lặng.
- ⚠️ **Chức vụ đã ngừng dùng: chặn gán MỚI, nhưng hồ sơ đang giữ vẫn lưu được.**
  Màn hồ sơ gửi lại mọi ô mỗi lần lưu, nên không có ngoại lệ đó thì người đó
  không sửa nổi ô nào khác cho tới khi ai đi đổi chức vụ của họ.
- ⚠️ Đừng lẫn với **`job_level` (Cấp bậc)** — thang bậc CỐ ĐỊNH bảy mức khai
  trong mã nguồn (`employee/constants.py`), dùng để lọc và làm báo cáo cơ cấu.
  Chức vụ là chức danh cụ thể in trên phiếu, người dùng tự thêm bớt.
- ⚠️ Lọc danh sách nhân sự theo chức vụ đi bằng **`position_id`**, không bằng
  chữ: lọc bằng chữ thì đổi tên là bộ lọc đã lưu trượt sạch, và `contains` khớp
  cả chuỗi con («Phó phòng» lọt vào kết quả tìm «Trưởng phòng»).
- ⚠️ **Danh sách cột của bảng KHÁC danh sách ô nhập** (duoc-CR-321). `sort_order`
  và `department_id` còn dưới DB nhưng **cố ý không lên giao diện**: cột thứ tự
  là khái niệm của người dựng hệ thống (bảng hiện toàn 10·20·130, không chỗ nào
  giải nghĩa), còn «phòng ban thường giữ» không chặn gì cả nên hỏi cũng bằng
  thừa. Ô chọn chức vụ vì thế **phải khai `sort_by=name`** — mặc định của
  `make_crud_router` là `id desc`, tức danh sách tự đổi chỗ mỗi lần có ai thêm
  một dòng.
- ⚠️ **Hai cột đếm ngược («Đang giữ» · «Phòng ban đang giữ») và đường API
  `/api/job-positions/stats` ĐÃ BỎ** (duoc-CR-426, 19/09/2026) — cùng hai hàm
  `count_holders_by_department` / `list_holder_faces`. Đừng dựng lại theo
  serializer: đếm trong serializer là N+1, chạy cả ở những chỗ chỉ cần tên chức
  vụ. Còn muốn biết ai đang giữ thì mở tab **«Người đang giữ»** ở trang chi tiết
  (đọc thẳng `/api/employees?position_id=`, phân trang thật). Chốt chặn xóa vẫn
  dùng `count_employees` và vẫn **đếm toàn công ty** (không lọc phạm vi) vì đó là
  toàn vẹn dữ liệu — câu chặn nói rõ «trên toàn công ty».
- ⚠️ **Cột nhận diện trên bảng là `id`, không phải `code`** (cùng CR): mã
  `cv-truong-phong-…` dài bằng cả tên, luôn cụt đuôi trong ô bảng, và chỉ là khóa
  cho tệp CSV nhập/xuất. Mã vẫn nằm trong biểu mẫu và vẫn lọc được ở bộ lọc nâng
  cao — đừng tưởng nó đã bỏ.
- ⚠️ Ô lọc phòng ban của tab «Người đang giữ» nay đọc **danh mục phòng ban**
  (`useDepartments`, tự tắt khi thiếu `department.read`), nên nó liệt kê MỌI
  phòng chứ không riêng phòng đang có người giữ, và không còn kèm số người. Mục
  **«(Chưa gắn phòng ban)»** phải tự thêm bằng tay: `department_id = 0` là bộ lọc
  thật nhưng danh mục không có dòng nào mang id 0.
- Nút _Thêm chức vụ_ mở **trang riêng** `/hr/job-positions/new`
  (`CrudConfig.createRoute`) chứ không phải hộp thoại — khuôn có sẵn, dùng chung
  với Loại nghỉ · Phòng họp · Ngày lễ · Xe · Tài xế. Lý do không phải form dài
  (4 ô) mà là mỗi ô kéo theo một hệ quả phải đọc TRƯỚC khi gõ, hộp thoại thì
  buộc cắt ngắn cho vừa khung.
- ⚠️ **Chữ viết tắt trong vòng tròn ảnh**: tên NGƯỜI lấy hai từ **cuối**
  (`nameInitials`), tên PHÒNG BAN lấy hai từ **đầu** (`departmentInitials`) (họ Việt
  đứng trước nên phần phân biệt ở cuối; tên phòng đọc xuôi nên ở đầu — lấy hai
  từ cuối thì «Công nghệ thông tin» ra «TT», trùng «Truyền thông»). Cả hai hàm ở
  `shared/utils/name-initials.ts`.
- Trang chi tiết chạy hết bề ngang (`detailMaxWidth: 'max-w-none'`) vì có tab
  **«Người đang giữ»** — bảng nhân sự phân trang thật, kèm ô tìm kiếm và hai ô
  lọc *phòng ban* · *tình trạng*.
