from enum import IntEnum

from sqlalchemy import BigInteger, Boolean, Index, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import Base, AuditMixin

# Đồng tiền mặc định của cả hệ. Đơn thường vẫn ghi "VND" + tỷ giá 1 để mọi dòng có cùng
# một cách đọc số tiền — không có dòng nào "không loại tiền".
DEFAULT_CURRENCY = "VND"


class OrderType(IntEnum):
    """Loại đơn mua hàng (bao-CR-319). Cột mới nên lưu SỐ theo luật R2/QĐ-11."""

    DOMESTIC = 1        # Trong nước
    IMPORT = 2          # Nhập khẩu


ORDER_TYPE_LABELS = {OrderType.DOMESTIC: "Trong nước", OrderType.IMPORT: "Nhập khẩu"}


class ImportCostType(IntEnum):
    """Loại chi phí của lô hàng nhập khẩu (bao-CR-319 P3).

    Hai nhóm khác hẳn nhau về NGƯỜI NHẬN tiền, đừng gộp lại:
    - Thuế (IMPORT_DUTY · IMPORT_VAT · EXCISE_TAX · ENV_TAX) nộp NGÂN SÁCH NHÀ NƯỚC.
    - Còn lại trả cho hãng tàu / đơn vị khai thuê / kho bãi / bảo hiểm — mỗi khoản một
      nhà cung cấp riêng, nên NCC khai ở TỪNG DÒNG chứ không lấy theo đơn.
    """

    OCEAN_FREIGHT = 1     # Cước vận tải quốc tế (đường biển / hàng không)
    LOCAL_CHARGE = 2      # Phí địa phương tại cảng (THC, nâng hạ, D/O...)
    CUSTOMS_SERVICE = 3   # Phí dịch vụ khai thuê hải quan
    IMPORT_DUTY = 4       # Thuế nhập khẩu
    IMPORT_VAT = 5        # Thuế GTGT hàng nhập khẩu
    EXCISE_TAX = 6        # Thuế tiêu thụ đặc biệt
    ENV_TAX = 7           # Thuế bảo vệ môi trường
    INSPECTION = 8        # Phí kiểm tra chuyên ngành / kiểm dịch
    INSURANCE = 9         # Bảo hiểm hàng hóa
    INLAND_FREIGHT = 10   # Vận chuyển nội địa từ cảng về kho
    STORAGE = 11          # Lưu kho / lưu bãi / lưu container
    # bao-CR-347: ba loại khách liệt kê trên mẫu báo cáo giá vốn mà bộ mã cũ chưa có.
    # THÊM mã mới chứ không sửa nghĩa mã cũ — số đã nằm trong dữ liệu prod.
    IMPORT_SERVICE = 12   # Dịch vụ hỗ trợ nhập khẩu, vận chuyển (trọn gói)
    CONTAINER_DAMAGE = 13 # Chi tiền hư container
    LATE_INTEREST = 14    # Lãi trả chậm
    OTHER = 99            # Chi phí khác


IMPORT_COST_TYPE_LABELS = {
    ImportCostType.OCEAN_FREIGHT: "Cước vận tải quốc tế",
    ImportCostType.LOCAL_CHARGE: "Phí địa phương tại cảng",
    ImportCostType.CUSTOMS_SERVICE: "Phí dịch vụ hải quan",
    ImportCostType.IMPORT_DUTY: "Thuế nhập khẩu",
    ImportCostType.IMPORT_VAT: "Thuế GTGT hàng nhập khẩu",
    ImportCostType.EXCISE_TAX: "Thuế tiêu thụ đặc biệt",
    ImportCostType.ENV_TAX: "Thuế bảo vệ môi trường",
    ImportCostType.INSPECTION: "Phí kiểm tra chuyên ngành",
    ImportCostType.INSURANCE: "Bảo hiểm hàng hóa",
    ImportCostType.INLAND_FREIGHT: "Vận chuyển nội địa",
    ImportCostType.STORAGE: "Lưu kho / lưu bãi",
    ImportCostType.IMPORT_SERVICE: "Dịch vụ hỗ trợ nhập khẩu, vận chuyển",
    ImportCostType.CONTAINER_DAMAGE: "Chi tiền hư container",
    ImportCostType.LATE_INTEREST: "Lãi trả chậm",
    ImportCostType.OTHER: "Chi phí khác",
}


