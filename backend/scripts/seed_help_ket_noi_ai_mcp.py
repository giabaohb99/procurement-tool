# -*- coding: utf-8 -*-
"""Seed nội dung Trung tâm trợ giúp cho cụm KẾT NỐI AI RIÊNG + KHO SKILL AI (bao-CR-631, 19/10/2026).

Dựng cây bài viết: 1 thẻ phân hệ (hiện ngoài trang chủ "Các Phân hệ") -> 6 bài chia theo TÁC VỤ:
  (a) tạo khóa kết nối ở Trang cá nhân · (b) nối Claude Desktop · (c) nối Claude Code, Cursor, Gemini CLI ·
  (g) nối ChatGPT, claude.ai bằng đăng nhập ERP (OAuth) · (d) AI của bạn làm được gì: công cụ và skill ·
  (e) quản trị Kho skill AI · (f) nhật ký và lỗi thường gặp.

bao-CR-639 (19/10, tối, đính chính theo ảnh đại ca chụp): ChatGPT nối ở Settings → Connectors → hộp New Connector (Name,
MCP Server URL, Authentication OAuth, tick I trust this application) → Create; Developer mode bật trước; cần gói trả phí.
Khớp khối chatgpt của `mcp_setup.py`.
bao-CR-636 (19/10, chiều): thêm bài (g) OAuth (ai-CR-218/222/225); Claude Desktop có hai cách (Connectors hoặc mcp-remote);
khóa xem lại được + bật / tắt tạm (ai-CR-221) — bỏ câu «chỉ hiện một lần»; quản trị có màn Ứng dụng AI đã kết nối
(bao-CR-635) và bộ Cẩm nang hệ thống 7 skill (ai-CR-220). ⚠️ Nhãn nút Hiện / Tạm tắt ở màn Khóa của bạn viết theo hợp đồng
API; màn giao diện là bao-CR-633 của Agent 3 — lên dev xong đối chiếu lại nhãn.

Nguồn sự thật của từng bước nối ứng dụng là `app/modules/agent_hub/mcp_setup.py` (màn «AI của tôi» đọc đúng tệp đó);
bài ở đây chép lại CÙNG bước, cùng tên tệp, cùng khối cấu hình — đổi bên kia thì sửa bên này.

Chạy trong container api:
    docker compose exec -T api python scripts/seed_help_ket_noi_ai_mcp.py
    (dev VPS2: docker exec procurement-tool-dev-api-1 python scripts/seed_help_ket_noi_ai_mcp.py)
rồi `python scripts/reindex_help_rag.py` để Trợ lý AI đọc được bài mới.

Idempotent: có thẻ gốc cũ thì xóa nguyên cây con (con trước, cha sau — FK tự tham chiếu không cascade) rồi dựng lại.

⚠️ Nội dung ở đây phải KHỚP với `doc/tai-lieu-chuc-nang/22-ket-noi-ai-rieng-va-kho-skill.md` và
`doc/agent-hub/06-cong-mcp.md` (hợp đồng cổng). Ba nơi lệch nhau thì người dùng đọc một đằng, màn hình làm một nẻo.

⚠️ Tiêu đề bài phải KHÁC mọi bài đang có trong Trung tâm trợ giúp (portal tra ngược slug -> id trên client, trùng tiêu đề
là trùng slug). Cụm Trợ lý AI đã có các bài «Trợ lý AI», «Lập bộ tài khoản thu mua bằng Trợ lý AI», «Tạo, sửa, xóa phiếu
và xem quyền bằng Trợ lý AI» — bài ở đây luôn mang chữ «AI riêng» hoặc «Kho skill AI» để không đụng.

⚠️ KHÔNG bao giờ in khóa thật vào bài: mọi ví dụ dùng chỗ giữ <KHÓA_CỦA_BẠN> đúng như màn hình.
"""
import re
import sys
import unicodedata

sys.path.insert(0, "/app")

from sqlalchemy import text  # noqa: E402

import app.core.all_models  # noqa: F401,E402 — nạp đủ mapper trước khi query
from app.core.database import SessionLocal  # noqa: E402
from seed_help_ket_noi_ai_cach_1 import (OAUTH, OAUTH_CONTENT, OAUTH_SUMMARY, ROOT_CONTENT,  # noqa: E402
                                         ROOT_SUMMARY, TAO_KHOA, TAO_KHOA_CONTENT, TAO_KHOA_SUMMARY)
from seed_help_ai_rieng_lam_duoc_gi import CONTENT as AI_RIENG_CONTENT  # noqa: E402
from seed_help_ai_rieng_lam_duoc_gi import SUMMARY as AI_RIENG_SUMMARY  # noqa: E402
from app.modules.help_center.model import (  # noqa: E402
    HelpArticle,
    HelpHomeItem,
    HelpHomeSection,
)

ROOT_TITLE = "Hướng dẫn sử dụng Kết nối AI riêng và Kho skill AI"


def slugify(value: str) -> str:
    """Sinh slug y hệt `slugify()` của help-center (help-slug.tsx)."""
    value = value.replace("đ", "d").replace("Đ", "D")
    value = unicodedata.normalize("NFD", value)
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return re.sub(r"^-+|-+$", "", value)


def ref(target_title: str, label: str) -> str:
    return (
        f'<a href="/{slugify(target_title)}" '
        'style="color:var(--primary,#2563eb);font-weight:600;text-decoration:underline">'
        f"{label}</a>"
    )


CLAUDE_DESKTOP = "Nối Claude Desktop với ERP"
CLIENT_KHAC = "Nối Claude Code, Cursor và Gemini CLI với ERP"
CONG_CU = "AI riêng của bạn làm được gì trong ERP: công cụ và skill"
QUAN_TRI = "Dành cho quản trị — Kho skill AI: bộ skill, xuất bản, ai được đọc"
NHAT_KY = "Nhật ký lượt gọi của AI riêng và lỗi thường gặp khi nối"

#  Chỗ giữ khóa + tên máy chủ đúng như `mcp_setup.py` (KEY_PLACEHOLDER, SERVER_NAME) — người dùng thấy cùng một chữ ở hai nơi.
KEY = "&lt;KHÓA_CỦA_BẠN&gt;"
SERVER = "dego-erp"
URL = "https://erp.degoholding.vn/api/mcp"      # địa chỉ thật lấy ở màn AI của tôi (dev là deverp.degoholding.vn)

