"""Bộ cột + bộ parse ô của «Nhập Excel Nhân sự» (duoc-CR-628).

Một nguồn duy nhất cho: tiêu đề cột (kèm alias để tệp XUẤT cũ nhập lại được), kiểu ô, cờ nhạy cảm
(tính từ `employee.sensitive.SENSITIVE_FIELDS`, KHÔNG gõ danh sách thứ hai) và sheet «Huong dan».

Luật ô: cột vắng hoặc ô TRỐNG = giữ nguyên (không đưa vào dict ghi). Chỉ ô ghi `__/empty_value/__`
mới xóa. Parse sai KHÔNG đoán bừa mà ném `CellError` để dòng đó thành lỗi.
"""
import unicodedata
from datetime import date, datetime

from app.modules.employee.constants import (EDUCATION_LEVEL_LABELS, EMPLOYMENT_TYPE_LABELS,
                                            GENDER_LABELS, JOB_LEVEL_LABELS,
                                            MARITAL_STATUS_LABELS)
from app.modules.employee.sensitive import SENSITIVE_FIELDS
from app.modules.employee.status_parse import status_code_from_text

EMPTY_SENTINEL = "__/empty_value/__"          # trùng catalog_import.EMPTY_SENTINEL (tránh import vòng)

#  Ô bắt buộc / không được xóa bằng sentinel.
NOT_CLEARABLE = ("full_name", "status", "is_active")

#  attr -> bộ nhãn của cột mã số (nhận số hoặc nhãn).
CODE_LABELS = {
    "gender": GENDER_LABELS, "marital_status": MARITAL_STATUS_LABELS,
    "education_level": EDUCATION_LEVEL_LABELS, "employment_type": EMPLOYMENT_TYPE_LABELS,
    "job_level": JOB_LEVEL_LABELS,
}


def _ef(header, attr, t="str", aliases=None, required=False):
    """Một cột. `t`: str | date | code | bool | int | status | company | department | position | manager."""
    return {"header": header, "attr": attr, "t": t, "kind": t, "aliases": aliases or [],
            "required": required, "ref": None, "default": None,
            "sensitive": attr in SENSITIVE_FIELDS}


EMPLOYEE_FIELDS: list[dict] = [
    # Định danh
    _ef("Mã NV *", "code", aliases=["Mã nhân viên"], required=True),
    _ef("Họ tên *", "full_name"),   # bắt buộc khi TẠO (kiểm theo dòng), cột không bắt buộc có mặt
    _ef("Email", "email"),
    _ef("Điện thoại", "phone", aliases=["Số điện thoại"]),
    _ef("Email cá nhân", "personal_email"),
    _ef("Giới tính", "gender", "code"),
    _ef("Tình trạng hôn nhân", "marital_status", "code"),
    _ef("Trình độ học vấn", "education_level", "code"),
    _ef("Ngày sinh", "date_of_birth", "date"),
    _ef("Nơi sinh", "place_of_birth"),
    _ef("Dân tộc", "ethnicity"),
    _ef("Tôn giáo", "religion"),
    _ef("Số con", "children_count", "int"),
    _ef("Chuyên ngành", "major"),
    _ef("Mã số thuế", "tax_code"),
    # Công việc
    _ef("Công ty (mã)", "company_id", "company", aliases=["Công ty"]),
    _ef("Phòng ban (mã)", "department_id", "department", aliases=["Phòng ban"]),
    _ef("Chức vụ (mã/tên)", "position_id", "position", aliases=["Chức vụ", "Vị trí"]),
    _ef("Quản lý trực tiếp (mã NV)", "manager_id", "manager"),
    _ef("Hình thức nhân viên", "employment_type", "code"),
    _ef("Cấp bậc", "job_level", "code"),
    _ef("Nơi làm việc", "work_location"),
    _ef("Ngày vào làm", "hire_date", "date"),
    _ef("Ngày nghỉ việc", "resign_date", "date"),
    _ef("Trạng thái", "status", "status",
        aliases=["Trạng thái NS", "Trạng thái (official/probation/…)"]),
    _ef("Đang dùng (1/0)", "is_active", "bool", aliases=["Hoạt động (1/0)"]),
    # Địa chỉ
    _ef("Địa chỉ thường trú", "permanent_address"),
    _ef("Địa chỉ hiện tại", "current_address"),
    # Ngân hàng
    _ef("Số tài khoản", "bank_account_no"),
    _ef("Tên chủ tài khoản", "bank_account_name"),
    _ef("Ngân hàng", "bank_name"),
    _ef("Chi nhánh", "bank_branch"),
    # Giấy tờ
    _ef("Số CCCD", "id_number"),
    _ef("Ngày cấp CCCD", "id_issue_date", "date"),
    _ef("Nơi cấp CCCD", "id_issue_place"),
    _ef("Ngày hết hạn CCCD", "id_expiry_date", "date"),
    _ef("Số BHXH", "social_insurance_no"),
    _ef("Nơi KCB BHYT", "health_care_place"),
    _ef("Mã KCB BHYT", "health_care_code"),
]

