from pydantic import BaseModel, field_validator

from app.core.contract_types import CONTRACT_TYPE_SET
from app.core.status_codes import CONTRACT_PARTY_TYPE, CONTRACT_STATUS


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
    code: str | None = None
    party_type: str = "supplier"
    party_code: str = ""
    party_name: str = ""
    company_id: int = 0
    title: str = ""
    contract_type: str = ""
    start_date: str = ""
    end_date: str = ""
    signed: bool = False
    status: str = "active"
    note: str = ""

    _v_type = field_validator("contract_type")(_check_contract_type)
    _v_party_type = field_validator("party_type")(_check_party_type)
    _v_status = field_validator("status")(_check_status)


class ContractUpdate(BaseModel):
    party_type: str | None = None
    party_code: str | None = None
    party_name: str | None = None
    company_id: int | None = None
    title: str | None = None
    contract_type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    signed: bool | None = None
    status: str | None = None
    note: str | None = None

    _v_type = field_validator("contract_type")(_check_contract_type)
    _v_party_type = field_validator("party_type")(_check_party_type)
    _v_status = field_validator("status")(_check_status)
