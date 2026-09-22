"""bao-CR-461 — nhật ký của màn *Cấu hình hệ thống* phải nói rõ ĐỔI GÌ.

Trước CR này `save()` ghi đúng một câu "Cập nhật cấu hình hệ thống" cho mọi
lần bấm Lưu, kể cả lần không đổi gì. Mở nhật ký ra không ai biết ai đã tắt
gửi email hay đổi máy chủ SMTP — mà đó lại là hai thứ làm cả hệ thống ngừng
gửi thư.
"""
import time

import pytest

from app.core import app_settings
from app.modules.audit.model import AuditLog
from app.modules.setting import service
from app.modules.setting.model import Setting


@pytest.fixture(autouse=True)
def _settings_read_test_db(db, monkeypatch):
    """Bắt `app_settings` đọc từ DB của bài kiểm, và dọn bộ nhớ đệm quanh mỗi bài.

    `_load()` thật mở `SessionLocal` (MySQL) chứ không dùng phiên đang truyền
    vào, nên không thay thì "giá trị trước" lấy từ DB thật — bài kiểm vừa chạm
    hệ thật vừa xanh/đỏ theo cấu hình của máy đang chạy. Đệm 30 giây cũng phải
    dọn, không thì bài sau đọc trúng giá trị bài trước.
    """
    def load_from_test_db():
        app_settings._cache = {s.skey: s.svalue for s in db.query(Setting).all()}
        app_settings._exp = time.time() + app_settings._TTL

    monkeypatch.setattr(app_settings, "_load", load_from_test_db)
    app_settings.refresh()
    yield
    app_settings.refresh()


def _logs(db):
    return db.query(AuditLog).filter(AuditLog.entity == "setting").order_by(AuditLog.id).all()


def test_ghi_ro_gia_tri_truoc_va_sau(db):
    db.add(Setting(skey="smtp_host", svalue="smtp-relay.brevo.com"))
    db.commit()
    app_settings.refresh()

    service.save(db, {"smtp_host": "smtp.larksuite.com"}, user_id=7)

    logs = _logs(db)
    assert len(logs) == 1
    assert "smtp-relay.brevo.com -> smtp.larksuite.com" in logs[0].message
    assert logs[0].changed_fields == "smtp_host"
    assert logs[0].change_count == 1


def test_khong_doi_gi_thi_khong_de_dong_nhat_ky(db):
    db.add(Setting(skey="smtp_host", svalue="smtp-relay.brevo.com"))
    db.commit()
    app_settings.refresh()

    #  Màn hình gửi lại TOÀN BỘ ô mỗi lần bấm Lưu, nên "gửi y nguyên giá trị cũ"
    #  là đường đi thường gặp nhất, không phải ca hiếm.
    service.save(db, {"smtp_host": "smtp-relay.brevo.com"}, user_id=7)

    assert _logs(db) == []


def test_bool_ghi_thanh_bat_tat_chu_khong_phai_true_false(db):
    service.save(db, {"email_enabled": False}, user_id=7)
    #  Lần hai mới có cái để so: lần đầu giá trị cũ lấy từ `.env`.
    app_settings.refresh()
    service.save(db, {"email_enabled": True}, user_id=7)

    ket_qua = _logs(db)[-1].message
    assert "Tắt -> Bật" in ket_qua
    assert "true" not in ket_qua


def test_o_trong_noi_thanh_loi_chu_khong_de_khoang_trang(db):
    db.add(Setting(skey="email_test_override", svalue=""))
    db.commit()
    app_settings.refresh()

    service.save(db, {"email_test_override": "test@degoholding.vn"}, user_id=7)

    assert "(trống) -> test@degoholding.vn" in _logs(db)[0].message


def test_khoa_bi_mat_khong_bao_gio_ro_gia_tri(db):
    service.save(db, {"smtp_password": "quAPOmeJUvtjwT5L"}, user_id=7)

    logs = _logs(db)
    assert len(logs) == 1
    assert "quAPOmeJUvtjwT5L" not in logs[0].message
    assert "đã đặt giá trị mới" in logs[0].message
    assert logs[0].changed_fields == "smtp_password"


def test_khoa_bi_mat_de_trong_thi_khong_tinh_la_thay_doi(db):
    service.save(db, {"smtp_password": "   "}, user_id=7)

    assert _logs(db) == []
    assert db.query(Setting).filter(Setting.skey == "smtp_password").first() is None


def test_nhieu_o_cung_luc_dem_du_va_moi_o_mot_dong(db):
    for key, val in [("smtp_host", "cu.example.com"), ("smtp_port", "587")]:
        db.add(Setting(skey=key, svalue=val))
    db.commit()
    app_settings.refresh()

    service.save(db, {"smtp_host": "moi.example.com", "smtp_port": 465, "smtp_user": "a@b.vn"},
                 user_id=7)

    log = _logs(db)[0]
    assert log.change_count == 3
    #  Dòng đầu là câu tóm tắt, mỗi ô một dòng phía dưới — giao diện tách theo '\n'.
    assert len(log.message.split("\n")) == 4
    assert "587 -> 465" in log.message


def test_khoa_la_bi_bo_qua_khong_ghi_nhat_ky(db):
    service.save(db, {"khong_co_khoa_nay": "x"}, user_id=7)

    assert _logs(db) == []
    assert db.query(Setting).filter(Setting.skey == "khong_co_khoa_nay").first() is None


def test_gia_tri_moi_van_duoc_luu_xuong_bang(db):
    service.save(db, {"smtp_host": "moi.example.com"}, user_id=7)

    row = db.query(Setting).filter(Setting.skey == "smtp_host").first()
    assert row is not None and row.svalue == "moi.example.com"
    assert row.updated_by == 7 or row.created_by == 7


def test_danh_sach_khoa_khong_tran_cot_500_ky_tu(db):
    #  `changed_fields` là String(500); MySQL chặt chuỗi dài hơn thì 500 thật sự
    #  (SQLite của bộ test KHÔNG ép độ dài — nên phải kiểm chính giá trị).
    values = {f["key"]: "x" for f in service.FIELDS if f["type"] == "str"}
    service.save(db, values, user_id=7)

    assert len(_logs(db)[0].changed_fields) <= 500
