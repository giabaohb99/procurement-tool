"""duoc-CR-744 — bấm tiêu đề cột bảng VĂN BẢN ĐI xếp được tại SERVER.

Trước đây `GET /api/documents` chỉ nhận `?sort=-col` với 4 cột (id, book_seq_no, issued_at, created_at) và bảng
giao diện không có cột nào bấm được. Nay `sort_by`/`sort_dir` xếp theo ĐÚNG thứ ô đang hiện, trên cả tập, và tệp
Export ra cùng thứ tự. Kiểm: từng khóa cột, cả hai chiều; Loại / Pháp nhân / Phòng / Sổ / Người xếp theo TÊN;
Số hiệu = mã bất biến rồi tới số theo sổ; Số vào sổ theo (tiền tố, năm, số) chứ không theo chuỗi; Bản theo
(lớn, nhỏ); Trạng thái theo hạng vòng đời kể cả nhãn "Hết hiệu lực" / "Chưa hiệu lực" suy ra từ ngày; ô trống xuống
cuối; khóa phụ `id`; `?sort=` cũ vẫn chạy; khóa lạ / cột bị cấm về mặc định.

Không đụng DB thật — fixture SQLite in-memory ở conftest. Dữ liệu dùng chữ ASCII vì SQLite so chuỗi theo mã byte.
"""
import json
from datetime import timedelta
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.vn_time import vn_today
from app.modules.company.model import Company
from app.modules.department.model import Department
from app.modules.doc_catalog.book_model import DocumentBook
from app.modules.doc_catalog.model import DocType
from app.modules.document import controller, model as dm
from app.modules.document.model import Document
from app.modules.document.version_model import DocumentVersion
from app.modules.employee.model import Employee
from app.modules.user.model import User

PAGE = {"offset": 0, "limit": 100}


def _req(qs: str = ""):
    return SimpleNamespace(query_params=QueryParams(qs))


def _items(resp) -> list[dict]:
    return json.loads(resp.body)["data"]["items"]


@pytest.fixture()
def docs(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "document", read=True, export=True)
    today = vn_today()
    t_z = DocType(code="TZ", name="Zeta Loai", id_scheme=1, number_when=2)
    t_a = DocType(code="TA", name="Alpha Loai", id_scheme=1, number_when=2)
    db.add_all([t_z, t_a])
    cty_z = Company(code="DZC", name="Cty Zeta", is_active=True)
    cty_a = Company(code="DAC", name="Cty Alpha", is_active=True)
    db.add_all([cty_z, cty_a])
    dep_z = Department(code="DZD", name="Phong Zeta", is_active=True)
    dep_a = Department(code="DAD", name="Phong Alpha", is_active=True)
    db.add_all([dep_z, dep_a])
    owner_z = Employee(code="DZE", full_name="Zeta Chu", is_active=True)
    owner_a = Employee(code="DAE", full_name="Alpha Chu", is_active=True)
    db.add_all([owner_z, owner_a])
    db.flush()
    book_z = DocumentBook(code="BZ", name="So Zeta", number_prefix="CVD", company_id=cty_z.id, is_active=True)
    book_a = DocumentBook(code="BA", name="So Alpha", number_prefix="CVD", company_id=cty_a.id, is_active=True)
    db.add_all([book_z, book_a])
    db.flush()

    def _d(title, **kw):
        base = dict(origin=dm.ORIGIN_INTERNAL, title=title, doc_type_id=t_z.id, company_id=cty_z.id,
                    department_id=dep_z.id, owner_employee_id=owner_z.id, status=dm.STATUS_DRAFT)
        base.update(kw)
        doc = Document(**base)
        db.add(doc)
        db.flush()
        return doc

    #  d1: có hiệu lực, hết hạn hôm qua -> nhãn "Hết hiệu lực"; d2: có hiệu lực, bắt đầu ngày mai -> "Chưa hiệu lực";
    #  d3: có hiệu lực đang chạy; d4: nháp, để trống mọi ô; d5: đã từ chối.
    d1 = _d("Quy che ba", doc_code="QC-03", doc_type_id=t_a.id, company_id=cty_a.id, department_id=dep_a.id,
            owner_employee_id=owner_a.id, status=dm.STATUS_EFFECTIVE, effective_date=today - timedelta(days=30),
            expire_date=today - timedelta(days=1), book_id=book_z.id, book_seq_no=12, book_year=2026,
            secrecy_level=3, urgency=1, legacy_code="OLD-2", storage_location="Tu B")
    d2 = _d("Quy che mot", doc_code="QC-01", status=dm.STATUS_EFFECTIVE, effective_date=today + timedelta(days=1),
            book_id=book_z.id, book_seq_no=9, book_year=2026, secrecy_level=1, urgency=3, legacy_code="OLD-1",
            storage_location="Tu A")
    d3 = _d("Quy che hai", doc_code="", issue_number="08/2026/TB", status=dm.STATUS_EFFECTIVE,
            effective_date=today - timedelta(days=5), book_id=book_a.id, book_seq_no=9, book_year=2027,
            secrecy_level=2, urgency=2, legacy_code="", storage_location="Tu C")
    d4 = _d("", doc_code=None, issue_number="", doc_type_id=0, company_id=0, department_id=0,
            owner_employee_id=0, status=dm.STATUS_DRAFT, secrecy_level=2, urgency=1, legacy_code="",
            storage_location="")
    d5 = _d("Quy che nam", doc_code="QC-05", status=dm.STATUS_REJECTED, effective_date=None)
    #  Bản đang dùng: d1 = 2.10, d2 = 2.9, d3 = 1.0 -> "2.10" phải đứng SAU "2.9" (xếp theo chuỗi sai).
    for doc, major, minor in ((d1, 2, 10), (d2, 2, 9), (d3, 1, 0)):
        v = DocumentVersion(document_id=doc.id, major=major, minor=minor, status=1)
        db.add(v)
        db.flush()
        doc.current_version_id = v.id
    db.flush()
    return SimpleNamespace(user=db.get(User, seed.u_req_id), d1=d1, d2=d2, d3=d3, d4=d4, d5=d5)


