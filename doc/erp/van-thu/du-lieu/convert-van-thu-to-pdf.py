# -*- coding: utf-8 -*-
"""Gộp 8 tệp Markdown của bộ tài liệu Quản lý văn thư thành MỘT tệp PDF.

Dùng lại y nguyên giao diện của `../convert_to_pdf.py` (bìa, màu DEGO, bảng, thanh
đầu trang, chân trang có số trang). Khác ở chỗ script cũ khóa cứng vào một tệp và
đòi tệp đó phải có sẵn khối `## MỤC LỤC` ngăn bằng `---`; bộ văn thư không có nên
phần đọc tệp được viết lại:

- mỗi tệp .md là MỘT CHƯƠNG, bắt đầu ở trang mới;
- tiêu đề H1 dòng đầu tệp trở thành tên chương, toàn bộ tiêu đề còn lại bị hạ một cấp
  (H1 -> H2, H2 -> H3...) để cả tập chỉ có một trật tự cấp bậc;
- mục lục sinh tự động: 8 chương + các mục cấp hai của từng chương. Mỗi tệp dùng cấp
  tiêu đề khác nhau (tệp 01 dùng H1 cho nhóm, các tệp khác dùng H2) nên "cấp hai" được
  lấy theo cấp NÔNG NHẤT có trong thân của chính chương đó;
- số trang trong mục lục dò bằng cách dựng nháp một lần rồi tìm chữ trong PDF. Nháp và
  bản cuối có cùng số dòng mục lục nên số trang không xê dịch giữa hai lần dựng.

Chạy: python convert_van_thu_to_pdf.py
"""

import os
import re
import unicodedata

import fitz
import markdown
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "quan-ly-van-thu-bo-tai-lieu.html")
PDF_FILE = os.path.join(BASE_DIR, "quan-ly-van-thu-bo-tai-lieu.pdf")
PREVIEW_DIR = os.path.join(BASE_DIR, "_preview_pdf")

# Thứ tự đọc theo README: README dẫn nhập -> 00..05 -> nhật ký thay đổi ở cuối.
FILES = [
    "README.md",
    "00-danh-gia-va-cau-hoi.md",
    "01-danh-sach-tinh-nang.md",
    "02-lo-trinh-phat-trien.md",
    "03-lark-approver.md",
    "04-bang-du-lieu.md",
    "05-vong-doi-phien-ban.md",
    "CHANGELOG.md",
]

# Chuỗi vô hình đặt ở đầu thân tài liệu để biết mục lục hết ở trang nào.
# Không dùng mốc "trang bìa + phê duyệt + mục lục = 3 trang" vì mục lục có thể tràn trang.
BODY_SENTINEL = "DEGOVANTHUBODYSTART"


# ---------------------------------------------------------------------------
# Đọc Markdown
# ---------------------------------------------------------------------------

def _demote_headings(md_text: str) -> str:
    """Hạ mọi tiêu đề xuống một cấp, BỎ QUA phần nằm trong khối mã.

    Không hạ thì tệp 01 (dùng H1 cho từng nhóm tính năng) sẽ có 16 tiêu đề ngang hàng
    với tên chương, đọc ra là 16 chương con giả.
    """
    out, in_fence = [], False
    for line in md_text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence:
            m = re.match(r"^(#{1,5})(\s+)(.*)$", line)
            if m:
                out.append("#" + m.group(1) + m.group(2) + m.group(3))
                continue
        out.append(line)
    return "\n".join(out)


_LIST_RE = re.compile(r"^\s*([-*+]|\d+\.)\s+")


def _loosen_lists(md_text: str) -> str:
    """Chèn dòng trống trước danh sách dính liền đoạn văn phía trên.

    Có 12 chỗ trong bộ tài liệu viết `Câu dẫn:` rồi xuống dòng gạch đầu dòng ngay.
    Với `sane_lists` thì markdown coi đó là văn xuôi chứ không phải danh sách, in ra
    thành mấy dòng có dấu gạch trần. Chèn dòng trống là xong, không đụng tệp gốc.
    """
    out, in_fence = [], False
    for line in md_text.split("\n"):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue
        if not in_fence and out and _LIST_RE.match(line):
            prev = out[-1].rstrip()
            if prev and not _LIST_RE.match(prev) and not prev.startswith(("|", "#", ">")):
                out.append("")
        out.append(line)
    return "\n".join(out)


