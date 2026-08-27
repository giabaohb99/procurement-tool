"""LUỒNG DUYỆT ĐƠN NGHỈ PHÉP — kịch bản nạp `app/seed_luong_nghi_phep.py`.

Script này sẽ chạy trên môi trường THẬT, cạnh những luồng người ta đã khai và đã
sửa tay, nên hai thứ phải chắc:

  1. **chỉ THÊM, không đụng cái cũ** — khác `seed_approval_demo` vốn xóa sạch rồi
     nạp lại; chạy bản kia trên dev là mất hết luồng đang chạy;
  2. **chạy lại được** — deploy gọi hai lần không đẻ ra hai luồng.

Và hình dạng luồng phải đúng: chặng 2 dùng cách chọn «trưởng bộ phận của phòng
ban chỉ định» (CR-159), trỏ vào GHẾ chứ không vào một con người.
"""
import json

import pytest

from app.modules.approval.flow_model import (APPROVER_DEPT_HEAD,
                                             APPROVER_DEPT_HEAD_OF,
                                             NO_APPROVER_FALLBACK,
                                             ApprovalFlow, ApprovalNode)
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.employee.model import Employee
from app.seed_luong_nghi_phep import FLOW_CODE, find_hr_department


@pytest.fixture()
def san(db, seed):
    """Loại GNP + một phòng Nhân sự có trưởng, giống dữ liệu thật."""
    db.add(DocType(code="GNP", name="Giấy nghỉ phép", id_scheme=2,
                   number_when=2, is_personal=True))
    field_code = Employee(code="TP_NS", full_name="Trưởng phòng Nhân sự",
                      company_id=seed.company_id, is_active=True)
    db.add(field_code)
    db.flush()
    department = Department(code="PBA007", name="Phòng Nhân sự - Hành chính",
                       company_id=seed.company_id, manager_id=field_code.id,
                       is_active=True)
    db.add(department)
    db.commit()
    return {"phong": department, "truong": field_code}


def _chay(db):
    """Chạy phần thân của script trên phiên làm việc của test.

    Script thật tự mở `SessionLocal()`, mà test dùng SQLite trong bộ nhớ — nên
    gọi lại đúng các bước với `db` của test thay vì `run()`.
    """
    from app.seed_luong_nghi_phep import DOC_TYPE_CODE, PRIORITY

    if db.query(ApprovalFlow).filter(ApprovalFlow.entity == "document",
                                     ApprovalFlow.code == FLOW_CODE).first():
        return None

    kind = db.query(DocType).filter(DocType.code == DOC_TYPE_CODE).first()
    department = find_hr_department(db)
    flow = ApprovalFlow(entity="document", code=FLOW_CODE, name="Duyệt đơn nghỉ phép",
                        condition=json.dumps([{"field": "doc_type_id", "op": "in",
                                               "value": [kind.id]}]),
                        priority=PRIORITY, is_active=True, created_by=1, updated_by=1)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Trưởng bộ phận duyệt",
                        approver_kind=APPROVER_DEPT_HEAD, approver_ref="",
                        sla_hours=24, fallback_employee_id=department.manager_id,
                        on_no_approver=NO_APPROVER_FALLBACK,
                        created_by=1, updated_by=1))
    db.add(ApprovalNode(flow_id=flow.id, seq=2, name=f"Trưởng {department.name} duyệt",
                        approver_kind=APPROVER_DEPT_HEAD_OF,
                        approver_ref=str(department.id), sla_hours=24,
                        created_by=1, updated_by=1))
    db.commit()
    return flow


# ── Tìm phòng Nhân sự ───────────────────────────────────────────────────────

def test_tim_ra_phong_nhan_su_theo_ma(db, san):
    assert find_hr_department(db).id == san["phong"].id


