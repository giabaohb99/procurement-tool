"""Bảng của phân hệ Tra cứu giá hải quan (bao-CR-470).

Thiết kế + số đo: `doc/erp/hai-quan/02-thiet-ke-ky-thuat.md` §3.

- `CustomsParty` — bảng ĐỐI TƯỢNG: doanh nghiệp trong nước + đối tác nước ngoài,
  phân loại theo bản chất (`PartyType`). Tên lặp lại rất nhiều trên dòng hàng
  (mã số thuế lặp ~12,6 lần) nên tách ra là gọn thật.
- `CustomsLine` — mỗi dòng là MỘT DÒNG HÀNG của một tờ khai, KHÔNG phải một tờ khai
  (02 §2.2): tệp GTT02 không có số tờ khai và đã lọc bớt dòng khác mã HS, nên
  không gom ngược lại thành tờ khai được. Đếm số dòng rồi gọi là "số tờ khai" là
  sai gần gấp đôi.

⚠️ Lô nạp KHÔNG có bảng riêng: dùng lại `tab_import_batch` / `tab_import_log` của
`import_tool` (`ImportModule.CUSTOMS_DECLARATION`). Cột `batch_id` trỏ vào đó.
"""
from datetime import date

from sqlalchemy import (BigInteger, Boolean, Date, Index, Integer, Numeric, SmallInteger,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import AuditMixin, Base


class CustomsParty(Base, AuditMixin):
    __tablename__ = "tab_customs_party"
    __table_args__ = (UniqueConstraint("party_type", "dedupe_key", name="uq_customs_party_key"),)

    party_type: Mapped[int] = mapped_column(SmallInteger, default=0)       # PartyType
    #  Khóa chống trùng: MÃ SỐ THUẾ (DOMESTIC) hoặc MD5 của tên đã chuẩn hóa (FOREIGN).
    #  Trong nước KHÔNG chống trùng theo tên: 1.447 mã số thuế có tới 1.504 cách viết
    #  tên (nguồn viết hoa lộn xộn), theo tên là một công ty tách thành nhiều dòng.
    dedupe_key: Mapped[str] = mapped_column(String(40), default="")
    tax_code: Mapped[str] = mapped_column(String(14), default="")          # chỉ DOMESTIC có
    name: Mapped[str] = mapped_column(String(255), default="")             # tên của lần nạp MỚI NHẤT


class CustomsLine(Base):
    """Dòng hàng — bảng lớn nhất, cố ý KHÔNG mang `AuditMixin`.

    Người nạp / lúc nạp / tệp nào đã nằm ở lô (`batch_id`), chép thêm bốn cột
    audit vào từng dòng là ~32 byte mỗi dòng không đổi được gì.

    Trên MySQL bảng chia phân vùng theo năm của `reg_date` và khóa chính là
    `(id, reg_date)` — do migration dựng, cùng khuôn bốn bảng nhật ký (CR-454).
    Model khai khóa chính là `id` một mình để ORM và SQLite (bộ test) chạy bình
    thường.
    """
    __tablename__ = "tab_customs_line"
    #  Cố ý ÍT chỉ mục — mỗi chỉ mục tốn thêm dung lượng (02 §3.3). Tìm theo tên hàng
    #  là LIKE '%…%', không dùng được B-tree; biểu đồ vào bằng mã HS + khoảng ngày.
    __table_args__ = (
        Index("ix_customs_line_hs_date", "hs_code", "reg_date"),
        Index("ix_customs_line_importer_date", "importer_id", "reg_date"),
        #  Nút «Các lần nhập khác của đối tác này» lọc theo partner_id — thiếu chỉ mục này
        #  là quét cả bảng qua mọi phân vùng rồi mới sắp xếp (đo 1,8 giây trên dev, 23/09).
        Index("ix_customs_line_partner_date", "partner_id", "reg_date"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True)
    source_row: Mapped[int] = mapped_column(Integer, default=0)            # dòng mấy trong tệp gốc
    date_fixed: Mapped[int] = mapped_column(SmallInteger, default=0)       # 1 = ngày đăng ký đã vá

    reg_date: Mapped[date] = mapped_column(Date)                           # 0  Ngày đăng ký (ĐÃ vá)
    office_code: Mapped[str] = mapped_column(String(10), default="")       # 1
    importer_id: Mapped[int] = mapped_column(BigInteger, default=0)        # 2-3 → CustomsParty DOMESTIC
    partner_id: Mapped[int] = mapped_column(BigInteger, default=0)         # 4   → CustomsParty FOREIGN
    hs_code: Mapped[str] = mapped_column(String(8), default="")            # 5  giữ chữ: có số 0 đầu
    line_no: Mapped[int] = mapped_column(SmallInteger, default=0)          # 6
    product_name: Mapped[str] = mapped_column(String(255), default="")     # 7  lưu thẳng (02 §2.1)
    price_usd: Mapped[float | None] = mapped_column(Numeric(16, 4), nullable=True)       # 8
    price_nt: Mapped[float | None] = mapped_column(Numeric(16, 4), nullable=True)        # 9
    adj_price_usd: Mapped[float | None] = mapped_column(Numeric(16, 4), nullable=True)   # 10
    adj_price_nt: Mapped[float | None] = mapped_column(Numeric(16, 4), nullable=True)    # 11
    currency: Mapped[str] = mapped_column(String(3), default="")           # 12
    fx_rate: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)         # 13
    usd_rate: Mapped[float | None] = mapped_column(Numeric(14, 4), nullable=True)        # 14
    quantity: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)        # 15
    unit_code: Mapped[str] = mapped_column(String(4), default="")          # 16
    origin_country: Mapped[str] = mapped_column(String(2), default="")     # 17
    contract_no: Mapped[str] = mapped_column(String(40), default="")       # 18
    contract_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # 19 KHÔNG vá
    incoterm: Mapped[str] = mapped_column(String(3), default="")           # 20
    transport_mode: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)      # 21 TransportMode
    #  22-30: rỗng giữ NULL, KHÔNG đổi thành 0 — rỗng là tờ khai không khai, 0 là thuế suất 0.
    rate_import: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    rate_excise: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    rate_vat: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    rate_safeguard: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    #  Tiền thuế VND trong nguồn có 3 chữ số lẻ (vd 19961918.592) — scale 2 sẽ cắt mất.
    tax_import: Mapped[float | None] = mapped_column(Numeric(18, 3), nullable=True)
    tax_excise: Mapped[float | None] = mapped_column(Numeric(18, 3), nullable=True)
    tax_vat: Mapped[float | None] = mapped_column(Numeric(18, 3), nullable=True)
    tax_environment: Mapped[float | None] = mapped_column(Numeric(18, 3), nullable=True)
    tax_safeguard: Mapped[float | None] = mapped_column(Numeric(18, 3), nullable=True)
    import_country: Mapped[str] = mapped_column(String(2), default="")     # 31

    #  Hai cột DẪN XUẤT từ tên hàng lúc nạp (HQ4 — `ingredient.py`), không có trong
    #  tệp gốc. Đo trên dữ liệu thật: gắn được hoạt chất ~41% số dòng (phần còn lại phần
    #  lớn là hóa chất khử trùng / tẩy rửa, không có hoạt chất BVTV để nối), tách được
    #  hàm lượng / dạng bào chế ~93%. Danh mục đổi thì chạy lại `retag_all`.
    active_ingredient: Mapped[str] = mapped_column(String(255), default="", index=True)
    formulation: Mapped[str] = mapped_column(String(40), default="")


