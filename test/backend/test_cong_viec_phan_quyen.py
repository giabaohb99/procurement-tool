"""Phân hệ Công việc (CR-216 / W1) — khóa tầng THÀNH VIÊN.

`work_task` khai `PUBLIC` ở `SCOPE_FIELDS`, nghĩa là khuôn `apply_scope` KHÔNG
lọc gì cho phân hệ này: toàn bộ phạm vi dữ liệu do `membership_service` gánh.
Bộ test này là cái chốt cho thỏa thuận đó — nới lỏng chỗ nào ở đây là mở toang
việc của cả công ty.

Sáu bài bắt buộc theo `doc/erp/cong-viec/04-phan-quyen.md` §5 nằm ở đây; bài 7
(tập cha CR-215) thuộc W3, chưa tới.
"""
import pytest
from fastapi import HTTPException

from app.modules.work import group_service, list_service, task_service
from app.modules.work import schema
from app.modules.work.membership_service import (Actor, effective_role,
                                                 get_list_or_403,
                                                 visible_list_ids)
from app.modules.work.model import (WorkListMember, WorkMemberRole,
                                    WorkTaskStatus)
from app.modules.work.task_model import WorkTask

COMPANY = 1


def _nguoi(uid: int, emp_id: int, company_id: int = COMPANY) -> Actor:
    """Người thao tác giả lập — không cần tài khoản thật, service chỉ đọc ba số này."""
    return Actor(user_id=uid, employee_id=emp_id, company_id=company_id)


@pytest.fixture()
def chu(db):
    return _nguoi(1, 11)


@pytest.fixture()
def nguoi_ngoai(db):
    return _nguoi(2, 22)


def _tao_list(db, actor, name="Thu mua", group_id=None):
    return list_service.create_list(
        db, actor, schema.ListCreate(name=name, group_id=group_id))


def _tao_task(db, actor, list_id, title="Việc A", **kw):
    return task_service.create_task(
        db, actor, schema.TaskCreate(list_id=list_id, title=title, **kw))


# ── 1. Người ngoài bị chặn CẢ HAI đường ─────────────────────────────────────────

def test_nguoi_ngoai_khong_thay_list_va_khong_doc_duoc_task_theo_id(db, chu, nguoi_ngoai):
    """Bài khóa số 1 — lỗ `get_scoped` kinh điển.

    Không thấy list ở danh sách là chưa đủ: kẻ tò mò gõ thẳng id vào URL. Cả hai
    đường phải cùng chặn, và chặn bằng 403 chứ không 404 — phân biệt hai mã đó
    là đã xác nhận "id này có thật" cho người ngoài.
    """
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"])

    assert visible_list_ids(db, nguoi_ngoai.employee_id, COMPANY) == set()
    assert list_service.get_lists(db, nguoi_ngoai) == []

    with pytest.raises(HTTPException) as e1:
        get_list_or_403(db, nguoi_ngoai, lst["id"])
    assert e1.value.status_code == 403

    with pytest.raises(HTTPException) as e2:
        task_service.get_task(db, nguoi_ngoai, task["id"])
    assert e2.value.status_code == 403


def test_list_cua_phap_nhan_khac_khong_lot_qua_du_co_dong_thanh_vien(db, chu):
    """Mời chéo pháp nhân cũng không mở được cửa — `visible_list_ids` lọc `company_id`.

    Trường hợp này sinh ra từ dữ liệu bẩn (nhập tay, đổi pháp nhân của nhân sự),
    không phải từ thao tác bình thường; nhưng nếu lọt thì lọt im lặng.
    """
    lst = _tao_list(db, chu)
    nguoi_cty_khac = _nguoi(3, 33, company_id=99)
    db.add(WorkListMember(company_id=COMPANY, list_id=lst["id"],
                          employee_id=nguoi_cty_khac.employee_id,
                          role=int(WorkMemberRole.MEMBER)))
    db.commit()

    assert visible_list_ids(db, 33, 99) == set()
    with pytest.raises(HTTPException):
        get_list_or_403(db, nguoi_cty_khac, lst["id"])


# ── 2. Kế thừa từ nhóm ──────────────────────────────────────────────────────────

def test_thanh_vien_nhom_thay_list_tao_sau_do_trong_nhom(db, chu):
    """A-09: gán ở NHÓM là kế thừa xuống mọi list bên trong, kể cả list tạo SAU."""
    nhom = group_service.create_group(db, chu, schema.GroupCreate(name="Đội Thu mua"))
    ban = _nguoi(4, 44)
    group_service.add_member(db, chu, nhom["id"],
                             schema.MemberIn(employee_id=ban.employee_id,
                                             role=int(WorkMemberRole.MEMBER)))
    lst = _tao_list(db, chu, group_id=nhom["id"])

    assert lst["id"] in visible_list_ids(db, ban.employee_id, COMPANY)
    assert effective_role(db, ban.employee_id, lst["id"]) == int(WorkMemberRole.MEMBER)


