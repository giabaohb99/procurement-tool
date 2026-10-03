"""bao-CR-583 — thu mua cập nhật thông tin PHƯƠNG ÁN 0 trên màn chọn, kèm «Khôi phục ban đầu».

Đại ca chốt 03/10/2026: «cho nhân sự thu mua có thể cập nhật thông tin trên phương án 0, nhưng
phải có nút trả về tình trạng đầu tiên của nó». Phương án 0 sinh từ dòng yêu cầu nên thường
thiếu mã VTBB / NCC / giá thật; mà lập đơn đọc mã ở DÒNG (bao-CR-568), nên phương án 0 đang
được chọn đổi mã thì dòng đổi theo.
"""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.product.model import Product
from app.modules.purchase_request import controller as C
from app.modules.purchase_request import option_service as OS
from app.modules.purchase_request import service as SV
from app.modules.purchase_request.constants import PR_OPT_MANUAL, PR_OPT_ORIGINAL, PR_OPT_SURVEY
from app.modules.purchase_request.model import (PurchaseRequest, PurchaseRequestItem,
                                                PurchaseRequestItemOption)
from app.modules.purchase_request.schema import PROptionDetailsIn
from app.modules.user.model import User


@pytest.fixture(autouse=True)
def _options_on(monkeypatch):
    monkeypatch.setattr(OS, "options_enabled", lambda: True)


