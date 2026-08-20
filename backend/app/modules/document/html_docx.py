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

from .docx_writer import (AnhNhung, GoiDocx, doan_dau_chan_trang, dong_goi,
                          truong_so_trang, xml_escape)

#  Thẻ khối tạo ra một đoạn mới trong Word.
_THE_DOAN = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"}
#  Thẻ bật/tắt một kiểu chữ.
_THE_KIEU = {"strong": "b", "b": "b", "em": "i", "i": "i",
             "u": "u", "s": "s", "strike": "s", "del": "s"}

_CANH_LE = {"left": "left", "center": "center", "right": "right", "justify": "both"}

_EMU_PER_PX = 9525
_TWIPS_PER_PX = 15
#  Word đo giãn dòng theo 1/240 dòng đơn; CSS `line-height` là bội của cỡ chữ,
#  còn "dòng đơn" của Word = 1,15 lần cỡ chữ (xem `docx_html._SINGLE_LINE_RATIO`).
_SINGLE_LINE_RATIO = 1.15

_SO_LA_MA = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
             "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"]


def _doc_style(chuoi: str) -> dict[str, str]:
    ra: dict[str, str] = {}
    for phan in (chuoi or "").split(";"):
        if ":" not in phan:
            continue
        khoa, _, giatri = phan.partition(":")
        ra[khoa.strip().lower()] = giatri.strip()
    return ra


def _px(giatri: str | None) -> float | None:
    if not giatri:
        return None
    so = re.match(r"^(-?[\d.]+)\s*px$", giatri.strip())
    return float(so.group(1)) if so else None


def _mau(giatri: str | None) -> str | None:
    """`#1a2b3c` hoặc `rgb(1,2,3)` → `1A2B3C`. Word không nhận dấu #."""
    if not giatri:
        return None
    giatri = giatri.strip()
    if giatri.startswith("#"):
        so = giatri[1:]
        if len(so) == 3:
            so = "".join(c * 2 for c in so)
        return so.upper() if len(so) == 6 else None
    rgb = re.match(r"^rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)", giatri)
    if rgb:
        return "".join(f"{int(v):02X}" for v in rgb.groups())
    return None


class _KieuChu:
    """Định dạng đang có hiệu lực tại một điểm trong cây HTML."""

    def __init__(self) -> None:
        self.dam = self.nghieng = self.gach_chan = self.gach_ngang = False
        self.phong: str | None = None
        self.co_pt: float | None = None
        self.mau: str | None = None
        self.nen: str | None = None

    def nhan_ban(self) -> "_KieuChu":
        moi = _KieuChu()
        moi.__dict__.update(self.__dict__)
        return moi

    def rpr(self) -> str:
        phan = ""
        if self.phong:
            ten = xml_escape(self.phong)
            phan += f'<w:rFonts w:ascii="{ten}" w:hAnsi="{ten}" w:cs="{ten}"/>'
        if self.dam:
            phan += "<w:b/>"
        if self.nghieng:
            phan += "<w:i/>"
        if self.gach_chan:
            phan += '<w:u w:val="single"/>'
        if self.gach_ngang:
            phan += "<w:strike/>"
        if self.mau:
            phan += f'<w:color w:val="{self.mau}"/>'
        if self.nen:
            phan += f'<w:shd w:val="clear" w:color="auto" w:fill="{self.nen}"/>'
        if self.co_pt:
            nua_diem = int(round(self.co_pt * 2))
            phan += f'<w:sz w:val="{nua_diem}"/><w:szCs w:val="{nua_diem}"/>'
        return f"<w:rPr>{phan}</w:rPr>" if phan else ""