class ImportCostStatus(IntEnum):
    """Khoản chi phí đang là số DỰ KIẾN hay số THỰC TẾ (bao-CR-347).

    Thu mua gõ trước một bộ chi phí dự toán lúc chưa có hóa đơn để chốt giá bán, rồi
    thay dần bằng số thật khi chứng từ về. Hai loại phải sống CÙNG một dòng vì báo cáo
    giá vốn cần bày cạnh nhau và tính chênh lệch.

    Chỉ dòng THỰC TẾ mới sinh công nợ và mới bị xét khi Hoàn thành đơn — nếu không thì
    Yêu cầu thanh toán đòi trả một khoản chưa có hóa đơn.
    """

    ESTIMATED = 1   # Dự kiến
    ACTUAL = 2      # Thực tế


IMPORT_COST_STATUS_LABELS = {
    ImportCostStatus.ESTIMATED: "Dự kiến",
    ImportCostStatus.ACTUAL: "Thực tế",
}

# Khoản nộp cho nhà nước — giao diện gợi ý sẵn NCC "Ngân sách nhà nước" cho mấy loại này.
IMPORT_COST_TAX_TYPES = frozenset({ImportCostType.IMPORT_DUTY, ImportCostType.IMPORT_VAT,
                                   ImportCostType.EXCISE_TAX, ImportCostType.ENV_TAX})

# NCC đại diện cho khoản nộp thuế. Có thật trong danh mục NCC (migration seed) để công nợ
# và Yêu cầu thanh toán ở P5 đi chung một đường với mọi khoản chi phí khác.
STATE_BUDGET_SUPPLIER_CODE = "NSNN"
STATE_BUDGET_SUPPLIER_NAME = "Ngân sách nhà nước"


class AllocationMethod(IntEnum):
    """Cách chia một khoản chi phí về các dòng hàng (bao-CR-319 P3/P4).

    Chỉ để XEM: kết quả chia tính lúc xem / lúc in, không ghi xuống cột nào, không
    đẩy vào giá tồn kho — hệ chưa có phân hệ hóa đơn nên chưa tính giá vốn.
    """

    BY_VALUE = 1      # theo giá trị dòng hàng (mặc định)
    BY_WEIGHT = 2     # theo khối lượng
    BY_QUANTITY = 3   # theo số lượng
    BY_PRODUCT = 4    # chỉ định đích danh một mã hàng
    MANUAL = 5        # thu mua gõ tay số tiền từng dòng hàng (`manual_allocation`), tổng phải khớp khoản


ALLOCATION_METHOD_LABELS = {
    AllocationMethod.BY_VALUE: "Theo giá trị",
    AllocationMethod.BY_WEIGHT: "Theo khối lượng",
    AllocationMethod.BY_QUANTITY: "Theo số lượng",
    AllocationMethod.BY_PRODUCT: "Chỉ định một mã hàng",
    AllocationMethod.MANUAL: "Nhập tay",
}


