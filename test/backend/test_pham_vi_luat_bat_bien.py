"""Cụm 00 — bốn luật BẤT BIẾN của trục phạm vi dữ liệu.

Khác mọi tệp còn lại của đợt này: đây không phải test nghiệp vụ. Nó không hỏi
"người X thấy phiếu Y không", nó hỏi "có ai vừa thêm một thứ mới mà quên khai
phạm vi cho nó không". Cùng loại với `test_pham_vi_khai_du_b07.py::test_du_53_entity`.

Lý do cần loại test này: mọi lỗ phạm vi tìm được cho tới nay đều KHÔNG phải do
ai viết sai điều kiện, mà do **thêm thứ mới rồi quên khai** — thêm entity quên
khai `SCOPE_FIELDS` (N-14), thêm module vào bộ máy duyệt quên khai reader, thêm
controller quên gọi `apply_scope`. Test nghiệp vụ không bắt được nhóm này: nó chỉ
kiểm những thứ đã có tên trong đầu người viết.

Bốn luật:
  BB-1  entity vào bộ máy duyệt phải có hàm kiểm quyền đọc  (`can_read` fail-open)
  BB-2  cột khai trong `SCOPE_FIELDS` phải CÓ THẬT trên model
  BB-3  entity khai `PUBLIC` phải có tên trong danh sách miễn trừ, kèm lý do
  BB-4  controller không lọc phạm vi phải có tên trong danh sách miễn trừ, kèm lý do
"""
from pathlib import Path

import pytest

from app.core.permissions import ENTITIES
from app.core.scoping import PUBLIC, SCOPE_FIELDS
from scope_factory import ENTITY_MODEL_PATHS, build_world, model_of

# ── BB-1 ────────────────────────────────────────────────────────────────────────


def test_bb1_moi_entity_vao_bo_may_duyet_deu_phai_khai_ham_kiem_quyen_doc():
    """`can_read` trả **True** khi entity không có hàm kiểm (`entity_hooks.py:123`).

    Fail-open, và fail-open ở đúng chỗ lộ nhiều nhất: phiên duyệt mang theo tên
    phiếu, tên luồng, tên người đang duyệt. Hôm nay bốn bridge đều khai đủ nên
    chưa thủng — module thứ năm quên khai thì lộ cho mọi người đăng nhập mà
    không có một dòng test nào đỏ.

    ⚠️ Không sửa bằng cách đổi mặc định thành `False`: làm thế thì module quên
    khai bị KHÓA im lặng, người dùng thật ăn 404 không giải thích được, và vẫn
    không ai biết vì sao. Thà đỏ ở đây.
    """
    import app.main  # noqa: F401 — nạp mọi module để các bridge tự đăng ký
    from app.modules.approval.entity_hooks import _HOOKS, _READERS

    assert _HOOKS, "chưa module nào đăng ký hook — kiểm lại việc nạp app.main"
    missing = sorted(set(_HOOKS) - set(_READERS))
    assert missing == [], (
        f"{len(missing)} loại chứng từ vào bộ máy duyệt mà không khai hàm kiểm quyền "
        f"đọc: {missing}. Gọi `entity_hooks.register_reader(<entity>, fn)` trong bridge "
        "của module đó — thiếu nó thì `can_read` cho qua tất."
    )


# ── BB-2 ────────────────────────────────────────────────────────────────────────

#  Cột khai nhưng KHÔNG có trên model — có lý do chính đáng, ghi ra đây.
#  Rỗng là đúng: hôm nay không có ngoại lệ nào. Thêm dòng vào đây phải kèm lý do
#  thật, đừng dùng nó làm chỗ đổ những khai báo gõ sai.
BB2_EXEMPT: dict[str, set[str]] = {}


