# KIẾN TRÚC TỔNG THỂ — NỀN ERP V2

Bản 1.0 — 28/08/2026. Mô tả hiện trạng đang chạy, không phải kế hoạch.

## 1. Hệ thống là gì bây giờ

Từ Mini Tool Thu mua (một luồng nghiệp vụ, một giao diện), hệ đã nở thành **nền ERP nhiều phân hệ**:
vào web thấy màn chọn phân hệ dạng lưới thẻ, ai có quyền tới đâu thấy tới đó. Các phân hệ đang chạy
thật: **Thu mua · Sản xuất (danh mục) · Kho · Tài chính · Nhân sự · Văn thư · Phê duyệt ·
Diễn đàn · Hỗ trợ · Trợ lý AI · Quản trị**, cộng Trung tâm HDSD chạy app riêng.

Ba nguyên tắc từ [`doc/erp/README.md`](../README.md) vẫn là luật gốc:

1. Cơ sở dữ liệu cũ **chỉ thêm, không sửa** — Thu mua đang chạy thật, không có cửa sổ dừng hệ.
2. Thu mua **không được gián đoạn** — mọi thay đổi giao diện có đường lui.
3. **Khai một chỗ, dùng nhiều chỗ** — danh sách phân hệ, entity, bộ mã trạng thái khai đúng một nơi.

## 2. Hai nhánh, hai giao diện, một backend

| | `main` (prod) | `erp-v2` (dev) |
|---|---|---|
| Giao diện | `frontend/` (React 18, **đóng băng** — chỉ sửa lỗi, D-026) + `help-center/` | `frontend-v2/` (React 19 + Vite + Tailwind 4 + shadcn + TanStack Query) |
| Backend | dùng chung `backend/` — v2 gọi đúng `/api/...` cũ, đúng phong bì `{success, message, data}` | như prod, cộng các migration/module mới chưa lên prod |
| Merge | **một chiều `main` → `erp-v2`** — đưa ngược là kéo migration chưa duyệt vào DB thật | |

Chi tiết luật nhánh + lệnh deploy: [`quy-trinh-nhanh-va-deploy.md`](../../tai-lieu-ky-thuat/quy-trinh-nhanh-va-deploy.md) — đọc bản đó, đừng làm theo trí nhớ.

## 3. Các service Docker (local)

`docker compose up` dựng: **db** (MySQL 8) · **api** (FastAPI, tự chạy `alembic upgrade` + seed lúc khởi động)
· **web** (frontend v1, :8080) · **erp** (frontend-v2, :8083) · **help** (Help Center, :8082)
· **adminer** (:8081) · **redis** · **qdrant** · **celery-worker / celery-beat** (việc nền: backup R2, gửi mail)
· **redisinsight**. Code bind-mount nên backend lẫn frontend hot-reload, không cần rebuild khi sửa mã.

Ba môi trường: **local** (tất cả trên) · **dev VPS** (`devthumua`/`deverp`, compose project `procurement-dev`)
· **prod VPS** (`thumua`, `docker-compose.production.yml`). Dev và prod là **hai database trong cùng một MySQL 8.4**,
cách ly file bằng `STORAGE_PREFIX` và email bằng `EMAIL_HARD_OFF`. Sơ đồ ở [`04-so-do-kien-truc.md`](04-so-do-kien-truc.md).

## 4. Khuôn backend — mỗi tính năng một module

`backend/app/modules/<feature>/` gồm `model.py` (SQLAlchemy) · `schema.py` (Pydantic) ·
`service.py` (nghiệp vụ) · `controller.py` (route FastAPI); router nối trong `app/main.py`.
Hạ tầng dùng chung nằm ở `app/core/`: phong bì phản hồi, phân quyền (`permissions/auth/scoping`),
CRUD generic (`crud.py`), lọc + phân trang (`base_controller.py`), audit, danh mục file đính kèm
(`file_registry.py`), bộ mã trạng thái (`status_catalog.py` + `code_sets.py`).

Bốn luật hay bị quên:

- Model mới phải import vào `core/all_models.py`, không thì `alembic --autogenerate` không thấy bảng.
- Endpoint trả qua `success()/error()` — frontend bóc đúng phong bì đó.
- Cột trạng thái/loại/bậc **MỚI** lưu `SMALLINT` + `IntEnum` (QĐ-11); riêng chứng từ Thu mua cũ đi
  mã chuỗi tiếng Anh `draft|submitted|approved` (QĐ-9) — hai khuôn, không trộn trong một chứng từ.
  Bộ mã khai ở `status_catalog.py`, bản TypeScript **sinh tự động** bằng `scripts/gen_status_ts.py`, cấm gõ tay.
