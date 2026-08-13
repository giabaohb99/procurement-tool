# Hệ thống & Báo cáo

Tài liệu này mô tả sáu chức năng thuộc nhóm quản trị hệ thống và báo cáo: Nhân sự, Người dùng, Vai trò & Phân quyền, Cấu hình hệ thống, Báo cáo mua hàng, Báo cáo khảo sát.

---

## Nhân sự

### Mục đích

Quản lý danh sách nhân viên thuộc các công ty/phòng ban. Hồ sơ nhân sự là nền tảng để gắn kết tài khoản đăng nhập, xác định phạm vi dữ liệu, phân bổ công việc mua hàng và khảo sát.

Đường dẫn: `/employees` (danh sách + chi tiết qua sidebar). Hỗ trợ nhập/xuất CSV (nút Import/Export trên danh sách).

### Danh sách trường

### 1. Mã nhân viên (`code`)

- Kiểu nhập: Nhập tay (chuỗi, tối đa 25 ký tự)
- Mặc định: trống
- Bắt buộc: Có (unique)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `employee:write`
- Logic đặc biệt: Không được sửa sau khi tạo (`readonlyOnEdit: true`); dùng làm khóa tra cứu trong phân bổ (`PurchaseRequestItem.assignee`, `SurveyRequestLine.assignee`)

### 2. Họ tên (`full_name`)

- Kiểu nhập: Nhập tay (chuỗi, tối đa 255 ký tự)
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `employee:write`

### 3. Email (`email`)

- Kiểu nhập: Nhập tay
- Mặc định: rỗng (`""`)
- Bắt buộc: Không (nhưng cần để gửi thông báo)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `employee:write`

### 4. Số điện thoại (`phone`)

- Kiểu nhập: Nhập tay (tối đa 25 ký tự)
- Mặc định: rỗng
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `employee:write`

### 5. Phòng ban (`department_id`)

- Kiểu nhập: Chọn (ô tìm kiếm)
- Mặc định: 0 (chưa gán)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Bảng Phòng ban (`tab_department`); hiển thị `name`
- Người sửa: Người có quyền `employee:write`
- Logic đặc biệt: Phòng ban xác định `dept_name` và `dept_id` trong hồ sơ phân quyền; ảnh hưởng đến phạm vi `dept` của các vai trò gán cho tài khoản liên kết

### 6. Vị trí / Chức vụ (`position`)

- Kiểu nhập: Nhập tay (tối đa 100 ký tự)
- Mặc định: rỗng
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `employee:write`
- Logic đặc biệt: **Chỉ là chức danh hiển thị** (in lên YCBG/YCMH ở ô "Chức vụ"), KHÔNG phải phân quyền. Quyền thật của tài khoản chỉ gán ở màn **Phân quyền tài khoản** (xem CR-022 / D-019). Form có sẵn dòng chú thích nhắc điều này

### 7. ~~Vai trò nghiệp vụ (`role_name`)~~ — ĐÃ BỎ (CR-022)

- Ô "Vai trò" trên hồ sơ nhân sự đã bị gỡ khỏi form và danh sách; giá trị cũ được chép sang `position` bằng migration `c8d1f6b3a92e`
- Cột `role_name` vẫn còn trong DB để giữ dữ liệu lịch sử nhưng **không còn được đọc/ghi ở bất kỳ luồng nào**

### 8. Trạng thái (`status`)

- Kiểu nhập: Chọn (danh sách cố định)
- Mặc định: `Chính thức`
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: Chính thức / Cộng tác viên / Nghỉ thai sản / Nghỉ việc
- Người sửa: Người có quyền `employee:write`

### 9. Hoạt động (`is_active`)

- Kiểu nhập: Checkbox (Boolean)
- Mặc định: `true`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người có quyền `employee:write`
- Logic đặc biệt: Nhân sự không hoạt động không được chọn trong các trường liên kết (phân công, người đại diện pháp lý, NSTM...)

### 10. Ảnh đại diện (`avatar`) — chỉ đọc trên hồ sơ nhân sự

- Kiểu nhập: Tải ảnh lên (bấm vào ảnh tròn ở đầu trang chi tiết nhân sự)
- Mặc định: rỗng — hiện chữ cái đầu của họ tên trên nền màu
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: **`tab_user.avatar` của tài khoản gắn với nhân sự đó** — bảng `tab_employee` KHÔNG có cột ảnh
- Người sửa: `employee:write` (đổi hộ người khác) hoặc chính chủ tự đổi ở Trang cá nhân
- Logic đặc biệt: Ảnh chỉ có **một chỗ lưu duy nhất**. Người dùng tự đổi ảnh ở Trang cá nhân thì danh sách nhân sự đổi theo và ngược lại — cố ý làm vậy để không có hai nguồn lệch nhau. Hệ quả: **nhân sự chưa được cấp tài khoản thì chưa đặt được ảnh**, hệ thống báo *"hãy tạo tài khoản trước khi đặt ảnh đại diện"*
- Logic đặc biệt: API `POST /api/employees/{id}/avatar`; danh sách nhân sự nạp gộp ảnh qua `selectinload(user)` để không sinh mỗi dòng một câu truy vấn

### Xóa hồ sơ nhân sự (CR-023)

