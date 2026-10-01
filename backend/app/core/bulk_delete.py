"""Xóa NHIỀU phiếu một lần — bao-CR-547 (đại ca chốt 01/10/2026: CHỈ phiếu Nháp).

Bốn chứng từ YCBG · YCMH · ĐMH · YCTT có đường `DELETE /api/<chứng từ>?ids=…`. Trước CR này mỗi
đường lặp xóa từng phiếu, gặp phiếu không xóa được thì DỪNG — nhưng các phiếu đã xóa trước đó
vẫn mất, người bấm chỉ thấy một câu lỗi và không biết lô đã bị xóa dở. Nay kiểm CẢ LÔ trước:
có phiếu nào không phải Nháp thì KHÔNG xóa phiếu nào, báo đúng mã các phiếu vướng.

Luật xóa TỪNG phiếu giữ nguyên ở service của từng phân hệ (YCMH/YCBG còn cho Bị trả lại, Đã từ
chối; ĐMH cho Bị từ chối) — đại ca chốt chỉ siết đường xóa nhiều, riêng YCTT siết cả xóa từng phiếu.
"""
from fastapi import HTTPException

DRAFT = "draft"
_LISTED_CODES = 10


def ensure_all_draft(rows, label: str) -> None:
    """Mọi phiếu trong lô phải đang Nháp — không thì 400, không xóa phiếu nào."""
    blocked = [r for r in rows if (getattr(r, "status", "") or "") != DRAFT]
    if not blocked:
        return
    codes = [getattr(r, "code", "") or f"#{r.id}" for r in blocked]
    listed = ", ".join(codes[:_LISTED_CODES])
    more = f" và {len(codes) - _LISTED_CODES} phiếu khác" if len(codes) > _LISTED_CODES else ""
    raise HTTPException(
        400,
        f"Chỉ xóa nhiều được {label} ở trạng thái Nháp — chưa xóa phiếu nào. "
        f"Bỏ chọn {len(codes)} phiếu không phải Nháp: {listed}{more}.")
