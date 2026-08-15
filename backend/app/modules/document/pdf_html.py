"""Chuyển PDF thành HTML có thể tiếp tục chỉnh sửa trong Tiptap.

PDF chỉ lưu glyph tại tọa độ, không có khái niệm đoạn/heading như DOCX. Với
PDF có lớp chữ, bộ chuyển đổi dựng lại từng dòng và giữ font, cỡ, màu, kiểu chữ,
căn lề cùng hyperlink. Với trang scan không có lớp chữ, trang được raster hóa
thành ảnh để không làm mất nội dung hoặc hình thức của tài liệu.
"""
from __future__ import annotations

import base64
import html
import re
import statistics
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError
from pdfminer.psparser import PSEOF
from PIL import Image

MAX_PAGES = 60
PX_PER_POINT = 4 / 3
EDITOR_CONTENT_WIDTH = 642


@dataclass(frozen=True)
class _LineBlock:
    top: float
    bottom: float
    x0: float
    x1: float
    chars: list[dict[str, Any]]


@dataclass(frozen=True)
class _ImageBlock:
    top: float
    bottom: float
    html: str


def _source_marker(content: str, import_id: str | None, page_number: int) -> str:
    """Gắn mốc nguồn vào node đầu trang để UI có thể nhảy tới chỗ cần rà soát."""
    if not import_id:
        return content
    marker = (
        f' data-import-id="{html.escape(import_id, quote=True)}"'
        f' data-source-page="{page_number}"'
    )
    return re.sub(r"<(p|h[1-6]|img)\b", rf"<\1{marker}", content, count=1, flags=re.I)


def _number(value: Any, default: float = 0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _css_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.2f}".rstrip("0").rstrip(".")


def _font_info(raw_name: Any) -> tuple[str, bool, bool]:
    raw = str(raw_name or "Arial").split("+", 1)[-1]
    low = raw.lower()
    bold = any(token in low for token in ("bold", "semibold", "demi", "black", "heavy"))
    italic = any(token in low for token in ("italic", "oblique", "slanted"))

    family = re.sub(
        r"(?i)[,_-]?(?:bold|semibold|demi|black|heavy|italic|oblique|slanted|regular)+$",
        "",
        raw,
    )
    family = re.sub(r"(?i)(?:PSMT|MT)$", "", family).replace("-", " ").strip()
    normalized = family.lower().replace(" ", "")
    if normalized.startswith("timesnewroman") or normalized == "timesroman":
        family = "Times New Roman"
    elif normalized.startswith("helvetica") or normalized.startswith("arial"):
        family = "Arial"
    elif normalized.startswith("courier"):
        family = "Courier New"
    family = re.sub(r"[^\w\s.,()\-]", "", family, flags=re.UNICODE).strip()[:120]
    return family or "Arial", bold, italic


def _color(value: Any) -> str | None:
    if isinstance(value, (int, float)):
        channels = [float(value)]
    elif isinstance(value, (tuple, list)):
        channels = [_number(item) for item in value]
    else:
        return None

    if any(channel > 1 for channel in channels):
        channels = [channel / 255 for channel in channels]
    channels = [min(1.0, max(0.0, channel)) for channel in channels]
    if len(channels) == 1:
        red = green = blue = channels[0]
    elif len(channels) == 3:
        red, green, blue = channels
    elif len(channels) == 4:
        cyan, magenta, yellow, black = channels
        red = 1 - min(1, cyan + black)
        green = 1 - min(1, magenta + black)
        blue = 1 - min(1, yellow + black)
    else:
        return None
    rgb = tuple(round(channel * 255) for channel in (red, green, blue))
    if rgb == (0, 0, 0):
        return None
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _link_for_char(char: dict[str, Any], links: list[dict[str, Any]]) -> str | None:
    center_x = (_number(char.get("x0")) + _number(char.get("x1"))) / 2
    center_y = (_number(char.get("top")) + _number(char.get("bottom"))) / 2
    for link in links:
        uri = link.get("uri")
        if not uri:
            continue
        if (
            _number(link.get("x0")) <= center_x <= _number(link.get("x1"))
            and _number(link.get("top")) <= center_y <= _number(link.get("bottom"))
        ):
            return str(uri)
    return None


def _char_style(char: dict[str, Any], links: list[dict[str, Any]]) -> tuple:
    family, bold, italic = _font_info(char.get("fontname"))
    size = min(200.0, max(1.0, _number(char.get("size"), 12)))
    return (
        family,
        round(size, 2),
        _color(char.get("non_stroking_color")),
        bold,
        italic,
        _link_for_char(char, links),
    )


