"""duoc-CR-755 — SỬA THEO RÀ MÃ (12/11/2026): C1 (L2 cho đổi phòng CHÍNH theo cặp), N2 (khóa hàng hồ sơ cha),
N3 (L2 theo cặp xét TỪNG grant).

C1 là lỗ L2 "vô công ty": cặp kiêm nhiệm khác công ty mở quyền GHI hồ sơ công ty B, nên đổi phòng chính chỉ so ID phòng
là để người ta đẩy nhân sự công ty B sang cặp (phòng, B) mà họ không phủ. Mỗi chốt có cặp đối chứng ở chiều ngược
(cặp phủ thì VẪN được), vì chặn sạch thì bài nào cũng xanh.
"""
import json
from datetime import timedelta

import pytest
from fastapi import HTTPException
from sqlalchemy import event
from sqlalchemy.dialects import mysql

from app.core.auth import perm_cache_clear
from app.core.hr_work_history_codes import WorkEventType
from app.core.vn_time import vn_today
from app.modules.department.model import Department
from app.modules.employee import concurrent_controller as cc
from app.modules.employee import concurrent_service
from app.modules.employee import controller as ctl
from app.modules.employee import department_service as dv
from app.modules.employee import work_history_apply_service as applysvc
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.concurrent_schema import ConcurrentIn, ConcurrentPatch
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeUpdate
from app.modules.employee.work_history_model import EmployeeWorkHistory

from test_nhap_excel_nhan_su_cr628 import errors, run_import, savepoint_that

TODAY = vn_today()
FROM = TODAY - timedelta(days=30)


@pytest.fixture()
def w(world):
    """Thế giới mẫu + phòng DÙNG CHUNG `SH` (company 0). a2 (A.kt, công ty A) ghi `employee` bậc phòng ban."""
    db = world.db
    row = Department(code="SH_DC", name="Phòng dùng chung", company_id=0, is_active=True)
    db.add(row)
    db.flush()
    world.dept["SH"] = row.id
    db.commit()
    return world


def pair(w, emp_key: str, dept_key: str, company_key: str) -> EmployeeConcurrent:
    """Dòng kiêm nhiệm hiệu lực + bật công tắc."""
    row = EmployeeConcurrent(employee_id=w.emp[emp_key], department_id=w.dept[dept_key], company_id=w.co[company_key],
                             from_date=FROM, counts_scope=True)
    w.db.add(row)
    w.db.commit()
    perm_cache_clear()
    return row


def dept_writer(w, key="a2"):
    return w.grant(key, "employee", scope="dept", actions=("read", "write"))


def dept_of(w, key: str) -> int:
    w.db.expire_all()
    return w.db.get(Employee, w.emp[key]).department_id


# ══════════════════════════════════════════════════════════════════════════════
#  C1 — PATCH hồ sơ
# ══════════════════════════════════════════════════════════════════════════════

def test_c1_patch_doi_phong_chinh_cong_ty_kia_sang_cap_khong_phu_bi_403(w):
    """Probe của báo cáo: a2 kiêm nhiệm (SH, A) + (B.kt, B) -> PATCH b1 (B, B.kt) sang SH. (SH, B) a2 KHÔNG phủ."""
    a2 = dept_writer(w)
    pair(w, "a2", "SH", "A")
    pair(w, "a2", "B.kt", "B")

    with pytest.raises(HTTPException) as err:
        ctl.update_employee(w.emp["b1"], EmployeeUpdate(department_id=w.dept["SH"]), w.db, a2.user)
    assert err.value.status_code == 403
    assert dept_of(w, "b1") == w.dept["B.kt"], "hồ sơ không bị đụng"


def test_c1_doi_chieu_cap_phu_thi_van_200(w):
    """Vế hợp lệ: a2 phủ cả (B.kt, B) lẫn (SH, B) -> đổi được."""
    a2 = dept_writer(w)
    pair(w, "a2", "B.kt", "B")
    pair(w, "a2", "SH", "B")

    ctl.update_employee(w.emp["b1"], EmployeeUpdate(department_id=w.dept["SH"]), w.db, a2.user)
    assert dept_of(w, "b1") == w.dept["SH"]


