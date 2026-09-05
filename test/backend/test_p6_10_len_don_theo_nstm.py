"""bao-CR-290 — nút "Tạo đơn mua hàng" chỉ dành cho NSTM ĐƯỢC PHÂN PHỐI dòng.

Lỗi gốc: `create_pos_from_confirmed` chỉ lọc theo `line_status == confirmed`, nên bất
kỳ ai có quyền `purchase_order.create` mở được màn Xử lý khảo sát đều lên đơn được cho
dòng của NSTM khác — kể cả dòng họ không nhìn thấy trong khung xử lý (khung đó đã lọc
bằng `can_process_line`, còn nút lên đơn thì không).

Luật khóa ở đây:
1. Truyền `profile` thì CHỈ dòng `can_process_line` cho phép mới vào đơn.
2. Không dòng nào thuộc phần mình mà lại có dòng của người khác đang chờ -> 403 (khác
   400 "chưa có dòng nào chốt": hai tình huống này phải nói khác nhau, không thì NSTM
   tưởng người yêu cầu chưa chốt).
3. Quản lý/Admin TM (scope=all) vẫn lên đơn được cho mọi dòng.
4. Không truyền `profile` (đường gọi nội bộ / test cũ) thì giữ nguyên hành vi cũ.
"""
import pytest
from fastapi import HTTPException

from app.modules.purchase_order.model import POItem
from app.modules.survey_request import service
from app.modules.survey_request.model import (SurveyRequest, SurveyRequestLine,
                                              SurveyRequestOption)


def _profile(emp_code: str, scope: str = "proc") -> dict:
    return {"emp_code": emp_code, "employee_id": 0,
            "grants": [{"perms": {"survey_request": {"read": True, "scope": scope}}}]}


def _sr(db, code: str = "YCBG-C290"):
    s = SurveyRequest(code=code, status="survey_done")
    db.add(s)
    db.commit()
    return s


def _confirmed_line(db, sid: int, assignee: str, product_code: str, supplier: str):
    ln = SurveyRequestLine(survey_request_id=sid, item_group="Thùng", request_qty=5,
                           assignee=assignee, product_code=product_code)
    db.add(ln)
    db.commit()
    db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=1,
                               supplier_code=supplier, is_chosen=True))
    db.commit()
    service.confirm_line_option(db, sid, ln.id, True, user_id=1)
    return ln


def test_chi_len_don_cho_dong_minh_duoc_phan_phoi(db, seed):
    s = _sr(db)
    cua_toi = _confirmed_line(db, s.id, "NSTM-A", "VT-A", "NCC-A")
    cua_nguoi_khac = _confirmed_line(db, s.id, "NSTM-B", "VT-B", "NCC-B")

    pos = service.create_pos_from_confirmed(db, s.id, user_id=1, profile=_profile("NSTM-A"))

    assert len(pos) == 1 and pos[0].supplier_code == "NCC-A"
    it = db.query(POItem).filter(POItem.po_id == pos[0].id).one()
    assert it.product_code == "VT-A"
    db.refresh(cua_toi)
    db.refresh(cua_nguoi_khac)
    assert cua_toi.po_code == pos[0].code
    assert cua_nguoi_khac.po_code == "", "dòng của NSTM khác không được kéo vào đơn"


def test_toan_dong_cua_nguoi_khac_thi_403_chu_khong_phai_400(db, seed):
    s = _sr(db)
    _confirmed_line(db, s.id, "NSTM-B", "VT-B", "NCC-B")

    with pytest.raises(HTTPException) as e:
        service.create_pos_from_confirmed(db, s.id, user_id=1, profile=_profile("NSTM-A"))
    assert e.value.status_code == 403
    assert "nhân sự thu mua khác" in e.value.detail


def test_khong_co_dong_nao_chot_van_bao_400(db, seed):
    """Phiếu chưa ai chốt: câu báo phải là 'chưa chốt', đừng đổ cho phân phối."""
    s = _sr(db)
    ln = SurveyRequestLine(survey_request_id=s.id, item_group="Thùng", request_qty=5,
                           assignee="NSTM-B")
    db.add(ln)
    db.commit()
    db.add(SurveyRequestOption(survey_request_line_id=ln.id, public_id=1,
                               supplier_code="NCC-B", is_chosen=True))
    db.commit()   # CHỌN nhưng chưa CHỐT

    with pytest.raises(HTTPException) as e:
        service.create_pos_from_confirmed(db, s.id, user_id=1, profile=_profile("NSTM-A"))
    assert e.value.status_code == 400


def test_quan_ly_scope_all_len_don_duoc_cho_moi_dong(db, seed):
    s = _sr(db)
    _confirmed_line(db, s.id, "NSTM-A", "VT-A", "NCC-A")
    _confirmed_line(db, s.id, "NSTM-B", "VT-B", "NCC-B")

    pos = service.create_pos_from_confirmed(db, s.id, user_id=1,
                                            profile=_profile("QL-TM", scope="all"))

    assert {p.supplier_code for p in pos} == {"NCC-A", "NCC-B"}


def test_khong_truyen_profile_thi_giu_hanh_vi_cu(db, seed):
    """Đường gọi nội bộ không có hồ sơ quyền — không được tự chặn thành 403."""
    s = _sr(db)
    _confirmed_line(db, s.id, "NSTM-A", "VT-A", "NCC-A")
    _confirmed_line(db, s.id, "NSTM-B", "VT-B", "NCC-B")

    pos = service.create_pos_from_confirmed(db, s.id, user_id=1)

    assert len(pos) == 2
