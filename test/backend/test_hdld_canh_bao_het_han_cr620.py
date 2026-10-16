"""duoc-CR-620 — cảnh báo HĐLĐ sắp hết hạn / đã hết hạn (chuông `/api/alerts` + thẻ Tổng quan Nhân sự).

Góc nhìn kẻ phá: HĐ đúng mốc 30/31/15/16 ngày, HĐ đã quá hạn, HĐ nháp / đã chấm dứt / không thời
hạn / đã xóa mềm, HĐ nối tiếp bị hủy hay bị xóa (không được tính là «đã xử»), HĐ CŨ hơn (không
được che HĐ mới), người đã nghỉ, pháp nhân khác, người không có quyền HĐLĐ, cửa sổ âm / quá lớn.
"""
from datetime import date, timedelta
from itertools import count

import pytest

from app.core.labor_contract_codes import LaborContractStatus as S
from app.core.vn_time import vn_today
from app.modules.employee.model import Employee
from app.modules.labor_contract import expiry_service
from app.modules.labor_contract.model import LaborContract
from hdld_factory import client_as, grant_all  # noqa: F401

TODAY = date(2026, 10, 16)
_seq = count(1)


def add_contract(db, world, emp_key="a2", *, end_in: int | None, status=S.SIGNED, start_ago=300,
                 contract_type=2, deleted=False, today=TODAY, co="A", dept="A.kt") -> LaborContract:
    row = LaborContract(
        code=f"HDLDT{next(_seq):04d}", employee_id=world.emp[emp_key], company_id=world.co[co],
        department_id=world.dept[dept], contract_type=contract_type, status=int(status),
        start_date=today - timedelta(days=start_ago),
        end_date=None if end_in is None else today + timedelta(days=end_in),
        is_deleted=deleted,
    )
    db.add(row)
    db.commit()
    return row


def found(db, **kw) -> dict[int, expiry_service.ExpiringContract]:
    return {c.id: c for c in expiry_service.find_expiring(db, TODAY, **kw)}


# ── Mốc ngày + mức ────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("end_in, level", [
    (30, "warn"), (16, "warn"),           # còn trong cửa sổ, chưa tới mốc báo trước 15 ngày
    (15, "danger"), (1, "danger"), (0, "danger"),
    (-1, "danger"), (-200, "danger"),     # hết hạn mà vẫn đi làm = không có HĐ: báo tới khi xử
])
def test_moc_ngay_ra_dung_muc(db, world, end_in, level):
    row = add_contract(db, world, end_in=end_in)
    hit = found(db)[row.id]
    assert (hit.days_left, hit.level) == (end_in, level)


def test_ngoai_cua_so_30_ngay_khong_bao(db, world):
    row = add_contract(db, world, end_in=31)
    assert row.id not in found(db)


def test_chu_tren_chuong_noi_dung_tinh_trang(db, world):
    rows = [add_contract(db, world, end_in=-3), add_contract(db, world, "a3", end_in=0, dept="A.mua"),
            add_contract(db, world, "khongtk", end_in=12)]
    hits = found(db)
    late, today, soon = (hits[r.id].alert_title() for r in rows)
    assert "ĐÃ HẾT HẠN 3 ngày" in late and "Nhân sự a2 (A2)" in late and "13/10/2026" in late
    assert "HÔM NAY" in today
    assert "còn 12 ngày" in soon and "28/10/2026" in soon


# ── Hợp đồng không thuộc diện báo ─────────────────────────────────────────────────────
@pytest.mark.parametrize("status", [S.DRAFT, S.TERMINATED, S.CANCELLED])
def test_chi_bao_hop_dong_da_ky(db, world, status):
    row = add_contract(db, world, end_in=5, status=status)
    assert row.id not in found(db)


def test_hop_dong_khong_thoi_han_va_da_xoa_mem_khong_bao(db, world):
    indefinite = add_contract(db, world, end_in=None, contract_type=3)
    deleted = add_contract(db, world, "a3", end_in=5, deleted=True, dept="A.mua")
    hits = found(db)
    assert indefinite.id not in hits and deleted.id not in hits


