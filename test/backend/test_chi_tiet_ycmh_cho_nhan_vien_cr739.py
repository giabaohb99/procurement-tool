"""bao-CR-739 — màn Chi tiết YC mua hàng mở cho người chỉ có quyền Xem YCMH.

Luật:
  - có `report.read` -> phạm vi phòng ban cũ (`report_dept_scope`), không đổi;
  - không có `report.read` nhưng có `purchase_request.read` -> lọc đúng phạm vi YCMH (own: phiếu mình
    lập HOẶC mình là người yêu cầu);
  - thiếu cả hai -> 403. Xuất Excel và bản tổng hợp giữ gác cũ (`report.export` / `report.read`).
  - màn Tiến độ đơn mua hàng trả thêm `pr_id` để giao diện bấm mã PYC sang chi tiết YCMH.

Đi qua `TestClient` vì gác quyền nằm ở dependency của route.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.modules.department.model import Department
from app.modules.purchase_order.model import POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.user.model import User


@pytest.fixture
def client_as(db):
    def build(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield build
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _make_pr(db, seed, code, *, created_by, requester_id, department="Phòng Test", department_id=None):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, requester="Người YC", requester_id=requester_id,
                         department=department, department_id=department_id or seed.dept_id, status="approved",
                         request_date="2026-10-01", created_by=created_by, updated_by=created_by)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code=f"SP-{code}", product_name=f"Hàng {code}", qty=1,
                               unit="cái", price=1000, vat_pct=0, amount=1000, line_status="no_po"))
    db.flush()
    return pr


@pytest.fixture
def three_prs(db, seed):
    """A: người YC tự lập · B: NSTM lập cho chính NSTM (cùng phòng) · C: NSTM lập giùm, người YC đứng tên.
    D: phiếu phòng khác — để soi phạm vi phòng ban của người có `report.read`."""
    other = Department(code="DEPT02", name="Phòng Khác", company_id=seed.company_id, is_active=True)
    db.add(other)
    db.flush()
    prs = {
        "A": _make_pr(db, seed, "PYC-739-A", created_by=seed.u_req_id, requester_id=seed.emp_req_id),
        "B": _make_pr(db, seed, "PYC-739-B", created_by=seed.u_nstm_id, requester_id=seed.emp_nstm_id),
        "C": _make_pr(db, seed, "PYC-739-C", created_by=seed.u_nstm_id, requester_id=seed.emp_req_id),
        "D": _make_pr(db, seed, "PYC-739-D", created_by=seed.u_nstm_id, requester_id=seed.emp_nstm_id,
                      department="Phòng Khác", department_id=other.id),
    }
    db.commit()
    return prs


def _codes(resp) -> set[str]:
    assert resp.status_code == 200, resp.text
    return {r["pr_code"] for r in resp.json()["data"]["items"]}


def test_nhan_vien_chi_co_ycmh_own_thay_dung_phieu_cua_minh(db, seed, cap_quyen, client_as, three_prs):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, create=True)
    client = client_as(db.get(User, seed.u_req_id))
    resp = client.get("/api/reports/pr-lines", params={"year": "2026"})
    assert _codes(resp) == {"PYC-739-A", "PYC-739-C"}   # B cùng phòng nhưng của người khác -> không thấy
    assert resp.json()["data"]["total"] == 2


def test_nhan_vien_khong_xuat_duoc_va_khong_xem_tong_hop(db, seed, cap_quyen, client_as, three_prs):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, create=True)
    client = client_as(db.get(User, seed.u_req_id))
    assert client.get("/api/reports/pr-lines/export", params={"year": "2026"}).status_code == 403
    assert client.get("/api/reports/pr-lines/summary", params={"year": "2026"}).status_code == 403


def test_nguoi_co_report_read_giu_pham_vi_phong_ban_cu(db, seed, cap_quyen, client_as, three_prs):
    cap_quyen(seed.u_nstm_id, "report", scope="dept", read=True)
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="own", read=True)   # có thêm YCMH own vẫn theo luật báo cáo
    client = client_as(db.get(User, seed.u_nstm_id))
    codes = _codes(client.get("/api/reports/pr-lines", params={"year": "2026"}))
    assert codes == {"PYC-739-A", "PYC-739-B", "PYC-739-C"}   # cả phòng Test, không có phòng Khác


def test_khong_quyen_nao_bi_403(db, seed, client_as, three_prs):
    client = client_as(db.get(User, seed.u_req_id))
    assert client.get("/api/reports/pr-lines", params={"year": "2026"}).status_code == 403


def test_tien_do_don_mua_hang_tra_pr_id(db, seed, cap_quyen, client_as, three_prs):
    pr = three_prs["A"]
    po = PurchaseOrder(code="DMH-739-1", status="approved", company_id=seed.company_id,
                       order_date="2026-10-02", pr_code=pr.code)
    orphan = PurchaseOrder(code="DMH-739-2", status="approved", company_id=seed.company_id,
                           order_date="2026-10-02", pr_code="PYC-KHONG-CO")
    db.add_all([po, orphan])
    db.flush()
    db.add_all([POItem(po_id=po.id, product_code="SP1", qty_order=1, price=1),
                POItem(po_id=orphan.id, product_code="SP1", qty_order=1, price=1)])
    db.commit()
    cap_quyen(seed.u_nstm_id, "purchase_order", scope="all", read=True)
    client = client_as(db.get(User, seed.u_nstm_id))
    resp = client.get("/api/purchase-progress")
    assert resp.status_code == 200, resp.text
    by_code = {r["po_code"]: r for r in resp.json()["data"]["items"]}
    assert by_code["DMH-739-1"]["pr_id"] == pr.id
    assert by_code["DMH-739-2"]["pr_id"] is None   # mã PYC không có phiếu -> không thành đường bấm
