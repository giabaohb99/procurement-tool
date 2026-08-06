# Help Center — Trung tâm Hướng dẫn sử dụng

App React độc lập cho tài liệu hướng dẫn sử dụng hệ thống Thu mua DEGO Holding.
Tách khỏi `frontend/` nhưng **dùng chung backend** (`/api/v1/help-center`) và **chung tài khoản**.

Stack: React 18 · Vite 5 · TypeScript · **Tailwind CSS v4 + shadcn/ui** · React Router 6 · axios ·
react-quill + quill1-table (trình soạn thảo khu quản trị) · react-easy-crop (cắt ảnh icon) ·
sonner (toast) · lucide-react (icon).

> Giữ React **18** (không lên 19) vì `react-quill@2` chưa hỗ trợ React 19; shadcn/Radix chạy tốt trên React 18.

## Chạy

```bash
# Cùng cả stack (khuyến nghị) — http://localhost:8082
docker compose up -d --build help

# Hoặc chạy tay (cần backend ở http://localhost:8000)
npm install && npm run dev
```

Vite proxy `/api` → `api:8000`, nên không dính CORS. Production build đặt `VITE_API_URL` (domain API thật).

## Tài khoản

| Loại | Đăng nhập | Quyền |
|---|---|---|
| Quản trị HDSD | `helpadmin` (hoặc mã NV `HDSD0001`) · mật khẩu `helpadmin` | CRUD bài viết + slide |
| Admin hệ thống | tài khoản admin sẵn có | CRUD bài viết + slide |
| User còn lại | *không cần đăng nhập* | Chỉ đọc khu người dùng |

Mật khẩu seed đổi qua biến môi trường `HELP_ADMIN_PASSWORD`. Vai trò `help_admin`
chỉ có quyền trên entity `help_article` — không đụng nghiệp vụ / cấu hình hệ thống.

## Hai khu vực

| Khu | Đường dẫn | Giao diện | Ai vào được |
|---|---|---|---|
| **Người dùng** | `/`, `/:id`, `/cau-hoi-thuong-gap` | Portal 3 tầng (xem dưới) + Câu hỏi thường gặp. **Chỉ đọc**. | **Công khai — không cần đăng nhập** |
| **Quản trị** | `/admin`, `/admin/:id`, `/admin/faq`, `/admin/lich-su` | Quản lý bài viết · soạn bài · câu hỏi thường gặp · lịch sử thay đổi | Cần `help_article/write` |

Các endpoint ĐỌC ở backend (`GET /api/v1/help-center/*`, `GET /api/v1/faq`) không yêu cầu token;
mọi endpoint GHI vẫn cần quyền trên entity `help_article`.

### Bàn giao phiên từ app Thu mua

Hai app khác cổng (8080 / 8082) nên **không dùng chung localStorage**. Khi người có quyền
`help_article/write` bấm "Hướng dẫn sử dụng" trong app Thu mua, link được gắn thêm token ở
**hash**: `http://localhost:8082#t=<access>&r=<refresh>` (xem `helpCenterUrl()` trong
`frontend/src/layouts/AppLayout.tsx`). Help Center nạp token vào localStorage, gọi `/api/auth/me`
lấy quyền rồi **xóa hash khỏi URL ngay** — nhờ vậy hiện được nút "Truy cập quản trị" mà admin
không phải đăng nhập lần hai. Hash không được trình duyệt gửi lên server. User thường không kèm
token vì khu người dùng vốn công khai.

### Khu quản trị

| Trang | Chức năng |
|---|---|
| `/admin` | Bảng cây: thêm/xóa, **sửa nhanh tiêu đề tại chỗ** (nút bút chì hoặc nhấp đúp), **kéo-thả** đổi thứ tự + chuyển mục cha, đổi thứ tự bằng nút lên/xuống, lọc theo tiêu đề |
| `/admin/:id` | Soạn bài trên 1 trang: tiêu đề inline · **mô tả ngắn + icon** · trình soạn thảo luôn mở · ảnh từng bước · bài viết con (**chuyển mục cha từng bài**) · lịch sử. Ctrl/⌘+S để lưu |
| `/admin/faq` | Câu hỏi thường gặp: thêm/sửa/xóa, bật-tắt hiển thị, đổi thứ tự |
| `/admin/trang-chu` | **Bố cục trang chủ**: sắp thứ tự / đổi tiêu đề / ẩn-hiện 4 khung, kéo-thả chọn bài viết cho khung, xem trước |
| `/admin/lich-su` | Nhật ký thay đổi của **mọi** bài viết |

Sidebar khu quản trị (`admin-sidebar-nav` + `admin-sidebar-tree-item`): ngoài các trang quản lý còn
có khối "Bài viết liên quan" — bài cha + các bài **cùng cấp**, mỗi bài có bài con thì **sổ xuống**
xem ngay tại đây, và **kéo-thả** đổi mục cha / thứ tự ngay trên sidebar. Nhánh chứa bài đang mở
bung sẵn; trạng thái bung tính **trực tiếp lúc render** (không nhét vào state qua `useEffect`) vì
cây tài liệu tải xong sau lần render đầu — effect chạy trên cây rỗng sẽ ra tập rỗng và không bao
giờ tính lại.

