# DIỄN ĐÀN — LỘ TRÌNH PHASE

Ngày lập: 26/08/2026. Chia việc của [`00`](./00-pham-vi-va-ke-hoach.md) mục 5 thành các phase làm được. **Không có mốc thời gian** (QĐ-D5 — làm từ từ, song song việc khác); thứ tự và điều kiện chuyển phase mới là thứ quan trọng. Thiết kế chi tiết từng phần ở [`01`](./01-giao-dien-va-logic-hien-thi.md).

Nguyên tắc chia: **mỗi phase kết thúc là hệ vẫn nguyên vẹn** — dừng giữa chừng bao lâu cũng được, không để bảng mồ côi hay màn hình gọi API chưa tồn tại.

---

## Sơ đồ phụ thuộc

```
F0 nền dữ liệu ──> F1 API bài viết ──> F2 khung FE + feed đọc ──> F3 đăng bài + trang cá nhân
                                                                        │
                                              F4 tương tác (like+comment+chuông) <──┘
                                                                        │
                                                    F5 quản trị ẩn/xóa ─┘──> F6 deploy chạy thử
                                                                                  │
                                     (đợt 2) F7 Help Center tab · F8 duyệt bài · F9 ghim + tìm kiếm
```

F0–F1 là backend thuần, F2–F3 là FE thuần — **hai người làm song song được** từ khi F1 chốt hợp đồng API (viết schema Pydantic xong là FE dựng theo được, không cần chờ service xong).

---

## Đợt 1 — MVP

### F0 — Nền dữ liệu và quyền — **XONG 27/08/2026**

- Bảng `tab_forum_post` (audience + dept/company đóng băng, `status` SMALLINT + IntEnum chừa `pending_review` theo QĐ-D2), `tab_forum_reaction`, `tab_forum_moderation_log`. Migration + khai `all_models.py`.
- Entity `forum_post` vào `ENTITIES` + `SCOPE_FIELDS` (sentinel PUBLIC — quyền xem đi theo luật audience riêng, không theo scope RBAC) + `FILE_POLICY` (chỉ đuôi ảnh, 10MB, 10 tấm).
- Vai trò `forum_admin` trong seed (khuôn `help_admin`); quyền không ghi đè trên prod theo luật seed_prod.
- **Điều kiện đủ:** `alembic heads` một đầu; test backend cho enum trạng thái + ràng buộc unique like + FILE_POLICY.

### F1 — API bài viết — **XONG 27/08/2026**

- CRUD bài: đăng (kèm `file_ids` khuôn tải-trước-gắn-sau), xóa bài của mình, đọc một bài, **feed con trỏ `before_id` + WHERE audience** (mục 4.2–4.3 của `01`), feed trang cá nhân.
- Bộ query gom theo trang: tác giả, số like, đã-like-chưa, số comment, ảnh — mỗi loại 1 query/trang.
- Mở comment: thêm `forum_post` vào `comment_registry` + nhánh `resolve_doc()` kiểm theo audience (chỗ duy nhất phải viết thêm của phần comment).
- **Điều kiện đủ:** test backend — người phòng khác không thấy bài `dept`, người công ty khác không thấy bài `company`, tác giả luôn thấy bài mình, con trỏ không lặp/không sót khi có bài chen giữa, comment vào bài không được xem bị 403.

#### Hợp đồng API F1 (chốt 27/08/2026 — FE dựng F2 theo đây, không chờ service)

Mọi endpoint đều đòi **đăng nhập** (Bearer), KHÔNG đòi grant RBAC — ai thấy bài nào đi theo
luật audience mục 4.2 của `01`. Phong bì chuẩn `{success, message, data}`.

