# -*- coding: utf-8 -*-
"""Seed DEMO cho phân hệ Đặt xe: 1 luồng duyệt + 10 phiếu đủ trạng thái.

Chạy: docker compose exec -T api python scripts/seed_datxe_demo.py
Idempotent: đã có thì bỏ qua (không nhân đôi). Dữ liệu để XEM/THỬ trên
/vehicle-booking và /approval/flows — không phải dữ liệu thật.
"""
import json
from datetime import datetime

import app.core.all_models  # noqa: F401 — nạp toàn bộ model để mapper resolve được quan hệ
from app.core.database import SessionLocal
from app.modules.approval.flow_model import (
    APPROVER_DEPT_HEAD, APPROVER_ROLE, MULTI_ANY, NODE_APPROVAL, ROLE_APPROVE,
    ApprovalFlow, ApprovalNode,
)
from app.modules.employee.model import Employee
from app.modules.user.model import User
from app.modules.vehicle_booking import model as m


def seed_flow(db):
    """Luồng duyệt cho vehicle_booking: TBP người nộp → Quản lý điều phối (vai trò)."""
    flow = db.query(ApprovalFlow).filter(
        ApprovalFlow.entity == "vehicle_booking",
        ApprovalFlow.name == "Duyệt yêu cầu đặt xe",
    ).first()
    if flow:
        print("Luồng duyệt đã có:", flow.id)
        return flow
    flow = ApprovalFlow(
        entity="vehicle_booking", code="DATXE", name="Duyệt yêu cầu đặt xe",
        description="Bước 1 Trưởng bộ phận người nộp duyệt; bước 2 Quản lý điều phối duyệt.",
        version_no=1, is_active=True, company_id=None, priority=0, condition="",
        created_by=0, updated_by=0,
    )
    db.add(flow)
    db.flush()
    db.add_all([
        ApprovalNode(
            flow_id=flow.id, seq=1, name="Trưởng bộ phận duyệt",
            node_kind=NODE_APPROVAL, flow_role=ROLE_APPROVE,
            approver_kind=APPROVER_DEPT_HEAD, approver_ref="",  # trưởng phòng người nộp
            multi_mode=MULTI_ANY, created_by=0, updated_by=0,
        ),
        ApprovalNode(
            flow_id=flow.id, seq=2, name="Quản lý điều phối duyệt",
            node_kind=NODE_APPROVAL, flow_role=ROLE_APPROVE,
            approver_kind=APPROVER_ROLE, approver_ref="booking_manager",  # theo vai trò
            multi_mode=MULTI_ANY, created_by=0, updated_by=0,
        ),
    ])
    db.commit()
    print("Đã tạo luồng duyệt:", flow.id, "(2 bước)")
    return flow


def _stops(*names):
    return json.dumps([{"location": n, "contact_name": "", "contact_phone": ""} for n in names],
                      ensure_ascii=False)


