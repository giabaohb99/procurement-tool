"""duoc-CR-666 (kh-CV1-1) — Công việc nối vào chuông thông báo (W3: F-01, F-02, F-04).

Mọi bài chạy ĐƯỜNG THẬT: service giao việc / đổi trạng thái / bình luận gọi hàm tạo
thông báo thật và ghi `tab_notification` xuống DB — KHÔNG mock hàm tạo thông báo
(bài học CR-662: mock làm đường thật chưa từng chạy, lỗi lộ ra trên máy thật).
Chỉ có Web Push là bị bỏ qua (không có khóa VAPID trong test).

Ba mệnh đề:

1. F-01 giao việc -> chuông CHỈ người MỚI được giao, không bao giờ chính người giao.
2. F-04 đổi trạng thái / bình luận -> chuông PIC + người theo dõi.
3. F-02 việc Dự án vào tab «Việc cần làm», và tab vẫn là TẬP CHA của chuông cảnh báo
   (bất biến CR-215) — kèm điều kiện: chỉ PIC, chỉ việc mở, còn là thành viên.
"""
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks

from app.modules.alert import controller as alert_ct
from app.modules.comment import controller as comment_ct
from app.modules.comment.schema import CommentIn
from app.modules.dashboard import controller as dash_ct
from app.modules.dashboard.service import dismiss_keys
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.purchase_order.model import PODelivery, POItem, PurchaseOrder
from app.modules.user.model import User
from app.modules.work import list_service, schema, task_service
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkTaskStatus
from app.modules.work.task_model import WorkTask

COMPANY = 1
# (user_id, employee_id) — người giao / người làm / người theo dõi
GIAO, LAM, THEO_DOI = (1, 11), (2, 22), (3, 33)


def _actor(p):
    return Actor(user_id=p[0], employee_id=p[1], company_id=COMPANY)


def _user(p):
    return SimpleNamespace(id=p[0], employee_id=p[1])


@pytest.fixture()
def du_lieu(db, cap_quyen):
    """Ba người có tài khoản + nhân sự thật, cùng là thành viên một dự án."""
    for uid, eid in (GIAO, LAM, THEO_DOI):
        db.add(Employee(id=eid, code=f"NV{eid}", full_name=f"Người {eid}", company_id=COMPANY))
        db.add(User(id=uid, email=f"u{uid}@dego.vn", employee_id=eid, is_active=True))
        cap_quyen(uid, "work_task", read=True, write=True, create=True, delete=True)
    db.commit()
    chu = _actor(GIAO)
    lst = list_service.create_list(db, chu, schema.ListCreate(name="Mua sắm Q4"))
    for p in (LAM, THEO_DOI):
        list_service.add_member(db, chu, lst["id"], schema.MemberIn(employee_id=p[1]))
    return SimpleNamespace(db=db, chu=chu, list_id=lst["id"])


def _tao(d, title="Chốt NCC", **kw):
    return task_service.create_task(d.db, d.chu, schema.TaskCreate(list_id=d.list_id, title=title, **kw))


def _chuong(db, p):
    return (db.query(Notification).filter(Notification.user_id == p[0])
            .order_by(Notification.id).all())


# ── 1. F-01 giao việc ───────────────────────────────────────────────────────────

def test_giao_viec_chuong_nguoi_duoc_giao_khong_chuong_nguoi_giao(du_lieu):
    d = du_lieu
    t = _tao(d, assignee_ids=[LAM[1]], due_date="2030-01-31")

    rows = _chuong(d.db, LAM)
    assert len(rows) == 1
    assert "Chốt NCC" in rows[0].title and rows[0].link == f"/project/tasks/{t['id']}"
    assert "hạn 2030-01-31" in rows[0].body
    assert rows[0].created_by == GIAO[0] and rows[0].is_read in (False, None)
    assert _chuong(d.db, GIAO) == [] and _chuong(d.db, THEO_DOI) == []


