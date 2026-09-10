"""Tổng quan Duyệt dấu — số liệu theo VAI TRÒ, suy từ QUYỀN.

Cùng khuôn Đặt xe (`vehicle_booking/dashboard_service.py`) và
`app/modules/dashboard/controller.py::overview`: gác TỪNG KHỐI bằng `can(action)`,
mọi truy vấn đi qua `apply_scope`; thiếu quyền thì khối VẮNG MẶT.

Luồng hai cổng (TBP duyệt → Văn thư đóng dấu) nên các khối là:
  · `mine`    — người dùng (`create`): phiếu của tôi, đếm theo trạng thái.
  · `approve` — Trưởng bộ phận / TBP (`approve`): hàng CHỜ TÔI DUYỆT (Chờ duyệt).
  · `clerk`   — Văn thư (`write`): hàng CHỜ ĐÓNG DẤU (Đã duyệt) + đã đóng dấu.
  · `company` — Giám đốc / phạm vi ≥ phòng: tổng hợp theo phạm vi.

⚠️ Nhánh phạm vi `company` của seal (xem `core/scoping.py`) CHỈ trả phiếu Đã duyệt /
Hoàn thành. Nên với Văn thư / Giám đốc (company), khối tổng hợp và "phiếu của tôi"
chỉ thấy phiếu đã qua TBP — đúng thiết kế, không phải thiếu số.
"""
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.scoping import apply_scope

from . import service
from .model import (
    SEAL_APPROVED,
    SEAL_COMPLETED,
    SEAL_PENDING,
    SEAL_STATUS_LABELS,
    SealRequest,
)

ENTITY = "seal_request"
RECENT_LIMIT = 8


