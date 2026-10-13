"""ai-CR-177 — đợt 2b xóa MỀM cho cụm Văn thư / Nhân sự: Hợp đồng NCC · Văn bản (bản nháp) ·
Hợp đồng lao động · Hồ sơ (qua CRUD chung). Nền: `SoftDeleteMixin` + lọc tập trung ở
`core/scoping` (ai-CR-170); văn bản thêm cửa chung `document/query.documents_query`.

Mỗi chứng từ kiểm cùng một bộ:
  1. xóa → còn trong DB với cờ + mốc + người xóa; dòng con / tệp / phiên bản / quan hệ GIỮ;
  2. biến khỏi danh sách · chi tiết · cảnh báo / báo cáo · tool Trợ lý;
  3. xóa lần hai 404; luật trạng thái cũ vẫn chặn (400 / 409);
  4. mã không tái dùng;
  5. CRUD chung rẽ đúng: model có `is_deleted` thì đánh cờ, model không có vẫn xóa cứng.
"""
import json
from datetime import date, datetime, timedelta

import pytest
from fastapi import HTTPException
from starlette.datastructures import QueryParams

from app.core.auth import get_perm_profile
from app.core.config import settings as core_settings
from app.core.crud import remove_or_mark_deleted
from app.core.utils import generate_code
from app.modules.assistant.tools.base import ToolContext
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.contract import controller as contract_ctl
from app.modules.contract.model import Contract
from app.modules.dossier import service as dossier_service
from app.modules.dossier.depends_service import check_depends, depends_names
from app.modules.dossier.model import Dossier
from app.modules.dossier.type_model import DossierType
from app.modules.labor_contract.model import LaborContract
from app.modules.user.model import User
from hdld_factory import client_as, grant_all, make_contract, storage  # noqa: F401

PG = {"page": 1, "page_size": 50, "offset": 0, "limit": 50}


class _Req:
    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _body(resp) -> dict:
    return json.loads(resp.body)


def _user(db, seed):
    return db.get(User, seed.u_req_id)


def _attach(db, entity: str, entity_id: int) -> int:
    sf = StoredFile(filename="a.pdf", file_key=f"k/{entity}/{entity_id}", created_by=1, updated_by=1)
    db.add(sf)
    db.flush()
    db.add(FileLink(file_id=sf.id, entity=entity, entity_id=entity_id, created_by=1, updated_by=1))
    db.commit()
    return sf.id


def _ctx(db, user) -> ToolContext:
    return ToolContext(db=db, user=user, _profile=get_perm_profile(db, user))


# ══════════════════════════════ 1. Hợp đồng NCC ══════════════════════════════

def _contract(db, seed, code, **kw):
    kw.setdefault("signed", False)
    kw.setdefault("status", "active")
    c = Contract(code=code, party_type="supplier", party_code="NX", party_name="NCC NX",
                 company_id=seed.company_id, created_by=seed.u_req_id, updated_by=seed.u_req_id, **kw)
    db.add(c)
    db.commit()
    return c


@pytest.fixture
def hop_dong(db, seed, cap_quyen):
    user = _user(db, seed)
    cap_quyen(user.id, "contract", scope="all", read=True, create=True, write=True, delete=True)
    het_han = (date.today() - timedelta(days=3)).isoformat()
    xoa = _contract(db, seed, "HD-XOA", end_date=het_han)        # chưa ký, không ngày bắt đầu → xóa được
    giu = _contract(db, seed, "HD-GIU", end_date=het_han)
    _attach(db, "contract", xoa.id)
    return user, xoa.id, giu.id


