"""PHẠM VI ÁP DỤNG của văn bản (F01–F05).

Bốn quy tắc, và quy tắc ngoại lệ là thứ dễ làm sai nhất:

1. Các dòng bao gồm cộng dồn.
2. Chiều cụ thể hơn thắng: cá nhân > phòng ban > pháp nhân.
3. Cùng một chiều thì loại trừ thắng bao gồm.
4. Không có dòng nào = áp cho TOÀN BỘ PHÁP NHÂN BAN HÀNH, và chỉ pháp nhân đó.

Quy tắc 4 đổi ngày 19/08/2026 (trước đó là "không ai thuộc phạm vi"). Bắt khai
tay một dòng "pháp nhân = công ty mình" cho gần như mọi văn bản thì ai cũng
quên, và văn bản ban hành xong nằm im không tới ai. Mặc định mới vẫn không làm
rò sang công ty khác — nó dừng đúng ở pháp nhân đứng tên văn bản.

Khai bất kỳ dòng nào là mặc định TẮT: lúc đó người soạn đã nói rõ ý mình, hệ
thống không được tự cộng thêm gì vào.
"""
import pytest
from pydantic import ValidationError

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.document import scope_service
from app.modules.document.model import (STATUS_DRAFT, STATUS_EFFECTIVE,
                                        Document)
from app.modules.document.scope_controller import ScopeCreate
from app.modules.document.scope_model import (DIM_COMPANY, DIM_DEPARTMENT,
                                              DIM_EMPLOYEE, MODE_EXCLUDE,
                                              MODE_INCLUDE, DocumentScope)

DOC_ID = 1


@pytest.fixture()
def to_chuc(db):
    """Tập đoàn (cấp 1) + hai công ty con (cấp 2), mỗi nơi một phòng Kế toán."""
    tap_doan = Company(code="DEGO", name="Tập đoàn", level=1, is_active=True)
    con_a = Company(code="ABA", name="Công ty A", level=2, is_active=True)
    con_b = Company(code="IDA", name="Công ty B", level=2, is_active=True)
    db.add_all([tap_doan, con_a, con_b])
    db.flush()

    ke_toan_a = Department(code="KT-A", name="Kế toán", company_id=con_a.id, is_active=True)
    ke_toan_b = Department(code="KT-B", name="Kế toán", company_id=con_b.id, is_active=True)
    db.add_all([ke_toan_a, ke_toan_b])
    db.flush()

    nguoi_a = Employee(code="NV-A", full_name="Anh A", company_id=con_a.id,
                       department_id=ke_toan_a.id, is_active=True)
    nguoi_b = Employee(code="NV-B", full_name="Chị B", company_id=con_b.id,
                       department_id=ke_toan_b.id, is_active=True)
    db.add_all([nguoi_a, nguoi_b])
    db.commit()

    return {"tap_doan": tap_doan, "con_a": con_a, "con_b": con_b,
            "kt_a": ke_toan_a, "kt_b": ke_toan_b, "a": nguoi_a, "b": nguoi_b}


def _khai(db, **kwargs):
    row = DocumentScope(document_id=DOC_ID, **kwargs)
    db.add(row)
    db.commit()
    return row


def _van_ban(db, company_id: int, status: int = STATUS_EFFECTIVE, doc_id: int = DOC_ID):
    """Một văn bản trần của pháp nhân nào đó — chỉ đủ cột để tính phạm vi.

    `doc_type_id` / `owner_employee_id` đặt bừa một số: ràng buộc
    `ck_document_internal_required` chỉ đòi chúng khác rỗng, mà phần tính phạm vi
    thì không đọc tới hai cột này.
    """
    doc = Document(id=doc_id, company_id=company_id, title="Văn bản", status=status,
                   doc_type_id=1, owner_employee_id=1)
    db.add(doc)
    db.commit()
    return doc


# ── Quy tắc 4 · chưa khai gì thì áp cho đúng pháp nhân ban hành ─────────────
def test_chua_khai_dong_nao_thi_ap_cho_ca_phap_nhan_ban_hanh(db, to_chuc):
    """Người của công ty A thấy văn bản của công ty A, người công ty B thì không."""
    _van_ban(db, to_chuc["con_a"].id)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is True
    assert scope_service.applies_to(db, DOC_ID, to_chuc["b"]) is False


def test_ban_nhap_chua_khai_gi_thi_chua_ap_cho_ai(db, to_chuc):
    """Mặc định chỉ chạy với văn bản còn sống — nháp không phải thứ để mọi người đọc."""
    _van_ban(db, to_chuc["con_a"].id, status=STATUS_DRAFT)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is False


