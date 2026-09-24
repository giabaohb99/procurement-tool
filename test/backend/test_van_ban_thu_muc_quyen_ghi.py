"""Vá hai lỗ BẢO MẬT phase 04 để lại (duoc-CR-475, "Việc còn treo") — 23/09/2026.

1. `document/service.create_document`/`update_document` nay đòi mức ĐÓNG GÓP
   (`FolderAccessLevel.CONTRIBUTE`) trên MỌI thư mục MỚI THÊM trong
   `folder_ids` — cùng cửa `folder_link_bulk_service.move_documents` đã có cho
   gắn hàng loạt, nay áp thêm ở `POST`/`PATCH /api/documents` (trước đây lách
   được bằng cách gửi `folder_ids` thẳng trong hai request đó).
2. `dashboard_service.overview`/`scope_controller.applies_to_me` nay truyền
   `user` xuống `serializer.serialize_many` — trường `folders` không còn lộ
   tên thư mục riêng tư qua hai màn đó nữa; `serializer.serialize_many` cũng
   đổi mặc định sang ĐÓNG (rỗng) khi thiếu `user`, thay vì MỞ hết như trước.

Dựng trên thế giới mẫu `world` (`scope_factory.build_world`) — cùng nền với
`test_van_ban_thu_muc_quyen.py` (phase 04).
"""
import json

import pytest
from fastapi import HTTPException

from app.core.subject_match import EFFECT_ALLOW, SUBJECT_EMPLOYEE
from app.modules.doc_catalog import (folder_access_grant_service, folder_root_service,
                                     folder_service)
from app.modules.doc_catalog.folder_access_schema import FolderAccessGrantIn
from app.modules.doc_catalog.folder_constants import FolderAccessLevel
from app.modules.doc_catalog.folder_link_model import DocumentFolderLink
from app.modules.doc_catalog.folder_schema import FolderCreate, FolderUpdate
from app.modules.doc_catalog.model import DocType
from app.modules.document import dashboard_service, scope_controller, service
from app.modules.document.model import ORIGIN_INTERNAL, STATUS_EFFECTIVE, Document
from app.modules.document.schema import DocumentCreate, DocumentUpdate
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

VIEW = int(FolderAccessLevel.VIEW)
CONTRIBUTE = int(FolderAccessLevel.CONTRIBUTE)
PRIVATE = int(FolderAccessLevel.PRIVATE)


@pytest.fixture()
def roots(db, world):
    created = folder_root_service.ensure_company_roots(db)
    return {f.company_id: f for f in created}


@pytest.fixture()
def doc_type(db):
    row = DocType(code="QGT", name="Loại thử vá lỗ hổng", id_scheme=1, number_when=2)
    db.add(row)
    db.commit()
    return row


def _grant_folder(db, folder, *, subject_kind, subject_id, effect=EFFECT_ALLOW,
                  level=VIEW, actor=0, **kw):
    data = FolderAccessGrantIn(subject_kind=subject_kind, subject_id=subject_id,
                               effect=effect, level=level, **kw)
    return folder_access_grant_service.grant(db, folder, data, actor)


def _doc(db, *, company_id, department_id=0, code="X"):
    row = Document(origin=ORIGIN_INTERNAL, doc_type_id=0, company_id=company_id,
                   department_id=department_id, owner_employee_id=0, title=f"Văn bản {code}",
                   legacy_code=code, created_by=0, updated_by=0)
    db.add(row)
    db.flush()
    return row


def _link(db, doc, folder, primary=True):
    db.add(DocumentFolderLink(document_id=doc.id, folder_id=folder.id, is_primary=primary))
    db.flush()


def _linked_folder_ids(db, document_id) -> set[int]:
    return {row[0] for row in db.query(DocumentFolderLink.folder_id)
            .filter(DocumentFolderLink.document_id == document_id).all()}


def _create(db, world, doc_type, *, folder_ids, title="Văn bản"):
    a1 = world.actor("a1")
    return service.create_document(db, DocumentCreate(
        doc_type_id=doc_type.id, company_id=world.co["A"], department_id=world.dept["A.kt"],
        owner_employee_id=world.emp["a1"], title=title, folder_ids=folder_ids,
    ), a1.user.id, user=a1.user)


