"""duoc-CR-761 P3 — trợ lý / bot / cổng MCP đọc CA LÀM VIỆC theo ngày.

1. `my_work_shifts`: ca của chính người hỏi — mẫu tuần + ca xếp riêng (thắng) + ngày nghỉ do xếp ca + ngày lễ, tổng giờ.
2. `employee_work_shifts`: ca của nhân sự khác — gác `employee.read` + phạm vi xem hồ sơ (như màn Xem lịch), cùng một câu
   cho người ngoài phạm vi và người không tồn tại, trần người × ngày, số truy vấn cố định.
3. Sổ khai: bộ lọc công cụ, cổng MCP (chỉ đọc + ngân sách dòng), nhóm G7.
Mốc ngày cố định `MON` = 05/01/2026 (thứ Hai).
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from app.core.work_schedule_codes import WorkScheduleLevel
from app.modules.assistant import tool_router as tr
from app.modules.assistant import tools as T
from app.modules.assistant.tools import work_shift_days, work_shift_tool
from app.modules.assistant.tools.base import ToolContext
from app.modules.assistant.tools.employee_leave_tool import NOT_FOUND
from app.modules.assistant.tools.work_shift_tool import EMPLOYEE_WORK_SHIFTS_SPEC
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.leave.catalog_model import Holiday
from app.modules.user.model import User
from app.modules.work_schedule.model import WorkShiftDay, WorkShiftSegment
from app.modules.work_schedule.shift_view import build_my_days
from lich_lam_viec_factory import MON, SUN, assign, count_queries, make_schedule, make_world, week_t2_t6_sat_am

LONG_AGO = date(2020, 1, 1)
TUE, WED, THU = MON + timedelta(days=1), MON + timedelta(days=2), MON + timedelta(days=3)
LIVESTREAM = [(8, 10), (14, 16), (20, 23)]   # 2 + 2 + 3 = 7 giờ, ba khung rời
WEEK = {"from_date": MON.isoformat(), "to_date": SUN.isoformat()}


def _put_shift(db, emp_id, day, segments, note=""):
    row = WorkShiftDay(employee_id=emp_id, work_date=day, note=note)
    db.add(row)
    db.flush()
    for order, (a, b) in enumerate(segments):
        db.add(WorkShiftSegment(shift_day_id=row.id, start_hour=a, end_hour=b, sort_order=order))
    db.flush()


def _week_world(db, seed):
    """Phòng Test theo lịch T2–T6 cả ngày + T7 sáng; người YC có ca livestream thứ Ba, nghỉ do xếp ca thứ Tư; lễ thứ Năm."""
    sched = make_schedule(db, "Lịch phòng Test", week_t2_t6_sat_am())
    assign(db, WorkScheduleLevel.DEPARTMENT, seed.dept_id, sched.id, LONG_AGO)
    _put_shift(db, seed.emp_req_id, TUE, LIVESTREAM, note="Livestream")
    _put_shift(db, seed.emp_req_id, WED, [])
    db.add(Holiday(company_id=0, date=THU, name="Lễ thử", is_recurring=False, is_active=True))
    db.commit()


def _mine(db, user_id, **args):
    return T.run_tool(db, db.get(User, user_id), "my_work_shifts", args)


def _team(db, user_id, **args):
    return T.run_tool(db, db.get(User, user_id), "employee_work_shifts", args)


# ── 1. my_work_shifts ───────────────────────────────────────────────────────────────

def test_ca_cua_toi_gop_mau_tuan_ca_xep_rieng_va_ngay_le(db, seed):
    _week_world(db, seed)
    out = _mine(db, seed.u_req_id, **WEEK)
    days = out["days"]
    assert out["employee"]["code"] == "TESTREQ" and len(days) == 7 and out["url"] == "/me"
    assert days[0] == {"date": MON.isoformat(), "weekday": "Thứ Hai", "source": work_shift_days.SOURCE_TEMPLATE,
                       "segments": ["08:00–12:00", "13:00–17:00"], "hours": 8.0, "schedule_name": "Lịch phòng Test"}
    #  Ca xếp riêng THẮNG mẫu tuần: ba khung rời, 7 giờ, kèm ghi chú.
    assert days[1]["source"] == work_shift_days.SOURCE_SHIFT and days[1]["hours"] == 7
    assert days[1]["segments"] == ["08:00–10:00", "14:00–16:00", "20:00–23:00"] and days[1]["note"] == "Livestream"
    #  Ngày có dòng xếp ca mà không khung = nghỉ do xếp ca.
    assert days[2]["source"] == work_shift_days.SOURCE_SHIFT and days[2]["is_day_off"] is True and days[2]["hours"] == 0
    #  Ngày lễ theo mẫu tuần: vẫn bày khung của mẫu nhưng không tính giờ.
    assert days[3]["holiday_name"] == "Lễ thử" and days[3]["hours"] == 0
    assert days[5]["segments"] == ["08:00–12:00"] and days[5]["hours"] == 4
    assert days[6]["is_day_off"] is True and days[6]["hours"] == 0
    assert out["total_hours"] == 8 + 7 + 8 + 4 and out["work_days"] == 4
    assert out["shift_dates"] == [TUE.isoformat(), WED.isoformat()]
    assert "salary" not in str(out) and "lương" not in str(out)


def test_ca_xep_vao_ngay_le_van_tinh_gio(db, seed):
    """Người xếp ca đã chủ động xếp ca vào ngày lễ (livestream dịp lễ) → ngày đó tính là ngày phải đi làm."""
    _put_shift(db, seed.emp_req_id, THU, [(9, 12)])
    db.add(Holiday(company_id=0, date=THU, name="Lễ thử", is_recurring=False, is_active=True))
    db.commit()
    day = _mine(db, seed.u_req_id, from_date=THU.isoformat(), to_date=THU.isoformat())["days"][0]
    assert day["source"] == work_shift_days.SOURCE_SHIFT and day["holiday_name"] == "Lễ thử" and day["hours"] == 3


def test_ca_cua_toi_chi_cua_chinh_minh_va_khoang_mac_dinh_tuan_nay(db, seed, monkeypatch):
    _week_world(db, seed)
    monkeypatch.setattr(work_shift_days, "vn_today", lambda: WED)
    other = _mine(db, seed.u_nstm_id)   # không có tham số chọn người: người khác hỏi thì ra lịch của chính họ
    assert other["employee"]["code"] == "DEMONV" and other["shift_dates"] == []
    assert (other["from_date"], other["to_date"]) == (MON.isoformat(), SUN.isoformat())
    nxt = _mine(db, seed.u_req_id, week_offset=1)
    assert nxt["from_date"] == (MON + timedelta(weeks=1)).isoformat()
    #  Tham số lạ ở ô chọn người bị bỏ qua (schema không có ô đó).
    assert _mine(db, seed.u_req_id, employee="DEMONV", **WEEK)["employee"]["code"] == "TESTREQ"


def test_ca_cua_toi_tai_khoan_chua_gan_ho_so_va_khoang_sai(db, seed):
    ghost = User(email="KHONGHOSO", employee_id=0, password_hash="x", is_active=True)
    db.add(ghost)
    db.commit()
    assert "chưa gắn hồ sơ nhân sự" in _mine(db, ghost.id)["error"]
    for bad in ({"from_date": "16/11/2026"}, {"from_date": SUN.isoformat(), "to_date": MON.isoformat()},
                {"from_date": MON.isoformat(), "to_date": (MON + timedelta(days=42)).isoformat()},
                {"from_date": "x" * 5000}, {"from_date": "9999-01-01"}):
        assert "error" in _mine(db, seed.u_req_id, **bad), bad
    ok = _mine(db, seed.u_req_id, from_date=MON.isoformat(), to_date=(MON + timedelta(days=41)).isoformat())
    assert len(ok["days"]) == 42


# ── 2. employee_work_shifts ─────────────────────────────────────────────────────────

def _neighbors(db, seed):
    """Người phòng bên cạnh cùng công ty + người công ty khác — đều có ca thứ Ba."""
    side = Department(code="DEPT02", name="Phòng Bên Cạnh", company_id=seed.company_id, is_active=True)
    company = Company(name="Cty Khác", code="CK01", is_active=True)
    db.add_all([side, company])
    db.flush()
    side_emp = Employee(code="BENCANH1", full_name="Người Bên Cạnh", company_id=seed.company_id,
                        department_id=side.id, is_active=True)
    far_emp = Employee(code="KHAC01", full_name="Lê Văn Khác", company_id=company.id, department_id=0, is_active=True)
    db.add_all([side_emp, far_emp])
    db.flush()
    for emp in (side_emp, far_emp):
        _put_shift(db, emp.id, TUE, [(18, 22)], note="BIMATPHONGKHAC")
    db.commit()


def test_ca_nguoi_khac_can_quyen_xem_ho_so(db, seed):
    out = _team(db, seed.u_nstm_id, employee="TESTREQ", **WEEK)
    assert out.get("denied") is True and "employees" not in out


def test_ca_nguoi_khac_truong_phong_chi_thay_phong_minh(db, seed, cap_quyen):
    _week_world(db, seed)
    _neighbors(db, seed)
    cap_quyen(seed.u_nstm_id, "employee", scope="dept", read=True)
    cap_quyen(seed.u_nstm_id, "work_schedule_personal", scope="dept", read=True)   # Trưởng phòng: thấy phòng mình (CR-761)

    out = _team(db, seed.u_nstm_id, employee="nguoi yc", **WEEK)   # không dấu vẫn khớp "Người YC"
    assert [e["code"] for e in out["employees"]] == ["TESTREQ"] and out["url"] == "/hr/work-roster"
    row = out["employees"][0]
    assert row["department_name"] == "Phòng Test" and row["total_hours"] == 27
    assert row["days"][1] == {"date": TUE.isoformat(), "weekday": "T3", "shift": True, "note": "Livestream",
                              "segments": ["08:00–10:00", "14:00–16:00", "20:00–23:00"], "hours": 7}
    assert row["days"][2]["off"] is True and row["days"][3]["holiday"] == "Lễ thử" and "shift" not in row["days"][0]
    assert "schedule_name" not in row["days"][0]   # bản nhiều người không lặp tên lịch từng ô

    whole = _team(db, seed.u_nstm_id, department="phòng Test", **WEEK)
    assert sorted(e["code"] for e in whole["employees"]) == ["BACKUP01", "DEMONV", "DEMOTP", "TESTREQ"]
    #  Người phòng khác / công ty khác và người không tồn tại: CÙNG một câu, không lộ ca.
    side = _team(db, seed.u_nstm_id, employee="BENCANH1", **WEEK)
    far = _team(db, seed.u_nstm_id, employee="KHAC01", **WEEK)
    missing = _team(db, seed.u_nstm_id, employee="ZZZ-KHONG-CO", **WEEK)
    assert side["employees"] == far["employees"] == missing["employees"] == []
    assert side["note"] == far["note"] == missing["note"] == NOT_FOUND
    assert _team(db, seed.u_nstm_id, department="Phòng Bên Cạnh", **WEEK)["employees"] == []
    assert "BIMATPHONGKHAC" not in str(_team(db, seed.u_nstm_id, department="Phòng", **WEEK))


def test_ca_nguoi_khac_nhan_su_ca_cong_ty_thay_ca_phong_ben_canh(db, seed, cap_quyen):
    _neighbors(db, seed)
    cap_quyen(seed.u_nstm_id, "employee", scope="company", read=True)
    cap_quyen(seed.u_nstm_id, "work_schedule", scope="all", read=True, write=True)   # Nhân sự: phạm vi employee
    side = _team(db, seed.u_nstm_id, department="bộ phận bên cạnh", **WEEK)["employees"]
    assert [e["code"] for e in side] == ["BENCANH1"] and side[0]["days"][1]["segments"] == ["18:00–22:00"]
    assert _team(db, seed.u_nstm_id, employee="KHAC01", **WEEK)["employees"] == []   # công ty khác vẫn ngoài tầm


def test_ca_nguoi_khac_tran_so_nguoi_so_ngay_va_tham_so_rac(db, seed, cap_quyen, monkeypatch):
    cap_quyen(seed.u_nstm_id, "employee", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "work_schedule", scope="all", read=True, write=True)   # Nhân sự: phạm vi employee
    assert "error" in _team(db, seed.u_nstm_id, **WEEK)
    out = _team(db, seed.u_nstm_id, department=str(seed.dept_id), limit=2, **WEEK)
    assert out["total"] == 4 and len(out["employees"]) == 2 and out["has_more"] is True and out["note"]
    assert _team(db, seed.u_nstm_id, department=str(seed.dept_id), limit="x", **WEEK)["total"] == 4
    too_long = {"from_date": MON.isoformat(), "to_date": (MON + timedelta(days=14)).isoformat()}
    assert "14 ngày" in _team(db, seed.u_nstm_id, department="phong test", **too_long)["error"]
    #  Trần người × ngày: 14 ngày × trần 28 ô → mỗi lượt 2 người dù xin 50.
    monkeypatch.setattr(work_shift_tool, "TEAM_MAX_CELLS", 28)
    two_weeks = {"from_date": MON.isoformat(), "to_date": (MON + timedelta(days=13)).isoformat()}
    capped = _team(db, seed.u_nstm_id, department="phong test", limit=50, **two_weeks)
    assert len(capped["employees"]) == 2 and capped["has_more"] is True
    assert _team(db, seed.u_nstm_id, employee="x" * 5000, **WEEK)["employees"] == []
    for raw in ("0", "-1"):
        assert _team(db, seed.u_nstm_id, department=raw, **WEEK)["employees"] == [], raw


def _many(db, n):
    company, dept, first = make_world(db, f"CA{n}")
    sched = make_schedule(db, f"Lịch {n}", week_t2_t6_sat_am())
    assign(db, WorkScheduleLevel.DEPARTMENT, dept.id, sched.id, LONG_AGO)
    db.add(Holiday(company_id=company.id, date=THU, name="Lễ riêng", is_recurring=False, is_active=True))
    _put_shift(db, first.id, TUE, LIVESTREAM)
    for i in range(n):
        emp = Employee(code=f"CA{n}-{i}", full_name=f"Nhân sự {i}", company_id=company.id,
                       department_id=dept.id, is_active=True)
        db.add(emp)
        db.flush()
        _put_shift(db, emp.id, MON + timedelta(days=i % 7), [(8, 12), (19, 22)])
    db.commit()
    return dept, first


def test_so_truy_van_co_dinh_va_ban_nhieu_nguoi_khop_ban_mot_nguoi(db, seed, cap_quyen):
    cap_quyen(seed.u_nstm_id, "employee", scope="all", read=True)
    cap_quyen(seed.u_nstm_id, "work_schedule", scope="all", read=True, write=True)   # Nhân sự: phạm vi employee
    ctx = ToolContext(db, db.get(User, seed.u_nstm_id))
    counts = []
    for n in (2, 10):
        dept, first = _many(db, n)
        args = {"department": str(dept.id), "limit": 50, **WEEK}
        EMPLOYEE_WORK_SHIFTS_SPEC.handler(ctx, args)   # nạp sẵn hồ sơ quyền
        out, sql = count_queries(db, lambda a=args: EMPLOYEE_WORK_SHIFTS_SPEC.handler(ctx, a))
        assert len(out["employees"]) == n + 1
        counts.append(len(sql))
        #  Bản gom nhiều người phải cho ĐÚNG kết quả của bản một người (`shift_view.build_my_days`).
        many = work_shift_days.build_days_many(db, [first], MON, SUN)[first.id]
        assert many == build_my_days(db, first, MON, SUN)
        assert many[3]["holiday_name"] == "Lễ riêng" and many[1]["is_shift"] is True
    assert counts[0] == counts[1], counts


# ── 3. Sổ khai: bộ lọc công cụ, cổng MCP, nhóm G7 ───────────────────────────────────

@pytest.mark.parametrize("q,must", [
    ("ca của tôi tuần này", {"my_work_shifts"}),
    ("lịch làm tuần này của anh thế nào", {"my_work_shifts"}),
    ("tuần này tôi làm mấy giờ", {"my_work_shifts"}),
    ("ca livestream thứ 7", {"my_work_shifts"}),
    ("phòng Kinh doanh tuần này ai làm ca nào", {"employee_work_shifts"}),
    ("xếp ca cho bé Lan ở đâu", {"employee_work_shifts"}),
])
def test_bo_loc_cong_cu_nap_nhom_ca(q, must):
    picked = tr.select(q)
    assert picked is not None and must <= picked, (q, sorted(must - (picked or set())))
    assert len(picked) < 40


def test_khong_nap_nhom_ca_cho_cau_lich_google():
    assert "my_work_shifts" not in (tr.select("lịch hôm nay của anh") or set())


def test_cong_mcp_chi_doc_ngan_sach_dong_va_nhom_g7(mcp_all_groups):
    from app.modules.agent_hub import intent_ledger, mcp, mcp_keys, mcp_settings

    names = {"my_work_shifts", "employee_work_shifts"}
    assert names <= mcp.READ_TOOLS and "employee_work_shifts" in mcp.ROW_BUDGET_TOOLS
    assert not any(mcp.is_write_tool(n) for n in names)
    owner = SimpleNamespace(id=1, is_active=True)
    assert names <= {t["name"] for t in mcp.list_tools(None, owner, mcp_keys.SCOPE_READ)}
    groups = [g for g in mcp_settings.GROUPS if names & g.tools]
    assert len(groups) == 1 and names <= groups[0].tools and groups[0].default_on is True
    assert names <= set(intent_ledger.TOOL_SUB)


# ── 4. scripts/publish_handbook_update.py --sync-summary: tóm tắt skill mới tới được hệ đang chạy ───────────────────

@pytest.fixture
def nghi_phep_skill(db, seed):
    """Bộ cẩm nang đã gieo, skill `nghi-phep` mang tóm tắt CŨ ở cả dòng skill lẫn bản xuất bản (như dev / prod)."""
    from app.modules.ai_skill import handbook_seed
    from app.modules.ai_skill.model import AiSkill, AiSkillSet, AiSkillVersion

    handbook_seed.ensure_system_handbook(db)
    skill_set = db.query(AiSkillSet).filter(AiSkillSet.code == handbook_seed.SET_CODE).one()
    skill = db.query(AiSkill).filter(AiSkill.skill_set_id == skill_set.id, AiSkill.slug == "nghi-phep").one()
    skill.summary = "Nghỉ phép: loại nghỉ, quỹ phép, nộp đơn, duyệt, hủy đơn."
    db.get(AiSkillVersion, skill.current_version_id).summary = skill.summary
    db.commit()
    _slug, title, summary, body = next(f for f in handbook_seed.seed_files() if f[0] == "nghi-phep")
    return SimpleNamespace(skill=skill, title=title, summary=summary, body=body)


def _versions(db, skill):
    from app.modules.ai_skill.model import AiSkillVersion

    return db.query(AiSkillVersion).filter(AiSkillVersion.skill_id == skill.id).all()


def test_dong_bo_tom_tat_xuat_ban_phien_ban_moi(db, nghi_phep_skill):
    from app.modules.ai_skill.model import AiSkillVersion
    from test_cam_nang_van_phong_cr235 import _load_publish_script

    script, x = _load_publish_script(), nghi_phep_skill
    assert "ca làm việc" in x.summary[:160]   # danh mục trong lời nhắc chỉ giữ 160 ký tự đầu
    #  Không bật cờ: hành vi cũ — nội dung trùng tệp là đã mới nhất, tóm tắt cũ nằm lại.
    assert script.decide_update(x.skill, _versions(db, x.skill), x.body, x.summary) == ("latest", "", False)
    assert script.decide_update(x.skill, _versions(db, x.skill), x.body, x.summary, True) == ("publish", "", True)

    before = len(_versions(db, x.skill))
    x.skill.summary = x.summary
    script.publish_new_version(db, x.skill, _versions(db, x.skill), x.body, x.title, "duoc-CR-761")
    db.commit()
    current = db.get(AiSkillVersion, x.skill.current_version_id)
    assert (current.summary, current.body_md, current.published_by) == (x.summary, x.body, 0)
    assert len(_versions(db, x.skill)) == before + 1
    #  Chạy lại lần hai: đã mới nhất, không sinh phiên bản.
    assert script.decide_update(x.skill, _versions(db, x.skill), x.body, x.summary, True)[0] == "latest"


def test_dong_bo_tom_tat_khong_de_ban_quan_tri_sua_tay(db, nghi_phep_skill):
    from test_cam_nang_van_phong_cr235 import _load_publish_script

    script, x = _load_publish_script(), nghi_phep_skill
    x.skill.summary = "Quản trị đang sửa dở tóm tắt"   # sửa ở màn Bộ skill, chưa xuất bản
    action, reason, changed = script.decide_update(x.skill, _versions(db, x.skill), x.body, x.summary, True)
    assert action == "publish" and changed is True and "quản trị đang soạn dở" in reason
    x.skill.summary = _versions(db, x.skill)[-1].summary
    _versions(db, x.skill)[-1].published_by = 5           # quản trị đã tự xuất bản một bản
    assert script.decide_update(x.skill, _versions(db, x.skill), x.body, x.summary, True)[1] != ""