def test_khai_mot_dong_la_tat_mac_dinh_theo_phap_nhan(db, to_chuc):
    """Văn bản công ty A khai áp cho công ty B thì người công ty A KHÔNG còn trong phạm vi.

    Khai rồi mà hệ thống vẫn cộng thêm pháp nhân ban hành thì không có cách nào
    ra văn bản "công ty A ban hành, chỉ công ty B đọc".
    """
    _van_ban(db, to_chuc["con_a"].id)
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["con_b"].id, mode=MODE_INCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is False
    assert scope_service.applies_to(db, DOC_ID, to_chuc["b"]) is True


# ── Quy tắc 1 · bao gồm cộng dồn ────────────────────────────────────────────
def test_bao_gom_theo_phap_nhan(db, to_chuc):
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["con_a"].id, mode=MODE_INCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is True
    assert scope_service.applies_to(db, DOC_ID, to_chuc["b"]) is False


def test_hai_dong_bao_gom_cong_don(db, to_chuc):
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["con_a"].id, mode=MODE_INCLUDE)
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["con_b"].id, mode=MODE_INCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is True
    assert scope_service.applies_to(db, DOC_ID, to_chuc["b"]) is True


def test_bao_gom_theo_ca_nhan(db, to_chuc):
    _khai(db, dim=DIM_EMPLOYEE, employee_id=to_chuc["a"].id, mode=MODE_INCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is True
    assert scope_service.applies_to(db, DOC_ID, to_chuc["b"]) is False


# ── F03 · phòng ban phải kèm pháp nhân ──────────────────────────────────────
def test_phong_ban_khai_kem_phap_nhan_chi_trung_dung_mot_noi(db, to_chuc):
    """Phòng "Kế toán" có ở cả hai công ty — khai kèm pháp nhân thì chỉ trúng một."""
    _khai(db, dim=DIM_DEPARTMENT, company_id=to_chuc["con_a"].id,
          department_id=to_chuc["kt_a"].id, mode=MODE_INCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is True
    assert scope_service.applies_to(db, DOC_ID, to_chuc["b"]) is False


def test_khai_phong_ban_khong_kem_phap_nhan_bi_chan(db):
    """Chặn ở tầng nhập liệu, kèm câu nói rõ vì sao — không chỉ báo "sai dữ liệu"."""
    with pytest.raises(ValidationError) as loi:
        ScopeCreate(dim=DIM_DEPARTMENT, department_id=9)
    assert "13 pháp nhân" in str(loi.value)


def test_khai_pham_vi_thieu_doi_tuong_bi_chan(db):
    with pytest.raises(ValidationError):
        ScopeCreate(dim=DIM_COMPANY)
    with pytest.raises(ValidationError):
        ScopeCreate(dim=DIM_EMPLOYEE)


def test_gom_don_vi_con_chi_co_nghia_voi_phap_nhan(db):
    with pytest.raises(ValidationError) as loi:
        ScopeCreate(dim=DIM_EMPLOYEE, employee_id=1, include_children=True)
    assert "đơn vị con" in str(loi.value)


# ── F04 · gồm đơn vị con ────────────────────────────────────────────────────
def test_tap_doan_khong_kem_co_thi_khong_lan_xuong_cong_ty_con(db, to_chuc):
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["tap_doan"].id, mode=MODE_INCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is False


def test_tap_doan_kem_co_gom_don_vi_con_thi_ap_cho_moi_cong_ty_con(db, to_chuc):
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["tap_doan"].id,
          include_children=True, mode=MODE_INCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is True
    assert scope_service.applies_to(db, DOC_ID, to_chuc["b"]) is True


# ── Quy tắc 2–3 · ưu tiên độ cụ thể, cùng cấp thì loại trừ thắng ─────────────
def test_loai_tru_thang_bao_gom_cung_chieu(db, to_chuc):
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["con_a"].id, mode=MODE_INCLUDE)
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["con_a"].id, mode=MODE_EXCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is False


def test_loai_tru_ca_nhan_thang_bao_gom_ca_phap_nhan(db, to_chuc):
    """Áp cho cả công ty A, trừ đúng anh A — đây là ca dùng thật của loại trừ."""
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["con_a"].id, mode=MODE_INCLUDE)
    _khai(db, dim=DIM_EMPLOYEE, employee_id=to_chuc["a"].id, mode=MODE_EXCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is False


def test_loai_tru_mot_phong_ban_khoi_pham_vi_toan_tap_doan(db, to_chuc):
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["tap_doan"].id,
          include_children=True, mode=MODE_INCLUDE)
    _khai(db, dim=DIM_DEPARTMENT, company_id=to_chuc["con_b"].id,
          department_id=to_chuc["kt_b"].id, mode=MODE_EXCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is True
    assert scope_service.applies_to(db, DOC_ID, to_chuc["b"]) is False


def test_bao_gom_ca_nhan_thang_loai_tru_phong_ban(db, to_chuc):
    """Cá nhân được gọi tên là ngoại lệ của dòng loại trừ phòng rộng hơn."""
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["con_a"].id, mode=MODE_INCLUDE)
    _khai(db, dim=DIM_DEPARTMENT, company_id=to_chuc["con_a"].id,
          department_id=to_chuc["kt_a"].id, mode=MODE_EXCLUDE)
    _khai(db, dim=DIM_EMPLOYEE, employee_id=to_chuc["a"].id, mode=MODE_INCLUDE)

    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is True


