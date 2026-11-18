"""duoc-CR-782 — màn Tổng quan phân hệ Dự án theo góc nhìn người QUẢN LÝ.

Anh Được báo 18/11/2026: báo cáo tổng quan "chưa có đối chiếu user, xáo rỗng". Hai gốc:
  1. Phạm vi chỉ theo tư cách thành viên, nên xếp (không là thành viên dự án nào) thấy toàn 0 —
     nay ai XEM ĐƯỢC báo cáo Công việc & Dự án thì đếm trên mọi dự án.
  2. Không có số liệu theo người, theo dự án, và không có danh sách việc cần ra tay.

Mỗi luật một bài; bài cuối canh số câu SQL KHÔNG tăng theo số người (luật "API báo cáo nhanh nhất").
"""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import event

from app.modules.work import list_service, overview_people, overview_scope, overview_service, schema, task_service
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkAssigneeKind, WorkList, WorkTaskStatus
from app.modules.work.task_model import WorkTask, WorkTaskAssignee

COMPANY = 1
ME = 11
AN = 21
BINH = 22


def _ngay(lech: int) -> str:
    return (datetime.utcnow() + timedelta(hours=7) + timedelta(days=lech)).strftime("%Y-%m-%d")


@pytest.fixture()
def toi(db):
    return Actor(user_id=1, employee_id=ME, company_id=COMPANY)


@pytest.fixture()
def du_an(db, toi):
    return list_service.create_list(db, toi, schema.ListCreate(name="Kho Quý 4"))


def _viec(db, actor, list_id, title, due="", pics=(), followers=(), xong_cach_day=None, huy=False):
    """Tạo việc rồi gắn người / trạng thái thẳng vào bảng — bài kiểm số liệu, không kiểm luật gán người."""
    task_id = task_service.create_task(db, actor, schema.TaskCreate(
        list_id=list_id, title=title, due_date=due))["id"]
    for emp in pics:
        db.add(WorkTaskAssignee(task_id=task_id, employee_id=emp, kind=int(WorkAssigneeKind.PIC)))
    for emp in followers:
        db.add(WorkTaskAssignee(task_id=task_id, employee_id=emp, kind=int(WorkAssigneeKind.FOLLOWER)))
    task = db.get(WorkTask, task_id)
    if xong_cach_day is not None:
        task.status = int(WorkTaskStatus.DONE)
        task.completed_at = datetime.utcnow() - timedelta(days=xong_cach_day)
    if huy:
        task.status = int(WorkTaskStatus.CANCELLED)
    db.commit()
    return task_id


def _nguoi(kq, emp_id):
    return next(row for row in kq["people"] if row["employee_id"] == emp_id)


# ── Phạm vi ──────────────────────────────────────────────────────────────────

def test_xep_xem_duoc_bao_cao_thay_moi_du_an_ke_ca_khong_la_thanh_vien(db, toi, du_an, monkeypatch):
    _viec(db, toi, du_an["id"], "Kiểm kê", _ngay(-2), pics=[AN])
    xep = Actor(user_id=2, employee_id=999, company_id=COMPANY)

    #  Không được giao xem báo cáo: giữ luật thành viên, xếp không là thành viên nên rỗng.
    monkeypatch.setattr(overview_scope, "can_view_report", lambda *a, **k: False)
    kq = overview_service.overview(db, xep, user=object())
    assert kq["scope"] == "member" and kq["task_open"] == 0 and kq["people"] == []

    #  Được giao xem báo cáo Công việc & Dự án (admin có sẵn): đếm trên MỌI dự án.
    monkeypatch.setattr(overview_scope, "can_view_report", lambda *a, **k: True)
    kq = overview_service.overview(db, xep, user=object())
    assert kq["scope"] == "all"
    assert kq["task_open"] == 1 and kq["task_overdue"] == 1
    assert _nguoi(kq, AN)["overdue"] == 1