Xóa hồ sơ nhân sự là **xóa cứng** bản ghi trong `tab_employee`. Từ CR-023, thao tác này **kéo theo tài khoản đăng nhập**:

- Mọi `tab_user` đang gắn nhân sự đó bị **khóa** (`is_active = 0`) và **gỡ liên kết** (`employee_id = 0`).
- Tài khoản **không bị xóa** — giữ lại để còn truy vết ai đã tạo/duyệt chứng từ cũ.
- Thông báo trả về ghi rõ số tài khoản bị khóa; nhật ký thao tác ghi kèm dòng "Khoá N tài khoản đăng nhập kèm theo".
- Áp dụng cho cả nhánh "xóa" của **Nhập file CSV** (cột *Hành động* = `xóa`).

Trước CR-023 tài khoản vẫn sống sau khi hồ sơ nhân sự bị xóa ("tài khoản mồ côi"): đăng nhập được, hiển thị thông tin
lấy từ bản ghi tài khoản, và nếu trùng email với người thật thì còn làm người thật không đăng nhập được.
Muốn giữ tài khoản thì **đừng xóa hồ sơ nhân sự** — bỏ tick *Hoạt động* (`is_active`) là đủ.

---

## Nguoi dung (Tài khoản)

### Mục đích

Quản lý tài khoản đăng nhập và liên kết tài khoản với hồ sơ nhân sự. Mỗi tài khoản giữ danh sách vai trò được gán và cấu hình phạm vi dữ liệu riêng theo từng vai trò.

Đường dẫn: `/users/:id` (trang chi tiết quyền). Danh sách người dùng xem ở tab "Người dùng" trong màn Phân quyền (`/roles`).

### Danh sách trường

### 1. Email (`email`)

- Kiểu nhập: Nhập tay (hoặc từ đăng nhập Google)
- Mặc định: rỗng
- Bắt buộc: Có (dùng làm định danh đăng nhập)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`user:write`)
- Logic đặc biệt: Email dùng để xác thực bằng mật khẩu hoặc SSO Google (`google_sub`); hai cơ chế này cùng tồn tại
- Logic đặc biệt (CR-023): không tạo được tài khoản mới với email đã có ở một tài khoản **đang hoạt động**

### 2. Mật khẩu (`password_hash`)

- Kiểu nhập: Nhập tay (ô password; không hiển thị lại)
- Mặc định: —
- Bắt buộc: Không nếu dùng SSO Google
- Nguồn dữ liệu / liên kết: —
- Người sửa: Người dùng tự đổi qua luồng Quên mật khẩu; Admin đặt lại qua API
- Logic đặc biệt: Lưu dạng bcrypt hash; không bao giờ trả về plaintext

### 3. Nhân sự liên kết (`employee_id`)

- Kiểu nhập: Chọn (liên kết với bảng Nhân sự)
- Mặc định: 0 (chưa liên kết)
- Bắt buộc: Không bắt buộc về mặt kỹ thuật, nhưng cần để phân quyền phạm vi hoạt động đúng
- Nguồn dữ liệu / liên kết: Bảng Nhân sự (`tab_employee`)
- Người sửa: Admin (`user:write`)
- Logic đặc biệt: Qua `employee_id`, hệ thống lấy `emp_code`, `company_id`, `dept_name`, `dept_id` để nạp vào hồ sơ phân quyền (`get_perm_profile`); thiếu liên kết này thì phạm vi `own/dept/company` không hoạt động đúng

### 4. Avatar (`avatar`)

- Kiểu nhập: URL hình ảnh (tự động từ SSO Google hoặc nhập tay)
- Mặc định: rỗng
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Hệ thống (SSO) hoặc Admin

### 5. Hoạt động (`is_active`)

- Kiểu nhập: Checkbox
- Mặc định: `true`
- Bắt buộc: —
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`user:write`)
- Logic đặc biệt: Tài khoản bị tắt (`is_active = false`) không thể đăng nhập; token cũ vẫn còn hiệu lực cho đến khi hết hạn nếu không invalidate
- Logic đặc biệt (CR-023): tài khoản đã khóa **không giữ chỗ email** — người khác vẫn tạo được tài khoản với email đó.
  Đăng nhập (cả mật khẩu lẫn Google) luôn **ưu tiên tài khoản đang hoạt động**, nên một tài khoản đã khóa trùng email
  không thể che mất tài khoản thật. Đổi lại, **mở khóa** một tài khoản mà email của nó đang trùng với một tài khoản
  đang hoạt động sẽ bị từ chối — phải sửa email trước.

### 6. Vai trò được gán (`role_ids` — bảng `tab_user_role`)

- Kiểu nhập: Checkbox đa chọn (danh sách tất cả vai trò trong hệ thống)
- Mặc định: không gán
- Bắt buộc: Không (tài khoản không có vai trò nào = không thấy dữ liệu nào)
- Nguồn dữ liệu / liên kết: Bảng Vai trò (`tab_role`)
- Người sửa: Admin (`user:write`) tại trang `/users/:id`
- Logic đặc biệt: Mỗi lần thay đổi vai trò sẽ gọi `perm_cache_clear()` để xóa cache phân quyền (cache sống 60 giây)
- Logic đặc biệt (CR-037): tài khoản mới **không chọn vai trò** thì tự gán vai trò `employee` (**Nhân sự**) — áp cho cả 3 đường tạo: cấp tài khoản từ màn Nhân sự, gọi API tạo người dùng, và đăng nhập Google lần đầu. Vai trò cao hơn vẫn phải gán tay. Trước đó (CR-022) tài khoản mới không có quyền gì nên đăng nhập vào **thấy màn trắng**, không hiểu là lỗi hay chưa được cấp quyền

