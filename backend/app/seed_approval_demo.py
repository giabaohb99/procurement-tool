"""DỮ LIỆU MẪU cho LUỒNG DUYỆT và QUY TẮC ĐÁNH SỐ.

⚠️ **Chạy tay, KHÔNG nối vào `start.sh`** — nó xóa sạch rồi nạp lại:

    docker compose exec api python -m app.seed_approval_demo

Dựng theo lối văn thư nhà nước, nơi đường ký một văn bản phụ thuộc vào **loại**
và **độ mật** của nó: quy chế thì phải qua pháp chế và tài chính rồi mới tới
Tổng Giám đốc; công văn thường thì trưởng phòng duyệt, chánh văn phòng ký.

⚠️ Về "song song": trong bộ máy này **nhiều bước cùng một chặng là các NHÁNH
RẼ** — chỉ một nhánh khớp điều kiện được chạy (`flow_service.buoc_cua_chang`).
Muốn hai người CÙNG phải duyệt thì khai MỘT bước, nhiều người, `multi_mode =
MULTI_ALL`. Bộ mẫu dùng cả hai kiểu để thấy rõ khác nhau.
"""
from datetime import date, timedelta

import app.core.all_models  # noqa: F401  — xem ghi chú ở `seed_document_demo`
from app.core.database import SessionLocal
from app.modules.approval.delegation_model import Delegation
from app.modules.approval.flow_model import (APPROVER_DEPT_HEAD,
                                             APPROVER_EMPLOYEE, MULTI_ALL,
                                             MULTI_ANY, NO_APPROVER_FALLBACK,
                                             NODE_APPROVAL, NODE_CC,
                                             ROLE_APPROVE, ROLE_CHECK,
                                             ApprovalFlow, ApprovalNode)
from app.modules.approval.instance_model import (ApprovalAction,
                                                 ApprovalInstance,
                                                 ApprovalTask)
from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.doc_catalog.numbering_rule_model import (
    DocumentNumberingRule, DocumentNumberingRuleBook,
    DocumentNumberingRuleDocType)
from app.modules.employee.model import Employee

ACTOR = 1
TODAY = date.today()

#  Ba chiều văn bản của quy tắc đánh số: đến · đi · nội bộ.
DIR_INCOMING, DIR_OUTGOING, DIR_INTERNAL = 1, 2, 3


def wipe(db) -> dict[str, int]:
    """Dọn luồng duyệt + phiên đang chạy + quy tắc đánh số. Công tắc GIỮ NGUYÊN."""
    count = {}
    for name, model in [
        ("thao tác duyệt", ApprovalAction),
        ("việc chờ duyệt", ApprovalTask),
        ("phiên duyệt", ApprovalInstance),
        ("bước duyệt", ApprovalNode),
        ("luồng duyệt", ApprovalFlow),
        ("ủy quyền", Delegation),
        ("loại của quy tắc số", DocumentNumberingRuleDocType),
        ("sổ của quy tắc số", DocumentNumberingRuleBook),
        ("quy tắc đánh số", DocumentNumberingRule),
    ]:
        count[name] = db.query(model).delete()
    db.commit()
    return count


def _assign_department_head(db, people) -> None:
    """Khai TRƯỞNG PHÒNG cho các phòng chưa có.

    Bước đầu của mọi luồng mẫu chọn người duyệt kiểu «trưởng bộ phận người nộp»
    (`_truong_bo_phan` đọc `Department.manager_id`). Phòng bỏ trống cột đó thì
    bước 1 không tìm ra ai, phiên duyệt rơi thẳng vào trạng thái **KẸT** và
    không sinh việc nào — màn «Việc của tôi» trống trơn dù luồng khai đúng.

    ⚠️ **Người này PHẢI KHÁC `chanh_vp`** (22/08/2026). Trước đây cả hai là một,
    nên mọi luồng hai bước sụp thành một chữ ký: bước 1 «trưởng bộ phận người
    nộp» và bước 2 «Chánh Văn phòng ký» ra cùng một người, bước 2 **tự qua vì
    trùng người** và văn bản ban hành xong chỉ có ĐÚNG MỘT người ký — trong khi
    nhìn cấu hình luồng thì tưởng có hai. Luật tự-qua là cố ý và đúng; cái sai
    nằm ở chỗ dữ liệu mẫu chọn trùng người.
    """
    from app.modules.department.model import Department

    dept_head = people["truong_bp"]
    office_chief_id = people["chanh_vp"].id

    for department in db.query(Department).filter(
            (Department.manager_id.is_(None)) | (Department.manager_id == 0)).all():
        department.manager_id = dept_head.id

    #  VÁ dữ liệu do chính bản seed cũ gán sai: phòng nào đang để `chanh_vp` làm
    #  trưởng phòng thì chuyển sang `truong_bp`. Không vá thì mọi máy đã seed
    #  trước 22/08/2026 vẫn dính lỗi hai-bước-một-chữ-ký, vì vòng lặp bên trên
    #  chỉ điền phòng CÒN TRỐNG.
    #
    #  Chỉ đụng đúng giá trị mà seed cũ ghi ra, và đây là seed DEMO chạy ở local
    #  — không phải nơi có trưởng phòng thật do người dùng khai.
    if dept_head.id != office_chief_id:
        for department in db.query(Department).filter(
                Department.manager_id == office_chief_id).all():
            department.manager_id = dept_head.id

    db.commit()


