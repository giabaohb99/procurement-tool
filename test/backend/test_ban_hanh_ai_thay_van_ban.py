"""BAN HÀNH XONG THÌ AI THẤY VĂN BẢN — kiểm theo tình huống thật, không theo hàm.

`test_pham_vi_ap_dung.py` đã kiểm bốn quy tắc ở mức từng hàm. Bài kiểm này đi
hướng ngược lại: dựng đúng những gì người dùng bấm trên màn ban hành rồi hỏi
**bốn đầu ra phải cùng trả lời một kết quả**:

| Đầu ra | Hàm | Người dùng thấy ở đâu |
| --- | --- | --- |
| Thuộc phạm vi | `scope_service.applies_to` | luật gốc |
| Danh sách của tôi | `scope_service.document_ids_for` | màn «Văn bản áp dụng cho tôi» |
| Mở được chi tiết | `access_service.can(..., "read")` | bấm từ chuông / gõ URL |
| Nhận chuông + email | `issue_notification.recipients_for_issue` | lúc bấm Ban hành |

Bốn đầu ra này nằm ở bốn tệp khác nhau nhưng phải cho cùng một tập người. Lệch
nhau là ra đúng hai lỗi tệ nhất của phân hệ: người trong phạm vi nhận mail rồi
bấm vào thì 404, hoặc người bị loại trừ vẫn mở được văn bản.

Năm tình huống, đúng thứ tự người dùng mô tả:

1. ban hành cho một pháp nhân, không khai gì → cả pháp nhân đó thấy;
2. như trên, loại trừ vài cá nhân;
3. như trên, loại trừ nguyên một phòng ban;
4. loại trừ phòng ban đó nhưng cho lại một người trong phòng;
5. bản clone do pháp nhân nhận tự ban hành, chọn phạm vi y như bốn ca trên.

⚠️ Bài `test_chi_khai_loai_tru_thi_khong_ai_thay` ghi lại một cái bẫy CÓ THẬT
đang tồn tại, không phải hành vi mong muốn — đọc ghi chú ở đó.
"""
from types import SimpleNamespace

import pytest

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.document import (access_service, clone_service,
                                  issue_notification, scope_service, service)
from app.modules.document.model import ALIVE_STATUSES, Document
from app.modules.document.schema import DocumentCreate
from app.modules.document.scope_model import (DIM_COMPANY, DIM_DEPARTMENT,
                                              DIM_EMPLOYEE, MODE_EXCLUDE,
                                              MODE_INCLUDE, DocumentScope)
from app.modules.employee.model import Employee
from app.modules.user.model import User

ACTOR = 1

#  Người trong pháp nhân A. Khóa dùng xuyên suốt bài kiểm.
NGUOI_CUA_A = ("giam_doc", "kt_truong", "kt_nhan_vien", "kd_truong", "kd_nhan_vien")


