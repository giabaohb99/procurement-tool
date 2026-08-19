"""CR-088 — BỘ LỌC TRÊN MÀN HÌNH ĐỔI SANG LỌC BẰNG ID.

Nối tiếp CR-086/087: chứng từ đã neo `department_id` / `nspt_id` / `head_of_dept_id`, nhưng
thanh lọc vẫn gửi CHUỖI TÊN và `apply_filters` so bằng `LIKE %tên%`. Ba chỗ hỏng, bài này chốt
đủ cả ba:

```
đổi tên phòng          →  lọc theo id vẫn ra phiếu cũ (phiếu giữ tên cũ trong ảnh chụp)
hai người trùng tên    →  lọc một người KHÔNG ra đơn của người kia
LIKE là khớp chuỗi con →  lọc "Hân" không kéo theo "Nguyễn Thị Ngọc Hân"
```

Cộng thêm hai cái bẫy của thời kỳ quá độ:
- dòng chưa điền lùi được id (`= 0`) vẫn phải so bằng TÊN, nếu không nó biến mất khỏi màn hình;
- `apply_filters` phải NHƯỜNG ô tham chiếu, kẻo nó so khớp chính xác thêm một lần rồi AND chồng
  lên nhánh lùi — nhánh lùi coi như không tồn tại.

Gọi thẳng hàm lọc chứ không qua HTTP: bài kiểm nhắm vào mệnh đề WHERE sinh ra, đi vòng qua
TestClient chỉ thêm lớp xác thực/phân quyền không liên quan.
"""
from starlette.datastructures import QueryParams

from app.core.base_controller import apply_filters
from app.core.ref_filter import apply_ref_filters, owns
from app.modules.department.model import Department
from app.modules.employee.model import Employee
from app.modules.purchase_order import service as po_service
from app.modules.purchase_order.model import PurchaseOrder


class _Req:
    """Chỉ cần đúng một thứ: `query_params`. `collect_conditions_map` gọi `multi_items()`
    nên phải là `QueryParams` thật, dict trần không đủ."""

    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _po(db, code, *, company_id, department_id=0, department="", nspt_id=0, nspt=""):
    po = PurchaseOrder(code=code, company_id=company_id,
                       department_id=department_id, department=department,
                       nspt_id=nspt_id, nspt=nspt, status="approved")
    db.add(po)
    db.commit()
    return po


def _loc(db, **params):
    """Đúng đường mà `purchase_order/controller._list_query` đi: lọc trần + lọc ô tham chiếu."""
    req = _Req(**params)
    q = apply_filters(db.query(PurchaseOrder), PurchaseOrder, req, po_service.FILTERABLE)
    q = apply_ref_filters(q, PurchaseOrder, req, db)
    return sorted(p.code for p in q.all())


def _emp(db, code, full_name, company_id, dept_id):
    e = Employee(code=code, full_name=full_name, company_id=company_id,
                 department_id=dept_id, is_active=True)
    db.add(e)
    db.commit()
    return e


# ── Hai người trùng tên ──────────────────────────────────────────────────────────
def test_hai_nguoi_trung_ten_loc_ra_dung_don_cua_tung_nguoi(db, seed):
    """Chính là lỗ hổng CR-087 vừa bịt ở phần PHẠM VI, nay bịt nốt ở phần BỘ LỌC.
    Lọc theo tên thì hai người trùng tên xem được đơn của nhau."""
    kia = _emp(db, "NV-TRUNG", "Trưởng Phòng", seed.company_id, seed.dept_id)
    _po(db, "PO-MINH", company_id=seed.company_id, nspt_id=seed.emp_tp_id, nspt="Trưởng Phòng")
    _po(db, "PO-KIA", company_id=seed.company_id, nspt_id=kia.id, nspt="Trưởng Phòng")

    assert _loc(db, nspt_id=str(seed.emp_tp_id)) == ["PO-MINH"]
    assert _loc(db, nspt_id=str(kia.id)) == ["PO-KIA"]
    # Đường cũ (lọc theo tên) gom cả hai — giữ lại đây làm bằng chứng vì sao phải đổi.
    assert _loc(db, nspt="Trưởng Phòng") == ["PO-KIA", "PO-MINH"]


def test_like_khong_con_vo_lay_ten_chua_chuoi_con(db, seed):
    """`LIKE %Hân%` kéo luôn mọi người có chữ "Hân" trong tên. Lọc theo id thì không."""
    han = _emp(db, "NV-HAN", "Hân", seed.company_id, seed.dept_id)
    ngoc_han = _emp(db, "NV-NGOCHAN", "Nguyễn Thị Ngọc Hân", seed.company_id, seed.dept_id)
    _po(db, "PO-HAN", company_id=seed.company_id, nspt_id=han.id, nspt="Hân")
    _po(db, "PO-NGOCHAN", company_id=seed.company_id, nspt_id=ngoc_han.id,
        nspt="Nguyễn Thị Ngọc Hân")

    assert _loc(db, nspt_id=str(han.id)) == ["PO-HAN"]
    assert _loc(db, nspt="Hân") == ["PO-HAN", "PO-NGOCHAN"]     # đường cũ vẫn vơ cả hai


