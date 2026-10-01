from pydantic import BaseModel, field_validator

from app.core.contract_types import CONTRACT_TYPE_SET
from app.core.status_codes import CONTRACT_PARTY_TYPE, CONTRACT_STATUS
from app.modules.employee.field_limits import Str10, Str30, Str50, Str255


def _check_contract_type(v: str | None) -> str | None:
    """Chỉ nhận MÃ trong bộ cố định (CR-118). Chuỗi rỗng = chưa phân loại, vẫn cho qua.

    Cột này từng là chữ tự do nên mỗi màn tự bịa một bộ giá trị tiếng Việt khác nhau,
    dữ liệu thật thì lưu bộ thứ tư. Chặn ngay ở đây để không đẻ thêm giá trị lạ.

    B-01: dùng validator chung của `status_catalog` thay cho bản viết tay — thông điệp lỗi
    giữ nguyên định dạng cũ ("Loại hợp đồng không hợp lệ: x").
    """
    return CONTRACT_TYPE_SET.validate(v)


def _check_party_type(v: str | None) -> str | None:
    """B-02: chỉ nhận MÃ (`supplier` | `customer` | `other`), không nhận nhãn tiếng Việt.

    Chặn thẳng chứ KHÔNG tự dịch "Nhà cung cấp" thành `supplier`: dịch hộ thì bản giao diện
    cũ chưa vá vẫn chạy được, và sẽ không ai vá nữa cho tới lúc nó hỏng vì lý do khác.
    """
    return CONTRACT_PARTY_TYPE.validate(v)


def _check_status(v: str | None) -> str | None:
    """B-02: chỉ nhận MÃ (`active` | `expired` | `liquidated` | `cancelled`)."""
    return CONTRACT_STATUS.validate(v)


class ContractCreate(BaseModel):
    code: Str50 | None = None
    party_type: Str30 = "supplier"
    party_code: Str50 = ""
    party_name: Str255 = ""
    company_id: int = 0
    title: Str255 = ""
    contract_type: Str50 = ""
    start_date: Str10 = ""
    end_date: Str10 = ""
    signed: bool = False
    status: Str30 = "active"
    note: str = ""

    _v_type = field_validator("contract_type")(_check_contract_type)
    _v_party_type = field_validator("party_type")(_check_party_type)
    _v_status = field_validator("status")(_check_status)


class ContractUpdate(BaseModel):
    party_type: Str30 | None = None
    party_code: Str50 | None = None
    party_name: Str255 | None = None
    company_id: int | None = None
    title: Str255 | None = None
    contract_type: Str50 | None = None
    start_date: Str10 | None = None
    end_date: Str10 | None = None
    signed: bool | None = None
    status: Str30 | None = None
    note: str | None = None

    _v_type = field_validator("contract_type")(_check_contract_type)
    _v_party_type = field_validator("party_type")(_check_party_type)
    _v_status = field_validator("status")(_check_status)
