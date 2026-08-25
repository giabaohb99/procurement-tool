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


# ── Chiều GHI: sửa / xóa sổ ──────────────────────────────────────────────────

def test_co_quyen_ghi_nhung_so_cua_phap_nhan_KHAC_thi_khong_sua_duoc(db, canh, cap_quyen):
    """Quyền vai trò `write` nói "được sửa sổ", KHÔNG nói "sổ của mọi pháp nhân".

    Trước 25/08/2026 hai endpoint sửa / xóa sổ không gọi một hàm phạm vi nào —
    ai có `document_book.write` là sửa được mọi quyển, kể cả sổ của pháp nhân
    khác. Cùng họ lỗi với chỗ đọc sổ ở trên.
    """
    cap_quyen(canh["tk_b"].id, "document_book", scope="company", write=True, delete=True)
    profile = get_perm_profile(db, canh["tk_b"])

    for hanh_dong in ("write", "delete"):
        with pytest.raises(HTTPException) as loi:
            book_service.so_sua_duoc_hoac_404(
                db, canh["so"].id, canh["tk_b"], profile, hanh_dong)
        assert loi.value.status_code == 404, hanh_dong


def test_NGUOI_QUAN_LY_so_thi_sua_duoc_du_o_phap_nhan_khac(db, canh, cap_quyen):
    """Đúng câu chú thích dưới ô *Người quản lý*: «Sửa, đóng và xóa được sổ».

    Trước đây câu đó là chữ suông — backend không đọc tới bảng thành viên khi
    xét quyền sửa.
    """
    cap_quyen(canh["tk_b"].id, "document_book", scope="company", write=True, delete=True)
    book_service.update_book(db, canh["so"].id,
                             _sua(manager_ids=[canh["nv_b"].id]), ACTOR)
    db.commit()
    profile = get_perm_profile(db, canh["tk_b"])

    assert book_service.so_sua_duoc_hoac_404(
        db, canh["so"].id, canh["tk_b"], profile, "write").id == canh["so"].id


def test_chi_NGUOI_XEM_thi_van_khong_sua_duoc(db, canh, cap_quyen):
    """Chia để đọc không phải là chia để sửa — hai vai khác nhau."""
    cap_quyen(canh["tk_b"].id, "document_book", scope="company", write=True)
    book_service.update_book(db, canh["so"].id,
                             _sua(viewer_ids=[canh["nv_b"].id]), ACTOR)
    db.commit()
    profile = get_perm_profile(db, canh["tk_b"])

    #  Xem thì được…
    assert book_service.so_xem_duoc_hoac_404(
        db, canh["so"].id, canh["tk_b"], profile).id == canh["so"].id
    #  …sửa thì không.
    with pytest.raises(HTTPException) as loi:
        book_service.so_sua_duoc_hoac_404(db, canh["so"].id, canh["tk_b"], profile, "write")
    assert loi.value.status_code == 404


def test_vua_quan_ly_vua_nguoi_xem_thi_danh_sach_KHONG_nhan_doi(db, canh, cap_quyen):
    """Một người khai ở cả hai vai là chuyện thường; sổ không được hiện hai dòng."""
    book_service.update_book(db, canh["so"].id, _sua(
        manager_ids=[canh["nv_b"].id], viewer_ids=[canh["nv_b"].id]), ACTOR)
    db.commit()

    assert _danh_sach(db, canh["tk_b"]) == [canh["so"].code]


# ── Cửa vào: được chia sổ thì KHÔNG cần vai trò trên danh mục Sổ ─────────────

def test_bo_loc_cho_qua_nguoi_duoc_chia_du_KHONG_co_vai_tro(db, canh):
    """Nửa BỘ LỌC của việc chia sổ (nửa CỬA nằm ở bài kiểm cuối tệp).

    Người được chia thường là nhân sự nghiệp vụ, KHÔNG có vai trò nào trên danh
    mục Sổ. Bộ lọc phải cho họ qua bằng chính tư cách thành viên.
    """
    from app.modules.doc_catalog.book_model import DocumentBookMember

    _, tk_ngoai = _nguoi(db, "SO_NGOAI", canh["cty_b"], 0)
    nv_ngoai = db.query(Employee).filter(Employee.code == "SO_NGOAI").one()
    db.add(DocumentBookMember(book_id=canh["so"].id, employee_id=nv_ngoai.id,
                              role=2, created_by=ACTOR, updated_by=ACTOR))
    db.commit()

    #  Không cấp vai trò `document_book` nào cho người này — đúng bối cảnh thật.
    assert get_perm_profile(db, tk_ngoai)["perms_union"].get("document_book") is None
    assert canh["so"].code in _danh_sach(db, tk_ngoai)


def test_nguoi_NGOAI_CUOC_van_khong_thay_gi(db, canh):
    """CẶP ĐỐI CHỨNG. Mở cửa cho người được chia không được biến nó thành cửa mở
    toang: người không có vai trò VÀ không phải thành viên vẫn phải thấy rỗng."""
    _, tk_la = _nguoi(db, "SO_LA", canh["cty_b"], 0)
    db.commit()

    assert get_perm_profile(db, tk_la)["perms_union"].get("document_book") is None
    assert _danh_sach(db, tk_la) == []


def test_nguoi_ngoai_cuoc_go_thang_id_len_URL_an_404(db, canh):
    from fastapi import HTTPException

    _, tk_la = _nguoi(db, "SO_LA2", canh["cty_b"], 0)
    db.commit()

    with pytest.raises(HTTPException) as loi:
        book_service.so_xem_duoc_hoac_404(
            db, canh["so"].id, tk_la, get_perm_profile(db, tk_la))
    assert loi.value.status_code == 404


def test_ba_cua_DOC_mo_cho_nguoi_dang_nhap_con_GHI_thi_khong(db):
    """⚠️ Bài kiểm giữ nửa CỬA của việc chia sổ — lỗ khách báo 25/08/2026.

    Ba endpoint đọc sổ từng gác bằng `require("document_book", "read")`, một câu
    hỏi thuần vai trò. Nhưng quyền xem sổ còn tới từ **chính bảng thành viên**:
    văn thư thêm ai đó vào ô «Người xem sổ» là đã quyết định cho người ấy xem.
    Người được chia không có vai trò nào trên danh mục Sổ nên ăn **403 ngay ở
    cửa**, trước khi bộ lọc kịp chạy — và kết luận là «chia sổ không có tác
    dụng». Cùng cái bẫy, cùng cách chữa với `document/controller.doc_reader`.

    Kiểm bằng cách ĐỌC MÃ chứ không gọi route: `httpx` không có trong container
    nên chưa dựng được `TestClient`. Đây là bài duy nhất trong tệp chạm tới lớp
    cửa — mấy bài kia gọi thẳng `dieu_kien_xem_so` nên đi vòng qua nó.

    Ranh giới của ngoại lệ quan trọng ngang bản thân nó: được cho xem một quyển
    sổ KHÔNG có nghĩa là được khai sổ mới hay xóa sổ của người khác.
    """
    import re

    from pathlib import Path

    import app as goi_app

    ma = (Path(goi_app.__file__).resolve().parent
          / "modules" / "doc_catalog" / "book_controller.py").read_text(encoding="utf-8")
    assert len(re.findall(r"Depends\(nguoi_doc_so\)", ma)) == 3, "đúng ba cửa ĐỌC"
    for hanh_dong in ("create", "write", "delete"):
        assert f'require("document_book", "{hanh_dong}")' in ma, hanh_dong
