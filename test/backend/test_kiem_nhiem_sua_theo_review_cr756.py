"""duoc-CR-756 — SỬA THEO RÀ MÃ (13/11/2026): C1 (L2 theo công ty phải tôn trọng ô "Chỉ trong công ty" / "Loại trừ công ty"
của TỪNG grant), N1 (đọc-có-khóa + nạp lại sau khóa hàng hồ sơ cha), G1 (công ty ngừng hoạt động), G2 (Áp QTCT trùng chính),
N3 (nhật ký MỞ / ĐÓNG phạm vi khi dòng loại Công ty bật / tắt).

C1 là lỗ L2: cấu hình `all` + "Chỉ trong công ty A" là cách DUY NHẤT cho một người có phạm vi pháp nhân hẹp, mà L2 cũ thấy
`all` là qua ngay. Mỗi chốt có cặp đối chứng ở chiều ngược (công ty nằm trong ô thì VẪN được) — chặn sạch thì bài nào cũng xanh.
N1 chỉ chứng minh được bằng câu SQL biên dịch sang MySQL (SQLite bỏ qua khóa).
"""
import json
from datetime import timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import event, text
from sqlalchemy.dialects import mysql

from app.core.hr_work_history_codes import WorkEventType
from app.core.vn_time import vn_today
from app.modules.audit.model import AuditLog
from app.modules.company.model import Company
from app.modules.employee import concurrent_company_change_service as company_change
from app.modules.employee import concurrent_controller as cc
from app.modules.employee import concurrent_scope_audit as scope_audit
from app.modules.employee import concurrent_service
from app.modules.employee import concurrent_transition_service as transition
from app.modules.employee import department_service as dv
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.concurrent_schema import ConcurrentIn, ConcurrentPatch
from app.modules.employee.model import Employee
from app.modules.employee.work_history_model import EmployeeWorkHistory
from kiem_nhiem_factory import DAY, TODAY, build_kn_world, kc, kn

FROM = TODAY - 30 * DAY
OPEN, CLOSE = scope_audit.ACTION_SCOPE_OPEN, scope_audit.ACTION_SCOPE_CLOSE


@pytest.fixture()
def w(world):
    """Thế giới mẫu + công ty C + phòng SH / C.kt. a1, a2, a3 ở công ty A; b1 ở B; c1 ở C."""
    return build_kn_world(world)


def hr_all(w, key="a1", **kw):
    """HR `employee.read/write` bậc `all`; `inc_company` / `exc_company` là hai ô công ty của grant đó."""
    return w.grant(key, "employee", scope="all", actions=("read", "write"), **kw)


def co_in(w, company_key: str, **kw) -> ConcurrentIn:
    base = dict(kind=2, company_id=w.co[company_key], from_date=FROM)
    base.update(kw)
    return ConcurrentIn(**base)


def create(w, actor, emp_key: str, company_key: str, **kw):
    return cc.create_concurrent(w.emp[emp_key], co_in(w, company_key, **kw), w.db, actor.user)


def seat_rows(w, emp_key: str) -> list[EmployeeConcurrent]:
    w.db.expire_all()
    return w.db.query(EmployeeConcurrent).filter(EmployeeConcurrent.employee_id == w.emp[emp_key],
                                                 EmployeeConcurrent.kind == 2).all()


def row_id(resp) -> int:
    return json.loads(resp.body)["data"]["item"]["id"]


# ══════════════════════════════════════════════════════════════════════════════
#  C1 — L2 theo công ty tôn trọng inc / exc của grant
# ══════════════════════════════════════════════════════════════════════════════

def test_c1_probe_all_chi_trong_cong_ty_a_gan_loai_cong_ty_c_bi_403_khong_tao_dong(w):
    """Tái hiện probe của rà mã: a1 `all` + "Chỉ trong công ty A" gán kiêm nhiệm cả công ty C cho a3 -> 403, không tạo dòng."""
    a1 = hr_all(w, inc_company=["A"])
    with pytest.raises(HTTPException) as err:
        create(w, a1, "a3", "C")
    assert err.value.status_code == 403 and "Công ty C" in err.value.detail
    assert seat_rows(w, "a3") == []


def test_c1_doi_chieu_cong_ty_nam_trong_o_chi_trong_cong_ty_thi_duoc(w):
    a1 = hr_all(w, inc_company=["A", "C"])
    assert create(w, a1, "a3", "C").status_code == 201
    assert len(seat_rows(w, "a3")) == 1


