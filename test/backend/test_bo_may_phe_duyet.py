"""BỘ MÁY PHÊ DUYỆT DÙNG CHUNG — sáu bài nghiệm thu của phase 3.

Sáu bài dưới đây là **điều kiện chuyển phase** ghi trong kế hoạch, không phải
test cho vui. Mỗi bài canh một cách mà bộ máy duyệt biến thành thảm họa:

  1. khai luồng 4 bước bằng dữ liệu, không sửa mã → phiếu chạy đúng qua 4 người;
  2. người ở bước 1 cũng ở bước 3 → tự qua, và nhật ký ghi RÕ là tự qua;
  3. người duyệt nghỉ việc → chuyển người thay, KHÔNG phiếu nào tự duyệt qua;
  4. sửa luồng khi có phiếu đang chạy → phiếu cũ vẫn đi theo luồng cũ;
  5. phiếu không khớp nhánh nào → rơi vào nhánh mặc định, không biến mất;
  6. năm luồng Thu mua vẫn xanh → `test_luong_duyet_thu_mua.py` + `test_po_submit_guard.py`.

Bài 6 không viết lại ở đây: nó chính là hai tệp kia, và điều kiện là chạy cả bộ
vẫn xanh sau khi thêm bộ máy này.
"""
import json
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.modules.approval import (action_service, flow_service,
                                  instance_service)
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE, MULTI_ALL,
                                             NO_APPROVER_FALLBACK, NODE_CC,
                                             SKIP_ADJACENT, SKIP_ANY_BEFORE,
                                             SKIP_NONE, ApprovalFlow,
                                             ApprovalNode, ApprovalSwitch)
from app.modules.approval.instance_model import (ACTION_SKIP_DUPLICATE,
                                                 INSTANCE_APPROVED,
                                                 INSTANCE_BLOCKED,
                                                 INSTANCE_REJECTED,
                                                 INSTANCE_RETURNED,
                                                 INSTANCE_RUNNING,
                                                 INSTANCE_WITHDRAWN,
                                                 TASK_APPROVED, TASK_PENDING,
                                                 TASK_SKIPPED_DUPLICATE,
                                                 TASK_WAITING, ApprovalAction,
                                                 ApprovalTask)
from app.modules.employee.model import Employee

ACTOR = 1
ENTITY = "document"


# ── Dựng cảnh ───────────────────────────────────────────────────────────────

@pytest.fixture()
def person(db, seed):
    """Sáu nhân sự đủ để khai một luồng bốn bước."""
    ids = {"nop": seed.emp_req_id}
    for name in ("a", "b", "c", "d", "du_phong"):
        employee = Employee(code=f"NV_{name.upper()}", full_name=f"Người {name.upper()}",
                            company_id=seed.company_id, department_id=seed.dept_id,
                            is_active=True)
        db.add(employee)
        db.flush()
        ids[name] = employee.id
    db.commit()
    return ids


def _luong(db, code="LUONG-01", **kw) -> ApprovalFlow:
    flow = ApprovalFlow(entity=ENTITY, code=code, name=kw.pop("name", "Luồng thử"),
                        is_active=True, created_by=ACTOR, updated_by=ACTOR, **kw)
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


