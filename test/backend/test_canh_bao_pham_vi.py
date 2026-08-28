"""Cảnh báo (chuông /api/alerts + khối alerts của dashboard) phải lọc PHẠM VI dữ liệu.

Lỗ hổng đã có (phát hiện 28/08/2026 qua tài khoản DEMOTP): `alert/controller.py::build`
chỉ kiểm QUYỀN đọc từng loại (`user_has_permission`) mà không chạy `apply_scope`, nên
trưởng phòng có `contract.read` phạm vi `company` vẫn thấy cảnh báo hợp đồng hết hạn
của PHÁP NHÂN KHÁC (kèm tên NCC trong tiêu đề). Dashboard còn gọi `build_alerts(db)`
không truyền user — bỏ luôn cả lớp kiểm quyền bên trong build.

Bài này chốt: có user thì từng khối (giao hàng / công nợ / hợp đồng) chỉ trả chứng từ
trong phạm vi của user; user=None (worker) vẫn thấy tất cả như cũ.

Gọi thẳng build() và monkeypatch hai hàm quyền — bài kiểm nhắm vào mệnh đề lọc,
không kiểm lớp xác thực HTTP.
"""
from types import SimpleNamespace

import pytest

from app.modules.alert import controller as alert_ct
from app.modules.contract.model import Contract
from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder

USER_ID = 7
CTY_A, CTY_B = 101, 202
QUA_HAN = "2000-01-01"   # luôn < hôm nay -> chắc chắn rơi vào nhánh cảnh báo danger

_ACTIONS = ("read", "create", "write", "delete", "approve", "cancel", "print", "export")


def _profile(scope="company", company_id=CTY_A):
    """Hồ sơ quyền tối thiểu đúng hình dạng `get_perm_profile`: đủ quyền đọc cả ba
    entity của cảnh báo, cùng một phạm vi."""
    perms = {e: {**{a: True for a in _ACTIONS}, "scope": scope}
             for e in ("contract", "payable", "purchase_order")}
    return {
        "grants": [{"role_id": 1, "perms": perms, "scope": {"inc": {}, "exc": {}}}],
        "company_id": company_id, "dept_id": 0, "dept_name": "",
        "employee_id": 0, "emp_code": "", "emp_name": "",
    }


@pytest.fixture
def du_lieu_hai_phap_nhan(db):
    """Mỗi pháp nhân một bộ: HĐ hết hạn + công nợ quá hạn + dòng giao hàng trễ."""
    for cty, hau_to in ((CTY_A, "A"), (CTY_B, "B")):
        db.add(Contract(code=f"HD-{hau_to}", company_id=cty, party_type="supplier",
                        party_name=f"NCC {hau_to}", title=f"Hợp đồng {hau_to}",
                        status="active", end_date=QUA_HAN))
        db.add(Payable(company_id=cty, supplier_code=f"NCC-{hau_to}",
                       supplier_name=f"NCC {hau_to}", po_code=f"PO-{hau_to}",
                       due_date=QUA_HAN, status="unpaid"))
        po = PurchaseOrder(code=f"PO-{hau_to}", company_id=cty, status="ordered")
        db.add(po)
        db.flush()
        item = POItem(po_id=po.id, product_code=f"SP-{hau_to}",
                      product_name=f"Hàng {hau_to}")
        db.add(item)
        db.flush()
        db.add(PODelivery(po_id=po.id, po_item_id=item.id,
                          received_qty=0, promised_date=QUA_HAN))
    db.commit()
    return db


def _build(db, monkeypatch, profile):
    """Chạy build() với user giả: quyền đọc luôn có, phạm vi theo `profile`."""
    monkeypatch.setattr(alert_ct, "user_has_permission", lambda *a, **k: True)
    monkeypatch.setattr(alert_ct, "get_perm_profile", lambda _db, _u: profile)
    return alert_ct.build(db, SimpleNamespace(id=USER_ID))


def test_pham_vi_cong_ty_chi_thay_canh_bao_phap_nhan_minh(du_lieu_hai_phap_nhan, monkeypatch):
    out = _build(du_lieu_hai_phap_nhan, monkeypatch, _profile(company_id=CTY_A))
    titles = "\n".join(x["title"] for x in out["items"])
    # Đủ ba loại cảnh báo của pháp nhân mình...
    assert "HD-A" in titles and "PO-A" in titles
    assert sum(1 for x in out["items"] if x["type"] == "delivery") == 1
    # ...và KHÔNG một dòng nào của pháp nhân khác (tiêu đề chứa cả tên NCC).
    assert "HD-B" not in titles and "PO-B" not in titles and "NCC B" not in titles
    assert out["total"] == 3


def test_doi_phap_nhan_thi_doi_bo_canh_bao(du_lieu_hai_phap_nhan, monkeypatch):
    out = _build(du_lieu_hai_phap_nhan, monkeypatch, _profile(company_id=CTY_B))
    titles = "\n".join(x["title"] for x in out["items"])
    assert "HD-B" in titles and "HD-A" not in titles
    assert out["total"] == 3


def test_worker_khong_user_van_thay_het(du_lieu_hai_phap_nhan):
    """Đường Celery (user=None) giữ nguyên hành vi cũ: quét toàn hệ."""
    out = alert_ct.build(du_lieu_hai_phap_nhan)
    titles = "\n".join(x["title"] for x in out["items"])
    assert "HD-A" in titles and "HD-B" in titles
    assert out["total"] == 6
