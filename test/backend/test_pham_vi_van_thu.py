"""Cụm 05 — VĂN THƯ: hai tầng quyền chồng lên nhau.

Văn thư là phân hệ **duy nhất** có hai tầng quyền xếp chồng:

1. **phạm vi RBAC** (`core/scoping.scope_condition`) — chỉ biết THU HẸP;
2. **`document/access_service`** — chia sẻ đích danh, thành viên sổ, phạm vi áp
   dụng, việc duyệt: những nguồn quyền **CỘNG THÊM**.

Chính vì tầng 2 phải cộng thêm mà `scope_condition` mới được tách khỏi
`apply_scope` (`scoping.py:449-461`). Mọi lỗ của cụm này nằm ở **chỗ hai tầng
gặp nhau**, không nằm trong từng tầng.

──────────────────────────────────────────────────────────────────────────────
CÂU TRẢ LỜI VIẾT RA ĐƯỢC — «văn bản X, người Y: ai quyết định, theo thứ tự nào»
──────────────────────────────────────────────────────────────────────────────

Đọc MỘT văn bản (`access_service.can(..., "read")`, `access_service.py:356-450`).
Dừng ở dòng đầu tiên khớp; không có dòng nào khớp thì **không được**:

    0. hành động ≠ đọc  → phải ĐỌC ĐƯỢC trước đã, không thì dừng     (:371)
    1. đã BÃI BỎ + không phải người tạo/chịu trách nhiệm/bãi bỏ,
       và phạm vi vai trò không phải company|all                     → KHÔNG (:377)
    2. đang / đã có VIỆC DUYỆT trên chính văn bản này                → ĐƯỢC  (:388)
    3. dòng CẤM đích danh (mình · phòng mình · pháp nhân mình · vai trò mình)
                                                                     → KHÔNG (:400)
    4. dòng CHO PHÉP đích danh                                        → ĐƯỢC  (:402)
    5. LOẠI văn bản bật `is_personal` mà mình không phải người nghỉ /
       người lập → chỉ vai trò phạm vi *tất cả* đi tiếp               (:416)
    6. nằm trong PHẠM VI ÁP DỤNG của văn bản (chỉ chiều ĐỌC)          → ĐƯỢC  (:427)
    7. là THÀNH VIÊN quyển sổ chứa nó (quản lý: đọc+ghi · người xem: đọc)
                                                                     → ĐƯỢC  (:433)
    8. đọc được một BẢN CLONE của nó (chỉ chiều ĐỌC)                  → ĐƯỢC  (:441)
    9. PHẠM VI VAI TRÒ (`scope_condition`) có với tới nó không        (:444-450)

Danh sách (`visible_condition`, `:220-308`) phải nói **cùng một câu**, và nó
ghép ngược lại: `phạm vi ∪ (chia đích danh, thành viên sổ, việc duyệt của tôi)`,
rồi `∩ luật văn bản cá nhân`, `∩ ¬cấm đích danh`, `∩ luật bãi bỏ`.

⚠️ **Mức mật KHÔNG nằm trong danh sách trên.** `secrecy_level` hôm nay chỉ là
NHÃN — xem `document/controller.py:19-21` và `doc_catalog/model.py:54-57`. Ca
A1 dưới đây ghim đúng sự vắng mặt đó.

⚠️ Đừng lẫn với `test_pham_vi_ap_dung.py`: tệp đó kiểm *phạm vi ÁP DỤNG của văn
bản* (bước 6), không phải phạm vi dữ liệu RBAC (bước 9).

Bốn nhóm ca: **A** giao hai tầng · **B** đủ 29 route của `document/controller.py`
· **C** bình luận · **D** danh mục Văn thư.
"""
import inspect
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.modules.document import access_service, controller as doc_controller
from app.modules.document.model import (ORIGIN_INTERNAL, STATUS_EFFECTIVE,
                                        STATUS_REVOKED, Document)
from app.modules.document.query import documents_query
from scope_factory import build_world  # noqa: F401 — fixture `world` dùng nó


# ══════════════════════════════════════════════════════════════════════════════
#  Dựng dữ liệu Văn thư trên thế giới mẫu của cụm 00
# ══════════════════════════════════════════════════════════════════════════════
#
#  Cố ý dựng bản ghi THẲNG bằng model thay vì đi `service.create_document`:
#  đường service kéo theo cấp số, phiên bản, kiểm mức mật — toàn thứ không liên
#  quan tới phạm vi, mà lại bắt mọi ca phải khai đủ pháp nhân có `issue_code`.
#  Các fixture nặng của `test_ban_hanh_*.py` giữ nguyên chỗ của chúng (chúng
#  kiểm *phạm vi áp dụng*, bước 6); ở đây cần bước 3, 4, 7, 9.


def create_doc(db, *, code, company_id, department_id, created_by,
               doc_type_id, book_id=None, status=STATUS_EFFECTIVE,
               owner_employee_id=0, secrecy_level=2):
    """Một văn bản tối thiểu — chỉ điền cột mà hai tầng quyền nhìn tới."""
    row = Document(origin=ORIGIN_INTERNAL, doc_type_id=doc_type_id,
                   company_id=company_id, department_id=department_id,
                   owner_employee_id=owner_employee_id, title=f"Văn bản {code}",
                   legacy_code=code, status=status, book_id=book_id,
                   secrecy_level=secrecy_level, created_by=created_by,
                   updated_by=created_by)
    db.add(row)
    db.flush()
    return row


@pytest.fixture()
def vt(world):
    """Hai loại văn bản, hai quyển sổ, năm văn bản trải đủ hai pháp nhân.

    `ca_nhan_b` dùng loại bật `is_personal` — nhánh thu hẹp ở bước 5; `mat_a`
    để mức Tuyệt mật để ca A1 chứng minh cột đó không gác gì.
    """
    from app.modules.doc_catalog.book_model import DocumentBook
    from app.modules.doc_catalog.model import DocType

    db = world.db
    loai_qc = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    loai_np = DocType(code="NP", name="Đơn nghỉ phép", id_scheme=2,
                      number_when=2, is_personal=True)
    db.add_all([loai_qc, loai_np])
    db.flush()

    uid = {k: world.actor(k).user.id for k in ("a1", "a2", "a3", "b1")}
    so_a = DocumentBook(code="SO_A", name="Sổ pháp nhân A", kind=3,
                        company_id=world.co["A"], created_by=uid["a1"],
                        updated_by=uid["a1"], is_active=True)
    so_b = DocumentBook(code="SO_B", name="Sổ pháp nhân B", kind=3,
                        company_id=world.co["B"], created_by=uid["b1"],
                        updated_by=uid["b1"], is_active=True)
    db.add_all([so_a, so_b])
    db.flush()

    docs = {
        "a_kt": create_doc(db, code="A-KT", company_id=world.co["A"],
                           department_id=world.dept["A.kt"], created_by=uid["a1"],
                           doc_type_id=loai_qc.id),
        "a_mua": create_doc(db, code="A-MUA", company_id=world.co["A"],
                            department_id=world.dept["A.mua"], created_by=uid["a3"],
                            doc_type_id=loai_qc.id),
        "mat_a": create_doc(db, code="A-MAT", company_id=world.co["A"],
                            department_id=world.dept["A.kt"], created_by=uid["a2"],
                            doc_type_id=loai_qc.id, secrecy_level=4),
        "b_kt": create_doc(db, code="B-KT", company_id=world.co["B"],
                           department_id=world.dept["B.kt"], created_by=uid["b1"],
                           doc_type_id=loai_qc.id),
        "b_so": create_doc(db, code="B-SO", company_id=world.co["B"],
                           department_id=world.dept["B.kt"], created_by=uid["b1"],
                           doc_type_id=loai_qc.id, book_id=so_b.id),
        "ca_nhan_b": create_doc(db, code="B-NP", company_id=world.co["B"],
                                department_id=world.dept["B.kt"], created_by=uid["b1"],
                                doc_type_id=loai_np.id,
                                owner_employee_id=world.emp["b1"]),
    }
    db.commit()
    return SimpleNamespace(world=world, db=db, doc=docs, so_a=so_a, so_b=so_b,
                           loai_qc=loai_qc, loai_np=loai_np)


