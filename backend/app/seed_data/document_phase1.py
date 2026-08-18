"""Dữ liệu nền Phase 1 của phân hệ Văn thư.

Danh mục 32 loại gồm 29 tên loại văn bản hành chính theo hệ thống tên gọi đang
dùng ở Việt Nam, cộng 3 loại tài liệu nội bộ DEGO: Chính sách, Quy trình và
Biểu mẫu. Sáu mã đã có trên môi trường dev (CV, QD, TB, QC, HD, BM) được giữ
nguyên để không làm lệch các văn bản đã tạo.

Loại thứ 33 TL được bổ sung theo quyết định của người dùng ngày 15/08/2026;
ba cấu hình bắt buộc lấy đúng từ C20: id_scheme=2, needs_decision=False,
number_when=2.
"""


def _doc_type(
    code: str,
    name: str,
    group_code: str,
    description: str,
    *,
    id_scheme: int = 2,
    needs_decision: bool = False,
    needs_signature: bool = True,
    review_cycle_months: int = 0,
    retention_months: int = 120,
) -> dict:
    return {
        "code": code,
        "name": name,
        "group_code": group_code,
        "description": description,
        "id_scheme": id_scheme,
        "number_when": 2,
        "default_secrecy": 2,
        "is_confidential_type": False,
        "needs_approval": True,
        "needs_signature": needs_signature,
        "needs_decision": needs_decision,
        "needs_request": False,
        "review_cycle_months": review_cycle_months,
        "retention_months": retention_months,
        "default_flow_id": 0,
        "is_active": True,
    }


# 32 loại chính thức của Phase 1. Thứ tự này cũng là sort_order trên giao diện.
OFFICIAL_DOC_TYPES = [
    # A · Tài liệu hệ thống — mã bất biến, sửa bằng phiên bản mới.
    _doc_type("CS", "Chính sách", "A", "Nguyên tắc và định hướng quản trị áp dụng lâu dài.",
              id_scheme=1, needs_decision=True, review_cycle_months=12),
    _doc_type("QC", "Quy chế", "A", "Quy chế quản lý và vận hành trong tập đoàn.",
              id_scheme=1, needs_decision=True, review_cycle_months=12),
    _doc_type("QDI", "Quy định", "A", "Quy định bắt buộc áp dụng cho một lĩnh vực hoặc hoạt động.",
              id_scheme=1, needs_decision=True, review_cycle_months=12),
    _doc_type("QT", "Quy trình", "A", "Trình tự và trách nhiệm thực hiện một công việc.",
              id_scheme=1, needs_decision=True, review_cycle_months=12),
    _doc_type("HDCV", "Hướng dẫn công việc", "A", "Hướng dẫn chi tiết cách thực hiện một bước công việc.",
              id_scheme=1, review_cycle_months=12),
    _doc_type("BM", "Biểu mẫu", "A", "Biểu mẫu chuẩn dùng kèm quy chế, quy định hoặc quy trình.",
              id_scheme=1, needs_signature=False, review_cycle_months=12),

    # B · Văn bản quản lý, chỉ đạo.
    _doc_type("NQ", "Nghị quyết", "B", "Văn bản ghi nhận quyết nghị của tập thể có thẩm quyền."),
    _doc_type("QD", "Quyết định", "B", "Quyết định cá biệt về tổ chức, nhân sự hoặc công việc."),
    _doc_type("CT", "Chỉ thị", "B", "Mệnh lệnh điều hành của người có thẩm quyền."),

    # C · Giao dịch, cam kết.
    _doc_type("HD", "Hợp đồng", "C", "Thỏa thuận có ràng buộc giữa DEGO và bên liên quan.",
              retention_months=240),
    _doc_type("BGN", "Bản ghi nhớ", "C", "Ghi nhận nội dung đã trao đổi hoặc thống nhất sơ bộ."),
    _doc_type("BTT", "Bản thỏa thuận", "C", "Ghi nhận thỏa thuận giữa các bên."),
    _doc_type("GUQ", "Giấy ủy quyền", "C", "Ủy quyền cho cá nhân hoặc đơn vị thực hiện công việc."),

    # D · Văn bản sự vụ.
    _doc_type("CV", "Công văn", "D", "Trao đổi, đề nghị hoặc trả lời giữa các đơn vị."),
    _doc_type("CD", "Công điện", "D", "Chỉ đạo hoặc thông tin cần truyền đạt khẩn."),
    _doc_type("TB", "Thông báo", "D", "Thông tin chính thức gửi tới một hoặc nhiều đối tượng.",
              needs_signature=False),
    _doc_type("TC", "Thông cáo", "D", "Thông tin chính thức công bố rộng rãi."),
    _doc_type("BC", "Báo cáo", "D", "Tổng hợp tình hình, kết quả và kiến nghị."),
    _doc_type("TTR", "Tờ trình", "D", "Trình cấp có thẩm quyền xem xét và quyết định."),
    _doc_type("BB", "Biên bản", "D", "Ghi nhận diễn biến, ý kiến hoặc kết quả một sự việc."),

    # E · Kế hoạch, chương trình và đề án.
    _doc_type("CTR", "Chương trình", "E", "Tập hợp hoạt động có mục tiêu và thời gian thực hiện."),
    _doc_type("KH", "Kế hoạch", "E", "Mục tiêu, tiến độ, nguồn lực và trách nhiệm thực hiện."),
    _doc_type("PA", "Phương án", "E", "Cách thức dự kiến để xử lý một công việc hoặc tình huống."),
    _doc_type("DAN", "Đề án", "E", "Đề xuất có phân tích, mục tiêu và giải pháp triển khai."),
    _doc_type("DUAN", "Dự án", "E", "Hồ sơ xác lập một dự án có phạm vi, nguồn lực và tiến độ."),

    # F · Giấy tờ và phiếu hành chính.
    _doc_type("GM", "Giấy mời", "F", "Mời cá nhân hoặc đơn vị tham dự sự kiện, cuộc họp."),
    _doc_type("GGT", "Giấy giới thiệu", "F", "Giới thiệu người của đơn vị đến liên hệ công tác."),
    _doc_type("GNP", "Giấy nghỉ phép", "F", "Xác nhận hoặc đề nghị nghỉ phép theo quy định.",
              needs_signature=False),
    _doc_type("PG", "Phiếu gửi", "F", "Phiếu kèm hồ sơ hoặc tài liệu được gửi đi.",
              needs_signature=False),
    _doc_type("PC", "Phiếu chuyển", "F", "Chuyển hồ sơ hoặc công việc tới đơn vị xử lý.",
              needs_signature=False),
    _doc_type("PB", "Phiếu báo", "F", "Thông báo ngắn theo mẫu phiếu hành chính.",
              needs_signature=False),
    _doc_type("THC", "Thư công", "F", "Thư giao dịch chính thức phục vụ công việc."),
]


