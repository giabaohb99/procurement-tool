# Bình luận (Trao đổi) trên chứng từ

Tài liệu mô tả khối **"Trao đổi"** gắn ở cuối trang chi tiết chứng từ — nơi những người liên quan tới **cùng một phiếu** nói chuyện với nhau ngay trong phiếu, thay vì nhắn Zalo/email rời rạc rồi không ai truy lại được đã chốt gì.

Không phải màn hình riêng, không có mục menu. Đây là một **khối dùng chung** (`components/CommentThread.tsx`) được nhúng vào các trang chi tiết đã có.

> **Khác với Phiếu hỗ trợ (`10-ho-tro-ticket.md`)**: Phiếu hỗ trợ là kênh gửi yêu cầu tới **nhóm Hỗ trợ** và có vòng đời trạng thái riêng. Bình luận ở đây **bám vào chứng từ nghiệp vụ**, không có trạng thái, không giao cho ai — chỉ là dòng trao đổi kèm phiếu.

---

## 1. Có ở những phiếu nào

| Chứng từ | `entity` | Trang |
|---|---|---|
| Yêu cầu mua hàng (YCMH) | `purchase_request` | `/purchase-requests/:id` |
| Yêu cầu báo giá (YCBG) | `survey_request` | `/survey-requests/:id` |
| Phiếu khảo sát | `survey` | `/surveys/:id` |
| Đơn mua hàng (ĐMH) | `purchase_order` | `/purchase-orders/:id` |

**Yêu cầu thanh toán chưa mở** — chốt theo khách, phân hệ này trao đổi qua kế toán bên ngoài hệ thống.

Khối chỉ hiện khi phiếu **đã lưu** (đã có `id`). Ở màn tạo mới (`/…/new`) khối không render — chưa có phiếu thì chưa có gì để bàn.

---

## 2. Người dùng thấy gì

Cuối trang chi tiết là một thẻ **"Trao đổi"** kèm số lượng bình luận (đếm **cả gốc lẫn phản hồi**):

- **Mỗi luồng gốc là một thẻ trắng riêng** (bo góc, viền mảnh) — gốc và toàn bộ phản hồi của nó nằm chung trong thẻ đó, nên nhìn ra ngay đâu là một mạch trao đổi thay vì một danh sách dài dính liền.
- Mỗi bình luận: **ảnh đại diện** (hoặc vòng tròn chữ cái đầu của **tên gọi** — chữ cuối trong họ tên, đúng cách gọi tên tiếng Việt), **họ tên người viết**, **mã nhân sự**, **thời điểm**, nội dung giữ nguyên xuống dòng.
- **Mã nhân sự** (`DEMONV`, `TESTREQ`…) chỉ hiện ở **bình luận gốc** — tên tiếng Việt trùng nhau rất nhiều nên cần mã để biết chắc là ai; nhánh phản hồi bỏ đi cho đỡ rối.
- **Thời điểm hiển thị tương đối**: "Vừa xong", "25 phút trước", "3 giờ trước", "2 ngày trước", "3 tuần trước", "2 tháng trước". Quá **60 ngày** thì đổi sang **ngày tháng** (`12/03/2026`) — đọc "14 tháng trước" không hình dung được gì. Rê chuột lên luôn hiện **mốc giờ đầy đủ** theo giờ Việt Nam.
- Thứ tự mặc định: **cũ ở trên, mới ở dưới** — đọc như một cuộc hội thoại. Nút **"Cũ nhất trước / Mới nhất trước"** ở góc phải tiêu đề để đảo lại; nút "Xem N bình luận trước" cũng tự chuyển xuống đáy cho khớp.
- Ô nhập ở cuối, có **ảnh đại diện của chính mình** bên trái, ô bo tròn tự cao dần theo nội dung + nút **Gửi**. **Ctrl/⌘ + Enter** để gửi nhanh; **Enter** thường là xuống dòng (nội dung trao đổi hay nhiều dòng, gửi nhầm khó chịu hơn là phải bấm thêm phím). **Esc** đóng ô trả lời.
- Nút **thùng rác màu đỏ** nằm **ngay cạnh nút "Phản hồi"** (không đẩy ra mép phải — để gần đúng nội dung mà nó tác động), chỉ hiện trên bình luận **của chính mình**.
- Tối đa **5.000 ký tự** một bình luận; nội dung toàn khoảng trắng bị từ chối.

