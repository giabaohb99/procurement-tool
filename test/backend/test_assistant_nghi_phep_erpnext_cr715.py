"""duoc-CR-713 / CR-715 phía AI — Trợ lý web, bot, cổng MCP theo kịp nghỉ phép kiểu ERPNext.

1. `draft_leave_comp_request` (mới): soạn nháp phiếu xin nghỉ bù chạy trước đúng các chốt của service, lập hộ theo
   luật `ensure_can_create_for` (mã lạ và mã ngoài phạm vi cùng một câu), xác nhận tạo / gửi duyệt qua `draft_create`
   và cổng MCP (`confirm_draft` kind=leave_comp, nhóm G7 "leave" tắt thì chặn).
2. `propose_approval` duyệt được phiếu nghỉ bù, và KHÔNG BAO GIỜ đề xuất cho chính người đi làm.
3. `my_leave_summary`: số còn lại = `available_days` (trừ phần chưa tới tháng), kèm `comp_days`, luật ứng phép, phiếu nghỉ bù.
4. `draft_leave_request`: cảnh báo ngày cấm nghỉ, đơn lùi ngày, chưa đủ ngày vào làm, ứng phép.
"""
import json
import time
from datetime import date, timedelta

import pytest

from app.core import app_settings
from app.core.vn_time import vn_today
from app.modules.agent_hub import draft_create, mcp, mcp_keys, mcp_settings
from app.modules.assistant import tool_router
from app.modules.assistant import tools as T
from app.modules.assistant.tools.update_tool import confirm_update
from app.modules.employee.model import Employee
from app.modules.leave import balance_service
from app.modules.leave.balance_model import LeaveBalance
from app.modules.leave.catalog_model import LeaveBlockPeriod, LeaveType
from app.modules.leave.comp_request_model import LeaveCompRequest
from app.modules.leave.constants import LeaveAccrualMode, LeaveCompStatus
from app.modules.setting import service as setting_service
from app.modules.setting.model import Setting
from app.modules.user.model import User

TOOL = "draft_leave_comp_request"
ENTITY = "leave_comp_request"


@pytest.fixture(autouse=True)
def _settings_from_test_db(db, monkeypatch):
    """Cài đặt nhân sự đọc từ DB của bài kiểm (cache `app_settings` không lẫn giữa các bài)."""
    def load_from_test_db():
        app_settings._cache = {s.skey: s.svalue for s in db.query(Setting).all()}
        app_settings._exp = time.time() + app_settings._TTL

    monkeypatch.setattr(app_settings, "_load", load_from_test_db)
    app_settings.refresh()
    yield
    app_settings.refresh()


@pytest.fixture()
def comp_type(db):
    row = LeaveType(code="comp", name="Nghỉ bù", counts_balance=True, is_compensatory=True, annual_quota_days=0.0)
    db.add(row)
    db.commit()
    return row


def _last_sunday() -> date:
    """Chủ nhật gần nhất ĐÃ QUA (nghỉ theo lịch mặc định) — ngày đi làm hợp lệ để xin nghỉ bù."""
    d = vn_today() - timedelta(days=1)
    while d.weekday() != 6:
        d -= timedelta(days=1)
    return d


def _weekday(start: date, weekday: int) -> date:
    d = start
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


def _user_of(db, employee_id: int) -> User:
    return db.query(User).filter(User.employee_id == employee_id).one()


def _comp(db, user, **args):
    return T.run_tool(db, user, TOOL, {"work_date": _last_sunday().isoformat(), "reason": "Trực kho", **args})


# ── 1. Soạn nháp phiếu xin nghỉ bù ──────────────────────────────────────────────────────

