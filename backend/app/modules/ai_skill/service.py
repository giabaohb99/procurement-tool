"""Soạn / xuất bản / tệp / nhập gói của Kho skill AI (bao-CR-621, K1).

Phạm vi QUẢN TRỊ: mọi thao tác trên bộ đi qua `get_scoped(..., entity="ai_skill", action=...)` của bộ — skill, phiên
bản, tệp không có phạm vi riêng mà ăn theo BỘ chứa nó. Ngoài phạm vi trả 404 như id không tồn tại.
"""
from __future__ import annotations

import hashlib
import io
import posixpath
import re
import zipfile
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.audit import record
from app.core.auth import get_perm_profile
from app.core.scoping import apply_scope, get_scoped

from .constants import (BODY_MAX_CHARS, ENTITY, FILE_MAX_BYTES, FILE_PATH_MAX, FILE_PATH_MAX_DEPTH, FILES_MAX_BYTES,
                        PACKAGE_MAX_BYTES, PACKAGE_MAX_ENTRIES, SECURITY_LEVEL_LABELS, SKILL_SET_STATUS_LABELS,
                        SKILL_STATUS_LABELS, SUMMARY_MAX, TEXT_FILE_EXTS, TITLE_MAX, SkillSetStatus, SkillStatus)
from .model import AiSkill, AiSkillFile, AiSkillSet, AiSkillVersion
from .schema import SLUG_HINT, SLUG_RE

AUDIT_SET = "ai_skill_set"
AUDIT_SKILL = "ai_skill"
_SEGMENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_JUNK = ("__MACOSX/", ".DS_Store")


def _iso(value):
    return value.isoformat(timespec="seconds") if value else None


# ---------------------------------------------------------------------------
# Bộ skill
# ---------------------------------------------------------------------------

def _set_or_404(db: Session, set_id: int, user, action: str) -> AiSkillSet:
    row = get_scoped(db, AiSkillSet, ENTITY, set_id, user, get_perm_profile(db, user), action=action)
    if row is None:
        raise HTTPException(404, "Không tìm thấy bộ skill")
    return row


def serialize_set(row: AiSkillSet, skill_count: int = 0) -> dict:
    return {
        "id": row.id, "code": row.code, "name": row.name, "description": row.description,
        "company_id": row.company_id, "owner_department_id": row.owner_department_id,
        "status": row.status, "status_label": SKILL_SET_STATUS_LABELS.get(row.status, ""),
        "security_level": row.security_level, "security_level_label": SECURITY_LEVEL_LABELS.get(row.security_level, ""),
        "sort_order": row.sort_order, "skill_count": skill_count,
        "created_at": _iso(row.created_at), "updated_at": _iso(row.updated_at),
    }


def list_sets(db: Session, user) -> list[dict]:
    query = apply_scope(db.query(AiSkillSet), AiSkillSet, ENTITY, user, get_perm_profile(db, user))
    rows = query.order_by(AiSkillSet.sort_order, AiSkillSet.id).all()
    counts = {}
    if rows:
        counts = dict(db.query(AiSkill.skill_set_id, func.count(AiSkill.id))
                      .filter(AiSkill.skill_set_id.in_([r.id for r in rows]), AiSkill.is_deleted.is_(False))
                      .group_by(AiSkill.skill_set_id).all())
    return [serialize_set(r, counts.get(r.id, 0)) for r in rows]


def get_set(db: Session, set_id: int, user) -> AiSkillSet:
    return _set_or_404(db, set_id, user, "read")


def create_set(db: Session, data, user) -> AiSkillSet:
    profile = get_perm_profile(db, user)
    code = (data.code or "").strip()
    if code and db.query(AiSkillSet.id).filter(AiSkillSet.code == code, AiSkillSet.is_deleted.is_(False)).first():
        raise HTTPException(400, f"Mã bộ skill «{code}» đã có")
    row = AiSkillSet(code=code, name=data.name.strip(), description=data.description,
                     company_id=data.company_id or int(profile.get("company_id") or 0),
                     owner_department_id=data.owner_department_id, status=data.status,
                     security_level=data.security_level, sort_order=data.sort_order,
                     created_by=user.id, updated_by=user.id)
    db.add(row)
    db.flush()
    if not row.code:
        row.code = f"SK{row.id:04d}"
    #  Tạo xong phải còn nằm trong phạm vi GHI của chính người tạo — chặn trưởng phòng tạo bộ cho phòng khác rồi
    #  mất quyền quản lý chính bộ mình vừa tạo (hoặc lách phạm vi bằng cách gán phòng chủ quản ngoài nhánh).
    if get_scoped(db, AiSkillSet, ENTITY, row.id, user, profile, action="write") is None:
        db.rollback()
        raise HTTPException(403, "Bộ skill này nằm ngoài phạm vi bạn được quản lý (pháp nhân / phòng chủ quản)")
    db.commit()
    record(db, user.id, AUDIT_SET, row.id, "create", f"Tạo bộ skill {row.code} — {row.name}", doc_code=row.code)
    return row


