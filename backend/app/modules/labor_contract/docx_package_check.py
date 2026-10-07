"""Kiểm GÓI .docx (zip) TRƯỚC mọi bước Jinja / python-docx: đầu vào KHÔNG tin cậy, phải rẻ và có trần.

Chặn: zip bom (số mục, tổng dung lượng giải nén), phần XML phình to, quá nhiều chỗ `{{ }}` (bộ biên
dịch Jinja ngốn RAM tỉ lệ số biểu thức: tệp ~40KB nén có thể đòi hàng trăm MB), macro, và các móc
ra ngoài (liên kết ngoài `TargetMode="External"`, đối tượng nhúng OLE / embeddings).

Mọi con số đo bằng byte THỰC ĐỌC (có hạn mức), không tin `file_size` khai trong tiêu đề zip.
"""
import re
import zipfile
from io import BytesIO

MAX_ZIP_ENTRIES = 2000
MAX_UNZIPPED_BYTES = 60 * 1024 * 1024
MAX_XML_PART_BYTES = 5 * 1024 * 1024     # mỗi phần word/*.xml và *.rels
MAX_PLACEHOLDERS = 1000                  # số chỗ `{{ }}` (danh mục thật chỉ vài chục)
#  Đếm ký tự `{` thô (2 dấu mỗi biến) thay vì chuỗi `{{`: Word hay tách `{{` thành hai run — docxtpl
#  gộp lại thành một biểu thức, nên đếm `{{` sẽ lọt đúng ca tách run.
_MAX_OPEN_BRACES = MAX_PLACEHOLDERS * 2
_EXTERNAL_REL = re.compile(rb"TargetMode\s*=\s*[\"']External[\"']", re.IGNORECASE)


class TemplateRejected(Exception):
    """Mẫu không dùng được. `unknown` = các biến ngoài danh mục (nếu là lý do bị từ chối)."""

    def __init__(self, message: str, unknown: list[str] | None = None):
        super().__init__(message)
        self.message = message
        self.unknown = unknown or []


def _read_bounded(zf: zipfile.ZipFile, info: zipfile.ZipInfo, limit: int) -> bytes:
    """Đọc tối đa `limit` byte; vượt → từ chối (không đọc hết phần bị khai gian)."""
    if info.file_size > limit:
        raise TemplateRejected(f"Tệp .docx có thành phần «{info.filename}» quá lớn.")
    try:
        with zf.open(info) as part:
            data = part.read(limit + 1)
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError):
        raise TemplateRejected("Tệp .docx hỏng hoặc dùng kiểu nén / mã hóa không hỗ trợ.")
    if len(data) > limit:
        raise TemplateRejected(f"Tệp .docx có thành phần «{info.filename}» quá lớn.")
    return data


def _scan_parts(zf: zipfile.ZipFile, infos: list[zipfile.ZipInfo]) -> None:
    """Đọc các phần XML / rels với hạn mức tổng; đếm `{`, soi liên kết ngoài."""
    budget, braces = MAX_UNZIPPED_BYTES, 0
    for info in infos:
        low = info.filename.lower()
        is_rels = low.endswith(".rels")
        is_word_xml = low.startswith("word/") and low.endswith(".xml")
        if not (is_rels or is_word_xml):
            continue
        data = _read_bounded(zf, info, min(MAX_XML_PART_BYTES, budget))
        budget -= len(data)
        if is_rels and _EXTERNAL_REL.search(data):
            raise TemplateRejected("Tệp .docx có liên kết ra ngoài (hyperlink / ảnh từ máy chủ khác), "
                                   "không được phép.")
        if is_word_xml:
            braces += data.count(b"{")
            if braces > _MAX_OPEN_BRACES:
                raise TemplateRejected(
                    f"Mẫu có quá nhiều chỗ điền biến (tối đa {MAX_PLACEHOLDERS} dấu {{{{ }}}}).")


def check_package(data: bytes) -> None:
    """Kiểm gói zip: hợp lệ, không bom, có document.xml, không macro / nhúng / liên kết ngoài.
    Sai → TemplateRejected."""
    if not data:
        raise TemplateRejected("Tệp rỗng.")
    try:
        zf = zipfile.ZipFile(BytesIO(data))
    except zipfile.BadZipFile:
        raise TemplateRejected("Tệp không phải .docx hợp lệ (không mở được gói nén).")
    with zf:
        infos = zf.infolist()
        if len(infos) > MAX_ZIP_ENTRIES:
            raise TemplateRejected("Tệp .docx có quá nhiều thành phần bên trong.")
        if sum(i.file_size for i in infos) > MAX_UNZIPPED_BYTES:
            raise TemplateRejected("Tệp .docx giải nén ra quá lớn.")
        names = {i.filename for i in infos}
        if "word/document.xml" not in names:
            raise TemplateRejected("Tệp không phải văn bản Word (.docx): thiếu word/document.xml.")
        if any("vbaproject" in n.lower() or "vbadata" in n.lower() for n in names):
            raise TemplateRejected("Tệp .docx chứa macro, không được phép.")
        if any(n.lower().startswith("word/embeddings/") or "oleobject" in n.lower() for n in names):
            raise TemplateRejected("Tệp .docx chứa đối tượng nhúng (OLE / embeddings), không được phép.")
        try:
            content_types = zf.read("[Content_Types].xml")
        except KeyError:
            raise TemplateRejected("Tệp .docx thiếu [Content_Types].xml.")
        if b"macroEnabled" in content_types:
            raise TemplateRejected("Tệp là văn bản bật macro (.docm đổi đuôi), không được phép.")
        _scan_parts(zf, infos)
