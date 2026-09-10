"""Nghiệp vụ Điểm cà phê — sổ cái, reset kỳ, xử lý đơn POS365.

Hai luật cứng của tệp này (xem `doc/erp/diem-ca-phe/02-bang-du-lieu.md`):

1. **`append_ledger` là ĐƯỜNG GHI SỔ DUY NHẤT.** Controller và task đều gọi nó; chỉ
   nó biết luật `uniq_key` và `reason` bắt buộc. Không chỗ nào `db.add(CoffeeLedger)`.
2. **Số dư = SUM(points).** Không cột cache, không UPDATE dòng cũ.
"""
import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.employee.model import Employee

from .model import (CoffeeLedger, CoffeeLedgerType, CoffeeMember,
                    CoffeeMemberStatus, CoffeePolicy, PosOrder,
                    PosOrderMatchStatus, PosSyncKind, PosSyncRun, PosSyncStatus)

log = logging.getLogger("app.coffee_point")

#  Cột cho `apply_filters` ở controller — whitelist, đừng mở rộng tùy tiện.
LEDGER_FILTERABLE = ["employee_id", "period", "type", "company_id"]
MEMBER_FILTERABLE = ["level_code", "status", "company_id"]
ORDER_FILTERABLE = ["match_status", "is_voided", "employee_id"]


# ── Thời gian & kỳ ──────────────────────────────────────────────────────────────

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def vn_time_str(iso: str) -> str:
    """Chuỗi ISO của POS365 (UTC, đuôi Z) → "YYYY-MM-DD HH:MM:SS" giờ VN.

    Cộng 7h là quan trọng ở mép ngày/kỳ: đơn 17:30 UTC ngày 31 là 00:30 ngày 1 giờ
    VN — thuộc KỲ MỚI. Chuỗi không parse được thì trả nguyên 19 ký tự đầu (đừng ném
    lỗi giữa vòng kéo vì một dòng dữ liệu xấu — dòng đó vẫn lưu được raw_json).
    """
    if not iso:
        return ""
    try:
        s = iso.strip()
        utc = s.endswith("Z")
        s = s.rstrip("Z")
        dt = datetime.fromisoformat(s[:26])  # cắt phần thập phân dài quá microsecond
        if utc:
            dt += timedelta(hours=7)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return iso[:19]


def period_of(date_str: str) -> str:
    """"YYYY-MM-DD..." → "YYYYMM"."""
    return date_str[:7].replace("-", "") if date_str else current_period()


def current_period() -> str:
    return datetime.now().strftime("%Y%m")


# ── Sổ cái ──────────────────────────────────────────────────────────────────────

def _uniq_key(type_: int, employee_id: int, period: str, pos_order_id: int) -> str | None:
    """Khóa idempotent theo loại dòng — bảng tra ở `02-bang-du-lieu.md` §4."""
    t = CoffeeLedgerType(type_)
    if t == CoffeeLedgerType.GRANT:
        return f"G-{employee_id}-{period}"
    if t == CoffeeLedgerType.EXPIRE:
        return f"E-{employee_id}-{period}"
    if t == CoffeeLedgerType.SPEND:
        return f"S-{pos_order_id}"
    if t == CoffeeLedgerType.REFUND:
        return f"R-{pos_order_id}"
    return None  # ADJUST / REVOKE: cho nhiều dòng — dấu vết là reason + created_by


def append_ledger(db: Session, *, company_id: int, employee_id: int, period: str,
                  type_: int, points: int, pos_order_id: int = 0, reason: str = "",
                  actor_id: int = 0) -> CoffeeLedger | None:
    """Đường ghi sổ duy nhất. Trả None khi dòng ĐÃ tồn tại (trùng `uniq_key`) —
    với người gọi đó là "bỏ qua im lặng", đúng nghĩa idempotent.

    `ADJUST` bắt buộc có lý do — không có đường đổi số dư nào không để lại dấu vết.
    """
    if type_ == CoffeeLedgerType.ADJUST and not (reason or "").strip():
        raise ValueError("Điều chỉnh tay bắt buộc có lý do")
    row = CoffeeLedger(
        company_id=company_id, employee_id=employee_id, period=period,
        type=int(type_), points=int(points), pos_order_id=pos_order_id,
        reason=(reason or "").strip(),
        uniq_key=_uniq_key(type_, employee_id, period, pos_order_id),
        created_by=actor_id, updated_by=actor_id,
    )
    try:
        #  Savepoint: trùng khóa chỉ hủy dòng này, không hủy transaction ngoài.
        with db.begin_nested():
            db.add(row)
            db.flush()
    except IntegrityError:
        return None
    return row


