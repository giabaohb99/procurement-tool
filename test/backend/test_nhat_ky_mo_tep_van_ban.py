"""NHẬT KÝ MỞ / TẢI TỆP ĐÍNH KÈM + cảnh báo bất thường (24/08/2026).

Không chặn được người xem chụp màn hình, nên thứ thay thế là **biết ai mở cái gì
lúc nào**, và báo ngay khi một người mở dồn dập.

Bốn chỗ dễ sai mà bài kiểm này canh:
  * ghi đúng một dòng cho mỗi lượt, treo vào CHÍNH văn bản;
  * chỉ báo khi VƯỢT ngưỡng, không báo sớm;
  * **không báo lại** trong cùng cửa sổ — báo mỗi lượt thì người nhận tắt chuông,
    và lần sau có chuyện thật thì không ai nhìn nữa;
  * người đang thao tác **không tự nhận** cảnh báo về chính mình.
"""
from types import SimpleNamespace

import pytest

from app.core import app_settings
from app.modules.audit.model import AuditLog
from app.modules.document import file_access_log as nk
from app.modules.document.model import Document
from app.modules.notification.model import Notification

NGUOI_MO = 7
QUAN_TRI = 8


@pytest.fixture()
def doc(db):
    obj = Document(id=500, title="Bảng lương kỳ 8", doc_code="01/2026/BL-DEGO")
    return obj


@pytest.fixture()
def cau_hinh(monkeypatch):
    """Ngưỡng 3 lượt / 10 phút — đủ nhỏ để bài kiểm chạy nhanh."""
    value = {"doc_file_alert_threshold": 3, "doc_file_alert_window_min": 10,
               "doc_file_alert_recipients": ""}
    monkeypatch.setattr(app_settings, "get", lambda key: value.get(key))
    monkeypatch.setattr(nk, "setting", lambda key: value.get(key))
    return value


@pytest.fixture()
def recipients(monkeypatch):
    """Cắt phần dò người nhận — nó phụ thuộc vai trò/quyền, đã có bài kiểm riêng."""
    monkeypatch.setattr(nk, "alert_recipients", lambda db: [QUAN_TRI, NGUOI_MO])


def _mo(db, doc, lan: int):
    for _ in range(lan):
        nk.log_and_alert(db, doc, SimpleNamespace(id=NGUOI_MO), nk.ACTION_VIEW, "luong.pdf")


def _dem(db, action: str) -> int:
    return db.query(AuditLog).filter(AuditLog.action == action).count()


def test_moi_luot_ghi_mot_dong_tren_chinh_van_ban(db, doc, cau_hinh, recipients):
    _mo(db, doc, 2)

    dong = db.query(AuditLog).filter(AuditLog.action == nk.ACTION_VIEW).all()
    assert len(dong) == 2
    assert all(d.entity == "document" and d.entity_id == doc.id for d in dong)
    assert "luong.pdf" in dong[0].message


def test_chua_toi_nguong_thi_khong_bao(db, doc, cau_hinh, recipients):
    _mo(db, doc, 2)  # ngưỡng là 3

    assert db.query(Notification).count() == 0
    assert _dem(db, nk.ACTION_ALERT) == 0


def test_toi_nguong_thi_bao(db, doc, cau_hinh, recipients):
    _mo(db, doc, 3)

    assert _dem(db, nk.ACTION_ALERT) == 1
    tin = db.query(Notification).all()
    #  Chỉ quản trị nhận; người đang thao tác thì không.
    assert [t.user_id for t in tin] == [QUAN_TRI]
    assert "3" in tin[0].title
    assert tin[0].link == f"/document/documents/{doc.id}"


def test_khong_bao_lai_trong_cung_cua_so(db, doc, cau_hinh, recipients):
    """Báo mỗi lượt thì người nhận tắt chuông — lần sau có chuyện thật không ai nhìn."""
    _mo(db, doc, 6)  # vượt ngưỡng gấp đôi

    assert _dem(db, nk.ACTION_ALERT) == 1
    assert db.query(Notification).count() == 1


def test_nguong_0_la_tat_han_canh_bao_nhung_van_ghi(db, doc, monkeypatch, recipients):
    monkeypatch.setattr(nk, "setting", lambda key: 0 if key == "doc_file_alert_threshold" else None)

    _mo(db, doc, 5)

    assert _dem(db, nk.ACTION_VIEW) == 5, "tắt cảnh báo KHÔNG được tắt nhật ký"
    assert db.query(Notification).count() == 0


def test_dong_danh_dau_da_bao_treo_theo_NGUOI_khong_theo_van_ban(db, doc, cau_hinh, recipients):
    """Một người mở dồn dập trên NHIỀU văn bản khác nhau vẫn chỉ bị báo một lần.

    Nếu dòng đánh dấu treo theo văn bản thì mở 3 tệp ở 5 văn bản = 5 lần báo.
    """
    _mo(db, doc, 3)
    doc_khac = Document(id=501, title="Hồ sơ thầu", doc_code="02/2026/HS-DEGO")
    _mo(db, doc_khac, 3)

    assert _dem(db, nk.ACTION_ALERT) == 1
    dau = db.query(AuditLog).filter(AuditLog.action == nk.ACTION_ALERT).first()
    assert dau.entity_id == NGUOI_MO
