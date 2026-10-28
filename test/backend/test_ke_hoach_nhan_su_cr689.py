"""duoc-CR-689 (phase 17) — kế hoạch nhân sự `/api/headcount-plans` (entity `headcount_plan`), khuôn MỚI theo kỳ (duoc-CR-690).

Bản đợt 4 (một dòng năm × pháp nhân × phòng, hai số «định biên» và «quỹ lương / tháng») đã thay bằng kế hoạch theo kỳ;
tệp này giữ các luật CR-689 vẫn đúng ở khuôn mới: CRUD + nhật ký, kiểm đầu vào, pháp nhân / phòng dùng chung, trùng khóa,
che tiền theo pháp nhân, thiếu quyền hành động, phạm vi dữ liệu, xuất CSV danh sách, và việc bảng không còn hai cột `planned_*`
mà báo cáo A4 / A5 vẫn đọc. Phần mới của CR-690 nằm ở `test_ke_hoach_nhan_su_theo_ky_cr690.py`.
"""
import pytest
from hdld_factory import client_as  # noqa: F401
from headcount_plan_factory import URL, add_plan, cost_item, grant_hr, plan_body
from pydantic import ValidationError

from app.modules.audit.model import AuditLog
from app.modules.headcount_plan.model import HeadcountPlan
from app.modules.headcount_plan.schema import HeadcountPlanCreate, PlanDraft


def _quiet(world, **kw):
    """Body không có tiền (một khoản cả phòng 0 đồng): người không xem được tiền cũng lưu được."""
    return plan_body(world, cost_items=[cost_item("L", 1)],
                     lines=[{"position_id": 0, "headcounts": [20, 20, 20, 20]}], **kw)


def test_crud_day_du_va_ghi_nhat_ky(db, world, client_as):
    client = grant_hr(world, client_as)
    resp = client.post(URL, json=plan_body(world))
    assert resp.status_code == 201, resp.text
    row = resp.json()["data"]
    assert row["company_name"] == "Công ty A" and row["department_name"] == "Phòng Kế toán"
    pid = row["id"]
    assert client.get(f"{URL}/{pid}").json()["data"]["note"] == "Được duyệt"
    resp = client.put(f"{URL}/{pid}", json=plan_body(world, note="Sửa"))
    assert resp.status_code == 200 and resp.json()["data"]["note"] == "Sửa"
    listing = client.get(URL, params={"year": 2026, "company_id": world.co["A"]}).json()["data"]
    assert listing["total"] == 1 and listing["items"][0]["id"] == pid
    assert client.get(URL, params={"year": 2027}).json()["data"]["total"] == 0
    assert client.get(URL, params={"period_type": 3}).json()["data"]["total"] == 0
    assert client.delete(f"{URL}/{pid}").status_code == 200
    assert client.get(f"{URL}/{pid}").status_code == 404
    actions = [a.action for a in db.query(AuditLog).filter(AuditLog.entity == "headcount_plan").all()]
    assert sorted(actions) == ["create", "delete", "update"]


def test_bang_ke_hoach_khong_con_cot_suy_ra(db, world, client_as):
    #  hcplan03: báo cáo A4 / A5 đọc kế hoạch có hiệu lực theo tháng (`headcount_plan.effective`), không còn cột suy ra.
    assert not hasattr(HeadcountPlan, "planned_headcount") and not hasattr(HeadcountPlan, "planned_payroll_monthly")
    assert {"planned_headcount", "planned_payroll_monthly"}.isdisjoint(HeadcountPlan.__table__.columns.keys())


def test_dong_toan_phap_nhan_department_id_0(db, world, client_as):
    client = grant_hr(world, client_as)
    resp = client.post(URL, json=plan_body(world, department_id=0))
    assert resp.status_code == 201, resp.text
    assert resp.json()["data"]["department_name"] == "Toàn pháp nhân"


def test_schema_chan_chuoi_dai_va_nam_ngoai_dai():
    with pytest.raises(ValidationError):
        HeadcountPlanCreate(year=2026, period_type=1, company_id=1, note="x" * 501)
    with pytest.raises(ValidationError):
        HeadcountPlanCreate(year=1999, period_type=1, company_id=1)
    with pytest.raises(ValidationError):
        PlanDraft(year=2026, period_type=1, company_id=1, basis_no="x" * 101)
    assert HeadcountPlanCreate(year=2000, period_type=1, company_id=1).department_id == 0
    assert HeadcountPlanCreate(year=2100, period_type=4, period_no=12, company_id=1, note="x" * 500).note == "x" * 500


