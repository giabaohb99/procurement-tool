"""Xóa THEO LÔ cho các vòng dọn hằng ngày (ai-CR-139, Agent 1 nhắc 09/10/2026).

Một câu `DELETE … WHERE created_at < …` chạm vài trăm nghìn dòng giữ khóa bảng (và nhật ký hoàn tác) suốt cả lượt: bot
đang ghi tin / sổ ý định vào đúng bảng đó thì đứng chờ. Nay lấy từng lô id (BATCH dòng), xóa theo id, commit từng lô —
mỗi lô khóa ngắn, lượt ghi khác chen vào được giữa hai lô. Có trần số lô để một lượt dọn không chạy vô hạn; còn sót thì
lượt hôm sau dọn tiếp.
"""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

BATCH = 5000
MAX_BATCHES = 200          # tối đa 1.000.000 dòng mỗi lượt


def delete_in_batches(db: Session, model, *conditions, batch: int = BATCH, max_batches: int = MAX_BATCHES) -> int:
    total = 0
    for _ in range(max_batches):
        ids = list(db.scalars(select(model.id).where(*conditions).order_by(model.id).limit(batch)))
        if not ids:
            break
        res = db.execute(delete(model).where(model.id.in_(ids)))
        db.commit()
        total += int(res.rowcount or 0)
        if len(ids) < batch:
            break
    return total