def _ids(db, w, qs: str) -> list[int]:
    mine = {w.d1.id, w.d2.id, w.d3.id, w.d4.id, w.d5.id}
    resp = controller.list_documents(_req(qs), "", None, None, PAGE, db, w.user)
    return [it["id"] for it in _items(resp) if it["id"] in mine]


def test_so_hieu_la_ma_bat_bien_roi_toi_so_theo_so_o_trong_cuoi(db, docs):
    """d3 không có doc_code nên hiện issue_number '08/2026/TB'; d4 trống -> cuối cả hai chiều."""
    w = docs
    assert _ids(db, w, "sort_by=display_code&sort_dir=asc") == [w.d3.id, w.d2.id, w.d1.id, w.d5.id, w.d4.id]
    assert _ids(db, w, "sort_by=display_code&sort_dir=desc") == [w.d5.id, w.d1.id, w.d2.id, w.d3.id, w.d4.id]


def test_loai_phap_nhan_phong_chu_xep_theo_ten_khong_theo_id(db, docs):
    w = docs
    #  Loại Zeta (id nhỏ hơn) nhưng tên đứng sau Alpha. d4 không có loại / pháp nhân / phòng / người -> cuối.
    for key, alpha in (("doc_type_name", w.d1), ("company_name", w.d1), ("department_name", w.d1),
                       ("owner_name", w.d1)):
        asc = _ids(db, w, f"sort_by={key}&sort_dir=asc")
        desc = _ids(db, w, f"sort_by={key}&sort_dir=desc")
        assert asc[0] == alpha.id and asc[-1] == w.d4.id, key
        assert desc[-1] == w.d4.id and desc[-2] == alpha.id, key