def _pr(db, seed, code=""):
    pr = PurchaseRequest(code="PYC-CR583", company_id=seed.company_id, requester="Người YC",
                         requester_id=seed.emp_req_id, department="Phòng Test", department_id=seed.dept_id,
                         status="dispatched", request_date="2026-10-03",
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(pr)
    db.flush()
    it = PurchaseRequestItem(pr_id=pr.id, product_code=code, product_name="Nhãn decal", item_group="Nhãn",
                             qty=10, unit="cuộn", price=1000, vat_pct=8, amount=10800,
                             assignee=seed.emp_nstm_code, created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(it)
    db.commit()
    OS.ensure_option_zero(db, pr)
    zero = (db.query(PurchaseRequestItemOption)
            .filter(PurchaseRequestItemOption.pr_item_id == it.id,
                    PurchaseRequestItemOption.source == PR_OPT_ORIGINAL).one())
    return pr, it, zero


def _product(db, code="SP-CR583", active=True):
    db.add(Product(code=code, name=f"Hàng {code}", item_group="Nhãn", unit="cuộn", is_active=active,
                   created_by=0, updated_by=0))
    db.commit()
    return code


def _nstm(db, seed, cap_quyen, supplier_read=True):
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="assigned", read=True, write=True)
    if supplier_read:
        cap_quyen(seed.u_nstm_id, "supplier", scope="all", read=True)
    return db.get(User, seed.u_nstm_id)


def _update(db, pr, it, zero, user, **fields):
    return C.update_option_details(pr.id, it.id, zero.id, PROptionDetailsIn(**fields), db=db, user=user)


def test_purchasing_fills_every_field_of_option_zero_and_line_code_follows(db, seed, cap_quyen):
    pr, it, zero = _pr(db, seed)
    code = _product(db)
    assert zero.is_chosen  # phương án 0 được chọn sẵn

    _update(db, pr, it, zero, _nstm(db, seed, cap_quyen), snap_product_name="Nhãn decal 5x7",
            snap_internal_code=code, supplier_name="CÔNG TY IN B", snap_price_by_volume=1250,
            snap_quote_unit="cuộn", snap_moq=100, snap_vat=10, snap_origin="Việt Nam",
            snap_delivery_time="7 ngày", snap_delivery_place="Kho Long An", snap_shipping_cost=50000,
            snap_sample_ready=True, nstm_note="Giá tốt nhất")

    db.refresh(zero)
    db.refresh(it)
    assert (zero.snap_product_name, zero.snap_internal_code, zero.supplier_name) == \
        ("Nhãn decal 5x7", code, "CÔNG TY IN B")
    assert float(zero.snap_price_by_volume) == 1250 and float(zero.snap_vat) == 10
    assert zero.snap_sample_ready is True and zero.nstm_note == "Giá tốt nhất"
    assert it.product_code == code  # lập đơn đọc mã ở dòng


def test_unknown_or_inactive_code_is_rejected_and_nothing_changes(db, seed, cap_quyen):
    pr, it, zero = _pr(db, seed)
    _product(db, "SP-NGUNG", active=False)
    user = _nstm(db, seed, cap_quyen)
    for bad in ("SP-KHONG-CO", "SP-NGUNG"):
        with pytest.raises(HTTPException) as e:
            _update(db, pr, it, zero, user, snap_internal_code=bad, snap_price_by_volume=9999)
        assert e.value.status_code == 400
    db.refresh(zero)
    db.refresh(it)
    assert zero.snap_internal_code == "" and float(zero.snap_price_by_volume) == 1000
    assert it.product_code == ""


def test_code_change_blocked_once_the_line_is_on_an_order(db, seed, cap_quyen):
    pr, it, zero = _pr(db, seed, code="SP-CU")
    it.line_status = SV.LINE_STATUS_NOT_ORDERED
    db.commit()
    code = _product(db)
    with pytest.raises(HTTPException) as e:
        _update(db, pr, it, zero, _nstm(db, seed, cap_quyen), snap_internal_code=code)
    assert "đã lên đơn" in e.value.detail
    db.refresh(it)
    assert it.product_code == "SP-CU"


def test_code_on_an_unchosen_option_zero_leaves_the_line_alone(db, seed, cap_quyen):
    pr, it, zero = _pr(db, seed)
    zero.is_chosen = False
    db.commit()
    code = _product(db)
    _update(db, pr, it, zero, _nstm(db, seed, cap_quyen), snap_internal_code=code)
    db.refresh(it)
    assert it.product_code == ""


def test_reset_brings_option_zero_back_to_the_request_line(db, seed, cap_quyen):
    pr, it, zero = _pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    _update(db, pr, it, zero, user, snap_product_name="Đã sửa", supplier_name="NCC X",
            snap_price_by_volume=5, snap_moq=7, snap_delivery_place="Đâu đó", nstm_note="ghi chú",
            snap_sample_ready=True, snap_vat=0)

    C.reset_option_zero(pr.id, it.id, zero.id, db=db, user=user)

    db.refresh(zero)
    assert zero.snap_product_name == "Nhãn decal" and zero.snap_quote_unit == "cuộn"
    assert float(zero.snap_price_by_volume) == 1000 and float(zero.snap_vat) == 8
    assert (zero.supplier_code, zero.supplier_name) == ("", "")
    assert float(zero.snap_moq) == 0 and zero.snap_delivery_place == "" and zero.nstm_note == ""
    assert zero.snap_sample_ready is False
    assert zero.is_chosen  # khôi phục không đụng việc chọn


def test_supplier_can_be_cleared_by_sending_two_blanks(db, seed, cap_quyen):
    pr, it, zero = _pr(db, seed)
    user = _nstm(db, seed, cap_quyen)
    _update(db, pr, it, zero, user, supplier_name="NCC X")
    _update(db, pr, it, zero, user, supplier_code="", supplier_name="")
    db.refresh(zero)
    assert (zero.supplier_code, zero.supplier_name) == ("", "")


def _extra_option(db, it, source, label="Phương án 1"):
    o = PurchaseRequestItemOption(pr_item_id=it.id, source=source, public_id=1, display_label=label,
                                  supplier_name="NCC nhập tay", snap_price_by_volume=900,
                                  created_by=0, updated_by=0)
    db.add(o)
    db.commit()
    return o


def test_manual_option_is_edited_like_option_zero(db, seed, cap_quyen):
    #  Đại ca: «phương án 0 xem như phương án nhập tay và chỉnh sửa lại được».
    pr, it, _zero = _pr(db, seed)
    manual = _extra_option(db, it, PR_OPT_MANUAL)
    _update(db, pr, it, manual, _nstm(db, seed, cap_quyen), snap_product_name="Nhãn khác",
            snap_price_by_volume=950, snap_delivery_time="3 ngày")
    db.refresh(manual)
    assert (manual.snap_product_name, float(manual.snap_price_by_volume), manual.snap_delivery_time) ==         ("Nhãn khác", 950, "3 ngày")


def test_manual_option_cannot_lose_its_supplier(db, seed, cap_quyen):
    pr, it, _zero = _pr(db, seed)
    manual = _extra_option(db, it, PR_OPT_MANUAL)
    with pytest.raises(HTTPException) as e:
        _update(db, pr, it, manual, _nstm(db, seed, cap_quyen), supplier_code="", supplier_name="")
    assert e.value.status_code == 400
    db.refresh(manual)
    assert manual.supplier_name == "NCC nhập tay"


def test_survey_option_is_refused_and_only_option_zero_can_be_reset(db, seed, cap_quyen):
    pr, it, _zero = _pr(db, seed)
    survey = _extra_option(db, it, PR_OPT_SURVEY, "Phương án 2")
    manual = _extra_option(db, it, PR_OPT_MANUAL, "Phương án 3")
    user = _nstm(db, seed, cap_quyen)
    for call in (lambda: _update(db, pr, it, survey, user, snap_price_by_volume=1),
                 lambda: C.reset_option_zero(pr.id, it.id, manual.id, db=db, user=user),
                 lambda: C.reset_option_zero(pr.id, it.id, survey.id, db=db, user=user)):
        with pytest.raises(HTTPException) as e:
            call()
        assert e.value.status_code == 400


def test_needs_supplier_read(db, seed, cap_quyen):
    pr, it, zero = _pr(db, seed)
    user = _nstm(db, seed, cap_quyen, supplier_read=False)
    for call in (lambda: _update(db, pr, it, zero, user, snap_price_by_volume=1),
                 lambda: C.reset_option_zero(pr.id, it.id, zero.id, db=db, user=user)):
        with pytest.raises(HTTPException) as e:
            call()
        assert e.value.status_code == 403


def test_still_editable_after_the_line_is_marked_done(db, seed, cap_quyen):
    #  Khe nới H.10.4: thu mua điền NCC / giá trên màn chọn kể cả khi NSTM đã chốt dòng.
    pr, it, zero = _pr(db, seed)
    it.options_done = True
    db.commit()
    _update(db, pr, it, zero, _nstm(db, seed, cap_quyen), snap_price_by_volume=1300)
    db.refresh(zero)
    assert float(zero.snap_price_by_volume) == 1300


@pytest.mark.parametrize("field,length", [("snap_internal_code", 51), ("snap_product_name", 256),
                                          ("snap_quote_unit", 26), ("supplier_name", 256)])
def test_schema_rejects_values_longer_than_the_column(field, length):
    with pytest.raises(ValidationError):
        PROptionDetailsIn(**{field: "x" * length})


def test_schema_rejects_negative_numbers_and_full_vat():
    for kwargs in ({"snap_price_by_volume": -1}, {"snap_moq": -1}, {"snap_shipping_cost": -1},
                   {"snap_vat": 100}, {"snap_vat": -1}):
        with pytest.raises(ValidationError):
            PROptionDetailsIn(**kwargs)
