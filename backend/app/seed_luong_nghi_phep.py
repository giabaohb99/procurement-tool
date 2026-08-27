"""LUỒNG DUYỆT ĐƠN NGHỈ PHÉP — nạp một lần, CHẠY LẠI ĐƯỢC.

    docker compose exec api python -m app.seed_luong_nghi_phep

⚠️ Khác `seed_approval_demo` ở chỗ quan trọng nhất: bản kia **xóa sạch luồng rồi
nạp lại**, chạy trên môi trường thật là mất hết luồng người ta đã khai và đã sửa
tay. Bản này chỉ **THÊM** đúng một luồng, và chỉ khi nó chưa có. Chạy mười lần
cũng ra một luồng.

Đường đi của một đơn nghỉ phép:

    Chặng 1 — trưởng bộ phận CỦA NGƯỜI XIN NGHỈ  (dự phòng: trưởng phòng Nhân sự)
    Chặng 2 — trưởng phòng NHÂN SỰ               (dự phòng: người đại diện pháp nhân)

Chặng 2 dùng cách chọn **«trưởng bộ phận của phòng ban chỉ định»** — mới có từ
CR-159. Trước đó phải khai đích danh một CON NGƯỜI, và người đó chuyển việc là
luồng trỏ sai mà không có gì báo. Trỏ vào GHẾ thì đổi người ngồi ghế là luồng tự
đi theo.

⚠️ Vì sao hai chặng đều phải có người DỰ PHÒNG: luật I08 bỏ người nộp ra khỏi
danh sách người duyệt. Trưởng phòng tự xin nghỉ thì chặng 1 không còn ai, và
chính trưởng phòng Nhân sự xin nghỉ thì chặng 2 không còn ai — mà quản lý thì
cũng phải nghỉ phép. Không khai dự phòng là những đơn đó **kẹt**.
"""
import json

import app.core.all_models  # noqa: F401  — nạp đủ model để mapper cấu hình được
from app.core.database import SessionLocal
from app.modules.approval.flow_model import (APPROVER_DEPT_HEAD,
                                             APPROVER_DEPT_HEAD_OF, MULTI_ANY,
                                             NO_APPROVER_BLOCK,
                                             NO_APPROVER_FALLBACK,
                                             NODE_APPROVAL, ROLE_APPROVE,
                                             ApprovalFlow, ApprovalNode,
                                             ApprovalSwitch)
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType

ACTOR = 1

FLOW_CODE = "VB_NGHI_PHEP"
DOC_TYPE_CODE = "GNP"

#  Cao hơn mọi luồng văn bản trong bộ mẫu (`VB_QUAN_TRI` 20, `VB_HANH_CHINH` 10)
#  để không phải đoán thứ tự xét. Điều kiện của chúng vốn không phủ `GNP`, nhưng
#  dựa vào điều đó là dựa vào một chi tiết có thể đổi.
PRIORITY = 30

#  Tên phòng Nhân sự khác nhau giữa các nơi ("Phòng Nhân sự", "Phòng Nhân sự -
#  Hành chính", "Phòng Hành chính Nhân sự"), nên dò theo MÃ trước rồi mới tới
#  chuỗi con trong tên. Không thấy thì dừng và nói rõ, đừng đoán bừa một phòng.
HR_DEPT_CODES = ("PBA007", "NS", "HCNS")
NAME_KEYWORDS = ("nhân sự", "hành chính")


def find_hr_department(db) -> Department | None:
    department = (db.query(Department)
             .filter(Department.code.in_(HR_DEPT_CODES),
                     Department.is_active.is_(True))
             .order_by(Department.id).first())
    if department:
        return department
    for kw in NAME_KEYWORDS:
        department = (db.query(Department)
                 .filter(Department.name.ilike(f"%{kw}%"),
                         Department.is_active.is_(True))
                 .order_by(Department.id).first())
        if department:
            return department
    return None


