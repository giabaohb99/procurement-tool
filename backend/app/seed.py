"""Tạo bảng + seed dữ liệu khởi tạo (idempotent). Chạy: python -m app.seed

NGUYÊN TẮC: seed chạy TỰ ĐỘNG mỗi lần api khởi động (start.prod.sh / start.sh) nên nó chỉ được
THÊM dữ liệu còn thiếu, TUYỆT ĐỐI không ghi đè dữ liệu người dùng đã sửa (phân quyền vai trò,
danh mục, NCC...). Mọi khối ghi đè phải đặt sau cờ FORCE_SYNC (biến .env SEED_FORCE_SYNC).
"""
import json
import os

from app.core.auth import hash_password
from app.core.base_model import Base
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.permissions import ENTITIES

# Import tất cả model để metadata biết các bảng
from app.modules.attachment.model import FileLink, StoredFile  # noqa: F401
from app.modules.audit.model import AuditLog  # noqa: F401
from app.modules.catalog.model import (Brand, ItemGroup,  # noqa: F401
                                       Unit, Warehouse)
from app.modules.company.model import Company
from app.modules.department.model import Department, DepartmentCompany
from app.modules.doc_catalog.book_model import DocumentBook
from app.modules.doc_catalog.model import DocType, ExternalParty
from app.modules.doc_catalog.security_level_model import SecurityLevel
from app.modules.employee.model import Employee
from app.modules.product.model import Product
from app.modules.purchase_request.model import (PurchaseRequest,  # noqa: F401
                                                PurchaseRequestItem)
from app.modules.purchase_order.model import (PurchaseOrder,  # noqa: F401
                                              POItem, PODelivery)
from app.modules.goods_receipt.model import GoodsReceipt  # noqa: F401
from app.modules.inventory.model import Inventory, InventoryMove  # noqa: F401
from app.modules.payable.model import Payable  # noqa: F401
from app.modules.payment_request.model import (PaymentRequest,  # noqa: F401
                                               PaymentRequestLine)
from app.modules.role.model import Permission, Role
from app.modules.supplier.model import Supplier
from app.modules.survey.model import (Survey, SurveyProductLine,  # noqa: F401
                                      SurveySupplierLine)
from app.modules.user.model import User, UserRole
from app.seed_data.document_phase1 import (ALL_DOC_TYPES, DOC_TYPE_LINK_RULES,
                                          SECURITY_LEVELS,
                                           DEPARTMENT_DOCUMENT_CONFIG,
                                           DOCUMENT_COMPANIES)
from app.modules.notification.model import Notification, EmailLog  # noqa: F401


# Seed chạy MỖI LẦN api khởi động (start.prod.sh: alembic upgrade -> python -m app.seed -> uvicorn).
# Vì vậy seed CHỈ ĐƯỢC THÊM dữ liệu còn thiếu; mọi khối GHI ĐÈ dữ liệu đã có (ma trận quyền vai trò
# chuẩn, scope, hình thức thanh toán NCC) phải nằm sau cờ này, nếu không mỗi lần deploy sẽ xóa sạch
# phần admin chỉnh tay trên màn "Phân quyền".
# Bật 1 lần khi cố ý áp lại chuẩn: SEED_FORCE_SYNC=true trong .env -> restart api -> trả về false.
FORCE_SYNC = bool(getattr(settings, "SEED_FORCE_SYNC", False))


SAMPLE_COMPANIES = [
    ("DEGO", "CÔNG TY TNHH DEGO HOLDING", "1801722464"),
    ("IDA", "CÔNG TY TNHH XUẤT NHẬP KHẨU IDA GLOBAL", "0314562909"),
    ("ABA", "CÔNG TY TNHH SẢN XUẤT HÓA CHẤT ABA", "0316342296"),
]

SAMPLE_SUPPLIERS = [
    ("Cẩm Hùng", "CÔNG TY TNHH SẢN XUẤT THƯƠNG MẠI BAO BÌ CẨM HÙNG", "1801778241", "goods", "Công nợ 30 ngày", 0.08),
    ("Đông Tây", "CÔNG TY TNHH SẢN XUẤT BAO BÌ ĐÔNG TÂY", "0316254811", "goods", "Công nợ 30 ngày", 0.08),
    ("Mộc Ấn", "CÔNG TY TNHH QUẢNG CÁO MỘC ẤN", "0312214688", "goods", "Công nợ 30 ngày", 0.10),
    ("Mekong Logistics", "Mekong Logistics", "", "transport", "Công nợ 30 ngày", 0.08),
    ("Sang Giàu", "Vận chuyển Sang Giàu", "", "transport", "Công nợ 30 ngày", 0.0),
]

# Phòng ban mẫu (mã theo quy ước generate_code prefix "PBA": PBA001, PBA002…).
# Trưởng bộ phận để trống — gán trên UI vì phụ thuộc danh sách nhân sự thật.
SAMPLE_DEPARTMENTS = [
    ("PBA001", "Phòng Thu mua"),
    ("PBA002", "Phòng Kế toán"),
    ("PBA003", "Phòng Kinh doanh"),
    ("PBA004", "Phòng Kho vận"),
    ("PBA005", "Phòng Sản xuất"),
    ("PBA006", "Phòng Marketing"),
    ("PBA007", "Phòng Nhân sự - Hành chính"),
    ("PBA008", "Phòng Công nghệ thông tin"),
    ("PBA009", "Ban Giám đốc"),
]

# Phân công NSTM phụ trách theo phân loại VTBB — dữ liệu MẪU để thử màn
# /category-assignees (chỉ nạp khi bảng còn rỗng, xem seed_category_assignees).
# Tham chiếu bằng TÊN phân loại + MÃ nhân sự vì id khác nhau giữa các môi trường.
# Dự phòng để "" = phân loại đó chỉ có NSTM chính (chủ ý, để test cả 2 trường hợp).
SAMPLE_CATEGORY_ASSIGNEES = [
    # Nhóm chai / nắp / can — NSTM chính là nhân viên thu mua
    ("Chai Pet", "DEMO_PURCHASER", "DEMO_MANAGER_PURCHASE"),
    ("Chai Hdpe", "DEMO_PURCHASER", "DEMO_MANAGER_PURCHASE"),
    ("Chai Nhôm", "DEMO_PURCHASER", ""),
    ("Nắp Pet", "DEMO_PURCHASER", "DEMO_MANAGER_PURCHASE"),
    ("Nắp Hdpe", "DEMO_PURCHASER", ""),
    # Nhóm nhãn / tem — trưởng phòng thu mua ôm chính, nhân viên dự phòng
    ("Nhãn giấy", "DEMO_MANAGER_PURCHASE", "DEMO_PURCHASER"),
    ("Nhãn Decal", "DEMO_MANAGER_PURCHASE", "DEMO_PURCHASER"),
    ("Tem chống hàng giả", "DEMO_MANAGER_PURCHASE", ""),
    # Nhóm thùng / hộp carton
    ("Thùng carton 3 lớp", "DEMO_PURCHASER", "DEMO_MANAGER_PURCHASE"),
    ("Thùng carton 5 lớp", "DEMO_PURCHASER", "DEMO_MANAGER_PURCHASE"),
    ("Hộp carton 3 lớp", "DEMO_MANAGER_PURCHASE", ""),
    # Nhóm túi / màng / băng keo
    ("Túi PE (Túi nilong)", "DEMO_PURCHASER", "DEMO_MANAGER_PURCHASE"),
    ("Màng PE cuộn", "DEMO_PURCHASER", ""),
    ("Băng keo trong", "DEMO_MANAGER_PURCHASE", "DEMO_PURCHASER"),
    ("Vận chuyển", "DEMO_MANAGER_PURCHASE", ""),
]

