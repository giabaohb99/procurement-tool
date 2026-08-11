# Trung tâm Hướng dẫn sử dụng (Help Center)

Tài liệu chức năng — cập nhật 2026-08-11.

Tài liệu **kỹ thuật** chi tiết (stack, bố cục CSS, trình soạn thảo Quill, kéo-thả, token màu) nằm ở [`help-center/README.md`](../../help-center/README.md). File này mô tả **nghiệp vụ**: ai dùng, làm được gì, dữ liệu gồm những trường nào, và các quyết định đã chốt.

---

## 1. Đây là gì và vì sao tách riêng

Trung tâm HDSD là nơi chứa **tài liệu hướng dẫn dùng hệ Thu mua**: bài viết theo phân hệ, ảnh minh họa từng bước, video/demo nhúng, câu hỏi thường gặp.

Nó là **một ứng dụng riêng**, không phải một màn hình trong app Thu mua:

- Chạy ở **tên miền riêng** — prod `help.degoholding.vn`, dev `devhelp.degoholding.vn`, local `localhost:8082`.
- **Dùng chung backend và chung tài khoản** với app Thu mua (`/api/v1/help-center`, `/api/v1/faq`).
- Trong app Thu mua **không còn** mục "Hướng dẫn sử dụng" ở menu trái; lối vào duy nhất là **nút dấu hỏi `?` cạnh chuông thông báo** trên thanh trên cùng, mở tab mới.

Tách ra vì khu người dùng của Trung tâm HDSD **công khai** — người chưa đăng nhập vẫn đọc được. Để nó nằm trong app nghiệp vụ thì mọi trang đều nằm sau lớp đăng nhập, mà hướng dẫn sử dụng lại là thứ cần đọc được **trước** khi biết đăng nhập thế nào. (CR-019)

## 2. Hai khu vực

| Khu | Đường dẫn | Ai vào được | Làm gì |
|-----|-----------|-------------|--------|
| **Người dùng** | `/`, `/<slug-bài>`, `/cau-hoi-thuong-gap` | **công khai, không cần đăng nhập** | chỉ đọc: trang chủ · trang danh mục · trang bài viết · câu hỏi thường gặp · tìm kiếm |
| **Quản trị** | `/admin`, `/admin/:id`, `/admin/faq`, `/admin/trang-chu`, `/admin/lich-su` | cần quyền `help_article:write` | quản lý cây bài viết · soạn bài · câu hỏi thường gặp · bố cục trang chủ · lịch sử thay đổi |

Mọi endpoint **ĐỌC** ở backend (`GET /api/v1/help-center/*`, `GET /api/v1/faq`) không đòi token; mọi endpoint **GHI** vẫn kiểm quyền trên entity `help_article`.

Nút "Quản trị" chỉ hiện ở header khi user có quyền ghi; gõ thẳng `/admin` mà không có quyền thì bị đẩy về `/`.

### Bàn giao phiên từ app Thu mua

Hai app khác cổng nên **không dùng chung localStorage** — vào Trung tâm HDSD sẽ là khách vãng lai dù đang đăng nhập bên Thu mua. Khi người có `help_article:write` bấm nút `?`, link được gắn token ở **phần hash** của URL (`#t=…&r=…`); Help Center nạp token, gọi `/api/auth/me` lấy quyền rồi **xóa hash khỏi thanh địa chỉ ngay**. Nhờ vậy quản trị viên không phải đăng nhập lần hai. Dùng hash chứ không phải query string vì **hash không được trình duyệt gửi lên server** — token không lọt vào log web server.

Người dùng thường không được kèm token, vì khu người dùng vốn công khai.

## 3. Vai trò và quyền

| Loại | Tài khoản | Quyền |
|------|-----------|-------|
| Quản trị HDSD | `helpadmin` (mã NV `HDSD0001`) — vai trò `help_admin` seed sẵn | CRUD bài viết · ảnh từng bước · FAQ · bố cục trang chủ |
| Admin hệ thống | tài khoản admin có sẵn | như trên |
| Mọi người còn lại | *không cần tài khoản* | chỉ đọc khu người dùng |

Vai trò `help_admin` **chỉ** có quyền trên entity `help_article` — không đụng tới bất kỳ nghiệp vụ hay cấu hình hệ thống nào. Người viết tài liệu thường không phải người có quyền trong hệ Thu mua, nên không thể dùng vai trò sẵn có.

