"""API sổ việc chạy ngầm (bao-CR-703) — màn Hệ thống > Việc chạy ngầm. Chỉ đọc, gác setting.read (quản trị)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import service

router = APIRouter(prefix="/api/system/jobs", tags=["system-jobs"])


@router.get("")
def list_jobs(group: str = Query("", max_length=20), status: int | None = Query(None, ge=0, le=4),
              q: str = Query("", max_length=100), db: Session = Depends(get_db),
              user=Depends(require("setting", "read"))):
    return success(service.list_jobs(db, group=group, status=status, q=q))


@router.get("/{code}/runs")
def list_runs(code: str, status: int | None = Query(None, ge=1, le=4), page: int = Query(1, ge=1, le=10_000),
              page_size: int = Query(20, ge=1, le=200), db: Session = Depends(get_db),
              user=Depends(require("setting", "read"))):
    return success(service.list_runs(db, code[:120], status=status, page=page, page_size=page_size))