def _buoc(db, flow, seq, employee_id=None, **kw) -> ApprovalNode:
    node = ApprovalNode(
        flow_id=flow.id, seq=seq, name=kw.pop("name", f"Bước {seq}"),
        approver_kind=kw.pop("approver_kind", APPROVER_EMPLOYEE),
        approver_ref=kw.pop("approver_ref", str(employee_id or "")),
        skip_duplicate=kw.pop("skip_duplicate", SKIP_NONE),
        created_by=ACTOR, updated_by=ACTOR, **kw,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


def _trinh(db, flow_khong_dung=None, subject=None, submitter=None, entity_id=101):
    return instance_service.start(
        db, ENTITY, entity_id, subject or {}, submitter, ACTOR,
        entity_code="VB-001", entity_title="Quy chế thử",
    )


def _dang_cho(db, instance) -> list[ApprovalTask]:
    return [row for row in instance_service.tasks_of_instance(db, instance.id)
            if row.status == TASK_PENDING]


# ── Bài 1 · khai luồng bằng dữ liệu, phiếu chạy đủ bốn người ────────────────

def test_bai1_luong_bon_buoc_chay_dung_qua_bon_nguoi(db, seed, person):
    """Khai luồng bằng DỮ LIỆU, không sửa dòng mã nào, không deploy lại."""
    flow = _luong(db)
    for seq, name in enumerate(("a", "b", "c", "d"), start=1):
        _buoc(db, flow, seq, person[name])

    instance = _trinh(db, submitter=person["nop"])
    assert instance.status == INSTANCE_RUNNING

    da_di_qua = []
    for name in ("a", "b", "c", "d"):
        cho = _dang_cho(db, instance)
        assert len(cho) == 1, f"Bước của {name} phải có đúng một người chờ"
        da_di_qua.append(cho[0].assignee_employee_id)
        action_service.approve(db, instance, person[name], ACTOR, {})

    assert da_di_qua == [person["a"], person["b"], person["c"], person["d"]]
    assert instance.status == INSTANCE_APPROVED


def test_bai1_khong_co_luong_nao_thi_tra_none_de_goi_duong_cu(db, seed):
    """Chưa khai luồng = bộ máy đứng ngoài, người gọi quay về đường duyệt cũ."""
    assert _trinh(db) is None


def test_luong_rieng_phap_nhan_thang_luong_dung_chung_du_uu_tien_thap_hon(
        db, seed, person):
    """Bản clone phải vào luồng của nơi nhận, không theo luồng chung của gốc."""
    dung_chung = _luong(db, code="VB-CHUNG", priority=999)
    _buoc(db, dung_chung, 1, person["a"])
    specific = _luong(db, code="VB-CONG-TY-CON", company_id=88, priority=0)
    _buoc(db, specific, 1, person["b"])

    instance = _trinh(db, subject={"company_id": 88}, submitter=person["nop"])

    assert instance.flow_id == specific.id
    assert [row.assignee_employee_id for row in _dang_cho(db, instance)] == [person["b"]]


def test_khong_co_luong_rieng_thi_moi_dung_luong_dung_chung(db, seed, person):
    dung_chung = _luong(db, code="VB-CHUNG")
    _buoc(db, dung_chung, 1, person["a"])

    instance = _trinh(db, subject={"company_id": 99}, submitter=person["nop"])

    assert instance.flow_id == dung_chung.id
    assert flow_service.pick_flow(
        db, ENTITY, {"company_id": 99}, company_only=True,
    ) is None


# ── Bài 2 · trùng người thì tự qua, và nói rõ là tự qua ─────────────────────

def test_bai2_trung_nguoi_thi_tu_qua_va_ghi_ro_ly_do(db, seed, person):
    """Người ở bước 1 cũng là người ở bước 3 → bước 3 tự qua.

    ⚠️ Việc tự qua mang TRẠNG THÁI RIÊNG, không phải "đã duyệt". Bản in dấu vết
    phải phân biệt *người này đã ký* với *bước này tự qua vì trùng người* — gộp
    làm một là bản in nói dối rằng có thêm một người đã xem xét.
    """
    flow = _luong(db)
    _buoc(db, flow, 1, person["a"])
    _buoc(db, flow, 2, person["b"])
    _buoc(db, flow, 3, person["a"], skip_duplicate=SKIP_ANY_BEFORE)

    instance = _trinh(db, submitter=person["nop"])
    action_service.approve(db, instance, person["a"], ACTOR, {})
    action_service.approve(db, instance, person["b"], ACTOR, {})

    buoc3 = [row for row in instance_service.tasks_of_instance(db, instance.id)
             if row.node_seq == 3]
    assert [row.status for row in buoc3] == [TASK_SKIPPED_DUPLICATE]
    assert instance.status == INSTANCE_APPROVED

    dau_vet = db.query(ApprovalAction).filter(
        ApprovalAction.instance_id == instance.id,
        ApprovalAction.action == ACTION_SKIP_DUPLICATE).all()
    assert len(dau_vet) == 1
    #  Dấu vết phải NÓI RA vì sao bước này không có chữ ký — đọc lại sau một năm
    #  mà chỉ thấy một bước trống thì không ai biết là cố ý hay bị bỏ sót.
    assert "tự qua" in dau_vet[0].comment.lower()


def test_bai2_chi_bo_qua_buoc_lien_truoc_thi_khong_bo_buoc_xa(db, seed, person):
    """`SKIP_ADJACENT` chỉ nhìn bước liền trước — bước 3 vẫn phải bấm."""
    flow = _luong(db)
    _buoc(db, flow, 1, person["a"])
    _buoc(db, flow, 2, person["b"])
    _buoc(db, flow, 3, person["a"], skip_duplicate=SKIP_ADJACENT)

    instance = _trinh(db, submitter=person["nop"])
    action_service.approve(db, instance, person["a"], ACTOR, {})
    action_service.approve(db, instance, person["b"], ACTOR, {})

    assert [row.assignee_employee_id for row in _dang_cho(db, instance)] == [person["a"]]


# ── Bài 3 · không có người duyệt thì KHÔNG tự động duyệt qua ────────────────

def test_bai3_nguoi_duyet_nghi_viec_thi_chuyen_nguoi_du_phong(db, seed, person):
    flow = _luong(db)
    _buoc(db, flow, 1, person["a"], on_no_approver=NO_APPROVER_FALLBACK,
          fallback_employee_id=person["du_phong"])

    db.get(Employee, person["a"]).is_active = False
    db.commit()

    instance = _trinh(db, submitter=person["nop"])

    assert [row.assignee_employee_id for row in _dang_cho(db, instance)] == [person["du_phong"]]
    assert instance.status == INSTANCE_RUNNING


def test_bai3_khong_ai_duyet_va_khong_du_phong_thi_KET_chu_khong_tu_duyet(db, seed, person):
    """⚠️ Bài quan trọng nhất của nhóm này.

    Lark có tùy chọn "không có người duyệt thì tự động duyệt qua". Bộ máy này
    **cố ý không khai giá trị đó** — với văn bản, nó tạo ra văn bản CÓ HIỆU LỰC
    mà không ai chịu trách nhiệm. Phiếu phải KẸT và còn hiện trên màn quản trị,
    chứ không được lặng lẽ đi tiếp.
    """
    flow = _luong(db)
    _buoc(db, flow, 1, person["a"])
    _buoc(db, flow, 2, person["b"])

    db.get(Employee, person["a"]).is_active = False
    db.commit()

    instance = _trinh(db, submitter=person["nop"])

    assert instance.status == INSTANCE_BLOCKED
    assert instance.status != INSTANCE_APPROVED
    assert "không tìm được người duyệt" in instance.finish_reason.lower()


def test_bai3_nguoi_nop_khong_tu_duyet_phieu_cua_minh(db, seed, person):
    """I08 — bước chỉ có mỗi người nộp thì không tự ký cho xong được."""
    flow = _luong(db)
    _buoc(db, flow, 1, person["nop"])

    instance = _trinh(db, submitter=person["nop"])

    assert instance.status == INSTANCE_BLOCKED


# ── Bài 4 · sửa luồng khi phiếu đang chạy ───────────────────────────────────

def test_bai4_sua_luong_khong_lam_hong_phieu_dang_chay(db, seed, person):
    """Phiếu chạy theo BẢN CHỤP của chính nó (`flow_snapshot`).

    Đọc bảng bước lúc chạy thì người quản trị xóa một bước là phiếu đang đứng ở
    đó mất đích tới — và nó biến mất khỏi mọi danh sách.
    """
    flow = _luong(db)
    _buoc(db, flow, 1, person["a"])
    buoc2 = _buoc(db, flow, 2, person["b"])

    instance = _trinh(db, submitter=person["nop"])

    #  Quản trị sửa luồng giữa chừng: xóa bước 2, thêm bước 3 cho người khác.
    db.delete(buoc2)
    db.commit()
    _buoc(db, flow, 3, person["c"])
    flow.version_no = 2
    db.commit()

    action_service.approve(db, instance, person["a"], ACTOR, {})

    #  Phiếu cũ vẫn đi tới người B của bản 1, không nhảy sang người C của bản 2.
    assert [row.assignee_employee_id for row in _dang_cho(db, instance)] == [person["b"]]

    action_service.approve(db, instance, person["b"], ACTOR, {})
    assert instance.status == INSTANCE_APPROVED


def test_bai4_phieu_moi_di_theo_luong_da_sua(db, seed, person):
    flow = _luong(db)
    _buoc(db, flow, 1, person["a"])
    old = _trinh(db, submitter=person["nop"], entity_id=201)
    assert json.loads(old.flow_snapshot)["nodes"][0]["approver_ref"] == str(person["a"])

    db.query(ApprovalNode).filter(ApprovalNode.flow_id == flow.id).delete()
    db.commit()
    _buoc(db, flow, 1, person["c"])

    new = _trinh(db, submitter=person["nop"], entity_id=202)
    assert [row.assignee_employee_id for row in _dang_cho(db, new)] == [person["c"]]


# ── Bài 5 · nhánh mặc định — cột chống mất phiếu ────────────────────────────

def test_bai5_phieu_khong_khop_nhanh_nao_roi_vao_nhanh_mac_dinh(db, seed, person):
    """Không có nhánh mặc định thì phiếu rơi vào khoảng không: không nhánh nào
    nhận, biến mất khỏi mọi danh sách, tới lúc có người đi hỏi mới phát hiện."""
    flow = _luong(db)
    _buoc(db, flow, 1, person["a"], branch_key="to",
          condition=json.dumps([{"field": "total", "op": "gte", "value": 50000000}]))
    _buoc(db, flow, 1, person["b"], branch_key="mac_dinh", is_default_branch=True)

    instance = _trinh(db, subject={"total": 1000}, submitter=person["nop"])

    assert instance.status == INSTANCE_RUNNING
    assert [row.assignee_employee_id for row in _dang_cho(db, instance)] == [person["b"]]


def test_bai5_khop_dieu_kien_thi_di_dung_nhanh_do(db, seed, person):
    flow = _luong(db)
    _buoc(db, flow, 1, person["a"], branch_key="to",
          condition=json.dumps([{"field": "total", "op": "gte", "value": 50000000}]))
    _buoc(db, flow, 1, person["b"], branch_key="mac_dinh", is_default_branch=True)

    instance = _trinh(db, subject={"total": 90000000}, submitter=person["nop"])

    assert [row.assignee_employee_id for row in _dang_cho(db, instance)] == [person["a"]]


def test_bai5_thieu_nhanh_mac_dinh_thi_phieu_KET_chu_khong_bien_mat(db, seed, person):
    """Khai thiếu nhánh mặc định là lỗi cấu hình — phiếu phải kẹt ra mặt."""
    flow = _luong(db)
    _buoc(db, flow, 1, person["a"], branch_key="to",
          condition=json.dumps([{"field": "total", "op": "gte", "value": 50000000}]))
    _buoc(db, flow, 1, person["b"], branch_key="nho",
          condition=json.dumps([{"field": "total", "op": "lte", "value": 100}]))

    instance = _trinh(db, subject={"total": 1000}, submitter=person["nop"])

    assert instance.status == INSTANCE_BLOCKED
    assert "nhánh mặc định" in instance.finish_reason


# ── Cờ bật/tắt — đường lui của cả phase ─────────────────────────────────────

def test_co_mac_dinh_la_TAT(db, seed):
    """Thêm bảng mới không được đổi hành vi của thứ đang chạy."""
    assert flow_service.is_enabled(db, ENTITY) is False


def test_bat_co_thi_bo_may_moi_vao_cuoc(db, seed):
    db.add(ApprovalSwitch(entity=ENTITY, is_enabled=True, created_by=ACTOR, updated_by=ACTOR))
    db.commit()
    assert flow_service.is_enabled(db, ENTITY) is True
    assert flow_service.is_enabled(db, "purchase_request") is False


# ── Thứ tự đăng ký route ────────────────────────────────────────────────────

def test_duong_dan_tinh_dang_ky_truoc_route_dong():
    """Cùng cái bẫy đã giết ba endpoint văn bản ngày 17/08.

    `/api/approvals/my-tasks` và `/api/approvals/handover` là đường TĨNH; đăng ký
    sau `/{instance_id}` thì bị nuốt và chết ở bước ép kiểu số nguyên — trả
    **422 chứ không phải 404**, nên nhìn log cũng không nghĩ ngay tới định tuyến.
    """
    from app.main import app

    PREFIX = "/api/approvals"
    vi_tri_dong = next(
        (i for i, route in enumerate(app.routes)
         if getattr(route, "path", "") == PREFIX + "/{instance_id}"), None)
    assert vi_tri_dong is not None

    borrowed = [
        route.path for i, route in enumerate(app.routes)
        if i > vi_tri_dong and getattr(route, "path", "").startswith(PREFIX + "/")
        and len(route.path[len(PREFIX) + 1:].split("/")) == 1
        and "{" not in route.path[len(PREFIX) + 1:]
    ]
    assert borrowed == [], f"Các đường dẫn tĩnh này bị /{{instance_id}} nuốt: {borrowed}"


def test_cau_truy_van_viec_cua_toi_khong_dung_NULLS_LAST(db, seed):
    """Lỗi 17/08: `.nulls_last()` chạy ngon trên SQLite nhưng MySQL 8 KHÔNG hiểu.

    Cả bộ kiểm này chạy SQLite nên không có bài nào bắt được — màn «Việc của
    tôi» trả 500 ngay lần gọi thật đầu tiên. Nên canh bằng cách soi thẳng câu
    SQL sinh ra, thứ duy nhất kiểm được mà không cần MySQL.
    """
    from sqlalchemy.dialects import mysql

    from app.modules.approval.instance_model import ApprovalTask

    message = str(
        db.query(ApprovalTask)
        .order_by(ApprovalTask.due_at.is_(None), ApprovalTask.due_at.asc(),
                  ApprovalTask.id.asc())
        .statement.compile(dialect=mysql.dialect())
    ).upper()
    assert "NULLS LAST" not in message


# ── Kéo thả đổi thứ tự các bước ─────────────────────────────────────────────

def test_doi_thu_tu_buoc_khong_dam_vao_rang_buoc_duy_nhat(db, seed, person, grant_role):
    """Hoán vị hai chặng phải đi HAI LƯỢT.

    `UNIQUE(flow_id, seq, branch_key)` nổ ngay giữa chừng nếu gán thẳng: có một
    khoảnh khắc hai bước cùng mang `seq = 1`. Bài này canh đúng chỗ đó.
    """
    from app.modules.approval.flow_controller import ReorderIn, reorder_nodes

    grant_role(ACTOR, "approval_flow", write=True)   # B-07: sửa luồng phải có grant thật
    flow = _luong(db, code="LUONG-DND")
    a = _buoc(db, flow, 1, person["a"])
    b = _buoc(db, flow, 2, person["b"])

    reorder_nodes(flow.id, ReorderIn(stages=[[b.id], [a.id]]), db=db,
                  user=SimpleNamespace(id=ACTOR))

    db.refresh(a)
    db.refresh(b)
    assert (b.seq, a.seq) == (1, 2)


def test_gop_hai_buoc_vao_cung_mot_chang_thi_tach_nhanh_khac_nhau(db, seed, person, grant_role):
    """Hai nhánh song song phải khác `branch_key`, nếu không cũng đâm ràng buộc.

    Đánh lại theo vị trí thay vì tin giá trị cũ — kéo một bước từ chặng khác
    sang là trùng ngay.
    """
    from app.modules.approval.flow_controller import ReorderIn, reorder_nodes

    grant_role(ACTOR, "approval_flow", write=True)
    flow = _luong(db, code="LUONG-NHANH")
    a = _buoc(db, flow, 1, person["a"])
    b = _buoc(db, flow, 2, person["b"])

    reorder_nodes(flow.id, ReorderIn(stages=[[a.id, b.id]]), db=db,
                  user=SimpleNamespace(id=ACTOR))

    db.refresh(a)
    db.refresh(b)
    assert a.seq == b.seq == 1
    assert a.branch_key != b.branch_key


def test_doi_thu_tu_thi_luong_len_ban_moi(db, seed, person, grant_role):
    """Phiếu ĐANG chạy giữ bản chụp riêng nên không bị ảnh hưởng — nhưng số bản
    vẫn phải tăng, không thì hai luồng khác hẳn nhau cùng mang một số."""
    from app.modules.approval.flow_controller import ReorderIn, reorder_nodes

    grant_role(ACTOR, "approval_flow", write=True)
    flow = _luong(db, code="LUONG-BAN")
    a = _buoc(db, flow, 1, person["a"])
    ban_cu = flow.version_no

    reorder_nodes(flow.id, ReorderIn(stages=[[a.id]]), db=db, user=SimpleNamespace(id=ACTOR))

    db.refresh(flow)
    assert flow.version_no > ban_cu