def test_c1_bac_company_co_loai_tru_chinh_cong_ty_kiem_nhiem_bi_403(w):
    """a1 bậc `company` + có ghế công ty B + "Loại trừ công ty B" -> gán B cho người khác bị chặn; bỏ ô loại trừ thì được."""
    kc(w, "a1", "B")
    a1 = w.grant("a1", "employee", scope="company", actions=("read", "write"), exc_company=["B"])
    assert w.co["B"] in a1.profile().get("concurrent_companies", [])
    with pytest.raises(HTTPException) as err:
        create(w, a1, "a3", "B")
    assert err.value.status_code == 403
    assert seat_rows(w, "a3") == []

    kc(w, "a2", "B")
    a2 = w.grant("a2", "employee", scope="company", actions=("read", "write"))
    assert create(w, a2, "a3", "B").status_code == 201


def test_c1_don_vi_grant_khop_explicit_cond(w):
    """Hàm dùng chung `grant_writes_company` — từng bậc, ô chọn, ô loại trừ, ô chọn toàn rác."""
    def grant(scope, inc=None, exc=None):
        box = {"inc": {"company": inc} if inc is not None else {}, "exc": {"company": exc} if exc is not None else {}}
        return {"perms": {"employee": {"write": True, "scope": scope}}, "scope": box}

    reach = {1, 2}
    assert dv.grant_writes_company(grant("all"), 9, reach) is True                 # all không ràng công ty
    assert dv.grant_writes_company(grant("all", inc=[1]), 9, reach) is False       # ... trừ ô "Chỉ trong công ty"
    assert dv.grant_writes_company(grant("all", inc=[1, 9]), 9, reach) is True
    assert dv.grant_writes_company(grant("all", exc=[9]), 9, reach) is False
    assert dv.grant_writes_company(grant("all", inc=["rac"]), 9, reach) is False   # ô có giá trị mà không dùng được: chặn
    assert dv.grant_writes_company(grant("company"), 2, reach) is True
    assert dv.grant_writes_company(grant("company"), 9, reach) is False            # ngoài tầm công ty
    assert dv.grant_writes_company(grant("company", exc=[2]), 2, reach) is False
    assert dv.grant_writes_company(grant("company", inc=[1]), 2, reach) is False
    assert dv.grant_writes_company(grant("dept"), 9, reach) is False
    #  Xét TỪNG grant rồi OR (giữ sửa N3 của CR-755): một grant hẹp không kéo grant rộng xuống.
    profile = {"company_id": 1, "grants": [grant("all", inc=[1]), grant("all", inc=[9])]}
    assert dv.company_in_write_scope(profile, 9) is True
    assert dv.company_in_write_scope(profile, 5) is False


def test_c1_pair_va_doi_phong_chinh_cung_ton_trong_o_cong_ty(w):
    """`pair_in_write_scope` (loại Phòng ban + đổi phòng chính) cùng đường với loại Công ty."""
    hr = hr_all(w, inc_company=["A"])
    profile = hr.profile()
    assert dv.pair_in_write_scope(w.db, profile, w.dept["A.kt"], w.co["A"]) is True
    assert dv.pair_in_write_scope(w.db, profile, w.dept["C.kt"], w.co["C"]) is False
    with pytest.raises(HTTPException) as err:           # đổi phòng CHÍNH của hồ sơ công ty C
        dv.block_out_of_scope_primary_department(w.db, w.dept["C.kt"], w.co["C"], profile)
    assert err.value.status_code == 403
    dv.block_out_of_scope_primary_department(w.db, w.dept["A.kt"], w.co["A"], profile)   # đối chứng: được

    excl = hr_all(w, key="a2", exc_company=["A"])
    assert dv.pair_in_write_scope(w.db, excl.profile(), w.dept["A.kt"], w.co["A"]) is False


def test_c1_giu_ghe_cong_ty_cu_khi_doi_phap_nhan_cung_bi_chan(w):
    """`check_keep_company_seat` -> L2 loại Công ty: all + chỉ A không giữ ghế ở công ty cũ C."""
    a1 = hr_all(w, inc_company=["A"])
    emp = w.db.get(Employee, w.emp["a3"])
    with pytest.raises(HTTPException) as err:
        company_change.check_keep_company_seat(w.db, emp, w.co["C"], a1.user, a1.profile())
    assert err.value.status_code == 403
    company_change.check_keep_company_seat(w.db, emp, w.co["A"], a1.user, a1.profile())   # đối chứng


