"""ai-CR-169 — đợt 1 chống mất dữ liệu do xóa cứng (doc/erp/20-ra-soat-xoa-cung.md §2).

Bảy mục, mỗi mục một cụm bài kiểm:
1. Hợp đồng: chỉ xóa được khi chưa ký và chưa hiệu lực; xóa nhiều kiểm cả lô.
2. Hoàn tác lô nhập: phiếu đã đổi trạng thái / đã phát sinh thì từ chối cả lượt; phiếu có xóa mềm thì xóa mềm.
3. Công nợ đã trả / đã có YCTT trỏ tới thì không gỡ được (sửa đợt giao).
4. NCC / sản phẩm còn chứng từ tham chiếu thì không xóa, chỉ ngưng dùng; lấy một dòng qua phạm vi.
5. Nhập CSV hành động «xóa» phải qua `before_delete` như nút xóa.
6. Bot vận hành: lan can SQL chặn hẳn DELETE (bài ở `test_agent_hub.py`).
7. Xóa cha + tệp đính kèm là MỘT giao dịch (không commit trước khi cha bị xóa).
"""
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile

from app.modules.attachment.model import FileLink, StoredFile
from app.modules.contract import controller as contract_ctl
from app.modules.contract.model import Contract
from app.modules.payable import service as pay_service
from app.modules.payable.model import Payable
from app.modules.payment_request.model import PaymentRequest, PaymentRequestLine
from app.modules.purchase_order.model import PurchaseOrder
from app.modules.user.model import User


def _user(db, seed):
    return db.get(User, seed.u_req_id)


def _attach(db, entity: str, entity_id: int) -> int:
    sf = StoredFile(filename="a.pdf", file_key=f"k/{entity}/{entity_id}", created_by=1, updated_by=1)
    db.add(sf)
    db.flush()
    db.add(FileLink(file_id=sf.id, entity=entity, entity_id=entity_id, created_by=1, updated_by=1))
    db.flush()
    return sf.id


# ──────────────────────────── 1. Hợp đồng ────────────────────────────
def _contract(db, seed, code, **kw):
    c = Contract(code=code, party_type="supplier", party_code="NX", company_id=seed.company_id,
                 created_by=seed.u_req_id, updated_by=seed.u_req_id, **kw)
    db.add(c)
    db.commit()
    return c


def test_hop_dong_chi_xoa_duoc_khi_chua_ky_chua_hieu_luc(db, seed, cap_quyen):
    user = _user(db, seed)
    cap_quyen(user.id, "contract", scope="all", read=True, delete=True)
    draft = _contract(db, seed, "HD-NHAP", signed=False, status="active", start_date="2099-01-01")
    signed = _contract(db, seed, "HD-KY", signed=True, status="active")
    running = _contract(db, seed, "HD-HL", signed=False, status="active", start_date="2020-01-01")
    expired = _contract(db, seed, "HD-HET", signed=False, status="expired")
    _attach(db, "contract", signed.id)

    for c, word in ((signed, "đã ký"), (running, "đang hiệu lực"), (expired, "đã hết hạn")):
        with pytest.raises(HTTPException) as e:
            contract_ctl.delete_(c.id, db, user)
        assert e.value.status_code == 400 and word in e.value.detail and c.code in e.value.detail
    #  Hợp đồng đã ký còn nguyên, tệp đính kèm còn nguyên.
    assert db.get(Contract, signed.id) is not None
    assert db.query(FileLink).filter(FileLink.entity == "contract", FileLink.entity_id == signed.id).count() == 1

    contract_ctl.delete_(draft.id, db, user)
    assert db.get(Contract, draft.id) is None