def test_vai_tro_hieu_luc_lay_cai_cao_hon_khi_vua_moi_rieng_vua_ke_thua(db, chu):
    """Q9 — `min()` vì số nhỏ = quyền to.

    VIEWER mời riêng ở list + ADMIN kế thừa từ nhóm → hiệu lực là ADMIN. Nếu
    ngày nào đó ai đổi thành `max()` "cho an toàn", bài này đỏ ngay: nó biến
    người quản trị nhóm thành khách xem ở chính list của nhóm mình.
    """
    nhom = group_service.create_group(db, chu, schema.GroupCreate(name="Đội"))
    ban = _nguoi(5, 55)
    group_service.add_member(db, chu, nhom["id"],
                             schema.MemberIn(employee_id=ban.employee_id,
                                             role=int(WorkMemberRole.ADMIN)))
    lst = _tao_list(db, chu, group_id=nhom["id"])
    list_service.add_member(db, chu, lst["id"],
                            schema.MemberIn(employee_id=ban.employee_id,
                                            role=int(WorkMemberRole.VIEWER)))

    assert effective_role(db, ban.employee_id, lst["id"]) == int(WorkMemberRole.ADMIN)


def test_ke_thua_chay_qua_hai_cap_nhom(db, chu):
    """Nhóm ông → nhóm con → list: thành viên nhóm ông vẫn thấy list ở nhóm cháu."""
    ong = group_service.create_group(db, chu, schema.GroupCreate(name="Khối"))
    con = group_service.create_group(db, chu,
                                     schema.GroupCreate(name="Đội", parent_id=ong["id"]))
    ban = _nguoi(6, 66)
    group_service.add_member(db, chu, ong["id"],
                             schema.MemberIn(employee_id=ban.employee_id,
                                             role=int(WorkMemberRole.MEMBER)))
    lst = _tao_list(db, chu, group_id=con["id"])

    assert lst["id"] in visible_list_ids(db, ban.employee_id, COMPANY)


# ── 3. Bất biến MỘT chủ sở hữu ─────────────────────────────────────────────────

def test_chuyen_quyen_so_huu_giu_dung_mot_chu(db, chu):
    """A-04 — hạ chủ cũ xuống ADMIN và nâng chủ mới, trong một lượt."""
    lst = _tao_list(db, chu)
    nguoi_moi = _nguoi(7, 77)
    list_service.transfer_ownership(db, chu, lst["id"], nguoi_moi.employee_id)

    chu_so_huu = (db.query(WorkListMember)
                  .filter(WorkListMember.list_id == lst["id"],
                          WorkListMember.role == int(WorkMemberRole.OWNER)).all())
    assert len(chu_so_huu) == 1
    assert chu_so_huu[0].employee_id == nguoi_moi.employee_id
    assert effective_role(db, chu.employee_id, lst["id"]) == int(WorkMemberRole.ADMIN)


def test_khong_gan_thang_vai_tro_chu_so_huu_bang_duong_moi_thanh_vien(db, chu):
    """Mời thẳng role=OWNER là đường vòng đẻ ra hai chủ — phải bị chặn."""
    lst = _tao_list(db, chu)
    with pytest.raises(HTTPException):
        list_service.add_member(db, chu, lst["id"],
                                schema.MemberIn(employee_id=88,
                                                role=int(WorkMemberRole.OWNER)))


def test_quan_tri_khong_cap_duoc_vai_tro_cao_hon_chinh_minh(db, chu):
    """ADMIN không nâng ai lên ADMIN... được, nhưng không lên OWNER, và MEMBER
    thì không mời được ai — vòng lách quyền cổ điển."""
    lst = _tao_list(db, chu)
    quan_tri = _nguoi(8, 99)
    list_service.add_member(db, chu, lst["id"],
                            schema.MemberIn(employee_id=quan_tri.employee_id,
                                            role=int(WorkMemberRole.ADMIN)))
    with pytest.raises(HTTPException):
        list_service.add_member(db, quan_tri, lst["id"],
                                schema.MemberIn(employee_id=100,
                                                role=int(WorkMemberRole.OWNER)))


def test_khong_go_duoc_chu_so_huu(db, chu):
    lst = _tao_list(db, chu)
    m = (db.query(WorkListMember)
         .filter(WorkListMember.list_id == lst["id"]).first())
    with pytest.raises(HTTPException):
        list_service.remove_member(db, chu, lst["id"], m.id)


# ── 4. Chặn cấp 3 ──────────────────────────────────────────────────────────────

def test_nhom_khong_long_qua_hai_cap(db, chu):
    ong = group_service.create_group(db, chu, schema.GroupCreate(name="Khối"))
    con = group_service.create_group(db, chu,
                                     schema.GroupCreate(name="Đội", parent_id=ong["id"]))
    with pytest.raises(HTTPException) as e:
        group_service.create_group(db, chu,
                                   schema.GroupCreate(name="Tổ", parent_id=con["id"]))
    assert e.value.status_code == 400


