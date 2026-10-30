"""bao-CR-634 — quản trị Kho skill + khóa AI BẰNG LỜI qua cổng MCP (K9, doc/erp/21 §7.2 đợt P7).

Cố làm nó SAI: khóa chỉ đọc / người không quyền gọi tool quản trị; xác nhận khi chưa soạn nháp, với token sửa tay, token
của người khác, token khác loại, bản nháp đã dùng rồi, đích bị sửa chen giữa hai bước; biên tập phòng này với tay sang bộ
phòng khác, hoặc mất phạm vi giữa lúc soạn và lúc xác nhận; tên đối tượng mơ hồ. Và hoàn tác 24 giờ của sổ thay đổi.
"""
import json
from types import SimpleNamespace

import pytest

from app.core.subject_match import SUBJECT_DEPARTMENT, SUBJECT_EMPLOYEE
from app.modules.agent_hub import mcp, mcp_admin, mcp_keys, mcp_settings
from app.modules.agent_hub.model import AgentMcpKey
from app.modules.ai_skill import access_service, service
from app.modules.ai_skill.model import AiSkill, AiSkillAccess, AiSkillVersion
from app.modules.ai_skill.schema import SkillPatch, SkillSetIn, SkillSetPatch
from app.modules.assistant import change_service
from app.modules.assistant.change_model import AssistantChange, ChangeAction, ChangeSource
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.user.model import User

from test_ai_skill_kho_k1 import admin, give, make_skill, org  # noqa: F401 — dùng chung thế giới mẫu của K1

SKILL_TOOLS = {"draft_skill", "draft_skill_publish", "draft_skill_access"}
KEY_TOOLS = {"draft_key_issue", "draft_key_revoke"}


class _Key:
    def __init__(self, scope=mcp_keys.SCOPE_WRITE):
        self.scope = scope
        self.id = 0


def _call(db, user, name, args, scope=mcp_keys.SCOPE_WRITE):
    trace = {}
    res = mcp.handle(db, user, _Key(scope), {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                            "params": {"name": name, "arguments": args}}, trace)
    return json.loads(res["result"]["content"][0]["text"]), trace


def _confirm(db, user, out, scope=mcp_keys.SCOPE_WRITE, kind=None):
    return _call(db, user, "confirm_draft", {"kind": kind or out["kind"], "draft": out["draft"]}, scope)


def _names(db, user, scope=mcp_keys.SCOPE_WRITE):
    return {t["name"] for t in mcp.list_tools(db, user, scope)}


def _skill(db, slug):
    return db.query(AiSkill).filter(AiSkill.slug == slug, AiSkill.is_deleted.is_(False)).one_or_none()


# ── Ai thấy, ai gọi được ────────────────────────────────────────────────────────────

def test_only_write_key_with_rights_lists_admin_tools(org, admin):
    db = org.db
    assert _names(db, admin) >= SKILL_TOOLS and not (_names(db, admin) & KEY_TOOLS)     # chưa có ai_mcp_key_admin
    assert not (_names(db, admin, mcp_keys.SCOPE_READ) & mcp_admin.TOOL_NAMES)           # khóa chỉ đọc
    assert not (_names(db, org.boss) & mcp_admin.TOOL_NAMES)                             # không quyền gì
    body, trace = _call(db, admin, "draft_skill", {"skill_set": "x", "name": "y"}, mcp_keys.SCOPE_READ)
    assert body["denied"] and trace["status"] == 2
    body, _ = _call(db, org.boss, "draft_skill", {"skill_set": "x", "name": "y"})
    assert body["denied"] and "không có quyền" in body["error"]


def test_group_switched_off_hides_and_blocks_admin_tools(org, admin, monkeypatch):
    db = org.db
    monkeypatch.setattr(mcp_settings, "_stored", lambda _db: {"groups": {"admin": False}})
    assert not (_names(db, admin) & mcp_admin.TOOL_NAMES)
    body, _ = _call(db, admin, "draft_skill", {"skill_set": "x", "name": "y"})
    assert body["denied"]


def test_publish_tool_needs_approve_not_just_write(org, cap_quyen):
    db = org.db
    cap_quyen(org.kt.id, "ai_skill", scope="all", read=True, write=True)
    names = _names(db, org.kt)
    assert {"draft_skill", "draft_skill_access"} <= names and "draft_skill_publish" not in names


# ── Nháp → xác nhận ─────────────────────────────────────────────────────────────────

