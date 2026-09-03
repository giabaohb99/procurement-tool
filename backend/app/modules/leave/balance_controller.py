"""API QUỸ PHÉP — `/api/leave-balances`.

Màn của phòng Nhân sự: xem quỹ của mọi người, cấp phát cho một năm, chỉnh tay.

⚠️ Khóa `leave_balance` là khóa **nhạy cảm nhất** của phân hệ: ai có `write` ở
đây thì tặng thêm ngày phép cho bất kỳ ai được, qua cột «điều chỉnh tay». Đó
chính là lý do nó tách khỏi `leave_request` chứ không đi chung một khóa.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_perm_profile, require
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped
from app.modules.employee.model import Employee

from . import balance_service
from .balance_model import LeaveBalance
from .catalog_model import LeaveType
from .schema import (LeaveBalanceAdjust, LeaveBalanceAllocate,
                     LeaveBalanceResponse)

router = APIRouter(prefix="/api/leave-balances", tags=["leave"])

ENTITY = "leave_balance"

FILTERABLE = ["employee_id", "year", "leave_type_id", "company_id"]


def _dump(obj: LeaveBalance, names: dict[int, str], types: dict[int, str]) -> dict:
    data = LeaveBalanceResponse.model_validate(obj).model_dump()
    #  Hai số dẫn xuất — `model_validate` không lấy được `@property` nên gán tay.
    data["total_days"] = obj.total_days
    data["remaining_days"] = obj.remaining_days
    data["employee_name"] = names.get(obj.employee_id, "")
    data["leave_type_name"] = types.get(obj.leave_type_id, "")
    return data


def _names(db: Session, ids: set[int]) -> dict[int, str]:
    ids = {i for i in ids if i}
    if not ids:
        return {}
    return {r[0]: r[1] for r in
            db.query(Employee.id, Employee.full_name).filter(Employee.id.in_(ids)).all()}


def _type_names(db: Session) -> dict[int, str]:
    return {r[0]: r[1] for r in db.query(LeaveType.id, LeaveType.name).all()}


def apply_employee_search(db: Session, query, keyword: str | None):
    """Lọc theo TÊN hoặc MÃ nhân sự.

    `apply_filters` chỉ lọc được cột của chính bảng quỹ, mà bảng đó chỉ giữ
    `employee_id` — người dùng thì tìm bằng tên. Không có đường này thì màn Quỹ
    phép chỉ còn cách cuộn tay: một công ty vài trăm người là vài chục trang.

    Dịch tên → danh sách id rồi lọc bằng `IN`, chứ không `JOIN`: `apply_scope`
    phía sau còn gắn thêm điều kiện lên chính bảng quỹ, và một câu có JOIN thì
    dễ nhân đôi dòng khi ai đó thêm quan hệ mới.
    """
    keyword = (keyword or "").strip()
    if not keyword:
        return query

    #  ⚠️ So khớp bằng PYTHON, không đẩy `ilike` xuống cơ sở dữ liệu. Lý do là
    #  tiếng Việt có dấu: `LOWER()` của SQLite chỉ hạ được chữ ASCII, nên
    #  `ilike` khớp "TRUONG" mà trượt "TRƯỞNG" — chạy đúng trên MySQL (collation
    #  `utf8mb4_..._ci`) rồi hỏng lặng lẽ ở chỗ khác. Một luật tìm kiếm không
    #  được phụ thuộc vào collation của máy chủ.
    #
    #  Quét ba cột của bảng nhân sự trong bộ nhớ là chấp nhận được: bảng này cỡ
    #  vài trăm dòng và đây là một truy vấn nhẹ, không phải vòng lặp truy vấn.
    needle = keyword.lower()
    ids = [
        row.id for row in
        db.query(Employee.id, Employee.full_name, Employee.code).all()
        if needle in (row.full_name or "").lower() or needle in (row.code or "").lower()
    ]
    #  Không ai khớp thì trả RỖNG, đừng bỏ qua bộ lọc — bỏ qua nghĩa là gõ sai
    #  tên lại ra nguyên cả bảng, và người dùng tưởng mình tìm đúng.
    return query.filter(LeaveBalance.employee_id.in_(ids or [0]))


@router.get("")
def list_balances(request: Request, pg: dict = Depends(pagination),
                  search: str | None = None,
                  db: Session = Depends(get_db),
                  user=Depends(require(ENTITY, "read"))):
    """Quỹ trong phạm vi người xem («Quỹ của tôi» khi phạm vi = own)."""
    query = apply_filters(db.query(LeaveBalance), LeaveBalance, request, FILTERABLE)
    query = apply_employee_search(db, query, search)
    query = apply_scope(query, LeaveBalance, ENTITY, user, get_perm_profile(db, user))
    total = query.count()
    items = (query.order_by(LeaveBalance.year.desc(), LeaveBalance.employee_id)
             .offset(pg["offset"]).limit(pg["limit"]).all())

    names = _names(db, {i.employee_id for i in items})
    types = _type_names(db)
    return success({"total": total, "items": [_dump(i, names, types) for i in items]})


@router.get("/{bid}")
def get_balance(bid: int, db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "read"))):
    obj = get_scoped(db, LeaveBalance, ENTITY, bid, user, get_perm_profile(db, user))
    if obj is None:
        raise HTTPException(404, "Không tìm thấy dòng quỹ phép")
    return success(_dump(obj, _names(db, {obj.employee_id}), _type_names(db)))


@router.patch("/{bid}/adjust")
def adjust_balance(bid: int, data: LeaveBalanceAdjust, db: Session = Depends(get_db),
                   user=Depends(require(ENTITY, "write"))):
    """Chỉnh tay — cộng hoặc TRỪ. Cột duy nhất nhận số âm.

    Ghi ĐÈ `adjusted_days` chứ không cộng dồn: người dùng nhìn thấy con số hiện
    tại trên màn hình và gõ con số họ muốn nó thành. Cộng dồn thì bấm Lưu hai
    lần là gấp đôi, và không ai đoán được điều đó từ giao diện.

    Bắt buộc có lý do: đây là thao tác tặng ngày phép, phải truy được ai làm và
    vì sao. Dấu vết ghi vào `tab_audit_log` kèm câu này.
    """
    obj = get_scoped(db, LeaveBalance, ENTITY, bid, user, get_perm_profile(db, user),
                     "write")
    if obj is None:
        raise HTTPException(404, "Không tìm thấy dòng quỹ phép")
    if not (data.note or "").strip():
        raise HTTPException(400, "Phải ghi lý do điều chỉnh quỹ phép")

    truoc = obj.adjusted_days
    obj.adjusted_days = round(float(data.adjusted_days), 2)
    obj.note = data.note.strip()[:500]
    obj.updated_by = user.id
    db.commit()
    db.refresh(obj)
    audit_record(db, user.id, ENTITY, obj.id, "update",
                 f"Điều chỉnh quỹ phép: {truoc} → {obj.adjusted_days} ngày. "
                 f"Lý do: {obj.note}")
    return success(_dump(obj, _names(db, {obj.employee_id}), _type_names(db)),
                   "Đã điều chỉnh quỹ phép")


@router.post("/allocate")
def allocate(data: LeaveBalanceAllocate, db: Session = Depends(get_db),
             user=Depends(require(ENTITY, "create"))):
    """Cấp phát quỹ hàng loạt cho một năm — Q1: cấp MỘT LẦN đầu năm.

    Chạy lại được: `ensure_balance` chỉ tạo dòng còn thiếu, dòng đã có thì giữ
    nguyên. Nghĩa là bấm hai lần không nhân đôi quỹ, và thêm người mới vào giữa
    năm thì bấm lại là họ có quỹ — không phải nhớ trạng thái đã chạy hay chưa.

    ⚠️ Cố ý KHÔNG cập nhật dòng đã có theo hạn mức mới. Đổi hạn mức giữa năm thì
    quỹ đã cấp phải giữ nguyên, luật mới áp cho lần cấp sau — xem
    `balance_model.allocated_days`.
    """
    year = data.year or date.today().year

    types = db.query(LeaveType).filter(LeaveType.is_active.is_(True),
                                       LeaveType.counts_balance.is_(True))
    if data.leave_type_ids:
        types = types.filter(LeaveType.id.in_(data.leave_type_ids))
    types = types.all()
    if not types:
        raise HTTPException(400, "Không có loại nghỉ nào cần cấp quỹ "
                                 "(loại phải bật «Trừ vào quỹ phép»).")

    #  Nhân sự được cấp phải nằm trong PHẠM VI của người bấm — không có dòng này
    #  thì Nhân sự công ty con cấp quỹ cho toàn tập đoàn.
    employees = db.query(Employee).filter(Employee.is_active.is_(True))
    if data.employee_ids:
        employees = employees.filter(Employee.id.in_(data.employee_ids))
    employees = apply_scope(employees, Employee, "employee", user,
                            get_perm_profile(db, user)).all()

    created, missing_hire_date = 0, []
    for employee in employees:
        for leave_type in types:
            before = balance_service.get_balance(db, employee.id, year, leave_type.id)
            balance_service.ensure_balance(db, employee, year, leave_type, user.id)
            if before is None:
                created += 1
        if getattr(employee, "hire_date", None) is None:
            missing_hire_date.append(employee.full_name)
    db.commit()

    audit_record(db, user.id, ENTITY, 0, "create",
                 f"Cấp quỹ phép năm {year}: {created} dòng cho {len(employees)} nhân sự")
    return success({
        "year": year,
        "employee_count": len(employees),
        "created": created,
        #  Q4 — nói thẳng ra ai chưa có ngày vào làm. Những người này được cấp
        #  quỹ với thâm niên 0, tức là THIẾU ngày nếu họ đã làm lâu năm. Im lặng
        #  ở đây là để sai số nằm trong sổ cả năm không ai biết.
        "missing_hire_date": missing_hire_date[:50],
        "missing_hire_date_count": len(missing_hire_date),
    }, f"Đã cấp quỹ phép năm {year} — thêm {created} dòng")


@router.get("/tools/summary")
def balance_summary(employee_id: int = 0, year: int = Query(0),
                    db: Session = Depends(get_db),
                    user=Depends(require(ENTITY, "read"))):
    """Toàn bộ quỹ của MỘT người trong một năm — dữ liệu của thẻ «Quỹ phép của tôi».

    Bỏ trống `employee_id` là hỏi quỹ của chính mình. Vẫn đi qua `apply_scope`:
    truyền id người khác vào mà không có phạm vi thì ra rỗng, không ra 403 —
    cùng luật với `get_scoped`, người ngoài phạm vi không cần biết có hay không.
    """
    target = employee_id or getattr(user, "employee_id", 0) or 0
    if not target:
        raise HTTPException(400, "Tài khoản này chưa gắn hồ sơ nhân sự")
    year = year or date.today().year

    query = (db.query(LeaveBalance)
             .filter(LeaveBalance.employee_id == target, LeaveBalance.year == year))
    query = apply_scope(query, LeaveBalance, ENTITY, user, get_perm_profile(db, user))
    rows = query.all()

    names, types = _names(db, {target}), _type_names(db)
    return success({
        "employee_id": target,
        "employee_name": names.get(target, ""),
        "year": year,
        "items": [_dump(r, names, types) for r in rows],
        "total_remaining": round(sum(r.remaining_days for r in rows), 2),
    })