def test_soan_nhap_nghi_bu_chay_truoc_cac_chot_cua_service(db, seed, cap_quyen, comp_type):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, ENTITY, scope="own", read=True, create=True, write=True)
    sun = _last_sunday()

    #  Lý do bắt buộc khi gửi duyệt → luôn hỏi, kể cả lượt gọi thẳng không có lời người dùng.
    ask = T.run_tool(db, user, TOOL, {"work_date": sun.isoformat()})
    assert [q["field"] for q in ask["need_info"]] == ["reason"] and "draft" not in ask

    out = _comp(db, user, days=0.5)
    assert out["status"] == "ready" and out["total"] == 1 and out["kind"] == "leave_comp"
    assert out["draft"] == {"kind": ENTITY, "employee_id": 0, "employee_name": "Người YC",
                            "work_date": sun.isoformat(), "days": 0.5, "reason": "Trực kho"}
    assert out["comp_leave_type"] == "Nghỉ bù" and "KHÔNG tự duyệt" in out["note"]
    assert db.query(LeaveCompRequest).count() == 0                                   # soạn nháp không ghi gì

    workday = T.run_tool(db, user, TOOL, {"work_date": (sun + timedelta(days=1)).isoformat(), "reason": "x"})
    assert "ngày làm việc bình thường" in workday["error"] and "draft" not in workday
    future = T.run_tool(db, user, TOOL, {"work_date": (vn_today() + timedelta(days=3)).isoformat(), "reason": "x"})
    assert "tương lai" in future["error"]
    assert "0,5 hoặc 1" in _comp(db, user, days=2)["error"]
    assert "YYYY-MM-DD" in T.run_tool(db, user, TOOL, {"work_date": "25/10", "reason": "x"})["error"]


def test_chua_khai_loai_nhan_ngay_bu_thi_bao_ro(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, ENTITY, scope="own", read=True, create=True)
    assert "Loại nhận ngày nghỉ bù" in _comp(db, user)["error"]


def test_lap_ho_theo_luat_ensure_can_create_for(db, seed, cap_quyen, comp_type):
    own_only = db.get(User, seed.u_req_id)
    cap_quyen(own_only.id, ENTITY, scope="own", read=True, create=True)
    out = _comp(db, own_only, employee="DEMOTP")
    assert out.get("denied") is True and "cho chính mình" in out["reason"]

    hr = _user_of(db, seed.emp_tp_id)
    cap_quyen(hr.id, ENTITY, scope="all", read=True, create=True)
    cap_quyen(hr.id, "employee", scope="all", read=True)
    out = _comp(db, hr, employee="testreq")                                          # mã không phân biệt hoa thường
    assert out["draft"]["employee_id"] == seed.emp_req_id and out["draft"]["employee_name"] == "Người YC"

    #  Có quyền lập hộ nhưng hồ sơ nhân sự chỉ phạm vi "của mình": mã có thật ngoài phạm vi == mã không có.
    narrow = db.get(User, seed.u_nstm_id)
    cap_quyen(narrow.id, ENTITY, scope="all", read=True, create=True)
    cap_quyen(narrow.id, "employee", scope="own", read=True)
    hidden = _comp(db, narrow, employee="TESTREQ")["error"]
    ghost = _comp(db, narrow, employee="ZZKHONGCO")["error"]
    assert hidden.replace("TESTREQ", "?") == ghost.replace("ZZKHONGCO", "?")


# ── 1b. Xác nhận: tạo + gửi duyệt bằng service của web; bot / cổng MCP dùng chung ─────────

