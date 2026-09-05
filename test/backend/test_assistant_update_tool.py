"""Tầng GHI có xác nhận của Trợ lý AI (CR-218) — `propose_document_update` + `confirm_update`.

Nguyên tắc phải giữ: token chỉ là TỜ ĐỀ XUẤT có hạn dùng, không phải giấy thông hành.
Bộ test này ép đủ các cửa: thiếu quyền / ngoài phạm vi ghi / sai trạng thái / trường
ngoài whitelist / token hết hạn / token của người khác / phiếu đổi trạng thái giữa hai
bước — và happy path phải ghi qua ĐÚNG service của form (update_pr / update_sr /
update_request) chứ không setattr thẳng.
"""
import json
import time

import pytest
from fastapi import HTTPException

from app.modules.assistant import tools as T
from app.modules.assistant.tools.update_tool import (
    CONFIRM_TTL_SECONDS,
    _fernet,
    confirm_update,
)
from app.modules.purchase_request.model import PurchaseRequest
from app.modules.survey_request.model import SurveyRequest
from app.modules.user.model import User


def _tao_ycmh(db, seed, created_by, status="draft", purpose="Mua giấy A4"):
    pr = PurchaseRequest(code="YCMH-TEST-1", company_id=seed.company_id,
                         department_id=seed.dept_id, purpose=purpose,
                         need_date="2026-09-01", note="Ghi chú cũ", status=status,
                         created_by=created_by, updated_by=created_by)
    db.add(pr)
    db.commit()
    db.refresh(pr)
    return pr


def _tao_ycbg(db, seed, created_by, status="draft"):
    sr = SurveyRequest(code="YCBG-TEST-1", company_id=seed.company_id,
                       purpose="Khảo sát giá nhãn", status=status,
                       created_by=created_by, updated_by=created_by)
    db.add(sr)
    db.commit()
    db.refresh(sr)
    return sr


def _de_xuat(db, seed, args):
    user = db.get(User, seed.u_req_id)
    return T.run_tool(db, user, "propose_document_update", args)


# ── propose_document_update ─────────────────────────────────────────────────────────────

def test_thieu_quyen_write_thi_tu_choi(db, seed, grant_role):
    """Có mỗi quyền ĐỌC vẫn không đề xuất sửa được — tool đòi đúng `entity.write`."""
    grant_role(seed.u_req_id, "purchase_request", scope="all", read=True)
    _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _de_xuat(db, seed, {"entity": "purchase_request", "code": "YCMH-TEST-1",
                              "changes": {"purpose": "Mua giấy A5"}})
    assert out.get("denied") is True
    assert "proposal" not in out


def test_ngoai_pham_vi_ghi_coi_nhu_khong_co(db, seed, grant_role):
    """Scope `own` mà phiếu của người khác -> 'Không tìm thấy', không lộ cả việc phiếu tồn tại."""
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    _tao_ycmh(db, seed, created_by=seed.u_nstm_id)
    out = _de_xuat(db, seed, {"entity": "purchase_request", "code": "YCMH-TEST-1",
                              "changes": {"purpose": "Mua giấy A5"}})
    assert "Không tìm thấy" in out["error"]


def test_sai_trang_thai_khong_de_xuat(db, seed, grant_role):
    """Phiếu đã gửi duyệt thì chặn ngay từ bước đề xuất — đừng để người dùng bấm rồi mới vỡ."""
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    _tao_ycmh(db, seed, created_by=seed.u_req_id, status="submitted")
    out = _de_xuat(db, seed, {"entity": "purchase_request", "code": "YCMH-TEST-1",
                              "changes": {"purpose": "Mua giấy A5"}})
    assert "trạng thái" in out["error"]
    assert "proposal" not in out


def test_truong_ngoai_whitelist_bi_chan(db, seed, grant_role):
    """YCBG không có `need_date` trong whitelist — model điền lạc trường phải bị chặn kèm
    danh sách trường hợp lệ, không được lẳng lặng bỏ qua trường lạ rồi sửa phần còn lại."""
    grant_role(seed.u_req_id, "survey_request", scope="own", read=True, write=True)
    _tao_ycbg(db, seed, created_by=seed.u_req_id)
    out = _de_xuat(db, seed, {"entity": "survey_request", "code": "YCBG-TEST-1",
                              "changes": {"purpose": "Mục đích mới",
                                          "need_date": "2026-09-10"}})
    assert "need_date" in out["error"]
    assert "proposal" not in out


