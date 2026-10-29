---
paths:
  - "backend/app/modules/employee/**"
  - "backend/app/seed*.py"
  - "frontend-v2/src/modules/hr/**"
  - "frontend-v2/src/shared/utils/name-initials.ts"
  - "test/backend/*ho_so*"
  - "test/backend/*nhan_su*"
  - "test/backend/*qua_trinh*"
  - "doc/erp/hrm/**"
  - "backend/app/modules/import_tool/employee_import*.py"
  - "test/backend/*cr628*"
  - "test/backend/*cr693*"
  - "backend/app/modules/labor_contract/payroll_report*"
  - "backend/app/modules/labor_contract/salary_sync.py"
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
- ⚠️ **Ở đường CẬP NHẬT, «bỏ chọn» là id thật → 0, KHÔNG phải 0 → 0** (duoc-CR-627).
  Màn hồ sơ gửi lại `position_id = 0` ở MỌI lần lưu; coi 0 → 0 là bỏ chọn thì hồ sơ
  cũ còn chức danh dạng chữ (CSV chưa map) mất chức danh mỗi khi ai lưu một ô bất kỳ.
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

### QUÁ TRÌNH CÔNG TÁC (duoc-CR-585, 03/10/2026)

Bảng `tab_employee_work_history` lưu lịch sử công tác ghi tay theo người (bổ nhiệm, điều chuyển, kiêm nhiệm, thôi việc).
Chi tiết: `doc/erp/hrm/01-ho-so-nhan-su.md` §7.11. Bốn bẫy, một quyết định, một lưu ý giờ VN:

1. **Áp hồ sơ chỉ đi qua `update_employee` / `set_extra_departments` — cấm ghi thẳng cột.**
   Thứ tự THẬT trong `update_employee`: gán ô (`status`/`resign_date`…) → `has_left_company`
   phát hiện lần lưu này vừa chuyển sang nghỉ việc → `lock_linked_users` khóa tài khoản + đá
   phiên — cả ba trong CÙNG một giao dịch với dòng lịch sử. Không gọi `lock_linked_users` tách
   riêng ở tab Tài khoản là lệch đường, vì không có audit trail nào khoá TK mà không có dòng lịch
   sử. Test chốt ghi dòng và khóa TK không bị lộn xộn.

2. **`position_label` là nhãn CHỤP, không `propagate_rename`.**
   Khi đổi tên chức vụ trong danh mục, lịch sử vẫn giữ tên đó để bản in lịch sử không đổi.
   Giữ nguyên như ô `employee.position` — hai đường ghi duy nhất ở service.

3. **Tệp QĐ người khác gác bằng `employee_sensitive.read`** ở `work_history_access.check_file`,
   cộng với quyền `employee.read` + phạm vi thường. Chính chủ (`employee_id = id đăng nhập`)
   luôn xem được. Gác **trước khi trả thân API** (không phải gác ở tầng giao diện). `file_count`
   vẫn lộ ra (số đếm, không nội dung) — cố ý để người đó biết là có tệp nhưng không được xem.

4. **Hộp thoại có `<form>` bên trong trang hồ sơ phải gọi `e.stopPropagation()`**
   ở `onSubmit`, trước `form.handleSubmit(onSubmit)(event)`. Không thì bấm Lưu dòng lịch sử
   sẽ submit cả form hồ sơ phía ngoài. Test xác nhận `onSubmit` của form cha KHÔNG bị gọi.

5. **API: SÁU loại sự kiện áp được.** NĂM loại nhóm chính — HIRE · TRANSFER · APPOINT · DISMISS ·
   RESIGN (mã 1/2/3/5/6) — đổi hồ sơ qua `update_employee` (RESIGN qua nhánh `has_left_company`,
   không đổi company/department/position). CỘNG loại CONCURRENT (mã 4, kiêm nhiệm) — áp qua
   `set_extra_departments` vào `tab_employee_department` trực tiếp, KHÔNG đổi chức vụ chính (khác
   hàm ghi, không phải "không áp"). Dòng tương lai (`from_date` > hôm nay) → nút Áp tắt. Chỉ loại
   OTHER/«Khác» (mã 9) là không áp được vào đâu — ghi chú thuần.