def test_phap_nhan_phong_khong_hop_le_422(db, world, client_as):
    client = grant_hr(world, client_as)
    assert client.post(URL, json=plan_body(world, company_id=999_999)).status_code == 422
    assert client.post(URL, json=plan_body(world, department_id=999_999)).status_code == 422
    #  Phòng ban dùng chung cho mọi pháp nhân (dev/local: `tab_department_company` rỗng, `Department.company_id` = 0)
    #  — kế hoạch «pháp nhân A × phòng B.kt» là HỢP LỆ (28/10/2026).
    assert client.post(URL, json=plan_body(world, department_id=world.dept["B.kt"])).status_code == 201


def test_thieu_quyen_hanh_dong_403(db, world, client_as):
    world.grant("a1", "headcount_plan", "all", actions=("read",))
    client = client_as(world.actor("a1"))
    assert client.get(URL).status_code == 200
    assert client.post(URL, json=plan_body(world)).status_code == 403
    assert client.get(f"{URL}/export/csv").status_code == 403
    assert client.delete(f"{URL}/1").status_code == 403


def test_che_tien_theo_quyen_hdld_o_danh_sach_chi_tiet_va_csv(db, world, client_as):
    row = add_plan(db, world, lump=777_000_000)
    client = grant_hr(world, client_as, pay=False)
    item = client.get(URL).json()["data"]["items"][0]
    assert item["total_cost"] is None and item["headcount_end"] == 10
    assert client.get(f"{URL}/{row.id}").json()["data"]["computed"]["total"] is None
    csv_text = client.get(f"{URL}/export/csv").content.decode("utf-8-sig")
    assert "777000000" not in csv_text and "A_KT" in csv_text
    assert client.post(URL, json=plan_body(world, year=2030)).status_code == 403          # ghi tiền khi không xem được
    assert client.post(URL, json=_quiet(world, year=2030)).status_code == 201             # không có tiền thì ghi được


def test_tien_chi_hien_khi_quyen_hdld_phu_dung_phap_nhan_do(db, world, client_as):
    a = add_plan(db, world, dept="A.kt", co="A", lump=111)
    b = add_plan(db, world, dept="B.hc", co="B", lump=222)
    world.grant("a1", "headcount_plan", "all", actions=("read", "create", "write", "delete", "export"))
    world.grant("a1", "labor_contract", "all", actions=("read",), inc_company=("A",))
    client = client_as(world.actor("a1"))
    pay = {i["id"]: i["total_cost"] for i in client.get(URL).json()["data"]["items"]}
    assert pay == {a.id: 111, b.id: None}
    csv_text = client.get(f"{URL}/export/csv").content.decode("utf-8-sig")
    assert ",111," in csv_text and "222" not in csv_text
    assert client.post(URL, json=plan_body(world, year=2033, company_id=world.co["B"],
                                           department_id=world.dept["B.hc"])).status_code == 403


def test_luong_an_khi_quyen_hdld_chi_phong(db, world, client_as):
    a = add_plan(db, world, dept="A.kt", co="A", lump=111)
    world.grant("a1", "headcount_plan", "all", actions=("read",))
    world.grant("a1", "labor_contract", "dept", actions=("read",))
    client = client_as(world.actor("a1"))
    assert client.get(f"{URL}/{a.id}").json()["data"]["can_see_money"] is False


def test_pham_vi_phong_khong_thay_dong_toan_phap_nhan_va_phong_khac(db, world, client_as):
    mine = add_plan(db, world, dept="A.kt")
    other = add_plan(db, world, dept="A.mua")
    whole = add_plan(db, world, dept=None)
    client = grant_hr(world, client_as, scope="dept", inc_dept=("A.kt",))
    assert {i["id"] for i in client.get(URL).json()["data"]["items"]} == {mine.id}
    assert client.get(f"{URL}/{other.id}").status_code == 404
    assert client.get(f"{URL}/{whole.id}").status_code == 404
    assert client.delete(f"{URL}/{other.id}").status_code == 404
    assert client.post(URL, json=_quiet(world, year=2031, department_id=world.dept["A.mua"])).status_code == 403
    assert db.query(HeadcountPlan).filter(HeadcountPlan.year == 2031).count() == 0


def test_csv_danh_sach_xuat_dung_cot_va_chong_cong_thuc(db, world, client_as):
    add_plan(db, world, dept="A.kt", n=5, lump=600_000_000).note = "=HYPERLINK(\"x\")"
    add_plan(db, world, dept=None, n=40, lump=12_000_000)
    db.commit()
    client = grant_hr(world, client_as)
    text = client.get(f"{URL}/export/csv", params={"year": 2026}).content.decode("utf-8-sig")
    lines = text.strip().splitlines()
    assert lines[0] == ("year,period_type,period_no,period_label,company_code,department_code,headcount_end,"
                        "total_cost,basis_no,basis_date,note")
    assert any(ln.startswith("2026,1,1,2026,CTY_A,A_KT,5,600000000,") for ln in lines)
    assert any(ln.startswith("2026,1,1,2026,CTY_A,,40,12000000,") for ln in lines)
    assert "'=HYPERLINK" in text
