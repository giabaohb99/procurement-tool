"""B-08 (N-13) — TỆP ĐÍNH KÈM PHẢI LỌC THEO PHẠM VI DỮ LIỆU.

Lỗ hổng đã có: `attachment/controller._check()` chỉ hỏi `user_has_permission` trên
entity CHA, không hỏi bản ghi cha đó có nằm trong phạm vi của người này không. Ai có
`contract.read` phạm vi `company` vẫn tải được đính kèm hợp đồng của pháp nhân khác,
chỉ cần đoán đúng `entity_id` (hoặc đúng `link_id` ở lối tải một tệp). Chung cho cả
mười loại chứng từ.

Bài này chốt bốn tầng:

```
tra chứng từ cha  →  entity treo vào DÒNG phải lần ngược ra phiếu (không nhận id dòng là id phiếu)
tầng lọc          →  _check(..., entity_id) sinh ra 403 khi phiếu cha ngoài phạm vi
đường lùi chuỗi   →  tải lẻ một tệp trong chuỗi PO → PYC → PKS → YCKS vẫn chạy
không chặn nhầm   →  tải tệp TẠM (chưa gắn) và `__self__` không có gì để soi
```

Gọi thẳng hàm chứ không qua HTTP: nhắm vào mệnh đề WHERE và nhánh 403, đi vòng qua
TestClient chỉ thêm lớp xác thực không liên quan.
"""
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core import attachment_scope as asc
from app.core.file_registry import FILE_POLICY
from app.modules.attachment import controller as ac
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.contract.model import Contract
from app.modules.purchase_order.model import PODelivery, PurchaseOrder
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey.model import Survey
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine

USER_ID = 10
CTY_A, CTY_B = 101, 202

_ACTIONS = ("read", "create", "write", "delete", "approve", "cancel", "print", "export")


def _profile(entities, scope="company", company_id=CTY_A):
    """Hồ sơ quyền tối thiểu, đúng hình dạng `get_perm_profile` trả về."""
    perms = {}
    for e in entities:
        perms[e] = {a: True for a in _ACTIONS} | {"scope": scope}
    return {
        "grants": [{"role_id": 1, "perms": perms, "scope": {"inc": {}, "exc": {}}}],
        "company_id": company_id, "dept_id": 0, "dept_name": "",
        "employee_id": 0, "emp_code": "", "emp_name": "",
    }


@pytest.fixture
def nguoi_dung(monkeypatch):
    """Đặt hồ sơ quyền và MỞ SẴN lớp vai trò.

    `user_has_permission` đọc DB và có bộ đệm 60s; lớp vai trò không phải thứ bài
    này nhắm tới — trừ đúng một bài khẳng định nó vẫn còn nguyên.
    """
    def _dat(profile, co_quyen_vai_tro=True):
        monkeypatch.setattr(asc, "get_perm_profile", lambda db, user: profile)
        monkeypatch.setattr(ac, "get_perm_profile", lambda db, user: profile)
        monkeypatch.setattr(asc, "user_has_permission",
                            lambda db, user, entity, action: co_quyen_vai_tro)
        monkeypatch.setattr(ac, "user_has_permission",
                            lambda db, user, entity, action: co_quyen_vai_tro)
        return SimpleNamespace(id=USER_ID, employee_id=0)
    return _dat


