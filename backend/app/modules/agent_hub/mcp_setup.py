"""Đoạn cấu hình nối ứng dụng AI với cổng MCP của ERP — cho màn «AI của tôi» (ai-CR-213, K6 doc/erp/21 §6.2 G8).

Mỗi ứng dụng một khuôn riêng, viết ĐÚNG cách ứng dụng đó nhận:
- Claude Desktop KHÔNG nhận `url` + `headers` trong `claude_desktop_config.json` (chỉ chạy lệnh cục bộ) → dùng cầu
  `npx -y mcp-remote <url> --header Authorization:${DEGO_MCP_AUTH}`, khóa để trong `env` (khoảng trắng trong `args`
  làm hỏng lệnh trên Windows, nên `Bearer …` nằm ở biến môi trường). Cần Node.js 18+.
- Claude Code: lệnh `claude mcp add --transport http … --header`.
- Cursor: `~/.cursor/mcp.json` với `url` + `headers`. Gemini CLI: `~/.gemini/settings.json` với `httpUrl` + `headers`.
- claude.ai (web) và ChatGPT: kết nối tùy chỉnh của hai nơi này chỉ đăng nhập bằng OAuth, không nhận khóa dạng header
  → `supported = false`, nói rõ và gợi ý dùng ứng dụng khác. Xem lại khi hai nơi đó đổi.

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
                    "args": ["-y", "mcp-remote", url, "--header", "Authorization:${DEGO_MCP_AUTH}"],
                    "env": {"DEGO_MCP_AUTH": bearer}}}}),
                "steps": ["Cài Node.js bản LTS nếu máy chưa có (mở cửa sổ lệnh gõ `node -v` thấy số 18 trở lên là được).",
                          "Mở Claude Desktop → Settings → Developer → Edit Config.",
                          f"Dán đoạn dưới vào tệp; tệp đã có `mcpServers` thì chỉ thêm khối `{SERVER_NAME}` vào trong.",
                          f"Thay {KEY_PLACEHOLDER} bằng khóa của bạn, giữ nguyên chữ `Bearer ` phía trước.",
                          "Lưu tệp, THOÁT HẲN Claude Desktop (cả biểu tượng dưới khay) rồi mở lại.",
                          f"Trong ô chat bấm biểu tượng công cụ, thấy `{SERVER_NAME}` là đã nối."],
                "note": "Claude Desktop không nhận địa chỉ máy chủ trực tiếp trong tệp cấu hình — phải đi qua cầu "
                        "mcp-remote như đoạn dưới."}
    if client == "claude_code":
        return {"client": client, "label": "Claude Code", "supported": True, "format": "shell",
                "snippet": f'claude mcp add --transport http --scope user {SERVER_NAME} {url} '
                           f'--header "Authorization: {bearer}"',
                "steps": ["Mở cửa sổ lệnh (terminal).", f"Thay {KEY_PLACEHOLDER} trong lệnh dưới bằng khóa của bạn rồi chạy.",
                          f"Gõ `claude mcp list` — thấy `{SERVER_NAME}` báo đã kết nối là xong."],
                "note": "`--scope user` để dùng ở mọi thư mục; bỏ đi nếu chỉ muốn dùng trong dự án hiện tại."}
    if client == "cursor":
        return {"client": client, "label": "Cursor", "supported": True, "format": "json",
                "files": {"all": "~/.cursor/mcp.json (hoặc .cursor/mcp.json trong dự án)"},
                "snippet": _json({"mcpServers": {SERVER_NAME: {"url": url, "headers": {"Authorization": bearer}}}}),
                "steps": ["Mở Cursor → Settings → MCP → Add new MCP server (hoặc mở thẳng tệp mcp.json).",
                          f"Dán đoạn dưới, thay {KEY_PLACEHOLDER} bằng khóa của bạn, lưu.",
                          f"Trong danh sách MCP thấy `{SERVER_NAME}` có chấm xanh là đã nối."]}
    if client == "gemini_cli":
        return {"client": client, "label": "Gemini CLI", "supported": True, "format": "json",
                "files": {"all": "~/.gemini/settings.json"},
                "snippet": _json({"mcpServers": {SERVER_NAME: {"httpUrl": url, "headers": {"Authorization": bearer}}}}),
                "steps": ["Mở tệp ~/.gemini/settings.json (chưa có thì tạo).",
                          f"Dán đoạn dưới (gộp vào `mcpServers` nếu đã có), thay {KEY_PLACEHOLDER} bằng khóa, lưu.",
                          f"Chạy `gemini`, gõ `/mcp` — thấy `{SERVER_NAME}` là đã nối."]}
    if client == "claude_ai":
        return {"client": client, "label": "claude.ai (trình duyệt)", "supported": False, "format": "",
                "snippet": "", "steps": [],
                "note": "Kết nối tùy chỉnh trên claude.ai chỉ đăng nhập bằng OAuth, chưa nhận khóa ERP. Dùng Claude "
                        "Desktop (cùng tài khoản claude.ai) để nối với ERP."}
    if client == "chatgpt":
        return {"client": client, "label": "ChatGPT", "supported": False, "format": "", "snippet": "", "steps": [],
                "note": "Kết nối của ChatGPT chỉ đăng nhập bằng OAuth hoặc không xác thực, chưa nhận khóa ERP. Tạm dùng "
                        "Claude Desktop, Cursor hoặc Gemini CLI."}
    return None


def catalog() -> list[dict]:
    return [{k: v for k, v in build(c).items() if k in ("client", "label", "supported")} for c in CLIENTS]