SAMPLE_PRODUCTS = [
    ("THI0002", "Thùng IDA Chai Pet Vuông 35 450ml-500ml - Xanh lá", "Thùng", "Cái"),
    ("THC0003", "Thùng DC Chai Pet Vuông 35 450ml-500ml - Trắng viền đen", "Thùng", "Cái"),
    ("THC0004", "Thùng DC Chai Pet Tròn 43 450ml-500ml - Trắng", "Thùng", "Cái"),
    ("NL0001", "Nguyên liệu Vi lượng AV4", "Nguyên liệu", "Kg"),
]


def seed_demo_accounts(db, company_id):
    from app.modules.role.model import Role, Permission
    from app.modules.user.model import User, UserRole
    from app.modules.employee.model import Employee
    from app.core.auth import hash_password
    
    # Mapping tài khoản demo với vai trò chuẩn trong STD_ROLES
    demo_role_map = {
        "staff": "employee",                # DEMO_STAFF / staff@demo.com -> Nhân sự (chỉ tạo YCMH, KHÔNG xem ĐMH hay Báo cáo)
        "manager": "dept_head",              # DEMO_MANAGER / manager@demo.com -> Trưởng phòng (duyệt YCMH/YCBG)
        "purchaser": "pur_staff",            # DEMO_PURCHASER / purchaser@demo.com -> Nhân viên thu mua
        "manager_purchase": "pur_manager",  # DEMO_MANAGER_PURCHASE / manager_purchase@demo.com -> Quản lý thu mua
    }

    from app.core.auth import perm_cache_clear

    for code, role_code in demo_role_map.items():
        role = db.query(Role).filter(Role.code == role_code).first()
        if not role:
            continue

        emp_code = f"DEMO_{code.upper()}"
        emp = db.query(Employee).filter(Employee.code == emp_code).first()
        if not emp:
            emp = Employee(code=emp_code, full_name=role.name, company_id=company_id, position=role.name, is_active=True)
            db.add(emp)
            db.commit()
            db.refresh(emp)

        # Cập nhật tất cả tài khoản User liên kết với Employee demo này (cả dạng email staff@demo.com và DEMO_STAFF)
        users = db.query(User).filter((User.employee_id == emp.id) | (User.email == email) | (User.email == emp_code)).all() if (email := f"{code}@demo.com") else []
        for u in users:
            u.password_hash = hash_password("demo123")
            u.is_active = True
            db.commit()
            db.query(UserRole).filter(UserRole.user_id == u.id).delete()
            db.add(UserRole(user_id=u.id, role_id=role.id))
            db.commit()
            perm_cache_clear(u.id)

    # Đồng bộ mật khẩu các tài khoản test chuẩn (TESTREQ, DEMONV, DEMOTP, DEMOQL, DEMOAD, DEMOTP2, DEMOTP3)
    test_codes = ["TESTREQ", "DEMONV", "DEMOTP", "DEMOQL", "DEMOAD", "DEMOTP2", "DEMOTP3"]
    for tcode in test_codes:
        temp = db.query(Employee).filter(Employee.code == tcode).first()
        if temp:
            tuser = (db.query(User).filter(User.employee_id == temp.id).first()
                     or db.query(User).filter(User.email == tcode).first())
            if tuser:
                tuser.password_hash = hash_password(tcode)
                tuser.is_active = True
                db.commit()


# Vai trò chuẩn theo phân quyền DEGO. Mỗi entity: (danh sách hành động, phạm vi).
# Phạm vi: own | dept | company | all. Xem doc/Thiet_Ke_Phan_Quyen.md.
# employee KHÔNG nằm ở đây: danh sách nhân sự phải giới hạn theo phạm vi từng vai trò
# (phòng ban của mình) — cấu hình riêng bên dưới.
_CATALOG_READ = {e: (["read"], "all") for e in
                 ["supplier", "product", "warehouse", "unit", "item_group", "department", "company"]}

# "Cụm danh mục" — Admin thu mua được toàn quyền thêm/sửa/xóa
_CATALOG_CRUD = {e: (["read", "create", "write", "delete"], "all") for e in
                 ["supplier", "product", "warehouse", "unit", "item_group",
                  "brand", "company", "category_assignee"]}

# CR-117 — HỢP ĐỒNG KHÔNG phải danh mục dùng chung như ĐVT hay Kho: mỗi hợp đồng đứng tên
# MỘT pháp nhân (`company_id`), nên phạm vi mặc định là 'company' chứ không phải 'all'.
# Chỉ `pur_manager` và `admin` giữ 'all' (xem cả tập đoàn).
# ⚠️ Dòng này chỉ áp cho CÀI MỚI. Môi trường đang chạy giữ nguyên phân quyền trên DB
# (D-018) — muốn áp lại phải đặt SEED_FORCE_SYNC=true một lần, hoặc sửa tay ở màn Phân quyền.
_CONTRACT_READ = {"contract": (["read"], "company")}
_CONTRACT_CRUD = {"contract": (["read", "create", "write", "delete"], "company")}

# Quản lý thu mua = toàn quyền như quản trị NGHIỆP VỤ: mọi entity TRỪ quản trị hệ thống
# (user/role/setting) — full 8 hành động, phạm vi 'all'.
_ALL_ACTIONS = ["read", "create", "write", "delete", "approve", "cancel", "print", "export"]
# help_article nằm ở đây để nghiệp vụ thu mua KHÔNG tự động sửa được tài liệu HDSD —
# quyền này chỉ cấp cho admin hệ thống và vai trò 'help_admin'.
# `mailbox` cũng ở đây (26/08/2026): bảng hộp thư giữ MẬT KHẨU ỨNG DỤNG của các
# địa chỉ gửi thật, và ai sửa được nó thì cấp được cho mình quyền gửi thư danh
# nghĩa cả một phòng ban. Đó là việc của quản trị hệ thống, không phải của nghiệp
# vụ thu mua — mà `_PUR_MANAGER_PERMS` dưới đây cấp TẤT CẢ những gì không nằm
# trong tập này.
_SYS_ENTITIES = {"user", "role", "setting", "backup", "help_article", "mailbox"}
_PUR_MANAGER_PERMS = {e: (_ALL_ACTIONS, "all") for e in ENTITIES if e not in _SYS_ENTITIES}

