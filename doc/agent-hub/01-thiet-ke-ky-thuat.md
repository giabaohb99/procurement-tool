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
  >
  > **Đính chính lần hai 22/09/2026 (`ai-CR-008`).** Câu "10 giây không ai thấy" sai ngay khi
  > bot thành cửa Telegram của Trợ lý AI: đại ca hỏi một câu là ngồi chờ câu trả lời, và
  > 0-10 giây chờ bot *thấy* tin cộng 5-10 giây model trả lời, không một dấu hiệu nào, đọc
  > ra là "bot bị chậm". Nay **tách tiến trình `agent-poller` riêng** (service trong
  > `docker-compose.agent.yml`, `python -m app.modules.agent_hub.poller`) giữ kết nối
  > **25 giây** (`telegram.LONG_POLL_TIMEOUT`) — tin tới là Telegram thả ngay. Vòng beat 10
  > giây **tắt** khi cờ `AGENT_LONG_POLL=true` (đặt sẵn trong `environment` của celery-beat +
  > celery-worker ở tệp compose đó), chặn hai lớp: bỏ khỏi lịch beat, và việc
  > `agent.poll_telegram` tự trả rỗng — hai bên cùng đọc một con trỏ là xử trùng một tin.
  > Kèm theo: bot bật "đang soạn tin..." (`sendChatAction`) ngay khi nhận tin và bật lại
  > trước khi gọi Trợ lý AI; Gemini trả 429 kèm `retryDelay` không quá 10 giây thì chờ rồi
  > gọi lại đúng một lần. Stack local không dùng tệp compose agent thì vẫn chạy vòng beat cũ.
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
| 2 | **TRIAGE** | Gemini | Gom nhóm ticket cùng loại + tóm tắt → **chạy thẳng sang PLAN**, không nhắn thẻ riêng (`ai-CR-005`) |
| 3 | **PLAN** | Gemini | Bản đề xuất cách sửa → Telegram: *Duyệt · Sửa · Bỏ* |
| 4 | **CODE** | Claude Code | Sửa mã + bài kiểm + chạy cổng của phần vừa sửa |
| 5 | **CI** | GitHub Actions | Chạy lại cổng trên máy sạch, mở/cập nhật PR |
| 6 | **REVIEW** | Gemini | Tổng hợp diff + kết quả kiểm + link dev → Telegram |
| 7 | **PROD** | đại ca | Ra lệnh thì mới chạy kịch bản phát hành |

Thêm ba trạng thái kết: `DONE`, `CANCELLED` (đại ca bỏ), `FAILED` (bot chịu thua, đã leo thang).

**Luật chung cho mọi trạm:** máy chỉ đi từ trạm này sang trạm kia khi có **một hành động rõ
ràng** — đại ca bấm nút, hoặc một tiến trình kết thúc thành công. TRIAGE → PLAN là *một tiến
trình kết thúc thành công* nên chạy liền tay: đại ca cần đọc **phương án** để quyết, chứ
không cần bấm một nút chỉ để bot bắt đầu nghĩ (`ai-CR-005`). **Không có đường nào tự đi
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

### Rà soát mã thật trước khi lập kế hoạch (ai-CR-017, 23/09/2026)

Đại ca chốt: **mọi việc đều rà soát**. Lý do là ca AI-0006: bước lập kế hoạch chỉ đọc tài liệu nên
đề xuất sửa lại đúng chỗ màn v1 đã sửa từ bao-CR-376, và ghi tên tệp thiếu đường dẫn.

Luồng mới: gom xong → `service.start_scan` đưa việc sang **«Đang rà soát mã»** (`ST_SCANNING = 13`),
nhắn đại ca «Đậu Đậu nhận việc … đang đọc mã» (hết cảnh im lặng), giao `agent.scan_task` (hàng đợi
`agent_code`) → runner cắt worktree từ nhánh nền **mới nhất trên GitHub**, chạy `claude -p` với
công cụ CHỈ ĐỌC (`Read/Glob/Grep` + `git diff/status/log/show`, 40 lượt, trần 15 phút, phiên
mới) → Claude trả một tin nhắn cho đại ca (mở bằng **Kết luận**, có dẫn chứng `tệp:dòng`, so cả
`frontend/` lẫn `frontend-v2/`) + một khối JSON (`files`, `root_cause`, `already_fixed`,
`risk_level`, `questions`) → runner nhắn đoạn phân tích (kèm «Cần đại ca quyết» nếu có) → lập kế
hoạch ngay trong runner với kết quả rà soát trong đề bài (`manager.run_plan(review=…)`).
Lượt `STAGE_SCAN = 25` giữ tin nhắn + JSON; đề bài sửa mã sau này cũng mang đoạn rà soát.

| Chốt | Làm gì |
|---|---|
| Nhánh nền đúng | `coder.fetch_base`: có `AGENT_GITHUB_TOKEN` thì kéo thẳng `+refs/heads/<nền>` từ GitHub vào `origin/<nền>` của kho base; lỗi hoặc không khóa thì lùi về `.git` ở máy. **Vá lỗi có sẵn**: kho base nhân bản từ `.git` máy đại ca, erp-v2 ở máy chậm **7 commit** so với GitHub ngày 23/09 — bot đọc/sửa trên mã cũ, và lượt gộp sẽ bị GitHub từ chối |
| Tệp đầy đủ | `service.resolve_plan_files`: tên tệp trơn trong kế hoạch được nối đủ đường dẫn khi khớp đúng một tệp trong kết quả rà soát. Tệp cấm lọt vào JSON bị gạt ngay ở `parse_scan` |
| Câu của đại ca | Câu nghiệp vụ rà soát nêu mà đại ca chưa trả lời thì kế hoạch KHÔNG tự quyết: bỏ phần đó ra, ghi «Chưa làm: … — chờ đại ca quyết» |
| Không bỏ rơi việc | Rà soát hỏng (CLI lỗi, hết hạn mức, quá giờ) → nhắn một câu rồi lập kế hoạch theo tài liệu như trước. Runner tắt / broker chết lúc giao → lập kế hoạch ngay. Vòng beat `resume_stuck_plans`: việc ở rà soát mà lượt chưa bắt đầu sau 45 phút (runner `-c 1` có thể đang sửa việc khác tới 30 phút), hoặc lượt chạy quá trần + 3 phút, thì đóng lượt và lập kế hoạch theo tài liệu |
| Trả lời câu hỏi lại | Lập lại kế hoạch (trong poller) dùng lại kết quả rà soát cũ, không rà soát lại |
| So `main` (ai-CR-018) | `fetch_base` kéo cả `main` từ GitHub; đề bài rà soát BẮT chạy `git log origin/erp-v2..origin/main` và dò trong đó — lỗi đã sửa ở main mà chưa gộp thì ghi `already_fixed` + nói ở Kết luận. Ca AI-0006: bao-CR-465 ở main sáng 23/09, bot không thấy vì chỉ nhìn erp-v2 |
| Tài liệu ở máy (ai-CR-018) | `../procurement-tool/doc` mount CHỈ ĐỌC vào runner ở `/local-docs` (`AGENT_LOCAL_DOCS_DIR`), `claude` mở bằng `--add-dir`; đề bài chỉ thẳng change-log-bao, change-log, nhật ký. Kho tài liệu của bot (Qdrant `agent_docs`) nạp từ `doc/` + `CLAUDE.md` ở máy thay cho bản chép trong worktree bot (tách từ 18/09); `doc/agent-hub/` lấy từ chỗ mount của sổ. Nạp lại 23/09: 48 tệp, 4569 đoạn. Lưu ý: thư mục ở máy là bản làm việc CHÍNH, có thể chậm hơn GitHub (23/09 chậm 7 commit) — nó bù phần CHƯA commit, còn phần đã đẩy lên thì bước so main/erp-v2 bắt |