def test_hop_dong_xoa_nhieu_mot_dong_sai_la_khong_xoa_dong_nao(db, seed, cap_quyen):
    user = _user(db, seed)
    cap_quyen(user.id, "contract", scope="all", read=True, delete=True)
    a = _contract(db, seed, "HD-A", signed=False, status="cancelled")
    b = _contract(db, seed, "HD-B", signed=True, status="active")
    c = _contract(db, seed, "HD-C", signed=False, status="active")   # chưa ký, không đặt ngày -> nháp

    with pytest.raises(HTTPException) as e:
        contract_ctl.bulk_delete_contracts(f"{a.id},{b.id},{c.id}", db, user)
    assert e.value.status_code == 400 and "HD-B" in e.value.detail and "HD-A" not in e.value.detail
    assert db.query(Contract).filter(Contract.id.in_([a.id, b.id, c.id])).count() == 3

    contract_ctl.bulk_delete_contracts(f"{a.id},{c.id}", db, user)
    assert db.query(Contract).filter(Contract.id.in_([a.id, c.id])).count() == 0
    assert db.get(Contract, b.id) is not None


# ──────────────────────────── 2. Hoàn tác lô nhập ────────────────────────────
def test_hoan_tac_lo_tu_choi_khi_phieu_da_doi_trang_thai_va_khong_xoa_phieu_nao(db):
    from test_import_documents import _PR, _batch, _wb
    from app.modules.import_tool import doc_import, service
    from app.modules.import_tool.model import ImportMode, ImportStatus
    from app.modules.purchase_request.model import PurchaseRequest

    wb = _wb(_PR, [{"code": "PYC-A", "product_name": "SP A", "qty": 1},
                   {"code": "PYC-B", "product_name": "SP B", "qty": 2}])
    b = _batch(db, _PR, ImportMode.APPLY)
    doc_import.run(db, b, wb, apply=True)
    pa = db.query(PurchaseRequest).filter(PurchaseRequest.code == "PYC-A").one()
    pb = db.query(PurchaseRequest).filter(PurchaseRequest.code == "PYC-B").one()
    pb.status = "submitted"          # đã gửi duyệt sau khi nhập
    db.commit()

    res = service.revert_batch(db, b, user_id=1)
    assert res["ok"] is False
    assert "PYC-B" in res["message"] and "trạng thái đã đổi" in res["message"] and "PYC-A" not in res["message"]
    #  Không phiếu nào bị đụng — kể cả PYC-A còn nháp — và lô vẫn DONE.
    db.expire_all()
    assert pa.is_deleted is False and pb.is_deleted is False
    assert b.status == ImportStatus.DONE


def test_hoan_tac_lo_tu_choi_khi_ycbg_da_co_phuong_an(db):
    from test_import_documents import _batch, _wb
    from app.modules.import_tool import doc_import, service
    from app.modules.import_tool.model import ImportModule, ImportMode
    from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine, SurveyRequestOption

    m = ImportModule.SURVEY_REQUEST
    wb = _wb(m, [{"code": "YCBG-X", "requester": "A", "requirement_detail": "TSKT", "request_qty": 1}])
    b = _batch(db, m, ImportMode.APPLY)
    doc_import.run(db, b, wb, apply=True)
    sr = db.query(SurveyRequest).filter(SurveyRequest.code == "YCBG-X").one()
    line = db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sr.id).one()
    db.add(SurveyRequestOption(survey_request_line_id=line.id, supplier_code="NX", created_by=1, updated_by=1))
    db.commit()

    res = service.revert_batch(db, b, user_id=1)
    assert res["ok"] is False and "YCBG-X" in res["message"] and "đã có phương án" in res["message"]
    assert db.query(SurveyRequest).filter(SurveyRequest.code == "YCBG-X").count() == 1


def test_hoan_tac_lo_tu_choi_khi_ycmh_da_co_don_mua_hang(db):
    from test_import_documents import _PR, _batch, _wb
    from app.modules.import_tool import doc_import, service
    from app.modules.import_tool.model import ImportMode

    wb = _wb(_PR, [{"code": "PYC-DON", "product_name": "SP", "qty": 1}])
    b = _batch(db, _PR, ImportMode.APPLY)
    doc_import.run(db, b, wb, apply=True)
    db.add(PurchaseOrder(code="PO-1", pr_code="PYC-DON", status="draft", created_by=1, updated_by=1))
    db.commit()

    res = service.revert_batch(db, b, user_id=1)
    assert res["ok"] is False and "PYC-DON" in res["message"] and "đã có đơn mua hàng" in res["message"]


