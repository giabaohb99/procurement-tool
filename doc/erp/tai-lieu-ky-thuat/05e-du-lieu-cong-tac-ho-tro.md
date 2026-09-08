# TỪ ĐIỂN DỮ LIỆU — CỘNG TÁC · HỖ TRỢ · THÔNG BÁO

Bản 1.0 — 28/08/2026. Nguồn sự thật là model.py; tệp này chép Ý NGHĨA, không thay mã.

---

Mọi bảng đều kế thừa `AuditMixin`. Các cột dùng chung không lặp lại trong từng mục:

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | BIGINT PK | Khóa chính tự tăng |
| `created_at` | DATETIME | Thời điểm tạo dòng (server default = now()) |
| `created_by` | BIGINT | `user_id` người tạo |
| `updated_at` | DATETIME | Thời điểm sửa cuối (tự cập nhật) |
| `updated_by` | BIGINT | `user_id` người sửa cuối |

---

## Cụm A — Diễn đàn nội bộ

### `tab_forum_post` — Bài viết diễn đàn

Bảng trung tâm của diễn đàn nội bộ. Mỗi dòng là một bài đăng; tác giả xác định qua `created_by` (user_id), không phải employee_id. Trường `dept_id` và `company_id` đóng băng theo hồ sơ tác giả tại thời điểm đăng — chuyển phòng sau không làm bài cũ đổi phạm vi xem.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `body` | TEXT | Nội dung bài viết (tối đa 10 000 ký tự, không rich text) |
| `status` | SMALLINT | Trạng thái bài: 0=PENDING_REVIEW (chừa sẵn, chưa dùng), 1=PUBLISHED (đang hiển thị), 2=HIDDEN (quản trị ẩn — tác giả vẫn thấy kèm lý do), 3=REMOVED (xóa — biến khỏi mọi feed, giữ dòng để đối soát) |
| `audience` | SMALLINT | Đối tượng xem: 1=DEPT (phòng ban tác giả), 2=COMPANY (pháp nhân tác giả), 3=PUBLIC (toàn tập đoàn) |
| `kind` | SMALLINT | Loại bài: 0=NORMAL (bài thường), 1=AVATAR_UPDATE (bài đổi ảnh đại diện — phải kèm đúng 1 file) |
| `dept_id` | BIGINT | ID phòng ban của tác giả tại thời điểm đăng (đóng băng) |
| `company_id` | BIGINT | ID pháp nhân của tác giả tại thời điểm đăng (đóng băng) |
| `pinned_at` | DATETIME NULL | Mốc thời gian ghim bài (NULL = bài thường; có giá trị = đang ghim, dùng để sắp xếp dải ghim mới lên đầu) |
| `board_id` | BIGINT NULL | F13a: box chứa bài (trỏ `tab_forum_board.id`). NULL = bài Bảng tin thuần |
| `title` | VARCHAR(255) NULL | F13a: tiêu đề thread — bắt buộc khi có `board_id` (service chặn 400), bài feed để NULL |
| `prefix` | SMALLINT | F13a: prefix thread (`ForumPrefix`): 0=NONE, 1=DISCUSSION (thảo luận), 2=QUESTION (thắc mắc), 3=KNOWLEDGE (kiến thức), 4=SHOWCASE (khoe), 5=REVIEW (đánh giá). Nhãn TV khai ở `core/forum_codes.py`, sinh TS qua `gen_status_ts.py` |

Index: `(status, id)` cho feed chung; `(created_by, id)` cho trang cá nhân; `(board_id, id)` cho thread list của box (F13a).

**Logic chính:**
- Feed lọc theo điều kiện: `status=PUBLISHED AND (audience=PUBLIC OR (audience=COMPANY AND company_id=pháp_nhân_người_xem) OR (audience=DEPT AND dept_id=phòng_người_xem) OR created_by=người_xem)`.
- Người thường không có grant RBAC trên `forum_post`; entity này chỉ gác cổng kiểm duyệt của `forum_admin`.
- Phân trang dùng con trỏ `before_id` (id nhỏ nhất đang hiện), cấm OFFSET để tránh lệch trang khi có bài mới chen vào.
- Bài `REMOVED` biến khỏi mọi mắt qua API nhưng dòng trong DB được giữ lại để đối soát.
- Bài `HIDDEN` chỉ tác giả và `forum_admin` còn thấy, kèm lý do từ `tab_forum_moderation_log`.
- Đính kèm ảnh/video đi qua `FileLink` entity `forum_post`; tối đa 10 file/bài.
- Bài `AVATAR_UPDATE` phải kèm đúng 1 file (chính avatar mới); thiếu thì bị 400.
- Bài trong box (F13a): audience bị ÉP theo box (đợt đầu toàn PUBLIC — QĐ-D7a); bài vẫn ra feed như thường (QĐ-D7b). Thread list của box phân trang SỐ TRANG `page/per_page`, sắp theo hoạt động cuối = max(lúc đăng, bình luận cuối), thread ghim (`pinned_at`) nổi lên đầu.

