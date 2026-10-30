"""Chuẩn hóa đường dẫn màn hình thành MẪU route không chứa id (thuần, không đụng DB).

Dùng ở hai nơi để hai phía không lệch nhau: gom ngày (đổi `referer` của nhật ký request thành
mẫu) và nhận sự kiện giao diện (server chuẩn hóa lại dù FE đã chuẩn hóa — FE lỗi cũng không
để lọt id). Luật: bỏ host/query/hash; đoạn toàn số, UUID, hoặc mã phiếu dạng `PO2026001`
→ `:id`; gộp `//`; cắt 120 ký tự. Query bị bỏ vì có thể chứa `q=` từ khóa tìm kiếm.
"""
import re

from app.core.usage_codes import UiApp

MAX_ROUTE_LEN = 120

#  bao-CR-649: màn của app cũ thumua (frontend/) có bản tương ứng ở ERP v2 thì quy về route v2 để báo cáo theo chức
#  năng không tách đôi một màn thành hai. BẢNG DUY NHẤT: đoạn đầu của route thumua → đoạn thay vào (đối chiếu
#  `frontend/src/App.tsx` + `config/cruds.tsx` với `frontend-v2/src/shared/constants/app-routes.ts`, 20/10/2026).
#  Thumua không có bản v2 (me, notifications, import-batches, customs-regulations, /print/...) thì GIỮ NGUYÊN — báo cáo
#  v2 hiện "Giao diện cũ: …". Nguồn app vẫn giữ ở cột `tab_ui_event.app`. Thêm màn: thêm dòng ở đây + một dòng bài kiểm.
_THUMUA_TO_V2 = {
    # Thu mua
    "purchase-requests": "procurement/purchase-requests",
    "survey-requests": "procurement/survey-requests",
    "purchase-orders": "procurement/purchase-orders",
    "surveys": "procurement/surveys",
    "surveys-supplier": "procurement/surveys",      # link cũ trong thông báo, cùng phiếu khảo sát
    "surveys-product": "procurement/surveys",
    "survey-progress": "procurement/survey-progress",
    "purchase-progress": "procurement/purchase-progress",
    "category-assignees": "procurement/category-assignees",
    "customs-prices": "procurement/customs-prices",
    "po-cost-types": "procurement/po-cost-types",
    "pr-lines-report": "procurement/pr-lines-report",
    "survey-report": "procurement/survey-report",
    "documents": "procurement/purchase-orders/:id/documents",   # thumua: chứng từ của MỘT đơn (`/documents?po=`)
    # Sản xuất / danh mục
    "suppliers": "production/suppliers",
    "products": "production/products",
    "units": "production/units",
    "item-groups": "production/item-groups",
    "contracts": "production/contracts",
    # Tài chính
    "payables": "finance/payables",
    "payment-requests": "finance/payment-requests",
    # Nhân sự
    "companies": "hr/companies",
    "departments": "hr/departments",
    "employees": "hr/employees",
    # Kho
    "inventory": "inventory/stock",
    "warehouses": "inventory/warehouses",
    # Hệ thống / báo cáo / hỗ trợ
    "backups": "system/backups",
    "settings": "system/settings",
    "roles": "system/permissions",
    "users": "system/permissions/users",            # thumua `/users/:id` = quyền từng người
    "reports": "report",
    "tickets": "support/tickets",                   # chi tiết `/support/tickets/:id`; danh sách là gốc `/support`
}
#  Route đầy đủ cần sửa lại sau khi thay đoạn đầu (danh sách phiếu hỗ trợ ở v2 đứng ở gốc `/support`).
_EXACT_FIX = {"/support/tickets": "/support"}


def canonical_route(route: str, app: int) -> str:
    """`/purchase-orders/:id` (thumua) → `/procurement/purchase-orders/:id`; app v2 hoặc route lạ → giữ nguyên."""
    if app != int(UiApp.THUMUA) or not route or route == "/":
        return route
    parts = route.split("/", 2)
    head = parts[1]
    replacement = _THUMUA_TO_V2.get(head)
    if not replacement:
        return route
    rest = "/" + parts[2] if len(parts) > 2 and parts[2] else ""
    out = "/" + replacement + rest
    return _EXACT_FIX.get(out, out)[:MAX_ROUTE_LEN]

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