Kéo-thả ở sidebar và ở bảng cây `/admin` dùng chung hook `lib/use-help-tree-dnd.ts` (state + handler
DOM) trên nền logic thuần `lib/help-tree-dnd.ts`. Thứ tự mới luôn tính trên cây **đầy đủ**, nên
sidebar chỉ hiện một phần cây vẫn ghi `sort_order` đúng. Thẻ `<a>` trong dòng phải đặt
`draggable={false}`, nếu không trình duyệt kéo cái link thay vì kéo bài viết.

Cây tài liệu sâu **tối đa 3 cấp**, nhưng chỉ phân biệt 2 loại: **Mục gốc** (cấp 0, hiện thành thẻ
danh mục ở trang người dùng) và **Bài viết** (mọi cấp bên dưới, cấp 1 lẫn cấp 2 đều gọi chung
là bài viết — xem `LEVEL_LABELS` trong `lib/help-article-actions.ts`).

**Xóa bài viết sẽ xóa luôn toàn bộ bài con/cháu bên trong** — hộp thoại xác nhận báo rõ số bài sẽ mất.
Chuyển bài viết bị chặn nếu tạo vòng lặp cây hoặc làm cấu trúc vượt quá 3 cấp.

#### Mô tả ngắn & icon

Bài viết có thêm 2 cột `summary` (mô tả ngắn) và `icon`, nhập ngay ở hộp thoại **Thêm bài viết**
và sửa lại được ở `/admin/:id` (khối "Hiển thị ngoài trang chủ"). Cả hai chỉ dùng để hiển thị
trên thẻ ở khu người dùng:

- **Mô tả ngắn** — dòng chữ dưới tiêu đề trên thẻ. Bỏ trống thì thẻ chỉ hiện tiêu đề
  (KHÔNG chèn câu đếm số bài con thay thế — đó là chữ độn, không mang thông tin).
  Riêng trang danh mục `/:id` thì bài chưa có mô tả sẽ lấy tạm trích đoạn đầu nội dung.
- **Icon** — chọn 1 trong bộ icon dựng sẵn (`lib/help-icons.ts`, lưu slug như `rocket`),
  **hoặc tải ảnh riêng lên**: cắt vuông ngay tại chỗ bằng react-easy-crop → xuất PNG 256px →
  upload qua `/api/v1/help-center/upload-image` → lưu URL vào chính cột `icon`.
  Giá trị bắt đầu bằng `/` hoặc `http` được hiểu là ảnh (xem `isImageIcon`), còn lại là slug.
  Chưa chọn thì khu người dùng tự gán icon mặc định xoay vòng theo vị trí.

Vì `icon` chứa được cả URL nên cột là `String(500)`.

#### Bố cục trang chủ (`/admin/trang-chu`)

Trang 3 cột: **nguồn** (kéo) · **4 khung** (thả) · **xem trước**.

Mỗi khung nhận đúng MỘT loại phần tử — backend quyết định qua `item_kind` và chặn thẳng (400)
nếu gửi sai loại (`SECTION_ITEM_KIND` trong `home_service.py`):

| Khung | `item_kind` | Sửa được gì |
|---|---|---|
| Bắt đầu ngay | `article` | tiêu đề · ẩn/hiện · thứ tự · **kéo bài viết** + nền gradient + ảnh minh họa từng tile |
| Các Phân hệ | `article` | tiêu đề · ẩn/hiện · thứ tự · **kéo bài viết** |
| Không tìm thấy điều bạn cần? | `faq` | tiêu đề · ẩn/hiện · thứ tự · **kéo câu hỏi thường gặp** |
| Mẹo tra cứu | `custom` | tiêu đề · ẩn/hiện · thứ tự · **thẻ tự nhập** (icon + tiêu đề + mô tả) |

- 4 khung là **cố định** (backend seed sẵn ở `tab_help_home_section`), không thêm/xóa khung được.
- `tab_help_home_item` phục vụ cả 3 loại nên `article_id` · `faq_id` · `title/description/icon`
  đều nullable; service bắt buộc đúng nhóm cột theo `item_kind`. Phần tử trỏ tới bài/câu hỏi đã
  xóa bị loại khỏi kết quả; thẻ tự do không tham chiếu gì nên luôn giữ.
- Cột nguồn có 2 tab **Bài viết / Câu hỏi**. Kéo một dòng thả vào khung; kéo tay cầm ⠿ trong khung
  để đổi thứ tự. Nút lên/xuống vẫn giữ để dùng được bằng bàn phím. Kéo-thả dùng `dataTransfer` với
  MIME riêng (`application/x-help-home`) nên không lẫn với kéo-thả cây tài liệu.
- Mỗi khung **tối đa `MAX_HOME_ITEMS` = 6 mục** (vừa đúng 2 hàng lưới 3 cột). Đầy rồi thì thả thêm
  bị từ chối kèm toast và nút "Thêm thẻ" tắt — nhưng **kéo đổi thứ tự vẫn chạy**. Giới hạn này chỉ
  đặt ở frontend: đây là cấu hình hiển thị, chỉ quản trị viên sửa được.
- Mọi thay đổi **ghi ngay xuống server**, không có nút Lưu — đây là cấu hình hiển thị. Riêng ô
  tiêu đề/mô tả thẻ chỉ ghi khi **rời ô**, gõ tới đâu gọi API tới đó thì spam request.