@pytest.mark.parametrize("entity", sorted(ENTITY_MODEL_PATHS))
def test_bb2_cot_khai_trong_scope_fields_phai_co_that(entity):
    """Khai sai tên cột thì `getattr(model, col)` nổ `AttributeError` LÚC CHẠY.

    Nổ còn là may. Trường hợp xấu hơn: tên đó trúng một thuộc tính khác của model
    (quan hệ, `@property`, phương thức) — SQLAlchemy dựng ra một điều kiện vô
    nghĩa nhưng hợp lệ, và phạm vi lọc sai mà không báo gì.
    """
    fields = SCOPE_FIELDS[entity]
    assert fields is not PUBLIC, f"{entity} khai PUBLIC — bỏ khỏi ENTITY_MODEL_PATHS"
    model = model_of(entity)
    exempt = BB2_EXEMPT.get(entity, set())
    for dim, col in fields.items():
        if col in exempt:
            continue
        attr = getattr(model, col, None)
        assert attr is not None, (
            f"SCOPE_FIELDS['{entity}']['{dim}'] = '{col}' — {model.__name__} không có "
            "cột này. Sửa tên cột, đừng bỏ chiều đi."
        )
        assert hasattr(attr, "in_"), (
            f"SCOPE_FIELDS['{entity}']['{dim}'] = '{col}' trỏ vào {attr!r} — đây không "
            "phải cột. Điều kiện dựng từ nó sẽ chạy được nhưng lọc sai."
        )


def test_bb2_moi_entity_co_loc_that_deu_phai_co_model():
    """Chiều ngược lại: khai cột thật mà quên thêm vào map = không ai kiểm nó."""
    real = {e for e, f in SCOPE_FIELDS.items() if f is not PUBLIC}
    assert sorted(real - set(ENTITY_MODEL_PATHS)) == [], (
        "entity khai cột thật nhưng chưa có trong `scope_factory.ENTITY_MODEL_PATHS` "
        "→ BB-2 không kiểm tới nó."
    )


# ── BB-3 ────────────────────────────────────────────────────────────────────────

#  Khai `PUBLIC` là nói "entity này CỐ Ý không lọc theo dòng". Đó là cách nhanh
#  nhất để làm bài kiểm B-07 xanh mà không phải nghĩ — nên bắt phải ghi tên vào
#  đây kèm lý do người đọc hiểu được. Lý do đầy đủ nằm ở `core/scoping.py`.
BB3_PUBLIC_CO_LY_DO = {
    "warehouse": "danh mục kho dùng chung mọi pháp nhân",
    "unit": "danh mục đơn vị tính dùng chung",
    "item_group": "danh mục phân loại dùng chung",
    "brand": "danh mục thương hiệu dùng chung",
    "supplier": "danh mục NCC dùng chung — giấu NCC thì tắt bằng QUYỀN supplier.read",
    "product": "danh mục SP/vật tư dùng chung, hạt dữ liệu của cả hệ (D-025)",
    "category_assignee": "bảng phân công NSTM theo phân loại, không thuộc pháp nhân nào",
    "doc_type": "danh mục nền Văn thư, tách khóa là để phân quyền theo MÀN HÌNH (CR-157)",
    "doc_template": "cùng lý do CR-157",
    "doc_numbering_rule": "cùng lý do CR-157",
    "doc_link_rule": "cùng lý do CR-157",
    "security_level": "thang mức mật dùng chung",
    "external_party": "danh bạ đối tác ngoài dùng chung",
    "seal_type": "danh mục loại dấu dùng chung",
    "vehicle": "danh mục xe dùng chung",
    "driver": "danh mục tài xế dùng chung",
    "help_article": "bài hướng dẫn, ai cũng đọc được",
    "role": "danh mục vai trò — phạm vi của nó là quyền role.write",
    "setting": "cấu hình hệ thống, toàn hệ theo thiết kế",
    "mailbox": "cột company_id chỉ để LỌC HIỂN THỊ; ai gửi được nằm ở tab_mailbox_member",
    "report": "quyền HÀNH ĐỘNG, không có bảng để lọc",
    "backup": "quyền HÀNH ĐỘNG toàn hệ",
    "import": "quyền HÀNH ĐỘNG — ⚠️ nghĩa là nhập được cho MỌI pháp nhân, xem cụm 07 C3",
    "payment": "quyền HÀNH ĐỘNG, không có model nào",
    "assistant": "cổng require() thuần; dữ liệu bot đọc đã qua apply_scope của từng tool",
    "forum_post": "luật audience riêng viết thẳng trong WHERE của API feed (QĐ-D3)",
    "forum_board": "cùng lý do forum_post (QĐ-D7a)",
    "work_task": "phạm vi thật = tư cách THÀNH VIÊN list; NGHĨA VỤ tự lọc qua visible_list_ids",
    "leave_type": "danh mục luật nghỉ dùng chung; ai sửa gác bằng leave_type.write",
    "holiday": "company_id = 0 nghĩa là 'áp mọi pháp nhân'; lọc đúng ở workday_service",
    "meeting_room": "company_id = 0 nghĩa là 'phòng dùng chung'; lọc đúng ở list_availability",
}


