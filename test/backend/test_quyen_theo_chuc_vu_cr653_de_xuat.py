"""duoc-CR-653 — script đề xuất gói quyền: ngưỡng 60%, bỏ admin, dry-run KHÔNG ghi, --apply --yes chỉ thêm gói."""
import pytest

from app.modules.employee import service as emp_service
from app.modules.employee.position_model import JobPosition, JobPositionRole
from app.modules.employee.schema import EmployeeUpdate
from app.modules.role.model import Role
from app.modules.user.model import User, UserRole
from scripts import de_xuat_quyen_theo_chuc_vu as script


def mk_role(db, code):
    r = Role(code=code, name=f"Vai trò {code}")
    db.add(r)
    db.flush()
    return r


class _Keep:
    """Bọc phiên test: `main()` gọi `close()` ở cuối, mà bài kiểm còn đọc lại đối tượng."""

    def __init__(self, db):
        self._db = db

    def __getattr__(self, name):
        return getattr(self._db, name)

    def close(self):
        pass


@pytest.fixture
def world3(db, seed):
    """Chức vụ P có 3 người (req, tp, nstm). ZA: 3/3, ZB: 2/3 (67%), ZC: 1/3 (33%), admin: 3/3."""
    pos = JobPosition(code="cv-p", name="P", is_active=True)
    db.add(pos)
    db.flush()
    admin = mk_role(db, "admin")
    za, zb, zc = mk_role(db, "ZA"), mk_role(db, "ZB"), mk_role(db, "ZC")
    users = [db.query(User).filter(User.employee_id == e).one()
             for e in (seed.emp_req_id, seed.emp_tp_id, seed.emp_nstm_id)]
    for i, u in enumerate(users):
        for r in (admin, za) + ((zb,) if i < 2 else ()) + ((zc,) if i == 0 else ()):
            db.add(UserRole(user_id=u.id, role_id=r.id))
    db.commit()
    for e in (seed.emp_req_id, seed.emp_tp_id, seed.emp_nstm_id):
        emp_service.update_employee(db, e, EmployeeUpdate(position_id=pos.id), 1)
    return pos, za, zb, zc, admin


def test_nguong_va_bo_admin(db, world3):
    pos, za, zb, zc, admin = world3
    p = next(x for x in script.compute_proposal(db) if x["position_id"] == pos.id)
    by = {r["code"]: r for r in p["roles"]}
    assert p["holders"] == 3 and "admin" not in by
    assert by["ZA"]["proposed"] and by["ZB"]["proposed"] and not by["ZC"]["proposed"]
    assert by["ZB"]["count"] == 2 and round(by["ZB"]["pct"], 2) == 0.67
    p2 = next(x for x in script.compute_proposal(db, threshold=0.9) if x["position_id"] == pos.id)
    assert {r["code"] for r in p2["roles"] if r["proposed"]} == {"ZA"}


def test_dry_run_khong_ghi_gi(db, world3, monkeypatch, capsys, tmp_path):
    from app.core import database
    monkeypatch.setattr(database, "SessionLocal", lambda: _Keep(db))
    before = (db.query(JobPositionRole).count(), db.query(UserRole).count())
    out = tmp_path / "dx.md"
    assert script.main(["--out", str(out)]) == 0
    assert (db.query(JobPositionRole).count(), db.query(UserRole).count()) == before == (0, before[1])
    assert "Đề xuất quyền mặc định" in out.read_text(encoding="utf-8")


def test_apply_can_yes(db, world3, monkeypatch):
    from app.core import database
    monkeypatch.setattr(database, "SessionLocal", lambda: _Keep(db))
    with pytest.raises(SystemExit):
        script.main(["--apply"])
    assert db.query(JobPositionRole).count() == 0


def test_apply_yes_chi_them_goi_khong_cap_cho_ai(db, world3, monkeypatch):
    pos, za, zb, zc, admin = world3
    from app.core import database
    monkeypatch.setattr(database, "SessionLocal", lambda: _Keep(db))
    roles_before = db.query(UserRole).count()
    assert script.main(["--apply", "--yes"]) == 0
    assert {r.role_id for r in db.query(JobPositionRole).filter(JobPositionRole.job_position_id == pos.id)} == {za.id, zb.id}
    assert db.query(UserRole).count() == roles_before          # không cấp gì cho tài khoản
    assert script.main(["--apply", "--yes"]) == 0               # chạy lại: không nhân đôi
    assert db.query(JobPositionRole).count() == 2


def test_csv_va_nguong_sai(db, world3):
    text = script.render_csv(script.compute_proposal(db))
    assert text.splitlines()[0].startswith("position_id,position_name")
    with pytest.raises(SystemExit):
        script.main(["--threshold", "0"])