# ──────────────────────────── 3. Công nợ đã trả ────────────────────────────
def _payable(db, ref_id: int, **kw) -> Payable:
    p = Payable(source_type="goods", ref_type="delivery", ref_id=ref_id, po_code="PO-X", invoice_no="HD-1",
                total=1000, created_by=1, updated_by=1, **kw)
    db.add(p)
    db.commit()
    return p


def test_cong_no_da_tra_thi_khong_go_duoc_lan_giao(db):
    p = _payable(db, 11, paid_amount=400)
    with pytest.raises(HTTPException) as e:
        pay_service.remove(db, "goods", 11)
    assert e.value.status_code == 400 and "đã trả" in e.value.detail and "Hủy / điều chỉnh thanh toán" in e.value.detail
    assert db.get(Payable, p.id) is not None


def test_cong_no_co_yctt_tro_toi_thi_khong_go_duoc(db):
    p = _payable(db, 12, paid_amount=0)
    req = PaymentRequest(code="YCTT-1", status="draft", created_by=1, updated_by=1)
    db.add(req)
    db.flush()
    db.add(PaymentRequestLine(request_id=req.id, payable_id=p.id, created_by=1, updated_by=1))
    db.commit()
    with pytest.raises(HTTPException) as e:
        pay_service.remove(db, "goods", 12)
    assert e.value.status_code == 400 and "yêu cầu thanh toán" in e.value.detail
    assert db.get(Payable, p.id) is not None


def test_cong_no_chua_tra_chua_co_yctt_van_go_duoc(db):
    p = _payable(db, 13, paid_amount=0)
    pay_service.remove(db, "goods", 13)
    db.commit()
    assert db.get(Payable, p.id) is None


# ──────────────────────────── 4. NCC / sản phẩm đang dùng ────────────────────────────
def test_ncc_con_chung_tu_thi_khong_xoa_chi_ngung_dung(db, seed, cap_quyen):
    from app.modules.supplier import controller as sup_ctl
    from app.modules.supplier.model import Supplier

    user = _user(db, seed)
    cap_quyen(user.id, "supplier", scope="all", read=True, delete=True)
    used = Supplier(code="NCC-DUNG", name="Đang có đơn", is_active=True, created_by=1, updated_by=1)
    db.add(used)
    db.add(PurchaseOrder(code="PO-NX", supplier_code="NCC-DUNG", status="draft", created_by=1, updated_by=1))
    db.add(Contract(code="HD-NX", party_type="supplier", party_code="NCC-DUNG", created_by=1, updated_by=1))
    db.commit()

    with pytest.raises(HTTPException) as e:
        sup_ctl.delete_supplier(used.id, db, user)
    assert e.value.status_code == 400
    assert "đang được dùng ở 2 chứng từ" in e.value.detail and "ngưng dùng" in e.value.detail
    assert "đơn mua hàng" in e.value.detail and "hợp đồng" in e.value.detail
    assert db.get(Supplier, used.id) is not None

    #  Xóa nhiều: một NCC đang dùng + một NCC trống -> từ chối cả lô, không xóa NCC trống.
    free = Supplier(code="NCC-TRONG", name="Chưa ai dùng", is_active=True, created_by=1, updated_by=1)
    db.add(free)
    db.commit()
    with pytest.raises(HTTPException) as e:
        sup_ctl.bulk_delete_suppliers(f"{used.id},{free.id}", db, user)
    assert e.value.status_code == 400 and "NCC-DUNG" in e.value.detail
    assert db.get(Supplier, free.id) is not None

    sup_ctl.bulk_delete_suppliers(str(free.id), db, user)
    assert db.get(Supplier, free.id) is None


