"""QUYỀN TRÊN TỪNG VĂN BẢN — ai thấy, ai đọc, ai sửa, ai xóa.

Bài kiểm bám đúng thứ tự quyết định của `access_service`:

```
CẤM đích danh          →  không được, dừng luôn
CHO PHÉP đích danh     →  được
THÀNH VIÊN SỔ chứa nó  →  được (quản lý sổ: xem + sửa · người xem sổ: xem)
phạm vi vai trò        →  được
còn lại                →  không được
```

Người trong bài kiểm dựng bằng tay chứ không qua API vì hồ sơ quyền
(`get_perm_profile`) có bộ đệm 60 giây — dựng thẳng dict cho mỗi tình huống thì
mỗi bài kiểm một trạng thái rõ ràng, không dính bộ đệm của bài trước.
"""
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import access_service, service
from app.modules.document.access_model import (EFFECT_ALLOW, EFFECT_DENY,
                                               SUBJECT_DEPARTMENT,
                                               SUBJECT_EMPLOYEE, SUBJECT_ROLE,
                                               DocumentAccess)
from app.modules.document.model import Document
from app.modules.document.query import documents_query
from app.modules.document.schema import AccessGrant, DocumentCreate

OWNER_USER_ID = 10
OUTSIDER_USER_ID = 20


def _profile(employee_id=0, dept_id=0, company_id=0, scope="own", role_id=1,
             actions=("read", "write", "delete")):
    """Hồ sơ quyền tối thiểu, đúng hình dạng `get_perm_profile` trả về."""
    perms = {a: a in actions for a in ("read", "create", "write", "delete",
                                       "approve", "cancel", "print", "export")}
    perms["scope"] = scope
    return {
        "grants": [{"role_id": role_id, "perms": {"document": perms},
                    "scope": {"inc": {}, "exc": {}}}],
        "company_id": company_id, "dept_id": dept_id, "dept_name": "",
        "employee_id": employee_id, "emp_code": "", "emp_name": "",
    }


@pytest.fixture()
def doc(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()

    return service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế lương",
        content_html="<p>Mật</p>",
    ), OWNER_USER_ID)


def _visible(db, user, profile, action="read"):
    cond = access_service.visible_condition(user, profile, action)
    q = documents_query(db)
    return (q if cond is None else q.filter(cond)).all()


# ── Không có gì thì không thấy ───────────────────────────────────────────────
def test_nguoi_ngoai_khong_thay_van_ban(db, doc, seed):
    outsider = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")

    assert _visible(db, outsider, profile) == []
    assert access_service.can(db, doc, outsider, profile) is False


def test_nguoi_tao_thay_van_ban_cua_minh(db, doc, seed):
    owner = SimpleNamespace(id=OWNER_USER_ID, employee_id=seed.emp_req_id)
    profile = _profile(employee_id=seed.emp_req_id, scope="own")

    assert [row.id for row in _visible(db, owner, profile)] == [doc.id]
    assert access_service.can(db, doc, owner, profile, "write") is True


# ── Chia sẻ đích danh mở thêm ────────────────────────────────────────────────
def test_chia_dich_danh_cho_nguoi_ngoai_pham_vi(db, doc, seed):
    outsider = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")

    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id,
        effect=EFFECT_ALLOW, can_read=True, reason="Gửi Trưởng phòng đọc"), OWNER_USER_ID)

    assert [row.id for row in _visible(db, outsider, profile)] == [doc.id]
    assert access_service.can(db, doc, outsider, profile, "read") is True
    #  Chia ĐỌC thì không kèm theo SỬA.
    assert access_service.can(db, doc, outsider, profile, "write") is False


def test_chia_cho_ca_phong_ban(db, doc, seed):
    member = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_nstm_id)
    profile = _profile(employee_id=seed.emp_nstm_id, dept_id=seed.dept_id, scope="own")

    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_DEPARTMENT, subject_id=seed.dept_id,
        effect=EFFECT_ALLOW, can_read=True), OWNER_USER_ID)

    #  Chia cho phòng thì người mới vào phòng tự có quyền — đó là lý do cấp theo
    #  phòng thay vì liệt kê từng người.
    assert access_service.can(db, doc, member, profile) is True


