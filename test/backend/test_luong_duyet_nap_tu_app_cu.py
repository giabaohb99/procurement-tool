"""Dải chấm + câu tóm tắt cho phiên duyệt NẠP TỪ APP CŨ.

Phiên do bộ máy ERP mở luôn có việc `TASK_PENDING` ở chặng đang chờ, nên dải chấm
đọc bảng việc là đủ. Phiên nạp từ app đặt xe cũ thì KHÔNG: người ta vẫn bấm duyệt
bên app cũ, còn `scripts/legacy_sync/import_approval_history.py` chỉ dựng được
việc cho những chặng ĐÃ KÝ (chặng chưa ký không có dòng nào trong `history`).

Hậu quả thật, phiếu DD000864 ngày 19/09/2026: phiếu đã ký chặng 1, đang chờ Pháp
chế ở chặng 3, mà ERP không chặng nào sáng lên và câu tóm tắt rơi về «Đang chạy» —
trong khi app cũ lại gọi cùng phiếu đó là «Đã Duyệt» (nó đặt tên trạng thái theo
chặng đang chờ). Hai màn hình, hai câu chuyện, cùng một tờ phiếu.
"""
import json
from datetime import datetime

import pytest

from app.modules.approval import steps_service
from app.modules.approval.flow_model import (APPROVER_ROLE, MULTI_ANY,
                                             NODE_APPROVAL, NODE_CC,
                                             NO_APPROVER_BLOCK, ROLE_APPROVE,
                                             SKIP_NONE)
from app.modules.approval.instance_model import (INSTANCE_APPROVED, INSTANCE_RUNNING,
                                                 TASK_APPROVED, TASK_CANCELLED,
                                                 ApprovalInstance, ApprovalTask)
from app.modules.employee.model import Employee

ACTOR = 1
ENTITY = "seal_request"
#  Ba chặng đúng như luồng đóng dấu của app cũ: TBP → Ban giám đốc → Pháp chế.
STEP_NAMES = {1: "Duyệt của Trưởng bộ phận", 2: "Duyệt của Ban giám đốc",
              3: "Duyệt Brand & Pháp chế"}


def _node(seq: int, name: str, *, node_kind: int = NODE_APPROVAL) -> dict:
    return {
        "id": 0, "seq": seq, "branch_key": "", "name": name,
        "node_kind": node_kind, "flow_role": ROLE_APPROVE,
        "approver_kind": APPROVER_ROLE, "approver_ref": "Legal",
        "multi_mode": MULTI_ANY, "quorum_percent": 50, "condition": "",
        "is_default_branch": False, "skip_duplicate": SKIP_NONE, "sla_hours": 0,
        "fallback_employee_id": None, "on_no_approver": NO_APPROVER_BLOCK,
    }


def _snapshot(*nodes: dict) -> str:
    return json.dumps({"flow_id": 0, "code": "wf-dongdau", "name": "Đóng dấu",
                       "version_no": 0, "nodes": list(nodes)}, ensure_ascii=False)


@pytest.fixture()
def signer(db):
    obj = Employee(code="TBP", full_name="Trưởng bộ phận", company_id=1,
                   department_id=7, is_active=True)
    db.add(obj)
    db.flush()
    return obj


