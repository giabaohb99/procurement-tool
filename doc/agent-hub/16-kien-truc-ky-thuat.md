# 16 — Kiến trúc kỹ thuật: AI của ERP và bot tự sửa phần mềm

> Bản 1.0 · 09/10/2026. Viết lại gọn từ các tài liệu 01, 05, 06, 07, 08, 09, 13, 14 và sổ `change-log-ai.md`, đối chiếu
> với mã trên nhánh `erp-v2` ngày 09/10/2026. Chỗ nào tài liệu và mã khác nhau thì theo **mã**; chỗ chưa đối chiếu được
> thì ghi «chưa kiểm». Tài liệu gốc vẫn giữ để tra sâu (mục 6).
>
> Hai khối được mô tả: **(A) AI của ERP** — Trợ lý AI trên web và bot Lạc Lạc trên Telegram / Zalo; **(B) bot tự sửa
> phần mềm** — nhận việc, rà mã, sửa, kiểm, gộp, deploy dev, bằng Claude Code chạy trên «máy sửa mã».

---

## 1. Tổng quan một trang

```
 Người dùng: đại ca (chủ bot) · nhân viên đã nối tài khoản ERP · ứng dụng AI ngoài (MCP)
      │ web                │ Telegram           │ Zalo A (bot) / B (tk công ty)  │ MCP
      ▼                    ▼                    ▼                                ▼
╔═════════════════════════ VPS (dev; prod CHƯA có bot / dịch vụ AI) ═══════════════════════╗
║ STACK ERP (docker-compose.dev.yml)          STACK DỊCH VỤ AI (-p agent-hub)             ║
║ ┌─────────────────────────────────┐        ┌─────────────────────────────────────────┐  ║
║ │ erp      giao diện v2 (deverp)  │        │ agent-api    app.agent_main, :8000       │  ║
║ │ api      FastAPI, AGENT_MODE=erp│ ─(1)─► │              (health 127.0.0.1:8020)     │  ║
║ │   proxy.py chuyển tiếp web/MCP  │        │ agent-poller kéo tin Telegram/Zalo, xử lý│  ║
║ │   cổng B /api/agent-gw/*  ◄─────┼──(2)── │ agent-worker Celery -c 2 (việc nặng)     │  ║
║ │ celery-worker · celery-beat     │        │ agent-beat   lịch nền                    │  ║
║ │ redis · qdrant (kb_docs: HDSD)  │        │ zalo-listener Node + zca-js (Zalo B)     │  ║
║ └───────────────┬─────────────────┘        │ redis-agent  hàng đợi + vé máy sửa mã    │  ║
║                 │                          │ qdrant-agent agent_docs · agent_personal │  ║
║                 │                          │ redis-agent-forward 127.0.0.1:16379      │  ║
║                 ▼                          └───────────────┬─────────────────────────┘  ║
║   MySQL procurement-mysql (mạng dego-db): DB ERP procurement_dev │ DB agent_hub ◄─────┘   ║
║                                            127.0.0.1:13306 (procurement-db-forward)      ║
╚══════════════════════════════════▲══════════════════════════════════▲═══════════════════╝
                                   │ (4) deploy.sh qua SSH            │ (3) đường hầm SSH
                                   │     (máy có cờ deploy)           │     chỉ mở 13306 + 16379
 MÁY SỬA MÃ (máy đại ca; -p agentrunner, docker-compose.runner.yml)    │
 ┌──────────────────────────────────────────────────────────────────────┴──────────────┐
 │ tunnel (ssh -L)  ── agent-runner: Celery -c 1, hàng đợi agent_code.<tên máy>          │
 │                     claude -p (gói Claude Code của chủ máy) · git worktree bot/* ·    │
 │                     cổng kiểm pytest / frontend-v2 · ghi sổ tab_agent_* qua MySQL     │
 └──────────────────────────────────────┬───────────────────────────────────────────────┘
                                        │ (5) git push bot/* · gộp erp-v2 khi được «Đồng ý»
                                        ▼
                                     GitHub (giabaohb99/procurement-tool)
```

| Mũi tên | Là gì | Bảo vệ bằng |
|---|---|---|
| (1) ERP → dịch vụ AI | ERP kiểm JWT rồi chuyển `/api/assistant/*`, `/api/agent-hub/*`, `/api/mcp/*` sang `AGENT_SERVICE_URL` | Chữ ký HMAC mang id người dùng (`core/agent_signature.py`) |
| (2) Dịch vụ AI → ERP | Cổng B: hồ sơ người dùng, quyền, chạy công cụ ERP, nháp phiếu, phiếu hỗ trợ, chuông | Cùng chữ ký; ERP chạy công cụ **dưới quyền người đó** |
| (3) Máy sửa mã → VPS | Kéo vé từ Redis dịch vụ AI, ghi kết quả vào DB `agent_hub` | Khóa SSH riêng từng máy, `authorized_keys` chỉ `permitopen` hai cổng; tài khoản MySQL `agent_runner` cấp theo từng bảng |
| (4) Máy sửa mã → VPS | `backend/scripts/deploy/deploy.sh` gửi qua `ssh … bash -s` | Chỉ máy có cờ deploy; khóa SSH của đại ca bind-mount chỉ đọc; `claude` không thấy khóa |
| (5) Máy sửa mã → GitHub | Đẩy nhánh `bot/<mã>-<slug>`; gộp `erp-v2` chỉ sau nút «Đồng ý» | PAT của chủ máy, không vào tiến trình `claude`; không bao giờ đẩy `main` |

Ba chế độ chạy cùng một mã nguồn (`AGENT_MODE`, mục 2.5). Trên dev từ 08/10/2026: ERP chạy `erp`, dịch vụ AI chạy
`service`. Máy local và prod vẫn `embedded` (bot nằm trong stack ERP, một DB).

---

## 2. AI của ERP (Trợ lý AI + bot chat)

### 2.1 Đường đi một câu hỏi

