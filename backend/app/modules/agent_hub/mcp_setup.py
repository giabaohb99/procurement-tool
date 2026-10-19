"""Đoạn cấu hình nối ứng dụng AI với cổng MCP của ERP — cho màn «AI của tôi» (ai-CR-213, K6 doc/erp/21 §6.2 G8).

Mỗi ứng dụng một khuôn riêng, viết ĐÚNG cách ứng dụng đó nhận:
- Claude Desktop KHÔNG nhận `url` + `headers` trong `claude_desktop_config.json` (chỉ chạy lệnh cục bộ) → dùng cầu
  `npx -y mcp-remote <url> --header Authorization:${DEGO_MCP_KEY}`, khóa để trong `env` (khoảng trắng trong `args`
  làm hỏng lệnh trên Windows, nên `Bearer …` nằm ở biến môi trường). Cần Node.js 18+.
- Claude Code: lệnh `claude mcp add --transport http … --header`.
- Cursor: `~/.cursor/mcp.json` với `url` + `headers`. Gemini CLI: `~/.gemini/settings.json` với `httpUrl` + `headers`.
- claude.ai (web) và ChatGPT: kết nối tùy chỉnh đăng nhập bằng OAuth → từ ai-CR-218 ERP là máy chủ cấp quyền, nên
  `auth = "oauth"`, đoạn «cấu hình» chỉ là địa chỉ cổng; người dùng đăng nhập ERP và bấm Cho phép. Các ứng dụng còn lại
  `auth = "key"` (dán khóa).

Khóa thật không bao giờ nằm ở đây: đoạn cấu hình mang chỗ giữ `KEY_PLACEHOLDER`, màn hình tự thay bằng khóa vừa hiện.
"""
from __future__ import annotations

import json

from app.core.config import settings

KEY_PLACEHOLDER = "<KHÓA_CỦA_BẠN>"
SERVER_NAME = "dego-erp"
CLIENTS = ("claude_desktop", "claude_code", "cursor", "gemini_cli", "claude_ai", "chatgpt")


