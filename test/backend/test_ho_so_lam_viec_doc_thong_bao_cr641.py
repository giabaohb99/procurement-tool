"""duoc-CR-641 phase 03 — `tab_notification.read_at` ở hai đường đánh dấu đã đọc + cờ `usage_tracking` ở /auth/me."""
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.core import app_settings
from app.modules.auth.controller import _me_payload
from app.modules.notification.controller import mark_all_read, mark_read
from app.modules.notification.model import Notification

from ho_so_lam_viec_factory import make_person


def _notif(db, uid, read=False, read_at=None):
    n = Notification(user_id=uid, title="t", body="b", is_read=read, read_at=read_at)
    db.add(n)
    db.commit()
    return n


def test_doc_lan_dau_ghi_read_at_doc_lai_khong_ghi_de(db):
    user, _ = make_person(db, "N1")
    n = _notif(db, user.id)
    mark_read(n.id, db=db, user=user)
    db.refresh(n)
    first = n.read_at
    assert n.is_read and first is not None
    n.read_at = first - timedelta(hours=1)
    db.commit()
    mark_read(n.id, db=db, user=user)
    db.refresh(n)
    assert n.read_at == first - timedelta(hours=1)    # lần 2 không ghi đè mốc


def test_doc_het_chi_dong_chua_doc(db):
    user, _ = make_person(db, "N2")
    old = datetime(2026, 1, 1, 8, 0)
    done = _notif(db, user.id, read=True, read_at=old)
    fresh = _notif(db, user.id)
    other = _notif(db, user.id + 999)
    mark_all_read(db=db, user=user)
    for n in (done, fresh, other):
        db.refresh(n)
    assert done.read_at == old                       # dòng đã đọc không bị đụng
    assert fresh.is_read and fresh.read_at is not None
    assert not other.is_read and other.read_at is None   # của người khác không đụng


def test_auth_me_co_co_usage_tracking_theo_cong_tac(db):
    user, _ = make_person(db, "N3")
    payload = _me_payload(db, user)
    assert payload["usage_tracking"] is True          # mặc định BẬT
    app_settings._cache["usage_tracking_enabled"] = "false"
    assert _me_payload(db, user)["usage_tracking"] is False