@pytest.fixture()
def to_chuc(db):
    """Hai pháp nhân. A có hai phòng và năm người; B là chốt chặn "không rò".

    B tồn tại để mọi bài kiểm khẳng định được cả chiều ngược: văn bản của A
    KHÔNG được lọt sang người của B. Thiếu chốt này thì một hàm trả "ai cũng
    thấy" vẫn qua được hết bài kiểm.
    """
    cong_ty_a = Company(code="ABA", name="Công ty A", issue_code="ABA", level=2, is_active=True)
    cong_ty_b = Company(code="IDA", name="Công ty B", issue_code="IDA", level=2, is_active=True)
    db.add_all([cong_ty_a, cong_ty_b])
    db.flush()

    ke_toan = Department(code="KT-A", name="Kế toán", company_id=cong_ty_a.id, is_active=True)
    kinh_doanh = Department(code="KD-A", name="Kinh doanh", company_id=cong_ty_a.id, is_active=True)
    phong_b = Department(code="HC-B", name="Hành chính", company_id=cong_ty_b.id, is_active=True)
    db.add_all([ke_toan, kinh_doanh, phong_b])
    db.flush()

    person = {
        #  Chủ pháp nhân A — người đứng tên ban hành ở mọi tình huống.
        "giam_doc": Employee(code="A-GD", full_name="Giám đốc A", company_id=cong_ty_a.id,
                             department_id=kinh_doanh.id, email="gd@a.vn", is_active=True),
        "kt_truong": Employee(code="A-KT1", full_name="Trưởng Kế toán", company_id=cong_ty_a.id,
                              department_id=ke_toan.id, email="kt1@a.vn", is_active=True),
        "kt_nhan_vien": Employee(code="A-KT2", full_name="Nhân viên Kế toán", company_id=cong_ty_a.id,
                                 department_id=ke_toan.id, email="kt2@a.vn", is_active=True),
        "kd_truong": Employee(code="A-KD1", full_name="Trưởng Kinh doanh", company_id=cong_ty_a.id,
                              department_id=kinh_doanh.id, email="kd1@a.vn", is_active=True),
        "kd_nhan_vien": Employee(code="A-KD2", full_name="Nhân viên Kinh doanh", company_id=cong_ty_a.id,
                                 department_id=kinh_doanh.id, email="kd2@a.vn", is_active=True),
        #  Người của pháp nhân B.
        "b_giam_doc": Employee(code="B-GD", full_name="Giám đốc B", company_id=cong_ty_b.id,
                               department_id=phong_b.id, email="gd@b.vn", is_active=True),
        "b_nhan_vien": Employee(code="B-NV", full_name="Nhân viên B", company_id=cong_ty_b.id,
                                department_id=phong_b.id, email="nv@b.vn", is_active=True),
    }
    db.add_all(person.values())
    db.flush()

    #  Mỗi nhân sự một tài khoản: `recipients_for_issue` chỉ đếm người CÓ tài
    #  khoản đang hoạt động, nhân sự trần không nhận được chuông.
    tai_khoan = {
        key: User(employee_id=emp.id, email=emp.email, is_active=True)
        for key, emp in person.items()
    }
    db.add_all(tai_khoan.values())

    kind = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(kind)
    db.commit()

    return SimpleNamespace(a=cong_ty_a, b=cong_ty_b, ke_toan=ke_toan,
                           kinh_doanh=kinh_doanh, phong_b=phong_b,
                           person=person, tai_khoan=tai_khoan, kind=kind)


@pytest.fixture()
def van_ban(db, to_chuc):
    """Quy chế của pháp nhân A, đã duyệt xong — tức là đã ban hành."""
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=to_chuc.kind.id,
        company_id=to_chuc.a.id,
        department_id=to_chuc.kinh_doanh.id,
        owner_employee_id=to_chuc.person["giam_doc"].id,
        title="Quy chế chi tiêu nội bộ",
        content_html="<p>Điều 1.</p>",
    ), ACTOR)
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    assert doc.status in ALIVE_STATUSES, "Văn bản phải còn sống thì phạm vi mới tính"
    return doc


# ── Hỏi cả bốn đầu ra một lượt ───────────────────────────────────────────────
def _ai_thay(db, doc: Document, to_chuc) -> set[str]:
    """Tập người thấy văn bản — và khẳng định luôn bốn đầu ra không lệch nhau.

    Gộp vào một hàm thay vì viết bốn khẳng định rời ở từng bài: chỉ cần một đầu
    ra tính khác ba cái kia là mọi tình huống bên dưới đỏ cùng lúc, chỉ đúng
    chỗ đó chứ không phải dò lại từng bài.
    """
    theo_luat, theo_danh_sach, theo_chi_tiet = set(), set(), set()

    for key, employee in to_chuc.person.items():
        if scope_service.applies_to(db, doc.id, employee):
            theo_luat.add(key)
        if doc.id in scope_service.document_ids_for(db, employee):
            theo_danh_sach.add(key)

        #  Hồ sơ quyền RỖNG: không vai trò, không phạm vi, không chia sẻ đích
        #  danh. Người bình thường trong công ty đúng là như vậy — họ mở được
        #  văn bản CHỈ nhờ nằm trong phạm vi áp dụng. Cho sẵn vai trò ở đây là
        #  bài kiểm tự bịt mất thứ cần kiểm.
        user = SimpleNamespace(id=to_chuc.tai_khoan[key].id, employee_id=employee.id)
        profile = {"grants": [], "company_id": employee.company_id,
                   "dept_id": employee.department_id, "employee_id": employee.id}
        if access_service.can(db, doc, user, profile, "read"):
            theo_chi_tiet.add(key)

    nhan_thong_bao = {
        key
        for key, emp in to_chuc.person.items()
        for recipients in issue_notification.recipients_for_issue(db, doc.id)
        if recipients.employee.id == emp.id
    }

    assert theo_danh_sach == theo_luat, "Màn «áp dụng cho tôi» lệch luật phạm vi"
    assert theo_chi_tiet == theo_luat, "Mở chi tiết lệch luật phạm vi (nhận mail xong bấm vào 404)"
    assert nhan_thong_bao == theo_luat, "Người nhận chuông/email lệch luật phạm vi"
    return theo_luat


