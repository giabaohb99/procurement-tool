"""ai-CR-237 — trợ lý ghi SỐ + NGÀY HÓA ĐƠN vào lần giao của ĐMH (bổ sung bao-CR-740).

- draft_po_receipt nhận `invoice_no` / `invoice_date` (theo phiếu hoặc theo dòng) ghi cùng lần nhận;
- chế độ `invoice_deliveries`: ghi hóa đơn vào lần giao CÓ SẴN theo id, không đổi số lượng;
- ngày hóa đơn không đoán (bao-CR-367): thiếu một trong hai là lỗi đọc được;
- lần giao đã có số HĐ khác: nháp cảnh báo GHI ĐÈ; xác nhận chặn khi hóa đơn đổi sau lúc soạn;
- ghi bằng đúng `update_po` như màn web (công nợ hàng lấy số HĐ theo lần giao);
- kết quả kèm link tuyệt đối mở đúng lần giao để người dùng tự đính tệp hóa đơn.
"""
# ruff: noqa: F811  (fixture `kho` dùng chung từ bài bao-CR-740)
import pytest

from app.modules.agent_hub import draft_create, mcp, mcp_keys
from app.modules.assistant import tools as T
from app.modules.payable.model import Payable
from app.modules.purchase_order.model import PODelivery

from test_assistant_ghi_lan_nhan_hang_cr740 import SUP, _item, _po, _receive, kho  # noqa: F401

INV = {"invoice_no": "6265", "invoice_date": "12/11/2026"}


def _draft(w, user=None, **args):
    base = {"supplier": "Bao bì nhựa Phương Nam"}
    return T.run_tool(w.db, user or w.staff, "draft_po_receipt", {**base, **args})


def test_ghi_hoa_don_cung_lan_nhan_moi(kho, db):
    out = _draft(kho, slip_date="2026-11-12", lines=[{"product_code": "NAP0169", "qty": 100}], **INV)
    (row,) = out["draft"]["rows"]
    assert (row["op"], row["invoice_no"], row["invoice_date"]) == ("add", "6265", "2026-11-12")
    draft_create.create(db, kho.staff, "po_receipt", out["draft"])
    d = db.query(PODelivery).filter(PODelivery.po_item_id == _item(db, kho.po712, "NAP0169").id).one()
    assert (d.invoice_no, d.invoice_date, float(d.received_qty)) == ("6265", "2026-11-12", 100)
    pay = db.query(Payable).filter(Payable.source_type == "goods", Payable.ref_id == d.id).one()
    assert pay.invoice_no == "6265"                      # công nợ hàng lấy số HĐ theo lần giao, như lưu trên web


def test_hoa_don_theo_tung_dong(kho):
    out = _draft(kho, slip_date="2026-11-12", lines=[
        {"product_code": "NAP0169", "qty": 100, "invoice_no": "A1", "invoice_date": "2026-11-10"},
        {"product_code": "NAP0156", "qty": 50}], **INV)
    got = {r["product_code"]: (r["invoice_no"], r["invoice_date"]) for r in out["draft"]["rows"]}
    assert got == {"NAP0169": ("A1", "2026-11-10"), "NAP0156": ("6265", "2026-11-12")}


def test_ngay_hoa_don_khong_doan(kho):
    out = _draft(kho, slip_date="2026-11-12", lines=[{"product_code": "NAP0169", "qty": 1}], invoice_no="6265")
    assert "ngày hóa đơn" in out["error"].lower() and "draft" not in out
    out = _draft(kho, slip_date="2026-11-12", lines=[{"product_code": "NAP0169", "qty": 1}], invoice_date="2026-11-12")
    assert "số hóa đơn" in out["error"].lower()
    out = _draft(kho, invoice_deliveries=[1], invoice_no="6265", invoice_date="12/13/2026")
    assert "ngày hóa đơn" in out["error"].lower()


