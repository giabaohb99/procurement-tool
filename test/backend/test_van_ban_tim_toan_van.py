"""TÌM KIẾM TOÀN VĂN văn bản (phase 07, duoc-CR-477) — `search_service` +
`search_index_service` + `search_extract` + móc nối các đường lưu.

Gọi thẳng `search_service.search(...)` (không qua HTTP): nhắm vào logic gập
dấu/cụm/loại trừ/điểm/đoạn trích và luật phạm vi, đi vòng qua `TestClient` chỉ
thêm một lớp xác thực không liên quan — cùng quy ước với các tệp cụm 07/08.

Bộ kiểm này chạy trên SQLite (nhánh LIKE của `search_service`, không phải
FULLTEXT MySQL) — kiểm ĐÚNG luật khớp/gập dấu/cụm/loại trừ/phạm vi/đoạn trích,
những thứ độc lập với dialect. Bản FULLTEXT thật kiểm TAY trên MySQL local
(ghi số liệu trong báo cáo triển khai, không lặp lại ở đây).
"""
import hashlib
import json
from datetime import date, timedelta
from types import SimpleNamespace

import pytest
from starlette.datastructures import QueryParams

from app.core.config import settings as core_settings
from app.modules.document import search_extract, search_index_service, search_service
from app.modules.document import service as doc_service
from app.modules.document import version_service
from app.modules.document.access_model import SUBJECT_EMPLOYEE, EFFECT_DENY
from app.modules.document.schema import AccessGrant, DocumentCreate, VersionContentUpdate
from app.modules.document.search_model import DocumentSearch
from app.modules.document.version_model import DocumentVersion

#  ⚠️ KHÔNG dùng số nhỏ (1, 2, 3…): `seed`/`world` cấp `id` tự tăng từ 1 cho cả
#  `User` lẫn `Employee`, nên một ACTOR trùng số dễ vô tình khớp một tài khoản
#  thật trong bài kiểm (dính đúng chốt `access_service.block_self_ban` — actor
#  "tự cấm chính mình" ở `test_thay_mot_phan_ba_van_ban_chi_thay_mot`).
ACTOR = 999999
ACTIONS = ("read", "create", "write", "delete", "approve", "cancel", "print", "export")


# ── Hạ tầng dựng dữ liệu ─────────────────────────────────────────────────────
@pytest.fixture(autouse=True)
def _sync_index(monkeypatch):
    """Ép chỉ mục dựng ĐỒNG BỘ ngay trên session `db` của bài kiểm.

    Tiến trình pytest không có celery-worker nào tiêu thụ hàng đợi, và tác vụ
    nền lại mở `SessionLocal()` RIÊNG (MySQL thật) nên không bao giờ thấy được
    DB SQLite trong bộ nhớ của bài kiểm — xem `search_index_service.queue_reindex`.
    """
    monkeypatch.setattr(core_settings, "DOCUMENT_SEARCH_INDEX_SYNC", True)


def _profile(scope="all", company_id=0, employee_id=0):
    perms = {"document": {a: True for a in ACTIONS} | {"scope": scope}}
    return {"grants": [{"role_id": 1, "perms": perms, "scope": {"inc": {}, "exc": {}}}],
           "company_id": company_id, "dept_id": 0, "dept_name": "",
           "employee_id": employee_id, "emp_code": "", "emp_name": ""}


def _user(employee_id=0):
    return SimpleNamespace(id=ACTOR, employee_id=employee_id)


def _doc_type(db, code="QD"):
    from app.modules.doc_catalog.model import DocType

    kind = DocType(code=code, name=f"Loại {code}", id_scheme=2, number_when=2)
    db.add(kind)
    db.commit()
    return kind


def _tao(db, *, company_id, department_id, owner_employee_id, kind, title="Văn bản",
         content_html="", **extra):
    return doc_service.create_document(db, DocumentCreate(
        doc_type_id=kind.id, company_id=company_id, department_id=department_id,
        owner_employee_id=owner_employee_id, title=title, content_html=content_html,
        **extra,
    ), ACTOR)


