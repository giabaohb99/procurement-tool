"""Năm bản vá RÒ DỮ LIỆU XUYÊN PHÁP NHÂN — mục #9 #11 #13 #15 #18 của đợt rà
`plans/260905-0931-stress-test-pham-vi-phan-quyen`.

Mỗi bản vá có **hai vế, luôn đi cặp**:

* vế CHẶN — người ngoài phạm vi không đọc/không xóa được;
* vế KHÔNG CHẶN NHẦM — người TRONG phạm vi vẫn thấy đủ, đúng số.

Thiếu vế thứ hai thì một bản vá "an toàn" bằng cách khóa sạch cũng xanh, rồi
tuần sau có người gỡ nó ra vì màn hình trống trơn. Nên ca nào cũng so bằng
**tập id / con số cụ thể**, không so "khác rỗng".

Thế giới mẫu là `scope_factory.build_world`: hai pháp nhân A/B, bốn phòng (hai
phòng TRÙNG TÊN khác pháp nhân), bảy nhân sự.
"""
import json
from datetime import date, timedelta

import pytest
from fastapi import HTTPException

from scope_factory import build_world  # noqa: F401 — fixture `world` của conftest dùng nó

TODAY = date(2026, 3, 2)
YEAR = 2026


def body(response) -> dict:
    """Bóc lớp phong bì `{success, message, data}` của một `JSONResponse`."""
    return json.loads(response.body)["data"]


def message(response) -> str:
    return json.loads(response.body)["message"]


# ══════════════════════════════════════════════════════════════════════════════
#  Dựng dữ liệu — tên hàm là ĐỘNG TỪ, mỗi hàm một loại bản ghi
# ══════════════════════════════════════════════════════════════════════════════

def create_purchase_request(db, *, code, company_id, department_id, created_by):
    from app.modules.purchase_request.model import PurchaseRequest

    row = PurchaseRequest(code=code, company_id=company_id, department_id=department_id,
                          status="submitted", created_by=created_by)
    db.add(row)
    db.flush()
    return row


def create_survey_with_lines(db, *, code, created_by, tax_code, supplier_code):
    """Một phiếu khảo sát kèm ĐÚNG một dòng NCC và một dòng sản phẩm."""
    from app.modules.survey.model import (Survey, SurveyProductLine,
                                          SurveySupplierLine)

    survey = Survey(code=code, survey_type="supplier", status="submitted",
                    created_by=created_by)
    db.add(survey)
    db.flush()
    db.add(SurveySupplierLine(survey_id=survey.id, supplier_code=supplier_code,
                              supplier_name=f"NCC {supplier_code}", tax_code=tax_code))
    db.add(SurveyProductLine(survey_id=survey.id, supplier_code=supplier_code,
                             product_name=f"Hàng của {code}"))
    db.flush()
    return survey


def create_survey_request(db, *, code, company_id, department_id, created_by):
    from app.modules.survey_request.model import SurveyRequest

    row = SurveyRequest(code=code, company_id=company_id, department_id=department_id,
                        status="draft", created_by=created_by)
    db.add(row)
    db.flush()
    return row


def create_document(db, *, title, doc_type_id, company_id, department_id,
                    owner_employee_id, created_by):
    from app.modules.document.model import (ORIGIN_INTERNAL, STATUS_EFFECTIVE,
                                            Document)

    row = Document(origin=ORIGIN_INTERNAL, doc_type_id=doc_type_id,
                   company_id=company_id, department_id=department_id,
                   owner_employee_id=owner_employee_id, title=title,
                   status=STATUS_EFFECTIVE, effective_date=TODAY,
                   created_by=created_by, updated_by=created_by)
    db.add(row)
    db.flush()
    return row


def create_leave_type(db, *, code="annual", name="Phép năm", quota=12.0):
    from app.modules.leave.catalog_model import LeaveType

    row = LeaveType(code=code, name=name, counts_balance=True,
                    annual_quota_days=quota, is_active=True)
    db.add(row)
    db.flush()
    return row