def _styled_text(text: str, style: tuple) -> str:
    family, size, color, bold, italic, href = style
    value = html.escape(text)
    declarations = [
        f'font-family: "{family}"',
        f"font-size: {_css_number(float(size))}pt",
    ]
    if color:
        declarations.append(f"color: {color}")
    value = f'<span style="{html.escape("; ".join(declarations), quote=True)}">{value}</span>'
    if bold:
        value = f"<strong>{value}</strong>"
    if italic:
        value = f"<em>{value}</em>"
    if href:
        value = (
            f'<a href="{html.escape(str(href), quote=True)}" '
            f'target="_blank" rel="noopener noreferrer">{value}</a>'
        )
    return value


def _line_content(chars: list[dict[str, Any]], links: list[dict[str, Any]]) -> str:
    ordered = sorted(chars, key=lambda char: (_number(char.get("x0")), _number(char.get("top"))))
    groups: list[tuple[tuple, str]] = []
    previous: dict[str, Any] | None = None

    def append(style: tuple, text: str) -> None:
        if not text:
            return
        if groups and groups[-1][0] == style:
            groups[-1] = (style, groups[-1][1] + text)
        else:
            groups.append((style, text))

    for char in ordered:
        text = str(char.get("text") or "")
        if not text:
            continue
        style = _char_style(char, links)
        if previous is not None and not text[0].isspace():
            previous_text = str(previous.get("text") or "")
            gap = _number(char.get("x0")) - _number(previous.get("x1"))
            threshold = max(1.2, _number(previous.get("size"), 12) * 0.18)
            if previous_text and not previous_text[-1].isspace() and gap > threshold:
                append(_char_style(previous, links), " ")
        append(style, text)
        previous = char
    return "".join(_styled_text(text, style) for style, text in groups)


def _alignment(line: _LineBlock, page_width: float, base_left: float) -> tuple[str, float]:
    left = line.x0
    right = max(0.0, page_width - line.x1)
    width = max(0.0, line.x1 - line.x0)
    if width < page_width * 0.92 and abs(left - right) <= max(10, page_width * 0.03):
        return "center", 0
    if right <= max(8, page_width * 0.015) and left > base_left + 24:
        return "right", 0
    return "left", max(0.0, (left - base_left) * PX_PER_POINT)


def _line_html(
    line: _LineBlock,
    page_width: float,
    base_left: float,
    median_size: float,
    margin_top: float,
    links: list[dict[str, Any]],
) -> str:
    content = _line_content(line.chars, links)
    if not content:
        return ""
    alignment, indent = _alignment(line, page_width, base_left)
    styles = [
        f"margin-top: {_css_number(margin_top)}px",
        "margin-right: 0px",
        "margin-bottom: 0px",
        f"margin-left: {_css_number(indent)}px",
        "line-height: 1.15",
    ]
    if alignment != "left":
        styles.append(f"text-align: {alignment}")

    sizes = [_number(char.get("size"), median_size) for char in line.chars]
    line_size = max(sizes, default=median_size)
    bold_chars = sum(_font_info(char.get("fontname"))[1] for char in line.chars)
    mostly_bold = bold_chars >= max(1, len(line.chars) * 0.6)
    if mostly_bold and line_size >= median_size * 1.55:
        tag = "h1"
    elif mostly_bold and line_size >= median_size * 1.25:
        tag = "h2"
    else:
        tag = "p"
    return f'<{tag} style="{"; ".join(styles)}">{content}</{tag}>'


def _image_html(image: Image.Image, width: int, height: int, alt: str, *, page_scan: bool) -> str:
    target = BytesIO()
    if page_scan or image.width * image.height > 300_000:
        image.convert("RGB").save(target, format="JPEG", quality=78, optimize=True)
        mime = "image/jpeg"
    else:
        image.save(target, format="PNG", optimize=True)
        mime = "image/png"
    payload = base64.b64encode(target.getvalue()).decode("ascii")
    return (
        f'<img src="data:{mime};base64,{payload}" alt="{html.escape(alt, quote=True)}" '
        f'width="{width}" height="{height}">'
    )


def _render_page_scan(page: Any, page_number: int) -> str:
    page_image = page.to_image(resolution=96, antialias=True).original
    ratio = page_image.height / max(1, page_image.width)
    width = EDITOR_CONTENT_WIDTH
    return _image_html(
        page_image,
        width,
        round(width * ratio),
        f"Trang PDF {page_number} (ảnh quét)",
        page_scan=True,
    )