def test_hop_dong_xoa_mem_con_trong_db_giu_tep_va_bien_khoi_moi_cua_doc(db, hop_dong):
    user, xoa, giu = hop_dong
    truoc = datetime.utcnow().replace(microsecond=0)
    assert _body(contract_ctl.delete_(xoa, db, user))["message"] == "Đã xóa"

    row = db.get(Contract, xoa)
    assert row is not None and row.is_deleted is True and row.deleted_by == user.id
    assert row.deleted_at is not None and row.deleted_at >= truoc
    assert db.query(FileLink).filter(FileLink.entity == "contract", FileLink.entity_id == xoa).count() == 1

    # Chi tiết / lấy theo phạm vi: 404 như id không tồn tại (không phải 403).
    for fn in (lambda: contract_ctl.get_(xoa, db, user), lambda: contract_ctl._in_scope(db, xoa, user)):
        with pytest.raises(HTTPException) as e:
            fn()
        assert e.value.status_code == 404
    # Danh sách bỏ phiếu đã xóa, kể cả bộ lọc hết hạn.
    codes = {it["code"] for it in _body(contract_ctl.list_(_Req(), PG, db, user))["data"]["items"]}
    assert codes == {"HD-GIU"}
    codes = {it["code"] for it in _body(contract_ctl.list_(_Req(expiry="expired"), PG, db, user))["data"]["items"]}
    assert codes == {"HD-GIU"}
    # Xóa lần hai 404; xóa lô trỏ vào phiếu đã xóa → 403 (apply_scope không trả dòng nào).
    with pytest.raises(HTTPException) as e:
        contract_ctl.delete_(xoa, db, user)
    assert e.value.status_code == 404
    with pytest.raises(HTTPException) as e:
        contract_ctl.bulk_delete_contracts(str(xoa), db, user)
    assert e.value.status_code == 403
    # Phiếu còn lại nguyên vẹn.
    assert db.get(Contract, giu).is_deleted is False
    assert _body(contract_ctl.get_(giu, db, user))["data"]["code"] == "HD-GIU"


def test_hop_dong_luat_trang_thai_giu_nguyen_va_xoa_lo_mem(db, seed, hop_dong):
    user, xoa, giu = hop_dong
    ky = _contract(db, seed, "HD-KY", signed=True)
    with pytest.raises(HTTPException) as e:
        contract_ctl.delete_(ky.id, db, user)
    assert e.value.status_code == 400 and "đã ký" in e.value.detail
    assert db.get(Contract, ky.id).is_deleted is False

    contract_ctl.bulk_delete_contracts(f"{xoa},{giu}", db, user)
    assert all(db.get(Contract, i).is_deleted for i in (xoa, giu))
    assert _body(contract_ctl.list_(_Req(), PG, db, user))["data"]["total"] == 1   # còn HD-KY


def test_hop_dong_da_xoa_khong_vao_canh_bao_trang_chu_va_tool_tro_ly(db, hop_dong):
    from app.modules.alert.controller import build as build_alerts
    from app.modules.assistant.tools import catalog
    from app.modules.dashboard.controller import overview

    user, xoa, giu = hop_dong
    contract_ctl.delete_(xoa, db, user)

    alerts = {it["title"] for it in build_alerts(db, user)["items"] if it["type"] == "contract"}
    assert any("HD-GIU" in t for t in alerts) and not any("HD-XOA" in t for t in alerts)

    assert _body(overview(db, user))["data"]["kpi"]["contract_expiring"] == 1

    ctx = _ctx(db, user)
    assert [r["code"] for r in catalog.supplier_contracts(ctx, {"supplier_code": "NX"})["items"]] == ["HD-GIU"]
    assert [r["code"] for r in catalog.contract_list_by_expiry(ctx, {"status": "expired"})["items"]] == ["HD-GIU"]
    assert catalog.contract_count_by_status(ctx, {})["total"] == 1


# ══════════════════════════════ 2. Văn bản (bản nháp) ══════════════════════════════

