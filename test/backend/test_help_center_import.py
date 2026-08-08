"""Nhập bài viết Help Center từ file HTML / Markdown (CR-053).

Trọng tâm là BỘ LỌC HTML. File nhập vào đến từ ngoài hệ thống (soạn bằng trình khác, xuất từ
AI, chép từ web) và nội dung bài viết được render bằng `dangerouslySetInnerHTML` ở khu người
đọc — lọt một thẻ chạy được là dính XSS lưu trữ, kẻ tấn công đọc được phiên của mọi người vào
xem tài liệu. Nên mỗi đường vào phải có test riêng, sửa bộ lọc sau này mà hở là test đỏ ngay.
"""
import pytest

from app.modules.help_center import service
from app.modules.help_center.import_service import (MAX_FILE_SIZE, parse_file,
                                                    sanitize_html)
from app.modules.help_center.schema import HelpArticleCreate

# ── Bộ lọc HTML: những gì phải CHẶN ─────────────────────────────────────────────


@pytest.mark.parametrize("tag", ["script", "style", "noscript", "template"])
def test_bo_ca_ruot_cua_the_chay_duoc(tag):
    """Bỏ mỗi cái thẻ là chưa đủ: mã JS/CSS bên trong sẽ rơi ra thành chữ hiển thị."""
    out = sanitize_html(f"<p>truoc</p><{tag}>alert(1)</{tag}><p>sau</p>")

    assert "alert(1)" not in out
    assert out == "<p>truoc</p><p>sau</p>"


def test_bo_srcdoc_cua_iframe():
    """`srcdoc` là NGUYÊN một trang HTML nhét vào thuộc tính, chạy CÙNG ORIGIN với trang cha
    nên script trong đó đọc được token của người xem. Chặn cả khi viết hoa lẫn lộn."""
    out = sanitize_html('<iframe SrcDoc="&lt;script&gt;alert(1)&lt;/script&gt;"></iframe>')

    assert "srcdoc" not in out.lower()
    assert "<script>" not in out


def test_giu_iframe_nhung_video():
    """Bỏ srcdoc nhưng KHÔNG được bỏ luôn iframe — bài hướng dẫn có nhúng video."""
    out = sanitize_html('<iframe src="https://www.youtube.com/embed/abc" allowfullscreen></iframe>')

    assert out == '<iframe src="https://www.youtube.com/embed/abc" allowfullscreen=""></iframe>'


@pytest.mark.parametrize("handler", [
    '<img src="x" onerror="alert(1)">',
    '<div onclick="alert(1)">x</div>',
    '<body onload="alert(1)">x</body>',
    '<p ONMOUSEOVER="alert(1)">x</p>',
])
def test_bo_moi_thuoc_tinh_on(handler):
    out = sanitize_html(handler)

    assert "alert(1)" not in out


@pytest.mark.parametrize("url", [
    "javascript:alert(1)",
    "JaVaScRiPt:alert(1)",
    "  javascript:alert(1)",          # khoảng trắng đầu
    "java\nscript:alert(1)",          # xuống dòng chèn giữa
    "vbscript:msgbox(1)",
    "data:text/html;base64,PHNjcmlwdD4=",
])
def test_chan_url_chay_duoc(url):
    out = sanitize_html(f'<a href="{url}">bam vao day</a>')

    assert "href" not in out
    assert out == "<a>bam vao day</a>"       # chữ vẫn giữ, chỉ mất đường dẫn


def test_chan_javascript_viet_bang_ma_thuc_the():
    """`&#58;` là dấu hai chấm — HTMLParser tự giải mã nên phải chặn được sau khi giải."""
    out = sanitize_html('<a href="javascript&#58;alert(1)">x</a>')

    assert "href" not in out


def test_cho_qua_anh_dan_inline():
    """Quill dán ảnh vào bài dưới dạng data:image — chặn nhầm là mất ảnh."""
    src = "data:image/png;base64,iVBORw0KGgo="
    out = sanitize_html(f'<img src="{src}">')

    assert out == f'<img src="{src}">'


def test_bo_the_la_nhung_giu_chu_ben_trong():
    out = sanitize_html("<marquee>chu quan trong</marquee>")

    assert out == "chu quan trong"