# ── Gap #1 — cửa ĐÓNG GÓP khi TẠO văn bản ────────────────────────────────────
def test_tao_van_ban_vao_thu_muc_chi_xem_bi_chan(db, world, roots, doc_type):
    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Chỉ xem"), 0)
    folder_service.update_folder(db, folder, FolderUpdate(default_access=PRIVATE), 0)
    _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"], level=VIEW)

    with pytest.raises(HTTPException) as exc:
        _create(db, world, doc_type, folder_ids=[folder.id], title="Bị chặn")
    assert exc.value.status_code == 403

    #  Chặn TRƯỚC khi ghi bất cứ gì — không để lại văn bản mồ côi.
    assert db.query(Document).filter(Document.title == "Bị chặn").count() == 0


def test_tao_van_ban_vao_thu_muc_du_dong_gop_thi_thanh_cong(db, world, roots, doc_type):
    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]   # mức nền CONTRIBUTE mặc định của gốc pháp nhân
    doc = _create(db, world, doc_type, folder_ids=[root.id], title="Vào được")
    assert _linked_folder_ids(db, doc.id) == {root.id}


def test_tao_van_ban_khong_gui_folder_ids_khong_bi_kiem(db, world, roots, doc_type):
    """Bỏ trống `folder_ids` → tự rơi về thư mục mặc định, không có gì để kiểm
    (đúng luật "Việc còn treo" #1 của phase 04: rỗng thì bỏ qua)."""
    doc = _create(db, world, doc_type, folder_ids=None, title="Mặc định")
    assert _linked_folder_ids(db, doc.id) == {roots[world.co["A"]].id}


def test_kiem_dong_gop_nhieu_thu_muc_chi_tinh_effective_levels_mot_lan(
        db, world, roots, doc_type, monkeypatch):
    """M1 (rà soát 23/09/2026): `effective_levels` (2 truy vấn NẶNG — mọi thư
    mục + mọi dòng ACL) phải tính MỘT LẦN cho cả danh sách `folder_ids`. Trước
    fix, `ensure_level` (gọi trong vòng lặp `_ensure_folder_contribute`) tự
    tính lại TOÀN BỘ ở MỖI id — N id là N lần gọi thay vì 1."""
    from app.modules.doc_catalog import folder_access_service

    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    folders = [
        folder_service.create_folder(db, FolderCreate(parent_id=root.id, name=f"F{i}"), 0)
        for i in range(5)
    ]
    for f in folders:
        _grant_folder(db, f, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                      level=CONTRIBUTE)

    calls = {"n": 0}
    real_effective_levels = folder_access_service.effective_levels

    def _dem_roi_goi_that(*a, **kw):
        calls["n"] += 1
        return real_effective_levels(*a, **kw)

    monkeypatch.setattr(folder_access_service, "effective_levels", _dem_roi_goi_that)
    _create(db, world, doc_type, folder_ids=[f.id for f in folders], title="Năm thư mục")

    assert calls["n"] == 1, (
        f"gọi effective_levels() {calls['n']} lần cho 5 thư mục — phải ĐÚNG 1 lần, "
        "không nhân theo số thư mục")


def test_thu_muc_khong_ton_tai_va_khong_thay_ra_cung_mot_cau_404(db, world, roots, doc_type):
    """Thư mục KHÔNG TỒN TẠI và thư mục TỒN TẠI NHƯNG KHÔNG THẤY phải ra CÙNG
    một câu lỗi chung — không dò được "thư mục có thật không" bằng cách thử id."""
    world.grant("a1", "document", scope="dept", actions=("read",))   # không với tới pháp nhân B
    root_b = roots[world.co["B"]]   # tồn tại thật, nhưng a1 không có ACL nào ở đó

    def _err(folder_id):
        with pytest.raises(HTTPException) as exc:
            _create(db, world, doc_type, folder_ids=[folder_id], title=f"Thử {folder_id}")
        return exc.value

    not_visible = _err(root_b.id)
    not_exist = _err(999999)
    assert not_visible.status_code == not_exist.status_code == 404
    assert not_visible.detail == not_exist.detail


