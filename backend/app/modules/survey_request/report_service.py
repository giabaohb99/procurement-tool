"""Nghiệp vụ khối Báo cáo thực hiện của phiếu YCBG.

⚠️ Không hàm nào ở đây xét quyền — chốt nằm ở `report_controller`: phạm vi lấy
từ phiếu CHA (`_in_scope`) rồi cửa ghi gác bằng cờ `process` (NS Thu mua).
Mọi hàm ghi KHÔNG commit; controller commit một lượt rồi ghi audit.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from .model import SurveyRequestLine
from .report_constants import (DEFAULT_PHASES, DEFAULT_TEMPLATE_DOCS, MAX_DEPENDS,
                               RD_DONE, REPORT_DOC_STATUS_LABELS)
from .report_model import (SurveyReportDoc, SurveyReportItem,
                           SurveyReportPhase, SurveyReportTrash)


def _to_date(value: str | None) -> date | None:
    """Chuỗi `yyyy-mm-dd` (đã được schema kiểm) → `date`; rỗng/None → None."""
    if not value:
        return None
    return date.fromisoformat(value)


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
    #  Tên nhân sự thực hiện resolve MỘT LƯỢT (tránh N+1) — id chết (nhân sự đã
    #  xóa) ra chuỗi rỗng, FE hiện «Chưa cử». Không join vì chỉ cần tên.
    assignee_ids = {d.assignee_id for d in docs if d.assignee_id}
    names: dict[int, str] = {}
    if assignee_ids:
        names = {eid: full_name for eid, full_name in
                 db.query(Employee.id, Employee.full_name)
                 .filter(Employee.id.in_(assignee_ids)).all()}
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
            "start_date": d.start_date.isoformat() if d.start_date else "",
            "expires_at": d.expires_at.isoformat() if d.expires_at else "",
            "assignee_id": d.assignee_id,
            "assignee_name": names.get(d.assignee_id, ""),
            "sort_order": d.sort_order,
        } for d in docs],
        #  Có bản xóa gần nhất chưa hoàn tác không → FE hiện nút «Hoàn tác» đúng
        #  dòng lịch sử (`restorable_audit_id`). Chỉ có nghĩa khi khối đang RỖNG.
        **_restorable_fields(db, sr_id),
    }


def _latest_trash(db: Session, sr_id: int) -> SurveyReportTrash | None:
    return (db.query(SurveyReportTrash)
            .filter(SurveyReportTrash.survey_request_id == sr_id,
                    SurveyReportTrash.restored.is_(False))
            .order_by(SurveyReportTrash.id.desc())
            .first())


def _restorable_fields(db: Session, sr_id: int) -> dict:
    trash = _latest_trash(db, sr_id)
    return {
        "restorable": trash is not None,
        "restorable_audit_id": trash.audit_id if trash else 0,
    }


def snapshot_report(db: Session, sr_id: int) -> dict:
    """Ảnh chụp ĐẦY ĐỦ khối báo cáo để hoàn tác — giữ id CŨ để dựng lại `depends`.

    Không dùng `get_report_payload` (nó lọc id chết, thêm nhãn dẫn xuất) — snapshot
    cần dữ liệu THÔ và trung thực để khôi phục nguyên trạng.
    """
    return {
        "items": [{"id": r.id, "name": r.name, "sort_order": r.sort_order}
                  for r in _rows_of(db, SurveyReportItem, sr_id)],
        "phases": [{"id": r.id, "name": r.name, "location": r.location, "sort_order": r.sort_order}
                   for r in _rows_of(db, SurveyReportPhase, sr_id)],
        "docs": [{
            "id": d.id, "phase_id": d.phase_id, "item_id": d.item_id,
            "title": d.title, "description": d.description, "required": d.required,
            "status": d.status, "file_note": d.file_note, "depends": list(d.depends or []),
            "start_date": d.start_date.isoformat() if d.start_date else "",
            "expires_at": d.expires_at.isoformat() if d.expires_at else "",
            "assignee_id": d.assignee_id, "sort_order": d.sort_order,
        } for d in _rows_of(db, SurveyReportDoc, sr_id)],
    }


def delete_all(db: Session, sr_id: int, user_id: int) -> SurveyReportTrash:
    """Xóa CẢ khối báo cáo, giữ ảnh chụp vào sọt rác để hoàn tác. KHÔNG commit.

    `audit_id` để 0, nơi gọi (controller) gắn sau khi ghi dòng lịch sử để lấy id.
    """
    snap = snapshot_report(db, sr_id)
    trash = SurveyReportTrash(survey_request_id=sr_id, snapshot=snap,
                              doc_count=len(snap["docs"]),
                              created_by=user_id, updated_by=user_id)
    db.add(trash)
    for model in (SurveyReportDoc, SurveyReportItem, SurveyReportPhase):
        db.query(model).filter(model.survey_request_id == sr_id).delete(synchronize_session=False)
    db.flush()
    return trash


def restore_latest(db: Session, sr_id: int, user_id: int) -> SurveyReportTrash | None:
    """Dựng lại khối từ bản xóa gần nhất chưa hoàn tác. KHÔNG commit.

    Id thay đổi khi tạo lại, nên phải ÁNH XẠ id cũ→mới cho cả `phase_id`,
    `item_id` lẫn `depends`. Trả về trash đã khôi phục, hoặc None nếu không có.
    Nếu khối hiện KHÔNG rỗng (đã dựng lại khác) thì bỏ qua để không nhân đôi.
    """
    trash = _latest_trash(db, sr_id)
    if not trash:
        return None
    if db.query(SurveyReportDoc.id).filter_by(survey_request_id=sr_id).first() \
            or db.query(SurveyReportPhase.id).filter_by(survey_request_id=sr_id).first() \
            or db.query(SurveyReportItem.id).filter_by(survey_request_id=sr_id).first():
        # Khối không rỗng — coi như đã có nội dung mới, chỉ đánh dấu đã hoàn tác.
        trash.restored = True
        trash.updated_by = user_id
        return trash
    snap = trash.snapshot or {}
    phase_map: dict[int, int] = {}
    for p in snap.get("phases", []):
        row = SurveyReportPhase(survey_request_id=sr_id, name=p["name"],
                                location=p.get("location", ""), sort_order=p.get("sort_order", 0),
                                created_by=user_id, updated_by=user_id)
        db.add(row)
        db.flush()
        phase_map[p["id"]] = row.id
    item_map: dict[int, int] = {}
    for it in snap.get("items", []):
        row = SurveyReportItem(survey_request_id=sr_id, name=it["name"],
                               sort_order=it.get("sort_order", 0),
                               created_by=user_id, updated_by=user_id)
        db.add(row)
        db.flush()
        item_map[it["id"]] = row.id
    doc_map: dict[int, int] = {}
    new_docs: list[tuple[SurveyReportDoc, list[int]]] = []
    for d in snap.get("docs", []):
        row = SurveyReportDoc(
            survey_request_id=sr_id,
            phase_id=phase_map.get(d.get("phase_id", 0), 0),
            item_id=item_map.get(d.get("item_id", 0), 0) if d.get("item_id") else 0,
            title=d["title"], description=d.get("description", ""),
            required=d.get("required", True), status=d.get("status", 0),
            file_note=d.get("file_note", ""),
            start_date=_to_date(d.get("start_date")), expires_at=_to_date(d.get("expires_at")),
            assignee_id=d.get("assignee_id", 0), sort_order=d.get("sort_order", 0),
            depends=[], created_by=user_id, updated_by=user_id)
        db.add(row)
        db.flush()
        doc_map[d["id"]] = row.id
        new_docs.append((row, list(d.get("depends", []))))
    for row, old_deps in new_docs:            # ánh xạ tiên quyết sau khi có đủ id mới
        row.depends = [doc_map[o] for o in old_deps if o in doc_map]
    trash.restored = True
    trash.updated_by = user_id
    db.flush()
    return trash


def required_docs_pending(db: Session, sr_id: int) -> list[SurveyReportDoc]:
    """Hồ sơ BẮT BUỘC chưa Hoàn thành của khối báo cáo.

    Rỗng = đủ điều kiện đóng phiếu (không có hồ sơ bắt buộc, hoặc mọi hồ sơ bắt
    buộc đã Hoàn thành). Dùng để chặn `finalize` — báo cáo là tùy chọn, nhưng khi
    đã khai hồ sơ bắt buộc thì phải hoàn tất trước khi đóng phiếu.
    """
    return (db.query(SurveyReportDoc)
            .filter(SurveyReportDoc.survey_request_id == sr_id,
                    SurveyReportDoc.required.is_(True),
                    SurveyReportDoc.status != RD_DONE)
            .order_by(SurveyReportDoc.sort_order, SurveyReportDoc.id)
            .all())


def _line_item_name(line: SurveyRequestLine, index: int) -> str:
    """Tên nút mặc định cho một dòng hàng — dòng YCBG không có ô «tên sản phẩm»
    nên lấy thứ gần nhất người đọc nhận ra: mô tả yêu cầu, rồi phân loại."""
    for raw in (line.requirement_detail, line.item_group):
        name = (raw or "").strip().splitlines()[0][:100] if (raw or "").strip() else ""
        if name:
            return name
    return f"Dòng {index + 1}"


def init_report(db: Session, sr_id: int, user_id: int) -> int:
    """Khởi tạo báo cáo mẫu: 5 giai đoạn + một nút cho mỗi dòng hàng + bộ hồ sơ
    CHUNG của mẫu (`apply_template`). Trả về số hồ sơ đã dựng.

    Idempotent: khối đã có giai đoạn hoặc nút thì KHÔNG đụng gì (trả -1) — bấm
    hai lần không nhân đôi khung. Muốn thêm hồ sơ mẫu vào khối đang có thì đi
    đường «Tạo mẫu» (`apply_template`), nó cộng thêm và bỏ qua trùng.
    """
    has_any = (db.query(SurveyReportPhase.id).filter_by(survey_request_id=sr_id).first()
               or db.query(SurveyReportItem.id).filter_by(survey_request_id=sr_id).first())
    if has_any:
        return -1
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
    return apply_template(db, sr_id, item_id=0, phase_id=None, user_id=user_id)


def _norm_name(value: str | None) -> str:
    """Khóa so khớp tên giai đoạn / tiêu đề hồ sơ: gộp khoảng trắng, bỏ hoa-thường."""
    return " ".join((value or "").split()).casefold()


def apply_template(db: Session, sr_id: int, item_id: int, phase_id: int | None,
                   user_id: int) -> int:
    """Đổ MẪU CHUNG (`DEFAULT_TEMPLATE_DOCS`) vào một nút dòng hàng, hoặc chỉ vào
    một giai đoạn của nút đó. KHÔNG commit. Trả về số hồ sơ THÊM MỚI.

    - `item_id` 0 = hồ sơ Chung; khác 0 phải là nút của phiếu.
    - `phase_id` None = mọi giai đoạn của mẫu: giai đoạn TRÙNG TÊN thì dùng lại,
      thiếu thì tạo. Có `phase_id` = chỉ phần mẫu của giai đoạn trùng tên với nó;
      giai đoạn người dùng tự đặt tên không có trong mẫu → 400 (không đoán).
    - CỘNG THÊM, không xóa gì: hồ sơ cùng (giai đoạn, nút, tiêu đề) đã có thì bỏ
      qua nhưng vẫn được dùng làm mốc tiên quyết — bấm hai lần không nhân đôi.
    - Tiên quyết trỏ ra ngoài phần được đổ (áp một giai đoạn) thì bỏ, không lỗi.

    Mẫu đang nằm trong mã nguồn; có quản lý mẫu thì thay nguồn ở đây, chữ ký giữ.
    """
    _check_refs(db, sr_id, phase_id, item_id)
    phases = _rows_of(db, SurveyReportPhase, sr_id)
    phase_of_no: dict[int, SurveyReportPhase] = {}
    if phase_id is not None:
        target = next(p for p in phases if p.id == phase_id)
        for no, (name, _) in enumerate(DEFAULT_PHASES, start=1):
            if _norm_name(name) == _norm_name(target.name):
                phase_of_no[no] = target
                break
        if not phase_of_no:
            names = " · ".join(n for n, _ in DEFAULT_PHASES)
            raise HTTPException(400, f"Giai đoạn '{target.name}' không có trong mẫu chung "
                                     f"(mẫu chỉ có: {names})")
    else:
        by_name: dict[str, SurveyReportPhase] = {}
        for p in phases:
            by_name.setdefault(_norm_name(p.name), p)
        for no, (name, location) in enumerate(DEFAULT_PHASES, start=1):
            row = by_name.get(_norm_name(name))
            if row is None:
                row = create_phase(db, sr_id, name, location, user_id)
            phase_of_no[no] = row

    existing = {(d.phase_id, _norm_name(d.title)): d.id
                for d in _rows_of(db, SurveyReportDoc, sr_id) if d.item_id == item_id}
    id_of_no: dict[int, int] = {}                 # số thứ tự trong mẫu → id hồ sơ
    created: list[tuple[SurveyReportDoc, list[int]]] = []
    for no, (phase_no, title, description, required, depends) in enumerate(
            DEFAULT_TEMPLATE_DOCS, start=1):
        phase = phase_of_no.get(phase_no)
        if phase is None:
            continue
        key = (phase.id, _norm_name(title))
        if key in existing:
            id_of_no[no] = existing[key]
            continue
        row = SurveyReportDoc(survey_request_id=sr_id, phase_id=phase.id, item_id=item_id,
                              title=title, description=description, required=required,
                              depends=[], sort_order=_next_order(db, SurveyReportDoc, sr_id),
                              created_by=user_id, updated_by=user_id)
        db.add(row)
        db.flush()
        id_of_no[no] = row.id
        created.append((row, list(depends)))
    for row, depends in created:                  # nối tiên quyết sau khi có đủ id
        row.depends = [id_of_no[no] for no in depends if no in id_of_no]
    db.flush()
    return len(created)


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
                          start_date=_to_date(data.start_date),
                          expires_at=_to_date(data.expires_at),
                          assignee_id=data.assignee_id,
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
    #  Ngày tách riêng: '' nghĩa là XÓA ngày (ghi None), khác với không gửi. Vòng
    #  generic bên dưới bỏ qua mọi None nên không phân biệt được hai ca đó.
    for key in ("start_date", "expires_at"):
        if key in changes:
            setattr(row, key, _to_date(changes.pop(key)))
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
