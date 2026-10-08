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

#  Các router trên kéo theo model ERP `Employee` / `User` (qua assistant.usage). Quan hệ của chúng trỏ tới `Department`,
#  `Company` — không nạp thì SQLAlchemy dựng quan hệ hỏng ngay lần truy vấn đầu, và hỏng LUÔN cho tới khi khởi động
#  lại: mọi đường có truy vấn (danh sách nhóm, lịch sử hội thoại…) trả 500 (gặp trên dev 08/10/2026). Chỉ nạp để đăng ký
#  lớp — DB `agent_hub` không có các bảng này và không đường nào ở đây truy vấn chúng.
#  `from … import model as …` chứ KHÔNG `import app.modules…` — câu đó gán đè tên `app` (ứng dụng FastAPI ở trên).
from app.modules.company import model as _company_model  # noqa: E402,F401
from app.modules.department import model as _department_model  # noqa: E402,F401

app.include_router(agent_hub_router)
app.include_router(mcp_router)
app.include_router(assistant_router)