### 7. Phạm vi theo vai trò (`tab_user_scope`)

- Kiểu nhập: Popup "Phạm vi" mở sau khi đã lưu vai trò (nút riêng từng dòng vai trò)
- Mặc định: không giới hạn (tương đương phạm vi mặc định của vai trò)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Công ty (`tab_company`), Phòng ban (`tab_department`), Nhân sự (`tab_employee`)
- Người sửa: Admin (`user:write`)
- Logic đặc biệt: Xem chi tiết ở mục Vai trò & Phân quyền bên dưới

### Dọn tài khoản mồ côi (CR-037)

CR-023 khóa và gỡ liên kết tài khoản khi xóa hồ sơ nhân sự, nhưng **không xóa** tài khoản. Hệ quả là danh sách người dùng
dần tích lại những dòng đã khóa, không còn nhân sự, không ai dám đụng vì sợ mất dấu vết. CR-037 bổ sung công cụ để nhìn ra
và dọn đúng nhóm đó.

**Nhìn ra chúng — bộ lọc "Tình trạng"** (tab *Người dùng* của màn Phân quyền `/roles`), hai lựa chọn:

| Lựa chọn | Nghĩa là gì |
| --- | --- |
| Chưa gán vai trò | Tài khoản đăng nhập được nhưng chưa có vai trò nào — vào hệ thống là màn trắng |
| Mồ côi (không có hồ sơ nhân sự) | Tài khoản không còn gắn hồ sơ nhân sự nào (`employee_id = 0` hoặc trỏ vào nhân sự đã bị xóa) |

Ngoài bộ lọc, mỗi dòng trong bảng tự đeo nhãn **"Mồ côi"** (đỏ) / **"Đã khóa"** (xám) để nhận ra ngay mà không cần lọc.

**Xử lý chúng — hai nút biểu tượng ở cuối dòng:**

- **Ổ khóa** — khóa / mở khóa (`is_active`), không mất gì. Đây là lựa chọn mặc định, nên dùng trước.
- **Thùng rác** — xóa cứng bản ghi tài khoản. Nút này **chỉ hiện trên dòng có nhãn "Mồ côi"**.

**Bốn chốt chặn khi xóa** (kiểm ở backend, không phải chỉ ẩn nút):

1. Không xóa được **chính tài khoản đang đăng nhập**.
2. Không xóa được tài khoản **còn gắn hồ sơ nhân sự** — kể cả khi nó đang bị khóa. Muốn xóa thì xử lý hồ sơ nhân sự trước.
3. Không xóa được **tài khoản admin cuối cùng** — hệ thống phải luôn còn ít nhất một người mở được cửa.
4. Không xóa được tài khoản **đã tạo chứng từ** — bất kỳ bảng nghiệp vụ nào còn `created_by` trỏ vào nó.

Chốt 4 là lý do đa số tài khoản cũ **sẽ không xóa được**, và như vậy là đúng: xóa xong thì không còn trả lời được câu
"phiếu này ai tạo". Chỉ những tài khoản chưa từng làm gì mới thực sự biến mất.

**Xóa thì mất theo cái gì:** vai trò được gán, phạm vi dữ liệu, thông báo, và đăng ký nhận web-push của tài khoản đó.
**Nhật ký thao tác được giữ nguyên** — các dòng cũ hiển thị "User #id" thay cho tên.

**API liên quan:**

- `GET /api/users` — thêm tham số `no_role`, `orphan`; mỗi dòng trả về thêm trường `is_orphan`
- `PUT /api/users/{id}/active` — khóa / mở khóa (`user:write`)
- `DELETE /api/users/{id}` — xóa cứng, yêu cầu quyền `user:delete`

---

## Vai trò & Phan quyen

### Mục đích

Kiểm soát ai được làm gì với dữ liệu nào thông qua mô hình hai trục: **Trục 1 — Hành động** thuộc vai trò (entity x action), **Trục 2 — Phạm vi dữ liệu** thuộc người dùng (scope per grant + include/exclude). Cơ chế này được mô tả dưới đây; đây là tài liệu về cơ chế hơn là liệt kê trường nhập liệu đơn thuần.

Đường dẫn: `/roles` (tab "Vai trò & quyền" + tab "Người dùng").

### Mô hình hai trục

**Trục 1 — Hành động (gắn vào VAI TRO)**

