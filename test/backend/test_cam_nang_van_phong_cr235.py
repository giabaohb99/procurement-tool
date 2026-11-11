"""ai-CR-235 — bốn cẩm nang văn phòng (đặt xe, duyệt dấu, diễn đàn, kho) trong bộ SYS-HANDBOOK.

Canh: cẩm nang chỉ được nhắc công cụ CÓ THẬT (đổi tên công cụ mà quên sửa cẩm nang thì trợ lý gọi công cụ ma), không
emoji, không ngoặc kép góc.
"""
import re

import pytest

from app.modules.ai_skill import handbook_seed
from app.modules.assistant.tools import _active_specs

OFFICE_SLUGS = [s for _f, s, _sum in handbook_seed.SKILLS if s in ("dat-xe", "duyet-dau", "dien-dan", "kho")]
#  Chữ trong `...` trông như tên công cụ: draft_* / confirm_* / *_read.
TOOL_LIKE = re.compile(r"`((?:draft|confirm)_[a-z_]+|[a-z_]+_read)`")
MCP_ONLY = {"confirm_draft"}   # chỉ cổng MCP có, sổ Trợ lý không có
FORBIDDEN = re.compile("[«»☀-➿\U0001f300-\U0001faff]")


def _bodies() -> dict[str, str]:
    return {slug: body for slug, _t, _s, body in handbook_seed.seed_files() if slug in OFFICE_SLUGS}


def test_cam_nang_van_phong_co_trong_bo_hat_giong():
    assert OFFICE_SLUGS, "chưa khai cẩm nang văn phòng nào trong SKILLS"


@pytest.mark.parametrize("slug", OFFICE_SLUGS)
def test_chi_nhac_cong_cu_co_that(slug):
    real = {s.name for s in _active_specs()} | MCP_ONLY
    named = set(TOOL_LIKE.findall(_bodies()[slug]))
    assert named, f"{slug}: cẩm nang không nhắc công cụ nào"
    assert named <= real, f"{slug}: nhắc công cụ không có thật {sorted(named - real)}"


@pytest.mark.parametrize("slug", OFFICE_SLUGS)
def test_khong_emoji_khong_ngoac_goc(slug):
    assert not FORBIDDEN.search(_bodies()[slug])


# ── scripts/publish_handbook_update.py: chỉ THÊM skill chưa có, cấm đè / xóa ────────────────────────────────────────

def _load_publish_script():
    import importlib.util
    from pathlib import Path

    backend = Path(__file__).resolve().parents[2] / "backend"
    if not (backend / "scripts").exists():  # chạy trong container: backend mount ở /app
        backend = Path("/app")
    spec = importlib.util.spec_from_file_location("publish_handbook_cr235", backend / "scripts" / "publish_handbook_update.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def handbook_old(db, seed):
    """Hệ đã gieo TRƯỚC ai-CR-235: bộ có đủ skill cũ, chưa có bốn cẩm nang văn phòng."""
    from app.modules.ai_skill.model import AiSkill, AiSkillSet

    handbook_seed.ensure_system_handbook(db)
    skill_set = db.query(AiSkillSet).filter(AiSkillSet.code == handbook_seed.SET_CODE).one()
    for skill in db.query(AiSkill).filter(AiSkill.skill_set_id == skill_set.id, AiSkill.slug.in_(OFFICE_SLUGS)):
        db.delete(skill)
    db.commit()
    return skill_set


def test_chua_co_thi_tao_skill_moi_da_xuat_ban(db, handbook_old):
    from app.modules.ai_skill.model import AiSkill, AiSkillVersion

    script = _load_publish_script()
    for order, (slug, title, summary, body) in enumerate(handbook_seed.seed_files(), start=1):
        if slug not in OFFICE_SLUGS:
            continue
        skill = script.add_missing_skill(db, handbook_old, slug, title, summary, body, order, "ai-CR-235")
        assert skill is not None and skill.current_version_id
        version = db.get(AiSkillVersion, skill.current_version_id)
        assert (version.version_no, version.body_md, version.published_by) == (1, body, 0)
    slugs = {s for (s,) in db.query(AiSkill.slug).filter(AiSkill.skill_set_id == handbook_old.id)}
    assert slugs == {s for _f, s, _sum in handbook_seed.SKILLS}


def test_da_co_thi_bo_qua_khong_de_khong_xoa(db, handbook_old):
    from app.modules.ai_skill.model import AiSkill, AiSkillVersion

    script = _load_publish_script()
    slug, title, summary, body = next(f for f in handbook_seed.seed_files() if f[0] == "nghi-phep")
    skill = db.query(AiSkill).filter(AiSkill.skill_set_id == handbook_old.id, AiSkill.slug == slug).one()
    db.get(AiSkillVersion, skill.current_version_id).body_md = "Bản quản trị đã sửa"
    #  Skill đã xóa mềm vẫn tính là "đã có": không được hồi sinh.
    office = OFFICE_SLUGS[0]
    o_title, o_summary, o_body = next(f[1:] for f in handbook_seed.seed_files() if f[0] == office)
    deleted = script.add_missing_skill(db, handbook_old, office, o_title, o_summary, o_body, 1, "lần 1")
    deleted.is_deleted = True
    db.commit()
    before = db.query(AiSkill).filter(AiSkill.skill_set_id == handbook_old.id).count()

    assert script.add_missing_skill(db, handbook_old, slug, title, summary, body, 1, "ai-CR-235") is None
    assert script.add_missing_skill(db, handbook_old, office, o_title, o_summary, o_body, 1, "lần 2") is None
    assert db.query(AiSkill).filter(AiSkill.skill_set_id == handbook_old.id).count() == before
    assert db.get(AiSkillVersion, skill.current_version_id).body_md == "Bản quản trị đã sửa"
    assert db.query(AiSkillVersion).filter(AiSkillVersion.skill_id == deleted.id).count() == 1
