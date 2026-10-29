"""Tính báo cáo ma trận (đối tượng × tháng) + precompute snapshot.

Đọc báo cáo -> lấy snapshot đã tính (nhanh). Nút "Cập nhật" -> tính lại + lưu (chạy nền)."""
import json
from datetime import datetime

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_order.service import normalize_rate
from .department_label import department_label, load_department_names
from .model import ReportSnapshot


# "Đơn hàng thật" = đã duyệt trở đi (bỏ nháp/chờ duyệt/hủy/từ chối) — dùng cho mọi thống kê đặt hàng
_REAL_PO = ("approved", "partial", "received", "completed")
#  ai-CR-176: mọi truy vấn ĐMH của báo cáo đi kèm điều kiện này — đơn đã xóa mềm không vào số liệu.
_PO_LIVE = PurchaseOrder.is_deleted.is_(False)


def _mk(s):
    return (s or "")[:7]  # 'YYYY-MM'


def _rate_of(it):
    """bao-CR-319 — tỷ giá của dòng hàng; dòng cũ / dòng VNĐ đọc thành 1."""
    return normalize_rate(getattr(it, "exchange_rate", 0))


def order_amount_of(it) -> float:
    """Giá trị ĐẶT HÀNG của một dòng, ĐÃ quy đổi: SL đặt × đơn giá × VAT × tỷ giá.

    bao-CR-437 — đổi từ tên riêng `_amt` sang tên dùng chung được, vì `controller.py`
    từng giữ một bản chép CÙNG TÊN nhưng thiếu tỷ giá. Hai bản đó nuôi hai tab của cùng
    một màn Báo cáo, nên một đơn ngoại tệ ra hai con số tùy người xem bấm vào tab nào.
    """
    # Báo cáo cộng gộp nhiều đơn nên PHẢI quy đổi về một loại tiền, không thì tổng vô nghĩa.
    return float(it.qty_order or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100) * _rate_of(it)


def received_amount_of(it) -> float:
    """Giá trị ĐÃ NHẬN của một dòng, ĐÃ quy đổi — cùng luật với `order_amount_of`."""
    return float(it.qty_received or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100) * _rate_of(it)


#  Tên cũ, giữ cho phần thân tệp này khỏi phải sửa hàng loạt.
_amt = order_amount_of
_recv_amt = received_amount_of


def _rate(part, whole):
    return round(part / whole * 100, 2) if whole else 0