Mỗi vai trò (`tab_role`) có một bản ghi quyền (`tab_permission`) cho từng entity. Mỗi bản ghi quyền là tổ hợp:
- **Entity**: đối tượng nghiệp vụ (ví dụ: `purchase_request`, `survey`, `employee`, `report`...). Danh sách đầy đủ trong `core/permissions.py`: `company`, `department`, `employee`, `user`, `role`, `warehouse`, `unit`, `item_group`, `brand`, `supplier`, `product`, `contract`, `purchase_request`, `survey`, `purchase_order`, `goods_receipt`, `inventory`, `payable`, `payment`, `payment_request`, `report`, `setting`, `category_assignee`, `survey_request`.
- **Actions** (8 hành động): `read` (Xem), `create` (Tạo), `write` (Sửa), `delete` (Xóa), `approve` (Duyệt), `cancel` (Hủy), `print` (In), `export` (Xuất). Mỗi hành động là một cờ boolean độc lập.
- **Scope mặc định của vai trò**: phạm vi dữ liệu áp dụng cho MỌI tài khoản mang vai trò đó, trừ khi bị override ở cấp người dùng. Các giá trị: `own` (Của mình), `assigned` (Được giao), `proc` (Thu mua: được giao + đã duyệt), `dept` (Phòng ban), `company` (Công ty), `all` (Tất cả).

Trong code: endpoint được bảo vệ bằng `require(entity, action)` — dependency này kiểm tra xem người dùng có bất kỳ grant nào cho `(entity, action)` không.

**Trục 2 — Phạm vi dữ liệu (gắn vào NGUOI DUNG, theo từng vai trò)**

Sau khi gán vai trò, mỗi cặp `(user, role)` có thể đặt thêm phạm vi cụ thể qua popup "Phạm vi". Các chiều tùy chỉnh:

- **Công ty được xem** (include company): thu hẹp về các công ty được chọn. Để trống = không giới hạn.
- **Phòng ban được xem** (include department): cộng thêm phạm vi — user thấy TẤT CA dữ liệu của các phòng ban này bên cạnh phạm vi cấp bậc vai trò. Cơ chế: OR với phạm vi vai trò, không thu hẹp.
- **Chỉ xem chứng từ do nhân sự tạo** (include employee): thu hẹp về chứng từ do nhân sự được chọn tạo. Để trống = không giới hạn theo chiều nhân sự.
- **Loại trừ phòng ban** (exclude department): ẩn dữ liệu của phòng ban bị loại trừ, áp sau include.
- **Loại trừ nhân sự** (exclude employee): ẩn dữ liệu do nhân sự bị loại trừ tạo, áp sau include.

**Cách kết hợp (hàm `apply_scope` trong `core/scoping.py`)**

Hệ thống tính HOP (OR) trên MỌI grant mà user có quyền `action` trên `entity`. Mỗi grant tạo một điều kiện:
1. Điều kiện cấp bậc vai trò (own / dept / company / all) theo `SCOPE_FIELDS` của entity.
2. Cộng thêm điều kiện "phòng ban được xem" (OR với điều kiện trên).
3. AND với điều kiện thu hẹp: include công ty + mọi loại trừ (company, department, employee).

Nếu không có grant nào → không thấy dữ liệu. Nếu ít nhất một grant là `all` và không có thu hẹp → thấy toàn bộ.

Các entity có định nghĩa `SCOPE_FIELDS` (nghĩa là có lọc phạm vi): `purchase_request`, `survey_request`, `purchase_order`, `payable`, `payment_request`, `inventory`, `survey`, `employee`. Entity không có trong `SCOPE_FIELDS` mặc định thấy tất cả khi đủ quyền.

**Hồ sơ phân quyền và cache**

Hàm `get_perm_profile(db, user)` xây dựng hồ sơ gồm toàn bộ grants (kèm scope) và thông tin nhân sự (`company_id`, `dept_name`, `emp_code`...). Hồ sơ được cache in-process 60 giây. Sau khi thay đổi vai trò hoặc quyền, hệ thống gọi `perm_cache_clear()` để vô hiệu hóa cache.

### Danh sách trường — Vai trò

### 1. Mã vai trò (`code`)

- Kiểu nhập: Nhập tay (chuỗi, tối đa 50 ký tự; vd: `pur_staff`, `manager`)
- Mặc định: trống (FE gợi ý `role_` + chuỗi ngẫu nhiên nếu bỏ trống)
- Bắt buộc: Có (unique)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`role:write`) khi tạo; không sửa sau khi tạo (`readonlyOnEdit`)
- Logic đặc biệt: Vai trò có code `ADMIN` / `ADMINISTRATOR` không được xóa

### 2. Tên vai trò (`name`)

- Kiểu nhập: Nhập tay (chuỗi, tối đa 100 ký tự)
- Mặc định: trống
- Bắt buộc: Có
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`role:write`)

### 3. Mô tả (`description`)

- Kiểu nhập: Nhập nhiều dòng (textarea)
- Mặc định: rỗng
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`role:write`)

### Danh sách trường — Ma trận quyền (tab "Vai trò & quyền")

Sau khi chọn một vai trò, màn hiển thị bảng ma trận entity x action. Mỗi dòng là một entity, mỗi cột là một action, thêm cột Phạm vi ở cuối.

### 4. Hành động (checkbox per entity x action)

- Kiểu nhập: Checkbox (8 ô per entity: Xem, Tạo, Sửa, Xóa, Duyệt, Hủy, In, Xuất)
- Mặc định: tất cả false
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: Danh sách cố định từ `ENTITIES` x `ACTIONS` trong `core/permissions.py`
- Người sửa: Admin (`role:write`)
- Logic đặc biệt: Nút "tất cả" (per dòng) bật/tắt đồng thời 8 hành động. Lưu = gửi PUT `/api/roles/{rid}/permissions`; bên BE xóa toàn bộ quyền cũ rồi ghi lại (chỉ lưu entity có ít nhất 1 action được bật)

