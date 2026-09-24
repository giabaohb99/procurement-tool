"""Cụm Trợ lý AI dời từ `.env` sang bảng cấu hình — bao-CR-429, nhịp 2.

Khóa API của Claude và Gemini là thứ người dùng tự đăng ký lấy về. Để chúng ở
`.env` nghĩa là mỗi lần đổi key phải có người mở SSH vào máy chủ — chặn đúng
người đáng ra tự làm được, và đổi key là việc xảy ra thường xuyên (lộ key, hết
hạn thẻ, đổi tài khoản).

Dời xong thì mọc ra ba chỗ dễ hỏng, ba chỗ ấy là nội dung của tệp này:
bảng cấu hình giờ CHỨA bí mật nên cửa đọc công khai tuyệt đối không được lộ;
`default_model` từng là thuộc tính lớp nên nó chốt giá trị lúc import, đổi trên
màn hình sẽ không ăn thua; và cửa PUT nhận `dict` tự do nên trần chi phí gõ sai
sẽ lặng lẽ thành `0` — mà `0` ở ô đó nghĩa là KHÔNG GIỚI HẠN.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core import app_settings
from app.modules.assistant.provider.claude import ClaudeProvider
from app.modules.assistant.provider.gemini import GeminiProvider
from app.modules.setting import service


@pytest.fixture
def cfg(db, monkeypatch):
    """`app_settings` đọc DB qua `SessionLocal` — trỏ nó vào DB của test.

    Cache của nó là biến toàn cục, nên phải dọn CẢ hai đầu: không dọn đầu vào
    thì bài này ăn giá trị bài khác để lại, không dọn đầu ra thì bài này đầu độc
    bài sau.
    """
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)
    app_settings.refresh()
    yield
    app_settings.refresh()


# ---------------------------------------------------------------------------
# Khai báo màn hình phải khớp lớp cấu hình
# ---------------------------------------------------------------------------
def test_moi_o_tren_man_hinh_deu_da_dang_ky():
    """Khai ô trên màn hình mà quên đăng ký thì lưu xong KHÔNG có tác dụng.

    Lỗi này im lặng hoàn toàn: ô vẫn hiện, bấm Lưu vẫn báo thành công, giá trị
    vẫn nằm dưới DB — chỉ là không ai đọc tới nó, `app_settings.get()` vẫn trả
    giá trị `.env` cũ.
    """
    for f in service.FIELDS:
        assert f["key"] in app_settings.REGISTRY, f"ô {f['key']} chưa đăng ký ở REGISTRY"
    for s in service.SECRET_FIELDS:
        assert s["key"] in app_settings.SECRETS, f"ô bí mật {s['key']} chưa đăng ký ở SECRETS"


def test_kieu_khai_tren_man_hinh_khop_kieu_o_lop_cau_hinh():
    """Lệch kiểu thì ô số hiện thành ô chữ, hoặc công tắc lưu ra chuỗi rỗng."""
    for f in service.FIELDS:
        khai = f.get("type", "str")
        thuc = app_settings.REGISTRY[f["key"]][0]
        #  `select` là chuyện của giao diện (vẽ ô chọn), dưới DB vẫn là chuỗi.
        assert (thuc if khai != "select" else "str") == thuc
        assert khai in ("str", "int", "bool", "select")


def test_bon_khoa_rag_co_y_o_lai_env():
    """Chốt NGƯỢC: canh người sau dời nốt cho "đủ bộ".

    Đổi model nhúng hay số chiều vector là mọi vector đã nhúng thành vô nghĩa và
    phải dựng lại cả kho — một ô nhập trên màn hình không nói được cái giá đó.
    Còn `QDRANT_URL` và cờ bật RAG gắn với việc container `qdrant` có chạy hay
    không, tức chuyện của người dựng máy.
    """
    for khoa in ("ai_embed_model", "ai_embed_dim", "qdrant_url", "ai_rag_enabled"):
        assert khoa not in app_settings.REGISTRY


def test_o_dan_link_thi_link_phai_ra_ngoai_va_an_toan():
    """`doc_url` là thứ người dùng sẽ bấm vào — không để lọt đường dẫn rác."""
    for f in list(service.FIELDS) + list(service.SECRET_FIELDS):
        url = f.get("doc_url")
        if url is not None:
            assert url.startswith("https://"), f"{f['key']} có doc_url không phải https"


# ---------------------------------------------------------------------------
# Bảng cấu hình nay CHỨA bí mật — cửa đọc không được lộ
# ---------------------------------------------------------------------------
def test_cua_doc_khong_tra_ve_khoa_api_duoi_bat_ky_dang_nao(db, cfg):
    """Bài kiểm quan trọng nhất của cả nhịp này.

    `get_all()` là thứ trả về cho trình duyệt. Nó gắn `value` cho ô thường và chỉ
    gắn `configured` cho ô bí mật — nhưng đó là hai vòng lặp riêng, và ngày ai đó
    gộp lại cho gọn thì khóa API đi thẳng ra cửa công khai. Quét cả cây trả về,
    tìm cả bản gốc lẫn bản mã.
    """
    khoa_that = "sk-ant-khoa-that-khong-duoc-lo"
    service.save(db, {"anthropic_api_key": khoa_that}, user_id=7)

    ket_qua = repr(service.get_all())
    assert khoa_that not in ket_qua
    ban_ma = db.execute(
        text("SELECT svalue FROM tab_setting WHERE skey='anthropic_api_key'")
    ).scalar()
    assert ban_ma and ban_ma not in ket_qua

    o = next(s for s in service.get_all()["secrets"] if s["key"] == "anthropic_api_key")
    assert o["configured"] is True
    assert "value" not in o


def test_dan_key_tren_man_hinh_thi_nha_cung_cap_dung_duoc_ngay(db, cfg):
    """Cả đường đi: ô nhập -> mã hóa -> giải mã -> adapter báo đã cấu hình."""
    service.save(db, {"gemini_api_key": "AIza-khoa-nguoi-dung-tu-dan"}, user_id=7)

    assert app_settings.get("gemini_api_key") == "AIza-khoa-nguoi-dung-tu-dan"
    assert GeminiProvider().is_configured() is True


# ---------------------------------------------------------------------------
# `default_model` phải đọc lúc CHẠY, không phải lúc import
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nha, khoa, model_moi", [
    (ClaudeProvider, "ai_claude_model", "claude-opus-5"),
    (GeminiProvider, "ai_gemini_model", "gemini-3.5-flash-lite"),
])
def test_doi_model_tren_man_hinh_thi_an_ngay(db, cfg, nha, khoa, model_moi):
    """Bản cũ khai `default_model` là thuộc tính LỚP, tức chốt giá trị lúc import.

    Nguồn nay là bảng cấu hình, nên nếu vẫn là thuộc tính lớp thì hai chuyện xảy
    ra: module chạm DB ngay lúc import, và người dùng đổi model trên màn hình
    sẽ không thấy gì đổi cho tới lần khởi động lại — không có thông báo nào.
    """
    service.save(db, {khoa: model_moi}, user_id=7)
    assert nha().default_model == model_moi


def test_de_trong_model_thi_ve_mac_dinh_chu_khong_ve_rong(db, cfg):
    """Chuỗi rỗng đi thẳng vào tên model là request trả 400 khó hiểu."""
    service.save(db, {"ai_claude_model": ""}, user_id=7)
    assert ClaudeProvider().default_model == "claude-sonnet-5"


# ---------------------------------------------------------------------------
# Chặn giá trị hỏng ở cửa vào
# ---------------------------------------------------------------------------
def test_tran_cau_hoi_go_sai_thi_chan_chu_khong_thanh_khong_gioi_han(db, cfg):
    """`0` ở ô này MANG NGHĨA "không giới hạn", nên nuốt lỗi là mở toang chi phí."""
    with pytest.raises(HTTPException) as e:
        service.save(db, {"ai_daily_msg_limit": "50 câu"}, user_id=7)
    assert e.value.status_code == 400
    assert app_settings.get("ai_daily_msg_limit") != 0


def test_tran_cau_hoi_dung_thi_luu_va_doc_lai_ra_so(db, cfg):
    service.save(db, {"ai_daily_msg_limit": "120"}, user_id=7)
    assert app_settings.get("ai_daily_msg_limit") == 120


def test_o_so_de_trong_thi_ve_lai_env_chu_khong_chan_ca_lan_luu(db, cfg):
    """Màn hình gửi lại MỌI ô mỗi lần bấm Lưu.

    Ô trống mà coi là giá trị hỏng thì người dùng sửa một ô email cũng không lưu
    nổi, chỉ vì ở tab khác có một ô số họ chưa từng đụng tới.
    """
    service.save(db, {"ai_daily_msg_limit": "", "ai_default_provider": ""}, user_id=7)
    assert app_settings.get("ai_daily_msg_limit") == 50  # giá trị dự phòng ở .env


def test_nha_cung_cap_ngoai_danh_sach_thi_chan(db, cfg):
    """Cửa PUT nhận `dict` tự do; gõ sai tên nhà thì trợ lý im lặng rơi sang nhà khác."""
    with pytest.raises(HTTPException) as e:
        service.save(db, {"ai_default_provider": "chatgpt"}, user_id=7)
    assert e.value.status_code == 400


def test_cong_tac_nhan_chu_la_thi_chan(db, cfg):
    """Không chặn thì `_cast` đọc chữ lạ thành `False` — tắt trợ lý trong im lặng."""
    with pytest.raises(HTTPException):
        service.save(db, {"ai_enabled": "bật"}, user_id=7)


def test_cong_tac_nhan_dung_bool_lan_chuoi_quen_thuoc(db, cfg):
    service.save(db, {"ai_enabled": True}, user_id=7)
    assert app_settings.get("ai_enabled") is True
    service.save(db, {"ai_enabled": "false"}, user_id=7)
    assert app_settings.get("ai_enabled") is False
