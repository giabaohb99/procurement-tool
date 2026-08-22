from decimal import Decimal

from collections import Counter

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, apply_sort_from_request, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope
from app.modules.notification.service import trigger_notification

from . import service
from .model import Survey, SurveyProductLine
from .schema import LineApproveCombined, RejectIn, SurveyCreate, SurveyUpdate


def _dict(obj) -> dict:
    d = {}
    for c in sa_inspect(obj).mapper.column_attrs:
        v = getattr(obj, c.key)
        d[c.key] = float(v) if isinstance(v, Decimal) else v
    return d


def _price_hint(db: Session, s: Survey) -> dict:
    """Giá mua GẦN NHẤT và CAO NHẤT của mã VTBB ở đầu phiếu (CR-111).

    Lấy từ Lịch sử mua hàng để FE điền sẵn hai ô "Giá mua gần nhất" / "Giá mua max" của dòng
    khảo sát — khỏi bắt NSPT mở màn khác tra tay rồi gõ lại. Người dùng vẫn SỬA ĐÈ được nên
    đây chỉ là gợi ý; con số chốt vẫn nằm ở cột của dòng khảo sát.

    Phiếu khảo sát hàng chưa có mã trong hệ thống thì `item_code` rỗng → trả 0, FE bỏ qua.
    `unit` trả kèm để FE cảnh báo khi ĐVT lịch sử khác ĐVT báo giá (giá không so thẳng được).
    """
    from sqlalchemy import func

    from app.modules.purchase_history.model import PurchaseHistory

    empty = {"last": 0.0, "max": 0.0, "count": 0, "unit": "", "date": ""}
    code = (s.item_code or "").strip()
    if not code:
        return empty
    q = db.query(PurchaseHistory).filter(PurchaseHistory.product_code == code,
                                         PurchaseHistory.price > 0)
    # order_date là chuỗi 'YYYY-MM-DD' nên sắp xếp chữ cũng ra đúng thứ tự thời gian.
    last = q.order_by(PurchaseHistory.order_date.desc(), PurchaseHistory.id.desc()).first()
    if last is None:
        return empty
    mx = (db.query(func.max(PurchaseHistory.price))
          .filter(PurchaseHistory.product_code == code).scalar())
    return {"last": float(last.price or 0), "max": float(mx or 0), "count": q.count(),
            "unit": last.unit or "", "date": last.order_date or ""}


def _out(db: Session, s: Survey) -> dict:
    """Phiếu khảo sát GỘP: trả cả 2 bảng dòng (NCC + SP)."""
    base = _dict(s)
    base["price_hint"] = _price_hint(db, s)
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


def search_condition(keyword: str):
    """Điều kiện của ô tìm kiếm đa trường: 6 cột trên phiếu HOẶC mã/tên hàng ở bảng dòng SP.

    Vế bảng dòng dùng SUBQUERY, KHÔNG gom id ra Python rồi `.in_(list)`: bảng dòng SP trên
    thật đã hơn 5000 dòng, gõ một từ phổ biến là SQLAlchemy nhồi hàng nghìn tham số thẳng vào
    câu SQL (mẫu C1 trong doc/tai-lieu-ky-thuat/ra-soat-api-hieu-nang.md — đúng lỗi đã vá ở
    `service.report_rows`).
    """
    from sqlalchemy import or_, select

    like = f"%{keyword}%"
    # `survey_id > 0` giữ đúng chốt chặn `if r[0]` của bản cũ: dòng nhập từ Excel có thể để
    # survey_id = 0 (chưa gắn phiếu nào), không được kéo theo gì cả.
    line_sub = select(SurveyProductLine.survey_id).where(
        SurveyProductLine.survey_id > 0,
        or_(SurveyProductLine.internal_code.like(like),
            SurveyProductLine.product_name.like(like)),
    )
    return or_(
        Survey.code.like(like),
        Survey.pr_code.like(like),
        Survey.sr_code.like(like),
        Survey.item_code.like(like),
        Survey.item_name.like(like),
        Survey.main_content.like(like),
        Survey.id.in_(line_sub),
    )


@router.get("")
def list_surveys(request: Request, pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("survey", "read"))):
    # `code` chỉ bị loại khỏi lọc TRẦN (nhường cho ô tìm kiếm đa trường ngay dưới), bộ lọc điều
    # kiện `code__contains=...` vẫn phải chạy -> truyền FILTERABLE đầy đủ cho vế operator.
    filterable = [f for f in service.FILTERABLE if f != "code"]
    q = apply_filters(db.query(Survey), Survey, request, filterable,
                      operator_filterable=service.FILTERABLE)
    search = (request.query_params.get("code") or request.query_params.get("q") or request.query_params.get("search") or request.query_params.get("product_code") or "").strip()
    if search:
        q = q.filter(search_condition(search))
    q = apply_scope(q, Survey, "survey", user, get_perm_profile(db, user))
    q = apply_sort_from_request(q, Survey, request)
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