---

### `tab_forum_board` — Nhóm/box chuyên mục (F13a, QĐ-D7)

Cấu trúc chuyên mục kiểu VOZ — MỘT bảng cho cả hai tầng: dòng không `parent_id` là NHÓM chỉ làm tiêu đề (không chứa bài trực tiếp), dòng có `parent_id` là BOX nhận bài. Đúng hai tầng, service chặn lồng sâu hơn. Cấu trúc do `forum_admin` quyết thủ công (entity `forum_board` — grant riêng, tách khỏi kiểm duyệt bài); bài trong box đăng là hiện ngay, KHÔNG duyệt trước (chốt 03/09/2026).

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `parent_id` | BIGINT NULL | NULL = nhóm tiêu đề; có giá trị = box thuộc nhóm đó |
| `name` | VARCHAR(255) | Tên nhóm/box |
| `description` | TEXT | Mô tả ngắn hiện dưới tên box |
| `icon` | VARCHAR(50) | Tên icon lucide hoặc 1 emoji do admin chọn — FE tự vẽ |
| `sort_order` | SMALLINT | Thứ tự hiển thị trong cây (nhỏ trước) |
| `status` | SMALLINT | `ForumBoardStatus`: 1=ACTIVE (đang mở), 2=HIDDEN (admin ẩn — không nhận bài mới, biến khỏi cây với người thường, bài cũ giữ nguyên) |
| `audience` | SMALLINT | Chừa sẵn cho box theo phòng/pháp nhân — đợt đầu ÉP PUBLIC=3 (QĐ-D7a), không nhận từ client |

**Logic chính:**
- `GET /api/forum/boards` trả cây nhóm → box, mỗi box kèm bộ đếm (số thread + tổng bình luận, COUNT trực tiếp chưa denormalize) và khối bài-mới-nhất (thread + mốc + người viết cuối theo công thức hoạt động cuối).
- Box ẩn / nhóm cha ẩn / nhóm tiêu đề / id không tồn tại đều KHÔNG nhận bài (400 gộp).
- Xóa chỉ được khi RỖNG: nhóm còn box hay box còn bài thì 400 — muốn rút khỏi mắt thì ẨN.
- Nhóm đang chứa box không hạ xuống làm box được (chặn đẻ tầng ba).

---

### `tab_forum_reaction` — Cảm xúc bài viết

Lưu cảm xúc kiểu Facebook của một người với một bài viết. Unique theo cặp (bài, người) — đổi cảm xúc là UPDATE, bấm lại cùng cảm xúc là xóa dòng.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `post_id` | BIGINT | Trỏ `tab_forum_post.id` |
| `user_id` | BIGINT | Trỏ `tab_user.id` (người bày tỏ) |
| `kind` | SMALLINT | Loại cảm xúc: 1=LIKE (Thích), 2=LOVE (Yêu thích), 3=HAHA, 4=WOW (Tuyệt vời), 5=SAD (Buồn), 6=ANGRY (Phẫn nộ) |

Ràng buộc: `UNIQUE(post_id, user_id)`.

**Logic chính:**
- Dữ liệu like cũ (đợt 1 chỉ có LIKE=1) tự thành cảm xúc "Thích" mà không cần migration.
- Không sinh thông báo chuông khi bấm cảm xúc (theo quyết định D-Q6).
- API trả `{liked, count, my_reaction, reactions}` — `reactions` là dict `{kind: số_người}` chỉ chứa kind có người bấm.
- `like_map()` gom số đếm cho cả trang bằng đúng 1 query.

---

### `tab_forum_moderation_log` — Nhật ký kiểm duyệt

Ghi lại mọi hành động kiểm duyệt của `forum_admin` trên một bài. Không có đường "ẩn lặng lẽ" — mọi thay đổi trạng thái đều phải để lại dấu vết ở đây.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `post_id` | BIGINT | Trỏ `tab_forum_post.id` (index) |
| `action` | SMALLINT | Hành động: 1=HIDE (ẩn bài), 2=REMOVE (xóa bài), 3=RESTORE (khôi phục bài đã ẩn) |
| `reason` | TEXT | Lý do (bắt buộc khi HIDE/REMOVE; bỏ qua khi RESTORE) |
| `notified_at` | DATETIME NULL | Thời điểm đã bắn thông báo cho tác giả (NULL = chưa báo) |

**Logic chính:**
- Quản trị viên là `created_by` trên dòng nhật ký.
- Lý do rỗng khi HIDE/REMOVE sẽ bị 400 — điều kiện đủ của F5.
- Chuyển trạng thái hợp lệ: HIDE chỉ từ PUBLISHED; RESTORE chỉ từ HIDDEN; REMOVE từ PUBLISHED hoặc HIDDEN.
- REMOVE chỉ đổi `status`, không xóa dòng `tab_forum_post` (delete_post là hành động khác, cuốn theo toàn bộ comment và ảnh).
- `notified_at` tách biệt "đã ẩn" với "đã báo tác giả" để đối soát độc lập.

