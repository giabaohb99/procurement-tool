"""API GÓI QUYỀN MẶC ĐỊNH CỦA CHỨC VỤ — `/api/job-positions/{id}/roles` (duoc-CR-653).

Gác bằng quyền QUẢN LÝ VAI TRÒ (`role.read` / `role.write`), không phải `job_position.write`: người
sửa danh mục chức vụ (Nhân sự) chưa chắc được quyết ai nhận quyền gì. Sửa gói và «Áp lại» còn qua chốt
chống nâng quyền L2 của `core/privilege_escalation` — gói là cách cấp quyền cho người KHÁC.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import privilege_escalation
from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import position_role_service as svc

router = APIRouter(prefix="/api/job-positions", tags=["job-position-roles"])


class PositionRolesUpdate(BaseModel):
    #  Trần 200: số vai trò toàn hệ chỉ vài chục; trần chặn gói rác chứ không phải luật nghiệp vụ.
    role_ids: list[int] = Field(default_factory=list, max_length=200)


@router.get("/{position_id}/roles")
def get_position_roles(position_id: int, db: Session = Depends(get_db),
                       user=Depends(require("role", "read"))):
    svc.require_position(db, position_id)
    return success({"roles": svc.get_bundle(db, position_id),
                    "eligible_holders": svc.count_eligible_holders(db, position_id)})


@router.put("/{position_id}/roles")
def set_position_roles(position_id: int, data: PositionRolesUpdate, db: Session = Depends(get_db),
                       user=Depends(require("role", "write"))):
    position = svc.require_position(db, position_id)
    new_ids = sorted(set(data.role_ids))
    privilege_escalation.block_missing_roles(db, new_ids)
    svc.block_forbidden_roles(db, new_ids)          # admin / ghi-tạo-xóa trên role, user (M5)
    #  Chỉ vai trò MỚI THÊM mới cần chốt: bỏ bớt thì không trao thêm quyền cho ai.
    added = sorted(set(new_ids) - set(svc.bundle_role_ids(db, position_id)))
    if added and not privilege_escalation.is_system_admin(db, user.id):
        #  H2: không tự thêm quyền vào gói của CHÍNH chức vụ mình đang giữ (L1 cho đường gói).
        if svc.actor_holds_position(db, user, position_id):
            raise HTTPException(403, "Bạn đang giữ chức vụ này nên không tự thêm vai trò vào quyền mặc định của nó. "
                                     + privilege_escalation.SELF_CHANGE_MESSAGE)
    privilege_escalation.block_role_escalation(db, user, added)
    svc.set_bundle(db, position, new_ids, user.id)
    return success({"roles": svc.get_bundle(db, position_id),
                    "eligible_holders": svc.count_eligible_holders(db, position_id)},
                   "Đã lưu quyền mặc định của chức vụ. Chưa áp cho người đang giữ — bấm «Áp lại» nếu cần.")


@router.post("/{position_id}/roles/apply")
def apply_position_roles(position_id: int, db: Session = Depends(get_db),
                         user=Depends(require("role", "write"))):
    position = svc.require_position(db, position_id)
    summary = svc.reapply_to_holders(db, position, user)
    return success(summary, f"Đã áp lại cho {summary['holders']} người giữ chức vụ")