@router.post("/{sid}/clone")
def clone_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey", "create"))):
    """Nhân bản phiếu khảo sát thành phiếu nháp mới."""
    return success(_out(db, service.copy_survey(db, sid, user.id)), "Đã nhân bản thành phiếu Nháp mới", 201)


@router.delete("/{sid}")
def delete_(sid: int, db: Session = Depends(get_db), user=Depends(require("survey", "delete"))):
    s = service.get_survey(db, sid)
    if s.status not in ("draft", "cancelled", "rejected"):
        raise HTTPException(400, "Chỉ được xóa phiếu khảo sát ở trạng thái Nháp / Bị trả lại / Đã hủy")
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
            if s.status not in ("draft", "cancelled", "rejected"):
                raise HTTPException(400, f"Phiếu {s.code} không ở trạng thái Nháp / Bị trả lại / Đã hủy")
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
    # "Trả lại" = đưa phiếu về trạng thái BỊ TRẢ LẠI (rejected) để NSPT sửa & gửi duyệt lại
    # (đồng bộ với Yêu cầu khảo sát: rejected = sửa lại được, khác với cancelled = khóa hẳn).
    s = service.set_status(db, sid, "rejected", user.id, data.reason)
    trigger_notification(db=db, event="survey_rejected", doc_type="survey", doc_code=s.code,
                         creator_id=s.created_by or user.id, background_tasks=background_tasks,
                         reason=data.reason or "", link=f"/surveys/{s.id}")
    return success(_out(db, s), "Đã trả lại phiếu")


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
                  code: str | None = Query(None), q: str | None = Query(None), nspt: str | None = Query(None),
                  item_code: str | None = Query(None), main_content: str | None = Query(None),
                  date_from: str | None = Query(None), date_to: str | None = Query(None),
                  sort_by: str = Query(""), sort_dir: str = Query("asc"),
                  pg: dict = Depends(pagination), db: Session = Depends(get_db),
                  user=Depends(require("survey", "read"))):
    base = apply_scope(db.query(Survey), Survey, "survey", user, get_perm_profile(db, user))
    rows = service.report_rows(db, base)

    search_kw = (q or code or "").strip().lower()

    def keep(r):
        if kind and r["kind"] != kind:
            return False
        if item_group and r["item_group"] != item_group:
            return False
        if supplier and supplier.lower() not in (r["supplier_code"] or "").lower():
            return False
        if search_kw:
            match = (
                search_kw in (r.get("survey_code") or "").lower()
                or search_kw in (r.get("content") or "").lower()
                or search_kw in (r.get("supplier_code") or "").lower()
                or search_kw in (r.get("item_code") or "").lower()
                or search_kw in (r.get("item_group") or "").lower()
                or search_kw in (r.get("main_content") or "").lower()
                or search_kw in (r.get("nspt") or "").lower()
                or search_kw in (r.get("sr_code") or "").lower()
                or search_kw in (r.get("pr_code") or "").lower()
            )
            if not match:
                return False
        if nspt and nspt.lower() not in (r["nspt"] or "").lower():
            return False
        if item_code and item_code.lower() not in (r["item_code"] or "").lower():
            return False
        if main_content and main_content.lower() not in (r["main_content"] or "").lower():
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
    rows.sort(key=lambda r: (-r["survey_id"], r["kind"], r["line_id"]))   # thứ tự mặc định
    # Sort theo cột người dùng chọn (sort ổn định -> thứ tự mặc định làm tiebreak)
    _allow = {"survey_code", "kind", "content", "supplier_code", "item_group",
              "nspt", "item_code", "main_content", "date", "line_approve", "line_approve_note"}
    if sort_by in _allow:
        rows.sort(key=lambda r: (r.get(sort_by) or ""), reverse=str(sort_dir).lower() == "desc")
    total = len(rows)
    items = rows[pg["offset"]: pg["offset"] + pg["limit"]]
    return success({"total": total, "items": items, "summary": summary})


@report_router.get("/by-supplier")
def by_supplier_(tax_code: str = Query(""), supplier_code: str = Query(""),
                 db: Session = Depends(get_db), user=Depends(require("survey", "read"))):
    """Task 9: khảo sát của 1 NCC — KSNCC (theo tax_code) + KSSP (theo supplier_code)."""
    sup, prod = service.lines_by_supplier(db, tax_code, supplier_code)
    return success({"supplier_lines": sup, "product_lines": prod})