def _khai(db, doc: Document, **kwargs) -> DocumentScope:
    row = DocumentScope(document_id=doc.id, created_by=ACTOR, updated_by=ACTOR, **kwargs)
    db.add(row)
    db.commit()
    return row


def _bao_gom_phap_nhan(db, doc: Document, company_id: int):
    return _khai(db, doc, dim=DIM_COMPANY, mode=MODE_INCLUDE, company_id=company_id)


# ── Ca 1 · ban hành cho một pháp nhân, không khai gì ─────────────────────────
def test_ca1_khong_khai_gi_thi_ca_phap_nhan_ban_hanh_deu_thay(db, van_ban, to_chuc):
    """Quy tắc 4 — không khai dòng nào là áp cho ĐÚNG pháp nhân đứng tên."""
    assert _ai_thay(db, van_ban, to_chuc) == set(NGUOI_CUA_A)


def test_ca1_khai_tay_dung_phap_nhan_do_cho_ket_qua_y_het(db, van_ban, to_chuc):
    """Khai tay «bao gồm Công ty A» phải bằng đúng mặc định, không hơn không kém.

    Người soạn cẩn thận sẽ khai tay; người soạn vội thì bỏ trống. Hai lối bấm
    ấy mà ra hai tập người khác nhau là văn bản tới ai phụ thuộc thói quen gõ.
    """
    _bao_gom_phap_nhan(db, van_ban, to_chuc.a.id)
    assert _ai_thay(db, van_ban, to_chuc) == set(NGUOI_CUA_A)


def test_ca1_van_ban_chua_duyet_thi_chua_toi_ai(db, to_chuc):
    """Bản nháp không phải thứ nằm trong «Văn bản áp dụng cho tôi»."""
    nhap = service.create_document(db, DocumentCreate(
        doc_type_id=to_chuc.kind.id, company_id=to_chuc.a.id,
        department_id=to_chuc.kinh_doanh.id,
        owner_employee_id=to_chuc.person["giam_doc"].id,
        title="Quy chế đang soạn", content_html="<p>Nháp.</p>",
    ), ACTOR)
    assert _ai_thay(db, nhap, to_chuc) == set()


# ── Ca 2 · loại trừ vài cá nhân ──────────────────────────────────────────────
def test_ca2_loai_tru_vai_ca_nhan_thi_dung_ho_khong_thay(db, van_ban, to_chuc):
    _bao_gom_phap_nhan(db, van_ban, to_chuc.a.id)
    for key in ("kt_nhan_vien", "kd_nhan_vien"):
        _khai(db, van_ban, dim=DIM_EMPLOYEE, mode=MODE_EXCLUDE,
              employee_id=to_chuc.person[key].id)

    assert _ai_thay(db, van_ban, to_chuc) == {"giam_doc", "kt_truong", "kd_truong"}


def test_ca2_nguoi_bi_loai_tru_go_thang_url_van_khong_vao_duoc(db, van_ban, to_chuc):
    """Loại trừ phải chặn ở CẢ đường vòng, không chỉ ẩn khỏi danh sách."""
    _bao_gom_phap_nhan(db, van_ban, to_chuc.a.id)
    bi_loai = to_chuc.person["kt_nhan_vien"]
    _khai(db, van_ban, dim=DIM_EMPLOYEE, mode=MODE_EXCLUDE, employee_id=bi_loai.id)

    user = SimpleNamespace(id=to_chuc.tai_khoan["kt_nhan_vien"].id, employee_id=bi_loai.id)
    profile = {"grants": [], "company_id": bi_loai.company_id,
               "dept_id": bi_loai.department_id, "employee_id": bi_loai.id}
    assert access_service.can(db, van_ban, user, profile, "read") is False


def test_chi_khai_loai_tru_thi_khong_ai_thay(db, van_ban, to_chuc):
    """⚠️ BẪY ĐANG CÓ THẬT — ghi lại hành vi, KHÔNG phải xác nhận nó đúng.

    Người dùng chỉ bấm «loại trừ anh B» mà quên khai «bao gồm Công ty A»: khai
    bất kỳ dòng nào là mặc định-theo-pháp-nhân TẮT (quy tắc 4), nên còn đúng một
    dòng loại trừ, không ai có dòng BAO GỒM nào trúng mình → văn bản không tới
    một ai, kể cả những người chẳng liên quan tới dòng loại trừ đó.

    Không có gì trong backend chặn hay cảnh báo tình huống này. Bài kiểm để đây
    để lúc sửa (hoặc tự thêm dòng bao gồm, hoặc chặn ở API) thì thấy ngay là
    mình đang đổi hành vi nào.
    """
    _khai(db, van_ban, dim=DIM_EMPLOYEE, mode=MODE_EXCLUDE,
          employee_id=to_chuc.person["kt_nhan_vien"].id)

    assert _ai_thay(db, van_ban, to_chuc) == set()