- Gõ **`@`** giữa câu để nhắc tên ai đó — xem mục 2bb.

Chưa hỗ trợ: sửa bình luận đã gửi, đính kèm file trong bình luận. Đính kèm vẫn dùng khối "Tài liệu đính kèm" sẵn có của phiếu.

---

## 2b. Trả lời — luồng **chỉ 2 cấp** (CR-030)

Mô hình giống YouTube, **không phải** cây lồng nhau vô hạn như diễn đàn:

- **Cấp 1** — bình luận gốc, nằm thẳng trong danh sách.
- **Cấp 2** — phản hồi, thụt vào dưới gốc, gom sau nút **"N phản hồi"** (mặc định **gập lại**).

Bấm **"Phản hồi"** trên **một phản hồi** thì bài viết ra **vẫn ở cấp 2** — nó treo vào chính bình luận gốc và tự gắn **chip `@Tên người vừa được trả lời`** ở đầu nội dung. Nhờ vậy một tranh luận dài không thụt lề mãi sang phải mà vẫn biết ai đang nói với ai.

- Chip `@` nằm **ngay bên trong ô nhập**, trước con trỏ gõ — nhìn là biết bài này gửi cho ai; **xóa đi được** (bấm Backspace, cả cụm mất luôn) nếu chỉ muốn nói chung.
- Ô trả lời chỉ hiện nút **Gửi / Hủy** khi đã gõ chữ, để nhánh phản hồi không bị hai nút to chiếm chỗ.
- Trả lời **thẳng bình luận gốc** thì không gắn chip — người nhận đã rõ.
- **Không ai tự `@` chính mình**: nếu người được nhắc trùng người viết, chip bị bỏ khi lưu.
- Chip lưu theo **ID người**, không dò chữ `@Tên` trong nội dung — tên tiếng Việt trùng nhau nhiều và người dùng sửa được chữ.

**Giao diện ép đúng luật này, nhưng backend mới là nơi chốt**: dù gọi API với `parent_id` trỏ vào một phản hồi, hệ thống vẫn kéo về gốc. Không tồn tại bản ghi cấp 3.

---

## 2bb. Gõ `@` để nhắc bất kỳ ai (CR-031)

Ngoài chip tự mồi khi trả lời, người viết **gõ `@` giữa câu** là có danh sách người xổ ra để chọn.

- Gõ `@` (đầu dòng hoặc sau khoảng trắng) → hiện ngay **những người đang dính tới phiếu**: người tạo phiếu và ai đã bình luận, có nhãn **"trong phiếu"**.
- Gõ tiếp vài chữ → tìm trong **toàn bộ nhân sự đang hoạt động**, theo **tên hoặc mã nhân sự** (`DEMOQL`, `NSU144`…). Nhờ vậy kéo được người mới vào cuộc trao đổi.
- Chọn bằng **phím mũi tên lên/xuống + Enter (hoặc Tab)** — dòng đang nhắm tới có **nền xanh nhạt + vạch xanh bên trái**, lên/xuống hết danh sách thì vòng lại đầu. Bấm chuột cũng được. `Esc` đóng danh sách mà không mất chữ đang gõ. Chọn xong thành **chip màu xanh**, không sửa chữ bên trong được.
- **Nhắc được nhiều người** trong cùng một bình luận (tối đa 20 — quá số đó là spam chuông chứ không phải trao đổi).
- Xóa chip: bấm **Backspace** — cả cụm `@Tên` mất một lần, không để lại chữ cụt mà hệ thống vẫn tưởng là nhắc ai.
- Mỗi người được nhắc nhận **một chuông "Bạn được nhắc tên"** và **không** nhận thêm chuông "Bình luận mới" — một việc một chuông.
- **Gõ tay `@Nguyễn Văn A` không có tác dụng gì** — phải chọn từ danh sách thì hệ thống mới biết là ai. Địa chỉ email trong câu (`abc@degoholding.com`) cũng không bị hiểu nhầm thành lời nhắc.

Ô nhập là vùng soạn thảo (`contenteditable`) chứ không phải ô chữ thuần — bắt buộc, vì ô chữ thuần không hiện được chip. Bộ gõ tiếng Việt (Telex/VNI) vẫn chạy bình thường: React không ghi đè nội dung trong lúc gõ nên không bị nhảy dấu.

