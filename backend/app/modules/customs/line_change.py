"""Bản chụp dòng hàng trước khi ghi đè / xóa, và hoàn tác lô theo bản chụp — bao-CR-608.

Đại ca 07/10/2026: tệp nạp có cột «ID» (ghi đè đúng dòng đó) và «Thao tác = xóa» (xóa dòng đó);
màn hình có thêm sửa / xóa từng dòng. Cả hai đều đụng vào dòng ĐÃ CÓ, nên trước khi đụng phải
chụp lại đủ mọi cột vào `tab_customs_line_change` (`CustomsLineChange`).

Luật hoàn tác một lô (`revert_batch_lines`), làm theo thứ tự NGƯỢC thời gian:
  (a) xóa dòng THÊM MỚI của lô (`batch_id` = lô — dòng bị ghi đè giữ `batch_id` CŨ nên không dính);
  (b) dựng lại dòng bị xóa từ bản chụp, chèn lại ĐÚNG id cũ;
  (c) trả dòng bị ghi đè về bản chụp.
Dòng bị lô sau / người sửa tay đụng tiếp sau lô này thì VẪN trả về bản chụp của lô này, kèm
cảnh báo trong kết quả — người hoàn tác biết phần sửa sau đã mất.

⚠️ Ghi bằng lệnh hàng loạt (`insert` / `update` theo khóa chính), không `db.add` từng dòng:
một lô nạp có thể ghi đè hàng nghìn dòng (xem chú thích đầu `importer.py`).
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, Numeric, insert, update
from sqlalchemy.orm import Session

from .constants import INSERT_CHUNK, CustomsLineChangeAction, CustomsLineChangeSource
from .model import CustomsLine, CustomsLineChange

_CHUNK = 1000
#  Cảnh báo dài quá thì câu trả về vô dụng — liệt kê tối đa từng này dòng, còn lại đếm.
_MAX_WARNINGS_SHOWN = 20


def _columns():
    return CustomsLine.__table__.columns


def snapshot_of(line: CustomsLine) -> dict:
    """Mọi cột của dòng → dict an toàn cho JSON (ngày ISO, số thập phân dạng chuỗi để không lệch)."""
    out = {}
    for c in _columns():
        v = getattr(line, c.key)
        if isinstance(v, date):
            v = v.isoformat()
        elif isinstance(v, Decimal):
            v = str(v)
        elif isinstance(v, bool):
            v = bool(v)
        out[c.key] = v
    return out


def values_from_snapshot(snap: dict) -> dict:
    """Bản chụp → giá trị đúng kiểu cột để chèn / cập nhật lại (kèm `id`)."""
    out = {}
    for c in _columns():
        if c.key not in snap:
            continue
        v = snap[c.key]
        if v is not None and isinstance(c.type, Date):
            v = date.fromisoformat(v)
        elif v is not None and isinstance(c.type, Numeric):
            v = Decimal(str(v))
        elif v is not None and isinstance(c.type, Boolean):
            v = bool(v)
        out[c.key] = v
    return out


def load_lines_by_id(db: Session, ids) -> dict[int, CustomsLine]:
    """Tra các dòng theo id, từng cụm 1000 (`IN`), KHÔNG truy vấn từng dòng. Đối tượng đọc xong
    được bỏ khỏi phiên — chỉ dùng để chụp / so, ghi thì đi lệnh hàng loạt."""
    wanted = sorted({int(i) for i in ids if i})
    out: dict[int, CustomsLine] = {}
    for i in range(0, len(wanted), _CHUNK):
        for line in db.query(CustomsLine).filter(CustomsLine.id.in_(wanted[i:i + _CHUNK])):
            out[line.id] = line
    for line in out.values():
        db.expunge(line)
    return out


def record_snapshots(db: Session, lines: list[CustomsLine], action: CustomsLineChangeAction,
                     source: CustomsLineChangeSource, batch_id: int, user_id: int) -> None:
    """Chụp các dòng TRƯỚC khi ghi đè / xóa — gọi trước lệnh ghi, cùng giao dịch."""
    payload = [{"batch_id": batch_id, "line_id": ln.id, "action": int(action), "source": int(source),
                "snapshot": snapshot_of(ln), "created_by": user_id} for ln in lines]
    for i in range(0, len(payload), INSERT_CHUNK):
        db.execute(insert(CustomsLineChange), payload[i:i + INSERT_CHUNK])


def delete_lines(db: Session, ids: list[int]) -> int:
    done = 0
    for i in range(0, len(ids), _CHUNK):
        done += (db.query(CustomsLine).filter(CustomsLine.id.in_(ids[i:i + _CHUNK]))
                 .delete(synchronize_session=False))
    return done


def has_snapshots(db: Session, batch_id: int) -> bool:
    return db.query(CustomsLineChange.id).filter(CustomsLineChange.batch_id == batch_id).first() is not None


def _later_touches(db: Session, batch_id: int, line_ids: list[int], after_change_id: int) -> dict[int, str]:
    """Dòng nào bị lô KHÁC / người sửa tay đụng SAU lô này → id dòng → câu «lô #m» / «sửa tay»."""
    out: dict[int, str] = {}
    for i in range(0, len(line_ids), _CHUNK):
        rows = (db.query(CustomsLineChange.line_id, CustomsLineChange.batch_id, CustomsLineChange.source)
                .filter(CustomsLineChange.line_id.in_(line_ids[i:i + _CHUNK]),
                        CustomsLineChange.id > after_change_id, CustomsLineChange.batch_id != batch_id)
                .order_by(CustomsLineChange.id).all())
        for line_id, other_batch, source in rows:
            out.setdefault(line_id, "sửa / xóa tay" if source == CustomsLineChangeSource.MANUAL
                           else f"lô #{other_batch}")
    return out