def test_so_vao_so_xep_theo_so_nam_khong_theo_chuoi(db, docs):
    """Cùng tiền tố 'CVD': d2 = 09/2026, d1 = 12/2026, d3 = 09/2027 (sổ khác nhưng cùng tiền tố). Theo chuỗi
    '09/2027' sẽ đứng TRƯỚC '12/2026'; theo (năm, số) thì d3 đứng cuối. Chưa vào sổ (d4, d5) -> cuối."""
    w = docs
    asc = _ids(db, w, "sort_by=book_number_display&sort_dir=asc")
    assert asc[:3] == [w.d2.id, w.d1.id, w.d3.id] and set(asc[3:]) == {w.d4.id, w.d5.id}
    desc = _ids(db, w, "sort_by=book_number_display&sort_dir=desc")
    assert desc[:3] == [w.d3.id, w.d1.id, w.d2.id] and set(desc[3:]) == {w.d4.id, w.d5.id}


def test_ten_so_xep_theo_ten_so_ban_bang_nhau_theo_id_giam_dan(db, docs):
    """d3 ở 'So Alpha', d1 + d2 cùng 'So Zeta' (bằng nhau -> id giảm dần), d4 + d5 không có sổ -> cuối."""
    w = docs
    assert _ids(db, w, "sort_by=book_name&sort_dir=asc") == [w.d3.id, w.d2.id, w.d1.id, w.d5.id, w.d4.id]
    assert _ids(db, w, "sort_by=book_name&sort_dir=desc") == [w.d2.id, w.d1.id, w.d3.id, w.d5.id, w.d4.id]


def test_ban_xep_theo_so_lon_so_nho_khong_theo_chuoi(db, docs):
    """1.0 (d3) < 2.9 (d2) < 2.10 (d1). Theo chuỗi '2.10' đứng trước '2.9'. Không có bản (d4, d5) -> cuối."""
    w = docs
    asc = _ids(db, w, "sort_by=version_no&sort_dir=asc")
    assert asc[:3] == [w.d3.id, w.d2.id, w.d1.id] and set(asc[3:]) == {w.d4.id, w.d5.id}
    desc = _ids(db, w, "sort_by=version_no&sort_dir=desc")
    assert desc[:3] == [w.d1.id, w.d2.id, w.d3.id] and set(desc[3:]) == {w.d4.id, w.d5.id}


def test_trang_thai_xep_theo_hang_ke_ca_nhan_suy_ra_tu_ngay(db, docs):
    """Nháp(d4) < Chưa hiệu lực(d2) < Có hiệu lực(d3) < Hết hiệu lực(d1) < Đã từ chối(d5). Mã số thô (4,4,4,1,10)
    sẽ xếp d1/d2/d3 chung một nhóm và đặt d4 lên đầu bằng id."""
    w = docs
    assert _ids(db, w, "sort_by=status&sort_dir=asc") == [w.d4.id, w.d2.id, w.d3.id, w.d1.id, w.d5.id]
    assert _ids(db, w, "sort_by=status&sort_dir=desc") == [w.d5.id, w.d1.id, w.d3.id, w.d2.id, w.d4.id]


def test_ngay_hieu_luc_muc_mat_do_khan_xep_dung_o_trong_cuoi(db, docs):
    w = docs
    #  effective_date: d1 (-30) < d3 (-5) < d2 (+1); d4, d5 chưa có -> cuối.
    asc = _ids(db, w, "sort_by=effective_date&sort_dir=asc")
    assert asc[:3] == [w.d1.id, w.d3.id, w.d2.id] and set(asc[3:]) == {w.d4.id, w.d5.id}
    desc = _ids(db, w, "sort_by=effective_date&sort_dir=desc")
    assert desc[:3] == [w.d2.id, w.d3.id, w.d1.id] and set(desc[3:]) == {w.d4.id, w.d5.id}
    #  secrecy_level: d2=1 < d3,d4,d5=2 < d1=3 (bằng nhau -> id giảm dần).
    sec = _ids(db, w, "sort_by=secrecy_level&sort_dir=asc")
    assert sec[0] == w.d2.id and sec[-1] == w.d1.id and sec[1:4] == sorted([w.d3.id, w.d4.id, w.d5.id], reverse=True)