# ── Ca 3 · loại trừ nguyên một phòng ban ─────────────────────────────────────
def test_ca3_loai_tru_mot_phong_ban(db, van_ban, to_chuc):
    _bao_gom_phap_nhan(db, van_ban, to_chuc.a.id)
    _khai(db, van_ban, dim=DIM_DEPARTMENT, mode=MODE_EXCLUDE,
          company_id=to_chuc.a.id, department_id=to_chuc.ke_toan.id)

    assert _ai_thay(db, van_ban, to_chuc) == {"giam_doc", "kd_truong", "kd_nhan_vien"}


def test_ca3_loai_tru_phong_cung_ten_o_phap_nhan_khac_khong_anh_huong(db, van_ban, to_chuc):
    """Phòng ban luôn khai kèm pháp nhân, nên «Kế toán» của B là phòng khác."""
    ke_toan_b = Department(code="KT-B", name="Kế toán", company_id=to_chuc.b.id, is_active=True)
    db.add(ke_toan_b)
    db.commit()

    _bao_gom_phap_nhan(db, van_ban, to_chuc.a.id)
    _khai(db, van_ban, dim=DIM_DEPARTMENT, mode=MODE_EXCLUDE,
          company_id=to_chuc.b.id, department_id=ke_toan_b.id)

    #  Dòng loại trừ trỏ vào phòng của pháp nhân khác — không ai của A trúng nó.
    assert _ai_thay(db, van_ban, to_chuc) == set(NGUOI_CUA_A)


# ── Ca 4 · loại trừ phòng ban nhưng cho lại một người trong phòng ────────────
def test_ca4_cho_lai_mot_nguoi_trong_phong_da_bi_loai(db, van_ban, to_chuc):
    """Quy tắc 2 — cá nhân (3) cụ thể hơn phòng ban (2) nên thắng."""
    _bao_gom_phap_nhan(db, van_ban, to_chuc.a.id)
    _khai(db, van_ban, dim=DIM_DEPARTMENT, mode=MODE_EXCLUDE,
          company_id=to_chuc.a.id, department_id=to_chuc.ke_toan.id)
    _khai(db, van_ban, dim=DIM_EMPLOYEE, mode=MODE_INCLUDE,
          employee_id=to_chuc.person["kt_truong"].id)

    assert _ai_thay(db, van_ban, to_chuc) == {
        "giam_doc", "kd_truong", "kd_nhan_vien", "kt_truong",
    }


def test_ca4_cam_dich_danh_van_thang_khi_da_cho_lai(db, van_ban, to_chuc):
    """Quy tắc 3 — cùng chiều cá nhân thì loại trừ thắng bao gồm.

    Khai cả hai dòng trên cùng một người là mâu thuẫn; luật chọn phía an toàn.
    """
    _bao_gom_phap_nhan(db, van_ban, to_chuc.a.id)
    _khai(db, van_ban, dim=DIM_DEPARTMENT, mode=MODE_EXCLUDE,
          company_id=to_chuc.a.id, department_id=to_chuc.ke_toan.id)
    _khai(db, van_ban, dim=DIM_EMPLOYEE, mode=MODE_INCLUDE,
          employee_id=to_chuc.person["kt_truong"].id)
    _khai(db, van_ban, dim=DIM_EMPLOYEE, mode=MODE_EXCLUDE,
          employee_id=to_chuc.person["kt_truong"].id)

    assert _ai_thay(db, van_ban, to_chuc) == {"giam_doc", "kd_truong", "kd_nhan_vien"}