def pick(vt, *keys: str) -> set[int]:
    return {vt.doc[k].id for k in keys}


def visible_ids(vt, actor, action: str = "read") -> set[int]:
    """Tập id văn bản mà DANH SÁCH trả về — tầng 1 ∪ tầng 2, đúng như controller."""
    query = documents_query(vt.db)
    cond = access_service.visible_condition(actor.user, actor.profile(), action)
    if cond is not None:
        query = query.filter(cond)
    return {row.id for row in query.all()}


def can(vt, actor, key: str, action: str = "read") -> bool:
    """Tầng 2 trên MỘT văn bản — đúng hàm mà mọi endpoint chi tiết gọi."""
    return access_service.can(vt.db, vt.doc[key], actor.user, actor.profile(), action)


def share(vt, key: str, actor, *, effect, read=True, write=False):
    """Một dòng `tab_document_access` đích danh theo NHÂN SỰ."""
    from app.modules.document.access_model import SUBJECT_EMPLOYEE, DocumentAccess

    row = DocumentAccess(document_id=vt.doc[key].id, subject_kind=SUBJECT_EMPLOYEE,
                         subject_id=actor.employee.id, effect=effect,
                         can_read=read, can_write=write)
    vt.db.add(row)
    vt.db.commit()
    return row


def add_book_member(vt, book, actor, role: int):
    from app.modules.doc_catalog.book_model import DocumentBookMember

    vt.db.add(DocumentBookMember(book_id=book.id, employee_id=actor.employee.id,
                                 role=role))
    vt.db.commit()


def make_request(path: str = "/api/documents", **params) -> Request:
    """`Request` tối thiểu cho `apply_filters` — nó chỉ đọc `query_params`."""
    query = urlencode({k: v for k, v in params.items() if v not in (None, "")})
    return Request({"type": "http", "method": "GET", "path": path,
                    "headers": [], "query_string": query.encode()})


PAGE = {"offset": 0, "limit": 50}


def payload(response) -> dict:
    """Bóc phong bì `{success, message, data}` ra khỏi `JSONResponse`.

    `core.response.success()` trả về `JSONResponse` chứ không trả dict, nên gọi
    thẳng hàm controller thì phải giải mã thân phản hồi mới đọc được `data`.
    """
    import json

    return json.loads(response.body)


# ══════════════════════════════════════════════════════════════════════════════
#  A. Giao của hai tầng
# ══════════════════════════════════════════════════════════════════════════════


def test_a1_muc_mat_tuyet_mat_khong_chan_ai_ca(vt):
    """🔴 A1 — kế hoạch giả định "mức mật cao thì tầng 2 chặn". **KHÔNG có chuyện đó.**

    Soi mã trước khi gọi là lỗ: `access_service.py` 577 dòng không đọc
    `Document.secrecy_level` một lần nào, và hai chỗ khác nói thẳng điều đó —
    `document/controller.py:19-21` ("lớp kiểm mức mật vẫn CHƯA có, nó là P5") và
    `doc_catalog/model.py:54-57` ("cột này KHÔNG gác quyền đọc").

    Nên đây không phải lỗ hổng mới phát hiện, mà là một tính năng chưa làm. Ca
    này ghim sự vắng mặt đó để lúc P5 lên thì nó đỏ đúng chỗ, và để không ai
    tưởng nhầm rằng đánh dấu Tuyệt mật là đã giấu được văn bản.

    Cái CHẶN thật ở tầng 2 là dòng CẤM đích danh — xem ca A1b ngay dưới.
    """
    a1 = vt.world.grant("a1", "document", scope="company")
    assert pick(vt, "mat_a") <= visible_ids(vt, a1), "mức mật 4 vẫn nằm trong danh sách"
    assert can(vt, a1, "mat_a") is True

    nguon = inspect.getsource(access_service)
    assert "secrecy_level" not in nguon, "có ai đó vừa thêm lớp mức mật — cập nhật ca này"


def test_a1b_dong_cam_dich_danh_chan_van_ban_dang_o_trong_pham_vi(vt):
    """A1 (bản đúng) — trong phạm vi RBAC nhưng tầng 2 CẤM → mất cả hai đầu ra.

    Đây là chiều duy nhất tầng 2 thu hẹp được thứ tầng 1 đã cho. Hỏng thì hỏng
    lệch: `can()` chặn mà `visible_condition` quên trừ thì văn bản vẫn nằm trong
    danh sách và trong file Excel, bấm vào mới 404 — lộ đúng cái tiêu đề mà dòng
    cấm sinh ra để giấu (K03).
    """
    from app.modules.document.access_model import EFFECT_DENY

    a1 = vt.world.grant("a1", "document", scope="company")
    assert visible_ids(vt, a1) == pick(vt, "a_kt", "a_mua", "mat_a")

    share(vt, "a_mua", a1, effect=EFFECT_DENY)
    assert can(vt, a1, "a_mua") is False
    assert visible_ids(vt, a1) == pick(vt, "a_kt", "mat_a"), "danh sách phải trừ cùng lúc"


def test_a2_van_ban_ngoai_pham_vi_nhung_duoc_chia_dich_danh_thi_mo_duoc(vt):
    """A2 — nguồn quyền CỘNG THÊM: `apply_scope` một mình sẽ cắt mất người này.

    `B-08` đã kiểm điều đó cho ĐÍNH KÈM; đây là bản cho chính văn bản, và kiểm
    cả hai đầu ra. Nếu ai đó "dọn cho gọn" bằng cách đổi `visible_condition`
    thành `apply_scope`, người vừa được chia tay mất sạch văn bản mà không có
    thông báo nào — đúng lỗi khách báo 24/08/2026 ở phần Sổ.
    """
    from app.modules.document.access_model import EFFECT_ALLOW

    a1 = vt.world.grant("a1", "document", scope="company")   # pháp nhân A
    assert can(vt, a1, "b_kt") is False

    share(vt, "b_kt", a1, effect=EFFECT_ALLOW)
    assert can(vt, a1, "b_kt") is True
    assert visible_ids(vt, a1) == pick(vt, "a_kt", "a_mua", "mat_a", "b_kt")


def test_a3_ngoai_ca_hai_tang_thi_404_chu_khong_phai_403(vt):
    """A3 — `ensure_can` trả **404** cho chiều ĐỌC, 403 cho sửa/xóa (`:453-464`).

    Cố ý: 403 đã là xác nhận "có văn bản này, anh không được xem". Gộp hai mã
    lại thì màn tìm kiếm thành máy dò sự tồn tại của văn bản mật.
    """
    a1 = vt.world.grant("a1", "document", scope="company", actions=("read", "write"))

    with pytest.raises(HTTPException) as err:
        access_service.ensure_can(vt.db, vt.doc["b_kt"], a1.user, a1.profile(), "read")
    assert err.value.status_code == 404

    #  Văn bản mình ĐỌC được nhưng không SỬA được thì 403 — đã lộ sẵn rồi.
    a2 = vt.world.grant("a2", "document", scope="company")   # chỉ có read
    with pytest.raises(HTTPException) as err:
        access_service.ensure_can(vt.db, vt.doc["a_kt"], a2.user, a2.profile(), "write")
    assert err.value.status_code == 403


