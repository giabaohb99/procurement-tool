"""Bộ mã HỢP ĐỒNG LAO ĐỘNG — `tab_labor_contract.contract_type` / `.status`.

R2/QĐ-11: cột phân loại / trạng thái mới là `SMALLINT` + `IntEnum`, tiếng Việt chỉ
ở tầng hiển thị. Thiết kế: plan `frontend-v2/plans/261005-1537-hop-dong-lao-dong-mau-theo-phap-nhan/`.

Thuần stdlib (không import SQLAlchemy) để `scripts/gen_status_ts.py` nạp được ở máy
không cài SQLAlchemy.

Luật bất biến:
  - Số đã cấp GIỮ NGUYÊN mãi mãi, KHÔNG tái dùng; mã bị bỏ thì để trống số đó.
  - Mã mới → cấp số tiếp theo sau số lớn nhất.
"""
from enum import IntEnum

from app.core.status_catalog import Code, CodeSet, register


class LaborContractType(IntEnum):
    """Loại HĐLĐ. `0` KHÔNG hợp lệ — chặn ở tầng schema."""

    PROBATION = 1     # Thử việc
    FIXED_TERM = 2    # Xác định thời hạn
    INDEFINITE = 3    # Không xác định thời hạn
    SERVICE = 4       # Khoán việc / dịch vụ
    COLLABORATOR = 5  # Cộng tác viên
    OTHER = 9         # Khác


class LaborContractStatus(IntEnum):
    """Trạng thái HĐLĐ. EXPIRED là SUY RA (SIGNED + end_date < hôm nay), KHÔNG ghi DB."""

    DRAFT = 1       # Nháp
    SIGNED = 2      # Đã ký – hiệu lực
    EXPIRED = 3     # Hết hạn (suy ra, giữ chỗ số 3)
    TERMINATED = 4  # Đã chấm dứt / thanh lý
    CANCELLED = 5   # Đã hủy


LABOR_CONTRACT_TYPE_LABELS: dict[LaborContractType, str] = {
    LaborContractType.PROBATION: "Thử việc",
    LaborContractType.FIXED_TERM: "Xác định thời hạn",
    LaborContractType.INDEFINITE: "Không xác định thời hạn",
    LaborContractType.SERVICE: "Khoán việc / dịch vụ",
    LaborContractType.COLLABORATOR: "Cộng tác viên",
    LaborContractType.OTHER: "Khác",
}

LABOR_CONTRACT_STATUS_LABELS: dict[LaborContractStatus, str] = {
    LaborContractStatus.DRAFT: "Nháp",
    LaborContractStatus.SIGNED: "Đã ký – hiệu lực",
    LaborContractStatus.EXPIRED: "Hết hạn",
    LaborContractStatus.TERMINATED: "Đã chấm dứt / thanh lý",
    LaborContractStatus.CANCELLED: "Đã hủy",
}

#  Loại BẮT BUỘC có ngày kết thúc. INDEFINITE thì CẤM có end_date; OTHER thì tùy.
REQUIRES_END_DATE: frozenset[LaborContractType] = frozenset({
    LaborContractType.PROBATION,
    LaborContractType.FIXED_TERM,
    LaborContractType.SERVICE,
    LaborContractType.COLLABORATOR,
})
FORBIDS_END_DATE: frozenset[LaborContractType] = frozenset({LaborContractType.INDEFINITE})

#  `value` là SỐ VIẾT DƯỚI DẠNG CHUỖI — khung `status_catalog` dùng mã chuỗi (cùng
#  lối `hr_work_history_codes.py`); FE tra `labelOf(SET, String(n))`.
LABOR_CONTRACT_TYPE_SET = register(CodeSet("labor_contract_type", "Loại hợp đồng lao động", [
    Code(str(int(k)), label, sort_order=int(k))
    for k, label in LABOR_CONTRACT_TYPE_LABELS.items()
]))
LABOR_CONTRACT_STATUS_SET = register(CodeSet("labor_contract_status", "Trạng thái hợp đồng lao động", [
    Code(str(int(k)), label, sort_order=int(k))
    for k, label in LABOR_CONTRACT_STATUS_LABELS.items()
]))


# ---- Danh sách biến mẫu HĐLĐ (duoc-CR-630) --------------------------------------------------
class LaborContractVariableSource(IntEnum):
    """Nguồn biến: HỆ THỐNG (giá trị lấy từ mã nguồn) hay TÙY CHỈNH (nhập tay theo từng hợp đồng)."""

    SYSTEM = 1
    CUSTOM = 2


class LaborContractVariableType(IntEnum):
    """Kiểu giá trị của biến TÙY CHỈNH. Biến hệ thống lưu `TEXT` (không có ý nghĩa)."""

    TEXT = 1       # Chữ (một dòng)
    MULTILINE = 2  # Chữ nhiều dòng
    NUMBER = 3     # Số (không âm, tối đa 2 số lẻ)
    DATE = 4       # Ngày
    MONEY = 5      # Tiền (đồng nguyên) — tự có bạn đồng hành `<mã>_bang_chu`


LABOR_CONTRACT_VARIABLE_SOURCE_LABELS: dict[LaborContractVariableSource, str] = {
    LaborContractVariableSource.SYSTEM: "Hệ thống",
    LaborContractVariableSource.CUSTOM: "Tùy chỉnh",
}

LABOR_CONTRACT_VARIABLE_TYPE_LABELS: dict[LaborContractVariableType, str] = {
    LaborContractVariableType.TEXT: "Chữ",
    LaborContractVariableType.MULTILINE: "Chữ nhiều dòng",
    LaborContractVariableType.NUMBER: "Số",
    LaborContractVariableType.DATE: "Ngày",
    LaborContractVariableType.MONEY: "Tiền",
}

LABOR_CONTRACT_VARIABLE_SOURCE_SET = register(CodeSet(
    "labor_contract_variable_source", "Nguồn biến mẫu hợp đồng lao động", [
        Code(str(int(k)), label, sort_order=int(k))
        for k, label in LABOR_CONTRACT_VARIABLE_SOURCE_LABELS.items()
    ]))
LABOR_CONTRACT_VARIABLE_TYPE_SET = register(CodeSet(
    "labor_contract_variable_type", "Kiểu giá trị biến mẫu hợp đồng lao động", [
        Code(str(int(k)), label, sort_order=int(k))
        for k, label in LABOR_CONTRACT_VARIABLE_TYPE_LABELS.items()
    ]))