Câu hỏi thường gặp **dùng chung** quyền `help_article`, cố ý không đẻ thêm entity quyền mới cho một bảng 4 cột.

Không có `apply_scope` cho entity này: tài liệu hướng dẫn không có "phạm vi dữ liệu" — ai viết được thì viết được tất cả.

## 4. Cấu trúc nội dung

### 4.1 Cây bài viết (`tab_help_article`)

Bảng **tự tham chiếu** `parent_id` để thành cây, sâu **tối đa 3 cấp**.

| Trường | Kiểu | Ý nghĩa |
|--------|------|---------|
| `parent_id` | BigInt, nullable | mục cha; `NULL` = **mục gốc** |
| `title` | String(255) | tiêu đề — cũng là thứ sinh ra đường dẫn ở khu người dùng |
| `content` | Text | nội dung HTML (soạn bằng trình soạn thảo, hoặc nhập từ file) |
| `sort_order` | Int | thứ tự trong cùng mục cha |
| `summary` | String(255), nullable | **mô tả ngắn** — dòng chữ dưới tiêu đề trên thẻ ở khu người dùng |
| `icon` | String(500), nullable | slug icon dựng sẵn (vd `rocket`) **hoặc URL ảnh** người dùng tự tải lên |

Cột `icon` để tới 500 ký tự vì nó chứa được cả URL ảnh. Giá trị bắt đầu bằng `/` hoặc `http` được hiểu là ảnh, còn lại là slug.

Tuy cây sâu 3 cấp nhưng giao diện chỉ phân biệt **2 loại**: **Mục gốc** (cấp 0 — hiện thành thẻ danh mục ngoài trang chủ) và **Bài viết** (mọi cấp bên dưới, cấp 1 lẫn cấp 2 gọi chung như nhau).

**Ảnh hướng dẫn từng bước** nằm ở bảng riêng `tab_help_article_slide` (`article_id` · `image_url` · `caption` · `step_order`), xóa bài thì xóa theo (`ondelete=CASCADE`).

### 4.2 Câu hỏi thường gặp (`tab_faq`)

`question` · `answer` (HTML) · `sort_order` · `is_active`. Trang người dùng gọi `?active_only=true` nên câu đang tắt không lộ ra.

### 4.3 Bố cục trang chủ (`tab_help_home_section` + `tab_help_home_item`)

**4 khung cố định**, seed sẵn, **không thêm/xóa khung được** — chỉ đổi tiêu đề · ẩn/hiện · thứ tự · nội dung bên trong:

| Khung | Nhận loại gì (`item_kind`) |
|-------|---------------------------|
| Bắt đầu ngay | bài viết (kèm nền gradient + ảnh minh họa cho từng tile) |
| Các Phân hệ | bài viết |
| Không tìm thấy điều bạn cần? | câu hỏi thường gặp |
| Mẹo tra cứu | thẻ tự nhập (icon + tiêu đề + mô tả) |

Backend chặn thẳng (400) nếu gửi sai loại cho khung. Mỗi khung tối đa **6 mục** (vừa 2 hàng lưới 3 cột) — giới hạn đặt ở frontend vì đây là cấu hình hiển thị, chỉ quản trị viên chạm tới.

**Khung để trống thì trang chủ dùng nội dung mặc định** (bài đầu mỗi nhánh · các mục gốc · thẻ dẫn sang FAQ · 3 mẹo viết trong code). Gọi API lỗi cũng rơi về bố cục mặc định — **trang chủ không bao giờ trắng**, kể cả hệ mới cài chưa cấu hình gì.

Mọi thay đổi ở trang Bố cục **ghi ngay xuống server, không có nút Lưu** — đây là cấu hình hiển thị chứ không phải nội dung đang soạn dở.

## 5. Người dùng thấy gì (khu công khai)

Ba tầng:

