"""Chuẩn hóa đường dẫn màn hình thành MẪU route không chứa id (thuần, không đụng DB).

Dùng ở hai nơi để hai phía không lệch nhau: gom ngày (đổi `referer` của nhật ký request thành
mẫu) và nhận sự kiện giao diện (server chuẩn hóa lại dù FE đã chuẩn hóa — FE lỗi cũng không
để lọt id). Luật: bỏ host/query/hash; đoạn toàn số, UUID, hoặc mã phiếu dạng `PO2026001`
→ `:id`; gộp `//`; cắt 120 ký tự. Query bị bỏ vì có thể chứa `q=` từ khóa tìm kiếm.
"""
import re

from app.core.usage_codes import UiApp

MAX_ROUTE_LEN = 120

#  bao-CR-649: ba chức năng phòng Thu mua làm trên app cũ (frontend/) có route giống hệt v2, chỉ thiếu tiền tố
#  `/procurement` — quy về route v2 để báo cáo không tách đôi một màn thành hai. Route khác của thumua giữ nguyên
#  (báo cáo v2 hiện «Giao diện cũ: …»); `/print/...` hai app đã giống nhau. Nguồn app giữ ở cột `tab_ui_event.app`.
_THUMUA_TO_V2_PREFIX = {"purchase-requests": "procurement", "survey-requests": "procurement",
                        "purchase-orders": "procurement"}


def canonical_route(route: str, app: int) -> str:
    """`/purchase-orders/:id` (thumua) → `/procurement/purchase-orders/:id`; app v2 hoặc route lạ → giữ nguyên."""
    if app != int(UiApp.THUMUA) or not route or route == "/":
        return route
    head = route.split("/", 2)[1]
    prefix = _THUMUA_TO_V2_PREFIX.get(head)
    if not prefix:
        return route
    return ("/" + prefix + route)[:MAX_ROUTE_LEN]

_SCHEME_HOST = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://[^/?#]*")
_UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
_DOC_CODE = re.compile(r"^[A-Za-z]{2,}[-_]?\d+$")
_NUMERIC = re.compile(r"^\d+$")


def normalize_route(raw: str | None) -> str:
    """`/procurement/purchase-orders/129?q=abc#x` → `/procurement/purchase-orders/:id`."""
    if not raw:
        return "/"
    text = _SCHEME_HOST.sub("", str(raw).strip())
    text = text.split("#", 1)[0].split("?", 1)[0]
    parts: list[str] = []
    for seg in text.split("/"):
        if not seg:
            continue
        if seg == ":id" or _NUMERIC.match(seg) or _UUID.match(seg):
            parts.append(":id")
        elif _DOC_CODE.match(seg) and any(c.isdigit() for c in seg) and seg[:2].isupper():
            parts.append(":id")
        else:
            parts.append(seg)
    out = "/" + "/".join(parts)
    return out[:MAX_ROUTE_LEN] or "/"
