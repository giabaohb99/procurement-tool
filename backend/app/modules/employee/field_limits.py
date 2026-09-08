"""RÀNG BUỘC KÍCH THƯỚC của hồ sơ nhân sự — chặn ở schema, không để MySQL nổ.

Vì sao có tệp này (duoc-CR-316, 08/09/2026): bắn thử vào MySQL thật thì **sáu
nhóm ca trả 500** «Hệ thống gặp lỗi không lường trước». Không ca nào là lỗi
logic — tất cả chỉ vì Pydantic không khai giới hạn, nên chuỗi dài / JSON khổng
lồ / ngày năm 0001 đi thẳng xuống cột và **MySQL** là chỗ đầu tiên phản đối.

Hậu quả thật: người dùng dán nhầm một đoạn văn bản vào ô «Mã số thuế» thì nhận
được một mã sự cố, quản trị đi tra một lỗi vốn đáng ra phải là câu *«tối đa 20
ký tự»*. Chặn ở đây thì cùng một tình huống ra 422 kèm câu tiếng Việt, và tra
được ngay ô nào sai.

⚠️ **Số trong tệp này phải khớp `model.py`.** Đổi độ dài cột mà quên sửa ở đây
thì hoặc chặn hụt (500 quay lại), hoặc chặn thừa (người dùng không dùng hết
được ô). `test_ho_so_nhan_su_cuc_doan.py` canh từng cặp một.

⚠️ **SQLite KHÔNG ép độ dài VARCHAR**, nên bộ test không thể phát hiện việc
thiếu khai bằng cách ghi xuống DB — nó phải kiểm thẳng ở tầng schema.
"""
from datetime import date
from typing import Annotated

from pydantic import Field, StringConstraints

# ── Chuỗi: bí danh theo ĐỘ DÀI CỘT ở `model.py` ────────────────────────────
#  Đặt tên theo con số để nơi dùng đọc là đối chiếu được ngay với `String(n)`.
Str20 = Annotated[str, StringConstraints(max_length=20)]
Str25 = Annotated[str, StringConstraints(max_length=25)]
#  `Str30` = mã chức vụ (`tab_job_position.code`), thêm ở duoc-CR-320.
Str30 = Annotated[str, StringConstraints(max_length=30)]
Str50 = Annotated[str, StringConstraints(max_length=50)]
Str100 = Annotated[str, StringConstraints(max_length=100)]
Str255 = Annotated[str, StringConstraints(max_length=255)]
Str500 = Annotated[str, StringConstraints(max_length=500)]

# ── Ngày: dải HỢP LÝ, hẹp hơn dải MySQL cho phép ───────────────────────────
#  MySQL `DATE` nhận tới năm 9999, nhưng một hồ sơ nhân sự thì không.
#
#  ⚠️ Đây KHÔNG phải chuyện gọn gàng dữ liệu. `hire_date` là mốc tính THÂM
#  NIÊN, và `balance_service` cộng ngày phép theo bậc thâm niên — gõ nhầm năm
#  0001 là người đó có hai nghìn năm thâm niên, tức một số ngày phép mà không
#  dòng mã nào coi là vô lý. Ngày sinh năm 9999 thì ngược lại: âm thâm niên.
MIN_PROFILE_YEAR = 1900
MAX_PROFILE_YEAR = 2200

#  Ngày nào cũng đi qua đây. Dùng `date` chứ không dùng chuỗi: Pydantic đã tự
#  phân tích `"1990-05-01"` thành `date` trước khi tới validator.
ProfileDate = Annotated[
    date,
    Field(ge=date(MIN_PROFILE_YEAR, 1, 1), le=date(MAX_PROFILE_YEAR, 12, 31)),
]

# ── Ô JSON tùy biến ────────────────────────────────────────────────────────
#  Trần SỐ KHÓA đã có từ đầu (`MAX_EXTRA_FIELDS`), nhưng nó không cứu được gì:
#  20 khóa × 2MB = 40MB một hồ sơ, MySQL nhận hết (cột JSON chứa tới 1GB) và
#  không có gì nổ — chỉ là mọi màn hình đọc hồ sơ đó về sau đều đứng hình, và
#  không ai truy ra vì sao. Nên phải chặn thêm ba chiều dưới đây.
MAX_EXTRA_KEY_LEN = 60
MAX_EXTRA_VALUE_LEN = 500
#  Tổng cả ô, tính theo JSON đã tuần tự hoá.
MAX_EXTRA_TOTAL_BYTES = 8_000