| Bước | Web (Trợ lý AI) | Telegram | Zalo |
|---|---|---|---|
| Nhận tin | `POST /api/assistant/chat` → (dev: ERP chuyển tiếp) → `assistant/controller.py` → `conversation.chat` | `agent-poller` giữ kết nối 25 giây (`telegram.LONG_POLL_TIMEOUT`), `service.poll_once` → `handle_message` chạy **ngay trong poller** | A (bot chính thức, `zalo.py`): luồng phụ trong poller, mã chat `zl:`. B (tài khoản công ty): `zalo-listener` xếp sự kiện, poller kéo `GET /updates`, mã chat `zu:` (riêng) / `zg:` (nhóm). `channels.py` đổi về đúng hình dạng tin Telegram |
| Danh tính | JWT của ERP | Chat đã `/dangnhap <mã 6 số>` (`chat_link.py`, mã lấy ở Trang cá nhân). Chat chủ bot chưa nối thì lùi về `AGENT_ASSISTANT_USER` (trên dev để trống) | Như Telegram |
| Quyền dùng | `require("assistant","read")` | Bắt buộc `assistant.read` (ai-CR-131); chat chủ bot không bị chặn | Như Telegram |
| Câu lệnh nhận ra ngay | — | Mẫu chữ cố định, không gọi AI: `nhớ:`/`quên:`, «tạo», «đúng», nhắc việc, thuật ngữ, máy, môi trường… và các **mạch đang chờ** (hỏi thêm bản vá, giờ hẹn gộp: 10 phút; trả lời câu hỏi kế hoạch: 30 phút; nháp phiếu: 15 phút) | Như Telegram |
| Khóa + trần | Khóa công ty; `AI_DAILY_MSG_LIMIT` (mặc định 50, cấu hình `ai_daily_msg_limit`) kiểm **trước** khi gọi model | Khóa của chính người đó (`user_keys.active_key`); trần `AGENT_USER_DAILY_TURNS` (`_over_daily_cap`) | Như Telegram |
| Phân loại ý định | Không có — loại câu (`kind`) do giao diện gửi | `manager.run_intent`, lượt `STAGE_INTENT = 20`, kèm mạch 2 lượt / 600 ký tự | Như Telegram |
| Lịch sử đưa vào | `HISTORY_LIMIT = 20` lượt của hội thoại | `HISTORY_TURNS = 8` lượt, trong `HISTORY_WINDOW = 2 giờ`, trần `HISTORY_MAX_CHARS = 6000` | Như Telegram |
| Gọi model | `assistant.service.ask(...)` | `answer_question` → cùng `ask(...)` với `provider="agent_gemini"` | Như Telegram |

**Sáu nhãn ý định** (`manager.py`): `hoi` (hỏi / nhờ làm nghiệp vụ / trả lời bot) · `viec` (nhờ sửa phần mềm → vào
INBOX) · `mo_ho` (không chắc → trả lời luôn kèm dòng gợi «ghi việc: …») · `thao_tac` (lệnh trên một việc AI-xxxx: gộp,
deploy, thu hồi, bỏ…) · `tra_cuu` (nghiên cứu web / kiểm chứng / tài liệu nội bộ, `research.py`) · `du_lieu` (đại ca
nhờ sửa dữ liệu bằng lời → luồng thao tác VPS, doc 09 §4). Kèm cờ phạm vi `ca_nhan` để tin cá nhân không vào hàng đợi việc.

**Dựng ngữ cảnh trong `assistant.service.ask`** (dùng chung web và bot):

1. `knowledge.build_system`: gói tri thức tĩnh (`assistant/packs/*.md`), bật prompt caching (`cache_system=True`).
2. Khi mở công cụ: ngày hôm nay + `TOOL_GUIDE` (bản đồ năng lực) + **thuật ngữ** có xuất hiện trong câu (`glossary`) +
   **chân dung người hỏi** (họ tên, chức vụ, phòng ban, công ty — qua `erp.caller_context`).
3. Riêng bot: lời nhắc thêm `persona` (Đậu Đậu / Lạc Lạc, cách xưng hô) + `policy.ASSISTANT_RULES` + các đoạn sự thật
   (nháp phiếu, cách đăng nhập) + **khối sổ nhớ cá nhân** (`personal_memory.prompt_block`: lõi + 5 đoạn kho liên quan).
   Web **không** chèn khối sổ nhớ vào lời nhắc; công cụ sổ nhớ vẫn nằm trong danh mục (hành vi trên web chưa kiểm).
4. `ROUTING` theo loại câu: `lookup` 1024 token · `advice` 2048 token có suy nghĩ · `general` 1536 · `document` 8192
   (đọc tệp). Biến `ai_lookup_model` cho phép chạy câu tra cứu bằng model rẻ hơn.

**Vòng công cụ:** `provider.run_tools(...)` cho model tự gọi công cụ, mỗi công cụ chạy qua `erp.run_tool` dưới danh tính
người hỏi; tối đa **`max_iters = 6` vòng** mỗi câu (mọi adapter), token cộng dồn qua các vòng.

**Trả lời:** web nhận Markdown. Bot đổi Markdown → HTML Telegram (`telegram.md_to_html`), sổ vẫn giữ Markdown gốc cho lượt
sau; rồi `deliver_tool_results` xử ba khối: `file` → gửi tệp bằng `sendDocument`; `proposal` → thẻ «Xác nhận sửa» /
«Không sửa» (gọi đúng `update_tool.confirm_update` của web); `draft` → thẻ tóm tắt chờ «tạo» / «tạo và gửi duyệt».

### 2.2 Lớp mô hình

| Thành phần | Tệp | Ghi chú |
|---|---|---|
| Giao diện chung | `assistant/provider/base.py` | `ChatMessage`, `ChatResult` (token vào/ra/suy nghĩ/cache), `run_tools` |
| Adapter | `provider/claude.py`, `gemini.py`, `openai_compat.py` | `_REGISTRY`: `claude`, `gemini`, `openai`, `openrouter`, `deepseek`, `xai`. Gọi REST bằng `requests`, không SDK |
| Chọn nhà (web) | `provider/__init__.get_provider` | Theo `ai_default_provider` trong cấu hình hệ thống; chưa có khóa thì lấy nhà đầu tiên có khóa |
| Provider của bot | `agent_hub/manager.AgentGeminiProvider` (tên `agent_gemini`) | Lấy khóa đang dùng trong chuỗi khóa của người chat; khóa không phải Gemini thì giao adapter hãng đó |
| Sổ khóa | `agent_hub/ai_keys.py`, bảng `tab_ai_key` | Một bảng cho cả công ty (`owner_type=1`) và cá nhân (`2`); mã hóa Fernet, giữ 4 ký tự cuối; `priority`, `daily_cap`, `model`, `base_url` |
| Chuỗi khóa | `agent_hub/user_keys.py` | Thứ tự: khóa cá nhân → khóa công ty (có trần lượt/ngày) → `.env`. Giữ trong `ContextVar` theo từng tin / việc nền |

**Tự lùi khóa:** lỗi do khóa (402 hết tiền, 429 hạn mức, 401/403 khóa sai — `ai_keys.is_key_problem`) thì nhảy sang khóa
kế và gọi lại, **không báo**; hết chuỗi thì nói thẳng lỗi. Lỗi tạm (503 quá tải) thì đổi sang model dự phòng một lần.
Gemini trả 429 kèm `retryDelay` ≤ 10 giây thì chờ rồi gọi lại đúng một lần (`RETRY_429_MAX_WAIT`).