def test_chia_theo_vai_tro(db, doc, seed):
    user = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own", role_id=7)

    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_ROLE, subject_id=7, effect=EFFECT_ALLOW), OWNER_USER_ID)

    assert access_service.can(db, doc, user, profile) is True


def test_chia_quyen_sua_va_xoa(db, doc, seed):
    user = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")

    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id,
        can_read=True, can_write=True, can_delete=True), OWNER_USER_ID)

    for action in ("read", "write", "delete"):
        assert access_service.can(db, doc, user, profile, action) is True


# ── Cấm thắng cho phép ───────────────────────────────────────────────────────
def test_cam_dich_danh_thang_ca_pham_vi_vai_tro(db, doc, seed):
    """Người tạo văn bản, nhưng bị cấm đích danh → không còn thấy nó nữa."""
    owner = SimpleNamespace(id=OWNER_USER_ID, employee_id=seed.emp_req_id)
    profile = _profile(employee_id=seed.emp_req_id, scope="own")
    assert access_service.can(db, doc, owner, profile) is True

    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_req_id,
        effect=EFFECT_DENY, can_read=True, reason="Đã chuyển công tác"), OWNER_USER_ID)

    assert access_service.can(db, doc, owner, profile) is False
    assert _visible(db, owner, profile) == []


def test_cam_thang_ca_dong_cho_phep(db, doc, seed):
    user = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, dept_id=seed.dept_id, scope="own")

    #  Cho phép cả phòng, rồi cấm riêng một người trong phòng đó.
    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_DEPARTMENT, subject_id=seed.dept_id), OWNER_USER_ID)
    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id,
        effect=EFFECT_DENY), OWNER_USER_ID)

    assert access_service.can(db, doc, user, profile) is False
    assert _visible(db, user, profile) == []


def test_khong_doc_duoc_thi_bao_404_khong_phai_403(db, doc, seed):
    """403 đã là xác nhận 'có văn bản này' — chỉ riêng việc đó đã lộ (K03)."""
    outsider = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")

    with pytest.raises(HTTPException) as err:
        access_service.ensure_can(db, doc, outsider, profile, "read")
    assert err.value.status_code == 404

    #  Đọc được nhưng không sửa được thì 403 — lúc đó họ đã biết văn bản tồn tại.
    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id), OWNER_USER_ID)
    with pytest.raises(HTTPException) as err:
        access_service.ensure_can(db, doc, outsider, profile, "write")
    assert err.value.status_code == 403


# ── Thời hạn và thu hồi ──────────────────────────────────────────────────────
def test_qua_han_thi_tu_mat_quyen(db, doc, seed):
    user = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")

    yesterday = date.today() - timedelta(days=1)
    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id,
        valid_from=yesterday - timedelta(days=5), valid_to=yesterday), OWNER_USER_ID)

    assert access_service.can(db, doc, user, profile) is False


def test_chua_toi_ngay_bat_dau_thi_chua_co_quyen(db, doc, seed):
    user = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")

    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id,
        valid_from=date.today() + timedelta(days=3)), OWNER_USER_ID)

    assert access_service.can(db, doc, user, profile) is False


def test_thu_hoi_la_danh_dau_khong_xoa_dong(db, doc, seed):
    user = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")

    row = access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id), OWNER_USER_ID)
    assert access_service.can(db, doc, user, profile) is True

    access_service.revoke(db, doc, row.id, "Hết việc", OWNER_USER_ID)

    assert access_service.can(db, doc, user, profile) is False
    #  Dòng PHẢI còn trong bảng, kèm mốc thu hồi và lý do (G19, G20).
    kept = db.query(DocumentAccess).filter(DocumentAccess.document_id == doc.id).all()
    assert len(kept) == 1
    assert kept[0].revoked_at is not None
    assert kept[0].revoke_reason == "Hết việc"


