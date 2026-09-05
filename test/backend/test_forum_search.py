"""CR-263 Diễn đàn — tìm kiếm bài viết + nhật ký kiểm duyệt. Điều kiện đủ:

  1. người thường tìm gì cũng CHỈ ra bài mình vốn được xem (`_visible_cond`
     nằm ngay trong SQL, không phải lọc sau);
  2. từ khóa khớp cả nội dung lẫn tiêu đề thread;
  3. `%`/`_` người dùng gõ là ký tự thường, không phải wildcard mở toang;
  4. lọc theo người tạo (gõ tên/mã NV), công ty, phòng ban ĐÓNG BĂNG trên bài;
  5. trạng thái ẩn chỉ quản trị lọc được — người thường gửi `status=2` bị bỏ qua;
  6. nhật ký kiểm duyệt đọc được, mới → cũ, phân trang có tổng.

Test gọi thẳng tầng service — khuôn `test_forum_api.py` (dựng lại đúng bộ máy
ba tọa độ phòng/công ty của nó để thử chéo luật audience).
"""
from types import SimpleNamespace

import pytest

from app.core.auth import get_perm_profile
from app.modules.forum import service
from app.modules.forum.model import (ForumAudience, ForumModerationAction,
                                     ForumPostStatus)


def _people(db, code, company_id, dept_id):
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    emp = Employee(code=code, full_name=f"NV {code}", company_id=company_id,
                   department_id=dept_id, is_active=True)
    db.add(emp)
    db.flush()
    u = User(email=code, employee_id=emp.id, password_hash="x", is_active=True)
    db.add(u)
    db.flush()
    return u


@pytest.fixture()
def bo_may(db, seed):
    from app.modules.company.model import Company
    from app.modules.department.model import Department
    from app.modules.user.model import User

    cty2 = Company(name="Cty Hai", code="CT02", is_active=True)
    db.add(cty2)
    db.flush()
    dept2 = Department(code="DEPT02", name="Phòng Hai", company_id=seed.company_id, is_active=True)
    dept3 = Department(code="DEPT03", name="Phòng Cty Hai", company_id=cty2.id, is_active=True)
    db.add_all([dept2, dept3])
    db.flush()

    tac_gia = db.get(User, seed.u_req_id)   # DEPT01 / CT01
    cung_phong = _people(db, "SCUNGPHONG", seed.company_id, seed.dept_id)
    khac_phong = _people(db, "SKHACPHONG", seed.company_id, dept2.id)
    khac_cty = _people(db, "SKHACCTY", cty2.id, dept3.id)
    db.commit()
    return SimpleNamespace(tac_gia=tac_gia, cung_phong=cung_phong,
                           khac_phong=khac_phong, khac_cty=khac_cty)


def _dang(db, user, body, audience=ForumAudience.PUBLIC, **kw):
    return service.create_post(db, user, get_perm_profile(db, user), body,
                               int(audience), **kw)


def _tim_ids(db, user, **kw):
    rows, total = service.search_posts(db, user, get_perm_profile(db, user), **kw)
    return [p.id for p in rows], total


# ── 1. Tìm kiếm vẫn nguyên luật audience ────────────────────────────────────────

def test_tim_khong_lo_bai_ngoai_pham_vi(db, bo_may):
    p = _dang(db, bo_may.tac_gia, "báo cáo quý bí mật", ForumAudience.DEPT)
    ids, _ = _tim_ids(db, bo_may.cung_phong, q="bí mật")
    assert p.id in ids
    ids, total = _tim_ids(db, bo_may.khac_phong, q="bí mật")
    assert p.id not in ids and total == 0          # total cũng không được đếm lộ
    ids, _ = _tim_ids(db, bo_may.tac_gia, q="bí mật")
    assert p.id in ids                              # tác giả luôn thấy bài mình


def test_nguoi_thuong_khong_loc_duoc_trang_thai_an(db, bo_may, grant_role):
    """Người thường gửi status=2 phải bị BỎ QUA — không thành cửa dò bài ẩn."""
    from app.modules.user.model import User
    p = _dang(db, bo_may.tac_gia, "bài sắp bị ẩn")
    admin = bo_may.khac_cty
    grant_role(admin.id, "forum_post", scope="all", read=True, write=True, delete=True)
    admin = db.get(User, admin.id)
    service.moderate(db, admin, p, ForumModerationAction.HIDE, "vi phạm")

    ids, _ = _tim_ids(db, bo_may.cung_phong, q="sắp bị ẩn",
                      status=int(ForumPostStatus.HIDDEN))
    assert p.id not in ids
    # quản trị thì lọc được đúng bài ẩn
    ids, _ = _tim_ids(db, admin, q="sắp bị ẩn", status=int(ForumPostStatus.HIDDEN))
    assert p.id in ids
    # và lọc "đang hiện" thì bài ẩn biến đi
    ids, _ = _tim_ids(db, admin, q="sắp bị ẩn", status=int(ForumPostStatus.PUBLISHED))
    assert p.id not in ids


