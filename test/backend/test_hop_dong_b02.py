"""B-02 — `tab_contract.party_type` + `status` chuyển từ chữ tiếng Việt sang MÃ tiếng Anh.

Đợt thứ hai của kế hoạch đổ bê tông nền v2 (`doc/erp/15-do-be-tong-nen-v2.md` §3). Trước
đợt này, hai cột lưu thẳng "Nhà cung cấp" / "Hiệu lực" nên mọi chỗ so sánh đều là so chuỗi
tiếng Việt rải khắp backend lẫn hai bản giao diện: sửa một chữ trong nhãn là hỏng lặng lẽ
đúng chỗ không ai nhìn (`Contract.status != "Thanh lý"` ở cảnh báo và bảng điều khiển).

Cột `expiry` KHÔNG có trong CSDL — backend tính từ `end_date` — nhưng nó đi qua API *và*
làm giá trị tham số URL (`?expiry=Hết hạn`, tiếng Việt có dấu trong query string), nên
cũng chuyển sang mã trong đợt này.
"""
import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.status_codes import CONTRACT_EXPIRY, CONTRACT_PARTY_TYPE, CONTRACT_STATUS
from app.modules.contract.controller import _out, expiry_state
from app.modules.contract.model import Contract
from app.modules.contract.schema import ContractCreate, ContractUpdate

# Chữ người dùng từng thấy trên giao diện — nay là giá trị KHÔNG hợp lệ ở tầng ghi.
_NHAN_CU_PARTY = ["Nhà cung cấp", "Khách hàng", "Khác"]
_NHAN_CU_STATUS = ["Hiệu lực", "Hết hạn", "Thanh lý", "Hủy"]


# ── Bộ mã ───────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("bo", [CONTRACT_PARTY_TYPE, CONTRACT_STATUS, CONTRACT_EXPIRY])
def test_ma_la_ascii_thuong_va_khong_trung(bo):
    """Cột lưu MÃ. Lọt tiếng Việt vào đây là quay lại đúng cái mớ vừa dọn."""
    for c in bo.codes:
        assert c.value.isascii() and c.value.islower(), c
        assert c.label, c
    assert len(set(bo.values)) == len(bo.values)


def test_hai_bo_co_nhan_trung_nhau_nhung_ma_khac_nhau():
    """`CONTRACT_STATUS` và `CONTRACT_EXPIRY` cùng có nhãn "Hết hạn" — và đó là hai thứ
    KHÁC nhau: một cái người dùng đặt tay, một cái tính từ `end_date`. Gộp hai bộ lại (hoặc
    tra nhãn ngược ra mã) là lẫn ngay, nên test này giữ ranh giới đó cho rõ."""
    assert CONTRACT_STATUS.label_of("expired") == CONTRACT_EXPIRY.label_of("expired")
    assert "expiring_soon" not in CONTRACT_STATUS.values
    assert "liquidated" not in CONTRACT_EXPIRY.values


def test_ma_dung_trong_cau_truy_van_van_con_trong_bo():
    """`alert/controller.py` và `dashboard/controller.py` lọc bằng chuỗi trần
    `Contract.status != "liquidated"`. Đổi tên mã đó mà quên hai chỗ kia thì câu lọc vẫn
    chạy, chỉ là lọc nhầm — không có lỗi nào nổ ra để biết."""
    assert "liquidated" in CONTRACT_STATUS.values


# ── Tầng ghi ────────────────────────────────────────────────────────────────────
def test_chi_nhan_ma_trong_bo():
    for ma in CONTRACT_PARTY_TYPE.values:
        assert ContractCreate(party_type=ma).party_type == ma
    for ma in CONTRACT_STATUS.values:
        assert ContractCreate(status=ma).status == ma


def test_mac_dinh_la_ma_chu_khong_phai_nhan():
    c = ContractCreate()
    assert c.party_type == "supplier"
    assert c.status == "active"


