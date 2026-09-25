"""PHÂN QUYỀN THƯ MỤC (phase 04, duoc-CR-475) — `folder_access_service` +
`folder_access_grant_service` + điểm nối vào `folder_tree_service`/
`folder_link_query`.

Dựng trên thế giới mẫu `world` (hai pháp nhân A/B, `scope_factory.build_world`)
— cùng nền với `test_van_ban_thu_muc.py` (phase 03).
"""
import pytest
from fastapi import HTTPException

from app.core.subject_match import (EFFECT_ALLOW, EFFECT_DENY, SUBJECT_COMPANY,
                                    SUBJECT_DEPARTMENT, SUBJECT_EMPLOYEE)
from app.modules.doc_catalog import (folder_access_grant_service, folder_access_service,
                                     folder_link_query, folder_root_service, folder_service,
                                     folder_tree_service)
from app.modules.doc_catalog.folder_access_model import DocFolderAccess
from app.modules.doc_catalog.folder_access_schema import FolderAccessGrantIn
from app.modules.doc_catalog.folder_constants import FolderAccessLevel
from app.modules.doc_catalog.folder_link_model import DocumentFolderLink
from app.modules.doc_catalog.folder_schema import FolderCreate, FolderUpdate
from app.modules.document.access_model import DocumentAccess
from app.modules.document.model import ORIGIN_INTERNAL, Document
from app.modules.doc_catalog.model import DocType
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó

VIEW = int(FolderAccessLevel.VIEW)
CONTRIBUTE = int(FolderAccessLevel.CONTRIBUTE)
MANAGE = int(FolderAccessLevel.MANAGE)
PRIVATE = int(FolderAccessLevel.PRIVATE)


@pytest.fixture()
def roots(db, world):
    created = folder_root_service.ensure_company_roots(db)
    return {f.company_id: f for f in created}


def _doc(db, *, company_id, department_id=0, created_by=0, doc_type_id=0, code="X"):
    row = Document(origin=ORIGIN_INTERNAL, doc_type_id=doc_type_id, company_id=company_id,
                   department_id=department_id, owner_employee_id=0, title=f"Văn bản {code}",
                   legacy_code=code, created_by=created_by, updated_by=created_by)
    db.add(row)
    db.flush()
    return row


def _link(db, doc, folder, primary=True):
    db.add(DocumentFolderLink(document_id=doc.id, folder_id=folder.id, is_primary=primary))
    db.flush()


def _grant_folder(db, folder, *, subject_kind, subject_id, effect=EFFECT_ALLOW,
                  level=int(FolderAccessLevel.VIEW), actor=0, **kw):
    data = FolderAccessGrantIn(subject_kind=subject_kind, subject_id=subject_id,
                               effect=effect, level=level, **kw)
    return folder_access_grant_service.grant(db, folder, data, actor)


def _levels(db, actor_key, world):
    a = world.actor(actor_key)
    return folder_access_service.effective_levels(db, a.user, a.profile())


