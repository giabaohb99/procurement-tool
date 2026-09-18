# AGENT HUB — THIẾT KẾ KỸ THUẬT

| | |
|---|---|
| **Phiên bản** | v0.1 (bản nháp, chưa chốt) |
| **Ngày** | 2026-09-18 |
| **Người viết** | Trợ lý (theo yêu cầu của đại ca) |
| **Trạng thái** | DRAFT — chờ đại ca duyệt trước khi dựng bậc 1 |
| **Sổ CR** | [`change-log-ai.md`](../tai-lieu-ky-thuat/change-log-ai.md), dòng `ai-CR-001` |
| **Bộ quy tắc** | [`02-bo-quy-tac-bot.md`](02-bo-quy-tac-bot.md) |

---

## 1. Bản này trả lời câu gì

Đại ca muốn: có ticket thì một con AI kiểu quản lý nhận, tóm gọn lại dựa trên trí nhớ và dữ
liệu hệ thống, nhắn qua Telegram; đại ca xác nhận; bot gom một hoặc nhiều ticket cùng loại vào
một lần, đề xuất cách sửa; đại ca gật hoặc sửa; bot giao xuống một con bot chuyên code, con đó
làm cả backend lẫn frontend kèm bài kiểm nó tự viết, đẩy lên VPS qua CI/CD của GitHub; xong thì
báo ngược lên bot quản lý, tổng hợp gửi lại Telegram; đại ca ra lệnh thì mới lên prod.

Bản này mô tả xây cái đó bằng cách nào.

**Ngoài phạm vi bản này:** bot tự tìm việc mà không có ticket; bot sửa trên prod; bot tự quyết
định lên prod; nhiều người cùng duyệt (chỉ mình đại ca).

---

## 2. Ba quyết định nền, đại ca đã chốt 18/09/2026

| # | Quyết định | Vì sao |
|---|---|---|
| **QĐ-AI-1** | Nguồn ticket = **Phiếu hỗ trợ của ERP v2** + **tin nhắn Telegram của đại ca** | Hai nguồn nhưng **một bảng, một luồng**. Không đẻ hai nhánh mã cho cùng một việc. ⚠️ Đây là đích đến; **bậc 1 chỉ chạy nguồn Telegram** — xem `QĐ-AI-7` ở §12. |
| **QĐ-AI-2** | Agent Hub là **service mới trong repo `procurement-tool`**, không dựng repo/VPS riêng | Tận dụng nguyên Celery + Redis + Qdrant + DB + `tab_ticket` + lớp provider AI **đã chạy sẵn**. Ổ cứng VPS vừa dọn xong, không dựng thêm hệ thứ hai. |
| **QĐ-AI-3** | Bot code chạy **trên máy đại ca**, bằng **Claude Code CLI**; bot quản lý dùng **Gemini API** | Không cần API key Anthropic. Bot code là chỗ đốt tiền nhất thì ăn vào subscription; bot quản lý chỉ tóm tắt nên Gemini Flash gần như miễn phí. Biến phí cả hệ thống xấp xỉ bằng không. |

### Hệ quả của QĐ-AI-3: chiều gọi đảo lại, và hub về chạy ở máy đại ca

Bot quản lý gọi API ra ngoài, bot code chạy tại chỗ, cho nên **hub nên chạy luôn trên máy đại
ca**, không đặt ở VPS. Ba cái đỡ được ngay:

- Telegram **hub tự đi kéo tin** chứ không nhận gọi vào, nên không cần địa chỉ công khai, không
  cần Cloudflare tunnel, không cần webhook, không cần ký HMAC trên nút bấm.

  > **Đính chính 18/09/2026 (lúc dựng bậc 1).** Chỗ này viết "long-polling", bản dựng thật
  > **kéo ngắn mỗi 10 giây** (`timeout=0`). Lý do: vòng kéo chạy trong `celery-worker`, mà
  > worker đó khai `-c 1` — giữ một kết nối treo 30 giây nghĩa là suốt 30 giây đó không việc
  > nền nào khác chạy được, kể cả gửi thư và nạp chỉ mục. Đổi lại độ trễ tối đa 10 giây, mà
  > mọi trạm đều đang chờ người duyệt nên 10 giây không ai thấy. Muốn long-polling thật thì
  > phải tách hàng riêng cho vòng kéo, để dành cho bậc sau.
