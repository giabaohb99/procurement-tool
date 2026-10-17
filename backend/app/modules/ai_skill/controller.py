"""`/api/ai-skills` — Kho skill AI (bao-CR-621, K1 của doc 21).

Hai lớp gác như mọi phân hệ: `require("ai_skill", action)` ở đường + phạm vi của BỘ qua `get_scoped` trong service
(ngoài phạm vi → 404). Riêng `/me` chỉ cần đăng nhập: ai cũng xem được AI của mình đang đọc skill nào.
Prefix KHÔNG nằm dưới `/api/assistant` / `/api/agent-hub` / `/api/mcp` — mấy prefix đó bị proxy sang dịch vụ AI.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, require
from app.core.database import get_db
from app.core.response import success

from . import access_service, service
from .constants import ENTITY, PACKAGE_MAX_BYTES, AccessTarget
from .schema import (AccessGrantIn, AccessRevokeIn, PublishIn, SkillFileIn, SkillIn, SkillPatch, SkillSetIn,
                     SkillSetPatch)

router = APIRouter(prefix="/api/ai-skills", tags=["ai_skill"])


@router.get("/me")
def my_visible_skills(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Skill AI của chính người đang đăng nhập được đọc (đúng thứ cổng MCP sẽ trả)."""
    return success({"items": access_service.visible_skills(db, user)})


# -- Bộ skill -----------------------------------------------------------------------------------------------------

@router.get("/sets")
def list_sets(db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success({"items": service.list_sets(db, user)})


@router.post("/sets")
def create_set(data: SkillSetIn, db: Session = Depends(get_db), user=Depends(require(ENTITY, "create"))):
    return success(service.serialize_set(service.create_set(db, data, user)), "Đã tạo bộ skill", 201)


@router.get("/sets/{set_id}")
def get_set(set_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(service.serialize_set(service.get_set(db, set_id, user)))


@router.patch("/sets/{set_id}")
def update_set(set_id: int, data: SkillSetPatch, db: Session = Depends(get_db),
               user=Depends(require(ENTITY, "write"))):
    return success(service.serialize_set(service.update_set(db, set_id, data, user)), "Đã lưu bộ skill")


@router.delete("/sets/{set_id}")
def delete_set(set_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    service.delete_set(db, set_id, user)
    return success(None, "Đã xóa bộ skill")


# -- Skill --------------------------------------------------------------------------------------------------------

@router.get("/sets/{set_id}/skills")
def list_skills(set_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success({"items": service.list_skills(db, set_id, user)})


@router.post("/sets/{set_id}/skills")
def create_skill(set_id: int, data: SkillIn, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    skill = service.create_skill(db, set_id, data, user)
    return success(service.get_skill(db, skill.id, user), "Đã tạo skill", 201)


@router.post("/sets/{set_id}/import")
async def import_package(set_id: int, file: UploadFile = File(...), slug: str = Query("", max_length=100),
                         db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    """Tải gói .zip / .skill. Trùng tên skill trong bộ → THAY GÓI (ghi đè nháp, thay toàn bộ tệp đính kèm)."""
    data = await file.read(PACKAGE_MAX_BYTES + 1)
    result = service.import_package(db, set_id, data, user, slug=slug)
    return success(result, "Đã thay gói skill" if result["replaced"] else "Đã tạo skill từ gói")


@router.get("/skills/{skill_id}")
def get_skill(skill_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(service.get_skill(db, skill_id, user))


@router.patch("/skills/{skill_id}")
def update_skill(skill_id: int, data: SkillPatch, db: Session = Depends(get_db),
                 user=Depends(require(ENTITY, "write"))):
    service.update_skill(db, skill_id, data, user)
    return success(service.get_skill(db, skill_id, user), "Đã lưu nháp skill")


@router.delete("/skills/{skill_id}")
def delete_skill(skill_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "delete"))):
    service.delete_skill(db, skill_id, user)
    return success(None, "Đã xóa skill")


@router.post("/skills/{skill_id}/publish")
def publish_skill(skill_id: int, data: PublishIn, db: Session = Depends(get_db),
                  user=Depends(require(ENTITY, "approve"))):
    version = service.publish_skill(db, skill_id, data.change_note, user)
    return success({"version_id": version.id, "version_no": version.version_no},
                   f"Đã xuất bản phiên bản {version.version_no}")


@router.get("/skills/{skill_id}/versions")
def list_versions(skill_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success({"items": service.list_versions(db, skill_id, user)})


@router.get("/versions/{version_id}")
def get_version(version_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success(service.get_version(db, version_id, user))


# -- Tệp đính kèm -------------------------------------------------------------------------------------------------

@router.get("/skills/{skill_id}/files")
def list_files(skill_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "read"))):
    return success({"items": service.list_files(db, skill_id, user)})


@router.put("/skills/{skill_id}/files")
def put_file(skill_id: int, data: SkillFileIn, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    row = service.put_file(db, skill_id, data.path, data.content_text, user)
    return success({"id": row.id, "path": row.path, "size": row.size}, "Đã lưu tệp")


@router.delete("/skills/{skill_id}/files/{file_id}")
def delete_file(skill_id: int, file_id: int, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    service.delete_file(db, skill_id, file_id, user)
    return success(None, "Đã xóa tệp")


# -- Ai được đọc --------------------------------------------------------------------------------------------------

def _check_target(db: Session, target_kind: int, target_id: int, user, action: str) -> None:
    """Gán quyền đọc cho bộ / skill nào thì phải có quyền trên chính BỘ đó (phạm vi quản trị)."""
    if target_kind == AccessTarget.SKILL_SET:
        service._set_or_404(db, target_id, user, action)
    elif target_kind == AccessTarget.SKILL:
        service._skill_or_404(db, target_id, user, action)
    else:
        raise HTTPException(400, "Đối tượng gán quyền không hợp lệ")


@router.get("/access")
def list_access(target_kind: int = Query(...), target_id: int = Query(..., gt=0), db: Session = Depends(get_db),
                user=Depends(require(ENTITY, "read"))):
    _check_target(db, target_kind, target_id, user, "read")
    return success({"items": access_service.list_access(db, target_kind, target_id)})


@router.post("/access")
def grant_access(data: AccessGrantIn, db: Session = Depends(get_db), user=Depends(require(ENTITY, "write"))):
    _check_target(db, data.target_kind, data.target_id, user, "write")
    return success(access_service.grant(db, data, user), "Đã lưu quyền đọc")


@router.delete("/access/{access_id}")
def revoke_access(access_id: int, data: AccessRevokeIn | None = None, db: Session = Depends(get_db),
                  user=Depends(require(ENTITY, "write"))):
    from .model import AiSkillAccess

    row = db.get(AiSkillAccess, access_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy dòng phân quyền")
    _check_target(db, row.target_kind, row.target_id, user, "write")
    access_service.revoke(db, access_id, data.reason if data else "", user)
    return success(None, "Đã thu hồi quyền đọc")
