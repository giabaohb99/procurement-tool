"""bao-CR-740 — trợ lý ghi LẦN NHẬN HÀNG vào ĐMH từ phiếu xuất kho NCC (po_open_lines · draft_po_receipt · confirm_draft
kind=po_receipt). CHỈ kiểm phần vừa làm:

- chia theo bộ mã đi kèm (chai + nắp cùng đơn) trước đơn cũ; không có bộ thì đơn cũ trước;
- giao dư không chặn, có cảnh báo; bỏ đơn nháp / đơn đã nhận đủ;
- người ngoài phạm vi không thấy, không ghi được;
- xác nhận ghi đúng lần giao + sinh phiếu nhập kho / tồn kho / công nợ y như màn web (so với `update_po` nhận payload
  dựng từ `_out` như giao diện gửi lên); không đè lần giao cũ; sửa lần giao đang chờ; thêm + sửa trong một nháp;
- xác nhận lần hai không ghi đôi.
"""
import re
from types import SimpleNamespace

import pytest

from app.modules.agent_hub import draft_create, mcp, mcp_keys
from app.modules.assistant import tools as T
from app.modules.goods_receipt.model import GoodsReceipt
from app.modules.inventory.model import InventoryMove
from app.modules.payable.model import Payable
from app.modules.product.model import Product
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.purchase_order.schema import DeliveryIn, POItemIn, POUpdate
from app.modules.purchase_order.serializer import _out
from app.modules.supplier.model import Supplier
from app.modules.user.model import User

SUP = "NCCPN"
SLIP = [{"product_code": "CPT0234", "qty": 3780}, {"product_code": "NAP0169", "qty": 504},
        {"product_code": "NAP0156", "qty": 3276}]


def _po(db, code, order_date, lines, *, status="approved", supplier=SUP, created_by=999, company_id=1):
    name = "CÔNG TY TNHH BAO BÌ NHỰA PHƯƠNG NAM" if supplier == SUP else f"NCC {supplier}"
    po = PurchaseOrder(code=code, misa_code="MS" + code[2:], supplier_code=supplier, supplier_name=name,
                       order_date=order_date, status=status, company_id=company_id, created_by=created_by,
                       updated_by=created_by, currency="VND", exchange_rate=1)
    db.add(po)
    db.flush()
    for pcode, qty in lines:
        db.add(POItem(po_id=po.id, product_code=pcode, product_name=f"Hàng {pcode}", unit="Cái", item_group="Chai",
                      qty_order=qty, price=1000, vat=8, warehouse_code="KHO1", currency="VND", exchange_rate=1,
                      progress_status="ordered", created_by=created_by, updated_by=created_by))
    db.flush()
    return po


def _item(db, po, pcode):
    return db.query(POItem).filter(POItem.po_id == po.id, POItem.product_code == pcode).one()


def _receive(db, po, pcode, qty, *, ship=None, date="2026-10-05", uid=1):
    """Một lần giao đã có sẵn (qty = 0 → lần giao đang chờ), tính lại hiệu ứng như lúc lưu trên web."""
    it = _item(db, po, pcode)
    n = db.query(PODelivery).filter(PODelivery.po_item_id == it.id).count() + 1
    d = PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=n, ship_qty=ship if ship is not None else qty,
                   received_qty=qty, received_date=date if qty else "", warehouse_code="KHO1", created_by=uid,
                   updated_by=uid)
    db.add(d)
    db.flush()
    po_service.recompute_effects(db, po, uid)
    db.commit()
    return d


