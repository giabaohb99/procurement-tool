"""ERP CHUYỂN TIẾP sang DỊCH VỤ AI (ai-CR-119, phase S-3) — chỉ gắn khi `AGENT_MODE=erp`.

Giao diện ERP v2 không đổi một dòng: vẫn gọi `/api/agent-hub/*` (sổ bot, khóa AI, Google, MCP key), `/api/assistant/*`
(Trợ lý AI trên web) và `/api/mcp/*` ở tên miền ERP. ERP xác thực JWT như mọi API, rồi ký danh tính người dùng
(`core/agent_signature.py`) và chuyển nguyên yêu cầu sang `AGENT_SERVICE_URL`. Dịch vụ AI tin danh tính trong chữ ký.

Ba đường KHÔNG chuyển (ERP tự phục vụ vì đụng kho tệp / Trung tâm HDSD của ERP): `/api/assistant/uploads*`,
`/api/assistant/files/*`, `/api/assistant/rag/*` — xem `assistant/controller.erp_local_router`.
`/api/agent-hub/google/callback` đi KHÔNG kèm JWT (Google gọi về) — chuyển thẳng, dịch vụ AI kiểm `state` ký bằng JWT_SECRET.
"""
from __future__ import annotations

import logging

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.core import agent_signature
from app.core.auth import get_current_user, require
from app.core.config import settings

log = logging.getLogger("app.agent_proxy")
router = APIRouter(tags=["agent-proxy"])
TIMEOUT = 120
#  Header không được chép sang (do lớp vận chuyển tự đặt) và không được chép về.
_SKIP_REQ = {"host", "content-length", "connection", "authorization", "cookie", "transfer-encoding"}
_SKIP_RESP = {"content-length", "transfer-encoding", "connection", "content-encoding", "server", "date"}


async def forward(request: Request, user_id: int) -> Response:
    base = (settings.AGENT_SERVICE_URL or "").rstrip("/")
    if not base:
        raise HTTPException(503, "Chưa khai AGENT_SERVICE_URL — dịch vụ AI chưa nối với ERP")
    body = await request.body()
    path = request.url.path
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _SKIP_REQ}
    try:
        headers.update(agent_signature.sign_headers(request.method, path, body, user_id))
    except ValueError as e:
        raise HTTPException(503, str(e)) from None
    #  MCP xác thực bằng khóa riêng trong Authorization: giữ nguyên cho dịch vụ AI kiểm.
    if path.startswith("/api/mcp") and request.headers.get("authorization"):
        headers["authorization"] = request.headers["authorization"]
    try:
        resp = requests.request(request.method, f"{base}{path}", params=request.url.query or None, data=body or None,
                                headers=headers, timeout=TIMEOUT, allow_redirects=False)
    except requests.RequestException as e:
        log.warning("agent_proxy: không gọi được dịch vụ AI: %s", e)
        raise HTTPException(503, "Dịch vụ AI không phản hồi, thử lại sau ít phút") from None
    out_headers = {k: v for k, v in resp.headers.items() if k.lower() not in _SKIP_RESP}
    return Response(content=resp.content, status_code=resp.status_code, headers=out_headers,
                    media_type=resp.headers.get("content-type"))


METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@router.api_route("/api/agent-hub/google/callback", methods=["GET"])
async def google_callback(request: Request):
    return await forward(request, 0)


@router.api_route("/api/agent-hub/{path:path}", methods=METHODS)
async def agent_hub(path: str, request: Request, user=Depends(get_current_user)):
    if path.startswith("internal"):
        #  Đường máy-nói-máy của dịch vụ AI (vd internal/revoke) không bao giờ mở cho người dùng web.
        raise HTTPException(404, "Không có đường này")
    return await forward(request, int(user.id))


@router.api_route("/api/assistant/{path:path}", methods=METHODS)
async def assistant(path: str, request: Request, user=Depends(require("assistant", "read"))):
    return await forward(request, int(user.id))


@router.api_route("/api/mcp/{path:path}", methods=METHODS)
@router.api_route("/api/mcp", methods=METHODS)
async def mcp(request: Request, path: str = ""):
    return await forward(request, 0)
