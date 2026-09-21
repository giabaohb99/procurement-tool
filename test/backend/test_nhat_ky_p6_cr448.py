"""bao-CR-448 — CR-312 P6 đợt 1: cảnh báo bất thường lên chuông + dọn bốn bảng quá 16 tháng.

Hai luật cứng được canh ở đây:

1. **Gói xong mới xóa, theo từng tháng của từng bảng.** Tháng nào chưa có tệp
   `.sha256` trên R2 thì tháng đó giữ nguyên dù đã quá hạn — và cả bốn bảng
   phải nằm trong danh sách đóng gói, không thì hai bảng sau không bao giờ được
   dọn (hoặc bị dọn mà không có bản sao).
2. **Mỗi sự kiện bất thường báo ĐÚNG MỘT LẦN.** Cửa sổ quét dài gấp đôi nhịp
   chạy nên cùng dòng dữ liệu được nhìn hai lần; không có dòng đánh dấu
   `anomaly_alert` là chuông kêu đúp.

Tài liệu: `doc/tai-lieu-ky-thuat/nhat-ky-va-phien-dang-nhap.md` §9, §10.
"""
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.action_catalog import ACTION_LABELS
from app.core.logging_codes import ACTION_GROUP_DELETE, CHANGE_OP_DELETE
from app.core.logging_policy import (ANOMALY_BULK_DELETE_MIN, ANOMALY_FORBIDDEN_MIN,
                                     ANOMALY_WINDOW_MINUTES)
from app.modules.audit.model import AuditLog
from app.modules.audit.tasks import ARCHIVE_TABLES
from app.modules.change_log.model import ChangeLog
from app.modules.login_session.model import LoginSession
from app.modules.notification.model import Notification
from app.modules.request_log.model import RequestLog
from app.modules.system_log import anomaly, retention
from app.modules.system_log.tasks import cleanup_expired_logs_task
from app.modules.user.model import User

NOW = datetime(2026, 9, 21, 10, 0, 0)


# ---------------------------------------------------------------------------
# Dựng dữ liệu
# ---------------------------------------------------------------------------
def _user(db, handle: str) -> User:
    user = User(email=f"{handle}@test.local", is_active=True)
    db.add(user)
    db.flush()
    return user


def _session(db, user_id: int, ip: str, created_at: datetime, revoked_at=None,
             expires_at=None, last_seen_ip: str = "") -> LoginSession:
    row = LoginSession(user_id=user_id, token_id=str(uuid.uuid4()), ip=ip,
                       last_seen_ip=last_seen_ip or ip, device_label="chrome / windows",
                       created_at=created_at, revoked_at=revoked_at,
                       expires_at=expires_at or created_at + timedelta(days=7))
    db.add(row)
    db.flush()
    return row


def _request(db, created_at: datetime, *, user_id: int = 0, session_id=None, ip: str = "1.1.1.1",
             status: int = 200, device_hash: bytes | None = None) -> RequestLog:
    row = RequestLog(request_id=uuid.uuid4().bytes, method="GET", path="/api/x", route="/api/x",
                     http_status=status, user_id=user_id, session_id=session_id, ip=ip,
                     device_hash=device_hash, created_at=created_at)
    db.add(row)
    db.flush()
    return row


def _audit(db, created_at: datetime, **extra) -> AuditLog:
    row = AuditLog(entity="unit", entity_id=1, action=extra.pop("action", "update"), message="x",
                   created_by=extra.pop("created_by", 1), created_at=created_at, **extra)
    db.add(row)
    db.flush()
    return row


def _change(db, created_at: datetime, **extra) -> ChangeLog:
    row = ChangeLog(table_name="tab_unit", row_id=1, field="name", created_at=created_at, **extra)
    db.add(row)
    db.flush()
    return row


def _admin_with_session_read(db, cap_quyen) -> User:
    admin = _user(db, "quantri")
    cap_quyen(admin.id, "login_session", scope="all", read=True)
    return admin


def _bells(db, user_id: int) -> list[Notification]:
    return db.query(Notification).filter(Notification.user_id == user_id).all()


def _markers(db) -> list[AuditLog]:
    return db.query(AuditLog).filter(AuditLog.action == anomaly.ACTION_ANOMALY).all()


# ---------------------------------------------------------------------------
# Khai báo
# ---------------------------------------------------------------------------
def test_dong_goi_du_bon_bang():
    """Thiếu bảng nào ở đây là bảng đó không bao giờ được dọn — hoặc bị dọn mà không có bản sao."""
    assert [name for name, _ in ARCHIVE_TABLES] == ["audit", "request", "change", "session"]


