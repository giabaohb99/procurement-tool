"""bao-CR-717 — một dòng tồn cho mỗi bộ (công ty, kho, mã): ràng buộc duy nhất ở CSDL + tính lại tồn chịu được chạy đồng thời.

PCN-KHO-08: trước chỉ có ba chỉ mục rời, hai lượt lưu ĐMH / nhận hàng cùng lúc có thể sinh hai dòng tồn. Nay:
- `tab_inventory` có UniqueConstraint (model + migration invuq717, migration kiểm trùng trước và dừng nếu có);
- `_recompute` chèn trong savepoint; đụng ràng buộc thì đọc lại dòng lượt kia vừa chèn rồi ghi tổng — không nhân đôi, không mất.
"""
import importlib.util
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.modules.inventory import service as inv
from app.modules.inventory.model import INVENTORY_KEY_CONSTRAINT, Inventory, InventoryMove

KEY = dict(company_id=3, warehouse_code="KHO-A", product_code="SP717")


def _rows(db):
    return db.query(Inventory).filter_by(**KEY).all()


def test_rang_buoc_duy_nhat_co_o_model(db):
    names = {c.name for c in Inventory.__table__.constraints}
    assert INVENTORY_KEY_CONSTRAINT in names
    db.add(Inventory(**KEY, product_name="A"))
    db.flush()
    db.add(Inventory(**KEY, product_name="B"))
    with pytest.raises(IntegrityError):
        db.flush()
    db.rollback()


def test_hai_lan_giao_cung_khoa_chi_mot_dong_ton(db):
    inv.apply_delivery(db, delivery_id=1, **KEY, product_name="Hàng", unit="kg", qty=10, price=5, user_id=1)
    inv.apply_delivery(db, delivery_id=2, **KEY, product_name="Hàng", unit="kg", qty=5, price=8, user_id=1)
    db.commit()
    (row,) = _rows(db)
    assert float(row.qty) == 15 and float(row.value) == 90 and float(row.avg_cost) == 6


def test_chay_dong_thoi_luot_sau_dung_rang_buoc_thi_doc_lai_va_cong_don(db, monkeypatch):
    """Mô phỏng: lượt A tra 'chưa có dòng' rồi, trước khi A chèn thì lượt B đã chèn và commit cùng khóa.

    Giả lập bằng cách cho lần tìm đầu của A trả None dù dòng đã có (đúng điều A nhìn thấy ngoài đời), lần tìm sau
    (đường cứu) chạy thật. Kết quả: một dòng, số đúng bằng tổng mọi phát sinh, không nổ ra ngoài.
    """
    db.add(InventoryMove(ref_type="gr", ref_id=1, **KEY, qty=10, unit_price=5))
    db.add(InventoryMove(ref_type="gr", ref_id=2, **KEY, qty=5, unit_price=8))
    db.add(Inventory(**KEY, product_name="Do B chèn", unit="kg", qty=10, value=50, avg_cost=5))   # lượt B đã xong
    db.commit()

    real_find = inv._find_row
    calls = {"n": 0}

    def blind_first_lookup(db_, *a, **kw):
        calls["n"] += 1
        return None if calls["n"] == 1 else real_find(db_, *a, **kw)

    monkeypatch.setattr(inv, "_find_row", blind_first_lookup)
    row = inv._recompute(db, 3, "KHO-A", "SP717", "Hàng", "kg")
    db.commit()
    assert calls["n"] == 2                              # có đi vào đường cứu
    assert [r.id for r in _rows(db)] == [row.id]        # vẫn một dòng, là dòng của B
    assert float(row.qty) == 15 and float(row.value) == 90 and row.product_name == "Hàng"


def test_migration_kiem_trung_truoc_khi_them_rang_buoc(db):
    #  Trong container backend mount ở /app (test ở /app/test) nên không có tầng `backend/`; ngoài repo thì có.
    root = Path(__file__).resolve().parents[2]
    rel = "migrations/versions/invuq717_bao_cr717_ton_kho_khoa_duy_nhat.py"
    path = next(c for c in (root / "backend" / rel, root / rel) if c.exists())
    spec = importlib.util.spec_from_file_location("invuq717", path)
    mig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mig)
    assert mig.down_revision == "lvcmp716" and mig.CONSTRAINT == INVENTORY_KEY_CONSTRAINT
    conn = db.connection()
    assert mig.duplicate_groups(conn) == []
    #  Bảng test đã mang ràng buộc (create_all từ model) nên không chèn trùng được vào nó; kiểm câu đếm trùng của migration
    #  trên một bảng tạm cùng hình dạng chưa có ràng buộc.
    conn.execute(text("CREATE TEMP TABLE tab_inventory_dup AS SELECT * FROM tab_inventory WHERE 0"))
    for name in ("x", "y"):
        conn.execute(text("INSERT INTO tab_inventory_dup (company_id, warehouse_code, product_code, product_name) "
                          "VALUES (3, 'KHO-A', 'SP717', :n)"), {"n": name})
    dup_sql = str(mig.DUP_SQL).replace("tab_inventory", "tab_inventory_dup")
    assert [tuple(r) for r in conn.execute(text(dup_sql)).fetchall()] == [(3, "KHO-A", "SP717", 2)]
