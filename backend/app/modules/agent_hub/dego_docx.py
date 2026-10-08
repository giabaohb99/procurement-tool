# -*- coding: utf-8 -*-
"""
dego_docx — thư viện dựng file Word (.docx) đúng định dạng DEGO.

ai-CR-116 (08/10/2026): chép NGUYÊN từ skill `dego-docx` của DEGO (chuẩn STD-RECAP-DEGO-v1.0) để bot xuất biên bản họp
đúng mẫu công ty; chỉ đổi đường dẫn logo. Sửa định dạng thì sửa ở skill gốc rồi chép lại, đừng sửa lệch hai nơi.

Đây là NƠI ĐỂ CUSTOMIZE: đổi màu ở phần PALETTE, chỉnh cỡ/khoảng cách trong từng
helper khối, hoặc thêm khối mới theo cùng khuôn mẫu.

Cách dùng tối thiểu:
    from dego_docx import *
    doc = new_document()
    header(doc, ["RECAP HỌP", "MEETING RECAP", "Mã: ...", "v1.0"])
    title(doc, "TIÊU ĐỀ TÀI LIỆU")
    subtitle(doc, "phụ đề mô tả")
    mt = meta_table(doc, [("Ngày","21/07","Giờ","14:00")],
                    full=[("Thành phần","<strong>DX:</strong> A · B")])
    tldr_box(doc, "TL;DR", ["ý 1", "ý <strong>quan trọng</strong>"])
    section_bar(doc, "1. Mục lớn")
    bullet(doc, "gạch đầu dòng <strong>đậm</strong>")
    data_table(doc, ("Hạng mục","Nội dung"), [("A","chi tiết"), ("B","chi tiết")])
    footer(doc, "DEGO HOLDING · Nội bộ", "dòng phụ footer")
    doc.save("OUTPUT.docx")

Yêu cầu: pip install python-docx  (pymupdf tùy chọn — để rasterize logo SVG).
"""
import os, re
from docx import Document
from docx.shared import Pt, RGBColor, Cm, Inches, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_LINE_SPACING, WD_TAB_LEADER
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ======================= PALETTE (customize tại đây) =======================
NAVY="1A4D6B"; TEAL="1E7F9C"; DEEP="115E7D"; GREEN="6DBF3C"; GREENCHK="2E7D32"
BLUE="27ACE3"; INK="1F2937"; GRAY="6B7C8A"; LINE="CBD5DD"; AMBER="E8A317"
BG_TLDR="FFF6E0"; BG_KEY="F1F7FA"; BG_ROWALT="FAFCFD"; WHITE="FFFFFF"
BG_MAU="E9ECEF"; BG_HL="DFF0D8"; BG_HEAD="E7ECEF"; LINKC="0563C1"; CROSS="7E57C2"
BG_SIGN="DCE3EF"                    # nền header "XÉT DUYỆT" (xanh xám nhạt)
FONT="Inter"                       # đổi 'Arial' nếu máy chưa cài Inter
USABLE_CM = 17.78                  # bề rộng bảng = 7.0 inch (7.0*2.54); vùng in ~7.07"
# Indent from left: ĐỒNG NHẤT = 0" cho MỌI loại bảng (per user 2026-08-13);
# và mọi bảng đều preferred width = 7" (USABLE_CM).
FRAME_INDENT_IN = 0.0             # section bar (tiêu đề Phần I/II)
TABLE_INDENT_IN = 0.0             # bảng nội dung có STT: data_table & tasks
TASK_INDENT_IN  = TABLE_INDENT_IN # alias (giữ tương thích)
META_INDENT_IN  = 0.0             # bảng thông tin (Ngày họp / Thành phần)
TLDR_INDENT_IN  = 0.0             # hộp TL;DR
H2_INDENT_IN    = 0.0             # đề mục con h2 (tiêu đề A·/B·, 4.1/4.2/4.3)
# Lề trang: top/bottom 0.43", left/right 0.6"; footer cách mép 0.13" (đặt trong new_document)
PAGE_MARGIN_TB_IN = 0.43
PAGE_MARGIN_LR_IN = 0.6
FOOTER_FROM_EDGE_IN = 0.13

# Màu chip cột "Ưu tiên" theo cấp độ: {nhãn: (nền, chữ)}
PRI = {
    "Cao":        ("FBE3E4", "C0392B"),   # đỏ — ưu tiên cao
    "TB":         ("FFF3CD", "B25E00"),   # vàng — trung bình
    "Trung bình": ("FFF3CD", "B25E00"),
    "Thấp":       ("E1F0DA", "2E7D32"),   # xanh — thấp
}
PRI_DEFAULT = ("EDEFF2", "5A6672")

# vị trí logo — ai-CR-116: bot dùng sẵn PNG đã rasterize (`agent_hub/assets/dego_logo.png`), không cần pymupdf.
_HERE = os.path.dirname(os.path.abspath(__file__))
LOGO_SVG = os.path.join(_HERE, "assets", "dego_logo.svg")
LOGO_PNG = os.path.join(_HERE, "assets", "dego_logo.png")

def C(h): return RGBColor.from_string(h)

# ============================ LOW-LEVEL HELPERS ============================
def set_font(run, name=FONT):
    run.font.name = name
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn('w:rFonts'))
    if rf is None: rf = OxmlElement('w:rFonts'); rpr.append(rf)
    for a in ('w:ascii','w:hAnsi','w:cs'): rf.set(qn(a), name)