def _legacy_instance(db, entity_id: int, *, current_seq: int, signed_until: int,
                     signer_id: int, status: int = INSTANCE_RUNNING,
                     nodes: list[dict] | None = None) -> ApprovalInstance:
    """Phiên y như bản nạp: `flow_id = 0`, việc CHỈ có ở những chặng đã ký."""
    inst = ApprovalInstance(
        entity=ENTITY, entity_id=entity_id, entity_code=f"DD{entity_id:06d}",
        entity_title="HĐ testa", flow_id=0, flow_version=0,
        flow_snapshot=_snapshot(*(nodes or [_node(s, STEP_NAMES[s]) for s in (1, 2, 3)])),
        status=status, current_seq=current_seq, started_by_employee_id=signer_id,
        started_at=datetime(2026, 9, 19, 8, 2), created_by=ACTOR, updated_by=ACTOR)
    db.add(inst)
    db.flush()
    for seq in range(1, signed_until + 1):
        db.add(ApprovalTask(instance_id=inst.id, node_seq=seq, node_name=STEP_NAMES[seq],
                            order_no=1, assignee_employee_id=signer_id,
                            status=TASK_APPROVED,
                            decided_at=datetime(2026, 9, 19, 8, 2, 56),
                            created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    return inst


def _flow(db, entity_id: int) -> dict:
    return steps_service.steps_of_entities(db, ENTITY, [entity_id])[entity_id]


# ══════════════════════════════════════════════════════════════════════════════
#  Chặng đang chờ phải sáng lên dù bảng việc trống
# ══════════════════════════════════════════════════════════════════════════════

def test_chang_chua_co_viec_nhung_dung_chang_dang_cho_thi_SANG_LEN(db, signer):
    """Đúng ca DD000864: ký chặng 1, đang chờ chặng 3, bảng việc không có chặng 3."""
    _legacy_instance(db, 864, current_seq=3, signed_until=1, signer_id=signer.id)
    flow = _flow(db, 864)

    assert [s["state"] for s in flow["steps"]] == [
        steps_service.STEP_DONE, steps_service.STEP_TODO, steps_service.STEP_CURRENT]


def test_cau_tom_tat_goi_TEN_CHANG_khi_khong_biet_ten_nguoi(db, signer):
    """«Đang ở chặng 3/3» một mình thì đúng nhưng vô dụng — người xem vẫn phải mở
    phiếu ra mới biết đang kẹt ở đâu. Việc duyệt còn nằm bên app cũ nên ERP không
    có ai được giao để mà kể tên."""
    _legacy_instance(db, 864, current_seq=3, signed_until=1, signer_id=signer.id)

    assert _flow(db, 864)["summary"] == "Đang ở chặng 3/3 · Duyệt Brand & Pháp chế"


def test_chang_bi_TRA_VE_roi_nop_lai_dung_chang_do_thi_sang_lai(db, signer):
    """DD000865: Pháp chế trả về cho sửa, người nộp sửa rồi gửi lại đúng chặng 3.

    Bản nạp ghi lượt cũ thành việc ĐÃ HỦY, mà phiên thì vẫn đang chạy. Đọc mỗi
    bảng việc thì chặng 3 hiện «đã hủy» — người xem đọc ra phiếu chết, trong khi
    phiếu đang nằm chờ đúng chặng đó.
    """
    inst = _legacy_instance(db, 869, current_seq=3, signed_until=1, signer_id=signer.id)
    db.add(ApprovalTask(instance_id=inst.id, node_seq=3, node_name=STEP_NAMES[3],
                        order_no=1, assignee_employee_id=signer.id,
                        status=TASK_CANCELLED, decided_at=datetime(2026, 9, 18, 3, 0),
                        created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    flow = _flow(db, 869)

    assert flow["steps"][2]["state"] == steps_service.STEP_CURRENT
    assert flow["summary"] == "Đang ở chặng 3/3 · Duyệt Brand & Pháp chế"


def test_chang_da_ky_thi_current_seq_khong_noi_nguoc_lai_duoc(db, signer):
    """`current_seq` lệch (bản nạp lấy thẳng `currentLevel` của app cũ) không
    được phép biến một chặng đã ký thành chặng đang chờ."""
    _legacy_instance(db, 870, current_seq=1, signed_until=1, signer_id=signer.id)

    assert _flow(db, 870)["steps"][0]["state"] == steps_service.STEP_DONE


def test_chang_chua_toi_luot_van_la_TODO_chu_khong_sang_theo(db, signer):
    """Chỉ ĐÚNG MỘT chặng được sáng. Sáng cả cụm thì dải chấm hết ý nghĩa."""
    _legacy_instance(db, 865, current_seq=2, signed_until=1, signer_id=signer.id)
    states = [s["state"] for s in _flow(db, 865)["steps"]]

    assert states.count(steps_service.STEP_CURRENT) == 1
    assert states[2] == steps_service.STEP_TODO


def test_phieu_da_duyet_xong_thi_KHONG_chang_nao_sang(db, signer):
    """`current_seq` của phiên đã xong vẫn trỏ vào chặng cuối. Lấy nó ra vẽ thì
    phiếu duyệt xong đọc thành phiếu còn đang chờ chữ ký."""
    _legacy_instance(db, 866, current_seq=3, signed_until=3, signer_id=signer.id,
                     status=INSTANCE_APPROVED)
    flow = _flow(db, 866)

    assert steps_service.STEP_CURRENT not in [s["state"] for s in flow["steps"]]
    assert flow["summary"] == "Đã duyệt đủ 3/3 chặng"


def test_current_seq_tro_ra_ngoai_ban_chup_thi_khong_no(db, signer):
    """Bản chụp của app cũ thiếu bước, hoặc `currentLevel` vượt số chặng — phải
    ra một dải chấm không chặng nào sáng, không được vỡ."""
    _legacy_instance(db, 867, current_seq=9, signed_until=1, signer_id=signer.id)
    flow = _flow(db, 867)

    assert [s["seq"] for s in flow["steps"]] == [1, 2, 3]
    assert steps_service.STEP_CURRENT not in [s["state"] for s in flow["steps"]]


def test_cau_tom_tat_ca_trang_van_chi_ton_BA_truy_van(db, signer):
    """Câu tóm tắt đi kèm MỌI dòng của màn danh sách, nên nó phải phẳng.

    `summaries_of_entities` là cửa mà bốn hàm dựng dữ liệu của Duyệt dấu và Đặt
    xe gọi vào. Đặt một truy vấn trong vòng lặp ở đây là mỗi dòng danh sách một
    lượt vào cơ sở dữ liệu — hai mươi dòng thành hơn sáu mươi lượt, đúng cái
    `steps_service` sinh ra để tránh. Ba là TRẦN CỨNG, không phải số đo tham
    khảo: phiên + việc + tên người, không thêm gì nữa.
    """
    from sqlalchemy import event

    ids = list(range(900, 930))
    for entity_id in ids:
        _legacy_instance(db, entity_id, current_seq=3, signed_until=1, signer_id=signer.id)

    counted: list[str] = []

    def _count(conn, cursor, statement, *args):
        counted.append(statement)

    event.listen(db.get_bind(), "before_cursor_execute", _count)
    try:
        summaries = steps_service.summaries_of_entities(db, ENTITY, ids)
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", _count)

    assert len(summaries) == len(ids)
    assert len(counted) <= 3, f"Đã quay lại N+1: {len(counted)} truy vấn cho {len(ids)} dòng"


def test_buoc_nhan_ban_sao_khong_bao_gio_thanh_chang_dang_cho(db, signer):
    """`NODE_CC` không chặn ai. Đếm nó vào là bịa ra một chặng phải chờ."""
    nodes = [_node(1, STEP_NAMES[1]),
             _node(2, "Gửi bản sao Kế toán", node_kind=NODE_CC),
             _node(3, STEP_NAMES[3])]
    _legacy_instance(db, 868, current_seq=2, signed_until=1, signer_id=signer.id,
                     nodes=nodes)
    flow = _flow(db, 868)

    assert [s["seq"] for s in flow["steps"]] == [1, 3]
    assert steps_service.STEP_CURRENT not in [s["state"] for s in flow["steps"]]
