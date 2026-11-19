"""duoc-CR-783 — tạo dự án trong nhóm thì chép thành viên nhóm thành thành viên riêng của dự án.

Anh Được báo 18/11/2026: người trong nhóm dự án có quyền trên dự án con (kế thừa) nhưng không hiện là thành viên của
dự án — hộp Quản lý dự án và ô chọn người phụ trách không thấy họ. Hộp tạo dự án nay có ô tick (bật sẵn) + chọn người.
"""
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.modules.work import group_service, list_service, schema
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkListMember, WorkMemberRole

COMPANY = 1
ME = 11
AN = 21
BINH = 22
CUONG = 23
NGUOI_LA = 99


@pytest.fixture()
def toi(db):
    return Actor(user_id=1, employee_id=ME, company_id=COMPANY)


@pytest.fixture()
def nhom(db, toi):
    grp = group_service.create_group(db, toi, schema.GroupCreate(name="DX"))
    group_service.add_member(db, toi, grp["id"], schema.MemberIn(employee_id=AN, role=int(WorkMemberRole.ADMIN)))
    group_service.add_member(db, toi, grp["id"], schema.MemberIn(employee_id=BINH, role=int(WorkMemberRole.MEMBER)))
    group_service.add_member(db, toi, grp["id"], schema.MemberIn(employee_id=CUONG, role=int(WorkMemberRole.VIEWER)))
    return grp


def _vai_tro(db, list_id) -> dict[int, int]:
    rows = db.query(WorkListMember).filter(WorkListMember.list_id == list_id).all()
    return {r.employee_id: int(r.role) for r in rows}


def test_chep_dung_nguoi_duoc_chon_va_giu_vai_tro_o_nhom(db, toi, nhom):
    lst = list_service.create_list(db, toi, schema.ListCreate(
        name="ERP v3", group_id=nhom["id"], member_employee_ids=[AN, CUONG]))
    vai_tro = _vai_tro(db, lst["id"])
    assert vai_tro == {ME: int(WorkMemberRole.OWNER), AN: int(WorkMemberRole.ADMIN),
                       CUONG: int(WorkMemberRole.VIEWER)}
    #  Bình bị bỏ chọn: không có dòng riêng (vẫn thấy dự án nhờ kế thừa từ nhóm — đó là luật cũ, không đổi).
    assert BINH not in vai_tro


def test_chu_nhom_vao_du_an_lam_quan_tri_vi_du_an_chi_co_mot_chu(db, nhom):
    #  Người tạo nhóm (chủ nhóm) là ME; người khác tạo dự án trong nhóm và chọn cả chủ nhóm.
    an = Actor(user_id=2, employee_id=AN, company_id=COMPANY)
    lst = list_service.create_list(db, an, schema.ListCreate(
        name="Kho", group_id=nhom["id"], member_employee_ids=[ME, BINH]))
    vai_tro = _vai_tro(db, lst["id"])
    assert vai_tro[AN] == int(WorkMemberRole.OWNER)
    assert vai_tro[ME] == int(WorkMemberRole.ADMIN)
    assert list(vai_tro.values()).count(int(WorkMemberRole.OWNER)) == 1


def test_bo_qua_chinh_nguoi_tao_va_id_trung_lap(db, toi, nhom):
    lst = list_service.create_list(db, toi, schema.ListCreate(
        name="CRM", group_id=nhom["id"], member_employee_ids=[ME, AN, AN, 0]))
    assert _vai_tro(db, lst["id"]) == {ME: int(WorkMemberRole.OWNER), AN: int(WorkMemberRole.ADMIN)}


def test_chan_nguoi_ngoai_nhom_va_khong_de_lai_du_an_do_dang(db, toi, nhom):
    with pytest.raises(HTTPException) as loi:
        list_service.create_list(db, toi, schema.ListCreate(
            name="Lén mời", group_id=nhom["id"], member_employee_ids=[AN, NGUOI_LA]))
    assert loi.value.status_code == 400
    db.rollback()
    assert not db.query(WorkListMember).filter(WorkListMember.employee_id == NGUOI_LA).count()


def test_khong_gui_danh_sach_thi_giu_hanh_vi_cu(db, toi, nhom):
    #  Người gọi cũ (công cụ MCP, lập kế hoạch AI) không gửi trường mới: chỉ người tạo là thành viên riêng.
    lst = list_service.create_list(db, toi, schema.ListCreate(name="Cũ", group_id=nhom["id"]))
    assert _vai_tro(db, lst["id"]) == {ME: int(WorkMemberRole.OWNER)}


def test_du_an_le_bo_qua_danh_sach_thanh_vien_nhom(db, toi, nhom):
    #  Không có nhóm thì không có gì để chép — kể cả khi giao diện lỡ gửi danh sách.
    lst = list_service.create_list(db, toi, schema.ListCreate(name="Lẻ", member_employee_ids=[AN]))
    assert _vai_tro(db, lst["id"]) == {ME: int(WorkMemberRole.OWNER)}


def test_chan_danh_sach_qua_dai_o_tang_schema():
    with pytest.raises(ValidationError):
        schema.ListCreate(name="X", group_id=1, member_employee_ids=list(range(1, 502)))


# ── Chuông mời + nút Mời lại (anh Được 19/11/2026: "mời vào dự án mà chuông không thấy gì") ──────────────────────────