def test_draft_writes_nothing_and_confirm_creates_skill_with_change_log(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin)
    out, _ = _call(db, admin, "draft_skill", {"skill_set": skill_set.code, "name": "quy-trinh-nhap",
                                              "title": "Quy trình nhập", "summary": "Khi nhập khẩu", "body_md": "# A"})
    assert out["kind"] == "skill" and out["draft"]["token"] and _skill(db, "quy-trinh-nhap") is None
    done, trace = _confirm(db, admin, out)
    created = _skill(db, "quy-trinh-nhap")
    assert done["ok"] and created is not None and created.draft_body_md == "# A" and not created.current_version_id
    assert trace["skill_id"] == created.id and "skill_id" not in done
    log = db.query(AssistantChange).filter_by(entity="ai_skill", entity_id=created.id).one()
    assert (log.action, log.source) == (int(ChangeAction.CREATE), int(ChangeSource.MCP))


def test_confirm_rejects_missing_tampered_foreign_wrong_kind_and_reused_drafts(org, admin, cap_quyen):
    db = org.db
    skill_set, skill = make_skill(db, admin)
    out, _ = _call(db, admin, "draft_skill", {"name": f"{skill_set.code}/quy-trinh-mua", "body_md": "# Mới"})
    assert "nội dung" in out["preview"]
    assert "Thiếu bản nháp" in _call(db, admin, "confirm_draft", {"kind": "skill", "draft": {}})[0]["error"]
    bad = {"kind": "skill", "draft": {"token": out["draft"]["token"][:-4] + "AAAA"}}
    assert "hết hạn hoặc không hợp lệ" in _call(db, admin, "confirm_draft", bad)[0]["error"]
    cap_quyen(org.kt.id, "ai_skill", scope="all", read=True, write=True)
    assert "không phải của bạn" in _confirm(db, org.kt, out)[0]["error"]
    cap_quyen(org.kt.id, "ai_skill", scope="all", read=True, write=True, approve=True)
    assert "không phải \"skill_publish\"" in _confirm(db, admin, out, kind="skill_publish")[0]["error"]
    assert _confirm(db, admin, out)[0]["ok"]
    db.refresh(skill)
    assert skill.draft_body_md == "# Mới"
    again, _ = _confirm(db, admin, out)                                    # dùng lại cùng bản nháp
    assert "đã đổi sau lúc soạn" in again["error"]


def test_target_edited_between_draft_and_confirm_is_rejected(org, admin):
    db = org.db
    _, skill = make_skill(db, admin)
    out, _ = _call(db, admin, "draft_skill", {"name": "quy-trinh-mua", "summary": "Tóm tắt mới"})
    service.update_skill(db, skill.id, SkillPatch(body_md="người khác sửa chen"), admin)
    assert "đã đổi sau lúc soạn" in _confirm(db, admin, out)[0]["error"]
    db.refresh(skill)
    assert skill.summary == "Khi lập YCMH"


def test_draft_with_no_change_and_bad_slug_say_so(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin)
    same, _ = _call(db, admin, "draft_skill", {"name": "quy-trinh-mua", "summary": "Khi lập YCMH"})
    assert "không có gì để sửa" in same["error"]
    bad, _ = _call(db, admin, "draft_skill", {"skill_set": skill_set.code, "name": "có dấu và cách"})
    assert "chưa hợp lệ" in bad["error"] and "chữ không dấu" in bad["error"]
    climb, _ = _call(db, admin, "draft_skill", {"name": "../etc"})          # «..» bị coi là mã bộ, không ra bộ nào
    assert "error" in climb and _skill(db, "etc") is None
    missing, _ = _call(db, admin, "draft_skill", {"skill_set": "khong-co-bo-nay", "name": "abc"})
    assert skill_set.code in missing["error"]                              # gợi ý bộ mình được quản lý


def test_update_undo_restores_previous_draft_and_blocks_after_manual_edit(org, admin):
    db = org.db
    _, skill = make_skill(db, admin)
    out, _ = _call(db, admin, "draft_skill", {"name": "quy-trinh-mua", "body_md": "# Bản AI"})
    _confirm(db, admin, out)
    row = db.query(AssistantChange).filter_by(entity="ai_skill", action=int(ChangeAction.UPDATE)).one()
    assert change_service.can_undo(db, admin, row) == (True, "")
    change_service.undo(db, admin, row.id)
    db.refresh(skill)
    assert skill.draft_body_md == "# Bước 1\nLập phiếu"
    out, _ = _call(db, admin, "draft_skill", {"name": "quy-trinh-mua", "body_md": "# Bản AI 2"})
    _confirm(db, admin, out)
    service.update_skill(db, skill.id, SkillPatch(title="sửa tay"), admin)
    latest = db.query(AssistantChange).filter_by(entity="ai_skill", action=int(ChangeAction.UPDATE), undo_of=0) \
        .order_by(AssistantChange.id.desc()).first()
    ok, reason = change_service.can_undo(db, admin, latest)
    assert not ok and "sửa sau lúc AI ghi" in reason


