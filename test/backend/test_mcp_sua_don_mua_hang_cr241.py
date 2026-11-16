"""ai-CR-241 — cổng MCP / Trợ lý đề xuất SỬA Đơn mua hàng (ĐMH) đang Nháp / Bị trả lại.

`propose_document_update` (entity=purchase_order) chỉ trả bảng cũ → mới + confirm_token; `confirm_update` (nút Xác nhận
của web, `confirm_draft` kind=update của MCP) kiểm lại TỪ ĐẦU rồi ghi qua đúng `purchase_order.edit_service.update_po`
với danh sách dòng dựng lại ĐỦ từ sổ — để `_save_items`, `recompute_effects`, nhật ký chạy y như nút Lưu trên web.

Bối cảnh: 16/11 PO01178 tạo trên v2 bị trống kho và đơn giá về 0, phải chạy script trên prod mới sửa được.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.agent_hub import mcp, mcp_keys, mcp_settings
from app.modules.assistant import tools as T
from app.modules.assistant.tools.update_tool import confirm_update
from app.modules.catalog.model import Warehouse
from app.modules.purchase_order.model import OrderType, PODelivery, POItem, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.user.model import User


def _po(db, code, lines, *, status="draft", created_by, company_id, order_type=OrderType.DOMESTIC, pr_code="",
        currency="VND"):
    po = PurchaseOrder(code=code, supplier_code="NCC01", supplier_name="NCC Một", order_date="2026-11-16",
                       status=status, company_id=company_id, created_by=created_by, updated_by=created_by,
                       currency=currency, exchange_rate=1 if currency == "VND" else 25000,
                       order_type=int(order_type), pr_code=pr_code, payment_terms="Chuyển khoản", note="")
    db.add(po)
    db.flush()
    for pcode, qty, price, vat, wh in lines:
        db.add(POItem(po_id=po.id, product_code=pcode, product_name=f"Hàng {pcode}", unit="Cái", item_group="Chai",
                      qty_request=qty, qty_order=qty, price=price, vat=vat, warehouse_code=wh, currency=currency,
                      exchange_rate=1, required_date="2026-11-30", created_by=created_by, updated_by=created_by))
    db.flush()
    return po


def _line(db, po, pcode):
    return db.query(POItem).filter(POItem.po_id == po.id, POItem.product_code == pcode).order_by(POItem.id).first()


@pytest.fixture
def w(db, seed, cap_quyen):
    db.add_all([Warehouse(code="KHO1", name="Kho Tổng", is_active=True),
                Warehouse(code="KHO2", name="Kho Thành Phẩm", is_active=True),
                Warehouse(code="KHOCU", name="Kho Đã Đóng", is_active=False)])
    staff = db.get(User, seed.u_nstm_id)        # thu mua: sửa mọi đơn
    outsider = db.get(User, seed.u_req_id)      # chỉ đơn của mình
    reader = db.query(User).filter(User.email == "DEMOTP").one()   # chỉ được xem
    cap_quyen(staff.id, "purchase_order", scope="all", read=True, write=True)
    cap_quyen(outsider.id, "purchase_order", scope="own", read=True, write=True)
    cap_quyen(reader.id, "purchase_order", scope="all", read=True)

    pr = PurchaseRequest(code="YCMH09001", company_id=seed.company_id, department_id=seed.dept_id, purpose="Mua chai",
                         status="processing", created_by=staff.id, updated_by=staff.id)
    db.add(pr)
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP1", product_name="Hàng SP1", qty=100, unit="Cái",
                               price=1000, created_by=staff.id, updated_by=staff.id))

    ns = SimpleNamespace(db=db, staff=staff, outsider=outsider, reader=reader)
    ns.draft = _po(db, "PO01178", [("SP1", 100, 0, 8, ""), ("SP2", 50, 2000, 8, "")], created_by=staff.id,
                   company_id=seed.company_id, pr_code="YCMH09001")
    ns.approved = _po(db, "PO01179", [("SP1", 10, 1000, 8, "KHO1")], status="approved", created_by=staff.id,
                      company_id=seed.company_id)
    ns.imported = _po(db, "PO01180", [("SP9", 5, 30, 0, "KHO1")], created_by=staff.id, company_id=seed.company_id,
                      order_type=OrderType.IMPORT, currency="USD")
    ns.dup = _po(db, "PO01181", [("SP1", 1, 100, 8, ""), ("SP1", 2, 200, 8, "")], status="rejected",
                 created_by=staff.id, company_id=seed.company_id)
    db.commit()
    return ns


def _propose(w, user, code, po_lines=None, changes=None):
    args = {"entity": "purchase_order", "code": code}
    if po_lines is not None:
        args["po_lines"] = po_lines
    if changes is not None:
        args["changes"] = changes
    return T.run_tool(w.db, user, "propose_document_update", args)


def _token(out):
    assert out.get("status") == "ready", out
    return out["proposal"]["confirm_token"]


# ── ghi đúng ────────────────────────────────────────────────────────────────────────────

def test_sua_gia_va_kho_don_nhap_ghi_dung_va_tinh_lai(w):
    out = _propose(w, w.staff, "po01178", po_lines=[
        {"product_code": "SP1", "price": 1100, "warehouse_code": "Kho Tổng"},
        {"product_code": "SP2", "qty_order": 40, "warehouse_code": "kho2"}])
    p = out["proposal"]
    assert p["entity"] == "purchase_order" and p["code"] == "PO01178"
    assert p["url"].endswith(f"/procurement/purchase-orders/{w.draft.id}")
    labels = {(c["label"], c["old"], c["new"]) for c in p["changes"]}
    assert ("Dòng 1 · SP1 · Đơn giá", "0", "1.100") in labels
    assert ("Dòng 1 · SP1 · Kho nhận", "(trống)", "KHO1 · Kho Tổng") in labels
    assert ("Dòng 2 · SP2 · SL đặt", "50", "40") in labels
    money = next(c for c in p["changes"] if c["label"] == "Dòng 1 · SP1 · Giá trị đặt (trước / sau VAT)")
    assert money["old"] == "0 / 0 VND" and money["new"] == "110.000 / 118.800 VND"
    assert p["warnings"] == []                    # 1.100 lệch 10% giá đề xuất 1.000 của YCMH — dưới ngưỡng 20%

    #  Đề xuất KHÔNG ghi gì.
    w.db.expire_all()
    assert float(_line(w.db, w.draft, "SP1").price) == 0

    res = confirm_update(w.db, w.staff, _token(out))
    assert res["code"] == "PO01178"
    w.db.expire_all()
    sp1, sp2 = _line(w.db, w.draft, "SP1"), _line(w.db, w.draft, "SP2")
    assert (float(sp1.price), sp1.warehouse_code) == (1100, "KHO1")
    assert (float(sp2.qty_order), sp2.warehouse_code, float(sp2.price)) == (40, "KHO2", 2000)
    assert float(sp2.qty_remaining) == 40         # recompute_effects đã chạy (còn lại = SL đặt mới − 0 đã nhận)
    assert w.db.query(POItem).filter(POItem.po_id == w.draft.id).count() == 2


def test_sua_dau_don_va_dat_kho_ca_don(w):
    out = _propose(w, w.staff, "PO01178", changes={"payment_terms": "Tiền mặt", "note": "Giao buổi sáng"},
                   po_lines=[{"all_lines": True, "warehouse_code": "KHO2"}])
    fields = {c["label"] for c in out["proposal"]["changes"]}
    assert {"Hình thức thanh toán NCC", "Ghi chú", "Dòng 1 · SP1 · Kho nhận", "Dòng 2 · SP2 · Kho nhận"} <= fields
    confirm_update(w.db, w.staff, _token(out))
    w.db.expire_all()
    po = w.db.get(PurchaseOrder, w.draft.id)
    assert (po.payment_terms, po.note) == ("Tiền mặt", "Giao buổi sáng")
    assert {i.warehouse_code for i in po_items(w)} == {"KHO2"}


def po_items(w):
    return w.db.query(POItem).filter(POItem.po_id == w.draft.id).all()


def test_giu_nguyen_lan_giao_khi_sua(w):
    """Dựng lại dòng từ sổ phải kèm lần giao — không thì `_save_items` xóa sạch lần giao của dòng."""
    it = _line(w.db, w.draft, "SP2")
    w.db.add(PODelivery(po_id=w.draft.id, po_item_id=it.id, delivery_no=1, ship_qty=50, received_qty=0,
                        promised_date="2026-12-01", warehouse_code="", created_by=w.staff.id, updated_by=w.staff.id))
    w.db.commit()
    confirm_update(w.db, w.staff, _token(_propose(w, w.staff, "PO01178", po_lines=[{"product_code": "SP2", "price": 2100}])))
    w.db.expire_all()
    d = w.db.query(PODelivery).filter(PODelivery.po_item_id == it.id).all()
    assert len(d) == 1 and d[0].promised_date == "2026-12-01"


def test_canh_bao_lech_gia_de_xuat_ycmh(w):
    out = _propose(w, w.staff, "PO01178", po_lines=[{"product_code": "SP1", "price": 1300}])
    assert any("30%" in x and "1.000" in x for x in out["proposal"]["warnings"])


# ── chặn ────────────────────────────────────────────────────────────────────────────────

def test_don_da_duyet_bi_chan_kem_link(w):
    out = _propose(w, w.staff, "PO01179", po_lines=[{"product_code": "SP1", "price": 1}])
    assert "proposal" not in out
    assert "Đã duyệt" in out["error"] and "Nháp hoặc Bị trả lại" in out["error"]
    assert out["url"].endswith(f"/procurement/purchase-orders/{w.approved.id}")


def test_thieu_quyen_ghi_bi_chan(w):
    out = _propose(w, w.reader, "PO01178", po_lines=[{"product_code": "SP1", "price": 1}])
    assert out.get("denied") is True and "purchase_order.write" in out["reason"]


def test_ngoai_pham_vi_cung_cau_voi_khong_ton_tai(w):
    ngoai = _propose(w, w.outsider, "PO01178", po_lines=[{"product_code": "SP1", "price": 1}])
    khong_co = _propose(w, w.outsider, "PO99999", po_lines=[{"product_code": "SP1", "price": 1}])
    assert ngoai["error"].replace("PO01178", "X") == khong_co["error"].replace("PO99999", "X")


def test_kho_khong_co_trong_danh_muc(w):
    out = _propose(w, w.staff, "PO01178", po_lines=[{"product_code": "SP1", "warehouse_code": "Kho Bến Tre"}])
    assert "Kho Bến Tre" in out["error"] and "KHO1" in out["error"]
    out = _propose(w, w.staff, "PO01178", po_lines=[{"product_code": "SP1", "warehouse_code": "KHOCU"}])
    assert "proposal" not in out                   # kho đã tắt cũng không nhận


def test_don_nhap_khau_vat_khac_0_bi_chan(w):
    out = _propose(w, w.staff, "PO01180", po_lines=[{"product_code": "SP9", "vat": 10}])
    assert "nhập khẩu" in out["error"] and "proposal" not in out


@pytest.mark.parametrize("line, needle", [
    ({"product_code": "SP1", "price": -5}, "Đơn giá"),
    ({"product_code": "SP1", "qty_order": 10 ** 12}, "SL đặt"),
    ({"product_code": "SP1", "vat": 150}, "VAT"),
    ({"product_code": "SP1", "required_date": "30/11/2026"}, "YYYY-MM-DD"),
    ({"product_code": "SP1", "discount": 5}, "discount"),
    ({"product_code": "KHONGCO", "price": 1}, "KHONGCO"),
    ({"line_id": 999999, "price": 1}, "999999"),
    ({"all_lines": True, "price": 1}, "all_lines"),
])
def test_gia_tri_sai_bi_chan(w, line, needle):
    out = _propose(w, w.staff, "PO01178", po_lines=[line])
    assert "proposal" not in out and needle in out["error"]


def test_ma_hang_trung_bat_buoc_dung_id(w):
    out = _propose(w, w.staff, "PO01181", po_lines=[{"product_code": "SP1", "price": 300}])
    assert "line_id" in out["error"]
    second = w.db.query(POItem).filter(POItem.po_id == w.dup.id).order_by(POItem.id.desc()).first()
    out = _propose(w, w.staff, "PO01181", po_lines=[{"line_id": second.id, "price": 300}])
    confirm_update(w.db, w.staff, _token(out))
    w.db.expire_all()
    assert [float(i.price) for i in w.db.query(POItem).filter(POItem.po_id == w.dup.id).order_by(POItem.id)] == [100, 300]


def test_gia_tri_doi_giua_hai_buoc_thi_chan(w):
    token = _token(_propose(w, w.staff, "PO01178", po_lines=[{"product_code": "SP1", "price": 1100}]))
    sp1 = _line(w.db, w.draft, "SP1")
    sp1.price = 950                                # người khác sửa tay trên web giữa hai bước
    w.db.commit()
    with pytest.raises(HTTPException) as e:
        confirm_update(w.db, w.staff, token)
    assert e.value.status_code == 409
    w.db.expire_all()
    assert float(_line(w.db, w.draft, "SP1").price) == 950


def test_don_bi_gui_duyet_giua_hai_buoc_thi_chan(w):
    token = _token(_propose(w, w.staff, "PO01178", po_lines=[{"product_code": "SP1", "price": 1100}]))
    w.draft.status = "submitted"
    w.db.commit()
    with pytest.raises(HTTPException) as e:
        confirm_update(w.db, w.staff, token)
    assert e.value.status_code == 400 and "Chờ duyệt" in e.value.detail


def test_xac_nhan_hai_lan_khong_ghi_doi(w):
    token = _token(_propose(w, w.staff, "PO01178", po_lines=[{"product_code": "SP2", "qty_order": 45}]))
    confirm_update(w.db, w.staff, token)
    with pytest.raises(HTTPException) as e:
        confirm_update(w.db, w.staff, token)
    assert e.value.status_code == 409
    w.db.expire_all()
    assert float(_line(w.db, w.draft, "SP2").qty_order) == 45


def test_token_cua_nguoi_khac_bi_chan(w):
    token = _token(_propose(w, w.staff, "PO01178", po_lines=[{"product_code": "SP1", "price": 1100}]))
    with pytest.raises(HTTPException) as e:
        confirm_update(w.db, w.reader, token)
    assert e.value.status_code == 403


# ── cổng MCP ────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def edit_on(monkeypatch):
    """Nhóm G7 "edit" bật (mặc định tắt) — như test_agent_hub_mcp_sua_xoa_kh_ai2_5."""
    real = mcp_settings.tool_blocked
    monkeypatch.setattr(mcp_settings, "tool_blocked",
                        lambda db, name, args=None: None if name in mcp.PROPOSAL_TOOLS else real(db, name, args))


def _mcp_call(w, scope, name, args):
    import json

    key = SimpleNamespace(scope=scope, id=1)
    res = mcp.handle(w.db, w.staff, key, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                          "params": {"name": name, "arguments": args}}, {})
    return json.loads(res["result"]["content"][0]["text"])


def test_khoa_chi_doc_bi_chan(w, edit_on):
    args = {"entity": "purchase_order", "code": "PO01178", "po_lines": [{"product_code": "SP1", "price": 1100}]}
    out = _mcp_call(w, mcp_keys.SCOPE_READ, "propose_document_update", args)
    assert out.get("denied") is True and "proposal" not in out
    tools = {t["name"] for t in mcp.list_tools(w.db, w.staff, mcp_keys.SCOPE_READ)}
    assert "propose_document_update" not in tools


def test_qua_mcp_khoa_duoc_ghi_ghi_dung(w, edit_on):
    args = {"entity": "purchase_order", "code": "PO01178", "po_lines": [{"product_code": "SP1", "price": 1100}]}
    out = _mcp_call(w, mcp_keys.SCOPE_WRITE, "propose_document_update", args)
    assert out["proposal"]["url"].startswith("http")           # đường tuyệt đối cho ứng dụng AI ngoài
    done = _mcp_call(w, mcp_keys.SCOPE_WRITE, "confirm_draft", {"kind": "update", "draft": out["proposal"]})
    assert done.get("ok") is True, done
    w.db.expire_all()
    assert float(_line(w.db, w.draft, "SP1").price) == 1100
    again = _mcp_call(w, mcp_keys.SCOPE_WRITE, "confirm_draft", {"kind": "update", "draft": out["proposal"]})
    assert "Chưa ghi gì" in again["error"]
