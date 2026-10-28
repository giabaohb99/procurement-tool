"""duoc-CR-689 (phase 17) — bảng kế hoạch nhân sự `/api/headcount-plans` (entity `headcount_plan`).

Canh: CRUD đủ đường + nhật ký, kiểm đầu vào 422 (năm 2000–2100, số âm, `note` > 500, pháp nhân / phòng không
có hoặc phòng thuộc pháp nhân khác), duy nhất (năm, pháp nhân, phòng) ở cả tạo lẫn sửa, CHE số lương khi thiếu
`labor_contract.read` (danh sách / chi tiết / xuất CSV; ghi lương → 403), phạm vi dữ liệu (dòng «toàn pháp nhân»
ẩn với người chỉ có phạm vi phòng), xuất / nhập CSV (upsert, nguyên khối, báo lỗi theo dòng).
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.modules.headcount_plan.model import HeadcountPlan
from app.modules.headcount_plan.schema import HeadcountPlanCreate, HeadcountPlanUpdate
from app.modules.audit.model import AuditLog

URL = "/api/headcount-plans"
ALL = ("read", "create", "write", "delete", "export")


@pytest.fixture
def client_as(db):
    def make(user):
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        return TestClient(app, headers={"Authorization": f"Bearer test-{uuid.uuid4().hex}"})

    yield make
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _hr(world, client_as, *, pay=True, scope="all", key="a1", **grant_kw):
    """Người dùng có quyền kế hoạch (+ xem hợp đồng nếu `pay`)."""
    world.grant(key, "headcount_plan", scope, actions=ALL, **grant_kw)
    if pay:
        world.grant(key, "labor_contract", "all", actions=("read",))
    return client_as(world.actor(key).user)


def _body(world, **kw):
    return {"year": 2026, "company_id": world.co["A"], "department_id": world.dept["A.kt"],
            "planned_headcount": 20, "planned_payroll_monthly": 300_000_000, "note": "Được duyệt", **kw}


def _add(db, world, dept="A.kt", co="A", year=2026, n=10, pay=1_000_000):
    row = HeadcountPlan(year=year, company_id=world.co[co], department_id=world.dept[dept] if dept else 0,
                        planned_headcount=n, planned_payroll_monthly=pay, note="")
    db.add(row)
    db.commit()
    return row


def test_crud_day_du_va_ghi_nhat_ky(db, world, client_as):
    client = _hr(world, client_as)
    resp = client.post(URL, json=_body(world))
    assert resp.status_code == 201, resp.text
    row = resp.json()["data"]
    assert row["company_name"] == "Công ty A" and row["department_name"] == "Phòng Kế toán"
    assert row["planned_headcount"] == 20 and row["planned_payroll_monthly"] == 300_000_000
    pid = row["id"]
    assert client.get(f"{URL}/{pid}").json()["data"]["note"] == "Được duyệt"
    resp = client.patch(f"{URL}/{pid}", json={"planned_headcount": 25})
    assert resp.status_code == 200 and resp.json()["data"]["planned_headcount"] == 25
    assert resp.json()["data"]["planned_payroll_monthly"] == 300_000_000      # không đụng tới lương khi không gửi
    listing = client.get(URL, params={"year": 2026, "company_id": world.co["A"]}).json()["data"]
    assert listing["total"] == 1 and listing["items"][0]["id"] == pid
    assert client.get(URL, params={"year": 2027}).json()["data"]["total"] == 0
    assert client.delete(f"{URL}/{pid}").status_code == 200
    assert client.get(f"{URL}/{pid}").status_code == 404
    actions = [a.action for a in db.query(AuditLog).filter(AuditLog.entity == "headcount_plan").all()]
    assert sorted(actions) == ["create", "delete", "update"]


def test_dong_toan_phap_nhan_department_id_0(db, world, client_as):
    client = _hr(world, client_as)
    resp = client.post(URL, json=_body(world, department_id=0))
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["department_name"] == "Toàn pháp nhân"


@pytest.mark.parametrize("patch", [
    {"year": 1999}, {"year": 2101}, {"planned_headcount": -1}, {"planned_payroll_monthly": -5},
    {"note": "x" * 501}, {"company_id": 0}, {"department_id": -1}, {"bogus": 1},
])
def test_kiem_dau_vao_422(db, world, client_as, patch):
    client = _hr(world, client_as)
    resp = client.post(URL, json=_body(world, **patch))
    assert resp.status_code == 422, (patch, resp.text)


def test_schema_chan_chuoi_dai_va_so_am():
    with pytest.raises(ValidationError):
        HeadcountPlanCreate(year=2026, company_id=1, note="x" * 501)
    with pytest.raises(ValidationError):
        HeadcountPlanUpdate(planned_headcount=-1)
    assert HeadcountPlanCreate(year=2000, company_id=1).department_id == 0
    assert HeadcountPlanCreate(year=2100, company_id=1, note="x" * 500).note == "x" * 500


def test_phap_nhan_phong_khong_hop_le_422(db, world, client_as):
    client = _hr(world, client_as)
    assert client.post(URL, json=_body(world, company_id=999_999)).status_code == 422
    assert client.post(URL, json=_body(world, department_id=999_999)).status_code == 422
    #  Phòng ban dùng chung cho mọi pháp nhân (dev/local: `tab_department_company` rỗng,
    #  `Department.company_id` = 0) — kế hoạch «pháp nhân A × phòng B.kt» là HỢP LỆ (28/10/2026:
    #  bản đầu từ chối nên không lưu được kế hoạch theo phòng nào).
    assert client.post(URL, json=_body(world, department_id=world.dept["B.kt"])).status_code == 201


def test_trung_nam_phap_nhan_phong_la_400_ca_khi_tao_lan_sua(db, world, client_as):
    client = _hr(world, client_as)
    assert client.post(URL, json=_body(world)).status_code == 201
    assert client.post(URL, json=_body(world)).status_code == 400
    other = client.post(URL, json=_body(world, year=2027)).json()["data"]["id"]
    resp = client.patch(f"{URL}/{other}", json={"year": 2026})
    assert resp.status_code == 400
    assert client.patch(f"{URL}/{other}", json={"year": 2028}).status_code == 200


def test_che_luong_khi_thieu_labor_contract_read(db, world, client_as):
    row = _add(db, world, pay=777_000_000)
    client = _hr(world, client_as, pay=False)
    item = client.get(URL).json()["data"]["items"][0]
    assert item["planned_payroll_monthly"] is None and item["planned_headcount"] == 10
    assert client.get(f"{URL}/{row.id}").json()["data"]["planned_payroll_monthly"] is None
    csv_text = client.get(f"{URL}/export/csv").content.decode("utf-8-sig")
    assert "777000000" not in csv_text and "A_KT" in csv_text
    # ghi lương khi không được xem lương -> 403; không gửi lương thì ghi bình thường
    assert client.post(URL, json=_body(world, year=2030)).status_code == 403
    body = _body(world, year=2030)
    body.pop("planned_payroll_monthly")
    assert client.post(URL, json=body).status_code == 201
    assert client.patch(f"{URL}/{row.id}", json={"planned_payroll_monthly": 1}).status_code == 403
    assert client.patch(f"{URL}/{row.id}", json={"planned_headcount": 11}).status_code == 200
    # biểu mẫu gửi ô lương trống = 0 (E2E CR-689 N1): lưu được, và KHÔNG đè quỹ lương thật đang bị che
    assert client.patch(f"{URL}/{row.id}", json={"planned_headcount": 12, "planned_payroll_monthly": 0}).status_code == 200
    assert client.post(URL, json={**body, "year": 2031, "planned_payroll_monthly": 0}).status_code == 201
    db.refresh(row)
    assert row.planned_payroll_monthly == 777_000_000 and row.planned_headcount == 12   # không bị đè về 0


def test_thieu_quyen_hanh_dong_403(db, world, client_as):
    world.grant("a1", "headcount_plan", "all", actions=("read",))
    client = client_as(world.actor("a1").user)
    assert client.get(URL).status_code == 200
    assert client.post(URL, json=_body(world)).status_code == 403
    assert client.get(f"{URL}/export/csv").status_code == 403
    assert client.delete(f"{URL}/1").status_code == 403


def test_pham_vi_phong_khong_thay_dong_toan_phap_nhan_va_phong_khac(db, world, client_as):
    mine = _add(db, world, dept="A.kt")
    other = _add(db, world, dept="A.mua")
    whole = _add(db, world, dept=None)
    client = _hr(world, client_as, scope="dept", inc_dept=("A.kt",))
    ids = {i["id"] for i in client.get(URL).json()["data"]["items"]}
    assert ids == {mine.id}
    assert client.get(f"{URL}/{other.id}").status_code == 404
    assert client.get(f"{URL}/{whole.id}").status_code == 404
    assert client.patch(f"{URL}/{other.id}", json={"note": "x"}).status_code == 404
    assert client.delete(f"{URL}/{other.id}").status_code == 404
    # tạo dòng ngoài phạm vi -> 403 và không để lại gì
    assert client.post(URL, json=_body(world, year=2031, department_id=world.dept["A.mua"])).status_code == 403
    assert db.query(HeadcountPlan).filter(HeadcountPlan.year == 2031).count() == 0


def test_csv_xuat_nhap_vong_tron(db, world, client_as):
    _add(db, world, dept="A.kt", n=5, pay=50_000_000)
    _add(db, world, dept=None, n=40, pay=900_000_000)
    client = _hr(world, client_as)
    text = client.get(f"{URL}/export/csv", params={"year": 2026}).content.decode("utf-8-sig")
    lines = text.strip().splitlines()
    assert lines[0] == "year,company_code,department_code,planned_headcount,planned_payroll_monthly,note"
    assert "2026,CTY_A,A_KT,5,50000000," in lines and "2026,CTY_A,,40,900000000," in lines
    new = ("year,company_code,department_code,planned_headcount,planned_payroll_monthly,note\n"
           "2026,CTY_A,A_KT,8,60000000,Tăng\n"          # cập nhật
           "2026,CTY_B,B_HC,3,,Mới\n")                    # thêm, bỏ trống lương
    resp = client.post(f"{URL}/import/csv", files={"file": ("k.csv", new.encode("utf-8-sig"), "text/csv")})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == {"created": 1, "updated": 1}
    kt = db.query(HeadcountPlan).filter(HeadcountPlan.department_id == world.dept["A.kt"]).one()
    db.refresh(kt)
    assert (kt.planned_headcount, kt.planned_payroll_monthly, kt.note) == (8, 60_000_000, "Tăng")
    hc = db.query(HeadcountPlan).filter(HeadcountPlan.department_id == world.dept["B.hc"]).one()
    assert (hc.planned_headcount, hc.planned_payroll_monthly) == (3, 0)


@pytest.mark.parametrize("row", [
    "2026,CTY_A,A_KT,-3,,x", "1999,CTY_A,A_KT,3,,x", "2026,KHONG_CO,A_KT,3,,x", "2026,CTY_A,KHONG_PHONG,3,,x",
    "2026,CTY_A,A_KT,abc,,x", "2026,CTY_A,A_KT,3,-1,x",
])
def test_csv_nhap_nguyen_khoi_va_bao_loi_theo_dong(db, world, client_as, row):
    client = _hr(world, client_as)
    head = "year,company_code,department_code,planned_headcount,planned_payroll_monthly,note\n"
    good = "2026,CTY_A,A_MUA,3,,ok\n"
    resp = client.post(f"{URL}/import/csv", files={"file": ("k.csv", (head + good + row + "\n").encode(), "text/csv")})
    assert resp.status_code == 422, resp.text
    assert "Dòng 3" in resp.json()["error"]["message"] and "Dòng 2" not in resp.json()["error"]["message"]
    assert db.query(HeadcountPlan).count() == 0          # dòng tốt ở trên cũng không được ghi


@pytest.mark.parametrize("row,expect", [
    ("2026,CTY_A,A_KT,abc,,x", 'Ô "Định biên kế hoạch" phải là số'),
    ("2026,CTY_A,A_KT,3,-1,x", 'Ô "Quỹ lương kế hoạch / tháng" phải từ 0'),
    ("1999,CTY_A,A_KT,3,,x", 'Ô "Năm" phải từ 2000'),
])
def test_csv_loi_kieu_du_lieu_bang_tieng_viet(db, world, client_as, row, expect):
    #  E2E CR-689 M2: câu lỗi từng ra tiếng Anh («planned_headcount Input should be a valid integer»).
    client = _hr(world, client_as)
    head = "year,company_code,department_code,planned_headcount,planned_payroll_monthly,note\n"
    resp = client.post(f"{URL}/import/csv", files={"file": ("k.csv", (head + row + "\n").encode(), "text/csv")})
    assert resp.status_code == 422 and expect in resp.json()["error"]["message"], resp.text


def test_csv_nhap_trung_trong_tep_thieu_cot_va_khong_utf8(db, world, client_as):
    client = _hr(world, client_as)
    head = "year,company_code,department_code,planned_headcount,planned_payroll_monthly,note\n"
    dup = head + "2026,CTY_A,A_KT,3,,a\n2026,CTY_A,A_KT,4,,b\n"
    assert client.post(f"{URL}/import/csv", files={"file": ("k.csv", dup.encode(), "text/csv")}).status_code == 422
    assert client.post(f"{URL}/import/csv", files={"file": ("k.csv", b"year,note\n1,2\n", "text/csv")}).status_code == 400
    assert client.post(f"{URL}/import/csv", files={"file": ("k.csv", b"\xff\xfe\x00", "text/csv")}).status_code == 400


def test_csv_nhap_luong_khi_thieu_quyen_xem_luong_422_va_ngoai_pham_vi_403(db, world, client_as):
    head = "year,company_code,department_code,planned_headcount,planned_payroll_monthly,note\n"
    client = _hr(world, client_as, pay=False)
    resp = client.post(f"{URL}/import/csv", files={"file": ("k.csv", (head + "2026,CTY_A,A_KT,3,100,x\n").encode(), "text/csv")})
    assert resp.status_code == 422
    scoped = _hr(world, client_as, scope="dept", inc_dept=("A.kt",), key="a2")
    resp = scoped.post(f"{URL}/import/csv", files={"file": ("k.csv", (head + "2026,CTY_A,A_MUA,3,,x\n").encode(), "text/csv")})
    assert resp.status_code == 403 and db.query(HeadcountPlan).count() == 0


def test_csv_phong_dung_chung_company_id_0_nhap_duoc_va_vong_tron(db, world, client_as):
    from app.modules.department.model import Department
    db.query(Department).update({Department.company_id: 0})   # dữ liệu thật: phòng dùng chung mọi pháp nhân
    db.commit()
    client = _hr(world, client_as)
    head = "year,company_code,department_code,planned_headcount,planned_payroll_monthly,note\n"
    body = head + "2026,CTY_A,B_HC,3,10,x\n2026,CTY_B,A_KT,4,,y\n"
    resp = client.post(f"{URL}/import/csv", files={"file": ("k.csv", body.encode(), "text/csv")})
    assert resp.status_code == 200 and resp.json()["data"] == {"created": 2, "updated": 0}, resp.text
    out = client.get(f"{URL}/export/csv").content
    again = client.post(f"{URL}/import/csv", files={"file": ("k.csv", out, "text/csv")})
    assert again.status_code == 200 and again.json()["data"] == {"created": 0, "updated": 2}, again.text


def test_csv_ghi_chu_chong_cong_thuc_va_vong_tron(db, world, client_as):
    _add(db, world, dept="A.kt").note = "=HYPERLINK(\"x\")"
    db.commit()
    client = _hr(world, client_as)
    out = client.get(f"{URL}/export/csv").content
    assert "'=HYPERLINK" in out.decode("utf-8-sig")
    assert client.post(f"{URL}/import/csv", files={"file": ("k.csv", out, "text/csv")}).status_code == 200
    assert db.query(HeadcountPlan).one().note == "=HYPERLINK(\"x\")"      # không dồn dấu nháy


def test_luong_chi_hien_khi_quyen_hdld_phu_dung_phap_nhan_do(db, world, client_as):
    a = _add(db, world, dept="A.kt", co="A", pay=111)
    b = _add(db, world, dept="B.hc", co="B", pay=222)
    world.grant("a1", "headcount_plan", "all", actions=ALL)
    world.grant("a1", "labor_contract", "all", actions=("read",), inc_company=("A",))
    client = client_as(world.actor("a1").user)
    pay = {i["id"]: i["planned_payroll_monthly"] for i in client.get(URL).json()["data"]["items"]}
    assert pay == {a.id: 111, b.id: None}
    assert client.get(f"{URL}/{b.id}").json()["data"]["planned_payroll_monthly"] is None
    csv_text = client.get(f"{URL}/export/csv").content.decode("utf-8-sig")
    assert "111" in csv_text and "222" not in csv_text
    assert client.post(URL, json=_body(world, year=2033, company_id=world.co["B"],
                                       department_id=world.dept["B.hc"])).status_code == 403
    assert client.patch(f"{URL}/{b.id}", json={"planned_payroll_monthly": 5}).status_code == 403
    assert client.patch(f"{URL}/{a.id}", json={"planned_payroll_monthly": 5}).status_code == 200


def test_doi_phap_nhan_dong_co_luong_phai_xem_duoc_luong_ca_hai_ben(db, world, client_as):
    a = _add(db, world, dept="A.kt", co="A", pay=111)
    b = _add(db, world, dept="B.hc", co="B", pay=222)
    world.grant("a1", "headcount_plan", "all", actions=ALL)
    world.grant("a1", "labor_contract", "all", actions=("read",), inc_company=("A",))
    client = client_as(world.actor("a1").user)
    # dời dòng B (không xem được lương) sang A (xem được) -> 403, nếu không là đọc ra 222
    assert client.patch(f"{URL}/{b.id}", json={"company_id": world.co["A"]}).status_code == 403
    # dời dòng A (có lương) sang B (không xem được lương) -> 403
    assert client.patch(f"{URL}/{a.id}", json={"company_id": world.co["B"]}).status_code == 403
    db.refresh(a), db.refresh(b)
    assert (a.company_id, b.company_id) == (world.co["A"], world.co["B"])


def test_luong_an_khi_quyen_hdld_chi_phong_hoac_ban_than(db, world, client_as):
    a = _add(db, world, dept="A.kt", co="A", pay=111)
    world.grant("a1", "headcount_plan", "all", actions=ALL)
    world.grant("a1", "labor_contract", "dept", actions=("read",))
    client = client_as(world.actor("a1").user)
    assert client.get(f"{URL}/{a.id}").json()["data"]["planned_payroll_monthly"] is None