def test_viec_con_khong_de_ra_viec_chau(db, chu):
    """C-05 — hai cấp là hết. Cấp ba làm hỏng mọi phép đếm n/m của thẻ cha."""
    lst = _tao_list(db, chu)
    cha = _tao_task(db, chu, lst["id"])
    con = task_service.create_task(
        db, chu, schema.TaskCreate(title="Việc con", parent_id=cha["id"]))
    with pytest.raises(HTTPException):
        task_service.create_task(
            db, chu, schema.TaskCreate(title="Việc cháu", parent_id=con["id"]))


# ── 5. Việc con vô hình ngoài panel cha, xóa mềm không lộ ──────────────────────

def test_viec_con_khong_hien_thanh_the_tren_kanban_nhung_dem_vao_n_tren_m(db, chu):
    """Q10 chốt "bản đầu tuyệt đối ẩn": việc con chỉ sống trong panel của cha."""
    lst = _tao_list(db, chu)
    cha = _tao_task(db, chu, lst["id"])
    con = task_service.create_task(
        db, chu, schema.TaskCreate(title="Bước 1", parent_id=cha["id"]))
    task_service.create_task(db, chu, schema.TaskCreate(title="Bước 2", parent_id=cha["id"]))
    task_service.update_task(db, chu, con["id"],
                             schema.TaskUpdate(status=int(WorkTaskStatus.DONE)))

    bang = task_service.board(db, chu, lst["id"])
    assert [t["id"] for t in bang["tasks"]] == [cha["id"]]
    the_cha = bang["tasks"][0]
    assert (the_cha["subtask_done"], the_cha["subtask_total"]) == (1, 2)
    #  Việc con không thuộc cột nào — có `section_id` là nó lọt ra kanban.
    assert db.get(WorkTask, con["id"]).section_id is None


def test_xoa_mem_bien_khoi_moi_query_thuong_va_keo_theo_viec_con(db, chu):
    """B-09 — dòng còn trong CSDL nhưng không màn nào thấy; việc con chết theo cha."""
    lst = _tao_list(db, chu)
    cha = _tao_task(db, chu, lst["id"])
    con = task_service.create_task(
        db, chu, schema.TaskCreate(title="Bước 1", parent_id=cha["id"]))

    task_service.delete_task(db, chu, cha["id"])

    assert task_service.board(db, chu, lst["id"])["tasks"] == []
    assert db.get(WorkTask, cha["id"]).deleted_at is not None
    assert db.get(WorkTask, con["id"]).deleted_at is not None
    with pytest.raises(HTTPException):
        task_service.get_task(db, chu, cha["id"])


def test_thanh_vien_thuong_chi_xoa_duoc_viec_minh_tao(db, chu):
    """Ma trận §3: MEMBER xóa việc của mình, ADMIN/OWNER xóa việc bất kỳ."""
    lst = _tao_list(db, chu)
    nhan_vien = _nguoi(9, 111)
    list_service.add_member(db, chu, lst["id"],
                            schema.MemberIn(employee_id=nhan_vien.employee_id,
                                            role=int(WorkMemberRole.MEMBER)))
    cua_chu = _tao_task(db, chu, lst["id"], title="Của chủ")
    cua_nv = _tao_task(db, nhan_vien, lst["id"], title="Của nhân viên")

    with pytest.raises(HTTPException) as e:
        task_service.delete_task(db, nhan_vien, cua_chu["id"])
    assert e.value.status_code == 403

    task_service.delete_task(db, nhan_vien, cua_nv["id"])   # việc mình tạo thì được
    task_service.delete_task(db, chu, cua_chu["id"])        # chủ xóa được việc người khác


def test_khach_xem_khong_tao_duoc_viec(db, chu):
    """VIEWER là đọc, chấm hết (§3)."""
    lst = _tao_list(db, chu)
    khach = _nguoi(10, 222)
    list_service.add_member(db, chu, lst["id"],
                            schema.MemberIn(employee_id=khach.employee_id,
                                            role=int(WorkMemberRole.VIEWER)))
    with pytest.raises(HTTPException) as e:
        _tao_task(db, khach, lst["id"])
    assert e.value.status_code == 403


def test_list_da_luu_tru_thi_doc_duoc_nhung_khong_ghi_duoc(db, chu):
    """04 §2 — lưu trữ là đóng băng, không phải xóa."""
    lst = _tao_list(db, chu)
    list_service.archive_list(db, chu, lst["id"])

    assert list_service.get_list(db, chu, lst["id"])["is_archived"] == 1
    with pytest.raises(HTTPException) as e:
        _tao_task(db, chu, lst["id"])
    assert e.value.status_code == 400
