"""Điểm cà phê × POS365 — 6 bài bắt buộc của phase CP2
(`doc/erp/diem-ca-phe/06-lo-trinh-phase.md`):

1. Kéo đơn 2 lần trên cùng dữ liệu — lần hai không ghi gì, số dư không đổi.
2. Reset kỳ 2 lần cùng kỳ — không nhân đôi điểm (nghiệm thu 2 của `09` §11).
3. Đơn void → đúng MỘT dòng hoàn, chạy lại không hoàn thêm.
4. Nhân sự nghỉ việc → số dư về 0, có dòng REVOKE (nghiệm thu 3).
5. SUM(sổ) = số dư hiển thị với chuỗi giao dịch trộn đủ loại (nghiệm thu 5).
6. POS365_HARD_OFF bật → KHÔNG một HTTP call nào phát ra (nghiệm thu 9).

POS365 mock ở tầng client (FakeClient) — service không biết gì về HTTP.
"""
import json

import pytest

from app.core.config import settings
from app.modules.coffee_point import service
from app.modules.coffee_point.model import (CoffeeLedger, CoffeeLedgerType,
                                            CoffeeMember, CoffeeMemberStatus,
                                            CoffeePolicy, PosOrder)
from app.modules.coffee_point.pos365_client import (Pos365Client,
                                                    Pos365Disabled)
from app.modules.employee.model import Employee

ACCOUNT_ID = 7815  # tài khoản thanh toán "Trừ điểm" giả lập


@pytest.fixture(autouse=True)
def _account_id(monkeypatch):
    monkeypatch.setattr(settings, "POS365_PAYMENT_ACCOUNT_ID", ACCOUNT_ID)


def lam_don(oid: int, partner_id: int, value: int, status: int = 2,
            extra_cash: int = 0) -> dict:
    """Một đơn POS365 như spec §5.3 — nhiều phương thức qua MoreAttributes.

    PurchaseDate = giờ UTC hiện tại để không rơi ra ngoài mốc kéo tăng dần
    (`_pull_cutoff` mặc định là đầu ngày hôm qua) dù test chạy ngày nào.
    """
    from datetime import datetime, timedelta
    utc_now = datetime.now() - timedelta(hours=7)
    methods = [{"AccountId": ACCOUNT_ID, "Value": value}]
    if extra_cash:
        methods.append({"AccountId": None, "Value": extra_cash})
    return {
        "Id": oid, "Code": f"HC-{oid}",
        "PurchaseDate": utc_now.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
        "Partner": {"Id": partner_id}, "Status": status,
        "Total": value + extra_cash, "TotalPayment": value + extra_cash,
        "MoreAttributes": json.dumps({"PaymentMethods": methods}),
    }


class FakeClient:
    """POS365 giả — trả đơn từ bộ nhớ, phân trang như thật."""

    def __init__(self, orders: list[dict]):
        self.orders = orders

    def list_orders(self, top=50, skip=0, **kw):
        return {"__count": len(self.orders), "results": self.orders[skip:skip + top]}

    def get_order(self, oid):
        return next((o for o in self.orders if o["Id"] == oid), None)


def dung_thanh_vien(db, code="NV001", partner_id=555, level=1, company=1):
    emp = Employee(code=code, full_name=f"Nhân sự {code}", company_id=company)
    db.add(emp)
    db.flush()
    m = CoffeeMember(employee_id=emp.id, level_code=level, company_id=company,
                     pos_partner_id=partner_id,
                     status=int(CoffeeMemberStatus.ACTIVE))
    db.add(m)
    db.flush()
    return emp, m


# ── 1. Kéo đơn idempotent ──────────────────────────────────────────────────────

def test_keo_don_hai_lan_khong_tru_hai_lan(db):
    emp, _ = dung_thanh_vien(db)
    client = FakeClient([lam_don(1001, 555, 30000),
                         lam_don(1002, 555, 20000, extra_cash=15000)])

    s1 = service.run_pull_orders(db, client)
    assert s1["written"] == 2
    #  Đơn hỗn hợp: chỉ phần trả bằng tài khoản "Trừ điểm" vào sổ, tiền mặt không.
    assert service.balance_of(db, emp.id) == -50000

    s2 = service.run_pull_orders(db, client)
    assert s2["written"] == 0
    assert service.balance_of(db, emp.id) == -50000
    assert db.query(CoffeeLedger).filter(
        CoffeeLedger.type == int(CoffeeLedgerType.SPEND)).count() == 2