def create_leave_balance(db, *, employee_id, company_id, leave_type_id,
                         allocated=12.0, used=0.0):
    from app.modules.leave.balance_model import LeaveBalance

    row = LeaveBalance(employee_id=employee_id, company_id=company_id, year=YEAR,
                       leave_type_id=leave_type_id, allocated_days=allocated,
                       used_days=used)
    db.add(row)
    db.flush()
    return row


# ══════════════════════════════════════════════════════════════════════════════
#  #9 — GET /api/dashboard/stats
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def stats_data(world):
    """Một YCMH mỗi pháp nhân — đủ để phân biệt "đếm toàn hệ" với "đếm trong phạm vi"."""
    db = world.db
    rows = {
        "A": create_purchase_request(db, code="PR-A", company_id=world.co["A"],
                                     department_id=world.dept["A.kt"],
                                     created_by=world.user_id("a1")),
        "B": create_purchase_request(db, code="PR-B", company_id=world.co["B"],
                                     department_id=world.dept["B.kt"],
                                     created_by=world.user_id("b1")),
    }
    db.commit()
    return rows


def test_09_stats_tai_khoan_khong_quyen_khong_nhan_duoc_khoa_nao(world, stats_data):
    """Vế CHẶN — `perms_union` rỗng thì mọi khóa số liệu VẮNG MẶT.

    Vắng mặt chứ không phải `0`: `0` nghĩa là "đếm được, không có dòng nào".
    Đây là luật chung của `/overview`, `/stats` nay theo đúng nó.
    """
    from app.modules.dashboard.controller import stats

    data = body(stats(days="all", db=world.db, user=world.actor("a1").user))

    for khoa in ("pr_total", "pr_pending", "pr_processing", "employees",
                 "suppliers", "products", "survey_pending", "po_ordered"):
        assert khoa not in data, f"khóa «{khoa}» lọt ra cho tài khoản không có quyền nào"
    assert data["can"] == {"supplier": False, "product": False, "employee": False,
                           "purchase_request": False, "survey": False,
                           "purchase_order": False}
    #  Đường xu hướng vẫn có nhãn ngày (khung biểu đồ), nhưng không có số nào.
    assert all(set(point) == {"label"} for point in data["trends"])


def test_09_stats_dem_dung_trong_pham_vi_chu_khong_dem_toan_he(world, stats_data):
    """Vế KHÔNG CHẶN NHẦM — có quyền thì vẫn ra số, và là số ĐÚNG của pháp nhân mình."""
    from app.modules.employee.model import Employee
    from app.modules.dashboard.controller import stats

    db = world.db
    world.grant("a1", "purchase_request", scope="company")
    world.grant("a1", "employee", scope="company")

    data = body(stats(days="all", db=db, user=world.actor("a1").user))

    assert data["can"]["purchase_request"] is True
    assert data["pr_total"] == 1, "chỉ YCMH của pháp nhân A, không đếm phiếu của B"
    assert data["pr_pending"] == 1
    assert data["trends"][-1]["pr"] == 1
    assert "po_ordered" not in data, "không cấp quyền ĐMH thì khối đó vẫn vắng mặt"

    nhan_su_a = db.query(Employee).filter(Employee.company_id == world.co["A"]).count()
    assert data["employees"] == nhan_su_a > 0
    assert data["employees"] < db.query(Employee).count(), "không đếm nhân sự pháp nhân khác"