def test_ncc_lay_mot_dong_qua_pham_vi_khong_co_la_404(db, seed, cap_quyen):
    from app.modules.supplier import controller as sup_ctl

    user = _user(db, seed)
    cap_quyen(user.id, "supplier", scope="all", read=True, delete=True)
    with pytest.raises(HTTPException) as e:
        sup_ctl.delete_supplier(999_999, db, user)
    assert e.value.status_code == 404


def test_san_pham_con_chung_tu_thi_khong_xoa(db, seed, cap_quyen):
    from app.modules.product import controller as prod_ctl
    from app.modules.product.model import Product
    from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem

    user = _user(db, seed)
    cap_quyen(user.id, "product", scope="all", read=True, delete=True)
    sp = Product(code="SP-DUNG", name="Sản phẩm đang dùng", created_by=1, updated_by=1)
    free = Product(code="SP-TRONG", name="Sản phẩm trống", created_by=1, updated_by=1)
    pr = PurchaseRequest(code="PYC-SP", created_by=1, updated_by=1)
    db.add_all([sp, free, pr])
    db.flush()
    db.add(PurchaseRequestItem(pr_id=pr.id, product_code="SP-DUNG", product_name="x", created_by=1, updated_by=1))
    db.commit()

    with pytest.raises(HTTPException) as e:
        prod_ctl.delete_product(sp.id, db, user)
    assert e.value.status_code == 400
    assert "đang được dùng ở 1 chứng từ" in e.value.detail and "dòng yêu cầu mua hàng" in e.value.detail
    assert "ngưng dùng" in e.value.detail

    with pytest.raises(HTTPException) as e:
        prod_ctl.bulk_delete_products(f"{sp.id},{free.id}", db, user)
    assert e.value.status_code == 400
    assert db.get(Product, free.id) is not None and db.get(Product, sp.id) is not None

    prod_ctl.delete_product(free.id, db, user)
    assert db.get(Product, free.id) is None


# ──────────────────────────── 5. Nhập CSV hành động xóa ────────────────────────────
def _csv_import_endpoint(router):
    return next(r.endpoint for r in router.routes if r.path.endswith("/import/csv"))


def test_nhap_csv_xoa_phai_qua_before_delete(db, seed, cap_quyen):
    from app.modules.employee.model import Employee
    from app.modules.employee.position_controller import router as pos_router
    from app.modules.employee.position_model import JobPosition

    user = _user(db, seed)
    cap_quyen(user.id, "job_position", scope="all", read=True, write=True, delete=True)
    used = JobPosition(code="cv_dung", name="Chức vụ đang giữ", created_by=1, updated_by=1)
    free = JobPosition(code="cv_trong", name="Chức vụ trống", created_by=1, updated_by=1)
    db.add_all([used, free])
    db.flush()
    db.get(Employee, seed.emp_req_id).position_id = used.id
    db.commit()

    import_csv = _csv_import_endpoint(pos_router)

    def _upload(code: str):
        data = ("Mã chức vụ,Tên chức vụ,Đang dùng,Ghi chú,Hành động\n" + f"{code},x,1,,xóa\n").encode("utf-8")
        return UploadFile(file=BytesIO(data), filename="cv.csv")

    #  Chức vụ còn người giữ: dòng CSV «xóa» ăn đúng câu chặn của nút xóa, không xóa.
    with pytest.raises(HTTPException) as e:
        import_csv(file=_upload("cv_dung"), db=db, user=user)
    assert e.value.status_code == 400 and "đang có 1 hồ sơ" in e.value.detail
    db.rollback()
    assert db.get(JobPosition, used.id) is not None

    #  Chức vụ trống thì vẫn xóa được qua CSV như trước.
    import_csv(file=_upload("cv_trong"), db=db, user=user)
    assert db.get(JobPosition, free.id) is None