FIELD_BY_ATTR = {f["attr"]: f for f in EMPLOYEE_FIELDS}
#  Mọi attr cột adapter có thể ghi (+ nhãn `position`) — dùng làm snapshot hoàn tác.
SNAPSHOT_ATTRS = [f["attr"] for f in EMPLOYEE_FIELDS if f["attr"] != "code"] + ["position"]
DATE_ATTRS = {f["attr"] for f in EMPLOYEE_FIELDS if f["t"] == "date"}
SENSITIVE_ATTRS = {f["attr"] for f in EMPLOYEE_FIELDS if f["sensitive"]}


def label_of(attr: str) -> str:
    """Nhãn cột để đưa vào thông báo lỗi (bỏ dấu sao)."""
    return FIELD_BY_ATTR[attr]["header"].replace(" *", "").replace("*", "").strip()


class CellError(Exception):
    """Ô không hợp lệ — câu thông báo KHÔNG chứa giá trị ô nhạy cảm."""


def fold(s: str) -> str:
    """Bỏ dấu + hạ chữ + gộp khoảng trắng — để so nhãn gõ lệch."""
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.replace("đ", "d").replace("Đ", "D").lower().split())


def cell_text(v) -> str:
    """Ô -> chuỗi. Số nguyên kiểu float của Excel (79123456789.0) về dạng nguyên."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, datetime):
        return v.date().isoformat()
    return str(v).strip()


def parse_date(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    t = cell_text(v)
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(t, fmt).date()
        except ValueError:
            continue
    raise CellError("ngày không đọc được — dùng dd/mm/yyyy hoặc yyyy-mm-dd")


def parse_code(attr: str, v) -> int:
    labels = CODE_LABELS[attr]
    t = cell_text(v)
    if t.lstrip("-").isdigit() and int(t) in labels:
        return int(t)
    f = fold(t)
    for code, lab in labels.items():
        if code and fold(lab) == f:
            return code
    valid = ", ".join(f"{c} = {lab}" for c, lab in labels.items() if c)
    raise CellError(f"giá trị không nhận ra. Nhận: {valid}")


def parse_bool(v) -> bool:
    f = fold(cell_text(v))
    if f in ("1", "true", "co", "yes", "y", "hoat dong", "dang dung", "bat"):
        return True
    if f in ("0", "false", "khong", "no", "n", "ngung", "ngung dung", "tat", "an"):
        return False
    raise CellError("chỉ nhận 1/0 (hoặc có/không)")


def parse_int(v) -> int:
    t = cell_text(v)
    try:
        return int(float(t))
    except (ValueError, OverflowError):          # "inf"/"1e999" -> OverflowError (L6)
        raise CellError("phải là số nguyên")


def parse_scalar(spec: dict, raw):
    """Parse ô KHÔNG cần tra DB. Trả giá trị đã xử lý; ném `CellError`. Gọi khi ô KHÔNG trống."""
    t, attr = spec["t"], spec["attr"]
    if cell_text(raw) == EMPTY_SENTINEL:
        if attr in NOT_CLEARABLE:
            raise CellError("không xóa được ô bắt buộc")
        return None if t == "date" else (0 if t in ("code", "int") else "")
    if t == "date":
        return parse_date(raw)
    if t == "code":
        return parse_code(attr, raw)
    if t == "bool":
        return parse_bool(raw)
    if t == "int":
        return parse_int(raw)
    if t == "status":
        code = status_code_from_text(cell_text(raw))
        if not code:
            from app.core.status_codes import EMPLOYEE_STATUS
            raise CellError("trạng thái không nhận ra. Nhận: " + " / ".join(EMPLOYEE_STATUS.labels.values()))
        return code
    return cell_text(raw)


TEMPLATE_NOTES: list[tuple[str, str]] = [
    ("Quy tắc chung", "Ô TRỐNG hoặc cột vắng = giữ nguyên giá trị cũ (không xóa). Muốn xóa một ô, ghi đúng "
                      "__/empty_value/__. Không xóa được ô bắt buộc (Họ tên, Trạng thái, Đang dùng)."),
    ("Mã NV", "Có mã khớp hồ sơ → cập nhật. Mã chưa có → tạo mới. Để trống → tạo mới và tự sinh mã NSU…; "
              "mã sinh ra ghi ở nhật ký lô."),
    ("Xóa nhân sự", "KHÔNG xóa được qua Excel. Muốn ngưng, đặt Trạng thái = Nghỉ việc (khóa luôn tài khoản "
                    "đăng nhập) hoặc Đang dùng = 0."),
    ("Ngày", "dd/mm/yyyy hoặc yyyy-mm-dd, hoặc ô kiểu ngày của Excel. Năm từ 1900 đến 2200."),
    ("Số CCCD / Số tài khoản / Điện thoại", "Định dạng ô là Văn bản (Text) để Excel không cắt số 0 ở đầu."),
    ("Giới tính", "1 = Nam, 2 = Nữ, 3 = Khác (hoặc gõ chữ)."),
    ("Tình trạng hôn nhân", "1 = Độc thân, 2 = Có gia đình, 3 = Ly hôn (hoặc gõ chữ)."),
    ("Trình độ học vấn", "1 = Phổ thông, 2 = Trung cấp, 3 = Cao đẳng, 4 = Đại học, 5 = Sau đại học."),
    ("Hình thức nhân viên", "1 = Toàn thời gian, 2 = Bán thời gian, 3 = Thời vụ, 4 = Cộng tác viên, "
                            "5 = Thử việc, 6 = Thực tập."),
    ("Cấp bậc", "1 = Nhân viên, 2 = Tổ trưởng, 3 = Phó phòng, 4 = Trưởng phòng, 5 = Giám đốc khối, "
                "6 = Ban tổng giám đốc."),
    ("Trạng thái", "Mã (official, probation, resigned…) hoặc nhãn (Chính thức, Nghỉ việc…). Sai thì dòng lỗi, "
                   "không tự đoán."),
    ("Công ty (mã)", "Mã, tên, mã số thuế hoặc tên viết tắt của pháp nhân."),
    ("Phòng ban (mã)", "Mã phòng ban; hoặc tên CHÍNH XÁC trong đúng công ty (trùng tên → lỗi)."),
    ("Chức vụ (mã/tên)", "Mã hoặc tên trong danh mục Chức vụ. Không khớp → giữ chữ làm chức danh, cảnh báo REVIEW."),
    ("Quản lý trực tiếp (mã NV)", "Mã nhân viên đã có trong hệ thống hoặc ở dòng PHÍA TRÊN trong cùng tệp."),
    ("Cột nhạy cảm", "Ngày sinh, MST, địa chỉ, ngân hàng, CCCD, BHXH: cần quyền ghi thông tin nhạy cảm; "
                     "không có quyền thì các cột này bị bỏ qua kèm cảnh báo."),
    ("Ngoài phạm vi", "Ảnh CCCD, trường tùy biến, người thân/liên hệ, kiêm nhiệm phòng ban, tài khoản đăng nhập "
                      "— làm ở màn hồ sơ."),
]
