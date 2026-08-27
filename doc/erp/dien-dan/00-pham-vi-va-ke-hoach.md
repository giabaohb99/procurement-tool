# DIỄN ĐÀN NỘI BỘ — PHẠM VI VÀ KẾ HOẠCH

Ngày lập: 26/08/2026. Trạng thái: **đã chốt phạm vi sơ bộ với sếp, chưa duyệt thiết kế chi tiết, chưa viết dòng mã nào**.

Diễn đàn nội bộ kiểu Facebook cho toàn công ty: đăng bài, comment, like, kèm ảnh, bảng tin chung và trang cá nhân. **Không nằm trong 12 phân hệ WorkHub** (SRS-HOLDING-IT-001-2026) — là sản phẩm mới ngoài lộ trình, chạy song song với các việc đang làm, không chen ưu tiên.

Bộ tài liệu ba tệp: **`00`** (tệp này) — phạm vi, quyết định, câu hỏi mở · [**`01`** Giao diện và logic hiển thị](./01-giao-dien-va-logic-hien-thi.md) — khung màn hình, trang cá nhân, luồng đăng bài, logic feed và comment khi dữ liệu lớn · [**`02`** Lộ trình phase](./02-lo-trinh-phase.md) — 6 phase đợt 1 + 3 phase đợt 2, điều kiện đủ từng phase.

---

## 1. Các quyết định đã chốt (QĐ-D1..D5 ngày 26/08, QĐ-D6 ngày 27/08/2026)

| # | Quyết định | Hệ quả thiết kế |
|---|---|---|
| QĐ-D1 | **Mọi nhân viên đều đăng bài, KHÔNG duyệt trước.** Quản trị viên được ẩn hoặc xóa bài, nhưng **bắt buộc kèm lý do và hệ thống phải thông báo cho tác giả** | Cần bảng nhật ký kiểm duyệt (ai ẩn, lúc nào, lý do gì) + bắn thông báo tự động. Không có đường "ẩn lặng lẽ" |
| QĐ-D2 | **Trước mắt không duyệt bài, nhưng sau này CÓ THỂ cần** | Trạng thái bài viết lưu SMALLINT + IntEnum theo luật R2/QĐ-11 (`published / hidden / removed`...), chừa sẵn giá trị `pending_review`. Bật duyệt sau này = thêm một cấu hình hệ thống, không phải sửa mô hình dữ liệu |
| QĐ-D3 | **Trang cá nhân chỉ hiện bài của chính mình.** Feed chung hiện nhiều bài. **Mỗi bài viết có cấu hình đối tượng xem: phòng ban của mình / công ty (pháp nhân) / public toàn tập đoàn** | Cột `audience` trên bài viết + lọc feed theo phòng ban/pháp nhân của người xem. Khớp khái niệm "đơn vị" của thiết kế đa pháp nhân erp-v2. KHÔNG cần cơ chế follow ở bản đầu |
| QĐ-D4 | **Help Center sau này là một TAB trong diễn đàn** | FE diễn đàn dựng dạng nhiều tab ngay từ đầu (Bảng tin · Hướng dẫn · ...). Trước mắt Help Center giữ nguyên app riêng; khi gộp thì tab Hướng dẫn đọc cùng API `help_article` sẵn có, domain help cũ redirect về |
| QĐ-D5 | **Làm từ từ, song song việc khác** — không mốc ép | Chia đợt nhỏ, mỗi đợt tự chạy được. Không cam kết thời gian, chỉ cam kết thứ tự |
| QĐ-D6 | **Diễn đàn là MỘT PHÂN HỆ trong ERP v2, KHÔNG làm app riêng** *(27/08/2026 — đảo phương án app riêng của bản 26/08)*. Nguyên tắc kèm theo: hệ nội bộ gom hết về một ERP; **chỉ tách app khi có người NGOÀI công ty dùng** (đồng bộ sản phẩm cho đối tác, đơn gia công cho NCC...) | FE = module trong `frontend-v2` (route `/forum`, layout riêng một cột, lazy-load) — mục 2 dưới. F6 deploy gọn lại (không Dockerfile/nginx/domain/tunnel mới), câu hỏi D-Q1 (tên domain) **giải thể**. QĐ-D4 giữ nguyên ý (Hướng dẫn thành tab trong diễn đàn) nhưng tab đó nay nằm trong ERP — đích redirect của domain help cũ bàn lại khi làm F7. Backend F0/F1 không đổi |

## 2. Kiến trúc

**Đảo phương án 27/08/2026 (QĐ-D6):** bản 26/08 chọn app riêng + domain riêng theo khuôn Help Center / Project-M; nay **gộp thẳng vào ERP v2** — tách theo NGƯỜI DÙNG (nội bộ / bên ngoài), không tách theo tính năng.

- **Backend:** module `forum/` trong mã nguồn Thu mua (nhánh `erp-v2`), dùng chung tài khoản, nhân sự, phòng ban, pháp nhân, phân quyền, thông báo, kho tệp R2. *(Không đổi so với bản 26/08 — F0/F1 đã xây đúng chỗ này.)*
- **Frontend:** **phân hệ `forum` trong `frontend-v2`** — thêm một dòng vào `module-registry`, route gốc `/forum`, **layout riêng một cột giữa** (không dùng sidebar nghiệp vụ của ERP — xem `01` mục 1), lazy-load để không nặng bundle các phân hệ khác. Không có Dockerfile / nginx / domain / tunnel mới.
- **Đăng nhập:** dùng ngay phiên ERP đang mở; chuông thông báo dùng chuông ERP sẵn có.

## 3. Dùng lại được gì

