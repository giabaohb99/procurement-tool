"""VĂN BẢN CÁ NHÂN — AI THẤY ĐƯỢC. Đơn nghỉ phép không được lộ ra ngoài.

Phương châm của cả tệp: **người không liên quan thì không thấy nó ở BẤT KỲ đâu** —
không trong danh sách, không trong tìm kiếm, không qua «Áp dụng cho tôi», không
qua quyền theo sổ, và gõ thẳng id lên URL cũng không.

Nền của vấn đề: `document.read` phạm vi *công ty* nghĩa là "đọc mọi văn bản của
pháp nhân". Với công văn thì đúng; áp lên đơn xin nghỉ ốm thì thành cả công ty
đọc được chuyện riêng của từng người. Nên loại bật `is_personal` **không đi theo
phạm vi vai trò** nữa (CR-159).

Bốn vai được thấy, và chỉ bốn: người nghỉ · người lập đơn · người đang/đã duyệt ·
người được chia đích danh. Cộng vai trò phạm vi *tất cả* (HR / quản trị) — đó là
chủ ý, nhân sự phải tổng hợp được ngày phép.

⚠️ Mỗi bài kiểm ở đây đều có **cặp đối chứng** trên một văn bản loại THƯỜNG. Chặn
sạch mọi thứ thì bài nào cũng xanh mà tính năng thì chết — cặp đối chứng là thứ
phân biệt "giấu đúng cái cần giấu" với "giấu tất".
"""
import pytest
from fastapi import HTTPException

from app.core.auth import get_perm_profile
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, SKIP_NONE,
                                             ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.doc_catalog.model import DocType
from app.modules.document import access_service, service
from app.modules.document.model import Document
from app.modules.document.schema import DocumentCreate
from app.modules.employee.model import Employee
from app.modules.user.model import User

ACTOR_HE_THONG = 1
ENTITY = "document"


def _nguoi(db, seed, ma: str, department_id=None):
    """Một nhân sự kèm tài khoản, chưa có vai trò nào."""
    employee = Employee(code=ma, full_name=f"Nhân sự {ma}", company_id=seed.company_id,
                        department_id=department_id or seed.dept_id, is_active=True)
    db.add(employee)
    db.flush()
    user = User(email=f"{ma.lower()}@test.local", employee_id=employee.id,
                password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    return employee, user


@pytest.fixture()
def canh(db, seed, cap_quyen):
    """Một đơn nghỉ phép của Nam, đang chờ trưởng phòng duyệt.

    Kèm một CÔNG VĂN cùng pháp nhân làm đối chứng.
    """
    loai_ca_nhan = DocType(code="GNP", name="Giấy nghỉ phép", id_scheme=2,
                           number_when=2, is_personal=True)
    loai_thuong = DocType(code="CV", name="Công văn", id_scheme=2, number_when=2)
    db.add_all([loai_ca_nhan, loai_thuong])
    db.flush()

    nam, tk_nam = _nguoi(db, seed, "NAM")
    truong_phong, tk_truong_phong = _nguoi(db, seed, "TRUONGPHONG")
    dong_nghiep, tk_dong_nghiep = _nguoi(db, seed, "DONGNGHIEP")
    hr, tk_hr = _nguoi(db, seed, "HR")
    _, tk_nguoi_la = _nguoi(db, seed, "NGUOILA")

    #  Nam và đồng nghiệp: quyền đọc phạm vi CÔNG TY — đúng vai trò `vanban_xem`
    #  của dữ liệu thật. Đây chính là cái phạm vi làm lộ đơn nghỉ phép.
    cap_quyen(tk_nam.id, "document", scope="company", read=True, create=True, write=True)
    cap_quyen(tk_dong_nghiep.id, "document", scope="company", read=True)
    #  HR: phạm vi TẤT CẢ — cố ý vẫn thấy.
    cap_quyen(tk_hr.id, "document", scope="all", read=True)

    #  Luồng một bước, người duyệt là trưởng phòng (khai đích danh cho gọn; cách
    #  chọn theo phòng ban kiểm riêng ở `test_nguoi_duyet_theo_phong_ban.py`).
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True,
                          created_by=ACTOR_HE_THONG, updated_by=ACTOR_HE_THONG))
    flow = ApprovalFlow(entity=ENTITY, code="NP-01", name="Duyệt nghỉ phép",
                        is_active=True, created_by=ACTOR_HE_THONG, updated_by=ACTOR_HE_THONG)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Trưởng bộ phận duyệt",
                        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(truong_phong.id),
                        skip_duplicate=SKIP_NONE,
                        created_by=ACTOR_HE_THONG, updated_by=ACTOR_HE_THONG))
    db.commit()

    don = service.create_document(db, DocumentCreate(
        doc_type_id=loai_ca_nhan.id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=nam.id,
        title="Đơn xin nghỉ ốm 3 ngày",
        content_html="<p>Kính gửi Ban Giám đốc.</p>",
        metadata={"from_date": "2026-09-01", "to_date": "2026-09-03",
                  "leave_type": "sick", "reason": "Điều trị nội trú"},
    ), tk_nam.id)
    don = service.submit(db, don, tk_nam.id)

    cong_van = service.create_document(db, DocumentCreate(
        doc_type_id=loai_thuong.id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=nam.id,
        title="Công văn nhắc lịch họp", content_html="<p>Nội dung.</p>",
    ), tk_nam.id)

    return {"don": don, "cong_van": cong_van, "loai_thuong": loai_thuong,
            "nam": nam, "tk_nam": tk_nam,
            "truong_phong": truong_phong, "tk_truong_phong": tk_truong_phong,
            "dong_nghiep": dong_nghiep, "tk_dong_nghiep": tk_dong_nghiep,
            "hr": hr, "tk_hr": tk_hr, "tk_nguoi_la": tk_nguoi_la}