#  ⚠️ CHỈ nhận giá trị VÔ HƯỚNG. Ô này sinh ra cho nhu cầu LẺ — size áo, số hộ
#  chiếu, đã tiêm vắc xin — tức mỗi khóa một giá trị. Nhận cả cây lồng nhau là
#  biến nó thành một cơ sở dữ liệu thứ hai mà không ai rà, không ai di trú
#  được, và không màn hình nào hiện nổi. (Kèm lý do kỹ thuật: JSON lồng quá sâu
#  làm MySQL từ chối thẳng → 500.)
_SCALAR_TYPES = (str, int, float, bool, type(None))

#  Số dòng tối đa của MỘT bảng con (người báo tin / hộ gia đình).
#
#  Đây là bảng «cha, mẹ, vợ/chồng» nằm trong một tab — vài chục dòng đã là vô
#  lý. Không có trần thì `PUT` 5000 dòng lọt thẳng (đã thử được trên MySQL
#  thật), và `sort_order` là `SMALLINT` nên dòng thứ 32768 còn tràn kiểu.
MAX_PEOPLE_ROWS = 30


def check_extra_fields(value: dict | None, max_keys: int) -> dict:
    """Ràng buộc ô `extra_fields` — bốn chiều, thứ tự từ rẻ tới đắt."""
    import json

    v = value or {}
    if not isinstance(v, dict):
        raise ValueError("Trường tùy biến phải là một đối tượng {khóa: giá trị}")

    if len(v) > max_keys:
        raise ValueError(f"Trường tùy biến tối đa {max_keys} mục (đang gửi {len(v)}). "
                         "Nhu cầu lặp lại nhiều thì xin một cột thật.")

    for key, item in v.items():
        if len(str(key)) > MAX_EXTRA_KEY_LEN:
            raise ValueError(f"Tên trường tùy biến tối đa {MAX_EXTRA_KEY_LEN} ký tự")
        if not isinstance(item, _SCALAR_TYPES):
            raise ValueError(
                f"Trường tùy biến «{key}» phải là một giá trị đơn (chữ, số, đúng/sai). "
                "Ô này dành cho nhu cầu lẻ như size áo hay số hộ chiếu, "
                "không phải nơi chứa cấu trúc lồng nhau.")
        if isinstance(item, str) and len(item) > MAX_EXTRA_VALUE_LEN:
            raise ValueError(f"Giá trị của «{key}» tối đa {MAX_EXTRA_VALUE_LEN} ký tự")

    #  Chốt cuối theo TỔNG kích thước — ba chốt trên vẫn để lọt 20 khóa × 500
    #  ký tự × 4 byte/ký tự tiếng Việt.
    size = len(json.dumps(v, ensure_ascii=False).encode())
    if size > MAX_EXTRA_TOTAL_BYTES:
        raise ValueError(f"Trường tùy biến tối đa {MAX_EXTRA_TOTAL_BYTES} byte "
                         f"(đang gửi {size}).")
    return v


def check_resign_after_hire(hire, resign) -> None:
    """Nghỉ việc không thể TRƯỚC ngày vào làm.

    Cho phép BẰNG nhau — vào làm rồi nghỉ ngay trong ngày là chuyện có thật
    (thử việc một buổi rồi thôi).

    ⚠️ Chỉ so khi payload có ĐỦ CẢ HAI. `PATCH` sửa riêng ô ngày nghỉ việc thì
    không có `hire_date` để so, và chặn lúc đó là chặn nhầm một thao tác hợp lệ.
    Đổi lại: sửa riêng một ô vẫn có thể tạo ra cặp ngược đời — chốt này bắt
    được ca thường gặp (nhập cả hai cùng lúc), không bắt được mọi ca. Bắt hết
    thì phải đọc bản ghi cũ trong validator, tức kéo tầng dữ liệu vào schema.
    """
    if hire is not None and resign is not None and resign < hire:
        raise ValueError("Ngày nghỉ việc không được trước ngày vào làm")