@pytest.fixture
def du_lieu(db):
    """Hai pháp nhân, mỗi bên một bộ chứng từ; chuỗi PO-A → PYC-A → PKS-A → YCKS-A."""
    ycks_a = SurveyRequest(code="YCKS-A", company_id=CTY_A, created_by=99)
    ycks_b = SurveyRequest(code="YCKS-B", company_id=CTY_B, created_by=99)
    db.add_all([ycks_a, ycks_b])
    db.flush()
    dong_a = SurveyRequestLine(survey_request_id=ycks_a.id, item_group="Nhãn")
    dong_b = SurveyRequestLine(survey_request_id=ycks_b.id, item_group="Nhãn")
    pyc_a = PurchaseRequest(code="PYC-A", company_id=CTY_A, created_by=99)
    pyc_b = PurchaseRequest(code="PYC-B", company_id=CTY_B, created_by=99)
    pks_a = Survey(code="PKS-A", survey_type="product", sr_code="YCKS-A", created_by=99)
    hd_a = Contract(code="HD-A", company_id=CTY_A, title="Hợp đồng A", created_by=99)
    hd_b = Contract(code="HD-B", company_id=CTY_B, title="Hợp đồng B", created_by=99)
    db.add_all([dong_a, dong_b, pyc_a, pyc_b, pks_a, hd_a, hd_b])
    db.flush()
    po_a = PurchaseOrder(code="PO-A", company_id=CTY_A, pr_code="PYC-A",
                         survey_code="PKS-A", created_by=99)
    po_b = PurchaseOrder(code="PO-B", company_id=CTY_B, pr_code="PYC-B", created_by=99)
    db.add_all([po_a, po_b])
    db.flush()
    giao_a = PODelivery(po_id=po_a.id, po_item_id=0)
    giao_b = PODelivery(po_id=po_b.id, po_item_id=0)
    db.add_all([giao_a, giao_b])
    db.commit()
    return SimpleNamespace(db=db, ycks_a=ycks_a, ycks_b=ycks_b, dong_a=dong_a, dong_b=dong_b,
                           pyc_a=pyc_a, pyc_b=pyc_b, pks_a=pks_a, hd_a=hd_a, hd_b=hd_b,
                           po_a=po_a, po_b=po_b, giao_a=giao_a, giao_b=giao_b)


def _doc(db, user, entity, entity_id, mode="read"):
    return ac._check(db, user, entity, mode, entity_id)


# ── Tra chứng từ cha ────────────────────────────────────────────────────────────
def test_moi_loai_dinh_kem_deu_tra_duoc_chung_tu_cha(db):
    """Thêm dòng vào `FILE_POLICY` mà quên khai bộ tra ở đây = mở lại đúng lỗ N-13.

    Ba loại `__self__` (`avatar`, `comment`) và văn bản đi nhánh riêng nên trừ ra.
    """
    thieu = [e for e, (parent, _, _) in FILE_POLICY.items()
             if parent not in ("__self__", "document")
             and asc.parent_records(db, e, 1)[0] is None]
    assert thieu == []


def test_dinh_kem_theo_dong_lan_nguoc_ra_phieu_chu_khong_nhan_id_dong(du_lieu):
    """`entity_id` của `survey_request_line` là id DÒNG. Coi nó là id phiếu là soi nhầm phiếu."""
    model, ids = asc.parent_records(du_lieu.db, "survey_request_line", du_lieu.dong_b.id)
    assert model is SurveyRequest
    assert ids == [du_lieu.ycks_b.id]

    model, ids = asc.parent_records(du_lieu.db, "delivery", du_lieu.giao_b.id)
    assert model is PurchaseOrder
    assert ids == [du_lieu.po_b.id]


def test_survey_line_mo_ho_thi_tra_ca_hai_kha_nang(db):
    """`survey_line` không nói rõ dòng NCC hay dòng sản phẩm, mà hai bảng đánh id riêng."""
    from app.modules.survey.model import SurveyProductLine, SurveySupplierLine

    ks1 = Survey(code="KS-1", survey_type="product", created_by=1)
    ks2 = Survey(code="KS-2", survey_type="supplier", created_by=1)
    db.add_all([ks1, ks2])
    db.flush()
    ncc = SurveySupplierLine(survey_id=ks1.id, supplier_name="NCC")
    sp = SurveyProductLine(survey_id=ks2.id, product_name="SP")
    db.add_all([ncc, sp])
    db.commit()
    #  Hai dòng cùng mang id 1 ở hai bảng khác nhau — phải soi cả hai phiếu.
    assert ncc.id == sp.id == 1
    _, ids = asc.parent_records(db, "survey_line", 1)
    assert sorted(ids) == sorted([ks1.id, ks2.id])


# ── Tầng lọc ────────────────────────────────────────────────────────────────────
def test_dinh_kem_hop_dong_phap_nhan_khac_bi_chan(du_lieu, nguoi_dung):
    """Chính lỗ N-13: có `contract.read` phạm vi `company` là tải được của pháp nhân khác."""
    user = nguoi_dung(_profile(["contract"], scope="company", company_id=CTY_A))
    with pytest.raises(HTTPException) as e:
        _doc(du_lieu.db, user, "contract", du_lieu.hd_b.id)
    assert e.value.status_code == 403


def test_dinh_kem_hop_dong_phap_nhan_minh_van_mo_duoc(du_lieu, nguoi_dung):
    user = nguoi_dung(_profile(["contract"], scope="company", company_id=CTY_A))
    assert _doc(du_lieu.db, user, "contract", du_lieu.hd_a.id)