def test_bb3_khai_public_phai_co_ten_trong_danh_sach_kem_ly_do():
    """Thêm entity mới rồi khai `PUBLIC` cho nhanh → đỏ ở đây, buộc phải ghi lý do."""
    public = {e for e, f in SCOPE_FIELDS.items() if f is PUBLIC}
    undeclared = sorted(public - set(BB3_PUBLIC_CO_LY_DO))
    assert undeclared == [], (
        f"{len(undeclared)} entity khai PUBLIC mà chưa ghi lý do: {undeclared}. "
        "Thêm vào BB3_PUBLIC_CO_LY_DO kèm MỘT CÂU nói rõ vì sao entity này cố ý "
        "không lọc theo dòng — hoặc khai cột thật ở SCOPE_FIELDS."
    )
    stale = sorted(set(BB3_PUBLIC_CO_LY_DO) - public)
    assert stale == [], f"đã hết PUBLIC nhưng còn tên trong danh sách: {stale}"


def test_bb3_khong_entity_nao_vua_public_vua_co_cot():
    """Ba trạng thái phải rời nhau: PUBLIC · khai cột · chưa khai (B-07 chặn)."""
    for entity in ENTITIES:
        f = SCOPE_FIELDS.get(entity)
        assert f is not None, f"{entity} chưa khai — xem test_pham_vi_khai_du_b07"
        assert (f is PUBLIC) != bool(f), f"{entity} vừa là PUBLIC vừa có cột: {f!r}"


# ── BB-4 ────────────────────────────────────────────────────────────────────────