---

## Cụm B — Bình luận dùng chung

### `tab_comment` — Bình luận

Bình luận gắn vào bất kỳ loại chứng từ nào theo cặp `(entity, entity_id)`. Một bảng dùng chung cho mọi phân hệ, cùng khuôn `tab_file_link`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `entity` | VARCHAR(50) | Loại chứng từ (vd `forum_post`, `purchase_request`, `purchase_order`...) — danh sách hợp lệ ở `comment_registry.py` |
| `entity_id` | BIGINT | ID của chứng từ thuộc loại `entity` |
| `body` | TEXT | Nội dung bình luận; mention dùng thẻ `@[<user_id>]` trong chuỗi |
| `parent_id` | BIGINT | 0 = bình luận gốc; >0 = phản hồi treo vào bình luận gốc (chỉ 2 cấp — trả lời phản hồi cũng về cấp 2) |
| `reply_to_user_id` | BIGINT | User được trả lời trực tiếp (lưu ID, không dò chữ `@Tên` để tránh nhầm) |

**Logic chính:**
- Cây bình luận tối đa 2 tầng (khuôn YouTube): service tự kéo `parent_id` về gốc nếu trả lời một phản hồi.
- Mention nhiều người trong một bình luận thì cần `tab_comment_mention` — `reply_to_user_id` chỉ đủ cho đúng 1 người và mang nghĩa khác.
- Khi xóa bài diễn đàn, toàn bộ comment (kèm reaction và mention của chúng) bị cuốn theo.
- `entity` chỉ được nhận giá trị nằm trong registry — tránh bình luận lạc vào chứng từ không hỗ trợ.

---

### `tab_comment_mention` — Người được nhắc trong bình luận

Lưu danh sách user bị `@` trong một bình luận, mỗi người một dòng. Tách bảng vì một bình luận có thể nhắc nhiều người.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `comment_id` | BIGINT | Trỏ `tab_comment.id` |
| `user_id` | BIGINT | Trỏ `tab_user.id` (người được nhắc) |

Ràng buộc: `UNIQUE(comment_id, user_id)`.

**Logic chính:**
- Bảng phẳng dùng để bắn chuông và tra tên mà không phải mổ chuỗi `body`.
- Vị trí `@` trong câu vẫn nằm ở `tab_comment.body` dưới dạng `@[<user_id>]`.
- Không lưu `@Tên` vì tên tiếng Việt hay trùng và người viết có thể sửa sau.

---

### `tab_comment_reaction` — Lượt thích bình luận

Một người thích một bình luận — tối đa 1 dòng/cặp, bấm lại là bỏ. Cố ý chỉ có một loại (thích), không có dislike hay dải cảm xúc.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `comment_id` | BIGINT | Trỏ `tab_comment.id` |
| `user_id` | BIGINT | Trỏ `tab_user.id` (người thích) |

Ràng buộc: `UNIQUE(comment_id, user_id)`.

**Logic chính:**
- Mang nghĩa "đã đọc / đồng ý" trong nội bộ, thay cho hàng loạt bình luận "ok anh" làm loãng chứng từ.
- Không sinh thông báo chuông (sẽ rất ồn nếu chuông mỗi lượt thích bình luận).

---

## Cụm C — Phiếu hỗ trợ

### `tab_ticket` — Phiếu hỗ trợ

Mọi nhân viên đăng nhập đều mở được phiếu; nhóm vai trò `support` xử lý tập trung. Trạng thái và mức độ ưu tiên lưu dưới dạng mã chuỗi tiếng Anh (module này được tạo trước khi áp R2/QĐ-11).

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `code` | VARCHAR(50) UNIQUE | Mã phiếu tự sinh |
| `subject` | VARCHAR(255) | Tiêu đề phiếu |
| `department` | VARCHAR(255) | Nhóm/bộ phận (nhãn văn bản, dùng để lọc) |
| `priority` | VARCHAR(20) | Mức ưu tiên: `low`, `normal`, `high`, `urgent` |
| `status` | VARCHAR(30) | Trạng thái: `open` (mới), `in_progress` (đang xử lý), `answered` (đã trả lời), `closed` (đóng) |
| `company_id` | BIGINT | ID pháp nhân của người gửi |
| `requester_id` | BIGINT | ID nhân sự người gửi (hiển thị) — là employee_id, không phải user_id |
| `assignee_id` | BIGINT | `user_id` tài khoản người xử lý (tùy chọn) |
| `origin_url` | VARCHAR(500) | Trang người gửi đang đứng lúc tạo (dùng cho debug) |
| `closed_at` | DATETIME NULL | Thời điểm đóng phiếu |

