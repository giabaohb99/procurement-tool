"""Web Push: lưu subscription của thiết bị + đẩy thông báo qua pywebpush (VAPID).

Best-effort: gửi lỗi không được làm hỏng luồng chính. Endpoint hết hạn (404/410) → tự xóa.
"""
import json
import os

from sqlalchemy.orm import Session

from .model import PushSubscription

# VAPID keys — public không bí mật (gửi cho trình duyệt); private nên đặt qua ENV ở prod.
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY",
                             "BISns6RZMWCc9ZlK6hD47LsMmxWqFKsfCS4pC9U49nop3ZzLmQlI7BhztRVMRycOy2FAiU09et5VrhagKwdUe_k")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "Hk2R7IrE6bk7zBXW7nN133AWGgAQZiYTOHeLUKeOD7M")
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:admin@degoholding.vn")


def save_subscription(db: Session, user_id: int, sub: dict) -> PushSubscription:
    """Lưu/cập nhật subscription theo endpoint (mỗi thiết bị 1 dòng)."""
    endpoint = (sub or {}).get("endpoint") or ""
    keys = (sub or {}).get("keys") or {}
    if not endpoint:
        return None
    row = db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).first()
    if not row:
        row = PushSubscription(endpoint=endpoint, created_by=user_id)
        db.add(row)
    row.user_id = user_id
    row.p256dh = keys.get("p256dh", "")
    row.auth = keys.get("auth", "")
    row.updated_by = user_id
    db.commit()
    return row


def remove_subscription(db: Session, endpoint: str) -> None:
    db.query(PushSubscription).filter(PushSubscription.endpoint == endpoint).delete()
    db.commit()


def send_to_users(db_factory, user_ids: list[int], title: str, body: str, url: str = "") -> None:
    """Đẩy Web Push tới mọi thiết bị của các user. Chạy nền — tự mở session riêng."""
    if not user_ids:
        return
    try:
        from pywebpush import webpush, WebPushException
    except Exception:
        return   # chưa cài pywebpush → bỏ qua (chuông vẫn chạy)
    db = db_factory()
    try:
        subs = db.query(PushSubscription).filter(PushSubscription.user_id.in_(list(user_ids))).all()
        payload = json.dumps({"title": title, "body": body, "url": url or "/"})
        for s in subs:
            try:
                webpush(
                    subscription_info={"endpoint": s.endpoint,
                                       "keys": {"p256dh": s.p256dh, "auth": s.auth}},
                    data=payload,
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": VAPID_SUBJECT},
                    timeout=10,
                )
            except WebPushException as ex:
                code = getattr(getattr(ex, "response", None), "status_code", None)
                if code in (404, 410):     # endpoint hết hạn → xóa
                    db.delete(s)
                    db.commit()
            except Exception:
                pass
    finally:
        db.close()
