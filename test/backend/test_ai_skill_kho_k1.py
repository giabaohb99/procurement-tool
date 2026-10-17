"""bao-CR-621 — Kho skill AI, đợt K1 (doc/erp/21 §4).

Kiểm luật ĐỌC (`access_service.visible_skills`): kế thừa phòng con, cấm thắng, thu hẹp theo skill, nháp không lộ,
chức vụ / cấp bậc, hết hạn / thu hồi. Kiểm luật QUẢN TRỊ: phạm vi `dept` của biên tập phòng, xuất bản tạo phiên bản
chỉ thêm, nhập gói .zip + thay gói. Viết theo hướng cố làm nó SAI (testing.md): người ngoài phòng, phòng anh em, hạn
qua, slug bẩn, đường dẫn tệp leo thư mục.
"""
import io
import zipfile
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.subject_match import EFFECT_ALLOW, EFFECT_DENY, SUBJECT_DEPARTMENT, SUBJECT_EMPLOYEE
from app.modules.ai_skill import access_service, service
from app.modules.ai_skill.constants import (SUBJECT_JOB_LEVEL, SUBJECT_POSITION, AccessTarget, SkillSetStatus,
                                            SkillStatus)
from app.modules.ai_skill.model import AiSkill, AiSkillAccess, AiSkillFile, AiSkillVersion
from app.modules.ai_skill.schema import AccessGrantIn, SkillIn, SkillPatch, SkillSetIn


# ---------------------------------------------------------------------------
# Thế giới nhỏ: công ty, cây phòng (Thu mua → Thu mua NK), phòng anh em (Kế toán), 4 người
# ---------------------------------------------------------------------------

@pytest.fixture()
def org(db):
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.employee.model import Employee
    from app.modules.employee.position_model import JobPosition
    from app.modules.user.model import User

    company = Company(code="C621", name="Công ty 621")
    db.add(company)
    db.flush()
    root = Department(code="D621TM", name="Thu mua", company_id=company.id, is_active=True)
    other = Department(code="D621KT", name="Kế toán", company_id=company.id, is_active=True)
    db.add_all([root, other])
    db.flush()
    child = Department(code="D621NK", name="Thu mua NK", company_id=company.id, parent=root.id, is_active=True)
    db.add(child)
    position = JobPosition(code="CV621", name="Chuyên viên thu mua")
    db.add(position)
    db.flush()

    def person(code, dept, job_level=0, position_id=0):
        emp = Employee(code=code, full_name=code, company_id=company.id, department_id=dept.id,
                       job_level=job_level, position_id=position_id)
        db.add(emp)
        db.flush()
        user = User(email=f"{code}@t.vn", employee_id=emp.id, password_hash="x", is_active=True)
        db.add(user)
        db.flush()
        return user

    return SimpleNamespace(
        db=db, company=company, root=root, child=child, other=other, position=position,
        boss=person("E621A", root), nk=person("E621B", child), kt=person("E621C", other),
        cv=person("E621D", other, job_level=1, position_id=position.id))


@pytest.fixture()
def admin(org, cap_quyen):
    from app.modules.user.model import User

    user = User(email="admin621@t.vn", employee_id=0, password_hash="x", is_active=True)
    org.db.add(user)
    org.db.flush()
    cap_quyen(user.id, "ai_skill", scope="all", read=True, create=True, write=True, delete=True, approve=True)
    return user


def make_skill(db, admin, set_name="Thu mua", slug="quy-trinh-mua", publish=True, set_active=True, **set_kw):
    skill_set = service.create_set(db, SkillSetIn(name=set_name, status=int(
        SkillSetStatus.ACTIVE if set_active else SkillSetStatus.DRAFT), **set_kw), admin)
    skill = service.create_skill(db, skill_set.id, SkillIn(slug=slug, title="Quy trình mua", summary="Khi lập YCMH",
                                                           body_md="# Bước 1\nLập phiếu"), admin)
    if publish:
        service.publish_skill(db, skill.id, "bản đầu", admin)
    return skill_set, skill


def give(db, admin, target_id, subjects, *, target=AccessTarget.SKILL_SET, effect=EFFECT_ALLOW, children=True,
         valid_to=None):
    access_service.grant(db, AccessGrantIn(target_kind=int(target), target_id=target_id,
                                           subjects=[{"subject_kind": k, "subject_id": i} for k, i in subjects],
                                           effect=effect, include_children=children, valid_to=valid_to), admin)


def slugs(db, user):
    return {row["slug"] for row in access_service.visible_skills(db, user)}


# ---------------------------------------------------------------------------
# Luật ĐỌC
# ---------------------------------------------------------------------------

