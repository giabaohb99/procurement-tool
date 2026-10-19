"""duoc-CR-629b bước B — CÁCH LY: người đọc `doc_template` (mọi vai trò) KHÔNG BAO GIỜ thấy mẫu HĐLĐ.

Hai loại mẫu chung bảng `tab_document_template` (single-table inheritance, cột `template_kind`).
Mỗi bài có cặp đối chứng để chứng minh «chặn đúng chỗ» chứ không «chặn tất».
"""
import ast
import uuid
from pathlib import Path

import pytest
from sqlalchemy.orm import sessionmaker

from app.core.audit import record
from app.core.change_tracker import flush_changes
from app.core.logging_codes import ACTOR_KIND_USER
from app.core.request_context import RequestContext, reset_context, set_context
from app.core.scoping import get_scoped
from app.modules.audit.model import AuditLog
from app.modules.change_log.model import ChangeLog
from app.core.auth import get_perm_profile
from app.core.reference_guard import count_references
from app.modules.attachment.model import StoredFile
from app.modules.company.model import Company
from app.modules.doc_catalog.model import DocType
from app.modules.document.template_model import DocumentTemplate, TemplateRecord
from app.modules.labor_contract.lookup import names_map
from app.modules.labor_contract.template_model import LaborContractTemplate
from hdld_factory import client_as, grant_all, storage, upload_template  # noqa: F401

DOC_URL = "/api/document-templates"
LCT_URL = "/api/labor-contract-templates"
CRUD = ("read", "create", "write", "delete")


@pytest.fixture
def ctx(db, world, storage, client_as):  # noqa: F811
    """a1 = HR công ty A (có labor_contract_template); a3 = văn thư (doc_template phạm vi tất cả, KHÔNG có
    labor_contract_template); khongphong = admin Văn bản. `vb` = mẫu văn bản thường, `hd` = mẫu HĐLĐ."""
    grant_all(world, "a1")
    world.actor("a3").grant("doc_template", "all", actions=CRUD)
    world.actor("khongphong").grant("doc_template", "all", actions=CRUD)
    kind = DocType(code="QD", name="Quyết định", id_scheme=2, number_when=2, is_active=True)
    db.add(kind)
    db.commit()
    vb = DocumentTemplate(doc_type_id=kind.id, name="Quyết định bổ nhiệm", content_html="<p>x</p>")
    db.add(vb)
    db.commit()
    a1 = client_as(world.actor("a1"))
    hd = upload_template(a1, company_id=world.co["A"], name="Mẫu HĐLĐ A").json()["data"]

    class C:
        pass

    c = C()
    c.world, c.db, c.kind, c.vb, c.hd, c.a1, c.storage = world, db, kind, vb, hd, a1, storage
    c.van_thu = client_as(world.actor("a3"))
    c.admin_vb = client_as(world.actor("khongphong"))
    return c


def test_mau_hdld_nam_chung_bang_nhung_khac_loai(ctx):
    rows = {r.id: r.template_kind for r in ctx.db.query(TemplateRecord.id, TemplateRecord.template_kind)}
    assert rows == {ctx.vb.id: 1, ctx.hd["id"]: 2}


def test_danh_sach_van_ban_mau_khong_co_mau_hdld(ctx):
    for who in (ctx.van_thu, ctx.admin_vb):
        data = who.get(DOC_URL).json()["data"]
        assert data["total"] == 1 and [i["name"] for i in data["items"]] == ["Quyết định bổ nhiệm"]
        # Ô «Chọn mẫu» khi soạn: lọc theo loại + đang dùng.
        sel = who.get(DOC_URL, params={"doc_type_id": ctx.kind.id, "is_active": "true"}).json()["data"]
        assert [i["name"] for i in sel["items"]] == ["Quyết định bổ nhiệm"]
        # Dò bằng loại 0 / loại HDLD / tên mẫu HĐLĐ đều rỗng.
        for params in ({"doc_type_id": 0}, {"name": "HĐLĐ"}, {"doc_type_id": 0, "is_active": "true"}):
            assert who.get(DOC_URL, params=params).json()["data"]["total"] == 0, params


def test_danh_sach_van_ban_mau_khong_lo_mau_hdld_ke_ca_khi_gan_loai_hdld(ctx):
    """Mẫu HĐLĐ mang doc_type_id của loại HDLD (quyết định 2) — lọc theo loại đó vẫn không thấy."""
    hdld = DocType(code="HDLD", name="Hợp đồng lao động", id_scheme=2, number_when=2, is_active=True)
    ctx.db.add(hdld)
    ctx.db.commit()
    row = ctx.db.query(LaborContractTemplate).one()
    row.doc_type_id = hdld.id
    ctx.db.commit()
    res = ctx.van_thu.get(DOC_URL, params={"doc_type_id": hdld.id}).json()["data"]
    assert res["total"] == 0 and res["items"] == []
    assert ctx.van_thu.get(f"{DOC_URL}/{ctx.hd['id']}").status_code == 404