def test_c1_hoan_tac_lo_revert_problems_va_restore_ended_dung_chot_moi(w):
    """Dòng loại Công ty ở C bị kết thúc do lô nhập; người hoàn tác `all` + chỉ A thì bị từ chối."""
    row = kc(w, "a3", "C", to_date=TODAY - DAY)
    entries = [[row.id, None, (TODAY - DAY).isoformat()]]
    a1 = hr_all(w, inc_company=["A"])
    emp = w.db.get(Employee, w.emp["a3"])
    problems = company_change.revert_problems(w.db, emp, entries, a1.profile())
    assert problems and "Công ty C" in problems[0]
    with pytest.raises(HTTPException):
        company_change.restore_ended(w.db, emp, entries, a1.profile(), actor_id=a1.user.id)
    ok = hr_all(w, key="a2", inc_company=["A", "C"])
    assert company_change.revert_problems(w.db, emp, entries, ok.profile()) == []


def test_c1_tab_sua_dong_sang_cong_ty_ngoai_o_cung_403(w):
    """Sửa dòng B -> C qua PATCH: dòng MỚI ở C ngoài ô "Chỉ trong công ty" -> 403, dòng giữ nguyên."""
    row = kc(w, "a3", "B")
    a1 = hr_all(w, inc_company=["A", "B"])
    with pytest.raises(HTTPException) as err:
        cc.update_concurrent(w.emp["a3"], row.id, ConcurrentPatch(company_id=w.co["C"]), w.db, a1.user)
    assert err.value.status_code == 403
    assert seat_rows(w, "a3")[0].company_id == w.co["B"]


# ══════════════════════════════════════════════════════════════════════════════
#  N1 — đọc-có-khóa + nạp lại sau khóa hàng hồ sơ cha (soi SQL biên dịch sang MySQL)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def mysql_view(w):
    seen: list[str] = []

    def spy(state):
        if state.is_select:
            seen.append(str(state.statement.compile(dialect=mysql.dialect())))

    event.listen(w.db, "do_orm_execute", spy)
    yield seen
    event.remove(w.db, "do_orm_execute", spy)


LOCK_MARKS = ("FOR UPDATE", "FOR SHARE", "LOCK IN SHARE MODE")


def _lock_index(seen: list[str]) -> int:
    for i, sql in enumerate(seen):
        if "FROM tab_employee " in sql and "FOR UPDATE" in sql:
            return i
    return -1


def _unlocked_concurrent_reads(seen: list[str], after: int) -> list[str]:
    """SELECT trên bảng kiêm nhiệm SAU khóa mà không đọc-có-khóa."""
    return [sql for sql in seen[after + 1:] if "FROM tab_employee_concurrent" in sql
            and not any(mark in sql for mark in LOCK_MARKS)]


def test_n1_lock_employee_row_nap_lai_ho_so_va_khong_mat_thay_doi_chua_ghi(w):
    emp = w.db.get(Employee, w.emp["a3"])
    emp.company_id = w.co["B"]                                    # chưa flush (autoflush tắt)
    got = concurrent_service.lock_employee_row(w.db, emp.id)
    assert got is emp and emp.company_id == w.co["B"], "populate_existing không được đè ô vừa gán"
    assert w.db.execute(text("select company_id from tab_employee where id = :i"), {"i": emp.id}).scalar() == w.co["B"]


def test_n1_lock_employee_row_thay_thay_doi_cua_giao_dich_khac(w):
    """Giao dịch khác vừa đổi `company_id` (UPDATE thẳng): sau khóa, `emp.company_id` phải là giá trị MỚI."""
    emp = w.db.get(Employee, w.emp["a3"])
    assert emp.company_id == w.co["A"]
    w.db.execute(text("update tab_employee set company_id = :c where id = :i"), {"c": w.co["C"], "i": emp.id})
    assert emp.company_id == w.co["A"], "điều kiện đầu: bản trong bộ nhớ còn cũ"
    concurrent_service.lock_employee_row(w.db, emp.id)
    assert emp.company_id == w.co["C"]