# ── Thư mục nhóm «Công ty» (24/09/2026) ────────────────────────────────────
def test_nhom_cong_ty_hien_khi_thay_it_nhat_mot_phap_nhan(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read",))
    group = folder_root_service.get_or_create_company_group(db)
    assert _levels(db, "a1", world).get(group.id) == VIEW


def test_nhom_cong_ty_an_khi_khong_thay_phap_nhan_nao(db, world, roots):
    """Không bày ra một thư mục «Công ty» rỗng cho người không thấy gì bên trong."""
    group = folder_root_service.get_or_create_company_group(db)
    assert group.id not in _levels(db, "a1", world)


def test_nhom_cong_ty_quan_tri_toan_he_la_quan_ly(db, world, roots):
    world.grant("a1", "doc_folder", scope="all", actions=("read", "write"))
    group = folder_root_service.get_or_create_company_group(db)
    assert _levels(db, "a1", world).get(group.id) == MANAGE


# ── Luật thấy CÂY theo pháp nhân (chốt 3) ───────────────────────────────────
def test_scope_company_khong_thay_nhanh_phap_nhan_khac(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read",))
    levels = _levels(db, "a1", world)
    assert roots[world.co["A"]].id in levels
    assert roots[world.co["B"]].id not in levels


def test_scope_all_thay_moi_phap_nhan(db, world, roots):
    world.grant("a1", "document", scope="all", actions=("read",))
    levels = _levels(db, "a1", world)
    assert roots[world.co["A"]].id in levels
    assert roots[world.co["B"]].id in levels


def test_scope_dept_van_thay_goc_phap_nhan_minh(db, world, roots):
    """Bậc HẸP hơn `company` (own/dept/dept_proc/proc) vẫn không vượt ra khỏi
    pháp nhân của chính người đó — nhưng vẫn với tới đúng pháp nhân mình."""
    world.grant("a1", "document", scope="dept", actions=("read",))
    levels = _levels(db, "a1", world)
    assert roots[world.co["A"]].id in levels
    assert roots[world.co["B"]].id not in levels


def test_include_cong_ty_khac_mo_them_nhanh(db, world, roots):
    """Ô "Chỉ trong công ty" của CHÍNH grant CỘNG THÊM một pháp nhân, không
    thay thế pháp nhân chính của người đó."""
    world.grant("a1", "document", scope="company", actions=("read",),
               inc_company=["B"])
    levels = _levels(db, "a1", world)
    assert roots[world.co["A"]].id in levels
    assert roots[world.co["B"]].id in levels


def test_khong_grant_document_read_thi_khong_thay_gi(db, world, roots):
    levels = _levels(db, "a1", world)
    assert levels == {}


# ── Kế thừa mức nền + ACL cho/cấm ────────────────────────────────────────────
def test_ke_thua_muc_nen_tu_to_tien_gan_nhat(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read",))
    root = roots[world.co["A"]]
    mid = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Giữa"), 0)
    folder_service.update_folder(db, mid, FolderUpdate(default_access=VIEW), 0)
    leaf = folder_service.create_folder(db, FolderCreate(parent_id=mid.id, name="Lá"), 0)

    levels = _levels(db, "a1", world)
    assert levels[mid.id] == VIEW
    #  `leaf` KHÔNG tự khai `default_access` → kế thừa đúng mức của `mid`, KHÔNG
    #  phải mức CONTRIBUTE của gốc pháp nhân (tổ tiên GẦN NHẤT thắng).
    assert levels[leaf.id] == VIEW


def test_default_access_private_khoa_nhanh_con(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read",))
    root = roots[world.co["A"]]
    locked = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Khóa"), 0)
    folder_service.update_folder(db, locked, FolderUpdate(default_access=PRIVATE), 0)
    child = folder_service.create_folder(db, FolderCreate(parent_id=locked.id, name="Con"), 0)

    levels = _levels(db, "a1", world)
    assert locked.id not in levels
    assert child.id not in levels


def test_acl_cho_dich_danh_mo_duoc_nhanh_du_khong_voi_toi_phap_nhan(db, world, roots):
    """Không grant `document.read` nào → không với tới pháp nhân A. Một dòng
    ACL CHO đích danh vẫn mở được ĐÚNG thư mục đó (chia sẻ xuyên rào)."""
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Chia riêng"), 0)
    _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                 level=CONTRIBUTE)
    #  `doc_folder` không mở pháp nhân nào (chỉ `document.read` mới «với tới»),
    #  nhưng là quyền GHI — không có nó thì trần vai trò hạ dòng ACL về Xem.
    world.grant("a1", "doc_folder", scope="own", actions=("read", "create"))

    levels = _levels(db, "a1", world)
    assert folder.id not in levels.keys() - {folder.id}   # gốc KHÔNG thấy
    assert root.id not in levels
    assert levels[folder.id] == CONTRIBUTE


def test_cam_o_cha_chan_ca_con(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read",))
    root = roots[world.co["A"]]
    parent = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Cha"), 0)
    child = folder_service.create_folder(db, FolderCreate(parent_id=parent.id, name="Con"), 0)
    #  Trước khi cấm: cả hai đều thấy (kế thừa mức CONTRIBUTE của gốc).
    assert child.id in _levels(db, "a1", world)

    _grant_folder(db, parent, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                 effect=EFFECT_DENY)
    levels = _levels(db, "a1", world)
    assert parent.id not in levels
    assert child.id not in levels   # CẤM kế thừa xuống, chặn cả cháu


def test_acl_theo_phong_ban_va_phap_nhan_cung_khop(db, world, roots):
    root = roots[world.co["A"]]
    folder_dept = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Theo phòng"), 0)
    _grant_folder(db, folder_dept, subject_kind=SUBJECT_DEPARTMENT, subject_id=world.dept["A.kt"],
                 level=VIEW)
    folder_co = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Theo pháp nhân"), 0)
    _grant_folder(db, folder_co, subject_kind=SUBJECT_COMPANY, subject_id=world.co["A"], level=VIEW)

    levels = _levels(db, "a1", world)   # a1 ở phòng A.kt, pháp nhân A — không grant document nào
    assert levels[folder_dept.id] == VIEW
    assert levels[folder_co.id] == VIEW


def test_het_han_valid_to_khong_con_hieu_luc(db, world, roots):
    import datetime

    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Hết hạn"), 0)
    _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                 level=CONTRIBUTE, valid_to=datetime.date(2020, 1, 1))

    levels = _levels(db, "a1", world)
    assert folder.id not in levels


def test_thu_hoi_khong_con_hieu_luc(db, world, roots):
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Thu hồi"), 0)
    row = _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                       level=CONTRIBUTE)
    assert folder.id in _levels(db, "a1", world)

    folder_access_grant_service.revoke(db, folder, row.id, "thu hồi để kiểm", 0)
    levels = _levels(db, "a1", world)
    assert folder.id not in levels


def test_quan_tri_khong_bi_cam_chan(db, world, roots):
    world.grant("a1", "doc_folder", scope="all", actions=("read", "write"))
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Bị cấm nhưng vẫn quản lý"), 0)
    _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                 effect=EFFECT_DENY)

    levels = _levels(db, "a1", world)
    assert levels[folder.id] == MANAGE
    assert levels[root.id] == MANAGE
    assert levels[roots[world.co["B"]].id] == MANAGE   # `doc_folder.write` scope=all → mọi pháp nhân


# ── C2 (rà soát 23/09/2026) — quản trị thư mục scope "company" KHÔNG vượt ────
def test_quan_tri_scope_company_khong_vuot_phap_nhan_khac(db, world, roots):
    """Đối chứng của `test_quan_tri_khong_bi_cam_chan` ở trên: `doc_folder.write`
    scope `company` (đúng scope seed `vanban_sua` dùng sau C2, KHÔNG phải
    `all`) chỉ quản trị được pháp nhân CỦA CHÍNH MÌNH — cấm ở pháp nhân KHÁC
    vẫn CHẶN bình thường (không có cửa quản trị nào mở ra ngoài phạm vi)."""
    world.grant("a1", "doc_folder", scope="company", actions=("read", "write"))
    folder_a = folder_service.create_folder(
        db, FolderCreate(parent_id=roots[world.co["A"]].id, name="Cty của mình"), 0)
    folder_b = folder_service.create_folder(
        db, FolderCreate(parent_id=roots[world.co["B"]].id, name="Cty khác, bị cấm"), 0)
    _grant_folder(db, folder_b, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                 effect=EFFECT_DENY)

    levels = _levels(db, "a1", world)
    assert levels[folder_a.id] == MANAGE          # pháp nhân của mình — vẫn quản trị được
    #  Pháp nhân KHÁC + bị cấm đích danh: KHÔNG còn cửa quản trị nào cứu — mất
    #  hẳn khỏi kết quả (không thấy), đúng luật "CẤM thắng" khi không phải admin.
    assert folder_b.id not in levels


def test_seed_doc_folder_write_khong_con_scope_all(db):
    """Chốt DỮ LIỆU SEED — vá thẳng ở `seed.py`, không chỉ ở cơ chế
    `effective_levels`: `vanban_sua` (vai trò soạn/sửa văn bản, KHÔNG phải
    quản trị) đổi scope `doc_folder` từ `all` sang `company` (C2). Hồi quy
    kiểu "ai đó trả lại `all`" phải đỏ ngay ở đây, không cần dựng cả `world`."""
    from app import seed

    perms = seed.STD_ROLES["vanban_sua"]["perms"]["doc_folder"]
    actions, scope = perms
    assert scope == "company", (
        f"doc_folder scope của vanban_sua phải là 'company', đang là {scope!r} — "
        "scope 'all' cấp QUẢN LÝ (bỏ qua cả ACL cấm) trên thư mục của MỌI pháp nhân")
    assert set(actions) >= {"write"}

    assert "doc_folder" in seed._SYS_ENTITIES, (
        "doc_folder phải nằm trong _SYS_ENTITIES — thiếu thì _PUR_MANAGER_PERMS "
        "(quét mọi ENTITIES không nằm trong tập này) tự cấp doc_folder.write scope=all "
        "cho Quản lý thu mua, vượt hẳn phạm vi đọc văn bản 'company' của chính vai trò đó")

    #  `_PUR_MANAGER_PERMS` loại `doc_folder` khỏi vòng quét `_ALL_ACTIONS`/`all`,
    #  nhưng vòng `setdefault` CHUNG cho MỌI vai trò (kể cả `pur_manager`, chạy
    #  SAU vì nó ĐỌC vào cùng dict `_PUR_MANAGER_PERMS`) vẫn cấp `read` — đúng ý
    #  "mọi vai trò đọc được cây thư mục", chỉ riêng `write` là không có.
    pur_manager_doc_folder = seed.STD_ROLES["pur_manager"]["perms"]["doc_folder"]
    assert pur_manager_doc_folder == (["read"], "all"), (
        f"pur_manager phải chỉ có 'read' trên doc_folder (từ setdefault chung), "
        f"đang là {pur_manager_doc_folder!r} — có 'write' nghĩa là lọt lại đúng lỗ C2")


def test_ensure_level_khong_thay_ra_404(db, world, roots):
    a1 = world.actor("a1")
    with pytest.raises(HTTPException) as exc:
        folder_access_service.ensure_level(db, a1.user, roots[world.co["A"]], VIEW, a1.profile())
    assert exc.value.status_code == 404


def test_ensure_level_thay_nhung_thieu_muc_ra_403(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read",))
    a1 = world.actor("a1")
    root = roots[world.co["A"]]   # mức nền CONTRIBUTE, không đủ MANAGE
    with pytest.raises(HTTPException) as exc:
        folder_access_service.ensure_level(db, a1.user, root, MANAGE, a1.profile())
    assert exc.value.status_code == 403


# ── «Thấy một phần» — 5 văn bản, người dùng chỉ thấy 2 ──────────────────────
def test_5_van_ban_nguoi_dung_chi_thay_2(db, world, roots):
    """1 mật (loại `is_personal`, không dính người xem) · 1 bị cấm đích danh ·
    1 của phòng khác · 2 thấy được — số đếm cây + lọc `folder_id` phải khớp
    ĐÚNG 2, không rò tên/số của ba văn bản còn lại."""
    world.grant("a1", "document", scope="dept", actions=("read",))
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Năm văn bản"), 0)

    secret_type = DocType(code="MAT01", name="Loại mật", is_personal=True)
    db.add(secret_type)
    db.flush()

    doc1 = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="1")
    doc2 = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="2")
    doc3_other_dept = _doc(db, company_id=world.co["A"], department_id=world.dept["A.mua"], code="3")
    doc4_secret = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"],
                       doc_type_id=secret_type.id, code="4")
    doc5_denied = _doc(db, company_id=world.co["A"], department_id=world.dept["A.kt"], code="5")
    db.add(DocumentAccess(document_id=doc5_denied.id, subject_kind=SUBJECT_EMPLOYEE,
                          subject_id=world.emp["a1"], effect=EFFECT_DENY, can_read=True))
    db.commit()

    for d in (doc1, doc2, doc3_other_dept, doc4_secret, doc5_denied):
        _link(db, d, folder)
    db.commit()

    a1 = world.actor("a1")
    nodes = {n["id"]: n for n in folder_tree_service.tree(db, a1.user)}
    assert nodes[folder.id]["document_count"] == 2
    assert nodes[folder.id]["document_count_branch"] == 2

    #  Bộ lọc `folder_id=` của `/api/documents` KẾT HỢP hai lớp — điều kiện
    #  thư mục (`folder_documents_condition`, thư mục nào chứa văn bản) VÀ
    #  điều kiện quyền ĐỌC văn bản (`access_service.visible_condition`), đúng
    #  như `document/controller._list_query` ghép chúng. Lớp thư mục một mình
    #  không đủ — nó chỉ trả lời "văn bản có nằm trong thư mục này", không
    #  trả lời "người này đọc được văn bản đó".
    from app.modules.document import access_service

    folder_cond = folder_link_query.folder_documents_condition(
        db, folder.id, False, a1.user, a1.profile())
    doc_cond = access_service.visible_condition(a1.user, a1.profile())
    q = db.query(Document).filter(folder_cond)
    if doc_cond is not None:
        q = q.filter(doc_cond)
    visible_ids = {row.id for row in q.all()}
    assert visible_ids == {doc1.id, doc2.id}


