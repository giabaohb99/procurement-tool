# Kết nối AI riêng và Kho skill AI

| | |
|---|---|
| Bản | 1.1 — 19/10/2026 (bao-CR-631; 1.1 bao-CR-636: OAuth ChatGPT / claude.ai, xem lại khóa + tạm tắt, màn Ứng dụng AI đã kết nối, bộ Cẩm nang hệ thống) |
| CR | **bao-CR-631** + **bao-CR-636** — bài Trung tâm trợ giúp + tài liệu này; mã của cụm ở ai-CR-063, 207–225 (cổng MCP, OAuth, xem lại khóa), bao-CR-620–625 (Trang cá nhân, Kho skill K1–K6), bao-CR-635 (Ứng dụng AI đã kết nối) |
| Giao diện | **chỉ có trên `frontend-v2/`**: Trang cá nhân ▸ *Trợ lý AI của tôi* ▸ *Kết nối AI riêng* (`/me?tab=ai-connect`, mọi người) · phân hệ **Kho skill AI** (`/ai-skill/*`, quản trị) |
| Bài Help Center | `backend/scripts/seed_help_ket_noi_ai_mcp.py` — thẻ *Hướng dẫn sử dụng Kết nối AI riêng và Kho skill AI* + 7 bài theo tác vụ (a–g). **Nội dung ở đây và ở seed phải khớp nhau** |
| Hợp đồng kỹ thuật | `doc/agent-hub/06-cong-mcp.md` (cổng, khóa, nhóm tool, trần, API giao diện) · `doc/erp/21-kho-skill-ai-mcp.md` (thiết kế kho skill) · `doc/erp/21a-kich-ban-thu-mcp-dev.md` (kịch bản thử) |
| Nguồn bước nối ứng dụng | `backend/app/modules/agent_hub/mcp_setup.py` — màn *AI của tôi* đọc đúng tệp đó; đổi bước thì sửa seed + tài liệu này |

---

## 1. Chức năng này để làm gì

Nhân sự dùng **ứng dụng AI của chính mình** (Claude Desktop, Claude Code, Cursor, Gemini CLI) để hỏi dữ liệu ERP và đọc
cẩm nang công ty, **dưới đúng tài khoản và quyền của người đó**. Khác Trợ lý AI web / bot Telegram (công ty chạy model):
ở đây **tiền model do người dùng trả**, ERP chỉ cung cấp dữ liệu và cẩm nang qua một cổng chuẩn MCP (đại ca chốt 17/10/2026:
MCP là đường chính, bot Telegram đóng băng tính năng).

Hai thứ người dùng gặp:

| Thứ | Là gì | Ở đâu |
|---|---|---|
| **Khóa kết nối** | Chuỗi `dego_mcp_…` thay mật khẩu khi AI gọi vào ERP. Hai kiểu: **dán tay** (Claude Desktop qua tệp, Claude Code, Cursor, Gemini CLI) hoặc **kết nối qua đăng nhập ERP** (OAuth — ChatGPT, claude.ai, Claude Desktop Connectors). Gỡ / tạm tắt tức thì | Trang cá nhân ▸ *Kết nối AI riêng* |
| **Kho skill AI** | Cẩm nang công ty viết cho AI đọc (quy trình, quy định, mẫu báo cáo). Soạn một lần, gán theo sơ đồ tổ chức | Phân hệ *Kho skill AI* (quản trị) · thẻ *Skill bạn được đọc* ở màn AI của tôi |

Luật dùng chữ trên màn hình: lớp nhân sự **không** dùng «MCP», «JSON-RPC» — gọi là *Kết nối AI riêng*, *khóa kết nối*,
*công cụ*, *skill*.

## 2. Tạo khóa kết nối ở Trang cá nhân (bài a)

Màn **AI của tôi** (`profile-ai-connect-section.tsx`) đi theo ba bước đánh số.