def seed_bookings(db):
    if db.query(m.VehicleBooking).filter(m.VehicleBooking.code.like("DXTC%")).first():
        print("Phiếu demo DXTC đã có — bỏ qua.")
        return

    # Người tạo = admin (để tài khoản admin phạm vi 'all' nhìn thấy hết).
    admin = db.query(User).filter(User.email.like("%admin%")).first() or db.query(User).first()
    uid = admin.id if admin else 0
    emp = db.get(Employee, admin.employee_id) if admin and admin.employee_id else None
    name = (emp.full_name if emp and emp.full_name else "") or (admin.email if admin else "Demo")
    dept = emp.department_id if emp else 0
    company = emp.company_id if emp else 0

    # Xe + tài xế để gán cho phiếu đã điều phối (dùng cái đang có, hoặc tạo).
    veh = db.query(m.Vehicle).first()
    if not veh:
        veh = m.Vehicle(license_plate="65C-172.76", model="Toyota Hilux", type="Bán tải")
        db.add(veh); db.flush()
    drv = db.query(m.Driver).first()
    if not drv:
        drv = m.Driver(name="Lê Minh Thông", phone="0907507103", license_number="B2")
        db.add(drv); db.flush()

    ST = "2026-09-10T08:00"
    ET = "2026-09-10T11:00"

    common = dict(requester=name, requester_id=uid, department_id=dept, company_id=company,
                  start_time=ST, end_time=ET, created_by=uid, updated_by=uid)

    rows = [
        # (code, mô tả, request_type, status, driver_status, purpose, gán xe/tài xế, thêm)
        ("DXTC01", m.TYPE_CAR, m.BK_DRAFT, m.DRV_NONE, "Đi khảo sát mặt bằng Q7", False, {}),
        ("DXTC02", m.TYPE_DELIVERY, m.BK_PENDING, m.DRV_NONE, "Giao hồ sơ thầu cho đối tác", False,
         dict(goods_name="Thùng hồ sơ", sender_name="Ngân", sender_phone="0901",
              receiver_name="Bình", receiver_phone="0902")),
        ("DXTC03", m.TYPE_CAR, m.BK_APPROVED, m.DRV_NONE, "Đón khách sân bay Tân Sơn Nhất", False,
         dict(passenger_count=3, is_round_trip=True)),
        ("DXTC04", m.TYPE_CAR, m.BK_DISPATCHED, m.DRV_WAITING, "Họp chi nhánh Bình Dương", True, {}),
        ("DXTC05", m.TYPE_DELIVERY, m.BK_DISPATCHED, m.DRV_ACCEPTED, "Giao mẫu sản phẩm cho khách", True,
         dict(goods_name="Mẫu SP", sender_name="Kho", sender_phone="0903",
              receiver_name="Khách A", receiver_phone="0904")),
        ("DXTC06", m.TYPE_CAR, m.BK_DISPATCHED, m.DRV_ONGOING, "Đi công tác Long An", True,
         dict(actual_start_time="2026-09-10T08:05")),
        ("DXTC07", m.TYPE_CAR, m.BK_COMPLETED, m.DRV_COMPLETED, "Đưa đoàn tham quan nhà máy", True,
         dict(actual_start_time="2026-09-09T08:00", actual_end_time="2026-09-09T16:30",
              distance_km=120, cost=850000)),
        ("DXTC08", m.TYPE_DELIVERY, m.BK_RETURNED, m.DRV_NONE, "Giao quà Tết (thiếu địa chỉ nhận)", False,
         dict(goods_name="Giỏ quà", sender_name="HC", sender_phone="0905",
              receiver_name="", receiver_phone="", note="Bổ sung địa chỉ người nhận rồi gửi lại.")),
        ("DXTC09", m.TYPE_CAR, m.BK_REJECTED, m.DRV_NONE, "Đi ăn trưa nhóm (ngoài công tác)", False,
         dict(note="Không thuộc mục đích công tác.")),
        ("DXTC10", m.TYPE_CAR, m.BK_CANCELLED, m.DRV_NONE, "Đi gặp khách (khách hoãn lịch)", False, {}),
    ]

    created = 0
    for code, rtype, status, dstatus, purpose, dispatched, extra in rows:
        b = m.VehicleBooking(
            code=code, request_type=rtype, status=status, driver_status=dstatus,
            purpose=purpose, start_location="Văn phòng Degoholding", end_location="Địa điểm công tác",
            stops=_stops("Ghé kho Q4"), note=extra.pop("note", ""),
            **common,
        )
        for k, v in extra.items():
            setattr(b, k, v)
        if dispatched:
            b.assigned_vehicle_id = veh.id
            b.assigned_driver_id = drv.id
            b.dispatched_by = uid
            b.dispatched_at = datetime.now().isoformat(timespec="seconds")
        db.add(b)
        created += 1
    db.commit()
    print(f"Đã tạo {created} phiếu demo (DXTC01..DXTC10) đủ trạng thái.")


def main():
    db = SessionLocal()
    try:
        seed_flow(db)
        seed_bookings(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