| Tầng | Khi nào | Nội dung |
|------|---------|----------|
| **Trang chủ** `/` | — | hero + ô tìm kiếm lớn · 3 tile "Bắt đầu ngay" · lưới thẻ "Các Phân hệ" · câu hỏi thường gặp · mẹo tra cứu |
| **Trang danh mục** `/<slug>` | node **có** bài con | sidebar cây tài liệu + breadcrumb + tiêu đề + nội dung mở đầu + **danh sách bài con dạng thẻ** |
| **Trang bài viết** `/<slug>` | node **không** có con | 3 cột: cây tài liệu trái · nội dung giữa · mục lục "Trong bài viết này" phải |

Cuối bài có nút **Bài trước / Bài tiếp theo**.

**Đường dẫn là slug sinh từ tiêu đề** (`/bao-cao-mua-hang` thay vì `/7`), tính ngay trên client nên không cần thêm cột ở DB. Trùng slug hoặc đụng đường dẫn cố định (`login` · `admin` · `cau-hoi-thuong-gap`) thì gắn thêm id (`bao-cao-mua-hang-7`). Link cũ dạng số vẫn vào đúng bài và tự đổi sang slug trên thanh địa chỉ.

**Đánh đổi đã chấp nhận:** đổi tiêu đề là đổi đường dẫn, link cũ gãy. Chấp nhận được vì đây là tài liệu nội bộ, người ta vào bằng menu và ô tìm kiếm chứ không lưu bookmark sâu.

Ba mức bề ngang màn hình có hành vi khác nhau: từ 1280px hiện đủ cả cây tài liệu lẫn mục lục; 1024–1279px thì **mục lục nhường chỗ**, chỉ hiện khi người đọc tự tắt cây tài liệu; dưới 1024px cây tài liệu thành **ngăn kéo phủ lên**, mục lục ẩn hẳn. Ở khổ 1024 mà giữ cả hai cột thì phần nội dung còn chưa tới 400px, đọc không nổi.

**Không bao giờ để trang trắng:** slug không khớp bài nào thì hiện thẻ "Không tìm thấy bài viết" (vẫn còn header + menu + ô tìm kiếm để đi tiếp); lỗi render bất kỳ rơi vào error boundary với nút Tải lại / Về trang chủ.

### Tìm kiếm

`GET /api/v1/help-center/search?q=` khớp **cả tiêu đề lẫn nội dung**, trả về đoạn trích quanh từ khóa (đã bỏ HTML) kèm vị trí khớp để client bôi đậm. **Gõ không dấu vẫn khớp**. Bài khớp tiêu đề xếp trước.

## 6. Quản trị viên làm được gì

| Trang | Chức năng |
|-------|-----------|
| `/admin` | bảng cây: thêm/xóa · **sửa nhanh tiêu đề tại chỗ** · **kéo-thả** đổi thứ tự và chuyển mục cha · nút lên/xuống · lọc theo tiêu đề · **Nhập từ file** |
| `/admin/:id` | soạn bài trên 1 trang: tiêu đề inline · mô tả ngắn + icon · trình soạn thảo luôn mở · ảnh từng bước · danh sách bài con · lịch sử. **Ctrl/⌘+S** để lưu |
| `/admin/faq` | câu hỏi thường gặp: thêm/sửa/xóa · bật-tắt hiển thị · đổi thứ tự |
| `/admin/trang-chu` | bố cục trang chủ: 3 cột nguồn / 4 khung / xem trước, kéo-thả chọn nội dung |
| `/admin/lich-su` | nhật ký thay đổi của **mọi** bài viết |

Quy tắc cứng khi sửa cây:

- **Xóa bài viết là xóa luôn toàn bộ bài con/cháu bên trong** — hộp thoại xác nhận báo rõ số bài sẽ mất.
- Chuyển bài bị **chặn** nếu tạo vòng lặp cây hoặc làm cấu trúc vượt quá 3 cấp.
- Bài được chuyển sang mục mới luôn nằm ở **cuối** mục đó, không chen vào giữa (nếu không sẽ trùng `sort_order` với các bài sẵn có).
- **Kéo-thả tắt khi đang lọc theo tiêu đề**: lúc đó danh sách là cây đã cắt bớt, tính lại thứ tự trên đó sẽ ghi sai `sort_order` của các bài đang bị ẩn.

### Trình soạn thảo

Bài viết và câu trả lời FAQ dùng **chung một** trình soạn thảo (FAQ chỉ rút gọn thanh công cụ). Ngoài định dạng thường có thêm 3 nút riêng:

