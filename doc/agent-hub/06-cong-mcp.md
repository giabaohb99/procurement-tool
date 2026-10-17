# AGENT HUB — CỔNG MCP: dùng AI của bạn với dữ liệu ERP

**Bản 2.0 · 17/10/2026** — gộp ai-CR-063 (bản 1.0, 25/09) và đợt ai-CR-207 … 216 (doc/erp/21 Kho skill AI qua MCP, đại ca
chốt 17/10: MCP là đường chính, người dùng tự trả tiền gói AI của họ). Một chỗ đọc đủ: người dùng làm gì, cổng mở gì, gác
gì, và hợp đồng API cho giao diện (§7). Lịch sử từng thay đổi nằm ở `doc/tai-lieu-ky-thuat/change-log-ai.md`.

Đại ca chốt 24/09/2026: mỗi người **tự do chọn ứng dụng AI** (Claude Desktop, Claude Code, Cursor, Gemini CLI…) và gắn khóa
của mình; hệ thống chỉ cung cấp **công cụ** qua một cổng MCP. Cổng dùng **chung bộ tool** với Trợ lý AI trên web và bot
Telegram (`assistant.tools`) — không viết lại tool, không mở đường mới vào dữ liệu; mọi tool chạy **dưới danh tính chủ khóa**.

## 1. Người dùng làm gì

1. **Lấy khóa** — một trong hai đường:
   - Tự tạo: Trang cá nhân → tab **Khóa AI** → đặt tên, chọn mức, **Tạo khóa**. Khóa (`dego_mcp_…`) hiện **đúng một lần**.
   - Quản trị phát hộ (§2.2): nhận **chuông** «Bạn có khóa kết nối AI chờ nhận» → Trang cá nhân (`/me?tab=ai-key`) → **Nhận
     khóa** → khóa hiện đúng một lần. Khóa phát hộ **chưa nhận thì chưa dùng được**.
2. **Nối ứng dụng** — màn *AI của tôi* lấy đoạn cấu hình đúng từng ứng dụng ở `GET /api/agent-hub/mcp-setup?client=…`
   (§7.1). Tóm tắt:
   - **Claude Desktop**: KHÔNG nhận `url` + `headers` trong `claude_desktop_config.json` — phải đi cầu `mcp-remote` (cần
     Node.js 18+). Settings → Developer → Edit Config:
     ```json
     {"mcpServers": {"dego-erp": {"command": "npx",
       "args": ["-y", "mcp-remote", "https://deverp.degoholding.vn/api/mcp", "--header", "Authorization:${DEGO_MCP_KEY}"],
       "env": {"DEGO_MCP_KEY": "Bearer dego_mcp_…"}}}}
     ```
     Khóa để trong biến `DEGO_MCP_KEY` (khoảng trắng trong `args` làm hỏng lệnh trên Windows). Đã `setx DEGO_MCP_KEY
     "Bearer dego_mcp_…"` cho cả máy thì bỏ được khối `env`. Lưu xong **thoát hẳn** Claude Desktop (cả biểu tượng dưới khay)
     rồi mở lại — `setx` chỉ có hiệu lực với tiến trình mở sau lệnh.
   - **Claude Code**: `claude mcp add --transport http --scope user dego-erp <url> --header "Authorization: Bearer …"`.
   - **Cursor**: `~/.cursor/mcp.json` → `{"mcpServers": {"dego-erp": {"url": "<url>", "headers": {"Authorization": "Bearer …"}}}}`.
   - **Gemini CLI**: `~/.gemini/settings.json` → như Cursor nhưng khóa `httpUrl` thay `url`.
   - **claude.ai (trình duyệt), ChatGPT**: kết nối tùy chỉnh chỉ đăng nhập OAuth, chưa nhận khóa ERP — dùng ứng dụng khác.
3. **Kiểm tra** — màn báo «đã nối» khi khóa có lượt gọi thành công (`mcp-keys/{id}/last-call`).
4. **Hỏi** như hỏi Trợ lý: «quy trình mua gấp làm sao», «đơn PO00358 tới đâu», «nghỉ phép còn bao nhiêu ngày».