def test_a4_o_loai_tru_phong_ban_khong_de_duoc_len_chia_se_dich_danh(vt):
    """🔶 A4 — ghim hành vi hiện tại, **KHÔNG kết luận đúng/sai**.

    Ô số 4 của hộp thoại «Phạm vi — <vai trò>» (*Loại trừ phòng ban*) là thứ
    người khai quyền dùng để giấu phòng Nhân sự / Kế toán. Nó đi qua
    `_explicit_cond` nên chỉ thu hẹp phần `scope`; còn dòng CHO PHÉP đích danh
    thì `visible_condition:272` OR **ra ngoài** `scope`, và `can():402` trả
    `True` trước khi đọc tới `scope_condition`. Kết quả: chia tay đích danh
    thắng ô loại trừ.

    Có lập luận cho cả hai phía. Bịt lại là **cắt quyền xem của người đang được
    chia sẻ đích danh** — nhóm đông nhất của phân hệ này, và họ mất quyền lặng
    lẽ. Để nguyên thì ô loại trừ không phải hàng rào kín.

    # QUYẾT ĐỊNH CHỜ: ô «Loại trừ phòng ban» có được đè lên dòng CHO PHÉP đích
    # danh không? (Nếu có thì phải kèm cảnh báo trên màn Chia sẻ: "phòng này
    # đang bị loại trừ ở vai trò X, chia xong người đó vẫn không thấy".)
    """
    from app.modules.document.access_model import EFFECT_ALLOW

    a1 = vt.world.grant("a1", "document", scope="company", exc_dept=["A.kt"])
    assert visible_ids(vt, a1) == pick(vt, "a_mua"), "ô loại trừ cắt đúng phòng A.kt"

    share(vt, "a_kt", a1, effect=EFFECT_ALLOW)
    assert can(vt, a1, "a_kt") is True, "chia đích danh thắng ô loại trừ"
    assert visible_ids(vt, a1) == pick(vt, "a_mua", "a_kt")


def test_a5_pham_vi_cong_ty_khong_duoc_coi_la_quan_tri_toan_he(vt):
    """A5 — `has_global_scope` (`scoping.py:430-446`) chỉ nhận phạm vi *tất cả*.

    Hàm này mở ngoại lệ cho **lập ủy quyền hộ người khác** và **bàn giao việc
    duyệt của người khác** — hai thứ không gắn với bảng nào nên không hỏi được
    bằng `scope_condition`. Nới nó ra tới `company` là mọi trưởng bộ phận đa
    pháp nhân ký hộ được người khác.

    Ba vế: `company` KHÔNG · `all` CÓ · và `all` trên khóa KHÁC cũng KHÔNG —
    hàm nhận `entity` chứ không hỏi "người này có phải admin nói chung".
    """
    from app.core.scoping import has_global_scope

    a1 = vt.world.grant("a1", "document", scope="company")
    assert has_global_scope(a1.profile(), "document", "read") is False
    assert visible_ids(vt, a1) == pick(vt, "a_kt", "a_mua", "mat_a"), "vẫn lọc thật"

    a2 = vt.world.grant("a2", "document", scope="all")
    assert has_global_scope(a2.profile(), "document", "read") is True
    assert has_global_scope(a2.profile(), "document_book", "read") is False

    a3 = vt.world.grant("a3", "document", scope="all", actions=("read",))
    assert has_global_scope(a3.profile(), "document", "write") is False, (
        "phạm vi *tất cả* nhưng không có quyền write thì không phải quản trị chiều đó")


def test_a6_thanh_vien_so_mo_duoc_so_va_van_ban_trong_so_ngoai_phap_nhan(vt):
    """A6 — sổ là NGUỒN QUYỀN thứ ba, cắt ngang cả pháp nhân.

    Hai đầu ra phải mở cùng lúc, và đây là chỗ chúng từng lệch (khách báo
    25/08/2026): danh sách SỔ đi qua `book_service.book_view_condition`, danh
    sách VĂN BẢN đi qua `access_service._book_ids` — hai hàm ở hai module. Mở
    một bên thì người được chia sổ thấy quyển sổ mà bấm vào thì rỗng.

    Vế cuối là chốt chặn "không rò": `b_kt` cùng pháp nhân B nhưng KHÔNG nằm
    trong sổ vẫn phải tối. Thiếu vế đó thì một hàm trả "mở hết" cũng xanh.
    """
    from app.modules.doc_catalog import book_service
    from app.modules.doc_catalog.book_model import DocumentBook

    a1 = vt.world.grant("a1", "document", scope="company")
    a1.grant("document_book", scope="company")
    add_book_member(vt, vt.so_b, a1, role=access_service.ROLE_BOOK_VIEWER)

    cond = book_service.book_view_condition(a1.user, a1.profile())
    so_thay = {b.id for b in vt.db.query(DocumentBook).filter(cond).all()}
    assert so_thay == {vt.so_a.id, vt.so_b.id}, "sổ pháp nhân B mở nhờ dòng thành viên"

    assert can(vt, a1, "b_so") is True
    assert can(vt, a1, "b_kt") is False, "cùng pháp nhân B nhưng ngoài sổ thì vẫn tối"
    assert visible_ids(vt, a1) == pick(vt, "a_kt", "a_mua", "mat_a", "b_so")


def test_a6b_nguoi_xem_so_khong_sua_duoc_van_ban_trong_so(vt):
    """Vế thứ hai của A6: `_book_ids` phân vai — quản lý sổ (1) mới có `write`.

    `access_service.py:108-125`. Gộp hai vai làm một là ô «Người xem sổ» hóa
    thành quyền sửa: văn thư thêm một người vào cho họ tra cứu, người đó sửa
    được số hiệu của mọi văn bản trong quyển.
    """
    a1 = vt.world.grant("a1", "document", scope="company", actions=("read", "write"))
    add_book_member(vt, vt.so_b, a1, role=access_service.ROLE_BOOK_VIEWER)
    assert can(vt, a1, "b_so", "read") is True
    assert can(vt, a1, "b_so", "write") is False

    a2 = vt.world.grant("a2", "document", scope="company", actions=("read", "write"))
    add_book_member(vt, vt.so_b, a2, role=access_service.ROLE_BOOK_MANAGER)
    assert can(vt, a2, "b_so", "write") is True
    assert can(vt, a2, "b_so", "delete") is False, "giữ sổ không có nghĩa là được dọn sổ"


def test_a7_hai_o_phong_ban_vo_hieu_tren_document_book(vt):
    """A7 — `SCOPE_FIELDS["document_book"]` cố ý KHÔNG có chiều phòng ban.

    Sổ thuộc pháp nhân, quyền xem cấp cho người đích danh (`book_model.py:37-41`).
    Nên hai ô phòng ban của hộp thoại phạm vi là **ô câm** trên khóa này: cả ô
    *Phòng ban được xem* (vốn CỘNG THÊM) lẫn ô *Loại trừ phòng ban* (vốn thu hẹp)
    đều không sinh mệnh đề nào — `_dept_match` đọc `SCOPE_FIELDS` ra dict không
    có `dept_id`/`dept_name` và trả `None`.

    Cùng họ với nghi ngờ 2 của cụm 01 (`test_b4_...` trên entity PUBLIC), nhưng
    tệ hơn một bậc: `document_book` KHÔNG phải PUBLIC — bậc `company` của nó cắt
    thật (vế cuối), nên người khai quyền có mọi lý do để tin hai ô kia cũng chạy.

    # QUYẾT ĐỊNH CHỜ: hộp thoại phạm vi có nên ẩn / tắt hai ô phòng ban khi
    # entity không khai chiều đó, thay vì nhận rồi lặng lẽ bỏ?
    """
    from app.modules.doc_catalog.book_model import DocumentBook

    def sees_books(actor):
        from app.modules.doc_catalog import book_service
        cond = book_service.book_view_condition(actor.user, actor.profile())
        q = vt.db.query(DocumentBook)
        return {b.id for b in (q if cond is None else q.filter(cond)).all()}

    #  Ô LOẠI TRỪ: sổ A do a1 mở, phòng A.kt là phòng của a1 — loại trừ không cắt.
    a1 = vt.world.grant("a1", "document_book", scope="company", exc_dept=["A.kt"])
    assert sees_books(a1) == {vt.so_a.id}

    #  Ô CỘNG THÊM: a2 phạm vi `own` không mở sổ nào; chọn thêm phòng A.kt (phòng
    #  đang giữ sổ A) vẫn không cộng được gì.
    a2 = vt.world.grant("a2", "document_book", scope="own", inc_dept=["A.kt"])
    assert sees_books(a2) == set()

    #  Vế đối chứng: chiều `company` của cùng entity thì cắt thật.
    b1 = vt.world.grant("b1", "document_book", scope="company")
    assert sees_books(b1) == {vt.so_b.id}


