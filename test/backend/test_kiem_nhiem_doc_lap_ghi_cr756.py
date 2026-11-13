"""duoc-CR-756 giai đoạn 01 — KIÊM NHIỆM hai loại dòng ĐỘC LẬP (Phòng ban / Công ty): migration `kn756a`, luồng ghi,
đổi pháp nhân + giữ kiêm nhiệm ở công ty cũ, Áp quá trình công tác đổi loại tại chỗ, hoàn tác lô Excel, L2 theo loại.

Phần CRUD cơ bản của tab (tám ca hình sai theo loại ở schema, L3, chồng giai đoạn theo loại, L2 các bậc, PATCH ô loại
kia) nằm ở `test_kiem_nhiem_khac_cong_ty_du_lieu_cr755.py`; ở đây là phần RIÊNG của CR-756.
"""
import importlib.util
import json
from datetime import timedelta
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from app.core.hr_work_history_codes import WorkEventType
from app.core.vn_time import vn_today
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.company.model import Company
from app.modules.employee import concurrent_company_change_service as company_change
from app.modules.employee import concurrent_controller as cc
from app.modules.employee import work_history_apply_service as applysvc
from app.modules.employee.concurrent_model import EmployeeConcurrent
from app.modules.employee.concurrent_schema import ConcurrentIn, ConcurrentPatch
from app.modules.employee.model import Employee
from app.modules.employee.schema import EmployeeUpdate
from app.modules.employee.service import update_employee
from app.modules.employee.work_history_model import EmployeeWorkHistory

from test_kiem_nhiem_luong_ghi_cr755 import ROW, xl  # noqa: F401  — fixture + dòng nhập Excel dùng chung
from test_nhap_excel_nhan_su_cr628 import emp, errors, hr, run_import  # noqa: F401

TODAY = vn_today()
YESTERDAY = TODAY - timedelta(days=1)
ACTOR = 1


# ══════════════════════════════════════════════════════════════════════════════
#  Migration kn756a (engine SQLite riêng, khuôn test_kiem_nhiem_migration_cr755)
# ══════════════════════════════════════════════════════════════════════════════

_MIG = "kn756a_kiem_nhiem_loai_phong_cong_ty.py"
_DDL = [
    "CREATE TABLE tab_employee (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id BIGINT, department_id BIGINT)",
    """CREATE TABLE tab_employee_concurrent (
        id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id BIGINT NOT NULL, company_id BIGINT NOT NULL,
        department_id BIGINT NOT NULL, from_date DATE, to_date DATE)""",
]


