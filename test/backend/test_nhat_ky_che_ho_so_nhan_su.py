"""Nhật ký hệ thống KHÔNG được chép nhóm nhạy cảm của hồ sơ nhân sự (HRM §7.10, 02/10/2026).

Trước bản vá: `PATCH /api/employees/{id}` lưu nguyên văn số tài khoản, số CCCD, mã số
thuế vào `tab_request_log.request_body`, và lớp ORM ghi giá trị trước/sau của đúng các
cột đó vào `tab_change_log`. Ai có quyền xem nhật ký là đọc được — không cần khóa
`employee_sensitive`, đi vòng qua chốt mà `employee/sensitive.py` dựng ở API/CSV/AI.

Ngược lại, cùng tên ô ở NHÀ CUNG CẤP (`tax_code`, `bank_account_no`) PHẢI giữ giá trị:
đổi tài khoản nhận tiền của nhà cung cấp là thao tác cần dấu vết nhất. Bài nào ở đây
canh chiều đó thì đừng «sửa cho xanh» bằng cách che toàn hệ.
"""
import json
import uuid

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker

from app.core.logging_codes import ACTOR_KIND_USER
from app.core.logging_policy import MASKED, mask_payload, sensitive_keys_for_path
from app.core.request_context import RequestContext, reset_context, set_context
from app.core.request_middleware import RequestContextMiddleware
from app.main import validation_exception_handler
from app.modules.employee.contact_model import EmployeeContact, EmployeeFamily
from app.modules.employee.model import Employee
from app.modules.employee.sensitive import SENSITIVE_FIELDS
from app.modules.request_log.model import RequestLog
from app.modules.supplier.model import Supplier

SECRET_BANK = "9704229999888877"
SECRET_ID = "079199001234"


# ---------------------------------------------------------------------------
# Luật theo đường dẫn
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", [
    "/api/employees", "/api/employees/5", "/api/employees/me/contact",
    "/api/employees/5/set-password",
])
def test_every_employee_path_masks_all_sensitive_fields(path):
    assert set(SENSITIVE_FIELDS) <= sensitive_keys_for_path(path)


@pytest.mark.parametrize("path", [
    "/api/suppliers/5", "/api/companies/1", "/api/employees-export", "/api/employeesX/5",
    "/x/api/employees/5", "",
])
def test_other_paths_get_no_extra_masking(path):
    #  `/api/employees-export` là đường nhái tiền tố: so `startswith` trần sẽ nuốt nó.
    assert sensitive_keys_for_path(path) == frozenset()


@pytest.mark.parametrize("path, masks_items", [
    ("/api/employees/5/contacts", True),
    ("/api/employees/5/families", True),
    ("/api/employees/me/contacts", True),
    ("/api/employees/5/contacts/", True),
    #  `items` ở đây là phòng ban kiêm nhiệm — phải giữ để tra ai chuyển ai sang đâu.
    ("/api/employees/5/departments", False),
    ("/api/employees/5", False),
])
def test_items_masked_only_on_people_tables(path, masks_items):
    assert ("items" in sensitive_keys_for_path(path)) is masks_items


def test_extra_keys_mask_at_every_depth_and_keep_the_rest():
    goc = {"full_name": "Nguyễn A", "bank_account_no": SECRET_BANK,
           "nested": [{"id_number": SECRET_ID, "department_id": 3}]}
    che = mask_payload(goc, sensitive_keys_for_path("/api/employees/5"))
    assert che == {"full_name": "Nguyễn A", "bank_account_no": MASKED,
                   "nested": [{"id_number": MASKED, "department_id": 3}]}
    #  Chép chứ không sửa tại chỗ — endpoint còn đọc thân gốc.
    assert goc["bank_account_no"] == SECRET_BANK


def test_without_extra_keys_supplier_bank_account_is_kept():
    assert mask_payload({"bank_account_no": SECRET_BANK}) == {"bank_account_no": SECRET_BANK}


# ---------------------------------------------------------------------------
# Middleware chạy thật
# ---------------------------------------------------------------------------
@pytest.fixture
def client(db, monkeypatch):
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)

    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    async def echo(request: Request):
        return {"success": True, "message": "ok", "data": {"id": 5, "echo": await request.json()}}

    app.add_api_route("/api/employees/{eid}", echo, methods=["PATCH"])
    app.add_api_route("/api/employees/{eid}/contacts", echo, methods=["PUT"])
    app.add_api_route("/api/employees/{eid}/departments", echo, methods=["PUT"])
    app.add_api_route("/api/suppliers/{sid}", echo, methods=["PATCH"])

    class SoCccdIn(BaseModel):
        id_number: int

    @app.post("/api/employees")
    def tao(data: SoCccdIn):
        return {"success": True, "data": {"id": 1}}

    return TestClient(app)


def _last_row(db):
    return db.query(RequestLog).order_by(RequestLog.id.desc()).first()