# ══════════════════════════════════════════════════════════════════════════════
#  #11 — GET /api/documents/suggestions
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def doc_world(world):
    """Hai loại văn bản (thường + cá nhân) × hai pháp nhân."""
    from app.modules.doc_catalog.model import DocType

    db = world.db
    loai_thuong = DocType(code="CV", name="Công văn", id_scheme=2, number_when=2)
    loai_ca_nhan = DocType(code="GNP", name="Giấy nghỉ phép", id_scheme=2,
                           number_when=2, is_personal=True)
    db.add_all([loai_thuong, loai_ca_nhan])
    db.flush()

    ids = {
        "cv_a": create_document(db, title="Quy chế chi tiêu A", doc_type_id=loai_thuong.id,
                                company_id=world.co["A"], department_id=world.dept["A.kt"],
                                owner_employee_id=world.emp["a1"],
                                created_by=world.user_id("a1")).id,
        "cv_b": create_document(db, title="Quy chế chi tiêu B", doc_type_id=loai_thuong.id,
                                company_id=world.co["B"], department_id=world.dept["B.kt"],
                                owner_employee_id=world.emp["b1"],
                                created_by=world.user_id("b1")).id,
        "np_b": create_document(db, title="Đơn nghỉ phép của b1", doc_type_id=loai_ca_nhan.id,
                                company_id=world.co["B"], department_id=world.dept["B.kt"],
                                owner_employee_id=world.emp["b1"],
                                created_by=world.user_id("b1")).id,
    }
    db.commit()
    return {"thuong": loai_thuong.id, "ca_nhan": loai_ca_nhan.id, **ids}


def goi_suggestions(world, actor_key: str, doc_type_id: int) -> set[int]:
    from app.modules.document.controller import list_suggestions

    actor = world.actor(actor_key)
    return {row["id"] for row in body(list_suggestions(
        doc_type_id=doc_type_id, department_id=None, company_id=None,
        exclude_id=None, db=world.db, user=actor.user))}


def test_11_suggestions_khong_tra_van_ban_ngoai_pham_vi(world, doc_world):
    """Vế CHẶN — người xem phạm vi pháp nhân A không nhận tiêu đề văn bản của B.

    Endpoint trả `title` + `display_code`, đúng thứ `ensure_can` phải trả 404 để
    giấu (K03). Trước bản vá, hai bộ lọc duy nhất là tham số do người gọi truyền,
    bỏ trống là quét cả bảng.
    """
    world.grant("a1", "document", scope="company")
    assert goi_suggestions(world, "a1", doc_world["thuong"]) == {doc_world["cv_a"]}


def test_11_suggestions_van_tra_van_ban_trong_pham_vi(world, doc_world):
    """Vế KHÔNG CHẶN NHẦM — người phạm vi *tất cả* vẫn thấy đủ hai pháp nhân.

    Đây là ca canh cho việc vá bằng cách khóa sạch: nếu `visible_condition` bị
    ghép sai thì ca này rỗng ngay.
    """
    world.grant("b1", "document", scope="all")
    assert goi_suggestions(world, "b1", doc_world["thuong"]) == {
        doc_world["cv_a"], doc_world["cv_b"]}


def test_11_suggestions_khong_lo_tieu_de_van_ban_ca_nhan(world, doc_world):
    """Loại bật `is_personal` — phạm vi vai trò KHÔNG còn tính (CR-159).

    Người ngoài truyền `doc_type_id` của Giấy nghỉ phép thì không ra dòng nào;
    chính chủ vẫn ra đơn của mình.
    """
    world.grant("a1", "document", scope="company")
    world.grant("b1", "document", scope="company")

    assert goi_suggestions(world, "a1", doc_world["ca_nhan"]) == set()
    assert goi_suggestions(world, "b1", doc_world["ca_nhan"]) == {doc_world["np_b"]}


# ══════════════════════════════════════════════════════════════════════════════
#  #13 — GET /api/survey-report/by-supplier
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def survey_world(world):
    """Hai phiếu khảo sát của CÙNG một nhà cung cấp, hai người lập khác nhau.

    `SCOPE_FIELDS["survey"]` chỉ có chiều `owner` (`created_by`) — phiếu khảo sát
    không có cột pháp nhân — nên bậc `own` là bậc duy nhất phân biệt được hai
    phiếu này.
    """
    db = world.db
    rows = {
        "cua_a1": create_survey_with_lines(db, code="KS-A", created_by=world.user_id("a1"),
                                           tax_code="TAX-1", supplier_code="NCC1"),
        "cua_b1": create_survey_with_lines(db, code="KS-B", created_by=world.user_id("b1"),
                                           tax_code="TAX-1", supplier_code="NCC1"),
    }
    db.commit()
    return rows