def balance_of(db: Session, employee_id: int) -> int:
    val = (db.query(func.coalesce(func.sum(CoffeeLedger.points), 0))
           .filter(CoffeeLedger.employee_id == employee_id).scalar())
    return int(val or 0)


def period_summary(db: Session, employee_id: int, period: str) -> dict:
    """Được cấp / đã tiêu trong một kỳ — cho màn Ví của tôi."""
    rows = (db.query(CoffeeLedger.type, func.coalesce(func.sum(CoffeeLedger.points), 0))
            .filter(CoffeeLedger.employee_id == employee_id, CoffeeLedger.period == period)
            .group_by(CoffeeLedger.type).all())
    by_type = {int(t): int(v) for t, v in rows}
    spent = -(by_type.get(int(CoffeeLedgerType.SPEND), 0)
              + by_type.get(int(CoffeeLedgerType.REFUND), 0))
    return {
        "granted": by_type.get(int(CoffeeLedgerType.GRANT), 0),
        "spent": max(spent, 0),
    }


# ── Chính sách & reset kỳ ───────────────────────────────────────────────────────

def policy_points(db: Session, company_id: int, level_code: int, period: str) -> int | None:
    """Mức của một cấp cho một kỳ = dòng có `effective_from` lớn nhất ≤ ngày 1 của kỳ.
    Không có dòng nào → None (cấp chưa khai mức — lỗi cấu hình, phải nổi lên).

    Dòng khai `company_id = 0` = "áp MỌI pháp nhân" — dòng riêng của pháp nhân
    (nếu có) thắng dòng chung; quán một pháp nhân thì khai hết ở 0 cho gọn."""
    first_day = f"{period[:4]}-{period[4:6]}-01"
    row = (db.query(CoffeePolicy)
           .filter(CoffeePolicy.company_id.in_([company_id, 0]),
                   CoffeePolicy.level_code == level_code,
                   CoffeePolicy.effective_from <= first_day)
           .order_by(CoffeePolicy.company_id.desc(),
                     CoffeePolicy.effective_from.desc())
           .first())
    return int(row.monthly_points) if row else None


