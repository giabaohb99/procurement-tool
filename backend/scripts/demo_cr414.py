"""Dựng dữ liệu DEMO để bấm thử tay bao-CR-414 — "Phòng ban tự mua hàng".

Chạy:  docker compose exec api python -m scripts.demo_cr414
CHẠY LẠI ĐƯỢC — xóa sạch phiếu demo cũ (mã bắt đầu bằng DEMO-CR414-) rồi dựng lại từ đầu,
nên bấm thử hỏng thế nào cũng reset được.

CHỈ DÙNG Ở MÁY LOCAL. Cần chín tài khoản test đã có (`python -m app.seed_tai_khoan_cr414`).

Bộ phiếu dựng ra (ai thấy gì ghi trong bảng ở cuối log):
  NM01  YCMH nhà máy ĐÃ DUYỆT, chưa giao ai            → NM_MUA tiếp nhận / phân công / chuyển phòng
  NM02  YCMH nhà máy ĐÃ TIẾP NHẬN, giao NM_NV, có ĐMH   → nút chuyển phòng phải ẨN (đã có đơn)
  NM03  YCMH nhà máy CHỜ DUYỆT                        → NM_TP duyệt, tự gán NM_NV theo bảng phân công phòng
  NM04  YCMH nhà máy NHỜ phòng Thu mua chung           → TM_AD thấy dù bị loại trừ nhà máy; TM_FULL trả về được
  MKT01 YCMH phòng Hành chính NHỜ nhà máy              → NM_MUA thấy phiếu phòng khác nhờ mình
  MKT02 YCMH phòng Hành chính thường                   → NM_MUA KHÔNG thấy; TM_AD/TM_FULL thấy
  YCBG01 YCBG nhà máy ĐÃ DUYỆT, chưa khảo sát          → NM_MUA chuyển phòng / xử lý; TM_AD không thấy
  PO01  ĐMH nhà máy (từ NM02) + khoản nợ phòng nhà máy
  PO02  ĐMH phòng Hành chính + khoản nợ, CÙNG một NCC  → NM_MUA xem công nợ thấy hai con số
"""
from datetime import date, timedelta

import app.core.all_models  # noqa: F401 — nạp đủ model, không thì mapper User gãy
from app.core.database import SessionLocal
from app.modules.category_assignee.model import CategoryAssignee
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.catalog.model import ItemGroup
from app.modules.payable.model import Payable
from app.modules.payable.service import recalc_status
from app.modules.purchase_order.model import PurchaseOrder, POItem
from app.modules.purchase_request.model import (PurchaseRequest, PurchaseRequestItem,
                                                PurchaseRequestItemOption)
from app.modules.supplier.model import Supplier
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption, SurveyRequestPr)
from app.modules.user.model import User

PREFIX = "DEMO-CR414-"
FACTORY_DEPT = "Dego Organic"
PURCHASING_DEPT = "Sản xuất -Thu mua"
OTHER_DEPT = "Hành chính"
COMPANY_ID = 1

#  (phân loại — phải trùng tên trong tab_item_group, tên hàng, SL, ĐVT, giá đề xuất)
FACTORY_LINES_A = [
    ("Băng keo", "Băng keo trong 48mm x 100y (nhà máy)", 200, "cuộn", 12000),
    ("Bao PE", "Bao PE 50x70cm dày 0.05 (nhà máy)", 5000, "cái", 900),
]
FACTORY_LINES_B = [
    ("Bao PP", "Bao PP dệt 60x100cm (nhà máy)", 3000, "cái", 2500),
]
OTHER_LINES = [
    ("Băng keo", "Băng keo in logo 48mm (hành chính)", 50, "cuộn", 25000),
]


def _dept(db, name):
    d = db.query(Department).filter(Department.name == name).first()
    if not d:
        raise SystemExit(f"Không có phòng «{name}» trong DB local")
    return d


def _person(db, code):
    e = db.query(Employee).filter(Employee.code == code).first()
    if not e:
        raise SystemExit(f"Chưa có nhân sự {code} — chạy `python -m app.seed_tai_khoan_cr414` trước")
    u = db.query(User).filter(User.employee_id == e.id).first()
    return e, u