---

## 2c. Nhiều bình luận thì hiển thị thế nào

- Mỗi lần tải **10 bình luận gốc mới nhất**, hiện theo thứ tự cũ → mới. Mở phiếu ra là thấy ngay phần đang bàn dở. **Không có trần trên**: bấm "Xem thêm" đủ số lần thì hiện hết cả luồng, dù phiếu có bao nhiêu bình luận.
- Còn cũ hơn thì có nút **"Xem thêm 10 bình luận trước (còn 25)"** ở đầu khối, bấm tải thêm 10 và **chèn lên trên**. Chữ trên nút ghi **số sẽ ra lần này** trước, tổng còn lại để trong ngoặc; còn dưới 10 thì bỏ ngoặc, ghi thẳng "Xem thêm 6 bình luận trước". (Trước đây nút chỉ ghi tổng còn lại — "Xem 25 bình luận trước" — dễ khiến người dùng tưởng bấm một phát ra hết 25.)
- Bung ra rồi thì có **đường lùi**: nút **"Thu gọn"** nằm cạnh nút xem thêm, bấm là trả về đúng **10 gốc mới nhất**, gập luôn các nhánh phản hồi đang mở và kéo màn hình về đầu khối (luồng ngắn lại đột ngột mà không kéo thì đang đọc bị nhảy lung tung). Nút này chỉ hiện khi đã bấm "Xem thêm" ít nhất một lần.
- Bấm vào **tiêu đề "Trao đổi"** để **gập / mở cả khối** — phiếu vốn đã dài, có lúc chỉ muốn xem nội dung phiếu. Gập rồi vẫn thấy **số bình luận** cạnh tiêu đề nên biết là có trao đổi chứ không phải trống. Mặc định là **mở**, không nhớ trạng thái giữa các lần vào phiếu.
- Phản hồi **không tải kèm** — chỉ nạp khi bấm bung **"N phản hồi"**, và bung là hiện **toàn bộ** phản hồi của gốc đó.

Phân trang chạy theo **con trỏ** (`before_id` = id nhỏ nhất đang hiện), không dùng OFFSET: ai đó gửi bình luận mới giữa chừng cũng không làm lệch trang hay lặp dòng.

Nút **đổi thứ tự** ("Cũ nhất trước" ⇄ "Mới nhất trước") chỉ là chuyện **hiển thị ở giao diện** — API luôn trả về 10 gốc **mới nhất**, FE đảo mảng và chuyển nút "Xem thêm" xuống đáy. Không có tham số sắp xếp nào ở backend.

---

## 2d. Thích bình luận

- Biểu tượng **ngón tay cái** dưới mỗi bình luận (cả gốc lẫn phản hồi). Bấm là thích, **bấm lại là bỏ**; mỗi người tối đa **1 lượt** trên một bình luận.
- Bên cạnh là **số lượt**; bấm vào con số sẽ xổ ra **danh sách ai đã thích**.
- **Cố ý không sinh thông báo** khi có người thích — nếu không chuông sẽ rất ồn.

Chỉ có "thích", không có bộ biểu cảm nhiều loại: đây là công cụ nội bộ, "đã đọc / đồng ý" là đủ dùng.

---

## 3. Ai xem được, ai xóa được

Bình luận **không có phân quyền riêng** — nó thừa hưởng quyền của chính chứng từ:

1. Phải có quyền `read` trên entity của phiếu (vd `purchase_request:read`).
2. Phiếu đó phải **nằm trong phạm vi dữ liệu** của người dùng (`apply_scope`) — ai không thấy được phiếu thì không thấy được, cũng không gửi được bình luận vào phiếu đó.

Hệ quả: mở rộng phạm vi xem phiếu là tự động mở rộng phạm vi đọc bình luận, không phải cấu hình thêm chỗ nào.

**Xóa**: chỉ **người viết** xóa được bình luận của mình. Ngoại lệ: người có quyền `user:delete` (quản trị hệ thống) xóa được mọi bình luận — để dọn nội dung không phù hợp. Xóa là **xóa cứng**, không có thùng rác.

