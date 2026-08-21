from pydantic import BaseModel, field_validator

from app.core.contract_types import CONTRACT_TYPE_VALUES


def _check_contract_type(v: str | None) -> str | None:
    """Chỉ nhận MÃ trong bộ cố định (CR-118). Chuỗi rỗng = chưa phân loại, vẫn cho qua.

    Cột này từng là chữ tự do nên mỗi màn tự bịa một bộ giá trị tiếng Việt khác nhau,
    dữ liệu thật thì lưu bộ thứ tư. Chặn ngay ở đây để không đẻ thêm giá trị lạ.
    """
    if v is None or v == "":
        return v
    if v not in CONTRACT_TYPE_VALUES:
        raise ValueError(f"Loại hợp đồng không hợp lệ: {v}")
    return v


class ContractCreate(BaseModel):
    code: str | None = None
    party_type: str = "Nhà cung cấp"
    party_code: str = ""
    party_name: str = ""
    company_id: int = 0
    title: str = ""
    contract_type: str = ""
    start_date: str = ""
    end_date: str = ""
    signed: bool = False
    status: str = "Hiệu lực"
    note: str = ""

    _v_type = field_validator("contract_type")(_check_contract_type)


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
