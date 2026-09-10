"""Tổng quan Đặt xe — số liệu theo VAI TRÒ, suy từ QUYỀN + hồ sơ tài xế.

Cùng khuôn `app/modules/dashboard/controller.py::overview`: hàm chạy sau khi route
đã xác thực đăng nhập, gác TỪNG KHỐI bằng `can(action)`, mọi truy vấn đi qua
`apply_scope` nên số liệu luôn nằm trong phạm vi người xem. **Thiếu quyền thì khối
VẮNG MẶT** (không trả `0`) — giao diện đọc kèm `?? 0` và chỉ vẽ khối nào có mặt.

Mỗi khối ứng một vai (app không lưu mã vai trò; vai suy từ quyền):
  · `mine`     — người dùng (`create`): phiếu của tôi, đếm theo trạng thái.
  · `approve`  — người duyệt / TBP (`approve`): hàng chờ tôi duyệt.
  · `dispatch` — điều phối viên (`write`): chờ điều phối + KPI đội xe.
  · `driver`   — tài xế (có hồ sơ `Driver` nối tài khoản): bảng chuyến của tôi.
  · `company`  — giám đốc / phạm vi ≥ phòng: tổng hợp theo phạm vi xem được.
"""
from datetime import datetime, timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.auth import get_perm_profile
from app.core.scoping import apply_scope

from . import service
from .model import (
    BK_APPROVED,
    BK_COMPLETED,
    BK_DISPATCHED,
    BK_PENDING,
    BOOKING_STATUS_LABELS,
    DRV_ACCEPTED,
    DRV_COMPLETED,
    DRV_ONGOING,
    DRV_WAITING,
    TYPE_CAR,
    TYPE_DELIVERY,
    VehicleBooking,
)

ENTITY = "vehicle_booking"
RECENT_LIMIT = 8

#  Hạng phạm vi — CHỈ để quyết định có hiện khối tổng hợp "toàn phạm vi" (Giám đốc)
#  hay không. Không lộ scope ra giao diện; việc lọc dữ liệu vẫn do `apply_scope` lo.
_SCOPE_RANK = {"own": 0, "assigned": 0, "proc": 1, "dept": 2, "company": 3, "all": 4}


def _top_scope_rank(prof: dict, entity: str) -> int:
    """Hạng phạm vi CAO NHẤT người dùng có quyền đọc trên entity (−1 nếu không có)."""
    best = -1
    for grant in prof.get("grants", []):
        perm = grant.get("perms", {}).get(entity)
        if perm and perm.get("read"):
            best = max(best, _SCOPE_RANK.get(perm.get("scope", "own"), 0))
    return best


