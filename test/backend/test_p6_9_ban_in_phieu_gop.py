"""P6-9 (bao-CR-287) — hai bản in của luồng gộp chứng từ (doc/erp/12 §P6-9).

Luật cần khóa:

1. Bản in NGƯỜI YÊU CẦU (`GET /{sid}/print`): dòng ĐÃ CHỐT in NCC của phương án đã
   chốt (source `confirmed`, kèm giá/VAT/giao hàng snap); dòng CHƯA chốt in NCC người
   yêu cầu tự nhập trên đầu phiếu (source `requester`) và KHÔNG lộ giá phương án —
   luật ẩn NCC khảo sát chỉ mở đúng phương án đã khóa.
2. Dòng đánh dấu ĐÃ CHỐT nhưng mất phương án chọn (dữ liệu lệch) phải rơi về nhánh
   `requester`, không được nổ hay lộ NCC rỗng nửa vời.
3. Ngoài phạm vi dữ liệu → 403 (bản in không phải cửa sau vượt `apply_scope`).
4. Bản in THU MUA (`/print-purchasing`): gác `supplier.read` → thiếu quyền là 403;
   có quyền thì gom dòng đã chốt THEO TỪNG NCC + kèm danh sách ĐMH đã sinh từ phiếu.
"""
import json

import pytest
from fastapi import HTTPException

from app.modules.survey_request import controller
from app.modules.survey_request.model import (LS_CONFIRMED, SurveyRequest,
                                              SurveyRequestLine,
                                              SurveyRequestOption,
                                              SurveyRequestPo)
from app.modules.user.model import User


def _sr(db, user_id: int, code: str = "YCBG-P69", **kw):
    s = SurveyRequest(code=code, status="survey_done", created_by=user_id, **kw)
    db.add(s)
    db.commit()
    return s


def _line(db, sid: int, **kw):
    ln = SurveyRequestLine(survey_request_id=sid,
                           item_group=kw.pop("item_group", "Thùng"),
                           request_qty=kw.pop("request_qty", 5), **kw)
    db.add(ln)
    db.commit()
    return ln


def _opt(db, line_id: int, public_id: int = 1, chosen: bool = True, **kw):
    o = SurveyRequestOption(survey_request_line_id=line_id, public_id=public_id,
                            supplier_code=kw.pop("supplier", "NCC-A"),
                            is_chosen=chosen, **kw)
    db.add(o)
    db.commit()
    return o


def _data(res) -> dict:
    return json.loads(res.body)["data"]


@pytest.fixture
def mo_pham_vi(monkeypatch):
    """Bản in người YC: bỏ qua điều kiện phạm vi để test tập trung vào luật cột NCC."""
    monkeypatch.setattr(controller, "_scope_with_named_head", lambda u, p: None)


# ───────────────────── bản in NGƯỜI YÊU CẦU: cột NCC ─────────────────────

def test_dong_da_chot_in_ncc_phuong_an(db, seed, mo_pham_vi):
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id, suggested_supplier="NCC đề xuất X")
    ln = _line(db, s.id, line_status=LS_CONFIRMED)
    _opt(db, ln.id, supplier="NCC-A", supplier_name="Công ty A",
         snap_price_by_volume=12000, snap_vat=8, snap_delivery_time="3 ngày")

    out = _data(controller.print_view_(s.id, db=db, user=user))

    row = out["lines"][0]
    assert row["print_supplier_source"] == "confirmed"
    assert row["print_supplier_name"] == "Công ty A"
    assert row["chosen_price"] == 12000
    assert row["chosen_vat"] == 8
    assert row["chosen_delivery_time"] == "3 ngày"


def test_dong_chua_chot_in_ncc_de_xuat_va_giau_gia(db, seed, mo_pham_vi):
    """Dòng chưa chốt: option ĐANG CHỌN (chưa khóa) tuyệt đối không lộ ra bản in."""
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id, suggested_supplier="NCC đề xuất X")
    ln = _line(db, s.id)  # line_status="" — chưa chốt
    _opt(db, ln.id, supplier="NCC-BI-MAT", supplier_name="NCC phải giấu",
         snap_price_by_volume=99999)

    out = _data(controller.print_view_(s.id, db=db, user=user))

    row = out["lines"][0]
    assert row["print_supplier_source"] == "requester"
    assert row["print_supplier_name"] == "NCC đề xuất X"
    assert row["chosen_price"] == 0, "giá phương án chưa khóa không được rò ra bản in"
    assert "NCC phải giấu" not in json.dumps(out, ensure_ascii=False)


