"""Phân hệ Dự án — TRƯỜNG TÙY BIẾN sáu kiểu (B-13).

Trước B-13 chỉ có một kiểu (chọn một giá trị) và ràng buộc "một trường một giá
trị" do unique `(task_id, field_id)` dưới CSDL giữ. Unique đó đã bị GỠ để chứa
kiểu chọn nhiều, nên luật ấy nay nằm hoàn toàn ở `label_value_service`. Tệp này
là cái chốt cho nó — nới lỏng chỗ nào ở đây là task lặng lẽ mọc hai giá trị cho
một trường chọn-một, mà giao diện chỉ vẽ cái đầu nên không ai thấy.
"""
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.modules.work import list_config_service as cfg
from app.modules.work import list_service, schema, task_service
from app.modules.work.label_model import WorkTaskLabel
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkLabelFieldType

COMPANY = 1


@pytest.fixture()
def owner(db):
    return Actor(user_id=1, employee_id=11, company_id=COMPANY)


@pytest.fixture()
def work_list(db, owner):
    return list_service.create_list(db, owner, schema.ListCreate(name="Thu mua"))


@pytest.fixture()
def task(db, owner, work_list):
    return task_service.create_task(
        db, owner, schema.TaskCreate(list_id=work_list["id"], title="Việc A"))


def _field(db, owner, list_id, name, kind):
    return cfg.create_label_field(
        db, owner, list_id, schema.LabelFieldIn(name=name, field_type=int(kind)))


def _option(db, owner, field_id, name):
    return cfg.create_label_option(
        db, owner, field_id, schema.LabelOptionIn(name=name))


def _values(db, task_id, field_id):
    return (db.query(WorkTaskLabel)
            .filter(WorkTaskLabel.task_id == task_id,
                    WorkTaskLabel.field_id == field_id).all())


def _labels_of(task_dict, field_id):
    return [l for l in task_dict["labels"] if l["field_id"] == field_id]


# ── Khai trường ────────────────────────────────────────────────────────────────

def test_truong_khai_khong_ghi_kieu_thi_van_la_chon_mot(db, owner, work_list):
    """Bất biến hợp nhất ngược: mọi trường khai TRƯỚC B-13 mang `field_type` mặc
    định, không phải vá dữ liệu cũ."""
    f = cfg.create_label_field(db, owner, work_list["id"], schema.LabelFieldIn(name="Phiên bản"))
    assert f["field_type"] == int(WorkLabelFieldType.SINGLE)


def test_kieu_la_bi_chan_ngay_luc_khai(db, owner, work_list):
    """Kiểu lạ lọt xuống CSDL là mọi nơi đọc `WorkLabelFieldType` ném ValueError
    và cả bảng kanban trắng trang."""
    for bad in (0, 7, 99, -1):
        with pytest.raises(HTTPException) as e:
            cfg.create_label_field(
                db, owner, work_list["id"], schema.LabelFieldIn(name=f"X{bad}", field_type=bad))
        assert e.value.status_code == 400


# ── Chọn một ───────────────────────────────────────────────────────────────────

def test_chon_mot_ghi_de_chu_khong_cong_don(db, owner, work_list, task):
    """Đây là bất biến unique cũ, nay do service giữ."""
    f = _field(db, owner, work_list["id"], "Phiên bản", WorkLabelFieldType.SINGLE)
    a = _option(db, owner, f["id"], "v1")
    b = _option(db, owner, f["id"], "v2")

    task_service.set_label(db, owner, task["id"], f["id"], a["id"])
    task_service.set_label(db, owner, task["id"], f["id"], b["id"])

    rows = _values(db, task["id"], f["id"])
    assert len(rows) == 1 and rows[0].option_id == b["id"]


def test_chon_mot_gui_danh_sach_nhieu_gia_tri_bi_chan(db, owner, work_list, task):
    f = _field(db, owner, work_list["id"], "Phiên bản", WorkLabelFieldType.SINGLE)
    a = _option(db, owner, f["id"], "v1")
    b = _option(db, owner, f["id"], "v2")
    with pytest.raises(HTTPException) as e:
        task_service.set_label(db, owner, task["id"], f["id"], [a["id"], b["id"]])
    assert e.value.status_code == 400


