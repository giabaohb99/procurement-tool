"""Test cây bài viết Hướng dẫn sử dụng: chuyển thư mục cha + chặn vòng lặp + xóa nhánh + tìm kiếm."""
import pytest
from fastapi import HTTPException
from sqlalchemy import text

from app.modules.help_center import home_service, service
from app.modules.help_center.home_schema import (HelpHomeItemCreate,
                                                  HelpHomeItemUpdate,
                                                  HelpHomeSectionUpdate)
from app.modules.help_center.model import HelpArticle, HelpHomeItem, HelpHomeSection
from app.modules.help_center.schema import HelpArticleCreate, HelpArticleUpdate


@pytest.fixture(autouse=True)
def enforce_foreign_keys(db):
    """SQLite mặc định KHÔNG cưỡng chế khóa ngoại — bật lên để test xóa nhánh
    phát hiện được lỗi thứ tự DELETE (MySQL thật sẽ báo lỗi 1451)."""
    db.execute(text("PRAGMA foreign_keys=ON"))


@pytest.fixture
def tree(db):
    """goc > con > chau (3 cấp)."""
    origin = service.create_article(db, HelpArticleCreate(title="Muc goc"), user_id=1)
    con = service.create_article(db, HelpArticleCreate(title="Bai con", parent_id=origin.id), user_id=1)
    chau = service.create_article(db, HelpArticleCreate(title="Bai chi tiet", parent_id=con.id), user_id=1)
    return origin, con, chau


# ── Chuyển thư mục cha ──────────────────────────────────────────────────────────

def test_chuyen_bai_sang_cha_khac(db, tree):
    origin, con, _ = tree
    goc2 = service.create_article(db, HelpArticleCreate(title="Muc goc 2"), user_id=1)

    service.update_article(db, con.id, HelpArticleUpdate(parent_id=goc2.id), user_id=1)

    assert db.get(HelpArticle, con.id).parent_id == goc2.id


def test_dua_bai_ve_muc_goc(db, tree):
    """Gửi parent_id=null phải đưa bài lên cấp gốc (không phải bỏ qua)."""
    _, con, _ = tree

    service.update_article(db, con.id, HelpArticleUpdate(parent_id=None), user_id=1)

    assert db.get(HelpArticle, con.id).parent_id is None


def test_khong_gui_parent_id_thi_giu_nguyen_cha(db, tree):
    origin, con, _ = tree

    service.update_article(db, con.id, HelpArticleUpdate(title="Ten moi"), user_id=1)

    article = db.get(HelpArticle, con.id)
    assert article.title == "Ten moi"
    assert article.parent_id == origin.id


# ── Chặn vòng lặp cây ───────────────────────────────────────────────────────────

def test_chan_dat_lam_cha_cua_chinh_no(db, tree):
    _, con, _ = tree

    with pytest.raises(HTTPException) as e:
        service.update_article(db, con.id, HelpArticleUpdate(parent_id=con.id), user_id=1)
    assert e.value.status_code == 400


def test_chan_chuyen_vao_bai_con_cua_chinh_no(db, tree):
    """goc -> con: không được đặt `con` làm cha của `goc` (tạo vòng lặp)."""
    origin, con, _ = tree

    with pytest.raises(HTTPException) as e:
        service.update_article(db, origin.id, HelpArticleUpdate(parent_id=con.id), user_id=1)
    assert e.value.status_code == 400
    assert db.get(HelpArticle, origin.id).parent_id is None


def test_chan_chuyen_vao_bai_chau_cua_chinh_no(db, tree):
    """Vòng lặp gián tiếp qua 2 cấp cũng phải bị chặn."""
    origin, _, chau = tree

    with pytest.raises(HTTPException) as e:
        service.update_article(db, origin.id, HelpArticleUpdate(parent_id=chau.id), user_id=1)
    assert e.value.status_code == 400


def test_chan_cha_khong_ton_tai(db, tree):
    _, con, _ = tree

    with pytest.raises(HTTPException) as e:
        service.update_article(db, con.id, HelpArticleUpdate(parent_id=999999), user_id=1)
    assert e.value.status_code == 404


# ── Xóa cả nhánh ────────────────────────────────────────────────────────────────

def test_xoa_muc_goc_xoa_luon_toan_bo_nhanh(db, tree):
    origin, con, chau = tree

    service.delete_article(db, origin.id, user_id=1)

    assert db.get(HelpArticle, origin.id) is None
    assert db.get(HelpArticle, con.id) is None
    assert db.get(HelpArticle, chau.id) is None


def test_xoa_nhanh_khong_dung_toi_nhanh_khac(db, tree):
    origin, _, _ = tree
    other = service.create_article(db, HelpArticleCreate(title="Muc goc khac"), user_id=1)

    service.delete_article(db, origin.id, user_id=1)

    assert db.get(HelpArticle, other.id) is not None


def test_dem_so_bai_trong_nhanh(db, tree):
    origin, con, _ = tree

    assert service.count_branch(db, origin.id) == 3   # goc + con + chau
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


# ── Cấu hình hiển thị trang chủ (4 khung cố định) ────────────────────────────────