def test_thu_muc_khong_thay_qua_bo_loc_folder_id_thi_ket_qua_rong(db, world, roots):
    """Không với tới pháp nhân B → lọc `folder_id=<gốc B>` phải ra RỖNG, không
    phải "bỏ qua bộ lọc" (điều đó sẽ lộ toàn bộ văn bản của B)."""
    world.grant("a2", "document", scope="company", actions=("read",))   # chỉ pháp nhân A
    root_b = roots[world.co["B"]]
    doc_b = _doc(db, company_id=world.co["B"], code="B1")
    _link(db, doc_b, root_b)
    db.commit()

    a2 = world.actor("a2")
    cond = folder_link_query.folder_documents_condition(db, root_b.id, False, a2.user, a2.profile())
    visible_ids = {row.id for row in db.query(Document).filter(cond).all()}
    assert visible_ids == set()


# ── Cửa ĐÓNG GÓP khi gắn văn bản vào thư mục ────────────────────────────────
def test_gan_van_ban_can_muc_dong_gop_tren_thu_muc_dich(db, world, roots):
    from app.modules.doc_catalog import folder_link_bulk_service

    world.grant("a1", "document", scope="company", actions=("read", "write"))
    root = roots[world.co["A"]]
    #  Thư mục chỉ cấp mức XEM cho a1 — không đủ ĐÓNG GÓP để gắn văn bản vào.
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Chỉ xem"), 0)
    folder_service.update_folder(db, folder, FolderUpdate(default_access=PRIVATE), 0)
    _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"], level=VIEW)

    doc = _doc(db, company_id=world.co["A"], created_by=world.user_id("a1"))
    db.commit()
    a1 = world.actor("a1")

    with pytest.raises(HTTPException) as exc:
        folder_link_bulk_service.move_documents(
            db, [doc.id], folder.id, "add", a1.user, a1.profile(), a1.user.id)
    assert exc.value.status_code == 403


