import os
import re
import markdown
from playwright.sync_api import sync_playwright
import fitz

def parse_markdown(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    parts = re.split(r'\n---\s*\n', md_text, maxsplit=2)

    # TOC items
    toc_raw = parts[1].replace('## MỤC LỤC', '').strip()
    toc_lines = [l.strip() for l in toc_raw.split('\n') if l.strip()]
    toc_items = []
    appendix_items = []
    for l in toc_lines:
        if l.startswith('- ') or 'Phụ lục' in l:
            appendix_items.append(re.sub(r'^[-\s•*]+', '', l))
        else:
            m = re.match(r'^(\d+)\.\s*(.*)', l)
            if m:
                toc_items.append((m.group(1), m.group(2).strip()))
            else:
                toc_items.append((str(len(toc_items) + 1), l))

    body_md = parts[2]
    extensions = [
        'tables',
        'fenced_code',
        'codehilite',
        'nl2br',
        'sane_lists',
        'attr_list'
    ]
    body_html = markdown.markdown(body_md, extensions=extensions)

    # Styling replacements
    body_html = re.sub(r'<td>\s*<strong>B</strong>\s*</td>', '<td class="col-center"><strong>B</strong></td>', body_html)
    body_html = re.sub(r'<td>\s*<strong>N</strong>\s*</td>', '<td class="col-center"><strong>N</strong></td>', body_html)
    body_html = re.sub(r'<td>\s*<strong>T</strong>\s*</td>', '<td class="col-center"><strong>T</strong></td>', body_html)
    body_html = re.sub(r'<td>\s*B\s*</td>', '<td class="col-center"><strong>B</strong></td>', body_html)
    body_html = re.sub(r'<td>\s*N\s*</td>', '<td class="col-center"><strong>N</strong></td>', body_html)
    body_html = re.sub(r'<td>\s*T\s*</td>', '<td class="col-center"><strong>T</strong></td>', body_html)
    
    # Table column formatting
    body_html = re.sub(r'<th>#</th>', '<th class="col-center col-num">#</th>', body_html)
    body_html = re.sub(r'<td>(\d+)</td>', r'<td class="col-center col-num">\1</td>', body_html)
    
    body_html = body_html.replace('<hr />', '<div class="section-divider"></div>')
    body_html = body_html.replace('<h2>PHỤ LỤC A — BẢNG THUẬT NGỮ</h2>', '<div class="page-break"></div><h2 id="sec-app">PHỤ LỤC A — BẢNG THUẬT NGỮ</h2>')
    body_html = re.sub(r'<p><em>Hết báo cáo\.</em></p>', '<div class="doc-end-marker">— HẾT BÁO CÁO —</div>', body_html)

    # Add IDs to H2 headings for exact detection
    def add_h2_ids(match):
        num = match.group(1)
        title = match.group(2)
        return f'<h2 id="sec-{num}">{num}. {title}</h2>'
    body_html = re.sub(r'<h2>(\d+)\.\s*(.*?)</h2>', add_h2_ids, body_html)

    return toc_items, appendix_items, body_html

def generate_html(toc_items, appendix_items, body_html, page_map=None):
    toc_html_list = ""
    for num, title in toc_items:
        p_num = page_map.get(f"sec-{num}", "") if page_map else ""
        p_str = f'<span class="toc-page-num">{p_num}</span>' if p_num else ""
        toc_html_list += f'''
        <div class="toc-row">
            <span class="toc-title-text"><strong>{num}. {title.upper()}</strong></span>
            <span class="toc-dots"></span>
            {p_str}
        </div>
        '''
    for app in appendix_items:
        p_num = page_map.get("sec-app", "") if page_map else ""
        p_str = f'<span class="toc-page-num">{p_num}</span>' if p_num else ""
        toc_html_list += f'''
        <div class="toc-row toc-appendix">
            <span class="toc-title-text"><strong>{app.upper()}</strong></span>
            <span class="toc-dots"></span>
            {p_str}
        </div>
        '''

    full_html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>BÁO CÁO KẾ HOẠCH TRIỂN KHAI — DEGO WORKHUB</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400;1,600&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

  @page {{
    size: A4;
    margin: 22mm 22mm 20mm 22mm;
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    font-size: 9.6pt;
    line-height: 1.55;
    color: #222222;
    background: #ffffff;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  .page-break {{
    page-break-after: always;
    break-after: page;
    height: 0;
  }}

  /* Cover Page */
  .cover-page {{
    height: 235mm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    page-break-after: always;
    break-after: page;
    padding-top: 8mm;
  }}

  .cover-header-group {{
    text-align: center;
    margin-bottom: 20px;
  }}

  .cover-main-title {{
    font-size: 21pt;
    font-weight: 800;
    color: #0E7DA8;
    letter-spacing: -0.3px;
    line-height: 1.25;
    text-transform: uppercase;
    margin-bottom: 6px;
  }}

  .cover-sub-title {{
    font-size: 17pt;
    font-weight: 800;
    color: #0E7DA8;
    line-height: 1.3;
    text-transform: uppercase;
    margin-bottom: 16px;
  }}

  .cover-tagline {{
    font-size: 10.5pt;
    color: #4B5563;
    font-weight: 500;
    margin-bottom: 25px;
  }}

  .cover-meta-table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 25px;
    font-size: 9.25pt;
  }}

  .cover-meta-table td {{
    border: 1px solid #CCCCCC;
    padding: 7px 12px;
    vertical-align: middle;
  }}

  .cover-meta-table tr td:first-child {{
    width: 28%;
    background-color: #F2F2F2;
    font-weight: 700;
    color: #000000;
  }}

  .cover-meta-table tr td:last-child {{
    background-color: #FFFFFF;
    color: #222222;
  }}

  .cover-footer-note {{
    text-align: center;
    font-size: 8.75pt;
    color: #4B5563;
    line-height: 1.6;
    padding: 0 10mm;
    margin-top: auto;
    margin-bottom: 5mm;
  }}

  /* Page 2: Approval Page */
  .approval-page {{
    page-break-after: always;
    break-after: page;
  }}

  /* Page 3: TOC Page */
  .toc-page {{
    page-break-after: always;
    break-after: page;
  }}

  .toc-row {{
    display: flex;
    align-items: baseline;
    margin-bottom: 10px;
    font-size: 9.5pt;
    color: #0E7DA8;
  }}

  .toc-title-text {{
    white-space: nowrap;
    color: #0E7DA8;
  }}

  .toc-dots {{
    flex-grow: 1;
    border-bottom: 1.5px dotted #0E7DA8;
    margin: 0 8px;
    height: 1px;
    opacity: 0.65;
  }}

  .toc-page-num {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
    color: #0E7DA8;
    font-size: 9.5pt;
    min-width: 16px;
    text-align: right;
  }}

  .toc-appendix {{
    margin-top: 14px;
    padding-top: 10px;
    border-top: 1px solid #E5E7EB;
  }}

  /* Headings */
  h1, h2, h3, h4 {{
    font-family: 'Plus Jakarta Sans', sans-serif;
    color: #0E7DA8;
    page-break-after: avoid;
    break-after: avoid;
  }}

  h2 {{
    font-size: 13.5pt;
    font-weight: 800;
    color: #0E7DA8;
    text-transform: uppercase;
    margin-top: 22px;
    margin-bottom: 10px;
    line-height: 1.3;
  }}

  h3 {{
    font-size: 10.75pt;
    font-weight: 700;
    color: #0E7DA8;
    margin-top: 16px;
    margin-bottom: 8px;
    line-height: 1.35;
  }}

  h4 {{
    font-size: 9.75pt;
    font-weight: 700;
    color: #0E7DA8;
    margin-top: 12px;
    margin-bottom: 6px;
  }}

  p {{
    margin-bottom: 8.5px;
    text-align: justify;
    color: #222222;
  }}

  strong {{
    font-weight: 700;
    color: #000000;
  }}

  em {{
    font-style: italic;
    color: #4B5563;
  }}

  /* Lists */
  ul, ol {{
    margin-top: 4px;
    margin-bottom: 10px;
    padding-left: 20px;
  }}

  li {{
    margin-bottom: 3.5px;
    line-height: 1.5;
  }}

  /* Tables — Exact DEGO WorkHub SRS Styling */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 8px;
    margin-bottom: 14px;
    font-size: 8.9pt;
    page-break-inside: auto;
    break-inside: auto;
  }}

  tr {{
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  thead {{
    display: table-header-group;
  }}

  th {{
    background-color: #0E7DA8;
    color: #FFFFFF;
    font-weight: 700;
    text-align: left;
    padding: 6.5px 9px;
    border: 1px solid #0E7DA8;
    font-size: 8.65pt;
    letter-spacing: 0.15px;
  }}

  td {{
    padding: 5.5px 9px;
    border: 1px solid #CCCCCC;
    vertical-align: top;
    line-height: 1.45;
    background-color: #FFFFFF;
  }}

  tbody tr:nth-child(even) td {{
    background-color: #F8FAFC;
  }}

  .col-center {{
    text-align: center;
    vertical-align: middle;
  }}

  .col-num {{
    width: 30px;
    font-weight: 600;
    color: #4B5563;
  }}

  /* Callout / Note Box */
  .brand-note-box {{
    background-color: #F2F2F2;
    border: 1px solid #E0E0E0;
    border-radius: 4px;
    padding: 10px 14px;
    font-size: 8.75pt;
    color: #333333;
    line-height: 1.5;
    margin-top: 16px;
    margin-bottom: 16px;
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  /* Code & Monospace */
  code {{
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 8pt;
    background-color: #F0F4F8;
    color: #0E7DA8;
    padding: 1px 4px;
    border-radius: 3px;
    border: 1px solid #D1D5DB;
    white-space: nowrap;
  }}

  pre {{
    font-family: 'JetBrains Mono', 'Consolas', monospace;
    font-size: 7.8pt;
    line-height: 1.45;
    background-color: #F8FAFC;
    color: #1E293B;
    border: 1px solid #CCCCCC;
    padding: 10px 14px;
    border-radius: 4px;
    margin-top: 8px;
    margin-bottom: 12px;
    overflow-x: auto;
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  pre code {{
    background: transparent;
    color: inherit;
    padding: 0;
    border: none;
    font-size: inherit;
    white-space: pre;
  }}

  .section-divider {{
    height: 1px;
    background-color: #E5E7EB;
    margin: 18px 0 14px 0;
    page-break-after: avoid;
  }}

  .doc-end-marker {{
    text-align: center;
    font-size: 8.75pt;
    font-weight: 700;
    letter-spacing: 2px;
    color: #0E7DA8;
    margin-top: 24px;
    padding-top: 12px;
    border-top: 1px solid #E5E7EB;
    page-break-inside: avoid;
  }}

  table td:first-child:has(> code) {{
    width: 110px;
    white-space: nowrap;
  }}

</style>
</head>
<body>

<!-- PAGE 1: COVER PAGE -->
<div class="cover-page">
  <div class="cover-header-group">
    <div class="cover-main-title">BÁO CÁO KẾ HOẠCH TRIỂN KHAI</div>
    <div class="cover-sub-title">HỆ THỐNG QUẢN TRỊ NỘI BỘ<br>DEGO WORKHUB</div>
    <div class="cover-tagline">Quản trị Tổ chức — Văn bản tài liệu — Nhân sự — Đào tạo — Công việc</div>
  </div>

  <table class="cover-meta-table">
    <tr>
      <td>Mã tài liệu</td>
      <td><strong>BC-DEGO-IT-001-2026</strong></td>
    </tr>
    <tr>
      <td>Phiên bản</td>
      <td>2.0</td>
    </tr>
    <tr>
      <td>Ngày ban hành</td>
      <td>12/08/2026</td>
    </tr>
    <tr>
      <td>Đơn vị soạn thảo</td>
      <td>Đội Công nghệ thông tin DEGO Holding</td>
    </tr>
    <tr>
      <td>Loại tài liệu</td>
      <td>Báo cáo kế hoạch triển khai</td>
    </tr>
    <tr>
      <td>Trả lời cho</td>
      <td><code>SRS-HOLDING-IT-001-2026</code> — Tài liệu yêu cầu phần mềm DEGO WorkHub, bản 1.1, ngày 11/08/2026</td>
    </tr>
    <tr>
      <td>Trạng thái</td>
      <td>Trình duyệt</td>
    </tr>
    <tr>
      <td>Phạm vi áp dụng</td>
      <td>Toàn tập đoàn DEGO Holding</td>
    </tr>
  </table>

  <div class="cover-footer-note">
    Tài liệu này xác lập lộ trình triển khai chi tiết cho hệ thống DEGO WorkHub theo SRS-HOLDING-IT-001-2026, dựa trên hiện trạng nền tảng công nghệ sẵn có của Tập đoàn DEGO Holding.
  </div>
</div>

<!-- PAGE 2: APPROVAL & BRAND NOTES -->
<div class="approval-page">
  <h2>LỊCH SỬ SOẠN THẢO VÀ PHÊ DUYỆT</h2>
  
  <table>
    <thead>
      <tr>
        <th style="width: 15%;">Phiên bản</th>
        <th style="width: 18%;">Ngày</th>
        <th style="width: 42%;">Nội dung thay đổi</th>
        <th style="width: 25%;">Người thực hiện</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="col-center"><strong>1.0</strong></td>
        <td>11/08/2026</td>
        <td>Dự thảo kế hoạch triển khai sơ bộ</td>
        <td>Đội Công nghệ thông tin</td>
      </tr>
      <tr>
        <td class="col-center"><strong>2.0</strong></td>
        <td>12/08/2026</td>
        <td>Hoàn thiện báo cáo kế hoạch chi tiết: vá nền, phỏng vấn chốt ưu tiên, lộ trình 6 giai đoạn và định biên nhân lực</td>
        <td>Đội Công nghệ thông tin</td>
      </tr>
    </tbody>
  </table>

  <h3 style="margin-top: 20px;">Bảng phê duyệt</h3>
  
  <table>
    <thead>
      <tr>
        <th style="width: 18%;">Vai trò</th>
        <th style="width: 25%;">Họ tên / Đơn vị</th>
        <th style="width: 37%;">Nội dung xác nhận</th>
        <th style="width: 10%;">Ngày</th>
        <th style="width: 10%;">Chữ ký</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Người lập</strong></td>
        <td>Đội Công nghệ thông tin</td>
        <td>Số liệu hiện trạng là số đếm được trên mã nguồn, không phải ước lượng</td>
        <td></td>
        <td></td>
      </tr>
      <tr>
        <td><strong>Người rà soát</strong></td>
        <td>Văn phòng Điều hành</td>
        <td>Thứ tự triển khai và phạm vi từng giai đoạn đúng nhu cầu quản trị</td>
        <td></td>
        <td></td>
      </tr>
      <tr>
        <td><strong>Người phê duyệt</strong></td>
        <td>Tổng Giám đốc</td>
        <td>Chốt lộ trình, chốt nhân lực, chốt các nội dung tại mục 11</td>
        <td></td>
        <td></td>
      </tr>
    </tbody>
  </table>

  <div class="brand-note-box">
    <strong>Ghi chú về nhận diện thương hiệu:</strong> tài liệu dùng hai màu nhận diện của DEGO Holding là xanh lơ (màu chủ đạo <code>#0E7DA8</code>) và xanh lá (màu nhấn <code>#3A9E4E</code>) theo xác nhận của Ban lãnh đạo. Mã màu chính xác theo tệp logo gốc sẽ do phòng Marketing cung cấp để tinh chỉnh đồng loạt khi áp dụng cho giao diện phần mềm.
  </div>
</div>

<!-- PAGE 3: TABLE OF CONTENTS -->
<div class="toc-page">
  <h2>MỤC LỤC</h2>
  <div style="margin-top: 18px;">
    {toc_html_list}
  </div>
</div>

<!-- BODY PAGES (SECTIONS 1 TO 12 + APPENDIX) -->
<div class="body-content">
  {body_html}
</div>

</body>
</html>
"""
    return full_html

def stamp_pdf_headers_and_footers(pdf_path):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    blue_fill = (0.0549, 0.4902, 0.6588)   # #0E7DA8
    green_fill = (0.2275, 0.6196, 0.3059)  # #3A9E4E
    gray_line = (0.82, 0.82, 0.82)
    gray_text = (0.40, 0.40, 0.40)
    white_text = (1.0, 1.0, 1.0)
    
    left_x = 62.36 # 22mm
    
    font_reg_path = "C:/Windows/Fonts/segoeui.ttf"
    font_bold_path = "C:/Windows/Fonts/segoeuib.ttf"
    
    for idx, page in enumerate(doc):
        rect = page.rect
        width = rect.width
        height = rect.height
        page_num = idx + 1
        
        # Insert Unicode fonts into each page
        page.insert_font(fontname="segoe", fontfile=font_reg_path)
        page.insert_font(fontname="segoe-bold", fontfile=font_bold_path)
        
        # 1. Top Header Bar (all pages)
        header_height = 39.69
        page.draw_rect(fitz.Rect(0, 0, width, header_height), color=None, fill=blue_fill)
        
        # Header Left Text
        page.insert_text(
            fitz.Point(left_x, 24.5),
            "DEGO HOLDING",
            fontname="segoe-bold",
            fontsize=11.5,
            color=white_text
        )
        
        # Header Right Text
        if page_num == 1:
            right_text = "Tài liệu nội bộ — Lưu hành hạn chế"
        else:
            right_text = "BC-DEGO-IT-001-2026 · Phiên bản 2.0"
            
        # Compute text length with fitz Font
        f = fitz.Font(fontfile=font_reg_path)
        text_len = f.text_length(right_text, fontsize=9)
        page.insert_text(
            fitz.Point(width - left_x - text_len, 24.5),
            right_text,
            fontname="segoe",
            fontsize=9,
            color=white_text
        )
        
        # 2. Cover Page Bottom Bars (Page 1 only)
        if page_num == 1:
            page.draw_rect(fitz.Rect(0, height - 21.5, width, height - 17.0), color=None, fill=green_fill)
            page.draw_rect(fitz.Rect(0, height - 17.0, width, height), color=None, fill=blue_fill)
            
        # 3. Inner Page Footer (Pages 2+)
        if page_num > 1:
            page.draw_line(fitz.Point(left_x, height - 40), fitz.Point(width - left_x, height - 40), color=gray_line, width=0.75)
            
            footer_left = "Hệ thống Quản trị Nội bộ DEGO WorkHub — Báo cáo kế hoạch triển khai"
            page.insert_text(
                fitz.Point(left_x, height - 26),
                footer_left,
                fontname="segoe",
                fontsize=8.5,
                color=gray_text
            )
            
            footer_right = f"Trang {page_num}"
            f_len = f.text_length(footer_right, fontsize=8.5)
            page.insert_text(
                fitz.Point(width - left_x - f_len, height - 26),
                footer_right,
                fontname="segoe",
                fontsize=8.5,
                color=gray_text
            )
            
    doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    doc.close()

def run_pipeline():
    md_file = r"d:\New folder\thuthapykien\ke-hoach\erp\10-lo-trinh-phat-trien-hrm.md"
    html_file = r"d:\New folder\thuthapykien\ke-hoach\erp\10-lo-trinh-phat-trien-hrm.html"
    pdf_file = r"d:\New folder\thuthapykien\ke-hoach\erp\10-lo-trinh-phat-trien-hrm.pdf"
    
    toc_items, appendix_items, body_html = parse_markdown(md_file)
    
    # Pass 1: Render draft HTML without TOC page numbers
    draft_html = generate_html(toc_items, appendix_items, body_html)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(draft_html)
        
    print("Pass 1: Rendering draft to calculate section page numbers...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page()
        page.goto(f"file:///{html_file.replace(os.sep, '/')}", wait_until="networkidle")
        page.pdf(path=pdf_file, format="A4", print_background=True, display_header_footer=False)
        browser.close()
        
    # Discover section page numbers
    doc = fitz.open(pdf_file)
    page_map = {}
    
    for num, title in toc_items:
        query = f"{num}. {title[:15]}"
        for p_idx, page in enumerate(doc):
            text = page.get_text()
            if query.upper() in text.upper() and p_idx >= 3:
                page_map[f"sec-{num}"] = p_idx + 1
                break
                
    for p_idx, page in enumerate(doc):
        text = page.get_text()
        if "PHỤ LỤC A" in text and p_idx >= 3:
            page_map["sec-app"] = p_idx + 1
            break
            
    doc.close()
    print("Page mapping discovered:", page_map)
    
    # Pass 2: Re-render final HTML with accurate TOC numbers
    final_html = generate_html(toc_items, appendix_items, body_html, page_map)
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print("Pass 2: Rendering final PDF...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page()
        page.goto(f"file:///{html_file.replace(os.sep, '/')}", wait_until="networkidle")
        page.pdf(path=pdf_file, format="A4", print_background=True, display_header_footer=False)
        browser.close()
        
    # Pass 3: Stamp brand headers, footers, and cover stripes
    print("Pass 3: Stamping brand headers, footers, and cover stripes...")
    stamp_pdf_headers_and_footers(pdf_file)
    
    # Export previews
    doc = fitz.open(pdf_file)
    print(f"Complete! Total pages: {len(doc)}")
    preview_dir = r"d:\New folder\thuthapykien\ke-hoach\srs_matched_preview"
    os.makedirs(preview_dir, exist_ok=True)
    for p in [0, 1, 2, 3, 4, len(doc)-1]:
        pix = doc[p].get_pixmap(dpi=150)
        pix.save(os.path.join(preview_dir, f"perfect_srs_{p+1}.png"))
    doc.close()
    print("Saved perfect previews.")

if __name__ == "__main__":
    run_pipeline()