**Logic chính:**
- `created_by` (AuditMixin) = `user_id` người gửi, dùng cho phạm vi `own`.
- `requester_id` là employee_id (không phải user_id) — dùng để hiển thị tên nhân sự trên phiếu.
- `assignee_id` là user_id người xử lý — khác `requester_id` về kiểu tham chiếu.
- Trao đổi giữa người gửi và nhóm hỗ trợ lưu trong `tab_ticket_message`.
- Cần gán vai trò `support` cho người phụ trách trước khi dùng tính năng phân công.

---

### `tab_ticket_message` — Tin nhắn trong phiếu hỗ trợ

Một lượt trao đổi trong luồng của phiếu hỗ trợ. Phân biệt tin của nhóm hỗ trợ và tin của người gửi qua cờ `is_staff`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `ticket_id` | BIGINT | Trỏ `tab_ticket.id` (index) |
| `body` | TEXT | Nội dung tin nhắn |
| `is_staff` | BOOLEAN | `True` = do nhóm hỗ trợ viết; `False` = do người gửi phiếu viết |

**Logic chính:**
- `created_by` (AuditMixin) = `user_id` người viết tin.
- Không dùng `tab_comment` — phiếu hỗ trợ có luồng trao đổi riêng biệt với bình luận chứng từ.

---

## Cụm D — Trung tâm hướng dẫn sử dụng

### `tab_help_article` — Bài viết hướng dẫn

Bài viết hướng dẫn sử dụng của Trung tâm HDSD. Tự tham chiếu qua `parent_id` để tạo cây thư mục bài viết.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `parent_id` | BIGINT NULL FK | Trỏ `tab_help_article.id` — bài cha trong cây thư mục (NULL = bài gốc/danh mục) |
| `title` | VARCHAR(255) | Tiêu đề bài |
| `content` | TEXT | Nội dung bài (HTML — phải qua `sanitize_html` khi nhận từ ngoài) |
| `sort_order` | INT | Thứ tự hiển thị trong cùng cấp |
| `summary` | VARCHAR(255) NULL | Mô tả ngắn hiển thị dưới tiêu đề ở thẻ danh mục trang chủ portal |
| `icon` | VARCHAR(500) NULL | Slug icon (vd `rocket`) hoặc URL ảnh do người dùng upload |

**Logic chính:**
- Cây thư mục không giới hạn cấp (self-referential); frontend tự dựng cây từ danh sách phẳng.
- Xóa bài cha cuốn theo bài con và slide nhờ cascade `delete-orphan`.
- Nội dung từ ngoài phải qua `sanitize_html` — đã có lỗ `srcdoc` từng bị khai thác.
- Đồng bộ nội dung dev → prod dùng flag `--theo-id --xoa-thua`.
- Chạy độc lập ở domain `help.degoholding.vn` / `devhelp.degoholding.vn`, dùng chung backend + tài khoản.

---

### `tab_help_article_slide` — Ảnh từng bước của bài viết

Danh sách ảnh minh họa từng bước gắn vào một bài hướng dẫn. Mỗi bài có thể có nhiều slide, hiển thị theo `step_order`.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `article_id` | BIGINT FK | Trỏ `tab_help_article.id` ON DELETE CASCADE |
| `image_url` | VARCHAR(500) | URL ảnh hướng dẫn |
| `caption` | TEXT NULL | Chú thích ảnh (tùy chọn) |
| `step_order` | INT | Thứ tự bước trong bài (0-based) |

**Logic chính:**
- Cascade `delete-orphan` từ `HelpArticle` — xóa bài thì slide biến theo.
- Relationship được `order_by="HelpArticleSlide.step_order"` để luôn trả đúng thứ tự bước.

---

### `tab_help_home_section` — Khung trang chủ Help Center

Bốn khung cố định trên trang chủ khu người dùng: `quick_start`, `categories`, `faq`, `tips`. Được seed sẵn, không cho thêm/xóa qua API — chỉ đổi tiêu đề, ẩn/hiện, thứ tự.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `key` | VARCHAR(30) UNIQUE | Định danh khung: `quick_start`, `categories`, `faq`, `tips` |
| `title` | VARCHAR(150) | Tiêu đề hiển thị của khung |
| `is_visible` | BOOLEAN | Ẩn/hiện khung trên trang chủ |
| `sort_order` | INT | Thứ tự khung |

**Logic chính:**
- 4 dòng seed sẵn; API không cho CREATE/DELETE — chỉ UPDATE tiêu đề/is_visible/sort_order.
- Mỗi khung chứa danh sách phần tử `tab_help_home_item` cascade `delete-orphan`.

---

### `tab_help_home_item` — Phần tử trong khung trang chủ

