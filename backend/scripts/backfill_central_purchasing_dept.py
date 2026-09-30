# -*- coding: utf-8 -*-
"""Chuyển dữ liệu «Thu mua chung» (phòng ảo, id 0) sang PHÒNG THU MUA MẶC ĐỊNH — bao-CR-524.

Khách chốt 30/09/2026: bỏ phòng ảo «Thu mua chung»; phòng thu mua mặc định là phòng THẬT mang mã
`central_purchasing_dept_code` (mặc định `PBA017` «Sản xuất -Thu mua»). Id tra theo MÃ ở
`app/core/central_purchasing.py`, không gõ cứng (id local / dev / prod khác nhau).

    docker compose exec -T api python scripts/backfill_central_purchasing_dept.py            # xem thử (mặc định)
    docker compose exec -T api python scripts/backfill_central_purchasing_dept.py --apply    # ghi thật

Mặc định CHỈ ĐẾM, không ghi gì. Chạy lại vô hại: lần hai không còn dòng `0` nào để đổi. Không
chạy script này hệ thống vẫn đúng (mọi chỗ đọc coi `0` là phòng thu mua mặc định), script chỉ
làm dữ liệu sạch cho báo cáo / bộ lọc / người đọc thẳng DB.

Đụng ĐÚNG những dòng sau (không xóa dòng nào):
  1. `tab_purchase_request` · `tab_survey_request` · `tab_purchase_order`: `handler_dept_id = 0`
     → id phòng mặc định. Từ bao-CR-480, `0` ở ba cột này chỉ còn một nghĩa: thu mua chung xử lý.
     Phiếu `0` mà phòng LẬP là một phòng tự mua KHÁC được đếm riêng để soát (có thể là phiếu cũ
     chưa chạy `backfill_handling_dept.py`) — vẫn đổi, vì thời CR-480 chúng đã đang được coi là
     của thu mua chung.
  2. `tab_payable.department_id = 0`: CHỈ khoản nợ CÓ ĐƠN (`po_id > 0`) mà đơn do phòng mặc định
     xử lý (`handler_dept_id` = 0 hoặc id phòng mặc định) — đúng luật `debt_dept_of` (bao-CR-484).
     Nợ không có đơn giữ `0` (ở đó `0` nghĩa là «không gắn phòng»); nợ `0` mà đơn thuộc phòng
     khác thì bỏ qua và báo — đó là nợ chưa chạy `resync_departments_from_orders`.
  3. `tab_payment_request.department_id = 0`: CHỈ phiếu có gắn khoản nợ, và MỌI khoản nợ gắn
     vào đều là nợ của phòng mặc định (sau bước 2). Phiếu gõ tay / không gắn nợ / nợ không có đơn
     giữ `0` (ở đó `0` nghĩa là «phiếu cũ, không gắn phòng», xem `get_hanging_lines`).
  4. `tab_category_assignee.department_id = 0` → id phòng mặc định. Khóa duy nhất là (phòng,
     phân loại): phân loại đã có SẴN dòng của phòng mặc định thì là XUNG ĐỘT — bỏ qua, in ra để
     người quản trị tự chọn giữ dòng nào trên màn Phân công phụ trách. Không xóa dòng nào.
"""
import argparse
import sys

sys.path.insert(0, "/app")

import app.core.all_models  # noqa: E402,F401
from sqlalchemy.orm import Session  # noqa: E402

from app.core.central_purchasing import get_central_dept, get_central_dept_code  # noqa: E402


def _doc_models():
    from app.modules.purchase_order.model import PurchaseOrder
    from app.modules.purchase_request.model import PurchaseRequest
    from app.modules.survey_request.model import SurveyRequest
    return (("purchase_request", PurchaseRequest), ("survey_request", SurveyRequest),
            ("purchase_order", PurchaseOrder))


def _backfill_documents(db: Session, central: int, other_self_depts: set[int], apply: bool) -> dict:
    out = {}
    for key, model in _doc_models():
        rows = db.query(model).filter(model.handler_dept_id == 0).all()
        out[key] = {"changed": len(rows),
                    "self_purchasing_creator": sum(1 for r in rows
                                                   if int(r.department_id or 0) in other_self_depts)}
        if apply:
            for r in rows:
                r.handler_dept_id = central
    return out


def _payable_dept_after(p, po_handler: dict[int, int], central: int) -> int:
    """Phòng của một khoản nợ SAU backfill (bước 2) — dùng chung cho bước 3."""
    dept = int(p.department_id or 0)
    if dept:
        return dept
    if int(p.po_id or 0) and po_handler.get(int(p.po_id)) in (0, central):
        return central
    return 0


def _backfill_payables(db: Session, central: int, apply: bool) -> tuple[dict, dict[int, int]]:
    from app.modules.payable.model import Payable
    from app.modules.purchase_order.model import PurchaseOrder

    po_ids = {int(pid) for (pid,) in db.query(Payable.po_id).filter(Payable.department_id == 0,
                                                                     Payable.po_id > 0).distinct()}
    po_handler = {int(i): int(h or 0) for i, h in
                  db.query(PurchaseOrder.id, PurchaseOrder.handler_dept_id)
                  .filter(PurchaseOrder.id.in_(po_ids)).all()} if po_ids else {}
    stats = {"changed": 0, "skipped_no_order": 0, "skipped_other_dept": 0}
    after: dict[int, int] = {}
    for p in db.query(Payable).filter(Payable.department_id == 0).all():
        want = _payable_dept_after(p, po_handler, central)
        after[p.id] = want
        if want == central:
            stats["changed"] += 1
            if apply:
                p.department_id = central
        elif not int(p.po_id or 0) or int(p.po_id) not in po_handler:
            stats["skipped_no_order"] += 1
        else:
            stats["skipped_other_dept"] += 1
    return stats, after


