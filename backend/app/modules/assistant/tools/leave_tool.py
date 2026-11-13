"""Tool NGHỈ PHÉP của trợ lý AI (T35 `my_leave_summary`).

Trả lời đúng ba câu người ta hỏi hằng ngày: "tôi còn mấy ngày phép", "mỗi loại
còn bao nhiêu", "đơn tôi nộp duyệt tới đâu rồi".

Ba ràng buộc của phân hệ Nghỉ phép mà tool này phải tuân, không phải tùy chọn:

* **Số còn lại KHÔNG có cột nào lưu sẵn** — `balance_service.available_days_map` là chỗ
  duy nhất tính (property `remaining_days` trừ thêm phần chưa tới tháng của loại cộng dần,
  duoc-CR-715). Đừng cộng trừ các cột của `tab_leave_balance` ở đây.
* **Một đơn khai NHIỀU loại nghỉ** (`tab_leave_request_line`, 07/09/2026). Hai
  cột đầu đơn là DẪN XUẤT: `total_days` = tổng các dòng, `leave_type_id` = loại
  của dòng nhiều ngày nhất. Muốn nói đúng "3 ngày phép năm + 2 ngày không lương"
  thì phải đọc THEO DÒNG.
* **Read-only tuyệt đối.** `balance_service.ensure_balance()` vừa đọc vừa CẤP
  PHÁT một dòng quỹ mới — tool không được gọi nó (luật 4 ở `base.py`). Loại nghỉ
  chưa ai cấp quỹ thì trả về với cờ `allocated=False` chứ không tự đẻ dòng.
* **Ngày đã nghỉ + lịch làm việc** (duoc-CR-757): `taken_by_type` (mọi loại, kể cả loại không trừ quỹ) và
  `work_schedule` (lịch đang áp hôm nay) dựng ở `leave_taken_schedule` — dùng chung với `employee_leave_summary`.
* **Chính sách nghỉ phép** (duoc-CR-717): `policy` + `policy_name` / `policy_annual_days` từng loại đọc qua
  `policy_allocation.load_assignments` / `load_lines` (không khóa, không ghi) — để trả lời "vì sao hạn mức của tôi
  khác người khác". Con số hạn mức vẫn là `allocated_days` của dòng quỹ.

Gác quyền: `leave_request.read`, cùng lý lẽ với `GET /api/leave-requests/tools/my-balance`
— đây là quỹ của CHÍNH người hỏi, ai nộp được đơn thì phải thấy được số còn lại;
bắt thêm khóa `leave_balance` nữa là chắc chắn có người quên cấp rồi con số hiện
0 vĩnh viễn.

⚠️ **Chỉ lọc theo `employee_id`, KHÔNG lọc theo `created_by`** — khác khuôn
`my_tickets`/`my_procurement_requests` và khác có chủ ý. Ở phân hệ này
`created_by` nghĩa là "tôi lập hộ NGƯỜI KHÁC", tức dữ liệu nghỉ phép của người
đó; gộp vào "đơn của tôi" là vừa trả lời sai câu hỏi vừa phát dữ liệu người khác
qua một tool không đi qua `apply_scope`. Hành chính muốn xem đơn mình lập hộ thì
vào màn Nghỉ phép.
"""
from datetime import date

from app.core.vn_time import vn_today
from app.modules.employee.model import Employee
from app.modules.leave import balance_service, policy_allocation
from app.modules.leave.policy_model import LeavePolicy
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveType
from app.modules.leave.constants import (LEAVE_ACCRUAL_MODE_LABELS, LEAVE_REQUEST_STATUS_LABELS,
                                         LEAVE_SESSION_LABELS, LR_APPROVED, LR_CANCELLED, LR_DRAFT, LR_PENDING,
                                         LR_REJECTED, LR_RETURNED, label)
from app.modules.leave.period_spans import header_period, period_text, periods_by_request
from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine
from app.modules.work_schedule import resolver