def test_tu_giao_cho_minh_khong_chuong(du_lieu):
    d = du_lieu
    _tao(d, assignee_ids=[GIAO[1]])
    assert d.db.query(Notification).count() == 0


def test_dat_lai_nguoi_phu_trach_chi_bao_nguoi_moi(du_lieu):
    """Lưu lại đúng bộ PIC cũ không được kêu chuông lần nữa — chuông ồn là chuông bị tắt."""
    d = du_lieu
    t = _tao(d, assignee_ids=[LAM[1]])
    task_service.set_assignees(d.db, d.chu, t["id"], [LAM[1]], [])
    assert len(_chuong(d.db, LAM)) == 1

    task_service.set_assignees(d.db, d.chu, t["id"], [LAM[1], THEO_DOI[1]], [])
    assert len(_chuong(d.db, LAM)) == 1          # người cũ không bị báo lại
    assert len(_chuong(d.db, THEO_DOI)) == 1     # người mới thì có


def test_giao_viec_nhan_su_chua_co_tai_khoan_khong_vo(du_lieu):
    """Nhân sự chưa có tài khoản thì không có chuông nào để kêu — nhưng việc vẫn giao được."""
    d = du_lieu
    d.db.add(Employee(id=99, code="NV99", full_name="Chưa có tài khoản", company_id=COMPANY))
    d.db.commit()
    t = _tao(d, assignee_ids=[99])
    assert d.db.query(Notification).count() == 0
    assert d.db.get(WorkTask, t["id"]) is not None


# ── 2. F-04 đổi trạng thái / bình luận ──────────────────────────────────────────

def test_doi_trang_thai_bao_pic_va_nguoi_theo_doi_tru_nguoi_doi(du_lieu):
    d = du_lieu
    t = _tao(d, assignee_ids=[LAM[1]])
    task_service.set_assignees(d.db, d.chu, t["id"], [LAM[1]], [THEO_DOI[1]])
    d.db.query(Notification).delete()
    d.db.commit()

    task_service.update_task(d.db, d.chu, t["id"],
                             schema.TaskUpdate(status=int(WorkTaskStatus.DONE)))
    for p in (LAM, THEO_DOI):
        rows = _chuong(d.db, p)
        assert len(rows) == 1 and "hoàn thành" in rows[0].title
    assert _chuong(d.db, GIAO) == []


def test_sua_tieu_de_khong_doi_trang_thai_thi_khong_chuong(du_lieu):
    d = du_lieu
    t = _tao(d, assignee_ids=[LAM[1]])
    d.db.query(Notification).delete()
    d.db.commit()
    task_service.update_task(d.db, d.chu, t["id"], schema.TaskUpdate(title="Đổi tên"))
    assert d.db.query(Notification).count() == 0


def test_nguoi_lam_tu_doi_trang_thai_thi_chi_bao_nguoi_con_lai(du_lieu):
    d = du_lieu
    t = _tao(d, assignee_ids=[LAM[1]])
    task_service.set_assignees(d.db, d.chu, t["id"], [LAM[1]], [THEO_DOI[1]])
    d.db.query(Notification).delete()
    d.db.commit()
    task_service.update_task(d.db, _actor(LAM), t["id"],
                             schema.TaskUpdate(status=int(WorkTaskStatus.DONE)))
    assert _chuong(d.db, LAM) == []
    assert len(_chuong(d.db, THEO_DOI)) == 1