def revert_batch_lines(db: Session, batch_id: int) -> dict:
    """Hoàn tác MỘT lô: xóa dòng thêm mới, dựng lại dòng đã xóa, trả dòng ghi đè về bản chụp.

    → {"deleted", "restored", "reinserted", "warnings"}. Không commit (người gọi commit).
    """
    changes = (db.query(CustomsLineChange).filter(CustomsLineChange.batch_id == batch_id)
               .order_by(CustomsLineChange.id.desc()).all())
    warnings: list[str] = []
    first_change = min((c.id for c in changes), default=0)

    #  (a) dòng THÊM MỚI của lô. Dòng do lô này thêm mà sau đó bị sửa tiếp thì vẫn xóa, kèm cảnh báo.
    added_ids = [i for (i,) in db.query(CustomsLine.id).filter(CustomsLine.batch_id == batch_id)]
    for line_id, who in _later_touches(db, batch_id, added_ids, 0).items():
        warnings.append(f"Dòng ID {line_id} do lô này thêm đã bị {who} sửa sau đó — vẫn xóa")
    deleted = delete_lines(db, added_ids)

    #  (b) + (c) theo thứ tự ngược thời gian.
    touched = sorted({c.line_id for c in changes})
    later = _later_touches(db, batch_id, touched, first_change)
    current = {i for (i,) in _ids_present(db, touched)}
    restored = reinserted = 0
    to_update: list[dict] = []
    to_insert: list[dict] = []
    for c in changes:
        values = values_from_snapshot(c.snapshot or {})
        values["id"] = c.line_id
        if c.line_id in later:
            warnings.append(f"Dòng ID {c.line_id} đã bị {later[c.line_id]} đụng sau lô này — vẫn trả về "
                            "bản trước lô, phần sửa sau đó mất")
        if c.line_id in current:
            to_update.append(values)
            restored += 1
        else:
            to_insert.append(values)
            current.add(c.line_id)
            reinserted += 1
            if c.action == CustomsLineChangeAction.UPDATE:
                warnings.append(f"Dòng ID {c.line_id} bị ghi đè ở lô này rồi bị xóa sau đó — đã dựng lại")
    for i in range(0, len(to_update), INSERT_CHUNK):
        db.execute(update(CustomsLine), to_update[i:i + INSERT_CHUNK])
    for i in range(0, len(to_insert), INSERT_CHUNK):
        db.execute(insert(CustomsLine), to_insert[i:i + INSERT_CHUNK])
    return {"deleted": deleted, "restored": restored, "reinserted": reinserted, "warnings": warnings}


def _ids_present(db: Session, ids: list[int]):
    for i in range(0, len(ids), _CHUNK):
        yield from db.query(CustomsLine.id).filter(CustomsLine.id.in_(ids[i:i + _CHUNK])).all()


def summarize_warnings(warnings: list[str]) -> str:
    if not warnings:
        return ""
    shown = warnings[:_MAX_WARNINGS_SHOWN]
    more = len(warnings) - len(shown)
    return " Cảnh báo: " + "; ".join(shown) + (f"; và {more} cảnh báo khác" if more > 0 else "") + "."
