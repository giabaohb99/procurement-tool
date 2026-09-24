# -*- coding: utf-8 -*-
"""Xuất «Hướng dẫn sử dụng — Quản lý Văn bản» ra HTML + PDF theo mẫu tài liệu nội bộ DEGO.

Mẫu trình bày lấy theo các văn bản nội bộ đang soạn trên chính hệ thống (ví dụ «Kế hoạch
thực hiện công việc DX Team»): phần đầu là bảng logo | tên đơn vị, tiêu đề in hoa xanh navy,
bảng thông tin tài liệu, thanh đầu phần hai màu xanh lá | xanh ngọc, khung ghi chú nền vàng.

Chạy:  ~/.claude/skills/.venv/bin/python3 xuat-tai-lieu.py            # xuất mọi tài liệu
       ~/.claude/skills/.venv/bin/python3 xuat-tai-lieu.py nhanh      # chỉ một tài liệu (nhanh | hdsd | nghiep-vu)
Mỗi tài liệu ra một tệp .html (mở bằng trình duyệt) và .pdf (in bằng Chrome chạy ngầm).
"""

import os
import re
import subprocess
import sys
import unicodedata

import markdown

BASE = os.path.dirname(os.path.abspath(__file__))
# Mỗi tài liệu: tên tệp gốc (không đuôi), dòng loại ở phần đầu, tiêu đề hai dòng, dòng phụ.
DOCS = {
    "nhanh": ("gioi-thieu-nhanh-van-ban", "GIỚI THIỆU NHANH",
              "Giới thiệu nhanh<br>phân hệ Quản lý văn bản",
              "Đọc trong 5 phút · Luồng văn bản · Năm việc hay làm · Điều cần nhớ"),
    "hdsd": ("huong-dan-su-dung-van-ban", "HƯỚNG DẪN SỬ DỤNG",
             "Hướng dẫn sử dụng<br>phân hệ Quản lý văn bản",
             "Soạn thảo · Phê duyệt · Ban hành · Phân phối cho công ty con · Phân quyền"),
    "nghiep-vu": ("mo-ta-luong-nghiep-vu-van-ban", "MÔ TẢ LUỒNG NGHIỆP VỤ",
                  "Mô tả luồng nghiệp vụ<br>phân hệ Quản lý văn bản",
                  "Vòng đời văn bản · 9 quy trình · Quy tắc nghiệp vụ · Thiết lập · Phân quyền"),
}
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

ORG = "DEGO HOLDING · PHÒNG CNTT — DX TEAM"
# Bề rộng ảnh trong tệp .md tính theo khung xem 760px — quy ra % bề rộng trang giấy.
MD_IMAGE_FRAME = 760