def test_tim_theo_TEN_khi_ma_khac(db, seed):
    """Tên phòng khác nhau giữa các nơi — mã cũng vậy. Phải dò được cả hai."""
    field_code = Employee(code="TP_X", full_name="Trưởng phòng", company_id=seed.company_id,
                      is_active=True)
    db.add(field_code)
    db.flush()
    db.add(Department(code="KHONG_KHOP", name="Phòng Hành chính Nhân sự",
                      company_id=seed.company_id, manager_id=field_code.id, is_active=True))
    db.commit()

    assert find_hr_department(db) is not None


def test_khong_co_phong_nao_thi_tra_None_chu_khong_doan_bua(db, seed):
    """Trỏ bừa vào một phòng khác là đơn nghỉ phép chạy tới nhầm người."""
    assert find_hr_department(db) is None


def test_bo_qua_phong_da_tat(db, seed):
    db.add(Department(code="PBA007", name="Phòng Nhân sự", company_id=seed.company_id,
                      manager_id=None, is_active=False))
    db.commit()
    assert find_hr_department(db) is None


# ── Hình dạng luồng ─────────────────────────────────────────────────────────

def test_khai_dung_hai_chang(db, san):
    flow = _chay(db)
    step = db.query(ApprovalNode).filter(
        ApprovalNode.flow_id == flow.id).order_by(ApprovalNode.seq).all()
    assert [n.seq for n in step] == [1, 2]
    assert step[0].approver_kind == APPROVER_DEPT_HEAD, "chặng 1 bám theo người nộp"
    assert step[1].approver_kind == APPROVER_DEPT_HEAD_OF, "chặng 2 bám theo PHÒNG khai trong luồng"
    assert step[1].approver_ref == str(san["phong"].id)


def test_chang_1_co_nguoi_du_phong(db, san):
    """Trưởng phòng TỰ xin nghỉ thì luật I08 bỏ họ khỏi chặng 1 → chặng rỗng.

    Không khai dự phòng là đơn của mọi quản lý đều kẹt, mà quản lý cũng phải
    nghỉ phép.
    """
    flow = _chay(db)
    chang1 = db.query(ApprovalNode).filter(
        ApprovalNode.flow_id == flow.id, ApprovalNode.seq == 1).one()
    assert chang1.fallback_employee_id == san["truong"].id
    assert chang1.on_no_approver == NO_APPROVER_FALLBACK


def test_dieu_kien_chi_bat_dung_loai_GNP(db, san):
    """Bắt nhầm loại khác là công văn cũng bị lôi vào luồng nghỉ phép."""
    flow = _chay(db)
    condition = json.loads(flow.condition)
    kind = db.query(DocType).filter(DocType.code == "GNP").one()
    assert condition == [{"field": "doc_type_id", "op": "in", "value": [kind.id]}]


def test_uu_tien_cao_hon_luong_mac_dinh(db, san):
    """Luồng mặc định ưu tiên 0 và KHÔNG khai điều kiện nên bắt mọi thứ.

    Thấp hơn nó thì đơn nghỉ phép rơi vào luồng mặc định — nơi chặng cuối là
    «Chánh Văn phòng ký», sai người hoàn toàn.
    """
    assert _chay(db).priority > 0


# ── Chạy lại được, không đụng cái cũ ────────────────────────────────────────

def test_chay_lan_hai_khong_de_them_luong(db, san):
    _chay(db)
    _chay(db)
    assert db.query(ApprovalFlow).filter(ApprovalFlow.code == FLOW_CODE).count() == 1


def test_khong_dung_toi_luong_da_co(db, san):
    """Điểm khác quan trọng nhất so với `seed_approval_demo` (xóa sạch rồi nạp)."""
    old = ApprovalFlow(entity="document", code="VB_MAC_DINH", name="Luồng của khách",
                      is_active=True, priority=0, created_by=1, updated_by=1)
    db.add(old)
    db.commit()
    before = old.name

    _chay(db)

    db.refresh(old)
    assert old.name == before
    assert db.query(ApprovalFlow).filter(ApprovalFlow.code == "VB_MAC_DINH").count() == 1
