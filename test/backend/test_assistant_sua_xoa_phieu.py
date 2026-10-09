"""AI-0006 (đại ca chốt 09/10/2026): Trợ lý / bot SỬA thêm dòng hàng YCMH-YCBG + ngày, loại
nghỉ của đơn nghỉ phép, và XÓA phiếu nháp của CHÍNH mình — đều qua thẻ đề xuất + nút xác nhận.

Luật xóa phải giữ: đủ CẢ BA — chính người hỏi lập · còn Nháp / Bị trả lại · có quyền `delete`
và phiếu trong phạm vi xóa. Thiếu một là KHÔNG có đề xuất, chỉ có câu giải thích + link.
Đề nghị thanh toán và phiếu hỗ trợ không bao giờ xóa qua trợ lý.
"""
import json
from datetime import date

import pytest
from fastapi import HTTPException

from app.modules.assistant import tools as T
from app.modules.assistant.tools.update_tool import _fernet, confirm_update
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.survey_request.model import SurveyRequest, SurveyRequestLine
from app.modules.user.model import User


def _tao_ycmh(db, seed, created_by, status="draft", code="YCMH-AI6-1"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, department_id=seed.dept_id,
                         purpose="Mua văn phòng phẩm", need_date="2026-10-20", status=status,
                         created_by=created_by, updated_by=created_by)
    db.add(pr)
    db.flush()
    db.add_all([
        PurchaseRequestItem(pr_id=pr.id, product_name="Giấy A4", qty=10, unit="ram",
                            required_date="2026-10-20", created_by=created_by),
        PurchaseRequestItem(pr_id=pr.id, product_name="Bút bi", qty=20, unit="cây",
                            required_date="2026-10-20", created_by=created_by),
    ])
    db.commit()
    db.refresh(pr)
    return pr


def _dong_ycmh(db, pr_id):
    return (db.query(PurchaseRequestItem).filter(PurchaseRequestItem.pr_id == pr_id)
            .order_by(PurchaseRequestItem.id).all())


def _goi(db, user_id, tool, args):
    return T.run_tool(db, db.get(User, user_id), tool, args)


# ── Sửa dòng hàng ────────────────────────────────────────────────────────────────────────

def test_sua_dong_ycmh_them_bo_doi_so_luong_roi_xac_nhan(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "purchase_request", "code": "YCMH-AI6-1",
        "line_ops": [{"op": "set_qty", "line_no": 1, "qty": 15},
                     {"op": "remove", "line_no": 2},
                     {"op": "add", "product_name": "Kẹp giấy", "qty": 5, "unit": "hộp"}]})
    assert out["status"] == "ready"
    nhan = [c["new"] for c in out["proposal"]["changes"]]
    assert nhan == ["SL 15 ram", "Bỏ dòng", "Kẹp giấy · SL 5 hộp"]
    assert len(_dong_ycmh(db, pr.id)) == 2                    # đề xuất xong phiếu vẫn nguyên

    done = confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    assert "Dòng hàng" in done["updated_fields"]
    dong = _dong_ycmh(db, pr.id)
    assert [(d.product_name, float(d.qty)) for d in dong] == [("Giấy A4", 15.0), ("Kẹp giấy", 5.0)]
    assert dong[1].required_date == "2026-10-20"              # dòng mới mang ngày cần hàng đầu phiếu


def test_bam_lai_the_cu_thi_khong_them_trung_dong(db, seed, cap_quyen):
    """ai-CR-153 — tải lại trang web rồi bấm lại thẻ thêm dòng (token còn hạn 15 phút) từng thêm trùng dòng."""
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "purchase_request", "code": "YCMH-AI6-1",
        "line_ops": [{"op": "add", "product_name": "Kẹp giấy", "qty": 5, "unit": "hộp"}]})
    token = out["proposal"]["confirm_token"]
    user = db.get(User, seed.u_req_id)
    confirm_update(db, user, token)
    assert len(_dong_ycmh(db, pr.id)) == 3
    with pytest.raises(HTTPException) as ei:
        confirm_update(db, user, token)
    assert ei.value.status_code == 409 and "đã dùng rồi" in ei.value.detail
    assert len(_dong_ycmh(db, pr.id)) == 3


def test_phieu_bi_sua_xen_giua_hai_buoc_thi_409(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "purchase_request", "code": "YCMH-AI6-1", "changes": {"purpose": "Mua giấy in"}})
    pr.note = "người khác vừa ghi chú"
    db.commit()
    with pytest.raises(HTTPException) as ei:
        confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    assert ei.value.status_code == 409
    db.refresh(pr)
    assert pr.purpose == "Mua văn phòng phẩm"


