"""kh-AI1-2 (doc/erp/tai-lieu-ai/22 §4, §6) — hai công cụ AI `team_capacity` và `task_type_stats` bọc `capability/ai_contract`.

Luật quyền (A1 chốt 22/10, phương án A — đúng doc 22 §6 *AI chỉ đề xuất, người quyết*):
  · có khóa báo cáo 16 «Năng lực theo loại việc» → thấy đủ số, phòng nào cũng được;
  · trưởng phòng (`Department.manager_id`) không có khóa 16 → chỉ THỨ TỰ gợi ý người trong phòng mình + phòng con, không số;
  · nhân viên thường → từ chối, câu giải thích nói rõ cần khóa 16 và ai giao được;
  · `task_type_stats` chỉ người có khóa 16.
"""
from datetime import datetime, timedelta
from itertools import count

import pytest

from app.core.capability_codes import CycleKind, CycleOutcome, CycleRole
from app.core.subject_match import SUBJECT_ROLE
from app.modules.assistant import tools as T
from app.modules.capability.model import WorkCycle
from app.modules.work.task_type_model import WorkTaskType

from ho_so_lam_viec_factory import make_company, make_dept, make_person

_ids = count(1)


def _cycle(db, emp, days, *, kind=CycleKind.PURCHASE_REQUEST, type_id=0, dept=0, company=0, rework=0):
    start = datetime.utcnow() - timedelta(days=20)
    db.add(WorkCycle(kind=int(kind), entity_id=next(_ids), role=int(CycleRole.HANDLER), employee_id=emp.id, company_id=company,
                     department_id=dept, task_type_id=type_id, started_at=start, done_at=start + timedelta(days=days),
                     outcome=int(CycleOutcome.DONE), cycle_hours=days * 24.0, rework_count=rework, is_estimated=False,
                     is_late=None, estimate_hours=None, actual_hours=None, review_outcome=0, computed_at=datetime.utcnow()))


@pytest.fixture
def world(db):
    co = make_company(db, "C1")
    d1, d2, d3 = make_dept(db, co, "D1"), make_dept(db, co, "D2"), make_dept(db, co, "D3")
    d1a = make_dept(db, co, "D1A")
    d1a.parent = d1.id                                         # phòng con của D1
    d1.name, d2.name = "Phòng Thu mua", "Phòng Kế toán"
    h_u, h = make_person(db, "H", co, d1)                      # trưởng D1
    h2_u, h2 = make_person(db, "H2", co, d2)                   # trưởng HAI phòng: D2 và D3
    _a_u, a = make_person(db, "A", co, d1)
    _x_u, x = make_person(db, "X", co, d1a)
    _b_u, b = make_person(db, "B", co, d2)
    _c_u, c = make_person(db, "C", co, d3)
    plain_u, _p = make_person(db, "P", co, d1)
    adm_u, _adm = make_person(db, "ADM", co, d2)
    d1.manager_id, d2.manager_id, d3.manager_id = h.id, h2.id, h2.id
    tt = WorkTaskType(company_id=co.id, code="TK", name="Thiết kế bao bì", is_active=True)
    db.add(tt)
    db.flush()
    for d in (1, 2, 3, 4, 5):
        _cycle(db, a, d, dept=d1.id, company=co.id)
        _cycle(db, x, d + 5, dept=d1a.id, company=co.id)
        _cycle(db, b, d, kind=CycleKind.WORK_TASK, type_id=tt.id, dept=d2.id, company=co.id)
    db.commit()
    return type("W", (), dict(co=co, d1=d1, d1a=d1a, d2=d2, d3=d3, h_u=h_u, h2_u=h2_u, plain_u=plain_u, adm_u=adm_u, tt=tt,
                              a=a, x=x, b=b, c=c, h=h, h2=h2))


@pytest.fixture
def khoa16(cap_quyen, gan_bao_cao, db):
    def _grant(user):
        role = cap_quyen(user.id, "setting", scope="all", read=True)
        gan_bao_cao(SUBJECT_ROLE, role.id, 16)
        db.commit()
    return _grant


def _codes(out):
    return [p["employee_code"] for p in out["people"]]


def test_nhan_vien_thuong_bi_tu_choi_noi_ro_khoa_16(db, world):
    for name, args in (("team_capacity", {}), ("task_type_stats", {"kind": "purchase_request"})):
        out = T.run_tool(db, world.plain_u, name, args)
        assert out.get("denied") is True, name
        assert "16" in out["reason"] and "Năng lực theo loại việc" in out["reason"] and "quản trị" in out["reason"].lower()


