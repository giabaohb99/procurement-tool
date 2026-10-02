"""Phase 03 — `ensure_report_access_defaults` + bất biến của `ReportKey`/`REPORT_META`.

Migration (lên/xuống/lên) kiểm TAY ở phase 01 — SQLite không chạy alembic nên
không lặp lại ở đây.
"""
from app.core import code_sets  # noqa: F401 — side-effect: nạp bộ mã report_key vào sổ đăng ký
from app.core.report_keys import REPORT_META, ReportKey
from app.core.status_catalog import all_sets
from app.core.subject_match import SUBJECT_ROLE
from app.modules.report_access.model import ReportAccess
from app.modules.report_access.seed_defaults import ensure_report_access_defaults
from app.modules.role.model import Role


def _admin_role(db) -> Role:
    role = Role(code="admin", name="Quản trị hệ thống")
    db.add(role)
    db.commit()
    return role


def test_co_admin_chen_du_13_dong(db):
    admin = _admin_role(db)
    n = ensure_report_access_defaults(db)
    assert n == 13
    rows = db.query(ReportAccess).filter(ReportAccess.subject_kind == SUBJECT_ROLE,
                                         ReportAccess.subject_id == admin.id).all()
    assert len(rows) == 13
    assert {r.report_key for r in rows} == {int(k) for k in ReportKey}


def test_chay_lan_2_khong_chen_them(db):
    _admin_role(db)
    ensure_report_access_defaults(db)
    assert ensure_report_access_defaults(db) == 0


def test_thu_hoi_dong_admin_roi_chay_lai_khong_chen_lai(db):
    admin = _admin_role(db)
    ensure_report_access_defaults(db)
    from datetime import datetime
    row = (db.query(ReportAccess)
          .filter(ReportAccess.subject_kind == SUBJECT_ROLE, ReportAccess.subject_id == admin.id,
                 ReportAccess.report_key == int(ReportKey.DOCUMENT)).one())
    row.revoked_at = datetime.now()
    db.commit()

    assert ensure_report_access_defaults(db) == 0
    still_only_one = db.query(ReportAccess).filter(
        ReportAccess.report_key == int(ReportKey.DOCUMENT)).count()
    assert still_only_one == 1   # không chèn dòng mới cho khóa đã có dòng (dù đã thu hồi)


def test_khoa_co_dong_gan_cho_nguoi_khac_khong_chen_admin(db):
    admin = _admin_role(db)
    #  Dòng gán cho MỘT VAI TRÒ KHÁC (không phải admin) trên khóa WORK.
    other = Role(code="khac", name="Vai trò khác")
    db.add(other)
    db.flush()
    db.add(ReportAccess(report_key=int(ReportKey.WORK), subject_kind=SUBJECT_ROLE,
                        subject_id=other.id, effect=1, reason="t", created_by=0, updated_by=0))
    db.commit()

    n = ensure_report_access_defaults(db)
    assert n == 12   # 13 trừ WORK (đã có dòng, dù không phải admin)
    admin_has_work = db.query(ReportAccess).filter(
        ReportAccess.report_key == int(ReportKey.WORK), ReportAccess.subject_kind == SUBJECT_ROLE,
        ReportAccess.subject_id == admin.id).count()
    assert admin_has_work == 0


def test_khong_co_role_admin_tra_0_khong_no(db):
    assert ensure_report_access_defaults(db) == 0
    assert db.query(ReportAccess).count() == 0


#  ── M5 — chèn cho CẢ 'admin' lẫn 'ADMINISTRATOR' nếu cùng tồn tại ───────────────────

def test_admin_va_administrator_cung_ton_tai_ca_hai_duoc_chen_du_lan_dau(db):
    """Chốt "quyết định theo trạng thái TRƯỚC khi chèn": nếu cài sai thành đọc lại
    `keys_with_any_row` GIỮA hai vòng vai trò, vai trò xử lý THỨ HAI sẽ thấy mọi khóa đã
    "có dòng" (do vai trò thứ nhất vừa thêm) và bị skip hết — n sẽ ra 13 chứ không phải 26."""
    admin = Role(code="admin", name="Quản trị hệ thống")
    legacy = Role(code="ADMINISTRATOR", name="Quản trị (đời cũ)")
    db.add_all([admin, legacy])
    db.commit()

    n = ensure_report_access_defaults(db)
    assert n == 26   # 13 khóa × 2 vai trò quản trị

    admin_rows = db.query(ReportAccess).filter(ReportAccess.subject_kind == SUBJECT_ROLE,
                                               ReportAccess.subject_id == admin.id).count()
    legacy_rows = db.query(ReportAccess).filter(ReportAccess.subject_kind == SUBJECT_ROLE,
                                                ReportAccess.subject_id == legacy.id).count()
    assert admin_rows == 13
    assert legacy_rows == 13

    #  Chạy lại -> cả hai vai trò đã đủ 13 dòng mỗi bên, không chèn thêm.
    assert ensure_report_access_defaults(db) == 0


def test_chi_administrator_khong_co_admin_van_duoc_chen(db):
    """DB cũ chưa đổi tên vai trò (chỉ còn `ADMINISTRATOR`, chưa có `admin`) vẫn phải
    được chèn — không riêng mã mới."""
    legacy = Role(code="ADMINISTRATOR", name="Quản trị (đời cũ)")
    db.add(legacy)
    db.commit()

    n = ensure_report_access_defaults(db)
    assert n == 13
    rows = db.query(ReportAccess).filter(ReportAccess.subject_kind == SUBJECT_ROLE,
                                         ReportAccess.subject_id == legacy.id).all()
    assert len(rows) == 13


def test_report_key_lien_tuc_khong_trung():
    values = [int(k) for k in ReportKey]
    assert values == list(range(1, len(values) + 1)), "khóa phải liên tục 1..N, không trùng"
    assert len(set(values)) == len(values)


def test_report_meta_du_moi_khoa():
    assert set(REPORT_META) == set(ReportKey)
    for key, (label, group) in REPORT_META.items():
        assert label.strip() and group.strip(), key


def test_bo_ma_report_key_co_trong_all_sets():
    """`import code_sets` ở đầu tệp đã nạp `report_keys` (side-effect, xem
    `code_sets.py`) — chỉ cần gọi `all_sets()` là đủ thấy bộ mã `report_key`."""
    sets = all_sets()
    assert "report_key" in sets
    cs = sets["report_key"]
    assert {c.value for c in cs.codes} == {str(int(k)) for k in ReportKey}
    assert len(cs.codes) == len(ReportKey)