Một phần tử bên trong khung trang chủ Help Center. Loại dữ liệu của phần tử phụ thuộc vào khung cha: khung `quick_start`/`categories` trỏ bài viết; khung `faq` trỏ câu hỏi thường gặp; khung `tips` là thẻ tự do.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `section_id` | BIGINT FK | Trỏ `tab_help_home_section.id` ON DELETE CASCADE |
| `article_id` | BIGINT NULL FK | Trỏ `tab_help_article.id` — dùng khi khung là `quick_start` hoặc `categories` |
| `faq_id` | BIGINT NULL FK | Trỏ `tab_faq.id` — dùng khi khung là `faq` |
| `title` | VARCHAR(150) NULL | Tiêu đề thẻ tự do (khung `tips`) |
| `description` | VARCHAR(500) NULL | Mô tả thẻ tự do (khung `tips`) |
| `icon` | VARCHAR(50) NULL | Slug icon dựng sẵn ở frontend (backend chỉ lưu chuỗi) |
| `background_image` | VARCHAR(500) NULL | Ảnh minh họa góc phải tile — chỉ khung `quick_start` dùng |
| `gradient` | VARCHAR(30) NULL | Slug nền gradient (frontend ánh xạ sang CSS) |
| `sort_order` | INT | Thứ tự phần tử trong khung |

**Logic chính:**
- Ba nhóm cột (article, faq, free-text) đều nullable; service chịu trách nhiệm bắt buộc đúng cột theo `key` của khung cha.
- `faq_id` FK ON DELETE CASCADE — xóa FAQ thì item tự biến.

---

## Cụm E — Câu hỏi thường gặp

### `tab_faq` — Câu hỏi thường gặp

Danh sách câu hỏi thường gặp hiển thị ở trang người dùng của Trung tâm Hướng dẫn. Có thể tắt từng mục mà không cần xóa.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `question` | VARCHAR(500) | Nội dung câu hỏi |
| `answer` | TEXT | Nội dung trả lời |
| `sort_order` | INT | Thứ tự hiển thị |
| `is_active` | BOOLEAN | `False` = ẩn khỏi trang người dùng (vẫn quản lý được qua admin) |

**Logic chính:**
- `tab_help_home_item.faq_id` trỏ vào bảng này — xóa FAQ kéo theo item trên trang chủ (cascade).
- Ẩn bằng `is_active=False` thay vì xóa để giữ lại nội dung cho lần dùng sau.

---

## Cụm F — Trợ lý AI

### `tab_assistant_conversation` — Hội thoại với trợ lý AI

Một cuộc hội thoại của một tài khoản với trợ lý AI. Module mới, lưu kiểu theo R2/QĐ-11 (SMALLINT+IntEnum cho cột phân loại). Danh sách và chi tiết lọc theo chính chủ (`created_by`).

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `title` | VARCHAR(255) | Tiêu đề hội thoại (thường lấy từ câu hỏi đầu tiên) |
| `provider` | VARCHAR(30) | Nhà cung cấp model dùng cho lượt gần nhất (vd `anthropic`) |
| `model` | VARCHAR(80) | Tên model dùng cho lượt gần nhất (vd `claude-sonnet-4-6`) |
| `last_message_at` | DATETIME NULL | Thời điểm tin nhắn cuối (có index — dùng để sắp xếp danh sách) |

**Logic chính:**
- Mỗi hội thoại thuộc về một tài khoản; API không để người khác truy cập hội thoại của người khác.
- `provider` và `model` ghi lại lượt gần nhất để hiển thị lại, không ràng buộc lượt sau phải dùng cùng model.
- Các tin nhắn chi tiết nằm ở `tab_assistant_message`.

---

### `tab_assistant_message` — Tin nhắn trong hội thoại AI

Một lượt tin trong hội thoại. Phân biệt tin người dùng và tin trợ lý qua `role` (SMALLINT+IntEnum). Lưu thông tin token để soi chi phí gọi model.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `conversation_id` | BIGINT | Trỏ `tab_assistant_conversation.id` (index) |
| `role` | SMALLINT | Vai trò: 1=USER (người dùng), 2=ASSISTANT (trợ lý AI) |
| `content` | TEXT | Nội dung tin nhắn |
| `attachments` | TEXT | JSON danh sách file đính kèm lượt hỏi: `[{id, filename, content_type, size}]`; rỗng = không đính kèm; chỉ có ở tin USER |
| `provider` | VARCHAR(30) | Nhà cung cấp model (chỉ có ở tin ASSISTANT) |
| `model` | VARCHAR(80) | Tên model đã dùng (chỉ có ở tin ASSISTANT) |
| `input_tokens` | INT | Số token đầu vào lượt gọi (chỉ có ở tin ASSISTANT) |
| `output_tokens` | INT | Số token đầu ra lượt gọi |
| `thinking_tokens` | INT | Số token suy luận nội bộ (extended thinking) |
| `cache_read_tokens` | INT | Số token đọc từ cache prompt |
| `cache_write_tokens` | INT | Số token ghi vào cache prompt |

