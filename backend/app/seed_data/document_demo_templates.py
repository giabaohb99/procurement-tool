"""THƯ VIỆN VĂN BẢN MẪU — khung trắng để người soạn bắt đầu, không phải văn bản thật.

Khác `document_demo_content.py` ở đúng một điểm nhưng là điểm quyết định: bên đó
là văn bản **đã ban hành**, có số hiệu, có người ký; còn đây là **tờ mẫu** —
mọi chỗ phải điền để dấu chấm lửng, không gán sẵn tên người, không gán số hiệu.

Gán sẵn thì người soạn quên xóa và văn bản ra đời mang tên một người không liên
quan — lỗi này ngoài đời hay xảy ra và rất khó nhận ra khi đọc lướt.

Mỗi mẫu gắn với MỘT loại văn bản: form tạo văn bản lọc mẫu theo loại đang chọn.
"""

_DAU_MAU = (
    '<p style="text-align:center"><strong>{{PHAP_NHAN}}</strong></p>'
    '<p style="text-align:center"><strong>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</strong></p>'
    '<p style="text-align:center"><strong>Độc lập - Tự do - Hạnh phúc</strong></p>'
    '<p style="text-align:center">———————</p>'
    '<p style="text-align:center">Số: ……/……/…… </p>'
    '<p style="text-align:right"><em>…………, ngày …… tháng …… năm 20……</em></p>'
)


def _mau(ten_loai: str, trich_yeu_goi_y: str, than: str, ky: str) -> str:
    return (
        _DAU_MAU
        + f'<p style="text-align:center"><strong>{ten_loai}</strong></p>'
        + f'<p style="text-align:center"><em>{trich_yeu_goi_y}</em></p>'
        + than
        + '<p><strong>Nơi nhận:</strong></p><ul>'
          '<li>Như trên;</li><li>………………;</li>'
          '<li>Lưu: VT, ………</li></ul>'
        + f'<p style="text-align:right"><strong>{ky}</strong></p>'
          '<p style="text-align:right"><em>(Ký, ghi rõ họ tên, đóng dấu)</em></p>'
          '<p style="text-align:right">&nbsp;</p>'
          '<p style="text-align:right">……………………………</p>'
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
     "Khung biên bản: thời gian, thành phần, nội dung thảo luận và kết luận.",
     _mau("BIÊN BẢN", "Họp về việc ……………………………………",
          "<p><strong>Thời gian:</strong> ……… giờ ………, ngày ……/……/………</p>"
          "<p><strong>Địa điểm:</strong> ………………………………………</p>"
          "<p><strong>Thành phần tham dự:</strong></p>"
          "<ul><li>Chủ trì: ………………………;</li>"
          "<li>Thành viên: ………………………;</li>"
          "<li>Thư ký: ………………………</li></ul>"
          "<p><strong>Nội dung:</strong> ………………………………………</p>"
          "<p><strong>Ý kiến thảo luận:</strong> ………………………………</p>"
          "<p><strong>Kết luận:</strong> ………………………………………</p>"
          "<p>Biên bản được đọc lại trước cuộc họp và nhất trí thông qua./.</p>"
          "<p><strong>THƯ KÝ</strong> — ………………………</p>",
          "CHỦ TRÌ CUỘC HỌP")),

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