def test_department_grant_reaches_child_department_but_not_sibling(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    assert slugs(db, org.boss) == {"quy-trinh-mua"}
    assert slugs(db, org.nk) == {"quy-trinh-mua"}      # phòng con kế thừa
    assert slugs(db, org.kt) == set()                  # phòng anh em không


def test_department_grant_without_children_stays_in_that_department(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)], children=False)
    assert slugs(db, org.boss) == {"quy-trinh-mua"}
    assert slugs(db, org.nk) == set()


def test_deny_on_set_wins_over_allow_from_department(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    give(db, admin, skill_set.id, [(SUBJECT_EMPLOYEE, org.nk.employee_id)], effect=EFFECT_DENY)
    assert slugs(db, org.nk) == set()
    assert slugs(db, org.boss) == {"quy-trinh-mua"}


def test_deny_on_set_also_blocks_skill_level_allow(org, admin):
    db = org.db
    skill_set, skill = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_EMPLOYEE, org.kt.employee_id)], effect=EFFECT_DENY)
    give(db, admin, skill.id, [(SUBJECT_EMPLOYEE, org.kt.employee_id)], target=AccessTarget.SKILL)
    assert slugs(db, org.kt) == set()


def test_skill_with_own_rows_narrows_set_audience(org, admin):
    """Skill có dòng quyền RIÊNG thì quyền bộ không còn đủ — chỉ người khớp dòng riêng đọc."""
    db = org.db
    skill_set, secret = make_skill(db, admin, slug="bang-gia-mat")
    open_skill = service.create_skill(db, skill_set.id, SkillIn(slug="huong-dan-chung", summary="chung",
                                                                body_md="x"), admin)
    service.publish_skill(db, open_skill.id, "", admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    give(db, admin, secret.id, [(SUBJECT_EMPLOYEE, org.boss.employee_id)], target=AccessTarget.SKILL)
    assert slugs(db, org.boss) == {"bang-gia-mat", "huong-dan-chung"}
    assert slugs(db, org.nk) == {"huong-dan-chung"}


def test_skill_level_allow_opens_skill_even_without_set_grant(org, admin):
    db = org.db
    _, skill = make_skill(db, admin)
    give(db, admin, skill.id, [(SUBJECT_EMPLOYEE, org.kt.employee_id)], target=AccessTarget.SKILL)
    assert slugs(db, org.kt) == {"quy-trinh-mua"}
    assert slugs(db, org.boss) == set()


def test_draft_skill_and_draft_set_never_visible(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin, publish=False)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    assert slugs(db, org.boss) == set()                 # skill chưa xuất bản
    draft_set, _ = make_skill(db, admin, set_name="Nháp", slug="nhap", set_active=False)
    give(db, admin, draft_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    assert slugs(db, org.boss) == set()                 # bộ còn nháp


def test_archived_and_deleted_skill_disappear(org, admin):
    db = org.db
    skill_set, skill = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    service.update_skill(db, skill.id, SkillPatch(status=int(SkillStatus.ARCHIVED)), admin)
    assert slugs(db, org.boss) == set()
    service.update_skill(db, skill.id, SkillPatch(status=int(SkillStatus.ACTIVE)), admin)
    assert slugs(db, org.boss) == {"quy-trinh-mua"}
    service.delete_skill(db, skill.id, admin)
    assert slugs(db, org.boss) == set()


def test_position_and_job_level_subjects_match(org, admin):
    db = org.db
    set_a, _ = make_skill(db, admin, set_name="Theo chức vụ", slug="theo-chuc-vu")
    set_b, _ = make_skill(db, admin, set_name="Theo cấp bậc", slug="theo-cap-bac")
    give(db, admin, set_a.id, [(SUBJECT_POSITION, org.position.id)])
    give(db, admin, set_b.id, [(SUBJECT_JOB_LEVEL, 1)])
    assert slugs(db, org.cv) == {"theo-chuc-vu", "theo-cap-bac"}
    assert slugs(db, org.kt) == set()


def test_revoked_or_expired_grant_stops_working(org, admin):
    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_EMPLOYEE, org.kt.employee_id)])
    assert slugs(db, org.kt) == {"quy-trinh-mua"}
    row = db.query(AiSkillAccess).filter(AiSkillAccess.subject_id == org.kt.employee_id).one()
    row.valid_to = date.today() - timedelta(days=1)
    db.commit()
    assert slugs(db, org.kt) == set()
    row.valid_to = None
    db.commit()
    access_service.revoke(db, row.id, "thôi", admin)
    assert slugs(db, org.kt) == set()


def test_moving_department_changes_skills_without_new_key(org, admin):
    db = org.db
    from app.core.auth import perm_cache_clear
    from app.modules.employee.model import Employee

    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    assert slugs(db, org.kt) == set()
    db.get(Employee, org.kt.employee_id).department_id = org.child.id
    db.commit()
    perm_cache_clear(org.kt.id)
    assert slugs(db, org.kt) == {"quy-trinh-mua"}


