"""API Điểm cà phê — `/api/coffee/...`.

Gác hai trục như mọi module: `require(entity, action)` cho quyền hành động,
`apply_scope(...)` bó phạm vi; đọc lẻ theo id qua `get_scoped` (không `db.get`).
Bảng quyền: `doc/erp/diem-ca-phe/04-phan-quyen.md`.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import record as audit_record
from app.core.auth import get_current_user, get_perm_profile, require
from app.core.config import settings
from app.core.base_controller import apply_filters, pagination
from app.core.database import get_db
from app.core.response import success
from app.core.scoping import apply_scope, get_scoped
from app.modules.employee.model import Employee

from . import service
from .model import (ENUM_LABELS, CoffeeLedger, CoffeeLedgerType, CoffeeLevel,
                    CoffeeMember, CoffeeMemberStatus, CoffeePolicy, PosOrder,
                    PosOrderMatchStatus, PosSyncKind, PosSyncRun)
from .pos365_client import Pos365Disabled, Pos365Error, get_client
from .schema import (AdjustIn, CreatePartnerIn, MatchIn, MemberCreate,
                     MemberUpdate, PolicyIn, ResetExecuteIn, ResolveIn,
                     SelfOrderIn, SyncRunIn)

router = APIRouter(prefix="/api/coffee", tags=["coffee-point"])


# ── Meta (nhãn enum — giao diện KHÔNG gõ lại tiếng Việt) ────────────────────────

@router.get("/meta")
def get_meta(user=Depends(require("coffee_member", "read"))):
    def options(name: str) -> list[dict]:
        return [{"value": v, "label": lb} for v, lb in ENUM_LABELS[name].items()]
    return success({
        "levels": options("coffee_level"),
        "ledger_types": options("coffee_ledger_type"),
        "member_statuses": options("coffee_member_status"),
        "match_statuses": options("pos_order_match_status"),
        "sync_kinds": options("pos_sync_kind"),
    })


# ── Chính sách (A-01) ───────────────────────────────────────────────────────────

def _policy_locked(db: Session, p: CoffeePolicy) -> bool:
    """Dòng đã được một kỳ cấp dùng tới thì CHỈ ĐỌC — đổi mức = thêm dòng mới,
    để "mức của tháng trước" tra lại được (02 §2)."""
    period = service.period_of(p.effective_from)
    return (db.query(CoffeeLedger)
            .filter(CoffeeLedger.type == int(CoffeeLedgerType.GRANT),
                    CoffeeLedger.company_id == p.company_id,
                    CoffeeLedger.period >= period)
            .limit(1).count()) > 0


@router.get("/policies")
def list_policies(db: Session = Depends(get_db),
                  user=Depends(require("coffee_policy", "read"))):
    query = apply_scope(db.query(CoffeePolicy), CoffeePolicy, "coffee_policy",
                        user, get_perm_profile(db, user))
    rows = query.order_by(CoffeePolicy.level_code, CoffeePolicy.effective_from.desc()).all()
    return success({"items": [{
        "id": p.id, "company_id": p.company_id,
        "level_code": p.level_code, "level_label": p.level_label,
        "monthly_points": p.monthly_points, "effective_from": p.effective_from,
        "note": p.note, "locked": _policy_locked(db, p),
    } for p in rows]})


@router.post("/policies")
def create_policy(data: PolicyIn, db: Session = Depends(get_db),
                  user=Depends(require("coffee_policy", "create"))):
    if data.level_code not in [int(v) for v in CoffeeLevel]:
        raise HTTPException(400, "Cấp phúc lợi không hợp lệ")
    row = CoffeePolicy(**data.model_dump(), created_by=user.id, updated_by=user.id)
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Đã có dòng chính sách cho cấp này với cùng ngày hiệu lực")
    audit_record(db, user.id, "coffee_policy", row.id, "create",
                 f"Khai mức {data.monthly_points} điểm/kỳ cho cấp {row.level_label} "
                 f"từ {data.effective_from}")
    db.commit()
    return success({"id": row.id}, "Đã thêm dòng chính sách", 201)


@router.patch("/policies/{pid}")
def update_policy(pid: int, data: PolicyIn, db: Session = Depends(get_db),
                  user=Depends(require("coffee_policy", "write"))):
    row = get_scoped(db, CoffeePolicy, "coffee_policy", pid, user, get_perm_profile(db, user))
    if row is None:
        raise HTTPException(404, "Không tìm thấy dòng chính sách")
    if _policy_locked(db, row):
        raise HTTPException(400, "Dòng đã được kỳ cấp phát dùng tới — chỉ đọc. "
                                 "Đổi mức bằng cách THÊM dòng hiệu lực mới.")
    for k, v in data.model_dump().items():
        setattr(row, k, v)
    row.updated_by = user.id
    audit_record(db, user.id, "coffee_policy", row.id, "update", "Sửa dòng chính sách")
    db.commit()
    return success({"id": row.id}, "Đã cập nhật")


# ── Thành viên & ghép POS365 (B-01…B-04) ────────────────────────────────────────

@router.get("/members")
def list_members(request: Request, pg: dict = Depends(pagination),
                 db: Session = Depends(get_db),
                 user=Depends(require("coffee_member", "read"))):
    query = apply_filters(db.query(CoffeeMember), CoffeeMember, request,
                          service.MEMBER_FILTERABLE)
    query = apply_scope(query, CoffeeMember, "coffee_member", user,
                        get_perm_profile(db, user))
    total = query.count()
    rows = query.order_by(CoffeeMember.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total,
                    "items": [service.serialize_member(db, m) for m in rows]})


@router.post("/members")
def create_member(data: MemberCreate, db: Session = Depends(get_db),
                  user=Depends(require("coffee_member", "create"))):
    emp = db.get(Employee, data.employee_id)
    if emp is None:
        raise HTTPException(404, "Không tìm thấy nhân sự")
    if data.level_code not in [int(v) for v in CoffeeLevel]:
        raise HTTPException(400, "Cấp phúc lợi không hợp lệ")
    row = CoffeeMember(
        employee_id=data.employee_id, level_code=data.level_code,
        company_id=data.company_id or emp.company_id, note=data.note,
        created_by=user.id, updated_by=user.id,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Nhân sự đã thuộc chương trình điểm cà phê")
    audit_record(db, user.id, "coffee_member", row.id, "create",
                 f"Gán {emp.full_name} vào chương trình, cấp {row.level_label}")
    db.commit()
    return success(service.serialize_member(db, row), "Đã thêm thành viên", 201)


@router.patch("/members/{mid}")
def update_member(mid: int, data: MemberUpdate, db: Session = Depends(get_db),
                  user=Depends(require("coffee_member", "write"))):
    row = get_scoped(db, CoffeeMember, "coffee_member", mid, user, get_perm_profile(db, user))
    if row is None:
        raise HTTPException(404, "Không tìm thấy thành viên")
    notes = []
    if data.level_code is not None and data.level_code != row.level_code:
        if data.level_code not in [int(v) for v in CoffeeLevel]:
            raise HTTPException(400, "Cấp phúc lợi không hợp lệ")
        row.level_code = data.level_code
        notes.append(f"đổi cấp → {row.level_label}")
    if data.status is not None and data.status != row.status:
        if data.status == int(CoffeeMemberStatus.LEFT):
            #  A-05: nghỉ việc → thu hồi số dư về 0, có dòng sổ, rồi mới khóa.
            revoked = service.mark_member_left(db, row, actor_id=user.id)
            notes.append(f"khóa (nghỉ việc), thu hồi {revoked} điểm")
        else:
            row.status = data.status
            notes.append(f"trạng thái → {row.status_label}")
    if data.note is not None:
        row.note = data.note
    row.updated_by = user.id
    if notes:
        audit_record(db, user.id, "coffee_member", row.id, "update",
                     "Cập nhật thành viên: " + ", ".join(notes))
    db.commit()
    return success(service.serialize_member(db, row), "Đã cập nhật")


@router.get("/members/pos-search")
def pos_search(q: str = Query(min_length=3), db: Session = Depends(get_db),
               user=Depends(require("coffee_member", "write"))):
    """Tra khách bên POS365 (SĐT/tên) phục vụ ghép — proxy, đã lọc `Password`."""
    try:
        results = get_client().search_partners(q)
    except Pos365Disabled:
        raise HTTPException(400, "Kết nối POS365 đang tắt (POS365_HARD_OFF)")
    except Pos365Error as e:
        raise HTTPException(502, str(e))
    return success({"items": [{
        "pos_partner_id": p.get("Id"), "code": p.get("Code"), "name": p.get("Name"),
        "phone": p.get("Phone"), "point": p.get("Point"),
    } for p in results]})


@router.post("/members/{mid}/match")
def match_member(mid: int, data: MatchIn, db: Session = Depends(get_db),
                 user=Depends(require("coffee_member", "write"))):
    row = get_scoped(db, CoffeeMember, "coffee_member", mid, user, get_perm_profile(db, user))
    if row is None:
        raise HTTPException(404, "Không tìm thấy thành viên")
    #  Luật A3: KHÔNG ghi đè khóa ghép — muốn ghép lại phải gỡ trước (có audit).
    if row.pos_partner_id:
        raise HTTPException(400, "Thành viên đã ghép POS365 — gỡ ghép trước nếu muốn ghép lại")
    dup = (db.query(CoffeeMember)
           .filter(CoffeeMember.pos_partner_id == data.pos_partner_id).first())
    if dup:
        raise HTTPException(400, f"Khách POS365 này đã ghép với thành viên #{dup.id}")
    row.pos_partner_id = data.pos_partner_id
    row.pos_partner_code = data.pos_partner_code
    row.matched_by = user.id
    row.matched_at = service.now_str()
    row.updated_by = user.id
    audit_record(db, user.id, "coffee_member", row.id, "update",
                 f"Ghép POS365: khách {data.pos_partner_code or data.pos_partner_id}")
    db.commit()
    return success(service.serialize_member(db, row), "Đã ghép khách POS365")


@router.post("/members/{mid}/unmatch")
def unmatch_member(mid: int, db: Session = Depends(get_db),
                   user=Depends(require("coffee_member", "write"))):
    row = get_scoped(db, CoffeeMember, "coffee_member", mid, user, get_perm_profile(db, user))
    if row is None:
        raise HTTPException(404, "Không tìm thấy thành viên")
    old = row.pos_partner_code or row.pos_partner_id
    row.pos_partner_id = 0
    row.pos_partner_code = ""
    row.updated_by = user.id
    audit_record(db, user.id, "coffee_member", row.id, "update",
                 f"Gỡ ghép POS365 (trước đó: {old})")
    db.commit()
    return success(service.serialize_member(db, row), "Đã gỡ ghép")


@router.post("/members/{mid}/create-partner")
def create_partner(mid: int, data: CreatePartnerIn, db: Session = Depends(get_db),
                   user=Depends(require("coffee_member", "write"))):
    """B-03: tạo khách mới bên POS365 (mã = mã nhân viên) rồi tự ghép."""
    row = get_scoped(db, CoffeeMember, "coffee_member", mid, user, get_perm_profile(db, user))
    if row is None:
        raise HTTPException(404, "Không tìm thấy thành viên")
    if row.pos_partner_id:
        raise HTTPException(400, "Thành viên đã ghép POS365")
    emp = db.get(Employee, row.employee_id)
    try:
        created = get_client().create_partner(
            name=data.name or (emp.full_name if emp else ""),
            phone=data.phone or (emp.phone if emp else ""),
            code=emp.code if emp else "")
    except Pos365Disabled:
        raise HTTPException(400, "Kết nối POS365 đang tắt (POS365_HARD_OFF)")
    except Pos365Error as e:
        raise HTTPException(502, str(e))
    row.pos_partner_id = int(created.get("Id") or 0)
    row.pos_partner_code = str(created.get("Code") or "")
    row.matched_by = user.id
    row.matched_at = service.now_str()
    row.updated_by = user.id
    audit_record(db, user.id, "coffee_member", row.id, "update",
                 f"Tạo khách POS365 {row.pos_partner_code} và ghép")
    db.commit()
    return success(service.serialize_member(db, row), "Đã tạo khách POS365 và ghép")


# ── Ví của tôi (C-02) ───────────────────────────────────────────────────────────

@router.get("/my-wallet")
def my_wallet(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Ví của CHÍNH người gọi — chỉ cần đăng nhập, service tự lấy `employee_id`
    của người gọi; không nhận tham số id nên không có gì để vượt scope (04 §3)."""
    emp_id = getattr(user, "employee_id", 0) or 0
    member = (db.query(CoffeeMember).filter(CoffeeMember.employee_id == emp_id).first()
              if emp_id else None)
    if member is None:
        return success({"member": None, "balance": 0, "granted": 0, "spent": 0,
                        "items": []})
    period = service.current_period()
    rows = (db.query(CoffeeLedger)
            .filter(CoffeeLedger.employee_id == emp_id)
            .order_by(CoffeeLedger.id.desc()).limit(200).all())
    return success({
        "member": service.serialize_member(db, member, with_balance=False),
        "balance": service.balance_of(db, emp_id),
        **service.period_summary(db, emp_id, period),
        "period": period,
        "items": service.serialize_ledger_rows(db, rows),
    })