def test_xep_khong_la_thanh_vien_xem_duoc_so_nhung_khong_duoc_dan_link(db, toi, du_an, monkeypatch):
    #  Nới phạm vi chỉ là ĐỌC SỐ LIỆU: dự án / việc mình không là thành viên mở ra là 403, nên phải báo
    #  `can_open = False` để giao diện không dẫn link vào chỗ hỏng.
    _viec(db, toi, du_an["id"], "Trễ", _ngay(-2), pics=[AN])
    _viec(db, toi, du_an["id"], "Chưa ai nhận")
    monkeypatch.setattr(overview_scope, "can_view_report", lambda *a, **k: True)
    xep = Actor(user_id=2, employee_id=999, company_id=COMPANY)

    kq = overview_service.overview(db, xep, user=object())
    assert kq["projects"][0]["can_open"] is False
    assert kq["overdue_tasks"][0]["can_open"] is False
    assert kq["unassigned_tasks"][0]["can_open"] is False
    viec = overview_service.person_overview_tasks(db, xep, object(), AN)
    assert [v["title"] for v in viec] == ["Trễ"] and viec[0]["can_open"] is False

    #  Chính người tạo dự án (thành viên) cùng phạm vi "mọi dự án" thì mở được.
    kq = overview_service.overview(db, toi, user=object())
    assert kq["projects"][0]["can_open"] is True and kq["overdue_tasks"][0]["can_open"] is True


def test_loi_goi_noi_bo_khong_kem_user_giu_luat_thanh_vien(db, toi, du_an):
    _viec(db, toi, du_an["id"], "Việc trong dự án mình", pics=[ME])
    kq = overview_service.overview(db, Actor(user_id=3, employee_id=777, company_id=COMPANY))
    assert kq["scope"] == "member" and kq["task_open"] == 0


# ── Bảng theo người ─────────────────────────────────────────────────────────

def test_bang_theo_nguoi_dem_dung_tung_chi_so(db, toi, du_an):
    lid = du_an["id"]
    _viec(db, toi, lid, "Trễ 10 ngày", _ngay(-10), pics=[AN])
    _viec(db, toi, lid, "Trễ 2 ngày", _ngay(-2), pics=[AN])
    _viec(db, toi, lid, "Hạn mai", _ngay(1), pics=[AN])
    _viec(db, toi, lid, "Hạn 20 ngày nữa", _ngay(20), pics=[AN])
    _viec(db, toi, lid, "Xong đúng hạn", _ngay(5), pics=[AN], xong_cach_day=1)
    _viec(db, toi, lid, "Xong trễ", _ngay(-9), pics=[AN], xong_cach_day=2)
    _viec(db, toi, lid, "Xong ngoài kỳ", _ngay(-60), pics=[AN], xong_cach_day=50)

    an = _nguoi(overview_service.overview(db, toi, period_days=30), AN)
    assert an["open"] == 4
    assert an["overdue"] == 2
    assert an["due_soon"] == 1               # chỉ "Hạn mai"; quá hạn không tính là sắp tới hạn
    assert an["done_in_period"] == 2         # việc xong 50 ngày trước nằm ngoài kỳ 30 ngày
    assert an["on_time_rate"] == 50          # 1 đúng hạn / 2 việc xong trong kỳ có hạn
    assert an["max_overdue_days"] == 10


def test_nguoi_theo_doi_khong_tinh_va_mot_viec_hai_nguoi_gop_ca_hai_dong(db, toi, du_an):
    _viec(db, toi, du_an["id"], "Việc chung", _ngay(-1), pics=[AN, BINH], followers=[ME])
    kq = overview_service.overview(db, toi)
    ids = {row["employee_id"] for row in kq["people"]}
    assert ids == {AN, BINH}                 # người theo dõi không có dòng
    assert _nguoi(kq, AN)["overdue"] == _nguoi(kq, BINH)["overdue"] == 1


def test_tinh_trang_viec_dang_mo_chia_du_bon_phan(db, toi, du_an):
    #  Bốn phần của vòng tình trạng: quá hạn + sắp tới hạn + còn hạn + chưa đặt hạn = đang mở, không sót không trùng.
    lid = du_an["id"]
    _viec(db, toi, lid, "Quá hạn", _ngay(-1))
    _viec(db, toi, lid, "Hôm nay", _ngay(0))
    _viec(db, toi, lid, "Ngày thứ 7", _ngay(6))
    _viec(db, toi, lid, "Ngày thứ 8", _ngay(7))
    _viec(db, toi, lid, "Không hạn")
    kq = overview_service.overview(db, toi)
    assert (kq["task_overdue"], kq["task_due_soon"], kq["task_no_due"]) == (1, 2, 1)
    con_han = kq["task_open"] - kq["task_overdue"] - kq["task_due_soon"] - kq["task_no_due"]
    assert con_han == 1 and kq["task_open"] == 5