Khóa hết hạn sau 90 ngày (tự tạo: 1–365; phát hộ: 7 / 30 / 90 / 180 / 365), gỡ được bất cứ lúc nào, mỗi lượt gọi ghi «dùng
lần cuối». Tối đa **5 khóa còn hiệu lực** mỗi tài khoản. Nghỉ việc thì khóa đóng cùng phiên đăng nhập.

## 2. Khóa

### 2.1 Hai mức

| Mức | Thấy tool nào | Ghi chú |
|---|---|---|
| **Chỉ đọc** (mặc định, khóa phát hộ luôn là mức này) | Tool trong danh sách trắng `READ_TOOLS` (`agent_hub/mcp.py`) + 3 tool skill + `report_issue` | Không soạn nháp, không tạo / ghi gì; tool mới mặc định coi là «ghi» cho tới khi khai vào `READ_TOOLS` |
| **Được ghi** (chỉ người dùng tự tạo — Q5) | Thêm `draft_*`, `ticket_create`, lịch / sổ nhớ / ghi chú, xuất tệp, `confirm_draft` | Tạo phiếu luôn **hai bước**: nháp → người dùng xem → `confirm_draft` |

Không bao giờ mở qua MCP: `propose_*` (xác nhận bằng nút trên web / Telegram), `report_missing_feature`, `propose_glossary_term`
(`HIDDEN`); đề nghị thanh toán chỉ tạo trên web (`confirm_draft` trả link form điền sẵn). Ba tool báo cáo mua hàng cũ đã
**rời MCP** (§3.4). Ngoài mức khóa còn lớp **nhóm tool** do quản trị bật / tắt (§4) — tool phải qua cả hai lớp.

### 2.2 Phát hộ, nhận, thu hồi (ai-CR-212, 215)

- Quyền `ai_mcp_key_admin` (read · create · delete). Phạm vi đặt trên **hồ sơ nhân sự của CHỦ KHÓA** (pháp nhân + phòng ban +
  chính mình, như `employee`); bảng khóa nằm ở DB dịch vụ AI nên phạm vi hỏi ERP qua cổng B (§6). Vai trò seed: *Quản trị
  kho skill AI* = toàn công ty, *Biên tập skill AI phòng ban* = phòng mình.
- Phát cho một / nhiều người (`user_ids` hoặc `employee_ids`) hoặc cả phòng — **≤ 50 người một lượt**; có người ngoài phạm vi →
  từ chối cả lượt, không phát khóa nào; người đủ 5 khóa, nhân sự chưa có tài khoản / tài khoản đã khóa → bỏ qua kèm lý do.
- Khóa phát hộ: trạng thái **Chờ nhận**, khóa thô niêm phong Fernet (`raw_sealed`) chỉ tới khi nhận; nhận xong / thu hồi xóa
  trắng. Chưa nhận thì cổng từ chối (nhật ký ghi «Khóa phát hộ chưa được chủ khóa nhận»).
- Thu hồi một khóa, mọi khóa của một người, hoặc cả một lượt phát (`batch_id`); chủ khóa ngoài phạm vi → từ chối cả lệnh.
  Dòng thu hồi giữ lại («Đã thu hồi») để đối soát. Chỉ báo bằng **chuông ERP** — không email, không Telegram (doc 21 §7.1).

## 3. Công cụ

### 3.1 Tool riêng của cổng

- `confirm_draft(kind, draft, submit)` — tạo thật từ bản nháp `draft_*`; `submit=true` gửi duyệt luôn (thiếu trường bắt buộc
  thì không tạo gì). Chỉ khóa được ghi.
- `report_issue(title, detail, screen_url)` — báo lỗi → phiếu hỗ trợ gắn bộ phận của bot (`AGENT_TICKET_DEPARTMENTS`). Ai cũng gọi.

### 3.2 Kho skill (bao-CR-622, K2)

`list_skills(query?)` · `read_skill(name)` · `read_skill_file(name, path)` — chỉ skill **đã xuất bản** người đó được đọc
(`ai_skill.access_service.visible_skills`); bộ mức *Bảo vệ* không trả tệp, mức *Khóa* chỉ tên + tóm tắt. `INSTRUCTIONS` của
server dặn AI gọi `list_skills` trước việc nghiệp vụ, áp dụng nội dung chứ không đọc lại nguyên văn. Nhật ký ghi `skill_id`.

### 3.3 Ba tầng dữ liệu (doc 21 §5.5)

