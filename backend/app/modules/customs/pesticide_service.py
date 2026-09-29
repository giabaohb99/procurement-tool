"""Danh mục thuốc BVTV — mục «Thuốc BVTV» của Tra cứu thị trường (29/09/2026).

Bảng `tab_customs_pesticide` có HAI người đọc:
  · màn tra cứu (danh sách + phạm vi sử dụng) — tệp này;
  · bộ gắn hoạt chất cho dòng hàng hải quan (`ingredient.load_tagger`) — đọc `trade_key` +
    `active_ingredient`. Vì vậy nạp lại danh mục xong phải `retag_all`, không thì dòng hàng
    cũ vẫn mang hoạt chất suy ra từ danh mục trước.
"""
from contextlib import contextmanager

from fastapi import HTTPException
from sqlalchemy import delete, false, func, insert, or_, select, text
from sqlalchemy.orm import Session

from app.core.audit import record

from . import banned_ingredient_match as banned_match
from .constants import PESTICIDE_STATUS_LABELS
from .ingredient import retag_all
from .model import CustomsPesticide, CustomsPesticideUse

#  Khóa SỬA danh mục thuốc (duoc-CR-490) — cũng là entity ghi vào nhật ký. Xem vẫn theo `customs_price`.
ENTITY = "customs_pesticide"
_CHUNK = 2000
_LOCK_NAME = "customs_pesticide_import"


@contextmanager
def _import_lock(db: Session):
    """Chặn HAI lượt nạp chạy cùng lúc — kể cả khác tiến trình uvicorn (khóa có tên của MySQL).

    Khóa giữ trên một kết nối RIÊNG: khóa của MySQL gắn với kết nối, mà kết nối của `db` được
    trả về pool ngay khi `retag_all` commit — giữ khóa ở đó là khóa trôi theo kết nối vào pool.
    SQLite (pytest) không có khóa có tên — bỏ qua.
    """
    bind = db.get_bind()
    if bind.dialect.name != "mysql":
        yield
        return
    with bind.connect() as conn:
        if conn.execute(text("SELECT GET_LOCK(:n, 0)"), {"n": _LOCK_NAME}).scalar() != 1:
            raise HTTPException(409, "Đang có người nạp danh mục thuốc BVTV — chờ xong rồi thử lại")
        try:
            yield
        finally:
            conn.execute(text("SELECT RELEASE_LOCK(:n)"), {"n": _LOCK_NAME})