def test_sua_dong_so_dong_khong_ton_tai_bi_chan(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "purchase_request", "code": "YCMH-AI6-1",
        "line_ops": [{"op": "remove", "line_no": 7}]})
    assert "không có dòng số 7" in out["error"]
    assert "proposal" not in out


def test_sua_dong_khong_duoc_bo_het_dong(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "purchase_request", "code": "YCMH-AI6-1",
        "line_ops": [{"op": "remove", "line_no": 1}, {"op": "remove", "line_no": 2}]})
    assert "ít nhất một dòng" in out["error"]


def test_so_luong_am_hoac_bang_khong_bi_chan(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    _tao_ycmh(db, seed, created_by=seed.u_req_id)
    for qty in (0, -3, "abc", True):
        out = _goi(db, seed.u_req_id, "propose_document_update", {
            "entity": "purchase_request", "code": "YCMH-AI6-1",
            "line_ops": [{"op": "set_qty", "line_no": 1, "qty": qty}]})
        assert "lớn hơn 0" in out["error"], qty


def test_yctt_khong_sua_dong_qua_tro_ly(db, seed, cap_quyen):
    from app.modules.payment_request.model import PaymentRequest

    cap_quyen(seed.u_req_id, "payment_request", scope="own", read=True, write=True)
    db.add(PaymentRequest(code="YCTT-AI6-1", supplier_code="NX", company_id=seed.company_id,
                          status="draft", created_by=seed.u_req_id))
    db.commit()
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "payment_request", "code": "YCTT-AI6-1",
        "line_ops": [{"op": "remove", "line_no": 1}]})
    assert "chỉ YCMH và YCBG" in out["error"]


def test_dong_da_bi_xoa_giua_hai_buoc_thi_400(db, seed, cap_quyen):
    """Token nêu dòng theo ID: dòng đó biến mất trước lúc bấm thì chặn, không đoán dòng khác."""
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "purchase_request", "code": "YCMH-AI6-1",
        "line_ops": [{"op": "set_qty", "line_no": 2, "qty": 30}]})
    db.delete(_dong_ycmh(db, pr.id)[1])
    db.commit()
    with pytest.raises(HTTPException) as ei:
        confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    assert ei.value.status_code == 409          # ai-CR-153: dấu trạng thái lệch chặn trước cả bước dựng dòng
    assert [float(r.qty) for r in _dong_ycmh(db, pr.id)] == [10.0]


def test_token_gia_mang_thao_tac_dong_sai_hinh_bi_chan(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    gia = _fernet().encrypt(json.dumps({"u": seed.u_req_id, "e": "purchase_request", "id": pr.id,
                                        "ch": {}, "ln": [{"op": "drop_table"}]}).encode()).decode()
    with pytest.raises(HTTPException) as ei:
        confirm_update(db, db.get(User, seed.u_req_id), gia)
    assert ei.value.status_code == 400
    assert len(_dong_ycmh(db, pr.id)) == 2


def test_sua_dong_ycbg_doi_so_luong(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "survey_request", scope="own", read=True, write=True)
    sr = SurveyRequest(code="YCBG-AI6-1", company_id=seed.company_id, purpose="Khảo sát",
                       status="draft", created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(sr)
    db.flush()
    db.add(SurveyRequestLine(survey_request_id=sr.id, requirement_detail="Nhãn decal",
                             request_qty=100, uom="tờ", created_by=seed.u_req_id))
    db.commit()
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "survey_request", "code": "YCBG-AI6-1",
        "line_ops": [{"op": "set_qty", "line_no": 1, "qty": 250}]})
    confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    dong = db.query(SurveyRequestLine).filter(SurveyRequestLine.survey_request_id == sr.id).one()
    assert float(dong.request_qty) == 250.0


# ── Sửa đơn nghỉ phép ───────────────────────────────────────────────────────────────────

def _tao_don_nghi(db, seed, status=1):
    from app.modules.leave.catalog_model import LeaveType
    from app.modules.leave.request_model import LeaveRequest, LeaveRequestLine

    phep = LeaveType(code="ANNUAL", name="Phép năm", counts_balance=False, is_active=True,
                     sort_order=1)
    om = LeaveType(code="SICK", name="Nghỉ ốm", counts_balance=False, is_active=True, sort_order=2)
    db.add_all([phep, om])
    db.flush()
    don = LeaveRequest(code="NP-AI6-1", company_id=seed.company_id, department_id=seed.dept_id,
                       employee_id=seed.emp_req_id, leave_type_id=phep.id,
                       from_date=date(2026, 10, 12), to_date=date(2026, 10, 12), total_days=1,
                       status=status, reason="Việc riêng", created_by=seed.u_req_id)
    db.add(don)
    db.flush()
    db.add(LeaveRequestLine(request_id=don.id, leave_type_id=phep.id, days=1, sort_order=1))
    db.commit()
    db.refresh(don)
    return don, phep, om