def test_get_sua_xoa_van_ban_mau_bang_id_hdld_tra_404(ctx):
    tid = ctx.hd["id"]
    for method, kw in (("get", {}), ("patch", {"json": {"name": "bị sửa"}}), ("delete", {})):
        for who in (ctx.van_thu, ctx.admin_vb):
            res = getattr(who, method)(f"{DOC_URL}/{tid}", **kw)
            assert res.status_code == 404, f"{method} → {res.status_code}"
    ctx.db.expire_all()
    row = ctx.db.query(LaborContractTemplate).filter_by(id=tid).one()
    assert row.name == "Mẫu HĐLĐ A" and row.file_id
    assert ctx.db.get(StoredFile, row.file_id) is not None and len(ctx.storage) == 1
    # Đối chứng: mẫu văn bản thường cùng API thì sửa/xóa được.
    assert ctx.van_thu.patch(f"{DOC_URL}/{ctx.vb.id}", json={"name": "Đã sửa"}).status_code == 200
    assert ctx.van_thu.delete(f"{DOC_URL}/{ctx.vb.id}").status_code == 200


def test_get_va_get_scoped_khong_lan_loai(ctx):
    db = ctx.db
    # Đã nạp cả hai vào identity map của phiên rồi vẫn không lẫn.
    db.query(TemplateRecord).all()
    assert db.get(DocumentTemplate, ctx.hd["id"]) is None
    assert db.get(LaborContractTemplate, ctx.vb.id) is None
    user = ctx.world.actor("a1").user
    profile = get_perm_profile(db, user)
    assert get_scoped(db, LaborContractTemplate, "labor_contract_template", ctx.vb.id, user, profile) is None
    assert names_map(db, LaborContractTemplate, {ctx.vb.id}) == {}
    assert names_map(db, DocumentTemplate, {ctx.hd["id"]}) == {}


def test_api_mau_hdld_khong_tra_mau_van_ban(ctx):
    admin = ctx.world.actor("khongphong")
    admin.grant("labor_contract_template", "all", actions=("read",))
    res = ctx.admin_vb.get(LCT_URL).json()["data"]
    assert [r["name"] for r in res["items"]] == ["Mẫu HĐLĐ A"]
    assert ctx.admin_vb.get(f"{LCT_URL}/{ctx.vb.id}").status_code == 404
    # Và người chỉ có doc_template (không có quyền HĐLĐ) bị chặn hẳn.
    assert ctx.van_thu.get(LCT_URL).status_code == 403


def test_chot_xoa_loai_van_ban_va_phap_nhan_dem_dung_loai(ctx):
    db = ctx.db
    kind_refs = dict(count_references(db, "doc_type", ctx.kind))
    assert kind_refs.get("mẫu văn bản") == 1
    assert "mẫu hợp đồng lao động" not in kind_refs
    hdld = DocType(code="HDLD", name="Hợp đồng lao động", id_scheme=2, number_when=2, is_active=True)
    db.add(hdld)
    db.commit()
    db.query(LaborContractTemplate).one().doc_type_id = hdld.id
    db.commit()
    refs = dict(count_references(db, "doc_type", hdld))
    assert refs.get("mẫu hợp đồng lao động") == 1 and "mẫu văn bản" not in refs
    company = db.get(Company, ctx.world.co["A"])
    company_refs = dict(count_references(db, "company", company))
    assert company_refs.get("mẫu hợp đồng lao động") == 1


def _app_dir() -> Path:
    app_dir = Path(__file__).resolve().parents[2] / "backend" / "app"
    return app_dir if app_dir.exists() else Path("/app/app")


def _docstring_nodes(tree) -> set[int]:
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant):
                ids.add(id(body[0].value))
    return ids


def test_khong_ma_ung_dung_nao_truy_van_lop_goc():
    app_dir = _app_dir()
    users = sorted(str(p.relative_to(app_dir)) for p in app_dir.rglob("*.py")
                   if "TemplateRecord" in p.read_text(encoding="utf-8"))
    assert users == ["modules/document/template_model.py", "modules/labor_contract/template_model.py"], users


def test_khong_ma_ung_dung_nao_dung_sql_tho_hay_table_cua_bang_mau():
    """Lớp con STI chỉ tự lọc loại khi truy vấn qua ORM. Chuỗi tên bảng (SQL thô, core `Table`) và `.__table__`
    của các lớp mẫu đi vòng qua bộ lọc đó ⇒ rò mẫu HĐLĐ cho người chỉ có `doc_template`."""
    app_dir = _app_dir()
    bad = []
    for path in app_dir.rglob("*.py"):
        rel = str(path.relative_to(app_dir))
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docs = _docstring_nodes(tree)
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs
                    and "tab_document_template" in node.value
                    and rel != "modules/document/template_model.py"):
                bad.append(f"{rel}:{node.lineno} chuỗi tab_document_template")
            if (isinstance(node, ast.Attribute) and node.attr == "__table__"
                    and isinstance(node.value, ast.Name)
                    and node.value.id in {"TemplateRecord", "DocumentTemplate", "LaborContractTemplate"}):
                bad.append(f"{rel}:{node.lineno} {node.value.id}.__table__")
    assert not bad, bad