def _request(**params):
    query = {k: str(v) for k, v in params.items() if v is not None}
    return SimpleNamespace(query_params=QueryParams(query))


def _search(db, q, *, user=None, profile=None, page=1, page_size=20, **params):
    user = user or _user()
    profile = profile or _profile()
    return search_service.search(db, _request(**params), user, profile, q,
                                 page=page, page_size=page_size)


@pytest.fixture()
def gia_lap_tep(monkeypatch):
    """`{sha256: bytes}` — nội dung THẬT của tệp trong bài kiểm, không gọi mạng
    (R2/kho app cũ). Khóa theo `sha256` — cột đã PERSIST, không phụ thuộc thuộc
    tính tạm có sống sót qua `db.commit()` (mặc định `expire_on_commit=True`) hay không.
    """
    kho: dict[str, bytes] = {}

    def _doc(f):
        return kho.get(f.sha256, b"")

    monkeypatch.setattr(search_index_service, "_read_attachment_bytes", _doc)
    return kho


def _attach_file(db, kho, version_id, *, filename, raw_bytes, sort_order=0):
    from app.modules.attachment.model import FileLink, StoredFile

    sha = hashlib.sha256(raw_bytes).hexdigest()
    f = StoredFile(filename=filename, file_key="k", url="u",
                   content_type="application/octet-stream",
                   size=len(raw_bytes), sha256=sha)
    db.add(f)
    db.flush()
    kho[sha] = raw_bytes
    link = FileLink(file_id=f.id, entity="document_version", entity_id=version_id,
                    sort_order=sort_order, created_by=ACTOR, updated_by=ACTOR)
    db.add(link)
    db.commit()
    return link, f


# ── Gập dấu / cụm / loại trừ / ký tự đặc biệt ───────────────────────────────
def test_gap_dau_khong_phan_biet_hoa_thuong(db, seed):
    kind = _doc_type(db, "QD1")
    _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, kind=kind, title="Quyết định về việc điều động")

    ra = _search(db, "quyet dinh dieu dong")
    assert ra["total"] == 1
    assert "quyet dinh" not in ra["items"][0]["title"].lower()  # tiêu đề vẫn giữ dấu gốc


def test_cum_tu_trong_ngoac_kep_khop_lien_mach(db, seed):
    kind = _doc_type(db, "QD2")
    lien_mach = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
                     owner_employee_id=seed.emp_req_id, title="Văn bản 1", kind=kind,
                     content_html="<p>Đây là bản hợp đồng lao động chính thức.</p>")
    roi_rac = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
                   owner_employee_id=seed.emp_req_id, title="Văn bản 2", kind=kind,
                   content_html="<p>Hợp đồng này liên quan tới người lao động và tiền lương.</p>")

    ra = _search(db, '"hợp đồng lao động"')
    ids = {row["id"] for row in ra["items"]}
    assert ids == {lien_mach.id}, "cụm phải khớp LIỀN MẠCH, không khớp khi từ nằm rải rác"
    assert roi_rac.id not in ids


def test_loai_tru_bang_dau_tru(db, seed):
    kind = _doc_type(db, "QD3")
    may_in = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
                  owner_employee_id=seed.emp_req_id, title="Văn bản A", kind=kind,
                  content_html="<p>Máy in laser mới mua cho phòng kế toán.</p>")
    may_tinh = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
                    owner_employee_id=seed.emp_req_id, title="Văn bản B", kind=kind,
                    content_html="<p>Máy tính laser dùng thử, chưa quyết mua.</p>")

    ra = _search(db, "laser -tinh")
    ids = {row["id"] for row in ra["items"]}
    assert ids == {may_in.id}
    assert may_tinh.id not in ids


def test_ky_tu_dac_biet_fulltext_khong_lam_vo_cau_tim(db, seed):
    kind = _doc_type(db, "QD4")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title='Hợp đồng "đặc biệt"', kind=kind)

    #  Không crash, và cụm ký tự đặc biệt LẺ LOI (không kèm chữ) không được coi
    #  là một từ khóa — kết quả phải giống hệt tìm "hop dong" thuần.
    voi_dac_biet = _search(db, '+-*"()<>~@ hop dong')
    thuan = _search(db, "hop dong")
    assert {r["id"] for r in voi_dac_biet["items"]} == {r["id"] for r in thuan["items"]}
    assert doc.id in {r["id"] for r in voi_dac_biet["items"]}