**Bước 1 — Chọn ứng dụng AI**: ô *Ứng dụng AI* có 6 mục (`mcp_setup.CLIENTS`): Claude Desktop · Claude Code · Cursor ·
Gemini CLI · claude.ai (trình duyệt) · ChatGPT. Chọn một mục → hiện bước cài, tệp cần sửa, điều kiện, đoạn cấu hình
(`GET /api/agent-hub/mcp-setup?client=…`, trường `auth: "key" | "oauth"`). Ứng dụng `auth = key`: đoạn mẫu mang chỗ giữ
`<KHÓA_CỦA_BẠN>`, tạo khóa xong màn tự thay bằng khóa vừa hiện. Ứng dụng `auth = oauth` (claude.ai, ChatGPT; Claude
Desktop qua Connectors): `format = url`, «đoạn cấu hình» chỉ là địa chỉ cổng — không cần khóa, xem §4b.

**Bước 2 — Khóa của bạn**

| Việc | Cách | Luật |
|---|---|---|
| Tạo khóa | *Tên khóa* (vd «Claude máy công ty») · *Mức* · **Tạo khóa** → khóa hiện kèm nút chép, đoạn cấu hình bước 1 tự điền | Hạn 90 ngày (tự tạo); tối đa **5 khóa dán tay còn hiệu lực** / tài khoản (kể cả đang tắt; kết nối OAuth không tính); mỗi lượt gọi ghi *dùng lần cuối*; nghỉ việc đóng cùng tài khoản |
| Xem lại khóa (ai-CR-221) | `GET mcp-keys/{id}/reveal` — chỉ CHỦ KHÓA, đăng nhập web; quản trị ở Khóa nhân sự chỉ thấy 4 ký tự cuối; qua MCP không có đường | Bản mã hóa hai chiều `raw_view` (Fernet từ `JWT_SECRET`); mỗi lần xem ghi nhật ký `key/reveal` (ứng dụng «ERP web»), `Cache-Control: no-store`. Không xem được (409): khóa tạo trước ai-CR-221 → *tạo lại để xem*; kết nối OAuth; phát hộ chưa nhận; hết hạn. Đổi `JWT_SECRET` thì mọi bản xem lại hỏng |
| Tạm tắt / bật lại (ai-CR-221) | `PATCH mcp-keys/{id} {enabled}` — cả kết nối OAuth | Trạng thái **5 Đang tắt**; `/api/mcp` 401, nhật ký «Khóa đang tắt»; OAuth tắt thì không làm mới được (`invalid_grant`); vẫn tính trần 5 khóa; chờ nhận / hết hạn → 409. Khác thu hồi: bật lại là chạy ngay |
| Nhận khóa phát hộ | Chuông *«Bạn có khóa kết nối AI chờ nhận»* → khối *Khóa quản trị phát cho bạn, chờ nhận* → **Nhận khóa** (hiện một lần) | Chưa nhận thì cổng từ chối; khóa phát hộ luôn mức Chỉ đọc |
| Gỡ khóa | Nút **Gỡ khóa** trên từng khóa | Hiệu lực tức thì; dùng khi đổi máy, nghi lộ |
| Kết nối OAuth | Mỗi lần **Cho phép** = một dòng khóa `kind = 2` tên *Qua ChatGPT* / *Qua Claude* trong cùng khối | Cùng mức, nhật ký, nút gỡ, công tắc tạm tắt; gỡ = chặn cả mã làm mới; sống 90 ngày cố định |

⚠️ Nhãn nút *Hiện khóa* / *Tạm tắt* trên màn Khóa của bạn là của bao-CR-633 (Agent 3) — seed viết theo hợp đồng API; màn
lên dev xong đối chiếu lại nhãn.

| Mức | AI làm được | Dùng khi |
|---|---|---|
| **Chỉ đọc** (mặc định) | Tra cứu trong danh sách trắng `READ_TOOLS` + 3 tool skill + `report_issue` | Lần đầu nối; máy dùng chung |
| **Được ghi** | Thêm `draft_*`, `ticket_create`, ghi chú, `confirm_draft`. Tạo phiếu luôn **hai bước** nháp → xác nhận; đề nghị thanh toán chỉ tạo trên web | Nhờ AI lập phiếu |

**Bước 3 — Kiểm tra kết nối**: mỗi khóa còn hiệu lực hiện *Đã nối, lượt thành công gần nhất lúc…* hoặc *Chưa thấy AI gọi
lần nào* (`GET mcp-keys/{id}/last-call`, `connected` = có ít nhất một lượt thành công); nút **Kiểm tra lại**.

