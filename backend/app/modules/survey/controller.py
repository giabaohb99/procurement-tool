from decimal import Decimal

from collections import Counter

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.notification.service import trigger_notification

from . import service
from .model import Survey
from .schema import LineApproveCombined, RejectIn, SurveyCreate, SurveyUpdate


def _dict(obj) -> dict:
    d = {}
    for c in sa_inspect(obj).mapper.column_attrs:
        v = getattr(obj, c.key)
        d[c.key] = float(v) if isinstance(v, Decimal) else v
    return d


def _out(db: Session, s: Survey) -> dict:
    """Phiếu khảo sát GỘP: trả cả 2 bảng dòng (NCC + SP)."""
    base = _dict(s)
    sup = service.supplier_lines_of(db, s.id)
    prod = service.product_lines_of(db, s.id)
    base["supplier_lines"] = [_dict(x) for x in sup]
    base["product_lines"] = [_dict(x) for x in prod]
    base["supplier_count"] = len(sup)
    base["product_count"] = len(prod)
    base["subtotal"] = round(sum(float(x.amount or 0) for x in prod), 2)
    base["main"] = ((sup[0].supplier_name or sup[0].supplier_code) if sup
                    else (prod[0].product_name if prod else ""))
    return base


router = APIRouter(prefix="/api/surveys", tags=["survey"])


@router.get("")
def list_(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("survey", "read"))):
    q = apply_filters(db.query(Survey), Survey, request, service.FILTERABLE)
    q = apply_scope(q, Survey, "survey", user, get_perm_profile(db, user))
    total, items = service.list_surveys(db, q, pg)
    return success({"total": total, "items": [_dict(x) for x in items]})


@router.get("/{sid}")
def get_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey", "read"))):
    s = apply_scope(db.query(Survey).filter(Survey.id == sid),
                    Survey, "survey", user, get_perm_profile(db, user)).first()
    if not s:
        raise HTTPException(403, "Ngoài phạm vi được phép xem")
    return success(_out(db, s))


@router.post("")
def create_(data: SurveyCreate, db: Session = Depends(get_db), user=Depends(require("survey", "create"))):
    return success(_out(db, service.create_survey(db, data, user.id)), "Đã tạo", 201)


@router.patch("/{sid}")
def update_(sid: int, data: SurveyUpdate, db: Session = Depends(get_db), user=Depends(require("survey", "write"))):
    return success(_out(db, service.update_survey(db, sid, data, user.id)), "Đã cập nhật")


@router.delete("/{sid}")
def delete_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey", "delete"))):
    s = service.get_survey(db, sid)
    if s.status not in ("draft", "cancelled"):
        raise HTTPException(400, "Chỉ được xóa phiếu khảo sát ở trạng thái Nháp hoặc Đã hủy")
    service.delete_survey(db, sid, user.id)
    return success(None, "Đã xóa")


@router.delete("")
def bulk_delete_surveys(ids: str, db: Session = Depends(get_db), user=Depends(require("survey", "delete"))):
    id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "Không có ID hợp lệ")
    for sid in id_list:
        try:
            s = service.get_survey(db, sid)
            if s.status not in ("draft", "cancelled"):
                raise HTTPException(400, f"Phiếu {s.code} không ở trạng thái Nháp hoặc Đã hủy")
            service.delete_survey(db, sid, user.id)
        except Exception as e:
            raise HTTPException(400, f"Lỗi khi xóa khảo sát ID {sid}: {str(e)}")
    return success(None, f"Đã xóa {len(id_list)} bản ghi")


@router.post("/{sid}/submit")
def submit_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("survey", "write"))):
    s = service.set_status(db, sid, "submitted", user.id)
    trigger_notification(db=db, event="survey_submitted", doc_type="survey", doc_code=s.code,
                         creator_id=s.created_by or user.id, background_tasks=background_tasks,
                         link=f"/surveys/{s.id}")
    return success(_out(db, s), "Đã gửi duyệt")


def _sync_ycks_options(db: Session, s, user_id: int) -> None:
    """Phiếu khảo sát có liên kết Yêu cầu khảo sát -> tự gắn option cho dòng YCKS khớp phân loại
    ngay khi DÒNG được duyệt (không cần duyệt cả phiếu)."""
    if getattr(s, "survey_request_id", 0):
        try:
            from app.modules.survey_request import service as sr_service
            sr_service.sync_options_from_surveys(db, s.survey_request_id, user_id)
        except Exception:
            pass


@router.patch("/{sid}/line-approve")
def line_approve_(sid: int, data: LineApproveCombined, db: Session = Depends(get_db),
                  user=Depends(require("survey", "approve"))):
    s = service.approve_lines(db, sid, data, user.id)
    _sync_ycks_options(db, s, user.id)
    return success(_out(db, s), "Đã lưu duyệt dòng")


