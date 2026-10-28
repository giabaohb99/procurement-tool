"""Chi tiết MỘT kế hoạch (`GET /{id}`): header + khoản + dòng vị trí + văn bản liên kết + tệp + số tự tính.

CHE TIỀN theo pháp nhân (`can_see_payroll`): `amount`, `cap_amount`, `amounts` và `computed` chỉ trả khi được xem;
tệp đính kèm (có thể là bảng tính chi phí) cũng chỉ liệt kê khi được xem (`files_hidden`, cùng luật ở `attachment_scope`);
`computed.actual` (thực tế so với kế hoạch, `actual_detail.py`) luôn có, riêng phần tiền là None khi bị che;
ngược lại là None — định biên, tỷ lệ, mã khoản và cấu trúc vẫn trả. Văn bản liên kết người xem KHÔNG đọc được chỉ
có `{document_id, can_read: false}` (không lộ số hiệu, trích yếu, trạng thái); văn bản đã xóa có `deleted: true`.
"""
from sqlalchemy.orm import Session

from app.modules.attachment.model import FileLink, StoredFile
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.document.access_service import can as can_read_document
from app.modules.document.model import Document
from app.modules.employee.position_model import JobPosition
from app.modules.labor_contract.lookup import names_map

from .actual_detail import build_actual_block
from .cost_model import HeadcountPlanCostItem
from .costing import PlanCalcError
from .model import HeadcountPlan, HeadcountPlanDocument, HeadcountPlanLine
from .serializer import can_see_payroll, compute_from, header_out, mask_computed, readable_names

ATTACHMENT_ENTITY = "headcount_plan"


def cost_item_out(it, see_money: bool) -> dict:
    """Dùng cho khoản của kế hoạch lẫn khoản của mẫu (mẫu luôn `see_money=True`: không chứa lương ai)."""
    return {
        "id": it.id, "code": it.code, "name": it.name, "group_id": it.group_id or 0, "calc_method": int(it.calc_method),
        "rate": float(it.rate or 0), "factor": float(it.factor or 0),
        "cap_amount": int(it.cap_amount or 0) if see_money else None,
        "amount": int(it.amount or 0) if see_money else None,
        "base_codes": list(it.base_codes or []), "applies_to": int(it.applies_to or 1),
        "position_ids": list(it.position_ids or []), "months": list(it.months or []),
        "actual_source": int(it.actual_source or 0), "sort_order": it.sort_order or 0,
    }


def line_out(ln: HeadcountPlanLine, position_names: dict, see_money: bool) -> dict:
    return {
        "id": ln.id, "position_id": ln.position_id or 0,
        "position_name": position_names.get(ln.position_id, "") if ln.position_id else "Không theo vị trí",
        "headcounts": list(ln.headcounts or []),
        "amounts": {k: int(v or 0) for k, v in (ln.amounts or {}).items()} if see_money else None,
        "note": ln.note or "",
    }


def documents_out(db: Session, plan_id: int, user, profile: dict) -> list[dict]:
    ids = [i for (i,) in db.query(HeadcountPlanDocument.document_id).filter(
        HeadcountPlanDocument.plan_id == plan_id).order_by(HeadcountPlanDocument.id).all()]
    docs = {d.id: d for d in db.query(Document).filter(Document.id.in_(ids or [0])).all()}
    out = []
    for i in ids:
        d = docs.get(i)
        if d is None or d.is_deleted:
            out.append({"document_id": i, "can_read": False, "deleted": True})
        elif not can_read_document(db, d, user, profile, "read"):
            out.append({"document_id": i, "can_read": False})
        else:
            out.append({"document_id": i, "can_read": True, "code": d.doc_code or d.issue_number or "",
                        "title": d.title or "", "status": int(d.status or 0)})
    return out


def files_out(db: Session, plan_id: int) -> list[dict]:
    """Tệp đính kèm theo khuôn `modules/attachment` (FileLink). `url` rỗng: entity riêng tư, tải qua `/api/attachments/{id}/download`."""
    rows = (db.query(FileLink, StoredFile).join(StoredFile, StoredFile.id == FileLink.file_id)
            .filter(FileLink.entity == ATTACHMENT_ENTITY, FileLink.entity_id == plan_id)
            .order_by(FileLink.sort_order.asc(), FileLink.id.desc()).all())
    return [{"id": lk.id, "file_id": f.id, "filename": f.filename, "content_type": f.content_type,
             "size": f.size, "url": ""} for lk, f in rows]


def load_children(db: Session, plan_id: int):
    items = db.query(HeadcountPlanCostItem).filter(HeadcountPlanCostItem.plan_id == plan_id).order_by(
        HeadcountPlanCostItem.sort_order, HeadcountPlanCostItem.id).all()
    lines = db.query(HeadcountPlanLine).filter(HeadcountPlanLine.plan_id == plan_id).order_by(HeadcountPlanLine.id).all()
    return items, lines


def position_names_of(db: Session, lines) -> dict:
    return names_map(db, JobPosition, {ln.position_id for ln in lines})


def compute_out(db: Session, plan: HeadcountPlan, items, lines, see_money: bool, user, profile: dict) -> dict | None:
    try:
        computed = compute_from(db, plan.year, plan.period_type, plan.period_no, items, lines)
    except PlanCalcError:
        return None
    actual = build_actual_block(db, plan, items, computed, see_money, user, profile)
    out = computed if see_money else mask_computed(computed)
    out["actual"] = actual
    return out


def serialize_detail(db: Session, plan: HeadcountPlan, user, profile: dict) -> dict:
    see = can_see_payroll(profile, plan.company_id, plan.department_id or 0)
    items, lines = load_children(db, plan.id)
    approvers = readable_names(db, user, profile, {plan.approver_employee_id})
    head = header_out(plan, names_map(db, Company, {plan.company_id}), names_map(db, Department, {plan.department_id}),
                      approvers)
    names = position_names_of(db, lines)
    return head | {
        "cost_items": [cost_item_out(i, see) for i in items],
        "lines": [line_out(ln, names, see) for ln in lines],
        "documents": documents_out(db, plan.id, user, profile),
        "files": files_out(db, plan.id) if see else [],
        "files_hidden": not see,
        "can_see_money": see,
        "computed": compute_out(db, plan, items, lines, see, user, profile),
    }
