"""NỘI DUNG SOẠN THẢO của bộ văn bản mẫu — HTML cho trình soạn thảo.

Tách riêng khỏi `document_demo_corpus.py` (bên đó khai *quan hệ* giữa các văn
bản) vì đây thuần là **văn bản dài**: mỗi mục là một tờ văn bản hoàn chỉnh, có
đủ thể thức từ khối đầu tới chữ ký. Tệp dài là đương nhiên — chẻ nhỏ thì một tờ
văn bản nằm ở hai chỗ, sửa một câu phải mở hai tệp.

Thể thức theo Nghị định 30/2020/NĐ-CP: khối tên cơ quan + quốc hiệu, số ký
hiệu, địa danh ngày tháng, tên loại và trích yếu, nội dung, **Nơi nhận** và
khối chữ ký. Bỏ bất kỳ khối nào trong số đó là tờ giấy không dùng được ngoài
đời — mà bộ mẫu này chính là để cho thấy hình hài văn bản thật.

Ba mã được thay lúc nạp (xem `_Xuong._thay_the_ma`): `{{SO_HIEU}}`, `{{NGAY}}`,
`{{PHAP_NHAN}}` — số hiệu in trên giấy phải đúng số hệ thống đã cấp.

Trình soạn thảo (tiptap) nhận `h2/h3/p/ul/ol/table/strong/em` và
`style="text-align:…"`; không dùng thẻ ngoài danh sách đó vì sẽ bị lọc khi lưu.
"""

from . import document_the_thuc as the_thuc


def _dau(ten_loai: str, trich_yeu: str = "") -> str:
    """Khối đầu văn bản HAI CỘT + tên loại — thể thức chung ở `document_the_thuc`."""
    return (the_thuc.khoi_dau("{{PHAP_NHAN}}", "{{SO_HIEU}}", "Hà Nội, {{NGAY}}")
            + the_thuc.khoi_ten_loai(ten_loai, trich_yeu))


def _noi_nhan(*noi: str) -> str:
    """Khối «Nơi nhận» — phần không ai được quên ở văn bản gửi ra ngoài."""
    return the_thuc.khoi_noi_nhan(*noi, luu="Lưu: VT, Ban Hành chính.")


def _ky(chuc_vu: str, ho_ten: str = "Nguyễn Văn A") -> str:
    """Khối chữ ký: chức vụ, khoảng trống ký tay, họ tên."""
    return the_thuc.khoi_ky_mot_ben(chuc_vu, ho_ten)


def _bang(tieu_de: list[str], *hang: list[str]) -> str:
    """Bảng có hàng tiêu đề — dùng cho biểu mẫu và phụ lục."""
    dau = "<tr>" + "".join(f"<th><p>{c}</p></th>" for c in tieu_de) + "</tr>"
    than = "".join(
        "<tr>" + "".join(f"<td><p>{c}</p></td>" for c in h) + "</tr>" for h in hang)
    return f"<table><tbody>{dau}{than}</tbody></table>"