# ── Biên: rỗng / 1 ký tự / 500 ký tự ────────────────────────────────────────
def test_cau_tim_rong_tra_rong_khong_liet_ke_tat_ca(db, seed):
    kind = _doc_type(db, "QD5")
    _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Bất kỳ văn bản nào", kind=kind)

    ra = _search(db, "")
    assert ra == {"total": 0, "items": [], "truncated": False}

    ra_khoang_trang = _search(db, "     ")
    assert ra_khoang_trang == {"total": 0, "items": [], "truncated": False}


def test_mot_ky_tu_tra_rong_khong_loi(db, seed):
    kind = _doc_type(db, "QD6")
    _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="A", kind=kind)

    ra = _search(db, "a")
    assert ra == {"total": 0, "items": [], "truncated": False}, \
        "token 1 ký tự không có ngram nào để khớp"


def test_cau_tim_500_ky_tu_khong_loi(db, seed):
    kind = _doc_type(db, "QD7")
    _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Văn bản dài", kind=kind)

    q = "từ khóa siêu dài " * 30  # > 500 ký tự
    assert len(q) > 500
    ra = _search(db, q)
    assert ra["total"] == 0
    assert ra["items"] == []


def test_cham_tran_ung_vien_bao_truncated(db, seed, monkeypatch):
    """M2 (rà soát 23/09/2026): SQL cắt ứng viên THÔ ở `CANDIDATE_LIMIT` TRƯỚC
    khi Python xếp hạng chính xác — quá trần phải báo `truncated=True`, không
    được lặng lẽ coi là "đã tìm hết". Hạ trần xuống 2 để không phải tạo hàng
    nghìn văn bản thật."""
    monkeypatch.setattr(search_service, "CANDIDATE_LIMIT", 2)

    kind = _doc_type(db, "QD7B")
    for i in range(3):
        _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
            owner_employee_id=seed.emp_req_id, title=f"Hợp đồng thi công số {i}", kind=kind)

    ra = _search(db, "hợp đồng")
    assert ra["truncated"] is True
    assert len(ra["items"]) <= 2


def test_khong_cham_tran_bao_truncated_false(db, seed):
    """Đối chứng: số ứng viên khớp DƯỚI trần thì `truncated` phải là `False`,
    không phải cứ có kết quả là báo cắt."""
    kind = _doc_type(db, "QD7C")
    _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Hợp đồng nguyên tắc", kind=kind)

    ra = _search(db, "hợp đồng")
    assert ra["truncated"] is False
    assert ra["total"] == 1


# ── Phạm vi: văn bản mật không lộ, thấy MỘT PHẦN ────────────────────────────
def test_van_ban_ngoai_pham_vi_khong_lo_ra(db, seed):
    """Văn bản ở PHÁP NHÂN KHÁC (ngoài phạm vi `company` của người tìm) không
    được lọt vào kết quả dù trúng từ khóa — K03: kết quả tìm không lộ cả tiêu đề."""
    from app.modules.company.model import Company

    other = Company(name="Cty Khác", code="CTK", is_active=True)
    db.add(other)
    db.commit()

    kind = _doc_type(db, "QD8")
    thay = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
               owner_employee_id=seed.emp_req_id, title="Báo cáo tài chính quý 3", kind=kind)
    _tao(db, company_id=other.id, department_id=0,
        owner_employee_id=seed.emp_req_id, title="Báo cáo tài chính quý 3 (Cty Khác)",
        kind=kind)

    profile = _profile(scope="company", company_id=seed.company_id)
    ra = _search(db, "bao cao tai chinh", profile=profile)
    ids = {row["id"] for row in ra["items"]}
    assert ids == {thay.id}
    assert ra["total"] == 1


