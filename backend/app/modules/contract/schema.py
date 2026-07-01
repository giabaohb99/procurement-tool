from pydantic import BaseModel


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
