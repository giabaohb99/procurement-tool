"""bao-CR-727 — lưu nội dung thư + nút Gửi lại trên màn Nhật ký email (`POST /api/email-logs/{id}/resend`).

Chỗ dễ lủng:
- Nội dung phải được giữ ở chỗ nghẽn chung `send_smtp_email` VÀ lúc xếp thư, kể cả khi email đang tắt (thư bị tắt mới là
  thư người ta cần gửi lại nhất).
- Thư đặt lại mật khẩu / cấp tài khoản KHÔNG BAO GIỜ được lưu nội dung (chứa liên kết đặt mật khẩu) — yêu cầu bảo mật.
- Gửi lại sinh DÒNG MỚI (`resent_from_id`), giữ người nhận / tiêu đề / hộp thư danh nghĩa, dòng cũ không đổi, có audit.
- Bấm liên tục trong 60 giây → 429, kể cả bấm từ chính bản gửi lại.
- Thư cũ không có nội dung → 400 kèm câu "Thư gửi trước ngày ...".
- Chỉ `audit.read` thì không gửi lại được (403).
"""
from datetime import datetime, timedelta

import pytest

from app.modules.audit.model import AuditLog
from app.modules.notification import email_log_controller
from app.modules.notification import service as notification_service
from app.modules.notification.model import EmailLog, can_keep_body, is_secret_email_event
from app.modules.user.model import User
from hdld_factory import client_as  # noqa: F401

BODY = "<html><body><p>YCĐX DX001 đang chờ bạn duyệt</p></body></html>"


class _NonClosingSession:
    """`send_smtp_email` tự `close()` phiên của nó; bài kiểm chỉ có MỘT phiên SQLite trong bộ nhớ."""

    def __init__(self, db):
        self._db = db

    def __getattr__(self, name):
        return getattr(self._db, name)

    def close(self):
        pass


def _factory(db):
    return lambda: _NonClosingSession(db)


@pytest.fixture
def email_on(monkeypatch):
    from app.core import app_settings

    conf = {"email_enabled": True, "smtp_host": "smtp.he-thong.vn", "smtp_port": 587, "smtp_user": "erp@dego.vn",
            "smtp_from": "erp@dego.vn", "smtp_password": "mk", "email_test_override": ""}
    monkeypatch.setattr(app_settings, "get", lambda key: conf.get(key, ""))
    return conf


@pytest.fixture
def sent_calls(monkeypatch):
    """Thay đường gửi nền của API Gửi lại bằng bộ ghi — không mở `SessionLocal()` (MySQL thật)."""
    calls = []
    monkeypatch.setattr(notification_service, "send_smtp_email", lambda *a, **kw: calls.append(a))
    return calls


def _log(db, **kw):
    base = dict(event="dx_submitted", to_email="an@dego.vn", subject="YCĐX DX001 chờ duyệt", status="failed",
                error="SMTP 550", mailbox_id=None, from_email="")
    base.update(kw)
    row = EmailLog(**base)
    db.add(row)
    db.commit()
    return row


def _writer(world):
    world.grant("a1", "audit", "all", actions=("read", "write"))
    return world.actor("a1")


# ── Lưu nội dung ────────────────────────────────────────────────────────────────────────────────────────────────

def test_send_smtp_email_luu_noi_dung_ca_khi_email_dang_tat(db, monkeypatch):
    from app.core import app_settings

    monkeypatch.setattr(app_settings, "get", lambda key: {"email_enabled": False}.get(key, ""))
    row = _log(db, status="pending", error=None)
    notification_service.send_smtp_email(_factory(db), row.id, row.to_email, row.subject, BODY)
    db.refresh(row)
    assert row.status == "disabled" and row.html_body == BODY


def test_send_smtp_email_gui_xong_van_luu_noi_dung(db, email_on):
    row = _log(db, status="pending", error=None)
    notification_service.send_smtp_email(_factory(db), row.id, row.to_email, row.subject, BODY)
    db.refresh(row)
    assert row.status == "sent" and row.html_body == BODY


