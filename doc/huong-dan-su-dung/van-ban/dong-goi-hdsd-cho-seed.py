# -*- coding: utf-8 -*-
"""Đóng gói tài liệu HDSD Văn bản thành gói seed cho phân hệ «Hướng dẫn sử dụng».

Thư mục doc/ KHÔNG có trong container api trên prod, nên nội dung được dựng sẵn ở máy
mình rồi ghi vào backend/scripts/help_van_ban/ (thư mục này commit cùng code):
  bai-viet.json   — cây bài: bài gốc + một bài con cho mỗi PHẦN của huong-dan-su-dung-van-ban.md
  hinh/*.webp     — đúng những ảnh các bài dùng, đổi sang WebP cho gói nhẹ (cần `cwebp`)

Ảnh trong HTML viết dạng src="__HINH__/<tên tệp>"; seed trên server tải ảnh lên kho rồi thay
bằng URL thật (backend/scripts/seed_help_van_ban.py).

Chạy mỗi khi sửa tệp .md, rồi commit thư mục gói:
  ~/.claude/skills/.venv/bin/python3 doc/huong-dan-su-dung/van-ban/dong-goi-hdsd-cho-seed.py
"""

import json
import os
import re
import shutil
import subprocess
import unicodedata

import markdown

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(BASE, "..", "..", "..", "backend", "scripts", "help_van_ban"))
IMG_PLACEHOLDER = "__HINH__"

ROOT_TITLE = "Hướng dẫn sử dụng Văn bản"
ROOT_SUMMARY = "Soạn, trình duyệt, ban hành văn bản nội bộ; phân phối cho công ty con; sổ, số hiệu và phân quyền"
ROOT_ICON = "book-open"

# Tiêu đề PHẦN trong tệp .md → (tiêu đề bài con, mô tả ngắn, icon). Tiêu đề phải duy nhất
# trên toàn cây vì đường dẫn bài sinh từ tiêu đề.
PARTS = {
    "PHẦN I. LÀM QUEN": ("Làm quen với phân hệ Văn bản",
                         "Bố cục màn hình, thanh menu, trang Tổng quan và các bước một văn bản đi qua", "rocket"),
    "PHẦN II. DÀNH CHO NGƯỜI SOẠN VĂN BẢN": ("Soạn và gửi duyệt văn bản",
                                             "Tìm văn bản, tạo mới ba bước, soạn nội dung, gửi duyệt, xử lý khi bị trả lại", "file-text"),
    "PHẦN III. DÀNH CHO NGƯỜI DUYỆT": ("Duyệt văn bản",
                                      "Tìm việc chờ duyệt, duyệt nhiều bước và một bước, trả lại, từ chối", "workflow"),
    "PHẦN IV. BAN HÀNH VÀ SAU BAN HÀNH": ("Ban hành và quản lý văn bản sau ban hành",
                                          "Ban hành, phân phối cho công ty con, sửa đổi, liên kết, bãi bỏ, bản trích, chữ ký", "clipboard-list"),
    "PHẦN V. DÀNH CHO VĂN THƯ VÀ NGƯỜI THIẾT LẬP": ("Văn bản — Sổ, số hiệu và thiết lập",
                                                   "Sổ văn bản, loại văn bản, văn bản mẫu, mức mật, quy tắc đánh số và quy tắc liên kết", "settings"),
    "PHẦN VI. PHÂN QUYỀN": ("Văn bản — Phân quyền",
                            "Ba lớp quyền, cấp quyền cho vai trò, giao vai trò và phạm vi cho từng người", "shield-check"),
    "PHẦN VII. HỎI ĐÁP": ("Văn bản — Câu hỏi thường gặp",
                          "Những thắc mắc hay gặp khi soạn, duyệt và quản lý văn bản", "help"),
}


# ---------------------------------------------------------------- ảnh
_images: set[str] = set()


def image_ref(rel: str) -> str:
    """Ghi nhận ảnh cần đóng gói, trả chỗ giữ để seed thay bằng URL thật."""
    name = os.path.basename(rel)
    _images.add(name)
    return f"{IMG_PLACEHOLDER}/{os.path.splitext(name)[0]}.webp"


# ---------------------------------------------------------------- slug như help-center
def slugify(text: str) -> str:
    """Bản Python của `slugify` ở help-center/src/lib/help-slug.tsx — phải cho ra đúng chuỗi đó."""
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = re.sub(r"[̀-ͯ]", "", text).lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def md_anchor(text: str) -> str:
    """Neo mà mục lục trong tệp .md dùng (kiểu GitHub)."""
    text = unicodedata.normalize("NFC", text).strip().lower()
    return re.sub(r"[^\w\- ]", "", text).replace(" ", "-")


# ---------------------------------------------------------------- dựng nội dung
def md_to_html(text: str) -> str:
    # `toc` gắn id cho đề mục đúng như neo trong tệp .md → liên kết cùng bài nhảy thẳng tới mục.
    # Trang đọc giữ nguyên id có sẵn trên đề mục (help-center/src/hooks/use-heading-toc.ts).
    return markdown.markdown(text, extensions=["tables", "sane_lists", "toc"],
                             extension_configs={"toc": {"slugify": lambda v, _sep: md_anchor(v)}})