def test_a8_dinh_kem_van_ban_khong_phat_link_va_van_di_qua_hai_tang(vt):
    """A8 — tệp của văn bản: `url` RỖNG, và cửa xem đi qua đúng `access_service`.

    Hai nửa của cùng một luật:
      * `document_version` nằm trong `PRIVATE_ENTITIES` nên `_link_out` không trả
        đường tải thẳng kho — ai cầm chuỗi đó cũng mở được, kể cả người đã bị thu
        hồi quyền. Phải đi `/api/attachments/{id}/view`.
      * cửa `view` gọi `_check` → `ensure_in_scope` → `_ensure_document`
        (`attachment_scope.py:121-137`) — tức là **hai tầng**, không phải
        `apply_scope`. Ghim luôn: chia đích danh mở được tệp, đúng như mở được
        văn bản; ngoài phạm vi thì 404 chứ không 403.
    """
    from app.core.file_registry import is_private
    from app.modules.attachment import controller as ac
    from app.modules.attachment.controller import _link_out
    from app.modules.attachment.model import FileLink, StoredFile
    from app.modules.document.access_model import EFFECT_ALLOW
    from app.modules.document.version_model import DocumentVersion

    ban = DocumentVersion(document_id=vt.doc["b_kt"].id, content_html="<p>x</p>")
    vt.db.add(ban)
    vt.db.flush()
    tep = StoredFile(filename="a.pdf", file_key="k/a.pdf", url="https://kho/a.pdf",
                     content_type="application/pdf", size=1, sha256="s")
    vt.db.add(tep)
    vt.db.flush()
    lien_ket = FileLink(file_id=tep.id, entity="document_version", entity_id=ban.id,
                        doc_type="", sort_order=0)
    vt.db.add(lien_ket)
    vt.db.commit()

    assert is_private("document_version") is True
    assert _link_out(lien_ket, tep)["url"] == "", "không phát link công khai"

    a1 = vt.world.grant("a1", "document", scope="company")   # pháp nhân A
    with pytest.raises(HTTPException) as err:
        ac._check(vt.db, a1.user, "document_version", "read", ban.id)
    assert err.value.status_code == 404

    share(vt, "b_kt", a1, effect=EFFECT_ALLOW)
    assert ac._check(vt.db, a1.user, "document_version", "read", ban.id)


def test_a9_van_ban_ca_nhan_chan_ca_pham_vi_lan_thanh_vien_so(vt):
    """Phần giao còn thiếu tên trong kế hoạch: loại `is_personal` cắt **bước 6–9**.

    Đơn nghỉ phép quẳng vào một quyển sổ chung là cả phòng Hành chính đọc được —
    đúng thứ `access_service.py:405-417` + `:276-290` chặn. Ca này ghim rằng
    nhánh đó đứng ĐÚNG CHỖ: sau dòng chia đích danh (vẫn cho qua) nhưng trước
    thành viên sổ (không cho qua).

    Bốn vế, đọc từ trên xuống là đọc chính thứ tự quyết định.
    """
    from app.modules.document.access_model import EFFECT_ALLOW

    #  1. phạm vi công ty B — không đủ để mở đơn của người khác.
    b_kt = vt.world.grant("b1", "document", scope="company")
    assert can(vt, b_kt, "ca_nhan_b") is True, "b1 là chính người nghỉ"

    a1 = vt.world.grant("a1", "document", scope="all")
    assert can(vt, a1, "ca_nhan_b") is True, "vai trò phạm vi *tất cả* (HR) vẫn thấy"

    #  2. người ngoài, phạm vi company trên B: chặn.
    a2 = vt.world.grant("a2", "document", scope="company", inc_company=["B"])
    assert can(vt, a2, "ca_nhan_b") is False
    assert vt.doc["ca_nhan_b"].id not in visible_ids(vt, a2)

    #  3. thành viên sổ KHÔNG mở được đơn cá nhân…
    vt.doc["ca_nhan_b"].book_id = vt.so_b.id
    vt.db.commit()
    add_book_member(vt, vt.so_b, a2, role=access_service.ROLE_BOOK_MANAGER)
    assert can(vt, a2, "ca_nhan_b") is False, "quẳng đơn vào sổ chung không mở được nó"

    #  4. …nhưng chia ĐÍCH DANH thì có (một trong bốn nguồn hợp lệ).
    a3 = vt.world.grant("a3", "document", scope="company")
    share(vt, "ca_nhan_b", a3, effect=EFFECT_ALLOW)
    assert can(vt, a3, "ca_nhan_b") is True
    assert vt.doc["ca_nhan_b"].id in visible_ids(vt, a3)


def test_a10_van_ban_da_bai_bo_chi_con_bon_nhom_xem_duoc(vt):
    """Bãi bỏ là một thay đổi về QUYỀN XEM, không phải đổi nhãn (`revoke_access.py`).

    Nhân với điều kiện chứ không thay thế: phạm vi `dept` không giữ quyền, phạm
    vi `company` thì có (người giữ sổ phải tra được số đã cấp). Ghim cả hai
    chiều, vì bịt nhầm chiều thứ hai là thủng sổ đăng ký.
    """
    vt.doc["a_kt"].status = STATUS_REVOKED
    vt.db.commit()

    #  a2 ở phòng A.kt, phạm vi `dept`, KHÔNG phải người tạo/chịu trách nhiệm.
    a2 = vt.world.grant("a2", "document", scope="dept")
    assert can(vt, a2, "a_kt") is False
    assert vt.doc["a_kt"].id not in visible_ids(vt, a2)

    #  a1 là người tạo → vẫn thấy, dù phạm vi cũng chỉ `dept`.
    a1 = vt.world.grant("a1", "document", scope="dept")
    assert can(vt, a1, "a_kt") is True

    #  a3 phạm vi `company`: giữ sổ nên vẫn tra ra.
    a3 = vt.world.grant("a3", "document", scope="company")
    assert vt.doc["a_kt"].id in visible_ids(vt, a3)


# ══════════════════════════════════════════════════════════════════════════════
#  B. Đủ 29 route của `document/controller.py`
# ══════════════════════════════════════════════════════════════════════════════
#
#  Controller này có **0 lần gọi `apply_scope`/`get_scoped`**. Toàn bộ phần gác
#  nằm ở `_load()` → `ensure_can()` (một văn bản) và `_list_query()` →
#  `visible_condition()` (nhiều văn bản). Route nào lọt khỏi hai đường đó là lỗ
#  y hệt `db.get(...)` của B-08.
#
#  Bảng dưới là bản khai TAY của 29 route. Nó tồn tại để một route mới thêm vào
#  mà không khai thì test đỏ — chứ không phải để đọc cho vui.

