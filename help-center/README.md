# Help Center — Trung tâm Hướng dẫn sử dụng

App React độc lập cho tài liệu hướng dẫn sử dụng hệ thống Thu mua DEGO Holding.
Tách khỏi `frontend/` nhưng **dùng chung backend** (`/api/v1/help-center`) và **chung tài khoản**.

Stack: React 18 · Vite 5 · TypeScript · **Tailwind CSS v4 + shadcn/ui** · React Router 6 · axios ·
react-quill (trình soạn thảo khu quản trị) · sonner (toast) · lucide-react (icon).

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
| User còn lại | tài khoản nội bộ bất kỳ | Chỉ đọc |

Mật khẩu seed đổi qua biến môi trường `HELP_ADMIN_PASSWORD`. Vai trò `help_admin`
chỉ có quyền trên entity `help_article` — không đụng nghiệp vụ / cấu hình hệ thống.

## Hai khu vực

| Khu | Đường dẫn | Giao diện | Ai vào được |
|---|---|---|---|
| **Người dùng** | `/`, `/:id` | Portal 3 tầng (xem dưới). **Chỉ đọc**. | Mọi user đăng nhập |
| **Quản trị** | `/admin`, `/admin/:id` | Sidebar cây + trình soạn thảo, quản lý slide, lịch sử chỉnh sửa | Cần `help_article/write` |

Nút **Quản trị** chỉ hiện ở header khi user có quyền ghi; vào thẳng `/admin` mà không có quyền sẽ bị đẩy về `/`.

### Khu người dùng — 3 tầng

Bố cục tham khảo help center của MISA (`helpamis.misa.vn`).

| Tầng | Đường dẫn | Nội dung |
|---|---|---|
| **Trang chủ** | `/` | Hero gradient + vòm cong + ô tìm kiếm lớn · 3 thẻ "bắt đầu nhanh" nổi đè hero · lưới thẻ danh mục (icon tròn canh giữa) · mẹo tra cứu |
| **Danh mục** | `/:id` khi node **có bài con** | Thanh breadcrumb nền xám + ô tìm kiếm · 2 cột: danh sách bài viết (tiêu đề + trích đoạn) · box "Bài viết trong mục" / "Nhóm nghiệp vụ khác" |
| **Bài viết** | `/:id` khi node **không có con** | Thanh breadcrumb + tìm kiếm · 2 cột: nội dung · box "Nội dung" (mục lục sticky, mục đang đọc tô nền primary) + "Bài viết liên quan" |

`/:id` tự phân nhánh giữa 2 loại trang trong `pages/portal-node.tsx` dựa vào cây tài liệu.
Header chỉ có logo trái + nút Quản trị (nếu có quyền) + menu tài khoản.

## Cấu trúc

```
src/
├─ components/ui/          # component shadcn (npx shadcn@latest add ...)
├─ components/             # component nghiệp vụ: help-search-box · help-breadcrumb ·
│                          # help-topbar · help-category-tiles · help-article-toc ·
│                          # help-article-slides · help-audit-timeline · help-tree-nav ·
│                          # confirm-dialog (askConfirm/askPrompt)
├─ layouts/                # portal-layout (khu người dùng) · admin-layout (khu quản trị)
├─ pages/                  # login · portal-home · portal-node · portal-category ·
│                          # portal-article · admin-home · admin-article
├─ hooks/use-heading-toc.ts   # sinh mục lục + theo dõi heading đang đọc
├─ lib/help-tree.ts        # dựng cây · breadcrumb · tìm node/cha
├─ lib/utils.ts            # cn() gộp class Tailwind
├─ api/client.ts           # axios + auto refresh token
├─ auth/auth-context.tsx   # login/logout + can(entity, action)
├─ index.css               # Tailwind v4 + token màu shadcn ánh xạ theo DEGO (teal/navy)
└─ styles/article-content.css  # kiểu chữ cho HTML từ Quill (.hc-content) + editor
```

### Thêm component shadcn

```bash
npx shadcn@latest add <tên-component>
```

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