def compute(db: Session, year: str, company_id, full_detail: bool = False) -> dict:
    """full_detail=True: KHÔNG cắt shipping_detail[:300] (dùng cho xuất Excel)."""
    poq = db.query(PurchaseOrder).filter(PurchaseOrder.status.in_(_REAL_PO), _PO_LIVE)
    if company_id:
        poq = poq.filter(PurchaseOrder.company_id == int(company_id))
    if year and year != "all":
        poq = poq.filter(PurchaseOrder.order_date.like(f"{year}%"))
    pos = poq.all()
    po_ids = [p.id for p in pos]
    po_by = {p.id: p for p in pos}
    items = db.query(POItem).filter(POItem.po_id.in_(po_ids)).all() if po_ids else []
    item_by = {it.id: it for it in items}
    delivs = (db.query(PODelivery).filter(PODelivery.po_id.in_(po_ids), PODelivery.received_qty > 0).all()
              if po_ids else [])

    # ---- Danh sách tháng ----
    if year and year != "all":
        months = [f"{year}-{m:02d}" for m in range(1, 13)]
    else:
        s = set()
        for p in pos:
            if p.order_date:
                s.add(_mk(p.order_date))
        for d in delivs:
            if d.received_date:
                s.add(_mk(d.received_date))
        months = sorted(x for x in s if x)
    month_out = [{"key": m, "label": f"{m[5:7]}/{m[:4]}"} for m in months]
    mset = set(months)

    # ================= 1) BỘ PHẬN (đặt hàng / gấp) — theo order_date =================
    dept = {}
    dept_names = load_department_names(db)   # duoc-CR-663: gom theo id, nhãn = tên hiện hành
    for p in pos:
        m = _mk(p.order_date)
        label = department_label(dept_names, p.department_id, p.department)
        if m not in mset or not label:   # bỏ dòng phòng ban rỗng ("(Không rõ)")
            continue
        r = dept.setdefault(label, {"key": label, "department_id": int(p.department_id or 0),
                                    "m": {}, "orders": 0, "urgent": 0})
        c = r["m"].setdefault(m, {"orders": 0, "urgent": 0})
        c["orders"] += 1
        r["orders"] += 1
        if p.is_urgent:
            c["urgent"] += 1
            r["urgent"] += 1
    for r in dept.values():
        for c in r["m"].values():
            c["rate"] = _rate(c["urgent"], c["orders"])
        r["rate"] = _rate(r["urgent"], r["orders"])
        r["warn"] = r["rate"] > 30
    department = sorted(dept.values(), key=lambda x: -x["orders"])

    # ================= per-delivery helpers =================
    def deliv_dim(dimfn, metricfn):
        """Gom deliveries theo key(dimfn) × tháng; metricfn(cell, delivery, item)."""
        agg = {}
        for d in delivs:
            m = _mk(d.received_date)
            if m not in mset:
                continue
            po = po_by.get(d.po_id)
            it = item_by.get(d.po_item_id)
            key = dimfn(po, it)
            if not key or key == "(Không rõ)":   # bỏ dòng NSPT/NCC/loại rỗng
                continue
            r = agg.setdefault(key, {"key": key, "m": {}})
            c = r["m"].setdefault(m, {})
            metricfn(c, r, d, it)
        return agg

    # ================= 2) NCC (giao dịch / trễ theo quy định) =================
    def sup_metric(c, r, d, it):
        c["trans"] = c.get("trans", 0) + 1
        r["trans"] = r.get("trans", 0) + 1
        if (d.diff_regulated or 0) < 0:
            c["late"] = c.get("late", 0) + 1
            r["late"] = r.get("late", 0) + 1
    sup_agg = deliv_dim(lambda po, it: (po.supplier_name or po.supplier_code) if po else "(Không rõ)", sup_metric)
    for r in sup_agg.values():
        r.setdefault("trans", 0); r.setdefault("late", 0)
        for c in r["m"].values():
            c["rate"] = _rate(c.get("late", 0), c.get("trans", 0))
        r["rate"] = _rate(r["late"], r["trans"])
        r["warn"] = r["rate"] > 30
    supplier = sorted(sup_agg.values(), key=lambda x: -x["trans"])

    # ================= 3) NSPT (số đơn giao / trễ-đúng-sớm) =================
    def nspt_metric(c, r, d, it):
        dv = d.diff_regulated or 0
        for k in ("orders", "late", "ontime", "early"):
            c.setdefault(k, 0)
        c["orders"] += 1; r["orders"] = r.get("orders", 0) + 1
        if dv < 0:
            c["late"] += 1; r["late"] = r.get("late", 0) + 1
        elif dv == 0:
            c["ontime"] += 1; r["ontime"] = r.get("ontime", 0) + 1
        else:
            c["early"] += 1; r["early"] = r.get("early", 0) + 1
    nspt_agg = deliv_dim(lambda po, it: (po.nspt or "(Không rõ)") if po else "(Không rõ)", nspt_metric)
    for r in nspt_agg.values():
        for k in ("orders", "late", "ontime", "early"):
            r.setdefault(k, 0)
        for c in r["m"].values():
            c["rate"] = _rate(c.get("late", 0), c.get("orders", 0))
        r["rate"] = _rate(r["late"], r["orders"])
    nspt = sorted(nspt_agg.values(), key=lambda x: -x["orders"])

    # ================= 4) PHÂN LOẠI VTBB/NL (tần suất mua / chi phí) =================
    def ig_metric(c, r, d, it):
        c["trans"] = c.get("trans", 0) + 1
        r["trans"] = r.get("trans", 0) + 1
        cost = _recv_amt(it) if it else 0
        c["cost"] = round(c.get("cost", 0) + cost, 2)
        r["cost"] = round(r.get("cost", 0) + cost, 2)
    ig_agg = deliv_dim(lambda po, it: (it.item_group or "(Không rõ)") if it else "(Không rõ)", ig_metric)
    for r in ig_agg.values():
        r.setdefault("trans", 0); r.setdefault("cost", 0)
    item_group = sorted(ig_agg.values(), key=lambda x: -x["cost"])

    # ================= 5) CHI PHÍ VẬN CHUYỂN (theo đơn vị VC) =================
    ship_agg = {}
    ship_detail = []
    for d in delivs:
        if not (d.carrier_code and float(d.shipping_amount or 0) > 0):
            continue
        m = _mk(d.received_date)
        if m not in mset:
            continue
        po = po_by.get(d.po_id); it = item_by.get(d.po_item_id)
        key = d.carrier_name or d.carrier_code
        r = ship_agg.setdefault(key, {"key": key, "m": {}, "freq": 0, "order_value": 0.0, "ship_cost": 0.0})
        c = r["m"].setdefault(m, {"freq": 0, "order_value": 0.0, "ship_cost": 0.0})
        ov = _recv_amt(it) if it else 0
        sc = float(d.shipping_amount or 0)
        c["freq"] += 1; r["freq"] += 1
        c["order_value"] = round(c["order_value"] + ov, 2); r["order_value"] = round(r["order_value"] + ov, 2)
        c["ship_cost"] = round(c["ship_cost"] + sc, 2); r["ship_cost"] = round(r["ship_cost"] + sc, 2)
        ship_detail.append({
            "carrier": key, "month": f"{m[5:7]}/{m[:4]}",
            "product_code": it.product_code if it else "", "misa_code": po.misa_code if po else "",
            "invoice_no": (d.invoice_no or (it.invoice_no if it else "")), "received_date": d.received_date,
            "qty_order": float(it.qty_order or 0) if it else 0, "qty_received": float(d.received_qty or 0),
            "order_amount": ov, "ship_amount": sc, "rate": _rate(sc, ov),
        })
    for r in ship_agg.values():
        for c in r["m"].values():
            c["rate"] = _rate(c["ship_cost"], c["order_value"])
        r["rate"] = _rate(r["ship_cost"], r["order_value"])
    shipping = sorted(ship_agg.values(), key=lambda x: -x["ship_cost"])

    return {
        "computed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "year": year, "months": month_out,
        "department": department, "supplier": supplier, "nspt": nspt,
        "item_group": item_group, "shipping": shipping,
        "shipping_detail": ship_detail if full_detail else ship_detail[:300],
    }


def compute_nspt_range(db: Session, date_from: str, date_to: str, company_id) -> list:
    """Giao hàng theo NSPT trong khoảng NGÀY [date_from, date_to] (YYYY-MM-DD).

    Tính realtime từ deliveries (không snapshot) — dùng cho bộ lọc khoảng ngày tab NSPT.
    So sánh chuỗi ISO YYYY-MM-DD hợp lệ về thứ tự."""
    dq = (db.query(PODelivery)
          .filter(PODelivery.received_qty > 0,
                  PODelivery.received_date >= date_from,
                  PODelivery.received_date <= date_to))
    delivs = dq.all()
    po_ids = list({d.po_id for d in delivs})
    if not po_ids:
        return []
    poq = db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(po_ids), PurchaseOrder.status.in_(_REAL_PO), _PO_LIVE)
    if company_id:
        poq = poq.filter(PurchaseOrder.company_id == int(company_id))
    po_by = {p.id: p for p in poq.all()}

    agg = {}
    for d in delivs:
        po = po_by.get(d.po_id)
        if po is None:  # bị loại bởi filter công ty / đơn không hợp lệ
            continue
        if not po.nspt:   # bỏ NSPT rỗng
            continue
        key = po.nspt
        r = agg.setdefault(key, {"key": key, "orders": 0, "late": 0, "ontime": 0, "early": 0})
        dv = d.diff_regulated or 0
        r["orders"] += 1
        if dv < 0:
            r["late"] += 1
        elif dv == 0:
            r["ontime"] += 1
        else:
            r["early"] += 1
    for r in agg.values():
        r["rate"] = _rate(r["late"], r["orders"])
    return sorted(agg.values(), key=lambda x: -x["orders"])


