"""ai-CR-220 — K7 doc/erp/21 §7.2: Trợ lý web + bot core_v2 đọc cẩm nang từ KHO SKILL thay 7 gói `assistant/packs`.

Canh (chỗ dễ lủng):
  - hạt giống «Cẩm nang hệ thống» gieo đủ (7 skill xuất bản, 11 tệp gốc nhà máy, mỗi pháp nhân một dòng cho phép) và
    CHẠY LẠI KHÔNG ĐÈ: quản trị sửa / lưu trữ / xóa mềm bộ thì seed không gieo lại, không sửa nội dung;
  - trợ lý nội bộ đọc được bộ mức Khóa (nội dung + tệp), cổng MCP thì KHÔNG (bản riêng của cổng giữ nguyên gác);
  - cổng MCP không liệt kê trùng `list_skills` (sổ tool Trợ lý nay cũng có ba tool cùng tên);
  - danh mục trong lời nhắc có trần 1,5k ký tự, cắt tóm tắt dài, báo số còn lại; không có skill thì không chèn gì;
  - lời nhắc core_v2: danh mục là khối CUỐI (phần tĩnh phía trước giữ nguyên để trúng bộ đệm trạm);
  - ba tool skill nằm ở nhóm LÕI của bộ lọc công cụ (đọc được ở mọi câu, kể cả câu chào).
"""
from types import SimpleNamespace

import pytest

from app.modules.ai_skill import handbook_seed, mcp_read
from app.modules.ai_skill.constants import SecurityLevel, SkillSetStatus
from app.modules.ai_skill.model import AiSkill, AiSkillAccess, AiSkillFile, AiSkillSet, AiSkillVersion
from app.modules.assistant import knowledge, tool_router
from app.modules.company.model import Company
from app.modules.user.model import User


@pytest.fixture
def user(db, seed):
    return db.get(User, seed.u_req_id)


@pytest.fixture
def handbook(db, seed):
    assert handbook_seed.ensure_system_handbook(db) == len(handbook_seed.SKILLS)
    return db.query(AiSkillSet).filter(AiSkillSet.code == handbook_seed.SET_CODE).one()


# ── Hạt giống ─────────────────────────────────────────────────────────────────

def test_gieo_du_bo_cam_nang_cho_moi_phap_nhan(db, handbook):
    assert (handbook.status, handbook.security_level) == (int(SkillSetStatus.ACTIVE), int(SecurityLevel.OPEN))
    skills = db.query(AiSkill).filter(AiSkill.skill_set_id == handbook.id).all()
    assert len(skills) == 7 and all(s.current_version_id for s in skills)
    for s in skills:
        v = db.get(AiSkillVersion, s.current_version_id)
        assert v.version_no == 1 and v.body_md.strip() and 0 < len(v.summary) <= 500
    factory = next(s for s in skills if s.slug == handbook_seed.FACTORY_SLUG)
    files = db.query(AiSkillFile).filter(AiSkillFile.skill_id == factory.id).all()
    assert len(files) == 11 and all(f.path.startswith("references/nhamay-") and f.sha256 for f in files)
    companies = {c for (c,) in db.query(Company.id)}
    grants = {a.subject_id for a in db.query(AiSkillAccess).filter(AiSkillAccess.target_id == handbook.id)}
    assert grants == companies and companies


def test_chay_lai_khong_de_noi_dung_quan_tri_da_sua(db, handbook):
    skill = db.query(AiSkill).filter(AiSkill.skill_set_id == handbook.id, AiSkill.slug == "nghi-phep").one()
    version = db.get(AiSkillVersion, skill.current_version_id)
    version.body_md = "Bản quản trị đã sửa"
    handbook.status = int(SkillSetStatus.ARCHIVED)
    db.commit()
    assert handbook_seed.ensure_system_handbook(db) == 0
    assert db.get(AiSkillVersion, skill.current_version_id).body_md == "Bản quản trị đã sửa"
    assert db.query(AiSkillSet).filter(AiSkillSet.code == handbook_seed.SET_CODE).count() == 1
    #  Xóa mềm cả bộ: seed cũng KHÔNG gieo lại (quản trị chủ ý bỏ).
    handbook.is_deleted = True
    db.commit()
    assert handbook_seed.ensure_system_handbook(db) == 0


def test_ten_goi_hat_giong_khong_trung_va_dung_khuon_slug():
    slugs = [slug for _f, slug, _s in handbook_seed.SKILLS]
    assert len(slugs) == len(set(slugs))
    assert all(slug == slug.lower() and " " not in slug and len(slug) <= 100 for slug in slugs)


# ── Đọc: nội bộ vs cổng MCP ──────────────────────────────────────────────────

