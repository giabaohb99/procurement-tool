"""duoc-CR-629 — HĐLĐ sinh BẢN LƯU TRỮ ở phân hệ Văn bản: tạo, đồng bộ, gương tệp, trạng thái, xóa, script bù.

Dùng khung `hdld_factory` (kho tệp giả, client đăng nhập giả). Mỗi test tự dựng loại `HDLD`
(test HĐLĐ cũ không có loại này nên cầu nối im lặng — hành vi cũ giữ nguyên).
"""
import importlib.util
import pathlib

import pytest

from app.core.labor_contract_codes import LaborContractStatus as S
from app.modules.attachment.model import FileLink, StoredFile
from app.modules.doc_catalog.model import DocType
from app.modules.document import model as dm
from app.modules.document.model import Document
from app.modules.document.service import ATTACH_ENTITY
from app.modules.labor_contract import document_archive_sync, service as lc_service
from app.modules.labor_contract.model import LaborContract
from hdld_factory import (PDF_BYTES, PNG_BYTES, client_as, grant_all, make_contract,  # noqa: F401
                          storage, upload_template)

CT_URL = "/api/labor-contracts"


@pytest.fixture
def setup(db, world, storage, client_as):  # noqa: F811
    grant_all(world, "a1")
    world.grant("a1", "document", "company", actions=("read",))
    db.add(DocType(code="HDLD", name="Hợp đồng lao động", id_scheme=2, number_when=2,
                   is_personal=True, needs_approval=False, needs_signature=False))
    db.commit()
    a1 = client_as(world.actor("a1"))
    tpl = upload_template(a1, company_id=world.co["A"]).json()["data"]
    return world, a1, storage, tpl["id"]


def _doc(db, cid) -> Document:
    db.expire_all()
    lc = db.get(LaborContract, cid)
    return db.get(Document, lc.document_id) if lc.document_id else None


def _links(db, doc):
    return db.query(FileLink).filter(FileLink.entity == ATTACH_ENTITY,
                                     FileLink.entity_id == doc.current_version_id).all()


def _sha(db, link):
    return db.get(StoredFile, link.file_id).sha256


def test_lap_hd_sinh_van_ban_nhap_khong_lo_luong(setup, db):
    world, a1, _, _ = setup
    item = make_contract(a1, world.emp["a2"])
    doc = _doc(db, item["id"])
    assert doc is not None and item["document_id"] == doc.id and item["can_open_document"] is True
    assert (doc.status, doc.content_mode) == (dm.STATUS_DRAFT, dm.CONTENT_MODE_FILES)
    assert (doc.company_id, doc.department_id) == (world.co["A"], world.dept["A.kt"])
    assert not doc.owner_employee_id and not doc.meta
    assert db.get(DocType, doc.doc_type_id).code == "HDLD"
    blob = f"{doc.title} {doc.summary}"
    for secret in ("15000000", "15.000.000", "10000000", "500000", "Xăng xe"):
        assert secret not in blob
    assert doc.effective_date.isoformat() == "2026-01-01" and doc.expire_date.isoformat() == "2026-12-31"


def test_thieu_loai_hdld_van_lap_duoc_roi_tu_lanh(setup, db):
    world, a1, _, tpl = setup
    db.query(DocType).filter(DocType.code == "HDLD").update({"is_active": False})
    db.commit()
    item = make_contract(a1, world.emp["a2"])
    assert item["document_id"] == 0 and item["can_open_document"] is False
    db.query(DocType).filter(DocType.code == "HDLD").update({"is_active": True})
    db.commit()
    assert a1.post(f"{CT_URL}/{item['id']}/generate", json={"template_id": tpl}).status_code == 200
    assert _doc(db, item["id"]) is not None


def test_loi_tao_van_ban_khong_lam_hong_viec_lap_hd(setup, db, monkeypatch):
    world, a1, _, _ = setup

    def boom(*a, **k):
        raise RuntimeError("hỏng")
    monkeypatch.setattr("app.modules.document.service.create_document", boom)
    res = a1.post(f"/api/employees/{world.emp['a2']}/labor-contracts",
                  json={"contract_type": 2, "start_date": "2026-01-01", "end_date": "2026-12-31",
                        "base_salary": 1, "insurance_salary": 1, "allowance": 0})
    assert res.status_code == 201 and res.json()["data"]["item"]["document_id"] == 0
    assert db.query(Document).count() == 0