CLAUDE_DESKTOP_JSON = f"""{{
  "mcpServers": {{
    "{SERVER}": {{
      "command": "npx",
      "args": ["-y", "mcp-remote", "{URL}", "--header", "Authorization:${{DEGO_MCP_KEY}}"],
      "env": {{ "DEGO_MCP_KEY": "Bearer {KEY}" }}
    }}
  }}
}}"""

CURSOR_JSON = f"""{{
  "mcpServers": {{
    "{SERVER}": {{ "url": "{URL}", "headers": {{ "Authorization": "Bearer {KEY}" }} }}
  }}
}}"""

GEMINI_JSON = f"""{{
  "mcpServers": {{
    "{SERVER}": {{ "httpUrl": "{URL}", "headers": {{ "Authorization": "Bearer {KEY}" }} }}
  }}
}}"""

CLAUDE_CODE_CMD = f'claude mcp add --transport http --scope user {SERVER} {URL} --header "Authorization: Bearer {KEY}"'


TREE = {
    "title": ROOT_TITLE,
    "icon": "rocket",
    #  Bài gốc + Cách 1 + Cách 2 sở hữu ở seed_help_ket_noi_ai_cach_1.py (26/10: đăng nhập ERP là cách ưu tiên).
    "summary": ROOT_SUMMARY,
    "content": ROOT_CONTENT,
    "children": [
        {
            "title": OAUTH,
            "icon": "shield-check",
            "summary": OAUTH_SUMMARY,
            "content": OAUTH_CONTENT,
        },
        {
            "title": TAO_KHOA,
            "icon": "key-round",
            "summary": TAO_KHOA_SUMMARY,
            "content": TAO_KHOA_CONTENT,
        },
        {
            "title": CLAUDE_DESKTOP,
            "icon": "file-text",
            "summary": "Hai cách: thêm Connector rồi đăng nhập ERP (không cần Node.js), hoặc dán khóa vào tệp cấu hình qua cầu mcp-remote; các bẫy thoát hẳn, Edit Config",
            "content": f"""<h2>Nối Claude Desktop với ERP</h2>
<p>Claude Desktop là ứng dụng khung chat của Anthropic trên Windows / macOS. Có <strong>hai cách</strong> nối, chọn một:</p>
<table>
<thead><tr><th></th><th>Cách 1 — Connectors (đăng nhập ERP)</th><th>Cách 2 — Tệp cấu hình (dán khóa)</th></tr></thead>
<tbody>
<tr><td>Cần gì</td><td>Bản Claude Desktop có mục <strong>Settings ▸ Connectors</strong>. Không cần Node.js, không cần khóa.</td><td>Node.js 18 trở lên + khóa kết nối.</td></tr>
<tr><td>Cách làm</td><td>Settings ▸ Connectors ▸ <strong>Add custom connector</strong> ▸ dán địa chỉ cổng ▸ Connect ▸ trang ERP mở ra, bấm <strong>Cho phép</strong>. Đúng các bước của {ref(OAUTH, "bài Nối ChatGPT và claude.ai")} (mục claude.ai).</td><td>Sáu bước bên dưới.</td></tr>
<tr><td>Gỡ</td><td>Trang cá nhân ▸ Khóa của bạn ▸ dòng <em>Qua Claude</em> ▸ Gỡ.</td><td>Gỡ khóa ở Trang cá nhân rồi xóa khối trong tệp.</td></tr>
</tbody>
</table>
<p>Bản Claude Desktop của bạn không có mục Connectors, hoặc muốn dùng chung một khóa với Claude Code? Dùng cách 2. Cách 2 nói kỹ ở phần còn lại của bài.</p>

<h2>Cách 2 — Vì sao phải qua cầu mcp-remote</h2>
<p>Claude Desktop <strong>không nhận địa chỉ máy chủ trực tiếp</strong> trong tệp cấu hình (chỉ chạy lệnh cục bộ), nên phải đi qua một cầu nối tên <code>mcp-remote</code> chạy bằng Node.js. Nghe kỹ thuật nhưng chỉ là <strong>dán một khối chữ vào một tệp</strong>; màn AI của tôi đã soạn sẵn khối đó cho bạn.</p>

<h2>Điều kiện</h2>
<ul>
<li>Máy có <strong>Node.js 18 trở lên</strong> (bản LTS ở nodejs.org). Kiểm: mở cửa sổ lệnh gõ <code>node -v</code>, thấy số 18 trở lên là được. Chưa có thì cài, cài xong mở lại cửa sổ lệnh.</li>
<li>Đã có {ref(TAO_KHOA, "khóa kết nối")} (mức Chỉ đọc là đủ để bắt đầu).</li>
</ul>

<h2>Sáu bước</h2>
<ol>
<li>Ở màn AI của tôi, bước 1 chọn <strong>Claude Desktop</strong>, tạo khóa ở bước 2 (đoạn mẫu tự điền khóa), bấm chép đoạn cấu hình.</li>
<li>Mở Claude Desktop ▸ <strong>Settings ▸ Developer ▸ Edit Config</strong>. Claude mở thư mục chứa tệp <code>claude_desktop_config.json</code> (Windows: <code>%APPDATA%\\Claude\\claude_desktop_config.json</code>; macOS: <code>~/Library/Application Support/Claude/claude_desktop_config.json</code>). Mở tệp đó bằng Notepad hoặc trình soạn bất kỳ.</li>
<li>Dán khối dưới vào tệp. ⚠️ <strong>Tệp đã có khối <code>mcpServers</code></strong> (bạn từng nối máy chủ khác) thì <strong>chỉ thêm phần <code>{SERVER}</code> vào trong</strong>, đừng dán đè cả tệp.</li>
<li>Thay <code>{KEY}</code> bằng khóa của bạn (đoạn chép từ màn đã thay sẵn), <strong>giữ nguyên chữ <code>Bearer</code> và dấu cách</strong> phía trước.</li>
<li>Lưu tệp, rồi <strong>THOÁT HẲN Claude Desktop</strong>: bấm biểu tượng Claude dưới khay hệ thống ▸ Quit. Chỉ đóng cửa sổ là <strong>chưa</strong> thoát — Claude vẫn chạy nền với cấu hình cũ.</li>
<li>Mở lại Claude Desktop. Trong ô chat bấm biểu tượng công cụ (hình cái búa / tìm kiếm và công cụ), thấy <code>{SERVER}</code> cùng danh sách công cụ là đã nối. Quay lại ERP bấm <strong>Kiểm tra lại</strong> sau câu hỏi đầu tiên.</li>
</ol>

<h2>Khối cấu hình</h2>
<pre>{CLAUDE_DESKTOP_JSON}</pre>
<p>Địa chỉ cổng trong khối lấy đúng theo màn AI của tôi của hệ thống bạn đang dùng (môi trường thử là <code>deverp.degoholding.vn</code>).</p>

<h2>Vì sao khóa nằm trong <code>env</code> mà không nằm trong <code>args</code></h2>
<p>Trên Windows, một khoảng trắng trong <code>args</code> làm hỏng lệnh, mà <em>«Bearer khóa»</em> có khoảng trắng. Nên khóa để ở biến môi trường <code>DEGO_MCP_KEY</code>, còn <code>args</code> chỉ tham chiếu tên biến. Muốn gọn hơn: đặt biến cho cả máy bằng lệnh <code>setx DEGO_MCP_KEY "Bearer {KEY}"</code> thì bỏ được khối <code>env</code>; nhưng <code>setx</code> chỉ có hiệu lực với ứng dụng <strong>mở sau</strong> lệnh — lại phải thoát hẳn Claude Desktop.</p>

<h2>Ba lỗi hay gặp riêng của Claude Desktop</h2>
<table>
<thead><tr><th>Hiện tượng</th><th>Nguyên nhân</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Dán xong, sửa xong mà tệp cấu hình <strong>trở lại như cũ</strong></td><td>Claude Desktop <strong>ghi đè tệp</strong> khi nó đang chạy.</td><td>Thoát hẳn Claude (Quit ở khay) <em>trước khi</em> sửa tệp, hoặc luôn mở tệp qua <strong>Settings ▸ Developer ▸ Edit Config</strong> rồi thoát hẳn sau khi lưu.</td></tr>
<tr><td>Thấy <code>{SERVER}</code> nhưng báo <em>Server disconnected</em>, không có công cụ nào</td><td>Thiếu Node.js, hoặc chưa thoát hẳn, hoặc dòng <code>Authorization</code> sai (thiếu chữ Bearer, khóa chép thiếu ký tự), hoặc khóa đã hết hạn / bị gỡ.</td><td>Gõ <code>node -v</code>; xem lại dòng khóa; thoát hẳn rồi mở lại. Vẫn hỏng thì đọc log ở <code>%LOCALAPPDATA%\\Claude\\logs\\mcp-server-{SERVER}.log</code> — dòng cuối nói rõ lỗi gì, chụp gửi quản trị (che khóa).</td></tr>
<tr><td>Nối được ở máy này, máy khác không</td><td>Mỗi máy một tệp cấu hình, và khóa nên <strong>mỗi máy một khóa</strong>.</td><td>Tạo thêm khóa (tối đa 5), đặt tên theo máy.</td></tr>
</tbody>
</table>
<p>Các lỗi chung (khóa sai, quá tần suất, nhóm công cụ bị tắt): {ref(NHAT_KY, "bài Nhật ký và lỗi thường gặp")}.</p>

<h2>Dùng thử</h2>
<p>Hỏi Claude: <em>«Liệt kê các skill công ty mà bạn đọc được»</em> — phải ra danh sách cẩm nang bạn được gán. Rồi <em>«Tôi muốn mua 10 thùng giấy A4 thì làm thế nào?»</em> — Claude tự đọc skill quy trình thu mua và trả lời theo cách làm của công ty. Những gì AI làm được: {ref(CONG_CU, "bài Công cụ và skill")}.</p>""",
        },
        {
            "title": CLIENT_KHAC,
            "icon": "workflow",
            "summary": "Một lệnh cho Claude Code (mẹo PowerShell), tệp mcp.json của Cursor, settings.json của Gemini CLI — ba ứng dụng dán khóa",
            "content": f"""<h2>Nối Claude Code, Cursor và Gemini CLI với ERP</h2>
<p>Ba ứng dụng này <strong>nhận thẳng địa chỉ cổng và dòng khóa</strong>, không cần cầu nối như Claude Desktop. Mỗi ứng dụng chọn ở bước 1 màn AI của tôi là có đoạn mẫu đúng dạng, đã điền khóa.</p>

<h2>Claude Code (dòng lệnh / thẻ Code trong ứng dụng Claude)</h2>
<ol>
<li>Mở cửa sổ lệnh (Terminal, PowerShell hoặc Command Prompt).</li>
<li>Chạy lệnh dưới (thay <code>{KEY}</code> bằng khóa của bạn):</li>
</ol>
<pre>{CLAUDE_CODE_CMD}</pre>
<ol start="3">
<li>Gõ <code>claude mcp list</code> — thấy <code>{SERVER}</code> báo đã kết nối là xong.</li>
</ol>
<ul>
<li><code>--scope user</code> để dùng ở mọi thư mục; bỏ đi nếu chỉ muốn dùng trong dự án đang mở.</li>
<li>⚠️ <strong>Mẹo Windows:</strong> trong <strong>PowerShell</strong>, gõ <code>claude</code> có thể bị chặn với câu báo về <em>execution policy</em> / tệp <code>.ps1</code> (chính sách chạy script của máy). Gõ <code>claude.cmd mcp add …</code> thay cho <code>claude mcp add …</code>, hoặc mở <strong>Command Prompt</strong> (cmd) để chạy. Không cần đổi chính sách máy.</li>
</ul>

<h2>Cursor</h2>
<ol>
<li>Mở Cursor ▸ <strong>Settings ▸ MCP ▸ Add new MCP server</strong>, hoặc mở thẳng tệp <code>~/.cursor/mcp.json</code> (muốn chỉ dùng trong một dự án thì tệp <code>.cursor/mcp.json</code> trong thư mục dự án).</li>
<li>Dán khối dưới (tệp đã có <code>mcpServers</code> thì chỉ thêm phần <code>{SERVER}</code> vào trong), thay khóa, lưu.</li>
<li>Trong danh sách MCP thấy <code>{SERVER}</code> có <strong>chấm xanh</strong> là đã nối.</li>
</ol>
<pre>{CURSOR_JSON}</pre>

<h2>Gemini CLI</h2>
<ol>
<li>Mở tệp <code>~/.gemini/settings.json</code> (chưa có thì tạo).</li>
<li>Dán khối dưới, gộp vào <code>mcpServers</code> nếu đã có, thay khóa, lưu. Chú ý Gemini dùng tên ô <code>httpUrl</code>, không phải <code>url</code>.</li>
<li>Chạy <code>gemini</code>, gõ <code>/mcp</code> — thấy <code>{SERVER}</code> là đã nối.</li>
</ol>
<pre>{GEMINI_JSON}</pre>

<h2>claude.ai (trình duyệt) và ChatGPT: không dán khóa, mà đăng nhập</h2>
<p>Hai nơi này không nhận khóa dán tay; chúng tự mở trang ERP để bạn đăng nhập và bấm <strong>Cho phép</strong>. Xem {ref(OAUTH, "bài Nối ChatGPT và claude.ai bằng đăng nhập ERP")}.</p>

<h2>Sau khi nối</h2>
<p>Hỏi một câu về ERP (<em>«Tôi còn bao nhiêu ngày phép?»</em>), rồi về màn AI của tôi bấm <strong>Kiểm tra lại</strong>. Mọi lỗi chung xem {ref(NHAT_KY, "bài Nhật ký và lỗi thường gặp")}; AI làm được gì xem {ref(CONG_CU, "bài Công cụ và skill")}.</p>""",
        },
        {
            "title": CONG_CU,
            "icon": "lightbulb",
            #  Nội dung bài sở hữu ở seed_help_ai_rieng_lam_duoc_gi.py (viết lại 26/10 cho khớp prod) — sửa ở đó.
            "summary": AI_RIENG_SUMMARY,
            "content": AI_RIENG_CONTENT,
        },
        {
            "title": QUAN_TRI,
            "icon": "settings",
            "summary": "Bộ skill, soạn và xuất bản, mức bảo mật, gán ai được đọc, phát khóa cho nhân sự, ứng dụng AI đã kết nối, bộ Cẩm nang hệ thống, cấu hình",
            "content": f"""<h2>Dành cho quản trị — Kho skill AI</h2>
<p>Phân hệ <strong>Kho skill AI</strong> đứng cạnh Trợ lý AI trên màn chọn phân hệ, chỉ hiện với người có quyền <em>Kho skill AI</em> hoặc được giao <em>quản lý khóa kết nối AI của nhân sự</em>. Menu: <strong>Tổng quan · Bộ skill · Khóa nhân sự · Ứng dụng AI đã kết nối · Nhật ký sử dụng · Giới thiệu · Cấu hình</strong>.</p>

<h2>Ba khái niệm</h2>
<table>
<thead><tr><th>Thứ</th><th>Là gì</th></tr></thead>
<tbody>
<tr><td><strong>Bộ skill</strong></td><td>Nhóm cẩm nang theo chủ đề hoặc phòng (ví dụ <em>Quy trình thu mua</em>, <em>Quy định nghỉ phép</em>). Có pháp nhân, <strong>phòng chủ quản</strong>, trạng thái (Nháp / Đang dùng / Lưu trữ) và <strong>mức bảo mật</strong>.</td></tr>
<tr><td><strong>Skill</strong></td><td>Một bài cẩm nang trong bộ: <strong>tên máy</strong> (AI gọi bằng tên này), tiêu đề, <strong>câu tóm tắt cho AI</strong>, nội dung Markdown, tệp đi kèm. Nội dung xuất bản theo <strong>phiên bản</strong>, bản cũ giữ nguyên.</td></tr>
<tr><td><strong>Ai được đọc</strong></td><td>Dòng quyền gắn vào bộ hoặc vào từng skill: người · phòng ban (tick <em>kể cả phòng con</em>) · pháp nhân · vai trò · chức vụ · cấp bậc; chiều <em>Cho phép</em> hoặc <em>Không cho phép</em>; có hạn.</td></tr>
</tbody>
</table>

<h2>Tạo bộ skill</h2>
<ol>
<li>Menu <strong>Bộ skill</strong> ▸ nút <strong>Tạo bộ</strong>. Điền mã, tên, mô tả, pháp nhân, phòng chủ quản, mức bảo mật.</li>
<li>Hoặc <strong>Tải gói lên</strong>: nhận gói <code>.zip</code> / <code>.skill</code> có tệp <code>SKILL.md</code> (phần đầu tệp ghi <code>name</code>, <code>description</code>). Tải lại gói cùng tên là <strong>thay toàn bộ tệp đính kèm</strong>; thêm từng tệp thì cộng dồn.</li>
</ol>
<table>
<thead><tr><th>Mức bảo mật</th><th>AI bên ngoài nhận được</th></tr></thead>
<tbody>
<tr><td><strong>Mở</strong> (mặc định)</td><td>Nội dung và tệp đi kèm.</td></tr>
<tr><td><strong>Bảo vệ</strong></td><td>Nội dung, <strong>không</strong> tệp đi kèm. Dùng cho bộ có bảng giá, mẫu nội bộ.</td></tr>
<tr><td><strong>Khóa</strong></td><td>Chỉ tên và tóm tắt. Nội dung chỉ bot và Trợ lý AI nội bộ đọc.</td></tr>
</tbody>
</table>
<p>Nói thật như màn hình nói: <em>ai cầm khóa hợp lệ thì đọc được thứ khóa đó trả về; nhật ký cho biết ai đã đọc gì</em>. Không có chống sao chép.</p>

<h2>Soạn và xuất bản skill</h2>
<ol>
<li>Mở bộ ▸ tab <strong>Skill</strong> ▸ <strong>Thêm skill</strong>. <strong>Tên skill</strong> 2 tới 100 ký tự, chỉ chữ không dấu, số, gạch ngang, gạch dưới (ví dụ <code>bao-cao-mua-hang-thang</code>) — AI gọi bằng tên này.</li>
<li>Màn <strong>Soạn skill</strong> hai cột: trái là <strong>Nội dung (Markdown)</strong> có thanh chèn nhanh tiêu đề, chữ đậm, danh sách, bảng; phải là <strong>Xem như AI đọc</strong>.</li>
<li>Ô <strong>Tóm tắt cho AI</strong> (tối đa 500 ký tự) <strong>bắt buộc trước khi xuất bản</strong>. AI đọc câu này để quyết định có mở skill hay không, nên viết rõ <em>KHI NÀO dùng</em>: <em>«Dùng khi người dùng hỏi cách lập yêu cầu mua hàng»</em>, không viết <em>«Hướng dẫn mua hàng»</em>.</li>
<li><strong>Lưu nháp</strong> bằng nút hoặc <strong>Ctrl+S</strong>. Rời trang khi chưa lưu thì màn hỏi lại.</li>
<li><strong>Xuất bản</strong> (cần quyền duyệt): màn tự lưu nháp rồi mới xuất bản, kèm <strong>Ghi chú thay đổi</strong>. Từ lúc này AI đọc được bản vừa xuất bản; sửa tiếp là nháp mới, AI vẫn đọc bản đã xuất bản cho tới lần xuất bản sau (màn ghi <em>Nháp mới hơn bản AI đang đọc</em>).</li>
</ol>
<ul>
<li>Tab <strong>Tệp đi kèm</strong>: chỉ tệp chữ (md, txt, json, csv, yaml, xml, html…), mỗi tệp tối đa 2 MB, tên tệp chữ không dấu, không leo thư mục. Ví dụ bảng cột của mẫu báo cáo.</li>
<li>Tab <strong>Phiên bản</strong>: so hai bản cạnh nhau, tô dòng thêm và bớt.</li>
<li>Tab <strong>Ai được đọc</strong> của skill: dòng quyền riêng ở đây <strong>thay</strong> quyền của bộ (thu hẹp), không cộng thêm.</li>
<li>Viết skill như viết cho một nhân viên mới: nói rõ bước, ai làm, ô nào trên màn; dặn <em>áp dụng vào việc, không đọc lại nguyên văn</em>. Skill là <strong>mẫu báo cáo</strong> thì ghi cột nào, nhóm theo gì, tính VAT ra sao, lấy số từ báo cáo nào.</li>
</ul>

<h2>Gán ai được đọc</h2>
<p>Mở bộ ▸ tab <strong>Ai được đọc</strong> ▸ <strong>Gán thêm</strong>: chọn <em>phòng ban · chức vụ · cấp bậc · người · pháp nhân · vai trò</em>, chiều <strong>Cho phép</strong> / <strong>Không cho phép</strong>, hạn (không bắt buộc), lý do. Bốn luật:</p>
<ol>
<li>Skill đọc được khi <strong>bộ</strong> của nó đọc được <strong>và</strong> skill không bị thu hẹp.</li>
<li>Phòng ban tick <strong>kể cả phòng con</strong> thì phòng con nhận theo. Quyền tính theo hồ sơ nhân sự <strong>lúc AI gọi</strong>: đổi phòng là đổi skill ngay.</li>
<li><strong>Không cho phép thắng Cho phép</strong> (dòng không cho phép tô đỏ).</li>
<li>Chỉ skill <em>Đang dùng</em> của bộ <em>Đang dùng</em> lộ ra AI bên ngoài. Nháp chỉ người soạn thấy.</li>
</ol>
<p>Thu hồi một dòng quyền có hiệu lực trong khoảng một phút (bộ đệm quyền).</p>

<h2>Khóa nhân sự: phát hộ và thu hồi</h2>
<p>Menu <strong>Khóa nhân sự</strong> liệt kê mọi khóa kết nối trong phạm vi bạn quản lý: người, phòng, tên khóa, mức, hạn, lần dùng cuối, trạng thái (<em>Chờ nhận / Đang dùng / Hết hạn / Đã thu hồi</em>). Lọc theo phòng ban và trạng thái.</p>
<ul>
<li><strong>Phát khóa</strong>: cho một hay nhiều người (chọn theo danh sách nhân sự) hoặc <strong>cả phòng</strong>, tối đa <strong>50 người một lượt</strong>, chọn hạn 7 / 30 / 90 / 180 / 365 ngày. Khóa phát hộ <strong>luôn là Chỉ đọc</strong>; khóa Được ghi chỉ người dùng tự tạo. Người nhận có <strong>chuông</strong>, vào Trang cá nhân bấm <strong>Nhận khóa</strong> mới thấy khóa — bạn không thấy khóa của họ. Có người ngoài phạm vi thì <strong>từ chối cả lượt</strong>; người đã đủ 5 khóa, chưa có tài khoản hoặc tài khoản đã khóa thì bỏ qua kèm lý do.</li>
<li><strong>Thu hồi</strong>: tick chọn rồi bấm <strong>Thu hồi</strong>; hộp xác nhận chỉ đếm khóa còn hiệu lực. Thu hồi được từng khóa, mọi khóa của một người, hoặc cả một lượt phát. Dòng thu hồi giữ lại để đối soát; AI gọi bằng khóa đó vẫn vào nhật ký với trạng thái <em>Bị từ chối</em>.</li>
</ul>

<h2>Ứng dụng AI đã kết nối (người quản lý trợ lý AI)</h2>
<p>Khi nhân sự nối ChatGPT, claude.ai hay Claude Desktop bằng cách {ref(OAUTH, "đăng nhập ERP")}, ứng dụng đó <strong>tự đăng ký</strong> với cổng. Màn này liệt kê mọi ứng dụng đã đăng ký: <strong>tên tự khai</strong> kèm sáu ký tự cuối mã ứng dụng, <strong>nơi quay về</strong> (tên miền), số <strong>kết nối đang sống</strong>, dùng lần cuối, ngày đăng ký; hai cột IP đăng ký và cách xác thực ẩn mặc định (menu Cột).</p>
<ul>
<li>⚠️ <strong>Tên là do ứng dụng tự khai, đừng tin.</strong> Nhìn cột nơi quay về: không thuộc ứng dụng AI quen (chatgpt.com, openai.com, claude.ai, anthropic.com, claude.com, máy cục bộ) thì ô tô đỏ kèm nhãn <strong>Host lạ</strong>, dòng tóm tắt trên bảng đếm số host lạ. Host lạ mà có kết nối đang sống nghĩa là đã có người bấm Cho phép cho một ứng dụng không rõ — hỏi người đó, rồi xóa.</li>
<li><strong>Xóa ứng dụng</strong> (cần quyền ghi quản lý bot AI): hộp xác nhận nêu tên, nơi quay về và số kết nối sẽ bị cắt. <strong>Xóa là cắt mọi kết nối của ứng dụng này ngay</strong>, cả mã làm mới; người đang dùng phải bấm Cho phép lại từ đầu nếu muốn nối tiếp. Dòng khóa tương ứng ở Khóa nhân sự chuyển sang Đã thu hồi.</li>
<li>Ứng dụng quá 7 ngày không có kết nối sống và không dùng thì hệ tự dọn; màn này chủ yếu để xem và xóa tay ứng dụng lạ.</li>
</ul>

<h2>Bộ Cẩm nang hệ thống</h2>
<p>Hệ gieo sẵn một bộ tên <strong>Cẩm nang hệ thống</strong> (mã <code>SYS-HANDBOOK</code>, mức Mở, Đang dùng) gồm <strong>7 skill</strong>: quy trình thu mua · văn thư, văn bản · dự án, công việc · nghỉ phép · đặt phòng họp · hồ sơ nhân sự · hệ thống công việc nhà máy (kèm 11 tệp gốc nhà máy làm tệp đi kèm). Đây là các gói tri thức trước nằm cứng trong mã của Trợ lý AI, nay chuyển hẳn vào kho:</p>
<ul>
<li>Trợ lý AI web, bot Telegram và AI riêng của nhân sự <strong>đọc cùng một bản</strong>. Quản trị sửa skill trên màn Bộ skill rồi <strong>Xuất bản</strong> là lượt hỏi kế tiếp AI đã dùng bản mới; không còn phải sửa mã.</li>
<li>Hệ chỉ gieo khi chưa có bộ mã này, <strong>không ghi đè</strong> thứ quản trị đã sửa.</li>
<li>Bộ được gán sẵn cho mọi pháp nhân có lúc gieo; <strong>pháp nhân tạo sau</strong> phải vào bộ ▸ tab Ai được đọc gán tay.</li>
</ul>

<h2>Cấu hình (người quản lý trợ lý AI)</h2>
<ul>
<li><strong>Nhóm công cụ qua MCP</strong>: bật / tắt từng nhóm (mỗi nhóm ghi số và tên công cụ). Mặc định bật: Việc của tôi, Nghỉ phép, Danh bạ, Báo cáo, Kho skill; các nhóm Thu mua, Công nợ và thanh toán, Văn thư, Soạn việc, Tra cứu thị trường, Lịch và Drive, Sổ nhớ mặc định tắt. Tắt nhóm là công cụ biến khỏi mọi ứng dụng AI đã nối.</li>
<li><strong>Giới hạn</strong>: lượt mỗi phút theo khóa (mặc định 120) và theo IP (600), số khóa sai mỗi phút theo IP (30), số dòng dữ liệu mỗi phút (3.000), số ngày giữ nhật ký (180). Ô trống không được hiểu là 0; ngoài dải thì màn chặn lưu.</li>
<li><strong>Câu dặn thêm cho AI</strong> (tối đa 1.000 ký tự): nối sau câu dặn mặc định của cổng, áp cho mọi khóa.</li>
</ul>

<h2>Quyền và vai trò</h2>
<table>
<thead><tr><th>Khóa quyền</th><th>Mở gì</th></tr></thead>
<tbody>
<tr><td><code>ai_skill</code> (Kho skill AI)</td><td>Đọc · tạo · ghi · xóa bộ và skill; <strong>duyệt</strong> = xuất bản. Phạm vi theo pháp nhân và <strong>phòng chủ quản</strong> của bộ: trưởng phòng chỉ soạn bộ của phòng mình.</td></tr>
<tr><td><code>ai_mcp_key_admin</code></td><td>Màn Khóa nhân sự: đọc · phát hộ · thu hồi. Phạm vi theo hồ sơ của <strong>chủ khóa</strong>.</td></tr>
<tr><td>Quản lý bot AI (<code>agent_group</code>)</td><td>Tổng quan, Nhật ký sử dụng của người khác, Ứng dụng AI đã kết nối, Cấu hình.</td></tr>
</tbody>
</table>
<p>Hai vai trò mẫu: <strong>Quản trị kho skill AI</strong> (toàn công ty) và <strong>Biên tập skill AI phòng ban</strong> (phòng mình). Hệ đang chạy không tự nhận vai trò mới — vào <strong>Nhân sự ▸ Phân quyền tài khoản</strong> tick tay. Màn <strong>Tổng quan</strong>: số bộ và skill, người đã nối AI, lượt gọi 7 ngày so với 7 ngày trước, số từ chối và lỗi, biểu đồ theo ngày, bảng xếp hạng công cụ, người, skill, khóa sắp hết hạn.</p>

<h2>Thứ tự dựng</h2>
<ol>
<li>Tick quyền cho hai vai trò mẫu; gán vai trò cho người soạn.</li>
<li>Tạo bộ cho một phòng, soạn 2 tới 3 skill từ quy trình đang có (Help Center, tệp Word), viết kỹ câu tóm tắt, xuất bản.</li>
<li>Gán <em>Ai được đọc</em>: phòng đó, tick kể cả phòng con.</li>
<li>Phát khóa chỉ đọc cho vài người thử; họ nối theo {ref(OAUTH, "bài ChatGPT, claude.ai")} hoặc {ref(CLAUDE_DESKTOP, "bài Claude Desktop")}.</li>
<li>Xem {ref(NHAT_KY, "Nhật ký sử dụng")} sau một tuần: skill nào được đọc, câu nào bị từ chối, rồi mới mở rộng nhóm công cụ.</li>
</ol>""",
        },
        {
            "title": NHAT_KY,
            "icon": "help",
            "summary": "Đọc nhật ký lượt gọi, tra câu từ chối: khóa sai, hết hạn, chưa nhận, quá tần suất, nhóm tắt, Server disconnected",
            "content": f"""<h2>Nhật ký lượt gọi của AI riêng và lỗi thường gặp khi nối</h2>

<h2>Nhật ký ở đâu</h2>
<table>
<thead><tr><th>Ai</th><th>Xem ở</th><th>Thấy gì</th></tr></thead>
<tbody>
<tr><td>Mọi người</td><td>Trang cá nhân ▸ Kết nối AI riêng ▸ khối <strong>20 lượt AI tra cứu gần nhất</strong></td><td>Lượt của chính mình: lúc nào, ứng dụng nào, công cụ gì, thành công hay bị từ chối, lý do.</td></tr>
<tr><td>Quản trị</td><td>Kho skill AI ▸ <strong>Nhật ký sử dụng</strong></td><td>Mọi lượt trong phạm vi: người, phòng, khóa, ứng dụng, công cụ, skill được đọc, trạng thái, thời gian xử lý, IP. Lọc theo ngày, công cụ, trạng thái; <strong>Xuất CSV (trang hiện tại)</strong>.</td></tr>
</tbody>
</table>
<p>Mỗi lượt AI gọi vào ERP là một dòng, <strong>kể cả lượt bị từ chối</strong> và lượt khóa sai (lượt sai hàng loạt chỉ ghi 10 dòng đầu mỗi phút). Nhật ký giữ 180 ngày rồi gom thành số đếm theo ngày. Ba trạng thái: <strong>Thành công · Bị từ chối · Lỗi</strong>.</p>
<p>Thấy lượt gọi lúc bạn không ngồi máy, hoặc từ ứng dụng bạn không dùng: <strong>gỡ khóa ngay</strong> ở màn AI của tôi, rồi báo quản trị.</p>

<h2>Ứng dụng không thấy công cụ nào / báo Server disconnected</h2>
<table>
<thead><tr><th>Kiểm</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td>Dòng khóa trong cấu hình</td><td>Phải là <code>Bearer</code> + một dấu cách + khóa <code>dego_mcp_…</code> nguyên vẹn. Thiếu chữ Bearer, thừa dấu ngoặc, chép thiếu ký tự cuối đều hỏng.</td></tr>
<tr><td>Khóa còn hiệu lực?</td><td>Màn AI của tôi, bước 2: khóa hết hạn hay đã gỡ thì tạo khóa mới, dán lại. Khóa phát hộ phải bấm <strong>Nhận khóa</strong> trước.</td></tr>
<tr><td>Claude Desktop</td><td><code>node -v</code> ra 18 trở lên; đã <strong>thoát hẳn</strong> (Quit ở khay) rồi mở lại; tệp cấu hình không bị ghi đè. Log: <code>%LOCALAPPDATA%\\Claude\\logs\\mcp-server-{SERVER}.log</code>. Chi tiết ở {ref(CLAUDE_DESKTOP, "bài Claude Desktop")}.</td></tr>
<tr><td>Địa chỉ cổng</td><td>Đúng địa chỉ hiện trên màn AI của tôi, kết thúc bằng <code>/api/mcp</code>. Máy phải vào được ERP bằng trình duyệt.</td></tr>
<tr><td>Vẫn hỏng</td><td>Mở Nhật ký (của mình hoặc nhờ quản trị): <strong>không có dòng nào</strong> = ứng dụng chưa gọi tới ERP, lỗi ở máy bạn; <strong>có dòng Bị từ chối</strong> = đọc lý do ở bảng dưới.</td></tr>
</tbody>
</table>

<h2>Câu từ chối và nghĩa của nó</h2>
<table>
<thead><tr><th>Lý do trong nhật ký / câu AI nhận</th><th>Nghĩa là</th><th>Làm gì</th></tr></thead>
<tbody>
<tr><td><em>Khóa sai</em> · <em>Khóa MCP không hợp lệ hoặc đã hết hạn</em></td><td>Khóa chép sai, hoặc không tồn tại. Ứng dụng chỉ nhận một câu chung; lý do thật nằm ở nhật ký.</td><td>Chép lại khóa từ đoạn mẫu, hoặc tạo khóa mới.</td></tr>
<tr><td><em>Khóa đã hết hạn</em></td><td>Quá 90 ngày (hoặc hạn quản trị chọn khi phát).</td><td>Tạo khóa mới, dán lại.</td></tr>
<tr><td><em>Khóa đã bị thu hồi</em></td><td>Bạn gỡ, hoặc quản trị thu hồi.</td><td>Hỏi quản trị nếu không phải bạn gỡ; tạo khóa mới.</td></tr>
<tr><td><em>Khóa phát hộ chưa được chủ khóa nhận</em></td><td>Bạn dán khóa người khác đưa, hoặc chưa bấm Nhận khóa.</td><td>Vào Trang cá nhân bấm <strong>Nhận khóa</strong> — khóa chỉ hiện cho chính bạn.</td></tr>
<tr><td><em>Khóa đang tắt</em></td><td>Bạn (hoặc chính bạn ở máy khác) đã bấm tạm tắt khóa / kết nối này.</td><td>Trang cá nhân ▸ Khóa của bạn ▸ bật lại. Không cần tạo khóa mới.</td></tr>
<tr><td>Ứng dụng báo <em>invalid_grant</em> / mất kết nối sau khi đang dùng bình thường</td><td>Kết nối qua đăng nhập hết 90 ngày, bị gỡ, tạm tắt, hoặc quản trị xóa ứng dụng.</td><td>Bấm Connect lại trong ứng dụng; xem {ref(OAUTH, "bài Nối ChatGPT và claude.ai")}.</td></tr>
<tr><td><em>Quá tần suất (khóa)</em> · <em>Quá tần suất: tối đa n lượt / phút…</em></td><td>Một khóa gọi hơn 120 lượt trong một phút (AI đang lặp, hoặc nhiều máy dùng chung một khóa).</td><td>Đợi một phút. Mỗi máy nên một khóa riêng.</td></tr>
<tr><td><em>Quá tần suất (IP)</em> · <em>Quá tần suất (khóa sai liên tục)</em></td><td>Cả văn phòng chung một địa chỉ mạng vượt 600 lượt / phút, hoặc có máy đang thử khóa sai liên tục (30 lần / phút).</td><td>Đợi một phút; báo quản trị nếu lặp lại — có thể là máy ai đó cấu hình sai.</td></tr>
<tr><td>AI báo <em>công cụ bị từ chối</em> kèm <strong>tên nhóm</strong></td><td>Quản trị tắt nhóm đó qua cổng (ví dụ Công nợ).</td><td>Không phải lỗi. Cần thì xin quản trị bật nhóm ở Cấu hình.</td></tr>
<tr><td><em>Khóa này chỉ đọc; tạo phiếu cần khóa «được ghi»</em></td><td>Nhờ AI tạo phiếu bằng khóa Chỉ đọc.</td><td>Tạo khóa mức <strong>Được ghi</strong> ở Trang cá nhân, dán vào ứng dụng.</td></tr>
<tr><td>AI báo <em>bị từ chối, thiếu quyền…</em> khi hỏi báo cáo hay phiếu</td><td>Phạm vi dữ liệu của bạn trên ERP, giống như không thấy trên web.</td><td>Xin quản trị mở quyền / giao báo cáo; không phải lỗi kết nối.</td></tr>
<tr><td>AI báo <em>không có skill đó</em></td><td>Skill chưa xuất bản, hoặc không gán cho bạn — hệ cố ý trả cùng câu với skill không tồn tại.</td><td>Hỏi người soạn skill của phòng.</td></tr>
<tr><td>AI báo <em>bộ ở mức Bảo vệ, không mở tệp</em></td><td>Quản trị đặt mức Bảo vệ cho bộ đó.</td><td>Đúng ý thiết kế; nội dung skill vẫn đọc được.</td></tr>
<tr><td>Đọc danh sách dài, AI báo <em>còn nữa</em> hoặc <em>đã hết ngân sách dòng</em></td><td>Mỗi lượt tối đa vài trang; mỗi phút tối đa 3.000 dòng dữ liệu.</td><td>Bảo AI lọc hẹp hơn (theo tháng, theo nhà cung cấp) thay vì kéo hết.</td></tr>
</tbody>
</table>

<h2>Không phải lỗi, nhưng hay bị tưởng là lỗi</h2>
<ul>
<li><strong>Số công cụ khác nhau giữa hai người</strong> — khóa Chỉ đọc thấy ít hơn khóa Được ghi, và nhóm công cụ do quản trị bật.</li>
<li><strong>AI trả lời không theo quy trình công ty</strong> — AI chưa mở skill. Nhắc: <em>«Hãy xem cẩm nang công ty trước khi trả lời»</em>; vẫn không có thì bạn chưa được gán skill đó.</li>
<li><strong>Kiểm tra kết nối báo chưa thấy</strong> dù ứng dụng đã liệt kê công cụ — liệt kê công cụ là lượt <em>khởi tạo</em>; hỏi một câu để có lượt gọi thật rồi bấm <strong>Kiểm tra lại</strong>.</li>
<li><strong>Sửa skill mà AI vẫn trả lời như cũ</strong> — chưa bấm <strong>Xuất bản</strong>, AI chỉ đọc bản đã xuất bản.</li>
<li><strong>Nhật ký có dòng <em>key/reveal</em> từ ứng dụng ERP web</strong> — đó là bạn vừa bấm xem lại khóa, không phải ai đó lấy khóa qua AI.</li>
</ul>

<h2>Báo lỗi hệ thống</h2>
<p>Nhờ chính AI: <em>«Báo lỗi: nối ERP bị từ chối lúc 9:10, màn AI của tôi»</em> — công cụ báo lỗi luôn mở kể cả khóa Chỉ đọc, tạo phiếu hỗ trợ gắn bộ phận phụ trách. Hoặc lập phiếu ở Trang cá nhân ▸ <strong>Yêu cầu hỗ trợ</strong>, kèm giờ thử để quản trị tra đúng dòng nhật ký. <strong>Che khóa</strong> trước khi chụp màn hình.</p>""",
        },
    ],
}


