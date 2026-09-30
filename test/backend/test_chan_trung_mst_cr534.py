"""bao-CR-534 — chặn tạo/sửa công ty trùng mã số thuế (đại ca chốt 30/09/2026: chặn hẳn).

Sinh ra sau bao-CR-532: hai dòng «DEGO Holding» cùng MST, ~1.340 dòng chứng từ prod chia đôi giữa
hai dòng, phải viết script gộp. Hệ chỉ chặn trùng ``code`` — mà ``code`` ai cũng tự đặt được.
"""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.company.model import Company
from app.modules.company.schema import CompanyCreate, CompanyUpdate
from app.modules.company.service import create_company, update_company

MST = "1801722464"


def _new(db, name, tax_code, code=None):
    return create_company(db, CompanyCreate(name=name, code=code or name.replace(" ", "")[:20],
                                            tax_code=tax_code), user_id=1)


@pytest.mark.parametrize("dup", [MST, f" {MST} ", "1801 722 464", "1801722464\t"])
def test_create_blocks_the_same_tax_code_whatever_the_spacing(db, dup):
    _new(db, "DEGO Holding", MST, code="DEGO")
    with pytest.raises(HTTPException) as e:
        _new(db, "DEGO Holding 2", dup, code="DEGO HOLDING")
    assert e.value.status_code == 400
    #  Câu báo phải chỉ ra công ty nào đang giữ mã đó — không thì người tạo không biết sửa ở đâu.
    assert "DEGO Holding" in e.value.detail and "DEGO" in e.value.detail
    assert db.query(Company).count() == 1


def test_a_branch_tax_code_is_a_different_legal_entity(db):
    """``-001`` là mã chi nhánh — khác hẳn công ty mẹ, phải tạo được."""
    _new(db, "Cong ty me", "0301234567", code="ME")
    _new(db, "Chi nhanh 1", "0301234567-001", code="CN1")
    assert db.query(Company).count() == 2


def test_empty_tax_code_is_never_a_duplicate(db):
    _new(db, "Chua co MST 1", "", code="A1")
    _new(db, "Chua co MST 2", "   ", code="A2")
    assert db.query(Company).count() == 2


def test_create_stores_the_trimmed_tax_code(db):
    c = _new(db, "Cong ty", f"  {MST}  ", code="CT")
    assert c.tax_code == MST


def test_update_blocks_moving_onto_another_companys_tax_code(db):
    _new(db, "DEGO Holding", MST, code="DEGO")
    other = _new(db, "Cong ty khac", "0309999999", code="KHAC")
    with pytest.raises(HTTPException) as e:
        update_company(db, other.id, CompanyUpdate(tax_code=f" {MST} "), user_id=1)
    assert e.value.status_code == 400
    assert db.get(Company, other.id).tax_code == "0309999999"


def test_update_with_the_form_resending_its_own_tax_code_is_fine(db):
    """Màn sửa gửi lại MỌI ô mỗi lần lưu — gửi lại chính MST của mình không được coi là trùng."""
    c = _new(db, "DEGO Holding", MST, code="DEGO")
    update_company(db, c.id, CompanyUpdate(tax_code=f"{MST} ", address="Cần Thơ"), user_id=1)
    assert db.get(Company, c.id).address == "Cần Thơ"


def test_legacy_duplicates_stay_editable_as_long_as_the_tax_code_is_untouched(db):
    """Dữ liệu cũ đã trùng (nạp tay, trước khi có chốt) không được bị khóa luôn việc sửa."""
    a = Company(code="OLD1", name="Cu 1", tax_code=MST, is_active=True)
    b = Company(code="OLD2", name="Cu 2", tax_code=MST, is_active=True)
    db.add_all([a, b])
    db.commit()

    update_company(db, b.id, CompanyUpdate(tax_code=MST, address="Địa chỉ mới"), user_id=1)
    assert db.get(Company, b.id).address == "Địa chỉ mới"


def test_clearing_the_tax_code_is_allowed(db):
    c = _new(db, "Cong ty", MST, code="CT")
    update_company(db, c.id, CompanyUpdate(tax_code=""), user_id=1)
    assert db.get(Company, c.id).tax_code == ""


@pytest.mark.parametrize("schema", [CompanyCreate, CompanyUpdate])
def test_a_tax_code_longer_than_the_column_is_rejected_before_the_database(schema):
    """Luật duoc-CR-316: thiếu trần thì MySQL mới là chỗ phản đối — ra 500 thay vì 422."""
    kwargs = {"tax_code": "1" * 26}
    if schema is CompanyCreate:
        kwargs["name"] = "Cong ty"
    with pytest.raises(ValidationError):
        schema(**kwargs)