**Đo token / chi phí:** bot ghi mọi lượt gọi vào `tab_agent_run` (`provider`, `model`, `input_tokens`, `output_tokens`,
`cost_usd`, `stage`). `cost_usd` ước theo bảng `constants.MODEL_PRICES_USD` — **chỉ có giá Gemini**; model lạ ghi 0 (cố
ý). Lượt `claude -p` ghi `total_cost_usd` do CLI trả. Web đọc thẳng các cột `*_tokens` của `tab_assistant_message`
(`usage.py`) cho màn theo dõi chi phí.

### 2.3 Công cụ

Danh mục nằm ở `assistant/tools/` (`tools/__init__._active_specs`). Model **không viết SQL**: mỗi công cụ là một truy vấn
viết sẵn, model chỉ chọn công cụ và điền tham số theo khuôn.

| Nhóm | Tệp | Chạy ở đâu khi tách dịch vụ |
|---|---|---|
| Tra cứu thu mua, hợp đồng, giá, thống kê tùy biến, danh mục | `catalog.py` | ERP (cổng B) |
| Chứng từ thu mua, phiếu của tôi, phiếu chờ tôi duyệt | `procurement_doc_tool.py`, `approval_tool.py` | ERP |
| Công nợ, đề nghị thanh toán | `payable_tool.py` | ERP |
| Văn bản, luồng phê duyệt | `document_tool.py` | ERP |
| Danh bạ, nghỉ phép, phiếu hỗ trợ, việc Dự án | `employee_tool.py`, `leave_tool.py`, `ticket_tool.py`, `work_tool.py` | ERP |
| Hải quan (giá thị trường, thời điểm mua, pháp lý) | `customs_tool.py` | ERP |
| HDSD (Qdrant `kb_docs`) | `rag_tool.py` → `assistant/rag/` | ERP |
| Soạn nháp YCBG / YCMH / nghỉ phép / YCTT | `draft_tool.py` | ERP |
| Đề xuất sửa phiếu, lập bộ tài khoản | `update_tool.py`, `account_setup_tool.py` | ERP |
| Xuất Excel / Word | `export_tool.py` | ERP |
| Thuật ngữ, báo thiếu chức năng | `learning_tool.py` | ERP |
| Sổ nhớ, ghi chú, tìm hội thoại cũ (`search_chat_history`) | `personal_tool.py` | **Dịch vụ AI** |
| Đọc nhóm chat | `group_tool.py` | **Dịch vụ AI** |
| Biên bản họp theo mẫu | `meeting_tool.py` | **Dịch vụ AI** |
| Lịch / Drive Google cá nhân | `google_tool.py` | **Dịch vụ AI** |

Bốn nhóm cuối là `erp.LOCAL_TOOL_MODULES`; mọi tên khác đi `POST /api/agent-gw/tools/run`. Tổng số công cụ model thấy:
doc 14 ghi 66, doc 13 ghi «62 công cụ ERP», doc 07 ghi 49 — **số chính xác chưa kiểm**.

**Gác quyền** (`tools/base.py`, «bảy tầng»): `ToolContext` giữ `db` + **user thật** của người hỏi; chỉ tên có trong danh
mục mới gọi được; mỗi handler tự `ctx.can(entity)` rồi `apply_scope` theo phạm vi của người đó; mỗi lượt ghi audit
(`core/audit.record`). Ở chế độ `service`, dịch vụ AI không có bảng ERP: công cụ chạy ở ERP qua `_Local` — **cùng một mã**
với chế độ nhúng, nên hai chế độ không lệch nhau.

**Công cụ ghi luôn qua nháp / xác nhận:**

- `draft_*` chỉ trả bản nháp. Web: nút mở form điền sẵn, người dùng tự bấm Lưu. Bot: thẻ tóm tắt, người dùng nhắn «tạo»
  / «tạo và gửi duyệt» → `agent_hub/draft_create.py` kiểm lại quyền `create` của chính người đó rồi tạo (ở chế độ
  `service` đi `POST /draft/create` / `/draft/submit`). MCP: `confirm_draft`.
- `propose_document_update`, `propose_account_setup`: chỉ trả bảng cũ → mới; ghi khi người dùng bấm xác nhận (token Fernet
  hạn 15 phút). Không mở qua MCP.
- Sửa dữ liệu hàng loạt bằng lời chỉ dành cho chat chủ bot, đi **cổng duyệt thao tác VPS** (mục 3, doc 08/09): thẻ «đúng»,
  sao lưu bảng trước, lệnh hoàn tác.

### 2.4 Trí nhớ và học

| Thứ | Lưu ở | Cách dùng |
|---|---|---|
| Lõi nhớ cá nhân | `tab_agent_memory`, mỗi người một dòng, Markdown bốn mục, trần `CORE_MAX = 8000` ký tự | Nạp nguyên văn vào mọi câu hỏi của người đó; đệm 600 giây, ghi là xóa đệm |
| Kho ghi chú | `tab_agent_note` + Qdrant `agent_personal` (payload có `user_id`) | Mỗi câu lấy `NOTE_HITS = 5` đoạn liên quan; Qdrant hỏng thì tìm theo tiêu đề. Có dòng «nhớ có hạn» |
| Tóm tắt cuối buổi | `sessions.py` → `tab_agent_note` «Buổi dd/mm HH:MM–HH:MM» | Im lặng 30 phút, ít nhất 3 câu hỏi; vòng 10 phút; lượt `STAGE_SESSION = 28`; không nhắn gì |
| Hồi ức hội thoại | `search_chat_history` (`personal_tool.py`) | Tìm trong sổ tin của chính người đó |
| Sổ thuật ngữ | `tab_setting` khóa `assistant_glossary` (`assistant/glossary.py`) | Chèn đúng từ có trong câu. Dạy bằng câu nhắn ở chat chủ bot. Ở dịch vụ AI đọc / ghi qua cổng B `settings/raw` (ai-CR-128) |
| Vòng tự học | `learning.py`, beat `agent.learning_tick` 5 phút | Đề xuất thuật ngữ nằm chờ tới khi đại ca nhắn «cập nhật thuật ngữ»; chỗ thiếu chức năng lặp `GAP_MIN` lần → mở việc sửa mã nguồn `SRC_GAP = 4` |
| Nhóm chat | `tab_agent_group*`, `groups.py` | Bot ghi lặng tin + tệp nhóm, giữ 90 ngày; người đọc được = thành viên đã nối ERP; câu trả lời tóm tắt nhóm lưu lại (`groups.record_answers`) để xem ở màn «Nhóm chat» `/assistant/groups` |
| Trí nhớ của bot sửa mã | Qdrant `agent_docs` (`memory.py`, nạp `doc/` + `CLAUDE.md`), sổ quyết định `03-so-quyet-dinh.md` (`playbook.py`) | Đưa vào đề bài lập kế hoạch / sửa mã |

