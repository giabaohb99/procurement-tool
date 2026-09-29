"""Thêm / sửa / xóa MỘT thuốc BVTV trên màn (duoc-CR-490, 29/09/2026). Khóa `customs_pesticide`.

Hai điều phải nhớ khi đụng vào tệp này:
  · Thuốc THÊM trên màn mang `is_manual = True` — nạp lại danh mục giữ chúng. Thuốc LẤY TỪ NGUỒN
    thì sửa được, nhưng lần nạp sau ghi đè theo nguồn (hộp nạp nói điều đó với người dùng).
  · KHÔNG tự `retag_all` sau mỗi lần sửa: gắn lại hoạt chất quét mọi dòng hàng hải quan (~18 nghìn
    dòng trên prod), bắt người sửa một dấu chấm phải chờ cả lượt đó là vô lý. Tên thương mại /
    hoạt chất vừa sửa chỉ vào dòng hàng khi bấm «Gắn lại nhãn» ở mục Cấu hình, hoặc lần nạp sau.
"""
from fastapi import HTTPException
from sqlalchemy import delete, insert
from sqlalchemy.orm import Session

from app.core.audit import record
from app.modules.attachment.service import delete_attachments_for

from .model import CustomsPesticide, CustomsPesticideUse
from .pesticide_reader import trade_key
from .pesticide_schema import PesticideIn
from .pesticide_service import ENTITY, get_pesticide

_FIELDS = ("trade_name", "active_ingredient", "concentration", "pest_group", "sector", "registrant",
           "registration_no", "registered_on", "expires_on", "status", "toxicity", "resistance",
           "source_url", "summary")


def _get_or_404(db: Session, pesticide_id: int) -> CustomsPesticide:
    p = db.get(CustomsPesticide, pesticide_id)
    if not p:
        raise HTTPException(404, "Không tìm thấy thuốc BVTV")
    return p


def _write_uses(db: Session, pesticide_id: int, data: PesticideIn) -> None:
    db.execute(delete(CustomsPesticideUse).where(CustomsPesticideUse.pesticide_id == pesticide_id))
    rows = [{"pesticide_id": pesticide_id, "sort_order": i, **u.model_dump()}
            for i, u in enumerate(data.uses, start=1)]
    if rows:
        db.execute(insert(CustomsPesticideUse), rows)


def create_pesticide(db: Session, data: PesticideIn, user_id: int) -> dict:
    p = CustomsPesticide(**{f: getattr(data, f) for f in _FIELDS}, trade_key=trade_key(data.trade_name),
                         source_id=0, is_manual=True, created_by=user_id, updated_by=user_id)
    db.add(p)
    db.flush()
    _write_uses(db, p.id, data)
    record(db, user_id, ENTITY, p.id, "create", f"Thêm thuốc BVTV «{p.trade_name}»")
    db.commit()
    return get_pesticide(db, p.id)


def update_pesticide(db: Session, pesticide_id: int, data: PesticideIn, user_id: int) -> dict:
    p = _get_or_404(db, pesticide_id)
    changed = [f for f in _FIELDS if getattr(p, f) != getattr(data, f)]
    for f in _FIELDS:
        setattr(p, f, getattr(data, f))
    p.trade_key = trade_key(data.trade_name)
    p.updated_by = user_id
    _write_uses(db, p.id, data)
    fields = f" ({', '.join(changed)})" if changed else ""
    record(db, user_id, ENTITY, p.id, "update",
           f"Sửa thuốc BVTV «{p.trade_name}»{fields}, {len(data.uses)} dòng phạm vi")
    db.commit()
    return get_pesticide(db, p.id)


def delete_pesticide(db: Session, pesticide_id: int, user_id: int) -> None:
    p = _get_or_404(db, pesticide_id)
    name = p.trade_name
    db.execute(delete(CustomsPesticideUse).where(CustomsPesticideUse.pesticide_id == p.id))
    db.delete(p)
    record(db, user_id, ENTITY, pesticide_id, "delete", f"Xóa thuốc BVTV «{name}»")
    db.commit()
    #  Tệp đính kèm của thuốc (duoc-CR-494) — dọn SAU khi xóa xong: dọn chạm tới kho lưu trữ,
    #  không lùi được, nên không để nó chạy trước một lượt xóa có thể còn hỏng.
    delete_attachments_for(db, [(ENTITY, pesticide_id)])
