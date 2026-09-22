"""Nạp dữ liệu mẫu cho phân hệ DUYỆT DẤU (Yêu cầu đóng dấu).

Tạo:
- Phân công Văn thư mẫu (tab_seal_clerk)
- Danh sách Yêu cầu đóng dấu mẫu (tab_seal_request + tab_seal_request_company) với đa dạng trạng thái:
  + Nháp (SEAL_DRAFT)
  + Chờ duyệt (SEAL_PENDING)
  + Đã duyệt - chờ đóng dấu (SEAL_APPROVED)
  + Hoàn thành (SEAL_COMPLETED)
  + Từ chối (SEAL_REJECTED)
  + Yêu cầu chỉnh sửa (SEAL_RETURNED)

Chạy (LOCAL/DEV): docker compose exec -T api python -m scripts.seed_seal_requests
"""
from datetime import datetime, timedelta

import app.core.all_models  # noqa: F401 — nạp toàn bộ model
from app.core.audit import record as audit_record
from app.core.database import SessionLocal
from app.modules.audit.model import AuditLog
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.seal_clerk.model import CLERK_ACTIVE, SealClerk
from app.modules.seal_request.model import (
    SEAL_APPROVED,
    SEAL_COMPLETED,
    SEAL_DRAFT,
    SEAL_PENDING,
    SEAL_REJECTED,
    SEAL_RETURNED,
    SealRequest,
    SealRequestCompany,
    SealType,
)
from app.modules.user.model import User

#  Câu nhật ký phải KHỚP `seal_request/controller.py::_with_reason` — màn chi tiết
#  moi lý do ra từ đúng chuỗi này (`frontend-v2/.../utils/extract-seal-reason.ts`).
#  Gõ khác một ký tự là phiếu mẫu mất lý do mà không có lỗi nào báo.
REASON_MARK = " — Lý do: "

#  Hai kết cục chặn, mỗi cái một câu mở đầu riêng (giống hệt controller).
STOP_ACTIONS = {
    SEAL_RETURNED: ("update", "Yêu cầu chỉnh sửa"),
    SEAL_REJECTED: ("cancel", "Từ chối yêu cầu"),
}


def _ghi_ly_do_chan(db, req, reason: str, actor_user_id: int) -> bool:
    """Ghi dấu vết LÝ DO bị trả về / từ chối cho một phiếu mẫu.

    ⚠️ Vì sao seed phải tự ghi dòng này: lý do KHÔNG có cột riêng trên phiếu —
    backend cố ý chỉ đặt nó trong câu nhật ký (`_with_reason`) và thư thông báo,
    còn `note` để dành cho chữ của người TẠO phiếu. Seed nào nhét lý do vào
    `note` là vừa sai chỗ, vừa làm màn chi tiết không có gì để hiện.

    Chạy lại được: đã có dòng mang dấu «— Lý do:» thì bỏ qua.
    """
    action, prefix = STOP_ACTIONS.get(req.status, ("", ""))
    if not action or not reason:
        return False

    da_co = (db.query(AuditLog)
             .filter(AuditLog.entity == "seal_request", AuditLog.entity_id == req.id,
                     AuditLog.message.like(f"%{REASON_MARK.strip()}%"))
             .first())
    if da_co:
        return False

    audit_record(db, actor_user_id, "seal_request", req.id, action,
                 f"{prefix}{REASON_MARK}{reason}", doc_code=req.code)
    return True