GUARD_LOAD = "_load"                 # → ensure_can trên ĐÚNG một văn bản
GUARD_VISIBLE = "visible_condition"  # → lọc danh sách
GUARD_NONE = "khong-cham-van-ban"    # không đọc bản ghi văn bản nào

ROUTE_GUARD = {
    #  ── nhiều văn bản ────────────────────────────────────────────────────────
    ("GET", "/api/documents"): GUARD_VISIBLE,
    ("GET", "/api/documents/storage-locations"): GUARD_VISIBLE,
    ("GET", "/api/documents/export/xlsx"): GUARD_VISIBLE,
    #  ── không chạm văn bản nào ───────────────────────────────────────────────
    ("GET", "/api/documents/number-preview"): GUARD_NONE,
    ("POST", "/api/documents/import/parse"): GUARD_NONE,
    ("POST", "/api/documents"): GUARD_NONE,
    ("POST", "/api/documents/maintenance/activate-due"): GUARD_NONE,
    #  ⚠️ LỖ — xem `test_b4_...` bên dưới. Để đúng hiện trạng, không tô hồng.
    ("GET", "/api/documents/suggestions"): GUARD_NONE,
    #  ── một văn bản ──────────────────────────────────────────────────────────
    ("GET", "/api/documents/{document_id}"): GUARD_LOAD,
    ("POST", "/api/documents/{document_id}/copy"): GUARD_LOAD,
    ("PATCH", "/api/documents/{document_id}"): GUARD_LOAD,
    ("PATCH", "/api/documents/{document_id}/issue-number"): GUARD_LOAD,
    ("DELETE", "/api/documents/{document_id}/ban-nhap"): GUARD_LOAD,
    ("DELETE", "/api/documents/{document_id}"): GUARD_LOAD,
    ("POST", "/api/documents/{document_id}/submit"): GUARD_LOAD,
    ("POST", "/api/documents/{document_id}/approve"): GUARD_LOAD,
    ("GET", "/api/documents/{document_id}/mailboxes"): GUARD_LOAD,
    ("POST", "/api/documents/{document_id}/reject"): GUARD_LOAD,
    ("POST", "/api/documents/{document_id}/reviewed"): GUARD_LOAD,
    ("POST", "/api/documents/{document_id}/revoke"): GUARD_LOAD,
    ("GET", "/api/documents/{document_id}/export/docx"): GUARD_LOAD,
    ("GET", "/api/documents/{document_id}/versions"): GUARD_LOAD,
    ("GET", "/api/documents/{document_id}/versions/{version_id}"): GUARD_LOAD,
    ("POST", "/api/documents/{document_id}/versions"): GUARD_LOAD,
    ("PATCH", "/api/documents/{document_id}/versions/{version_id}"): GUARD_LOAD,
    ("GET", "/api/documents/{document_id}/access"): GUARD_LOAD,
    ("POST", "/api/documents/{document_id}/access"): GUARD_LOAD,
    ("POST", "/api/documents/{document_id}/access/{access_id}/revoke"): GUARD_LOAD,
    ("GET", "/api/documents/{document_id}/permissions"): GUARD_LOAD,
}


def router_routes() -> dict[tuple[str, str], object]:
    out = {}
    for route in doc_controller.router.routes:
        for method in sorted(route.methods - {"HEAD", "OPTIONS"}):
            out[(method, route.path)] = route.endpoint
    return out


def test_b1_dung_29_route_va_khong_route_nao_thieu_khai(vt):
    """Bản khai tay phải khớp router THẬT, cả hai chiều.

    Thêm một endpoint mà quên khai ở đây thì đỏ; xóa endpoint mà quên xóa dòng
    khai cũng đỏ. Không có bảng này thì hai ca dưới chỉ soi được những route mà
    người viết test tình cờ nhớ tới.
    """
    thuc_te = set(router_routes())
    assert len(thuc_te) == 29, f"router có {len(thuc_te)} route, bảng khai 29"
    assert thuc_te == set(ROUTE_GUARD), (
        f"lệch bảng khai: thừa {thuc_te - set(ROUTE_GUARD)}, "
        f"thiếu {set(ROUTE_GUARD) - thuc_te}")


def test_b2_moi_route_nhan_document_id_deu_phai_goi_load(vt):
    """🔒 LUẬT BẤT BIẾN — route có `{document_id}` thì **bắt buộc** đi qua `_load`.

    `_load` là chỗ duy nhất gọi `ensure_can` trong cả tệp controller. Một
    endpoint tự `db.get(Document, document_id)` sẽ chạy đúng, trả đúng dữ liệu,
    qua được `require(...)` — và bỏ qua sạch tầng 2: gõ id lên URL là mở được
    văn bản của pháp nhân khác, kể cả văn bản mình đang bị CẤM đích danh.

    Soi mã chứ không gọi: gọi đủ 21 endpoint phải dựng phiên bản, hộp thư, luồng
    duyệt… mà thứ cần khẳng định chỉ là "có đi qua cửa hay không".
    """
    thieu = []
    for (method, path), endpoint in router_routes().items():
        if "{document_id}" not in path:
            continue
        assert ROUTE_GUARD[(method, path)] == GUARD_LOAD, f"{method} {path} khai sai bảng"
        if "_load(" not in inspect.getsource(endpoint):
            thieu.append(f"{method} {path}")
    assert thieu == [], f"route nhận document_id nhưng không gọi `_load`: {thieu}"

    #  Và `_load` phải thật sự gọi `ensure_can` — nếu không thì luật trên rỗng nghĩa.
    assert "ensure_can" in inspect.getsource(doc_controller._load)


def test_b3_ba_route_danh_sach_deu_di_qua_visible_condition(vt):
    """Ba đường trả NHIỀU văn bản phải dùng chung một luật lọc.

    Danh sách và bản xuất Excel đi chung `_list_query` là có chủ ý (chép luật hai
    lần thì file Excel sớm muộn chứa văn bản người xuất không được xem);
    `/storage-locations` thì lọc riêng nhưng cùng bằng `visible_condition` — tên
    ngăn tủ của phòng Nhân sự cũng là một mẩu thông tin.
    """
    for (method, path), guard in ROUTE_GUARD.items():
        if guard != GUARD_VISIBLE:
            continue
        nguon = inspect.getsource(router_routes()[(method, path)])
        assert "_list_query" in nguon or "visible_condition" in nguon, f"{method} {path}"


def test_b4_goi_y_van_ban_khong_lo_tieu_de_ra_ngoai_pham_vi(vt):
    """Bài giữ của lỗ B4 — **đã vá 05/09/2026**.

    Trước bản vá, `GET /api/documents/suggestions` (`controller.py:186-196`) gọi
    thẳng `service.suggestions`, mà hàm đó **không nhận `user`** nên không lọc
    được kể cả muốn: nó chỉ lọc `origin` + `doc_type_id` + `status` + hai tham số
    do CHÍNH NGƯỜI GỌI truyền vào (`company_id`, `department_id`). Trả về `id`,
    **`title`** và **`display_code`** — đúng ba thứ `ensure_can` trả 404 để giấu (K03).

    Ai có `document.read` (kể cả phạm vi `own`) đều gọi được, và `company_id` là
    tham số tự do nên duyệt sạch 13 pháp nhân bằng 13 lượt gọi. Nặng nhất là loại
    bật `is_personal`: truyền id loại «Đơn nghỉ phép» ra thẳng tiêu đề đơn của
    từng người.

    Vá bằng cách bắt `suggestions` nhận `user`/`profile` (keyword **bắt buộc**,
    không có mặc định — nên không nơi gọi nào quên được) rồi lọc bằng chính
    `access_service.visible_condition`, tức dùng lại luật xem văn bản chứ không
    viết lại nó.
    """
    from app.modules.document import service as doc_service

    a1 = vt.world.grant("a1", "document", scope="own")
    prof = a1.profile()
    assert visible_ids(vt, a1) == pick(vt, "a_kt"), "phạm vi `own` chỉ thấy bản mình lập"

    #  Vẫn truyền `company_id` của pháp nhân B như kẻ tấn công sẽ làm.
    ro_ri = doc_service.suggestions(vt.db, vt.loai_qc.id, None, vt.world.co["B"],
                                    user=a1.user, profile=prof)
    assert ro_ri == [], "không còn lọt văn bản pháp nhân B qua tham số company_id tự do"

    #  Và tiêu đề đơn cá nhân — thứ `can()` chặn ở ca A9 — cũng phải im.
    don = doc_service.suggestions(vt.db, vt.loai_np.id, None, vt.world.co["B"],
                                  user=a1.user, profile=prof)
    assert don == []
    assert can(vt, a1, "ca_nhan_b") is False, "hai đường cùng nói một câu"


