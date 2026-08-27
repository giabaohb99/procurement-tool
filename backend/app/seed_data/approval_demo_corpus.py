"""NỘI DUNG bộ luồng duyệt + quy tắc đánh số mẫu.

Đường ký một văn bản ở cơ quan nhà nước phụ thuộc vào **loại** và **độ mật**
của nó, nên bộ mẫu dựng ba luồng cho văn bản chứ không phải một:

  * quy chế · quy định · quy trình → qua pháp chế và tài chính, rồi mới tới
    người ký; văn bản MẬT thì đích thân Tổng Giám đốc ký;
  * công văn · thông báo · giấy mời → trưởng phòng duyệt, chánh văn phòng ký;
  * còn lại → luồng mặc định hai bước.

Luồng có điều kiện được xét TRƯỚC luồng mặc định (`flow_service.chon_luong`),
nên luồng mặc định cố ý để trống điều kiện và ưu tiên thấp nhất.
"""
import json

from app.modules.approval.flow_model import (APPROVER_DEPT_HEAD,
                                             APPROVER_DEPT_HEAD_OF,
                                             APPROVER_EMPLOYEE, MULTI_ALL,
                                             NODE_CC, ROLE_CHECK,
                                             ROLE_EXECUTE)

#  Mức mật 3 = MẬT. Xem `security-level.ts` phía giao diện và cột
#  `secrecy_level` trên `tab_document`.
SECRET_LEVEL = 3


def _condition_confidential_from_level_3() -> str:
    return json.dumps([{"field": "secrecy_level", "op": "gte", "value": SECRET_LEVEL}])


def build_flows(x, people) -> list:
    """Ba luồng cho văn bản + một luồng cho đơn mua hàng."""
    out = []

    # ── 1. Văn bản quản trị: quy chế, quy định, quy trình, chính sách ────────
    governance_flow = x.flow(
        "document", "VB_QUAN_TRI", "Ban hành văn bản quản trị",
        "Quy chế, quy định, quy trình, chính sách — phải qua pháp chế và tài "
        "chính trước khi trình ký.",
        condition=x.type_condition("QC", "QDI", "QT", "CS"), priority=20)
    x.step(governance_flow, 1, "Trưởng bộ phận soạn thảo rà soát",
           ai=APPROVER_DEPT_HEAD, role=ROLE_CHECK, due_hours=24)
    #  MỘT bước, HAI người, «tất cả phải duyệt» — đây mới là song song thật.
    #  Khai thành hai bước cùng chặng là RẼ NHÁNH: chỉ một nhánh được chạy.
    x.step(governance_flow, 2, "Pháp chế và Tài chính cùng rà soát",
           ai=APPROVER_EMPLOYEE,
           ref=f"{people['phap_che'].id},{people['tai_chinh'].id}",
           multi_mode=MULTI_ALL, role=ROLE_CHECK, due_hours=48)
    #  Chặng 3 rẽ hai nhánh theo độ mật — nhánh có điều kiện phải đứng trước,
    #  nhánh mặc định hứng phần còn lại. Thiếu nhánh mặc định là phiếu không
    #  khớp gì sẽ KẸT và biến mất khỏi mọi danh sách.
    x.step(governance_flow, 3, "Tổng Giám đốc ký ban hành", branch="n1",
           ai=APPROVER_EMPLOYEE, ref=str(people["tgd"].id),
           condition=_condition_confidential_from_level_3(), due_hours=24)
    x.step(governance_flow, 3, "Phó Tổng Giám đốc ký ban hành", branch="n2",
           ai=APPROVER_EMPLOYEE, ref=str(people["chanh_vp"].id),
           default=True, due_hours=24)
    #  Văn thư chỉ NHẬN BẢN SAO để vào sổ, không chặn luồng.
    x.step(governance_flow, 4, "Văn thư vào sổ và phát hành",
           ai=APPROVER_EMPLOYEE, ref=str(people["chanh_vp"].id),
           node_type=NODE_CC, role=ROLE_EXECUTE)
    out.append(governance_flow)

    # ── 2. Văn bản hành chính thường ngày ────────────────────────────────────
    administrative_flow = x.flow(
        "document", "VB_HANH_CHINH", "Ban hành văn bản hành chính",
        "Công văn, thông báo, giấy mời, giấy giới thiệu — hai bước, có hạn duyệt "
        "trong ngày.",
        condition=x.type_condition("CV", "TB", "GM", "GGT"), priority=10)
    #  Có người dự phòng: trưởng phòng nghỉ thì phiếu không đứng im chờ, cũng
    #  không tự duyệt qua.
    x.step(administrative_flow, 1, "Trưởng bộ phận duyệt nội dung",
           ai=APPROVER_DEPT_HEAD, role=ROLE_CHECK, due_hours=8,
           fallback=people["chanh_vp"].id)
    x.step(administrative_flow, 2, "Chánh Văn phòng ký ban hành",
           ai=APPROVER_EMPLOYEE, ref=str(people["chanh_vp"].id), due_hours=8)
    out.append(administrative_flow)

    # ── 3. Luồng MẶC ĐỊNH — không khai điều kiện, ưu tiên thấp nhất ─────────
    default = x.flow(
        "document", "VB_MAC_DINH", "Ban hành văn bản (mặc định)",
        "Áp cho mọi loại văn bản chưa có luồng riêng. Không có luồng mặc định "
        "thì phiếu không khớp luồng nào sẽ rơi về đường duyệt cũ.")
    x.step(default, 1, "Trưởng bộ phận duyệt", ai=APPROVER_DEPT_HEAD, due_hours=24)
    x.step(default, 2, "Chánh Văn phòng ký",
           ai=APPROVER_EMPLOYEE, ref=str(people["chanh_vp"].id))
    out.append(default)

    # ── 4. ĐƠN NGHỈ PHÉP — chặng 2 trỏ vào GHẾ, không trỏ vào người ─────────
    #
    #  Ưu tiên 30, cao hơn mọi luồng văn bản ở trên: điều kiện của chúng vốn
    #  không phủ `GNP`, nhưng dựa vào điều đó là dựa vào một chi tiết có thể đổi.
    #
    #  ⚠️ Cả hai chặng đều có NGƯỜI DỰ PHÒNG vì luật I08 bỏ người nộp khỏi danh
    #  sách người duyệt: trưởng phòng tự xin nghỉ thì chặng 1 rỗng, mà quản lý
    #  thì cũng phải nghỉ phép. Không khai dự phòng là những đơn đó kẹt.
    leave_flow = x.flow(
        "document", "VB_NGHI_PHEP", "Duyệt đơn nghỉ phép",
        "Trưởng bộ phận của người xin nghỉ duyệt trước, rồi tới trưởng phòng "
        "Nhân sự. Chặng 2 trỏ vào GHẾ trưởng phòng Nhân sự nên đổi người ngồi "
        "ghế thì luồng tự đi theo.",
        condition=x.type_condition("GNP"), priority=30)
    x.step(leave_flow, 1, "Trưởng bộ phận duyệt",
           ai=APPROVER_DEPT_HEAD, due_hours=24, fallback=people["chanh_vp"].id)
    x.step(leave_flow, 2, "Trưởng phòng Nhân sự duyệt",
           ai=APPROVER_DEPT_HEAD_OF, ref=x.hr_department(), due_hours=24,
           fallback=people["tgd"].id)
    out.append(leave_flow)

    # ── 5. Đơn mua hàng — bộ máy này dùng chung, không riêng văn bản ─────────
    purchasing_flow = x.flow(
        "purchase_order", "PO_CHUAN", "Duyệt đơn mua hàng",
        "Trưởng bộ phận duyệt rồi Quản lý thu mua ký. Bộ máy duyệt dùng chung "
        "cho mọi loại chứng từ, không riêng văn bản.")
    x.step(purchasing_flow, 1, "Trưởng bộ phận duyệt", ai=APPROVER_DEPT_HEAD, due_hours=24)
    x.step(purchasing_flow, 2, "Quản lý thu mua ký",
           ai=APPROVER_EMPLOYEE, ref=str(people["tai_chinh"].id))
    out.append(purchasing_flow)

    return out


