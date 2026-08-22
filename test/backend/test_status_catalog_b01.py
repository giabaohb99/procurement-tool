"""B-01 / QĐ-9 — khung khai báo bộ mã cố định dùng chung.

QĐ-9 (22/08/2026) chốt: mọi cột trạng thái của Thu mua lưu MÃ chuỗi tiếng Anh, đúng khuôn
CR-118. B-01 dựng khung `app/core/status_catalog.py` để chín đợt sau khai vào một chỗ, thay
cho việc mỗi phân hệ tự khai một tệp rồi mỗi giao diện chép tay lại một bản.

Tệp này kiểm ba thứ: khung tự bắt được lỗi khai sai, `contract_type` chuyển sang khung mới mà
API không đổi hình dạng (bài thử của khung), và bản TypeScript sinh ra khớp với backend.
"""
import pytest

from app.core.contract_types import (CONTRACT_TYPE_LABEL, CONTRACT_TYPE_SET,
                                     CONTRACT_TYPE_VALUES, CONTRACT_TYPES)
from app.core.status_catalog import Code, CodeSet, all_sets, get
from scripts.gen_status_ts import out_path, render


# --- khung tự bắt lỗi khai sai --------------------------------------------

def test_khai_trung_ma_thi_no_ngay_luc_dung():
    """Trùng `value` là lỗi câm: bản khai sau đè bản trước ở dict nhãn, không ai biết."""
    with pytest.raises(ValueError, match="trùng value"):
        CodeSet("x", "X", [Code("a", "A"), Code("b", "B"), Code("a", "A lần hai")])


def test_khai_trung_sort_order_thi_no_ngay_luc_dung():
    """Thứ tự không toàn phần thì `next_value` trả về tùy hên xui — chặn từ lúc khai."""
    with pytest.raises(ValueError, match="sort_order trùng"):
        CodeSet("x", "X", [Code("a", "A", 1), Code("b", "B", 1)])


def test_bo_khong_co_thu_tu_thi_de_sort_order_0_het_van_hop_le():
    """Loại hợp đồng, loại chứng từ... không có chuỗi tiến trình — giữ nguyên thứ tự khai."""
    cs = CodeSet("x", "X", [Code("a", "A"), Code("b", "B"), Code("c", "C")])
    assert cs.ordered_values == ("a", "b", "c")


# --- sort_order / is_terminal / is_exception ------------------------------

def _chuoi_tien_do() -> CodeSet:
    """Dựng đúng hình dạng `PROGRESS_ORDER` + `PROGRESS_EXCEPTIONS` của ĐMH sẽ dùng ở B-06."""
    return CodeSet("x", "Tiến độ", [
        Code("not_ordered", "Chưa đặt hàng", 1),
        Code("ordered", "Đã đặt hàng", 2),
        Code("received", "Đã nhận hàng", 3),
        Code("completed", "Hoàn thành", 4, is_terminal=True),
        Code("paused", "Tạm ngưng", is_exception=True),
        Code("cancelled", "Hủy đơn", is_exception=True),
    ])


def test_ordered_values_bo_ma_ngoai_le_ra_khoi_chuoi():
    assert _chuoi_tien_do().ordered_values == (
        "not_ordered", "ordered", "received", "completed")


def test_next_value_thay_cho_order_index_cong_mot():
    """Kiểu cũ `ORDER[ORDER.index(x) + 1]` ném ValueError với mã lạ và IndexError ở bước
    cuối — hai lỗi mà nơi gọi hầu như không ai bắt. Ở đây cả ba đều trả None."""
    cs = _chuoi_tien_do()
    assert cs.next_value("not_ordered") == "ordered"
    assert cs.next_value("received") == "completed"
    assert cs.next_value("completed") is None      # bước cuối
    assert cs.next_value("paused") is None         # ngoại lệ, ngoài chuỗi
    assert cs.next_value("ma_la") is None          # mã lạ
    assert cs.next_value(None) is None


def test_co_terminal_va_exception_thay_cho_viec_rai_chuoi_khap_service():
    cs = _chuoi_tien_do()
    assert cs.is_terminal("completed") and not cs.is_terminal("ordered")
    assert cs.is_exception("paused") and cs.is_exception("cancelled")
    assert not cs.is_exception("completed")
    assert not cs.is_terminal("ma_la") and not cs.is_exception("ma_la")


def test_validate_chan_ma_la_va_cho_qua_chuoi_rong():
    cs = _chuoi_tien_do()
    assert cs.validate("ordered") == "ordered"
    assert cs.validate("") == ""
    assert cs.validate(None) is None
    with pytest.raises(ValueError, match="không hợp lệ"):
        cs.validate("Đã đặt hàng")     # nhãn tiếng Việt KHÔNG phải mã
    with pytest.raises(ValueError, match="không được để trống"):
        cs.validate("", allow_blank=False)


# --- bài thử của khung: contract_type ------------------------------------

def test_contract_type_da_dang_ky_vao_so():
    assert get("contract_type") is CONTRACT_TYPE_SET
    assert "contract_type" in all_sets()


def test_ba_ten_cu_giu_nguyen_kieu_va_nguyen_thu_tu():
    """`/contracts/meta/types` trả thẳng `CONTRACT_TYPES` — đổi hình dạng là vỡ ô chọn."""
    assert CONTRACT_TYPES == [
        {"value": "purchase", "label": "Hợp đồng mua bán"},
        {"value": "principle", "label": "Hợp đồng nguyên tắc"},
        {"value": "economic", "label": "Hợp đồng kinh tế"},
        {"value": "template", "label": "Hợp đồng khuôn mẫu"},
        {"value": "transport", "label": "Hợp đồng vận chuyển"},
        {"value": "service", "label": "Hợp đồng dịch vụ"},
        {"value": "other", "label": "Khác"},
    ]
    # Chỉ hai khóa value/label, không có sort_order lọt ra API.
    assert all(set(t) == {"value", "label"} for t in CONTRACT_TYPES)
    assert CONTRACT_TYPE_VALUES == {
        "purchase", "principle", "economic", "template", "transport", "service", "other"}
    assert CONTRACT_TYPE_LABEL["principle"] == "Hợp đồng nguyên tắc"


def test_thong_diep_loi_giu_nguyen_dinh_dang_cu():
    """Giao diện đang hiện thẳng thông điệp này cho người dùng."""
    with pytest.raises(ValueError, match="Loại hợp đồng không hợp lệ: Mua bán"):
        CONTRACT_TYPE_SET.validate("Mua bán")


# --- bản TypeScript sinh ra phải khớp ------------------------------------

def test_ban_typescript_khop_voi_backend():
    """Cách H2 (`doc/erp/06` §5): sinh ra rồi lưu vào mã nguồn, CI so lại.

    Hỏng test này nghĩa là ai đó sửa bộ mã ở Python mà quên sinh lại, hoặc vá tay tệp .ts.
    Chạy: cd backend && python -m scripts.gen_status_ts

    Bỏ qua trong container api: ở đó `backend/` được mount thẳng thành `/app` nên không có
    `frontend-v2/`. Test này có nghĩa ở máy và ở CI, nơi có đủ repo.
    """
    ts = out_path()
    if ts is None:
        pytest.skip("Môi trường này không có frontend-v2/ (container api)")
    assert ts.read_text(encoding="utf-8") == render(), (
        f"{ts} lệch với backend — chạy lại: cd backend && python -m scripts.gen_status_ts")