def test_b4b_goi_y_van_ban_van_chay_dung_trong_pham_vi(vt):
    """VẾ ĐỐI CHỨNG của B4 — thiếu nó thì bản vá trả `[]` cho tất cả cũng xanh.

    `suggestions` sinh ra để chống soạn trùng: người soạn phải thấy được văn bản
    cùng loại mà họ CÓ QUYỀN xem. Bịt lỗ mà giết luôn công dụng thì bản vá bị gỡ.
    """
    from app.modules.document import service as doc_service

    a1 = vt.world.grant("a1", "document", scope="own")
    trong_pham_vi = doc_service.suggestions(vt.db, vt.loai_qc.id, None, None,
                                            user=a1.user, profile=a1.profile())
    assert {row["id"] for row in trong_pham_vi} == pick(vt, "a_kt"), (
        "vẫn phải gợi ý đúng những bản thân mình xem được")


def test_b5_nhom_doc_go_thang_id_van_ban_ngoai_pham_vi_ra_404(vt):
    """Nhóm ĐỌC — chạy thật `GET /api/documents/{id}` và `/versions`.

    Đường vòng kinh điển: danh sách lọc đúng nhưng chi tiết quên kiểm, gõ id lên
    URL là mở được. Hai endpoint này còn dùng `doc_reader` (bỏ hẳn lớp
    `require`), nên `_load` là chốt chặn **duy nhất** của chúng.
    """
    a1 = vt.world.grant("a1", "document", scope="company")   # pháp nhân A

    with pytest.raises(HTTPException) as err:
        doc_controller.get_document(vt.doc["b_kt"].id, vt.db, a1.user)
    assert err.value.status_code == 404

    with pytest.raises(HTTPException) as err:
        doc_controller.list_versions(vt.doc["b_kt"].id, vt.db, a1.user)
    assert err.value.status_code == 404

    #  Vế đối chứng — trong phạm vi thì mở được, kẻo ca trên xanh vì lý do khác.
    mo_duoc = payload(doc_controller.get_document(vt.doc["a_kt"].id, vt.db, a1.user))
    assert mo_duoc["data"]["id"] == vt.doc["a_kt"].id


def test_b6_nhom_ghi_doc_duoc_khong_co_nghia_la_sua_duoc(vt):
    """Nhóm GHI — chạy thật `PATCH /api/documents/{id}`.

    Dựng đúng tổ hợp `access_service.can:359-371` sinh ra để bịt: một dòng chia
    sẻ **chỉ `can_read`** trên văn bản NGOÀI phạm vi. Đọc thì mở (404 → 200),
    ghi thì phải 403. Nếu `_load` gọi nhầm `action="read"` cho đường sửa thì ca
    này bắt được — mà đó chính là kiểu nhầm không màn hình nào lộ ra.
    """
    from app.modules.document.access_model import EFFECT_ALLOW
    from app.modules.document.schema import DocumentUpdate

    a1 = vt.world.grant("a1", "document", scope="company", actions=("read", "write"))
    share(vt, "b_kt", a1, effect=EFFECT_ALLOW, read=True, write=False)

    assert can(vt, a1, "b_kt", "read") is True
    with pytest.raises(HTTPException) as err:
        doc_controller.update_document(vt.doc["b_kt"].id,
                                       DocumentUpdate(title="Đổi tên"),
                                       vt.db, a1.user)
    assert err.value.status_code == 403
    assert vt.db.get(Document, vt.doc["b_kt"].id).title == "Văn bản B-KT"


def test_b7_nhom_ban_hanh_va_thu_hoi_chan_truoc_khi_lam_gi(vt):
    """Nhóm BAN HÀNH + THU HỒI — hai đường đổi trạng thái, chạy thật.

    Ban hành cấp SỐ HIỆU (không cấp lại được) và thu hồi giết một văn bản đang
    có hiệu lực. Cả hai phải chặn **trước** khi chạm vào dữ liệu, nên ca này
    khẳng định luôn trạng thái không đổi — chỉ bắt exception thì một bản vá đặt
    `_load` sau `service.approve` vẫn xanh.

    `approve` đi `_load(..., "read")` nên ra 404; `revoke` đi `_load(..., "write")`
    nên ra 403 khi đọc được nhưng không sửa được. Hai mã khác nhau là cố ý.
    """
    from app.modules.document.access_model import EFFECT_ALLOW
    from app.modules.document.schema import RejectIn

    a1 = vt.world.grant("a1", "document", scope="company",
                        actions=("read", "write", "approve", "cancel"))

    with pytest.raises(HTTPException) as err:
        doc_controller.approve_document(vt.doc["b_kt"].id, None, vt.db, a1.user)
    assert err.value.status_code == 404

    share(vt, "b_kt", a1, effect=EFFECT_ALLOW, read=True, write=False)
    with pytest.raises(HTTPException) as err:
        doc_controller.revoke_document(vt.doc["b_kt"].id, RejectIn(reason="thử"),
                                       vt.db, a1.user)
    assert err.value.status_code == 403

    assert vt.db.get(Document, vt.doc["b_kt"].id).status == STATUS_EFFECTIVE
    assert vt.db.get(Document, vt.doc["b_kt"].id).issue_number == ""


def test_b8_nhom_in_xuat_word_theo_dung_quyen_doc(vt):
    """Nhóm IN — `GET /{id}/export/docx` gác bằng `doc_reader` + `_load("read")`.

    Cố ý KHÔNG đòi quyền `export`: đó là quyền kéo cả DANH SÁCH ra ngoài, còn
    tải một bản Word là đúng thứ người dùng đang xem trên màn hình. Nghĩa là
    `_load` gánh toàn bộ, và chia đích danh phải mở được nó — nếu không thì
    người được chia tay xem được văn bản mà không in được.
    """
    from app.modules.document.access_model import EFFECT_ALLOW
    from app.modules.document.version_model import DocumentVersion

    ban = DocumentVersion(document_id=vt.doc["b_kt"].id, content_html="<p>Điều 1.</p>")
    vt.db.add(ban)
    vt.db.flush()
    vt.doc["b_kt"].current_version_id = ban.id
    vt.db.commit()

    a1 = vt.world.grant("a1", "document", scope="company")
    with pytest.raises(HTTPException) as err:
        doc_controller.export_docx(vt.doc["b_kt"].id, None, vt.db, a1.user)
    assert err.value.status_code == 404

    share(vt, "b_kt", a1, effect=EFFECT_ALLOW)
    tra_ve = doc_controller.export_docx(vt.doc["b_kt"].id, None, vt.db, a1.user)
    assert tra_ve.status_code == 200 and tra_ve.body


