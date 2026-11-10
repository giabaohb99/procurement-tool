"""bao-CR-743 — màn AI › Kết nối: khóa nào đang được dùng THẬT (phần máy chủ).

Canh:
  - nhãn KeyState.ACTIVE đổi thành *Còn hiệu lực* (trước ghi *Đang dùng* cho mọi khóa còn hạn, admin tưởng khóa nào
    cũng đang chạy);
  - mức dùng tính từ `last_used_at`, CHỈ cho khóa còn hiệu lực: Đang dùng (≤ 7 ngày) · Ít dùng (7–30 ngày) · Lâu không
    dùng (> 30 ngày) · Chưa dùng (null); khóa chờ nhận / tắt / hết hạn / thu hồi thì không có mức dùng;
  - `GET /mcp-key-admin/keys?usage=` lọc ở máy chủ, `total` tính sau khi lọc, giá trị lạ → 422; meta trả `usages`.
"""
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.agent_hub import controller, mcp_keys
from app.modules.employee.model import Employee
from app.modules.user.model import User

NOW = datetime(2026, 11, 10, 9, 0, 0)


def _json(resp):
    return json.loads(resp.body)["data"]


def _row(**kw) -> SimpleNamespace:
    base = {"revoked_at": None, "expires_at": NOW + timedelta(days=30), "issued_by": 0, "claimed_at": None,
            "disabled_at": None, "kind": mcp_keys.KIND_MANUAL, "access_expires_at": None, "last_used_at": None}
    return SimpleNamespace(**{**base, **kw})


def test_nhan_trang_thai_con_hieu_luc_khong_con_ghi_dang_dung():
    assert mcp_keys.STATE_LABELS[mcp_keys.KeyState.ACTIVE] == "Còn hiệu lực"


@pytest.mark.parametrize("days_ago,expected", [
    (None, "never"), (0, "recent"), (7, "recent"), (8, "idle"), (30, "idle"), (31, "stale"), (200, "stale"),
])
def test_muc_dung_theo_lan_dung_cuoi(days_ago, expected):
    last = None if days_ago is None else NOW - timedelta(days=days_ago)
    assert mcp_keys.usage_of(_row(last_used_at=last), NOW) == expected


@pytest.mark.parametrize("kw", [
    {"revoked_at": NOW},                                    # đã thu hồi
    {"expires_at": NOW - timedelta(days=1)},                # hết hạn
    {"issued_by": 9},                                       # phát hộ chưa nhận
    {"disabled_at": NOW},                                   # chủ khóa tắt tạm
])
def test_khoa_khong_con_hieu_luc_khong_co_muc_dung(kw):
    assert mcp_keys.usage_of(_row(last_used_at=None, **kw), NOW) is None


def test_nhan_muc_dung_du_bon_loai():
    assert mcp_keys.USAGE_LABELS == {"recent": "Đang dùng", "idle": "Ít dùng", "stale": "Lâu không dùng",
                                     "never": "Chưa dùng"}


# ── Danh sách quản trị ───────────────────────────────────────────────────────────────

def _person(db, code: str, company_id: int, dept_id: int) -> User:
    emp = Employee(code=code, full_name=f"Người {code}", company_id=company_id, department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    u = User(email=f"{code.lower()}@cr743.vn", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    return u


@pytest.fixture
def org(db, seed, cap_quyen):
    admin = _person(db, "QL743", seed.company_id, seed.dept_id)
    cap_quyen(admin.id, controller.KEY_ADMIN_ENTITY, scope="dept", read=True, delete=True)
    mate = _person(db, "NV743", seed.company_id, seed.dept_id)
    now = datetime.now()
    rows = {}
    for name, last in (("moi", now - timedelta(days=1)), ("it", now - timedelta(days=15)),
                       ("lau", now - timedelta(days=45)), ("chua", None), ("chua2", None)):
        row, _raw = mcp_keys.create(db, mate.id, name=name)
        row.last_used_at = last
        rows[name] = row
    rows["chua2"].disabled_at = now                         # tắt tạm — không tính vào mức dùng
    db.commit()
    return SimpleNamespace(admin=admin, mate=mate, rows=rows)


def _keys(db, admin, **kw):
    args = {"department_id": 0, "state": None, "user_id": None, "batch_id": "", "page": 1, "size": 50, **kw}
    return _json(controller.key_admin_list(user=admin, db=db, **args))


def test_danh_sach_tra_muc_dung_cho_tung_khoa(db, org):
    items = {i["name"]: i for i in _keys(db, org.admin)["items"]}
    got = {n: (i["state_label"], i["usage"], i["usage_label"]) for n, i in items.items()}
    assert got == {"moi": ("Còn hiệu lực", "recent", "Đang dùng"), "it": ("Còn hiệu lực", "idle", "Ít dùng"),
                   "lau": ("Còn hiệu lực", "stale", "Lâu không dùng"), "chua": ("Còn hiệu lực", "never", "Chưa dùng"),
                   "chua2": ("Đang tắt", None, "")}


def test_loc_theo_muc_dung_o_may_chu(db, org):
    out = _keys(db, org.admin, usage="never")
    assert (out["total"], [i["name"] for i in out["items"]]) == (1, ["chua"])
    assert [i["name"] for i in _keys(db, org.admin, usage="stale")["items"]] == ["lau"]
    assert [i["name"] for i in _keys(db, org.admin, usage="recent")["items"]] == ["moi"]
    assert [i["name"] for i in _keys(db, org.admin, usage="idle")["items"]] == ["it"]
    paged = _keys(db, org.admin, size=1)
    assert (paged["total"], paged["has_more"]) == (5, True)                # không lọc thì đủ 5 khóa


def test_loc_muc_dung_gia_tri_la_bi_tu_choi(db, org):
    with pytest.raises(HTTPException) as err:
        _keys(db, org.admin, usage="xyz")
    assert err.value.status_code == 422


def test_meta_tra_danh_sach_muc_dung(db, org):
    meta = _json(controller.key_admin_meta(user=org.admin, db=db))
    assert meta["usages"] == [{"value": "recent", "label": "Đang dùng"}, {"value": "idle", "label": "Ít dùng"},
                              {"value": "stale", "label": "Lâu không dùng"}, {"value": "never", "label": "Chưa dùng"}]
    assert {s["value"]: s["label"] for s in meta["states"]}[2] == "Còn hiệu lực"