@pytest.fixture
def home_sections(db):
    """4 khung giống seed thật, trả dict key -> HelpHomeSection."""
    sections = {
        key: HelpHomeSection(key=key, title=title, is_visible=True, sort_order=i)
        for i, (key, title) in enumerate([
            ("quick_start", "Bắt đầu ngay"), ("categories", "Các Phân hệ"),
            ("faq", "Không tìm thấy điều bạn cần?"), ("tips", "Mẹo tra cứu"),
        ])
    }
    db.add_all(sections.values())
    db.commit()
    for s in sections.values():
        db.refresh(s)
    return sections


def test_them_bai_viet_vao_khung_quick_start(db, home_sections):
    article = service.create_article(db, HelpArticleCreate(title="Bat dau", summary="Mo ta"), user_id=1)

    item = home_service.add_home_item(
        db, home_sections["quick_start"].id,
        HelpHomeItemCreate(article_id=article.id, background_image="/x.png", gradient="blue"),
        user_id=1,
    )

    assert item["article_id"] == article.id
    assert item["article_title"] == "Bat dau"
    assert item["article_summary"] == "Mo ta"
    assert item["background_image"] == "/x.png"
    assert item["gradient"] == "blue"


def test_chan_them_trung_bai_viet_trong_cung_khung(db, home_sections):
    article = service.create_article(db, HelpArticleCreate(title="Bat dau"), user_id=1)
    home_service.add_home_item(db, home_sections["quick_start"].id,
                               HelpHomeItemCreate(article_id=article.id), user_id=1)

    with pytest.raises(HTTPException) as e:
        home_service.add_home_item(db, home_sections["quick_start"].id,
                                   HelpHomeItemCreate(article_id=article.id), user_id=1)
    assert e.value.status_code == 400


def test_khong_chan_bai_viet_trung_o_khung_khac(db, home_sections):
    """Cùng 1 bài viết vẫn được gắn vào khung categories dù đã có ở quick_start."""
    article = service.create_article(db, HelpArticleCreate(title="Bat dau"), user_id=1)
    home_service.add_home_item(db, home_sections["quick_start"].id,
                               HelpHomeItemCreate(article_id=article.id), user_id=1)

    item = home_service.add_home_item(db, home_sections["categories"].id,
                                      HelpHomeItemCreate(article_id=article.id), user_id=1)

    assert item["article_id"] == article.id


@pytest.mark.parametrize("section_key", ["faq", "tips"])
def test_chan_them_bai_viet_vao_khung_faq_tips(db, home_sections, section_key):
    article = service.create_article(db, HelpArticleCreate(title="Bat dau"), user_id=1)

    with pytest.raises(HTTPException) as e:
        home_service.add_home_item(db, home_sections[section_key].id,
                                   HelpHomeItemCreate(article_id=article.id), user_id=1)
    assert e.value.status_code == 400


def test_xoa_duoc_background_image_ve_null(db, home_sections):
    article = service.create_article(db, HelpArticleCreate(title="Bat dau"), user_id=1)
    item = home_service.add_home_item(
        db, home_sections["quick_start"].id,
        HelpHomeItemCreate(article_id=article.id, background_image="/x.png", gradient="blue"),
        user_id=1,
    )

    updated = home_service.update_home_item(
        db, item["id"], HelpHomeItemUpdate(background_image=None), user_id=1
    )

    assert updated["background_image"] is None
    assert updated["gradient"] == "blue"   # không gửi -> giữ nguyên


def test_khong_gui_field_thi_giu_nguyen(db, home_sections):
    article = service.create_article(db, HelpArticleCreate(title="Bat dau"), user_id=1)
    item = home_service.add_home_item(
        db, home_sections["quick_start"].id,
        HelpHomeItemCreate(article_id=article.id, background_image="/x.png"),
        user_id=1,
    )

    updated = home_service.update_home_item(db, item["id"], HelpHomeItemUpdate(sort_order=5), user_id=1)

    assert updated["background_image"] == "/x.png"
    assert updated["sort_order"] == 5


def test_xoa_item_khoi_khung(db, home_sections):
    article = service.create_article(db, HelpArticleCreate(title="Bat dau"), user_id=1)
    item = home_service.add_home_item(db, home_sections["quick_start"].id,
                                      HelpHomeItemCreate(article_id=article.id), user_id=1)

    home_service.delete_home_item(db, item["id"], user_id=1)

    assert db.get(HelpHomeItem, item["id"]) is None


def test_xoa_bai_viet_thi_item_bien_mat_khoi_khung(db, home_sections):
    """FK CASCADE: xóa bài viết gốc phải tự động dọn luôn item gắn ở trang chủ."""
    article = service.create_article(db, HelpArticleCreate(title="Bat dau"), user_id=1)
    home_service.add_home_item(db, home_sections["quick_start"].id,
                               HelpHomeItemCreate(article_id=article.id), user_id=1)

    service.delete_article(db, article.id, user_id=1)

    sections = home_service.get_home_sections(db)
    quick_start = next(s for s in sections if s["key"] == "quick_start")
    assert quick_start["items"] == []


def test_cap_nhat_khung_doi_tieu_de_va_an_hien(db, home_sections):
    updated = home_service.update_home_section(
        db, home_sections["tips"].id,
        HelpHomeSectionUpdate(title="Meo moi", is_visible=False), user_id=1,
    )

    assert updated["title"] == "Meo moi"
    assert updated["is_visible"] is False


def test_get_home_sections_sap_theo_sort_order(db, home_sections):
    sections = home_service.get_home_sections(db)
    assert [s["key"] for s in sections] == ["quick_start", "categories", "faq", "tips"]
