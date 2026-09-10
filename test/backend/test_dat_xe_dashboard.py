"""Tổng quan Đặt xe — mỗi vai trò chỉ nhận đúng KHỐI của mình, số liệu theo phạm vi.

Chạy `build_overview` thật trên dữ liệu thật: khối vắng mặt khi thiếu quyền (không
trả 0), tài xế chỉ thấy chuyến của mình, điều phối/giám đốc thấy tổng hợp trong
phạm vi. Bắt đúng các nhầm lẫn dễ xảy ra: tài xế (cũng có `write`) KHÔNG được nhận
khối điều phối; người chỉ tạo phiếu KHÔNG thấy hàng chờ duyệt.
"""
from types import SimpleNamespace

from app.modules.employee.model import Employee
from app.modules.vehicle_booking.dashboard_service import build_overview
from app.modules.vehicle_booking.model import (
    BK_APPROVED,
    BK_COMPLETED,
    BK_DISPATCHED,
    BK_DRAFT,
    BK_PENDING,
    DRV_ONGOING,
    TYPE_CAR,
    TYPE_DELIVERY,
    Driver,
    VehicleBooking,
)

CTY, DEPT = 1, 10
_seq = {"n": 0}


def _person(db, cap_quyen, *, uid, dept, company, scope, **actions):
    emp = Employee(code=f"NV{uid}", full_name=f"NV{uid}", email=f"nv{uid}@dego.vn",
                   department_id=dept, company_id=company)
    db.add(emp)
    db.flush()
    cap_quyen(uid, "vehicle_booking", scope=scope, **actions)
    return SimpleNamespace(id=uid, employee_id=emp.id, email=f"nv{uid}@dego.vn")


def _booking(db, *, created_by, status=BK_DRAFT, request_type=TYPE_CAR, dept=DEPT,
             company=CTY, driver_status=0, assigned_driver_id=None, distance_km=0, cost=0):
    _seq["n"] += 1
    obj = VehicleBooking(
        code=f"XE{_seq['n']:04d}", request_type=request_type, status=status,
        created_by=created_by, requester_id=created_by,
        department_id=dept, company_id=company, driver_status=driver_status,
        assigned_driver_id=assigned_driver_id, distance_km=distance_km, cost=cost,
        purpose="[test]")
    db.add(obj)
    db.flush()
    return obj


def _seed(db, cap_quyen):
    """Một tài xế + một bộ phiếu nhiều trạng thái dùng chung cho mọi vai."""
    driver_user = _person(db, cap_quyen, uid=4004, dept=DEPT, company=CTY,
                          scope="assigned", read=True, write=True)
    drv = Driver(user_id=4004, name="Tài xế Tí")
    db.add(drv)
    db.flush()

    # Phiếu của "người dùng" own (uid 4001)
    _booking(db, created_by=4001, status=BK_DRAFT)
    _booking(db, created_by=4001, status=BK_PENDING)
    _booking(db, created_by=4001, status=BK_COMPLETED)
    # Hàng chờ điều phối + đang chạy + hoàn thành (loại giao hàng)
    _booking(db, created_by=9001, status=BK_APPROVED)
    _booking(db, created_by=9001, status=BK_DISPATCHED, driver_status=DRV_ONGOING,
             assigned_driver_id=drv.id, distance_km=10, cost=100_000)
    _booking(db, created_by=9001, status=BK_COMPLETED, request_type=TYPE_DELIVERY,
             distance_km=5, cost=50_000)
    return drv, driver_user


def test_nguoi_dung_chi_thay_khoi_phieu_cua_toi(db, cap_quyen):
    _seed(db, cap_quyen)
    user = _person(db, cap_quyen, uid=4001, dept=DEPT, company=CTY, scope="own",
                   read=True, create=True)
    data = build_overview(db, user)

    assert set(data) >= {"can", "mine"}
    assert data["mine"]["by_status"] == {BK_DRAFT: 1, BK_PENDING: 1, BK_COMPLETED: 1}
    # Người chỉ tạo phiếu KHÔNG có khối duyệt / điều phối / tổng hợp.
    assert "approve" not in data and "dispatch" not in data
    assert "driver" not in data and "company" not in data


def test_dieu_phoi_vien_thay_khoi_dispatch_va_kpi_doi_xe(db, cap_quyen):
    _seed(db, cap_quyen)
    user = _person(db, cap_quyen, uid=4003, dept=99, company=CTY, scope="all",
                   read=True, write=True)
    data = build_overview(db, user)

    d = data["dispatch"]
    assert d["to_dispatch"] == 1 and d["ongoing"] == 1 and d["completed"] == 2
    assert d["distance_sum"] == 15 and d["cost_sum"] == 150_000
    assert d["by_type"]["delivery"] == 1
    # Điều phối viên không tạo phiếu → không có "mine"; có tổng hợp (scope all).
    assert "mine" not in data and "company" in data


def test_nguoi_duyet_thay_hang_cho_duyet(db, cap_quyen):
    _seed(db, cap_quyen)
    user = _person(db, cap_quyen, uid=4002, dept=DEPT, company=CTY, scope="dept",
                   read=True, approve=True)
    data = build_overview(db, user)

    assert data["approve"]["pending"] == 1
    assert "dispatch" not in data  # chỉ duyệt, không điều phối
    assert "company" in data       # scope phòng ⇒ có khối tổng hợp phòng


def test_tai_xe_chi_thay_chuyen_cua_minh_khong_nhan_khoi_dieu_phoi(db, cap_quyen):
    _drv, driver_user = _seed(db, cap_quyen)
    data = build_overview(db, driver_user)

    assert data["driver"]["ongoing"] == 1
    # Tài xế cũng có `write` nhưng phạm vi `assigned` → KHÔNG được khối điều phối.
    assert "dispatch" not in data and "company" not in data


def test_giam_doc_chi_doc_thay_tong_hop_khong_thay_khoi_thao_tac(db, cap_quyen):
    _seed(db, cap_quyen)
    user = _person(db, cap_quyen, uid=4005, dept=99, company=CTY, scope="company",
                   read=True)
    data = build_overview(db, user)

    assert "company" in data
    total = sum(row["value"] for row in data["company"]["by_status"])
    assert total == 6  # toàn bộ phiếu công ty
    assert "mine" not in data and "approve" not in data and "dispatch" not in data


def test_khong_co_quyen_doc_thi_khong_co_khoi_nao(db, cap_quyen):
    _seed(db, cap_quyen)
    emp = Employee(code="NV4006", full_name="NV4006", email="nv4006@dego.vn",
                   department_id=DEPT, company_id=CTY)
    db.add(emp)
    db.flush()
    user = SimpleNamespace(id=4006, employee_id=emp.id, email="nv4006@dego.vn")
    data = build_overview(db, user)

    assert set(data) == {"can"}
    assert data["can"]["vehicle_booking"] is False
