"""THƯ VIỆN VĂN BẢN MẪU — khung trắng để người soạn bắt đầu, không phải văn bản thật.

Khác `document_demo_content.py` ở đúng một điểm nhưng là điểm quyết định: bên đó
là văn bản **đã ban hành**, có số hiệu, có người ký; còn đây là **tờ mẫu** —
mọi chỗ phải điền để dấu chấm lửng, không gán sẵn tên người, không gán số hiệu.

Gán sẵn thì người soạn quên xóa và văn bản ra đời mang tên một người không liên
quan — lỗi này ngoài đời hay xảy ra và rất khó nhận ra khi đọc lướt.

Mỗi mẫu gắn với MỘT loại văn bản: form tạo văn bản lọc mẫu theo loại đang chọn.

Thể thức (khối đầu hai cột, khối ký) lấy từ `document_the_thuc.py` — sửa thể
thức một chỗ là cả bộ mẫu lẫn bộ văn bản demo cùng đổi theo.
"""
from . import document_the_thuc as the_thuc

#  Khối đầu HAI CỘT đúng Nghị định 30 — dựng ở `document_the_thuc.py`, dùng
#  chung với bộ văn bản demo để hai nơi không lệch thể thức.
_DAU_MAU = the_thuc.khoi_dau("{{PHAP_NHAN}}", "……/……/……",
                             "…………, ngày …… tháng …… năm 20……")


def _mau(ten_loai: str, trich_yeu_goi_y: str, than: str, ky: str) -> str:
    return (
        _DAU_MAU
        + the_thuc.khoi_ten_loai(ten_loai, trich_yeu_goi_y)
        + than
        + the_thuc.khoi_noi_nhan("Như trên", "………………")
        + the_thuc.khoi_ky_mot_ben(ky)
    )


def _bien_ban_hop() -> str:
    """BIÊN BẢN HỌP — dựng riêng, không dùng `_mau`.

    Khác mọi mẫu khác ở hai chỗ và cả hai đều đúng với biên bản ngoài đời:
    **không có khối «Nơi nhận»** (biên bản không gửi đi đâu, nó là bản ghi của
    cuộc họp), và **ký hai bên** — thư ký ghi, chủ trì xác nhận. Một chữ ký thì
    biên bản không có giá trị đối chiếu.
    """
    return (
        _DAU_MAU
        + the_thuc.khoi_ten_loai("BIÊN BẢN HỌP", "Về việc ……………………………………")
        + "<p>Hôm nay, vào lúc ……… giờ ……… ngày …… tháng …… năm ………</p>"
          "<p>Tại ………………………………………………………………………</p>"
          "<p>Diễn ra cuộc họp với nội dung ………………………………………</p>"
          "<p><strong>I. Thành phần tham dự:</strong></p>"
          "<p>1. Chủ trì: Ông/Bà ……………………………… Chức vụ: ………………</p>"
          "<p>2. Thư ký: Ông/Bà ……………………………… Chức vụ: ………………</p>"
          "<p>3. Thành phần khác:</p>"
          "<p>………………………………………………………………………………</p>"
          "<p>………………………………………………………………………………</p>"
          "<p><strong>II. Nội dung cuộc họp:</strong></p>"
          "<p>………………………………………………………………………………</p>"
          "<p>………………………………………………………………………………</p>"
          "<p><strong>III. Biểu quyết (nếu có):</strong></p>"
          "<p>- Tổng số phiếu: ………………… phiếu</p>"
          "<p>- Số phiếu tán thành: ………… phiếu, chiếm …… %</p>"
          "<p>- Số phiếu không tán thành: ………… phiếu, chiếm …… %</p>"
          "<p><strong>IV. Kết luận cuộc họp:</strong></p>"
          "<p>………………………………………………………………………………</p>"
          "<p>………………………………………………………………………………</p>"
          "<p>Cuộc họp kết thúc vào lúc …… giờ …… ngày …… tháng …… năm ………, "
          "nội dung cuộc họp đã được các thành viên dự họp thông qua và cùng ký "
          "vào biên bản./.</p>"
        + the_thuc.khoi_ky_hai_ben("THƯ KÝ", "CHỦ TRÌ CUỘC HỌP")
    )


