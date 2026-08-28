"""Phân hệ Công việc (CR-216 / W1) — luật nghiệp vụ của task, cột, tag, nhãn.

Phần phân quyền nằm ở `test_cong_viec_phan_quyen.py`. Tệp này chỉ soi những chỗ
dữ liệu dễ lệch âm thầm: tag/nhãn của list khác gắn nhầm sang, cột xóa để lại
việc mồ côi, hoàn thành rồi mở lại còn sót dấu, một người vừa PIC vừa theo dõi.
"""
import pytest
from fastapi import HTTPException

from app.modules.work import list_config_service as cfg
from app.modules.work import list_service, schema, task_service
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkAssigneeKind, WorkTaskStatus
from app.modules.work.task_model import WorkTask

COMPANY = 1


@pytest.fixture()
def owner(db):
    return Actor(user_id=1, employee_id=11, company_id=COMPANY)


@pytest.fixture()
def work_list(db, owner):
    return list_service.create_list(db, owner, schema.ListCreate(name="Thu mua"))


def _create_task(db, owner, list_id, title="Việc A", **kw):
    return task_service.create_task(
        db, owner, schema.TaskCreate(list_id=list_id, title=title, **kw))


# ── Cột kanban ─────────────────────────────────────────────────────────────────

def test_tao_list_la_co_san_ba_cot_va_viec_moi_roi_vao_cot_dau(db, owner, work_list):
    """Không có cột sẵn thì người dùng mở bảng ra thấy trang trắng, chẳng kéo đi đâu."""
    sections = cfg.get_sections(db, owner, work_list["id"])
    assert [c["name"] for c in sections] == ["Cần làm", "Đang làm", "Hoàn thành"]

    t = _create_task(db, owner, work_list["id"])
    assert t["section_id"] == sections[0]["id"]


def test_xoa_cot_con_viec_thi_bat_chon_cot_nhan(db, owner, work_list):
    """Việc mồ côi (`section_id` NULL) là việc BIẾN MẤT khỏi kanban mà vẫn nằm
    trong CSDL — người dùng tưởng mất dữ liệu."""
    sections = cfg.get_sections(db, owner, work_list["id"])
    t = _create_task(db, owner, work_list["id"])

    with pytest.raises(HTTPException) as e:
        cfg.delete_section(db, owner, sections[0]["id"], None)
    assert e.value.status_code == 400

    cfg.delete_section(db, owner, sections[0]["id"], sections[1]["id"])
    assert db.get(WorkTask, t["id"]).section_id == sections[1]["id"]


def test_khong_keo_duoc_viec_sang_cot_cua_list_khac(db, owner, work_list):
    """Cột của list B không có nghĩa gì ở list A; nhận bừa là thẻ mất tích."""
    list_b = list_service.create_list(db, owner, schema.ListCreate(name="Kho"))
    cot_b = cfg.get_sections(db, owner, list_b["id"])[0]
    t = _create_task(db, owner, work_list["id"])

    with pytest.raises(HTTPException) as e:
        task_service.update_task(db, owner, t["id"],
                                 schema.TaskUpdate(section_id=cot_b["id"]))
    assert e.value.status_code == 400


def test_cot_xoa_roi_thi_khong_con_trong_danh_sach(db, owner, work_list):
    sections = cfg.get_sections(db, owner, work_list["id"])
    cfg.delete_section(db, owner, sections[2]["id"], None)   # cột rỗng, xóa thẳng được
    assert [c["name"] for c in cfg.get_sections(db, owner, work_list["id"])] == ["Cần làm", "Đang làm"]


# ── Trạng thái ─────────────────────────────────────────────────────────────────

def test_mo_lai_viec_thi_xoa_sach_dau_hoan_thanh(db, owner, work_list):
    """Giữ lại `completed_at` của lần xong trước là báo cáo đếm nhầm việc đang mở
    thành việc đã xong."""
    t = _create_task(db, owner, work_list["id"])
    task_service.update_task(db, owner, t["id"],
                             schema.TaskUpdate(status=int(WorkTaskStatus.DONE)))
    row = db.get(WorkTask, t["id"])
    assert row.completed_at is not None and row.completed_by == owner.employee_id

    task_service.update_task(db, owner, t["id"],
                             schema.TaskUpdate(status=int(WorkTaskStatus.OPEN)))
    row = db.get(WorkTask, t["id"])
    assert row.completed_at is None and row.completed_by is None


