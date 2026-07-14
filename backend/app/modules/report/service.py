"""Tính báo cáo ma trận (đối tượng × tháng) + precompute snapshot.

Đọc báo cáo -> lấy snapshot đã tính (nhanh). Nút "Cập nhật" -> tính lại + lưu (chạy nền)."""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from .model import ReportSnapshot


# "Đơn hàng thật" = đã duyệt trở đi (bỏ nháp/chờ duyệt/hủy/từ chối) — dùng cho mọi thống kê đặt hàng
_REAL_PO = ("approved", "partial", "received", "completed")


def _mk(s):
    return (s or "")[:7]  # 'YYYY-MM'


def _amt(it):
    return float(it.qty_order or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)


def _recv_amt(it):
    return float(it.qty_received or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)


def _rate(part, whole):
    return round(part / whole * 100, 2) if whole else 0


def compute(db: Session, year: str, company_id) -> dict:
    poq = db.query(PurchaseOrder).filter(PurchaseOrder.status.in_(_REAL_PO))
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
    for p in pos:
        m = _mk(p.order_date)
        if m not in mset or not p.department:   # bỏ dòng phòng ban rỗng ("(Không rõ)")
            continue
        r = dept.setdefault(p.department, {"key": p.department, "m": {}, "orders": 0, "urgent": 0})
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
            "invoice_no": it.invoice_no if it else "", "received_date": d.received_date,
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
        "item_group": item_group, "shipping": shipping, "shipping_detail": ship_detail[:300],
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
    poq = db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(po_ids), PurchaseOrder.status.in_(_REAL_PO))
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
    poq = db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(po_ids), PurchaseOrder.status.in_(_REAL_PO))
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
    poq = db.query(PurchaseOrder).filter(PurchaseOrder.id.in_(po_ids), PurchaseOrder.status.in_(_REAL_PO))
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
        PurchaseOrder.status.in_(_REAL_PO),
    )
    if company_id:
        poq = poq.filter(PurchaseOrder.company_id == int(company_id))

    agg = {}
    for p in poq.all():
        if not p.department:   # bỏ phòng ban rỗng
            continue
        r = agg.setdefault(p.department, {"key": p.department, "orders": 0, "urgent": 0})
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
    "pyc": ["draft", "submitted", "approved", "processing", "completed", "rejected", "cancelled"],
    "ycks": ["draft", "submitted", "processing", "survey_done", "pr_created", "done", "cancelled"],
}


def _req_model(kind):
    if kind == "ycks":
        from app.modules.survey_request.model import SurveyRequest
        return SurveyRequest, "survey_request"
    from app.modules.purchase_request.model import PurchaseRequest
    return PurchaseRequest, "purchase_request"


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
    for r in recs:
        mo = (r.request_date or "")[:7]
        if mo not in mset or not r.department:   # bỏ phòng ban rỗng
            continue
        dept = r.department
        row = agg.setdefault(dept, {"key": dept, "m": {}, **_blank_cell(statuses)})
        cell = row["m"].setdefault(mo, _blank_cell(statuses))
        st = r.status if r.status in statuses else None
        cell["total"] += 1
        row["total"] += 1
        if st:
            cell[st] += 1
            row[st] += 1
    rows = sorted(agg.values(), key=lambda x: -x["total"])
    return {"months": month_out, "rows": rows}


def compute_request_range(db, kind, date_from, date_to, company_id, user) -> list:
    """Bảng phẳng phòng ban trong khoảng ngày (có scope) — cho bộ lọc khoảng ngày."""
    kind = "ycks" if kind == "ycks" else "pyc"
    statuses = _REQ_STATUS[kind]
    recs = _req_scoped_rows(db, kind, user, company_id=company_id, date_from=date_from, date_to=date_to)
    agg = {}
    for r in recs:
        if not r.department:   # bỏ phòng ban rỗng
            continue
        row = agg.setdefault(r.department, {"key": r.department, **_blank_cell(statuses)})
        st = r.status if r.status in statuses else None
        row["total"] += 1
        if st:
            row[st] += 1
    return sorted(agg.values(), key=lambda x: -x["total"])


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