def test_don_khong_ghep_duoc_thi_cho_xu_ly_khong_doan(db):
    """D-02: khách lạ → UNMATCHED, KHÔNG dòng sổ nào."""
    dung_thanh_vien(db, partner_id=555)
    client = FakeClient([lam_don(2001, 999, 40000)])   # partner 999 chưa ghép ai
    s = service.run_pull_orders(db, client)
    assert s["written"] == 1
    row = db.query(PosOrder).filter(PosOrder.pos_order_id == 2001).one()
    assert row.match_status == 2   # UNMATCHED
    assert db.query(CoffeeLedger).count() == 0

    #  Gán tay (resolve) → có dòng tiêu, đúng một lần.
    emp2, _ = dung_thanh_vien(db, code="NV002", partner_id=777)
    service.resolve_order(db, row, employee_id=emp2.id, actor_id=1)
    assert service.balance_of(db, emp2.id) == -40000


# ── 2. Reset kỳ idempotent ─────────────────────────────────────────────────────

def test_reset_ky_hai_lan_khong_nhan_doi(db):
    emp, _ = dung_thanh_vien(db)
    db.add(CoffeePolicy(company_id=1, level_code=1, monthly_points=200000,
                        effective_from="2026-01-01"))
    db.flush()

    s1 = service.run_monthly_reset(db, period="202609")
    assert s1["granted"] == 1
    assert service.balance_of(db, emp.id) == 200000

    s2 = service.run_monthly_reset(db, period="202609")
    assert s2["granted"] == 0 and s2["skipped"] == 1
    assert service.balance_of(db, emp.id) == 200000   # nghiệm thu 2: không nhân đôi


def test_reset_thu_het_du_ky_cu_roi_cap_moi(db):
    """Không cộng dồn (N2 đã chốt): dư 80k kỳ trước → expire hết rồi cấp mức mới."""
    emp, _ = dung_thanh_vien(db)
    db.add(CoffeePolicy(company_id=1, level_code=1, monthly_points=200000,
                        effective_from="2026-01-01"))
    db.flush()
    service.append_ledger(db, company_id=1, employee_id=emp.id, period="202608",
                          type_=CoffeeLedgerType.GRANT, points=80000)

    service.run_monthly_reset(db, period="202609", prev_period="202608")
    assert service.balance_of(db, emp.id) == 200000
    expire = db.query(CoffeeLedger).filter(
        CoffeeLedger.type == int(CoffeeLedgerType.EXPIRE)).one()
    assert expire.points == -80000 and expire.period == "202608"


def test_cap_chua_khai_muc_thi_khong_cap_mo(db):
    """Cấp chưa có dòng chính sách = lỗi CẤU HÌNH — bỏ qua + nổi lên, không cấp mò."""
    emp, _ = dung_thanh_vien(db, level=3)   # MANAGER, chưa khai mức
    s = service.run_monthly_reset(db, period="202609")
    assert s["granted"] == 0
    assert s["no_policy"] == [emp.id]
    assert service.balance_of(db, emp.id) == 0


# ── 3. Đơn void → hoàn đúng một lần ────────────────────────────────────────────

def test_don_void_hoan_dung_mot_lan(db):
    emp, _ = dung_thanh_vien(db)
    don = lam_don(3001, 555, 60000)
    client = FakeClient([don])
    service.run_pull_orders(db, client)
    assert service.balance_of(db, emp.id) == -60000

    don["Status"] = 3   # quầy hủy bill
    s1 = service.run_check_voids(db, client)
    assert s1["written"] == 1
    assert service.balance_of(db, emp.id) == 0

    s2 = service.run_check_voids(db, client)   # chạy lại: đơn đã is_voided, bỏ qua
    assert s2["written"] == 0
    assert service.balance_of(db, emp.id) == 0
    assert db.query(CoffeeLedger).filter(
        CoffeeLedger.type == int(CoffeeLedgerType.REFUND)).count() == 1


# ── 4. Nghỉ việc → thu hồi về 0 ────────────────────────────────────────────────

