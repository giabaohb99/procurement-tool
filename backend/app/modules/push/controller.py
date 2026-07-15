from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.response import success

from . import service

router = APIRouter(prefix="/api/push", tags=["push"])


@router.get("/vapid-public-key")
def vapid_public_key(user=Depends(get_current_user)):
    return success({"key": service.VAPID_PUBLIC_KEY})


@router.post("/subscribe")
def subscribe(sub: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    service.save_subscription(db, user.id, sub)
    return success(None, "Đã bật thông báo trên thiết bị này")


@router.post("/unsubscribe")
def unsubscribe(data: dict, db: Session = Depends(get_db), user=Depends(get_current_user)):
    service.remove_subscription(db, (data or {}).get("endpoint", ""))
    return success(None, "Đã tắt thông báo trên thiết bị này")