def test_hoan_thanh_cha_khong_tu_tick_viec_con(db, owner, work_list):
    """`02` §3: dữ liệu phải khớp sự thật — người dùng xác nhận ở giao diện, hệ
    thống không tự tick hộ rồi báo "xong hết"."""
    parent = _create_task(db, owner, work_list["id"])
    con = task_service.create_task(
        db, owner, schema.TaskCreate(title="Bước 1", parent_id=parent["id"]))
    task_service.update_task(db, owner, parent["id"],
                             schema.TaskUpdate(status=int(WorkTaskStatus.DONE)))
    assert db.get(WorkTask, con["id"]).status == int(WorkTaskStatus.OPEN)


# ── Người phụ trách ────────────────────────────────────────────────────────────

def test_nhieu_pic_va_nguoi_vua_pic_vua_theo_doi_thi_tinh_la_pic(db, owner, work_list):
    """Q5 — nhiều PIC như Lark. Trùng vai thì PIC thắng, không đẻ hai dòng."""
    t = _create_task(db, owner, work_list["id"])
    ra = task_service.set_assignees(db, owner, t["id"], [11, 22, 11], [22, 33])

    theo_nguoi = {a["employee_id"]: a["kind"] for a in ra["assignees"]}
    assert theo_nguoi == {11: int(WorkAssigneeKind.PIC),
                          22: int(WorkAssigneeKind.PIC),
                          33: int(WorkAssigneeKind.FOLLOWER)}


def test_dat_lai_nguoi_phu_trach_la_thay_the_ca_bo_khong_phai_cong_don(db, owner, work_list):
    t = _create_task(db, owner, work_list["id"])
    task_service.set_assignees(db, owner, t["id"], [11, 22], [])
    ra = task_service.set_assignees(db, owner, t["id"], [33], [])
    assert [a["employee_id"] for a in ra["assignees"]] == [33]


# ── Tag và nhãn tùy biến ───────────────────────────────────────────────────────

def test_khong_gan_duoc_tag_cua_list_khac(db, owner, work_list):
    """B-05: tag thuộc list. Gắn chéo thì thẻ hiện tag mà bộ lọc của list không có."""
    list_b = list_service.create_list(db, owner, schema.ListCreate(name="Kho"))
    tag_b = cfg.create_tag(db, owner, list_b["id"], schema.TagIn(name="Gấp"))
    t = _create_task(db, owner, work_list["id"])

    with pytest.raises(HTTPException) as e:
        task_service.set_tags(db, owner, t["id"], [tag_b["id"]])
    assert e.value.status_code == 400


def test_tag_trung_ten_trong_mot_list_bi_chan(db, owner, work_list):
    cfg.create_tag(db, owner, work_list["id"], schema.TagIn(name="Gấp"))
    with pytest.raises(HTTPException):
        cfg.create_tag(db, owner, work_list["id"], schema.TagIn(name="Gấp"))


def test_nhan_tuy_bien_chi_giu_mot_gia_tri_moi_truong(db, owner, work_list):
    """B-08 kiểu chọn-một: gán giá trị thứ hai là THAY, không phải thêm dòng."""
    f = cfg.create_label_field(db, owner, work_list["id"], schema.LabelFieldIn(name="Phiên bản"))
    v1 = cfg.create_label_option(db, owner, f["id"], schema.LabelOptionIn(name="v1"))
    v2 = cfg.create_label_option(db, owner, f["id"], schema.LabelOptionIn(name="v2"))
    t = _create_task(db, owner, work_list["id"])

    task_service.set_label(db, owner, t["id"], f["id"], v1["id"])
    ra = task_service.set_label(db, owner, t["id"], f["id"], v2["id"])
    #  Khẳng định ĐÚNG MỘT DÒNG và đúng giá trị, không so dict tuyệt đối: từ
    #  B-13 payload nhãn còn mang thêm các cột `value_*` của năm kiểu kia.
    assert len(ra["labels"]) == 1
    assert ra["labels"][0]["field_id"] == f["id"]
    assert ra["labels"][0]["option_id"] == v2["id"]

    ra = task_service.set_label(db, owner, t["id"], f["id"], None)   # bỏ chọn
    assert ra["labels"] == []


