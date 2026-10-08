"""ERP gọi sang DỊCH VỤ AI cho việc nội bộ (ai-CR-119) — chiều ngược của `agent_hub/erp.py`.

Hiện chỉ một việc: nhân sự nghỉ → khóa AI cá nhân, liên kết Telegram, khóa MCP, token Google của người đó phải đóng ở
dịch vụ AI (bảng nằm bên đó). Chế độ embedded gọi thẳng hàm cũ; chế độ erp ký rồi gọi `/api/agent-hub/internal/revoke`.
Hỏng thì ghi log và đi tiếp — khóa tài khoản ERP không được chờ dịch vụ AI.
"""
from __future__ import annotations

import json
import logging

import requests

from app.core import agent_signature
from app.core.config import settings

log = logging.getLogger("app.agent_client")
TIMEOUT = 10


def revoke_user(db, user_id: int) -> bool:
    if not settings.agent_is_erp:
        from app.modules.agent_hub.service import revoke_user_access

        revoke_user_access(db, user_id)
        return True
    base = (settings.AGENT_SERVICE_URL or "").rstrip("/")
    path = "/api/agent-hub/internal/revoke"
    body = json.dumps({"user_id": int(user_id)}).encode("utf-8")
    try:
        headers = agent_signature.sign_headers("POST", path, body, 0)
        headers["content-type"] = "application/json"
        resp = requests.post(f"{base}{path}", data=body, headers=headers, timeout=TIMEOUT)
        if resp.status_code >= 400:
            raise RuntimeError(f"dịch vụ AI trả {resp.status_code}")
        return True
    except Exception as e:  # noqa: BLE001 — khóa tài khoản ERP vẫn phải xong
        log.warning("agent_client: không đóng được quyền bot của user %s ở dịch vụ AI: %s", user_id, e)
        return False