class CustomsIngredientAlias(Base, AuditMixin):
    """Từ khóa → tên hoạt chất chuẩn (`EMAMECTIN` → `EMAMECTIN BENZOATE`) — HQ4."""
    __tablename__ = "tab_customs_ingredient_alias"

    keyword: Mapped[str] = mapped_column(String(100), unique=True)
    canonical: Mapped[str] = mapped_column(String(255), default="")


class CustomsPesticide(Base, AuditMixin):
    """Danh mục thuốc BVTV được phép (tên thương mại → hoạt chất) — HQ4.

    Nạp bằng `scripts/load_customs_catalogs.py` từ nguồn ngoài, không nhập tay.
    `trade_key` = phần tên trước hàm lượng, viết hoa (`BIPYRHONE`), dùng để dò trong tên hàng.
    """
    __tablename__ = "tab_customs_pesticide"

    source_id: Mapped[int] = mapped_column(Integer, default=0)
    trade_name: Mapped[str] = mapped_column(String(255), default="")
    trade_key: Mapped[str] = mapped_column(String(255), default="", index=True)
    active_ingredient: Mapped[str] = mapped_column(String(500), default="")
    pest_group: Mapped[str] = mapped_column(String(100), default="")
    registrant: Mapped[str] = mapped_column(String(255), default="")


class CustomsRegulation(Base, AuditMixin):
    """Danh mục hóa chất theo văn bản pháp lý — HQ6 (P-01 ngưỡng, P-03 tra cứu nghĩa vụ).

    MỘT bảng cho mọi danh sách: phụ lục I–IV của NĐ 24/2026/NĐ-CP, hoạt chất cấm theo
    TT 75/2025/TT-BNNMT, hóa chất phải công bố theo TT 01/2026/TT-BCT. Ngưỡng khối lượng
    (`threshold_kg`) chỉ có ở phụ lục IV. Sửa được trên màn hình (khóa
    `customs_regulation`) vì nghị định đổi thì phải có người cập nhật.
    """
    __tablename__ = "tab_customs_regulation"

    list_code: Mapped[int] = mapped_column(SmallInteger, default=0, index=True)   # RegulationList
    name: Mapped[str] = mapped_column(String(500), default="")
    name_vi: Mapped[str] = mapped_column(String(500), default="")
    cas_no: Mapped[str] = mapped_column(String(40), default="", index=True)
    category: Mapped[str] = mapped_column(String(100), default="")
    threshold_kg: Mapped[float | None] = mapped_column(Numeric(14, 3), nullable=True)
    banned_year: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    legal_basis: Mapped[str] = mapped_column(String(255), default="")
    note: Mapped[str] = mapped_column(String(500), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class CustomsTariff(Base):
    """Biểu thuế xuất nhập khẩu theo mã HS — HQ6 (P-04). Dữ liệu tham khảo, nạp bằng
    kịch bản, không sửa tay; cố ý không mang AuditMixin."""
    __tablename__ = "tab_customs_tariff"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    hs_code: Mapped[str] = mapped_column(String(10), default="", index=True)
    name_vn: Mapped[str] = mapped_column(Text, default="")
    name_en: Mapped[str] = mapped_column(Text, default="")
    unit: Mapped[str] = mapped_column(String(40), default="")
    rate_normal: Mapped[str] = mapped_column(String(20), default="")       # thuế suất thông thường — cột `tt` của nguồn
    rate_mfn: Mapped[str] = mapped_column(String(20), default="")      # thuế suất ưu đãi (MFN) — cột `ud` của nguồn
    rate_vat: Mapped[str] = mapped_column(String(20), default="")
    fta_json: Mapped[str] = mapped_column(Text, default="")             # {hiệp định: thuế suất}
    policy: Mapped[str] = mapped_column(Text, default="")              # chính sách quản lý