def test_thu_hoi_hai_lan_bi_chan(db, doc, seed):
    row = access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id), OWNER_USER_ID)
    access_service.revoke(db, doc, row.id, "Hết việc", OWNER_USER_ID)

    with pytest.raises(HTTPException) as err:
        access_service.revoke(db, doc, row.id, "Lần nữa", OWNER_USER_ID)
    assert err.value.status_code == 400


def test_chia_lai_cho_cung_mot_nguoi_thi_sua_dong_cu(db, doc, seed):
    """Hai dòng cho phép cùng một người, thu hồi một dòng mà vẫn đọc được là
    chuyện không ai giải thích nổi — nên `grant` sửa dòng đang sống."""
    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id), OWNER_USER_ID)
    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id,
        can_write=True), OWNER_USER_ID)

    live = db.query(DocumentAccess).filter(DocumentAccess.document_id == doc.id,
                                           DocumentAccess.revoked_at.is_(None)).all()
    assert len(live) == 1
    assert live[0].can_write is True


def test_han_nguoc_dau_bi_chan(db, doc, seed):
    with pytest.raises(HTTPException) as err:
        access_service.grant(db, doc, AccessGrant(
            subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id,
            valid_from=date.today(), valid_to=date.today() - timedelta(days=1)),
            OWNER_USER_ID)
    assert err.value.status_code == 400


# ── Không ảnh hưởng văn bản khác ─────────────────────────────────────────────
def test_chia_mot_van_ban_khong_mo_cac_van_ban_khac(db, doc, seed):
    other = service.create_document(db, DocumentCreate(
        doc_type_id=doc.doc_type_id, company_id=seed.company_id,
        department_id=seed.dept_id, owner_employee_id=seed.emp_req_id,
        title="Quy chế khác", content_html="<p>x</p>"), OWNER_USER_ID)

    user = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")
    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id), OWNER_USER_ID)

    assert [row.id for row in _visible(db, user, profile)] == [doc.id]
    assert access_service.can(db, other, user, profile) is False


# ── Pháp nhân nhận clone được đối chiếu bản gốc ─────────────────────────────
def _clone_o_phap_nhan_con(db, doc, seed):
    child = Company(code="CON", name="Công ty nhận clone", level=2, is_active=True)
    db.add(child)
    db.commit()

    clone = service.create_document(db, DocumentCreate(
        doc_type_id=doc.doc_type_id,
        company_id=child.id,
        department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id,
        title="Bản riêng Quy chế lương",
        content_html="<p>Nội dung nhận từ bản gốc</p>",
    ), OUTSIDER_USER_ID)
    clone.source_document_id = doc.id
    db.commit()
    return child, clone


def test_doc_duoc_ban_clone_thi_xem_lai_duoc_ban_goc(db, doc, seed):
    child, clone = _clone_o_phap_nhan_con(db, doc, seed)
    user = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(
        employee_id=seed.emp_tp_id,
        company_id=child.id,
        scope="company",
        actions=("read", "write"),
    )

    assert access_service.can(db, clone, user, profile, "read") is True
    #  Mở thêm đúng quyền ĐỌC bản gốc để đối chiếu, không cho sửa bản của mẹ.
    assert access_service.can(db, doc, user, profile, "read") is True
    assert access_service.can(db, doc, user, profile, "write") is False
    #  Bản gốc không trộn vào danh sách chung của pháp nhân con; họ đi tới nó
    #  bằng nút «Xem bản gốc» trên chính bản clone.
    assert [row.id for row in _visible(db, user, profile)] == [clone.id]


def test_cam_dich_danh_ban_goc_van_thang_quyen_doc_qua_clone(db, doc, seed):
    child, clone = _clone_o_phap_nhan_con(db, doc, seed)
    user = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(
        employee_id=seed.emp_tp_id,
        company_id=child.id,
        scope="company",
        actions=("read", "write"),
    )
    assert access_service.can(db, clone, user, profile, "read") is True

    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE,
        subject_id=seed.emp_tp_id,
        effect=EFFECT_DENY,
        can_read=True,
        reason="Không được xem bản gốc",
    ), OWNER_USER_ID)

    assert access_service.can(db, doc, user, profile, "read") is False