- Khung để trống thì trang chủ dùng **nội dung mặc định** như trước (`firstLeaves` · các mục gốc ·
  thẻ dẫn sang trang FAQ · 3 mẹo trong code), nên hệ mới cài vẫn có nội dung ngay. Gọi API lỗi
  cũng rơi về bố cục mặc định — trang chủ không bao giờ trắng.
- Nền gradient lưu ở backend dưới dạng **slug** (`lib/help-home-skins.ts` ánh xạ sang CSS), đổi
  bảng màu sau này không phải chạy migration.
- Khung xem trước (`help-home-preview.tsx`) dựng lại markup **rút gọn**, không tái dùng `PortalHome`
  (trang thật cần router/slug/trích đoạn nội dung — kéo cả bộ vào khu quản trị chỉ để xem trước là
  quá nặng). Đánh đổi: sửa giao diện trang chủ thì phải sửa cả ở đây cho khớp.

#### Chuyển bài sang mục cha khác

| Chuyển bài nào | Ở đâu |
|---|---|
| Chính bài đang mở | Menu `…` trên đầu trang → **Chuyển sang mục khác** |
| Từng **bài con** | Menu `…` trên mỗi dòng ở khối "Bài viết con" (cột phải) → **Chọn mục cha khác** — khỏi phải mở bài con ra rồi mới chuyển |
| Bài bất kỳ | Kéo-thả ở bảng cây `/admin` hoặc ở sidebar khu quản trị |

Dòng bài con để **một hàng**: icon + tiêu đề (cắt bớt) + hai nút đổi thứ tự + menu `…`. Chỉ để lộ
hai nút lên/xuống vì đó là thao tác cần bấm liên tục; bày đủ 5 nút ra thì cột phải hẹp không đủ chỗ,
tiêu đề bị đẩy xuống hàng riêng và danh sách cao gần gấp đôi.

Tất cả dùng chung `MoveArticleDialog` — chỉ liệt kê nơi hợp lệ qua `validParents`. Thao tác chuyển
**ghi ngay xuống server**, không chờ nút Lưu (đây là thuộc tính cây, không phải nội dung bài), và
bài được đặt xuống **cuối** mục đích (`moveArticle` nhận thêm `sortOrder`) — không thì trùng
`sort_order` với anh em sẵn có ở đó.

#### Kéo-thả ở bảng cây

Kéo tay cầm ⠿ của một dòng rồi thả vào dòng khác:

| Thả vào | Kết quả |
|---|---|
| Mép **trên** dòng đích | Chèn **trước** dòng đó, cùng cấp |
| Mép **dưới** dòng đích | Chèn **sau** dòng đó, cùng cấp |
| **Giữa** dòng đích | Chuyển **vào trong** làm bài con (mục đích tự mở ra) |

Nước thả không hợp lệ (thả vào chính nó, vào bài con của nó, hoặc làm cây vượt 3 cấp) sẽ không
hiện vạch chỉ dẫn và không thả được — logic kiểm tra ở `lib/help-tree-dnd.ts`, phần ghi xuống
server ở `dropArticle` trong `lib/help-article-actions.ts`.

> Kéo-thả **tắt khi đang lọc theo tiêu đề**: lúc đó danh sách là cây đã cắt bớt, tính lại thứ tự
> trên đó sẽ ghi sai `sort_order` của các bài đang bị ẩn. Dùng nút lên/xuống hoặc xóa từ khóa.

Nút **Quản trị** chỉ hiện ở header khi user có quyền ghi; vào thẳng `/admin` mà không có quyền sẽ bị đẩy về `/`.

### Khu người dùng — 3 tầng

Trang danh mục / bài viết tham khảo bố cục help center của MISA (`helpamis.misa.vn`).
**Trang chủ** thì bám theo Trung tâm trợ giúp của hệ Văn thư (`frontvanthu.degoholding.vn/hdsd`)
để hai hệ nhìn đồng bộ — xem bảng token bên dưới.

| Tầng | Đường dẫn | Nội dung |
|---|---|---|
| **Trang chủ** | `/` | Hero nền sáng (gradient `#f0f4ff → #fff`) + tiêu đề lớn canh giữa + ô tìm kiếm bo tròn · 3 tile "Bắt đầu ngay" nền gradient kèm ảnh minh họa · lưới thẻ "Các Phân hệ" · câu hỏi thường gặp · mẹo tra cứu |
| **Danh mục** | `/:id` khi node **có bài con** | Cùng khung với trang bài viết, bỏ cột mục lục: sidebar trái + (breadcrumb · tiêu đề · nội dung mở đầu · **danh sách bài viết dạng thẻ**) |
| **Bài viết** | `/:id` khi node **không có con** | Breadcrumb + **3 cột** (xem dưới) |

`/:slug` tự phân nhánh giữa 2 loại trang trong `pages/portal-node.tsx` dựa vào cây tài liệu.

#### Đường dẫn dạng slug (`lib/help-slug.tsx`)