def replace_catalog(db: Session, records: list[dict], user_id: int, filename: str) -> dict:
    """Thay các thuốc LẤY TỪ NGUỒN bằng `records` (đã đọc + kiểm ở `pesticide_reader`).

    Thuốc người dùng tự thêm trên màn (`is_manual`) được GIỮ nguyên (duoc-CR-490); thuốc từ nguồn
    đã sửa tay thì bị ghi đè theo nguồn — hộp nạp nói rõ điều này. Một giao dịch: xóa, chèn lại,
    gắn lại hoạt chất cho dòng hàng. Lỗi giữa chừng thì rollback — danh mục cũ còn nguyên.

    ⚠️ GIỮ NGUYÊN id của thuốc vẫn còn trong nguồn (khớp theo `source_id`) — duoc-CR-494: tệp đính
    kèm và nhật ký thao tác gắn theo id thuốc, cấp id mới mỗi lần nạp là mọi tệp mất chủ. Id cho
    thuốc MỚI luôn lớn hơn mọi id đã từng có, để id của thuốc vừa rơi khỏi nguồn không bao giờ bị
    cấp lại — tái dùng là thuốc mới «nhận» tệp của thuốc cũ. Thuốc rơi khỏi nguồn thì tệp của nó
    được dọn SAU khi giao dịch chính xong (dọn tệp chạm tới kho lưu trữ, không lùi được).
    """
    with _import_lock(db):
        try:
            old_ids = dict(db.query(CustomsPesticide.source_id, CustomsPesticide.id)
                           .filter(CustomsPesticide.is_manual.is_(False), CustomsPesticide.source_id != 0)
                           .all())
            old_sourced = {i for (i,) in db.query(CustomsPesticide.id)
                           .filter(CustomsPesticide.is_manual.is_(False))}
            next_id = (db.query(func.max(CustomsPesticide.id)).scalar() or 0) + 1
            sourced = select(CustomsPesticide.id).where(CustomsPesticide.is_manual.is_(False))
            db.execute(delete(CustomsPesticideUse).where(CustomsPesticideUse.pesticide_id.in_(sourced)))
            db.execute(delete(CustomsPesticide).where(CustomsPesticide.is_manual.is_(False)))
            kept = db.query(func.count(CustomsPesticide.id)).scalar() or 0
            #  Tự cấp id trong CÙNG giao dịch — nhờ vậy chèn theo LÔ thay vì bảy nghìn câu lẻ để lấy
            #  id. Bản chèn lẻ đo được đủ lâu để lượt nạp trên prod đụng trần 120 giây của nginx.
            parents, uses, reused = [], [], set()
            for rec in records:
                pid = old_ids.get(rec.get("source_id") or 0)
                if pid is None or pid in reused:   # thuốc mới, hoặc nguồn trùng mã
                    pid, next_id = next_id, next_id + 1
                reused.add(pid)
                parents.append({k: v for k, v in rec.items() if k != "uses"}
                               | {"id": pid, "is_manual": False,
                                  "created_by": user_id, "updated_by": user_id})
                uses.extend({"pesticide_id": pid, "sort_order": i, **u}
                            for i, u in enumerate(rec["uses"], start=1))
            for start in range(0, len(parents), _CHUNK):
                db.execute(insert(CustomsPesticide), parents[start:start + _CHUNK])
            for start in range(0, len(uses), _CHUNK):
                db.execute(insert(CustomsPesticideUse), uses[start:start + _CHUNK])
            db.flush()
            retag = retag_all(db)   # commit DUY NHẤT: xóa + chèn + gắn lại cùng đi hoặc cùng lùi
        except Exception:
            db.rollback()
            raise
    dropped = sorted(old_sourced - reused)
    if dropped:
        from app.modules.attachment.service import delete_attachments_for
        delete_attachments_for(db, [(ENTITY, i) for i in dropped])
    record(db, user_id, ENTITY, 0, "catalog_import",
           f"Nạp danh mục thuốc BVTV từ {filename}: {len(records)} thuốc, {len(uses)} dòng phạm vi"
           f"{f', giữ {kept} thuốc tự thêm' if kept else ''}")
    db.commit()
    return {"pesticides": len(records), "uses": len(uses), "kept_manual": kept,
            "dropped": len(dropped), "retag": retag}


def _filtered(db: Session, query, q: str, status: int | None, pest_group: str, sector: str,
              banned_ids: set[int] | None = None):
    if q.strip():
        like = f"%{q.strip()}%"
        query = query.filter(or_(CustomsPesticide.trade_name.ilike(like),
                                 CustomsPesticide.active_ingredient.ilike(like),
                                 CustomsPesticide.registrant.ilike(like),
                                 CustomsPesticide.registration_no.ilike(like)))
    if status is not None:
        query = query.filter(CustomsPesticide.status == status)
    if pest_group:
        query = query.filter(CustomsPesticide.pest_group == pest_group)
    if sector:
        query = query.filter(CustomsPesticide.sector == sector)
    if banned_ids is not None:
        query = query.filter(CustomsPesticide.id.in_(banned_ids) if banned_ids else false())
    return query


def _banned_ids(db: Session, matcher: "banned_match.BannedIngredientMatcher", banned_only: bool,
                banned_regulation_id: int | None) -> set[int] | None:
    """Lọc «có hoạt chất cấm» (mọi hoạt chất, hoặc đúng một dòng TT 75) → tập id thuốc; `None` = không lọc."""
    if not banned_only and banned_regulation_id is None:
        return None
    index = banned_match.build_index(db, matcher)
    if banned_regulation_id is not None:
        return index.get(banned_regulation_id, set())
    return set().union(*index.values())


def _out(p: CustomsPesticide, use_count: int = 0, banned: list | None = None) -> dict:
    return {"id": p.id, "source_id": p.source_id, "trade_name": p.trade_name,
            "active_ingredient": p.active_ingredient, "concentration": p.concentration,
            "pest_group": p.pest_group, "sector": p.sector, "registrant": p.registrant,
            "registration_no": p.registration_no, "registered_on": p.registered_on,
            "expires_on": p.expires_on, "status": p.status,
            "status_label": PESTICIDE_STATUS_LABELS.get(p.status, ""),   # IntEnum băm như int
            "toxicity": p.toxicity, "resistance": p.resistance, "source_url": p.source_url,
            "summary": p.summary or "",
            "use_count": use_count, "is_manual": bool(p.is_manual),
            #  Hoạt chất trong danh sách CẤM (TT 75/2025) mà thuốc này chứa — khớp theo tên, tham khảo.
            "banned": [banned_match.banned_out(r) for r in (banned or [])]}