def test_sinh_tep_chep_byte_sang_ban_sao_rieng_va_sinh_lai_khong_trung(setup, db, storage):
    world, a1, _, tpl = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    assert a1.post(f"{CT_URL}/{cid}/generate", json={"template_id": tpl}).status_code == 200
    lc, doc = db.get(LaborContract, cid), _doc(db, cid)
    links = _links(db, doc)
    assert len(links) == 1 and links[0].file_id != lc.generated_file_id
    assert _sha(db, links[0]) == db.get(StoredFile, lc.generated_file_id).sha256
    old_key = db.get(StoredFile, links[0].file_id).file_key

    assert a1.post(f"{CT_URL}/{cid}/generate", json={"template_id": tpl}).status_code == 200
    db.expire_all()
    doc = _doc(db, cid)
    links = _links(db, doc)
    assert len(links) == 1
    lc = db.get(LaborContract, cid)
    assert _sha(db, links[0]) == db.get(StoredFile, lc.generated_file_id).sha256
    new_key = db.get(StoredFile, links[0].file_id).file_key
    if old_key != new_key:
        assert old_key not in storage          # bản sao cũ bị gỡ cả byte
    assert new_key in storage and lc.generated_file_id != links[0].file_id


def test_sua_hd_nhap_go_ban_sao_docx_va_dong_bo_tieu_de_ngay(setup, db):
    world, a1, _, tpl = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    a1.post(f"{CT_URL}/{cid}/generate", json={"template_id": tpl})
    assert len(_links(db, _doc(db, cid))) == 1
    res = a1.patch(f"{CT_URL}/{cid}", json={"contract_no": "SO-77", "end_date": "2026-11-30"})
    assert res.status_code == 200, res.text
    doc = _doc(db, cid)
    assert _links(db, doc) == [] and "SO-77" in doc.title and doc.expire_date.isoformat() == "2026-11-30"


def test_ban_ky_hai_tep_va_thay_ban_ky_van_hai_tep(setup, db):
    world, a1, _, tpl = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    a1.post(f"{CT_URL}/{cid}/generate", json={"template_id": tpl})
    r = a1.put(f"{CT_URL}/{cid}/signed-file", files={"file": ("scan.pdf", PDF_BYTES, "application/pdf")})
    assert r.status_code == 200
    doc = _doc(db, cid)
    assert len(_links(db, doc)) == 2
    r = a1.put(f"{CT_URL}/{cid}/signed-file", files={"file": ("scan.png", PNG_BYTES, "image/png")})
    assert r.status_code == 200
    links = _links(db, _doc(db, cid))
    assert len(links) == 2
    names = sorted(db.get(StoredFile, l.file_id).filename for l in links)
    assert any(n.endswith(".png") for n in names) and not any(n.endswith(".pdf") for n in names)


def test_trang_thai_ky_cham_dut_huy(setup, db):
    world, a1, _, _ = setup
    c1 = make_contract(a1, world.emp["a2"])["id"]
    assert a1.post(f"{CT_URL}/{c1}/transition", json={"to_status": int(S.SIGNED), "date": "2026-01-05"}).status_code == 200
    assert _doc(db, c1).status == dm.STATUS_EFFECTIVE
    r = a1.post(f"{CT_URL}/{c1}/transition",
                json={"to_status": int(S.TERMINATED), "date": "2026-06-30", "reason": "Hết nhu cầu"})
    assert r.status_code == 200, r.text
    doc = _doc(db, c1)
    assert doc.status == dm.STATUS_EXPIRED and doc.expire_date.isoformat() == "2026-06-30"

    c2 = make_contract(a1, world.emp["a3"])["id"]
    r = a1.post(f"{CT_URL}/{c2}/transition", json={"to_status": int(S.CANCELLED), "reason": "Nhập nhầm"})
    assert r.status_code == 200, r.text
    doc = _doc(db, c2)
    assert doc.status == dm.STATUS_ARCHIVED and "Đã hủy: Nhập nhầm" in doc.summary