**Logic chính:**
- `attachments` lưu "danh thiếp" file (metadata), không lưu nội dung — nội dung thực tế ở `StoredFile`.
- Các cột token chỉ có ý nghĩa ở tin ASSISTANT; tin USER để 0.
- Dữ liệu token dùng để phân tích chi phí, không bắt buộc và không ảnh hưởng đến nghiệp vụ.

---

## Cụm G — Thông báo và hộp thư

### `tab_notification` — Thông báo trong ứng dụng (chuông)

Thông báo in-app cho một người dùng cụ thể. Đây là kênh chuông — hoàn toàn tách biệt với email.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `user_id` | BIGINT NULL | Trỏ `tab_user.id` (người nhận thông báo, có index) |
| `title` | VARCHAR(255) | Tiêu đề thông báo (vd mã phiếu + hành động) |
| `body` | TEXT | Nội dung chi tiết thông báo |
| `link` | VARCHAR(500) NULL | Đường dẫn tương đối tới chứng từ liên quan |
| `is_read` | BOOLEAN | `False` = chưa đọc; `True` = đã đọc |

**Logic chính:**
- `trigger_notification()` tạo một dòng riêng cho mỗi người nhận — không gộp.
- Sau khi tạo chuông, hàm tiếp tục đẩy Web Push (best-effort, chạy nền) tới thiết bị đăng ký của từng người nhận.
- Định tuyến người nhận theo sự kiện: `pr_submitted`/`sr_submitted` → trưởng phòng + vai trò `dept_head` cùng phòng; `pay_submitted`/`po_submitted` → người có quyền duyệt entity tương ứng; `pr_approved` → người tạo + `pur_admin`; các sự kiện còn lại → người tạo phiếu.
- Email workflow chỉ gửi khi `EMAIL_WORKFLOW_ENABLED=true` (chủ yếu dev/UAT); kênh chuông luôn kích hoạt.

---

### `tab_email_log` — Nhật ký email đã gửi

Ghi lại mọi email được hệ thống tạo ra, kèm trạng thái gửi. Cũng lưu địa chỉ thực tế đã gửi (`from_email`) ngay cả khi hộp thư về sau thay đổi.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `event` | VARCHAR(100) | Tên sự kiện kích hoạt (vd `workflow_purchase_request`, `account_creation`, `password_reset`) |
| `to_email` | VARCHAR(255) | Địa chỉ nhận (có thể là địa chỉ test override) |
| `subject` | VARCHAR(255) | Tiêu đề email |
| `status` | VARCHAR(20) | Trạng thái: `pending` (chưa gửi), `sent` (đã gửi), `failed` (lỗi), `disabled` (bị chặn bởi cấu hình) |
| `error` | TEXT NULL | Thông báo lỗi nếu `status=failed` hoặc `status=disabled` |
| `sent_at` | DATETIME NULL | Thời điểm gửi thành công |
| `mailbox_id` | BIGINT NULL | ID hộp thư đã gửi (index); rỗng = dùng SMTP dùng chung |
| `from_email` | VARCHAR(255) | Địa chỉ người gửi thực tế đã dùng (ghi lại sau khi gửi xong) |

**Logic chính:**
- `from_email` ghi lại địa chỉ đã gửi chứ không chỉ trỏ khóa ngoại — hộp thư đổi địa chỉ hay bị xóa thì nhật ký vẫn đúng.
- `status=disabled` xảy ra khi `EMAIL_HARD_OFF=true` (chặn cứng theo môi trường) hoặc `email_enabled=false` (công tắc cấu hình) và email không thuộc loại `force=True`.
- Email thiết yếu (`password_reset`) gửi với `force=True`, bỏ qua công tắc `email_enabled` nhưng vẫn bị `EMAIL_HARD_OFF` chặn.
- Gửi nền qua `BackgroundTasks` để không chặn luồng xử lý chính.

---

### `tab_mailbox` — Hộp thư gửi danh nghĩa

Một địa chỉ email danh nghĩa với bộ SMTP riêng của nó. Cho phép nhân sự gửi thư đại diện địa chỉ phòng ban (vd `hr@gmail.com`) thay vì địa chỉ cá nhân, mà người nhận thực sự thấy đúng địa chỉ danh nghĩa đó.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `code` | VARCHAR(30) UNIQUE | Mã hộp thư |
| `name` | VARCHAR(200) | Tên hộp thư (vd "Phòng Hành chính") |
| `email` | VARCHAR(255) UNIQUE | Địa chỉ email danh nghĩa — phải là unique vì hai hộp cùng địa chỉ khác mật khẩu gây nhầm lẫn |
| `display_name` | VARCHAR(200) | Tên hiển thị trước địa chỉ: `Phòng Hành chính <hr@gmail.com>`; rỗng thì dùng `name` |
| `smtp_host` | VARCHAR(200) | Máy chủ SMTP của hộp thư |
| `smtp_port` | INT | Cổng SMTP (mặc định 587) |
| `smtp_user` | VARCHAR(255) | Tài khoản đăng nhập SMTP |
| `smtp_password_enc` | TEXT | Mật khẩu ứng dụng mã hóa Fernet (khóa suy từ `JWT_SECRET`); API không bao giờ trả giá trị này |
| `use_tls` | BOOLEAN | Có dùng STARTTLS không (mặc định `True`) |
| `company_id` | BIGINT NULL | Giới hạn hộp thư trong một pháp nhân; NULL = dùng được ở mọi pháp nhân |
| `note` | TEXT | Ghi chú nội bộ |
| `is_active` | BOOLEAN | Hộp thư đang dùng được không |

