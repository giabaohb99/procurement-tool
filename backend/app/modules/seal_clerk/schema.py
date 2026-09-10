from pydantic import BaseModel, ConfigDict


class SealClerkCreate(BaseModel):
    employee_id: int
    company_id: int = 0
    is_head: bool = False


class SealClerkBulk(BaseModel):
    """Gán MỘT văn thư cho NHIỀU công ty một lần (mỗi công ty một dòng)."""
    employee_id: int
    company_ids: list[int] = []
    is_head: bool = False


class SealClerkUpdate(BaseModel):
    company_id: int | None = None
    is_head: bool | None = None


class SealClerkSync(BaseModel):
    """Đặt LẠI toàn bộ công ty một văn thư phụ trách = đúng danh sách này (thêm/bớt)."""
    employee_id: int
    company_ids: list[int] = []
    is_head: bool = False
    #  Trạng thái phân công (1=Đang hoạt động, 2=Tạm dừng). None = GIỮ NGUYÊN trạng
    #  thái cũ (để công tắc "Đa pháp nhân" ở danh sách không vô tình bật lại).
    status: int | None = None
    #  Dòng đang mở (để ghi nhật ký đúng mốc); 0 thì ghi theo employee_id.
    anchor_id: int = 0


class SealClerkForEmployee(BaseModel):
    employee_id: int
    company_ids: list[int]
    is_head: bool
    status: int = 1


class SealClerkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    company_id: int
    is_head: bool
    status: int = 1
    #  Tên hiển thị (join lúc trả) — không lưu trên bảng.
    employee_name: str | None = None
    employee_code: str | None = None
    company_name: str | None = None
    status_label: str | None = None