def test_binh_luan_bao_pic_va_nguoi_theo_doi(du_lieu):
    """Đi cả đường thật `POST /api/comments`: người theo dõi chưa từng bình luận vẫn nhận chuông."""
    d = du_lieu
    t = _tao(d)
    task_service.set_assignees(d.db, d.chu, t["id"], [LAM[1]], [THEO_DOI[1]])
    d.db.query(Notification).delete()
    d.db.commit()

    comment_ct.create_comment(CommentIn(entity="work_task", entity_id=t["id"], body="Báo giá về rồi"),
                              BackgroundTasks(), d.db, _user(GIAO))
    for p in (LAM, THEO_DOI):
        rows = _chuong(d.db, p)
        assert len(rows) == 1 and "Bình luận mới" in rows[0].title
        assert rows[0].link == f"/project/tasks/{t['id']}"
    assert _chuong(d.db, GIAO) == []


def _go_khoi_du_an(d, p):
    """Gỡ người khỏi dự án — dòng PIC/theo dõi của họ trên việc VẪN CÒN (đúng như chạy thật)."""
    from app.modules.work.model import WorkListMember
    (d.db.query(WorkListMember)
     .filter(WorkListMember.list_id == d.list_id, WorkListMember.employee_id == p[1]).delete())
    d.db.commit()


def test_nguoi_da_roi_du_an_khong_nhan_chuong_trang_thai_va_binh_luan(du_lieu):
    """Chuông mang tên việc + trích bình luận: người đã rời dự án không được nhận nữa."""
    d = du_lieu
    t = _tao(d, assignee_ids=[LAM[1]])
    task_service.set_assignees(d.db, d.chu, t["id"], [LAM[1]], [THEO_DOI[1]])
    _go_khoi_du_an(d, THEO_DOI)
    d.db.query(Notification).delete()
    d.db.commit()

    task_service.update_task(d.db, d.chu, t["id"], schema.TaskUpdate(status=int(WorkTaskStatus.DONE)))
    comment_ct.create_comment(
        CommentIn(entity="work_task", entity_id=t["id"], body=f"Xong rồi @[{THEO_DOI[0]}]"),
        BackgroundTasks(), d.db, _user(GIAO))
    assert _chuong(d.db, THEO_DOI) == []                 # cả chuông nhắc tên lẫn chuông chung
    assert len(_chuong(d.db, LAM)) == 2                  # người còn trong dự án vẫn đủ


def test_giao_cho_nhan_su_ngoai_du_an_khong_chuong(du_lieu):
    """Gán qua API một nhân sự không phải thành viên: không được lộ tên việc qua chuông."""
    d = du_lieu
    d.db.add(Employee(id=44, code="NV44", full_name="Người ngoài", company_id=COMPANY))
    d.db.add(User(id=4, email="u4@dego.vn", employee_id=44, is_active=True))
    d.db.commit()
    _tao(d, assignee_ids=[44])
    assert _chuong(d.db, (4, 44)) == []


def test_thanh_vien_mat_quyen_doc_cong_viec_khong_chuong(du_lieu, cap_quyen):
    d = du_lieu
    d.db.add(Employee(id=55, code="NV55", full_name="Không quyền đọc", company_id=COMPANY))
    d.db.add(User(id=5, email="u5@dego.vn", employee_id=55, is_active=True))
    d.db.commit()
    cap_quyen(5, "work_task", read=False)
    list_service.add_member(d.db, d.chu, d.list_id, schema.MemberIn(employee_id=55))
    _tao(d, assignee_ids=[55])
    assert _chuong(d.db, (5, 55)) == []


# ── 3. F-02 Việc cần làm + bất biến tập cha ─────────────────────────────────────

def _profile():
    perms = {"work_task": {"read": True, "scope": "all"}}
    return {"grants": [], "perms_union": perms, "company_id": COMPANY, "dept_id": 0, "dept_name": "",
            "employee_id": 0, "emp_code": "", "emp_name": ""}


def _jobs(db, p):
    return {t["key"]: t for t in dash_ct.build_my_tasks(db, _user(p), _profile()) if t["type"] == "job"}


