"""Đường HTTP của máy chủ cấp quyền OAuth cho cổng MCP (ai-CR-218, K14). Lõi ở `oauth.py`.

Hai loại đường:
- CÔNG KHAI (ứng dụng AI gọi, không có JWT web): `/.well-known/oauth-authorization-server[/...]`,
  `/.well-known/oauth-protected-resource[/...]`, `POST /api/oauth/register`, `GET /api/oauth/authorize` (trình duyệt của
  người dùng mở — chuyển sang màn đồng ý ERP v2 `/oauth/consent/<mã ký>`), `POST /api/oauth/token`, `POST /api/oauth/revoke`.
  Chế độ tách dịch vụ: ERP chuyển nguyên các đường này sang dịch vụ AI (`agent_gateway/proxy.py`), nginx erp chuyển
  `/.well-known/oauth-*` sang api.
- CẦN ĐĂNG NHẬP (màn đồng ý gọi, qua proxy `/api/agent-hub/*`): đọc yêu cầu, Cho phép, Từ chối.
"""
from __future__ import annotations

import base64
import html
import json
import logging
from urllib.parse import parse_qs, unquote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.response import success

from . import mcp_log, oauth

log = logging.getLogger("app.agent_hub.oauth")
public_router = APIRouter(tags=["mcp-oauth"])
router = APIRouter(prefix="/api/agent-hub/oauth", tags=["mcp-oauth"])
REGISTER_PER_MIN_PER_IP = 5          # ai-CR-225: 30 → 5 (ứng dụng thật đăng ký một lần mỗi lần nối)
_NO_STORE = {"Cache-Control": "no-store", "Pragma": "no-cache"}
if not settings.AGENT_ERP_URL:
    #  ai-CR-222: báo NGAY lúc nạp router — không khai thì mọi đường OAuth trả 503 (trừ máy local), xem oauth.issuer.
    log.error("AGENT_ERP_URL chưa khai: OAuth cổng MCP (ChatGPT / claude.ai) sẽ trả 503 — khai gốc công khai của ERP.")


def _base(request: Request) -> str:
    """Gốc công khai — chỉ `AGENT_ERP_URL` (ai-CR-222: bỏ X-Forwarded-Host). Chưa khai mà không phải máy local → 503."""
    try:
        return oauth.issuer(request.url.scheme, request.url.netloc)
    except oauth.OAuthError as e:
        log.error("OAuth cổng MCP: %s", e.description)
        raise HTTPException(503, e.description) from e


def _error(e: oauth.OAuthError) -> JSONResponse:
    return JSONResponse(e.body(), status_code=e.status, headers=_NO_STORE)


async def _form(request: Request) -> dict:
    raw = await request.body()
    if "application/json" in (request.headers.get("content-type") or ""):
        try:
            data = json.loads(raw or b"{}")
        except ValueError:
            return {}
        return {k: str(v) for k, v in data.items()} if isinstance(data, dict) else {}
    return {k: v[0] for k, v in parse_qs(raw.decode("utf-8", "replace"), keep_blank_values=True).items()}


def _client_credentials(request: Request, form: dict) -> tuple[str, str]:
    """client_secret_basic (header Basic, RFC 6749 §2.3.1 — hai phần đã url-encode) hoặc trong form."""
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("basic "):
        try:
            cid, _, secret = base64.b64decode(auth.split(" ", 1)[1]).decode().partition(":")
            return unquote(cid), unquote(secret)
        except (ValueError, UnicodeDecodeError):
            return "", ""
    return form.get("client_id", ""), form.get("client_secret", "")


# --- công khai -------------------------------------------------------------------------------------------------------
@public_router.get("/.well-known/oauth-authorization-server")
@public_router.get("/.well-known/oauth-authorization-server/{rest:path}")
def as_metadata(request: Request, rest: str = ""):
    return JSONResponse(oauth.authorization_server_metadata(_base(request)))


@public_router.get("/.well-known/oauth-protected-resource")
@public_router.get("/.well-known/oauth-protected-resource/{rest:path}")
def pr_metadata(request: Request, rest: str = ""):
    return JSONResponse(oauth.protected_resource_metadata(_base(request)))