| Nút | Dùng khi |
|-----|----------|
| **Bảng** | chèn bảng, thêm/xóa hàng cột, gộp/tách ô, **kéo giãn độ rộng cột** (độ rộng có được lưu lại) |
| **Nhúng mã** | có **cả đoạn code** nhúng của nhà cung cấp (Guideflow, YouTube…) — dán vào, xem trước, rồi chèn |
| **Mã HTML** | bật/tắt giữa soạn trực quan và sửa thẳng mã nguồn |

Chỉ có **URL nhúng** (không có code) thì dùng nút video (▶) thông thường.

Toàn bộ tooltip và nhãn ô dán URL đã dịch sang tiếng Việt — thư viện gốc không có tooltip và nhãn là tiếng Anh.

### Nhập bài từ file (CR-052, CR-053)

Ba đường vào, chọn theo thứ đang có trong tay:

| Nguồn | Cách nạp | Ghi chú |
|-------|----------|---------|
| **File HTML / Markdown** (Word → HTML, xuất từ AI, chép từ web) | nút **"Nhập từ file"** ở `/admin` — chọn nhiều file, chọn mục đích, công tắc ghi đè bài trùng tiêu đề | **2 MB/file, 30 file/lần**. Trả kết quả **từng file** (`đã tạo` / `đã cập nhật` / `lỗi`) chứ không dừng ở file lỗi đầu — nhập 10 file hỏng 1 vẫn giữ được 9 |
| **File HTML / Markdown, đổ vào bài đang mở** | hộp thoại ngay trong trang soạn bài `/admin/:id` | Chỉ **bóc tách, KHÔNG ghi DB** — nội dung vào ô soạn thảo, người dùng xem lại rồi tự bấm Lưu. Chọn *thay toàn bộ* hay *chèn vào cuối*, và có lấy tiêu đề từ file hay không |
| **File Excel do khách soạn** (cột *Phân cấp* 1 / 1.1 / 1.1.1) | script vận hành `scripts/import_help_content_xlsx.py` | Mặc định **chạy thử**; khớp theo tiêu đề, có thì cập nhật, chưa có thì tạo, **không xóa gì** |

Cách lấy tiêu đề khi nhập file: **`<h1>` đầu tiên** (và **xóa thẻ đó khỏi nội dung** — trang đã hiện tiêu đề riêng, không xóa thì hiện hai lần), không có thì `<title>`, không nữa thì tên file. Mô tả ngắn cắt 250 ký tự chữ trần.

### Lọc HTML là bắt buộc, không phải tùy chọn

Nội dung bài render bằng `dangerouslySetInnerHTML`, nên **`<script>` trong file nhập vào sẽ chạy thật** ở máy mọi người đọc tài liệu. Mọi HTML từ ngoài đi qua `sanitize_html` theo danh sách thẻ/thuộc tính cho phép:

- Bỏ cả **nội dung** của `<script>` / `<style>` / `<noscript>` / `<template>` — chỉ bỏ thẻ thì mã JS rơi ra thành text hiển thị.
- Chặn mọi thuộc tính `on*=`, mọi `javascript:` / `vbscript:` (kể cả viết hoa lẫn lộn, chèn xuống dòng, hay mã hóa thực thể `&#58;`), và `data:` không phải `data:image/`.
- **Không cho `srcdoc`** — xem mục 8.

Bộ lọc có **47 test** riêng ở `test/backend/test_help_center_import.py`, phủ từng đường vào.

## 7. Nội dung nằm trong CSDL — cách mang giữa các môi trường

Đây là điểm dễ nhầm nhất của phân hệ này.

**Bài viết và FAQ là dữ liệu trong DB của từng môi trường, không phải file trong repo.** Soạn ở local hay dev thì dev/prod **không tự có**. Cố ý không nhét vào seed: seed chạy lại mỗi lần deploy, sẽ đè mất bài người dùng vừa sửa trên giao diện.

Quy trình mang đi:

1. **Xuất** từ môi trường nguồn: `python -m scripts.export_help_content` → JSON (duyệt cây theo chiều sâu nên **cha luôn đứng trước con**).
2. **Nạp** vào môi trường đích: `python -m scripts.import_help_content` (chạy thử, không ghi gì) rồi thêm `--nap`.

Hai chế độ khớp:

