"""Chuyển HTML của trình soạn thảo thành .docx — chiều ngược của `docx_html.py`.

Đọc HTML bằng `html.parser` của thư viện chuẩn (giống `help_center/import_service`),
không kéo thêm bs4/lxml: tập thẻ ở đây HẸP và do chính trình soạn thảo sinh ra,
không phải HTML hoang dã ngoài internet.

**Giữ được:** đoạn văn · tiêu đề 1–3 · đậm/nghiêng/gạch chân/gạch ngang · phông ·
cỡ chữ · màu chữ · màu nền chữ · canh lề · giãn dòng · thụt lề · danh sách ·
bảng (kể cả viền và ô gộp theo bề ngang cột) · ảnh · xuống dòng.

**Đánh đổi đã chốt — nói trước để khỏi tìm:**

* Danh sách xuất ra dưới dạng **đoạn có ký hiệu đầu dòng** (`•`, `1.`) chứ không
  phải danh sách thật của Word. Danh sách thật đòi thêm `numbering.xml` với bộ
  `abstractNum` riêng cho từng cấp; đổi lấy việc người nhận bấm Tab để thụt cấp
  được — trong khi 99% văn bản hành chính chỉ cần nhìn đúng.
* Đánh số mục tự động (I · 1 · a) được **viết thẳng vào chữ** của tiêu đề, vì số
  đó ở giao diện do bộ đếm CSS vẽ ra, không nằm trong nội dung.
"""
from __future__ import annotations

import base64
import re
from html.parser import HTMLParser

from .docx_writer import (EmbeddedImage, DocxPackage, header_footer_paragraph, pack,
                          page_number_field, xml_escape)

#  Thẻ khối tạo ra một đoạn mới trong Word.
_PARAGRAPH_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"}
#  Thẻ bật/tắt một kiểu chữ.
_STYLE_TAGS = {"strong": "b", "b": "b", "em": "i", "i": "i",
             "u": "u", "s": "s", "strike": "s", "del": "s"}

_TEXT_ALIGN = {"left": "left", "center": "center", "right": "right", "justify": "both"}

_EMU_PER_PX = 9525
_TWIPS_PER_PX = 15
_ROMAN_NUMERALS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
             "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]


