"""ĐÓNG GÓI tệp .docx — phần vỏ OpenXML, không biết gì về HTML.

Vì sao tự sinh thay vì kéo `python-docx` về: thư viện đó **không đọc HTML**, nên
dù có nó thì phần việc nặng (dịch HTML sang OOXML) vẫn phải tự viết — mà phần vỏ
zip thì chỉ vài trăm dòng XML tĩnh. Thêm một phụ thuộc để dùng 5% của nó là đắt
hơn. Cùng lý do với `docx_html.py` ở chiều ngược lại (đọc .docx không cần
LibreOffice).

Một tệp .docx tối thiểu mà Word mở được gồm:

    [Content_Types].xml          khai kiểu MIME cho từng phần
    _rels/.rels                  trỏ tới phần chính
    word/document.xml            thân văn bản
    word/_rels/document.xml.rels quan hệ của thân (ảnh, đầu/chân trang)
    word/styles.xml              style Normal + Heading 1..3

Thiếu bất kỳ phần nào ở trên là Word báo "tệp hỏng" chứ không mở nửa vời.
"""
from __future__ import annotations

import zipfile
from dataclasses import dataclass, field
from io import BytesIO

#  Khổ A4 và đơn vị của Word. Word đo bằng TWIP (1/20 point, 1440 twip = 1 inch)
#  cho khoảng cách, và half-point cho cỡ chữ.
TWIPS_PER_MM = 56.7
A4_WIDTH_TWIPS = 11906
A4_HEIGHT_TWIPS = 16838

#  Thể thức mặc định — trùng `page-format.ts` bên giao diện.
DEFAULT_FONT = "Times New Roman"
DEFAULT_FONT_SIZE_PT = 14


def mm_to_twips(mm: float) -> int:
    return int(round(mm * TWIPS_PER_MM))


def xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))


@dataclass
class EmbeddedImage:
    """Một ảnh đã nhúng: tên tệp trong gói + dữ liệu nhị phân."""

    name: str
    data: bytes
    ext: str
    rid: str


@dataclass
class DocxPackage:
    """Bộ phần của một tệp .docx đang dựng."""

    body_xml: str = ""
    header_xml: str = ""
    footer_xml: str = ""
    images: list[EmbeddedImage] = field(default_factory=list)


_IMAGE_CONTENT_TYPES = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "gif": "image/gif", "bmp": "image/bmp", "webp": "image/webp",
}


def _content_types(pkg: DocxPackage) -> str:
    image_exts = sorted({a.ext for a in pkg.images})
    default = "".join(
        f'<Default Extension="{d}" ContentType="{_IMAGE_CONTENT_TYPES.get(d, "image/png")}"/>'
        for d in image_exts
    )
    part = ""
    if pkg.header_xml:
        part += ('<Override PartName="/word/header1.xml" ContentType="application/vnd.'
                 'openxmlformats-officedocument.wordprocessingml.header+xml"/>')
    if pkg.footer_xml:
        part += ('<Override PartName="/word/footer1.xml" ContentType="application/vnd.'
                 'openxmlformats-officedocument.wordprocessingml.footer+xml"/>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
        'relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        + default +
        '<Override PartName="/word/document.xml" ContentType="application/vnd.'
        'openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.'
        'openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        + part +
        '</Types>'
    )


_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
    'relationships/officeDocument" Target="word/document.xml"/>'
    '</Relationships>'
)