def test_gia_tri_nhan_phai_thuoc_dung_truong_do(db, owner, work_list):
    f1 = cfg.create_label_field(db, owner, work_list["id"], schema.LabelFieldIn(name="Phiên bản"))
    f2 = cfg.create_label_field(db, owner, work_list["id"], schema.LabelFieldIn(name="Khu vực"))
    v_cua_f2 = cfg.create_label_option(db, owner, f2["id"], schema.LabelOptionIn(name="Nam"))
    t = _create_task(db, owner, work_list["id"])

    with pytest.raises(HTTPException):
        task_service.set_label(db, owner, t["id"], f1["id"], v_cua_f2["id"])


def test_xoa_truong_nhan_thi_don_sach_gia_tri_da_gan_len_task(db, owner, work_list):
    """Bỏ lại dòng `tab_work_task_label` trỏ vào trường đã chết là thẻ vẽ ra nhãn rỗng."""
    f = cfg.create_label_field(db, owner, work_list["id"], schema.LabelFieldIn(name="Phiên bản"))
    v = cfg.create_label_option(db, owner, f["id"], schema.LabelOptionIn(name="v1"))
    t = _create_task(db, owner, work_list["id"])
    task_service.set_label(db, owner, t["id"], f["id"], v["id"])

    cfg.delete_label_field(db, owner, f["id"])
    assert task_service.get_task(db, owner, t["id"])["labels"] == []


# ── Danh sách và đếm ───────────────────────────────────────────────────────────

def test_dem_viec_cua_list_chi_tinh_task_cha_con_song(db, owner, work_list):
    """Đếm cả việc con thì con số trên sidebar luôn to hơn số thẻ nhìn thấy."""
    parent = _create_task(db, owner, work_list["id"])
    task_service.create_task(db, owner, schema.TaskCreate(title="Bước 1", parent_id=parent["id"]))
    dropped = _create_task(db, owner, work_list["id"], title="Việc bỏ")
    task_service.delete_task(db, owner, dropped["id"])

    row = [x for x in list_service.get_lists(db, owner) if x["id"] == work_list["id"]][0]
    assert row["task_count"] == 1


def test_list_luu_tru_khong_hien_o_danh_sach_thuong_nhung_van_lay_duoc(db, owner, work_list):
    list_service.archive_list(db, owner, work_list["id"])
    assert [x["id"] for x in list_service.get_lists(db, owner)] == []
    assert [x["id"] for x in list_service.get_lists(db, owner, include_archived=True)] == [work_list["id"]]


# ── Màn liệt kê DỰ ÁN (chủ sở hữu + thành viên) ────────────────────────────────

def test_khong_xin_thi_khong_kem_nguoi_cho_nhe(db, owner, work_list):
    """`with_people` mặc định TẮT: cây điều hướng và ô chọn gọi `get_lists` liên
    tục, nạp kèm thành viên là thêm hai query mỗi lần mà chẳng ai dùng."""
    row = list_service.get_lists(db, owner)[0]
    assert row["owner"] is None
    assert row["members"] == []
    assert row["created_at"]          # ngày tạo thì luôn có, không tốn query


def test_xin_kem_nguoi_thi_co_chu_so_huu_va_thanh_vien(db, owner, work_list):
    list_service.add_member(db, owner, work_list["id"],
                            schema.MemberIn(employee_id=22, role=3))
    row = list_service.get_lists(db, owner, with_people=True)[0]

    assert row["owner"]["employee_id"] == 11          # người tạo là OWNER (A-04)
    assert sorted(m["employee_id"] for m in row["members"]) == [11, 22]


def test_thanh_vien_khong_lan_giua_cac_du_an(db, owner):
    """Gom thành viên theo từng dự án bằng MỘT query cho cả bảng — sai chỗ này
    thì bảng liệt kê hiện người của dự án bên cạnh, không ai nhìn ra."""
    a = list_service.create_list(db, owner, schema.ListCreate(name="Dự án A"))
    b = list_service.create_list(db, owner, schema.ListCreate(name="Dự án B"))
    list_service.add_member(db, owner, a["id"], schema.MemberIn(employee_id=22, role=3))
    list_service.add_member(db, owner, b["id"], schema.MemberIn(employee_id=33, role=3))
    list_service.add_member(db, owner, b["id"], schema.MemberIn(employee_id=44, role=3))

    by_id = {x["id"]: x for x in list_service.get_lists(db, owner, with_people=True)}
    assert sorted(m["employee_id"] for m in by_id[a["id"]]["members"]) == [11, 22]
    assert sorted(m["employee_id"] for m in by_id[b["id"]]["members"]) == [11, 33, 44]