def test_thay_mot_phan_ba_van_ban_chi_thay_mot(db, seed):
    """Ba văn bản cùng khớp từ khóa: một NGOÀI phạm vi pháp nhân, một bị CẤM
    đích danh, một thấy được — kết quả tìm phải khớp ĐÚNG phần thấy được, không
    thừa không thiếu (duoc-CR-475 "thấy một phần")."""
    from app.modules.company.model import Company

    other = Company(name="Cty Khác 2", code="CTK2", is_active=True)
    db.add(other)
    db.commit()

    kind = _doc_type(db, "QD9")
    EMP = seed.emp_req_id
    thay_duoc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
                     owner_employee_id=EMP, title="Kế hoạch mua sắm 2026", kind=kind)
    ngoai_pham_vi = _tao(db, company_id=other.id, department_id=0,
                        owner_employee_id=EMP, title="Kế hoạch mua sắm 2026 - B", kind=kind)
    bi_cam = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
                  owner_employee_id=EMP, title="Kế hoạch mua sắm 2026 - Mật", kind=kind)

    from app.modules.document import access_service

    access_service.grant(db, bi_cam, AccessGrant(
        subject_kind=SUBJECT_EMPLOYEE, subject_id=EMP, effect=EFFECT_DENY, can_read=True,
    ), ACTOR)

    profile = _profile(scope="company", company_id=seed.company_id, employee_id=EMP)
    user = _user(employee_id=EMP)
    ra = _search(db, "ke hoach mua sam", user=user, profile=profile)
    ids = {row["id"] for row in ra["items"]}
    assert ids == {thay_duoc.id}
    assert ngoai_pham_vi.id not in ids
    assert bi_cam.id not in ids
    assert ra["total"] == 1


# ── Kết hợp lọc thư mục ──────────────────────────────────────────────────────
def test_ket_hop_loc_theo_thu_muc(db, seed):
    """Hai văn bản cùng khớp từ khóa, mỗi văn bản tự vào thư mục PHÁP NHÂN của
    nó lúc tạo (không khai `folder_ids`) — lọc `folder_id=` phải tách đúng."""
    from app.modules.company.model import Company
    from app.modules.doc_catalog import folder_root_service

    other = Company(name="Cty Thư Mục", code="CTTM", is_active=True)
    db.add(other)
    db.commit()

    roots = {f.company_id: f for f in folder_root_service.ensure_company_roots(db)}
    #  Pháp nhân của `seed` có thể đã có gốc từ trước (tùy thứ tự chạy) — gọi
    #  lại vẫn an toàn (idempotent), nạp đủ CẢ HAI gốc.
    for f in folder_root_service.ensure_company_roots(db):
        roots[f.company_id] = f
    assert seed.company_id in roots and other.id in roots

    kind = _doc_type(db, "QD10")
    cua_seed = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
                    owner_employee_id=seed.emp_req_id, title="Thông báo lịch nghỉ lễ",
                    kind=kind)
    cua_other = _tao(db, company_id=other.id, department_id=0,
                     owner_employee_id=seed.emp_req_id, title="Thông báo lịch nghỉ lễ B",
                     kind=kind)

    profile = _profile(scope="all")
    ra_seed = _search(db, "thong bao lich nghi", profile=profile,
                      folder_id=roots[seed.company_id].id)
    assert {r["id"] for r in ra_seed["items"]} == {cua_seed.id}

    ra_other = _search(db, "thong bao lich nghi", profile=profile,
                       folder_id=roots[other.id].id)
    assert {r["id"] for r in ra_other["items"]} == {cua_other.id}