Dưới cùng: thẻ **Skill bạn được đọc** (`visible_skills`) và **20 lượt AI tra cứu gần nhất** (`GET mcp-calls`, người thường
chỉ của mình). Nút **Xem cách hoạt động** mở demo chín chương (dữ liệu giả).

Ba mục cạnh nhau trong nhóm *Trợ lý AI của tôi*, không lẫn: *Kết nối AI riêng* (AI của bạn vào ERP) · *Khóa model AI*
(khóa Gemini / Claude cho bot và Trợ lý công ty suy nghĩ) · *Liên kết Telegram*.

## 3. Nối Claude Desktop (bài b)

**Hai cách** (ai-CR-218): *Cách 1* Settings ▸ Connectors ▸ Add custom connector ▸ dán địa chỉ cổng ▸ Connect ▸ đăng nhập
ERP, Cho phép (không cần Node.js, không cần khóa; gỡ ở dòng *Qua Claude* trong Khóa của bạn) — đúng §4b. *Cách 2* tệp cấu
hình + khóa dán tay, dưới đây. Bản Claude Desktop không có mục Connectors, hoặc muốn dùng chung khóa với Claude Code → cách 2.

Cách 2: Claude Desktop **không nhận `url` + `headers`** trong `claude_desktop_config.json` (chỉ chạy lệnh cục bộ) → đi qua cầu
`npx -y mcp-remote`. Điều kiện: **Node.js 18+** (`node -v`), đã có khóa.

1. Màn AI của tôi chọn *Claude Desktop*, tạo khóa, chép đoạn cấu hình (đã điền khóa).
2. Claude Desktop ▸ **Settings ▸ Developer ▸ Edit Config** → mở `%APPDATA%\Claude\claude_desktop_config.json`
   (macOS `~/Library/Application Support/Claude/claude_desktop_config.json`).
3. Dán khối dưới; tệp đã có `mcpServers` thì **chỉ thêm khối `dego-erp` vào trong**.
4. Thay `<KHÓA_CỦA_BẠN>`, **giữ `Bearer ` phía trước**.
5. Lưu, **THOÁT HẲN** Claude Desktop (Quit ở biểu tượng khay — đóng cửa sổ chưa phải thoát).
6. Mở lại; ô chat bấm biểu tượng công cụ thấy `dego-erp` là đã nối; về ERP bấm *Kiểm tra lại*.

```json
{
  "mcpServers": {
    "dego-erp": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://erp.degoholding.vn/api/mcp", "--header", "Authorization:${DEGO_MCP_KEY}"],
      "env": { "DEGO_MCP_KEY": "Bearer <KHÓA_CỦA_BẠN>" }
    }
  }
}
```

Địa chỉ cổng lấy theo màn AI của tôi (`AGENT_ERP_URL` + `/api/mcp`; dev là `deverp.degoholding.vn`). Khóa nằm ở biến
`DEGO_MCP_KEY` vì khoảng trắng trong `args` làm hỏng lệnh trên Windows; đặt `setx DEGO_MCP_KEY "Bearer …"` cho cả máy thì
bỏ được khối `env`, nhưng `setx` chỉ có hiệu lực với tiến trình mở sau.

Ba lỗi riêng của Claude Desktop:

| Hiện tượng | Nguyên nhân | Làm gì |
|---|---|---|
| Tệp cấu hình trở lại như cũ sau khi sửa | Claude Desktop **ghi đè tệp** khi đang chạy | Thoát hẳn trước khi sửa, hoặc luôn sửa qua *Settings ▸ Developer ▸ Edit Config* rồi thoát hẳn |
| Thấy `dego-erp` nhưng *Server disconnected*, không có công cụ | Thiếu Node.js · chưa thoát hẳn · dòng `Authorization` sai · khóa hết hạn / đã gỡ | `node -v`; xem lại dòng khóa; thoát hẳn; đọc `%LOCALAPPDATA%\Claude\logs\mcp-server-dego-erp.log` (che khóa khi gửi) |
| Máy này nối được, máy khác không | Mỗi máy một tệp cấu hình, nên mỗi máy một khóa | Tạo thêm khóa (≤ 5), đặt tên theo máy |

