# Requirement chi tiết — VAI TRÒ & PHÂN QUYỀN

> Màn **Vai trò** (`/roles`) — Quản lý danh sách vai trò (Role) và cấu hình phân quyền (Permission) chi tiết cho từng đối tượng/bảng (Entity). Hệ thống cấp quyền truy cập, thao tác và phạm vi dữ liệu cho tài khoản dựa trên vai trò được gán.

## 1. Danh sách Vai trò mặc định (Default Roles)
Dựa theo yêu cầu nghiệp vụ, hệ thống cần định nghĩa tối thiểu 3 vai trò mặc định sau:

| Mã Vai trò | Tên Vai trò | Cấp quyền (Permissions) | Phạm vi (Scope) |
|---|---|---|---|
| `ADMIN` | **Administrator** | Full quyền (Đọc, Tạo, Sửa, Xóa, Duyệt, In, Export) trên TẤT CẢ các chức năng và module. | `all` (Toàn hệ thống) |
| `MANAGER` | **Trưởng bộ phận** | Được phép Xem (`read`) và Duyệt (`approve`) các yêu cầu (mua hàng, thanh toán, v.v.). | `dept` (Toàn bộ dữ liệu của Phòng ban mình quản lý) |
| `STAFF` | **Nhân viên** | Chỉ được Tạo mới (`create`) và Xem (`read`) trạng thái các yêu cầu do chính mình tạo. KHÔNG có quyền duyệt. | `own` (Chỉ dữ liệu do chính mình tạo) |

*Lưu ý: Quản trị viên (Administrator) có quyền thêm mới hoặc chỉnh sửa các vai trò khác (ví dụ: Kế toán, Thủ kho) tùy theo nhu cầu vận hành thực tế.*

## 2. Nguồn dữ liệu & Cấu trúc (DB)
Bảng dùng: `tab_role` (Vai trò) và `tab_permission` (Phân quyền chi tiết).
- **`tab_role`**:
  - `code`: Mã vai trò (duy nhất, vd: ADMIN, MANAGER, STAFF).
  - `name`: Tên vai trò hiển thị.
  - `description`: Mô tả ý nghĩa của vai trò.
- **`tab_permission`**:
  - `role_id`: Khóa ngoại trỏ về `tab_role`.
  - `entity`: Mã đối tượng/module (vd: `purchase_request`, `employee`, `report`).
  - Phân quyền hành động (Boolean): `can_read`, `can_create`, `can_write`, `can_delete`, `can_approve`, `can_print`, `can_export`.
  - `scope`: Phạm vi áp dụng quyền (enum: `own` - của mình, `dept` - của phòng ban, `all` - tất cả).

## 3. Chức năng CRUD Vai trò
- **Danh sách vai trò:** Hiển thị danh sách bảng (CrudList) gồm Mã, Tên, Mô tả.
- **Thêm/Sửa vai trò (Kèm Ma trận phân quyền - Permission Matrix):**
  - Màn hình thêm/sửa ngoài thông tin cơ bản (Mã, Tên, Mô tả) còn hiển thị **Ma trận phân quyền**.
  - **Dòng (Rows):** Các module chức năng (Yêu cầu mua, Đơn hàng, Nhân sự, Kho, Báo cáo...).
  - **Cột (Columns):** Các quyền (Xem, Tạo, Sửa, Xóa, Duyệt...) và một cột Chọn Scope (Cá nhân / Phòng ban / Tất cả).
  - Khi người dùng ấn **Lưu**, API sẽ nhận thông tin vai trò và danh sách các dòng quyền để cập nhật đồng thời (ghi đè vào `tab_permission`).
- **Xóa vai trò:** Không cho phép xóa các vai trò mặc định của hệ thống (ADMIN) hoặc các vai trò đang có người dùng (User/Employee) gắn vào.

## 4. API & Logic xử lý (Backend)
```text
GET /api/roles                -> Lấy danh sách Vai trò
GET /api/roles/{id}           -> Lấy thông tin Vai trò + mảng Permissions đi kèm
POST /api/roles               -> Tạo mới Vai trò + bulk insert bảng Permissions
PATCH /api/roles/{id}         -> Cập nhật Vai trò + cập nhật/ghi đè Permissions
DELETE /api/roles/{id}        -> Xóa vai trò (kiểm tra điều kiện ràng buộc)
```

**Middleware Phân quyền (`app.core.auth.require`):**
Mọi API thao tác dữ liệu đều phải chạy qua hàm Depends kiểm tra quyền. Luồng xử lý:
1. Lấy thông tin tài khoản từ Token -> Xác định `role_id` từ bảng `tab_user_role`.
2. Kiểm tra trong `tab_permission` xem `role_id` đó có quyền trên `entity` (vd: `purchase_request`) với hành động tương ứng (vd: `can_approve`) hay không.
3. Nếu hợp lệ, trả về thông tin đối tượng kèm theo biến `scope` để truyền xuống tầng Service.
4. Ở tầng Service (Lọc dữ liệu):
   - Nếu `scope == "own"` -> Query chỉ filter các bản ghi có `created_by = user.id`.
   - Nếu `scope == "dept"` -> Query filter các bản ghi có `department_id = user.department_id`.
   - Nếu `scope == "all"` -> Trả về toàn bộ (Không filter).

## 5. UI/UX (Frontend)
- Màn hình danh sách `/roles` thiết kế dạng Table list (có bộ lọc Mã, Tên).
- Màn hình chi tiết `/roles/new` và `/roles/:id`:
  - Nửa trên: Form thông tin chung.
  - Nửa dưới: **Bảng phân quyền (Checkbox Grid)**. Sử dụng toggle hoặc checkbox để bật/tắt nhanh các quyền cho từng module.
  - Cột Scope dùng Dropdown Select (Tất cả / Phòng ban / Cá nhân).
  - Thêm nút tiện ích: "Chọn tất cả Xem", "Chọn tất cả Tạo"... trên đầu các cột để thao tác nhanh.

## 6. Mở rộng sau
- Tính năng ủy quyền (Delegation): Trưởng phòng đi công tác có thể ủy quyền "Duyệt" (Approve) tạm thời cho một Nhân viên trong thời gian nhất định.
- Hỗ trợ Kế thừa vai trò (Role Inheritance) để giảm bớt việc phải check lại toàn bộ ma trận khi tạo mới.

## 7. Ràng buộc nghiệp vụ liên quan (Data Constraints)
Sự tồn tại của các vai trò ảnh hưởng trực tiếp đến logic nhập liệu của các module khác, cụ thể:
- **Module Nhân sự (`tab_employee`):** Khi tạo mới hoặc cập nhật thông tin nhân sự, trường **Vai trò** (Role) là **bắt buộc chọn**.
- **Module Phòng ban (`tab_department`):** Khi tạo mới hoặc cập nhật một phòng ban, tại trường chọn **Trưởng bộ phận**, hệ thống phải lọc và chỉ hiển thị danh sách các nhân sự đang được gán vai trò là **Trưởng bộ phận** (hoặc `MANAGER`). Không cho phép chọn nhân sự thông thường làm trưởng bộ phận.
