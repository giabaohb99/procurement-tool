"""bao-CR-538 — nới các ô chữ đoạn văn thu mua theo luật đại ca chốt: «255 thêm 100», công nợ 50 → 100.

Sinh ra sau sự cố D30D24DF (nspt_note tràn VARCHAR(255) → lỗi 500). SQLite KHÔNG ép độ dài
VARCHAR, nên kiểm ở tầng MODEL (trần cột) và SCHEMA (max_length khớp trần): thiếu max_length là
lỗi 500 thay vì 422 (luật duoc-CR-316).
"""
import pytest
from pydantic import ValidationError

from app.modules.purchase_order.cost_type import POCostTypeCreate, POCostTypeUpdate
from app.modules.purchase_order.model import POCost, POCostType, POItem
from app.modules.purchase_order.schema import POImportCostIn, POItemIn
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import PRCreate, PRItemIn, PRUpdate
from app.modules.survey.model import Survey, SurveyProductLine, SurveySupplierLine
from app.modules.survey.schema import ProductLineIn, SupplierLineIn
from app.modules.survey_request.model import SurveyRequest
from app.modules.survey_request.schema import SurveyRequestUpdate

COLUMNS = [
    (SurveySupplierLine, "debt_policy", 100), (SurveyProductLine, "debt_policy", 100),
    (SurveyProductLine, "active_ingredient", 355), (SurveyProductLine, "shipping_policy", 355),
    (SurveySupplierLine, "delivery_policy", 355), (SurveySupplierLine, "reliability", 355),
    (SurveySupplierLine, "production_tech", 355), (SurveySupplierLine, "invoice_policy", 355),
    (SurveySupplierLine, "defect_return", 355), (SurveySupplierLine, "source_of_information", 355),
    (SurveyRequest, "purpose", 355), (PurchaseRequest, "purpose", 355),
    (PurchaseRequestItem, "note", 355), (POItem, "note", 355), (POCost, "description", 355),
    (Survey, "main_content", 600), (POCostType, "note", 600),
]


@pytest.mark.parametrize("model,column,length", COLUMNS, ids=lambda v: getattr(v, "__name__", str(v)))
def test_column_widened(model, column, length):
    assert model.__table__.c[column].type.length == length


SCHEMAS = [
    (SupplierLineIn, "debt_policy", 100), (ProductLineIn, "debt_policy", 100),
    (ProductLineIn, "active_ingredient", 355), (ProductLineIn, "shipping_policy", 355),
    (SupplierLineIn, "delivery_policy", 355), (SupplierLineIn, "reliability", 355),
    (SupplierLineIn, "production_tech", 355), (SupplierLineIn, "invoice_policy", 355),
    (SupplierLineIn, "defect_return", 355), (SupplierLineIn, "source_of_information", 355),
    (SurveyRequestUpdate, "purpose", 355), (PRUpdate, "purpose", 355), (PRItemIn, "note", 355),
    (POItemIn, "note", 355), (POImportCostIn, "description", 355), (POCostTypeUpdate, "note", 600),
]


@pytest.mark.parametrize("schema,field,length", SCHEMAS, ids=lambda v: getattr(v, "__name__", str(v)))
def test_schema_accepts_new_limit_and_rejects_beyond(schema, field, length):
    schema.model_validate({field: "x" * length}, strict=False) if not _required(schema) else None
    with pytest.raises(ValidationError):
        schema.model_validate({field: "x" * (length + 1)})


def _required(schema) -> bool:
    return any(f.is_required() for f in schema.model_fields.values())


def test_create_schemas_carry_same_limits():
    for schema, field, length in [(PRCreate, "purpose", 355), (POCostTypeCreate, "note", 600)]:
        meta = schema.model_fields[field].metadata
        assert any(getattr(m, "max_length", None) == length for m in meta), (schema.__name__, field)
