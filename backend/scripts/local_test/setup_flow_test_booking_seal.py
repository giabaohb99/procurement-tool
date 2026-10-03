"""Dựng bộ THỬ luồng duyệt cấu hình cho Đặt xe + Duyệt dấu — CHỈ DÙNG Ở LOCAL.

Làm 5 việc, chạy lại bao nhiêu lần cũng không sinh trùng:
1. Gán vai trò cho các tài khoản DEMO (mật khẩu = mã đăng nhập).
2. Khai 3 luồng: Đặt xe (TBP → Quản lý điều phối), Đặt xe giao hàng (TBP → Giám đốc →
   Quản lý điều phối, luồng có điều kiện), Duyệt dấu (TBP → Giám đốc duyệt dấu).
3. Phân văn thư DEGO cho công ty 1.
4. Bật công tắc bộ máy duyệt cho `vehicle_booking` và `seal_request`.
5. Tạo phiếu mẫu (mục đích bắt đầu bằng «[THỬ LUỒNG]») bằng đúng tầng dịch vụ.

Chạy trong container api:
    docker compose exec -T api python scripts/local_test/setup_flow_test_booking_seal.py

Từ chối chạy khi database không phải `dego-erp` (local), để không lỡ tay chạy lên dev/prod.
"""
import io
import sys

import app.core.all_models  # noqa: F401 — đăng ký toàn bộ mapper
from app.core.database import SessionLocal, engine
from app.modules.approval.flow_model import (APPROVER_DEPT_HEAD, APPROVER_EMPLOYEE,
                                             APPROVER_ROLE, MULTI_ANY,
                                             NODE_APPROVAL, NO_APPROVER_BLOCK, ROLE_APPROVE,
                                             ApprovalFlow, ApprovalNode, ApprovalSwitch)
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.role.model import Role
from app.modules.seal_clerk.model import CLERK_ACTIVE, SealClerk
from app.modules.seal_request import service as seal_service
from app.modules.seal_request.model import SealRequest
from app.modules.seal_request.schema import SealRequestCreate
from app.modules.user.model import User, UserRole
from app.modules.vehicle_booking import service as booking_service
from app.modules.vehicle_booking.model import TYPE_CAR, TYPE_DELIVERY, VehicleBooking
from app.modules.vehicle_booking.schema import VehicleBookingCreate
from app.core.storage import upload_fileobj

ALLOWED_DATABASE = "dego-erp"
MARK = "[THỬ LUỒNG]"
COMPANY_ID = 1

#  Tài khoản DEMO → vai trò cần thêm. Vai trò đã có thì giữ nguyên.
ROLE_GRANTS = {
    "TESTREQ": ["booking_requester"],                      # người tạo phiếu
    "DEMOTP": ["booking_requester", "seal_approver"],      # trưởng bộ phận phòng 17
    "DEMOQL": ["booking_manager", "seal_director", "seal_admin"],  # bước 2 của hai luồng
    "DEMOAD": ["booking_dispatcher"],                      # điều phối xe
    "TESTMEDEGO": ["seal_clerk"],                          # văn thư DEGO
    "DEMOTP3": ["booking_requester"],                      # đóng vai Giám đốc, cần quyền đọc
    "DEMONV": ["thu_cau_hinh_luong"],                      # đóng vai hành chính cấu hình luồng
}

#  Vai trò THỬ, chỉ dựng ở local: người được giao cấu hình luồng duyệt. Seed chưa có
#  vai trò nào riêng cho việc này — ngoài admin, ai có `approval_flow` thì cấu hình được.
CONFIG_ROLE = {
    "code": "thu_cau_hinh_luong",
    "name": "Cấu hình luồng duyệt (thử local)",
    "perms": {
        "approval_flow": ("all", ["read", "create", "write", "delete"]),
        "role": ("all", ["read"]),
        "employee": ("all", ["read"]),
        "department": ("all", ["read"]),
        "company": ("all", ["read"]),
        "seal_type": ("all", ["read"]),
    },
}

FLOWS = [
    {
        "entity": "vehicle_booking", "code": "THU-DX-2B",
        "name": "Đặt xe — Trưởng bộ phận rồi Quản lý điều phối (thử local)",
        "steps": [
            ("Trưởng bộ phận duyệt", APPROVER_DEPT_HEAD, ""),
            ("Quản lý điều phối duyệt", APPROVER_ROLE, "booking_manager"),
        ],
    },
    {
        #  Ca LỚN: luồng riêng có điều kiện, ưu tiên cao hơn nên được xét trước luồng
        #  mặc định. Phiếu đặt xe chưa có ô giá trị tài sản, nên mượn «giao hàng» làm
        #  ví dụ cho điều kiện. Giám đốc ở đây là tài khoản DEMOTP3 đóng vai.
        "entity": "vehicle_booking", "code": "THU-DX-3B",
        "name": "Đặt xe giao hàng — thêm Giám đốc duyệt (thử local)",
        "priority": 10,
        "condition": '[{"field": "request_type", "op": "eq", "value": 2}]',
        "steps": [
            ("Trưởng bộ phận duyệt", APPROVER_DEPT_HEAD, ""),
            ("Giám đốc duyệt", APPROVER_EMPLOYEE, "@DEMOTP3"),
            ("Quản lý điều phối duyệt", APPROVER_ROLE, "booking_manager"),
        ],
    },
    {
        "entity": "seal_request", "code": "THU-DD-2B",
        "name": "Duyệt dấu — Trưởng bộ phận rồi Giám đốc duyệt dấu (thử local)",
        "steps": [
            ("Trưởng bộ phận duyệt", APPROVER_DEPT_HEAD, ""),
            ("Giám đốc duyệt dấu", APPROVER_ROLE, "seal_director"),
        ],
    },
]

