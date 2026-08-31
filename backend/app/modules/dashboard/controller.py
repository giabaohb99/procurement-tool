from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def stats(days: str = "30", db: Session = Depends(get_db), user=Depends(get_current_user)):
    from app.modules.employee.model import Employee
    from app.modules.product.model import Product
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.supplier.model import Supplier
    from app.modules.survey.model import Survey
    from app.modules.purchase_order.model import PurchaseOrder

    since = None
    if days != "all":
        try:
            n_days = int(days)
            since = datetime.now() - timedelta(days=n_days)
        except ValueError:
            pass

    def filter_since(query, model):
        if since is not None:
            return query.filter(model.created_at >= since)
        return query

    # General statistics
    suppliers_count = filter_since(db.query(Supplier), Supplier).count()
    products_count = filter_since(db.query(Product), Product).count()
    employees_count = filter_since(db.query(Employee), Employee).count()

    # PR / Purchase Request stats
    pr_query = db.query(PurchaseRequest)
    pr_total = filter_since(pr_query, PurchaseRequest).count()
    pr_pending = filter_since(pr_query.filter(PurchaseRequest.status == "submitted"), PurchaseRequest).count()
    # CR-034: "đã duyệt" gồm cả phiếu chờ điều phối lẫn đã điều phối (khỏi tụt số so với trước)
    pr_approved = filter_since(pr_query.filter(PurchaseRequest.status.in_(["approved", "dispatched"])), PurchaseRequest).count()

    # Survey stats (Real data)
    survey_query = db.query(Survey)
    survey_pending = filter_since(survey_query.filter(Survey.status == "submitted"), Survey).count()

    # PO / Purchase Order stats (Real data)
    po_query = db.query(PurchaseOrder)
    po_ordered = filter_since(po_query.filter(PurchaseOrder.status.in_(["approved", "partial", "received"])), PurchaseOrder).count()
    po_delivered = filter_since(po_query.filter(PurchaseOrder.status == "received"), PurchaseOrder).count()
    po_partial = filter_since(po_query.filter(PurchaseOrder.status == "partial"), PurchaseOrder).count()
    po_completed = filter_since(po_query.filter(PurchaseOrder.status == "completed"), PurchaseOrder).count()

    # Generate trend data based on timeframe
    trends = []
    end_date = datetime.now()
    if days == "7":
        steps = 7
        interval_days = 1
    elif days == "30":
        steps = 6
        interval_days = 5
    else:  # all
        steps = 6
        interval_days = 30

    for i in range(steps - 1, -1, -1):
        d = end_date - timedelta(days=i * interval_days)
        d_str = d.strftime("%d/%m")

        start_range = d.replace(hour=0, minute=0, second=0)
        end_range = d.replace(hour=23, minute=59, second=59)
        if interval_days > 1:
            start_range = (d - timedelta(days=interval_days - 1)).replace(hour=0, minute=0, second=0)

        pr_cnt = db.query(PurchaseRequest).filter(
            PurchaseRequest.created_at >= start_range,
            PurchaseRequest.created_at <= end_range
        ).count()

        po_cnt = db.query(PurchaseOrder).filter(
            PurchaseOrder.created_at >= start_range,
            PurchaseOrder.created_at <= end_range
        ).count()

        trends.append({"label": d_str, "pr": pr_cnt, "po": po_cnt})

    return success({
        "suppliers": suppliers_count,
        "products": products_count,
        "employees": employees_count,
        "pr_total": pr_total,
        "pr_pending": pr_pending,
        "pr_processing": pr_approved,
        "survey_pending": survey_pending,
        "po_ordered": po_ordered,
        "po_delivered": po_delivered,
        "po_partial": po_partial,
        "po_completed": po_completed,
        "trends": trends,
    })