CSS = """
@page { size: A4; margin: 18mm 17mm 18mm 22mm;
  @top-center { content: counter(page); font: 11pt "Times New Roman", serif; color: #1A4D6B; } }
@page :first { @top-center { content: none; } }
* { box-sizing: border-box; }
body { font: 12pt/1.5 "Times New Roman", serif; color: #111827; margin: 0; }
a { color: #1E7F9C; text-decoration: none; }
b, strong { color: #1A4D6B; }
code { font: 10.5pt "Courier New", monospace; background: #F1F7FA; padding: 0 3px; border-radius: 3px; }
table { width: 100%; border-collapse: collapse; margin: 8px 0 14px; font-size: 11pt; }
th { background: #1E7F9C; color: #fff; font-weight: bold; text-align: left; padding: 6px 8px; border: 1px solid #1E7F9C; }
td { padding: 5px 8px; border: 1px solid #CBD5DD; vertical-align: top; }
tbody tr:nth-child(even) td { background: #F8FBFC; }
tr, img { break-inside: avoid; }
ul, ol { margin: 4px 0 8px; padding-left: 22px; }
li { margin: 2px 0; }
p { margin: 5px 0 8px; text-align: justify; }

/* Phần đầu tài liệu */
.doc-head { width: 100%; border-collapse: collapse; margin: 0; }
.doc-head td { border: 1px solid #9CA3AF; border-bottom: 2px solid #1E7F9C; padding: 8px 10px; background: #fff; }
.doc-head img { width: 150px; }
.doc-head .org { text-align: right; color: #1A4D6B; font-weight: bold; font-size: 13pt; }
.doc-head .kind { text-align: right; color: #6B7C8A; font-style: italic; font-size: 9pt; }
.doc-head .meta { text-align: right; color: #1A4D6B; font-size: 8.5pt; }
.doc-title { text-align: center; color: #1A4D6B; font-weight: bold; font-size: 20pt; line-height: 1.2; margin: 18px 0 4px; text-transform: uppercase; }
.doc-sub { text-align: center; color: #6B7C8A; font-style: italic; margin: 0 0 14px; }
.info td.label { background: #F1F7FA; border-left: 2px solid #1E7F9C; color: #1E7F9C; font-weight: bold; width: 22%; }
.info tbody tr:nth-child(even) td { background: none; }
.info tbody tr:nth-child(even) td.label { background: #F1F7FA; }

/* Thanh đầu phần: khối xanh lá | tên phần trên nền xanh ngọc */
.sec { display: flex; margin: 22px 0 12px; border: 1px solid #9CA3AF; break-after: avoid; }
.sec .g { background: #6DBF3C; width: 50%; }
.sec .t { background: #1E7F9C; color: #fff; width: 50%; padding: 7px 10px; font-weight: bold; font-size: 13pt; text-transform: uppercase; }
.page-break { break-before: page; }
/* Đầu mục con */
h3 { background: #FAFCFD; border: 1px solid #CBD5DD; border-left: 3px solid #27ACE3; color: #1A4D6B;
     font-size: 13pt; padding: 6px 10px; margin: 18px 0 8px; break-after: avoid; }
h4 { color: #1E7F9C; font-size: 12pt; margin: 12px 0 6px; break-after: avoid; }
/* Khung ghi chú */
blockquote { background: #FFF6E0; border: 1px solid #E8D6A8; border-left: 3px solid #E8A317; margin: 10px 0; padding: 6px 12px; }
blockquote p { margin: 4px 0; }
/* Hình + chú thích đi liền, không tách trang */
.figure { break-inside: avoid; text-align: center; margin: 10px 0 4px; }
.figure img { max-width: 100%; border: 1px solid #CBD5DD; }
.caption { text-align: center; color: #6B7C8A; font-size: 10.5pt; margin: 2px 0 8px; break-after: avoid; }
hr { display: none; }
/* Mục lục: tên phần in đậm, các mục thụt vào bên dưới */
.toc p { margin: 10px 0 2px; }
.toc ol { margin: 0 0 4px; padding-left: 30px; }
.toc li { margin: 1px 0; }
"""