def test_ma_canh_bao_da_dang_ky_nhan():
    assert ACTION_LABELS[anomaly.ACTION_ANOMALY] == "Cảnh báo bất thường"


def test_moc_16_thang_lam_tron_dau_thang():
    assert retention.retention_cutoff(NOW) == datetime(2025, 5, 1)
    assert retention.retention_cutoff(datetime(2026, 1, 15), months=1) == datetime(2025, 12, 1)


# ---------------------------------------------------------------------------
# Dọn 16 tháng
# ---------------------------------------------------------------------------
@pytest.fixture
def cleanup(db, monkeypatch):
    """Việc dọn chạy trên DB của fixture; R2 coi như sẵn sàng; gói tồn tại theo tập `packaged`."""
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.modules.system_log.tasks.SessionLocal", Session)
    monkeypatch.setattr("app.modules.system_log.tasks.is_remote_storage_ready", lambda: True)
    packaged: set[str] = set()
    asked: list[str] = []

    def _key_exists(key: str) -> bool:
        asked.append(key)
        return any(key.endswith(f"/{label}/{name}.jsonl.gz.sha256") for name, label in
                   (item.split(":") for item in packaged))

    monkeypatch.setattr("app.modules.system_log.retention.key_exists", _key_exists)

    def _run(**kw):
        return retention.cleanup_expired(db, now=NOW, **kw)

    return type("Cleanup", (), {"run": staticmethod(_run), "packaged": packaged, "asked": asked})


def test_khong_co_r2_thi_khong_don(monkeypatch, db):
    monkeypatch.setattr("app.modules.system_log.tasks.is_remote_storage_ready", lambda: False)
    result = cleanup_expired_logs_task()
    assert result["status"] == "skipped" and result["reason"] == "no_remote_archive"


def test_chi_xoa_thang_da_co_goi(cleanup, db):
    #  Hai tháng quá hạn: 2025-03 có gói, 2025-04 chưa. Một dòng còn hạn.
    _audit(db, datetime(2025, 3, 10))
    _audit(db, datetime(2025, 3, 20))
    _audit(db, datetime(2025, 4, 5))
    _audit(db, datetime(2026, 9, 1))
    db.commit()
    cleanup.packaged.add("audit:2025-03")

    result = cleanup.run()

    assert result["deleted"] == {"audit": 2}
    assert "audit:2025-04" in result["skipped"]
    remaining = sorted(r.created_at for r in db.query(AuditLog).all())
    assert remaining == [datetime(2025, 4, 5), datetime(2026, 9, 1)]
    #  Hỏi R2 đúng khóa của việc đóng gói — lệch một ký tự là không bao giờ dọn được.
    assert any(k.endswith("/log-archive/2025-03/audit.jsonl.gz.sha256") for k in cleanup.asked)


def test_bon_bang_deu_duoc_don(cleanup, db):
    old = datetime(2025, 2, 14)
    _audit(db, old)
    _request(db, old)
    _change(db, old)
    _session(db, 1, "1.1.1.1", old, revoked_at=old + timedelta(hours=8))
    db.commit()
    cleanup.packaged.update({"audit:2025-02", "request:2025-02", "change:2025-02", "session:2025-02"})

    result = cleanup.run()

    assert result["deleted"] == {"audit": 1, "request": 1, "change": 1, "session": 1}
    assert result["skipped"] == [] and result["status"] == "success"


def test_phien_con_song_hoac_chua_het_han_thi_giu(cleanup, db):
    old = datetime(2025, 2, 14)
    #  Phiên mở tháng 02/2025 nhưng chưa ai đóng và hạn sống... rất xa (dữ liệu lỗi) — giữ.
    _session(db, 1, "1.1.1.1", old, expires_at=datetime(2026, 12, 31))
    #  Phiên đóng đàng hoàng — xóa.
    _session(db, 1, "1.1.1.1", old, revoked_at=old + timedelta(days=1))
    db.commit()
    cleanup.packaged.add("session:2025-02")

    result = cleanup.run()

    assert result["deleted"] == {"session": 1}
    assert db.query(LoginSession).count() == 1


def test_dry_run_chi_dem_khong_xoa(cleanup, db):
    _audit(db, datetime(2025, 1, 3))
    db.commit()
    cleanup.packaged.add("audit:2025-01")

    result = cleanup.run(dry_run=True)

    assert result["status"] == "dry_run" and result["matched"] == {"audit": 1}
    assert result["deleted"] == {} and db.query(AuditLog).count() == 1


