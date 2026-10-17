# AGENT HUB — CỔNG MCP: dùng AI của bạn với dữ liệu ERP

**Bản 1.0 · 25/09/2026 · ai-CR-063 (M-01 · M-02 · M-03 · M-04 · M-05 của [`04`](./04-danh-sach-tinh-nang.md), phase 4).**

Đại ca chốt 24/09/2026: mỗi người **tự do chọn ứng dụng AI** (Claude Desktop, Cursor, ChatGPT, …) và tự
gắn khóa của mình; hệ thống chỉ cung cấp **công cụ** qua một cổng MCP nằm trong backend ERP. Cổng dùng
**chung bộ tool** với Trợ lý AI trên web và bot Telegram — không viết lại tool, không mở đường mới vào dữ liệu.

## 1. Người dùng làm gì

1. ERP → Trang cá nhân → tab **Khóa AI** → khối **Kết nối MCP** → đặt tên, chọn mức, **Tạo khóa MCP**.
2. Khóa hiện **đúng một lần** (`dego_mcp_…`), kèm đoạn cấu hình sẵn. Dán vào ứng dụng:
   - **Claude Desktop** (đính chính 17/10, ai-CR-213): Claude Desktop KHÔNG nhận `url` + `headers` trong
     `claude_desktop_config.json` — phải đi cầu `mcp-remote` (cần Node.js 18+). Settings → Developer → Edit Config:
     ```json
     {"mcpServers": {"dego-erp": {"command": "npx",
       "args": ["-y", "mcp-remote", "https://deverp.degoholding.vn/api/mcp", "--header", "Authorization:${DEGO_MCP_KEY}"],
       "env": {"DEGO_MCP_KEY": "Bearer dego_mcp_…"}}}}
     ```
     Khóa để trong biến `DEGO_MCP_KEY` (khoảng trắng trong `args` làm hỏng lệnh trên Windows). Đã `setx DEGO_MCP_KEY
     "Bearer dego_mcp_…"` cho cả máy thì bỏ được khối `env`. Lưu xong thoát hẳn Claude Desktop rồi mở lại.
   - **Claude Code**: `claude mcp add --transport http --scope user dego-erp <url> --header "Authorization: Bearer …"`.
   - **Cursor**: `~/.cursor/mcp.json` → `{"mcpServers": {"dego-erp": {"url": "<url>", "headers": {"Authorization": "Bearer …"}}}}`.
   - **Gemini CLI**: `~/.gemini/settings.json` → như Cursor nhưng khóa `httpUrl` thay `url`.
   - claude.ai (trình duyệt) và ChatGPT: kết nối tùy chỉnh chỉ đăng nhập OAuth, chưa nhận khóa ERP.
   - Đoạn cấu hình đúng cho từng ứng dụng lấy ở `GET /api/agent-hub/mcp-setup?client=…` (§6.1) — màn AI của tôi dùng đường này.
3. Hỏi ứng dụng như hỏi Trợ lý: «3 đơn mua hàng gần nhất», «giá atrazine 6 tháng qua», «soạn đơn nghỉ phép thứ 6».

Khóa hết hạn sau 90 ngày (tối đa 365), gỡ được bất cứ lúc nào, mỗi lượt gọi ghi «dùng lần cuối». Tối đa 5 khóa
mỗi tài khoản. Nghỉ việc thì khóa đóng cùng phiên đăng nhập.

## 2. Hai mức khóa

| Mức | Thấy tool nào | Ghi chú |
|---|---|---|
| **Chỉ đọc** (mặc định) | Mọi tool tra cứu (sản phẩm, NCC, hợp đồng, đơn hàng, công nợ, văn bản, việc chờ duyệt, hải quan…) + `report_issue` | Không soạn nháp, không tạo phiếu |
| **Được ghi** | Thêm `draft_*` (soạn nháp YCBG / YCMH / nghỉ phép / đề nghị thanh toán), `ticket_create`, xuất báo cáo, và `confirm_draft` | Tạo phiếu luôn **hai bước**: nháp → người dùng xem → `confirm_draft` |

Không mở qua MCP: `propose_document_update`, `propose_account_setup` (xác nhận bằng nút trên web/Telegram),
và đề nghị thanh toán (chỉ tạo trên web, `confirm_draft` trả link form điền sẵn).

Mọi tool chạy **dưới danh tính chủ khóa**: hai lớp quyền (`can` + `apply_scope`) và audit của tool giữ nguyên
như Trợ lý web. Khóa chỉ là cách xác thực, không phải cách mở rộng quyền.

## 3. Hai tool riêng của cổng

- `confirm_draft(kind, draft, submit)` — tạo thật từ bản nháp do `draft_*` trả về; `submit=true` gửi duyệt luôn
  (luật bắt buộc khi gửi duyệt được kiểm như bot Telegram: thiếu thì không tạo gì). Dùng lại `agent_hub/draft_create`.
- `report_issue(title, detail, screen_url)` — báo lỗi → phiếu hỗ trợ gắn bộ phận của bot (`AGENT_TICKET_DEPARTMENTS`)
  → vòng nhặt phiếu của Đậu Đậu / Lạc Lạc nhận việc (ai-CR-037). Ai cũng gọi được (M-05).

## 4. Kỹ thuật

- Cửa: `POST /api/mcp`, JSON-RPC 2.0, giao thức MCP `2025-06-18`. Hỗ trợ `initialize`, `notifications/*` (202),
  `ping`, `tools/list`, `tools/call`; mảng yêu cầu (batch) được. `GET` → 405, `DELETE` → 204.