# ── Tệp đính kèm: đoạn trích chỉ khi cho phép ───────────────────────────────
def test_tep_qua_han_xem_khong_lot_va_khong_co_doan_trich(db, seed, gia_lap_tep, monkeypatch):
    from app.core import app_settings

    kind = _doc_type(db, "QD11")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title="Hồ sơ kèm phụ lục", kind=kind,
              attachment_view_until=date.today() - timedelta(days=1))
    _attach_file(db, gia_lap_tep, doc.current_version_id, filename="phu-luc.txt",
                raw_bytes="Mã số bí mật ABC-999-XYZ chỉ nằm trong tệp này.".encode("utf-8"))
    search_index_service.reindex(db, doc.id)

    #  Công tắc TẮT (mặc định) — xem thoải mái, có đoạn trích.
    ra_tat = _search(db, "ABC-999-XYZ")
    assert doc.id in {r["id"] for r in ra_tat["items"]}
    row_tat = next(r for r in ra_tat["items"] if r["id"] == doc.id)
    assert row_tat["search"]["snippet"] is not None
    assert row_tat["search"]["matched_in"] == "file"

    #  Công tắc BẬT — hạn xem đã qua, KHÔNG được xét `file_text`: từ khóa chỉ có
    #  trong tệp thì văn bản không còn lọt vào kết quả nữa.
    app_settings._cache["doc_attachment_view_window_enabled"] = "1"
    ra_bat = _search(db, "ABC-999-XYZ")
    assert doc.id not in {r["id"] for r in ra_bat["items"]}
    assert ra_bat["total"] == 0


def test_tep_con_han_van_thay_doan_trich_du_cong_tac_bat(db, seed, gia_lap_tep):
    from app.core import app_settings

    kind = _doc_type(db, "QD12")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title="Hồ sơ còn hạn", kind=kind,
              attachment_view_until=date.today() + timedelta(days=30))
    _attach_file(db, gia_lap_tep, doc.current_version_id, filename="con-han.txt",
                raw_bytes="Mã QLKX-777 nằm trong tệp còn hạn xem.".encode("utf-8"))
    search_index_service.reindex(db, doc.id)

    app_settings._cache["doc_attachment_view_window_enabled"] = "1"
    ra = _search(db, "QLKX-777")
    assert doc.id in {r["id"] for r in ra["items"]}
    row = next(r for r in ra["items"] if r["id"] == doc.id)
    assert row["search"]["snippet"] is not None
    assert row["search"]["match_label"].startswith("Tệp")


# ── Móc nối các đường LƯU (Rủi ro §: "hook bị bỏ sót") ──────────────────────
def test_tao_van_ban_tu_dong_len_chi_muc(db, seed):
    kind = _doc_type(db, "QD13")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title="Quy chế lương thưởng 2026", kind=kind)

    row = db.get(DocumentSearch, doc.id)
    assert row is not None
    assert "quy che luong thuong" in row.meta_text


def test_sua_van_ban_cap_nhat_chi_muc(db, seed):
    from app.modules.document.schema import DocumentUpdate

    kind = _doc_type(db, "QD14")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title="Tiêu đề cũ chưa sửa", kind=kind)

    doc = doc_service.update_document(db, doc, DocumentUpdate(title="Tiêu đề mới đã sửa"), ACTOR)

    row = db.get(DocumentSearch, doc.id)
    assert "tieu de moi da sua" in row.meta_text
    assert "tieu de cu chua sua" not in row.meta_text


def test_luu_noi_dung_phien_ban_cap_nhat_chi_muc(db, seed):
    kind = _doc_type(db, "QD15")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title="Văn bản đang soạn", kind=kind)
    version = db.get(DocumentVersion, doc.current_version_id)

    version_service.save_content(db, version, VersionContentUpdate(
        content_html="<p>Nội dung vừa gõ có từ khóa DUYNHAT888.</p>"), ACTOR)

    row = db.get(DocumentSearch, doc.id)
    assert "duynhat888" in row.body_text


def test_xoa_van_ban_xoa_luon_dong_chi_muc(db, seed):
    kind = _doc_type(db, "QD16")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title="Văn bản sắp xóa", kind=kind)
    doc_id = doc.id
    assert db.get(DocumentSearch, doc_id) is not None

    doc_service.delete_document(db, doc)

    assert db.get(DocumentSearch, doc_id) is None


