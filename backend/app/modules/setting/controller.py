from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import require
from app.core.database import get_db
from app.core.response import success

from . import service

router = APIRouter(prefix="/api/settings", tags=["setting"])


class SaveIn(BaseModel):
    values: dict = {}


class TestEmailIn(BaseModel):
    to: str = ""


@router.get("")
def get_settings(db: Session = Depends(get_db), user=Depends(require("setting", "read"))):
    return success(service.get_all())


@router.put("")
def save_settings(data: SaveIn, db: Session = Depends(get_db), user=Depends(require("setting", "write"))):
    return success(service.save(db, data.values, user.id), "Đã lưu cấu hình")


@router.post("/test-email")
def test_email(data: TestEmailIn, db: Session = Depends(get_db), user=Depends(require("setting", "write"))):
    ok, msg = service.test_email(data.to)
    return success({"ok": ok, "message": msg}, msg)


@router.post("/test-storage")
def test_storage(db: Session = Depends(get_db), user=Depends(require("setting", "write"))):
    ok, msg = service.test_storage()
    return success({"ok": ok, "message": msg}, msg)
