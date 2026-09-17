"""BỘ TRƯỜNG TÙY BIẾN của một loại hồ sơ — phần «metadata» của phân hệ Hồ sơ.

Mỗi loại hồ sơ tự khai danh sách ô nhập riêng của nó (`tab_dossier_type.
field_schema`), và màn lập hồ sơ dựng biểu mẫu **theo loại đang chọn**. Giấy
phép con hỏi *Số giấy phép · Cơ quan cấp*; hợp đồng hỏi *Đối tác · Giá trị*.
Không loại nào phải chờ lập trình viên thêm cột.

⚠️ **Đây là chỗ đổi lấy: mềm dẻo ăn mất tính toàn vẹn.** Giá trị nằm trong một ô
JSON nên không cột nào ràng buộc chúng, không khóa ngoại nào trỏ tới, và không
truy vấn SQL nào lọc chúng cho ra hồn. Nhu cầu nào **lặp lại ở mọi loại hồ sơ**
thì xin một CỘT THẬT, đừng khai vào đây — cột thật mới lọc, sắp xếp và báo cáo
được.

⚠️ **Trần khai ở đây là chốt chặn thật, không phải cho gọn** (bài học
duoc-CR-316): ô JSON không khai trần thì 20 khóa × 2MB = 40MB một bản ghi, MySQL
nhận hết và không gì nổ — chỉ là mọi màn đọc hồ sơ đó về sau đều đứng hình mà
không ai truy ra vì sao.
"""
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

from .reference_sources import REFERENCE_LABELS, is_known

#  Kiểu ô nhập mà biểu mẫu hồ sơ dựng được. Cố ý là một tập ĐÓNG và khớp đúng
#  `CrudFormField['type']` của `frontend-v2/src/shared/crud/types.ts` — kiểu lạ
#  lọt xuống thì giao diện không biết vẽ ô gì và người dùng mất trắng ô đó.
#
#  KHÔNG có `percent`: ô phần trăm quy đổi giữa 8 và 0.08 ở tầng giao diện
#  (`field-values.ts`), mà quy đổi ấy chỉ đúng khi nơi nhận biết trường nào là
#  phần trăm — ô JSON thì không ai biết. Cần tỷ lệ thì khai `number` và ghi đơn
#  vị vào nhãn.
#  `reference` = chọn từ DANH MỤC có sẵn (nhân sự, nhà cung cấp…) và lưu **ID**,
#  khác `select` vốn chọn từ danh sách chữ người dùng tự gõ. Giữ cả hai: danh
#  mục thì có `reference`, còn mấy tập hai-ba giá trị đặc thù («Bắt buộc /
#  Không bắt buộc») thì không có danh mục nào để mà trỏ tới.
FIELD_TYPES = ("text", "textarea", "number", "date", "select", "reference", "switch")
FieldType = Literal["text", "textarea", "number", "date", "select", "reference", "switch"]

#  Số ô tùy biến tối đa của MỘT loại hồ sơ. Hai mươi ô đã là một biểu mẫu dài
#  hơn màn hình; quá đó thì thứ người ta cần là một phân hệ riêng, không phải
#  thêm ô.
MAX_FIELDS = 20
#  Số mục tối đa của một ô chọn. Danh sách dài hơn thì nó là một DANH MỤC (có
#  màn quản lý, có mã, sửa được) chứ không phải mấy dòng gõ thẳng vào cấu hình.
MAX_OPTIONS = 30
MAX_OPTION_LEN = 100
#  Tổng kích thước bộ trường, tính theo JSON đã tuần tự hoá. Bốn chốt trên vẫn
#  để lọt 20 ô × 30 mục × 100 ký tự tiếng Việt.
MAX_SCHEMA_BYTES = 16_000

Key40 = Annotated[str, StringConstraints(max_length=40)]
Label100 = Annotated[str, StringConstraints(max_length=100)]
Hint200 = Annotated[str, StringConstraints(max_length=200)]