def enable_switch(db) -> str:
    """BẬT bộ máy duyệt nhiều bước cho văn bản (I26).

    `xoa()` cố ý không đụng tới công tắc, nhưng nạp luồng mà để công tắc TẮT thì
    cả bộ dữ liệu mẫu này là đồ trang trí: `service.submit()` đi thẳng đường một
    bước cũ, không phiên nào được mở, và người xem tưởng luồng đang chạy vì
    trong bảng vẫn có sẵn hai phiên do chính seed này gọi tay vào engine.

    Chỉ áp cho `document` — các loại chứng từ khác vẫn giữ nguyên trạng thái của
    chúng, và tắt lại lúc nào cũng được ở màn «Bộ máy duyệt».
    """
    from app.modules.approval.flow_model import ApprovalSwitch

    row = db.query(ApprovalSwitch).filter(ApprovalSwitch.entity == "document").first()
    if row is None:
        db.add(ApprovalSwitch(entity="document", is_enabled=True, note="",
                              created_by=ACTOR, updated_by=ACTOR))
        db.commit()
        return "bật"
    if not row.is_enabled:
        row.is_enabled, row.updated_by = True, ACTOR
        db.commit()
        return "bật"
    return "giữ nguyên (đang bật)"


def _people(db) -> dict[str, Employee]:
    """Ba vai người duyệt. Ít nhân sự thì dùng lại người đầu — dữ liệu mẫu
    không được nổ chỉ vì máy local mới seed có hai nhân viên."""
    items = db.query(Employee).filter(Employee.is_active.is_(True)).order_by(Employee.id).all()
    if not items:
        raise SystemExit("Chưa có nhân sự — chạy `python -m app.seed` trước.")
    pick = lambda i: items[i] if i < len(items) else items[-1]  # noqa: E731
    office_chief = pick(3)

    #  TRƯỞNG BỘ PHẬN mặc định của các phòng chưa khai — phải KHÁC `chanh_vp`,
    #  xem `_gan_truong_phong`. Lấy người thứ 5; máy chỉ có vài nhân sự thì tìm
    #  bất kỳ ai khác `chanh_vp` để ít nhất luồng hai bước vẫn ra hai người.
    dept_head = pick(4)
    if dept_head.id == office_chief.id:
        dept_head = next((e for e in items if e.id != office_chief.id), office_chief)

    return {"tgd": pick(0), "phap_che": pick(1), "tai_chinh": pick(2),
            "chanh_vp": office_chief, "truong_bp": dept_head}


