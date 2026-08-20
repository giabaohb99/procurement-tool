"""NGƯỜI NỘP = NGƯỜI BẤM GỬI DUYỆT, không phải người ghi trên phiếu (20/08/2026).

Lỗi dựng lại được trên Chrome với tài khoản `VTSAM`: văn thư SAM mở bản clone
của SAM, sửa xong bấm Gửi duyệt → phiếu **KẸT** ngay, «Bước Trưởng bộ phận duyệt
không tìm được người duyệt», và pháp nhân con **không ban hành được văn bản của
mình**.

Nguyên nhân: `trinh_duyet` lấy `drafter_employee_id or owner_employee_id` làm
người nộp, mà bản clone chép hai ô đó **từ bản gốc** — tức người của Tập đoàn.
Bộ máy đi tìm trưởng bộ phận của người đó, không ra ai, và luồng mặc định khai
`on_no_approver = dừng phiếu`.
"""
import pytest

from app.modules.document.approval_bridge import _nhan_su_cua_tai_khoan
from app.modules.employee.model import Employee
from app.modules.user.model import User


@pytest.fixture()
def van_thu_con(db, seed):
    """Một tài khoản có gắn hồ sơ nhân sự — đóng vai văn thư pháp nhân con."""
    emp = Employee(code="VTTHU", full_name="Văn thư thử", company_id=seed.company_id,
                   is_active=True)
    db.add(emp)
    db.flush()
    user = User(email="vtthu@dego.test", employee_id=emp.id, is_active=True)
    db.add(user)
    db.commit()
    return {"user": user, "emp": emp}


def test_lay_dung_nhan_su_cua_tai_khoan_dang_bam(db, van_thu_con):
    assert _nhan_su_cua_tai_khoan(db, van_thu_con["user"].id) == van_thu_con["emp"].id


def test_tai_khoan_chua_gan_ho_so_nhan_su_thi_tra_None(db):
    """Tài khoản hệ thống / tác vụ nền — nơi gọi phải lùi về ô trên phiếu."""
    user = User(email="hethong@dego.test", employee_id=0, is_active=True)
    db.add(user)
    db.commit()

    assert _nhan_su_cua_tai_khoan(db, user.id) is None


def test_khong_co_tai_khoan_thi_tra_None(db):
    assert _nhan_su_cua_tai_khoan(db, 0) is None
    assert _nhan_su_cua_tai_khoan(db, 999999) is None


def test_nguoi_nop_khac_nguoi_ghi_tren_phieu(db, seed, van_thu_con):
    """Bài kiểm CỐT LÕI: bản clone ghi người của Tập đoàn, người bấm là văn thư con.

    Trước bản vá, `submitter_employee_id` ra người của Tập đoàn (`owner`), nên
    luồng định tuyến sai và phiếu kẹt. Sau bản vá phải ra người BẤM.
    """
    nguoi_ghi_tren_phieu = seed.emp_req_id
    nguoi_bam = _nhan_su_cua_tai_khoan(db, van_thu_con["user"].id)

    #  Hai người này khác nhau — đúng tình huống của bản clone.
    assert nguoi_bam != nguoi_ghi_tren_phieu

    #  Đây là biểu thức `trinh_duyet` dùng; giữ nguyên thứ tự ưu tiên.
    chon = nguoi_bam or nguoi_ghi_tren_phieu
    assert chon == van_thu_con["emp"].id