def _mo_duoc(db, doc, user) -> bool:
    """Mở được ĐÚNG văn bản này không (tầng chi tiết)."""
    return access_service.can(db, doc, user, get_perm_profile(db, user), "read")


def _danh_sach(db, user) -> set[int]:
    """Id văn bản người này thấy trong danh sách / tìm kiếm (tầng truy vấn)."""
    dieu_kien = access_service.visible_condition(user, get_perm_profile(db, user), "read")
    query = db.query(Document.id)
    if dieu_kien is not None:
        query = query.filter(dieu_kien)
    return {row[0] for row in query.all()}


# ── Người KHÔNG liên quan ───────────────────────────────────────────────────

def test_dong_nghiep_cung_phong_khong_thay_don_nghi_phep(db, canh):
    """Ca nặng nhất: người ngồi cạnh, cùng phòng, cùng pháp nhân, CÓ quyền đọc.

    Trước CR-159 họ đọc được — `document.read` phạm vi *công ty* phủ luôn cả đơn
    nghỉ ốm của đồng nghiệp.
    """
    assert _mo_duoc(db, canh["don"], canh["tk_dong_nghiep"]) is False
    assert canh["don"].id not in _danh_sach(db, canh["tk_dong_nghiep"])


def test_dong_nghiep_VAN_thay_van_ban_thuong_cung_phap_nhan(db, canh):
    """CẶP ĐỐI CHỨNG. Không có bài này thì "chặn tất" cũng làm bài trên xanh."""
    assert _mo_duoc(db, canh["cong_van"], canh["tk_dong_nghiep"]) is True
    assert canh["cong_van"].id in _danh_sach(db, canh["tk_dong_nghiep"])


def test_nguoi_khong_co_vai_tro_nao_khong_thay_gi(db, canh):
    assert _mo_duoc(db, canh["don"], canh["tk_nguoi_la"]) is False
    assert _danh_sach(db, canh["tk_nguoi_la"]) == set()


def test_tim_kiem_khong_lo_tieu_de_don_nghi_phep(db, canh):
    """K03 — danh sách và tìm kiếm chạy cùng một điều kiện.

    Lọc ở chi tiết mà quên lọc ở truy vấn thì gõ «nghỉ ốm» vào ô tìm kiếm là ra
    nguyên cái tiêu đề, đủ để biết ai đang ốm dù bấm vào ăn 404.
    """
    thay = _danh_sach(db, canh["tk_dong_nghiep"])
    lo = db.query(Document.id).filter(Document.id.in_(thay),
                                      Document.title.like("%nghỉ ốm%")).all()
    assert lo == []


