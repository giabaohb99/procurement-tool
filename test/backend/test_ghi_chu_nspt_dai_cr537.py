"""bao-CR-537 — «Ghi chú NSPT» dài hơn 255 ký tự không còn làm lưu phiếu khảo sát báo lỗi 500.

Mã sự cố D30D24DF trên prod 30/09: ghi chú 263 ký tự, cột VARCHAR(255). SQLite không ép độ dài
VARCHAR (xem CLAUDE.md), nên kiểm ở tầng MODEL (kiểu cột) và SCHEMA (trần 5000).
"""
import pytest
from pydantic import ValidationError
from sqlalchemy import Text

from app.modules.survey import schema
from app.modules.survey.model import SurveyProductLine, SurveySupplierLine

LONG_NOTE = "NCC tự sản xuất chai nhôm, nên nguồn cung ổn định hơn. " * 5   # ~280 ký tự


@pytest.mark.parametrize("model", [SurveySupplierLine, SurveyProductLine])
def test_column_is_text(model):
    assert isinstance(model.__table__.c.nspt_note.type, Text)


def _line_schemas():
    return [cls for cls in vars(schema).values()
            if isinstance(cls, type) and hasattr(cls, "model_fields") and "nspt_note" in cls.model_fields]


def test_schemas_accept_long_note_and_cap_at_5000():
    classes = _line_schemas()
    assert len(classes) >= 2
    for cls in classes:
        field = cls.model_fields["nspt_note"]
        assert any(getattr(m, "max_length", None) == 5000 for m in field.metadata), cls.__name__
    cls = classes[0]
    required = {k: v for k, v in cls.model_fields.items() if v.is_required()}
    assert not required, f"{cls.__name__} có trường bắt buộc {list(required)}"
    assert cls(nspt_note=LONG_NOTE).nspt_note == LONG_NOTE
    with pytest.raises(ValidationError):
        cls(nspt_note="x" * 5001)