# ── Ca 5 · bản clone do pháp nhân nhận tự ban hành ───────────────────────────
@pytest.fixture()
def ban_clone(db, van_ban, to_chuc):
    """A ban hành gốc → clone xuống B → giám đốc B ban hành bản của mình."""
    #  Gốc phải khai rõ hai pháp nhân, nếu không thì clone chỉ mang đúng dòng
    #  «bao gồm pháp nhân nhận» do `clone_service` tự điền.
    _bao_gom_phap_nhan(db, van_ban, to_chuc.a.id)
    _bao_gom_phap_nhan(db, van_ban, to_chuc.b.id)

    clone = clone_service.create_clones(db, van_ban, [to_chuc.b.id], None, "", ACTOR)[0]
    clone.owner_employee_id = to_chuc.person["b_giam_doc"].id
    clone.department_id = to_chuc.phong_b.id
    db.commit()

    service.submit(db, clone, ACTOR)
    service.approve(db, clone, ACTOR)
    return clone


def test_ca5_clone_thua_dung_pham_vi_phap_nhan_nhan(db, ban_clone, to_chuc):
    """Bản của B tới người của B; người của A không dính bản clone."""
    rows = scope_service.scopes_of(db, ban_clone.id)
    assert [(r.dim, r.mode, r.company_id) for r in rows] == [
        (DIM_COMPANY, MODE_INCLUDE, to_chuc.b.id)
    ]
    assert _ai_thay(db, ban_clone, to_chuc) == {"b_giam_doc", "b_nhan_vien"}


def test_ca5_clone_loai_tru_ca_nhan_cua_phap_nhan_nhan(db, ban_clone, to_chuc):
    """Ca 2 lặp lại trên bản clone — giám đốc B loại trừ một người của mình."""
    _khai(db, ban_clone, dim=DIM_EMPLOYEE, mode=MODE_EXCLUDE,
          employee_id=to_chuc.person["b_nhan_vien"].id)

    assert _ai_thay(db, ban_clone, to_chuc) == {"b_giam_doc"}


def test_ca5_clone_loai_tru_phong_roi_cho_lai_mot_nguoi(db, ban_clone, to_chuc):
    """Ca 4 lặp lại trên bản clone: loại phòng Hành chính B, giữ lại giám đốc B."""
    _khai(db, ban_clone, dim=DIM_DEPARTMENT, mode=MODE_EXCLUDE,
          company_id=to_chuc.b.id, department_id=to_chuc.phong_b.id)
    _khai(db, ban_clone, dim=DIM_EMPLOYEE, mode=MODE_INCLUDE,
          employee_id=to_chuc.person["b_giam_doc"].id)

    assert _ai_thay(db, ban_clone, to_chuc) == {"b_giam_doc"}


def test_ca5_pham_vi_hai_ban_doc_lap_nhau(db, ban_clone, van_ban, to_chuc):
    """Sửa phạm vi bản clone KHÔNG được đụng tới bản gốc, và ngược lại.

    Đây là điều kiện sống còn của tính năng clone: hai bản là hai văn bản riêng
    của hai pháp nhân, chung nhau mỗi cái liên kết nguồn.
    """
    _khai(db, ban_clone, dim=DIM_EMPLOYEE, mode=MODE_EXCLUDE,
          employee_id=to_chuc.person["b_nhan_vien"].id)
    _khai(db, van_ban, dim=DIM_EMPLOYEE, mode=MODE_EXCLUDE,
          employee_id=to_chuc.person["kt_nhan_vien"].id)

    assert _ai_thay(db, ban_clone, to_chuc) == {"b_giam_doc"}
    #  Gốc khai bao gồm cả A và B (xem fixture) nên người của B vẫn trong phạm
    #  vi bản gốc — bản clone không cắt điều đó.
    assert _ai_thay(db, van_ban, to_chuc) == {
        "giam_doc", "kt_truong", "kd_truong", "kd_nhan_vien",
        "b_giam_doc", "b_nhan_vien",
    }


def test_ca5_nguoi_doc_duoc_clone_thi_mo_lai_duoc_ban_goc(db, ban_clone, van_ban, to_chuc):
    """Pháp nhân nhận phải đặt được hai bản cạnh nhau để đối chiếu.

    Chỉ mở thêm quyền ĐỌC gốc; đọc được clone không có nghĩa là sửa được gốc.
    """
    nguoi_b = to_chuc.person["b_nhan_vien"]
    user = SimpleNamespace(id=to_chuc.tai_khoan["b_nhan_vien"].id, employee_id=nguoi_b.id)
    profile = {"grants": [], "company_id": nguoi_b.company_id,
               "dept_id": nguoi_b.department_id, "employee_id": nguoi_b.id}

    assert access_service.can(db, ban_clone, user, profile, "read") is True
    assert access_service.can(db, van_ban, user, profile, "read") is True
    assert access_service.can(db, van_ban, user, profile, "write") is False
