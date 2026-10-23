# VẬN HÀNH ĐỒNG BỘ APP ĐẶT XE CŨ ↔ ERP — sổ tay cho người trực

| | |
|---|---|
| Bản | 1.0 — 23/10/2026 (bao-CR-660) |
| Dùng khi | cần biết hệ nào đang nối với hệ nào, bật / tắt ở đâu, đẩy mã app cũ thế nào, kiểm Worker trên Cloudflare, tra phiếu không sang, và thông tin dev / prod của app cũ |
| Thiết kế | [`mo-ta-ky-thuat.md`](mo-ta-ky-thuat.md) (hợp đồng webhook, chữ ký, sổ đồng bộ) · [`p3-erp-sang-app-cu.md`](p3-erp-sang-app-cu.md) (chiều ERP → app cũ) · [`doi-chieu-truong.md`](doi-chieu-truong.md) (ánh xạ trường) |
| Mã | ERP: `backend/app/modules/legacy_datxe/` + `sync_log/` · App cũ: `app đặt xe/my-firebase-api` (Worker) + `app đặt xe/degoholding-app-frontend` (web) |
| Số liệu dưới đây đo lúc | 23/10/2026 11:45, chỉ đọc |

Luật chung của tài liệu này: **không chép khóa, mật khẩu, service account vào đây**. Mọi giá trị bí mật chỉ nêu TÊN và chỗ cất.

---

## 1. Bản đồ hệ thống — dev và prod là HAI BỘ RIÊNG, không chung gì

| Thành phần | DEV | PROD |
|---|---|---|
| Firebase project (RTDB + Auth + Storage) | `api-degoholding` (tên hiển thị *API Degoholding Dev*) | `api-degoholding-com` (số project `676653675722`) |
| Realtime Database | `api-degoholding-default-rtdb.asia-southeast1.firebasedatabase.app` | `api-degoholding-com-default-rtdb.asia-southeast1.firebasedatabase.app` |
| Worker (API app cũ) | `my-firebase-api-dev` → `https://dev-api.degoholding.vn` | `my-firebase-api` → `https://api.degoholding.vn` |
| Web app cũ (Cloudflare Pages `dego-app-frontend`) | nhánh `dev` → `https://dev.app.degoholding.vn` | nhánh `main` → `https://app.degoholding.vn` |
| ERP nhận | `https://deverp.degoholding.vn` (VPS 2 `45.252.248.229`, container `procurement-tool-dev-api-1`, helper `vps2_ssh.py`) | `https://erp.degoholding.vn` (VPS cũ `180.93.2.176`, `~/procurement-tool`, bắt buộc `-f docker-compose.production.yml`, helper `vps_ssh.py`) |
| Công tắc ERP `sync_datxe_enabled` (nhận) | **BẬT** | **BẬT** |
| Công tắc ERP `sync_datxe_outbound_enabled` (gửi, P3) | TẮT | TẮT |
| Worker `SYNC_ENABLED` (app cũ bắn sang ERP) | `"true"` | `"true"` |
| Worker `ERP_INBOUND_ENABLED` (app cũ nhận từ ERP, P3) | `"false"` | `"false"` |
| Worker `SYNC_ERP_BASE` | `https://deverp.degoholding.vn` | `https://erp.degoholding.vn` |
| Nhịp quét lưới an toàn của ERP | 3 phút | 5 phút |
| Sổ đồng bộ ERP (`tab_sync_log`, chiều nhận) | 21 342 thành công · 17 932 bỏ qua · 0 lỗi; chiều gửi 17 thành công (chạy thử 05/10) | 11 356 thành công · 40 976 bỏ qua · 48 lỗi |

Dev **không phải bản sao** của prod (đo 17/09: 0/480 phiếu dev có mặt trong prod). Khóa đọc Firebase theo từng project: cắm nhầm không nổ, chỉ tra trượt sạch và phiếu về ERP thiếu xe.

Tài khoản Cloudflare đang đăng nhập `wrangler` trên máy này: `marketing.degoholding@gmail.com`, Account ID `d74f2df39b62699e41bb0a88d0856fe9`. Tài khoản Firebase Console cùng email đó (Administrator ở cả hai project).

## 2. Hai chiều chạy thế nào (để biết tắt cái gì khi có sự cố)

