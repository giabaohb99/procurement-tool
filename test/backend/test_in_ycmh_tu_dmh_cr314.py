"""bao-CR-314 — in phiếu YCMH từ đơn mua hàng, chỉ những dòng có trên đơn.

Cổng là ĐƠN chứ không phải phiếu: người cầm đơn thường không có phạm vi đọc cả phiếu
(một YCMH chia cho nhiều NSTM phụ trách). Bộ này gọi thẳng `get_po_purchase_request`
với user thật từ fixture `seed`, cấp vai trò bằng `_grant`.

Các ca:
- lọc dòng theo mã hàng trên đơn + tính LẠI tiền hàng / VAT / tổng cộng;
- dòng ĐMH trùng mã (bao-CR-308) chỉ ra một dòng in;
- dòng ĐMH thiếu mã hoặc mã lạ -> không lọt vào bản in, đếm ở `po_lines_unmatched`;
- đơn ngoài phạm vi -> 403; đơn không gắn YCMH / YCMH không còn -> 404;
- KHÔNG cần quyền đọc YCMH, nhưng NCC đề xuất vẫn bị che khi thiếu `supplier.read`.
"""
import json

import pytest
from fastapi import HTTPException

from app.core.auth import perm_cache_clear
from app.modules.purchase_order.controller import get_po_purchase_request
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.user.model import User


@pytest.fixture(autouse=True)
def _clear_perm_cache():
    perm_cache_clear()
    yield
    perm_cache_clear()


@pytest.fixture(autouse=True)
def _tat_cong_tac_dieu_phoi(monkeypatch):
    """`_out` của YCMH hỏi công tắc điều phối, mà công tắc đó đọc bảng `Setting` bằng
    session THẬT (MySQL) — trong pytest SQLite thì đó là một lượt gọi mạng hỏng. Chốt cứng
    như `test_dispatch.py` vẫn làm; công tắc không liên quan gì tới bản in."""
    from app.modules.purchase_request import service as pr_service
    monkeypatch.setattr(pr_service, "dispatch_enabled", lambda: False)


def _grant(db, user_id: int, entity: str, scope: str = "company"):
    from app.modules.role.model import Permission, Role
    from app.modules.user.model import UserRole
    role = Role(code=f"R{user_id}{scope}{entity[:8]}", name="Vai trò test")
    db.add(role)
    db.flush()
    db.add(Permission(role_id=role.id, entity=entity, scope=scope,
                      can_read=True, can_print=True))
    db.add(UserRole(user_id=user_id, role_id=role.id))
    db.flush()
    perm_cache_clear()
    return role.id


def _make_pr(db, seed, code="PR-314", company_id=None):
    """Phiếu 3 dòng, mỗi dòng một NSTM phụ trách khác nhau (đúng cảnh chia việc thật)."""
    pr = PurchaseRequest(code=code, company_id=company_id or seed.company_id,
                         requester="Người YC", requester_id=seed.emp_req_id,
                         department="Phòng Test", created_by=0)
    db.add(pr)
    db.flush()
    rows = [
        # (mã hàng, SL, đơn giá, VAT %, người phụ trách)
        ("SP-A", 10, 1000, 8, seed.emp_nstm_code),
        ("SP-B", 5, 2000, 8, seed.emp_backup_code),
        ("SP-C", 2, 50000, 0, seed.emp_nstm_code),
    ]
    for code_, qty, price, vat, who in rows:
        db.add(PurchaseRequestItem(
            pr_id=pr.id, product_code=code_, product_name=f"Hàng {code_}", unit="cái",
            qty=qty, price=price, vat_pct=vat, amount=qty * price * (1 + vat / 100),
            assignee=who))
    db.flush()
    return pr


def _make_po(db, seed, pr_code="PR-314", codes=("SP-A",), company_id=None):
    po = PurchaseOrder(code="PO-314", pr_code=pr_code, status="approved",
                       company_id=company_id or seed.company_id, created_by=0)
    db.add(po)
    db.flush()
    for c in codes:
        db.add(POItem(po_id=po.id, product_code=c, product_name=f"Hàng {c}",
                      unit="cái", qty_order=1, price=1000))
    db.flush()
    return po


def _print(db, user, po_id):
    return json.loads(get_po_purchase_request(po_id, db, user).body)["data"]


