"""CR-075 — Trang "Tiến độ báo giá".

Nguồn: join tab_survey_request -> tab_survey_request_line, một hàng = MỘT DÒNG yêu cầu
(kèm phương án đã chốt). Là bản song sinh của màn Tiến độ mua hàng nhưng **KHÔNG đụng vào
`purchase_progress`** — hai màn đọc hai chuỗi chứng từ khác nhau, gộp lại là dính nhau.

Quyền — **hai cờ RỜI, đừng gộp** (bài học CR-071):
- `survey_request.read` quyết định PHẠM VI dữ liệu (qua `apply_scope`) và cả việc NSTM chỉ
  thấy dòng mình phụ trách;
- `supplier.read` quyết định cụm cột NCC (mã/tên NCC, mã SP theo NCC, ghi chú NSTM, mã dòng
  nội bộ) hiện hay bị che — giống hệt luật của màn Kết quả khảo sát, kẻo màn tiến độ thành
  đường rò danh tính nhà cung cấp.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_perm_profile, user_has_permission
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.filter_operators import apply_operator_filters_map
from app.core.ref_filter import apply_ref_filters
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.survey_request.model import (LS_COMPLETED, LS_CONFIRMED, LS_RESURVEY,
                                              SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)

from . import export as ex

router = APIRouter(prefix="/api/survey-progress", tags=["survey_progress"])

VN_OFFSET = timedelta(hours=7)   # container chạy giờ UTC — "hôm nay" phải là hôm nay ở VN


def _today():
    return (datetime.utcnow() + VN_OFFSET).date()


def _sort_map():
    """Key cột (FE) -> cột DB thật để sort tại server. Cột TÍNH (trễ hạn, số ngày xử lý,
    tiến độ dòng, số phương án, cụm phương án) không có ở đây — sort chúng phải làm ở FE
    trên trang đang xem, vì giá trị không nằm trong DB."""
    return {
        "code": SurveyRequest.code, "company_id": SurveyRequest.company_id,
        "department": SurveyRequest.department, "requester": SurveyRequest.requester,
        "purpose": SurveyRequest.purpose, "request_date": SurveyRequest.request_date,
        "status": SurveyRequest.status,
        "internal_line_code": SurveyRequestLine.internal_line_code,
        "item_group": SurveyRequestLine.item_group,
        "request_qty": SurveyRequestLine.request_qty, "uom": SurveyRequestLine.uom,
        "proposed_price": SurveyRequestLine.proposed_price,
        "assignee_name": SurveyRequestLine.assignee,
        "received_date": SurveyRequestLine.received_date,
        "result_due_date": SurveyRequestLine.result_due_date,
        "result_date": SurveyRequestLine.result_date,
        "line_status": SurveyRequestLine.line_status,
        "pr_code": SurveyRequestLine.pr_code,
    }


def _cond_map(show_supplier: bool) -> dict:
    """CR-080 — whitelist cho BỘ LỌC ĐIỀU KIỆN (`<field>__<op>`).

    Lấy thẳng `_sort_map()` (cột nào sort được tại server thì lọc được) và bỏ `company_id` — ô
    Công ty đã nằm ở thanh lọc cơ bản, chọn theo tên chứ không gõ id. Thêm bí danh `assignee`
    trỏ cùng cột với `assignee_name` để tên field trên URL đọc ra nghĩa (giá trị là MÃ nhân sự).

    Cột thuộc cụm NCC bị gỡ khỏi map với người không có `supplier.read` — cột đã che trên bảng thì
    cũng không cho lọc, kẻo lọc rồi đếm dòng còn lại là mò ra được nhà cung cấp. Cột TÍNH (trễ
    hạn, số ngày xử lý, tiến độ dòng, số phương án) không có ở đây vì không nằm trong DB: tiến độ
    dòng vẫn lọc bằng ô `state` sẵn có, hai cột ngày thì lọc qua các mốc ngày thật.
    """
    m = {k: v for k, v in _sort_map().items() if k != "company_id"}
    m["assignee"] = SurveyRequestLine.assignee
    # CR-088: lọc ô tham chiếu theo ID. Không nhét vào `_sort_map()` — sắp xếp theo id ra thứ tự
    # số, chẳng ai đọc được. Lối này khớp id THẲNG, nhánh lùi nằm ở `apply_ref_filters`.
    m["department_id"] = SurveyRequest.department_id
    m["requester_id"] = SurveyRequest.requester_id
    if not show_supplier:
        for k in ex.SUPPLIER_HIDDEN_KEYS:
            m.pop(k, None)
    return m


def _state_cond(state: str):
    """Dịch nhãn cột TÍNH "Tiến độ dòng" thành điều kiện SQL để lọc được tại server.

    Phải bám đúng thứ tự ưu tiên của `export.progress_state`: mỗi nhãn = "khớp mốc của mình
    VÀ không khớp mốc nào xa hơn". Bỏ vế sau là lọc ra thừa — ví dụ chọn "Đang khảo sát" sẽ
    kéo về cả những dòng đã chốt xong từ lâu, vì chúng cũng có phương án.

    Trả None với nhãn lạ (người dùng sửa URL) — coi như không lọc, hơn là trả bảng rỗng khó hiểu.
    """
    L = SurveyRequestLine
    chosen = exists(select(SurveyRequestOption.id)
                    .where(SurveyRequestOption.survey_request_line_id == L.id,
                           SurveyRequestOption.is_chosen.is_(True)))
    any_opt = exists(select(SurveyRequestOption.id)
                     .where(SurveyRequestOption.survey_request_line_id == L.id))
    line_st = func.coalesce(L.line_status, "")
    no_pr = func.coalesce(L.pr_code, "") == ""
    answered = func.coalesce(L.result_date, "") != ""

    # CR-077: HOÀN THÀNH là mốc xa nhất, đứng TRÊN "Đã tạo YCMH".
    if state == ex.STATE_DONE:
        return line_st == LS_COMPLETED
    not_done = line_st != LS_COMPLETED
    # P6-6 (bao-CR-284): "Đã lên đơn" (po_code — luồng v2 lên thẳng ĐMH) xét TRƯỚC pr_code,
    # bám `progress_state`. Trước đây chuỗi này quên hẳn po_code: hai nhãn P6-3 lọc ra None
    # (lặng lẽ không lọc), còn dòng đã lên đơn thẳng thì lọt vào các nhãn phía sau.
    no_po = func.coalesce(L.po_code, "") == ""
    if state == ex.STATE_PO_CREATED:
        return and_(not_done, func.coalesce(L.po_code, "") != "")
    r0 = and_(not_done, no_po)                                # chưa hoàn thành, chưa lên đơn
    if state == ex.STATE_PR_CREATED:
        return and_(r0, func.coalesce(L.pr_code, "") != "")
    r1 = and_(r0, no_pr)                                      # … và chưa tạo YCMH
    if state == ex.STATE_RESURVEY:
        return and_(r1, line_st == LS_RESURVEY)
    r2 = and_(r1, line_st != LS_RESURVEY)
    if state == ex.STATE_CONFIRMED:
        return and_(r2, line_st == LS_CONFIRMED)
    r2b = and_(r2, line_st != LS_CONFIRMED)
    if state == ex.STATE_CHOSEN:
        return and_(r2b, chosen)
    r3 = and_(r2b, ~chosen)
    if state == ex.STATE_NO_OPTION:
        return and_(r3, L.no_option.is_(True))
    r4 = and_(r3, L.no_option.is_(False))
    if state == ex.STATE_ANSWERED:
        return and_(r4, answered)
    r5 = and_(r4, ~answered)
    if state == ex.STATE_SURVEYING:
        return and_(r5, any_opt)
    r6 = and_(r5, ~any_opt)
    if state == ex.STATE_RECEIVED:
        return and_(r6, func.coalesce(L.assignee, "") != "")
    if state == ex.STATE_NOT_RECEIVED:
        return and_(r6, func.coalesce(L.assignee, "") == "")
    return None


def _require_progress(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user_has_permission(db, user, "survey_request", "read"):
        return user
    raise HTTPException(403, "Không có quyền xem tiến độ báo giá")


def _require_progress_export(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user_has_permission(db, user, "survey_request", "export"):
        return user
    raise HTTPException(403, "Không có quyền xuất dữ liệu tiến độ báo giá")


def _show_supplier(db: Session, user) -> bool:
    """Cụm cột NCC đi theo quyền `supplier.read`, KHÔNG theo quyền YCBG."""
    return user_has_permission(db, user, "supplier", "read")


def _sees_every_line(profile: dict) -> bool:
    """Ai được thấy MỌI dòng của phiếu nằm trong phạm vi mình — bản dịch sang SQL của
    `survey_request.service._see_all_lines` (phần không phụ thuộc từng phiếu)."""
    for g in profile.get("grants", []):
        p = g["perms"].get("survey_request")
        if not p:
            continue
        if p.get("approve"):
            return True
        if p.get("read") and p.get("scope") in ("dept", "company", "all"):
            return True
        # Admin thu mua = đọc-chỉ phạm vi 'proc' (không có 'write') -> giám sát, thấy hết dòng
        if p.get("read") and p.get("scope") == "proc" and not p.get("write"):
            return True
    return False


def _line_visible_cond(db: Session, user, profile: dict):
    """Điều kiện lọc DÒNG cho NSTM (người chỉ xử lý phần việc của mình).

    Bản SQL của `_see_all_lines` + `can_process_line`: thấy dòng của phiếu mình tạo / mình là
    người yêu cầu, dòng gán đúng mã mình, hoặc dòng thuộc phân loại mình phụ trách chính/phụ.
    Trả None nghĩa là không phải lọc gì thêm."""
    if _sees_every_line(profile):
        return None
    from app.modules.catalog.model import ItemGroup
    from app.modules.category_assignee.model import CategoryAssignee

    emp_code = profile.get("emp_code") or ""
    emp_id = profile.get("employee_id") or 0
    conds = [SurveyRequest.created_by == getattr(user, "id", 0)]
    if emp_id:
        conds.append(SurveyRequest.requester_id == emp_id)
    if emp_code:
        conds.append(SurveyRequestLine.assignee == emp_code)
    if emp_id:
        groups = [name for (name,) in db.query(ItemGroup.name)
                  .join(CategoryAssignee, CategoryAssignee.item_group_id == ItemGroup.id)
                  .filter(or_(CategoryAssignee.primary_employee_id == emp_id,
                              CategoryAssignee.backup_employee_id == emp_id)).all()]
        if groups:
            conds.append(SurveyRequestLine.item_group.in_(groups))
    return or_(*conds)


def _build_query(request: Request, db: Session, user, prof: dict,
                 show_supplier: bool = False):
    """Bộ lọc + phạm vi + sắp xếp — dùng chung cho danh sách và xuất Excel, để file xuất luôn
    khớp đúng những gì đang bày trên bảng."""
    q = (db.query(SurveyRequest, SurveyRequestLine)
         .join(SurveyRequestLine, SurveyRequestLine.survey_request_id == SurveyRequest.id))

    # ----- Filter -----
    company_id = (request.query_params.get("company_id") or "").strip()
    if company_id.isdigit():
        q = q.filter(SurveyRequest.company_id == int(company_id))
    # CR-088: màn hình đã đổi sang `department_id=` (xử lý ở `apply_ref_filters` bên dưới);
    # nhánh theo TÊN này giữ cho các đường dẫn đã lưu sẵn và ai gọi API thẳng.
    department = (request.query_params.get("department") or "").strip()
    if department:
        q = q.filter(SurveyRequest.department == department)
    sr_status = (request.query_params.get("sr_status") or "").strip()
    if sr_status:
        q = q.filter(SurveyRequest.status == sr_status)
    item_group = (request.query_params.get("item_group") or "").strip()
    if item_group:
        q = q.filter(SurveyRequestLine.item_group == item_group)
    assignee = (request.query_params.get("assignee") or "").strip()
    if assignee:
        q = q.filter(SurveyRequestLine.assignee == assignee)
    line_status = (request.query_params.get("line_status") or "").strip()
    if line_status:
        q = q.filter(SurveyRequestLine.line_status == line_status)
    state = (request.query_params.get("state") or "").strip()   # cột TÍNH "Tiến độ dòng"
    if state:
        cond = _state_cond(state)
        if cond is not None:
            q = q.filter(cond)
    # P6-6 (bao-CR-284): bước "Đang so giá" của màn Tiến độ mua hàng gộp — chỉ lấy dòng
    # CHƯA rời giai đoạn báo giá: chưa hoàn thành, chưa tạo YCMH, chưa lên đơn thẳng.
    if (request.query_params.get("phase") or "").strip() == "quoting":
        q = q.filter(func.coalesce(SurveyRequestLine.line_status, "") != LS_COMPLETED,
                     func.coalesce(SurveyRequestLine.pr_code, "") == "",
                     func.coalesce(SurveyRequestLine.po_code, "") == "")
    month = (request.query_params.get("month") or "").strip()      # YYYY-MM theo ngày tiếp nhận
    if month:
        q = q.filter(SurveyRequestLine.received_date.like(f"{month}%"))
    # Các khoảng ngày (chuỗi YYYY-MM-DD nên so sánh chuỗi vẫn đúng thứ tự thời gian)
    for prefix, col in (("received_date", SurveyRequestLine.received_date),
                        ("result_due_date", SurveyRequestLine.result_due_date),
                        ("result_date", SurveyRequestLine.result_date)):
        v_from = (request.query_params.get(f"{prefix}_from") or "").strip()
        v_to = (request.query_params.get(f"{prefix}_to") or "").strip()
        if v_from:
            q = q.filter(col != "", col >= v_from)
        if v_to:
            q = q.filter(col != "", col <= v_to)
    # Lọc nhanh trạng thái trả kết quả — phần người dùng vào màn này để tìm
    answered = (request.query_params.get("answered") or "").strip()
    if answered == "yes":
        q = q.filter(SurveyRequestLine.result_date != "")
    elif answered == "no":
        q = q.filter(SurveyRequestLine.result_date == "")
    # Trễ hạn: đã trả sau hạn, HOẶC chưa trả mà hạn đã qua. Cả hai vế so sánh chuỗi ngày.
    if (request.query_params.get("late") or "").strip() in ("1", "true", "yes"):
        today = _today().strftime("%Y-%m-%d")
        q = q.filter(SurveyRequestLine.result_due_date != "").filter(or_(
            (SurveyRequestLine.result_date != "")
            & (SurveyRequestLine.result_date > SurveyRequestLine.result_due_date),
            (SurveyRequestLine.result_date == "") & (SurveyRequestLine.result_due_date < today)))
    kw = (request.query_params.get("q") or "").strip()
    if kw:
        like = f"%{kw}%"
        q = q.filter((SurveyRequest.code.like(like)) | (SurveyRequest.purpose.like(like))
                     | (SurveyRequestLine.item_group.like(like))
                     | (SurveyRequestLine.requirement_detail.like(like))
                     | (SurveyRequestLine.pr_code.like(like)))

    # ----- Bộ lọc điều kiện (CR-080) -----
    # Thanh lọc cố định phía trên chỉ còn Công ty / Tiến độ dòng / Tìm kiếm / Trễ hạn; các cột
    # còn lại (bộ phận, phân loại, NSTM, trạng thái phiếu, trạng thái dòng, các mốc ngày…) lọc
    # qua đây với đủ phép so sánh. Param cũ (month, *_from/_to, answered…) vẫn đọc ở trên để
    # link cũ không chết, chỉ là FE không còn ô nhập cho chúng.
    q = apply_operator_filters_map(q, _cond_map(show_supplier), request)
    # CR-088: param trần `department_id=` / `requester_id=`, có nhánh lùi cho phiếu chưa có id.
    q = apply_ref_filters(q, SurveyRequest, request, db)

    # ----- Phạm vi dữ liệu: phiếu theo scope, rồi dòng theo phần việc -----
    q = apply_scope(q, SurveyRequest, "survey_request", user, prof)
    cond = _line_visible_cond(db, user, prof)
    if cond is not None:
        q = q.filter(cond)

    # ----- Sort -----
    sort_by = (request.query_params.get("sort_by") or "").strip()
    sort_dir = (request.query_params.get("sort_dir") or "asc").strip().lower()
    col = _sort_map().get(sort_by)
    if col is not None:
        q = q.order_by(col.desc() if sort_dir == "desc" else col.asc())
    return q.order_by(SurveyRequest.code, SurveyRequestLine.id)


def _decorate(db: Session, rows, show_supplier: bool, start: int) -> list[dict]:
    """Ghép phương án đã chốt + số phương án + tên NSTM + tên công ty cho các hàng của trang.

    Nạp theo LÔ (một truy vấn cho cả trang) — bảng này có thể lên hàng nghìn dòng khi xuất."""
    from app.modules.company.model import Company
    from app.modules.employee.model import Employee

    line_ids = [ln.id for _s, ln in rows]
    chosen: dict[int, SurveyRequestOption] = {}
    counts: dict[int, int] = {}
    if line_ids:
        for o in (db.query(SurveyRequestOption)
                  .filter(SurveyRequestOption.survey_request_line_id.in_(line_ids),
                          SurveyRequestOption.is_chosen == True).all()):
            chosen[o.survey_request_line_id] = o
        counts = {lid: n for lid, n in
                  db.query(SurveyRequestOption.survey_request_line_id, func.count())
                  .filter(SurveyRequestOption.survey_request_line_id.in_(line_ids))
                  .group_by(SurveyRequestOption.survey_request_line_id).all()}
    codes = {ln.assignee for _s, ln in rows if ln.assignee}
    names = ({e.code: (f"{e.code} — {e.full_name}" if e.full_name else e.code)
              for e in db.query(Employee).filter(Employee.code.in_(codes)).all()} if codes else {})
    company_name = {c.id: c.name for c in db.query(Company).all()}

    today = _today()
    out = []
    for i, (s, ln) in enumerate(rows):
        r = ex.row_values(s, ln, chosen.get(ln.id), counts.get(ln.id, 0),
                          names.get(ln.assignee, ln.assignee or ""),
                          company_name.get(s.company_id, ""), show_supplier, today)
        r["stt"] = start + i + 1
        out.append(r)
    return out


@router.get("")
def list_progress(request: Request, pg: dict = Depends(pagination),
                  db: Session = Depends(get_db), user=Depends(_require_progress)):
    prof = get_perm_profile(db, user)
    show_supplier = _show_supplier(db, user)
    q = _build_query(request, db, user, prof, show_supplier)
    total = q.count()
    rows = q.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": _decorate(db, rows, show_supplier, pg["offset"]),
                    "show_supplier": show_supplier, "states": ex.STATES})


@router.get("/export/xlsx")
def export_xlsx(request: Request, cols: str = "", db: Session = Depends(get_db),
                user=Depends(_require_progress_export)):
    """Xuất Excel theo đúng bộ lọc + cột đang hiện (cùng lối với màn Tiến độ mua hàng)."""
    from app.core.export_xlsx import check_row_limit, pick_columns, xlsx_response

    prof = get_perm_profile(db, user)
    show_supplier = _show_supplier(db, user)
    q = _build_query(request, db, user, prof, show_supplier)
    check_row_limit(q.count())
    rows = _decorate(db, q.all(), show_supplier, 0)
    columns = pick_columns(ex.columns_for(show_supplier), cols)
    return xlsx_response(ex.FILE_NAME, columns, rows, ex.SHEET_TITLE)
