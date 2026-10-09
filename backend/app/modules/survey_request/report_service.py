"""Nghiệp vụ khối Báo cáo thực hiện — dùng chung cho YCBG và ĐMH (bao-CR-602).

Mọi hàm nhận `report_id` = id dòng ĐẦU `tab_exec_report`; chứng từ chủ → đầu
báo cáo đi qua `find_report` / `ensure_report`. Không hàm nào ở đây xét quyền —
chốt nằm ở `report_controller`: phạm vi lấy từ chứng từ CHA (`_in_scope`) rồi
cửa ghi gác bằng cờ ghi của cha. Mọi hàm ghi KHÔNG commit; controller commit một
lượt rồi ghi audit.
"""
from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.modules.employee.model import Employee

from .model import SurveyRequestLine
from .report_constants import (DEFAULT_PHASES, MAX_DEPENDS, RD_DONE, REPORT_DOC_STATUS_LABELS,
                               REPORT_TEMPLATES, RT_COMMON)
from .report_model import (REPORT_OWNER_ENTITIES, ExecReport, SurveyReportDoc,
                           SurveyReportItem, SurveyReportPhase, SurveyReportTrash)

#  Một dòng chứng từ nhìn từ khối báo cáo: (id dòng, tên hiện trên nút).
LineRef = tuple[int, str]


def _to_date(value: str | None) -> date | None:
    """Chuỗi `yyyy-mm-dd` (đã được schema kiểm) → `date`; rỗng/None → None."""
    if not value:
        return None
    return date.fromisoformat(value)


# ── Đầu báo cáo: chứng từ chủ ↔ report_id ───────────────────────────────────────
def _check_owner(entity: str) -> None:
    if entity not in REPORT_OWNER_ENTITIES:
        raise HTTPException(404, "Loại chứng từ không có khối báo cáo thực hiện")


def find_report(db: Session, entity: str, owner_id: int) -> ExecReport | None:
    """Đầu báo cáo của một chứng từ — None khi chứng từ chưa từng có khối."""
    _check_owner(entity)
    return (db.query(ExecReport)
            .filter(ExecReport.owner_entity == entity, ExecReport.owner_id == owner_id)
            .first())


def report_id_of(db: Session, entity: str, owner_id: int) -> int:
    """`report_id` của chứng từ, 0 nếu chưa có đầu — các hàm đọc nhận 0 và trả khối rỗng."""
    head = find_report(db, entity, owner_id)
    return head.id if head else 0


def ensure_report(db: Session, entity: str, owner_id: int, user_id: int) -> ExecReport:
    """Đầu báo cáo của chứng từ — có rồi thì trả, chưa có thì tạo (flush, KHÔNG commit).

    Gọi ở mọi cửa GHI: khối chỉ có đầu khi có người bắt đầu khai, nên GET của
    một chứng từ không ai đụng tới không đẻ dòng nào.
    """
    head = find_report(db, entity, owner_id)
    if head is None:
        head = ExecReport(owner_entity=entity, owner_id=owner_id,
                          created_by=user_id, updated_by=user_id)
        db.add(head)
        db.flush()
    return head


def _rows_of(db: Session, model, report_id: int) -> list:
    return (db.query(model)
            .filter(model.report_id == report_id)
            .order_by(model.sort_order, model.id)
            .all())