def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    for old in tcPr.findall(qn('w:shd')): tcPr.remove(old)
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),'clear'); shd.set(qn('w:color'),'auto'); shd.set(qn('w:fill'),hexcolor)
    tcPr.append(shd)

def set_cell_margins(cell, top=40, bottom=40, left=90, right=90):
    tcPr = cell._tc.get_or_add_tcPr()
    m = OxmlElement('w:tcMar')
    for tag,val in (('w:top',top),('w:bottom',bottom),('w:start',left),('w:end',right)):
        e = OxmlElement(tag); e.set(qn('w:w'),str(val)); e.set(qn('w:type'),'dxa'); m.append(e)
    tcPr.append(m)

def cell_borders(cell, color=LINE, sz=4, sides=('top','bottom','left','right')):
    tcPr = cell._tc.get_or_add_tcPr()
    tb = tcPr.find(qn('w:tcBorders'))
    if tb is None: tb = OxmlElement('w:tcBorders'); tcPr.append(tb)
    tagmap={'top':'w:top','bottom':'w:bottom','left':'w:start','right':'w:end'}
    for s in sides:
        e = tb.find(qn(tagmap[s]))
        if e is None: e = OxmlElement(tagmap[s]); tb.append(e)
        e.set(qn('w:val'),'single'); e.set(qn('w:sz'),str(sz)); e.set(qn('w:space'),'0'); e.set(qn('w:color'),color)

def no_table_borders(table):
    b = OxmlElement('w:tblBorders')
    for tag in ('w:top','w:left','w:bottom','w:right','w:insideH','w:insideV'):
        e=OxmlElement(tag); e.set(qn('w:val'),'none'); b.append(e)
    table._tbl.tblPr.append(b)

def set_table_indent(table, inches):
    """Đặt 'indent from left' của bảng (w:tblInd). Giá trị âm kéo bảng sang trái —
    dùng để canh khung KHÔNG viền bằng với khung CÓ viền."""
    tblPr=table._tbl.tblPr
    for old in tblPr.findall(qn('w:tblInd')): tblPr.remove(old)
    ind=OxmlElement('w:tblInd'); ind.set(qn('w:w'),str(int(round(inches*1440)))); ind.set(qn('w:type'),'dxa')
    tblPr.append(ind)

def set_col_widths(table, widths_cm):
    """Ép bề rộng cột CỨNG (tblLayout=fixed + tblW + tblGrid). BẮT BUỘC dùng
    cách này, chỉ đặt cell.width sẽ bị Word co giãn -> tràn/cắt chữ."""
    table.autofit=False; table.allow_autofit=False
    tbl=table._tbl; tblPr=tbl.tblPr
    twips=[Cm(w).twips for w in widths_cm]
    for old in tblPr.findall(qn('w:tblLayout')): tblPr.remove(old)
    lay=OxmlElement('w:tblLayout'); lay.set(qn('w:type'),'fixed'); tblPr.append(lay)
    for old in tblPr.findall(qn('w:tblW')): tblPr.remove(old)
    tblW=OxmlElement('w:tblW'); tblW.set(qn('w:w'),str(sum(twips))); tblW.set(qn('w:type'),'dxa'); tblPr.append(tblW)
    grid=tbl.find(qn('w:tblGrid'))
    if grid is not None: tbl.remove(grid)
    grid=OxmlElement('w:tblGrid')
    for tw in twips:
        gc=OxmlElement('w:gridCol'); gc.set(qn('w:w'),str(tw)); grid.append(gc)
    tbl.insert(list(tbl).index(tblPr)+1, grid)
    for row in table.rows:
        for i,w in enumerate(widths_cm): row.cells[i].width=Cm(w)

def add_runs(par, text, base_color=INK, size=10, bold_all=False, name=FONT):
    """Parse <strong>...</strong> (in đậm, tô navy) và <br> (xuống dòng) thành run."""
    bold=False
    for tok in re.split(r'(<strong>|</strong>|<br\s*/?>)', text):
        if tok=='<strong>': bold=True; continue
        if tok=='</strong>': bold=False; continue
        if re.match(r'<br\s*/?>', tok):
            (par.runs[-1] if par.runs else par.add_run()).add_break(); continue
        if not tok: continue
        r=par.add_run(tok)
        r.bold=bool(bold or bold_all); r.font.size=Pt(size)
        r.font.color.rgb=C(NAVY if (bold or bold_all) else base_color); set_font(r,name)

def add_hyperlink(par, url, text, color=LINKC, size=9, name=FONT):
    """Chèn hyperlink thật (xanh, gạch chân) vào paragraph."""
    part = par.part
    r_id = part.relate_to(
        url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True)
    link = OxmlElement('w:hyperlink'); link.set(qn('r:id'), r_id)
    r = OxmlElement('w:r'); rpr = OxmlElement('w:rPr')
    col = OxmlElement('w:color'); col.set(qn('w:val'), color); rpr.append(col)
    u = OxmlElement('w:u'); u.set(qn('w:val'), 'single'); rpr.append(u)
    sz = OxmlElement('w:sz'); sz.set(qn('w:val'), str(int(size*2))); rpr.append(sz)
    rf = OxmlElement('w:rFonts')
    for a in ('w:ascii','w:hAnsi','w:cs'): rf.set(qn(a), name)
    rpr.append(rf); r.append(rpr)
    t = OxmlElement('w:t'); t.set(qn('xml:space'),'preserve'); t.text = text; r.append(t)
    link.append(r); par._p.append(link)
    return link