def run_monthly_reset(db: Session, period: str | None = None, prev_period: str | None = None,
                      actor_id: int = 0, dry_run: bool = False) -> dict:
    """A-03: với từng thành viên ACTIVE ghi cặp `EXPIRE` (thu hết dư kỳ cũ) +
    `GRANT` (mức của cấp). Idempotent nhờ `uniq_key` — chạy lại cùng kỳ vô hại.

    **A-06 ĐÃ CHỐT 08/09/2026: cấp phát từng kỳ PHẢI CÓ NGƯỜI DUYỆT.** Đường ghi
    thật chỉ còn endpoint `POST /api/coffee/reset/execute` (quyền
    `coffee_ledger.approve`, `created_by` của dòng grant = người chốt); task beat
    ngày 1 chỉ chạy `dry_run` + bắn chuông nhắc. `dry_run=True` trả bảng DỰ KIẾN
    (từng người: thu bao nhiêu, cấp bao nhiêu) và KHÔNG ghi một dòng nào.

    Cấp VÔ HẠN (`UNLIMITED_LEVELS`) bỏ qua trọn: không cấp, không thu — dòng tiêu
    của họ vẫn ghi như thường.

    Commit TỪNG NGƯỜI: đứt giữa chừng thì người đã xong không lặp, người chưa xong
    chạy lại là tiếp. Dư ÂM cũng expire về 0 — khoản âm đã nằm trên màn đối soát từ
    lúc phát sinh (C-05), kỳ mới bắt đầu sạch.
    """
    from .model import UNLIMITED_LEVELS

    period = period or current_period()
    if prev_period is None:
        first = datetime.strptime(period, "%Y%m").replace(day=1)
        prev_period = (first - timedelta(days=1)).strftime("%Y%m")

    stats = {"granted": 0, "expired": 0, "skipped": 0, "no_policy": [],
             "period": period, "preview": []}
    members = (db.query(CoffeeMember)
               .filter(CoffeeMember.status == int(CoffeeMemberStatus.ACTIVE)).all())
    for m in members:
        if m.level_code in UNLIMITED_LEVELS:
            continue
        points = policy_points(db, m.company_id, m.level_code, period)
        if points is None:
            #  Cấp chưa khai mức là lỗi CẤU HÌNH — đếm để nổi lên cảnh báo, không cấp mò.
            stats["no_policy"].append(m.employee_id)
            continue
        if dry_run:
            du = balance_of(db, m.employee_id)
            da_cap = bool(db.query(CoffeeLedger)
                          .filter(CoffeeLedger.uniq_key == f"G-{m.employee_id}-{period}")
                          .first())
            stats["preview"].append({
                "employee_id": m.employee_id, "level_code": m.level_code,
                "level_label": m.level_label, "current_balance": du,
                "expire": -du if not da_cap else 0,
                "grant": points if not da_cap else 0,
                "already_granted": da_cap,
            })
            continue
        #  Đã có dòng GRANT của kỳ này = người này ĐÃ reset xong — bỏ qua TRỌN BỘ.
        #  Không được để nhánh EXPIRE chạy lẻ: lần đầu số dư 0 thì không có dòng
        #  expire chiếm khóa, chạy lại sẽ expire luôn số vừa cấp (bug bắt được ở
        #  test `test_reset_ky_hai_lan_khong_nhan_doi`). Còn ca đứt giữa chừng
        #  (expire xong, grant chưa) thì rơi xuống dưới: expire trùng khóa tự bỏ
        #  qua, grant chạy tiếp — vẫn đúng.
        if (db.query(CoffeeLedger)
                .filter(CoffeeLedger.uniq_key == f"G-{m.employee_id}-{period}")
                .first()):
            stats["skipped"] += 1
            continue
        du = balance_of(db, m.employee_id)
        if du != 0:
            row = append_ledger(db, company_id=m.company_id, employee_id=m.employee_id,
                                period=prev_period, type_=CoffeeLedgerType.EXPIRE,
                                points=-du, reason=f"Thu số dư cuối kỳ {prev_period}",
                                actor_id=actor_id)
            if row:
                stats["expired"] += 1
        row = append_ledger(db, company_id=m.company_id, employee_id=m.employee_id,
                            period=period, type_=CoffeeLedgerType.GRANT, points=points,
                            reason=f"Cấp điểm kỳ {period}", actor_id=actor_id)
        if row:
            stats["granted"] += 1
        else:
            stats["skipped"] += 1
        db.commit()
    return stats


def mark_member_left(db: Session, member: CoffeeMember, actor_id: int = 0,
                     reason: str = "Nghỉ việc") -> int:
    """A-05: thu hồi toàn bộ số dư (dòng `REVOKE`) + khóa thành viên.

    Không thu hồi là người đã nghỉ vẫn quẹt được — lỗ tiền thật (N5 của `09` §7).
    Trả về số điểm đã thu.
    """
    du = balance_of(db, member.employee_id)
    if du != 0:
        append_ledger(db, company_id=member.company_id, employee_id=member.employee_id,
                      period=current_period(), type_=CoffeeLedgerType.REVOKE,
                      points=-du, reason=reason, actor_id=actor_id)
    member.status = int(CoffeeMemberStatus.LEFT)
    member.updated_by = actor_id
    db.flush()
    return du


# ── Đơn hàng POS365 ─────────────────────────────────────────────────────────────

def extract_points_paid(order: dict, account_id: int) -> int:
    """Phần tiền trả bằng tài khoản "Trừ điểm" trên một đơn.

    Đơn nhiều phương thức: `MoreAttributes` là CHUỖI JSON chứa
    `PaymentMethods: [{AccountId, Value}]` (spec §5.3). Đơn một phương thức có thể
    chỉ mang `AccountId` trên chính đơn — ⚠️POC P1 chốt hình dạng thật; viết phòng
    cả hai, dữ liệu xấu thì trả 0 chứ không ném lỗi giữa vòng kéo.
    """
    if not account_id:
        return 0
    more = order.get("MoreAttributes")
    if more:
        try:
            payload = json.loads(more) if isinstance(more, str) else more
            methods = payload.get("PaymentMethods") or []
            total = sum(float(m.get("Value") or 0) for m in methods
                        if m.get("AccountId") == account_id)
            if total:
                return int(round(total))
        except (ValueError, TypeError, AttributeError):
            log.warning("MoreAttributes không đọc được ở đơn %s", order.get("Id"))
    if order.get("AccountId") == account_id:
        return int(round(float(order.get("TotalPayment") or order.get("Total") or 0)))
    return 0