def test_publish_creates_new_version_and_is_logged_but_not_undoable(org, admin):
    db = org.db
    _, skill = make_skill(db, admin)
    nothing, _ = _call(db, admin, "draft_skill_publish", {"name": "quy-trinh-mua"})
    assert "giống hệt phiên bản 1" in nothing["error"]
    service.update_skill(db, skill.id, SkillPatch(body_md="# Bước 1\nLập phiếu\n# Bước 2"), admin)
    out, _ = _call(db, admin, "draft_skill_publish", {"name": "quy-trinh-mua", "change_note": "thêm bước 2"})
    assert out["preview"]["phiên bản"] == "1 → 2" and db.query(AiSkillVersion).count() == 1
    assert _confirm(db, admin, out)[0]["ok"]
    assert db.query(AiSkillVersion).filter_by(skill_id=skill.id).count() == 2
    row = db.query(AssistantChange).filter_by(action=int(ChangeAction.PUBLISH)).one()
    ok, reason = change_service.can_undo(db, admin, row)
    assert not ok and "Xuất bản" in reason


# ── Quyền đọc ───────────────────────────────────────────────────────────────────────

def test_grant_then_revoke_then_undo_revoke_through_drafts(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin)
    seen = lambda u: {r["slug"] for r in access_service.visible_skills(db, u)}  # noqa: E731
    out, _ = _call(db, admin, "draft_skill_access", {"skill_set": skill_set.code,
                                                     "subjects": [{"kind": "department", "ref": org.root.code}]})
    assert out["preview"]["đối tượng"] == [f"{org.root.name} ({org.root.code})"] and seen(org.nk) == set()
    _confirm(db, admin, out)
    assert seen(org.nk) == {"quy-trinh-mua"}                               # phòng con kế thừa
    out, _ = _call(db, admin, "draft_skill_access", {"action": "revoke", "skill_set": skill_set.code,
                                                     "subjects": [{"kind": "department", "ref": "Thu mua"}]})
    assert len(out["preview"]["dòng sẽ thu hồi"]) == 1 and seen(org.nk) == {"quy-trinh-mua"}   # nháp chưa thu hồi
    _confirm(db, admin, out)
    assert seen(org.nk) == set()
    row = db.query(AssistantChange).filter_by(entity="ai_skill_access", action=int(ChangeAction.DELETE)).one()
    change_service.undo(db, admin, row.id)
    assert seen(org.nk) == {"quy-trinh-mua"}