| Chế độ | Khớp theo | Dùng khi |
|--------|-----------|----------|
| mặc định | **tiêu đề** bài / **câu hỏi** FAQ | môi trường đích có nội dung soạn riêng cần giữ |
| `--theo-id` (+ `--xoa-thua`) | **id** | muốn đích thành **bản sao y hệt** nguồn |

**Khớp theo tiêu đề có bẫy:** đổi tên bài rồi nạp thì script hiểu là bài **mới** → sinh ra bản sao và để lại vỏ mục cũ rỗng, phải xóa tay. Đó chính là chuyện đã xảy ra khi đưa nội dung dev sang prod (CR-056): dev đã dựng lại cây mục, prod lại còn 2 bài trùng tên nên dict khớp theo tiêu đề chỉ giữ được 1. Vì vậy mới thêm `--theo-id`.

Khớp theo id còn là cách **duy nhất giữ được ảnh minh họa từng bước** — `tab_help_article_slide.article_id` trỏ theo id, khớp theo tiêu đề mà bài bị đổi tên thì bài mang ảnh bị bỏ lại.

**Luôn xuất bản hiện tại của đích ra file trước khi nạp** làm đường lùi.

## 8. Sự cố bảo mật đã xử lý — XSS qua `srcdoc` (CR-054)

Bộ lọc HTML cho `iframe` đi qua và để `srcdoc` trong danh sách thuộc tính cho phép, nhưng `srcdoc` **không nằm trong danh sách thuộc tính-URL** nên **không bị kiểm gì cả**. `srcdoc` là **cả một trang HTML nhét vào thuộc tính** và chạy **cùng origin** với trang cha — nên `<iframe srcdoc="<script>…">` đi thẳng qua bộ lọc rồi chạy thật ở khu người đọc, đọc được token của mọi người vào xem tài liệu. Đã dựng lại được lỗ hổng trước khi sửa.

Sửa: **bỏ `srcdoc` khỏi danh sách thuộc tính cho phép**. Iframe nhúng video vẫn chạy vì chỉ cần `src` (đã có kiểm URL).

Mức nguy hiểm có giảm vì phải có quyền `help_article:create` mới gọi được endpoint nhập file, nhưng vẫn là leo thang từ "biên tập tài liệu" lên "chiếm phiên người đọc" — không chấp nhận được.

> Lưu ý: nút **Nhúng mã** trong trình soạn thảo **vẫn** dùng `srcdoc`, nhưng đó là đường khác — mã do chính quản trị viên dán trên giao diện, được bọc iframe `sandbox` và chỉ nhận URL `http(s)`. Cái bị bỏ là `srcdoc` **đi qua bộ lọc file nhập từ ngoài**.

## 9. Quyết định đã chốt