# ── Đã có hợp đồng nối tiếp = Nhân sự đã xử ──────────────────────────────────────────
@pytest.mark.parametrize("next_status", [S.DRAFT, S.SIGNED])
def test_co_hop_dong_noi_tiep_thi_thoi_bao(db, world, next_status):
    old = add_contract(db, world, end_in=10)
    add_contract(db, world, end_in=375, status=next_status, start_ago=-11)
    assert old.id not in found(db)


def test_nhap_noi_tiep_khong_che_hop_dong_da_qua_han(db, world):
    #  Rà soát M1: hết hạn rồi mà bản nháp gia hạn vẫn nằm đó = đang đi làm không có HĐ hiệu lực.
    old = add_contract(db, world, end_in=-2)
    add_contract(db, world, end_in=360, status=S.DRAFT, start_ago=1)
    assert found(db)[old.id].level == "danger"


def test_hop_dong_da_ky_noi_tiep_che_ca_hop_dong_da_qua_han(db, world):
    old = add_contract(db, world, end_in=-2)
    add_contract(db, world, end_in=360, start_ago=1)
    assert old.id not in found(db)


def test_hop_dong_noi_tiep_bi_huy_hoac_bi_xoa_khong_tinh_la_da_xu(db, world):
    old = add_contract(db, world, end_in=10)
    add_contract(db, world, end_in=375, status=S.CANCELLED, start_ago=-11)
    add_contract(db, world, end_in=375, start_ago=-11, status=S.DRAFT, deleted=True)
    assert old.id in found(db)


def test_hop_dong_cu_hon_khong_che_hop_dong_moi(db, world):
    #  HĐ thử việc cũ đã ký (bắt đầu TRƯỚC) không phải «HĐ nối tiếp» của HĐ chính thức.
    add_contract(db, world, end_in=-300, start_ago=400, contract_type=1)
    current = add_contract(db, world, end_in=10, start_ago=290)
    hits = found(db)
    assert current.id in hits


def test_hai_hop_dong_cung_ngay_bat_dau_khong_che_nhau(db, world):
    first = add_contract(db, world, end_in=10, start_ago=100)
    second = add_contract(db, world, end_in=20, start_ago=100)
    assert {first.id, second.id} <= set(found(db))


@pytest.mark.parametrize("change", [{"status": "resigned"}, {"is_active": False}])
def test_nguoi_da_nghi_viec_khong_bao(db, world, change):
    row = add_contract(db, world, end_in=5)
    emp = db.get(Employee, world.emp["a2"])
    for field, value in change.items():
        setattr(emp, field, value)
    db.commit()
    assert row.id not in found(db)


def test_xep_het_han_som_nhat_len_dau(db, world):
    later = add_contract(db, world, end_in=20)
    overdue = add_contract(db, world, "a3", end_in=-5, dept="A.mua")
    soon = add_contract(db, world, "khongtk", end_in=2)
    ids = [c.id for c in expiry_service.find_expiring(db, TODAY)]
    assert ids == [overdue.id, soon.id, later.id]


@pytest.mark.parametrize("asked, sees_100_days_out", [(-5, False), (0, False), (10**9, True)])
def test_cua_so_am_hoac_qua_lon_bi_cat_ve_dai_hop_le(db, world, asked, sees_100_days_out):
    far = add_contract(db, world, end_in=100)
    overdue = add_contract(db, world, "a3", end_in=-1, dept="A.mua")
    hits = found(db, within_days=asked)
    assert overdue.id in hits                      # cửa sổ 0 vẫn phải thấy HĐ ĐÃ quá hạn
    assert (far.id in hits) is sees_100_days_out   # 10^9 cắt về 180 ngày, không nổ SQL


# ── Đường API + phạm vi ──────────────────────────────────────────────────────────────
@pytest.fixture
def api(db, world, client_as):  # noqa: F811
    grant_all(world, "a1", template=False)   # Nhân sự pháp nhân A
    grant_all(world, "b1", template=False)   # Nhân sự pháp nhân B
    real_today = vn_today()
    row = add_contract(db, world, end_in=7, today=real_today)
    return row, client_as