| Tầng | Tool | Gác | Ghi chú |
|---|---|---|---|
| T1 báo cáo gom sẵn (ai-CR-208) | `report_summary(report_key, filters)` — 13 báo cáo | `can_view_report` + dependency quyền vai trò của route + `apply_scope` trong route | Gọi thẳng hàm route `/summary`, số khớp màn web; nhóm trên trần 50 + `has_more` |
| T2 bảng số tổng hợp (ai-CR-210) | `dataset_query(dataset, measures, dimensions, filters)` — bộ `purchase`, `payable`, `payment_request` | `ctx.can(entity)` + `apply_scope` (purchase: `product.read` + `supplier.read` cho chiều NCC + quyền Báo cáo mua hàng) | Khai ở `assistant/datasets/catalog.py`, không sinh SQL; ≤ 4 chỉ số × 2 chiều × 500 nhóm |
| T3 đọc danh sách / chi tiết (ai-CR-211) | `erp_read(resource, id?, filters?, page?, page_size?, pages?)` — YCMH, YCBG, ĐMH, nhận hàng, NCC, sản phẩm, hợp đồng | Hàm route danh sách của màn web (require + apply_scope); chi tiết qua bộ đọc đã lọc phạm vi | Mặc định 1 trang × 50 dòng, tối đa 5 × 100 khi AI xin rõ; ngoài phạm vi = không tồn tại; chi tiết YCMH KHÔNG gọi route web (route đó ghi ngầm «phương án 0») |

### 3.4 Tool tra cứu cũ và chuẩn §5.6 (ai-CR-216)

- Rời MCP (vẫn còn ở Trợ lý web / bot): `purchase_report` → `report_summary`; `analytics_query`, `top_suppliers_by_purchase`
  → `dataset_query dataset=purchase` (`MCP_RETIRED`, gọi thì trả lỗi chỉ đường mới).
- Chuẩn §5.6 áp ở lớp cổng cho MỌI tool: đường `url` / `link` / `*_url` ở mọi tầng thành tuyệt đối (trừ đường Help Center
  `/articles`, `/faq` của `search_docs`); `total` là tổng thật mà thiếu `has_more` thì cổng gắn thêm. Từng tool đã thêm (không
  đổi trường cũ): `has_more`, nhãn trạng thái (`*_label`), `currency` (ĐMH theo nguyên tệ của đơn, hải quan USD, công nợ / YCTT
  VND), căn cứ VAT (`amount_basis` / `money_basis`). `structuredContent` có ở `report_summary`, `dataset_query`, `erp_read`.

## 4. Nhóm tool và cấu hình (G7, ai-CR-216)

Quản trị (quyền `agent_group.write`) bật / tắt **nhóm** tool qua MCP, chỉnh trần và câu dặn thêm cho AI. Mỗi tool thuộc đúng
một nhóm (`agent_hub/mcp_settings.GROUPS`; bài kiểm canh tool mới quên xếp nhóm). Nhóm tắt: tool không có trong `tools/list`,
gọi thẳng thì `denied` kèm tên nhóm. `report_issue`, `confirm_draft` luôn mở.

| Mặc định | Nhóm |
|---|---|
| **Bật** (Q4 + Agent 1 17/10) | `mine` tra cứu phiếu / việc của chính mình · `leave` nghỉ phép · `directory` danh bạ, thuật ngữ, HDSD · `reports` báo cáo gom sẵn + bảng số · `skills` Kho skill |
| **Tắt** | `purchase` thu mua (gồm `erp_read`) · `finance` công nợ và thanh toán (kéo theo bộ `payable` / `payment_request` của `dataset_query`) · `document` văn thư · `work` soạn việc / kế hoạch · `customs` tra cứu thị trường · `google` lịch / Drive · `personal` sổ nhớ, ghi chú, nhóm chat, biên bản · `ticket` tạo phiếu hỗ trợ · `research` nghiên cứu sâu (tốn phí) · `export` xuất tệp |

Cấu hình lưu MỘT dòng JSON ở `tab_setting.agent_mcp_settings` của ERP (đi qua cổng B `/settings/raw` ở chế độ tách dịch
vụ — khóa này phải có trong `erp.SETTING_RAW_KEYS`), đệm 60 giây. Trường chưa lưu theo biến môi trường (§5).

## 5. Kỹ thuật