def test_nghi_viec_thu_hoi_ve_khong(db):
    emp, m = dung_thanh_vien(db)
    service.append_ledger(db, company_id=1, employee_id=emp.id, period="202609",
                          type_=CoffeeLedgerType.GRANT, points=150000)
    revoked = service.mark_member_left(db, m, actor_id=9)
    assert revoked == 150000
    assert service.balance_of(db, emp.id) == 0
    assert m.status == int(CoffeeMemberStatus.LEFT)
    assert db.query(CoffeeLedger).filter(
        CoffeeLedger.type == int(CoffeeLedgerType.REVOKE)).count() == 1
    #  Đã LEFT thì reset kỳ sau bỏ qua — người nghỉ không được cấp lại.
    db.add(CoffeePolicy(company_id=1, level_code=1, monthly_points=200000,
                        effective_from="2026-01-01"))
    db.flush()
    service.run_monthly_reset(db, period="202610")
    assert service.balance_of(db, emp.id) == 0


# ── 5. Số dư = SUM(sổ) với chuỗi trộn đủ loại ──────────────────────────────────

def test_so_du_bang_tong_so(db):
    emp, _ = dung_thanh_vien(db)
    ghi = [
        (CoffeeLedgerType.GRANT, 200000, 0),
        (CoffeeLedgerType.SPEND, -35000, 9001),
        (CoffeeLedgerType.SPEND, -20000, 9002),
        (CoffeeLedgerType.REFUND, 20000, 9002),
        (CoffeeLedgerType.ADJUST, -5000, 0),
        (CoffeeLedgerType.EXPIRE, -160000, 0),
    ]
    for t, p, oid in ghi:
        service.append_ledger(db, company_id=1, employee_id=emp.id, period="202609",
                              type_=t, points=p, pos_order_id=oid,
                              reason="test điều chỉnh")
    tong = sum(p for _, p, _ in ghi)
    assert service.balance_of(db, emp.id) == tong == 0


def test_dieu_chinh_bat_buoc_ly_do(db):
    emp, _ = dung_thanh_vien(db)
    with pytest.raises(ValueError):
        service.append_ledger(db, company_id=1, employee_id=emp.id, period="202609",
                              type_=CoffeeLedgerType.ADJUST, points=1000, reason="  ")


# ── Cấp VÔ HẠN + duyệt cấp phát từng kỳ (chốt 08/09/2026) ──────────────────────

def test_cap_vo_han_khong_cap_khong_thu_van_ghi_tieu(db):
    """Chúa tể HĐQT: reset bỏ qua trọn (không grant/expire), nhưng dòng TIÊU vẫn
    vào sổ — vô hạn là không ai chặn, không phải không ai đếm."""
    from app.modules.coffee_point.model import CoffeeLevel
    emp, m = dung_thanh_vien(db, level=int(CoffeeLevel.OVERLORD))
    db.add(CoffeePolicy(company_id=1, level_code=int(CoffeeLevel.OVERLORD),
                        monthly_points=999, effective_from="2026-01-01"))
    db.flush()
    s = service.run_monthly_reset(db, period="202609")
    assert s["granted"] == 0
    assert service.balance_of(db, emp.id) == 0
    assert m.is_unlimited is True
    #  Tiêu vẫn ghi — âm vô tư.
    service.append_ledger(db, company_id=1, employee_id=emp.id, period="202609",
                          type_=CoffeeLedgerType.SPEND, points=-70000, pos_order_id=71)
    assert service.balance_of(db, emp.id) == -70000


def test_du_kien_khong_ghi_dong_nao(db):
    """A-06: bảng DỰ KIẾN (dry_run) liệt kê đúng thu/cấp mà sổ vẫn trắng —
    đường ghi thật chỉ còn bước CHỐT."""
    emp, _ = dung_thanh_vien(db)
    db.add(CoffeePolicy(company_id=1, level_code=1, monthly_points=150000,
                        effective_from="2026-01-01"))
    db.flush()
    service.append_ledger(db, company_id=1, employee_id=emp.id, period="202608",
                          type_=CoffeeLedgerType.GRANT, points=20000)

    s = service.run_monthly_reset(db, period="202609", dry_run=True)
    assert s["preview"] == [{
        "employee_id": emp.id, "level_code": 1, "level_label": "Thực tập sinh",
        "current_balance": 20000, "expire": -20000, "grant": 150000,
        "already_granted": False,
    }]
    assert service.balance_of(db, emp.id) == 20000     # chưa ghi gì
    assert db.query(CoffeeLedger).count() == 1

    #  Chốt thật rồi xem lại dự kiến: đánh dấu đã cấp, không đề nghị cấp nữa.
    service.run_monthly_reset(db, period="202609", actor_id=9)
    s2 = service.run_monthly_reset(db, period="202609", dry_run=True)
    assert s2["preview"][0]["already_granted"] is True
    assert s2["preview"][0]["grant"] == 0
    assert service.balance_of(db, emp.id) == 150000