def test_b9_nhom_xuat_excel_va_danh_sach_ra_cung_mot_tap(vt):
    """Nhóm XUẤT — `GET /export/xlsx` và `GET ""` dùng chung `_list_query`.

    Khẳng định bằng TẬP ID, không bằng số dòng: xuất ra đúng số lượng nhưng lệch
    một văn bản thì đếm vẫn khớp. Bản Excel là thứ rời khỏi hệ thống rồi đi vào
    email, nên nó lệch danh sách một dòng là lộ hẳn một văn bản.
    """
    a1 = vt.world.grant("a1", "document", scope="company",
                        actions=("read", "export"))
    profile = a1.profile()

    danh_sach = payload(doc_controller.list_documents(
        make_request(), "", None, None, PAGE, vt.db, a1.user))
    hien = {row["id"] for row in danh_sach["data"]["items"]}
    assert hien == pick(vt, "a_kt", "a_mua", "mat_a")
    assert danh_sach["data"]["total"] == 3

    query, _ = doc_controller._list_query(make_request(), vt.db, a1.user, profile)
    assert {row.id for row in query.all()} == hien, "bản xuất Excel lệch danh sách"

    #  Tick tay id ngoài phạm vi cũng không kéo được nó ra (`ids=` chỉ THU HẸP).
    query, _ = doc_controller._list_query(make_request(), vt.db, a1.user, profile)
    query = query.filter(Document.id.in_([vt.doc["b_kt"].id]))
    assert query.all() == []


def test_b10_maintenance_activate_due_cham_toan_bang_khong_qua_pham_vi(vt):
    """🔶 Ghim hành vi: `POST /maintenance/activate-due` chạy trên **cả bảng**.

    `service.activate_due_versions(db)` không nhận `user` nên không có chỗ nào
    cho phạm vi chen vào. Không xếp là lỗ **đọc**: nó chỉ chuyển phiên bản đã
    duyệt sang hiệu lực khi tới ngày, không trả dữ liệu văn bản nào ra ngoài, và
    endpoint chi tiết cũng tự chạy phần của mình. Nhưng nó là một thao tác GHI
    trên văn bản của mọi pháp nhân, mở cho bất kỳ ai có `document.approve`.

    # QUYẾT ĐỊNH CHỜ: endpoint này có nên bó theo phạm vi của người gọi, hay
    # chuyển hẳn thành việc chạy nền (cron) và bỏ khỏi API?
    """
    nguon = inspect.getsource(doc_controller.activate_due)
    assert "_load" not in nguon and "visible_condition" not in nguon
    assert "get_perm_profile" not in nguon
    assert "activate_due_versions(db)" in nguon, "không nhận tham số lọc nào"


# ══════════════════════════════════════════════════════════════════════════════
#  C. Bình luận — 7 route, 0 `require`, 0 `apply_scope` **trên giấy**
# ══════════════════════════════════════════════════════════════════════════════
#
#  Soi mã rồi: KHÔNG phải lỗ. Cả 7 route đi qua `service.resolve_doc`
#  (`comment/service.py:46-103`) và hàm đó làm đủ hai tầng — `user_has_permission`
#  rồi `apply_scope` trên CHỨNG TỪ CHA. Việc ở đây là GHIM, không phải vá.
#
#  ⚠️ `document` KHÔNG nằm trong `COMMENT_POLICY` — văn bản không có ô bình luận.
#  Nên nhóm C dựng trên YCMH, đúng như chạy thật.


@pytest.fixture()
def pyc(world):
    """Hai phiếu YCMH: một của pháp nhân A, một của B, kèm một bình luận sẵn."""
    from app.modules.comment.model import Comment
    from app.modules.purchase_request.model import PurchaseRequest

    db = world.db
    a = PurchaseRequest(code="PYC-A", company_id=world.co["A"],
                        department_id=world.dept["A.kt"], status="draft",
                        created_by=world.actor("a1").user.id)
    b = PurchaseRequest(code="PYC-B", company_id=world.co["B"],
                        department_id=world.dept["B.kt"], status="draft",
                        created_by=world.actor("b1").user.id)
    db.add_all([a, b])
    db.flush()
    cua_b1 = Comment(entity="purchase_request", entity_id=b.id, body="của b1",
                     parent_id=0, created_by=world.actor("b1").user.id)
    cua_a1 = Comment(entity="purchase_request", entity_id=a.id, body="của a1",
                     parent_id=0, created_by=world.actor("a1").user.id)
    db.add_all([cua_b1, cua_a1])
    db.commit()
    return SimpleNamespace(db=db, world=world, a=a, b=b,
                           cmt_b1=cua_b1, cmt_a1=cua_a1)


def test_c1_doc_binh_luan_cua_chung_tu_ngoai_pham_vi_bi_chan(pyc):
    """C1 — `GET /api/comments` chỉ đòi đăng nhập; chốt chặn nằm trong thân hàm.

    Ghim đủ hai vế trên cùng một người: phiếu A mở được, phiếu B thì 403. Chỉ
    khẳng định vế chặn thì một `resolve_doc` chặn tất cũng xanh.
    """
    from app.modules.comment import controller as cc

    a1 = pyc.world.grant("a1", "purchase_request", scope="company")
    thay = payload(cc.list_comments("purchase_request", pyc.a.id, 10, 0, pyc.db, a1.user))
    assert [row["id"] for row in thay["data"]["items"]] == [pyc.cmt_a1.id]

    with pytest.raises(HTTPException) as err:
        cc.list_comments("purchase_request", pyc.b.id, 10, 0, pyc.db, a1.user)
    assert err.value.status_code == 403


def test_c2_ghi_binh_luan_vao_chung_tu_ngoai_pham_vi_bi_chan(pyc):
    """C2 — chiều GHI phải chặn ngang chiều đọc.

    Chặn mỗi lượt đọc là vẫn cho người ta nhét bình luận (kèm tệp) vào phiếu của
    pháp nhân khác, và người trong phiếu đó nhận chuông từ một người lạ. Khẳng
    định luôn là bảng không mọc thêm dòng nào.
    """
    from app.modules.comment import controller as cc
    from app.modules.comment.model import Comment
    from app.modules.comment.schema import CommentIn
    from fastapi import BackgroundTasks

    a1 = pyc.world.grant("a1", "purchase_request", scope="company")
    truoc = pyc.db.query(Comment).count()

    with pytest.raises(HTTPException) as err:
        cc.create_comment(CommentIn(entity="purchase_request", entity_id=pyc.b.id,
                                    body="chen ngang"),
                          BackgroundTasks(), pyc.db, a1.user)
    assert err.value.status_code == 403
    assert pyc.db.query(Comment).count() == truoc


def test_c3_xoa_binh_luan_cua_nguoi_khac_bi_chan(pyc):
    """C3 — trong phạm vi vẫn không xóa được bài của người khác.

    Hai chốt khác nhau, đừng nhầm: `resolve_doc` hỏi "phiếu này của anh không",
    còn `controller.py:220` hỏi "bài này của anh không". Ca này đi qua chốt thứ
    nhất (a1 thấy phiếu A) để bắt đúng chốt thứ hai.

    Ngoại lệ `user.delete` là cố ý — quản trị phải dọn được nội dung không phù hợp.
    """
    from app.modules.comment import controller as cc
    from app.modules.comment.model import Comment

    #  Giữ lại id trước khi xóa: `delete_comment` commit xong thì đối tượng ORM
    #  hết hạn, đọc `.id` sau đó là một lượt SELECT vào dòng không còn nữa.
    cid = pyc.cmt_a1.id

    #  a2 thấy cả phiếu A, nhưng bình luận trên đó là của a1.
    a2 = pyc.world.grant("a2", "purchase_request", scope="company")
    with pytest.raises(HTTPException) as err:
        cc.delete_comment(cid, pyc.db, a2.user)
    assert err.value.status_code == 403
    assert pyc.db.get(Comment, cid) is not None

    #  Chính chủ thì xóa được.
    a1 = pyc.world.grant("a1", "purchase_request", scope="company")
    cc.delete_comment(cid, pyc.db, a1.user)
    assert pyc.db.get(Comment, cid) is None