def test_ty_le_dung_han_rong_khi_chua_co_viec_nao_de_do(db, toi, du_an):
    #  Xong mà không đặt hạn: không có "đúng" hay "trễ" — trả None, không trả 0% (0% là "trễ hết").
    _viec(db, toi, du_an["id"], "Xong không hạn", pics=[AN], xong_cach_day=1)
    kq = overview_service.overview(db, toi)
    assert _nguoi(kq, AN)["on_time_rate"] is None
    assert kq["on_time_rate"] is None
    assert kq["task_done_in_period"] == 1


def test_nguoi_nhieu_viec_qua_han_dung_dau_bang(db, toi, du_an):
    _viec(db, toi, du_an["id"], "B mở", pics=[BINH])
    _viec(db, toi, du_an["id"], "B mở 2", pics=[BINH])
    _viec(db, toi, du_an["id"], "A trễ", _ngay(-1), pics=[AN])
    kq = overview_service.overview(db, toi)
    assert [row["employee_id"] for row in kq["people"]] == [AN, BINH]


# ── Sức khỏe dự án ──────────────────────────────────────────────────────────

def test_suc_khoe_du_an_theo_nguong_va_bo_viec_huy_khoi_mau_so(db, toi):
    def tao(ten):
        return list_service.create_list(db, toi, schema.ListCreate(name=ten))["id"]

    on, rui_ro, tre, rong = tao("Ổn"), tao("Rủi ro"), tao("Trễ"), tao("Chưa có việc")
    _viec(db, toi, on, "Mở", _ngay(3))
    _viec(db, toi, on, "Xong", xong_cach_day=1)
    _viec(db, toi, on, "Hủy", huy=True)
    for i in range(4):
        _viec(db, toi, rui_ro, f"Mở {i}", _ngay(3))
    _viec(db, toi, rui_ro, "Trễ 1", _ngay(-1))     # 1/5 = 20% < 25%: Có rủi ro
    _viec(db, toi, tre, "Mở", _ngay(3))
    _viec(db, toi, tre, "Trễ", _ngay(-1))          # 1/2 = 50%: Trễ

    rows = {r["name"]: r for r in overview_service.overview(db, toi)["projects"]}
    assert rows["Ổn"]["health"] == 1 and rows["Ổn"]["health_label"] == "Đúng tiến độ"
    assert rows["Ổn"]["total"] == 2 and rows["Ổn"]["progress"] == 50   # việc hủy không vào mẫu số
    assert rows["Ổn"]["done_in_period"] == 1
    assert rows["Rủi ro"]["health"] == 2
    assert rows["Trễ"]["health"] == 3
    #  Bảng trống không được khen "Đúng tiến độ" — nhãn riêng, xếp cuối.
    assert rows["Chưa có việc"]["health"] == 0 and rows["Chưa có việc"]["health_label"] == "Chưa có việc"
    assert rows["Chưa có việc"]["total"] == 0 and rows["Chưa có việc"]["progress"] == 0
    assert list(rows)[0] == "Trễ" and list(rows)[-1] == "Chưa có việc"


def test_xong_trong_ky_theo_du_an_bo_viec_xong_ngoai_ky(db, toi, du_an):
    _viec(db, toi, du_an["id"], "Xong hôm qua", xong_cach_day=1)
    _viec(db, toi, du_an["id"], "Xong 40 ngày trước", xong_cach_day=40)
    row = overview_service.overview(db, toi, period_days=30)["projects"][0]
    assert row["done"] == 2 and row["done_in_period"] == 1


def test_du_an_luu_tru_khong_vao_bang_suc_khoe(db, toi, du_an):
    db.get(WorkList, du_an["id"]).is_archived = 1
    db.commit()
    assert overview_service.overview(db, toi)["projects"] == []


# ── Cần xử lý ngay ──────────────────────────────────────────────────────────