def test_cot_chu_o_trong_xuong_cuoi_ca_hai_chieu(db, docs):
    w = docs
    for key in ("title", "legacy_code", "storage_location"):
        asc = _ids(db, w, f"sort_by={key}&sort_dir=asc")
        desc = _ids(db, w, f"sort_by={key}&sort_dir=desc")
        assert w.d4.id in asc[-2:], key
        assert w.d4.id in desc[-2:], key
    assert _ids(db, w, "sort_by=title&sort_dir=asc")[-1] == w.d4.id
    assert _ids(db, w, "sort_by=title&sort_dir=desc")[-1] == w.d4.id


def test_so_tep_dinh_kem_0_la_o_trong(db, docs):
    from app.modules.attachment.model import FileLink
    w = docs
    for _ in range(2):
        db.add(FileLink(entity="document_version", entity_id=w.d3.current_version_id, file_id=1))
    db.add(FileLink(entity="document_version", entity_id=w.d1.current_version_id, file_id=1))
    db.flush()
    asc = _ids(db, w, "sort_by=attachment_count&sort_dir=asc")
    desc = _ids(db, w, "sort_by=attachment_count&sort_dir=desc")
    assert asc[:2] == [w.d1.id, w.d3.id] and desc[:2] == [w.d3.id, w.d1.id]
    #  Không tệp = 0 hiện trống -> cuối ở CẢ hai chiều.
    assert set(asc[2:]) == set(desc[2:]) == {w.d2.id, w.d4.id, w.d5.id}


def test_khoa_cu_sort_van_chay_va_sort_by_thang(db, docs):
    w = docs
    all_ids = [w.d1.id, w.d2.id, w.d3.id, w.d4.id, w.d5.id]
    resp = controller.list_documents(_req(), "", None, None, PAGE, db, w.user, sort="-id")
    got = [it["id"] for it in _items(resp) if it["id"] in all_ids]
    assert got == sorted(all_ids, reverse=True)
    resp = controller.list_documents(_req("sort_by=id&sort_dir=asc"), "", None, None, PAGE, db, w.user,
                                     sort="-id")
    got = [it["id"] for it in _items(resp) if it["id"] in all_ids]
    assert got == sorted(all_ids)   # sort_by thắng ?sort= cũ


def test_khoa_la_va_cot_bi_cam_ve_mac_dinh_khong_loi(db, docs):
    w = docs
    default = sorted([w.d1.id, w.d2.id, w.d3.id, w.d4.id, w.d5.id], reverse=True)
    for key in ("summary", "meta", "no_such_column", "'; DROP TABLE tab_document; --", "folder",
                "primary_folder_path"):
        assert _ids(db, w, f"sort_by={key}&sort_dir=asc") == default, key


def test_xuat_excel_di_cung_thu_tu_voi_bang(db, docs):
    """`export_xlsx` đọc cùng `sort_by`/`sort_dir`: lấy hàng đã xếp từ chính truy vấn dựng cho Export."""
    from app.modules.document import sort_expressions
    w = docs
    order = sort_expressions.build_order_by("status", "desc")
    assert order, "khóa status phải xếp được"
    rows = (db.query(Document.id).filter(Document.id.in_([w.d1.id, w.d2.id, w.d3.id, w.d4.id, w.d5.id]))
            .order_by(*order).all())
    assert [r[0] for r in rows] == [w.d5.id, w.d1.id, w.d3.id, w.d2.id, w.d4.id]


def test_moi_khoa_cua_bang_deu_xep_duoc_tru_cot_thu_muc_va_thao_tac():
    """Canh: thêm cột vào bảng frontend mà quên backend thì khóa thành lặng lẽ không xếp — bài này đỏ."""
    from app.modules.document import sort_expressions
    keys = ["id", "display_code", "book_number_display", "title", "doc_type_name", "company_name",
            "department_name", "book_name", "version_no", "status", "effective_date", "secrecy_level",
            "urgency", "owner_name", "legacy_code", "storage_location", "attachment_count",
            "book_seq_no", "drafter_name"]
    for key in keys:
        for direction in ("asc", "desc"):
            assert sort_expressions.build_order_by(key, direction), (key, direction)
    for key in ("folder", "copy_action", "", "x"):
        assert sort_expressions.build_order_by(key, "asc") == []