@pytest.fixture
def kho(db, seed, cap_quyen):
    for code in ("CPT0234", "NAP0169", "NAP0156", "NAP0999", "KHAC01"):
        db.add(Product(code=code, name=f"Hàng {code}", unit="Cái"))
    db.add(Supplier(code=SUP, name="Công ty TNHH Bao Bì Nhựa Phương Nam", tax_code="0301234567"))
    db.add(Supplier(code="NCCTWIN", name="NCC Đối chứng"))
    staff = db.get(User, seed.u_nstm_id)
    outsider = db.get(User, seed.u_req_id)
    cap_quyen(staff.id, "purchase_order", scope="all", read=True, write=True)
    cap_quyen(staff.id, "supplier", scope="all", read=True)
    cap_quyen(outsider.id, "purchase_order", scope="own", read=True, write=True)
    cap_quyen(outsider.id, "supplier", scope="all", read=True)
    w = SimpleNamespace(staff=staff, outsider=outsider, db=db)
    w.po650 = _po(db, "PO00650", "2026-09-01", [("CPT0234", 1000)])                       # cũ nhất, chỉ có chai
    w.po712 = _po(db, "PO00712", "2026-09-10", [("CPT0234", 500), ("NAP0169", 500)])      # bộ chai + nắp
    w.po807 = _po(db, "PO00807", "2026-10-01", [("CPT0234", 3200), ("NAP0156", 3200)])    # bộ chai + nắp
    w.draft = _po(db, "PO00900", "2026-08-01", [("CPT0234", 9000)], status="draft")
    w.full = _po(db, "PO00901", "2026-08-02", [("NAP0169", 500)])
    w.mine = _po(db, "PO00950", "2026-11-01", [("NAP0999", 100)], created_by=outsider.id)   # đơn của người ngoài
    db.commit()
    _receive(db, w.full, "NAP0169", 500)
    return w


def _draft(w, user=None, lines=None, **over):
    args = {"supplier": "Bao bì nhựa Phương Nam", "slip_date": "2026-11-06", "slip_no": "XK-0815",
            "lines": lines if lines is not None else SLIP, **over}
    return T.run_tool(w.db, user or w.staff, "draft_po_receipt", args)


def _plan(out):
    return {(r["po_code"], r["product_code"]): r["qty"] for r in out["draft"]["rows"]}


# ── đọc ───────────────────────────────────────────────────────────────────────────────────
def test_doc_dong_con_thieu_kem_lan_giao(kho):
    _receive(kho.db, kho.po807, "CPT0234", 1000, date="2026-10-20")
    out = T.run_tool(kho.db, kho.staff, "po_open_lines", {"supplier": "phuong nam", "product_codes": ["CPT0234"]})
    assert out["supplier"]["code"] == SUP
    rows = {r["po_code"]: r for r in out["items"]}
    assert set(rows) == {"PO00650", "PO00712", "PO00807"}            # bỏ đơn nháp
    r = rows["PO00807"]
    assert (r["misa_code"], r["qty_order"], r["qty_received"], r["qty_remaining"]) == ("MS00807", 3200, 1000, 2200)
    assert r["deliveries"][0]["received_qty"] == 1000 and r["deliveries"][0]["status_label"] == "Đã nhận"
    assert "price" not in r and r["url"] == f"/procurement/purchase-orders/{kho.po807.id}"
    nap = T.run_tool(kho.db, kho.staff, "po_open_lines", {"supplier": SUP, "product_codes": ["NAP0169"]})
    assert [x["po_code"] for x in nap["items"]] == ["PO00712"]   # PO00901 đã nhận đủ → bỏ


def test_thieu_quyen_va_ngoai_pham_vi(kho, db):
    nobody = User(email="NOBODY", password_hash="x", is_active=True)
    db.add(nobody)
    db.commit()
    assert T.run_tool(db, nobody, "po_open_lines", {"supplier": SUP}).get("denied")
    assert T.run_tool(db, nobody, "draft_po_receipt", {"supplier": SUP}).get("denied")
    out = T.run_tool(db, kho.outsider, "po_open_lines", {"supplier": SUP})
    assert [x["po_code"] for x in out["items"]] == ["PO00950"]       # chỉ đơn của mình
    d = _draft(kho, kho.outsider, lines=[*SLIP, {"product_code": "NAP0999", "qty": 100}])
    assert {r["po_code"] for r in d["draft"]["rows"]} == {"PO00950"}
    assert sum("không có dòng ĐMH" in w for w in d["warnings"]) == 3     # mã của đơn người khác: như không có
    #  Nháp sửa tay trỏ sang đơn ngoài phạm vi → xác nhận chặn, cùng câu với đơn không tồn tại.
    staff_draft = _draft(kho)["draft"]
    with pytest.raises(draft_create.DraftError, match="phạm vi bạn được ghi") as e1:
        draft_create.create(db, kho.outsider, "po_receipt", staff_draft)
    ghost = {**staff_draft, "rows": [{**staff_draft["rows"][0], "po_id": 987654}]}
    with pytest.raises(draft_create.DraftError, match="phạm vi bạn được ghi") as e2:
        draft_create.create(db, kho.outsider, "po_receipt", ghost)
    assert re.sub(r"#\d+", "#", str(e1.value)) == re.sub(r"#\d+", "#", str(e2.value))
    assert db.query(PODelivery).filter(PODelivery.received_date == "2026-11-06").count() == 0