def compute_ig_range(db: Session, date_from: str, date_to: str, company_id) -> list:
    """Tần suất mua & chi phí theo LOẠI VTBB/NL trong khoảng NGÀY [date_from, date_to] (YYYY-MM-DD).

    Tính realtime từ deliveries theo received_date — dùng cho bộ lọc khoảng ngày tab Phân loại."""
    delivs = (db.query(PODelivery)
              .filter(PODelivery.received_qty > 0,
                      PODelivery.received_date >= date_from,
                      PODelivery.received_date <= date_to)
              .all())
    po_ids = list({d.po_id for d in delivs})
    if not po_ids:
        return []
    poq = db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(po_ids), PurchaseOrder.status.in_(_REAL_PO), _PO_LIVE)
    if company_id:
        poq = poq.filter(PurchaseOrder.company_id == int(company_id))
    ok_po = {p.id for p in poq.all()}
    item_by = {it.id: it for it in db.query(POItem).filter(POItem.po_id.in_(po_ids)).all()}

    agg = {}
    for d in delivs:
        if d.po_id not in ok_po:  # bị loại bởi filter công ty
            continue
        it = item_by.get(d.po_item_id)
        key = it.item_group if it else None
        if not key:   # bỏ loại VTBB/NL rỗng
            continue
        r = agg.setdefault(key, {"key": key, "trans": 0, "cost": 0.0})
        r["trans"] += 1
        r["cost"] = round(r["cost"] + (_recv_amt(it) if it else 0), 2)
    return sorted(agg.values(), key=lambda x: -x["cost"])


def compute_sup_range(db: Session, date_from: str, date_to: str, company_id) -> list:
    """Giao dịch & trễ theo NCC trong khoảng NGÀY [date_from, date_to] (YYYY-MM-DD).

    Tính realtime từ deliveries theo received_date — dùng cho bộ lọc khoảng ngày tab NCC."""
    delivs = (db.query(PODelivery)
              .filter(PODelivery.received_qty > 0,
                      PODelivery.received_date >= date_from,
                      PODelivery.received_date <= date_to)
              .all())
    po_ids = list({d.po_id for d in delivs})
    if not po_ids:
        return []
    poq = db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(po_ids), PurchaseOrder.status.in_(_REAL_PO), _PO_LIVE)
    if company_id:
        poq = poq.filter(PurchaseOrder.company_id == int(company_id))
    po_by = {p.id: p for p in poq.all()}

    agg = {}
    for d in delivs:
        po = po_by.get(d.po_id)
        if po is None:  # bị loại bởi filter công ty / đơn không hợp lệ
            continue
        key = po.supplier_name or po.supplier_code
        if not key:   # bỏ NCC rỗng
            continue
        r = agg.setdefault(key, {"key": key, "trans": 0, "late": 0})
        r["trans"] += 1
        if (d.diff_regulated or 0) < 0:
            r["late"] += 1
    for r in agg.values():
        r["rate"] = _rate(r["late"], r["trans"])
    return sorted(agg.values(), key=lambda x: -x["trans"])


def compute_dept_range(db: Session, date_from: str, date_to: str, company_id) -> list:
    """Đặt hàng & đơn gấp theo BỘ PHẬN trong khoảng NGÀY [date_from, date_to] (YYYY-MM-DD).

    Tính realtime từ PurchaseOrder theo order_date — dùng cho bộ lọc khoảng ngày tab Bộ phận."""
    poq = db.query(PurchaseOrder).filter(
        PurchaseOrder.order_date >= date_from,
        PurchaseOrder.order_date <= date_to,
        PurchaseOrder.status.in_(_REAL_PO), _PO_LIVE,
    )
    if company_id:
        poq = poq.filter(PurchaseOrder.company_id == int(company_id))

    agg = {}
    dept_names = load_department_names(db)   # duoc-CR-663: gom theo id, nhãn = tên hiện hành
    for p in poq.all():
        label = department_label(dept_names, p.department_id, p.department)
        if not label:   # bỏ phòng ban rỗng
            continue
        r = agg.setdefault(label, {"key": label, "department_id": int(p.department_id or 0),
                                   "orders": 0, "urgent": 0})
        r["orders"] += 1
        if p.is_urgent:
            r["urgent"] += 1
    for r in agg.values():
        r["rate"] = _rate(r["urgent"], r["orders"])
    return sorted(agg.values(), key=lambda x: -x["orders"])


# ===== Báo cáo Yêu cầu mua hàng (PYC) / Yêu cầu khảo sát (YCKS) theo phòng ban =====
# Tính live + apply_scope theo user (dept thấy phòng mình, company/all thấy toàn cty) — KHÔNG cache snapshot.

# Bộ trạng thái đúng theo enum thật trong DB (để Tổng = tổng các cột)
_REQ_STATUS = {
    "pyc": ["draft", "submitted", "approved", "dispatched", "processing", "purchasing", "purchased", "completed", "rejected", "cancelled"],
    "ycks": ["draft", "submitted", "processing", "survey_done", "pr_created", "done", "cancelled"],
}


def _req_model(kind):
    if kind == "ycks":
        from app.modules.survey_request.model import SurveyRequest
        return SurveyRequest, "survey_request"
    from app.modules.purchase_request.model import PurchaseRequest
    return PurchaseRequest, "purchase_request"


