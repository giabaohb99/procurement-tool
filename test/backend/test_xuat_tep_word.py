"""XUẤT TỆP WORD (.docx) — tự sinh OpenXML, không qua thư viện ngoài.

Cách kiểm chắc tay nhất ở đây là **đi vòng tròn**: sinh .docx rồi đọc lại bằng
chính bộ đọc đã có (`docx_html.docx_to_html`). Nếu XML sai chuẩn thì bộ đọc vỡ
ngay, khỏi phải mở Word ra nhìn.

Ngoài ra kiểm mấy chỗ mà sai thì Word **báo tệp hỏng** chứ không mở nửa vời:
thiếu một phần bắt buộc trong gói, hoặc thiếu khai kiểu MIME của ảnh.
"""
import re
import zipfile
from io import BytesIO

from app.modules.document.docx_html import docx_to_html
from app.modules.document.html_docx import html_to_docx

PHAN_BAT_BUOC = {
    "[Content_Types].xml",
    "_rels/.rels",
    "word/document.xml",
    "word/_rels/document.xml.rels",
    "word/styles.xml",
}


def _doc_lai(data: bytes) -> str:
    out = docx_to_html(data)
    return out["content_html"] if isinstance(out, dict) else str(out)


def _chu(data: bytes) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", _doc_lai(data))).strip()


def test_goi_co_du_phan_bat_buoc():
    """Thiếu một phần là Word báo 'tệp hỏng', không mở nửa vời."""
    z = zipfile.ZipFile(BytesIO(html_to_docx("<p>xin chào</p>")))

    assert PHAN_BAT_BUOC.issubset(set(z.namelist()))


def test_doc_lai_duoc_bang_chinh_bo_doc_docx():
    """Đi vòng tròn: sinh ra rồi đọc lại — XML sai chuẩn thì vỡ ngay ở đây."""
    data = html_to_docx("<p>Điều 1. Nội dung.</p>")

    assert "Điều 1. Nội dung." in _chu(data)


def test_giu_dam_nghieng_gach_chan_va_canh_le():
    data = html_to_docx(
        '<p style="text-align:center"><strong>ĐẬM</strong> <em>nghiêng</em> '
        '<u>gạch chân</u></p>'
    )
    html = _doc_lai(data)

    assert "<strong>" in html and "<em>" in html
    assert "center" in html


def test_giu_mau_chu_va_mau_nen():
    data = html_to_docx(
        '<p><span style="color:#C00000">đỏ</span>'
        '<span style="background-color:#FFFF00">nền</span></p>'
    )
    html = _doc_lai(data).upper()

    assert "C00000" in html
    assert "FFFF00" in html


def test_giu_bang_va_o():
    data = html_to_docx(
        "<table><tbody><tr><td><p>ô A</p></td><td><p>ô B</p></td></tr></tbody></table>"
    )
    html = _doc_lai(data)

    assert "<table" in html
    assert html.count("<td") == 2
    assert "ô A" in html and "ô B" in html


def test_o_khai_khong_vien_thi_word_cung_khong_ke():
    """Khối đầu văn bản hai cột dựng bằng bảng KHÔNG VIỀN — kẻ ô ra là hỏng thể thức."""
    xml = zipfile.ZipFile(BytesIO(html_to_docx(
        '<table><tbody><tr>'
        '<td style="border-top: hidden; border-left: hidden; border-bottom: hidden; '
        'border-right: hidden"><p>cơ quan</p></td>'
        '</tr></tbody></table>'
    ))).read("word/document.xml").decode()

    assert "<w:tcBorders>" in xml
    assert xml.count('w:val="nil"') == 4


def test_danh_so_muc_duoc_viet_thang_vao_chu():
    """Số mục ở giao diện do bộ đếm CSS vẽ, không nằm trong nội dung — sang Word
    phải tự viết vào, nếu không tệp xuất ra mất sạch số mục."""
    data = html_to_docx("<h1>A</h1><h2>B</h2><h3>C</h3><h3>D</h3><h2>E</h2><h1>F</h1>",
                        number_headings=True)
    text = _chu(data)

    for mong_doi in ("I. A", "1. B", "a) C", "b) D", "2. E", "II. F"):
        assert mong_doi in text, f"thiếu {mong_doi!r} trong: {text}"