@pytest.fixture
def van_ban(db, seed, cap_quyen, monkeypatch):
    """Hai bản nháp cùng loại; `xoa` có tệp ở phiên bản, quan hệ hai chiều với `giu`, một phiếu
    duyệt đã đóng và một dòng chỉ mục tìm toàn văn."""
    from app.modules.approval.instance_model import ApprovalInstance
    from app.modules.company.model import Company
    from app.modules.doc_catalog.link_rule_model import RELATION_REFERENCE
    from app.modules.doc_catalog.model import DocType
    from app.modules.document import search_index_service, service
    from app.modules.document.link_model import DocumentLink
    from app.modules.document.schema import DocumentCreate

    monkeypatch.setattr(core_settings, "DOCUMENT_SEARCH_INDEX_SYNC", True)
    user = _user(db, seed)
    cap_quyen(user.id, "document", scope="all", read=True, create=True, write=True, delete=True)
    db.get(Company, seed.company_id).issue_code = "DEGO"
    kind = DocType(code="QC", name="Quy chế", id_scheme=1, number_when=2)
    db.add(kind)
    db.commit()

    def _mk(title):
        return service.create_document(db, DocumentCreate(
            doc_type_id=kind.id, company_id=seed.company_id, department_id=seed.dept_id,
            owner_employee_id=seed.emp_req_id, title=title, content_html=f"<p>{title}</p>"), user.id)

    xoa, giu = _mk("Quy chế sẽ xóa"), _mk("Quy chế còn giữ")
    #  Dựng chỉ mục TRƯỚC khi gắn tệp: `reindex` trích chữ từ tệp thật, mà bài kiểm không có storage.
    assert search_index_service.reindex(db, xoa.id) is not None
    version = service.open_version(db, xoa)
    _attach(db, "document_version", version.id)
    db.add(DocumentLink(source_document_id=xoa.id, target_document_id=giu.id,
                        relation=RELATION_REFERENCE, created_by=user.id, updated_by=user.id))
    db.add(DocumentLink(source_document_id=giu.id, target_document_id=xoa.id,
                        relation=RELATION_REFERENCE, created_by=user.id, updated_by=user.id))
    db.add(ApprovalInstance(entity="document", entity_id=xoa.id, flow_id=1, status=4, current_seq=1,
                            created_by=user.id, updated_by=user.id))
    db.commit()
    return user, xoa.id, giu.id, version.id


def test_van_ban_xoa_mem_giu_phien_ban_tep_quan_he_phieu_duyet(db, van_ban):
    from app.modules.approval import entity_hooks
    from app.modules.approval.instance_model import ApprovalInstance
    from app.modules.document import approval_bridge, link_service, service
    from app.modules.document import controller as doc_ctl
    from app.modules.document.link_model import DocumentLink
    from app.modules.document.model import Document
    from app.modules.document.query import documents_query
    from app.modules.document.search_model import DocumentSearch
    from app.modules.document.version_model import DocumentVersion

    user, xoa, giu, version_id = van_ban
    assert _body(doc_ctl.delete_document(xoa, db, user))["message"] == "Đã xóa văn bản"

    row = db.get(Document, xoa)
    assert row.is_deleted is True and row.deleted_by == user.id and row.deleted_at is not None
    # Con GIỮ: phiên bản, tệp của phiên bản, quan hệ hai chiều, phiếu duyệt đã đóng.
    assert db.query(DocumentVersion).filter(DocumentVersion.document_id == xoa).count() == 1
    assert db.query(FileLink).filter(FileLink.entity == "document_version",
                                     FileLink.entity_id == version_id).count() == 1
    assert db.query(DocumentLink).filter((DocumentLink.source_document_id == xoa)
                                         | (DocumentLink.target_document_id == xoa)).count() == 2
    assert db.query(ApprovalInstance).filter(ApprovalInstance.entity == "document",
                                             ApprovalInstance.entity_id == xoa).count() == 1
    # Chỉ mục tìm toàn văn thì GỠ — FULLTEXT không trả về văn bản đã xóa.
    assert db.get(DocumentSearch, xoa) is None

    # Chi tiết 404 (cả service lẫn cửa `_load` của controller); cửa chung `documents_query` giấu.
    for fn in (lambda: service.get_or_404(db, xoa), lambda: doc_ctl._load(db, xoa, user, "read")):
        with pytest.raises(HTTPException) as e:
            fn()
        assert e.value.status_code == 404
    assert {d.id for d in documents_query(db).all()} == {giu}
    assert xoa in {d.id for d in documents_query(db, include_deleted=True).all()}
    # Danh sách (cùng truy vấn với xuất Excel) bỏ văn bản đã xóa.
    prof = get_perm_profile(db, user)
    q, _ = doc_ctl._list_query(_Req(), db, user, prof)
    assert {d.id for d in q.all()} == {giu}
    # Tab Quan hệ của văn bản còn sống không bày dòng trỏ vào văn bản đã xóa.
    assert link_service.links_of(db, giu) == [] and link_service.links_to(db, giu) == []
    # Bộ máy duyệt: không đọc được phiếu của văn bản đã xóa, bối cảnh rỗng.
    assert approval_bridge._can_read_document(db, xoa, user) is False
    assert entity_hooks.entity_context(db, "document", xoa) == {}
    assert approval_bridge._can_read_document(db, giu, user) is True

    # Xóa lần hai 404; văn bản còn lại mở được.
    with pytest.raises(HTTPException) as e:
        doc_ctl.delete_document(xoa, db, user)
    assert e.value.status_code == 404
    assert doc_ctl._load(db, giu, user, "read").id == giu