def report_dept_scope(db, user):
    """Phạm vi PHÒNG BAN cho báo cáo Bộ phận / Yêu cầu mua hàng / Yêu cầu báo giá.

    None  -> xem MỌI phòng ban (thu mua / quản lý công ty: report scope company|all).
    set() -> chỉ các phòng ban được xem (phòng ban YÊU CẦU / trưởng bộ phận: report scope dept)
             = phòng ban của chính mình + 'Phòng ban được xem' cấp thêm."""
    from app.core.auth import get_perm_profile
    prof = get_perm_profile(db, user)
    allow: set = set()
    for g in prof.get("grants", []):
        p = g["perms"].get("report")
        if not p or not p.get("read"):
            continue
        if p.get("scope", "own") in ("all", "company"):
            return None   # thấy hết
        if prof.get("dept_name"):
            allow.add(prof["dept_name"])
        # CR-086: báo cáo gom dòng theo TÊN phòng (khóa `key` cũng là tên) nên phạm vi ở đây
        # vẫn là tập TÊN — lấy `department_name` chứ không lấy `department` (nay là id).
        # Gom theo id là việc của lần dựng lại màn Báo cáo ở frontend-v2 (N-008).
        for d in ((g.get("scope") or {}).get("inc") or {}).get("department_name", []) or []:
            allow.add(d)
    return allow


def _req_scoped_rows(db, kind, user, *, company_id=None, year=None, date_from=None, date_to=None):
    """Lấy các phiếu (PYC/YCKS) theo công ty/năm/khoảng ngày. Báo cáo = TOÀN CÔNG TY (không áp scope user)."""
    Model, _entity = _req_model(kind)
    q = db.query(Model)
    if hasattr(Model, "is_deleted"):
        q = q.filter(Model.is_deleted == False)   # BỎ phiếu đã xóa mềm (đồng bộ với danh sách)
    if company_id:
        q = q.filter(Model.company_id == int(company_id))
    if year and year != "all":
        q = q.filter(Model.request_date.like(f"{year}%"))
    if date_from and date_to:
        q = q.filter(Model.request_date >= date_from, Model.request_date <= date_to)
    return q.all()


def _blank_cell(statuses):
    d = {"total": 0}
    for s in statuses:
        d[s] = 0
    return d


def compute_request_matrix(db, kind, year, company_id, user) -> dict:
    """Ma trận phòng ban × tháng, đếm phiếu theo trạng thái (+tổng). Shape khớp MatrixPivotTab."""
    kind = "ycks" if kind == "ycks" else "pyc"
    statuses = _REQ_STATUS[kind]
    recs = _req_scoped_rows(db, kind, user, company_id=company_id, year=year)

    if year and year != "all":
        months = [f"{year}-{m:02d}" for m in range(1, 13)]
    else:
        months = sorted({(r.request_date or "")[:7] for r in recs if r.request_date})
    mset = set(months)
    month_out = [{"key": m, "label": f"{m[5:7]}/{m[:4]}"} for m in months]

    agg = {}
    dept_names = load_department_names(db)   # duoc-CR-663: gom theo id, nhãn = tên hiện hành
    for r in recs:
        mo = (r.request_date or "")[:7]
        dept = department_label(dept_names, getattr(r, "department_id", 0), r.department)
        if mo not in mset or not dept:   # bỏ phòng ban rỗng
            continue
        row = agg.setdefault(dept, {"key": dept, "department_id": int(getattr(r, "department_id", 0) or 0),
                                    "m": {}, **_blank_cell(statuses)})
        cell = row["m"].setdefault(mo, _blank_cell(statuses))
        st = r.status if r.status in statuses else None
        cell["total"] += 1
        row["total"] += 1
        if st:
            cell[st] += 1
            row[st] += 1
    rows = sorted(agg.values(), key=lambda x: -x["total"])
    allow = report_dept_scope(db, user)   # phòng ban YÊU CẦU chỉ thấy phòng của mình
    if allow is not None:
        rows = [r for r in rows if r["key"] in allow]
    return {"months": month_out, "rows": rows}


def compute_request_range(db, kind, date_from, date_to, company_id, user) -> list:
    """Bảng phẳng phòng ban trong khoảng ngày (có scope) — cho bộ lọc khoảng ngày."""
    kind = "ycks" if kind == "ycks" else "pyc"
    statuses = _REQ_STATUS[kind]
    recs = _req_scoped_rows(db, kind, user, company_id=company_id, date_from=date_from, date_to=date_to)
    agg = {}
    dept_names = load_department_names(db)   # duoc-CR-663: gom theo id, nhãn = tên hiện hành
    for r in recs:
        dept = department_label(dept_names, getattr(r, "department_id", 0), r.department)
        if not dept:   # bỏ phòng ban rỗng
            continue
        row = agg.setdefault(dept, {"key": dept, "department_id": int(getattr(r, "department_id", 0) or 0),
                                    **_blank_cell(statuses)})
        st = r.status if r.status in statuses else None
        row["total"] += 1
        if st:
            row[st] += 1
    rows = sorted(agg.values(), key=lambda x: -x["total"])
    allow = report_dept_scope(db, user)   # phòng ban YÊU CẦU chỉ thấy phòng của mình
    if allow is not None:
        rows = [r for r in rows if r["key"] in allow]
    return rows


def _pr_lines_base_query(db, user, year, company_id):
    """Truy vấn gốc (dòng YCMH × phiếu) của báo cáo Chi tiết YC mua hàng: bỏ phiếu đã xóa,
    lọc năm / công ty và scope phòng ban. Dùng CHUNG cho bảng phân trang và bản tổng hợp —
    hai đường mà lệch scope là biểu đồ đếm cả dòng bảng không cho xem."""
    from fastapi import HTTPException

    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem

    q = (db.query(PurchaseRequestItem, PurchaseRequest)
         .join(PurchaseRequest, PurchaseRequestItem.pr_id == PurchaseRequest.id)
         .filter(PurchaseRequest.is_deleted == False))
    if company_id:
        #  L3 (review 28/09/2026) — chuỗi không phải số nguyên -> 422, không phải `ValueError`
        #  trần của `int(...)` lộ ra 500.
        cid = str(company_id).strip()
        if not cid.isdigit():
            raise HTTPException(422, "company_id phải là số nguyên")
        q = q.filter(PurchaseRequest.company_id == int(cid))
    if year and year != "all":
        q = q.filter(PurchaseRequest.request_date.like(f"{year}%"))
    allow = report_dept_scope(db, user)   # phòng ban YÊU CẦU chỉ thấy phòng của mình
    if allow is not None:
        q = q.filter(PurchaseRequest.department.in_(list(allow)))   # set rỗng -> IN () = không dòng nào
    return q