# ── Cấp phát kỳ: xem trước → CHỐT (A-03 + A-06 đã chốt: từng kỳ phải có duyệt) ──

@router.get("/reset/preview")
def reset_preview(period: str | None = Query(None, pattern=r"^\d{6}$"),
                  db: Session = Depends(get_db),
                  user=Depends(require("coffee_ledger", "approve"))):
    """Bảng DỰ KIẾN của kỳ: từng người thu bao nhiêu / cấp bao nhiêu — chưa ghi gì."""
    stats = service.run_monthly_reset(db, period, dry_run=True)
    emps = {e.id: e for e in db.query(Employee).filter(
        Employee.id.in_([r["employee_id"] for r in stats["preview"]] or [0])).all()}
    for row in stats["preview"]:
        emp = emps.get(row["employee_id"])
        row["employee_code"] = emp.code if emp else ""
        row["employee_name"] = emp.full_name if emp else ""
    return success(stats)


@router.post("/reset/execute")
def reset_execute(data: ResetExecuteIn, db: Session = Depends(get_db),
                  user=Depends(require("coffee_ledger", "approve"))):
    """CHỐT cấp phát kỳ — dòng grant mang `created_by` = người chốt (dấu vết duyệt).
    Idempotent nhờ `uniq_key`: chốt lại cùng kỳ không nhân đôi."""
    stats = service.run_monthly_reset(db, data.period, actor_id=user.id)
    audit_record(db, user.id, "coffee_ledger", 0, "approve",
                 f"Chốt cấp phát kỳ {data.period}: cấp {stats['granted']} người, "
                 f"thu cuối kỳ {stats['expired']} người"
                 + (f", {len(stats['no_policy'])} người chưa khai mức" if stats['no_policy'] else ""))
    db.commit()
    return success(stats, f"Đã chốt cấp phát kỳ {data.period}")