# ── QUY TẮC ĐÁNH SỐ ─────────────────────────────────────────────────────────
#  (chiều, mẫu, ưu tiên, reset hằng năm, cho phép sửa tay, mô tả, các mã loại)
#
#  Thể thức theo Nghị định 30/2020/NĐ-CP: `<số>/<năm>/<viết tắt loại>-<viết tắt
#  đơn vị soạn>-<viết tắt pháp nhân>`. Văn bản quản trị nội bộ thì dùng MÃ BẤT
#  BIẾN (`DEGO-QC-001`) — nó được viện dẫn suốt nhiều năm, gắn năm vào là mỗi
#  lần sang năm lại phải sửa hết các văn bản trỏ tới nó.
NUMBERING_RULES = [
    (2, "{STT}/{Nam}/{LoaiVB}-{PhongBan}-{PhapNhan}", 100, True, False,
     "Thể thức chuẩn Nghị định 30 cho văn bản gửi ra ngoài.", []),
    (2, "{STT}/{Nam}/QĐ-{PhapNhan}", 50, True, False,
     "Quyết định không kèm tên phòng soạn thảo — nó là văn bản của người đứng "
     "đầu pháp nhân, không phải của một phòng.", ["QD"]),
    (3, "{PhapNhan}-{LoaiVB}-{STT}", 100, False, False,
     "Mã bất biến cho văn bản quản trị nội bộ: không reset theo năm, để văn bản "
     "khác viện dẫn suốt nhiều năm mà không phải sửa số.",
     ["QC", "QT", "QDI", "CS", "HDCV", "BM"]),
    (1, "{STT}/{Nam}/VBĐ-{PhapNhan}", 100, True, True,
     "Văn bản đến: số do văn thư ghi khi nhận. Cho phép sửa tay vì bì thư có "
     "thể tới sau khi đã vào sổ.", []),
]