def test_dong_chot_nhung_mat_phuong_an_roi_ve_requester(db, seed, mo_pham_vi):
    """Dữ liệu lệch (đánh dấu chốt mà không còn option is_chosen) không được nổ."""
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id)  # suggested_supplier rỗng luôn
    _line(db, s.id, line_status=LS_CONFIRMED)  # không tạo option nào

    out = _data(controller.print_view_(s.id, db=db, user=user))

    row = out["lines"][0]
    assert row["print_supplier_source"] == "requester"
    assert row["print_supplier_name"] == ""
    assert row["chosen_price"] == 0


def test_ban_in_ngoai_pham_vi_403(db, seed, monkeypatch):
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id)
    monkeypatch.setattr(controller, "_scope_with_named_head",
                        lambda u, p: SurveyRequest.id == -1)

    with pytest.raises(HTTPException) as e:
        controller.print_view_(s.id, db=db, user=user)
    assert e.value.status_code == 403


# ───────────────────── bản in THU MUA: quyền + gom NCC ─────────────────────

def test_ban_in_thu_mua_thieu_quyen_ncc_403(db, seed, monkeypatch):
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id)
    monkeypatch.setattr(controller, "user_has_permission", lambda *a, **k: False)

    with pytest.raises(HTTPException) as e:
        controller.print_purchasing_view_(s.id, db=db, user=user)
    assert e.value.status_code == 403


def test_ban_in_thu_mua_gom_theo_tung_ncc(db, seed, monkeypatch):
    monkeypatch.setattr(controller, "user_has_permission", lambda *a, **k: True)
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id)
    # 2 dòng chốt về NCC-A, 1 dòng chốt về NCC-B, 1 dòng chưa chốt (phải bị loại)
    ln1 = _line(db, s.id, item_group="Thùng", line_status=LS_CONFIRMED)
    ln2 = _line(db, s.id, item_group="Băng keo", line_status=LS_CONFIRMED)
    ln3 = _line(db, s.id, item_group="Màng co", line_status=LS_CONFIRMED)
    ln4 = _line(db, s.id, item_group="Chưa chốt")
    _opt(db, ln1.id, supplier="NCC-A", supplier_name="Công ty A",
         snap_price_by_volume=1000, snap_vat=8, snap_product_name="Thùng A5",
         snap_quote_unit="cái")
    _opt(db, ln2.id, supplier="NCC-A", supplier_name="Công ty A",
         snap_price_by_volume=2000)
    _opt(db, ln3.id, supplier="NCC-B", supplier_name="Công ty B",
         snap_price_by_volume=3000)
    _opt(db, ln4.id, supplier="NCC-C", supplier_name="Không được lộ")

    out = _data(controller.print_purchasing_view_(s.id, db=db, user=user))

    by_code = {g["supplier_code"]: g for g in out["groups"]}
    assert set(by_code) == {"NCC-A", "NCC-B"}, "dòng chưa chốt không được vào nhóm nào"
    assert len(by_code["NCC-A"]["lines"]) == 2
    assert len(by_code["NCC-B"]["lines"]) == 1
    first = by_code["NCC-A"]["lines"][0]
    assert first["chosen_price"] == 1000 and first["chosen_vat"] == 8
    assert first["chosen_product_name"] == "Thùng A5"
    assert first["chosen_quote_unit"] == "cái"
    assert "Không được lộ" not in json.dumps(out, ensure_ascii=False)


def test_ban_in_thu_mua_kem_danh_sach_dmh(db, seed, monkeypatch):
    from app.modules.purchase_order.model import PurchaseOrder
    monkeypatch.setattr(controller, "user_has_permission", lambda *a, **k: True)
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id)
    ln = _line(db, s.id, line_status=LS_CONFIRMED)
    o = _opt(db, ln.id, supplier="NCC-A", supplier_name="Công ty A")
    po = PurchaseOrder(code="PO-P69", supplier_code="NCC-A",
                       supplier_name="Công ty A", status="draft")
    po_khac = PurchaseOrder(code="PO-KHAC", supplier_code="NCC-Z",
                            supplier_name="Phiếu khác", status="draft")
    db.add_all([po, po_khac])
    db.commit()
    db.add(SurveyRequestPo(survey_request_id=s.id, survey_request_line_id=ln.id,
                           option_id=o.id, po_id=po.id, po_code=po.code))
    db.commit()

    out = _data(controller.print_purchasing_view_(s.id, db=db, user=user))

    assert [p["code"] for p in out["purchase_orders"]] == ["PO-P69"], \
        "chỉ liệt kê ĐMH sinh từ CHÍNH phiếu này"
    assert out["purchase_orders"][0]["supplier_name"] == "Công ty A"
    assert out["purchase_orders"][0]["status"] == "draft"