def test_gan_va_go_tep_qua_controller_len_xuong_chi_muc(db, seed, gia_lap_tep, monkeypatch):
    """Đi qua ĐÚNG endpoint `attachment/controller.py` (không gọi thẳng
    `search_index_service`) — canh cửa móc `_reindex_document_search` đang
    treo trên `register_files`/`remove`, không phải hành vi của chính nó."""
    from app.core import attachment_scope as asc
    from app.modules.attachment import controller as ac
    from app.modules.attachment.model import StoredFile

    kind = _doc_type(db, "QD17")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title="Văn bản có tệp", kind=kind)
    version_id = doc.current_version_id

    profile = _profile(scope="all")
    user = SimpleNamespace(id=ACTOR, employee_id=0)
    monkeypatch.setattr(ac, "get_perm_profile", lambda db, u: profile)
    monkeypatch.setattr(asc, "get_perm_profile", lambda db, u: profile)
    monkeypatch.setattr(ac, "user_has_permission", lambda db, u, entity, action: True)
    monkeypatch.setattr(asc, "user_has_permission", lambda db, u, entity, action: True)

    raw = "Từ khóa GANLENXOAXUONG chỉ có trong tệp.".encode("utf-8")
    sha = hashlib.sha256(raw).hexdigest()
    gia_lap_tep[sha] = raw
    f = StoredFile(filename="dinh-kem.txt", file_key="k", url="u",
                   content_type="text/plain", size=len(raw), sha256=sha,
                   created_by=ACTOR, updated_by=ACTOR)
    db.add(f)
    db.commit()

    out = ac.register_files(
        ac.RegisterIn(entity="document_version", entity_id=version_id, file_ids=[f.id]),
        db, user,
    )
    link_id = json.loads(out.body)["data"][0]["id"]

    ra = _search(db, "GANLENXOAXUONG", profile=profile)
    assert doc.id in {r["id"] for r in ra["items"]}, "hook thêm tệp chưa dựng chỉ mục"

    ac.remove(link_id, db, user)

    ra_sau = _search(db, "GANLENXOAXUONG", profile=profile)
    assert doc.id not in {r["id"] for r in ra_sau["items"]}, "hook gỡ tệp chưa dựng lại chỉ mục"


# ── Trích chữ từ tệp — docx/xlsx/txt, tệp hỏng không làm vỡ lượt dựng ───────
def test_trich_chu_tu_docx_ca_bang(tmp_path):
    from docx import Document as DocxDocument

    doc = DocxDocument()
    doc.add_paragraph("Đoạn văn thường")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Ô trái BANGDOCX"
    table.rows[0].cells[1].text = "Ô phải"
    path = tmp_path / "mau.docx"
    doc.save(path)

    text = search_extract.extract_file_text("mau.docx", path.read_bytes())
    assert "Đoạn văn thường" in text
    assert "BANGDOCX" in text  # chữ trong BẢNG cũng phải trích được


def test_trich_chu_tu_xlsx(tmp_path):
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws["A1"] = "DULIEUXLSX"
    ws["B1"] = 12345
    path = tmp_path / "mau.xlsx"
    wb.save(path)

    text = search_extract.extract_file_text("mau.xlsx", path.read_bytes())
    assert "DULIEUXLSX" in text
    assert "12345" in text


def test_trich_chu_tep_txt():
    text = search_extract.extract_file_text("ghi-chu.txt", "Ghi chú tiếng Việt có dấu".encode("utf-8"))
    assert text == "Ghi chú tiếng Việt có dấu"


def test_tep_hong_khong_nem_loi_tra_rong():
    #  .docx giả — không phải zip hợp lệ.
    assert search_extract.extract_file_text("hong.docx", b"khong phai file docx that") == ""
    #  .pdf giả.
    assert search_extract.extract_file_text("hong.pdf", b"%PDF-khong-hop-le") == ""


def test_duoi_khong_ho_tro_tra_rong_khong_loi():
    assert search_extract.extract_file_text("anh.png", b"\x89PNG\r\n") == ""
    assert search_extract.extract_file_text("khong-co-duoi", b"abc") == ""


def test_tep_qua_20mb_khong_trich():
    big = b"a" * (search_extract.MAX_FILE_BYTES + 1)
    assert search_extract.extract_file_text("qua-lon.txt", big) == ""