def endpoint() -> str:
    return f"{(settings.AGENT_ERP_URL or '').rstrip('/')}/api/mcp"


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def build(client: str) -> dict | None:
    url = endpoint()
    bearer = f"Bearer {KEY_PLACEHOLDER}"
    if client == "claude_desktop":
        return {"client": client, "label": "Claude Desktop", "supported": True, "format": "json",
                "files": {"windows": r"%APPDATA%\Claude\claude_desktop_config.json",
                          "macos": "~/Library/Application Support/Claude/claude_desktop_config.json"},
                "requires": ["Node.js 18 trở lên (nodejs.org, bản LTS)"],
                "snippet": _json({"mcpServers": {SERVER_NAME: {
                    "command": "npx",
                    "args": ["-y", "mcp-remote", url, "--header", "Authorization:${DEGO_MCP_KEY}"],
                    "env": {"DEGO_MCP_KEY": bearer}}}}),
                "steps": ["Cài Node.js bản LTS nếu máy chưa có (mở cửa sổ lệnh gõ `node -v` thấy số 18 trở lên là được).",
                          "Mở Claude Desktop → Settings → Developer → Edit Config.",
                          f"Dán đoạn dưới vào tệp; tệp đã có `mcpServers` thì chỉ thêm khối `{SERVER_NAME}` vào trong.",
                          f"Thay {KEY_PLACEHOLDER} bằng khóa của bạn, giữ nguyên chữ `Bearer ` phía trước.",
                          "Lưu tệp, THOÁT HẲN Claude Desktop (cả biểu tượng dưới khay) rồi mở lại.",
                          f"Trong ô chat bấm biểu tượng công cụ, thấy `{SERVER_NAME}` là đã nối."],
                "auth": "key",
                "note": "Cách khác không cần Node.js: Claude Desktop → Settings → Connectors → Add custom connector, dán "
                        "địa chỉ cổng rồi đăng nhập ERP (như claude.ai, xem mục claude.ai). Còn nếu dùng tệp cấu hình thì "
                        "Claude Desktop không nhận địa chỉ máy chủ trực tiếp — phải đi qua cầu "
                        "mcp-remote như đoạn dưới. Đã đặt biến DEGO_MCP_KEY cho cả máy (Windows: setx DEGO_MCP_KEY "
                        "\"Bearer <khóa>\") thì bỏ được khối env."}
    if client == "claude_code":
        return {"client": client, "label": "Claude Code", "supported": True, "auth": "key", "format": "shell",
                "snippet": f'claude mcp add --transport http --scope user {SERVER_NAME} {url} '
                           f'--header "Authorization: {bearer}"',
                "steps": ["Mở cửa sổ lệnh (terminal).", f"Thay {KEY_PLACEHOLDER} trong lệnh dưới bằng khóa của bạn rồi chạy.",
                          f"Gõ `claude mcp list` — thấy `{SERVER_NAME}` báo đã kết nối là xong."],
                "note": "`--scope user` để dùng ở mọi thư mục; bỏ đi nếu chỉ muốn dùng trong dự án hiện tại."}
    if client == "cursor":
        return {"client": client, "label": "Cursor", "supported": True, "auth": "key", "format": "json",
                "files": {"all": "~/.cursor/mcp.json (hoặc .cursor/mcp.json trong dự án)"},
                "snippet": _json({"mcpServers": {SERVER_NAME: {"url": url, "headers": {"Authorization": bearer}}}}),
                "steps": ["Mở Cursor → Settings → MCP → Add new MCP server (hoặc mở thẳng tệp mcp.json).",
                          f"Dán đoạn dưới, thay {KEY_PLACEHOLDER} bằng khóa của bạn, lưu.",
                          f"Trong danh sách MCP thấy `{SERVER_NAME}` có chấm xanh là đã nối."]}
    if client == "gemini_cli":
        return {"client": client, "label": "Gemini CLI", "supported": True, "auth": "key", "format": "json",
                "files": {"all": "~/.gemini/settings.json"},
                "snippet": _json({"mcpServers": {SERVER_NAME: {"httpUrl": url, "headers": {"Authorization": bearer}}}}),
                "steps": ["Mở tệp ~/.gemini/settings.json (chưa có thì tạo).",
                          f"Dán đoạn dưới (gộp vào `mcpServers` nếu đã có), thay {KEY_PLACEHOLDER} bằng khóa, lưu.",
                          f"Chạy `gemini`, gõ `/mcp` — thấy `{SERVER_NAME}` là đã nối."]}
    if client == "claude_ai":
        #  ai-CR-218 (K14): kết nối tùy chỉnh của claude.ai đăng nhập bằng OAuth — ERP nay là máy chủ cấp quyền.
        return {"client": client, "label": "claude.ai (trình duyệt)", "supported": True, "auth": "oauth", "format": "url",
                "snippet": url,
                "steps": ["Mở claude.ai → Settings (Cài đặt) → Connectors → Add custom connector.",
                          "Đặt tên (vd DEGO ERP), dán địa chỉ ở dưới vào ô Remote MCP server URL → Add.",
                          "Bấm Connect: trang ERP mở ra — đăng nhập ERP nếu chưa, chọn mức Chỉ đọc hoặc Được ghi, bấm "
                          "Cho phép.",
                          "Quay lại claude.ai, trong ô chat bật DEGO ERP ở nút công cụ là dùng được."],
                "note": "Không cần khóa: claude.ai đăng nhập ERP thay bạn. Gói Team / Enterprise thì chủ tổ chức thêm kết "
                        "nối trong Organization settings trước. Kết nối dùng 90 ngày, hết thì bấm Connect lại. Gỡ ở Trang cá "
                        "nhân → Khóa AI (dòng Qua Claude)."}
    if client == "chatgpt":
        return {"client": client, "label": "ChatGPT", "supported": True, "auth": "oauth", "format": "url", "snippet": url,
                "steps": ["Mở ChatGPT → Settings (Cài đặt) → Apps & Connectors → Advanced settings → bật Developer mode.",
                          "Quay lại Apps & Connectors → Create (Tạo): đặt tên DEGO ERP, dán địa chỉ ở dưới vào ô MCP Server "
                          "URL, Authentication chọn OAuth, tick tin tưởng ứng dụng → Create.",
                          "Trang ERP mở ra — đăng nhập ERP nếu chưa, chọn mức Chỉ đọc hoặc Được ghi, bấm Cho phép.",
                          "Trong ô chat chọn DEGO ERP ở nút + (Developer mode) rồi hỏi như bình thường."],
                "note": "Không cần khóa: ChatGPT đăng nhập ERP thay bạn. Tên mục trong Cài đặt có thể đổi theo phiên bản "
                        "ChatGPT. Kết nối dùng 90 ngày, hết thì kết nối lại. Gỡ ở Trang cá nhân → Khóa AI (dòng Qua "
                        "ChatGPT)."}
    return None


def catalog() -> list[dict]:
    return [{k: v for k, v in build(c).items() if k in ("client", "label", "supported", "auth")} for c in CLIENTS]