class PurchaseOrder(Base, AuditMixin):
    """Đơn mua hàng (PO) — header. Là module trung tâm của vòng đời mua hàng."""

    __tablename__ = "tab_purchase_order"
    # created_by nằm ở AuditMixin — index qua __table_args__ (apply_scope lọc theo cột này ở MỌI list)
    __table_args__ = (Index("ix_po_created_by", "created_by"),)

    code: Mapped[str] = mapped_column(String(50), unique=True, default="")     # PO00045
    misa_code: Mapped[str] = mapped_column(String(50), default="")
    pr_code: Mapped[str] = mapped_column(String(50), default="", index=True)   # nguồn PYC — cross-ref nóng (sync/tiến độ/list theo PYC)
    survey_code: Mapped[str] = mapped_column(String(50), default="")
    company_id: Mapped[int] = mapped_column(BigInteger, default=0, index=True) # pháp nhân nhận HĐ — apply_scope lọc theo cột này
    supplier_code: Mapped[str] = mapped_column(String(50), default="")         # NCC bán hàng
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    department: Mapped[str] = mapped_column(String(255), default="", index=True)
    nspt: Mapped[str] = mapped_column(String(100), default="")
    order_date: Mapped[str] = mapped_column(String(10), default="", index=True)
    vat_rate: Mapped[float] = mapped_column(Numeric(5, 4), default=0.08)
    payment_terms: Mapped[str] = mapped_column(String(255), default="")    # hình thức TT cho NCC (col46)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    # draft | submitted | approved | partial | received | cancelled
    # Trạng thái hồ sơ chứng từ — người dùng cập nhật TAY (Task 10b):
    #   "chưa có chứng từ" · "đã có thông tin chứng từ" · "đã đủ chứng từ"
    document_status: Mapped[str] = mapped_column(String(30), default="chưa có chứng từ", index=True)
    note: Mapped[str] = mapped_column(Text, default="")
    approve_note: Mapped[str] = mapped_column(Text, default="")
    # --- bao-CR-319: đơn nhập khẩu -------------------------------------------------------
    order_type: Mapped[int] = mapped_column(SmallInteger, default=int(OrderType.DOMESTIC), index=True)
    # Đồng tiền + tỷ giá MẶC ĐỊNH của đơn — dòng hàng chép xuống khi thêm mới, sửa riêng được.
    currency: Mapped[str] = mapped_column(String(10), default=DEFAULT_CURRENCY)
    exchange_rate: Mapped[float] = mapped_column(Numeric(18, 6), default=1)
    customs_decl_no: Mapped[str] = mapped_column(String(50), default="")     # số tờ khai hải quan
    customs_decl_date: Mapped[str] = mapped_column(String(10), default="")   # ngày tờ khai
    # bao-CR-347: ngày hàng rời cảng xuất (ETD) — dòng "Ngày gửi" trên báo cáo giá vốn.
    etd_date: Mapped[str] = mapped_column(String(10), default="")
    # --- bao-CR-321: điều khoản in trên đơn, chép từ NCC lúc chọn, sửa riêng từng đơn ---
    # 0 / rỗng = chưa khai -> bản in lùi về giá trị của NCC, rồi về mặc định (xem resolve_print_terms).
    inspection_days: Mapped[int] = mapped_column(SmallInteger, default=0)
    return_days: Mapped[int] = mapped_column(SmallInteger, default=0)
    invoice_deadline: Mapped[str] = mapped_column(String(255), default="")