def goi_by_supplier(world, actor_key: str) -> dict:
    from app.modules.survey.controller import by_supplier_

    actor = world.actor(actor_key)
    return body(by_supplier_(tax_code="TAX-1", supplier_code="NCC1",
                             db=world.db, user=actor.user))


def test_13_by_supplier_khong_tra_dong_cua_phieu_ngoai_pham_vi(world, survey_world):
    """Vế CHẶN — route anh em `/lines` đã có `apply_scope`, route này nay theo.

    Dòng khảo sát mang giá chào, chính sách công nợ và người liên hệ của NCC:
    đổi một đoạn đường dẫn mà đọc được cả hai phiếu là đường vòng của `/lines`.
    """
    world.grant("a1", "survey", scope="own")
    ket_qua = goi_by_supplier(world, "a1")

    assert {r["survey_id"] for r in ket_qua["supplier_lines"]} == {survey_world["cua_a1"].id}
    assert {r["survey_id"] for r in ket_qua["product_lines"]} == {survey_world["cua_a1"].id}


def test_13_by_supplier_van_tra_du_dong_trong_pham_vi(world, survey_world):
    """Vế KHÔNG CHẶN NHẦM — phạm vi *tất cả* vẫn gom đủ hai phiếu, đủ hai loại dòng."""
    world.grant("a3", "survey", scope="all")
    ket_qua = goi_by_supplier(world, "a3")

    ky_vong = {survey_world["cua_a1"].id, survey_world["cua_b1"].id}
    assert {r["survey_id"] for r in ket_qua["supplier_lines"]} == ky_vong
    assert {r["survey_id"] for r in ket_qua["product_lines"]} == ky_vong


# ══════════════════════════════════════════════════════════════════════════════
#  #15 — GET /api/leave-requests/tools/my-balance
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def leave_world(world):
    """Một loại nghỉ + quỹ đã cấp cho a1 (pháp nhân A) và b1 (pháp nhân B)."""
    db = world.db
    loai = create_leave_type(db)
    quy = {
        "a1": create_leave_balance(db, employee_id=world.emp["a1"], company_id=world.co["A"],
                                   leave_type_id=loai.id, used=1.0),
        "a2": create_leave_balance(db, employee_id=world.emp["a2"], company_id=world.co["A"],
                                   leave_type_id=loai.id, used=2.0),
        "b1": create_leave_balance(db, employee_id=world.emp["b1"], company_id=world.co["B"],
                                   leave_type_id=loai.id, used=3.0),
    }
    db.commit()
    return {"loai": loai, "quy": quy}


def goi_my_balance(world, actor_key: str, employee_id: int, loai) -> dict:
    from app.modules.leave.request_controller import my_balance

    return body(my_balance(leave_type_id=loai.id, year=YEAR, employee_id=employee_id,
                           db=world.db, user=world.actor(actor_key).user))


def test_15_my_balance_khong_doc_duoc_quy_cua_nguoi_ngoai_pham_vi(world, leave_world):
    """Vế CHẶN — `leave_request.read` KHÔNG còn là đường vòng qua khóa `leave_balance`.

    Trước bản vá, `resolve_leave_taker` là `db.get(Employee, ...)` trần: truyền
    `employee_id` lên URL là đọc `total_days` / `used_days` / `remaining_days`
    của bất kỳ ai, kể cả pháp nhân khác.
    """
    from app.modules.leave import balance_service

    world.grant("a1", "leave_request", scope="own")

    with pytest.raises(HTTPException) as loi:
        goi_my_balance(world, "a1", world.emp["b1"], leave_world["loai"])
    assert loi.value.status_code == 404

    #  Và KHÔNG được để lại dấu vết: `ensure_balance` cấp phát lúc chạm tới, nên
    #  một lượt dò id không được phép ghi thêm dòng quỹ nào.
    assert balance_service.get_balance(world.db, world.emp["khongphong"], YEAR,
                                       leave_world["loai"].id) is None


