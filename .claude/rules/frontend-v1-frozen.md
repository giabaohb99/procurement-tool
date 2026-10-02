---
paths:
  - "frontend/**"
  - "help-center/**"
---
# `frontend/` — bản đang chạy thật (đóng băng)

> Chuyển nguyên văn từ CLAUDE.md gốc ngày 01/10/2026 — chỉ nạp khi làm việc với các đường dẫn ở trên.

**Config-driven CRUD.** Most list/detail screens are declared as data in `src/config/cruds.tsx` (`CrudConfig`: columns, fields, filters, entity, apiPath) and rendered generically by `components/CrudList.tsx` + `components/CrudDetail.tsx`. Routing in `App.tsx`: the catch-all `:entity` / `:entity/:id` routes drive these; anything needing bespoke logic (PurchaseRequestDetail, SurveyDetail, PurchaseOrderDetail, Reports, RolePermissions, print pages, …) gets an explicit route + a page in `src/pages/`. **To add a simple screen, add a config entry; only write a page when behavior is genuinely custom.**

**Auth & gating.** `auth/AuthContext.tsx` exposes `can(entity, action)` backed by the permissions map returned at login. Use it to hide menu items / action buttons and lock fields. This is UI-only convenience — the backend `require`/`apply_scope` is the real enforcement, so never rely on `can()` for security.

**Help Center is a separate app.** `help-center/` (React 18 + Vite + **Tailwind v4 + shadcn/ui** — KHÁC stack plain-CSS của `frontend/`) chạy độc lập ở cổng 8082, **dùng chung backend + tài khoản**. Menu "Hướng dẫn sử dụng" trong `frontend/` chỉ là link ra ngoài (`VITE_HELP_URL`) — không còn route `/hdsd`. Quyền ghi tài liệu = entity `help_article` (vai trò `help_admin` seed sẵn, đăng nhập `helpadmin`). Chi tiết: `help-center/README.md`.

**Money formatting.** Never call `toLocaleString('vi-VN')` straight on an amount — it defaults to 3 fraction digits, so cents leak into list columns (`4.760.000,08 đ`). Use `src/utils/money.ts`: `fmtVND` for TIỀN (rounds to đồng) and `fmtPrice` for ĐƠN GIÁ (keeps all 4 decimals allowed since migration `d4b9e7c1a305`). Display-only — stored values stay exact.

**API client.** `src/api/client.ts` — axios instance with a request interceptor injecting the Bearer token and a response interceptor that auto-refreshes the access token once on 401 (via `/api/auth/refresh`) then retries, logging out on failure. Non-GET errors auto-toast unless `config._silent` is set.