def test_gia_tri_trung_thi_khong_co_gi_de_sua(db, seed, grant_role):
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    _tao_ycmh(db, seed, created_by=seed.u_req_id, purpose="Mua giấy A4")
    out = _de_xuat(db, seed, {"entity": "purchase_request", "code": "YCMH-TEST-1",
                              "changes": {"purpose": "  Mua giấy A4  "}})
    assert "trùng" in out["error"]


def test_de_xuat_thanh_cong_tra_proposal_va_token_dung_chu(db, seed, grant_role):
    """Happy path: khối `proposal` đủ hình cho FE + token Fernet buộc đúng người hỏi,
    và phiếu CHƯA bị đụng tới."""
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id, purpose="Mua giấy A4")
    out = _de_xuat(db, seed, {"entity": "purchase_request", "code": "ycmh-test-1",
                              "changes": {"purpose": "Mua giấy A5", "note": "Ghi chú cũ"}})

    assert out["status"] == "ready"
    assert out["total"] == 1                     # note trùng giá trị cũ -> bị loại khỏi đề xuất
    p = out["proposal"]
    assert p["kind"] == "update_proposal"
    assert p["code"] == "YCMH-TEST-1"
    assert p["changes"] == [{"field": "purpose", "label": "Mục đích mua hàng",
                             "old": "Mua giấy A4", "new": "Mua giấy A5"}]
    assert str(pr.id) in p["url"]
    assert "CHƯA bị sửa" in out["reminder"]

    payload = json.loads(_fernet().decrypt(p["confirm_token"].encode()))
    assert payload == {"u": seed.u_req_id, "e": "purchase_request", "id": pr.id,
                       "ch": {"purpose": "Mua giấy A5"}}
    db.refresh(pr)
    assert pr.purpose == "Mua giấy A4"           # đề xuất xong phiếu vẫn nguyên


# ── confirm_update ──────────────────────────────────────────────────────────────────────

def test_xac_nhan_ghi_qua_dung_service_cua_form(db, seed, grant_role):
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _de_xuat(db, seed, {"entity": "purchase_request", "code": "YCMH-TEST-1",
                              "changes": {"purpose": "Mua giấy A5",
                                          "need_date": "2026-09-15"}})

    user = db.get(User, seed.u_req_id)
    done = confirm_update(db, user, out["proposal"]["confirm_token"])
    assert done["code"] == "YCMH-TEST-1"
    assert set(done["updated_fields"]) == {"Mục đích mua hàng", "Ngày cần hàng"}

    db.refresh(pr)
    assert pr.purpose == "Mua giấy A5"
    assert pr.need_date == "2026-09-15"
    assert pr.updated_by == seed.u_req_id        # update_pr chạy thật -> audit trail có chủ


def test_xac_nhan_ycbg_cung_ghi_duoc(db, seed, grant_role):
    grant_role(seed.u_req_id, "survey_request", scope="own", read=True, write=True)
    sr = _tao_ycbg(db, seed, created_by=seed.u_req_id)
    out = _de_xuat(db, seed, {"entity": "survey_request", "code": "YCBG-TEST-1",
                              "changes": {"note": "Cần báo giá trước cuối tháng"}})

    confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    db.refresh(sr)
    assert sr.note == "Cần báo giá trước cuối tháng"


def test_token_cua_nguoi_khac_thi_403(db, seed, grant_role):
    """Người B cầm token của người A bấm xác nhận -> 403, kể cả khi B cũng có quyền write."""
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    grant_role(seed.u_nstm_id, "purchase_request", scope="all", read=True, write=True)
    _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _de_xuat(db, seed, {"entity": "purchase_request", "code": "YCMH-TEST-1",
                              "changes": {"purpose": "Mua giấy A5"}})

    with pytest.raises(HTTPException) as ei:
        confirm_update(db, db.get(User, seed.u_nstm_id), out["proposal"]["confirm_token"])
    assert ei.value.status_code == 403