# ── Đổi tên phòng ────────────────────────────────────────────────────────────────
def test_doi_ten_phong_bo_loc_van_ra_phieu_cu(db, seed):
    """Đơn giữ TÊN CŨ (ảnh chụp để in), phòng đã đổi tên. Lọc theo id vẫn phải ra."""
    _po(db, "PO-CU", company_id=seed.company_id, department_id=seed.dept_id,
        department="Phòng Test")
    db.get(Department, seed.dept_id).name = "Phòng Test (đổi tên)"
    db.commit()

    assert _loc(db, department_id=str(seed.dept_id)) == ["PO-CU"]
    assert _loc(db, department="Phòng Test (đổi tên)") == []    # đường cũ trượt sạch


# ── Nhánh lùi cho dòng id = 0 ────────────────────────────────────────────────────
def test_dong_chua_dien_lui_duoc_id_thi_so_bang_ten(db, seed):
    """Dev đang có 77/126 ĐMH `nspt_id = 0` (nhập lịch sử bằng biệt danh). Lọc thuần theo id là
    mấy dòng đó biến mất khỏi màn hình mà người dùng không hiểu vì sao."""
    _po(db, "PO-CO-ID", company_id=seed.company_id, nspt_id=seed.emp_tp_id, nspt="Trưởng Phòng")
    _po(db, "PO-KHONG-ID", company_id=seed.company_id, nspt_id=0, nspt="Trưởng Phòng")
    _po(db, "PO-NGUOI-KHAC", company_id=seed.company_id, nspt_id=0, nspt="NSTM Chính")

    assert _loc(db, nspt_id=str(seed.emp_tp_id)) == ["PO-CO-ID", "PO-KHONG-ID"]


def test_nhanh_lui_so_BANG_chu_khong_LIKE(db, seed):
    """Nhánh lùi so tên bằng `==`. Nếu lỡ dùng `LIKE` thì nó thừa hưởng luôn tật khớp chuỗi con
    mà CR-088 đang đi chữa."""
    _emp(db, "NV-HAN", "Hân", seed.company_id, seed.dept_id)
    han = db.query(Employee).filter(Employee.code == "NV-HAN").one()
    _po(db, "PO-CHUOI-CON", company_id=seed.company_id, nspt_id=0, nspt="Nguyễn Thị Ngọc Hân")

    assert _loc(db, nspt_id=str(han.id)) == []


def test_id_khac_thi_ten_trung_cung_khong_lot(db, seed):
    """Dòng ĐÃ có id của người khác thì tên trùng cũng không lọt — id là nguồn sự thật,
    nhánh lùi chỉ mở cho dòng id = 0."""
    kia = _emp(db, "NV-TRUNG", "Trưởng Phòng", seed.company_id, seed.dept_id)
    _po(db, "PO-KIA", company_id=seed.company_id, nspt_id=kia.id, nspt="Trưởng Phòng")

    assert _loc(db, nspt_id=str(seed.emp_tp_id)) == []


# ── `apply_filters` phải nhường ô tham chiếu ─────────────────────────────────────
def test_apply_filters_nhuong_o_tham_chieu(db, seed):
    """Bẫy AND chồng: `apply_filters` mà cũng so `department_id == X` thì AND với nhánh lùi
    (`department_id == 0`) ra rỗng — dòng chưa có id mất tích."""
    _po(db, "PO-KHONG-ID", company_id=seed.company_id, department_id=0, department="Phòng Test")

    req = _Req(department_id=str(seed.dept_id))
    chi_loc_tran = apply_filters(db.query(PurchaseOrder), PurchaseOrder, req,
                                 po_service.FILTERABLE)
    assert [p.code for p in chi_loc_tran.all()] == ["PO-KHONG-ID"]   # chưa lọc gì cả
    assert _loc(db, department_id=str(seed.dept_id)) == ["PO-KHONG-ID"]


def test_bang_chi_co_cot_id_van_loc_khop_chinh_xac(db, seed):
    """`tab_document.department_id` KHÔNG có cột tên đi kèm — bảng neo id ngay từ đầu, không có
    nợ nào để trả. Nhường nhầm cả bảng này là màn Văn thư hết lọc được phòng ban."""
    from app.modules.document.controller import FILTERABLE as DOC_FILTERABLE
    from app.modules.document.model import Document

    assert owns(PurchaseOrder, "department_id") is True
    assert owns(Document, "department_id") is False
    assert "department_id" in DOC_FILTERABLE

    # `ck_document_internal_required`: văn bản nội bộ bắt buộc có loại + pháp nhân + người phụ trách.
    chung = dict(doc_type_id=1, company_id=seed.company_id, owner_employee_id=seed.emp_req_id)
    db.add_all([
        Document(doc_code="VB-01", title="Của phòng mình", department_id=seed.dept_id, **chung),
        Document(doc_code="VB-02", title="Của phòng khác", department_id=seed.dept_id + 99, **chung),
    ])
    db.commit()
    q = apply_filters(db.query(Document), Document, _Req(department_id=str(seed.dept_id)),
                      DOC_FILTERABLE)
    assert [d.doc_code for d in q.all()] == ["VB-01"]