#  41/68 controller không gọi `apply_scope`/`get_scoped`/`scope_condition`.
#
#  ⚠️ PHẦN LỚN CÓ LÝ DO ĐÚNG. Đây là đếm CHUỖI, không phải kết luận: bốn module
#  gác bằng hàm tự viết trong thân hàm (`import_tool._guard`,
#  `export_log._guard_view`, `comment.resolve_doc`, `document.ensure_can`) nên
#  grep không thấy. Gọi bừa một dòng ở đây là lỗ thì tốn nửa ngày và làm mất tin
#  vào cả đợt — soi mã trước.
#
#  Giá trị của bài kiểm này KHÔNG nằm ở 40 dòng đang có, mà ở dòng thứ 41: ai
#  thêm controller mới buộc phải trả lời "màn này có phải lọc phạm vi không".
BB4_CONTROLLER_MIEN_TRU = {
    # -- gác bằng hàm tự viết trong thân hàm, grep không thấy --
    "import_tool/controller.py": "gác bằng `_guard` → user_has_permission(..., 'import')",
    "export_log/controller.py": "gác bằng `_guard_view` (can_view_any hoặc setting.read)",
    "comment/controller.py": "gác bằng `service.resolve_doc` — làm CẢ require lẫn apply_scope",
    "document/controller.py": "gác bằng `access_service.ensure_can` (2 tầng) — cụm 05 B",
    "document/link_controller.py": "cùng `ensure_can` — cụm 05",
    "document/clone_controller.py": "cùng `ensure_can` — cụm 05",
    "document/scope_controller.py": "cùng `ensure_can` — cụm 05",
    "document/signature_controller.py": "cùng `ensure_can` — cụm 05",
    "document/template_controller.py": "cùng `ensure_can` — cụm 05",
    "document/dashboard_controller.py": "số tổng, đi qua `ensure_can` — cụm 04 + 05",
    "approval/instance_controller.py": "gác bằng `entity_hooks.can_read` — cụm 07 A",
    "approval/delegation_controller.py": "gác bằng `has_global_scope` — cụm 07 A9",
    "work/controller.py": "work_task PUBLIC + NGHĨA VỤ tự lọc `visible_list_ids` — cụm 07 D1",
    "work/task_controller.py": "cùng `visible_list_ids` — cụm 07 D1",
    "forum/controller.py": "luật audience riêng trong WHERE của feed — cụm 07 D4",
    # -- không có dữ liệu theo dòng để lọc --
    "auth/controller.py": "đăng nhập/đổi mật khẩu — chưa có phiên quyền để lọc",
    "meta/controller.py": "hằng số + danh mục mã trạng thái, không đọc bảng nghiệp vụ",
    "backup/controller.py": "sao lưu toàn hệ, require('backup') là đúng cổng",
    "setting/controller.py": "cấu hình toàn hệ (PUBLIC)",
    "role/controller.py": "danh mục vai trò (PUBLIC) — cổng là quyền role.write",
    "audit/controller.py": "# QUYẾT ĐỊNH CHỜ (cụm 07 C1): nhật ký toàn hệ hay bị phạm vi cắt?",
    # -- thư/thông báo của CHÍNH MÌNH, lọc bằng user_id chứ không bằng phạm vi --
    "notification/controller.py": "chỉ đọc thư gửi cho mình, lọc theo user_id — cụm 07 B1",
    "push/controller.py": "đăng ký thiết bị của chính mình",
    "user_preference/controller.py": "tùy chọn cá nhân của chính mình",
    "notification/email_exclusion_controller.py": "cấu hình gửi thư toàn hệ",
    "notification/email_template_controller.py": "mẫu thư toàn hệ",
    "leave/inbox_controller.py": "hộp việc duyệt của CHÍNH MÌNH (TASK_PENDING) — cụm 06",
    "meeting_room/inbox_controller.py": "cùng lý do leave/inbox — cụm 06",
    # -- danh mục PUBLIC: cổng là QUYỀN, không phải phạm vi --
    "catalog/controller.py": "unit/item_group/brand — PUBLIC",
    "product/controller.py": "product — PUBLIC (D-025)",
    "supplier/controller.py": "supplier — PUBLIC, giấu NCC bằng quyền supplier.read",
    "category_assignee/controller.py": "category_assignee — PUBLIC",
    "doc_catalog/controller.py": "doc_type/security_level/external_party — PUBLIC",
    "doc_catalog/issue_code_controller.py": "cấp số hiệu, ràng buộc ở sổ — cụm 05",
    "doc_catalog/link_rule_controller.py": "doc_link_rule — PUBLIC (CR-157)",
    "doc_catalog/numbering_rule_controller.py": "doc_numbering_rule — PUBLIC (CR-157)",
    "leave/catalog_controller.py": "leave_type + holiday — PUBLIC, xem lý do ở scoping.py",
    "vehicle_booking/catalog_controller.py": "vehicle + driver — PUBLIC",
    "help_center/controller.py": "help_article — PUBLIC, bài hướng dẫn ai cũng đọc",
    "faq/controller.py": "câu hỏi thường gặp, nội dung công khai",
}

_SCOPE_CALLS = ("apply_scope", "get_scoped", "scope_condition")


def _modules_dir() -> Path:
    """Thư mục `app/modules` — hỏi chính gói đã nạp.

    Không suy từ `__file__` của tệp test: trong container mã nguồn nằm ở `/app`
    còn test ở `/app/test/backend`, đường lùi hai cấp trỏ ra ngoài và bài kiểm
    lặng lẽ `skip` — tức là mất luôn cái nó canh, đúng lúc CI cần nó nhất.
    """
    import app.modules

    return Path(app.modules.__file__).parent