class _BoChuyen(HTMLParser):
    """Duyệt HTML một lượt, sinh thẳng XML của thân tài liệu."""

    def __init__(self, *, danh_so_muc: bool = False) -> None:
        super().__init__(convert_charrefs=True)
        self.ra: list[str] = []
        self.anh: list[AnhNhung] = []
        self.danh_so_muc = danh_so_muc
        self._dem = [0, 0, 0]              # bộ đếm ba cấp tiêu đề

        self._kieu = [_KieuChu()]
        self._doan_mo = False
        self._runs: list[str] = []
        self._ppr = ""
        self._the_doan = "p"
        self._ngan_xep_list: list[tuple[str, int]] = []   # (ul|ol, số thứ tự)
        self._trong_bang = False
        self._bang: list[str] = []

    # ── tiện ích ─────────────────────────────────────────────────────────────
    @property
    def _kieu_hien(self) -> _KieuChu:
        return self._kieu[-1]

    def _mo_doan(self, the: str, attrs: dict[str, str]) -> None:
        self._doan_mo = True
        self._the_doan = the
        self._runs = []
        self._ppr = self._tinh_ppr(the, attrs)

    def _tinh_ppr(self, the: str, attrs: dict[str, str]) -> str:
        style = _doc_style(attrs.get("style", ""))
        phan = ""
        if the in {"h1", "h2", "h3"}:
            phan += f'<w:pStyle w:val="Heading{the[1]}"/>'
        elif the == "blockquote":
            phan += '<w:ind w:left="720"/>'

        canh = _CANH_LE.get(style.get("text-align", ""))
        if canh:
            phan += f'<w:jc w:val="{canh}"/>'

        thut_trai = _px(style.get("margin-left")) or 0
        thut_dau = _px(style.get("text-indent")) or 0
        #  Danh sách: mỗi cấp thụt thêm một nấc, giữ đúng hình thức bản gốc.
        thut_trai += 360 / _TWIPS_PER_PX * len(self._ngan_xep_list)
        if thut_trai or thut_dau:
            phan += '<w:ind'
            if thut_trai:
                phan += f' w:left="{int(thut_trai * _TWIPS_PER_PX)}"'
            if thut_dau:
                phan += f' w:firstLine="{int(thut_dau * _TWIPS_PER_PX)}"'
            phan += "/>"

        gian = style.get("line-height")
        truoc = _px(style.get("margin-top"))
        sau = _px(style.get("margin-bottom"))
        spacing = ""
        if gian:
            try:
                #  CSS 1.725 = 1,5 dòng Word → 1.5 * 240 = 360.
                dong = float(gian) / _SINGLE_LINE_RATIO
                spacing += f' w:line="{int(round(dong * 240))}" w:lineRule="auto"'
            except ValueError:
                pass
        if truoc:
            spacing += f' w:before="{int(truoc * _TWIPS_PER_PX)}"'
        if sau:
            spacing += f' w:after="{int(sau * _TWIPS_PER_PX)}"'
        if spacing:
            phan += f"<w:spacing{spacing}/>"
        return f"<w:pPr>{phan}</w:pPr>" if phan else ""

    def _dong_doan(self) -> None:
        if not self._doan_mo:
            return
        self._doan_mo = False
        noi_dung = "".join(self._runs)
        #  Đoạn rỗng vẫn phải giữ: người soạn dùng nó làm khoảng trống ký tên.
        xml = f"<w:p>{self._ppr}{noi_dung}</w:p>"
        (self._bang if self._trong_bang else self.ra).append(xml)
        self._runs = []

    def _them_run(self, chu: str) -> None:
        if not chu:
            return
        self._runs.append(
            f'<w:r>{self._kieu_hien.rpr()}<w:t xml:space="preserve">{xml_escape(chu)}</w:t></w:r>'
        )

    def _tien_to_muc(self, the: str) -> str:
        """Số mục tự động cho tiêu đề — viết thẳng vào chữ (xem chú thích đầu tệp)."""
        cap = int(the[1])
        if not self.danh_so_muc or cap > 3:
            return ""
        self._dem[cap - 1] += 1
        for sau in range(cap, 3):
            self._dem[sau] = 0
        so = self._dem[cap - 1]
        if cap == 1:
            return f"{_SO_LA_MA[so - 1] if so <= len(_SO_LA_MA) else so}. "
        if cap == 2:
            return f"{so}. "
        return f"{chr(ord('a') + so - 1) if so <= 26 else so}) "

    # ── HTMLParser ───────────────────────────────────────────────────────────
    def handle_starttag(self, tag: str, attrs_list) -> None:  # noqa: D102
        attrs = {k: (v or "") for k, v in attrs_list}
        tag = tag.lower()

        if tag in _THE_KIEU:
            moi = self._kieu_hien.nhan_ban()
            setattr(moi, {"b": "dam", "i": "nghieng", "u": "gach_chan",
                          "s": "gach_ngang"}[_THE_KIEU[tag]], True)
            self._kieu.append(moi)
            return

        if tag == "span":
            style = _doc_style(attrs.get("style", ""))
            moi = self._kieu_hien.nhan_ban()
            if style.get("font-family"):
                moi.phong = style["font-family"].split(",")[0].strip(" '\"")
            co = style.get("font-size", "")
            if co.endswith("pt"):
                try:
                    moi.co_pt = float(co[:-2])
                except ValueError:
                    pass
            moi.mau = _mau(style.get("color")) or moi.mau
            moi.nen = _mau(style.get("background-color")) or moi.nen
            self._kieu.append(moi)
            return

        if tag in {"ul", "ol"}:
            self._ngan_xep_list.append((tag, 0))
            return

        if tag == "table":
            self._trong_bang = True
            self._bang = ["<w:tbl>", self._tbl_pr()]
            return
        if tag == "tr":
            self._bang.append("<w:tr>")
            return
        if tag in {"td", "th"}:
            self._bang.append(self._tc_pr(attrs))
            #  Ô luôn phải mở bằng một đoạn, kể cả ô trống.
            self._mo_doan("p", {})
            if tag == "th":
                moi = self._kieu_hien.nhan_ban()
                moi.dam = True
                self._kieu.append(moi)
            return

        if tag == "br":
            self._runs.append("<w:r><w:br/></w:r>")
            return

        if tag == "img":
            self._chen_anh(attrs)
            return

        if tag in _THE_DOAN:
            self._dong_doan()
            self._mo_doan(tag, attrs)
            if tag == "li" and self._ngan_xep_list:
                loai, so = self._ngan_xep_list[-1]
                so += 1
                self._ngan_xep_list[-1] = (loai, so)
                self._them_run("• " if loai == "ul" else f"{so}. ")
            elif tag in {"h1", "h2", "h3"}:
                self._them_run(self._tien_to_muc(tag))

    def handle_endtag(self, tag: str) -> None:  # noqa: D102
        tag = tag.lower()
        if tag in _THE_KIEU or tag == "span":
            if len(self._kieu) > 1:
                self._kieu.pop()
            return
        if tag in {"ul", "ol"} and self._ngan_xep_list:
            self._ngan_xep_list.pop()
            return
        if tag in {"td", "th"}:
            self._dong_doan()
            if tag == "th" and len(self._kieu) > 1:
                self._kieu.pop()
            self._bang.append("</w:tc>")
            return
        if tag == "tr":
            self._bang.append("</w:tr>")
            return
        if tag == "table":
            self._bang.append("</w:tbl>")
            self._trong_bang = False
            self.ra.append("".join(self._bang))
            #  Word đòi một đoạn ngay sau bảng, thiếu thì hai bảng liền nhau dính
            #  làm một và người nhận không tách ra được.
            self.ra.append("<w:p/>")
            self._bang = []
            return
        if tag in _THE_DOAN:
            self._dong_doan()

    def handle_data(self, data: str) -> None:  # noqa: D102
        if not data:
            return
        if not self._doan_mo:
            #  Chữ trần ngoài mọi thẻ khối — vẫn phải giữ.
            if not data.strip():
                return
            self._mo_doan("p", {})
        self._them_run(data)

    # ── bảng và ảnh ──────────────────────────────────────────────────────────
    def _tbl_pr(self) -> str:
        canh = "".join(
            f'<w:{v} w:val="single" w:sz="4" w:space="0" w:color="9CA3AF"/>'
            for v in ("top", "left", "bottom", "right", "insideH", "insideV")
        )
        return (f'<w:tblPr><w:tblW w:w="5000" w:type="pct"/>'
                f'<w:tblBorders>{canh}</w:tblBorders></w:tblPr>')

    def _tc_pr(self, attrs: dict[str, str]) -> str:
        style = _doc_style(attrs.get("style", ""))
        phan = ""
        rong = attrs.get("colwidth") or attrs.get("data-colwidth")
        if rong and rong.split(",")[0].strip().isdigit():
            phan += (f'<w:tcW w:w="{int(rong.split(",")[0]) * _TWIPS_PER_PX}" '
                     f'w:type="dxa"/>')
        nen = _mau(style.get("background-color"))
        if nen:
            phan += f'<w:shd w:val="clear" w:color="auto" w:fill="{nen}"/>'
        #  Ô khai `border-*: hidden` (khối đầu văn bản hai cột) phải mất viền
        #  trong Word, nếu không bản xuất ra kẻ ô lù lù giữa quốc hiệu.
        an = [c for c in ("top", "left", "bottom", "right")
              if (style.get(f"border-{c}") or "").strip().startswith("hidden")]
        if an:
            phan += ("<w:tcBorders>"
                     + "".join(f'<w:{c} w:val="nil"/>' for c in an)
                     + "</w:tcBorders>")
        if attrs.get("colspan", "").isdigit() and int(attrs["colspan"]) > 1:
            phan += f'<w:gridSpan w:val="{attrs["colspan"]}"/>'
        return f'<w:tc><w:tcPr>{phan}</w:tcPr>' if phan else "<w:tc><w:tcPr/>"

    def _chen_anh(self, attrs: dict[str, str]) -> None:
        src = attrs.get("src", "")
        khop = re.match(r"^data:image/([a-z]+);base64,(.+)$", src, re.I | re.S)
        if not khop:
            #  Ảnh trỏ ra ngoài: không tải về trong lúc xuất tệp (chậm, và có thể
            #  là đường dẫn nội bộ người nhận không mở được). Ghi chú thay chỗ.
            self._them_run("[ảnh]")
            return
        duoi = khop.group(1).lower()
        duoi = "jpg" if duoi == "jpeg" else duoi
        try:
            du_lieu = base64.b64decode(khop.group(2))
        except Exception:      # noqa: BLE001 — ảnh hỏng thì bỏ qua, không chặn cả tệp
            return

        stt = len(self.anh) + 1
        anh = AnhNhung(ten=f"anh{stt}.{duoi}", du_lieu=du_lieu, duoi=duoi,
                       rid=f"rIdAnh{stt}")
        self.anh.append(anh)

        rong_px = _px(attrs.get("width", "")) or float(attrs.get("width") or 480)
        cao_px = _px(attrs.get("height", "")) or float(attrs.get("height") or 0) or rong_px * 0.62
        cx, cy = int(rong_px * _EMU_PER_PX), int(cao_px * _EMU_PER_PX)
        self._runs.append(
            f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{stt}" name="Anh {stt}"/>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/'
            f'drawingml/2006/picture">'
            f'<pic:pic><pic:nvPicPr><pic:cNvPr id="{stt}" name="{anh.ten}"/>'
            f'<pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{anh.rid}"/><a:stretch><a:fillRect/>'
            f'</a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'
        )

    def ket_thuc(self) -> str:
        self._dong_doan()
        return "".join(self.ra) or "<w:p/>"