class POItem(Base, AuditMixin):
    """Dòng hàng của PO."""

    __tablename__ = "tab_po_item"

    po_id: Mapped[int] = mapped_column(BigInteger, index=True)
    product_code: Mapped[str] = mapped_column(String(50), default="")
    product_name: Mapped[str] = mapped_column(String(255), default="")
    invoice_name: Mapped[str] = mapped_column(String(255), default="")      # tên trên hóa đơn (col15/43)
    item_group: Mapped[str] = mapped_column(String(100), default="")
    spec: Mapped[str] = mapped_column(String(255), default="")              # xuất xứ/TSKT/chất liệu
    fg_code: Mapped[str] = mapped_column(String(50), default="")           # Mã HH / thành phẩm (col42)
    fg_name: Mapped[str] = mapped_column(String(255), default="")          # Tên HH / thành phẩm (theo master SP)
    invoice_no: Mapped[str] = mapped_column(String(50), default="")        # Số hóa đơn (theo sản phẩm, col31)
    invoice_date: Mapped[str] = mapped_column(String(10), default="")       # Ngày hóa đơn — NGƯỜI DÙNG nhập, hệ thống không đoán hộ (bao-CR-367)
    document_delivery_date: Mapped[str] = mapped_column(String(10), default="")  # Ngày giao chứng từ cho KT (Task 8)
    supplier_ready: Mapped[bool] = mapped_column(Boolean, default=False)    # NCC có sẵn hàng (col17)
    required_date: Mapped[str] = mapped_column(String(10), default="")      # ngày yêu cầu có hàng (col3)
    expected_date: Mapped[str] = mapped_column(String(10), default="")      # dự kiến có hàng — copy xuống từ dòng YCMH, sửa tay được
    unit: Mapped[str] = mapped_column(String(25), default="")
    qty_request: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    qty_order: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    price: Mapped[float] = mapped_column(Numeric(18, 4), default=0)        # ĐƠN GIÁ giữ 4 số lẻ (giá quy đổi hay lẻ tới phần nghìn đồng)
    vat: Mapped[float] = mapped_column(Numeric(5, 2), default=0)            # % VAT của dòng
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)        # qty_order*price*(1+vat%) — NGUYÊN TỆ
    # --- bao-CR-319: dòng hàng ngoại tệ ---------------------------------------------------
    # `price` và `amount` ghi theo ĐỒNG TIỀN CỦA DÒNG. Mọi nơi tiền rời khỏi phân hệ này
    # (công nợ, tồn kho, báo cáo, trang chủ) phải dùng `base_amount` / giá đã nhân tỷ giá —
    # bảng công nợ không có cột loại tiền nên cộng thẳng số nguyên tệ vào là sai âm thầm.
    currency: Mapped[str] = mapped_column(String(10), default=DEFAULT_CURRENCY)
    exchange_rate: Mapped[float] = mapped_column(Numeric(18, 6), default=1)
    base_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)   # amount × exchange_rate
    weight_kg: Mapped[float] = mapped_column(Numeric(18, 3), default=0)     # khối lượng — dùng chia chi phí theo cân nặng
    dimension: Mapped[str] = mapped_column(String(100), default="")         # quy cách / kích thước (dài×rộng×cao)
    qty_received: Mapped[float] = mapped_column(Numeric(18, 3), default=0)  # auto = Σ giao đã nhận
    qty_remaining: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    line_status: Mapped[str] = mapped_column(String(30), default="")        # Chưa giao/Đang giao/Đủ
    warehouse_code: Mapped[str] = mapped_column(String(50), default="")     # kho mặc định cho dòng
    note: Mapped[str] = mapped_column(String(255), default="")
    progress_status: Mapped[str] = mapped_column(String(40), default="Chưa đặt hàng", index=True)  # cột P — máy trạng thái tiến độ (lọc ở màn Tiến độ mua hàng)
    pay_confirm_date: Mapped[str] = mapped_column(String(10), default="")   # AU — Ngày KT xác nhận thanh toán
    pause_reason: Mapped[str] = mapped_column(String(500), default="")      # AV — Lý do hủy/tạm ngưng
    status_before_pause: Mapped[str] = mapped_column(String(40), default="")  # AW — trạng thái trước khi tạm ngưng


class POImportCost(Base, AuditMixin):
    """Một khoản chi phí của lô hàng nhập khẩu (bao-CR-319 P3).

    Bảng PHẲNG, gắn thẳng vào ĐƠN chứ không vào dòng hàng: một khoản cước biển là của
    cả lô, không của riêng mã nào. Việc chia về dòng hàng là chuyện XEM (P4), tính lúc
    xem/in theo `allocation_method`, không lưu kết quả xuống đây.

    Mỗi dòng tự khai NCC vì tiền đi về nhiều nơi khác nhau: cước trả hãng tàu, thuế nộp
    ngân sách nhà nước, phí khai thuê trả đơn vị dịch vụ.
    """

    __tablename__ = "tab_po_import_cost"

    po_id: Mapped[int] = mapped_column(BigInteger, index=True)
    cost_type: Mapped[int] = mapped_column(SmallInteger, default=int(ImportCostType.OTHER), index=True)
    # bao-CR-347. Dòng cũ đều là số thật (đã sinh công nợ) nên migration điền ACTUAL.
    cost_status: Mapped[int] = mapped_column(SmallInteger, default=int(ImportCostStatus.ACTUAL), index=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    supplier_code: Mapped[str] = mapped_column(String(50), default="", index=True)
    supplier_name: Mapped[str] = mapped_column(String(255), default="")
    # Tiền của khoản chi phí. Cùng quy ước với dòng hàng: `amount` là số TRƯỚC thuế theo
    # đồng tiền của chính dòng chi phí, `base_amount` là tổng ĐÃ gồm VAT quy về VNĐ.
    currency: Mapped[str] = mapped_column(String(10), default=DEFAULT_CURRENCY)
    exchange_rate: Mapped[float] = mapped_column(Numeric(18, 6), default=1)
    amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    vat: Mapped[float] = mapped_column(Numeric(5, 2), default=0)             # % VAT của khoản chi phí
    base_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)    # amount × (1 + vat%) × tỷ giá
    allocation_method: Mapped[int] = mapped_column(SmallInteger, default=int(AllocationMethod.BY_VALUE))
    allocation_target: Mapped[str] = mapped_column(String(50), default="")   # mã hàng, chỉ dùng khi chỉ định
    # Cách 5 "Nhập tay": JSON {"<id dòng hàng>": số tiền VNĐ}. Đây là cách chia DUY NHẤT phải lưu
    # kết quả, vì con số do người gõ chứ không suy ra được từ dữ liệu khác. Tổng phải bằng đúng
    # `base_amount` (kiểm khi lưu); cách khác thì cột này để trống.
    manual_allocation: Mapped[str] = mapped_column(Text, default="")
    invoice_no: Mapped[str] = mapped_column(String(50), default="")
    invoice_date: Mapped[str] = mapped_column(String(10), default="")
    payment_due_date: Mapped[str] = mapped_column(String(10), default="")    # hạn trả khoản chi phí
    note: Mapped[str] = mapped_column(String(255), default="")