def test_thoat_dau_ngoac_trong_phan_chu():
    """Chữ có < > phải thành &lt; &gt;, không thì trình duyệt đọc lại thành thẻ."""
    out = sanitize_html("<p>so sanh a &lt; b</p>")

    assert out == "<p>so sanh a &lt; b</p>"


def test_thoat_dau_nhay_trong_gia_tri_thuoc_tinh():
    """Không thoát dấu nháy kép là chèn được thuộc tính mới vào thẻ đang mở.
    Chữ `onmouseover` vẫn còn nhưng phải nằm gọn trong giá trị (dấu nháy đã thành &quot;)."""
    out = sanitize_html('<a title=\'x" onmouseover="alert(1)\'>x</a>')

    assert 'onmouseover="' not in out
    assert "&quot;" in out


# ── Bộ lọc HTML: những gì phải GIỮ ──────────────────────────────────────────────


def test_giu_cau_truc_bai_viet():
    html = ('<h2>Muc</h2><p><strong>dam</strong> va <em>nghieng</em></p>'
            '<ul><li>mot</li><li>hai</li></ul>'
            '<table><thead><tr><th>Cot</th></tr></thead><tbody><tr><td>O</td></tr></tbody></table>'
            '<a href="https://degoholding.vn" target="_blank" rel="noopener">lien ket</a>')

    assert sanitize_html(html) == html


def test_giu_class_va_style_de_khong_vo_dinh_dang():
    out = sanitize_html('<p class="ghi-chu" style="text-align:center">x</p>')

    assert out == '<p class="ghi-chu" style="text-align:center">x</p>'


# ── parse_file: kiểm tra đầu vào ────────────────────────────────────────────────


@pytest.mark.parametrize("filename", ["virus.exe", "bang.xlsx", "khong-co-duoi"])
def test_tu_choi_duoi_file_la(filename):
    with pytest.raises(ValueError, match="Chỉ nhận file"):
        parse_file(filename, b"<p>x</p>")


def test_tu_choi_file_qua_2mb():
    with pytest.raises(ValueError, match="2MB"):
        parse_file("to.html", b"x" * (MAX_FILE_SIZE + 1))


def test_nhan_file_dung_bang_2mb():
    """Chặn ở NGƯỠNG chứ không chặn tại đúng mốc — file 2MB chẵn vẫn phải nhận."""
    parsed = parse_file("vua-du.html", b"<p>x</p>" + b" " * (MAX_FILE_SIZE - 8))

    assert parsed["content"] == "<p>x</p>"


def test_doc_duoc_file_ma_hoa_cu():
    """File xuất từ Word bản Việt hay là cp1258/cp1252, không được ném lỗi giải mã."""
    parsed = parse_file("cu.html", "<p>C\xe0 ph\xea</p>".encode("cp1252"))

    assert "ph" in parsed["content"]


# ── parse_file: lấy tiêu đề ─────────────────────────────────────────────────────


def test_lay_tieu_de_tu_h1_va_bo_the_do_khoi_noi_dung():
    """Trang đã hiện tiêu đề riêng ở đầu bài — để lại <h1> là tiêu đề hiện hai lần."""
    parsed = parse_file("bo-qua.html", b"<h1>Huong dan tao YCMH</h1><p>Buoc 1</p>")

    assert parsed["title"] == "Huong dan tao YCMH"
    assert parsed["content"] == "<p>Buoc 1</p>"


def test_lay_tieu_de_tu_the_title_khi_khong_co_h1():
    """<title> nằm trong <head>; phải lấy TRƯỚC khi cắt lấy <body>, không thì mất trắng
    và tiêu đề bị rơi về tên file."""
    raw = b"<html><head><title>Bao cao cong no</title></head><body><p>ND</p></body></html>"

    parsed = parse_file("tai-ve-123.html", raw)

    assert parsed["title"] == "Bao cao cong no"


def test_chu_trong_the_title_khong_lot_vao_noi_dung():
    """<title> không nằm trong danh sách thẻ cho phép nên bộ lọc bỏ thẻ mà giữ chữ —
    phải cắt hẳn thẻ đó ra, không thì đầu bài có một dòng chữ thừa."""
    parsed = parse_file("x.html", b"<title>Bao cao cong no</title><p>ND</p>")

    assert parsed["content"] == "<p>ND</p>"
    assert "Bao cao cong no" not in parsed["content"]