STD_ROLES = {
    "employee": {"name": "Nhân sự", "perms": {
        # chỉ các danh mục cần cho form tạo yêu cầu (không có Hợp đồng/NCC)
        "product": (["read"], "all"), "unit": (["read"], "all"),
        "item_group": (["read"], "all"), "warehouse": (["read"], "all"),
        "department": (["read"], "all"), "company": (["read"], "all"),
        # CR-068: KHÔNG cấp 'export' (xuất Excel) cho nhân sự yêu cầu thường — khách chốt: ai được
        # xuất báo cáo thì gán thêm một vai trò riêng tự tạo, tick ô "Xuất" ở màn Phân quyền.
        "purchase_request": (["read", "create"], "own"),
        "survey_request": (["read", "create", "write"], "own"),
        "ticket": (["read", "create", "write"], "own"),
    }},
    "dept_head": {"name": "Trưởng phòng (duyệt PYC)", "perms": {
        **_CATALOG_READ, **_CONTRACT_READ,
        "employee": (["read"], "dept"),
        "purchase_request": (["read", "approve", "export"], "dept"),
        "survey_request": (["read", "approve", "export"], "dept"),
        "ticket": (["read", "create", "write"], "own"),
        "report": (["read"], "dept"),
    }},
    "company_head": {"name": "Quản lý công ty", "perms": {
        **_CATALOG_READ, **_CONTRACT_READ,
        "employee": (["read"], "company"),
        "purchase_request": (["read", "export"], "company"),
        "purchase_order": (["read", "export"], "company"),
        "ticket": (["read", "create", "write"], "own"),
        "report": (["read"], "company"),
        "assistant": (["read"], "all"),   # Trợ lý AI — vai trò lãnh đạo
    }},
    "pur_staff": {"name": "Nhân viên thu mua", "perms": {
        **_CATALOG_READ, **_CONTRACT_READ,
        "employee": (["read"], "dept"),
        "purchase_request": (["read", "create", "write", "export"], "assigned"),
        "survey_request": (["read", "write", "export"], "proc"),
        "ticket": (["read", "create", "write"], "own"),
        "survey": (["read", "create", "write"], "all"),
        "purchase_order": (["read", "create", "write", "delete", "print", "export"], "assigned"),   # chỉ đơn mình tạo/NSPT là mình; xóa được đơn NHÁP của mình
        "inventory": (["read"], "company"),
        "payable": (["read"], "company"),
        "payment_request": (["read", "create", "write", "print"], "company"),
        "report": (["read"], "company"),
    }},
    # Quản lý thu mua: toàn quyền nghiệp vụ (như admin, trừ quản trị hệ thống user/role/setting)
    "pur_manager": {"name": "Quản lý thu mua", "perms": _PUR_MANAGER_PERMS},
    # Admin thu mua: CRUD toàn bộ danh mục; nghiệp vụ CHỈ ĐỌC.
    # PYC/YCKS phạm vi 'proc' (chỉ thấy chứng từ đã duyệt); ĐMH phạm vi 'all'
    # (thấy + IN MỌI đơn của phòng kể cả nháp/chờ duyệt — KHÔNG duyệt).
    "pur_admin": {"name": "Admin thu mua", "perms": {
        **_CATALOG_CRUD, **_CONTRACT_CRUD,
        "department": (["read"], "all"),
        "employee": (["read"], "all"),
        # CR-034: 'approve' ở đây KHÔNG phải duyệt thay trưởng phòng (phạm vi 'proc' không thấy
        # phiếu Chờ duyệt) — nó mở nút DUYỆT ĐIỀU PHỐI + phân bổ NSTM cho Admin thu mua.
        # Dòng này chỉ áp cho cài mới; môi trường đang chạy được vá bằng migration d2e6f4b81a37
        # (D-018: seed không ghi đè phân quyền trên DB thật).
        "purchase_request": (["read", "approve", "export"], "proc"),
        "survey_request": (["read", "export"], "proc"),
        "ticket": (["read", "create", "write"], "own"),
        "purchase_order": (["read", "print", "export"], "all"),
        "survey": (["read", "create", "write", "delete", "approve"], "all"),   # Admin TM thao tác được phiếu khảo sát
        "import": (["read", "create", "delete"], "all"),   # nạp data cũ + hoàn tác
        "goods_receipt": (["read"], "all"),
        "inventory": (["read"], "all"),
        "payable": (["read"], "all"),
        "payment_request": (["read"], "all"),
        "report": (["read", "export"], "all"),
    }},
    # Quản trị Trung tâm Hướng dẫn sử dụng (app help-center chạy riêng, cổng 8082).
    # CHỈ có quyền trên tài liệu HDSD — không đụng tới nghiệp vụ / cấu hình hệ thống.
    "help_admin": {"name": "Quản trị Hướng dẫn sử dụng", "perms": {
        "help_article": (["read", "create", "write", "delete"], "all"),
    }},
    # Nhóm Hỗ trợ: xử lý tập trung MỌI phiếu hỗ trợ (đọc/trả lời/đổi trạng thái/đóng), phạm vi all.
    "support": {"name": "Nhân viên hỗ trợ", "perms": {
        "ticket": (["read", "create", "write", "delete"], "all"),
    }},
    # ── Hai vai trò MẪU cho phân hệ Văn bản (24/08/2026) ─────────────────────
    #
    # Chúng trả lời đúng hai câu hay bị hỏi nhất: "nhân viên chỉ được XEM văn
    # bản" và "được SỬA nhưng không được XÓA". Khai sẵn ở đây để mọi môi trường
    # có mẫu bấm-là-dùng, thay vì mỗi người tự tick lại 8 ô từ đầu và mỗi nơi
    # tick một kiểu. Không tài khoản nào bị gán tự động — việc gán làm ở màn
    # *Nhân sự ▸ Phân quyền tài khoản ▸ tab Người dùng*.
    #
    # ⚠️ MẤY entity đọc kèm không phải thừa: thiếu chúng thì form Tạo/Sửa văn bản
    # rỗng sạch mọi ô bắt buộc (loại · pháp nhân · phòng · người chịu trách
    # nhiệm) và không lưu nổi — đã bị đúng lỗi đó với vai trò `vanthu_cty`.
    #
    # `security_level` là cái dễ quên nhất vì ô của nó nằm tận BƯỚC 3: thiếu nó
    # thì `/api/security-levels` trả 403, ô «Mức mật» rỗng danh sách, và form
    # gửi lên `secrecy_level = 0` → `422` báo lỗi ở một ô người dùng chưa hề mở
    # tới (dựng lại được 24/08/2026 với tài khoản DEMOTP).
    "vanban_xem": {"name": "Văn bản — chỉ xem", "perms": {
        #  ĐÚNG một hành động. Không `print`, không `export`: "không thao tác gì"
        #  thì cũng không mang văn bản ra ngoài được.
        "document": (["read"], "company"),
        "doc_type": (["read"], "all"),
        "document_book": (["read"], "all"),
        "security_level": (["read"], "all"),
        "company": (["read"], "all"),
        "department": (["read"], "all"),
        "employee": (["read"], "all"),
    }},
    "vanban_sua": {"name": "Văn bản — soạn & sửa (không xóa, không duyệt)", "perms": {
        #  Cố ý KHÔNG có `delete`, `approve`, `cancel`: soạn được, sửa được, gửi
        #  duyệt được (gửi duyệt tính là `write`), nhưng không tự duyệt bài của
        #  mình, không xóa, không bãi bỏ văn bản đã ban hành.
        "document": (["read", "create", "write", "print", "export"], "company"),
        "doc_type": (["read"], "all"),
        #  Người SOẠN phải đọc được thư viện mẫu — ô «Dùng mẫu» ở bước 1 của màn
        #  Tạo văn bản gọi `/api/document-templates`. Từ CR-157 nó có khóa riêng
        #  (`doc_template`) nên không còn đi kèm `doc_type` nữa; thiếu dòng này
        #  là ô mẫu rỗng và người soạn ăn toast 403 ngay lúc mở màn.
        "doc_template": (["read"], "all"),
        "document_book": (["read"], "all"),
        "security_level": (["read"], "all"),
        "company": (["read"], "all"),
        "department": (["read"], "all"),
        "employee": (["read"], "all"),
    }},
}