Khu người dùng đi bằng **slug sinh từ tiêu đề** — `/bao-cao-mua-hang` thay vì `/7`. Slug tính ngay
trên client (cây tài liệu vốn đã tải sẵn ở `PortalLayout`) nên **không cần thêm cột ở DB**;
`SlugIndexProvider` bọc ngoài khu người dùng, mọi chỗ render `<Link>` lấy đường dẫn qua
`useArticlePath()`.

- Trùng slug (hai bài cùng tiêu đề) hoặc đụng đường dẫn cố định (`login` · `admin` ·
  `cau-hoi-thuong-gap`) thì gắn thêm id: `bao-cao-mua-hang-7`.
- Link cũ dạng số vẫn vào đúng bài và **tự đổi sang slug** trên thanh địa chỉ (`Navigate replace`),
  nên nút "Xem trang người dùng" bên khu quản trị (`/{id}`) không cần sửa.
- Khu quản trị vẫn đi theo id (`/admin/:id`) — id ổn định, không đổi khi sửa tiêu đề.
- Đánh đổi: **đổi tiêu đề là đổi đường dẫn**, link cũ gãy. Chấp nhận được vì đây là tài liệu nội bộ,
  người dùng vào bằng menu/tìm kiếm. Muốn đường dẫn cố định thì phải thêm cột `slug` ở backend.

Các trang trong **không còn dải breadcrumb + tìm kiếm nền xám** ở đầu trang (component
`help-topbar` đã xóa): breadcrumb nằm ngay trên tiêu đề trong cột nội dung, ô tìm kiếm dời hẳn
lên header. Khung trang danh mục / bài viết chạy hết chiều ngang với đúng lề của header
(`px-6 md:px-8`, KHÔNG `max-w` + canh giữa) để sidebar thẳng hàng với logo và mục lục thẳng hàng
với cụm tài khoản; chiều rộng dễ đọc do cột giữa tự giới hạn `max-w-3xl`.

#### Trang bài viết — bố cục 3 cột (`components/help-portal-shell.tsx`)

Khung 3 cột dùng chung cho **trang danh mục lẫn trang bài viết**, tham khảo help center của Lark:

| Cột | Thành phần |
|---|---|
| Trái (`w-64`) | `help-section-nav` — toàn bộ mục gốc, bung nhánh đang đọc |
| Giữa | tiêu đề · nội dung · ảnh từng bước · bài trước/tiếp theo |
| Phải (`w-64`) | `help-article-toc` — "Trong bài viết này" |

Cột giữa `mx-auto max-w-3xl flex-1` — **canh giữa** chỗ trống còn lại chứ không dính sát danh mục;
nếu không, màn rộng mà bài không có heading (không dựng cột mục lục) sẽ chừa một dải trắng rất lớn
bên phải. Hai cột bên bám `top-[4.25rem]` (bằng chiều cao header) và tự cuộn riêng khi dài.

**Ba mức bề ngang** (dùng `hooks/use-media-query.ts` — phải biết bề ngang trong JS vì hành vi đổi
hẳn, không chỉ ẩn/hiện bằng class):

| Bề ngang | Danh mục | Mục lục |
|---|---|---|
| ≥ 1280 (`xl`) | cột, bật/tắt được | luôn hiện |
| 1024–1279 (`lg`) | cột, bật/tắt được | **chỉ hiện khi tắt danh mục** |
| < 1024 | **ngăn kéo** phủ lên, mở bằng nút ☰ ở header | ẩn hẳn |

Ở mức `lg` không thể để cả hai: 1024 − 256×2 − lề − khoảng cách còn chưa tới 400px cho nội dung,
đọc không nổi. Nên mục lục "nhường chỗ" cho danh mục và chỉ hiện khi người đọc tự tắt danh mục.
Dưới 1024 danh mục thành ngăn kéo **phủ lên** thay vì đẩy — đẩy thì nội dung chỉ còn vài trăm px.

- Trạng thái đóng/mở nằm ở `portal-layout` (header giữ nút), trang con lấy qua outlet context
  `sidebar`. Trang chủ / câu hỏi thường gặp không có danh mục nên **ẩn luôn nút** — khung 3 cột tự
  báo `setAvailable(true)` lúc mount và `false` lúc unmount.
- Đổi qua màn hẹp thì ngăn kéo tự đóng, và **đóng lại mỗi lần chuyển trang** — không thì bấm một
  bài trong ngăn kéo xong nó vẫn che nội dung vừa mở.
- Dưới `lg` các nút ở header rút còn icon (nhãn giữ trong `title`) — bày đủ chữ thì header tràn
  ngang ngay ở khổ máy tính bảng.

- **Sidebar trái** (`help-section-nav`, dùng chung cho cả trang danh mục): liệt kê **toàn bộ mục
  gốc** (bám theo help center của Lark) và **chỉ bung nhánh chứa bài đang đọc**. Bài đang đọc tô
  nền `accent` + chữ primary; mũi tên bên trái để đóng/mở tay.
  Mỗi lần chuyển bài, trạng thái bung được **đặt lại** theo đúng nhánh mới chứ không gộp thêm vào
  cái cũ — gộp thì đọc vài bài là cả cây bung hết, sidebar dài không tra được.
  (Trước đây sidebar chỉ hiện đúng cụm của mục gốc đang mở; đổi vì người đọc không thấy hệ thống
  tài liệu còn những phần nào và phải quay về trang chủ mới đi tiếp được.)
