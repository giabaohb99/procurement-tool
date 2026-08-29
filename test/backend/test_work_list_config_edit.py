"""Phân hệ Dự án — SỬA danh mục của một list: trường tùy biến · bộ giá trị.

Trước đây hai thứ này chỉ có TẠO và XÓA, nên sửa một lỗi chính tả trong tên một
giá trị là phải xóa rồi khai lại — mà xóa giá trị kéo theo mọi task đang gắn nó.
Tệp này chốt cái luật ấy: **sửa tại chỗ, dữ liệu đã gán còn nguyên**.

Tag cũng đi đúng đường này: từ migration `c8a1d4f60b72` nó chỉ là một trường
tùy biến kiểu chọn nhiều, không còn bảng lẫn CRUD riêng.
"""
import pytest
from fastapi import HTTPException

from app.modules.work import list_config_service as cfg
from app.modules.work import list_service, schema, task_service
from app.modules.work.label_model import WorkTaskLabel
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkLabelFieldType, WorkMemberRole

COMPANY = 1


@pytest.fixture()
def owner(db):
    return Actor(user_id=1, employee_id=11, company_id=COMPANY)


@pytest.fixture()
def work_list(db, owner):
    return list_service.create_list(db, owner, schema.ListCreate(name="Thu mua"))


@pytest.fixture()
def field(db, owner, work_list):
    return cfg.create_label_field(
        db, owner, work_list["id"],
        schema.LabelFieldIn(name="Phiên bản", field_type=int(WorkLabelFieldType.SINGLE)))


@pytest.fixture()
def option(db, owner, field):
    return cfg.create_label_option(db, owner, field["id"],
                                   schema.LabelOptionIn(name="v2.0", color="sky"))


# ── Trường "Tag": một trường tùy biến như mọi trường khác ──────────────────────

def test_list_moi_duoc_nap_san_truong_tag_chon_nhieu_khong_phai_truong_he(db, owner, work_list):
    """Nạp sẵn cho tiện, nhưng KHÔNG mang `system_key`: đổi tên, đổi kiểu (khi
    chưa có việc nào gán) và xóa hẳn đều được, khác trường Độ ưu tiên."""
    tag = next(f for f in cfg.get_label_fields(db, owner, work_list["id"])
               if f["name"] == cfg.TAG_FIELD_NAME)
    assert tag["field_type"] == int(WorkLabelFieldType.MULTI)
    assert (tag["system_key"], tag["options"]) == ("", [])

    ra = cfg.update_label_field(db, owner, tag["id"], schema.LabelFieldUpdate(name="Thẻ"))
    assert ra["name"] == "Thẻ"


def test_truong_chon_nhieu_giu_duoc_nhieu_gia_tri_tren_mot_viec(db, owner, work_list):
    """Chính là hành vi cũ của tag: một việc gắn được nhiều giá trị cùng lúc."""
    tag = next(f for f in cfg.get_label_fields(db, owner, work_list["id"])
               if f["name"] == cfg.TAG_FIELD_NAME)
    a = cfg.create_label_option(db, owner, tag["id"], schema.LabelOptionIn(name="Backend"))
    b = cfg.create_label_option(db, owner, tag["id"], schema.LabelOptionIn(name="Giao diện"))
    task = task_service.create_task(
        db, owner, schema.TaskCreate(list_id=work_list["id"], title="Việc A"))

    ra = task_service.set_label(db, owner, task["id"], tag["id"], [a["id"], b["id"]])
    assert sorted(v["option_id"] for v in ra["labels"]) == sorted([a["id"], b["id"]])


# ── Trường tùy biến & giá trị ──────────────────────────────────────────────────

def test_doi_ten_truong_giu_nguyen_bo_gia_tri(db, owner, field, option):
    ra = cfg.update_label_field(db, owner, field["id"],
                                schema.LabelFieldUpdate(name="Version"))
    assert ra["name"] == "Version"
    assert [o["name"] for o in ra["options"]] == ["v2.0"]