def test_ensure_can_tra_404_chu_khong_phai_403(db, canh):
    """403 đã tự nói «có văn bản này nhưng anh không được xem» — lộ đúng thứ cần giấu."""
    with pytest.raises(HTTPException) as loi:
        access_service.ensure_can(db, canh["don"], canh["tk_dong_nghiep"],
                                  get_perm_profile(db, canh["tk_dong_nghiep"]), "read")
    assert loi.value.status_code == 404


# ── Bốn vai ĐƯỢC thấy ───────────────────────────────────────────────────────

def test_nguoi_nghi_thay_don_cua_chinh_minh(db, canh):
    assert _mo_duoc(db, canh["don"], canh["tk_nam"]) is True
    assert canh["don"].id in _danh_sach(db, canh["tk_nam"])


def test_nguoi_dang_duyet_thay_du_khong_co_vai_tro_nao(db, canh):
    """Trưởng phòng không được cấp vai trò nào ở phân hệ Văn bản — như dữ liệu thật."""
    assert _mo_duoc(db, canh["don"], canh["tk_truong_phong"]) is True
    assert canh["don"].id in _danh_sach(db, canh["tk_truong_phong"])


def test_ky_xong_roi_van_mo_lai_duoc(db, canh):
    """Chữ ký vào tờ giấy không xem lại được là chữ ký mù ở thì quá khứ."""
    from app.modules.approval import action_service, instance_service

    phien = instance_service.phien_dang_chay(db, ENTITY, canh["don"].id)
    action_service.duyet(db, phien, canh["truong_phong"].id, ACTOR_HE_THONG, {})

    assert _mo_duoc(db, canh["don"], canh["tk_truong_phong"]) is True
    assert canh["don"].id in _danh_sach(db, canh["tk_truong_phong"])


def test_hr_pham_vi_tat_ca_van_thay(db, canh):
    """Cố ý. Nhân sự phải tổng hợp được ngày phép, quản trị phải gỡ được phiếu kẹt."""
    assert _mo_duoc(db, canh["don"], canh["tk_hr"]) is True
    assert canh["don"].id in _danh_sach(db, canh["tk_hr"])


def test_chia_dich_danh_thi_thay(db, canh, seed):
    """Chia đích danh là quyết định CÓ Ý THỨC của người giữ văn bản.

    Khác hẳn phạm vi khai rộng tay — nên nó thắng, cả ở danh sách lẫn chi tiết.
    """
    from app.modules.document.access_model import EFFECT_ALLOW, SUBJECT_EMPLOYEE
    from app.modules.document.access_service import grant
    from app.modules.document.schema import AccessGrant

    grant(db, canh["don"], AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=canh["dong_nghiep"].id,
        effect=EFFECT_ALLOW, can_read=True, reason="Nhờ xử lý hộ"), ACTOR_HE_THONG)
    db.commit()

    assert _mo_duoc(db, canh["don"], canh["tk_dong_nghiep"]) is True
    assert canh["don"].id in _danh_sach(db, canh["tk_dong_nghiep"])


# ── Những đường vòng phải bịt ───────────────────────────────────────────────

def test_thanh_vien_SO_khong_mo_duoc_don_nghi_phep(db, canh, seed):
    """Quẳng đơn nghỉ phép vào một quyển sổ chung là cả phòng Hành chính đọc được.

    Quyền theo sổ vốn là cách phân việc cho văn thư — đúng với công văn, quyết
    định. Với văn bản cá nhân thì nó là một đường vòng, phải đóng.
    """
    from app.modules.doc_catalog.book_model import (DocumentBook,
                                                    DocumentBookMember)

    so = DocumentBook(code="SO-NS", name="Sổ Nhân sự", company_id=seed.company_id,
                      created_by=ACTOR_HE_THONG, updated_by=ACTOR_HE_THONG)
    db.add(so)
    db.flush()
    db.add(DocumentBookMember(book_id=so.id, employee_id=canh["dong_nghiep"].id,
                              role=access_service.ROLE_BOOK_VIEWER,
                              created_by=ACTOR_HE_THONG, updated_by=ACTOR_HE_THONG))
    canh["don"].book_id = so.id
    db.commit()

    #  Đối chứng: cùng quyển sổ đó VẪN mở được văn bản thường.
    canh["cong_van"].book_id = so.id
    db.commit()

    assert _mo_duoc(db, canh["don"], canh["tk_dong_nghiep"]) is False
    assert canh["don"].id not in _danh_sach(db, canh["tk_dong_nghiep"])
    assert _mo_duoc(db, canh["cong_van"], canh["tk_dong_nghiep"]) is True