def test_dinh_kem_theo_dong_ngoai_pham_vi_bi_chan(du_lieu, nguoi_dung):
    """59/92 đính kèm trên dev là `survey_request_line` — đường vào lớn nhất của lỗ này."""
    user = nguoi_dung(_profile(["survey_request"], scope="company", company_id=CTY_A))
    with pytest.raises(HTTPException) as e:
        _doc(du_lieu.db, user, "survey_request_line", du_lieu.dong_b.id)
    assert e.value.status_code == 403
    assert _doc(du_lieu.db, user, "survey_request_line", du_lieu.dong_a.id)


def test_gan_them_tep_vao_phieu_ngoai_pham_vi_cung_bi_chan(du_lieu, nguoi_dung):
    """Chặn mỗi lượt ĐỌC là vẫn cho người ta nhét tệp vào phiếu của pháp nhân khác."""
    user = nguoi_dung(_profile(["purchase_order"], scope="company", company_id=CTY_A))
    with pytest.raises(HTTPException) as e:
        _doc(du_lieu.db, user, "delivery", du_lieu.giao_b.id, mode="manage")
    assert e.value.status_code == 403


def test_pham_vi_tat_ca_van_thay_het(du_lieu, nguoi_dung):
    """Cấu hình đang chạy thật của phần lớn vai trò — bản vá không được đổi hành vi hôm nay."""
    user = nguoi_dung(_profile(["contract", "survey_request"], scope="all"))
    assert _doc(du_lieu.db, user, "contract", du_lieu.hd_b.id)
    assert _doc(du_lieu.db, user, "survey_request_line", du_lieu.dong_b.id)


def test_quyen_vai_tro_van_chan_truoc_nhu_cu(du_lieu, nguoi_dung):
    """Lớp cũ phải còn nguyên: hết quyền vai trò là 403 ngay, không cần soi phạm vi."""
    user = nguoi_dung(_profile(["contract"], scope="all"), co_quyen_vai_tro=False)
    with pytest.raises(HTTPException) as e:
        _doc(du_lieu.db, user, "contract", du_lieu.hd_a.id)
    assert e.value.status_code == 403


def test_chung_tu_cha_khong_con_thi_404_chu_khong_phai_403(du_lieu, nguoi_dung):
    """Phân biệt 'gõ nhầm id' với 'có nhưng ngoài phạm vi' — gộp thành 403 hết là khó dùng."""
    user = nguoi_dung(_profile(["survey_request"], scope="all"))
    with pytest.raises(HTTPException) as e:
        _doc(du_lieu.db, user, "survey_request_line", 999999)
    assert e.value.status_code == 404


# ── Không chặn nhầm ─────────────────────────────────────────────────────────────
def test_tai_tep_tam_chua_gan_vao_dau_thi_khong_soi_pham_vi(du_lieu, nguoi_dung):
    """`POST /upload-file` gọi `_check` KHÔNG kèm `entity_id` — chưa có bản ghi nào để soi."""
    user = nguoi_dung(_profile(["contract"], scope="company", company_id=CTY_A))
    assert ac._check(du_lieu.db, user, "contract", "manage")


def test_o_khong_co_chung_tu_cha_thi_khong_soi_pham_vi(du_lieu, nguoi_dung):
    """`__self__` — không có chứng từ cha nào để soi, nên `_check` đi thẳng.

    Đại diện là `comment`: bình luận treo được vào NHIỀU loại chứng từ nên không
    có một entity cha cố định; quyền thật do API bình luận quyết
    (`comment/service.resolve_doc`), `__self__` ở đây chỉ mở bước tải tệp.

    ⚠️ Bài này trước dùng `avatar` và đỏ từ lúc ảnh đại diện được gỡ khỏi
    `FILE_POLICY` (nó lưu thẳng `tab_user.avatar_file_id`, không qua `FileLink`).
    Xem `test_anh_dai_dien_KHONG_phai_mot_o_dinh_kem` ở `test_attachment_ext.py`.
    """
    user = nguoi_dung(_profile([], scope="company"))
    assert ac._check(du_lieu.db, user, "comment", "manage", 12345)