@pytest.mark.parametrize("xau", _NHAN_CU_PARTY)
def test_nhan_party_type_cu_bi_chan_ca_luc_tao_lan_luc_sua(xau):
    """Chặn ở CẢ HAI schema. Chỉ chặn `Create` thì màn sửa vẫn ghi chữ tự do vào lại."""
    with pytest.raises(ValidationError):
        ContractCreate(party_type=xau)
    with pytest.raises(ValidationError):
        ContractUpdate(party_type=xau)


@pytest.mark.parametrize("xau", _NHAN_CU_STATUS)
def test_nhan_status_cu_bi_chan_ca_luc_tao_lan_luc_sua(xau):
    with pytest.raises(ValidationError):
        ContractCreate(status=xau)
    with pytest.raises(ValidationError):
        ContractUpdate(status=xau)


def test_khong_tu_dich_nhan_thanh_ma():
    """Cố ý KHÔNG nhận "Nhà cung cấp" rồi âm thầm đổi thành `supplier`: dịch hộ thì bản
    giao diện cũ chưa vá vẫn chạy được, và sẽ không ai vá nữa cho tới lúc nó hỏng vì lý do
    khác. Thà 422 ngay lúc deploy."""
    with pytest.raises(ValidationError):
        ContractCreate(party_type="Nhà cung cấp")


# ── Tầng đọc ────────────────────────────────────────────────────────────────────
def test_expiry_state_tra_ma_chu_khong_tra_chu():
    from datetime import date, timedelta
    hom_nay = date.today()
    assert expiry_state("") == ""
    assert expiry_state("khong-phai-ngay") == ""
    assert expiry_state((hom_nay - timedelta(days=1)).strftime("%Y-%m-%d")) == "expired"
    assert expiry_state((hom_nay + timedelta(days=10)).strftime("%Y-%m-%d")) == "expiring_soon"
    assert expiry_state((hom_nay + timedelta(days=90)).strftime("%Y-%m-%d")) == "valid"


def test_out_gui_kem_nhan_de_giao_dien_cu_khong_phai_khai_lai_bang_nhan():
    """Bản `frontend/` đóng băng vẫn chạy ở dev (service `web`); nó chỉ đổi CHỖ ĐỌC sang
    `*_label` chứ không dựng lại màn."""
    c = Contract(id=1, code="HD00001", party_type="supplier", party_code="NCC001",
                 party_name="Cty A", company_id=0, title="HĐ khung", contract_type="purchase",
                 start_date="2026-01-01", end_date="", signed=True, status="liquidated", note="")
    d = _out(c)
    assert d["party_type"] == "supplier" and d["party_type_label"] == "Nhà cung cấp"
    assert d["status"] == "liquidated" and d["status_label"] == "Thanh lý"
    assert d["contract_type_label"] == "Hợp đồng mua bán"
    # Không đặt hạn -> `expiry` rỗng, nhãn cũng rỗng (không bịa "Còn hạn").
    assert d["expiry"] == "" and d["expiry_label"] == ""


def test_ma_la_khong_lam_no_tang_doc_chi_la_khong_co_nhan():
    """Dữ liệu cũ chưa chạy migration (hoặc do nơi khác ghi vào) vẫn phải đọc được."""
    c = Contract(id=2, code="HD00002", party_type="Nhà cung cấp", status="Hiệu lực",
                 party_code="", party_name="", company_id=0, title="", contract_type="",
                 start_date="", end_date="", signed=False, note="")
    d = _out(c)
    assert d["party_type"] == "Nhà cung cấp"      # giữ nguyên, không nuốt mất
    assert d["party_type_label"] == ""            # nhưng không nhận ra -> không có nhãn


# ── Migration đổi dữ liệu ───────────────────────────────────────────────────────
_TEN_MIG = "c1d4a7b93e56_b02_chuan_hoa_contract_party_type_status.py"


