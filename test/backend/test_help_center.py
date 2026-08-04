"""Test cây bài viết Hướng dẫn sử dụng: chuyển thư mục cha + chặn vòng lặp + xóa nhánh + tìm kiếm."""
import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.modules.help_center import service
from app.modules.help_center.model import HelpArticle
from app.modules.help_center.schema import HelpArticleCreate, HelpArticleUpdate


@pytest.fixture(autouse=True)
def enforce_foreign_keys(db):
    """SQLite mặc định KHÔNG cưỡng chế khóa ngoại — bật lên để test xóa nhánh
    phát hiện được lỗi thứ tự DELETE (MySQL thật sẽ báo lỗi 1451)."""
    db.execute(text("PRAGMA foreign_keys=ON"))


@pytest.fixture
def tree(db):
    """goc > con > chau (3 cấp)."""
    goc = service.create_article(db, HelpArticleCreate(title="Muc goc"), user_id=1)
    con = service.create_article(db, HelpArticleCreate(title="Bai con", parent_id=goc.id), user_id=1)
    chau = service.create_article(db, HelpArticleCreate(title="Bai chi tiet", parent_id=con.id), user_id=1)
    return goc, con, chau


# ── Chuyển thư mục cha ──────────────────────────────────────────────────────────

def test_chuyen_bai_sang_cha_khac(db, tree):
    goc, con, _ = tree
    goc2 = service.create_article(db, HelpArticleCreate(title="Muc goc 2"), user_id=1)

    service.update_article(db, con.id, HelpArticleUpdate(parent_id=goc2.id), user_id=1)

    assert db.get(HelpArticle, con.id).parent_id == goc2.id


def test_dua_bai_ve_muc_goc(db, tree):
    """Gửi parent_id=null phải đưa bài lên cấp gốc (không phải bỏ qua)."""
    _, con, _ = tree

    service.update_article(db, con.id, HelpArticleUpdate(parent_id=None), user_id=1)

    assert db.get(HelpArticle, con.id).parent_id is None


def test_khong_gui_parent_id_thi_giu_nguyen_cha(db, tree):
    goc, con, _ = tree

    service.update_article(db, con.id, HelpArticleUpdate(title="Ten moi"), user_id=1)

    article = db.get(HelpArticle, con.id)
    assert article.title == "Ten moi"
    assert article.parent_id == goc.id


# ── Chặn vòng lặp cây ───────────────────────────────────────────────────────────

def test_chan_dat_lam_cha_cua_chinh_no(db, tree):
    _, con, _ = tree

    with pytest.raises(HTTPException) as e:
        service.update_article(db, con.id, HelpArticleUpdate(parent_id=con.id), user_id=1)
    assert e.value.status_code == 400


def test_chan_chuyen_vao_bai_con_cua_chinh_no(db, tree):
    """goc -> con: không được đặt `con` làm cha của `goc` (tạo vòng lặp)."""
    goc, con, _ = tree

    with pytest.raises(HTTPException) as e:
        service.update_article(db, goc.id, HelpArticleUpdate(parent_id=con.id), user_id=1)
    assert e.value.status_code == 400
    assert db.get(HelpArticle, goc.id).parent_id is None


def test_chan_chuyen_vao_bai_chau_cua_chinh_no(db, tree):
    """Vòng lặp gián tiếp qua 2 cấp cũng phải bị chặn."""
    goc, _, chau = tree

    with pytest.raises(HTTPException) as e:
        service.update_article(db, goc.id, HelpArticleUpdate(parent_id=chau.id), user_id=1)
    assert e.value.status_code == 400


def test_chan_cha_khong_ton_tai(db, tree):
    _, con, _ = tree

    with pytest.raises(HTTPException) as e:
        service.update_article(db, con.id, HelpArticleUpdate(parent_id=999999), user_id=1)
    assert e.value.status_code == 404


# ── Xóa cả nhánh ────────────────────────────────────────────────────────────────

def test_xoa_muc_goc_xoa_luon_toan_bo_nhanh(db, tree):
    goc, con, chau = tree

    service.delete_article(db, goc.id, user_id=1)

    assert db.get(HelpArticle, goc.id) is None
    assert db.get(HelpArticle, con.id) is None
    assert db.get(HelpArticle, chau.id) is None


def test_xoa_nhanh_khong_dung_toi_nhanh_khac(db, tree):
    goc, _, _ = tree
    khac = service.create_article(db, HelpArticleCreate(title="Muc goc khac"), user_id=1)

    service.delete_article(db, goc.id, user_id=1)

    assert db.get(HelpArticle, khac.id) is not None


def test_dem_so_bai_trong_nhanh(db, tree):
    goc, con, _ = tree

    assert service.count_branch(db, goc.id) == 3   # goc + con + chau
    assert service.count_branch(db, con.id) == 2   # con + chau


# ── Tìm kiếm theo nội dung ──────────────────────────────────────────────────────

def test_tim_kiem_khop_noi_dung_tra_ve_trich_doan(db):
    service.create_article(
        db,
        HelpArticleCreate(title="Bai huong dan", content="<p>Huong dan tao phieu mua hang moi</p>"),
        user_id=1,
    )

    hits = service.search_articles(db, "phieu mua hang")

    assert len(hits) == 1
    hit = hits[0]
    assert hit["in_title"] is False
    # match_at trỏ đúng vị trí từ khóa trong đoạn trích đã bỏ thẻ HTML
    assert hit["snippet"][hit["match_at"]:hit["match_at"] + hit["match_len"]].lower() == "phieu mua hang"


def test_tim_kiem_uu_tien_khop_tieu_de(db):
    service.create_article(db, HelpArticleCreate(title="Khac", content="<p>cong no</p>"), user_id=1)
    service.create_article(db, HelpArticleCreate(title="Cong no"), user_id=1)

    hits = service.search_articles(db, "cong no")

    assert [h["in_title"] for h in hits] == [True, False]
