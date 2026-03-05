import uuid
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from app.core.enums import AcademicLevel, ALevelCategory
from typing import Optional

class TeacherUserBrief(BaseModel):
    first_name: str
    last_name: str
    model_config = ConfigDict(from_attributes=True)

class FormTeacherBrief(BaseModel):
    id: uuid.UUID
    user: TeacherUserBrief
    model_config = ConfigDict(from_attributes=True)

class ClassCreate(BaseModel):
    name: str                           
    stream: str | None = None           
    level: AcademicLevel
    # Required only when level is A_LEVEL; must be None for all other levels.
    category: ALevelCategory | None = None
    capacity: int | None = None
    form_teacher_id: uuid.UUID | None = None

    @field_validator('name', 'stream')
    @classmethod
    def normalize_strings(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().upper()
        return v

    @model_validator(mode='after')
    def validate_category_for_level(self) -> 'ClassCreate':
        """
        Business rule enforcement at the schema boundary:
        - A_LEVEL classes MUST declare a category (Sciences or Arts).
        - All other levels MUST NOT have a category.
        """
        if self.level == AcademicLevel.A_LEVEL and self.category is None:
            raise ValueError("A-Level classes must specify a category: SCIENCES or ARTS.")
        if self.level != AcademicLevel.A_LEVEL and self.category is not None:
            raise ValueError(f"Category is only applicable to A-Level classes, not {self.level}.")
        return self


class ClassResponse(BaseModel):
    id: uuid.UUID
    name: str
    stream: str | None
    level: AcademicLevel
    category: ALevelCategory | None
    capacity: int | None
    school_id: uuid.UUID
    form_teacher_id: uuid.UUID | None
    form_teacher: FormTeacherBrief | None = None
    
    model_config = ConfigDict(from_attributes=True)

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    stream: Optional[str] = None
    level: Optional[AcademicLevel] = None
    category: Optional[ALevelCategory] = None
    capacity: Optional[int] = None
    form_teacher_id: Optional[uuid.UUID] = None

    @field_validator('name', 'stream')
    @classmethod
    def normalize_strings(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip().upper()
        return v

    @model_validator(mode='after')
    def validate_category_consistency(self) -> 'ClassUpdate':
        """
        Partial update guard: if both level and category are being updated together,
        enforce the A_LEVEL rule. Mixed partial updates (changing only one) are
        validated in the service layer where we have the full current record.
        """
        if self.level is not None and self.category is not None:
            if self.level == AcademicLevel.A_LEVEL and self.category is None:
                raise ValueError("A-Level classes must specify a category: SCIENCES or ARTS.")
            if self.level != AcademicLevel.A_LEVEL and self.category is not None:
                raise ValueError(f"Category is only applicable to A-Level classes, not {self.level}.")
        return self