def _backfill_payment_requests(db: Session, central: int, payable_after: dict[int, int],
                               apply: bool) -> dict:
    from app.modules.payable.model import Payable
    from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine

    stats = {"changed": 0, "skipped_no_payable": 0, "skipped_other_dept": 0}
    for req in db.query(PaymentRequest).filter(PaymentRequest.department_id == 0).all():
        pay_ids = {int(x) for (x,) in db.query(PaymentRequestLine.payable_id)
                   .filter(PaymentRequestLine.request_id == req.id, PaymentRequestLine.payable_id > 0)}
        if not pay_ids:
            stats["skipped_no_payable"] += 1
            continue
        depts = set()
        for p in db.query(Payable).filter(Payable.id.in_(pay_ids)).all():
            depts.add(payable_after.get(p.id, int(p.department_id or 0)))
        if depts == {central}:
            stats["changed"] += 1
            if apply:
                req.department_id = central
        else:
            stats["skipped_other_dept"] += 1
    return stats


def _backfill_category_assignees(db: Session, central: int, apply: bool) -> dict:
    from app.modules.category_assignee.model import CategoryAssignee

    taken = {int(g) for (g,) in db.query(CategoryAssignee.item_group_id)
             .filter(CategoryAssignee.department_id == central)}
    stats = {"changed": 0, "conflicts": []}
    for row in db.query(CategoryAssignee).filter(CategoryAssignee.department_id == 0).all():
        if int(row.item_group_id) in taken:
            stats["conflicts"].append({"id": row.id, "item_group_id": int(row.item_group_id)})
            continue
        stats["changed"] += 1
        if apply:
            row.department_id = central
    return stats


def run_backfill(db: Session, apply: bool = False) -> dict:
    """Đếm (và nếu `apply` thì ghi) mọi dòng `0` → id phòng thu mua mặc định. Trả báo cáo theo bảng.
    Danh mục chưa có phòng mang mã đã cấu hình → `{"error": ...}`, không đụng gì."""
    dept = get_central_dept(db)
    if not dept:
        return {"error": f"Danh mục phòng ban chưa có mã {get_central_dept_code()} — không làm gì"}
    central = int(dept.id)
    from app.modules.purchase_request.service import list_self_purchasing_dept_ids
    other_self_depts = list_self_purchasing_dept_ids(db) - {central}

    report = {"central": {"id": central, "code": dept.code, "name": dept.name}, "apply": apply}
    # Bước 2 đọc handler_dept_id của ĐMH TRƯỚC bước 1 (0 hoặc id mặc định đều tính) nên thứ tự
    # không làm lệch kết quả giữa xem thử và ghi thật.
    report["payable"], payable_after = _backfill_payables(db, central, apply)
    report["payment_request"] = _backfill_payment_requests(db, central, payable_after, apply)
    report.update(_backfill_documents(db, central, other_self_depts, apply))
    report["category_assignee"] = _backfill_category_assignees(db, central, apply)
    if apply:
        db.commit()
    else:
        db.rollback()
    return report


def _print(report: dict) -> None:
    if "error" in report:
        print("LOI:", report["error"])
        return
    c = report["central"]
    verb = "da doi" if report["apply"] else "se doi"
    print(f"phong thu mua mac dinh: {c['code']} (id {c['id']}) {c['name']}")
    print("che do:", "GHI THAT (--apply)" if report["apply"] else "XEM THU (chua ghi gi)")
    for key in ("purchase_request", "survey_request", "purchase_order"):
        r = report[key]
        print(f"  {key}.handler_dept_id 0 -> {c['id']}: {r['changed']} {verb}"
              + (f" (trong do {r['self_purchasing_creator']} phieu do phong tu mua KHAC lap — nen soat)"
                 if r["self_purchasing_creator"] else ""))
    p = report["payable"]
    print(f"  payable.department_id 0 -> {c['id']}: {p['changed']} {verb}; "
          f"bo qua {p['skipped_no_order']} (khong co don), {p['skipped_other_dept']} (don thuoc phong khac)")
    q = report["payment_request"]
    print(f"  payment_request.department_id 0 -> {c['id']}: {q['changed']} {verb}; "
          f"bo qua {q['skipped_no_payable']} (khong gan cong no), {q['skipped_other_dept']} (no cua phong khac / khong co don)")
    a = report["category_assignee"]
    print(f"  category_assignee.department_id 0 -> {c['id']}: {a['changed']} {verb}; "
          f"xung dot {len(a['conflicts'])} (bo qua, khong xoa)")
    for x in a["conflicts"]:
        print(f"    - xung dot: dong id {x['id']} phan loai {x['item_group_id']} "
              f"da co dong rieng cua phong {c['id']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="chỉ đếm, không ghi (mặc định)")
    mode.add_argument("--apply", action="store_true", help="ghi thật")
    args = ap.parse_args()
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        report = run_backfill(db, apply=bool(args.apply))
        _print(report)
        if "error" in report:
            sys.exit(2)
    finally:
        db.close()


if __name__ == "__main__":
    main()