| Endpoint | Vào | Ra (`data`) |
|---|---|---|
| `GET /api/forum/posts?limit=20&before_id=0` | con trỏ `before_id` = id nhỏ nhất đang hiện (0 = trang đầu) | `{items: [PostOut...] mới → cũ, next_before_id, has_more}` |
| `GET /api/forum/users/{user_id}/posts?limit&before_id` | feed trang cá nhân; xem trang CHÍNH MÌNH thấy cả bài bị ẩn | như trên |
| `GET /api/forum/posts/{id}` | | `PostOut` — 403 nếu ngoài đối tượng xem |
| `POST /api/forum/posts` | `{body, audience, file_ids}` — `audience` 1=phòng ban 2=công ty 3=toàn tập đoàn; ảnh tải trước qua `POST /api/attachments/upload-file` (entity=`forum_post`) lấy `file_ids` | `PostOut` (201) |
| `DELETE /api/forum/posts/{id}` | chỉ tác giả (admin ẩn/xóa là F5, đường khác) | `null` |
| `POST /api/forum/posts/{id}/like` | bấm thích/bỏ thích | `{liked, count}` |
| `GET /api/forum/posts/{id}/likes` | ai đã thích | `[{user_id, name}]` |

`PostOut` = `{id, body, status, audience, dept_id, company_id, author_id, author_name,
author_code, author_avatar, created_at, can_delete, like_count, liked, comment_count,
images: [{link_id, file_id, filename, url, content_type, size}]}`.

Ràng buộc tầng service: chữ tối đa **10.000 ký tự**, tối đa **10 tệp media/bài** — ảnh +
video `mp4`/`webm`, mỗi tệp **50MB** theo `FILE_POLICY` (D-Q3 chốt 27/08/2026; bản F1 gốc
là "chỉ ảnh, 10MB"), bài rỗng (không chữ không ảnh) bị 400; chọn `audience` phòng ban/công ty
mà hồ sơ nhân sự chưa gắn phòng/pháp nhân cũng 400 — không đoán, bắt sửa dữ liệu nhân sự.
Comment dùng nguyên bộ `/api/comments` với `entity=forum_post`.

### F2 — Khung FE + feed đọc — **XONG 27/08/2026**

- Dựng **phân hệ `forum` trong `frontend-v2`** (QĐ-D6 — không còn app riêng): thêm dòng vào `module-registry`, route gốc `/forum`, **layout riêng một cột** (mục 1 của `01`), lazy-load, tab shell + responsive điện thoại trong shell ERP.
- Feed đọc: `useInfiniteQuery` cuộn vô hạn, thẻ bài (ảnh lưới + đèn chiếu + "Xem thêm"), nút "Có bài viết mới", trang `/forum/posts/:id`.
- **Điều kiện đủ:** đăng nhập bằng tài khoản thật ở local (cổng 8083), lướt được feed dữ liệu mẫu cả desktop lẫn devtools mobile; `npm run check` xanh.

### F3 — Đăng bài + trang cá nhân — **XONG 27/08/2026**

- Hộp thoại đăng bài: chữ + ảnh (kéo thả/dán, tải-trước-gắn-sau) + chọn đối tượng xem (nhớ lựa chọn trước); xóa bài của mình.
- Trang cá nhân `/forum/me`, `/forum/users/:id` — đầu trang hồ sơ + feed lọc tác giả.
- **Điều kiện đủ:** đăng bài 10 ảnh từ điện thoại (qua devtools mobile) trơn tru; bài `dept` không hiện với tài khoản phòng khác trên UI.

### F4 — Tương tác — **XONG 27/08/2026**

- Like bài (không chuông), khối comment nhúng (component mới trên FE diễn đàn, gọi bộ API `/api/comments` sẵn có), chuông "bình luận mới trong bài của bạn" + web push.
- **Điều kiện đủ:** hai tài khoản comment qua lại nhận chuông đúng luật (không tự báo mình, nhắc tên chỉ một chuông).

### F5 — Quản trị — **XONG 27/08/2026**