**Chiều đang chạy thật — app cũ → ERP.** Người dùng tạo / duyệt phiếu trên app cũ → Worker gọi `POST {ERP}/api/sync/datxe/events` ngay trong lượt xử lý (header `X-Sync-Source: datxe`, `X-Sync-Timestamp`, `X-Sync-Signature` = HMAC-SHA256 của `<ts>.<path>.<body>` bằng `SYNC_SHARED_SECRET`, lệch quá 5 phút thì ERP từ chối) → ERP ghi một dòng `tab_sync_log` rồi tạo / cập nhật phiếu `vehicle_booking` / `seal_request` / giao hàng, trả `erp_id`. Nếu móc trượt, ba vòng Celery của ERP vá lại:

| Vòng | Lịch | Làm gì |
|---|---|---|
| `datxe.pull_updated` | mỗi `SYNC_DATXE_PULL_MINUTES` phút (dev 3, prod 5) | đọc Firebase nhánh `requests` có `updatedAt` mới hơn con trỏ lần trước, kéo về |
| `datxe.retry_pending` | phút 3, 13, 23, 33, 43, 53 | chạy lại dòng sổ đang chờ / lỗi (chỉ chiều nhận) |
| `datxe.full_sweep` | 02:15 mỗi ngày | đọc cả nhánh, bỏ con trỏ, dựng lại dữ liệu suy ra — nặng, đừng hạ xuống nhịp phút |
| chuông sổ đồng bộ (bao-CR-449) | 08:00 | báo người trực khi có dòng lỗi quá 24 giờ chưa ai vá |

ERP **chỉ đọc** Firebase (khóa `legacy_firebase_secret`), không bao giờ ghi thẳng: chiều ngược phải qua API Worker.

**Chiều đã dựng, đang KHÓA — ERP → app cũ (P3, bao-CR-596).** Khi bật: ERP ghi dòng sổ OUTBOUND lúc phiếu đổi, Celery `datxe.retry_outbound` (phút 7, 17, …) gửi `POST {Worker}/v1/sync/erp-events` (không có tiền tố `/api`), Worker ghi kết cục vào RTDB. Cần bật **cả ba**: `sync_datxe_enabled` + `sync_datxe_outbound_enabled` bên ERP và `ERP_INBOUND_ENABLED: "true"` bên Worker; chạy tay `datxe.backfill_outbound` một lần để gửi phiếu đang có. Đại ca chốt 05/10: xây xong, chưa triển khai, chưa có hạn.

Tắt khẩn cấp: tắt `sync_datxe_enabled` ở ERP (màn Cấu hình hệ thống ▸ nhóm Đồng bộ) là ngắt cả hai chiều phía ERP; tắt `SYNC_ENABLED` trong `wrangler.jsonc` rồi đẩy nhánh là Worker thôi bắn.

## 3. Cấu hình phía ERP — ở đâu, sửa thế nào

Mọi khóa đều có hai nơi: biến `.env` (giá trị khởi tạo, `seed_app_settings.py` nạp xuống bảng) và **bảng `tab_setting`** là nơi chạy thật, sửa trên màn **Quản trị ▸ Cấu hình hệ thống ▸ nhóm Đồng bộ** (`/system/settings`). Ô bí mật chỉ hiện *đã đặt / chưa đặt*.

| Khóa (`tab_setting` / `.env`) | Ý | Prod hiện | Dev hiện |
|---|---|---|---|
| `sync_datxe_enabled` / `SYNC_DATXE_ENABLED` | cầu dao tổng | bật | bật |
| `sync_datxe_outbound_enabled` / `SYNC_DATXE_OUTBOUND_ENABLED` | chiều gửi P3 | tắt | tắt |
| `sync_legacy_api_base` / `SYNC_LEGACY_API_BASE` | gốc API Worker | `https://api.degoholding.vn` | `https://dev-api.degoholding.vn` |
| `legacy_firebase_db_url` / `LEGACY_FIREBASE_DB_URL` | RTDB app cũ (chỉ đọc) | kho `-com` | kho dev |
| `legacy_firebase_secret` / `LEGACY_FIREBASE_SECRET` | khóa đọc RTDB, **theo từng project** | đã đặt | đã đặt |
| `sync_shared_secret` / `SYNC_SHARED_SECRET` | khóa ký chung hai bên, **khác nhau dev / prod**, phải trùng Secret cùng tên bên Worker | đã đặt | đã đặt |
| `sync_datxe_auto_create` | tra trượt có tự tạo xe / tài xế không | tắt | tắt |
| `SYNC_DATXE_PULL_MINUTES` (chỉ `.env`, cần restart celery-beat) | nhịp quét | 5 | 3 |
| `SYNC_DEFAULT_COMPANY_ID` / `SYNC_NOTIFY_ON_IMPORT` | công ty mặc định `1`; không bắn chuông khi nạp | 1 / tắt | 1 / tắt |