def test_sua_don_nghi_doi_ngay_va_loai_nghi(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    don, _, om = _tao_don_nghi(db, seed)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "leave_request", "code": "NP-AI6-1",
        "changes": {"to_date": "2026-10-13", "leave_type": "nghỉ ốm"}})
    assert out["status"] == "ready"
    assert {c["field"]: c["new"] for c in out["proposal"]["changes"]} == {
        "to_date": "2026-10-13", "leave_type": "Nghỉ ốm"}

    confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    db.refresh(don)
    assert don.to_date == date(2026, 10, 13)
    assert don.leave_type_id == om.id


def test_sua_ly_do_don_nghi(db, seed, cap_quyen):
    """ai-CR-151 — ca thật 09/10: «chỉnh lý do của đơn ngày t2 tuần sau, lý do là đi khám nghĩa vụ vòng 1 địa
    phương» → bot trả «em không sửa được». Lý do nay sửa được, qua đúng thẻ xác nhận."""
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    don, _, _ = _tao_don_nghi(db, seed)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "leave_request", "code": "NP-AI6-1",
        "changes": {"reason": "đi khám nghĩa vụ vòng 1 địa phương"}})
    assert out["status"] == "ready"
    change = out["proposal"]["changes"][0]
    assert change["field"] == "reason" and change["old"] == "Việc riêng"
    assert change["new"] == "đi khám nghĩa vụ vòng 1 địa phương"
    db.refresh(don)
    assert don.reason == "Việc riêng"                       # chưa bấm thì chưa ghi
    confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    db.refresh(don)
    assert don.reason == "đi khám nghĩa vụ vòng 1 địa phương"
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "leave_request", "code": "NP-AI6-1", "changes": {"reason": "  "}})
    assert "reason rỗng" in out["error"]


def test_loai_nghi_la_khong_tu_lui_ve_phep_nam(db, seed, cap_quyen):
    """Tool soạn nháp lùi về phép năm khi không rõ loại; SỬA đơn thì không được đoán."""
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    _tao_don_nghi(db, seed)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "leave_request", "code": "NP-AI6-1", "changes": {"leave_type": "nghỉ mát"}})
    assert "Không có loại nghỉ" in out["error"]
    assert "proposal" not in out


def test_den_ngay_truoc_tu_ngay_bi_chan(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    _tao_don_nghi(db, seed)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "leave_request", "code": "NP-AI6-1", "changes": {"to_date": "2026-10-01"}})
    assert "sau đến ngày" in out["error"]


def test_don_nghi_cho_duyet_khong_sua(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, write=True)
    _tao_don_nghi(db, seed, status=2)
    out = _goi(db, seed.u_req_id, "propose_document_update", {
        "entity": "leave_request", "code": "NP-AI6-1", "changes": {"to_date": "2026-10-13"}})
    assert "chỉ sửa được khi đơn Nháp" in out["error"]


# ── Xóa phiếu ───────────────────────────────────────────────────────────────────────────

def test_xoa_ycmh_nhap_cua_minh_qua_xac_nhan(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, delete=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "purchase_request", "code": "ycmh-ai6-1"})
    assert out["status"] == "ready"
    p = out["proposal"]
    assert p["action"] == "delete" and p["kind"] == "update_proposal"
    db.refresh(pr)
    assert pr.is_deleted is False                             # đề xuất chưa xóa gì

    done = confirm_update(db, db.get(User, seed.u_req_id), p["confirm_token"])
    assert done["deleted"] is True and done["url"] == ""
    db.refresh(pr)
    assert pr.is_deleted is True


def test_thieu_quyen_delete_thi_tu_choi(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "purchase_request", "code": "YCMH-AI6-1"})
    assert out.get("denied") is True
    assert "proposal" not in out


def test_phieu_nguoi_khac_lap_thi_chi_tra_link(db, seed, cap_quyen):
    """Có quyền delete phạm vi `all` vẫn KHÔNG xóa hộ phiếu người khác qua trợ lý."""
    cap_quyen(seed.u_req_id, "purchase_request", scope="all", read=True, delete=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_nstm_id)
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "purchase_request", "code": "YCMH-AI6-1"})
    assert "người khác lập" in out["error"]
    assert out["url"].endswith(f"/{pr.id}")
    assert "proposal" not in out