# ──────────────────────────── 7. Xóa cha + tệp là MỘT giao dịch ────────────────────────────
def _assert_no_commit_before_parent_gone(db, monkeypatch, model, oid: int, run) -> None:
    """Mọi lần `commit` trong lúc xóa đều phải xảy ra SAU khi cha đã bị gỡ khỏi phiên — tức tệp
    đính kèm không được commit riêng trước (trước đây `delete_attachments_for` tự commit)."""
    real_commit = db.commit
    seen: list[int] = []

    def spy():
        db.flush()   # phiên test không autoflush — đẩy phần chờ xuống rồi mới soi cha còn hay mất
        seen.append(db.query(model).filter(model.id == oid).count())
        real_commit()

    monkeypatch.setattr(db, "commit", spy)
    run()
    monkeypatch.setattr(db, "commit", real_commit)
    assert seen and all(n == 0 for n in seen), seen


def test_xoa_don_mua_hang_khong_commit_tep_truoc(db, seed, monkeypatch):
    from app.modules.purchase_order import service as po_service

    po = PurchaseOrder(code="PO-TEP", status="draft", created_by=1, updated_by=1)
    db.add(po)
    db.commit()
    _attach(db, "purchase_order", po.id)
    _assert_no_commit_before_parent_gone(db, monkeypatch, PurchaseOrder, po.id,
                                         lambda: po_service.delete_po(db, po.id, seed.u_req_id))
    assert db.query(FileLink).filter(FileLink.entity == "purchase_order", FileLink.entity_id == po.id).count() == 0


def test_xoa_phieu_khao_sat_khong_commit_tep_truoc(db, seed, monkeypatch):
    from app.modules.survey import service as sv_service
    from app.modules.survey.model import Survey

    sid = seed.sv_nhan_id
    _attach(db, "survey", sid)
    _assert_no_commit_before_parent_gone(db, monkeypatch, Survey, sid,
                                         lambda: sv_service.delete_survey(db, sid, seed.u_req_id))
    assert db.query(FileLink).filter(FileLink.entity == "survey", FileLink.entity_id == sid).count() == 0


def test_xoa_yctt_khong_commit_tep_truoc(db, seed, monkeypatch):
    from app.modules.payment_request import service as pr_service

    req = PaymentRequest(code="YCTT-TEP", status="draft", created_by=1, updated_by=1)
    db.add(req)
    db.commit()
    _attach(db, "payment_request", req.id)
    _assert_no_commit_before_parent_gone(db, monkeypatch, PaymentRequest, req.id,
                                         lambda: pr_service.delete_request(db, req.id, seed.u_req_id))


def test_xoa_hop_dong_khong_commit_tep_truoc(db, seed, cap_quyen, monkeypatch):
    user = _user(db, seed)
    cap_quyen(user.id, "contract", scope="all", read=True, delete=True)
    c = _contract(db, seed, "HD-TEP", signed=False, status="active")
    _attach(db, "contract", c.id)
    _assert_no_commit_before_parent_gone(db, monkeypatch, Contract, c.id,
                                         lambda: contract_ctl.delete_(c.id, db, user))
    assert db.query(FileLink).filter(FileLink.entity == "contract", FileLink.entity_id == c.id).count() == 0


def test_delete_block_reason_bang_lap(db, seed):
    """Luật nháp / chưa hiệu lực của hợp đồng, soi từng nhánh."""
    today = "2026-10-10"

    def mk(**kw):
        return SimpleNamespace(**{"signed": False, "status": "active", "start_date": "", **kw})

    assert contract_ctl.delete_block_reason(mk(), today) == ""
    assert contract_ctl.delete_block_reason(mk(status="cancelled"), today) == ""
    assert contract_ctl.delete_block_reason(mk(start_date="2026-12-01"), today) == ""
    assert contract_ctl.delete_block_reason(mk(start_date="2026-10-10"), today) == "đang hiệu lực"
    assert contract_ctl.delete_block_reason(mk(signed=True), today) == "đã ký"
    assert contract_ctl.delete_block_reason(mk(status="expired"), today) == "đã hết hạn"
    assert contract_ctl.delete_block_reason(mk(status="liquidated"), today) == "đã thanh lý"