def _nap():
    path = Path(__file__).resolve().parents[2] / "backend" / "migrations" / "versions" / _MIG
    if not path.exists():   # trong container: /app/test/backend + /app/migrations
        path = Path("/app/migrations/versions") / _MIG
    spec = importlib.util.spec_from_file_location("mig_kn756a", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mig():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    with engine.begin() as c:
        for stmt in _DDL:
            c.execute(text(stmt))
    conn = engine.connect()
    ctx = MigrationContext.configure(conn)
    module = _nap()

    class Env:
        def up(self):
            with Operations.context(ctx):
                module.upgrade()
            conn.commit()

        def down(self):
            with Operations.context(ctx):
                module.downgrade()
            conn.commit()

        def sql(self, stmt, **p):
            conn.execute(text(stmt), p)
            conn.commit()

        def rows(self, stmt):
            return [tuple(r) for r in conn.execute(text(stmt)).fetchall()]

        insp = staticmethod(lambda: inspect(conn))
        module_ = module

    yield Env()
    conn.close()


def _seed_mig(env):
    env.sql("INSERT INTO tab_employee (id, company_id, department_id) VALUES (1, 10, 100), (2, 20, 200), (3, 0, 0)")
    ins = ("INSERT INTO tab_employee_concurrent (employee_id, company_id, department_id, from_date, to_date) "
           "VALUES (:e, :c, :d, :f, :t)")
    env.sql(ins, e=1, c=10, d=101, f=None, t=None)                     # cùng công ty chính -> loại 1
    env.sql(ins, e=1, c=99, d=555, f=None, t=None)                     # khác công ty -> loại 2, mất phòng
    env.sql(ins, e=2, c=0, d=201, f=None, t=None)                      # công ty 0 -> chuẩn hóa về công ty chính (20)
    env.sql(ins, e=3, c=0, d=300, f=None, t=None)                      # hồ sơ chưa có pháp nhân -> giữ 0, loại 1


def test_migration_len_chia_loai_va_chuan_hoa_cong_ty(mig):
    _seed_mig(mig)
    mig.up()
    assert mig.rows("SELECT employee_id, kind, company_id, department_id FROM tab_employee_concurrent "
                    "ORDER BY id") == [(1, 1, 10, 101), (1, 2, 99, 0), (2, 1, 20, 201), (3, 1, 0, 300)]
    assert "ix_employee_concurrent_company_kind" in {i["name"] for i in mig.insp().get_indexes("tab_employee_concurrent")}
    assert "kind" in {c["name"] for c in mig.insp().get_columns("tab_employee_concurrent")}


def test_migration_chay_lai_khong_doi_va_khong_nhan_doi(mig):
    _seed_mig(mig)
    mig.up()
    before = mig.rows("SELECT * FROM tab_employee_concurrent ORDER BY id")
    mig.up()
    assert mig.rows("SELECT * FROM tab_employee_concurrent ORDER BY id") == before


def test_migration_in_so_cap_loai_cong_ty_chong_giai_doan(mig, capsys):
    mig.sql("INSERT INTO tab_employee (id, company_id, department_id) VALUES (1, 10, 100)")
    ins = ("INSERT INTO tab_employee_concurrent (employee_id, company_id, department_id, from_date, to_date) "
           "VALUES (1, 99, :d, :f, :t)")
    mig.sql(ins, d=1, f="2026-01-01", t="2026-06-30")
    mig.sql(ins, d=2, f="2026-06-30", t=None)                           # chồng dòng trên ở đúng ngày 30/6
    mig.sql(ins, d=3, f="2026-07-01", t=None)                           # dòng 3 chồng dòng 2 (đều mở), không chồng dòng 1
    mig.up()
    out = capsys.readouterr().out
    assert "bỏ phòng): 3" in out
    assert "chồng giai đoạn (để nguyên): 2" in out


def test_migration_down_bo_cot_va_chi_muc_giu_dong_loai_cong_ty_voi_phong_0(mig):
    _seed_mig(mig)
    mig.up()
    mig.down()
    assert "kind" not in {c["name"] for c in mig.insp().get_columns("tab_employee_concurrent")}
    assert "ix_employee_concurrent_company_kind" not in {
        i["name"] for i in mig.insp().get_indexes("tab_employee_concurrent")}
    #  Dòng loại Công ty ở lại với phòng 0 — hồ sơ quyền của CR-755 bỏ qua phòng 0 nên hạ không mở thêm quyền.
    assert (1, 99, 0) in {tuple(r) for r in mig.rows("SELECT employee_id, company_id, department_id "
                                                     "FROM tab_employee_concurrent")}
    mig.up()     # lên lại được
    assert mig.rows("SELECT kind FROM tab_employee_concurrent WHERE company_id = 99") == [(2,)]


def test_migration_noi_tiep_kn755a():
    module = _nap()
    assert (module.revision, module.down_revision) == ("kn756a", "kn755a")


# ══════════════════════════════════════════════════════════════════════════════
#  Dựng dữ liệu cho luồng ghi
# ══════════════════════════════════════════════════════════════════════════════

def _row(db, eid, kind, company, dept=0, **kw) -> EmployeeConcurrent:
    kw.setdefault("from_date", TODAY - timedelta(days=10))
    row = EmployeeConcurrent(employee_id=eid, kind=kind, company_id=company, department_id=dept,
                             counts_scope=True, created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _rows(db, eid) -> list[EmployeeConcurrent]:
    db.expire_all()
    return db.query(EmployeeConcurrent).filter(EmployeeConcurrent.employee_id == eid).order_by(
        EmployeeConcurrent.id).all()


def _company_c(db) -> int:
    row = Company(code="CTY_C", name="Công ty C", is_active=True)
    db.add(row)
    db.commit()
    return row.id


def _wh(db, eid, **kw) -> EmployeeWorkHistory:
    row = EmployeeWorkHistory(employee_id=eid, event_type=int(WorkEventType.CONCURRENT),
                              from_date=kw.pop("from_date", TODAY - timedelta(days=5)),
                              created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# ══════════════════════════════════════════════════════════════════════════════
#  L1 / PATCH / L2 theo loại
# ══════════════════════════════════════════════════════════════════════════════

def test_l1_patch_khong_nhan_kind_va_ke_ca_quan_tri_khong_tu_sua_dong_loai_cong_ty(world):
    boss = world.grant("a1", "employee", scope="all", actions=("read", "write"))
    own = _row(world.db, world.emp["a1"], 2, world.co["B"])
    for call in (
        lambda: cc.update_concurrent(world.emp["a1"], own.id, ConcurrentPatch(note="x"), world.db, boss.user),
        lambda: cc.delete_concurrent(world.emp["a1"], own.id, world.db, boss.user),
        lambda: cc.create_concurrent(world.emp["a1"], ConcurrentIn(kind=2, company_id=world.co["B"], from_date=TODAY),
                                     world.db, boss.user),
    ):
        with pytest.raises(HTTPException) as err:
            call()
        assert err.value.status_code == 403
    with pytest.raises(Exception):
        ConcurrentPatch.model_validate({"kind": 1})


def test_l2_sua_dong_loai_cong_ty_do_ca_cu_lan_moi(world):
    """Dời dòng Công ty B sang C: người bậc `company` (A) có B kiêm nhiệm nhưng KHÔNG có C -> chặn ở vế mới; không có B
    -> chặn ngay ở vế cũ."""
    from app.modules.employee import concurrent_service
    c_id = _company_c(world.db)
    emp_row = world.db.get(Employee, world.emp["a2"])
    row = _row(world.db, emp_row.id, 2, world.co["B"])
    grant = {"perms": {"employee": {"write": True, "scope": "company"}}, "scope": {}}
    actor = type("A", (), {"id": 1, "employee_id": 0})()
    with_b = {"grants": [grant], "company_id": world.co["A"], "concurrent_companies": [world.co["B"]]}
    with pytest.raises(HTTPException) as err:
        concurrent_service.update_concurrent(world.db, emp_row, row.id, ConcurrentPatch(company_id=c_id), actor, with_b)
    assert err.value.status_code == 403 and "Công ty C" in err.value.detail
    only_a = {"grants": [grant], "company_id": world.co["A"]}
    with pytest.raises(HTTPException) as err2:
        concurrent_service.update_concurrent(world.db, emp_row, row.id, ConcurrentPatch(note="x"), actor, only_a)
    assert err2.value.status_code == 403 and "Công ty B" in err2.value.detail
    #  Đối chứng: có cả B và C kiêm nhiệm thì dời được.
    both = {**with_b, "concurrent_companies": [world.co["B"], c_id]}
    concurrent_service.update_concurrent(world.db, emp_row, row.id, ConcurrentPatch(company_id=c_id), actor, both)
    assert world.db.get(EmployeeConcurrent, row.id).company_id == c_id


# ══════════════════════════════════════════════════════════════════════════════
#  Đổi pháp nhân A -> C, giữ kiêm nhiệm ở công ty cũ
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def move(world):
    """a3 (A, A.mua): dòng Phòng ban A.kt (A), dòng Công ty C và dòng Công ty D (khác, không bị đụng)."""
    db = world.db
    c_id = _company_c(db)
    d_co = Company(code="CTY_D", name="Công ty D", is_active=True)
    db.add(d_co)
    db.commit()
    eid = world.emp["a3"]
    return {"w": world, "eid": eid, "c": c_id, "d": d_co.id,
            "dept_a": _row(db, eid, 1, world.co["A"], world.dept["A.kt"]),
            "seat_c": _row(db, eid, 2, c_id), "seat_d": _row(db, eid, 2, d_co.id)}


def _boss(world, scope="all"):
    return world.grant("a1", "employee", scope=scope, actions=("read", "write"))


def test_doi_phap_nhan_giu_ghe_mot_dong_loai_cong_ty_a_va_ket_thuc_phong_a_va_cong_ty_c(move):
    w = move["w"]
    boss = _boss(w)
    update_employee(w.db, move["eid"], EmployeeUpdate(company_id=move["c"], department_id=0,
                                                      keep_old_company_concurrent=True), boss.user.id,
                    profile=boss.profile())
    rows = {r.id: r for r in _rows(w.db, move["eid"])}
    assert rows[move["dept_a"].id].to_date == YESTERDAY, "loại 1 ở A kết thúc"
    assert rows[move["seat_c"].id].to_date == YESTERDAY, "loại 2 trùng C kết thúc"
    assert rows[move["seat_d"].id].to_date is None, "loại 2 (D khác) không đụng"
    seats = [r for r in rows.values() if r.note == "Giữ kiêm nhiệm khi đổi pháp nhân"]
    assert [(r.kind, r.company_id, r.department_id, r.from_date, r.to_date) for r in seats] == [
        (2, w.co["A"], 0, TODAY, None)]


def test_giu_ghe_thieu_l2_403_va_khong_doi_gi(move):
    w = move["w"]
    dept_only = _boss(w, "dept")           # bậc phòng ban: không có quyền ghi toàn công ty A
    with pytest.raises(HTTPException) as err:
        update_employee(w.db, move["eid"], EmployeeUpdate(company_id=move["c"], department_id=0,
                                                          keep_old_company_concurrent=True), dept_only.user.id,
                        profile=dept_only.profile())
    assert err.value.status_code == 403 and "toàn công ty" in err.value.detail
    w.db.expire_all()
    assert w.db.get(Employee, move["eid"]).company_id == w.co["A"], "không đổi pháp nhân"
    assert all(r.to_date is None for r in _rows(w.db, move["eid"])), "không kết thúc dòng nào"


def test_giu_ghe_khong_co_profile_thi_bo_qua_duong_noi_bo(move):
    w = move["w"]
    update_employee(w.db, move["eid"], EmployeeUpdate(company_id=move["c"], department_id=0,
                                                      keep_old_company_concurrent=True), ACTOR)
    assert [r for r in _rows(w.db, move["eid"]) if r.note == "Giữ kiêm nhiệm khi đổi pháp nhân"] == []


def test_giu_ghe_khong_nhan_doi_khi_da_co_dong_loai_cong_ty_a_hieu_luc(move):
    w = move["w"]
    boss = _boss(w)
    _row(w.db, move["eid"], 2, w.co["A"])             # trạng thái lệch cũ: đã có sẵn dòng Công ty A đang mở
    update_employee(w.db, move["eid"], EmployeeUpdate(company_id=move["c"], department_id=0,
                                                      keep_old_company_concurrent=True), boss.user.id,
                    profile=boss.profile())
    assert len([r for r in _rows(w.db, move["eid"]) if r.kind == 2 and r.company_id == w.co["A"]]) == 1


def test_l1_khong_tu_giu_ghe_cho_chinh_minh(move):
    w = move["w"]
    me = w.grant("a3", "employee", scope="all", actions=("read", "write"))
    with pytest.raises(HTTPException) as err:
        update_employee(w.db, move["eid"], EmployeeUpdate(company_id=move["c"], department_id=0,
                                                          keep_old_company_concurrent=True), me.user.id,
                        profile=me.profile())
    assert err.value.status_code == 403


def test_nhap_excel_dong_loai_cong_ty_dich_chua_bat_dau_la_loi_dong(db, seed, hr, xl):
    future = _row(db, xl["eid"], 2, xl["co2"], from_date=TODAY + timedelta(days=3))
    b = run_import(db, [ROW], hr)
    assert b.error_count == 1 and b.updated_count == 0
    assert "chưa bắt đầu" in errors(db, b.id)[0].message
    assert db.get(EmployeeConcurrent, future.id) is not None
    assert emp(db, "DEMONV").company_id == xl["co1"], "dòng lỗi thì hồ sơ không đổi"


def test_hoan_tac_lo_khoi_phuc_to_date_dong_loai_cong_ty_dich(db, seed, hr, xl):
    seat = _row(db, xl["eid"], 2, xl["co2"])
    dept = _row(db, xl["eid"], 1, xl["co1"], xl["d3"])
    b = run_import(db, [ROW], hr)
    assert b.error_count == 0
    db.expire_all()
    assert db.get(EmployeeConcurrent, seat.id).to_date == YESTERDAY
    assert db.get(EmployeeConcurrent, dept.id).to_date == YESTERDAY

    from app.modules.import_tool import service
    res = service.revert_batch(db, b, hr)
    assert res["ok"], res
    db.expire_all()
    assert db.get(EmployeeConcurrent, seat.id).to_date is None
    assert db.get(EmployeeConcurrent, dept.id).to_date is None


def test_hoan_tac_chong_giai_doan_theo_loai_tu_choi_neu_da_co_dong_cung_cong_ty_moi(db, seed, hr, xl):
    seat = _row(db, xl["eid"], 2, xl["co2"])
    b = run_import(db, [ROW], hr)
    assert b.error_count == 0
    #  Sau lô, ai đó thêm dòng Công ty CT02 đang mở -> khôi phục `to_date` trống của dòng cũ sẽ chồng nó.
    _row(db, xl["eid"], 2, xl["co2"], from_date=TODAY)
    entries = [[seat.id, None, YESTERDAY.isoformat()]]
    profile = {"grants": [{"perms": {"employee": {"write": True, "scope": "all"}}, "scope": {}}]}
    problems = company_change.revert_problems(db, db.get(Employee, xl["eid"]), entries, profile)
    assert problems and "cùng công ty" in " ".join(problems)


# ══════════════════════════════════════════════════════════════════════════════
#  Áp quá trình công tác: loại theo công ty, đổi loại tại chỗ
# ══════════════════════════════════════════════════════════════════════════════

def test_ap_qtct_cung_cong_ty_chinh_la_loai_phong_ban_khac_cong_ty_la_loai_cong_ty(world):
    db = world.db
    a1 = _boss(world)
    eid = world.emp["a3"]
    same = _wh(db, eid, department_id=world.dept["A.kt"])                         # công ty trống = công ty chính
    other = _wh(db, eid, department_id=world.dept["B.kt"], company_id=world.co["B"])
    msg1 = applysvc.apply(db, same, a1.user, a1.profile())
    msg2 = applysvc.apply(db, other, a1.user, a1.profile())
    db.commit()
    assert msg1 == ['Kiêm nhiệm — thêm phòng "Phòng Kế toán"']
    assert msg2 == ['Kiêm nhiệm — thêm công ty "Công ty B"']
    by_wh = {r.work_history_id: r for r in _rows(db, eid)}
    assert (by_wh[same.id].kind, by_wh[same.id].company_id, by_wh[same.id].department_id) == (1, world.co["A"],
                                                                                              world.dept["A.kt"])
    assert (by_wh[other.id].kind, by_wh[other.id].company_id, by_wh[other.id].department_id) == (2, world.co["B"], 0)


def test_ap_qtct_trung_phong_chinh_hoac_khong_phong_o_cong_ty_chinh_thi_bo_qua(world):
    db = world.db
    a1 = _boss(world)
    eid = world.emp["a3"]                                                          # phòng chính A.mua
    assert applysvc.apply(db, _wh(db, eid, department_id=world.dept["A.mua"]), a1.user, a1.profile()) == []
    assert applysvc.apply(db, _wh(db, eid, department_id=0), a1.user, a1.profile()) == []
    assert _rows(db, eid) == []


def test_ap_lai_sau_khi_qtct_doi_cong_ty_thi_doi_loai_tai_cho_giu_id_va_tep(world):
    db = world.db
    a1 = _boss(world)
    eid = world.emp["a3"]
    wh = _wh(db, eid, department_id=world.dept["A.kt"])
    stored = StoredFile(filename="qd.pdf", file_key="k/qd.pdf")
    db.add(stored)
    db.flush()
    db.add(FileLink(file_id=stored.id, entity="employee_work_history", entity_id=wh.id, doc_type="decision"))
    db.commit()
    applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    (first,) = _rows(db, eid)
    assert first.kind == 1

    wh.company_id = world.co["B"]                                                  # QTCT đổi sang công ty khác
    db.commit()
    assert applysvc.apply(db, wh, a1.user, a1.profile())
    db.commit()
    (again,) = _rows(db, eid)
    assert again.id == first.id and (again.kind, again.company_id, again.department_id) == (2, world.co["B"], 0)
    assert db.query(FileLink).filter(FileLink.entity == "employee_concurrent",
                                     FileLink.entity_id == again.id).count() == 1, "tệp quyết định giữ nguyên"


def test_ap_qtct_khac_cong_ty_l2_bac_cong_ty_chi_qua_khi_co_cong_ty_kiem_nhiem(world):
    db = world.db
    eid = world.emp["a3"]
    wh = _wh(db, eid, company_id=world.co["B"])
    company_grant = world.grant("a1", "employee", scope="company", actions=("read", "write"))
    with pytest.raises(HTTPException) as err:
        applysvc.apply(db, wh, company_grant.user, company_grant.profile())
    assert err.value.status_code == 403
    assert _rows(db, eid) == []
    db.rollback()
    #  Có công ty B trong tầm (dòng Công ty B của chính người áp) thì qua.
    _row(db, world.emp["a1"], 2, world.co["B"])
    profile = dict(company_grant.profile(), concurrent_companies=[world.co["B"]])
    assert applysvc.apply(db, wh, company_grant.user, profile)
    db.commit()
    assert [(r.kind, r.company_id) for r in _rows(db, eid)] == [(2, world.co["B"])]


def test_ap_qtct_ho_so_chua_gan_phap_nhan_chinh_la_400(world):
    db = world.db
    a1 = _boss(world)
    eid = world.emp["a3"]
    db.get(Employee, eid).company_id = 0
    db.commit()
    wh = _wh(db, eid, company_id=world.co["B"])
    with pytest.raises(HTTPException) as err:
        applysvc.apply(db, wh, a1.user, a1.profile())
    assert err.value.status_code == 400 and "chưa gắn pháp nhân chính" in err.value.detail


def test_ap_qtct_tra_dung_json_cho_api(world):
    """Bao đảm `kind` đi ra qua `serialize_one` để giao diện dựng nhãn loại."""
    a1 = _boss(world)
    wh = _wh(world.db, world.emp["a3"], company_id=world.co["B"])
    applysvc.apply(world.db, wh, a1.user, a1.profile())
    world.db.commit()
    data = json.loads(cc.list_concurrents(world.emp["a3"], world.db, a1.user).body)["data"]
    assert [(i["kind"], i["kind_label"], i["department_id"], i["department_name"], i["company_name"])
            for i in data["items"]] == [(2, "Công ty", 0, "", "Công ty B")]
