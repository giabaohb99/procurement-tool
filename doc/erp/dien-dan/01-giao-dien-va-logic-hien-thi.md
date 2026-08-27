# DIỄN ĐÀN — GIAO DIỆN VÀ LOGIC HIỂN THỊ

Ngày lập: 26/08/2026. Tài liệu trả lời bốn câu: **giao diện trông thế nào · có trang cá nhân không · đăng bài ra sao · dữ liệu lớn thì bảng tin và comment hiển thị theo logic gì**. Đọc sau [`00`](./00-pham-vi-va-ke-hoach.md); chia việc xem [`02`](./02-lo-trinh-phase.md).

**Quy mô để thiết kế:** ~300 tài khoản (theo SRS WorkHub). Giả định cao tay 50 bài/ngày thì một năm ~15.000 bài, comment vài trăm nghìn dòng — với MySQL có index đây là dữ liệu NHỎ. Cái làm chậm không phải kích thước bảng mà là ba thói quen xấu: OFFSET phân trang, COUNT(*) từng dòng, và hỏi DB theo từng bài (N+1). Toàn bộ thiết kế dưới đây xoay quanh việc tránh đúng ba thứ đó — và hệ bình luận CR-033 đang chạy đã tránh sẵn cả ba, nên phần khó nhất là **bê sang, không phải nghĩ mới**.

---

## 1. Khung màn hình

**Phân hệ trong ERP v2** (QĐ-D6, 27/08/2026 — xem `00` mục 2; bản 26/08 ghi "app riêng khuôn Help Center" đã đảo). Vào ô **Diễn đàn** trên màn chọn phân hệ là rời khung sidebar nghiệp vụ, sang **layout riêng** của phân hệ này. Bố cục:

```
┌────────────────────────────────────────────────┐
│  Logo   [ Bảng tin ]  [ Hướng dẫn ]   chuông ▾ │   <- thanh tab trên cùng
├────────────────────────────────────────────────┤
│                ┌──────────────┐                │
│   (trống /     │  Ô đăng bài  │   (trống /     │
│    rail trái   ├──────────────┤    rail phải   │
│    để sau)     │   Bài viết   │    để sau:     │
│                │   Bài viết   │    bài ghim)   │
│                │   Bài viết   │                │
│                │     ...      │                │
└────────────────────────────────────────────────┘
```

- **Một cột giữa cố định ~640px** như Facebook — feed là dạng đọc dọc, trải rộng màn hình chỉ làm dòng chữ dài khó đọc. Hai rail hai bên đợt 1 để trống, đợt 2 rail phải chứa bài ghim.
- **Tab trên cùng** chứ không phải sidebar trái kiểu ERP: đây là chỗ đọc tin lúc rảnh, không phải màn hình nghiệp vụ — dù nằm trong ERP, phân hệ này vẫn dùng layout tab riêng. Chuông là chuông ERP sẵn có. Đợt 1 có 2 tab: **Bảng tin** · **Cá nhân** (qua avatar góc phải). Tab **Hướng dẫn** chừa sẵn chỗ, đợt 2 mới gắn Help Center vào (QĐ-D4).
- **Ưu tiên điện thoại**: ~300 người dùng phần lớn sẽ lướt trên điện thoại. Cột giữa co về full-width, tab thành thanh dưới đáy màn hình. Các màn `/forum/*` **phải responsive tử tế** — đây là ngoại lệ trong ERP vốn thiết kế desktop trước; ERP v2 đã có PWA cài lên điện thoại nên không cần app riêng để đạt trải nghiệm mobile.
- Route (dưới gốc `/forum`): `/forum` (bảng tin) · `/forum/posts/:id` (chi tiết một bài — đích đến của chuông thông báo) · `/forum/me` và `/forum/users/:id` (trang cá nhân).

## 2. Trang cá nhân — CÓ

Theo QĐ-D3. Gồm hai phần, cả hai đều **không phải làm dữ liệu mới**:

- **Đầu trang:** ảnh đại diện, họ tên, chức danh, phòng ban, công ty — lấy thẳng từ hồ sơ nhân sự đang có. **Không cho sửa hồ sơ ở đây** — hồ sơ là của phân hệ Nhân sự, diễn đàn chỉ hiển thị.
- **Thân trang:** danh sách bài của đúng người đó, dùng **cùng một component feed** với bảng tin, chỉ thêm điều kiện lọc tác giả. Xem trang của chính mình thì thấy đủ mọi bài kể cả bài đã bị ẩn (kèm nhãn "Đã bị ẩn — lý do"); xem trang người khác thì chỉ thấy bài mà mình vốn được xem theo luật đối tượng (mục 4.2).