def _line_status_values(line_status) -> list[str]:
    """`line_status` một giá trị, chuỗi nối dấu phẩy hoặc danh sách (bao-CR-691: lọc NHIỀU trạng thái)
    -> danh sách mã; `chua_dat` nở thành hai trạng thái chưa đặt."""
    from app.modules.purchase_request.service import LINE_STATUS_IDLE

    raw = line_status if isinstance(line_status, (list, tuple, set)) else str(line_status or "").split(",")
    out: list[str] = []
    for value in raw:
        value = str(value or "").strip()
        for code in (LINE_STATUS_IDLE if value == "chua_dat" else (value,)):
            if code and code not in out:
                out.append(code)
    return out[:20]


def _apply_pr_line_filters(q, *, status=None, line_status=None, assignee=None, search=None):
    """Bốn bộ lọc chi tiết của báo cáo Chi tiết YC mua hàng — dùng chung bảng và tổng hợp."""
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem

    if status:
        q = q.filter(PurchaseRequest.status == status)
    #  "chua_dat" gộp "Chưa tạo đơn mua hàng" + "Chưa đặt hàng" — đúng mục tiêu soi sót; nhiều giá trị (bao-CR-691)
    #  thì lọc IN, một giá trị vẫn ra đúng tập cũ.
    codes = _line_status_values(line_status)
    if codes:
        q = q.filter(PurchaseRequestItem.line_status.in_(codes))
    if assignee:
        q = q.filter(PurchaseRequestItem.assignee == assignee)
    if search:
        like = f"%{search}%"
        q = q.filter(PurchaseRequestItem.product_code.like(like)
                     | PurchaseRequestItem.product_name.like(like)
                     | PurchaseRequest.code.like(like))
    return q


def compute_pr_lines_summary(db, user, *, year=None, company_id=None, status=None,
                             line_status=None, assignee=None, search=None) -> dict:
    """Bản TỔNG HỢP của báo cáo Chi tiết YC mua hàng — nuôi màn biểu đồ (phân hệ Báo cáo).

    Cùng truy vấn gốc + bộ lọc với bảng nên số khớp nhau. Luật đếm:
    - `by_line_status` đếm MỌI dòng, kể cả dòng hủy (để thấy tỷ lệ hủy).
    - Mọi khối còn lại BỎ dòng hủy: dòng hủy không còn là việc phải đặt, cộng vào thì
      "giá trị yêu cầu" phình ra bằng đúng số tiền không ai mua.
    - `idle_*` = dòng CHƯA ĐƯỢC ĐẶT (no_po + not_ordered) — đúng mục tiêu soi sót của báo cáo.
    - `line_status` rỗng ở dữ liệu cũ tính là `no_po`, cùng luật `recompute_status`.
    """
    from app.modules.employee.model import Employee
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
    from app.modules.purchase_request.service import (
        LINE_STATUS_CANCELLED, LINE_STATUS_IDLE, LINE_STATUS_NO_PO)

    q = _apply_pr_line_filters(_pr_lines_base_query(db, user, year, company_id),
                               status=status, line_status=line_status,
                               assignee=assignee, search=search)
    rows = q.with_entities(PurchaseRequest.request_date, PurchaseRequest.department,
                           PurchaseRequestItem.item_group, PurchaseRequestItem.assignee,
                           PurchaseRequestItem.line_status, PurchaseRequestItem.amount,
                           PurchaseRequest.department_id).all()
    dept_names = load_department_names(db)   # duoc-CR-663: gom theo id, nhãn = tên hiện hành

    def bucket():
        return {"lines": 0, "idle_lines": 0, "amount": 0.0, "idle_amount": 0.0}

    def add(b, idle, amount):
        b["lines"] += 1
        b["amount"] += amount
        if idle:
            b["idle_lines"] += 1
            b["idle_amount"] += amount

    total = bucket()
    by_status, by_month, by_dept, by_group, by_assignee = {}, {}, {}, {}, {}
    for request_date, department, item_group, who, ls, amount, department_id in rows:
        ls = ls or LINE_STATUS_NO_PO
        amount = float(amount or 0)
        st = by_status.setdefault(ls, {"code": ls, "lines": 0, "amount": 0.0})
        st["lines"] += 1
        st["amount"] += amount
        if ls == LINE_STATUS_CANCELLED:
            continue
        idle = ls in LINE_STATUS_IDLE
        add(total, idle, amount)
        month = (request_date or "")[:7]
        if len(month) == 7:
            add(by_month.setdefault(month, {"month": month, **bucket()}), idle, amount)
        dept_label = department_label(dept_names, department_id, department) or "(Không rõ)"
        add(by_dept.setdefault(dept_label, {"key": dept_label, **bucket()}), idle, amount)
        add(by_group.setdefault(item_group or "(Không rõ)", {"key": item_group or "(Không rõ)", **bucket()}), idle, amount)
        add(by_assignee.setdefault(who or "", {"code": who or "", **bucket()}), idle, amount)

    codes = [c for c in by_assignee if c]
    names = dict(db.query(Employee.code, Employee.full_name)
                 .filter(Employee.code.in_(codes)).all()) if codes else {}

    def money(d):
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in d.items()}

    def ranked(d):
        return [money(v) for v in sorted(d.values(), key=lambda x: (-x["amount"], str(x.get("key", ""))))]

    return {
        "total": money(total),
        "by_line_status": [money(v) for v in by_status.values()],
        "by_month": [money(by_month[m]) for m in sorted(by_month)],
        "by_department": ranked(by_dept),
        "by_item_group": ranked(by_group),
        # NSTM xếp theo số dòng CHƯA ĐẶT — ai đang ôm việc tồn nhất đứng đầu.
        "by_assignee": [money({**v, "name": names.get(v["code"], "")})
                        for v in sorted(by_assignee.values(),
                                        key=lambda x: (-x["idle_lines"], -x["lines"], x["code"]))],
    }