def test_user_without_employee_profile_sees_nothing(org, admin):
    from app.modules.user.model import User

    db = org.db
    skill_set, _ = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    ghost = User(email="ghost621@t.vn", employee_id=0, password_hash="x", is_active=True)
    db.add(ghost)
    db.flush()
    assert access_service.visible_skills(db, ghost) == []


def test_grant_skips_unknown_subjects_and_rejects_deny_on_admin_role(org, admin):
    db = org.db
    from app.modules.role.model import Role

    skill_set, _ = make_skill(db, admin)
    result = access_service.grant(db, AccessGrantIn(target_kind=1, target_id=skill_set.id, subjects=[
        {"subject_kind": SUBJECT_EMPLOYEE, "subject_id": 999_999},
        {"subject_kind": SUBJECT_JOB_LEVEL, "subject_id": 99}]), admin)
    assert result == {"created": 0, "updated": 0, "skipped": 2}
    role = Role(code="admin", name="Quản trị")
    db.add(role)
    db.flush()
    with pytest.raises(HTTPException) as exc:
        access_service.grant(db, AccessGrantIn(target_kind=1, target_id=skill_set.id, effect=EFFECT_DENY,
                                               subjects=[{"subject_kind": 4, "subject_id": role.id}]), admin)
    assert exc.value.status_code == 400


def test_grant_schema_rejects_bad_kind_past_expiry_and_zero_id():
    with pytest.raises(ValueError):
        AccessGrantIn(target_kind=1, target_id=1, subjects=[{"subject_kind": 9, "subject_id": 1}])
    with pytest.raises(ValueError):
        AccessGrantIn(target_kind=1, target_id=1, subjects=[{"subject_kind": 1, "subject_id": 0}])
    with pytest.raises(ValueError):
        AccessGrantIn(target_kind=1, target_id=1, subjects=[{"subject_kind": 1, "subject_id": 1}],
                      valid_to=date.today() - timedelta(days=1))
    with pytest.raises(ValueError):
        AccessGrantIn(target_kind=7, target_id=1, subjects=[{"subject_kind": 1, "subject_id": 1}])


# ---------------------------------------------------------------------------
# Luật QUẢN TRỊ
# ---------------------------------------------------------------------------

def test_department_editor_manages_only_own_department_sets(org, admin, cap_quyen):
    db = org.db
    cap_quyen(org.boss.id, "ai_skill", scope="dept", read=True, create=True, write=True, approve=True)
    mine = service.create_set(db, SkillSetIn(name="Bộ của Thu mua", owner_department_id=org.root.id), org.boss)
    assert {row["id"] for row in service.list_sets(db, org.boss)} == {mine.id}
    other = service.create_set(db, SkillSetIn(name="Bộ của Kế toán", owner_department_id=org.other.id), admin)
    with pytest.raises(HTTPException) as exc:
        service.get_set(db, other.id, org.boss)
    assert exc.value.status_code == 404
    with pytest.raises(HTTPException) as exc:     # tạo bộ cho phòng khác → ngoài phạm vi, không được lưu
        service.create_set(db, SkillSetIn(name="Lách", owner_department_id=org.other.id), org.boss)
    assert exc.value.status_code == 403
    with pytest.raises(HTTPException):            # đổi phòng chủ quản ra ngoài nhánh
        service.update_set(db, mine.id, SimpleNamespace(model_dump=lambda exclude_unset: {
            "owner_department_id": org.other.id}), org.boss)


def test_publish_appends_versions_and_requires_summary_and_body(org, admin):
    db = org.db
    skill_set = service.create_set(db, SkillSetIn(name="Bộ"), admin)
    skill = service.create_skill(db, skill_set.id, SkillIn(slug="viet-bao-cao"), admin)
    with pytest.raises(HTTPException):
        service.publish_skill(db, skill.id, "", admin)          # chưa có nội dung
    service.update_skill(db, skill.id, SkillPatch(body_md="Nội dung"), admin)
    with pytest.raises(HTTPException):
        service.publish_skill(db, skill.id, "", admin)          # chưa có tóm tắt
    service.update_skill(db, skill.id, SkillPatch(summary="Khi viết báo cáo tuần"), admin)
    v1 = service.publish_skill(db, skill.id, "v1", admin)
    service.update_skill(db, skill.id, SkillPatch(body_md="Nội dung mới"), admin)
    v2 = service.publish_skill(db, skill.id, "v2", admin)
    assert (v1.version_no, v2.version_no) == (1, 2)
    assert db.get(AiSkillVersion, v1.id).body_md == "Nội dung"         # bản cũ không bị sửa
    assert db.get(AiSkill, skill.id).current_version_id == v2.id