def _dong_khung_trang(mau: str, thay: dict[str, str]) -> str:
    """Một vế đầu/chân trang → chuỗi run XML, thẻ số trang thành trường Word."""
    if not mau:
        return ""
    phan: list[str] = []
    con_lai = mau
    for the, truong in (("{{trang}}", "PAGE"), ("{{tong_trang}}", "NUMPAGES")):
        moi: list[str] = []
        for i, khuc in enumerate(con_lai.split(the)):
            if i:
                moi.append("\x00" + truong + "\x00")
            moi.append(khuc)
        con_lai = "".join(moi)
    for khuc in con_lai.split("\x00"):
        if khuc in {"PAGE", "NUMPAGES"}:
            phan.append(truong_so_trang(khuc))
            continue
        for the, giatri in thay.items():
            khuc = khuc.replace(the, giatri)
        if khuc:
            phan.append(f'<w:r><w:t xml:space="preserve">{xml_escape(khuc)}</w:t></w:r>')
    return "".join(phan)


def html_to_docx(
    noi_dung_html: str,
    *,
    le_trai_mm: int = 30,
    le_phai_mm: int = 20,
    danh_so_muc: bool = False,
    dau_trang: tuple[str, str] = ("", ""),
    chan_trang: tuple[str, str] = ("", ""),
    the_thay: dict[str, str] | None = None,
) -> bytes:
    """Chuyển nội dung một phiên bản văn bản thành tệp .docx (bytes)."""
    bo = _BoChuyen(danh_so_muc=danh_so_muc)
    bo.feed(noi_dung_html or "")
    bo.close()

    thay = the_thay or {}
    goi = GoiDocx(than_xml=bo.ket_thuc(), anh=bo.anh)

    trai, phai = (_dong_khung_trang(o, thay) for o in dau_trang)
    if trai or phai:
        goi.dau_trang_xml = doan_dau_chan_trang(trai, phai)
    trai, phai = (_dong_khung_trang(o, thay) for o in chan_trang)
    if trai or phai:
        goi.chan_trang_xml = doan_dau_chan_trang(trai, phai)

    return dong_goi(goi, le_trai_mm=le_trai_mm, le_phai_mm=le_phai_mm)