def test_n1_tao_va_sua_kiem_nhiem_moi_select_bang_dong_sau_khoa_deu_co_khoa(w, mysql_view):
    boss = hr_all(w)
    profile, emp = boss.profile(), w.db.get(Employee, w.emp["a3"])
    mysql_view.clear()
    row = concurrent_service.create_concurrent(w.db, emp, co_in(w, "B"), boss.user, profile)
    lock = _lock_index(mysql_view)
    assert lock >= 0 and _unlocked_concurrent_reads(mysql_view, lock) == [], mysql_view
    assert any("FROM tab_employee_concurrent" in s for s in mysql_view[lock:]), "phải có truy vấn đếm / chồng giai đoạn"

    mysql_view.clear()
    concurrent_service.update_concurrent(w.db, emp, row.id, ConcurrentPatch(note="x"), boss.user, profile)
    lock = _lock_index(mysql_view)
    assert lock >= 0 and _unlocked_concurrent_reads(mysql_view, lock) == [], mysql_view
    assert any("FROM tab_employee_concurrent" in s and "FOR UPDATE" in s for s in mysql_view[lock:]), "đọc dòng sửa"


def test_n1_doi_phap_nhan_giu_ghe_giu_phong_cu_va_ap_qtct_doc_co_khoa(w, mysql_view):
    boss = hr_all(w)
    profile, emp = boss.profile(), w.db.get(Employee, w.emp["a3"])

    mysql_view.clear()                                    # đổi pháp nhân A -> B: end_rows_at_company
    company_change.end_rows_at_company(w.db, emp, w.co["A"], w.co["B"], boss.user.id)
    lock = _lock_index(mysql_view)
    assert lock >= 0 and _unlocked_concurrent_reads(mysql_view, lock) == [], ("end_rows", mysql_view)

    mysql_view.clear()                                    # giữ ghế công ty cũ (emp.company_id vẫn là A trong ca này)
    emp.company_id = w.co["B"]
    company_change.keep_company_seat(w.db, emp, w.co["A"], boss.user, profile)
    lock = _lock_index(mysql_view)
    assert lock >= 0 and _unlocked_concurrent_reads(mysql_view, lock) == [], ("keep_seat", mysql_view)

    mysql_view.clear()                                    # giữ phòng cũ (cùng công ty)
    transition.create_from_kept_department(w.db, emp, w.dept["A.kt"], boss.user.id)
    lock = _lock_index(mysql_view)
    assert lock >= 0 and _unlocked_concurrent_reads(mysql_view, lock) == [], ("kept_dept", mysql_view)

    wh = EmployeeWorkHistory(employee_id=emp.id, event_type=int(WorkEventType.CONCURRENT), from_date=FROM,
                             company_id=w.co["C"], created_by=1, updated_by=1)
    w.db.add(wh)
    w.db.commit()
    mysql_view.clear()                                    # Áp QTCT
    transition.upsert_from_work_history(w.db, emp, wh, boss.user, profile)
    lock = _lock_index(mysql_view)
    assert lock >= 0 and _unlocked_concurrent_reads(mysql_view, lock) == [], ("upsert", mysql_view)

    mysql_view.clear()                                    # hoàn tác lô
    ended = [[seat_rows(w, "a3")[0].id, None, (TODAY - DAY).isoformat()]]
    company_change.restore_ended(w.db, emp, ended, profile, actor_id=boss.user.id)
    assert any("FROM tab_employee_concurrent" in s and "FOR UPDATE" in s for s in mysql_view), mysql_view


# ══════════════════════════════════════════════════════════════════════════════
#  G1 — công ty ngừng hoạt động; G2 — Áp QTCT trùng chính
# ══════════════════════════════════════════════════════════════════════════════

def test_g1_gan_loai_cong_ty_vao_cong_ty_ngung_hoat_dong_la_400(w):
    boss = hr_all(w)
    w.db.get(Company, w.co["C"]).is_active = False
    w.db.commit()
    with pytest.raises(HTTPException) as err:
        create(w, boss, "a3", "C")
    assert err.value.status_code == 400 and "ngừng hoạt động" in err.value.detail
    assert seat_rows(w, "a3") == []
    assert create(w, boss, "a3", "B").status_code == 201          # đối chứng: công ty đang hoạt động