CHINH_SACH = _dau("CHÍNH SÁCH QUẢN TRỊ NỘI BỘ") + """
<h3>I. MỤC TIÊU</h3>
<p>Chính sách này xác lập khung nguyên tắc quản trị thống nhất trong toàn Tập
đoàn, làm căn cứ ban hành các quy chế, quy định và quy trình nội bộ; bảo đảm
mọi hoạt động điều hành đều rõ thẩm quyền, rõ trách nhiệm và có thể truy vết.</p>
<h3>II. NGUYÊN TẮC QUẢN TRỊ</h3>
<ol>
<li><strong>Đúng thẩm quyền.</strong> Mỗi quyết định phải do đúng cấp có thẩm
quyền ban hành. Việc ký thay, ký thừa lệnh chỉ thực hiện khi có văn bản ủy
quyền còn hiệu lực.</li>
<li><strong>Một việc một đầu mối.</strong> Mỗi nhiệm vụ có một đơn vị chủ trì
chịu trách nhiệm cuối cùng; các đơn vị khác phối hợp.</li>
<li><strong>Lưu vết đầy đủ.</strong> Mọi văn bản quản trị đều được lập, trình
ký, ban hành và lưu trữ trên hệ thống; không ban hành văn bản ngoài hệ thống.</li>
<li><strong>Công khai trong phạm vi áp dụng.</strong> Văn bản phải đến được
người có nghĩa vụ thực hiện; phạm vi áp dụng khai rõ ngay khi ban hành.</li>
<li><strong>Kế thừa và cập nhật.</strong> Văn bản mới thay thế văn bản cũ phải
nêu rõ văn bản bị thay thế, tránh hai văn bản cùng hiệu lực điều chỉnh một
việc.</li>
</ol>
<h3>III. TỔ CHỨC THỰC HIỆN</h3>
<p>Ban Hành chính là đầu mối hướng dẫn, theo dõi việc thực hiện Chính sách này
và định kỳ hằng năm rà soát, đề xuất sửa đổi cho phù hợp thực tiễn.</p>
<p>Trưởng các đơn vị, người đứng đầu pháp nhân thành viên chịu trách nhiệm phổ
biến và tổ chức thực hiện trong phạm vi quản lý của mình.</p>
""" + _noi_nhan("Các đơn vị trực thuộc", "Các pháp nhân thành viên",
                "Hội đồng quản trị (để báo cáo)") + _ky("TỔNG GIÁM ĐỐC", "Trần Minh Quang")

QUYET_DINH = _dau("QUYẾT ĐỊNH", "Về việc ban hành Quy chế công tác văn thư, lưu trữ") + """
<h3>TỔNG GIÁM ĐỐC</h3>
<p><em>Căn cứ</em> Điều lệ tổ chức và hoạt động của Tập đoàn;</p>
<p><em>Căn cứ</em> Nghị định số 30/2020/NĐ-CP ngày 05/3/2020 của Chính phủ về
công tác văn thư;</p>
<p><em>Căn cứ</em> Chính sách quản trị nội bộ Tập đoàn;</p>
<p><em>Xét</em> đề nghị của Trưởng ban Hành chính,</p>
<h3>QUYẾT ĐỊNH:</h3>
<p><strong>Điều 1.</strong> Ban hành kèm theo Quyết định này Quy chế công tác
văn thư, lưu trữ của Tập đoàn.</p>
<p><strong>Điều 2.</strong> Quyết định này có hiệu lực kể từ ngày ký. Bãi bỏ
Quyết định số 01/2024/QĐ-DEGO và các quy định trước đây trái với Quy chế ban
hành kèm theo Quyết định này.</p>
<p><strong>Điều 3.</strong> Trưởng ban Hành chính, trưởng các đơn vị và người
đứng đầu các pháp nhân thành viên chịu trách nhiệm thi hành Quyết định này./.</p>
""" + _noi_nhan("Như Điều 3 (để thực hiện)", "Hội đồng quản trị (để báo cáo)",
                "Các pháp nhân thành viên") + _ky("TỔNG GIÁM ĐỐC", "Trần Minh Quang")

QUYET_DINH_CU = _dau("QUYẾT ĐỊNH",
                     "Về việc ban hành Quy chế công tác văn thư năm 2024") + """
<h3>TỔNG GIÁM ĐỐC</h3>
<p><em>Căn cứ</em> Điều lệ tổ chức và hoạt động của Tập đoàn;</p>
<p><em>Xét</em> đề nghị của Trưởng ban Hành chính,</p>
<h3>QUYẾT ĐỊNH:</h3>
<p><strong>Điều 1.</strong> Ban hành kèm theo Quyết định này Quy chế công tác
văn thư năm 2024.</p>
<p><strong>Điều 2.</strong> Quyết định này có hiệu lực kể từ ngày ký.</p>
<p><strong>Điều 3.</strong> Trưởng các đơn vị chịu trách nhiệm thi hành./.</p>
<p><em>(Văn bản này đã được thay thế — giữ lại để tra cứu lịch sử.)</em></p>
""" + _noi_nhan("Như Điều 3", "Hội đồng quản trị (để báo cáo)") + _ky(
    "TỔNG GIÁM ĐỐC", "Trần Minh Quang")