def test_doi_ten_gia_tri_giu_nguyen_task_dang_gan(db, owner, work_list, field, option):
    task = task_service.create_task(
        db, owner, schema.TaskCreate(list_id=work_list["id"], title="Việc A"))
    task_service.set_label(db, owner, task["id"], field["id"], option["id"])

    ra = cfg.update_label_option(db, owner, option["id"],
                                 schema.LabelOptionUpdate(name="v2.0.1", color="rose"))

    assert (ra["name"], ra["color"]) == ("v2.0.1", "rose")
    assert db.query(WorkTaskLabel).filter(
        WorkTaskLabel.option_id == option["id"]).count() == 1


def test_trung_ten_gia_tri_trong_cung_mot_truong_bi_chan(db, owner, field, option):
    khac = cfg.create_label_option(db, owner, field["id"], schema.LabelOptionIn(name="v2.1"))
    with pytest.raises(HTTPException) as e:
        cfg.update_label_option(db, owner, khac["id"], schema.LabelOptionUpdate(name="v2.0"))
    assert e.value.status_code == 400


def test_trung_ten_voi_gia_tri_cua_TRUONG_KHAC_thi_van_cho(db, owner, work_list, option):
    """Hai trường khác nhau được phép có cùng tên giá trị — phép kiểm chỉ trong một trường."""
    truong_2 = cfg.create_label_field(
        db, owner, work_list["id"],
        schema.LabelFieldIn(name="Môi trường", field_type=int(WorkLabelFieldType.SINGLE)))
    gia_tri = cfg.create_label_option(db, owner, truong_2["id"],
                                      schema.LabelOptionIn(name="staging"))

    ra = cfg.update_label_option(db, owner, gia_tri["id"],
                                 schema.LabelOptionUpdate(name="v2.0"))
    assert ra["name"] == "v2.0"


def test_sua_moi_mau_thi_ten_gia_tri_khong_bi_xoa_trang(db, owner, option):
    """Trường vắng mặt = KHÔNG đụng tới, khác hẳn trường gửi lên rỗng."""
    ra = cfg.update_label_option(db, owner, option["id"],
                                 schema.LabelOptionUpdate(color="rose"))
    assert (ra["name"], ra["color"]) == ("v2.0", "rose")


def test_ten_gia_tri_rong_bi_chan_chu_khong_luu_gia_tri_khong_ten(db, owner, option):
    with pytest.raises(HTTPException) as e:
        cfg.update_label_option(db, owner, option["id"],
                                schema.LabelOptionUpdate(name="   "))
    assert e.value.status_code == 400


def test_luu_lai_dung_ten_cu_cua_chinh_no_thi_khong_bi_bao_trung(db, owner, option):
    """Bấm Lưu mà không đổi gì cũng phải chạy — phép kiểm trùng loại chính nó ra."""
    ra = cfg.update_label_option(db, owner, option["id"],
                                 schema.LabelOptionUpdate(name="v2.0", color="lime"))
    assert (ra["name"], ra["color"]) == ("v2.0", "lime")


def test_gia_tri_khong_co_that_thi_404(db, owner):
    with pytest.raises(HTTPException) as e:
        cfg.update_label_option(db, owner, 9999, schema.LabelOptionUpdate(name="X"))
    assert e.value.status_code == 404


def test_ten_truong_rong_bi_chan(db, owner, field):
    with pytest.raises(HTTPException) as e:
        cfg.update_label_field(db, owner, field["id"], schema.LabelFieldUpdate(name=""))
    assert e.value.status_code == 400


# ── Đổi KIỂU trường ────────────────────────────────────────────────────────────

def test_doi_kieu_duoc_khi_truong_chua_co_gia_tri_nao_gan(db, owner, field):
    ra = cfg.update_label_field(
        db, owner, field["id"],
        schema.LabelFieldUpdate(field_type=int(WorkLabelFieldType.TEXT)))
    assert ra["field_type"] == int(WorkLabelFieldType.TEXT)


