"""Máy chủ cấp quyền OAuth 2.1 TỐI THIỂU cho cổng MCP (ai-CR-218, K14 — doc/erp/21 §7.2, đại ca chốt 19/10).

ChatGPT, claude.ai, Claude Desktop (Connectors) không dán được khóa vào header — chúng nối MCP qua OAuth theo đặc tả MCP
2025-06-18: đọc `/.well-known/oauth-protected-resource` (RFC 9728) → `/.well-known/oauth-authorization-server` (RFC 8414)
→ tự đăng ký (RFC 7591) → mở trang cấp quyền trên ERP → đổi mã lấy token (PKCE S256 bắt buộc) → gọi `/api/mcp` với
`Authorization: Bearer <access_token>`.

Thiết kế:
- Mỗi lần người dùng bấm "Cho phép" một ứng dụng = MỘT dòng `tab_agent_mcp_key` loại `KIND_OAUTH` (cùng mức chỉ đọc /
  được ghi, cùng nhật ký, cùng màn Khóa của tôi / Khóa nhân sự, gỡ là cắt ngay). `token_hash` = băm mã truy cập hiện hành
  (hạn `ACCESS_TTL_SEC`), `refresh_hash` = băm mã làm mới hiện hành (xoay vòng mỗi lần đổi), `expires_at` = hạn cả kết nối.
  Cấp lại cho cùng (người, ứng dụng) thì kết nối cũ bị thu hồi — không chất đống dòng.
- Mã truy cập mang tiền tố `mcp_keys.PREFIX` nên cổng MCP phân giải chung đường với khóa dán tay; khác mỗi hạn ngắn.
- Mã cấp quyền (code) chỉ giữ băm, sống `CODE_TTL_SEC`, dùng MỘT lần.
- Yêu cầu cấp quyền (tham số của `/authorize`) đi tới màn đồng ý dưới dạng chuỗi KÝ HMAC (`JWT_SECRET`), không lưu DB.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlsplit

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings

from . import mcp_keys
from .model import AgentMcpKey, AgentOAuthClient, AgentOAuthCode

ACCESS_TTL_SEC = 3600
CODE_TTL_SEC = 300
REQUEST_TTL_SEC = 600
GRANT_DAYS = 90
REFRESH_PREFIX = "dego_mcr_"
CLIENT_PREFIX = "dego_oc_"
MAX_REDIRECT_URIS = 10
URI_MAX_LEN = 500
NAME_MAX_LEN = 200
SCOPE_READ_STR = "mcp:read"
SCOPE_WRITE_STR = "mcp:write"
AUTH_METHODS = ("none", "client_secret_post", "client_secret_basic")
GRANT_TYPES = ("authorization_code", "refresh_token")
_BAD_SCHEMES = frozenset({"javascript", "data", "file", "vbscript", "about", "blob"})
_LOOPBACK = frozenset({"localhost", "127.0.0.1", "[::1]", "::1"})
#  ai-CR-225 (Agent 1 rà 19/10, mục 3 consent-phishing): địa chỉ quay về của các ứng dụng AI quen — khác thì màn đồng ý
#  cảnh báo đỏ. So theo HOSTNAME (đuôi tên miền), không theo netloc: `https://chatgpt.com@evil.example/cb` có hostname
#  evil.example (phần trước @ là userinfo) — netloc in ra "chatgpt.com@evil.example" lừa được người đọc lướt.
KNOWN_REDIRECT_HOSTS = ("chatgpt.com", "openai.com", "claude.ai", "anthropic.com", "claude.com")
#  Mục 4: bảng ứng dụng / mã cấp quyền không phình vô hạn.
CODE_KEEP_DAYS = 1                  # mã cấp quyền hết hạn quá 1 ngày → xóa
UNUSED_CLIENT_DAYS = 7              # ứng dụng đăng ký mà 7 ngày không kết nối được ai (không có kết nối sống) → xóa
REGISTER_PER_DAY = 200              # trần đăng ký toàn hệ / 24 giờ (thêm cho trần mỗi IP ở controller)
_VERIFIER_RX = re.compile(r"^[A-Za-z0-9\-._~]{43,128}$")


class OAuthError(Exception):
    """Lỗi theo RFC 6749 §5.2 / RFC 7591 §3.2.2. `redirect` = có được trả về redirect_uri của ứng dụng hay không."""

    def __init__(self, error: str, description: str, status: int = 400):
        super().__init__(description)
        self.error, self.description, self.status = error, description, status

    def body(self) -> dict:
        return {"error": self.error, "error_description": self.description}


# --- địa chỉ ---------------------------------------------------------------------------------------------------------
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
MISSING_ISSUER = "Máy chủ chưa khai AGENT_ERP_URL (gốc công khai của ERP) nên chưa nối OAuth được — báo quản trị."


def issuer(scheme: str = "", host: str = "") -> str:
    """Gốc công khai của ERP — CHỈ lấy `AGENT_ERP_URL` (ai-CR-222, Agent 1 rà 19/10). Không bao giờ đọc `X-Forwarded-Host`:
    người gọi tự đặt được header đó, và ở chế độ tách dịch vụ địa chỉ đến là gốc NỘI BỘ (agent:8001) — ChatGPT không nối
    được. Chưa khai thì chỉ máy local (dev, host loopback) mới dùng tạm địa chỉ đang đến; còn lại báo lỗi rõ (503)."""
    if settings.AGENT_ERP_URL:
        return settings.AGENT_ERP_URL.rstrip("/")
    try:
        name = (urlsplit(f"//{host}").hostname or "").lower() if host else ""
    except ValueError:
        name = ""
    if scheme and name in LOOPBACK_HOSTS:
        return f"{scheme}://{host}".rstrip("/")
    raise OAuthError("server_error", MISSING_ISSUER, 503)


def resource_url(base: str) -> str:
    return f"{base}/api/mcp"


def protected_resource_metadata_url(base: str) -> str:
    return f"{base}/.well-known/oauth-protected-resource"


def authorization_server_metadata(base: str) -> dict:
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/api/oauth/authorize",
        "token_endpoint": f"{base}/api/oauth/token",
        "registration_endpoint": f"{base}/api/oauth/register",
        "revocation_endpoint": f"{base}/api/oauth/revoke",
        "response_types_supported": ["code"],
        "grant_types_supported": list(GRANT_TYPES),
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": list(AUTH_METHODS),
        "revocation_endpoint_auth_methods_supported": list(AUTH_METHODS),
        "scopes_supported": [SCOPE_READ_STR, SCOPE_WRITE_STR],
        "authorization_response_iss_parameter_supported": True,
    }


def protected_resource_metadata(base: str) -> dict:
    return {
        "resource": resource_url(base),
        "authorization_servers": [base],
        "bearer_methods_supported": ["header"],
        "scopes_supported": [SCOPE_READ_STR, SCOPE_WRITE_STR],
        "resource_name": "DEGO ERP",
    }


# --- đăng ký ứng dụng (RFC 7591) -------------------------------------------------------------------------------------
def _valid_redirect(uri) -> bool:
    if not isinstance(uri, str) or not uri or len(uri) > URI_MAX_LEN or "#" in uri:
        return False
    try:
        parts = urlsplit(uri)
        parts.port                  # cổng sai dạng → ValueError
    except ValueError:
        return False
    scheme = (parts.scheme or "").lower()
    if not scheme or scheme in _BAD_SCHEMES:
        return False
    if "@" in (parts.netloc or ""):
        return False                # ai-CR-225: userinfo trong địa chỉ quay về chỉ để giả tên miền
    if scheme == "https":
        return bool(parts.netloc)
    if scheme == "http":
        return (parts.hostname or "").lower() in _LOOPBACK       # RFC 8252: http chỉ cho máy cục bộ
    return True                                                 # lược đồ riêng của ứng dụng cài máy (cursor://…)


def register(db: Session, payload: dict, ip: str = "") -> dict:
    if not isinstance(payload, dict):
        raise OAuthError("invalid_client_metadata", "Thân yêu cầu phải là đối tượng JSON.")
    uris = payload.get("redirect_uris")
    if not isinstance(uris, list) or not uris or len(uris) > MAX_REDIRECT_URIS:
        raise OAuthError("invalid_redirect_uri", f"Cần 1 tới {MAX_REDIRECT_URIS} redirect_uris.")
    bad = [u for u in uris if not _valid_redirect(u)]
    if bad:
        raise OAuthError("invalid_redirect_uri", "redirect_uri không hợp lệ (https, http cục bộ, hoặc lược đồ riêng; "
                                                 "không có #): " + ", ".join(str(b)[:80] for b in bad[:3]))
    since = datetime.now() - timedelta(days=1)
    if db.query(AgentOAuthClient.id).filter(AgentOAuthClient.created_at >= since).count() >= REGISTER_PER_DAY:
        raise OAuthError("temporarily_unavailable", "Hôm nay đã quá nhiều ứng dụng đăng ký — thử lại sau.", 429)
    method = str(payload.get("token_endpoint_auth_method") or "none")
    if method not in AUTH_METHODS:
        raise OAuthError("invalid_client_metadata", f"token_endpoint_auth_method chỉ nhận: {', '.join(AUTH_METHODS)}.")
    grants = payload.get("grant_types") or list(GRANT_TYPES)
    if not isinstance(grants, list) or not set(grants) <= set(GRANT_TYPES) or "authorization_code" not in grants:
        raise OAuthError("invalid_client_metadata", "grant_types chỉ nhận authorization_code (+ refresh_token).")
    responses = payload.get("response_types") or ["code"]
    if responses != ["code"]:
        raise OAuthError("invalid_client_metadata", "response_types chỉ nhận [\"code\"].")
    name = str(payload.get("client_name") or "").strip()[:NAME_MAX_LEN] or "Ứng dụng AI"
    client_id = CLIENT_PREFIX + secrets.token_urlsafe(24)
    secret = secrets.token_urlsafe(32) if method != "none" else ""
    row = AgentOAuthClient(client_id=client_id, client_name=name, redirect_uris=list(uris),
                           token_endpoint_auth_method=method, client_secret_hash=_hash(secret) if secret else "",
                           ip=(ip or "")[:45])
    db.add(row)
    db.commit()
    out = {"client_id": client_id, "client_id_issued_at": int(time.time()), "client_name": name,
           "redirect_uris": list(uris), "grant_types": list(grants), "response_types": ["code"],
           "token_endpoint_auth_method": method}
    if secret:
        out.update(client_secret=secret, client_secret_expires_at=0)
    return out


def client_by_id(db: Session, client_id: str) -> AgentOAuthClient | None:
    if not client_id or not str(client_id).startswith(CLIENT_PREFIX):
        return None
    return db.scalar(select(AgentOAuthClient).where(AgentOAuthClient.client_id == str(client_id)[:64]))


def authenticate_client(db: Session, client_id: str, secret: str) -> AgentOAuthClient:
    """Xác thực ứng dụng ở đường token / revoke. Ứng dụng công khai (`none`) chỉ cần client_id (đã có PKCE)."""
    client = client_by_id(db, client_id)
    if client is None:
        raise OAuthError("invalid_client", "Ứng dụng chưa đăng ký.", 401)
    if client.token_endpoint_auth_method != "none":
        if not secret or not hmac.compare_digest(_hash(secret), client.client_secret_hash or ""):
            raise OAuthError("invalid_client", "Sai bí mật ứng dụng.", 401)
    return client


# --- yêu cầu cấp quyền (/authorize → màn đồng ý) ---------------------------------------------------------------------
def _hash(raw: str) -> str:
    return hashlib.sha256(f"agent-oauth:{raw}".encode()).hexdigest()


def _sign(payload: str) -> str:
    return hmac.new(settings.JWT_SECRET.encode(), f"oauth-req:{payload}".encode(), hashlib.sha256).hexdigest()[:32]


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def sign_request(data: dict, now: float | None = None) -> str:
    payload = _b64(json.dumps({**data, "exp": int((now or time.time()) + REQUEST_TTL_SEC)}, separators=(",", ":"),
                              ensure_ascii=False).encode())
    return f"{payload}.{_sign(payload)}"


def read_request(token: str, now: float | None = None) -> dict | None:
    try:
        payload, sig = str(token or "").rsplit(".", 1)
    except ValueError:
        return None
    if not hmac.compare_digest(_sign(payload), sig):
        return None
    try:
        data = json.loads(_unb64(payload))
    except (ValueError, json.JSONDecodeError):
        return None
    try:                                 # ai-CR-222: `exp` lạ (chuỗi, số thực…) thì coi như yêu cầu hỏng, không ném 500
        exp = int(data.get("exp") or 0) if isinstance(data, dict) else 0
    except (TypeError, ValueError):
        return None
    if not isinstance(data, dict) or exp < (now or time.time()):
        return None
    return data


def redirect_with(uri: str, params: dict) -> str:
    sep = "&" if urlsplit(uri).query else "?"
    return uri + sep + urlencode({k: v for k, v in params.items() if v not in (None, "")})


def begin_authorize(db: Session, params: dict, base: str) -> tuple[str, str]:
    """Kiểm tham số /authorize. Trả ("consent", chuỗi ký) để chuyển sang màn đồng ý, hoặc ("redirect", url lỗi) khi lỗi trả
    được về ứng dụng. Ứng dụng lạ / redirect_uri lạ → OAuthError (KHÔNG chuyển hướng tới địa chỉ chưa kiểm — RFC 6749 §4.1.2.1)."""
    client = client_by_id(db, str(params.get("client_id") or ""))
    if client is None:
        raise OAuthError("invalid_client", "Ứng dụng chưa đăng ký với ERP (client_id lạ).")
    registered = list(client.redirect_uris or [])
    redirect_uri = str(params.get("redirect_uri") or "")
    if not redirect_uri and len(registered) == 1:
        redirect_uri = registered[0]
    if redirect_uri not in registered:
        raise OAuthError("invalid_request", "redirect_uri không khớp địa chỉ ứng dụng đã đăng ký.")
    state = str(params.get("state") or "")[:1000]

    def fail(error: str, description: str) -> tuple[str, str]:
        return "redirect", redirect_with(redirect_uri, {"error": error, "error_description": description,
                                                        "state": state, "iss": base})

    if str(params.get("response_type") or "") != "code":
        return fail("unsupported_response_type", "Chỉ hỗ trợ response_type=code.")
    challenge = str(params.get("code_challenge") or "")
    if not challenge or str(params.get("code_challenge_method") or "") != "S256" or not 43 <= len(challenge) <= 128:
        return fail("invalid_request", "Bắt buộc PKCE: code_challenge + code_challenge_method=S256.")
    resource = str(params.get("resource") or "")[:URI_MAX_LEN]
    if resource and not resource.rstrip("/").startswith(base):
        return fail("invalid_target", "resource không thuộc ERP này.")
    scope = str(params.get("scope") or "")
    want = mcp_keys.SCOPE_WRITE if SCOPE_WRITE_STR in scope.split() else mcp_keys.SCOPE_READ
    return "consent", sign_request({"c": client.client_id, "r": redirect_uri, "s": state, "pc": challenge,
                                    "rs": resource, "w": int(want)})


def describe_request(db: Session, token: str) -> dict:
    """Dữ liệu cho màn đồng ý. OAuthError nếu chuỗi ký sai / hết hạn / ứng dụng đã bị xóa."""
    req = read_request(token)
    if req is None:
        raise OAuthError("invalid_request", "Yêu cầu cấp quyền đã hết hạn hoặc không hợp lệ — quay lại ứng dụng AI và "
                                            "kết nối lại.")
    client = client_by_id(db, req["c"])
    if client is None:
        raise OAuthError("invalid_client", "Ứng dụng không còn đăng ký.")
    host, trusted = redirect_target(req["r"])
    return {"client_name": client.client_name, "redirect_host": host, "redirect_trusted": trusted,
            "requested_scope": int(req.get("w") or 0), "grant_days": GRANT_DAYS,
            "scopes": [{"value": k, "label": v} for k, v in mcp_keys.SCOPE_LABELS.items()]}


def redirect_target(uri: str) -> tuple[str, bool]:
    """(nhãn nơi quay về để hiện cho người dùng, có thuộc ứng dụng AI quen không). Nhãn là HOSTNAME — không userinfo, không
    cổng; máy cục bộ ghi rõ; lược đồ riêng (ứng dụng cài máy, vd cursor://) ghi tên lược đồ."""
    parts = urlsplit(uri or "")
    host = (parts.hostname or "").lower()
    scheme = (parts.scheme or "").lower()
    if host in _LOOPBACK:
        return f"máy tính của bạn ({host})", True
    if scheme not in ("http", "https"):
        return f"ứng dụng cài trên máy ({scheme}://)", False
    trusted = any(host == h or host.endswith("." + h) for h in KNOWN_REDIRECT_HOSTS)
    return host or "(không rõ)", trusted


def purge(db: Session, now: datetime | None = None) -> dict:
    """ai-CR-225 (mục 4): xóa mã cấp quyền hết hạn quá CODE_KEEP_DAYS ngày và ứng dụng đăng ký mà UNUSED_CLIENT_DAYS ngày
    không có kết nối nào còn sống (chưa ai cho phép, hoặc mọi kết nối đã thu hồi / hết hạn)."""
    now = now or datetime.now()
    codes = db.query(AgentOAuthCode).filter(AgentOAuthCode.expires_at < now - timedelta(days=CODE_KEEP_DAYS)) \
        .delete(synchronize_session=False)
    cutoff = now - timedelta(days=UNUSED_CLIENT_DAYS)
    live = {cid for (cid,) in db.query(AgentMcpKey.oauth_client_id).filter(
        AgentMcpKey.kind == mcp_keys.KIND_OAUTH, AgentMcpKey.revoked_at.is_(None),
        (AgentMcpKey.expires_at.is_(None)) | (AgentMcpKey.expires_at > now))}
    stale = [c for c in db.query(AgentOAuthClient).filter(AgentOAuthClient.created_at < cutoff)
             if c.id not in live and (c.last_used_at is None or c.last_used_at < cutoff)]
    for c in stale:
        db.query(AgentOAuthCode).filter(AgentOAuthCode.client_pk == c.id).delete(synchronize_session=False)
        db.delete(c)
    db.commit()
    return {"oauth_codes_deleted": int(codes or 0), "oauth_clients_deleted": len(stale)}


def list_clients(db: Session, now: datetime | None = None) -> list[dict]:
    """Màn quản trị ứng dụng OAuth: mọi ứng dụng đã đăng ký + số kết nối còn sống."""
    now = now or datetime.now()
    counts: dict[int, int] = {}
    for (cid,) in db.query(AgentMcpKey.oauth_client_id).filter(
            AgentMcpKey.kind == mcp_keys.KIND_OAUTH, AgentMcpKey.revoked_at.is_(None),
            (AgentMcpKey.expires_at.is_(None)) | (AgentMcpKey.expires_at > now)):
        counts[int(cid)] = counts.get(int(cid), 0) + 1
    iso = lambda d: d.isoformat(timespec="seconds") if d else None  # noqa: E731
    out = []
    for c in db.query(AgentOAuthClient).order_by(AgentOAuthClient.id.desc()).limit(500):
        hosts = [redirect_target(u) for u in (c.redirect_uris or [])]
        out.append({"id": c.id, "client_id": c.client_id, "client_name": c.client_name,
                    "redirect_hosts": sorted({h for h, _t in hosts}), "trusted": bool(hosts) and all(t for _h, t in hosts),
                    "auth_method": c.token_endpoint_auth_method, "ip": c.ip, "created_at": iso(c.created_at),
                    "last_used_at": iso(c.last_used_at), "live_grants": counts.get(int(c.id), 0)})
    return out


def delete_client(db: Session, client_pk: int, by_user_id: int = 0) -> int | None:
    """Xóa một ứng dụng: thu hồi mọi kết nối của nó (mã truy cập + làm mới chết ngay), xóa mã cấp quyền. None = không có."""
    client = db.get(AgentOAuthClient, int(client_pk))
    if client is None:
        return None
    grants = list(db.scalars(select(AgentMcpKey).where(AgentMcpKey.kind == mcp_keys.KIND_OAUTH,
                                                       AgentMcpKey.oauth_client_id == client.id)))
    n = mcp_keys.revoke_rows(db, grants, by_user_id)
    db.query(AgentOAuthCode).filter(AgentOAuthCode.client_pk == client.id).delete(synchronize_session=False)
    db.delete(client)
    db.commit()
    return n


def approve(db: Session, user, token: str, scope: int, base: str, now: datetime | None = None) -> str:
    """Người dùng bấm Cho phép → tạo mã cấp quyền một lần → URL quay về ứng dụng (kèm code, state, iss)."""
    req = read_request(token)
    if req is None:
        raise OAuthError("invalid_request", "Yêu cầu cấp quyền đã hết hạn — quay lại ứng dụng AI và kết nối lại.")
    client = client_by_id(db, req["c"])
    if client is None:
        raise OAuthError("invalid_client", "Ứng dụng không còn đăng ký.")
    now = now or datetime.now()
    code = secrets.token_urlsafe(32)
    db.add(AgentOAuthCode(code_hash=_hash(code), client_pk=client.id, user_id=int(user.id), redirect_uri=req["r"],
                          code_challenge=req["pc"], resource=req.get("rs") or "",
                          scope=mcp_keys.SCOPE_WRITE if int(scope) == mcp_keys.SCOPE_WRITE else mcp_keys.SCOPE_READ,
                          expires_at=now + timedelta(seconds=CODE_TTL_SEC), created_at=now))
    db.commit()
    return redirect_with(req["r"], {"code": code, "state": req.get("s"), "iss": base})


def deny(token: str, base: str) -> str:
    req = read_request(token)
    if req is None:
        raise OAuthError("invalid_request", "Yêu cầu cấp quyền đã hết hạn.")
    return redirect_with(req["r"], {"error": "access_denied", "error_description": "Người dùng từ chối.",
                                    "state": req.get("s"), "iss": base})


# --- token -----------------------------------------------------------------------------------------------------------
def pkce_ok(verifier: str, challenge: str) -> bool:
    if not _VERIFIER_RX.match(verifier or ""):
        return False
    return hmac.compare_digest(_b64(hashlib.sha256(verifier.encode()).digest()), challenge or "")


def _scope_str(scope: int) -> str:
    return f"{SCOPE_READ_STR} {SCOPE_WRITE_STR}" if int(scope) == mcp_keys.SCOPE_WRITE else SCOPE_READ_STR


def _issue_tokens(row: AgentMcpKey, now: datetime) -> dict:
    access = mcp_keys.PREFIX + secrets.token_urlsafe(30)
    refresh = REFRESH_PREFIX + secrets.token_urlsafe(40)
    row.token_hash = mcp_keys.hash_token(access)
    row.key_hint = access[-4:]
    row.access_expires_at = now + timedelta(seconds=ACCESS_TTL_SEC)
    row.refresh_hash = _hash(refresh)
    return {"access_token": access, "token_type": "Bearer", "expires_in": ACCESS_TTL_SEC, "refresh_token": refresh,
            "scope": _scope_str(row.scope)}


def exchange_code(db: Session, client: AgentOAuthClient, code: str, redirect_uri: str, verifier: str,
                  resource: str = "", now: datetime | None = None) -> dict:
    now = now or datetime.now()
    row = db.scalar(select(AgentOAuthCode).where(AgentOAuthCode.code_hash == _hash(code or "")))
    if row is None or row.client_pk != client.id:
        raise OAuthError("invalid_grant", "Mã cấp quyền không hợp lệ.")
    #  ai-CR-222: ĐỐT mã ngay (UPDATE có điều kiện + commit) TRƯỚC mọi kiểm tra — hai yêu cầu song song cùng mã thì chỉ một
    #  bên đổi được dòng; mã sai PKCE / sai redirect cũng bị đốt (RFC 6749 §4.1.2: mã chỉ dùng một lần, kể cả lần hỏng).
    burned = db.execute(update(AgentOAuthCode).where(AgentOAuthCode.id == row.id, AgentOAuthCode.used_at.is_(None))
                        .values(used_at=now)).rowcount
    db.commit()
    if not burned:
        raise OAuthError("invalid_grant", "Mã cấp quyền đã dùng rồi.")
    db.refresh(row)
    if row.expires_at <= now:
        raise OAuthError("invalid_grant", "Mã cấp quyền đã hết hạn.")
    if (redirect_uri or row.redirect_uri) != row.redirect_uri:
        raise OAuthError("invalid_grant", "redirect_uri không khớp lúc xin cấp quyền.")
    if not pkce_ok(verifier, row.code_challenge):
        raise OAuthError("invalid_grant", "code_verifier sai (PKCE).")
    if resource and row.resource and resource.rstrip("/") != row.resource.rstrip("/"):
        raise OAuthError("invalid_target", "resource khác lúc xin cấp quyền.")
    #  Cấp lại cho cùng người + ứng dụng → kết nối cũ chết (khỏi chất đống dòng, khỏi để mã cũ sống tiếp).
    old = list(db.scalars(select(AgentMcpKey).where(
        AgentMcpKey.user_id == row.user_id, AgentMcpKey.kind == mcp_keys.KIND_OAUTH,
        AgentMcpKey.oauth_client_id == client.id, AgentMcpKey.revoked_at.is_(None))))
    for k in old:
        k.revoked_at, k.refresh_hash, k.updated_by = now, "", row.user_id
    grant = AgentMcpKey(user_id=row.user_id, name=f"Qua {client.client_name}"[:80], scope=row.scope,
                        kind=mcp_keys.KIND_OAUTH, oauth_client_id=client.id,
                        expires_at=now + timedelta(days=GRANT_DAYS), created_by=row.user_id, updated_by=row.user_id)
    tokens = _issue_tokens(grant, now)
    db.add(grant)
    client.last_used_at = now
    db.commit()
    return tokens


def refresh(db: Session, client: AgentOAuthClient, refresh_token: str, now: datetime | None = None) -> dict:
    now = now or datetime.now()
    raw = refresh_token or ""
    row = db.scalar(select(AgentMcpKey).where(AgentMcpKey.refresh_hash == _hash(raw), AgentMcpKey.kind == mcp_keys.KIND_OAUTH)) \
        if raw.startswith(REFRESH_PREFIX) else None
    if row is None or row.oauth_client_id != client.id or row.revoked_at is not None:
        raise OAuthError("invalid_grant", "Mã làm mới không hợp lệ hoặc kết nối đã bị thu hồi.")
    if row.expires_at is not None and row.expires_at <= now:
        raise OAuthError("invalid_grant", "Kết nối đã hết hạn — kết nối lại từ ứng dụng AI.")
    if row.disabled_at is not None:      # ai-CR-221: chủ khóa tắt tạm thì không cấp mã truy cập mới
        raise OAuthError("invalid_grant", "Kết nối đang tắt — bật lại ở Trang cá nhân, Khóa AI.")
    tokens = _issue_tokens(row, now)
    client.last_used_at = now
    db.commit()
    return tokens


def revoke_token(db: Session, client: AgentOAuthClient, token: str) -> None:
    """RFC 7009: thu hồi theo mã truy cập hoặc mã làm mới; mã lạ cũng trả 200 (không lộ gì)."""
    raw = token or ""
    if raw.startswith(REFRESH_PREFIX):
        cond = AgentMcpKey.refresh_hash == _hash(raw)
    elif raw.startswith(mcp_keys.PREFIX):
        cond = AgentMcpKey.token_hash == mcp_keys.hash_token(raw)
    else:
        return
    row = db.scalar(select(AgentMcpKey).where(cond, AgentMcpKey.kind == mcp_keys.KIND_OAUTH))
    if row is not None and row.oauth_client_id == client.id:
        mcp_keys.revoke_rows(db, [row])


def client_name_of_key(db: Session, key: AgentMcpKey) -> str:
    """Tên ứng dụng ghi lúc đăng ký — nhật ký MCP dùng cho kết nối OAuth."""
    if int(key.kind or mcp_keys.KIND_MANUAL) != mcp_keys.KIND_OAUTH or not key.oauth_client_id:
        return ""
    client = db.get(AgentOAuthClient, key.oauth_client_id)
    return client.client_name if client is not None else ""
