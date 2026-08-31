"""Phân hệ Công việc — tab «Hoạt động» cấp dự án (D-09, §8 của `05-giao-dien.md`).

Hai thứ dễ hỏng ÂM THẦM ở đây, cả hai đều không lộ ra trên màn hình:

1. **Rò dòng của dự án khác.** Việc · dự án · nhóm đánh số độc lập nhau, mà cả
   phân hệ từng ghi nhật ký chung một tên `work_task`. Lọc theo `entity_id` mà
   không kèm `entity` là dự án #5 nuốt luôn nhật ký của việc #5. Đó chính là lý
   do có `audit_entity.py` và migration `c3a91d47f2b8`.
2. **Rò cho người ngoài.** `/api/audit-logs` dùng chung cả hệ và KHÔNG kiểm
   quyền theo entity; đường mới phải tự đi qua `get_list_or_403`.
"""
import pytest
from fastapi import HTTPException

from app.modules.work import activity_service, list_service, schema, task_service
from app.modules.work.audit_entity import WorkActivityKind
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkMemberRole

COMPANY = 1


def _nguoi(uid: int, emp_id: int) -> Actor:
    return Actor(user_id=uid, employee_id=emp_id, company_id=COMPANY)


@pytest.fixture()
def chu(db):
    return _nguoi(1, 11)


@pytest.fixture()
def nguoi_ngoai(db):
    return _nguoi(2, 22)


def _tao_list(db, actor, name="Dự án A"):
    return list_service.create_list(db, actor, schema.ListCreate(name=name))


def _tao_task(db, actor, list_id, title="Việc A"):
    return task_service.create_task(
        db, actor, schema.TaskCreate(list_id=list_id, title=title))


def _cau(items):
    """Tập câu ghi log của một trang — so nội dung, khỏi phụ thuộc thứ tự."""
    return {i["message"] for i in items}


# ── Phạm vi: chỉ dòng của ĐÚNG dự án này ────────────────────────────────────────

def test_khong_lay_nham_dong_cua_du_an_khac_du_trung_so_id(db, chu):
    """Việc #n và dự án #n là hai thứ khác nhau — lỗi kinh điển của bản trước.

    Dựng đúng thế trận gây lỗi: hai dự án, và một việc mang id trùng với id của
    dự án còn lại. Lọc chỉ theo `entity_id` thì dòng "Tạo dự án B" chui vào
    nhật ký của dự án A.
    """
    a = _tao_list(db, chu, "Dự án A")
    b = _tao_list(db, chu, "Dự án B")
    for i in range(b["id"] + 1):
        _tao_task(db, chu, a["id"], f"Việc {i}")

    items = activity_service.list_activities(db, chu, a["id"])["items"]
    assert "Tạo danh sách Dự án B" not in _cau(items)
    assert "Tạo danh sách Dự án A" in _cau(items)
    assert all(i["message"].startswith(("Tạo công việc", "Tạo danh sách Dự án A"))
               for i in items)


def test_gom_ca_viec_thanh_vien_va_du_an_vao_mot_dong(db, chu):
    """§8: dòng thời gian là hợp của ba nguồn, không phải mỗi nhật ký việc."""
    lst = _tao_list(db, chu)
    _tao_task(db, chu, lst["id"])
    list_service.add_member(
        db, chu, lst["id"],
        schema.MemberIn(employee_id=22, role=int(WorkMemberRole.MEMBER)))

    items = activity_service.list_activities(db, chu, lst["id"])["items"]
    assert {i["kind"] for i in items} == {
        int(WorkActivityKind.TASK), int(WorkActivityKind.MEMBER),
        int(WorkActivityKind.LIST)}


def test_van_giu_dong_cua_viec_da_bi_xoa(db, chu):
    """Xóa việc là dòng người ta cần nhất — lọc `deleted_at` là mất luôn nó."""
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"], "Việc sắp xóa")
    task_service.delete_task(db, chu, task["id"])

    items = activity_service.list_activities(db, chu, lst["id"])["items"]
    assert "Xóa công việc: Việc sắp xóa" in _cau(items)
    #  Tiêu đề vẫn tra được (xóa MỀM) nên dòng nhật ký còn bấm sang việc được.
    xoa = next(i for i in items if i["action"] == "delete")
    assert xoa["task_id"] == task["id"]
    assert xoa["task_title"] == "Việc sắp xóa"


# ── Quyền ───────────────────────────────────────────────────────────────────────

def test_nguoi_ngoai_bi_chan_403_ca_hai_duong(db, chu, nguoi_ngoai):
    lst = _tao_list(db, chu)
    _tao_task(db, chu, lst["id"])

    with pytest.raises(HTTPException) as e1:
        activity_service.list_activities(db, nguoi_ngoai, lst["id"])
    assert e1.value.status_code == 403

    with pytest.raises(HTTPException) as e2:
        activity_service.list_actors(db, nguoi_ngoai, lst["id"])
    assert e2.value.status_code == 403


# ── Bộ lọc + phân trang ─────────────────────────────────────────────────────────