def collect_descendants(db, root_id):
    """Trả [(id, độ sâu)] của cả cây, gồm chính gốc."""
    found = [(root_id, 0)]
    frontier = [(root_id, 0)]
    while frontier:
        nid, depth = frontier.pop()
        for (cid,) in db.query(HelpArticle.id).filter(HelpArticle.parent_id == nid).all():
            found.append((cid, depth + 1))
            frontier.append((cid, depth + 1))
    return found


def delete_subtree(db, root_id):
    nodes = collect_descendants(db, root_id)
    #  Xóa RAW theo thứ tự sâu-trước: FK tự tham chiếu parent_id KHÔNG cascade.
    for nid, _ in sorted(nodes, key=lambda x: x[1], reverse=True):
        db.execute(text("DELETE FROM tab_help_home_item WHERE article_id = :id"), {"id": nid})
        db.execute(text("DELETE FROM tab_help_article WHERE id = :id"), {"id": nid})
    db.flush()
    return len(nodes)


def insert_node(db, node, parent_id, order):
    art = HelpArticle(
        parent_id=parent_id,
        title=node["title"],
        content=node.get("content", ""),
        summary=node.get("summary"),
        icon=node.get("icon"),
        sort_order=order,
    )
    db.add(art)
    db.flush()
    count = 1
    for i, child in enumerate(node.get("children", [])):
        child_count, _ = insert_node(db, child, art.id, i)
        count += child_count
    return count, art.id


