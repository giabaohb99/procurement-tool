"""duoc-CR-667 (kh-CV1-2) — sửa bình luận của mình (E-05) và thùng rác có khôi phục (B-09).

Chạy đường thật: bình luận tạo qua `comment.controller.create_comment`, sửa qua
`task_comment_service`, thùng rác qua `task_trash_service`; RBAC dùng vai trò thật
(`cap_quyen`), không mock cổng quyền.
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import BackgroundTasks, HTTPException

from app.modules.comment import controller as comment_ct
from app.modules.comment.model import Comment
from app.modules.comment.schema import CommentIn
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.user.model import User
from app.modules.work import list_service, schema, task_comment_service, task_service, task_trash_service
from app.modules.work.membership_service import Actor
from app.modules.work.model import WorkMemberRole
from app.modules.work.task_model import WorkTask

COMPANY = 1
CHU, VIET, KHACH, NGOAI = (1, 11), (2, 22), (3, 33), (4, 44)   # (user_id, employee_id)


def _actor(p):
    return Actor(user_id=p[0], employee_id=p[1], company_id=COMPANY)


def _user(p):
    return SimpleNamespace(id=p[0], employee_id=p[1])


@pytest.fixture()
def d(db, cap_quyen):
    for uid, eid in (CHU, VIET, KHACH, NGOAI):
        db.add(Employee(id=eid, code=f"NV{eid}", full_name=f"Người {eid}", company_id=COMPANY))
        db.add(User(id=uid, email=f"u{uid}@dego.vn", employee_id=eid, is_active=True))
        cap_quyen(uid, "work_task", read=True, write=True, create=True, delete=True)
    db.commit()
    lst = list_service.create_list(db, _actor(CHU), schema.ListCreate(name="Dự án X"))
    list_service.add_member(db, _actor(CHU), lst["id"], schema.MemberIn(employee_id=VIET[1]))
    list_service.add_member(db, _actor(CHU), lst["id"],
                            schema.MemberIn(employee_id=KHACH[1], role=int(WorkMemberRole.VIEWER)))
    t = task_service.create_task(db, _actor(CHU), schema.TaskCreate(list_id=lst["id"], title="Việc 1"))
    return SimpleNamespace(db=db, list_id=lst["id"], task_id=t["id"])


# Bóc phong bì `success()` thành dict dữ liệu, bất kể kiểu trả về.
def _data(resp):
    import json
    return json.loads(resp.body)["data"] if hasattr(resp, "body") else resp["data"]


def _tao_bl(d, p, body="Xin chào"):
    resp = comment_ct.create_comment(CommentIn(entity="work_task", entity_id=d.task_id, body=body),
                                     BackgroundTasks(), d.db, _user(p))
    return _data(resp)["id"]


# ── E-05 sửa bình luận ──────────────────────────────────────────────────────────

def test_nguoi_viet_sua_duoc_va_co_dau_da_sua(d):
    cid = _tao_bl(d, VIET, "Bản đầu")
    #  Lùi `created_at` để `updated_at` do DB đóng dấu chắc chắn lớn hơn (SQLite chỉ chính xác tới giây).
    d.db.query(Comment).filter(Comment.id == cid).update(
        {Comment.created_at: datetime.utcnow() - timedelta(hours=1)})
    d.db.commit()

    out = task_comment_service.edit_comment(d.db, _actor(VIET), _user(VIET), d.task_id, cid, "  Bản sửa  ")
    assert out["body"] == "Bản sửa" and out["edited"] is True and out["can_edit"] is True
    assert d.db.get(Comment, cid).body == "Bản sửa"


def test_binh_luan_chua_sua_khong_co_dau_da_sua(d):
    cid = _tao_bl(d, VIET)
    fresh = comment_ct.list_comments("work_task", d.task_id, 10, 0, d.db, _user(VIET))
    item = _data(fresh)["items"][0]
    assert item["id"] == cid and item["edited"] is False and item["can_edit"] is True
    #  Người khác nhìn cùng bình luận thì KHÔNG có nút sửa.
    other = _data(comment_ct.list_comments("work_task", d.task_id, 10, 0, d.db, _user(CHU)))["items"][0]
    assert other["can_edit"] is False


def test_nguoi_khac_sua_la_403_ke_ca_chu_du_an(d):
    cid = _tao_bl(d, VIET, "Của Viết")
    for p in (CHU, NGOAI):
        with pytest.raises(HTTPException) as e:
            task_comment_service.edit_comment(d.db, _actor(p), _user(p), d.task_id, cid, "Đổi lời người khác")
        #  Chủ dự án: 403 "chỉ người viết"; người ngoài dự án: 403 từ cổng thành viên.
        assert e.value.status_code == 403
    assert d.db.get(Comment, cid).body == "Của Viết"


def test_khach_xem_khong_sua_duoc_du_la_nguoi_viet(d):
    """Khách xem viết được bình luận từ lúc còn là MEMBER, sau bị hạ quyền thì mất quyền sửa."""
    cid = _tao_bl(d, VIET)
    d.db.get(Comment, cid).created_by = KHACH[0]     # coi như KHÁCH là người viết
    d.db.commit()
    with pytest.raises(HTTPException) as e:
        task_comment_service.edit_comment(d.db, _actor(KHACH), _user(KHACH), d.task_id, cid, "Sửa")
    assert e.value.status_code == 403


def test_sua_rong_hoac_qua_dai_bi_chan_va_sai_viec_la_404(d):
    cid = _tao_bl(d, VIET)
    for bad in ("   ", "x" * 5001):
        with pytest.raises(HTTPException) as e:
            task_comment_service.edit_comment(d.db, _actor(VIET), _user(VIET), d.task_id, cid, bad)
        assert e.value.status_code == 400
    khac = task_service.create_task(d.db, _actor(CHU), schema.TaskCreate(list_id=d.list_id, title="Việc 2"))
    with pytest.raises(HTTPException) as e:
        task_comment_service.edit_comment(d.db, _actor(VIET), _user(VIET), khac["id"], cid, "Sửa")
    assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        task_comment_service.edit_comment(d.db, _actor(VIET), _user(VIET), d.task_id, 99999, "Sửa")
    assert e.value.status_code == 404


def test_sua_them_nhac_ten_chi_bao_nguoi_moi(d):
    cid = _tao_bl(d, VIET, f"Chào @[{CHU[0]}]")
    d.db.query(Notification).delete()
    d.db.commit()

    out = task_comment_service.edit_comment(
        d.db, _actor(VIET), _user(VIET), d.task_id, cid, f"Chào @[{CHU[0]}] và @[{KHACH[0]}]")
    assert {m["user_id"] for m in out["mentions"]} == {CHU[0], KHACH[0]}
    rows = d.db.query(Notification).all()
    assert [r.user_id for r in rows] == [KHACH[0]]         # CHU đã được nhắc từ trước -> không báo lại
    assert "nhắc tên" in rows[0].title

    out = task_comment_service.edit_comment(d.db, _actor(VIET), _user(VIET), d.task_id, cid, "Bỏ hết nhắc tên")
    assert out["mentions"] == []


def test_sua_nhac_ten_nguoi_ngoai_du_an_khong_chuong(d):
    """Thẻ `@[id]` gõ tay được ai cũng được — nhưng chuông (kèm tên việc) chỉ tới thành viên."""
    cid = _tao_bl(d, VIET, "Chào")
    d.db.query(Notification).delete()
    d.db.commit()
    out = task_comment_service.edit_comment(d.db, _actor(VIET), _user(VIET), d.task_id, cid,
                                            f"Chào @[{NGOAI[0]}]")
    assert {m["user_id"] for m in out["mentions"]} == {NGOAI[0]}   # thẻ vẫn lưu
    assert d.db.query(Notification).count() == 0


# ── B-09 thùng rác ──────────────────────────────────────────────────────────────

def _xoa(d, p, task_id):
    task_service.delete_task(d.db, _actor(p), task_id)


def test_thung_rac_liet_ke_viec_da_xoa_va_khoi_phuc_ca_viec_con(d):
    con = task_service.create_task(d.db, _actor(CHU), schema.TaskCreate(title="Con", parent_id=d.task_id))
    _xoa(d, CHU, d.task_id)

    rows = task_trash_service.list_trash(d.db, _actor(CHU), d.list_id)
    assert [r["id"] for r in rows] == [d.task_id]          # con đi theo cha, không liệt kê riêng
    assert rows[0]["can_restore"] is True and rows[0]["deleted_by_name"] == "Người 11"

    out = task_trash_service.restore_task(d.db, _actor(CHU), d.task_id)
    assert out["id"] == d.task_id
    assert d.db.get(WorkTask, d.task_id).deleted_at is None
    assert d.db.get(WorkTask, con["id"]).deleted_at is None
    assert task_trash_service.list_trash(d.db, _actor(CHU), d.list_id) == []


def test_con_xoa_rieng_tu_truoc_van_o_lai_thung_rac_khi_khoi_phuc_cha(d):
    con = task_service.create_task(d.db, _actor(CHU), schema.TaskCreate(title="Con", parent_id=d.task_id))
    _xoa(d, CHU, con["id"])
    #  Cố định hai mốc xóa khác nhau (SQLite/giây có thể trùng).
    d.db.get(WorkTask, con["id"]).deleted_at = datetime.utcnow() - timedelta(days=1)
    d.db.commit()
    _xoa(d, CHU, d.task_id)

    task_trash_service.restore_task(d.db, _actor(CHU), d.task_id)
    assert d.db.get(WorkTask, con["id"]).deleted_at is not None
    assert [r["id"] for r in task_trash_service.list_trash(d.db, _actor(CHU), d.list_id)] == [con["id"]]


def test_khong_khoi_phuc_con_khi_cha_con_trong_thung_rac(d):
    con = task_service.create_task(d.db, _actor(CHU), schema.TaskCreate(title="Con", parent_id=d.task_id))
    _xoa(d, CHU, d.task_id)
    with pytest.raises(HTTPException) as e:
        task_trash_service.restore_task(d.db, _actor(CHU), con["id"])
    assert e.value.status_code == 400


def test_viec_chua_xoa_khong_khoi_phuc_duoc(d):
    with pytest.raises(HTTPException) as e:
        task_trash_service.restore_task(d.db, _actor(CHU), d.task_id)
    assert e.value.status_code == 400


def test_member_chi_khoi_phuc_viec_minh_tao(d):
    """Cùng luật với XÓA: MEMBER chỉ động vào việc do mình tạo; quản trị khôi phục được mọi việc."""
    cua_chu = d.task_id
    cua_viet = task_service.create_task(
        d.db, _actor(VIET), schema.TaskCreate(list_id=d.list_id, title="Của Viết"))["id"]
    _xoa(d, CHU, cua_chu)
    _xoa(d, VIET, cua_viet)

    rows = {r["id"]: r for r in task_trash_service.list_trash(d.db, _actor(VIET), d.list_id)}
    assert rows[cua_viet]["can_restore"] is True and rows[cua_chu]["can_restore"] is False
    with pytest.raises(HTTPException) as e:
        task_trash_service.restore_task(d.db, _actor(VIET), cua_chu)
    assert e.value.status_code == 403
    task_trash_service.restore_task(d.db, _actor(VIET), cua_viet)

    task_trash_service.restore_task(d.db, _actor(CHU), cua_chu)       # OWNER khôi phục mọi việc
    assert d.db.get(WorkTask, cua_chu).deleted_at is None


def test_nguoi_ngoai_va_khach_xem_khong_thay_thung_rac(d):
    _xoa(d, CHU, d.task_id)
    for p in (NGOAI, KHACH):
        with pytest.raises(HTTPException) as e:
            task_trash_service.list_trash(d.db, _actor(p), d.list_id)
        assert e.value.status_code == 403
        with pytest.raises(HTTPException) as e:
            task_trash_service.restore_task(d.db, _actor(p), d.task_id)
        assert e.value.status_code == 403
    assert d.db.get(WorkTask, d.task_id).deleted_at is not None


def test_khoi_phuc_viec_ve_cot_dau_khi_cot_cu_da_bi_xoa(d):
    """Cột bị xóa trong lúc việc nằm thùng rác -> việc sống lại phải có cột, không mất khỏi kanban."""
    t = d.db.get(WorkTask, d.task_id)
    cot_cu = t.section_id
    _xoa(d, CHU, d.task_id)
    d.db.get(WorkTask, d.task_id).section_id = None       # mô phỏng FK `SET NULL` khi cột bị xóa
    d.db.commit()

    out = task_trash_service.restore_task(d.db, _actor(CHU), d.task_id)
    assert out["section_id"] == cot_cu                    # cột đầu tiên của dự án


def test_du_an_da_luu_tru_khoa_khoi_phuc(d):
    _xoa(d, CHU, d.task_id)
    list_service.archive_list(d.db, _actor(CHU), d.list_id)
    with pytest.raises(HTTPException) as e:
        task_trash_service.restore_task(d.db, _actor(CHU), d.task_id)
    assert e.value.status_code in (400, 403, 409)
    rows = task_trash_service.list_trash(d.db, _actor(CHU), d.list_id)
    assert rows[0]["can_restore"] is False