def _month_starts(count: int = 12) -> list[datetime]:
    now = datetime.now()
    base_year, base_month = now.year, now.month
    starts: list[datetime] = []
    for offset in range(count - 1, -1, -1):
        total = (base_year * 12 + (base_month - 1)) - offset
        starts.append(datetime(total // 12, total % 12 + 1, 1))
    return starts


def _month_range(d_from: datetime, d_to: datetime) -> list[datetime]:
    """Danh sách mốc đầu-tháng phủ [d_from, d_to] (giới hạn 36 tháng cho khỏi phình)."""
    first = d_from.year * 12 + (d_from.month - 1)
    last = d_to.year * 12 + (d_to.month - 1)
    if last < first:
        last = first
    last = min(last, first + 35)  # trần 36 cột
    return [datetime(t // 12, t % 12 + 1, 1) for t in range(first, last + 1)]


def _trend(scoped_query, starts: list[datetime]) -> list[dict]:
    """Số phiếu tạo theo THÁNG cho các mốc `starts` (đếm theo khoảng `created_at`)."""
    points: list[dict] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else None
        q = scoped_query.filter(SealRequest.created_at >= start)
        if end is not None:
            q = q.filter(SealRequest.created_at < end)
        points.append({"label": f"{start.month:02d}/{start.year}", "value": q.count()})
    return points


def _has_grant(prof: dict, action: str, scope: str) -> bool:
    """Có grant nào cấp `action` cho seal_request ở ĐÚNG `scope` không?

    Phân vai bằng grant (không phải `perms_union` toàn cục): Văn thư = có `write`
    phạm vi company; Giám đốc = có `read` phạm vi company. Đọc toàn cục sẽ sai vì ai
    cũng có `write` phạm vi own (vai trò nền `employee`)."""
    for g in prof.get("grants", []):
        p = g["perms"].get(ENTITY)
        if p and p.get(action) and p.get("scope") == scope:
            return True
    return False


def _parse_day(value: str | None):
    """'yyyy-mm-dd' → datetime đầu ngày; None/rỗng/sai định dạng → None."""
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return None


def build_overview(db: Session, user, date_from: str | None = None,
                   date_to: str | None = None) -> dict:
    """Số liệu tổng quan Duyệt dấu cho người đang đăng nhập.

    `date_from`/`date_to` (yyyy-mm-dd) lọc theo KHOẢNG NGÀY TẠO cho MỌI khối báo cáo
    (theo tháng · theo trạng thái · theo công ty). Bỏ trống = tất cả. Giao diện mặc
    định truyền 30 ngày gần nhất."""
    prof = get_perm_profile(db, user)

    def can(action: str) -> bool:
        return bool(prof["perms_union"].get(ENTITY, {}).get(action))

    def scoped():
        query = db.query(SealRequest).filter(SealRequest.is_deleted == False)  # noqa: E712
        return apply_scope(query, SealRequest, ENTITY, user, prof)

    data: dict = {
        "can": {e: bool(prof["perms_union"].get(e, {}).get("read"))
                for e in ("seal_request", "seal_type")},
    }
    if not can("read"):
        return data

    # ── mine (người dùng): phiếu của tôi ──────────────────────────────────────
    if can("create"):
        mine_q = scoped().filter(SealRequest.created_by == user.id)
        by_status = dict(
            mine_q.with_entities(SealRequest.status, func.count(SealRequest.id))
            .group_by(SealRequest.status).all())
        recent = mine_q.order_by(SealRequest.id.desc()).limit(RECENT_LIMIT).all()
        data["mine"] = {
            "by_status": {int(k): int(v) for k, v in by_status.items()},
            "recent": service.serialize_seal_requests(db, recent),
        }

    # ── approve (TBP): chờ tôi duyệt ──────────────────────────────────────────
    if can("approve"):
        pend_q = scoped().filter(SealRequest.status == SEAL_PENDING)
        data["approve"] = {
            "pending": pend_q.count(),
            "items": service.serialize_seal_requests(
                db, pend_q.order_by(SealRequest.id.desc()).limit(RECENT_LIMIT).all()),
        }

    #  Văn thư = có grant `write` phạm vi COMPANY (đóng dấu). KHÔNG dùng `can("write")`
    #  toàn cục vì mọi nhân sự đều có write phạm vi own (vai trò `employee`).
    is_clerk = _has_grant(prof, "write", "company")

    # ── clerk (Văn thư): chờ đóng dấu (Đã duyệt) + đã đóng dấu ─────────────────
    if is_clerk:
        base = scoped()
        to_stamp = base.filter(SealRequest.status == SEAL_APPROVED)
        data["clerk"] = {
            "to_stamp": to_stamp.count(),
            "completed": base.filter(SealRequest.status == SEAL_COMPLETED).count(),
            "queue": service.serialize_seal_requests(
                db, to_stamp.order_by(SealRequest.id.desc()).limit(RECENT_LIMIT).all()),
        }

    # ── director (Giám đốc — chỉ ĐỌC, phạm vi công ty): yêu cầu ĐÃ phê duyệt ───
    #  Giám đốc = có `read` phạm vi company nhưng KHÔNG phải Văn thư (không đóng dấu)
    #  và KHÔNG duyệt (TBP). Khối bảng ở cột 2: yêu cầu đã phê duyệt của công ty mình.
    is_director = _has_grant(prof, "read", "company") and not is_clerk and not can("approve")
    if is_director:
        appr = scoped().filter(SealRequest.status.in_([SEAL_APPROVED, SEAL_COMPLETED]))
        data["director"] = {
            "count": appr.count(),
            "items": service.serialize_seal_requests(
                db, appr.order_by(SealRequest.id.desc()).limit(RECENT_LIMIT).all()),
        }

    # ── stats (MỌI vai trò): thống kê theo PHẠM VI RIÊNG của người xem ─────────
    #  Theo tháng / trạng thái / công ty, tính trên `scoped()` nên mỗi người thấy
    #  đúng phần dữ liệu mình xem được (own = phiếu của tôi, dept/company = rộng hơn).
    #  MỘT khoảng ngày tạo áp cho CẢ BA khối (giao diện mặc định 30 ngày; bỏ = tất cả).
    d_from, d_to = _parse_day(date_from), _parse_day(date_to)
    ranged = scoped()
    if d_from is not None:
        ranged = ranged.filter(SealRequest.created_at >= d_from)
    if d_to is not None:  # bao trọn ngày kết thúc
        ranged = ranged.filter(SealRequest.created_at < d_to + timedelta(days=1))
    st_rows = dict(
        ranged.with_entities(SealRequest.status, func.count(SealRequest.id))
        .group_by(SealRequest.status).all())
    #  Khối "theo tháng": có khoảng thì dựng cột theo tháng của khoảng đó, không thì 12
    #  tháng gần nhất. Đếm trên `ranged` để khớp đúng hai khối kia.
    starts = _month_range(d_from, d_to) if (d_from and d_to) else _month_starts(12)
    data["stats"] = {
        "by_status": [
            {"key": int(k), "label": SEAL_STATUS_LABELS.get(int(k), str(k)), "value": int(v)}
            for k, v in sorted(st_rows.items())],
        "by_company": _by_company(db, ranged),
        "trend": _trend(ranged, starts),
    }
    return data


def _by_company(db: Session, scoped_query) -> list[dict]:
    """Top CÔNG TY theo số phiếu (kèm tên công ty).

    Một phiếu gắn NHIỀU công ty (bảng nối `tab_seal_request_company`) nên đếm theo
    bảng nối — mỗi công ty trong phiếu +1. Giữ đúng phạm vi bằng cách join với các
    phiếu người xem thấy được (`scoped_query`)."""
    from app.modules.company.model import Company

    from .model import SealRequestCompany as SRC

    rows = (scoped_query
            .join(SRC, SRC.seal_request_id == SealRequest.id)
            .with_entities(SRC.company_id, func.count(func.distinct(SealRequest.id)))
            .group_by(SRC.company_id).all())
    if not rows:
        return []
    names = dict(db.query(Company.id, Company.name)
                 .filter(Company.id.in_([r[0] for r in rows if r[0]])).all())
    out = [{"id": int(cid or 0),
            "name": names.get(cid, f"#{cid}") if cid else "Chưa gán công ty",
            "value": int(count)}
           for cid, count in rows]
    out.sort(key=lambda x: x["value"], reverse=True)
    return out[:8]