Không có "sửa ảnh bìa", không có "trạng thái tâm trạng" — trang cá nhân là **tủ bài viết**, không phải hồ sơ mạng xã hội đầy đủ.

## 3. Đăng bài

**Ô mồi trên đầu feed** — một dòng "Chia sẻ điều gì đó với mọi người…" kèm avatar. Bấm vào mở **hộp thoại đăng bài**:

1. **Nội dung**: ô chữ thuần, giữ nguyên xuống dòng, tối đa 10.000 ký tự. Link `http(s)://` tự thành bấm được khi hiển thị. **Đợt 1 không có rich text** (đậm nghiêng, tiêu đề) — bài Facebook cũng là chữ thuần; cần trình bày đẹp là việc của bài Hướng dẫn bên Help Center. Tiptap đã có sẵn trong stack nếu đợt sau muốn nâng.
2. **Ảnh**: bấm nút ảnh / kéo thả / dán từ clipboard — dùng lại nguyên khuôn "tải trước, gắn sau" của đính kèm bình luận: ảnh lên R2 ngay khi chọn và nhận `file_id`, bấm Đăng mới gắn vào bài, bỏ dở thì không treo rác. Tối đa **10 ảnh/bài, 10MB mỗi ảnh** (ảnh điện thoại đời mới 3–8MB, trần 5MB của các entity ảnh hiện tại là không đủ). Chỉ nhận đuôi ảnh (`jpg/jpeg/png/webp`) — bài viết không đính PDF/Excel; hồ sơ tài liệu là việc của hệ nghiệp vụ.
3. **Chọn đối tượng xem** — nút xổ ngay cạnh nút Đăng, 3 mức theo QĐ-D3: **Phòng ban của tôi** · **Công ty của tôi** · **Toàn tập đoàn**. Mặc định là lựa chọn **lần đăng trước** (nhớ ở máy); lần đầu tiên mặc định "Công ty của tôi". Phòng ban/công ty lấy theo hồ sơ nhân sự của người đăng **tại thời điểm đăng** và đóng băng vào bài — người chuyển phòng thì bài cũ vẫn thuộc phòng cũ, đúng ngữ cảnh lúc viết.
4. Bấm **Đăng** → bài hiện ngay đầu feed, không qua duyệt (QĐ-D1).

Sửa/xóa bài của chính mình: chờ chốt D-Q4 — mặc định tạm của đợt 1 là **cho xóa, chưa cho sửa** (giống bình luận hiện hành, đỡ một cửa phức tạp; đảo lại chỉ là mở thêm API).

## 4. Bảng tin — logic hiển thị khi dữ liệu lớn

### 4.1. Thứ tự: thời gian thuần, không xếp hạng

Feed hiện **bài mới nhất trước**, hết. Không có thuật toán "bài nhiều like nổi lên" — với 300 người, xếp hạng thuật toán chỉ làm người dùng không hiểu vì sao bài biến mất, và làm feed không còn là dòng thời sự của công ty. Bài quan trọng cần nổi thì đợt 2 có **ghim** (quản trị ghim lên rail phải/đầu feed) — cơ chế minh bạch hơn thuật toán.

### 4.2. Ai thấy bài nào — lọc ngay trong SQL

Mỗi bài mang `audience` (SMALLINT) + `dept_id` + `company_id` đóng băng lúc đăng. Người xem có `dept_id`/`company_id` từ hồ sơ nhân sự. Một câu WHERE duy nhất:

```
status = published
AND ( audience = public
   OR (audience = company AND company_id = :cty_nguoi_xem)
   OR (audience = dept    AND dept_id    = :phong_nguoi_xem)
   OR created_by = :nguoi_xem )        -- luôn thấy bài của chính mình
```

- Lọc ở **tầng SQL, không lọc ở FE** — FE lọc nghĩa là dữ liệu người ta không được xem đã rời máy chủ.
- `forum_admin` bỏ điều kiện audience (phải thấy hết mới dọn được), và thấy cả bài `hidden`.
- Người thuộc holding thấy gì ở mức "công ty" là câu D-Q5, chưa chặn: đổi câu trả lời chỉ là đổi điều kiện WHERE.

### 4.3. Phân trang: con trỏ, cấm OFFSET

