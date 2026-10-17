"""Tool `erp_read` — đọc danh sách / chi tiết chứng từ và danh mục ERP cho AI (ai-CR-211, K13 — tầng T3 doc/erp/21 §5.5).

MỘT tool chỉ đọc trên danh sách TRẮNG resource. Mỗi resource khai: hàm đọc danh sách, hàm đọc chi tiết, bộ lọc được
chuyển xuống, bộ trường được trả (gọt bớt trường kỹ thuật / màn hình), đường dẫn màn ERP.

- Danh sách: gọi ĐÚNG hàm route danh sách của màn web ngay trong tiến trình (`route_call.call_route`) — cùng `require`,
  cùng `apply_filters`, cùng `apply_scope` như người đó mở màn. Mỗi lượt tối đa `MAX_PAGES` trang × `MAX_PAGE_SIZE` dòng;
  còn nữa thì `has_more` + `next_page`.
- Chi tiết: YCMH / YCBG / ĐMH đi qua bộ đọc của `procurement_doc_read` (lọc phạm vi, CHỈ ĐỌC) — KHÔNG gọi route chi tiết
  YCMH vì route đó ghi ngầm «phương án 0» (`option_service.ensure_option_zero`). Hợp đồng / NCC / sản phẩm gọi route
  chi tiết (không tác dụng phụ). Ngoài phạm vi và không tồn tại trả CÙNG một câu — không lộ phiếu có tồn tại.
- Nhận hàng (`goods_receipt`) không có màn riêng: đọc bảng qua `apply_scope(GoodsReceipt, "goods_receipt")`.
- Không có đường xuất Excel / ghi nhật ký nào trong danh sách trắng.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from fastapi import HTTPException

from app.core.scoping import apply_scope
from app.core.status_codes import CONTRACT_STATUS, PO_DOCUMENT_STATUS

from .base import ToolContext, ToolSpec

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 50      # ai-CR-213: mặc định MỘT trang × 50 dòng; 5 × 100 chỉ khi AI xin rõ (`pages`, `page_size`)
MAX_PAGES = 5
TEXT_MAX_LEN = 100


def _route(module: str, name: str) -> Callable[[], Callable]:
    def load():
        import importlib

        return getattr(importlib.import_module(f"app.modules.{module}"), name)

    return load


@dataclass(frozen=True)
class Resource:
    key: str
    label: str
    entity: str
    list_path: str
    fields: tuple[str, ...]
    filters: tuple[str, ...]
    list_route: Callable[[], Callable] | None = None
    detail: Callable | None = None            # (ctx, id) -> dict | None (None = không tìm thấy trong phạm vi)
    detail_url: str = ""                      # mẫu đường dẫn chi tiết, `{id}`
    money: tuple[str, ...] = ()               # trường tiền (VND)
    vat: dict = field(default_factory=dict)   # {trường tiền: căn cứ VAT} — chỉ ghi chỗ đã soi công thức
    hide_without_supplier: tuple[str, ...] = ()
    decorate: Callable[[dict], dict] | None = None


# ── nhãn trạng thái ───────────────────────────────────────────────────────────────────────────────────────────────
def _status_labels(entity: str) -> dict:
    from .procurement_doc_tool import _STATUS_LABELS

    return _STATUS_LABELS.get(entity, {})


def _with_status(entity: str):
    def deco(item: dict) -> dict:
        if "status" in item:
            item["status_label"] = _status_labels(entity).get(item["status"], item["status"])
        return item
    return deco


def _po_deco(item: dict) -> dict:
    item = _with_status("purchase_order")(item)
    if "document_status" in item:
        item["document_status_label"] = PO_DOCUMENT_STATUS.labels.get(item["document_status"], item["document_status"])
    return item


def _contract_deco(item: dict) -> dict:
    if "status" in item and "status_label" not in item:
        item["status_label"] = CONTRACT_STATUS.labels.get(item["status"], item["status"])
    return item


# ── đọc chi tiết ──────────────────────────────────────────────────────────────────────────────────────────────────
def _doc_reader(entity: str):
    def read(ctx: ToolContext, oid: int):
        from .procurement_doc_tool import _READERS

        out = _READERS[entity](ctx, "", oid)
        return None if "error" in out else out
    return read


def _route_detail(module: str, name: str, id_param: str):
    def read(ctx: ToolContext, oid: int):
        from .route_call import call_route

        try:
            return call_route(_route(module, name)(), ctx.db, ctx.user, {id_param: oid})
        except HTTPException as e:
            if e.status_code in (403, 404):
                return None
            raise
    return read


def _gr_query(ctx: ToolContext):
    from app.modules.goods_receipt.model import GoodsReceipt

    return apply_scope(ctx.db.query(GoodsReceipt), GoodsReceipt, "goods_receipt", ctx.user, ctx.profile), GoodsReceipt


def _gr_row(r) -> dict:
    return {k: getattr(r, k) for k in RESOURCES["goods_receipt"].fields if hasattr(r, k)}


def _gr_detail(ctx: ToolContext, oid: int):
    q, gr = _gr_query(ctx)
    row = q.filter(gr.id == oid).first()
    return _gr_row(row) if row is not None else None


def _gr_list(ctx: ToolContext, params: dict, page: int, size: int) -> dict:
    q, gr = _gr_query(ctx)
    for key in ("po_code", "product_code", "warehouse_code"):
        if params.get(key):
            q = q.filter(getattr(gr, key).like(f"%{params[key]}%"))
    if params.get("company_id"):
        q = q.filter(gr.company_id == _int(params["company_id"], 0, 0, 2**62))
    if params.get("received_date_from"):
        q = q.filter(gr.received_date >= params["received_date_from"])
    if params.get("received_date_to"):
        q = q.filter(gr.received_date <= params["received_date_to"])
    total = q.count()
    rows = q.order_by(gr.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"total": total, "items": [_gr_row(r) for r in rows]}


RESOURCES: dict[str, Resource] = {r.key: r for r in (
    Resource("purchase_request", "Yêu cầu mua hàng (YCMH)", "purchase_request", "/procurement/purchase-requests",
             fields=("id", "code", "status", "request_date", "need_date", "requester", "department", "purpose",
                     "is_urgent", "total", "company_id"),
             filters=("q", "status", "request_date_from", "request_date_to", "need_date_from", "need_date_to",
                      "company_id", "department_id", "is_urgent", "item_group"),
             list_route=_route("purchase_request.controller", "list_pr"), detail=_doc_reader("purchase_request"),
             detail_url="/procurement/purchase-requests/{id}", money=("total",), vat={"total": "sau VAT"},
             decorate=_with_status("purchase_request")),
    Resource("survey_request", "Yêu cầu báo giá (YCBG)", "survey_request", "/procurement/survey-requests",
             fields=("id", "code", "status", "request_date", "requester", "department", "purpose", "company_id"),
             filters=("q", "status", "request_date_from", "request_date_to", "company_id", "department_id", "item_group"),
             list_route=_route("survey_request.controller", "list_"), detail=_doc_reader("survey_request"),
             detail_url="/procurement/survey-requests/{id}", decorate=_with_status("survey_request")),
    Resource("purchase_order", "Đơn mua hàng (ĐMH)", "purchase_order", "/procurement/purchase-orders",
             fields=("id", "code", "misa_code", "pr_code", "status", "document_status", "order_date", "supplier_code",
                     "supplier_name", "department", "nspt", "amount", "currency", "order_type_label", "company_id"),
             filters=("q", "status", "document_status", "supplier_code", "pr_code", "order_date_from", "order_date_to",
                      "company_id", "department_id", "invoice_no", "item_group"),
             list_route=_route("purchase_order.controller", "list_po"), detail=_doc_reader("purchase_order"),
             detail_url="/procurement/purchase-orders/{id}", money=("amount",),
             hide_without_supplier=("supplier_code", "supplier_name"), decorate=_po_deco),
    Resource("goods_receipt", "Phiếu nhận hàng (GR)", "goods_receipt", "/procurement/purchase-progress",
             fields=("id", "code", "po_code", "product_code", "product_name", "unit", "qty_received", "received_date",
                     "qc_result", "warehouse_code", "company_id"),
             filters=("po_code", "product_code", "warehouse_code", "company_id", "received_date_from",
                      "received_date_to"),
             detail=_gr_detail),
    Resource("supplier", "Nhà cung cấp", "supplier", "/production/suppliers",
             fields=("id", "code", "name", "tax_code", "legal_type_label", "supplier_type", "address", "contact_person",
                     "phone", "payment_terms", "is_active"),
             filters=("name", "code", "tax_code", "supplier_type", "is_active"),
             list_route=_route("supplier.controller", "list_suppliers"),
             detail=_route_detail("supplier.controller", "get_supplier", "sid"), detail_url="/production/suppliers/{id}"),
    Resource("product", "Sản phẩm", "product", "/production/products",
             fields=("id", "code", "name", "item_group", "unit", "hh_code", "hh_name", "specs", "is_active"),
             filters=("search", "item_group", "unit", "is_active"),
             list_route=_route("product.controller", "list_products"),
             detail=_route_detail("product.controller", "get_product", "pid"), detail_url="/production/products/{id}"),
    Resource("contract", "Hợp đồng", "contract", "/production/contracts",
             fields=("id", "code", "title", "party_type_label", "party_code", "party_name", "contract_type_label",
                     "start_date", "end_date", "signed", "status", "status_label", "expiry_label", "company_id"),
             filters=("status", "party_code", "party_name", "contract_type", "signed", "expiry", "end_date_from",
                      "end_date_to"),
             list_route=_route("contract.controller", "list_"),
             detail=_route_detail("contract.controller", "get_", "cid"), detail_url="/production/contracts/{id}",
             decorate=_contract_deco),
)}


def _trim(ctx: ToolContext, res: Resource, row: dict, see_supplier: bool) -> dict:
    item = {k: row[k] for k in res.fields if k in row}
    if not see_supplier:
        for k in res.hide_without_supplier:
            item.pop(k, None)
    if res.decorate is not None:
        item = res.decorate(item)
    if res.detail_url and item.get("id"):
        item["url"] = res.detail_url.format(id=item["id"])
    return item


def _clean_filters(res: Resource, raw: dict) -> tuple[dict, list[str]]:
    out, ignored = {}, []
    for k, v in (raw or {}).items():
        if k not in res.filters:
            ignored.append(str(k))
            continue
        if v is None or v == "":
            continue
        out[k] = str(v).strip()[:TEXT_MAX_LEN] if not isinstance(v, bool) else ("true" if v else "false")
    return out, ignored


def _int(raw, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(int(raw), hi))
    except (TypeError, ValueError):
        return default


def _list_page(ctx: ToolContext, res: Resource, params: dict, page: int, size: int) -> dict:
    if res.list_route is None:
        return _gr_list(ctx, params, page, size)
    from .route_call import call_route

    return call_route(res.list_route(), ctx.db, ctx.user, {**params, "page": page, "page_size": size})


def _erp_read(ctx: ToolContext, args: dict) -> dict:
    key = str(args.get("resource") or "").strip().lower()
    res = RESOURCES.get(key)
    if res is None:
        return {"error": f"resource {key!r} không có trong danh sách đọc được. Chọn: "
                         + ", ".join(f"{k} ({r.label})" for k, r in RESOURCES.items()) + "."}
    if not ctx.can(res.entity):
        return {"denied": True, "error": f"Không có quyền xem «{res.label}» (cần quyền đọc {res.entity}) — nhờ quản trị "
                                         "gán vai trò."}
    see_supplier = ctx.can("supplier")
    meta = {"resource": res.key, "label": res.label, "currency": "VND"}
    if res.money:
        meta["money_fields"] = {m: res.vat.get(m, "") for m in res.money}

    if args.get("id") not in (None, ""):
        oid = _int(args.get("id"), 0, 0, 2**62)
        found = res.detail(ctx, oid) if oid and res.detail is not None else None
        if found is None:
            return {"error": f"Không tìm thấy {res.label} id {args.get('id')} trong phạm vi dữ liệu của bạn — id sai, hoặc "
                             "nằm ngoài quyền xem."}
        if res.key in ("purchase_request", "survey_request", "purchase_order"):
            #  Bộ đọc procurement_doc_read đã gọt + có url + nhãn trạng thái; dàn phẳng `header` cho cùng khuôn `item`.
            item = {**(found.get("header") or {}), "id": oid, "lines": found.get("lines") or [],
                    "line_count": found.get("total", 0), "totals": found.get("totals") or {}}
            for extra in ("payables", "payable_note", "progress_summary", "note", "supplier_note"):
                if extra in found:
                    item[extra] = found[extra]
            return {**meta, "item": item}
        return {**meta, "item": _trim(ctx, res, found, see_supplier)}

    params, ignored = _clean_filters(res, args.get("filters") if isinstance(args.get("filters"), dict) else {})
    page = _int(args.get("page"), 1, 1, 10_000)
    size = _int(args.get("page_size"), DEFAULT_PAGE_SIZE, 1, MAX_PAGE_SIZE)
    pages = _int(args.get("pages"), 1, 1, MAX_PAGES)
    items, total, read = [], 0, 0
    try:
        for p in range(page, page + pages):
            data = _list_page(ctx, res, params, p, size)
            total = int(data.get("total") or 0)
            rows = data.get("items") or []
            items += [_trim(ctx, res, r, see_supplier) for r in rows]
            read += 1
            if len(rows) < size or p * size >= total:
                break
    except HTTPException as e:
        if e.status_code == 403:
            return {"denied": True, "error": f"«{res.label}»: {e.detail}"}
        return {"error": f"«{res.label}»: {e.detail}"}
    last = page + read - 1
    has_more = last * size < total
    out = {**meta, "link": res.list_path, "total": total, "page": page, "page_size": size, "pages_read": read,
           "returned": len(items), "has_more": has_more, "items": items}
    if has_more:
        out["next_page"] = last + 1
        out["note"] = (f"Còn {total - last * size} dòng: gọi lại với page={last + 1} (tối đa {MAX_PAGES} trang × "
                       f"{MAX_PAGE_SIZE} dòng mỗi lượt), hoặc thêm bộ lọc cho hẹp.")
    if not see_supplier and res.hide_without_supplier:
        out["hidden"] = "Ẩn mã / tên nhà cung cấp vì người hỏi không có quyền xem NCC."
    if ignored:
        out["ignored_filters"] = ignored
        out["allowed_filters"] = list(res.filters)
    return out


def _description() -> str:
    parts = [f"{k} = {r.label} [lọc: {', '.join(r.filters)}]" for k, r in RESOURCES.items()]
    return ("Đọc DANH SÁCH hoặc CHI TIẾT (truyền id) chứng từ / danh mục ERP đúng như màn web, đúng phạm vi quyền người hỏi "
            "— dùng để đào sâu từng phiếu (vd mở chi tiết một ĐMH, phiếu đang chờ duyệt của một phòng). Số tổng hợp thì "
            "dùng report_summary / dataset_query. Resource: " + " | ".join(parts)
            + f". Mặc định một trang {DEFAULT_PAGE_SIZE} dòng; chỉ xin thêm (tối đa {MAX_PAGES} trang × {MAX_PAGE_SIZE} dòng) "
              "khi thật cần đọc hết — lọc hẹp trước, mỗi khóa có ngân sách dòng mỗi phút. Còn nữa thì has_more + "
              "next_page. Ngày YYYY-MM-DD; mỗi dòng có url mở màn chi tiết.")


ERP_READ_SPEC = ToolSpec(
    name="erp_read",
    description=_description(),
    parameters={
        "type": "object",
        "properties": {
            "resource": {"type": "string", "enum": list(RESOURCES),
                         "description": "; ".join(f"{k}: {r.label}" for k, r in RESOURCES.items())},
            "id": {"type": "integer", "description": "Có id = đọc chi tiết một bản ghi; bỏ trống = đọc danh sách."},
            "filters": {"type": "object", "description": "{tên bộ lọc: giá trị} — chỉ các tên khai ở mô tả resource."},
            "page": {"type": "integer", "description": "Trang bắt đầu (mặc định 1)."},
            "page_size": {"type": "integer", "description": f"Số dòng mỗi trang (mặc định {DEFAULT_PAGE_SIZE}, trần "
                                                            f"{MAX_PAGE_SIZE})."},
            "pages": {"type": "integer", "description": f"Đọc liền bao nhiêu trang (mặc định 1, trần {MAX_PAGES})."},
        },
        "required": ["resource"],
    },
    handler=_erp_read,
)
