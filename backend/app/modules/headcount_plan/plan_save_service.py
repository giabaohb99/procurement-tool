"""Tạo / thay nguyên MỘT kế hoạch (header + khoản + dòng vị trí + văn bản liên kết) trong một giao dịch.

Luật chung: dựng khoản / dòng ở dạng ORM CHƯA gắn phiên → kiểm bằng bộ tính (`compute_from`, sai luật → 422) → rồi mới
xóa cũ + thêm mới. Ô tiền gửi None = GIỮ NGUYÊN số đang lưu (mọi người; muốn xóa thì gửi 0). Người KHÔNG xem được tiền của pháp nhân: ô tiền None / 0 = GIỮ NGUYÊN số đang lưu (khớp mã khoản /
vị trí), khác 0 → 403 (`service.deny_blind_money`). Chép khoản từ mẫu là BẢN CHỤP: sửa mẫu về sau không đổi kế hoạch đã lập.
"""
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .cost_model import HeadcountPlanCostItem, HrCostTemplate, HrCostTemplateItem
from .costing import PlanCalcError, period_months
from .model import HeadcountPlan, HeadcountPlanLine
from .schema import CostItemIn, PlanLineIn
from .serializer import can_see_payroll, compute_from
from .service import STRUCTURE_DENIED, deny_blind_money, link_documents

_ITEM_FIELDS = ("code", "name", "group_id", "calc_method", "rate", "factor", "cap_amount", "amount", "base_codes",
                "applies_to", "position_ids", "months", "actual_source", "sort_order")


def copy_template_items(db: Session, template_id: int, period_type: int, period_no: int) -> tuple[list, list[str]]:
    """Chép khoản của mẫu thành khoản kế hoạch (chưa gắn phiên). Kế hoạch không phải loại Năm: bỏ tháng rơi ngoài kỳ;
    khoản mà MỌI tháng rơi đều ngoài kỳ (thưởng T12 trong kế hoạch Q1) không có gì để tính → bỏ, kéo theo khoản trỏ vào nó.
    Trả (khoản, tên khoản đã bỏ)."""
    if db.get(HrCostTemplate, template_id) is None:
        raise HTTPException(422, "Mẫu khoản chi phí không tồn tại")
    in_period = set(period_months(period_type, period_no))
    src = db.query(HrCostTemplateItem).filter(HrCostTemplateItem.template_id == template_id).order_by(
        HrCostTemplateItem.sort_order, HrCostTemplateItem.id).all()
    kept: dict[str, dict] = {}
    skipped: list[str] = []
    for s in src:
        vals = {f: getattr(s, f) for f in _ITEM_FIELDS}
        vals["base_codes"], vals["position_ids"] = list(s.base_codes or []), list(s.position_ids or [])
        months = [m for m in (s.months or []) if m in in_period]
        if s.months and not months:
            skipped.append(s.name)
            continue
        vals["months"] = months
        kept[s.code] = vals
    changed = True
    while changed:   # khoản trỏ vào khoản đã bỏ: % thì bớt gốc (hết gốc → bỏ), «số tháng» mất gốc → bỏ
        changed = False
        for code, vals in list(kept.items()):
            if not vals["base_codes"]:
                continue
            present = [b for b in vals["base_codes"] if b in kept]
            if len(present) != len(vals["base_codes"]):
                vals["base_codes"] = present
                if not present:
                    skipped.append(vals["name"])
                    del kept[code]
                changed = True
    return [HeadcountPlanCostItem(**v) for v in kept.values()], skipped


_STRUCTURE_FIELDS = ("calc_method", "group_id", "applies_to", "actual_source")


def _same_structure(old, vals: dict) -> bool:
    """Khoản gửi lên có cùng CẤU TRÚC với khoản đang lưu không (tên, thứ tự, tiền không tính — tiền có chốt riêng)."""
    if any(int(getattr(old, f) or 0) != int(vals[f] or 0) for f in _STRUCTURE_FIELDS):
        return False
    if any(Decimal(str(getattr(old, f) or 0)) != Decimal(str(vals[f] or 0)) for f in ("rate", "factor")):
        return False
    if list(old.base_codes or []) != list(vals["base_codes"]) or list(old.position_ids or []) != list(vals["position_ids"]):
        return False
    return sorted(old.months or []) == sorted(vals["months"])


def deny_structure_change(incoming: list[CostItemIn], existing: dict) -> None:
    """Người KHÔNG xem được tiền chỉ được sửa định biên / vị trí / căn cứ / văn bản: thêm, xóa, đổi mã hay đổi cách tính,
    tỷ lệ, hệ số, tháng, khoản gốc, phạm vi áp, nguồn thực tế, nhóm của khoản → 403 (đổi cấu trúc là đổi cả số tiền họ không thấy)."""
    codes = [it.code for it in incoming]
    if set(codes) != set(existing):
        raise HTTPException(403, STRUCTURE_DENIED)
    for it in incoming:
        if not _same_structure(existing[it.code], it.model_dump()):
            raise HTTPException(403, STRUCTURE_DENIED)