def _render_embedded_images(
    page: Any,
    has_text: bool,
    page_number: int,
) -> tuple[list[_ImageBlock], dict[str, int]]:
    blocks: list[_ImageBlock] = []
    seen: set[tuple[int, int, int, int]] = set()
    stats = {
        "detected": len(page.images),
        "rendered": 0,
        "background_skipped": 0,
        "failed": 0,
    }
    page_area = max(1.0, _number(page.width) * _number(page.height))
    for index, item in enumerate(page.images, start=1):
        x0 = max(0.0, _number(item.get("x0")))
        x1 = min(_number(page.width), _number(item.get("x1")))
        top = max(0.0, _number(item.get("top")))
        bottom = min(_number(page.height), _number(item.get("bottom")))
        if x1 - x0 < 12 or bottom - top < 12:
            continue
        key = tuple(round(value) for value in (x0, top, x1, bottom))
        if key in seen:
            continue
        seen.add(key)
        area = (x1 - x0) * (bottom - top)
        if has_text and area / page_area > 0.75:
            # Thường là ảnh nền hoặc bản scan có OCR ẩn; chèn thêm sẽ lặp toàn
            # bộ trang ngay bên cạnh phần chữ đã lấy được.
            stats["background_skipped"] += 1
            continue
        try:
            image = page.crop((x0, top, x1, bottom), strict=False).to_image(
                resolution=96,
                antialias=True,
            ).original
            width = min(EDITOR_CONTENT_WIDTH, max(1, round((x1 - x0) * PX_PER_POINT)))
            height = max(1, round(width * image.height / max(1, image.width)))
            blocks.append(
                _ImageBlock(
                    top=top,
                    bottom=bottom,
                    html=_image_html(
                        image,
                        width,
                        height,
                        f"Hình {index} từ trang PDF {page_number}",
                        page_scan=False,
                    ),
                )
            )
            stats["rendered"] += 1
        except Exception:
            # Một số PDF dùng mask / colorspace mà renderer không đọc được.
            # Không làm hỏng toàn bộ import chỉ vì một ảnh phụ bị lỗi.
            stats["failed"] += 1
            continue
    return blocks, stats


