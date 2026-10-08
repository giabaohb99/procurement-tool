# 14 — Hợp đồng cổng B (ERP ↔ dịch vụ AI) và cách dựng dịch vụ AI tách riêng

> Bản 1.0 — 08/10/2026 (ai-CR-119, phase S của [`13-lo-trinh.md`](13-lo-trinh.md) §3). Mã: `app/modules/agent_gateway/`
> (ERP), `app/modules/agent_hub/erp.py` (bot), `app/core/agent_signature.py` (chữ ký), `app/agent_main.py` (ứng dụng dịch vụ
> AI), `docker-compose.agent-hub.yml`, `backend/alembic_agent.ini`, `backend/scripts/agent_split/`.

## 1. Ba cách chạy một mã nguồn (`AGENT_MODE`)

| Giá trị | Tiến trình này là | DB | Bot | Trợ lý web, MCP | Cổng B / chuyển tiếp |
|---|---|---|---|---|---|
| `embedded` (mặc định) | ERP + bot trong một | một DB chung | chạy | tại chỗ | không có |
| `service` | **Dịch vụ AI (nút A)** | `agent_hub` riêng | chạy | tại chỗ (ERP chuyển tiếp tới) | gọi cổng B qua `AGENT_GATEWAY_URL` |
| `erp` | **ERP (nút B)** | DB ERP (không bảng bot) | không | chuyển tiếp sang `AGENT_SERVICE_URL` (trừ uploads / files / rag) | mở `/api/agent-gw/*` |

Mọi deploy hiện tại (dev, prod) vẫn là `embedded` cho tới khi làm bước ở §4 — không đổi gì nếu không khai `AGENT_MODE`.

## 2. Chữ ký máy-nói-máy

`HMAC-SHA256(AGENT_SERVICE_SECRET, "<ts>.<METHOD>.<path>.<user_id>.<sha256(body)>")`, header `X-Agent-Ts`, `X-Agent-Sign`,
`X-Agent-User`; lệch giờ > 5 phút từ chối; so bằng `compare_digest`. Khóa trùng hai đầu (`.env.dev` của ERP và `.env.agent`).

- Chiều **AI → ERP** (cổng B): `X-Agent-User` = tài khoản ERP mà lượt gọi chạy DƯỚI QUYỀN; ERP tra tài khoản (phải đang hoạt
  động) rồi chạy công cụ / nháp phiếu y như người đó bấm trên web (`require` + `apply_scope` nằm trong công cụ).
- Chiều **ERP → AI** (chuyển tiếp web): ERP xác thực JWT, rồi ký id người dùng; dịch vụ AI (`core/agent_identity.py`) tin chữ ký,
  hỏi cổng B lấy hồ sơ (`/me`, bộ đệm 60 s). Quyền (`require`) ở dịch vụ AI hỏi cổng `/can`.
- Đường `/api/agent-hub/internal/*` của dịch vụ AI chỉ nhận chữ ký với user 0 (ERP gọi nội bộ), ERP không chuyển tiếp đường này.

## 3. Cổng B — `/api/agent-gw/*` (ERP, chỉ gắn khi `AGENT_MODE=erp`)

