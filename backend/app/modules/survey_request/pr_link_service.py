"""YCBG — sinh Yêu cầu mua hàng từ phương án đã chọn; tự hoàn tất phiếu khi YCMH xong; gỡ liên kết YCMH đã xóa
(bao-CR-715 tách từ service.py).
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.central_purchasing import normalize_handler_dept_id
from app.core.utils import assert_unique_product_codes

from .model import LS_COMPLETED, SurveyRequest, SurveyRequestLine, SurveyRequestPr
from .base_service import ENTITY, get_sr, lines_of, options_of
from .lifecycle_service import set_status


# ───────────────────────── Phase 5D: sinh PYC từ option đã chọn ─────────────────────────

def _gen_pr_code(db: Session, request_date: str = "") -> str:
    from app.modules.purchase_request.model import PurchaseRequest
    date_str = ""
    if request_date and len(request_date) >= 10 and "-" in request_date:
        p = request_date.split("-")
        if len(p) == 3:
            date_str = f"{p[2]}{p[1]}{p[0][-2:]}"
    if not date_str:
        date_str = datetime.now().strftime("%d%m%y")
    prefix = f"PYC{date_str}"
    last = (db.query(PurchaseRequest).filter(PurchaseRequest.code.like(f"{prefix}%"))
            .order_by(PurchaseRequest.code.desc()).first())
    seq = 1
    if last and last.code.startswith(prefix):
        try:
            seq = int(last.code[len(prefix):]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:02d}"


def create_prs(db: Session, sid: int, user_id: int):
    """Gom option đã chọn theo NCC → mỗi NCC 1 PYC nháp (giá từ snapshot khảo sát).
    Cập nhật dòng: pr_id/pr_code/is_completed; phiếu KS → 'pr_created'."""
    from app.modules.purchase_request.model import (PurchaseRequest,
                                                    PurchaseRequestItem)
    from app.modules.purchase_request import service as pr_service
    from app.modules.purchase_request.service import (apply_supplier_info,
                                                     find_dept_head,
                                                     find_dept_head_id)
    from app.modules.supplier.model import Supplier
    s = get_sr(db, sid)
    # Cho tạo YCMH khi: Đang xử lý (mua trước dòng đã khảo sát xong), Đã khảo sát, Đã tạo YCMH, Hoàn thành.
    if s.status not in ("processing", "survey_done", "pr_created", "done"):
        raise HTTPException(400, "Chỉ tạo YCMH khi phiếu đang xử lý trở đi")

    # Dòng TÁI SỬ DỤNG: 1 dòng có thể tạo NHIỀU YCMH (mua lại). KHÔNG bỏ qua dòng đã completed;
    # chỉ tạo cho dòng ĐANG chọn PA. Sau khi tạo sẽ tự bỏ chọn (tránh tạo trùng lần sau).
    groups: dict[str, list] = {}
    for ln in lines_of(db, sid):
        chosen = [o for o in options_of(db, ln.id) if o.is_chosen]
        if not chosen:
            continue
        groups.setdefault(chosen[0].supplier_code or "", []).append((ln, chosen[0]))
    if not groups:
        raise HTTPException(400, "Chưa chọn phương án nào để tạo YCMH")
    # Mỗi NCC ra 1 YCMH → 2 dòng khảo sát cùng gắn 1 mã VTBB sẽ đẻ ra 2 dòng trùng mã trên
    # YCMH, làm sai tiến độ SL khi đồng bộ từ ĐMH. Chặn TRƯỚC vòng lặp vì vòng lặp commit theo
    # từng NCC — báo lỗi giữa chừng sẽ để lại vài YCMH đã tạo dở.
    for group_items in groups.values():
        assert_unique_product_codes(
            [(o.system_product_code or "") for _, o in group_items],
            message=("Nhiều dòng khảo sát của cùng một nhà cung cấp đang gắn trùng mã VTBB: "
                     "{codes}. Mỗi mã chỉ được 1 dòng trên YCMH — hãy gắn lại mã cho đúng "
                     "hoặc gộp các dòng khảo sát đó làm một."))

    today = datetime.now().strftime("%Y-%m-%d")
    created = []
    for sup_code, items in groups.items():
        sup = db.query(Supplier).filter(Supplier.code == sup_code).first() if sup_code else None
        first_opt = items[0][1]
        pr = PurchaseRequest(
            code=_gen_pr_code(db, today), company_id=s.company_id, requester=s.requester,
            requester_id=s.requester_id,
            requester_position=s.requester_position, department=s.department,
            department_id=s.department_id,      # CR-086: PYC sinh ra thừa kế id phòng của YCBG
            # bao-CR-414: phòng được nhờ đi theo phiếu con; bao-CR-524: `0` cũ → phòng thu mua mặc định
            handler_dept_id=normalize_handler_dept_id(db, s.handler_dept_id),
            head_of_dept=s.head_of_dept or find_dept_head(db, s.department or "", s.department_id),
            # CR-087: YCBG nay đã có id TBP → thừa kế thẳng, chỉ suy lại từ phòng khi phiếu
            # nguồn chưa có (phiếu cũ). 0 = không chỉ định ai, chạy theo luật duyệt cũ.
            head_of_dept_id=(s.head_of_dept_id
                             or find_dept_head_id(db, s.department or "", s.department_id)),
            purpose=s.purpose, request_date=today, status="draft",
            note=f"Sinh tự động từ Yêu cầu báo giá {s.code}",
            suggested_supplier=first_opt.supplier_name or "",
            suggested_supplier_tax_code=(sup.tax_code if sup else ""),
            suggested_supplier_contact=(sup.address if sup else ""),   # Liên hệ NCC lấy Địa chỉ từ bảng NCC
            created_by=user_id, updated_by=user_id,
        )
        # Task 4: NCC từ khảo sát -> cụm 'pur' (khóa với người yêu cầu; QL/Admin thu mua sửa được)
        apply_supplier_info(pr, {
            "req": {"name": "", "tax_code": "", "contact": ""},
            "pur": {"name": first_opt.supplier_name or "",
                    "tax_code": (sup.tax_code if sup else ""),
                    "contact": (sup.address if sup else "")},
            "from_survey": True,
        })
        db.add(pr)
        db.commit()
        db.refresh(pr)
        for ln, opt in items:
            qty = float(ln.request_qty or 0)
            price = float(opt.snap_price_by_volume or 0)
            # VAT của phương án đã chọn phải theo sang YCMH (CR-058). Trước đây không gán
            # `vat_pct` nên dòng nhận mặc định 0% — NCC báo giá 8% mà YCMH ghi 0%, người lập
            # phải sửa tay từng dòng, quên thì ĐMH prefill sai và thiếu luôn tiền thuế.
            vat = float(opt.snap_vat or 0)
            db.add(PurchaseRequestItem(
                pr_id=pr.id,
                product_code=(opt.system_product_code or "").strip(),   # mã SP hệ thống gắn ở option
                product_name=opt.snap_product_name or ln.requirement_detail or "Sản phẩm",
                item_group=ln.item_group or "", qty=qty, unit=opt.snap_quote_unit or ln.uom or "",
                price=price, vat_pct=vat,
                # Thành tiền GỒM VAT — cùng công thức với khi lưu YCMH (purchase_request/service.py)
                amount=round(qty * price * (1 + vat / 100), 2), note="",
                # CR-074 · B-06: mã cố định, xem purchase_request.service.LINE_STATUS_NO_PO
                line_status=pr_service.LINE_STATUS_NO_PO, created_by=user_id, updated_by=user_id,
            ))
            # Liên kết YCKS-dòng <-> YCMH (đếm được nhiều lần tạo) + tự BỎ CHỌN option
            db.add(SurveyRequestPr(
                survey_request_id=sid, survey_request_line_id=ln.id, option_id=opt.id,
                product_survey_line_id=opt.product_survey_line_id or 0,
                pr_id=pr.id, pr_code=pr.code, created_by=user_id, updated_by=user_id))
            opt.is_chosen = False          # tự bỏ chọn sau khi tạo
            ln.pr_id = pr.id               # giữ YCMH gần nhất (tương thích + auto-complete)
            ln.pr_code = pr.code
            ln.is_completed = True         # cờ "đã từng tạo YCMH" (KHÔNG còn khoá tạo thêm)
            ln.updated_by = user_id
        db.commit()
        created.append(pr)

    # Chỉ nâng cấp từ 'Đã khảo sát' → 'Đã tạo YCMH'; KHÔNG hạ cấp phiếu đã Hoàn thành (done).
    if s.status == "survey_done":
        s.status = "pr_created"
    s.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, sid, "pr_created")
    return created


def auto_complete_from_pr(db: Session, pr_id: int, user_id: int = 0) -> None:
    """Khi 1 Yêu cầu mua hàng (PR) hoàn thành: nếu Yêu cầu khảo sát liên quan (qua line.pr_id)
    đang ở 'pr_created' VÀ tất cả các PR sinh ra từ nó đều đã 'completed' -> tự chuyển YCKS sang 'done'."""
    sr_ids = [r[0] for r in db.query(SurveyRequestPr.survey_request_id)
              .filter(SurveyRequestPr.pr_id == pr_id).distinct().all()]
    for sid in sr_ids:
        _auto_complete_sr(db, sid, user_id)


def _auto_complete_sr(db: Session, sid: int, user_id: int = 0) -> None:
    """YCBG đang "Đã tạo YCMH" mà MỌI YCMH còn sống sinh từ nó đã hoàn thành -> tự "Hoàn thành".
    YCMH đã xóa không tính (bao-CR-580) — bình thường dây nối của nó đã gỡ, đây chỉ là lưới đỡ."""
    from app.modules.purchase_request.model import PurchaseRequest
    s = db.get(SurveyRequest, sid)
    if not s or s.is_deleted or s.status != "pr_created":
        return
    pr_ids = [r[0] for r in db.query(SurveyRequestPr.pr_id)
              .filter(SurveyRequestPr.survey_request_id == sid).distinct().all()]
    prs = [db.get(PurchaseRequest, pid) for pid in pr_ids]
    prs = [p for p in prs if p and not p.is_deleted]
    #  Còn hồ sơ báo cáo bắt buộc chưa hoàn tất thì KHÔNG tự đóng — bỏ qua im
    #  lặng, để người dùng đóng tay sau khi hoàn tất báo cáo (đường finalize).
    from . import report_service
    if prs and all(p.status == "completed" for p in prs) \
            and not report_service.required_docs_pending_of(db, ENTITY, sid):
        set_status(db, sid, "done", user_id or s.created_by or 0)
        record(db, user_id or s.created_by or 0, ENTITY, sid, "auto_done",
               "Tự hoàn thành: mọi Yêu cầu mua hàng liên quan đã hoàn thành")


def unlink_deleted_pr(db: Session, pr, user_id: int) -> list[int]:
    """bao-CR-580 — YCMH sinh từ YCBG bị xóa (xóa mềm) thì YCBG gỡ liên kết tới nó.

    Trước đây chỉ phiếu YCMH mang cờ `is_deleted`, nên YCBG vẫn bày mã YCMH đã xóa, vẫn đứng ở
    "Đã tạo YCMH", cờ "đã sinh YCMH" trên dòng vẫn khóa chuyển phòng / trả về, và việc tự hoàn
    thành vẫn chờ cả phiếu đã xóa. Nay:
      - xóa dây nối `tab_survey_request_pr` của YCMH đó;
      - dòng YCBG đang trỏ tới nó thì trỏ về YCMH gần nhất CÒN LẠI của dòng (mua lại nhiều lần);
        không còn YCMH nào thì xóa dấu, và gỡ cờ `is_completed` trừ khi người YC đã chốt dòng
        Hoàn thành bằng tay;
      - YCBG "Đã tạo YCMH" không còn YCMH sống nào thì về "Đã khảo sát"; còn thì xét lại việc tự
        hoàn thành. YCBG đã "Hoàn thành" giữ nguyên.
    Phương án đã chọn lúc tạo YCMH vốn đã tự bỏ chọn — muốn mua lại thì chọn lại như thường.
    Trả về danh sách id YCBG bị đụng."""
    links = db.query(SurveyRequestPr).filter(SurveyRequestPr.pr_id == pr.id).all()
    #  Đường cũ: phiếu tạo trước khi có bảng nối chỉ để dấu trên dòng.
    legacy = db.query(SurveyRequestLine).filter(SurveyRequestLine.pr_id == pr.id).all()
    line_ids = {lk.survey_request_line_id for lk in links} | {ln.id for ln in legacy}
    sr_ids = {lk.survey_request_id for lk in links} | {ln.survey_request_id for ln in legacy}
    if not sr_ids:
        return []
    for lk in links:
        db.delete(lk)
    db.flush()
    for ln in db.query(SurveyRequestLine).filter(SurveyRequestLine.id.in_(line_ids)).all():
        if ln.pr_id != pr.id:
            continue  # dòng đang trỏ YCMH khác (mới hơn) — giữ nguyên
        last = (db.query(SurveyRequestPr)
                .filter(SurveyRequestPr.survey_request_line_id == ln.id)
                .order_by(SurveyRequestPr.id.desc()).first())
        if last:
            ln.pr_id, ln.pr_code = last.pr_id, last.pr_code
        else:
            ln.pr_id, ln.pr_code = 0, ""
            if ln.line_status != LS_COMPLETED:
                ln.is_completed = False
        ln.updated_by = user_id
    db.commit()
    for sid in sorted(sr_ids):
        s = db.get(SurveyRequest, sid)
        if not s or s.is_deleted:
            continue   # ai-CR-170: YCBG đã xóa mềm thì không đổi trạng thái / không ghi sổ nữa
        has_live = bool(db.query(SurveyRequestPr.id).filter(SurveyRequestPr.survey_request_id == sid).first()
                        or db.query(SurveyRequestLine.id).filter(SurveyRequestLine.survey_request_id == sid,
                                                                 SurveyRequestLine.pr_code != "").first())
        message = f"Gỡ liên kết Yêu cầu mua hàng {pr.code} vì phiếu đó đã bị xóa"
        if s.status == "pr_created" and not has_live:
            s.status = "survey_done"
            message += "; không còn Yêu cầu mua hàng nào nên phiếu về \"Đã khảo sát\""
        s.updated_by = user_id
        db.commit()
        record(db, user_id, ENTITY, sid, "pr_unlinked", message)
        if has_live:
            _auto_complete_sr(db, sid, user_id)
    return sorted(sr_ids)


def list_deleted_linked_prs(db: Session) -> list:
    """YCMH đã xóa mềm mà YCBG vẫn còn nối tới (dữ liệu trước bao-CR-580)."""
    from app.modules.purchase_request.model import PurchaseRequest
    pr_ids = {r[0] for r in db.query(SurveyRequestPr.pr_id).distinct().all()}
    pr_ids |= {r[0] for r in db.query(SurveyRequestLine.pr_id).filter(SurveyRequestLine.pr_id != 0).distinct().all()}
    if not pr_ids:
        return []
    return (db.query(PurchaseRequest)
            .filter(PurchaseRequest.id.in_(pr_ids), PurchaseRequest.is_deleted == True)  # noqa: E712
            .order_by(PurchaseRequest.id).all())


def unlink_deleted_prs(db: Session, user_id: int) -> list[str]:
    """Dọn dữ liệu cũ (bao-CR-580): YCMH xóa mềm TRƯỚC bản vá vẫn còn dây nối với YCBG. Chạy lại
    không đổi gì. Trả về mã các YCMH đã gỡ."""
    return [pr.code for pr in list_deleted_linked_prs(db) if unlink_deleted_pr(db, pr, user_id)]
