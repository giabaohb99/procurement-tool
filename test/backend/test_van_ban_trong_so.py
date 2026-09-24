"""TAB «VĂN BẢN TRONG SỔ» (duoc-CR-474, 23/09/2026) — sort + lọc theo năm vào sổ.

Bốn việc backend thêm ở `document/controller.py` cho tab mới trong trang chi
tiết Sổ văn bản:

1. `?sort=` — whitelist RIÊNG (`SORTABLE_COLUMNS`), hẹp hơn mọi cột vật lý mà
   `apply_sort` cho phép. Tên lạ phải bị BỎ QUA an toàn, không ném lỗi, không
   lọt thành tên cột SQL tuỳ ý.
2. `book_seq_no` sắp GIẢM DẦN phải đẩy NULL (văn bản chưa vào sổ) xuống CUỐI.
3. `book_year` vào `FILTERABLE` — lọc đúng năm, không đụng `issue_year`.
4. `visible_condition` (lớp quyền) vẫn còn hiệu lực dù có `sort`/`book_year` —
   tab mới không phải là đường vòng qua quyền xem văn bản.

Gọi thẳng các hàm lọc/sắp xếp chứ không qua HTTP, cùng lối với
`test_loc_theo_id_cr088.py`: bài kiểm nhắm vào mệnh đề WHERE/ORDER BY sinh ra,
TestClient chỉ thêm lớp xác thực không liên quan.
"""
from types import SimpleNamespace

from starlette.datastructures import QueryParams

from app.core.base_controller import apply_filters, apply_sort
from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import access_service, controller, service
from app.modules.document.model import Document
from app.modules.document.query import documents_query
from app.modules.document.schema import DocumentCreate

ACTOR = 1


class _Req:
    """Chỉ cần đúng một thứ: `query_params` (`apply_filters` gọi `.items()`)."""

    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _doc_type(db, code="QC"):
    doc_type = DocType(code=code, name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()
    return doc_type


def _doc(db, seed, doc_type, title="Văn bản thử", **extra):
    doc = service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title=title, content_html="<p>x</p>",
    ), ACTOR)
    for key, val in extra.items():
        setattr(doc, key, val)
    db.commit()
    return doc


def _profile(employee_id=0, scope="own"):
    """Hồ sơ quyền tối thiểu — cùng hình dạng `test_document_access.py` dùng."""
    perms = {a: True for a in ("read", "create", "write", "delete",
                               "approve", "cancel", "print", "export")}
    perms["scope"] = scope
    return {
        "grants": [{"role_id": 1, "perms": {"document": perms}, "scope": {"inc": {}, "exc": {}}}],
        "company_id": 0, "dept_id": 0, "dept_name": "",
        "employee_id": employee_id, "emp_code": "", "emp_name": "",
    }


# ── Whitelist `?sort=` ───────────────────────────────────────────────────────
def test_sort_giam_dan_tach_dung_ten_cot_va_chieu():
    assert controller._sort_from_param("-book_seq_no") == ("book_seq_no", "desc")


def test_sort_tang_dan_khong_dau_gach():
    assert controller._sort_from_param("book_seq_no") == ("book_seq_no", "asc")


def test_sort_rong_ve_mac_dinh():
    assert controller._sort_from_param("") == ("", "asc")
    assert controller._sort_from_param("   ") == ("", "asc")


def test_sort_khong_phai_chuoi_khong_lam_no():
    """Regression: `list_documents` gọi TRỰC TIẾP (không qua HTTP) mà không
    truyền `sort` thì tham số vẫn còn nguyên đối tượng `Query(...)` của
    FastAPI — chỉ HTTP thật mới phân giải nó thành chuỗi. `_sort_from_param`
    từng gọi thẳng `.strip()` và nổ `AttributeError` ở đúng ca này
    (`test_pham_vi_van_thu.py::test_b9_...` gọi `list_documents(req, "", None,
    None, PAGE, db, user)` — thiếu `sort`)."""
    from fastapi import Query as FastapiQuery

    assert controller._sort_from_param(FastapiQuery("")) == ("", "asc")
    assert controller._sort_from_param(None) == ("", "asc")
    assert controller._sort_from_param(123) == ("", "asc")


