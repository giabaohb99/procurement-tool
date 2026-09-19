"""Nhật ký trước/sau của màn Cấu hình hệ thống — bao-CR-429, nhịp 1.

`tab_setting` là bảng KHÓA-GIÁ TRỊ, nên lớp sự kiện ORM của bao-CR-402 nói
không nên lời: nó ghi theo tên cột, mà cột ở đây tên là `svalue`. Dòng nhật ký
đọc ra *"tab_setting#7 svalue: false -> true"* — biết có người đổi một thứ gì
đó, không biết thứ gì. Bảng vì vậy tự khai vào `NO_LOG_TABLES` rồi tự ghi lấy
bằng `record_change()` với `field` là khóa thật.

Vì sao đáng canh bằng bài kiểm: bảng này sắp giữ endpoint lưu trữ và các khóa
API của bên thứ ba (nhịp 2 và 3 của cùng CR). Đổi endpoint lưu trữ là chuyển
hướng toàn bộ tệp của công ty sang chỗ khác, và nếu quyển sổ chỉ nói "ai đó đã
cập nhật cấu hình" thì lúc đi tra không còn gì để đọc.
"""
import uuid

import pytest
from sqlalchemy.orm import sessionmaker

from app.core import app_settings
from app.core.change_tracker import flush_changes
from app.core.logging_codes import ACTOR_KIND_USER, CHANGE_OP_UPDATE
from app.core.logging_policy import NO_LOG_TABLES
from app.core.request_context import RequestContext, reset_context, set_context
from app.modules.audit.model import AuditLog
from app.modules.change_log.model import ChangeLog
from app.modules.setting import service
from app.modules.setting.model import Setting


@pytest.fixture
def ctx(db, monkeypatch):
    """Ngữ cảnh thật + `SessionLocal` trỏ vào DB của test (xem CR-402)."""
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)
    context = RequestContext(request_id=uuid.uuid4().bytes, user_id=7,
                             actor_kind=ACTOR_KIND_USER)
    token = set_context(context)
    try:
        yield context
    finally:
        reset_context(token)


def _rows(db) -> list[ChangeLog]:
    return db.query(ChangeLog).order_by(ChangeLog.id).all()


# ---------------------------------------------------------------------------
# Ô thường
# ---------------------------------------------------------------------------
def test_o_thuong_ghi_dung_khoa_va_gia_tri(db, ctx):
    """Một dòng, `field` là khóa cấu hình chứ không phải tên cột `svalue`."""
    service.save(db, {"pr_dispatch_enabled": True}, user_id=7)
    assert flush_changes(ctx) == 1

    row = _rows(db)[0]
    assert row.table_name == "tab_setting"
    assert row.field == "pr_dispatch_enabled"
    assert row.op == CHANGE_OP_UPDATE
    assert row.after_value == "true"
    assert row.is_masked is False
    assert row.created_by == 7


def test_ghi_duoc_gia_tri_cu_khi_doi_lan_hai(db, ctx):
    """Lần đầu chưa có dòng nào dưới DB nên `before` rỗng; lần sau phải có."""
    service.save(db, {"smtp_host": "smtp.cu.vn"}, user_id=7)
    flush_changes(ctx)
    service.save(db, {"smtp_host": "smtp.moi.vn"}, user_id=7)
    flush_changes(ctx)

    lan_hai = _rows(db)[-1]
    assert lan_hai.before_value == "smtp.cu.vn"
    assert lan_hai.after_value == "smtp.moi.vn"


def test_luu_lai_y_gia_tri_cu_thi_khong_de_dong(db, ctx):
    """Màn hình gửi lại MỌI ô mỗi lần bấm Lưu.

    Không lọc thì mỗi lần bấm đẻ một dòng cho từng khóa, và quyển sổ chìm trong
    những dòng nói "đổi từ X sang X".
    """
    service.save(db, {"smtp_host": "smtp.abc.vn"}, user_id=7)
    flush_changes(ctx)
    service.save(db, {"smtp_host": "smtp.abc.vn"}, user_id=7)

    assert flush_changes(ctx) == 0