def test_bo_chon_thi_xoa_sach_dong(db, owner, work_list, task):
    f = _field(db, owner, work_list["id"], "Phiên bản", WorkLabelFieldType.SINGLE)
    a = _option(db, owner, f["id"], "v1")
    task_service.set_label(db, owner, task["id"], f["id"], a["id"])
    task_service.set_label(db, owner, task["id"], f["id"], None)
    assert _values(db, task["id"], f["id"]) == []


# ── Chọn nhiều ─────────────────────────────────────────────────────────────────

def test_chon_nhieu_giu_du_gia_tri_va_dung_thu_tu_nguoi_gui(db, owner, work_list, task):
    f = _field(db, owner, work_list["id"], "Mảng", WorkLabelFieldType.MULTI)
    a = _option(db, owner, f["id"], "Backend")
    b = _option(db, owner, f["id"], "Frontend")
    c = _option(db, owner, f["id"], "QA")

    out = task_service.set_label(db, owner, task["id"], f["id"], [c["id"], a["id"], b["id"]])
    assert [l["option_id"] for l in _labels_of(out, f["id"])] == [c["id"], a["id"], b["id"]]


def test_chon_nhieu_bo_gia_tri_trung_trong_cung_mot_lan_gui(db, owner, work_list, task):
    """Gửi trùng thì lưu trùng là thẻ hiện hai chip y hệt nhau."""
    f = _field(db, owner, work_list["id"], "Mảng", WorkLabelFieldType.MULTI)
    a = _option(db, owner, f["id"], "Backend")
    task_service.set_label(db, owner, task["id"], f["id"], [a["id"], a["id"], a["id"]])
    assert len(_values(db, task["id"], f["id"])) == 1


def test_chon_nhieu_ghi_lan_sau_thay_the_han_lan_truoc(db, owner, work_list, task):
    f = _field(db, owner, work_list["id"], "Mảng", WorkLabelFieldType.MULTI)
    a = _option(db, owner, f["id"], "Backend")
    b = _option(db, owner, f["id"], "Frontend")
    task_service.set_label(db, owner, task["id"], f["id"], [a["id"], b["id"]])
    task_service.set_label(db, owner, task["id"], f["id"], [b["id"]])
    rows = _values(db, task["id"], f["id"])
    assert len(rows) == 1 and rows[0].option_id == b["id"]