def seed_standard_roles(db):
    """Tạo các vai trò chuẩn + ma trận quyền. Không tạo user; gán cho nhân sự ở màn Phân quyền.

    QUAN TRỌNG — seed chạy MỖI LẦN khởi động container (start.prod.sh), nên ma trận quyền chỉ
    được nạp cho vai trò VỪA ĐƯỢC TẠO. Vai trò đã tồn tại thì GIỮ NGUYÊN quyền trên DB: người
    quản trị sửa gì ở màn "Phân quyền" thì lần deploy sau vẫn còn.
    Muốn áp lại đúng theo STD_ROLES: đặt SEED_FORCE_SYNC=true trong .env, restart api, rồi tắt.
    """
    for code, info in STD_ROLES.items():
        role = db.query(Role).filter(Role.code == code).first()
        is_new = role is None
        if is_new:
            role = Role(code=code, name=info["name"])
            db.add(role)
            db.commit()
            db.refresh(role)
        if not is_new and not FORCE_SYNC:
            continue   # vai trò đã có trên DB -> KHÔNG đụng vào quyền đã chỉnh tay
        existing = {p.entity for p in db.query(Permission).filter(Permission.role_id == role.id).all()}
        for entity, (actions, scope) in info["perms"].items():
            if entity in existing:
                continue
            db.add(Permission(
                role_id=role.id, entity=entity, scope=scope,
                can_read="read" in actions, can_create="create" in actions,
                can_write="write" in actions, can_delete="delete" in actions,
                can_approve="approve" in actions, can_cancel="cancel" in actions,
                can_print="print" in actions, can_export="export" in actions,
            ))
        db.commit()

    if not FORCE_SYNC:
        return   # phần dưới GHI ĐÈ scope trên DB — chỉ chạy khi cố ý đồng bộ lại

    # Ép scope PYC theo mô hình mới: NV thu mua = 'assigned' (chỉ phiếu của mình / được gán,
    # KHÔNG thấy mọi phiếu đã duyệt — khớp tài liệu); Admin thu mua giữ 'proc'.
    for role_code, scope in [("pur_staff", "assigned"), ("pur_admin", "proc")]:
        role = db.query(Role).filter(Role.code == role_code).first()
        if role:
            db.query(Permission).filter(
                Permission.role_id == role.id, Permission.entity == "purchase_request"
            ).update({"scope": scope}, synchronize_session=False)
    # ĐMH: NV thu mua chỉ thấy đơn mình tạo / NSPT là mình (assigned), giống YCMH — áp cả DB cũ
    _ps = db.query(Role).filter(Role.code == "pur_staff").first()
    if _ps:
        db.query(Permission).filter(
            Permission.role_id == _ps.id, Permission.entity == "purchase_order"
        ).update({"scope": "assigned", "can_delete": True}, synchronize_session=False)  # xóa được đơn NHÁP của mình
    db.commit()


def resync_role_perms(db, code: str, perms: dict):
    """Ghi ĐÈ toàn bộ ma trận quyền của 1 vai trò theo `perms` (xóa cũ → tạo lại).

    NGUY HIỂM: xóa sạch phân quyền admin đã chỉnh trên UI. CHỈ gọi trong nhánh FORCE_SYNC."""
    role = db.query(Role).filter(Role.code == code).first()
    if not role:
        return
    db.query(Permission).filter(Permission.role_id == role.id).delete(synchronize_session=False)
    for entity, (actions, scope) in perms.items():
        db.add(Permission(
            role_id=role.id, entity=entity, scope=scope,
            can_read="read" in actions, can_create="create" in actions,
            can_write="write" in actions, can_delete="delete" in actions,
            can_approve="approve" in actions, can_cancel="cancel" in actions,
            can_print="print" in actions, can_export="export" in actions,
        ))
    db.commit()