def test_gan_van_ban_du_muc_dong_gop_thi_thanh_cong(db, world, roots):
    from app.modules.doc_catalog import folder_link_bulk_service

    world.grant("a1", "document", scope="company", actions=("read", "write"))
    root = roots[world.co["A"]]   # gốc pháp nhân mặc định CONTRIBUTE
    doc = _doc(db, company_id=world.co["A"], created_by=world.user_id("a1"))
    db.commit()
    a1 = world.actor("a1")

    result = folder_link_bulk_service.move_documents(
        db, [doc.id], root.id, "add", a1.user, a1.profile(), a1.user.id)
    assert result["moved"] == [doc.id]
    assert result["denied"] == []


# ── Cấp / thu quyền qua service ──────────────────────────────────────────────
def test_grant_sua_dong_cu_khong_them_dong_moi(db, world, roots):
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Cấp lại"), 0)
    row1 = _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"], level=VIEW)
    row2 = _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                        level=CONTRIBUTE)
    assert row1.id == row2.id
    assert row2.level == CONTRIBUTE
    assert folder_access_grant_service.list_direct(db, folder.id) == [row2]


def test_grant_effect_cam_ep_level_private(db, world, roots):
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Cấm"), 0)
    row = _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"],
                       effect=EFFECT_DENY, level=MANAGE)
    assert row.level == PRIVATE   # level của dòng CẤM vô nghĩa, luôn ép về PRIVATE