SAMPLE_REQUESTS = [
    {
        "code": "DD001",
        "title": "Hợp đồng mua bán thiết bị phòng lab",
        "purpose": "Đóng dấu Hợp đồng mua bán số 08/2026/HĐMB-DEGO với Công ty CP Thiết bị Khoa học Kỹ thuật",
        "companies": [1],  # DEGO HOLDING
        "copies": 3,
        "status": SEAL_COMPLETED,
        "days_ago": 18,
        "seal_type": "Dấu tròn công ty",
        "note": "Đã đóng dấu giáp lai và dấu tròn pháp nhân theo quy định.",
    },
    {
        "code": "DD002",
        "title": "Hồ sơ dự thầu gói hóa chất thí nghiệm",
        "purpose": "Đóng dấu Hồ sơ dự thầu Gói thầu số 02 - Hóa chất phân tích phục vụ dự án nông nghiệp công nghệ cao",
        "companies": [1, 3],  # DEGO HOLDING + HÓA CHẤT ABA
        "copies": 5,
        "status": SEAL_COMPLETED,
        "days_ago": 15,
        "seal_type": "Dấu tròn công ty",
        "note": "Hồ sơ gồm 5 bộ gốc, đã hoàn tất niêm phong.",
    },
    {
        "code": "DD003",
        "title": "Biên bản nghiệm thu dự án phần mềm",
        "purpose": "Đóng dấu Biên bản nghiệm thu và thanh lý Hợp đồng dịch vụ tư vấn chuyển đổi số số 15/2026/HĐDV",
        "companies": [1],
        "copies": 2,
        "status": SEAL_COMPLETED,
        "days_ago": 12,
        "seal_type": "Dấu tròn công ty",
        "note": "Đã bàn giao cho đối tác ngày 08/09.",
    },
    {
        "code": "DD004",
        "title": "Hợp đồng nguyên tắc phân phối dược phẩm",
        "purpose": "Đóng dấu Hợp đồng nguyên tắc phân phối sản phẩm thực phẩm bảo vệ sức khỏe khu vực miền Nam",
        "companies": [5],  # DƯỢC PHẨM ICARE
        "copies": 4,
        "status": SEAL_APPROVED,
        "days_ago": 3,
        "seal_type": "Dấu tròn công ty",
        "note": "Chờ đối tác ký trước khi văn thư dập dấu bản cuối.",
    },
    {
        "code": "DD005",
        "title": "Giấy ủy quyền ký kết phụ lục ngân hàng",
        "purpose": "Đóng dấu Giấy ủy quyền giao dịch ngân hàng số 22/2026/GUQ-IDA cho Phó Giám đốc",
        "companies": [2],  # IDA GLOBAL
        "copies": 2,
        "status": SEAL_APPROVED,
        "days_ago": 2,
        "seal_type": "Dấu chức danh",
        "note": "Văn bản ủy quyền phục vụ mở LC xuất khẩu.",
    },
    {
        "code": "DD006",
        "title": "Hợp đồng xuất khẩu nông sản đi Châu Âu",
        "purpose": "Đóng dấu Hợp đồng ngoại thương xuất khẩu lô hàng cà phê sạch 20 tấn sang thị trường Đức",
        "companies": [1, 2],  # DEGO + IDA GLOBAL
        "copies": 4,
        "status": SEAL_APPROVED,
        "days_ago": 1,
        "seal_type": "Dấu tròn công ty",
        "note": "Đã có chữ ký của Tổng Giám đốc trên bản cứng.",
    },
    {
        "code": "DD007",
        "title": "Thỏa thuận bảo mật thông tin (NDA)",
        "purpose": "Đóng dấu Thỏa thuận bảo mật thông tin đối tác công nghệ sinh học BioTech Singapore",
        "companies": [1],
        "copies": 2,
        "status": SEAL_PENDING,
        "days_ago": 1,
        "seal_type": "Dấu tròn công ty",
        "note": "Hồ sơ gấp cần hoàn thành trong ngày mai để kịp ký online.",
    },
    {
        "code": "DD008",
        "title": "Báo cáo tài chính quý 2 đã kiểm toán",
        "purpose": "Đóng dấu Báo cáo tài chính và báo cáo kiểm toán nộp Cục Thuế và Sở Kế hoạch Đầu tư",
        "companies": [1],
        "copies": 6,
        "status": SEAL_PENDING,
        "days_ago": 2,
        "seal_type": "Dấu giáp lai",
        "note": "Gồm 6 bộ tài liệu 45 trang, cần đóng dấu giáp lai toàn bộ.",
    },
    {
        "code": "DD009",
        "title": "Hợp đồng thuê văn phòng đại diện",
        "purpose": "Đóng dấu Hợp đồng thuê mặt bằng văn phòng chi nhánh Cần Thơ thời hạn 3 năm",
        "companies": [1],
        "copies": 3,
        "status": SEAL_PENDING,
        "days_ago": 0,
        "seal_type": "Dấu tròn công ty",
        "note": "Phòng Pháp chế đã thẩm định nội dung hợp đồng.",
    },
    {
        "code": "DD010",
        "title": "Quyết định bổ nhiệm Trưởng nhóm R&D",
        "purpose": "Đóng dấu Quyết định bổ nhiệm nhân sự số 45/QĐ-NS cho bà Nguyễn Thị Lan",
        "companies": [1],
        "copies": 2,
        "status": SEAL_PENDING,
        "days_ago": 0,
        "seal_type": "Dấu chức danh",
        "note": "Phòng Nhân sự trình Giám đốc phê duyệt.",
    },
    {
        "code": "DD011",
        "title": "Đơn đăng ký bảo hộ nhãn hiệu DEGO LAB",
        "purpose": "Đóng dấu Tờ khai đăng ký nhãn hiệu hàng hóa nộp Cục Sở hữu trí tuệ Việt Nam",
        "companies": [1],
        "copies": 3,
        "status": SEAL_RETURNED,
        "days_ago": 5,
        "seal_type": "Dấu tròn công ty",
        "note": "Hồ sơ gồm tờ khai và 3 mẫu nhãn in màu.",
        "stop_reason": "Bổ sung thêm mẫu nhãn hiệu màu và danh mục nhóm sản phẩm 05.",
    },
    {
        "code": "DD012",
        "title": "Đề xuất tạm ứng chi phí công tác nước ngoài",
        "purpose": "Đóng dấu Giấy đề nghị tạm ứng kinh phí đoàn công tác xúc tiến thương mại tại Thái Lan",
        "companies": [2],
        "copies": 1,
        "status": SEAL_REJECTED,
        "days_ago": 7,
        "seal_type": "Dấu chức danh",
        "note": "Đoàn 4 người, đi 5 ngày.",
        "stop_reason": "Chưa đính kèm thư mời chính thức của ban tổ chức hội chợ.",
    },
    {
        "code": "DD013",
        "title": "Phụ lục gia hạn hợp đồng cung cấp bao bì",
        "purpose": "Đóng dấu Phụ lục số 03 gia hạn hợp đồng cung cấp bao bì màng nhôm vụ mùa 2026-2027",
        "companies": [3],  # HÓA CHẤT ABA
        "copies": 2,
        "status": SEAL_DRAFT,
        "days_ago": 3,
        "seal_type": "Dấu tròn công ty",
        "note": "Bản thảo đang đối soát giá niêm yết mới.",
    },
    {
        "code": "DD014",
        "title": "Văn bản gửi Chi cục Quản lý thị trường",
        "purpose": "Đóng dấu Công văn giải trình nguồn gốc xuất xứ nguyên liệu nhập khẩu lô hàng số 778/HQ",
        "companies": [1, 2],
        "copies": 2,
        "status": SEAL_DRAFT,
        "days_ago": 1,
        "seal_type": "Dấu treo",
        "note": "Đang hoàn thiện phần phụ lục hải quan kèm theo.",
    },
    {
        "code": "DD015",
        "title": "Hồ sơ công bố tiêu chuẩn cơ sở phân bón vi sinh",
        "purpose": "Đóng dấu Bản tự công bố hợp chuẩn hợp quy cho dòng phân bón lá N2SBIO",
        "companies": [3],
        "copies": 4,
        "status": SEAL_COMPLETED,
        "days_ago": 25,
        "seal_type": "Dấu tròn công ty",
        "note": "Đã nhận kết quả tiếp nhận từ Sở Nông nghiệp.",
    },
]


