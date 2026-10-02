"""bao-CR-563 — «Trả về» phiếu khảo sát dọn những gì phiếu đã đẩy đi.

Lỗ có thật sau bao-CR-554 (cho trả về cả phiếu ĐÃ DUYỆT): dòng được duyệt là phương án tự gắn
sang Yêu cầu báo giá; trả về mà để nguyên thì phương án cũ ở lại, nhân viên sửa phiếu là dòng
bị xóa rồi tạo lại nên phương án trỏ vào dòng đã mất, duyệt lại thì gắn trùng — và dòng sửa
giá xong vẫn «Đã duyệt». Đại ca chốt 02/10/2026: trạng thái vẫn là Bị trả lại, sửa được như Nháp.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.modules.purchase_request.model import PurchaseRequestItemOption
from app.modules.purchase_request.schema import RejectIn
from app.modules.survey import controller as sv_ctl
from app.modules.survey import service as sv_service
from app.modules.survey.model import Survey, SurveyProductLine, SurveySupplierLine
from app.modules.survey.schema import SurveyUpdate
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine, SurveyRequestOption

USER = SimpleNamespace(id=1)


@pytest.fixture(autouse=True)
def _world(monkeypatch, cap_quyen):
    monkeypatch.setattr(sv_ctl, "trigger_notification", lambda **kw: None)
    for entity in ("survey", "survey_request", "purchase_request"):
        cap_quyen(USER.id, entity, scope="all", read=True, write=True, approve=True, cancel=True)


def _survey(db, status="approved", product_states=("Đã duyệt", "Đã duyệt"), supplier_states=("Đã duyệt",),
            code="KS-563"):
    s = Survey(code=code, survey_type="combined", status=status, item_group="Nhãn")
    db.add(s)
    db.flush()
    products = []
    for state in product_states:
        ln = SurveyProductLine(survey_id=s.id, supplier_code="NX", line_approve=state)
        db.add(ln)
        products.append(ln)
    for state in supplier_states:
        db.add(SurveySupplierLine(survey_id=s.id, supplier_code="NX", line_approve=state))
    db.commit()
    db.refresh(s)
    return s, products


def _ycbg_line(db, code="YCBG-563"):
    sr = SurveyRequest(code=code, department="Phòng Test", status="processing")
    db.add(sr)
    db.flush()
    line = SurveyRequestLine(survey_request_id=sr.id)
    db.add(line)
    db.commit()
    return line


def _option(db, line, product_line, chosen=False):
    o = SurveyRequestOption(survey_request_line_id=line.id, product_survey_line_id=product_line.id,
                            is_chosen=chosen, snap_product_name="Nhãn A")
    db.add(o)
    db.commit()
    return o


def _return(db, s, reason="Giá chưa đúng"):
    sv_ctl.reject_(s.id, RejectIn(reason=reason), BackgroundTasks(), db=db, user=USER)
    db.refresh(s)
    return s


def _options_of(db, product_lines):
    ids = [ln.id for ln in product_lines]
    return db.query(SurveyRequestOption).filter(SurveyRequestOption.product_survey_line_id.in_(ids)).count()


def test_return_removes_pushed_options_and_reopens_every_decided_line(db):
    s, products = _survey(db, product_states=("Đã duyệt", "Không duyệt", "Thiếu thông tin"))
    line = _ycbg_line(db)
    _option(db, line, products[0])
    _option(db, line, products[1])

    s = _return(db, s)

    assert s.status == "rejected"
    assert _options_of(db, products) == 0
    states = [ln.line_approve for ln in sv_service.product_lines_of(db, s.id)]
    assert states == ["Chờ duyệt", "Chờ duyệt", "Thiếu thông tin"]
    assert [ln.line_approve for ln in sv_service.supplier_lines_of(db, s.id)] == ["Chờ duyệt"]
    assert "Giá chưa đúng" in s.approve_note and "gỡ 2 phương án" in s.approve_note


def test_chosen_option_blocks_return_and_changes_nothing(db):
    s, products = _survey(db)
    line = _ycbg_line(db)
    _option(db, line, products[0], chosen=True)
    _option(db, line, products[1])

    with pytest.raises(HTTPException) as error:
        _return(db, s)

    assert error.value.status_code == 400 and "CHỌN" in error.value.detail
    db.refresh(s)
    assert s.status == "approved"
    assert _options_of(db, products) == 2
    assert all(ln.line_approve == "Đã duyệt" for ln in sv_service.product_lines_of(db, s.id))


def test_option_already_in_purchase_request_blocks_return(db):
    s, products = _survey(db)
    db.add(PurchaseRequestItemOption(pr_item_id=99, product_survey_line_id=products[1].id))
    db.commit()

    with pytest.raises(HTTPException) as error:
        _return(db, s)

    assert error.value.status_code == 400 and "Yêu cầu mua hàng" in error.value.detail
    db.refresh(s)
    assert s.status == "approved"


def test_options_from_other_surveys_are_left_alone(db):
    s, products = _survey(db, code="KS-563-A")
    _other, other_products = _survey(db, code="KS-563-B")
    line = _ycbg_line(db)
    _option(db, line, products[0])
    _option(db, line, other_products[0], chosen=True)

    _return(db, s)

    assert _options_of(db, products) == 0
    assert _options_of(db, other_products) == 1


def test_returning_a_submitted_survey_also_reopens_lines(db):
    #  Duyệt từng dòng lúc phiếu còn chờ duyệt cũng đã đẩy phương án đi — cùng một lỗ.
    s, products = _survey(db, status="submitted", product_states=("Đã duyệt", "Chờ duyệt"))
    _option(db, _ycbg_line(db), products[0])

    s = _return(db, s)

    assert s.status == "rejected"
    assert _options_of(db, products) == 0
    assert [ln.line_approve for ln in sv_service.product_lines_of(db, s.id)] == ["Chờ duyệt", "Chờ duyệt"]


def test_return_without_any_option_keeps_reason_untouched(db):
    s, _products = _survey(db, product_states=())
    s = _return(db, s, reason="Thiếu báo giá thứ hai")
    assert s.approve_note == "Thiếu báo giá thứ hai"


def test_returned_survey_is_editable_like_a_draft(db):
    s, _products = _survey(db)
    _return(db, s)

    updated = sv_service.update_survey(db, s.id, SurveyUpdate(main_content="Sửa lại giá"), USER.id)

    assert updated.main_content == "Sửa lại giá"
    assert updated.status == "rejected"


def test_returned_survey_must_be_reapproved_line_by_line(db):
    #  Dòng đã về «Chờ duyệt» nên duyệt cả phiếu ngay sau khi gửi lại phải bị chặn.
    s, _products = _survey(db)
    _return(db, s)
    s.status = "submitted"
    db.commit()

    with pytest.raises(HTTPException) as error:
        sv_ctl.approve_(s.id, BackgroundTasks(), db=db, user=USER)
    assert error.value.status_code == 400