from .base import ToolContext, ToolSpec, denied
from .leave_comp_tool import my_comp_requests
from .leave_encashment_tool import my_encashments
from .leave_taken_schedule import SCHEDULE_GLOSSARY, TAKEN_GLOSSARY, build_schedule_brief, taken_by_type_many

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
    "rồi', 'lịch làm việc của tôi thế nào'... Chỉ trả dữ liệu của người hỏi — tra phép của NGƯỜI KHÁC thì dùng "
    "employee_leave_summary. Hỏi 'đã nghỉ mấy ngày' thì đọc `taken_total_days` / `approved_days` của "
    "`taken_by_type` (đủ mọi loại nghỉ, kể cả không lương, ốm; chỉ ngày đã / đang nghỉ — ngày đã duyệt chưa tới nằm ở "
    "`approved_upcoming_days`, nói riêng); hỏi 'lịch làm việc của tôi' / 'thứ Bảy có phải đi làm không' thì đọc `work_schedule` "
    "(lịch đang áp hôm nay, ngày nghỉ phép được đếm theo lịch này). Khi trả "
    "lời, nói rõ 'đang giữ chỗ' là ngày của đơn đã gửi nhưng chưa duyệt xong (đã bị trừ "
    "khỏi số còn lại), và kèm `url` dạng link để người dùng bấm mở đơn. Số còn nghỉ được là "
    "`remaining_days` (đã trừ phần chưa tới tháng của loại cộng dần) — đừng tự cộng trừ; "
    "`comp_days` là ngày nghỉ bù đã được duyệt cộng thêm, `max_negative_days` > 0 là được ứng "
    "phép tới số đó. Kèm cả phiếu xin nghỉ bù của họ (`comp_requests`) và chính sách nghỉ phép đang áp "
    "(`policy`, null = theo hạn mức của loại nghỉ)."
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
                   "is_active": bool(r.is_active),
                   #  duoc-CR-715: luật cấp quỹ — để trợ lý giải thích được vì sao con số thấp hơn hạn mức năm.
                   "accrual_mode": int(r.accrual_mode or 1),
                   "max_negative_days": float(r.max_negative_days or 0.0),
                   "applicable_after_days": int(r.applicable_after_days or 0),
                   "is_compensatory": bool(r.is_compensatory),
                   #  duoc-CR-719: luật thanh toán ngày phép chưa nghỉ ra tiền (chỉ ngày, không tiền).
                   "allow_encashment": bool(r.allow_encashment),
                   "max_encashable_days": float(r.max_encashable_days or 0.0),
                   "non_encashable_days": float(r.non_encashable_days or 0.0)} for r in rows}


def _rules(info: dict) -> dict:
    """Luật của loại nghỉ người dùng hay hỏi (cách cấp, ứng phép, dùng sau N ngày vào làm, nhận ngày bù)."""
    mode = info.get("accrual_mode", 1)
    return {"accrual_mode": mode, "accrual_mode_label": label(LEAVE_ACCRUAL_MODE_LABELS, mode),
            "max_negative_days": info.get("max_negative_days", 0.0),
            "applicable_after_days": info.get("applicable_after_days", 0),
            "is_compensatory": info.get("is_compensatory", False),
            "allow_encashment": info.get("allow_encashment", False),
            "max_encashable_days": info.get("max_encashable_days", 0.0),
            "non_encashable_days": info.get("non_encashable_days", 0.0)}


def _active_policy(db, employee_id: int, year: int) -> dict | None:
    """Chính sách nghỉ phép đang áp cho người hỏi (duoc-CR-717) — CHỈ ĐỌC, cố định 3 truy vấn.

    Mốc xem = hôm nay kẹp vào năm hỏi (năm đã qua → 31/12, năm sau → 01/01): trả lời được "vì sao hạn mức Phép năm
    của tôi là 15 chứ không phải 12". Không có phân bổ nào phủ mốc → `None` (hạn mức theo luật của loại nghỉ).
    Năm đổi chính sách giữa chừng thì `allocated_days` đã là số chia theo tháng — đây chỉ nói gói ĐANG áp.
    """
    ref = min(max(vn_today(), date(year, 1, 1)), date(year, 12, 31))
    spans = policy_allocation.load_assignments(db, [employee_id], year)[employee_id]
    current = next((a for a in spans if a.effective_from <= ref and (a.effective_to is None or a.effective_to >= ref)),
                   None)
    if current is None:
        return None
    policy = db.get(LeavePolicy, current.policy_id)
    lines = policy_allocation.load_lines(db, {current.policy_id}).get(current.policy_id, {})
    return {"name": policy.name if policy else "", "code": policy.code if policy else "",
            "effective_from": current.effective_from.isoformat(),
            "effective_to": current.effective_to.isoformat() if current.effective_to else None,
            "lines": lines}