# ---------------------------------------------------------------------------
# Cảnh báo bất thường
# ---------------------------------------------------------------------------
@pytest.fixture
def clock(db) -> datetime:
    """Mốc «bây giờ» theo ĐỒNG HỒ CSDL — dòng đánh dấu do `record()` ghi cũng theo đồng hồ đó."""
    return anomaly.db_now(db)


def _run(db, clock):
    return anomaly.run_detection(db, now=clock)


def test_dang_nhap_ip_la_bao_mot_lan(db, cap_quyen, clock):
    admin = _admin_with_session_read(db, cap_quyen)
    user = _user(db, "nhanvien")
    _session(db, user.id, "27.64.1.1", clock - timedelta(days=3))       # IP quen
    fresh = _session(db, user.id, "103.9.9.9", clock - timedelta(minutes=5))  # IP lạ
    db.commit()

    first = _run(db, clock)
    assert first[anomaly.KIND_NEW_IP] == 1
    bells = _bells(db, admin.id)
    assert len(bells) == 1 and "103.9.9.9" in bells[0].title
    assert bells[0].link == anomaly.LINK_SESSIONS
    marker = _markers(db)
    assert len(marker) == 1 and marker[0].doc_code == f"new_ip:s:{fresh.id}"
    assert marker[0].entity_id == user.id and marker[0].created_by == 0
    #  Chính người đó không nhận chuông về việc mình vừa làm.
    assert _bells(db, user.id) == []

    second = _run(db, clock)
    assert second["alerted"] == 0 and len(_bells(db, admin.id)) == 1


def test_lan_dang_nhap_dau_tien_khong_bao(db, cap_quyen, clock):
    _admin_with_session_read(db, cap_quyen)
    user = _user(db, "nguoimoi")
    _session(db, user.id, "103.9.9.9", clock - timedelta(minutes=5))
    db.commit()

    assert _run(db, clock)[anomaly.KIND_NEW_IP] == 0
    assert _markers(db) == []


def test_ip_quen_khong_bao(db, cap_quyen, clock):
    _admin_with_session_read(db, cap_quyen)
    user = _user(db, "nhanvien")
    _session(db, user.id, "27.64.1.1", clock - timedelta(days=10))
    _session(db, user.id, "27.64.1.1", clock - timedelta(minutes=5))
    db.commit()

    assert _run(db, clock)["alerted"] == 0


def test_doi_thiet_bi_giua_phien(db, cap_quyen, clock):
    admin = _admin_with_session_read(db, cap_quyen)
    user = _user(db, "nhanvien")
    sess = _session(db, user.id, "27.64.1.1", clock - timedelta(hours=1))
    when = clock - timedelta(minutes=10)
    _request(db, when, user_id=user.id, session_id=sess.id, device_hash=b"\x01" * 8)
    _request(db, when, user_id=user.id, session_id=sess.id, device_hash=b"\x02" * 8)
    #  Phiên khác chỉ một dấu thiết bị — im.
    other = _session(db, user.id, "27.64.1.1", clock - timedelta(hours=1))
    _request(db, when, user_id=user.id, session_id=other.id, device_hash=b"\x03" * 8)
    _request(db, when, user_id=user.id, session_id=other.id, device_hash=b"\x03" * 8)
    db.commit()

    result = _run(db, clock)
    assert result[anomaly.KIND_DEVICE_CHANGED] == 1
    bells = _bells(db, admin.id)
    assert len(bells) == 1 and "2 thiết bị" in bells[0].title
    assert _markers(db)[0].doc_code == f"device:s:{sess.id}"
    assert _run(db, clock)["alerted"] == 0


def test_doi_ip_giua_phien_khong_bao_chuong(db, cap_quyen, clock):
    """Đổi wifi sang 4G là chuyện mỗi ngày — đã có `refresh_ip_changed` trong nhật ký."""
    _admin_with_session_read(db, cap_quyen)
    user = _user(db, "nhanvien")
    sess = _session(db, user.id, "27.64.1.1", clock - timedelta(hours=1), last_seen_ip="10.0.0.9")
    when = clock - timedelta(minutes=10)
    _request(db, when, user_id=user.id, session_id=sess.id, device_hash=b"\x01" * 8)
    db.commit()

    assert _run(db, clock)["alerted"] == 0