def update_set(db: Session, set_id: int, data, user) -> AiSkillSet:
    row = _set_or_404(db, set_id, user, "write")
    changes = data.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(row, key, value.strip() if isinstance(value, str) and key == "name" else value)
    row.updated_by = user.id
    db.flush()
    if get_scoped(db, AiSkillSet, ENTITY, row.id, user, get_perm_profile(db, user), action="write") is None:
        db.rollback()
        raise HTTPException(403, "Đổi phòng chủ quản ra ngoài phạm vi bạn được quản lý là không được")
    db.commit()
    record(db, user.id, AUDIT_SET, row.id, "update", f"Sửa bộ skill {row.code}: {', '.join(changes) or '—'}",
           doc_code=row.code)
    return row


def delete_set(db: Session, set_id: int, user) -> None:
    from app.core.base_model import mark_deleted

    row = _set_or_404(db, set_id, user, "delete")
    mark_deleted(row, user.id)
    for skill in db.query(AiSkill).filter(AiSkill.skill_set_id == row.id, AiSkill.is_deleted.is_(False)):
        mark_deleted(skill, user.id)
    db.commit()
    record(db, user.id, AUDIT_SET, row.id, "delete", f"Xóa bộ skill {row.code}", doc_code=row.code)


# ---------------------------------------------------------------------------
# Skill
# ---------------------------------------------------------------------------

def serialize_skill(row: AiSkill, version: AiSkillVersion | None = None, with_body: bool = False) -> dict:
    out = {
        "id": row.id, "skill_set_id": row.skill_set_id, "slug": row.slug, "title": row.title, "summary": row.summary,
        "status": row.status, "status_label": SKILL_STATUS_LABELS.get(row.status, ""),
        "current_version_id": row.current_version_id, "version_no": version.version_no if version else 0,
        "published_at": _iso(version.published_at) if version else None,
        "has_unpublished_changes": bool(row.draft_updated_at and (version is None or version.published_at is None
                                                                  or row.draft_updated_at > version.published_at)),
        "draft_updated_at": _iso(row.draft_updated_at), "sort_order": row.sort_order,
    }
    if with_body:
        out["draft_body_md"] = row.draft_body_md or ""
    return out


def _skill_or_404(db: Session, skill_id: int, user, action: str) -> tuple[AiSkill, AiSkillSet]:
    skill = db.get(AiSkill, skill_id)
    if skill is None or skill.is_deleted:
        raise HTTPException(404, "Không tìm thấy skill")
    return skill, _set_or_404(db, skill.skill_set_id, user, action)


def _slug_taken(db: Session, set_id: int, slug: str, skip_id: int = 0) -> bool:
    query = db.query(AiSkill.id).filter(AiSkill.skill_set_id == set_id, AiSkill.slug == slug,
                                        AiSkill.is_deleted.is_(False))
    if skip_id:
        query = query.filter(AiSkill.id != skip_id)
    return query.first() is not None


def list_skills(db: Session, set_id: int, user) -> list[dict]:
    _set_or_404(db, set_id, user, "read")
    rows = (db.query(AiSkill).filter(AiSkill.skill_set_id == set_id, AiSkill.is_deleted.is_(False))
            .order_by(AiSkill.sort_order, AiSkill.id).all())
    versions = {v.id: v for v in db.query(AiSkillVersion).filter(
        AiSkillVersion.id.in_([r.current_version_id for r in rows if r.current_version_id]))} if rows else {}
    return [serialize_skill(r, versions.get(r.current_version_id)) for r in rows]


def get_skill(db: Session, skill_id: int, user) -> dict:
    skill, _ = _skill_or_404(db, skill_id, user, "read")
    version = db.get(AiSkillVersion, skill.current_version_id) if skill.current_version_id else None
    out = serialize_skill(skill, version, with_body=True)
    out["files"] = list_files(db, skill_id, user, _checked=True)
    return out


