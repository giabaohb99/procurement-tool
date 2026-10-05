"""Ba tool để Trợ lý TỰ HỌC (ai-CR-078) — mục 1, 2, 5 trong đề xuất đại ca chọn ngày 05/10/2026.

  - `glossary_lookup`        (đọc)  : dò nghĩa một từ nội bộ trong DỮ LIỆU THẬT — sổ thuật ngữ, danh mục phòng ban,
                                      pháp nhân, chức vụ, NCC (khi có quyền xem NCC), tên phòng ghi trên phiếu — kèm số lần
                                      xuất hiện làm bằng chứng. (mục 2: tự dò nghĩa từ dữ liệu)
  - `propose_glossary_term`  (đề xuất): người dùng SỬA cách hiểu một từ, hoặc Trợ lý phải tự suy nghĩa → ghi ĐỀ XUẤT.
                                      Lời sửa của chính đại ca thì ghi thẳng vào sổ; còn lại chờ đại ca «đúng» trên Telegram.
                                      (mục 1: học từ lời sửa)
  - `report_missing_feature` (đề xuất): công cụ thiếu tính năng → ghi sổ chỗ thiếu; lặp lại thì bot mở việc sửa mã.
                                      (mục 5: tự đề xuất sửa công cụ)

Hai tool đề xuất KHÔNG ghi dữ liệu nghiệp vụ nào — chỉ ghi một dòng chờ duyệt vào `tab_setting`; mọi thứ thật sự đổi
(sổ thuật ngữ, việc sửa mã) đều qua tay đại ca.
"""
from __future__ import annotations

from sqlalchemy import func, or_

from .. import feedback, glossary
from .base import ToolContext, ToolSpec

MAX_CANDIDATES = 8


def _glossary_lookup(ctx: ToolContext, args: dict) -> dict:
    term = " ".join(str(args.get("term") or "").split())[:60]
    if not term:
        return {"error": "thiếu term"}
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.position_model import JobPosition
    from app.modules.purchase_order.model import PurchaseOrder
    from app.modules.purchase_request.model import PurchaseRequest

    db = ctx.db
    like = f"%{term}%"
    out: dict = {"term": term}
    known = glossary.find(glossary.load(db), term)
    if known is not None:
        out["glossary"] = known["meaning"]
    cands: list[dict] = []
    for d in db.query(Department).filter(or_(Department.name.ilike(like), Department.code.ilike(like))).limit(5):
        cands.append({"kind": "phòng ban", "name": d.name, "code": d.code})
    for c in db.query(Company).filter(or_(Company.name.ilike(like), Company.code.ilike(like))).limit(5):
        cands.append({"kind": "pháp nhân", "name": c.name, "code": c.code})
    for p in db.query(JobPosition).filter(JobPosition.name.ilike(like)).limit(5):
        cands.append({"kind": "chức vụ", "name": p.name, "code": p.code})
    if ctx.can("supplier"):
        from app.modules.supplier.model import Supplier

        for s in db.query(Supplier).filter(or_(Supplier.name.ilike(like), Supplier.code.ilike(like))).limit(5):
            cands.append({"kind": "nhà cung cấp", "name": s.name, "code": s.code})
    #  Tên phòng CHÉP trên phiếu (cột chữ) — người dùng hay gọi theo cách ghi trên phiếu, không theo danh mục.
    #  Chỉ đếm phiếu khi người hỏi có quyền xem loại phiếu đó (đếm cũng là thông tin).
    for model, label, entity in ((PurchaseRequest, "phòng ghi trên YCMH", "purchase_request"),
                                 (PurchaseOrder, "phòng ghi trên đơn mua hàng", "purchase_order")):
        if not ctx.can(entity):
            continue
        rows = db.query(model.department, func.count(model.id)).filter(model.department.ilike(like)) \
            .group_by(model.department).order_by(func.count(model.id).desc()).limit(3).all()
        cands += [{"kind": label, "name": name, "count": int(n)} for name, n in rows if name]
    out["candidates"] = cands[:MAX_CANDIDATES]
    if not cands and known is None:
        out["note"] = ("Không thấy từ này trong dữ liệu. Thử search_docs (tài liệu hướng dẫn) nếu có; vẫn không rõ thì hỏi "
                       "người dùng MỘT câu, đừng đoán.")
    return out