Xóa một **bình luận gốc** sẽ **cuốn theo toàn bộ phản hồi** của nó (và các lượt thích liên quan) — hệ thống hỏi xác nhận có nêu rõ số phản hồi sẽ mất. Giữ lại phản hồi mồ côi khi gốc biến mất chỉ làm luồng không ai hiểu đang trả lời cái gì. Xóa một **phản hồi** thì chỉ mất đúng nó.

**Không có màn hình quản lý bình luận tập trung** — chốt theo khách ở CR-030: nội dung nằm rải trong phiếu, quản trị cần dọn thì vào thẳng phiếu.

---

## 4. Thông báo

Có **hai loại chuông tách bạch**, một việc chỉ sinh **một** chuông cho mỗi người:

**a) "Bạn được nhắc tên"** — gửi riêng cho **mọi người bị `@`** trong bài (chip mồi khi trả lời lẫn các chip gõ giữa câu):
tiêu đề `{mã phiếu} — Bạn được nhắc tên`, nội dung `{Tên người viết} đã nhắc bạn trong {loại phiếu} {mã phiếu}: {trích 140 ký tự đầu}`.

Chuông là chữ thuần nên các thẻ `@[12]` trong nội dung được đổi thành `@Tên` trước khi gửi — người nhận đọc ra tên chứ không thấy con số.

**b) "Bình luận mới"** — gửi cho:

- **Người tạo phiếu**, và
- **mọi người đã từng bình luận** trong phiếu đó,

**trừ** người vừa gõ (không tự báo cho mình) **và trừ người vừa nhận chuông nhắc tên** ở trên.

Nội dung chuông: tiêu đề `{mã phiếu} — Bình luận mới`, nội dung `{Tên người viết} đã bình luận trong {loại phiếu} {mã phiếu}: {trích 140 ký tự đầu}`, bấm vào nhảy thẳng tới trang chi tiết phiếu.

**Bấm thích không sinh thông báo.**

**Không gửi email workflow** — bình luận là trao đổi thường xuyên, đẩy qua email sẽ gây nhiễu hộp thư. Web Push chạy nền theo kiểu best-effort: push hỏng thì bình luận vẫn lưu thành công.

---

## 5. Kỹ thuật (tóm tắt)

**Một bảng dùng chung cho mọi loại phiếu** — `tab_comment`, gắn theo cặp `(entity, entity_id)`, đúng khuôn `tab_file_link` của đính kèm. Không đẻ bảng `tab_pr_comment`, `tab_po_comment`… cho từng phân hệ.

| Cột | Ý nghĩa |
|---|---|
| `entity` | loại chứng từ (`purchase_request`, `survey_request`, `survey`, `purchase_order`) — có index |
| `entity_id` | id phiếu — có index |
| `body` | nội dung (TEXT) |
| `parent_id` | `0` = bình luận gốc; `> 0` = id bình luận **gốc** mà nó phản hồi — có index. **Luôn trỏ vào gốc**, không bao giờ trỏ vào một phản hồi |
| `reply_to_user_id` | id người được `@` (`0` = không nhắc ai) |
| `created_by` / `created_at` | người viết / thời điểm (từ `AuditMixin`) |

Bảng lượt thích `tab_comment_reaction`: `comment_id` + `user_id`, ràng buộc **unique `uq_comment_reaction`** đảm bảo mỗi người tối đa 1 lượt trên một bình luận ngay ở tầng CSDL.

**Nhắc tên (CR-031) lưu ở hai chỗ, mỗi chỗ một việc**:

- Trong `body` là **thẻ `@[<user_id>]`** đúng vị trí trong câu, ví dụ `nhờ @[240] và @[241] xem lại giá giúp`. Thẻ giữ được chỗ đứng của lời nhắc giữa câu — thứ mà một bảng quan hệ không diễn tả nổi.
- Bảng phẳng `tab_comment_mention` (`comment_id` + `user_id`, unique `uq_comment_mention`, cả hai cột có index) liệt kê ai bị nhắc. Nhờ nó mà việc bắn chuông và tra tên chỉ tốn **1 query cho cả trang** thay vì bóc thẻ từng bình luận.

Tên hiển thị **không** lưu trong `body` — FE tra theo `mentions` trả kèm mỗi bình luận, nên người đổi tên thì bình luận cũ cũng hiện tên mới. Xóa bình luận thì xóa luôn các dòng nhắc tên của nó (và của các phản hồi bị cuốn theo).

