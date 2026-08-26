"""CHIA SỔ VĂN BẢN — mấy ca BIÊN mà `test_chia_so_van_ban.py` chưa chạm tới.

Khách báo lại 26/08/2026: chia sổ xong người được chia **vẫn không thấy sổ ở
trang của mình**. Lần này thủ phạm nằm ở CỬA GIAO DIỆN (mục menu «Sổ văn bản»
gác `document_book.read`, xem `frontend-v2/src/modules/document/routes.test.ts`)
chứ không phải ở đây — nhưng đúng dịp soi lại toàn bộ đường quyền của sổ, và
mấy ca dưới đây trước giờ chưa ai kiểm:

  - sổ NGỪNG DÙNG · sổ chưa gán pháp nhân · nhân sự đã nghỉ;
  - người được chia mà tài khoản có phạm vi `own` (hẹp nhất);
  - chia cho nhiều người, gỡ đúng một người;
  - sổ bị xóa / id không tồn tại;
  - `dieu_kien_xem_so` trả `None` (thấy tất) thì không được nuốt mất ai.

Gọi thẳng hàm lọc chứ không qua HTTP — bài kiểm nhắm vào mệnh đề WHERE sinh ra.
"""
import pytest
from fastapi import HTTPException

from app.core.auth import get_perm_profile
from app.modules.company.model import Company
from app.modules.doc_catalog import book_service
from app.modules.doc_catalog.book_model import DocumentBook, DocumentBookMember
from app.modules.doc_catalog.book_schema import DocumentBookCreate, DocumentBookUpdate
from app.modules.employee.model import Employee
from app.modules.user.model import User

ACTOR = 1


def _nguoi(db, ma: str, company_id: int, dept_id: int = 0, is_active: bool = True):
    employee = Employee(code=ma, full_name=f"Người {ma}", company_id=company_id,
                        department_id=dept_id, is_active=is_active)
    db.add(employee)
    db.flush()
    user = User(email=f"{ma.lower()}@test.local", employee_id=employee.id,
                password_hash="x", is_active=True)
    db.add(user)
    db.flush()
    return employee, user


def _so(db, name="Sổ thử", kind=1, company_id=0, manager_ids=None, viewer_ids=None):
    return book_service.create_book(db, DocumentBookCreate(
        name=name, kind=kind, company_id=company_id,
        manager_ids=manager_ids or [1], viewer_ids=viewer_ids or [],
    ), ACTOR)


def _danh_sach(db, user):
    """Đúng câu truy vấn mà endpoint danh sách chạy."""
    dieu_kien = book_service.dieu_kien_xem_so(user, get_perm_profile(db, user))
    q = db.query(DocumentBook)
    if dieu_kien is not None:
        q = q.filter(dieu_kien)
    return sorted(row.code for row in q.all())


def _sua(**doi):
    return DocumentBookUpdate(**doi)


@pytest.fixture()
def cty_khac(db, seed):
    khac = Company(code="CTX", name="Công ty X", issue_code="CTX", level=2, is_active=True)
    db.add(khac)
    db.flush()
    db.commit()
    return khac


# ── Người được chia ở phạm vi HẸP NHẤT ──────────────────────────────────────
def test_pham_vi_own_van_thay_so_duoc_chia(db, seed, cty_khac, cap_quyen):
    """`own` là phạm vi hẹp nhất: chỉ thấy thứ do chính mình tạo.

    Người được chia sổ hầu hết rơi vào đây. Chia đích danh phải THẮNG được cả
    phạm vi hẹp nhất, nếu không thì ô «Người xem sổ» chỉ có tác dụng với đúng
    những người vốn đã xem được.
    """
    nv, tk = _nguoi(db, "SO_OWN", cty_khac.id)
    cap_quyen(tk.id, "document_book", scope="own", read=True)
    so = _so(db, company_id=seed.company_id, manager_ids=[seed.emp_tp_id])
    db.commit()

    assert _danh_sach(db, tk) == []

    book_service.update_book(db, so.id, _sua(viewer_ids=[nv.id]), ACTOR)
    db.commit()
    assert _danh_sach(db, tk) == [so.code]