@public_router.post("/api/oauth/register")
async def register_client(request: Request, db: Session = Depends(get_db)):
    ip = mcp_log.client_ip(request)
    if mcp_log.over_limit(f"oreg:{ip}", REGISTER_PER_MIN_PER_IP):
        return JSONResponse({"error": "invalid_client_metadata", "error_description": "Đăng ký quá dồn dập, thử lại sau."},
                            status_code=429)
    try:
        payload = json.loads((await request.body()) or b"{}")
    except ValueError:
        return _error(oauth.OAuthError("invalid_client_metadata", "Thân yêu cầu không phải JSON."))
    try:
        return JSONResponse(oauth.register(db, payload, ip), status_code=201, headers=_NO_STORE)
    except oauth.OAuthError as e:
        return _error(e)


def _error_page(message: str, status: int = 400) -> HTMLResponse:
    body = ("<!doctype html><meta charset='utf-8'><title>Không kết nối được</title>"
            "<div style='font-family:system-ui;max-width:32rem;margin:4rem auto;line-height:1.5'>"
            "<h2>Không kết nối được ứng dụng AI với ERP</h2>"
            f"<p>{html.escape(message)}</p><p>Quay lại ứng dụng AI và thử kết nối lại.</p></div>")
    return HTMLResponse(body, status_code=status)


@public_router.get("/api/oauth/authorize")
def authorize(request: Request, db: Session = Depends(get_db)):
    base = _base(request)
    try:
        kind, value = oauth.begin_authorize(db, dict(request.query_params), base)
    except oauth.OAuthError as e:
        return _error_page(e.description)
    if kind == "redirect":
        return RedirectResponse(value, status_code=302)
    return RedirectResponse(f"{base}/oauth/consent/{value}", status_code=302)


@public_router.post("/api/oauth/token")
async def token(request: Request, db: Session = Depends(get_db)):
    form = await _form(request)
    cid, secret = _client_credentials(request, form)
    try:
        client = oauth.authenticate_client(db, cid, secret)
        grant = form.get("grant_type", "")
        if grant == "authorization_code":
            out = oauth.exchange_code(db, client, form.get("code", ""), form.get("redirect_uri", ""),
                                      form.get("code_verifier", ""), form.get("resource", ""))
        elif grant == "refresh_token":
            out = oauth.refresh(db, client, form.get("refresh_token", ""))
        else:
            raise oauth.OAuthError("unsupported_grant_type", "Chỉ nhận authorization_code / refresh_token.")
    except oauth.OAuthError as e:
        return _error(e)
    return JSONResponse(out, headers=_NO_STORE)


@public_router.post("/api/oauth/revoke")
async def revoke(request: Request, db: Session = Depends(get_db)):
    form = await _form(request)
    cid, secret = _client_credentials(request, form)
    try:
        client = oauth.authenticate_client(db, cid, secret)
    except oauth.OAuthError as e:
        return _error(e)
    oauth.revoke_token(db, client, form.get("token", ""))
    return JSONResponse({}, headers=_NO_STORE)


# --- màn đồng ý (cần đăng nhập ERP) ----------------------------------------------------------------------------------
class ConsentIn(BaseModel):
    req: str = Field(max_length=4000)
    scope: int = Field(default=0, ge=0, le=1)


@router.get("/request/{req}")
def consent_request(req: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    from . import erp

    try:
        info = oauth.describe_request(db, req)
    except oauth.OAuthError as e:
        raise HTTPException(400, e.description) from e
    return success({**info, "user_label": erp.describe(db, user)[0]})


@router.post("/approve")
def consent_approve(body: ConsentIn, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        return success({"redirect_to": oauth.approve(db, user, body.req, body.scope, _base(request))})
    except oauth.OAuthError as e:
        raise HTTPException(400, e.description) from e


@router.post("/deny")
def consent_deny(body: ConsentIn, request: Request, user=Depends(get_current_user)):
    try:
        return success({"redirect_to": oauth.deny(body.req, _base(request))})
    except oauth.OAuthError as e:
        raise HTTPException(400, e.description) from e
