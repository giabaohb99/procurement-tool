"""Chuyển Word/Markdown/HTML thành nội dung cho trình soạn thảo văn bản."""
from io import BytesIO
from types import SimpleNamespace
import zipfile

import pytest

from app.modules.document import import_service


def _docx(document_xml: str) -> bytes:
    output = BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    return output.getvalue()


def test_nhap_markdown_giu_tieu_de_va_bang():
    raw = (
        "# Quyết định\n\n"
        "| Họ tên | Chức vụ |\n"
        "| --- | --- |\n"
        "| Nguyễn Văn A | Trưởng phòng |\n"
    ).encode()

    parsed = import_service.parse_document_file("quyet-dinh.md", raw)

    assert "<h1>Quyết định</h1>" in parsed["content_html"]
    assert "<table>" in parsed["content_html"]
    assert parsed["filename"] == "quyet-dinh.md"


def test_nhap_html_chi_lay_body_va_loc_ma_chay():
    raw = (
        '<html><head><title>Bỏ</title></head><body><h2>Nội dung</h2>'
        '<script>alert(1)</script><img src="x" onerror="alert(2)"></body></html>'
    ).encode()

    content = import_service.parse_document_file("mau.html", raw)["content_html"]

    assert content.startswith("<h2>Nội dung</h2>")
    assert "<title>" not in content
    assert "alert" not in content
    assert "onerror" not in content


def test_nhap_docx_giu_tieu_de_dinh_dang_va_bang():
    raw = _docx(
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:body>'
        '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        '<w:r><w:t>QUYẾT ĐỊNH</w:t></w:r></w:p>'
        '<w:p><w:r><w:rPr><w:b/><w:i/></w:rPr><w:t>Điều 1</w:t></w:r></w:p>'
        '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Họ tên</w:t></w:r></w:p></w:tc>'
        '<w:tc><w:p><w:r><w:t>Nguyễn Văn A</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
        '</w:body></w:document>'
    )

    content = import_service.parse_document_file("quyet-dinh.docx", raw)["content_html"]

    assert "<h1>QUYẾT ĐỊNH</h1>" in content
    assert "<em><strong>Điều 1</strong></em>" in content
    assert "<table><tbody><tr>" in content
    assert "Nguyễn Văn A" in content


def test_docx_hong_duoc_bao_ro():
    with pytest.raises(ValueError, match="không hợp lệ|bị hỏng"):
        import_service.parse_document_file("hong.docx", b"khong-phai-zip")


def test_nhap_doc_doi_cu_bang_antiword(monkeypatch):
    captured_path = ""

    def fake_run(command, **kwargs):
        nonlocal captured_path
        captured_path = command[1]
        assert kwargs["timeout"] == 20
        return SimpleNamespace(returncode=0, stdout="CỘNG HÒA\n\nĐiều 1".encode(), stderr=b"")

    monkeypatch.setattr(import_service.shutil, "which", lambda name: "/usr/bin/antiword")
    monkeypatch.setattr(import_service.subprocess, "run", fake_run)

    content = import_service.parse_document_file("quyet-dinh.doc", b"word-binary")["content_html"]

    assert content == "<p>CỘNG HÒA</p><p>Điều 1</p>"
    assert captured_path
    assert not import_service.os.path.exists(captured_path)


@pytest.mark.parametrize("filename", ["bang.xlsx", "anh.png", "khong-co-duoi"])
def test_tu_choi_dinh_dang_khong_ho_tro(filename):
    with pytest.raises(ValueError, match="Chỉ nhận tệp"):
        import_service.parse_document_file(filename, b"x")


def test_tu_choi_file_rong_va_qua_10mb():
    with pytest.raises(ValueError, match="không có nội dung"):
        import_service.parse_document_file("rong.md", b"")
    with pytest.raises(ValueError, match="10MB"):
        import_service.parse_document_file(
            "qua-lon.html",
            b"x" * (import_service.MAX_FILE_SIZE + 1),
        )