#  (mã loại, tên mẫu, mô tả, nội dung)
VAN_BAN_MAU = [
    ("CV", "Công văn trao đổi, đề nghị",
     "Khung công văn hành chính thông thường: kính gửi, nội dung chia ý, đề nghị "
     "và thời hạn phản hồi.",
     _mau("CÔNG VĂN", "V/v ……………………………………",
          "<p><strong>Kính gửi:</strong> ………………………………………</p>"
          "<p>Căn cứ ……………………………………………………………;</p>"
          "<p>………………… (nêu bối cảnh, lý do gửi công văn) …………………</p>"
          "<p><strong>1.</strong> ………………………………………………………</p>"
          "<p><strong>2.</strong> ………………………………………………………</p>"
          "<p><strong>3.</strong> Đề nghị …………… phản hồi trước ngày ……/……/………, "
          "đầu mối liên hệ: ……………………, số máy lẻ ………</p>"
          "<p>Trân trọng./.</p>",
          "TL. TỔNG GIÁM ĐỐC<br/>TRƯỞNG BAN ………………")),

    ("QD", "Quyết định ban hành văn bản nội bộ",
     "Khung quyết định có phần căn cứ, các điều khoản ban hành, hiệu lực và "
     "trách nhiệm thi hành.",
     _mau("QUYẾT ĐỊNH", "Về việc ……………………………………",
          "<h3>TỔNG GIÁM ĐỐC</h3>"
          "<p><em>Căn cứ</em> Điều lệ tổ chức và hoạt động của ………………;</p>"
          "<p><em>Căn cứ</em> ……………………………………………………………;</p>"
          "<p><em>Xét</em> đề nghị của ……………………………,</p>"
          "<h3>QUYẾT ĐỊNH:</h3>"
          "<p><strong>Điều 1.</strong> ………………………………………………</p>"
          "<p><strong>Điều 2.</strong> Quyết định này có hiệu lực kể từ ngày ký. "
          "Bãi bỏ ………………………………………………</p>"
          "<p><strong>Điều 3.</strong> ……………… chịu trách nhiệm thi hành Quyết "
          "định này./.</p>",
          "TỔNG GIÁM ĐỐC")),

    ("TB", "Thông báo điều hành",
     "Khung thông báo nội bộ: nội dung thông báo, phân công thực hiện và thời "
     "hạn áp dụng.",
     _mau("THÔNG BÁO", "Về việc ……………………………………",
          "<p>……………… (đơn vị) thông báo tới các đơn vị nội dung sau:</p>"
          "<p><strong>1. Nội dung thông báo.</strong> …………………………………</p>"
          "<p><strong>2. Thời gian áp dụng.</strong> Từ ngày ……/……/……… đến "
          "ngày ……/……/………</p>"
          "<p><strong>3. Phân công thực hiện.</strong> ………………………………</p>"
          "<p>Đề nghị các đơn vị nghiêm túc thực hiện./.</p>",
          "TL. TỔNG GIÁM ĐỐC<br/>TRƯỞNG BAN ………………")),

    ("TTR", "Tờ trình phê duyệt",
     "Khung tờ trình: sự cần thiết, nội dung trình và kiến nghị cụ thể.",
     _mau("TỜ TRÌNH", "Về việc ……………………………………",
          "<p><strong>Kính trình:</strong> ………………………………………</p>"
          "<p><strong>1. Sự cần thiết.</strong> ………………………………………</p>"
          "<p><strong>2. Nội dung trình.</strong> ………………………………………</p>"
          "<p><strong>3. Kiến nghị.</strong></p>"
          "<ul><li>………………………………;</li><li>………………………………;</li>"
          "<li>………………………………</li></ul>"
          "<p>Kính trình ……………… xem xét, quyết định./.</p>",
          "TRƯỞNG ĐƠN VỊ TRÌNH")),

    ("BB", "Biên bản họp",
     "Khung biên bản họp thông dụng: thời gian địa điểm, thành phần tham dự, "
     "nội dung, biểu quyết và kết luận; ký hai bên thư ký — chủ trì.",
     _bien_ban_hop()),

    ("KH", "Kế hoạch triển khai",
     "Khung kế hoạch bốn phần: mục đích yêu cầu, nội dung và tiến độ, kinh phí, "
     "tổ chức thực hiện.",
     _mau("KẾ HOẠCH", "……………………………………",
          "<h3>I. MỤC ĐÍCH, YÊU CẦU</h3><p>………………………………………</p>"
          "<h3>II. NỘI DUNG VÀ TIẾN ĐỘ</h3>"
          "<table><tbody>"
          "<tr><th><p>Giai đoạn</p></th><th><p>Nội dung</p></th>"
          "<th><p>Đơn vị chủ trì</p></th><th><p>Kết quả</p></th></tr>"
          "<tr><td><p>………</p></td><td><p>………</p></td><td><p>………</p></td>"
          "<td><p>………</p></td></tr>"
          "<tr><td><p>………</p></td><td><p>………</p></td><td><p>………</p></td>"
          "<td><p>………</p></td></tr>"
          "</tbody></table>"
          "<h3>III. KINH PHÍ</h3><p>………………………………………</p>"
          "<h3>IV. TỔ CHỨC THỰC HIỆN</h3><p>………………………………………</p>",
          "TRƯỞNG ĐƠN VỊ CHỦ TRÌ")),

    ("GM", "Giấy mời họp",
     "Khung giấy mời: nội dung, thời gian, địa điểm và đề nghị xác nhận.",
     _mau("GIẤY MỜI", "Về việc ……………………………………",
          "<p>……………… trân trọng kính mời: ………………………………</p>"
          "<p><strong>Tới dự:</strong> ………………………………………</p>"
          "<p><strong>Thời gian:</strong> ……… giờ ………, ngày ……/……/………</p>"
          "<p><strong>Địa điểm:</strong> ………………………………………</p>"
          "<p><strong>Thành phần:</strong> ………………………………………</p>"
          "<p>Đề nghị xác nhận tham dự trước ngày ……/……/……… qua đầu mối "
          "………………………, số máy lẻ ………</p>"
          "<p>Rất mong sự có mặt của quý vị./.</p>",
          "TL. TỔNG GIÁM ĐỐC<br/>TRƯỞNG BAN ………………")),

    ("QDI", "Quy định nội bộ",
     "Khung quy định theo điều khoản: phạm vi, nội dung quy định, trách nhiệm "
     "và hiệu lực thi hành.",
     _mau("QUY ĐỊNH", "Về ……………………………………",
          "<p><strong>Điều 1. Phạm vi điều chỉnh và đối tượng áp dụng</strong></p>"
          "<p>………………………………………………………………</p>"
          "<p><strong>Điều 2. Giải thích từ ngữ</strong></p>"
          "<p>………………………………………………………………</p>"
          "<p><strong>Điều 3. Nội dung quy định</strong></p>"
          "<p>………………………………………………………………</p>"
          "<p><strong>Điều 4. Trách nhiệm thi hành</strong></p>"
          "<p>………………………………………………………………</p>"
          "<p><strong>Điều 5. Hiệu lực thi hành</strong></p>"
          "<p>Quy định này có hiệu lực kể từ ngày ……/……/………./.</p>",
          "TỔNG GIÁM ĐỐC")),
]
