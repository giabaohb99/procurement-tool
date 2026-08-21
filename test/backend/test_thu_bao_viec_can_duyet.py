"""THƯ BÁO «có việc chờ bạn duyệt» — bộ máy duyệt phải tự gọi người.

Trước đây bộ máy **không báo cho ai cả**: việc rơi vào hộp «Việc của tôi» và nằm
im tới khi người duyệt tự nhớ ra mà mở hộp. Với văn bản, đó là văn bản nằm chết
giữa luồng còn người trình thì không biết phải giục ai.

Bốn ca canh ở đây đều là ca im lặng gây mất phiếu:

  1. mở chặng → người duyệt có thư, và thư dẫn thẳng tới văn bản;
  2. bước «lần lượt» → CHỈ người đầu có thư, người sau nhận khi tới lượt
     (báo cả hàng là ba người lao vào bấm khi chưa tới lượt mình);
  3. người được ỦY QUYỀN cũng phải có thư — việc mang tên người đi vắng;
  4. người duyệt không có tài khoản → không được làm hỏng phiên duyệt.
"""
from datetime import date

import pytest

from app.modules.approval import action_service, instance_service
from app.modules.approval.delegation_model import Delegation
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE,
                                             MULTI_SEQUENTIAL, ApprovalFlow,
                                             ApprovalNode)
from app.modules.employee.model import Employee
from app.modules.notification.model import Notification
from app.modules.user.model import User

ACTOR = 1
ENTITY = "document"
DOCUMENT_ID = 731


@pytest.fixture()
def nguoi(db, seed):
    """Ba người duyệt, mỗi người một tài khoản để nhận được thư."""
    ids = {"nop": seed.emp_req_id}
    for ten in ("a", "b", "khong_tai_khoan"):
        employee = Employee(code=f"NV_{ten.upper()}", full_name=f"Người {ten.upper()}",
                            company_id=seed.company_id, department_id=seed.dept_id,
                            is_active=True)
        db.add(employee)
        db.flush()
        ids[ten] = employee.id
        #  Người thứ ba CỐ Ý không có tài khoản — xem bài 4.
        if ten != "khong_tai_khoan":
            db.add(User(email=f"USER_{ten.upper()}", employee_id=employee.id,
                        password_hash="x", is_active=True))
    db.commit()
    return ids


def _luong(db, code="LUONG-THU"):
    flow = ApprovalFlow(entity=ENTITY, code=code, name="Luồng thử thư báo",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


def _buoc(db, flow, seq, employee_ids, **kw):
    node = ApprovalNode(
        flow_id=flow.id, seq=seq, name=kw.pop("name", f"Bước {seq}"),
        approver_kind=APPROVER_EMPLOYEE,
        approver_ref=",".join(str(row) for row in employee_ids),
        created_by=ACTOR, updated_by=ACTOR, **kw,
    )
    db.add(node)
    db.commit()
    return node


def _trinh(db, nguoi_nop):
    return instance_service.bat_dau(
        db, ENTITY, DOCUMENT_ID, {}, nguoi_nop, ACTOR,
        entity_code="VB-731", entity_title="Quy chế bảo mật",
    )


def _thu_cua(db, employee_id) -> list[Notification]:
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if user is None:
        return []
    return db.query(Notification).filter(Notification.user_id == user.id).all()


def test_mo_chang_thi_nguoi_duyet_co_thu_dan_thang_toi_van_ban(db, seed, nguoi):
    flow = _luong(db)
    _buoc(db, flow, 1, [nguoi["a"]], name="Trưởng bộ phận duyệt")

    _trinh(db, nguoi["nop"])

    thu = _thu_cua(db, nguoi["a"])
    assert len(thu) == 1, "Người đang giữ việc phải nhận đúng một thư"
    assert "Quy chế bảo mật" in thu[0].title
    assert "Trưởng bộ phận duyệt" in thu[0].body
    #  Link phải là đường của app v2 — `toAppPath()` bên giao diện giữ nguyên
    #  tiền tố `/document`. Ghi sai kiểu là bấm vào thông báo không đi đâu cả.
    assert thu[0].link == f"/document/documents/{DOCUMENT_ID}"


def test_nguoi_khong_lien_quan_khong_nhan_thu(db, seed, nguoi):
    flow = _luong(db)
    _buoc(db, flow, 1, [nguoi["a"]])
    _buoc(db, flow, 2, [nguoi["b"]])

    _trinh(db, nguoi["nop"])

    #  B đứng ở chặng 2, chưa tới lượt — báo sớm là làm loãng chính cái thư sẽ
    #  gửi khi tới lượt họ thật.
    assert _thu_cua(db, nguoi["b"]) == []


def test_buoc_lan_luot_chi_bao_nguoi_dang_toi_luot(db, seed, nguoi):
    flow = _luong(db)
    _buoc(db, flow, 1, [nguoi["a"], nguoi["b"]], multi_mode=MULTI_SEQUENTIAL)

    instance = _trinh(db, nguoi["nop"])
    assert len(_thu_cua(db, nguoi["a"])) == 1
    assert _thu_cua(db, nguoi["b"]) == [], "Người xếp sau chưa tới lượt thì chưa báo"

    action_service.duyet(db, instance, nguoi["a"], ACTOR, {})

    assert len(_thu_cua(db, nguoi["b"])) == 1, "Tới lượt ai thì báo người đó"


def test_nguoi_duoc_uy_quyen_cung_nhan_thu_va_thu_noi_ro_bam_thay(db, seed, nguoi):
    """Việc mang tên người ĐI VẮNG — báo mỗi họ là thư rơi vào hộp không ai đọc."""
    db.add(Delegation(
        from_employee_id=nguoi["a"], to_employee_id=nguoi["b"], entity="",
        from_date=date(2020, 1, 1), to_date=date(2099, 12, 31), is_active=True,
        created_by=ACTOR, updated_by=ACTOR,
    ))
    db.commit()

    flow = _luong(db)
    _buoc(db, flow, 1, [nguoi["a"]])

    _trinh(db, nguoi["nop"])

    thu_nguoi_thay = _thu_cua(db, nguoi["b"])
    assert len(thu_nguoi_thay) == 1
    #  Ký thay người khác là việc khác hẳn ký cho mình, và nhật ký ghi cả hai
    #  tên — nói ra trong thư chứ không để họ biết sau khi đã bấm.
    assert "THAY" in thu_nguoi_thay[0].body
    assert "Người A" in thu_nguoi_thay[0].body
    #  Người gốc vẫn nhận thư của mình: ủy quyền không chuyển việc đi đâu cả.
    assert len(_thu_cua(db, nguoi["a"])) == 1


def test_nguoi_duyet_khong_co_tai_khoan_thi_phien_van_chay(db, seed, nguoi):
    """Không gửi được thư KHÔNG được phép làm hỏng việc duyệt.

    Mất phiếu vì không gửi nổi một cái thư thì tệ hơn nhiều so với thiếu thư.
    """
    flow = _luong(db)
    _buoc(db, flow, 1, [nguoi["khong_tai_khoan"]])

    instance = _trinh(db, nguoi["nop"])

    assert instance is not None
    cho = [row for row in instance_service.viec_cua_phien(db, instance.id)]
    assert [row.assignee_employee_id for row in cho] == [nguoi["khong_tai_khoan"]]
