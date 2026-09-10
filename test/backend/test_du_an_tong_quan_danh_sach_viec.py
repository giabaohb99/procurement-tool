"""Phân hệ Dự án — màn Tổng quan trả kèm HAI DANH SÁCH việc.

Trước đây màn này chỉ có số đếm: nó nói «22 việc quá hạn» rồi dừng ở đó, người
đọc biết mình đang có vấn đề nhưng không có chỗ nào bấm vào để xem vấn đề nằm ở
đâu. Tệp này chốt phần bù: `overdue_tasks` và `my_tasks`.

Ba luật dễ vỡ nhất, mỗi luật một bài:
  1. Quá hạn xếp theo hạn CŨ NHẤT trước — việc trễ lâu nhất là việc đáng hỏi nhất.
  2. Việc CHƯA đặt hạn phải xuống CUỐI danh sách của tôi, không lên đầu.
  3. Cả hai danh sách chỉ lấy việc trong dự án mình THẤY, và chỉ task CHA.
"""
from datetime import datetime, timedelta

import pytest

from app.modules.work import list_service, overview_service, schema, task_service
from app.modules.work.membership_service import Actor

COMPANY = 1
ME = 11
NGUOI_KHAC = 22


def _ngay(lech: int) -> str:
    """Ngày theo giờ VN, lệch `lech` ngày so với hôm nay."""
    return (datetime.utcnow() + timedelta(hours=7) + timedelta(days=lech)).strftime("%Y-%m-%d")


@pytest.fixture()
def toi(db):
    return Actor(user_id=1, employee_id=ME, company_id=COMPANY)


@pytest.fixture()
def du_an(db, toi):
    return list_service.create_list(db, toi, schema.ListCreate(name="Thu mua Quý 3"))


def _tao_viec(db, actor, list_id, title, due_date="", assignee_ids=None):
    return task_service.create_task(db, actor, schema.TaskCreate(
        list_id=list_id, title=title, due_date=due_date,
        assignee_ids=assignee_ids or []))


def test_viec_qua_han_xep_han_cu_nhat_len_dau(db, toi, du_an):
    #  Tạo lộn xộn để chắc chắn thứ tự là do câu truy vấn, không do thứ tự thêm.
    _tao_viec(db, toi, du_an["id"], "Trễ 2 ngày", _ngay(-2))
    _tao_viec(db, toi, du_an["id"], "Trễ 30 ngày", _ngay(-30))
    _tao_viec(db, toi, du_an["id"], "Trễ 9 ngày", _ngay(-9))

    kq = overview_service.overview(db, toi)

    assert kq["task_overdue"] == 3
    assert [t["title"] for t in kq["overdue_tasks"]] == [
        "Trễ 30 ngày", "Trễ 9 ngày", "Trễ 2 ngày",
    ]


def test_viec_chua_qua_han_khong_lot_vao_danh_sach_qua_han(db, toi, du_an):
    _tao_viec(db, toi, du_an["id"], "Hạn hôm nay", _ngay(0))
    _tao_viec(db, toi, du_an["id"], "Hạn tuần sau", _ngay(7))
    _tao_viec(db, toi, du_an["id"], "Chưa đặt hạn")

    kq = overview_service.overview(db, toi)

    #  ⚠️ Hạn HÔM NAY chưa phải quá hạn. Máy chủ chạy UTC nên so ngày thẳng là
    #  việc đến hạn hôm nay bị tính trễ suốt buổi tối giờ VN.
    assert kq["task_overdue"] == 0
    assert kq["overdue_tasks"] == []


def test_viec_cua_toi_day_viec_chua_dat_han_xuong_cuoi(db, toi, du_an):
    _tao_viec(db, toi, du_an["id"], "Không hạn", assignee_ids=[ME])
    _tao_viec(db, toi, du_an["id"], "Hạn xa", _ngay(30), assignee_ids=[ME])
    _tao_viec(db, toi, du_an["id"], "Hạn gần", _ngay(1), assignee_ids=[ME])

    kq = overview_service.overview(db, toi)

    #  Chuỗi rỗng nhỏ hơn mọi chuỗi ngày, nên sắp thẳng `due_date` là việc chưa
    #  đặt hạn chiếm sạch đầu danh sách — đúng thứ KHÔNG cần nhắc.
    assert [t["title"] for t in kq["my_tasks"]] == ["Hạn gần", "Hạn xa", "Không hạn"]


def test_viec_cua_nguoi_khac_khong_vao_danh_sach_cua_toi(db, toi, du_an):
    _tao_viec(db, toi, du_an["id"], "Việc của người khác", _ngay(1),
              assignee_ids=[NGUOI_KHAC])
    _tao_viec(db, toi, du_an["id"], "Việc của tôi", _ngay(1), assignee_ids=[ME])

    kq = overview_service.overview(db, toi)

    assert kq["task_mine"] == 1
    assert [t["title"] for t in kq["my_tasks"]] == ["Việc của tôi"]


def test_moi_dong_du_de_nhan_ra_va_bam_vao(db, toi, du_an):
    viec = _tao_viec(db, toi, du_an["id"], "Chốt giá NCC", _ngay(-3), assignee_ids=[ME])

    dong = overview_service.overview(db, toi)["overdue_tasks"][0]

    #  Thiếu `id` thì bấm vào không đi đâu; thiếu `list_name` thì tám dòng việc
    #  của tám dự án khác nhau đọc ra như cùng một chỗ.
    assert dong == {
        "id": viec["id"],
        "list_id": du_an["id"],
        "list_name": "Thu mua Quý 3",
        "title": "Chốt giá NCC",
        "due_date": _ngay(-3),
    }


def test_chua_tham_gia_du_an_nao_van_tra_du_khoa(db):
    nguoi_la = Actor(user_id=9, employee_id=999, company_id=COMPANY)

    kq = overview_service.overview(db, nguoi_la)

    #  Trả đủ KHÓA với danh sách rỗng chứ không thiếu khóa: giao diện đọc thẳng
    #  `data.overdue_tasks.map(...)`, thiếu khóa là `undefined` và màn nổ.
    assert kq["overdue_tasks"] == []
    assert kq["my_tasks"] == []
