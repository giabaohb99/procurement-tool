"""ĐƠN NGHỈ PHÉP — phần riêng của loại (`metadata`) và người duyệt theo phòng ban.

Hai thứ mới của CR-159 ngoài chuyện hiển thị:

* `tab_document.metadata` — ô mở, nên phải có người canh cửa. Hình dạng khai ở
  `type_metadata.py`, **khóa lạ bị loại bỏ chứ không lưu**. Không canh thì sáu
  tháng nữa không ai biết trong đó có gì và module Nghỉ phép đọc ra rác.

* `APPROVER_DEPT_HEAD_OF` — trưởng bộ phận của phòng ban CHỈ ĐỊNH. Trước đây chỉ
  có "trưởng bộ phận của người nộp", nên không khai nổi bước có thật như «đơn
  nghỉ phép của mọi phòng đều qua trưởng phòng Nhân sự».
"""
import pytest
from fastapi import HTTPException

from app.modules.approval import approver_resolver
from app.modules.approval.flow_model import APPROVER_DEPT_HEAD_OF, ApprovalNode
from app.modules.department.model import Department
from app.modules.doc_catalog.model import DocType
from app.modules.document import service, type_metadata
from app.modules.document.schema import DocumentCreate, DocumentUpdate
from app.modules.employee.model import Employee

ACTOR = 1


# ── Hình dạng metadata ──────────────────────────────────────────────────────

def _don(**ghi_de) -> dict:
    origin = {"from_date": "2026-09-01", "to_date": "2026-09-03",
           "leave_type": type_metadata.ANNUAL_LEAVE, "reason": "Về quê"}
    return {**origin, **ghi_de}


def test_loai_bo_khoa_la_chu_khong_luu(db):
    """Nhận bừa là mỗi người gửi một hình dạng, module đọc sau phải đỡ hết."""
    cleaned = type_metadata.sanitize("GNP", _don(salary=99999999, hacked="<script>"), 7)
    assert "salary" not in cleaned
    assert "hacked" not in cleaned
    assert set(cleaned) == {"employee_id", "leave_type", "from_date", "from_session",
                         "to_date", "to_session", "total_days", "reason",
                         "handover_employee_id", "contact_phone"}


def test_loai_chua_khai_hinh_dang_thi_khong_luu_gi(db):
    """Công văn không có phần riêng — gửi metadata lên cũng không nhận."""
    assert type_metadata.sanitize("CV", _don(), 7) is None


def test_gui_rong_thi_khong_luu_de_con_luu_duoc_ban_nhap(db):
    """Chốt «phải nhập đủ» đặt ở lúc GỬI DUYỆT, không phải lúc lưu nháp."""
    assert type_metadata.sanitize("GNP", {}, 7) is None
    assert type_metadata.sanitize("GNP", None, 7) is None


def test_ngay_ve_truoc_ngay_di_bi_chan(db):
    with pytest.raises(HTTPException) as error:
        type_metadata.sanitize("GNP", _don(from_date="2026-09-05",
                                           to_date="2026-09-01"), 7)
    assert error.value.status_code == 400


def test_thieu_ly_do_bi_chan(db):
    with pytest.raises(HTTPException):
        type_metadata.sanitize("GNP", _don(reason="   "), 7)


def test_loai_nghi_khong_co_trong_danh_muc_bi_chan(db):
    with pytest.raises(HTTPException):
        type_metadata.sanitize("GNP", _don(leave_type="khong_co_that"), 7)


def test_nghi_tu_chieu_den_sang_cung_ngay_la_khoang_trong(db):
    """Nửa ngày phải khai được, nhưng «chiều → sáng» cùng ngày thì vô nghĩa."""
    with pytest.raises(HTTPException):
        type_metadata.sanitize("GNP", _don(
            from_date="2026-09-01", to_date="2026-09-01",
            from_session=type_metadata.SESSION_AFTERNOON,
            to_session=type_metadata.SESSION_MORNING), 7)