| Đường | Người | Trả | Bot dùng cho |
|---|---|---|---|
| `GET /ping` | — | `{ok}` | kiểm nối |
| `GET /me` | có | `ErpUser` {id, email, employee_id, is_active, label, detail, context, names} | tài khoản của chat, chân dung cho prompt |
| `POST /users/lookup {ids, emails}` | — | [ErpUser] | tài khoản bot (`AGENT_ASSISTANT_USER`, `AGENT_TICKET_ASSIGNEE`) |
| `GET /users/search?q` | — | [ErpUser] | «cho anh Được quyền gộp», tìm chủ máy |
| `POST /can {entity, action}` | có | `{ok}` | `require` ở dịch vụ AI; quyền tạo việc Dự án |
| `GET /settings` | — | tab_setting {key: value} | `app_settings` của dịch vụ AI (bộ đệm 30 s, hỏng → .env) |
| `POST /glossary/block {texts}` | — | `{block}` | thuật ngữ nội bộ chèn vào prompt |
| `GET /tools` | có | [{name, description, parameters}] | danh sách công cụ ERP cho model (bộ đệm 10 phút) |
| `POST /tools/run {name, args}` | có | kết quả công cụ (dict) | mọi công cụ KHÔNG thuộc nhóm cá nhân |
| `POST /draft/create {kind, draft}` · `POST /draft/submit {kind, id}` · `GET /draft/details?kind&id` | có | {code, id} / {ok} / [chi tiết] | «tạo» / «gửi duyệt» phiếu từ chat, việc từ biên bản |
| `POST /tickets/open {statuses, exclude_ids}` · `GET /tickets/max-id` · `POST /tickets/by-ids` · `POST /tickets/{id}/note` · `POST /tickets` | —/có | phiếu dạng dict | phiếu hỗ trợ → việc sửa mã, báo lại, MCP report_issue |
| `GET /notifications?after_id&limit` · `GET /notifications/max-id` | — | chuông | chuyển chuông ERP sang chat |
| `POST /attachments/blocks {ids}` | có | {blocks, meta} | tệp đính kèm của Trợ lý web |
| `GET /files/{id}` | có | byte + `X-Filename` | gửi tệp báo cáo công cụ xuất |
| `GET /employees/match?name` · `GET /projects` | —/có | nhân sự khớp / dự án tạo việc được | thẻ việc từ biên bản |

Công cụ chạy **tại dịch vụ AI** (không qua cổng): `personal_tool`, `group_tool`, `meeting_tool`, `google_tool` — sổ nhớ,
thẻ cá nhân, nhóm, biên bản, Lịch / Drive Google. Mọi tên khác chạy ở ERP. Danh sách công cụ model thấy = cá nhân + ERP, bằng
đúng 66 tên như chế độ embedded (bài kiểm `test_agent_hub_tach_dich_vu.py`).

## 4. Dựng trên dev (Agent 1 làm theo thứ tự này — chưa làm cho prod)

```bash
# 0. MySQL: database + tài khoản riêng (THAY mật khẩu trong tệp trước khi chạy)
docker exec -i procurement-mysql sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql' < backend/scripts/agent_split/create_agent_db.sql

# 1. Checkout riêng cho dịch vụ AI (cùng kho, nhánh erp-v2) — deploy.sh đích «agent» dùng thư mục này
git clone -b erp-v2 <repo> ~/agent-hub && cd ~/agent-hub
cp .env.agent.example .env.agent      # điền: DB_PASSWORD, JWT_SECRET (TRÙNG .env.dev), AGENT_* tokens chép từ .env.dev,
                                       # AGENT_SERVICE_SECRET=$(openssl rand -hex 32), AGENT_GATEWAY_URL=http://procurement-tool-dev-api-1:8000
# 2. Dừng bot cũ trong stack ERP dev (tin không bị xử hai nơi)
cd ~/procurement-tool-dev && docker compose --env-file .env.dev -f docker-compose.dev.yml stop agent-poller celery-worker celery-beat
# 3. Chép dữ liệu bot sang DB mới (bảng cũ GIỮ NGUYÊN ở DB ERP, dọn sau)
MYSQL_ROOT_PASSWORD=… bash ~/agent-hub/backend/scripts/agent_split/copy_agent_tables.sh procurement_dev agent_hub
# 4. Dựng stack dịch vụ AI (start.agent.sh: alembic_agent upgrade head — bảng đã có thì chỉ ghi version)
cd ~/agent-hub && docker compose --env-file .env.agent -p agent-hub -f docker-compose.agent-hub.yml up -d --build
curl -s 127.0.0.1:8020/api/health            # {"success": true, "service": "agent-hub", "mode": "service"}
# 5. ERP sang chế độ tách: .env.dev thêm AGENT_MODE=erp, AGENT_SERVICE_URL=http://agent-api:8000,
#    AGENT_SERVICE_SECRET=<cùng khóa>; bỏ COMPOSE_PROFILES=bot (agent-poller không còn ở stack ERP)
cd ~/procurement-tool-dev && docker compose --env-file .env.dev -f docker-compose.dev.yml up -d --build api celery-worker celery-beat
docker compose --env-file .env.dev -f docker-compose.dev.yml rm -sf agent-poller
# 6. Kiểm: web ERP → Trang cá nhân → Khóa AI (đi qua chuyển tiếp); nhắn bot trên Telegram; log agent-worker
```

