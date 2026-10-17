"""ai-CR-211 — tool `erp_read` (K13, tầng T3 doc/erp/21 §5.5): đọc danh sách / chi tiết theo danh sách TRẮNG resource.

Canh:
  - resource ngoài danh sách bị từ chối kèm danh sách hợp lệ; thiếu quyền entity → denied nói rõ;
  - danh sách đi qua đúng hàm route của màn web (phạm vi «của mình» chỉ ra phiếu của mình);
  - id ngoài phạm vi trả ĐÚNG câu như id không tồn tại;
  - phân trang: tối đa 5 trang × 100 dòng mỗi lượt, còn nữa thì has_more + next_page;
  - gọt trường + nhãn trạng thái + url; thiếu supplier.read thì ẩn NCC của ĐMH;
  - đọc chi tiết YCMH KHÔNG ghi gì (route chi tiết YCMH ghi ngầm «phương án 0» — tool không được gọi nó);
  - cổng MCP: khóa đọc thấy tool, url thành tuyệt đối.
"""
from types import SimpleNamespace

import pytest

from app.modules.assistant import tools as T
from app.modules.assistant.tools import erp_read_tool as er
from app.modules.contract.model import Contract
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.user.model import User


def _user(db, seed):
    return db.get(User, seed.u_req_id)


def _read(db, user, resource, **args):
    return T.run_tool(db, user, "erp_read", {"resource": resource, **args})


def _prs(db, seed, n: int, created_by: int):
    rows = [PurchaseRequest(code=f"PYC{900 + i:05d}", company_id=seed.company_id, department_id=seed.dept_id,
                            department="Phòng Test", requester="Người YC", purpose=f"Mua đợt {i}", status="submitted",
                            request_date=f"2026-10-{i + 1:02d}", created_by=created_by, is_deleted=False)
            for i in range(n)]
    db.add_all(rows)
    db.commit()
    return rows


# ── Danh sách trắng + quyền ───────────────────────────────────────────────────

def test_resource_ngoai_danh_sach_va_thieu_quyen(db, seed):
    user = _user(db, seed)
    out = _read(db, user, "user")
    assert "không có trong danh sách" in out["error"] and "purchase_order (Đơn mua hàng (ĐMH))" in out["error"]
    assert "goods_receipt" in out["error"]
    out = _read(db, user, "contract")
    assert out["denied"] and "contract" in out["error"]


# ── Phân trang ────────────────────────────────────────────────────────────────

def test_phan_trang_toi_da_5_trang_100_dong_va_has_more(db, seed, cap_quyen):
    _prs(db, seed, 7, created_by=seed.u_req_id)
    cap_quyen(seed.u_req_id, "purchase_request", scope="all", read=True)
    user = _user(db, seed)
    out = _read(db, user, "purchase_request", page_size=2, pages=2)
    assert (out["total"], out["returned"], out["pages_read"], out["has_more"], out["next_page"]) == (7, 4, 2, True, 3)
    assert "page=3" in out["note"]
    last = _read(db, user, "purchase_request", page_size=2, page=3, pages=5)
    assert (last["returned"], last["pages_read"], last["has_more"]) == (3, 2, False) and "next_page" not in last
    big = _read(db, user, "purchase_request", page_size=100000, pages=99)
    assert big["page_size"] == er.MAX_PAGE_SIZE and big["returned"] == 7

    item = out["items"][0]
    assert set(item) <= set(er.RESOURCES["purchase_request"].fields) | {"status_label", "url"}
    assert item["status_label"] == "Chờ duyệt" and item["url"] == f"/procurement/purchase-requests/{item['id']}"
    assert out["money_fields"] == {"total": "sau VAT"} and out["currency"] == "VND"
    assert out["link"] == "/procurement/purchase-requests"