Đọc nhanh trạng thái thật (không in bí mật) — chạy trong container api, qua `python -` với base64 như mọi lệnh VPS khác:

```python
from app.core import app_settings
for k in ("sync_datxe_enabled","sync_datxe_outbound_enabled","sync_legacy_api_base","legacy_firebase_db_url"):
    print(k, app_settings.get(k))
print("shared secret:", "có" if app_settings.get("sync_shared_secret") else "trống")
```

Chạy tay một vòng (trong container api; dev: `docker exec procurement-tool-dev-api-1 …`, prod: `docker compose -f docker-compose.production.yml exec -T api …`):

```bash
python -c "from app.modules.legacy_datxe.tasks import pull_updated_task; print(pull_updated_task())"
python -c "from app.modules.legacy_datxe.tasks import retry_pending_task; print(retry_pending_task())"
python -c "from app.modules.legacy_datxe.tasks import full_sweep_task; print(full_sweep_task())"        # nặng, chạy ngoài giờ
python -c "from app.modules.legacy_datxe.outbound_tasks import backfill_outbound_task; print(backfill_outbound_task())"   # chỉ khi bật P3
```

## 4. Tra một phiếu sang chưa, hỏng vì gì

1. Màn **Quản trị ▸ Sổ đồng bộ** (`/system/sync-logs`, khóa quyền `sync_log`): lọc theo nguồn `datxe`, trạng thái, mã app cũ (`legacy_id`) hay số phiếu ERP. Mỗi dòng có thân gửi tới, câu lỗi, nút chạy lại.
2. Ý nghĩa trạng thái: 1 Chờ · 2 Đang chạy · 3 Thành công · 4 **Lỗi** · 5 Bỏ qua (trùng sự kiện, nội dung không đổi, hoặc phiếu đã chốt bên ERP — bỏ qua KHÔNG phải lỗi, chiếm đa số dòng). Chiều: 1 nhận, 2 gửi.
3. Dòng lỗi quá 24 giờ thì chuông 08:00 gọi người giữ khóa `sync_log`.
4. Phiếu bên ERP có `legacy_id` (mã Firebase) ở chi tiết phiếu; app cũ có `erpId` trên bản ghi. Một bên thiếu là chưa khớp.
5. Phía Worker (xem §6) đọc log trực tiếp: `npx wrangler tail --env production` rồi tạo một phiếu thử — thấy dòng gọi `/api/sync/datxe/events` và mã trả về.

Ba lỗi hay gặp: (a) **chữ ký sai / lệch giờ** → `sync_shared_secret` hai bên không trùng, hoặc đồng hồ lệch quá 5 phút; (b) **phiếu về thiếu xe / tài xế** → cắm nhầm khóa đọc RTDB sang project kia, hoặc danh mục chưa có `legacy_id` (tra trượt, `sync_datxe_auto_create` tắt nên không tự tạo); (c) **không có dòng sổ nào** → Worker chưa bắn: kiểm `SYNC_ENABLED`, `SYNC_ERP_BASE` trong `wrangler.jsonc` của đúng môi trường.

## 5. Thao tác Firebase