QUY_CHE_BAN_1 = _dau("QUY CHẾ", "Công tác văn thư, lưu trữ") + """
<p style="text-align:center"><em>(Ban hành kèm theo Quyết định của Tổng Giám đốc)</em></p>
<h3>Chương I. QUY ĐỊNH CHUNG</h3>
<p><strong>Điều 1. Phạm vi điều chỉnh và đối tượng áp dụng</strong></p>
<p>Quy chế này quy định công tác văn thư, lưu trữ tại công ty mẹ và các pháp
nhân thành viên, gồm: soạn thảo, ký ban hành, quản lý văn bản, lập hồ sơ và
nộp lưu hồ sơ vào lưu trữ cơ quan.</p>
<p><strong>Điều 2. Nguyên tắc</strong></p>
<p>Văn bản chỉ có hiệu lực sau khi được người có thẩm quyền ký ban hành và được
cấp số trên hệ thống. Không sử dụng văn bản chưa cấp số để giao dịch./.</p>
""" + _ky("TỔNG GIÁM ĐỐC", "Trần Minh Quang")

QUY_CHE_BAN_2 = _dau("QUY CHẾ", "Công tác văn thư, lưu trữ") + """
<p style="text-align:center"><em>(Ban hành kèm theo Quyết định của Tổng Giám đốc
— bản sửa đổi lần 1)</em></p>
<h3>Chương I. QUY ĐỊNH CHUNG</h3>
<p><strong>Điều 1. Phạm vi điều chỉnh và đối tượng áp dụng</strong></p>
<p>Quy chế này quy định công tác văn thư, lưu trữ tại công ty mẹ và các pháp
nhân thành viên, gồm: soạn thảo, ký ban hành, quản lý văn bản, lập hồ sơ và
nộp lưu hồ sơ vào lưu trữ cơ quan.</p>
<p><strong>Điều 2. Thể thức và kỹ thuật trình bày</strong></p>
<p>Văn bản hành chính được trình bày theo Nghị định số 30/2020/NĐ-CP. Chi tiết
khổ giấy, phông chữ, canh lề thực hiện theo Hướng dẫn thể thức và kỹ thuật
trình bày văn bản của Tập đoàn.</p>
<h3>Chương II. SOẠN THẢO VÀ BAN HÀNH</h3>
<p><strong>Điều 3. Cấp số văn bản</strong></p>
<p>Số hiệu văn bản do hệ thống cấp tự động tại thời điểm văn bản được ký ban
hành, theo quy tắc đánh số đang có hiệu lực. Nghiêm cấm cấp số thủ công, cấp
số lùi ngày hoặc để trống số hiệu trên văn bản đã phát hành.</p>
<p><strong>Điều 4. Trách nhiệm của đơn vị soạn thảo</strong></p>
<ul>
<li>Chịu trách nhiệm về nội dung, tính chính xác của số liệu trích dẫn;</li>
<li>Lấy ý kiến các đơn vị liên quan trước khi trình ký;</li>
<li>Khai đúng phạm vi áp dụng để văn bản đến được người phải thực hiện.</li>
</ul>
<h3>Chương III. LẬP HỒ SƠ VÀ NỘP LƯU</h3>
<p><strong>Điều 5. Thời hạn nộp lưu</strong></p>
<p>Hồ sơ công việc được nộp lưu vào lưu trữ cơ quan trong thời hạn 01 năm kể từ
ngày công việc kết thúc. Hồ sơ nộp lưu phải đủ thành phần, có mục lục văn bản
và bản kê nộp lưu.</p>
<p><strong>Điều 6. Bảo quản và khai thác</strong></p>
<p>Tài liệu thuộc độ MẬT trở lên chỉ được khai thác trên hệ thống, có ghi nhận
người xem; không sao chụp, không gửi ra ngoài khi chưa được người có thẩm
quyền cho phép.</p>
<p><strong>Điều 7. Bản riêng của pháp nhân thành viên</strong></p>
<p>Pháp nhân thành viên có đặc thù riêng được tách bản riêng trên cơ sở bản gốc,
mang số hiệu của chính pháp nhân đó. Khi bản gốc lên phiên bản mới, pháp nhân
thành viên có trách nhiệm rà soát bản riêng trong thời hạn 30 ngày./.</p>
""" + _ky("TỔNG GIÁM ĐỐC", "Trần Minh Quang")