def test_bo_loc_qua_route_va_bo_loc_la(db, seed, cap_quyen):
    _prs(db, seed, 3, created_by=seed.u_req_id)
    cap_quyen(seed.u_req_id, "purchase_request", scope="all", read=True)
    user = _user(db, seed)
    out = _read(db, user, "purchase_request", filters={"q": "PYC00901", "is_deleted": "1", "sort_by": "id"})
    assert [i["code"] for i in out["items"]] == ["PYC00901"]
    assert sorted(out["ignored_filters"]) == ["is_deleted", "sort_by"] and "status" in out["allowed_filters"]
    dated = _read(db, user, "purchase_request", filters={"request_date_from": "2026-10-02"})
    assert dated["total"] == 2


# ── Phạm vi + id ngoài phạm vi ────────────────────────────────────────────────

def test_pham_vi_cua_minh_va_id_ngoai_pham_vi_nhu_khong_ton_tai(db, seed, cap_quyen):
    mine = Contract(code="HD-MINE", title="HĐ của tôi", company_id=seed.company_id, status="active",
                    created_by=seed.u_req_id)
    other = Contract(code="HD-OTHER", title="HĐ người khác", company_id=seed.company_id, status="active",
                     created_by=seed.u_req_id + 999)
    db.add_all([mine, other])
    db.commit()
    cap_quyen(seed.u_req_id, "contract", scope="own", read=True)
    user = _user(db, seed)
    out = _read(db, user, "contract")
    assert [i["code"] for i in out["items"]] == ["HD-MINE"] and out["items"][0]["status_label"]
    detail = _read(db, user, "contract", id=mine.id)
    assert detail["item"]["code"] == "HD-MINE" and detail["item"]["url"] == f"/production/contracts/{mine.id}"
    hidden = _read(db, user, "contract", id=other.id)["error"]
    missing = _read(db, user, "contract", id=987654)["error"]
    assert hidden.replace(str(other.id), "#") == missing.replace("987654", "#")
    assert "Không tìm thấy" in hidden


def test_chi_tiet_ycmh_khong_ghi_phuong_an_0_va_ngoai_pham_vi(db, seed, cap_quyen, monkeypatch):
    from app.modules.purchase_request import option_service

    monkeypatch.setattr(option_service, "ensure_option_zero", lambda *a, **k: pytest.fail("không được ghi phương án 0"))
    mine, = _prs(db, seed, 1, created_by=seed.u_req_id)
    theirs = PurchaseRequest(code="PYC09999", company_id=seed.company_id, department_id=0, department="Khác",
                             status="submitted", created_by=seed.u_req_id + 999, is_deleted=False)
    db.add(theirs)
    db.commit()
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True)
    user = _user(db, seed)
    detail = _read(db, user, "purchase_request", id=mine.id)
    assert detail["item"]["code"] == mine.code and detail["item"]["status_label"] == "Chờ duyệt"
    assert "Không tìm thấy" in _read(db, user, "purchase_request", id=theirs.id)["error"]


def test_dmh_an_ncc_khi_thieu_quyen_va_nhan_trang_thai(db, seed, cap_quyen):
    db.add(PurchaseOrder(code="PO-ER1", company_id=seed.company_id, department_id=seed.dept_id, order_date="2026-10-01",
                         status="approved", supplier_code="A", supplier_name="NCC A", created_by=seed.u_req_id))
    db.commit()
    cap_quyen(seed.u_req_id, "purchase_order", scope="all", read=True)
    user = _user(db, seed)
    out = _read(db, user, "purchase_order")
    item = out["items"][0]
    assert item["code"] == "PO-ER1" and item["status_label"] == "Đã duyệt" and "supplier_name" not in item
    assert "Ẩn mã / tên nhà cung cấp" in out["hidden"]
    cap_quyen(seed.u_req_id, "supplier", scope="all", read=True)
    assert _read(db, user, "purchase_order")["items"][0]["supplier_name"] == "NCC A"


