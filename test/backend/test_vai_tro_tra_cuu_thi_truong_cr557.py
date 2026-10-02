"""bao-CR-557 — Tra cứu thị trường tách thành vai trò riêng `market_lookup`.

Đại ca chốt 02/10/2026: chỉ trưởng phòng thu mua và vài người được chỉ định xem được, nhà máy và
nhân viên thu mua thường thì không. Bài này giữ cho seed không cấp lại hai khóa cho vai trò nào
khác ngoài vai trò riêng và quản trị hệ thống.
"""
from app.core.permissions import ENTITIES
from app.seed import _SYS_ENTITIES, ROLE_DESCRIPTIONS, STD_ROLES

KEYS = ("customs_price", "customs_regulation")


def test_market_lookup_role_carries_both_keys_company_wide():
    role = STD_ROLES["market_lookup"]
    assert role["name"] == "Tra cứu thị trường"
    actions, scope = role["perms"]["customs_price"]
    assert "read" in actions and scope == "all"
    assert "read" in role["perms"]["customs_regulation"][0]
    assert ROLE_DESCRIPTIONS["market_lookup"]


def test_no_other_standard_role_gets_the_market_lookup_keys():
    #  Lọt vào vai trò khác (nhất là cụm thu mua, nhà máy) là người nhà máy lại thấy menu.
    for code, info in STD_ROLES.items():
        if code in ("admin", "market_lookup"):
            continue
        for key in KEYS:
            actions = info["perms"].get(key, ([], ""))[0]
            assert not actions, f"{code} không được giữ {key}"


def test_keys_stay_out_of_the_purchasing_manager_sweep():
    #  `_PUR_MANAGER_PERMS` quét cả ENTITIES trừ `_SYS_ENTITIES` — rớt khỏi tập này là
    #  Quản lý thu mua tự nhận lại quyền ở lần seed kế tiếp.
    for key in KEYS:
        assert key in ENTITIES
        assert key in _SYS_ENTITIES
