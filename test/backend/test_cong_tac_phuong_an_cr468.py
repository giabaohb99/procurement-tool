"""bao-CR-468 — CÔNG TẮC cụm phương án (báo giá) của Yêu cầu mua hàng.

Luật phải giữ:
1. Mặc định TẮT. Nguồn là màn Cấu hình hệ thống (khóa `pr_options_enabled`, lưu DB) rồi mới
   tới `.env` — bật/tắt không cần deploy.
2. TẮT thì mọi đường GHI của cụm bị từ chối (gắn / sửa / chốt / gom đơn theo phương án), và
   «Phương án 0» KHÔNG được sinh thêm — kể cả đường sinh bù chạy kèm lúc đọc phiếu.
3. TẮT nhưng ĐỌC vẫn mở: phương án đã lưu trên phiếu cũ vẫn xem được, không mất dấu.
4. Chi tiết phiếu trả cờ `options_enabled` để giao diện ẩn đúng hai chỗ — người dùng thường
   không có quyền đọc cấu hình nên không tự hỏi được.
"""
import json

import pytest
from fastapi import HTTPException

from app.core import app_settings
from app.modules.purchase_request import controller as C
from app.modules.purchase_request import option_service as OS
from app.modules.purchase_request.model import PurchaseRequest, PurchaseRequestItem
from app.modules.purchase_request.schema import PROptionManualIn
from app.modules.setting import service as setting_service


def _data(resp):
    return json.loads(resp.body)["data"]


def _make_pr(db, seed, code="PYC-CR468"):
    pr = PurchaseRequest(code=code, company_id=seed.company_id, department="Thu mua",
                         requester="NV001", request_date="2026-09-23", status="dispatched")
    db.add(pr)
    db.flush()
    item = PurchaseRequestItem(pr_id=pr.id, product_code="SP01", product_name="Giấy A4",
                               unit="ram", qty=10, price=50_000, assignee="NV002")
    db.add(item)
    db.flush()
    return pr, item


def test_mac_dinh_tat(db):
    # Không đặt gì trong DB thì rơi về `.env`, và mặc định của `.env` là TẮT — cụm phương án
    # là luồng làm việc MỚI, hệ đang chạy không được tự có thêm quy trình sau một lần deploy.
    assert OS.options_enabled() is False


def test_khai_bao_du_hai_noi_de_bat_tat_duoc():
    # Phải có mặt ở CẢ HAI nơi: sổ đăng ký cấu hình hiệu lực (đọc được, có đường lui về
    # `.env`) và danh sách trường của màn Cấu hình hệ thống (có ô để bấm). Thiếu nơi nào thì
    # công tắc hoặc không đọc được, hoặc không ai bật tắt được bằng tay.
    assert app_settings.REGISTRY["pr_options_enabled"] == ("bool", "PR_OPTIONS_ENABLED")
    field = next(f for f in setting_service.FIELDS if f["key"] == "pr_options_enabled")
    assert field["type"] == "bool" and field["group"] == "workflow" and field.get("hint")


def test_doc_qua_cau_hinh_hieu_luc_chu_khong_doc_thang_env(monkeypatch):
    # Đọc thẳng `.env` thì bật ở màn Cấu hình xong vẫn phải deploy mới ăn — mất đúng cái lợi
    # của công tắc.
    monkeypatch.setattr(app_settings, "get", lambda key: key == "pr_options_enabled")
    assert OS.options_enabled() is True
    monkeypatch.setattr(app_settings, "get", lambda key: False)
    assert OS.options_enabled() is False


def test_tat_thi_moi_duong_ghi_bi_tu_choi(db, seed, monkeypatch):
    pr, item = _make_pr(db, seed)
    monkeypatch.setattr(OS, "options_enabled", lambda: False)
    with pytest.raises(HTTPException) as e:
        OS.ensure_stage(pr)
    assert e.value.status_code == 400 and "đang TẮT" in e.value.detail


def test_tat_thi_khong_sinh_phuong_an_0(db, seed, monkeypatch):
    # Đường sinh bù chạy kèm lúc ĐỌC phiếu — để nguyên thì tắt công tắc xong hệ thống vẫn
    # lặng lẽ đẻ dữ liệu phương án mỗi lần có người mở một phiếu.
    pr, item = _make_pr(db, seed, code="PYC-CR468-B")
    monkeypatch.setattr(OS, "options_enabled", lambda: False)
    assert OS.ensure_option_zero(db, pr, [item]) == 0
    assert OS.options_of(db, item.id) == []

    monkeypatch.setattr(OS, "options_enabled", lambda: True)
    assert OS.ensure_option_zero(db, pr, [item]) == 1


def test_tat_van_doc_duoc_phuong_an_da_luu(db, seed, monkeypatch):
    # Bật → gắn một phương án → tắt: số liệu cũ phải còn nguyên và vẫn đọc ra được.
    pr, item = _make_pr(db, seed, code="PYC-CR468-C")
    monkeypatch.setattr(OS, "options_enabled", lambda: True)
    OS.create_manual(db, pr, item, PROptionManualIn(
        supplier_code="NCC01", supplier_name="NCC Thử", snap_vat=8), user_id=1)
    db.flush()
    truoc = len(OS.options_of(db, item.id))
    assert truoc >= 1

    monkeypatch.setattr(OS, "options_enabled", lambda: False)
    assert len(OS.options_of(db, item.id)) == truoc


def test_chi_tiet_phieu_tra_co_cho_giao_dien(db, seed, cap_quyen, monkeypatch):
    from app.modules.user.model import User

    pr, _ = _make_pr(db, seed, code="PYC-CR468-D")
    cap_quyen(seed.u_nstm_id, "purchase_request", scope="all", read=True, write=True)
    user = db.get(User, seed.u_nstm_id)

    monkeypatch.setattr(OS, "options_enabled", lambda: False)
    assert _data(C.get_pr(pr.id, db=db, user=user))["options_enabled"] is False

    monkeypatch.setattr(OS, "options_enabled", lambda: True)
    assert _data(C.get_pr(pr.id, db=db, user=user))["options_enabled"] is True