def test_khong_co_grant_nao_van_thay_so_duoc_chia(db, seed, cty_khac):
    """Không một vai trò nào trên danh mục Sổ — đúng bối cảnh nhân sự nghiệp vụ.

    `scope_condition` khi thiếu grant trả `false()` (B-07/CR-131 chặn hết), nên
    nhánh OR với tư cách thành viên là đường sống DUY NHẤT của họ.
    """
    nv, tk = _nguoi(db, "SO_KHONG_QUYEN", cty_khac.id)
    so = _so(db, company_id=seed.company_id, manager_ids=[seed.emp_tp_id],
             viewer_ids=[nv.id])
    db.commit()

    assert get_perm_profile(db, tk)["perms_union"].get("document_book") is None
    assert _danh_sach(db, tk) == [so.code]


# ── Trạng thái của sổ ────────────────────────────────────────────────────────
def test_so_NGUNG_DUNG_van_hien_cho_nguoi_duoc_chia(db, seed, cty_khac):
    """Đóng sổ là ngừng cấp số mới, KHÔNG phải giấu sổ đi.

    Sổ cũ vẫn phải tra cứu được — đó là toàn bộ lý do người ta giữ sổ lại thay
    vì xóa. Bộ lọc ẩn/hiện là việc của thanh công cụ, không phải của lớp quyền.
    """
    nv, tk = _nguoi(db, "SO_NGUNG", cty_khac.id)
    so = _so(db, company_id=seed.company_id, manager_ids=[seed.emp_tp_id],
             viewer_ids=[nv.id])
    book_service.update_book(db, so.id, _sua(is_active=False), ACTOR)
    db.commit()

    assert _danh_sach(db, tk) == [so.code]


def test_so_CHUA_GAN_PHAP_NHAN_khong_no_va_van_chia_duoc(db, cty_khac):
    """`company_id = 0` là dữ liệu cũ có thật (sổ khai trước khi bắt buộc pháp nhân).

    Điều kiện phạm vi so `company_id` với danh sách pháp nhân được xem; số 0
    không khớp cái nào — nhưng nhánh thành viên vẫn phải kéo được sổ về.
    """
    nv, tk = _nguoi(db, "SO_MO_COI", cty_khac.id)
    so = _so(db, company_id=0, manager_ids=[1], viewer_ids=[nv.id])
    db.commit()

    assert _danh_sach(db, tk) == [so.code]


def test_nhan_su_da_NGHI_thi_khong_con_thay(db, seed, cty_khac, cap_quyen):
    """Nghỉ việc thì khóa TÀI KHOẢN, còn dòng thành viên sổ vẫn nằm đó.

    Bài này chốt hành vi ĐANG CÓ để ai đổi thì biết mình đang đổi cái gì: lớp
    quyền của sổ KHÔNG tự xét `Employee.is_active` — chặn đăng nhập mới là chỗ
    chặn. Muốn đổi thành "nghỉ là mất quyền xem sổ" thì phải sửa có chủ đích.
    """
    nv, tk = _nguoi(db, "SO_NGHI", cty_khac.id)
    so = _so(db, company_id=seed.company_id, manager_ids=[seed.emp_tp_id],
             viewer_ids=[nv.id])
    nv.is_active = False
    db.commit()

    assert _danh_sach(db, tk) == [so.code]


# ── Nhiều người, nhiều sổ ────────────────────────────────────────────────────
def test_go_MOT_nguoi_khong_lam_nguoi_kia_mat_quyen(db, seed, cty_khac):
    """Ghi đè danh sách thành viên là xóa sạch rồi thêm lại (`_replace_members`).

    Gọi `update_book` với `viewer_ids` thiếu một người là đúng ý "bỏ người đó",
    nhưng phải giữ nguyên những người còn lại — đây là chỗ dễ sót nhất.
    """
    nv1, tk1 = _nguoi(db, "SO_N1", cty_khac.id)
    nv2, tk2 = _nguoi(db, "SO_N2", cty_khac.id)
    so = _so(db, company_id=seed.company_id, manager_ids=[seed.emp_tp_id],
             viewer_ids=[nv1.id, nv2.id])
    db.commit()

    assert _danh_sach(db, tk1) == [so.code]
    assert _danh_sach(db, tk2) == [so.code]

    book_service.update_book(db, so.id, _sua(viewer_ids=[nv2.id]), ACTOR)
    db.commit()

    assert _danh_sach(db, tk1) == []
    assert _danh_sach(db, tk2) == [so.code]