def test_c1_doi_chieu_cung_cong_ty_chinh_van_200(w):
    """Hồi quy: người bậc phòng ban đổi phòng chính nhân sự CÙNG công ty vào phòng trong tầm mình vẫn được."""
    a1 = dept_writer(w, "a1")
    pair(w, "a1", "SH", "A")        # SH vào dept_ids của a1 (cùng công ty chính)

    ctl.update_employee(w.emp["a2"], EmployeeUpdate(department_id=w.dept["SH"]), w.db, a1.user)
    assert dept_of(w, "a2") == w.dept["SH"]


def test_c1_patch_doi_ca_cong_ty_do_cong_ty_dich_la_cong_ty_moi(w):
    """Gửi cả `company_id` mới + phòng mới: cặp đích đo theo công ty MỚI (không phải công ty hiện tại của hồ sơ)."""
    a2 = dept_writer(w)
    pair(w, "a2", "B.kt", "B")
    pair(w, "a2", "SH", "A")        # (SH, A) phủ; (SH, B) không
    with pytest.raises(HTTPException) as err:
        ctl.update_employee(w.emp["b1"], EmployeeUpdate(department_id=w.dept["SH"], company_id=w.co["B"]), w.db, a2.user)
    assert err.value.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
#  C1 — Áp quá trình công tác (điều chuyển)
# ══════════════════════════════════════════════════════════════════════════════

def _transfer(w, key: str, dept_key: str) -> EmployeeWorkHistory:
    row = EmployeeWorkHistory(employee_id=w.emp[key], event_type=int(WorkEventType.TRANSFER), from_date=FROM,
                              department_id=w.dept[dept_key], created_by=1, updated_by=1)
    w.db.add(row)
    w.db.commit()
    return row


def test_c1_ap_dieu_chuyen_sang_cap_khong_phu_bi_403_con_cap_phu_thi_qua(w):
    a2 = dept_writer(w)
    pair(w, "a2", "SH", "A")
    pair(w, "a2", "B.kt", "B")
    wh = _transfer(w, "b1", "SH")
    with pytest.raises(HTTPException) as err:
        applysvc.apply(w.db, wh, a2.user, a2.profile())
    assert err.value.status_code == 403
    assert dept_of(w, "b1") == w.dept["B.kt"]

    pair(w, "a2", "SH", "B")        # đối chứng: nay cặp (SH, B) đã được phủ
    w.db.rollback()
    assert applysvc.apply(w.db, wh, a2.user, a2.profile())
    w.db.commit()
    assert dept_of(w, "b1") == w.dept["SH"]


# ══════════════════════════════════════════════════════════════════════════════
#  C1 — nhập Excel nhân sự
# ══════════════════════════════════════════════════════════════════════════════

def test_c1_nhap_excel_doi_phong_chinh_sang_cap_khong_phu_la_loi_dong(w):
    savepoint_that(w.db)
    a2 = dept_writer(w)
    pair(w, "a2", "SH", "A")
    pair(w, "a2", "B.kt", "B")
    b = run_import(w.db, [{"Mã NV *": "B1", "Phòng ban (mã)": "SH_DC"}], a2.user.id)
    assert b.error_count == 1, [e.message for e in errors(w.db, b.id)]
    assert dept_of(w, "b1") == w.dept["B.kt"]

    pair(w, "a2", "SH", "B")        # đối chứng
    b2 = run_import(w.db, [{"Mã NV *": "B1", "Phòng ban (mã)": "SH_DC"}], a2.user.id)
    assert b2.error_count == 0, [e.message for e in errors(w.db, b2.id)]
    assert dept_of(w, "b1") == w.dept["SH"]


def test_c1_hoan_tac_lo_nhap_do_cap_phong_cu_nguoi_hoan_tac_khong_phu_bi_chan(w):
    """Hoàn tác khôi phục phòng cũ: phải đo cặp (phòng cũ, công ty đích) như lúc nhập."""
    from app.modules.import_tool import employee_import_revert as revert
    from app.modules.import_tool.model import ImportChange

    savepoint_that(w.db)
    boss = w.grant("a1", "employee", scope="all", actions=("read", "write"))
    b = run_import(w.db, [{"Mã NV *": "B1", "Phòng ban (mã)": "SH_DC"}], boss.user.id)
    assert b.error_count == 0, [e.message for e in errors(w.db, b.id)]
    assert dept_of(w, "b1") == w.dept["SH"]
    changes = w.db.query(ImportChange).filter(ImportChange.batch_id == b.id).all()

    #  a2 ghi được hồ sơ b1 (nay ở (SH, B)) nhưng KHÔNG phủ phòng cũ (B.kt, B) -> chặn.
    a2 = dept_writer(w)
    pair(w, "a2", "SH", "B")
    problems = revert.revert_blockers(w.db, changes, a2.user.id, b)
    assert problems and "Không gán được phòng ban" in " ".join(problems), problems

    #  Đối chứng: phủ thêm (B.kt, B) thì hết bị chặn ở chốt phòng.
    pair(w, "a2", "B.kt", "B")
    assert not [p for p in revert.revert_blockers(w.db, changes, a2.user.id, b) if "Không gán được phòng ban" in p]