- Hub và bot code cùng máy nên không cần hàng đợi kéo việc qua mạng.
- Docker và git đều ngay tại chỗ, chạy cổng kiểm là gọi thẳng.

Đổi lại: **máy tắt thì không có gì chạy**. Chấp nhận được, vì trạm nào cũng đang chờ đại ca duyệt.

Ticket từ ERP v2 trên prod thì hub **quét theo mốc sửa** (`updated_at > con trỏ lần trước`) chứ
không nhận webhook — đúng khuôn `pull_updated` mà `legacy_datxe` đang chạy. Máy tắt vài ngày
cũng không mất ticket nào, bật lại là bắt kịp.

---

## 3. Kiến trúc

```
 ┌─────────────────────────── MÁY ĐẠI CA ───────────────────────────┐
 │                                                                  │
 │   agent-hub  (module mới trong backend/, chạy trên Celery)        │
 │   ├── cổng vào : quét tab_ticket theo mốc sửa  ◄── ERP v2 prod    │
 │   │              long-poll Telegram            ◄── đại ca nhắn   │
 │   ├── bộ nhớ   : Qdrant (đã có) + kho tài liệu repo               │
 │   ├── quản lý  : provider "gemini" (ĐÃ CÓ SẴN trong assistant/)   │
 │   ├── sổ       : tab_agent_task · tab_agent_run · tab_agent_msg   │
 │   └── điều phối: Celery beat + worker (đã có)                     │
 │                          │                                        │
 │                          │ spawn tiến trình, 1 job một lúc         │
 │                          ▼                                        │
 │   agent-runner  (container riêng, chỉ mount đúng worktree)        │
 │   └── claude -p ...  → sửa mã, viết bài kiểm, chạy cổng, commit   │
 │                          │                                        │
 └──────────────────────────┼────────────────────────────────────────┘
                            │ git push  nhánh  bot/ai-CR-xxx
                            ▼
                    GitHub  →  Actions chạy lại cổng trên máy sạch
                            │
                            ▼  (bậc 3 trở đi)
                    VPS dev  →  đại ca kiểm  →  VPS prod (bậc 4)
```

### Tái dùng cái gì đã có

| Cần gì | Đã có sẵn ở đâu | Phải làm thêm |
|---|---|---|
| Gọi model Gemini | `app/modules/assistant/provider/gemini.py`, lấy qua `get_provider("gemini")`; key ở `settings.GEMINI_API_KEY` | Không. Dùng thẳng. |
| Trí nhớ / tra cứu ngữ nghĩa | `assistant/rag/` + Qdrant (`settings.QDRANT_URL`) | Thêm một bộ sưu tập riêng cho nhật ký task và sổ CR |
| Ticket | `tab_ticket` + `tab_ticket_message` (module `ticket/`) | Không đụng bảng. Chỉ đọc. |
| Chạy nền, hẹn giờ | Celery + Redis + `core/celery_app.py` | Khai thêm vài việc nền |
| Sổ đồng bộ, con trỏ, nút chạy lại | `tab_sync_log` + `sync_log/registry.py` (bao-CR-416) | Khai thêm một `SyncSource` mã `agent` |
| Bộ mã trạng thái | `core/status_catalog.py` + `scripts/gen_status_ts.py` | Khai các bộ mã mới |

Nói cách khác: **phần lớn việc là ráp, không phải xây.** Thứ thật sự mới chỉ có ba: cầu nối
Telegram, ba cái bảng sổ, và con `agent-runner`.

---

## 4. Vòng đời một task — bảy trạm

