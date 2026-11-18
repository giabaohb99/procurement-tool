"""duoc-CR-782 — diễn biến theo ngày / tuần của MỘT dự án hoặc MỘT người (màn Tổng quan Dự án).

Anh Được hỏi biểu đồ có theo dõi được từng dự án, hiệu suất từng người không. Các luật dễ vỡ:
  1. đủ mọi mốc kể cả mốc 0; kỳ ≤ 31 ngày chia ngày, dài hơn chia tuần;
  2. việc xong tách đúng hạn / trễ hạn / không đặt hạn theo NGÀY GIỜ VN của lúc xong;
  3. dự án ngoài phạm vi ra chuỗi rỗng; theo người chỉ đếm việc người đó PHỤ TRÁCH;
  4. số câu SQL không tăng theo số việc.
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import event

from app.modules.work import list_service, overview_service, schema, task_service
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkAssigneeKind, WorkTaskStatus
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

COMPANY = 1
ME = 11
AN = 21


def _ngay(lech: int) -> str:
    return (datetime.utcnow() + timedelta(hours=7) + timedelta(days=lech)).strftime("%Y-%m-%d")


@pytest.fixture()
def toi(db):
    return Actor(user_id=1, employee_id=ME, company_id=COMPANY)


@pytest.fixture()
def du_an(db, toi):
    return list_service.create_list(db, toi, schema.ListCreate(name="Kho Quý 4"))


def _viec(db, actor, list_id, due="", pics=(), followers=(), xong_cach_day=None, tao_cach_day=0):
    task_id = task_service.create_task(db, actor, schema.TaskCreate(list_id=list_id, title="Việc", due_date=due))["id"]
    for emp in pics:
        db.add(WorkTaskAssignee(task_id=task_id, employee_id=emp, kind=int(WorkAssigneeKind.PIC)))
    for emp in followers:
        db.add(WorkTaskAssignee(task_id=task_id, employee_id=emp, kind=int(WorkAssigneeKind.FOLLOWER)))
    task = db.get(WorkTask, task_id)
    task.created_at = datetime.utcnow() - timedelta(days=tao_cach_day)
    if xong_cach_day is not None:
        task.status = int(WorkTaskStatus.DONE)
        task.completed_at = datetime.utcnow() - timedelta(days=xong_cach_day)
    db.commit()
    return task_id


def _tong(kq, khoa):
    return sum(b[khoa] for b in kq["buckets"])


def test_ky_ngan_chia_ngay_ky_dai_chia_tuan_du_moi_moc(db, toi, du_an):
    kq7 = overview_service.overview_trend(db, toi, None, "project", du_an["id"], 7)
    assert kq7["granularity"] == "day" and len(kq7["buckets"]) == 7
    assert kq7["buckets"][-1]["start"] == _ngay(0)            # mốc cuối là hôm nay
    assert all(b["created"] == 0 for b in kq7["buckets"][:-1])  # mốc 0 vẫn có mặt
    kq90 = overview_service.overview_trend(db, toi, None, "project", du_an["id"], 90)
    assert kq90["granularity"] == "week" and len(kq90["buckets"]) == 13


def test_viec_xong_tach_dung_han_tre_han_khong_han(db, toi, du_an):
    lid = du_an["id"]
    _viec(db, toi, lid, due=_ngay(3), xong_cach_day=1)          # xong trước hạn
    _viec(db, toi, lid, due=_ngay(-5), xong_cach_day=1)         # xong sau hạn
    _viec(db, toi, lid, xong_cach_day=2)                        # không đặt hạn
    _viec(db, toi, lid, due=_ngay(-40), xong_cach_day=40)       # xong ngoài kỳ 30 ngày
    _viec(db, toi, lid, tao_cach_day=3)                         # mới giao, chưa xong

    kq = overview_service.overview_trend(db, toi, None, "project", lid, 30)
    assert (_tong(kq, "done_on_time"), _tong(kq, "done_late"), _tong(kq, "done_no_due")) == (1, 1, 1)
    #  Năm việc tạo trong lúc chạy bài; việc "xong 40 ngày trước" cũng tạo hôm nay nên vẫn tính là mới giao.
    assert _tong(kq, "created") == 5
    hom_qua = next(b for b in kq["buckets"] if b["start"] == _ngay(-1))
    assert hom_qua["done_on_time"] == 1 and hom_qua["done_late"] == 1


def test_du_an_ngoai_pham_vi_ra_chuoi_rong(db, toi, du_an):
    _viec(db, toi, du_an["id"], xong_cach_day=1)
    nguoi_la = Actor(user_id=9, employee_id=999, company_id=COMPANY)
    kq = overview_service.overview_trend(db, nguoi_la, None, "project", du_an["id"], 30)
    assert kq["buckets"] == []


def test_theo_nguoi_chi_dem_viec_minh_phu_trach(db, toi, du_an):
    lid = du_an["id"]
    _viec(db, toi, lid, due=_ngay(2), pics=[AN], xong_cach_day=1)
    _viec(db, toi, lid, due=_ngay(2), followers=[AN], xong_cach_day=1)   # chỉ theo dõi: không tính
    _viec(db, toi, lid, due=_ngay(2), pics=[ME], xong_cach_day=1)        # việc người khác
    kq = overview_service.overview_trend(db, toi, None, "person", AN, 30)
    assert _tong(kq, "done_on_time") == 1 and _tong(kq, "created") == 1


def test_loai_la_hoac_id_rong_ra_chuoi_rong(db, toi, du_an):
    assert overview_service.overview_trend(db, toi, None, "nhom", du_an["id"], 30)["buckets"] == []
    assert overview_service.overview_trend(db, toi, None, "person", 0, 30)["buckets"] == []


def test_so_cau_sql_khong_tang_theo_so_viec(db, toi, du_an):
    eng = db.get_bind()

    def dem():
        stmts = []

        def on(conn, cursor, statement, *a):
            stmts.append(statement)
        event.listen(eng, "before_cursor_execute", on)
        try:
            overview_service.overview_trend(db, toi, None, "project", du_an["id"], 30)
        finally:
            event.remove(eng, "before_cursor_execute", on)
        return len(stmts)

    _viec(db, toi, du_an["id"], xong_cach_day=1)
    it = dem()
    for i in range(25):
        _viec(db, toi, du_an["id"], due=_ngay(i % 5), xong_cach_day=i % 9)
    assert it > 0 and dem() == it