Ba hàng rào của sổ nhớ: không ghi bí mật (mật khẩu, khóa, số thẻ) · trùng thì không thêm · `user_id` lấy từ chat đã
đăng nhập, **không bao giờ** là tham số model điền.

### 2.5 Tách dịch vụ (phase 11 — trước gọi là phase S, ai-CR-119)

| `AGENT_MODE` | Tiến trình | DB | Web / MCP | Cổng B / chuyển tiếp |
|---|---|---|---|---|
| `embedded` (mặc định; local, prod) | ERP + bot chung | Một DB | Tại chỗ | Không |
| `service` (dịch vụ AI) | `app.agent_main` + poller + worker + beat | `agent_hub` | Nhận qua chuyển tiếp | Gọi cổng B ở `AGENT_GATEWAY_URL` |
| `erp` (ERP khi đã tách) | `app.main`, không bot | DB ERP | Chuyển sang `AGENT_SERVICE_URL` | Mở `/api/agent-gw/*` |

**Chữ ký máy-nói-máy:** `HMAC-SHA256(AGENT_SERVICE_SECRET, "<ts>.<METHOD>.<path>.<user_id>.<sha256(body)>")`, header
`X-Agent-Ts` / `X-Agent-Sign` / `X-Agent-User`; lệch giờ quá 5 phút thì từ chối; so bằng `compare_digest`. Khóa trùng hai
đầu (`.env.dev` của ERP và `.env.agent`). `zalo-listener` dùng cùng khuôn ký.

- **AI → ERP:** `X-Agent-User` = tài khoản chạy dưới quyền; ERP kiểm tài khoản còn hoạt động rồi chạy như người đó bấm.
  Dịch vụ AI không có «khóa thần».
- **ERP → AI:** ERP kiểm JWT xong mới ký; dịch vụ AI (`core/agent_identity.py`) tin chữ ký, hỏi cổng B `/me` lấy hồ sơ
  (đệm 60 giây); `require(...)` ở dịch vụ AI hỏi cổng `/can`.
- **Không chuyển tiếp:** `/api/assistant/uploads*`, `/api/assistant/files/*`, `/api/assistant/rag/*` (ERP tự phục vụ vì
  đụng kho tệp + HDSD); `/api/agent-hub/internal/*` (chỉ máy-nói-máy, ERP trả 404 cho người dùng web).

**Bảng ở DB nào** (`core/agent_tables.py` là nguồn duy nhất): `tab_agent_*`, `tab_ai_key`, `tab_assistant_conversation`,
`tab_assistant_message` → DB `agent_hub` (alembic riêng `alembic_agent.ini` + `migrations_agent/`). Mọi bảng khác — kể
cả `tab_setting`, `tab_notification`, `tab_ticket`, tài khoản, nhân sự — ở DB ERP, dịch vụ AI chỉ chạm qua cổng B. Bảng
bot cũ trong DB ERP dev **vẫn còn** (chép sang, chưa dọn).

**Hai lỗi đã vá khi dựng trên dev 08/10/2026:**

1. `agent_gateway/proxy.py` gọi dịch vụ AI bằng `requests` chặn ngay trong vòng sự kiện. Dịch vụ AI quay lại hỏi ERP qua
   cổng B (vd quyền `agent_group`) giữa lúc ERP đang chờ → hai bên chờ nhau tới hết 120 giây, mọi API ERP treo theo.
   Vá: `await run_in_threadpool(requests.request, ...)`.
2. `app/agent_main.py` thiếu nạp model `Department` / `Company`: router kéo theo `Employee` / `User`, quan hệ trỏ tới hai
   lớp đó không dựng được → mọi đường có truy vấn trả 500 tới khi khởi động lại. Vá: `from app.modules.company import
   model` và `department` chỉ để đăng ký lớp (không gọi `import app.modules…` vì đè tên `app`).

Bẫy cấu hình: `AGENT_GATEWAY_URL` phải là **tên container** `procurement-tool-dev-api-1`, không phải bí danh `api` — trên
mạng `dego-db` bí danh đó trỏ tới hai máy, lượt gọi rơi luân phiên sang máy không có cổng B (404).

### 2.6 Bảo mật và quyền

| Khóa quyền | Cho phép |
|---|---|
| `assistant.read` | Dùng Trợ lý AI trên web **và** dùng bot (ai-CR-131). Thu quyền là bot thôi trả lời |
| `agent_task` | Xem màn «Việc của bot» `/system/agent-tasks` (chỉ đọc; mọi thao tác vẫn qua Telegram) |
| `agent_group` | Màn «Nhóm chat» + «Người dùng bot»; `write` gỡ được liên kết |
| `agent_ops` | Nhận **bản sao không nút** tin vận hành của bot (ai-CR-132); nút duyệt vẫn chỉ ở chat chủ bot |
| Chat chủ bot (`AGENT_TELEGRAM_CHAT_ID`) | Ra lệnh sửa mã, cấp quyền sửa mã (`tab_agent_grant`), thêm máy, thao tác VPS, sửa dữ liệu bằng lời |

- **Dữ liệu ERP luôn lọc theo quyền người hỏi**: công cụ chạy với user thật, `require` + `apply_scope`; không có tài khoản
  bot đọc hộ (trừ `AGENT_ASSISTANT_USER` ở chat chủ bot chưa nối — trên dev để trống).
- **Không cho AI viết SQL**: Trợ lý chỉ gọi công cụ viết sẵn. Đường duy nhất có SQL do AI soạn là «sửa dữ liệu bằng lời»
  của chủ bot: Claude trên máy sửa mã soạn **một** lệnh, `guardrails.classify_sql` phân loại, thẻ «đúng», sao lưu bảng,
  trần 500 dòng, cấm `DROP/TRUNCATE/ALTER/CREATE/GRANT`, cấm bảng tài khoản / phân quyền / cấu hình / sổ của bot.
- **Chặn địa chỉ nội bộ khi tải link** (`web_search.py`): chỉ `http/https`; chặn `localhost`, `.local`, `.internal`; phân
  giải tên rồi chặn IP private / loopback / link-local / reserved / multicast; kiểm lại **ở mỗi bước chuyển hướng**
  (ai-CR-133/134).
