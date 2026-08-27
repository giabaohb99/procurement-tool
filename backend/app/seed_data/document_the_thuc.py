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
NO_BORDER = ("border-top: hidden; border-right: hidden; "
              "border-bottom: hidden; border-left: hidden")

#  Bề ngang hai cột của khối đầu, ĐO THẬT chứ không ước lượng: dòng "CỘNG HÒA
#  XÃ HỘI CHỦ NGHĨA VIỆT NAM" in đậm Times New Roman 14pt chiếm **387px**, cộng
#  padding ô 8px mỗi bên là 403px. Hụt một chút thôi là quốc hiệu gãy làm hai
#  dòng — đã thấy tận mắt ở bản in lúc để 365px.
#
#  ⚠️ KHÔNG bù bằng `padding: 0` đặt thẳng vào ô: tiptap chỉ giữ những thuộc
#  tính nó biết (viền, màu nền, colwidth), nên padding sẽ bay mất ngay lần tự
#  lưu đầu tiên và chữ gãy lại — lúc đó không ai hiểu vì sao.
COL_RIGHT_PX = 403
COL_LEFT_PX = 202

#  Khối ký thì chia đôi — hai bên ngang vai nhau.
SIGN_LEFT_PX = 302
SIGN_RIGHT_PX = 303

_DIVIDER_LINE = '<p style="text-align:center">———————</p>'


def _o(content: str, width: int) -> str:
    #  `colwidth` (KHÔNG phải `data-colwidth`) là thuộc tính mà tiptap đọc để
    #  dựng lại bề ngang cột khi mở trong trình soạn thảo.
    return f'<td colwidth="{width}" style="{NO_BORDER}">{content}</td>'


def _two_col_table(left: str, right: str, left_width: int, right_width: int) -> str:
    """Bảng hai cột KHÔNG VIỀN, có khai bề ngang cho CẢ HAI nơi đọc nó.

    `<colgroup>` là cho bản in và mọi chỗ hiển thị HTML thô: bảng để
    `table-layout: fixed`, thiếu colgroup là trình duyệt chia đều 50/50 và
    "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" gãy làm hai dòng — đã thấy tận mắt.
    `colwidth` trên ô là cho trình soạn thảo. Khai cả hai thì hai nơi vẽ giống
    nhau, không nơi nào phải đoán.
    """
    return (f'<table><colgroup><col style="width: {left_width}px">'
            f'<col style="width: {right_width}px"></colgroup><tbody><tr>'
            + _o(left, left_width) + _o(right, right_width)
            + "</tr></tbody></table>")


def _centered(content: str) -> str:
    return f'<p style="text-align:center">{content}</p>'


def opening_block(agency_name: str, issue_number: str, place_and_date: str) -> str:
    """Khối đầu hai cột: cơ quan · số ký hiệu ‖ quốc hiệu · tiêu ngữ · ngày.

    Ba tham số nhận thẳng chuỗi (kể cả mã `{{PHAP_NHAN}}`, `{{SO_HIEU}}`,
    `{{NGAY}}` để thay lúc nạp) — hàm này không biết gì về dữ liệu.
    """
    left = _centered(f"<strong>{agency_name}</strong>") + _centered(f"Số: {issue_number}")
    right = (
        _centered("<strong>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</strong>")
        + _centered("<strong>Độc lập - Tự do - Hạnh phúc</strong>")
        + _DIVIDER_LINE
        + _centered(f"<em>{place_and_date}</em>")
    )
    return _two_col_table(left, right, COL_LEFT_PX, COL_RIGHT_PX)


def title_block(type_name: str, subject: str = "") -> str:
    """Tên loại văn bản + trích yếu, cùng căn giữa."""
    title = _centered(f"<strong>{type_name}</strong>")
    return title + (_centered(f"<em>{subject}</em>") if subject else "")


def single_signature_block(job_title: str, full_name: str = "") -> str:
    """Khối chữ ký một bên, nằm bên phải như văn bản thường gặp."""
    title = f'<p style="text-align:right"><strong>{full_name}</strong></p>' if full_name else \
        '<p style="text-align:right">……………………………</p>'
    return (f'<p style="text-align:right"><strong>{job_title}</strong></p>'
            '<p style="text-align:right"><em>(Ký, ghi rõ họ tên, đóng dấu)</em></p>'
            '<p style="text-align:right">&nbsp;</p>'
            + title)


def dual_signature_block(left_title: str, right_title: str) -> str:
    """Hai khối ký đứng cạnh nhau — biên bản luôn cần (thư ký ‖ chủ trì)."""
    def _one_side(job_title: str) -> str:
        return (_centered(f"<strong>{job_title}</strong>")
                + _centered("<em>(Ký, ghi rõ họ tên)</em>")
                + _centered("&nbsp;")
                + _centered("&nbsp;")
                + _centered("……………………………"))

    #  Hai khối ký chia đôi trang, khác khối đầu (cơ quan hẹp, quốc hiệu rộng).
    return _two_col_table(_one_side(left_title), _one_side(right_title),
                         SIGN_LEFT_PX, SIGN_RIGHT_PX)


def recipients_block(*places: str, archive_note: str = "Lưu: VT, ………") -> str:
    """Khối «Nơi nhận» — phần không ai được quên ở văn bản gửi ra ngoài."""
    return ("<p><strong>Nơi nhận:</strong></p><ul>"
            + "".join(f"<li>{n};</li>" for n in places)
            + f"<li>{archive_note}</li></ul>")