Đo thật trên AI-0006 (23/09): 6,6 phút, 11 lượt, ước ~1,7 USD theo giá API (gói thuê bao, không
tính tiền theo lượt). Rà soát tìm ra gốc thật: giao diện cả hai bản chỉ gửi TÊN phòng ban, máy chủ
dò lại theo tên và cố ý trả 0 khi hai pháp nhân có phòng trùng tên (`department/service.py`) —
khớp chữ «thỉnh thoảng» của đại ca; lỗi gửi thông báo bị nuốt im lặng.

### Sổ quyết định: tra trước khi hỏi (ai-CR-015, 23/09/2026)

Đại ca muốn bot bớt hỏi xác nhận bằng cách ghi những quyết định quen thuộc thành một tệp cho bot
tra. Tệp là [`03-so-quyet-dinh.md`](03-so-quyet-dinh.md), bản đầu 11 mục gom từ các lần đại ca
đã chốt. Ba luật của sổ đại ca chốt 23/09: **bot chỉ đề xuất ghi, đại ca bấm mới thành luật** ·
**sổ nằm trong kho mã** · **việc dính tiền, công nợ, phân quyền (và DB, prod, main, gộp mã) luôn
hỏi**.

| Chỗ | Làm gì |
|---|---|
| Lượt PLAN (`manager.run_plan`) | Đề bài mang theo sổ. Luật 2 của lời nhắc: có mục khớp → làm theo, ghi `assumptions` «Theo QĐ-xx: …»; không có mà có một đường an toàn, dễ đảo → chọn, ghi «Em giả định: …»; chỉ hỏi khi không viết nổi `plan_files`, khi dính chủ đề luôn hỏi, hoặc khi hai cách hiểu dẫn tới hai việc khác hẳn. Không hỏi đại ca đường dẫn tệp. Giả định được nối vào cuối `plan` dưới dòng «Em tự quyết, không hỏi lại» — thẻ duyệt hiện ra, runner đọc lại y nguyên |
| Việc rủi ro cao (`risk_level` 3) | **Không nạp sổ**, lời nhắc cấm giả định; model vẫn giả định thì `plan_task` đổi mọi giả định thành câu hỏi và để việc ở «Đang hỏi lại». Thi hành trong mã |
| Đề bài Claude Code (`coder.build_brief`) | Nạp sổ (trừ việc rủi ro cao); hai ca «không tái hiện được lỗi» và «thiếu dữ liệu để quyết» thôi là lý do dừng; phần 4 của tổng kết liệt kê từng dòng «Theo QĐ-xx» / «Em giả định» |
| Lệch kế hoạch (`coder.check_drift`) | Tệp `.md` không tính vào tỷ lệ 30 % (QĐ-02); trần 25 tệp vẫn đếm. Sổ quyết định là **tệp cấm** với `claude` — sổ chỉ ghi qua nút đại ca duyệt |
| Trả lời câu hỏi lại | **Vá lỗ có sẵn**: trước đây câu trả lời rơi vào INBOX và đẻ thành việc MỚI, việc cũ treo ở «Đang hỏi lại». Nay thẻ hỏi lại đóng dấu `cho_tra_loi_kh`; tin kế của đại ca (trong 30 phút, không xen tin hay nút bấm khác) gắn vào việc đó (tin nối vào `tab_agent_task_item`, câu hỏi + câu trả lời nối vào `summary`) rồi lập lại kế hoạch ngay, không cần `/gom`. Trả lời trễ thì bấm «Trả lời câu hỏi» (`ans:`) mở lại cửa. Nút «Sửa lại» đi cùng đường |
| Đề xuất ghi sổ (`service.propose_rule`) | Sau khi lập lại kế hoạch, một lượt Gemini (`manager.run_rule_draft`, trạm `STAGE_RULE = 24`) xem câu trả lời có dùng lại được không; được thì thẻ «Lần sau gặp tương tự em tự làm vậy, khỏi hỏi nhé?» với «Ghi vào sổ» (`qdok:`) · «Không, lần nào cũng hỏi» (`qdno:`). Câu hỏi/đáp chạm chủ đề luôn hỏi → không gọi model, nói một dòng «lần sau em vẫn hỏi». Bản nháp nằm trong `tab_agent_run.artifact` (`state` = `cho_duyet` · `da_ghi` · `bo` · `khong_ap` · `loi`) |
| Ghi sổ (`playbook.append_entry`) | Soi chủ đề cấm LẦN NỮA rồi nối mục `QĐ-<số kế>` vào cuối tệp, ghi nguồn «đại ca bấm «Ghi vào sổ» trên Telegram ngày …, từ việc AI-xxxx». Tệp mount ở `/agent-docs` (poller + agent-api ghi được; celery-worker + runner chỉ đọc) |

Đo thật 23/09 với Gemini: việc «màn đơn hàng lọc ngày ra thiếu đơn, không kèm mã phiếu» trước
đây hỏi lại, nay ra thẳng kế hoạch với «Theo QĐ-01: …» (hai lượt liên tiếp như nhau); bản nháp
trùng ý QĐ-01 thì model tự bỏ; bản nháp mới «cột mới trên bảng danh sách để ẩn mặc định» ra
đúng bốn ý. Hai lỗi tìm ra khi chạy thật: trần 4096 token cắt cụt JSON (phần suy nghĩ của Gemini
ăn 6-7 nghìn) → nâng 16384; bộ lọc chủ đề bắt nhầm «thêm cột» của bảng giao diện là cấu trúc DB
→ thu hẹp về câu có nhắc DB/migration.

---

## 7. Bot code (Claude Code CLI)

*(Bản đầu viết trước khi dựng, còn nói `stream-json` + `~/.claude/.credentials.json`. Từ
**ai-CR-011** (22/09/2026) phần này ghi đúng cái đang chạy. Mã: `agent_hub/coder.py`, tiến trình
`agent-runner` trong `docker-compose.agent.yml`, ảnh `docker/Dockerfile.runner`.)*

### Ba giai đoạn của bậc 2