# ── chia ──────────────────────────────────────────────────────────────────────────────────
def test_chia_theo_bo_ma_di_kem(kho):
    out = _draft(kho)
    assert _plan(out) == {("PO00712", "CPT0234"): 504, ("PO00712", "NAP0169"): 504,
                          ("PO00807", "CPT0234"): 3276, ("PO00807", "NAP0156"): 3276}
    assert all(r["op"] == "add" and r["received_date"] == "2026-11-06" for r in out["draft"]["rows"])
    over = [w for w in out["warnings"] if w.startswith("GIAO DƯ")]
    assert len(over) == 4 and any("4 Cái mã NAP0169 ở PO00712" in w for w in over)
    assert out["kind"] == "po_receipt" and out["draft"]["draft_ref"]


def test_khong_co_bo_thi_don_cu_truoc_va_bo_don_nhap(kho):
    out = _draft(kho, lines=[{"product_code": "CPT0234", "qty": "1.200"}])
    assert _plan(out) == {("PO00650", "CPT0234"): 1000, ("PO00712", "CPT0234"): 200}
    assert not out["warnings"]


def test_giao_du_vuot_moi_don_va_ma_la(kho):
    out = _draft(kho, lines=[{"product_code": "CPT0234", "qty": 5000}, {"product_code": "ZZZ999", "qty": 5},
                             {"product_code": "KHAC01", "qty": 5}])
    plan = _plan(out)
    assert plan[("PO00807", "CPT0234")] == 3500 and sum(plan.values()) == 5000   # dư 300 dồn dòng chia sau cùng
    assert any(w.startswith("GIAO DƯ 300") for w in out["warnings"])
    #  Số kiểu Việt: chấm ngăn nghìn, bỏ ,0 thừa — không in dạng khoa học (1e+06).
    assert any("đã nhận 3.500 / đặt 3.200." in w for w in out["warnings"])
    from app.modules.assistant.tools.po_receipt_tool import vn
    assert (vn(1_000_000.0), vn(990000), vn(12.5), vn(0.125)) == ("1.000.000", "990.000", "12,5", "0,125")
    assert any("ZZZ999" in w and "danh mục" in w for w in out["warnings"])
    assert any("KHAC01" in w and "không có dòng ĐMH" in w for w in out["warnings"])


def test_chi_dinh_cua_nguoi_dung(kho):
    out = _draft(kho, lines=[{"product_code": "CPT0234", "qty": 3780,
                              "assign": [{"po_code": "MS00807", "qty": 3000}, {"po_code": "PO00900", "qty": 1}]}])
    plan = _plan(out)
    assert plan[("PO00807", "CPT0234")] == 3000 and plan[("PO00650", "CPT0234")] == 780
    assert any("PO00900" in w for w in out["warnings"])                      # đơn nháp không nhận chỉ định


# ── xác nhận ──────────────────────────────────────────────────────────────────────────────
_SKIP = {"id", "po_id", "po_code", "code", "delivery_id", "ref_id", "po_item_id", "supplier_code", "supplier_name",
         "created_at", "updated_at", "created_by", "updated_by"}