def test_15_my_balance_van_doc_duoc_quy_cua_chinh_minh_khong_can_khoa_moi(world, leave_world):
    """Vế KHÔNG CHẶN NHẦM (1) — quỹ của CHÍNH MÌNH không đòi thêm khóa nào.

    Ràng buộc §6.1: form nộp đơn phải hiện số phép còn lại. Bắt cấp thêm
    `leave_balance.read` cho nhân viên thường là chắc chắn có người quên cấp,
    rồi ô đó hiện 0 vĩnh viễn.
    """
    world.grant("a1", "leave_request", scope="own")

    ket_qua = goi_my_balance(world, "a1", 0, leave_world["loai"])
    assert ket_qua["employee_id"] == world.emp["a1"]
    assert ket_qua["used_days"] == 1.0
    assert ket_qua["total_days"] == 12.0


def test_15_my_balance_hanh_chinh_van_xem_ho_duoc_nguoi_trong_pham_vi(world, leave_world):
    """Vế KHÔNG CHẶN NHẦM (2) — hành chính lập hộ vẫn xem được quỹ người trong phạm vi.

    a3 có `leave_balance` bậc `company` (pháp nhân A): xem hộ a2 thì được, xem
    hộ b1 (pháp nhân B) thì không. Đúng ranh giới, không phải khóa sạch.
    """
    world.grant("a3", "leave_request", scope="company")
    world.grant("a3", "leave_balance", scope="company")

    trong_pham_vi = goi_my_balance(world, "a3", world.emp["a2"], leave_world["loai"])
    assert trong_pham_vi["employee_id"] == world.emp["a2"]
    assert trong_pham_vi["used_days"] == 2.0

    with pytest.raises(HTTPException) as loi:
        goi_my_balance(world, "a3", world.emp["b1"], leave_world["loai"])
    assert loi.value.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
#  #18 — DELETE /api/survey-requests (xóa hàng loạt)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def sr_world(world):
    db = world.db
    rows = {
        "A": create_survey_request(db, code="SR-A", company_id=world.co["A"],
                                   department_id=world.dept["A.kt"],
                                   created_by=world.user_id("a1")),
        "B": create_survey_request(db, code="SR-B", company_id=world.co["B"],
                                   department_id=world.dept["B.kt"],
                                   created_by=world.user_id("b1")),
    }
    db.commit()
    return {k: v.id for k, v in rows.items()}


def con_lai(db) -> set[int]:
    from app.modules.survey_request.model import SurveyRequest

    return {row.id for row in db.query(SurveyRequest).all()}


def test_18_xoa_hang_loat_ycbg_bo_qua_id_ngoai_pham_vi(world, sr_world):
    """Vế CHẶN + vế KHÔNG CHẶN NHẦM trong một ca — đúng khuôn `contract`.

    Gửi lên cả hai id: phiếu trong phạm vi PHẢI bị xóa (nếu không thì nút Xóa
    hàng loạt chết), phiếu ngoài phạm vi PHẢI còn nguyên, và câu báo phải nói số
    ĐÃ xóa chứ không nói số đã gửi lên.
    """
    from app.modules.survey_request.controller import bulk_delete_survey_requests

    world.grant("a1", "survey_request", scope="company", actions=("read", "delete"))

    ket_qua = bulk_delete_survey_requests(ids=f"{sr_world['A']},{sr_world['B']}",
                                          db=world.db, user=world.actor("a1").user)
    assert message(ket_qua) == "Đã xóa 1 bản ghi"
    assert con_lai(world.db) == {sr_world["B"]}


def test_18_xoa_hang_loat_ycbg_toan_id_ngoai_pham_vi_thi_403(world, sr_world):
    """Gửi toàn id ngoài phạm vi → 403, không xóa gì, không báo "đã xóa 0"."""
    from app.modules.survey_request.controller import bulk_delete_survey_requests

    world.grant("a1", "survey_request", scope="company", actions=("read", "delete"))

    with pytest.raises(HTTPException) as loi:
        bulk_delete_survey_requests(ids=str(sr_world["B"]), db=world.db,
                                    user=world.actor("a1").user)
    assert loi.value.status_code == 403
    assert con_lai(world.db) == {sr_world["A"], sr_world["B"]}