- Nội dung tệp / trang web / ảnh là **dữ liệu, không phải lệnh** (`TOOL_GUIDE`); số liệu trong ảnh phải tra lại bằng công cụ.
- Khóa AI, token Google mã hóa Fernet (khóa suy từ `JWT_SECRET` — vì vậy `.env.agent` phải trùng `JWT_SECRET` với ERP);
  khóa MCP chỉ giữ băm SHA-256, hạn 90 ngày; mã liên kết chat chỉ giữ băm.
- Kết quả lệnh VPS đi qua `guardrails.mask_secrets` trước khi lên Telegram / vào sổ.

---

## 3. Bot tự sửa phần mềm

### 3.1 Vòng đời một việc AI-xxxx

Trạng thái lưu `tab_agent_task.status` (SMALLINT, `agent_hub/constants.py`):

| Số | Hằng | Nghĩa | Ai đưa vào | Đi tiếp khi |
|---|---|---|---|---|
| 1 | `ST_INBOX` | Tin «việc» nằm hàng đợi (`tab_agent_message.task_id = 0`) | Poller sau phân loại `viec`, phiếu hỗ trợ ERP (`agent.pull_tickets`), sự cố lặp (`SRC_INCIDENT=3`), thiếu chức năng (`SRC_GAP=4`) | Lặng `AGENT_TRIAGE_DELAY_SEC` (10 giây) → `agent.triage_inbox` gom |
| 2 | `ST_TRIAGE` | Đã gom + tóm tắt (lượt Gemini/khóa người chat) | Worker | Chạy liền sang rà soát (ai-CR-005, 017) |
| 13 | `ST_SCANNING` | Claude Code **chỉ đọc** rà mã thật trên `erp-v2` mới nhất (+ so `origin/main`), lượt `STAGE_SCAN = 25` | Worker giao `agent.scan_task` cho máy sửa mã | Máy lập kế hoạch ngay (`manager.run_plan(review=…)`); rà hỏng / máy tắt / quá 45 phút → lập kế hoạch theo tài liệu |
| 3 | `ST_PLAN` | Có kế hoạch + `plan_files` | Máy / worker | Rủi ro ≤ 2 và không còn câu hỏi → **tự duyệt** («em làm luôn», ai-CR-086); rủi ro 3 → thẻ kế hoạch chờ «duyệt» |
| 11 | `ST_NEEDS_INPUT` | Đang hỏi lại đại ca | Kế hoạch có câu hỏi; bot đi lạc / đụng tệp cấm / không sửa được tệp nào; sau «Thu hồi» | Đại ca trả lời (gắn vào việc, lập lại kế hoạch) |
| 4 | `ST_CODE` | Máy sửa mã đang chạy `claude -p` | `coder.approve_gate` → `dispatch` → `agent.code_task` | Cổng kiểm xong → REVIEW, hoặc NEEDS_INPUT |
| 5 | `ST_CI` | (Thiết kế: GitHub Actions) | **Không chỗ nào trong mã đặt trạng thái này**; kho cũng chưa có `.github/workflows` | — |
| 6 | `ST_REVIEW` | Có thẻ kết quả + tệp `.diff`, chờ đại ca | Máy sửa mã | «Gộp erp-v2 + deploy dev» → «Đồng ý» / «Hẹn giờ» |
| 12 | `ST_DEPLOYING` | Đang `merge --no-ff` + đẩy `erp-v2` + `deploy.sh dev` | `agent.deploy_task` trên máy có cờ deploy | Health dev 200 → PROD; hỏng trước khi đẩy → REVIEW |
| 7 | `ST_PROD` | Đã lên dev, chờ «Xong» (lên prod không có đường tự động) | Máy sửa mã | «Xong» → DONE; «Thu hồi» (`git revert -m 1` + deploy lại) → NEEDS_INPUT |
| 8 / 9 / 10 | `ST_DONE` / `ST_CANCELLED` / `ST_FAILED` | Đóng (`CLOSED_STATUSES`) | Đại ca / bot chịu thua | Tin gắn vào được thả cho lượt gom sau |

**Làn:** `LANE_QUICK` (việc nhỏ rõ, ≤ `QUICK_MAX_FILES = 3` tệp, rủi ro 1) bỏ rà soát riêng, kế hoạch gọn rồi sửa luôn;
«làm kỹ» ép làn đầy đủ, «làm luôn» ép làn tắt. Model của `claude -p` theo làn: `AGENT_CODER_MODEL_QUICK` /
`AGENT_CODER_MODEL` trong `.env.runner`.

**Chỗ dừng bắt buộc chờ đại ca (hiện nay, theo mã + doc 09):**

1. Kế hoạch rủi ro **cao** (tiền, công nợ, phân quyền, cấu trúc DB, `main`) → «duyệt».
2. **Gộp vào `erp-v2` + deploy dev** → «Đồng ý» trên thẻ, từ đúng chat chủ bot hoặc người được cấp cấp «gộp dev».
3. **Prod**: không có đường nào từ việc sửa mã lên prod; lệnh «deploy prod <commit>» là thao tác VPS riêng, phải «đúng»
   (OTP tạm bỏ theo lệnh đại ca).
4. Việc có migration: thẻ kết quả có mục «CÓ ĐỔI CẤU TRÚC DB», «gộp» là duyệt; sao lưu cả DB dev trước deploy.

Không có đường nào tự đi tiếp sau khi hết giờ: hết giờ thì việc đứng im, Telegram nhận một dòng báo. Vòng nhặt việc kẹt
(`resume_stuck_plans`, heartbeat) chỉ **làm lại bước dở**, không vượt qua chỗ dừng.

### 3.2 Máy sửa mã (runner)

