"""bao-CR-622 — Kho skill qua cổng MCP (K2 của doc/erp/21 §5.1).

Cố làm nó SAI: đọc skill không được giao, đoán tên skill phòng khác, đọc tệp của bộ Bảo vệ / Khóa, đọc bản nháp chưa
xuất bản, trùng tên skill giữa hai bộ, gọi thiếu tham số. Và kiểm cổng: khóa chỉ đọc thấy 3 tool, nhật ký ghi skill_id.
"""
import json

from app.core.subject_match import SUBJECT_DEPARTMENT, SUBJECT_EMPLOYEE
from app.modules.agent_hub import mcp, mcp_keys
from app.modules.ai_skill import mcp_read, service
from app.modules.ai_skill.constants import AccessTarget, SecurityLevel
from app.modules.ai_skill.schema import SkillIn, SkillPatch

from test_ai_skill_kho_k1 import admin, give, make_skill, org  # noqa: F401 — dùng chung thế giới mẫu của K1


def test_list_shows_only_granted_skills_with_summary(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    out = mcp_read.list_for_ai(db, org.boss)
    assert out["total"] == 1 and out["items"][0]["name"] == "quy-trinh-mua"
    assert out["items"][0]["summary"] == "Khi lập YCMH"
    empty = mcp_read.list_for_ai(db, org.kt)
    assert empty["total"] == 0 and "chưa được giao" in empty["note"]
    assert mcp_read.list_for_ai(db, org.boss, query="không-khớp")["total"] == 0


def test_read_returns_published_version_not_draft(org, admin):
    db = org.db
    skill_set, skill = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    service.update_skill(db, skill.id, SkillPatch(body_md="BẢN NHÁP CHƯA DUYỆT"), admin)
    out = mcp_read.read_for_ai(db, org.boss, "quy-trinh-mua")
    assert out["content"].startswith("# Bước 1") and "NHÁP" not in out["content"]
    assert out["version"] == 1 and out["skill_id"] == skill.id


def test_not_granted_and_nonexistent_skill_answer_the_same(org, admin):
    """Người ngoài không được dò ra skill phòng khác có tồn tại hay không."""
    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    hidden = mcp_read.read_for_ai(db, org.kt, "quy-trinh-mua")
    missing = mcp_read.read_for_ai(db, org.kt, "khong-ton-tai")
    assert hidden["denied"] and missing["denied"]
    assert hidden["error"].replace("quy-trinh-mua", "X") == missing["error"].replace("khong-ton-tai", "X")
    assert "skill_id" not in hidden


def test_security_levels_control_content_and_files(org, admin):
    db = org.db
    for level, slug in ((SecurityLevel.OPEN, "mo"), (SecurityLevel.PROTECTED, "bao-ve"), (SecurityLevel.LOCKED, "khoa")):
        skill_set, skill = make_skill(db, admin, set_name=f"Bộ {slug}", slug=slug, security_level=int(level))
        service.put_file(db, skill.id, "references/a.md", "nội dung tệp", admin)
        give(db, admin, skill_set.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)])
    opened = mcp_read.read_for_ai(db, org.boss, "mo")
    assert opened["content"] and [f["path"] for f in opened["files"]] == ["references/a.md"]
    assert mcp_read.file_for_ai(db, org.boss, "mo", "references/a.md")["content"] == "nội dung tệp"
    protected = mcp_read.read_for_ai(db, org.boss, "bao-ve")
    assert protected["content"] and protected["files"] == []
    assert mcp_read.file_for_ai(db, org.boss, "bao-ve", "references/a.md")["denied"]
    locked = mcp_read.read_for_ai(db, org.boss, "khoa")
    assert "content" not in locked and "files" not in locked and "Khóa" in locked["note"]
    assert mcp_read.file_for_ai(db, org.boss, "khoa", "references/a.md")["denied"]
    listed = {i["name"]: i for i in mcp_read.list_for_ai(db, org.boss)["items"]}
    assert listed["mo"]["files"] == 1 and listed["bao-ve"]["files"] == 0 and not listed["khoa"]["content_readable"]


def test_file_errors_wrong_path_and_traversal(org, admin):
    db = org.db
    skill_set, skill = make_skill(db, admin)
    service.put_file(db, skill.id, "references/a.md", "x", admin)
    give(db, admin, skill_set.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)])
    for path in ("references/b.md", "../references/a.md", "/references/a.md", ""):
        assert "error" in mcp_read.file_for_ai(db, org.boss, "quy-trinh-mua", path)


def test_same_slug_in_two_sets_gets_set_code_prefix(org, admin):
    db = org.db
    set_a, _ = make_skill(db, admin, set_name="Bộ A", slug="huong-dan")
    set_b, _ = make_skill(db, admin, set_name="Bộ B", slug="huong-dan")
    give(db, admin, set_a.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)])
    give(db, admin, set_b.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)])
    names = {i["name"] for i in mcp_read.list_for_ai(db, org.boss)["items"]}
    assert names == {f"{set_a.code}/huong-dan", f"{set_b.code}/huong-dan"}
    assert mcp_read.read_for_ai(db, org.boss, f"{set_b.code}/huong-dan")["skill_set"] == "Bộ B"
    assert mcp_read.read_for_ai(db, org.boss, "huong-dan")["denied"]       # tên mơ hồ → không đoán


def test_skill_narrowed_to_one_person_is_hidden_from_department(org, admin):
    db = org.db
    skill_set, secret = make_skill(db, admin, slug="bang-gia")
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    give(db, admin, secret.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)], target=AccessTarget.SKILL)
    assert mcp_read.read_for_ai(db, org.boss, "bang-gia")["content"]
    assert mcp_read.read_for_ai(db, org.nk, "bang-gia")["denied"]


# --- cổng MCP -------------------------------------------------------------------------------------------------------

class _Key:
    def __init__(self, scope):
        self.scope = scope


def _call(db, user, name, args, scope=mcp_keys.SCOPE_READ):
    trace = {}
    res = mcp.handle(db, user, _Key(scope), {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                            "params": {"name": name, "arguments": args}}, trace)
    return json.loads(res["result"]["content"][0]["text"]), res["result"]["isError"], trace


def test_read_only_key_sees_three_skill_tools_first(org, admin):
    names = [t["name"] for t in mcp.list_tools(org.db, org.boss, mcp_keys.SCOPE_READ)]
    assert names[:3] == ["list_skills", "read_skill", "read_skill_file"]
    assert "list_skills" in mcp.INSTRUCTIONS


def test_mcp_call_logs_skill_id_and_strips_it_from_answer(org, admin):
    db = org.db
    skill_set, skill = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)])
    body, is_error, trace = _call(db, org.boss, "read_skill", {"name": "quy-trinh-mua"})
    assert not is_error and "skill_id" not in body and trace["skill_id"] == skill.id
    body, is_error, trace = _call(db, org.kt, "read_skill", {"name": "quy-trinh-mua"})
    assert body["denied"] and trace["status"] == 2 and "skill_id" not in trace     # DENIED, không lộ id
    body, is_error, trace = _call(db, org.boss, "read_skill", {})
    assert is_error and "Thiếu" in body["error"]
    body, _, _ = _call(db, org.boss, "read_skill_file", {"name": "quy-trinh-mua"})
    assert "Thiếu `path`" in body["error"]