QUY_TRINH = _dau("QUY TRÌNH", "Soạn thảo và ban hành văn bản") + """
<p><em>Cụ thể hóa Chương II Quy chế công tác văn thư, lưu trữ.</em></p>
<h3>1. Bảng tóm tắt</h3>
""" + _bang(
    ["Bước", "Nội dung", "Đơn vị thực hiện", "Thời hạn"],
    ["1", "Đề xuất, phân công soạn thảo", "Đơn vị phát sinh nhu cầu", "01 ngày"],
    ["2", "Soạn thảo, lấy ý kiến", "Người được phân công", "03 ngày"],
    ["3", "Kiểm tra thể thức, trình ký", "Ban Hành chính", "01 ngày"],
    ["4", "Ký ban hành, cấp số", "Người có thẩm quyền", "01 ngày"],
    ["5", "Phát hành, vào sổ", "Văn thư", "Trong ngày"],
    ["6", "Lập hồ sơ, nộp lưu", "Đơn vị chủ trì", "01 năm"],
) + """
<h3>2. Diễn giải các bước</h3>
<p><strong>Bước 1. Đề xuất và phân công soạn thảo.</strong> Đơn vị phát sinh nhu
cầu đề xuất bằng phiếu trình. Lãnh đạo đơn vị phân công người soạn thảo và ấn
định thời hạn hoàn thành.</p>
<p><strong>Bước 2. Soạn thảo và lấy ý kiến.</strong> Người soạn thảo dự thảo
trên hệ thống, gửi lấy ý kiến các đơn vị liên quan. Ý kiến góp ý ghi trực tiếp
trên bản dự thảo; không tiếp thu thì nêu rõ lý do. Văn bản khẩn rút thời hạn
góp ý còn 01 ngày làm việc.</p>
<p><strong>Bước 3. Kiểm tra thể thức và trình ký.</strong> Ban Hành chính kiểm
tra thể thức, kỹ thuật trình bày và tính đầy đủ của hồ sơ trình ký.</p>
<p><strong>Bước 4. Ký ban hành và cấp số.</strong> Số hiệu cấp tự động tại thời
điểm ký; văn bản chuyển sang hiệu lực theo ngày ghi trên văn bản.</p>
<p><strong>Bước 5. Phát hành.</strong> Văn thư phát hành tới các đơn vị thuộc
phạm vi áp dụng và vào sổ văn bản đi.</p>
<p><strong>Bước 6. Lập hồ sơ và nộp lưu.</strong> Đơn vị chủ trì lập hồ sơ công
việc, nộp lưu theo Điều 5 Quy chế./.</p>
""" + _ky("TỔNG GIÁM ĐỐC", "Trần Minh Quang")

HUONG_DAN = _dau("HƯỚNG DẪN", "Thể thức và kỹ thuật trình bày văn bản") + """
<p><em>Hướng dẫn Bước 3 của Quy trình soạn thảo và ban hành văn bản.</em></p>
<h3>1. Khổ giấy, kiểu trình bày</h3>
<p>Khổ A4 (210mm x 297mm), trình bày theo chiều dài của khổ giấy. Văn bản có
bảng biểu lớn được trình bày theo chiều rộng.</p>
<h3>2. Phông chữ, cỡ chữ và canh lề</h3>
""" + _bang(
    ["Thành phần", "Phông, cỡ chữ", "Ghi chú"],
    ["Quốc hiệu, tiêu ngữ", "Times New Roman 12–13, in đậm", "Canh giữa"],
    ["Tên loại văn bản", "Times New Roman 13–14, in hoa đậm", "Canh giữa"],
    ["Trích yếu nội dung", "Times New Roman 13–14, in nghiêng", "Dưới tên loại"],
    ["Nội dung", "Times New Roman 13–14", "Canh đều hai bên"],
    ["Số trang", "Times New Roman 13–14", "Giữa lề trên, bỏ trang 1"],
) + """
<p>Canh lề: trên 20–25mm, dưới 20–25mm, trái 30–35mm, phải 15–20mm.</p>
<h3>3. Các lỗi thường gặp khi trình ký</h3>
<ul>
<li>Thiếu trích yếu hoặc trích yếu không phản ánh đúng nội dung;</li>
<li>Thiếu khối «Nơi nhận» ở văn bản gửi ra ngoài;</li>
<li>Viện dẫn văn bản đã hết hiệu lực;</li>
<li>Ghi số hiệu thủ công trên bản thảo trước khi ký;</li>
<li>Thiếu dấu «./.» kết thúc nội dung./.</li>
</ul>
""" + _ky("TL. TỔNG GIÁM ĐỐC<br/>TRƯỞNG BAN HÀNH CHÍNH", "Phạm Thị Bích")

