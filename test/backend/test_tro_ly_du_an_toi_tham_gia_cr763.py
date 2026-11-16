"""duoc-CR-763 — trợ lý / bot / cổng MCP liệt kê DỰ ÁN và NHÓM DỰ ÁN người hỏi tham gia (`my_projects`).

Lỗi gốc (prod 16/11/2026): thành viên 14 dự án nhóm DX hỏi **anh đang có trong những dự án nào** thì bot trả không có dự án
nào (chỉ có `my_work_tasks` — việc của mình hạn hôm nay), hỏi **nhóm dự án** thì bot kể nhóm Telegram.

1. Tập dự án ĐÚNG như màn Dự án (`list_service.get_lists`): đối chiếu thẳng với hàm của màn, không viết luật thứ hai.
2. Số liệu mỗi dự án: vai trò = `effective_role`, tiến độ = công thức thanh tiến độ, việc đang mở / của tôi đếm đúng.
3. Bộ lọc công cụ chọn `my_projects` cho cả hai câu, câu **nhóm dự án** không kéo công cụ nhóm chat.
4. Sổ khai: cổng MCP chỉ đọc, đúng một nhóm G7 (bật sẵn), nhãn ý định, mẫu chấm lõi.
5. Số truy vấn cố định: 2 dự án và 20 dự án cùng số câu SQL.
"""
from datetime import datetime
from types import SimpleNamespace

import pytest

from app.modules.assistant import tool_router as tr
from app.modules.assistant.tools.base import ToolContext
from app.modules.assistant.tools.my_projects_tool import MY_PROJECTS_SPEC, compute_progress_pct
from app.modules.user.model import User
from app.modules.work import list_service
from app.modules.work.membership_service import effective_role, resolve_actor
from app.modules.work.model import (WorkAssigneeKind, WorkGroup, WorkGroupMember, WorkList, WorkListMember,
                                    WorkMemberRole, WorkTaskStatus)
from app.modules.work.task_model import WorkTask, WorkTaskAssignee
from lich_lam_viec_factory import count_queries

SECRET = "ZZNOIDUNGPHONGKHAC"
OPEN, DONE = int(WorkTaskStatus.OPEN), int(WorkTaskStatus.DONE)
PIC, FOLLOWER = int(WorkAssigneeKind.PIC), int(WorkAssigneeKind.FOLLOWER)


def _ctx(db, user_id, can=True):
    ctx = ToolContext(db=db, user=db.get(User, user_id))
    orig = ctx.can
    ctx.can = lambda entity, action="read": can if entity == "work_task" else orig(entity, action)
    return ctx


def _run(db, seed, **args):
    return MY_PROJECTS_SPEC.handler(_ctx(db, seed.u_req_id), args)


def _projects(out) -> dict[int, dict]:
    return {p["id"]: p for g in out["groups"] for p in g["projects"]}


def _task(db, list_id, title, status=OPEN, parent_id=None, deleted=False, people=()):
    t = WorkTask(title=title, list_id=list_id, status=status, parent_id=parent_id,
                 deleted_at=datetime(2026, 11, 1) if deleted else None)
    db.add(t)
    db.flush()
    for emp_id, kind in people:
        db.add(WorkTaskAssignee(task_id=t.id, employee_id=emp_id, kind=kind))
    return t