# ── Gap #1 — cửa ĐÓNG GÓP khi SỬA văn bản (chỉ thư mục MỚI THÊM) ─────────────
def test_sua_them_thu_muc_moi_thieu_dong_gop_bi_chan(db, world, roots, doc_type):
    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    doc = _create(db, world, doc_type, folder_ids=[root.id], title="Gốc")

    other = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Thư mục lạ"), 0)
    folder_service.update_folder(db, other, FolderUpdate(default_access=PRIVATE), 0)
    _grant_folder(db, other, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"], level=VIEW)

    a1 = world.actor("a1")
    with pytest.raises(HTTPException) as exc:
        service.update_document(db, doc, DocumentUpdate(folder_ids=[root.id, other.id]),
                                a1.user.id, user=a1.user)
    assert exc.value.status_code == 403

    #  Thư mục GỐC (đã có từ trước) không hề bị đụng tới — `set_folders` chưa
    #  từng chạy vì cửa mới chặn TRƯỚC nó.
    assert _linked_folder_ids(db, doc.id) == {root.id}


def test_sua_van_ban_giu_nguyen_thu_muc_da_mat_dong_gop_van_luu_duoc(db, world, roots, doc_type):
    """Văn bản ĐÃ NẰM trong một thư mục; người dùng sau đó MẤT quyền Đóng góp ở
    đó (hạ còn Xem). Gửi lại ĐÚNG thư mục cũ (không thêm thư mục nào mới) thì
    vẫn lưu được — cửa mới chỉ chặn thư mục MỚI THÊM, không chặn sửa đổi khác
    không liên quan tới thư mục đó."""
    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Rồi mất quyền"), 0)
    folder_service.update_folder(db, folder, FolderUpdate(default_access=PRIVATE), 0)
    grant_row = _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE,
                              subject_id=world.emp["a1"], level=CONTRIBUTE)

    doc = _create(db, world, doc_type, folder_ids=[folder.id], title="Bản gốc")

    #  Hạ quyền: thu hồi Đóng góp, cấp lại chỉ mức Xem.
    folder_access_grant_service.revoke(db, folder, grant_row.id, "hạ quyền để kiểm", 0)
    _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"], level=VIEW)

    a1 = world.actor("a1")
    updated = service.update_document(
        db, doc, DocumentUpdate(title="Bản đã sửa", folder_ids=[folder.id]),
        a1.user.id, user=a1.user)

    assert updated.title == "Bản đã sửa"
    assert _linked_folder_ids(db, doc.id) == {folder.id}


def test_sua_khong_dung_toi_folder_ids_khong_bi_kiem(db, world, roots, doc_type):
    """Không gửi `folder_ids` trong `PATCH` (giữ `None`) = không đụng thư mục —
    luôn lưu được các trường khác dù người dùng không còn quyền gì trên thư mục
    văn bản đang nằm (kể cả mất VIEW hoàn toàn)."""
    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Khóa hẳn"), 0)
    grant_row = _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE,
                              subject_id=world.emp["a1"], level=CONTRIBUTE)
    doc = _create(db, world, doc_type, folder_ids=[folder.id], title="Bản gốc 2")

    #  Khóa nhánh + thu hồi ACL — a1 giờ KHÔNG THẤY thư mục này nữa.
    folder_service.update_folder(db, folder, FolderUpdate(default_access=PRIVATE), 0)
    folder_access_grant_service.revoke(db, folder, grant_row.id, "khóa hẳn để kiểm", 0)

    a1 = world.actor("a1")
    updated = service.update_document(db, doc, DocumentUpdate(title="Bản đã sửa 2"),
                                      a1.user.id, user=a1.user)
    assert updated.title == "Bản đã sửa 2"
    assert _linked_folder_ids(db, doc.id) == {folder.id}


