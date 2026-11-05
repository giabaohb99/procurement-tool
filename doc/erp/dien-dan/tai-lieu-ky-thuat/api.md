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

> Bảng mục 1 dựng TỰ ĐỘNG từ `app.routes` bằng `backend/scripts/dung_bang_api.py` (lần cuối 05/11/2026): *Mục đích* = dòng đầu docstring (không có thì tên hàm — sửa docstring trong mã, đừng sửa tay); *Quyền* = `require(entity, action)` / `require_report` gắn trên đường; *Phạm vi* và *Ai gọi* ghi tay được giữ, chữ *tự dò:* là máy dò từ frontend-v2 và cổng MCP. *Phạm vi* trống nghĩa là **chưa soát** (có thể lọc ở service).

Mã backend: `forum`

## 1. Bảng đường API

| Phương thức | Đường | Mục đích | Quyền (`entity.action`) | Phạm vi | Ai gọi |
|---|---|---|---|---|---|
| GET | `/api/forum/boards` | Cây nhóm → box kèm bộ đếm + khối bài-mới-nhất — màn "Diễn đàn" (F13b). | đăng nhập |  | tự dò: v2 `forum` |
| POST | `/api/forum/boards` | Tạo nhóm/box — cấu trúc chuyên mục do admin quyết thủ công (chốt 03/09). | `forum_board.create` |  | tự dò: v2 `forum` |
| GET | `/api/forum/boards/highlights` | Sidebar phải màn "Diễn đàn" (F13c): "Đang sôi nổi" (auto 7 ngày) + "Mới nhất". | đăng nhập |  | tự dò: v2 `forum` |
| PUT | `/api/forum/boards/{board_id}` | Sửa tên/mô tả/icon/thứ tự/trạng thái — ẩn box là rút khỏi mắt, không xóa. | `forum_board.write` |  | tự dò: v2 `forum` |
| DELETE | `/api/forum/boards/{board_id}` | Xóa nhóm/box RỖNG — còn box con hay còn bài thì service chặn 400. | `forum_board.delete` |  | tự dò: v2 `forum` |
| GET | `/api/forum/boards/{board_id}/threads` | Danh sách thread của một box — phân trang số trang, sắp theo hoạt động cuối, thread ghim nổi lên đầu (F13a). | đăng nhập |  | tự dò: v2 `forum` |
| GET | `/api/forum/moderation-logs` | Nhật ký kiểm duyệt (CR-263) — bảng ghi từ F5, giờ mới có màn đọc. | `forum_post.read` |  | tự dò: v2 `forum` |
| GET | `/api/forum/posts` | Bảng tin — thời gian thuần mới → cũ, con trỏ `before_id`, lọc audience trong SQL. | đăng nhập |  | tự dò: v2 `forum` |
| POST | `/api/forum/posts` | Đăng bài — lên feed ngay, không qua duyệt (QĐ-D1). | đăng nhập |  | tự dò: v2 `forum` |
| GET | `/api/forum/posts/pinned` | Bài đang ghim (F9a/CR-199) — dải đầu Bảng tin + tab "Thông báo". | đăng nhập |  | tự dò: v2 `forum` |
| GET | `/api/forum/posts/search` | Tìm bài viết (CR-263) — mở cho MỌI người đăng nhập, kết quả tự lọc qua luật audience trong SQL nên người thường tìm gì cũng chỉ ra bài mình vốn được xem; quản trị thấy cả bài ẩn + lọc `status`. | đăng nhập |  | tự dò: v2 `forum` |
| GET | `/api/forum/posts/{pid}` | Một bài — đích đến của chuông thông báo (`/posts/:id`). | đăng nhập |  | tự dò: v2 `forum` |
| PATCH | `/api/forum/posts/{pid}` | Sửa bài (bao-CR-707) — tác giả sửa bài mình; quản trị diễn đàn sửa mọi bài, chuyển box, gắn nhãn Thông báo. | đăng nhập |  | tự dò: v2 `forum` |
| DELETE | `/api/forum/posts/{pid}` | Xóa bài của CHÍNH MÌNH. | đăng nhập |  | tự dò: v2 `forum` |
| POST | `/api/forum/posts/{pid}/hide` | Ẩn bài — lý do bắt buộc, tác giả nhận chuông kèm lý do (QĐ-D1). | `forum_post.write` |  | tự dò: v2 `forum` |
| POST | `/api/forum/posts/{pid}/like` | Bấm cảm xúc (CR-206) — không sinh chuông (D-Q6, cùng lý do CR-030). | đăng nhập |  | tự dò: v2 `forum` |
| GET | `/api/forum/posts/{pid}/likes` | Ai đã bày tỏ cảm xúc với bài — hiện khi bấm vào con số, kèm `kind` để FE lọc. | đăng nhập |  | tự dò: v2 `forum` |
| POST | `/api/forum/posts/{pid}/pin` | Ghim bài lên dải Thông báo — chỉ bài đang hiển thị (service chặn 400). | `forum_post.write` |  | tự dò: v2 `forum` |
| POST | `/api/forum/posts/{pid}/remove` | Xóa bài (kiểm duyệt) — KHÁC tác giả tự xóa: chỉ đổi trạng thái REMOVED, giữ dòng + nhật ký để đối soát; bài biến khỏi mọi mắt qua API. | `forum_post.delete` |  | tự dò: v2 `forum` |
| POST | `/api/forum/posts/{pid}/restore` | Khôi phục bài đã ẩn — báo tác giả để họ khỏi tưởng bài vẫn bị ẩn. | `forum_post.write` |  | tự dò: v2 `forum` |
| POST | `/api/forum/posts/{pid}/unpin` | Bỏ ghim — bài vẫn nằm nguyên trên feed theo thời gian. | `forum_post.write` |  | tự dò: v2 `forum` |
| GET | `/api/forum/search/filters` | Danh sách công ty + phòng ban cho ô lọc màn tìm kiếm — lấy distinct từ chính bảng bài viết, không đụng grant danh mục của người thường. | đăng nhập |  | tự dò: v2 `forum` |
| GET | `/api/forum/users/{author_id}/posts` | Trang cá nhân = tủ bài viết (QĐ-D3). | đăng nhập |  | tự dò: v2 `forum` |

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