### 5. Phạm vi mặc định của vai trò (`scope` per entity)

- Kiểu nhập: Chọn (dropdown)
- Mặc định: `own`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: own / assigned / proc / dept / company / all
- Người sửa: Admin (`role:write`)
- Logic đặc biệt: Đây là phạm vi mặc định áp cho mọi tài khoản mang vai trò này; có thể override bằng cấu hình phạm vi riêng ở trang chi tiết Người dùng

---

## Cau hinh he thong

### Mục đích

Lưu các thông số vận hành của hệ thống dưới dạng key-value trong cơ sở dữ liệu. Khóa bí mật (mật khẩu SMTP, khóa R2) được mã hóa bằng Fernet trước khi lưu và không hiển thị lại sau khi đặt. Cấu hình có hiệu lực ngay, không cần sửa `.env` hay build lại Docker; `.env` là giá trị dự phòng khi DB chưa đặt.

Đường dẫn: `/settings`. Quyền truy cập: `setting:read` (xem), `setting:write` (sửa).

Bảng `tab_setting`: hai cột `skey` (VARCHAR 64, unique) và `svalue` (Text). Secret được lưu cùng bảng với `svalue` đã mã hóa.

### Danh sách trường — Nhóm Email (SMTP)

### 1. Bật gửi email (`email_enabled`)

- Kiểu nhập: Checkbox (Boolean)
- Mặc định: `false`
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)
- Logic đặc biệt: Khi tắt, hệ thống không gửi bất kỳ email thông báo nào (workflow bell-only)

### 2. SMTP Host (`smtp_host`)

- Kiểu nhập: Nhập tay
- Mặc định: trống (dự phòng từ `.env`)
- Bắt buộc: Cần để gửi email
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)

### 3. SMTP Port (`smtp_port`)

- Kiểu nhập: Nhập số
- Mặc định: 587
- Bắt buộc: Cần để gửi email
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)

### 4. SMTP User (`smtp_user`)

- Kiểu nhập: Nhập tay (địa chỉ email gửi đi)
- Mặc định: trống
- Bắt buộc: Cần để gửi email
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)

### 5. Tên người gửi (`smtp_from`)

- Kiểu nhập: Nhập tay (hiển thị trong trường From của email)
- Mặc định: trống (dùng `smtp_user` nếu trống)
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)

### 6. Email test (`email_test_override`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Không
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)
- Logic đặc biệt: Khi đặt giá trị, MỌI email hệ thống (kể cả email thật) đều chuyển hướng về địa chỉ này — dùng để kiểm thử mà không gửi email thật tới người dùng

### 7. SMTP App Password (`smtp_password`) — BÍ MẬT

- Kiểu nhập: Nhập tay (ô password; mã hóa Fernet khi lưu; không hiển thị lại)
- Mặc định: —
- Bắt buộc: Cần để gửi email
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)
- Logic đặc biệt: Để trống = giữ nguyên giá trị cũ. Trạng thái "Đã cấu hình" / "Chưa" hiển thị bên cạnh nhãn

### Danh sách trường — Nhóm Lưu trữ (R2 / S3)

### 8. Endpoint (`r2_endpoint`)

- Kiểu nhập: Nhập tay (URL endpoint Cloudflare R2 hoặc S3-compatible)
- Mặc định: trống
- Bắt buộc: Cần để lưu file đính kèm
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)

### 9. Bucket (`r2_bucket`)

- Kiểu nhập: Nhập tay
- Mặc định: trống
- Bắt buộc: Cần để lưu file
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)

### 10. Public URL (`r2_public_url`)

- Kiểu nhập: Nhập tay (URL gốc để tạo link tải file công khai)
- Mặc định: trống
- Bắt buộc: Không (nhưng cần để hiển thị link file đính kèm)
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)

### 11. R2 Access Key ID (`r2_access_key_id`) — BÍ MẬT

- Kiểu nhập: Nhập tay (mã hóa Fernet khi lưu)
- Mặc định: —
- Bắt buộc: Cần để kết nối lưu trữ
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)

### 12. R2 Secret Key (`r2_secret_access_key`) — BÍ MẬT

- Kiểu nhập: Nhập tay (mã hóa Fernet khi lưu)
- Mặc định: —
- Bắt buộc: Cần để kết nối lưu trữ
- Nguồn dữ liệu / liên kết: —
- Người sửa: Admin (`setting:write`)

### Thao tác kiểm tra

- **Gửi email thử**: nhập email nhận thử, bấm "Gửi email thử" → hệ thống gửi một email kiểm tra qua cấu hình SMTP hiện tại (nếu đặt `email_test_override` thì gửi về đó)
- **Kiểm tra kết nối R2**: hệ thống thực hiện put + delete một file nhỏ (`healthcheck/ping.txt`) để xác nhận kết nối thành công

---

## Bao cao mua hang

### Mục đích

Cung cấp cái nhìn tổng thể và phân tích đa chiều về hoạt động mua hàng: giá trị đặt hàng, công nợ, tiến độ giao hàng, tần suất và chi phí theo nhiều chiều phân tích (NCC, nhân sự, phòng ban, phân loại vật tư, vận chuyển, tồn kho). Số liệu tải từ hai nguồn: `/api/reports/procurement` (tổng quan — tính realtime) và `/api/reports/matrix` (ma trận phân tích — đọc từ snapshot precompute, cập nhật theo yêu cầu).