def test_list_documents_goi_truc_tiep_thieu_tham_so_sort_khong_loi(db, seed):
    """Ghim đúng HÌNH DẠNG lời gọi mà `test_pham_vi_van_thu.py` dùng — đủ 7
    tham số vị trí (request, q, effective_from, effective_to, pg, db, user),
    THIẾU hẳn `sort` — để không ai vô tình chèn tham số mới xen giữa
    `effective_to` và `pg` một lần nữa (làm lệch vị trí của mọi tham số phía
    sau) mà không bị bài kiểm nào bắt được. Không đòi hỏi số liệu cụ thể (user
    dựng tay không có vai trò/phạm vi thật) — chỉ cần KHÔNG NỔ."""
    from starlette.datastructures import QueryParams

    class _Req:
        def __init__(self):
            self.query_params = QueryParams({})

    doc_type = _doc_type(db)
    _doc(db, seed, doc_type, title="Gọi trực tiếp thiếu sort")

    #  id lạ, tránh đụng cache quyền (`_PERM_CACHE`, khóa theo `user.id`) của
    #  các bài kiểm khác đang chạy chung tiến trình.
    user = SimpleNamespace(id=9_987_654, employee_id=seed.emp_req_id)
    response = controller.list_documents(
        _Req(), "", None, None, {"offset": 0, "limit": 20}, db, user,
    )
    #  `core.response.success()` trả `JSONResponse`, không phải dict — phải
    #  giải mã thân phản hồi mới đọc được (cùng cách `test_pham_vi_van_thu.py`
    #  làm ở hàm `payload()`).
    import json

    body = json.loads(response.body)
    assert body["success"] is True


def test_sort_ten_la_bi_bo_qua_khong_loi():
    """Tên cột lạ (kể cả cột THẬT của bảng nhưng không nằm trong whitelist hẹp)
    phải rơi về mặc định — không phải 500, không phải lỗi kiểu."""
    assert controller._sort_from_param("secrecy_level") == ("", "asc")
    assert controller._sort_from_param("-secrecy_level") == ("", "asc")
    #  Chuỗi rác / mưu toan tiêm SQL qua tên cột.
    assert controller._sort_from_param("id; DROP TABLE tab_document") == ("", "asc")
    assert controller._sort_from_param("-") == ("", "asc")


def test_moi_cot_trong_whitelist_deu_co_that_tren_bang():
    """Whitelist hẹp vẫn phải trỏ đúng cột thật — sai tên là `apply_sort` câm
    lặng bỏ qua (`valid = col is not None`), tab mới sắp xếp bằng chính `id desc`
    mà không ai biết vì sao."""
    cols = Document.__table__.columns.keys()
    for name in controller.SORTABLE_COLUMNS:
        assert name in cols, f"{name} không phải cột thật của tab_document"


# ── `book_seq_no` giảm dần đẩy NULL xuống cuối ──────────────────────────────
def test_sap_giam_dan_theo_so_vao_so_day_null_xuong_cuoi(db, seed):
    doc_type = _doc_type(db)
    #  d1 chưa vào sổ (book_seq_no = None) — mặc định `create_document` để trống.
    d1 = _doc(db, seed, doc_type, title="Chưa vào sổ")
    d2 = _doc(db, seed, doc_type, title="Số 3", book_seq_no=3)
    d3 = _doc(db, seed, doc_type, title="Số 1", book_seq_no=1)
    assert d1.book_seq_no is None

    query = apply_sort(documents_query(db), Document, "book_seq_no", "desc",
                       default=Document.id.desc(), nulls_last=("book_seq_no",))
    ids = [row.id for row in query.all()]

    #  Số lớn trước, số nhỏ sau, NULL luôn ở cuối — dù đang sắp GIẢM dần.
    assert ids == [d2.id, d3.id, d1.id]


def test_sap_tang_dan_theo_so_vao_so_van_day_null_xuong_cuoi(db, seed):
    """`nulls_last` không phụ thuộc chiều sắp — tăng dần cũng phải đẩy NULL cuối,
    nếu không văn bản chưa vào sổ (id=NULL) lại đứng đầu bảng."""
    doc_type = _doc_type(db)
    d1 = _doc(db, seed, doc_type, title="Chưa vào sổ")
    d2 = _doc(db, seed, doc_type, title="Số 1", book_seq_no=1)
    d3 = _doc(db, seed, doc_type, title="Số 2", book_seq_no=2)

    query = apply_sort(documents_query(db), Document, "book_seq_no", "asc",
                       default=Document.id.desc(), nulls_last=("book_seq_no",))
    ids = [row.id for row in query.all()]

    assert ids == [d2.id, d3.id, d1.id]