def seed_help_admin(db, company_id):
    """Tài khoản quản trị riêng cho app Help Center (idempotent).

    Đăng nhập bằng mã nhân viên HDSD0001 hoặc username 'helpadmin'.
    Mật khẩu mặc định 'helpadmin' — đổi qua biến môi trường HELP_ADMIN_PASSWORD.
    """
    role = db.query(Role).filter(Role.code == "help_admin").first()
    if not role:
        return  # seed_standard_roles chưa chạy — không nên xảy ra

    emp = db.query(Employee).filter(Employee.code == "HDSD0001").first()
    if not emp:
        emp = Employee(code="HDSD0001", full_name="Quản trị Hướng dẫn sử dụng",
                       company_id=company_id, position="Quản trị HDSD", is_active=True)
        db.add(emp)
        db.commit()
        db.refresh(emp)

    user = db.query(User).filter(User.employee_id == emp.id).first()
    if not user:
        user = User(email="helpadmin", employee_id=emp.id,
                    password_hash=hash_password(os.getenv("HELP_ADMIN_PASSWORD", "helpadmin")),
                    is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    if not db.query(UserRole).filter(UserRole.user_id == user.id,
                                     UserRole.role_id == role.id).first():
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()
    print("Help Center admin: helpadmin (hoặc HDSD0001)")


_HOME_SECTIONS = [
    ("quick_start", "Bắt đầu ngay", 0),
    ("categories", "Các Phân hệ", 1),
    ("faq", "Không tìm thấy điều bạn cần?", 2),
    ("tips", "Mẹo tra cứu", 3),
]


def seed_help_home_sections(db):
    """4 khung cấu hình trang chủ Help Center (idempotent — chỉ tạo nếu chưa có `key` đó,
    KHÔNG ghi đè title mà người dùng đã tự sửa qua trang quản trị)."""
    from app.modules.help_center.model import HelpHomeSection

    existing = {s.key for s in db.query(HelpHomeSection).all()}
    for key, title, sort_order in _HOME_SECTIONS:
        if key not in existing:
            db.add(HelpHomeSection(key=key, title=title, is_visible=True, sort_order=sort_order))
    db.commit()


def seed_category_assignees(db):
    """Nạp phân công NSTM mẫu (SAMPLE_CATEGORY_ASSIGNEES) — CHỈ khi bảng còn RỖNG.

    Giống phòng ban mẫu: seed chạy lại mỗi lần khởi động, nên nếu nạp vô điều kiện thì
    mỗi lần deploy sẽ dựng lại đúng những dòng người dùng vừa xóa trên UI.

    Bỏ qua dòng nào không tìm thấy phân loại/nhân sự tương ứng (môi trường khác có thể
    chưa nạp danh mục đó, hoặc đã tắt tài khoản demo bằng SEED_DEMO_ACCOUNTS=false).
    """
    from app.modules.category_assignee.model import CategoryAssignee

    if db.query(CategoryAssignee).count():
        return 0

    groups = {g.name.strip().upper(): g.id for g in db.query(ItemGroup).all() if g.name}
    emps = {e.code.strip().upper(): e.id for e in db.query(Employee).all() if e.code}
    n = 0
    for group_name, primary_code, backup_code in SAMPLE_CATEGORY_ASSIGNEES:
        gid = groups.get(group_name.upper())
        pid = emps.get(primary_code.upper())
        if not gid or not pid:
            continue
        db.add(CategoryAssignee(item_group_id=gid, primary_employee_id=pid,
                                backup_employee_id=emps.get(backup_code.upper(), 0) if backup_code else 0))
        n += 1
    db.commit()
    return n


def cleanup_legacy_staff_role(db):
    """Gộp vai trò legacy 'Nhân viên' (code STAFF) vào 'Nhân sự' (code employee) rồi XÓA.
    Idempotent: chỉ chạy khi vẫn còn vai trò STAFF."""
    staff = db.query(Role).filter(Role.code == "STAFF").first()
    if not staff:
        return
    emp_role = db.query(Role).filter(Role.code == "employee").first()
    if emp_role:
        # 1) Nhân sự để role_name = tên STAFF → đổi sang tên 'Nhân sự'
        db.query(Employee).filter(Employee.role_name == staff.name).update(
            {"role_name": emp_role.name}, synchronize_session=False)
        # 2) Tài khoản đang gán vai trò STAFF → chuyển sang vai trò employee (khỏi mất quyền)
        staff_uids = [ur.user_id for ur in db.query(UserRole).filter(UserRole.role_id == staff.id).all()]
        for uid in staff_uids:
            if db.query(UserRole).filter(UserRole.user_id == uid, UserRole.role_id == emp_role.id).first():
                db.query(UserRole).filter(UserRole.user_id == uid, UserRole.role_id == staff.id).delete(
                    synchronize_session=False)   # đã có vai trò employee → chỉ bỏ gán STAFF
            else:
                db.query(UserRole).filter(UserRole.user_id == uid, UserRole.role_id == staff.id).update(
                    {"role_id": emp_role.id}, synchronize_session=False)
    # 3) Dọn quyền + scope + gán còn sót của STAFF rồi xóa vai trò
    from app.modules.user.model import UserScope
    db.query(Permission).filter(Permission.role_id == staff.id).delete(synchronize_session=False)
    db.query(UserScope).filter(UserScope.role_id == staff.id).delete(synchronize_session=False)
    db.query(UserRole).filter(UserRole.role_id == staff.id).delete(synchronize_session=False)
    db.delete(staff)
    db.commit()


def assign_default_roles(db):
    """Tài khoản nào CHƯA có vai trò → gán 'Nhân sự' (employee) để ai cũng tạo/xem PYC của mình.
    Không đụng tài khoản đã có vai trò (admin, đã gán tay...)."""
    emp_role = db.query(Role).filter(Role.code == "employee").first()
    if not emp_role:
        return 0
    assigned = {ur.user_id for ur in db.query(UserRole).all()}
    n = 0
    for u in db.query(User).all():
        if u.id not in assigned:
            db.add(UserRole(user_id=u.id, role_id=emp_role.id))
            n += 1
    if n:
        db.commit()
    return n


def ensure_admin_role(db):
    """Vai trò 'admin' (quản trị hệ thống) + quyền đầy đủ cho MỌI entity.

    CỐ Ý chạy mỗi lần khởi động: đây là vai trò "chìa khóa dự phòng" — không được để phân hệ mới
    ra đời mà admin hệ thống không vào được. Chỉ THÊM entity còn thiếu, KHÔNG sửa dòng có sẵn."""
    admin_role = db.query(Role).filter(Role.code == "admin").first()
    if not admin_role:
        admin_role = Role(code="admin", name="Quản trị hệ thống")
        db.add(admin_role)
        db.commit()
        db.refresh(admin_role)

    for _ar in db.query(Role).filter(Role.code.in_(["admin", "ADMINISTRATOR"])).all():
        existing = {p.entity for p in db.query(Permission).filter(Permission.role_id == _ar.id).all()}
        for entity in ENTITIES:
            if entity not in existing:
                db.add(Permission(
                     role_id=_ar.id, entity=entity, can_read=True, can_create=True,
                     can_write=True, can_delete=True, can_approve=True, can_cancel=True,
                     can_print=True, can_export=True, scope="all",
                ))
    db.commit()
    return admin_role


def force_resync_roles(db):
    """GHI ĐÈ phân quyền các vai trò chuẩn về đúng STD_ROLES (chỉ chạy khi SEED_FORCE_SYNC=true).

    Gồm các bản vá dữ liệu một lần cho DB seed từ đời trước; đã áp xong ở local/dev/prod.
    Mặc định KHÔNG chạy để deploy không xóa phân quyền admin chỉnh tay trên màn "Phân quyền"."""
    if not FORCE_SYNC:
        return
    # Bổ sung can_cancel cho các vai trò quản trị (admin, ADMINISTRATOR) tạo trước khi có action 'cancel'
    admin_role_ids = [r.id for r in db.query(Role).filter(Role.code.in_(["admin", "ADMINISTRATOR"])).all()]
    if admin_role_ids:
        db.query(Permission).filter(Permission.role_id.in_(admin_role_ids), Permission.can_cancel == False).update({"can_cancel": True}, synchronize_session=False)
    # QL thu mua "Ghi nhận đã chi" (pay) cần quyền write trên payment_request — áp cả DB đã seed trước đây
    _pm = db.query(Role).filter(Role.code == "pur_manager").first()
    if _pm:
        db.query(Permission).filter(
            Permission.role_id == _pm.id, Permission.entity == "payment_request"
        ).update({"can_write": True}, synchronize_session=False)
    db.commit()

    # Sửa phạm vi employee-read cho các vai trò đã seed trước đây (khi còn để "all").
    # Danh sách nhân sự phải giới hạn theo phòng ban/công ty của người xem.
    _EMP_READ_SCOPE = {"dept_head": "dept", "company_head": "company",
                       "pur_staff": "dept"}   # pur_manager giờ full (như admin) — không giới hạn employee
    for rcode, sc in _EMP_READ_SCOPE.items():
        r = db.query(Role).filter(Role.code == rcode).first()
        if r:
            db.query(Permission).filter(
                Permission.role_id == r.id, Permission.entity == "employee",
                Permission.scope == "all",
            ).update({"scope": sc}, synchronize_session=False)
    db.commit()

    # CR-117: hạ phạm vi HỢP ĐỒNG từ 'all' về 'company' cho các vai trò không phải quản lý.
    # Trước CR-117 entity `contract` không có trong SCOPE_FIELDS nên phạm vi ghi gì cũng
    # KHÔNG lọc — mọi DB đang chạy đều để 'all' vì nó vô hại. Nay bộ lọc ăn thật, phải áp lại.
    # Chỉ hạ dòng đang là 'all'; vai trò nào đã được chỉnh tay xuống 'own'/'dept' thì để yên.
    # (pur_admin không nằm ở đây — nó được ghi đè trọn gói bằng resync_role_perms bên dưới.)
    for rcode in ("dept_head", "company_head", "pur_staff"):
        r = db.query(Role).filter(Role.code == rcode).first()
        if r:
            db.query(Permission).filter(
                Permission.role_id == r.id, Permission.entity == "contract",
                Permission.scope == "all",
            ).update({"scope": "company"}, synchronize_session=False)
    db.commit()

    # Cập nhật lại 2 vai trò thu mua theo phân quyền mới:
    #  - Quản lý thu mua: toàn quyền nghiệp vụ (như admin, trừ user/role/setting)
    #  - Admin thu mua: CRUD danh mục, nghiệp vụ chỉ đọc (proc)
    resync_role_perms(db, "pur_manager", STD_ROLES["pur_manager"]["perms"])
    resync_role_perms(db, "pur_admin", STD_ROLES["pur_admin"]["perms"])

    # Task 5 (CR-007): gỡ quyền xem NCC (supplier.read) khỏi vai trò nhân viên cơ bản.
    _basic_role_ids = [r.id for r in db.query(Role).filter(Role.code.in_(["employee", "staff"])).all()]
    if _basic_role_ids:
        db.query(Permission).filter(Permission.role_id.in_(_basic_role_ids),
                                    Permission.entity == "supplier").delete(synchronize_session=False)
        db.commit()
    print("SEED_FORCE_SYNC=true: đã ghi đè ma trận quyền các vai trò chuẩn theo app/seed.py.")


# ---- Phân hệ VĂN THƯ · danh mục nền ----
# Ba sổ mở sẵn cho pháp nhân đầu tiên: đến / đi / nội bộ.
# Mỗi sổ một bộ đếm riêng, đếm lại từ 1 mỗi năm — đúng lệ hành chính.
SAMPLE_DOCUMENT_BOOKS = [
    # mã, tên sổ, loại (1 đến · 2 đi · 3 nội bộ), tiền tố số
    ("SD001", "Sổ văn bản đến", 1, "VBĐ"),
    ("SDI001", "Sổ văn bản đi", 2, "VBĐI"),
    ("SNB001", "Sổ văn bản nội bộ", 3, "NB"),
]

SAMPLE_EXTERNAL_PARTIES = [
    ("SKHDT", "Sở Kế hoạch và Đầu tư", 1),
    ("CUCTHUE", "Cục Thuế TP.HCM", 1),
    ("VCB", "Ngân hàng Vietcombank — CN Tân Bình", 2),
]


def seed_document_phase1(db):
    """Nạp insert-only dữ liệu A01, C20, A04, A05 và dòng A06 pháp nhân gốc.

    Chỉ thêm bản ghi còn thiếu và điền ô đang rỗng. Không ghi đè mã người dùng
    đã sửa, vì các mã này có thể đã xuất hiện trên văn bản ban hành.
    """
    changed = 0

    existing_types = {row.code.upper(): row for row in db.query(DocType).all()}
    for values in ALL_DOC_TYPES:
        if values["code"].upper() in existing_types:
            continue
        row = DocType(**values)
        db.add(row)
        existing_types[values["code"].upper()] = row
        changed += 1

    #  Mức mật / độ khẩn. Insert-only theo `code`: bảy dòng gốc phải luôn có
    #  mặt (số trên `tab_document` mới tra ra tên), nhưng tên và mô tả thì quản
    #  trị sửa được trên giao diện — seed chạy lại ở mỗi lần deploy, ghi đè là
    #  xóa mất chữ người ta vừa sửa.
    existing_levels = {row.code.upper() for row in db.query(SecurityLevel).all()}
    for values in SECURITY_LEVELS:
        if values["code"].upper() in existing_levels:
            continue
        db.add(SecurityLevel(**values, is_active=True))
        existing_levels.add(values["code"].upper())
        changed += 1

    existing_companies = {row.code.upper(): row for row in db.query(Company).all()}
    for values in DOCUMENT_COMPANIES:
        row = existing_companies.get(values["code"].upper())
        if row is None:
            row = Company(**values, is_active=True)
            db.add(row)
            existing_companies[values["code"].upper()] = row
            changed += 1
            continue
        first_document_backfill = not (row.short_name or "").strip()
        for field in ("issue_code", "short_name"):
            if not (getattr(row, field, "") or "").strip() and values.get(field):
                setattr(row, field, values[field])
                changed += 1
        # Chỉ điền level cùng lần backfill dữ liệu Văn thư đầu tiên. Những lần
        # startup sau không ghi đè cấp pháp nhân mà người dùng đã chỉnh trên UI.
        if first_document_backfill and row.level != values["level"]:
            row.level = values["level"]
            changed += 1

    db.flush()

    employee_by_code = {row.code.upper(): row for row in db.query(Employee).all()}
    for department in db.query(Department).all():
        config = DEPARTMENT_DOCUMENT_CONFIG.get((department.code or "").upper())
        if config and not (department.issue_code or "").strip():
            department.issue_code = config["issue_code"]
            department.kind = config["kind"]
            changed += 1

        manager_code = (config or {}).get("manager_employee_code", "").upper()
        manager = employee_by_code.get(manager_code) if manager_code else None
        if manager and not department.manager_id:
            department.manager_id = manager.id
            changed += 1

        if not department.company_id:
            continue
        link = (
            db.query(DepartmentCompany)
            .filter(DepartmentCompany.department_id == department.id,
                    DepartmentCompany.company_id == department.company_id)
            .one_or_none()
        )
        if link is None:
            db.add(DepartmentCompany(
                department_id=department.id,
                company_id=department.company_id,
                manager_employee_id=department.manager_id or None,
                issue_code_override="",
                is_active=department.is_active,
            ))
            changed += 1
        elif not link.manager_employee_id and department.manager_id:
            link.manager_employee_id = department.manager_id
            changed += 1

    db.flush()
    changed += _seed_doc_type_link_rules(db, existing_types)

    db.commit()
    return changed


def _seed_doc_type_link_rules(db, types_by_code: dict) -> int:
    """E01 — bảy dòng quy tắc quan hệ mẫu. INSERT-ONLY.

    Không ghi đè dòng đã có: Hành chính chỉnh "bắt buộc hay không" trên giao diện
    rồi mà seed đè lại thì mỗi lần deploy là một lần chặn nhầm người gửi duyệt.
    """
    from app.modules.doc_catalog.link_rule_model import DocTypeLinkRule

    added = 0
    for source_code, relation, target_code, required, min_count, max_count in DOC_TYPE_LINK_RULES:
        source = types_by_code.get(source_code.upper())
        target = types_by_code.get(target_code.upper())
        if source is None or target is None:
            continue
        exists = (
            db.query(DocTypeLinkRule.id)
            .filter(DocTypeLinkRule.source_type_id == source.id,
                    DocTypeLinkRule.relation == relation,
                    DocTypeLinkRule.target_type_id == target.id)
            .first()
        )
        if exists:
            continue
        db.add(DocTypeLinkRule(
            source_type_id=source.id, relation=relation, target_type_id=target.id,
            is_required=required, min_count=min_count, max_count=max_count,
        ))
        added += 1
    return added


def seed_doc_catalog(db, company_id=0):
    """Danh mục phụ phân hệ Văn thư — CHỈ nạp khi bảng còn rỗng.

    Bảng có dữ liệu rồi thì bỏ qua hoàn toàn: seed chạy lại mỗi lần deploy, nạp
    đè sẽ dựng lại đúng những loại mà Hành chính vừa xóa trên giao diện.
    """
    n = 0
    if db.query(DocumentBook).count() == 0 and company_id:
        for code, name, kind, prefix in SAMPLE_DOCUMENT_BOOKS:
            db.add(DocumentBook(code=code, name=name, kind=kind, number_prefix=prefix,
                                company_id=company_id, reset_yearly=True, start_no=1,
                                is_active=True))
            n += 1

    if db.query(ExternalParty).count() == 0:
        for code, name, kind in SAMPLE_EXTERNAL_PARTIES:
            db.add(ExternalParty(code=code, name=name, kind=kind, is_active=True))
            n += 1

    # Mã đi vào số hiệu văn bản: điền cho pháp nhân đang BỎ TRỐNG, lấy từ `code`
    # nếu mã đó vốn đã chỉ có chữ và số ("DEGO", "IDA"). Mã có dấu hoặc khoảng
    # trắng thì để trống — Hành chính khai tay, chứ tự bịa ra một mã rồi cấp số
    # theo nó là không rút lại được (P1-T05 khóa mã sau khi đã cấp số).
    for company in db.query(Company).filter(
            (Company.issue_code == "") | (Company.issue_code.is_(None))).all():
        candidate = (company.code or "").strip().upper()
        if candidate.isalnum() and len(candidate) <= 20:
            company.issue_code = candidate
            n += 1

    db.commit()
    return n


def seed_sample_documents(db, company_id=0):
    """Vài văn bản mẫu — **CHỈ dùng cho máy local**, `seed_prod.py` không gọi hàm này.

    Có mẫu để mở màn hình lên là thấy ngay bảng danh sách, trang chi tiết và tab
    phiên bản trông ra sao, chứ không phải một bảng trắng. Chỉ nạp khi bảng còn
    rỗng — nạp đè sẽ dựng lại đúng những bản ghi vừa bị xóa lúc thử nghiệm.
    """
    from datetime import date

    from app.modules.document.model import (STATUS_DRAFT, STATUS_EFFECTIVE,
                                            Document)
    from app.modules.document.version_model import (CHANGE_MAJOR, VERSION_APPROVED,
                                                    VERSION_DRAFT, VERSION_SUPERSEDED,
                                                    DocumentVersion)

    if db.query(Document).count() or not company_id:
        return 0

    doc_types = {t.code: t for t in db.query(DocType).all()}
    employee = db.query(Employee).first()
    department = db.query(Department).first()
    if not doc_types or not employee:
        return 0

    owner_id = employee.id
    dept_id = department.id if department else None

    def add_document(type_code, title, summary, status, versions):
        from app.modules.document import numbering

        doc_type = doc_types.get(type_code)
        if not doc_type:
            return 0
        doc = Document(
            doc_type_id=doc_type.id, company_id=company_id, department_id=dept_id,
            owner_employee_id=owner_id, drafter_employee_id=owner_id,
            title=title, summary=summary, keywords="mẫu, thử nghiệm",
            secrecy_level=doc_type.default_secrecy, urgency=1, status=status,
            effective_date=date.today() if status == STATUS_EFFECTIVE else None,
        )
        db.add(doc)
        db.flush()

        #  Văn bản mẫu đang có hiệu lực thì phải có số hiệu thật — một văn bản
        #  "có hiệu lực" mà bỏ trống ô số hiệu là hình ảnh sai ngay từ dữ liệu
        #  mẫu. Đi qua đúng bộ cấp số chứ không gán chuỗi tay.
        if status == STATUS_EFFECTIVE:
            numbering.assign(db, doc, doc_type, date.today().year)

        last = None
        for major, minor, ver_status, html, change in versions:
            version = DocumentVersion(
                document_id=doc.id, major=major, minor=minor, status=ver_status,
                #  Bản ĐÃ THAY THẾ cũng là bản đã từng được duyệt, nên phải khóa
                #  y như bản đang dùng. Chỉ khóa mỗi bản `APPROVED` là để lại một
                #  bản cũ còn "mở": trang chi tiết ưu tiên mở bản chưa khóa nên
                #  sẽ mở nhầm bản 1.0, băng cảnh báo đọc ra "chưa có hiệu lực"
                #  thay vì "đã bị thay thế", và nút Mở phiên bản mới biến mất vì
                #  hệ tưởng còn một bản nháp đang dở.
                is_locked=ver_status in (VERSION_APPROVED, VERSION_SUPERSEDED),
                content_html=html, change_summary=change,
                change_kind=CHANGE_MAJOR if change else 0,
                effective_from=date.today() if ver_status != VERSION_DRAFT else None,
                prev_version_id=last.id if last else None,
            )
            db.add(version)
            db.flush()
            last = version
            if ver_status == VERSION_APPROVED:
                doc.current_version_id = version.id
        if doc.current_version_id is None and last is not None:
            doc.current_version_id = last.id
        return 1

    n = add_document(
        "QC", "Quy chế quản lý văn bản nội bộ",
        "Quy định cách lập, duyệt, ban hành và lưu trữ văn bản trong tập đoàn.",
        STATUS_EFFECTIVE,
        [
            #  Bản 1.0 đã bị 2.0 thay thế — để trang chi tiết có sẵn một băng
            #  cảnh báo "đã bị thay thế" mà xem.
            (1, 0, VERSION_SUPERSEDED,
             "<p>Bản đầu tiên của quy chế quản lý văn bản.</p>", ""),
            (2, 0, VERSION_APPROVED,
             "<p><strong>QUY CHẾ QUẢN LÝ VĂN BẢN NỘI BỘ</strong></p>"
             "<p>Điều 1. Phạm vi áp dụng: toàn bộ pháp nhân thuộc tập đoàn.</p>"
             "<p>Điều 2. Văn bản chỉ có hiệu lực sau khi được duyệt và cấp số.</p>",
             "Bổ sung Điều 2 về hiệu lực và cấp số"),
        ])
    n += add_document(
        "CV", "Công văn trao đổi lịch làm việc quý III",
        "Đề nghị các đơn vị gửi lịch làm việc quý III trước ngày 25 hằng tháng.",
        STATUS_DRAFT,
        [(1, 0, VERSION_DRAFT, "<p>Kính gửi: Các đơn vị trực thuộc.</p>", "")])

    db.commit()
    return n


def run():
    # Schema do Alembic quản lý (start.sh chạy `alembic upgrade head` trước). Seed chỉ nạp DATA.
    db = SessionLocal()
    try:
        admin_role = ensure_admin_role(db)

        # Vai trò chuẩn (Nhân sự / Trưởng phòng / Quản lý cty / NV thu mua / QL thu mua / Admin thu mua)
        seed_standard_roles(db)
        force_resync_roles(db)

        # Deduplication tracking sets (using upper case for case-insensitivity)
        seen_companies = {c[0].upper() for c in db.query(Company.code).all()}
        seen_suppliers = {s[0].upper() for s in db.query(Supplier.code).all()}
        seen_products = {p[0].upper() for p in db.query(Product.code).all()}
        seen_warehouses = {w[0].upper() for w in db.query(Warehouse.code).all()}
        seen_units = {u[0].upper() for u in db.query(Unit.code).all()}
        seen_item_groups = {g[0].upper() for g in db.query(ItemGroup.name).all()}
        seen_brands = {b[0].upper() for b in db.query(Brand.code).all()}
        seen_departments = {d[0].upper() for d in db.query(Department.code).all() if d[0]}

        # Danh mục mẫu + master data JSON CHỈ nạp khi bảng còn RỖNG (cài mới / DB test).
        # DB đang chạy thì bỏ qua: nếu không, mỗi lần deploy sẽ dựng lại đúng những bản ghi
        # mà người dùng đã XÓA trên màn danh mục.
        for code, name, mst in (SAMPLE_COMPANIES if not seen_companies else []):
            db.add(Company(code=code, name=name, tax_code=mst, is_active=True))
            seen_companies.add(code.upper())
        db.commit()
        company = (db.query(Company).filter(Company.code == "DEGO").first()
                   or db.query(Company).order_by(Company.id).first())

        for code, name, mst, stype, terms, vat in (SAMPLE_SUPPLIERS if not seen_suppliers else []):
            db.add(Supplier(code=code, name=name, tax_code=mst, supplier_type=stype,
                            payment_terms=terms, vat=vat, is_active=True))
            seen_suppliers.add(code.upper())
        for code, name, group, unit in (SAMPLE_PRODUCTS if not seen_products else []):
            db.add(Product(code=code, name=name, item_group=group, unit=unit, is_active=True))
            seen_products.add(code.upper())
        # Phòng ban: cũng chỉ nạp khi bảng còn rỗng, tránh dựng lại phòng ban đã bị xóa trên UI.
        for code, name in (SAMPLE_DEPARTMENTS if not seen_departments else []):
            db.add(Department(code=code, name=name, company_id=company.id, is_active=True))
            seen_departments.add(code.upper())
        db.commit()

        # Master data thật từ JSON (sinh từ doc/datamau) — cũng chỉ nạp cho bảng còn rỗng.
        seed_dir = os.path.join(os.path.dirname(__file__), "seed_data")

        def _load(n, skip=False):
            if skip:
                return []
            p = os.path.join(seed_dir, n)
            return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []

        for c in _load("companies.json", skip=bool(seen_companies)):
            code = (c.get("code") or "")[:25]
            if code and code.upper() not in seen_companies:
                db.add(Company(code=code, name=c.get("name", ""), address=c.get("address", ""),
                               tax_code=c.get("tax_code", ""), is_active=True))
                seen_companies.add(code.upper())
        for s in _load("suppliers.json", skip=bool(seen_suppliers)):
            code = (s.get("code") or "")[:25]
            if code and code.upper() not in seen_suppliers:
                db.add(Supplier(code=code, name=s.get("name", ""), address=s.get("address", ""),
                                tax_code=s.get("tax_code", ""), supplier_type=s.get("supplier_type", "goods"),
                                is_active=True))
                seen_suppliers.add(code.upper())
        db.commit()

        # Danh mục: kho, ĐVT, phân loại, thương hiệu
        for w in _load("warehouses.json", skip=bool(seen_warehouses)):
            code = (w.get("code") or "")[:25]
            if code and code.upper() not in seen_warehouses:
                db.add(Warehouse(code=code, name=w.get("name", ""), address=w.get("address", ""), is_active=True))
                seen_warehouses.add(code.upper())
        for u in _load("units.json", skip=bool(seen_units)):
            nm = (u.get("name") or "").strip()
            code = nm[:25]
            if code and code.upper() not in seen_units:
                db.add(Unit(code=code, name=nm[:100], is_active=True))
                seen_units.add(code.upper())
        ig_seq = db.query(ItemGroup).count()
        for g in _load("item_groups.json", skip=bool(seen_item_groups)):
            nm = (g.get("name") or "").strip()
            if nm and nm[:100].upper() not in seen_item_groups:
                ig_seq += 1
                code = (g.get("code") or f"PL{ig_seq:03d}")[:25]
                db.add(ItemGroup(code=code, name=nm[:100], std_days=str(g.get("std_days", "")),
                                 std_days_unavail=str(g.get("std_days_unavail", "")),
                                 note=g.get("note", ""), apply_date=g.get("apply_date", ""), is_active=True))
                seen_item_groups.add(nm[:100].upper())
        for b in _load("brands.json", skip=bool(seen_brands)):
            code = (b.get("code") or "")[:25]
            if code and code.upper() not in seen_brands:
                db.add(Brand(code=code, department=b.get("department", ""), is_active=True))
                seen_brands.add(code.upper())
        db.commit()

        emp = db.query(Employee).filter(Employee.code == settings.ADMIN_CODE).first()
        if not emp:
            emp = Employee(code=settings.ADMIN_CODE, full_name="Quản trị viên",
                           company_id=company.id, position="Admin", is_active=True)
            db.add(emp)
            db.commit()
            db.refresh(emp)

        user = db.query(User).filter(User.employee_id == emp.id).first()
        if not user:
            user = User(email="hgbao.idagroup@gmail.com", employee_id=emp.id,
                        password_hash=hash_password(settings.ADMIN_PASSWORD), is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)
            db.add(UserRole(user_id=user.id, role_id=admin_role.id))
            db.commit()

        # Seed second admin: DEGO0001 (username: admin, pass: admin, name: Dego Admin)
        emp2 = db.query(Employee).filter(Employee.code == "DEGO0001").first()
        if not emp2:
            emp2 = Employee(code="DEGO0001", full_name="Dego Admin",
                            company_id=company.id, position="Admin", is_active=True)
            db.add(emp2)
            db.commit()
            db.refresh(emp2)

        user2 = db.query(User).filter(User.employee_id == emp2.id).first()
        if not user2:
            user2 = User(email="admin", employee_id=emp2.id,
                         password_hash=hash_password("admin"), is_active=True)
            db.add(user2)
            db.commit()
            db.refresh(user2)
            db.add(UserRole(user_id=user2.id, role_id=admin_role.id))
            db.commit()

        # Seed demo accounts (chỉ khi bật — prod đặt SEED_DEMO_ACCOUNTS=false để bỏ qua)
        if getattr(settings, "SEED_DEMO_ACCOUNTS", True):
            seed_demo_accounts(db, company.id)
        else:
            print("Bỏ qua seed tài khoản demo (SEED_DEMO_ACCOUNTS=false).")

        # Bảy tài khoản của nhóm «Tài khoản Test (Data)» trong menu đổi tài khoản
        # nhanh — CHỈ local. Trước 24/08/2026 bảy dòng đó nằm trong menu mà không
        # có bản ghi nào trong CSDL, bấm vào chỉ ăn toast lỗi.
        # CHẠY SAU seed_standard_roles vì nó gán vai trò chuẩn.
        if getattr(settings, "SEED_DEMO_ACCOUNTS", True):
            from app.seed_tai_khoan_test import seed_tai_khoan_test

            n_test = seed_tai_khoan_test(db, company.id)
            if n_test:
                print(f"Tạo {n_test} tài khoản test (TESTREQ, DEMONV, DEMOTP…).")

        # Phân công NSTM mẫu — CHẠY SAU seed_demo_accounts vì tham chiếu mã nhân sự demo
        n_assign = seed_category_assignees(db)
        if n_assign:
            print(f"Nạp {n_assign} dòng phân công NSTM mẫu.")

        # Tài khoản quản trị Trung tâm Hướng dẫn sử dụng (app help-center)
        seed_help_admin(db, company.id)

        # 4 khung cấu hình trang chủ Help Center (Bắt đầu ngay/Phân hệ/Câu hỏi/Mẹo)
        seed_help_home_sections(db)

        # Phase 1 Văn thư: 32 loại + Trích lục, 13 mã pháp nhân, mã phòng ban và
        # dòng A06 cho pháp nhân gốc. Chỉ thêm/điền ô trống, không ghi đè.
        n_phase1 = seed_document_phase1(db)
        if n_phase1:
            print(f"Nạp/cập nhật {n_phase1} dòng dữ liệu Phase 1 Văn thư.")

        # Danh mục phụ phân hệ Văn thư (đơn vị gửi nhận, sổ mẫu)
        n_doc = seed_doc_catalog(db, company.id if company else 0)
        if n_doc:
            print(f"Nạp {n_doc} dòng danh mục Văn thư.")

        # Văn bản mẫu — CHỈ local (`seed_prod.py` không gọi hàm này).
        n_sample = seed_sample_documents(db, company.id if company else 0)
        if n_sample:
            print(f"Nạp {n_sample} văn bản mẫu.")

        # Văn thư ở TỪNG pháp nhân con — CHỈ local. Không có mấy tài khoản này thì
        # bản clone sinh ra ở 12 công ty con không ai mở được, tức là nửa sau của
        # luồng "ban hành xuống pháp nhân con" không diễn được.
        from app.seed_van_thu_phap_nhan_con import seed_van_thu_phap_nhan_con

        n_vt = seed_van_thu_phap_nhan_con(db)
        if n_vt:
            print(f"Tạo {n_vt} văn thư ở pháp nhân con.")

        # Gán vai trò mặc định "Nhân sự" cho tài khoản chưa có vai trò
        n_default = assign_default_roles(db)
        if n_default:
            print(f"Gán vai trò 'Nhân sự' mặc định cho {n_default} tài khoản.")

        # Gộp vai trò 'Nhân viên' (STAFF/staff, kể cả demo — MariaDB không phân biệt hoa/thường)
        # vào 'Nhân sự' rồi xóa. CHẠY SAU seed_demo_accounts để dọn cả role demo vừa tạo.
        cleanup_legacy_staff_role(db)

        # Hình thức thanh toán mặc định "Công nợ 30 ngày": CHỈ điền cho NCC đang BỎ TRỐNG.
        # (Trước đây ghi đè TOÀN BỘ NCC mỗi lần khởi động -> xóa sạch điều khoản riêng của từng NCC.)
        _q = db.query(Supplier).filter((Supplier.payment_terms == None) | (Supplier.payment_terms == ""))  # noqa: E711
        if FORCE_SYNC:
            _q = db.query(Supplier)   # cố ý áp lại cho toàn bộ NCC
        n_updated = _q.update({"payment_terms": "Công nợ 30 ngày"}, synchronize_session=False)
        db.commit()
        if n_updated:
            print(f"Đã điền hình thức thanh toán 'Công nợ 30 ngày' cho {n_updated} nhà cung cấp.")

        print(f"Seed done. Admin login: {settings.ADMIN_CODE} / (mật khẩu trong .env)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
