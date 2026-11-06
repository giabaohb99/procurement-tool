"""YCBG — quyền xử lý từng dòng, dòng người gọi được thấy, trạng thái dòng, phân công dòng, kho khảo sát (bao-CR-715
tách từ service.py).
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.central_purchasing import get_central_dept_id

from .model import LINE_STATUSES, LS_COMPLETED, LS_RESURVEY, SurveyRequest, SurveyRequestLine
from .base_service import ENTITY, get_line, get_sr, lines_of, options_of


# Task 2: trạng thái dòng do người YC/phòng ban cập nhật — hằng số gốc nằm ở model.py


def set_line_status(db: Session, sid: int, line_id: int, new_status: str, user_id: int) -> SurveyRequestLine:
    """Đổi trạng thái 1 dòng khảo sát (người YC / cùng phòng ban). Đồng bộ is_completed."""
    new_status = (new_status or "").strip()
    if new_status not in LINE_STATUSES:
        raise HTTPException(400, "Trạng thái dòng không hợp lệ")
    ln = get_line(db, sid, line_id)
    # Chỉ được chốt HOÀN THÀNH sau khi dòng đã chọn 1 phương án (Đã chọn PA).
    # "Cần khảo sát lại" thì KHÔNG cần chọn phương án — đây là lúc kết quả khảo sát
    # chưa đạt, người YC muốn yêu cầu khảo sát lại mà không phải chọn phương án nào.
    if new_status == LS_COMPLETED and not any(o.is_chosen for o in options_of(db, line_id)):
        raise HTTPException(400, "Cần chọn 1 phương án (Đã chọn PA) trước khi chốt Hoàn thành")
    ln.line_status = new_status
    ln.is_completed = (new_status == LS_COMPLETED)
    # Hướng B: gắn cờ "Cần khảo sát lại" thì TỰ BỎ CHỌN mọi phương án — cờ khảo sát lại
    # và "đã chọn PA" là hai trạng thái loại trừ nhau (không cho vừa chê vừa tạo YCMH).
    if new_status == LS_RESURVEY:
        for o in options_of(db, line_id):
            if o.is_chosen:
                o.is_chosen = False
                o.updated_by = user_id
        # Phiếu đã "Đã khảo sát" mà 1 dòng cần khảo sát lại thì phiếu chưa xong khảo sát
        # → hạ về "Đang xử lý" (KHÔNG hạ phiếu đã tạo YCMH/hoàn thành). Chốt lại sẽ đưa về Đã khảo sát.
        sr = get_sr(db, sid)
        if sr.status == "survey_done":
            sr.status = "processing"
            sr.updated_by = user_id
    ln.updated_by = user_id
    db.commit()
    record(db, user_id, ENTITY, sid, "line_status",
           f"Dòng #{line_id} -> {new_status or 'chưa xác định'}")
    db.refresh(ln)
    return ln


def resolve_supplier_name(db: Session, code: str) -> str:
    if not code:
        return ""
    from app.modules.supplier.model import Supplier
    sup = db.query(Supplier).filter(Supplier.code == code).first()
    return sup.name if sup else code


def survey_header(db: Session, survey_id: int):
    """Đầu phiếu khảo sát của một dòng khảo sát SP — chỉ tra mã / phân loại / mã VTBB để
    hiển thị ở ô chọn kho khảo sát (YCMH lẫn YCBG). Khảo sát là dữ liệu tham chiếu, tìm MỞ
    theo thiết kế; phạm vi đã hỏi trên phiếu nền ở route gọi (bao-CR-711 dời từ controller)."""
    from app.modules.survey.model import Survey
    return db.get(Survey, survey_id)


def is_purchaser(profile: dict) -> bool:
    """NSTM/Quản lý/Admin TM = có grant survey_request read với scope proc|dept_proc|all.
    Người YC (own) & trưởng BP (dept) KHÔNG phải purchaser → không xem được màn xử lý (ẩn NCC).
    bao-CR-414: `dept_proc` (thu mua của phòng tự mua) cũng là purchaser."""
    for g in profile.get("grants", []):
        p = g["perms"].get("survey_request")
        if p and p.get("read") and p.get("scope") in ("proc", "dept_proc", "all"):
            return True
    return False


def _has_scope_all(profile: dict | None) -> bool:
    if not profile or not isinstance(profile, dict):
        return True
    for g in profile.get("grants", []):
        p = g["perms"].get("survey_request")
        if p and p.get("read") and p.get("scope") == "all":
            return True
    return False


def can_process_line(db: Session, line: SurveyRequestLine, profile: dict) -> bool:
    """Ai được gắn/xóa option cho 1 dòng:
       - Quản lý/Admin TM (scope=all): mọi dòng.
       - NSTM (scope=proc): là NSTM chính HOẶC phụ của phân loại dòng, hoặc dòng đã gán mã mình."""
    if _has_scope_all(profile):
        return True
    emp_id = profile.get("employee_id") or 0
    emp_code = profile.get("emp_code") or ""
    if emp_code and line.assignee == emp_code:
        return True
    if not emp_id:
        return False
    from app.modules.catalog.model import ItemGroup
    from app.modules.category_assignee.model import CategoryAssignee
    row = (db.query(CategoryAssignee)
           .join(ItemGroup, ItemGroup.id == CategoryAssignee.item_group_id)
           .filter(ItemGroup.name == line.item_group).first())
    return bool(row and emp_id in (row.primary_employee_id, row.backup_employee_id))


def _see_all_lines(profile: dict, s, user) -> bool:
    """Ai thấy HẾT dòng (để phân bổ): người TẠO / người DUYỆT (Admin·Quản lý TM) /
    quản lý theo phạm vi dept·company·all. (Đồng bộ với purchase_request._see_all_items.)"""
    if getattr(user, "id", 0) == getattr(s, "created_by", None):
        return True
    # Người YÊU CẦU (dù admin tạo giùm) cũng thấy HẾT dòng của phiếu mình
    rid = getattr(user, "employee_id", 0) or 0
    if rid and getattr(s, "requester_id", 0) == rid:
        return True
    for g in profile.get("grants", []):
        p = g["perms"].get("survey_request")
        if not p:
            continue
        if p.get("approve"):
            return True
        if p.get("read") and p.get("scope") in ("dept", "company", "all"):
            return True
        # Admin thu mua = đọc-chỉ phạm vi 'proc' (KHÔNG có 'write') -> giám sát toàn quá trình,
        # thấy HẾT dòng. NSTM (có 'write', 'proc') vẫn chỉ thấy dòng được giao để xử lý.
        # bao-CR-414: `dept_proc` (quản lý thu mua của phòng) thấy hết dòng để phân bổ trong phòng.
        if p.get("read") and (p.get("scope") == "dept_proc"
                              or (p.get("scope") == "proc" and not p.get("write"))):
            return True
    return False


def visible_lines_for(db: Session, s, lines, user, profile: dict):
    """Lọc dòng theo NGƯỜI XEM:
    - Người tạo / người duyệt (Admin·Quản lý TM) / quản lý dept·company·all -> thấy HẾT dòng
      (để phân bổ NSTM cho từng dòng).
    - NSTM -> chỉ thấy dòng mình xử lý được (được giao / phụ trách phân loại)."""
    if _see_all_lines(profile, s, user):
        return list(lines)
    return [ln for ln in lines if can_process_line(db, ln, profile)]


def normalize_filter_values(value) -> list[str]:
    """Một chuỗi hay một danh sách chuỗi → danh sách đã bỏ rỗng (bao-CR-487).

    Ô lọc NCC / phân loại nay chọn được NHIỀU; đường gọi cũ (màn Xử lý YCMH, bản v1 chưa
    đổi) vẫn truyền một chuỗi — hai dạng cùng đi qua đây để phần lọc bên dưới chỉ có một luật.
    """
    if value is None:
        return []
    items = [value] if isinstance(value, str) else list(value)
    return [str(v).strip() for v in items if str(v or "").strip()]


def available_survey_lines(db: Session, supplier_code: "str | list[str]" = "",
                           item_group: "str | list[str]" = "",
                           search: str = "", page: int = 1, page_size: int = 8,
                           sort_by: str = "", sort_dir: str = "desc"):
    """Dòng khảo sát SẢN PHẨM đã DUYỆT (line_approve='Đã duyệt') — nguồn để tạo option.
    Dùng cho CHỌN NCC THỦ CÔNG: lọc mở theo nhiều tiêu chí (tùy chọn, KHÔNG giới hạn liên kết YCKS):
    - supplier_code: theo NCC — một mã hoặc NHIỀU mã (bao-CR-487), nhiều mã nghĩa là HOẶC.
    - item_group: theo PHÂN LOẠI của Survey cha — một hoặc nhiều (mặc định = phân loại dòng, đổi được).
    - search: khớp Tên SP hoặc Mã SP theo NCC (LIKE).
    Cần ít nhất 1 tiêu chí (controller đã chặn rỗng).
    Phân trang phía server (kết quả có thể vài trăm dòng) -> trả (items, total)."""
    from sqlalchemy import or_
    from app.modules.survey.model import Survey, SurveyProductLine
    q = (db.query(SurveyProductLine)
         .join(Survey, Survey.id == SurveyProductLine.survey_id)
         .filter(SurveyProductLine.line_approve == "Đã duyệt",
                 Survey.is_deleted.is_(False),   # ai-CR-176: dòng của PKS đã xóa mềm không gợi ý
                 Survey.status.notin_(["cancelled"])))
    supplier_codes = normalize_filter_values(supplier_code)
    item_groups = normalize_filter_values(item_group)
    if supplier_codes:
        q = q.filter(SurveyProductLine.supplier_code.in_(supplier_codes))
    if item_groups:
        q = q.filter(Survey.item_group.in_(item_groups))
    if (search or "").strip():
        like = f"%{search.strip()}%"
        q = q.filter(or_(SurveyProductLine.product_name.ilike(like),
                         SurveyProductLine.internal_code.ilike(like)))
    total = q.count()
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    # Sắp xếp theo cột (whitelist khớp các cột hiển thị ở FE; Mã VTBB nằm ở Survey cha)
    sort_cols = {
        #  duoc-CR-738: cột ID tự thêm của bảng chọn ở giao diện v2 gửi `sort_by=id`.
        "id": SurveyProductLine.id,
        "supplier_code": SurveyProductLine.supplier_code,
        "product_name": SurveyProductLine.product_name,
        "result_date": SurveyProductLine.result_date,
        "spec": SurveyProductLine.spec,
        "origin": SurveyProductLine.origin,
        "price_by_volume": SurveyProductLine.price_by_volume,
        "moq": SurveyProductLine.moq,
        "quote_unit": SurveyProductLine.quote_unit,
        "lab_result": SurveyProductLine.lab_result,
        "survey_item_code": Survey.item_code,
    }
    col = sort_cols.get(sort_by or "")
    if col is not None:
        order = col.desc() if str(sort_dir).lower() == "desc" else col.asc()
    else:
        order = SurveyProductLine.id.desc()   # mặc định: mới nhất trước
    items = (q.order_by(order)
             .offset((page - 1) * page_size).limit(page_size).all())
    return items, total


def auto_assign(db: Session, s: SurveyRequest, allow_global_assignee: bool = True) -> int:
    """Sau khi trưởng phòng duyệt: tự gán NSTM cho TỪNG DÒNG theo phân loại (tái dùng Task 4).
    KHÔNG ghi NSTM ở đầu phiếu — một phiếu có thể do nhiều NSTM khảo sát, việc thuộc về dòng.

    bao-CR-414 (GĐ2): tra bảng phân công theo PHÒNG ĐANG XỬ LÝ phiếu (phòng được nhờ, không thì
    phòng lập phiếu); `allow_global_assignee=False` (người duyệt chỉ có bậc `dept_proc`) thì
    không rơi về bộ của phòng thu mua mặc định (bao-CR-524, trước là "Thu mua chung")."""
    from app.modules.category_assignee.service import handling_dept_of, resolve_for_group
    dept_id = handling_dept_of(s, get_central_dept_id(db))
    assigned = 0
    for ln in lines_of(db, s.id):
        if ln.assignee:
            continue
        emp = resolve_for_group(db, ln.item_group, dept_id, allow_global_assignee)
        if emp and emp.code:
            ln.assignee = emp.code
            if not ln.received_date:                          # Ngày tiếp nhận = ngày NSTM được gán
                ln.received_date = datetime.now().strftime("%Y-%m-%d")
            assigned += 1
    if assigned:
        db.commit()
    return assigned


def set_line_assignee(db: Session, sid: int, line_id: int, assignee: str, user_id: int) -> SurveyRequestLine:
    """Gán/đổi NSTM phụ trách một dòng; Ngày tiếp nhận = ngày được gán (bỏ gán thì xóa).

    bao-CR-486: người phụ trách phải thuộc phòng xử lý của phiếu.
    """
    ln = db.query(SurveyRequestLine).filter(SurveyRequestLine.id == line_id,
                                            SurveyRequestLine.survey_request_id == sid).first()
    if not ln:
        raise HTTPException(404, "Không tìm thấy dòng")
    from app.modules.category_assignee.service import check_assignee_allowed
    check_assignee_allowed(db, get_sr(db, sid), assignee or "")
    ln.assignee = (assignee or "").strip()
    # Ngày tiếp nhận = ngày NSTM được gán (tự tính); bỏ gán thì xóa
    if ln.assignee and not ln.received_date:
        ln.received_date = datetime.now().strftime("%Y-%m-%d")
    elif not ln.assignee:
        ln.received_date = ""
    ln.updated_by = user_id
    db.commit()
    return ln
