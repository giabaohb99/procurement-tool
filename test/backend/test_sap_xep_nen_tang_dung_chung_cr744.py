"""duoc-CR-744 (đợt 2 / W1) - HAI LUẬT SẮP XẾP CHUNG của `apply_sort` và `apply_sort_from_request`.

1. Ô trống (NULL; cột chữ thì cả chuỗi rỗng / chỉ khoảng trắng) luôn xuống CUỐI ở cả hai chiều;
   cột số chỉ coi NULL là trống, số 0 là giá trị thật.
2. Luôn có khóa phụ `id` giảm dần: các dòng trùng giá trị không đổi chỗ giữa các trang. Đây là
   lỗi MẤT / LẶP dòng đo ngày 10/11/2026 (Hợp đồng xếp theo Trạng thái: 80/179 dòng không bao giờ
   hiện ra).

Bài chạy trên SQLite nhưng dựng đúng câu lệnh `CASE ... ORDER BY` mà MySQL cũng hiểu (không dùng
`NULLS LAST`).
"""
from sqlalchemy import BigInteger, Column, String
from sqlalchemy.orm import declarative_base
from starlette.datastructures import QueryParams

from app.core.base_controller import apply_sort, apply_sort_from_request
from app.modules.contract.model import Contract
from app.modules.payment_request.model import PaymentRequest


class _Req:
    def __init__(self, **params):
        self.query_params = QueryParams(params)


def _mk(db, code, supplier_name="", total=0, status="draft"):
    row = PaymentRequest(code=code, supplier_name=supplier_name, total=total, status=status)
    db.add(row)
    db.flush()
    return row


def _codes(query):
    return [r.code for r in query.all()]


# ── Luật 1: ô trống xuống cuối ───────────────────────────────────────────────────────────
def test_cot_chu_o_trong_xuong_cuoi_ca_hai_chieu(db):
    _mk(db, "A", "Bình")
    _mk(db, "B", "")
    _mk(db, "C", "An")
    _mk(db, "D", "   ")
    base = db.query(PaymentRequest)
    asc = _codes(apply_sort(base, PaymentRequest, "supplier_name", "asc"))
    desc = _codes(apply_sort(base, PaymentRequest, "supplier_name", "desc"))
    assert asc[:2] == ["C", "A"]
    assert desc[:2] == ["A", "C"]
    # hai ô trống ('' và chỉ khoảng trắng) đứng cuối ở CẢ HAI chiều
    assert set(asc[2:]) == {"B", "D"}
    assert set(desc[2:]) == {"B", "D"}


def test_cot_so_khong_coi_so_0_la_o_trong(db):
    _mk(db, "Z", total=0)
    _mk(db, "M", total=5)
    _mk(db, "N", total=3)
    base = db.query(PaymentRequest)
    assert _codes(apply_sort(base, PaymentRequest, "total", "asc")) == ["Z", "N", "M"]
    assert _codes(apply_sort(base, PaymentRequest, "total", "desc")) == ["M", "N", "Z"]


def test_cot_ngay_null_xuong_cuoi_khong_can_khai_nulls_last(db):
    db.add_all([
        Contract(code="HD-1", end_date="2030-01-01"),
        Contract(code="HD-2", end_date=""),
        Contract(code="HD-3", end_date="2027-05-05"),
    ])
    db.flush()
    base = db.query(Contract)
    assert [c.code for c in apply_sort(base, Contract, "end_date", "asc").all()] == ["HD-3", "HD-1", "HD-2"]
    assert [c.code for c in apply_sort(base, Contract, "end_date", "desc").all()] == ["HD-1", "HD-3", "HD-2"]


# ── Luật 2: khóa phụ id ổn định qua các trang ────────────────────────────────────────────
def test_trung_gia_tri_phan_trang_khong_mat_khong_lap(db):
    # 25 phiếu cùng trạng thái: không khóa phụ thì MySQL trả thứ tự tùy hứng mỗi trang một kiểu.
    ids = [_mk(db, f"P{i:02d}", status="draft").id for i in range(25)]
    base = db.query(PaymentRequest)
    seen = []
    for page in range(4):
        q = apply_sort(base, PaymentRequest, "status", "asc").offset(page * 7).limit(7)
        seen += [r.id for r in q.all()]
    assert len(seen) == 25
    assert len(set(seen)) == 25, "có dòng lặp giữa các trang"
    assert set(seen) == set(ids), "có dòng không bao giờ hiện ra"
    assert seen == sorted(ids, reverse=True)   # trùng giá trị -> id giảm dần


