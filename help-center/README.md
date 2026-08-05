# Help Center — Trung tâm Hướng dẫn sử dụng

App React độc lập cho tài liệu hướng dẫn sử dụng hệ thống Thu mua DEGO Holding.
Tách khỏi `frontend/` nhưng **dùng chung backend** (`/api/v1/help-center`) và **chung tài khoản**.

Stack: React 18 · Vite 5 · TypeScript · **Tailwind CSS v4 + shadcn/ui** · React Router 6 · axios ·
react-quill (trình soạn thảo khu quản trị) · react-easy-crop (cắt ảnh icon) · sonner (toast) ·
lucide-react (icon).

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
| `/admin` | Bảng cây: thêm/sửa/xóa, **kéo-thả** đổi thứ tự + chuyển mục cha, đổi thứ tự bằng nút lên/xuống, lọc theo tiêu đề |
| `/admin/:id` | Soạn bài trên 1 trang: tiêu đề inline · **mô tả ngắn + icon** · trình soạn thảo luôn mở · ảnh từng bước · bài viết con · lịch sử. Ctrl/⌘+S để lưu |
| `/admin/faq` | Câu hỏi thường gặp: thêm/sửa/xóa, bật-tắt hiển thị, đổi thứ tự |
| `/admin/lich-su` | Nhật ký thay đổi của **mọi** bài viết |

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

#### Trang bài viết — bố cục 3 cột

Bố cục giống khu quản trị (sidebar + nội dung), tham khảo help center của Lark:

| Cột | Thành phần | Ẩn khi |
|---|---|---|
| Trái (`w-64`) | `help-section-nav` — cây tài liệu của **mục gốc đang đọc** | `< lg` |
| Giữa | tiêu đề · nội dung · ảnh từng bước · bài trước/tiếp theo | — |
| Phải (`w-64`) | `help-article-toc` — "Trong bài viết này" | `< xl` |

Hai cột hai bên `sticky top-[4.25rem]` (bằng chiều cao header) và tự cuộn riêng khi dài.

- **Sidebar trái** (`help-section-nav`, dùng chung cho cả trang danh mục): luôn bám theo **mục gốc**
  của trang đang mở và liệt kê **trọn** các bài bên trong nó, nên đi lại trong cùng một cụm thì
  sidebar không đổi. Bài đang đọc tô nền `accent` + chữ primary, nhánh chứa nó **tự bung**; mũi tên
  bên trái để đóng/mở thư mục. Mục gốc là **bài đơn** (không có bài con) thì sidebar chỉ hiện đúng
  bài đó — KHÔNG đôn các mục gốc khác vào cho đầy, vì như vậy bấm sang cụm khác sidebar sẽ đổi
  hoàn toàn, người đọc mất phương hướng.
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
│                          # help-icon-picker (chọn icon / tải ảnh + cắt) ·
│                          # help-article-icon (render icon: component lucide hoặc <img>) ·
│                          # confirm-dialog (askConfirm/askPrompt) ·
│                          # create-article-dialog (askNewArticle: tiêu đề + mô tả ngắn + icon)
├─ layouts/                # portal-layout (khu người dùng) · admin-layout (khu quản trị)
├─ pages/                  # login · portal-home · portal-node · portal-category ·
│                          # portal-article · admin-home · admin-article
├─ hooks/use-heading-toc.ts   # sinh mục lục + theo dõi heading đang đọc
├─ lib/help-slug.tsx       # slug từ tiêu đề + tra ngược slug -> id (đường dẫn khu người dùng)
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

## Câu hỏi thường gặp

Bảng `tab_faq` (`question` · `answer` HTML · `sort_order` · `is_active`), API `/api/v1/faq`.
Dùng chung quyền `help_article` với bài viết nên **không phát sinh entity quyền mới**.
Trang người dùng gọi `?active_only=true` để bỏ câu đang ẩn.

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