def _rows(db, model, **flt):
    q = db.query(model).filter_by(**flt).order_by(model.id)
    return [{c.name: (float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
             for c in model.__table__.columns if c.name not in _SKIP for v in [getattr(r, c.name)]} for r in q]


def _effects(db, po):
    dels = db.query(PODelivery).filter(PODelivery.po_id == po.id).order_by(PODelivery.id).all()
    ids = [d.id for d in dels]
    return {"deliveries": _rows(db, PODelivery, po_id=po.id),
            "receipts": _rows(db, GoodsReceipt, po_id=po.id),
            "moves": [m for i in ids for m in _rows(db, InventoryMove, ref_id=i)],
            "payables": _rows(db, Payable, po_id=po.id),
            "items": [(float(i.qty_received), float(i.qty_remaining), i.line_status) for i in
                      db.query(POItem).filter(POItem.po_id == po.id).order_by(POItem.id)],
            "status": db.get(PurchaseOrder, po.id).status}


def _web_save(db, po, pcode, new: dict, uid, update_id=0):
    """Đúng cách màn web lưu: lấy `_out` (GET chi tiết), sửa / thêm lần giao, gửi lại nguyên đơn qua update_po."""
    data = _out(db, db.get(PurchaseOrder, po.id))
    items = []
    for it in data["items"]:
        dels = [dict(d) for d in it["deliveries"]]
        if it["product_code"] == pcode:
            if update_id:
                for d in dels:
                    if d["id"] == update_id:
                        d.update(new)
            else:
                dels.append({"delivery_no": len(dels) + 1, **new})
        items.append(POItemIn.model_validate({**it, "deliveries": [DeliveryIn.model_validate(d) for d in dels]}))
    po_service.update_po(db, po.id, POUpdate(items=items), uid)


def test_xac_nhan_ghi_nhu_man_web_va_giu_lan_giao_cu(kho, db):
    old = _receive(db, kho.po807, "CPT0234", 1000, date="2026-10-20")
    twin = _po(db, "PO09807", "2026-10-01", [("CPT0234", 3200), ("NAP0156", 3200)], supplier="NCCTWIN")
    db.commit()
    _receive(db, twin, "CPT0234", 1000, date="2026-10-20")
    out = _draft(kho, lines=[{"product_code": "CPT0234", "qty": 2200, "assign": [{"po_code": "PO00807", "qty": 2200}]}])
    code, oid = draft_create.create(db, kho.staff, "po_receipt", out["draft"])
    assert code == "PO00807" and oid == kho.po807.id
    _web_save(db, twin, "CPT0234", {"ship_qty": 2200, "received_qty": 2200, "received_date": "2026-11-06",
                                   "warehouse_code": "KHO1", "ship_unit": "Cái",
                                   "progress_note": "Phiếu xuất kho NCC số XK-0815 — ghi qua trợ lý AI"}, kho.staff.id)
    got, want = _effects(db, kho.po807), _effects(db, twin)
    assert got == want
    assert got["status"] == "partial" and len(got["deliveries"]) == 2 and len(got["receipts"]) == 2
    d_old = db.get(PODelivery, old.id)
    assert float(d_old.received_qty) == 1000 and d_old.received_date == "2026-10-20"      # lần cũ giữ nguyên
    assert float(_item(db, kho.po807, "CPT0234").qty_received) == 3200
    #  Nhật ký: ai ghi, qua trợ lý, từ nháp nào; sổ thay đổi của bot.
    from app.modules.assistant.change_model import AssistantChange
    from app.modules.audit.model import AuditLog

    log = db.query(AuditLog).filter(AuditLog.entity == "purchase_order", AuditLog.message.like("%trợ lý AI%")).one()
    assert log.created_by == kho.staff.id and out["draft"]["draft_ref"] in log.message and "XK-0815" in log.message
    ch = db.query(AssistantChange).filter(AssistantChange.entity == "purchase_order").one()
    assert ch.entity_id == kho.po807.id and ch.user_id == kho.staff.id
    #  Xác nhận lần hai cùng nháp: dòng đã đổi → chặn, không ghi đôi.
    with pytest.raises(draft_create.DraftError, match="sau lúc soạn nháp"):
        draft_create.create(db, kho.staff, "po_receipt", out["draft"])
    assert db.query(PODelivery).filter(PODelivery.po_id == kho.po807.id).count() == 2


def test_sua_lan_giao_dang_cho_sinh_hieu_ung_nhu_man_web(kho, db):
    pend = _receive(db, kho.po712, "NAP0169", 0, ship=504)
    keep = _receive(db, kho.po712, "CPT0234", 0, ship=500)
    twin = _po(db, "PO09712", "2026-09-10", [("CPT0234", 500), ("NAP0169", 500)], supplier="NCCTWIN")
    db.commit()
    tw_pend = _receive(db, twin, "NAP0169", 0, ship=504)
    _receive(db, twin, "CPT0234", 0, ship=500)
    out = _draft(kho, lines=[{"product_code": "NAP0169", "qty": 504}])
    (row,) = out["draft"]["rows"]
    assert row["op"] == "update" and row["delivery_id"] == pend.id               # lần đang chờ khớp số → điền lần đó
    draft_create.create(db, kho.staff, "po_receipt", out["draft"])
    _web_save(db, twin, "NAP0169", {"received_qty": 504, "received_date": "2026-11-06"}, kho.staff.id,
              update_id=tw_pend.id)
    assert _effects(db, kho.po712) == _effects(db, twin)
    d = db.get(PODelivery, pend.id)
    assert (float(d.received_qty), d.received_date, d.status, float(d.ship_qty)) == (504, "2026-11-06", "received", 504)
    k = db.get(PODelivery, keep.id)
    assert (float(k.received_qty), float(k.ship_qty), k.received_date) == (0, 500, "")    # lần khác không đổi
    assert db.query(GoodsReceipt).filter(GoodsReceipt.delivery_id == pend.id).count() == 1


def test_them_va_sua_trong_cung_mot_nhap(kho, db):
    pend = _receive(db, kho.po807, "NAP0156", 0, ship=3000)
    out = _draft(kho, lines=[{"product_code": "NAP0156", "qty": 3276,
                              "assign": [{"po_code": "PO00807", "qty": 3000, "delivery_no": 1}]},
                             {"product_code": "CPT0234", "qty": 500}])
    ops = sorted((r["po_code"], r["product_code"], r["op"], r["qty"]) for r in out["draft"]["rows"])
    #  Chai đi theo bộ với nắp NAP0156 của PO00807 (đơn bộ xét trước đơn cũ PO00650).
    assert ops == [("PO00807", "CPT0234", "add", 500), ("PO00807", "NAP0156", "add", 276),
                   ("PO00807", "NAP0156", "update", 3000)]
    code, _ = draft_create.create(db, kho.staff, "po_receipt", out["draft"])
    assert code == "PO00807"
    nap = db.query(PODelivery).filter(PODelivery.po_item_id == _item(db, kho.po807, "NAP0156").id) \
        .order_by(PODelivery.delivery_no).all()
    assert [(d.id == pend.id, d.delivery_no, float(d.received_qty)) for d in nap] == [(True, 1, 3000), (False, 2, 276)]
    assert float(_item(db, kho.po807, "NAP0156").qty_received) == 3276
    assert float(_item(db, kho.po807, "CPT0234").qty_received) == 500


def test_cong_mcp_nhom_tat_mac_dinh(kho, db):
    from app.modules.agent_hub import mcp_settings

    out = _draft(kho, lines=[{"product_code": "NAP0169", "qty": 10}])
    assert "po_open_lines" in mcp.READ_TOOLS and mcp.is_write_tool("draft_po_receipt")
    assert mcp_settings.GROUP_OF["draft_po_receipt"].key == "po_receipt"
    args = {"kind": "po_receipt", "draft": out["draft"]}
    assert mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "confirm_draft", args).get("denied")   # nhóm tắt mặc định
    assert mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_READ, "confirm_draft", args).get("denied")    # khóa chỉ đọc


def test_cong_mcp_xac_nhan(kho, db, mcp_all_groups):
    out = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "draft_po_receipt",
                        {"supplier": SUP, "slip_date": "06/11/2026", "lines": [{"product_code": "NAP0169", "qty": 10}]})
    assert out["draft"]["rows"][0]["received_date"] == "2026-11-06"
    assert mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_READ, "draft_po_receipt", {"supplier": SUP}).get("denied")
    ok = mcp.call_tool(db, kho.staff, mcp_keys.SCOPE_WRITE, "confirm_draft", {"kind": "po_receipt", "draft": out["draft"]})
    assert ok["ok"] and ok["code"] == "PO00712" and any("NAP0169: đã nhận 10 / đặt 500" in x for x in ok["details"])