# ── Tự đặt nước (menu từ POS365, đơn đẩy sang quầy) ─────────────────────────────

@router.get("/menu")
def get_menu(user=Depends(get_current_user)):
    """Thực đơn đọc từ POS365 (tên/giá/ảnh theo dữ liệu quán đang bán)."""
    try:
        products = get_client().list_products(top=200)
    except Pos365Disabled:
        raise HTTPException(400, "Kết nối POS365 đang tắt (POS365_HARD_OFF)")
    except Pos365Error as e:
        raise HTTPException(502, str(e))
    items = []
    for p in products:
        if int(p.get("ProductType") or 0) != 1:
            continue
        images = p.get("ProductImages") or []
        image = next((i.get("ThumbnailUrl") or i.get("ImageURL")
                      for i in images if i.get("IsDefault")), None) \
            or (images[0].get("ThumbnailUrl") or images[0].get("ImageURL") if images else "")
        items.append({
            "product_id": p.get("Id"), "code": p.get("Code"), "name": p.get("Name"),
            "price": int(round(float(p.get("Price") or 0))),
            "category": (p.get("Category") or {}).get("Name") or "Khác",
            "image": image or "",
        })
    items.sort(key=lambda x: (x["category"], x["name"]))
    return success({"items": items})


@router.post("/self-order")
def create_self_order(data: SelfOrderIn, db: Session = Depends(get_db),
                      user=Depends(get_current_user)):
    """Nhân sự tự đặt: DEGO tạo đơn trên POS365 (trả trọn bằng tài khoản "Trừ
    điểm", gắn khách đã ghép) → quầy thấy đơn và pha → điểm trừ qua vòng kéo.

    Giá tra lại từ thực đơn POS365 ngay lúc đặt — KHÔNG tin giá client gửi.
    """
    emp_id = getattr(user, "employee_id", 0) or 0
    member = (db.query(CoffeeMember)
              .filter(CoffeeMember.employee_id == emp_id,
                      CoffeeMember.status == int(CoffeeMemberStatus.ACTIVE)).first()
              if emp_id else None)
    if member is None:
        raise HTTPException(400, "Bạn chưa thuộc chương trình điểm cà phê — liên hệ Nhân sự")
    if not member.pos_partner_id:
        raise HTTPException(400, "Hồ sơ của bạn chưa ghép với POS365 — liên hệ Nhân sự")

    client = get_client()
    try:
        products = {int(p.get("Id")): p for p in client.list_products(top=200)}
    except Pos365Disabled:
        raise HTTPException(400, "Kết nối POS365 đang tắt (POS365_HARD_OFF)")
    except Pos365Error as e:
        raise HTTPException(502, str(e))

    items, total = [], 0
    for line in data.items:
        p = products.get(line.product_id)
        if p is None:
            raise HTTPException(400, f"Món #{line.product_id} không còn trong thực đơn")
        price = int(round(float(p.get("Price") or 0)))
        total += price * line.quantity
        items.append({"ProductId": line.product_id, "Code": p.get("Code", ""),
                      "Name": p.get("Name", ""), "Price": price,
                      "Quantity": line.quantity})

    if not member.is_unlimited:
        balance = service.balance_of(db, emp_id)
        if balance < total:
            raise HTTPException(400, f"Không đủ điểm: cần {total:,} mà ví còn {balance:,}")

    emp = db.get(Employee, emp_id)
    note = f"DEGO tự đặt — {emp.full_name if emp else ''}"
    if data.note:
        note += f" — {data.note.strip()}"
    try:
        created = client.create_order(
            partner_id=member.pos_partner_id, items=items,
            account_id=settings.POS365_PAYMENT_ACCOUNT_ID, description=note)
    except Pos365Error as e:
        raise HTTPException(502, f"POS365 từ chối đơn: {e}")

    audit_record(db, user.id, "pos_order", 0, "create",
                 f"Tự đặt nước {created.get('Code')} — {total:,} điểm")
    db.commit()
    #  Kéo ngay một vòng để dòng tiêu hiện liền trong Ví (best-effort — không
    #  được thì 5 phút sau beat/nút chạy tay cũng kéo về).
    try:
        service.run_pull_orders(db, client, actor_id=user.id)
    except Exception:  # noqa: BLE001
        pass
    return success({"code": created.get("Code"), "pos_order_id": created.get("Id"),
                    "total": total,
                    "balance": None if member.is_unlimited
                    else service.balance_of(db, emp_id)},
                   f"Đã gửi đơn {created.get('Code')} sang quầy", 201)