Index: `(is_active, company_id)` để lọc hộp thư còn dùng theo pháp nhân.

**Logic chính:**
- Mỗi hộp thư giữ SMTP riêng — đăng nhập đúng hộp thư đó chứ không chỉ đổi header `From` (Gmail ghi đè `From` nếu chỉ đổi header).
- `smtp_password_enc` mã hóa Fernet, cùng khóa với `app_settings`; API chỉ trả cờ "đã cấu hình hay chưa".
- `company_id` là bộ lọc hiển thị trên màn chọn, không phải chốt quyền — quyền gửi chốt ở `tab_mailbox_member`.
- Khi hộp thư bị xóa hoặc `is_active=False`, `service.py` fallback về SMTP dùng chung thay vì để thư nằm chết.

---

### `tab_mailbox_member` — Nhân sự được gửi danh nghĩa hộp thư

Khai đích danh từng nhân sự được phép gửi thư dưới danh nghĩa một hộp thư. Đây là câu trả lời kiểm toán "vì sao người A gửi được thư của địa chỉ B".

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `mailbox_id` | BIGINT | Trỏ `tab_mailbox.id` (index) |
| `employee_id` | BIGINT | Trỏ `tab_employee.id` — ID nhân sự, không phải user_id |

Ràng buộc: `UNIQUE(mailbox_id, employee_id)`.

**Logic chính:**
- Khai đích danh từng người, không suy theo phòng ban hay vai trò — quyền gửi thư danh nghĩa cả công ty phải chỉ mặt đặt tên.
- `employee_id` là ID nhân sự; khi xác thực, service tra `tab_user.employee_id` để tìm tài khoản tương ứng.

---

## Cụm H — Đặt xe

### `tab_vehicle` — Xe

Danh mục xe nội bộ và xe thuê ngoài.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `license_plate` | VARCHAR(50) UNIQUE | Biển số xe |
| `model` | VARCHAR(100) | Hiệu xe / model |
| `type` | VARCHAR(50) | Loại xe (nhãn văn bản) |
| `capacity` | INT | Sức chứa (số chỗ ngồi, mặc định 4) |
| `status` | VARCHAR(30) | Trạng thái: `available` (sẵn sàng), `on_trip` (đang chạy), `maintenance` (bảo dưỡng) |
| `is_external` | BOOLEAN | `True` = xe thuê ngoài |
| `external_company` | VARCHAR(255) | Tên công ty cung cấp xe thuê (khi `is_external=True`) |

**Logic chính:**
- Trạng thái là mã chuỗi tiếng Anh — module tạo trước R2/QĐ-11.
- Khi phân công xe cho yêu cầu, `status` cần được cập nhật đồng bộ.

---

### `tab_driver` — Tài xế

Danh mục tài xế nội bộ và tài xế thuê ngoài.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `user_id` | BIGINT NULL | Trỏ `tab_user.id` (liên kết tài khoản nội bộ nếu có) |
| `name` | VARCHAR(255) | Họ tên tài xế |
| `phone` | VARCHAR(20) | Số điện thoại |
| `license_number` | VARCHAR(50) | Số bằng lái |
| `status` | VARCHAR(30) | Trạng thái: `available` (sẵn sàng) và các trạng thái khác theo nghiệp vụ |
| `is_external` | BOOLEAN | `True` = tài xế thuê ngoài |
| `external_company` | VARCHAR(255) | Tên công ty cung cấp tài xế thuê (khi `is_external=True`) |

**Logic chính:**
- `user_id` nullable — tài xế thuê ngoài không có tài khoản hệ thống.
- Tài xế nội bộ liên kết qua `user_id` để nhận thông báo và cập nhật trạng thái chuyến.

---

### `tab_vehicle_booking` — Yêu cầu đặt xe