- Console: `https://console.firebase.google.com/project/api-degoholding/database` (dev) và `.../project/api-degoholding-com/database` (prod). Vào bằng tài khoản marketing (Administrator). Luật Realtime Database sửa ngay trên console tab *Rules*, **không có tệp rules trong repo** — sửa xong chép một bản vào `app đặt xe/GHI-CHU-BAN-GIAO.md` để có lịch sử.
- Dữ liệu phiếu nằm ở nhánh `requests` (đặt xe, giao hàng, đóng dấu chung một nhánh, phân biệt bằng `type`); từ bao-CR-452 có thêm `updatedAt` để ERP quét theo con trỏ, và `erpId` ghi ngược. Danh mục xe / tài xế / người dùng là các nhánh riêng, ERP tra qua `legacy_id`.
- **Không sửa tay phiếu trên console** để "cho khớp" ERP: không có `updatedAt` mới thì ERP không thấy, có thì nó đè lại phiếu ERP theo luật cú sau ghi đè. Muốn sửa phiếu thì sửa trên app cũ (có nghiệp vụ, có lịch sử).
- Khóa đọc RTDB cho ERP (`legacy_firebase_secret`): Console ▸ Project settings ▸ Service accounts ▸ *Database secrets* (khóa cũ kiểu legacy). Đổi khóa thì cập nhật `tab_setting` ngay, hai vòng Celery sẽ báo lỗi đọc nếu quên.
- Service account cho Worker (ghi RTDB, gửi FCM, Drive, Wiki) nằm ở **Secret của Worker** (§6), không nằm trong repo. Sinh lại ở Console ▸ Service accounts ▸ Generate new private key, rồi `wrangler secret put`.
- Bộ cấu hình web (apiKey, authDomain…) của ba web app trong project prod và của project dev được chép sẵn ở `app đặt xe/GHI-CHU-BAN-GIAO.md` §2, §2b. apiKey web là khóa công khai theo thiết kế Firebase nhưng vẫn không dán vào chat.
- Kiểm nhanh từ máy mình xem khóa đọc còn sống (thay `<URL>` và `<khóa>` bằng giá trị trong `tab_setting`, không ghi vào tệp): `curl -s "<URL>/requests.json?auth=<khóa>&orderBy=\"updatedAt\"&limitToLast=1"`.

## 6. App cũ — đẩy mã ở đâu, kiểm Worker trên Cloudflare thế nào

### 6.1 Worker `my-firebase-api` (repo GitHub `degoholding/my-firebase-api`)

- Thư mục máy: `D:\New folder\thuthapykien\app đặt xe\my-firebase-api`. Chữ `đ` trong đường dẫn làm `@cloudflare/vitest-pool-workers` hỏng; chạy test bằng cấu hình tạm `vitest.node.config.mts` (xem `TIEN-DO.md`), không commit tệp đó.
- Nhánh: **`feat/<việc>` → ff vào `dev` → ff vào `main`**. Hook husky chỉ cho commit trên nhánh `feat/*` (validate-branch-name) và chạy `npm run cf-typegen`. Khung đẩy: `git switch -c feat/x` → commit → `git switch dev && git merge --ff-only feat/x && git push origin dev`.
- **Đẩy nhánh = deploy.** GitHub Actions `.github/workflows/deploy.yml` chạy `npm test` rồi `wrangler deploy --env dev` (nhánh `dev`) hoặc `--env production` (nhánh `main`), mất khoảng một phút. Vì vậy đẩy `dev` cũng phải hỏi trước khi làm việc có người dùng thật thấy; đẩy `main` chỉ khi đại ca gật.
- Biến thường (`SYNC_ENABLED`, `SYNC_ERP_BASE`, `ERP_INBOUND_ENABLED`, `ENVIRONMENT`) khai trong `wrangler.jsonc` mục `env.dev.vars` / `env.production.vars`. **Không đặt trên Dashboard**: mỗi lần deploy wrangler gỡ Variable không có trong tệp. Bật tắt = sửa tệp rồi đẩy nhánh.
- Secret (wrangler không đụng, không vào git): `ADMIN_SERVICE_ACCOUNT_JSON`, `FCM_SERVICE_ACCOUNT_JSON`, `FIREBASE_DATABASE_URL`, `FIREBASE_PROJECT_NUMBER`, `SYNC_SHARED_SECRET`, `GGDRIVER_SERVICE_ACCOUNT_JSON`, `SMTP_TRANSPORT_JSON`, `RESEND_API_JSON`, `MESA_API_KEY`, `WIKI_*`; prod thêm `FIREBASE_PROJECT_ID`, `GOOGLE_CLIENT_*`, `GOOGLE_REFRESH_TOKEN`, `APPS_SCRIPT_ID`, `RESEND_*`. Đặt bằng `npx wrangler secret put <TÊN> --env dev|production` (gõ giá trị vào dấu nhắc, không để trong lệnh). Liệt kê tên: `npx wrangler secret list --env production`.
- Kiểm trên Cloudflare (chạy trong thư mục Worker, wrangler đã đăng nhập):

```bash
gh run list --repo degoholding/my-firebase-api --limit 5           # lần deploy gần nhất xanh / đỏ, nhánh nào
npx wrangler deployments list --env production                     # bản đang chạy, giờ tạo
npx wrangler tail --env production --format pretty                 # log trực tiếp; tạo phiếu thử rồi xem dòng gọi sang ERP
npx wrangler versions list --env dev                               # khi cần đối chiếu commit
```