def test_khong_bat_thi_khong_tu_them_so():
    assert "I." not in _chu(html_to_docx("<h1>A</h1>"))


def test_danh_sach_giu_ky_hieu_dau_dong():
    text = _chu(html_to_docx("<ul><li>ý một</li></ul><ol><li>số một</li><li>số hai</li></ol>"))

    assert "• ý một" in text
    assert "1. số một" in text and "2. số hai" in text


def test_le_trang_theo_dung_ban_ghi():
    """30mm ≈ 1701 twips. Sai đơn vị ở đây thì bản Word lệch hẳn so với bản in."""
    xml = zipfile.ZipFile(BytesIO(html_to_docx("<p>x</p>", margin_left_mm=30, margin_right_mm=20))
                          ).read("word/document.xml").decode()
    pg_mar = re.search(r"<w:pgMar[^/]+/>", xml).group(0)

    assert 'w:left="1701"' in pg_mar
    assert 'w:right="1134"' in pg_mar


def test_so_trang_la_TRUONG_cua_word_khong_phai_so_chep_cung():
    """Chép số cứng thì người nhận thêm một đoạn là số trang sai hết."""
    z = zipfile.ZipFile(BytesIO(html_to_docx(
        "<p>x</p>", footer=("", "Trang {{trang}}/{{tong_trang}}"))))
    footer = z.read("word/footer1.xml").decode()

    assert "PAGE" in footer and "NUMPAGES" in footer
    assert "fldChar" in footer


def test_the_khac_duoc_thay_bang_gia_tri_that():
    z = zipfile.ZipFile(BytesIO(html_to_docx(
        "<p>x</p>", header=("{{so_hieu}}", ""),
        replacements={"{{so_hieu}}": "08/2026/TB-DEGO"})))
    header = z.read("word/header1.xml").decode()

    assert "08/2026/TB-DEGO" in header
    assert "{{so_hieu}}" not in header


def test_khong_khai_dau_chan_trang_thi_khong_sinh_phan_thua():
    name = set(zipfile.ZipFile(BytesIO(html_to_docx("<p>x</p>"))).namelist())

    assert "word/header1.xml" not in name
    assert "word/footer1.xml" not in name


def test_anh_base64_duoc_nhung_vao_goi():
    #  PNG 1×1 hợp lệ.
    png = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmM"
           "IQAAAABJRU5ErkJggg==")
    z = zipfile.ZipFile(BytesIO(html_to_docx(f'<p><img src="data:image/png;base64,{png}"></p>')))

    assert "word/media/anh1.png" in z.namelist()
    #  Thiếu khai kiểu MIME là Word báo tệp hỏng.
    assert 'Extension="png"' in z.read("[Content_Types].xml").decode()
    assert "rIdAnh1" in z.read("word/_rels/document.xml.rels").decode()


def test_noi_dung_rong_van_ra_tep_mo_duoc():
    """Văn bản mới tạo chưa gõ gì vẫn phải xuất được, không nổ."""
    z = zipfile.ZipFile(BytesIO(html_to_docx("")))

    assert PHAN_BAT_BUOC.issubset(set(z.namelist()))


def test_ky_tu_dac_biet_khong_lam_vo_xml():
    """`<`, `&` trong nội dung mà không thoát là XML hỏng, Word không mở nổi.

    Kiểm thẳng trên XML: phải PARSE ĐƯỢC và ký tự phải nằm ở dạng đã thoát.
    """
    from xml.etree import ElementTree

    xml = zipfile.ZipFile(BytesIO(html_to_docx("<p>A &lt; B &amp; C</p>"))
                          ).read("word/document.xml").decode()

    #  Parse được = XML hợp lệ. Vỡ ở đây nghĩa là Word cũng không mở nổi.
    ElementTree.fromstring(xml)
    assert "A &lt; B &amp; C" in xml