def test_api_chi_tra_hop_dong_trong_pham_vi_va_khong_lo_luong(db, world, api):
    row, client_as = api
    res = client_as(world.actor("a1")).get("/api/labor-contracts/expiring")
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert [i["id"] for i in data["items"]] == [row.id]
    item = data["items"][0]
    assert (item["days_left"], item["level"], item["employee_name"]) == (7, "danger", "Nhân sự a2")
    assert {"base_salary", "insurance_salary", "allowance"}.isdisjoint(item)
    assert (data["danger"], data["warn_days"], data["danger_days"]) == (1, 30, 15)

    other = client_as(world.actor("b1")).get("/api/labor-contracts/expiring")
    assert other.status_code == 200 and other.json()["data"]["items"] == []


def test_api_khong_co_quyen_hdld_bi_chan(world, api):
    _, client_as = api
    assert client_as(world.actor("a3")).get("/api/labor-contracts/expiring").status_code == 403


def test_duong_expiring_khong_bi_nuot_boi_duong_theo_id(world, api):
    #  Khai sau `/{cid}` thì «expiring» bị đọc thành id và ăn 422.
    _, client_as = api
    res = client_as(world.actor("a1")).get("/api/labor-contracts/expiring")
    assert res.status_code == 200, res.text


def test_co_nguoi_xem_ma_thieu_profile_van_loc_pham_vi(db, world, api):
    #  Rà soát L1: nơi gọi quên truyền `profile` không được thành «trả hết».
    row, _ = api
    assert row.id not in {c.id for c in expiry_service.find_expiring(db, vn_today(), user=world.actor("b1").user)}
    assert row.id in {c.id for c in expiry_service.find_expiring(db, vn_today(), user=world.actor("a1").user)}


# ── Chuông cảnh báo ──────────────────────────────────────────────────────────────────
def _labor_alerts(client) -> list[dict]:
    res = client.get("/api/alerts")
    assert res.status_code == 200, res.text
    return [i for i in res.json()["data"]["items"] if i["type"] == "labor_contract"]


def test_chuong_bao_dung_nguoi_dung_pham_vi(world, api):
    row, client_as = api
    mine = _labor_alerts(client_as(world.actor("a1")))
    assert [(a["key"], a["level"]) for a in mine] == [(f"labor_contract:{row.id}:danger", "danger")]
    assert mine[0]["link"] == f"/employees/{world.emp['a2']}?tab=labor-contracts"
    assert _labor_alerts(client_as(world.actor("b1"))) == []      # pháp nhân khác
    assert _labor_alerts(client_as(world.actor("a3"))) == []      # không có quyền HĐLĐ


# ── Tab Việc cần làm: tập cha của chuông + ẩn được ───────────────────────────────────
def test_viec_can_lam_chua_canh_bao_hdld_va_danh_dau_lam_het_an_duoc_chuong(world, api):
    #  Rà soát H1: thiếu khối HĐLĐ ở `build_my_tasks` thì cảnh báo trên chuông không ẩn được bằng cách nào.
    row, client_as = api
    a1 = client_as(world.actor("a1"))
    tasks = a1.get("/api/dashboard/tasks?page_size=500").json()["data"]["items"]
    labor = [t for t in tasks if t["type"] == "labor_contract"]
    assert [t["key"] for t in labor] == [f"labor_contract:{row.id}:danger"]
    assert labor[0]["link"] == f"/employees/{world.emp['a2']}?tab=labor-contracts"
    assert {a["key"] for a in _labor_alerts(a1)} <= {t["key"] for t in tasks}

    assert a1.post("/api/dashboard/tasks/dismiss", json={"all": True}).status_code == 200
    assert _labor_alerts(a1) == []
    #  Ẩn là của TÀI KHOẢN đó — người khác cùng phạm vi vẫn thấy.
    grant_all(world, "a3", template=False)
    assert len(_labor_alerts(client_as(world.actor("a3")))) == 1