def test_g1_sua_doi_sang_cong_ty_ngung_hoat_dong_cung_400_nhung_ap_qtct_da_ket_thuc_van_ghi_duoc(w):
    boss = hr_all(w)
    rid = row_id(create(w, boss, "a3", "B"))
    w.db.get(Company, w.co["C"]).is_active = False
    w.db.commit()
    with pytest.raises(HTTPException) as err:
        cc.update_concurrent(w.emp["a3"], rid, ConcurrentPatch(company_id=w.co["C"]), w.db, boss.user)
    assert err.value.status_code == 400
    concurrent_service.check_concurrent_target(w.db, w.co["C"], 0, 2, allow_inactive_company=True)   # lịch sử đã kết thúc


def test_g2_ap_lai_qtct_trung_cong_ty_va_phong_chinh_noi_ra_dong_cu_con_do(w):
    boss = hr_all(w)
    emp = w.db.get(Employee, w.emp["a3"])
    wh = EmployeeWorkHistory(employee_id=emp.id, event_type=int(WorkEventType.CONCURRENT), from_date=FROM,
                             company_id=w.co["B"], created_by=1, updated_by=1)
    w.db.add(wh)
    w.db.commit()
    first = transition.upsert_from_work_history(w.db, emp, wh, boss.user, boss.profile())
    assert first and len(seat_rows(w, "a3")) == 1

    wh.company_id, wh.department_id = w.co["A"], emp.department_id          # nay trùng công ty + phòng chính
    w.db.commit()
    msg = transition.upsert_from_work_history(w.db, emp, wh, boss.user, boss.profile())
    assert msg and "tab Kiêm nhiệm" in msg[0]
    assert len(seat_rows(w, "a3")) == 1, "dòng cũ giữ nguyên (không tự kết thúc)"

    other = EmployeeWorkHistory(employee_id=emp.id, event_type=int(WorkEventType.CONCURRENT), from_date=FROM,
                                company_id=w.co["A"], department_id=emp.department_id, created_by=1, updated_by=1)
    w.db.add(other)
    w.db.commit()
    assert transition.upsert_from_work_history(w.db, emp, other, boss.user, boss.profile()) == []   # đối chứng: chưa từng áp


# ══════════════════════════════════════════════════════════════════════════════
#  N3 — nhật ký mở / đóng phạm vi cho dòng loại Công ty
# ══════════════════════════════════════════════════════════════════════════════

def audit(w, action: str | None = None) -> list[AuditLog]:
    q = w.db.query(AuditLog).filter(AuditLog.action.in_([OPEN, CLOSE]) if action is None else AuditLog.action == action)
    return q.order_by(AuditLog.id).all()


def test_n3_tao_loai_cong_ty_bat_cong_tac_ghi_mot_dong_open(w):
    boss = hr_all(w)
    create(w, boss, "a3", "B")
    rows = audit(w)
    assert [r.action for r in rows] == [OPEN]
    log = rows[0]
    assert log.entity == "employee" and log.entity_id == w.emp["a3"] and log.doc_code == "A3"
    assert log.message == f"Mở phạm vi công ty Công ty B cho A3 Nhân sự a3 (kiêm nhiệm từ {FROM.strftime('%d/%m/%Y')})", log.message
    assert log.created_by == boss.user.id


def test_n3_tao_tat_cong_tac_khong_ghi_sua_tat_thanh_bat_ghi_open_bat_thanh_tat_ghi_close(w):
    boss = hr_all(w)
    rid = row_id(create(w, boss, "a3", "B", counts_scope=False))
    assert audit(w) == []
    cc.update_concurrent(w.emp["a3"], rid, ConcurrentPatch(counts_scope=True), w.db, boss.user)
    assert [r.action for r in audit(w)] == [OPEN]
    cc.update_concurrent(w.emp["a3"], rid, ConcurrentPatch(note="chỉ sửa ghi chú"), w.db, boss.user)
    assert [r.action for r in audit(w)] == [OPEN], "không đổi trạng thái phạm vi thì không ghi thêm"
    cc.update_concurrent(w.emp["a3"], rid, ConcurrentPatch(counts_scope=False), w.db, boss.user)
    rows = audit(w)
    assert [r.action for r in rows] == [OPEN, CLOSE]
    assert rows[1].message.startswith("Đóng phạm vi công ty Công ty B của A3 Nhân sự a3")