def test_c4_moi_entity_binh_luan_duoc_deu_phai_co_duong_kiem_pham_vi():
    """🔒 C4 — LUẬT BẤT BIẾN, cùng khuôn `test_pham_vi_dinh_kem_b08.py`.

    `COMMENT_POLICY` mở bình luận cho một entity bằng **một dòng**. Nhưng phần
    kiểm phạm vi thì không tự có: `resolve_doc` chỉ chạy được `apply_scope` khi
    `doc_model(entity)` trả về một model, và `apply_scope` chỉ lọc thật khi
    entity cha KHÔNG khai `PUBLIC` ở `SCOPE_FIELDS`.

    Nên có đúng hai cách hợp lệ, và mọi entity phải rơi vào một trong hai:
      (a) có model + entity cha lọc thật → đi đường chung;
      (b) entity cha khai `PUBLIC` → **bắt buộc** có nhánh riêng trong
          `resolve_doc` (hôm nay: `forum_post` theo audience của bài,
          `work_task` theo tư cách thành viên).

    Thêm một dòng vào `COMMENT_POLICY` trỏ vào entity `PUBLIC` mà quên nhánh
    riêng thì `apply_scope` không thêm mệnh đề nào — ai đăng nhập và có quyền
    vai trò là bình luận được vào bản ghi của người khác, im lặng. Ca này bắt
    đúng lúc dòng đó được thêm.
    """
    from app.core.comment_registry import COMMENT_POLICY, doc_model
    from app.core.scoping import PUBLIC, SCOPE_FIELDS
    from app.modules.comment.service import resolve_doc

    than_ham = inspect.getsource(resolve_doc)
    thieu_model, thieu_nhanh, chua_khai = [], [], []
    for entity, (parent, _, _) in COMMENT_POLICY.items():
        if doc_model(entity) is None:
            thieu_model.append(entity)
        if parent not in SCOPE_FIELDS:
            chua_khai.append(parent)
        elif SCOPE_FIELDS[parent] is PUBLIC and f'"{entity}"' not in than_ham:
            thieu_nhanh.append(entity)

    assert thieu_model == [], f"entity bình luận không có model để soi phạm vi: {thieu_model}"
    assert chua_khai == [], f"entity cha chưa khai trong SCOPE_FIELDS: {chua_khai}"
    assert thieu_nhanh == [], (
        f"entity cha khai PUBLIC nhưng `resolve_doc` không có nhánh riêng: {thieu_nhanh}")


def test_c4b_entity_khong_khai_thi_tu_choi_ngay_chu_khong_bo_qua(pyc):
    """Vế còn lại của C4: entity lạ phải **400**, không phải "chạy tiếp".

    `document` là ví dụ sống — văn bản không có ô bình luận, và nếu `resolve_doc`
    bỏ qua entity lạ thay vì từ chối thì đây là đường vòng bỏ qua cả hai tầng
    quyền của phân hệ Văn thư.
    """
    from app.modules.comment.service import resolve_doc

    a1 = pyc.world.grant("a1", "purchase_request", scope="all")
    for entity in ("document", "khong-co-that"):
        with pytest.raises(HTTPException) as err:
            resolve_doc(pyc.db, a1.user, entity, 1)
        assert err.value.status_code == 400, entity


# ══════════════════════════════════════════════════════════════════════════════
#  D. Danh mục Văn thư — sáu khóa PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

DOC_CATALOG_KEYS = ("doc_type", "doc_template", "doc_numbering_rule",
                    "doc_link_rule", "security_level", "external_party")


def test_d1_quyen_tren_mot_khoa_khong_keo_theo_khoa_danh_muc_khac(vt):
    """D1 — tách sáu khóa (CR-157) là để phân quyền THEO MÀN HÌNH.

    Tách rồi mà `user_has_permission` gộp lại thì việc tách thành trang trí:
    người được giao khai quy tắc cấp số sẽ sửa được luôn danh mục Loại văn bản —
    mà `doc_type` quyết định cách cấp số, mức mật mặc định và cờ `is_personal`.

    Vế cuối là chốt "không chặn nhầm": khóa được cấp thì phải chạy, nếu không ca
    này xanh chỉ vì mọi thứ đều bị chặn.
    """
    from app.core.auth import user_has_permission

    a1 = vt.world.grant("a1", "doc_numbering_rule", scope="all",
                        actions=("read", "write"))
    for khoa in DOC_CATALOG_KEYS:
        if khoa == "doc_numbering_rule":
            continue
        assert not user_has_permission(vt.db, a1.user, khoa, "write"), khoa
        assert not user_has_permission(vt.db, a1.user, khoa, "read"), khoa

    assert user_has_permission(vt.db, a1.user, "doc_numbering_rule", "write")


def test_d2_bon_o_pham_vi_tren_sau_khoa_danh_muc_deu_vo_hieu(vt):
    """D2 — cả sáu khóa khai `PUBLIC`, nên năm ô phạm vi là trang trí.

    Nối với nghi ngờ 2 của cụm 01 (`test_b4_...`): người khai quyền tick đủ bốn
    ô, bấm Lưu, nhận «Đã lưu phạm vi» — và không có gì thay đổi. Đây KHÔNG phải
    lỗi của `scoping.py` (danh mục Văn thư dùng chung mọi pháp nhân, cố ý), mà là
    lỗ hổng của MÀN HÌNH: nó không nói ra.

    Khẳng định trên dữ liệu THẬT (`tab_doc_type` có 2 dòng từ fixture) chứ không
    chỉ đọc `SCOPE_FIELDS` — bảng khai đúng mà `_role_scope_cond` xử sai thì đọc
    bảng không bắt được.

    # QUYẾT ĐỊNH CHỜ: hộp thoại «Phạm vi — <vai trò>» có nên tắt/ẩn năm ô kèm
    # câu "Danh mục này dùng chung mọi pháp nhân" cho entity PUBLIC?
    """
    from app.core.scoping import PUBLIC, SCOPE_FIELDS
    from app.modules.doc_catalog.model import DocType

    for khoa in DOC_CATALOG_KEYS:
        assert SCOPE_FIELDS[khoa] is PUBLIC, khoa

    tat_ca = {row.id for row in vt.db.query(DocType).all()}
    assert tat_ca == {vt.loai_qc.id, vt.loai_np.id}, "phải có dữ liệu thật rồi mới khẳng định"

    a1 = vt.world.grant("a1", "doc_type", scope="own", inc_company=["A"],
                        inc_dept=["A.kt"], exc_dept=["A.kt"],
                        inc_employee=["a2"], exc_employee=["a3"])
    assert a1.sees(DocType, "doc_type") == tat_ca


def test_d3_sau_khoa_danh_muc_van_ban_deu_nam_trong_bang_quyen(vt):
    """Chốt cái danh sách sáu khóa ở trên, kẻo nó lệch `ENTITIES` lúc nào không hay.

    B-07 đã ràng `ENTITIES == SCOPE_FIELDS`; ở đây ràng thêm rằng sáu khóa mà
    hai ca trên nói tới đúng là sáu khóa đang tồn tại — đổi tên một khóa mà quên
    tệp này thì hai ca kia lặng lẽ kiểm một khóa không ai dùng.
    """
    from app.core.permissions import ENTITIES

    thieu = [k for k in DOC_CATALOG_KEYS if k not in ENTITIES]
    assert thieu == [], f"khóa khai ở tệp test nhưng không có trong ENTITIES: {thieu}"