def _strip_md(text: str) -> str:
    """Bỏ dấu định dạng khỏi tiêu đề để đem đi so với chữ đọc được từ PDF."""
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)   # [chữ](link) -> chữ
    text = re.sub(r"[*_`]", "", text)
    return text.strip()


def read_chapters():
    """Trả về danh sách chương: tên chương, HTML thân chương, các mục cấp hai."""
    chapters = []
    for idx, name in enumerate(FILES, start=1):
        path = os.path.join(BASE_DIR, name)
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()

        lines = raw.split("\n")
        title = name
        for i, line in enumerate(lines):
            if line.startswith("# "):
                title = _strip_md(line[2:])
                lines = lines[i + 1:]
                break
        body_md = _loosen_lists(_demote_headings("\n".join(lines)))

        # Cấp tiêu đề nông nhất trong thân -> đó là cấp đem lên mục lục.
        levels, in_fence = [], False
        for line in body_md.split("\n"):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = re.match(r"^(#{2,6})\s+(.*)$", line)
            if m:
                levels.append(len(m.group(1)))
        sub_level = min(levels) if levels else 0

        subs = []
        if sub_level:
            in_fence = False
            for line in body_md.split("\n"):
                if line.lstrip().startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence:
                    continue
                m = re.match(r"^(#{%d})\s+(.*)$" % sub_level, line)
                if m:
                    subs.append(_strip_md(m.group(2)))

        html = markdown.markdown(
            body_md,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists", "attr_list"],
        )
        html = _decorate(html)
        html = _add_anchors(html, idx, sub_level, subs)

        chapters.append({
            "index": idx,
            "file": name,
            "title": title,
            "subs": subs,
            "html": html,
        })
    return chapters


def _decorate(html: str) -> str:
    """Vài chỗ chỉnh cho hợp bản in — giữ đúng cách làm của script cũ."""
    html = re.sub(r"<th>#</th>", '<th class="col-center col-num">#</th>', html)
    html = re.sub(r"<td>(\d+)</td>", r'<td class="col-center col-num">\1</td>', html)
    html = html.replace("<hr />", '<div class="section-divider"></div>')
    return html


def _add_anchors(html: str, chap_idx: int, sub_level: int, subs: list) -> str:
    """Gắn id cho các tiêu đề cấp hai để mục lục trỏ tới được."""
    if not sub_level:
        return html
    tag = "h%d" % sub_level
    counter = {"n": 0}

    def repl(m):
        counter["n"] += 1
        return '<%s id="s-%d-%d">%s</%s>' % (tag, chap_idx, counter["n"], m.group(1), tag)

    return re.sub(r"<%s>(.*?)</%s>" % (tag, tag), repl, html, flags=re.S)


# ---------------------------------------------------------------------------
# Dựng HTML
# ---------------------------------------------------------------------------

CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,600&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

  @page { size: A4; margin: 22mm 22mm 20mm 22mm; }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: 'Plus Jakarta Sans', 'Segoe UI', -apple-system, Roboto, Helvetica, Arial, sans-serif;
    font-size: 9.6pt; line-height: 1.55; color: #222222; background: #ffffff;
    -webkit-print-color-adjust: exact; print-color-adjust: exact;
  }

  .page-break { page-break-after: always; break-after: page; height: 0; }

  /* Trang bìa */
  .cover-page {
    height: 235mm; display: flex; flex-direction: column; justify-content: space-between;
    page-break-after: always; break-after: page; padding-top: 8mm;
  }
  .cover-header-group { text-align: center; margin-bottom: 20px; }
  .cover-main-title {
    font-size: 21pt; font-weight: 800; color: #0E7DA8; letter-spacing: -0.3px;
    line-height: 1.25; text-transform: uppercase; margin-bottom: 6px;
  }
  .cover-sub-title {
    font-size: 17pt; font-weight: 800; color: #0E7DA8; line-height: 1.3;
    text-transform: uppercase; margin-bottom: 16px;
  }
  .cover-tagline { font-size: 10.5pt; color: #4B5563; font-weight: 500; margin-bottom: 25px; }
  .cover-meta-table { width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 9.25pt; }
  .cover-meta-table td { border: 1px solid #CCCCCC; padding: 7px 12px; vertical-align: middle; }
  .cover-meta-table tr td:first-child { width: 28%; background-color: #F2F2F2; font-weight: 700; color: #000000; }
  .cover-meta-table tr td:last-child { background-color: #FFFFFF; color: #222222; }
  .cover-footer-note {
    text-align: center; font-size: 8.75pt; color: #4B5563; line-height: 1.6;
    padding: 0 10mm; margin-top: auto; margin-bottom: 5mm;
  }

  .front-page { page-break-after: always; break-after: page; }

  /* Mục lục */
  .toc-row { display: flex; align-items: baseline; margin-bottom: 7px; font-size: 9.5pt; color: #0E7DA8; }
  .toc-row.toc-sub { margin-bottom: 4px; font-size: 8.9pt; padding-left: 16px; color: #3F6E85; }
  .toc-title-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 132mm; }
  .toc-row.toc-chapter { margin-top: 12px; }
  .toc-dots { flex-grow: 1; border-bottom: 1.5px dotted #0E7DA8; margin: 0 8px; height: 1px; opacity: 0.55; }
  .toc-row.toc-sub .toc-dots { border-bottom-style: dotted; opacity: 0.35; }
  .toc-page-num {
    font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 700; color: #0E7DA8;
    font-size: 9.5pt; min-width: 18px; text-align: right;
  }
  .toc-row.toc-sub .toc-page-num { font-weight: 500; font-size: 8.9pt; color: #3F6E85; }

  /* Tiêu đề */
  h1, h2, h3, h4, h5, h6 {
    font-family: 'Plus Jakarta Sans', sans-serif; color: #0E7DA8;
    page-break-after: avoid; break-after: avoid;
  }
  .chapter { page-break-before: always; break-before: page; }
  .chapter-title {
    font-size: 17pt; font-weight: 800; text-transform: uppercase; line-height: 1.25;
    padding-bottom: 9px; margin-bottom: 4px; border-bottom: 2.5px solid #0E7DA8;
  }
  .chapter-source { font-size: 8.4pt; color: #6B7280; font-weight: 500; margin-bottom: 18px; }
  h2 { font-size: 13.5pt; font-weight: 800; text-transform: uppercase; margin-top: 22px; margin-bottom: 10px; line-height: 1.3; }
  h3 { font-size: 10.75pt; font-weight: 700; margin-top: 16px; margin-bottom: 8px; line-height: 1.35; }
  h4 { font-size: 9.75pt; font-weight: 700; margin-top: 12px; margin-bottom: 6px; }
  h5, h6 { font-size: 9.3pt; font-weight: 700; margin-top: 10px; margin-bottom: 5px; }

  p { margin-bottom: 8.5px; text-align: justify; color: #222222; }
  strong { font-weight: 700; color: #000000; }
  em { font-style: italic; color: #4B5563; }
  a { color: #0E7DA8; text-decoration: none; }

  blockquote {
    border-left: 3px solid #0E7DA8; background-color: #F4F9FC; padding: 8px 13px;
    margin: 10px 0 13px 0; font-size: 9.1pt; color: #33505E;
    page-break-inside: avoid; break-inside: avoid;
  }
  blockquote p { margin-bottom: 4px; text-align: left; color: #33505E; }
  blockquote p:last-child { margin-bottom: 0; }

  ul, ol { margin-top: 4px; margin-bottom: 10px; padding-left: 20px; }
  li { margin-bottom: 3.5px; line-height: 1.5; }

  table {
    width: 100%; border-collapse: collapse; margin-top: 8px; margin-bottom: 14px;
    font-size: 8.5pt; page-break-inside: auto; break-inside: auto; table-layout: fixed;
  }
  tr { page-break-inside: avoid; break-inside: avoid; }
  thead { display: table-header-group; }
  th {
    background-color: #0E7DA8; color: #FFFFFF; font-weight: 700; text-align: left;
    padding: 6.5px 9px; border: 1px solid #0E7DA8; font-size: 8.3pt; letter-spacing: 0.15px;
  }
  td {
    padding: 5.5px 9px; border: 1px solid #CCCCCC; vertical-align: top;
    line-height: 1.45; background-color: #FFFFFF; word-wrap: break-word; overflow-wrap: anywhere;
  }
  tbody tr:nth-child(even) td { background-color: #F8FAFC; }
  .col-center { text-align: center; vertical-align: middle; }
  .col-num { width: 32px; font-weight: 600; color: #4B5563; }

  .brand-note-box {
    background-color: #F2F2F2; border: 1px solid #E0E0E0; border-radius: 4px;
    padding: 10px 14px; font-size: 8.75pt; color: #333333; line-height: 1.5;
    margin-top: 16px; margin-bottom: 16px; page-break-inside: avoid; break-inside: avoid;
  }

  code {
    font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 8pt;
    background-color: #F0F4F8; color: #0E7DA8; padding: 1px 4px; border-radius: 3px;
    border: 1px solid #D1D5DB; word-break: normal; overflow-wrap: anywhere;
  }
  pre {
    font-family: 'JetBrains Mono', 'Consolas', monospace; font-size: 7.6pt; line-height: 1.45;
    background-color: #F8FAFC; color: #1E293B; border: 1px solid #CCCCCC;
    padding: 10px 14px; border-radius: 4px; margin-top: 8px; margin-bottom: 12px;
    white-space: pre-wrap; page-break-inside: avoid; break-inside: avoid;
  }
  pre code { background: transparent; color: inherit; padding: 0; border: none; font-size: inherit; }

  .section-divider { height: 1px; background-color: #E5E7EB; margin: 18px 0 14px 0; page-break-after: avoid; }
  .doc-end-marker {
    text-align: center; font-size: 8.75pt; font-weight: 700; letter-spacing: 2px;
    color: #0E7DA8; margin-top: 24px; padding-top: 12px; border-top: 1px solid #E5E7EB;
    page-break-inside: avoid;
  }
  /* Mốc vô hình để dò trang bắt đầu phần thân — không hiện trên bản in. */
  .sentinel { color: #FFFFFF; font-size: 1pt; }
"""


def build_html(chapters, page_map=None):
    toc_rows = ""
    for ch in chapters:
        num = page_map.get("ch-%d" % ch["index"], "") if page_map else ""
        toc_rows += (
            '<div class="toc-row toc-chapter"><span class="toc-title-text">'
            '<strong>%d. %s</strong></span><span class="toc-dots"></span>'
            '<span class="toc-page-num">%s</span></div>'
            % (ch["index"], ch["title"].upper(), num)
        )
        for j, sub in enumerate(ch["subs"], start=1):
            snum = page_map.get("s-%d-%d" % (ch["index"], j), "") if page_map else ""
            toc_rows += (
                '<div class="toc-row toc-sub"><span class="toc-title-text">%s</span>'
                '<span class="toc-dots"></span>'
                '<span class="toc-page-num">%s</span></div>' % (sub, snum)
            )

    body = ""
    for i, ch in enumerate(chapters):
        sentinel = '<span class="sentinel">%s</span>' % BODY_SENTINEL if i == 0 else ""
        body += (
            '<div class="chapter">%s<h1 class="chapter-title" id="ch-%d">%d. %s</h1>'
            '<div class="chapter-source">Nguồn: ke-hoach/erp/van-thu/%s</div>%s</div>'
            % (sentinel, ch["index"], ch["index"], ch["title"], ch["file"], ch["html"])
        )

    return """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>QUẢN LÝ VĂN THƯ — BỘ TÀI LIỆU</title>
<style>%s</style>
</head>
<body>

<div class="cover-page">
  <div class="cover-header-group">
    <div class="cover-main-title">Bộ tài liệu thiết kế</div>
    <div class="cover-sub-title">Phân hệ Quản lý Văn thư</div>
    <div class="cover-tagline">Xây trên nền mã nguồn Thu mua đang chạy — dùng lại tài khoản, nhân sự, phòng ban, pháp nhân, phân quyền, thông báo và kho tệp</div>
  </div>

  <table class="cover-meta-table">
    <tr><td>Tên bộ tài liệu</td><td><strong>Quản lý văn thư — bộ tài liệu thiết kế</strong></td></tr>
    <tr><td>Nguồn</td><td><code>ke-hoach/erp/van-thu/</code> — 8 tệp Markdown gộp thành một bản in</td></tr>
    <tr><td>Ngày sửa gần nhất</td><td>13/08/2026</td></tr>
    <tr><td>Đơn vị soạn thảo</td><td>Đội Công nghệ thông tin DEGO Holding</td></tr>
    <tr><td>Loại tài liệu</td><td>Bản đề xuất thiết kế phân hệ</td></tr>
    <tr><td>Phạm vi</td><td>174 tính năng · 10 phase · 25 bảng dữ liệu mới + 4 bảng sửa</td></tr>
    <tr><td>Trạng thái</td><td><strong>Bản đề xuất — chưa được duyệt</strong></td></tr>
    <tr><td>Việc đang chặn</td><td>17 câu hỏi ở chương <code>00</code> mục 8 và 4 câu ở chương <code>05</code> mục 9</td></tr>
  </table>

  <div class="cover-footer-note">
    Bản in này gộp nguyên văn tám tệp trong thư mục <code>ke-hoach/erp/van-thu/</code>. Bản gốc để đọc và sửa vẫn là các tệp Markdown; khi nội dung đổi thì phải dựng lại tệp PDF này, không sửa trực tiếp lên PDF.
  </div>
</div>

<div class="front-page">
  <h2>Bộ tài liệu gồm những gì</h2>
  <table>
    <thead><tr>
      <th style="width: 8%%;">Chương</th><th style="width: 32%%;">Tên</th>
      <th style="width: 28%%;">Tệp gốc</th><th style="width: 32%%;">Đọc khi nào</th>
    </tr></thead>
    <tbody>%s</tbody>
  </table>

  <div class="brand-note-box">
    <strong>Ghi chú về nhận diện thương hiệu:</strong> tài liệu dùng hai màu nhận diện của DEGO Holding là xanh lơ (màu chủ đạo <code>#0E7DA8</code>) và xanh lá (màu nhấn <code>#3A9E4E</code>).
  </div>
</div>

<div class="front-page">
  <h2>Mục lục</h2>
  <div style="margin-top: 14px;">%s</div>
</div>

<div class="doc-body">%s</div>

<div class="doc-end-marker">— HẾT BỘ TÀI LIỆU —</div>

</body>
</html>
""" % (CSS, _files_table(chapters), toc_rows, body)


WHEN_TO_READ = {
    "README.md": "Đọc đầu tiên — dẫn nhập và năm điều quan trọng nhất",
    "00-danh-gia-va-cau-hoi.md": "Đọc thứ hai — đánh giá cách làm và 17 câu hỏi cần chốt",
    "01-danh-sach-tinh-nang.md": "Khi cần biết phạm vi công việc",
    "02-lo-trinh-phat-trien.md": "Khi cần biết làm gì trước làm gì sau",
    "03-lark-approver.md": "Trước khi thiết kế bộ máy phê duyệt (phase 3)",
    "04-bang-du-lieu.md": "Khi bắt đầu viết mã",
    "05-vong-doi-phien-ban.md": "Cùng lúc với chương 04 — chỗ dễ làm sai nhất",
    "CHANGELOG.md": "Khi quay lại sau một thời gian, hoặc khi thấy nội dung khác lần đọc trước",
}


def _files_table(chapters):
    rows = ""
    for ch in chapters:
        rows += (
            '<tr><td class="col-center col-num">%d</td><td><strong>%s</strong></td>'
            '<td><code>%s</code></td><td>%s</td></tr>'
            % (ch["index"], ch["title"], ch["file"], WHEN_TO_READ.get(ch["file"], ""))
        )
    return rows


# ---------------------------------------------------------------------------
# Dò số trang
# ---------------------------------------------------------------------------

def _norm(text: str) -> str:
    """Bỏ hết khoảng trắng, dấu câu, ký hiệu — chỉ giữ chữ và số, viết hoa.

    Chữ đọc từ PDF bị ngắt dòng và mất khoảng trắng lung tung; so kiểu này thì
    tiêu đề dài mấy cũng khớp. `text-transform: uppercase` của CSS cũng được xử lý luôn.
    """
    text = unicodedata.normalize("NFC", text).upper()
    return "".join(c for c in text if c.isalnum())


def discover_pages(pdf_path, chapters):
    doc = fitz.open(pdf_path)
    pages = [_norm(p.get_text()) for p in doc]
    doc.close()

    start = 0
    for i, t in enumerate(pages):
        if BODY_SENTINEL in t:
            start = i
            break

    page_map, cursor, missed = {}, start, []
    entries = []
    for ch in chapters:
        entries.append(("ch-%d" % ch["index"], ch["title"]))
        for j, sub in enumerate(ch["subs"], start=1):
            entries.append(("s-%d-%d" % (ch["index"], j), sub))

    for key, title in entries:
        needle = _norm(title)[:45]
        if not needle:
            continue
        for i in range(cursor, len(pages)):
            if needle in pages[i]:
                page_map[key] = i + 1
                cursor = i
                break
        else:
            missed.append(title)

    return page_map, missed, start


# ---------------------------------------------------------------------------
# Đóng dấu đầu trang / chân trang
# ---------------------------------------------------------------------------

def stamp(pdf_path):
    doc = fitz.open(pdf_path)
    blue = (0.0549, 0.4902, 0.6588)    # #0E7DA8
    green = (0.2275, 0.6196, 0.3059)   # #3A9E4E
    gray_line = (0.82, 0.82, 0.82)
    gray_text = (0.40, 0.40, 0.40)
    white = (1.0, 1.0, 1.0)

    left_x = 62.36  # 22mm
    font_reg = "C:/Windows/Fonts/segoeui.ttf"
    font_bold = "C:/Windows/Fonts/segoeuib.ttf"
    f = fitz.Font(fontfile=font_reg)

    for idx, page in enumerate(doc):
        width, height = page.rect.width, page.rect.height
        n = idx + 1
        page.insert_font(fontname="segoe", fontfile=font_reg)
        page.insert_font(fontname="segoe-bold", fontfile=font_bold)

        page.draw_rect(fitz.Rect(0, 0, width, 39.69), color=None, fill=blue)
        page.insert_text(fitz.Point(left_x, 24.5), "DEGO HOLDING",
                         fontname="segoe-bold", fontsize=11.5, color=white)

        right = ("Tài liệu nội bộ — Lưu hành hạn chế" if n == 1
                 else "Quản lý văn thư — bộ tài liệu thiết kế")
        page.insert_text(fitz.Point(width - left_x - f.text_length(right, fontsize=9), 24.5),
                         right, fontname="segoe", fontsize=9, color=white)

        if n == 1:
            page.draw_rect(fitz.Rect(0, height - 21.5, width, height - 17.0), color=None, fill=green)
            page.draw_rect(fitz.Rect(0, height - 17.0, width, height), color=None, fill=blue)
        else:
            page.draw_line(fitz.Point(left_x, height - 40), fitz.Point(width - left_x, height - 40),
                           color=gray_line, width=0.75)
            left_txt = "Phân hệ Quản lý Văn thư — bản đề xuất thiết kế"
            page.insert_text(fitz.Point(left_x, height - 26), left_txt,
                             fontname="segoe", fontsize=8.5, color=gray_text)
            right_txt = "Trang %d/%d" % (n, len(doc))
            page.insert_text(
                fitz.Point(width - left_x - f.text_length(right_txt, fontsize=8.5), height - 26),
                right_txt, fontname="segoe", fontsize=8.5, color=gray_text)

    doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()


# ---------------------------------------------------------------------------

def render(html_path, pdf_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page()
        page.goto("file:///" + html_path.replace(os.sep, "/"), wait_until="networkidle")
        page.pdf(path=pdf_path, format="A4", print_background=True, display_header_footer=False)
        browser.close()


def run():
    chapters = read_chapters()
    total_subs = sum(len(c["subs"]) for c in chapters)
    print("Doc %d chuong, %d muc cap hai." % (len(chapters), total_subs))
    for c in chapters:
        print("   %d. %-46s %2d muc  (%s)" % (c["index"], c["title"][:46], len(c["subs"]), c["file"]))

    print("Buoc 1: dung ban nhap de do so trang...")
    html_path_write(build_html(chapters))
    render(HTML_FILE, PDF_FILE)

    page_map, missed, body_start = discover_pages(PDF_FILE, chapters)
    print("   Than tai lieu bat dau o trang %d; do duoc %d/%d muc."
          % (body_start + 1, len(page_map), len(chapters) + total_subs))
    if missed:
        print("   KHONG do duoc so trang cho %d muc: %s" % (len(missed), "; ".join(missed[:6])))

    print("Buoc 2: dung ban cuoi kem so trang trong muc luc...")
    html_path_write(build_html(chapters, page_map))
    render(HTML_FILE, PDF_FILE)

    print("Buoc 3: dong dau thanh dau trang va chan trang...")
    stamp(PDF_FILE)

    doc = fitz.open(PDF_FILE)
    total = len(doc)
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    for p in sorted({0, 1, 2, 3, body_start, body_start + 1, total - 1}):
        if 0 <= p < total:
            doc[p].get_pixmap(dpi=110).save(os.path.join(PREVIEW_DIR, "trang_%03d.png" % (p + 1)))
    doc.close()

    size_mb = os.path.getsize(PDF_FILE) / 1024 / 1024
    print("Xong. %d trang, %.2f MB -> %s" % (total, size_mb, PDF_FILE))


def html_path_write(html: str) -> str:
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    return HTML_FILE


if __name__ == "__main__":
    run()