def test_phieu_da_gui_duyet_thi_khong_xoa_va_tra_link(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, delete=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id, status="submitted")
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "purchase_request", "code": "YCMH-AI6-1"})
    assert "không xóa được" in out["error"]
    assert "liên hệ người có quyền" in out["error"]
    assert out["url"].endswith(f"/{pr.id}")
    assert "proposal" not in out


def test_de_nghi_thanh_toan_khong_bao_gio_xoa(db, seed, cap_quyen):
    from app.modules.payment_request.model import PaymentRequest

    cap_quyen(seed.u_req_id, "payment_request", scope="own", read=True, delete=True)
    req = PaymentRequest(code="YCTT-AI6-1", supplier_code="NX", company_id=seed.company_id,
                         status="draft", created_by=seed.u_req_id)
    db.add(req)
    db.commit()
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "payment_request", "code": "YCTT-AI6-1"})
    assert "dính tiền" in out["error"]
    assert out["url"].endswith(f"/{req.id}")
    assert "proposal" not in out


def test_phieu_doi_trang_thai_truoc_luc_bam_xoa_thi_chan(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, delete=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "purchase_request", "code": "YCMH-AI6-1"})
    pr.status = "submitted"
    db.commit()
    with pytest.raises(HTTPException) as ei:
        confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    assert ei.value.status_code == 400
    db.refresh(pr)
    assert pr.is_deleted is False


def test_token_xoa_cua_nguoi_khac_thi_403(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, delete=True)
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="all", read=True, delete=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "purchase_request", "code": "YCMH-AI6-1"})
    with pytest.raises(HTTPException) as ei:
        confirm_update(db, db.get(User, seed.u_nstm_id), out["proposal"]["confirm_token"])
    assert ei.value.status_code == 403
    db.refresh(pr)
    assert pr.is_deleted is False


def test_quyen_delete_bi_thu_hoi_truoc_luc_bam_thi_403(db, seed, cap_quyen):
    from app.core.auth import perm_cache_clear
    from app.modules.user.model import UserRole

    role = cap_quyen(seed.u_req_id, "purchase_request", scope="own", read=True, delete=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "purchase_request", "code": "YCMH-AI6-1"})
    db.query(UserRole).filter(UserRole.role_id == role.id).delete()
    db.commit()
    perm_cache_clear(seed.u_req_id)
    with pytest.raises(HTTPException) as ei:
        confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    assert ei.value.status_code == 403
    db.refresh(pr)
    assert pr.is_deleted is False


def test_xoa_ycbg_nhap_cua_minh(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "survey_request", scope="own", read=True, delete=True)
    sr = SurveyRequest(code="YCBG-AI6-2", company_id=seed.company_id, purpose="Khảo sát",
                       status="rejected", created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(sr)
    db.commit()
    sid = sr.id
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "survey_request", "code": "YCBG-AI6-2"})
    confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    assert db.get(SurveyRequest, sid) is None


def test_xoa_don_nghi_nhap_cua_minh(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "leave_request", scope="own", read=True, delete=True)
    don, _, _ = _tao_don_nghi(db, seed)
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "leave_request", "code": "NP-AI6-1"})
    confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    db.refresh(don)
    assert don.is_deleted is True


def _tao_viec(db, seed, creator_emp, status=1):
    from app.modules.work.model import WorkList, WorkListMember
    from app.modules.work.task_model import WorkTask

    lst = WorkList(name="Dự án AI6", company_id=0)
    db.add(lst)
    db.flush()
    db.add(WorkListMember(list_id=lst.id, employee_id=seed.emp_req_id))
    t = WorkTask(title="Gọi NCC giấy", list_id=lst.id, status=status,
                 creator_employee_id=creator_emp)
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def test_xoa_viec_du_an_minh_tao_theo_ten(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "work_task", scope="all", read=True, delete=True)
    t = _tao_viec(db, seed, creator_emp=seed.emp_req_id)
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "work_task", "code": "gọi ncc giấy"})
    assert out["status"] == "ready"
    confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    db.refresh(t)
    assert t.deleted_at is not None


def test_viec_du_an_nguoi_khac_tao_thi_khong_xoa(db, seed, cap_quyen):
    cap_quyen(seed.u_req_id, "work_task", scope="all", read=True, delete=True)
    t = _tao_viec(db, seed, creator_emp=seed.emp_nstm_id)
    out = _goi(db, seed.u_req_id, "propose_document_delete",
               {"entity": "work_task", "code": str(t.id)})
    assert "người khác tạo" in out["error"]
    assert "proposal" not in out