BIEU_MAU_TRINH_KY = _dau("PHIẾU TRÌNH KÝ VĂN BẢN") + """
<p>Đơn vị trình: ………………………………………  Ngày trình: ……/……/………</p>
<p>Tên văn bản trình ký: ………………………………………………………………</p>
<h3>1. Nội dung trình</h3>
<p>………………………………………………………………………………………</p>
<h3>2. Hồ sơ kèm theo</h3>
""" + _bang(
    ["TT", "Thành phần hồ sơ", "Số lượng", "Có / Không"],
    ["1", "Bản thảo văn bản", "01", ""],
    ["2", "Văn bản là căn cứ ban hành", "", ""],
    ["3", "Ý kiến của các đơn vị liên quan", "", ""],
    ["4", "Tài liệu khác (ghi rõ)", "", ""],
) + """
<h3>3. Ý kiến kiểm tra thể thức</h3>
<p>Ban Hành chính: ……………………………………………………………………</p>
<h3>4. Ý kiến người có thẩm quyền</h3>
<p>………………………………………………………………………………………</p>
""" + _ky("NGƯỜI CÓ THẨM QUYỀN KÝ", "……………………")

BIEU_MAU_SO_DI = _dau("SỔ ĐĂNG KÝ VĂN BẢN ĐI") + """
<p>Năm: …………  Đơn vị: ………………………………  Quyển số: ………</p>
""" + _bang(
    ["Số, ký hiệu", "Ngày VB", "Tên loại và trích yếu", "Người ký", "Nơi nhận",
     "SL bản", "Ghi chú"],
    ["01/2026/CV-NSHC-DEGO", "05/01/2026",
     "Công văn hướng dẫn nộp lưu hồ sơ năm 2025", "Trần Minh Quang",
     "Các đơn vị trực thuộc", "12", ""],
    ["02/2026/TB-NSHC-DEGO", "18/02/2026",
     "Thông báo lịch trực dịp nghỉ lễ", "Phạm Thị Bích",
     "Các đơn vị, pháp nhân thành viên", "15", "Khẩn"],
    ["……", "……", "……", "……", "……", "……", "……"],
) + """
<h3>Hướng dẫn ghi sổ</h3>
<ul>
<li>Ghi ngay sau khi văn bản được ký ban hành, không ghi gộp cuối ngày;</li>
<li>Văn bản mật đăng ký vào sổ riêng theo Quy định về độ mật;</li>
<li>Cột «Ghi chú» dùng ghi độ khẩn, văn bản thu hồi hoặc đính chính./.</li>
</ul>
""" + _ky("TRƯỞNG BAN HÀNH CHÍNH", "Phạm Thị Bích")