# ── C1 (rà soát 23/09/2026) — `set_folders` xóa mất liên kết ẨN với người sửa ──
def test_thay_mot_phan_luu_link_an_con_nguyen(db, world, roots, doc_type):
    """Văn bản nằm ở HAI thư mục: A (a1 thấy, Đóng góp) + B (a1 KHÔNG thấy —
    riêng tư, không ACL). a1 mở «Sửa thư mục», chỉ thấy A, gửi lại
    `folder_ids=[A]` → B phải CÒN NGUYÊN, không bị xóa âm thầm (C1)."""
    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    folder_a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A thấy"), 0)
    _grant_folder(db, folder_a, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                  level=CONTRIBUTE)
    folder_b = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="B riêng tư"), 0)
    folder_service.update_folder(db, folder_b, FolderUpdate(default_access=PRIVATE), 0)
    #  a1 KHÔNG có ACL nào ở B — vô hình với a1.

    doc = _create(db, world, doc_type, folder_ids=[folder_a.id], title="Nằm hai thư mục")
    _link(db, doc, folder_b, primary=False)
    assert _linked_folder_ids(db, doc.id) == {folder_a.id, folder_b.id}

    a1 = world.actor("a1")
    service.update_document(db, doc, DocumentUpdate(folder_ids=[folder_a.id]),
                            a1.user.id, user=a1.user)

    assert _linked_folder_ids(db, doc.id) == {folder_a.id, folder_b.id}, \
        "gửi lại đúng thư mục ĐANG THẤY không phải là ý muốn gỡ phần còn lại"


def test_go_thu_muc_thay_nhung_thieu_dong_gop_bi_chan_403(db, world, roots, doc_type):
    """Văn bản nằm ở HAI thư mục a1 đều THẤY: A (chỉ Xem) + B (Đóng góp). a1 gửi
    lại CHỈ B (ngầm định gỡ A) → phải chặn 403 vì thiếu Đóng góp ở A, không được
    âm thầm cho gỡ (C1)."""
    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    folder_a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A chỉ xem"), 0)
    folder_service.update_folder(db, folder_a, FolderUpdate(default_access=PRIVATE), 0)
    _grant_folder(db, folder_a, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"], level=VIEW)
    folder_b = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="B đóng góp"), 0)
    _grant_folder(db, folder_b, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                  level=CONTRIBUTE)

    #  Dựng thẳng bằng `_doc`/`_link` (không qua `create_document`) — a1 chỉ có
    #  Xem ở A nên không TẠO được văn bản vào A qua cửa ĐÓNG GÓP lúc tạo; kịch
    #  bản kiểm là văn bản đã NẰM SẴN ở đó từ trước (vd do người khác gắn).
    doc = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="HTM")
    _link(db, doc, folder_a, primary=True)
    _link(db, doc, folder_b, primary=False)
    db.commit()
    assert _linked_folder_ids(db, doc.id) == {folder_a.id, folder_b.id}

    a1 = world.actor("a1")
    with pytest.raises(HTTPException) as exc:
        service.update_document(db, doc, DocumentUpdate(folder_ids=[folder_b.id]),
                                a1.user.id, user=a1.user)
    assert exc.value.status_code == 403

    #  Không đổi gì — chặn TRƯỚC khi ghi.
    assert _linked_folder_ids(db, doc.id) == {folder_a.id, folder_b.id}


def test_thu_muc_chinh_dang_an_giu_nguyen_lam_chinh(db, world, roots, doc_type):
    """Thư mục CHÍNH đang ẨN với a1 (B) — gửi lại chỉ A (thấy, không khai
    `primary_id`) thì B vẫn giữ vai trò CHÍNH, không bị A soán mất chỉ vì A là
    thư mục duy nhất a1 gửi lên (C1, luật "chính giữ nguyên khi ẩn")."""
    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    folder_a = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="A phụ"), 0)
    _grant_folder(db, folder_a, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                  level=CONTRIBUTE)
    folder_b = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="B chính ẩn"), 0)
    folder_service.update_folder(db, folder_b, FolderUpdate(default_access=PRIVATE), 0)

    doc = _create(db, world, doc_type, folder_ids=[folder_a.id], title="Chính ẩn")
    #  Đặt B làm CHÍNH tay (giả lập trạng thái trước khi a1 mất quyền ở B).
    db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).update(
        {DocumentFolderLink.is_primary: False})
    _link(db, doc, folder_b, primary=True)
    db.commit()

    a1 = world.actor("a1")
    service.update_document(db, doc, DocumentUpdate(folder_ids=[folder_a.id]),
                            a1.user.id, user=a1.user)

    rows = {row.folder_id: row.is_primary for row in
           db.query(DocumentFolderLink).filter(DocumentFolderLink.document_id == doc.id).all()}
    assert rows == {folder_a.id: False, folder_b.id: True}