def test_doi_kieu_bi_chan_khi_da_co_viec_dang_gan(db, owner, work_list, field, option):
    """Mỗi kiểu ghi vào một cột `value_*` khác nhau: đổi kiểu khi đã có dữ liệu là
    mọi giá trị cũ nằm sai cột, nhìn như mất sạch."""
    task = task_service.create_task(
        db, owner, schema.TaskCreate(list_id=work_list["id"], title="Việc A"))
    task_service.set_label(db, owner, task["id"], field["id"], option["id"])

    with pytest.raises(HTTPException) as e:
        cfg.update_label_field(db, owner, field["id"],
                               schema.LabelFieldUpdate(field_type=int(WorkLabelFieldType.TEXT)))
    assert e.value.status_code == 400


def test_truong_he_thong_khong_doi_duoc_kieu_nhung_van_doi_duoc_ten(db, owner, work_list):
    truong_he = next(f for f in cfg.get_label_fields(db, owner, work_list["id"])
                     if f["system_key"] == cfg.PRIORITY_KEY)

    with pytest.raises(HTTPException) as e:
        cfg.update_label_field(db, owner, truong_he["id"],
                               schema.LabelFieldUpdate(field_type=int(WorkLabelFieldType.TEXT)))
    assert e.value.status_code == 400

    ra = cfg.update_label_field(db, owner, truong_he["id"],
                                schema.LabelFieldUpdate(name="Mức độ gấp"))
    assert ra["name"] == "Mức độ gấp"


def test_value_count_dem_dung_so_viec_dang_gan(db, owner, work_list, field, option):
    """Giao diện khóa ô "kiểu trường" dựa vào con số này, nên nó phải đúng."""
    truoc = next(f for f in cfg.get_label_fields(db, owner, work_list["id"])
                 if f["id"] == field["id"])
    assert truoc["value_count"] == 0

    task = task_service.create_task(
        db, owner, schema.TaskCreate(list_id=work_list["id"], title="Việc A"))
    task_service.set_label(db, owner, task["id"], field["id"], option["id"])

    sau = next(f for f in cfg.get_label_fields(db, owner, work_list["id"])
               if f["id"] == field["id"])
    assert sau["value_count"] == 1


def test_list_moi_duoc_nap_san_truong_do_uu_tien_bon_bac(db, owner, work_list):
    """Độ ưu tiên nay là TRƯỜNG TÙY BIẾN nạp sẵn, không còn cột cứng của task."""
    fields = cfg.get_label_fields(db, owner, work_list["id"])
    uu_tien = [f for f in fields if f["system_key"] == cfg.PRIORITY_KEY]
    assert len(uu_tien) == 1
    assert [o["name"] for o in uu_tien[0]["options"]] == [ten for ten, _ in cfg.PRIORITY_OPTIONS]


# ── Quyền ──────────────────────────────────────────────────────────────────────

def test_thanh_vien_thuong_khong_sua_duoc_danh_muc(db, owner, work_list, field, option):
    """Sửa danh mục là việc của ADMIN trở lên (04 §3), y như tạo và xóa."""
    thanh_vien = Actor(user_id=2, employee_id=22, company_id=COMPANY)
    list_service.add_member(
        db, owner, work_list["id"],
        schema.MemberIn(employee_id=22, role=int(WorkMemberRole.MEMBER)))

    for goi in (
        lambda: cfg.update_label_field(db, thanh_vien, field["id"],
                                       schema.LabelFieldUpdate(name="X")),
        lambda: cfg.update_label_option(db, thanh_vien, option["id"],
                                        schema.LabelOptionUpdate(name="X")),
    ):
        with pytest.raises(HTTPException) as e:
            goi()
        assert e.value.status_code == 403


def test_list_da_luu_tru_thi_khong_sua_duoc_danh_muc(db, owner, work_list, field):
    """Lưu trữ là ĐÓNG BĂNG — đọc được, ghi thì không."""
    list_service.archive_list(db, owner, work_list["id"])
    with pytest.raises(HTTPException) as e:
        cfg.update_label_field(db, owner, field["id"], schema.LabelFieldUpdate(name="X"))
    assert e.value.status_code == 400