Backend **kiểm lại từng thẻ**, không tin FE: id phải có thật, tài khoản phải còn hoạt động, bỏ trường hợp tự nhắc chính mình, và cắt còn tối đa `MAX_MENTIONS = 20` người. Thẻ không hợp lệ vẫn nằm nguyên trong chữ nhưng không sinh chuông và FE hiện là "không rõ".

**Ép luật 2 cấp ở backend**, không tin FE — `service.create_comment()` gán `parent_id = parent.parent_id or parent.id`. Parent phải **cùng `entity` + `entity_id`**, nếu không thì 400 (chống treo phản hồi sang phiếu khác).

**Registry `app/core/comment_registry.py`** — `COMMENT_POLICY` ánh xạ `entity → (entity cha để kiểm quyền, nhãn hiển thị, route FE)`; `doc_model(entity)` trả model tương ứng. Entity **không có trong bảng này bị từ chối** (chống entity rác). Mở bình luận cho phân hệ mới = thêm 1 dòng ở registry + 1 nhánh ở `doc_model()` + nhúng `<CommentThread>` vào trang, **không đụng model/bảng/migration**.

**API** (`/api/comments`, `app/modules/comment/`):

| Method | Đường dẫn | Mô tả |
|---|---|---|
| `GET` | `/api/comments?entity=&entity_id=&limit=&before_id=` | Một trang bình luận **gốc** (cũ → mới) + số phản hồi từng cái. Trả kèm `total` (cả gốc lẫn phản hồi), `total_roots`, `older_count` (còn bao nhiêu cũ hơn), `oldest_id` (con trỏ trang sau) |
| `GET` | `/api/comments/{id}/replies` | Toàn bộ phản hồi của một bình luận gốc, cũ → mới |
| `GET` | `/api/comments/mentionable?entity=&entity_id=&q=` | Gợi ý người để `@`. Không có `q`: người tạo phiếu + ai đã bình luận (gắn cờ `related`). Có `q`: tìm thêm trong toàn bộ nhân sự đang hoạt động theo **tên hoặc mã nhân sự**, người trong phiếu xếp trước |
| `POST` | `/api/comments` | Gửi bình luận (`{entity, entity_id, body, parent_id?, reply_to_user_id?}`), trả bình luận vừa tạo + bắn thông báo |
| `POST` | `/api/comments/{id}/like` | Thích / bỏ thích, trả `{liked, count}` |
| `GET` | `/api/comments/{id}/likes` | Danh sách ai đã thích |
| `DELETE` | `/api/comments/{id}` | Xóa bình luận (người viết hoặc `user:delete`); gốc thì cuốn theo phản hồi |

Lưu ý thứ tự: `/mentionable` phải khai báo **trước** `/{cid}/replies`, không thì FastAPI khớp nó thành `cid = "mentionable"`.

Mọi endpoint đều đi qua `service.resolve_doc()` — hàm kiểm hai lớp (`user_has_permission(entity cha, 'read')` rồi `apply_scope`) và trả về chính chứng từ để dùng cho thông báo.

Số phản hồi, lượt thích và trạng thái "mình đã thích chưa" đều gom **1 query cho cả trang** (`reply_counts()`, `like_map()`), không hỏi từng dòng. Tên + ảnh + **mã nhân sự** (`author_code`, lấy từ `tab_employee.code` qua `User.employee_id`) cũng gom **2 query cho cả luồng** trong `_authors()` — không có bảng nào bị hỏi theo từng bình luận.

**Hiển thị thời gian**: `fmtRelative(v, cutoffDays = 60)` trong `frontend/src/utils/datetime.ts`. Backend lưu UTC naive nên hàm này tự gắn `Z` trước khi tính; quá `cutoffDays` thì rơi về `fmtDate()`, và mốc giờ đầy đủ luôn nằm ở `title` của thẻ (rê chuột thấy).

**Ô nhập ở FE**: `frontend/src/components/MentionInput.tsx` — vùng `contenteditable` **không điều khiển** (React không ghi đè nội dung trong lúc gõ, nếu không bộ gõ tiếng Việt sẽ nhảy dấu). Mỗi người được nhắc là một `<span data-uid contenteditable="false">` nên Backspace xóa nguyên cụm; lúc bấm Gửi thì `serialize()` đọc ngược cây DOM ra chữ thuần + thẻ `@[id]`. Bẫy `@` dùng regex `(^|khoảng trắng)@…` để **email trong câu không bị hiểu nhầm** thành lời nhắc, và gọi API sau 180ms nghỉ gõ.