# ── Sổ cái & điều chỉnh (C-03, A-07) ────────────────────────────────────────────

@router.get("/ledger")
def list_ledger(request: Request, pg: dict = Depends(pagination),
                db: Session = Depends(get_db),
                user=Depends(require("coffee_ledger", "read"))):
    query = apply_filters(db.query(CoffeeLedger), CoffeeLedger, request,
                          service.LEDGER_FILTERABLE)
    query = apply_scope(query, CoffeeLedger, "coffee_ledger", user,
                        get_perm_profile(db, user))
    total = query.count()
    rows = query.order_by(CoffeeLedger.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": service.serialize_ledger_rows(db, rows)})


@router.post("/ledger/adjust")
def adjust_ledger(data: AdjustIn, db: Session = Depends(get_db),
                  user=Depends(require("coffee_ledger", "write"))):
    member = (db.query(CoffeeMember)
              .filter(CoffeeMember.employee_id == data.employee_id).first())
    if member is None:
        raise HTTPException(404, "Nhân sự chưa thuộc chương trình điểm cà phê")
    try:
        row = service.append_ledger(
            db, company_id=member.company_id, employee_id=data.employee_id,
            period=service.current_period(), type_=CoffeeLedgerType.ADJUST,
            points=data.points, reason=data.reason, actor_id=user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    audit_record(db, user.id, "coffee_ledger", row.id if row else 0, "create",
                 f"Điều chỉnh {data.points:+d} điểm cho nhân sự #{data.employee_id} — "
                 f"Lý do: {data.reason}")
    db.commit()
    return success({"balance": service.balance_of(db, data.employee_id)},
                   "Đã ghi dòng điều chỉnh", 201)


# ── Tra cứu quầy (C-04) ─────────────────────────────────────────────────────────

@router.get("/lookup")
def counter_lookup(q: str = Query(min_length=3), db: Session = Depends(get_db),
                   user=Depends(require("coffee_member", "read"))):
    """Trả đúng {name, balance} — KHÔNG lịch sử, KHÔNG danh sách (04 §4.2):
    khớp đúng mã NV hoặc SĐT đầy đủ, đáp án tối đa MỘT người."""
    q = q.strip()
    emp = (db.query(Employee)
           .filter((Employee.code == q) | (Employee.phone == q)).first())
    if emp is None:
        return success({"found": False})
    member = (db.query(CoffeeMember)
              .filter(CoffeeMember.employee_id == emp.id,
                      CoffeeMember.status == int(CoffeeMemberStatus.ACTIVE)).first())
    if member is None:
        return success({"found": False})
    if member.is_unlimited:
        #  Chúa tể HĐQT: quầy không chặn, không cần biết số — sổ vẫn ghi tiêu.
        return success({"found": True, "name": emp.full_name, "unlimited": True})
    return success({"found": True, "name": emp.full_name,
                    "balance": service.balance_of(db, emp.id)})


# ── Đơn POS365 & đối soát (D-02, D-04) ──────────────────────────────────────────

@router.get("/pos-orders")
def list_pos_orders(request: Request, pg: dict = Depends(pagination),
                    db: Session = Depends(get_db),
                    user=Depends(require("pos_order", "read"))):
    query = apply_filters(db.query(PosOrder), PosOrder, request, service.ORDER_FILTERABLE)
    query = apply_scope(query, PosOrder, "pos_order", user, get_perm_profile(db, user))
    total = query.count()
    rows = query.order_by(PosOrder.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total,
                    "items": [service.serialize_pos_order(db, r) for r in rows]})


@router.post("/pos-orders/{oid}/resolve")
def resolve_pos_order(oid: int, data: ResolveIn, db: Session = Depends(get_db),
                      user=Depends(require("coffee_ledger", "write"))):
    row = db.query(PosOrder).filter(PosOrder.id == oid).first()
    if row is None:
        raise HTTPException(404, "Không tìm thấy đơn")
    if row.match_status != int(PosOrderMatchStatus.UNMATCHED):
        raise HTTPException(400, "Đơn không ở trạng thái chờ xử lý")
    try:
        service.resolve_order(db, row, employee_id=data.employee_id,
                              reason=data.reason, actor_id=user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    action = (f"Gán đơn {row.pos_code} cho nhân sự #{data.employee_id}"
              if data.employee_id else f"Bỏ qua đơn {row.pos_code} — Lý do: {data.reason}")
    audit_record(db, user.id, "pos_order", row.id, "update", action)
    db.commit()
    return success(service.serialize_pos_order(db, row), "Đã xử lý đơn")


# ── Màn Quản lý POS — chỉ ĐỌC từ POS365 (doc 09 §12) ────────────────────────────

@router.get("/pos-dashboard")
def pos_dashboard(days: int = Query(7, ge=1, le=31),
                  user=Depends(require("pos_order", "read"))):
    """Số liệu quầy đọc TRỰC TIẾP từ POS365 lúc mở màn: hôm nay + doanh thu theo
    ngày + đơn gần đây kèm phương thức. Không ghi gì, không đụng sổ."""
    client = get_client()
    try:
        accounts = client.list_accounts()
        orders = service.fetch_recent_orders(client, days=days)
    except Pos365Disabled:
        raise HTTPException(400, "Kết nối POS365 đang tắt (POS365_HARD_OFF) — "
                                 "màn này cần đọc trực tiếp từ cửa hàng")
    except Pos365Error as e:
        raise HTTPException(502, str(e))
    data = service.build_pos_dashboard(
        orders, accounts, settings.POS365_PAYMENT_ACCOUNT_ID, days=days)
    data["store_url"] = settings.POS365_BASE_URL
    return success(data)


# ── Đồng bộ: chạy tay + nhật ký (D-05) ──────────────────────────────────────────

@router.post("/sync/run")
def run_sync(data: SyncRunIn, db: Session = Depends(get_db),
             user=Depends(require("pos_order", "write"))):
    """Chạy đồng bộ NGAY trong request (không cần worker) — quán nhỏ, mỗi vòng
    vài giây. Kết quả là một dòng nhật ký như beat chạy."""
    from . import tasks
    runners = {
        int(PosSyncKind.PULL_ORDERS): lambda: tasks.pull_orders_task(actor_id=user.id),
        int(PosSyncKind.CHECK_VOIDS): lambda: tasks.check_voids_task(actor_id=user.id),
        int(PosSyncKind.MONTHLY_RESET): lambda: tasks.monthly_reset_task(
            period=data.period, actor_id=user.id),
        int(PosSyncKind.RECONCILE): lambda: tasks.reconcile_task(actor_id=user.id),
        int(PosSyncKind.MIRROR): lambda: tasks.mirror_balance_task(actor_id=user.id),
    }
    runner = runners.get(data.kind)
    if runner is None:
        raise HTTPException(400, "Loại đồng bộ không hợp lệ")
    result = runner()
    audit_record(db, user.id, "pos_order", 0, "update",
                 f"Chạy tay đồng bộ POS365 (kind={data.kind}) → {result.get('status')}")
    db.commit()
    return success(result, "Đã chạy đồng bộ")


@router.get("/sync/runs")
def list_sync_runs(pg: dict = Depends(pagination), db: Session = Depends(get_db),
                   user=Depends(require("pos_order", "read"))):
    query = db.query(PosSyncRun).order_by(PosSyncRun.id.desc())
    total = query.count()
    rows = query.offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [service.serialize_sync_run(r) for r in rows]})