def test_token_het_han_hoac_rac_thi_400(db, seed, grant_role):
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    user = db.get(User, seed.u_req_id)

    payload = json.dumps({"u": user.id, "e": "purchase_request", "id": pr.id,
                          "ch": {"purpose": "Mua giấy A5"}})
    het_han = _fernet().encrypt_at_time(
        payload.encode(), int(time.time()) - CONFIRM_TTL_SECONDS - 5).decode()
    with pytest.raises(HTTPException) as ei:
        confirm_update(db, user, het_han)
    assert ei.value.status_code == 400
    assert "hết hạn" in ei.value.detail

    with pytest.raises(HTTPException) as rac:
        confirm_update(db, user, "token-rác-không-phải-fernet")
    assert rac.value.status_code == 400


def test_phieu_doi_trang_thai_giua_hai_buoc_thi_chan(db, seed, grant_role):
    """Đề xuất lúc Nháp nhưng phiếu được duyệt TRƯỚC khi người dùng bấm -> phải kiểm lại
    và chặn 400, token không phải giấy thông hành."""
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    out = _de_xuat(db, seed, {"entity": "purchase_request", "code": "YCMH-TEST-1",
                              "changes": {"purpose": "Mua giấy A5"}})

    pr.status = "approved"
    db.commit()
    with pytest.raises(HTTPException) as ei:
        confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    assert ei.value.status_code == 400
    db.refresh(pr)
    assert pr.purpose == "Mua giấy A4"


def test_token_gia_mang_truong_ngoai_whitelist_van_bi_chan(db, seed, grant_role):
    """Whitelist phải kiểm LẠI ở bước xác nhận — token tự chế nhét `status` vào changes
    không được phép lọt qua dù chữ ký Fernet hợp lệ."""
    grant_role(seed.u_req_id, "purchase_request", scope="own", read=True, write=True)
    pr = _tao_ycmh(db, seed, created_by=seed.u_req_id)
    user = db.get(User, seed.u_req_id)

    gia = _fernet().encrypt(json.dumps({"u": user.id, "e": "purchase_request", "id": pr.id,
                                        "ch": {"status": "approved"}}).encode()).decode()
    with pytest.raises(HTTPException) as ei:
        confirm_update(db, user, gia)
    assert ei.value.status_code == 400
    db.refresh(pr)
    assert pr.status == "draft"


def test_yctt_print_texts_gop_cau_khong_sua_va_mo_ca_khi_da_duyet(db, seed, grant_role):
    """YCTT: 3 câu bản in sửa được cả khi Đã duyệt (CR-149), và chỉ đè khóa người dùng đổi —
    câu không nhắc tới phải giữ nguyên sau khi gộp."""
    from app.modules.payment_request.model import PaymentRequest
    from app.modules.payment_request.service import parse_print_texts

    grant_role(seed.u_req_id, "payment_request", scope="own", read=True, write=True)
    req = PaymentRequest(code="YCTT-TEST-1", supplier_code="NX", supplier_name="Nhà Xuất NX",
                         company_id=seed.company_id, status="approved",
                         print_texts=json.dumps({"content": "Thanh toán đợt 1",
                                                 "transfer": "CK theo hợp đồng"},
                                                ensure_ascii=False),
                         created_by=seed.u_req_id, updated_by=seed.u_req_id)
    db.add(req)
    db.commit()
    db.refresh(req)

    out = _de_xuat(db, seed, {"entity": "payment_request", "code": "YCTT-TEST-1",
                              "changes": {"print_line_desc": "Diễn giải mới cho bảng"}})
    assert out["status"] == "ready"              # approved vẫn đề xuất được vì chỉ đụng bản in

    confirm_update(db, db.get(User, seed.u_req_id), out["proposal"]["confirm_token"])
    db.refresh(req)
    assert parse_print_texts(req.print_texts) == {
        "content": "Thanh toán đợt 1",           # câu không sửa giữ nguyên
        "line_desc": "Diễn giải mới cho bảng",
        "transfer": "CK theo hợp đồng",
    }
    assert req.status == "approved"