# ---------------------------------------------------------------------------
# Ô bí mật
# ---------------------------------------------------------------------------
def test_o_bi_mat_co_dong_nhung_che_gia_tri(db, ctx):
    """Ghi lại VIỆC đổi khóa, không ghi giá trị — kể cả bản đã mã hóa.

    Dưới DB nó là bản mã Fernet. Chép bản mã sang một bảng CHỈ-THÊM thì không
    ai đọc được mà bí mật lại nằm thêm một chỗ nữa; thứ đáng giữ là *đã có
    người đổi khóa này, lúc nào, ai đổi*.
    """
    service.save(db, {"smtp_password": "mat-khau-that"}, user_id=7)
    assert flush_changes(ctx) == 1

    row = _rows(db)[0]
    assert row.field == "smtp_password"
    assert row.is_masked is True
    assert row.before_value is None
    assert row.after_value is None


def test_khong_dong_nao_chua_mat_khau_dang_chu(db, ctx):
    """Chốt chặn cuối: quét cả bảng, không ô nào được mang chuỗi gốc."""
    service.save(db, {"smtp_password": "mat-khau-that"}, user_id=7)
    flush_changes(ctx)

    for row in _rows(db):
        assert "mat-khau-that" not in (row.before_value or "")
        assert "mat-khau-that" not in (row.after_value or "")


def test_o_bi_mat_rong_thi_giu_nguyen_khong_ghi_de(db, ctx):
    """Gửi rỗng = "không đổi", không phải "xóa khóa đi"."""
    service.save(db, {"smtp_password": "khoa-cu"}, user_id=7)
    flush_changes(ctx)
    service.save(db, {"smtp_password": ""}, user_id=7)

    assert flush_changes(ctx) == 0
    assert app_settings.get("smtp_password") == "khoa-cu"


# ---------------------------------------------------------------------------
# Dòng audit
# ---------------------------------------------------------------------------
def test_dong_audit_ke_ten_o_da_doi(db, ctx):
    """Dòng thời gian bày câu này, nên nó phải nói được mức nghiêm trọng.

    "Đã đổi Endpoint lưu trữ" và "đã đổi số ngày giữ thông báo" là hai chuyện
    rất khác nhau; một câu chung cho cả hai thì phải mở nhật ký chi tiết mới
    biết, mà phần lớn người đọc dừng ở dòng thời gian.
    """
    service.save(db, {"r2_endpoint": "https://kho-la.example.com"}, user_id=7)

    dong = db.query(AuditLog).filter(AuditLog.entity == "setting").all()[-1]
    assert "Endpoint" in dong.message


def test_khong_o_nao_doi_thi_noi_thang(db, ctx):
    """Bấm Lưu mà không sửa gì cũng để lại dấu, nhưng nói rõ là không đổi gì."""
    service.save(db, {}, user_id=7)

    dong = db.query(AuditLog).filter(AuditLog.entity == "setting").all()[-1]
    assert "không ô nào đổi" in dong.message


# ---------------------------------------------------------------------------
# Chốt cấu hình
# ---------------------------------------------------------------------------
def test_bang_setting_nam_trong_danh_sach_cam_lop_tu_dong():
    """Thiếu tên này là mỗi lần lưu ra HAI dòng: một dòng tay, một dòng
    `svalue` vô nghĩa của lớp tự động."""
    assert "tab_setting" in NO_LOG_TABLES


def test_moi_khoa_khai_bao_deu_co_nhan(db):
    """`_label_of` là thứ dựng nên câu trong dòng audit.

    Khóa thiếu nhãn thì câu đó rơi về tên khóa kỹ thuật — vẫn đọc được, nhưng
    đây là chỗ rẻ nhất để bắt một khai báo viết vội.
    """
    for khoa in list(service._FIELD_KEYS) + list(service._SECRET_KEYS):
        assert service._label_of(khoa) != khoa, f"khóa {khoa} chưa có nhãn"


def test_khoa_la_thi_bo_qua_khong_no(db, ctx):
    """Gửi khóa không khai báo thì lặng lẽ bỏ, không ghi và không nổ.

    Đây là cửa PUT công khai: ai cũng gửi được thân tùy ý, và bảng cấu hình
    không phải chỗ để người ngoài gieo khóa lạ.
    """
    service.save(db, {"khoa_la_hoac_go_sai": "x"}, user_id=7)

    assert flush_changes(ctx) == 0
    assert db.query(Setting).filter(Setting.skey == "khoa_la_hoac_go_sai").first() is None
