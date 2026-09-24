"""Tab «Tệp» của văn bản (phase 09, duoc-CR-478) —
`GET /api/documents/{id}/attachments`.

Khác `GET /api/attachments?entity=document_version&entity_id=<phiên bản>`
(chỉ MỘT phiên bản): đường này gộp tệp của MỌI phiên bản trong một lần gọi,
kèm `version_id`/`version_no`/`is_current_version` để giao diện dựng cây theo
phiên bản mà không phải gọi API cho từng bản.

Quyền đọc đi qua `_load` (đúng khuôn `GET /api/documents/{id}`) — bài kiểm ở
đây monkeypatch thẳng `_load` để tách phần LOGIC GỘP TỆP (thứ mới, cần kiểm)
khỏi phần KIỂM QUYỀN (đã có bộ kiểm riêng ở `test_pham_vi_van_thu.py`).
"""
import json
from types import SimpleNamespace

from app.modules.attachment.model import FileLink, StoredFile
from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document import files_controller, service, version_service
from app.modules.document.schema import DocumentCreate, VersionCreate
from app.modules.document.version_model import DocumentVersion

ACTOR = 1
FAKE_USER = SimpleNamespace(id=ACTOR)


def payload(response) -> list:
    """Bóc phong bì `{success, message, data}` khỏi `JSONResponse` — cùng khuôn
    `test_pham_vi_van_thu.py`: `core.response.success()` trả `JSONResponse`
    chứ không trả dict khi gọi thẳng hàm controller."""
    return json.loads(response.body)["data"]


def _doc(db, seed):
    company = db.get(Company, seed.company_id)
    company.issue_code = "DEGO"
    doc_type = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(doc_type)
    db.commit()
    return service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế có tệp",
        content_html="<p>Bản 1</p>",
    ), ACTOR)


def _attach(db, version_id: int, filename: str, sort_order: int = 0) -> FileLink:
    stored = StoredFile(filename=filename, file_key=f"k-{filename}", url="https://kho/x",
                        content_type="application/pdf", size=10, sha256="abc")
    db.add(stored)
    db.flush()
    link = FileLink(file_id=stored.id, entity="document_version", entity_id=version_id,
                    doc_type="", sort_order=sort_order)
    db.add(link)
    db.flush()
    return link


def _stub_load(monkeypatch, doc):
    """Bỏ qua lớp quyền của `_load` (đã kiểm riêng ở `test_pham_vi_van_thu.py`),
    chỉ còn logic GỘP TỆP theo phiên bản — thứ MỚI cần kiểm ở tệp này."""
    monkeypatch.setattr(files_controller, "_load", lambda db, document_id, user: doc)


def test_khong_co_phien_ban_nao_tra_danh_sach_rong(db, seed, monkeypatch):
    """Ca lý thuyết (dữ liệu hỏng) — `version_ids` rỗng, không được nổ 500."""
    doc = _doc(db, seed)
    doc.current_version_id = None
    #  Xóa hẳn phiên bản 1.0 mà `create_document` vừa dựng, để tái hiện đúng ca
    #  "không phiên bản nào".
    db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).delete()
    db.commit()
    _stub_load(monkeypatch, doc)

    out = payload(files_controller.list_all_attachments(doc.id, db, FAKE_USER))
    assert out == []


def test_khong_co_tep_nao_tra_danh_sach_rong(db, seed, monkeypatch):
    doc = _doc(db, seed)
    _stub_load(monkeypatch, doc)
    out = payload(files_controller.list_all_attachments(doc.id, db, FAKE_USER))
    assert out == []


def test_mot_phien_ban_nhieu_tep_deu_danh_dau_dang_dung(db, seed, monkeypatch):
    doc = _doc(db, seed)
    _attach(db, doc.current_version_id, "a.pdf", sort_order=1)
    _attach(db, doc.current_version_id, "b.pdf", sort_order=0)
    _stub_load(monkeypatch, doc)

    out = payload(files_controller.list_all_attachments(doc.id, db, FAKE_USER))
    assert len(out) == 2
    assert all(row["is_current_version"] for row in out)
    assert all(row["version_id"] == doc.current_version_id for row in out)
    #  `sort_order` tăng dần trước — cùng thứ tự với `GET /api/attachments` gốc.
    assert [row["filename"] for row in out] == ["b.pdf", "a.pdf"]