def test_van_ban_bao_cao_duyet_va_tool_tro_ly_khong_thay_van_ban_da_xoa(db, van_ban):
    from app.modules.approval.report_service import _document_ids
    from app.modules.assistant.tools.document_tool import _run_document_read, _run_document_search
    from app.modules.document import service
    from app.modules.document.model import Document

    user, xoa, giu, _ = van_ban
    service.delete_document(db, db.get(Document, xoa), user.id)

    sub = _document_ids(db, user, get_perm_profile(db, user))
    assert {r[0] for r in db.query(sub.c.id).all()} == {giu}

    ctx = _ctx(db, user)
    assert "error" in _run_document_read(ctx, {"document_id": xoa})
    assert _run_document_read(ctx, {"document_id": giu}).get("error") is None
    found = {it["document_id"] for it in _run_document_search(ctx, {"keyword": "Quy chế"})["items"]}
    assert found == {giu}


def test_van_ban_luat_trang_thai_va_bo_nhap_cua_minh(db, van_ban):
    from app.modules.document import service
    from app.modules.document.model import STATUS_SUBMITTED, Document

    user, xoa, giu, _ = van_ban
    db.get(Document, giu).status = STATUS_SUBMITTED
    db.commit()
    with pytest.raises(HTTPException) as e:
        service.delete_document(db, db.get(Document, giu), user.id)
    assert e.value.status_code == 400
    assert db.get(Document, giu).is_deleted is False

    # Nút «Hủy» ở màn Tạo văn bản: cũng xóa mềm, ghi đúng người bỏ nháp.
    service.discard_own_draft(db, db.get(Document, xoa), user.id)
    row = db.get(Document, xoa)
    assert row.is_deleted is True and row.deleted_by == user.id


# ══════════════════════════════ 3. Hợp đồng lao động ══════════════════════════════

CT_URL = "/api/labor-contracts"


@pytest.fixture
def hdld(db, world, storage, client_as):  # noqa: F811
    grant_all(world, "a1", scope="all")
    a1 = client_as(world.actor("a1"))
    xoa = make_contract(a1, world.emp["a2"], contract_no="HD/2026-01")
    giu = make_contract(a1, world.emp["a2"], contract_no="HD/2026-02")
    return world, a1, xoa, giu