@pytest.fixture
def world(db, seed):
    """Nhóm DX (mình là Thành viên) ⊃ nhóm con DX / Sàn; dự án mời riêng ngoài nhóm (Khách xem); dự án của người khác."""
    me, owner = seed.emp_req_id, seed.emp_tp_id
    dx = WorkGroup(name="DX", sort_order=1)
    db.add(dx)
    db.flush()
    sub = WorkGroup(name="Sàn", parent_id=dx.id, sort_order=1)
    db.add(sub)
    db.flush()
    db.add(WorkGroupMember(group_id=dx.id, employee_id=me, role=int(WorkMemberRole.MEMBER)))
    a = WorkList(name="ERP v2", group_id=dx.id, sort_order=2)
    b = WorkList(name="Livestream Shopee", group_id=sub.id, sort_order=1)
    c = WorkList(name="Dự án riêng", sort_order=1)
    hidden = WorkList(name=f"Dự án {SECRET}", sort_order=1)
    archived = WorkList(name="Dự án cũ", group_id=dx.id, sort_order=3, is_archived=1)
    db.add_all([a, b, c, hidden, archived])
    db.flush()
    for lst in (a, b, c, hidden, archived):
        db.add(WorkListMember(list_id=lst.id, employee_id=owner, role=int(WorkMemberRole.OWNER)))
    #  Dự án A: mời riêng thêm vai trò Quản trị → hiệu lực Quản trị (min với Thành viên kế thừa từ nhóm).
    db.add(WorkListMember(list_id=a.id, employee_id=me, role=int(WorkMemberRole.ADMIN)))
    db.add(WorkListMember(list_id=c.id, employee_id=me, role=int(WorkMemberRole.VIEWER)))
    db.add(WorkListMember(list_id=a.id, employee_id=seed.emp_nstm_id, role=int(WorkMemberRole.MEMBER)))

    #  Dự án A: 3 việc cha (1 xong, 2 đang mở trong đó 1 mình phụ trách), 1 việc con mình phụ trách, 1 việc mình chỉ
    #  theo dõi, 1 việc đã xóa mềm mình phụ trách, 1 việc đã hủy.
    p1 = _task(db, a.id, "việc mở của tôi", people=[(me, PIC)])
    _task(db, a.id, "việc xong", status=DONE, people=[(me, PIC)])
    _task(db, a.id, "việc tôi theo dõi", people=[(me, FOLLOWER), (owner, PIC)])
    _task(db, a.id, "việc con của tôi", parent_id=p1.id, people=[(me, PIC)])
    _task(db, a.id, "việc đã xóa", deleted=True, people=[(me, PIC)])
    _task(db, a.id, "việc đã hủy", status=int(WorkTaskStatus.CANCELLED))
    #  Dự án B: 1/8 xong → 12,5% → thanh tiến độ hiện 13% (Math.round), khác round() của Python (12).
    for i in range(8):
        _task(db, b.id, f"việc B{i}", status=DONE if i == 0 else OPEN)
    _task(db, hidden.id, f"việc {SECRET}", people=[(me, PIC)])
    db.commit()
    return SimpleNamespace(dx=dx, sub=sub, a=a, b=b, c=c, hidden=hidden, archived=archived, me=me)


def _screen(db, seed, include_archived=False):
    actor = resolve_actor(db, db.get(User, seed.u_req_id))
    return {r["id"]: r for r in list_service.get_lists(db, actor, include_archived, with_people=True)}


# ── 1. Cùng tập dự án với màn Dự án ─────────────────────────────────────────────────────────────────────────────────

def test_chi_thay_dung_du_an_cua_man_du_an(db, seed, world):
    out = _run(db, seed)
    got = _projects(out)
    assert set(got) == set(_screen(db, seed)) == {world.a.id, world.b.id, world.c.id}
    assert world.hidden.id not in got and SECRET not in str(out)
    assert (out["total"], out["returned"], out["has_more"]) == (3, 3, False)
    #  Gom theo nhóm, nhóm con hiện đường dẫn cha / con, dự án ngoài nhóm đứng cuối.
    assert [g["name"] for g in out["groups"]] == ["DX", "DX / Sàn", "Không thuộc nhóm nào"]
    assert out["group_count"] == 2 and out["groups"][-1]["group_id"] is None
    assert got[world.a.id]["url"] == f"/project/lists/{world.a.id}"


def test_du_an_luu_tru_chi_hien_khi_xin(db, seed, world):
    assert world.archived.id not in _projects(_run(db, seed))
    got = _projects(_run(db, seed, include_archived=True))
    assert set(got) == set(_screen(db, seed, include_archived=True))
    assert got[world.archived.id]["archived"] is True and got[world.a.id]["archived"] is False