| Phần | Cách làm |
|---|---|
| Hai container | `tunnel` (`ssh -L` mở 127.0.0.1:3306 → MySQL dev, 127.0.0.1:6379 → Redis dịch vụ AI; đứt thì 5 giây nối lại) và `agent-runner` dùng chung mạng (`network_mode: service:tunnel`) |
| Nhận vé | Celery `-c 1`, hàng đợi riêng `agent_code.<AGENT_RUNNER_NAME>` (`start.runner.sh`). Vé nằm trong Redis tới khi máy nối vào — máy tắt thì việc chờ, không mất |
| Đường vé từ 08/10 | Bot xếp vé vào `redis-agent` → `redis-agent-forward` giữ 127.0.0.1:16379 trên VPS → đường hầm của máy (ai-CR-124). Trước đó cổng này trỏ Redis ERP và vé không bao giờ tới máy |
| Chia việc | Việc mới → máy đang bật ít việc nhất; không máy nào bật → `AGENT_DEFAULT_RUNNER`. Việc đã bắt đầu **dính máy** (`AgentTask.runner_id`) vì worktree + phiên Claude chỉ có ở đó. Nhịp tim 30 giây |
| Kho mã | Clone từ GitHub vào volume `agent_runner_worktrees`; mỗi việc một `git worktree add -B bot/<mã>-<slug>` từ `origin/erp-v2` mới nhất (`coder.fetch_base`) |
| Chạy Claude | `claude -p --output-format json --permission-mode acceptEdits --allowedTools "<hẹp>" --session-id <mới> --max-turns 80`, đề bài qua stdin. Không cho `git commit/push`, `docker`, `pip`, `npm`, `ssh`. Môi trường con dựng sạch; `CLAUDE_CODE_OAUTH_TOKEN` chỉ đưa vào `claude`. Phiên cất ở `/worktrees/.claude` để «Hỏi thêm về bản vá» (`--resume`, chỉ đọc) sống qua dựng lại |
| Chống đi lạc | Sau sửa: đụng tệp cấm (`guardrails.BANNED_PATTERNS`) · quá 25 tệp · quá 30 % tệp ngoài `plan_files` (bài kiểm và `.md` không tính) · không sửa gì → `git reset`, không commit, NEEDS_INPUT |
| Cổng kiểm | `python -m pytest` đúng tệp test backend vừa đụng; đụng `frontend-v2/` thì `tsc --noEmit` cả cây + `eslint` tệp vừa đụng + `vitest run` đúng thư mục vừa đụng (thư viện cài một lần theo băm lockfile). `frontend/` (v1) chưa có cổng. Không chạy được = «chưa kiểm», không tính xanh. Có migration: phải dịch được và kho chỉ còn một đầu |
| Đẩy / PR | Commit do runner làm sau cổng kiểm; đẩy `bot/*` bằng `--force`. PR vào `erp-v2` chỉ khi bấm «Gửi link PR để anh tự merge» (`AGENT_PR_ENABLED` giữ tắt) |
| Gộp + deploy dev | `coder.merge_and_deploy`: worktree `agent-merge` từ `origin/erp-v2` → `merge --no-ff` (xung đột thì abort, về REVIEW) → kiểm lại một đầu migration → đẩy **không** `--force` → ghi `merge_sha` ngay → `deploy.sh dev <commit>` qua SSH → chờ health. Hẹn giờ là dòng `AgentRun` + beat `agent.deploy_due` mỗi phút |
| Thu hồi | `coder.revert_and_deploy`: `git revert --no-edit -m 1 <bản gộp>` → đẩy → deploy dev lại (`STAGE_REVERT = 23`) |
| Tự cập nhật | `runner_update.py`: bot ghi vân tay mã (`bot_fp`) vào `tab_agent_cursor`; máy rảnh mà lệch thì kéo nhánh nền, tìm commit có `backend/` băm đúng vân tay, ghi `current` rồi tự tắt; `start.runner.sh` chạy mã ở `/worktrees/.runner-code/<sha>/backend` (lỗi nạp thì quay về mã trong ảnh). Chỉ dựng lại ảnh khi đổi `Dockerfile.runner` |
| Thao tác VPS | Máy có cờ deploy còn nhận vé `agent.run_op` / `agent.diagnose_incident` / `agent.resource_report` (`ops_runner.py`): chạy lệnh, `mysqldump` bảng trước khi sửa, hoàn tác, chẩn đoán, tự chữa dev |
| Không có trên máy | Token Telegram, khóa Gemini, khóa SSH prod. Tin Telegram đi vòng qua worker của bot |

### 3.3 Bậc tự chủ 1–4

Bốn bậc ở doc 01 §10 là **mức bot được tự làm tới đâu**, không phải các phase của lộ trình (phase 0–11, S ở doc 13).
Một phase có thể thêm tính năng mà không đổi bậc.

| Bậc | Bot được làm | Tình trạng |
|---|---|---|
| 1 | Gom việc, lập kế hoạch, nhắn Telegram, ghi sổ. Không đụng mã | Xong 18/09 |
| 2 | Sửa mã trong worktree, kiểm, đẩy nhánh `bot/*`, mở PR; **gộp `erp-v2` + deploy dev chỉ khi đại ca «Đồng ý»** | **Đang ở đây** (GĐ1, 2a, 2b, 3 xong 22–23/09) |
| 3 | Tự gộp `erp-v2` khi CI xanh + tự lên dev | Chưa — kho chưa có CI; tự duyệt kế hoạch rủi ro thấp/vừa (ai-CR-086) là nới ở **bước kế hoạch**, không phải bậc 3 |
| 4 | Cổng prod: đại ca ra lệnh → môi trường GitHub có người duyệt → sao lưu DB → phát hành | Chưa. Lệnh «deploy prod» qua thao tác VPS có «đúng» là đường vận hành, không gắn với việc sửa mã |

### 3.4 Rủi ro và rào chắn chính

| Rủi ro | Mức | Rào chắn |
|---|---|---|
| Bot chạy cạnh chìa khóa (máy đại ca) | Cao | Container kín, chỉ mount volume worktree, không Docker socket, không mount home; tiến trình con hạ quyền `runner` |
| Bot đi lạc, sửa tùm lum | Cao | `plan_files` + trần 25 tệp + ngưỡng 30 % + danh sách tệp cấm, dừng không commit |
| Bài kiểm do chính bot viết | Cao | Bắt buộc có bài canh chiều ngược; đại ca đọc diff trên thẻ; chưa có CI máy sạch |
| Bot tự sửa luật của chính nó | Cao | `grants.py`, `runners.py`, `ops.py`, `ops_runner.py`, `policy.py`, `guardrails.py`, `scripts/deploy/*`, sổ quyết định đều là tệp cấm |
| Migration làm hỏng DB | Cao | Được viết nhưng: một đầu duy nhất, thẻ liệt kê thay đổi mất dữ liệu, sao lưu cả DB dev trước deploy |
| Runner ra Internet tự do (chưa chặn egress) | Vừa | Worktree không có bí mật; `--allowedTools` không có `curl`/`wget`/Bash tự do. Chưa có proxy allowlist |
| `CLAUDE_CODE_OAUTH_TOKEN`, PAT GitHub, khóa SSH VPS trên máy | Vừa | Không khai trong `Settings`; chỉ đưa đúng tiến trình cần; khóa SSH chép tạm 0600 rồi xóa; không lên dòng lệnh |
| PAT ghi được mọi nhánh | Vừa | Mã chỉ đẩy `bot/*` và `erp-v2` (sau «Đồng ý»), không bao giờ `main`. Branch protection chưa bật (K-03 chờ đại ca) |
| Đốt hết hạn mức gói Claude | Vừa | Một việc một lúc (`-c 1`), `AGENT_DAILY_TASK_CAP = 5`, chỉ kiểm phần vừa sửa |
| Máy sửa mã tắt | Thấp | Vé chờ trong Redis; bot báo đang chờ máy nào |