6. **"Hôm nay" dùng `app.core.vn_time.vn_today()`, KHÔNG `date.today()`.** Container chạy UTC;
   `date.today()` đọc ngày UTC, lệch với ngày Việt Nam từ 00:00-06:59 giờ VN (review backend
   03/10/2026, finding H2). Mọi chốt theo ngày của phân hệ này (`apply_gate`, `compute_can_apply`,
   gỡ kiêm nhiệm hết hạn) phải qua `vn_today()` — thêm chốt ngày mới thì nhớ đi qua đây, đừng chép
   tay `datetime.utcnow() + timedelta(hours=7)` lần nữa.

Test: `test/backend/*qua_trinh*` (7 tệp) + `test/backend/*ho_so_nhan_su_dot1.py`; `vitest` trên
`modules/hr/components/employee-tab-work-history*.tsx` + `use-employee-work-history*.ts`.
Paths cập nhật: thêm `test/backend/*qua_trinh*`.

### NHẬP EXCEL NHÂN SỰ (duoc-CR-628, 19/10/2026)

Nút «Nhập Excel» ở `/hr/employees` → `import_tool` (adapter `EMPLOYEE`, hook ở `import_tool/employee_import*.py`).
Thiết kế: `plans/261019-0935-nhap-excel-nhan-su-cr628/`; khung hook: `doc/erp/nen-tang/16-quan-ly-import-export-v2.md` §9.3.

1. **Mọi đường ghi hàng loạt hồ sơ phải qua `*_core` của `employee/service.py`** (`create_employee_core`,
   `update_employee_core`, `delete_employee_core`) — cấm `setattr` trần như Import CSV cũ (đã 410). Lõi flush,
   KHÔNG commit/`record()` (record luôn commit, BM-013); bên gọi tự bọc savepoint, commit, audit, xóa cache quyền.
2. **Ô trống = giữ nguyên; chỉ `__/empty_value/__` mới xóa** (không xóa được Họ tên · Trạng thái · Đang dùng).
   Giá trị lạ ở ô mã số/trạng thái/ngày là LỖI DÒNG, không đoán bừa.
3. **Cột nhạy cảm cần `employee_sensitive.write`** — lấy từ `sensitive.SENSITIVE_FIELDS`, không gõ danh sách thứ
   hai. Thiếu quyền → bỏ cột + 1 cảnh báo `sensitive_ignored`. Log KHÔNG được chứa giá trị cột nhạy cảm.
4. **Tệp lô Nhân sự và `tab_import_change.snapshot` chứa CCCD/STK bản rõ** — tải tệp gác `employee_sensitive.read`.
   ⚠️ **Rủi ro treo:** snapshot hoàn tác giữ vĩnh viễn, CHƯA có việc dọn sau N ngày (chủ dự án chốt hoãn).
5. **Vai trò cũ cần tick tay** `import.read/create` + `employee.create/write` + `employee_sensitive.write` (D-018;
   seed KHÔNG đổi theo CR này). `import.read` là toàn cục: người có nó thấy cả danh sách/log lô Thu mua, Kho.
6. Không xóa nhân sự qua tệp (`allow_delete=False`); hoàn tác KHÔNG mở lại tài khoản đã khóa vì nghỉ việc.
7. Test: pysqlite không phát `BEGIN` trước `SAVEPOINT` nên dry-run "commit nhầm" — test dùng `savepoint_that(db)`
   (`test_nhap_excel_nhan_su_cr628.py`) để ép `BEGIN` như MySQL.