- **Mục lục phải**: một đường kẻ dọc chạy dọc danh sách, mục đang đọc tô primary + vạch đậm
  (bỏ kiểu khung/nền thẻ cũ).
- Box "Bài viết liên quan" / "Bài viết trong mục" / "Nhóm nghiệp vụ khác" và link "Về mục cha" đã
  **bỏ** — sidebar trái đã liệt kê đúng các bài cùng cụm, giữ lại là lặp nội dung.

Ở **trang danh mục**, danh sách bài con để dạng **thẻ bấm được** (icon + tiêu đề + trích đoạn cắt
2 dòng) dưới nhãn "BÀI VIẾT TRONG MỤC", tách hẳn khỏi phần văn bản mở đầu; nội dung mở đầu dùng
thêm class `hc-content--intro` để hạ cỡ `h1/h2` xuống dưới tiêu đề mục. Trước đây cả hai đều là
chữ đậm + gạch ngang cỡ gần bằng nhau nên không phân biệt được đâu là nội dung, đâu là link
sang bài khác.
Header: logo + gạch dọc + **"Trung tâm trợ giúp"** (18px, in đậm) bên trái; kế đó là **thanh nav
chính**; bên phải là Câu hỏi thường gặp + nút Quản trị (nếu có quyền) + menu tài khoản.

#### Thanh nav chính (`components/help-main-nav.tsx`)

Nhãn nav là **nhóm ngắn gọn** khai báo trong hằng `NAV_GROUPS`, các **mục gốc** nằm trong menu
xổ xuống. KHÔNG lấy tiêu đề mục gốc làm nhãn nav — tiêu đề kiểu "2. Dành cho Phòng ban (Người
Yêu Cầu)" đưa ngang lên header sẽ bị cắt cụt, đọc không ra.

| Nhóm | Mục gốc thuộc nhóm | Menu xổ xuống hiện gì |
|---|---|---|
| Bắt đầu | `Bắt đầu` · `1.` … | **3 lối tắt của khối "Bắt đầu ngay"** ở trang chủ (`quickStart: true`) |
| Sử dụng | `2.` · `3.` · `4.` … | các mục gốc của nhóm |
| Tài nguyên khác | `5.` · `6.` … | các mục gốc + link tĩnh **Câu hỏi thường gặp** |

Nhóm "Bắt đầu" và tile "Bắt đầu ngay" dùng chung `firstLeaves()` (`lib/help-tree.ts`) nên luôn
trỏ tới đúng một bộ bài — sửa cây tài liệu là cả hai đổi theo.

- Menu mở khi **rê chuột** (bấm vẫn mở được), đóng trễ `CLOSE_DELAY = 150ms` để chuột kịp đi từ
  nhãn xuống menu — Radix DropdownMenu vốn chỉ mở bằng click nên `open` được điều khiển tay.
  Hai điều kiện bắt buộc để hover không bị giật:
  - **`modal={false}`** — ở chế độ modal (mặc định), Radix đặt `pointer-events: none` lên `<body>`
    khi menu mở, nút nav mất hover ngay → `mouseleave` → menu đóng → body được trả lại →
    chuột vẫn nằm trên nút → `mouseenter` → mở lại… lặp vô hạn, menu nhấp nháy ~3 lần/giây.
  - **`openLabel` giữ ở cấp thanh nav**, không phải trong từng mục — nếu mỗi mục tự giữ state,
    rê ngang sang nhóm khác sẽ có ~150ms hai menu cùng mở, chồng lên nhau.
- Gom theo **tiền tố tiêu đề** (`prefixes`), không theo id — để local và prod dùng chung cấu hình.
- Mục gốc không khớp nhóm nào **rơi vào nhóm cuối**, nên thêm mục gốc mới ở `/admin` vẫn lên nav;
  muốn xếp đúng nhóm thì bổ sung tiền tố vào `NAV_GROUPS`.
- Nav **không** đánh dấu mục đang đọc: breadcrumb + sidebar trái đã chỉ rõ đang ở đâu, nav chỉ để
  nhảy nhanh sang nhóm khác.
- Menu rộng rãi hơn mặc định shadcn (`w-72`, item `px-4 py-2.5`, chữ 15px, cho **xuống dòng**
  thay vì cắt cụt) để khớp mẫu của hệ Văn thư.
- Ẩn dưới breakpoint `xl`; ở màn nhỏ người dùng dùng lưới thẻ "Các Phân hệ" ở trang chủ.

#### Ô tìm kiếm trên header

Đây là ô tìm kiếm **duy nhất** của khu người dùng, luôn hiện (từ `md`) — trừ khi đang ở **đầu
trang chủ**, vì lúc đó ô lớn giữa hero đang hiển thị. `portal-layout` dùng `IntersectionObserver`
theo dõi `#hc-hero-search` (hằng `HERO_SEARCH_ID`) với `rootMargin` bằng chiều cao header, nên ô
trên header xuất hiện đúng lúc ô lớn chui xuống dưới header. Trang không có ô lớn thì hiện luôn.

Ô này `flex-1 max-w-64 min-w-32` (co giãn theo chỗ trống) nên khi header chật nó tự hẹp lại thay
vì đẩy tràn. Thanh nav chỉ hiện từ `xl` cũng vì lý do này.