QUY_DINH_MAT = _dau("QUY ĐỊNH", "Về độ mật và thời hạn bảo quản hồ sơ") + """
<p><strong>Điều 1. Phạm vi áp dụng</strong></p>
<p>Quy định này áp dụng cho toàn bộ tài liệu hình thành trong hoạt động của Tập
đoàn, kể cả tài liệu điện tử trên hệ thống.</p>
<p><strong>Điều 2. Phân loại độ mật và thời hạn bảo quản</strong></p>
""" + _bang(
    ["Nhóm tài liệu", "Độ mật", "Thời hạn bảo quản"],
    ["Thông cáo, thông báo tuyển dụng, hồ sơ năng lực", "Công khai", "01 năm"],
    ["Quy trình tác nghiệp, biểu mẫu, thông báo điều hành", "Nội bộ", "05 năm"],
    ["Hồ sơ nhân sự, hợp đồng, số liệu tài chính chưa công bố", "Mật", "10 năm"],
    ["Phương án tái cấu trúc, hồ sơ mua bán sáp nhập", "Tuyệt mật", "Vĩnh viễn"],
    ["Điều lệ, quyết định thành lập, giấy phép", "Nội bộ", "Vĩnh viễn"],
) + """
<p><strong>Điều 3. Khai thác tài liệu mật</strong></p>
<p>Tài liệu từ độ MẬT trở lên chỉ được xem trên hệ thống, có ghi nhận người xem
và thời điểm xem. Việc sao chụp, gửi ra ngoài phải được Tổng Giám đốc đồng ý
bằng văn bản.</p>
<p><strong>Điều 4. Trách nhiệm</strong></p>
<p>Trưởng các đơn vị xác định độ mật ngay khi lập hồ sơ; Ban Hành chính kiểm tra
và điều chỉnh khi tiếp nhận nộp lưu./.</p>
""" + _noi_nhan("Các đơn vị trực thuộc", "Các pháp nhân thành viên") + _ky(
    "TỔNG GIÁM ĐỐC", "Trần Minh Quang")

CONG_VAN_NOP_LUU = _dau("CÔNG VĂN", "V/v hướng dẫn nộp lưu hồ sơ năm 2025") + """
<p><strong>Kính gửi:</strong> Các đơn vị trực thuộc Tập đoàn.</p>
<p>Thực hiện Điều 5 Quy chế công tác văn thư, lưu trữ, Ban Hành chính đề nghị
các đơn vị triển khai nộp lưu hồ sơ công việc năm 2025 như sau:</p>
<p><strong>1. Phạm vi hồ sơ nộp lưu.</strong> Toàn bộ hồ sơ công việc đã kết
thúc trong năm 2025, gồm cả hồ sơ điện tử trên hệ thống và hồ sơ giấy còn lưu
tại đơn vị.</p>
<p><strong>2. Yêu cầu về hồ sơ.</strong></p>
<ul>
<li>Có mục lục văn bản trong hồ sơ và bản kê nộp lưu;</li>
<li>Sắp xếp theo trình tự thời gian, loại bỏ bản trùng và bản nháp;</li>
<li>Ghi rõ thời hạn bảo quản theo Quy định về độ mật.</li>
</ul>
<p><strong>3. Thời hạn và đầu mối.</strong> Hoàn thành trước ngày 31/3/2026.
Đầu mối tiếp nhận: Ban Hành chính (bộ phận Lưu trữ), số máy lẻ 108.</p>
<p>Trân trọng đề nghị các đơn vị phối hợp thực hiện./.</p>
""" + _noi_nhan("Như trên", "Tổng Giám đốc (để báo cáo)") + _ky(
    "TL. TỔNG GIÁM ĐỐC<br/>TRƯỞNG BAN HÀNH CHÍNH", "Phạm Thị Bích")

THONG_BAO_TRUC = _dau("THÔNG BÁO",
                      "Về lịch trực và phân công xử lý văn bản dịp nghỉ lễ") + """
<p>Ban Hành chính thông báo lịch trực và đầu mối xử lý văn bản trong thời gian
nghỉ lễ như sau:</p>
<p><strong>1. Thời gian nghỉ.</strong> Toàn Tập đoàn nghỉ theo lịch chung; bộ
phận trực bảo đảm quân số tối thiểu.</p>
<p><strong>2. Phân công trực.</strong></p>
""" + _bang(
    ["Ca trực", "Bộ phận", "Đầu mối", "Số liên hệ"],
    ["Trực lãnh đạo", "Ban Tổng Giám đốc", "Theo lịch phân công", "—"],
    ["Trực văn thư", "Ban Hành chính", "Chuyên viên văn thư", "Máy lẻ 108"],
    ["Trực kỹ thuật", "Phòng CNTT", "Trực hệ thống", "Máy lẻ 115"],
) + """
<p><strong>3. Xử lý văn bản khẩn, hỏa tốc.</strong> Văn bản đến có độ khẩn phải
được chuyển tới người có thẩm quyền ngay khi tiếp nhận, không chờ hết kỳ nghỉ.
Trường hợp không liên hệ được, báo cáo Trưởng ban Hành chính để xử lý./.</p>
""" + _noi_nhan("Các đơn vị trực thuộc", "Các pháp nhân thành viên") + _ky(
    "TL. TỔNG GIÁM ĐỐC<br/>TRƯỞNG BAN HÀNH CHÍNH", "Phạm Thị Bích")