**Migration**:

- `4fbb4f65df99` (down `c8d1f6b3a92e`) — tạo `tab_comment` + 2 index.
- `7ac2e5d0b418` (down `4fbb4f65df99`) — thêm `parent_id` / `reply_to_user_id` + index, tạo `tab_comment_reaction`.
- `9b41c7e0d5a2` (down `7ac2e5d0b418`) — tạo `tab_comment_mention` + unique `uq_comment_mention` + 2 index.

**Kiểm thử**: `test/backend/test_comment.py` (32 ca) — không lẫn bình luận giữa hai phiếu cùng `entity_id` khác `entity`, thứ tự cũ→mới, chặn nội dung rỗng/quá dài, danh sách người nhận chuông, entity lạ bị chặn, mọi entity trong registry đều có model; **CR-030**: trả lời phản hồi vẫn ở cấp 2, tự `@` đúng người, không tự nhắc mình, parent khác phiếu bị chặn, phân trang theo con trỏ, đếm phản hồi/lượt thích, thích–bỏ thích, xóa gốc cuốn theo nhánh, người được nhắc không nhận chuông chung; **CR-031**: rút id theo thứ tự và bỏ trùng, chữ `@` thường (email) không bị hiểu là nhắc tên, bỏ id không có thật, không tự nhắc mình bằng thẻ, nhắc nhiều người trong một bài, chuông đổi thẻ thành tên, xóa bình luận cuốn theo lời nhắc, quá 20 người thì bị cắt bớt.

---

## 6. Quyết định đã chốt