def spacer(doc, pts=6):
    p=doc.add_paragraph(); pf=p.paragraph_format
    pf.space_before=Pt(0); pf.space_after=Pt(0); pf.line_spacing=Pt(pts)
    return p

# ============================== DOCUMENT SETUP ==============================
def new_document(font=FONT):
    doc=Document(); s=doc.sections[0]
    s.page_height=Cm(29.7); s.page_width=Cm(21)
    s.top_margin=Inches(PAGE_MARGIN_TB_IN); s.bottom_margin=Inches(PAGE_MARGIN_TB_IN)
    s.left_margin=Inches(PAGE_MARGIN_LR_IN); s.right_margin=Inches(PAGE_MARGIN_LR_IN)
    s.footer_distance=Inches(FOOTER_FROM_EDGE_IN)          # Footer From Edge = 0.13"
    st=doc.styles['Normal']; st.font.name=font; st.font.size=Pt(10); st.font.color.rgb=C(INK)
    rpr=st.element.get_or_add_rPr(); rf=OxmlElement('w:rFonts')
    for a in ('w:ascii','w:hAnsi','w:cs'): rf.set(qn(a),font)
    rpr.append(rf)
    return doc

# ============================== LOGO (SVG->PNG) ==============================
def ensure_logo_png():
    """Sinh logo.png từ logo.svg (cần pymupdf). Trả về path hoặc None nếu không được."""
    if os.path.exists(LOGO_PNG): return LOGO_PNG
    if not os.path.exists(LOGO_SVG): return None
    try:
        import fitz
        d=fitz.open(LOGO_SVG); pdfb=d.convert_to_pdf()
        pix=fitz.open("pdf",pdfb)[0].get_pixmap(matrix=fitz.Matrix(8,8), alpha=True)
        pix.save(LOGO_PNG); return LOGO_PNG
    except Exception:
        return None

# ============================== BLOCK BUILDERS ==============================
def header(doc, right_lines, logo_width_cm=3.4):
    """right_lines: [dòng1 (đậm to), dòng2 (nghiêng), dòng3.., ...] ở góc phải."""
    ht=doc.add_table(rows=1, cols=2); no_table_borders(ht); set_col_widths(ht,[USABLE_CM/2, USABLE_CM/2])
    lc,rc=ht.rows[0].cells
    set_cell_margins(lc,0,0,0,0); set_cell_margins(rc,0,0,0,0)
    png=ensure_logo_png()
    lp=lc.paragraphs[0]
    if png: lp.add_run().add_picture(png, width=Cm(logo_width_cm))
    else:
        r=lp.add_run("DEGO HOLDING"); r.bold=True; r.font.size=Pt(16); r.font.color.rgb=C(NAVY); set_font(r)
    rp=rc.paragraphs[0]; rp.alignment=WD_ALIGN_PARAGRAPH.RIGHT; rp.paragraph_format.line_spacing=1.1
    for i,line in enumerate(right_lines):
        if i>0: rp.add_run().add_break()
        r=rp.add_run(line)
        if i==0:   r.bold=True;  r.font.size=Pt(12); r.font.color.rgb=C(NAVY)
        elif i==1: r.italic=True; r.font.size=Pt(7.5); r.font.color.rgb=C(GRAY)
        else:      r.font.size=Pt(7); r.font.color.rgb=C(NAVY)
        set_font(r)
    for cc in (lc,rc): cell_borders(cc, color=TEAL, sz=16, sides=('bottom',))
    spacer(doc,6)