def _controllers_without_scope_call() -> dict[str, str]:
    """{đường dẫn tương đối: nội dung} cho controller không gọi hàm phạm vi nào."""
    root = _modules_dir()
    out = {}
    for path in sorted(root.rglob("*controller*.py")):
        text = path.read_text(encoding="utf-8")
        if not any(call in text for call in _SCOPE_CALLS):
            out[str(path.relative_to(root))] = text
    return out


def test_bb4_controller_khong_loc_pham_vi_phai_co_ten_kem_ly_do():
    """Thêm controller mới → hoặc gọi phạm vi, hoặc ghi lý do vào danh sách này.

    Đây là bài kiểm DANH SÁCH TRẮNG, không phải bài kiểm đúng/sai: nó không biết
    controller nào thật sự cần lọc. Việc nó làm được là **không cho ai lặng lẽ
    thêm một màn không lọc phạm vi**.
    """
    found = set(_controllers_without_scope_call())
    undeclared = sorted(found - set(BB4_CONTROLLER_MIEN_TRU))
    assert undeclared == [], (
        f"{len(undeclared)} controller không gọi apply_scope/get_scoped/scope_condition "
        f"và chưa có lý do: {undeclared}.\n"
        "Hoặc gọi `apply_scope(...)` / `get_scoped(...)`, hoặc thêm vào "
        "BB4_CONTROLLER_MIEN_TRU kèm lý do THẬT (gác bằng hàm nào, hay entity PUBLIC "
        "vì sao). Đừng ghi lý do lấy lệ — soi mã trước."
    )
    stale = sorted(set(BB4_CONTROLLER_MIEN_TRU) - found)
    assert stale == [], (
        f"{len(stale)} tệp đã lọc phạm vi (hoặc đã xóa) nhưng còn tên trong danh sách "
        f"miễn trừ: {stale}. Rút tên ra — danh sách còn rác thì lần sau không ai tin nó."
    )


# ── Khung dựng dữ liệu chạy được ───────────────────────────────────────────────


def test_khung_dung_du_lieu_chay_duoc(db, world):
    """Bài tự kiểm của `scope_factory` — hỏng khung thì cả 8 cụm sau sai theo."""
    from app.modules.contract.model import Contract

    db.add_all([Contract(code="HD_A", company_id=world.co["A"], title="Của A"),
                Contract(code="HD_B", company_id=world.co["B"], title="Của B")])
    db.flush()
    ids = {c.code: c.id for c in db.query(Contract).all()}

    # Phạm vi `company` — chỉ thấy hợp đồng pháp nhân mình.
    a1 = world.grant("a1", "contract", scope="company")
    assert a1.sees(Contract) == {ids["HD_A"]}
    assert a1.can_get(Contract, ids["HD_A"]) is True
    assert a1.can_get(Contract, ids["HD_B"]) is False, "gõ id vào URL không được lọt"

    # Vai trò THỨ HAI hợp thêm phạm vi — `scope_condition` OR các grant.
    a1.grant("contract", scope="all")
    assert a1.sees(Contract) == set(ids.values()), "hai vai trò phải HỢP, không phải GIAO"

    # Nhân sự KHÔNG có tài khoản vẫn dựng được (ca hỏng số 1 của cụm 01).
    assert "khongtk" in world.emp
    assert "khongtk" not in world._actors

    # Hai phòng TRÙNG TÊN khác pháp nhân — nền của lỗ 09-A.
    assert world.dept["A.kt"] != world.dept["B.kt"]


def test_khung_khong_de_ro_ri_cache_quyen(db, world):
    """Cấp thêm quyền GIỮA chừng phải có hiệu lực NGAY, không đợi 60 giây."""
    from app.modules.company.model import Company

    a2 = world.actor("a2")
    assert a2.profile()["grants"] == []
    a2.grant("company", scope="company")
    assert a2.sees(Company, "company") == {world.co["A"]}
