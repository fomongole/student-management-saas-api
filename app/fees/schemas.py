import uuid
from datetime import date
from pydantic import BaseModel, ConfigDict, Field

class FeeStructureCreate(BaseModel):
    name: str = Field(..., max_length=100)
    amount: float = Field(..., gt=0)
    year: int
    term: int
    class_id: uuid.UUID | None = None

class FeeStructureResponse(BaseModel):
    id: uuid.UUID
    name: str
    amount: float
    year: int
    term: int
    class_id: uuid.UUID | None
    
    model_config = ConfigDict(from_attributes=True)

class FeePaymentCreate(BaseModel):
    student_id: uuid.UUID
    fee_structure_id: uuid.UUID
    amount_paid: float = Field(..., gt=0)
    payment_method: str = Field(..., max_length=50)
    reference_number: str = Field(..., max_length=100)
    
class FeeStructureUpdate(BaseModel):
    """Schema for updating an existing fee structure. All fields are optional."""
    name: str | None = Field(None, max_length=100)
    amount: float | None = Field(None, gt=0)
    year: int | None = None
    term: int | None = None
    class_id: uuid.UUID | None = None

class FeePaymentResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    fee_structure_id: uuid.UUID
    amount_paid: float
    payment_date: date
    payment_method: str
    reference_number: str
    
    model_config = ConfigDict(from_attributes=True)

class StudentBalanceResponse(BaseModel):
    student_id: uuid.UUID
    total_billed: float
    total_paid: float
    outstanding_balance: float
    
class FeePaymentDetailResponse(FeePaymentResponse):
    """Includes the name of the fee structure so the frontend can display 'Paid for Term 1 Tuition'."""
    fee_structure_name: str
    
    model_config = ConfigDict(from_attributes=True)