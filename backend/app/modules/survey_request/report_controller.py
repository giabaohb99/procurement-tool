"""Khối BÁO CÁO THỰC HIỆN — `/api/execution-report/{entity}/{owner_id}` (bao-CR-598).

Một bộ đường API cho MỌI chứng từ chủ; `entity` chọn luật ở `_OWNER_RULES`:

- `survey_request` (YCBG, bao-CR-388): ĐỌC = `survey_request.read` + `_in_scope(read)`;
  GHI = `survey_request.process` — cờ suy ra «là NS Thu mua» (xem ghi chú ở
  `set_line_assignee_`), nên PHẠM VI vẫn hỏi theo `read`. Nút dòng hàng đặt tay.
- `purchase_order` (ĐMH, bao-CR-598): ĐỌC = `purchase_order.read` + `_in_scope(read)`;
  GHI = `purchase_order.write` + `_in_scope(write)` — ai sửa được đơn thì sửa được
  báo cáo. Nút dòng hàng SINH TỰ ĐỘNG theo dòng đơn (đồng bộ mỗi lần đọc), không
  thêm/đổi tên/xóa tay.

Hai lớp chốt đều tái dùng khóa của chứng từ cha (khối nằm TRONG màn chi tiết, luật
«một khóa = một màn hình» — không đẻ entity mới). Mọi mutation trả về NGUYÊN khối
báo cáo mới — FE thay cache một lượt, không vá tay.
"""
from dataclasses import dataclass
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_current_user, user_has_permission
from app.core.database import get_db
from app.core.response import success
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.controller import _in_scope as po_in_scope

from . import report_service
from .controller import _in_scope as sr_in_scope
from .report_model import (REPORT_OWNER_PURCHASE_ORDER, REPORT_OWNER_SURVEY_REQUEST,
                           SurveyReportItem, SurveyReportPhase)
from .report_schema import (ReportDocIn, ReportDocPatch, ReportItemIn, ReportPhaseIn,
                            ReportTemplateApplyIn)

report_router = APIRouter(prefix="/api/execution-report/{entity}/{owner_id}",
                          tags=["execution_report"])


@dataclass(frozen=True)
class OwnerRule:
    """Luật của một loại chứng từ chủ — xem docstring đầu tệp."""

    entity: str
    read_action: str
    write_action: str
    #  Phạm vi hỏi khi GHI: YCBG hỏi theo `read` (cờ `process` không có grant phạm vi).
    write_scope_action: str
    #  Nạp chứng từ cha trong phạm vi `action` → 404 ngoài phạm vi.
    load: Callable[[Session, int, object, str], object]
    #  Trạng thái chứng từ mà báo cáo đóng băng (chỉ đọc).
    locked_statuses: tuple[str, ...]
    #  Dòng hàng của chứng từ → (id dòng, tên nút).
    lines: Callable[[Session, object], list[report_service.LineRef]]
    #  Nút dòng hàng sinh tự động theo dòng chứng từ (ĐMH) — cấm sửa tay.
    items_locked: bool
    #  Chữ gọi chứng từ trong câu lỗi / lịch sử.
    label: str


def _po_lines(db: Session, po) -> list[report_service.LineRef]:
    out: list[report_service.LineRef] = []
    for index, item in enumerate(po_service.items_of(db, po.id)):
        name = (item.product_name or item.product_code or "").strip()[:100] or f"Dòng {index + 1}"
        out.append((item.id, name))
    return out


_OWNER_RULES: dict[str, OwnerRule] = {
    REPORT_OWNER_SURVEY_REQUEST: OwnerRule(
        entity=REPORT_OWNER_SURVEY_REQUEST, read_action="read", write_action="process",
        write_scope_action="read", load=sr_in_scope, locked_statuses=("done", "cancelled"),
        lines=lambda db, sr: report_service.survey_request_lines(db, sr.id),
        items_locked=False, label="Phiếu"),
    REPORT_OWNER_PURCHASE_ORDER: OwnerRule(
        entity=REPORT_OWNER_PURCHASE_ORDER, read_action="read", write_action="write",
        write_scope_action="write", load=po_in_scope, locked_statuses=("completed", "cancelled"),
        lines=_po_lines, items_locked=True, label="Đơn"),
}