def test_ncc_san_pham_nhan_hang(db, seed, cap_quyen):
    from app.modules.goods_receipt.model import GoodsReceipt
    from app.modules.product.model import Product
    from app.modules.supplier.model import Supplier

    sup = Supplier(code="NCC-ER", name="NCC Đọc", tax_code="0101", bank_account="123456789")
    prod = Product(code="SP-ER", name="Thùng carton", unit="cái")
    db.add_all([sup, prod, GoodsReceipt(code="GR00001", delivery_id=1, po_code="PO-ER1", product_code="SP-ER", qty_received=5,
                                        received_date="2026-10-05", company_id=seed.company_id,
                                        created_by=seed.u_req_id),
                GoodsReceipt(code="GR00002", delivery_id=2, po_code="PO-X", product_code="SP-X", qty_received=1,
                             received_date="2026-10-06", company_id=seed.company_id, created_by=seed.u_req_id + 999)])
    db.commit()
    for entity in ("supplier", "product"):
        cap_quyen(seed.u_req_id, entity, scope="all", read=True)
    cap_quyen(seed.u_req_id, "goods_receipt", scope="own", read=True)
    user = _user(db, seed)
    s = _read(db, user, "supplier", id=sup.id)["item"]
    assert s["name"] == "NCC Đọc" and "bank_account" not in s                          # gọt trường ngân hàng
    p = _read(db, user, "product", filters={"search": "carton"})
    assert [i["code"] for i in p["items"]] == ["SP-ER"]
    gr = _read(db, user, "goods_receipt")
    assert [i["code"] for i in gr["items"]] == ["GR00001"]                             # phạm vi «của mình»
    assert "Không tìm thấy" in _read(db, user, "goods_receipt", id=gr["items"][0]["id"] + 1)["error"]


# ── Cổng MCP ──────────────────────────────────────────────────────────────────

def test_mcp_khoa_doc_thay_tool_va_url_tuyet_doi(db, monkeypatch):
    from app.core.config import settings
    from app.modules.agent_hub import mcp

    assert "erp_read" in mcp.READ_TOOLS and not mcp.is_write_tool("erp_read")
    monkeypatch.setattr(settings, "AGENT_ERP_URL", "https://deverp.degoholding.vn")
    out = mcp._absolute_downloads({"link": "/procurement/purchase-orders",
                                   "items": [{"url": "/procurement/purchase-orders/7"}],
                                   "item": {"url": "/production/contracts/3"}})
    assert out["items"][0]["url"] == "https://deverp.degoholding.vn/procurement/purchase-orders/7"
    assert out["item"]["url"] == "https://deverp.degoholding.vn/production/contracts/3"
    assert mcp._absolute_downloads(SimpleNamespace()) is not None


def test_ycbg_danh_sach_va_dmh_chi_tiet_chay_duoc(db, seed, cap_quyen):
    from app.modules.survey_request.model import SurveyRequest

    sr = SurveyRequest(code="YCKS-ER1", company_id=seed.company_id, department_id=seed.dept_id, department="Phòng Test",
                       status="draft", request_date="2026-10-03", created_by=seed.u_req_id)
    po = PurchaseOrder(code="PO-ER2", company_id=seed.company_id, department_id=seed.dept_id, order_date="2026-10-01",
                       status="partial", created_by=seed.u_req_id)
    db.add_all([sr, po])
    db.commit()
    for entity in ("survey_request", "purchase_order"):
        cap_quyen(seed.u_req_id, entity, scope="all", read=True)
    user = _user(db, seed)
    srs = _read(db, user, "survey_request")
    assert [(i["code"], i["status_label"]) for i in srs["items"]] == [("YCKS-ER1", "Nháp")]
    d = _read(db, user, "purchase_order", id=po.id)["item"]
    assert d["code"] == "PO-ER2" and d["status_label"] == "Đã nhận một phần" and d["lines"] == []
    assert d["url"] == f"/procurement/purchase-orders/{po.id}"