def create_skill(db: Session, set_id: int, data, user) -> AiSkill:
    skill_set = _set_or_404(db, set_id, user, "write")
    if _slug_taken(db, skill_set.id, data.slug):
        raise HTTPException(400, f"Bộ này đã có skill tên «{data.slug}»")
    row = AiSkill(skill_set_id=skill_set.id, slug=data.slug, title=data.title or data.slug, summary=data.summary,
                  draft_body_md=data.body_md, draft_updated_at=datetime.now(), sort_order=data.sort_order,
                  status=int(SkillStatus.DRAFT), created_by=user.id, updated_by=user.id)
    db.add(row)
    db.commit()
    record(db, user.id, AUDIT_SKILL, row.id, "create", f"Tạo skill {row.slug} trong bộ {skill_set.code}",
           doc_code=row.slug, parent=(AUDIT_SET, skill_set.id))
    return row


def update_skill(db: Session, skill_id: int, data, user) -> AiSkill:
    skill, skill_set = _skill_or_404(db, skill_id, user, "write")
    changes = data.model_dump(exclude_unset=True)
    if "body_md" in changes:
        skill.draft_body_md = changes.pop("body_md") or ""
        skill.draft_updated_at = datetime.now()
    for key in ("title", "summary"):
        if key in changes:
            setattr(skill, key, changes.pop(key) or "")
            skill.draft_updated_at = datetime.now()
    if "status" in changes:
        status = changes.pop("status")
        if status == SkillStatus.ACTIVE and not skill.current_version_id:
            raise HTTPException(400, "Skill chưa xuất bản lần nào — bấm Xuất bản để đưa vào dùng")
        skill.status = status
    if "sort_order" in changes:
        skill.sort_order = changes.pop("sort_order")
    skill.updated_by = user.id
    db.commit()
    record(db, user.id, AUDIT_SKILL, skill.id, "update", f"Sửa skill {skill.slug}", doc_code=skill.slug,
           parent=(AUDIT_SET, skill_set.id))
    return skill


def delete_skill(db: Session, skill_id: int, user) -> None:
    from app.core.base_model import mark_deleted

    skill, skill_set = _skill_or_404(db, skill_id, user, "delete")
    mark_deleted(skill, user.id)
    db.commit()
    record(db, user.id, AUDIT_SKILL, skill.id, "delete", f"Xóa skill {skill.slug}", doc_code=skill.slug,
           parent=(AUDIT_SET, skill_set.id))


def publish_skill(db: Session, skill_id: int, change_note: str, user) -> AiSkillVersion:
    """Chép bản nháp thành một phiên bản mới (chỉ thêm) và đặt làm bản hiện hành — cần quyền DUYỆT trên bộ."""
    skill, skill_set = _skill_or_404(db, skill_id, user, "approve")
    body = (skill.draft_body_md or "").strip()
    if not body:
        raise HTTPException(400, "Nội dung skill đang trống — viết hướng dẫn cho AI rồi mới xuất bản")
    if not (skill.summary or "").strip():
        raise HTTPException(400, "Thiếu tóm tắt cho AI — AI chọn skill bằng chính câu tóm tắt này")
    last = db.query(func.max(AiSkillVersion.version_no)).filter(AiSkillVersion.skill_id == skill.id).scalar() or 0
    version = AiSkillVersion(skill_id=skill.id, version_no=int(last) + 1, title=skill.title, summary=skill.summary,
                             body_md=skill.draft_body_md, change_note=change_note or "",
                             published_at=datetime.now(), published_by=user.id,
                             created_by=user.id, updated_by=user.id)
    db.add(version)
    db.flush()
    skill.current_version_id = version.id
    skill.status = int(SkillStatus.ACTIVE)
    skill.updated_by = user.id
    db.commit()
    record(db, user.id, AUDIT_SKILL, skill.id, "approve",
           f"Xuất bản skill {skill.slug} phiên bản {version.version_no}" + (f": {change_note}" if change_note else ""),
           doc_code=skill.slug, parent=(AUDIT_SET, skill_set.id))
    return version


def list_versions(db: Session, skill_id: int, user) -> list[dict]:
    skill, _ = _skill_or_404(db, skill_id, user, "read")
    rows = (db.query(AiSkillVersion).filter(AiSkillVersion.skill_id == skill.id)
            .order_by(AiSkillVersion.version_no.desc()).all())
    return [{"id": v.id, "version_no": v.version_no, "title": v.title, "change_note": v.change_note,
             "published_at": _iso(v.published_at), "published_by": v.published_by,
             "is_current": v.id == skill.current_version_id} for v in rows]


def get_version(db: Session, version_id: int, user) -> dict:
    version = db.get(AiSkillVersion, version_id)
    if version is None:
        raise HTTPException(404, "Không tìm thấy phiên bản")
    _skill_or_404(db, version.skill_id, user, "read")
    return {"id": version.id, "skill_id": version.skill_id, "version_no": version.version_no, "title": version.title,
            "summary": version.summary, "body_md": version.body_md, "change_note": version.change_note,
            "published_at": _iso(version.published_at)}