def _page_html(page: Any, page_number: int, import_id: str | None) -> tuple[str, dict[str, Any]]:
    text_page = page.dedupe_chars(tolerance=1, extra_attrs=("fontname", "size"))
    raw_lines = text_page.extract_text_lines(
        layout=False,
        strip=True,
        return_chars=True,
        x_tolerance=2,
        y_tolerance=3,
    )
    lines = [
        _LineBlock(
            top=_number(line.get("top")),
            bottom=_number(line.get("bottom")),
            x0=_number(line.get("x0")),
            x1=_number(line.get("x1")),
            chars=[char for char in line.get("chars", []) if char.get("text")],
        )
        for line in raw_lines
        if str(line.get("text") or "").strip()
    ]
    char_count = sum(len(line.chars) for line in lines)
    if not lines:
        content = _source_marker(_render_page_scan(page, page_number), import_id, page_number)
        return content, {
            "page": page_number,
            "mode": "image",
            "character_count": 0,
            "line_count": 0,
            "embedded_images_detected": len(page.images),
            "embedded_images_rendered": 1,
            "background_images_skipped": 0,
            "image_render_failures": 0,
            "replacement_characters": 0,
            "vector_elements": 0,
        }

    all_sizes = [
        _number(char.get("size"), 12)
        for line in lines
        for char in line.chars
        if _number(char.get("size")) > 0
    ]
    median_size = statistics.median(all_sizes) if all_sizes else 12
    candidate_lefts = [line.x0 for line in lines if line.x1 - line.x0 >= page.width * 0.2]
    if not candidate_lefts:
        candidate_lefts = [line.x0 for line in lines]
    ordered_lefts = sorted(candidate_lefts)
    base_left = statistics.median(ordered_lefts[: max(1, len(ordered_lefts) // 3)])
    links = list(page.hyperlinks or [])

    image_blocks, image_stats = _render_embedded_images(page, True, page_number)
    blocks: list[_LineBlock | _ImageBlock] = [*lines]
    blocks.extend(image_blocks)
    blocks.sort(key=lambda block: (block.top, 0 if isinstance(block, _ImageBlock) else 1))

    rendered: list[str] = []
    previous_bottom: float | None = None
    for block in blocks:
        if isinstance(block, _ImageBlock):
            rendered.append(block.html)
        else:
            gap = 0.0 if previous_bottom is None else max(0.0, block.top - previous_bottom)
            rendered.append(
                _line_html(
                    block,
                    _number(page.width),
                    base_left,
                    median_size,
                    min(160.0, gap * PX_PER_POINT),
                    links,
                )
            )
        previous_bottom = max(previous_bottom or block.bottom, block.bottom)
    replacement_characters = sum(
        str(char.get("text") or "").count("\ufffd")
        for line in lines
        for char in line.chars
    )
    vector_elements = sum(
        len(getattr(page, name, None) or []) for name in ("lines", "rects", "curves")
    )
    content = _source_marker("".join(rendered), import_id, page_number)
    return content, {
        "page": page_number,
        "mode": "editable_text",
        "character_count": char_count,
        "line_count": len(lines),
        "embedded_images_detected": image_stats["detected"],
        "embedded_images_rendered": image_stats["rendered"],
        "background_images_skipped": image_stats["background_skipped"],
        "image_render_failures": image_stats["failed"],
        "replacement_characters": replacement_characters,
        "vector_elements": vector_elements,
    }


def _trace_issue(code: str, severity: str, message: str, pages: list[int]) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "pages": pages,
    }


def pdf_to_html_with_trace(raw: bytes, import_id: str) -> tuple[str, dict[str, Any]]:
    try:
        with pdfplumber.open(BytesIO(raw), unicode_norm="NFC") as pdf:
            if not pdf.pages:
                raise ValueError("Tệp PDF không có trang nào")
            if len(pdf.pages) > MAX_PAGES:
                raise ValueError(f"Tệp PDF vượt quá {MAX_PAGES} trang")
            rendered: list[str] = []
            pages: list[dict[str, Any]] = []
            for page_number, page in enumerate(pdf.pages, start=1):
                page_html, page_trace = _page_html(page, page_number, import_id)
                rendered.append(page_html)
                pages.append(page_trace)

            editable_pages = [page["page"] for page in pages if page["mode"] == "editable_text"]
            image_pages = [page["page"] for page in pages if page["mode"] == "image"]
            background_pages = [
                page["page"] for page in pages if page["background_images_skipped"] > 0
            ]
            failed_image_pages = [
                page["page"] for page in pages if page["image_render_failures"] > 0
            ]
            replacement_pages = [
                page["page"] for page in pages if page["replacement_characters"] > 0
            ]
            vector_pages = [page["page"] for page in pages if page["vector_elements"] > 0]

            issues: list[dict[str, Any]] = []
            if editable_pages:
                issues.append(_trace_issue(
                    "layout_reconstructed",
                    "info",
                    "Chữ đã được dựng lại để chỉnh sửa. Hãy kiểm tra ngắt dòng, cột, bảng và vị trí tuyệt đối so với PDF gốc.",
                    editable_pages,
                ))
            if image_pages:
                issues.append(_trace_issue(
                    "image_only_page",
                    "warning",
                    "Trang không có lớp chữ nên được giữ dưới dạng ảnh; nội dung trên trang này chưa thể sửa như văn bản.",
                    image_pages,
                ))
            if vector_pages:
                issues.append(_trace_issue(
                    "vector_layout",
                    "warning",
                    "Phát hiện đường kẻ hoặc đồ họa vector; bảng, khung và sơ đồ có thể cần căn chỉnh lại.",
                    vector_pages,
                ))
            if background_pages:
                issues.append(_trace_issue(
                    "background_omitted",
                    "warning",
                    "Ảnh nền toàn trang có lớp chữ phủ lên đã được bỏ để tránh lặp nội dung; hãy đối chiếu màu nền và bố cục trang gốc.",
                    background_pages,
                ))
            if failed_image_pages:
                issues.append(_trace_issue(
                    "image_render_failed",
                    "error",
                    "Có ảnh dùng định dạng màu hoặc mặt nạ PDF không đọc được và chưa được đưa vào tài liệu.",
                    failed_image_pages,
                ))
            if replacement_pages:
                issues.append(_trace_issue(
                    "character_mapping",
                    "error",
                    "Có ký tự không ánh xạ được từ font PDF; hãy kiểm tra lại tên riêng, số liệu và ký hiệu đặc biệt.",
                    replacement_pages,
                ))

            if not editable_pages:
                quality = "visual_only"
            elif image_pages or any(issue["severity"] == "error" for issue in issues):
                quality = "mixed"
            else:
                quality = "editable_with_review"

            return "".join(rendered), {
                "source_type": "pdf",
                "import_id": import_id,
                "quality": quality,
                "page_count": len(pages),
                "editable_page_count": len(editable_pages),
                "image_page_count": len(image_pages),
                "issues": issues,
                "pages": pages,
            }
    except PDFPasswordIncorrect as exc:
        raise ValueError("Tệp PDF có mật khẩu, vui lòng gỡ mật khẩu trước khi nhập") from exc
    except (PDFSyntaxError, PSEOF) as exc:
        raise ValueError("Tệp PDF không hợp lệ hoặc đã bị hỏng") from exc


def pdf_to_html(raw: bytes) -> str:
    """API tương thích cũ cho nơi chỉ cần HTML, không cần báo cáo trace."""
    content, _ = pdf_to_html_with_trace(raw, "pdf-import")
    return content