def test_nua_ngay_phep_tinh_ra_nua_cong(db):
    """Bỏ ô buổi đi thì người ta khai một ngày cho một buổi, sai từ nguồn."""
    cleaned = type_metadata.sanitize("GNP", _don(
        from_date="2026-09-01", to_date="2026-09-01",
        from_session=type_metadata.SESSION_MORNING,
        to_session=type_metadata.SESSION_MORNING), 7)
    assert cleaned["total_days"] == 0.5


def test_ba_ngay_tron_ven_tinh_ra_ba_cong(db):
    assert type_metadata.sanitize("GNP", _don(), 7)["total_days"] == 3.0


def test_nguoi_dung_sua_de_so_ngay_thi_giu_nguyen_cua_ho(db):
    """Lịch làm việc mỗi pháp nhân một khác — con số máy tính chỉ là gợi ý."""
    assert type_metadata.sanitize("GNP", _don(total_days=2), 7)["total_days"] == 2


def test_nguoi_nghi_mac_dinh_la_nguoi_chiu_trach_nhiem(db):
    assert type_metadata.sanitize("GNP", _don(), 7)["employee_id"] == 7


def test_khai_tuong_minh_nguoi_nghi_thi_thang(db):
    """Hành chính lập hộ — người nghỉ không phải người lập."""
    assert type_metadata.sanitize("GNP", _don(employee_id=12), 7)["employee_id"] == 12


# ── Chốt lúc gửi duyệt ──────────────────────────────────────────────────────

def test_gui_duyet_ma_chua_khai_gi_thi_bi_chan(db):
    with pytest.raises(HTTPException) as error:
        type_metadata.require_on_submit("GNP", None)
    assert error.value.status_code == 400
    assert "nghỉ phép" in str(error.value.detail)


def test_loai_thuong_khong_bi_doi_metadata(db):
    """Đừng chặn nhầm 32 loại còn lại."""
    type_metadata.require_on_submit("CV", None)


def test_gui_duyet_don_thieu_metadata_bi_chan_that(db, seed):
    """Chạy qua đường thật `service.submit`, không chỉ gọi hàm kiểm."""
    kind = DocType(code="GNP", name="Giấy nghỉ phép", id_scheme=2,
                   number_when=2, is_personal=True)
    db.add(kind)
    db.flush()
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=kind.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Đơn nghỉ phép chưa khai gì",
        content_html="<p>Nội dung.</p>",
    ), ACTOR)

    with pytest.raises(HTTPException) as error:
        service.submit(db, doc, ACTOR)
    assert error.value.status_code == 400


# ── Lưu / sửa qua service ───────────────────────────────────────────────────

def test_metadata_xuong_duoc_toi_CSDL(db, seed):
    """⚠️ Bài kiểm chống lỗi im lặng.

    Thuộc tính Python của cột là `meta`, không phải `metadata` (SQLAlchemy giữ
    riêng tên đó cho `Base.metadata`). Gán nhầm `doc.metadata = ...` thì giá trị
    nằm trong `__dict__` của instance và **không bao giờ xuống CSDL** — API vẫn
    trả 200, dữ liệu thì mất.
    """
    kind = DocType(code="GNP", name="Giấy nghỉ phép", id_scheme=2, number_when=2)
    db.add(kind)
    db.flush()
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=kind.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Đơn nghỉ phép",
        content_html="<p>x</p>", metadata=_don(),
    ), ACTOR)

    db.expire_all()
    doc = service.get_or_404(db, doc.id)
    assert doc.meta["reason"] == "Về quê"
    assert doc.meta["total_days"] == 3.0


def test_sua_metadata_cung_xuong_duoc_CSDL(db, seed):
    kind = DocType(code="GNP", name="Giấy nghỉ phép", id_scheme=2, number_when=2)
    db.add(kind)
    db.flush()
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=kind.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Đơn nghỉ phép",
        content_html="<p>x</p>", metadata=_don(),
    ), ACTOR)

    service.update_document(db, doc, DocumentUpdate(
        metadata=_don(reason="Đổi lý do", to_date="2026-09-02")), ACTOR)

    db.expire_all()
    doc = service.get_or_404(db, doc.id)
    assert doc.meta["reason"] == "Đổi lý do"
    assert doc.meta["total_days"] == 2.0


