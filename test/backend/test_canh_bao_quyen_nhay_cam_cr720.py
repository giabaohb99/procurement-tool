"""bao-CR-720 — cảnh báo vàng trên màn Vai trò & quyền: vai trò người yêu cầu được tick Xem / Xuất ở entity nhạy cảm thu mua.

Danh sách khai MỘT chỗ ở `core/permissions.py`, trả qua `/api/roles/meta`; giao diện chỉ đọc. Không chặn lưu.
"""
from app.core.permissions import ACTIONS, ENTITIES, SENSITIVE_PROCUREMENT_ENTITIES, SENSITIVE_WARN_ACTIONS
from app.modules.user.service import DEFAULT_ROLE_CODE
from hdld_factory import client_as  # noqa: F401


def test_danh_sach_nhay_cam_la_entity_va_hanh_dong_that():
    assert set(SENSITIVE_PROCUREMENT_ENTITIES) <= set(ENTITIES)
    assert set(SENSITIVE_WARN_ACTIONS) <= set(ACTIONS)
    assert {"supplier", "contract", "payable", "payment_request", "customs_price"} <= set(SENSITIVE_PROCUREMENT_ENTITIES)
    assert "read" in SENSITIVE_WARN_ACTIONS and "export" in SENSITIVE_WARN_ACTIONS


def test_meta_tra_du_ba_truong_cho_man_phan_quyen(world, client_as):  # noqa: F811
    world.grant("a1", "role", "all", actions=("read",))
    meta = client_as(world.actor("a1")).get("/api/roles/meta").json()["data"]
    assert meta["sensitive_entities"] == list(SENSITIVE_PROCUREMENT_ENTITIES)
    assert meta["sensitive_actions"] == list(SENSITIVE_WARN_ACTIONS)
    assert meta["requester_role_codes"] == [DEFAULT_ROLE_CODE] == ["employee"]
    assert set(meta["sensitive_entities"]) <= {e["key"] for e in meta["entities"]}


def test_khong_chan_luu_quyen_nhay_cam_cho_vai_tro_nguoi_yeu_cau(world, client_as):  # noqa: F811
    """Chỉ nhắc, không chặn: lưu Xem NCC cho vai trò employee vẫn 200 (quyết định là của người quản trị)."""
    from app.modules.role.model import Role

    world.grant("a1", "role", "all", actions=("read", "write"))
    world.grant("a1", "supplier", "all", actions=("read",))      # bộ chặn leo quyền: chỉ cấp được quyền mình đang có
    role = world.db.query(Role).filter(Role.code == DEFAULT_ROLE_CODE).first()
    if role is None:
        role = Role(code=DEFAULT_ROLE_CODE, name="Nhân sự")
        world.db.add(role)
        world.db.commit()
    res = client_as(world.actor("a1")).put(
        f"/api/roles/{role.id}/permissions",
        json={"permissions": [{"entity": "supplier", "scope": "all", "can_read": True}]})
    assert res.status_code == 200, res.text