def test_xac_nhan_tao_gui_duyet_va_ai_duyet_khong_tu_duyet(db, seed, cap_quyen, comp_type):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, ENTITY, scope="own", read=True, create=True, write=True)
    cap_quyen(user.id, "leave_request", scope="own", read=True)
    draft = _comp(db, user)["draft"]

    assert draft_create.kind_of(TOOL) == "leave_comp"
    assert any("Ngày đi làm" in line for line in draft_create.summarize("leave_comp", draft))
    code, oid = draft_create.create(db, user, "leave_comp", draft)
    obj = db.get(LeaveCompRequest, oid)
    assert obj.code == code and obj.status == int(LeaveCompStatus.DRAFT) and obj.employee_id == seed.emp_req_id
    with pytest.raises(draft_create.DraftError, match="mỗi ngày một phiếu"):         # chốt của service đi nguyên văn
        draft_create.create(db, user, "leave_comp", draft)
    draft_create.submit(db, user, "leave_comp", oid)
    db.refresh(obj)
    assert obj.status == int(LeaveCompStatus.PENDING)
    assert any("Chờ duyệt" in line for line in draft_create.created_details(db, "leave_comp", oid))

    #  Người đi làm có cả quyền duyệt phạm vi "tất cả" vẫn KHÔNG được đề xuất duyệt phiếu của chính mình.
    cap_quyen(user.id, ENTITY, scope="all", read=True, approve=True)
    self_try = T.run_tool(db, user, "propose_approval", {"entity": ENTITY, "id": oid, "action": "approve"})
    assert self_try.get("denied") is True and "proposal" not in self_try

    boss = _user_of(db, seed.emp_tp_id)
    cap_quyen(boss.id, ENTITY, scope="all", read=True, approve=True)
    out = T.run_tool(db, boss, "propose_approval", {"entity": ENTITY, "code": code, "action": "approve"})
    p = out["proposal"]
    assert p["entity_label"] == "phiếu nghỉ bù" and p["url"] == f"/hr/leave-comp-requests/{oid}"
    assert "Ngày đi làm" in str(p["summary"])
    done = confirm_update(db, boss, p["confirm_token"])
    db.refresh(obj)
    assert done["approved"] is True and obj.status == int(LeaveCompStatus.APPROVED)

    summary = T.run_tool(db, user, "my_leave_summary", {"year": obj.balance_year})
    row = next(b for b in summary["balances"] if b["leave_type_id"] == comp_type.id)
    assert row["comp_days"] == 1.0 and row["remaining_days"] == 1.0 and row["is_compensatory"] is True
    assert summary["comp_requests"][0]["code"] == code
    assert summary["comp_requests"][0]["status_label"] == "Đã duyệt"


def test_cong_mcp_confirm_draft_leave_comp_va_nhom_leave_tat_thi_chan(db, seed, cap_quyen, comp_type, monkeypatch):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, ENTITY, scope="own", read=True, create=True, write=True)
    draft = _comp(db, user)["draft"]

    class _Key:
        scope, id = mcp_keys.SCOPE_WRITE, 1

    def call(args):
        res = mcp.handle(db, user, _Key(), {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                            "params": {"name": "confirm_draft", "arguments": args}}, {})
        return json.loads(res["result"]["content"][0]["text"])

    assert mcp_settings.GROUP_OF[TOOL].key == "leave"
    real = mcp_settings.tool_blocked
    monkeypatch.setattr(mcp_settings, "tool_blocked",
                        lambda db_, name, args=None: "Nhóm Nghỉ phép đang tắt." if name == TOOL else real(db_, name, args))
    assert call({"kind": "leave_comp", "draft": draft}).get("denied") is True
    assert db.query(LeaveCompRequest).count() == 0
    monkeypatch.setattr(mcp_settings, "tool_blocked", real)
    out = call({"kind": "leave_comp", "draft": draft, "submit": True})
    assert out["ok"] is True and out["submitted"] is True and out["link"] == f"/hr/leave-comp-requests/{out['id']}"
    assert db.get(LeaveCompRequest, out["id"]).status == int(LeaveCompStatus.PENDING)


def test_bo_loc_cong_cu_nap_nhom_nghi_phep_cho_cau_nghi_bu():
    for text in ("tôi đi trực kho chủ nhật vừa rồi, xin nghỉ bù", "làm ngày lễ 2/9 được bù không",
                 "loại phép này có cho ứng phép không"):
        assert "leave" in tool_router.groups_for(text), text


# ── 3. my_leave_summary đọc đúng số dùng được + luật loại nghỉ ──────────────────────────

def test_tom_tat_phep_tru_phan_chua_toi_thang_va_neu_luat_ung_phep(db, seed, cap_quyen, monkeypatch):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "leave_request", scope="own", read=True)
    db.get(Employee, seed.emp_req_id).hire_date = date(2020, 2, 1)
    lt = LeaveType(code="annual", name="Phép năm", counts_balance=True, annual_quota_days=12.0,
                   accrual_mode=int(LeaveAccrualMode.MONTHLY), max_negative_days=2.0, applicable_after_days=30)
    db.add(lt)
    db.flush()
    db.add(LeaveBalance(employee_id=seed.emp_req_id, year=2026, leave_type_id=lt.id, allocated_days=12.0))
    db.commit()
    monkeypatch.setattr(balance_service, "vn_today", lambda: date(2026, 5, 10))

    out = T.run_tool(db, user, "my_leave_summary", {"year": 2026})
    row = next(b for b in out["balances"] if b["leave_type_id"] == lt.id)
    assert row["total_days"] == 12.0 and row["remaining_days"] == 5.0 and row["not_yet_accrued_days"] == 7.0
    assert row["accrual_mode_label"] == "Cộng dần theo tháng"
    assert row["max_negative_days"] == 2.0 and row["applicable_after_days"] == 30 and row["comp_days"] == 0.0
    assert out["comp_requests"] == []                       # không có khóa leave_comp_request → bỏ qua, không chặn
    assert {"comp_days", "max_negative_days"} <= set(out["glossary"])


