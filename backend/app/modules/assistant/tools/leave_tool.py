"""Tool NGHỈ PHÉP của trợ lý AI (T35 `my_leave_summary`).

Trả lời đúng ba câu người ta hỏi hằng ngày: «tôi còn mấy ngày phép», «mỗi loại
còn bao nhiêu», «đơn tôi nộp duyệt tới đâu rồi».

Ba ràng buộc của phân hệ Nghỉ phép mà tool này phải tuân, không phải tùy chọn:

* **Số còn lại KHÔNG có cột nào lưu sẵn** — `LeaveBalance.remaining_days` là chỗ
  duy nhất tính. Đừng cộng trừ các cột của `tab_leave_balance` ở đây.
* **Một đơn khai NHIỀU loại nghỉ** (`tab_leave_request_line`, 07/09/2026). Hai
  cột đầu đơn là DẪN XUẤT: `total_days` = tổng các dòng, `leave_type_id` = loại
  của dòng nhiều ngày nhất. Muốn nói đúng «3 ngày phép năm + 2 ngày không lương»
  thì phải đọc THEO DÒNG.
* **Read-only tuyệt đối.** `balance_service.ensure_balance()` vừa đọc vừa CẤP
  PHÁT một dòng quỹ mới — tool không được gọi nó (luật 4 ở `base.py`). Loại nghỉ
  chưa ai cấp quỹ thì trả về với cờ `allocated=False` chứ không tự đẻ dòng.

Gác quyền: `leave_request.read`, cùng lý lẽ với `GET /api/leave-requests/tools/my-balance`
— đây là quỹ của CHÍNH người hỏi, ai nộp được đơn thì phải thấy được số còn lại;
bắt thêm khóa `leave_balance` nữa là chắc chắn có người quên cấp rồi con số hiện
0 vĩnh viễn.

⚠️ **Chỉ lọc theo `employee_id`, KHÔNG lọc theo `created_by`** — khác khuôn
`my_tickets`/`my_procurement_requests` và khác có chủ ý. Ở phân hệ này
`created_by` nghĩa là «tôi lập hộ NGƯỜI KHÁC», tức dữ liệu nghỉ phép của người
đó; gộp vào «đơn của tôi» là vừa trả lời sai câu hỏi vừa phát dữ liệu người khác
qua một tool không đi qua `apply_scope`. Hành chính muốn xem đơn mình lập hộ thì
vào màn Nghỉ phép.
"""
from datetime import date

from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (LEAVE_REQUEST_STATUS_LABELS, LEAVE_SESSION_LABELS,
                                         LR_APPROVED, LR_CANCELLED, LR_DRAFT, LR_PENDING,
                                         LR_REJECTED, LR_RETURNED, label)
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine

from .base import ToolContext, ToolSpec, denied

MAX_ROWS = 30

_STATUS_CODES = (LR_DRAFT, LR_PENDING, LR_APPROVED, LR_REJECTED, LR_RETURNED, LR_CANCELLED)

_PARAMS = {
    "type": "object",
    "properties": {
        "year": {
            "type": "integer",
            "description": "Năm của quỹ phép cần xem (ví dụ 2026). Bỏ trống = năm hiện tại.",
        },
        "status": {
            "type": "integer",
            "enum": list(_STATUS_CODES),
            "description": "Lọc đơn theo trạng thái: 1 Nháp | 2 Chờ duyệt | 3 Đã duyệt | "
                           "4 Từ chối | 5 Trả về chỉnh sửa | 6 Đã hủy. Bỏ trống = tất cả.",
        },
        "limit": {
            "type": "integer",
            "description": f"Số đơn tối đa liệt kê (mặc định 10, trần {MAX_ROWS}). "
                           "Quỹ phép luôn trả đủ mọi loại, không bị cắt theo số này.",
        },
    },
}

_DESC = (
    "Tình hình NGHỈ PHÉP của CHÍNH người hỏi: số ngày phép còn lại TỪNG LOẠI nghỉ trong "
    "năm (tổng quỹ, đã dùng, đang giữ chỗ chờ duyệt, còn lại) kèm danh sách đơn nghỉ phép "
    "của họ và trạng thái duyệt. Gọi khi người dùng hỏi 'tôi còn bao nhiêu ngày phép', "
    "'phép năm còn mấy ngày', 'đơn nghỉ phép của tôi duyệt chưa', 'tôi đã nghỉ mấy ngày "
    "rồi'... Chỉ trả dữ liệu của người hỏi — KHÔNG tra được phép của người khác. Khi trả "
    "lời, nói rõ 'đang giữ chỗ' là ngày của đơn đã gửi nhưng chưa duyệt xong (đã bị trừ "
    "khỏi số còn lại), và kèm `url` dạng link để người dùng bấm mở đơn."
)


def _clamp(value, default: int, hi: int = MAX_ROWS) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(n, hi))


def _type_names(db) -> dict[int, dict]:
    """Danh mục loại nghỉ tra một lần — tránh N+1 khi dựng quỹ và dựng dòng đơn."""
    rows = db.query(LeaveType).all()
    return {r.id: {"name": r.name, "code": r.code,
                   "counts_balance": bool(r.counts_balance),
                   "is_active": bool(r.is_active)} for r in rows}


