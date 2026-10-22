"""bao-CR-655 — hai lỗ bảo mật trong sổ BM:

* BM-023: giải mã bí mật hỏng không được im lặng — vẫn trả "" nhưng ghi lỗi `app.secrets`
  (chỉ tên khóa, không lộ giá trị), mỗi khóa một lần.
* BM-021: `/api/uploads` (StaticFiles, không hỏi đăng nhập) chỉ được gắn khi DEV_MODE.
"""
import logging

from app.core import app_settings
from app.core.config import settings


def test_giai_ma_rong_tra_rong_khong_bao_loi(caplog):
    with caplog.at_level(logging.ERROR, logger="app.secrets"):
        assert app_settings._decrypt("") == ""
    assert not caplog.records


def test_giai_ma_dung_tra_lai_gia_tri():
    token = app_settings.encrypt("gia-tri-bi-mat")
    assert app_settings._decrypt(token, "r2_secret_access_key") == "gia-tri-bi-mat"


def test_giai_ma_hong_bao_loi_mot_lan_chi_ten_khoa(caplog):
    app_settings._decrypt_failed.discard("khoa_thu_bm023")
    with caplog.at_level(logging.ERROR, logger="app.secrets"):
        assert app_settings._decrypt("khong-phai-fernet", "khoa_thu_bm023") == ""
        assert app_settings._decrypt("khong-phai-fernet", "khoa_thu_bm023") == ""
    hits = [r for r in caplog.records if "khoa_thu_bm023" in r.getMessage()]
    assert len(hits) == 1
    assert "khong-phai-fernet" not in hits[0].getMessage()
    assert "khoa_thu_bm023" in app_settings.decrypt_failures()


def test_uploads_cong_khai_chi_gan_khi_dev_mode():
    from app.main import app

    mounted = any(getattr(r, "name", "") == "uploads" for r in app.routes)
    assert mounted == bool(settings.DEV_MODE)