def test_xoa_hang_loat_trong_mot_luot_goi(db, cap_quyen, clock):
    admin = _admin_with_session_read(db, cap_quyen)
    user = _user(db, "nhanvien")
    when = clock - timedelta(minutes=3)
    big = uuid.uuid4().bytes
    for _ in range(ANOMALY_BULK_DELETE_MIN):
        _change(db, when, op=CHANGE_OP_DELETE, request_id=big, created_by=user.id)
    #  Lượt gọi khác xóa ít hơn ngưỡng — im.
    small = uuid.uuid4().bytes
    for _ in range(ANOMALY_BULK_DELETE_MIN - 1):
        _change(db, when, op=CHANGE_OP_DELETE, request_id=small, created_by=user.id)
    db.commit()

    result = _run(db, clock)
    assert result[anomaly.KIND_BULK_DELETE] == 1
    bells = _bells(db, admin.id)
    assert len(bells) == 1 and f"{ANOMALY_BULK_DELETE_MIN} dòng" in bells[0].title
    assert bells[0].link == f"{anomaly.LINK_LOGS}/{big.hex()}"
    assert _markers(db)[0].doc_code == f"bulk:{big.hex()}"[:anomaly.MAX_KEY]
    assert _run(db, clock)["alerted"] == 0


def test_xoa_hang_loat_lay_so_lon_hon_giua_hai_lop(db, cap_quyen, clock):
    """Lớp dấu vết đếm được nhiều hơn lớp thay đổi thì lấy số của lớp dấu vết."""
    admin = _admin_with_session_read(db, cap_quyen)
    user = _user(db, "nhanvien")
    when = clock - timedelta(minutes=3)
    rid = uuid.uuid4().bytes
    for _ in range(ANOMALY_BULK_DELETE_MIN):
        _change(db, when, op=CHANGE_OP_DELETE, request_id=rid, created_by=user.id)
    for _ in range(ANOMALY_BULK_DELETE_MIN + 5):
        _audit(db, when, action="delete", action_group=ACTION_GROUP_DELETE, request_id=rid,
               created_by=user.id)
    db.commit()

    _run(db, clock)
    assert f"{ANOMALY_BULK_DELETE_MIN + 5} dòng" in _bells(db, admin.id)[0].title


def test_don_dap_403_theo_nguoi(db, cap_quyen, clock):
    admin = _admin_with_session_read(db, cap_quyen)
    user = _user(db, "nhanvien")
    when = clock - timedelta(minutes=8)
    for _ in range(ANOMALY_FORBIDDEN_MIN):
        _request(db, when, user_id=user.id, ip="27.64.1.1", status=403)
    #  Người khác chỉ bị chặn vài lần — im.
    for _ in range(ANOMALY_FORBIDDEN_MIN - 1):
        _request(db, when, user_id=admin.id, ip="27.64.1.2", status=403)
    db.commit()

    result = _run(db, clock)
    assert result[anomaly.KIND_FORBIDDEN] == 1
    bells = _bells(db, admin.id)
    assert len(bells) == 1 and bells[0].link == anomaly.LINK_LOGS
    assert _markers(db)[0].doc_code == f"403:u:{user.id}"
    assert _run(db, clock)["alerted"] == 0


def test_don_dap_403_chua_dang_nhap_gom_theo_ip(db, cap_quyen, clock):
    admin = _admin_with_session_read(db, cap_quyen)
    when = clock - timedelta(minutes=8)
    for _ in range(ANOMALY_FORBIDDEN_MIN):
        _request(db, when, user_id=0, ip="45.33.1.1", status=403)
    db.commit()

    assert _run(db, clock)[anomaly.KIND_FORBIDDEN] == 1
    assert "chưa đăng nhập" in _bells(db, admin.id)[0].title
    assert _markers(db)[0].doc_code == "403:ip:45.33.1.1"


def test_ngoai_cua_so_khong_bao(db, cap_quyen, clock):
    _admin_with_session_read(db, cap_quyen)
    user = _user(db, "nhanvien")
    old = clock - timedelta(minutes=ANOMALY_WINDOW_MINUTES + 5)
    for _ in range(ANOMALY_FORBIDDEN_MIN):
        _request(db, old, user_id=user.id, ip="27.64.1.1", status=403)
    db.commit()

    assert _run(db, clock)["alerted"] == 0


def test_khong_ai_doc_phien_thi_lui_ve_admin(db, clock):
    """Không có ai giữ khóa `login_session` toàn hệ thì chuông rơi về vai trò `admin`."""
    from app.modules.role.model import Role
    from app.modules.user.model import UserRole

    role = Role(code="admin", name="Quản trị")
    db.add(role)
    db.flush()
    admin = _user(db, "admin")
    db.add(UserRole(user_id=admin.id, role_id=role.id))
    user = _user(db, "nhanvien")
    when = clock - timedelta(minutes=8)
    for _ in range(ANOMALY_FORBIDDEN_MIN):
        _request(db, when, user_id=user.id, ip="27.64.1.1", status=403)
    db.commit()

    assert anomaly.alert_recipients(db) == [admin.id]
    _run(db, clock)
    assert len(_bells(db, admin.id)) == 1