# ── Người duyệt: trưởng bộ phận của phòng ban chỉ định ──────────────────────

@pytest.fixture()
def departments(db, seed):
    """Hai phòng, mỗi phòng một trưởng — và một phòng bỏ trống ghế trưởng."""
    result = {}
    for code, name in (("NS", "Nhân sự"), ("TC", "Tài chính"), ("TRONG", "Phòng trống")):
        field_code = None
        if code != "TRONG":
            field_code = Employee(code=f"TP_{code}", full_name=f"Trưởng phòng {name}",
                              company_id=seed.company_id, is_active=True)
            db.add(field_code)
            db.flush()
        department = Department(code=f"P_{code}", name=name, company_id=seed.company_id,
                           manager_id=field_code.id if field_code else None)
        db.add(department)
        db.flush()
        result[code] = {"phong": department.id, "truong": field_code.id if field_code else None}
    db.commit()
    return result


def _buoc(ref: str) -> ApprovalNode:
    return ApprovalNode(flow_id=1, seq=1, name="Duyệt",
                        approver_kind=APPROVER_DEPT_HEAD_OF, approver_ref=ref,
                        created_by=ACTOR, updated_by=ACTOR)


def test_tra_ra_truong_cua_dung_phong_duoc_khai(db, departments):
    """Không phải phòng của người nộp — đó là cả điểm khác biệt."""
    out = approver_resolver.resolve(db, _buoc(str(departments["NS"]["phong"])), {}, None)
    assert out == [departments["NS"]["truong"]]


def test_nguoi_nop_o_phong_khac_van_ra_dung_truong_phong_da_khai(db, departments, seed):
    """Đơn nghỉ phép của MỌI phòng đều phải qua trưởng phòng Nhân sự."""
    submitter = Employee(code="NV_TC", full_name="Nhân viên Tài chính",
                         company_id=seed.company_id,
                         department_id=departments["TC"]["phong"], is_active=True)
    db.add(submitter)
    db.commit()

    out = approver_resolver.resolve(db, _buoc(str(departments["NS"]["phong"])), {},
                                   submitter.id)
    assert out == [departments["NS"]["truong"]]


def test_khai_nhieu_phong_thi_giu_dung_thu_tu_khai(db, departments):
    """Bước «lần lượt» đọc thứ tự này — `IN (...)` không hứa thứ tự trả về."""
    ref = f"{departments['TC']['phong']},{departments['NS']['phong']}"
    assert approver_resolver.resolve(db, _buoc(ref), {}, None) == [
        departments["TC"]["truong"], departments["NS"]["truong"]]


def test_phong_bo_trong_ghe_truong_thi_tra_rong_chu_khong_no(db, departments):
    """Rỗng thì `on_no_approver` của bước quyết định — không bịa ra người."""
    assert approver_resolver.resolve(db, _buoc(str(departments["TRONG"]["phong"])),
                                     {}, None) == []


def test_phong_khong_ton_tai_thi_tra_rong(db, departments):
    assert approver_resolver.resolve(db, _buoc("999999"), {}, None) == []


def test_khong_khai_phong_nao_thi_tra_rong(db, departments):
    for ref in ("", "   ", "abc"):
        assert approver_resolver.resolve(db, _buoc(ref), {}, None) == []


def test_truong_phong_da_nghi_viec_thi_bi_loai(db, departments):
    """Giao việc cho người đã tắt trạng thái là phiếu nằm im vĩnh viễn."""
    field_code = db.get(Employee, departments["NS"]["truong"])
    field_code.is_active = False
    db.commit()

    assert approver_resolver.resolve(db, _buoc(str(departments["NS"]["phong"])),
                                     {}, None) == []