- **Cửa**: `POST /api/mcp`, JSON-RPC 2.0, MCP `2025-06-18`: `initialize`, `notifications/*` (202), `ping`, `tools/list`,
  `tools/call`; batch được. `GET` → 405, `DELETE` → 204. Xác thực `Authorization: Bearer <khóa>`; sai / hết hạn / thu hồi /
  chưa nhận / tài khoản khóa → 401 + `WWW-Authenticate: Bearer` (câu trả ngoài chung một câu, lý do chỉ ở nhật ký).
- **Trần** (ai-CR-209, 213; chỉnh ở G7): 120 lượt / phút / khóa · 600 / phút / IP · 30 khóa sai / phút / IP → HTTP 429 + lỗi
  JSON-RPC -32000 + `Retry-After`; ngân sách dữ liệu `erp_read` 3.000 dòng / phút / khóa (đủ thì từ chối kèm lời dặn lọc hẹp).
  Đếm ở Redis (Redis hỏng thì đếm trong tiến trình). IP lấy `CF-Connecting-IP` → `X-Real-IP` → `X-Forwarded-For`.
  Đo dev 17/10: ĐMH xin 5 × 100 (103 đơn) mất 33 ms phía máy chủ, 51,6 KB (~500 byte / dòng) — nặng là cỡ dữ liệu sang AI.
- **Nhật ký** (ai-CR-209): mỗi lượt JSON-RPC một dòng `tab_agent_mcp_call` (kể cả initialize, khóa sai, quá tần suất — lượt sai
  hàng loạt chỉ ghi 10 dòng đầu mỗi phút): người, nhân sự, phòng ban, pháp nhân chụp lúc gọi, ứng dụng (`clientInfo`),
  method, tool, `skill_id`, trạng thái, lý do, thời gian, IP. Giữ 180 ngày; beat `agent-mcp-log-purge` 03:40 gom phần quá hạn vào
  `tab_agent_mcp_call_daily` rồi xóa.
- **Biến môi trường** (`core/config.py`): `AGENT_ERP_URL` (gốc đường dẫn tuyệt đối + đường kết nối hiện trên màn),
  `AGENT_MCP_RATE_PER_KEY`, `AGENT_MCP_RATE_PER_IP`, `AGENT_MCP_BAD_KEY_PER_IP`, `AGENT_MCP_ROW_BUDGET_PER_MIN`,
  `AGENT_MCP_LOG_RETENTION_DAYS`.
- **Bảng / migration** (DB dịch vụ AI; chế độ nhúng nằm chung DB ERP): `tab_agent_mcp_key` (+ `issued_by`, `claimed_at`,
  `raw_sealed`, `batch_id` — `mcpkey02` / `agent0012`), `tab_agent_mcp_call` + `tab_agent_mcp_call_daily` (`mcplog01` /
  `agent0011`). Phía ERP: entity `ai_mcp_key_admin` (78 entity), `ai_skill` (bao-CR-621).
- **Mã**: `agent_hub/mcp.py` (cổng), `mcp_keys.py` (khóa), `mcp_log.py` (nhật ký + trần), `mcp_settings.py` (nhóm + cấu hình),
  `mcp_setup.py` (đoạn cấu hình từng ứng dụng), `ai_overview.py` (Tổng quan); `agent_gateway/key_admin.py` (phía ERP của phát
  khóa hộ); `assistant/tools/{report_summary_tool,dataset_tool,erp_read_tool,route_call}.py` + `assistant/datasets/`.
- **Prod**: chưa mở (luật tạm dừng prod 19/09). Lên prod cần: migration `mcplog01` + `mcpkey02` (ERP) và `agent0011` +
  `agent0012` (DB `agent_hub`), `AGENT_ERP_URL=https://erp.degoholding.vn`, gán quyền `ai_mcp_key_admin` cho hai vai trò kho
  skill (seed prod không ghi đè — tick tay), và lưu cấu hình G7 nếu muốn khác mặc định Q4.

## 6. Cổng B mà cổng MCP dùng (chế độ tách dịch vụ, `agent_gateway/controller.py`)