class DossierFieldDef(BaseModel):
    """Khai báo MỘT ô nhập tùy biến."""

    #  ⚠️ `key` là tên khóa trong `tab_dossier.extra_fields` — tức là thứ dữ liệu
    #  đã lưu bám vào. Ép chữ thường + gạch dưới vì nó đi vào JSON, vào tiêu đề
    #  cột tệp Excel và vào tên ô của react-hook-form; RHF cắt chuỗi theo dấu
    #  chấm để hiểu là đường dẫn lồng nhau, nên một dấu chấm trong khóa là ô đó
    #  ghi vào nhầm chỗ, im lặng.
    key: Key40
    label: Label100
    type: FieldType = "text"
    required: bool = False
    #  Chỉ có nghĩa với `type="select"`. Để rỗng ở kiểu khác thay vì cấm, vì
    #  người dùng đổi kiểu qua lại trên giao diện và xóa sạch mục đã gõ mỗi lần
    #  đổi là mất công gõ lại.
    options: list[str] = []
    #  Chỉ có nghĩa với `type="reference"` — KHÓA của một danh mục trong
    #  `reference_sources.REFERENCE_MODELS`, KHÔNG phải một URL. Xem ghi chú dài
    #  ở tệp đó: nhận URL từ máy khách là biến ô chọn thành cửa dò endpoint.
    source: Key40 = ""
    hint: Hint200 = ""

    @field_validator("key")
    @classmethod
    def _key_is_slug(cls, v: str) -> str:
        key = (v or "").strip().lower().replace("-", "_").replace(" ", "_")
        if not key:
            raise ValueError("Mã trường không được để trống")
        if not key[0].isalpha():
            raise ValueError(f"Mã trường «{key}» phải bắt đầu bằng chữ cái")
        if not all(c.isalnum() and c.isascii() or c == "_" for c in key):
            raise ValueError(
                f"Mã trường «{key}» chỉ gồm chữ không dấu, số và gạch dưới"
            )
        return key

    @field_validator("label")
    @classmethod
    def _label_not_blank(cls, v: str) -> str:
        label = (v or "").strip()
        if not label:
            raise ValueError("Tên trường không được để trống")
        return label

    @field_validator("options")
    @classmethod
    def _options_clean(cls, v: list[str]) -> list[str]:
        items = [str(x).strip() for x in (v or [])]
        items = [x for x in items if x]
        if len(items) > MAX_OPTIONS:
            raise ValueError(f"Một ô chọn tối đa {MAX_OPTIONS} mục (đang khai {len(items)})")
        for item in items:
            if len(item) > MAX_OPTION_LEN:
                raise ValueError(f"Mỗi mục của ô chọn tối đa {MAX_OPTION_LEN} ký tự")
        #  Hai mục trùng chữ thì ô chọn hiện hai dòng y hệt nhau, bấm dòng nào
        #  cũng ra một giá trị — người dùng tưởng mình bấm nhầm.
        if len(set(items)) != len(items):
            raise ValueError("Các mục của ô chọn không được trùng nhau")
        return items


def validate_field_schema(value: list | None) -> list[dict]:
    """Kiểm cả bộ trường của một loại hồ sơ. Trả về dạng đã chuẩn hoá để lưu.

    ⚠️ Trả `list[dict]` chứ không trả `list[DossierFieldDef]`: cột là JSON, và
    SQLAlchemy cần thứ `json.dumps` nuốt được.
    """
    import json

    raw = value or []
    if not isinstance(raw, list):
        raise ValueError("Bộ trường tùy biến phải là một danh sách")
    if len(raw) > MAX_FIELDS:
        raise ValueError(
            f"Một loại hồ sơ tối đa {MAX_FIELDS} ô tùy biến (đang khai {len(raw)}). "
            "Nhu cầu nhiều hơn thế thì thứ cần dựng là một phân hệ riêng."
        )

    defs = [DossierFieldDef.model_validate(item) for item in raw]

    #  ⚠️ Trùng `key` là ca hỏng NGẦM nhất của cả tệp này: hai ô khai cùng khóa
    #  thì chúng ghi đè nhau trong `extra_fields`, biểu mẫu vẫn hiện đủ hai ô,
    #  người dùng gõ hai giá trị khác nhau và chỉ một cái sống sót — không lỗi,
    #  không cảnh báo.
    keys = [d.key for d in defs]
    dup = {k for k in keys if keys.count(k) > 1}
    if dup:
        raise ValueError(f"Mã trường bị trùng: {', '.join(sorted(dup))}")

    for d in defs:
        if d.type == "select" and not d.options:
            raise ValueError(f"Ô chọn «{d.label}» phải khai ít nhất một mục")
        if d.type == "reference":
            if not d.source:
                raise ValueError(f"Ô «{d.label}» phải chọn một danh mục để lấy dữ liệu")
            if not is_known(d.source):
                raise ValueError(
                    f"Ô «{d.label}» trỏ tới danh mục không có thật: «{d.source}». "
                    f"Nhận: {', '.join(sorted(REFERENCE_LABELS))}."
                )

    out = [d.model_dump() for d in defs]
    size = len(json.dumps(out, ensure_ascii=False).encode())
    if size > MAX_SCHEMA_BYTES:
        raise ValueError(
            f"Bộ trường tùy biến tối đa {MAX_SCHEMA_BYTES} byte (đang gửi {size})."
        )
    return out


def parse_field_defs(value: list | None) -> list[DossierFieldDef]:
    """Đọc bộ trường ĐÃ LƯU thành đối tượng, bỏ qua dòng hỏng.

    ⚠️ Khoan dung ở ĐƯỜNG ĐỌC là cố ý, ngược hẳn với `validate_field_schema` ở
    đường ghi. Một dòng khai hỏng dưới DB (sót lại từ bản cũ, hay ai đó sửa tay)
    mà làm cả màn hồ sơ trả 500 thì hỏng một ô thành mất cả phân hệ.
    """
    defs: list[DossierFieldDef] = []
    for item in value or []:
        try:
            defs.append(DossierFieldDef.model_validate(item))
        except Exception:  # noqa: BLE001 — dòng hỏng thì bỏ qua, xem docstring
            continue
    return defs
