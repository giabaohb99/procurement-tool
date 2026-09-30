"""bao-CR-526 — bộ vai trò «thu mua theo phòng»: `pur_dept_manager` (đã có) + `pur_dept_staff` (mới).

Đại ca chốt 30/09/2026: tạo SẴN, chưa gán cho ai. Nhân viên thu mua phòng cùng hành động với
nhân viên thu mua thường, chỉ khác phạm vi ba chứng từ là `dept_proc` (mọi phiếu đã duyệt của
phòng mình) thay vì chỉ phiếu được giao.
"""
from app.modules.assistant.tools.account_setup_tool import PURCHASING_ROLE_CODES, TEMPLATE_ROLE_CODES
from app.seed import ROLE_DESCRIPTIONS, STD_ROLES

DOCS = ("purchase_request", "survey_request", "purchase_order")


def test_dept_staff_role_scopes_the_three_documents_by_department():
    perms = STD_ROLES["pur_dept_staff"]["perms"]
    assert STD_ROLES["pur_dept_staff"]["name"] == "Nhân viên thu mua phòng"
    for doc in DOCS:
        assert perms[doc][1] == "dept_proc", doc


def test_dept_staff_has_exactly_the_same_actions_as_regular_staff():
    staff, dept_staff = STD_ROLES["pur_staff"]["perms"], STD_ROLES["pur_dept_staff"]["perms"]
    assert set(staff) == set(dept_staff), "hai vai trò phải phủ cùng bộ khóa quyền"
    for entity, (actions, _scope) in staff.items():
        assert sorted(dept_staff[entity][0]) == sorted(actions), entity


def test_dept_set_is_complete_and_described():
    assert STD_ROLES["pur_dept_manager"]["perms"]["purchase_request"][1] == "dept_proc"
    assert "pur_dept_staff" in ROLE_DESCRIPTIONS


def test_ai_account_setup_can_assign_the_new_role():
    assert "pur_dept_staff" in TEMPLATE_ROLE_CODES
    assert "pur_dept_staff" in PURCHASING_ROLE_CODES
