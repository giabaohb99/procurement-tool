"""bao-CR-659 — danh mục phòng ban: phòng DÙNG CHUNG (công ty = 0) luôn hiện khi XEM.

Sự cố 23/10/2026: tài khoản NSU012 khai phạm vi bằng danh sách công ty, mà 26/27 phòng
trên prod khai công ty = 0 (phòng dùng chung) nên danh mục phòng ban chỉ còn đúng phòng
Kinh doanh AGC; ô lọc Bộ phận của thumua tự dính phòng đó, bảng rỗng (bao-CR-657).

Luật mới: ai có quyền XEM phòng ban thì luôn thấy thêm phòng dùng chung. Thao tác SỬA /
XÓA phòng vẫn lọc theo công ty chính như cũ, để quản trị công ty con không sửa được phòng
chung của tập đoàn.
"""
import pytest

from app.modules.department.model import Department


@pytest.fixture
def shared_dept(world):
    row = Department(code="CHUNG", name="Phòng dùng chung", company_id=0, is_active=True)
    world.db.add(row)
    world.db.commit()
    return row.id


def test_thu_hep_theo_cong_ty_van_thay_phong_dung_chung(world, shared_dept):
    a1 = world.grant("a1", "department", scope="all", inc_company=["A"])
    assert a1.sees(Department) == {world.dept["A.kt"], world.dept["A.mua"], shared_dept}


def test_pham_vi_cong_ty_cua_vai_tro_van_thay_phong_dung_chung(world, shared_dept):
    b1 = world.grant("b1", "department", scope="company")
    assert b1.sees(Department) == {world.dept["B.kt"], world.dept["B.hc"], shared_dept}


def test_sua_phong_khong_mo_rong_sang_phong_dung_chung(world, shared_dept):
    a1 = world.grant("a1", "department", scope="all", actions=("read", "write"),
                     inc_company=["A"])
    assert shared_dept not in a1.sees(Department, action="write")
    assert a1.sees(Department, action="write") == {world.dept["A.kt"], world.dept["A.mua"]}


def test_khong_co_quyen_xem_phong_ban_thi_khong_thay_gi(world, shared_dept):
    a2 = world.grant("a2", "purchase_request", scope="all")
    assert a2.sees(Department, entity="department") == set()