def test_hdld_xoa_mem_bien_khoi_api_giu_tep_khong_tai_dung_ma(db, hdld):
    world, a1, xoa, giu = hdld
    sf = StoredFile(filename="ky.pdf", file_key="k/hdld/ky", created_by=1, updated_by=1)
    db.add(sf)
    db.commit()
    row = db.get(LaborContract, xoa["id"])
    row.signed_file_id = sf.id
    db.commit()

    assert a1.delete(f"{CT_URL}/{xoa['id']}").status_code == 200
    row = db.get(LaborContract, xoa["id"])
    assert row.is_deleted is True and row.deleted_by == world.user_id("a1") and row.deleted_at is not None
    assert row.signed_file_id == sf.id and db.get(StoredFile, sf.id) is not None   # tệp GIỮ

    assert a1.get(f"{CT_URL}/{xoa['id']}").status_code == 404
    assert a1.get(f"{CT_URL}/{xoa['id']}/signed-file").status_code == 404
    assert a1.delete(f"{CT_URL}/{xoa['id']}").status_code == 404
    assert a1.patch(f"{CT_URL}/{xoa['id']}", json={"note": "x"}).status_code == 404
    items = a1.get(f"/api/employees/{world.emp['a2']}/labor-contracts").json()["data"]["items"]
    assert [it["id"] for it in items] == [giu["id"]]

    # Mã HĐLD không tái dùng; số in trên giấy của bản nháp đã bỏ thì dùng lại được.
    moi = make_contract(a1, world.emp["a3"], contract_no="HD/2026-01")
    assert moi["code"] not in (xoa["code"], giu["code"])
    assert moi["code"] > giu["code"] > xoa["code"], "hậu tố phải tăng, không lấp chỗ của HĐ đã xóa"


def test_hdld_luat_trang_thai_giu_nguyen(hdld):
    world, a1, xoa, giu = hdld
    assert a1.post(f"{CT_URL}/{giu['id']}/transition",
                   json={"to_status": 2, "date": "2026-01-05"}).status_code == 200
    assert a1.delete(f"{CT_URL}/{giu['id']}").status_code == 409
    assert a1.get(f"{CT_URL}/{giu['id']}").status_code == 200


def test_hdld_da_xoa_khong_giu_chan_mau(db, hdld):
    from app.modules.labor_contract.template_model import LaborContractTemplate
    from app.modules.labor_contract.template_service import delete_template

    world, a1, xoa, giu = hdld
    tpl = LaborContractTemplate(company_id=world.co["A"], contract_type=2, name="Mẫu", file_id=0,
                                is_active=True, created_by=1, updated_by=1)
    db.add(tpl)
    db.commit()
    for cid in (xoa["id"], giu["id"]):
        db.get(LaborContract, cid).template_id = tpl.id
    db.commit()
    with pytest.raises(HTTPException) as e:
        delete_template(db, tpl)
    assert e.value.status_code == 409 and "2 hợp đồng" in e.value.detail

    a1.delete(f"{CT_URL}/{xoa['id']}")
    with pytest.raises(HTTPException) as e:
        delete_template(db, tpl)
    assert "1 hợp đồng" in e.value.detail


# ══════════════════════════════ 4. Hồ sơ (CRUD chung) ══════════════════════════════

@pytest.fixture
def ho_so(db, world, client_as):  # noqa: F811
    actor = world.actor("a1")
    actor.grant("dossier", "all", actions=("read", "create", "write", "delete"))
    actor.grant("dossier_type", "all", actions=("read", "create", "write", "delete"))
    a1 = client_as(actor)
    loai = DossierType(code="GP", name="Giấy phép", is_active=True, created_by=1, updated_by=1)
    db.add(loai)
    db.commit()

    def _mk(name, **over):
        res = a1.post("/api/dossiers", json={"name": name, "dossier_type_id": loai.id, **over})
        assert res.status_code == 201, res.text
        return res.json()["data"]

    xoa = _mk("Giấy phép sẽ xóa")
    giu = _mk("Giấy phép còn giữ", depends=[xoa["id"]])
    _attach(db, "dossier", xoa["id"])
    return world, a1, loai, xoa, giu


