"""Chuyển Word OpenXML (.docx) thành HTML mà Tiptap có thể sửa tiếp.

Không cố tái hiện mọi chi tiết dàn trang độc quyền của Word. Bộ chuyển đổi giữ
những định dạng mà trình soạn thảo văn bản của ERP hỗ trợ thật sự: style kế
thừa, phông/cỡ/màu chữ, căn lề và khoảng cách đoạn, danh sách, liên kết, ảnh,
bảng và các ô gộp. Làm trực tiếp trên OpenXML để image API không phải kéo theo
LibreOffice (hàng trăm MB) chỉ cho một endpoint nhập tệp.
"""
from __future__ import annotations

import base64
import html
import mimetypes
import posixpath
import re
import zipfile
from dataclasses import dataclass
from io import BytesIO
from xml.etree import ElementTree

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
_WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
_PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

_W = f"{{{_W_NS}}}"
_R = f"{{{_R_NS}}}"
_A = f"{{{_A_NS}}}"
_WP = f"{{{_WP_NS}}}"
_PR = f"{{{_PR_NS}}}"

_EMU_PER_PX = 9_525
_TWIPS_PER_PX = 15

# Word đo giãn dòng theo CHIỀU CAO MỘT DÒNG ĐƠN của bộ phông, CSS đo theo CỠ CHỮ.
# Times New Roman — phông quy định của văn bản hành chính — có dòng đơn cao 1,15
# lần cỡ chữ, nên "1.5 lines" trong Word phải ra `line-height: 1.725` thì trang
# web mới giãn đúng bằng bản gốc. Xem thêm
# `frontend-v2/src/shared/ui/rich-text-editor/word-line-spacing.ts`.
_SINGLE_LINE_RATIO = 1.15

_HIGHLIGHT_COLORS = {
    "black": "#000000",
    "blue": "#0000ff",
    "cyan": "#00ffff",
    "darkblue": "#00008b",
    "darkcyan": "#008b8b",
    "darkgray": "#a9a9a9",
    "darkgreen": "#006400",
    "darkmagenta": "#8b008b",
    "darkred": "#8b0000",
    "darkyellow": "#808000",
    "green": "#00ff00",
    "lightgray": "#d3d3d3",
    "magenta": "#ff00ff",
    "red": "#ff0000",
    "white": "#ffffff",
    "yellow": "#ffff00",
}

_IMAGE_MIME_TYPES = {
    "image/bmp",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
}


def _val(element: ElementTree.Element | None, default: str = "") -> str:
    return element.get(f"{_W}val", default) if element is not None else default


def _bool_value(element: ElementTree.Element | None) -> bool | None:
    if element is None:
        return None
    return _val(element, "1").lower() not in {"0", "false", "off", "none"}


def _number(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _css_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.3f}".rstrip("0").rstrip(".")


def _css_color(value: str | None) -> str | None:
    value = (value or "").strip().lstrip("#")
    if re.fullmatch(r"[0-9a-fA-F]{6}", value):
        return f"#{value.lower()}"
    if re.fullmatch(r"[0-9a-fA-F]{3}", value):
        return f"#{value.lower()}"
    return None


def _css_font(value: str | None) -> str | None:
    """Chỉ nhận ký tự hợp lệ trong tên phông trước khi ghi vào style nội tuyến."""
    cleaned = re.sub(r"[^\w\s.,()\-]", "", value or "", flags=re.UNICODE).strip()
    return cleaned[:120] or None


def _merge(*values: dict) -> dict:
    merged: dict = {}
    for value in values:
        merged.update(value)
    return merged


@dataclass(frozen=True)
class _Relationship:
    target: str
    kind: str
    external: bool


@dataclass(frozen=True)
class _Style:
    style_id: str
    name: str
    kind: str
    based_on: str | None
    paragraph: dict
    run: dict


@dataclass(frozen=True)
class _ListInfo:
    num_id: str
    level: int
    tag: str
    start: int


