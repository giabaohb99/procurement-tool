from pydantic import BaseModel, Field, model_validator

from .link_rule_model import RELATION_EXCERPT


class DocTypeLinkRuleBase(BaseModel):
    source_type_id: int
    relation: int = Field(ge=1, le=10)
    target_type_id: int | None = None
    is_required: bool = False
    min_count: int = Field(default=0, ge=0, le=99)
    max_count: int = Field(default=0, ge=0, le=99)
    on_parent_obsolete: int = Field(default=2, ge=1, le=3)
    on_parent_new_version: int = Field(default=3, ge=1, le=3)
    inherit_code: bool = False
    inherit_secrecy: bool = False
    is_active: bool = True

    @model_validator(mode="after")
    def _kiem_so_luong(self):
        #  Khai `từ 2 tới 1` thì không văn bản nào thỏa mãn, và câu báo lúc gửi
        #  duyệt sẽ đòi một thứ không bao giờ khai đủ được.
        if self.max_count and self.min_count > self.max_count:
            raise ValueError("Số lượng tối thiểu không được lớn hơn tối đa")
        if self.is_required and self.max_count and self.max_count < 1:
            raise ValueError("Quan hệ bắt buộc thì số lượng tối đa phải từ 1 trở lên")
        return self


class DocTypeLinkRuleCreate(DocTypeLinkRuleBase):
    pass


class DocTypeLinkRuleUpdate(DocTypeLinkRuleBase):
    pass


class DocTypeLinkRuleOut(DocTypeLinkRuleBase):
    id: int
    relation_label: str
    source_type_name: str
    target_type_name: str
    #  Dòng "trích từ" bị khóa ba cột — giao diện đọc cờ này để tắt ô, và để nói
    #  rõ vì sao tắt thay vì để người dùng bấm mãi không được.
    is_locked: bool

    @property
    def is_excerpt(self) -> bool:
        return self.relation == RELATION_EXCERPT