@pytest.mark.parametrize("event", ["password_reset", "account_creation", "password_reset_test"])
def test_thu_mat_khau_khong_bao_gio_luu_noi_dung(db, email_on, event):
    row = _log(db, event=event, status="pending", error=None)
    link_body = "<a href='https://erp/reset-password?token=bi-mat'>Đặt mật khẩu</a>"
    notification_service.send_smtp_email(_factory(db), row.id, row.to_email, row.subject, link_body, True)
    db.refresh(row)
    assert row.status == "sent" and row.html_body is None
    row.keep_body(link_body)
    assert row.html_body is None
    assert is_secret_email_event(event) and not can_keep_body(event, link_body)


def test_dat_lai_mat_khau_tu_luong_that_khong_ghi_noi_dung(db):
    class _Tasks:
        def __init__(self):
            self.jobs = []

        def add_task(self, fn, *args):
            self.jobs.append((fn, args))

    tasks = _Tasks()
    notification_service.send_password_reset_email(db, 1, tasks, "An", "an@dego.vn",
                                                   "https://erp/reset-password?token=bi-mat")
    row = db.query(EmailLog).filter(EmailLog.event == "password_reset").one()
    assert row.html_body is None
    #  Chạy đúng tác vụ nền mà luồng thật xếp (thay nhà máy phiên): vẫn không lưu.
    fn, args = tasks.jobs[0]
    fn(_factory(db), *args[1:])
    db.refresh(row)
    assert row.html_body is None


def test_xep_thu_theo_mau_luu_noi_dung_ngay_luc_xep(db):
    from app.modules.notification.email_queue import queue_event_email

    user = User(email="duyet@dego.vn", password_hash="x", is_active=True)
    db.add(user)
    db.commit()
    assert queue_event_email(db, "dx_submitted", [user], {"actor_id": 0}) == 1
    row = db.query(EmailLog).filter(EmailLog.to_email == "duyet@dego.vn").one()
    assert row.status == "pending" and row.html_body          # worker chưa nhặt mà đã gửi lại được
    db.rollback()


def test_thu_qua_to_khong_luu():
    assert not can_keep_body("dx_submitted", "x" * 1_000_001)
    assert can_keep_body("dx_submitted", "x" * 10)


# ── API danh sách / chi tiết ────────────────────────────────────────────────────────────────────────────────────

def test_danh_sach_tra_co_gui_lai_va_ly_do(world, client_as):  # noqa: F811
    old = _log(world.db, created_at=datetime(2026, 10, 1, 8, 0))
    secret = _log(world.db, event="password_reset", created_at=datetime(2026, 11, 4, 8, 0))
    fresh = _log(world.db, html_body=BODY, created_at=datetime(2026, 11, 4, 9, 0))
    c = client_as(_writer(world))
    items = {r["id"]: r for r in c.get("/api/email-logs").json()["data"]["items"]}
    assert "html_body" not in items[fresh.id]
    assert items[fresh.id]["can_resend"] is True and items[fresh.id]["has_body"] is True
    assert items[old.id]["can_resend"] is False
    assert items[old.id]["resend_block_reason"] == \
        "Thư gửi trước ngày 04/11/2026 không lưu nội dung nên không gửi lại được."
    assert items[secret.id]["can_resend"] is False and "mật khẩu" in items[secret.id]["resend_block_reason"]
    detail = c.get(f"/api/email-logs/{old.id}").json()["data"]
    assert detail["resend_block_reason"].startswith("Thư gửi trước ngày 04/11/2026")


