# -*- coding: utf-8 -*-
"""Xuất 1 HOẶC NHIỀU file markdown (kèm sơ đồ Mermaid) -> HTML + PDF hoàn chỉnh.
Nhiều file sẽ được GỘP vào 1 PDF (mỗi file ngắt sang trang mới).

Chạy:
  python doc/export/build_doc_pdf.py technical-design.md
  python doc/export/build_doc_pdf.py --out=tai-lieu-ky-thuat-full technical-design.md so-do-ky-thuat.md
"""
import re, sys, html as htmllib, pathlib
from playwright.sync_api import sync_playwright
import markdown as md

HERE = pathlib.Path(__file__).resolve().parent          # doc/export
DOCDIR = HERE.parent                                     # doc

args = sys.argv[1:] or ["technical-design.md"]
out_stem = None
files = []
for a in args:
    if a.startswith("--out="):
        out_stem = a[6:]
    else:
        files.append(a)
if not out_stem:
    out_stem = pathlib.Path(files[0]).stem if len(files) == 1 else "tai-lieu-full"

OUT_HTML = HERE / f"{out_stem}.html"
OUT_PDF = HERE / f"{out_stem}.pdf"

mermaids = []                                            # toàn cục để không trùng placeholder
def esc(s): return htmllib.escape(s)

def render_file(path: pathlib.Path) -> str:
    text = path.read_text(encoding="utf-8")
    def _grab(m):
        mermaids.append(m.group(1))
        return f"\n\n@@MERMAID{len(mermaids)-1}@@\n\n"
    text = re.sub(r"```mermaid\n(.*?)\n```", _grab, text, flags=re.DOTALL)
    body = md.markdown(text, extensions=["tables", "fenced_code", "sane_lists", "attr_list"])
    return body

sections = [render_file(DOCDIR / f) for f in files]
merged = '<div class="pagebreak"></div>'.join(sections)

# chèn lại sơ đồ (escape để Mermaid nhận đúng, gồm cả <br/>)
for i, code in enumerate(mermaids):
    holder = f"@@MERMAID{i}@@"
    pre = f'<pre class="mermaid">{esc(code)}</pre>'
    merged = merged.replace(f"<p>{holder}</p>", pre).replace(holder, pre)

page = f'''<!doctype html><html lang="vi"><head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; }}
  body {{ font-family:"Segoe UI",Arial,sans-serif; color:#22303f; line-height:1.55; margin:0; }}
  .doc {{ max-width: 880px; margin:0 auto; padding: 28px 40px 60px; }}
  .brandbar {{ background:#0b2a4a; color:#fff; padding:10px 40px; font-size:12px; letter-spacing:.6px; font-weight:600; }}
  .pagebreak {{ page-break-before: always; height:0; }}
  h1 {{ font-size:24px; color:#0b2a4a; margin:22px 0 10px; line-height:1.25; }}
  h2 {{ font-size:18px; color:#0b2a4a; margin:26px 0 8px; padding-bottom:5px; border-bottom:2px solid #E3E9F2; page-break-after: avoid; }}
  h3 {{ font-size:15px; color:#0b3a63; margin:18px 0 6px; }}
  h4 {{ font-size:13.5px; color:#33465a; margin:14px 0 4px; }}
  p, li {{ font-size:13px; }}
  a {{ color:#0b6bcb; text-decoration:none; }}
  table {{ border-collapse:collapse; width:100%; margin:10px 0 16px; font-size:12px; page-break-inside: avoid; }}
  th, td {{ border:1px solid #D8E0EC; padding:6px 9px; text-align:left; vertical-align:top; }}
  th {{ background:#F2F6FB; color:#0b2a4a; font-weight:600; }}
  tr:nth-child(even) td {{ background:#FAFCFE; }}
  code {{ background:#F0F3F8; padding:1px 5px; border-radius:4px; font-family:Consolas,monospace; font-size:12px; }}
  pre code {{ display:block; padding:12px; overflow:auto; }}
  blockquote {{ margin:10px 0; padding:8px 14px; border-left:4px solid #9FC5E8; background:#F5FAFF; color:#33465a; font-size:12.5px; }}
  blockquote p {{ margin:4px 0; }}
  hr {{ border:0; border-top:1px solid #E3E9F2; margin:22px 0; }}
  .mermaid {{ text-align:center; margin:14px 0 20px; page-break-inside: avoid; }}
  .mermaid svg {{ max-width:100%; height:auto; }}
  @page {{ margin: 12mm 10mm; }}
</style>
<script src="mermaid.min.js"></script>
</head><body>
<div class="brandbar">DEGO HOLDING · MINI TOOL QUẢN LÝ THU MUA</div>
<div class="doc">{merged}</div>
<script>
  mermaid.initialize({{ startOnLoad:true, theme:"default", flowchart:{{ htmlLabels:true, curve:"basis" }}, securityLevel:"loose" }});
</script>
</body></html>'''

OUT_HTML.write_text(page, encoding="utf-8")
print("Gộp", len(files), "file:", ", ".join(files), "| sơ đồ:", len(mermaids))

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width":1000,"height":1200}, device_scale_factor=2)
    pg.goto(OUT_HTML.as_uri())
    if mermaids:
        pg.wait_for_selector(".mermaid svg", timeout=30000)
    pg.wait_for_timeout(2000)
    bad = pg.query_selector('svg[aria-roledescription="error"]')
    print("Sơ đồ lỗi cú pháp:", "CÓ" if bad else "không")
    pg.emulate_media(media="screen")
    pg.pdf(path=str(OUT_PDF), format="A4", print_background=True,
           margin={"top":"12mm","bottom":"12mm","left":"10mm","right":"10mm"})
    b.close()

d = OUT_PDF.read_bytes()
print("PDF:", OUT_PDF.name, "|", len(d), "bytes | valid:", d[:5]==b"%PDF-")
print("XONG")