8. **Hoàn tác (lượt review):** bản chụp là `{cột: [cũ, mới]}` CHỈ cột đã đổi; khôi phục khi giá trị hiện tại còn là
   «mới», cột nào đã bị sửa về sau thì TỪ CHỐI CẢ LƯỢT (nêu mã + tên cột, không nêu giá trị). Mỗi dòng cần
   `employee.write` + phạm vi (lô tạo thêm `employee.delete`), cột nhạy cảm cần đọc+ghi nhạy cảm; ai đủ quyền
   trong phạm vi cũng hoàn tác được, không riêng người tạo. Xóa NV mới bị chặn nếu đã có liên hệ/người thân/quá trình
   công tác/HĐLĐ/kiêm nhiệm hoặc hồ sơ sửa sau lô (so `updated_at` với `created_at` + 60 giây, cùng đồng hồ DB).
9. **Một mã NV chỉ một lần trong tệp** (dòng sau = lỗi, kể cả mã vừa tự sinh). Lỗi DB không bao giờ đi vào log/
   `error_summary` (SQLAlchemy kèm THAM SỐ = CCCD/STK): chỉ tên lớp lỗi, chi tiết ở log máy chủ.
10. **Đánh đổi giao dịch dài (M2):** ghi thật sinh mã NSU bằng `generate_code` (FOR UPDATE hàng nhỏ nhất của tiền
    tố) và GIỮ khóa tới commit cuối lô (≤ 2000 dòng) → người khác tạo nhân sự bằng tay bị chờ trong lúc lô chạy.
    Chạy thử KHÔNG khóa (mã xem trước chỉ để tham khảo, có thể khác mã thật). Muốn nhẹ hơn: điền sẵn Mã NV trong tệp.
11. Ghi thật từ bản chạy thử chỉ MỘT lần (409 nếu đã có lô APPLY cùng tệp còn sống).
12. **Lượt 3:** bản chụp của hồ sơ SỬA có thêm `_depts` = `[tập phòng ban trước, sau]` (`[[id, is_primary], …]`); hoàn tác
    từ chối nếu tập hiện tại ≠ «sau» và khôi phục ĐÚNG tập cũ bằng `set_departments` (phòng bị hạ xuống kiêm nhiệm khi
    đổi phòng chính / bị gỡ khi đổi pháp nhân sẽ không còn sót → không mở rộng phạm vi dữ liệu). Hồ sơ MỚI có `_stamp` =
    `updated_at` lúc nhập; sau đó mà `updated_at` khác dấu này (không có độ trễ) thì không xóa. Hoàn tác đổi phòng/pháp
    nhân phải qua cùng chốt L1 (không tự đổi phòng mình) và L2 (phòng cũ phải trong tầm người hoàn tác). Hoàn tác khóa lại
    tài khoản nếu khôi phục về «nghỉ việc» (`lock_users=True`) và ghi nhật ký từng tài khoản.
13. **Giới hạn bộ nhớ đệm quyền:** `perm_cache_clear` chỉ xóa cache của TIẾN TRÌNH đang chạy (API hoặc worker). Các
    tiến trình khác tự hết hạn sau ≤ 60 giây — người bị đổi phạm vi bởi lô nhập/hoàn tác có thể còn thấy phạm vi cũ tối
    đa một phút. Cùng giới hạn với mọi đường sửa phạm vi khác; không thêm cơ chế phát tán cache ở CR này.
14. **Ghi thật một lần (MySQL):** câu dò lô APPLY cùng tệp phải là đọc-có-khóa (`live_apply_query`, FOR SHARE) vì
    REPEATABLE READ khiến SELECT thường thấy ảnh chụp cũ; SQLite không tái hiện được nên test chỉ kiểm câu biên dịch
    sang MySQL. Deadlock 1213 / hết chờ khóa 1205 / `PendingRollbackError` làm hỏng CẢ LÔ (không nuốt thành lỗi dòng).


### QUYỀN MẶC ĐỊNH THEO CHỨC VỤ (duoc-CR-653, 20/10/2026)

Mỗi chức vụ khai một **gói vai trò** (`tab_job_position_role`); tài khoản của nhân sự giữ chức vụ đó được hệ
thống tự cấp gói. Mã: `employee/position_role_service.py` (+ `position_role_controller.py`, màn tab «Quyền mặc
định» ở `/hr/job-positions/:id`). Script đề xuất gói từ dữ liệu hiện có: `backend/scripts/de_xuat_quyen_theo_chuc_vu.py`.