# ── Gap #2 — dashboard/scope không truyền `user` xuống serializer ───────────
def test_tong_quan_khong_lo_ten_thu_muc_rieng_tu(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    private_folder = folder_service.create_folder(
        db, FolderCreate(parent_id=root.id, name="Bí mật tổng quan"), 0)
    folder_service.update_folder(db, private_folder, FolderUpdate(default_access=PRIVATE), 0)
    #  a1 KHÔNG có ACL nào ở đây — thư mục vô hình với a1.

    doc = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="TQ1")
    db.commit()
    _link(db, doc, private_folder)
    db.commit()

    a1 = world.actor("a1")
    data = dashboard_service.overview(db, a1.user, a1.profile())
    recent = {row["id"]: row for row in data["recent"]}
    assert doc.id in recent
    #  Trước vá: `folders` trả nguyên tên "Bí mật tổng quan" dù a1 không thấy
    #  thư mục đó ở màn Quản lý cây thư mục.
    assert recent[doc.id]["folders"] == []


def test_ap_dung_cho_toi_khong_lo_ten_thu_muc_rieng_tu(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    private_folder = folder_service.create_folder(
        db, FolderCreate(parent_id=root.id, name="Bí mật phạm vi"), 0)
    folder_service.update_folder(db, private_folder, FolderUpdate(default_access=PRIVATE), 0)

    doc = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="AD1")
    doc.status = STATUS_EFFECTIVE   # F05 quy tắc 4: còn sống + không khai phạm vi → áp cho cả công ty
    db.commit()
    _link(db, doc, private_folder)
    db.commit()

    a1 = world.actor("a1")
    response = scope_controller.applies_to_me(db, a1.user)
    body = json.loads(response.body)
    items = {row["id"]: row for row in body["data"]["items"]}
    assert doc.id in items
    assert items[doc.id]["folders"] == []


def test_serialize_many_khong_truyen_user_thi_dong_khong_mo(db, world, roots):
    """Mặc định của `serializer.serialize_many` khi THIẾU `user` phải là ĐÓNG
    (rỗng), không phải MỞ hết như bản đầu phase 04 — phòng khi có nơi gọi khác
    (hiện tại hoặc về sau) quên truyền `user` xuống."""
    from app.modules.document import serializer

    root = roots[world.co["A"]]
    doc = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="SR1")
    db.commit()
    _link(db, doc, root)
    db.commit()

    rows = serializer.serialize_many(db, [doc])   # KHÔNG truyền `user`
    assert rows[0]["folders"] == []


# ── Gap #2 (mở rộng, theo yêu cầu lead 23/09/2026) — `primary_folder_path` ──
def test_duong_dan_thu_muc_chinh_khong_thay_thi_rong(db, world, roots):
    """Thư mục CHÍNH không thấy được, không còn thư mục nào khác → rỗng, KHÔNG
    lộ tên thư mục riêng tư qua `primary_folder_path`."""
    from app.modules.doc_catalog import folder_link_bulk_service

    root = roots[world.co["A"]]
    private_folder = folder_service.create_folder(
        db, FolderCreate(parent_id=root.id, name="Bí mật đường dẫn"), 0)
    folder_service.update_folder(db, private_folder, FolderUpdate(default_access=PRIVATE), 0)
    #  a1 không có ACL nào ở đây, cũng không có `document.read` nào cả.

    doc = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="PP1")
    db.commit()
    _link(db, doc, private_folder, primary=True)
    db.commit()

    a1 = world.actor("a1")
    paths = folder_link_bulk_service.primary_folder_path_for_documents(db, [doc.id], user=a1.user)
    assert paths.get(doc.id, "") == ""