def slugify(text: str, sep: str = "-") -> str:
    """Khớp cách GitHub đặt neo cho tiêu đề — mục lục trong tệp .md viết theo kiểu đó."""
    text = unicodedata.normalize("NFC", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", sep)


def split_header(md: str):
    """Tách khối đầu tệp (tiêu đề + bảng thông tin + «Cách đọc») khỏi thân tài liệu."""
    head, _, body = md.partition("\n---\n")
    info = dict(re.findall(r"^\| \*\*(.+?)\*\* \| (.+?) \|$", head, flags=re.M))
    guide = head.split("**Cách đọc tài liệu này**", 1)[1] if "**Cách đọc tài liệu này**" in head else ""
    return info, guide.strip(), body


def md_to_html(text: str) -> str:
    return markdown.markdown(
        text, extensions=["tables", "toc", "sane_lists"],
        extension_configs={"toc": {"slugify": slugify}},
    )


def dress_body(html: str) -> str:
    # Tiêu đề cấp 2 («PHẦN …», «MỤC LỤC») → thanh đầu phần; mỗi PHẦN sang trang mới.
    def sec(m):
        brk = " page-break" if m.group(2).startswith("PHẦN") else ""
        return f'<div class="sec{brk}" id="{m.group(1)}"><div class="g"></div><div class="t">{m.group(2)}</div></div>'
    html = re.sub(r'<h2 id="([^"]*)">(.*?)</h2>', sec, html)
    # Bảng hai cột tiêu đề rỗng («| | |») là bảng thông tin: bỏ hàng tiêu đề trống, cột đầu là nhãn.
    html = re.sub(r'<table>\s*<thead>\s*<tr>\s*<th></th>\s*<th></th>\s*</tr>\s*</thead>(.*?)</table>',
                  lambda m: '<table class="info">' + re.sub(r'<tr>\s*<td>', '<tr><td class="label">', m.group(1)) + '</table>',
                  html, flags=re.S)
    # Khối mục lục = từ thanh «MỤC LỤC» tới thanh PHẦN đầu tiên — bọc lại để định kiểu riêng.
    html = re.sub(r'(<div class="sec"[^>]*><div class="g"></div><div class="t">MỤC LỤC</div></div>)(.*?)(?=<div class="sec page-break")',
                  r'\1<div class="toc">\2</div>', html, count=1, flags=re.S)
    # Ảnh: bề rộng theo khung 760px → % bề rộng trang; bọc chung với chú thích ngay sau.
    def img(m):
        pct = min(100, round(int(m.group(2)) / MD_IMAGE_FRAME * 100))
        return f'<img src="{m.group(1)}" style="width:{pct}%"'
    html = re.sub(r'<img src="([^"]+)" width="(\d+)"', img, html)
    html = re.sub(
        r'<p align="center">(<img[^>]+>)</p>\s*<p><em>(Hình[^<]*)</em></p>',
        r'<div class="figure">\1<p class="caption"><em>\2</em></p></div>', html)
    return html


def build_head(info: dict, guide_html: str, kind: str, title: str, subtitle: str) -> str:
    rows = "".join(
        f'<tr><td class="label">{k}</td><td>{md_to_html(v)[3:-4]}</td></tr>' for k, v in info.items())
    return f"""
<table class="doc-head"><tr>
  <td style="width:50%"><img src="hinh/logo-dego.svg" alt="DEGO HOLDING"></td>
  <td><div class="org">{ORG}</div><div class="kind">{kind}</div>
      <div class="meta">Cập nhật {info.get('Cập nhật', '')}</div><div class="meta">Phân hệ Văn bản — ERP DEGO</div></td>
</tr></table>
<div class="doc-title">{title}</div>
<div class="doc-sub">{subtitle}</div>
<table class="info"><tbody>{rows}</tbody></table>
<blockquote><p><b>CÁCH ĐỌC TÀI LIỆU NÀY</b></p>{guide_html}</blockquote>
"""


def export(key: str):
    name, kind, title, subtitle = DOCS[key]
    src, html_out, pdf_out = (os.path.join(BASE, name + ext) for ext in (".md", ".html", ".pdf"))
    with open(src, encoding="utf-8") as f:
        info, guide, body = split_header(f.read())
    html = build_head(info, md_to_html(guide), kind, title, subtitle) + dress_body(md_to_html(body))
    page = (f'<!doctype html><html lang="vi"><head><meta charset="utf-8">'
            f'<title>{title.replace("<br>", " ")}</title><style>{CSS}</style></head>'
            f'<body>{html}</body></html>')
    with open(html_out, "w", encoding="utf-8") as f:
        f.write(page)
    print("HTML:", html_out)
    try:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf_out}", "file://" + html_out],
                       check=True, capture_output=True, timeout=180)
        print("PDF: ", pdf_out)
    except (OSError, subprocess.SubprocessError) as err:
        print("Không in được PDF (mở tệp HTML rồi In → Lưu PDF):", err)


def main():
    for key in (sys.argv[1:] or DOCS):
        export(key)


if __name__ == "__main__":
    main()