#  bao-CR-691: cột xuất / bày của bảng Chi tiết YC mua hàng — export dùng đúng thứ tự này.
PR_LINE_EXPORT_COLUMNS = (
    ("pr_code", "Mã YCMH", "text", 16), ("created_date", "Ngày lập", "date", 12), ("company_name", "Pháp nhân", "text", 24),
    ("department", "Bộ phận", "text", 20), ("requester", "Người yêu cầu", "text", 20), ("purpose", "Mục đích", "text", 30),
    ("is_urgent", "Gấp", "bool", 8), ("need_date", "Ngày cần (phiếu)", "date", 12),
    ("head_of_dept_name", "Trưởng bộ phận", "text", 20), ("approver_name", "Người duyệt", "text", 20),
    # Tiến độ dòng đứng TRƯỚC Trạng thái phiếu — khớp thứ tự cột màn v2 (chốt 28/10)
    ("handler_dept_name", "Phòng xử lý", "text", 20), ("line_status", "Tiến độ dòng", "text", 18),
    ("status", "Trạng thái phiếu", "text", 14),
    ("product_code", "Mã hàng", "text", 14), ("product_name", "Tên hàng", "text", 32), ("item_group", "Nhóm hàng", "text", 16),
    ("gram", "Gram", "text", 12), ("unit", "ĐVT", "text", 8), ("warehouse", "Kho nhận", "text", 14),
    ("qty", "SL yêu cầu", "qty", 12), ("price", "Đơn giá", "price", 14), ("vat_pct", "VAT %", "percent", 8),
    ("amount", "Thành tiền", "money", 16), ("required_date", "Ngày cần (dòng)", "date", 12),
    ("expected_date", "Dự kiến có hàng", "date", 12),
    ("qty_ordered", "SL đã đặt", "qty", 12), ("qty_received", "SL đã nhận", "qty", 12),
    ("assignee_name", "NSTM", "text", 18), ("suggested_supplier", "NCC đề xuất", "text", 24),
    ("po_codes", "Mã đơn mua hàng", "text", 24), ("po_count", "Số đơn", "int", 8),
    ("latest_po_supplier", "NCC đơn gần nhất", "text", 24), ("latest_delivery_date", "Hẹn giao gần nhất", "date", 12),
    ("delivery_count", "Số lần nhận hàng", "int", 10), ("progress_note", "Chi tiết tiến độ", "text", 30),
    ("line_note", "Ghi chú dòng", "text", 24),
)


def _pr_line_po_links(db, pr_codes: set[str]) -> tuple[dict, dict]:
    """bao-CR-691: đơn mua hàng của các dòng YCMH trên MỘT trang — gom bằng hai truy vấn, không N+1.

    Ghép theo (mã YCMH, mã hàng): `PurchaseOrder.pr_code` = mã phiếu VÀ dòng đơn cùng `product_code`. Bỏ đơn đã
    xóa / đã hủy và dòng đơn Hủy — đúng luật «đã tạo đơn» của `sync_from_purchase_orders` (màn Tiến độ mua hàng).
    HẠN CHẾ: hai dòng YCMH cùng mã hàng trong một phiếu nhận CÙNG một tập đơn (đơn không ghi dòng YCMH nguồn).
    Trả (links theo (pr_code, product_code) -> {po_codes, supplier mới nhất, po_item_ids}, giao hàng theo po_item_id)."""
    from sqlalchemy import func

    if not pr_codes:
        return {}, {}
    rows = (db.query(PurchaseOrder.code, PurchaseOrder.pr_code, PurchaseOrder.supplier_name, POItem.id, POItem.product_code)
            .join(POItem, POItem.po_id == PurchaseOrder.id)
            .filter(PurchaseOrder.pr_code.in_(list(pr_codes)), PurchaseOrder.is_deleted.is_(False),
                    PurchaseOrder.status != "cancelled", POItem.progress_status != "cancelled")
            .order_by(PurchaseOrder.created_at.asc(), PurchaseOrder.id.asc(), POItem.id.asc()).all())
    links: dict[tuple[str, str], dict] = {}
    for po_code, pr_code, supplier, item_id, product_code in rows:
        if not product_code:
            continue
        link = links.setdefault((pr_code, product_code), {"po_codes": [], "supplier": "", "item_ids": []})
        if po_code not in link["po_codes"]:
            link["po_codes"].append(po_code)
        link["supplier"] = supplier or link["supplier"]       # đơn tạo SAU cùng thắng (đã sắp theo ngày tạo tăng)
        link["item_ids"].append(item_id)
    item_ids = [i for link in links.values() for i in link["item_ids"]]
    deliveries: dict[int, dict] = {}
    if item_ids:
        for item_id, promised, received in (
                db.query(PODelivery.po_item_id, func.max(func.nullif(PODelivery.promised_date, "")),
                         func.sum(case((PODelivery.received_qty > 0, 1), else_=0)))
                .filter(PODelivery.po_item_id.in_(item_ids)).group_by(PODelivery.po_item_id).all()):
            deliveries[int(item_id)] = {"promised": promised or "", "received": int(received or 0)}
    return links, deliveries