# ── Màn Quản lý POS: gom số thuần từ đơn thô ───────────────────────────────────

def test_pos_dashboard_gom_dung_so():
    """Đơn hôm nay chia đúng ba túi (tiền mặt / trừ điểm / tài khoản khác);
    đơn void không tính doanh thu; đơn ngoài cửa sổ ngày không vào biểu đồ."""
    from datetime import datetime, timedelta
    utc_now = datetime.now() - timedelta(hours=7)

    def don(oid, aid, total, days_ago=0, status=2):
        t = utc_now - timedelta(days=days_ago)
        return {"Id": oid, "Code": f"HD-{oid}", "Status": status, "Total": total,
                "AccountId": aid,
                "PurchaseDate": t.strftime("%Y-%m-%dT%H:%M:%S.0000000Z"),
                "Partner": {"Name": "Khách"}}

    orders = [
        don(1, None, 50000),                 # tiền mặt hôm nay
        don(2, ACCOUNT_ID, 30000),           # trừ điểm hôm nay
        don(3, 19377, 20000),                # chuyển khoản hôm nay
        don(4, None, 99000, status=3),       # void hôm nay — không tính doanh thu
        don(5, None, 40000, days_ago=1),     # hôm qua — vào biểu đồ, không vào "hôm nay"
        don(6, None, 70000, days_ago=30),    # ngoài cửa sổ 7 ngày — bỏ
    ]
    accounts = [{"Id": 19377, "Name": "CHUYỂN KHOẢN"}, {"Id": ACCOUNT_ID, "Name": "TRU DIEM"}]
    data = service.build_pos_dashboard(orders, accounts, ACCOUNT_ID, days=7)

    assert data["today"] == {"orders": 3, "revenue": 100000, "cash": 50000,
                             "account": 20000, "points": 30000, "voided": 1}
    assert len(data["by_day"]) == 7
    assert data["by_day"][-1]["value"] == 100000      # hôm nay
    assert data["by_day"][-2]["value"] == 40000       # hôm qua
    assert sum(d["value"] for d in data["by_day"]) == 140000  # đơn 30 ngày trước không lọt
    methods = {r["code"]: r["method"] for r in data["recent"]}
    assert methods["HD-1"] == "Tiền mặt"
    assert methods["HD-2"] == "Trừ điểm"
    assert methods["HD-3"] == "CHUYỂN KHOẢN"
    assert next(r for r in data["recent"] if r["code"] == "HD-4")["is_voided"] is True


# ── 6. Cầu dao HARD_OFF: không một HTTP call nào ───────────────────────────────

class SpySession:
    """requests.Session giả — đếm mọi lần bị gọi; bị gọi là test đỏ."""

    def __init__(self):
        self.calls = 0

    def request(self, *a, **kw):
        self.calls += 1
        raise AssertionError("HARD_OFF bật mà vẫn có HTTP call ra POS365")

    get = post = request


def test_hard_off_khong_mot_call_nao(db, monkeypatch):
    monkeypatch.setattr(settings, "POS365_HARD_OFF", True)
    spy = SpySession()
    client = Pos365Client(base_url="https://test.pos365.vn", username="api",
                          password="x", session=spy)
    for goi in (client.login,
                client.list_orders,
                lambda: client.get_order(1),
                lambda: client.search_partners("0909"),
                lambda: client.create_partner("A", "0909"),
                client.list_accounts):
        with pytest.raises(Pos365Disabled):
            goi()
    assert spy.calls == 0
    #  Cả vòng nghiệp vụ cũng dừng sạch ở cầu dao — service không nuốt lỗi này.
    dung_thanh_vien(db)
    with pytest.raises(Pos365Disabled):
        service.run_pull_orders(db, client)
    assert spy.calls == 0


def test_chua_cau_hinh_base_url_cung_la_hard_off(monkeypatch):
    monkeypatch.setattr(settings, "POS365_HARD_OFF", False)
    spy = SpySession()
    client = Pos365Client(base_url="", username="", password="", session=spy)
    with pytest.raises(Pos365Disabled):
        client.list_orders()
    assert spy.calls == 0
