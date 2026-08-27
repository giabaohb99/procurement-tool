"""CR-058 — VAT theo dòng: nhập số tự do nhưng phải nằm trong 0 ≤ VAT < 100.

Trước CR-058 ô VAT trên UI là <select> khoá cứng vài mức (0/2/4/6/8/10 ở khảo sát,
0/5/8/10 ở YCMH) nên BE không cần chặn. Giờ người dùng gõ tay được, mà cột DB là
Numeric(5,2): nhập 1000 thì MySQL báo lỗi tràn (500) thay vì 422 tử tế, còn nhập 150
thì lưu êm và làm sai tiền. Bộ test này khoá cận trên/dưới ở tầng schema — nơi duy nhất
chặn thật, vì UI chỉ là tiện lợi và API gọi thẳng vẫn qua mặt được.
"""

import pytest
from pydantic import ValidationError

from app.modules.purchase_order.schema import POItemIn
from app.modules.purchase_request.schema import PRItemIn
from app.modules.supplier.schema import SupplierCreate, SupplierUpdate
from app.modules.survey.schema import ProductLineIn

# (tên schema, class, tên field VAT, các field bắt buộc khác của schema đó)
SCHEMA_VAT = [
    ("ĐMH — dòng hàng", POItemIn, "vat", {}),
    ("YCMH — dòng hàng", PRItemIn, "vat_pct", {"product_name": "Thùng carton"}),
    ("Khảo sát — phương án", ProductLineIn, "vat", {}),
]


@pytest.mark.parametrize("name,cls,field,step", SCHEMA_VAT)
def test_vat_hop_le(name, cls, field, step):
    """Mọi thuế suất thực tế đều qua được, kể cả mức không có trong <select> cũ."""
    for v in (0, 5, 8, 10, 3.5, 7.25, 99.99):
        obj = cls(**step, **{field: v})
        assert float(getattr(obj, field)) == pytest.approx(v), f"{name} — {v}"


@pytest.mark.parametrize("name,cls,field,step", SCHEMA_VAT)
def test_vat_tu_100_tro_len_bi_chan(name, cls, field, step):
    """Yêu cầu của khách là "< 100%" — 100 cũng KHÔNG hợp lệ."""
    for v in (100, 100.01, 150, 1000):
        with pytest.raises(ValidationError):
            cls(**step, **{field: v})


@pytest.mark.parametrize("name,cls,field,step", SCHEMA_VAT)
def test_vat_am_bi_chan(name, cls, field, step):
    for v in (-0.01, -8):
        with pytest.raises(ValidationError):
            cls(**step, **{field: v})


@pytest.mark.parametrize("name,cls,field,step", SCHEMA_VAT)
def test_vat_mac_dinh_bang_0(name, cls, field, step):
    """Không gửi VAT thì vẫn tạo được dòng (dòng chưa có giá) — mặc định 0."""
    assert float(getattr(cls(**step), field)) == 0


# ── NCC: VAT mặc định lưu dạng TỈ LỆ, không phải % ──────────────────────────────

def test_vat_ncc_la_ti_le_duoi_1():
    """`supplier.vat` là tỉ lệ (0.08 = 8%) — chặn dưới 1 chính là chặn dưới 100%."""
    assert SupplierCreate(name="NCC A", vat=0.08).vat == pytest.approx(0.08)
    assert SupplierCreate(name="NCC A").vat == pytest.approx(0.08)   # mặc định 8%
    assert SupplierUpdate(vat=0.1).vat == pytest.approx(0.1)


def test_vat_ncc_go_nham_theo_phan_tram_bi_chan():
    """Gõ 8 (ý là 8%) vào ô tỉ lệ = 800% — phải bị chặn, không lưu êm rồi sai tiền."""
    for v in (1, 8, 100):
        with pytest.raises(ValidationError):
            SupplierCreate(name="NCC A", vat=v)
        with pytest.raises(ValidationError):
            SupplierUpdate(vat=v)