def list_pesticides(db: Session, q: str, status: int | None, pest_group: str, sector: str,
                    offset: int, limit: int, banned_only: bool = False,
                    banned_regulation_id: int | None = None) -> tuple[int, list[dict]]:
    matcher = banned_match.load_matcher(db)
    banned_ids = _banned_ids(db, matcher, banned_only, banned_regulation_id)
    total = _filtered(db, db.query(func.count(CustomsPesticide.id)), q, status, pest_group,
                      sector, banned_ids).scalar() or 0
    rows = (_filtered(db, db.query(CustomsPesticide), q, status, pest_group, sector, banned_ids)
            .order_by(CustomsPesticide.trade_name, CustomsPesticide.id)
            .offset(offset).limit(limit).all())
    #  Số dòng phạm vi của CẢ TRANG trong một câu — không đếm trong vòng lặp (N+1).
    counts = dict(db.query(CustomsPesticideUse.pesticide_id, func.count(CustomsPesticideUse.id))
                  .filter(CustomsPesticideUse.pesticide_id.in_([p.id for p in rows] or [0]))
                  .group_by(CustomsPesticideUse.pesticide_id).all())
    return total, [_out(p, counts.get(p.id, 0), matcher.match(p.active_ingredient)) for p in rows]


def get_pesticide(db: Session, pesticide_id: int) -> dict:
    p = db.get(CustomsPesticide, pesticide_id)
    if not p:
        raise HTTPException(404, "Không tìm thấy thuốc BVTV")
    uses = (db.query(CustomsPesticideUse).filter(CustomsPesticideUse.pesticide_id == p.id)
            .order_by(CustomsPesticideUse.sort_order, CustomsPesticideUse.id).all())
    out = _out(p, len(uses), banned_match.load_matcher(db).match(p.active_ingredient))
    out["uses"] = [{"id": u.id, "crop": u.crop, "pest": u.pest, "dosage": u.dosage,
                    "pre_harvest_interval": u.pre_harvest_interval, "usage": u.usage}
                   for u in uses]
    return out


def options(db: Session) -> dict:
    """Giá trị cho ô lọc + số đếm, và lần nạp gần nhất (để màn nói danh mục cũ tới đâu)."""
    def counted(col):
        return [{"value": v, "count": n} for v, n in
                db.query(col, func.count(CustomsPesticide.id)).filter(col != "")
                .group_by(col).order_by(func.count(CustomsPesticide.id).desc()).all()]

    statuses = dict(db.query(CustomsPesticide.status, func.count(CustomsPesticide.id))
                    .group_by(CustomsPesticide.status).all())
    matcher = banned_match.load_matcher(db)
    banned_index = banned_match.build_index(db, matcher)
    return {
        "total": sum(statuses.values()),
        "last_loaded_at": db.query(func.max(CustomsPesticide.updated_at)).scalar(),
        "statuses": [{"value": int(code), "label": label, "count": statuses.get(int(code), 0)}
                     for code, label in PESTICIDE_STATUS_LABELS.items() if label],
        "pest_groups": counted(CustomsPesticide.pest_group),
        "sectors": counted(CustomsPesticide.sector),
        #  `banned_rules` = số hoạt chất cấm đang dùng để đối chiếu: 0 nghĩa là CHƯA nạp danh sách
        #  cấm, khác hẳn «đối chiếu rồi, không thuốc nào dính» (`banned_count` = 0).
        #  Thuốc tự thêm trên màn — nạp lại danh mục GIỮ chúng (hộp nạp nói số này).
        "manual_count": db.query(func.count(CustomsPesticide.id))
                          .filter(CustomsPesticide.is_manual.is_(True)).scalar() or 0,
        "banned_rules": len({r.id for regs in matcher.by_key.values() for r in regs}),
        "banned_count": len(set().union(*banned_index.values())),
    }