def test_loc_theo_nhom_va_ten(db, seed, world):
    assert set(_projects(_run(db, seed, group="dx"))) == {world.a.id, world.b.id}
    assert set(_projects(_run(db, seed, group="san"))) == {world.b.id}     # so không dấu
    assert set(_projects(_run(db, seed, q="livestream"))) == {world.b.id}
    out = _run(db, seed, q="khong co du an nay")
    assert out["total"] == 0 and "khớp bộ lọc" in out["note"]
    assert _run(db, seed, q="x" * 5000)["total"] == 0                     # tham số quá dài không vỡ


# ── 2. Số liệu từng dự án ───────────────────────────────────────────────────────────────────────────────────────────

def test_vai_tro_tien_do_va_nguoi_khop_man_du_an(db, seed, world):
    got, screen = _projects(_run(db, seed, include_archived=True)), _screen(db, seed, include_archived=True)
    for lid, p in got.items():
        row = screen[lid]
        assert p["my_role"] == effective_role(db, world.me, lid) == row["my_role"], p["name"]
        assert (p["task_count"], p["task_done"]) == (row["task_count"], row["task_done"])
        assert p["progress_pct"] == compute_progress_pct(row["task_done"], row["task_count"])
        assert p["owner_name"] == row["owner"]["employee_name"] and p["member_count"] == len(row["members"])
    assert got[world.a.id]["my_role_label"] == "Quản trị" and got[world.c.id]["my_role_label"] == "Khách xem"
    assert got[world.b.id]["my_role_label"] == "Thành viên"                 # kế thừa từ nhóm cha DX
    assert got[world.b.id]["progress_pct"] == 13 and got[world.c.id]["progress_pct"] == 0
    assert got[world.a.id]["member_count"] == 3


def test_dem_viec_dang_mo_va_viec_cua_toi(db, seed, world):
    out = _run(db, seed)
    a, b = _projects(out)[world.a.id], _projects(out)[world.b.id]
    #  A: việc cha đang mở = "việc mở của tôi" + "việc tôi theo dõi" (không đếm việc con, việc xóa, việc hủy, việc xong).
    assert a["open_task_count"] == 2
    #  Của tôi: việc mở của tôi + việc con của tôi (theo dõi, đã xóa, đã xong không tính) — như my_work_tasks all_open.
    assert a["my_open_task_count"] == 2
    assert (b["open_task_count"], b["my_open_task_count"]) == (7, 0)
    assert out["my_open_task_count"] == 2


def test_cong_thuc_tien_do_nhu_thanh_tien_do():
    assert [compute_progress_pct(d, t) for d, t in [(0, 0), (1, 8), (1, 3), (2, 3), (3, 3), (1, 200)]] == \
        [0, 13, 33, 67, 100, 1]


# ── Quyền ───────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_thieu_quyen_bi_tu_choi(db, seed, world):
    out = MY_PROJECTS_SPEC.handler(_ctx(db, seed.u_req_id, can=False), {})
    assert out.get("denied") is True and "groups" not in out


def test_tai_khoan_chua_gan_nhan_su(db, seed, world):
    user = db.get(User, seed.u_req_id)
    user.employee_id = 0
    db.commit()
    out = MY_PROJECTS_SPEC.handler(_ctx(db, seed.u_req_id), {})
    assert out["total"] == 0 and "chưa gắn hồ sơ nhân sự" in out["note"]


def test_chua_tham_gia_du_an_nao(db, seed):
    out = MY_PROJECTS_SPEC.handler(_ctx(db, seed.u_req_id), {})
    assert out["total"] == 0 and "chưa tham gia dự án nào" in out["note"]