TRICH_LUC_DOC_TYPE = _doc_type(
    "TL",
    "Trích lục",
    "F",
    "Bản trích chính thức có giá trị đối ngoại, có người ký xác nhận sao đúng với bản gốc.",
    id_scheme=2,
    needs_decision=False,
    needs_signature=True,
    review_cycle_months=0,
)

ALL_DOC_TYPES = OFFICIAL_DOC_TYPES + [TRICH_LUC_DOC_TYPE]
for _sort_order, _row in enumerate(ALL_DOC_TYPES, start=1):
    _row["sort_order"] = _sort_order


# 13 dòng theo tập dữ liệu đang có và hai pháp nhân được tài liệu B8 nêu đích danh
# nhưng còn thiếu (SAM, AGRIPLANT). Chỉ điền các trường đang trống, không ghi đè.
DOCUMENT_COMPANIES = [
    {"code": "DEGO", "name": "CÔNG TY TNHH DEGO HOLDING", "tax_code": "1801722464",
     "issue_code": "DEGO", "short_name": "DEGO Holding", "level": 1},
    {"code": "IDA", "name": "CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL", "tax_code": "0314562909",
     "issue_code": "IDA", "short_name": "IDA Global", "level": 2},
    {"code": "ABA", "name": "CÔNG TY TNHH SẢN XUẤT HÓA CHẤT ABA", "tax_code": "0316342296",
     "issue_code": "ABA", "short_name": "ABA", "level": 2},
    {"code": "DEGO HOLDING", "name": "CÔNG TY TNHH DEGO HOLDING", "tax_code": "1801722464",
     "issue_code": "DEGOHOLDING", "short_name": "DEGO Holding", "level": 1},
    {"code": "ICARE", "name": "CÔNG TY TNHH DƯỢC PHẨM ICARE", "tax_code": "0315593265",
     "issue_code": "ICARE", "short_name": "iCare", "level": 2},
    {"code": "NPP DR.XANH", "name": "NHÀ PHÂN PHỐI DR XANH", "tax_code": "578010406",
     "issue_code": "DRXANH", "short_name": "NPP Dr.Xanh", "level": 3},
    {"code": "HỘ KD DR.XANH", "name": "HỘ KINH DOANH DR XANH", "tax_code": "578005750",
     "issue_code": "HKDDRXANH", "short_name": "HKD Dr.Xanh", "level": 3},
    {"code": "BAMBOO", "name": "CÔNG TY TNHH XUẤT NHẬP KHẨU SẢN XUẤT THƯƠNG MẠI BAMBOO VIỆT NAM",
     "tax_code": "0318629897", "issue_code": "BAMBOO", "short_name": "Bamboo Việt Nam", "level": 2},
    {"code": "N2SBIO", "name": "CÔNG TY TNHH N2SBIO VIỆT NAM", "tax_code": "0318776965",
     "issue_code": "N2SBIO", "short_name": "N2SBIO", "level": 2},
    {"code": "NN DEGO", "name": "CÔNG TY TNHH SẢN XUẤT VÀ XUẤT NHẬP KHẨU HOÁ CHẤT NÔNG NGHIỆP DEGO",
     "tax_code": "0318430011", "issue_code": "NNDEGO", "short_name": "Nông nghiệp DEGO", "level": 2},
    {"code": "NN ABA", "name": "CÔNG TY TNHH HÓA CHẤT NÔNG NGHIỆP ABA", "tax_code": "1801818328",
     "issue_code": "NNABA", "short_name": "Nông nghiệp ABA", "level": 2},
    {"code": "SAM", "name": "SAM", "tax_code": "", "issue_code": "SAM",
     "short_name": "SAM", "level": 2},
    {"code": "AGRIPLANT", "name": "AGRIPLANT", "tax_code": "", "issue_code": "AGRIPLANT",
     "short_name": "AGRIPLANT", "level": 2},
]