def test_slug_rules_and_uniqueness_within_set(org, admin):
    db = org.db
    for bad in ("báo-cáo", "a", "-abc", "quy trình", "x" * 101, "report.md"):
        with pytest.raises(ValueError):
            SkillIn(slug=bad)
    skill_set = service.create_set(db, SkillSetIn(name="Bộ"), admin)
    service.create_skill(db, skill_set.id, SkillIn(slug="SOP2024"), admin)
    with pytest.raises(HTTPException):
        service.create_skill(db, skill_set.id, SkillIn(slug="SOP2024"), admin)


@pytest.mark.parametrize("path", ["../etc/passwd", "a/../../b.md", ".env", "dir/.git/x.md", "a\\b.md",
                                  "anh.png", "bang.xlsx", "/abs.md", "a/b/c/d/e/f/g.md", "tài-liệu.md"])
def test_file_path_rules_block_traversal_and_binary(path):
    with pytest.raises(HTTPException):
        service.check_file_path(path)


def test_put_file_size_limit_and_overwrite_by_path(org, admin):
    db = org.db
    _, skill = make_skill(db, admin, publish=False)
    service.put_file(db, skill.id, "references/guide.md", "bản 1", admin)
    service.put_file(db, skill.id, "references/guide.md", "bản 2", admin)
    rows = db.query(AiSkillFile).filter(AiSkillFile.skill_id == skill.id).all()
    assert [(r.path, r.content_text) for r in rows] == [("references/guide.md", "bản 2")]
    with pytest.raises(HTTPException):
        service.put_file(db, skill.id, "big.txt", "x" * (2 * 1024 * 1024 + 1), admin)


def _zip(entries: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_import_package_finds_shallowest_skill_md_and_replaces_files(org, admin):
    db = org.db
    skill_set = service.create_set(db, SkillSetIn(name="Bộ"), admin)
    first = _zip({
        "bao-cao-tuan/SKILL.md": "---\nname: bao-cao-tuan\ndescription: Cách viết báo cáo tuần\n---\n# Báo cáo",
        "bao-cao-tuan/references/guide.md": "hướng dẫn",
        "bao-cao-tuan/references/old.md": "cũ",
        "bao-cao-tuan/logo.png": b"\x89PNG\r\n",
        "__MACOSX/bao-cao-tuan/._SKILL.md": "rác",
        "bao-cao-tuan/deep/SKILL.md": "không phải gốc",
    })
    result = service.import_package(db, skill_set.id, first, admin)
    assert result["replaced"] is False and result["slug"] == "bao-cao-tuan"
    skill = db.get(AiSkill, result["skill_id"])
    assert skill.summary == "Cách viết báo cáo tuần"
    paths = {f.path for f in db.query(AiSkillFile).filter(AiSkillFile.skill_id == skill.id)}
    assert paths == {"references/guide.md", "references/old.md", "deep/SKILL.md"}
    assert "logo.png" in result["skipped"]
    second = _zip({"SKILL.md": "---\nname: bao-cao-tuan\n---\nmới", "references/guide.md": "mới"})
    result = service.import_package(db, skill_set.id, second, admin)
    assert result["replaced"] is True
    paths = {f.path for f in db.query(AiSkillFile).filter(AiSkillFile.skill_id == skill.id)}
    assert paths == {"references/guide.md"}            # THAY GÓI = thay toàn bộ tệp
    assert db.get(AiSkill, skill.id).draft_body_md.endswith("mới")


def test_import_package_rejects_missing_skill_md_and_not_zip(org, admin):
    db = org.db
    skill_set = service.create_set(db, SkillSetIn(name="Bộ"), admin)
    with pytest.raises(HTTPException):
        service.import_package(db, skill_set.id, _zip({"README.md": "x"}), admin)
    with pytest.raises(HTTPException):
        service.import_package(db, skill_set.id, b"not a zip", admin)
    with pytest.raises(HTTPException):          # không có name trong frontmatter, không truyền slug
        service.import_package(db, skill_set.id, _zip({"SKILL.md": "# chỉ có thân"}), admin)


def test_me_endpoint_returns_only_published_version_fields(org, admin):
    db = org.db
    skill_set, skill = make_skill(db, admin)
    give(db, admin, skill_set.id, [(SUBJECT_DEPARTMENT, org.root.id)])
    service.update_skill(db, skill.id, SkillPatch(title="Tên nháp chưa xuất bản"), admin)
    row = access_service.visible_skills(db, org.boss)[0]
    assert row["title"] == "Quy trình mua"           # đọc bản ĐÃ XUẤT BẢN, không phải nháp
    assert row["version_no"] == 1 and row["skill_set"] == "Thu mua"