Đường dẫn: `/reports`. Quyền: `report:read`.

### Bộ lọc chung

| Bộ lọc | Kiểu | Ghi chú |
|--------|------|---------|
| Công ty | Chọn (SearchSelect) | Lọc tất cả số liệu theo `company_id`; để trống = tất cả công ty |
| Năm | Chọn (SearchSelect) | Năm hiện tại mặc định; có thể chọn `all` (tất cả năm) |
| Nút Lọc | Bấm để tải lại | Tải lại cả hai endpoint |
| Nút Cập nhật | Bấm để tính lại | Gọi lại `matrix?refresh=1`; tính lại snapshot và lưu |

### Tab Tổng quan

**Thẻ số liệu:**

| Chỉ tiêu | Nguồn |
|----------|-------|
| Số đơn mua hàng (`po_count`) | Đếm PO "đơn thật" trong kỳ (theo `order_date`) |
| Giá trị đặt hàng | Tổng `qty_order * price * (1 + vat/100)` trên toàn bộ dòng PO đơn thật |
| Công nợ còn phải trả | Tổng `remaining` từ bảng Công nợ (tách riêng hàng hóa / vận chuyển) |
| Công nợ quá hạn | Công nợ chưa TT có `due_date` < ngày hôm nay |
| Giá trị tồn kho | Tổng `value` từ bảng Tồn kho (`tab_inventory`) |

"Đơn thật" = PO có trạng thái `approved`, `partial`, `received` hoặc `completed` (loại bỏ nháp, chờ duyệt, hủy, từ chối và bản ghi đã xóa mềm).

**Đơn theo trạng thái**: đếm PO đơn thật theo từng trạng thái (approved / partial / received / completed và các trạng thái khác có dữ liệu > 0).

**Tiến độ giao hàng**: số lần giao đúng hạn vs. trễ (theo `diff_regulated < 0`). Hiển thị thanh tiến độ và tỷ lệ phần trăm đúng hạn.

**Chi phí mua theo tháng**: biểu đồ cột 12 tháng. Bấm vào cột tháng mở popup "Chi phí theo ngày" với biểu đồ đường và bảng chi tiết (hàng hóa / vận chuyển / tổng).

### Tab NCC (trễ giao)

Dữ liệu từ snapshot `matrix.supplier`. Ma trận: NCC x tháng. Loại bỏ các dòng không có tên NCC (rỗng hoặc "(Không rõ)").

| Cột | Nội dung |
|-----|---------|
| Nhà cung cấp | Tên NCC (ưu tiên `supplier_name`, dự phòng `supplier_code`) |
| Số lần giao dịch (`trans`) | Số lần giao hàng (`PODelivery`) có `received_qty > 0` |
| Số lần trễ (`late`) | Số lần `diff_regulated < 0` |
| Tỷ lệ trễ (`rate`) | `late / trans * 100` (%) |

Dòng tô đỏ nhẹ khi `rate > 30%`. Chọn kỳ "Xem theo": cả năm hoặc theo tháng cụ thể.

### Tab Phân loại vật tư bao bì / nguyên liệu

Dữ liệu từ snapshot `matrix.item_group`. Ma trận: phân loại x tháng. Loại bỏ các dòng không có phân loại (rỗng hoặc "(Không rõ)").

| Cột | Nội dung |
|-----|---------|
| Loại vật tư bao bì / nguyên liệu | `item_group` của dòng PO |
| Số lần mua (`trans`) | Số lần giao hàng |
| Tổng chi phí mua (`cost`) | Tổng `qty_received * price * (1 + vat/100)` |

### Tab Nhân sự phụ trách

Dữ liệu từ snapshot `matrix.nspt`. Ma trận: nhân sự phụ trách x tháng. Loại bỏ các dòng không có NSPT (rỗng hoặc "(Không rõ)").

| Cột | Nội dung |
|-----|---------|
| Nhân sự phụ trách | Tên nhân sự phụ trách (`po.nspt`) |
| Số đơn (`orders`) | Số lần giao hàng phụ trách |
| Trễ quy định (`late`) | `diff_regulated < 0` |
| Đúng hạn (`ontime`) | `diff_regulated == 0` |
| Giao sớm (`early`) | `diff_regulated > 0` |
| Tỷ lệ trễ (`rate`) | `late / orders * 100` (%) |

### Tab Bộ phận (đơn gấp)

Dữ liệu từ snapshot `matrix.department`. Ma trận: phòng ban x tháng. Loại bỏ các dòng không có phòng ban (trường `department` trống).

| Cột | Nội dung |
|-----|---------|
| Bộ phận | `po.department` |
| Số lần đặt (`orders`) | Số PO |
| Số lần gấp (`urgent`) | PO có `is_urgent = true` |
| Tỷ lệ gấp (`rate`) | `urgent / orders * 100` (%) |

Dòng tô đỏ nhẹ khi `rate > 30%`.

### Tab Chi phí vận chuyển

**Bảng tóm tắt** (từ snapshot `matrix.shipping`): đơn vị vận chuyển x tháng.