Liên quan vận hành: từ ai-CR-218 nginx erp **chuyển** `/.well-known/(oauth-|openid-configuration)` sang api (thay dòng 404
của bao-CR-625) vì ERP nay là máy chủ cấp quyền; `mcp-remote` có khóa header hợp lệ vẫn đi thẳng, chỉ vào OAuth khi 401.

## 4. Nối Claude Code, Cursor, Gemini CLI (bài c)

Ba ứng dụng nhận thẳng địa chỉ + dòng khóa.

- **Claude Code**: `claude mcp add --transport http --scope user dego-erp https://erp.degoholding.vn/api/mcp --header "Authorization: Bearer <KHÓA_CỦA_BẠN>"`
  → `claude mcp list` thấy `dego-erp` đã kết nối. `--scope user` dùng ở mọi thư mục. **Mẹo Windows:** trong PowerShell
  gõ `claude` có thể bị chặn vì chính sách chạy tệp `.ps1` (execution policy) → gõ `claude.cmd mcp add …` hoặc dùng
  Command Prompt; không cần đổi chính sách máy.
- **Cursor**: Settings ▸ MCP ▸ Add new MCP server, hoặc `~/.cursor/mcp.json` (`.cursor/mcp.json` trong dự án nếu chỉ dùng
  ở đó): `{"mcpServers": {"dego-erp": {"url": "<url>", "headers": {"Authorization": "Bearer <KHÓA_CỦA_BẠN>"}}}}` → chấm xanh.
- **Gemini CLI**: `~/.gemini/settings.json`, như Cursor nhưng ô **`httpUrl`** thay `url` → chạy `gemini`, gõ `/mcp`.
- **claude.ai (trình duyệt), ChatGPT**: không dán khóa — tự mở trang ERP để đăng nhập và Cho phép, xem §4b.

## 4b. Nối ChatGPT và claude.ai bằng đăng nhập ERP (bài g — OAuth, ai-CR-218/222/225)

ERP là máy chủ cấp quyền OAuth 2.1 tối thiểu theo MCP 2025-06-18 (doc 06 §2.3): ứng dụng gọi `/api/mcp` không token → 401
kèm `resource_metadata` → đọc `/.well-known/oauth-protected-resource` + `oauth-authorization-server` → tự đăng ký
`POST /api/oauth/register` → `GET /api/oauth/authorize` (PKCE S256 bắt buộc) → màn ERP v2 `/oauth/consent/<chuỗi ký, 10
phút>` → `POST /api/oauth/token` (access `dego_mcp_` 1 giờ, refresh `dego_mcr_` xoay vòng) → `POST /api/oauth/revoke`.

Bước người dùng (từ `mcp_setup.py`):
- **claude.ai** (và Claude Desktop ▸ Settings ▸ Connectors): Settings ▸ Connectors ▸ Add custom connector → đặt tên, dán địa
  chỉ cổng vào *Remote MCP server URL* → Add → Connect → trang ERP: đăng nhập, chọn Chỉ đọc / Được ghi, **Cho phép** → về
  claude.ai bật DEGO ERP ở nút công cụ. Team / Enterprise: chủ tổ chức thêm ở Organization settings trước.
- **ChatGPT**: Settings ▸ Apps & Connectors ▸ Advanced settings ▸ bật Developer mode → Create: tên, *MCP Server URL*,
  Authentication = OAuth, tick tin tưởng → Create → trang ERP Cho phép → chọn DEGO ERP ở nút + trong ô chat. Tên mục đổi theo
  phiên bản ChatGPT.