def test_xoa_mem_hd_giu_van_ban_va_ban_sao_tep(setup, db):
    world, a1, _, tpl = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    a1.post(f"{CT_URL}/{cid}/generate", json={"template_id": tpl})
    assert a1.delete(f"{CT_URL}/{cid}").status_code == 200
    doc = _doc(db, cid)
    assert doc is not None and not doc.is_deleted and doc.status == dm.STATUS_ARCHIVED
    assert "đã xóa ở phân hệ Nhân sự" in doc.summary and len(_links(db, doc)) == 1


def test_xoa_cung_ho_so_nhan_su_xoa_mem_van_ban(setup, db):
    world, a1, _, _ = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    doc_id = db.get(LaborContract, cid).document_id
    a1.post(f"{CT_URL}/{cid}/transition", json={"to_status": int(S.CANCELLED), "reason": "x"})
    lc_service.delete_all_of(db, world.emp["a2"])
    db.commit()
    assert db.query(LaborContract).filter(LaborContract.id == cid).count() == 0
    assert db.get(Document, doc_id).is_deleted is True


def test_xoa_tep_goc_khong_dung_ban_sao_va_sync_hai_lan_khong_them(setup, db):
    world, a1, storage, tpl = setup
    cid = make_contract(a1, world.emp["a2"])["id"]
    a1.post(f"{CT_URL}/{cid}/generate", json={"template_id": tpl})
    lc = db.get(LaborContract, cid)
    doc_id = lc.document_id
    before = (db.query(Document).count(), db.query(FileLink).count(), db.query(StoredFile).count())
    assert document_archive_sync.archive_sync(db, cid, 1) == doc_id
    assert document_archive_sync.archive_sync(db, cid, 1) == doc_id
    assert before == (db.query(Document).count(), db.query(FileLink).count(), db.query(StoredFile).count())
    # xóa byte + dòng tệp gốc — bản sao vẫn nguyên
    copy = _links(db, _doc(db, cid))[0]
    from app.modules.attachment.service import delete_stored_file
    delete_stored_file(db, lc.generated_file_id)
    db.commit()
    assert db.get(StoredFile, copy.file_id).file_key in storage


def test_serializer_can_open_document_theo_document_read(setup, db, world, client_as):  # noqa: F811
    world_, a1, _, _ = setup
    cid = make_contract(a1, world_.emp["a2"])["id"]
    assert a1.get(f"{CT_URL}/{cid}").json()["data"]["can_open_document"] is True
    # a3 chỉ có labor_contract (không document.read)
    grant_all(world_, "a3", template=False)
    a3 = client_as(world_.actor("a3"))
    data = a3.get(f"{CT_URL}/{cid}").json()["data"]
    assert data["document_id"] > 0 and data["can_open_document"] is False


def _load_script():
    root = pathlib.Path(__file__).resolve().parents[2]   # host: gốc repo (có backend/); container: /app
    path = next(p for p in (root / "backend" / "scripts", root / "scripts")
                if (p / "backfill_hdld_van_ban_luu_tru.py").exists()) / "backfill_hdld_van_ban_luu_tru.py"
    spec = importlib.util.spec_from_file_location("backfill_hdld_cr629", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_script_bu_dry_run_khong_ghi_chay_hai_lan_moi_hd_mot_van_ban(setup, db):
    world, a1, _, _ = setup
    ids = [make_contract(a1, world.emp[k])["id"] for k in ("a2", "a3")]
    db.query(LaborContract).update({"document_id": 0})   # như HĐ có trước CR này
    db.query(Document).update({"is_deleted": True})   # dọn văn bản cũ khỏi tầm nhìn (id SQLite không tái dùng)
    db.commit()
    script = _load_script()
    old = db.query(Document).count()

    assert script.run(db, dry_run=True)["pending"] == 2
    assert db.query(Document).count() == old
    first = script.run(db)
    assert first["created"] == 2 and first["failed"] == 0
    second = script.run(db)
    assert second["created"] == 0 and second["synced"] == 2
    assert db.query(Document).count() == old + 2
    assert all(db.get(LaborContract, i).document_id for i in ids)

    removed = script.run(db, soft_delete_all=True)
    assert removed["removed"] == 2
    assert all(d.is_deleted for d in db.query(Document).all())
    assert all(db.get(LaborContract, i).document_id == 0 for i in ids)