Mạng: `docker-compose.agent-hub.yml` nối hai mạng ngoài `dego-db` (MySQL) và `procurement-tool-dev_procurement-internal`;
prod đổi tên mạng tương ứng. ⚠️ `AGENT_GATEWAY_URL` phải là **tên container** (`procurement-tool-dev-api-1`), KHÔNG phải bí
danh `api`: trên mạng `dego-db` bí danh `api` trỏ tới HAI máy chủ (dev và một stack khác) nên lượt gọi rơi luân phiên sang máy
không có cổng B → 404 (gặp ngay lúc dựng 08/10). Máy sửa mã (`.env.runner` trên máy đại ca): `DB_NAME=agent_hub`,
`DB_USER=agent_runner` — em tự đổi sau khi dev chạy.

Quay lui: đổi `.env.dev` về `AGENT_MODE=embedded` (hoặc bỏ dòng), bật lại profile bot, dựng lại 4 service ERP; bảng cũ vẫn
còn nguyên (dữ liệu mới phát sinh ở DB `agent_hub` trong lúc tách thì chép ngược bằng cùng script, đổi chiều).

## 5. Deploy dịch vụ AI sau này (S-4)

`deploy.sh agent <commit>` (đích mới, mặc định `~/agent-hub`, compose agent-hub, health `127.0.0.1:8020`). Thêm môi trường vào
sổ của bot: «thêm môi trường agent: dir=~/agent-hub compose="--env-file .env.agent -p agent-hub -f docker-compose.agent-hub.yml"
branch=erp-v2 health=http://127.0.0.1:8020/api/health kind=dev» — từ đó bot code tự deploy chính nó và O-01 theo dõi health.

## 6. S-5 (sang VPS riêng) và S-6 (tách kho tin nhắn) — runbook, chưa cần mã

- **S-5:** trên VPS AI cài Docker + MySQL (hoặc dùng MySQL của VPS chính qua mạng riêng); `mysqldump agent_hub` → nạp; chép
  `.env.agent` (đổi `DB_HOST`, `AGENT_GATEWAY_URL=https://deverp.degoholding.vn` — cổng B qua tên miền, có chữ ký nên an toàn,
  thêm chặn IP ở Cloudflare nếu muốn); volume `agent_files`, `agent_qdrant` chép bằng `docker cp`; ERP đổi
  `AGENT_SERVICE_URL=https://<tên miền dịch vụ AI>`; bật lại poller ở máy mới (tắt máy cũ trước — một token Telegram một poller).
- **S-6:** nhóm bảng `tab_agent_group*` + tệp nhóm tách thành DB / stack «kho tin nhắn» khi chạm ngưỡng §4 doc 13; giao diện
  nội bộ: `tin của nhóm X từ giờ Y`, `tìm toàn văn`, `tệp theo ref` — chính là 3 hàm `groups.read / find / file_by_ref` hiện nay.

## 7. Zalo hướng B — dựng `zalo-listener` trên dev (ai-CR-122, Agent 1)

Chỉ đụng stack agent-hub; ERP chỉ thêm migration `grp02` (cột `tab_agent_group.members`, cho chế độ embedded) — tự
chạy khi api ERP khởi động lại sau đợt gộp kế.