def _co_tai_khoan(db, cap_quyen, *pairs):
    """Gắn tài khoản đang hoạt động + quyền đọc Công việc — chuông chỉ kêu cho người có tài khoản và mở được link."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    for uid, eid in pairs:
        db.add(Employee(id=eid, code=f"NV{eid}", full_name=f"Người {eid}", company_id=COMPANY))
        db.add(User(id=uid, email=f"u{uid}@dego.vn", employee_id=eid, is_active=True))
        cap_quyen(uid, "work_task", read=True, write=True, create=True)
    db.commit()


def _chuong(db, user_id):
    from app.modules.notification.model import Notification

    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.id).all()


def test_moi_vao_du_an_keu_chuong_nguoi_moi_khong_keu_khi_doi_vai_tro(db, toi, cap_quyen):
    _co_tai_khoan(db, cap_quyen, (1, ME), (2, AN))
    lst = list_service.create_list(db, toi, schema.ListCreate(name="Kho Quý 4"))
    list_service.add_member(db, toi, lst["id"], schema.MemberIn(employee_id=AN))
    chuong = _chuong(db, 2)
    assert len(chuong) == 1
    assert chuong[0].title == "Bạn được mời vào dự án"
    assert "Kho Quý 4" in chuong[0].body and chuong[0].link == f"/project/lists/{lst['id']}"
    #  Đổi vai trò người đã có: không phải lời mời, không kêu thêm.
    list_service.add_member(db, toi, lst["id"], schema.MemberIn(employee_id=AN, role=int(WorkMemberRole.ADMIN)))
    assert len(_chuong(db, 2)) == 1
    #  Không bao giờ báo cho chính người mời.
    assert _chuong(db, 1) == []


def test_moi_vao_nhom_keu_chuong(db, toi, cap_quyen):
    _co_tai_khoan(db, cap_quyen, (1, ME), (3, BINH))
    grp = group_service.create_group(db, toi, schema.GroupCreate(name="IDA"))
    group_service.add_member(db, toi, grp["id"], schema.MemberIn(employee_id=BINH))
    chuong = _chuong(db, 3)
    assert [c.title for c in chuong] == ["Bạn được mời vào nhóm dự án"]
    assert "IDA" in chuong[0].body


def test_gan_san_luc_tao_du_an_trong_nhom_cung_keu_chuong(db, toi, nhom, cap_quyen):
    _co_tai_khoan(db, cap_quyen, (1, ME), (2, AN), (3, BINH))
    #  Chuông mời vào NHÓM ở fixture không tính — xóa đi để chỉ đếm chuông của lần tạo dự án.
    from app.modules.notification.model import Notification
    db.query(Notification).delete()
    db.commit()
    list_service.create_list(db, toi, schema.ListCreate(name="ERP v3", group_id=nhom["id"], member_employee_ids=[AN]))
    assert [c.title for c in _chuong(db, 2)] == ["Bạn được mời vào dự án"]
    assert _chuong(db, 3) == []


def test_moi_lai_gui_chuong_nhac_va_chan_dong_khong_thuoc_du_an(db, toi, cap_quyen):
    from app.modules.work import member_invite_service

    _co_tai_khoan(db, cap_quyen, (1, ME), (2, AN))
    lst = list_service.create_list(db, toi, schema.ListCreate(name="Kho"))
    m = list_service.add_member(db, toi, lst["id"], schema.MemberIn(employee_id=AN))
    assert member_invite_service.reinvite_list_member(db, toi, lst["id"], m["id"]) == 1
    assert [c.title for c in _chuong(db, 2)] == ["Bạn được mời vào dự án", "Nhắc lời mời vào dự án"]
    khac = list_service.create_list(db, toi, schema.ListCreate(name="Khác"))
    with pytest.raises(HTTPException) as loi:
        member_invite_service.reinvite_list_member(db, toi, khac["id"], m["id"])
    assert loi.value.status_code == 404


def test_chi_quan_tri_moi_bam_moi_lai(db, toi, cap_quyen):
    from app.modules.work import member_invite_service

    _co_tai_khoan(db, cap_quyen, (1, ME), (2, AN), (3, BINH))
    lst = list_service.create_list(db, toi, schema.ListCreate(name="Kho"))
    list_service.add_member(db, toi, lst["id"], schema.MemberIn(employee_id=AN))
    m_binh = list_service.add_member(db, toi, lst["id"], schema.MemberIn(employee_id=BINH))
    an = Actor(user_id=2, employee_id=AN, company_id=COMPANY)
    with pytest.raises(HTTPException) as loi:
        member_invite_service.reinvite_list_member(db, an, lst["id"], m_binh["id"])
    assert loi.value.status_code == 403


def test_dong_thanh_vien_tra_ngay_moi(db, toi):
    lst = list_service.create_list(db, toi, schema.ListCreate(name="Kho"))
    m = list_service.add_member(db, toi, lst["id"], schema.MemberIn(employee_id=AN))
    assert m["invited_at"]


def test_khong_co_quyen_doc_cong_viec_thi_khong_nhan_chuong_moi(db, toi, cap_quyen):
    """Bấm chuông mà link trả 403 thì tệ hơn không có chuông — cùng cổng với chuông giao việc."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    db.add(Employee(id=AN, code="NV21", full_name="An", company_id=COMPANY))
    db.add(User(id=2, email="u2@dego.vn", employee_id=AN, is_active=True))
    db.commit()
    cap_quyen(2, "work_task", read=False)
    lst = list_service.create_list(db, toi, schema.ListCreate(name="Kho"))
    list_service.add_member(db, toi, lst["id"], schema.MemberIn(employee_id=AN))
    assert _chuong(db, 2) == []