def _wipe_old(db):
    prs = db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{PREFIX}%")).all()
    for pr in prs:
        for it in db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all():
            (db.query(PurchaseRequestItemOption)
             .filter(PurchaseRequestItemOption.pr_item_id == it.id).delete())
            db.delete(it)
        db.delete(pr)
    srs = db.query(SurveyRequest).filter(SurveyRequest.code.like(f"{PREFIX}%")).all()
    for sr in srs:
        db.query(SurveyRequestPr).filter(SurveyRequestPr.survey_request_id == sr.id).delete()
        for ln in db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sr.id).all():
            (db.query(SurveyRequestOption)
             .filter(SurveyRequestOption.survey_request_line_id == ln.id).delete())
            db.delete(ln)
        db.delete(sr)
    pos = db.query(PurchaseOrder).filter(PurchaseOrder.code.like(f"{PREFIX}%")).all()
    for po in pos:
        db.query(POItem).filter(POItem.po_id == po.id).delete()
        db.query(Payable).filter(Payable.po_id == po.id).delete()
        db.delete(po)
    db.flush()
    print(f"  Đã xóa {len(prs)} YCMH, {len(srs)} YCBG, {len(pos)} ĐMH demo cũ")


def _make_pr(db, code, purpose, lines, requester, requester_user, status, *,
             handler_dept_id=0, assignee_code="", head=None, line_status="no_po"):
    today = date.today().isoformat()
    pr = PurchaseRequest(
        code=code, company_id=COMPANY_ID,
        requester=requester.full_name, requester_id=requester.id,
        requester_position=requester.position or "",
        department_id=requester.department_id, department="",
        handler_dept_id=handler_dept_id,
        head_of_dept_id=head.id if head else 0, head_of_dept=head.full_name if head else "",
        purpose=purpose, request_date=today, need_date=today,
        received_date=today if status == "dispatched" else "",
        status=status, vat_rate=0.08,
        created_by=requester_user.id, updated_by=requester_user.id,
    )
    db.add(pr)
    db.flush()
    items = []
    for group, name, qty, unit, price in lines:
        it = PurchaseRequestItem(
            pr_id=pr.id, product_name=name, item_group=group,
            qty=qty, unit=unit, price=price, vat_pct=8,
            amount=round(qty * price * 1.08, 2),
            required_date=today, assignee=assignee_code, line_status=line_status,
            qty_ordered=qty if line_status == "ordered" else 0,
            created_by=requester_user.id, updated_by=requester_user.id,
        )
        db.add(it)
        items.append(it)
    db.flush()
    return pr, items


def _make_sr(db, code, requester, requester_user, lines, head):
    today = date.today().isoformat()
    sr = SurveyRequest(
        code=code, company_id=COMPANY_ID,
        requester=requester.full_name, requester_id=requester.id,
        requester_position=requester.position or "",
        department_id=requester.department_id, department="",
        head_of_dept_id=head.id, head_of_dept=head.full_name,
        purpose="Demo CR-414 — nhà máy cần khảo sát bao bì mới", request_date=today,
        status="approved", created_by=requester_user.id, updated_by=requester_user.id,
    )
    db.add(sr)
    db.flush()
    for group, name, qty, unit, price in lines:
        db.add(SurveyRequestLine(
            survey_request_id=sr.id, item_group=group, requirement_detail=name,
            department_requester=f"{FACTORY_DEPT} / {requester.full_name}",
            request_qty=qty, uom=unit, proposed_price=price,
            created_by=requester_user.id, updated_by=requester_user.id,
        ))
    db.flush()
    return sr


