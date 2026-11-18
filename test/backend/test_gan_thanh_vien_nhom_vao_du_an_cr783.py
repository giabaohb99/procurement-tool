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