#### Token giao diện trang chủ

Lấy từ Trung tâm trợ giúp hệ Văn thư, khai báo trong `index.css`:

| Token | Giá trị | Dùng ở |
|---|---|---|
| `--ink` | `#1f2329` | Tiêu đề, chữ đậm trên trang chủ (gần đen, KHÔNG dùng navy `#1b2559`) |
| `--ink-muted` | `#646a73` | Mô tả dưới tiêu đề thẻ |
| `--hairline` | `#dee0e3` | Đường kẻ mảnh |

Quy ước còn lại: thẻ nền trắng **không viền** + `shadow-[0_4px_12px_rgba(0,0,0,.03)]`, bo `12px`
(tile hero `16px`), icon ô vuông `48px` nền `bg-primary/8`, tiêu đề mục `28px/700` canh giữa,
khoảng cách giữa các mục `80px`. Ảnh minh họa 3 tile ở `public/hc_overview.png` ·
`hc_new_user.png` · `hc_admin.png`.

## Cấu trúc

```
src/
├─ components/ui/          # component shadcn (npx shadcn@latest add ...)
├─ components/             # component nghiệp vụ: help-search-box · help-breadcrumb ·
│                          # help-main-nav (nav chính ở header: NAV_GROUPS + mục gốc) ·
│                          # help-section-nav (sidebar cây tài liệu ở trang bài viết) ·
│                          # help-topbar · help-category-tiles · help-article-toc ·
│                          # help-article-slides · help-audit-timeline · help-tree-nav ·
│                          # help-article-tree-table + help-article-tree-row (bảng cây + kéo-thả) ·
│                          # admin-sidebar-nav + admin-sidebar-tree-item (sidebar quản trị:
│                          #   sổ xuống xem bài con + kéo-thả đổi mục cha) ·
│                          # help-icon-picker (chọn icon / tải ảnh + cắt) ·
│                          # help-article-icon (render icon: component lucide hoặc <img>) ·
│                          # help-rich-editor (Quill dùng chung) + help-editor-extras
│                          #   (3 nút portal vào thanh công cụ: Bảng · Nhúng mã · Mã HTML) ·
│                          # embed-code-dialog (dán mã nhúng + xem trước) ·
│                          # help-portal-shell (khung 3 cột khu người dùng + ngăn kéo danh mục) ·
│                          # help-home-source-panel + help-home-item-list + help-home-preview
│                          #   (trang Bố cục trang chủ: kéo-thả bài/câu hỏi + thẻ tự do + xem trước) ·
│                          # confirm-dialog (askConfirm/askPrompt) ·
│                          # create-article-dialog (askNewArticle: tiêu đề + mô tả ngắn + icon)
├─ layouts/                # portal-layout (khu người dùng) · admin-layout (khu quản trị)
├─ pages/                  # login · portal-home · portal-node · portal-category ·
│                          # portal-article · admin-home · admin-article
├─ hooks/use-heading-toc.ts   # sinh mục lục + theo dõi heading đang đọc
├─ lib/help-slug.tsx       # slug từ tiêu đề + tra ngược slug -> id (đường dẫn khu người dùng)
├─ lib/quill-vietnamese-labels.ts  # tooltip + gợi ý tiếng Việt cho thanh công cụ soạn thảo
├─ lib/quill-table-actions.ts  # đăng ký + gọi module bảng quill1-table (lệnh, phím tắt bắt buộc)
├─ lib/quill-table-column-resize.ts  # kéo giãn cột + nới blot ô để LƯU được độ rộng
├─ lib/use-help-tree-dnd.ts    # state kéo-thả cây, dùng chung bảng cây /admin + sidebar quản trị
├─ lib/help-home-api.ts        # gọi API cấu hình 4 khung trang chủ (/api/v1/help-center/home)
├─ lib/help-home-skins.ts      # slug nền gradient + ảnh minh họa cho tile "Bắt đầu ngay"
├─ hooks/use-media-query.ts    # bề ngang màn hình trong JS (sidebar cột hay ngăn kéo)
├─ lib/quill-html-embed.ts     # blot "mã nhúng": bọc code nhà cung cấp vào iframe srcdoc
├─ lib/help-tree.ts        # dựng cây · breadcrumb · tìm node/cha
├─ lib/help-tree-dnd.ts    # logic thuần cho kéo-thả: vị trí thả + kiểm tra hợp lệ
├─ lib/help-icons.ts       # bộ icon dựng sẵn (slug -> component) + isImageIcon
├─ lib/crop-image.ts       # cắt ảnh bằng canvas -> File PNG 256px để upload
├─ lib/utils.ts            # cn() gộp class Tailwind · excerptFromHtml()
├─ api/client.ts           # axios + auto refresh token
├─ auth/auth-context.tsx   # login/logout + can(entity, action)
├─ index.css               # Tailwind v4 + token màu shadcn ánh xạ theo DEGO (teal/navy)
└─ styles/article-content.css  # kiểu chữ cho HTML từ Quill (.hc-content) + editor
```

### Thêm component shadcn

```bash
npx shadcn@latest add <tên-component>
```

#### Trình soạn thảo dùng chung (`components/help-rich-editor.tsx`)