def _make_po(db, code, pr, dept_id, handler_dept_id, nspt, nspt_user, supplier, items):
    today = date.today().isoformat()
    po = PurchaseOrder(
        code=code, pr_code=pr.code, company_id=COMPANY_ID,
        supplier_code=supplier.code, supplier_name=supplier.name,
        department_id=dept_id, handler_dept_id=handler_dept_id, department="",
        nspt_id=nspt.id, nspt=nspt.code, order_date=today, vat_rate=0.08,
        status="approved", created_by=nspt_user.id, updated_by=nspt_user.id,
    )
    db.add(po)
    db.flush()
    total = 0.0
    for it in items:
        amount = round(float(it.qty) * float(it.price) * 1.08, 2)
        total += amount
        db.add(POItem(
            po_id=po.id, product_name=it.product_name, item_group=it.item_group,
            unit=it.unit, qty_request=it.qty, qty_order=it.qty, price=it.price, vat=8,
            amount=amount, base_amount=amount, required_date=today,
            qty_received=it.qty, qty_remaining=0, line_status="full", progress_status="received",
            created_by=nspt_user.id, updated_by=nspt_user.id,
        ))
    db.flush()
    return po, total


def _make_payable(db, po, dept_id, supplier, total, user):
    incur = date.today() - timedelta(days=3)
    amount = round(total / 1.08, 2)
    p = Payable(
        company_id=COMPANY_ID, department_id=dept_id,
        supplier_code=supplier.code, supplier_name=supplier.name,
        source_type="goods", ref_type="delivery", ref_id=0,
        po_id=po.id, po_code=po.code, invoice_no=f"{po.code}-HD",
        incur_date=incur.isoformat(), period=str(incur.year),
        due_date=(incur + timedelta(days=30)).isoformat(),
        amount=amount, vat=round(total - amount, 2), total=total, paid_amount=0,
        created_by=user.id, updated_by=user.id,
    )
    recalc_status(p)
    db.add(p)
    db.flush()
    return p


def _ensure_factory_assignee_rows(db, dept_id, primary, backup, user):
    """Bảng phân công riêng của nhà máy (GĐ2): mọi phân loại dùng trong demo → NM_NV chính."""
    made = 0
    for group_name in {g for g, *_ in FACTORY_LINES_A + FACTORY_LINES_B}:
        g = db.query(ItemGroup).filter(ItemGroup.name == group_name).first()
        if not g:
            print(f"  ! Không có phân loại «{group_name}» — bỏ dòng phân công")
            continue
        row = (db.query(CategoryAssignee)
               .filter(CategoryAssignee.department_id == dept_id,
                       CategoryAssignee.item_group_id == g.id).first())
        if row:
            row.primary_employee_id, row.backup_employee_id = primary.id, backup.id
        else:
            db.add(CategoryAssignee(department_id=dept_id, item_group_id=g.id,
                                    primary_employee_id=primary.id, backup_employee_id=backup.id,
                                    created_by=user.id, updated_by=user.id))
            made += 1
    db.flush()
    print(f"  Bảng phân công nhà máy: thêm {made} dòng mới (chính NM_NV, dự phòng NM_MUA)")