def attach_home_card(db, article_id):
    """Gắn thẻ phân hệ vào khung "Các Phân hệ" trang chủ nếu chưa có."""
    section = db.query(HelpHomeSection).filter(HelpHomeSection.key == "categories").first()
    if section is None:
        print("Không thấy khung categories — bỏ qua gắn thẻ trang chủ.")
        return
    existing = (
        db.query(HelpHomeItem)
        .filter(HelpHomeItem.section_id == section.id, HelpHomeItem.article_id == article_id)
        .first()
    )
    if existing is not None:
        return
    max_order = (
        db.query(HelpHomeItem.sort_order)
        .filter(HelpHomeItem.section_id == section.id)
        .order_by(HelpHomeItem.sort_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0
    db.add(HelpHomeItem(section_id=section.id, article_id=article_id, sort_order=next_order))
    print(f"Đã gắn thẻ phân hệ vào trang chủ (sort_order={next_order}).")


def check_unique_titles(db):
    """Tiêu đề trùng bài khác (ngoài cây này) là trùng slug trên portal — chặn trước khi ghi."""
    titles = [TREE["title"]] + [c["title"] for c in TREE["children"]]
    assert len(titles) == 8, titles
    own_root = (
        db.query(HelpArticle.id)
        .filter(HelpArticle.title == ROOT_TITLE, HelpArticle.parent_id.is_(None))
        .first()
    )
    own_ids = {nid for nid, _ in collect_descendants(db, own_root[0])} if own_root else set()
    clash = [
        a.title for a in db.query(HelpArticle).filter(HelpArticle.title.in_(titles)).all() if a.id not in own_ids
    ]
    if clash:
        raise SystemExit(f"Tiêu đề đã có bài khác dùng, đổi tiêu đề trước: {clash}")


def main():
    db = SessionLocal()
    try:
        check_unique_titles(db)
        old = (
            db.query(HelpArticle)
            .filter(HelpArticle.title == ROOT_TITLE, HelpArticle.parent_id.is_(None))
            .first()
        )
        if old is not None:
            removed = delete_subtree(db, old.id)
            print(f"Đã xóa cây cũ: {removed} bài (gốc id={old.id}).")

        max_order = (
            db.query(HelpArticle.sort_order)
            .filter(HelpArticle.parent_id.is_(None))
            .order_by(HelpArticle.sort_order.desc())
            .first()
        )
        next_order = (max_order[0] + 1) if max_order and max_order[0] is not None else 0

        total, root_id = insert_node(db, TREE, None, next_order)
        attach_home_card(db, root_id)
        db.commit()
        print(f"Đã dựng cây Kết nối AI riêng + Kho skill AI: {total} bài (gốc id={root_id}, sort_order={next_order}).")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