def split_parts(md: str) -> list[tuple[str, str]]:
    """Cắt thân tài liệu theo tiêu đề «## PHẦN …» → [(tên phần, markdown của phần)]."""
    body = md.split("\n## PHẦN I.", 1)[1]
    body = "## PHẦN I." + body
    chunks = re.split(r"^## (PHẦN [^\n]+)\n", body, flags=re.M)
    return [(chunks[i].strip(), chunks[i + 1]) for i in range(1, len(chunks), 2)]


def build_anchor_map(parts) -> dict[str, str]:
    """Neo trong tệp .md (#18-liên-kết…, #phần-vi-…) → đường dẫn bài con chứa nó."""
    amap = {}
    for name, text in parts:
        slug = "/" + slugify(PARTS[name][0])
        amap[md_anchor(name)] = slug
        for h in re.findall(r"^#{3,4} (.+)$", text, flags=re.M):
            amap[md_anchor(h)] = slug
    return amap


def dress(html: str, amap: dict[str, str], shift_headings: bool = True, here: str = "") -> str:
    # Đề mục của bài con: mục (h3) thành h2, mục nhỏ (h4) thành h3 — mục lục bài đọc h2/h3.
    if shift_headings:
        html = re.sub(r"<h3( [^>]*)?>", r"<h2\1>", html).replace("</h3>", "</h2>")
        html = re.sub(r"<h4( [^>]*)?>", r"<h3\1>", html).replace("</h4>", "</h3>")
    # Hình: tải ảnh lên, bỏ số thứ tự hình (đã tách bài nên số liên tục không còn nghĩa).
    def fig(m):
        url = image_ref(m.group(1))
        return f'<p style="text-align:center"><img src="{url}" alt="{m.group(2)}" style="max-width:100%"></p>'
    html = re.sub(r'<p align="center"><img src="([^"]+)" width="\d+" alt="([^"]*)"></p>', fig, html)
    html = re.sub(r"<p><em>Hình \d+\. ([^<]*)</em></p>", r'<p style="text-align:center"><em>\1</em></p>', html)
    html = re.sub(r"\[Hình \d+\]", "hình", html)
    # Liên kết nội bộ «#neo» → bài con tương ứng.
    def link(m):
        target = amap.get(m.group(1))
        if not target:
            return m.group(2)
        if target == here:
            target = "#" + m.group(1)
        return (f'<a href="{target}" style="color:var(--primary,#2563eb);font-weight:600;'
                f'text-decoration:underline">{m.group(2)}</a>')
    html = re.sub(r'<a href="#([^"]+)">(.*?)</a>', link, html)
    return html


def root_content(amap_children: list[tuple[str, str, str]]) -> str:
    """Bài gốc = «Giới thiệu nhanh» (bỏ phần đầu và mục «Đọc thêm») + danh sách bài con."""
    with open(os.path.join(BASE, "gioi-thieu-nhanh-van-ban.md"), encoding="utf-8") as f:
        md = f.read().split("\n---\n", 1)[1]
    md = md.split("\n## 6. Đọc thêm ở đâu", 1)[0]
    md = re.sub(r"^## \d+\. ", "## ", md, flags=re.M)
    html = dress(md_to_html(md), {}, shift_headings=False)
    items = "".join(
        f'<li><a href="{path}" style="color:var(--primary,#2563eb);font-weight:600;text-decoration:underline">'
        f"{title}</a> — {summary}</li>" for title, summary, path in amap_children)
    return html + f"<h2>Các bài hướng dẫn chi tiết</h2><ol>{items}</ol>"


# ---------------------------------------------------------------- ghi gói
def main():
    with open(os.path.join(BASE, "huong-dan-su-dung-van-ban.md"), encoding="utf-8") as f:
        parts = split_parts(f.read())
    amap = build_anchor_map(parts)

    children, listing = [], []
    for name, text in parts:
        title, summary, icon = PARTS[name]
        content = dress(md_to_html(text), amap, here="/" + slugify(title))
        children.append({"title": title, "summary": summary, "icon": icon, "content": content})
        listing.append((title, summary, "/" + slugify(title)))

    tree = {"title": ROOT_TITLE, "summary": ROOT_SUMMARY, "icon": ROOT_ICON,
            "content": root_content(listing), "children": children}

    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(os.path.join(OUT, "hinh"))
    for name in sorted(_images):
        dst = os.path.join(OUT, "hinh", os.path.splitext(name)[0] + ".webp")
        subprocess.run(["cwebp", "-quiet", "-q", "85", os.path.join(BASE, "hinh", name), "-o", dst], check=True)
    with open(os.path.join(OUT, "bai-viet.json"), "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=1)
    print(f"Đã đóng gói vào {OUT}: 1 bài gốc, {len(children)} bài con, {len(_images)} ảnh.")


if __name__ == "__main__":
    main()
