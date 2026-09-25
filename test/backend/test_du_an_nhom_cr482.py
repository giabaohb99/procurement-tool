"""bao-CR-482 — Quản lý nhóm dự án + ảnh đại diện đi theo người trong phân hệ Dự án.

Phần backend của CR này nhỏ: (1) mọi chỗ trả NGƯỜI (thành viên nhóm, thành viên dự
án, người phụ trách việc) kèm `avatar`; (2) sổ đồng bộ tạo dự án mới TRONG nhóm cha.
Cửa API sửa nhóm / thành viên nhóm / chuyển dự án vào nhóm đã có từ bao-CR-216,
màn hình mới là phần thiếu — bài kiểm ở đây canh dữ liệu mà màn hình đó ăn.
"""
import importlib.util
import pathlib
import sys

import pytest

from app.modules.attachment.model import StoredFile
from app.modules.user.model import User
from app.modules.work import group_service, list_service, task_enrich
from app.modules.work.membership_service import resolve_actor
from app.modules.work.people import employee_info
from app.modules.work.schema import GroupCreate, ListCreate, MemberIn


@pytest.fixture
def anh_dai_dien(db, seed):
    """Người yêu cầu của seed có ảnh đại diện; NSTM thì không."""
    f = StoredFile(filename="a.png", file_key="dev/avatar/1/a.png",
                   url="https://kho/dev/avatar/1/a.png",
                   thumb_url="https://kho/dev/avatar/1/a-thumb.png", content_type="image/png",
                   size=10, created_by=seed.u_req_id)
    db.add(f)
    db.flush()
    db.get(User, seed.u_req_id).avatar_file_id = f.id
    db.commit()
    return f


def test_employee_info_carries_thumbnail_avatar_and_blank_when_none(db, seed, anh_dai_dien):
    info = employee_info(db, [seed.emp_req_id, seed.emp_nstm_id, 0, None])
    assert info[seed.emp_req_id] == {"name": "Người YC", "code": "TESTREQ",
                                     "avatar": "https://kho/dev/avatar/1/a-thumb.png"}
    assert info[seed.emp_nstm_id]["avatar"] == ""
    assert employee_info(db, []) == {}


def test_group_and_list_members_carry_avatar(db, seed, anh_dai_dien):
    actor = resolve_actor(db, db.get(User, seed.u_req_id))
    grp = group_service.create_group(db, actor, GroupCreate(name="DX"))
    group_service.add_member(db, actor, grp["id"], MemberIn(employee_id=seed.emp_nstm_id, role=3))
    members = {m["employee_id"]: m for m in group_service.list_members(db, actor, grp["id"])}
    assert members[seed.emp_req_id]["avatar"].endswith("a-thumb.png"), "chủ nhóm có ảnh"
    assert members[seed.emp_nstm_id]["avatar"] == "", "người chưa có ảnh thì rỗng, không lỗi"

    lst = list_service.create_list(db, actor, ListCreate(name="ERP v2", group_id=grp["id"]))
    projects = {p["id"]: p for p in list_service.get_lists(db, actor, with_people=True)}
    assert projects[lst["id"]]["owner"]["avatar"].endswith("a-thumb.png")


def test_task_assignee_names_include_avatar(db, seed, anh_dai_dien):
    names = task_enrich._employee_names(db, [seed.emp_req_id])
    assert names[seed.emp_req_id]["avatar"].endswith("a-thumb.png")


# ── Sổ đồng bộ: dự án mới sinh ra TRONG nhóm cha ─────────────────────────────────────

def _load_sync_script():
    #  Neo theo gói `app` chứ không theo tệp kiểm: trong container `backend/` được
    #  mount thành `/app` nên đường `../../backend/scripts` không tồn tại.
    import app as app_pkg
    path = pathlib.Path(app_pkg.__file__).resolve().parent.parent / "scripts" / "sync_task_journal.py"
    spec = importlib.util.spec_from_file_location("sync_task_journal", path)
    mod = importlib.util.module_from_spec(spec)
    #  `@dataclass` trong script tra `sys.modules[cls.__module__]` lúc dựng lớp —
    #  nạp bằng spec mà không đăng ký thì ra `None` và nổ ngay dòng đầu.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class _FakeApi:
    def __init__(self, tree, lists=()):
        self.tree, self.lists, self.posted = tree, list(lists), []

    def call(self, method, path, body=None):
        if path == "/api/work/groups":
            return self.tree
        if path == "/api/work/lists" and method == "GET":
            return self.lists
        if path == "/api/work/lists" and method == "POST":
            self.posted.append(body)
            return {"id": 99}
        raise AssertionError(f"khong mong cho {method} {path}")


def test_sync_finds_group_by_name_including_children():
    mod = _load_sync_script()
    tree = {"groups": [{"id": 1, "name": "DX", "children": [{"id": 5, "name": "Con", "children": []}]}]}
    api = _FakeApi(tree)
    assert mod.find_group_id(api, "dx") == 1
    assert mod.find_group_id(api, "Con") == 5
    assert mod.find_group_id(api, "Không có") is None
    assert mod.find_group_id(api, "") is None


def test_sync_creates_new_list_inside_default_group(monkeypatch):
    mod = _load_sync_script()
    monkeypatch.delenv("WORK_SYNC_GROUP", raising=False)
    api = _FakeApi({"groups": [{"id": 1, "name": "DX", "children": []}]})
    assert mod.ensure_list(api, "Nhật ký hệ thống", dry=False) == 99
    assert api.posted[0]["group_id"] == 1
    #  Nhóm không tồn tại (hoặc tắt bằng biến rỗng) thì tạo đứng lẻ như trước.
    monkeypatch.setenv("WORK_SYNC_GROUP", "")
    api2 = _FakeApi({"groups": []})
    mod.ensure_list(api2, "Khác", dry=False)
    assert "group_id" not in api2.posted[0]