1. `cd ~/agent-hub && git pull` (lên commit có ai-CR-122).
2. Thêm vào `.env.agent` (KHÔNG in giá trị khóa ra log):
   ```
   AGENT_ZALO_LISTENER_URL=http://zalo-listener:3100
   AGENT_GROUP_RETENTION_DAYS=90
   ```
   `zalo-listener` đọc `AGENT_SERVICE_SECRET` từ chính `.env.agent` (compose truyền qua `${AGENT_SERVICE_SECRET}`) —
   nhớ chạy `compose` với `--env-file .env.agent` như mọi lần.
3. `docker compose --env-file .env.agent -p agent-hub -f docker-compose.agent-hub.yml up -d --build` — dựng thêm image
   `dego-zalo-listener`, `agent-api` tự chạy `alembic -c alembic_agent.ini upgrade head` (lên `agent0002`).
4. Kiểm:
   - `docker logs agent-hub-zalo-listener-1 --tail 5` có «zalo-listener nghe cổng 3100» và «chưa có phiên»;
   - `docker logs agent-hub-agent-poller-1 --tail 20` có «Zalo tài khoản công ty BẬT»;
   - `docker exec agent-hub-agent-api-1 alembic -c alembic_agent.ini current` ra `agent0002 (head)`.
5. Báo em; đại ca nhắn bot Telegram `/zalo` (phải ra «chưa đăng nhập») rồi `/zalo dangnhap` để nhận ảnh QR.

Quay lui: xóa dòng `AGENT_ZALO_LISTENER_URL` khỏi `.env.agent`, `docker compose ... stop zalo-listener`, `up -d
agent-poller` — bot về như trước (cột `members` để nguyên, vô hại).

## 8. Màn «Nhóm chat» (ai-CR-123) — dựng trên dev

Đợt này đụng **cả ba**: ERP api (khóa quyền mới `agent_group` — dịch vụ AI hỏi quyền qua cổng B nên ERP phải biết khóa
này), giao diện ERP v2 (màn mới) và stack agent-hub (bảng mới + zalo-listener trả ảnh QR).

1. Gộp `agent-hub-bac-1` vào `erp-v2` như mọi lần; `alembic heads` ERP phải ra một head `grp03`.
2. ERP dev: dựng lại api (migration `grp03` + seed tự thêm `agent_group` đủ quyền cho vai trò Quản trị) và erp (giao
   diện v2) theo quy trình deploy dev thường lệ.
3. Stack agent-hub: `cd ~/agent-hub && git pull && docker compose --env-file .env.agent -p agent-hub -f
   docker-compose.agent-hub.yml up -d --build` — `agent-api` lên `agent0003`, `zalo-listener` dựng lại.
4. Kiểm: đăng nhập web dev bằng tài khoản quản trị → Trợ lý AI → **Nhóm chat** có tab «Tất cả nhóm» và thẻ «Zalo tài
   khoản công ty»; `alembic -c alembic_agent.ini current` = `agent0003 (head)`.

## 9. Máy sửa mã nối đúng Redis của dịch vụ AI (ai-CR-124) — dựng trên dev

1. `docker rm -f procurement-redis-dev-forward` (stack ERP dev, đang giữ cổng 127.0.0.1:16379 → Redis ERP).
2. `cd ~/agent-hub && git pull && docker compose --env-file .env.agent -p agent-hub -f docker-compose.agent-hub.yml up
   -d --build` — thêm `redis-agent-forward` (127.0.0.1:16379 → `redis-agent`), dựng lại bot (ghi vân tay `bot_fp`).
3. Kiểm: `docker exec agent-hub-redis-agent-1 redis-cli LLEN agent_code.may-dai-ca` giảm về 0 khi máy đại ca nối lại
   (máy đại ca không phải đổi gì: vẫn đường hầm 16379).
4. Quay lui: `docker compose ... stop redis-agent-forward`, rồi `docker compose -f docker-compose.dev.yml --profile bot
   up -d redis-dev-forward` ở stack ERP dev.
