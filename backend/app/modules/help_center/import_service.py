"""Nhập bài viết Help Center từ file HTML / Markdown.

Đầu vào là file NGOÀI hệ thống (soạn bằng trình khác, xuất từ AI, chép từ web) nên phải
LỌC HTML trước khi lưu: nội dung bài viết được render bằng dangerouslySetInnerHTML ở khu
người dùng, dán nguyên <script> vào là chạy thật.

Cách lấy tiêu đề: <h1> đầu tiên (và BỎ thẻ đó khỏi nội dung, vì trang đã hiện tiêu đề riêng
ở đầu bài) → không có thì <title> → không có nữa thì tên file.
"""
import re
from html.parser import HTMLParser

import markdown

MAX_FILE_SIZE = 2 * 1024 * 1024      # 2MB/file — bài hướng dẫn không thể to hơn thế
MAX_FILES = 30
HTML_EXTS = {"html", "htm"}
MD_EXTS = {"md", "markdown"}
ALLOWED_EXTS = HTML_EXTS | MD_EXTS

# Thẻ giữ lại — phủ đúng những gì trình soạn thảo Quill sinh ra, cộng bảng và iframe nhúng.
ALLOWED_TAGS = {
    "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
    "strong", "b", "em", "i", "u", "s", "del", "ins", "sub", "sup", "mark", "small",
    "blockquote", "pre", "code", "kbd",
    "ul", "ol", "li", "dl", "dt", "dd",
    "a", "img", "figure", "figcaption", "span", "div",
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption", "colgroup", "col",
    "iframe",
}
VOID_TAGS = {"br", "hr", "img", "col"}
# KHÔNG có `srcdoc`: đó là cả một trang HTML nhét vào thuộc tính, chạy CÙNG ORIGIN với trang
# cha — cho qua là mở đường cho <iframe srcdoc="<script>…">. Nhúng video chỉ cần `src`.
ALLOWED_ATTRS = {
    "href", "src", "alt", "title", "class", "style", "width", "height",
    "colspan", "rowspan", "span", "target", "rel", "start", "type",
    "allow", "allowfullscreen", "frameborder", "loading", "data-lang", "data-colwidth",
    "data-import-id", "data-source-page",
}
URL_ATTRS = {"href", "src"}


class _Cleaner(HTMLParser):
    """Lọc theo danh sách cho phép — thẻ lạ bị bỏ nhưng GIỮ phần chữ bên trong.

    Riêng <script>/<style> phải bỏ cả nội dung, nếu không mã JS/CSS rơi ra thành text hiển thị.
    """

    DROP_CONTENT = {"script", "style", "noscript", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self._skip_depth = 0

    def _attrs(self, attrs) -> str:
        parts = []
        for name, value in attrs:
            name = (name or "").lower()
            value = value or ""
            if name.startswith("on") or name not in ALLOWED_ATTRS:
                continue        # bỏ mọi handler onclick/onerror… và thuộc tính lạ
            if name in URL_ATTRS:
                url = value.strip().replace("\n", "").replace("\t", "")
                low = url.lower()
                # data:image cho phép (Quill dán ảnh inline), data: khác và javascript: thì không
                if low.startswith("javascript:") or low.startswith("vbscript:") or (
                        low.startswith("data:") and not low.startswith("data:image/")):
                    continue
                value = url
            parts.append(f' {name}="{value.replace(chr(34), "&quot;")}"')
        return "".join(parts)

    def handle_starttag(self, tag, attrs):
        if tag in self.DROP_CONTENT:
            self._skip_depth += 1
            return
        if self._skip_depth or tag not in ALLOWED_TAGS:
            return
        self.out.append(f"<{tag}{self._attrs(attrs)}>")

    def handle_startendtag(self, tag, attrs):
        if self._skip_depth or tag not in ALLOWED_TAGS:
            return
        self.out.append(f"<{tag}{self._attrs(attrs)}>")

    def handle_endtag(self, tag):
        if tag in self.DROP_CONTENT:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth or tag not in ALLOWED_TAGS or tag in VOID_TAGS:
            return
        self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if self._skip_depth:
            return
        self.out.append(data.replace("<", "&lt;").replace(">", "&gt;"))

    def result(self) -> str:
        return "".join(self.out)


def sanitize_html(html: str) -> str:
    cleaner = _Cleaner()
    cleaner.feed(html or "")
    cleaner.close()
    return cleaner.result().strip()


def _text_of(html: str) -> str:
    """Chữ trần — dùng lấy tiêu đề / mô tả ngắn."""
    return " ".join(re.sub(r"<[^>]+>", " ", html or "").split())


_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def _extract_title(html: str) -> tuple[str, str]:
    """Trả (tiêu đề, nội dung đã bỏ thẻ tiêu đề). Không tìm thấy thì tiêu đề rỗng."""
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    if m:
        return _text_of(m.group(1)), (html[:m.start()] + html[m.end():])
    return "", html


def _pop_doc_title(html: str) -> tuple[str, str]:
    """Tách <title> ra khỏi nội dung. Phải gọi TRƯỚC _body_only vì <title> nằm trong <head>
    (gọi sau thì <head> đã bị cắt, tiêu đề mất trắng). Và phải bỏ hẳn thẻ đó khỏi nội dung:
    <title> không nằm trong danh sách thẻ cho phép nên bộ lọc chỉ bỏ thẻ mà GIỮ chữ, tiêu đề
    sẽ lọt vào đầu bài viết thành một dòng trống nghĩa."""
    m = _TITLE_RE.search(html)
    if not m:
        return "", html
    return _text_of(m.group(1)), _TITLE_RE.sub("", html)


def _body_only(html: str) -> str:
    """File HTML đầy đủ thì chỉ lấy trong <body> (bỏ <head>, <!doctype>…)."""
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.I | re.S)
    return m.group(1) if m else html


def parse_file(filename: str, raw: bytes) -> dict:
    """File → {title, summary, content}. Ném ValueError nếu đuôi/kích thước không hợp lệ."""
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext not in ALLOWED_EXTS:
        raise ValueError("Chỉ nhận file .html, .htm, .md, .markdown")
    if len(raw) > MAX_FILE_SIZE:
        raise ValueError("File vượt quá 2MB")

    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # File xuất từ Word/Excel bản Việt hay là cp1258/cp1252 — thử trước khi bỏ cuộc
        for enc in ("cp1258", "cp1252", "latin-1"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Không đọc được nội dung file (mã hóa lạ)")

    doc_title = ""
    if ext in MD_EXTS:
        # tables: bảng Markdown | --- | ; fenced_code: khối ```; nl2br: xuống dòng giữ nguyên
        html = markdown.markdown(text, extensions=["tables", "fenced_code", "nl2br", "sane_lists"])
    else:
        doc_title, text = _pop_doc_title(text)
        html = _body_only(text)

    title, html = _extract_title(html)
    content = sanitize_html(html)
    title = title or doc_title
    if not title:
        title = re.sub(r"\.(html?|md|markdown)$", "", filename, flags=re.I).strip() or "Bài viết mới"
    summary = _text_of(content)[:250] or None
    return {"title": title[:255], "summary": summary, "content": content}