- Tên hàm/biến/hằng tiếng Anh; chuỗi hiển thị, comment, tài liệu tiếng Việt.

## 5. Khuôn frontend-v2 — bảng đăng ký phân hệ

Mỗi phân hệ là `src/modules/<tên>/` (`api/ · components/ · config/ · hooks/ · pages/ · types/ ·
utils/ · routes.tsx`), khai một object `ErpModule` trong `routes.tsx` và đăng ký **một dòng** ở
`src/app/router/module-registry.ts`. Màn chọn phân hệ, router, menu trái đều tự suy từ bảng này.

- Hợp đồng `ErpModule` (đọc chú thích trong `src/app/router/module-definition.ts`): `enabled` bật/tắt
  cả phân hệ (tắt = thẻ "Sắp có", không có route); `externalUrl` cho phân hệ chạy app khác (HDSD);
  `customLayout` cho phân hệ tự mang khung (Diễn đàn); `nav[]` khai mục menu kèm **khóa quyền**
  (`entity`/`entities`/`action`/`manage`).
- **Thẻ phân hệ mở khi còn ít nhất một mục menu hiện được** — luật ở
  `src/app/router/module-visibility.ts`, phân tích đầy đủ ở [`03-phan-quyen-va-hien-thi.md`](03-phan-quyen-va-hien-thi.md).
- Tầng dùng chung: `src/core/` (api, auth, authorization, i18n) và `src/shared/` (ui, data-table,
  crud khai báo, conditional-filter). Component riêng của phân hệ không để ở `shared/`.
- Ba cổng phải xanh trước khi giao: `docker compose exec erp npm run check`
  (typecheck 0 lỗi · lint 0 lỗi · test xanh hết). Luật chi tiết: `frontend-v2/.claude/rules/`.

## 6. Những mảng hạ tầng v2 thêm so với v1

| Mảng | Ở đâu | Ghi chú |
|---|---|---|
| Bộ máy duyệt dùng chung | `modules/approval/` | Luồng ký nhiều bước, khai theo loại chứng từ; Văn thư dùng đầu tiên |
| Văn thư | `modules/document/` + `doc_catalog/` | Soạn → ký → ban hành, clone xuống pháp nhân con, chèn chữ ký (CR-192), hộp thư gửi danh nghĩa (CR-184) |
| Diễn đàn nội bộ | `modules/forum/` | FE khung riêng (`customLayout`), thumbnail sinh lúc upload (CR-193) |
| Import/Export tập trung | `modules/import_tool/` + `export_log/` | Chạy thử → ghi thật → hoàn tác theo batch (CR-186) |
| Trợ lý AI | `modules/assistant/` | 29 tool nghiệp vụ, bong bóng chat + trang riêng |
| Thông báo + Web Push | `modules/notification/` + `push/` | Chuông trong app là kênh chính; email qua Brevo, mailbox riêng từng phòng |
| Phiếu hỗ trợ | `modules/ticket/` | Kênh khách báo lỗi/yêu cầu, vai trò `support` |
| Việc nền Celery | `celery-worker/beat` | Backup R2 2 lần/ngày, gửi mail — deploy backend phải build lại cả hai container |
| Đính kèm + thumbnail | `modules/attachment/` + `core/images.py` | Lưu R2, mọi ô đính kèm khai ở `file_registry.py`, trần 50MB (CR-148) |

Mỗi mảng có tài liệu quyết định riêng trong `doc/erp/` hoặc dòng CR trong change-log — bảng này chỉ để biết NÓ TỒN TẠI và nằm đâu.

## 7. Cái gì KHÔNG đổi so với v1

- Luồng nghiệp vụ Thu mua lõi (YCBG → khảo sát → YCMH → ĐMH → nhận hàng → công nợ → YCTT) —
  TDD v1 ([`technical-design.md`](../../tai-lieu-ky-thuat/technical-design.md)) vẫn là bản mô tả đúng.
- `tab_product` là bảng VARIANT (SKU), 7 bảng nối bằng chuỗi `product_code` — luật D-025,
  đọc [`mo-hinh-du-lieu-san-pham.md`](../../tai-lieu-ky-thuat/mo-hinh-du-lieu-san-pham.md) trước khi đụng.
- Hai trục phân quyền backend (`require` + `apply_scope`) — v2 chỉ thêm tầng hiển thị phía trên, xem `03`.
