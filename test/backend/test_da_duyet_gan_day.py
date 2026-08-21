"""ĐÃ DUYỆT GẦN ĐÂY — nhìn lại phiếu chính tôi vừa quyết định (CR-115).

Người duyệt ký xong là việc biến khỏi hộp việc, và trước đây không còn đường nào
tìm lại: *"nãy mình vừa ký cái gì?"* là câu không trả lời được nếu không nhớ tên
văn bản mà đi tra từng cái.

Ba chỗ dễ làm sai, và là thứ bộ bài này canh:

  1. đọc từ **dấu vết** chứ không từ bảng việc — dấu vết mới ghi *đã làm gì*;
  2. **ghi ý kiến KHÔNG phải một quyết định** — gộp vào là danh sách đầy những
     dòng người ta chỉ bình luận rồi bỏ đó;
  3. **"tôi đã duyệt" khác "phiếu đã xong"** — ký xong bước của mình mà phiếu
     còn ba bước nữa là chuyện thường, nên phải trả về cả trạng thái phiếu.
"""
import pytest

from app.modules.approval import action_service, instance_service, task_service
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, ApprovalFlow,
                                             ApprovalNode)
from app.modules.approval.instance_model import (ACTION_APPROVE, ACTION_REJECT,
                                                 INSTANCE_APPROVED,
                                                 INSTANCE_RUNNING)
from app.modules.employee.model import Employee

ACTOR = 1
ENTITY = "document"


@pytest.fixture()
def nguoi(db, seed):
    ids = {"nop": seed.emp_req_id}
    for ten in ("a", "b"):
        employee = Employee(code=f"NV_{ten.upper()}", full_name=f"Người {ten.upper()}",
                            company_id=seed.company_id, department_id=seed.dept_id,
                            is_active=True)
        db.add(employee)
        db.flush()
        ids[ten] = employee.id
    db.commit()
    return ids


def _luong(db, entity=ENTITY, code="LUONG-LS"):
    flow = ApprovalFlow(entity=entity, code=code, name="Luồng thử lịch sử",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


def _buoc(db, flow, seq, employee_id, name=None):
    node = ApprovalNode(flow_id=flow.id, seq=seq, name=name or f"Bước {seq}",
                        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(employee_id),
                        created_by=ACTOR, updated_by=ACTOR)
    db.add(node)
    db.commit()
    return node


def _trinh(db, nguoi_nop, entity=ENTITY, entity_id=555, code="VB-555"):
    return instance_service.bat_dau(db, entity, entity_id, {}, nguoi_nop, ACTOR,
                                    entity_code=code, entity_title="Phiếu thử")


def test_duyet_xong_thi_thay_lai_trong_danh_sach(db, seed, nguoi):
    flow = _luong(db)
    _buoc(db, flow, 1, nguoi["a"], name="Trưởng bộ phận duyệt")
    _buoc(db, flow, 2, nguoi["b"])

    instance = _trinh(db, nguoi["nop"])
    action_service.duyet(db, instance, nguoi["a"], ACTOR, {})

    rows = task_service.viec_da_xu_ly(db, nguoi["a"], ENTITY)
    assert len(rows) == 1
    assert rows[0]["entity_code"] == "VB-555"
    assert rows[0]["action"] == ACTION_APPROVE
    assert rows[0]["node_name"] == "Trưởng bộ phận duyệt"
    #  "Tôi đã duyệt" khác "phiếu đã xong": phiếu còn đứng ở bước 2.
    assert rows[0]["instance_status"] == INSTANCE_RUNNING


def test_nguoi_khac_khong_thay_quyet_dinh_cua_toi(db, seed, nguoi):
    flow = _luong(db)
    _buoc(db, flow, 1, nguoi["a"])
    instance = _trinh(db, nguoi["nop"])
    action_service.duyet(db, instance, nguoi["a"], ACTOR, {})

    assert task_service.viec_da_xu_ly(db, nguoi["b"], ENTITY) == []


def test_tu_choi_cung_la_mot_quyet_dinh(db, seed, nguoi):
    """Nhìn lại thì "tôi đã từ chối" cũng quan trọng y như "tôi đã duyệt"."""
    flow = _luong(db)
    _buoc(db, flow, 1, nguoi["a"])
    instance = _trinh(db, nguoi["nop"])
    action_service.tu_choi(db, instance, nguoi["a"], ACTOR, "thiếu căn cứ ở mục 2")

    rows = task_service.viec_da_xu_ly(db, nguoi["a"], ENTITY)
    assert [r["action"] for r in rows] == [ACTION_REJECT]
    assert rows[0]["comment"] == "thiếu căn cứ ở mục 2"


def test_ghi_y_kien_khong_phai_mot_quyet_dinh(db, seed, nguoi):
    """Ý kiến không đổi trạng thái phiếu — gộp vào là danh sách đầy dòng thừa."""
    flow = _luong(db)
    _buoc(db, flow, 1, nguoi["a"])
    instance = _trinh(db, nguoi["nop"])
    action_service.gop_y(db, instance, nguoi["a"], ACTOR, "để mai xem tiếp")

    assert task_service.viec_da_xu_ly(db, nguoi["a"], ENTITY) == []


def test_loc_dung_loai_chung_tu(db, seed, nguoi):
    """Màn Văn bản chỉ hỏi văn bản; việc của Thu mua không được lọt vào."""
    vb = _luong(db, ENTITY, "LS-VB")
    _buoc(db, vb, 1, nguoi["a"])
    action_service.duyet(db, _trinh(db, nguoi["nop"]), nguoi["a"], ACTOR, {})

    po = _luong(db, "purchase_order", "LS-PO")
    _buoc(db, po, 1, nguoi["a"])
    action_service.duyet(db, _trinh(db, nguoi["nop"], "purchase_order", 77, "PO-77"),
                         nguoi["a"], ACTOR, {})

    chi_van_ban = task_service.viec_da_xu_ly(db, nguoi["a"], ENTITY)
    assert [r["entity"] for r in chi_van_ban] == ["document"]
    #  Bỏ trống `entity` thì lấy hết — đường dùng chung cho màn gom mọi loại.
    assert len(task_service.viec_da_xu_ly(db, nguoi["a"], "")) == 2


def test_phieu_duyet_xong_thi_ghi_dung_trang_thai_cuoi(db, seed, nguoi):
    flow = _luong(db)
    _buoc(db, flow, 1, nguoi["a"])
    instance = _trinh(db, nguoi["nop"])
    action_service.duyet(db, instance, nguoi["a"], ACTOR, {})

    assert instance.status == INSTANCE_APPROVED
    rows = task_service.viec_da_xu_ly(db, nguoi["a"], ENTITY)
    assert rows[0]["instance_status"] == INSTANCE_APPROVED