def _parse_style(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (raw or "").split(";"):
        if ":" not in part:
            continue
        key, _, value = part.partition(":")
        out[key.strip().lower()] = value.strip()
    return out


def _px(value: str | None) -> float | None:
    if not value:
        return None
    so = re.match(r"^(-?[\d.]+)\s*px$", value.strip())
    return float(so.group(1)) if so else None


def _color(value: str | None) -> str | None:
    """`#1a2b3c` hoặc `rgb(1,2,3)` → `1A2B3C`. Word không nhận dấu #."""
    if not value:
        return None
    value = value.strip()
    if value.startswith("#"):
        so = value[1:]
        if len(so) == 3:
            so = "".join(c * 2 for c in so)
        return so.upper() if len(so) == 6 else None
    rgb = re.match(r"^rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)", value)
    if rgb:
        return "".join(f"{int(v):02X}" for v in rgb.groups())
    return None


class _CharStyle:
    """Định dạng đang có hiệu lực tại một điểm trong cây HTML."""

    def __init__(self) -> None:
        self.bold = self.italic = self.underline = self.strike = False
        self.font: str | None = None
        self.size_pt: float | None = None
        self.color: str | None = None
        self.background: str | None = None

    def clone(self) -> "_CharStyle":
        new = _CharStyle()
        new.__dict__.update(self.__dict__)
        return new

    def rpr(self) -> str:
        part = ""
        if self.font:
            name = xml_escape(self.font)
            part += f'<w:rFonts w:ascii="{name}" w:hAnsi="{name}" w:cs="{name}"/>'
        if self.bold:
            part += "<w:b/>"
        if self.italic:
            part += "<w:i/>"
        if self.underline:
            part += '<w:u w:val="single"/>'
        if self.strike:
            part += "<w:strike/>"
        if self.color:
            part += f'<w:color w:val="{self.color}"/>'
        if self.background:
            part += f'<w:shd w:val="clear" w:color="auto" w:fill="{self.background}"/>'
        if self.size_pt:
            half_points = int(round(self.size_pt * 2))
            part += f'<w:sz w:val="{half_points}"/><w:szCs w:val="{half_points}"/>'
        return f"<w:rPr>{part}</w:rPr>" if part else ""


class _Converter(HTMLParser):
    """Duyệt HTML một lượt, sinh thẳng XML của thân tài liệu."""

    def __init__(self, *, number_headings: bool = False) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.images: list[EmbeddedImage] = []
        self.number_headings = number_headings
        self._counters = [0, 0, 0]              # bộ đếm ba cấp tiêu đề

        self._styles = [_CharStyle()]
        self._paragraph_open = False
        self._runs: list[str] = []
        self._ppr = ""
        self._paragraph_tag = "p"
        self._list_stack: list[tuple[str, int]] = []   # (ul|ol, số thứ tự)
        self._in_labels = False
        self._table: list[str] = []

    # ── tiện ích ─────────────────────────────────────────────────────────────
    @property
    def _current_style(self) -> _CharStyle:
        return self._styles[-1]

    def _open_paragraph(self, tag: str, attrs: dict[str, str]) -> None:
        self._paragraph_open = True
        self._paragraph_tag = tag
        self._runs = []
        self._ppr = self._compute_ppr(tag, attrs)

    def _compute_ppr(self, tag: str, attrs: dict[str, str]) -> str:
        style = _parse_style(attrs.get("style", ""))
        part = ""
        if tag in {"h1", "h2", "h3"}:
            part += f'<w:pStyle w:val="Heading{tag[1]}"/>'
        elif tag == "blockquote":
            part += '<w:ind w:left="720"/>'

        align = _TEXT_ALIGN.get(style.get("text-align", ""))
        if align:
            part += f'<w:jc w:val="{align}"/>'

        left_indent = _px(style.get("margin-left")) or 0
        first_line_indent = _px(style.get("text-indent")) or 0
        #  Danh sách: mỗi cấp thụt thêm một nấc, giữ đúng hình thức bản gốc.
        left_indent += 360 / _TWIPS_PER_PX * len(self._list_stack)
        if left_indent or first_line_indent:
            part += '<w:ind'
            if left_indent:
                part += f' w:left="{int(left_indent * _TWIPS_PER_PX)}"'
            if first_line_indent:
                part += f' w:firstLine="{int(first_line_indent * _TWIPS_PER_PX)}"'
            part += "/>"

        line_height = style.get("line-height")
        before = _px(style.get("margin-top"))
        after = _px(style.get("margin-bottom"))
        spacing = ""
        if line_height:
            try:
                #  CSS 1.5 = 1,5 dòng Word → 1.5 * 240 = 360. Không quy đổi hệ
                #  số: xem `word-line-spacing.ts`, chốt "giãn dòng 1 là 1".
                #  Bóc đuôi `em` — giao diện ghi `1.5em` để khống chế được cả
                #  chữ to trong `<span>`; quên bóc thì `float()` nổ, khối `except`
                #  nuốt mất và văn bản xuất ra không còn giãn dòng.
                line_mult = float(str(line_height).strip().removesuffix("em"))
                spacing += f' w:line="{int(round(line_mult * 240))}" w:lineRule="auto"'
            except ValueError:
                pass
        if before:
            spacing += f' w:before="{int(before * _TWIPS_PER_PX)}"'
        if after:
            spacing += f' w:after="{int(after * _TWIPS_PER_PX)}"'
        if spacing:
            part += f"<w:spacing{spacing}/>"
        return f"<w:pPr>{part}</w:pPr>" if part else ""

    def _close_paragraph(self) -> None:
        if not self._paragraph_open:
            return
        self._paragraph_open = False
        content = "".join(self._runs)
        #  Đoạn rỗng vẫn phải giữ: người soạn dùng nó làm khoảng trống ký tên.
        xml = f"<w:p>{self._ppr}{content}</w:p>"
        (self._table if self._in_labels else self.out).append(xml)
        self._runs = []

    def _add_run(self, text: str) -> None:
        if not text:
            return
        self._runs.append(
            f'<w:r>{self._current_style.rpr()}<w:t xml:space="preserve">{xml_escape(text)}</w:t></w:r>'
        )

    def _heading_prefix(self, tag: str) -> str:
        """Số mục tự động cho tiêu đề — viết thẳng vào chữ (xem chú thích đầu tệp)."""
        cap = int(tag[1])
        if not self.number_headings or cap > 3:
            return ""
        self._counters[cap - 1] += 1
        for after in range(cap, 3):
            self._counters[after] = 0
        so = self._counters[cap - 1]
        if cap == 1:
            return f"{_ROMAN_NUMERALS[so - 1] if so <= len(_ROMAN_NUMERALS) else so}. "
        if cap == 2:
            return f"{so}. "
        return f"{chr(ord('a') + so - 1) if so <= 26 else so}) "

    # ── HTMLParser ───────────────────────────────────────────────────────────
    def handle_starttag(self, tag: str, attrs_list) -> None:  # noqa: D102
        attrs = {k: (v or "") for k, v in attrs_list}
        tag = tag.lower()

        if tag in _STYLE_TAGS:
            new = self._current_style.clone()
            setattr(new, {"b": "bold", "i": "italic", "u": "underline",
                          "s": "strike"}[_STYLE_TAGS[tag]], True)
            self._styles.append(new)
            return

        if tag == "span":
            style = _parse_style(attrs.get("style", ""))
            new = self._current_style.clone()
            if style.get("font-family"):
                new.font = style["font-family"].split(",")[0].strip(" '\"")
            size = style.get("font-size", "")
            if size.endswith("pt"):
                try:
                    new.size_pt = float(size[:-2])
                except ValueError:
                    pass
            new.color = _color(style.get("color")) or new.color
            new.background = _color(style.get("background-color")) or new.background
            self._styles.append(new)
            return

        if tag in {"ul", "ol"}:
            self._list_stack.append((tag, 0))
            return

        if tag == "table":
            self._in_labels = True
            self._table = ["<w:tbl>", self._tbl_pr()]
            return
        if tag == "tr":
            self._table.append("<w:tr>")
            return
        if tag in {"td", "th"}:
            self._table.append(self._tc_pr(attrs))
            #  Ô luôn phải mở bằng một đoạn, kể cả ô trống.
            self._open_paragraph("p", {})
            if tag == "th":
                new = self._current_style.clone()
                new.bold = True
                self._styles.append(new)
            return

        if tag == "br":
            self._runs.append("<w:r><w:br/></w:r>")
            return

        if tag == "img":
            self._insert_image(attrs)
            return

        if tag in _PARAGRAPH_TAGS:
            self._close_paragraph()
            self._open_paragraph(tag, attrs)
            if tag == "li" and self._list_stack:
                kind, so = self._list_stack[-1]
                so += 1
                self._list_stack[-1] = (kind, so)
                self._add_run("• " if kind == "ul" else f"{so}. ")
            elif tag in {"h1", "h2", "h3"}:
                self._add_run(self._heading_prefix(tag))

    def handle_endtag(self, tag: str) -> None:  # noqa: D102
        tag = tag.lower()
        if tag in _STYLE_TAGS or tag == "span":
            if len(self._styles) > 1:
                self._styles.pop()
            return
        if tag in {"ul", "ol"} and self._list_stack:
            self._list_stack.pop()
            return
        if tag in {"td", "th"}:
            self._close_paragraph()
            if tag == "th" and len(self._styles) > 1:
                self._styles.pop()
            self._table.append("</w:tc>")
            return
        if tag == "tr":
            self._table.append("</w:tr>")
            return
        if tag == "table":
            self._table.append("</w:tbl>")
            self._in_labels = False
            self.out.append("".join(self._table))
            #  Word đòi một đoạn ngay sau bảng, thiếu thì hai bảng liền nhau dính
            #  làm một và người nhận không tách ra được.
            self.out.append("<w:p/>")
            self._table = []
            return
        if tag in _PARAGRAPH_TAGS:
            self._close_paragraph()

    def handle_data(self, data: str) -> None:  # noqa: D102
        if not data:
            return
        if not self._paragraph_open:
            #  Chữ trần ngoài mọi thẻ khối — vẫn phải giữ.
            if not data.strip():
                return
            self._open_paragraph("p", {})
        self._add_run(data)

    # ── bảng và ảnh ──────────────────────────────────────────────────────────
    def _tbl_pr(self) -> str:
        align = "".join(
            f'<w:{v} w:val="single" w:sz="4" w:space="0" w:color="9CA3AF"/>'
            for v in ("top", "left", "bottom", "right", "insideH", "insideV")
        )
        return (f'<w:tblPr><w:tblW w:w="5000" w:type="pct"/>'
                f'<w:tblBorders>{align}</w:tblBorders></w:tblPr>')

    def _tc_pr(self, attrs: dict[str, str]) -> str:
        style = _parse_style(attrs.get("style", ""))
        part = ""
        width = attrs.get("colwidth") or attrs.get("data-colwidth")
        if width and width.split(",")[0].strip().isdigit():
            part += (f'<w:tcW w:w="{int(width.split(",")[0]) * _TWIPS_PER_PX}" '
                     f'w:type="dxa"/>')
        background = _color(style.get("background-color"))
        if background:
            part += f'<w:shd w:val="clear" w:color="auto" w:fill="{background}"/>'
        #  Ô khai `border-*: hidden` (khối đầu văn bản hai cột) phải mất viền
        #  trong Word, nếu không bản xuất ra kẻ ô lù lù giữa quốc hiệu.
        an = [c for c in ("top", "left", "bottom", "right")
              if (style.get(f"border-{c}") or "").strip().startswith("hidden")]
        if an:
            part += ("<w:tcBorders>"
                     + "".join(f'<w:{c} w:val="nil"/>' for c in an)
                     + "</w:tcBorders>")
        if attrs.get("colspan", "").isdigit() and int(attrs["colspan"]) > 1:
            part += f'<w:gridSpan w:val="{attrs["colspan"]}"/>'
        return f'<w:tc><w:tcPr>{part}</w:tcPr>' if part else "<w:tc><w:tcPr/>"

    def _insert_image(self, attrs: dict[str, str]) -> None:
        src = attrs.get("src", "")
        matched = re.match(r"^data:image/([a-z]+);base64,(.+)$", src, re.I | re.S)
        if not matched:
            #  Ảnh trỏ ra ngoài: không tải về trong lúc xuất tệp (chậm, và có thể
            #  là đường dẫn nội bộ người nhận không mở được). Ghi chú thay chỗ.
            self._add_run("[ảnh]")
            return
        ext = matched.group(1).lower()
        ext = "jpg" if ext == "jpeg" else ext
        try:
            data = base64.b64decode(matched.group(2))
        except Exception:      # noqa: BLE001 — ảnh hỏng thì bỏ qua, không chặn cả tệp
            return

        stt = len(self.images) + 1
        images = EmbeddedImage(name=f"anh{stt}.{ext}", data=data, ext=ext,
                       rid=f"rIdAnh{stt}")
        self.images.append(images)

        width_px = _px(attrs.get("width", "")) or float(attrs.get("width") or 480)
        height_px = _px(attrs.get("height", "")) or float(attrs.get("height") or 0) or width_px * 0.62
        cx, cy = int(width_px * _EMU_PER_PX), int(height_px * _EMU_PER_PX)
        self._runs.append(
            f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{stt}" name="Anh {stt}"/>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/'
            f'drawingml/2006/picture">'
            f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{stt}" name="{images.name}"/>'
            f'<pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{images.rid}"/><a:stretch><a:fillRect/>'
            f'</a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'
        )

    def finish(self) -> str:
        self._close_paragraph()
        return "".join(self.out) or "<w:p/>"


def _render_page_frame(template: str, replacements: dict[str, str]) -> str:
    """Một vế đầu/chân trang → chuỗi run XML, thẻ số trang thành trường Word."""
    if not template:
        return ""
    part: list[str] = []
    remaining = template
    for tag, field_code in (("{{trang}}", "PAGE"), ("{{tong_trang}}", "NUMPAGES")):
        new: list[str] = []
        for i, chunk in enumerate(remaining.split(tag)):
            if i:
                new.append("\x00" + field_code + "\x00")
            new.append(chunk)
        remaining = "".join(new)
    for chunk in remaining.split("\x00"):
        if chunk in {"PAGE", "NUMPAGES"}:
            part.append(page_number_field(chunk))
            continue
        for tag, value in replacements.items():
            chunk = chunk.replace(tag, value)
        if chunk:
            part.append(f'<w:r><w:t xml:space="preserve">{xml_escape(chunk)}</w:t></w:r>')
    return "".join(part)


def html_to_docx(
    html_content: str,
    *,
    margin_left_mm: int = 30,
    margin_right_mm: int = 20,
    number_headings: bool = False,
    header: tuple[str, str] = ("", ""),
    footer: tuple[str, str] = ("", ""),
    replacements: dict[str, str] | None = None,
) -> bytes:
    """Chuyển nội dung một phiên bản văn bản thành tệp .docx (bytes)."""
    converter = _Converter(number_headings=number_headings)
    converter.feed(html_content or "")
    converter.close()

    replacements = replacements or {}
    pkg = DocxPackage(body_xml=converter.finish(), images=converter.images)

    left, right = (_render_page_frame(o, replacements) for o in header)
    if left or right:
        pkg.header_xml = header_footer_paragraph(left, right)
    left, right = (_render_page_frame(o, replacements) for o in footer)
    if left or right:
        pkg.footer_xml = header_footer_paragraph(left, right)

    return pack(pkg, margin_left_mm=margin_left_mm, margin_right_mm=margin_right_mm)
