"""Dựng dữ liệu DEMO để thử tay bao-CR-310 — gắn PHƯƠNG ÁN lên dòng Yêu cầu mua hàng.

Chạy:  docker compose exec api python -m scripts.demo_cr310
CHẠY LẠI ĐƯỢC — xóa sạch phiếu demo cũ (kèm dòng + phương án) rồi dựng lại từ đầu,
nên bấm thử hỏng thế nào cũng reset được.

CHỈ DÙNG Ở MÁY LOCAL. Script tạo phiếu rác và gán thêm vai trò cho tài khoản demo,
đừng chạy trên dev/prod.
"""
from datetime import date

import app.core.all_models  # noqa: F401 — nạp đủ model, không thì mapper User gãy
from app.core.database import SessionLocal
from app.modules.employee.model import Employee
from app.modules.purchase_request.model import (PurchaseRequest, PurchaseRequestItem,
                                                PurchaseRequestItemOption)
from app.modules.role.model import Role
from app.modules.survey.model import Survey, SurveyProductLine
from app.modules.user.model import User, UserRole

PREFIX = "DEMO-CR310-"
NSTM_LOGIN = "DEMONV"        # người sẽ gắn phương án
REQUESTER_LOGIN = "TESTREQ"  # người lập phiếu
OTHER_ASSIGNEE = "DEMOTP"    # mã NV khác — để thử hàng rào "dòng không giao cho bạn"

# (phân loại, tên hàng, SL, ĐVT, giá đề xuất) — phân loại khớp `item_group` của phiếu khảo sát
LINES_01 = [
    ("Thùng", "Thùng carton 3 lớp 40x30x25", 500, "cái", 9000),
    ("Nhãn", "Nhãn decal sản phẩm 90x50mm", 20000, "cái", 350),
]
LINES_02 = [
    ("Nắp", "Nắp chai nhựa phi 28", 30000, "cái", 450),
    ("Chai", "Chai nhựa PET 500ml", 30000, "cái", 1200),   # dòng giao NGƯỜI KHÁC
]


def _user(db, login):
    u = db.query(User).filter(User.email == login).first()
    if not u:
        raise SystemExit(f"Không có tài khoản {login} trong DB local")
    return u, db.get(Employee, u.employee_id)


def _grant_pur_staff(db, user):
    """NSTM phải có vai trò thu mua thì mới ghi được YCMH được giao cho mình."""
    role = db.query(Role).filter(Role.code == "pur_staff").first()
    if not role:
        print("  ! Không thấy vai trò pur_staff — bỏ qua bước gán vai trò")
        return
    has = db.query(UserRole).filter(UserRole.user_id == user.id,
                                    UserRole.role_id == role.id).first()
    if has:
        print(f"  {user.email} đã có vai trò pur_staff")
        return
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    print(f"  Đã gán vai trò pur_staff cho {user.email}")


def _wipe_old(db):
    olds = db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{PREFIX}%")).all()
    for pr in olds:
        items = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr.id).all()
        for it in items:
            (db.query(PurchaseRequestItemOption)
             .filter(PurchaseRequestItemOption.pr_item_id == it.id).delete())
            db.delete(it)
        db.delete(pr)
    db.flush()
    if olds:
        print(f"  Đã xóa {len(olds)} phiếu demo cũ")


def _make_pr(db, code, purpose, lines, requester, req_emp, nstm_emp, other_code):
    today = date.today().isoformat()
    pr = PurchaseRequest(
        code=code, company_id=req_emp.company_id or 1,
        requester=req_emp.full_name, requester_id=req_emp.id,
        department_id=req_emp.department_id, department="",
        purpose=purpose,
        request_date=today,       # = Ngày tiếp nhận (bao-CR-293)
        need_date=today,
        status="dispatched",      # thu mua ĐÃ tiếp nhận -> cổng phương án mở
        vat_rate=0.08,
        assignee_id=nstm_emp.id,
        created_by=requester.id, updated_by=requester.id,
    )
    db.add(pr)
    db.flush()
    out = []
    for idx, (group, name, qty, unit, price) in enumerate(lines):
        # Dòng cuối của phiếu 02 cố ý giao cho người khác để thử rào 403
        assignee = other_code if (code.endswith("02") and idx == len(lines) - 1) else nstm_emp.code
        it = PurchaseRequestItem(
            pr_id=pr.id, product_name=name, item_group=group,
            qty=qty, unit=unit, price=price, vat_pct=8,
            amount=round(qty * price * 1.08, 2),
            required_date=today, assignee=assignee,
            created_by=requester.id, updated_by=requester.id,
        )
        db.add(it)
        db.flush()
        out.append((it, group, assignee))
    return pr, out


def _suggest_survey_lines(db, item_group, limit=3):
    rows = (db.query(SurveyProductLine, Survey)
            .join(Survey, Survey.id == SurveyProductLine.survey_id)
            .filter(Survey.item_group == item_group,
                    SurveyProductLine.line_approve == "Đã duyệt",
                    SurveyProductLine.price_by_volume > 0)
            .order_by(SurveyProductLine.id.desc()).limit(limit).all())
    return rows


def main():
    db = SessionLocal()
    print("== Chuẩn bị tài khoản ==")
    u_nstm, e_nstm = _user(db, NSTM_LOGIN)
    u_req, e_req = _user(db, REQUESTER_LOGIN)
    _grant_pur_staff(db, u_nstm)
    other = db.query(Employee).filter(Employee.code == OTHER_ASSIGNEE).first()
    other_code = other.code if other else ""

    print("== Dọn phiếu demo cũ ==")
    _wipe_old(db)

    print("== Dựng phiếu mới ==")
    made = []
    made.append(_make_pr(db, f"{PREFIX}01", "Demo gắn phương án - bao bì đóng gói",
                         LINES_01, u_req, e_req, e_nstm, other_code))
    made.append(_make_pr(db, f"{PREFIX}02", "Demo gắn phương án - chai nắp",
                         LINES_02, u_req, e_req, e_nstm, other_code))
    db.commit()

    for pr, items in made:
        print(f"\n  PHIẾU {pr.code}  (id={pr.id}, trạng thái={pr.status})")
        for it, group, assignee in items:
            ai = "  <-- giao NGƯỜI KHÁC, dùng để thử rào 403" if assignee != e_nstm.code else ""
            print(f"    dòng id={it.id} | {group} | {it.product_name} | giao cho {assignee}{ai}")
            for psl, sv in _suggest_survey_lines(db, group):
                print(f"        phương án gợi ý: product_survey_line_id={psl.id} "
                      f"| {sv.code} | NCC {psl.supplier_code} | "
                      f"{(psl.product_name or '')[:45]} | giá {psl.price_by_volume}")

    print(f"\n  Đăng nhập: {NSTM_LOGIN} / {NSTM_LOGIN}   (NSTM gắn phương án)")
    print(f"             {REQUESTER_LOGIN} / {REQUESTER_LOGIN}   (người yêu cầu - KHÔNG được thấy NCC)")
    db.close()


if __name__ == "__main__":
    main()