def test_hai_phien_ban_gop_ca_hai_kem_dung_co_dang_dung(db, seed, monkeypatch):
    doc = _doc(db, seed)
    v1_id = doc.current_version_id
    _attach(db, v1_id, "ban-cu.pdf")

    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    #  Mở bản 2.0 rồi DUYỆT LUÔN — `open_new_version` một mình KHÔNG đổi
    #  `current_version_id` (văn bản vẫn "có hiệu lực" bằng bản cũ trong lúc
    #  bản mới còn nháp/đang duyệt, C16/C17); phải duyệt xong bản 2.0 mới thật
    #  sự trở thành "đang dùng" — đúng ca cây tệp cần kiểm (kịch bản 5, phase 09).
    v2 = version_service.open_new_version(db, doc, VersionCreate(change_summary="Sửa"), ACTOR)
    _attach(db, v2.id, "ban-moi.pdf")
    service.submit(db, doc, ACTOR)
    service.approve(db, doc, ACTOR)
    _stub_load(monkeypatch, doc)

    out = payload(files_controller.list_all_attachments(doc.id, db, FAKE_USER))
    by_name = {row["filename"]: row for row in out}
    assert set(by_name) == {"ban-cu.pdf", "ban-moi.pdf"}
    assert by_name["ban-moi.pdf"]["is_current_version"] is True
    assert by_name["ban-moi.pdf"]["version_id"] == v2.id
    assert by_name["ban-cu.pdf"]["is_current_version"] is False
    assert by_name["ban-cu.pdf"]["version_id"] == v1_id
    #  Cả hai phải mang version_no khác nhau để cây bên FE nhóm đúng.
    assert by_name["ban-moi.pdf"]["version_no"] != by_name["ban-cu.pdf"]["version_no"]


def test_tep_cua_entity_khac_khong_lot_vao(db, seed, monkeypatch):
    """`entity_id` của phiên bản văn bản có thể TRÙNG SỐ với id của một bản ghi
    khác (YCMH, bình luận…) — phải lọc đúng `entity == 'document_version'`,
    không chỉ lọc theo `entity_id`."""
    doc = _doc(db, seed)
    _attach(db, doc.current_version_id, "cua-van-ban.pdf")
    #  Một link mang ĐÚNG entity_id nhưng khác entity — không được xuất hiện.
    stored = StoredFile(filename="lac.pdf", file_key="lac", url="https://kho/y",
                        content_type="application/pdf", size=1, sha256="x")
    db.add(stored)
    db.flush()
    db.add(FileLink(file_id=stored.id, entity="purchase_request",
                    entity_id=doc.current_version_id, doc_type="", sort_order=0))
    db.commit()
    _stub_load(monkeypatch, doc)

    out = payload(files_controller.list_all_attachments(doc.id, db, FAKE_USER))
    assert [row["filename"] for row in out] == ["cua-van-ban.pdf"]


def test_url_van_rong_vi_entity_rieng_tu(db, seed, monkeypatch):
    """Đường này đi qua `_link_out` — phải giữ nguyên luật C03 (giấu `url`)."""
    doc = _doc(db, seed)
    _attach(db, doc.current_version_id, "mat.pdf")
    _stub_load(monkeypatch, doc)

    out = payload(files_controller.list_all_attachments(doc.id, db, FAKE_USER))
    assert out[0]["url"] == ""


def test_nguoi_tai_va_ngay_tai_deu_co_mat(db, seed, monkeypatch):
    """Cột «người tải · ngày» của bảng danh sách tệp — gộp MỘT truy vấn cho cả
    trang, không tra tên trong vòng lặp."""
    from app.modules.employee.model import Employee
    from app.modules.user.model import User

    doc = _doc(db, seed)
    #  `_doc` tạo văn bản bằng `service.create_document(..., ACTOR)` nên
    #  `created_by` của link sẽ mang id tài khoản seed sẵn (`emp_req`/`u_req`)
    #  khi ta gắn tệp bằng chính actor đó — dựng một user/employee RIÊNG để
    #  chắc chắn tên tra ra đúng người, không trùng ai khác trong `seed`.
    emp = Employee(code="UPLOADER", full_name="Người Tải Tệp", company_id=seed.company_id,
                   department_id=seed.dept_id, is_active=True)
    db.add(emp)
    db.flush()
    user = User(email="uploader@test", employee_id=emp.id, password_hash="x", is_active=True)
    db.add(user)
    db.flush()

    link = _attach(db, doc.current_version_id, "co-nguoi-tai.pdf")
    link.created_by = user.id
    db.commit()
    _stub_load(monkeypatch, doc)

    out = payload(files_controller.list_all_attachments(doc.id, db, FAKE_USER))
    assert out[0]["created_by_name"] == "Người Tải Tệp"
    assert out[0]["created_at"] != ""


def test_nguoi_tai_khong_co_ho_so_nhan_su_thi_ten_rong_khong_nem_loi(db, seed, monkeypatch):
    """`created_by = 0` (chưa gắn ai, hoặc tài khoản đã xóa) không được làm sập
    truy vấn gộp tên — trả chuỗi rỗng."""
    doc = _doc(db, seed)
    link = _attach(db, doc.current_version_id, "khong-ro-nguoi-tai.pdf")
    link.created_by = 0
    db.commit()
    _stub_load(monkeypatch, doc)

    out = payload(files_controller.list_all_attachments(doc.id, db, FAKE_USER))
    assert out[0]["created_by_name"] == ""