def _pr_line_rows(db, pairs, *, show_supplier: bool) -> list[dict]:
    """Dựng các dòng của bảng / file xuất Chi tiết YC mua hàng từ các cặp (dòng YCMH, phiếu).

    Mọi tra cứu phụ (gram, tên NV, pháp nhân, phòng ban, đơn mua hàng, giao hàng) gom MỘT lần cho cả trang.
    `show_supplier` = có `supplier.read`: thiếu thì `suggested_supplier` / `latest_po_supplier` là null."""
    from app.core.central_purchasing import get_central_dept_id
    from app.modules.company.model import Company
    from app.modules.employee.model import Employee
    from app.modules.product.model import Product

    codes = {it.product_code for it, _ in pairs if it.product_code}
    specs = dict(db.query(Product.code, Product.specs).filter(Product.code.in_(codes)).all()) if codes else {}
    emp_codes = {it.assignee for it, _ in pairs if it.assignee}
    emp_names = dict(db.query(Employee.code, Employee.full_name)
                     .filter(Employee.code.in_(emp_codes)).all()) if emp_codes else {}
    emp_ids = {int(pr.head_of_dept_id or 0) for _, pr in pairs} | {int(pr.approver_employee_id or 0) for _, pr in pairs}
    emp_ids.discard(0)
    names_by_id = dict(db.query(Employee.id, Employee.full_name).filter(Employee.id.in_(emp_ids)).all()) if emp_ids else {}
    company_ids = {int(pr.company_id or 0) for _, pr in pairs} - {0}
    companies = dict(db.query(Company.id, Company.name).filter(Company.id.in_(company_ids)).all()) if company_ids else {}
    dept_names = load_department_names(db)
    central_id = get_central_dept_id(db) if any(int(pr.handler_dept_id or 0) == 0 for _, pr in pairs) else 0
    links, deliveries = _pr_line_po_links(db, {pr.code for _, pr in pairs if pr.code})

    rows = []
    for it, pr in pairs:
        link = links.get((pr.code, it.product_code)) if it.product_code else None
        item_ids = link["item_ids"] if link else []
        promised = max((deliveries[i]["promised"] for i in item_ids if i in deliveries), default="")
        handler_id = int(pr.handler_dept_id or 0) or central_id   # 0 = «Thu mua chung» cũ, đọc như phòng thu mua mặc định
        rows.append({
            "id": it.id, "pr_id": pr.id, "pr_code": pr.code, "created_date": pr.request_date,
            "requester": pr.requester, "department": pr.department,
            "product_code": it.product_code, "product_name": it.product_name,
            "warehouse": it.warehouse, "item_group": it.item_group,
            "gram": specs.get(it.product_code, ""),
            "qty": float(it.qty or 0), "price": float(it.price or 0),
            "vat_pct": float(it.vat_pct or 0), "amount": float(it.amount or 0),
            "status": pr.status, "line_status": it.line_status,
            "expected_date": it.expected_date,
            "assignee": it.assignee, "assignee_name": emp_names.get(it.assignee, ""),
            # ── bao-CR-691: phía YCMH ──
            "company_name": companies.get(int(pr.company_id or 0), ""),
            "purpose": pr.purpose or "", "is_urgent": bool(pr.is_urgent), "need_date": pr.need_date or "",
            "head_of_dept_name": names_by_id.get(int(pr.head_of_dept_id or 0)) or (pr.head_of_dept or ""),
            "approver_name": names_by_id.get(int(pr.approver_employee_id or 0), ""),
            "handler_dept_name": dept_names.get(handler_id, ""),
            # ── phía dòng ──
            "unit": it.unit or "", "required_date": it.required_date or "",
            "qty_ordered": float(it.qty_ordered or 0), "qty_received": float(it.qty_received or 0),
            "progress_note": it.progress_note or "", "line_note": it.note or "",
            "suggested_supplier": (pr.suggested_supplier or "") if show_supplier else None,
            # ── ghép đơn mua hàng ──
            "po_codes": ", ".join(link["po_codes"]) if link else None,
            "po_count": len(link["po_codes"]) if link else 0,
            "latest_po_supplier": ((link["supplier"] or None) if link else None) if show_supplier else None,
            "latest_delivery_date": promised or None,
            "delivery_count": sum(deliveries[i]["received"] for i in item_ids if i in deliveries),
        })
    return rows


def _pr_lines_filtered(db, user, *, year, company_id, status, line_status, assignee, search):
    """Truy vấn gốc + bộ lọc chi tiết, kèm danh sách NSTM của dropdown (tính TRƯỚC các lọc chi tiết)."""
    from app.modules.purchase_request.model import PurchaseRequestItem

    q = _pr_lines_base_query(db, user, year, company_id)
    assignees = sorted({a for (a,) in q.with_entities(PurchaseRequestItem.assignee)
                        .filter(PurchaseRequestItem.assignee != "").distinct().all()})
    q = _apply_pr_line_filters(q, status=status, line_status=line_status, assignee=assignee, search=search)
    return q, assignees


def _pr_lines_ordered(q):
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem

    return q.order_by(PurchaseRequest.request_date.desc(), PurchaseRequest.id.desc(), PurchaseRequestItem.id.asc())


def compute_pr_lines(db, user, *, year=None, company_id=None, status=None, line_status=None,
                     assignee=None, search=None, page=1, page_size=50, show_supplier=False) -> dict:
    """Báo cáo Yêu cầu mua hàng theo DÒNG hàng (bao-CR-295 / ticket 23).

    Mục tiêu: NSTM nhìn vào biết MÃ HÀNG nào chưa được đặt (1 phiếu 3 mã thuộc 3 NCC -> phải
    tách 3 ĐMH, dễ đặt sót). Phân trang server (50/trang); scope phòng ban giống báo cáo PYC
    (phòng ban YÊU CẦU chỉ thấy phòng mình). Cột GRAM lấy từ Thông số (specs) của Sản phẩm —
    hệ thống không có trường gram riêng. bao-CR-691: thêm cột phía phiếu / dòng / đơn mua hàng
    (xem `_pr_line_rows`), lọc nhiều trạng thái dòng."""
    from app.modules.employee.model import Employee

    q, assignees = _pr_lines_filtered(db, user, year=year, company_id=company_id, status=status,
                                      line_status=line_status, assignee=assignee, search=search)
    total = q.count()
    page = max(1, int(page or 1)); page_size = max(1, int(page_size or 50))
    pairs = _pr_lines_ordered(q).offset((page - 1) * page_size).limit(page_size).all()
    names = dict(db.query(Employee.code, Employee.full_name)
                 .filter(Employee.code.in_(assignees)).all()) if assignees else {}
    return {"items": _pr_line_rows(db, pairs, show_supplier=show_supplier), "total": total, "page": page,
            "page_size": page_size, "assignees": [{"code": c, "name": names.get(c, "")} for c in assignees]}