def _keep_or(new, old_value):
    """Ngữ nghĩa None thống nhất: None = GIỮ NGUYÊN số đang lưu (không có thì 0); muốn xóa thì gửi 0."""
    return old_value if new is None else new


def _build_items(incoming: list[CostItemIn], existing: dict, profile: dict, company_id: int, department_id: int) -> list:
    """Khoản của schema → ORM chưa gắn phiên; ô tiền None (mọi người) hoặc của người không thấy tiền lấy lại từ khoản cùng mã
    đang lưu."""
    see = can_see_payroll(profile, company_id, department_id)
    out = []
    for it in incoming:
        vals = it.model_dump()
        old = existing.get(it.code)
        if not see:
            deny_blind_money(profile, company_id, department_id, vals["cap_amount"], vals["amount"])
            vals["cap_amount"], vals["amount"] = (old.cap_amount, old.amount) if old else (0, 0)
        else:
            vals["cap_amount"] = _keep_or(vals["cap_amount"], old.cap_amount if old else 0) or 0
            vals["amount"] = _keep_or(vals["amount"], old.amount if old else 0) or 0
        out.append(HeadcountPlanCostItem(**vals))
    return out


def _build_lines(incoming: list[PlanLineIn], existing: dict, item_codes: set, profile: dict, company_id: int,
                 department_id: int) -> list:
    see = can_see_payroll(profile, company_id, department_id)
    out = []
    for ln in incoming:
        old = existing.get(ln.position_id)
        kept = {k: v for k, v in ((old.amounts or {}) if old else {}).items() if k in item_codes}
        if see and ln.amounts is not None:
            amounts = dict(ln.amounts)      # gửi dict (kể cả {}) = thay nguyên; muốn xóa một ô thì gửi 0
        else:
            if not see:
                deny_blind_money(profile, company_id, department_id, *(ln.amounts or {}).values())
            amounts = kept                  # None = giữ nguyên số đang lưu
        out.append(HeadcountPlanLine(position_id=ln.position_id, headcounts=list(ln.headcounts), amounts=amounts,
                                     note=ln.note))
    return out


def _stamp(rows: list, plan_id: int, actor_id: int) -> None:
    for r in rows:
        r.plan_id, r.created_by, r.updated_by = plan_id, actor_id, actor_id


def replace_children(db: Session, plan: HeadcountPlan, items: list | None, lines: list[PlanLineIn],
                     document_ids: list[int], user, profile: dict) -> None:
    """Thay khoản (None = giữ khoản đang có / đã chép) + dòng vị trí + văn bản liên kết, ."""
    existing_items = {i.code: i for i in db.query(HeadcountPlanCostItem).filter(HeadcountPlanCostItem.plan_id == plan.id)}
    existing_lines = {ln.position_id: ln for ln in db.query(HeadcountPlanLine).filter(HeadcountPlanLine.plan_id == plan.id)}
    new_items = list(existing_items.values()) if items is None else items
    new_lines = _build_lines(lines, existing_lines, {i.code for i in new_items}, profile, plan.company_id,
                             plan.department_id or 0)
    try:
        compute_from(db, plan.year, plan.period_type, plan.period_no, new_items, new_lines)
    except PlanCalcError as e:
        raise HTTPException(422, str(e))
    if items is not None:
        db.query(HeadcountPlanCostItem).filter(HeadcountPlanCostItem.plan_id == plan.id).delete(synchronize_session=False)
        _stamp(new_items, plan.id, user.id)
        db.add_all(new_items)
    db.query(HeadcountPlanLine).filter(HeadcountPlanLine.plan_id == plan.id).delete(synchronize_session=False)
    _stamp(new_lines, plan.id, user.id)
    db.add_all(new_lines)
    link_documents(db, plan.id, document_ids, user, profile, user.id)
    db.flush()


def build_items(db: Session, plan: HeadcountPlan, incoming: list[CostItemIn], profile: dict,
                restrict_structure: bool = False) -> list:
    """`restrict_structure=True` (sửa kế hoạch ĐÃ CÓ): người không xem được tiền không được đổi cấu trúc khoản."""
    existing = {i.code: i for i in db.query(HeadcountPlanCostItem).filter(HeadcountPlanCostItem.plan_id == plan.id)}
    if restrict_structure and not can_see_payroll(profile, plan.company_id, plan.department_id or 0):
        deny_structure_change(incoming, existing)
    return _build_items(incoming, existing, profile, plan.company_id, plan.department_id or 0)
