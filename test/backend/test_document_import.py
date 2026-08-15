from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from PIL import Image, ImageDraw

from app.modules.document.import_service import parse_document_file


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


def _docx(document: str, parts: dict[str, bytes | str]) -> bytes:
    target = BytesIO()
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", document)
        for path, content in parts.items():
            archive.writestr(path, content)
    return target.getvalue()


def _pdf_with_text() -> bytes:
    content = (
        b"BT /F2 20 Tf 0 0.6902 0.9412 rg 257 720 Td (PDF TITLE) Tj ET\n"
        b"BT /F1 12 Tf 0 0 0 rg 72 680 Td (Editable body) Tj ET"
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    document = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{index} 0 obj\n".encode())
        document.extend(obj)
        document.extend(b"\nendobj\n")
    xref = len(document)
    document.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode())
    document.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(document)


def _scanned_pdf() -> bytes:
    image = Image.new("RGB", (300, 400), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((25, 25, 275, 375), outline="#0f172a", width=3)
    draw.text((70, 180), "SCANNED PAGE", fill="#0f172a")
    target = BytesIO()
    image.save(target, format="PDF", resolution=72)
    return target.getvalue()


def test_docx_giu_style_danh_sach_va_lien_ket():
    document = f"""
    <w:document xmlns:w="{W}" xmlns:r="{R}">
      <w:body>
        <w:p>
          <w:pPr><w:spacing w:line="360" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr>
          <w:r><w:rPr><w:rFonts w:ascii="Calibri"/><w:b/><w:color w:val="00B0F0"/><w:sz w:val="40"/></w:rPr><w:t>TIÊU ĐỀ</w:t></w:r>
        </w:p>
        <w:p>
          <w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="7"/></w:numPr></w:pPr>
          <w:r><w:rPr><w:rStyle w:val="Strong"/><w:b w:val="0"/></w:rPr><w:t>Không đậm</w:t></w:r>
        </w:p>
        <w:p>
          <w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="7"/></w:numPr></w:pPr>
          <w:r><w:rPr><w:rStyle w:val="Strong"/></w:rPr><w:t>Đậm kế thừa</w:t></w:r>
        </w:p>
        <w:p>
          <w:hyperlink r:id="rIdMail"><w:r><w:t>hr@example.com</w:t></w:r></w:hyperlink>
        </w:p>
      </w:body>
    </w:document>
    """
    styles = f"""
    <w:styles xmlns:w="{W}">
      <w:docDefaults><w:rPrDefault><w:rPr><w:sz w:val="24"/></w:rPr></w:rPrDefault></w:docDefaults>
      <w:style w:type="character" w:styleId="Strong"><w:name w:val="Strong"/><w:rPr><w:b/></w:rPr></w:style>
    </w:styles>
    """
    numbering = f"""
    <w:numbering xmlns:w="{W}">
      <w:abstractNum w:abstractNumId="1"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/></w:lvl></w:abstractNum>
      <w:num w:numId="7"><w:abstractNumId w:val="1"/></w:num>
    </w:numbering>
    """
    relationships = f"""
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rIdMail" Type="{R}/hyperlink" Target="mailto:hr@example.com" TargetMode="External"/>
    </Relationships>
    """

    result = parse_document_file(
        "mau.docx",
        _docx(
            document,
            {
                "word/styles.xml": styles,
                "word/numbering.xml": numbering,
                "word/_rels/document.xml.rels": relationships,
            },
        ),
    )["content_html"]

    assert "text-align: center" in result
    assert "line-height: 1.5" in result
    assert "font-family: &quot;Calibri&quot;" in result
    assert "font-size: 20pt" in result
    assert "color: #00b0f0" in result
    assert result.count("<ul>") == 1
    assert result.count("<li>") == 2
    assert "<strong>Không đậm</strong>" not in result
    assert "<strong><span style=\"font-size: 12pt\">Đậm kế thừa</span></strong>" in result
    assert 'href="mailto:hr@example.com"' in result


def test_docx_dua_logo_header_vao_noi_dung_va_giu_kich_thuoc():
    document = f"""
    <w:document xmlns:w="{W}" xmlns:r="{R}">
      <w:body><w:p><w:r><w:t>Nội dung</w:t></w:r></w:p>
        <w:sectPr><w:headerReference w:type="default" r:id="rIdHeader"/></w:sectPr>
      </w:body>
    </w:document>
    """
    header = f"""
    <w:hdr xmlns:w="{W}" xmlns:r="{R}" xmlns:a="{A}" xmlns:wp="{WP}">
      <w:p><w:r><w:drawing><wp:inline><wp:extent cx="914400" cy="457200"/>
        <wp:docPr id="1" name="Logo công ty"/><a:graphic><a:graphicData>
          <a:blip r:embed="rIdLogo"/>
        </a:graphicData></a:graphic>
      </wp:inline></w:drawing></w:r></w:p>
    </w:hdr>
    """
    document_rels = f"""
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rIdHeader" Type="{R}/header" Target="header1.xml"/>
    </Relationships>
    """
    header_rels = f"""
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rIdLogo" Type="{R}/image" Target="media/logo.png"/>
    </Relationships>
    """

    result = parse_document_file(
        "co-logo.docx",
        _docx(
            document,
            {
                "word/header1.xml": header,
                "word/media/logo.png": b"\x89PNG\r\n\x1a\nlogo",
                "word/_rels/document.xml.rels": document_rels,
                "word/_rels/header1.xml.rels": header_rels,
            },
        ),
    )["content_html"]

    assert "data:image/png;base64," in result
    assert 'alt="Logo công ty"' in result
    assert 'width="96"' in result
    assert 'height="48"' in result
    assert result.index("<img") < result.index("Nội dung")


def test_pdf_co_lop_chu_giu_font_co_mau_can_le_va_kieu_chu():
    parsed = parse_document_file("mau.pdf", _pdf_with_text())
    result = parsed["content_html"]
    trace = parsed["import_trace"]

    assert "PDF TITLE" in result
    assert "Editable body" in result
    assert "font-family: &quot;Arial&quot;" in result
    assert "font-size: 20pt" in result
    assert "color: #00b0f0" in result
    assert "<strong>" in result
    assert "text-align: center" in result
    assert 'data-import-id="' in result
    assert 'data-source-page="1"' in result
    assert trace["source_type"] == "pdf"
    assert trace["quality"] == "editable_with_review"
    assert trace["page_count"] == 1
    assert trace["editable_page_count"] == 1
    assert trace["image_page_count"] == 0
    assert trace["issues"][0]["code"] == "layout_reconstructed"
    assert trace["issues"][0]["pages"] == [1]


def test_pdf_scan_duoc_giu_nguyen_duoi_dang_anh_trang():
    parsed = parse_document_file("ban-scan.pdf", _scanned_pdf())
    result = parsed["content_html"]
    trace = parsed["import_trace"]

    assert result.startswith('<img data-import-id="')
    assert 'src="data:image/jpeg;base64,' in result
    assert 'alt="Trang PDF 1 (ảnh quét)"' in result
    assert 'width="642"' in result
    assert trace["quality"] == "visual_only"
    assert trace["editable_page_count"] == 0
    assert trace["image_page_count"] == 1
    assert trace["issues"][0]["code"] == "image_only_page"