def test_van_ban_ngoai_khong_lot_qua_lop_chia_se(db, doc, seed):
    """Lớp quyền mới không được vô hiệu hóa lớp lọc `origin`."""
    from app.modules.document.model import ORIGIN_LEGAL

    legal = Document(origin=ORIGIN_LEGAL, title="Nghị định 30")
    db.add(legal)
    db.commit()

    admin = SimpleNamespace(id=OWNER_USER_ID, employee_id=seed.emp_req_id)
    profile = _profile(employee_id=seed.emp_req_id, scope="all")
    titles = {row.title for row in _visible(db, admin, profile)}
    assert "Nghị định 30" not in titles


# ── Quyền theo SỔ VĂN BẢN ────────────────────────────────────────────────────
def _book_with(db, seed, employee_id: int, role: int):
    """Một quyển sổ có `employee_id` giữ vai `role` (1 quản lý · 2 người xem)."""
    from app.modules.doc_catalog.book_model import DocumentBook, DocumentBookMember

    book = DocumentBook(code=f"SO{role}{employee_id}", name="Sổ thử", kind=2,
                        company_id=seed.company_id, number_prefix="CVĐ")
    db.add(book)
    db.flush()
    db.add(DocumentBookMember(book_id=book.id, employee_id=employee_id, role=role))
    db.commit()
    return book


def test_nguoi_quan_ly_so_xem_va_sua_duoc_van_ban_trong_so(db, doc, seed):
    """Cấp quyền theo SỔ: khai một lần cho cả quyển thay vì chia từng văn bản."""
    manager = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")
    assert access_service.can(db, doc, manager, profile) is False

    book = _book_with(db, seed, seed.emp_tp_id, role=1)
    doc.book_id = book.id
    db.commit()

    assert access_service.can(db, doc, manager, profile, "read") is True
    assert access_service.can(db, doc, manager, profile, "write") is True
    #  Giữ sổ không có nghĩa là được dọn sổ.
    assert access_service.can(db, doc, manager, profile, "delete") is False
    assert [row.id for row in _visible(db, manager, profile)] == [doc.id]


def test_nguoi_xem_so_chi_xem_khong_sua(db, doc, seed):
    viewer = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_nstm_id)
    profile = _profile(employee_id=seed.emp_nstm_id, scope="own")

    book = _book_with(db, seed, seed.emp_nstm_id, role=2)
    doc.book_id = book.id
    db.commit()

    assert access_service.can(db, doc, viewer, profile, "read") is True
    assert access_service.can(db, doc, viewer, profile, "write") is False


def test_cam_dich_danh_thang_ca_quyen_theo_so(db, doc, seed):
    manager = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")

    book = _book_with(db, seed, seed.emp_tp_id, role=1)
    doc.book_id = book.id
    db.commit()
    assert access_service.can(db, doc, manager, profile) is True

    access_service.grant(db, doc, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=seed.emp_tp_id,
        effect=EFFECT_DENY), OWNER_USER_ID)

    assert access_service.can(db, doc, manager, profile) is False
    assert _visible(db, manager, profile) == []


def test_van_ban_khong_thuoc_so_thi_thanh_vien_so_khong_thay(db, doc, seed):
    manager = SimpleNamespace(id=OUTSIDER_USER_ID, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")

    _book_with(db, seed, seed.emp_tp_id, role=1)   # sổ có, nhưng văn bản không vào sổ
    assert doc.book_id is None
    assert access_service.can(db, doc, manager, profile) is False


def test_vao_so_thi_duoc_cap_so_thu_tu_trong_so(db, doc, seed):
    """Văn bản vào sổ mang HAI số: số hiệu đi ra ngoài và số thứ tự trong sổ."""
    from datetime import date

    book = _book_with(db, seed, seed.emp_req_id, role=1)
    doc.book_id = book.id
    db.commit()

    service.assign_book_number(db, doc)
    db.commit()
    assert doc.book_seq_no == 1
    assert doc.book_year == date.today().year

    #  Gọi lại không cấp số mới — số đã ghi vào sổ.
    service.assign_book_number(db, doc)
    assert doc.book_seq_no == 1