class DocxHtmlConverter:
    def __init__(self, raw: bytes):
        try:
            self.archive = zipfile.ZipFile(BytesIO(raw))
            self.document_root = ElementTree.fromstring(self.archive.read("word/document.xml"))
        except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
            raise ValueError("Tệp .docx không hợp lệ hoặc đã bị hỏng") from exc

        self.theme_fonts: dict[str, str] = {}
        self.theme_colors: dict[str, str] = {}
        self.default_paragraph: dict = {}
        self.default_run: dict = {}
        self.styles: dict[str, _Style] = {}
        self.style_cache: dict[tuple[str, str], dict] = {}
        self.numbering: dict[tuple[str, int], tuple[str, int]] = {}
        self.relationship_cache: dict[str, dict[str, _Relationship]] = {}

        self._read_theme()
        self._read_styles()
        self._read_numbering()

    def convert(self) -> str:
        body = self.document_root.find(f"{_W}body")
        if body is None:
            raise ValueError("Tệp .docx không có nội dung")

        # Header không có khái niệm tương ứng trong editor. Đưa nội dung header
        # (thường là logo/tiêu ngữ) vào đầu tài liệu một lần vẫn đúng ý người
        # nhập hơn là âm thầm làm mất hẳn như parser cũ.
        header = self._default_header(body)
        content = self._render_blocks(list(body), "word/document.xml")
        return f"{header}{content}"

    def _read_xml(self, path: str) -> ElementTree.Element | None:
        try:
            return ElementTree.fromstring(self.archive.read(path))
        except (KeyError, ElementTree.ParseError):
            return None

    def _read_theme(self) -> None:
        root = self._read_xml("word/theme/theme1.xml")
        if root is None:
            return

        scheme = root.find(f".//{_A}fontScheme")
        if scheme is not None:
            for prefix, tag in (("major", "majorFont"), ("minor", "minorFont")):
                group = scheme.find(f"{_A}{tag}")
                if group is None:
                    continue
                latin = group.find(f"{_A}latin")
                east_asia = group.find(f"{_A}ea")
                complex_script = group.find(f"{_A}cs")
                latin_name = _css_font(latin.get("typeface") if latin is not None else None)
                east_name = _css_font(
                    east_asia.get("typeface") if east_asia is not None else None
                )
                complex_name = _css_font(
                    complex_script.get("typeface") if complex_script is not None else None
                )
                if latin_name:
                    self.theme_fonts[f"{prefix}Ascii"] = latin_name
                    self.theme_fonts[f"{prefix}HAnsi"] = latin_name
                if east_name:
                    self.theme_fonts[f"{prefix}EastAsia"] = east_name
                if complex_name:
                    self.theme_fonts[f"{prefix}Bidi"] = complex_name

        colors = root.find(f".//{_A}clrScheme")
        if colors is not None:
            for item in colors:
                value_node = next(iter(item), None)
                if value_node is None:
                    continue
                value = value_node.get("val") or value_node.get("lastClr")
                color = _css_color(value)
                if color:
                    self.theme_colors[item.tag.rsplit("}", 1)[-1]] = color

    def _read_styles(self) -> None:
        root = self._read_xml("word/styles.xml")
        if root is None:
            return

        defaults = root.find(f"{_W}docDefaults")
        if defaults is not None:
            self.default_run = self._run_properties(
                defaults.find(f"{_W}rPrDefault/{_W}rPr")
            )
            self.default_paragraph = self._paragraph_properties(
                defaults.find(f"{_W}pPrDefault/{_W}pPr")
            )

        for node in root.findall(f"{_W}style"):
            style_id = node.get(f"{_W}styleId", "")
            if not style_id:
                continue
            based_on_node = node.find(f"{_W}basedOn")
            self.styles[style_id] = _Style(
                style_id=style_id,
                name=_val(node.find(f"{_W}name"), style_id),
                kind=node.get(f"{_W}type", "paragraph"),
                based_on=_val(based_on_node) if based_on_node is not None else None,
                paragraph=self._paragraph_properties(node.find(f"{_W}pPr")),
                run=self._run_properties(node.find(f"{_W}rPr")),
            )

    def _resolved_style(self, style_id: str | None, part: str) -> dict:
        if not style_id:
            return {}
        key = (style_id, part)
        if key in self.style_cache:
            return self.style_cache[key]
        style = self.styles.get(style_id)
        if style is None:
            return {}

        # Chặn tài liệu hỏng tự tạo vòng basedOn A → B → A.
        self.style_cache[key] = {}
        inherited = self._resolved_style(style.based_on, part)
        own = style.paragraph if part == "paragraph" else style.run
        resolved = _merge(inherited, own)
        self.style_cache[key] = resolved
        return resolved

    def _read_numbering(self) -> None:
        root = self._read_xml("word/numbering.xml")
        if root is None:
            return

        abstracts: dict[str, dict[int, tuple[str, int]]] = {}
        for abstract in root.findall(f"{_W}abstractNum"):
            abstract_id = abstract.get(f"{_W}abstractNumId", "")
            levels: dict[int, tuple[str, int]] = {}
            for level in abstract.findall(f"{_W}lvl"):
                index = int(level.get(f"{_W}ilvl", "0") or 0)
                number_format = _val(level.find(f"{_W}numFmt"), "bullet")
                start = int(_val(level.find(f"{_W}start"), "1") or 1)
                levels[index] = (number_format, start)
            abstracts[abstract_id] = levels

        for number in root.findall(f"{_W}num"):
            num_id = number.get(f"{_W}numId", "")
            abstract_id = _val(number.find(f"{_W}abstractNumId"))
            levels = dict(abstracts.get(abstract_id, {}))
            for override in number.findall(f"{_W}lvlOverride"):
                index = int(override.get(f"{_W}ilvl", "0") or 0)
                level = override.find(f"{_W}lvl")
                if level is not None:
                    fmt = _val(level.find(f"{_W}numFmt"), levels.get(index, ("bullet", 1))[0])
                    start = int(_val(level.find(f"{_W}start"), str(levels.get(index, ("", 1))[1])))
                    levels[index] = (fmt, start)
                start_override = override.find(f"{_W}startOverride")
                if start_override is not None:
                    fmt = levels.get(index, ("decimal", 1))[0]
                    levels[index] = (fmt, int(_val(start_override, "1") or 1))
            for index, value in levels.items():
                self.numbering[(num_id, index)] = value

    def _relationships(self, part_path: str) -> dict[str, _Relationship]:
        if part_path in self.relationship_cache:
            return self.relationship_cache[part_path]
        name = posixpath.basename(part_path)
        rel_path = posixpath.join(posixpath.dirname(part_path), "_rels", f"{name}.rels")
        root = self._read_xml(rel_path)
        relationships: dict[str, _Relationship] = {}
        if root is not None:
            for node in root.findall(f"{_PR}Relationship"):
                rel_id = node.get("Id", "")
                if rel_id:
                    relationships[rel_id] = _Relationship(
                        target=node.get("Target", ""),
                        kind=node.get("Type", "").rsplit("/", 1)[-1],
                        external=node.get("TargetMode", "").lower() == "external",
                    )
        self.relationship_cache[part_path] = relationships
        return relationships

    def _part_target(self, part_path: str, relationship: _Relationship) -> str:
        return posixpath.normpath(
            posixpath.join(posixpath.dirname(part_path), relationship.target)
        )

    def _default_header(self, body: ElementTree.Element) -> str:
        relationships = self._relationships("word/document.xml")
        references = body.findall(f".//{_W}sectPr/{_W}headerReference")
        reference = next(
            (item for item in references if item.get(f"{_W}type", "default") == "default"),
            references[0] if references else None,
        )
        if reference is None:
            return ""
        relationship = relationships.get(reference.get(f"{_R}id", ""))
        if relationship is None or relationship.external:
            return ""
        path = self._part_target("word/document.xml", relationship)
        root = self._read_xml(path)
        return self._render_blocks(list(root), path) if root is not None else ""

    def _run_properties(self, properties: ElementTree.Element | None) -> dict:
        if properties is None:
            return {}
        result: dict = {}
        run_style = properties.find(f"{_W}rStyle")
        if run_style is not None:
            result["run_style"] = _val(run_style)

        fonts = properties.find(f"{_W}rFonts")
        if fonts is not None:
            font = next(
                (
                    _css_font(fonts.get(f"{_W}{name}"))
                    for name in ("ascii", "hAnsi", "eastAsia", "cs")
                    if fonts.get(f"{_W}{name}")
                ),
                None,
            )
            theme = next(
                (
                    fonts.get(f"{_W}{name}Theme")
                    for name in ("ascii", "hAnsi", "eastAsia", "cs")
                    if fonts.get(f"{_W}{name}Theme")
                ),
                None,
            )
            if font:
                result["font"] = font
            elif theme and self.theme_fonts.get(theme):
                result["font"] = self.theme_fonts[theme]

        for key, tag in (("bold", "b"), ("italic", "i"), ("strike", "strike")):
            value = _bool_value(properties.find(f"{_W}{tag}"))
            if value is not None:
                result[key] = value

        underline = properties.find(f"{_W}u")
        if underline is not None:
            result["underline"] = _val(underline, "single").lower() not in {"none", "0"}

        size = _number(_val(properties.find(f"{_W}sz")) or None)
        if size is not None and 1 <= size <= 600:
            result["font_size"] = size / 2

        color_node = properties.find(f"{_W}color")
        if color_node is not None:
            color = _css_color(_val(color_node))
            if not color:
                color = self.theme_colors.get(color_node.get(f"{_W}themeColor", ""))
            if color:
                result["color"] = color

        highlight = properties.find(f"{_W}highlight")
        if highlight is not None:
            color = _HIGHLIGHT_COLORS.get(_val(highlight).lower())
            if color:
                result["background"] = color
        shading = properties.find(f"{_W}shd")
        if shading is not None:
            color = _css_color(shading.get(f"{_W}fill"))
            if color:
                result["background"] = color

        vertical = _val(properties.find(f"{_W}vertAlign")).lower()
        if vertical in {"subscript", "superscript"}:
            result["vertical"] = vertical

        spacing = _number(_val(properties.find(f"{_W}spacing")) or None)
        if spacing is not None:
            result["letter_spacing"] = spacing / 20
        return result

    def _paragraph_properties(self, properties: ElementTree.Element | None) -> dict:
        if properties is None:
            return {}
        result: dict = {}
        paragraph_style = properties.find(f"{_W}pStyle")
        if paragraph_style is not None:
            result["paragraph_style"] = _val(paragraph_style)

        alignment = _val(properties.find(f"{_W}jc")).lower()
        if alignment:
            result["alignment"] = {
                "both": "justify",
                "distribute": "justify",
                "start": "left",
                "end": "right",
            }.get(alignment, alignment)

        spacing = properties.find(f"{_W}spacing")
        if spacing is not None:
            line = _number(spacing.get(f"{_W}line"))
            rule = spacing.get(f"{_W}lineRule", "auto")
            if line is not None:
                # `auto` = bội số dòng (w:line 360 = 1,5 dòng) — phải nhân thêm
                # `_SINGLE_LINE_RATIO` mới ra đúng con số của CSS. Hai kiểu còn
                # lại (`exact` / `atLeast`) đã là chiều cao tuyệt đối tính bằng
                # twip nên đổi thẳng sang px.
                result["line_height"] = (
                    _css_number(line / 240 * _SINGLE_LINE_RATIO)
                    if rule == "auto"
                    else f"{_css_number(line / _TWIPS_PER_PX)}px"
                )
            before = _number(spacing.get(f"{_W}before"))
            after = _number(spacing.get(f"{_W}after"))
            if before is not None:
                result["space_before"] = before / _TWIPS_PER_PX
            if after is not None:
                result["space_after"] = after / _TWIPS_PER_PX

        indent = properties.find(f"{_W}ind")
        if indent is not None:
            left = _number(indent.get(f"{_W}left") or indent.get(f"{_W}start"))
            right = _number(indent.get(f"{_W}right") or indent.get(f"{_W}end"))
            first_line = _number(indent.get(f"{_W}firstLine"))
            hanging = _number(indent.get(f"{_W}hanging"))
            if left is not None:
                result["indent_left"] = left / _TWIPS_PER_PX
            if right is not None:
                result["indent_right"] = right / _TWIPS_PER_PX
            if first_line is not None:
                result["text_indent"] = first_line / _TWIPS_PER_PX
            elif hanging is not None:
                result["text_indent"] = -hanging / _TWIPS_PER_PX

        shading = properties.find(f"{_W}shd")
        if shading is not None:
            color = _css_color(shading.get(f"{_W}fill"))
            if color and color != "#ffffff":
                result["background"] = color

        outline = _number(_val(properties.find(f"{_W}outlineLvl")) or None)
        if outline is not None and 0 <= outline <= 5:
            result["heading"] = int(outline) + 1

        numbering = properties.find(f"{_W}numPr")
        if numbering is not None:
            num_id = _val(numbering.find(f"{_W}numId"))
            level = int(_val(numbering.find(f"{_W}ilvl"), "0") or 0)
            if num_id and num_id != "0":
                result["num_id"] = num_id
                result["num_level"] = level
        return result

    def _resolved_paragraph(self, paragraph: ElementTree.Element) -> tuple[dict, ElementTree.Element | None]:
        direct = paragraph.find(f"{_W}pPr")
        direct_props = self._paragraph_properties(direct)
        style_id = direct_props.get("paragraph_style")
        return _merge(
            self.default_paragraph,
            self._resolved_style(style_id, "paragraph"),
            direct_props,
        ), direct

    def _resolved_run(
        self,
        paragraph_props: dict,
        paragraph_pr: ElementTree.Element | None,
        run_pr: ElementTree.Element | None,
    ) -> dict:
        paragraph_style = paragraph_props.get("paragraph_style")
        paragraph_run = self._resolved_style(paragraph_style, "run")
        paragraph_direct_run_node = (
            paragraph_pr.find(f"{_W}rPr") if paragraph_pr is not None else None
        )
        paragraph_direct_run = self._run_properties(paragraph_direct_run_node)
        paragraph_character = self._resolved_style(
            paragraph_direct_run.get("run_style"), "run"
        )
        direct_run = self._run_properties(run_pr)
        character = self._resolved_style(direct_run.get("run_style"), "run")
        return _merge(
            self.default_run,
            paragraph_run,
            paragraph_character,
            paragraph_direct_run,
            character,
            direct_run,
        )

    def _list_info(self, paragraph_props: dict) -> _ListInfo | None:
        num_id = paragraph_props.get("num_id")
        if not num_id:
            return None
        level = int(paragraph_props.get("num_level", 0))
        number_format, start = self.numbering.get((num_id, level), ("bullet", 1))
        tag = "ul" if number_format == "bullet" else "ol"
        return _ListInfo(num_id=num_id, level=level, tag=tag, start=start)

    def _paragraph_css(self, properties: dict, *, in_list: bool) -> str:
        # `margin-top: 0` vô hiệu khoảng cách mặc định `.doc-page > * + *` để
        # khoảng trước/sau lấy đúng từ Word, kể cả khi Word ghi giá trị bằng 0.
        styles = [f"margin-top: {_css_number(float(properties.get('space_before', 0)))}px"]
        if not in_list:
            if properties.get("indent_right"):
                styles.append(
                    f"margin-right: {_css_number(float(properties['indent_right']))}px"
                )
        if "space_after" in properties:
            styles.append(f"margin-bottom: {_css_number(float(properties['space_after']))}px")
        if not in_list:
            if properties.get("indent_left"):
                styles.append(
                    f"margin-left: {_css_number(float(properties['indent_left']))}px"
                )
            if properties.get("text_indent"):
                styles.append(
                    f"text-indent: {_css_number(float(properties['text_indent']))}px"
                )
        if properties.get("line_height"):
            styles.append(f"line-height: {properties['line_height']}")
        if properties.get("alignment") in {"left", "right", "center", "justify"}:
            styles.append(f"text-align: {properties['alignment']}")
        if properties.get("background"):
            styles.append(f"background-color: {properties['background']}")
        return "; ".join(styles)

    def _heading_level(self, properties: dict) -> int | None:
        if properties.get("heading"):
            return int(properties["heading"])
        style_id = str(properties.get("paragraph_style", ""))
        style_name = self.styles.get(style_id).name if style_id in self.styles else style_id
        match = re.search(r"(?:heading|tiêu\s*đề|tieude)\s*([1-6])", style_name, re.I)
        return int(match.group(1)) if match else None

    def _render_blocks(self, blocks: list[ElementTree.Element], part_path: str) -> str:
        rendered: list[str] = []
        index = 0
        while index < len(blocks):
            block = blocks[index]
            if block.tag == f"{_W}p":
                properties, _ = self._resolved_paragraph(block)
                if self._list_info(properties):
                    list_html, index = self._render_list(blocks, index, part_path)
                    rendered.append(list_html)
                    continue
                rendered.append(self._paragraph_html(block, part_path))
            elif block.tag == f"{_W}tbl":
                rendered.append(self._table_html(block, part_path))
            index += 1
        return "".join(rendered)

    def _render_list(
        self,
        blocks: list[ElementTree.Element],
        start_index: int,
        part_path: str,
    ) -> tuple[str, int]:
        first_props, _ = self._resolved_paragraph(blocks[start_index])
        first = self._list_info(first_props)
        if first is None:
            return "", start_index

        def level_at(index: int, level: int) -> tuple[str, int]:
            props, _ = self._resolved_paragraph(blocks[index])
            info = self._list_info(props)
            if info is None:
                return "", index
            attrs = f' start="{info.start}"' if info.tag == "ol" and info.start != 1 else ""
            items: list[str] = []
            cursor = index
            while cursor < len(blocks) and blocks[cursor].tag == f"{_W}p":
                current_props, _ = self._resolved_paragraph(blocks[cursor])
                current = self._list_info(current_props)
                if (
                    current is None
                    or current.level < level
                    or (current.level == level and (
                        current.num_id != info.num_id or current.tag != info.tag
                    ))
                ):
                    break
                if current.level > level:
                    # Nhánh này được lời gọi ngay sau một <li> xử lý; nếu file
                    # bắt đầu ở level lẻ thì coi level đó là gốc thay vì bỏ chữ.
                    break

                item = self._paragraph_html(blocks[cursor], part_path, in_list=True)
                cursor += 1
                nested: list[str] = []
                while cursor < len(blocks) and blocks[cursor].tag == f"{_W}p":
                    next_props, _ = self._resolved_paragraph(blocks[cursor])
                    next_info = self._list_info(next_props)
                    if next_info is None or next_info.level <= level:
                        break
                    child, next_cursor = level_at(cursor, next_info.level)
                    if next_cursor == cursor:
                        break
                    nested.append(child)
                    cursor = next_cursor
                items.append(f"<li>{item}{''.join(nested)}</li>")
            return f"<{info.tag}{attrs}>{''.join(items)}</{info.tag}>", cursor

        return level_at(start_index, first.level)

    def _paragraph_html(
        self,
        paragraph: ElementTree.Element,
        part_path: str,
        *,
        in_list: bool = False,
    ) -> str:
        properties, direct_pr = self._resolved_paragraph(paragraph)
        content: list[str] = []
        for child in paragraph:
            if child.tag == f"{_W}r":
                content.append(self._run_html(child, properties, direct_pr, part_path))
            elif child.tag == f"{_W}hyperlink":
                content.append(
                    self._hyperlink_html(child, properties, direct_pr, part_path)
                )
            elif child.tag in {f"{_W}smartTag", f"{_W}sdt"}:
                for run in child.iter(f"{_W}r"):
                    content.append(self._run_html(run, properties, direct_pr, part_path))

        level = self._heading_level(properties)
        tag = f"h{level}" if level else "p"
        css = html.escape(self._paragraph_css(properties, in_list=in_list), quote=True)
        value = "".join(content)
        # Image của Tiptap là block node. Để <img> trần khi một đoạn Word chỉ
        # chứa ảnh (logo header là trường hợp phổ biến); nhét nó vào <p>/<span>
        # là HTML không hợp lệ và ProseMirror có thể bỏ ảnh lúc parse.
        if value and re.fullmatch(r"(?:<img\b[^>]*>)+", value):
            return value
        return f'<{tag} style="{css}">{value}</{tag}>'

    def _run_html(
        self,
        run: ElementTree.Element,
        paragraph_props: dict,
        paragraph_pr: ElementTree.Element | None,
        part_path: str,
    ) -> str:
        parts: list[tuple[str, bool]] = []
        for node in run:
            if node.tag in {f"{_W}t", f"{_W}delText", f"{_W}instrText"}:
                parts.append((html.escape(node.text or ""), True))
            elif node.tag == f"{_W}tab":
                parts.append(("&emsp;", True))
            elif node.tag in {f"{_W}br", f"{_W}cr"}:
                parts.append(("<br>", True))
            elif node.tag == f"{_W}noBreakHyphen":
                parts.append(("&#8209;", True))
            elif node.tag == f"{_W}softHyphen":
                parts.append(("&shy;", True))
            elif node.tag == f"{_W}drawing":
                parts.append((self._image_html(node, part_path), False))
        if not parts:
            return ""

        properties = self._resolved_run(paragraph_props, paragraph_pr, run.find(f"{_W}rPr"))
        return "".join(
            self._styled_run_segment(value, properties) if styled else value
            for value, styled in parts
        )

    def _styled_run_segment(self, value: str, properties: dict) -> str:
        if not value:
            return ""
        styles: list[str] = []
        if properties.get("font"):
            styles.append(f'font-family: "{properties["font"]}"')
        if properties.get("font_size"):
            styles.append(f"font-size: {_css_number(float(properties['font_size']))}pt")
        if properties.get("color"):
            styles.append(f"color: {properties['color']}")
        if properties.get("background"):
            styles.append(f"background-color: {properties['background']}")
        if properties.get("letter_spacing"):
            styles.append(
                f"letter-spacing: {_css_number(float(properties['letter_spacing']))}pt"
            )
        if styles:
            value = f'<span style="{html.escape("; ".join(styles), quote=True)}">{value}</span>'
        if properties.get("bold"):
            value = f"<strong>{value}</strong>"
        if properties.get("italic"):
            value = f"<em>{value}</em>"
        if properties.get("underline"):
            value = f"<u>{value}</u>"
        if properties.get("strike"):
            value = f"<s>{value}</s>"
        if properties.get("vertical") == "subscript":
            value = f"<sub>{value}</sub>"
        elif properties.get("vertical") == "superscript":
            value = f"<sup>{value}</sup>"
        return value

    def _hyperlink_html(
        self,
        hyperlink: ElementTree.Element,
        paragraph_props: dict,
        paragraph_pr: ElementTree.Element | None,
        part_path: str,
    ) -> str:
        value = "".join(
            self._run_html(run, paragraph_props, paragraph_pr, part_path)
            for run in hyperlink.findall(f"{_W}r")
        )
        rel_id = hyperlink.get(f"{_R}id", "")
        relationship = self._relationships(part_path).get(rel_id)
        if not value or relationship is None or not relationship.external:
            return value
        href = html.escape(relationship.target, quote=True)
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{value}</a>'

    def _image_html(self, drawing: ElementTree.Element, part_path: str) -> str:
        blip = drawing.find(f".//{_A}blip")
        rel_id = blip.get(f"{_R}embed", "") if blip is not None else ""
        relationship = self._relationships(part_path).get(rel_id)
        if relationship is None or relationship.external:
            return ""
        target = self._part_target(part_path, relationship)
        mime, _ = mimetypes.guess_type(target)
        if mime not in _IMAGE_MIME_TYPES:
            return ""
        try:
            payload = self.archive.read(target)
        except KeyError:
            return ""

        extent = drawing.find(f".//{_WP}extent")
        width = round(float(extent.get("cx", "0")) / _EMU_PER_PX) if extent is not None else 0
        height = round(float(extent.get("cy", "0")) / _EMU_PER_PX) if extent is not None else 0
        doc_properties = drawing.find(f".//{_WP}docPr")
        alt = ""
        title = ""
        if doc_properties is not None:
            alt = doc_properties.get("descr") or doc_properties.get("name") or ""
            title = doc_properties.get("title", "")
        attributes = [
            f'src="data:{mime};base64,{base64.b64encode(payload).decode("ascii")}"',
            f'alt="{html.escape(alt, quote=True)}"',
        ]
        if title:
            attributes.append(f'title="{html.escape(title, quote=True)}"')
        if width > 0:
            attributes.append(f'width="{width}"')
        if height > 0:
            attributes.append(f'height="{height}"')
        return f"<img {' '.join(attributes)}>"

    def _table_html(self, table: ElementTree.Element, part_path: str) -> str:
        grid_widths = [
            max(1, round(float(column.get(f"{_W}w", "0")) / _TWIPS_PER_PX))
            for column in table.findall(f"{_W}tblGrid/{_W}gridCol")
        ]
        rows: list[list[dict]] = []
        active_vertical: dict[int, dict] = {}

        for row_node in table.findall(f"{_W}tr"):
            cells: list[dict] = []
            column = 0
            row_header = row_node.find(f"{_W}trPr/{_W}tblHeader") is not None
            for cell_node in row_node.findall(f"{_W}tc"):
                cell_pr = cell_node.find(f"{_W}tcPr")
                span = int(_val(cell_pr.find(f"{_W}gridSpan"), "1") or 1) if cell_pr is not None else 1
                merge_node = cell_pr.find(f"{_W}vMerge") if cell_pr is not None else None
                merge = _val(merge_node, "continue") if merge_node is not None else None
                if merge == "continue" and column in active_vertical:
                    active_vertical[column]["rowspan"] += 1
                    column += span
                    continue

                for occupied in range(column, column + span):
                    active_vertical.pop(occupied, None)
                cell = {
                    "node": cell_node,
                    "column": column,
                    "colspan": span,
                    "rowspan": 1,
                    "header": row_header,
                }
                cells.append(cell)
                if merge == "restart":
                    for occupied in range(column, column + span):
                        active_vertical[occupied] = cell
                column += span
            rows.append(cells)

        rendered_rows: list[str] = []
        for row_node, cells in zip(table.findall(f"{_W}tr"), rows):
            height_node = row_node.find(f"{_W}trPr/{_W}trHeight")
            height = _number(height_node.get(f"{_W}val")) if height_node is not None else None
            row_style = (
                f' style="height: {_css_number(height / _TWIPS_PER_PX)}px"'
                if height
                else ""
            )
            rendered_cells: list[str] = []
            for cell in cells:
                node = cell["node"]
                cell_pr = node.find(f"{_W}tcPr")
                tag = "th" if cell["header"] else "td"
                attributes: list[str] = []
                if cell["colspan"] > 1:
                    attributes.append(f'colspan="{cell["colspan"]}"')
                if cell["rowspan"] > 1:
                    attributes.append(f'rowspan="{cell["rowspan"]}"')
                widths = grid_widths[
                    cell["column"] : cell["column"] + cell["colspan"]
                ]
                if widths:
                    attributes.append(f'data-colwidth="{",".join(map(str, widths))}"')
                styles = self._cell_styles(cell_pr)
                if styles:
                    attributes.append(f'style="{html.escape("; ".join(styles), quote=True)}"')
                content = self._render_blocks(list(node), part_path) or "<p></p>"
                suffix = f" {' '.join(attributes)}" if attributes else ""
                rendered_cells.append(f"<{tag}{suffix}>{content}</{tag}>")
            rendered_rows.append(f"<tr{row_style}>{''.join(rendered_cells)}</tr>")
        return f"<table><tbody>{''.join(rendered_rows)}</tbody></table>" if rendered_rows else ""

    def _cell_styles(self, properties: ElementTree.Element | None) -> list[str]:
        if properties is None:
            return []
        styles: list[str] = []
        shading = properties.find(f"{_W}shd")
        if shading is not None:
            color = _css_color(shading.get(f"{_W}fill"))
            if color:
                styles.append(f"background-color: {color}")
        vertical = _val(properties.find(f"{_W}vAlign")).lower()
        if vertical in {"top", "center", "bottom"}:
            styles.append(f"vertical-align: {'middle' if vertical == 'center' else vertical}")
        borders = properties.find(f"{_W}tcBorders")
        if borders is not None:
            for side in ("top", "right", "bottom", "left"):
                border = borders.find(f"{_W}{side}")
                if border is None:
                    continue
                kind = _val(border, "single")
                if kind in {"nil", "none"}:
                    styles.append(f"border-{side}: none")
                    continue
                color = _css_color(border.get(f"{_W}color")) or "#000000"
                size = _number(border.get(f"{_W}sz")) or 6
                line = "dashed" if "dash" in kind else "dotted" if "dot" in kind else "solid"
                styles.append(
                    f"border-{side}: {_css_number(max(1.0, size / 6))}px {line} {color}"
                )
        return styles


def docx_to_html(raw: bytes) -> str:
    converter = DocxHtmlConverter(raw)
    try:
        return converter.convert()
    finally:
        converter.archive.close()