@pytest.fixture
def tracker(db, monkeypatch):
    Session = sessionmaker(bind=db.get_bind(), autoflush=False, autocommit=False, future=True)
    monkeypatch.setattr("app.core.database.SessionLocal", Session)
    context = RequestContext(request_id=uuid.uuid4().bytes, user_id=7, actor_kind=ACTOR_KIND_USER)
    token = set_context(context)
    try:
        yield context
    finally:
        reset_context(token)


def test_lich_su_thay_doi_mau_hdld_giu_ten_bang_cu_va_backfill_dung_entity(ctx, tracker):
    db = ctx.db
    hd = db.query(LaborContractTemplate).one()
    tracker.changes = []
    hd.note = "ghi chú mới"
    db.commit()
    record(db, 7, "labor_contract_template", hd.id, "update", "sửa")
    vb = db.query(DocumentTemplate).one()
    vb.description = "mô tả mới"
    db.commit()
    record(db, 7, "document_template", vb.id, "update", "sửa")
    tracker.changes = [c for c in tracker.changes]   # giữ bộ đệm của hai lần commit trên
    flush_changes(tracker)
    rows = {(r.table_name, r.row_id, r.field) for r in db.query(ChangeLog).filter(ChangeLog.field != "")}
    assert ("tab_labor_contract_template", hd.id, "description") in rows
    assert ("tab_document_template", vb.id, "description") in rows
    assert ("tab_document_template", hd.id, "description") not in rows
    audit = {(a.entity, a.entity_id): a.changed_fields for a in db.query(AuditLog)
             if a.entity in ("labor_contract_template", "document_template")}
    assert audit[("labor_contract_template", hd.id)] == "description"
    assert audit[("document_template", vb.id)] == "description"


def test_trung_ten_giua_hai_loai_duoc_phep(ctx):
    # Mẫu văn bản trùng tên mẫu HĐLĐ: được.
    res = ctx.van_thu.post(DOC_URL, json={"doc_type_id": ctx.kind.id, "name": "Mẫu HĐLĐ A", "content_html": "<p/>"})
    assert res.status_code == 201, res.text
    # Mẫu HĐLĐ trùng tên mẫu văn bản: được; trùng tên cùng pháp nhân: 400.
    ok = upload_template(ctx.a1, company_id=ctx.world.co["A"], name="Quyết định bổ nhiệm")
    assert ok.status_code == 201, ok.text
    dup = upload_template(ctx.a1, company_id=ctx.world.co["A"], name="Mẫu HĐLĐ A")
    assert dup.status_code == 400


def test_id_cap_moi_khong_dung_nhau_giua_hai_loai(ctx):
    ids = [r[0] for r in ctx.db.query(TemplateRecord.id).all()]
    assert len(ids) == len(set(ids))
    new = ctx.van_thu.post(DOC_URL, json={"doc_type_id": ctx.kind.id, "name": "Mới", "content_html": "<p/>"})
    assert new.json()["data"]["id"] not in ids


def test_mau_hdld_moi_tao_gan_loai_hdld_khi_loai_da_co(db, world, storage, client_as):  # noqa: F811
    grant_all(world, "a1")
    hdld = DocType(code="HDLD", name="Hợp đồng lao động", id_scheme=2, number_when=2, is_active=True)
    db.add(hdld)
    db.commit()
    res = upload_template(client_as(world.actor("a1")), company_id=world.co["A"])
    assert res.status_code == 201
    assert db.query(LaborContractTemplate).one().doc_type_id == hdld.id


def test_seed_dien_bu_doc_type_id_chi_o_dong_dang_0(db, world, storage, client_as):  # noqa: F811
    from app.seed import seed_document_phase1

    grant_all(world, "a1")
    a1 = client_as(world.actor("a1"))
    upload_template(a1, company_id=world.co["A"], name="Mẫu 0")
    upload_template(a1, company_id=world.co["A"], name="Mẫu đã gán")
    other = DocType(code="ZZ", name="Loại khác", id_scheme=2, number_when=2, is_active=True)
    db.add(other)
    db.commit()
    db.query(LaborContractTemplate).filter_by(name="Mẫu đã gán").one().doc_type_id = other.id
    db.commit()
    seed_document_phase1(db)
    db.commit()
    hdld = db.query(DocType).filter(DocType.code == "HDLD").one()
    got = {t.name: t.doc_type_id for t in db.query(LaborContractTemplate).all()}
    assert got == {"Mẫu 0": hdld.id, "Mẫu đã gán": other.id}