def test_duong_dan_thu_muc_chinh_khong_thay_roi_ve_thu_muc_phu_con_thay(db, world, roots):
    """Thư mục CHÍNH không thấy được nhưng văn bản còn nằm ở thư mục KHÁC mà
    người này thấy → rơi về đường dẫn của thư mục đó, không rỗng, không lộ tên
    thư mục chính riêng tư."""
    from app.modules.doc_catalog import folder_link_bulk_service

    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]   # mặc định CONTRIBUTE → a1 thấy được
    private_folder = folder_service.create_folder(
        db, FolderCreate(parent_id=root.id, name="Chính nhưng riêng tư"), 0)
    folder_service.update_folder(db, private_folder, FolderUpdate(default_access=PRIVATE), 0)

    doc = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="PP2")
    db.commit()
    _link(db, doc, private_folder, primary=True)   # CHÍNH nhưng a1 không thấy
    _link(db, doc, root, primary=False)             # PHỤ, a1 thấy được
    db.commit()

    a1 = world.actor("a1")
    paths = folder_link_bulk_service.primary_folder_path_for_documents(db, [doc.id], user=a1.user)
    path = paths.get(doc.id, "")
    assert path != ""
    assert "Chính nhưng riêng tư" not in path


def test_duong_dan_hien_ten_to_tien_du_to_tien_khong_tu_thay_rieng(db, world, roots):
    """Rule 5 (phase 04): thấy F thì thấy TÊN tổ tiên của F, dù bản thân tổ
    tiên đó KHÔNG tự thấy được riêng (nhánh khóa `PRIVATE`, F mở lại bằng ACL
    đích danh xuyên rào — không lọc lại từng mắt xích bên trong breadcrumb của
    MỘT thư mục đã qua cửa thấy được)."""
    from app.modules.doc_catalog import folder_link_bulk_service

    root = roots[world.co["A"]]   # a1 KHÔNG có `document.read` nào → root cũng không tự thấy
    mid = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Tổ Riêng"), 0)
    folder_service.update_folder(db, mid, FolderUpdate(default_access=PRIVATE), 0)
    leaf = folder_service.create_folder(db, FolderCreate(parent_id=mid.id, name="Lá Chia Riêng"), 0)
    _grant_folder(db, leaf, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                 level=CONTRIBUTE)   # chia ĐÍCH DANH đúng `leaf`, không đụng `mid`/`root`

    doc = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="PP3")
    db.commit()
    _link(db, doc, leaf, primary=True)
    db.commit()

    a1 = world.actor("a1")
    #  `mid`/`root` KHÔNG nằm trong `effective_levels` của a1 — xác nhận đúng
    #  tiền đề của ca này (tổ tiên tự nó không thấy được).
    from app.modules.doc_catalog import folder_access_service

    levels = folder_access_service.effective_levels(db, a1.user, a1.profile())
    assert mid.id not in levels and root.id not in levels and leaf.id in levels

    paths = folder_link_bulk_service.primary_folder_path_for_documents(db, [doc.id], user=a1.user)
    path = paths.get(doc.id, "")
    assert "Tổ Riêng" in path
    assert "Lá Chia Riêng" in path
    assert path.count(" / ") == 3   # Công ty / gốc / Tổ Riêng / Lá Chia Riêng (nhóm «Công ty», 24/09/2026)


def test_duong_dan_khong_truyen_user_thi_rong_het(db, world, roots):
    from app.modules.doc_catalog import folder_link_bulk_service

    root = roots[world.co["A"]]
    doc = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="PP4")
    db.commit()
    _link(db, doc, root)
    db.commit()

    paths = folder_link_bulk_service.primary_folder_path_for_documents(db, [doc.id])
    assert paths == {}


def test_serialize_many_primary_folder_path_theo_nguoi_xem(db, world, roots):
    """Kiểm nối dây đầu-cuối qua `serializer.serialize_many` — trường
    `primary_folder_path` trả về cho màn hình cũng phải theo đúng luật trên,
    không riêng hàm `folder_link_bulk_service` mới đúng."""
    from app.modules.document import serializer

    root = roots[world.co["A"]]
    private_folder = folder_service.create_folder(
        db, FolderCreate(parent_id=root.id, name="Riêng tư đầu cuối"), 0)
    folder_service.update_folder(db, private_folder, FolderUpdate(default_access=PRIVATE), 0)

    doc = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="PP5")
    db.commit()
    _link(db, doc, private_folder, primary=True)
    db.commit()

    a1 = world.actor("a1")
    rows = serializer.serialize_many(db, [doc], user=a1.user)
    assert rows[0]["primary_folder_path"] == ""

    rows_no_user = serializer.serialize_many(db, [doc])
    assert rows_no_user[0]["primary_folder_path"] == ""