def test_viec_chua_ai_nhan_va_chua_dat_han(db, toi, du_an):
    lid = du_an["id"]
    _viec(db, toi, lid, "Chưa ai nhận, có hạn", _ngay(2))
    _viec(db, toi, lid, "Chưa ai nhận, không hạn")
    _viec(db, toi, lid, "Có người, không hạn", pics=[AN])
    _viec(db, toi, lid, "Chỉ có người theo dõi", _ngay(4), followers=[AN])
    _viec(db, toi, lid, "Đã xong không ai nhận", xong_cach_day=1)

    kq = overview_service.overview(db, toi)
    assert kq["task_unassigned"] == 3          # người theo dõi không phải người nhận việc; việc xong không tính
    assert [t["title"] for t in kq["unassigned_tasks"]] == [
        "Chưa ai nhận, có hạn", "Chỉ có người theo dõi", "Chưa ai nhận, không hạn"]
    assert kq["task_no_due"] == 2
    assert {t["title"] for t in kq["no_due_tasks"]} == {"Chưa ai nhận, không hạn", "Có người, không hạn"}


def test_viec_cua_mot_nguoi_chi_trong_pham_vi_va_qua_han_truoc(db, toi, du_an):
    _viec(db, toi, du_an["id"], "Không hạn", pics=[AN])
    _viec(db, toi, du_an["id"], "Hạn tới", _ngay(5), pics=[AN])
    _viec(db, toi, du_an["id"], "Quá hạn", _ngay(-3), pics=[AN])
    _viec(db, toi, du_an["id"], "Đã xong", _ngay(-3), pics=[AN], xong_cach_day=1)
    ten = {du_an["id"]: "Kho Quý 4"}

    rows = overview_people.person_tasks(db, {du_an["id"]}, AN, _ngay(0), ten)
    assert [r["title"] for r in rows] == ["Quá hạn", "Hạn tới", "Không hạn"]
    assert rows[0]["overdue"] is True and rows[0]["list_name"] == "Kho Quý 4"
    #  Ngoài phạm vi (không dự án nào) thì rỗng — không lộ việc ở dự án khác.
    assert overview_people.person_tasks(db, set(), AN, _ngay(0), ten) == []


# ── Hiệu năng ───────────────────────────────────────────────────────────────

def test_so_cau_sql_khong_tang_theo_so_nguoi(db, toi, du_an):
    eng = db.get_bind()

    def dem():
        stmts = []

        def on(conn, cursor, statement, *a):
            stmts.append(statement)
        event.listen(eng, "before_cursor_execute", on)
        try:
            overview_service.overview(db, toi)
        finally:
            event.remove(eng, "before_cursor_execute", on)
        return len(stmts)

    _viec(db, toi, du_an["id"], "Một người", _ngay(-1), pics=[AN])
    it = dem()
    for emp in range(100, 130):
        _viec(db, toi, du_an["id"], f"Người {emp}", _ngay(-emp % 7), pics=[emp])
    assert it > 0 and dem() == it


# ── Báo cáo riêng một dự án ─────────────────────────────────────────────────

def test_bao_cao_rieng_mot_du_an_chi_dem_du_an_do(db, toi, du_an):
    khac = list_service.create_list(db, toi, schema.ListCreate(name="Dự án khác"))["id"]
    _viec(db, toi, du_an["id"], "Trễ trong dự án", _ngay(-2), pics=[AN])
    _viec(db, toi, khac, "Trễ dự án khác", _ngay(-3), pics=[BINH])
    _viec(db, toi, khac, "Mở dự án khác", pics=[BINH])

    kq = overview_service.overview(db, toi, list_id=du_an["id"])
    assert kq["task_open"] == 1 and kq["task_overdue"] == 1
    assert [p["employee_id"] for p in kq["people"]] == [AN]
    assert [p["list_id"] for p in kq["projects"]] == [du_an["id"]]
    assert [t["title"] for t in kq["overdue_tasks"]] == ["Trễ trong dự án"]


def test_bao_cao_du_an_ngoai_pham_vi_ra_bo_so_rong(db, toi, du_an):
    _viec(db, toi, du_an["id"], "Việc", _ngay(-1), pics=[AN])
    nguoi_la = Actor(user_id=9, employee_id=999, company_id=COMPANY)
    kq = overview_service.overview(db, nguoi_la, list_id=du_an["id"])
    assert kq["task_open"] == 0 and kq["people"] == [] and kq["projects"] == []