def upsert_pos_order(db: Session, order: dict, points_paid: int, actor_id: int = 0) -> tuple[PosOrder, bool]:
    """Ghi/đọc bản sao đơn theo `pos_order_id` (UNIQUE — kéo trùng vô hại).
    Trả (row, created)."""
    oid = int(order.get("Id") or 0)
    row = db.query(PosOrder).filter(PosOrder.pos_order_id == oid).first()
    if row:
        return row, False
    partner = order.get("Partner") or {}
    pos_partner_id = int(order.get("PartnerId") or partner.get("Id") or 0)
    row = PosOrder(
        pos_order_id=oid,
        pos_code=str(order.get("Code") or ""),
        purchase_date=vn_time_str(order.get("PurchaseDate") or ""),
        pos_partner_id=pos_partner_id,
        total=float(order.get("Total") or 0),
        points_paid=points_paid,
        pos_status=int(order.get("Status") or 0),
        raw_json=json.dumps(order, ensure_ascii=False)[:60000],
        synced_at=now_str(),
        created_by=actor_id, updated_by=actor_id,
    )
    db.add(row)
    db.flush()
    return row, True


def match_and_spend(db: Session, row: PosOrder, actor_id: int = 0) -> bool:
    """Khớp đơn với nhân sự qua khóa ghép rồi ghi dòng tiêu. Không khớp được thì
    UNMATCHED — nằm hàng chờ D-02 cho người xử lý, hệ KHÔNG đoán."""
    member = None
    if row.pos_partner_id:
        member = (db.query(CoffeeMember)
                  .filter(CoffeeMember.pos_partner_id == row.pos_partner_id).first())
    if member is None:
        row.match_status = int(PosOrderMatchStatus.UNMATCHED)
        return False
    row.employee_id = member.employee_id
    row.company_id = member.company_id
    row.match_status = int(PosOrderMatchStatus.MATCHED)
    append_ledger(db, company_id=member.company_id, employee_id=member.employee_id,
                  period=period_of(row.purchase_date), type_=CoffeeLedgerType.SPEND,
                  points=-row.points_paid, pos_order_id=row.pos_order_id,
                  reason=f"Tiêu tại quầy — đơn {row.pos_code}", actor_id=actor_id)
    return True


def resolve_order(db: Session, row: PosOrder, *, employee_id: int = 0,
                  reason: str = "", actor_id: int = 0) -> PosOrder:
    """Xử lý đơn chưa khớp: gán người (sinh dòng tiêu) hoặc bỏ qua có lý do."""
    if employee_id:
        member = (db.query(CoffeeMember)
                  .filter(CoffeeMember.employee_id == employee_id).first())
        if member is None:
            raise ValueError("Nhân sự chưa thuộc chương trình điểm cà phê")
        row.employee_id = member.employee_id
        row.company_id = member.company_id
        row.match_status = int(PosOrderMatchStatus.MATCHED)
        row.resolve_note = (reason or "").strip()
        append_ledger(db, company_id=member.company_id, employee_id=member.employee_id,
                      period=period_of(row.purchase_date), type_=CoffeeLedgerType.SPEND,
                      points=-row.points_paid, pos_order_id=row.pos_order_id,
                      reason=f"Gán tay đơn {row.pos_code}", actor_id=actor_id)
    else:
        if not (reason or "").strip():
            raise ValueError("Bỏ qua đơn phải có lý do")
        row.match_status = int(PosOrderMatchStatus.IGNORED)
        row.resolve_note = reason.strip()
    row.updated_by = actor_id
    db.flush()
    return row


# ── Ba vòng đồng bộ (gọi từ tasks.py; client mock được ở test) ──────────────────