- ⚠️ **Gói chỉ là DANH SÁCH VAI TRÒ, không có bậc phạm vi.** Bậc own/dept/company/all nằm ở
  `tab_permission.scope` (vai trò × đối tượng), KHÔNG ở `tab_user_role`. Muốn «Trưởng phòng bậc phòng ban» thì chọn
  vai trò đã cấu hình bậc đó.
- ⚠️ **Dấu `tab_user_role.granted_by_position_id`**: `0` = quản trị gán tay, `>0` = hệ thống tự cấp theo chức vụ đó.
  Chỉ dòng `>0` bị gỡ khi đổi/bỏ chức vụ; dòng tay không bao giờ bị đụng. Vai trò vừa gán tay vừa có trong gói →
  không thêm dòng, giữ dòng tay. `UNIQUE(user_id, role_id)`; đụng trùng khi ghi đồng thời = coi như đã có.
- **Một hàm lõi duy nhất** `sync_employee_roles` («đối chiếu», chạy lại bao nhiêu lần cũng cùng kết quả), gọi SAU khi đổi
  chức vụ ở: `update_employee_core` (lưu hồ sơ · nhập Excel nhánh danh mục · áp quá trình công tác), nhánh chữ tự do của
  nhập Excel, hoàn tác lô nhập, mở khóa tài khoản; `grant_on_account_creation` khi cấp tài khoản. Chỉ `flush`, nhật ký
  `record(..., commit=False)`, xóa cache quyền ngay + sau commit. Tài khoản khóa / hồ sơ nghỉ việc: bỏ qua.
- ⚠️ **CẤM TỰ CẤP CHO CHÍNH MÌNH (C1).** Người thao tác không phải quản trị thì KHÔNG BAO GIỜ được tự cấp gói cho tài
  khoản của chính họ (HR đổi chức vụ của mình = lấy gói). Thu hồi vẫn được. Chốt đặt ở `_sync_user`, phủ mọi đường.
  Thêm đường đổi chức vụ mới = gọi `sync_employee_roles`, đừng tự viết lại.
- ⚠️ **Lọc leo thang (H1).** Người thao tác không phải quản trị chỉ cấp được vai trò mà quyền ⊆ quyền của họ (cùng L2 của
  gán vai trò tay). Phần còn lại BỊ BỎ QUA + nhật ký `auto_grant_skipped_position`; «Áp lại» trả `skipped_no_permission`.
- ⚠️ **Vai trò cấm vào gói (M5)**: `admin` / `ADMINISTRATOR` và vai trò có ghi/tạo/xóa trên `role` hoặc `user`. Chặn ở PUT
  (400) VÀ ở lúc cấp (`forbidden_role_ids`), vì dữ liệu cũ/script có thể đưa lọt.
- Sửa gói cần `role.write` (không phải `job_position.write`) + chốt L2 cho vai trò MỚI THÊM; ai đang giữ chức vụ đó (không
  phải quản trị) thì 403 khi thêm vào gói của chính chức vụ mình (H2). Sửa gói KHÔNG đổi quyền ai — chỉ nút «Áp lại»
  (có xác nhận + số người; bỏ qua tài khoản của chính người bấm và không tính vào «holders»).
- Xóa vai trò đang trong gói: bị chặn (`role/references.py`). Xóa chức vụ: dọn gói. Xóa cứng hồ sơ nhân sự: gỡ dòng hệ
  thống cấp của tài khoản (`detach_users`).
- ⚠️ **Hạn chế đã biết — gỡ riêng một người**: admin lưu lại danh sách vai trò có chứa vai trò hệ thống tự cấp thì nó VẪN
  là «tự cấp». Muốn bỏ một vai trò của gói cho riêng một người: sửa gói hoặc đổi chức vụ của họ (bỏ tick ở Phân quyền tài
  khoản sẽ bị «Áp lại»/đổi chức vụ cấp lại).