def test_ho_so_crud_chung_xoa_mem_va_khong_tai_dung_ma(db, ho_so):
    world, a1, loai, xoa, giu = ho_so
    assert xoa["code"] == "HS001" and giu["code"] == "HS002"

    res = a1.delete(f"/api/dossiers/{xoa['id']}")
    assert res.status_code == 200 and res.json()["message"] == "Đã xóa"
    row = db.get(Dossier, xoa["id"])
    assert row is not None and row.is_deleted is True and row.deleted_by == world.user_id("a1")
    assert row.deleted_at is not None
    assert db.query(FileLink).filter(FileLink.entity == "dossier", FileLink.entity_id == xoa["id"]).count() == 1

    assert a1.get(f"/api/dossiers/{xoa['id']}").status_code == 404
    assert a1.delete(f"/api/dossiers/{xoa['id']}").status_code == 404
    assert a1.patch(f"/api/dossiers/{xoa['id']}", json={"note": "x"}).status_code == 404
    assert [it["id"] for it in a1.get("/api/dossiers").json()["data"]["items"]] == [giu["id"]]
    csv = a1.get("/api/dossiers/export/csv")
    assert csv.status_code == 200 and "HS002" in csv.text and "HS001" not in csv.text

    # Mã không tái dùng (MAX toàn bảng kể cả hàng đã xóa) và không tạo lại được mã đã xóa.
    moi = a1.post("/api/dossiers", json={"name": "Thứ ba", "dossier_type_id": loai.id}).json()["data"]
    assert moi["code"] == "HS003"
    assert generate_code(db, Dossier, "HS") == "HS004"
    assert a1.post("/api/dossiers", json={"name": "Trùng", "code": "HS001",
                                          "dossier_type_id": loai.id}).status_code == 400

    # Tiên quyết: tờ đã xóa không còn là tiên quyết hợp lệ, và không bày tên nữa.
    with pytest.raises(HTTPException) as e:
        check_depends(db, 0, [xoa["id"]])
    assert e.value.status_code == 400
    assert [d["id"] for d in depends_names(db, [xoa["id"], giu["id"]])] == [giu["id"]]
    assert a1.get(f"/api/dossiers/{giu['id']}").status_code == 200   # tờ còn sống không bị kẹt


def test_ho_so_da_xoa_khong_giu_chan_loai_va_model_khong_co_cot_van_xoa_cung(db, ho_so):
    world, a1, loai, xoa, giu = ho_so
    assert dossier_service.count_by_type(db, loai.id) == 2
    a1.delete(f"/api/dossiers/{xoa['id']}")
    assert dossier_service.count_by_type(db, loai.id) == 1
    # Loại còn một tờ sống → vẫn chặn xóa loại (chốt `before_delete` của CRUD chung giữ nguyên).
    assert a1.delete(f"/api/dossier-types/{loai.id}").status_code == 400

    # Model KHÔNG có `is_deleted` (Loại hồ sơ) đi qua cùng `delete_item` → vẫn xóa cứng.
    trong = DossierType(code="TRONG", name="Loại không ai dùng", is_active=True, created_by=1, updated_by=1)
    db.add(trong)
    db.commit()
    tid = trong.id
    assert a1.delete(f"/api/dossier-types/{tid}").status_code == 200
    assert db.get(DossierType, tid) is None


def test_remove_or_mark_deleted_re_theo_model(db, world):
    """Hàm rẽ dùng chung của CRUD: có cột → đánh cờ (trả True), không có → `db.delete` (trả False)."""
    loai = DossierType(code="X", name="X", is_active=True, created_by=1, updated_by=1)
    db.add(loai)
    db.flush()
    hs = Dossier(code="HS-X", name="x", dossier_type_id=loai.id, dossier_type_name="X",
                 created_by=1, updated_by=1)
    db.add(hs)
    db.commit()
    uid = world.user_id("a1")

    assert remove_or_mark_deleted(db, hs, uid) is True
    db.commit()
    assert db.get(Dossier, hs.id).is_deleted is True and db.get(Dossier, hs.id).deleted_by == uid

    lid = loai.id
    assert remove_or_mark_deleted(db, loai, uid) is False
    db.commit()
    assert db.get(DossierType, lid) is None