def test_khoa_phu_id_cung_ap_cho_nhanh_allow(db):
    for i in range(10):
        _mk(db, f"Q{i}", status="draft")
    allow = {"status": PaymentRequest.status}
    q = apply_sort_from_request(db.query(PaymentRequest), PaymentRequest,
                                _Req(sort_by="status", sort_dir="asc"), allow=allow)
    ids = [r.id for r in q.all()]
    assert ids == sorted(ids, reverse=True)


def test_nhanh_allow_o_trong_xuong_cuoi_ca_hai_chieu(db):
    _mk(db, "A", "Bình")
    _mk(db, "B", "")
    _mk(db, "C", "An")
    allow = {"name": PaymentRequest.supplier_name}
    for direction, head in (("asc", ["C", "A"]), ("desc", ["A", "C"])):
        q = apply_sort_from_request(db.query(PaymentRequest), PaymentRequest,
                                    _Req(sort_by="name", sort_dir=direction), allow=allow)
        codes = _codes(q)
        assert codes[:2] == head and codes[2] == "B"


def test_sap_theo_id_khong_gan_khoa_phu_thua(db):
    for i in range(3):
        _mk(db, f"I{i}")
    asc = apply_sort(db.query(PaymentRequest), PaymentRequest, "id", "asc").all()
    assert [r.code for r in asc] == ["I0", "I1", "I2"]
    desc = apply_sort(db.query(PaymentRequest), PaymentRequest, "id", "desc").all()
    assert [r.code for r in desc] == ["I2", "I1", "I0"]


# ── Biên: khóa lạ, mô hình không có cột id, tham số nulls_last cũ ────────────────────────
def test_khoa_la_ve_mac_dinh_khong_no(db):
    for i in range(3):
        _mk(db, f"K{i}")
    base = db.query(PaymentRequest)
    assert _codes(apply_sort(base, PaymentRequest, "khong_co_cot", "asc")) == ["K2", "K1", "K0"]
    assert _codes(apply_sort(base, PaymentRequest, None, "asc")) == ["K2", "K1", "K0"]
    # sort_dir rác thì coi như tăng dần, không nổ
    assert _codes(apply_sort(base, PaymentRequest, "code", "sideways")) == ["K0", "K1", "K2"]


def test_mo_hinh_khong_co_cot_id_van_xep_duoc(db):
    LocalBase = declarative_base()

    class NoId(LocalBase):
        __tablename__ = "tab_test_no_id_cr744"
        key = Column(String(10), primary_key=True)
        label = Column(String(20), nullable=True)
        weight = Column(BigInteger, nullable=True)

    LocalBase.metadata.create_all(db.get_bind())
    db.add_all([NoId(key="a", label="Z", weight=1), NoId(key="b", label=None, weight=2),
                NoId(key="c", label="A", weight=0)])
    db.flush()
    rows = apply_sort(db.query(NoId), NoId, "label", "asc", default=NoId.key.asc()).all()
    assert [r.key for r in rows] == ["c", "a", "b"]
    rows = apply_sort(db.query(NoId), NoId, "weight", "desc", default=NoId.key.asc()).all()
    assert [r.key for r in rows] == ["b", "a", "c"]


def test_tham_so_nulls_last_cu_van_nhan_va_khong_doi_ket_qua(db):
    _mk(db, "A", "Bình")
    _mk(db, "B", "")
    base = db.query(PaymentRequest)
    with_flag = _codes(apply_sort(base, PaymentRequest, "supplier_name", "asc", nulls_last=("supplier_name",)))
    without = _codes(apply_sort(base, PaymentRequest, "supplier_name", "asc"))
    assert with_flag == without == ["A", "B"]