| GĐ | Gồm gì | Trạng thái |
|---|---|---|
| **1** | Bấm **Duyệt** là runner sửa mã thật trong worktree riêng, chạy bài kiểm backend của phần vừa sửa, **commit vào nhánh nằm trong container**, gửi **thẻ kết quả + tệp `.diff`** về Telegram. Chưa đẩy GitHub. | **Xong 22/09/2026** |
| **2a** | Đẩy nhánh `bot/*` lên GitHub + **mở PR vào `erp-v2`** (ai-CR-012). Cờ `AGENT_PR_ENABLED` bật thì runner tự đẩy ngay sau commit; tắt thì thẻ kết quả có nút **«Gửi link PR để anh tự merge»** (tên cũ «Đẩy GitHub + mở PR», đổi 23/09) đẩy tay từng việc (cũng là nút đẩy lại khi hỏng). Khóa `AGENT_GITHUB_TOKEN` (PAT chi tiết, Contents + Pull requests, một kho) đại ca tự dán vào `.env`; runner đọc thẳng `os.environ` lúc đẩy, đưa vào `git push` bằng biến `GIT_CONFIG_*` (không lên dòng lệnh) + header API, **không bao giờ vào tiến trình `claude`**. Đẩy **đè** (`--force`) vì chạy lại việc là cắt lại nhánh; PR trùng nhánh thì lấy PR đang mở. Nhánh bot KHÔNG tự xóa sau merge (mặc định giữ, đại ca chưa quyết). Đẩy hỏng không làm hỏng việc — commit vẫn trong runner. | **Xong 22/09/2026** — PR đầu tiên do bot mở: #95 (AI-0005, nợ N-009) |
| **2b·1** | **Hỏi thêm về bản vá** ngay trên Telegram (ai-CR-013): nút «Hỏi thêm về bản vá» trên thẻ kết quả → tin chữ kế tiếp của đại ca đi vào **đúng phiên Claude Code đã sửa việc** (`claude -p --resume`, chỉ đọc) → câu trả lời về Telegram, nhắn tiếp trong 10 phút là hỏi tiếp. Phiên CLI nay cất trong volume worktree (`CLAUDE_CONFIG_DIR`) nên sống qua `up --force-recreate`. Chi tiết ở mục *Hỏi thêm về bản vá* bên dưới. | **Xong 22/09/2026** |
| **2b·2** | **Gộp `erp-v2` + deploy dev có hỏi trước** (ai-CR-014): nút «Gộp erp-v2 + deploy dev» trên thẻ kết quả → thẻ hỏi kể ba bước + số tệp/số dòng/cổng kiểm → «Đồng ý» · «Hẹn giờ» · «Thôi». Runner `merge --no-ff`, đẩy không `--force`, SSH lên VPS reset cứng + build đúng service, chờ health. Thẻ sau deploy có «Thu hồi» (`git revert -m 1` + deploy lại) và «Xong». Mục *Luật nhánh* bên dưới. | **Xong 22/09/2026** |
| **3** | Cổng kiểm frontend-v2 (ai-CR-019): typecheck cả cây · eslint tệp vừa đụng · vitest thư mục vừa đụng; thư viện Node cài MỘT lần mỗi `package-lock.json` vào volume runner, worktree gắn liên kết; Claude Code tự kiểm được bằng `npm --prefix frontend-v2 run typecheck` / `run test -- src/...`. `frontend/` (bản cũ) chưa có cổng. | **Xong 23/09/2026** |

### Gọi thế nào

```bash
claude -p --output-format json --permission-mode acceptEdits \
       --allowedTools "<danh sách hẹp>" --session-id <uuid mới> --max-turns 80  < đề bài
```

- **Đề bài đi qua stdin**, không đi qua tham số dòng lệnh, để `ps` trong container không lộ nội
  dung.
- `--output-format json` (không `stream-json`): runner cần đúng **một** JSON cuối để đọc
  `result` · `session_id` · `usage` · `total_cost_usd` · `num_turns`. Bản CLI 2.1 in kèm cảnh báo
  ở stderr, runner bóc JSON từ dấu `{` đầu đến `}` cuối của stdout.
- `--allowedTools` chỉ mở: đọc/sửa/tạo tệp, tìm kiếm, `pytest` (gõ `python` hay `python3` đều
  được), `py_compile`, và `git diff/status/log`. **Không có `git commit`, `git push`, `docker`,
  `pip`, `npm`** — runner tự commit sau khi kiểm, bot không được cầm git. Đây là hàng rào bằng
  quyền, không phải bằng câu dặn (§E của bộ quy tắc). ⚠️ Mẫu `Bash(python -m pytest:*)` khớp
  **theo tiền tố chuỗi lệnh**: lượt chạy thật đầu tiên (AI-0005, 22/09/2026) bot gõ `python3`,
  bị chặn, rồi đốt hơn nửa trong 54 lượt để thử lại kể cả lệnh `docker compose exec` chép từ
  CLAUDE.md — nên đề bài (C6) nay nói thẳng "không có Docker ở đây, lệnh bị chặn thì đừng lặp".
- **Mỗi việc một phiên mới** (`--session-id` sinh ngẫu nhiên, ghi vào `tab_agent_run.artifact`).
  Hỏi thêm (GĐ2b·1) thì `--resume` đúng phiên đó. **Không bao giờ gọi vào phiên chat của đại ca.**
  ⚠️ Phiên nằm ở `CLAUDE_CONFIG_DIR = <AGENT_WORKTREE_ROOT>/.claude` (trong volume `agent_worktrees`,
  `coder.claude_config_dir`), KHÔNG ở `~/.claude` của `runner`: thư mục home nằm trong lớp ghi của
  container, `up --force-recreate` (bắt buộc mỗi khi đổi `.env`) là mất sạch — phiên của AI-0005
  mất đúng kiểu đó trước khi có nút hỏi. Kiểm chứng 22/09/2026: tệp phiên nằm ở
  `/worktrees/.claude/projects/-worktrees-<mã>/<session>.jsonl`, `--resume` sau đó nhớ đúng lượt trước.
- **Đăng nhập bằng khóa OAuth của subscription**, cấp bởi `claude setup-token`, đại ca **tự dán**
  vào `.env` dưới tên `CLAUDE_CODE_OAUTH_TOKEN`. Không có `ANTHROPIC_API_KEY` (QĐ-AI-3). Khóa này
  **cố ý không nằm trong `Settings`** của ứng dụng — `coder.build_env` đọc thẳng `os.environ` và
  chỉ đưa nó vào tiến trình `claude`; `git` và `pytest` chạy với môi trường **không có** khóa đó.
- Môi trường của tiến trình con là **môi trường sạch** dựng từ đầu (PATH, HOME, LANG, PYTHONPATH),
  KHÔNG kế thừa của Celery — nên token Telegram, key Gemini, mật khẩu DB của tiến trình cha không
  bao giờ xuống tới `claude`. Có bài kiểm canh (`test_moi_truong_cho_claude_sach_...`).

### Chạy ở đâu

Service **`agent-runner`** — Celery worker `-c 1` chỉ nghe hàng đợi **`agent_code`** (định tuyến
ở `core/celery_app.py`). Trong container:

- `/src-repo` = thư mục `.git` của kho chính, mount **chỉ đọc**. Runner `clone --no-checkout` từ
  đó ra `/worktrees/base` một lần, rồi mỗi việc là một `git worktree add -B bot/<mã>-<slug>`
  từ `origin/erp-v2` (`AGENT_BASE_BRANCH`). Nhánh của bot **sống trong volume `agent_worktrees`**,
  kho chính trên máy đại ca không đổi một byte.
- Celery chạy root (bắt buộc với ảnh này), nhưng **mọi tiến trình con — `git`, `claude`, `pytest`
  — hạ xuống người dùng `runner` (uid 1000)** bằng `subprocess(user=..., group=...)`. Tệp trong
  worktree thuộc `runner`; `/app` (mã của hub) mount chỉ đọc.