def run() -> int:
    db = SessionLocal()
    try:
        if db.query(ApprovalFlow).filter(ApprovalFlow.entity == "document",
                                         ApprovalFlow.code == FLOW_CODE).first():
            print(f"BỎ QUA: luồng «{FLOW_CODE}» đã có. Sửa thì mở màn Luồng duyệt.")
            return 0

        kind = db.query(DocType).filter(DocType.code == DOC_TYPE_CODE).first()
        if kind is None:
            print(f"DỪNG: chưa có loại văn bản «{DOC_TYPE_CODE}» trong danh mục.")
            return 2

        hr_dept = find_hr_department(db)
        if hr_dept is None:
            print("DỪNG: không tìm ra phòng Nhân sự. Khai phòng đó rồi chạy lại, "
                  "hoặc tự khai chặng 2 trên màn Luồng duyệt.")
            return 2
        if not hr_dept.manager_id:
            print(f"CẢNH BÁO: phòng «{hr_dept.name}» chưa có trưởng bộ phận — "
                  "chặng 2 sẽ rơi về người dự phòng cho tới khi cử trưởng phòng.")

        #  Người dự phòng của chặng cuối: đại diện pháp nhân. Không có thì để
        #  trống và chặng đó DỪNG PHIẾU khi không tìm được ai — hiện ra để quản
        #  trị xử lý, chứ tuyệt đối không tự duyệt qua.
        representative = (db.query(Company.legal_representative_id)
                    .filter(Company.id == hr_dept.company_id).scalar())

        flow = ApprovalFlow(
            entity="document", code=FLOW_CODE, name="Duyệt đơn nghỉ phép",
            description=(
                "Đơn nghỉ phép: trưởng bộ phận của người xin nghỉ duyệt trước, "
                "rồi tới trưởng phòng Nhân sự. Chặng 2 trỏ vào GHẾ trưởng phòng "
                "Nhân sự nên đổi người ngồi ghế thì luồng tự đi theo."),
            condition=json.dumps([{"field": "doc_type_id", "op": "in",
                                   "value": [kind.id]}]),
            priority=PRIORITY, is_active=True,
            created_by=ACTOR, updated_by=ACTOR,
        )
        db.add(flow)
        db.flush()

        db.add(ApprovalNode(
            flow_id=flow.id, seq=1, branch_key="",
            name="Trưởng bộ phận duyệt",
            node_kind=NODE_APPROVAL, flow_role=ROLE_APPROVE,
            approver_kind=APPROVER_DEPT_HEAD, approver_ref="",
            multi_mode=MULTI_ANY, sla_hours=24,
            #  Chính trưởng phòng xin nghỉ → chặng này rỗng. Dự phòng là trưởng
            #  phòng Nhân sự, đúng người sẽ xử ở chặng sau.
            fallback_employee_id=hr_dept.manager_id or None,
            on_no_approver=NO_APPROVER_FALLBACK if hr_dept.manager_id else NO_APPROVER_BLOCK,
            created_by=ACTOR, updated_by=ACTOR,
        ))

        db.add(ApprovalNode(
            flow_id=flow.id, seq=2, branch_key="",
            name=f"Trưởng {hr_dept.name} duyệt",
            node_kind=NODE_APPROVAL, flow_role=ROLE_APPROVE,
            #  ĐÂY là cách chọn mới: bám theo PHÒNG BAN khai trong luồng, không
            #  bám theo phòng của người nộp.
            approver_kind=APPROVER_DEPT_HEAD_OF, approver_ref=str(hr_dept.id),
            multi_mode=MULTI_ANY, sla_hours=24,
            fallback_employee_id=representative or None,
            on_no_approver=NO_APPROVER_FALLBACK if representative else NO_APPROVER_BLOCK,
            created_by=ACTOR, updated_by=ACTOR,
        ))

        #  Bộ máy duyệt phải BẬT cho `document`, không thì `bat_dau` trả None và
        #  văn bản rơi về đường duyệt một bước cũ — luồng vừa khai nằm im.
        switch_row = db.query(ApprovalSwitch).filter(
            ApprovalSwitch.entity == "document").first()
        if switch_row is None:
            db.add(ApprovalSwitch(entity="document", is_enabled=True,
                                  created_by=ACTOR, updated_by=ACTOR))
        elif not switch_row.is_enabled:
            print("CẢNH BÁO: bộ máy duyệt đang TẮT cho «document» — bật ở màn "
                  "Luồng duyệt thì đơn nghỉ phép mới chạy qua luồng này.")

        db.commit()
        print(f"Đã khai luồng «{flow.name}» (id={flow.id}) cho loại {DOC_TYPE_CODE}:")
        print("   chặng 1 — Trưởng bộ phận của người xin nghỉ"
              + (f" (dự phòng: #{hr_dept.manager_id})" if hr_dept.manager_id else ""))
        print(f"   chặng 2 — Trưởng «{hr_dept.name}» (phòng #{hr_dept.id})"
              + (f", dự phòng: #{representative}" if representative else ""))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(run())