KE_HOACH_SO_HOA = _dau("KẾ HOẠCH",
                       "Số hóa tài liệu lưu trữ giai đoạn 2026–2027") + """
<h3>I. MỤC ĐÍCH, YÊU CẦU</h3>
<p>Chuyển toàn bộ hồ sơ pháp lý và hồ sơ nhân sự đang bảo quản tại kho lưu trữ
sang dạng số, bảo đảm tra cứu nhanh, giảm hư hỏng tài liệu gốc và sẵn sàng cho
việc kiểm toán, thanh tra.</p>
<p>Tài liệu số hóa phải đọc rõ, có mục lục, gắn đúng thời hạn bảo quản và độ
mật; tài liệu gốc giữ nguyên trạng.</p>
<h3>II. NỘI DUNG VÀ TIẾN ĐỘ</h3>
""" + _bang(
    ["Giai đoạn", "Nội dung", "Đơn vị chủ trì", "Kết quả"],
    ["Quý I/2026", "Thống kê, phân loại, xác định thời hạn bảo quản",
     "Ban Hành chính", "Danh mục tài liệu"],
    ["Quý II–III/2026", "Số hóa hồ sơ pháp lý và hồ sơ nhân sự",
     "Ban Hành chính, Phòng Nhân sự", "Khoảng 40.000 trang"],
    ["Quý IV/2026", "Số hóa hồ sơ kế toán, hợp đồng kinh tế",
     "Phòng Kế toán", "Khoảng 60.000 trang"],
    ["Năm 2027", "Số hóa tài liệu còn lại, nghiệm thu",
     "Ban Hành chính", "Đưa vào khai thác"],
) + """
<h3>III. KINH PHÍ</h3>
<p>Kinh phí thực hiện lấy từ nguồn chi thường xuyên của Ban Hành chính; phần
thuê ngoài lập dự toán riêng trình Tổng Giám đốc phê duyệt.</p>
<h3>IV. TỔ CHỨC THỰC HIỆN</h3>
<p>Ban Hành chính chủ trì, phối hợp với Phòng Công nghệ thông tin và các đơn vị
có tài liệu. Định kỳ hằng quý báo cáo tiến độ về Tổng Giám đốc./.</p>
""" + _noi_nhan("Các đơn vị liên quan", "Tổng Giám đốc (để báo cáo)") + _ky(
    "TRƯỞNG BAN HÀNH CHÍNH", "Phạm Thị Bích")

TO_TRINH = _dau("TỜ TRÌNH",
                "Về việc phê duyệt Kế hoạch số hóa tài liệu lưu trữ 2026–2027") + """
<p><strong>Kính trình:</strong> Hội đồng quản trị.</p>
<p><strong>1. Sự cần thiết.</strong> Kho lưu trữ hiện quản lý khoảng 120.000
trang tài liệu giấy hình thành từ năm 2016. Việc tra cứu mất trung bình 2–3
ngày làm việc; một số tài liệu đã xuống cấp do điều kiện bảo quản.</p>
<p><strong>2. Nội dung trình.</strong> Ban Hành chính kính trình Hội đồng quản
trị xem xét, phê duyệt Kế hoạch số hóa tài liệu lưu trữ giai đoạn 2026–2027
với nội dung và tiến độ nêu tại Kế hoạch kèm theo.</p>
<p><strong>3. Kiến nghị.</strong></p>
<ul>
<li>Phê duyệt chủ trương số hóa và tiến độ theo bốn giai đoạn;</li>
<li>Cho phép thuê đơn vị chuyên môn thực hiện phần khối lượng lớn;</li>
<li>Bố trí kinh phí trong kế hoạch tài chính năm 2026.</li>
</ul>
<p>Kính trình Hội đồng quản trị xem xét, quyết định./.</p>
""" + _noi_nhan("Như trên", "Tổng Giám đốc") + _ky("TRƯỞNG BAN HÀNH CHÍNH",
                                                   "Phạm Thị Bích")

