# AGENT HUB — CỔNG MCP: dùng AI của bạn với dữ liệu ERP

**Bản 1.0 · 25/09/2026 · ai-CR-063 (M-01 · M-02 · M-03 · M-04 · M-05 của [`04`](./04-danh-sach-tinh-nang.md), phase 4).**

Đại ca chốt 24/09/2026: mỗi người **tự do chọn ứng dụng AI** (Claude Desktop, Cursor, ChatGPT, …) và tự
gắn khóa của mình; hệ thống chỉ cung cấp **công cụ** qua một cổng MCP nằm trong backend ERP. Cổng dùng
**chung bộ tool** với Trợ lý AI trên web và bot Telegram — không viết lại tool, không mở đường mới vào dữ liệu.

## 1. Người dùng làm gì

1. ERP → Trang cá nhân → tab **Khóa AI** → khối **Kết nối MCP** → đặt tên, chọn mức, **Tạo khóa MCP**.
2. Khóa hiện **đúng một lần** (`dego_mcp_…`), kèm đoạn cấu hình sẵn. Dán vào ứng dụng:
   - **Claude Desktop**: `claude_desktop_config.json` → `mcpServers`:
     ```json
     {"mcpServers": {"dego-erp": {"url": "https://deverp.degoholding.vn/api/mcp",
                                  "headers": {"Authorization": "Bearer dego_mcp_…"}}}}
     ```
   - **Cursor**: Settings → MCP → Add server (URL + header như trên).
   - Ứng dụng nào nói MCP «Streamable HTTP» đều dùng được; cổng chỉ trả JSON, không cần luồng SSE.
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