@router.post("/{sid}/approve")
def approve_(sid: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
             user=Depends(require("survey", "approve"))):
    s = service.set_status(db, sid, "approved", user.id)
    _sync_ycks_options(db, s, user.id)
    trigger_notification(db=db, event="survey_approved", doc_type="survey", doc_code=s.code,
                         creator_id=s.created_by or user.id, background_tasks=background_tasks,
                         approve_note=s.approve_note or "", link=f"/surveys/{s.id}")
    return success(_out(db, s), "Đã duyệt")


@router.post("/{sid}/reject")
def reject_(sid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("survey", "approve"))):
    # "Trả lại" = đưa phiếu về NHÁP để NSPT sửa & gửi duyệt lại (bị trả lại xem như nháp)
    s = service.set_status(db, sid, "draft", user.id, data.reason)
    trigger_notification(db=db, event="survey_rejected", doc_type="survey", doc_code=s.code,
                         creator_id=s.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/surveys/{s.id}")
    return success(_out(db, s), "Đã trả lại (về nháp)")


@router.post("/{sid}/cancel")
def cancel_(sid: int, data: RejectIn, background_tasks: BackgroundTasks, db: Session = Depends(get_db),
            user=Depends(require("survey", "approve"))):
    """Từ chối phiếu đang chờ duyệt (khóa hẳn) — người duyệt thao tác."""
    s = service.get_survey(db, sid)
    if s.status != "submitted":
        raise HTTPException(400, "Chỉ từ chối được phiếu đang chờ duyệt")
    s = service.set_status(db, sid, "cancelled", user.id, data.reason)
    trigger_notification(db=db, event="survey_rejected", doc_type="survey", doc_code=s.code,
                         creator_id=s.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/surveys/{s.id}")
    return success(_out(db, s), "Đã từ chối")


@router.patch("/{sid}/lines/{table}/{line_id}/fill")
def fill_line_(sid: int, table: str, line_id: int, data: dict, db: Session = Depends(get_db),
               user=Depends(require("survey", "write"))):
    """Bổ sung 1 dòng đang 'Thiếu thông tin' (kể cả phiếu đã duyệt) — có guard trong service."""
    return success(_out(db, service.fill_missing_line(db, sid, table, line_id, data, user.id)), "Đã bổ sung dòng")


# ===== Báo cáo khảo sát theo DÒNG (gộp NCC + SP) =====
report_router = APIRouter(prefix="/api/survey-report", tags=["survey_report"])


@report_router.get("/lines")
def report_lines_(kind: str | None = Query(None), line_approve: str | None = Query(None),
                  item_group: str | None = Query(None), supplier: str | None = Query(None),
                  code: str | None = Query(None), nspt: str | None = Query(None),
                  date_from: str | None = Query(None), date_to: str | None = Query(None),
                  pg: dict = Depends(pagination), db: Session = Depends(get_db),
                  user=Depends(require("survey", "read"))):
    base = apply_scope(db.query(Survey), Survey, "survey", user, get_perm_profile(db, user))
    rows = service.report_rows(db, base)

    def keep(r):
        if kind and r["kind"] != kind:
            return False
        if item_group and r["item_group"] != item_group:
            return False
        if supplier and supplier.lower() not in (r["supplier_code"] or "").lower():
            return False
        if code and code.lower() not in (r["survey_code"] or "").lower():
            return False
        if nspt and nspt.lower() not in (r["nspt"] or "").lower():
            return False
        if date_from and (r["date"] or "") < date_from:
            return False
        if date_to and (r["date"] or "") > date_to:
            return False
        return True

    rows = [r for r in rows if keep(r)]
    cnt = Counter(r["line_approve"] for r in rows)   # tổng theo trạng thái (trước lọc trạng thái)
    summary = {k: cnt.get(k, 0) for k in ("Chờ duyệt", "Đã duyệt", "Không duyệt", "Thiếu thông tin")}
    if line_approve:
        rows = [r for r in rows if r["line_approve"] == line_approve]
    rows.sort(key=lambda r: (-r["survey_id"], r["kind"], r["line_id"]))
    total = len(rows)
    items = rows[pg["offset"]: pg["offset"] + pg["limit"]]
    return success({"total": total, "items": items, "summary": summary})


@report_router.get("/by-supplier")
def by_supplier_(tax_code: str = Query(""), supplier_code: str = Query(""),
                 db: Session = Depends(get_db), user=Depends(require("survey", "read"))):
    """Task 9: khảo sát của 1 NCC — KSNCC (theo tax_code) + KSSP (theo supplier_code)."""
    sup, prod = service.lines_by_supplier(db, tax_code, supplier_code)
    return success({"supplier_lines": sup, "product_lines": prod})