# ---------------------------------------------------------------------------
# Tệp đính kèm dạng chữ
# ---------------------------------------------------------------------------

def check_file_path(path: str) -> str:
    """Đường dẫn tương đối an toàn: tối đa 200 ký tự, 6 đoạn, mỗi đoạn bắt đầu bằng chữ / số; không `..`, không `\\`,
    không đoạn bắt đầu bằng dấu chấm; đuôi phải là tệp chữ."""
    path = (path or "").strip()
    if "\\" in path or ".." in path.split("/") or not path or len(path) > FILE_PATH_MAX:
        raise HTTPException(400, f"Đường dẫn tệp không hợp lệ: {path[:80]}")
    parts = path.split("/")
    if len(parts) > FILE_PATH_MAX_DEPTH or not all(_SEGMENT_RE.match(p) for p in parts):
        raise HTTPException(400, f"Đường dẫn tệp không hợp lệ (chữ không dấu, số, . _ -; tối đa "
                                 f"{FILE_PATH_MAX_DEPTH} cấp): {path[:80]}")
    if not path.lower().endswith(TEXT_FILE_EXTS):
        raise HTTPException(400, f"Chỉ nhận tệp dạng chữ ({', '.join(TEXT_FILE_EXTS)}): {path[:80]}")
    return path


def list_files(db: Session, skill_id: int, user, _checked: bool = False) -> list[dict]:
    if not _checked:
        _skill_or_404(db, skill_id, user, "read")
    rows = db.query(AiSkillFile).filter(AiSkillFile.skill_id == skill_id).order_by(AiSkillFile.path).all()
    return [{"id": f.id, "path": f.path, "size": f.size, "updated_at": _iso(f.updated_at)} for f in rows]


def _put_file_row(db: Session, skill: AiSkill, path: str, text: str, user) -> AiSkillFile:
    raw = text.encode("utf-8")
    if len(raw) > FILE_MAX_BYTES:
        raise HTTPException(400, f"Tệp {path} vượt {FILE_MAX_BYTES // (1024 * 1024)} MB")
    row = db.query(AiSkillFile).filter(AiSkillFile.skill_id == skill.id, AiSkillFile.path == path).first()
    if row is None:
        row = AiSkillFile(skill_id=skill.id, path=path, created_by=user.id)
        db.add(row)
    row.content_text, row.size, row.sha256 = text, len(raw), hashlib.sha256(raw).hexdigest()
    row.updated_by = user.id
    return row


def _check_total(db: Session, skill_id: int) -> None:
    total = db.query(func.coalesce(func.sum(AiSkillFile.size), 0)).filter(AiSkillFile.skill_id == skill_id).scalar()
    if int(total or 0) > FILES_MAX_BYTES:
        raise HTTPException(400, f"Tổng tệp đính kèm của một skill tối đa {FILES_MAX_BYTES // (1024 * 1024)} MB")


def put_file(db: Session, skill_id: int, path: str, text: str, user) -> AiSkillFile:
    """Thêm / ghi đè MỘT tệp theo đường dẫn — các tệp khác giữ nguyên (khác «Thay gói»)."""
    skill, skill_set = _skill_or_404(db, skill_id, user, "write")
    path = check_file_path(path)
    row = _put_file_row(db, skill, path, text, user)
    db.flush()
    _check_total(db, skill.id)
    skill.draft_updated_at = datetime.now()
    db.commit()
    record(db, user.id, AUDIT_SKILL, skill.id, "update", f"Ghi tệp {path} của skill {skill.slug}",
           doc_code=skill.slug, parent=(AUDIT_SET, skill_set.id))
    return row


def delete_file(db: Session, skill_id: int, file_id: int, user) -> None:
    skill, skill_set = _skill_or_404(db, skill_id, user, "write")
    row = db.get(AiSkillFile, file_id)
    if row is None or row.skill_id != skill.id:
        raise HTTPException(404, "Không tìm thấy tệp")
    db.delete(row)
    skill.draft_updated_at = datetime.now()
    db.commit()
    record(db, user.id, AUDIT_SKILL, skill.id, "update", f"Xóa tệp {row.path} của skill {skill.slug}",
           doc_code=skill.slug, parent=(AUDIT_SET, skill_set.id))


# ---------------------------------------------------------------------------
# Nhập gói .zip / .skill
# ---------------------------------------------------------------------------

_FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def parse_front_matter(text: str) -> tuple[dict, str]:
    """Phần đầu `---` của SKILL.md: chỉ đọc `name` và `description` (một dòng mỗi trường)."""
    match = _FRONT_RE.match(text or "")
    if not match:
        return {}, text or ""
    meta = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        key = key.strip().lower()
        if key in ("name", "description"):
            meta[key] = value.strip().strip("\"'")
    return meta, text[match.end():]


def read_package(data: bytes) -> dict:
    """Đọc gói: tìm SKILL.md nông nhất (không phân biệt hoa thường) làm gốc; mọi tệp chữ còn lại dưới gốc thành tệp
    đính kèm giữ đường dẫn tương đối. Tệp nhị phân / đường dẫn xấu → bỏ qua và báo lại."""
    if len(data) > PACKAGE_MAX_BYTES:
        raise HTTPException(400, f"Gói vượt {PACKAGE_MAX_BYTES // (1024 * 1024)} MB")
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise HTTPException(400, "Tệp không phải gói .zip / .skill hợp lệ")
    infos = [i for i in archive.infolist() if not i.is_dir()]
    if len(infos) > PACKAGE_MAX_ENTRIES:
        raise HTTPException(400, f"Gói có quá {PACKAGE_MAX_ENTRIES} mục")
    skill_md = sorted((i for i in infos if posixpath.basename(i.filename).lower() == "skill.md"),
                      key=lambda i: i.filename.count("/"))
    if not skill_md:
        raise HTTPException(400, "Gói phải có tệp SKILL.md")
    root = posixpath.dirname(skill_md[0].filename)
    prefix = f"{root}/" if root else ""
    files, skipped = {}, []
    for info in infos:
        name = info.filename
        if info is skill_md[0] or any(j in name for j in _JUNK) or not name.startswith(prefix):
            continue
        rel = name[len(prefix):]
        if info.file_size > FILE_MAX_BYTES:
            skipped.append(f"{rel} (quá 2 MB)")
            continue
        try:
            rel = check_file_path(rel)
            files[rel] = archive.read(info).decode("utf-8")
        except HTTPException:
            skipped.append(rel)
        except UnicodeDecodeError:
            skipped.append(f"{rel} (không phải chữ UTF-8)")
    try:
        body = archive.read(skill_md[0]).decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "SKILL.md phải là chữ UTF-8")
    meta, _ = parse_front_matter(body)
    if len(body) > BODY_MAX_CHARS:
        raise HTTPException(400, f"SKILL.md vượt {BODY_MAX_CHARS:,} ký tự")
    return {"body": body, "meta": meta, "files": files, "skipped": skipped}


def import_package(db: Session, set_id: int, data: bytes, user, slug: str = "") -> dict:
    """Tạo skill mới từ gói, hoặc THAY GÓI cho skill trùng tên: ghi đè nháp và THAY TOÀN BỘ tệp đính kèm."""
    skill_set = _set_or_404(db, set_id, user, "write")
    package = read_package(data)
    slug = (slug or package["meta"].get("name") or "").strip()
    if not SLUG_RE.match(slug):
        raise HTTPException(400, f"Không đặt được tên skill từ gói. {SLUG_HINT}")
    summary = (package["meta"].get("description") or "")[:SUMMARY_MAX]
    skill = (db.query(AiSkill).filter(AiSkill.skill_set_id == skill_set.id, AiSkill.slug == slug,
                                      AiSkill.is_deleted.is_(False)).first())
    replaced = skill is not None
    if skill is None:
        skill = AiSkill(skill_set_id=skill_set.id, slug=slug, title=slug[:TITLE_MAX], summary=summary,
                        status=int(SkillStatus.DRAFT), created_by=user.id)
        db.add(skill)
        db.flush()
    elif summary:
        skill.summary = summary
    skill.draft_body_md = package["body"]
    skill.draft_updated_at = datetime.now()
    skill.updated_by = user.id
    if replaced:
        db.query(AiSkillFile).filter(AiSkillFile.skill_id == skill.id).delete(synchronize_session=False)
    for path, text in package["files"].items():
        _put_file_row(db, skill, path, text, user)
    db.flush()
    _check_total(db, skill.id)
    db.commit()
    record(db, user.id, AUDIT_SKILL, skill.id, "update" if replaced else "create",
           f"{'Thay gói' if replaced else 'Tạo từ gói'} skill {slug}: {len(package['files'])} tệp, "
           f"bỏ qua {len(package['skipped'])}", doc_code=slug, parent=(AUDIT_SET, skill_set.id))
    return {"skill_id": skill.id, "slug": slug, "replaced": replaced, "files": len(package["files"]),
            "skipped": package["skipped"]}
