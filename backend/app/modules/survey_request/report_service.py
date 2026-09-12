"""Nghiệp vụ khối Báo cáo thực hiện của phiếu YCBG.

⚠️ Không hàm nào ở đây xét quyền — chốt nằm ở `report_controller`: phạm vi lấy
từ phiếu CHA (`_in_scope`) rồi cửa ghi gác bằng cờ `process` (NS Thu mua).
Mọi hàm ghi KHÔNG commit; controller commit một lượt rồi ghi audit.
"""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from .model import SurveyRequestLine
from .report_constants import DEFAULT_PHASES, MAX_DEPENDS, REPORT_DOC_STATUS_LABELS
from .report_model import SurveyReportDoc, SurveyReportItem, SurveyReportPhase


def _rows_of(db: Session, model, sr_id: int) -> list:
    return (db.query(model)
            .filter(model.survey_request_id == sr_id)
            .order_by(model.sort_order, model.id)
            .all())


def get_report_payload(db: Session, sr_id: int) -> dict:
    """Toàn bộ khối báo cáo của một phiếu — nút, giai đoạn, hồ sơ.

    `depends` trả đã LỌC id chết (hồ sơ tiên quyết bị xóa giữa chừng): id chết
    mà lọt ra thì tầng hiển thị đếm nó là «chưa xong» và hồ sơ khóa vĩnh viễn.
    """
    docs = _rows_of(db, SurveyReportDoc, sr_id)
    alive_ids = {d.id for d in docs}
    return {
        "items": [{"id": r.id, "name": r.name, "sort_order": r.sort_order}
                  for r in _rows_of(db, SurveyReportItem, sr_id)],
        "phases": [{"id": r.id, "name": r.name, "location": r.location, "sort_order": r.sort_order}
                   for r in _rows_of(db, SurveyReportPhase, sr_id)],
        "docs": [{
            "id": d.id,
            "phase_id": d.phase_id,
            "item_id": d.item_id,
            "title": d.title,
            "description": d.description,
            "required": d.required,
            "status": d.status,
            "status_label": REPORT_DOC_STATUS_LABELS.get(d.status, ""),
            "file_note": d.file_note,
            "depends": [i for i in (d.depends or []) if i in alive_ids],
            "sort_order": d.sort_order,
        } for d in docs],
    }


def _line_item_name(line: SurveyRequestLine, index: int) -> str:
    """Tên nút mặc định cho một dòng hàng — dòng YCBG không có ô «tên sản phẩm»
    nên lấy thứ gần nhất người đọc nhận ra: mô tả yêu cầu, rồi phân loại."""
    for raw in (line.requirement_detail, line.item_group):
        name = (raw or "").strip().splitlines()[0][:100] if (raw or "").strip() else ""
        if name:
            return name
    return f"Dòng {index + 1}"


def init_report(db: Session, sr_id: int, user_id: int) -> bool:
    """Khởi tạo bộ khung mặc định: 5 giai đoạn mẫu + một nút cho mỗi dòng hàng.

    Idempotent: khối đã có giai đoạn hoặc nút thì KHÔNG đụng gì (trả False) —
    bấm hai lần không nhân đôi khung.
    """
    has_any = (db.query(SurveyReportPhase.id).filter_by(survey_request_id=sr_id).first()
               or db.query(SurveyReportItem.id).filter_by(survey_request_id=sr_id).first())
    if has_any:
        return False
    for order, (name, location) in enumerate(DEFAULT_PHASES):
        db.add(SurveyReportPhase(survey_request_id=sr_id, name=name, location=location,
                                 sort_order=order, created_by=user_id, updated_by=user_id))
    lines = (db.query(SurveyRequestLine)
             .filter(SurveyRequestLine.survey_request_id == sr_id)
             .order_by(SurveyRequestLine.id).all())
    for order, line in enumerate(lines):
        db.add(SurveyReportItem(survey_request_id=sr_id, name=_line_item_name(line, order),
                                sort_order=order, created_by=user_id, updated_by=user_id))
    db.flush()
    return True


def _get_or_404(db: Session, model, sr_id: int, row_id: int):
    row = (db.query(model)
           .filter(model.id == row_id, model.survey_request_id == sr_id)
           .first())
    if not row:
        raise HTTPException(404, "Không tìm thấy dữ liệu báo cáo")
    return row