def _propose_glossary_term(ctx: ToolContext, args: dict) -> dict:
    term = str(args.get("term") or "")
    meaning = str(args.get("meaning") or "")
    kind = str(args.get("kind") or "inferred")
    evidence = str(args.get("evidence") or "")
    uid = int(getattr(ctx.user, "id", 0) or 0)
    try:
        if kind == "user_correction" and uid and uid == glossary.owner_user_id(ctx.db):
            item, old = glossary.upsert(ctx.db, term, meaning, uid)
            return {"saved": True, "term": item["term"], "meaning": item["meaning"], "replaced": old,
                    "note": "Đã ghi thẳng vào sổ thuật ngữ (người sửa là quản lý). Nói ngắn cho người dùng biết."}
        src = "lời sửa của người dùng" if kind == "user_correction" else "Trợ lý tự suy từ dữ liệu"
        item = glossary.propose(ctx.db, term, meaning, evidence=evidence, source=src, user_id=uid)
    except ValueError as e:
        return {"error": str(e)}
    if item.get("status") == "da_co":
        return {"saved": False, "note": "Sổ đã có đúng nghĩa này."}
    return {"proposed": True, "id": item["id"],
            "note": "Đã gửi đề xuất cho quản lý duyệt; trong lúc chờ, dùng nghĩa này cho câu trả lời hiện tại và nói rõ giả định."}


def _report_missing_feature(ctx: ToolContext, args: dict) -> dict:
    try:
        item = feedback.report(ctx.db, request=str(args.get("user_request") or ""),
                               missing=str(args.get("missing") or ""), tool=str(args.get("tool") or ""),
                               user_id=int(getattr(ctx.user, "id", 0) or 0))
    except ValueError as e:
        return {"error": str(e)}
    return {"recorded": True, "count": item["count"],
            "note": "Đã ghi nhận chỗ thiếu; lặp lại sẽ thành việc sửa phần mềm. Nói thật với người dùng phần chưa làm được."}


GLOSSARY_LOOKUP_SPEC = ToolSpec(
    name="glossary_lookup",
    description=("DÒ NGHĨA một từ / cụm NỘI BỘ công ty (vd «nhà máy», «kho 2», «bên Organic») trong dữ liệu thật: sổ thuật ngữ, "
                 "phòng ban, pháp nhân, chức vụ, NCC, tên phòng ghi trên phiếu. Gọi TRƯỚC khi đoán nghĩa một từ nội bộ không có "
                 "trong THUẬT NGỮ CỦA CÔNG TY, hoặc khi công cụ lọc theo từ đó ra rỗng."),
    parameters={"type": "object", "properties": {"term": {"type": "string"}}, "required": ["term"]},
    handler=_glossary_lookup,
)
PROPOSE_GLOSSARY_TERM_SPEC = ToolSpec(
    name="propose_glossary_term",
    description=("GHI NHỚ nghĩa một từ nội bộ. Gọi khi: (a) người dùng SỬA cách bạn hiểu một từ («không phải, nhà máy là phòng "
                 "Dego Organic», «ý anh là…») → kind=user_correction; hoặc (b) bạn đã TỰ SUY nghĩa một từ nội bộ từ kết quả "
                 "glossary_lookup → kind=inferred, kèm evidence (bằng chứng ngắn). KHÔNG gọi cho từ thông dụng."),
    parameters={"type": "object", "properties": {
        "term": {"type": "string"}, "meaning": {"type": "string", "description": "Nghĩa ngắn gọn, vd «phòng Dego Organic»."},
        "kind": {"type": "string", "enum": ["user_correction", "inferred"]},
        "evidence": {"type": "string", "description": "Vì sao (vd «danh mục có 1 phòng tên Dego Organic»)."}},
        "required": ["term", "meaning", "kind"]},
    handler=_propose_glossary_term,
)
REPORT_MISSING_FEATURE_SPEC = ToolSpec(
    name="report_missing_feature",
    description=("GHI NHẬN công cụ THIẾU TÍNH NĂNG khi bạn không đáp được yêu cầu vì công cụ không hỗ trợ (thiếu bộ lọc, thiếu "
                 "cột, không có công cụ cho loại câu hỏi đó). KHÔNG gọi khi chỉ thiếu quyền, không có dữ liệu, hay người dùng "
                 "hỏi mơ hồ. Lặp lại nhiều lần thì quản lý nhận đề xuất sửa phần mềm."),
    parameters={"type": "object", "properties": {
        "user_request": {"type": "string", "description": "Người dùng muốn gì (một câu)."},
        "missing": {"type": "string", "description": "Thiếu gì, cụ thể (vd «lọc đơn mua hàng theo kho nhận»)."},
        "tool": {"type": "string", "description": "Tên công cụ gần nhất đáng lẽ làm được (nếu có)."}},
        "required": ["user_request", "missing"]},
    handler=_report_missing_feature,
)
LEARNING_SPECS = [GLOSSARY_LOOKUP_SPEC, PROPOSE_GLOSSARY_TERM_SPEC, REPORT_MISSING_FEATURE_SPEC]