class PODelivery(Base, AuditMixin):
    """Một lần giao của 1 dòng hàng (1 sản phẩm có thể giao nhiều lần)."""

    __tablename__ = "tab_po_delivery"

    po_id: Mapped[int] = mapped_column(BigInteger, index=True)
    po_item_id: Mapped[int] = mapped_column(BigInteger, index=True)
    delivery_no: Mapped[int] = mapped_column(BigInteger, default=1)
    warehouse_code: Mapped[str] = mapped_column(String(50), default="")
    carrier_code: Mapped[str] = mapped_column(String(50), default="")       # đơn vị vận chuyển
    carrier_name: Mapped[str] = mapped_column(String(255), default="")
    ship_qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    ship_unit: Mapped[str] = mapped_column(String(25), default="")
    received_qty: Mapped[float] = mapped_column(Numeric(18, 3), default=0)
    promised_date: Mapped[str] = mapped_column(String(10), default="")      # NCC cam kết giao
    expected_date: Mapped[str] = mapped_column(String(10), default="")      # BỎ DÙNG — không nơi nào ghi; "dự kiến có hàng" nay ở POItem.expected_date. Giữ cột theo luật "CSDL cũ: chỉ thêm, không sửa"
    received_date: Mapped[str] = mapped_column(String(10), default="", index=True)  # ngày nhận thực tế
    std_days: Mapped[int] = mapped_column(BigInteger, default=0)            # số ngày quy định (AH)
    regulated_date: Mapped[str] = mapped_column(String(10), default="")     # ngày quy định (AI)
    diff_promise: Mapped[int] = mapped_column(BigInteger, default=0)        # CL cam kết−nhận (AL) <0=trễ
    diff_regulated: Mapped[int] = mapped_column(BigInteger, default=0)      # CL quy định−nhận (AM)
    diff_required: Mapped[int] = mapped_column(BigInteger, default=0)       # CL quy định−KD yêu cầu (AN)
    invoice_no: Mapped[str] = mapped_column(String(50), default="")
    invoice_date: Mapped[str] = mapped_column(String(10), default="")
    shipping_unit_price: Mapped[float] = mapped_column(Numeric(18, 4), default=0)   # đơn giá vận chuyển — cũng cho 4 số lẻ
    shipping_amount: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    qc_result: Mapped[str] = mapped_column(String(20), default="")          # Đạt | Thiếu | Lỗi
    status: Mapped[str] = mapped_column(String(30), default="")            # trạng thái giao (P)
    extra_request: Mapped[str] = mapped_column(Text, default="")           # yêu cầu khác (AC)
    progress_note: Mapped[str] = mapped_column(Text, default="")           # chi tiết tiến độ (AG)
