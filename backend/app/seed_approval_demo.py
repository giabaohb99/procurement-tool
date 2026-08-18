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
HOM_NAY = date.today()

#  Ba chiều văn bản của quy tắc đánh số: đến · đi · nội bộ.
CHIEU_DEN, CHIEU_DI, CHIEU_NOI_BO = 1, 2, 3


def xoa(db) -> dict[str, int]:
    """Dọn luồng duyệt + phiên đang chạy + quy tắc đánh số. Công tắc GIỮ NGUYÊN."""
    dem = {}
    for ten, model in [
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
        dem[ten] = db.query(model).delete()
    db.commit()
    return dem


def _gan_truong_phong(db, nguoi) -> None:
    """Khai TRƯỞNG PHÒNG cho các phòng chưa có.

    Bước đầu của mọi luồng mẫu chọn người duyệt kiểu «trưởng bộ phận người nộp»
    (`_truong_bo_phan` đọc `Department.manager_id`). Phòng bỏ trống cột đó thì
    bước 1 không tìm ra ai, phiên duyệt rơi thẳng vào trạng thái **KẸT** và
    không sinh việc nào — màn «Việc của tôi» trống trơn dù luồng khai đúng.
    """
    from app.modules.department.model import Department

    for phong in db.query(Department).filter(
            (Department.manager_id.is_(None)) | (Department.manager_id == 0)).all():
        phong.manager_id = nguoi["chanh_vp"].id
    db.commit()


def bat_cong_tac(db) -> str:
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


def _nguoi(db) -> dict[str, Employee]:
    """Ba vai người duyệt. Ít nhân sự thì dùng lại người đầu — dữ liệu mẫu
    không được nổ chỉ vì máy local mới seed có hai nhân viên."""
    ds = db.query(Employee).filter(Employee.is_active.is_(True)).order_by(Employee.id).all()
    if not ds:
        raise SystemExit("Chưa có nhân sự — chạy `python -m app.seed` trước.")
    lay = lambda i: ds[i] if i < len(ds) else ds[-1]  # noqa: E731
    return {"tgd": lay(0), "phap_che": lay(1), "tai_chinh": lay(2), "chanh_vp": lay(3)}


class _Xuong:
    def __init__(self, db):
        self.db = db
        self.loai = {t.code: t for t in db.query(DocType).all()}

    def luong(self, entity: str, ma: str, ten: str, mo_ta: str, *,
              dieu_kien: str = "", uu_tien: int = 0) -> ApprovalFlow:
        flow = ApprovalFlow(
            entity=entity, code=ma, name=ten, description=mo_ta,
            condition=dieu_kien, priority=uu_tien, is_active=True,
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(flow)
        self.db.flush()
        return flow

    def buoc(self, flow: ApprovalFlow, seq: int, ten: str, *,
             nhanh: str = "", ai: int = APPROVER_DEPT_HEAD, ref: str = "",
             nhieu_nguoi: int = MULTI_ANY, dieu_kien: str = "",
             mac_dinh: bool = False, han_gio: int = 0, du_phong: int | None = None,
             loai_buoc: int = NODE_APPROVAL, vai_tro: int = ROLE_APPROVE) -> ApprovalNode:
        node = ApprovalNode(
            flow_id=flow.id, seq=seq, branch_key=nhanh, name=ten,
            node_kind=loai_buoc, flow_role=vai_tro,
            approver_kind=ai, approver_ref=ref, multi_mode=nhieu_nguoi,
            condition=dieu_kien, is_default_branch=mac_dinh,
            sla_hours=han_gio, fallback_employee_id=du_phong,
            on_no_approver=NO_APPROVER_FALLBACK if du_phong else 3,
            created_by=ACTOR, updated_by=ACTOR,
        )
        self.db.add(node)
        self.db.flush()
        return node

    def dieu_kien_loai(self, *ma_loai: str) -> str:
        """`[{"field":"doc_type_id","op":"in","value":[...]}]` — đúng dạng bộ dựng
        điều kiện trên giao diện sinh ra, để mở lên sửa được chứ không thành
        «điều kiện khai tay»."""
        import json

        ids = [self.loai[ma].id for ma in ma_loai if ma in self.loai]
        return json.dumps([{"field": "doc_type_id", "op": "in", "value": ids}])


def nap_quy_tac_so(db) -> int:
    """Quy tắc đánh số — theo thể thức Nghị định 30 và thực tế văn thư."""
    from app.seed_data.approval_demo_corpus import QUY_TAC_SO

    loai = {t.code: t for t in db.query(DocType).all()}
    for chieu, mau, uu_tien, reset, sua_tay, _ly_do, ma_loai in QUY_TAC_SO:
        rule = DocumentNumberingRule(
            direction=chieu, pattern=mau, start_no=1, reset_yearly=reset,
            allow_manual=sua_tay, priority=uu_tien,
            #  `doc_type_mode` 2 = chỉ áp cho các loại liệt kê ở bảng con.
            doc_type_mode=2 if ma_loai else 1, book_mode=1,
            is_active=True, created_by=ACTOR, updated_by=ACTOR,
        )
        db.add(rule)
        db.flush()
        for ma in ma_loai:
            if ma in loai:
                db.add(DocumentNumberingRuleDocType(
                    rule_id=rule.id, doc_type_id=loai[ma].id,
                    created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return len(QUY_TAC_SO)


def nap_uy_quyen(db, nguoi) -> int:
    """I22 — Tổng Giám đốc đi công tác, ủy quyền Chánh Văn phòng ký thay."""
    db.add(Delegation(
        from_employee_id=nguoi["tgd"].id, to_employee_id=nguoi["chanh_vp"].id,
        entity="", from_date=HOM_NAY - timedelta(days=2),
        to_date=HOM_NAY + timedelta(days=12), is_active=True,
        reason="Tổng Giám đốc đi công tác nước ngoài từ ngày 16/8 đến 30/8.",
        created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return 1


def trinh_vai_van_ban(db) -> int:
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

    dem = 0
    for doc in db.query(Document).filter(Document.status == STATUS_SUBMITTED).all():
        service.submit(db, doc, ACTOR)
        if instance_service.phien_dang_chay(db, "document", doc.id) is not None:
            dem += 1
    db.commit()
    return dem


def run() -> None:
    db = SessionLocal()
    try:
        print("Đang xóa luồng duyệt và quy tắc đánh số cũ…")
        for ten, so in xoa(db).items():
            print(f"  - {ten}: {so}")

        nguoi = _nguoi(db)
        _gan_truong_phong(db, nguoi)
        xuong = _Xuong(db)

        from app.seed_data.approval_demo_corpus import dung_luong

        luong = dung_luong(xuong, nguoi)
        db.commit()
        print(f"Đã nạp {len(luong)} luồng duyệt, "
              f"{db.query(ApprovalNode).count()} bước.")
        print(f"Đã {bat_cong_tac(db)} bộ máy duyệt cho văn bản.")
        print(f"Đã nạp {nap_quy_tac_so(db)} quy tắc đánh số.")
        print(f"Đã nạp {nap_uy_quyen(db, nguoi)} dòng ủy quyền.")
        print(f"Đã trình {trinh_vai_van_ban(db)} văn bản vào bộ máy duyệt.")
        print("Xong.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
