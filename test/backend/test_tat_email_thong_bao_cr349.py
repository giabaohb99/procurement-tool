"""Công tắc "Nhận email thông báo" theo TỪNG NGƯỜI (bao-CR-349, ticket 37 prod).

Trước đây email luồng duyệt chỉ có một công tắc TOÀN HỆ (`EMAIL_WORKFLOW_ENABLED`), nên
một người xin ngưng nhận thư là phải tắt cho cả 28 người. Nay mỗi tài khoản có cột
`tab_user.notify_email`.

Ba ranh giới phải giữ, mỗi cái một bài kiểm:

* tắt thư của người này KHÔNG được ảnh hưởng người khác trong cùng lượt gửi;
* tắt email KHÔNG phải tắt thông báo — chuông trong app vẫn ghi đủ;
* tắt email KHÔNG đụng tới thư đặt lại mật khẩu / cấp tài khoản, vì đó là đường vào hệ thống.
"""
import pytest

from app.core.config import settings
from app.modules.notification import service as noti
from app.modules.notification.model import EmailLog
from app.modules.user.model import User


class _BackgroundTasks:
    """Thay `fastapi.BackgroundTasks`: chỉ ghi lại lời gọi, KHÔNG mở SMTP thật."""

    def __init__(self):
        self.tasks = []

    def add_task(self, fn, *args, **kwargs):
        self.tasks.append((fn, args, kwargs))


@pytest.fixture
def bat_email_luong_duyet():
    """Bật công tắc toàn hệ trong phạm vi một bài kiểm rồi trả về giá trị cũ."""
    cu = getattr(settings, "EMAIL_WORKFLOW_ENABLED", False)
    settings.EMAIL_WORKFLOW_ENABLED = True
    yield
    settings.EMAIL_WORKFLOW_ENABLED = cu


def _nguoi_dung(db, email: str, notify_email: bool = True) -> User:
    u = User(email=email, password_hash="x", is_active=True, notify_email=notify_email)
    db.add(u)
    db.commit()
    return u


def _gui(db, recipients, background_tasks=None):
    noti._send_workflow_emails(
        db, background_tasks or _BackgroundTasks(), recipients,
        subject="YCMH PR001 chờ duyệt", body="Có yêu cầu mua hàng chờ bạn duyệt",
        doc_type="purchase_request", doc_code="PR001", creator_name="Nguyễn Văn A",
        reason="", approve_note="", is_urgent=False, link="/purchase-requests/1",
    )


def test_tai_khoan_moi_mac_dinh_van_nhan_email(db):
    """Mặc định của cột là BẬT — thêm công tắc không được làm ai đó lặng lẽ mất thư."""
    u = _nguoi_dung(db, "moi@x.vn")
    assert u.notify_email is True


def test_nguoi_tat_thi_khong_gui_va_khong_ghi_log(db, bat_email_luong_duyet):
    """Tắt là bỏ hẳn: không thư, và cũng KHÔNG có dòng EmailLog nào mang tên họ.

    Cố ý không ghi log — có dòng log là có người đi tra "sao gửi rồi mà không tới"."""
    tat = _nguoi_dung(db, "khongnhan@x.vn", notify_email=False)
    _gui(db, [tat])
    assert db.query(EmailLog).filter(EmailLog.created_by == tat.id).count() == 0


def test_tat_cua_nguoi_nay_khong_anh_huong_nguoi_kia(db, bat_email_luong_duyet):
    """Cùng một lượt gửi: người còn bật vẫn nhận đủ."""
    tat = _nguoi_dung(db, "khongnhan@x.vn", notify_email=False)
    bat = _nguoi_dung(db, "vannhan@x.vn")
    bt = _BackgroundTasks()
    _gui(db, [tat, bat], bt)

    logs = db.query(EmailLog).all()
    assert [lg.to_email for lg in logs] == ["vannhan@x.vn"]
    assert len(bt.tasks) == 1


def test_cong_tac_toan_he_tat_thi_khong_ai_nhan(db):
    """Hành vi cũ giữ nguyên: `EMAIL_WORKFLOW_ENABLED=false` chặn trước, không xét từng người."""
    cu = getattr(settings, "EMAIL_WORKFLOW_ENABLED", False)
    settings.EMAIL_WORKFLOW_ENABLED = False
    try:
        bat = _nguoi_dung(db, "vannhan@x.vn")
        bt = _BackgroundTasks()
        _gui(db, [bat], bt)
        assert db.query(EmailLog).count() == 0
        assert bt.tasks == []
    finally:
        settings.EMAIL_WORKFLOW_ENABLED = cu


def test_tat_email_van_con_chuong_trong_app(db, bat_email_luong_duyet):
    """Tắt EMAIL không phải tắt THÔNG BÁO: `trigger_notification` vẫn ghi chuông cho họ."""
    from app.modules.notification.model import Notification
    tat = _nguoi_dung(db, "khongnhan@x.vn", notify_email=False)
    noti.trigger_notification(
        db, event="submit", doc_type="purchase_request", doc_code="PR001",
        creator_id=0, background_tasks=_BackgroundTasks(),
        link="/purchase-requests/1", recipient_ids=[tat.id],
    )
    assert db.query(Notification).filter(Notification.user_id == tat.id).count() == 1
    assert db.query(EmailLog).filter(EmailLog.created_by == tat.id).count() == 0


def test_thu_dat_lai_mat_khau_khong_bi_chan(db):
    """Đường vào hệ thống không đi qua công tắc này — tắt rồi vẫn quên mật khẩu được."""
    tat = _nguoi_dung(db, "khongnhan@x.vn", notify_email=False)
    bt = _BackgroundTasks()
    noti.send_password_reset_email(db, tat.id, bt, "Người Dùng", tat.email, "/reset?token=abc")

    logs = db.query(EmailLog).filter(EmailLog.event == "password_reset").all()
    assert [lg.to_email for lg in logs] == ["khongnhan@x.vn"]
    assert len(bt.tasks) == 1


def test_thu_cap_tai_khoan_khong_bi_chan(db):
    """Cùng lý do: người chưa đăng nhập lần nào thì chưa có cách nào bật lại."""
    tat = _nguoi_dung(db, "khongnhan@x.vn", notify_email=False)
    bt = _BackgroundTasks()
    noti.send_account_creation_email(db, tat.id, bt, "Người Dùng", tat.email, "/login")

    logs = db.query(EmailLog).filter(EmailLog.event == "account_creation").all()
    assert [lg.to_email for lg in logs] == ["khongnhan@x.vn"]


def test_quan_tri_tat_ho_va_bat_lai(db):
    """Cửa quản trị: `set_notify_email` đổi được hai chiều và ghi người sửa."""
    from app.modules.user import service as user_service
    u = _nguoi_dung(db, "ngan@x.vn")

    user_service.set_notify_email(db, u.id, False, actor_id=9)
    db.refresh(u)
    assert u.notify_email is False and u.updated_by == 9

    user_service.set_notify_email(db, u.id, True, actor_id=9)
    db.refresh(u)
    assert u.notify_email is True


def test_tat_cho_tai_khoan_khong_ton_tai_thi_bao_404(db):
    from fastapi import HTTPException
    from app.modules.user import service as user_service
    with pytest.raises(HTTPException) as e:
        user_service.set_notify_email(db, 999999, False, actor_id=9)
    assert e.value.status_code == 404
