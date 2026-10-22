"""duoc-CR-669 (HR2-5 / V2-6) — `GET /api/org-chart`: sơ đồ tổ chức tự vẽ từ dữ liệu.

Canh: đúng phạm vi người xem (không lộ người ngoài phạm vi, kể cả qua con trỏ
quản lý / trưởng phòng), vòng quản lý / vòng phòng cha không làm treo, không có
quyền đọc nhân sự thì 403, số truy vấn cố định, đổi quản lý là sơ đồ đổi theo.
"""
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import event

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.modules.department.model import Department
from app.modules.employee.model import Employee


def _get(db, actor):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: actor.user
    try:
        client = TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})
        return client.get("/api/org-chart")
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def _data(db, actor):
    resp = _get(db, actor)
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]


def _emp_ids(data):
    return {e["id"] for e in data["employees"]}


def test_khong_co_quyen_doc_nhan_su_thi_bi_chan(db, world):
    resp = _get(db, world.actor("a1"))
    assert resp.status_code == 403


def test_pham_vi_cong_ty_chi_thay_nguoi_cong_ty_minh(db, world):
    world.grant("a1", "employee", scope="company", inc_company=("A",))
    data = _data(db, world.actor("a1"))
    ids = _emp_ids(data)
    assert world.emp["a2"] in ids and world.emp["a3"] in ids
    assert world.emp["b1"] not in ids
    #  Pháp nhân B không có người nào xem được → không vẽ.
    assert {c["id"] for c in data["companies"]} == {world.co["A"]}
    assert all(d["company_id"] != world.co["B"] for d in data["departments"])


def test_quan_ly_ngoai_pham_vi_bi_an_khong_lo_con_tro(db, world):
    world.grant("a1", "employee", scope="company", inc_company=("A",))
    db.get(Employee, world.emp["a2"]).manager_id = world.emp["b1"]    # quản lý ở pháp nhân B
    db.get(Department, world.dept["A.kt"]).manager_id = world.emp["b1"]
    db.commit()
    data = _data(db, world.actor("a1"))
    a2 = next(e for e in data["employees"] if e["id"] == world.emp["a2"])
    assert a2["manager_id"] == 0
    dept = next(d for d in data["departments"] if d["id"] == world.dept["A.kt"])
    assert dept["manager_id"] == 0
    pointers = [e["manager_id"] for e in data["employees"]] + [d["manager_id"] for d in data["departments"]]
    assert world.emp["b1"] not in pointers


def test_quan_ly_trong_pham_vi_duoc_giu_va_doi_quan_ly_thi_so_do_doi(db, world):
    world.grant("a1", "employee", scope="all")
    db.get(Employee, world.emp["a2"]).manager_id = world.emp["a1"]
    db.commit()
    data = _data(db, world.actor("a1"))
    assert next(e for e in data["employees"] if e["id"] == world.emp["a2"])["manager_id"] == world.emp["a1"]
    db.get(Employee, world.emp["a2"]).manager_id = world.emp["a3"]
    db.commit()
    data = _data(db, world.actor("a1"))
    assert next(e for e in data["employees"] if e["id"] == world.emp["a2"])["manager_id"] == world.emp["a3"]


def test_vong_quan_ly_va_tu_quan_ly_khong_lam_treo(db, world):
    world.grant("a1", "employee", scope="all")
    db.get(Employee, world.emp["a1"]).manager_id = world.emp["a2"]
    db.get(Employee, world.emp["a2"]).manager_id = world.emp["a1"]    # vòng A1 <-> A2
    db.get(Employee, world.emp["a3"]).manager_id = world.emp["a3"]    # tự quản lý mình
    db.commit()
    data = _data(db, world.actor("a1"))
    by_id = {e["id"]: e for e in data["employees"]}
    assert by_id[world.emp["a1"]]["manager_id"] == world.emp["a2"]    # vòng để giao diện xử lý
    assert by_id[world.emp["a3"]]["manager_id"] == 0
    assert {world.emp["a1"], world.emp["a2"], world.emp["a3"]} <= set(by_id)


def test_vong_phong_cha_khong_lam_treo_va_keo_chuoi_phong_cha(db, world):
    world.grant("a1", "employee", scope="all")
    world.grant("a1", "department", scope="all")
    kt, mua = world.dept["A.kt"], world.dept["A.mua"]
    db.get(Department, kt).parent = mua
    db.get(Department, mua).parent = kt
    db.commit()
    data = _data(db, world.actor("a1"))
    ids = {d["id"] for d in data["departments"]}
    assert {kt, mua} <= ids


def test_phong_cha_ngoai_pham_vi_van_ve_duoc_cay_lien_mach(db, world):
    #  Nhân sự phạm vi `all` nhưng phòng chỉ cho pháp nhân A: phòng cha ở B vẫn được kéo vào
    #  vì chỉ lộ tên phòng; ở đây kiểm cha kéo theo khi phòng con có người xem được.
    world.grant("a1", "employee", scope="all")
    db.get(Department, world.dept["A.kt"]).parent = world.dept["B.hc"]
    db.commit()
    data = _data(db, world.actor("a1"))
    ids = {d["id"] for d in data["departments"]}
    assert world.dept["B.hc"] in ids
    child = next(d for d in data["departments"] if d["id"] == world.dept["A.kt"])
    assert child["parent"] == world.dept["B.hc"]


def test_nhan_su_nghi_viec_khong_ve(db, world):
    world.grant("a1", "employee", scope="all")
    db.get(Employee, world.emp["a2"]).status = "resigned"
    db.get(Employee, world.emp["a3"]).is_active = False
    db.commit()
    ids = _emp_ids(_data(db, world.actor("a1")))
    assert world.emp["a2"] not in ids and world.emp["a3"] not in ids and world.emp["a1"] in ids


def test_khong_lo_cot_nhay_cam(db, world):
    world.grant("a1", "employee", scope="all")
    data = _data(db, world.actor("a1"))
    assert set(data["employees"][0]) == {
        "id", "code", "full_name", "position", "company_id", "department_id", "manager_id"}


def test_so_truy_van_khong_tang_theo_so_nhan_su(db, world):
    world.grant("a1", "employee", scope="all")
    actor = world.actor("a1")
    actor.profile()

    def _add(n, start):
        for i in range(n):
            db.add(Employee(code=f"ORG{start + i}", full_name=f"NV {start + i}",
                            company_id=world.co["A"], department_id=world.dept["A.kt"],
                            manager_id=world.emp["a1"]))
        db.commit()

    def _count(fn):
        statements = []

        def _on(conn, cursor, statement, *a):
            statements.append(statement)

        engine = db.get_bind()
        event.listen(engine, "before_cursor_execute", _on)
        try:
            fn()
        finally:
            event.remove(engine, "before_cursor_execute", _on)
        return len(statements)

    _data(db, actor)  # làm nóng cache hồ sơ quyền
    _add(5, 0)
    c5 = _count(lambda: _data(db, actor))
    _add(45, 5)
    c50 = _count(lambda: _data(db, actor))
    assert c5 > 0 and c5 == c50, f"{c5} != {c50}"