def test_deny_by_employee_wins_and_undo_of_grant_revokes_only_created_rows(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    out, _ = _call(db, admin, "draft_skill_access", {"skill_set": skill_set.code, "effect": "deny",
                                                     "subjects": [{"kind": "employee", "ref": "E621A"}]})
    assert "THẮNG" in out["preview"]["lưu ý"]
    _confirm(db, admin, out)
    assert access_service.visible_skills(db, org.boss) == [] and access_service.visible_skills(db, org.nk)
    row = db.query(AssistantChange).filter_by(entity="ai_skill_access", action=int(ChangeAction.CREATE)).one()
    change_service.undo(db, admin, row.id)
    live = db.query(AiSkillAccess).filter(AiSkillAccess.revoked_at.is_(None)).all()
    assert [(r.subject_kind, r.subject_id) for r in live] == [(SUBJECT_DEPARTMENT, org.root.id)]


def test_ambiguous_or_unknown_subject_lists_candidates_without_guessing(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin)
    out, _ = _call(db, admin, "draft_skill_access", {"skill_set": skill_set.code,
                                                     "subjects": [{"kind": "department", "ref": "thu mua"}]})
    assert out["preview"]["đối tượng"] == [f"{org.root.name} ({org.root.code})"]   # tên ĐÚNG thắng tên chứa chữ
    out, _ = _call(db, admin, "draft_skill_access", {"skill_set": skill_set.code,
                                                     "subjects": [{"kind": "employee", "ref": "E621"}]})
    assert "khớp nhiều" in out["error"]
    out, _ = _call(db, admin, "draft_skill_access", {"skill_set": skill_set.code,
                                                     "subjects": [{"kind": "robot", "ref": "x"}]})
    assert "không có" in out["error"]


# ── Phạm vi phòng ban ───────────────────────────────────────────────────────────────

def test_department_editor_cannot_reach_other_department_set(org, admin, cap_quyen):
    db = org.db
    cap_quyen(org.kt.id, "ai_skill", scope="dept", read=True, write=True)
    theirs = service.create_set(db, SkillSetIn(name="Bộ Thu mua", company_id=org.company.id, owner_department_id=org.root.id), admin)
    mine = service.create_set(db, SkillSetIn(name="Bộ Kế toán", company_id=org.company.id, owner_department_id=org.other.id), admin)
    out, _ = _call(db, org.kt, "draft_skill", {"skill_set": theirs.code, "name": "lach-pham-vi", "body_md": "x"})
    listed = out["error"].split("được quản lý:")[1]                       # chỉ gợi ý bộ của mình
    assert "Không thấy bộ" in out["error"] and mine.code in listed and theirs.code not in listed
    out, _ = _call(db, org.kt, "draft_skill", {"skill_set": mine.code, "name": "quy-trinh-kt", "body_md": "x"})
    service.update_set(db, mine.id, SkillSetPatch(owner_department_id=org.root.id), admin)     # mất phạm vi giữa chừng
    done, trace = _confirm(db, org.kt, out)
    assert done.get("denied") and _skill(db, "quy-trinh-kt") is None and trace["status"] == 2


# ── Khóa AI của nhân sự ─────────────────────────────────────────────────────────────

def _person(db, code, company_id, dept_id):
    emp = Employee(code=code, full_name=f"Người {code}", company_id=company_id, department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email=f"{code.lower()}@k9.vn", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def keys(db, seed, cap_quyen):
    from app.modules.department.model import Department

    other = Department(code="DEPT-K9", name="Phòng K9 khác", company_id=seed.company_id, is_active=True)
    db.add(other)
    db.commit()
    boss = _person(db, "QLK9", seed.company_id, seed.dept_id)
    cap_quyen(boss.id, "ai_mcp_key_admin", scope="dept", read=True, create=True, delete=True)
    mate = _person(db, "BANK9", seed.company_id, seed.dept_id)
    outsider = _person(db, "NGOAIK9", seed.company_id, other.id)
    return SimpleNamespace(db=db, boss=boss, mate=mate, outsider=outsider)


def test_key_issue_draft_writes_nothing_confirm_issues_once(keys):
    db = keys.db
    assert KEY_TOOLS <= _names(db, keys.boss)
    out, _ = _call(db, keys.boss, "draft_key_issue", {"employees": ["BANK9"], "days": 30})
    assert out["preview"]["người nhận"] == ["Người BANK9 (BANK9)"] and db.query(AgentMcpKey).count() == 0
    done, _ = _confirm(db, keys.boss, out)
    row = db.query(AgentMcpKey).one()
    assert done["ok"] and (row.user_id, row.scope, row.issued_by) == (keys.mate.id, mcp_keys.SCOPE_READ, keys.boss.id)
    assert mcp_keys.state_of(row) == mcp_keys.KeyState.PENDING
    assert db.query(Notification).filter_by(user_id=keys.mate.id).count() == 1
    again, _ = _confirm(db, keys.boss, out)                                # bản nháp đã dùng → không phát lần hai
    assert "đã đổi sau lúc soạn" in again["error"] and db.query(AgentMcpKey).count() == 1


def test_key_issue_outside_scope_or_bad_days_is_refused(keys):
    db = keys.db
    out, _ = _call(db, keys.boss, "draft_key_issue", {"employees": ["NGOAIK9"]})
    assert "ngoài phạm vi" in out["error"]
    out, _ = _call(db, keys.boss, "draft_key_issue", {"employees": ["BANK9"], "days": 3})
    assert "Hạn khóa" in out["error"]
    out, _ = _call(db, keys.boss, "draft_key_issue", {})
    assert "Cần `employees`" in out["error"]
    assert db.query(AgentMcpKey).count() == 0


def test_key_revoke_needs_confirm_and_cannot_touch_outsider(keys):
    db = keys.db
    mine = mcp_keys.issue(db, keys.mate.id, keys.boss.id, days=30)
    theirs = mcp_keys.issue(db, keys.outsider.id, keys.outsider.id, days=30)
    db.commit()
    out, _ = _call(db, keys.boss, "draft_key_revoke", {"key_ids": [theirs.id]})
    assert "ngoài phạm vi" in out["error"]
    out, _ = _call(db, keys.boss, "draft_key_revoke", {"employees": ["BANK9"]})
    assert len(out["preview"]["khóa"]) == 1 and db.get(AgentMcpKey, mine.id).revoked_at is None   # nháp chưa thu hồi
    done, _ = _confirm(db, keys.boss, out)
    assert done["ok"] and db.get(AgentMcpKey, mine.id).revoked_at is not None
    again, _ = _confirm(db, keys.boss, out)
    assert "đã bị thu hồi" in again["error"]


def test_key_tools_refused_for_read_only_key_even_in_confirm(keys):
    db = keys.db
    out, _ = _call(db, keys.boss, "draft_key_issue", {"employees": ["BANK9"]})
    done, _ = _confirm(db, keys.boss, out, scope=mcp_keys.SCOPE_READ)
    assert done["denied"] and db.query(AgentMcpKey).count() == 0