# ── M11 (rà soát 23/09/2026) — trần SỐ TRANG của PDF ────────────────────────
def test_pdf_vuot_tran_trang_chi_trich_dan_dau(monkeypatch):
    """`MAX_FILE_BYTES` chặn được DUNG LƯỢNG nhưng không chặn được SỐ TRANG —
    một PDF rất nhiều trang gần trắng vẫn lọt dưới 20MB mà CPU vẫn ăn hết theo
    số trang. Hạ trần xuống 2 rồi đếm số lần `extract_text()` thật sự chạy
    trên một PDF 5 trang — phải DỪNG đúng ở trần, không trích hết."""
    import io

    from pypdf import PdfWriter
    from pypdf._page import PageObject

    monkeypatch.setattr(search_extract, "MAX_PDF_PAGES", 2)

    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    data = buf.getvalue()

    calls = {"n": 0}
    real_extract_text = PageObject.extract_text

    def _dem_roi_goi_that(self, *a, **kw):
        calls["n"] += 1
        return real_extract_text(self, *a, **kw)

    monkeypatch.setattr(PageObject, "extract_text", _dem_roi_goi_that)

    search_extract.extract_file_text("nhieu-trang.pdf", data)

    assert calls["n"] == 2, "phải dừng ĐÚNG ở MAX_PDF_PAGES, không trích hết 5 trang"


# ── Chỉ mục bỏ qua khi băm không đổi + không trích lại tệp khi bộ tệp giữ nguyên ──
def test_reindex_bo_qua_khi_khong_doi_gi(db, seed):
    kind = _doc_type(db, "QD18")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title="Văn bản ổn định", kind=kind)
    row1 = db.get(DocumentSearch, doc.id)
    moc1 = row1.indexed_at

    row2 = search_index_service.reindex(db, doc.id)
    assert row2.indexed_at == moc1, "không đổi gì thì không được ghi lại (đỡ một lượt ghi vô ích)"


def test_reindex_khong_trich_lai_tep_khi_bo_tep_khong_doi(db, seed, gia_lap_tep):
    kind = _doc_type(db, "QD19")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title="Văn bản có tệp ổn định", kind=kind)
    _attach_file(db, gia_lap_tep, doc.current_version_id, filename="a.txt",
                raw_bytes=b"noi dung tep")
    search_index_service.reindex(db, doc.id)
    row1 = db.get(DocumentSearch, doc.id)
    fingerprint1 = row1.file_fingerprint

    #  Đổi NỘI DUNG SOẠN THẢO (không đụng tệp) rồi dựng lại — `file_fingerprint`
    #  phải GIỮ NGUYÊN, chứng tỏ không trích lại tệp (chỉ dò qua CSDL, không gọi
    #  `_read_attachment_bytes` lần hai — xóa khỏi `gia_lap_tep` để chắc chắn).
    version = db.get(DocumentVersion, doc.current_version_id)
    version_service.save_content(db, version, VersionContentUpdate(
        content_html="<p>Nội dung đổi nhưng tệp thì không.</p>"), ACTOR)

    row2 = db.get(DocumentSearch, doc.id)
    assert row2.file_fingerprint == fingerprint1
    assert row2.file_text == row1.file_text  # vẫn còn (đọc lại từ dòng cũ, không trích lại)


# ── M11 (rà soát 23/09/2026) — lỗi reindex KHÔNG được lộ ra ngoài request ───
def test_queue_reindex_loi_khong_lam_vo_request(db, seed, monkeypatch):
    """`queue_reindex` LUÔN gọi SAU khi văn bản đã `commit` (xem docstring đầu
    `search_index_service.py`) — lỗi trích tệp/ghi chỉ mục ở đây KHÔNG được
    làm response trả 500 cho một thao tác THỰC RA đã thành công."""
    kind = _doc_type(db, "QD20")
    doc = _tao(db, company_id=seed.company_id, department_id=seed.dept_id,
              owner_employee_id=seed.emp_req_id, title="Văn bản lỗi reindex", kind=kind)

    def _no(*a, **kw):
        raise RuntimeError("giả lập lỗi trích tệp/ghi chỉ mục")

    monkeypatch.setattr(search_index_service, "reindex", _no)

    search_index_service.queue_reindex(db, doc.id)   # KHÔNG được ném lỗi ra ngoài