def main():
    db = SessionLocal()
    print("== Chuẩn bị ==")
    factory = _dept(db, FACTORY_DEPT)
    purchasing = _dept(db, PURCHASING_DEPT)
    other = _dept(db, OTHER_DEPT)
    nm_yc, u_nm_yc = _person(db, "NM_YC")
    nm_tp, _ = _person(db, "NM_TP")
    nm_mua, u_nm_mua = _person(db, "NM_MUA")
    nm_nv, u_nm_nv = _person(db, "NM_NV")
    tm_nv, u_tm_nv = _person(db, "TM_NV")
    mkt_yc, u_mkt_yc = _person(db, "MKT_YC")
    mkt_tp, _ = _person(db, "MKT_TP")
    supplier = db.query(Supplier).filter(Supplier.is_active.is_(True)).order_by(Supplier.id).first()
    if not supplier:
        raise SystemExit("DB local không có nhà cung cấp nào đang hoạt động")

    print("== Dọn phiếu demo cũ ==")
    _wipe_old(db)
    _ensure_factory_assignee_rows(db, factory.id, nm_nv, nm_mua, u_nm_mua)

    print("== Dựng phiếu mới ==")
    nm01, _ = _make_pr(db, f"{PREFIX}NM01", "Nhà máy mua bao bì đợt 1 (đã duyệt, chờ tiếp nhận)",
                       FACTORY_LINES_A, nm_yc, u_nm_yc, "approved", head=nm_tp)
    nm02, nm02_items = _make_pr(db, f"{PREFIX}NM02", "Nhà máy mua bao PP (đã có đơn mua hàng)",
                                FACTORY_LINES_B, nm_yc, u_nm_yc, "dispatched",
                                assignee_code=nm_nv.code, head=nm_tp, line_status="ordered")
    nm03, _ = _make_pr(db, f"{PREFIX}NM03", "Nhà máy mua bao bì đợt 2 (chờ trưởng phòng duyệt)",
                       FACTORY_LINES_A, nm_yc, u_nm_yc, "submitted", head=nm_tp)
    nm04, _ = _make_pr(db, f"{PREFIX}NM04", "Nhà máy NHỜ phòng Thu mua chung mua hộ",
                       FACTORY_LINES_B, nm_yc, u_nm_yc, "approved",
                       handler_dept_id=purchasing.id, head=nm_tp)
    mkt01, _ = _make_pr(db, f"{PREFIX}MKT01", "Hành chính NHỜ nhà máy mua hộ băng keo",
                        OTHER_LINES, mkt_yc, u_mkt_yc, "approved",
                        handler_dept_id=factory.id, head=mkt_tp)
    mkt02, mkt02_items = _make_pr(db, f"{PREFIX}MKT02", "Hành chính mua băng keo (phiếu thường)",
                                  OTHER_LINES, mkt_yc, u_mkt_yc, "approved", head=mkt_tp)
    ycbg = _make_sr(db, f"{PREFIX}YCBG01", nm_yc, u_nm_yc, FACTORY_LINES_A, nm_tp)

    po01, total01 = _make_po(db, f"{PREFIX}PO01", nm02, factory.id, 0, nm_nv, u_nm_nv,
                             supplier, nm02_items)
    _make_payable(db, po01, factory.id, supplier, total01, u_nm_nv)
    po02, total02 = _make_po(db, f"{PREFIX}PO02", mkt02, other.id, 0, tm_nv, u_tm_nv,
                             supplier, mkt02_items)
    _make_payable(db, po02, other.id, supplier, total02, u_tm_nv)
    db.commit()

    print("\n== Bộ phiếu demo ==")
    rows = [
        (nm01, "Nhà máy, đã duyệt, chưa giao ai", "NM_MUA · NM_TP · TM_FULL", "TM_AD · MKT_*"),
        (nm02, "Nhà máy, đã tiếp nhận, giao NM_NV, đã có ĐMH", "NM_MUA · NM_NV · TM_FULL", "TM_AD"),
        (nm03, "Nhà máy, CHỜ DUYỆT", "NM_YC · NM_TP", "NM_MUA (chưa duyệt) · TM_AD"),
        (nm04, "Nhà máy NHỜ Thu mua chung", "NM_MUA · TM_AD · TM_FULL", "MKT_*"),
        (mkt01, "Hành chính NHỜ nhà máy", "NM_MUA · TM_AD · TM_FULL · MKT_TP", "NM_NV (chưa giao)"),
        (mkt02, "Hành chính, phiếu thường", "TM_AD · TM_FULL · MKT_TP", "NM_MUA · NM_NV"),
        (ycbg, "YCBG nhà máy, đã duyệt", "NM_MUA · TM_FULL", "TM_AD"),
        (po01, f"ĐMH nhà máy, nợ {total01:,.0f} đ", "NM_MUA · NM_NV · TM_FULL", "TM_AD"),
        (po02, f"ĐMH hành chính, nợ {total02:,.0f} đ, cùng NCC {supplier.code}",
         "TM_AD · TM_FULL", "NM_MUA"),
    ]
    for obj, what, sees, hidden in rows:
        print(f"  {obj.code:<20} id={obj.id:<5} {what}")
        print(f"  {'':<20} thấy: {sees:<40} không thấy: {hidden}")
    print("\n  Mật khẩu = mã tài khoản (NM_MUA / NM_MUA ...). Menu Đổi tài khoản nhanh có sẵn hai nhóm CR-414.")
    db.close()


if __name__ == "__main__":
    main()