| Đường | Dùng cho |
|---|---|
| `GET /api/agent-gw/me` | Chủ khóa + `department_id`, `company_id` (nhật ký chụp lúc gọi) |
| `GET /api/agent-gw/skills`, `/skills/read`, `/skills/file` | 3 tool skill (bao-CR-622) |
| `POST /api/agent-gw/key-admin/people` | Người trong phạm vi `ai_mcp_key_admin.<action>` (phát / liệt kê / thu hồi hộ) |
| `POST /api/agent-gw/key-admin/employees` | Hồ sơ nhân sự → tài khoản (`people` / `no_account` / `outside`) |
| `POST /api/agent-gw/key-admin/notify` | Chuông «có khóa chờ nhận» |
| `GET /api/agent-gw/ai-skill/stats` | Số bộ / skill đang dùng cho Tổng quan |
| `GET`/`PUT /api/agent-gw/settings/raw` | Cấu hình G7 (`agent_mcp_settings` nằm trong `SETTING_RAW_KEYS`) |

## 7. Hợp đồng API cho giao diện (proxy ERP `/api/agent-hub/*`)

Mọi đường đi qua proxy ERP `/api/agent-hub/*` (JWT web), trả phong bì `{success, message, data}`; dưới đây là `data`.
Ngày giờ ISO `YYYY-MM-DDTHH:MM:SS` giờ VN. Mã trạng thái là SỐ kèm nhãn (luật R2).

**Bộ mã**
- `CallStatus` (nhật ký lượt gọi): 1 Thành công · 2 Bị từ chối · 3 Lỗi.
- `KeyState` (khóa): 1 Chờ nhận · 2 Đang dùng · 3 Hết hạn · 4 Đã thu hồi.

### 7.1 Nhân sự — màn AI của tôi (G8)

| Đường | Vào | `data` |
|---|---|---|
| `GET mcp-setup` | — | `{endpoint, placeholder, clients: [{client, label, supported}]}` — 6 ứng dụng: `claude_desktop`, `claude_code`, `cursor`, `gemini_cli`, `claude_ai`, `chatgpt` |
| `GET mcp-setup?client=<mã>` | `client` | `{client, label, supported, format: "json"\|"shell"\|"", snippet, steps: [str], files?: {windows?, macos?, all?}, requires?: [str], note?, endpoint, placeholder}` — `snippet` chứa `placeholder` (`<KHÓA_CỦA_BẠN>`), màn thay bằng khóa vừa hiện. `supported=false` (claude.ai, ChatGPT) thì `snippet` rỗng, `note` nói lý do. Mã lạ → 404 |
| `GET mcp-keys` | — | `{endpoint, items: [Key]}` |
| `POST mcp-keys` | `{name, scope: 0\|1, days}` | `Key + {key}` (khóa thô, chỉ một lần) |
| `DELETE mcp-keys/{id}` | — | `null` |
| `GET mcp-keys/pending` | — | `{items: [Key]}` — khóa quản trị phát hộ đang chờ nhận |
| `POST mcp-keys/{id}/claim` | — | `Key + {key}` — khóa thô ĐÚNG một lần; lần hai / không phải của mình / thu hồi / hết hạn → 404 |
| `GET mcp-keys/{id}/last-call` | — | `{key_id, connected: bool, last_call: Call?, last_ok_call: Call?}` — `connected` = đã có ít nhất một lượt thành công; khóa không phải của mình → 404 |
| `GET mcp-calls` | `date_from, date_to, key_id, tool, status, page, size≤200` | `{total, page, size, has_more, items: [CallRow], statuses: [{value, label}]}` — người thường chỉ của mình |
| `GET mcp-calls/daily?days=14` | `days≤90` | `{days, items: [{day, total, ok, denied, error}]}` — đủ từng ngày |

`Key` = `{id, name, hint: "…abcd", scope, scope_label, expires_at, last_used_at, created_at, state, state_label, issued_by,
claimed_at, batch_id, user_id}`.
`Call` = `{created_at, client_name, method, tool, status, status_label, deny_reason}`.
`CallRow` = `{id, created_at, key_id, user_id, user_label, employee_id, department_id, company_id, client_name, method, tool,
skill_id, status, status_label, deny_reason, duration_ms, ip}`.

### 7.2 Quản trị — Tổng quan (G1), Nhật ký (G6), Khóa nhân sự (G5)

