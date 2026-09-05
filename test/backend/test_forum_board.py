"""F13a Diễn đàn — chuyên mục kiểu VOZ. Điều kiện đủ của phase
(doc/erp/dien-dan/02-lo-trinh-phase.md):

  1. box ẩn (hoặc không tồn tại, hoặc là nhóm tiêu đề) không nhận bài;
  2. có `board_id` mà thiếu tiêu đề bị 400;
  3. thread list phân trang không lặp / không sót;
  4. bài đăng vào box hiện CẢ trong feed lẫn thread list (QĐ-D7b);
  5. bộ đếm thread + bình luận của box khớp.

Kèm các chốt phụ: audience bị ÉP theo box (QĐ-D7a), prefix ngoài dải bị 400,
bộ mã `forum_prefix` (sinh TS) khớp dải `ForumPrefix`, xóa nhóm/box còn đồ bị
chặn, và sắp thread theo hoạt động cuối (comment mới kéo thread lên đầu).
Test gọi thẳng tầng service — khuôn `test_forum_api.py`.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.auth import get_perm_profile
from app.modules.forum import service
from app.modules.forum.model import (ForumAudience, ForumBoard, ForumBoardStatus,
                                     ForumPrefix)


def _board_in(**kw):
    """BoardIn giả tối thiểu — service chỉ đọc thuộc tính, không cần Pydantic."""
    base = {"name": "", "description": "", "icon": "", "parent_id": 0,
            "sort_order": 0, "status": int(ForumBoardStatus.ACTIVE)}
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.fixture()
def bo_may(db, seed):
    """Một tác giả (user seed) + một nhóm chứa một box đang mở."""
    from app.modules.user.model import User

    tac_gia = db.get(User, seed.u_req_id)
    nhom = service.create_board(db, tac_gia, _board_in(name="Chia sẻ"))
    box = service.create_board(db, tac_gia, _board_in(name="Kiến thức", parent_id=nhom.id,
                                                      icon="book"))
    return SimpleNamespace(tac_gia=tac_gia, nhom=nhom, box=box)


def _dang(db, user, box_id=0, title="", body="nội dung", prefix=0, audience=None,
          body_format=0):
    profile = get_perm_profile(db, user)
    return service.create_post(db, user, profile, body,
                               int(audience if audience is not None else ForumAudience.PUBLIC),
                               board_id=box_id, title=title, prefix=prefix,
                               body_format=body_format)


def _binh_luan(db, post, user_id, when):
    from app.modules.comment.model import Comment
    c = Comment(entity="forum_post", entity_id=post.id, body="cmt",
                created_by=user_id, updated_by=user_id)
    db.add(c)
    db.flush()
    c.created_at = when
    db.commit()
    return c


# ── 1+2. Cửa vào box ────────────────────────────────────────────────────────────

def test_box_an_khong_nhan_bai(db, bo_may):
    bo_may.box.status = int(ForumBoardStatus.HIDDEN)
    db.commit()
    with pytest.raises(HTTPException) as e:
        _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Chủ đề")
    assert e.value.status_code == 400


def test_nhom_cha_an_thi_box_cung_khong_nhan_bai(db, bo_may):
    bo_may.nhom.status = int(ForumBoardStatus.HIDDEN)
    db.commit()
    with pytest.raises(HTTPException) as e:
        _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Chủ đề")
    assert e.value.status_code == 400


def test_nhom_tieu_de_va_id_ma_khong_nhan_bai(db, bo_may):
    """Nhóm chỉ làm tiêu đề — đăng thẳng vào nhóm hay vào id không tồn tại đều 400."""
    for bid in (bo_may.nhom.id, 99_999):
        with pytest.raises(HTTPException) as e:
            _dang(db, bo_may.tac_gia, box_id=bid, title="Chủ đề")
        assert e.value.status_code == 400


def test_thieu_tieu_de_bi_400(db, bo_may):
    with pytest.raises(HTTPException) as e:
        _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="   ")
    assert e.value.status_code == 400


def test_prefix_ngoai_dai_bi_400(db, bo_may):
    with pytest.raises(HTTPException) as e:
        _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Chủ đề", prefix=99)
    assert e.value.status_code == 400


def test_audience_bi_ep_theo_box(db, bo_may):
    """QĐ-D7a: client đòi DEPT vẫn ra PUBLIC — audience của box thắng."""
    p = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Chủ đề",
              audience=ForumAudience.DEPT)
    assert int(p.audience) == int(ForumAudience.PUBLIC)


def test_bai_feed_thuan_bo_qua_title_prefix(db, bo_may):
    """Không có board_id thì title/prefix gửi kèm bị bỏ qua, không 400."""
    p = _dang(db, bo_may.tac_gia, title="tiêu đề lạc", prefix=3)
    assert p.board_id is None and p.title is None and int(p.prefix) == 0


# ── 3. Phân trang thread không lặp / không sót ─────────────────────────────────

def test_phan_trang_khong_lap_khong_sot(db, bo_may):
    goc = datetime(2026, 9, 1, 8, 0, 0)
    ids = []
    for i in range(5):
        p = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title=f"Chủ đề {i}")
        p.created_at = goc + timedelta(hours=i)
        ids.append(p.id)
    db.commit()
    profile = get_perm_profile(db, bo_may.tac_gia)

    trang1, total = service.list_board_threads(db, bo_may.tac_gia, profile,
                                               bo_may.box.id, page=1, per_page=2)
    trang2, _ = service.list_board_threads(db, bo_may.tac_gia, profile,
                                           bo_may.box.id, page=2, per_page=2)
    trang3, _ = service.list_board_threads(db, bo_may.tac_gia, profile,
                                           bo_may.box.id, page=3, per_page=2)
    assert total == 5
    thay = [p.id for p in trang1 + trang2 + trang3]
    assert sorted(thay) == sorted(ids)           # không sót
    assert len(set(thay)) == len(thay)           # không lặp
    assert [p.id for p in trang1] == [ids[4], ids[3]]   # hoạt động cuối trước


def test_comment_moi_keo_thread_len_dau(db, bo_may):
    """Sắp theo hoạt động cuối = max(bài, comment cuối) — box tự vận hành."""
    goc = datetime(2026, 9, 1, 8, 0, 0)
    cu = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Bài cũ")
    moi = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Bài mới")
    cu.created_at, moi.created_at = goc, goc + timedelta(hours=1)
    db.commit()
    _binh_luan(db, cu, bo_may.tac_gia.id, goc + timedelta(hours=2))

    profile = get_perm_profile(db, bo_may.tac_gia)
    rows, _ = service.list_board_threads(db, bo_may.tac_gia, profile, bo_may.box.id)
    assert [p.id for p in rows] == [cu.id, moi.id]


def test_last_comment_at_map_lay_moc_cuoi(db, bo_may):
    """Cột «hoạt động cuối» (F13b) dựa trên map này — phải là bình luận MUỘN
    NHẤT của từng bài, bài chưa có bình luận thì vắng mặt trong map."""
    goc = datetime(2026, 9, 1, 8, 0, 0)
    p1 = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Có bình luận")
    p2 = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Chưa có")
    _binh_luan(db, p1, bo_may.tac_gia.id, goc + timedelta(hours=1))
    _binh_luan(db, p1, bo_may.tac_gia.id, goc + timedelta(hours=2))

    m = service.last_comment_at_map(db, [p1.id, p2.id])
    assert m[p1.id] == goc + timedelta(hours=2)
    assert p2.id not in m
    assert service.last_comment_at_map(db, []) == {}


# ── 4. Bài box hiện cả feed lẫn thread list (QĐ-D7b) ───────────────────────────

def test_bai_box_hien_ca_feed_lan_thread_list(db, bo_may):
    p = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Chủ đề")
    profile = get_perm_profile(db, bo_may.tac_gia)
    feed_ids = [x.id for x in service.list_posts(db, bo_may.tac_gia, profile)]
    rows, _ = service.list_board_threads(db, bo_may.tac_gia, profile, bo_may.box.id)
    assert p.id in feed_ids
    assert p.id in [x.id for x in rows]


# ── 5. Bộ đếm + khối bài-mới-nhất của GET /boards ──────────────────────────────

def test_bo_dem_va_bai_moi_nhat(db, bo_may):
    goc = datetime(2026, 9, 1, 8, 0, 0)
    p1 = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Chủ đề 1")
    p2 = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Chủ đề 2", prefix=3)
    p1.created_at, p2.created_at = goc, goc + timedelta(hours=1)
    db.commit()
    _binh_luan(db, p1, bo_may.tac_gia.id, goc + timedelta(hours=2))
    _binh_luan(db, p1, bo_may.tac_gia.id, goc + timedelta(hours=3))

    groups = service.list_boards(db, bo_may.tac_gia)
    assert len(groups) == 1
    box = groups[0]["children"][0]
    assert box["id"] == bo_may.box.id and box["icon"] == "book"
    assert box["thread_count"] == 2
    assert box["comment_count"] == 2
    # comment cuối (trên p1) muộn hơn bài đăng mới nhất (p2) → khối bài-mới-nhất là p1
    assert box["last_post"]["post_id"] == p1.id
    assert box["last_post"]["last_user_id"] == bo_may.tac_gia.id
    assert box["last_post"]["title"] == "Chủ đề 1"


def test_box_an_bien_khoi_cay_voi_nguoi_thuong(db, bo_may, grant_role, seed):
    from app.modules.user.model import User
    bo_may.box.status = int(ForumBoardStatus.HIDDEN)
    db.commit()

    groups = service.list_boards(db, bo_may.tac_gia)
    assert groups[0]["children"] == []
    # admin (grant forum_post.read) vẫn thấy kèm status để dọn
    admin = db.get(User, seed.u_nstm_id)
    grant_role(admin.id, "forum_post", scope="all", read=True)
    groups = service.list_boards(db, admin)
    assert [b["id"] for b in groups[0]["children"]] == [bo_may.box.id]
    assert groups[0]["children"][0]["status"] == int(ForumBoardStatus.HIDDEN)


# ── F13c. Sidebar «Đang sôi nổi» + «Mới nhất» ──────────────────────────────────

def _tha_cam_xuc(db, post, user_id, when):
    from app.modules.forum.model import ForumReaction, ForumReactionKind
    r = ForumReaction(post_id=post.id, user_id=user_id,
                      kind=int(ForumReactionKind.LIKE),
                      created_by=user_id, updated_by=user_id)
    db.add(r)
    db.flush()
    r.created_at = when
    db.commit()
    return r


def test_soi_noi_xep_theo_diem_7_ngay(db, bo_may):
    """Điểm = bình luận + reaction TRONG 7 ngày; tương tác cũ hơn không tính,
    bài feed thuần (không board) tương tác mấy cũng không chen vào sidebar."""
    gan = datetime.now() - timedelta(days=1)
    xua = datetime.now() - timedelta(days=8)
    a = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Thread A")
    b = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Thread B")
    c = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Thread C")
    feed = _dang(db, bo_may.tac_gia, body="bài feed")
    _binh_luan(db, a, bo_may.tac_gia.id, gan)                 # A: 1 điểm
    _binh_luan(db, b, bo_may.tac_gia.id, gan)                 # B: 2 điểm
    _tha_cam_xuc(db, b, bo_may.tac_gia.id, gan)
    _binh_luan(db, c, bo_may.tac_gia.id, xua)                 # C: ngoài cửa sổ
    _binh_luan(db, c, bo_may.tac_gia.id, xua)
    _binh_luan(db, feed, bo_may.tac_gia.id, gan)              # feed: không phải thread

    profile = get_perm_profile(db, bo_may.tac_gia)
    trending, latest = service.list_highlight_threads(db, bo_may.tac_gia, profile)
    assert [p.id for p in trending] == [b.id, a.id]
    # «Mới nhất» toàn diễn đàn theo id giảm dần, KHÔNG dính cửa sổ 7 ngày
    assert [p.id for p in latest] == [c.id, b.id, a.id]


def test_sidebar_khong_lo_thread_cua_box_an(db, bo_may, grant_role, seed):
    """Thread nằm trong box ẩn phải biến khỏi CẢ hai khối với người thường —
    admin thì vẫn thấy (thấy hết mới dọn được, cùng luật thread list)."""
    from app.modules.user.model import User
    gan = datetime.now() - timedelta(days=1)
    p = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Trong box ẩn")
    _binh_luan(db, p, bo_may.tac_gia.id, gan)
    bo_may.box.status = int(ForumBoardStatus.HIDDEN)
    db.commit()

    profile = get_perm_profile(db, bo_may.tac_gia)
    trending, latest = service.list_highlight_threads(db, bo_may.tac_gia, profile)
    assert trending == [] and latest == []

    admin = db.get(User, seed.u_nstm_id)
    grant_role(admin.id, "forum_post", scope="all", read=True)
    trending, latest = service.list_highlight_threads(
        db, admin, get_perm_profile(db, admin))
    assert [x.id for x in trending] == [p.id]
    assert [x.id for x in latest] == [p.id]


# ── CRUD cấu trúc — các cửa chặn ───────────────────────────────────────────────

def test_khong_long_qua_hai_tang(db, bo_may):
    with pytest.raises(HTTPException) as e:
        service.create_board(db, bo_may.tac_gia,
                             _board_in(name="Tầng ba", parent_id=bo_may.box.id))
    assert e.value.status_code == 400


def test_xoa_nhom_con_box_va_box_con_bai_bi_chan(db, bo_may):
    with pytest.raises(HTTPException) as e:
        service.delete_board(db, bo_may.nhom)
    assert e.value.status_code == 400
    _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Chủ đề")
    with pytest.raises(HTTPException) as e:
        service.delete_board(db, bo_may.box)
    assert e.value.status_code == 400
    # box rỗng thì xóa được
    box2 = service.create_board(db, bo_may.tac_gia,
                                _board_in(name="Box rỗng", parent_id=bo_may.nhom.id))
    service.delete_board(db, box2)
    assert db.get(ForumBoard, box2.id) is None


def test_nhom_dang_chua_box_khong_ha_xuong_lam_box(db, bo_may):
    nhom2 = service.create_board(db, bo_may.tac_gia, _board_in(name="Nhóm hai"))
    with pytest.raises(HTTPException) as e:
        service.update_board(db, bo_may.tac_gia, bo_may.nhom,
                             _board_in(name="Chia sẻ", parent_id=nhom2.id))
    assert e.value.status_code == 400


# ── CR-261. Rich text cho bài viết ─────────────────────────────────────────────

def test_rich_body_duoc_sanitize_ngay_cua_ghi(db, bo_may):
    """script/onerror phải CHẾT tại service — DB không bao giờ chứa markup độc,
    kể cả khi FE quên lọc (bài học lỗ srcdoc của Help Center, 28/08)."""
    hiem = ('<p>xin <strong>chào</strong></p>'
            '<script>alert(1)</script>'
            '<img src="x" onerror="alert(2)">')
    p = _dang(db, bo_may.tac_gia, box_id=bo_may.box.id, title="Chủ đề",
              body=hiem, body_format=1)
    assert int(p.body_format) == 1
    assert '<strong>chào</strong>' in p.body   # định dạng lành được GIỮ
    assert 'script' not in p.body and 'alert' not in p.body


def test_rich_ap_ca_cho_bai_feed(db, bo_may):
    """Khách chốt 03/09: Bảng tin CŨNG có in đậm/đánh số như Facebook —
    body_format=1 không đòi board_id."""
    p = _dang(db, bo_may.tac_gia, body='<p>đậm <strong>nè</strong></p>',
              body_format=1)
    assert int(p.body_format) == 1 and p.board_id is None
    assert '<strong>nè</strong>' in p.body


def test_rich_toan_the_rong_la_bai_trong(db, bo_may):
    """`<p></p><p>&nbsp;</p>` nhìn như có chữ nhưng là bài trống — không ảnh
    thì 400; có ảnh thì đăng được và body quy về CHUỖI RỖNG, không lưu xác HTML."""
    with pytest.raises(HTTPException) as e:
        _dang(db, bo_may.tac_gia, body='<p></p><p>&nbsp;</p>', body_format=1)
    assert e.value.status_code == 400
    profile = get_perm_profile(db, bo_may.tac_gia)
    p = service.create_post(db, bo_may.tac_gia, profile, '<p> &nbsp; </p>',
                            int(ForumAudience.PUBLIC), file_ids=[999_999],
                            body_format=1)
    assert p.body == ""


def test_rich_dinh_dang_ngoai_dai_va_qua_tran_bi_400(db, bo_may):
    with pytest.raises(HTTPException) as e:
        _dang(db, bo_may.tac_gia, body="x", body_format=9)
    assert e.value.status_code == 400
    with pytest.raises(HTTPException) as e:
        _dang(db, bo_may.tac_gia,
              body='<p>' + 'a' * service.MAX_BODY_HTML + '</p>', body_format=1)
    assert e.value.status_code == 400


def test_bai_chu_tron_giu_nguyen_duong_cu(db, bo_may):
    """Bài PLAIN không qua sanitize — gõ `a < b` hay dán thẻ vào phải LƯU
    NGUYÊN VĂN (FE vẽ dạng chữ, không phải HTML)."""
    p = _dang(db, bo_may.tac_gia, body='a < b và <b>không phải đậm</b>')
    assert int(p.body_format) == 0
    assert p.body == 'a < b và <b>không phải đậm</b>'


# ── Bộ mã prefix sinh TS khớp dải IntEnum ──────────────────────────────────────

def test_bo_ma_forum_prefix_khop_enum():
    """`forum_codes.FORUM_PREFIX_SET` (nguồn nhãn cho FE qua gen_status_ts) phải
    cùng dải giá trị với `ForumPrefix` (nguồn giá trị lưu DB) — lệch là FE có
    prefix không nhãn hoặc nhãn không giá trị."""
    from app.core.forum_codes import FORUM_PREFIX_SET
    assert {int(v) for v in FORUM_PREFIX_SET.values} == {int(p) for p in ForumPrefix}
