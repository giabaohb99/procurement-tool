"""SỬA NGƯỜI DUYỆT TRONG LUỒNG → PHIẾU ĐANG CHẠY BÁM THEO (CR-114).

Trước đây phiếu chạy theo **bản chụp luồng** lúc nó bắt đầu, kể cả ô *ai duyệt
bước này*. Người dùng đổi người duyệt trong màn Luồng duyệt rồi mở phiếu ra xem
— vẫn tên người cũ, không có đường nào sửa. Với họ đó là "sửa không ăn".

Ranh giới của khe vừa mở, và là thứ bộ bài này canh:

  1. bước ĐANG CHỜ → việc chuyển sang người mới, người cũ mất việc;
  2. bước CHƯA TỚI → tới lượt thì tính theo người mới;
  3. bước ĐÃ KÝ → tuyệt đối không đụng, chữ ký là chuyện đã rồi;
  4. phiếu đang KẸT → hồi sinh khi bước đó nay tìm được người duyệt;
  5. sửa xong mà không còn ai duyệt được → phiếu KẸT, không tự đi tiếp.

Bài cuối canh việc **bỏ nhánh «đẩy lên cấp trên»**: đó là chỗ duy nhất bộ máy
tự chọn một người không có tên trong luồng.
"""
import pytest

from app.modules.approval import (action_service, entity_hooks,
                                  flow_sync_service, instance_service)
from app.modules.approval.flow_model import (APPROVER_EMPLOYEE,
                                             NO_APPROVER_BLOCK,
                                             NO_APPROVER_ESCALATE,
                                             ApprovalFlow, ApprovalNode)
from app.modules.approval.instance_model import (INSTANCE_BLOCKED,
                                                 INSTANCE_RUNNING,
                                                 TASK_APPROVED,
                                                 TASK_CANCELLED, TASK_PENDING)
from app.modules.employee.model import Employee

ACTOR = 1
ENTITY = "document"
DOC_ID = 909


@pytest.fixture()
def nguoi(db, seed):
    ids = {"nop": seed.emp_req_id}
    for ten in ("a", "b", "c"):
        employee = Employee(code=f"NV_{ten.upper()}", full_name=f"Người {ten.upper()}",
                            company_id=seed.company_id, department_id=seed.dept_id,
                            is_active=True)
        db.add(employee)
        db.flush()
        ids[ten] = employee.id
    db.commit()
    return ids


@pytest.fixture()
def boi_canh():
    """Bối cảnh rỗng là đủ: các bước ở đây chỉ tay đích danh nhân sự."""
    return lambda entity, entity_id: {}


def _luong(db, code="LUONG-SYNC"):
    flow = ApprovalFlow(entity=ENTITY, code=code, name="Luồng thử bám theo",
                        is_active=True, created_by=ACTOR, updated_by=ACTOR)
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow


def _buoc(db, flow, seq, employee_id, **kw):
    node = ApprovalNode(
        flow_id=flow.id, seq=seq, name=kw.pop("name", f"Bước {seq}"),
        approver_kind=APPROVER_EMPLOYEE, approver_ref=str(employee_id),
        on_no_approver=kw.pop("on_no_approver", NO_APPROVER_BLOCK),
        created_by=ACTOR, updated_by=ACTOR, **kw,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


def _trinh(db, nguoi_nop, entity_id=DOC_ID):
    return instance_service.bat_dau(db, ENTITY, entity_id, {}, nguoi_nop, ACTOR,
                                    entity_code="VB-909", entity_title="Phiếu thử")


def _viec(db, instance, seq=None):
    rows = instance_service.viec_cua_phien(db, instance.id)
    return [r for r in rows if seq is None or r.node_seq == seq]


def _dang_cho(db, instance):
    return [r for r in _viec(db, instance) if r.status == TASK_PENDING]


# ── 1 · bước ĐANG CHỜ đổi người ─────────────────────────────────────────────

def test_buoc_dang_cho_thi_viec_chuyen_sang_nguoi_moi(db, seed, nguoi, boi_canh):
    flow = _luong(db)
    b1 = _buoc(db, flow, 1, nguoi["a"])

    instance = _trinh(db, nguoi["nop"])
    assert [r.assignee_employee_id for r in _dang_cho(db, instance)] == [nguoi["a"]]

    b1.approver_ref = str(nguoi["b"])
    flow_sync_service.dong_bo_sau_khi_sua_buoc(db, b1, ACTOR, boi_canh)
    db.commit()

    assert [r.assignee_employee_id for r in _dang_cho(db, instance)] == [nguoi["b"]], \
        "Bước đang chờ phải chuyển sang người vừa khai trong luồng"
    #  Người cũ mất việc — không để hai người cùng cầm một bước, và người cũ
    #  không được ký nữa (đó là cả điểm của việc đổi người).
    cu = [r for r in _viec(db, instance) if r.assignee_employee_id == nguoi["a"]]
    assert [r.status for r in cu] == [TASK_CANCELLED]


def test_nguoi_cu_khong_con_duyet_duoc_nua(db, seed, nguoi, boi_canh):
    flow = _luong(db)
    b1 = _buoc(db, flow, 1, nguoi["a"])
    instance = _trinh(db, nguoi["nop"])

    b1.approver_ref = str(nguoi["b"])
    flow_sync_service.dong_bo_sau_khi_sua_buoc(db, b1, ACTOR, boi_canh)
    db.commit()

    with pytest.raises(Exception):
        action_service.duyet(db, instance, nguoi["a"], ACTOR, {})


# ── 2 · bước CHƯA TỚI ───────────────────────────────────────────────────────

def test_buoc_chua_toi_cung_di_theo_nguoi_moi(db, seed, nguoi, boi_canh):
    flow = _luong(db)
    _buoc(db, flow, 1, nguoi["a"])
    b2 = _buoc(db, flow, 2, nguoi["b"])

    instance = _trinh(db, nguoi["nop"])
    b2.approver_ref = str(nguoi["c"])
    flow_sync_service.dong_bo_sau_khi_sua_buoc(db, b2, ACTOR, boi_canh)
    db.commit()

    action_service.duyet(db, instance, nguoi["a"], ACTOR, {})
    assert [r.assignee_employee_id for r in _dang_cho(db, instance)] == [nguoi["c"]]


# ── 3 · bước ĐÃ KÝ không đụng tới ───────────────────────────────────────────

def test_buoc_da_ky_giu_nguyen_chu_ky(db, seed, nguoi, boi_canh):
    """Vá lại bước đã ký là bản in dấu vết nói dối ai đã xem xét văn bản."""
    flow = _luong(db)
    b1 = _buoc(db, flow, 1, nguoi["a"])
    _buoc(db, flow, 2, nguoi["b"])

    instance = _trinh(db, nguoi["nop"])
    action_service.duyet(db, instance, nguoi["a"], ACTOR, {})

    b1.approver_ref = str(nguoi["c"])
    flow_sync_service.dong_bo_sau_khi_sua_buoc(db, b1, ACTOR, boi_canh)
    db.commit()

    buoc1 = _viec(db, instance, seq=1)
    assert [(r.assignee_employee_id, r.status) for r in buoc1] == \
        [(nguoi["a"], TASK_APPROVED)]


# ── 4 · phiếu đang KẸT thì hồi sinh ─────────────────────────────────────────

def test_phieu_ket_hoi_sinh_khi_buoc_do_co_nguoi_duyet(db, seed, nguoi, boi_canh):
    """Đây là đường gỡ kẹt bằng CẤU HÌNH, khỏi sửa tay dưới cơ sở dữ liệu."""
    flow = _luong(db)
    #  Bước chỉ tay vào chính người nộp → họ bị loại (I08) → không còn ai → kẹt.
    b1 = _buoc(db, flow, 1, nguoi["nop"])

    instance = _trinh(db, nguoi["nop"])
    assert instance.status == INSTANCE_BLOCKED

    b1.approver_ref = str(nguoi["a"])
    flow_sync_service.dong_bo_sau_khi_sua_buoc(db, b1, ACTOR, boi_canh)
    db.commit()

    assert instance.status == INSTANCE_RUNNING
    assert instance.finish_reason == ""
    assert [r.assignee_employee_id for r in _dang_cho(db, instance)] == [nguoi["a"]]


# ── 5 · sửa thành không còn ai duyệt được ───────────────────────────────────

def test_sua_thanh_khong_con_ai_thi_phieu_ket_chu_khong_di_tiep(db, seed, nguoi, boi_canh):
    """Bước không ai duyệt mà vẫn qua = văn bản có hiệu lực không ai chịu trách nhiệm."""
    flow = _luong(db)
    b1 = _buoc(db, flow, 1, nguoi["a"])
    _buoc(db, flow, 2, nguoi["b"])

    instance = _trinh(db, nguoi["nop"])
    b1.approver_ref = str(nguoi["nop"])   # chỉ còn chính người nộp
    flow_sync_service.dong_bo_sau_khi_sua_buoc(db, b1, ACTOR, boi_canh)
    db.commit()

    assert instance.status == INSTANCE_BLOCKED
    assert _dang_cho(db, instance) == []


# ── 6 · bỏ nhánh «đẩy lên cấp trên» ─────────────────────────────────────────

def test_bo_nhanh_day_len_cap_tren_thi_phieu_ket(db, seed, nguoi):
    """CR-114 — bộ máy không còn TỰ CHỌN người ngoài luồng.

    Luồng cũ còn khai giá trị 2 thì nay rơi thẳng xuống *dừng phiếu*: hiện ra để
    người ta sửa luồng, chứ không lặng lẽ giao cho một người lạ.
    """
    flow = _luong(db)
    _buoc(db, flow, 1, nguoi["nop"], on_no_approver=NO_APPROVER_ESCALATE)

    instance = _trinh(db, nguoi["nop"])

    assert instance.status == INSTANCE_BLOCKED
    assert "không tìm được người duyệt" in instance.finish_reason
    assert instance_service.viec_cua_phien(db, instance.id) == []


def test_o_chon_khong_con_bay_ra_nhanh_da_bo(db, seed):
    """Nhãn còn để đọc dữ liệu cũ, nhưng KHÔNG được nằm trong danh sách chọn."""
    from app.modules.approval.flow_model import (NO_APPROVER_CHOICES,
                                                 NO_APPROVER_LABELS)

    assert NO_APPROVER_ESCALATE not in NO_APPROVER_CHOICES
    assert NO_APPROVER_ESCALATE in NO_APPROVER_LABELS


# ── Bối cảnh dựng lại từ id ─────────────────────────────────────────────────

def test_loai_chung_tu_chua_khai_ham_boi_canh_thi_tra_rong(db, seed):
    """Bối cảnh rỗng dẫn tới phiếu KẸT — tức là HIỆN RA, không phải im lặng."""
    assert entity_hooks.boi_canh(db, "khong_co_loai_nay", 1) == {}