Bài viết (`/admin/:id`) và câu trả lời FAQ (`/admin/faq/:id`) dùng **cùng một** component; khác
nhau đúng ở prop `compact` (thanh công cụ rút gọn cho FAQ). Trước đây mỗi trang tự dựng Quill nên
thêm tính năng phải sửa hai chỗ.

Ba nút riêng — **Bảng · Nhúng mã · Mã HTML** — được `createPortal` thẳng vào thanh công cụ do
Quill dựng, nên tất cả nằm trên **một hàng** (`.hc-editor-extras` ở cuối `.ql-toolbar`). Không tự
dựng lại toàn bộ thanh công cụ (Quill có hỗ trợ truyền container tự viết) vì như vậy phải chép lại
toàn bộ markup picker của Quill. Quill bỏ qua mọi phần tử không mang class `ql-*` nên nút shadcn
nằm trong đó vẫn an toàn — nhưng **CSS thì không**: `quill.snow.css` áp cho mọi `<button>` trong
`.ql-toolbar` ba thứ phải gỡ hết trong `article-content.css`, nếu không nút sẽ hỏng theo kiểu khó
đoán:

| Quy tắc của Quill | Hậu quả nếu không gỡ |
|---|---|
| `width: 28px; height: 24px` | nhãn/khổ nút bị bóp |
| `background: none` | nút đang bật mất nền → chữ trắng trên nền trắng, tưởng như biến mất |
| `svg { float: left; height: 100% }` | `height:100%` không có mốc → nút cao đúng 16px |

Vì `background: none` (2 lớp + thẻ) thắng class tiện ích `bg-primary` (1 lớp), trạng thái **đang
bật** của nút Mã HTML tô bằng CSS qua `button[data-active='true']` chứ không dùng
`variant="default"` của shadcn.

**Bảng** — Quill 1.3.7 (bản `react-quill@2` dùng) **không** có module bảng: bật
`modules: { table: true }` sẽ ném `moduleClass is not a constructor`. Dùng **`quill1-table`** (port
của quill-better-table sang Quill 1, không kéo theo dependency runtime). Menu Bảng gọi thẳng
handler `table` mà module tự đăng ký vào thanh công cụ, nhờ vậy giữ được giao diện shadcn + nhãn
tiếng Việt (xem `lib/quill-table-actions.ts`). Có lưới chọn nhanh tới 6×6, ô nhập số hàng/cột cho
bảng lớn hơn, thêm/xóa hàng cột, gộp/tách ô.

- `TABLE_KEYBOARD_BINDINGS` là **bắt buộc** — Quill gắn handler mặc định ngay lúc khởi tạo nên chỉ
  chặn được bằng cách khai báo từ đầu; thiếu nó thì Backspace/Delete trong ô phá cấu trúc bảng và
  Ctrl+Z không hoàn tác đúng.
- Thư viện chỉ sinh `<td>`, **không có `<th>`** — hàng đầu tiên được tô như dòng tiêu đề bằng CSS
  (`table tr:first-child td`). Bảng viết tay bằng `<th>` không bị ảnh hưởng.
- Ô đang chọn tô `#cce0f8` + viền trong màu primary, đặt SAU quy tắc hàng tiêu đề để thắng độ ưu
  tiên — nếu không, gộp ô ở hàng đầu thành ra mò mẫm.
- **Kéo giãn cột** (`lib/quill-table-column-resize.ts`): rê tới mép phải một ô, con trỏ đổi thành
  `col-resize` rồi kéo. Blot của thư viện chỉ round-trip đúng 7 thuộc tính
  (`table_id|row_id|cell_id|merge_id|colspan|rowspan|hide_border`) — mọi `style`/`class` khác đặt
  lên `<td>` đều **mất khi tải lại bài**. Nên phải: (a) nới blot ô thêm **trường thứ 8** = độ rộng,
  (b) thêm matcher `TD, TH` đọc lại độ rộng khi nạp HTML. Matcher này **phải gắn theo từng
  instance sau khi module bảng dựng xong** — matcher của thư viện ghi đè thuộc tính `td` bằng đúng
  7 trường, cái nào chạy trước sẽ bị xoá mất phần độ rộng. Gắn trong `useEffect` lúc mount là kịp,
  vì lúc đó `value` còn rỗng, nội dung bài tải xong mới được dán vào.
  Độ rộng ghi lên **mọi ô cùng cột** (không chỉ hàng đầu) để xoá hàng nào cũng không mất.
  ⚠️ Đây là chỗ bám vào cấu trúc bên trong quill1-table — nâng cấp thư viện thì kiểm tra lại
  `TableCellBlot.formats()` và matcher `TD, TH` trong `index.js` của nó.
- ⚠️ **Chưa làm** tô màu nền ô cố định: cũng vướng đúng giới hạn round-trip ở trên.

**Mã HTML** — bật/tắt giữa soạn trực quan và sửa mã nguồn. Ở chế độ mã HTML, Quill **vẫn nằm
nguyên trong DOM** (chỉ ẩn `.ql-container` + các nhóm nút) và nhận một giá trị **đông cứng**: đẩy
từng ký tự đang gõ vào Quill thì nó chuẩn hóa lại và nuốt mất thẻ lạ ngay trong lúc gõ. Lưu ở chế
độ này thì HTML giữ nguyên; bấm *Soạn trực quan* mới để Quill dựng lại (và bỏ thẻ nó không hiểu).