def _policy_fields(policy: dict | None, leave_type_id: int) -> dict:
    """Tên gói đang áp + số ngày/năm gói khai cho loại này (`None` = gói không khai loại này → theo luật của loại)."""
    if policy is None:
        return {"policy_name": None, "policy_annual_days": None}
    return {"policy_name": policy["name"], "policy_annual_days": policy["lines"].get(leave_type_id)}


def _balances(db, employee_id: int, year: int, types: dict[int, dict], policy: dict | None = None) -> list[dict]:
    """Quỹ phép từng loại. Loại chưa được cấp quỹ vẫn liệt kê, kèm cờ `allocated`.

    Liệt kê cả loại chưa cấp vì im lặng bỏ qua thì người hỏi đọc ra "công ty
    không có loại nghỉ đó", trong khi sự thật là "Nhân sự chưa cấp quỹ cho bạn" —
    hai việc phải xử lý khác hẳn nhau.
    """
    rows = (db.query(LeaveBalance)
            .filter(LeaveBalance.employee_id == employee_id, LeaveBalance.year == year)
            .all())
    available = balance_service.available_days_map(db, rows)    # một lượt, không tra từng dòng
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
            "allocated_days": r.allocated_days,
            #  duoc-CR-715 C: ngày nghỉ bù đã duyệt cộng vào loại này (đã nằm trong `total_days`).
            "comp_days": float(r.comp_days or 0.0),
            #  duoc-CR-719: ngày đã thanh toán ra tiền (đã TRỪ khỏi `remaining_days`).
            "encashed_days": float(r.encashed_days or 0.0),
            #  Phần hạn mức CHƯA TỚI THÁNG của loại cộng dần — có trong `total_days` nhưng chưa nghỉ được.
            "not_yet_accrued_days": round(r.remaining_days - available[r.id], 2),
            **_rules(info),
            **_policy_fields(policy, r.leave_type_id),
            #  Nguồn DUY NHẤT của con số này là `balance_service.available_days` (property của model trừ phần chưa tới
            #  tháng của loại cộng dần — duoc-CR-715). Đọc thẳng `r.remaining_days` là trợ lý báo dư phép.
            "remaining_days": available[r.id],
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
            "allocated_days": 0.0,
            "comp_days": 0.0,
            "encashed_days": 0.0,
            "not_yet_accrued_days": 0.0,
            **_rules(info),
            **_policy_fields(policy, tid),
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
        year = vn_today().year   # giờ VN — container chạy UTC, 00:00–06:59 sáng 01/01 sẽ lệch năm
    if year < 2000 or year > 2100:
        year = vn_today().year
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
    periods = periods_by_request(ctx.db, [r.id for r in rows])   # 1 truy vấn cho cả danh sách

    requests = [{
        "code": r.code,
        "from_date": r.from_date.isoformat() if r.from_date else "",
        "to_date": r.to_date.isoformat() if r.to_date else "",
        "periods_text": period_text(periods.get(r.id) or [header_period(r)]),
        "periods": [{"from_date": p.from_date.isoformat(), "to_date": p.to_date.isoformat(),
                     "from_session_label": label(LEAVE_SESSION_LABELS, p.from_session),
                     "to_session_label": label(LEAVE_SESSION_LABELS, p.to_session),
                     "days": p.days}
                    for p in (periods.get(r.id) or [header_period(r)])],
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

    #  Phiếu xin nghỉ bù của CHÍNH người hỏi (khóa riêng `leave_comp_request`; thiếu khóa thì bỏ qua, không chặn cả tool).
    comp = my_comp_requests(ctx.db, emp_id, limit) if ctx.can("leave_comp_request") else None

    #  Phiếu thanh toán nghỉ phép của chính người hỏi, năm đang xem (khóa riêng; thiếu khóa thì bỏ qua). Chỉ ngày + trạng thái.
    encashments = my_encashments(ctx.db, emp_id, year, limit) if ctx.can("leave_encashment") else None

    policy = _active_policy(ctx.db, emp_id, year)
    today = vn_today()
    #  Đơn của CHÍNH người hỏi (đã gác `leave_request.read` ở đầu) — không cần lọc phạm vi.
    taken = taken_by_type_many(ctx.db, [emp_id], year, types, today=today)[emp_id]
    employee = ctx.db.get(Employee, emp_id)   # hồ sơ của CHÍNH người hỏi — không phải đọc hồ sơ người khác
    work_schedule = (build_schedule_brief(resolver.effective_for_employee(ctx.db, employee, today))
                     if employee is not None else None)
    return {
        "year": year,
        "balances": _balances(ctx.db, emp_id, year, types, policy),
        "taken_by_type": taken["taken_by_type"],
        "taken_total_days": taken["taken_total_days"],
        "upcoming_total_days": taken["upcoming_total_days"],
        "pending_total_days": taken["pending_total_days"],
        "work_schedule": work_schedule,
        "policy": None if policy is None else {k: v for k, v in policy.items() if k != "lines"},
        "requests": requests,
        "comp_requests": comp if comp is not None else [],
        "encashments": encashments if encashments is not None else [],
        "total": len(requests),
        "glossary": {
            "taken_by_type": TAKEN_GLOSSARY,
            "work_schedule": SCHEDULE_GLOSSARY,
            "total_days": "Tổng quỹ được hưởng trong năm (đã gồm thâm niên và ngày chuyển "
                          "sang từ năm trước).",
            "pending_days": "Ngày đang GIỮ CHỖ cho đơn đã gửi nhưng chưa duyệt xong — đã "
                            "trừ khỏi số còn lại; đơn bị từ chối/trả về/rút thì trả lại.",
            "from_date_to_date": "from_date/to_date là ngày ĐẦU và CUỐI của cả đơn. Đơn nghỉ nhiều "
                                 "khoảng không liền nhau (periods có từ 2 phần tử) thì chỉ nghỉ trong "
                                 "từng khoảng — đọc `periods`/`periods_text`, đừng nói nghỉ liền cả quãng.",
            "remaining_days": "Số ngày còn nghỉ được = tổng quỹ - đã dùng - đang giữ chỗ - phần chưa tới tháng "
                              "(not_yet_accrued_days, chỉ loại cộng dần theo tháng). Đây là con số DUY NHẤT để trả lời "
                              "'còn bao nhiêu phép'.",
            "comp_days": "Ngày nghỉ bù đã được duyệt (đi làm ngày lễ / ngày nghỉ), đã cộng vào total_days của loại "
                         "nghỉ bù. Xin thêm thì dùng draft_leave_comp_request.",
            "max_negative_days": "Lớn hơn 0 = loại này cho ỨNG PHÉP: được xin vượt số còn lại tối đa chừng đó ngày "
                                 "(còn lại thành số âm). Bằng 0 = không cho ứng, vượt phải chọn Nghỉ không lương.",
            "applicable_after_days": "Lớn hơn 0 = loại này chỉ dùng được sau chừng đó ngày kể từ ngày vào làm.",
            "accrual_mode_label": "Cách cấp quỹ: đủ hạn mức đầu năm / theo tỷ lệ tháng làm việc (người vào làm trong "
                                  "năm) / cộng dần theo tháng.",
            "encashed_days": "Ngày phép ĐÃ thanh toán ra tiền (phiếu thanh toán nghỉ phép đã duyệt) — đã trừ khỏi "
                             "remaining_days, không nghỉ được nữa. Chỉ có số ngày; trợ lý KHÔNG biết và KHÔNG nói số tiền.",
            "allow_encashment": "true = loại nghỉ này cho đổi ngày phép chưa nghỉ ra tiền (cuối năm hoặc khi nghỉ việc). "
                                "max_encashable_days > 0 là trần ngày thanh toán mỗi năm; non_encashable_days là số ngày "
                                "phải giữ lại (chỉ áp cho cuối năm). Muốn thanh toán thì mở Nghỉ phép ▸ Thanh toán nghỉ phép; "
                                "trợ lý không soạn phiếu này.",
            "encashments": "Phiếu thanh toán nghỉ phép của người hỏi trong năm đang xem: số ngày, trạng thái duyệt và "
                           "payment_status_label (trạng thái chi của kế toán). Không có số tiền.",
            "comp_requests": "Phiếu xin nghỉ bù của người hỏi; Đã duyệt = số ngày đã cộng vào comp_days.",
            "policy": "Chính sách nghỉ phép Nhân sự đang phân bổ cho người hỏi (null = không có, hạn mức theo luật "
                      "của loại nghỉ). policy_annual_days của từng loại = số ngày/năm gói khai; null = gói không khai "
                      "loại đó nên theo luật của loại. allocated_days mới là hạn mức thật (đổi gói giữa năm thì chia "
                      "theo tháng) — đừng lấy policy_annual_days thay cho nó.",
        },
    }


MY_LEAVE_SUMMARY_SPEC = ToolSpec(
    name="my_leave_summary",
    description=_DESC,
    parameters=_PARAMS,
    handler=_run,
)