def get_report_payload(db: Session, report_id: int) -> dict:
    """Toàn bộ khối báo cáo — nút, giai đoạn, hồ sơ. `report_id = 0` → khối rỗng.

    `depends` trả đã LỌC id chết (hồ sơ tiên quyết bị xóa giữa chừng): id chết
    mà lọt ra thì tầng hiển thị đếm nó là «chưa xong» và hồ sơ khóa vĩnh viễn.
    """
    docs = _rows_of(db, SurveyReportDoc, report_id)
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
        "items": [{"id": r.id, "name": r.name, "line_id": r.line_id, "sort_order": r.sort_order}
                  for r in _rows_of(db, SurveyReportItem, report_id)],
        "phases": [{"id": r.id, "name": r.name, "location": r.location, "sort_order": r.sort_order}
                   for r in _rows_of(db, SurveyReportPhase, report_id)],
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
            "result": d.result,
            "depends": [i for i in (d.depends or []) if i in alive_ids],
            "start_date": d.start_date.isoformat() if d.start_date else "",
            "expires_at": d.expires_at.isoformat() if d.expires_at else "",
            "planned_date": d.planned_date.isoformat() if d.planned_date else "",
            "assignee_id": d.assignee_id,
            "assignee_name": names.get(d.assignee_id, ""),
            "sort_order": d.sort_order,
        } for d in docs],
        #  Có bản xóa gần nhất chưa hoàn tác không → FE hiện nút «Hoàn tác» đúng
        #  dòng lịch sử (`restorable_audit_id`). Chỉ có nghĩa khi khối đang RỖNG.
        **_restorable_fields(db, report_id),
    }


def _latest_trash(db: Session, report_id: int) -> SurveyReportTrash | None:
    return (db.query(SurveyReportTrash)
            .filter(SurveyReportTrash.report_id == report_id,
                    SurveyReportTrash.restored.is_(False))
            .order_by(SurveyReportTrash.id.desc())
            .first())


def _restorable_fields(db: Session, report_id: int) -> dict:
    trash = _latest_trash(db, report_id)
    return {
        "restorable": trash is not None,
        "restorable_audit_id": trash.audit_id if trash else 0,
    }


def snapshot_report(db: Session, report_id: int) -> dict:
    """Ảnh chụp ĐẦY ĐỦ khối báo cáo để hoàn tác — giữ id CŨ để dựng lại `depends`.

    Không dùng `get_report_payload` (nó lọc id chết, thêm nhãn dẫn xuất) — snapshot
    cần dữ liệu THÔ và trung thực để khôi phục nguyên trạng.
    """
    head = db.get(ExecReport, report_id)
    return {
        #  Mẫu của khối (duoc-CR-614) — hoàn tác phải trả cả mẫu, không thì «Tạo mẫu»
        #  sau hoàn tác đổ nhầm mẫu của lần khởi tạo xen giữa.
        "template": head.template if head else RT_COMMON,
        "items": [{"id": r.id, "name": r.name, "line_id": r.line_id, "sort_order": r.sort_order}
                  for r in _rows_of(db, SurveyReportItem, report_id)],
        "phases": [{"id": r.id, "name": r.name, "location": r.location, "sort_order": r.sort_order}
                   for r in _rows_of(db, SurveyReportPhase, report_id)],
        "docs": [{
            "id": d.id, "phase_id": d.phase_id, "item_id": d.item_id,
            "title": d.title, "description": d.description, "required": d.required,
            "status": d.status, "file_note": d.file_note, "result": d.result,
            "depends": list(d.depends or []),
            "start_date": d.start_date.isoformat() if d.start_date else "",
            "expires_at": d.expires_at.isoformat() if d.expires_at else "",
            "planned_date": d.planned_date.isoformat() if d.planned_date else "",
            "assignee_id": d.assignee_id, "sort_order": d.sort_order,
        } for d in _rows_of(db, SurveyReportDoc, report_id)],
    }


def delete_all(db: Session, report_id: int, user_id: int) -> SurveyReportTrash:
    """Xóa CẢ khối báo cáo, giữ ảnh chụp vào sọt rác để hoàn tác. KHÔNG commit.

    `audit_id` để 0, nơi gọi (controller) gắn sau khi ghi dòng lịch sử để lấy id.
    """
    snap = snapshot_report(db, report_id)
    trash = SurveyReportTrash(report_id=report_id, snapshot=snap,
                              doc_count=len(snap["docs"]),
                              created_by=user_id, updated_by=user_id)
    db.add(trash)
    for model in (SurveyReportDoc, SurveyReportItem, SurveyReportPhase):
        db.query(model).filter(model.report_id == report_id).delete(synchronize_session=False)
    db.flush()
    return trash