---

## 4. Triển khai và vận hành

**Các stack Docker:**

| Stack | Tệp compose | Ở đâu | Service |
|---|---|---|---|
| ERP dev | `docker-compose.dev.yml` + `.env.dev`, thư mục `~/procurement-tool-dev` | VPS | `api`, `celery-worker`, `celery-beat` (ba image **riêng**), `erp`, `web`, `help`… |
| ERP prod | `docker-compose.production.yml`, `~/procurement-tool` | VPS | Như trên, `embedded`, **không bật bot** |
| Dịch vụ AI | `docker-compose.agent-hub.yml` + `.env.agent`, `-p agent-hub`, thư mục `~/agent-hub` (doc 14) | VPS, cùng máy với ERP | `agent-api`, `agent-worker`, `agent-beat`, `agent-poller` (**một image chung** `dego-agent-hub`), `zalo-listener`, `redis-agent`, `qdrant-agent`, `redis-agent-forward` |
| Máy sửa mã | `docker-compose.runner.yml` + `.env.runner`, `-p agentrunner` | Máy đại ca | `tunnel`, `agent-runner` |
| Local cũ | `docker-compose.agent.yml` | Máy đại ca | Bộ bot nhúng của bậc 1–2 (chưa kiểm còn dùng hay không) |

**Lệnh dựng dev:**

```bash
# ERP dev (trên VPS)
cd ~/procurement-tool-dev && docker compose --env-file .env.dev -f docker-compose.dev.yml up -d --build api celery-worker celery-beat erp
# Dịch vụ AI (trên VPS) — agent-api tự chạy alembic -c alembic_agent.ini upgrade head (start.agent.sh)
cd ~/agent-hub && git pull && docker compose --env-file .env.agent -p agent-hub -f docker-compose.agent-hub.yml up -d --build
curl -s 127.0.0.1:8020/api/health        # {"success": true, "service": "agent-hub", "mode": "service"}
# Máy sửa mã (máy đại ca)
docker compose --env-file .env.runner -p agentrunner -f docker-compose.runner.yml up -d --build
```

Hoặc qua `backend/scripts/deploy/deploy.sh` (gửi bằng `ssh vps 'bash -s -- <đích> <commit|latest> [service…]' < deploy.sh`):
đích `dev` / `prod` / `agent`; khóa lượt bằng `flock`; commit phải nằm trên `origin/<nhánh của đích>` (dev, agent =
`erp-v2`; prod = `main`); `reset --hard`; `up -d --build` đúng service (bỏ trống = tự chọn theo thư mục đổi); gõ health
2 phút, hỏng thì **tự quay về `PREV`**; ghi nhật ký `~/agent-deploy-logs`.

**Thứ tự khi đợt sửa có đường mới ở cổng B** (vd `settings/raw` ai-CR-128, quyền `agent_group` ai-CR-123, `agent_ops`
ai-CR-132): dựng **ERP api trước** (có đường mới, khóa quyền mới, migration ERP), rồi `erp` nếu có giao diện, **sau cùng**
mới dựng stack agent-hub. Làm ngược thì dịch vụ AI gọi vào đường chưa có → 404.

**Trước khi dựng lại agent-hub, kiểm việc đang chạy dở** (DB `agent_hub`) — dựng lại giữa chừng từng làm đứt lượt lập lại
kế hoạch (ai-CR-127):

```sql
SELECT code, status FROM tab_agent_task WHERE status IN (2, 4, 12, 13);  -- TRIAGE, CODE, DEPLOYING, SCANNING
SELECT id, task_id, stage FROM tab_agent_run WHERE status = 1;           -- lượt đang chạy
```

Có dòng thì chờ xong hoặc báo đại ca. Lưu ý thêm: `agent-worker` có `stop_grace_period: 120s` cho lượt chép lời họp dài.

**Công tắc vận hành:** `AGENT_OPS_ENABLED` (thao tác VPS qua bot) và `AGENT_HEAL_ENABLED` (tự chữa dev) phải bật ở **cả**
`.env` của bot và `.env.runner` của máy có cờ deploy. Health hỏng `AGENT_HEALTH_FAIL_STREAK = 3` lượt liền → mở sự cố,
máy chẩn đoán; dev tự chữa tối đa `AGENT_HEAL_MAX_PER_HOUR = 3` lần/giờ bằng một trong `restart_services`, `up_services`,
`rollback_last_deploy`, `prune_build_cache`; prod chỉ đề xuất, chờ «đúng». Thêm bảng bot mới mà máy sửa mã đọc/ghi thì
phải `GRANT` thêm cho `agent_runner` cùng đợt (thiếu là máy nhận vé rồi hỏng lặng).

**Prod:** phần bot / dịch vụ AI chưa lên prod; prod đang giữ theo chốt 19/09 (doc 13 §5 «Prod»). Đưa lên prod sẽ đi theo
stack đã tách (S-1), chưa có runbook riêng cho prod (doc 14 chỉ viết cho dev; tên mạng `erp-internal` phải đổi).

---

## 5. Bản đồ tệp mã — muốn sửa X thì mở tệp nào