def test_truong_phong_chi_thay_thu_tu_phong_minh_va_phong_con_khong_so(db, world):
    out = T.run_tool(db, world.h_u, "team_capacity", {"kind": "purchase_request"})
    assert out["detail"] is False
    assert set(_codes(out)) == {"H", "A", "X", "P"}                 # D1 + D1A, không có B (D2) / C (D3)
    assert _codes(out)[0] == "A"                                     # đủ mẫu, ít việc → đứng đầu
    assert all("stats" not in p and "load" not in p for p in out["people"])
    assert "16" in out["note"]
    #  Phòng ngoài phạm vi và phòng không tồn tại trả CÙNG một câu — không lộ phòng nào có thật.
    other = T.run_tool(db, world.h_u, "team_capacity", {"department": "D2"})
    ghost = T.run_tool(db, world.h_u, "team_capacity", {"department": "ZZKHONGCO"})
    assert other.get("error") and other["error"].replace("D2", "?") == ghost["error"].replace("ZZKHONGCO", "?")
    #  Chọn đúng phòng con của mình được.
    sub = T.run_tool(db, world.h_u, "team_capacity", {"department": "D1A"})
    assert set(_codes(sub)) == {"X"}
    #  Trưởng phòng không có khóa 16 không xem được bảng số.
    assert T.run_tool(db, world.h_u, "task_type_stats", {"kind": "purchase_request"}).get("denied") is True


def test_truong_hai_phong_thay_ca_hai(db, world):
    out = T.run_tool(db, world.h2_u, "team_capacity", {"limit": 20})
    assert set(_codes(out)) == {"H2", "B", "C", "ADM"}
    only_d3 = T.run_tool(db, world.h2_u, "team_capacity", {"department": "D3"})
    assert set(_codes(only_d3)) == {"C"}


def test_khoa_16_thay_du_so_moi_phong(db, world, khoa16):
    khoa16(world.adm_u)
    out = T.run_tool(db, world.adm_u, "team_capacity", {"department": "thu mua", "kind": "purchase_request"})
    assert out["detail"] is True and set(_codes(out)) == {"H", "A", "X", "P"}
    a = next(p for p in out["people"] if p["employee_code"] == "A")
    assert a["stats"]["p50_days"] == 3.0 and a["stats"]["n_done"] == 5 and "open_items_total" in a["load"]
    h = next(p for p in out["people"] if p["employee_code"] == "H")
    assert h["stats"]["p50_days"] is None and "chưa đủ" in " ".join(h["reasons"])

    st = T.run_tool(db, world.adm_u, "task_type_stats", {"kind": "purchase_request", "by_person": True})
    rows = {r["employee_code"]: r for r in st["rows"]}
    assert rows["A"]["p50_days"] == 3.0 and rows["X"]["p50_days"] == 8.0 and st["total"] == 2
    types = T.run_tool(db, world.adm_u, "task_type_stats", {"kind": "work_task", "task_type": "bao bì"})
    assert types["task_type"]["name"] == "Thiết kế bao bì"
    assert types["rows"][0]["n_done"] == 5 and types["rows"][0]["p50_days"] == 3.0 and "employee_code" not in types["rows"][0]
    one = T.run_tool(db, world.adm_u, "task_type_stats", {"person": "B", "by_person": True})
    assert {r["employee_code"] for r in one["rows"]} == {"B"}


def test_tham_so_la_khong_vo(db, world, khoa16):
    khoa16(world.adm_u)
    assert "error" in T.run_tool(db, world.adm_u, "team_capacity", {"kind": "khong-co"})
    assert "error" in T.run_tool(db, world.adm_u, "task_type_stats", {"task_type": "x" * 5000})
    assert "error" in T.run_tool(db, world.adm_u, "task_type_stats", {"person": "ZZKHONGCO"})
    out = T.run_tool(db, world.adm_u, "team_capacity", {"department": "D1", "limit": 10_000, "window_days": "abc"})
    assert len(out["people"]) <= 20


def test_khai_du_o_cong_mcp_va_bo_loc(db):
    from app.modules.agent_hub import intent_ledger, mcp, mcp_settings
    from app.modules.assistant import tool_router

    for name in ("team_capacity", "task_type_stats"):
        assert name in mcp.READ_TOOLS and name in mcp_settings.GROUP_OF and name in intent_ledger.TOOL_SUB
    assert "capacity" in tool_router.groups_for("Ai đang rảnh làm thiết kế bao bì?")
    assert "capacity" in tool_router.groups_for("loại việc này trung vị mất bao lâu")