# ══════════════════════════════════════════════════════════════════════════════
#  N3 — L2 theo cặp xét TỪNG grant
# ══════════════════════════════════════════════════════════════════════════════

def test_n3_grant_cong_ty_a_cong_grant_dept_phu_cap_xb_thi_duoc_cap_xb(w):
    """Có grant `company` (A) + grant `dept` có cặp (X, B): cặp (X, B) phải được, không bị bậc rộng nhất nuốt."""
    actor = w.grant("a2", "employee", scope="company", actions=("read", "write"))
    actor.grant("employee", scope="dept", actions=("read", "write"))
    pair(w, "a2", "B.hc", "B")
    profile = actor.profile()
    assert dv.pair_in_write_scope(w.db, profile, w.dept["B.hc"], w.co["B"]) is True
    assert dv.pair_in_write_scope(w.db, profile, w.dept["A.mua"], w.co["A"]) is True      # bậc công ty vẫn đúng
    assert dv.pair_in_write_scope(w.db, profile, w.dept["B.kt"], w.co["B"]) is False      # cặp không phủ vẫn bị chặn


def test_n3_chi_co_grant_cong_ty_thi_cap_cong_ty_khac_van_bi_chan(w):
    actor = w.grant("a2", "employee", scope="company", actions=("read", "write"))
    pair(w, "a2", "B.hc", "B")
    #  Chỉ grant `company` (A): cặp kiêm nhiệm KHÔNG mở thêm quyền ghi ở công ty B qua bậc này.
    assert dv.pair_in_write_scope(w.db, actor.profile(), w.dept["B.hc"], w.co["B"]) is False
    assert dv.pair_in_write_scope(w.db, actor.profile(), w.dept["A.mua"], w.co["A"]) is True


def test_n3_gan_va_ket_thuc_dong_xb_qua_controller(w):
    """Hệ quả cũ: người có company(A)+dept(X,B) không gán / kết thúc nổi dòng (X, B) dù phạm vi ghi thật phủ nó."""
    boss = w.grant("a2", "employee", scope="company", actions=("read", "write"))
    boss.grant("employee", scope="dept", actions=("read", "write"))
    pair(w, "a2", "B.hc", "B")
    # a2 sửa được hồ sơ b1 qua cặp (B.hc, B)? b1 ở B.kt nên cần cặp (B.kt, B); thêm
    pair(w, "a2", "B.kt", "B")
    resp = cc.create_concurrent(w.emp["b1"], ConcurrentIn(company_id=w.co["B"], department_id=w.dept["B.hc"],
                                                          from_date=FROM), w.db, boss.user)
    assert resp.status_code == 201
    row_id = json.loads(resp.body)["data"]["item"]["id"]
    assert row_id


# ══════════════════════════════════════════════════════════════════════════════
#  N2 — khóa hàng hồ sơ cha trên mọi đường ghi dòng kiêm nhiệm
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def mysql_view(w):
    """Ghi lại mọi SELECT dưới dạng SQL MySQL (SQLite bỏ qua `FOR UPDATE`, không tái hiện được race)."""
    seen: list[str] = []

    def spy(state):
        if state.is_select:
            seen.append(str(state.statement.compile(dialect=mysql.dialect())))

    event.listen(w.db, "do_orm_execute", spy)
    yield seen
    event.remove(w.db, "do_orm_execute", spy)


def _employee_lock_index(seen: list[str]) -> int:
    """Vị trí câu `SELECT tab_employee.id ... FOR UPDATE` đầu tiên, -1 nếu không có."""
    for i, sql in enumerate(seen):
        if "FROM tab_employee " in sql and "FOR UPDATE" in sql and "tab_employee.id" in sql:
            return i
    return -1


def _first_concurrent_read(seen: list[str]) -> int:
    for i, sql in enumerate(seen):
        if "FROM tab_employee_concurrent" in sql:
            return i
    return len(seen)