def test_revoke_da_thu_hoi_roi_thi_bao_loi(db, world, roots):
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Thu hồi 2 lần"), 0)
    row = _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"], level=VIEW)
    folder_access_grant_service.revoke(db, folder, row.id, "lần 1", 0)
    with pytest.raises(HTTPException) as exc:
        folder_access_grant_service.revoke(db, folder, row.id, "lần 2", 0)
    assert exc.value.status_code == 400


def test_grant_subject_kind_khong_hop_le_bi_chan_o_schema(db):
    with pytest.raises(ValueError):
        FolderAccessGrantIn(subject_kind=99, subject_id=1)


def test_grant_level_khong_hop_le_bi_chan_o_schema(db):
    with pytest.raises(ValueError):
        FolderAccessGrantIn(subject_kind=SUBJECT_EMPLOYEE, subject_id=1, level=9)


# ── `default_access` chỉ Quản lý đổi được (dải giá trị) ─────────────────────
def test_default_access_gia_tri_khong_hop_le_bi_chan(db, world, roots):
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Sai mức"), 0)
    with pytest.raises(HTTPException) as exc:
        folder_service.update_folder(db, folder, FolderUpdate(default_access=9), 0)
    assert exc.value.status_code == 400


# ── `my_level`/`effective_access` (annotate_detail) ─────────────────────────
def test_effective_access_chi_tra_cho_nguoi_muc_quan_ly(db, world, roots):
    from app.modules.doc_catalog import folder_access_view_service

    world.grant("a1", "document", scope="company", actions=("read", "create"))   # → CONTRIBUTE ở gốc
    root = roots[world.co["A"]]
    a1 = world.actor("a1")

    node = {}
    folder_access_view_service.annotate_detail(db, a1.user, root, node)
    assert node["my_level"] == CONTRIBUTE
    assert node["effective_access"] == []   # chưa đủ Quản lý → rỗng, không lộ ACL

    world.grant("a1", "doc_folder", scope="all", actions=("read", "write"))
    a1 = world.actor("a1")
    node2 = {}
    folder_access_view_service.annotate_detail(db, a1.user, root, node2)
    assert node2["my_level"] == MANAGE
    assert node2["effective_access"] == []   # không có dòng ACL nào khai trên nhánh này → vẫn rỗng, nhưng không lỗi