# ── 3. Bộ lọc công cụ ───────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("q", [
    "anh đang có trong những dự án nào",
    "anh có đang trong nhóm dự án nào ko",
    "tôi tham gia dự án nào",
    "danh sách dự án của tôi",
    "dự án của tôi",
])
def test_bo_loc_cong_cu_chon_my_projects(q):
    picked = tr.select(q)
    assert picked is not None and "my_projects" in picked, q
    assert not picked & {"list_my_groups", "read_group_messages", "read_group_file"}, q


def test_nhom_chat_van_nap_cong_cu_nhom():
    assert "list_my_groups" in (tr.select("bot đang ở nhóm nào") or set())
    assert "list_my_groups" in (tr.select("tóm tắt nhóm Mua hàng hôm nay") or set())


def test_mo_ta_cong_cu_chi_duong_cho_nhau():
    from app.modules.assistant.tools.group_tool import LIST_MY_GROUPS_SPEC
    from app.modules.assistant.tools.work_tool import MY_WORK_TASKS_SPEC

    assert "my_projects" in MY_WORK_TASKS_SPEC.description and "my_projects" in LIST_MY_GROUPS_SPEC.description
    assert "nhóm chat Telegram" in MY_PROJECTS_SPEC.description


# ── 4. Sổ khai ──────────────────────────────────────────────────────────────────────────────────────────────────────

def test_cong_mcp_chi_doc_va_nhom_g7(mcp_all_groups):
    from app.modules.agent_hub import intent_ledger, mcp, mcp_keys, mcp_settings

    assert "my_projects" in mcp.READ_TOOLS and not mcp.is_write_tool("my_projects")
    owner = SimpleNamespace(id=1, is_active=True)
    assert "my_projects" in {t["name"] for t in mcp.list_tools(None, owner, mcp_keys.SCOPE_READ)}
    groups = [g for g in mcp_settings.GROUPS if "my_projects" in g.tools]
    assert len(groups) == 1 and groups[0].key == "mine" and groups[0].default_on is True
    assert intent_ledger.TOOL_SUB["my_projects"] == intent_ledger.TOOL_SUB["my_work_tasks"]


def test_mau_cham_loi_goi_my_projects():
    from app.modules.agent_hub.core_eval_samples import SAMPLES

    turns = {s.id: s.turns[0] for s in SAMPLES if s.id in {"23", "24"}}
    assert turns["23"].text == "anh đang có trong những dự án nào"
    assert turns["24"].text == "anh có đang trong nhóm dự án nào ko"
    assert all("my_projects" in t.must_call and "list_my_groups" in t.must_not_call for t in turns.values())


# ── 5. Số truy vấn cố định ──────────────────────────────────────────────────────────────────────────────────────────

def _make_projects(db, seed, n):
    grp = WorkGroup(name=f"Nhóm {n}")
    db.add(grp)
    db.flush()
    db.add(WorkGroupMember(group_id=grp.id, employee_id=seed.emp_req_id, role=int(WorkMemberRole.MEMBER)))
    for i in range(n):
        lst = WorkList(name=f"Dự án {n}-{i}", group_id=grp.id if i % 2 else None)
        db.add(lst)
        db.flush()
        db.add(WorkListMember(list_id=lst.id, employee_id=seed.emp_tp_id, role=int(WorkMemberRole.OWNER)))
        if not i % 2:
            db.add(WorkListMember(list_id=lst.id, employee_id=seed.emp_req_id, role=int(WorkMemberRole.MEMBER)))
        _task(db, lst.id, "việc", people=[(seed.emp_req_id, PIC)])
        _task(db, lst.id, "việc xong", status=DONE)
    db.commit()


def test_so_truy_van_co_dinh(db, seed):
    from sqlalchemy import delete

    counts = []
    for n in (2, 20):
        _make_projects(db, seed, n)
        out, sql = count_queries(db, lambda: _run(db, seed))
        assert out["total"] == n
        counts.append(len(sql))
        for model in (WorkTaskAssignee, WorkTask, WorkListMember, WorkGroupMember, WorkList, WorkGroup):
            db.execute(delete(model))
        db.commit()
    assert counts[0] == counts[1], counts