def _nap_migration():
    duong_dan = Path(__file__).resolve().parents[2] / "migrations" / "versions" / _TEN_MIG
    if not duong_dan.exists():   # chạy trong container: /app/test/backend + /app/migrations
        duong_dan = Path("/app/migrations/versions") / _TEN_MIG
    spec = importlib.util.spec_from_file_location("mig_b02", duong_dan)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_migration_khop_theo_dang_chuan_hoa_chu_khong_khop_tuyet_doi():
    """Khớp tuyệt đối thì một dấu cách thừa hay một chữ hoa lệch là lọt lưới, và dòng đó
    nằm im trong CSDL với giá trị tiếng Việt cho tới lúc có người lọc không ra."""
    mig = _nap_migration()
    doi_pt = lambda s: mig._MAP_PARTY_TYPE.get(mig._norm(s))   # noqa: E731
    doi_st = lambda s: mig._MAP_STATUS.get(mig._norm(s))       # noqa: E731

    assert doi_pt("Nhà cung cấp") == "supplier"
    assert doi_pt("  NHÀ   cung cấp ") == "supplier"
    assert doi_pt("Khách hàng") == "customer"
    assert doi_st("Hiệu lực") == "active"
    assert doi_st("thanh ly") == "liquidated"      # bản gõ không dấu
    assert doi_st("Hủy") == "cancelled"
    assert doi_pt("Đối tác chiến lược") is None    # không đoán bừa, giữ nguyên + in log
    assert doi_st("Đang đàm phán") is None


def test_chieu_xuong_cua_migration_khop_nhan_chuan_dang_dung():
    """Bảng nhãn trong migration là bản CHÉP TAY của `status_codes.py` — migration không
    được import mã ứng dụng, vì mã đổi thì migration cũ vẫn phải chạy y như lúc viết.
    Lệch nhau là `downgrade()` ghi ra nhãn khác với nhãn giao diện đang hiện."""
    mig = _nap_migration()
    assert mig._LABEL_PARTY_TYPE == CONTRACT_PARTY_TYPE.labels
    assert mig._LABEL_STATUS == CONTRACT_STATUS.labels


def test_chay_xuoi_nguoc_xuoi_tra_ve_dung_tung_ky_tu(db):
    """QĐ-12 cho phép ĐỔI TẠI CHỖ (không thêm cột, không ghi hai nơi) với điều kiện
    `downgrade()` khôi phục byte-exact. Đây là chỗ kiểm điều kiện đó."""
    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    mig = _nap_migration()
    db.add_all([
        Contract(code="HD01", party_type="Nhà cung cấp", status="Hiệu lực"),
        Contract(code="HD02", party_type="Khách hàng", status="Thanh lý"),
        Contract(code="HD03", party_type="", status="Hủy"),          # rỗng: để nguyên hai chiều
        Contract(code="HD04", party_type="Đối tác lạ", status="Hết hạn"),  # không nhận ra
    ])
    db.commit()

    def doc():
        return {c.code: (c.party_type, c.status)
                for c in db.query(Contract).order_by(Contract.code).all()}

    ban_dau = doc()
    conn = db.connection()
    ctx = MigrationContext.configure(conn)

    with Operations.context(ctx):
        mig.upgrade()
    db.expire_all()
    sau_len = doc()
    assert sau_len["HD01"] == ("supplier", "active")
    assert sau_len["HD02"] == ("customer", "liquidated")
    assert sau_len["HD03"] == ("", "cancelled")
    # Giá trị không nhận ra thì GIỮ NGUYÊN — không đoán bừa trên dữ liệu thật.
    assert sau_len["HD04"] == ("Đối tác lạ", "expired")

    with Operations.context(ctx):
        mig.downgrade()
    db.expire_all()
    assert doc() == ban_dau

    with Operations.context(ctx):
        mig.upgrade()
    db.expire_all()
    assert doc() == sau_len
