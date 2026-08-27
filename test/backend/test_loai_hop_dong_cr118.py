"""CR-118 — bộ giá trị `contract_type` phải cố định và chỉ nhận MÃ tiếng Anh.

Trước CR-118 cột này là VARCHAR(50) chữ tự do: `frontend/src/config/cruds.tsx` khai 3 giá
trị, `ContractDetail.tsx` khai 5, `frontend-v2` khai 5 (bộ khác), còn dữ liệu thật lưu bộ
thứ tư — kể cả bản gõ SAI "Hơp đồng nguyên tắc" (thiếu dấu nặng ở "Hợp") chiếm 42/179 dòng.
Hệ quả: lọc "Loại HĐ" ra 0 dòng, ô chọn mở lên trống trơn dù bản ghi có dữ liệu.
"""
import importlib.util
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.contract_types import CONTRACT_TYPE_LABEL, CONTRACT_TYPE_VALUES, CONTRACT_TYPES
from app.modules.contract.controller import list_contract_types
from app.modules.contract.schema import ContractCreate, ContractUpdate

# Nhãn tiếng Việt người dùng từng thấy trên giao diện — nay là giá trị KHÔNG hợp lệ.
_NHAN_CU = ["Mua bán", "Nguyên tắc", "Hợp đồng mua bán", "Hơp đồng nguyên tắc"]


def test_bo_ma_la_ascii_khong_lot_tieng_viet_vao_cot_luu():
    """Cột lưu MÃ; lọt tiếng Việt vào đây là quay lại đúng cái mớ vừa dọn."""
    assert len(CONTRACT_TYPES) == 7
    for t in CONTRACT_TYPES:
        assert t["value"].isascii() and t["value"].islower(), t
        assert t["label"], t
    assert len(CONTRACT_TYPE_VALUES) == len(CONTRACT_TYPES)   # không mã nào trùng
    assert len(set(CONTRACT_TYPE_LABEL.values())) == len(CONTRACT_TYPES)  # không nhãn nào trùng


def test_chi_nhan_ma_trong_bo_co_dinh():
    for code in sorted(CONTRACT_TYPE_VALUES):
        assert ContractCreate(contract_type=code).contract_type == code


def test_bo_trong_van_qua_vi_chua_phan_loai_khong_phai_loi():
    # Bắt buộc trường này là chặn luôn việc lập HĐ lúc chưa biết xếp vào loại nào.
    assert ContractCreate(contract_type="").contract_type == ""
    assert ContractCreate().contract_type == ""
    assert ContractUpdate().contract_type is None


@pytest.mark.parametrize("xau", _NHAN_CU)
def test_nhan_tieng_viet_cu_bi_chan_ca_luc_tao_lan_luc_sua(xau):
    """Chặn ở CẢ HAI schema. Chỉ chặn `Create` thì màn sửa vẫn ghi chữ tự do vào lại."""
    with pytest.raises(ValidationError):
        ContractCreate(contract_type=xau)
    with pytest.raises(ValidationError):
        ContractUpdate(contract_type=xau)


def test_endpoint_meta_tra_dung_bo_cho_giao_dien_dung_o_chon():
    """`frontend-v2` nạp ô "Loại hợp đồng" từ đây thay vì khai tĩnh — lệch là 422."""
    res = list_contract_types(user=None)
    body = json.loads(res.body)
    assert body["success"] is True
    assert body["data"] == CONTRACT_TYPES


# ── Migration đổi dữ liệu ───────────────────────────────────────────────────────
def _nap_migration():
    duong_dan = Path(__file__).resolve().parents[2] / "migrations" / "versions" / \
        "a1c7e5d90f42_chuan_hoa_contract_type.py"
    if not duong_dan.exists():   # chạy trong container: /app/test/backend + /app/migrations
        duong_dan = Path("/app/migrations/versions/a1c7e5d90f42_chuan_hoa_contract_type.py")
    spec = importlib.util.spec_from_file_location("mig_cr118", duong_dan)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_migration_nhan_ra_ban_go_sai_dau_va_ban_thieu_tien_to():
    """Khớp theo DẠNG CHUẨN HÓA (bỏ dấu, bỏ tiền tố "hợp đồng") chứ không khớp chuỗi tuyệt
    đối. Khớp tuyệt đối thì riêng 42 dòng "Hơp đồng nguyên tắc" đã lọt lưới, còn 2 dòng
    "Nguyên tắc" (không có tiền tố) cũng lọt."""
    mig = _nap_migration()
    doi = lambda s: mig._MAP.get(mig._norm(s))   # noqa: E731

    assert doi("Hợp đồng nguyên tắc") == "principle"
    assert doi("Hơp đồng nguyên tắc") == "principle"    # bản gõ sai, 42 dòng
    assert doi("Nguyên tắc") == "principle"             # không tiền tố, 2 dòng
    assert doi("HD vận chuyển") == "transport"
    assert doi("  hợp  đồng   MUA BÁN ") == "purchase"  # thừa khoảng trắng + hoa thường lẫn lộn
    assert doi("Hợp đồng gia công") is None             # không đoán bừa, giữ nguyên + in log


def test_chieu_xuong_cua_migration_khop_nhan_chuan_dang_dung():
    """Danh sách nhãn trong migration là bản chép tay của `contract_types.py` (migration
    không được import mã ứng dụng — mã đổi thì migration cũ phải chạy y như lúc viết).
    Lệch nhau là downgrade ghi ra nhãn khác với nhãn giao diện đang hiện."""
    mig = _nap_migration()
    assert mig._LABEL == CONTRACT_TYPE_LABEL
