"""Dựng NGỮ CẢNH render cho mẫu HĐLĐ: bản ghi → dict[str, str] đúng danh mục biến.

THUẦN (không DB): nhận sẵn các đối tượng đã nạp. Mọi giá trị là CHUỖI đã định dạng,
thiếu dữ liệu → chuỗi rỗng (không bao giờ `None`/«None» lọt vào bản in).
Khóa trả về PHẢI bằng đúng `KNOWN_KEYS` (có test canh) — thêm biến thì sửa
`placeholder_catalog.py` và hàm này CÙNG LÚC.
"""
from calendar import monthrange
from datetime import date, timedelta

from app.core.labor_contract_codes import (
    LABOR_CONTRACT_TYPE_LABELS,
    LaborContractType,
)
from app.core.vn_number_words import read_amount_vi
from app.modules.employee.constants import EDUCATION_LEVEL_LABELS, GENDER_LABELS
from app.modules.labor_contract.placeholder_catalog import KNOWN_KEYS


def fmt_date(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def fmt_money(n: int | None) -> str:
    """15000000 → «15.000.000» (dấu chấm ngăn nghìn)."""
    return f"{int(n or 0):,}".replace(",", ".")


def _s(v) -> str:
    return "" if v is None else str(v)


def _add_months(d: date, months: int) -> date:
    """Cộng tháng, kẹp về ngày cuối tháng khi tháng đích ngắn hơn (31/01 + 1 tháng → 28/02)."""
    index = d.year * 12 + (d.month - 1) + months
    year, month = divmod(index, 12)
    return date(year, month + 1, min(d.day, monthrange(year, month + 1)[1]))


def describe_duration(start: date | None, end: date | None, contract_type: int) -> str:
    """«12 tháng» · «6 tháng 15 ngày» · «20 ngày» · «Không xác định thời hạn» · rỗng.

    Ngày kết thúc tính CẢ ngày đó: 01/10/2026 → 30/09/2027 = đúng 12 tháng.
    """
    if contract_type == int(LaborContractType.INDEFINITE):
        return "Không xác định thời hạn"
    if not start or not end or end < start:
        return ""
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1
    while True:  # tìm số tháng tròn lớn nhất mà «ngày cuối của kỳ» chưa vượt `end`
        anchor = _add_months(start, months)
        last_day = anchor - timedelta(days=1)
        if last_day <= end:
            break
        months -= 1
    days = (end - last_day).days
    #  Kẹp ngày (29-31 → ngày cuối tháng ngắn): kết thúc đúng ngày cuối tháng đích vẫn là tròn tháng.
    if days and anchor.day != start.day and end == anchor.replace(day=monthrange(anchor.year, anchor.month)[1]):
        days = 0
    if months <= 0:
        return f"{days} ngày"
    return f"{months} tháng" + (f" {days} ngày" if days else "")


def build_context(contract, employee, company, department, today: date) -> dict[str, str]:
    """Ngữ cảnh đầy đủ cho `docx_engine.render`. `company`/`department`/... có thể None."""
    rep = getattr(company, "legal_rep", None) if company else None
    base = int(contract.base_salary or 0)
    allowance = int(contract.allowance or 0)
    total = base + allowance
    sign = contract.sign_date
    try:
        type_label = LABOR_CONTRACT_TYPE_LABELS[LaborContractType(int(contract.contract_type))]
    except (ValueError, TypeError):
        type_label = ""

    ctx: dict[str, str] = {
        # --- Người lao động
        "ho_ten": _s(employee.full_name),
        "ma_nhan_vien": _s(employee.code),
        "gioi_tinh": GENDER_LABELS.get(employee.gender, "") if employee.gender else "",
        "ngay_sinh": fmt_date(employee.date_of_birth),
        "noi_sinh": _s(employee.place_of_birth),
        "dan_toc": _s(employee.ethnicity),
        "so_cccd": _s(employee.id_number),
        "ngay_cap_cccd": fmt_date(employee.id_issue_date),
        "noi_cap_cccd": _s(employee.id_issue_place),
        "dia_chi_thuong_tru": _s(employee.permanent_address),
        "dia_chi_hien_tai": _s(employee.current_address),
        "so_dien_thoai": _s(employee.phone),
        "email": _s(employee.personal_email or employee.email),
        "ma_so_thue": _s(employee.tax_code),
        "so_bhxh": _s(employee.social_insurance_no),
        "so_tai_khoan": _s(employee.bank_account_no),
        "ten_ngan_hang": _s(employee.bank_name),
        "chi_nhanh_ngan_hang": _s(employee.bank_branch),
        "trinh_do": EDUCATION_LEVEL_LABELS.get(employee.education_level, "") if employee.education_level else "",
        "chuyen_nganh": _s(employee.major),
        # --- Pháp nhân (bên A)
        "ten_cong_ty": _s(company.name) if company else "",
        "ten_viet_tat": _s(company.short_name) if company else "",
        "ma_so_thue_cong_ty": _s(company.tax_code) if company else "",
        "dia_chi_cong_ty": _s(company.address) if company else "",
        "nguoi_dai_dien": _s(rep.full_name) if rep else "",
        "chuc_vu_nguoi_dai_dien": _s(company.legal_rep_title) if company else "",
        # --- Hợp đồng
        "so_hop_dong": _s(contract.contract_no or contract.code),
        "loai_hop_dong": type_label,
        "ngay_ky": fmt_date(sign),
        "ngay_ky_ngay": f"{sign.day:02d}" if sign else "",
        "ngay_ky_thang": f"{sign.month:02d}" if sign else "",
        "ngay_ky_nam": str(sign.year) if sign else "",
        "ngay_bat_dau": fmt_date(contract.start_date),
        "ngay_ket_thuc": fmt_date(contract.end_date),
        "thoi_han": describe_duration(contract.start_date, contract.end_date, int(contract.contract_type or 0)),
        "chuc_danh": _s(contract.job_title),
        "phong_ban": _s(department.name) if department else "",
        "dia_diem_lam_viec": _s(contract.work_location),
        "ghi_chu": _s(contract.note),
        # --- Lương (đồng nguyên)
        "luong_co_ban": fmt_money(base),
        "luong_co_ban_bang_chu": read_amount_vi(base),
        "luong_dong_bao_hiem": fmt_money(contract.insurance_salary),
        "phu_cap": fmt_money(allowance),
        "phu_cap_bang_chu": read_amount_vi(allowance),
        "phu_cap_ghi_chu": _s(contract.allowance_note),
        "tong_thu_nhap": fmt_money(total),
        "tong_thu_nhap_bang_chu": read_amount_vi(total),
        # --- Hệ thống
        "ngay_lap": fmt_date(today),
    }
    assert set(ctx) == KNOWN_KEYS, "build_context lệch danh mục biến"
    return ctx