#  Trần SỐ DÒNG của mỗi bảng con trong một phiếu — `sort_order` là SMALLINT nên
#  không có trần thì dòng 32768 tràn số (họ lỗi duoc-CR-316). Con số đặt xa mức
#  dùng thật để không ai đụng trần vì làm việc bình thường.
_ROW_CAPS = {SurveyReportItem: 50, SurveyReportPhase: 50, SurveyReportDoc: 500}


def _next_order(db: Session, model, sr_id: int) -> int:
    count = db.query(model.id).filter(model.survey_request_id == sr_id).count()
    if count >= _ROW_CAPS[model]:
        raise HTTPException(400, f"Đã chạm trần {_ROW_CAPS[model]} dòng của khối báo cáo")
    last = (db.query(model.sort_order)
            .filter(model.survey_request_id == sr_id)
            .order_by(model.sort_order.desc()).first())
    return (last[0] + 1) if last else 0


# ── Nút dòng hàng ───────────────────────────────────────────────────────────────
def create_item(db: Session, sr_id: int, name: str, user_id: int) -> SurveyReportItem:
    row = SurveyReportItem(survey_request_id=sr_id, name=name,
                           sort_order=_next_order(db, SurveyReportItem, sr_id),
                           created_by=user_id, updated_by=user_id)
    db.add(row)
    db.flush()
    return row


def rename_item(db: Session, sr_id: int, item_id: int, name: str, user_id: int) -> SurveyReportItem:
    row = _get_or_404(db, SurveyReportItem, sr_id, item_id)
    row.name = name
    row.updated_by = user_id
    return row


def delete_item(db: Session, sr_id: int, item_id: int, user_id: int) -> str:
    """Xóa một nút. Hồ sơ đang gắn nút đó KHÔNG xóa theo — trả về «Chung»
    (`item_id = 0`): hồ sơ là công sức nhập liệu, nút chỉ là nhãn lọc."""
    row = _get_or_404(db, SurveyReportItem, sr_id, item_id)
    moved = (db.query(SurveyReportDoc)
             .filter(SurveyReportDoc.survey_request_id == sr_id,
                     SurveyReportDoc.item_id == item_id)
             .all())
    for doc in moved:
        doc.item_id = 0
        doc.updated_by = user_id
    name = row.name
    db.delete(row)
    return name


# ── Giai đoạn ───────────────────────────────────────────────────────────────────
def create_phase(db: Session, sr_id: int, name: str, location: str, user_id: int) -> SurveyReportPhase:
    row = SurveyReportPhase(survey_request_id=sr_id, name=name, location=location,
                            sort_order=_next_order(db, SurveyReportPhase, sr_id),
                            created_by=user_id, updated_by=user_id)
    db.add(row)
    db.flush()
    return row


def update_phase(db: Session, sr_id: int, phase_id: int, name: str, location: str,
                 user_id: int) -> SurveyReportPhase:
    row = _get_or_404(db, SurveyReportPhase, sr_id, phase_id)
    row.name = name
    row.location = location
    row.updated_by = user_id
    return row


def delete_phase(db: Session, sr_id: int, phase_id: int) -> str:
    """Chặn xóa giai đoạn còn hồ sơ — xóa lây là mất dữ liệu nhập tay; muốn bỏ
    thì chuyển hồ sơ sang giai đoạn khác trước."""
    row = _get_or_404(db, SurveyReportPhase, sr_id, phase_id)
    count = (db.query(SurveyReportDoc.id)
             .filter(SurveyReportDoc.survey_request_id == sr_id,
                     SurveyReportDoc.phase_id == phase_id)
             .count())
    if count:
        raise HTTPException(400, f"Giai đoạn còn {count} hồ sơ — chuyển hồ sơ sang "
                                 "giai đoạn khác trước khi xóa")
    name = row.name
    db.delete(row)
    return name


# ── Hồ sơ ───────────────────────────────────────────────────────────────────────
def _check_refs(db: Session, sr_id: int, phase_id: int | None, item_id: int | None) -> None:
    if phase_id is not None:
        _get_or_404(db, SurveyReportPhase, sr_id, phase_id)
    if item_id:                                  # 0 = Chung, không cần tra
        _get_or_404(db, SurveyReportItem, sr_id, item_id)