Dashboard: `https://dash.cloudflare.com/d74f2df39b62699e41bb0a88d0856fe9/workers/services/view/my-firebase-api` (prod; dev thêm `-dev`) — tab *Metrics* xem lỗi 5xx, tab *Logs* xem log nếu không mở được terminal. Tab Dashboard nặng, đọc bằng chữ chứ không chụp màn.

- Chạy local: `npm run dev` → `http://localhost:8787`, cần `.dev.vars` (mẫu biến ở `readme.md` §4); `npm test`.

### 6.2 Web app cũ `degoholding-app-frontend` (repo GitHub `degoholding/degoholding-app-frontend`)

- Không có husky, commit thẳng `dev`; deploy bằng **Cloudflare Pages** theo nhánh: `main` → `app.degoholding.vn`, `dev` → `dev.app.degoholding.vn` (project `dego-app-frontend`; project `degoholding-app-frontend` cũ không dùng).
- Lệnh dựng trên Pages: `npm ci --no-audit --no-fund && npm run build`, biến `SKIP_DEPENDENCY_INSTALL=true` cho cả Production lẫn Preview (bao-CR-597 sửa lỗi dựng hỏng từ 14/07); `package-lock.json` phải nằm trong git.
- Biến `VITE_*` (`VITE_ENVIRONMENT`, `VITE_API_URL`, `VITE_FIREBASE_CONFIG`, `VITE_VAPID_KEY`, `VITE_RECAPTCHA_SITE_KEY`) đặt ở Pages ▸ Settings ▸ Environment variables, tách Production / Preview; giá trị mẫu ở `GHI-CHU-BAN-GIAO.md`.
- Kiểm: `npx wrangler pages deployment list --project-name=dego-app-frontend` (trạng thái từng lần dựng, link xem trước); local `npm run dev` → `localhost:5173`, lần đầu phải đăng ký App Check debug token (hướng dẫn §4 bước 4 của ghi chú bàn giao).

### 6.3 Thứ tự đẩy một thay đổi đụng đồng bộ

1. Sửa ERP trước, lên dev ERP (Agent 1 dựng), bật công tắc dev.
2. Sửa Worker trên nhánh `feat/*`, test local, ff `dev`, đẩy → Worker dev tự deploy, kiểm `gh run list`.
3. Chạy thử đầu-cuối trên dev (tạo phiếu ở `dev.app.degoholding.vn`, xem `/system/sync-logs` dev và `wrangler tail --env dev`).
4. Prod: ERP lên theo đợt phát hành của Agent 1; Worker ff `main` và đẩy **sau khi đại ca gật**; đặt Secret / biến prod trước khi đẩy.
5. Ghi sổ `nhat-ky-task.md` + dòng `TIEN-DO.md` của thư mục này.

## 7. Việc còn treo (23/10/2026)

- P3 (ERP → app cũ) đã dựng, khóa ở cả hai đầu; app cũ nhánh `main` chưa có mã P3 (mới ở `dev`); màn app cũ hiện km / chi phí từ ERP ở nhánh `feat/hien-km-chi-phi-tu-erp` (bao-CR-600) chưa đẩy.
- Bước 0 (chặn app cũ đè thao tác ERP trên phiếu có `legacy_id`) chưa làm — phải làm trước khi cho điều phối viên / tài xế thao tác thật trên ERP với phiếu đồng bộ.
- 48 dòng lỗi chiều nhận trên prod — ĐÃ XỬ 23/10 (bao-CR-661): 19 dòng phiếu đóng dấu chỉ lỗi một đêm 02/10 rồi tự vá; 29 dòng còn lại cùng một mã app cũ `1NXIMnXkj_ULzAfvOYGtp` có hai phiếu DX000422 + DX000423 tạo cùng một giây 20/10 (hai lượt gọi song song). Đã xóa DX000423 (bản sao, không có việc duyệt, không tệp; app cũ trỏ 422; sao lưu JSON ở máy trực `D:	mpackup-dx000423-20261023.json`), và mã tra theo `legacy_id` nay chọn hàng cũ nhất kèm cảnh báo thay vì ném lỗi. Vòng quét 02:15 đêm 23/10 nhận lại phiếu, chuông 08:00 tự im. Còn nợ: chặn hai lượt gọi song song đẻ trùng (chưa có khóa duy nhất trên `legacy_id` vì cột mặc định rỗng).
