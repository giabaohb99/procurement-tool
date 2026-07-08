# -*- coding: utf-8 -*-
"""Render sơ đồ Mermaid trong so-do-ky-thuat.md -> PNG từng cái + PDF cả tài liệu.
Chạy: python doc/export/build_diagrams.py  (từ thư mục procurement-tool)
"""
import re, os, sys, pathlib
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent          # doc/export
MD = HERE.parent / "so-do-ky-thuat.md"
OUT_HTML = HERE / "diagrams.html"
OUT_PDF = HERE / "so-do-ky-thuat.pdf"

md = MD.read_text(encoding="utf-8")

# Trích (tiêu đề ##, caption *...*, code mermaid) theo thứ tự
blocks = []
lines = md.splitlines()
title, cap = "", ""
i = 0
while i < len(lines):
    ln = lines[i]
    if ln.startswith("## "):
        title = re.sub(r"[*⭐]", "", ln[3:]).strip()
        cap = ""
    elif ln.strip().startswith("*") and ln.strip().endswith("*") and len(ln.strip()) > 2:
        cap = ln.strip().strip("*").strip()
    elif ln.strip() == "```mermaid":
        code = []
        i += 1
        while i < len(lines) and lines[i].strip() != "```":
            code.append(lines[i]); i += 1
        blocks.append((title, cap, "\n".join(code)))
    i += 1

print(f"Tìm thấy {len(blocks)} sơ đồ")

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

cards = []
for idx, (t, c, code) in enumerate(blocks, 1):
    cards.append(f'''<section class="diagram">
  <div class="dnum">Sơ đồ {idx}</div>
  <h2>{esc(t)}</h2>
  {f'<p class="cap">{esc(c)}</p>' if c else ''}
  <pre class="mermaid">{esc(code)}</pre>
</section>''')

html = f'''<!doctype html><html lang="vi"><head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family: "Segoe UI", Arial, sans-serif; color:#1a2332; margin:0; padding:0; }}
  .page {{ max-width: 900px; margin: 0 auto; padding: 36px 40px; }}
  .cover {{ border-bottom: 3px solid #0b6bcb; padding-bottom: 18px; margin-bottom: 28px; }}
  .cover .brand {{ color:#0b6bcb; font-weight:700; letter-spacing:.5px; font-size:13px; }}
  .cover h1 {{ font-size: 24px; margin: 8px 0 6px; color:#0b2a4a; }}
  .cover .sub {{ color:#5b6b82; font-size:13px; }}
  .diagram {{ border:1px solid #E3E9F2; border-radius:12px; padding:18px 20px 22px; margin:0 0 22px; page-break-inside: avoid; background:#fff; }}
  .diagram .dnum {{ font-size:11px; font-weight:700; color:#0b6bcb; text-transform:uppercase; letter-spacing:.6px; }}
  .diagram h2 {{ font-size:16px; color:#0b2a4a; margin:3px 0 3px; }}
  .diagram .cap {{ color:#5b6b82; font-size:12.5px; margin:0 0 14px; font-style:italic; }}
  .mermaid {{ text-align:center; }}
  .mermaid svg {{ max-width:100%; height:auto; }}
</style>
<script src="mermaid.min.js"></script>
</head><body>
<div class="page">
  <div class="cover">
    <div class="brand">DEGO HOLDING · MINI TOOL QUẢN LÝ THU MUA</div>
    <h1>Sơ đồ Kỹ thuật Hệ thống</h1>
    <div class="sub">Phiên bản v1.0 · 2026-07-08 · Tài liệu bản vẽ (Technical Diagrams)</div>
  </div>
  {"".join(cards)}
</div>
<script>
  mermaid.initialize({{ startOnLoad: true, theme: "default", flowchart: {{ htmlLabels: true, curve: "basis" }}, securityLevel: "loose" }});
</script>
</body></html>'''

OUT_HTML.write_text(html, encoding="utf-8")
print("Đã ghi HTML:", OUT_HTML)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1100, "height": 900}, device_scale_factor=2)
    page.goto(OUT_HTML.as_uri())
    page.wait_for_selector(".mermaid svg", timeout=20000)
    page.wait_for_timeout(1500)  # để mermaid vẽ xong hết

    # kiểm tra lỗi cú pháp
    body = page.content()
    if "Syntax error" in body or "error-icon" in body:
        print("⚠️ CÓ SƠ ĐỒ LỖI CÚ PHÁP — kiểm tra lại!")
    else:
        print("✅ Tất cả sơ đồ render KHÔNG lỗi cú pháp")

    # PNG từng sơ đồ
    cards_el = page.query_selector_all(".diagram")
    for idx, el in enumerate(cards_el, 1):
        png = HERE / f"so-do-{idx:02d}.png"
        el.screenshot(path=str(png))
        print("PNG:", png.name)

    # PDF cả tài liệu
    page.emulate_media(media="screen")
    page.pdf(path=str(OUT_PDF), format="A4", print_background=True,
             margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"})
    print("PDF:", OUT_PDF)
    browser.close()

print("XONG")
