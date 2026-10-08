"""Ứng dụng FastAPI của DỊCH VỤ AI (nút A — bot cá nhân), ai-CR-119, phase S của `doc/agent-hub/13-lo-trinh.md`.

Chạy với `AGENT_MODE=service`: DB riêng `agent_hub`, số liệu ERP hỏi qua cổng B (`AGENT_GATEWAY_URL`), người dùng web
đi vào bằng chữ ký của ERP (ERP chuyển tiếp `/api/agent-hub/*`, `/api/assistant/*`, `/api/mcp/*` sang đây).

Chỉ gắn những router của dịch vụ AI: sổ bot / khóa AI / Google / MCP / Trợ lý. KHÔNG gắn router ERP nào — DB này không
có bảng ERP, gọi tới là lỗi ngay thay vì âm thầm đọc sai.
"""
from __future__ import annotations

from fastapi import FastAPI

from app.core.app_factory import install_cors, install_error_handlers
from app.core.config import settings

if not settings.agent_is_service:
    raise RuntimeError("app.agent_main chỉ chạy với AGENT_MODE=service (đặt trong .env.agent)")

app = FastAPI(title="DEGO Agent Hub — dịch vụ AI", version="0.1.0")
install_error_handlers(app)
install_cors(app)

#  Người dùng web tới đây qua ERP chuyển tiếp (chữ ký), không có JWT.
from app.core import agent_identity  # noqa: E402
from app.core.auth import get_current_user  # noqa: E402

app.dependency_overrides[get_current_user] = agent_identity.current_user


@app.get("/api/health")
def health():
    return {"success": True, "message": "ok", "service": "agent-hub", "mode": settings.AGENT_MODE}


from app.modules.agent_hub.controller import router as agent_hub_router  # noqa: E402
from app.modules.agent_hub.mcp import router as mcp_router  # noqa: E402
from app.modules.assistant.controller import router as assistant_router  # noqa: E402

app.include_router(agent_hub_router)
app.include_router(mcp_router)
app.include_router(assistant_router)