| Quyết định | Lý do |
|---|---|
| Một bảng `tab_comment` dùng chung, không mỗi phân hệ một bảng | Đúng khuôn đính kèm đang chạy tốt; thêm phân hệ mới không cần migration |
| Không có entity phân quyền riêng cho bình luận | Thấy phiếu = trao đổi được trong phiếu. Thêm 1 trục quyền nữa chỉ tăng chỗ cấu hình sai |
| Người nhận = người tạo phiếu + ai đã bình luận | Đủ để cuộc trao đổi không rơi; không spam cả phòng như cách báo "mọi người có quyền xem" |
| Không gửi email | Bình luận phát sinh liên tục, email sẽ thành rác. Chuông + Web Push là đủ |
| Không cho sửa bình luận đã gửi | Giữ vết trao đổi trung thực; muốn đính chính thì gửi thêm bình luận |
| **Chỉ 2 cấp**, cấp 3 trở đi tự `@` (CR-030) | Cây lồng nhau vô hạn thụt lề mãi sang phải, trên màn hình phiếu vốn đã nhiều thông tin thì không đọc nổi. `@` giữ được "ai nói với ai" mà không tốn chiều ngang |
| Ép luật 2 cấp ở backend chứ không chỉ ở giao diện | Có vậy dữ liệu mới **chắc chắn** không sinh cấp 3, kể cả khi gọi API trực tiếp |
| `@` lưu **ID người**, không dò chữ `@Tên` trong nội dung | Tên tiếng Việt trùng nhau rất nhiều và người dùng sửa được chữ trong bài |
| Phân trang theo con trỏ `before_id`, không OFFSET | Có bình luận mới chen vào giữa chừng thì OFFSET sẽ làm lệch trang / lặp dòng |
| Chỉ có "thích", không có bộ biểu cảm | Công cụ nội bộ — "đã đọc / đồng ý" là đủ, thêm biểu cảm chỉ thêm chỗ để tranh cãi |
| Thích **không** sinh thông báo | Chuông sẽ rất ồn mà không mang thêm thông tin nào cần hành động |
| Xóa gốc thì cuốn theo phản hồi | Phản hồi mồ côi làm luồng không ai hiểu đang trả lời cái gì |
| Chưa làm màn hình quản lý bình luận tập trung | Khách chốt ở CR-030: cần dọn thì vào thẳng phiếu; chưa có nhu cầu thống kê/kiểm duyệt |
| Mỗi luồng gốc một thẻ riêng thay vì một danh sách chung | Trang chi tiết phiếu vốn đã dày; tách thẻ mới nhìn ra ranh giới giữa các mạch trao đổi |
| Hiện **mã nhân sự** cạnh tên, nhưng chỉ ở bình luận gốc | Tên tiếng Việt trùng nhau rất nhiều; đưa xuống cả nhánh phản hồi thì thừa và rối |
| Thời gian **tương đối**, quá 60 ngày mới đổi sang ngày tháng | Trao đổi đang diễn ra thì "cách đây bao lâu" quan trọng hơn mốc giờ; nhưng "14 tháng trước" thì vô nghĩa, phải trả về ngày tra được |
| Lệch tới 5 phút về tương lai vẫn coi là "Vừa xong" | Đồng hồ máy trạm lệch máy chủ vài phút là chuyện thường; lệch xa hẳn mới là dữ liệu có vấn đề, lúc đó hiện mốc giờ để truy |
| Thùng rác đặt ngay sau "Phản hồi", màu đỏ | Đẩy ra mép phải thì xa nội dung nó tác động; màu đỏ để không bấm nhầm khi đang nhắm nút "Phản hồi" |
| Đổi thứ tự sắp xếp làm **hoàn toàn ở FE** | API vốn đã luôn trả 10 gốc mới nhất; thêm tham số `order` ở backend chỉ tăng bề mặt cần kiểm thử mà không đổi dữ liệu trả về |
| Nhắc được **nhiều người** trong một bình luận (CR-031) | Thực tế hay cần kéo cả người mua lẫn người duyệt vào cùng một câu hỏi; bắt gửi 2 bình luận chỉ để nhắc 2 người là vô lý |
| Lưu thẻ `@[id]` **trong nội dung** thay vì chỉ một bảng quan hệ | Bảng quan hệ mất chỗ đứng của lời nhắc trong câu — "nhờ @A hỏi @B" khác hẳn "nhờ @B hỏi @A" |
| Vẫn giữ thêm bảng `tab_comment_mention` chứ không chỉ bóc thẻ khi cần | Bắn chuông và tra tên cả trang chỉ tốn 1 query; bóc chuỗi từng dòng sẽ hỏng ngay khi luồng dài ra |
| Chưa gõ chữ thì **chỉ hiện người trong phiếu** | Xổ ra cả trăm nhân sự ngay từ đầu thì phải đọc; 95% trường hợp người cần nhắc đã có mặt trong phiếu |
| Gõ rồi thì tìm **toàn bộ nhân sự**, không giới hạn theo phiếu | Mục đích chính của `@` là kéo người **chưa** tham gia vào cuộc trao đổi |
| Không chạy `apply_scope` cho ô gợi ý người | Người được nhắc chỉ nhận một dòng chuông; bấm vào vẫn đụng 403 như thường nếu không có quyền xem phiếu |
| Giới hạn **20 người** một bình luận | Quá số đó là phát thanh chứ không phải trao đổi; chặn luôn kiểu spam chuông cả công ty |
| Bỏ `reply_to_user_id` khỏi lệnh gửi của FE, chip trả lời cũng là một lời nhắc | Xóa chip đi thì đúng nghĩa "đừng báo cho người đó" — không còn chuông ngầm sau lưng người viết. Dữ liệu cũ vẫn được đọc và gộp bình thường |
| Dùng `contenteditable` **không điều khiển**, không dùng `<textarea>` | Textarea không hiện được chip; còn contenteditable bọc bằng state React thì bộ gõ tiếng Việt bị nhảy dấu |
| Gõ tay `@Nguyễn Văn A` **không** tính là nhắc tên | Vẫn là chuyện "lưu ID, không dò chữ" ở trên: tên trùng nhiều và người viết sửa chữ được |
| "Thu gọn" **tải lại trang đầu** chứ không giữ dữ liệu cũ trong bộ nhớ | Giữ lại cũng chẳng nhanh hơn bao nhiêu, mà lỡ có người vừa gửi/xóa thì thu gọn xong là thấy đúng hiện trạng |
| Gập cả khối **không nhớ trạng thái** giữa các lần vào phiếu | Người vào phiếu lần sau thường là để xem có ai nói gì; mặc định gập sẵn dễ làm bỏ sót trao đổi |