# ── API gửi lại ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_gui_lai_tao_dong_moi_giu_nguyen_dong_cu_va_ghi_audit(world, client_as, sent_calls):  # noqa: F811
    row = _log(world.db, html_body=BODY, mailbox_id=5, from_email="hr@dego.vn", event="workflow_purchase_request")
    actor = _writer(world)
    c = client_as(actor)
    res = c.post(f"/api/email-logs/{row.id}/resend")
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["id"] != row.id and data["resent_from_id"] == row.id and data["status"] == "pending"
    new = world.db.get(EmailLog, data["id"])
    assert (new.to_email, new.subject, new.mailbox_id, new.html_body, new.event) == \
        (row.to_email, row.subject, 5, BODY, "workflow_purchase_request")
    assert new.created_by == actor.user.id
    world.db.refresh(row)
    assert row.status == "failed" and row.error == "SMTP 550"          # dòng cũ giữ nguyên
    #  Đi đúng đường gửi chung, với cờ của thư luồng duyệt (force, không override).
    assert len(sent_calls) == 1
    _factory_arg, log_id, to_email, subject, body, force, apply_override = sent_calls[0]
    assert (log_id, to_email, subject, body, force, apply_override) == \
        (new.id, "an@dego.vn", row.subject, BODY, True, False)
    audit = world.db.query(AuditLog).filter(AuditLog.entity == "email_log", AuditLog.action == "resend").one()
    assert audit.entity_id == new.id and f"#{row.id}" in audit.message
    #  Danh sách nhận ra dòng gửi lại.
    listed = {r["id"]: r for r in c.get("/api/email-logs").json()["data"]["items"]}
    assert listed[new.id]["resent_from_id"] == row.id


def test_thu_thuong_gui_lai_ton_trong_cong_tac_email(world, client_as, sent_calls):  # noqa: F811
    row = _log(world.db, html_body=BODY, event="document_issued")
    c = client_as(_writer(world))
    assert c.post(f"/api/email-logs/{row.id}/resend").status_code == 200
    assert sent_calls[0][5:] == (False, True)


def test_bam_lien_tuc_trong_60_giay_bi_chan(world, client_as, sent_calls):  # noqa: F811
    row = _log(world.db, html_body=BODY)
    c = client_as(_writer(world))
    first = c.post(f"/api/email-logs/{row.id}/resend")
    assert first.status_code == 200
    again = c.post(f"/api/email-logs/{row.id}/resend")
    assert again.status_code == 429 and "60 giây" in again.text
    #  Bấm từ chính bản gửi lại vừa sinh cũng bị chặn.
    new_id = first.json()["data"]["id"]
    assert c.post(f"/api/email-logs/{new_id}/resend").status_code == 429
    assert len(sent_calls) == 1
    #  Quá 60 giây thì gửi lại được.
    world.db.query(EmailLog).filter(EmailLog.id == new_id).update(
        {EmailLog.created_at: datetime.now() - timedelta(seconds=61)})
    world.db.commit()
    assert c.post(f"/api/email-logs/{row.id}/resend").status_code == 200
    assert len(sent_calls) == 2


def test_khong_gui_lai_thu_cu_va_thu_mat_khau(world, client_as, sent_calls):  # noqa: F811
    _log(world.db, html_body=BODY, created_at=datetime(2026, 11, 4, 9, 0))
    old = _log(world.db, created_at=datetime(2026, 10, 1, 8, 0))
    secret = _log(world.db, event="password_reset", html_body=None)
    c = client_as(_writer(world))
    res = c.post(f"/api/email-logs/{old.id}/resend")
    assert res.status_code == 400 and "Thư gửi trước ngày 04/11/2026" in res.text
    res = c.post(f"/api/email-logs/{secret.id}/resend")
    assert res.status_code == 400 and "mật khẩu" in res.text
    #  Dòng mật khẩu lỡ có nội dung (dữ liệu tay) vẫn không gửi lại.
    secret.html_body = BODY
    world.db.commit()
    assert c.post(f"/api/email-logs/{secret.id}/resend").status_code == 400
    assert c.post("/api/email-logs/999999/resend").status_code == 404
    assert sent_calls == []


def test_chi_quyen_doc_thi_khong_gui_lai_duoc(world, client_as, sent_calls):  # noqa: F811
    row = _log(world.db, html_body=BODY)
    world.grant("a1", "audit", "all", actions=("read",))
    c = client_as(world.actor("a1"))
    assert c.get(f"/api/email-logs/{row.id}").status_code == 200
    assert c.post(f"/api/email-logs/{row.id}/resend").status_code == 403
    assert world.db.query(EmailLog).count() == 1 and sent_calls == []


def test_co_gui_lai_theo_loai_thu():
    assert email_log_controller._send_flags("workflow_payment_request") == (True, False)
    assert email_log_controller._send_flags("dx_submitted_test") == (True, True)
    assert email_log_controller._send_flags("dd_completed") == (False, True)