def test_khong_gui_sort_thi_mac_dinh_id_desc(db, seed):
    """Tham số rỗng (`_sort_from_param("")`) → `apply_sort` rơi về `default`."""
    doc_type = _doc_type(db)
    d1 = _doc(db, seed, doc_type, title="Cũ")
    d2 = _doc(db, seed, doc_type, title="Mới")

    sort_by, sort_dir = controller._sort_from_param("")
    query = apply_sort(documents_query(db), Document, sort_by, sort_dir,
                       default=Document.id.desc(), nulls_last=("book_seq_no",))
    ids = [row.id for row in query.all()]

    assert ids == [d2.id, d1.id]


# ── Lọc theo NĂM VÀO SỔ (`book_year`) ────────────────────────────────────────
def test_loc_theo_book_year(db, seed):
    doc_type = _doc_type(db)
    nam_nay = _doc(db, seed, doc_type, title="Sổ 2026", book_year=2026)
    nam_truoc = _doc(db, seed, doc_type, title="Sổ 2025", book_year=2025)

    req = _Req(book_year="2026")
    query = apply_filters(documents_query(db), Document, req, controller.FILTERABLE)
    titles = {row.title for row in query.all()}

    assert titles == {"Sổ 2026"}
    assert nam_nay.id  # giữ tham chiếu, tránh cảnh báo biến không dùng
    assert nam_truoc.id


def test_book_year_khong_dung_nham_issue_year(db, seed):
    """Hai cột NĂM khác nhau: `issue_year` (năm ban hành theo số hiệu chung)
    và `book_year` (năm vào MỘT quyển sổ cụ thể) không được trộn lẫn."""
    doc_type = _doc_type(db)
    doc = _doc(db, seed, doc_type, title="Lệch năm", issue_year=2025, book_year=2026)

    req = _Req(book_year="2026")
    query = apply_filters(documents_query(db), Document, req, controller.FILTERABLE)
    assert doc.id in [row.id for row in query.all()]

    req_sai = _Req(book_year="2025")
    query_sai = apply_filters(documents_query(db), Document, req_sai, controller.FILTERABLE)
    assert doc.id not in [row.id for row in query_sai.all()]


# ── Lớp quyền vẫn áp dụng dù có `sort`/`book_year` ──────────────────────────
def test_visible_condition_van_loc_du_dang_sap_theo_so_vao_so(db, seed):
    """Người ngoài phạm vi (`scope=own`, không phải chủ) không được thấy văn
    bản dù bảng đang sắp theo `-book_seq_no` — tab mới không phải cửa sau."""
    doc_type = _doc_type(db)
    owned = _doc(db, seed, doc_type, title="Của người yêu cầu", book_seq_no=1)

    outsider = SimpleNamespace(id=999, employee_id=seed.emp_tp_id)
    profile = _profile(employee_id=seed.emp_tp_id, scope="own")

    cond = access_service.visible_condition(outsider, profile)
    query = documents_query(db)
    if cond is not None:
        query = query.filter(cond)
    query = apply_sort(query, Document, "book_seq_no", "desc",
                       default=Document.id.desc(), nulls_last=("book_seq_no",))

    assert [row.id for row in query.all()] == []
    assert owned.id  # văn bản có thật, chỉ là người ngoài không thấy


def test_visible_condition_chu_van_thay_van_ban_cua_minh_khi_sap_theo_so(db, seed):
    doc_type = _doc_type(db)
    owned = _doc(db, seed, doc_type, title="Của người yêu cầu", book_seq_no=1)

    owner = SimpleNamespace(id=1, employee_id=seed.emp_req_id)
    profile = _profile(employee_id=seed.emp_req_id, scope="own")

    cond = access_service.visible_condition(owner, profile)
    query = documents_query(db)
    if cond is not None:
        query = query.filter(cond)
    query = apply_sort(query, Document, "book_seq_no", "desc",
                       default=Document.id.desc(), nulls_last=("book_seq_no",))

    assert [row.id for row in query.all()] == [owned.id]