Đúng khuôn `before_id` của bình luận CR-033: trang đầu lấy `ORDER BY id DESC LIMIT 20`, cuộn xuống đáy thì gọi tiếp với `before_id` = id nhỏ nhất đang hiện. `id` tự tăng nên tương đương thứ tự thời gian, và **có bài mới chen vào giữa chừng cũng không lệch trang, không lặp bài** — chính là lỗi kinh điển của OFFSET mà hệ này đã cấm từ CR-030. FE dùng `useInfiniteQuery` (TanStack Query, có sẵn trong stack) — cuộn vô hạn.

Đang đọc mà có bài mới: **không tự chèn vào feed** (đang đọc dở mà trang nhảy là kiểu khó chịu nhất) — hiện nút nổi "Có bài viết mới" trên đầu, bấm mới tải lại trang đầu.

### 4.4. Số đếm và dữ liệu kèm bài: gom theo trang, không hỏi từng bài

Một trang 20 bài cần: tác giả (tên + avatar + chức danh), số like, "mình đã like chưa", số bình luận, danh sách ảnh. Luật cứng — **mỗi loại đúng 1 query cho cả trang** (`WHERE post_id IN (…20 id…) GROUP BY`), đúng khuôn `reply_counts()` / `like_map()` / `file_map()` / `_authors()` mà module comment đã viết sẵn. Tổng cộng ~6 query cho một trang bất kể trang có bao nhiêu bài.

**Cố ý KHÔNG làm cột đếm sẵn** (`like_count`, `comment_count` trên bảng bài) ở đợt 1: cột đếm sẵn nhanh hơn nhưng đẻ ra bài toán lệch số phải đối soát; ở quy mô 15k bài/năm, đếm gom theo trang là quá đủ nhanh. Khi nào đo được là chậm thì thêm cột đếm — thêm sau dễ, gỡ ra khó.

Index tối thiểu trên bảng bài: `(status, id)` và `(created_by, id)` (trang cá nhân); thêm `(audience, dept_id, id)` / `(audience, company_id, id)` nếu đo thấy cần — đừng rải index trước khi đo.

### 4.5. Trên thẻ bài viết

- Nội dung dài quá **~10 dòng thì cắt** kèm nút "Xem thêm" — bung tại chỗ, không bắt sang trang khác.
- **Ảnh xếp lưới kiểu Facebook**: 1 ảnh = nguyên khổ, 2 ảnh = 2 cột, 3 ảnh = 1 lớn 2 nhỏ, từ 5 ảnh = lưới 2×2 và ô cuối phủ "+N". Bấm ảnh mở đèn chiếu (lightbox đã có khuôn từ bình luận).
- Thời gian **tương đối** ("25 phút trước"), quá 60 ngày đổi sang ngày tháng — dùng lại đúng `fmtRelative` và lý do đã chốt ở CR-030.
- Góc bài có biểu tượng đối tượng xem (phòng ban / công ty / tập đoàn) — người đăng nhìn lại biết bài mình đang mở cho ai.

## 5. Comment — bê nguyên hệ CR-033, đây là chỗ RẺ nhất

Hệ bình luận đang chạy trên chứng từ đã giải trọn bài "comment số lượng lớn", dùng chung bảng `tab_comment` theo cặp `(entity, entity_id)`. Mở cho diễn đàn = thêm entity `forum_post` vào `comment_registry` + nhúng khối comment vào thẻ bài viết. **Không bảng mới, không migration cho phần comment.**

Cơ chế chịu tải đã có sẵn, đối chiếu `doc/tai-lieu-chuc-nang/11-binh-luan-tren-chung-tu.md`:

| Bài toán | CR-033 đã giải |
|---|---|
| Comment nhiều nghìn dòng một bài | Mỗi lần tải **10 comment gốc**, con trỏ `before_id`, "Xem thêm 10 bình luận trước (còn N)" |
| Cây trả lời sâu vô hạn | **Chỉ 2 cấp kiểu YouTube** — trả lời một phản hồi vẫn treo vào gốc + chip `@Tên`; backend ép luật, không tin FE |
| Phản hồi kéo nặng trang | Phản hồi **không tải kèm** — gom sau nút "N phản hồi", bấm mới nạp |
| N+1 query | Số phản hồi, số like, đã-like-chưa, tên + avatar tác giả, file — **mỗi loại 1–2 query cho cả trang** |
| Nhắc tên, like comment, đính ảnh vào comment | Có sẵn nguyên bộ (CR-030/031/033) |