Một yêu cầu đặt xe của nhân viên. Ghi lại thông tin chuyến đi, người yêu cầu, thông tin phân công xe/tài xế sau khi được duyệt.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `code` | VARCHAR(50) UNIQUE | Mã yêu cầu tự sinh |
| `purpose` | TEXT | Mục đích chuyến đi |
| `start_location` | VARCHAR(255) | Điểm đón |
| `end_location` | VARCHAR(255) | Điểm đến |
| `start_time` | VARCHAR(20) | Thời gian khởi hành (ISO string) |
| `end_time` | VARCHAR(20) | Thời gian dự kiến về (ISO string) |
| `passenger_count` | INT | Số hành khách |
| `attendees` | TEXT | Danh sách người đi cùng (văn bản tự do) |
| `contact_phone` | VARCHAR(20) | Số điện thoại liên lạc |
| `is_round_trip` | BOOLEAN | Có về không (khứ hồi) |
| `requester` | VARCHAR(255) | Tên người yêu cầu (lưu đóng băng) |
| `requester_id` | BIGINT | ID nhân sự người yêu cầu (employee_id, có index) |
| `department_id` | BIGINT | ID phòng ban |
| `company_id` | BIGINT | ID pháp nhân (có index) |
| `first_approver_id` | BIGINT | ID người duyệt đầu tiên |
| `status` | VARCHAR(30) | Trạng thái: `draft`, `submitted`, `approved`, `rejected`, `cancelled`, `dispatched`, `completed`, v.v. |
| `note` | TEXT | Ghi chú |
| `assigned_vehicle_id` | BIGINT NULL | Trỏ `tab_vehicle.id` (phân công sau khi duyệt) |
| `assigned_driver_id` | BIGINT NULL | Trỏ `tab_driver.id` (phân công sau khi duyệt) |
| `dispatched_by` | BIGINT NULL | `user_id` người điều phối xe |
| `dispatched_at` | VARCHAR(20) | Thời điểm điều phối (ISO string) |
| `driver_status` | VARCHAR(30) | Phản hồi của tài xế: `ACCEPTED` (chấp nhận), `REJECTED` (từ chối), `COMPLETED` (hoàn thành); rỗng = chưa phản hồi |
| `is_deleted` | BOOLEAN | Soft delete |

Index: `(created_by)` cho phạm vi của người tạo.

**Logic chính:**
- `requester_id` là employee_id (không phải user_id) — theo quy ước `assignee_id` của các chứng từ thu mua.
- `requester` lưu đóng băng tên người yêu cầu tại thời điểm tạo.
- `start_time`/`end_time`/`dispatched_at` lưu ISO string thay vì DATETIME — chú ý khi query theo khoảng thời gian.
- `is_deleted=True` là soft delete — lọc theo cờ này trong mọi câu query danh sách.

---

## Quan hệ trong cụm

```
tab_forum_board ──< tab_forum_board            (parent_id — nhóm chứa box, đúng 2 tầng)
tab_forum_board ──< tab_forum_post             (board_id NULL = bài feed thuần)
tab_forum_post ──< tab_forum_reaction          (post_id)
tab_forum_post ──< tab_forum_moderation_log    (post_id)
tab_forum_post ──< tab_comment [entity='forum_post'] (entity_id)

tab_comment ──< tab_comment_mention            (comment_id)
tab_comment ──< tab_comment_reaction           (comment_id)
tab_comment ──< tab_comment [parent_id]        (tự tham chiếu, tối đa 2 cấp)

tab_ticket ──< tab_ticket_message              (ticket_id)

tab_help_article ──< tab_help_article_slide    (article_id, CASCADE)
tab_help_article ──< tab_help_article [parent_id] (tự tham chiếu — cây thư mục)
tab_help_article ──< tab_help_home_item        (article_id, CASCADE)

tab_help_home_section ──< tab_help_home_item   (section_id, CASCADE)
tab_faq ──< tab_help_home_item                 (faq_id, CASCADE)

tab_assistant_conversation ──< tab_assistant_message (conversation_id)

tab_mailbox ──< tab_mailbox_member             (mailbox_id)
tab_mailbox ─── tab_email_log                  (mailbox_id — nullable, không FK cứng)

tab_vehicle ─── tab_vehicle_booking            (assigned_vehicle_id — nullable)
tab_driver  ─── tab_vehicle_booking            (assigned_driver_id — nullable)

tab_notification ─── tab_user                  (user_id — người nhận)
tab_email_log    ─── tab_user                  (created_by — người kích hoạt)
```

Ghi chú quan hệ liên cụm:
- `tab_comment` nối với mọi loại chứng từ qua cặp `(entity, entity_id)` — không có FK cứng; `comment_registry.py` là nguồn kiểm soát entity hợp lệ.
- `tab_email_log.mailbox_id` không có FK cứng vào `tab_mailbox` — cố ý để nhật ký không bị cascade xóa khi hộp thư bị gỡ.
- `tab_forum_post.dept_id` và `company_id` không có FK cứng — dữ liệu đóng băng tại thời điểm đăng, phòng ban/pháp nhân có thể đổi tên sau.
