"""duoc-CR-659 — nút «Ban hành» của bản lưu trữ HĐLĐ ở phân hệ Văn bản = KÝ hợp đồng gốc.

`/api/documents/{id}/permissions` trả thêm `archive_contract_id` + `can_issue_archive`. Cờ chỉ bật khi HĐ chưa xóa, đang
Nháp và người xem ghi được HĐ trong phạm vi `labor_contract`. Bấm nút = gọi `/api/labor-contracts/{id}/transition`
(→ Đã ký); đồng bộ đưa văn bản sang «Có hiệu lực» và cờ tắt.
"""
from app.core.labor_contract_codes import LaborContractStatus
from app.modules.document import model as doc_model
from app.modules.document.model import Document
from app.modules.labor_contract.model import LaborContract
from hdld_factory import client_as, storage  # noqa: F401
from test_hdld_ban_luu_tru_sua_duoc_cr640 import ctx  # noqa: F401

CT_URL = "/api/labor-contract" + "s"


def _perms(client, doc_id):
    return client.get(f"/api/documents/{doc_id}/permissions").json()["data"]


def test_nguoi_ghi_hdld_thay_nut_ban_hanh_khi_hd_con_nhap(ctx):
    perms = _perms(ctx["c"]["a1"], ctx["doc"].id)
    assert perms["is_archive"] is True
    assert perms["archive_contract_id"] == ctx["cid"]
    assert perms["can_issue_archive"] is True


def test_ban_hanh_ky_hd_goc_van_ban_co_hieu_luc_va_tat_nut(ctx):
    hr, db, d, cid = ctx["c"]["a1"], ctx["db"], ctx["doc"], ctx["cid"]
    r = hr.post(f"{CT_URL}/{cid}/transition", json={"to_status": int(LaborContractStatus.SIGNED), "date": "2026-10-22"})
    assert r.status_code == 200, r.text
    db.expire_all()
    assert int(db.get(LaborContract, cid).status) == int(LaborContractStatus.SIGNED)
    assert db.get(Document, d.id).status == doc_model.STATUS_EFFECTIVE
    assert _perms(hr, d.id)["can_issue_archive"] is False     # đã ký thì không còn nút


def test_chi_doc_hdld_khong_thay_nut_ban_hanh(ctx):
    """a2 có `document.write` nhưng chỉ ĐỌC HĐLĐ ⇒ không ký được nên không bày nút."""
    assert _perms(ctx["c"]["a2"], ctx["doc"].id)["can_issue_archive"] is False


def test_hd_da_xoa_mem_hoac_da_huy_khong_ban_hanh(ctx):
    hr, db, d, cid = ctx["c"]["a1"], ctx["db"], ctx["doc"], ctx["cid"]
    lc = db.get(LaborContract, cid)
    lc.status = int(LaborContractStatus.CANCELLED)
    db.commit()
    assert _perms(hr, d.id)["can_issue_archive"] is False
    lc.status, lc.is_deleted = int(LaborContractStatus.DRAFT), True
    db.commit()
    assert _perms(hr, d.id)["can_issue_archive"] is False


def test_van_ban_thuong_khong_co_hd_goc(ctx):
    clerk = ctx["c"]["a3"]          # văn thư, đủ quyền Văn bản
    r = clerk.post("/api/documents", json={"doc_type_id": ctx["thuong"].id, "company_id": ctx["world"].co["A"],
                                           "department_id": 0, "owner_employee_id": 0, "title": "Công văn thường"})
    assert r.status_code in (200, 201), r.text
    perms = _perms(clerk, r.json()["data"]["id"])
    assert perms["is_archive"] is False
    assert perms["archive_contract_id"] == 0 and perms["can_issue_archive"] is False