def _rule_of(entity: str) -> OwnerRule:
    rule = _OWNER_RULES.get(entity)
    if rule is None:
        raise HTTPException(404, "Loại chứng từ không có khối báo cáo thực hiện")
    return rule


def _require_owner(kind: str):
    """Dependency thay `require(entity, action)`: entity nằm trên URL nên tra luật lúc gọi."""

    def dep(entity: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
        rule = _rule_of(entity)
        action = rule.read_action if kind == "read" else rule.write_action
        if not user_has_permission(db, user, rule.entity, action):
            raise HTTPException(403, f"Không có quyền: {action} {rule.entity}")
        return user

    return dep


def _readable(db: Session, entity: str, owner_id: int, user):
    """Chứng từ cha trong phạm vi ĐỌC + id khối (0 = chưa có). ĐMH đồng bộ nút theo dòng đơn."""
    rule = _rule_of(entity)
    parent = rule.load(db, owner_id, user, rule.read_action)
    report_id = report_service.report_id_of(db, entity, owner_id)
    if report_id and rule.items_locked:
        #  Đồng bộ là việc của hệ thống, không phải người đọc: ghi nhận bằng
        #  `updated_by` của người đang xem nhưng không lên lịch sử thao tác.
        if report_service.sync_line_items(db, report_id, rule.lines(db, parent), user.id):
            db.commit()
    return parent, report_id


def _writable(db: Session, entity: str, owner_id: int, user):
    """Chứng từ cha cho một thao tác GHI + ĐẦU báo cáo (tạo nếu chưa có).

    Chặn ghi khi chứng từ đã Hoàn thành / đã Hủy: nội dung báo cáo đóng băng theo
    chứng từ (yêu cầu KH). `_require_owner("write")` đã gác AI được ghi; đây gác KHI nào.
    """
    rule = _rule_of(entity)
    parent = rule.load(db, owner_id, user, rule.write_scope_action)
    if parent.status in rule.locked_statuses:
        raise HTTPException(400, f"{rule.label} đã hoàn thành/đã hủy — không sửa được báo cáo thực hiện")
    head = report_service.ensure_report(db, entity, owner_id, user.id)
    return parent, head.id


def _done(db: Session, entity: str, parent, report_id: int, user, message: str):
    """Ghi audit lên CHỨNG TỪ CHA (khối không có khóa riêng) rồi trả khối mới.
    `record` tự commit — mọi thay đổi service dồn về đây ghi một lượt."""
    record(db, user.id, entity, parent.id, "update", message, doc_code=parent.code)
    return success(report_service.get_report_payload(db, report_id), message)


def _items_editable(entity: str) -> None:
    if _rule_of(entity).items_locked:
        raise HTTPException(400, "Nút dòng hàng của đơn mua hàng sinh tự động theo dòng đơn — "
                                 "thêm/sửa dòng ngay trên đơn")


@report_router.get("")
def get_report_(entity: str, owner_id: int, db: Session = Depends(get_db),
                user=Depends(_require_owner("read"))):
    _, report_id = _readable(db, entity, owner_id, user)
    return success(report_service.get_report_payload(db, report_id))


@report_router.post("/init")
def init_report_(entity: str, owner_id: int, db: Session = Depends(get_db),
                 user=Depends(_require_owner("write"))):
    parent, report_id = _writable(db, entity, owner_id, user)
    lines = _rule_of(entity).lines(db, parent)
    added = report_service.init_report(db, report_id, lines, user.id)
    if added < 0:
        # Đã có khung rồi thì trả nguyên trạng — bấm hai lần không nhân đôi.
        db.commit()
        return success(report_service.get_report_payload(db, report_id))
    return _done(db, entity, parent, report_id, user,
                 f"Báo cáo: khởi tạo theo mẫu chung ({added} hồ sơ)")


@report_router.post("/apply-template")
def apply_template_(entity: str, owner_id: int, data: ReportTemplateApplyIn,
                    db: Session = Depends(get_db), user=Depends(_require_owner("write"))):
    """Nút «Tạo mẫu» trên một nút dòng hàng / một giai đoạn — đổ mẫu chung vào,
    cộng thêm, bỏ qua hồ sơ đã có."""
    parent, report_id = _writable(db, entity, owner_id, user)
    added = report_service.apply_template(db, report_id, data.item_id, data.phase_id, user.id)
    target = "hồ sơ chung"
    if data.item_id:
        target = f"nút '{db.get(SurveyReportItem, data.item_id).name}'"
    if data.phase_id is not None:
        target += f", giai đoạn '{db.get(SurveyReportPhase, data.phase_id).name}'"
    if added == 0:
        # Mẫu đã có đủ ở đó — không ghi lịch sử cho một thao tác không đổi gì.
        db.commit()
        return success(report_service.get_report_payload(db, report_id),
                       f"Mẫu chung đã có đủ ở {target}")
    return _done(db, entity, parent, report_id, user,
                 f"Báo cáo: tạo mẫu vào {target} (+{added} hồ sơ)")


@report_router.delete("")
def delete_report_(entity: str, owner_id: int, db: Session = Depends(get_db),
                   user=Depends(_require_owner("write"))):
    """Xóa CẢ khối báo cáo — có thể HOÀN TÁC từ Lịch sử thao tác.

    Chụp ảnh khối vào sọt rác trước khi xóa, rồi gắn `audit_id` của dòng lịch sử
    vào ảnh chụp để FE hiện nút «Hoàn tác» đúng dòng đó.
    """
    parent, report_id = _writable(db, entity, owner_id, user)
    trash = report_service.delete_all(db, report_id, user.id)
    if trash.doc_count == 0 and not trash.snapshot.get("phases") and not trash.snapshot.get("items"):
        # Khối vốn đã rỗng — không có gì để xóa.
        raise HTTPException(400, "Chưa có báo cáo thực hiện để xóa")
    log = record(db, user.id, entity, parent.id, "delete",
                 f"Xóa toàn bộ báo cáo thực hiện ({trash.doc_count} hồ sơ)", doc_code=parent.code)
    trash.audit_id = log.id
    db.commit()
    return success(report_service.get_report_payload(db, report_id), "Đã xóa báo cáo thực hiện")


@report_router.post("/restore")
def restore_report_(entity: str, owner_id: int, db: Session = Depends(get_db),
                    user=Depends(_require_owner("write"))):
    """Hoàn tác lần xóa gần nhất — dựng lại khối từ ảnh chụp trong sọt rác."""
    parent, report_id = _writable(db, entity, owner_id, user)
    trash = report_service.restore_latest(db, report_id, user.id)
    if not trash:
        raise HTTPException(400, "Không có bản báo cáo nào để hoàn tác")
    record(db, user.id, entity, parent.id, "update",
           f"Hoàn tác: khôi phục báo cáo thực hiện ({trash.doc_count} hồ sơ)", doc_code=parent.code)
    return success(report_service.get_report_payload(db, report_id),
                   "Đã hoàn tác xóa báo cáo thực hiện")


# ── Nút dòng hàng ───────────────────────────────────────────────────────────────
@report_router.post("/items")
def create_item_(entity: str, owner_id: int, data: ReportItemIn, db: Session = Depends(get_db),
                 user=Depends(_require_owner("write"))):
    _items_editable(entity)
    parent, report_id = _writable(db, entity, owner_id, user)
    report_service.create_item(db, report_id, data.name, user.id)
    return _done(db, entity, parent, report_id, user, f"Báo cáo: thêm nút '{data.name}'")


@report_router.patch("/items/{item_id}")
def rename_item_(entity: str, owner_id: int, item_id: int, data: ReportItemIn,
                 db: Session = Depends(get_db), user=Depends(_require_owner("write"))):
    _items_editable(entity)
    parent, report_id = _writable(db, entity, owner_id, user)
    report_service.rename_item(db, report_id, item_id, data.name, user.id)
    return _done(db, entity, parent, report_id, user, f"Báo cáo: đổi tên nút thành '{data.name}'")


@report_router.delete("/items/{item_id}")
def delete_item_(entity: str, owner_id: int, item_id: int, db: Session = Depends(get_db),
                 user=Depends(_require_owner("write"))):
    _items_editable(entity)
    parent, report_id = _writable(db, entity, owner_id, user)
    name = report_service.delete_item(db, report_id, item_id, user.id)
    return _done(db, entity, parent, report_id, user,
                 f"Báo cáo: xóa nút '{name}' (hồ sơ gắn nút chuyển về Chung)")


# ── Giai đoạn ───────────────────────────────────────────────────────────────────
@report_router.post("/phases")
def create_phase_(entity: str, owner_id: int, data: ReportPhaseIn, db: Session = Depends(get_db),
                  user=Depends(_require_owner("write"))):
    parent, report_id = _writable(db, entity, owner_id, user)
    report_service.create_phase(db, report_id, data.name, data.location, user.id)
    return _done(db, entity, parent, report_id, user, f"Báo cáo: thêm giai đoạn '{data.name}'")


@report_router.patch("/phases/{phase_id}")
def update_phase_(entity: str, owner_id: int, phase_id: int, data: ReportPhaseIn,
                  db: Session = Depends(get_db), user=Depends(_require_owner("write"))):
    parent, report_id = _writable(db, entity, owner_id, user)
    report_service.update_phase(db, report_id, phase_id, data.name, data.location, user.id)
    return _done(db, entity, parent, report_id, user, f"Báo cáo: sửa giai đoạn '{data.name}'")


@report_router.delete("/phases/{phase_id}")
def delete_phase_(entity: str, owner_id: int, phase_id: int, db: Session = Depends(get_db),
                  user=Depends(_require_owner("write"))):
    parent, report_id = _writable(db, entity, owner_id, user)
    name = report_service.delete_phase(db, report_id, phase_id)
    return _done(db, entity, parent, report_id, user, f"Báo cáo: xóa giai đoạn '{name}'")


# ── Hồ sơ ───────────────────────────────────────────────────────────────────────
@report_router.post("/docs")
def create_doc_(entity: str, owner_id: int, data: ReportDocIn, db: Session = Depends(get_db),
                user=Depends(_require_owner("write"))):
    parent, report_id = _writable(db, entity, owner_id, user)
    report_service.create_doc(db, report_id, data, user.id)
    return _done(db, entity, parent, report_id, user, f"Báo cáo: thêm hồ sơ '{data.title}'")


@report_router.patch("/docs/{doc_id}")
def update_doc_(entity: str, owner_id: int, doc_id: int, data: ReportDocPatch,
                db: Session = Depends(get_db), user=Depends(_require_owner("write"))):
    parent, report_id = _writable(db, entity, owner_id, user)
    doc = report_service.update_doc(db, report_id, doc_id, data, user.id)
    return _done(db, entity, parent, report_id, user, f"Báo cáo: cập nhật hồ sơ '{doc.title}'")


@report_router.delete("/docs/{doc_id}")
def delete_doc_(entity: str, owner_id: int, doc_id: int, db: Session = Depends(get_db),
                user=Depends(_require_owner("write"))):
    parent, report_id = _writable(db, entity, owner_id, user)
    title = report_service.delete_doc(db, report_id, doc_id, user.id)
    return _done(db, entity, parent, report_id, user, f"Báo cáo: xóa hồ sơ '{title}'")