def test_h1_uu_tien_hon_title():
    raw = b"<html><head><title>Tu head</title></head><body><h1>Tu than bai</h1><p>ND</p></body></html>"

    assert parse_file("x.html", raw)["title"] == "Tu than bai"


def test_khong_co_tieu_de_thi_lay_ten_file():
    parsed = parse_file("Huong dan cong no.html", b"<p>ND</p>")

    assert parsed["title"] == "Huong dan cong no"


def test_ten_file_rong_thi_co_tieu_de_mac_dinh():
    assert parse_file(".html", b"<p>ND</p>")["title"] == "Bài viết mới"


def test_cat_tieu_de_qua_dai():
    parsed = parse_file("x.html", ("<h1>" + "a" * 400 + "</h1>").encode())

    assert len(parsed["title"]) == 255


# ── parse_file: nội dung ────────────────────────────────────────────────────────


def test_chi_lay_trong_body_cua_file_html_day_du():
    raw = (b"<!doctype html><html><head><style>p{color:red}</style></head>"
           b"<body><p>ND</p></body></html>")

    parsed = parse_file("x.html", raw)

    assert parsed["content"] == "<p>ND</p>"


def test_loc_html_ngay_ca_khi_nhap_tu_file():
    """Đường vào thật là parse_file — phải chắc nó có gọi bộ lọc, không chỉ sanitize_html."""
    parsed = parse_file("doc.html", b'<p>ND</p><script>alert(1)</script><img src=x onerror=alert(2)>')

    assert "alert" not in parsed["content"]


def test_markdown_thanh_html_giu_bang():
    md = b"# Bang gia\n\n| Ma | Gia |\n| --- | --- |\n| A1 | 10 |\n"

    parsed = parse_file("bang.md", md)

    assert parsed["title"] == "Bang gia"
    assert "<table>" in parsed["content"]
    assert "<th>Ma</th>" in parsed["content"]


def test_markdown_giu_khoi_code():
    parsed = parse_file("code.md", b"```\ndocker compose up\n```\n")

    assert "<code>" in parsed["content"]
    assert "docker compose up" in parsed["content"]


def test_markdown_khong_cho_html_tho_lot_qua():
    """Markdown cho phép nhúng HTML thẳng — vẫn phải qua bộ lọc."""
    parsed = parse_file("xss.md", b"Xin chao\n\n<script>alert(1)</script>\n")

    assert "alert(1)" not in parsed["content"]


def test_mo_ta_ngan_la_chu_tran_cat_250():
    parsed = parse_file("x.html", b"<h1>T</h1><p>" + b"a" * 400 + b"</p>")

    assert parsed["summary"] == "a" * 250


def test_bai_rong_thi_mo_ta_de_trong():
    parsed = parse_file("x.html", b"<h1>Chi co tieu de</h1>")

    assert parsed["summary"] is None
    assert parsed["content"] == ""


# ── Ghi đè bài trùng tiêu đề ────────────────────────────────────────────────────


def test_tim_bai_theo_dung_tieu_de(db):
    service.create_article(db, HelpArticleCreate(title="Cong no"), user_id=1)

    assert service.find_by_title(db, "Cong no") is not None
    assert service.find_by_title(db, "cong") is None       # khớp ĐÚNG, không khớp một phần


def test_thu_tu_bai_nhap_vao_nam_cuoi_muc(db):
    goc = service.create_article(db, HelpArticleCreate(title="Muc"), user_id=1)
    service.create_article(db, HelpArticleCreate(title="A", parent_id=goc.id, sort_order=3), user_id=1)
    service.create_article(db, HelpArticleCreate(title="B", parent_id=goc.id, sort_order=7), user_id=1)

    assert service.next_sort_order(db, goc.id) == 8


def test_thu_tu_trong_muc_rong_bat_dau_tu_1(db):
    goc = service.create_article(db, HelpArticleCreate(title="Muc"), user_id=1)

    assert service.next_sort_order(db, goc.id) == 1


def test_thu_tu_muc_goc_khong_dinh_muc_con(db):
    """Bài ở mục gốc và bài trong mục con đếm riêng, không được cộng nhầm sang nhau."""
    goc = service.create_article(db, HelpArticleCreate(title="Muc", sort_order=2), user_id=1)
    service.create_article(db, HelpArticleCreate(title="Con", parent_id=goc.id, sort_order=50), user_id=1)

    assert service.next_sort_order(db, None) == 3
