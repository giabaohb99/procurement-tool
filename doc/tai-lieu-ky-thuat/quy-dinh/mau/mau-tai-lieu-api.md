# TÀI LIỆU API — <TÊN PHÂN HỆ>

| | |
|---|---|
| Bản | 1.0 |
| Ngày | DD/MM/YYYY |
| Người phụ trách | <tên> |
| Trạng thái | Nháp / Hiệu lực |
| CR liên quan | <mã CR> |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `<tag>`. Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`. Danh sách có phân trang trả `data = {items, total, page, page_size}`.

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/<...>` | Danh sách, lọc, phân trang | `<entity>.read` | `apply_scope` | Màn `<...>`; MCP `<tool>` |
| GET | `/api/<...>/{id}` | Chi tiết | `<entity>.read` | `get_scoped` (ngoài phạm vi → 404) | |
| POST | `/api/<...>` | Tạo | `<entity>.create` | | |
| PATCH | `/api/<...>/{id}` | Sửa | `<entity>.write` | | |
| DELETE | `/api/<...>/{id}` | Xóa (mềm / cứng) | `<entity>.delete` | | |
| POST | `/api/<...>/{id}/<hành động>` | | | | |

## 2. Dữ liệu vào / ra chính

Chỉ ghi trường mang luật nghiệp vụ (bắt buộc, giá trị mã, đơn vị); phần còn lại xem `/docs`.

| Đường | Trường | Ý nghĩa / luật |
|---|---|---|
| | | |

## 3. Lỗi riêng của phân hệ

| Mã HTTP | Khi nào | Câu báo |
|---|---|---|
| 400 | | |
| 403 | | |
| 409 | | |
| 422 | | |

## 4. Bộ lọc danh sách

| Tham số | Kiểu | Ghi chú |
|---|---|---|
| | | |

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
