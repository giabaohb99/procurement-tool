"""bao-CR-707 — sửa bài diễn đàn, chuyển box, nhãn Thông báo, lọc quản trị.

Luật cần giữ:
  1. tác giả sửa được tiêu đề / nội dung / nhãn bài mình; người khác (không quản trị) bị 403;
  2. chỉ quản trị (forum_post.write) chuyển box và gắn nhãn Thông báo — cả khi đăng lẫn khi sửa;
  3. quản trị sửa bài người khác ghi một dòng nhật ký EDIT nói rõ đổi gì; tác giả tự sửa thì không;
  4. nội dung sửa đi qua cùng bộ lọc HTML với lúc đăng; bài trong box không được bỏ trống tiêu đề;
  5. tìm kiếm lọc được theo nhãn và theo ghim.
Gọi thẳng tầng service — khuôn `test_forum_board.py`.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.auth import get_perm_profile
from app.modules.forum import service
from app.modules.forum.model import (ForumAudience, ForumBodyFormat, ForumBoardStatus,
                                     ForumModerationAction, ForumModerationLog, ForumPrefix)


def _board_in(**kw):
    base = {"name": "", "description": "", "icon": "", "parent_id": 0,
            "sort_order": 0, "status": int(ForumBoardStatus.ACTIVE)}
    base.update(kw)
    return SimpleNamespace(**base)


def _people(db, code, company_id, dept_id):
    from app.modules.employee.model import Employee
    from app.modules.user.model import User
    e = Employee(code=code, full_name=f"NV {code}", company_id=company_id, department_id=dept_id,
                 is_active=True)
    db.add(e)
    db.flush()
    u = User(email=code, employee_id=e.id, password_hash="x", is_active=True)
    db.add(u)
    db.flush()
    return u


@pytest.fixture()
def bo_may(db, seed, cap_quyen):
    from app.modules.user.model import User
    tac_gia = db.get(User, seed.u_req_id)
    nguoi_khac = _people(db, "FSUAKHAC", seed.company_id, seed.dept_id)
    quan_tri = _people(db, "FSUAQT", seed.company_id, seed.dept_id)
    cap_quyen(quan_tri.id, "forum_post", scope="all", read=True, write=True, delete=True)
    nhom = service.create_board(db, tac_gia, _board_in(name="Thông báo & Chính sách"))
    box_a = service.create_board(db, tac_gia, _board_in(name="Thông báo công ty", parent_id=nhom.id))
    box_b = service.create_board(db, tac_gia, _board_in(name="Sự kiện", parent_id=nhom.id))
    return SimpleNamespace(tac_gia=tac_gia, nguoi_khac=nguoi_khac, quan_tri=quan_tri,
                           box_a=box_a, box_b=box_b)


def _dang(db, user, box_id, title="Chủ đề", body="nội dung", prefix=0):
    return service.create_post(db, user, get_perm_profile(db, user), body, int(ForumAudience.PUBLIC),
                               board_id=box_id, title=title, prefix=prefix)


def _logs(db, post_id):
    return db.query(ForumModerationLog).filter(ForumModerationLog.post_id == post_id).all()


# ── 1. Ai được sửa ──────────────────────────────────────────────────────────────

def test_tac_gia_sua_bai_minh(db, bo_may):
    p = _dang(db, bo_may.tac_gia, bo_may.box_a.id)
    service.update_post(db, bo_may.tac_gia, p, title="Tiêu đề mới", body="nội dung mới",
                        prefix=int(ForumPrefix.DISCUSSION))
    assert (p.title, p.body, p.prefix) == ("Tiêu đề mới", "nội dung mới", int(ForumPrefix.DISCUSSION))
    assert _logs(db, p.id) == []   # tự sửa bài mình không phải kiểm duyệt


def test_nguoi_khac_khong_sua_duoc(db, bo_may):
    p = _dang(db, bo_may.tac_gia, bo_may.box_a.id)
    with pytest.raises(HTTPException) as e:
        service.update_post(db, bo_may.nguoi_khac, p, title="Chen ngang")
    assert e.value.status_code == 403


# ── 2. Quyền riêng của quản trị ────────────────────────────────────────────────

def test_tac_gia_khong_chuyen_box_khong_gan_thong_bao(db, bo_may):
    p = _dang(db, bo_may.tac_gia, bo_may.box_a.id)
    with pytest.raises(HTTPException) as e:
        service.update_post(db, bo_may.tac_gia, p, board_id=bo_may.box_b.id)
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        service.update_post(db, bo_may.tac_gia, p, prefix=int(ForumPrefix.ANNOUNCEMENT))
    assert e.value.status_code == 403


def test_nguoi_thuong_dang_bai_nhan_thong_bao_bi_chan(db, bo_may):
    with pytest.raises(HTTPException) as e:
        _dang(db, bo_may.tac_gia, bo_may.box_a.id, prefix=int(ForumPrefix.ANNOUNCEMENT))
    assert e.value.status_code == 403


def test_quan_tri_dang_bai_nhan_thong_bao(db, bo_may):
    p = _dang(db, bo_may.quan_tri, bo_may.box_a.id, prefix=int(ForumPrefix.ANNOUNCEMENT))
    assert p.prefix == int(ForumPrefix.ANNOUNCEMENT)


def test_quan_tri_chuyen_box_gan_nhan_ghi_nhat_ky(db, bo_may):
    p = _dang(db, bo_may.tac_gia, bo_may.box_a.id)
    service.update_post(db, bo_may.quan_tri, p, board_id=bo_may.box_b.id,
                        prefix=int(ForumPrefix.ANNOUNCEMENT))
    assert p.board_id == bo_may.box_b.id
    assert p.audience == int(bo_may.box_b.audience)
    assert p.prefix == int(ForumPrefix.ANNOUNCEMENT)
    logs = _logs(db, p.id)
    assert len(logs) == 1 and logs[0].action == int(ForumModerationAction.EDIT)
    assert "chuyển box" in logs[0].reason and "đổi nhãn" in logs[0].reason


def test_khong_doi_gi_thi_khong_ghi_nhat_ky(db, bo_may):
    p = _dang(db, bo_may.tac_gia, bo_may.box_a.id, title="Giữ nguyên")
    service.update_post(db, bo_may.quan_tri, p, title="Giữ nguyên", board_id=bo_may.box_a.id)
    assert _logs(db, p.id) == []


def test_khong_chuyen_vao_box_an(db, bo_may):
    p = _dang(db, bo_may.tac_gia, bo_may.box_a.id)
    bo_may.box_b.status = int(ForumBoardStatus.HIDDEN)
    db.commit()
    with pytest.raises(HTTPException) as e:
        service.update_post(db, bo_may.quan_tri, p, board_id=bo_may.box_b.id)
    assert e.value.status_code == 400


# ── 4. Luật nội dung ────────────────────────────────────────────────────────────

def test_sua_noi_dung_rich_qua_bo_loc(db, bo_may):
    p = _dang(db, bo_may.tac_gia, bo_may.box_a.id)
    service.update_post(db, bo_may.tac_gia, p, body='<p>ok</p><script>alert(1)</script>',
                        body_format=int(ForumBodyFormat.RICH_HTML))
    assert "<script" not in p.body and "ok" in p.body
    assert p.body_format == int(ForumBodyFormat.RICH_HTML)


def test_bai_trong_box_khong_bo_trong_tieu_de(db, bo_may):
    p = _dang(db, bo_may.tac_gia, bo_may.box_a.id)
    with pytest.raises(HTTPException) as e:
        service.update_post(db, bo_may.tac_gia, p, title="  ")
    assert e.value.status_code == 400


def test_khong_xoa_trang_noi_dung_bai_khong_anh(db, bo_may):
    p = _dang(db, bo_may.tac_gia, bo_may.box_a.id)
    with pytest.raises(HTTPException) as e:
        service.update_post(db, bo_may.tac_gia, p, body="")
    assert e.value.status_code == 400


# ── 5. Lọc quản trị ─────────────────────────────────────────────────────────────

def test_tim_kiem_loc_nhan_va_ghim(db, bo_may):
    tb = _dang(db, bo_may.quan_tri, bo_may.box_a.id, prefix=int(ForumPrefix.ANNOUNCEMENT))
    thuong = _dang(db, bo_may.tac_gia, bo_may.box_a.id)
    service.set_post_pinned(db, bo_may.quan_tri, tb, True)
    prof = get_perm_profile(db, bo_may.quan_tri)
    rows, _ = service.search_posts(db, bo_may.quan_tri, prof, prefix=int(ForumPrefix.ANNOUNCEMENT))
    assert [r.id for r in rows] == [tb.id]
    rows, _ = service.search_posts(db, bo_may.quan_tri, prof, pinned=1)
    assert [r.id for r in rows] == [tb.id]
    rows, _ = service.search_posts(db, bo_may.quan_tri, prof, pinned=2)
    assert thuong.id in [r.id for r in rows] and tb.id not in [r.id for r in rows]