| # | Trạm | Ai làm | Kết thúc bằng |
|---|---|---|---|
| 1 | **INBOX** | hệ thống | Ticket mới rơi vào sổ, chưa ai đọc |
| 2 | **TRIAGE** | Gemini | Gom nhóm ticket cùng loại + tóm tắt → nhắn Telegram |
| 3 | **PLAN** | Gemini | Bản đề xuất cách sửa → Telegram: *Duyệt · Sửa · Bỏ* |
| 4 | **CODE** | Claude Code | Sửa mã + bài kiểm + chạy cổng của phần vừa sửa |
| 5 | **CI** | GitHub Actions | Chạy lại cổng trên máy sạch, mở/cập nhật PR |
| 6 | **REVIEW** | Gemini | Tổng hợp diff + kết quả kiểm + link dev → Telegram |
| 7 | **PROD** | đại ca | Ra lệnh thì mới chạy kịch bản phát hành |

Thêm ba trạng thái kết: `DONE`, `CANCELLED` (đại ca bỏ), `FAILED` (bot chịu thua, đã leo thang).

**Luật chung cho mọi trạm:** máy chỉ đi từ trạm này sang trạm kia khi có **một hành động rõ
ràng** — đại ca bấm nút, hoặc một tiến trình kết thúc thành công. **Không có đường nào tự đi
tiếp sau khi hết giờ.** Hết giờ thì task đứng im và Telegram nhận một dòng báo, không phải một
quyết định.

### Chỗ dừng bắt buộc (không được cấu hình bỏ qua)

- Giữa **PLAN** và **CODE** — đại ca duyệt cách sửa.
- Giữa **REVIEW** và **PROD** — đại ca duyệt lên prod.

Hai chỗ này là toàn bộ lý do hệ thống này an toàn. Đừng bao giờ thêm cờ "tự duyệt" cho chúng.

---

## 5. Mô hình dữ liệu

Theo luật **R2** trong `CLAUDE.md`: đây là phân hệ **mới**, không thuộc Thu mua, nên mọi cột
trạng thái là **`SMALLINT` + hằng số nguyên**. **Không lưu chữ tiếng Việt xuống cột trạng
thái.**

> ⚠️ **Đính chính 18/09/2026 (lúc dựng thật).** Bản đầu của mục này ghi "khai trong
> `core/status_catalog.py`, sinh TypeScript bằng `gen_status_ts.py`" — **sai**. Đọc mã thì
> `core/status_catalog.py` là khung cho bộ mã **CHUỖI** (QĐ-9, `Code.value: str`), và
> `gen_status_ts.py` cũng chỉ sinh cho mã chuỗi. Bộ mã **SỐ** trong repo này sống thành hằng
> số nguyên ở `<module>/constants.py` kèm `*_LABELS` — khuôn thật là `leave/constants.py` và
> `vehicle_booking/model.py`, không phải `import_tool`. Đã làm theo khuôn đó ở
> `backend/app/modules/agent_hub/constants.py`. Bậc 1 không có màn hình nên chưa cần bản
> TypeScript.

### `tab_agent_task` — một đầu việc

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `code` | `String(50)` unique | `AI-000123`, sinh tuần tự |
| `title` | `String(255)` | Gemini đặt, đại ca sửa được |
| `source` | `SMALLINT` | `1` ticket ERP · `2` Telegram |
| `status` | `SMALLINT` | 1..7 theo bảy trạm, 8 DONE, 9 CANCELLED, 10 FAILED |
| `summary` | `Text` | Bản tóm tắt Gemini viết ở TRIAGE |
| `plan` | `Text` | Bản đề xuất ở PLAN (markdown) |
| `plan_files` | `JSON` | **Danh sách tệp dự kiến đụng tới.** Cột quan trọng nhất bảng này — xem §7 |
| `risk_level` | `SMALLINT` | 1 thấp · 2 vừa · 3 cao (đụng DB, tiền, phân quyền) |
| `branch_name` | `String(120)` | `bot/ai-CR-xxx-slug` |
| `pr_url` | `String(255)` | |
| `approved_by` / `approved_at` | | ai duyệt PLAN, lúc nào |
| `deployed_dev_at` / `deployed_prod_at` | | |
| `closed_at` | | |

### `tab_agent_task_item` — nối nhiều đầu vào vào một task