def test_chon_nhieu_qua_tran_bi_chan(db, owner, work_list, task):
    """Không chặn thì một lời gọi đẻ hàng nghìn dòng và thẻ dài vô tận."""
    from app.modules.work.label_value_service import MAX_MULTI_VALUES

    f = _field(db, owner, work_list["id"], "Mảng", WorkLabelFieldType.MULTI)
    ids = [_option(db, owner, f["id"], f"O{i}")["id"] for i in range(3)]
    with pytest.raises(HTTPException) as e:
        task_service.set_label(db, owner, task["id"], f["id"], ids * (MAX_MULTI_VALUES // 3 + 2))
    assert e.value.status_code == 400


# ── Bốn kiểu không có bộ giá trị ───────────────────────────────────────────────

def test_kieu_chu_luu_va_cat_dung_be_rong_cot(db, owner, work_list, task):
    """Không cắt thì MySQL ném `Data too long` và cả lời gọi hỏng, thay vì lưu
    phần đọc được."""
    f = _field(db, owner, work_list["id"], "Ghi chú", WorkLabelFieldType.TEXT)
    task_service.set_label(db, owner, task["id"], f["id"], "  xin chào  ")
    assert _values(db, task["id"], f["id"])[0].value_text == "xin chào"

    task_service.set_label(db, owner, task["id"], f["id"], "x" * 10_000)
    assert len(_values(db, task["id"], f["id"])[0].value_text) == 500


def test_kieu_so_giu_nguyen_phan_le_khong_lam_tron(db, owner, work_list, task):
    """Dùng float là 1234.5678 hiện ra 1234.5677999999999 ngay trên thẻ."""
    f = _field(db, owner, work_list["id"], "Giá", WorkLabelFieldType.NUMBER)
    out = task_service.set_label(db, owner, task["id"], f["id"], "1234.5678")
    assert Decimal(_labels_of(out, f["id"])[0]["value_number"]) == Decimal("1234.5678")


def test_kieu_so_nhan_dau_phay_thap_phan_kieu_viet(db, owner, work_list, task):
    f = _field(db, owner, work_list["id"], "Giá", WorkLabelFieldType.NUMBER)
    out = task_service.set_label(db, owner, task["id"], f["id"], "12,5")
    #  So bằng Decimal chứ không bằng chuỗi: cột `Numeric(18, 4)` trả về
    #  "12.5000" — đủ bốn số lẻ, đúng như khai.
    assert Decimal(_labels_of(out, f["id"])[0]["value_number"]) == Decimal("12.5")


def test_kieu_so_nhan_chu_thi_bao_loi_chu_khong_luu_0(db, owner, work_list, task):
    f = _field(db, owner, work_list["id"], "Giá", WorkLabelFieldType.NUMBER)
    with pytest.raises(HTTPException) as e:
        task_service.set_label(db, owner, task["id"], f["id"], "mười hai")
    assert e.value.status_code == 400


def test_kieu_ngay_chi_nhan_dung_khuon_yyyy_mm_dd(db, owner, work_list, task):
    """Nhận bừa thì cột ngày lẫn chuỗi rác và mọi phép so ngày im lặng sai."""
    f = _field(db, owner, work_list["id"], "Mốc", WorkLabelFieldType.DATE)
    task_service.set_label(db, owner, task["id"], f["id"], "2026-09-01")
    assert _values(db, task["id"], f["id"])[0].value_date == "2026-09-01"

    for bad in ("01/09/2026", "2026-13-01", "2026-02-30", "hôm qua", "2026-9-1"):
        with pytest.raises(HTTPException) as e:
            task_service.set_label(db, owner, task["id"], f["id"], bad)
        assert e.value.status_code == 400, bad


def test_kieu_nguoi_luu_id_va_tra_kem_ten(db, owner, work_list, task):
    f = _field(db, owner, work_list["id"], "Người duyệt", WorkLabelFieldType.PERSON)
    out = task_service.set_label(db, owner, task["id"], f["id"], 11)
    row = _labels_of(out, f["id"])[0]
    assert row["value_employee_id"] == 11
    assert "value_employee_name" in row


def test_kieu_nguoi_nhan_gia_tri_khong_phai_so_thi_bao_loi(db, owner, work_list, task):
    f = _field(db, owner, work_list["id"], "Người duyệt", WorkLabelFieldType.PERSON)
    with pytest.raises(HTTPException) as e:
        task_service.set_label(db, owner, task["id"], f["id"], "ai đó")
    assert e.value.status_code == 400


# ── Chặn ───────────────────────────────────────────────────────────────────────

def test_gia_tri_phai_thuoc_dung_truong_do(db, owner, work_list, task):
    f1 = _field(db, owner, work_list["id"], "A", WorkLabelFieldType.SINGLE)
    f2 = _field(db, owner, work_list["id"], "B", WorkLabelFieldType.SINGLE)
    lac = _option(db, owner, f2["id"], "của trường B")
    with pytest.raises(HTTPException) as e:
        task_service.set_label(db, owner, task["id"], f1["id"], lac["id"])
    assert e.value.status_code == 400


def test_khong_gan_duoc_truong_cua_list_khac(db, owner, work_list, task):
    """Nhận bừa là task mang một nhãn không bao giờ hiện ra, vì giao diện chỉ vẽ
    trường của list mình."""
    other = list_service.create_list(db, owner, schema.ListCreate(name="Kho"))
    f = _field(db, owner, other["id"], "Phiên bản", WorkLabelFieldType.SINGLE)
    o = _option(db, owner, f["id"], "v1")
    with pytest.raises(HTTPException) as e:
        task_service.set_label(db, owner, task["id"], f["id"], o["id"])
    assert e.value.status_code == 400


def test_nguoi_ngoai_khong_dat_duoc_gia_tri(db, owner, work_list, task):
    f = _field(db, owner, work_list["id"], "Ghi chú", WorkLabelFieldType.TEXT)
    outsider = Actor(user_id=2, employee_id=22, company_id=COMPANY)
    with pytest.raises(HTTPException) as e:
        task_service.set_label(db, outsider, task["id"], f["id"], "x")
    assert e.value.status_code == 403


def test_xoa_truong_thi_don_sach_moi_gia_tri_da_gan(db, owner, work_list, task):
    f = _field(db, owner, work_list["id"], "Mảng", WorkLabelFieldType.MULTI)
    a = _option(db, owner, f["id"], "Backend")
    task_service.set_label(db, owner, task["id"], f["id"], [a["id"]])
    cfg.delete_label_field(db, owner, f["id"])
    assert task_service.get_task(db, owner, task["id"])["labels"] == []