| Cột | Nội dung |
|-----|---------|
| Đơn vị vận chuyển | `carrier_name` hoặc `carrier_code` |
| Tần suất (`freq`) | Số lần giao hàng dùng đơn vị này |
| Giá trị đơn hàng (`order_value`) | Tổng thành tiền theo lô nhận |
| Chi phí vận chuyển (`ship_cost`) | Tổng `shipping_amount` |
| Tỷ lệ (`rate`) | `ship_cost / order_value * 100` (%) |

**Bảng chi tiết**: mỗi dòng = một lần giao hàng có phí vận chuyển. Phân trang phía server, 50 dòng/trang. Có bộ lọc theo đơn vị vận chuyển và tháng. Các cột: Đơn vị vận chuyển, Tháng, Mã vật tư bao bì / nguyên liệu, Mã MISA, Số hóa đơn, Ngày nhận, Số lượng đặt, Số lượng nhận, Thành tiền đơn hàng, Thành tiền vận chuyển, Tỷ lệ.

### Tab Yêu cầu mua hàng (theo phòng ban)

Dữ liệu tính realtime từ `/api/reports/request-matrix?kind=pyc`. Ma trận: phòng ban × tháng. Chỉ hiển thị với người dùng có quyền `purchase_request:read`.

| Cột | Nội dung |
|-----|---------|
| Phòng ban | Phòng ban yêu cầu |
| Tổng | Tổng số phiếu YCMH |
| Nháp | Đang nháp |
| Chờ duyệt | Đã gửi, chờ TBP duyệt |
| Đã duyệt | TBP đã duyệt |
| Đang xử lý | Đang trong quy trình mua hàng |
| Hoàn tất | Hoàn thành |
| Từ chối | Bị từ chối |
| Đã hủy | Đã hủy |

### Tab Yêu cầu khảo sát (theo phòng ban)

Dữ liệu tính realtime từ `/api/reports/request-matrix?kind=ycks`. Ma trận: phòng ban × tháng. Chỉ hiển thị với người dùng có quyền `survey_request:read`.

| Cột | Nội dung |
|-----|---------|
| Phòng ban | Phòng ban yêu cầu |
| Tổng | Tổng số phiếu YCKS |
| Nháp | Đang nháp |
| Chờ duyệt | Đã gửi, chờ duyệt |
| Đang khảo sát | Đang trong quy trình khảo sát |
| Đã khảo sát | Khảo sát xong, chờ chốt |
| Đã tạo yêu cầu mua hàng | Đã chốt và tạo PYC |
| Hoàn tất | Hoàn thành |
| Đã hủy | Đã hủy |

### Tab Tồn kho

> Tạm ẩn trong phiên bản hiện tại (tab không hiển thị trên UI). Dữ liệu tồn kho được trình bày tóm tắt trong thẻ số liệu Tab Tổng quan.

---

### Tính năng giao diện & mobile

| Tính năng | Mô tả |
|---|---|
| Tab cuộn ngang | Thanh tab sử dụng `overflow-x: auto` — cuộn ngang khi quá nhiều tab không vừa màn hình nhỏ |
| Cột đầu ghim (sticky) | Cột STT (`#`) và cột tên ghim bên trái (`position: sticky`) khi cuộn bảng ngang — cột tên tối đa `nameMinWidth` trên desktop, tối đa 45vw trên mobile |
| Bộ lọc wrap | Khu bộ lọc trên sử dụng `flexWrap: wrap` — tự xuống hàng trên màn hình hẹp |

---

## Bao cao khao sat

### Mục đích

Tổng hợp và theo dõi trạng thái phê duyệt các dòng khảo sát (cả dòng NCC và dòng Sản phẩm) trên tất cả phiếu khảo sát mà người dùng có quyền xem. Hỗ trợ lọc đa chiều, xuất CSV.

Đường dẫn: `/survey-report`. Quyền: `survey:read` (kết hợp với phạm vi dữ liệu của entity `survey`).

API: `GET /api/survey-report/lines` — trả về danh sách dòng đã gộp NCC + SP, kèm bản tóm tắt đếm theo trạng thái duyệt.

### Thẻ tóm tắt (Summary cards)

Bốn thẻ đếm theo trạng thái duyệt dòng (`line_approve`), hiển thị tổng trước khi lọc theo trạng thái. Bấm vào thẻ để lọc nhanh theo trạng thái đó:

| Trạng thái | Màu |
|-----------|-----|
| Chờ duyệt | Cam |
| Đã duyệt | Xanh lá |
| Không duyệt | Đỏ |
| Thiếu thông tin | Cam sẫm |

### Bộ lọc

| Bộ lọc | Kiểu | Ghi chú |
|--------|------|---------|
| Loại dòng (`kind`) | Chọn | NCC / Sản phẩm / Tất cả |
| Trạng thái dòng (`line_approve`) | Chọn | Chờ duyệt / Đã duyệt / Không duyệt / Thiếu thông tin / Tất cả |
| Phân loại (`item_group`) | Chọn | Từ danh sách `item_group`; tương ứng `item_group` của phiếu khảo sát |
| NCC (`supplier`) | Nhập tay (LIKE) | Lọc theo `supplier_code` (chứa, không phân biệt hoa thường) |
| Mã phiếu (`code`) | Nhập tay (LIKE) | Lọc theo `survey_code` |
| NSPT (`nspt`) | Nhập tay (LIKE) | Lọc theo tên NSPT của phiếu |
| Từ ngày / Đến ngày (`date_from` / `date_to`) | Chọn ngày | Lọc theo ngày liên hệ của dòng (`contact_date`) |

