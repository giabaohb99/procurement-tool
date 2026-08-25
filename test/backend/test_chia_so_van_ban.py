"""CHIA SỔ VĂN BẢN — người được cho xem phải THẤY quyển sổ đó.

Lỗi khách báo 24/08/2026: mở sổ, thêm người vào ô *Người xem sổ*, lưu xong —
người đó vào trang **Sổ văn bản** vẫn thấy «Chưa có sổ văn bản đến nào khớp».
Bảng `tab_document_book_member` có dòng, nhưng câu truy vấn danh sách chỉ chạy
`apply_scope`, mà phạm vi vai trò chỉ biết THU HẸP (pháp nhân, người tạo) chứ
không biết mở thêm. Kết quả: ô *Người xem sổ* không có tác dụng nào.

Vá xong lại lòi ra chiều ngược — ba đường đọc một quyển sổ chỉ `db.get(...)`,
nên gõ thẳng id lên URL là mở được sổ của pháp nhân khác. Cả hai chiều đều có
bài kiểm ở đây.
"""
import pytest
from fastapi import HTTPException

from app.core.auth import get_perm_profile
from app.modules.company.model import Company
from app.modules.doc_catalog import book_service
from app.modules.doc_catalog.book_model import DocumentBook
from app.modules.doc_catalog.book_schema import DocumentBookCreate
from app.modules.employee.model import Employee
from app.modules.user.model import User

ACTOR = 1


def _nguoi(db, ma: str, company_id: int, dept_id: int):
    employee = Employee(code=ma, full_name=f"Người {ma}", company_id=company_id,
                        department_id=dept_id, is_active=True)
    db.add(employee)
    db.flush()
    user = User(email=f"{ma.lower()}@test.local", employee_id=employee.id,
                password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    return employee, user


@pytest.fixture()
def canh(db, seed, cap_quyen):
    """Một sổ của pháp nhân A + một người của pháp nhân B.

    Người B có quyền `document_book.read` nhưng phạm vi `company` — tức là theo
    vai trò thì KHÔNG bao giờ thấy sổ của A. Đây đúng là ca khắc nghiệt nhất của
    việc chia sổ: chia đích danh phải thắng được cả ranh giới pháp nhân.
    """
    khac = Company(code="CTB", name="Công ty B", issue_code="CTB", level=2, is_active=True)
    db.add(khac)
    db.flush()

    _, tk_a = _nguoi(db, "SO_A", seed.company_id, seed.dept_id)
    nv_b, tk_b = _nguoi(db, "SO_B", khac.id, seed.dept_id)
    cap_quyen(tk_a.id, "document_book", scope="company", read=True)
    cap_quyen(tk_b.id, "document_book", scope="company", read=True)

    so = book_service.create_book(db, DocumentBookCreate(
        name="Sổ văn bản đến", kind=1, company_id=seed.company_id,
        manager_ids=[seed.emp_tp_id], viewer_ids=[],
    ), ACTOR)
    db.commit()
    return {"so": so, "tk_a": tk_a, "tk_b": tk_b, "nv_b": nv_b, "cty_b": khac.id}


def _danh_sach(db, user):
    """Đúng câu truy vấn mà endpoint danh sách chạy."""
    dieu_kien = book_service.dieu_kien_xem_so(user, get_perm_profile(db, user))
    q = db.query(DocumentBook)
    if dieu_kien is not None:
        q = q.filter(dieu_kien)
    return [row.code for row in q.all()]


def test_chua_chia_thi_nguoi_phap_nhan_khac_khong_thay(db, canh):
    assert _danh_sach(db, canh["tk_b"]) == []


def test_chia_xong_thi_THAY_NGAY_trong_danh_sach(db, canh):
    """Chính là lỗi khách báo: chia rồi mà danh sách vẫn rỗng."""
    book_service.update_book(db, canh["so"].id, _sua(viewer_ids=[canh["nv_b"].id]), ACTOR)
    db.commit()

    assert _danh_sach(db, canh["tk_b"]) == [canh["so"].code]


def test_go_khoi_danh_sach_thi_so_bien_mat_lai(db, canh):
    book_service.update_book(db, canh["so"].id, _sua(viewer_ids=[canh["nv_b"].id]), ACTOR)
    db.commit()
    book_service.update_book(db, canh["so"].id, _sua(viewer_ids=[]), ACTOR)
    db.commit()

    assert _danh_sach(db, canh["tk_b"]) == []


def test_go_thanh_vien_book_id_khong_mo_duong_URL(db, canh):
    """Lọc ở danh sách bao nhiêu cũng vô nghĩa nếu gõ id lên URL là mở được."""
    profile = get_perm_profile(db, canh["tk_b"])
    with pytest.raises(HTTPException) as loi:
        book_service.so_xem_duoc_hoac_404(db, canh["so"].id, canh["tk_b"], profile)
    #  404 chứ không 403: nói "có sổ này nhưng anh không được xem" cũng là lộ.
    assert loi.value.status_code == 404

    book_service.update_book(db, canh["so"].id, _sua(viewer_ids=[canh["nv_b"].id]), ACTOR)
    db.commit()
    profile = get_perm_profile(db, canh["tk_b"])
    assert book_service.so_xem_duoc_hoac_404(
        db, canh["so"].id, canh["tk_b"], profile).id == canh["so"].id


def test_nguoi_cung_phap_nhan_van_thay_nhu_cu(db, canh):
    """Vá xong không được làm hẹp hơn trước: phạm vi vai trò vẫn phải chạy."""
    assert _danh_sach(db, canh["tk_a"]) == [canh["so"].code]


def test_tai_khoan_chua_gan_nhan_su_khong_no(db, canh, cap_quyen):
    """Tài khoản hệ thống không có hồ sơ nhân sự — không có gì để cộng thêm."""
    tk = User(email="hethong@test.local", employee_id=None, password_hash="x", is_active=True)
    db.add(tk)
    db.flush()
    cap_quyen(tk.id, "document_book", scope="company", read=True)

    assert _danh_sach(db, tk) == []


def _sua(**doi):
    from app.modules.doc_catalog.book_schema import DocumentBookUpdate

    return DocumentBookUpdate(**doi)