def test_viec_du_an_vao_tab_viec_can_lam_chi_cua_pic(du_lieu):
    d = du_lieu
    t = _tao(d, assignee_ids=[LAM[1]], due_date="2000-01-01")
    task_service.set_assignees(d.db, d.chu, t["id"], [LAM[1]], [THEO_DOI[1]])

    jobs = _jobs(d.db, LAM)
    row = jobs[f"job:{t['id']}"]
    assert row["label"] == "Việc quá hạn" and row["link"] == f"/project/tasks/{t['id']}"
    assert "Mua sắm Q4" in row["subtitle"] and row["dismissed"] is False
    assert _jobs(d.db, THEO_DOI) == {}     # theo dõi không phải việc phải làm
    assert _jobs(d.db, GIAO) == {}


def test_viec_xong_bi_xoa_hoac_het_la_thanh_vien_thi_khong_con_trong_tab(du_lieu):
    d = du_lieu
    xong, xoa, roi = (_tao(d, title=n, assignee_ids=[LAM[1]]) for n in ("Xong", "Xóa", "Rời"))
    task_service.update_task(d.db, d.chu, xong["id"], schema.TaskUpdate(status=int(WorkTaskStatus.DONE)))
    task_service.delete_task(d.db, d.chu, xoa["id"])
    assert set(_jobs(d.db, LAM)) == {f"job:{roi['id']}"}

    # Bị gỡ khỏi dự án thì việc trong dự án đó không được hiện (không lộ việc dự án người ta không tham gia)
    from app.modules.work.model import WorkListMember
    d.db.query(WorkListMember).filter(WorkListMember.employee_id == LAM[1]).delete()
    d.db.commit()
    assert _jobs(d.db, LAM) == {}


def test_danh_dau_xong_an_duoc_viec_du_an(du_lieu):
    d = du_lieu
    t = _tao(d, assignee_ids=[LAM[1]])
    dismiss_keys(d.db, _user(LAM), [f"job:{t['id']}"])
    assert _jobs(d.db, LAM)[f"job:{t['id']}"]["dismissed"] is True


def test_tab_van_la_tap_cha_cua_chuong_canh_bao_khi_co_viec_du_an(du_lieu, monkeypatch):
    """Bất biến CR-215 mở rộng: thêm loại `job` KHÔNG được làm tab mất key nào của chuông."""
    d = du_lieu
    db = d.db
    po = PurchaseOrder(code="PO-9", company_id=COMPANY, status="ordered")
    db.add(po)
    db.flush()
    item = POItem(po_id=po.id, product_code="SP-1", product_name="Hàng 1")
    db.add(item)
    db.flush()
    db.add(PODelivery(po_id=po.id, po_item_id=item.id, received_qty=0, promised_date="2000-01-01"))
    t = _tao(d, assignee_ids=[LAM[1]])
    db.commit()

    perms = {e: {a: True for a in ("read", "create", "write", "delete", "approve", "cancel", "print", "export")}
             | {"scope": "all"} for e in ("purchase_order", "payable", "contract", "work_task",
                                          "purchase_request", "survey_request", "labor_contract")}
    prof = {"grants": [{"role_id": 1, "perms": perms, "scope": {"inc": {}, "exc": {}}}],
            "perms_union": perms, "company_id": COMPANY, "dept_id": 0, "dept_name": "",
            "employee_id": 0, "emp_code": "", "emp_name": ""}
    monkeypatch.setattr(alert_ct, "user_has_permission", lambda *a, **k: True)
    monkeypatch.setattr(alert_ct, "get_perm_profile", lambda _db, _u: prof)

    me = _user(LAM)
    chuong = {x["key"] for x in alert_ct.build(db, me)["items"]}
    tab = {x["key"] for x in dash_ct.build_my_tasks(db, me, prof)}
    assert chuong, "bài này vô nghĩa nếu chuông rỗng"
    assert chuong <= tab, f"chuông có mà tab thiếu: {chuong - tab}"
    assert f"job:{t['id']}" in tab and f"job:{t['id']}" not in chuong