# Mã phòng dùng trong số hiệu. kind=2 là đơn vị kinh doanh/sản xuất nên bộ ghép
# số sẽ chủ động bỏ mã dù vẫn lưu để quản trị và tra cứu.
DEPARTMENT_DOCUMENT_CONFIG = {
    "PBA001": {"issue_code": "TM", "kind": 1, "manager_employee_code": "DEMO_MANAGER_PURCHASE"},
    "PBA002": {"issue_code": "KT", "kind": 1},
    "PBA003": {"issue_code": "KD", "kind": 2},
    "PBA004": {"issue_code": "KV", "kind": 1},
    "PBA005": {"issue_code": "SX", "kind": 2},
    "PBA006": {"issue_code": "MKT", "kind": 1},
    "PBA007": {"issue_code": "NSHC", "kind": 1},
    "PBA008": {"issue_code": "CNTT", "kind": 1},
    "PBA009": {"issue_code": "BGD", "kind": 1},
}


# ── E01 · Quy tắc quan hệ cha–con, bảy dòng mẫu theo `van-thu/04` mục 4.2 ─────
#
# Khai bằng MÃ LOẠI chứ không phải id: id sinh ra lúc seed chạy, mà seed chạy
# lại mỗi lần deploy nên không ghim được số nào.
#
# Hai chỗ lệch tài liệu, cố ý, ghi rõ ở đây để lần sau đọc không tưởng là sai:
#
#   1. Dòng "bất kỳ tham chiếu bất kỳ" KHÔNG seed. `source_type_id` là cột bắt
#      buộc nên khai cho đủ 33 loại sẽ làm bảng 15–25 dòng phình gấp đôi mà
#      không thêm nghĩa. Thay vào đó `link_service` cho quan hệ «tham chiếu» đi
#      qua thẳng không cần quy tắc — nó vốn là liên kết mềm.
#   2. Tài liệu ghi "BM thuộc về QT, QC — bắt buộc, từ 1", nghĩa là bắt buộc ÍT
#      NHẤT MỘT TRONG HAI loại đích. Bảng quy tắc khóa theo từng cặp nên hai
#      dòng bắt buộc sẽ đòi CẢ HAI. Tạm để BM→QT bắt buộc, BM→QC cho phép —
#      cần Hành chính chốt lại.
DOC_TYPE_LINK_RULES = [
    # (mã nguồn, quan hệ, mã đích, bắt buộc, min, max)
    ("HDCV", 4, "QT", True, 1, 1),    # Hướng dẫn công việc hướng dẫn đúng 1 Quy trình
    ("BM", 6, "QT", True, 1, 0),      # Biểu mẫu không đứng một mình
    ("BM", 6, "QC", False, 0, 0),
    #  Bốn loại dưới đây đều khai `needs_decision` ở `ALL_DOC_TYPES`, nghĩa là
    #  không có Quyết định kèm theo thì `ensure_can_issue` từ chối ban hành.
    #  Thiếu dòng quy tắc tương ứng ở đây là khóa chết: người soạn muốn khai
    #  quan hệ «Kèm theo» tới Quyết định cũng bị bảng quy tắc chặn, nên văn bản
    #  không còn đường nào ra. Đã từng thiếu ba dòng CS · QDI · QT.
    ("QC", 5, "QD", True, 1, 1),      # Quy chế ban hành kèm 1 Quyết định
    ("CS", 5, "QD", True, 1, 1),      # Chính sách — như trên
    ("QDI", 5, "QD", True, 1, 1),     # Quy định — như trên
    ("QT", 5, "QD", True, 1, 1),      # Quy trình — như trên
    ("QDI", 7, "CS", False, 0, 0),    # Quy định căn cứ theo Chính sách — có thì tốt
    ("QD", 1, "QD", False, 0, 0),     # Quyết định mới thay quyết định cũ
    ("QT", 7, "CS", False, 0, 0),     # Quy trình căn cứ theo Chính sách
]
