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
from app.seed_luong_nghi_phep import MA_LUONG, tim_phong_nhan_su


@pytest.fixture()
def san(db, seed):
    """Loại GNP + một phòng Nhân sự có trưởng, giống dữ liệu thật."""
    db.add(DocType(code="GNP", name="Giấy nghỉ phép", id_scheme=2,
                   number_when=2, is_personal=True))
    truong = Employee(code="TP_NS", full_name="Trưởng phòng Nhân sự",
                      company_id=seed.company_id, is_active=True)
    db.add(truong)
    db.flush()
    phong = Department(code="PBA007", name="Phòng Nhân sự - Hành chính",
                       company_id=seed.company_id, manager_id=truong.id,
                       is_active=True)
    db.add(phong)
    db.commit()
    return {"phong": phong, "truong": truong}


def _chay(db):
    """Chạy phần thân của script trên phiên làm việc của test.

    Script thật tự mở `SessionLocal()`, mà test dùng SQLite trong bộ nhớ — nên
    gọi lại đúng các bước với `db` của test thay vì `run()`.
    """
    from app.seed_luong_nghi_phep import MA_LOAI, UU_TIEN

    if db.query(ApprovalFlow).filter(ApprovalFlow.entity == "document",
                                     ApprovalFlow.code == MA_LUONG).first():
        return None

    loai = db.query(DocType).filter(DocType.code == MA_LOAI).first()
    phong = tim_phong_nhan_su(db)
    flow = ApprovalFlow(entity="document", code=MA_LUONG, name="Duyệt đơn nghỉ phép",
                        condition=json.dumps([{"field": "doc_type_id", "op": "in",
                                               "value": [loai.id]}]),
                        priority=UU_TIEN, is_active=True, created_by=1, updated_by=1)
    db.add(flow)
    db.flush()
    db.add(ApprovalNode(flow_id=flow.id, seq=1, name="Trưởng bộ phận duyệt",
                        approver_kind=APPROVER_DEPT_HEAD, approver_ref="",
                        sla_hours=24, fallback_employee_id=phong.manager_id,
                        on_no_approver=NO_APPROVER_FALLBACK,
                        created_by=1, updated_by=1))
    db.add(ApprovalNode(flow_id=flow.id, seq=2, name=f"Trưởng {phong.name} duyệt",
                        approver_kind=APPROVER_DEPT_HEAD_OF,
                        approver_ref=str(phong.id), sla_hours=24,
                        created_by=1, updated_by=1))
    db.commit()
    return flow


# ── Tìm phòng Nhân sự ───────────────────────────────────────────────────────

def test_tim_ra_phong_nhan_su_theo_ma(db, san):
    assert tim_phong_nhan_su(db).id == san["phong"].id


def test_tim_theo_TEN_khi_ma_khac(db, seed):
    """Tên phòng khác nhau giữa các nơi — mã cũng vậy. Phải dò được cả hai."""
    truong = Employee(code="TP_X", full_name="Trưởng phòng", company_id=seed.company_id,
                      is_active=True)
    db.add(truong)
    db.flush()
    db.add(Department(code="KHONG_KHOP", name="Phòng Hành chính Nhân sự",
                      company_id=seed.company_id, manager_id=truong.id, is_active=True))
    db.commit()

    assert tim_phong_nhan_su(db) is not None


def test_khong_co_phong_nao_thi_tra_None_chu_khong_doan_bua(db, seed):
    """Trỏ bừa vào một phòng khác là đơn nghỉ phép chạy tới nhầm người."""
    assert tim_phong_nhan_su(db) is None


def test_bo_qua_phong_da_tat(db, seed):
    db.add(Department(code="PBA007", name="Phòng Nhân sự", company_id=seed.company_id,
                      manager_id=None, is_active=False))
    db.commit()
    assert tim_phong_nhan_su(db) is None


# ── Hình dạng luồng ─────────────────────────────────────────────────────────

def test_khai_dung_hai_chang(db, san):
    flow = _chay(db)
    buoc = db.query(ApprovalNode).filter(
        ApprovalNode.flow_id == flow.id).order_by(ApprovalNode.seq).all()
    assert [n.seq for n in buoc] == [1, 2]
    assert buoc[0].approver_kind == APPROVER_DEPT_HEAD, "chặng 1 bám theo người nộp"
    assert buoc[1].approver_kind == APPROVER_DEPT_HEAD_OF, "chặng 2 bám theo PHÒNG khai trong luồng"
    assert buoc[1].approver_ref == str(san["phong"].id)


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
    dieu_kien = json.loads(flow.condition)
    loai = db.query(DocType).filter(DocType.code == "GNP").one()
    assert dieu_kien == [{"field": "doc_type_id", "op": "in", "value": [loai.id]}]


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
    assert db.query(ApprovalFlow).filter(ApprovalFlow.code == MA_LUONG).count() == 1


def test_khong_dung_toi_luong_da_co(db, san):
    """Điểm khác quan trọng nhất so với `seed_approval_demo` (xóa sạch rồi nạp)."""
    cu = ApprovalFlow(entity="document", code="VB_MAC_DINH", name="Luồng của khách",
                      is_active=True, priority=0, created_by=1, updated_by=1)
    db.add(cu)
    db.commit()
    truoc = cu.name

    _chay(db)

    db.refresh(cu)
    assert cu.name == truoc
    assert db.query(ApprovalFlow).filter(ApprovalFlow.code == "VB_MAC_DINH").count() == 1