# ── 4. draft_leave_request nói trước các luật mới ───────────────────────────────────────

def _leave_type(db, **kw):
    row = LeaveType(code=kw.pop("code", "annual"), name=kw.pop("name", "Phép năm"), **kw)
    db.add(row)
    db.commit()
    return row


def _draft_leave(db, user, day: date, to: date | None = None, leave_type="annual"):
    return T.run_tool(db, user, "draft_leave_request", {"from_date": day.isoformat(),
                                                        "to_date": (to or day).isoformat(),
                                                        "reason": "Việc gia đình", "leave_type": leave_type})


def test_nhap_don_nghi_canh_bao_ngay_cam_nghi_va_khong_chan(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "leave_request", scope="own", read=True, create=True)
    _leave_type(db, counts_balance=False)
    tue = _weekday(vn_today() + timedelta(days=7), 1)
    db.add(LeaveBlockPeriod(company_id=0, department_id=0, from_date=tue, to_date=tue + timedelta(days=1),
                            reason="Kiểm kê kho", is_active=True, created_by=1, updated_by=1))
    db.commit()

    out = _draft_leave(db, user, tue)
    assert out["status"] == "ready"                                                   # cảnh báo, không chặn soạn
    assert any("ngày cấm nghỉ" in w and "Kiểm kê kho" in w for w in out["warnings"])
    assert out["block_conflicts"][0]["reason"] == "Kiểm kê kho"
    assert out["block_conflicts"][0]["from_date"] == tue.isoformat()
    clear = _draft_leave(db, user, tue + timedelta(days=7))
    assert clear["block_conflicts"] == [] and clear["warnings"] == []


def test_nhap_don_nghi_bao_don_lui_ngay_va_chua_du_ngay_vao_lam(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "leave_request", scope="own", read=True, create=True)
    _leave_type(db, counts_balance=False, applicable_after_days=60)
    db.get(Employee, seed.emp_req_id).hire_date = vn_today() - timedelta(days=10)
    db.commit()
    past = _weekday(vn_today() - timedelta(days=13), 1)

    assert not any("ngày đã qua" in w for w in _draft_leave(db, user, past)["warnings"])   # công tắc tắt: không báo
    setting_service.save(db, {"leave_restrict_backdated": True}, user_id=1)
    warns = _draft_leave(db, user, past)["warnings"]
    assert any("ngày đã qua" in w and "chặn lúc lưu" in w for w in warns)
    assert any("sau 60 ngày vào làm" in w for w in warns)


def test_nhap_don_nghi_noi_ro_ung_phep(db, seed, cap_quyen):
    user = db.get(User, seed.u_req_id)
    cap_quyen(user.id, "leave_request", scope="own", read=True, create=True)
    lt = _leave_type(db, counts_balance=True, max_negative_days=2.0)
    tue = _weekday(vn_today() + timedelta(days=7), 1)
    db.add(LeaveBalance(employee_id=seed.emp_req_id, year=tue.year, leave_type_id=lt.id, allocated_days=1.0))
    db.commit()

    within = _draft_leave(db, user, tue, tue + timedelta(days=1))                     # 2 ngày, còn 1, ứng tối đa 2
    assert any("ỨNG PHÉP" in w for w in within["warnings"])
    assert not any("chặn lúc gửi duyệt" in w for w in within["warnings"])
    over = _draft_leave(db, user, tue, tue + timedelta(days=3))                       # 4 ngày > 1 + 2
    assert any("vẫn không đủ" in w and "chặn lúc gửi duyệt" in w for w in over["warnings"])
