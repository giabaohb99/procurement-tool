"""bao-CR-305 — bộ lọc khoảng NGÀY HÓA ĐƠN (`invoice_from`/`invoice_to`) màn Công nợ.

Ngày hóa đơn KHÔNG lưu trên tab_payable mà dò lúc đọc: PODelivery.invoice_date ->
POItem.invoice_date -> incur_date (khi đã có số HĐ). Bộ lọc SQL trong `_filtered`
phải cùng luật với `service.get_invoice_date`, kẻo cột hiện một đằng lọc một nẻo —
đúng kiểu lỗi "Ngày phát sinh" từng chiếu created_at trong khi lọc theo incur_date.

Không đụng DB thật — fixture SQLite in-memory ở conftest.
"""
import json
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.auth import perm_cache_clear
from app.modules.payable import controller as C
from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PODelivery, POItem


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


def _grant(db, user_id: int, entity: str, scope: str):
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import UserRole
    role = Role(code=f"R{user_id}{scope}{entity[:4]}", name="Vai trò test")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity=entity, scope=scope,
                      can_read=True, can_export=True))
    db.add(UserRole(user_id=user_id, role_id=role.id))
    db.flush()
    perm_cache_clear()


def _payable(db, company_id, **kw):
    vals = dict(company_id=company_id, supplier_code="NX", supplier_name="NCC Xanh",
                source_type="goods", po_code="PO-1", invoice_no="HD-1",
                incur_date="2026-08-10", due_date="2026-09-10", amount=1000, vat=0,
                total=1000, paid_amount=0, remaining=1000, status="Chờ TT")
    vals.update(kw)
    p = Payable(**vals)
    db.add(p)
    db.flush()
    return p


def _req(qs: str = ""):
    return SimpleNamespace(query_params=QueryParams(qs))


def _user(db, seed):
    from app.modules.user.model import User
    return db.get(User, seed.u_req_id)


def _list_ids(db, user, qs: str) -> set[int]:
    resp = C.list_payables(request=_req(qs), pg={"offset": 0, "limit": 50},
                           db=db, user=user)
    data = json.loads(resp.body)["data"]
    return {it["id"] for it in data["items"]}


@pytest.fixture()
def bon_khoan(db, seed):
    """4 khoản phủ đủ 4 nhánh của get_invoice_date.

    A: đợt giao có invoice_date 07/09  -> ngày HĐ = 2026-09-07 (dù phát sinh 03/09)
    B: đợt giao trống, POItem có 20/08 -> ngày HĐ = 2026-08-20
    C: không gắn đợt giao, có số HĐ    -> ngày HĐ = incur_date 2026-08-14
    D: chưa có số HĐ                   -> không có ngày HĐ, mọi lọc ngày HĐ phải loại
    """
    d_a = PODelivery(po_id=1, po_item_id=0, invoice_date="2026-09-07")
    item_b = POItem(po_id=1, product_code="SP-B", invoice_date="2026-08-20")
    db.add_all([d_a, item_b])
    db.flush()
    d_b = PODelivery(po_id=1, po_item_id=item_b.id, invoice_date="")
    db.add(d_b)
    db.flush()

    a = _payable(db, seed.company_id, ref_type="delivery", ref_id=d_a.id,
                 invoice_no="HD-A", incur_date="2026-09-03")
    b = _payable(db, seed.company_id, ref_type="delivery", ref_id=d_b.id,
                 invoice_no="HD-B", incur_date="2026-08-10")
    c = _payable(db, seed.company_id, ref_type="delivery", ref_id=0,
                 invoice_no="HD-C", incur_date="2026-08-14")
    d = _payable(db, seed.company_id, ref_type="delivery", ref_id=0,
                 invoice_no="", incur_date="2026-08-14")

    user = _user(db, seed)
    _grant(db, user.id, "payable", "company")
    return SimpleNamespace(a=a, b=b, c=c, d=d, user=user)


def test_loc_ngay_hoa_don_du_bon_nhanh(db, seed, bon_khoan):
    k = bon_khoan
    # Không lọc -> thấy đủ 4 khoản
    assert _list_ids(db, k.user, "year=all") == {k.a.id, k.b.id, k.c.id, k.d.id}
    # Tháng 9: chỉ A (ngày HĐ từ đợt giao thắng incur_date 03/09)
    assert _list_ids(db, k.user, "year=all&invoice_from=2026-09-01&invoice_to=2026-09-30") == {k.a.id}
    # Tháng 8: B (từ POItem) + C (rơi về incur_date); D không số HĐ nên bị loại
    assert _list_ids(db, k.user,
                     "year=all&invoice_from=2026-08-01&invoice_to=2026-08-31") == {k.b.id, k.c.id}
    # Chỉ chặn dưới
    assert _list_ids(db, k.user, "year=all&invoice_from=2026-08-21") == {k.a.id}
    # Chỉ chặn trên
    assert _list_ids(db, k.user, "year=all&invoice_to=2026-08-20") == {k.b.id, k.c.id}


def test_loc_ngay_hoa_don_khong_pha_summary(db, seed, bon_khoan):
    """Summary đi cùng `_filtered` — join thêm không được nhân đôi tiền."""
    k = bon_khoan
    resp = C.summary(request=_req("year=all&invoice_from=2026-08-01&invoice_to=2026-08-31"),
                     db=db, user=k.user)
    data = json.loads(resp.body)["data"]
    assert data["total"] == 2000            # đúng B + C, mỗi khoản 1000
    assert data["remaining"] == 2000


def test_khoang_ngay_hd_ket_hop_khoang_phat_sinh(db, seed, bon_khoan):
    """Hai cặp lọc độc lập: phát sinh tháng 8 + hóa đơn tháng 9 -> rỗng (A phát sinh 09)."""
    k = bon_khoan
    qs = "year=all&incur_from=2026-08-01&incur_to=2026-08-31&invoice_from=2026-09-01"
    assert _list_ids(db, k.user, qs) == set()