def test_n3_doi_cong_ty_cua_dong_dang_bat_ghi_dong_cong_ty_cu_va_mo_cong_ty_moi(w):
    boss = hr_all(w)
    rid = row_id(create(w, boss, "a3", "B"))
    cc.update_concurrent(w.emp["a3"], rid, ConcurrentPatch(company_id=w.co["C"]), w.db, boss.user)
    rows = audit(w)
    assert [r.action for r in rows] == [OPEN, CLOSE, OPEN]
    assert "Công ty B" in rows[1].message and "đổi sang công ty khác" in rows[1].message
    assert "Công ty C" in rows[2].message


def test_n3_xoa_dong_dang_bat_ghi_close_xoa_dong_tat_khong_ghi(w):
    boss = hr_all(w)
    on = row_id(create(w, boss, "a3", "B"))
    off = row_id(create(w, boss, "a3", "C", counts_scope=False))
    assert len(audit(w)) == 1
    cc.delete_concurrent(w.emp["a3"], off, w.db, boss.user)
    assert len(audit(w)) == 1
    cc.delete_concurrent(w.emp["a3"], on, w.db, boss.user)
    assert [r.action for r in audit(w)] == [OPEN, CLOSE]
    assert "xóa dòng kiêm nhiệm" in audit(w, CLOSE)[0].message


def test_n3_dong_loai_phong_ban_khong_bao_gio_ghi(w):
    boss = hr_all(w)
    resp = cc.create_concurrent(w.emp["a3"], ConcurrentIn(kind=1, department_id=w.dept["A.kt"], from_date=FROM),
                                w.db, boss.user)
    rid = row_id(resp)
    cc.update_concurrent(w.emp["a3"], rid, ConcurrentPatch(counts_scope=False), w.db, boss.user)
    cc.update_concurrent(w.emp["a3"], rid, ConcurrentPatch(counts_scope=True), w.db, boss.user)
    cc.delete_concurrent(w.emp["a3"], rid, w.db, boss.user)
    assert audit(w) == []


def test_n3_ket_thuc_do_doi_phap_nhan_ghi_close_va_hoan_tac_ghi_open_lai(w):
    boss = hr_all(w)
    emp = w.db.get(Employee, w.emp["a3"])
    seat = kc(w, "a3", "C")
    result = company_change.end_rows_at_company(w.db, emp, w.co["A"], w.co["C"], boss.user.id)
    assert result.ended
    rows = audit(w)
    assert [r.action for r in rows] == [CLOSE]
    assert "kết thúc do đổi pháp nhân" in rows[0].message and "Công ty C" in rows[0].message
    company_change.restore_ended(w.db, emp, [[seat.id, None, (TODAY - DAY).isoformat()]], boss.profile(),
                                 actor_id=boss.user.id)
    assert [r.action for r in audit(w)] == [CLOSE, OPEN]


def test_n3_giu_ghe_cong_ty_cu_va_ap_qtct_loai_cong_ty_ghi_open(w):
    boss = hr_all(w)
    emp = w.db.get(Employee, w.emp["a3"])
    emp.company_id = w.co["B"]
    assert company_change.keep_company_seat(w.db, emp, w.co["A"], boss.user, boss.profile()) is True
    assert [r.action for r in audit(w)] == [OPEN] and "Công ty A" in audit(w)[0].message

    wh = EmployeeWorkHistory(employee_id=emp.id, event_type=int(WorkEventType.CONCURRENT), from_date=FROM,
                             company_id=w.co["C"], created_by=1, updated_by=1)
    w.db.add(wh)
    w.db.commit()
    transition.upsert_from_work_history(w.db, emp, wh, boss.user, boss.profile())
    assert [r.action for r in audit(w)] == [OPEN, OPEN]
    wh.to_date = TODAY - DAY                       # Áp lại sau khi QTCT đã kết thúc: dòng chỉ nhận to_date, công tắc giữ bật
    w.db.commit()
    transition.upsert_from_work_history(w.db, emp, wh, boss.user, boss.profile())
    assert [r.action for r in audit(w)] == [OPEN, OPEN], "công tắc không đổi -> không ghi thêm"


def test_n3_hai_ma_hanh_dong_co_trong_bo_ma_va_thuoc_nhom_phan_quyen():
    from app.core.action_catalog import ACTION_CATALOG, group_of_action
    from app.core.logging_codes import ACTION_GROUP_PERMISSION

    for code in (OPEN, CLOSE):
        assert code in ACTION_CATALOG and group_of_action(code) == ACTION_GROUP_PERMISSION