def test_tro_ly_noi_bo_doc_duoc_bo_khoa_cong_mcp_thi_khong(db, user, handbook):
    from app.modules.assistant.tools import run_tool

    handbook.security_level = int(SecurityLevel.LOCKED)
    db.commit()
    inner = run_tool(db, user, "read_skill", {"name": handbook_seed.FACTORY_SLUG})
    assert "DEGO Organic" in inner.get("content", "") and len(inner["files"]) == 11
    one = run_tool(db, user, "read_skill_file", {"name": handbook_seed.FACTORY_SLUG,
                                                 "path": inner["files"][0]["path"]})
    assert one.get("content")
    outer = mcp_read.read_for_ai(db, user, handbook_seed.FACTORY_SLUG)
    assert "content" not in outer and "mức Khóa" in outer["note"]
    assert mcp_read.file_for_ai(db, user, handbook_seed.FACTORY_SLUG, inner["files"][0]["path"]).get("denied")
    listed = run_tool(db, user, "list_skills", {})
    assert listed["total"] == 7 and all(i["content_readable"] for i in listed["items"])


def test_nguoi_khong_duoc_gan_khong_doc_duoc(db, seed, handbook):
    from app.modules.assistant.tools import run_tool

    db.query(AiSkillAccess).filter(AiSkillAccess.target_id == handbook.id).delete()
    db.commit()
    out = run_tool(db, db.get(User, seed.u_req_id), "read_skill", {"name": "nghi-phep"})
    assert out.get("denied") and "content" not in out
    assert knowledge.handbook_block(db, db.get(User, seed.u_req_id)) == ""


def test_cong_mcp_khong_liet_ke_trung_ba_tool_skill(db, user, handbook):
    from app.modules.agent_hub import mcp, mcp_keys

    names = [t["name"] for t in mcp.list_tools(db, user, mcp_keys.SCOPE_READ)]
    for n in ("list_skills", "read_skill", "read_skill_file"):
        assert names.count(n) == 1, n


# ── Danh mục trong lời nhắc ──────────────────────────────────────────────────

def test_danh_muc_co_tran_cat_tom_tat_va_bao_so_con_lai():
    assert knowledge.handbook_text([]) == ""
    items = [{"name": f"skill-{i}", "summary": "x" * 400} for i in range(40)]
    text = knowledge.handbook_text(items, total=40)
    assert len(text) <= knowledge.HANDBOOK_MAX_CHARS
    assert text.startswith(knowledge.HANDBOOK_HEAD) and "x" * (knowledge.SUMMARY_MAX_CHARS + 1) not in text
    shown = text.count("\n- ")
    assert 0 < shown < 40 and f"còn {40 - shown} cẩm nang" in text
    #  Tóm tắt có xuống dòng / khoảng trắng thừa không làm vỡ một-dòng-một-skill.
    one = knowledge.handbook_text([{"name": "a", "summary": "dòng 1\n\n  dòng 2"}])
    assert one.splitlines()[1] == "- a: dòng 1 dòng 2"


def test_danh_muc_that_cua_nguoi_hoi(db, user, handbook):
    text = knowledge.handbook_block(db, user)
    assert "- nghi-phep:" in text and "- quy-trinh-thu-mua:" in text and len(text) <= knowledge.HANDBOOK_MAX_CHARS


def test_dinh_nghia_khong_con_goi_tri_thuc():
    system = knowledge.build_system()
    assert "GÓI TRI THỨC" not in system and "read_skill" in system
    assert not hasattr(knowledge, "load_pack") and not hasattr(tool_router, "pack_topics")


def test_tro_ly_web_xep_danh_muc_sau_loi_dan_kenh_truoc_thuat_ngu():
    from app.modules.assistant.service import _extra_system

    out = _extra_system(True, "LOI_DAN_KENH", "CHAN_DUNG", "THUAT_NGU", handbook="DANH_MUC")
    assert out.index("CHAN_DUNG") < out.index("LOI_DAN_KENH") < out.index("DANH_MUC") < out.index("THUAT_NGU")


def test_core_v2_danh_muc_la_khoi_cuoi_cua_phan_tinh(db, user, handbook, monkeypatch):
    from app.modules.agent_hub import core_v2

    row = SimpleNamespace(id=0, created_at=None)
    system = core_v2.build_system(db, "chat-x", row, user, "quy trình nghỉ phép thế nào")
    assert system.rstrip().endswith(knowledge.handbook_block(db, user).rstrip())
    assert "- nghi-phep:" in system
    #  Đổi danh mục chỉ đổi phần ĐUÔI — phần tĩnh phía trước giữ nguyên.
    monkeypatch.setattr(knowledge, "handbook_block", lambda _db, _u: "")
    bare = core_v2.build_system(db, "chat-x", row, user, "câu khác")
    assert system.startswith(bare)


def test_ba_tool_skill_o_nhom_loi_ke_ca_cau_chao():
    assert {"list_skills", "read_skill", "read_skill_file"} <= tool_router.CORE
    assert {"read_skill"} <= set(tool_router.CORE)