def _document_rels(pkg: DocxPackage) -> str:
    entries = ['<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/'
           'officeDocument/2006/relationships/styles" Target="styles.xml"/>']
    if pkg.header_xml:
        entries.append('<Relationship Id="rIdHeader" Type="http://schemas.openxmlformats.org/'
                   'officeDocument/2006/relationships/header" Target="header1.xml"/>')
    if pkg.footer_xml:
        entries.append('<Relationship Id="rIdFooter" Type="http://schemas.openxmlformats.org/'
                   'officeDocument/2006/relationships/footer" Target="footer1.xml"/>')
    for a in pkg.images:
        entries.append(f'<Relationship Id="{a.rid}" Type="http://schemas.openxmlformats.org/'
                   f'officeDocument/2006/relationships/image" Target="media/{a.name}"/>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(entries) + '</Relationships>')


def _styles_xml() -> str:
    """Style tối thiểu: Normal đúng thể thức Nghị định 30 + ba cấp tiêu đề.

    Khai style thay vì bôi định dạng vào từng đoạn để người nhận mở ra còn dùng
    được khung Tiêu đề 1/2/3 của Word (mục lục tự động, ngăn điều hướng).
    """
    size = DEFAULT_FONT_SIZE_PT * 2      # half-point
    headings = "".join(
        f'<w:style w:type="paragraph" w:styleId="Heading{cap}">'
        f'<w:name w:val="heading {cap}"/><w:basedOn w:val="Normal"/>'
        f'<w:pPr><w:keepNext/><w:outlineLvl w:val="{cap - 1}"/>'
        f'<w:spacing w:before="180" w:after="60"/></w:pPr>'
        f'<w:rPr><w:b/><w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr></w:style>'
        for cap, sz in ((1, size + 8), (2, size + 4), (3, size + 2))
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:docDefaults><w:rPrDefault><w:rPr>'
        f'<w:rFonts w:ascii="{DEFAULT_FONT}" w:hAnsi="{DEFAULT_FONT}" w:cs="{DEFAULT_FONT}"/>'
        f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr></w:rPrDefault>'
        '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="276" w:lineRule="auto"/>'
        '</w:pPr></w:pPrDefault></w:docDefaults>'
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/></w:style>'
        + headings +
        '</w:styles>'
    )


def _sect_pr(margin_left_mm: int, margin_right_mm: int, margin_top_mm: int, margin_bottom_mm: int,
             pkg: DocxPackage) -> str:
    """Khai khổ giấy, lề và tham chiếu đầu/chân trang cho cả tài liệu."""
    references = ""
    if pkg.header_xml:
        references += '<w:headerReference w:type="default" r:id="rIdHeader"/>'
    if pkg.footer_xml:
        references += '<w:footerReference w:type="default" r:id="rIdFooter"/>'
    return (
        f'<w:sectPr>{references}'
        f'<w:pgSz w:w="{A4_WIDTH_TWIPS}" w:h="{A4_HEIGHT_TWIPS}"/>'
        f'<w:pgMar w:top="{mm_to_twips(margin_top_mm)}" w:right="{mm_to_twips(margin_right_mm)}" '
        f'w:bottom="{mm_to_twips(margin_bottom_mm)}" w:left="{mm_to_twips(margin_left_mm)}" '
        f'w:header="{mm_to_twips(10)}" w:footer="{mm_to_twips(10)}" w:gutter="0"/>'
        f'</w:sectPr>'
    )


_NS_W = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
         'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
         'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
         'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
         'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')


def pack(pkg: DocxPackage, *, margin_left_mm: int, margin_right_mm: int,
             margin_top_mm: int = 20, margin_bottom_mm: int = 20) -> bytes:
    """Ghép các phần thành một tệp .docx hoàn chỉnh, trả về bytes."""
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document {_NS_W}><w:body>'
        + pkg.body_xml
        + _sect_pr(margin_left_mm, margin_right_mm, margin_top_mm, margin_bottom_mm, pkg)
        + '</w:body></w:document>'
    )

    buffer = BytesIO()
    #  `ZIP_DEFLATED` chứ không phải STORED: một quy chế dài nén còn khoảng 1/5,
    #  mà tệp đi qua email nội bộ.
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _content_types(pkg))
        z.writestr("_rels/.rels", _ROOT_RELS)
        z.writestr("word/document.xml", document)
        z.writestr("word/_rels/document.xml.rels", _document_rels(pkg))
        z.writestr("word/styles.xml", _styles_xml())
        if pkg.header_xml:
            z.writestr("word/header1.xml", _wrap("hdr", pkg.header_xml))
        if pkg.footer_xml:
            z.writestr("word/footer1.xml", _wrap("ftr", pkg.footer_xml))
        for a in pkg.images:
            z.writestr(f"word/media/{a.name}", a.data)
    return buffer.getvalue()


def _wrap(tag: str, content: str) -> str:
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:{tag} {_NS_W}>{content}</w:{tag}>')


def header_footer_paragraph(left: str, right: str) -> str:
    """Một dòng đầu/chân trang: chữ trái — tab — chữ phải.

    Dùng **tab canh phải** đúng cách Word làm, thay vì bảng vô hình: bảng trong
    đầu trang là thứ hay vỡ nhất khi người nhận sửa lại lề.

    Thẻ `{{trang}}` / `{{tong_trang}}` đã được đổi thành **trường PAGE/NUMPAGES
    của Word** trước khi vào đây, nên số trang tự cập nhật khi người nhận thêm
    bớt nội dung — chép số cứng thì sửa một dòng là sai hết.
    """
    return (
        '<w:p><w:pPr><w:tabs><w:tab w:val="right" w:pos="9000"/></w:tabs>'
        '<w:spacing w:after="0"/></w:pPr>'
        + left + ('<w:r><w:tab/></w:r>' if right else "") + right +
        '</w:p>'
    )


def page_number_field(kind: str) -> str:
    """Trường PAGE hoặc NUMPAGES — Word tự tính lại, không phải số chép cứng."""
    return (
        '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
        f'<w:r><w:instrText xml:space="preserve"> {kind} </w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
        '<w:r><w:t>1</w:t></w:r>'
        '<w:r><w:fldChar w:fldCharType="end"/></w:r>'
    )
