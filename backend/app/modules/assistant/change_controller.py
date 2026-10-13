"""Đường web ERP cho SỔ THAY ĐỔI do bot ghi + hoàn tác (ai-CR-182, phase 15.1).

Gác như các đường Trợ lý khác: đăng nhập + `assistant.read` + cờ AI bật. Dữ liệu chỉ của CHÍNH người gọi;
`all=1` (của mọi người) chỉ cho người có `agent_group.read` (quản lý bot AI) — kiểm trong service. Không có
entity phân quyền mới, không `db.get` trong controller (`test_pham_vi_duong_vong`): chủ sở hữu kiểm ở
`change_service.get_for`.

Bảng này nằm ở DB ERP nên router PHẢI đăng ký ở `app/main.py` TRƯỚC router chuyển tiếp `/api/assistant/*`
(ERP đã tách thì phần còn lại của Trợ lý sống ở dịch vụ AI, nhưng sổ này ở đây).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import change_service
from .change_model import ChangeSource
from .controller import _guard

router = APIRouter(prefix="/api/assistant/changes", tags=["assistant"])


@router.get("")
def list_changes(limit: int = Query(30, ge=1, le=change_service.LIST_MAX), all: int = Query(0, ge=0, le=1),
                 user=Depends(require("assistant", "read")), db: Session = Depends(get_db)):
    """Sổ thay đổi của tôi (mới nhất trước), mỗi dòng kèm `can_undo` + `undo_reason`. `all=1` = của mọi người."""
    _guard()
    return success({"items": change_service.list_for(db, user, limit=limit, all_users=bool(all))})


@router.get("/{change_id}")
def get_change(change_id: int, user=Depends(require("assistant", "read")), db: Session = Depends(get_db)):
    """Một dòng sổ kèm ảnh trước / sau. Của người khác (không phải quản lý bot AI) thì 404."""
    _guard()
    row = change_service.get_for(db, user, change_id)
    if row is None:
        raise HTTPException(404, "Không tìm thấy dòng thay đổi này.")
    return success(change_service.serialize(db, user, row, detail=True))


@router.post("/{change_id}/undo")
def undo_change(change_id: int, user=Depends(require("assistant", "read")), db: Session = Depends(get_db)):
    """Hoàn tác một dòng — kiểm lại từ đầu (hạn 24 giờ, chủ sở hữu, quyền, phạm vi, trạng thái, dấu phiếu)."""
    _guard()
    out = change_service.undo(db, user, change_id, source=int(ChangeSource.WEB))
    return success(out, message=out["summary"])