| Diễn đàn cần | Đã có trong hệ | Mức dùng lại |
|---|---|---|
| Đăng nhập, phân quyền | Auth + RBAC hai trục | Nguyên vẹn |
| Hồ sơ người đăng, avatar | Hồ sơ nhân sự + `tab_user.avatar_file_id` | Nguyên vẹn |
| Comment 2 cấp | CR-033 (`doc/tai-lieu-chuc-nang/11-binh-luan-tren-chung-tu.md`) | Mô hình + mã bê sang, thêm entity bài viết |
| Up ảnh | `file_registry` + R2, trần dung lượng theo entity | Thêm entity `forum_post` vào FILE_POLICY |
| Thông báo like/comment/bị ẩn bài | 3 kênh: chuông trong app, email, web push | Thêm loại sự kiện mới |
| Lọc ai xem được bài | `apply_scope` + dữ liệu phòng ban/pháp nhân | Dùng dữ liệu tổ chức, logic lọc feed viết mới |

Phải xây mới thật sự: bảng bài viết + feed (phân trang cuộn) + like + nhật ký kiểm duyệt + toàn bộ giao diện.

## 4. Phác mô hình dữ liệu (chưa phải thiết kế cuối)

- `tab_forum_post` — tác giả, nội dung, `audience` (SMALLINT: phòng ban / pháp nhân / public) + tham chiếu phòng ban/pháp nhân, `status` (SMALLINT IntEnum), thời điểm đăng/sửa.
- Ảnh đính kèm — qua FileLink với entity `forum_post` (như chứng từ hiện nay), giới hạn ảnh, trần MB nhỏ (ảnh, không phải file in ấn).
- `tab_forum_reaction` — like theo (bài, người), unique để khỏi like đúp; chừa cột loại reaction nếu sau muốn thêm tim/haha.
- Comment — dùng lại mô hình CR-033 gắn entity `forum_post`.
- `tab_forum_moderation_log` — bài, quản trị viên, hành động (ẩn/xóa/khôi phục), **lý do bắt buộc**, đã thông báo tác giả lúc nào.
- Vai trò mới `forum_admin` (kiểu `help_admin`, `support`): quyền ẩn/xóa bài người khác.

Lưu ý đã biết trước: cột người trên chứng từ hiện là **employee_id chứ không phải user_id** — khi thiết kế bảng forum phải chốt rõ trục tác giả ngay từ đầu, đừng lặp lại sự mơ hồ đó.

## 5. Chia đợt

**Đợt 1 — MVP dùng được:** bảng tin chung + đăng bài kèm ảnh + chọn đối tượng xem (phòng ban / công ty / public) + like + comment + trang cá nhân hiện bài của mình + thông báo khi có tương tác + quản trị ẩn/xóa kèm lý do và thông báo tác giả.

**Đợt 2:** gộp Help Center thành tab Hướng dẫn · bật cơ chế duyệt bài (cấu hình hệ thống) · ghim bài thông báo công ty · tìm kiếm bài viết · sửa bài sau khi đăng (kèm dấu "đã chỉnh sửa").

**Đợt 3 (chỉ làm nếu sếp còn muốn):** follow người/phòng để có feed cá nhân hóa · nhóm kín · khảo sát/bình chọn trong bài · ~~video~~ (video đã kéo lên làm sớm 27/08/2026 — xem D-Q3).

## 6. Câu hỏi còn mở (không chặn đợt 1)

1. ~~D-Q1 — Tên domain?~~ **Giải thể 27/08/2026** theo QĐ-D6 — không còn domain riêng.
2. ~~D-Q2 — Ai giữ vai trò `forum_admin`?~~ **Chốt 27/08/2026**: không có cơ chế riêng — `forum_admin` là vai trò RBAC seed sẵn từ F0, gán cho ai là qua màn phân quyền sẵn có.
3. ~~D-Q3 — Bài viết có cho **video** không?~~ **Chốt 27/08/2026 — CÓ**: nhận thêm `mp4`/`webm`, `FILE_POLICY` nới 10MB → **50MB/tệp** dùng chung ảnh + video, vẫn trần 10 tệp/bài. Định dạng video khác (mov...) vẫn chặn.
4. D-Q4 — Người đăng có được tự xóa/sửa bài của mình không, hay chỉ ẩn?
5. D-Q5 — "Công ty" trong đối tượng xem là pháp nhân theo hồ sơ nhân sự — người thuộc holding thấy gì? Cần chốt khi làm bộ lọc feed.
6. D-Q6 — Like bài có sinh chuông thông báo cho tác giả không? Mặc định đợt 1: **không** (chuông like là chuông ồn nhất — cùng lý do đã chốt ở CR-030); muốn có thì làm chuông gộp "N người đã thích bài của bạn".

## 7. Nhật ký

| Ngày | Nội dung |
|---|---|
| 26/08/2026 | Lập tài liệu. Chốt QĐ-D1..D5 với sếp qua trao đổi |
| 26/08/2026 | Thêm `01` (giao diện + logic hiển thị) và `02` (lộ trình phase); mục 5 "Chia đợt" nay được `02` chi tiết hóa, lệch nhau thì lấy `02` |
| 27/08/2026 | **QĐ-D6 — gộp vào ERP v2, bỏ app riêng + domain riêng** (chốt với sếp sau khi F1 xong). Sửa mục 2 Kiến trúc, giải thể D-Q1; `01` mục 1 và `02` F2/F6 sửa theo. Backend F0/F1 không phải đổi gì |
| 27/08/2026 | Chốt **D-Q2** (forum_admin = vai trò RBAC seed sẵn) và **D-Q3** (cho video mp4/webm, 50MB/tệp — kéo mục "video" của đợt 3 lên làm luôn theo lệnh sếp). Chi tiết ở nhật ký `02` |