Tất cả bộ lọc có debounce 300ms và tự động tải lại khi thay đổi.

**Bộ lọc được lưu lên URL (CR-045).** Mọi ô lọc ở trên ghi thẳng vào query string, nên **F5 không mất điều kiện lọc** và **gửi link cho đồng nghiệp là họ mở ra thấy đúng cái mình đang xem**. Ba quy ước:

- Ô **rỗng hoặc đúng bằng giá trị mặc định thì không ghi lên URL** — link ngắn gọn, và sau này đổi mặc định cũng không làm link cũ hiểu sai.
- Ghi theo kiểu **`replace`**, nên bấm **Back** là quay về **trang trước**, không phải lùi từng lần gõ ô lọc.
- Dùng hook chung `frontend/src/hooks/use-url-filters.ts` (`useUrlFilters`), cùng chỗ với **Bộ lọc điều kiện** (`<trường>__<phép so sánh>`); hai bên chỉ đụng đúng các key của mình nên không đè nhau.

> Báo cáo mua hàng (`/reports`) **chưa áp** cơ chế này — bộ lọc Công ty / Năm ở đó vẫn mất khi F5.

### Cột bảng kết quả

| Cột | Nội dung |
|-----|---------|
| Mã phiếu (`survey_code`) | Link dẫn tới `/surveys/:id` |
| Loại (`kind`) | Badge: NCC (xanh dương nhạt) / SP (xanh lá nhạt) |
| Nội dung (`content`) | Tóm tắt nội dung dòng (tên NCC hoặc tên SP) |
| Phân loại (`item_group`) | Phân loại VTBB/NL của phiếu |
| NSPT (`nspt`) | Nhân sự phụ trách phiếu |
| Ngày (`date`) | Ngày liên hệ của dòng (`contact_date`) |
| Trạng thái duyệt (`line_approve`) | Badge màu theo trạng thái |
| Ghi chú duyệt (`line_approve_note`) | Nội dung yêu cầu/ý kiến của TP/QL |

### Sắp xếp và phân trang

Mặc định sắp xếp theo `survey_id` giảm dần, sau đó theo `kind` (supplier trước product), sau đó `line_id`. Phân trang 20 dòng / trang với điều hướng trang đầu/cuối/lân cận.

### Xuất CSV

Nút "Xuất CSV" xuất toàn bộ trang hiện tại (theo bộ lọc đang áp) ra file `bao-cao-khao-sat-YYYY-MM-DD.csv`. Các cột: Mã phiếu, Loại, Nội dung, Phân loại, NSPT, Ngày, Trạng thái duyệt, Ghi chú duyệt. File UTF-8 có BOM để Excel đọc đúng tiếng Việt.

---

## Lần rà soát gần nhất

Tài liệu này viết ngày 2026-08-05 và **để nguyên gần một tháng** trong khi phần Nhân sự / Người dùng có thay đổi. Lần rà soát 2026-08-11 đối chiếu lại với mã nguồn và bổ sung những phần đã thiếu:

| Nội dung | Đối chiếu với | Kết quả |
|---|---|---|
| Vai trò mặc định của tài khoản mới (CR-037) | `backend/app/modules/user/service.py` — `DEFAULT_ROLE_CODE = "employee"` | Đã bổ sung vào trường 6 mục *Người dùng* |
| Dọn tài khoản mồ côi (CR-037) | `service.py` — `orphan_user_ids`, `delete_user`, `user_data_refs`; `controller.py` — `no_role` / `orphan` / `is_orphan`, `PUT .../active`, `DELETE /api/users/{id}` | Đã bổ sung mục riêng; **4 chốt chặn khi xóa** kiểm lại đúng từng dòng mã |
| Xóa kéo theo dữ liệu nào | `delete_user` — xóa `UserRole`, `UserScope`, `Notification`, `PushSubscription`; **giữ** `tab_audit_log` (`_SKIP_REF_TABLES`) | Khớp; đã ghi rõ trong tài liệu |
| Ảnh đại diện nhân sự | `employee/model.py` (property `avatar` đọc từ `tab_user`), `employee/controller.py` — `POST /{eid}/avatar` | Trước đây tài liệu **không có** trường này; đã thêm thành trường 10 mục *Nhân sự* |
| Bộ lọc lưu lên URL (CR-045) | `frontend/src/hooks/use-url-filters.ts`; `SurveyReport.tsx` có dùng, `Reports.tsx` và `RolePermissions.tsx` **không** | Đã ghi vào mục *Báo cáo khảo sát*, kèm ghi chú Báo cáo mua hàng chưa áp |
| Các trường còn lại của Nhân sự / Người dùng / Vai trò / Cấu hình | Model + form tương ứng | Không đổi so với bản 2026-08-05 |

Còn thiếu, sẽ bổ sung khi có dịp: **Bộ lọc điều kiện** (`frontend/src/config/conditional-filters.ts`) là cơ chế dùng chung cho 17 màn danh sách — nên viết thành một mục riêng ở tài liệu khối dùng chung thay vì nhắc rải rác từng file.
