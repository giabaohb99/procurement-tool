"""bao-CR-545 — «Admin thu mua phòng» (`pur_dept_admin`): bộ thu mua theo phòng đủ ba vai trò
như bộ chung (Nhân viên · Admin · Quản lý). Chép quyền `pur_admin`, ba chứng từ phạm vi `dept_proc`.
"""
from app.modules.assistant.tools.account_setup_tool import PURCHASING_ROLE_CODES, TEMPLATE_ROLE_CODES
from app.seed import ROLE_DESCRIPTIONS, STD_ROLES

DOCS = ("purchase_request", "survey_request", "purchase_order")


def test_dept_admin_scopes_the_three_documents_by_department():
    role = STD_ROLES["pur_dept_admin"]
    assert role["name"] == "Admin thu mua phòng"
    for doc in DOCS:
        assert role["perms"][doc][1] == "dept_proc", doc


def test_dept_admin_has_the_same_actions_as_admin_on_documents_and_catalogs():
    admin, dept_admin = STD_ROLES["pur_admin"]["perms"], STD_ROLES["pur_dept_admin"]["perms"]
    for entity in (*DOCS, "survey"):
        assert sorted(dept_admin[entity][0]) == sorted(admin[entity][0]), entity
    catalogs = [e for e, (actions, _s) in admin.items() if e not in DOCS and "delete" in actions
                and e not in ("survey", "import")]
    for entity in catalogs:
        assert entity in dept_admin, entity


def test_dept_admin_never_sees_wider_than_company():
    perms = STD_ROLES["pur_dept_admin"]["perms"]
    for entity in ("payable", "payment_request", "goods_receipt", "inventory"):
        assert perms[entity][1] == "company", entity
    assert perms["report"][1] == "dept"
    assert "import" not in perms


def test_described_and_assignable_by_ai_setup():
    assert "pur_dept_admin" in ROLE_DESCRIPTIONS
    assert "pur_dept_admin" in TEMPLATE_ROLE_CODES
    assert "pur_dept_admin" in PURCHASING_ROLE_CODES