# ── 2+3. Từ khóa ────────────────────────────────────────────────────────────────

def test_khop_ca_tieu_de_thread(db, bo_may):
    nhom = service.create_board(db, bo_may.tac_gia, SimpleNamespace(
        name="Nhóm", description="", icon="", parent_id=0, sort_order=0, status=1))
    box = service.create_board(db, bo_may.tac_gia, SimpleNamespace(
        name="Box", description="", icon="", parent_id=nhom.id, sort_order=0, status=1))
    p = _dang(db, bo_may.tac_gia, "nội dung thường", board_id=box.id,
              title="Hướng dẫn quyết toán")
    ids, _ = _tim_ids(db, bo_may.cung_phong, q="quyết toán")
    assert p.id in ids


def test_ky_tu_dai_dien_khong_mo_toang(db, bo_may):
    """Gõ `100%` phải ra đúng bài chứa `100%`, không phải mọi bài có `100`."""
    dung = _dang(db, bo_may.tac_gia, "giảm giá 100% hôm nay")
    _dang(db, bo_may.tac_gia, "giảm giá 100k hôm nay")
    ids, total = _tim_ids(db, bo_may.tac_gia, q="100%")
    assert ids == [dung.id] and total == 1
    assert service.escape_like("a%b_c\\d") == "a\\%b\\_c\\\\d"


# ── 4. Bộ lọc người tạo / công ty / phòng ban ──────────────────────────────────

def test_loc_theo_nguoi_tao_bang_ten(db, bo_may):
    cua_ban = _dang(db, bo_may.cung_phong, "bài của đồng nghiệp")
    _dang(db, bo_may.tac_gia, "bài của tác giả")
    ids, _ = _tim_ids(db, bo_may.tac_gia, author_q="NV SCUNGPHONG")
    assert ids == [cua_ban.id]
    # khớp cả MÃ nhân sự, không phân biệt cần gõ đủ tên
    ids, _ = _tim_ids(db, bo_may.tac_gia, author_q="SCUNGPHONG")
    assert cua_ban.id in ids


def test_loc_theo_cong_ty_va_phong_ban_dong_bang(db, bo_may):
    p_cty1 = _dang(db, bo_may.tac_gia, "bài công ty một")
    p_cty2 = _dang(db, bo_may.khac_cty, "bài công ty hai")
    profile = get_perm_profile(db, bo_may.tac_gia)
    ids, _ = _tim_ids(db, bo_may.tac_gia, company_id=profile["company_id"])
    assert p_cty1.id in ids and p_cty2.id not in ids
    ids, _ = _tim_ids(db, bo_may.tac_gia, dept_id=profile["dept_id"])
    assert p_cty1.id in ids and p_cty2.id not in ids


def test_tuy_chon_bo_loc_chi_gom_don_vi_da_co_bai(db, bo_may):
    _dang(db, bo_may.tac_gia, "bài duy nhất")
    opts = service.list_search_filter_options(db)
    profile = get_perm_profile(db, bo_may.tac_gia)
    assert [c["id"] for c in opts["companies"]] == [profile["company_id"]]
    assert [d["id"] for d in opts["departments"]] == [profile["dept_id"]]


# ── 5. Phân trang ───────────────────────────────────────────────────────────────

def test_phan_trang_khong_lap_khong_sot(db, bo_may):
    tao = [_dang(db, bo_may.tac_gia, f"trang thử số {i}").id for i in range(5)]
    trang1, total = _tim_ids(db, bo_may.tac_gia, q="trang thử", page=1, per_page=2)
    trang2, _ = _tim_ids(db, bo_may.tac_gia, q="trang thử", page=2, per_page=2)
    trang3, _ = _tim_ids(db, bo_may.tac_gia, q="trang thử", page=3, per_page=2)
    assert total == 5
    assert trang1 + trang2 + trang3 == sorted(tao, reverse=True)


# ── 6. Nhật ký kiểm duyệt ──────────────────────────────────────────────────────

def test_nhat_ky_kiem_duyet_moi_truoc_cu_sau(db, bo_may, grant_role):
    from app.modules.user.model import User
    admin = bo_may.khac_cty
    grant_role(admin.id, "forum_post", scope="all", read=True, write=True, delete=True)
    admin = db.get(User, admin.id)
    p = _dang(db, bo_may.tac_gia, "bài bị xử")
    service.moderate(db, admin, p, ForumModerationAction.HIDE, "lý do ẩn")
    service.moderate(db, admin, p, ForumModerationAction.RESTORE, "")
    service.moderate(db, admin, p, ForumModerationAction.REMOVE, "lý do xóa")

    rows, total = service.list_moderation_logs(db)
    assert total == 3
    assert [int(r.action) for r in rows] == [int(ForumModerationAction.REMOVE),
                                             int(ForumModerationAction.RESTORE),
                                             int(ForumModerationAction.HIDE)]
    assert rows[0].reason == "lý do xóa" and rows[0].created_by == admin.id

    trang2, total = service.list_moderation_logs(db, page=2, per_page=2)
    assert total == 3 and len(trang2) == 1
