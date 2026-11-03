# TÀI LIỆU API — DIỄN ĐÀN

| | |
|---|---|
| Bản | 0.1 |
| Ngày | 03/11/2026 |
| Người phụ trách | chưa giao (bản dựng tự động từ mã) |
| Trạng thái | Nháp |
| CR liên quan | bao-CR-712 |

**Tra tham số đầy đủ:** trang `/docs` (Swagger do FastAPI sinh từ mã — dev `https://deverp.degoholding.vn/docs`, prod `https://erp.degoholding.vn/docs`), nhóm (tag) `forum`.
Tệp này giữ phần Swagger không nói được: **quyền, phạm vi, luật nghiệp vụ, ai gọi**.

**Phong bì chung:** mọi đường trả `{success, message, data}`; lỗi trả `{success: false, error: {code, message, details}}`.

> Bảng mục 1 dựng TỰ ĐỘNG ngày 03/11/2026 từ `app.routes` (bao-CR-712): *Mục đích* = dòng đầu docstring (không có thì tên hàm); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* chỉ ghi khi thấy `apply_scope` / `get_scoped` / `scope_condition` ngay trong hàm đường — trống nghĩa là **chưa soát** (có thể lọc ở service). Người phụ trách soát lại và điền cột *Ai gọi*, mục 2–4.

Mã backend: `forum`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/forum/boards` | Cây nhóm → box kèm bộ đếm + khối bài-mới-nhất — màn "Diễn đàn" (F13b). | — |  | |
| POST | `/api/forum/boards` | Tạo nhóm/box — cấu trúc chuyên mục do admin quyết thủ công (chốt 03/09). | `forum_board.create` |  | |
| GET | `/api/forum/boards/highlights` | Sidebar phải màn "Diễn đàn" (F13c): "Đang sôi nổi" (auto 7 ngày) + | — |  | |
| DELETE | `/api/forum/boards/{board_id}` | Xóa nhóm/box RỖNG — còn box con hay còn bài thì service chặn 400. | `forum_board.delete` |  | |
| PUT | `/api/forum/boards/{board_id}` | Sửa tên/mô tả/icon/thứ tự/trạng thái — ẩn box là rút khỏi mắt, không xóa. | `forum_board.write` |  | |
| GET | `/api/forum/boards/{board_id}/threads` | Danh sách thread của một box — phân trang số trang, sắp theo hoạt động | — |  | |
| GET | `/api/forum/moderation-logs` | Nhật ký kiểm duyệt (CR-263) — bảng ghi từ F5, giờ mới có màn đọc. | `forum_post.read` |  | |
| GET | `/api/forum/posts` | Bảng tin — thời gian thuần mới → cũ, con trỏ `before_id`, lọc audience trong SQL. | — |  | |
| POST | `/api/forum/posts` | Đăng bài — lên feed ngay, không qua duyệt (QĐ-D1). | — |  | |
| GET | `/api/forum/posts/pinned` | Bài đang ghim (F9a/CR-199) — dải đầu Bảng tin + tab "Thông báo". | — |  | |
| GET | `/api/forum/posts/search` | Tìm bài viết (CR-263) — mở cho MỌI người đăng nhập, kết quả tự lọc qua | — |  | |
| DELETE | `/api/forum/posts/{pid}` | Xóa bài của CHÍNH MÌNH. Quản trị ẩn/xóa bài người khác là chuyện F5 — | — |  | |
| GET | `/api/forum/posts/{pid}` | Một bài — đích đến của chuông thông báo (`/posts/:id`). | — |  | |
| PATCH | `/api/forum/posts/{pid}` | Sửa bài (bao-CR-707) — tác giả sửa bài mình; quản trị diễn đàn sửa mọi bài, | — |  | |
| POST | `/api/forum/posts/{pid}/hide` | Ẩn bài — lý do bắt buộc, tác giả nhận chuông kèm lý do (QĐ-D1). | `forum_post.write` |  | |
| POST | `/api/forum/posts/{pid}/like` | Bấm cảm xúc (CR-206) — không sinh chuông (D-Q6, cùng lý do CR-030). | — |  | |
| GET | `/api/forum/posts/{pid}/likes` | Ai đã bày tỏ cảm xúc với bài — hiện khi bấm vào con số, kèm `kind` để FE lọc. | — |  | |
| POST | `/api/forum/posts/{pid}/pin` | Ghim bài lên dải Thông báo — chỉ bài đang hiển thị (service chặn 400). | `forum_post.write` |  | |
| POST | `/api/forum/posts/{pid}/remove` | Xóa bài (kiểm duyệt) — KHÁC tác giả tự xóa: chỉ đổi trạng thái REMOVED, | `forum_post.delete` |  | |
| POST | `/api/forum/posts/{pid}/restore` | Khôi phục bài đã ẩn — báo tác giả để họ khỏi tưởng bài vẫn bị ẩn. | `forum_post.write` |  | |
| POST | `/api/forum/posts/{pid}/unpin` | Bỏ ghim — bài vẫn nằm nguyên trên feed theo thời gian. | `forum_post.write` |  | |
| GET | `/api/forum/search/filters` | Danh sách công ty + phòng ban cho ô lọc màn tìm kiếm — lấy distinct từ | — |  | |
| GET | `/api/forum/users/{author_id}/posts` | Trang cá nhân = tủ bài viết (QĐ-D3). Trang của CHÍNH MÌNH thấy cả bài bị ẩn. | — |  | |

## 2. Dữ liệu vào / ra chính

Chưa có — người phụ trách điền các trường mang luật nghiệp vụ.

## 3. Lỗi riêng của phân hệ

Chưa có.

## 4. Bộ lọc danh sách

Chưa có.

## 5. Thay đổi gần đây

| Ngày | CR | Đổi gì (thêm / sửa / bỏ đường) |
|---|---|---|
| 03/11/2026 | bao-CR-712 | Dựng bản đầu từ mã |