def test_loc_theo_loai_su_kien_va_theo_nguoi(db, chu):
    lst = _tao_list(db, chu)
    _tao_task(db, chu, lst["id"])

    chi_viec = activity_service.list_activities(
        db, chu, lst["id"], kind=int(WorkActivityKind.TASK))
    assert chi_viec["total"] == 1
    assert chi_viec["items"][0]["message"].startswith("Tạo công việc")

    assert activity_service.list_activities(db, chu, lst["id"], by=chu.user_id)["total"] > 0
    #  Người chưa từng thao tác: rỗng, KHÔNG phải bỏ qua bộ lọc.
    assert activity_service.list_activities(db, chu, lst["id"], by=999)["total"] == 0


def test_ma_loai_su_kien_la_thi_tra_rong_chu_khong_do_ra_tat_ca(db, chu):
    """Sửa `?kind=` trong URL thành số bậy không được biến thành "xem tất cả"."""
    lst = _tao_list(db, chu)
    _tao_task(db, chu, lst["id"])
    assert activity_service.list_activities(db, chu, lst["id"], kind=99)["total"] == 0


def test_phan_trang_khong_lap_va_khong_mat_dong(db, chu):
    """Hai thao tác trong cùng một giây là chuyện thường — sắp theo `id` mới ổn định."""
    lst = _tao_list(db, chu)
    for i in range(5):
        _tao_task(db, chu, lst["id"], f"Việc {i}")

    trang1 = activity_service.list_activities(db, chu, lst["id"], offset=0, limit=3)
    trang2 = activity_service.list_activities(db, chu, lst["id"], offset=3, limit=3)

    assert trang1["has_more"] is True
    assert trang2["has_more"] is False
    ids = [i["id"] for i in trang1["items"]] + [i["id"] for i in trang2["items"]]
    assert len(set(ids)) == len(ids) == trang1["total"]
    #  Mới nhất trước.
    assert ids == sorted(ids, reverse=True)


def test_limit_bi_ep_ve_tran_va_offset_am_ve_khong(db, chu):
    lst = _tao_list(db, chu)
    _tao_task(db, chu, lst["id"])
    #  `limit` khổng lồ không được phép quét sạch bảng.
    ket_qua = activity_service.list_activities(
        db, chu, lst["id"], limit=10_000, offset=-5)
    assert len(ket_qua["items"]) == ket_qua["total"]
    assert ket_qua["has_more"] is False


def test_du_an_chua_co_gi_thi_tra_dong_tao_du_an(db, chu):
    """Dự án vừa tạo KHÔNG bao giờ rỗng — luôn có ít nhất dòng "Tạo danh sách"."""
    lst = _tao_list(db, chu)
    ket_qua = activity_service.list_activities(db, chu, lst["id"])
    assert ket_qua["total"] == 1
    assert ket_qua["has_more"] is False
    assert ket_qua["items"][0]["kind"] == int(WorkActivityKind.LIST)


def test_danh_sach_nguoi_thao_tac_khong_trung_va_co_ten(db, chu):
    lst = _tao_list(db, chu)
    _tao_task(db, chu, lst["id"])
    _tao_task(db, chu, lst["id"], "Việc B")

    nguoi = activity_service.list_actors(db, chu, lst["id"])
    assert [n["id"] for n in nguoi] == [chu.user_id]
    #  Không có bảng `User` trong test này → rơi về "User #1", KHÔNG được rỗng:
    #  ô lọc mà hiện dòng trắng thì không ai bấm trúng.
    assert nguoi[0]["name"]


# ── Tên việc rỗng (lỗ lộ ra lúc stress test thẻ kanban) ─────────────────────────

def test_khong_tao_duoc_viec_khong_ten(db, chu):
    """`title: str` ở schema nhận cả chuỗi TOÀN DẤU CÁCH.

    `.strip()` xong thành rỗng và đẻ ra một việc không tên — trên kanban là một
    thẻ trắng trơn, nhìn như giao diện hỏng. Giao diện đã chặn, nhưng ai gọi
    thẳng API thì không.
    """
    lst = _tao_list(db, chu)
    for ten in ("", "   ", "\t\n"):
        with pytest.raises(HTTPException) as e:
            _tao_task(db, chu, lst["id"], ten)
        assert e.value.status_code == 400


def test_khong_doi_ten_viec_thanh_rong_duoc(db, chu):
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"], "Việc có tên")

    with pytest.raises(HTTPException) as e:
        task_service.update_task(db, chu, task["id"], schema.TaskUpdate(title="   "))
    assert e.value.status_code == 400

    #  Tên cũ phải còn nguyên, không bị ghi đè dở dang rồi mới ném lỗi.
    sau = task_service.get_task(db, chu, task["id"])
    assert sau["title"] == "Việc có tên"


def test_van_cat_duoc_dau_cach_thua_hai_dau_ten(db, chu):
    """Chặn rỗng không được làm hỏng việc cắt dấu cách thừa vẫn chạy xưa nay."""
    lst = _tao_list(db, chu)
    task = _tao_task(db, chu, lst["id"], "  Việc có tên  ")
    assert task["title"] == "Việc có tên"