def _pull_cutoff(db: Session) -> str:
    """Mốc kéo tăng dần: `cursor_to` của lần PULL SUCCESS gần nhất, lùi 10 phút đè
    mép; không có thì đầu ngày hôm qua. Cursor chỉ tiến khi SUCCESS — POS365 sập
    thì chu kỳ sau tự kéo bù."""
    last = (db.query(PosSyncRun)
            .filter(PosSyncRun.kind == int(PosSyncKind.PULL_ORDERS),
                    PosSyncRun.status == int(PosSyncStatus.SUCCESS),
                    PosSyncRun.cursor_to != "")
            .order_by(PosSyncRun.id.desc()).first())
    if last:
        try:
            dt = datetime.strptime(last.cursor_to, "%Y-%m-%d %H:%M:%S")
            return (dt - timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")


def run_pull_orders(db: Session, client, actor_id: int = 0, page_size: int = 50,
                    max_pages: int = 10) -> dict:
    """D-01: kéo đơn mới, lọc phương thức "Trừ điểm", ghi bản sao + dòng tiêu.

    Danh sách POS365 mới nhất trước (theo spec mẫu); dừng khi cả trang đã cũ hơn
    mốc hoặc hết `max_pages` (chặn kéo vô hạn khi dữ liệu bất thường).
    """
    account_id = settings.POS365_PAYMENT_ACCOUNT_ID
    cutoff = _pull_cutoff(db)
    started = now_str()
    stats = {"fetched": 0, "written": 0, "skipped": 0,
             "cursor_from": cutoff, "cursor_to": started}
    for page in range(max_pages):
        data = client.list_orders(top=page_size, skip=page * page_size)
        results = data.get("results") or []
        if not results:
            break
        all_older = True
        for order in results:
            stats["fetched"] += 1
            pdate = vn_time_str(order.get("PurchaseDate") or "")
            if pdate >= cutoff:
                all_older = False
            else:
                continue
            points = extract_points_paid(order, account_id)
            if points <= 0:
                continue  # đơn khách vãng lai / không trả bằng điểm
            row, created = upsert_pos_order(db, order, points, actor_id)
            if not created:
                stats["skipped"] += 1
                continue
            #  Đơn ĐÃ void trước cả lần kéo đầu: ghi bản sao làm chứng cứ nhưng
            #  KHÔNG sinh dòng tiêu — khỏi đẻ cặp spend/refund vô nghĩa.
            if row.pos_status != POS_STATUS_ACTIVE:
                row.is_voided = 1
                stats["written"] += 1
                continue
            match_and_spend(db, row, actor_id)
            stats["written"] += 1
        db.commit()
        if all_older or len(results) < page_size:
            break
    return stats


#  Trạng thái "đơn còn hiệu lực" theo spec mẫu là 2; đơn void mang giá trị khác —
#  ⚠️POC P4 chốt con số thật, sửa MỘT chỗ này.
POS_STATUS_ACTIVE = 2


def run_check_voids(db: Session, client, actor_id: int = 0, days: int = 7) -> dict:
    """D-03: đơn đã trừ điểm mà bị void ở quầy → hoàn đúng một lần (`uniq_key R-`)."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
    rows = (db.query(PosOrder)
            .filter(PosOrder.match_status == int(PosOrderMatchStatus.MATCHED),
                    PosOrder.is_voided == 0,
                    PosOrder.purchase_date >= since).all())
    stats = {"fetched": len(rows), "written": 0, "skipped": 0}
    for row in rows:
        fresh = client.get_order(row.pos_order_id)
        if fresh is None:
            continue
        status = int(fresh.get("Status") or 0)
        row.pos_status = status
        if status == POS_STATUS_ACTIVE:
            continue
        row.is_voided = 1
        refund = append_ledger(
            db, company_id=row.company_id, employee_id=row.employee_id,
            period=period_of(row.purchase_date), type_=CoffeeLedgerType.REFUND,
            points=row.points_paid, pos_order_id=row.pos_order_id,
            reason=f"Hoàn điểm — đơn {row.pos_code} bị hủy", actor_id=actor_id)
        if refund:
            stats["written"] += 1
        db.commit()
    return stats


def run_reconcile(db: Session, days: int = 3) -> dict:
    """D-04: so tổng tiêu trong SỔ ↔ tổng `points_paid` của bản sao đơn theo ngày.

    Lệch chỉ LÊN BÁO CÁO (detail của sync_run — màn đối soát đọc), KHÔNG tự sửa
    (luật số 3 của `09` §2). Người xử lý bấm từng dòng sinh `ADJUST` có lý do.
    """
    mismatches = []
    for d in range(days):
        day = (datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d")
        #  Phía "POS365": tổng điểm trên bản sao đơn đã khớp, chưa void, của ngày đó.
        pos_sum = int((db.query(func.coalesce(func.sum(PosOrder.points_paid), 0))
                       .filter(PosOrder.purchase_date.like(f"{day}%"),
                               PosOrder.match_status == int(PosOrderMatchStatus.MATCHED),
                               PosOrder.is_voided == 0).scalar()) or 0)
        #  Phía SỔ: -SUM(SPEND) - SUM(REFUND) của các dòng gắn đơn ngày đó.
        order_ids = [r.pos_order_id for r in
                     db.query(PosOrder.pos_order_id)
                     .filter(PosOrder.purchase_date.like(f"{day}%")).all()]
        ledger_sum = 0
        if order_ids:
            val = (db.query(func.coalesce(func.sum(CoffeeLedger.points), 0))
                   .filter(CoffeeLedger.pos_order_id.in_(order_ids),
                           CoffeeLedger.type.in_([int(CoffeeLedgerType.SPEND),
                                                  int(CoffeeLedgerType.REFUND)]))
                   .scalar())
            ledger_sum = -int(val or 0)
        #  Đơn void đã hoàn: pos_sum loại nó ra và ledger SPEND+REFUND triệt tiêu → khớp.
        if pos_sum != ledger_sum:
            mismatches.append({"day": day, "pos": pos_sum, "ledger": ledger_sum,
                               "diff": pos_sum - ledger_sum})
    unmatched = (db.query(PosOrder)
                 .filter(PosOrder.match_status == int(PosOrderMatchStatus.UNMATCHED))
                 .count())
    return {"mismatches": mismatches, "unmatched": unmatched}


def run_mirror_balance(db: Session, client) -> dict:
    """D-07 (tùy chọn — chỉ chạy khi POC P5 xác nhận `PartnerSave` ghi được).
    CHỈ hiển thị: không bao giờ đọc ngược `Point` từ POS365 về sổ."""
    members = (db.query(CoffeeMember)
               .filter(CoffeeMember.status == int(CoffeeMemberStatus.ACTIVE),
                       CoffeeMember.pos_partner_id != 0).all())
    stats = {"fetched": len(members), "written": 0, "skipped": 0}
    for m in members:
        du = balance_of(db, m.employee_id)
        client.update_partner({"Id": m.pos_partner_id, "Type": 1, "Point": max(du, 0)})
        stats["written"] += 1
    return stats


# ── Màn Quản lý POS (chỉ-đọc, doc 09 §12) ───────────────────────────────────────

def fetch_recent_orders(client, days: int = 7, page_size: int = 100,
                        max_pages: int = 5) -> list[dict]:
    """Kéo đơn của `days` ngày gần nhất (mới nhất trước, cắt mốc ở client — POS365
    không lọc thời gian server-side, xem ghi chú `list_orders`)."""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
    out: list[dict] = []
    for page in range(max_pages):
        data = client.list_orders(top=page_size, skip=page * page_size)
        results = data.get("results") or []
        if not results:
            break
        stop = False
        for order in results:
            if vn_time_str(order.get("PurchaseDate") or "") < cutoff:
                stop = True
                continue
            out.append(order)
        if stop or len(results) < page_size:
            break
    return out


def build_pos_dashboard(orders: list[dict], accounts: list[dict],
                        account_id: int, days: int = 7) -> dict:
    """Gom số cho màn Quản lý POS từ đơn thô — hàm THUẦN để test được.

    Đơn void (Status != 2) không tính doanh thu, đếm riêng. Phương thức đọc từ
    `AccountId` top-level (POC 08/09): None = tiền mặt, = tài khoản "Trừ điểm"
    = trừ điểm, còn lại = tài khoản khác (tra tên qua AccountList).
    """
    acc_names = {int(a.get("Id") or 0): str(a.get("Name") or "") for a in accounts}

    def method_label(order: dict) -> str:
        aid = order.get("AccountId")
        if not aid:
            return "Tiền mặt"
        if int(aid) == account_id:
            return "Trừ điểm"
        return acc_names.get(int(aid), f"Tài khoản #{aid}")

    today = datetime.now().strftime("%Y-%m-%d")
    day_labels = [(datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d")
                  for d in range(days - 1, -1, -1)]
    by_day = {d: 0 for d in day_labels}
    stats = {"orders": 0, "revenue": 0, "cash": 0, "account": 0, "points": 0,
             "voided": 0}
    recent = []
    for order in orders:
        pdate = vn_time_str(order.get("PurchaseDate") or "")
        day = pdate[:10]
        total = int(round(float(order.get("Total") or 0)))
        voided = int(order.get("Status") or 0) != POS_STATUS_ACTIVE
        aid = order.get("AccountId")
        if len(recent) < 15:
            recent.append({
                "pos_order_id": order.get("Id"), "code": order.get("Code"),
                "time": pdate, "total": total, "method": method_label(order),
                "is_points": bool(aid) and int(aid) == account_id,
                "is_voided": voided,
                "partner_name": (order.get("Partner") or {}).get("Name") or "",
            })
        if voided:
            if day == today:
                stats["voided"] += 1
            continue
        if day in by_day:
            by_day[day] += total
        if day == today:
            stats["orders"] += 1
            stats["revenue"] += total
            if not aid:
                stats["cash"] += total
            elif int(aid) == account_id:
                stats["points"] += total
            else:
                stats["account"] += total
    return {
        "today": stats,
        "by_day": [{"label": f"{d[8:10]}/{d[5:7]}", "value": by_day[d]}
                   for d in day_labels],
        "recent": recent,
    }


# ── Serialize ───────────────────────────────────────────────────────────────────

def _emp_map(db: Session, ids: set[int]) -> dict[int, Employee]:
    if not ids:
        return {}
    rows = db.query(Employee).filter(Employee.id.in_(list(ids))).all()
    return {e.id: e for e in rows}


def serialize_ledger_rows(db: Session, rows: list[CoffeeLedger]) -> list[dict]:
    emps = _emp_map(db, {r.employee_id for r in rows})
    orders = {}
    oids = {r.pos_order_id for r in rows if r.pos_order_id}
    if oids:
        orders = {o.pos_order_id: o for o in
                  db.query(PosOrder).filter(PosOrder.pos_order_id.in_(list(oids))).all()}
    out = []
    for r in rows:
        emp = emps.get(r.employee_id)
        order = orders.get(r.pos_order_id)
        out.append({
            "id": r.id, "employee_id": r.employee_id,
            "employee_code": emp.code if emp else "",
            "employee_name": emp.full_name if emp else "",
            "period": r.period, "type": r.type, "type_label": r.type_label,
            "points": r.points, "reason": r.reason,
            "pos_order_id": r.pos_order_id,
            "pos_code": order.pos_code if order else "",
            "created_at": str(r.created_at or ""), "created_by": r.created_by,
        })
    return out


def serialize_member(db: Session, m: CoffeeMember, with_balance: bool = True) -> dict:
    emp = db.get(Employee, m.employee_id)
    return {
        "id": m.id, "employee_id": m.employee_id,
        "employee_code": emp.code if emp else "",
        "employee_name": emp.full_name if emp else "",
        "department_name": (emp.department_name or "") if emp else "",
        "company_id": m.company_id,
        "level_code": m.level_code, "level_label": m.level_label,
        "status": m.status, "status_label": m.status_label,
        "pos_partner_id": m.pos_partner_id, "pos_partner_code": m.pos_partner_code,
        "matched_at": m.matched_at,
        "unlimited": m.is_unlimited,
        "balance": balance_of(db, m.employee_id) if with_balance else None,
    }


def serialize_pos_order(db: Session, row: PosOrder) -> dict:
    emp = db.get(Employee, row.employee_id) if row.employee_id else None
    return {
        "id": row.id, "pos_order_id": row.pos_order_id, "pos_code": row.pos_code,
        "purchase_date": row.purchase_date,
        "pos_partner_id": row.pos_partner_id,
        "employee_id": row.employee_id,
        "employee_name": emp.full_name if emp else "",
        "total": float(row.total or 0), "points_paid": row.points_paid,
        "match_status": row.match_status, "match_status_label": row.match_status_label,
        "is_voided": row.is_voided, "resolve_note": row.resolve_note,
        "synced_at": row.synced_at,
    }


def serialize_sync_run(r: PosSyncRun) -> dict:
    return {
        "id": r.id, "kind": r.kind, "kind_label": r.kind_label,
        "status": r.status, "status_label": r.status_label,
        "started_at": r.started_at, "finished_at": r.finished_at,
        "cursor_from": r.cursor_from, "cursor_to": r.cursor_to,
        "fetched": r.fetched, "written": r.written, "skipped": r.skipped,
        "error": r.error, "detail": r.detail, "created_by": r.created_by,
    }
