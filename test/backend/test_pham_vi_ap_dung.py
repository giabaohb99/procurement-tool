"""PHẠM VI ÁP DỤNG của văn bản (F01–F05).

Ba quy tắc, và quy tắc thứ ba là thứ dễ làm sai nhất vì nó **ngược trực giác**:

1. Các dòng bao gồm cộng dồn.
2. Loại trừ luôn thắng bao gồm.
3. Không có dòng nào = KHÔNG AI thuộc phạm vi.

Quy tắc 3 an toàn hơn: quên khai thì văn bản không tới ai và người ta sẽ hỏi.
Mặc định "mọi người" thì quên khai nghĩa là gửi văn bản mật cho cả tập đoàn —
và không ai phát hiện ra, vì mọi người đều đọc được nên không ai đi hỏi.
"""
import pytest
from pydantic import ValidationError

from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.document import scope_service
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


# ── Quy tắc 3 · chưa khai gì thì không ai thuộc phạm vi ─────────────────────
def test_chua_khai_dong_nao_thi_khong_ai_thuoc_pham_vi(db, to_chuc):
    assert scope_service.applies_to(db, DOC_ID, to_chuc["a"]) is False
    assert scope_service.applies_to(db, DOC_ID, to_chuc["b"]) is False


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


# ── Quy tắc 2 · loại trừ luôn thắng ─────────────────────────────────────────
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


# ── F05 · văn bản áp dụng cho tôi ───────────────────────────────────────────
def test_liet_ke_van_ban_ap_dung_cho_mot_nguoi(db, to_chuc):
    _khai(db, dim=DIM_COMPANY, company_id=to_chuc["con_a"].id, mode=MODE_INCLUDE)
    db.add(DocumentScope(document_id=2, dim=DIM_COMPANY,
                         company_id=to_chuc["con_b"].id, mode=MODE_INCLUDE))
    db.commit()

    assert scope_service.document_ids_for(db, to_chuc["a"]) == [DOC_ID]
    assert scope_service.document_ids_for(db, to_chuc["b"]) == [2]


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
