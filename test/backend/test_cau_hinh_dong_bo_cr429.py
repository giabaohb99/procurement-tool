"""Cụm đồng bộ dời từ `.env` sang bảng cấu hình — bao-CR-429, nhịp 3.

Lý do dời đúng CỤM NÀY trước các cụm khác: khi đường máy-gọi-máy giữa ERP và một
hệ ngoài trục trặc, thứ phải làm ngay là TẮT nó. Mà tắt bằng `.env` nghĩa là mở
SSH vào máy chủ, sửa tệp, dựng lại dịch vụ — trong lúc phiếu hỏng vẫn đang chảy
vào. Sửa trên màn hình thì cầu dao hạ trong vài giây.

Dời xong mọc ra bốn chỗ dễ hỏng, bốn chỗ ấy là nội dung của tệp này:

1. Lớp tiếp hợp `SyncSource` lưu TÊN khóa chứ không lưu giá trị — đọc lúc chạy.
   Chụp giá trị lúc nạp module thì cầu dao trên màn hình thành nút giả.
2. Bảng cấu hình nay giữ thêm ba bí mật nữa (mã ký chung, khóa Firebase, mật
   khẩu POS365). Cửa đọc công khai tuyệt đối không được lộ chúng.
3. Vài con số vừa dời vốn mang nghĩa "giữ lại bao nhiêu" — ô rỗng hoặc số 0 đi
   thẳng xuống là XÓA SẠCH, nên phải có sàn.
4. Có những khóa CỐ Ý ở lại `.env`; chốt ngược canh người sau dời nốt cho đủ bộ.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core import app_settings, legacy_files
from app.modules.backup import service as backup_service
from app.modules.coffee_point.pos365_client import Pos365Client
from app.modules.legacy_datxe import firebase
from app.modules.notification.model import Notification
from app.modules.setting import service
from app.modules.sync_log.registry import SOURCE_DATXE, SOURCE_POS365, require_source


@pytest.fixture
def cfg(db, monkeypatch):
    """`app_settings` đọc DB qua `SessionLocal` — trỏ nó vào DB của test.

    Cache của nó là biến toàn cục, nên phải dọn CẢ hai đầu: không dọn đầu vào thì
    bài này ăn giá trị bài khác để lại, không dọn đầu ra thì bài này đầu độc bài
    sau.
    """
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)
    app_settings.refresh()
    yield Session
    app_settings.refresh()


@pytest.fixture
def env_trong(monkeypatch):
    """Xóa TẦNG DƯỚI — tức `.env` — cho cụm đồng bộ.

    Máy của người đang chạy bài kiểm thường đã có sẵn địa chỉ app cũ và khóa
    Firebase trong `.env` (di sản của đợt nạp dữ liệu cũ). Bài nào muốn khẳng
    định «không cấu hình» mà không dọn tầng dưới thì kết quả phụ thuộc vào máy:
    xanh trên máy này, đỏ trên máy khác, và người sau sẽ đi sửa nhầm mã nguồn.
    """
    for bien in ("SYNC_LEGACY_API_BASE", "SYNC_SHARED_SECRET",
                 "LEGACY_FIREBASE_DB_URL", "LEGACY_FIREBASE_SECRET"):
        monkeypatch.setattr(app_settings._env, bien, "", raising=False)
    app_settings.refresh()


# ---------------------------------------------------------------------------
# 0. Ba trường hợp của luật «bảng trước, `.env` sau»
# ---------------------------------------------------------------------------
def test_bang_cau_hinh_thang_env_khi_ca_hai_cung_co(db, cfg, monkeypatch):
    """Luật đại ca chốt: cả hai cùng có thì TIN Ở BẢNG.

    Ngược lại thì việc dời cụm này ra màn hình thành công cốc — người dùng sửa
    trên màn hình, hệ thống vẫn chạy bằng giá trị cũ trong tệp môi trường, và
    không chỗ nào nói cho họ biết.
    """
    monkeypatch.setattr(app_settings._env, "SYNC_LEGACY_API_BASE", "https://cu.example.com")
    app_settings.refresh()
    assert app_settings.get("sync_legacy_api_base") == "https://cu.example.com"

    service.save(db, {"sync_legacy_api_base": "https://moi.example.com"}, user_id=7)
    assert app_settings.get("sync_legacy_api_base") == "https://moi.example.com"


def test_o_bo_trong_thi_roi_ve_env(db, cfg, monkeypatch):
    """Nhánh thứ hai: bảng chưa có thì đọc `.env`.

    Đây cũng là đường sống của hệ ĐANG CHẠY lúc vừa deploy bản này — bảng cấu
    hình trống trơn, mọi thứ phải chạy y như trước mà không cần ai đi nhập lại.
    """
    monkeypatch.setattr(app_settings._env, "SYNC_LEGACY_API_BASE", "https://cu.example.com")
    service.save(db, {"sync_legacy_api_base": ""}, user_id=7)
    assert app_settings.get("sync_legacy_api_base") == "https://cu.example.com"


def test_ca_hai_deu_rong_thi_coi_nhu_chua_cau_hinh(db, cfg, env_trong):
    """Nhánh thứ ba: không có ở đâu cả thì đừng đoán, cứ trả rỗng."""
    assert (app_settings.get("sync_legacy_api_base") or "") == ""
    assert (app_settings.get("sync_shared_secret") or "") == ""
    assert require_source(SOURCE_DATXE).is_ready() is False


# ---------------------------------------------------------------------------
# 1. Cầu dao và mã ký đọc LÚC CHẠY
# ---------------------------------------------------------------------------
def test_ha_cau_dao_tren_man_hinh_thi_ngat_dong_bo_ngay(db, cfg):
    """Bài kiểm quan trọng nhất của cả nhịp.

    Đây chính là tình huống người ta dời cụm này vì nó: đường nối với app cũ đang
    đổ phiếu hỏng vào, người trực mở màn Cấu hình và gạt công tắc. Nếu `SyncSource`
    chụp giá trị lúc nạp module thì công tắc ấy không làm gì cả cho tới lần khởi
    động lại — mà màn hình vẫn báo «đã lưu».
    """
    nguon = require_source(SOURCE_DATXE)

    service.save(db, {"sync_datxe_enabled": True}, user_id=7)
    assert nguon.is_enabled() is True

    service.save(db, {"sync_datxe_enabled": False}, user_id=7)
    assert nguon.is_enabled() is False


def test_doi_ma_ky_tren_man_hinh_thi_lan_goi_sau_dung_ma_moi(db, cfg):
    """Mã ký dời xuống bảng dưới dạng BÍ MẬT (mã hóa), nhưng nội bộ vẫn đọc ra được."""
    nguon = require_source(SOURCE_DATXE)
    service.save(db, {"sync_shared_secret": "ma-ky-vua-xoay"}, user_id=7)
    assert nguon.secret() == "ma-ky-vua-xoay"


def test_dia_chi_app_cu_bo_dau_gach_cheo_thua(db, cfg):
    """Người dùng dán địa chỉ kèm gạch chéo cuối là chuyện thường; ghép đường dẫn
    sau đó sẽ ra hai gạch liền và hệ bên kia trả 404."""
    nguon = require_source(SOURCE_DATXE)
    service.save(db, {"sync_legacy_api_base": "https://app-cu.example.com/"}, user_id=7)
    assert nguon.base_url() == "https://app-cu.example.com"


def test_du_ba_o_thi_moi_coi_la_san_sang(db, cfg, env_trong):
    """`is_ready` và `legacy_ready` là hai cửa khác nhau nhưng cùng một điều kiện:
    thiếu một trong ba ô thì đừng gọi ra ngoài, kẻo lỗi hiện ra ở tận chỗ khác."""
    service.save(db, {"sync_datxe_enabled": True,
                      "sync_legacy_api_base": "https://app-cu.example.com",
                      "sync_shared_secret": "ma-ky"}, user_id=7)
    assert require_source(SOURCE_DATXE).is_ready() is True
    assert legacy_files.legacy_ready() is True

    service.save(db, {"sync_legacy_api_base": ""}, user_id=7)
    assert legacy_files.legacy_ready() is False


def test_tat_cau_dao_thi_khong_san_sang_du_da_co_ma_ky(db, cfg, env_trong):
    """Tắt rồi mà vẫn «sẵn sàng» thì cầu dao chỉ là trang trí."""
    service.save(db, {"sync_datxe_enabled": False,
                      "sync_shared_secret": "ma-ky"}, user_id=7)
    assert require_source(SOURCE_DATXE).is_ready() is False


def test_tra_danh_muc_firebase_doc_theo_bang_cau_hinh(db, cfg, env_trong):
    """Thiếu một trong hai ô thì việc tra danh mục nằm im — và nằm im TRONG IM
    LẶNG, vì `read_node` nuốt lỗi thành `None`. Nên cửa `is_configured` phải nói
    đúng sự thật, không thì triệu chứng duy nhất là phiếu thiếu ô xe."""
    service.save(db, {"legacy_firebase_db_url": "https://du-an.firebaseio.com"}, user_id=7)
    assert firebase.is_configured() is False

    service.save(db, {"legacy_firebase_secret": "khoa-doc"}, user_id=7)
    assert firebase.is_configured() is True


# ---------------------------------------------------------------------------
# 2. POS365 — đọc lúc dựng phiên, cầu dao vẫn ở `.env`
# ---------------------------------------------------------------------------
def test_doi_mat_khau_pos365_thi_phien_ke_tiep_dung_ngay(db, cfg):
    """Ba ô này từng là mặc định của tham số hàm dựng, tức đọc lúc gọi — nhưng
    đọc từ `settings`. Nay đọc từ bảng cấu hình, vẫn phải là lúc GỌI."""
    service.save(db, {"pos365_base_url": "https://cua-hang.pos365.vn/",
                      "pos365_username": "dego",
                      "pos365_password": "mat-khau-moi"}, user_id=7)

    client = Pos365Client()
    assert client.base_url == "https://cua-hang.pos365.vn"
    assert client.username == "dego"
    assert client.password == "mat-khau-moi"


def test_tham_so_truyen_thang_van_de_len_bang_cau_hinh(db, cfg):
    """Bài kiểm vẫn phải dựng được client giả mà không đụng bảng cấu hình."""
    service.save(db, {"pos365_username": "dego"}, user_id=7)
    assert Pos365Client(username="tai-khoan-cua-bai-kiem").username == "tai-khoan-cua-bai-kiem"


def test_dia_chi_cua_hang_pos365_doc_theo_bang(db, cfg):
    service.save(db, {"pos365_base_url": "https://cua-hang.pos365.vn"}, user_id=7)
    assert require_source(SOURCE_POS365).base_url() == "https://cua-hang.pos365.vn"


# ---------------------------------------------------------------------------
# 3. Bí mật mới KHÔNG được đi ngược ra cửa đọc
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("khoa, gia_tri", [
    ("sync_shared_secret", "ma-ky-chung-khong-duoc-lo"),
    ("legacy_firebase_secret", "khoa-firebase-khong-duoc-lo"),
    ("pos365_password", "mat-khau-pos365-khong-duoc-lo"),
])
def test_cua_doc_khong_tra_ve_bi_mat_moi_duoi_bat_ky_dang_nao(db, cfg, khoa, gia_tri):
    """`get_all()` là thứ trả về cho trình duyệt. Nó gắn `value` cho ô thường và
    chỉ gắn `configured` cho ô bí mật — hai vòng lặp riêng. Ngày ai đó gộp lại
    cho gọn thì ba khóa này đi thẳng ra cửa công khai. Quét cả bản gốc lẫn bản mã.
    """
    service.save(db, {khoa: gia_tri}, user_id=7)

    ket_qua = repr(service.get_all())
    assert gia_tri not in ket_qua
    ban_ma = db.execute(
        text("SELECT svalue FROM tab_setting WHERE skey=:k"), {"k": khoa}
    ).scalar()
    assert ban_ma and ban_ma not in ket_qua

    o = next(s for s in service.get_all()["secrets"] if s["key"] == khoa)
    assert o["configured"] is True
    assert "value" not in o


# ---------------------------------------------------------------------------
# 4. Con số «giữ lại bao nhiêu» phải có sàn
# ---------------------------------------------------------------------------
def test_so_ban_sao_luu_khong_bao_gio_xuong_duoi_mot(db, cfg):
    """Ô này quyết định XÓA BAO NHIÊU BẢN SAO LƯU. Để trống hay gõ 0 mà đi thẳng
    xuống thì lượt dọn kế tiếp xóa sạch mọi bản sao lưu đang có — và đó là thứ
    người ta chỉ phát hiện đúng lúc cần phục hồi."""
    service.save(db, {"backup_keep": "0"}, user_id=7)
    assert backup_service.keep_count() >= 1

    service.save(db, {"backup_keep": ""}, user_id=7)
    assert backup_service.keep_count() >= 1


def test_so_ban_sao_luu_dat_dung_thi_nghe_theo_man_hinh(db, cfg):
    service.save(db, {"backup_keep": "12"}, user_id=7)
    assert backup_service.keep_count() == 12


def test_so_ngay_giu_thong_bao_bang_khong_thi_khong_xoa_sach(db, cfg, monkeypatch):
    """Cùng một cái bẫy ở một ô khác: `keep_days = 0` nghĩa là mốc cắt bằng ĐÚNG
    lúc này, tức lượt chạy nền xóa sạch thông báo của cả hệ mà không ai thấy."""
    from app.modules.notification import tasks

    monkeypatch.setattr(tasks, "SessionLocal", cfg)
    db.add(Notification(user_id=1, title="Thông báo hôm qua", body="",
                        created_at=datetime.now() - timedelta(days=1)))
    db.commit()

    tasks.cleanup_notifications_task()

    con_lai = db.query(Notification).filter(Notification.title == "Thông báo hôm qua").count()
    assert con_lai == 1


# ---------------------------------------------------------------------------
# 5. Chốt NGƯỢC — những khóa cố ý ở lại `.env`
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("khoa", [
    "backup_once_daily", "sync_datxe_pull_minutes", "pos365_pull_minutes", "pos365_hard_off",
])
def test_khoa_bi_chup_luc_nap_module_thi_khong_duoc_bay_len_man_hinh(khoa):
    """Bốn khóa này được đọc trong lúc dựng lịch chạy nền ở `celery_app.py`, tức
    lúc nạp module. Bày chúng lên màn hình là hứa một điều KHÔNG đúng: người dùng
    bấm Lưu, màn hình báo thành công, còn lịch chạy vẫn y nguyên cho tới khi ai
    đó dựng lại `celery-beat`. Một ô không có tác dụng còn tệ hơn không có ô nào.
    """
    assert khoa not in app_settings.REGISTRY
    assert khoa not in {f["key"] for f in service.FIELDS}


@pytest.mark.parametrize("khoa", [
    #  Sai một lần là hỏng không cứu được.
    "storage_prefix", "email_hard_off",
    #  Chuyện của người dựng máy, không phải lựa chọn nghiệp vụ.
    "db_host", "db_password", "jwt_secret", "cors_origins", "trusted_proxy_cidrs",
    "login_rate_limit", "redis_url", "dev_mode",
    #  Có bản sao ở phía màn hình; sửa một bên là đăng nhập Google chết.
    "google_client_id",
    #  Không chỗ nào đọc — bày lên là hứa một nút không nối vào đâu cả.
    "sync_default_company_id", "sync_notify_on_import",
])
def test_cum_quan_trong_va_khoa_chet_khong_duoc_dat_len_man_hinh(khoa):
    """Đại ca chốt: cụm quan trọng như cơ sở dữ liệu hay mã ký thẻ ra vào thì để
    nguyên ở `.env`."""
    assert khoa not in app_settings.REGISTRY
    assert khoa not in app_settings.SECRETS
    assert khoa not in {f["key"] for f in service.FIELDS}
    assert khoa not in {s["key"] for s in service.SECRET_FIELDS}


def test_kho_tep_app_cu_van_o_env():
    """`LEGACY_R2_*` chỉ ĐỌC kho tệp của app cũ và đã cố ý không đi qua bảng này
    từ lúc dựng — giữ nguyên chốt đó."""
    for khoa in ("legacy_r2_endpoint", "legacy_r2_bucket",
                 "legacy_r2_access_key_id", "legacy_r2_secret_access_key"):
        assert khoa not in app_settings.REGISTRY
        assert khoa not in app_settings.SECRETS