def export_pr_lines_rows(db, user, *, year=None, company_id=None, status=None, line_status=None,
                         assignee=None, search=None, show_supplier=False) -> list[dict]:
    """bao-CR-691: mọi dòng theo đúng bộ lọc của bảng (không phân trang) cho file Excel — chặn ở trần dòng xuất."""
    from app.core.export_xlsx import check_row_limit

    q, _ = _pr_lines_filtered(db, user, year=year, company_id=company_id, status=status,
                              line_status=line_status, assignee=assignee, search=search)
    from app.core.status_codes import PR_LINE_STATUS
    from app.modules.purchase_request.export import STATUS_LABEL

    check_row_limit(q.count())
    rows = _pr_line_rows(db, _pr_lines_ordered(q).all(), show_supplier=show_supplier)
    for row in rows:   # tệp Excel đọc bằng mắt: nhãn tiếng Việt thay mã (API giữ mã)
        row["status"] = STATUS_LABEL.get(row["status"], row["status"])
        row["line_status"] = PR_LINE_STATUS.label_of(row["line_status"] or "no_po", row["line_status"] or "")
    return rows


def compute_shipping_detail(db, year, company_id, carrier=None, month=None, page=1, page_size=50) -> dict:
    """Chi tiết chi phí vận chuyển theo từng đơn hàng — PHÂN TRANG phía server (tránh tải full lag trang).
    Trả kèm danh sách đơn vị VC + tháng (để đổ dropdown lọc) tính trên toàn bộ dữ liệu năm/công ty."""
    poq = db.query(PurchaseOrder).filter(PurchaseOrder.status.in_(_REAL_PO), _PO_LIVE)
    if company_id:
        poq = poq.filter(PurchaseOrder.company_id == int(company_id))
    if year and year != "all":
        poq = poq.filter(PurchaseOrder.order_date.like(f"{year}%"))
    pos = poq.all()
    po_ids = [p.id for p in pos]
    empty = {"items": [], "total": 0, "page": 1, "page_size": page_size, "carriers": [], "months": []}
    if not po_ids:
        return empty
    po_by = {p.id: p for p in pos}
    item_by = {it.id: it for it in db.query(POItem).filter(POItem.po_id.in_(po_ids)).all()}
    delivs = db.query(PODelivery).filter(PODelivery.po_id.in_(po_ids), PODelivery.received_qty > 0).all()

    rows = []
    for d in delivs:
        if not (d.carrier_code and float(d.shipping_amount or 0) > 0):
            continue
        m = _mk(d.received_date)
        if not m:
            continue
        po = po_by.get(d.po_id); it = item_by.get(d.po_item_id)
        ov = _recv_amt(it) if it else 0
        sc = float(d.shipping_amount or 0)
        rows.append({
            "carrier": d.carrier_name or d.carrier_code, "month": f"{m[5:7]}/{m[:4]}",
            "product_code": it.product_code if it else "", "misa_code": po.misa_code if po else "",
            "invoice_no": (d.invoice_no or (it.invoice_no if it else "")), "received_date": d.received_date,
            "qty_order": float(it.qty_order or 0) if it else 0, "qty_received": float(d.received_qty or 0),
            "order_amount": ov, "ship_amount": sc, "rate": _rate(sc, ov),
        })
    rows.sort(key=lambda r: r["received_date"] or "", reverse=True)   # mới nhất trước
    carriers = sorted({r["carrier"] for r in rows if r["carrier"]})
    months = sorted({r["month"] for r in rows if r["month"]}, key=lambda mm: mm[3:] + mm[:2])

    filtered = [r for r in rows
                if (not carrier or r["carrier"] == carrier) and (not month or r["month"] == month)]
    total = len(filtered)
    page = max(1, int(page or 1)); page_size = max(1, int(page_size or 50))
    off = (page - 1) * page_size
    return {"items": filtered[off:off + page_size], "total": total,
            "page": page, "page_size": page_size, "carriers": carriers, "months": months}


def _key(year, company_id):
    return f"{year or 'all'}|{company_id or 'all'}"


def _persist_snapshot(db: Session, key: str, data: dict):
    snap = db.query(ReportSnapshot).filter(ReportSnapshot.key == key).first()
    if not snap:
        snap = ReportSnapshot(key=key)
        db.add(snap)
    snap.data = json.dumps(data, ensure_ascii=False)
    snap.computed_at = data["computed_at"]
    db.commit()


# Stale-while-revalidate: đọc snapshot ngay (nhanh), nếu cũ hơn TTL thì tính lại ở background.
_SNAP_TTL = 120           # giây — snapshot cũ hơn ngưỡng này sẽ được tính lại ngầm
_recomputing: set = set()  # các key đang tính lại (chống thundering herd trong 1 tiến trình)


def _is_stale(computed_at: str) -> bool:
    try:
        age = (datetime.now() - datetime.strptime(computed_at, "%Y-%m-%d %H:%M:%S")).total_seconds()
        return age > _SNAP_TTL
    except Exception:
        return True


def _recompute_key(year, company_id):
    """Tính lại + lưu snapshot bằng session RIÊNG (chạy ngoài request, background)."""
    key = _key(year, company_id)
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        _persist_snapshot(db, key, compute(db, year, company_id))
    except Exception:
        pass
    finally:
        db.close()
        _recomputing.discard(key)


def get_snapshot(db: Session, year, company_id, refresh: bool = False, background=None) -> dict:
    """SWR: refresh=1 -> tính đồng bộ (nút 'Cập nhật'). Ngược lại trả snapshot ngay,
    tự tính lại ngầm nếu snapshot cũ hoặc chưa có (lần đầu phải tính đồng bộ)."""
    key = _key(year, company_id)
    snap = db.query(ReportSnapshot).filter(ReportSnapshot.key == key).first()

    if not refresh and snap:
        try:
            data = json.loads(snap.data)
        except Exception:
            data = None
        if data is not None:
            # cũ hơn TTL -> đẩy tính lại ngầm (chỉ 1 lần/key), vẫn trả bản hiện có ngay
            if background is not None and _is_stale(snap.computed_at) and key not in _recomputing:
                _recomputing.add(key)
                background.add_task(_recompute_key, year, company_id)
            return data

    # refresh tay HOẶC chưa có snapshot -> tính đồng bộ rồi trả
    data = compute(db, year, company_id)
    _persist_snapshot(db, key, data)
    return data