Màn Cho phép (`oauth-consent-page.tsx`, API `GET /api/agent-hub/oauth/request/{req}`, `POST …/approve | deny`): tiêu đề
*Cho phép ứng dụng AI dùng ERP thay bạn*; ghi tên ứng dụng (TỰ KHAI) + **`redirect_host`** (hostname nơi quay về; máy cục bộ
= *máy tính của bạn*, lược đồ riêng = *ứng dụng cài trên máy (x://)*) + tài khoản; `redirect_trusted = false` (host ngoài
chatgpt.com / openai.com / claude.ai / anthropic.com / claude.com / cục bộ) → hộp cảnh báo đỏ *Nơi quay về … không thuộc
ứng dụng AI quen* — người dùng **phải dừng** nếu không phải chính mình vừa thêm kết nối; chọn Chỉ đọc (mặc định theo mức
ứng dụng xin) / Được ghi; **Cho phép** / **Từ chối** (`error=access_denied`). Chống nhúng: `X-Frame-Options DENY` +
`frame-ancestors 'none'` cho `/oauth/consent/`, màn tự kiểm `window.top !== window.self`.

Sau Cho phép: một dòng khóa `kind = 2` *Qua <tên ứng dụng>* ở Khóa của bạn / Khóa nhân sự (cùng mức, nhật ký ghi
`client_name`); gỡ ở đó = chặn cả mã làm mới; tạm tắt được; sống **90 ngày cố định**, hết thì Connect lại; cấp lại cùng
(người, ứng dụng) thì kết nối cũ chết; không tính trần 5 khóa. Trần tự đăng ký 5 / phút / IP + 200 / 24 giờ (429).

Lỗi hay gặp: Connect không mở trang ERP (chặn cửa sổ bật lên; địa chỉ phải kết thúc `/api/mcp`); đăng nhập xong không thấy
màn Cho phép (lượt quá 10 phút → Connect lại); `access_denied` (đã Từ chối); mất kết nối sau một thời gian (hết 90 ngày /
gỡ / tạm tắt / quản trị xóa ứng dụng → Connect lại).

## 5. AI làm được gì: công cụ và skill (bài d)

| | Công cụ | Skill |
|---|---|---|
| Là gì | Hàm AI gọi vào ERP (`assistant.tools`, chung với Trợ lý web / bot) | Bài cẩm nang trong Kho skill AI |
| Ai làm ra | Có sẵn; quản trị bật / tắt theo **nhóm** (`mcp_settings.GROUPS`) | Quản trị / trưởng phòng soạn, gán ai được đọc |
| Số lượng | Tùy mức khóa + nhóm bật (dev 19/10: khóa Chỉ đọc, 7 nhóm bật ≈ 34 công cụ) | Tùy phòng ban, chức vụ, cấp bậc; ai cũng có bộ **Cẩm nang hệ thống** 7 skill (§6) |

Nhóm công cụ (doc 06 §4): mặc định **bật** `mine` việc của tôi · `leave` nghỉ phép · `directory` danh bạ, thuật ngữ, HDSD ·
`reports` báo cáo gom sẵn (`report_summary`, 13 báo cáo, gác `require_report`) + bảng số (`dataset_query`) · `skills`;
mặc định **tắt** `purchase` (gồm `erp_read`) · `finance` · `document` · `work` · `customs` · `google` · `personal`. Nhóm
tắt: tool không có trong `tools/list`, gọi thẳng → `denied` kèm tên nhóm. `report_issue`, `confirm_draft` luôn mở.
Mọi tool chạy **dưới quyền chủ khóa** (`require` + `apply_scope` + `require_report`): nhóm bật không có nghĩa thấy tất cả.

Skill: cổng dặn AI *gọi `list_skills` trước việc nghiệp vụ, `read_skill` đúng cái cần, áp dụng vào việc chứ không đọc lại
nguyên văn*. AI chỉ đọc skill **đã xuất bản** và **được gán** (`visible_skills`, tính lúc gọi — đổi phòng là đổi skill, khóa
giữ nguyên). Skill không được gán trả cùng câu với skill không tồn tại. Mức *Bảo vệ* không trả tệp; *Khóa* chỉ tên + tóm tắt.
AI không tự mở skill thì nhắc *«Hãy xem cẩm nang công ty trước khi trả lời»*.

Câu mẫu: *Liệt kê các skill công ty mà bạn đọc được* · *Tôi còn bao nhiêu ngày phép?* · *Yêu cầu mua hàng tôi lập tuần
trước đang ở bước nào?* · *Lập báo cáo mua hàng tháng 9 theo nhà cung cấp, xuất Excel* · khóa được ghi: *Soạn đơn nghỉ
phép thứ Sáu tuần sau* → xem nháp → *tạo và gửi duyệt*.

## 6. Quản trị Kho skill AI (bài e)

Phân hệ *Kho skill AI* hiện với người có `ai_skill.read` hoặc `ai_mcp_key_admin.read`. Menu: Tổng quan · Bộ skill · Khóa
nhân sự · **Ứng dụng AI đã kết nối** (bao-CR-635) · Nhật ký sử dụng · Giới thiệu · Cấu hình.

| Khái niệm | Bảng | Ghi chú |
|---|---|---|
| Bộ skill | `tab_ai_skill_set` | mã, tên, pháp nhân, **phòng chủ quản**, trạng thái Nháp / Đang dùng / Lưu trữ, mức bảo mật Mở / Bảo vệ / Khóa |
| Skill | `tab_ai_skill` + `tab_ai_skill_version` + `tab_ai_skill_file` | `slug` 2–100 ký tự `[A-Za-z0-9][A-Za-z0-9_-]*`; *Tóm tắt cho AI* ≤ 500 ký tự bắt buộc khi xuất bản; phiên bản chỉ thêm; tệp chữ ≤ 2 MB |
| Ai được đọc | `tab_ai_skill_access` | khuôn `tab_report_access` + chức vụ, cấp bậc; `include_children`; cấm thắng; dòng của skill **thay** quyền bộ |

Màn **Bộ skill**: *Tạo bộ* · *Tải gói lên* (`.zip` / `.skill` có `SKILL.md` với `name` / `description`; tải lại gói cùng tên =
thay toàn bộ tệp; thêm tệp = cộng dồn). **Chi tiết bộ**: tab *Skill* (Thêm skill, Tải gói lên, Xuất bản, xóa) · *Ai được đọc*
(*Gán thêm*: phòng ban [kể cả phòng con] · chức vụ · cấp bậc · người · pháp nhân · vai trò; chiều Cho phép / Không cho phép
tô đỏ; hạn; lý do; thu hồi hiệu lực ~1 phút) · *Lịch sử*. **Soạn skill**: hai cột Markdown / *Xem như AI đọc*; *Lưu nháp*
hoặc Ctrl+S; rời trang chưa lưu thì hỏi; *Xuất bản* (cần `ai_skill.approve`) tự lưu nháp trước, kèm *Ghi chú thay đổi*;
sau đó nháp mới hơn bản AI đọc được đánh dấu; tab *Tệp đi kèm* · *Phiên bản* (so hai bản) · *Ai được đọc* (riêng skill) ·
*Lịch sử*.

Luật đọc (doc 21 §4.2): bộ đọc được **và** skill không bị thu hẹp; phòng con kế thừa theo `parent`; cấm thắng; chỉ skill
*Đang dùng* của bộ *Đang dùng* lộ ra MCP; một hàm `ai_skill.access_service.visible_skills(db, user)` dùng chung MCP /
bot / Trợ lý web / màn AI của tôi.

**Khóa nhân sự** (`ai_mcp_key_admin`, phạm vi theo hồ sơ **chủ khóa**): bảng khóa (Chờ nhận / Đang dùng / Hết hạn / Đã thu
hồi), lọc phòng + trạng thái; **Phát khóa** cho người (theo danh sách nhân sự) hoặc cả phòng, ≤ 50 / lượt, hạn 7 / 30 / 90 /
180 / 365, luôn Chỉ đọc; có người ngoài phạm vi → từ chối cả lượt; đủ 5 khóa / chưa có tài khoản / tài khoản khóa → bỏ qua
kèm lý do; người nhận có **chuông** (không email, không Telegram). **Thu hồi**: tick → hộp chỉ đếm khóa còn hiệu lực; thu hồi
theo khóa / người / lượt; dòng thu hồi giữ lại.

**Ứng dụng AI đã kết nối** (bao-CR-635; `GET /api/agent-hub/oauth-clients` gác `agent_group.read`, `DELETE …/{id}` gác
`.write`, trả `can_delete`): bảng ứng dụng tự đăng ký OAuth — tên tự khai + 6 ký tự cuối `client_id`, `redirect_hosts`,
`live_grants`, dùng lần cuối, đăng ký; IP + `auth_method` ẩn mặc định; `trusted = false` → ô đỏ + nhãn *Host lạ*, dòng tóm
tắt đếm host lạ. **Xóa** có hộp xác nhận nêu số kết nối bị cắt — thu hồi mọi kết nối + xóa mã cấp quyền, dòng khóa tương
ứng → Đã thu hồi; người dùng Cho phép lại từ đầu. Ứng dụng > 7 ngày không kết nối sống và không dùng → `oauth.purge` tự dọn.

**Bộ Cẩm nang hệ thống** (ai-CR-220, K7): mã `SYS-HANDBOOK`, mức Mở, Đang dùng, 7 skill `quy-trinh-thu-mua` ·
`van-thu-van-ban` · `du-an-cong-viec` · `nghi-phep` · `dat-phong-hop` · `nhan-su-ho-so` · `nha-may-he-thong-cong-viec`
(+ 11 tệp gốc nhà máy làm `references/`), gieo bởi `ai_skill/handbook_seed.ensure_system_handbook` ở `seed.py` +
`seed_prod.py` khi chưa có bộ mã đó (kể cả bản xóa mềm) — có rồi **không đụng**. Trợ lý web + bot core_v2 + MCP đọc cùng
kho qua `visible_skills` (lời nhắc chỉ mang danh mục ≤ 1.500 ký tự; tool nội bộ `skill_tool.py` chạy `internal=True`, mức
bảo mật chỉ chặn AI ngoài). Sửa skill + Xuất bản → lượt sau AI đọc bản mới. Pháp nhân tạo sau lần gieo phải gán quyền đọc
tay ở tab Ai được đọc.

**Cấu hình** (`agent_group.write`; `tab_setting.agent_mcp_settings`): bật / tắt nhóm; giới hạn `rate_per_key` 10–2000
(mặc định 120) · `rate_per_ip` 0–20000 (600) · `bad_key_per_ip` 5–1000 (30) · `row_budget_per_min` 0–100000 (3000, 0 =
không chặn) · `log_retention_days` 30–730 (180); *Câu dặn thêm cho AI* ≤ 1000 ký tự. Ô trống không hiểu là 0; ngoài dải
chặn lưu; chỉ gửi phần đã đổi.

**Tổng quan** (`agent_group.read`): bộ / skill, người đã nối AI, lượt 7 ngày so 7 ngày trước, từ chối + lỗi, biểu đồ 14
ngày, top công cụ / người / skill, khóa sắp hết hạn.

Quyền: `ai_skill` (read · create · write · delete · approve = xuất bản; phạm vi pháp nhân + phòng chủ quản) ·
`ai_mcp_key_admin` (read · create · delete) · `agent_group` (Tổng quan, nhật ký người khác, Cấu hình). Hai vai trò seed
*Quản trị kho skill AI* (toàn công ty) và *Biên tập skill AI phòng ban* (phòng mình); seed prod không ghi đè → tick tay ở
*Nhân sự ▸ Phân quyền tài khoản*.

Thứ tự dựng: tick quyền → tạo bộ cho một phòng, 2–3 skill, viết kỹ tóm tắt, xuất bản → gán phòng (kể cả phòng con) → phát
khóa chỉ đọc cho vài người thử → đọc nhật ký một tuần rồi mới mở thêm nhóm công cụ.

## 7. Nhật ký và lỗi thường gặp (bài f)

Nhật ký (`tab_agent_mcp_call`): mỗi lượt JSON-RPC một dòng, kể cả `initialize`, khóa sai, quá tần suất (lượt sai hàng
loạt chỉ ghi 10 dòng đầu / phút); người, nhân sự, phòng, pháp nhân chụp lúc gọi, ứng dụng (`clientInfo`), method, tool,
`skill_id`, trạng thái (1 Thành công · 2 Bị từ chối · 3 Lỗi), lý do, thời gian, IP. Giữ 180 ngày, beat `agent-mcp-log-purge`
gom vào `tab_agent_mcp_call_daily`. Người thường xem 20 lượt của mình ở màn AI của tôi; quản trị xem *Nhật ký sử dụng*
(lọc ngày / công cụ / trạng thái, *Xuất CSV (trang hiện tại)*, chặn công thức Excel ở ô bắt đầu bằng `= + - @`).

| Lý do trong nhật ký / câu AI nhận | Nghĩa | Làm gì |
|---|---|---|
| *Khóa sai* · *Khóa MCP không hợp lệ hoặc đã hết hạn* (401) | khóa chép sai / không tồn tại; câu trả ngoài chung một câu, lý do chỉ ở nhật ký | chép lại hoặc tạo khóa mới |
| *Khóa đã hết hạn* | quá hạn | tạo khóa mới |
| *Khóa đã bị thu hồi* | người dùng gỡ hoặc quản trị thu hồi | hỏi quản trị; tạo khóa mới |
| *Khóa phát hộ chưa được chủ khóa nhận* | chưa bấm Nhận khóa / dán khóa của người khác | Trang cá nhân → Nhận khóa |
| *Khóa đang tắt* | đã tạm tắt khóa / kết nối (ai-CR-221) | bật lại ở Khóa của bạn |
| `invalid_grant` / mất kết nối OAuth | hết 90 ngày, gỡ, tạm tắt, hoặc quản trị xóa ứng dụng | Connect lại (§4b) |
| dòng `key/reveal` ứng dụng «ERP web» | chính chủ vừa xem lại khóa | không phải rò rỉ |
| *Quá tần suất (khóa)* (429, JSON-RPC -32000, `Retry-After`) | > 120 lượt / phút / khóa | đợi một phút; mỗi máy một khóa |
| *Quá tần suất (IP)* · *(khóa sai liên tục)* | > 600 lượt / phút / IP · > 30 khóa sai / phút / IP | đợi; báo quản trị nếu lặp |
| `denied` kèm tên nhóm | nhóm tool bị tắt ở Cấu hình | xin bật nhóm |
| *Khóa này chỉ đọc; tạo phiếu cần khóa «được ghi»* | nhờ tạo phiếu bằng khóa Chỉ đọc | tạo khóa Được ghi |
| `denied` thiếu quyền / chưa được giao báo cáo | phạm vi dữ liệu như trên web | xin quyền / giao báo cáo |
| *không có skill đó* | chưa xuất bản hoặc không gán — cùng câu với không tồn tại | hỏi người soạn |
| bộ mức Bảo vệ không mở tệp | đúng thiết kế | — |
| `has_more` / hết ngân sách dòng | ≤ 5 trang × 100 dòng / lượt, 3.000 dòng / phút / khóa | lọc hẹp hơn |

Ứng dụng không thấy công cụ / *Server disconnected*: kiểm dòng `Authorization: Bearer <khóa>`, khóa còn hiệu lực (phát hộ
phải Nhận), Claude Desktop thì Node.js + thoát hẳn + tệp không bị ghi đè + log `mcp-server-dego-erp.log`, địa chỉ cổng kết
thúc `/api/mcp`; nhật ký **không có dòng nào** = ứng dụng chưa gọi tới ERP (lỗi ở máy người dùng), **có dòng Bị từ chối** =
đọc lý do. Không phải lỗi: số công cụ khác nhau giữa hai người; AI không theo quy trình (chưa mở skill); *Kiểm tra kết nối*
chưa thấy dù đã liệt kê công cụ (cần một lượt gọi thật); sửa skill mà AI như cũ (chưa Xuất bản). Báo lỗi: nhờ AI
(`report_issue`, luôn mở) hoặc Trang cá nhân ▸ Yêu cầu hỗ trợ, kèm giờ thử, **che khóa**.

## 8. Phạm vi chưa làm / ghi chú

- Prod **chưa mở cổng MCP** (luật tạm dừng prod 19/09; doc 06 §5 liệt kê việc cần khi lên prod). Bài Help Center viết
  địa chỉ `erp.degoholding.vn` làm ví dụ, luôn dặn lấy địa chỉ thật ở màn AI của tôi.
- Nhãn nút xem lại / tạm tắt trên màn Khóa của bạn chờ bao-CR-633 (Agent 3) lên dev; đối chiếu lại bài (a).
- Tên mục trong Cài đặt của ChatGPT / claude.ai đổi theo phiên bản của họ; sửa `mcp_setup.py` + seed + tài liệu này cùng lúc.
- Bot Telegram đọc chung kho skill (K7) và quản trị qua bot (K9): gác (doc 21 §7.1).