- ⚠️ **Hạn chế đã biết — cache quyền 60 giây theo TIẾN TRÌNH (M3)**: `perm_cache_clear` chỉ xóa trong tiến trình gọi. Prod
  chạy nhiều worker uvicorn + nhập Excel chạy trong Celery nên một vai trò vừa thu hồi có thể còn tác dụng tới 60 giây ở
  worker khác. Có sẵn cho mọi thao tác phân quyền, CR-653 chỉ thêm thu hồi hàng loạt; chưa chuyển cache sang Redis.
- Script đề xuất: mặc định dry-run, `--min-holders 3`, loại vai trò cấm, `--apply --yes` chỉ THÊM gói + ghi nhật ký, không
  cấp cho ai (dùng «Áp lại» sau).


### Ô LƯƠNG TRÊN HỒ SƠ (duoc-CR-693, 29/10/2026)

`tab_employee` có `salary_monthly` + `allowance_monthly` (BIGINT đồng, 0 = chưa nhập) + `salary_updated_at`. Migration `emp_salary01`.
Đại ca chốt: **CHỈ chính nhân sự đó đọc được SỐ**. Người khác — kể cả người nhập, admin, người có `employee_sensitive` /
`labor_contract` — chỉ thấy cờ `salary_set` (đã nhập chưa).

- ⚠️ **Một chốt che duy nhất: `sensitive.mask` / `mask_many` (`SALARY_FIELDS`).** Khác nhóm nhạy cảm: KHÔNG mở bằng khóa quyền, chỉ
  nhánh `self` (`is_self`, chặn `employee_id = 0`). `mask(data, allowed, profile)` **mặc định CHE** nếu không truyền `profile` —
  đường mới quên truyền thì lương về 0 chứ không lộ. Mọi cửa trả hồ sơ (`/`, `/me`, `/{id}`, PATCH, CSV/XLSX qua `export_mask`)
  đi qua đây; trợ lý AI dùng danh sách trắng nên không có lương; nhật ký (`change_tracker` denylist + `logging_policy` theo đường
  dẫn) không giữ số; audit chỉ ghi «Cập nhật lương».
- ⚠️ **Che bằng 0 nên màn sửa hồ sơ PHẢI không gửi hai ô này khi người xem không phải chính chủ** (cùng bẫy `pickWritableProfile`):
  gửi 0 đè lương thật. Backend không phân biệt «bị che» với «muốn xóa». Gửi `null`/vắng = giữ nguyên; xóa = gửi 0.
- Ghi: `employee.write` trong phạm vi; **không ai tự đổi lương của mình** (403 khi giá trị đổi thật — gửi lại nguyên giá trị cũ thì
  qua, vì chính chủ đọc được số). Đường ghi duy nhất: `employee.service.set_salary` (PATCH và ký HĐLĐ dùng chung).
- Không sắp xếp danh sách theo lương (400): thứ tự cũng là thông tin. Nhập Excel nhân sự KHÔNG có cột lương: tiêu đề «Lương/Phụ cấp»
  bị bỏ qua + cảnh báo (`ignored_headers` của adapter ở `catalog_import.py`).
- Ký HĐLĐ (DRAFT→SIGNED) tự chép `base_salary`/`allowance` sang hồ sơ nếu HĐ đó là **hiệu lực mới nhất** (`labor_contract/salary_sync.py`:
  đã bắt đầu, chưa hết hạn, không HĐ Đã ký nào khác bắt đầu muộn hơn). Chỉ Nháp sửa được lương HĐ nên không có đường «sửa HĐ đã ký».
- Báo cáo Quỹ lương (khóa 21) đọc ô này, không đọc HĐ: ảnh chụp hiện tại, không kỳ so sánh/xu hướng, chỉ TỔNG, nhóm/Tổng dưới 3 người bị
  che, `/rows` không có cột tiền, gác `employee.read|export` + `require_report(21)`. Test: `test_o_luong_ho_so_cr693.py`, `test_bao_cao_quy_luong_cr688.py`.
