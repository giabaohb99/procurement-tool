"""NHÓM TRƯỜNG NHẠY CẢM của hồ sơ nhân sự — một danh sách, một chỗ che.

Vì sao khai cứng ngay từ đầu thay vì thêm phân quyền sau: thêm phân quyền vào
một cột đã có dữ liệu là việc đắt — phải rà lại mọi màn, mọi bản in, mọi tệp
xuất đã trót hiện nó ra, và trong lúc rà thì dữ liệu vẫn đang lộ.

**Che ở tầng SERIALIZER, không che ở giao diện.** Ẩn ô trên màn hình thì API,
tệp CSV/XLSX và trợ lý AI vẫn trả nguyên số tài khoản ngân hàng của cả công ty —
ba đường vòng mà không đường nào cần biết gõ lệnh gì đặc biệt.

⚠️ **Hai bảng con (`tab_employee_contact`, `tab_employee_family`) thuộc trọn
nhóm này.** Chúng KHÔNG có khóa phân quyền riêng, và đó là chủ ý: chúng không có
màn hình riêng (luật «một khóa = một màn hình», CR-157), mà phạm vi dữ liệu của
chúng cũng không diễn đạt được bằng khuôn một-cột của `apply_scope` — bảng con
chỉ có `employee_id`, không có `company_id`/`department_id`. Nên chốt của chúng
là chốt của HỒ SƠ CHA: `get_scoped(Employee, "employee", ...)` để xét phạm vi, và
`employee_sensitive.read` để xét có được xem nội dung hay không.
"""

#  Đọc ô này là biết ngày sinh, số CCCD, địa chỉ nhà và số tài khoản ngân hàng
#  của một con người — đủ để mạo danh họ ở ngân hàng hoặc tìm tới tận nhà.
#
#  KHÔNG có trong danh sách (cố ý): `health_care_place` / `health_care_code` —
#  nơi khám chữa bệnh BHYT là thứ hành chính hỏi nhau hằng ngày để làm thủ tục,
#  giấu nó chỉ tạo ra một vòng hỏi qua Zalo. Cũng không có `personal_email`:
#  nhạy cảm hơn email công việc nhưng không dùng để mạo danh được.
SENSITIVE_FIELDS: tuple[str, ...] = (
    # Nhóm 1
    "date_of_birth",
    "tax_code",
    # Nhóm 3 — địa chỉ nhà riêng
    "permanent_address",
    "current_address",
    # Nhóm 4 — ngân hàng nhận lương
    "bank_account_no",
    "bank_account_name",
    "bank_name",
    "bank_branch",
    # Nhóm 5 — giấy tờ tùy thân và BHXH
    "id_number",
    "id_issue_date",
    "id_issue_place",
    "id_expiry_date",
    "id_front_image",
    "id_back_image",
    "social_insurance_no",
)

#  Giá trị thay thế khi che. Trả về ĐÚNG KIỂU của trường chứ không trả `None`
#  cho tất cả: `EmployeeOut` khai `bank_name: str`, nhét `None` vào là 500 ngay
#  ở `model_validate` — một lỗi chỉ nổ với người KHÔNG có quyền, tức đúng nhóm
#  người ít ai ngồi thử.
_BLANK_BY_FIELD: dict[str, object] = {
    "date_of_birth": None,
    "id_issue_date": None,
    "id_expiry_date": None,
}


def can_read_sensitive(profile, employee_id: int = 0) -> bool:
    """Người này có được xem nhóm nhạy cảm của hồ sơ `employee_id` không.

    Hai đường vào:

    * Có khóa `employee_sensitive.read` (phòng Nhân sự, quản trị).
    * **Hồ sơ của CHÍNH MÌNH** — ngoại lệ `self`. Không ai phải xin quyền để đọc
      số CCCD của bản thân, và chặn thì màn *Trang cá nhân* rỗng một nửa với
      chính chủ.

    `employee_id = 0` nghĩa là đang hỏi cho MỘT DANH SÁCH, không cho một hồ sơ cụ
    thể — lúc đó chỉ khóa quyền mới tính. Nhánh `self` phải xét theo từng dòng,
    và nơi gọi (`mask_many`) làm việc đó.
    """
    perms = (profile or {}).get("perms_union") or {}
    if (perms.get("employee_sensitive") or {}).get("read"):
        return True
    me = int((profile or {}).get("employee_id") or 0)
    #  ⚠️ Chặn `me == 0`: tài khoản chưa gắn nhân sự (admin, tài khoản hệ thống)
    #  có `employee_id = 0`, mà hồ sơ nào chưa lưu cũng có id 0 trong bộ nhớ —
    #  so bằng thì «chưa gắn ai» hóa ra khớp, và ngoại lệ self mở cho tất cả.
    return bool(me) and me == int(employee_id or 0)


def mask(data: dict, allowed: bool) -> dict:
    """Xóa trắng các trường nhạy cảm trong MỘT dict đã `model_dump()`.

    Xóa trắng chứ không **bỏ khóa** khỏi dict: bỏ khóa thì giao diện phải phân
    biệt "không có quyền" với "chưa nhập" bằng cách đoán, và mọi chỗ đọc phải
    thêm một nhánh `if "bank_name" in data`. Ô rỗng đọc ra đúng như ô chưa nhập,
    và đó là điều mình muốn — người không có quyền không cần biết ô đó có dữ
    liệu hay không.

    Sửa TẠI CHỖ rồi trả lại chính dict đó (tiện xâu chuỗi ở tầng controller).
    """
    if allowed:
        return data
    for f in SENSITIVE_FIELDS:
        if f in data:
            data[f] = _BLANK_BY_FIELD.get(f, "")
    return data


def mask_many(rows: list[dict], profile) -> list[dict]:
    """Che cho cả một DANH SÁCH, xét ngoại lệ `self` theo từng dòng.

    Không có khóa quyền thì vẫn phải để nguyên dòng hồ sơ của chính người đang
    xem — họ tìm thấy mình trong danh sách rồi thấy ngày sinh trống trong khi
    trang cá nhân hiện đầy đủ thì đó là một mâu thuẫn không giải thích được.
    """
    if can_read_sensitive(profile):
        return rows
    me = int((profile or {}).get("employee_id") or 0)
    for r in rows:
        mask(r, bool(me) and int(r.get("id") or 0) == me)
    return rows
