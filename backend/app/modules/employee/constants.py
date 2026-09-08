"""BỘ MÃ SỐ CỦA HỒ SƠ NHÂN SỰ — theo R2/QĐ-11.

Cột nào mang nghĩa *phân loại · cấp bậc · tình trạng* thì lưu `SMALLINT` và so với
hằng số ở đây; tiếng Việt chỉ sống trong các `*_LABELS` và ở tầng hiển thị. Cùng
khuôn với `leave/constants.py` và `vehicle_booking/model.py`.

⚠️ **`Employee.status` KHÔNG nằm ở đây** — cột đó lưu mã CHUỖI
(`app/core/status_codes.EMPLOYEE_STATUS`) từ đợt B-03. Đó là ngoại lệ lịch sử,
giữ nguyên; đừng đổi và cũng đừng lấy nó làm mẫu cho cột mới.

`0` ở mọi bộ mã dưới đây luôn nghĩa là **CHƯA KHAI**, không phải một giá trị
nghiệp vụ. Hồ sơ cũ nhập trước khi có cột đều mang `0`, nên chỗ nào đọc mà coi
`0` là "độc thân" hay "nhân viên" là gán bừa cho vài trăm con người.
"""

# --------------------------------------------------------------------------
# Giới tính — ĐÃ CÓ TỪ TRƯỚC (QĐ-NP3), khai lại ở đây để một chỗ tra
# --------------------------------------------------------------------------
#  ⚠️ Ba mã đầu vẫn lấy từ `leave/constants.py` (`GENDER_UNKNOWN/MALE/FEMALE`):
#  luật chặn loại nghỉ theo giới đọc từ đó. Ở đây nhắc lại con số để người đọc
#  hồ sơ nhân sự không phải mở sang phân hệ Nghỉ phép.
#
#  ⚠️ **`3` = «Khác» chỉ tồn tại cho HỒ SƠ CON NGƯỜI** (khách chốt 08/09/2026),
#  KHÔNG phải một lựa chọn của `tab_leave_type.gender`. Loại nghỉ chỉ nhận
#  `0` (mọi giới) · `1` · `2` — nên `leave/constants.GENDER_LABELS` cố ý KHÔNG
#  có mục này. Thêm vào đó là bày ra loại nghỉ "chỉ dành cho giới Khác".
#
#  ⚠️ Hệ quả ở nghỉ phép, có chủ ý: `check_gender` so `want != got`, nên người
#  khai «Khác» **bị chặn** khỏi loại nghỉ giới hạn nam hoặc nữ (thai sản). Đó là
#  khác biệt với `0` — chưa khai thì KHÔNG chặn. Ai cần ngoại lệ thì Nhân sự
#  chỉnh lại ô giới tính, đừng nới luật ở `request_service`.
GENDER_UNKNOWN = 0
GENDER_MALE = 1
GENDER_FEMALE = 2
GENDER_OTHER = 3

GENDER_VALUES = (GENDER_UNKNOWN, GENDER_MALE, GENDER_FEMALE, GENDER_OTHER)

GENDER_LABELS = {
    GENDER_UNKNOWN: "",
    GENDER_MALE: "Nam",
    GENDER_FEMALE: "Nữ",
    GENDER_OTHER: "Khác",
}

# --------------------------------------------------------------------------
# Tình trạng hôn nhân
# --------------------------------------------------------------------------
MARITAL_UNKNOWN = 0
MARITAL_SINGLE = 1
MARITAL_MARRIED = 2
MARITAL_DIVORCED = 3

MARITAL_STATUS_LABELS = {
    MARITAL_UNKNOWN: "",
    MARITAL_SINGLE: "Độc thân",
    MARITAL_MARRIED: "Có gia đình",
    MARITAL_DIVORCED: "Ly hôn",
}

# --------------------------------------------------------------------------
# Trình độ học vấn
# --------------------------------------------------------------------------
EDUCATION_UNKNOWN = 0
EDUCATION_HIGH_SCHOOL = 1
EDUCATION_INTERMEDIATE = 2
EDUCATION_COLLEGE = 3
EDUCATION_UNIVERSITY = 4
EDUCATION_POSTGRADUATE = 5

EDUCATION_LEVEL_LABELS = {
    EDUCATION_UNKNOWN: "",
    EDUCATION_HIGH_SCHOOL: "Phổ thông",
    EDUCATION_INTERMEDIATE: "Trung cấp",
    EDUCATION_COLLEGE: "Cao đẳng",
    EDUCATION_UNIVERSITY: "Đại học",
    EDUCATION_POSTGRADUATE: "Sau đại học",
}

# --------------------------------------------------------------------------
# Hình thức làm việc
# --------------------------------------------------------------------------
EMPLOYMENT_UNKNOWN = 0
EMPLOYMENT_FULL_TIME = 1
EMPLOYMENT_PART_TIME = 2
EMPLOYMENT_SEASONAL = 3
EMPLOYMENT_COLLABORATOR = 4
EMPLOYMENT_PROBATION = 5
EMPLOYMENT_INTERN = 6

EMPLOYMENT_TYPE_LABELS = {
    EMPLOYMENT_UNKNOWN: "",
    EMPLOYMENT_FULL_TIME: "Toàn thời gian",
    EMPLOYMENT_PART_TIME: "Bán thời gian",
    EMPLOYMENT_SEASONAL: "Thời vụ",
    EMPLOYMENT_COLLABORATOR: "Cộng tác viên",
    EMPLOYMENT_PROBATION: "Thử việc",
    EMPLOYMENT_INTERN: "Thực tập",
}