# ── Đường lùi theo chuỗi chứng từ ───────────────────────────────────────────────
def test_tep_pyc_ngoai_pham_vi_nhung_thuoc_don_minh_xem_duoc_thi_tai_duoc(du_lieu, nguoi_dung):
    """Trang «Chứng từ» liệt kê cả chuỗi rồi cho tải từng dòng.

    `chain/zip` đã cho tải TRỌN chuỗi cho bất kỳ ai mở được đơn, nên đường lùi này
    không nới thêm gì — chỉ thay 'tải cả gói' bằng 'tải lẻ'.
    """
    user = nguoi_dung(_profile(["purchase_order", "purchase_request"],
                               scope="own", company_id=CTY_A))
    #  Phạm vi `own` mà PYC-A do người khác lập → soi thẳng là ngoài phạm vi…
    with pytest.raises(HTTPException):
        _doc(du_lieu.db, user, "purchase_request", du_lieu.pyc_a.id)
    #  …nhưng đơn PO-A thì mở được, nên tệp PYC-A trong chuỗi vẫn tải lẻ được.
    du_lieu.po_a.created_by = USER_ID
    du_lieu.db.commit()
    assert asc.reachable_from_scoped_po(du_lieu.db, user, "purchase_request", du_lieu.pyc_a.id)


def test_duong_lui_lan_hai_chang_tu_ycks_qua_phieu_khao_sat(du_lieu, nguoi_dung):
    """YCKS → PKS → ĐMH: thiếu chặng giữa là dòng YCKS trong chuỗi bấm vào 403."""
    user = nguoi_dung(_profile(["purchase_order", "survey_request"],
                               scope="own", company_id=CTY_A))
    du_lieu.po_a.created_by = USER_ID
    du_lieu.db.commit()
    assert asc.reachable_from_scoped_po(du_lieu.db, user, "survey_request_line", du_lieu.dong_a.id)


def test_duong_lui_khong_mo_cho_tep_khong_thuoc_don_nao_minh_xem_duoc(du_lieu, nguoi_dung):
    user = nguoi_dung(_profile(["purchase_order", "purchase_request"],
                               scope="company", company_id=CTY_A))
    assert not asc.reachable_from_scoped_po(du_lieu.db, user, "purchase_request", du_lieu.pyc_b.id)


def test_duong_lui_khong_ap_cho_hop_dong(du_lieu, nguoi_dung):
    """Hợp đồng không nằm trong chuỗi chứng từ của đơn — không có cửa nào lùi."""
    user = nguoi_dung(_profile(["purchase_order", "contract"], scope="all"))
    assert not asc.reachable_from_scoped_po(du_lieu.db, user, "contract", du_lieu.hd_b.id)


def test_tai_mot_tep_hop_dong_ngoai_pham_vi_van_403_du_co_duong_lui(du_lieu, nguoi_dung, monkeypatch):
    """Đường lùi gắn vào `download_one` không được nuốt mất nhánh chặn."""
    monkeypatch.setattr(ac, "download_bytes", lambda key: b"x")
    user = nguoi_dung(_profile(["contract", "purchase_order"], scope="company", company_id=CTY_A))
    f = StoredFile(filename="a.pdf", file_key="k", url="u", content_type="application/pdf",
                   size=1, sha256="s")
    du_lieu.db.add(f)
    du_lieu.db.flush()
    lk = FileLink(file_id=f.id, entity="contract", entity_id=du_lieu.hd_b.id,
                  doc_type="", sort_order=0)
    du_lieu.db.add(lk)
    du_lieu.db.commit()

    with pytest.raises(HTTPException) as e:
        ac.download_one(lk.id, du_lieu.db, user)
    assert e.value.status_code == 403


def test_tai_mot_tep_trong_pham_vi_van_chay(du_lieu, nguoi_dung, monkeypatch):
    monkeypatch.setattr(ac, "download_bytes", lambda key: b"noi dung")
    user = nguoi_dung(_profile(["contract"], scope="company", company_id=CTY_A))
    f = StoredFile(filename="a.pdf", file_key="k", url="u", content_type="application/pdf",
                   size=1, sha256="s")
    du_lieu.db.add(f)
    du_lieu.db.flush()
    lk = FileLink(file_id=f.id, entity="contract", entity_id=du_lieu.hd_a.id,
                  doc_type="", sort_order=0)
    du_lieu.db.add(lk)
    du_lieu.db.commit()

    assert ac.download_one(lk.id, du_lieu.db, user).body == b"noi dung"