def test_pham_vi_ap_dung_khong_mo_duoc_don_nghi_phep(db, canh, seed):
    """«Áp dụng cho tôi» mở cho MỌI tài khoản đăng nhập — đường vòng rộng nhất.

    Nó vốn để nhân viên thường đọc được quy chế áp dụng cho mình. Đơn nghỉ phép
    lọt vào đó là cả nhóm áp dụng đọc được.
    """
    from app.modules.document.scope_model import (DIM_DEPARTMENT, MODE_INCLUDE,
                                                  DocumentScope)

    db.add(DocumentScope(document_id=canh["don"].id, dim=DIM_DEPARTMENT,
                         company_id=seed.company_id, department_id=seed.dept_id,
                         mode=MODE_INCLUDE,
                         created_by=ACTOR_HE_THONG, updated_by=ACTOR_HE_THONG))
    db.commit()

    assert _mo_duoc(db, canh["don"], canh["tk_dong_nghiep"]) is False


def test_doi_loai_sang_ca_nhan_thi_lap_tuc_bi_giau(db, canh):
    """Công văn lỡ tạo nhầm, đổi sang loại cá nhân → biến khỏi mắt người khác NGAY.

    Luật đọc theo LOẠI HIỆN TẠI của văn bản, không phải theo loại lúc tạo. Nếu
    chốt chặn chụp lại loại lúc tạo thì đổi loại xong dữ liệu vẫn hở.
    """
    assert canh["cong_van"].id in _danh_sach(db, canh["tk_dong_nghiep"])

    canh["cong_van"].doc_type_id = canh["don"].doc_type_id
    db.commit()

    assert _mo_duoc(db, canh["cong_van"], canh["tk_dong_nghiep"]) is False
    assert canh["cong_van"].id not in _danh_sach(db, canh["tk_dong_nghiep"])


def test_lap_HO_thi_ca_nguoi_lap_lan_nguoi_nghi_deu_thay(db, canh, seed):
    """Hành chính lập hộ là việc có thật. Cả hai người đều phải mở lại được."""
    don_ho = service.create_document(db, DocumentCreate(
        doc_type_id=canh["don"].doc_type_id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=canh["nam"].id,
        title="Đơn nghỉ phép lập hộ", content_html="<p>Nội dung.</p>",
        metadata={"from_date": "2026-10-01", "to_date": "2026-10-01",
                  "reason": "Việc gia đình"},
    ), canh["tk_hr"].id)

    #  Người NGHỈ (ghi ở owner + metadata) thấy…
    assert _mo_duoc(db, don_ho, canh["tk_nam"]) is True
    assert don_ho.id in _danh_sach(db, canh["tk_nam"])
    #  …người LẬP cũng thấy…
    assert _mo_duoc(db, don_ho, canh["tk_hr"]) is True
    #  …còn người thứ ba thì không.
    assert _mo_duoc(db, don_ho, canh["tk_dong_nghiep"]) is False


def test_danh_sach_va_chi_tiet_khong_bao_gio_lech_nhau(db, canh):
    """Hai tầng phải nói CÙNG một câu về từng văn bản.

    Danh sách rộng hơn = lộ tiêu đề rồi bấm vào 404 (đúng cái bẫy đã ghi ở
    `van-thu/06` §4.6). Danh sách hẹp hơn = văn bản mở được mà tìm không ra.
    """
    moi_van_ban = db.query(Document).all()
    for tai_khoan in (canh["tk_nam"], canh["tk_truong_phong"], canh["tk_dong_nghiep"],
                      canh["tk_hr"], canh["tk_nguoi_la"]):
        thay = _danh_sach(db, tai_khoan)
        for doc in moi_van_ban:
            assert (doc.id in thay) == _mo_duoc(db, doc, tai_khoan), (
                f"lệch ở văn bản #{doc.id} với tài khoản {tai_khoan.email}")