def _balances(db, employee_id: int, year: int, types: dict[int, dict]) -> list[dict]:
    """Quỹ phép từng loại. Loại chưa được cấp quỹ vẫn liệt kê, kèm cờ `allocated`.

    Liệt kê cả loại chưa cấp vì im lặng bỏ qua thì người hỏi đọc ra "công ty
    không có loại nghỉ đó", trong khi sự thật là "Nhân sự chưa cấp quỹ cho bạn" —
    hai việc phải xử lý khác hẳn nhau.
    """
    rows = (db.query(LeaveBalance)
            .filter(LeaveBalance.employee_id == employee_id, LeaveBalance.year == year)
            .all())
    items = []
    for r in rows:
        info = types.get(r.leave_type_id) or {}
        items.append({
            "leave_type_id": r.leave_type_id,
            "leave_type": info.get("name", ""),
            "leave_type_code": info.get("code", ""),
            "allocated": True,
            "total_days": r.total_days,
            "used_days": r.used_days,
            "pending_days": r.pending_days,
            "carried_days": r.carried_days,
            #  Nguồn DUY NHẤT của con số này là property của model — đừng tự trừ.
            "remaining_days": r.remaining_days,
        })
    have = {r.leave_type_id for r in rows}
    for tid, info in types.items():
        if tid in have or not info["is_active"] or not info["counts_balance"]:
            continue
        items.append({
            "leave_type_id": tid,
            "leave_type": info["name"],
            "leave_type_code": info["code"],
            "allocated": False,
            "total_days": 0.0,
            "used_days": 0.0,
            "pending_days": 0.0,
            "carried_days": 0.0,
            "remaining_days": 0.0,
            "note": "Nhân sự chưa cấp quỹ phép loại này cho bạn trong năm.",
        })
    items.sort(key=lambda x: (not x["allocated"], x["leave_type"]))
    return items


def _lines_by_request(db, request_ids: list[int], types: dict[int, dict]) -> dict[int, list]:
    """Dòng loại nghỉ của các đơn — MỘT truy vấn `IN`, không vòng lặp."""
    if not request_ids:
        return {}
    rows = (db.query(LeaveRequestLine)
            .filter(LeaveRequestLine.request_id.in_(request_ids))
            .order_by(LeaveRequestLine.sort_order, LeaveRequestLine.id)
            .all())
    out: dict[int, list] = {}
    for r in rows:
        info = types.get(r.leave_type_id) or {}
        out.setdefault(r.request_id, []).append({
            "leave_type_id": r.leave_type_id,
            "leave_type": info.get("name", ""),
            "days": r.days,
        })
    return out


def _run(ctx: ToolContext, args: dict) -> dict:
    if not ctx.can("leave_request"):
        return denied("đơn nghỉ phép (leave_request.read)")

    emp_id = int(getattr(ctx.user, "employee_id", 0) or 0)
    if not emp_id:
        return {"error": "Tài khoản của bạn chưa gắn hồ sơ nhân sự nên chưa có quỹ phép. "
                         "Liên hệ phòng Nhân sự để được gắn hồ sơ."}

    year = args.get("year")
    try:
        year = int(year)
    except (TypeError, ValueError):
        year = date.today().year
    if year < 2000 or year > 2100:
        year = date.today().year
    limit = _clamp(args.get("limit"), 10)

    types = _type_names(ctx.db)

    q = (ctx.db.query(LeaveRequest)
         .filter(LeaveRequest.employee_id == emp_id, LeaveRequest.is_deleted.is_(False)))
    status = args.get("status")
    try:
        status = int(status)
    except (TypeError, ValueError):
        status = 0
    if status in _STATUS_CODES:
        q = q.filter(LeaveRequest.status == status)
    rows = q.order_by(LeaveRequest.id.desc()).limit(limit).all()
    lines = _lines_by_request(ctx.db, [r.id for r in rows], types)

    requests = [{
        "code": r.code,
        "from_date": r.from_date.isoformat() if r.from_date else "",
        "to_date": r.to_date.isoformat() if r.to_date else "",
        "from_session_label": label(LEAVE_SESSION_LABELS, r.from_session),
        "to_session_label": label(LEAVE_SESSION_LABELS, r.to_session),
        "total_days": r.total_days,
        #  R2/QĐ-11: trả CẢ số lẫn nhãn — model cần nhãn để nói, số để so sánh.
        "status": r.status,
        "status_label": label(LEAVE_REQUEST_STATUS_LABELS, r.status),
        "reason": r.reason or "",
        "decision_note": r.decision_note or "",
        #  `leave_type_id` đầu đơn là dẫn xuất (loại của dòng nhiều ngày nhất) nên
        #  không trả ra — trả nguyên các dòng để nói đúng từng loại.
        "lines": lines.get(r.id, []),
        "url": f"/hr/leave-requests/{r.id}",
    } for r in rows]

    return {
        "year": year,
        "balances": _balances(ctx.db, emp_id, year, types),
        "requests": requests,
        "total": len(requests),
        "glossary": {
            "total_days": "Tổng quỹ được hưởng trong năm (đã gồm thâm niên và ngày chuyển "
                          "sang từ năm trước).",
            "pending_days": "Ngày đang GIỮ CHỖ cho đơn đã gửi nhưng chưa duyệt xong — đã "
                            "trừ khỏi số còn lại; đơn bị từ chối/trả về/rút thì trả lại.",
            "remaining_days": "Số ngày còn nghỉ được = tổng quỹ - đã dùng - đang giữ chỗ.",
        },
    }


MY_LEAVE_SUMMARY_SPEC = ToolSpec(
    name="my_leave_summary",
    description=_DESC,
    parameters=_PARAMS,
    handler=_run,
)