def test_employee_patch_body_is_masked_in_request_log(client, db):
    body = {"full_name": "Nguyễn A", "bank_account_no": SECRET_BANK, "id_number": SECRET_ID,
            "tax_code": "8888", "date_of_birth": "1990-01-01", "department_id": 3}
    res = client.patch("/api/employees/5", json=body)

    assert res.json()["data"]["echo"] == body  # endpoint vẫn nhận đủ thân thật
    dong = _last_row(db)
    #  Đọc cả dòng chứ không soi từng khóa: lọt ở đâu cũng là lọt.
    raw = json.dumps([dong.request_body, dong.response_body], ensure_ascii=False)
    assert SECRET_BANK not in raw and SECRET_ID not in raw and "1990-01-01" not in raw
    #  Ô thường vẫn giữ — nhật ký phải trả lời được «ai đổi phòng ban / tên của ai».
    assert dong.request_body["full_name"] == "Nguyễn A"
    assert dong.request_body["department_id"] == 3
    assert dong.request_body["bank_account_no"] == MASKED


def test_people_table_put_masks_whole_item_list(client, db):
    body = {"items": [{"full_name": "Mẹ", "relation": 1, "phone": "0909123456",
                       "address": "12 Lê Lợi"}]}
    client.put("/api/employees/5/contacts", json=body)

    dong = _last_row(db)
    assert dong.request_body == {"items": MASKED}


def test_department_put_keeps_items(client, db):
    body = {"items": [{"department_id": 4, "is_primary": True}]}
    client.put("/api/employees/5/departments", json=body)

    assert _last_row(db).request_body == body


def test_supplier_bank_account_change_keeps_its_value(client, db):
    body = {"bank_account_no": SECRET_BANK, "tax_code": "0312345678"}
    client.patch("/api/suppliers/7", json=body)

    assert _last_row(db).request_body == body


def test_validation_error_on_employee_path_does_not_store_raw_value(client, db):
    #  422 vác giá trị thô ở `input`; `redact_raw_inputs` lo phần đó — bài này canh
    #  rằng request_body của CÙNG dòng cũng không để lộ qua ô nhạy cảm.
    res = client.post("/api/employees", json={"id_number": "CCCD-" + SECRET_ID})

    assert res.status_code == 422
    dong = _last_row(db)
    assert SECRET_ID not in json.dumps([dong.request_body, dong.response_body],
                                       ensure_ascii=False)


# ---------------------------------------------------------------------------
# Lớp ORM — tab_change_log
# ---------------------------------------------------------------------------
@pytest.fixture
def ctx(db, monkeypatch):
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)
    context = RequestContext(request_id=uuid.uuid4().bytes, user_id=7,
                             actor_kind=ACTOR_KIND_USER)
    token = set_context(context)
    try:
        yield context
    finally:
        reset_context(token)


def _employee(db, seed):
    employee = Employee(code="NV_LOG", full_name="Nguyễn A", company_id=seed.company_id,
                        department_id=seed.dept_id, is_active=True,
                        bank_account_no=SECRET_BANK, id_number=SECRET_ID)
    db.add(employee)
    db.commit()
    return employee


def test_new_employee_snapshot_masks_sensitive_columns(db, seed, ctx):
    ctx.changes = []
    employee = _employee(db, seed)

    entry = next(e for e in ctx.changes if e.table_name == "tab_employee")
    assert entry.snapshot["bank_account_no"] == MASKED
    assert entry.snapshot["id_number"] == MASKED
    assert entry.snapshot["full_name"] == "Nguyễn A"
    assert employee.bank_account_no == SECRET_BANK  # chỉ che bản LƯU LẠI


def test_updating_sensitive_column_records_field_name_but_no_value(db, seed, ctx):
    employee = _employee(db, seed)
    ctx.changes = []

    employee.bank_account_no = "1111222233334444"
    employee.full_name = "Nguyễn B"
    db.commit()

    fields = {e.field: e for e in ctx.changes if e.table_name == "tab_employee"}
    bank = fields["bank_account_no"]
    #  Vẫn biết «ai đổi số tài khoản của ai, lúc nào» — chỉ không biết số.
    assert bank.is_masked and bank.before_value is None and bank.after_value is None
    assert fields["full_name"].before_value == "Nguyễn A"
    assert fields["full_name"].after_value == "Nguyễn B"


@pytest.mark.parametrize("column", SENSITIVE_FIELDS)
def test_every_sensitive_field_is_masked_in_change_log(column):
    from app.core.change_tracker import _is_allowed

    assert _is_allowed("tab_employee", column) is False


def test_supplier_columns_with_same_names_are_not_masked(db, ctx):
    supplier = Supplier(code="NCC_LOG", name="Cty A", created_by=1, updated_by=1)
    db.add(supplier)
    db.commit()
    ctx.changes = []

    supplier.tax_code = "0312345678"
    db.commit()

    entry = next(e for e in ctx.changes if e.field == "tax_code")
    assert not entry.is_masked and entry.after_value == "0312345678"


@pytest.mark.parametrize("model", [EmployeeContact, EmployeeFamily])
def test_people_rows_keep_only_relation_not_identity(db, seed, ctx, model):
    employee = _employee(db, seed)
    ctx.changes = []

    extra = {"id_number": SECRET_ID} if model is EmployeeFamily else {"address": "12 Lê Lợi"}
    db.add(model(employee_id=employee.id, full_name="Trần Mẹ", relation=1,
                 phone="0909123456", **extra))
    db.commit()

    entry = next(e for e in ctx.changes if e.table_name == model.__tablename__)
    raw = json.dumps(entry.snapshot, ensure_ascii=False)
    assert "Trần Mẹ" not in raw and "0909123456" not in raw and SECRET_ID not in raw
    assert entry.snapshot["relation"] == "1"
    assert entry.snapshot["employee_id"] == str(employee.id)