class _Factory:
    def __init__(self, db):
        self.db = db
        self.kind = {t.code: t for t in db.query(DocType).all()}

    def flow(self, entity: str, code: str, name: str, description: str, *,
              condition: str = "", priority: int = 0) -> ApprovalFlow:
        flow = ApprovalFlow(
            entity=entity, code=code, name=name, description=description,
            condition=condition, priority=priority, is_active=True,
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(flow)
        self.db.flush()
        return flow

    def step(self, flow: ApprovalFlow, seq: int, name: str, *,
             branch: str = "", ai: int = APPROVER_DEPT_HEAD, ref: str = "",
             multi_mode: int = MULTI_ANY, condition: str = "",
             default: bool = False, due_hours: int = 0, fallback: int | None = None,
             node_type: int = NODE_APPROVAL, role: int = ROLE_APPROVE) -> ApprovalNode:
        node = ApprovalNode(
            flow_id=flow.id, seq=seq, branch_key=branch, name=name,
            node_kind=node_type, flow_role=role,
            approver_kind=ai, approver_ref=ref, multi_mode=multi_mode,
            condition=condition, is_default_branch=default,
            sla_hours=due_hours, fallback_employee_id=fallback,
            on_no_approver=NO_APPROVER_FALLBACK if fallback else 3,
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(node)
        self.db.flush()
        return node

    def hr_department(self) -> str:
        """Id phòng Nhân sự dạng chuỗi, cho `approver_ref` của bước «trưởng bộ
        phận của phòng ban chỉ định».

        Dò theo MÃ trước rồi mới tới chuỗi con trong tên: tên phòng khác nhau
        giữa các nơi ("Phòng Nhân sự", "Phòng Nhân sự - Hành chính"). Không thấy
        thì trả rỗng — bước rơi về người dự phòng, chứ không trỏ bừa vào một
        phòng khác.
        """
        from app.modules.department.model import Department

        department = (self.db.query(Department)
                 .filter(Department.code.in_(("PBA007", "NS", "HCNS")))
                 .order_by(Department.id).first())
        if department is None:
            department = (self.db.query(Department)
                     .filter(Department.name.ilike("%nhân sự%"))
                     .order_by(Department.id).first())
        return str(department.id) if department else ""

    def type_condition(self, *type_code: str) -> str:
        """`[{"field":"doc_type_id","op":"in","value":[...]}]` — đúng dạng bộ dựng
        điều kiện trên giao diện sinh ra, để mở lên sửa được chứ không thành
        «điều kiện khai tay»."""
        import json

        ids = [self.kind[code].id for code in type_code if code in self.kind]
        return json.dumps([{"field": "doc_type_id", "op": "in", "value": ids}])


def seed_numbering_rules(db) -> int:
    """Quy tắc đánh số — theo thể thức Nghị định 30 và thực tế văn thư."""
    from app.seed_data.approval_demo_corpus import NUMBERING_RULES

    kind = {t.code: t for t in db.query(DocType).all()}
    for direction, pattern, priority, reset, manual_edit, _reason, type_code in NUMBERING_RULES:
        rule = DocumentNumberingRule(
            direction=direction, pattern=pattern, start_no=1, reset_yearly=reset,
            allow_manual=manual_edit, priority=priority,
            #  `doc_type_mode` 2 = chỉ áp cho các loại liệt kê ở bảng con.
            doc_type_mode=2 if type_code else 1, book_mode=1,
            is_active=True, created_by=ACTOR, updated_by=ACTOR,
        )
        db.add(rule)
        db.flush()
        for code in type_code:
            if code in kind:
                db.add(DocumentNumberingRuleDocType(
                    rule_id=rule.id, doc_type_id=kind[code].id,
                    created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return len(NUMBERING_RULES)


def seed_delegations(db, people) -> int:
    """I22 — Tổng Giám đốc đi công tác, ủy quyền Chánh Văn phòng ký thay."""
    db.add(Delegation(
        from_employee_id=people["tgd"].id, to_employee_id=people["chanh_vp"].id,
        entity="", from_date=TODAY - timedelta(days=2),
        to_date=TODAY + timedelta(days=12), is_active=True,
        reason="Tổng Giám đốc đi công tác nước ngoài từ ngày 16/8 đến 30/8.",
        created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return 1


def assign_document_roles(db) -> int:
    """Trình hai văn bản đang chờ duyệt vào bộ máy, để «Việc của tôi» có dữ liệu.

    Đi qua đúng `service.submit` — cùng một cửa mà người dùng bấm «Gửi duyệt» —
    chứ không gọi thẳng `instance_service.bat_dau`.

    Gọi thẳng vào engine thì mở được phiên duyệt nhưng **bỏ quên phiên bản**: nó
    vẫn nằm ở trạng thái nháp. Hậu quả thấy ngay trên màn hình: văn bản ghi
    «Đang duyệt» mà nút «Gửi duyệt» vẫn bày ra, và tới lúc duyệt xong hết bước
    thì `service.approve` báo "Không có bản nào đang chờ duyệt" — phiếu ghi đã
    duyệt còn văn bản thì không ban hành được. Dữ liệu mẫu phải đi đúng đường
    của người dùng, nếu không nó dựng ra một trạng thái không ai tạo nổi bằng
    tay và ta ngồi sửa những lỗi chỉ tồn tại trong seed.

    Công tắc phải BẬT trước khi gọi hàm này (xem `bat_cong_tac`), nếu không
    `service.submit` đi đường một bước cũ và không phiên nào được mở.
    """
    from app.modules.approval import instance_service
    from app.modules.document import service
    from app.modules.document.model import STATUS_SUBMITTED, Document

    count = 0
    for doc in db.query(Document).filter(Document.status == STATUS_SUBMITTED).all():
        service.submit(db, doc, ACTOR)
        if instance_service.running_instance(db, "document", doc.id) is not None:
            count += 1
    db.commit()
    return count


def run() -> None:
    db = SessionLocal()
    try:
        print("Đang xóa luồng duyệt và quy tắc đánh số cũ…")
        for name, so in wipe(db).items():
            print(f"  - {name}: {so}")

        people = _people(db)
        _assign_department_head(db, people)
        factory = _Factory(db)

        from app.seed_data.approval_demo_corpus import build_flows

        flow = build_flows(factory, people)
        db.commit()
        print(f"Đã nạp {len(flow)} luồng duyệt, "
              f"{db.query(ApprovalNode).count()} bước.")
        print(f"Đã {enable_switch(db)} bộ máy duyệt cho văn bản.")
        print(f"Đã nạp {seed_numbering_rules(db)} quy tắc đánh số.")
        print(f"Đã nạp {seed_delegations(db, people)} dòng ủy quyền.")
        print(f"Đã trình {assign_document_roles(db)} văn bản vào bộ máy duyệt.")
        print("Xong.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