def _month_starts(count: int = 12) -> list[datetime]:
    """Mốc đầu mỗi tháng cho `count` tháng gần nhất (cũ → mới)."""
    now = datetime.now()
    base_year, base_month = now.year, now.month
    starts: list[datetime] = []
    for offset in range(count - 1, -1, -1):
        total = (base_year * 12 + (base_month - 1)) - offset
        starts.append(datetime(total // 12, total % 12 + 1, 1))
    return starts


def _month_range(d_from: datetime, d_to: datetime) -> list[datetime]:
    """Mốc đầu-tháng phủ [d_from, d_to] (trần 36 cột cho khỏi phình)."""
    first = d_from.year * 12 + (d_from.month - 1)
    last = max(d_to.year * 12 + (d_to.month - 1), first)
    last = min(last, first + 35)
    return [datetime(t // 12, t % 12 + 1, 1) for t in range(first, last + 1)]


def _trend(scoped_query, starts: list[datetime]) -> list[dict]:
    """Số phiếu tạo theo THÁNG cho các mốc `starts` — đếm theo khoảng `created_at`
    (không dùng hàm ngày riêng của MySQL/SQLite nên chạy được cả hai)."""
    points: list[dict] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else None
        q = scoped_query.filter(VehicleBooking.created_at >= start)
        if end is not None:
            q = q.filter(VehicleBooking.created_at < end)
        points.append({"label": f"{start.month:02d}/{start.year}", "value": q.count()})
    return points


def _parse_day(value: str | None):
    """'yyyy-mm-dd' → datetime đầu ngày; None/rỗng/sai định dạng → None."""
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d")
    except ValueError:
        return None


def _apply_range(query, d_from, d_to):
    """Lọc theo KHOẢNG NGÀY TẠO [d_from, d_to] (bao trọn ngày kết thúc)."""
    if d_from is not None:
        query = query.filter(VehicleBooking.created_at >= d_from)
    if d_to is not None:
        query = query.filter(VehicleBooking.created_at < d_to + timedelta(days=1))
    return query


def build_overview(db: Session, user, date_from: str | None = None,
                   date_to: str | None = None) -> dict:
    """Số liệu tổng quan Đặt xe cho người đang đăng nhập.

    `date_from`/`date_to` (yyyy-mm-dd) lọc theo KHOẢNG NGÀY TẠO cho khối tổng hợp
    `company` (theo tháng · loại · trạng thái · bộ phận). Các khối hàng-chờ khác
    (mine/approve/dispatch/driver) là việc hiện tại nên KHÔNG lọc theo ngày. Giao
    diện mặc định truyền 30 ngày gần nhất; bỏ trống = tất cả."""
    prof = get_perm_profile(db, user)

    def can(action: str) -> bool:
        return bool(prof["perms_union"].get(ENTITY, {}).get(action))

    def scoped():
        query = db.query(VehicleBooking).filter(VehicleBooking.is_deleted == False)  # noqa: E712
        return apply_scope(query, VehicleBooking, ENTITY, user, prof)

    data: dict = {
        "can": {e: bool(prof["perms_union"].get(e, {}).get("read"))
                for e in ("vehicle_booking", "vehicle", "driver")},
    }
    if not can("read"):
        return data  # không đọc được phiếu thì không có khối nào

    # ── mine (người dùng): phiếu của tôi, mọi trạng thái ──────────────────────
    if can("create"):
        mine_q = scoped().filter(VehicleBooking.created_by == user.id)
        by_status = dict(
            mine_q.with_entities(VehicleBooking.status, func.count(VehicleBooking.id))
            .group_by(VehicleBooking.status).all())
        recent = mine_q.order_by(VehicleBooking.id.desc()).limit(RECENT_LIMIT).all()
        data["mine"] = {
            "by_status": {int(k): int(v) for k, v in by_status.items()},
            "recent": service.serialize_bookings(db, recent),
        }

    # ── approve (người duyệt / TBP): chờ tôi duyệt ────────────────────────────
    if can("approve"):
        pend_q = scoped().filter(VehicleBooking.status == BK_PENDING)
        data["approve"] = {
            "pending": pend_q.count(),
            "items": service.serialize_bookings(
                db, pend_q.order_by(VehicleBooking.id.desc()).limit(RECENT_LIMIT).all()),
        }

    # ── dispatch (điều phối viên): chờ điều phối + KPI đội xe ──────────────────
    #  Điều phối viên có `write` phạm vi công ty/toàn hệ; TÀI XẾ cũng có `write`
    #  nhưng phạm vi `assigned` — chặn theo hạng phạm vi để tài xế không nhận nhầm
    #  khối điều phối (tài xế đã có khối `driver` riêng).
    if can("write") and _top_scope_rank(prof, ENTITY) >= _SCOPE_RANK["dept"]:
        base = scoped()
        to_dispatch = base.filter(VehicleBooking.status == BK_APPROVED)
        by_type = dict(
            base.with_entities(VehicleBooking.request_type, func.count(VehicleBooking.id))
            .group_by(VehicleBooking.request_type).all())
        distance_sum = base.with_entities(
            func.coalesce(func.sum(VehicleBooking.distance_km), 0)).scalar()
        cost_sum = base.with_entities(
            func.coalesce(func.sum(VehicleBooking.cost), 0)).scalar()
        data["dispatch"] = {
            "to_dispatch": to_dispatch.count(),
            "ongoing": base.filter(VehicleBooking.status == BK_DISPATCHED).count(),
            "completed": base.filter(VehicleBooking.status == BK_COMPLETED).count(),
            "distance_sum": float(distance_sum or 0),
            "cost_sum": int(cost_sum or 0),
            "by_type": {"car": int(by_type.get(TYPE_CAR, 0)),
                        "delivery": int(by_type.get(TYPE_DELIVERY, 0))},
            "queue": service.serialize_bookings(
                db, to_dispatch.order_by(VehicleBooking.id.desc()).limit(RECENT_LIMIT).all()),
        }

    # ── driver (tài xế): bảng chuyến được phân cho tôi ────────────────────────
    if service.my_driver_profile(db, user) is not None:
        trips_q = service.filter_my_trips(scoped(), db, user)
        by_drv = dict(
            trips_q.with_entities(VehicleBooking.driver_status, func.count(VehicleBooking.id))
            .group_by(VehicleBooking.driver_status).all())
        active = trips_q.filter(
            VehicleBooking.driver_status.in_([DRV_WAITING, DRV_ACCEPTED, DRV_ONGOING]))
        data["driver"] = {
            "waiting": int(by_drv.get(DRV_WAITING, 0)),
            "accepted": int(by_drv.get(DRV_ACCEPTED, 0)),
            "ongoing": int(by_drv.get(DRV_ONGOING, 0)),
            "completed": int(by_drv.get(DRV_COMPLETED, 0)),
            "trips": service.serialize_bookings(
                db, active.order_by(VehicleBooking.id.desc()).limit(RECENT_LIMIT).all()),
        }

    #  Khoảng ngày tạo áp cho các khối tổng hợp (mặc định 30 ngày; bỏ = tất cả).
    d_from, d_to = _parse_day(date_from), _parse_day(date_to)

    # ── fleet (điều phối viên / giám đốc — quyền `approve`): thống kê theo XE và
    #  theo TÀI XẾ trong khoảng ngày. Người đặt xe / tài xế (không có `approve`)
    #  không thấy hai bảng đội xe này.
    if can("approve"):
        ranged_fleet = _apply_range(scoped(), d_from, d_to)
        data["fleet"] = {
            "by_vehicle": _by_vehicle(db, ranged_fleet),
            "by_driver": _by_driver(db, ranged_fleet),
        }

    # ── company (giám đốc / phạm vi ≥ phòng): tổng hợp toàn phạm vi ────────────
    #  MỘT khoảng ngày tạo áp cho cả bốn biểu đồ (mặc định 30 ngày; bỏ = tất cả).
    if _top_scope_rank(prof, ENTITY) >= _SCOPE_RANK["dept"]:
        ranged = _apply_range(scoped(), d_from, d_to)
        st_rows = dict(
            ranged.with_entities(VehicleBooking.status, func.count(VehicleBooking.id))
            .group_by(VehicleBooking.status).all())
        type_rows = dict(
            ranged.with_entities(VehicleBooking.request_type, func.count(VehicleBooking.id))
            .group_by(VehicleBooking.request_type).all())
        starts = _month_range(d_from, d_to) if (d_from and d_to) else _month_starts(12)
        data["company"] = {
            "by_status": [
                {"key": int(k), "label": BOOKING_STATUS_LABELS.get(int(k), str(k)), "value": int(v)}
                for k, v in sorted(st_rows.items())],
            "by_type": {"car": int(type_rows.get(TYPE_CAR, 0)),
                        "delivery": int(type_rows.get(TYPE_DELIVERY, 0))},
            "by_company": _by_company(db, ranged),
            "trend": _trend(ranged, starts),
        }
    return data


def _by_company(db: Session, scoped_query) -> list[dict]:
    """Top CÔNG TY theo số phiếu (kèm tên công ty)."""
    from app.modules.company.model import Company

    rows = (scoped_query
            .with_entities(VehicleBooking.company_id, func.count(VehicleBooking.id))
            .group_by(VehicleBooking.company_id).all())
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


#  Chỉ đếm/cộng cho phiếu ĐÃ HOÀN THÀNH — 1 khi hoàn thành, 0 nếu chưa.
_DONE = case((VehicleBooking.status == BK_COMPLETED, 1), else_=0)


def _by_vehicle(db: Session, scoped_query) -> list[dict]:
    """Thống kê theo XE: số phiếu · hoàn tất · tổng km · tổng chi phí (top 20)."""
    from .model import Vehicle

    rows = (scoped_query
            .filter(VehicleBooking.assigned_vehicle_id.isnot(None),
                    VehicleBooking.assigned_vehicle_id != 0)
            .with_entities(
                VehicleBooking.assigned_vehicle_id,
                func.count(VehicleBooking.id),
                func.coalesce(func.sum(_DONE), 0),
                func.coalesce(func.sum(VehicleBooking.distance_km), 0),
                func.coalesce(func.sum(VehicleBooking.cost), 0))
            .group_by(VehicleBooking.assigned_vehicle_id).all())
    if not rows:
        return []
    veh = {v.id: v for v in db.query(Vehicle)
           .filter(Vehicle.id.in_([r[0] for r in rows])).all()}
    out = []
    for vid, total, done, dist, cost in rows:
        v = veh.get(vid)
        label = service._vehicle_label(v) if v else f"#{vid}"
        out.append({"id": int(vid), "label": label or f"#{vid}",
                    "total": int(total), "completed": int(done),
                    "distance_km": float(dist or 0), "cost": int(cost or 0)})
    out.sort(key=lambda x: x["total"], reverse=True)
    return out[:20]


def _by_driver(db: Session, scoped_query) -> list[dict]:
    """Thống kê theo TÀI XẾ: số phiếu · hoàn tất · tổng km (top 20)."""
    from .model import Driver

    rows = (scoped_query
            .filter(VehicleBooking.assigned_driver_id.isnot(None),
                    VehicleBooking.assigned_driver_id != 0)
            .with_entities(
                VehicleBooking.assigned_driver_id,
                func.count(VehicleBooking.id),
                func.coalesce(func.sum(_DONE), 0),
                func.coalesce(func.sum(VehicleBooking.distance_km), 0))
            .group_by(VehicleBooking.assigned_driver_id).all())
    if not rows:
        return []
    drv = {d.id: d for d in db.query(Driver)
           .filter(Driver.id.in_([r[0] for r in rows])).all()}
    out = []
    for did, total, done, dist in rows:
        d = drv.get(did)
        out.append({"id": int(did), "name": (d.name if d else f"#{did}"),
                    "total": int(total), "completed": int(done),
                    "distance_km": float(dist or 0)})
    out.sort(key=lambda x: x["total"], reverse=True)
    return out[:20]