def test_n2_lock_employee_row_bien_dich_sang_mysql_for_update(w, mysql_view):
    concurrent_service.lock_employee_row(w.db, w.emp["a2"])
    assert _employee_lock_index(mysql_view) == 0, mysql_view


def test_n2_tao_va_sua_khoa_ho_so_cha_truoc_khi_doc_dong_kiem_nhiem(w, mysql_view):
    boss = w.grant("a1", "employee", scope="all", actions=("read", "write"))
    profile, emp = boss.profile(), w.db.get(Employee, w.emp["a2"])     # dựng hồ sơ quyền TRƯỚC (nó cũng đọc bảng dòng)
    mysql_view.clear()
    row = concurrent_service.create_concurrent(
        w.db, emp, ConcurrentIn(company_id=w.co["B"], department_id=w.dept["B.hc"], from_date=FROM), boss.user, profile)
    lock, first = _employee_lock_index(mysql_view), _first_concurrent_read(mysql_view)
    assert 0 <= lock < first, ("khóa hồ sơ cha phải đi TRƯỚC đếm trần / chống chồng", mysql_view)

    mysql_view.clear()
    concurrent_service.update_concurrent(w.db, emp, row.id, ConcurrentPatch(note="x"), boss.user, profile)
    lock, first = _employee_lock_index(mysql_view), _first_concurrent_read(mysql_view)
    assert 0 <= lock < first, ("sửa", mysql_view)


def test_n2_ap_qtct_giu_phong_cu_doi_phap_nhan_va_hoan_tac_deu_khoa(w, mysql_view):
    from app.modules.employee import concurrent_transition_service as transition

    boss = w.grant("a1", "employee", scope="all", actions=("read", "write"))
    emp, profile = w.db.get(Employee, w.emp["a3"]), boss.profile()    # hồ sơ quyền dựng TRƯỚC khi soi SQL

    # Áp QTCT loại kiêm nhiệm
    wh = EmployeeWorkHistory(employee_id=emp.id, event_type=int(WorkEventType.CONCURRENT), from_date=FROM,
                             department_id=w.dept["B.hc"], company_id=w.co["B"], created_by=1, updated_by=1)
    w.db.add(wh)
    w.db.commit()
    mysql_view.clear()
    applysvc.apply(w.db, wh, boss.user, profile)
    assert 0 <= _employee_lock_index(mysql_view) < _first_concurrent_read(mysql_view), "Áp QTCT"

    # Giữ phòng cũ
    mysql_view.clear()
    transition.create_from_kept_department(w.db, emp, w.dept["A.kt"], w.co["A"], 1)
    assert 0 <= _employee_lock_index(mysql_view) < _first_concurrent_read(mysql_view), "giữ phòng cũ"

    # Đổi pháp nhân
    mysql_view.clear()
    transition.end_rows_at_company(w.db, emp, w.co["B"], 1)
    assert 0 <= _employee_lock_index(mysql_view) < _first_concurrent_read(mysql_view), "đổi pháp nhân"

    # Hoàn tác
    mysql_view.clear()
    transition.restore_ended(w.db, emp, [], profile)
    assert _employee_lock_index(mysql_view) >= 0, "hoàn tác"


# ══════════════════════════════════════════════════════════════════════════════
#  G2 — sơ đồ tổ chức báo "đã cắt" khi chạm trần
# ══════════════════════════════════════════════════════════════════════════════

def test_g2_so_do_bao_concurrents_truncated_khi_cham_tran(w, monkeypatch):
    from app.modules.employee import concurrent_members_service as members
    from app.modules.employee import org_chart_controller as oc

    boss = w.grant("a1", "employee", scope="all", actions=("read",))
    boss.grant("department", scope="all", actions=("read",))
    pair(w, "a2", "B.kt", "B")
    pair(w, "a3", "B.kt", "B")

    def chart():
        return json.loads(oc.get_org_chart(w.db, boss.user).body)["data"]

    monkeypatch.setattr(members, "ORG_CHART_MAX_ROWS", 2)
    full = chart()
    assert len(full["concurrents"]) == 2 and full["concurrents_truncated"] is False, "vừa trần: chưa cắt"

    monkeypatch.setattr(members, "ORG_CHART_MAX_ROWS", 1)
    cut = chart()
    assert len(cut["concurrents"]) == 1 and cut["concurrents_truncated"] is True