def title(doc, text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before=Pt(2); p.paragraph_format.space_after=Pt(3)
    r=p.add_run(text); r.bold=True; r.font.size=Pt(19); r.font.color.rgb=C(NAVY); set_font(r)

def subtitle(doc, text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(10)
    r=p.add_run(text); r.italic=True; r.font.size=Pt(10.5); r.font.color.rgb=C(GRAY); set_font(r)

def _split_br(text):
    """Tách <br> thành các đoạn riêng. Lý do: trong đoạn canh đều (Justified), dòng kết
    thúc bằng NGẮT DÒNG MỀM <br> vẫn bị Word kéo giãn hết chiều ngang (chỉ dòng cuối THẬT
    của paragraph mới không giãn). Biến mỗi <br> thành một paragraph -> dòng cuối mỗi đoạn
    canh trái tự nhiên, hết lỗi 'vài chữ dàn ngang'."""
    parts=[s for s in re.split(r'<br\s*/?>', text) if s.strip()!='']
    return parts or ['']

def note(doc, text, size=8):
    parts=_split_br(text); p=None
    for k,seg in enumerate(parts):
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
        pf=p.paragraph_format; pf.right_indent=Inches(0.07)          # chuẩn đoạn văn: Justified + Right 0.07"
        pf.space_after=Pt(8 if k==len(parts)-1 else 2)
        add_runs(p, seg, base_color=GRAY, size=size)
        for r in p.runs: r.italic=True
    return p

def para(doc, text, size=10, space_after=4):
    """Đoạn văn bản thường của thân tài liệu. CHUẨN (per user 2026-08-22):
    Paragraph Alignment = Justified · Indentation Right = 0.07" · Line spacing 1.25.
    Hỗ trợ <strong> (đậm, tô navy). <br> được tách thành ĐOẠN RIÊNG (xem _split_br) để
    dòng cuối không bị canh đều kéo giãn."""
    parts=_split_br(text); p=None
    for k,seg in enumerate(parts):
        p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY
        pf=p.paragraph_format
        pf.right_indent=Inches(0.07); pf.space_before=Pt(0); pf.line_spacing=1.25
        pf.space_after=Pt(space_after if k==len(parts)-1 else 2)
        add_runs(p, seg, size=size)
    return p

def toc(doc, entries, right_at_in=None):
    """Mục lục dạng dòng dot-leader — KHÔNG kẻ bảng, KHÔNG hàng tiêu đề.
    entries: list tuple (label, title, page, level). level 1 (đậm, navy) hoặc 2 (thụt 0.34", nhạt).
    Mỗi dòng: [tên phần]  [tiêu đề phần]  ……  [số trang] — dấu chấm lấp khoảng trống tới lề phải,
    số trang canh sát phải. `label`='' thì bỏ cột tên phần. `page`='' để trống (bản nháp).
    Tab stop số trang mặc định = 7.0" (= mép phải bảng, USABLE_CM); override bằng `right_at_in`."""
    right = Inches(right_at_in) if right_at_in else Cm(USABLE_CM)   # 7.0" — canh bằng mép phải bảng
    for e in entries:
        label = e[0]; title = e[1]; page = e[2] if len(e) > 2 else ""
        level = e[3] if len(e) > 3 else 1
        p=doc.add_paragraph(); pf=p.paragraph_format
        pf.tab_stops.add_tab_stop(right, WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
        if level == 1:
            pf.space_before=Pt(6); pf.space_after=Pt(1); pf.line_spacing_rule=WD_LINE_SPACING.SINGLE
            lab_c, tit_c, fs, bold = NAVY, NAVY, 11, True
        else:
            pf.space_before=Pt(0); pf.space_after=Pt(0); pf.left_indent=Inches(0.34)
            pf.line_spacing_rule=WD_LINE_SPACING.SINGLE
            lab_c, tit_c, fs, bold = TEAL, INK, 9.5, False
        if label:
            r=p.add_run(str(label)+"   "); r.bold=True; r.font.size=Pt(fs); r.font.color.rgb=C(lab_c); set_font(r)
        add_runs(p, title, base_color=tit_c, size=fs, bold_all=bold)
        r=p.add_run("\t"+str(page)); r.bold=(level==1); r.font.size=Pt(fs)
        r.font.color.rgb=C(NAVY if level==1 else GRAY); set_font(r)
    spacer(doc,6)

def meta_table(doc, rows, full=None, widths=(2.6,6.29,2.6,6.29), full_key_w=2.6):
    """rows: list các tuple (k1,v1,k2,v2). full: list (key, value_html) chiếm cả dòng.
    widths: bề rộng 4 cột (key1,val1,key2,val2) — chỉnh để nhãn dài không bị xuống dòng
    (vd 'Phòng ban yêu cầu' cần cột key2 rộng hơn); tổng nên = USABLE_CM. `full_key_w`=bề
    rộng cột nhãn của các dòng full (Mục đích...)."""
    if rows:
        mt=doc.add_table(rows=0, cols=4)
        for (k1,v1,k2,v2) in rows:
            cells=mt.add_row().cells
            for c,(txt,kind) in zip(cells,[(k1,'k'),(v1,'v'),(k2,'k'),(v2,'v')]):
                set_cell_margins(c,60,60,110,110); cell_borders(c,color=LINE,sz=4)
                p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0)   # spacing after 0pt toàn bảng
                if kind=='k':
                    shade(c,BG_KEY); cell_borders(c,color=TEAL,sz=16,sides=('left',))
                    r=p.add_run(txt); r.bold=True; r.font.size=Pt(9); r.font.color.rgb=C(TEAL)
                else:
                    r=p.add_run(txt); r.font.size=Pt(9); r.font.color.rgb=C(INK)
                set_font(r)
        set_col_widths(mt,list(widths)); set_table_indent(mt, META_INDENT_IN)
    for (k,v) in (full or []):
        mf=doc.add_table(rows=1, cols=2); set_col_widths(mf,[full_key_w,USABLE_CM-full_key_w]); set_table_indent(mf, META_INDENT_IN)
        kc,vc=mf.rows[0].cells
        shade(kc,BG_KEY); cell_borders(kc,color=TEAL,sz=16,sides=('left',))
        cell_borders(kc,color=LINE,sz=4,sides=('top','bottom','right')); cell_borders(vc,color=LINE,sz=4)
        set_cell_margins(kc,60,60,110,110); set_cell_margins(vc,60,60,110,110)
        pk=kc.paragraphs[0]; pk.paragraph_format.space_after=Pt(0)
        r=pk.add_run(k); r.bold=True; r.font.size=Pt(9); r.font.color.rgb=C(TEAL); set_font(r)
        p=vc.paragraphs[0]; p.paragraph_format.line_spacing=1.25; p.paragraph_format.space_after=Pt(0); add_runs(p, v, size=9)
    spacer(doc,6)

def tldr_box(doc, heading, items):
    t=doc.add_table(rows=1,cols=1); no_table_borders(t); set_col_widths(t,[USABLE_CM])   # preferred width 7"
    set_table_indent(t, TLDR_INDENT_IN)                        # TL;DR: indent from left 0"
    c=t.rows[0].cells[0]; shade(c,BG_TLDR); cell_borders(c,color=AMBER,sz=18,sides=('left',))
    set_cell_margins(c,90,90,150,150)
    r=c.paragraphs[0].add_run(heading); r.bold=True; r.font.size=Pt(10); r.font.color.rgb=C(NAVY); set_font(r)
    for x in items:
        p=c.add_paragraph(); pf=p.paragraph_format
        pf.left_indent=Cm(0.5); pf.first_line_indent=Cm(-0.5); pf.space_after=Pt(3); pf.line_spacing=1.2
        r=p.add_run('•  '); r.bold=True; r.font.color.rgb=C(TEAL); r.font.size=Pt(10); set_font(r)
        add_runs(p, x, size=10)
    spacer(doc,8)

def section_bar(doc, text):
    t=doc.add_table(rows=1, cols=2); no_table_borders(t); set_col_widths(t,[0.14, USABLE_CM-0.14])
    set_table_indent(t, FRAME_INDENT_IN)                       # canh khung bằng bảng có viền
    badge,bar=t.rows[0].cells
    shade(badge,GREEN); shade(bar,TEAL); set_cell_margins(badge,0,0,0,0); set_cell_margins(bar,70,70,140,140)
    # Chuẩn CHUNG mọi văn bản: MỌI paragraph trong bảng tiêu đề lớn (cả ô badge lẫn ô chữ) =
    # Spacing After 0pt + Line spacing Single — nếu bỏ sót ô badge, Word hiện TRỐNG khi bôi cả thanh.
    for cell in (badge, bar):
        for pp in cell.paragraphs:
            pp.paragraph_format.space_before=Pt(0)
            pp.paragraph_format.space_after=Pt(0)                  # Spacing After = 0pt
            pp.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE  # Line spacing = Single
    p=bar.paragraphs[0]
    r=p.add_run(text.upper()); r.bold=True; r.font.size=Pt(11.5); r.font.color.rgb=C(WHITE); set_font(r)
    bar.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
    spacer(doc,2)                                              # tiêu đề lớn: bottom ~0, sát bảng bên dưới

def h2(doc, text):
    t=doc.add_table(rows=1,cols=1); no_table_borders(t); set_col_widths(t,[USABLE_CM])   # preferred width 7"
    set_table_indent(t, H2_INDENT_IN)                          # h2 (tiêu đề A·/B·, 4.1/4.2/4.3): indent 0.1"
    c=t.rows[0].cells[0]; shade(c,BG_ROWALT)
    cell_borders(c,color=BLUE,sz=18,sides=('left',)); cell_borders(c,color=LINE,sz=4,sides=('bottom',))
    set_cell_margins(c,50,50,120,120)
    p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(0)     # Spacing After 0pt
    r=p.add_run(text); r.bold=True; r.font.size=Pt(11); r.font.color.rgb=C(NAVY); set_font(r)
    spacer(doc,4)

def label(doc, text):
    p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(6); p.paragraph_format.space_after=Pt(2)
    r=p.add_run(text.upper()); r.bold=True; r.font.size=Pt(9.5); r.font.color.rgb=C(TEAL); set_font(r)

# CHUẨN đoạn văn nội dung (per user 2026-08-14, dùng chung mọi văn bản):
# Alignment=Justified · Indentation Left 0" (KHÔNG âm) · Right 0.1" · Special Hanging By 0.2" ·
# Before 0pt · After 3pt · Line spacing Multiple 1.25.
# Kỹ thuật: đặt w:left = w:hanging = 0.2" để first-line (marker) nằm ĐÚNG mốc 0"
# (Word hiển thị "Left = 0"", không âm); thân chữ hanging ở 0.2". Marker + TAB nhảy tới mốc
# hanging này → chữ thân canh đều, tab không bị justify kéo giãn.
def _content_para_format(pf):
    pf.left_indent=Inches(0.2); pf.first_line_indent=Inches(-0.2); pf.right_indent=Inches(0.1)
    pf.space_before=Pt(0); pf.space_after=Pt(3); pf.line_spacing=1.25

def bullet(doc, text, marker='•', mcolor=TEAL, size=10):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY; _content_para_format(p.paragraph_format)
    r=p.add_run(marker+'\t'); r.bold=True; r.font.color.rgb=C(mcolor); r.font.size=Pt(size); set_font(r)
    add_runs(p, text, size=size)

def check(doc, text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY; _content_para_format(p.paragraph_format)
    r=p.add_run('✓\t'); r.bold=True; r.font.color.rgb=C(GREENCHK); r.font.size=Pt(10); set_font(r)
    add_runs(p, text, size=10)

def data_table(doc, head, rows, widths=(1.25, 5.15, 11.38)):
    """Bảng 3 cột: STT | head[0] | head[1]. rows = list (col1_html, col2_html).
    Cùng định dạng chung với tasks() (header teal, STT navy, dòng chẵn tô nền, indent 0.08")."""
    t=doc.add_table(rows=1, cols=3)
    set_table_indent(t, TABLE_INDENT_IN)                      # indent chung 0.08" (giống bảng tasks)
    for i,c in enumerate(t.rows[0].cells):
        shade(c,TEAL); cell_borders(c,color=TEAL,sz=4); set_cell_margins(c,60,60,110,110)
        p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER if i==0 else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after=Pt(0)
        r=p.add_run(['STT',head[0],head[1]][i]); r.bold=True; r.font.size=Pt(9.5); r.font.color.rgb=C(WHITE); set_font(r)
        c.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
    for idx,(a,b) in enumerate(rows,1):
        cells=t.add_row().cells
        for j,c in enumerate(cells):
            if idx%2==0: shade(c,BG_ROWALT)
            cell_borders(c,color=LINE,sz=4); set_cell_margins(c,50,50,110,110)
            p=c.paragraphs[0]; p.paragraph_format.line_spacing=1.2; p.paragraph_format.space_after=Pt(0)
            if j==0:
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER; c.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
                r=p.add_run(str(idx)); r.bold=True; r.font.size=Pt(9); r.font.color.rgb=C(NAVY); set_font(r)
            elif j==1: add_runs(p, a, base_color=NAVY, size=9, bold_all=True)
            else:      add_runs(p, b, size=9)
    set_col_widths(t, list(widths))
    spacer(doc,6)
    return t

def notice_calendar(doc, month_title, dow, cells, row_h_cm=1.45):
    """Bảng LỊCH NGHỈ cho THÔNG BÁO (nghỉ lễ / lịch làm việc) — nhánh 'thông báo'.
    month_title: tiêu đề gộp trên cùng (vd 'THÁNG 8 & 9.2026').
    dow:   nhãn cột thứ (vd ['T2','T3','T4','T5','T6','T7','CN']).
    cells: cùng độ dài dow; mỗi phần tử (ngày, ghi_chú, kind):
           kind '' = ngày thường (nền trắng, số navy);
           'holiday' = nghỉ lễ (nền vàng nhạt, số + ghi chú đỏ);
           'weekend' = cuối tuần (số + ghi chú đỏ, không nền);
           'work'    = đi làm/làm bù (nền xanh nhạt, ghi chú xanh)."""
    n=len(dow); w=USABLE_CM/n
    HOL_BG='FFF3CD'; WORK_BG='E1F0DA'; REDC='C0392B'
    t=doc.add_table(rows=3, cols=n); set_table_indent(t, TABLE_INDENT_IN)
    # Hàng 0: tiêu đề tháng (gộp toàn hàng)
    m=t.rows[0].cells[0].merge(t.rows[0].cells[-1])
    shade(m,TEAL); cell_borders(m,color=TEAL,sz=4); set_cell_margins(m,55,55,90,90)
    m.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
    p=m.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
    r=p.add_run(month_title); r.bold=True; r.font.size=Pt(10.5); r.font.color.rgb=C(WHITE); set_font(r)
    # Hàng 1: thứ trong tuần (nền teal đậm, chữ trắng)
    for i,c in enumerate(t.rows[1].cells):
        shade(c,DEEP); cell_borders(c,color=TEAL,sz=4); set_cell_margins(c,40,40,50,50)
        c.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
        p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
        r=p.add_run(dow[i]); r.bold=True; r.font.size=Pt(9.5); r.font.color.rgb=C(WHITE); set_font(r)
    # Hàng 2: ngày (+ ghi chú), tô màu theo kind
    for i,c in enumerate(t.rows[2].cells):
        item=cells[i] if i<len(cells) else ('','','')
        day=item[0]; note_txt=item[1] if len(item)>1 else ''; kind=item[2] if len(item)>2 else ''
        cell_borders(c,color=LINE,sz=4); set_cell_margins(c,60,60,50,50); c.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
        if kind=='holiday': shade(c,HOL_BG)
        elif kind=='work': shade(c,WORK_BG)
        p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
        datecol = REDC if kind in ('holiday','weekend') else NAVY
        r=p.add_run(day); r.bold=True; r.font.size=Pt(10); r.font.color.rgb=C(datecol); set_font(r)
        if note_txt:
            p2=c.add_paragraph(); p2.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p2.paragraph_format.space_before=Pt(0); p2.paragraph_format.space_after=Pt(0)
            p2.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
            ncol = REDC if kind in ('holiday','weekend') else (GREENCHK if kind=='work' else GRAY)
            r=p2.add_run(note_txt); r.italic=True; r.font.size=Pt(8); r.font.color.rgb=C(ncol); set_font(r)
    trPr=t.rows[2]._tr.get_or_add_trPr()
    trh=OxmlElement('w:trHeight'); trh.set(qn('w:val'),str(int(Cm(row_h_cm).twips))); trh.set(qn('w:hRule'),'atLeast'); trPr.append(trh)
    set_col_widths(t,[w]*n); spacer(doc,6); return t

def _compare_val(par, val, size=9):
    """Render 1 ô của compare_table. Token đặc biệt:
    '✓' -> dấu check xanh · '✗' -> dấu ✗ tím · 'text|url' -> hyperlink · còn lại: add_runs."""
    v = ("" if val is None else str(val)).strip()
    if v in ('✓','[v]','v','yes','Yes'):
        r=par.add_run('✓'); r.bold=True; r.font.size=Pt(size+2); r.font.color.rgb=C(GREENCHK); set_font(r); return
    if v in ('✗','[x]','x','no','No'):
        r=par.add_run('✗'); r.bold=True; r.font.size=Pt(size+2); r.font.color.rgb=C(CROSS); set_font(r); return
    if '|' in v and 'http' in v.split('|',1)[1]:
        text,url = v.split('|',1); add_hyperlink(par, url.strip(), text.strip(), size=size); return
    if not v: return
    add_runs(par, v, size=size)

def compare_table(doc, headers, rows, highlight=None, base=None, label_w=3.2):
    """Bảng SO SÁNH nhiều phương án (cột) theo hạng mục (dòng).
    headers: [nhãn_cột_đầu, tên_PA1, tên_PA2, ...] — hàng tiêu đề (cột 0 = cột hạng mục).
    rows: list [(nhãn_hạng_mục, giá_trị_PA1, giá_trị_PA2, ...)] — mỗi tuple dài bằng headers.
    highlight: chỉ số cột (0-based, tính cả cột nhãn) được tô XANH LÁ = phương án đề xuất.
    base: chỉ số cột 'Mẫu'/yêu cầu được tô XÁM để đối chiếu.
    Giá trị đặc biệt trong ô: '✓' -> check xanh · '✗' -> ✗ tím · 'text|http...' -> hyperlink.
    Bề rộng: cột nhãn = label_w cm, các cột còn lại chia đều phần còn lại của USABLE_CM."""
    ncol = len(headers)
    data_w = (USABLE_CM - label_w) / (ncol - 1)
    widths = [label_w] + [data_w]*(ncol-1)
    t = doc.add_table(rows=1, cols=ncol); set_table_indent(t, TABLE_INDENT_IN)
    # ---- header (lặp lại đầu mỗi trang khi bảng tràn trang) ----
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement('w:tblHeader'); th.set(qn('w:val'),'true'); trPr.append(th)
    hcells = t.rows[0].cells
    for i,c in enumerate(hcells):
        shade(c,TEAL)                                          # hàng tiêu đề: nền teal #1E7F9C, chữ trắng
        cell_borders(c,color=TEAL,sz=4); set_cell_margins(c,55,55,90,90)
        p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.LEFT if i==0 else WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after=Pt(0)
        r=p.add_run(headers[i]); r.bold=True; r.font.size=Pt(9); r.font.color.rgb=C(WHITE); set_font(r)
        c.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
    # ---- body ----
    for row in rows:
        cells=t.add_row().cells
        for i,c in enumerate(cells):
            cell_borders(c,color=LINE,sz=4); set_cell_margins(c,45,45,90,90)
            if i==highlight: shade(c,BG_HL)
            elif i==base:    shade(c,BG_MAU)
            p=c.paragraphs[0]; p.paragraph_format.line_spacing=1.15; p.paragraph_format.space_after=Pt(0)
            if i==0:
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT
                r=p.add_run("" if row[i] is None else str(row[i]))
                r.bold=True; r.font.size=Pt(9); r.font.color.rgb=C(NAVY); set_font(r)
            else:
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                _compare_val(p, row[i] if i < len(row) else "")
            c.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
    set_col_widths(t, widths); spacer(doc,6); return t

def tasks(doc, rows, widths=(1.25, 9.53, 4.0, 3.0)):
    """Bảng công việc 4 cột: STT | Việc | Người | Ưu tiên.
    rows = list (viec_html, nguoi, pri). pri ∈ {Cao, TB, Trung bình, Thấp} — cột Ưu tiên
    tô màu theo cấp (đỏ/vàng/xanh)."""
    t=doc.add_table(rows=1, cols=4)
    set_table_indent(t, TASK_INDENT_IN)                       # bảng công việc: indent 0.08" (chung với data_table)
    heads=['STT','Việc','Người','Ưu tiên']
    aligns=[WD_ALIGN_PARAGRAPH.CENTER, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.CENTER]
    for i,c in enumerate(t.rows[0].cells):
        shade(c,TEAL); cell_borders(c,color=TEAL,sz=4); set_cell_margins(c,60,60,110,110)
        p=c.paragraphs[0]; p.alignment=aligns[i]; p.paragraph_format.space_after=Pt(0)
        r=p.add_run(heads[i]); r.bold=True; r.font.size=Pt(9.5); r.font.color.rgb=C(WHITE); set_font(r)
        c.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
    for idx,(viec,nguoi,pri) in enumerate(rows,1):
        cells=t.add_row().cells; alt=(idx%2==0)
        for j,c in enumerate(cells):
            cell_borders(c,color=LINE,sz=4); set_cell_margins(c,50,50,110,110)
            p=c.paragraphs[0]; p.paragraph_format.line_spacing=1.2; p.paragraph_format.space_after=Pt(0)
            if j==0:
                if alt: shade(c,BG_ROWALT)
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER; c.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
                r=p.add_run(str(idx)); r.bold=True; r.font.size=Pt(9); r.font.color.rgb=C(NAVY); set_font(r)
            elif j==1:
                if alt: shade(c,BG_ROWALT)
                add_runs(p, viec, size=9)
            elif j==2:
                if alt: shade(c,BG_ROWALT)
                add_runs(p, nguoi, size=9)
            else:
                bg,tx = PRI.get(pri, PRI_DEFAULT); shade(c, bg)
                p.alignment=WD_ALIGN_PARAGRAPH.CENTER; c.vertical_alignment=WD_ALIGN_VERTICAL.CENTER
                r=p.add_run(pri); r.bold=True; r.font.size=Pt(9); r.font.color.rgb=C(tx); set_font(r)
    set_col_widths(t, list(widths))
    spacer(doc,6)
    return t

def signoff(doc, cols, sign_h_cm=2.0, widths=None):
    """Khối chữ ký XÉT DUYỆT (KHÔNG viền, KHÔNG nền) — đặt NGAY SAU `section_bar('… XÉT DUYỆT')`
    (nhãn "XÉT DUYỆT" do thanh teal đảm nhiệm, block này chỉ dựng các cột chữ ký).
    cols = list (chức_danh, tên_ký_sẵn) — `tên_ký_sẵn`='' nếu để trống cho người ký điền.
    Mỗi cột: chức danh (đậm navy) + '(Ký, ghi rõ họ tên)' (nghiêng xám) ở trên → ô ký trống
    cao (`sign_h_cm`) → tên ký sẵn (nghiêng) canh dưới đáy.
    widths: bề rộng từng cột (cm) — chỉnh để chức danh dài (vd 'TP/Trưởng bộ phận duyệt')
    không bị xuống dòng; None = chia đều. Tổng nên = USABLE_CM."""
    n=len(cols)
    colws=list(widths) if widths else [USABLE_CM/n]*n
    t=doc.add_table(rows=2, cols=n); no_table_borders(t); set_table_indent(t, TABLE_INDENT_IN)
    # --- Hàng 0: chức danh + (Ký, ghi rõ họ tên) ---
    for i,c in enumerate(t.rows[0].cells):
        set_cell_margins(c,40,30,90,90); c.vertical_alignment=WD_ALIGN_VERTICAL.TOP
        p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
        add_runs(p, cols[i][0], base_color=NAVY, size=10, bold_all=True)
        p2=c.add_paragraph(); p2.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_after=Pt(0); p2.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
        r2=p2.add_run("(Ký, ghi rõ họ tên)"); r2.italic=True; r2.font.size=Pt(9); r2.font.color.rgb=C(GRAY); set_font(r2)
    # --- Hàng 1: ô ký trống cao, tên ký sẵn canh dưới ---
    for i,c in enumerate(t.rows[1].cells):
        set_cell_margins(c,40,40,90,90); c.vertical_alignment=WD_ALIGN_VERTICAL.BOTTOM
        p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after=Pt(0); p.paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
        name=cols[i][1] if len(cols[i])>1 else ""
        if name:
            r=p.add_run(name); r.italic=True; r.font.size=Pt(10); r.font.color.rgb=C(INK); set_font(r)
    trPr=t.rows[1]._tr.get_or_add_trPr()
    trh=OxmlElement('w:trHeight'); trh.set(qn('w:val'),str(int(Cm(sign_h_cm).twips))); trh.set(qn('w:hRule'),'atLeast'); trPr.append(trh)
    set_col_widths(t,colws); spacer(doc,6); return t

def footer(doc, left, center, right, sub=None):
    """Footer 3 cụm trên 1 dòng (tab): trái (đậm, sát trái) · giữa (canh giữa) · phải (đậm, sát phải).
    Paragraph có Spacing Before 6pt. `sub` = dòng phụ nghiêng, canh giữa (tùy chọn)."""
    sec=doc.sections[0]; ftr=sec.footer
    usable = sec.page_width - sec.left_margin - sec.right_margin   # EMU
    fp=ftr.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.LEFT
    fp.paragraph_format.space_before=Pt(6); fp.paragraph_format.space_after=Pt(0)
    ts=fp.paragraph_format.tab_stops
    # Bỏ tab mặc định của style Footer trong Word (center 3.25", right 6.5") — nếu không,
    # cụm giữa sẽ bám nhầm mốc 3.25" thay vì tâm vùng in.
    ts.add_tab_stop(Inches(3.25), WD_TAB_ALIGNMENT.CLEAR)
    ts.add_tab_stop(Inches(6.5),  WD_TAB_ALIGNMENT.CLEAR)
    ts.add_tab_stop(Emu(int(usable/2)), WD_TAB_ALIGNMENT.CENTER)   # canh giữa ở ~3.53" (tâm vùng in)
    ts.add_tab_stop(Emu(int(usable)),   WD_TAB_ALIGNMENT.RIGHT)    # canh phải ở mép phải vùng in
    def seg(txt, bold):
        r=fp.add_run(txt); r.bold=bold; r.font.size=Pt(7.5); r.font.color.rgb=C(GRAY); set_font(r)
    seg(left, True); fp.add_run('\t'); seg(center, False); fp.add_run('\t'); seg(right, True)
    if sub:
        fp2=ftr.add_paragraph(); fp2.alignment=WD_ALIGN_PARAGRAPH.CENTER
        r=fp2.add_run(sub); r.italic=True; r.font.size=Pt(7); r.font.color.rgb=C(GRAY); set_font(r)
