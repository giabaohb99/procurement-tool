"""THỂ THỨC VĂN BẢN HÀNH CHÍNH — các khối dùng chung cho mọi mẫu và mọi bản demo.

Nghị định 30/2020 điều 8: **khối đầu văn bản có HAI CỘT** — bên trái là tên cơ
quan và số ký hiệu, bên phải là Quốc hiệu, tiêu ngữ và địa danh ngày tháng. Xếp
dọc căn giữa như trước đây là sai thể thức: người nhận quen đọc tên cơ quan ở
góc trái trên cùng, và bản in ra khác hẳn tờ giấy họ đang dùng ngoài đời.

Hai cột dựng bằng **bảng không viền** vì trình soạn thảo (tiptap) không có tab
stop — đó cũng đúng cách Word dựng khối này. Viền tắt bằng `border-*: hidden`
đặt thẳng vào từng ô: đó là dạng mà `table-cell-background-extension.ts` đọc
được, nên mở lên là menu «Viền bảng» hiện đúng "Không viền", sửa tiếp được.

⚠️ Bề ngang cột tính theo trang A4 lề 30/20mm: 794 − 113 − 76 ≈ 605px.
"""

#  Tắt cả bốn cạnh. Khai từng cạnh chứ không viết tắt `border: hidden` — phần
#  đọc thuộc tính của trình soạn thảo dò theo từng cạnh một.
KHONG_VIEN = ("border-top: hidden; border-right: hidden; "
              "border-bottom: hidden; border-left: hidden")

#  Bề ngang hai cột của khối đầu, ĐO THẬT chứ không ước lượng: dòng "CỘNG HÒA
#  XÃ HỘI CHỦ NGHĨA VIỆT NAM" in đậm Times New Roman 14pt chiếm **387px**, cộng
#  padding ô 8px mỗi bên là 403px. Hụt một chút thôi là quốc hiệu gãy làm hai
#  dòng — đã thấy tận mắt ở bản in lúc để 365px.
#
#  ⚠️ KHÔNG bù bằng `padding: 0` đặt thẳng vào ô: tiptap chỉ giữ những thuộc
#  tính nó biết (viền, màu nền, colwidth), nên padding sẽ bay mất ngay lần tự
#  lưu đầu tiên và chữ gãy lại — lúc đó không ai hiểu vì sao.
COT_PHAI_PX = 403
COT_TRAI_PX = 202

#  Khối ký thì chia đôi — hai bên ngang vai nhau.
KY_TRAI_PX = 302
KY_PHAI_PX = 303

_GACH_NGANG = '<p style="text-align:center">———————</p>'


def _o(noi_dung: str, rong: int) -> str:
    #  `colwidth` (KHÔNG phải `data-colwidth`) là thuộc tính mà tiptap đọc để
    #  dựng lại bề ngang cột khi mở trong trình soạn thảo.
    return f'<td colwidth="{rong}" style="{KHONG_VIEN}">{noi_dung}</td>'


def _bang_hai_cot(trai: str, phai: str, rong_trai: int, rong_phai: int) -> str:
    """Bảng hai cột KHÔNG VIỀN, có khai bề ngang cho CẢ HAI nơi đọc nó.

    `<colgroup>` là cho bản in và mọi chỗ hiển thị HTML thô: bảng để
    `table-layout: fixed`, thiếu colgroup là trình duyệt chia đều 50/50 và
    "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" gãy làm hai dòng — đã thấy tận mắt.
    `colwidth` trên ô là cho trình soạn thảo. Khai cả hai thì hai nơi vẽ giống
    nhau, không nơi nào phải đoán.
    """
    return (f'<table><colgroup><col style="width: {rong_trai}px">'
            f'<col style="width: {rong_phai}px"></colgroup><tbody><tr>'
            + _o(trai, rong_trai) + _o(phai, rong_phai)
            + "</tr></tbody></table>")


def _giua(noi_dung: str) -> str:
    return f'<p style="text-align:center">{noi_dung}</p>'


def khoi_dau(ten_co_quan: str, so_hieu: str, dia_danh_ngay: str) -> str:
    """Khối đầu hai cột: cơ quan · số ký hiệu ‖ quốc hiệu · tiêu ngữ · ngày.

    Ba tham số nhận thẳng chuỗi (kể cả mã `{{PHAP_NHAN}}`, `{{SO_HIEU}}`,
    `{{NGAY}}` để thay lúc nạp) — hàm này không biết gì về dữ liệu.
    """
    trai = _giua(f"<strong>{ten_co_quan}</strong>") + _giua(f"Số: {so_hieu}")
    phai = (
        _giua("<strong>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</strong>")
        + _giua("<strong>Độc lập - Tự do - Hạnh phúc</strong>")
        + _GACH_NGANG
        + _giua(f"<em>{dia_danh_ngay}</em>")
    )
    return _bang_hai_cot(trai, phai, COT_TRAI_PX, COT_PHAI_PX)


def khoi_ten_loai(ten_loai: str, trich_yeu: str = "") -> str:
    """Tên loại văn bản + trích yếu, cùng căn giữa."""
    ten = _giua(f"<strong>{ten_loai}</strong>")
    return ten + (_giua(f"<em>{trich_yeu}</em>") if trich_yeu else "")


def khoi_ky_mot_ben(chuc_vu: str, ho_ten: str = "") -> str:
    """Khối chữ ký một bên, nằm bên phải như văn bản thường gặp."""
    ten = f'<p style="text-align:right"><strong>{ho_ten}</strong></p>' if ho_ten else \
        '<p style="text-align:right">……………………………</p>'
    return (f'<p style="text-align:right"><strong>{chuc_vu}</strong></p>'
            '<p style="text-align:right"><em>(Ký, ghi rõ họ tên, đóng dấu)</em></p>'
            '<p style="text-align:right">&nbsp;</p>'
            + ten)


def khoi_ky_hai_ben(trai_chuc_vu: str, phai_chuc_vu: str) -> str:
    """Hai khối ký đứng cạnh nhau — biên bản luôn cần (thư ký ‖ chủ trì)."""
    def _mot_ben(chuc_vu: str) -> str:
        return (_giua(f"<strong>{chuc_vu}</strong>")
                + _giua("<em>(Ký, ghi rõ họ tên)</em>")
                + _giua("&nbsp;")
                + _giua("&nbsp;")
                + _giua("……………………………"))

    #  Hai khối ký chia đôi trang, khác khối đầu (cơ quan hẹp, quốc hiệu rộng).
    return _bang_hai_cot(_mot_ben(trai_chuc_vu), _mot_ben(phai_chuc_vu),
                         KY_TRAI_PX, KY_PHAI_PX)


def khoi_noi_nhan(*noi: str, luu: str = "Lưu: VT, ………") -> str:
    """Khối «Nơi nhận» — phần không ai được quên ở văn bản gửi ra ngoài."""
    return ("<p><strong>Nơi nhận:</strong></p><ul>"
            + "".join(f"<li>{n};</li>" for n in noi)
            + f"<li>{luu}</li></ul>")