Trên thẻ bài ngoài feed chỉ hiện **số** bình luận; bấm vào mới nạp khối comment (trong thẻ bung ra hoặc ở `/posts/:id`) — feed không bao giờ tải comment của 20 bài cùng lúc.

**Một chỗ phải viết thêm thật sự:** `resolve_doc()` của comment hiện kiểm quyền theo RBAC + phạm vi chứng từ; với `forum_post` phải rẽ nhánh kiểm theo **luật đối tượng xem ở mục 4.2** (thấy được bài mới đọc/gửi được comment). Viết đúng một chỗ này thì đính kèm trong comment cũng tự ăn theo, vì đường kiểm file đã đi qua `resolve_doc()`.

## 6. Like bài viết

Bảng `tab_forum_reaction` (`post_id` + `user_id`, unique) — chép nguyên khuôn `tab_comment_reaction` đang chạy. Bấm like, bấm lại bỏ; bấm vào số hiện danh sách ai đã thích. **Đợt 1 like không sinh chuông** (theo đúng lý do đã chốt ở CR-030: chuông like là chuông ồn nhất) — sếp muốn có thì đảo lại thành chuông gộp "5 người đã thích bài của bạn", ghi nhận là D-Q6.

## 7. Quyết định thiết kế của tài liệu này

| Quyết định | Lý do |
|---|---|
| Feed một cột giữa ~640px, ưu tiên điện thoại | Feed là dạng đọc dọc; người dùng chính lướt trên điện thoại |
| Thứ tự thời gian thuần, không thuật toán xếp hạng | 300 người không cần thuật toán; minh bạch hơn, bài cần nổi thì ghim |
| Phân trang con trỏ `before_id`, cấm OFFSET | Bài mới chen giữa chừng không làm lệch trang — bài học đã trả tiền ở CR-030 |
| Bài mới không tự chèn vào feed đang đọc | Trang tự nhảy khi đang đọc là trải nghiệm tệ nhất; nút "Có bài viết mới" là đủ |
| Lọc đối tượng xem ở SQL, không ở FE | Lọc ở FE nghĩa là dữ liệu cấm xem đã rời máy chủ |
| `dept_id`/`company_id` đóng băng vào bài lúc đăng | Người chuyển phòng thì bài cũ giữ đúng ngữ cảnh lúc viết; khỏi join hồ sơ khi lọc feed |
| Không làm cột đếm sẵn ở đợt 1, đếm gom theo trang | Khuôn nhà đang chạy tốt; cột đếm sẵn đẻ bài toán lệch số — thêm sau dễ, gỡ khó |
| Comment dùng chung `tab_comment`, thêm entity `forum_post` | Không migration, kế thừa trọn bộ 2 cấp + con trỏ + gom query + nhắc tên + đính ảnh |
| Comment chỉ nạp khi mở bài, feed chỉ hiện số | Feed 20 bài mà kéo comment cả 20 là tự bóp mình |
| Bài chỉ nhận ảnh, không nhận PDF/Excel | Diễn đàn là chỗ đọc; hồ sơ tài liệu là việc của hệ nghiệp vụ và Help Center |
| Ảnh 10MB/tấm, 10 tấm/bài | Ảnh điện thoại 3–8MB; trần 5MB của entity ảnh hiện tại không đủ |
| Chữ thuần + tự nhận link, chưa rich text | Bài Facebook cũng chữ thuần; rich text để Help Center lo, tiptap sẵn trong stack nếu cần sau |
| Like không sinh chuông (đợt 1) | Cùng lý do CR-030; muốn có thì làm chuông gộp, ghi D-Q6 |
| Trang cá nhân = tủ bài viết, không sửa hồ sơ | Hồ sơ là của phân hệ Nhân sự; diễn đàn chỉ hiển thị |

## 8. Nhật ký

| Ngày | Nội dung |
|---|---|
| 26/08/2026 | Lập tài liệu theo yêu cầu: giao diện, trang cá nhân, luồng đăng bài, logic feed và comment khi dữ liệu lớn |
| 27/08/2026 | Sửa mục 1 theo **QĐ-D6**: phân hệ trong ERP v2 thay vì app riêng — route dời xuống gốc `/forum`, chuông dùng chuông ERP, thêm yêu cầu responsive cho các màn `/forum/*`. Bố cục một cột + tab giữ nguyên |