# ── F05 · văn bản áp dụng cho tôi ───────────────────────────────────────────
def test_liet_ke_van_ban_ap_dung_cho_mot_nguoi(db, to_chuc):
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["con_a"].id, mode=MODE_INCLUDE)
    db.add(DocumentScope(document_id=2, dim=DIM_COMPANY,
                         company_id=to_chuc["con_b"].id, mode=MODE_INCLUDE))
    db.commit()

    assert scope_service.document_ids_for(db, to_chuc["a"]) == [DOC_ID]
    assert scope_service.document_ids_for(db, to_chuc["b"]) == [2]


def test_van_ban_khong_khai_gi_van_vao_danh_sach_cua_nguoi_cung_phap_nhan(db, to_chuc):
    """Đây là đường đi của phần lớn văn bản — không khai dòng nào, chỉ lưu hành nội bộ."""
    _van_ban(db, to_chuc["con_a"].id, doc_id=7)
    _van_ban(db, to_chuc["con_b"].id, doc_id=8)

    assert scope_service.document_ids_for(db, to_chuc["a"]) == [7]
    assert scope_service.document_ids_for(db, to_chuc["b"]) == [8]


# ── F13 · chọn cơ chế lúc ban hành ──────────────────────────────────────────
#
# Hai cơ chế KHÔNG mâu thuẫn nhau, dùng cho hai tình huống khác nhau:
#   * nội dung giống hệt mọi công ty con  → một văn bản gắn phạm vi;
#   * pháp nhân con phải tự đứng tên       → clone thành bản nháp riêng.
# Chốt LÚC BAN HÀNH chứ không phải lúc soạn: tới lúc đó người ban hành mới biết
# nội dung cuối cùng có dùng chung được không.
from app.modules.company.model import Company as _Company  # noqa: E402
from app.modules.doc_catalog.model import DocType  # noqa: E402
from app.modules.document import service  # noqa: E402
from app.modules.document.model import (APPLY_MODE_CLONE,  # noqa: E402
                                        APPLY_MODE_SCOPE)
from app.modules.document.schema import ApproveIn, DocumentCreate  # noqa: E402

ACTOR = 1


@pytest.fixture()
def van_ban(db, seed):
    company = db.get(_Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế bảo mật",
        content_html="<p>Nội dung</p>",
    ), ACTOR)
    service.submit(db, doc, ACTOR)
    return doc


def test_mac_dinh_la_gan_pham_vi(db, van_ban):
    """Phạm vi là mặc định; clone là nút bấm có điều kiện."""
    service.approve(db, van_ban, ACTOR)
    assert van_ban.apply_mode == APPLY_MODE_SCOPE


def test_chon_clone_luc_ban_hanh_thi_ghi_lai(db, van_ban):
    service.approve(db, van_ban, ACTOR, apply_mode=APPLY_MODE_CLONE)
    assert van_ban.apply_mode == APPLY_MODE_CLONE


def test_khong_truyen_thi_giu_nguyen_gia_tri_dang_co(db, van_ban):
    """Đường gọi cũ không truyền gì — không được lặng lẽ đặt lại về mặc định."""
    van_ban.apply_mode = APPLY_MODE_CLONE
    db.commit()

    service.approve(db, van_ban, ACTOR)
    assert van_ban.apply_mode == APPLY_MODE_CLONE


def test_co_che_la_bi_tu_choi(db, van_ban):
    from fastapi import HTTPException

    with pytest.raises(HTTPException):
        service.approve(db, van_ban, ACTOR, apply_mode=9)


def test_schema_chan_gia_tri_ngoai_hai_co_che(db):
    with pytest.raises(ValidationError):
        ApproveIn(apply_mode=3)
    #  Bỏ trống là hợp lệ — nghĩa là "giữ nguyên".
    assert ApproveIn().apply_mode is None