def test_ghi_hoa_don_vao_lan_giao_co_san(kho, db):
    chai = _receive(db, kho.po712, "CPT0234", 500)
    nap = _receive(db, kho.po712, "NAP0169", 500)
    out = _draft(kho, invoice_deliveries=[chai.id, {"delivery_id": nap.id}], **INV)
    rows = out["draft"]["rows"]
    assert {(r["op"], r["delivery_id"]) for r in rows} == {("invoice", chai.id), ("invoice", nap.id)}
    assert not any("GHI ĐÈ" in w for w in out["warnings"])
    code, _ = draft_create.create(db, kho.staff, "po_receipt", out["draft"])
    assert code == "PO00712"
    for d in (db.get(PODelivery, chai.id), db.get(PODelivery, nap.id)):
        assert (d.invoice_no, d.invoice_date, float(d.received_qty)) == ("6265", "2026-11-12", 500)
    assert {p.invoice_no for p in db.query(Payable).filter(Payable.po_id == kho.po712.id)} == {"6265"}
    assert float(_item(db, kho.po712, "CPT0234").qty_received) == 500           # số lượng không đổi


def test_lan_giao_da_co_hoa_don_khac_canh_bao_ghi_de(kho, db):
    d = _receive(db, kho.po712, "NAP0169", 500)
    d.invoice_no, d.invoice_date = "111", "2026-11-01"
    db.commit()
    out = _draft(kho, invoice_deliveries=[d.id], **INV)
    (row,) = out["draft"]["rows"]
    assert row["overwrite"] is True and any("GHI ĐÈ" in w and "111" in w for w in out["warnings"])
    #  Lần nhận sửa lần giao đang có số HĐ khác cũng phải báo.
    pend = _receive(db, kho.po807, "NAP0156", 0, ship=3000)
    pend.invoice_no, pend.invoice_date = "222", "2026-11-02"
    db.commit()
    out = _draft(kho, slip_date="2026-11-12", lines=[{"product_code": "NAP0156", "qty": 3000}], **INV)
    assert any("GHI ĐÈ" in w and "222" in w for w in out["warnings"])


def test_hoa_don_doi_sau_luc_soan_thi_chan(kho, db):
    d = _receive(db, kho.po712, "NAP0169", 500)
    out = _draft(kho, invoice_deliveries=[d.id], **INV)
    d.invoice_no, d.invoice_date = "999", "2026-11-11"
    db.commit()
    with pytest.raises(draft_create.DraftError, match="đã đổi"):
        draft_create.create(db, kho.staff, "po_receipt", out["draft"])
    assert db.get(PODelivery, d.id).invoice_no == "999"


def test_lan_giao_ngoai_pham_vi_ghi(kho, db):
    d = _receive(db, kho.po712, "NAP0169", 500)
    out = _draft(kho, user=kho.outsider, invoice_deliveries=[d.id], **INV)
    assert "draft" not in out and "error" in out
    out = _draft(kho, invoice_deliveries=[987654], **INV)
    assert "draft" not in out and any("987654" in w for w in out.get("warnings", []))


def test_mcp_tra_link_tuyet_doi_mo_dung_lan_giao_de_dinh_tep(kho, db, mcp_all_groups):
    d = _receive(db, kho.po712, "NAP0169", 500)
    out = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "draft_po_receipt",
                        {"supplier": SUP, "invoice_deliveries": [d.id], **INV})
    (link,) = out["attach_links"]
    assert link["url"].startswith("http") and link["url"].endswith(f"/procurement/purchase-orders/{kho.po712.id}"
                                                                   f"?delivery={d.id}&attach=1")   # ai-CR-240
    assert "đính tệp" in out["note"]
    ok = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "confirm_draft", {"kind": "po_receipt", "draft": out["draft"]})
    assert ok["ok"] and ok["attach_links"][0]["url"] == link["url"] and "đính tệp" in ok["note"]
    assert db.get(PODelivery, d.id).invoice_no == "6265"
    #  Lần giao MỚI chưa có id lúc soạn: link mở đúng dòng hàng.
    out = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "draft_po_receipt",
                        {"supplier": SUP, "slip_date": "2026-11-12", "lines": [{"product_code": "NAP0156", "qty": 10}],
                         **INV})
    item_id = _item(db, kho.po807, "NAP0156").id
    assert out["attach_links"][0]["url"].endswith(f"/procurement/purchase-orders/{kho.po807.id}?line={item_id}")
