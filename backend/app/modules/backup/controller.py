from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.audit import resolve_actor
from app.core.auth import require
from app.core.base_controller import pagination
from app.core.database import get_db
from app.core.response import success
from app.core.storage import presigned_url

from . import service
from .model import DbBackup
from .tasks import run_backup_task

router = APIRouter(prefix="/api/backups", tags=["backup"])


def _out(db, r: DbBackup) -> dict:
    return {
        "id": r.id, "source": r.source, "status": r.status,
        "file_key": r.file_key, "size_bytes": r.size_bytes, "message": r.message,
        "started_at": r.started_at, "finished_at": r.finished_at,
        "created_at": r.created_at, "created_by": r.created_by,
        "created_by_name": resolve_actor(db, r.created_by) if r.created_by else "Hệ thống (tự động)",
    }


@router.get("")
def list_(pg: dict = Depends(pagination), db: Session = Depends(get_db),
          user=Depends(require("backup", "read"))):
    q = db.query(DbBackup)
    total = q.count()
    items = q.order_by(DbBackup.id.desc()).offset(pg["offset"]).limit(pg["limit"]).all()
    return success({"total": total, "items": [_out(db, r) for r in items], "keep": service.KEEP})


@router.post("/run")
def run_now(db: Session = Depends(get_db), user=Depends(require("backup", "create"))):
    """Sao lưu ngay (bấm tay) — đẩy task vào worker, trả về ngay."""
    run_backup_task.delay(source="manual", actor_id=user.id)
    return success(None, "Đã bắt đầu sao lưu — làm mới danh sách sau vài giây", 202)


@router.get("/{bid}/download")
def download(bid: int, db: Session = Depends(get_db), user=Depends(require("backup", "read"))):
    """Trả URL tải file backup (presigned, hết hạn ngắn). Bucket private nên không link công khai."""
    r = db.get(DbBackup, bid)
    if not r or not r.file_key:
        raise HTTPException(404, "Không có file backup")
    name = r.file_key.split("/")[-1]
    url = presigned_url(r.file_key, expires=600, download_name=name)
    return success({"url": url, "filename": name})


@router.delete("/{bid}")
def delete_(bid: int, db: Session = Depends(get_db), user=Depends(require("backup", "delete"))):
    if not service.delete_backup(db, bid):
        raise HTTPException(404, "Không tìm thấy bản backup")
    return success(None, "Đã xóa bản backup")