def run():
    db = SessionLocal()
    try:
        now = datetime.now()

        # 1. Đảm bảo có SealType
        seal_type_map = {}
        for st in db.query(SealType).all():
            seal_type_map[st.name] = st.id

        if not seal_type_map:
            from scripts.seed_seal_types import run as seed_st
            seed_st()
            for st in db.query(SealType).all():
                seal_type_map[st.name] = st.id

        # 2. Lấy danh sách Company, User, Employee
        companies = {c.id: c for c in db.query(Company).all()}
        users = db.query(User).filter(User.is_active == True).all()  # noqa: E712
        if not users:
            print("Chưa có User nào trong hệ thống!")
            return

        # Tìm user admin / approver / nhân viên
        admin_user = users[0]
        # Approver: ưu tiên user có mã DEMOTP hoặc user thứ 2
        approver_user = next((u for u in users if getattr(u, "email", "") == "DEMOTP"), users[min(1, len(users) - 1)])
        # Clerk user: ưu tiên user thứ 3 hoặc 4
        clerk_user = users[min(2, len(users) - 1)]

        # 3. Phân công văn thư nếu chưa có
        if db.query(SealClerk).count() == 0:
            clerk_emp_id = getattr(clerk_user, "employee_id", 0)
            if clerk_emp_id:
                # Văn thư tổng
                db.add(SealClerk(
                    employee_id=clerk_emp_id,
                    company_id=1,
                    is_head=True,
                    status=CLERK_ACTIVE,
                ))
                # Văn thư công ty 2
                if 2 in companies:
                    db.add(SealClerk(
                        employee_id=clerk_emp_id,
                        company_id=2,
                        is_head=False,
                        status=CLERK_ACTIVE,
                    ))
                db.commit()
                print(f"  + Đã tạo phân công Văn thư mẫu cho nhân viên ID {clerk_emp_id}")

        # 4. Tạo SealRequests
        created_count = 0
        for item in SAMPLE_REQUESTS:
            code = item["code"]
            existing = db.query(SealRequest).filter(SealRequest.code == code).first()
            if existing:
                #  Phiếu cũ vẫn có thể THIẾU dấu vết lý do (bản seed trước nhét lý do
                #  vào `note`). Vá ngay ở đây thay vì bắt người ta xóa sạch CSDL.
                #  Bản seed cũ nhét lý do vào ô Ghi chú. Trả ô đó về đúng nghĩa —
                #  nhưng CHỈ khi nó còn y nguyên chữ của bản seed cũ, để không đè
                #  lên ghi chú ai đó đã sửa tay trên giao diện.
                if item.get("stop_reason") and existing.note.startswith(("Từ chối:", "TBP yêu cầu chỉnh sửa:")):
                    existing.note = item["note"]

                if _ghi_ly_do_chan(db, existing, item.get("stop_reason", ""), approver_user.id):
                    print(f"  ~ Vá dấu vết lý do cho phiếu: {code}")
                else:
                    print(f"  = Đã có phiếu: {code}")
                continue

            created_time = now - timedelta(days=item["days_ago"], hours=item.get("hours", 3))
            created_str = created_time.strftime("%Y-%m-%d %H:%M:%S")

            status = item["status"]
            approved_at_str = ""
            approved_by_id = 0
            completed_at_str = ""
            completed_by_id = 0

            if status in (SEAL_APPROVED, SEAL_COMPLETED):
                appr_time = created_time + timedelta(hours=4)
                approved_at_str = appr_time.strftime("%Y-%m-%d %H:%M")
                approved_by_id = approver_user.id

            if status == SEAL_COMPLETED:
                comp_time = created_time + timedelta(hours=8)
                completed_at_str = comp_time.strftime("%Y-%m-%d %H:%M")
                completed_by_id = clerk_user.id

            comp_ids = [cid for cid in item["companies"] if cid in companies] or [1]
            primary_comp_id = comp_ids[0]

            seal_type_id = seal_type_map.get(item["seal_type"], list(seal_type_map.values())[0] if seal_type_map else 1)

            # Chọn requester xoay vòng
            user_idx = created_count % len(users)
            u = users[user_idx]
            emp = db.get(Employee, u.employee_id) if u.employee_id else None
            requester_name = (emp.full_name if emp else None) or u.email or "Nhân viên"
            dept_id = (emp.department_id if emp else 0) or 0
            dept = db.get(Department, dept_id) if dept_id else None
            role_desc = " · ".join(x for x in [(emp.position if emp else ""), (dept.name if dept else "")] if x)

            req = SealRequest(
                code=code,
                title=item["title"],
                purpose=item["purpose"],
                seal_type_id=seal_type_id,
                company_id=primary_comp_id,
                department_id=dept_id,
                copies=item["copies"],
                requester=requester_name,
                requester_id=u.employee_id or 1,
                requester_email=u.email or "",
                requester_phone=getattr(emp, "phone", "") if emp else "",
                requester_role=role_desc or "Chuyên viên nghiệp vụ",
                first_approver_id=approver_user.id,
                approved_by=approved_by_id,
                approved_at=approved_at_str,
                completed_by=completed_by_id,
                completed_at=completed_at_str,
                status=status,
                note=item["note"],
                created_by=u.id,
                created_at=created_time,
                updated_at=created_time,
            )
            db.add(req)
            db.flush()

            # Gắn các công ty vào bảng nối tab_seal_request_company
            for cid in comp_ids:
                db.add(SealRequestCompany(seal_request_id=req.id, company_id=cid))

            #  Phiếu bị trả về / từ chối: ghi dấu vết lý do đúng như luồng thật.
            _ghi_ly_do_chan(db, req, item.get("stop_reason", ""), approver_user.id)

            created_count += 1
            print(f"  + Tạo yêu cầu đóng dấu: {code} - {item['title']} ({req.status_label})")

        db.commit()
        print(f"\nHoàn tất! Đã tạo thành công {created_count} phiếu đóng dấu mẫu.")

    finally:
        db.close()


if __name__ == "__main__":
    run()