- `forum_admin` ẩn/xóa bài: **bắt buộc nhập lý do**, ghi `tab_forum_moderation_log`, bắn chuông cho tác giả kèm lý do (QĐ-D1). Khôi phục bài ẩn. Tác giả xem bài ẩn của mình kèm nhãn lý do.
- **Điều kiện đủ:** test — ẩn không lý do bị 400; tác giả nhận đúng một chuông; bài ẩn biến khỏi feed mọi người nhưng còn ở trang cá nhân tác giả và mắt admin.

### F6 — Deploy chạy thử

- **Không còn hạ tầng mới** (QĐ-D6 — hết Dockerfile/nginx/domain/tunnel riêng, D-Q1 giải thể): diễn đàn lên theo nhịp deploy ERP dev sẵn có (build lại ảnh + migration). Bật trước cho **một nhóm nhỏ** (IT + HR) dùng thử một thời gian rồi mới thông báo toàn công ty; lên prod thì đi cùng đợt bật service `erp` trên prod.
- **Điều kiện đủ:** nhóm thử đăng bài thật từ điện thoại qua domain ERP; backup R2 đã phủ bảng mới.

---

## Đợt 2 — sau khi MVP sống

| Phase | Nội dung | Ghi chú |
|---|---|---|
| F7 | Help Center thành tab **Hướng dẫn** (QĐ-D4) | Đọc chung API `help_article`; tab nay nằm trong ERP (QĐ-D6) — đích redirect của domain help cũ chốt khi làm F7 |
| F8 | Bật cơ chế **duyệt bài** khi sếp cần (QĐ-D2) | Chỉ là config + màn hàng chờ — dữ liệu đã chừa sẵn từ F0 |
| F9 | **Ghim bài** (rail phải/đầu feed) · **tìm kiếm** bài viết · **sửa bài** kèm nhãn "đã chỉnh sửa" | |
| F11 | **Cho người đăng tự chọn bố cục ảnh** kiểu Facebook/Instagram (sếp gợi ý 27/08/2026 — mới là ý tưởng, CHƯA chốt làm) | Hiện lưới tự xếp theo số ảnh (1 nguyên khổ · 2 chia đôi · 3 = 1 ngang + 2 vuông · 4+ ô 2x2 đè «+N») — đã là khuôn Facebook. Muốn cho tự chọn thì thêm cột `layout` SMALLINT+IntEnum trên bài + ô chọn bố cục trong hộp đăng bài + nhánh vẽ theo `layout` ở `post-image-grid.tsx`; dữ liệu cũ `layout=0` = tự xếp như nay |
| F10 — **XONG 27/08/2026** (làm sớm theo lệnh sếp, trước F4) | **Bài tự động theo sự kiện**: đổi avatar (cả hai cửa — thẻ danh tính `/me` VÀ menu tài khoản mọi màn hình) → hộp thoại "Đăng lên diễn đàn?" kèm caption + đối tượng xem (nhớ lựa chọn trước), "Để sau" là thôi — hỏi chứ không ép. Bài đăng mang `kind=AVATAR_UPDATE`, thẻ bài vẽ dòng hệ thống "đã cập nhật ảnh đại diện" cạnh tên | Cột `kind` SMALLINT+IntEnum (0=thường, 1=avatar), migration `7889a09c627e`; service ép AVATAR_UPDATE đúng 1 ảnh + caption được phép trống; FE: `avatar-post-dialog.tsx` (tải LẠI tệp avatar lên kho đính kèm diễn đàn — hai kho khác nhau, không mượn chéo); khuôn mở rộng sau cho thăng chức/sinh nhật/nhân sự mới = thêm giá trị enum |

Đợt 3 (follow/feed cá nhân hóa, nhóm kín, khảo sát trong bài) giữ nguyên như `00` mục 5 — chỉ bàn khi đợt 2 xong và sếp còn muốn. Riêng **video** vốn nằm đợt 3 đã kéo lên làm xong 27/08/2026 (D-Q3).

---

## Việc bắt đầu được ngay, không chờ ai