def restore_latest(db: Session, report_id: int, user_id: int) -> SurveyReportTrash | None:
    """Dựng lại khối từ bản xóa gần nhất chưa hoàn tác. KHÔNG commit.

    Id thay đổi khi tạo lại, nên phải ÁNH XẠ id cũ→mới cho cả `phase_id`,
    `item_id` lẫn `depends`. Trả về trash đã khôi phục, hoặc None nếu không có.
    Nếu khối hiện KHÔNG rỗng (đã dựng lại khác) thì bỏ qua để không nhân đôi.
    """
    trash = _latest_trash(db, report_id)
    if not trash:
        return None
    if db.query(SurveyReportDoc.id).filter_by(report_id=report_id).first() \
            or db.query(SurveyReportPhase.id).filter_by(report_id=report_id).first() \
            or db.query(SurveyReportItem.id).filter_by(report_id=report_id).first():
        # Khối không rỗng — coi như đã có nội dung mới, chỉ đánh dấu đã hoàn tác.
        trash.restored = True
        trash.updated_by = user_id
        return trash
    snap = trash.snapshot or {}
    head = db.get(ExecReport, report_id)
    #  Ảnh chụp trước duoc-CR-614 không có khóa này — giữ nguyên mẫu đang ghi trên đầu khối.
    if head and snap.get("template") in REPORT_TEMPLATES:
        head.template = snap["template"]
        head.updated_by = user_id
    phase_map: dict[int, int] = {}
    for p in snap.get("phases", []):
        row = SurveyReportPhase(report_id=report_id, name=p["name"],
                                location=p.get("location", ""), sort_order=p.get("sort_order", 0),
                                created_by=user_id, updated_by=user_id)
        db.add(row)
        db.flush()
        phase_map[p["id"]] = row.id
    item_map: dict[int, int] = {}
    for it in snap.get("items", []):
        row = SurveyReportItem(report_id=report_id, name=it["name"],
                               line_id=it.get("line_id", 0), sort_order=it.get("sort_order", 0),
                               created_by=user_id, updated_by=user_id)
        db.add(row)
        db.flush()
        item_map[it["id"]] = row.id
    doc_map: dict[int, int] = {}
    new_docs: list[tuple[SurveyReportDoc, list[int]]] = []
    for d in snap.get("docs", []):
        row = SurveyReportDoc(
            report_id=report_id,
            phase_id=phase_map.get(d.get("phase_id", 0), 0),
            item_id=item_map.get(d.get("item_id", 0), 0) if d.get("item_id") else 0,
            title=d["title"], description=d.get("description", ""),
            required=d.get("required", True), status=d.get("status", 0),
            file_note=d.get("file_note", ""), result=d.get("result", ""),
            start_date=_to_date(d.get("start_date")), expires_at=_to_date(d.get("expires_at")),
            planned_date=_to_date(d.get("planned_date")),
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


def required_docs_pending(db: Session, report_id: int) -> list[SurveyReportDoc]:
    """Hồ sơ BẮT BUỘC chưa Hoàn thành của khối báo cáo.

    Rỗng = đủ điều kiện đóng chứng từ (không có hồ sơ bắt buộc, hoặc mọi hồ sơ
    bắt buộc đã Hoàn thành). Dùng để chặn `finalize` YCBG — báo cáo là tùy chọn,
    nhưng khi đã khai hồ sơ bắt buộc thì phải hoàn tất trước khi đóng phiếu.
    """
    return (db.query(SurveyReportDoc)
            .filter(SurveyReportDoc.report_id == report_id,
                    SurveyReportDoc.required.is_(True),
                    SurveyReportDoc.status != RD_DONE)
            .order_by(SurveyReportDoc.sort_order, SurveyReportDoc.id)
            .all())


def required_docs_pending_of(db: Session, entity: str, owner_id: int) -> list[SurveyReportDoc]:
    """Như `required_docs_pending` nhưng đi từ chứng từ chủ; chưa có đầu báo cáo → rỗng."""
    return required_docs_pending(db, report_id_of(db, entity, owner_id))


def _line_item_name(line: SurveyRequestLine, index: int) -> str:
    """Tên nút mặc định cho một dòng hàng — dòng YCBG không có ô «tên sản phẩm»
    nên lấy thứ gần nhất người đọc nhận ra: mô tả yêu cầu, rồi phân loại."""
    for raw in (line.requirement_detail, line.item_group):
        name = (raw or "").strip().splitlines()[0][:100] if (raw or "").strip() else ""
        if name:
            return name
    return f"Dòng {index + 1}"


def survey_request_lines(db: Session, sid: int) -> list[LineRef]:
    """Dòng hàng của một YCBG dưới dạng (id dòng, tên nút) cho `init_report`."""
    lines = (db.query(SurveyRequestLine)
             .filter(SurveyRequestLine.survey_request_id == sid)
             .order_by(SurveyRequestLine.id).all())
    return [(line.id, _line_item_name(line, index)) for index, line in enumerate(lines)]


def init_report(db: Session, report_id: int, lines: list[LineRef], user_id: int,
                template: int = RT_COMMON) -> int:
    """Khởi tạo báo cáo theo MẪU ĐÃ CHỌN (duoc-CR-614): giai đoạn của mẫu + một nút cho
    mỗi dòng hàng + bộ hồ sơ CHUNG của mẫu (`apply_template`). Mẫu ghi lên đầu khối để
    «Tạo mẫu» về sau đổ đúng mẫu đó. Trả về số hồ sơ đã dựng.

    Idempotent: khối đã có giai đoạn hoặc nút thì KHÔNG đụng gì (trả -1) — bấm
    hai lần không nhân đôi khung. Muốn thêm hồ sơ mẫu vào khối đang có thì đi
    đường «Tạo mẫu» (`apply_template`), nó cộng thêm và bỏ qua trùng.
    """
    if not is_report_empty(db, report_id):
        return -1
    if template not in REPORT_TEMPLATES:
        raise HTTPException(400, "Mẫu báo cáo không hợp lệ")
    _set_template(db, report_id, template, user_id)
    _build_skeleton(db, report_id, lines, user_id, REPORT_TEMPLATES[template][2])
    return apply_template(db, report_id, item_id=0, phase_id=None, user_id=user_id)


def _set_template(db: Session, report_id: int, template: int, user_id: int) -> None:
    head = db.get(ExecReport, report_id)
    if head.template != template:
        head.template = template
        head.updated_by = user_id


def template_of(db: Session, report_id: int) -> int:
    """Mẫu của khối; mã lạ (mẫu đã gỡ khỏi mã nguồn) rơi về mẫu chung thay vì vỡ."""
    head = db.get(ExecReport, report_id)
    code = head.template if head else RT_COMMON
    return code if code in REPORT_TEMPLATES else RT_COMMON


def list_templates() -> list[dict]:
    """Ô chọn mẫu của hộp «Khởi tạo báo cáo mẫu» — đọc từ sổ mẫu, FE không gõ tay danh sách."""
    return [{"id": code, "name": name, "description": description,
             "phase_count": len(phases), "doc_count": len(docs)}
            for code, (name, description, phases, docs) in REPORT_TEMPLATES.items()]


def is_report_empty(db: Session, report_id: int) -> bool:
    """Khối chưa có giai đoạn, nút dòng hàng lẫn hồ sơ nào — đúng trạng thái «lần đầu»."""
    return not (db.query(SurveyReportPhase.id).filter_by(report_id=report_id).first()
                or db.query(SurveyReportItem.id).filter_by(report_id=report_id).first()
                or db.query(SurveyReportDoc.id).filter_by(report_id=report_id).first())


def _build_skeleton(db: Session, report_id: int, lines: list[LineRef], user_id: int,
                    phases=DEFAULT_PHASES) -> None:
    """KHUNG của khối: giai đoạn của mẫu (mặc định 5 giai đoạn của mẫu chung) + một nút cho
    mỗi dòng hàng, CHƯA có hồ sơ."""
    for order, (name, location) in enumerate(phases):
        db.add(SurveyReportPhase(report_id=report_id, name=name, location=location,
                                 sort_order=order, created_by=user_id, updated_by=user_id))
    for order, (line_id, name) in enumerate(lines):
        db.add(SurveyReportItem(report_id=report_id, name=name, line_id=line_id,
                                sort_order=order, created_by=user_id, updated_by=user_id))
    db.flush()


def sync_line_items(db: Session, report_id: int, lines: list[LineRef], user_id: int) -> bool:
    """Đồng bộ nút dòng hàng THEO dòng chứng từ (ĐMH, bao-CR-602). Trả True khi có đổi.

    Chạy mỗi lần đọc khối của ĐMH, vì đơn thêm/bớt/đổi tên dòng ở màn khác mà
    không ai báo cho khối báo cáo. Luật:
    - dòng mới → thêm nút (tên = tên hàng), nối đuôi thứ tự;
    - dòng đổi tên hàng → đổi tên nút;
    - dòng không còn → xóa nút, hồ sơ của nó về Chung (không mất);
    - khối CHƯA khởi tạo (không giai đoạn, không nút) → không làm gì: người chỉ
      xem không được thấy một khối «có nội dung» chỉ vì đơn có dòng hàng.
    Nút đặt tay (`line_id = 0`) không đụng tới.
    """
    items = _rows_of(db, SurveyReportItem, report_id)
    has_phase = db.query(SurveyReportPhase.id).filter_by(report_id=report_id).first() is not None
    if not items and not has_phase:
        return False
    changed = False
    by_line = {item.line_id: item for item in items if item.line_id}
    wanted = {line_id: name for line_id, name in lines if line_id}
    for line_id, item in by_line.items():
        if line_id not in wanted:
            delete_item(db, report_id, item.id, user_id)
            changed = True
        elif item.name != wanted[line_id]:
            item.name = wanted[line_id]
            item.updated_by = user_id
            changed = True
    for line_id, name in lines:
        if line_id and line_id not in by_line:
            create_item(db, report_id, name, user_id, line_id=line_id)
            changed = True
    if changed:
        db.flush()
    return changed


def _norm_name(value: str | None) -> str:
    """Khóa so khớp tên giai đoạn / tiêu đề hồ sơ: gộp khoảng trắng, bỏ hoa-thường."""
    return " ".join((value or "").split()).casefold()


def apply_template(db: Session, report_id: int, item_id: int, phase_id: int | None,
                   user_id: int) -> int:
    """Đổ MẪU CỦA KHỐI (`ExecReport.template`, duoc-CR-614) vào một nút dòng hàng, hoặc
    chỉ vào một giai đoạn của nút đó. KHÔNG commit. Trả về số hồ sơ THÊM MỚI.

    - `item_id` 0 = hồ sơ Chung; khác 0 phải là nút của khối.
    - `phase_id` None = mọi giai đoạn của mẫu: giai đoạn TRÙNG TÊN thì dùng lại,
      thiếu thì tạo. Có `phase_id` = chỉ phần mẫu của giai đoạn trùng tên với nó;
      giai đoạn người dùng tự đặt tên không có trong mẫu → 400 (không đoán).
    - CỘNG THÊM, không xóa gì: hồ sơ cùng (giai đoạn, nút, tiêu đề) đã có thì bỏ
      qua nhưng vẫn được dùng làm mốc tiên quyết — bấm hai lần không nhân đôi.
    - Tiên quyết trỏ ra ngoài phần được đổ (áp một giai đoạn) thì bỏ, không lỗi.

    Mẫu đang nằm trong mã nguồn; có quản lý mẫu thì thay nguồn ở đây, chữ ký giữ.
    """
    _check_refs(db, report_id, phase_id, item_id)
    template_name, _, template_phases, template_docs = REPORT_TEMPLATES[template_of(db, report_id)]
    phases = _rows_of(db, SurveyReportPhase, report_id)
    phase_of_no: dict[int, SurveyReportPhase] = {}
    if phase_id is not None:
        target = next(p for p in phases if p.id == phase_id)
        for no, (name, _) in enumerate(template_phases, start=1):
            if _norm_name(name) == _norm_name(target.name):
                phase_of_no[no] = target
                break
        if not phase_of_no:
            names = " · ".join(n for n, _ in template_phases)
            raise HTTPException(400, f"Giai đoạn '{target.name}' không có trong mẫu "
                                     f"«{template_name}» (mẫu chỉ có: {names})")
    else:
        by_name: dict[str, SurveyReportPhase] = {}
        for p in phases:
            by_name.setdefault(_norm_name(p.name), p)
        for no, (name, location) in enumerate(template_phases, start=1):
            row = by_name.get(_norm_name(name))
            if row is None:
                row = create_phase(db, report_id, name, location, user_id)
            phase_of_no[no] = row

    existing = {(d.phase_id, _norm_name(d.title)): d.id
                for d in _rows_of(db, SurveyReportDoc, report_id) if d.item_id == item_id}
    id_of_no: dict[int, int] = {}                 # số thứ tự trong mẫu → id hồ sơ
    created: list[tuple[SurveyReportDoc, list[int]]] = []
    for no, (phase_no, title, description, required, depends) in enumerate(
            template_docs, start=1):
        phase = phase_of_no.get(phase_no)
        if phase is None:
            continue
        key = (phase.id, _norm_name(title))
        if key in existing:
            id_of_no[no] = existing[key]
            continue
        row = SurveyReportDoc(report_id=report_id, phase_id=phase.id, item_id=item_id,
                              title=title, description=description, required=required,
                              depends=[], sort_order=_next_order(db, SurveyReportDoc, report_id),
                              created_by=user_id, updated_by=user_id)
        db.add(row)
        db.flush()
        id_of_no[no] = row.id
        created.append((row, list(depends)))
    for row, depends in created:                  # nối tiên quyết sau khi có đủ id
        row.depends = [id_of_no[no] for no in depends if no in id_of_no]
    db.flush()
    return len(created)


def _get_or_404(db: Session, model, report_id: int, row_id: int):
    row = (db.query(model)
           .filter(model.id == row_id, model.report_id == report_id)
           .first())
    if not row:
        raise HTTPException(404, "Không tìm thấy dữ liệu báo cáo")
    return row


#  Trần SỐ DÒNG của mỗi bảng con trong một khối — `sort_order` là SMALLINT nên
#  không có trần thì dòng 32768 tràn số (họ lỗi duoc-CR-316). Con số đặt xa mức
#  dùng thật để không ai đụng trần vì làm việc bình thường.
_ROW_CAPS = {SurveyReportItem: 50, SurveyReportPhase: 50, SurveyReportDoc: 500}


def _next_order(db: Session, model, report_id: int) -> int:
    count = db.query(model.id).filter(model.report_id == report_id).count()
    if count >= _ROW_CAPS[model]:
        raise HTTPException(400, f"Đã chạm trần {_ROW_CAPS[model]} dòng của khối báo cáo")
    last = (db.query(model.sort_order)
            .filter(model.report_id == report_id)
            .order_by(model.sort_order.desc()).first())
    return (last[0] + 1) if last else 0


# ── Nút dòng hàng ───────────────────────────────────────────────────────────────
def create_item(db: Session, report_id: int, name: str, user_id: int,
                line_id: int = 0) -> SurveyReportItem:
    row = SurveyReportItem(report_id=report_id, name=name, line_id=line_id,
                           sort_order=_next_order(db, SurveyReportItem, report_id),
                           created_by=user_id, updated_by=user_id)
    db.add(row)
    db.flush()
    return row


def rename_item(db: Session, report_id: int, item_id: int, name: str, user_id: int) -> SurveyReportItem:
    row = _get_or_404(db, SurveyReportItem, report_id, item_id)
    row.name = name
    row.updated_by = user_id
    return row


def delete_item(db: Session, report_id: int, item_id: int, user_id: int) -> str:
    """Xóa một nút. Hồ sơ đang gắn nút đó KHÔNG xóa theo — trả về «Chung»
    (`item_id = 0`): hồ sơ là công sức nhập liệu, nút chỉ là nhãn lọc."""
    row = _get_or_404(db, SurveyReportItem, report_id, item_id)
    moved = (db.query(SurveyReportDoc)
             .filter(SurveyReportDoc.report_id == report_id,
                     SurveyReportDoc.item_id == item_id)
             .all())
    for doc in moved:
        doc.item_id = 0
        doc.updated_by = user_id
    name = row.name
    db.delete(row)
    return name


# ── Giai đoạn ───────────────────────────────────────────────────────────────────
def create_phase(db: Session, report_id: int, name: str, location: str, user_id: int) -> SurveyReportPhase:
    row = SurveyReportPhase(report_id=report_id, name=name, location=location,
                            sort_order=_next_order(db, SurveyReportPhase, report_id),
                            created_by=user_id, updated_by=user_id)
    db.add(row)
    db.flush()
    return row


def update_phase(db: Session, report_id: int, phase_id: int, name: str, location: str,
                 user_id: int) -> SurveyReportPhase:
    row = _get_or_404(db, SurveyReportPhase, report_id, phase_id)
    row.name = name
    row.location = location
    row.updated_by = user_id
    return row


def delete_phase(db: Session, report_id: int, phase_id: int) -> str:
    """Chặn xóa giai đoạn còn hồ sơ — xóa lây là mất dữ liệu nhập tay; muốn bỏ
    thì chuyển hồ sơ sang giai đoạn khác trước."""
    row = _get_or_404(db, SurveyReportPhase, report_id, phase_id)
    count = (db.query(SurveyReportDoc.id)
             .filter(SurveyReportDoc.report_id == report_id,
                     SurveyReportDoc.phase_id == phase_id)
             .count())
    if count:
        raise HTTPException(400, f"Giai đoạn còn {count} hồ sơ — chuyển hồ sơ sang "
                                 "giai đoạn khác trước khi xóa")
    name = row.name
    db.delete(row)
    return name


# ── Hồ sơ ───────────────────────────────────────────────────────────────────────
def _check_refs(db: Session, report_id: int, phase_id: int | None, item_id: int | None) -> None:
    if phase_id is not None:
        _get_or_404(db, SurveyReportPhase, report_id, phase_id)
    if item_id:                                  # 0 = Chung, không cần tra
        _get_or_404(db, SurveyReportItem, report_id, item_id)


def check_depends(db: Session, report_id: int, doc_id: int, depends: list[int]) -> list[int]:
    """Kiểm danh sách tiên quyết: cùng khối, không tự trỏ mình, không tạo VÒNG.

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
            .filter(SurveyReportDoc.report_id == report_id)
            .all())
    graph = {rid: list(deps or []) for rid, deps in rows}
    unknown = [i for i in depends if i not in graph]
    if unknown:
        raise HTTPException(400, "Hồ sơ tiên quyết không thuộc chứng từ này")
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


def create_doc(db: Session, report_id: int, data, user_id: int) -> SurveyReportDoc:
    _check_refs(db, report_id, data.phase_id, data.item_id)
    row = SurveyReportDoc(report_id=report_id, phase_id=data.phase_id,
                          item_id=data.item_id, title=data.title,
                          description=data.description, required=data.required,
                          status=data.status, file_note=data.file_note, result=data.result,
                          start_date=_to_date(data.start_date),
                          expires_at=_to_date(data.expires_at),
                          planned_date=_to_date(data.planned_date),
                          assignee_id=data.assignee_id,
                          sort_order=_next_order(db, SurveyReportDoc, report_id),
                          created_by=user_id, updated_by=user_id)
    db.add(row)
    db.flush()
    row.depends = check_depends(db, report_id, row.id, data.depends)
    return row


def update_doc(db: Session, report_id: int, doc_id: int, data, user_id: int) -> SurveyReportDoc:
    row = _get_or_404(db, SurveyReportDoc, report_id, doc_id)
    changes = data.model_dump(exclude_unset=True)
    _check_refs(db, report_id, changes.get("phase_id"), changes.get("item_id"))
    if "depends" in changes and changes["depends"] is not None:
        changes["depends"] = check_depends(db, report_id, doc_id, changes["depends"])
    #  Ngày tách riêng: '' nghĩa là XÓA ngày (ghi None), khác với không gửi. Vòng
    #  generic bên dưới bỏ qua mọi None nên không phân biệt được hai ca đó.
    for key in ("start_date", "expires_at", "planned_date"):
        if key in changes:
            setattr(row, key, _to_date(changes.pop(key)))
    for key, value in changes.items():
        if value is not None:
            setattr(row, key, value)
    row.updated_by = user_id
    return row


def delete_doc(db: Session, report_id: int, doc_id: int, user_id: int) -> str:
    """Xóa một hồ sơ và GỠ nó khỏi danh sách tiên quyết của các hồ sơ khác —
    để lại id chết là hồ sơ khác khóa vĩnh viễn theo một thứ không còn tồn tại."""
    row = _get_or_404(db, SurveyReportDoc, report_id, doc_id)
    others = (db.query(SurveyReportDoc)
              .filter(SurveyReportDoc.report_id == report_id,
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


def delete_docs(db: Session, report_id: int, doc_ids: list[int], user_id: int) -> list[str]:
    """Xóa NHIỀU hồ sơ một lượt — cùng luật với `delete_doc`: gỡ các id vừa xóa khỏi
    danh sách tiên quyết của hồ sơ CÒN LẠI. Tất cả hoặc không: một id không thuộc
    khối này (đã bị người khác xóa, hay id của phiếu khác) → 404, không xóa gì cả."""
    wanted = set(doc_ids)
    rows = (db.query(SurveyReportDoc)
            .filter(SurveyReportDoc.report_id == report_id,
                    SurveyReportDoc.id.in_(wanted))
            .all())
    if len(rows) != len(wanted):
        raise HTTPException(404, "Có hồ sơ không còn trong báo cáo — tải lại rồi chọn lại")
    others = (db.query(SurveyReportDoc)
              .filter(SurveyReportDoc.report_id == report_id,
                      SurveyReportDoc.id.notin_(wanted))
              .all())
    for other in others:
        deps = list(other.depends or [])
        if any(i in wanted for i in deps):
            other.depends = [i for i in deps if i not in wanted]
            other.updated_by = user_id
    titles = [row.title for row in sorted(rows, key=lambda r: r.sort_order)]
    for row in rows:
        db.delete(row)
    return titles


def create_first_doc(db: Session, report_id: int, lines: list[LineRef], data,
                     user_id: int) -> SurveyReportDoc:
    """duoc-CR-611 — «Thêm hồ sơ» khi khối còn TRỐNG: dựng khung (5 giai đoạn + nút theo
    dòng hàng, KHÔNG đổ bộ hồ sơ mẫu) rồi thêm đúng một hồ sơ vào dòng hàng + giai đoạn đã
    chọn. Khối đã có gì rồi → 400: lúc đó nút «Thêm hồ sơ» thường đã có ô chọn nút sẵn, đi
    đường này nữa là dựng khung chồng lên khung."""
    if not is_report_empty(db, report_id):
        raise HTTPException(400, "Báo cáo đã có nội dung — tải lại rồi dùng nút «Thêm hồ sơ»")
    if data.line_id and data.line_id not in {line_id for line_id, _ in lines}:
        raise HTTPException(404, "Dòng hàng không còn trên chứng từ — tải lại rồi chọn lại")
    #  Khung ở đây là 5 giai đoạn của MẪU CHUNG → ghi đúng mẫu đó lên đầu khối (đầu khối có
    #  thể còn mã của lần khởi tạo trước đã bị xóa — «Tạo mẫu» sẽ đổ nhầm mẫu).
    _set_template(db, report_id, RT_COMMON, user_id)
    _build_skeleton(db, report_id, lines, user_id)
    phase = (db.query(SurveyReportPhase)
             .filter_by(report_id=report_id, sort_order=data.phase_order).one())
    item_id = 0
    if data.line_id:
        item_id = (db.query(SurveyReportItem.id)
                   .filter_by(report_id=report_id, line_id=data.line_id).scalar())
    row = SurveyReportDoc(report_id=report_id, phase_id=phase.id, item_id=item_id,
                          title=data.title, sort_order=0,
                          created_by=user_id, updated_by=user_id)
    db.add(row)
    db.flush()
    return row