def _status(fn):
    with pytest.raises(HTTPException) as exc:
        fn()
    return exc.value.status_code


# ── lọc dòng + tính lại tổng ────────────────────────────────────────────────────
def test_chi_in_dong_co_tren_don_va_tinh_lai_tong(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "purchase_order")
    _make_pr(db, seed)
    po = _make_po(db, seed, codes=("SP-A", "SP-C"))

    d = _print(db, user, po.id)
    assert [i["product_code"] for i in d["items"]] == ["SP-A", "SP-C"]
    #  Số lượng lấy từ PHIẾU (10 và 2), không phải SL đặt trên đơn (1 và 1).
    assert [i["qty"] for i in d["items"]] == [10, 2]
    assert d["subtotal"] == 10 * 1000 + 2 * 50000        # 110.000, chưa VAT
    assert d["total"] == 10 * 1000 * 1.08 + 2 * 50000    # 110.800, gồm VAT
    assert d["vat"] == 800
    assert d["po_lines_unmatched"] == 0
    #  Vẫn là phiếu gốc: giữ mã phiếu + thông tin người đề xuất (khách chốt không ghi
    #  thêm dòng nào báo đây là bản trích).
    assert d["code"] == "PR-314" and d["requester"] == "Người YC"
    assert d["po_code"] == "PO-314"


def test_dong_don_trung_ma_chi_in_mot_lan(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "purchase_order")
    _make_pr(db, seed)
    po = _make_po(db, seed, codes=("SP-B", "SP-B"))     # bao-CR-308: ĐMH được trùng mã

    d = _print(db, user, po.id)
    assert [i["product_code"] for i in d["items"]] == ["SP-B"]
    assert d["po_lines_unmatched"] == 0
    assert d["total"] == 5 * 2000 * 1.08


def test_dong_don_thieu_ma_hoac_ma_la_thi_dem_lai_khong_in(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "purchase_order")
    _make_pr(db, seed)
    po = _make_po(db, seed, codes=("SP-A", "", "SP-KHONG-CO"))

    d = _print(db, user, po.id)
    assert [i["product_code"] for i in d["items"]] == ["SP-A"]
    assert d["po_lines_unmatched"] == 2


def test_don_khong_co_dong_nao_khop_thi_bang_rong_tong_bang_khong(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "purchase_order")
    _make_pr(db, seed)
    po = _make_po(db, seed, codes=("SP-LA",))

    d = _print(db, user, po.id)
    assert d["items"] == []
    assert d["subtotal"] == 0 and d["vat"] == 0 and d["total"] == 0
    assert d["po_lines_unmatched"] == 1


# ── cổng vào ────────────────────────────────────────────────────────────────────
def test_don_ngoai_pham_vi_thi_403(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "purchase_order", scope="company")
    _make_pr(db, seed)
    po = _make_po(db, seed, codes=("SP-A",), company_id=seed.company_id + 100)
    assert _status(lambda: _print(db, user, po.id)) == 403


def test_don_khong_gan_phieu_hoac_phieu_khong_con_thi_404(db, seed):
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "purchase_order")

    po_trong = _make_po(db, seed, pr_code="", codes=("SP-A",))
    assert _status(lambda: _print(db, user, po_trong.id)) == 404

    db.delete(po_trong)
    db.flush()
    po_lac = _make_po(db, seed, pr_code="PR-KHONG-CO", codes=("SP-A",))
    assert _status(lambda: _print(db, user, po_lac.id)) == 404


def test_khong_can_quyen_doc_ycmh_nhung_van_che_ncc_de_xuat(db, seed):
    """Người dùng KHÔNG có grant nào trên `purchase_request` vẫn in được...

    ...vì cổng là quyền in ĐƠN. Nhưng NCC đề xuất (Task 5) vẫn phải bị che vì họ cũng
    không có `supplier.read` — bản in đi qua đúng serializer cũ của YCMH.
    """
    user = db.get(User, seed.u_req_id)
    _grant(db, user.id, "purchase_order")
    pr = _make_pr(db, seed)
    pr.suggested_supplier = "NCC bí mật"
    db.flush()
    po = _make_po(db, seed, codes=("SP-A",))

    d = _print(db, user, po.id)
    assert d["items"] and d["suggested_supplier"] == ""