Vì đại ca muốn **gom nhiều ticket cùng loại vào một lần**. Bảng nối mang một **cặp**
`(source, ref_id)` — `2` Telegram → `tab_agent_message.id`, `1` ERP → `tab_ticket.id` — kèm
`merged_by` (`1` Gemini tự gom · `2` đại ca gom tay). Một đầu vào chỉ thuộc một task; task bị
hủy thì nó được thả ra cho lượt gom sau.

> ⚠️ **Đổi tên và đổi khóa so với bản đầu (QĐ-AI-8, 18/09/2026).** Bản đầu ghi
> `tab_agent_task_ticket` với đúng một cột `ticket_id`. Nhưng bậc 1 **không có `tab_ticket`
> nào** (QĐ-AI-7) nên bảng ấy sẽ rỗng suốt bậc 1, tức chức năng gom không chạy thật — mà "bot
> gom được không" lại đúng là một trong hai câu bậc 1 sinh ra để trả lời. Cặp `(source,
> ref_id)` dùng chung cho cả hai nguồn: nối `tab_ticket` ở bậc sau là **thêm dòng, không phải
> sửa bảng**.

### `tab_agent_cursor` — con trỏ `getUpdates` của Telegram

Bảng thứ năm, **không có trong bản đầu**. Đúng một dòng, `name = "telegram_offset"`. Telegram
giữ tin chưa xác nhận tối đa 24h; không lưu con trỏ xuống DB thì mỗi lần restart là bot đọc
lại toàn bộ tin cũ và đẻ ra một loạt task trùng. Cố ý **không** để trong Redis: một lần flush
Redis là một lần phát lại 24h tin nhắn.

### `tab_agent_run` — mỗi lần gọi model hoặc chạy bot, một dòng

`task_id` · `stage` (`SMALLINT`, trạm nào) · `provider` · `model` · `status` · `started_at` ·
`finished_at` · `duration_ms` · `input_tokens` · `output_tokens` · `cost_usd` · `error` ·
`artifact` (`JSON`: danh sách tệp đã đụng, lệnh đã chạy, kết quả cổng kiểm).

Không có bảng này thì không ai biết con bot đốt bao nhiêu và làm gì. Đây cũng là thứ cấp dữ
liệu cho cái trần chi phí ở §8.

### `tab_agent_message` — mọi lượt Telegram

`task_id` · `direction` (`1` bot gửi · `2` đại ca gửi) · `chat_id` · `tg_message_id` · `body` ·
`action` (nút đã bấm) · `created_at`.

Lưu cả hai chiều để sau này truy được *vì sao hồi đó chốt vậy* — đúng thứ mà
`nhat-ky-task.md` đang làm cho việc tay.

---

## 6. Bot quản lý (Gemini)

Gọi qua `get_provider("gemini")`. Mỗi task đúng **hai lời gọi** ở đường chính (TRIAGE, PLAN) và
một lời gọi ở REVIEW. Gom mười ticket thì **gộp vào một lời gọi**, không lặp mười lần — Gemini
free tier giới hạn theo phút.

### Trí nhớ lấy từ đâu — ba tầng

1. **Kho tài liệu dự án**, index vào Qdrant: `doc/tai-lieu-ky-thuat/nhat-ky-task.md` (3156 dòng),
   `change-log.md`, `change-log-bao.md`, `doc/tai-lieu-chuc-nang/*`. Đây mới là thứ làm con bot
   quản lý có giá trị — nó tra được *"việc này giống bao-CR-388, hồi đó chốt là không tự gán"*.
   Tóm tắt suông thì không cần AI.
2. **Lịch sử task cũ** trong `tab_agent_task` — task nào đã làm, kết quả ra sao.
3. **Dữ liệu hệ thống** — chính các ticket trong `tab_ticket` + `tab_ticket_message`.

### TRIAGE phải trả ra cái gì

JSON có cấu trúc, không phải văn xuôi: `title` · `summary` · danh sách `ticket_ids` gom chung ·
`risk_level` · `related_docs` (trích từ Qdrant) · `needs_clarification` (bool) + `questions`.

### PLAN phải trả ra cái gì

`plan` (markdown: bối cảnh, cách sửa, ảnh hưởng, rủi ro) · **`plan_files`** (danh sách tệp dự
kiến đụng) · `test_plan` (bài kiểm dự kiến) · `estimated_scope` (nhỏ / vừa / lớn).

**Nếu Gemini không viết nổi `plan_files` cụ thể thì task KHÔNG được sang CODE.** Nó phải hỏi lại
đại ca qua Telegram. Ticket mơ hồ là nguồn gốc của mọi thảm họa trong loại hệ thống này.

---

## 7. Bot code (Claude Code CLI)

### Gọi thế nào

Runner spawn tiến trình con, đọc luồng JSON để biết nó sửa tệp gì, chạy lệnh gì, kết thúc ra sao:

```bash
claude -p "<task brief>" --output-format stream-json --permission-mode acceptEdits
```

Chạy bằng phiên đăng nhập subscription sẵn có (`~/.claude/.credentials.json`), **không đụng
`ANTHROPIC_API_KEY`**. Cờ có thể đổi theo bản — kiểm lại bằng `claude --help` lúc dựng.

**Mỗi ticket một phiên mới**, đặt `--session-id` riêng; cần sửa vòng hai thì `--resume` đúng
phiên đó. **Tuyệt đối không gọi vào phiên chat đang mở của đại ca** — phiên đó lẫn ngữ cảnh
việc khác, chạy lại không ra cùng kết quả.

### Chạy ở đâu

Trong **container riêng trên máy đại ca**, chỉ mount đúng **git worktree** của task đó. Không
mount `D:\`, không mount thư mục home, **không đưa Docker socket vào**. Cần chạy cổng kiểm thì
gọi ngược ra hub bằng một lệnh hẹp, đừng cho bot cầm cả Docker.

Lý do phải làm vậy, nói thẳng: máy này có `.env` prod, `dego-erp-key.pem`, credentials Firebase,
và cả `~/.claude/.credentials.json` của chính con bot. Không có hộp kín thì đây là một con bot
có quyền quản trị trên máy làm việc của đại ca, đọc được chìa khóa prod.

### Task brief gồm gì

`plan` + `plan_files` + trích đoạn tài liệu liên quan + **bộ quy tắc** (`02-bo-quy-tac-bot.md`)
nối vào system prompt + đường dẫn `CLAUDE.md` và `backend/.claude/rules/`.

### Cổng kiểm bot phải qua

Đúng luật đại ca chốt 17/09 — **chỉ chạy bài kiểm của phần vừa sửa**, không quét cả cây:

```bash
docker compose exec -T api python -m pytest test/backend/<tệp của phần vừa sửa> -q
docker compose exec -T erp npm run typecheck
docker compose exec -T erp npm run lint
docker compose exec -T erp npx vitest run src/modules/<phân hệ>
```

`npm run check` / `npm run test` đầy đủ thì để GitHub Actions lo trên máy sạch. Bài kiểm chạy
trên máy đại ca **không đủ làm bằng chứng** — môi trường bẩn, và bot vừa sửa xong chính nó.

### Chống bot đi lạc

`plan_files` ở §5 không phải để trang trí. Runner **so danh sách tệp bot thật sự đụng với
`plan_files`**; lệch quá ngưỡng thì **dừng, không commit, leo thang lên Telegram**. Ngưỡng cụ
thể nằm ở bộ quy tắc. Đây là cái phanh tay của cả hệ thống.

---

## 8. Trần chi phí và tài nguyên

- **Một job một lúc.** Stack local đã 11 container và `CLAUDE.md` có nguyên một bài về máy đơ
  (`gioi-han-tai-nguyen-docker.md`). Chạy song song hai job là tự bắn vào chân.
- **Trần số task mỗi ngày.** Subscription có trần dùng theo tuần. Bot ngốn hết thì đại ca ngồi
  gõ tay cũng hết lượt — nên cái trần này bảo vệ đại ca chứ không phải bảo vệ máy.
- **Hết giờ thì giết tiến trình**, ghi `FAILED`, nhắn Telegram. Không tự thử lại lần hai trên
  cùng nội dung; thử lại là một quyết định của con người.
- **Trần số tệp và số dòng sửa** cho một task. Vượt thì dừng — task to vậy thì phải chẻ ra.

---

## 9. Cấu hình (`.env`)

Mọi cờ mặc định **tắt**. Chưa bật thì không một lời gọi nào đi ra ngoài, đúng nếp của
`legacy_datxe` và `pos365`.

```
AGENT_HUB_ENABLED=false            # cầu dao tổng
AGENT_TELEGRAM_BOT_TOKEN=
AGENT_TELEGRAM_CHAT_ID=            # chỉ chat_id này được ra lệnh
AGENT_MANAGER_PROVIDER=gemini
AGENT_MANAGER_MODEL=gemini-flash-latest
AGENT_GEMINI_API_KEY=              # key RIÊNG của bot, không dùng chung với Trợ lý AI
AGENT_ASSISTANT_USER=              # email tài khoản ERP mà lệnh `/hoi` chạy dưới quyền
AGENT_TRIAGE_BATCH=20              # số tin tối đa gom trong một lượt TRIAGE
AGENT_CODER_ENABLED=false          # bậc 2 mới bật
AGENT_CODER_CMD=claude
AGENT_WORKTREE_ROOT=/worktrees
AGENT_MAX_CONCURRENT_RUNS=1
AGENT_DAILY_TASK_CAP=5
AGENT_RUN_TIMEOUT_SEC=1800
AGENT_MAX_FILES_TOUCHED=25
AGENT_AUTO_DEPLOY_DEV=false        # bậc 3 mới bật
```

**Key Gemini để RIÊNG** (`QĐ-AI-7`, đại ca chốt 18/09/2026). `core/config.py` đã có
`GEMINI_API_KEY` của Trợ lý AI, nhưng bot **không dùng chung**: bot chạy nền, gọi liên tục, đốt
hết hạn mức thì Trợ lý AI đang phục vụ người thật chết theo — mà lúc đó không ai biết vì sao.
Để riêng còn đo được chi phí của bot mà không phải trừ nhẩm.

Không có biến nào giữ khóa Anthropic. Đó là chủ ý.

### `AGENT_ASSISTANT_USER` — biến nguy hiểm nhất trong bảng trên (QĐ-AI-10, 18/09/2026)

Bot còn làm **cửa Telegram cho Trợ lý AI có sẵn**: nhắn `/hoi <câu hỏi>` thì câu đó đi thẳng
vào `assistant.service.ask()` và trả lời ngay tại chỗ, **không đẻ ra task nào**. Nhắn chữ
thường thì mới vào luồng INBOX → TRIAGE → PLAN. Một bot, hai nhánh, chia bằng chữ đầu dòng —
vì đại ca chỉ có một cái điện thoại, bắt nhớ hai con bot là thua.

Chỗ nguy: **Trợ lý AI lọc dữ liệu theo người đăng nhập**, mà Telegram thì không có đăng nhập.
Nên phải chỉ đích danh một tài khoản ERP để chạy dưới quyền người đó.

- Để **trống** = tắt hẳn `/hoi`. Đó là mặc định.
- **Đừng khai tài khoản quản trị.** Ai nhắn được cho bot sẽ đọc được đúng những gì tài khoản
  này đọc được — kể cả `employee_sensitive` nếu tài khoản đó có.
- Hàng rào duy nhất còn lại là `AGENT_TELEGRAM_CHAT_ID`. Nó là một con số, không phải mật khẩu.
- Tài khoản bị khóa (`is_active = false`) thì `/hoi` từ chối chạy, không âm thầm chạy không
  phạm vi.

---

## 10. Lộ trình bốn bậc

| Bậc | Gồm gì | Bot được đụng mã nguồn? |
|---|---|---|
| **1** | **Năm** bảng sổ · Telegram kéo tin 10 giây + nút · Gemini TRIAGE + PLAN · Qdrant index tài liệu (kho riêng `agent_docs`) · nhánh `/hoi` gọi Trợ lý AI. **Nguồn ticket chỉ Telegram, không màn hình, xem sổ bằng Adminer.** Đầu ra chỉ là in PLAN ra Telegram và ghi vào sổ. | Không |
| **2** | `agent-runner` + `claude -p`, nhánh riêng, **mở PR, KHÔNG tự merge** | Có, trong worktree |
| **3** | Tự merge vào `erp-v2` khi CI xanh + tự đưa lên **dev** | Có |
| **4** | Cổng **prod**: đại ca ra lệnh → GitHub Environment có required reviewer → sao lưu DB → phát hành | Có |

**Bậc 1 là bậc đáng giá nhất.** Nó trả lời câu hỏi đắt nhất — con quản lý có đủ khôn để gom
ticket và viết được `plan_files` cụ thể không — mà **không rủi ro một chút nào**, vì nó chưa
được phép sửa gì cả. Nếu bậc 1 cho ra những bản PLAN lởm thì dừng dự án ở đây, đỡ được rất
nhiều công.

**Đừng nhảy cóc lên bậc 4.**

---

## 11. Rủi ro đã biết

| Rủi ro | Mức | Chặn bằng |
|---|---|---|
| Bot có quyền quản trị trên máy đại ca, cạnh chìa khóa prod | **Cao** | Container kín + chỉ mount worktree + danh sách cấm cứng (§7, bộ quy tắc) |
| Bot đi lạc khỏi phạm vi, sửa tùm lum | **Cao** | `plan_files` + ngưỡng lệch + phanh tay ở runner |
| Bài kiểm do chính bot viết, không phải bằng chứng | **Cao** | Bắt buộc có bài canh chiều ngược lại; bot quản lý phải **đọc diff**, không chỉ đọc "kiểm xanh" |
| Bot tự sinh migration làm hỏng DB | **Cao** | **Cấm tuyệt đối.** Cần đổi cấu trúc DB thì dừng và leo thang cho người |
| Đốt hết hạn mức subscription | Vừa | Trần task/ngày, một job một lúc, chỉ chạy bài kiểm phần vừa sửa |
| Codebase to (141 bảng, ~3200 bài kiểm FE) nên mỗi task ăn nhiều lượt | Vừa | `plan_files` khoanh phạm vi ngay từ PLAN |
| Máy đại ca tắt thì hệ thống đứng | Thấp | Chấp nhận. Quét theo mốc sửa nên bật lại là bắt kịp |
| Gemini free tier hết lượt theo phút | Thấp | Gom nhiều ticket vào một lời gọi |

---

## 12. Phạm vi bậc 1 — đã chốt

Bốn câu treo ở bản nháp đầu, đại ca trả lời hết **18/09/2026**, gói vào `QĐ-AI-7`.

| Câu | Chốt |
|---|---|
| Bot Telegram | **Đã có sẵn.** Đại ca tự điền `AGENT_TELEGRAM_BOT_TOKEN` + `AGENT_TELEGRAM_CHAT_ID` vào `.env`. Token không đi qua khung chat, không commit |
| Key Gemini | **Tách riêng** `AGENT_GEMINI_API_KEY` — xem §9 |
| Nguồn ticket | **Chỉ Telegram.** Nối `tab_ticket` để dành bậc sau (`AN-005`) |
| Màn hình quản lý | **Chưa dựng.** Xem sổ bằng Adminer (`AN-006` cho bậc 2) |
| Kho vector | **Collection riêng `agent_docs`**, không dùng chung `kb_docs` của Trợ lý AI (`QĐ-AI-9`) |
| Hỏi đáp qua Telegram | **Có**, nhánh `/hoi` (`QĐ-AI-10`) — chạy dưới quyền `AGENT_ASSISTANT_USER`, không đẻ task |

Cả ba cái bị cắt đều là **việc cộng thêm sau, không phải việc sửa lại**: `tab_ticket` chỉ là một
nguồn thứ hai đổ vào đúng bảng đó, màn hình chỉ là một cách nhìn khác lên cùng bộ dữ liệu. Cắt
được vì bậc 1 chỉ có mỗi một việc phải làm — trả lời câu *con quản lý có đủ khôn không* — và
không thứ nào trong ba thứ đó giúp trả lời nhanh hơn.

**Không còn gì chặn bậc 1.** Việc tiếp theo là đại ca duyệt bản thiết kế này, rồi bắt tay
`ai-CR-002`.
