"""Khối BÁO CÁO THỰC HIỆN trên chi tiết phiếu YCBG — `/api/survey-requests/{sid}/report`.

Hai lớp chốt, tái dùng khóa `survey_request` (khối nằm TRONG màn chi tiết YCBG,
luật «một khóa = một màn hình» — không đẻ entity mới):

- ĐỌC: `require(read)` + `_in_scope(read)` — ai mở được phiếu thì xem được báo cáo.
- GHI: `require(process)` — cờ suy ra «là NS Thu mua» (xem ghi chú ở
  `set_line_assignee_`), nên PHẠM VI vẫn phải hỏi theo `read`: hỏi
  `scope_condition("process")` thì không grant nào có và cổng đóng sạch.

Mọi mutation trả về NGUYÊN khối báo cáo mới — FE thay cache một lượt, không vá tay.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import report_service
from .controller import _in_scope
from .report_schema import ReportDocIn, ReportDocPatch, ReportItemIn, ReportPhaseIn

report_router = APIRouter(prefix="/api/survey-requests/{sid}/report", tags=["survey_request_report"])

ENTITY = "survey_request"


@report_router.get("")
def get_report_(sid: int, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "read"))):
    _in_scope(db, sid, user, "read")
    return success(report_service.get_report_payload(db, sid))


#  Phiếu ĐÃ ĐÓNG (hoàn thành) hoặc ĐÃ HỦY: báo cáo chỉ đọc, cấm mọi thao tác ghi.
_LOCKED_STATUSES = ("done", "cancelled")


def _writable_sr(db: Session, sid: int, user):
    """Phiếu cha cho một thao tác GHI của khối báo cáo — xem docstring đầu tệp.

    Chặn ghi khi phiếu đã Hoàn thành / đã Hủy: nội dung báo cáo đóng băng theo
    phiếu (yêu cầu KH). `require(process)` đã gác ai được ghi; đây gác KHI nào."""
    sr = _in_scope(db, sid, user, "read")
    if sr.status in _LOCKED_STATUSES:
        raise HTTPException(400, "Phiếu đã hoàn thành/đã hủy — không sửa được báo cáo thực hiện")
    return sr


def _done(db: Session, sr, user, message: str):
    """Ghi audit lên PHIẾU CHA (khối không có khóa riêng) rồi trả khối mới.
    `record` tự commit — mọi thay đổi service dồn về đây ghi một lượt."""
    record(db, user.id, ENTITY, sr.id, "update", message, doc_code=sr.code)
    return success(report_service.get_report_payload(db, sr.id), message)


@report_router.post("/init")
def init_report_(sid: int, db: Session = Depends(get_db),
                 user=Depends(require(ENTITY, "process"))):
    sr = _writable_sr(db, sid, user)
    if not report_service.init_report(db, sid, user.id):
        # Đã có khung rồi thì trả nguyên trạng — bấm hai lần không nhân đôi.
        return success(report_service.get_report_payload(db, sid))
    return _done(db, sr, user, "Báo cáo: khởi tạo khung mặc định")


@report_router.delete("")
def delete_report_(sid: int, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "process"))):
    """Xóa CẢ khối báo cáo — có thể HOÀN TÁC từ Lịch sử thao tác.

    Chụp ảnh khối vào sọt rác trước khi xóa, rồi gắn `audit_id` của dòng lịch sử
    vào ảnh chụp để FE hiện nút «Hoàn tác» đúng dòng đó.
    """
    sr = _writable_sr(db, sid, user)
    trash = report_service.delete_all(db, sid, user.id)
    if trash.doc_count == 0 and not trash.snapshot.get("phases") and not trash.snapshot.get("items"):
        # Khối vốn đã rỗng — không có gì để xóa.
        raise HTTPException(400, "Chưa có báo cáo thực hiện để xóa")
    log = record(db, user.id, ENTITY, sr.id, "delete",
                 f"Xóa toàn bộ báo cáo thực hiện ({trash.doc_count} hồ sơ)", doc_code=sr.code)
    trash.audit_id = log.id
    db.commit()
    return success(report_service.get_report_payload(db, sid), "Đã xóa báo cáo thực hiện")


@report_router.post("/restore")
def restore_report_(sid: int, db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "process"))):
    """Hoàn tác lần xóa gần nhất — dựng lại khối từ ảnh chụp trong sọt rác."""
    sr = _writable_sr(db, sid, user)
    trash = report_service.restore_latest(db, sid, user.id)
    if not trash:
        raise HTTPException(400, "Không có bản báo cáo nào để hoàn tác")
    record(db, user.id, ENTITY, sr.id, "update",
           f"Hoàn tác: khôi phục báo cáo thực hiện ({trash.doc_count} hồ sơ)", doc_code=sr.code)
    return success(report_service.get_report_payload(db, sid), "Đã hoàn tác xóa báo cáo thực hiện")


# ── Nút dòng hàng ───────────────────────────────────────────────────────────────
@report_router.post("/items")
def create_item_(sid: int, data: ReportItemIn, db: Session = Depends(get_db),
                 user=Depends(require(ENTITY, "process"))):
    sr = _writable_sr(db, sid, user)
    report_service.create_item(db, sid, data.name, user.id)
    return _done(db, sr, user, f"Báo cáo: thêm nút '{data.name}'")


@report_router.patch("/items/{item_id}")
def rename_item_(sid: int, item_id: int, data: ReportItemIn, db: Session = Depends(get_db),
                 user=Depends(require(ENTITY, "process"))):
    sr = _writable_sr(db, sid, user)
    report_service.rename_item(db, sid, item_id, data.name, user.id)
    return _done(db, sr, user, f"Báo cáo: đổi tên nút thành '{data.name}'")


@report_router.delete("/items/{item_id}")
def delete_item_(sid: int, item_id: int, db: Session = Depends(get_db),
                 user=Depends(require(ENTITY, "process"))):
    sr = _writable_sr(db, sid, user)
    name = report_service.delete_item(db, sid, item_id, user.id)
    return _done(db, sr, user, f"Báo cáo: xóa nút '{name}' (hồ sơ gắn nút chuyển về Chung)")


# ── Giai đoạn ───────────────────────────────────────────────────────────────────
@report_router.post("/phases")
def create_phase_(sid: int, data: ReportPhaseIn, db: Session = Depends(get_db),
                  user=Depends(require(ENTITY, "process"))):
    sr = _writable_sr(db, sid, user)
    report_service.create_phase(db, sid, data.name, data.location, user.id)
    return _done(db, sr, user, f"Báo cáo: thêm giai đoạn '{data.name}'")


@report_router.patch("/phases/{phase_id}")
def update_phase_(sid: int, phase_id: int, data: ReportPhaseIn, db: Session = Depends(get_db),
                  user=Depends(require(ENTITY, "process"))):
    sr = _writable_sr(db, sid, user)
    report_service.update_phase(db, sid, phase_id, data.name, data.location, user.id)
    return _done(db, sr, user, f"Báo cáo: sửa giai đoạn '{data.name}'")


@report_router.delete("/phases/{phase_id}")
def delete_phase_(sid: int, phase_id: int, db: Session = Depends(get_db),
                  user=Depends(require(ENTITY, "process"))):
    sr = _writable_sr(db, sid, user)
    name = report_service.delete_phase(db, sid, phase_id)
    return _done(db, sr, user, f"Báo cáo: xóa giai đoạn '{name}'")


# ── Hồ sơ ───────────────────────────────────────────────────────────────────────
@report_router.post("/docs")
def create_doc_(sid: int, data: ReportDocIn, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "process"))):
    sr = _writable_sr(db, sid, user)
    report_service.create_doc(db, sid, data, user.id)
    return _done(db, sr, user, f"Báo cáo: thêm hồ sơ '{data.title}'")


@report_router.patch("/docs/{doc_id}")
def update_doc_(sid: int, doc_id: int, data: ReportDocPatch, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "process"))):
    sr = _writable_sr(db, sid, user)
    doc = report_service.update_doc(db, sid, doc_id, data, user.id)
    return _done(db, sr, user, f"Báo cáo: cập nhật hồ sơ '{doc.title}'")


@report_router.delete("/docs/{doc_id}")
def delete_doc_(sid: int, doc_id: int, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "process"))):
    sr = _writable_sr(db, sid, user)
    title = report_service.delete_doc(db, sid, doc_id, user.id)
    return _done(db, sr, user, f"Báo cáo: xóa hồ sơ '{title}'")