| Muốn sửa | Mở |
|---|---|
| Rẽ nhánh một tin nhắn, câu lệnh nhận ra ngay, mạch chờ, thẻ Telegram | `backend/app/modules/agent_hub/service.py` (`handle_message`, `_route_plain_text`, `answer_question`) |
| Lời nhắc phân loại ý định / gom việc / lập kế hoạch / đề xuất ghi sổ | `agent_hub/manager.py` |
| Luật «làm luôn / hỏi một lần / không làm» | `agent_hub/policy.py` + `doc/agent-hub/09-quy-dinh-hoi-va-lam.md` (bot code không được sửa) |
| Trạng thái, nhãn bước, dấu tin, đơn giá model, tên bot | `agent_hub/constants.py` |
| Bảng của bot | `agent_hub/model.py`; danh sách bảng thuộc dịch vụ AI: `core/agent_tables.py`; migration: `backend/migrations_agent/` |
| Gửi / nhận Telegram, đổi Markdown | `agent_hub/telegram.py`, `poller.py`; Zalo: `zalo.py`, `zalo_account.py`, `zalo-listener/index.mjs`; lớp kênh: `channels.py` |
| Đăng nhập chat, quyền dùng bot | `agent_hub/chat_link.py`, `service.py` (`BOT_USE_PERMISSION`) |
| Khóa AI, chuỗi dự phòng | `agent_hub/ai_keys.py`, `user_keys.py`; adapter: `assistant/provider/*.py` |
| Lời nhắc chung Trợ lý, routing loại câu | `assistant/service.py` (`ROUTING`, `TOOL_GUIDE`); gói tri thức: `assistant/packs/`; lịch sử web: `assistant/conversation.py`; trần ngày web: `assistant/usage.py` |
| Thêm / sửa công cụ | `assistant/tools/<nhóm>_tool.py` + đăng ký ở `tools/__init__.py`; khung gác quyền: `tools/base.py`; nhóm chạy ở dịch vụ AI: `erp.LOCAL_TOOL_MODULES` |
| Tạo phiếu thật từ nháp (bot, MCP) | `agent_hub/draft_create.py` |
| Cổng B (ERP mở cho dịch vụ AI) | `agent_gateway/controller.py`; phía gọi: `agent_hub/erp.py` (`_Local` / `_Remote`) |
| Chuyển tiếp web → dịch vụ AI | `agent_gateway/proxy.py`; ứng dụng dịch vụ AI: `app/agent_main.py`; danh tính: `core/agent_identity.py`; chữ ký: `core/agent_signature.py` |
| Sổ nhớ, tóm tắt buổi, thẻ cá nhân | `agent_hub/personal_memory.py`, `sessions.py`, `personal_items.py` |
| Thuật ngữ, vòng tự học, thiếu chức năng | `assistant/glossary.py`, `agent_hub/learning.py`, `assistant/feedback.py` |
| Nhóm chat, đọc tệp | `agent_hub/groups.py`, `doc_text.py`; màn ERP v2: `frontend-v2/src/modules/assistant/pages/chat-group-*.tsx`, `bot-user-list-page.tsx` |
| Tra mạng, đọc link, chặn địa chỉ nội bộ | `agent_hub/web_search.py`, `research.py` |
| Biên bản họp | `agent_hub/meetings.py`, `meeting_actions.py`, `meeting_drive.py`, `dego_docx.py` |
| Chuông, nhắc, bản tin sáng, Google | `agent_hub/bells.py`, `reminders.py`, `briefs.py`, `google_link.py` |
| Cổng MCP | `agent_hub/mcp.py`, `mcp_keys.py` |
| Việc nền + lịch beat + định tuyến hàng `agent_code` | `agent_hub/tasks.py`, `core/celery_app.py` |
| Đề bài Claude, cổng kiểm, đẩy, gộp, thu hồi | `agent_hub/coder.py` (`build_brief`, `approve_gate`, `check_drift`, `merge_and_deploy`, `revert_and_deploy`); migration: `schema_change.py` |
| Tệp cấm, phân loại lệnh / SQL, che bí mật | `agent_hub/guardrails.py` (bot code không được sửa) |
| Sổ máy, chia việc, tự cập nhật máy | `agent_hub/runners.py`, `runner_update.py`, `backend/start.runner.sh`, `docker/Dockerfile.runner`, `docker/Dockerfile.tunnel` |
| Ai được ra lệnh sửa mã | `agent_hub/grants.py` |
| Sổ quyết định, kho tài liệu của bot | `agent_hub/playbook.py` + `doc/agent-hub/03-so-quyet-dinh.md`; `agent_hub/memory.py` |
| Thao tác VPS, sự cố, tự chữa | `agent_hub/ops.py` (phía bot), `ops_runner.py` (phía máy), `backend/scripts/deploy/deploy.sh` |
| Màn «Việc của bot» | `agent_hub/controller.py` |
| Compose, khởi động | `docker-compose.agent-hub.yml`, `docker-compose.runner.yml`, `backend/start.agent.sh`, `backend/alembic_agent.ini`, `backend/scripts/agent_split/` |

---

## 6. Tài liệu chi tiết

| Tệp | Tra gì |
|---|---|
| `doc/agent-hub/01-thiet-ke-ky-thuat.md` | Thiết kế gốc: bảy trạm, mô hình dữ liệu, đề bài Claude, luật nhánh, cấu hình `.env`, bậc 1–4, bảng rủi ro §11 |
| `doc/agent-hub/02-bo-quy-tac-bot.md` | Bộ quy tắc A–G: ba luật trùm, luật bot quản lý, luật bot code C1–C10, khi nào leo thang, danh sách cấm cứng |
| `doc/agent-hub/03-so-quyet-dinh.md` | Sổ quyết định đại ca (QĐ-xx) bot tra trước khi hỏi |
| `doc/agent-hub/04-danh-sach-tinh-nang.md` | Mã tính năng chi tiết (A, N, P, M, K, D, V, O, L, T, R, C) |
| `doc/agent-hub/05-may-sua-ma.md` | Cài và đăng ký máy sửa mã, tài khoản MySQL `agent_runner`, `authorized_keys` |
| `doc/agent-hub/06-cong-mcp.md` | Cổng MCP: khóa, hai mức, `confirm_draft`, `report_issue` |
| `doc/agent-hub/07-quy-trinh-va-so-do.md` | Sơ đồ tổ chức, vai trò, các luồng (mermaid) |
| `doc/agent-hub/08-van-hanh-vps.md` | Sổ môi trường, câu lệnh VPS, lan can, sao lưu / hoàn tác, `deploy.sh`, tự vận hành |
| `doc/agent-hub/09-quy-dinh-hoi-va-lam.md` | Bảng «làm luôn / hỏi / không làm», sửa dữ liệu bằng lời |
| `doc/agent-hub/10` … `12` | Nối Google; biên bản họp; tóm tắt nhóm Telegram / Zalo |
| `doc/agent-hub/13-lo-trinh.md` | Lộ trình theo phase, bộ 44 chức năng, kiến trúc đích A2A bốn nút, phase S |
| `doc/agent-hub/14-cong-erp-api.md` | Hợp đồng cổng B, `AGENT_MODE`, runbook dựng dịch vụ AI trên dev, Zalo B, màn Nhóm chat, ai-CR-124 |
| `doc/agent-hub/15-ke-hoach-tong-bot-erp.md` | Kế hoạch tổng 09/10: đã làm gì, làm tiếp phase nào, định hướng về sau |
| `doc/tai-lieu-ky-thuat/change-log-ai.md` | Sổ `ai-CR-*`: ai yêu cầu gì, làm gì, tệp nào, trạng thái dev / prod |