#  Bản PDF nhỏ nhất đọc được, làm «chứng từ có chữ ký sống» cho phiếu dấu.
TINY_PDF = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
            b"trailer<</Root 1 0 R>>\n%%EOF\n")


def find_user(db, code: str) -> User:
    from app.modules.employee.model import Employee

    row = (db.query(User).join(Employee, Employee.id == User.employee_id)
           .filter(Employee.code == code).order_by(User.id).first())
    if row is None:
        raise SystemExit(f"Không thấy tài khoản {code}")
    return row


def ensure_config_role(db) -> list[str]:
    from app.modules.role.model import Permission

    role = db.query(Role).filter(Role.code == CONFIG_ROLE["code"]).first()
    if role is not None:
        return []
    role = Role(code=CONFIG_ROLE["code"], name=CONFIG_ROLE["name"], created_by=0, updated_by=0)
    db.add(role)
    db.flush()
    for entity, (scope, actions) in CONFIG_ROLE["perms"].items():
        db.add(Permission(role_id=role.id, entity=entity, scope=scope,
                          can_read="read" in actions, can_create="create" in actions,
                          can_write="write" in actions, can_delete="delete" in actions))
    db.commit()
    return [f"vai trò {CONFIG_ROLE['code']}"]


def grant_roles(db) -> list[str]:
    done = []
    for code, role_codes in ROLE_GRANTS.items():
        user = find_user(db, code)
        for role_code in role_codes:
            role = db.query(Role).filter(Role.code == role_code).first()
            if role is None:
                raise SystemExit(f"Thiếu vai trò {role_code} — chạy seed trước")
            exists = db.query(UserRole).filter(UserRole.user_id == user.id,
                                               UserRole.role_id == role.id).first()
            if exists is None:
                db.add(UserRole(user_id=user.id, role_id=role.id, created_by=0, updated_by=0))
                done.append(f"{code} + {role_code}")
    db.commit()
    return done


def ensure_flows(db) -> list[str]:
    done = []
    for spec in FLOWS:
        flow = db.query(ApprovalFlow).filter(ApprovalFlow.entity == spec["entity"],
                                             ApprovalFlow.code == spec["code"]).first()
        if flow is not None:
            continue
        flow = ApprovalFlow(entity=spec["entity"], code=spec["code"], name=spec["name"],
                            description="Dựng bởi scripts/local_test — chỉ để thử.",
                            is_active=True, priority=spec.get("priority", 0),
                            condition=spec.get("condition", ""),
                            created_by=0, updated_by=0)
        db.add(flow)
        db.flush()
        for seq, (name, kind, ref) in enumerate(spec["steps"], start=1):
            if ref.startswith("@"):   # «@MÃ» = id hồ sơ nhân sự của tài khoản đó
                ref = str(find_user(db, ref[1:]).employee_id)
            db.add(ApprovalNode(flow_id=flow.id, seq=seq, branch_key="", name=name,
                                node_kind=NODE_APPROVAL, flow_role=ROLE_APPROVE,
                                approver_kind=kind, approver_ref=ref, multi_mode=MULTI_ANY,
                                on_no_approver=NO_APPROVER_BLOCK, created_by=0, updated_by=0))
        done.append(f"luồng {spec['code']} ({len(spec['steps'])} bước)")
    db.commit()
    return done


def ensure_switches(db) -> list[str]:
    done = []
    for entity in ("vehicle_booking", "seal_request"):
        row = db.query(ApprovalSwitch).filter(ApprovalSwitch.entity == entity).first()
        if row is None:
            db.add(ApprovalSwitch(entity=entity, is_enabled=True,
                                  note="Bật để thử local", created_by=0, updated_by=0))
            done.append(f"bật {entity}")
        elif not row.is_enabled:
            row.is_enabled = True
            done.append(f"bật lại {entity}")
    db.commit()
    return done


def ensure_clerk(db) -> list[str]:
    clerk_user = find_user(db, "TESTMEDEGO")
    exists = db.query(SealClerk).filter(SealClerk.employee_id == clerk_user.employee_id,
                                        SealClerk.company_id == COMPANY_ID).first()
    if exists is not None:
        return []
    db.add(SealClerk(employee_id=clerk_user.employee_id, company_id=COMPANY_ID,
                     is_head=False, status=CLERK_ACTIVE, created_by=0, updated_by=0))
    db.commit()
    return ["văn thư TESTMEDEGO cho công ty 1"]


