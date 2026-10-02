"""Nạp CẬP NHẬT danh mục Thuốc BVTV từ một tệp xuất THEO TRANG (C1, review 02/10/2026).

Khác `pesticide_service.replace_catalog` (THAY TOÀN BỘ): tệp theo trang không đại diện cho cả
danh mục, nên nạp lại CHỈ sửa đúng những thuốc có trong tệp — khớp theo `source_id`, GIỮ
NGUYÊN id DB (không mất tệp đính kèm) — thêm mới thuốc chưa từng có, KHÔNG xóa gì khác. Thuốc
thủ công và thuốc nguồn trùng `source_id` (dữ liệu nhiễm) không bao giờ lọt vào `records` — bộ
đọc đã lọc theo `id <= 0` ở `pesticide_reader._read_xlsx` (C2) — nên không cần xử lý riêng ở đây.

Gắn lại hoạt chất cho dòng hàng hải quan: chạy LẠI TOÀN BỘ `retag_all` như `replace_catalog`,
KHÔNG tách riêng phần vừa đổi. Bộ tagger suy từ khóa từ TOÀN BỘ `active_ingredient` của danh
mục (`ingredient.derive_aliases`), nên vài thuốc đổi vẫn có thể làm sinh/mất một từ khóa suy ra
dùng CHUNG cho dòng hàng của thuốc KHÁC — tách theo phần đổi có thể bỏ sót dòng; chạy lại toàn bộ
là lựa chọn AN TOÀN hơn, đổi lấy một lượt gắn lại chậm hơn (đã đo ~2s/7000 thuốc ở
`replace_catalog`, chấp nhận được cho một lượt nạp trang).
"""
from sqlalchemy import delete, func, insert, update
from sqlalchemy.orm import Session

from app.core.audit import record

from .ingredient import retag_all
from .model import CustomsPesticide, CustomsPesticideUse
from .pesticide_service import ENTITY, _import_lock


def merge_catalog(db: Session, records: list[dict], user_id: int, filename: str) -> dict:
    """Cập nhật/thêm đúng các thuốc có trong `records` — xem docstring đầu tệp.

    Dùng CHUNG khóa nạp `pesticide_service._import_lock` với `replace_catalog`: hai lượt nạp
    (thay toàn bộ / chỉ cập nhật) không được chạy song song, cả hai đều sửa `tab_customs_
    pesticide` + gọi `retag_all`.
    """
    with _import_lock(db):
        try:
            existing = dict(db.query(CustomsPesticide.source_id, CustomsPesticide.id)
                            .filter(CustomsPesticide.is_manual.is_(False),
                                    CustomsPesticide.source_id != 0).all())
            next_id = (db.query(func.max(CustomsPesticide.id)).scalar() or 0) + 1
            used_pids: set[int] = set()
            updated = added = total_uses = 0
            for rec in records:
                uses = rec.pop("uses")
                pid = existing.get(rec.get("source_id") or 0)
                if pid is None or pid in used_pids:
                    #  Chưa từng có (hoặc `source_id` trùng MỘT bản khác TRONG CHÍNH tệp này) —
                    #  id MỚI, không bao giờ cấp lại id của thuốc nào khác (cùng công thức với
                    #  `replace_catalog`).
                    pid, next_id = next_id, next_id + 1
                    db.execute(insert(CustomsPesticide), [{**rec, "id": pid, "is_manual": False,
                               "created_by": user_id, "updated_by": user_id}])
                    added += 1
                else:
                    db.execute(update(CustomsPesticide).where(CustomsPesticide.id == pid)
                               .values(**rec, updated_by=user_id))
                    db.execute(delete(CustomsPesticideUse)
                               .where(CustomsPesticideUse.pesticide_id == pid))
                    updated += 1
                used_pids.add(pid)
                if uses:
                    db.execute(insert(CustomsPesticideUse),
                              [{"pesticide_id": pid, "sort_order": i, **u}
                               for i, u in enumerate(uses, start=1)])
                total_uses += len(uses)
            db.flush()
            retag = retag_all(db)   # commit DUY NHẤT — xem docstring đầu tệp
        except Exception:
            db.rollback()
            raise
    kept_manual = (db.query(func.count(CustomsPesticide.id))
                  .filter(CustomsPesticide.is_manual.is_(True)).scalar() or 0)
    record(db, user_id, ENTITY, 0, "catalog_merge",
           f"Cập nhật danh mục thuốc BVTV từ {filename}: {updated} thuốc sửa, {added} thuốc mới")
    db.commit()
    return {"pesticides": updated + added, "uses": total_uses, "kept_manual": kept_manual,
            "dropped": 0, "retag": retag, "mode": "merge", "updated": updated, "added": added}