# ── Văn bản: đi `access_service`, không đi `apply_scope` ───────────────────────
@pytest.fixture
def van_ban(db, seed):
    """Một văn bản của phòng `seed`, kèm phiên bản đầu — `entity_id` là id PHIÊN BẢN."""
    from app.modules.company.model import Company
    from app.modules.doc_catalog.model import DocType
    from app.modules.document import service as ds
    from app.modules.document.schema import DocumentCreate
    from app.modules.document.version_model import DocumentVersion

    db.get(Company, seed.company_id).issue_code = "DEGO"
    loai = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(loai)
    db.commit()
    doc = ds.create_document(db, DocumentCreate(
        doc_type_id=loai.id, company_id=seed.company_id, department_id=seed.dept_id,
        owner_employee_id=seed.emp_req_id, title="Quy chế lương",
        content_html="<p>Mật</p>",
    ), 99)
    ver = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).one()
    return SimpleNamespace(db=db, doc=doc, ver=ver, seed=seed)


def _ho_so_van_ban(employee_id=0, scope="own"):
    perms = {a: True for a in _ACTIONS} | {"scope": scope}
    return {"grants": [{"role_id": 1, "perms": {"document": perms},
                        "scope": {"inc": {}, "exc": {}}}],
            "company_id": 0, "dept_id": 0, "dept_name": "",
            "employee_id": employee_id, "emp_code": "", "emp_name": ""}


def test_dinh_kem_van_ban_ngoai_pham_vi_tra_404_chu_khong_403(van_ban, nguoi_dung):
    """K03: 403 là đã xác nhận 'có văn bản này, anh không được xem' — riêng nó đã lộ tin."""
    user = nguoi_dung(_ho_so_van_ban(employee_id=van_ban.seed.emp_tp_id, scope="own"))
    with pytest.raises(HTTPException) as e:
        _doc(van_ban.db, user, "document_version", van_ban.ver.id)
    assert e.value.status_code == 404


def test_dinh_kem_van_ban_chia_se_dich_danh_van_mo_duoc(van_ban, nguoi_dung):
    """Lý do nhánh văn bản KHÔNG dùng `apply_scope`.

    Chia sẻ đích danh và thành viên sổ là quyền CỘNG THÊM, nằm ngoài phạm vi vai
    trò. `apply_scope` chỉ biết thu hẹp — dùng nó ở đây là cắt đúng những người
    vừa được chia tay.
    """
    from app.modules.document.access_model import (EFFECT_ALLOW,
                                                   SUBJECT_EMPLOYEE,
                                                   DocumentAccess)

    van_ban.db.add(DocumentAccess(
        document_id=van_ban.doc.id, subject_kind=SUBJECT_EMPLOYEE,
        subject_id=van_ban.seed.emp_tp_id, effect=EFFECT_ALLOW, can_read=True))
    van_ban.db.commit()

    user = nguoi_dung(_ho_so_van_ban(employee_id=van_ban.seed.emp_tp_id, scope="own"))
    user.employee_id = van_ban.seed.emp_tp_id
    assert _doc(van_ban.db, user, "document_version", van_ban.ver.id)


def test_dinh_kem_van_ban_phien_ban_khong_ton_tai_thi_404(van_ban, nguoi_dung):
    user = nguoi_dung(_ho_so_van_ban(scope="all"))
    with pytest.raises(HTTPException) as e:
        _doc(van_ban.db, user, "document_version", 999999)
    assert e.value.status_code == 404


# ── Chuỗi chứng từ: câu import chết từ CR-007/008 ───────────────────────────────
def test_chuoi_chung_tu_khong_con_no_importerror(du_lieu, nguoi_dung):
    """`_resolve_chain` import `PurchaseOrderItem` — lớp thật tên `POItem`.

    Câu import sai nằm TRONG hàm nên không lộ lúc khởi động: cả `/chain` lẫn
    `/chain/zip` trả 500 mọi lượt gọi, từ CR-007/008 tới lúc B-08 bắt được.
    """
    user = nguoi_dung(_profile(["purchase_order"], scope="all"))
    po, groups = ac._resolve_chain(du_lieu.db, user, "purchase_order", du_lieu.po_a.id)
    assert po.code == "PO-A"
    #  Chuỗi phải lần đủ ba chặng theo mã, không dừng ở mỗi cái đơn.
    nguon = {ent for ent, _, _, _ in groups}
    assert {"purchase_order", "delivery", "purchase_request", "survey",
            "survey_request"} <= nguon