BIEN_BAN_HOP = _dau("BIÊN BẢN",
                    "Họp Hội đồng xác định giá trị tài liệu — đợt I năm 2026") + """
<p><strong>Thời gian:</strong> 09 giờ 00, tại phòng họp Ban Hành chính.</p>
<p><strong>Thành phần tham dự:</strong></p>
""" + _bang(
    ["TT", "Họ và tên", "Chức vụ", "Vai trò trong Hội đồng"],
    ["1", "Phạm Thị Bích", "Trưởng ban Hành chính", "Chủ tịch Hội đồng"],
    ["2", "Lê Quốc Hưng", "Trưởng phòng Pháp chế", "Thành viên"],
    ["3", "Ngô Thanh Hà", "Trưởng phòng Kế toán", "Thành viên"],
    ["4", "Đỗ Minh Tuấn", "Chuyên viên lưu trữ", "Thư ký"],
) + """
<p><strong>Nội dung:</strong> Hội đồng xem xét danh mục tài liệu hết thời hạn
bảo quản do bộ phận Lưu trữ trình, đối chiếu với Quy định về độ mật và thời hạn
bảo quản hồ sơ.</p>
<p><strong>Ý kiến thảo luận:</strong></p>
<ul>
<li>Phòng Pháp chế đề nghị giữ lại hồ sơ liên quan tranh chấp chưa kết thúc;</li>
<li>Phòng Kế toán đề nghị giữ thêm 02 năm với hồ sơ thuế đang trong kỳ thanh
tra.</li>
</ul>
<p><strong>Kết luận:</strong> Thống nhất trình Tổng Giám đốc phê duyệt hủy phần
tài liệu đã hết thời hạn bảo quản, trừ hai nhóm nêu trên. Bộ phận Lưu trữ hoàn
thiện danh mục trước ngày 30 của tháng.</p>
<p>Biên bản được đọc lại trước Hội đồng và nhất trí thông qua./.</p>
<p><strong>THƯ KÝ</strong> — Đỗ Minh Tuấn</p>
""" + _ky("CHỦ TỊCH HỘI ĐỒNG", "Phạm Thị Bích")

GIAY_UY_QUYEN = _dau("GIẤY ỦY QUYỀN", "Về việc ký văn bản hành chính") + """
<p><strong>Bên ủy quyền:</strong> Ông Trần Minh Quang — Tổng Giám đốc.</p>
<p><strong>Bên được ủy quyền:</strong> Bà Phạm Thị Bích — Trưởng ban Hành chính.</p>
<p><strong>1. Nội dung ủy quyền.</strong> Ký ban hành các văn bản hành chính
thông thường trong thời gian Tổng Giám đốc đi công tác, gồm: công văn trao đổi,
thông báo điều hành, giấy mời, giấy giới thiệu.</p>
<p><strong>2. Phạm vi KHÔNG được ủy quyền.</strong></p>
<ul>
<li>Quyết định về nhân sự, tiền lương;</li>
<li>Văn bản có nội dung tài chính vượt hạn mức được duyệt;</li>
<li>Văn bản thuộc độ MẬT trở lên;</li>
<li>Hợp đồng kinh tế và văn bản cam kết với bên thứ ba.</li>
</ul>
<p><strong>3. Thời hạn ủy quyền.</strong> Theo thời hạn ghi trên văn bản. Hết
thời hạn, việc ủy quyền chấm dứt mà không cần văn bản thu hồi.</p>
<p><strong>4. Trách nhiệm.</strong> Bên được ủy quyền chịu trách nhiệm trước
Tổng Giám đốc và trước pháp luật về các văn bản đã ký; báo cáo lại toàn bộ văn
bản đã ký ngay khi kết thúc thời hạn ủy quyền./.</p>
<p><strong>BÊN ĐƯỢC ỦY QUYỀN</strong> — Phạm Thị Bích</p>
""" + _ky("BÊN ỦY QUYỀN<br/>TỔNG GIÁM ĐỐC", "Trần Minh Quang")
