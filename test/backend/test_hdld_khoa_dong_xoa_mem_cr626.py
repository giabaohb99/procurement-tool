"""
test_hdld_khoa_dong_xoa_mem_cr626.py — chốt khóa dòng của HĐLĐ phải tính cả XÓA MỀM (duoc-CR-626).

Lỗi tìm ra khi rà mất dữ liệu 19/10/2026: «Ký» chạy đua với «Xóa». Người A qua chốt phạm vi
(dòng còn sống), người B xóa mềm và commit trước, A chờ khóa xong nạp lại dòng — giờ đã
`is_deleted = 1` — rồi chuyển sang ĐÃ KÝ. Kết quả là một HĐ đã ký nhưng ẩn khỏi mọi màn,
trong khi chốt xóa nhân sự vẫn đếm nó → hồ sơ người đó không bao giờ xóa được.

Dựng lại khe hở bằng cách cho chốt phạm vi trả về dòng (như lúc A đọc), còn trong DB dòng
đã bị xóa mềm (như sau khi B commit).
"""
from datetime import date

import pytest
from fastapi import HTTPException

from app.modules.labor_contract import access
from app.modules.labor_contract.model import LaborContract


def _contract(db, *, deleted: bool) -> LaborContract:
    row = LaborContract(code="HDLD-CR625", employee_id=1, contract_type=1,
                        start_date=date(2026, 1, 1))
    db.add(row)
    db.commit()
    if deleted:
        row.is_deleted = True
        db.commit()
    return row


def test_lock_rejects_row_soft_deleted_while_waiting(db, monkeypatch):
    row = _contract(db, deleted=True)
    #  Lúc A đọc, dòng còn sống → chốt phạm vi cho qua.
    monkeypatch.setattr(access, "get_scoped", lambda *a, **k: row)

    with pytest.raises(HTTPException) as exc:
        access.get_or_404_scoped(db, LaborContract, "labor_contract", row.id, None, {}, "write",
                                 lock=True)
    assert exc.value.status_code == 404


def test_lock_still_returns_live_row(db, monkeypatch):
    row = _contract(db, deleted=False)
    monkeypatch.setattr(access, "get_scoped", lambda *a, **k: row)

    got = access.get_or_404_scoped(db, LaborContract, "labor_contract", row.id, None, {}, "write",
                                   lock=True)
    assert got.id == row.id
