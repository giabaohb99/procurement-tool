"""F1 Diễn đàn — điều kiện đủ của phase (doc/erp/dien-dan/02-lo-trinh-phase.md):

  1. người phòng khác không thấy bài `dept`;
  2. người công ty khác không thấy bài `company`;
  3. tác giả luôn thấy bài mình;
  4. con trỏ không lặp / không sót khi có bài chen giữa;
  5. comment vào bài không được xem bị 403.

Kèm các chốt an ninh mới mở ra ở F1: ràng buộc đầu vào khi đăng, điều kiện
sở hữu khi gắn ảnh, nhánh `_check_forum` của đính kèm, và xóa bài cuốn theo
comment + like. Test gọi thẳng tầng service (khuôn các test B-07) — user là
bản ghi User thật để `get_perm_profile` dựng hồ sơ như chạy thật.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.auth import get_perm_profile
from app.modules.forum import service
from app.modules.forum.model import ForumAudience, ForumPost, ForumPostStatus


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
    """seed cho sẵn phòng DEPT01 / công ty CT01. Dựng thêm hai tọa độ để thử
    chéo: phòng thứ hai CÙNG công ty, và một công ty thứ hai."""
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
    cung_phong = _people(db, "FCUNGPHONG", seed.company_id, seed.dept_id)
    khac_phong = _people(db, "FKHACPHONG", seed.company_id, dept2.id)
    khac_cty = _people(db, "FKHACCTY", cty2.id, dept3.id)
    db.commit()
    return SimpleNamespace(tac_gia=tac_gia, cung_phong=cung_phong,
                           khac_phong=khac_phong, khac_cty=khac_cty)


def _dang(db, user, audience, body="bài viết thử"):
    return service.create_post(db, user, get_perm_profile(db, user), body, int(audience))


def _feed_ids(db, user, **kw):
    rows = service.list_posts(db, user, get_perm_profile(db, user), **kw)
    return [p.id for p in rows]


# ── 1+2+3. Luật audience trên feed ──────────────────────────────────────────────

def test_bai_pham_vi_phong_ban(db, bo_may):
    p = _dang(db, bo_may.tac_gia, ForumAudience.DEPT)
    assert p.dept_id and p.company_id            # đóng băng từ hồ sơ lúc đăng
    assert p.id in _feed_ids(db, bo_may.cung_phong)
    assert p.id not in _feed_ids(db, bo_may.khac_phong)   # khác phòng, cùng công ty
    assert p.id not in _feed_ids(db, bo_may.khac_cty)
    assert p.id in _feed_ids(db, bo_may.tac_gia)          # tác giả luôn thấy bài mình


def test_bai_pham_vi_cong_ty(db, bo_may):
    p = _dang(db, bo_may.tac_gia, ForumAudience.COMPANY)
    assert p.id in _feed_ids(db, bo_may.khac_phong)       # khác phòng nhưng cùng công ty
    assert p.id not in _feed_ids(db, bo_may.khac_cty)


def test_bai_public_ai_cung_thay(db, bo_may):
    p = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    for person in (bo_may.cung_phong, bo_may.khac_phong, bo_may.khac_cty):
        assert p.id in _feed_ids(db, person)


def test_xem_mot_bai_ngoai_pham_vi_bi_403(db, bo_may):
    """Đường vòng gõ thẳng id — cùng luật với feed, và 403 GỘP để không dò được
    bài kín có tồn tại hay không."""
    p = _dang(db, bo_may.tac_gia, ForumAudience.DEPT)
    with pytest.raises(HTTPException) as e:
        service.get_visible_post(db, bo_may.khac_cty, p.id)
    assert e.value.status_code == 403
    assert service.get_visible_post(db, bo_may.cung_phong, p.id).id == p.id


def test_forum_admin_thay_het_khong_theo_audience(db, bo_may, grant_role):
    """Quản trị phải thấy hết mới dọn được (mục 4.2 của `01`)."""
    p = _dang(db, bo_may.tac_gia, ForumAudience.DEPT)
    admin = bo_may.khac_cty
    grant_role(admin.id, "forum_post", scope="all", read=True, write=True, delete=True)
    assert p.id in _feed_ids(db, admin)


# ── 4. Con trỏ không lặp, không sót ────────────────────────────────────────────

def test_con_tro_khong_lap_khong_sot_khi_co_bai_chen(db, bo_may):
    old = [_dang(db, bo_may.tac_gia, ForumAudience.PUBLIC, f"bài {i}").id for i in range(5)]
    nguoi_xem = bo_may.cung_phong

    trang1 = _feed_ids(db, nguoi_xem, limit=2)
    assert trang1 == [old[4], old[3]]              # mới nhất trước

    # Bài mới chen vào GIỮA hai lần tải — chính là ca OFFSET làm lệch trang
    new = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC, "bài chen giữa").id

    trang2 = _feed_ids(db, nguoi_xem, limit=2, before_id=trang1[-1])
    trang3 = _feed_ids(db, nguoi_xem, limit=2, before_id=trang2[-1])
    grouped = trang1 + trang2 + trang3
    assert len(grouped) == len(set(grouped))             # không lặp
    assert set(grouped) == set(old)                   # không sót, bài chen không đẩy lệch
    assert new in _feed_ids(db, nguoi_xem, limit=10)   # tải lại trang đầu mới thấy nó


# ── 5. Comment ăn theo luật audience ────────────────────────────────────────────

def test_comment_vao_bai_khong_duoc_xem_bi_403(db, bo_may):
    from app.modules.comment.service import resolve_doc
    p = _dang(db, bo_may.tac_gia, ForumAudience.DEPT)
    with pytest.raises(HTTPException) as e:
        resolve_doc(db, bo_may.khac_cty, "forum_post", p.id)
    assert e.value.status_code == 403
    # người trong phạm vi thì đọc + góp ý bình thường, KHÔNG cần grant RBAC nào
    doc, label, route = resolve_doc(db, bo_may.cung_phong, "forum_post", p.id)
    # Route dạng v2 sẵn — "/posts" trần sẽ làm toAppPath bên FE trả null (chuông câm)
    assert doc.id == p.id and route == "/forum/posts"


# ── Ràng buộc khi đăng ──────────────────────────────────────────────────────────

def test_dang_bai_rang_buoc_dau_vao(db, bo_may):
    u = bo_may.tac_gia
    prof = get_perm_profile(db, u)
    for xau in [("  ", int(ForumAudience.PUBLIC), []),                       # rỗng
                ("x" * (service.MAX_BODY + 1), int(ForumAudience.PUBLIC), []),  # quá dài
                ("ok", int(ForumAudience.PUBLIC), list(range(1, 12))),       # quá 10 ảnh
                ("ok", 9, [])]:                                              # audience lạ
        with pytest.raises(HTTPException) as e:
            service.create_post(db, u, prof, *xau)
        assert e.value.status_code == 400


def test_chua_gan_phong_thi_khong_dang_bai_pham_vi_hep(db, bo_may):
    """Thiếu dữ liệu thì CHẶN (triết lý B-07) — không đóng băng số 0 vào bài."""
    from app.modules.user.model import User
    u = User(email="FTRONG", password_hash="x", is_active=True)
    db.add(u)
    db.commit()
    prof = get_perm_profile(db, u)
    for aud in (ForumAudience.DEPT, ForumAudience.COMPANY):
        with pytest.raises(HTTPException) as e:
            service.create_post(db, u, prof, "ok", int(aud))
        assert e.value.status_code == 400
    # ...và người đó cũng không thấy nhầm bài phạm vi hẹp của ai
    _dang(db, bo_may.tac_gia, ForumAudience.DEPT)
    _dang(db, bo_may.tac_gia, ForumAudience.COMPANY)
    assert _feed_ids(db, u) == []


# ── Trang cá nhân ───────────────────────────────────────────────────────────────

def test_trang_ca_nhan_minh_thay_ca_bai_an(db, bo_may):
    p_public = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    p_dept = _dang(db, bo_may.tac_gia, ForumAudience.DEPT)
    p_an = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC, "bài bị ẩn")
    p_an.status = int(ForumPostStatus.HIDDEN)
    db.commit()

    minh = _feed_ids(db, bo_may.tac_gia, author_id=bo_may.tac_gia.id)
    assert set(minh) == {p_public.id, p_dept.id, p_an.id}   # chính mình: đủ, kể cả bài ẩn
    khach = _feed_ids(db, bo_may.khac_cty, author_id=bo_may.tac_gia.id)
    assert khach == [p_public.id]                           # người ngoài: nguyên luật audience


# ── Ảnh: sở hữu khi gắn + nhánh `_check_forum` của đính kèm ────────────────────

def test_gan_anh_chi_nhan_file_cua_minh_chua_gan(db, bo_may):
    from app.modules.attachment.model import StoredFile
    mine = StoredFile(filename="a.jpg", file_key="k1", url="u1", content_type="image/jpeg",
                          size=1, sha256="s1",
                          created_by=bo_may.tac_gia.id, updated_by=bo_may.tac_gia.id)
    cua_nguoi_khac = StoredFile(filename="b.jpg", file_key="k2", url="u2", content_type="image/jpeg",
                                size=1, sha256="s2",
                                created_by=bo_may.khac_phong.id, updated_by=bo_may.khac_phong.id)
    db.add_all([mine, cua_nguoi_khac])
    db.commit()

    p = service.create_post(db, bo_may.tac_gia, get_perm_profile(db, bo_may.tac_gia),
                            "kèm ảnh", int(ForumAudience.PUBLIC),
                            [mine.id, cua_nguoi_khac.id])
    images = service.image_map(db, [p.id])[p.id]
    assert [a["file_id"] for a in images] == [mine.id]   # file người khác bị lặng lẽ bỏ


def test_check_forum_cua_dinh_kem_theo_luat_bai(db, bo_may):
    from app.modules.attachment.controller import _check_forum
    p = _dang(db, bo_may.tac_gia, ForumAudience.DEPT)
    with pytest.raises(HTTPException) as e:
        _check_forum(db, bo_may.khac_cty, p.id, "read")
    assert e.value.status_code == 403
    _check_forum(db, bo_may.cung_phong, p.id, "read")     # cùng phòng: xem được ảnh
    with pytest.raises(HTTPException) as e:               # ...nhưng không gỡ được
        _check_forum(db, bo_may.cung_phong, p.id, "manage")
    assert e.value.status_code == 403
    _check_forum(db, bo_may.tac_gia, p.id, "manage")      # tác giả gỡ được


# ── Like + đếm comment + xóa bài cuốn theo ─────────────────────────────────────

def test_like_va_dem_comment_gom_theo_trang(db, bo_may):
    p = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    assert service.toggle_like(db, p.id, bo_may.cung_phong.id) == {
        "liked": True, "count": 1, "my_reaction": 1, "reactions": {1: 1}}
    assert service.toggle_like(db, p.id, bo_may.cung_phong.id) == {
        "liked": False, "count": 0, "my_reaction": 0, "reactions": {}}

    from app.modules.comment.service import create_comment
    c = create_comment(db, "forum_post", p.id, "hay quá", bo_may.cung_phong.id)
    create_comment(db, "forum_post", p.id, "chuẩn", bo_may.tac_gia.id, parent_id=c.id)
    assert service.comment_count_map(db, [p.id]) == {p.id: 2}   # đếm cả phản hồi


def test_reaction_doi_cam_xuc_la_update_khong_them_dong(db, bo_may):
    """CR-206: đổi Thích -> Yêu thích phải UPDATE dòng cũ (unique bài+người),
    bấm lại cùng cảm xúc là bỏ; kind lạ bị 400 chứ không nằm xuống DB."""
    from app.modules.forum.model import ForumReaction, ForumReactionKind

    p = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    nguoi = bo_may.cung_phong.id
    service.toggle_like(db, p.id, nguoi, int(ForumReactionKind.LIKE))
    out = service.toggle_like(db, p.id, nguoi, int(ForumReactionKind.LOVE))
    assert out["my_reaction"] == int(ForumReactionKind.LOVE)
    assert out["reactions"] == {int(ForumReactionKind.LOVE): 1}
    assert db.query(ForumReaction).filter(ForumReaction.post_id == p.id).count() == 1

    # Người thứ hai bấm Haha — like_map phải tách số đếm theo từng cảm xúc.
    service.toggle_like(db, p.id, bo_may.khac_phong.id, int(ForumReactionKind.HAHA))
    lk = service.like_map(db, [p.id], nguoi)[p.id]
    assert lk["count"] == 2
    assert lk["my_reaction"] == int(ForumReactionKind.LOVE)
    assert lk["reactions"] == {int(ForumReactionKind.LOVE): 1, int(ForumReactionKind.HAHA): 1}

    # Danh sách người bấm mang kèm kind để FE lọc theo tab cảm xúc.
    assert service.reaction_users(db, p.id) == [
        (nguoi, int(ForumReactionKind.LOVE)),
        (bo_may.khac_phong.id, int(ForumReactionKind.HAHA)),
    ]

    with pytest.raises(HTTPException) as err:
        service.toggle_like(db, p.id, nguoi, 99)
    assert err.value.status_code == 400

    # Bấm lại đúng cảm xúc đang có là bỏ — không sót dòng mồ côi.
    out = service.toggle_like(db, p.id, nguoi, int(ForumReactionKind.LOVE))
    assert out["my_reaction"] == 0
    assert out["reactions"] == {int(ForumReactionKind.HAHA): 1}


def test_xoa_bai_cuon_theo_comment_va_like(db, bo_may):
    from app.modules.comment.model import Comment
    from app.modules.comment.service import create_comment
    from app.modules.forum.model import ForumReaction

    p = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    pid = p.id
    service.toggle_like(db, pid, bo_may.cung_phong.id)
    c = create_comment(db, "forum_post", pid, "gốc", bo_may.cung_phong.id)
    create_comment(db, "forum_post", pid, "trả lời", bo_may.tac_gia.id, parent_id=c.id)

    service.delete_post(db, db.get(ForumPost, pid))
    assert db.get(ForumPost, pid) is None
    assert db.query(Comment).filter(Comment.entity == "forum_post",
                                    Comment.entity_id == pid).count() == 0
    assert db.query(ForumReaction).filter(ForumReaction.post_id == pid).count() == 0


# ── F10. Bài sự kiện đổi ảnh đại diện (kind) ───────────────────────────────────

def _anh(db, user, key):
    from app.modules.attachment.model import StoredFile
    f = StoredFile(filename=f"{key}.jpg", file_key=key, url=f"u-{key}",
                   content_type="image/jpeg", size=1, sha256=f"s-{key}",
                   created_by=user.id, updated_by=user.id)
    db.add(f)
    db.commit()
    return f.id


def test_bai_avatar_f10_rang_buoc_kind(db, bo_may):
    """kind lạ bị 400; AVATAR_UPDATE bắt buộc ĐÚNG 1 ảnh (0 hay 2 đều 400)."""
    from app.modules.forum.model import ForumPostKind
    u = bo_may.tac_gia
    prof = get_perm_profile(db, u)
    hai_anh = [_anh(db, u, "k-a"), _anh(db, u, "k-b")]
    for body, files, kind in [("ok", [], 9),                                   # kind lạ
                              ("ok", [], int(ForumPostKind.AVATAR_UPDATE)),    # 0 ảnh
                              ("ok", hai_anh, int(ForumPostKind.AVATAR_UPDATE))]:  # 2 ảnh
        with pytest.raises(HTTPException) as e:
            service.create_post(db, u, prof, body, int(ForumAudience.PUBLIC), files, kind)
        assert e.value.status_code == 400


# ── F5. Kiểm duyệt: ẩn/xóa/khôi phục + chuông cho tác giả ──────────────────────

def _admin(db, bo_may, grant_role):
    admin = bo_may.khac_cty
    grant_role(admin.id, "forum_post", scope="all", read=True, write=True, delete=True)
    return admin


def test_an_bai_khong_ly_do_bi_400(db, bo_may, grant_role):
    """Điều kiện đủ F5: không có đường "ẩn lặng lẽ" (QĐ-D1)."""
    from app.modules.forum.model import ForumModerationAction
    admin = _admin(db, bo_may, grant_role)
    p = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    for reason in ("", "   "):
        with pytest.raises(HTTPException) as e:
            service.moderate(db, admin, p, ForumModerationAction.HIDE, reason)
        assert e.value.status_code == 400
    with pytest.raises(HTTPException) as e:
        service.moderate(db, admin, p, ForumModerationAction.REMOVE, "")
    assert e.value.status_code == 400
    assert int(p.status) == int(ForumPostStatus.PUBLISHED)   # chưa gì đổi cả


def test_an_bai_khoi_feed_nhung_tac_gia_va_admin_con_thay(db, bo_may, grant_role):
    """Điều kiện đủ F5: bài ẩn biến khỏi feed mọi người, còn ở trang cá nhân
    tác giả và mắt admin — kèm nhãn lý do."""
    from app.modules.forum.model import ForumModerationAction, ForumModerationLog
    admin = _admin(db, bo_may, grant_role)
    p = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    service.moderate(db, admin, p, ForumModerationAction.HIDE, "sai quy định nội bộ")

    assert p.id not in _feed_ids(db, bo_may.cung_phong)                      # feed người thường
    assert p.id in _feed_ids(db, bo_may.tac_gia, author_id=bo_may.tac_gia.id)  # trang cá nhân mình
    assert p.id in _feed_ids(db, admin)                                      # admin thấy để dọn
    assert service.hidden_reason_map(db, [p.id]) == {p.id: "sai quy định nội bộ"}
    log = db.query(ForumModerationLog).filter_by(post_id=p.id).one()
    assert log.action == int(ForumModerationAction.HIDE) and log.created_by == admin.id
    # tác giả vẫn mở được trang bài của mình (kèm nhãn), người ngoài thì 403
    assert service.get_visible_post(db, bo_may.tac_gia, p.id).id == p.id
    with pytest.raises(HTTPException):
        service.get_visible_post(db, bo_may.cung_phong, p.id)


def test_chuyen_trang_thai_kiem_duyet_dung_luat(db, bo_may, grant_role):
    """HIDE chỉ từ PUBLISHED, RESTORE chỉ từ HIDDEN; REMOVE đi từ cả hai."""
    from app.modules.forum.model import ForumModerationAction
    admin = _admin(db, bo_may, grant_role)
    p = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    with pytest.raises(HTTPException) as e:                    # restore bài đang hiện
        service.moderate(db, admin, p, ForumModerationAction.RESTORE, "")
    assert e.value.status_code == 400
    service.moderate(db, admin, p, ForumModerationAction.HIDE, "lý do")
    with pytest.raises(HTTPException) as e:                    # ẩn bài đã ẩn
        service.moderate(db, admin, p, ForumModerationAction.HIDE, "lý do")
    assert e.value.status_code == 400
    service.moderate(db, admin, p, ForumModerationAction.RESTORE, "")
    assert int(p.status) == int(ForumPostStatus.PUBLISHED)
    assert p.id in _feed_ids(db, bo_may.cung_phong)            # về lại feed
    service.moderate(db, admin, p, ForumModerationAction.HIDE, "lần hai")
    service.moderate(db, admin, p, ForumModerationAction.REMOVE, "vi phạm nặng")
    assert int(p.status) == int(ForumPostStatus.REMOVED)


def test_xoa_kiem_duyet_giu_dong_va_tac_gia_het_duong_xoa(db, bo_may, grant_role):
    """REMOVE giữ dòng + nhật ký để đối soát; bài biến khỏi mọi mắt kể cả tác
    giả, và tác giả cũng không xóa vật lý được nữa (mất dấu là mất chứng cứ)."""
    from app.modules.forum import controller
    from app.modules.forum.model import ForumModerationAction
    admin = _admin(db, bo_may, grant_role)
    p = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    service.moderate(db, admin, p, ForumModerationAction.REMOVE, "vi phạm")

    assert db.get(ForumPost, p.id) is not None                 # dòng còn nguyên
    assert not service.can_view(db, bo_may.tac_gia, p)         # tác giả cũng hết thấy
    assert p.id not in _feed_ids(db, bo_may.tac_gia, author_id=bo_may.tac_gia.id)
    with pytest.raises(HTTPException) as e:
        controller.delete_post(p.id, db=db, user=bo_may.tac_gia)
    assert e.value.status_code == 404


def test_an_bai_tac_gia_nhan_dung_mot_chuong(db, bo_may, grant_role):
    """Điều kiện đủ F5: tác giả nhận đúng MỘT chuông kèm lý do; admin tự xử bài
    mình thì không tự báo mình. `notified_at` ghi lên nhật ký để đối soát."""
    from app.modules.forum import controller, schema
    from app.modules.forum.model import ForumModerationLog
    from app.modules.notification.model import Notification
    admin = _admin(db, bo_may, grant_role)
    p = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    controller.hide_post(p.id, schema.ModerationIn(reason="đăng nhầm nhóm"), None,
                         db=db, user=admin)

    chuong = db.query(Notification).filter_by(user_id=bo_may.tac_gia.id).all()
    assert len(chuong) == 1
    assert "đăng nhầm nhóm" in chuong[0].body and chuong[0].link == f"/forum/posts/{p.id}"
    assert db.query(ForumModerationLog).filter_by(post_id=p.id).one().notified_at is not None

    # admin ẩn bài CỦA CHÍNH MÌNH: không sinh chuông nào thêm
    cua_admin = _dang(db, admin, ForumAudience.PUBLIC)
    controller.hide_post(cua_admin.id, schema.ModerationIn(reason="tự dọn"), None,
                         db=db, user=admin)
    assert db.query(Notification).filter_by(user_id=admin.id).count() == 0


def test_bai_avatar_f10_caption_rong_van_dang_duoc(db, bo_may):
    """Caption để trống + đúng 1 ảnh là hợp lệ — dòng hệ thống thay lời; `kind`
    lưu SMALLINT và đi ra ngoài qua PostOut cho FE vẽ."""
    from app.modules.forum.model import ForumPostKind
    u = bo_may.tac_gia
    p = service.create_post(db, u, get_perm_profile(db, u), "",
                            int(ForumAudience.PUBLIC), [_anh(db, u, "k-av")],
                            int(ForumPostKind.AVATAR_UPDATE))
    assert p.kind == int(ForumPostKind.AVATAR_UPDATE) and p.body == ""
    assert [a["file_id"] for a in service.image_map(db, [p.id])[p.id]]
    # bài thường không truyền kind thì mặc định NORMAL
    p2 = _dang(db, u, ForumAudience.PUBLIC)
    assert p2.kind == int(ForumPostKind.NORMAL)


# ── F9a (CR-199). Ghim bài + dải Thông báo ─────────────────────────────────────

def _pinned_ids(db, user):
    from app.core.auth import get_perm_profile
    rows = service.list_pinned_posts(db, user, get_perm_profile(db, user))
    return [p.id for p in rows]


def test_ghim_va_bo_ghim(db, bo_may, grant_role):
    """Ghim xong bài vào dải Thông báo mới → cũ theo MỐC GHIM (không theo lúc
    đăng); bỏ ghim là rời dải nhưng bài vẫn nguyên trên feed thường."""
    admin = _admin(db, bo_may, grant_role)
    cu = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC, "thông báo cũ")
    moi = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC, "thông báo mới")
    assert _pinned_ids(db, bo_may.cung_phong) == []

    # ghim bài ĐĂNG SAU trước — dải phải sắp theo mốc ghim, bài `cu` lên đầu
    service.set_post_pinned(db, admin, moi, True)
    service.set_post_pinned(db, admin, cu, True)
    assert cu.pinned_at is not None
    assert _pinned_ids(db, bo_may.cung_phong) == [cu.id, moi.id]

    # ghim lại bài đang ghim không đổi mốc (không nhảy đầu dải vô cớ)
    moc = cu.pinned_at
    service.set_post_pinned(db, admin, cu, True)
    assert cu.pinned_at == moc

    service.set_post_pinned(db, admin, cu, False)
    assert cu.pinned_at is None
    assert _pinned_ids(db, bo_may.cung_phong) == [moi.id]
    assert cu.id in _feed_ids(db, bo_may.cung_phong)   # feed thường vẫn còn


def test_dai_ghim_van_theo_luat_audience(db, bo_may, grant_role):
    """Ghim không phá luật audience: thông báo phạm vi phòng ban ghim lên thì
    phòng khác vẫn không thấy — cả trên dải ghim lẫn feed."""
    admin = _admin(db, bo_may, grant_role)
    p = _dang(db, bo_may.tac_gia, ForumAudience.DEPT, "họp phòng cuối tuần")
    service.set_post_pinned(db, admin, p, True)
    assert p.id in _pinned_ids(db, bo_may.cung_phong)
    assert p.id not in _pinned_ids(db, bo_may.khac_phong)


def test_ghim_bai_an_bi_chan_va_bai_ghim_bi_an_roi_dai(db, bo_may, grant_role):
    """Ghim bài đang ẩn phải 400 (treo thông báo không ai đọc được); bài ghim
    bị ẩn SAU ĐÓ tự rời dải của người thường nhưng admin còn thấy để dọn."""
    from app.modules.forum.model import ForumModerationAction
    admin = _admin(db, bo_may, grant_role)
    p = _dang(db, bo_may.tac_gia, ForumAudience.PUBLIC)
    service.moderate(db, admin, p, ForumModerationAction.HIDE, "sai chỗ")
    with pytest.raises(HTTPException) as e:
        service.set_post_pinned(db, admin, p, True)
    assert e.value.status_code == 400

    service.moderate(db, admin, p, ForumModerationAction.RESTORE, "")
    service.set_post_pinned(db, admin, p, True)
    service.moderate(db, admin, p, ForumModerationAction.HIDE, "hết hiệu lực")
    assert p.id not in _pinned_ids(db, bo_may.cung_phong)
    assert p.id in _pinned_ids(db, admin)
    # bỏ ghim bài đang ẩn vẫn được — dọn dẹp không kẹt luật trạng thái
    service.set_post_pinned(db, admin, p, False)
    assert p.pinned_at is None