| Đường | Quyền | Vào | `data` |
|---|---|---|---|
| `GET ai-overview` | `agent_group.read` | — | `{generated_at, skills: {skill_sets, skills}\|null, connected_users, connected_days: 30, calls_7d, calls_prev_7d, calls_change_pct\|null, denied_7d, error_7d, daily: [{day,total,ok,denied,error}×14], top_tools: [{key, calls}], top_users: [{key, calls, label}], top_skills: [{skill_id, calls}], keys_by_state: [{state, label, count}], expiring_keys: [{key_id, user_id, owner_label, name, expires_at, state}], expiring_days: 7}` — `skills = null` khi ERP không trả lời |
| `GET mcp-calls` | xem người khác: `agent_group.read` | + `user_id` | như §7.1; không quyền mà hỏi người khác → 403 |
| `GET mcp-calls/top?by=tool\|user&days=14&limit=10` | như trên | | `{by, days, items: [{key, calls, label?}]}` |
| `GET mcp-key-admin/meta` | — | — | `{days: [7,30,90,180,365], batch_max: 50, max_keys: 5, states: [{value, label}], can_read, can_create, can_delete}` |
| `GET mcp-key-admin/keys` | `ai_mcp_key_admin.read` | `department_id, state, user_id, batch_id, page, size≤200` | `{total, page, size, has_more, items: [Key + {owner_label, department_id, department, issued_by_label}]}` — chỉ khóa của người trong phạm vi |
| `POST mcp-key-admin/issue` | `ai_mcp_key_admin.create` | `{user_ids: [int] \| employee_ids: [int] \| department_id, days ∈ days, name}` — có `employee_ids` thì bỏ qua `department_id` | `{batch_id, issued: [{user_id, employee_id, label, key_id}], skipped: [{user_id, employee_id, label, reason}]}` — chỉ mức chỉ đọc; có người / nhân sự ngoài phạm vi (hoặc id nhân sự không có thật) → 403 cả lượt; tổng > 50 người → 400; người đủ 5 khóa → `skipped`; nhân sự chưa có tài khoản / tài khoản đã khóa → `skipped` với `user_id = 0` |
| `POST mcp-key-admin/revoke` | `ai_mcp_key_admin.delete` | `{key_ids: [int]} \| {user_id} \| {batch_id}` | `{revoked: n}` — chủ khóa ngoài phạm vi → 403 cả lệnh |

### 7.3 Cấu hình cổng (G7)

| Đường | Quyền | Vào | `data` |
|---|---|---|---|
| `GET mcp-settings` | `agent_group.read` | — | `{groups: [{key, label, enabled, default, tools: [str]}], limits: [{key, label, value, default, min, max}], extra_instructions, extra_max_len: 1000, can_write}` |
| `PUT mcp-settings` | `agent_group.write` | một phần hay toàn bộ: `{groups?: {key: bool}, rate_per_key?, rate_per_ip?, bad_key_per_ip?, row_budget_per_min?, log_retention_days?, extra_instructions?}` | như GET (không có `can_write`); sai kiểu / ngoài dải → 400, không lưu gì; lưu một phần giữ phần cũ |

Dải: `rate_per_key` 10–2000 · `rate_per_ip` 0–20000 · `bad_key_per_ip` 5–1000 · `row_budget_per_min` 0–100000 (0 = không
chặn) · `log_retention_days` 30–730. Mã nhóm ở §4.

### 7.4 Khung demo theo chương (K8, ai-CR-214 — giao diện, không phải API)

`frontend-v2/src/shared/ui/chapter-demo/`: `<ChapterDemo chapters={AI_SKILL_INTRO_CHAPTERS} />` (kịch bản 9 chương ở
`scripts/ai-skill-intro.tsx`); chưa đăng ký route — gắn vào trang giới thiệu Kho skill khi K5 xong.

## 8. Rủi ro đã chấp nhận

Dữ liệu ERP đi sang nhà cung cấp AI do từng người chọn (đại ca chốt 24/09). Giảm rủi ro bằng: khóa theo người và theo quyền của
người đó, mức chỉ đọc mặc định, nhóm tool mặc định hẹp (Q4), hết hạn, trần tần suất + ngân sách dữ liệu, nhật ký từng lượt gọi,
thu hồi tức thì, không mở tool đổi dữ liệu nhạy cảm. Nói thật trên màn: ai cầm khóa hợp lệ thì đọc được thứ khóa đó trả về;
nhật ký cho biết ai đã đọc gì — không hứa chống sao chép.