# --------------------------------------------------------------------------
# Cấp bậc
# --------------------------------------------------------------------------
#  ⚠️ ĐỪNG dùng cột này để suy ra NGƯỜI DUYỆT. Cấp bậc là thông tin nhân sự (để
#  lọc danh sách, để làm báo cáo cơ cấu); người duyệt của một tờ đơn suy từ
#  `manager_id` và từ trưởng bộ phận trong bảng phòng ban. Trộn hai thứ lại thì
#  sửa một ô hồ sơ là đổi đường đi của chứng từ mà không ai thấy.
JOB_LEVEL_UNKNOWN = 0
JOB_LEVEL_STAFF = 1
JOB_LEVEL_TEAM_LEADER = 2
JOB_LEVEL_DEPUTY_MANAGER = 3
JOB_LEVEL_MANAGER = 4
JOB_LEVEL_DIRECTOR = 5
JOB_LEVEL_EXECUTIVE = 6

JOB_LEVEL_LABELS = {
    JOB_LEVEL_UNKNOWN: "",
    JOB_LEVEL_STAFF: "Nhân viên",
    JOB_LEVEL_TEAM_LEADER: "Tổ trưởng",
    JOB_LEVEL_DEPUTY_MANAGER: "Phó phòng",
    JOB_LEVEL_MANAGER: "Trưởng phòng",
    JOB_LEVEL_DIRECTOR: "Giám đốc khối",
    JOB_LEVEL_EXECUTIVE: "Ban tổng giám đốc",
}

# --------------------------------------------------------------------------
# Quan hệ nhân thân — dùng cho CẢ HAI bảng con
# --------------------------------------------------------------------------
#  Bản đầu (duoc-CR-314) để `relation` là chữ TỰ DO với lý lẽ "quan hệ gia đình
#  Việt Nam không đóng được thành một danh sách ngắn". Khách chốt ngược lại
#  08/09/2026: phải là Ô CHỌN. Chữ tự do làm mỗi người gõ một kiểu — «vợ», «Vợ»,
#  «v/c», «vo» — nên không lọc được, không đếm được, và bản in ra không đều.
#
#  Thành danh sách cố định thì R2/QĐ-11 áp dụng: lưu SMALLINT, không lưu chữ.
#  Đổi ngay bây giờ vì bảng con **chưa lên prod** — đây là lúc rẻ nhất; để có
#  dữ liệu thật rồi mới đổi thì phải viết migration dịch từng chuỗi.
#
#  ⚠️ Danh sách dùng CHUNG cho cả hai bảng và **không lọc theo giới tính**
#  (khách chốt). Bảng hộ gia đình ghi quan hệ với CHỦ HỘ, bảng người báo tin ghi
#  quan hệ với NHÂN VIÊN — cùng một bộ từ, khác gốc quy chiếu.
RELATION_UNKNOWN = 0
RELATION_HOUSEHOLD_HEAD = 1
RELATION_FATHER = 2
RELATION_MOTHER = 3
RELATION_WIFE = 4
RELATION_HUSBAND = 5
RELATION_SON = 6
RELATION_DAUGHTER = 7
RELATION_OLDER_BROTHER = 8
RELATION_OLDER_SISTER = 9
RELATION_YOUNGER_BROTHER = 10
RELATION_YOUNGER_SISTER = 11
RELATION_GRANDFATHER = 12
RELATION_GRANDMOTHER = 13
#  `99` chứ không phải `14`: chừa chỗ cho các quan hệ thêm về sau được đánh số
#  liền mạch, và «Khác» thì luôn đứng cuối danh sách.
RELATION_OTHER = 99

RELATION_LABELS = {
    RELATION_UNKNOWN: "",
    RELATION_HOUSEHOLD_HEAD: "Chủ hộ",
    RELATION_FATHER: "Cha",
    RELATION_MOTHER: "Mẹ",
    RELATION_WIFE: "Vợ",
    RELATION_HUSBAND: "Chồng",
    RELATION_SON: "Con trai",
    RELATION_DAUGHTER: "Con gái",
    RELATION_OLDER_BROTHER: "Anh trai",
    RELATION_OLDER_SISTER: "Chị gái",
    RELATION_YOUNGER_BROTHER: "Em trai",
    RELATION_YOUNGER_SISTER: "Em gái",
    RELATION_GRANDFATHER: "Ông",
    RELATION_GRANDMOTHER: "Bà",
    RELATION_OTHER: "Khác",
}

# --------------------------------------------------------------------------
# Trần số khóa của ô tùy biến
# --------------------------------------------------------------------------
#  `extra_fields` là cột JSON mở cho nhu cầu lẻ (size áo, hộ chiếu…). Có trần vì
#  cột JSON không ai rà: không chặn thì nó thành nơi đổ mọi thứ người ta ngại xin
#  thêm cột, và ba năm sau không ai biết khóa nào còn dùng.
#
#  ⚠️ **KHÔNG** sinh cột động kiểu `vanbanngan17_5_0` của HrOnline. Nhu cầu nào
#  lặp lại đủ nhiều thì xin một cột thật, đừng nuôi nó trong JSON.
MAX_EXTRA_FIELDS = 20


def label_of(labels: dict[int, str], value: int | None) -> str:
    """Nhãn tiếng Việt của một mã số. Mã lạ → chuỗi rỗng.

    Trả rỗng chứ KHÔNG trả lại chính con số: giao diện đã có nhánh lùi, còn ở đây
    trả rỗng thì nhìn dữ liệu là biết ngay dòng nào mang giá trị ngoài bộ mã.
    Cùng lý lẽ với `Employee.status_label` (B-03).
    """
    return labels.get(int(value or 0), "")