#### Thanh công cụ soạn thảo

Quill không tự gắn tooltip cho nút nào và nhãn ô dán URL là tiếng Anh — đã bù cả hai:

- `lib/quill-vietnamese-labels.ts` gắn `title` cho từng nút + đổi gợi ý trong ô dán URL
  (gọi ở `useEffect` của `admin-article` và `admin-faq-editor`, chạy lại được nhiều lần).
- Nhãn còn lại của ô dán URL (`Dán URL nhúng:` · `Lưu` · `Sửa` · `Xóa`) đổi bằng CSS trong
  `styles/article-content.css`; file này cũng **ghim ô đó vào trong khung soạn thảo** —
  Quill đặt `left` theo vị trí con trỏ nên ô hay lòi ra ngoài và bị cắt mất đầu URL.

#### Nhúng video / demo tương tác (Guideflow, YouTube…)

Hai đường, chọn theo thứ người ta đưa cho:

| Có gì trong tay | Dùng nút | Kết quả |
|---|---|---|
| Chỉ **URL nhúng** (vd `https://app.guideflow.com/embed/qp71yw8sxp`) | **video (▶)** | `<iframe class="ql-video">`, CSS `.hc-content iframe` ép khổ 16:9 |
| **Cả đoạn code** `<div>` + `<iframe>` + `<script>` | **Nhúng mã (`</>`)** | Khối `div.hc-embed` chứa iframe `srcdoc` |

Nút **Nhúng mã** mở hộp thoại dán code, xem trước tại chỗ rồi mới chèn (`embed-code-dialog.tsx`).
Dán đúng 1 thẻ `<iframe>` và không ép chiều cao thì nó tự đi đường nhẹ hơn (embed `video` sẵn có
của Quill); còn lại mới bọc `srcdoc`.

Vì sao phải bọc `srcdoc` (`lib/quill-html-embed.ts`) thay vì chèn thẳng HTML:

- Quill chỉ giữ format đã đăng ký nên thẻ/thuộc tính lạ bị lột sạch khi dán vào editor.
- Nội dung bài render bằng `dangerouslySetInnerHTML`, mà **`<script>` chèn qua innerHTML thì
  trình duyệt không chạy** — script của nhà cung cấp sẽ nằm im dù có lưu được vào DB.

Đưa cả đoạn code vào `srcdoc` giải quyết cả hai: trình duyệt dựng một tài liệu con hoàn chỉnh nên
script chạy được, đồng thời CSS/JS của bên thứ ba bị nhốt trong iframe (`sandbox` bật đủ quyền cho
embed thương mại — nội dung do quản trị viên tự dán nên tin được). Mã gốc lưu base64 ở `data-embed`
để mở lại bài vẫn dựng lại và sửa được; khung mặc định 16:9, nhập chiều cao thì đè bằng inline
style. Chỉ nhận URL `http(s)` — chặn `javascript:`/`data:` lọt vào `src`.

## Câu hỏi thường gặp

Bảng `tab_faq` (`question` · `answer` HTML · `sort_order` · `is_active`), API `/api/v1/faq`.
Dùng chung quyền `help_article` với bài viết nên **không phát sinh entity quyền mới**.
Trang người dùng gọi `?active_only=true` để bỏ câu đang ẩn.

## Khi có lỗi

| Tình huống | Người dùng thấy gì |
|---|---|
| Slug không khớp bài nào (đổi tiêu đề, bài bị xóa) | Thẻ "Không tìm thấy bài viết" — vẫn còn header, menu, ô tìm kiếm để đi tiếp |
| URL hỏng (vd dán thiếu ký tự: `/bao-cao-mua-hang%`) | **Prod**: nginx `error_page 400 404 = /index.html` trả SPA -> hiện như trên. **Dev**: Vite dev server tự ném "URI malformed", không sửa được từ app (chỉ có ở môi trường dev) |
| Lỗi render bất kỳ | `components/app-error-boundary.tsx` — thẻ "Trang gặp sự cố" + nội dung lỗi + nút Tải lại / Về trang chủ. **Không bao giờ để trang trắng** |
| Lỗi gọi API | Interceptor ở `api/client.ts` tự toast (trừ khi đặt `config._silent`) |

## Tìm kiếm

Backend `GET /api/v1/help-center/search?q=` khớp **cả tiêu đề lẫn nội dung**, trả về:
`{id, title, parent_id, in_title, snippet, match_at, match_len}` — `snippet` là đoạn trích quanh
từ khóa (đã bỏ HTML), `match_at/match_len` để client bôi đậm đúng chỗ khớp. Gõ **không dấu**
vẫn khớp (MySQL `utf8mb4_general_ci`; offset tính bằng hàm bỏ dấu giữ nguyên độ dài).
Bài khớp tiêu đề xếp trước.

> Lưu ý dev:
> - Thêm file CSS mới xong phải `docker compose restart help` — Vite trong container không nhận
>   file style tạo sau khi server đã chạy.
> - Đổi `package.json` phải chạy `docker compose up -d --build --force-recreate --renew-anon-volumes help`
>   — `node_modules` nằm trong anonymous volume nên `--build` thôi là chưa đủ.