def attach_pdf(db, req: SealRequest, actor_id: int) -> None:
    filename = f"chung-tu-thu-{req.id}.pdf"
    sf = StoredFile(filename=filename, file_key="", url="", content_type="application/pdf",
                    size=len(TINY_PDF), created_by=actor_id, updated_by=actor_id)
    db.add(sf)
    db.flush()
    key = f"local-test/seal/{sf.id}-{filename}"
    sf.file_key = key
    sf.url = upload_fileobj(io.BytesIO(TINY_PDF), key, "application/pdf")
    db.add(FileLink(file_id=sf.id, entity="seal_request", entity_id=req.id,
                    doc_type="signed_doc", created_by=actor_id, updated_by=actor_id))
    db.commit()


def create_samples(db) -> list[str]:
    already = (db.query(VehicleBooking).filter(VehicleBooking.purpose.like(f"{MARK}%")).count()
               + db.query(SealRequest).filter(SealRequest.purpose.like(f"{MARK}%")).count())
    if already:
        return [f"đã có {already} phiếu mẫu, không tạo thêm"]

    requester = find_user(db, "TESTREQ")
    approver = find_user(db, "DEMOTP")
    done = []

    bookings = [
        (True, dict(request_type=TYPE_CAR, purpose=f"{MARK} Đi gặp khách hàng ở Cần Thơ",
                    start_location="Văn phòng DEGO", end_location="KCN Trà Nóc",
                    start_time="2026-10-08T08:00", end_time="2026-10-08T12:00",
                    passenger_count=3, attendees="TESTREQ, DEMONV, DEMO_STAFF",
                    contact_phone="0900000001", is_round_trip=True)),
        (True, dict(request_type=TYPE_CAR, purpose=f"{MARK} Đưa đoàn kiểm tra nhà máy",
                    start_location="Văn phòng DEGO", end_location="Nhà máy Dego Organic",
                    start_time="2026-10-09T07:30", end_time="2026-10-09T17:00",
                    passenger_count=5, contact_phone="0900000002", is_round_trip=True)),
        (True, dict(request_type=TYPE_DELIVERY, purpose=f"{MARK} Giao mẫu phân bón cho đại lý",
                    start_location="Kho DEGO", end_location="Đại lý Phong Điền",
                    start_time="2026-10-10T09:00", end_time="2026-10-10T11:00",
                    goods_name="Mẫu phân bón 20 bao", goods_size="20 bao x 25kg",
                    sender_name="Kho DEGO", sender_phone="0900000003",
                    receiver_name="Đại lý Phong Điền", receiver_phone="0900000004")),
        (False, dict(request_type=TYPE_CAR, purpose=f"{MARK} Phiếu nháp để tự gửi duyệt",
                     start_location="Văn phòng DEGO", end_location="Sân bay Cần Thơ",
                     start_time="2026-10-12T05:00", end_time="2026-10-12T07:00",
                     passenger_count=1, contact_phone="0900000005")),
    ]
    for submit, values in bookings:
        data = VehicleBookingCreate(**values, company_id=COMPANY_ID, department_id=17,
                                    first_approver_id=approver.id)
        obj = booking_service.create_booking(db, data, requester, submit=submit)
        done.append(f"{obj.code} đặt xe {'đã gửi duyệt' if submit else 'nháp'}")

    seals = [
        (True, f"{MARK} Đóng dấu hợp đồng mua bán với đại lý"),
        (True, f"{MARK} Đóng dấu công văn gửi Sở Nông nghiệp"),
        (False, f"{MARK} Phiếu dấu nháp để tự gửi duyệt"),
    ]
    for submit, purpose in seals:
        data = SealRequestCreate(purpose=purpose, copies=2, company_ids=[COMPANY_ID],
                                 department_id=17, first_approver_id=approver.id)
        req = seal_service.create_seal_request(db, data, requester, submit=False)
        attach_pdf(db, req, requester.id)
        if submit:
            req = seal_service.submit_seal_request(db, req, requester)
        done.append(f"{req.code} duyệt dấu {'đã gửi duyệt' if submit else 'nháp, có tệp'}")
    return done


def main() -> None:
    if engine.url.database != ALLOWED_DATABASE:
        raise SystemExit(f"Từ chối: database là {engine.url.database!r}, chỉ chạy trên "
                         f"{ALLOWED_DATABASE!r} (local).")
    db = SessionLocal()
    try:
        for label, step in (("Vai trò thử", ensure_config_role), ("Vai trò", grant_roles), ("Luồng", ensure_flows),
                            ("Văn thư", ensure_clerk), ("Công tắc", ensure_switches),
                            ("Phiếu mẫu", create_samples)):
            result = step(db)
            print(f"{label}: {', '.join(result) if result else 'không đổi'}")
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