def check_depends(db: Session, sr_id: int, doc_id: int, depends: list[int]) -> list[int]:
    """Kiểm danh sách tiên quyết: cùng phiếu, không tự trỏ mình, không tạo VÒNG.

    Vòng tiên quyết (A chờ B, B chờ A) làm cả cụm khóa vĩnh viễn mà không ai
    hiểu vì sao — chặn lúc lưu, đừng để nó thành dữ liệu. Vòng dò có trần độ
    sâu, và CHẠM TRẦN LÀ CHẶN chứ không trả về im lặng («dò không thấy» không
    phải «không có» — bài học `block_manager_cycle`).
    """
    depends = list(dict.fromkeys(int(i) for i in depends))       # khử trùng, giữ thứ tự
    if not depends:
        return []
    if doc_id and doc_id in depends:
        raise HTTPException(400, "Hồ sơ không thể là tiên quyết của chính nó")
    rows = (db.query(SurveyReportDoc.id, SurveyReportDoc.depends)
            .filter(SurveyReportDoc.survey_request_id == sr_id)
            .all())
    graph = {rid: list(deps or []) for rid, deps in rows}
    unknown = [i for i in depends if i not in graph]
    if unknown:
        raise HTTPException(400, "Hồ sơ tiên quyết không thuộc phiếu này")
    if doc_id:
        graph[doc_id] = depends                  # đồ thị SAU khi lưu
        seen: set[int] = set()
        stack = list(depends)
        steps = 0
        while stack:
            steps += 1
            if steps > MAX_DEPENDS * (len(graph) + 1):
                raise HTTPException(400, "Chuỗi tiên quyết quá sâu — rà lại các hồ sơ tiên quyết")
            cur = stack.pop()
            if cur == doc_id:
                raise HTTPException(400, "Chuỗi tiên quyết tạo thành vòng lặp — hồ sơ sẽ "
                                         "khóa lẫn nhau vĩnh viễn")
            if cur in seen:
                continue
            seen.add(cur)
            stack.extend(graph.get(cur, []))
    return depends


def create_doc(db: Session, sr_id: int, data, user_id: int) -> SurveyReportDoc:
    _check_refs(db, sr_id, data.phase_id, data.item_id)
    row = SurveyReportDoc(survey_request_id=sr_id, phase_id=data.phase_id,
                          item_id=data.item_id, title=data.title,
                          description=data.description, required=data.required,
                          status=data.status, file_note=data.file_note,
                          sort_order=_next_order(db, SurveyReportDoc, sr_id),
                          created_by=user_id, updated_by=user_id)
    db.add(row)
    db.flush()
    row.depends = check_depends(db, sr_id, row.id, data.depends)
    return row


def update_doc(db: Session, sr_id: int, doc_id: int, data, user_id: int) -> SurveyReportDoc:
    row = _get_or_404(db, SurveyReportDoc, sr_id, doc_id)
    changes = data.model_dump(exclude_unset=True)
    _check_refs(db, sr_id, changes.get("phase_id"), changes.get("item_id"))
    if "depends" in changes and changes["depends"] is not None:
        changes["depends"] = check_depends(db, sr_id, doc_id, changes["depends"])
    for key, value in changes.items():
        if value is not None:
            setattr(row, key, value)
    row.updated_by = user_id
    return row


def delete_doc(db: Session, sr_id: int, doc_id: int, user_id: int) -> str:
    """Xóa một hồ sơ và GỠ nó khỏi danh sách tiên quyết của các hồ sơ khác —
    để lại id chết là hồ sơ khác khóa vĩnh viễn theo một thứ không còn tồn tại."""
    row = _get_or_404(db, SurveyReportDoc, sr_id, doc_id)
    others = (db.query(SurveyReportDoc)
              .filter(SurveyReportDoc.survey_request_id == sr_id,
                      SurveyReportDoc.id != doc_id)
              .all())
    for other in others:
        deps = list(other.depends or [])
        if doc_id in deps:
            other.depends = [i for i in deps if i != doc_id]
            other.updated_by = user_id
    title = row.title
    db.delete(row)
    return title