def test_chia_NHIEU_so_thi_thay_du_ca_ba_loai(db, seed, cty_khac):
    """Ba loại sổ (đến · đi · nội bộ) đi qua cùng một điều kiện — không loại nào rớt."""
    nv, tk = _nguoi(db, "SO_BA_LOAI", cty_khac.id)
    ma = []
    for kind in (1, 2, 3):
        so = _so(db, name=f"Sổ loại {kind}", kind=kind, company_id=seed.company_id,
                 manager_ids=[seed.emp_tp_id], viewer_ids=[nv.id])
        ma.append(so.code)
    db.commit()

    assert _danh_sach(db, tk) == sorted(ma)


def test_khong_chia_so_nao_thi_danh_sach_RONG_chu_khong_no(db, cty_khac):
    _, tk = _nguoi(db, "SO_TRANG", cty_khac.id)
    db.commit()
    assert _danh_sach(db, tk) == []


# ── Thấy TẤT CẢ (điều kiện = None) ───────────────────────────────────────────
def test_pham_vi_ALL_thi_dieu_kien_la_None_va_thay_het(db, seed, cty_khac, cap_quyen):
    """`scope_condition` trả `None` nghĩa là "không lọc gì".

    Nhánh OR phải nhường đường: `or_(None, ...)` là lỗi lập trình, mà lỡ tay ghép
    vào thì người quản trị lại hóa ra chỉ thấy sổ mình là thành viên.
    """
    _, tk = _nguoi(db, "SO_ALL", cty_khac.id)
    cap_quyen(tk.id, "document_book", scope="all", read=True)
    so_a = _so(db, name="Sổ A", company_id=seed.company_id, manager_ids=[seed.emp_tp_id])
    so_b = _so(db, name="Sổ B", company_id=cty_khac.id, manager_ids=[seed.emp_tp_id])
    db.commit()

    assert book_service.dieu_kien_xem_so(tk, get_perm_profile(db, tk)) is None
    assert _danh_sach(db, tk) == sorted([so_a.code, so_b.code])


# ── Đường mở MỘT quyển ───────────────────────────────────────────────────────
def test_id_khong_ton_tai_ra_404_chu_khong_no(db, cty_khac):
    _, tk = _nguoi(db, "SO_404", cty_khac.id)
    db.commit()

    with pytest.raises(HTTPException) as loi:
        book_service.so_xem_duoc_hoac_404(db, 999999, tk, get_perm_profile(db, tk))
    assert loi.value.status_code == 404


def test_so_da_xoa_thi_dong_thanh_vien_khong_keo_ai_vao_duoc(db, seed, cty_khac):
    """Xóa sổ phải dọn luôn bảng thành viên, nếu không dòng mồ côi sẽ trỏ vào một
    id mà sau này sổ khác có thể tái dùng."""
    nv, tk = _nguoi(db, "SO_DA_XOA", cty_khac.id)
    so = _so(db, company_id=seed.company_id, manager_ids=[seed.emp_tp_id],
             viewer_ids=[nv.id])
    book_id = so.id
    book_service.delete_book(db, book_id)
    db.commit()

    con_lai = db.query(DocumentBookMember).filter(
        DocumentBookMember.book_id == book_id).count()
    assert con_lai == 0
    assert _danh_sach(db, tk) == []


def test_nguoi_duoc_chia_mo_duoc_BO_DEM_cua_so(db, seed, cty_khac):
    """Trang chi tiết sổ có khối «Bộ đếm» đi qua đúng cửa `so_xem_duoc_hoac_404`."""
    nv, tk = _nguoi(db, "SO_DEM", cty_khac.id)
    so = _so(db, company_id=seed.company_id, manager_ids=[seed.emp_tp_id],
             viewer_ids=[nv.id])
    db.commit()

    profile = get_perm_profile(db, tk)
    assert book_service.so_xem_duoc_hoac_404(db, so.id, tk, profile).id == so.id
    assert book_service.issued_count(db, so) == 0


# ── Vai QUẢN LÝ cũng là một đường thấy sổ ────────────────────────────────────
def test_nguoi_QUAN_LY_so_thay_so_du_khong_co_vai_tro(db, seed, cty_khac):
    """Cử ai làm người quản lý sổ mà họ không thấy sổ đâu thì lời cử đó vô nghĩa."""
    nv, tk = _nguoi(db, "SO_QL", cty_khac.id)
    so = _so(db, company_id=seed.company_id, manager_ids=[nv.id])
    db.commit()

    assert _danh_sach(db, tk) == [so.code]