- **Không mount `D:\`, không mount home, không có Docker socket.** Muốn chạy cổng kiểm frontend
  thì phải dựng thêm đường riêng (GĐ3), không phải đưa Docker vào.
- Trần tài nguyên: 3 GB RAM · 2 CPU · một việc một lúc. Không có `AGENT_MAX_CONCURRENT_RUNS`
  nữa — số việc song song **là** `-c 1` của worker.
- **Chưa chặn được egress.** Compose không có cách khai allowlist tên miền cho một container;
  runner hiện ra Internet được như mọi container khác. Ghi nhận là rủi ro mở ở §11, giải quyết ở
  GĐ sau (proxy có allowlist hoặc mạng nội bộ + proxy riêng).

### Task brief gồm gì

`coder.build_brief`: mã việc + tiêu đề · tóm tắt · kế hoạch + **`plan_files`** (ghi rõ là hàng rào)
· bài kiểm dự kiến · tài liệu liên quan do Gemini viện dẫn · trích đoạn `memory.recall` (Qdrant)
· bản rút gọn của bộ quy tắc **C1…C10 và §D** · yêu cầu **TỔNG KẾT bốn phần** ở cuối (đã sửa gì ·
bài kiểm · điều chưa chắc · đề nghị cho người). `CLAUDE.md` và `backend/.claude/rules/` bot tự đọc
được vì chúng nằm trong worktree — nhưng bot **không được sửa** chúng (danh sách cấm).

### Cổng kiểm bot phải qua

Đúng luật 17/09 — chỉ bài kiểm của phần vừa sửa. GĐ1 runner tự chạy
`python -m pytest <các tệp test/backend bot vừa đụng> -q` ngay trong container, kết quả in lên
thẻ là **XANH / ĐỎ** kèm đuôi log; không đụng bài kiểm backend nào thì thẻ nói thẳng là **chưa
kiểm**. Từ ai-CR-019 (23/09) có thêm **cổng frontend-v2** khi việc đụng `frontend-v2/`: `tsc --noEmit` cả cây · `eslint` đúng tệp vừa đụng (lint cả cây thì lỗi cũ của người khác làm đỏ việc này) · `vitest run` đúng thư mục `src/modules/<phân hệ>` / `src/shared/<khu>` / `src/core/<khu>` vừa đụng — không bao giờ cả bộ ~3200 bài. Thẻ có dòng riêng «Frontend v2: XANH/ĐỎ/CHƯA kiểm được»; không cài được thư viện thì KHÔNG tính là xanh. Thư viện: `/worktrees/.deps/fe-v2-<băm lockfile>/node_modules` cài bằng `npm ci` một lần (giữ 2 bộ gần nhất), worktree gắn liên kết `frontend-v2/node_modules` + khóa ở `info/exclude`. Đo thật 23/09 trên AI-0006: cài 12 giây, cổng (typecheck + lint 1 tệp + vitest procurement) 109 giây, xanh. Bài kiểm chạy trên máy đại ca **vẫn không đủ làm bằng chứng** —
PR + CI mới là bằng chứng; PR có từ GĐ2a (ai-CR-012), CI của kho tự chạy trên nhánh `bot/*`.

### Đẩy GitHub + mở PR (GĐ2a, ai-CR-012)

Sau `git commit` trong worktree, runner `git push --force https://github.com/<kho>.git
HEAD:refs/heads/bot/<mã>-<slug>` rồi `POST /repos/<kho>/pulls` (head = nhánh bot, base =
`AGENT_BASE_BRANCH`). Mô tả PR dựng từ chính dữ liệu của lượt chạy: việc + tóm tắt · kế hoạch đã
duyệt trên Telegram · từng tệp +/− (đánh dấu NGOÀI kế hoạch) · cổng kiểm XANH/ĐỎ kèm tên tệp bài
kiểm · tổng kết của bot · phiên Claude Code. `pr_url` ghi vào `tab_agent_task`, thẻ kết quả thêm
dòng «Đã đẩy GitHub, PR #n» và nút liên kết **«Mở PR trên GitHub»** (nút Telegram nay nhận cả
URL). Ba nhánh của thẻ: PR ok → nút mở PR · đẩy hỏng → dòng **HỎNG + lý do** và nút «Đẩy GitHub
lại» · cờ tắt → nút «Đẩy GitHub + mở PR». Cả hai nút sau đi `pr:<id>` → `agent.publish_task` trên
hàng đợi `agent_code` (chỉ runner thấy `/worktrees`) → `coder.publish_existing`: kiểm worktree còn
và đang ở đúng nhánh, lấy tệp/cổng kiểm/tổng kết từ `artifact` của lượt CODE gần nhất rồi đẩy y
như lượt tự động. Runner mở PR bằng `requests` (đã có sẵn cho Telegram); container không có
`curl`.

### Hỏi thêm về bản vá (GĐ2b·1, ai-CR-013)

Thẻ kết quả (cả thẻ leo thang) có nút **«Hỏi thêm về bản vá»** (`ask:<id>`). Đường đi:

1. Bấm nút → bot **không gỡ nút** của thẻ (khác mọi nút khác: «Mở PR» / «Bỏ việc này» còn phải
   dùng sau khi hỏi) → nhắn lời mời, dấu `cho_hoi_va`, gắn `task_id`. Không có phiên (việc chưa
   qua CODE) thì chỉ hiện toast.
2. Tin chữ kế tiếp của đại ca trong `FOLLOW_UP_WINDOW` (10 phút) sau một tin có dấu `cho_hoi_va` /
   `hoi_va` / `tra_loi_va` **là câu hỏi**, đi TRƯỚC mọi rẽ nhánh khác của `_route_plain_text`
   (không qua Gemini phân loại, không qua Trợ lý AI). Bot đóng dấu `hoi_va`, gắn việc, gửi Celery
   `agent.ask_task(task_id, message_id)` vào hàng đợi `agent_code` — câu hỏi đọc lại từ sổ theo
   id tin, không truyền chữ qua hàng đợi. Nối cả sau dấu `hoi_va` là cố ý: runner trả lời mất cả
   phút, nhắn bổ sung trong lúc chờ là phần tiếp của câu hỏi. Đổi lại, muốn giao việc MỚI trong
   10 phút sau khi hỏi thì phải chờ hết cửa sổ hoặc gõ `/gom`.
3. Runner (`coder.answer_patch_question`): tìm `session_id` ở lượt CODE OK gần nhất, worktree phải
   còn; mở dòng `tab_agent_run` trạm **`STAGE_ASK = 21`**; chạy `claude -p --resume <phiên>
   --allowedTools "Read,Glob,Grep,Bash(git diff:*),Bash(git status:*),Bash(git log:*)"
   --max-turns 15`, trần 10 phút — **chỉ đọc**, không Edit/Write, không pytest. Đề bài dặn: trả lời
   ngắn bằng Markdown đơn giản (không bảng, không tiêu đề vì hiện trên Telegram); câu hỏi thực chất
   là đòi đổi bản vá thì nói vậy và bảo đại ca bấm «Sửa», đừng tự sửa. Hai đường **không trộn**:
   hỏi là để hiểu, đổi bản vá là lượt CODE mới theo kế hoạch mới.
4. Trả lời: `reply(markdown=True)` (`**đậm**` → `<b>`), dấu `tra_loi_va`, nút **«Hỏi tiếp»**;
   `artifact` của lượt ASK giữ phiên + câu hỏi + câu trả lời + số lượt + phút. Hỏng (phiên mất,
   worktree mất, quá giờ) → lượt ASK ghi lỗi, Telegram nhận một câu lý do + nút **«Hỏi lại»**;
   **trạng thái việc không đổi**. Riêng lỗi `No conversation found` được dịch thành "phiên không
   còn trong runner — bấm Sửa để bot làm lại từ đầu" (đúng cảnh AI-0005 sau lần recreate 22/09).

Tổng kết của bot trên thẻ kết quả nay cũng đi qua `md_to_html` (trước đây gửi thô nên hiện
`**đậm**` và `1.` `2.` như dấu chữ) — quá trần thì lùi về bản thoát HTML như cũ.

### Luật nhánh và deploy thử VPS (ai-CR-014 — XONG 22/09/2026)

Đại ca 22/09/2026 chốt bốn câu chặn của bản đặt chỗ, gọn lại thành một luật: **muốn gộp
vào nhánh nền là phải hỏi, đại ca đồng ý mới làm; deploy thử thì dùng ngay stack dev và
khóa SSH có sẵn trên máy; «hỏi trước một tiếng» chỉ có nghĩa là hỏi để đại ca xác nhận,
đồng ý thì chạy ngay hoặc hẹn giờ.** Nguyên văn bốn câu trả lời nằm ở `change-log-ai.md`.

| Câu chặn cũ | Đại ca quyết | Bot làm |
|---|---|---|
| Deploy thử lên đâu | Không dựng stack thứ ba. Bot đẩy nhánh riêng rồi HỎI có gộp/lên dev không; đồng ý thì gộp thẳng `erp-v2` + deploy dev; sau đó bảo bỏ/trả về thì thu hồi | Nút «Gộp erp-v2 + deploy dev» trên thẻ kết quả → thẻ hỏi → «Đồng ý» mới chạy; thẻ sau deploy có «Thu hồi» |
| Khóa SSH riêng cho bot | Dùng khóa đang có trên máy đại ca | `AGENT_VPS_SSH_KEY_FILE` trong `.env` chỉ là ĐƯỜNG DẪN, compose bind-mount chỉ-đọc vào `/root/vps_ssh_key` của runner; giá trị khóa không qua chat, không vào git, không vào tiến trình `claude` |
| «Hỏi trước 1 tiếng» | = hỏi để xác nhận; OK thì đẩy luôn, hoặc đại ca hẹn giờ | Ba nút «Đồng ý: gộp + deploy ngay» · «Hẹn giờ» (nhắn `14:30` · `20h` · `45 phút nữa` · `8h sáng mai`…) · «Thôi, chưa gộp»; vòng beat mỗi phút nhặt lịch hẹn tới giờ |
| Branch protection | Giữ như hiện tại (chưa bật); merge là phải hỏi ý | Lệnh gộp chỉ phát ra từ nút «Đồng ý» của đúng chat đại ca; không có đường tự động nào khác |
| Gộp mặc định bằng gì (23/09) | *"em có thể merge code theo lệnh của anh rồi, còn khi anh muốn tự merge thì em mới gửi link"* | Thẻ kết quả xếp «Gộp erp-v2 + deploy dev» ĐẦU; nút PR đổi nhãn «Gửi link PR để anh tự merge», chỉ đẩy nhánh + mở PR khi bấm; `AGENT_PR_ENABLED` giữ tắt |

**Luồng một lượt gộp** (`coder.merge_and_deploy`, chạy trong `agent-runner`, task
`agent.deploy_task` hàng đợi `agent_code`):

1. Việc sang trạm **«Đang gộp + deploy dev»** (`ST_DEPLOYING = 12`), lượt ghi sổ
   `AgentRun` giai đoạn `STAGE_DEPLOY = 22`.
2. Worktree `agent-merge` cắt lại từ `origin/erp-v2` mỗi lượt; `git merge --no-ff --no-edit`
   nhánh `bot/<mã>-<slug>` với danh tính *Agent Hub bot*; xung đột → `merge --abort`, việc về
   REVIEW, nhánh nền không đổi, thẻ mời gộp lại hoặc đi đường PR.
3. `git push` lên `refs/heads/erp-v2` **không `--force`**, khóa GitHub đi bằng `GIT_CONFIG_*`
   như ai-CR-012. Đẩy xong ghi `artifact.merged + merge_sha` và commit NGAY, trước khi SSH —
   hỏng giữa chừng vẫn biết mã đã ở nhánh nền.
4. SSH lên VPS bằng `bash -s`, script qua stdin (không lên dòng lệnh, không lên lịch sử shell):
   `cd ~/procurement-tool-dev · git fetch · git reset --hard origin/erp-v2 · echo HEAD=… ·
   docker compose --env-file .env.dev -f docker-compose.dev.yml up -d --build <service>` — service
   suy từ tệp bản gộp đụng: `backend/` → api + celery-worker + celery-beat · `frontend-v2/` → erp ·
   `frontend/` → web · `help-center/` → help; chỉ doc/test thì không build gì. HEAD VPS trả về
   phải khớp bản vừa gộp, không thì báo có bản đẩy khác chen vào.
5. Chờ `/api/health` của dev trả 200 (12 lần × 10 giây), rồi việc sang **ST_PROD** +
   `deployed_dev_at`, thẻ «Đã gộp vào erp-v2 … Thử ở deverp» với nút «Thu hồi khỏi erp-v2 +
   dev» · «Hỏi thêm về bản vá» · «Xong, đóng việc».

**Hỏng ở đâu thì về đâu**: hỏng TRƯỚC khi đẩy → REVIEW như chưa có gì; hỏng SAU khi đẩy (SSH,
build, health) → ST_PROD với `deployed_dev_at` trống + nút «Deploy dev lại» (chỉ chạy lại bước
SSH, không gộp lần hai) và «Thu hồi». Worker chết giữa chừng thì lượt «đang chạy» quá
`DEPLOY_TIMEOUT_SEC + 15 phút` được tự đóng ở lần bấm sau, việc không kẹt mãi.

**Thu hồi** (`coder.revert_and_deploy`, `STAGE_REVERT = 23`): thẻ hỏi lại lần nữa → `git revert
--no-edit -m 1 <bản gộp>` trên nhánh nền (thêm bản đảo ngược, không xóa lịch sử) → đẩy không
`--force` → deploy dev lại → việc về **«Đang hỏi lại»** kèm ghi chú; đại ca nhắn cần sửa gì rồi
`/gom` để bot làm lại từ đầu (git không gộp lại cùng nhánh sau khi revert, nên không có nút «gộp
lại»). `merged_sha_for` đọc sổ lượt từ mới về cũ: gặp thu hồi OK là hết, gặp lượt gộp có `merged`
là bản đang sống — mọi cửa (nút, giờ hẹn, chạy lại) đều hỏi nó.

**Biên an toàn của bước SSH**: chạy bằng tiến trình worker (root, môi trường sạch chỉ
`PATH/HOME/LANG`), KHÔNG hạ quyền xuống `runner` — vì khóa phải ở 0600 và bind mount từ Windows
là 0644, nên mỗi lượt chép khóa ra tệp tạm 0600 dưới `/root`, đổi CRLF → LF, xóa ngay sau lượt kể
cả khi hỏng. Tiến trình `claude` không thấy khóa (`build_env` dựng từ rỗng, không có biến
`AGENT_VPS_*`), không có `ssh` trong `--allowedTools`, và lệnh cấm `ssh`/`docker compose` ở bộ
quy tắc §E vẫn nguyên với nó — bước deploy là mã của hub, nằm ngoài lượt `claude`. Máy chủ được
nhớ ở `/worktrees/.known_hosts` (`StrictHostKeyChecking=accept-new`).

**Hẹn giờ** không dùng `eta` của Celery (việc có eta nằm trong bộ nhớ worker, restart là mất):
lịch hẹn là dòng `AgentRun` pha `hen_gio` + `scheduled_for`; beat `agent-deploy-due` mỗi phút gọi
`service.dispatch_due_deploys` (chạy ở `celery-worker`), tới giờ thì đổi pha `dispatched` rồi mới
giao runner, nên không giao hai lần. «Hủy hẹn» đóng dòng đó. Tới giờ mà việc không còn chờ gộp
(đã đóng, đã lên dev) thì lượt tự đóng lỗi, không chạy.

### Chống bot đi lạc — số thật

Runner `git add -A` rồi so danh sách tệp đã đụng với `plan_files`:

| Điều kiện | Kết cục |
|---|---|
| Đụng **tệp cấm** (`.env*`, khóa, migration, seed prod, `permissions.py`, `scoping.py`, workflow CI, `CLAUDE.md`, `.claude/`, bộ quy tắc, sổ quyết định) | **Dừng, không commit**, `git reset`, việc sang `NEEDS_INPUT` |
| Hơn **`AGENT_MAX_FILES_TOUCHED`** (25) tệp | Dừng như trên — việc to vậy phải chẻ |
| Hơn **30 %** số tệp nằm ngoài `plan_files` (bài kiểm và tài liệu `.md` không tính, ai-CR-015) | Dừng như trên |
| Không sửa tệp nào | Sang `NEEDS_INPUT`, in tổng kết của bot để đại ca đọc vì sao |

Ngoài ra `coder.approve_gate` chặn **trước khi giao**: kế hoạch không có `plan_files` (luật B2)
hoặc `plan_files` đã đụng tệp cấm thì bấm Duyệt cũng không giao — trả lời ngay trên Telegram.

### Thẻ kết quả

Một tin HTML: mã việc · nhánh · **n tệp · +a/−d dòng · số lượt · phút · ~$** · từng tệp (đánh dấu
*NGOÀI kế hoạch*) · cổng kiểm · «Bot tổng kết» (Markdown → HTML, cắt trong trần 3 500 ký tự) · nút
**Hỏi thêm về bản vá** (ai-CR-013) · nút **Bỏ việc này**.
Kèm **tệp `<mã>.diff`** gửi bằng `sendDocument` để đọc trọn bản vá trên điện thoại. Mọi thứ ghi
vào `tab_agent_run` (`provider = claude_code`, model, token, chi phí, `artifact` = phiên + tệp +
cổng kiểm + tổng kết).

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
AGENT_LONG_POLL=false              # true = có `agent-poller` riêng giữ kết nối, vòng beat kéo tin tắt (ai-CR-008)
AGENT_TRIAGE_BATCH=20              # số tin tối đa gom trong một lượt TRIAGE
AGENT_DAILY_TASK_CAP=5

# ---- bậc 2 (ai-CR-011) — cả cụm chỉ `agent-runner` đọc, trừ AGENT_CODER_ENABLED (poller cũng đọc)
AGENT_CODER_ENABLED=false          # false = bấm Duyệt vẫn dừng ở PLAN như bậc 1
AGENT_CODER_CMD=claude
AGENT_CODER_MAX_TURNS=80           # --max-turns của một lượt claude
AGENT_WORKTREE_ROOT=/worktrees     # volume agent_worktrees
AGENT_REPO_SOURCE=/src-repo        # .git của kho chính, mount chỉ đọc
AGENT_BASE_BRANCH=erp-v2           # nhánh gốc của mọi nhánh bot/*
AGENT_RUNNER_USER=runner           # git/claude/pytest hạ xuống người dùng này
AGENT_RUN_TIMEOUT_SEC=1800         # trần một lượt claude; Celery giết ở +900 giây
AGENT_MAX_FILES_TOUCHED=25
CLAUDE_CODE_OAUTH_TOKEN=           # `claude setup-token` — đại ca TỰ dán, không qua chat, không commit
# ---- bậc 2 GĐ2a (ai-CR-012) — chỉ `agent-runner` đọc
AGENT_PR_ENABLED=false             # true = tự đẩy + mở PR sau commit; false = nút đẩy tay trên thẻ
AGENT_GITHUB_TOKEN=                # PAT chi tiết (Contents + Pull requests R/W, một kho) — đại ca TỰ dán
AGENT_GITHUB_REPO=giabaohb99/procurement-tool
AGENT_GITHUB_API_URL=https://api.github.com
# ---- bậc 2 GĐ2b·2 (ai-CR-014) — gộp erp-v2 + deploy dev, CHỈ sau khi đại ca bấm «Đồng ý»
AGENT_DEPLOY_ENABLED=false         # false = thẻ kết quả không có nút gộp; hẹn giờ cũ tới giờ cũng không chạy
AGENT_VPS_HOST=                    # VPS dev; trống = nút gộp báo chưa khai
AGENT_VPS_PORT=22
AGENT_VPS_USER=
AGENT_VPS_SSH_KEY_FILE=            # ĐƯỜNG DẪN khóa riêng trên máy đại ca; chỉ compose đọc để bind-mount
                                   # chỉ-đọc vào /root/vps_ssh_key của agent-runner. Không dán nội dung khóa
# AGENT_VPS_DEV_DIR=~/procurement-tool-dev
# AGENT_VPS_DEV_COMPOSE_ARGS=--env-file .env.dev -f docker-compose.dev.yml
# AGENT_DEV_HEALTH_URL=https://devthumua.degoholding.vn/api/health
# AGENT_DEV_UI_URL=https://deverp.degoholding.vn
# ---- ảnh chụp lỗi (ai-CR-035) — volume agent_files, runner chỉ đọc
# AGENT_FILES_DIR=/agent-files
# AGENT_FILE_MAX_MB=20
# ---- phiếu hỗ trợ ERP làm nguồn việc (ai-CR-037) — trống là tắt cửa đó
# AGENT_TICKET_ASSIGNEE=<email tài khoản ERP của bot>     # nhóm hỗ trợ giao phiếu cho tài khoản này
# AGENT_TICKET_DEPARTMENTS=Phần mềm,IT                    # nhãn «Bộ phận / Nhóm», chỉ phiếu MỚI
# ---- đăng nhập ERP trong Telegram (ai-CR-038)
# AGENT_LINK_ENABLED=true
# AGENT_LINK_DAYS=30
# AGENT_LINK_CODE_MINUTES=10
# AGENT_TELEGRAM_BOT_USERNAME=<tên bot, không @>          # để trang cá nhân dựng link mở thẳng bot
# ---- sổ quyết định (ai-CR-015) — compose mount ./doc/agent-hub vào /agent-docs
# AGENT_PLAYBOOK_PATH=/agent-docs/03-so-quyet-dinh.md   # không có tệp thì bot chạy như trước
```

**Key Gemini để RIÊNG** (`QĐ-AI-7`, đại ca chốt 18/09/2026). `core/config.py` đã có
`GEMINI_API_KEY` của Trợ lý AI, nhưng bot **không dùng chung**: bot chạy nền, gọi liên tục, đốt
hết hạn mức thì Trợ lý AI đang phục vụ người thật chết theo — mà lúc đó không ai biết vì sao.
Để riêng còn đo được chi phí của bot mà không phải trừ nhẩm.

**Không có biến nào giữ khóa API Anthropic** (`ANTHROPIC_API_KEY`) — đó là chủ ý (QĐ-AI-3).
`CLAUDE_CODE_OAUTH_TOKEN` là khóa **đăng nhập của subscription**, một thứ khác: nó cố ý **không
khai trong `Settings`** để không tiện tay đọc được từ mọi chỗ trong ứng dụng; chỉ `coder.build_env`
lấy nó từ `os.environ` và chỉ đưa vào tiến trình `claude`. Khóa hết hạn hoặc sai thì runner báo
`401` kèm câu «chạy lại `claude setup-token`». Không có `AGENT_MAX_CONCURRENT_RUNS`: số việc song
song là `-c 1` của worker, đổi thì đổi lệnh chạy, không đổi cờ.

### `AGENT_ASSISTANT_USER` — biến nguy hiểm nhất trong bảng trên (QĐ-AI-10, 18/09/2026)

Bot còn làm **cửa Telegram cho Trợ lý AI có sẵn**: câu hỏi đi thẳng vào
`assistant.service.ask()` và được trả lời ngay tại chỗ, **không đẻ ra task nào**; còn lời nhờ
sửa phần mềm mới vào luồng INBOX → TRIAGE → PLAN. Một bot, hai nhánh — vì đại ca chỉ có một
cái điện thoại, bắt nhớ hai con bot là thua.

⚠️ **Cách chia hai nhánh đã ĐỔI ngày 22/09/2026 (`ai-CR-003`).** Bản đầu bắt gõ tiền tố `/hoi`
mới được trả lời, chữ thường mặc định là giao việc. Đại ca bác ngay lần chạy thật đầu tiên:
*"trợ lý AI đâu có mấy cái lệnh này đâu, hỏi là trả lời luôn mà"*. Nay **mỗi tin chữ thường đi
qua một lượt Gemini phân loại ý định** (`manager.run_intent`) rồi mới rẽ; mập mờ thì bot hỏi lại
kèm hai nút *Trả lời luôn* / *Ghi thành việc* chứ không đoán. Các lệnh `/` vẫn sống, nhưng nay
chỉ là **đường tắt**. Kèm theo đó, tin bắt đầu bằng `/` được đóng dấu `action` nên không lọt vào
vòng gom nữa — trước đó chính chữ `/start` đẻ ra một đầu việc tên *"Xử lý tin nhắn lệnh /start"*.

**Mục tiêu trước mắt đại ca chốt 22/09/2026: nhánh hỏi đáp phải là đúng Trợ lý AI trên web,
chỉ khác chỗ đứng là Telegram** (`ai-CR-006`). Ba thứ web có mà Telegram lúc đầu thiếu, nay đã bù:

- **Định dạng.** Trợ lý trả Markdown, web render bằng `react-markdown`; Telegram in thô. Nay
  `telegram.md_to_html()` đổi sang HTML rút gọn: đậm · nghiêng · mã · link · gạch đầu dòng ·
  tiêu đề thành chữ đậm · bảng thành từng dòng ô cách nhau bằng ` · `. Telegram **không có** phông
  chữ, bảng kẻ ô, màu — đó là trần của nền tảng, không phải của bot.
- **Mạch hội thoại.** Web giữ cả cuộc trò chuyện trong một hội thoại; Telegram không có khái niệm
  đó nên bot lấy các cặp hỏi-đáp **gần đây** (`hoi` / `tra_loi`, tối đa 8 lượt, trong 2 giờ, trần
  6000 ký tự) đưa vào `ask(history=...)`. Sổ giữ Markdown gốc để lượt sau model đọc đúng như web.
- **Link thật.** Web tự nối gốc cho đường dẫn tương đối, Telegram thì không → bot nối
  `FRONTEND_URL` vào. Tool nào trả bản ghi có màn chi tiết thì phải kèm `url`, không thì model bịa.

Còn thiếu so với web: đăng nhập theo từng người (`ai-CR-004`), đại ca gửi tệp/ảnh **lên** cho bot,
và model — local đang chạy Gemini hạng miễn phí (dễ dính 429), web dev/prod chạy Claude.

**Kết quả tool đi ra Telegram (`ai-CR-009`, 22/09/2026).** Bot dùng lại nguyên bộ tool của Trợ lý
AI (không có allowlist riêng), nhưng `ask()` trả về ba loại khối mà chữ không chở được, nay
`service.deliver_tool_results()` xử sau câu trả lời:

- **Khối `file`** (tool xuất báo cáo Excel/Word). `download_url` của web cần Bearer, Telegram bấm
  vào là 401 → bot tải byte từ kho và gửi bằng `sendDocument` (multipart, trần 50 MB của Bot API).
  Chốt sở hữu **chép y đường tải web**: tệp phải do tài khoản bot tạo **và** khóa nằm trong
  `assistant-report/` — model bịa `id` không thành lối tải kho. Gửi hỏng thì đưa link tải web.
- **Khối `proposal`** (tool đề xuất sửa phiếu). Thành thẻ *Đề xuất sửa* (từng ô trước → sau, ghi rõ
  phiếu CHƯA sửa, hạn 15 phút) + hai nút **Xác nhận sửa** / **Không sửa**. `callback_data` chỉ chịu
  64 byte nên **token Fernet nằm trong sổ**: dòng `tab_agent_message` chiều ra, dấu `de_xuat`, thân
  là JSON khối proposal; nút chỉ mang id dòng. Bấm xác nhận → gọi **đúng
  `update_tool.confirm_update()` của web**, không có đường ghi riêng cho bot; hết hạn / mất quyền /
  phiếu đã đổi trạng thái đều ăn câu lỗi của web. Xong đóng dấu `da_sua` hoặc `bo_sua`, bấm lần hai
  chỉ được câu *"đã xử rồi"*.
- **Khối `draft`** (biểu mẫu nháp, vd đơn nghỉ phép). Form không dựng được trong chat → chỉ báo và
  đưa link `/assistant` trên web.

Bốn dấu mới `tep` · `de_xuat` · `da_sua` · `bo_sua` là tin **chiều ra**, `_recent_turns` chỉ lấy
`hoi` / `tra_loi` nên chúng không chen vào mạch hội thoại. Hệ quả: mọi tệp và mọi đề xuất gắn với
tài khoản `AGENT_ASSISTANT_USER` — đổi tài khoản đó là đổi luôn ai được xác nhận sửa phiếu.

⚠️ **Trạm phân loại phải đọc trong mạch, không đọc một câu trơ trọi (`ai-CR-007`, 22/09/2026).**
Ca lộ ra: Trợ lý hỏi *"nghỉ ngày nào, lý do gì?"*, đại ca đáp *"thứ 6, đi du lịch"*, câu đáp đi
qua trạm phân loại rời và thành đầu việc sửa mã AI-0004. Nay ba chốt ở `_route_plain_text`:

- **Bot vừa hỏi lại thì tin kế là câu trả lời.** Tin hội thoại gần nhất của chat là câu trả lời
  của Trợ lý AI **có dấu hỏi** và cách tin mới chưa quá `FOLLOW_UP_WINDOW` (10 phút, đồng hồ DB)
  → đi thẳng Trợ lý AI, **không tốn lượt phân loại**, không phụ thuộc hạn mức Gemini. Dấu hỏi là
  chốt hẹp cố ý: bot trả lời xuôi rồi đại ca báo *"màn đơn hàng lỗi lọc ngày"* là việc mới.
- **Phân loại có mạch.** `run_intent(text, context=)` nhận lượt hỏi-đáp gần nhất. Câu nhắc chia
  lại ranh: `hoi` = mọi thứ Trợ lý AI làm được — tra cứu, **nhờ làm nghiệp vụ** (tạo đơn nghỉ
  phép, lập báo cáo, duyệt), **và** trả lời bot; `viec` = chỉ **nhờ sửa phần mềm**.
- **Phân loại hỏng thì hỏi lại kèm hai nút**, không còn âm thầm xếp vào INBOX (bản `ai-CR-003`
  rơi về giao việc: một câu hỏi gặp lúc 429 là 90 giây sau có thẻ việc).

Hệ quả cần nhớ: mặc định của bot nay **nghiêng về Trợ lý AI**; vào sổ việc sửa mã là đường hiếm
hơn và luôn có người duyệt phía sau (QĐ-AI-5).

Chỗ nguy: **Trợ lý AI lọc dữ liệu theo người đăng nhập**, mà Telegram thì không có đăng nhập.
Nên phải chỉ đích danh một tài khoản ERP để chạy dưới quyền người đó.

- Để **trống** = tắt hẳn nhánh hỏi đáp (cả `/hoi` lẫn câu hỏi chữ thường). Đó là mặc định.
- **Đừng khai tài khoản quản trị.** Ai nhắn được cho bot sẽ đọc được đúng những gì tài khoản
  này đọc được — kể cả `employee_sensitive` nếu tài khoản đó có.
- Hàng rào duy nhất còn lại là `AGENT_TELEGRAM_CHAT_ID`. Nó là một con số, không phải mật khẩu.
- Tài khoản bị khóa (`is_active = false`) thì nhánh hỏi đáp từ chối chạy, không âm thầm chạy không
  phạm vi.

---

## 10. Lộ trình bốn bậc

| Bậc | Gồm gì | Bot được đụng mã nguồn? |
|---|---|---|
| **1** | **Năm** bảng sổ · Telegram kéo tin (poller riêng giữ kết nối 25 giây từ `ai-CR-008`; stack không có poller thì beat 10 giây) + nút · Gemini TRIAGE + PLAN · Qdrant index tài liệu (kho riêng `agent_docs`) · nhánh `/hoi` gọi Trợ lý AI. **Nguồn ticket chỉ Telegram, không màn hình, xem sổ bằng Adminer.** Đầu ra chỉ là in PLAN ra Telegram và ghi vào sổ. | Không |
| **2** | `agent-runner` + `claude -p`, nhánh riêng, **mở PR, hoặc gộp `erp-v2` chỉ khi đại ca bấm «Đồng ý» trên Telegram**. **GĐ1 xong 22/09/2026 (ai-CR-011)**: Duyệt → runner sửa mã trong worktree riêng → pytest phần vừa sửa → commit trong container → thẻ kết quả + tệp `.diff` về Telegram. **GĐ2a xong 22/09/2026 (ai-CR-012)**: đẩy nhánh lên GitHub + mở PR vào `erp-v2` (tự động theo cờ, hoặc nút trên thẻ) — PR #95 là PR đầu tiên do bot mở. **GĐ2b·1 xong 22/09/2026 (ai-CR-013)**: nút «Hỏi thêm về bản vá» → `claude -p --resume` đúng phiên, chỉ đọc, trả lời trên Telegram; phiên cất trong volume worktree. **GĐ2b·2 xong 22/09/2026 (ai-CR-014)**: nút «Gộp erp-v2 + deploy dev» → thẻ hỏi → đồng ý/hẹn giờ → runner `merge --no-ff` + đẩy + SSH deploy dev + health; «Thu hồi» = `git revert -m 1` + deploy lại. GĐ3 = cổng kiểm frontend (xem §7) | Có, trong worktree; PR trên GitHub; bản gộp trên `erp-v2` + dev VPS khi đại ca đồng ý |
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
| Runner chưa chặn được egress (compose không có allowlist tên miền) — bot lý thuyết gửi được mã đi bất kỳ đâu | **Vừa** | Ghi nhận mở từ ai-CR-011. Chặn tạm bằng: worktree không có bí mật nào (`.env` không nằm trong git), `--allowedTools` không có `curl`/`wget`/`Bash` tự do. Dứt điểm ở GĐ sau bằng proxy allowlist |
| `CLAUDE_CODE_OAUTH_TOKEN` là khóa đăng nhập subscription của đại ca, nằm trong `.env` của stack bot | **Vừa** | Chỉ đưa vào tiến trình `claude` (môi trường sạch, `git`/`pytest` không thấy) · không khai trong `Settings` · runner không mount home · khóa xoay bằng `claude setup-token` |
| `AGENT_GITHUB_TOKEN` ghi được vào kho (Contents R/W) — bot đẩy được lên `main`/`erp-v2` | **Vừa** | Mã runner đẩy `bot/*` (có `--force`) và `erp-v2` (KHÔNG `--force`, chỉ từ `merge_and_deploy`/`revert_and_deploy` sau nút «Đồng ý» của đúng chat đại ca — ai-CR-014); không bao giờ đẩy `main`; khóa không vào tiến trình `claude`, không lên dòng lệnh. Branch protection trên GitHub: đại ca 22/09 giữ như hiện tại (chưa bật). **22/09/2026: giá trị khóa này bị in ra bản ghi phiên làm việc của trợ lý khi rà `.env` — kiến nghị cấp lại PAT** |
| Khóa SSH của đại ca (`~/.ssh/id_ed25519_vps`) bind-mount vào `agent-runner` để deploy dev | **Vừa** | Chỉ-đọc; tiến trình worker (root) chép ra bản 0600 tạm rồi xóa ngay sau lượt; `claude` không thấy (`build_env` sạch, không `ssh` trong allowedTools); script deploy dựng toàn bộ từ `settings`, không nhận chữ từ bản vá hay Telegram; cờ `AGENT_DEPLOY_ENABLED` tắt là không có đường nào tới SSH. Khóa riêng cho bot với `command=` khóa cứng để sau, đại ca chọn dùng khóa sẵn có |
| Phiên Claude Code từng nằm trong lớp ghi của container (`~/.claude` của `runner`), mất mỗi lần `up --force-recreate` — nút hỏi thêm báo "phiên không còn" | Vừa | Từ ai-CR-013: `CLAUDE_CONFIG_DIR` trỏ vào volume `agent_worktrees`; kiểm chứng `--resume` sống qua recreate. Phiên của việc TRƯỚC 22/09 (AI-0005) đã mất, không cứu |
| `--permission-mode acceptEdits` cho bot ghi mọi tệp trong worktree, danh sách cấm ghi chỉ chặn được SAU (không commit) | Vừa | Worktree là bản checkout sạch (không `.env`, không khóa); tệp cấm bị đụng thì `git reset`, không commit, leo thang. Cấm ĐỌC thì thi hành bằng «không có gì để đọc» |
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

---

## 13. Hướng mở rộng đã chốt 24/09/2026 — «trợ lý mở»

Bậc 1–2 ở trên giữ nguyên. Từ 24/09/2026 đại ca chốt thêm ba hướng, ghi chi tiết và lộ trình theo
phase ở [`04-danh-sach-tinh-nang.md`](./04-danh-sach-tinh-nang.md) (nhóm M, K, P):

1. **Mỗi người tự chọn ứng dụng AI và tự gắn khóa** (Claude, ChatGPT, Gemini, Cursor…); hệ thống chỉ
   cung cấp công cụ qua một **cổng MCP trên backend ERP**, dùng CHUNG bộ tool với Trợ lý web và
   Telegram. Đại ca chấp nhận rủi ro dữ liệu ERP đi sang nhà cung cấp AI do từng người chọn. Làm trên
   **web trước**, rồi mở rộng Telegram và Zalo dùng chung lõi. Mỗi người tự nối Google (Drive, Lịch)
   của mình bằng OAuth riêng, khóa lưu mã hóa.
2. **Ai được ra lệnh sửa mã** không cấu hình trên web, không build, không khởi động lại: đại ca
   **nhắn cho bot** («cho anh Được quyền gộp dev»), bot hỏi lại rồi ghi sổ (`tab_agent_grant`), mỗi lần
   cấp/gỡ đều báo lại và tra lại được. Chỉ chat của đại ca (`AGENT_TELEGRAM_CHAT_ID` khai cứng trong
   `.env`) cấp được. Ba cấp: báo lỗi (ai cũng được) · duyệt kế hoạch · gộp dev. **Prod không cấp cho ai.**
   Người ra lệnh KHÔNG cần SSH hay quyền GitHub — khóa nằm ở bot và bị giới hạn (§11: khóa riêng của
   bot thay khóa của đại ca, `main` bảo vệ bằng PR).
3. **Bot lên ERP dev** (phase 2): gộp phần bot vào `erp-v2` để phiếu bot tạo là phiếu thật và link bấm
   được trên điện thoại. Chừng nào chưa lên, bot chạy trên máy đại ca với DB riêng `dego-agent`.