- Xác thực: `Authorization: Bearer <khóa>`; sai/hết hạn → 401 + `WWW-Authenticate: Bearer`.
- Mã: `backend/app/modules/agent_hub/mcp.py` (cổng), `mcp_keys.py` (khóa, băm SHA-256, bảng `tab_agent_mcp_key`),
  cửa tự phục vụ `GET/POST/DELETE /api/agent-hub/mcp-keys`, giao diện `profile-ai-key-tab.tsx`.
- Trên dev: `AGENT_ERP_URL` quyết định đường kết nối hiện trên màn (`https://deverp.degoholding.vn/api/mcp`).
  Prod chưa mở (theo luật tạm dừng prod 19/09).

## 5. Rủi ro đã chấp nhận

Dữ liệu ERP đi sang nhà cung cấp AI do từng người chọn (đại ca chốt 24/09). Giảm rủi ro bằng: khóa theo người
và theo quyền của người đó, mức chỉ đọc mặc định, hết hạn, audit từng lượt gọi, không mở tool đổi dữ liệu nhạy cảm.

## 6. Hợp đồng API cho giao diện Kho skill AI / AI của tôi (ai-CR-209, 212, 213 — doc/erp/21 §6.2)

Mọi đường đi qua proxy ERP `/api/agent-hub/*` (JWT web), trả phong bì `{success, message, data}`; dưới đây là `data`.
Ngày giờ ISO `YYYY-MM-DDTHH:MM:SS` giờ VN. Mã trạng thái là SỐ kèm nhãn (luật R2).

**Bộ mã**
- `CallStatus` (nhật ký lượt gọi): 1 Thành công · 2 Bị từ chối · 3 Lỗi.
- `KeyState` (khóa): 1 Chờ nhận · 2 Đang dùng · 3 Hết hạn · 4 Đã thu hồi.

### 6.1 Nhân sự — màn AI của tôi (G8)

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

### 6.2 Quản trị — Tổng quan (G1), Nhật ký (G6), Khóa nhân sự (G5)

| Đường | Quyền | Vào | `data` |
|---|---|---|---|
| `GET ai-overview` | `agent_group.read` | — | `{generated_at, skills: {skill_sets, skills}\|null, connected_users, connected_days: 30, calls_7d, calls_prev_7d, calls_change_pct\|null, denied_7d, error_7d, daily: [{day,total,ok,denied,error}×14], top_tools: [{key, calls}], top_users: [{key, calls, label}], top_skills: [{skill_id, calls}], keys_by_state: [{state, label, count}], expiring_keys: [{key_id, user_id, owner_label, name, expires_at, state}], expiring_days: 7}` — `skills = null` khi ERP không trả lời |
| `GET mcp-calls` | xem người khác: `agent_group.read` | + `user_id` | như §6.1; không quyền mà hỏi người khác → 403 |
| `GET mcp-calls/top?by=tool\|user&days=14&limit=10` | như trên | | `{by, days, items: [{key, calls, label?}]}` |
| `GET mcp-key-admin/meta` | — | — | `{days: [7,30,90,180,365], batch_max: 50, max_keys: 5, states: [{value, label}], can_read, can_create, can_delete}` |
| `GET mcp-key-admin/keys` | `ai_mcp_key_admin.read` | `department_id, state, user_id, batch_id, page, size≤200` | `{total, page, size, has_more, items: [Key + {owner_label, department_id, department, issued_by_label}]}` — chỉ khóa của người trong phạm vi |
| `POST mcp-key-admin/issue` | `ai_mcp_key_admin.create` | `{user_ids: [int] \| employee_ids: [int] \| department_id, days ∈ days, name}` — có `employee_ids` thì bỏ qua `department_id` (ai-CR-215) | `{batch_id, issued: [{user_id, employee_id, label, key_id}], skipped: [{user_id, employee_id, label, reason}]}` — chỉ mức chỉ đọc; có người / nhân sự ngoài phạm vi (hoặc id nhân sự không có thật) → 403 cả lượt; tổng > 50 người → 400; người đủ 5 khóa → `skipped`; nhân sự chưa có tài khoản / tài khoản đã khóa → `skipped` với `user_id = 0` |
| `POST mcp-key-admin/revoke` | `ai_mcp_key_admin.delete` | `{key_ids: [int]} \| {user_id} \| {batch_id}` | `{revoked: n}` — chủ khóa ngoài phạm vi → 403 cả lệnh |

### 6.3 Trần ở cổng `/api/mcp` (ai-CR-209, 213)

- 120 lượt / phút / khóa, 600 / phút / IP, 30 khóa sai / phút / IP → HTTP 429 + lỗi JSON-RPC -32000 + `Retry-After`.
- Ngân sách dữ liệu `erp_read`: 3.000 dòng / phút / khóa (`AGENT_MCP_ROW_BUDGET_PER_MIN`) — đủ thì tool trả từ chối
  kèm lời dặn lọc hẹp, nhật ký ghi «Quá ngân sách dữ liệu (dòng / phút)». Mặc định `erp_read` một trang × 50 dòng;
  5 trang × 100 dòng chỉ khi AI xin rõ. Đo trên dev 17/10: một lượt ĐMH xin 5 × 100 (dev có 103 đơn) mất 33 ms phía
  máy chủ, trả 51,6 KB (~500 byte / dòng) — 500 dòng đầy đủ sẽ cỡ 250 KB gửi sang ứng dụng AI.
