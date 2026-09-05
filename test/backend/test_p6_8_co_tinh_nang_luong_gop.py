"""P6-8 (bao-CR-286) — cờ tính năng luồng gộp chứng từ (doc/erp/12 §P6-8).

Luật cần khóa:

1. Cờ TẮT: chặn CHỐT phương án mới + chặn tạo thẳng ĐMH (400 ở controller — FE ẩn nút
   chỉ là lớp lịch sự). Nhưng vẫn CHO bỏ chốt (gỡ dòng kẹt khóa) và vẫn CHO chọn
   phương án / tạo YCMH — đó chính là "về đúng hành vi cũ" của điều kiện đủ P6.
2. Ba payload (_out / _out_result / _out_process) phải mang `merged_flow_enabled`
   để FE ẩn/hiện nút theo backend, không tự bịa cờ riêng.
3. Cờ đọc qua `app_settings.get` (DB đè .env) — test chặn ở `app_settings.get`,
   KHÔNG ghi dòng tab_setting vào DB test (bài học test_stress_gui_thu_theo_hop_thu).
"""
import pytest
from fastapi import HTTPException

from app.core import app_settings
from app.core.config import settings
from app.modules.survey_request import controller, service
from app.modules.survey_request.model import (LS_CONFIRMED, SurveyRequest,
                                              SurveyRequestLine,
                                              SurveyRequestOption)
from app.modules.survey_request.schema import LineConfirmIn
from app.modules.user.model import User


def _sr(db, user_id: int, status: str = "survey_done", code: str = "YCBG-P68"):
    s = SurveyRequest(code=code, status=status, created_by=user_id)
    db.add(s)
    db.commit()
    return s


def _line(db, sid: int, **kw):
    ln = SurveyRequestLine(survey_request_id=sid, item_group="Thùng",
                           request_qty=kw.pop("request_qty", 5), **kw)
    db.add(ln)
    db.commit()
    return ln


def _opt(db, line_id: int, public_id: int = 1, chosen: bool = False, **kw):
    o = SurveyRequestOption(survey_request_line_id=line_id, public_id=public_id,
                            supplier_code=kw.pop("supplier", "NCC-A"),
                            is_chosen=chosen, **kw)
    db.add(o)
    db.commit()
    return o


@pytest.fixture
def tat_cong_tac(monkeypatch):
    monkeypatch.setattr(service, "merged_flow_enabled", lambda: False)


# ───────────────────────── dây điện của công tắc ─────────────────────────

def test_cong_tac_dang_ky_du_ba_tang():
    """REGISTRY (app_settings) + .env dự phòng + màn Cấu hình hệ thống phải cùng có
    key `merged_flow_enabled` — thiếu tầng nào là công tắc thành nút trang trí."""
    assert app_settings.REGISTRY.get("merged_flow_enabled") == ("bool", "MERGED_FLOW_ENABLED")
    assert settings.MERGED_FLOW_ENABLED is True, "mặc định phải BẬT — luồng P6-3/P6-4 đang chạy dev"
    from app.modules.setting.service import FIELDS
    field = next((f for f in FIELDS if f["key"] == "merged_flow_enabled"), None)
    assert field is not None and field["group"] == "workflow" and field["type"] == "bool"


def test_doc_cong_tac_qua_app_settings(monkeypatch):
    monkeypatch.setattr(app_settings, "get",
                        lambda key: {"merged_flow_enabled": False}.get(key))
    assert service.merged_flow_enabled() is False
    monkeypatch.setattr(app_settings, "get",
                        lambda key: {"merged_flow_enabled": "1"}.get(key))
    assert service.merged_flow_enabled() is True


# ───────────────────────── cờ TẮT: chặn gì, tha gì ─────────────────────────

def test_tat_thi_chan_chot_moi(db, seed, tat_cong_tac):
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id)
    ln = _line(db, s.id)
    _opt(db, ln.id, chosen=True)

    with pytest.raises(HTTPException) as e:
        controller.confirm_line_option_(s.id, ln.id, LineConfirmIn(confirmed=True),
                                        db=db, user=user)
    assert e.value.status_code == 400
    db.refresh(ln)
    assert ln.line_status == ""


def test_tat_van_cho_bo_chot(db, seed, tat_cong_tac):
    """Dòng đã chốt TRƯỚC khi tắt cờ không được kẹt khóa vĩnh viễn."""
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id)
    ln = _line(db, s.id, line_status=LS_CONFIRMED)
    o = _opt(db, ln.id, chosen=True)

    controller.confirm_line_option_(s.id, ln.id, LineConfirmIn(confirmed=False),
                                    db=db, user=user)

    db.refresh(ln)
    db.refresh(o)
    assert ln.line_status == "" and o.is_chosen, "bỏ chốt chỉ mở khóa, giữ lựa chọn"


def test_tat_thi_chan_tao_don_thang(db, seed, tat_cong_tac):
    from app.modules.purchase_order.model import PurchaseOrder
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id)
    ln = _line(db, s.id, line_status=LS_CONFIRMED)
    _opt(db, ln.id, chosen=True)

    with pytest.raises(HTTPException) as e:
        controller.create_pos_(s.id, background_tasks=None, db=db, up=(user, {}))
    assert e.value.status_code == 400
    assert db.query(PurchaseOrder).count() == 0


def test_tat_van_cho_chon_phuong_an(db, seed, tat_cong_tac):
    """Hành vi cũ phải còn nguyên: chọn phương án (để tạo YCMH) không dính cờ."""
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id)
    ln = _line(db, s.id)
    o = _opt(db, ln.id)

    controller.choose_option_(s.id, ln.id, o.id, db=db, user=user)

    db.refresh(o)
    assert o.is_chosen


# ───────────────────────── payload mang cờ cho FE ─────────────────────────

@pytest.mark.parametrize("bat", [True, False])
def test_ca_ba_payload_mang_co(db, seed, monkeypatch, bat):
    monkeypatch.setattr(service, "merged_flow_enabled", lambda: bat)
    user = db.get(User, seed.u_req_id)
    s = _sr(db, user.id)
    _line(db, s.id)

    assert controller._out(db, s)["merged_flow_enabled"] is bat
    assert controller._out_result(db, s)["merged_flow_enabled"] is bat
    assert controller._out_process(db, s)["merged_flow_enabled"] is bat