# ── `my_level` trên `/tree` và `/search` (phase 06, duoc-CR-476 — ô chọn thư
#    mục lúc tạo văn bản chỉ liệt kê mức ≥ Đóng góp, lọc ngay ở backend) ─────
def test_tree_tra_my_level_dung_bang_effective_levels(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read", "create"))   # → CONTRIBUTE ở gốc
    root = roots[world.co["A"]]
    folder = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Chỉ xem"), 0)
    folder_service.update_folder(db, folder, FolderUpdate(default_access=PRIVATE), 0)
    _grant_folder(db, folder, subject_kind=SUBJECT_EMPLOYEE, subject_id=world.emp["a1"], level=VIEW)
    db.commit()

    a1 = world.actor("a1")
    expected = folder_access_service.effective_levels(db, a1.user, a1.profile())
    nodes = {n["id"]: n for n in folder_tree_service.tree(db, a1.user)}
    assert nodes[root.id]["my_level"] == expected[root.id] == CONTRIBUTE
    assert nodes[folder.id]["my_level"] == expected[folder.id] == VIEW


def test_search_folders_tra_my_level(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read", "create"))   # → CONTRIBUTE ở gốc
    root = roots[world.co["A"]]
    folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Hợp đồng thuê"), 0)
    a1 = world.actor("a1")

    results = folder_tree_service.search_folders(db, a1.user, "hop dong")
    assert results
    assert all(r["my_level"] >= VIEW for r in results)
    #  Không có ACL riêng nào ghi đè — thư mục con thừa hưởng đúng mức nền
    #  CONTRIBUTE của gốc pháp nhân.
    assert results[0]["my_level"] == CONTRIBUTE


# ── Trần theo vai trò (lỗi test UI 24/09/2026) ──────────────────────────────
def test_chi_quyen_doc_thi_toi_da_xem_du_thu_muc_mac_dinh_dong_gop(db, world, roots):
    """Gốc pháp nhân mặc định «Đóng góp» cho cả pháp nhân. Người CHỈ ĐỌC từng
    nhận `my_level = 2` → giao diện vẽ «Quyền: Đóng góp» + nút «+ Mới» rồi bấm
    vào ăn 403. Phải hạ về Xem — nhưng vẫn THẤY thư mục."""
    world.grant("a1", "document", scope="company", actions=("read",))
    world.grant("a1", "doc_folder", scope="company", actions=("read",))
    root = roots[world.co["A"]]
    assert _levels(db, "a1", world)[root.id] == VIEW


def test_co_quyen_ghi_van_ban_thi_giu_muc_dong_gop(db, world, roots):
    world.grant("a1", "document", scope="company", actions=("read", "create"))
    root = roots[world.co["A"]]
    assert _levels(db, "a1", world)[root.id] == CONTRIBUTE


def test_tran_vai_tro_khong_nang_muc_rieng_tu_len_xem(db, world, roots):
    """Trần chỉ HẠ, không bao giờ mở thêm: thư mục khóa riêng tư vẫn vô hình
    với người có đủ quyền ghi."""
    from app.modules.doc_catalog.folder_constants import FolderAccessLevel

    world.grant("a1", "document", scope="company", actions=("read", "create", "write"))
    root = roots[world.co["A"]]
    locked = folder_service.create_folder(db, FolderCreate(parent_id=root.id, name="Khóa"), 0)
    locked.default_access = int(FolderAccessLevel.PRIVATE)
    db.commit()
    assert locked.id not in _levels(db, "a1", world)