# ── Bộ lọc điều kiện (`<field>__<op>`) ───────────────────────────────────────────
def test_bo_loc_dieu_kien_dung_id_khop_thang(db, seed):
    """`nspt_id__eq=` khớp id THẲNG, không nhánh lùi: bộ lọc điều kiện là chỗ người dùng tự dựng
    mệnh đề, thêm nhánh ngầm vào là kết quả không còn giải thích được."""
    _po(db, "PO-CO-ID", company_id=seed.company_id, nspt_id=seed.emp_tp_id, nspt="Trưởng Phòng")
    _po(db, "PO-KHONG-ID", company_id=seed.company_id, nspt_id=0, nspt="Trưởng Phòng")

    assert _loc(db, nspt_id__eq=str(seed.emp_tp_id)) == ["PO-CO-ID"]
    assert _loc(db, nspt_id__ne=str(seed.emp_tp_id)) == ["PO-KHONG-ID"]


# ── Hai màn TIẾN ĐỘ: query JOIN, không đi qua `apply_filters` ────────────────────
def test_tien_do_mua_hang_loc_duoc_tren_query_join(db, seed):
    """`purchase_progress` tự đọc param chứ không dùng `apply_filters`, nên phải kiểm riêng:
    `apply_ref_filters` bám vào bảng ĐMH trong query join ba bảng, và nhánh lùi vẫn còn."""
    from app.modules.purchase_order.model import PODelivery, POItem

    for code, dept_id in (("PO-CO-ID", seed.dept_id), ("PO-KHONG-ID", 0), ("PO-KHAC", seed.dept_id + 99)):
        po = _po(db, code, company_id=seed.company_id, department_id=dept_id, department="Phòng Test")
        it = POItem(po_id=po.id, product_code="SP1", qty_order=1, price=1000)
        db.add(it); db.flush()
        db.add(PODelivery(po_id=po.id, po_item_id=it.id, delivery_no=1))
    db.commit()

    q = (db.query(PurchaseOrder, POItem, PODelivery)
         .join(POItem, POItem.po_id == PurchaseOrder.id)
         .outerjoin(PODelivery, PODelivery.po_item_id == POItem.id))
    req = _Req(department_id=str(seed.dept_id))
    assert sorted(po.code for po, _i, _d in apply_ref_filters(q, PurchaseOrder, req, db).all()) \
        == ["PO-CO-ID", "PO-KHONG-ID"]


def test_tien_do_bao_gia_loc_nguoi_yeu_cau_theo_id(db, seed):
    """`survey_progress` cũng là query join; ô Người yêu cầu của màn này neo bằng
    `SurveyRequest.requester_id` — cặp id/tên thứ tư trong `REF_PAIRS`."""
    from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine

    kia = _emp(db, "NV-TRUNG", "Người YC", seed.company_id, seed.dept_id)
    for code, rid in (("YC-MINH", seed.emp_req_id), ("YC-KIA", kia.id), ("YC-CU", 0)):
        sr = SurveyRequest(code=code, company_id=seed.company_id,
                           requester_id=rid, requester="Người YC", status="approved")
        db.add(sr); db.flush()
        db.add(SurveyRequestLine(survey_request_id=sr.id, item_group="Nhóm A"))
    db.commit()

    q = (db.query(SurveyRequest, SurveyRequestLine)
         .join(SurveyRequestLine, SurveyRequestLine.survey_request_id == SurveyRequest.id))
    req = _Req(requester_id=str(seed.emp_req_id))
    # "YC-KIA" trùng tên nhưng khác id -> không lọt; "YC-CU" chưa có id -> vào bằng nhánh lùi.
    assert sorted(sr.code for sr, _ln in apply_ref_filters(q, SurveyRequest, req, db).all()) \
        == ["YC-CU", "YC-MINH"]


# ── Giá trị rác ──────────────────────────────────────────────────────────────────
def test_id_rac_thi_bo_qua_chu_khong_vo_trang(db, seed):
    """Người dùng sửa tay URL là chuyện thường. Sai kiểu -> bỏ qua param, không raise."""
    _po(db, "PO-A", company_id=seed.company_id, department_id=seed.dept_id, department="Phòng Test")

    assert _loc(db, department_id="abc") == ["PO-A"]     # không phải số -> bỏ qua
    assert _loc(db, department_id="0") == ["PO-A"]       # 0 = "không chọn" -> bỏ qua
    assert _loc(db, department_id="") == ["PO-A"]
    assert _loc(db, department_id="999999") == []        # id có thật về mặt cú pháp -> lọc thật