@router.get("/overview")
def overview(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Tổng hợp trang chủ — LỌC THEO QUYỀN + PHẠM VI. Khối nào user không có quyền Xem
    entity tương ứng → trả rỗng (FE tự ẩn). Số liệu tính trong phạm vi của user."""
    from app.core.auth import get_perm_profile
    from app.core.scoping import apply_scope
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
    from app.modules.purchase_order.model import PurchaseOrder, POItem, PODelivery
    from app.modules.payable.model import Payable
    from app.modules.payable.service import ST_PAID
    from app.modules.contract.model import Contract
    from app.modules.inventory.model import Inventory
    from app.modules.survey.model import Survey
    from app.modules.alert.controller import build as build_alerts

    prof = get_perm_profile(db, user)

    def can(e):
        return bool(prof["perms_union"].get(e, {}).get("read"))

    today = datetime.now().date()
    tstr = today.strftime("%Y-%m-%d")
    in7 = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    in30 = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    def item_amt(it):
        a = float(it.amount or 0)
        return a if a > 0 else float(it.qty_order or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)

    kpi = {}
    cost_12m, categories, top_suppliers, dept_spend = [], [], [], []
    po_status, ap_aging, recent_pos, recent_prs, low_stock = [], [], [], [], []
    top_debt_suppliers = []
    pending_prs_list, pending_srs_list, pending_surveys_list, late_deliveries_list = [], [], [], []
    target_year = str(today.year)

    # ===== Yêu cầu mua =====
    if can("purchase_request"):
        prq = apply_scope(db.query(PurchaseRequest), PurchaseRequest, "purchase_request", user, prof)
        kpi["pr_pending"] = prq.filter(PurchaseRequest.status == "submitted").count()
        
        # Get pending list for dashboard action items
        pending_prs = prq.filter(PurchaseRequest.status == "submitted").order_by(PurchaseRequest.id.desc()).limit(5).all()
        pending_prs_list = [{"id": pr.id, "code": pr.code, "requester": pr.requester or "", "purpose": pr.purpose or "Yêu cầu mua hàng"} for pr in pending_prs]

        rprs = apply_scope(db.query(PurchaseRequest), PurchaseRequest, "purchase_request", user, prof) \
            .order_by(PurchaseRequest.id.desc()).limit(8).all()
        for pr in rprs:
            amt = sum(float(it.amount or 0) for it in db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all())
            recent_prs.append({"id": pr.id, "code": pr.code, "requester": pr.requester,
                               "description": pr.purpose or "Yêu cầu mua hàng", "department": pr.department or "",
                               "date": pr.request_date or tstr, "status": pr.status, "total": round(amt, 0)})

    # ===== Đơn mua hàng + phân tích =====
    if can("purchase_order"):
        scoped_pos = apply_scope(db.query(PurchaseOrder), PurchaseOrder, "purchase_order", user, prof).all()
        pos = {p.id: p for p in scoped_pos}
        po_ids = list(pos.keys())
        items = {it.id: it for it in db.query(POItem).filter(POItem.po_id.in_(po_ids)).all()} if po_ids else {}
        delivs = db.query(PODelivery).filter(PODelivery.po_id.in_(po_ids), PODelivery.received_qty > 0).all() if po_ids else []
        kpi["po_ordered"] = sum(1 for p in pos.values() if p.status in ("approved", "partial", "received"))
        late_src = db.query(PODelivery).filter(PODelivery.po_id.in_(po_ids), PODelivery.received_qty <= 0).all() if po_ids else []
        # Hạn giao = NCC cam kết giao (`promised_date`). Cột `PODelivery.expected_date` đã bỏ
        # dùng — không nơi nào ghi, xem migration e2c5a81f7b60.
        kpi["late_deliveries"] = sum(1 for d in late_src if d.promised_date and d.promised_date < tstr)

        # Get detailed late deliveries list
        late_delivs_sorted = sorted([d for d in late_src if d.promised_date and d.promised_date < tstr], key=lambda x: x.promised_date)[:5]
        for ld in late_delivs_sorted:
            po = pos.get(ld.po_id)
            it = items.get(ld.po_item_id)
            name = it.product_name if it else ""
            late_deliveries_list.append({
                "po_id": ld.po_id,
                "po_code": po.code if po else "",
                "product_name": name,
                "expected_date": ld.promised_date
            })

        cat, sup, dept, po_total = {}, {}, {}, {}
        for it in items.values():
            amt = item_amt(it)
            po = pos.get(it.po_id)
            po_total[it.po_id] = po_total.get(it.po_id, 0) + amt
            cat[it.item_group or "(Không rõ)"] = cat.get(it.item_group or "(Không rõ)", 0) + amt
            nm = (po.supplier_name or po.supplier_code) if po else "(Không rõ)"
            sup[nm] = sup.get(nm, 0) + amt
            dp = (po.department if po and po.department else "(Không rõ)")
            dept[dp] = dept.get(dp, 0) + amt

        def top_list(dic, kk, vk, n=5):
            return [{kk: k2, vk: round(v, 0)} for k2, v in sorted(dic.items(), key=lambda x: -x[1])[:n]]

        cs = sorted(cat.items(), key=lambda x: -x[1])
        ct = sum(v for _, v in cs) or 1
        categories = [{"name": k2, "cost": round(v, 0), "pct": round(v / ct * 100, 1)} for k2, v in cs[:4]]
        other = sum(v for _, v in cs[4:])
        if other > 0:
            categories.append({"name": "Khác", "cost": round(other, 0), "pct": round(other / ct * 100, 1)})
        top_suppliers = top_list(sup, "name", "value")
        dept_spend = top_list(dept, "name", "value")

        years = {(d.received_date or "")[:4] for d in delivs if d.received_date}
        years.discard("")
        target_year = max(years) if years else str(today.year)
        mc = {f"{m:02d}": 0.0 for m in range(1, 13)}
        for d in delivs:
            it = items.get(d.po_item_id)
            rd = d.received_date or ""
            if it and rd[:4] == target_year and len(rd) >= 7:
                mc[rd[5:7]] += float(d.received_qty or 0) * float(it.price or 0) * (1 + float(it.vat or 0) / 100)
        cost_12m = [{"label": f"T{int(m)}", "value": round(mc[m], 0)} for m in sorted(mc)]

        ST = [("draft", "Nháp"), ("submitted", "Chờ duyệt"), ("approved", "Đã duyệt"),
              ("partial", "Giao 1 phần"), ("received", "Đã nhận"), ("completed", "Hoàn thành"), ("cancelled", "Đã hủy")]
        scount = {}
        for p in pos.values():
            scount[p.status] = scount.get(p.status, 0) + 1
        po_status = [{"key": k2, "label": lb, "value": scount.get(k2, 0)} for k2, lb in ST if scount.get(k2, 0) > 0]

        recent = sorted(pos.values(), key=lambda p: (p.order_date or "", p.id), reverse=True)[:8]
        recent_pos = [{"id": p.id, "code": p.code, "supplier": p.supplier_name or p.supplier_code,
                       "order_date": p.order_date, "status": p.status, "total": round(po_total.get(p.id, 0), 0)} for p in recent]

    # ===== Khảo sát =====
    if can("survey"):
        svq = apply_scope(db.query(Survey), Survey, "survey", user, prof)
        kpi["survey_pending"] = svq.filter(Survey.status == "submitted").count()
        pending_surveys = svq.filter(Survey.status == "submitted").order_by(Survey.id.desc()).limit(5).all()
        pending_surveys_list = [{"id": s.id, "code": s.code, "main_content": s.main_content or s.item_name or "Khảo sát", "nspt": s.nspt or ""} for s in pending_surveys]

    # ===== Yêu cầu khảo sát (chờ trưởng bộ phận duyệt) =====
    if can("survey_request"):
        from app.modules.survey_request.model import SurveyRequest
        srq = apply_scope(db.query(SurveyRequest), SurveyRequest, "survey_request", user, prof)
        kpi["sr_pending"] = srq.filter(SurveyRequest.status == "submitted").count()
        pending_srs = srq.filter(SurveyRequest.status == "submitted").order_by(SurveyRequest.id.desc()).limit(5).all()
        pending_srs_list = [{"id": sr.id, "code": sr.code, "requester": sr.requester or "", "purpose": sr.purpose or ""} for sr in pending_srs]

    # ===== Công nợ =====
    if can("payable"):
        pays = apply_scope(db.query(Payable), Payable, "payable", user, prof).filter(Payable.status != ST_PAID).all()
        kpi["due_soon"] = round(sum(float(p.remaining or 0) for p in pays if p.due_date and tstr <= p.due_date <= in7), 0)
        kpi["overdue"] = round(sum(float(p.remaining or 0) for p in pays if p.due_date and p.due_date < tstr), 0)
        aging = {"Chưa đến hạn": 0.0, "1–30 ngày": 0.0, "31–60 ngày": 0.0, "> 60 ngày": 0.0}
        debt_by_supplier = {}
        for p in pays:
            rem = float(p.remaining or 0)
            if rem <= 0:
                continue
            nm = p.supplier_name or p.supplier_code or "(Không rõ)"
            debt_by_supplier[nm] = debt_by_supplier.get(nm, 0.0) + rem
            if not p.due_date or p.due_date >= tstr:
                aging["Chưa đến hạn"] += rem
            else:
                od = (today - datetime.strptime(p.due_date, "%Y-%m-%d").date()).days
                aging["1–30 ngày" if od <= 30 else "31–60 ngày" if od <= 60 else "> 60 ngày"] += rem
        ap_aging = [{"label": k2, "value": round(v, 0)} for k2, v in aging.items()]
        # NỢ CÒN LẠI theo NCC — đừng nhầm với `top_suppliers`: cái kia là CHI TIÊU
        # tính trên dòng đơn mua và nằm trong khối `purchase_order`, người chỉ có
        # quyền Công nợ sẽ không nhận được. Trang Tài chính cần đúng số này.
        top_debt_suppliers = [{"name": k2, "value": round(v, 0)}
                              for k2, v in sorted(debt_by_supplier.items(), key=lambda x: -x[1])[:5]]

    # ===== Hợp đồng (dùng chung) =====
    if can("contract"):
        # B-02: mã của bộ `CONTRACT_STATUS` (`app/core/status_codes.py`), trước là "Thanh lý".
        # `apply_scope` là BẮT BUỘC: phạm vi hợp đồng lọc theo `company_id`, thiếu nó thì
        # người xem phạm vi một pháp nhân vẫn đếm cả hợp đồng của pháp nhân khác.
        kpi["contract_expiring"] = apply_scope(db.query(Contract), Contract, "contract", user, prof).filter(
            Contract.status != "liquidated", Contract.end_date != "", Contract.end_date <= in30).count()

    # ===== Tồn kho =====
    if can("inventory"):
        invs = apply_scope(db.query(Inventory), Inventory, "inventory", user, prof).all()
        kpi["inv_value"] = round(sum(float(i.value or 0) for i in invs), 2)
        kpi["out_of_stock"] = sum(1 for i in invs if float(i.qty or 0) <= 0)
        low_stock = [{"product_code": i.product_code, "product_name": i.product_name, "qty": float(i.qty or 0),
                      "unit": i.unit, "warehouse_code": i.warehouse_code}
                     for i in sorted(invs, key=lambda x: float(x.qty or 0))[:8]]

    # ===== Cảnh báo (lọc theo quyền từng loại) =====
    # Truyền user để build() lọc cả QUYỀN lẫn PHẠM VI (apply_scope) — trước đây gọi
    # không user nên thấy cảnh báo của chứng từ ngoài phạm vi (vd HĐ pháp nhân khác).
    def alert_ok(it):
        t = it.get("type")
        return (t == "payable" and can("payable")) or (t == "contract" and can("contract")) or (t == "delivery" and can("purchase_order"))
    al_items = [x for x in build_alerts(db, user)["items"] if alert_ok(x)]

    can_map = {e: can(e) for e in ["purchase_request", "purchase_order", "survey", "survey_request", "payable", "contract", "inventory", "report"]}

    return success({
        "year": target_year,
        "kpi": kpi,
        "cost_12m": cost_12m,
        "categories": categories,
        "top_suppliers": top_suppliers,
        "top_debt_suppliers": top_debt_suppliers,
        "dept_spend": dept_spend,
        "po_status": po_status,
        "ap_aging": ap_aging,
        "recent_pos": recent_pos,
        "recent_prs": recent_prs,
        "low_stock": low_stock,
        "alerts": al_items[:6],
        "alert_total": len(al_items),
        "can": can_map,
        "pending_prs_list": pending_prs_list,
        "pending_srs_list": pending_srs_list,
        "pending_surveys_list": pending_surveys_list,
        "late_deliveries_list": late_deliveries_list,
    })


@router.get("/production")
def production_overview(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Tổng quan phân hệ Sản xuất — danh mục NCC · Sản phẩm · ĐVT · Phân loại · Hợp đồng.

    Cùng luật với `/overview`: route chỉ đòi ĐĂNG NHẬP, rồi gác TỪNG KHỐI bằng
    `can(entity)` và **bỏ hẳn khóa** khi thiếu quyền. Không trả `0` cho người
    không có quyền — `0` nghĩa là "đếm được, không có dòng nào", khác hẳn
    "không được xem"; FE đọc `can` để chọn ẩn khối hay hiện số không.

    Phân hệ Sản xuất chưa có bảng nghiệp vụ nào của riêng nó (không có lệnh sản
    xuất, không có định mức), nên toàn bộ số liệu ở đây là danh mục nền.
    """
    from sqlalchemy import func

    from app.core.auth import get_perm_profile
    from app.core.scoping import apply_scope
    from app.modules.catalog.model import ItemGroup, Unit
    from app.modules.contract.model import Contract
    from app.modules.product.model import Product
    from app.modules.supplier.model import Supplier

    prof = get_perm_profile(db, user)

    def can(e):
        return bool(prof["perms_union"].get(e, {}).get("read"))

    today = datetime.now().date()
    tstr = today.strftime("%Y-%m-%d")
    in30 = (today + timedelta(days=30)).strftime("%Y-%m-%d")

    # Số thẻ hiện trên trang; lấy dư thì thẻ cao lêu nghêu, phần đuôi gom vào "Khác".
    TOP_GROUPS = 6
    EXPIRING_ROWS = 8

    kpi: dict = {}
    product_groups: list[dict] = []
    expiring_contracts: list[dict] = []

    # ===== Nhà cung cấp =====
    if can("supplier"):
        sup_q = apply_scope(db.query(Supplier), Supplier, "supplier", user, prof)
        kpi["supplier_total"] = sup_q.count()
        kpi["supplier_goods"] = sup_q.filter(Supplier.supplier_type == "goods").count()
        kpi["supplier_transport"] = sup_q.filter(Supplier.supplier_type == "transport").count()
        kpi["supplier_inactive"] = sup_q.filter(Supplier.is_active.is_(False)).count()

    # ===== Sản phẩm & Vật tư =====
    if can("product"):
        prod_q = apply_scope(db.query(Product), Product, "product", user, prof)
        kpi["product_total"] = prod_q.count()
        kpi["product_inactive"] = prod_q.filter(Product.is_active.is_(False)).count()
        # GROUP BY chứ không kéo cả bảng về đếm trong Python: `tab_product` là bảng
        # SKU (mỗi quy cách một dòng), trên prod đã hàng nghìn dòng.
        rows = (apply_scope(db.query(Product.item_group, func.count(Product.id)),
                            Product, "product", user, prof)
                .group_by(Product.item_group).all())
        counted = sorted(((g or "(Chưa phân loại)", int(n)) for g, n in rows), key=lambda x: -x[1])
        product_groups = [{"name": g, "value": n} for g, n in counted[:TOP_GROUPS]]
        rest = sum(n for _, n in counted[TOP_GROUPS:])
        if rest:
            product_groups.append({"name": "Khác", "value": rest})

    # ===== Đơn vị tính / Phân loại VTBB =====
    if can("unit"):
        kpi["unit_total"] = apply_scope(db.query(Unit), Unit, "unit", user, prof).count()
    if can("item_group"):
        kpi["item_group_total"] = apply_scope(db.query(ItemGroup), ItemGroup, "item_group", user, prof).count()

    # ===== Hợp đồng =====
    if can("contract"):
        ct_q = apply_scope(db.query(Contract), Contract, "contract", user, prof)
        # Hợp đồng đã thanh lý / đã hủy không còn là việc của ai — mọi con số cảnh
        # báo bên dưới đều đếm trên tập CÒN SỐNG này.
        live_q = ct_q.filter(Contract.status.notin_(["liquidated", "cancelled"]))
        kpi["contract_total"] = ct_q.count()
        kpi["contract_live"] = live_q.count()
        # `end_date != ""` là BẮT BUỘC: cột là VARCHAR, hợp đồng không đặt hạn lưu
        # chuỗi rỗng, mà "" <= "2026-09-30" là ĐÚNG — bỏ điều kiện này thì mọi hợp
        # đồng vô thời hạn bị đếm là sắp hết hạn.
        soon_q = live_q.filter(Contract.end_date != "", Contract.end_date >= tstr,
                               Contract.end_date <= in30)
        kpi["contract_expiring"] = soon_q.count()
        kpi["contract_expired"] = live_q.filter(Contract.end_date != "", Contract.end_date < tstr).count()
        kpi["contract_unsigned"] = live_q.filter(Contract.signed.is_(False)).count()
        for c in soon_q.order_by(Contract.end_date.asc()).limit(EXPIRING_ROWS).all():
            expiring_contracts.append({
                "id": c.id, "code": c.code, "title": c.title or "",
                "party_name": c.party_name or c.party_code or "", "end_date": c.end_date,
            })

    can_map = {e: can(e) for e in ["supplier", "product", "unit", "item_group", "contract"]}

    return success({
        "kpi": kpi,
        "product_groups": product_groups,
        "expiring_contracts": expiring_contracts,
        "can": can_map,
    })


def build_my_tasks(db: Session, user, prof) -> list[dict]:
    """Dựng danh sách Việc CẦN TÔI XỬ LÝ, lọc theo quyền + phạm vi (CR-215 tách
    ra khỏi endpoint để test gọi thẳng được).

    Mỗi việc mang `key` ổn định DÙNG CHUNG với `/api/alerts` (`delivery:{id}:danger`,
    `payable:{id}:warn`…) và cờ `dismissed` — đánh dấu xong ở tab Việc cần làm
    thì chuông cũng ẩn đúng dòng đó, xem `tab_user_task_dismiss`.

    Danh sách này phải là TẬP CHA của chuông cảnh báo (cùng điều kiện lọc, đủ cả
    mức `warn` lẫn hợp đồng) — thiếu loại nào thì "Đánh dấu làm hết" quét không
    sạch chuông, người dùng không có chỗ đánh dấu phần còn lại. Test
    `test_viec_can_lam_dismiss.py` có bài khóa ràng buộc tập cha này."""
    from app.core.scoping import apply_scope
    from app.modules.contract.model import Contract
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.survey_request.model import SurveyRequest
    from app.modules.purchase_order.model import PurchaseOrder, PODelivery
    from app.modules.payable.model import Payable
    from app.modules.payable.service import ST_PAID
    from app.modules.approval import task_service
    from app.modules.dashboard.service import load_dismissed_keys

    def can(e):
        return bool(prof["perms_union"].get(e, {}).get("read"))

    today = datetime.now().strftime("%Y-%m-%d")
    tasks = []

    # Chờ tôi ký (bộ máy duyệt — hiện chỉ Văn bản chạy). Trước CR-215 khối này
    # đứng riêng ở nút «Chờ tôi duyệt» trên thanh trên; nay gom về đây.
    if getattr(user, "employee_id", 0):
        for t in task_service.my_tasks(db, user.employee_id):
            tasks.append({"key": f"sign:{t['id']}", "type": "sign", "label": "Chờ tôi duyệt",
                          "code": t.get("entity_code") or "", "title": t.get("entity_title") or "Chứng từ chờ duyệt",
                          "subtitle": (f"Trình bởi {t['started_by_name']}" if t.get("started_by_name") else ""),
                          "date": (t["due_at"].strftime("%Y-%m-%d") if t.get("due_at") else ""),
                          "link": "/document/pending-approval"})

    if can("purchase_request"):
        rows = (apply_scope(db.query(PurchaseRequest).filter(PurchaseRequest.status == "submitted"),
                            PurchaseRequest, "purchase_request", user, prof)
                .order_by(PurchaseRequest.id.desc()).limit(300).all())
        for pr in rows:
            tasks.append({"key": f"pr:{pr.id}", "type": "pr", "label": "YCMH chờ duyệt", "code": pr.code,
                          "title": pr.purpose or "Yêu cầu mua hàng", "subtitle": pr.requester or "",
                          "date": pr.request_date or "", "link": f"/purchase-requests/{pr.id}"})

    if can("survey_request"):
        rows = (apply_scope(db.query(SurveyRequest).filter(SurveyRequest.status == "submitted"),
                            SurveyRequest, "survey_request", user, prof)
                .order_by(SurveyRequest.id.desc()).limit(300).all())
        for sr in rows:
            tasks.append({"key": f"sr:{sr.id}", "type": "sr", "label": "Khảo sát chờ duyệt", "code": sr.code,
                          "title": sr.purpose or "Yêu cầu khảo sát", "subtitle": sr.requester or "",
                          "date": sr.request_date or "", "link": f"/survey-requests/{sr.id}"})

    if can("purchase_order"):
        rows = (apply_scope(db.query(PurchaseOrder).filter(PurchaseOrder.status == "submitted"),
                            PurchaseOrder, "purchase_order", user, prof)
                .order_by(PurchaseOrder.id.desc()).limit(300).all())
        for po in rows:
            tasks.append({"key": f"po:{po.id}", "type": "po", "label": "ĐMH chờ duyệt", "code": po.code,
                          "title": po.supplier_name or po.supplier_code or "Đơn mua hàng", "subtitle": "",
                          "date": po.order_date or "", "link": f"/purchase-orders/{po.id}"})
        # Lô hàng giao trễ / sắp tới hạn giao (điều kiện + mốc ngày khớp `/api/alerts`)
        scoped = apply_scope(db.query(PurchaseOrder), PurchaseOrder, "purchase_order", user, prof).all()
        pomap = {p.id: p for p in scoped}
        po_ids = list(pomap.keys())
        if po_ids:
            warn_until = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            late = db.query(PODelivery).filter(PODelivery.po_id.in_(po_ids), PODelivery.received_qty <= 0).all()
            for d in late:
                exp = d.promised_date   # `expected_date` của lần giao đã bỏ dùng (e2c5a81f7b60)
                if not exp:
                    continue
                po = pomap.get(d.po_id)
                base = {"type": "late", "code": po.code if po else "", "subtitle": f"Hạn giao {exp}",
                        "date": exp, "link": f"/purchase-orders/{d.po_id}"}
                if exp < today:
                    tasks.append({"key": f"delivery:{d.id}:danger", "label": "Giao hàng trễ",
                                  "title": "Lô hàng quá hạn giao", **base})
                elif exp <= warn_until:
                    tasks.append({"key": f"delivery:{d.id}:warn", "label": "Sắp tới hạn giao",
                                  "title": "Lô hàng sắp tới hạn giao", **base})

    if can("payable"):
        # KHÔNG lọc `remaining > 0`: chuông cũng không lọc — lệch điều kiện là
        # "Đánh dấu làm hết" sót key, chuông còn kẹt lại vài dòng không ẩn được.
        rows = (apply_scope(db.query(Payable).filter(Payable.status != ST_PAID, Payable.due_date != ""),
                            Payable, "payable", user, prof)
                .order_by(Payable.due_date).limit(300).all())
        warn_until = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        for p in rows:
            base = {"type": "payable", "code": p.po_code or p.supplier_code,
                    "title": p.supplier_name or p.supplier_code,
                    "subtitle": f"Còn lại {float(p.remaining or 0):,.0f} · hạn {p.due_date}",
                    "date": p.due_date, "link": f"/payables?supplier={p.supplier_code}"}
            if p.due_date < today:
                tasks.append({"key": f"payable:{p.id}:danger", "label": "Công nợ quá hạn", **base})
            elif p.due_date <= warn_until:
                tasks.append({"key": f"payable:{p.id}:warn", "label": "Công nợ sắp đến hạn", **base})

    if can("contract"):
        # B-02: "liquidated" là mã của bộ `CONTRACT_STATUS`, trước là "Thanh lý".
        rows = (apply_scope(db.query(Contract).filter(Contract.status != "liquidated", Contract.end_date != ""),
                            Contract, "contract", user, prof)
                .order_by(Contract.end_date).limit(300).all())
        warn_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        for c in rows:
            base = {"type": "contract", "code": c.code, "title": c.party_name or c.party_code or "Hợp đồng",
                    "subtitle": f"Hết hạn {c.end_date}", "date": c.end_date, "link": f"/contracts/{c.id}"}
            if c.end_date < today:
                tasks.append({"key": f"contract:{c.id}:danger", "label": "Hợp đồng hết hạn", **base})
            elif c.end_date <= warn_until:
                tasks.append({"key": f"contract:{c.id}:warn", "label": "HĐ sắp hết hạn", **base})

    dismissed = load_dismissed_keys(db, user)
    for t in tasks:
        t["dismissed"] = t["key"] in dismissed
    return tasks


@router.get("/tasks")
def my_tasks(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Việc CẦN TÔI XỬ LÝ — danh sách chi tiết (đầy đủ, phân trang), lọc theo quyền + phạm vi.
    Gồm: chứng từ chờ tôi ký (bộ máy duyệt), YCMH/khảo sát/ĐMH chờ duyệt, lô hàng
    giao trễ/sắp tới hạn, công nợ quá hạn/sắp đến hạn, hợp đồng hết hạn/sắp hết hạn
    (tập cha của chuông cảnh báo). Query: page, page_size, type, q, include_dismissed."""
    from app.core.auth import get_perm_profile

    prof = get_perm_profile(db, user)
    tasks = build_my_tasks(db, user, prof)

    # Đếm theo loại VIỆC CHƯA ẨN (trước khi lọc q/type — cho FE hiển thị số trong dropdown)
    by_type = {}
    dismissed_total = 0
    for t in tasks:
        if t["dismissed"]:
            dismissed_total += 1
        else:
            by_type[t["type"]] = by_type.get(t["type"], 0) + 1

    # Mặc định ẨN việc đã đánh dấu xong; FE bật "Hiện việc đã ẩn" thì truyền include_dismissed=1
    if (request.query_params.get("include_dismissed") or "") not in ("1", "true"):
        tasks = [t for t in tasks if not t["dismissed"]]

    q = (request.query_params.get("q") or "").strip().lower()
    if q:
        tasks = [t for t in tasks
                 if q in f"{t.get('code','')} {t.get('title','')} {t.get('subtitle','')}".lower()]
    ftype = (request.query_params.get("type") or "").strip()
    if ftype:
        tasks = [t for t in tasks if t["type"] == ftype]

    total = len(tasks)
    try:
        page = max(1, int(request.query_params.get("page") or 1))
    except (ValueError, TypeError):
        page = 1
    try:
        # Trần 500 chứ không phải 100 như các danh sách khác: tab Việc cần làm
        # nạp CẢ danh sách một lần rồi tự phân trang — trần thấp hơn tổng việc
        # thì by_type đếm ra số mà trang đầu không nhìn thấy (lỗi "9 việc mà
        # danh sách trống").
        size = min(500, max(1, int(request.query_params.get("page_size") or 20)))
    except (ValueError, TypeError):
        size = 20
    items = tasks[(page - 1) * size: page * size]
    return success({"total": total, "by_type": by_type, "dismissed_total": dismissed_total,
                    "page": page, "page_size": size, "items": items})


@router.post("/tasks/dismiss")
def dismiss_tasks(body: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Đánh dấu XONG các việc theo `keys` (hoặc `all: true` = mọi việc chưa ẩn) —
    ẩn khỏi tab Việc cần làm, chuông cảnh báo và dashboard của TÀI KHOẢN này
    (CR-215). Không đụng nghiệp vụ, khôi phục được."""
    from app.core.auth import get_perm_profile
    from app.modules.dashboard.service import dismiss_keys

    if body.get("all"):
        # "Đánh dấu làm hết": server tự gom key thay vì tin danh sách FE gửi lên —
        # FE chỉ nạp được một trang, quá trần là sót việc ở đuôi danh sách.
        prof = get_perm_profile(db, user)
        keys = [t["key"] for t in build_my_tasks(db, user, prof) if not t["dismissed"]]
    else:
        keys = body.get("keys") or []
        if not isinstance(keys, list):
            keys = []
        keys = [str(k) for k in keys]
    added = dismiss_keys(db, user, keys)
    return success({"added": added}, "Đã đánh dấu xong")


@router.post("/tasks/restore")
def restore_tasks(body: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Khôi phục việc đã đánh dấu xong. Body: `keys` (danh sách) hoặc `all: true`."""
    from app.modules.dashboard.service import restore_keys

    keys = body.get("keys") or []
    if not isinstance(keys, list):
        keys = []
    removed = restore_keys(db, user, [str(k) for k in keys], restore_all=bool(body.get("all")))
    return success({"removed": removed}, "Đã khôi phục")