| Quyết định | Lý do |
|-----------|-------|
| Trung tâm HDSD là **app riêng, domain riêng**, không phải màn hình trong app Thu mua | khu người dùng phải công khai — hướng dẫn cần đọc được trước khi biết đăng nhập thế nào |
| Khu người dùng **không cần đăng nhập**; chỉ endpoint GHI mới kiểm quyền | tài liệu nội bộ nhưng không nhạy cảm; bắt đăng nhập chỉ làm người mới nản |
| Bàn giao phiên bằng token ở **hash** URL, xóa ngay sau khi nạp | hai app khác cổng không chung localStorage; hash không được gửi lên server nên token không vào log |
| Vai trò **`help_admin` riêng**, chỉ có quyền trên `help_article` | người viết tài liệu thường không có vai trò nào trong hệ Thu mua |
| FAQ **dùng chung quyền** `help_article`, không đẻ entity mới | một bảng 4 cột không đáng có entity phân quyền riêng |
| Nội dung **sống trong DB**, mang đi bằng xuất/nạp script — **không** nhét vào seed | seed chạy lại mỗi lần deploy sẽ đè bản người dùng vừa sửa (D-018/D-024) |
| Script nạp **mặc định chạy thử**, phải thêm `--nap` mới ghi | nạp nhầm môi trường là hỏng cả kho tài liệu |
| Thêm chế độ **`--theo-id`** bên cạnh khớp theo tiêu đề | đổi tên bài mà khớp theo tiêu đề thì sinh bản sao + bỏ rơi ảnh minh họa (CR-056) |
| Cây tài liệu **tối đa 3 cấp** | sâu hơn thì breadcrumb và sidebar không đọc được nữa; tài liệu hướng dẫn không cần |
| Xóa bài **xóa luôn cây con**, có xác nhận báo rõ số bài | để lại bài con mồ côi thì chúng biến mất khỏi mọi lối điều hướng mà vẫn nằm trong DB |
| **Đường dẫn theo slug tiêu đề**, tính ở client, không thêm cột DB | link đọc được, không phải sửa backend; đánh đổi là đổi tiêu đề thì link cũ gãy — chấp nhận với tài liệu nội bộ |
| **4 khung trang chủ cố định**, mỗi khung 1 loại phần tử, tối đa 6 mục | giữ trang chủ luôn cân đối; khung trống thì rơi về nội dung mặc định nên không bao giờ trắng |
| Trang Bố cục trang chủ **ghi ngay, không có nút Lưu** | đây là cấu hình hiển thị, không phải nội dung đang soạn dở |
| Nhập file trả kết quả **từng file**, không dừng ở lỗi đầu | nhập 10 file hỏng 1 vẫn giữ được 9 |
| Nhập file **trong trang soạn bài** thì chỉ bóc tách, **không ghi DB** | tránh ghi đè bài đang soạn dở mà người dùng không kịp trở tay |
| **Lọc HTML bắt buộc** với mọi nội dung từ ngoài | nội dung render bằng `dangerouslySetInnerHTML` — `<script>` sẽ chạy thật |
| Bỏ `srcdoc` khỏi danh sách cho phép của bộ lọc | `srcdoc` chạy cùng origin, là XSS thật đã dựng lại được (CR-054) |
| Bọc mã nhúng của bên thứ ba vào **iframe `srcdoc` + `sandbox`** (đường soạn thảo) | `<script>` chèn qua innerHTML không chạy; và CSS/JS bên thứ ba phải bị nhốt lại |

## 10. Lịch sử thay đổi chính

| CR | Ngày | Nội dung |
|----|------|----------|
| CR-019 | 2026-08-05 | tách ra domain riêng (`help` / `devhelp`), bỏ menu trái, thêm nút `?` ở thanh trên cùng |
| CR-038 | 2026-08-07 | thêm `import_help_content.py` — đường nạp nội dung sang môi trường khác (khớp theo tiêu đề) |
| CR-052 | 2026-08-08 | nạp nội dung từ **file Excel** khách soạn; sửa lỗi bảng bị tô 2 hàng tiêu đề |
| CR-053 | 2026-08-08 | nhập bài từ **file HTML / Markdown** (ở `/admin` và ngay trong trang soạn bài) + bộ lọc HTML |
| CR-054 | 2026-08-08 | **vá XSS `srcdoc`** + sửa nhánh lấy tiêu đề từ `<title>` + 47 test cho bộ lọc |
| CR-056 | 2026-08-10 | thêm `export_help_content.py` và chế độ `--theo-id` / `--xoa-thua`; đồng bộ prod 35 → 55 bài |

## 11. Lần rà soát gần nhất

Rà 2026-08-11. Đối chiếu tài liệu với mã nguồn:

| Nội dung kiểm | Đối chiếu với | Kết quả |
|---------------|---------------|---------|
| Trường của bài viết · slide · 4 khung trang chủ | `backend/app/modules/help_center/model.py` | đúng |
| Danh sách endpoint, endpoint nào công khai / đòi quyền | `help_center/controller.py`, `faq/controller.py` | đúng |
| Giới hạn nhập file (2 MB · 30 file), cách lấy tiêu đề, bộ lọc HTML | `help_center/import_service.py` | đúng |
| Hai khu vực, bàn giao phiên, bố cục khu người dùng, trình soạn thảo | `help-center/README.md` + `help-center/src/` | đúng |
| Lịch sử CR-019 / 038 / 052 / 053 / 054 / 056 | `doc/tai-lieu-ky-thuat/change-log.md` | đúng |

Đây là **lần đầu** phân hệ này có tài liệu chức năng; trước đó toàn bộ mô tả chỉ nằm ở `help-center/README.md` (thiên về kỹ thuật) và các dòng CR trong change-log.