1. F0 nguyên phần dữ liệu — không đụng câu hỏi mở nào.
2. Chốt hợp đồng API của F1 (schema vào/ra) để người làm FE khởi động F2 song song.
3. ~~Hỏi sếp câu **D-Q2 — ai làm forum_admin**~~ — **đã chốt 27/08/2026**: không có cơ chế riêng, `forum_admin` chính là VAI TRÒ RBAC seed sẵn từ F0; ai được gán vai trò đó qua màn phân quyền sẵn có thì là quản trị diễn đàn. (D-Q1 tên domain đã giải thể theo QĐ-D6.)

## Nhật ký

| Ngày | Nội dung |
|---|---|
| 26/08/2026 | Lập tài liệu — chia 6 phase đợt 1 + 3 phase đợt 2, điều kiện đủ từng phase |
| 27/08/2026 | **F0 xong**: module `backend/app/modules/forum/` (3 bảng + 3 IntEnum), migration `9eba2501f2c4` (một head), entity `forum_post` vào ENTITIES (45) + SCOPE_FIELDS (PUBLIC) + FILE_POLICY (`__self__`, chỉ ảnh, 10MB), vai trò `forum_admin` trong STD_ROLES (loại `forum_post` khỏi quyền tự động của `pur_manager`), test `test_forum.py` + cập nhật `test_pham_vi_khai_du_b07.py` 44 → 45 |
| 27/08/2026 | **Chốt hợp đồng API F1** (bảng ở trên) trước khi viết service — FE bắt đầu F2 song song được từ đây |
| 27/08/2026 | **F1 xong**: `forum/schema.py + service.py + controller.py` (prefix `/api/forum`, nối `main.py`), luật audience `can_view`/`_visible_cond` (thiếu phòng/pháp nhân thì CHẶN, khuôn B-07), 4 map gom theo trang (tác giả/like/số comment/ảnh), mở comment (`comment_registry` + nhánh `resolve_doc` kiểm audience), nhánh `_check_forum` + chặn gắn trực tiếp trong `attachment/controller.py`, xóa bài cuốn theo comment + like + ảnh. Test `test_forum_api.py` 13 bài phủ đủ 5 điều kiện đủ; bộ comment/đính kèm cũ 62 bài vẫn xanh |
| 27/08/2026 | **QĐ-D6 — gộp vào ERP v2**: F2 thành phân hệ `forum` trong `frontend-v2` (route gốc `/forum`), F6 gọn lại không còn hạ tầng riêng, D-Q1 giải thể. Backend F0/F1 và hợp đồng API F1 không đổi |
| 27/08/2026 | **F2 xong**: phân hệ `frontend-v2/src/modules/forum/` (layout một cột `customLayout: true` — cờ mới trong `module-definition.ts`, registry tách `moduleRoutes`/`customModuleRoutes`, gắn thẳng dưới `ProtectedRoute`); feed `useInfiniteQuery` con trỏ `before_id` + lính canh IntersectionObserver, thẻ bài (lưới ảnh + đèn chiếu + "Xem thêm"), nút "Có bài viết mới" (poll 45s khóa `feedHead` riêng), trang `/forum/posts/:id` (403/404 quy về một câu chung); `formatRelativeTime` vào `shared/utils/format-date.ts`, `/forum` vào `V2_PREFIXES` của notification-link. `npm run check` xanh (791 test); duyệt thật ở local 8083 tài khoản TESTREQ cả desktop lẫn mobile 375px (13 bài mẫu tạo qua đúng đường API F1: login → upload-file → đăng bài) |
| 27/08/2026 | **Chốt D-Q2**: `forum_admin` = vai trò RBAC seed sẵn (F0), gán qua màn phân quyền sẵn có — không cần cơ chế riêng. Câu hỏi mở giải thể |
| 27/08/2026 | **F3 xong**: hộp thoại đăng bài (`post-composer-dialog` — chữ + ảnh kéo thả/dán/chọn tệp, tải-trước-gắn-sau qua `uploadForumImages`, đếm ký tự gần trần 10.000, lọc tệp `pick-image-files` gom lỗi thành toast tiếng Việt), nhớ đối tượng xem lần trước (`last-audience` localStorage), xóa bài của mình (`post-actions-menu` — menu ba chấm theo `can_delete` + AlertDialog xác nhận), trang cá nhân `/forum/me` + `/forum/users/:id` dùng chung `forum-profile-page` (đầu trang: chính mình lấy auth store, người khác lấy từ bài đầu hoặc state của link nên mở tức thì), reset query `feed` + `userPostsAll` sau đăng/xóa. `npm run check` xanh (122 tệp / 801 test). Duyệt thật local 8083: đăng chữ + đăng 3 ảnh desktop, đăng 10 ảnh viewport mobile 375px không tràn ngang (điều kiện đủ 1), xóa bài chạy đúng, bài `dept` của TESTREQ (phòng 21) KHÔNG hiện với DEMO_STAFF phòng 14 (điều kiện đủ 2 — lưu ý DEMOTP/DEMOTP2/DEMONV cùng phòng 21 với TESTREQ trên DB local nên không dùng kiểm được) |
| 27/08/2026 | Sếp gợi ý **bài tự động theo sự kiện** (đổi avatar kèm caption, kiểu Facebook) — ghi thành **F10** đợt 2, có hỏi trước khi đăng, không ép |
| 27/08/2026 | **F10 xong** (kéo lên làm trước F4 theo lệnh sếp): backend thêm `ForumPostKind` + cột `kind` (`model/schema/service/controller`, migration `7889a09c627e` — autogenerate lôi drift ~20 bảng cũ kèm cả một lệnh drop cột thật của `tab_survey_product_line`, đã cắt sạch chỉ giữ `add_column kind`); service ép AVATAR_UPDATE đúng 1 ảnh (0 hay 2 đều 400), caption trống hợp lệ, kind lạ 400 — `test_forum_api.py` lên 16 bài. FE: `FORUM_POST_KIND` + `kind` vào types, `avatar-post-dialog.tsx` (xem trước ảnh tròn + caption + đối tượng xem nhớ lần trước, "Để sau"/"Đăng"), gắn vào **cả hai cửa đổi avatar**: `profile-identity-card.tsx` (`/me`) và `user-menu.tsx` (menu tài khoản mọi màn hình — cửa hay dùng nhất, suýt sót); `post-card.tsx` vẽ dòng "đã cập nhật ảnh đại diện" khi `kind=1` + test `post-card.test.tsx`. `npm run check` xanh (123 tệp / 803 test). Duyệt thật local 8083: đổi avatar cả hai cửa đều bật hộp thoại, đăng kèm caption lên feed đúng dạng (dòng hệ thống + caption + ảnh + Công ty), "Để sau" đóng không đăng gì |
| 27/08/2026 | **F4 xong**: like bài — `toggleForumPostLike`/`fetchForumPostLikes` vào `forum-api.ts`, hook `use-toggle-post-like` **vá thẳng cache** (`setQueryData` bài lẻ + `setQueriesData` cả hai infinite cache `feed`/`userPostsAll` — một bài hiện ở 3 chỗ, refetch cả ba mỗi cú bấm là giật cuộn nên KHÔNG invalidate), hộp "Người đã thích" (`post-likes-dialog` + `use-post-likes`, chỉ nạp khi mở), footer `post-card.tsx` thành hàng đếm + hai nút Thích/Bình luận kiểu Facebook; like KHÔNG chuông đúng D-Q6. Khối bình luận nhúng `post-comments.tsx` chạy trên bộ máy `/api/comments` sẵn có (`entity=forum_post`) với `forum-comment-api.ts` **khai lại type trong module forum** (luật cấm import chéo từ `modules/procurement`): bong bóng kiểu Facebook, nhắc tên qua `MentionInput` dùng chung, phản hồi 2 tầng nạp-khi-mở (state cục bộ), đính kèm ảnh + lightbox, like/xóa bình luận, "Xem N bình luận trước"; tạo/xóa bình luận invalidate cả `comments` lẫn `post` để số đếm trên thẻ bài khớp. Chuông dùng nguyên luật comment cũ, route registry `/forum/posts` đã sửa từ F1 nên link chuông điều hướng thẳng vào bài. `npm run check` xanh (123 tệp / 805 test). **Điều kiện đủ kiểm thật** local 8083 hai tài khoản TESTREQ/DEMOTP trên bài 11: TESTREQ bình luận → hộp chuông của CHÍNH TESTREQ trống (không tự báo mình), DEMOTP (tác giả) nhận đúng MỘT chuông "Bình luận mới" bấm vào ra đúng bài; DEMOTP bình luận nhắc tên TESTREQ → TESTREQ nhận đúng MỘT chuông "Bạn được nhắc tên" (không kèm chuông chung); phản hồi 2 tầng + like bài/bình luận + hộp ai thích đều chạy đúng trên UI |
| 27/08/2026 | **F5 xong**: backend `service.moderate()` bảng chuyển trạng thái `_MOD_TRANSITIONS` (HIDE: published→hidden · RESTORE: hidden→published · REMOVE: published/hidden→removed), **bắt buộc lý do** trừ RESTORE (thiếu là 400), mỗi lần một dòng `tab_forum_moderation_log`, chuông cho tác giả kèm lý do (`_notify_author` — không tự báo mình, bài bị gỡ chuông không có link), map `hidden_reason_map` + cờ `can_moderate`/`hidden_reason` vào `PostOut`; 3 endpoint `hide/restore/remove` (`hide/restore` cần `forum_post.write`, `remove` cần `delete`); tác giả xóa vật lý bài đã REMOVED bị 404 để giữ vết. FE: `post-actions-menu` thêm nhánh quản trị (Ẩn/Khôi phục/Gỡ), `moderate-post-dialog` bắt nhập lý do mới cho bấm, nhãn "đã bị quản trị viên ẩn + lý do" trên thẻ bài, hook `use-moderate-forum-post` reset feed/trang cá nhân. `test_forum_api.py` lên 21 bài, `npm run check` xanh (123 tệp / 812 test). **Điều kiện đủ kiểm thật** local hai tài khoản (DEMOTP được gán `forum_admin` qua màn phân quyền): ẩn không lý do bị chặn ngay ở nút; ẩn bài 18 của TESTREQ → TESTREQ nhận đúng MỘT chuông kèm lý do, bài biến khỏi feed DEMONV nhưng còn ở trang cá nhân TESTREQ (kèm nhãn) và mắt admin; khôi phục qua UI về published |
| 27/08/2026 | **Chốt D-Q3 — cho video**: `FILE_POLICY` forum_post thành ảnh + `mp4`/`webm`, trần 10MB → **50MB/tệp** (trần chung, vẫn 10 tệp/bài). FE đổi `pick-image-files` → `pick-media-files` (`isVideoMedia` nhận diện theo content-type trước, đuôi tệp sau), hộp đăng bài nhận video (xem trước ô vuông câm), `post-image-grid` tách video đứng riêng dưới lưới ảnh nguyên khổ ngang + nút phát trình duyệt (không nhét vào lưới vì ô vuông cắt khung hình, đèn chiếu chỉ chiếu ảnh) |
| 27/08/2026 | **3 bài mẫu Hà Giang** đăng trên local qua đúng đường API (login → upload → đăng): bài 19 DEMOTP (đề xuất team-building Mã Pí Lèng — 1 video flycam + 2 ảnh), bài 20 TESTREQ (mùa tam giác mạch + Sủng Là, 4 ảnh), bài 23 DEMONV (Lũng Cú + hẻm Tu Sản, 2 ảnh). Media lấy từ Pexels (giấy phép miễn phí thương mại); video HD 16.8MB đi lọt cổng 50MB — chứng minh luôn đường mp4 mới chạy thật. Sếp gợi ý **cho người đăng tự chọn bố cục ảnh** kiểu Facebook/Instagram → ghi thành **F11** đợt 2 (chưa chốt làm) |
| 27/08/2026 | **Thumbnail sinh lúc upload** (sếp phát hiện feed kéo ảnh full-size + avatar nhòe vì không có CDN resize): `core/images.py` (`make_thumb` — Pillow sẵn trong ảnh api, EXIF transpose, nền trắng cho PNG trong suốt, bỏ qua khi nén không nhẹ hơn; GIF cố ý đứng ngoài kẻo mất chuyển động), cột `thumb_key`/`thumb_url` vào `tab_file` (migration tay `c3d9e14a58b7`, rỗng = FE fallback `url`), upload sinh bản `{file_key}.thumb.jpg` cạnh 1280 (avatar 320 — `set_user_avatar`), `User.avatar` ưu tiên thumb, xóa file dọn cả thumb. FE: `thumb_url` vào `ForumImage`/`ForumUploadedFile`, lưới feed + ô xem trước composer đọc thumb, đèn chiếu vẫn bản gốc. **Bẫy đã dính:** boto3 `upload_fileobj` ĐÓNG fileobj sau khi đẩy → phải sinh thumb TRƯỚC khi upload bản gốc (`make_thumb_for` tách khỏi `attach_thumb`); và uvicorn `--reload` desync bind-mount Windows không nạp code mới — upload đầu ra thumb rỗng, `docker compose restart api` mới ăn. Backfill một lần cho 57 tệp cũ (ảnh diễn đàn + avatar). Test `test_thumbnail.py` 5 bài; `npm run check` xanh (123 tệp / 812 test). Kiểm thật: feed 20/20 ảnh đọc `.thumb.jpg` |
| 27/08/2026 | **Làm mới data mẫu local**: xóa vật lý 17 bài mẫu cũ (giữ bộ Hà Giang 19/20/23) qua `service.delete_post`; đăng 3 bài du lịch mới bằng đúng đường API — bài 24 DEMO_MANAGER_PURCHASE (Đà Lạt, 4 ảnh), bài 25 TESTREQ (Hội An, 3 ảnh), bài 26 DEMONV (Sapa, 3 ảnh — audience 3 vì DEMONV không có pháp nhân), ảnh Pexels; tạo tương tác chéo 4 tài khoản: 15 like bài, 14 bình luận (có 2 tầng phản hồi + 2 nhắc tên `@[id]`), 6 like bình luận. Lưu ý: mật khẩu nhóm `DEMO_*` là `demo123` (không phải = mã như TESTREQ/DEMONV/DEMOTP) |
| 27/08/2026 | **Chi tiết bài viết mở dạng popup** (sếp yêu cầu kiểu Facebook — bấm ra ngoài là đóng, vẫn đứng nguyên vị trí cuộn thay vì mất dấu như khi điều hướng sang trang riêng): `PostDetailDialog` nội bộ trong `post-card.tsx` (bài + toàn bộ bình luận trong dialog cuộn được, tối đa 90svh, tiêu đề "Bài viết của X"); 3 lối vào chi tiết trên thẻ feed (thời gian, số bình luận, nút Bình luận) đổi từ `Link` sang nút mở popup — áp cho cả bảng tin lẫn trang cá nhân vì nằm ngay trong `PostCard`. Thêm prop `flat` cho `PostCard`/`PostComments` (bỏ viền/bóng khi nằm trong dialog); trong popup thao tác xóa/gỡ KHÔNG điều hướng (bài biến khỏi cache là popup tự đóng). Trang riêng `/forum/posts/:id` GIỮ NGUYÊN cho link chia sẻ + thông báo chuông. `post` truyền thẳng từ cache feed nên like/bình luận trong popup cập nhật ngược ra thẻ ngoài ngay. Test `post-card.test.tsx` thêm 2 ca (11 ca xanh); typecheck + lint sạch. Kiểm thật trên local: mở popup giữ nguyên URL `/forum`, đóng bằng click overlay, scrollY giữ nguyên 1200 |
