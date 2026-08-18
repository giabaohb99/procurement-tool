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
                                             APPROVER_EMPLOYEE, MULTI_ALL,
                                             NODE_CC, ROLE_CHECK,
                                             ROLE_EXECUTE)

#  Mức mật 3 = MẬT. Xem `security-level.ts` phía giao diện và cột
#  `secrecy_level` trên `tab_document`.
MUC_MAT = 3


def _dieu_kien_mat_tu_muc_3() -> str:
    return json.dumps([{"field": "secrecy_level", "op": "gte", "value": MUC_MAT}])


def dung_luong(x, nguoi) -> list:
    """Ba luồng cho văn bản + một luồng cho đơn mua hàng."""
    ra = []

    # ── 1. Văn bản quản trị: quy chế, quy định, quy trình, chính sách ────────
    quan_tri = x.luong(
        "document", "VB_QUAN_TRI", "Ban hành văn bản quản trị",
        "Quy chế, quy định, quy trình, chính sách — phải qua pháp chế và tài "
        "chính trước khi trình ký.",
        dieu_kien=x.dieu_kien_loai("QC", "QDI", "QT", "CS"), uu_tien=20)
    x.buoc(quan_tri, 1, "Trưởng bộ phận soạn thảo rà soát",
           ai=APPROVER_DEPT_HEAD, vai_tro=ROLE_CHECK, han_gio=24)
    #  MỘT bước, HAI người, «tất cả phải duyệt» — đây mới là song song thật.
    #  Khai thành hai bước cùng chặng là RẼ NHÁNH: chỉ một nhánh được chạy.
    x.buoc(quan_tri, 2, "Pháp chế và Tài chính cùng rà soát",
           ai=APPROVER_EMPLOYEE,
           ref=f"{nguoi['phap_che'].id},{nguoi['tai_chinh'].id}",
           nhieu_nguoi=MULTI_ALL, vai_tro=ROLE_CHECK, han_gio=48)
    #  Chặng 3 rẽ hai nhánh theo độ mật — nhánh có điều kiện phải đứng trước,
    #  nhánh mặc định hứng phần còn lại. Thiếu nhánh mặc định là phiếu không
    #  khớp gì sẽ KẸT và biến mất khỏi mọi danh sách.
    x.buoc(quan_tri, 3, "Tổng Giám đốc ký ban hành", nhanh="n1",
           ai=APPROVER_EMPLOYEE, ref=str(nguoi["tgd"].id),
           dieu_kien=_dieu_kien_mat_tu_muc_3(), han_gio=24)
    x.buoc(quan_tri, 3, "Phó Tổng Giám đốc ký ban hành", nhanh="n2",
           ai=APPROVER_EMPLOYEE, ref=str(nguoi["chanh_vp"].id),
           mac_dinh=True, han_gio=24)
    #  Văn thư chỉ NHẬN BẢN SAO để vào sổ, không chặn luồng.
    x.buoc(quan_tri, 4, "Văn thư vào sổ và phát hành",
           ai=APPROVER_EMPLOYEE, ref=str(nguoi["chanh_vp"].id),
           loai_buoc=NODE_CC, vai_tro=ROLE_EXECUTE)
    ra.append(quan_tri)

    # ── 2. Văn bản hành chính thường ngày ────────────────────────────────────
    hanh_chinh = x.luong(
        "document", "VB_HANH_CHINH", "Ban hành văn bản hành chính",
        "Công văn, thông báo, giấy mời, giấy giới thiệu — hai bước, có hạn duyệt "
        "trong ngày.",
        dieu_kien=x.dieu_kien_loai("CV", "TB", "GM", "GGT"), uu_tien=10)
    #  Có người dự phòng: trưởng phòng nghỉ thì phiếu không đứng im chờ, cũng
    #  không tự duyệt qua.
    x.buoc(hanh_chinh, 1, "Trưởng bộ phận duyệt nội dung",
           ai=APPROVER_DEPT_HEAD, vai_tro=ROLE_CHECK, han_gio=8,
           du_phong=nguoi["chanh_vp"].id)
    x.buoc(hanh_chinh, 2, "Chánh Văn phòng ký ban hành",
           ai=APPROVER_EMPLOYEE, ref=str(nguoi["chanh_vp"].id), han_gio=8)
    ra.append(hanh_chinh)

    # ── 3. Luồng MẶC ĐỊNH — không khai điều kiện, ưu tiên thấp nhất ─────────
    mac_dinh = x.luong(
        "document", "VB_MAC_DINH", "Ban hành văn bản (mặc định)",
        "Áp cho mọi loại văn bản chưa có luồng riêng. Không có luồng mặc định "
        "thì phiếu không khớp luồng nào sẽ rơi về đường duyệt cũ.")
    x.buoc(mac_dinh, 1, "Trưởng bộ phận duyệt", ai=APPROVER_DEPT_HEAD, han_gio=24)
    x.buoc(mac_dinh, 2, "Chánh Văn phòng ký",
           ai=APPROVER_EMPLOYEE, ref=str(nguoi["chanh_vp"].id))
    ra.append(mac_dinh)

    # ── 4. Đơn mua hàng — bộ máy này dùng chung, không riêng văn bản ─────────
    mua_hang = x.luong(
        "purchase_order", "PO_CHUAN", "Duyệt đơn mua hàng",
        "Trưởng bộ phận duyệt rồi Quản lý thu mua ký. Bộ máy duyệt dùng chung "
        "cho mọi loại chứng từ, không riêng văn bản.")
    x.buoc(mua_hang, 1, "Trưởng bộ phận duyệt", ai=APPROVER_DEPT_HEAD, han_gio=24)
    x.buoc(mua_hang, 2, "Quản lý thu mua ký",
           ai=APPROVER_EMPLOYEE, ref=str(nguoi["tai_chinh"].id))
    ra.append(mua_hang)

    return ra


# ── QUY TẮC ĐÁNH SỐ ─────────────────────────────────────────────────────────
#  (chiều, mẫu, ưu tiên, reset hằng năm, cho phép sửa tay, mô tả, các mã loại)
#
#  Thể thức theo Nghị định 30/2020/NĐ-CP: `<số>/<năm>/<viết tắt loại>-<viết tắt
#  đơn vị soạn>-<viết tắt pháp nhân>`. Văn bản quản trị nội bộ thì dùng MÃ BẤT
#  BIẾN (`DEGO-QC-001`) — nó được viện dẫn suốt nhiều năm, gắn năm vào là mỗi
#  lần sang năm lại phải sửa hết các văn bản trỏ tới nó.
QUY_TAC_SO = [
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
